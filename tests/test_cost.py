"""Phase 26: cost estimate (nnc/costmodel.py), cost cap (agents.runtime.Budget), stop and resume at the cap,
run history, the dashboard's queue."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from nnc import autorun, costmodel, flow, ui
from nnc.agents.backend import AgentError, AgentResult, AgentTask
from nnc.agents.runtime import Budget, BudgetExceeded, CachedBackend
from tests.test_autorun import make_inbox

REPO = Path(__file__).resolve().parents[1]


class CostModelTest(unittest.TestCase):
    def test_committed_model_is_the_fit_of_the_committed_designs(self):
        self.assertEqual(costmodel.load(), json.loads(json.dumps(costmodel.fit(costmodel.samples(REPO / "designs")))),
                         "run: python -c \"from pathlib import Path; from nnc import costmodel; "
                         "costmodel.write(Path('designs'))\"")

    def test_model_shape(self):
        m = costmodel.load()
        names = {s["design"] for s in m["samples"]}
        self.assertNotIn("gen_sync_fifo", names)            # derived designs reuse another's verification
        self.assertIn("spi_master", names)                  # generated RTL, its own verification
        self.assertAlmostEqual(sum(m["shares"].values()), 1.0, places=2)
        self.assertGreaterEqual(m["holdout"]["in_range"], 10)   # 10 of 13 when written (EVALUATION §18)

    def test_estimate(self):
        small, big = costmodel.estimate(2000), costmodel.estimate(40000)
        self.assertLess(small["mid"], big["mid"])
        self.assertAlmostEqual(big["low"] * 4, big["high"], places=1)
        later = costmodel.estimate(40000, ["sim", "triage", "mutate", "formal", "report"])
        self.assertLess(later["mid"], big["mid"])
        self.assertEqual(set(later["by_stage"]), {"sim", "triage", "mutate"})
        self.assertEqual(costmodel.estimate(40000, ["formal", "cdc", "report"])["mid"], 0)
        self.assertIn("USD", costmodel.text(big))

    def test_document_tokens(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "s.md"
            p.write_text("# Spec\n\n" + "The block shall do things. " * 200, encoding="utf-8")
            self.assertGreater(costmodel.document_tokens([p]), 1000)


class _Inner:
    name = "fake"

    def __init__(self, cost=1.0, fail=False):
        self.cost, self.fail, self.calls = cost, fail, 0

    def run(self, task, log_dir):
        self.calls += 1
        if self.fail:
            e = AgentError("bad answer")
            e.cost_usd = self.cost
            raise e
        return AgentResult({"n": self.calls}, self.name, None, self.cost, {})


def _task(n):
    return AgentTask(name=f"A1_t{n}", instructions=f"task {n}", schema={"type": "object"}, inputs={})


class BudgetTest(unittest.TestCase):
    def test_cap(self):
        with tempfile.TemporaryDirectory() as t:
            b = Budget(2.5)
            be = CachedBackend(_Inner(1.0), Path(t) / "cache", b)
            for n in range(3):
                be.run(_task(n), Path(t))
            self.assertEqual((b.spent, b.exceeded), (3.0, False))   # the third call started below the cap
            with self.assertRaises(BudgetExceeded):
                be.run(_task(9), Path(t))
            self.assertTrue(b.exceeded)
            be.run(_task(0), Path(t))                               # cached answers are free, even above the cap
            self.assertEqual(b.spent, 3.0)

    def test_failed_calls_count(self):
        with tempfile.TemporaryDirectory() as t:
            b = Budget(None)
            be = CachedBackend(_Inner(0.7, fail=True), Path(t) / "cache", b)
            with self.assertRaises(AgentError):
                be.run(_task(1), Path(t))
            self.assertAlmostEqual(b.spent, 0.7)
            with self.assertRaises(ValueError):
                Budget(-1)


class RunCapTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _intake(self, d, libs, adapt):
        rep = {"verdict": "ready", "collect": {"top": "m_x"}, "ports": [1], "reasons": []}
        (d.work / "intake.json").write_text(json.dumps(rep), encoding="utf-8")
        return rep

    def test_stop_at_the_cap_then_go_on(self):
        f = make_inbox(self.root)
        ran = []

        def spend(cost, swallow=False):
            def runner(d, o):
                ran.append(1)
                try:
                    o.budget.before_call("A7_x")
                    o.budget.add(cost)
                except BudgetExceeded:
                    if not swallow:
                        raise
            return runner
        runners = {n: (lambda d, o: None) for n in flow.STAGES}
        runners["extract"] = spend(3.0)
        runners["review"] = spend(1.0, swallow=True)     # a stage that goes on past a refused call
        with mock.patch.object(autorun, "_intake", self._intake), mock.patch.dict(flow.RUNNERS, runners):
            rec = autorun.run(f, self.root / "designs" / "m_x", flow.Options(backend="replay"), max_cost=2.0)
            self.assertEqual(rec["state"], "stopped_budget")
            self.assertEqual(rec["cost_usd"], 3.0)
            self.assertEqual([(s["name"], s["state"]) for s in rec["steps"]][-2:],
                             [("extract", "done"), ("review", "budget")])
            self.assertIn("raise the cap", rec["message"])
            self.assertIsNotNone(rec["estimate"])
            self.assertEqual(rec["estimate"]["tokens"], costmodel.document_tokens([f / "spec" / "m_x_spec.md"]))
            # the next run goes on from the stage the cap stopped
            self.assertEqual(autorun.resume_stage(rec, autorun.input_hashes(f))[0], "review")
            rec2 = autorun.run(f, self.root / "designs" / "m_x", flow.Options(backend="replay"), max_cost=10)
            self.assertEqual((rec2["state"], rec2["start"]), ("done", "review"))
        hist = autorun.history(self.root / "designs" / "m_x")
        self.assertEqual([h["state"] for h in hist], ["done", "stopped_budget"])


class QueueTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "designs").mkdir()
        self.db = ui.Dashboard(self.root / "designs", self.root / "inbox", cwd=self.root, parallel=1)
        for n in ("a1", "a2", "a3"):
            make_inbox(self.root, n)

    def tearDown(self):
        self.tmp.cleanup()

    def test_one_at_a_time(self):
        procs = {}

        def popen(argv, **kw):
            p = mock.Mock()
            p.poll.return_value = None
            p.pid = 4242
            procs[argv[argv.index("run") + 1]] = (p, argv)
            return p
        with mock.patch.object(ui.subprocess, "Popen", side_effect=popen):
            self.assertEqual(self.db.start("a1", "replay", False, 5.0), "started")
            self.assertEqual(self.db.start("a2", "replay", True, None), "queued")
            self.assertEqual(self.db.start("a3", "replay", False, None), "queued")
            self.assertEqual((self.db.queued("a2"), self.db.queued("a3")), (1, 2))
            with self.assertRaises(ui.ProjectError):
                self.db.start("a2", "replay", False)
            self.db.stop("a3")                                   # leaves the queue
            self.assertIsNone(self.db.queued("a3"))
            procs["a1"][0].poll.return_value = 0                 # a1 ends: a2 starts
            self.db.pump()
            self.assertIn("a2", procs)
            self.assertNotIn("a3", procs)
        argv1, argv2 = procs["a1"][1], procs["a2"][1]
        self.assertEqual(argv1[argv1.index("--max-cost") + 1], "5")
        self.assertIn("--gated", argv2)
        self.assertNotIn("--max-cost", argv2)

    def test_cap_from_the_page(self):
        self.assertEqual(ui._cap(self.db, "a1", "12,5"), 12.5)
        for bad in ("x", "-1", "nan"):
            with self.assertRaises(ui.ProjectError):
                ui._cap(self.db, "a1", bad)
        est = self.db.estimate("a1")
        self.assertEqual(est["start"], "ingest")
        self.assertEqual(ui._cap(self.db, "a1", ""), float(-(-est["estimate"]["high"] // 1)))
        self.assertTrue((self.root / "inbox" / "a1" / ".estimate.json").is_file())

    def test_page_shows_the_estimate_and_the_history(self):
        page = ui.design_page(self.db, "a1").decode("utf-8")
        self.assertIn("The next run starts at <b>ingest</b>", page)
        self.assertIn("Estimated agent cost", page)
        self.assertIn('name="max_cost"', page)
        d = self.root / "designs" / "a1" / "work" / autorun.HISTORY_DIR
        d.mkdir(parents=True)
        (self.root / "designs" / "a1" / "nnc_state.json").write_text(json.dumps({"gates": {}}), encoding="utf-8")
        for st, state in (("2026-11-25T10:00:00Z", "stopped_budget"), ("2026-11-25T11:00:00Z", "done")):
            (d / f"{autorun.stamp(st)}.json").write_text(json.dumps({
                "started": st, "finished": "2026-11-25T11:30:00Z", "state": state, "mode": "unreviewed",
                "backend": "claude", "cost_usd": 4.5, "start": "ingest"}), encoding="utf-8")
        logs = self.root / "inbox" / "a1" / "logs"
        logs.mkdir()
        (logs / "20261125T100000Z.log").write_text("old log <x>", encoding="utf-8")
        page = ui.design_page(self.db, "a1").decode("utf-8")
        self.assertIn("Earlier runs", page)
        self.assertIn("stopped: cost cap", page)
        self.assertIn('href="/d/a1/log/20261125T100000Z"', page)
        self.assertIn("old log &lt;x&gt;", ui.log_page(self.db, "a1", "20261125T100000Z").decode("utf-8"))
        with self.assertRaises(FileNotFoundError):
            ui.log_page(self.db, "a1", "..")


if __name__ == "__main__":
    unittest.main()

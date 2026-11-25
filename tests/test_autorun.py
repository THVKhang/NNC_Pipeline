"""nnc run (nnc/autorun.py): an inbox folder to a workspace, resumption, the run record."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from nnc import autorun, flow
from nnc.project import Design, ProjectError

SPEC = "# m_x specification\n\n| Port | Direction | Width |\n|---|---|---|\n| i_clk | input | 1 |\n"


def make_inbox(root: Path, name="m_x", spec=SPEC, rtl=("m_x.sv",), cfg=None) -> Path:
    f = root / "inbox" / name
    (f / "spec").mkdir(parents=True)
    (f / "rtl").mkdir()
    (f / "spec" / "m_x_spec.md").write_text(spec, encoding="utf-8")
    for r in rtl:
        (f / "rtl" / r).parent.mkdir(parents=True, exist_ok=True)
        (f / "rtl" / r).write_text("module m_x(input i_clk); endmodule\n", encoding="utf-8")
    if cfg is not None:
        (f / "inbox.json").write_text(json.dumps(cfg), encoding="utf-8")
    return f


class InboxTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_problems_are_named(self):
        f = self.root / "inbox" / "empty"
        f.mkdir(parents=True)
        probs = autorun.read_inbox(f)["problems"]
        self.assertTrue(any("no specification" in p for p in probs))
        self.assertTrue(any("no RTL" in p for p in probs))
        f2 = make_inbox(self.root, "two")
        (f2 / "spec" / "axi.pdf").write_bytes(b"%PDF")
        self.assertTrue(any("standards/" in p for p in autorun.read_inbox(f2)["problems"]))
        f3 = make_inbox(self.root, "badtag", cfg={"tag": "lower"})
        self.assertTrue(any("tag" in p for p in autorun.read_inbox(f3)["problems"]))
        self.assertEqual(autorun.read_inbox(make_inbox(self.root, "ok"))["problems"], [])

    def test_names(self):
        for bad in ("", "1x", "../x", "a/b", "x y"):
            with self.assertRaises(ProjectError):
                autorun.check_name(bad)
        self.assertEqual(autorun.check_name("my_ip-2"), "my_ip-2")

    def test_prepare_makes_and_updates_the_workspace(self):
        f = make_inbox(self.root, rtl=("m_x.sv", "sub/pkg.sv"),
                       cfg={"top": "m_x", "tag": "MX", "defines": ["A", "B"], "config": {"formal": "on"}})
        (f / "standards").mkdir()
        (f / "standards" / "bus.md").write_text("# bus\n", encoding="utf-8")
        d, box, done = autorun.prepare(f, self.root / "designs" / "m_x")
        self.assertTrue((d.root / "rtl" / "sub" / "pkg.sv").is_file())
        cfg = d.config()
        self.assertEqual((cfg["top"], cfg["formal"], cfg["formal_defines"]), ("m_x", "on", "A,B"))
        docs = {x["file"]: (x["role"], x["tag"]) for x in d.documents()}
        self.assertEqual(docs, {"spec/m_x_spec.md": ("ip_spec", "MX"), "spec/standards/bus.md": ("standard", "S1")})
        # again: files copied over, documents not registered twice
        (f / "rtl" / "m_x.sv").write_text("// changed\n", encoding="utf-8")
        d, _box, done = autorun.prepare(f, self.root / "designs" / "m_x")
        self.assertIn("exists", done[0])
        self.assertEqual(len(d.documents()), 2)
        self.assertEqual((d.root / "rtl" / "m_x.sv").read_text(encoding="utf-8"), "// changed\n")
        # another specification file name is refused rather than registered as a second one
        (f / "spec" / "m_x_spec.md").rename(f / "spec" / "other.md")
        with self.assertRaises(ProjectError):
            autorun.prepare(f, self.root / "designs" / "m_x")

    def test_resume_stage(self):
        now = {"documents": "D", "rtl": "R"}
        self.assertEqual(autorun.resume_stage(None, now)[0], "ingest")
        prev = {"inputs": dict(now), "state": "stopped_at_gate",
                "steps": [{"name": "prepare", "state": "done"}, {"name": "review", "state": "done"},
                          {"name": "contract", "state": "waiting"}]}
        self.assertEqual(autorun.resume_stage(prev, now)[0], "contract")
        self.assertEqual(autorun.resume_stage(prev, {"documents": "D2", "rtl": "R"})[0], "ingest")
        self.assertEqual(autorun.resume_stage(prev, {"documents": "D", "rtl": "R2"})[0], "contract")
        late = dict(prev, steps=[{"name": "report", "state": "failed"}])
        self.assertEqual(autorun.resume_stage(late, {"documents": "D", "rtl": "R2"})[0], "sim")
        done = dict(prev, state="done", steps=[{"name": "report", "state": "done"}])
        self.assertIsNone(autorun.resume_stage(done, now)[0])
        self.assertEqual(autorun.resume_stage(done, {"documents": "D", "rtl": "R2"})[0], "sim")
        self.assertEqual(autorun.resume_stage(dict(prev, state="needs_input", steps=[]), now)[0], "ingest")
        self.assertEqual(autorun.resume_stage(dict(prev, inputs={}), now)[0], "ingest")

    def _fake_intake(self, verdict):
        def fake(d, libs, adapt):
            rep = {"verdict": "ready" if adapt else verdict, "collect": {"top": "m_x"}, "ports": [1],
                   "reasons": [{"level": "needs_input", "message": "give a library"}]}
            (d.work / "intake.json").write_text(json.dumps(rep), encoding="utf-8")
            return rep
        return fake

    def test_run_records_the_steps_and_resumes(self):
        f = make_inbox(self.root)
        ran = []
        runners = {n: (lambda d, o, n=n: ran.append(n)) for n in flow.STAGES}
        o = flow.Options(backend="replay")
        with mock.patch.object(autorun, "_intake", self._fake_intake("ready")), \
                mock.patch.dict(flow.RUNNERS, runners):
            rec = autorun.run(f, self.root / "designs" / "m_x", o, gated=True)
            # gated: stops before contract (G1 not approved)
            self.assertEqual(rec["state"], "stopped_at_gate")
            self.assertEqual(ran, ["ingest", "extract", "review"])
            self.assertEqual(Design.open(self.root / "designs" / "m_x").config()["top"], "m_x")
            on_disk = autorun.read_record(self.root / "designs" / "m_x")
            self.assertEqual(on_disk["steps"][-1], {"name": "contract", "state": "waiting",
                                                    "note": "G1_rules needs review"})
            self.assertFalse((f / ".run.json").exists())
            # unreviewed, again: goes on from contract, does not redo the review (answers kept)
            ran.clear()
            rec = autorun.run(f, self.root / "designs" / "m_x", o)
            self.assertEqual(rec["state"], "done")
            self.assertEqual(ran[0], "contract")
            self.assertNotIn("review", ran)
            self.assertNotIn("gen-rtl", ran)   # a stage of the design half only
            self.assertTrue(o.unreviewed)
            # nothing changed: nothing runs
            ran.clear()
            rec = autorun.run(f, self.root / "designs" / "m_x", o)
            self.assertEqual((rec["state"], ran), ("done", []))
            # an RTL change: from sim
            (f / "rtl" / "m_x.sv").write_text("// new\n", encoding="utf-8")
            rec = autorun.run(f, self.root / "designs" / "m_x", o)
            self.assertEqual(ran[0], "sim")

    def test_a_failing_stage_is_recorded(self):
        f = make_inbox(self.root)

        def boom(d, o):
            raise RuntimeError("tool missing")
        runners = {n: (lambda d, o: None) for n in flow.STAGES}
        runners["extract"] = boom
        with mock.patch.object(autorun, "_intake", self._fake_intake("ready")), \
                mock.patch.dict(flow.RUNNERS, runners):
            rec = autorun.run(f, self.root / "designs" / "m_x", flow.Options(backend="replay"))
        self.assertEqual(rec["state"], "failed")
        self.assertIn("tool missing", rec["message"])
        self.assertEqual([s["state"] for s in rec["steps"] if s["name"] == "extract"], ["failed"])
        self.assertEqual(autorun.resume_stage(rec, autorun.input_hashes(f))[0], "extract")

    def test_needs_input_stops_before_the_flow(self):
        f = make_inbox(self.root)
        with mock.patch.object(autorun, "_intake", self._fake_intake("needs_input")), \
                mock.patch.dict(flow.RUNNERS, {n: mock.Mock(side_effect=AssertionError) for n in flow.STAGES}):
            rec = autorun.run(f, self.root / "designs" / "m_x", flow.Options(backend="replay"))
        self.assertEqual(rec["state"], "needs_input")
        self.assertIn("give a library", rec["message"])

    def test_adapt_runs_when_the_intake_asks(self):
        f = make_inbox(self.root)
        with mock.patch.object(autorun, "_intake", self._fake_intake("adapt")), \
                mock.patch.dict(flow.RUNNERS, {n: (lambda d, o: None) for n in flow.STAGES}):
            rec = autorun.run(f, self.root / "designs" / "m_x", flow.Options(backend="replay"), prepare_only=True)
        self.assertEqual([s["name"] for s in rec["steps"]], ["prepare", "intake", "adapt"])
        self.assertEqual(rec["state"], "done")
        self.assertEqual(rec["inputs"], {})   # a prepare does not count as a run of the flow


if __name__ == "__main__":
    unittest.main()

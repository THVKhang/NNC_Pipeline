"""nnc demo: the steps, the staged kit files and the exit status (no tools, no agent)."""
import ast
import shutil
import tempfile
import unittest
from pathlib import Path

from nnc import demo

ROOT = Path(__file__).resolve().parents[1]


class DemoTest(unittest.TestCase):
    def test_steps_need_no_agent(self):
        self.assertEqual(demo.STEPS, ("intake", "kit", "cdc", "formal"))
        # the module imports nothing that calls a model
        tree = ast.parse((ROOT / "nnc" / "demo.py").read_text(encoding="utf-8"))
        names = {a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
        mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        self.assertFalse({m for m in mods if "agents" in m}, mods)
        self.assertNotIn("make_backend", names)

    def test_kit_files_leave_out_run_outputs(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            d = tmp / "ip"
            for rel in ("rtl/a.sv", "verif/tests/test_ip.py", "sim/Makefile", "sim/results.xml", "sim/sim.log",
                        "sim/sim_build/x.o", "sim/runlogs/s1/sim.log", "verif/tests/__pycache__/t.pyc", "work/r.json"):
                (d / rel).parent.mkdir(parents=True, exist_ok=True)
                (d / rel).write_text("x", encoding="utf-8")
            self.assertEqual(sorted(demo.kit_files(d)), ["ip/rtl/a.sv", "ip/sim/Makefile", "ip/verif/tests/test_ip.py"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_kit_script(self):
        self.assertIn("cd ip/sim && make regression SEED=1", demo.kit_script("ip", ".", 1))
        self.assertIn("cd ip/sim/min && make regression SEED=2", demo.kit_script("ip", "min", 2))

    def test_ok_needs_one_same_and_no_difference(self):
        S = demo.Step
        self.assertTrue(demo.ok([S("intake", "SAME"), S("formal", "SKIPPED")]))
        self.assertFalse(demo.ok([S("intake", "SAME"), S("kit", "DIFFERENT")]))
        self.assertFalse(demo.ok([S("intake", "SAME"), S("kit", "ERROR")]))
        self.assertFalse(demo.ok([S("intake", "SKIPPED")]))

    def test_a_failing_step_is_reported_not_raised(self):
        def boom():
            raise RuntimeError("no tool")
        s = demo._timed("kit", boom)
        self.assertEqual((s.status, s.lines), ("ERROR", ["RuntimeError: no tool"]))

    def test_compare_records_ignores_run_noise_only(self):
        import json
        tmp = Path(tempfile.mkdtemp())
        try:
            rec = {"review": {"date": "2026-11-21", "usage": {"calls": 23, "cost_usd": 1.3}},
                   "rules": [{"id": "R-1", "text": "a write is accepted only when not full"}],
                   "questions": [{"question": "q1", "rules": ["R-1"], "decision": {"answer": "yes", "by": "x"}}]}
            noise = json.loads(json.dumps(rec))
            noise["review"] = {"date": "2026-11-23", "usage": {"calls": 23, "cached": 23, "cost_usd": 0.0}}
            noise["questions"][0]["decision"] = None
            real = json.loads(json.dumps(rec))
            real["rules"][0]["text"] = "a write is always accepted"
            for name, body in (("a", rec), ("b", noise), ("c", real)):
                (tmp / name / "work").mkdir(parents=True)
                (tmp / name / "work" / "rules.json").write_text(json.dumps(body), encoding="utf-8")
                (tmp / name / "work" / "rules.md").write_text(name, encoding="utf-8")   # a rendering: skipped
            self.assertEqual(demo.compare_records(tmp / "a", tmp / "b"), (["work/rules.json"], []))
            seen, diffs = demo.compare_records(tmp / "a", tmp / "c")
            self.assertEqual(diffs, ["work/rules.json: differs from the committed record"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_replay_never_calls_a_model(self):
        from nnc.agents.backend import AgentTask
        from nnc.agents.runtime import ReplayMiss, make_backend
        tmp = Path(tempfile.mkdtemp())
        try:
            b = make_backend(tmp, "replay")
            with self.assertRaises(ReplayMiss):
                b.run(AgentTask("A1_x", "instructions", {"type": "object"}), tmp)
            self.assertFalse((tmp / "cache" / "agents").exists())   # nothing was answered, nothing was cached
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_primary_run_of_the_committed_designs(self):
        self.assertEqual(demo.primary_run(ROOT / "designs" / "ot_gpio")[0], "base.s1")
        self.assertEqual(demo.primary_run(ROOT / "designs" / "sync_fifo")[1:], (".", 1))


if __name__ == "__main__":
    unittest.main()

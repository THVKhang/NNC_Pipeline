"""Run set: loading, merging per check, and the report (no simulator)."""
import json
import tempfile
import unittest
from pathlib import Path

from nnc import report, runset

CONTRACT = {
    "top": "m_demo",
    "interface": {"clock": "i_clk", "reset": "i_rst_n", "ports": [],
                  "clocks": [{"name": "i_clk_a"}, {"name": "i_clk_b"}],
                  "parameters": [{"name": "PARA_W", "default": "8"}, {"name": "PARA_MODE", "default": "0"},
                                 {"name": "LPARA_X", "default": "PARA_W*2", "derived": True}]},
    "checks": [{"id": "CHK-001", "kind": "assertion", "rules": ["R-1"], "title": "a"},
               {"id": "CHK-002", "kind": "test", "rules": ["R-2"], "title": "b"},
               {"id": "CHK-003", "kind": "test", "rules": ["R-3"], "title": "c"},
               {"id": "CHK-004", "kind": "test", "rules": ["R-4"], "title": "d"}],
}
CFG = {"clock_periods": "i_clk_a=10,i_clk_b=13.7", "plusargs": "+MS_SEED={seed} +MS_EN=1"}


def _load(doc):
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / runset.FILE
        p.write_text(json.dumps(doc), encoding="utf-8")
        return runset.load(p, CONTRACT, CFG)


def _run(label, tests, asserts=None, nv=None, status="ran"):
    cfg, _, seed = label.partition(".s")
    return {"label": label, "config": cfg, "seed": int(seed), "note": "", "params": {"PARA_W": 8},
            "overrides": {}, "opts": {"defines": [], "plusargs": ""}, "clock_periods": {}, "status": status,
            "tests": [{"name": n, "status": s} for n, s in tests.items()], "assertions": asserts or {},
            "not_verifiable": nv or {}, "functional": {}, "build_errors": []}


class LoadTest(unittest.TestCase):
    def test_inherit_override_and_seeds(self):
        runs = _load({"seeds": [1, 2], "configs": [
            {"name": "base"},
            {"name": "off", "plusargs": "+MS_EN=0", "seeds": [7]},
            {"name": "syn", "defines": "VLSIT_SYNTHESIS", "params": {"PARA_MODE": "1"},
             "clock_periods": {"i_clk_b": 23.7}}]})
        self.assertEqual([r["label"] for r in runs], ["base.s1", "base.s2", "off.s7", "syn.s1", "syn.s2"])
        base, off, syn = runs[0], runs[2], runs[3]
        self.assertEqual(base["opts"], {"defines": [], "plusargs": "+MS_SEED={seed} +MS_EN=1"})
        self.assertEqual(base["clock_periods"], {"i_clk_a": 10, "i_clk_b": 13.7})
        self.assertEqual(off["opts"]["plusargs"], "+MS_EN=0")
        self.assertEqual(syn["opts"], {"defines": ["VLSIT_SYNTHESIS"], "plusargs": "+MS_SEED={seed} +MS_EN=1"})
        self.assertEqual(syn["params"], {"PARA_MODE": 1})
        self.assertEqual(syn["clock_periods"], {"i_clk_a": 10, "i_clk_b": 23.7})

    def test_errors(self):
        for doc, msg in (({"configs": []}, "non-empty"),
                         ({"configs": [{"name": "a"}, {"name": "a"}]}, "twice"),
                         ({"configs": [{"name": "a", "params": {"LPARA_X": 3}}]}, "not overridable"),
                         ({"configs": [{"name": "a", "params": {"NOPE": 3}}]}, "not overridable"),
                         ({"configs": [{"name": "a", "seed": 3}]}, "unknown field"),
                         ({"configs": [{"name": "a b"}]}, "name"),
                         ({"configs": [{"name": "a", "seeds": []}]}, "non-empty list"),
                         ({"configs": [{"name": "a", "clock_periods": "i_clk_z=5"}]}, "unknown clocks")):
            with self.assertRaises(ValueError) as cm:
                _load(doc)
            self.assertIn(msg, str(cm.exception))


class MergeTest(unittest.TestCase):
    def setUp(self):
        a = _run("base.s1", {"test_chk_002": "pass", "test_chk_003": "pass", "test_chk_004": "pass"},
                 {"CHK-001": {"hits": 3, "fails": 0}},
                 nv={"CHK-002": "needs the model off", "CHK-004": "needs PARA_MODE=1"})
        b = _run("off.s1", {"test_chk_002": "pass", "test_chk_003": "fail", "test_chk_004": "pass"},
                 {"CHK-001": {"hits": 2, "fails": 1, "first_fail_time": 40}},
                 nv={"CHK-004": "needs PARA_MODE=1 too"})
        b["tests"][1].update({"message": "boom", "exception": "AssertionError"})
        broken = _run("syn.s1", {}, status="build_failed")
        broken["build_errors"] = ["%Error: x"]
        self.merged = runset.merge([a, b, broken], {"status": "measured"}, {})

    def test_merge(self):
        m = self.merged
        t = {x["name"]: x for x in m["tests"]}
        self.assertEqual(t["test_chk_002"]["status"], "pass")
        self.assertEqual(t["test_chk_003"]["status"], "fail")
        self.assertEqual(t["test_chk_003"]["failed_in"], ["off.s1"])
        self.assertTrue(t["test_chk_003"]["message"].startswith("[failed in off.s1] boom"))
        self.assertEqual(m["assertions"]["CHK-001"]["hits"], 5)
        self.assertEqual(m["assertions"]["CHK-001"]["fails"], 1)
        self.assertEqual(m["assertions"]["CHK-001"]["first_fail_run"], "off.s1")
        # CHK-002 verified by the model-off run: no longer NOT_VERIFIABLE; CHK-004 in no run
        self.assertNotIn("CHK-002", m["not_verifiable"])
        self.assertIn("needs PARA_MODE=1 | needs PARA_MODE=1 too", m["not_verifiable"]["CHK-004"])
        self.assertEqual(m["status"], "ran")
        self.assertEqual(m["run_set"]["failed_runs"], ["syn.s1"])
        self.assertEqual(m["run_set"]["primary"], "base.s1")
        self.assertEqual(m["build_errors"], ["syn.s1: %Error: x"])

    def test_report(self):
        m = self.merged
        st = report.check_status(m, CONTRACT)
        self.assertEqual(st["CHK-001"]["status"], "FAIL")
        self.assertEqual(st["CHK-002"]["status"], "PASS")
        self.assertEqual(st["CHK-002"]["verified_in"], ["off.s1"])
        self.assertEqual(st["CHK-003"]["status"], "FAIL")
        self.assertEqual(st["CHK-003"]["failed_in"], ["off.s1"])
        self.assertEqual(st["CHK-004"]["status"], "NOT_VERIFIABLE")
        self.assertEqual(st["CHK-004"]["verified_in"], [])
        rules = {"rules": [{"id": f"R-{i}", "section": "1", "sentences": [], "strength": "shall",
                            "statement": "x"} for i in range(1, 5)]}
        rep = report.build("demo", [], rules, CONTRACT, {**m, "integration": {"ok": True}}, None, None,
                           {"total_usd": 0, "calls": 0, "by_agent": {}}, [])
        md = report.to_markdown(rep, CONTRACT, None)
        self.assertIn("## Run set", md)
        self.assertIn("verified in off.s1", md)
        self.assertIn("fails in off.s1", md)
        conds = {n: ok for n, ok, _ in report.signoff_conditions(rep)}
        self.assertFalse(conds["Every run of the run set built and ran"])

    def test_all_runs_failed_to_build(self):
        m = runset.merge([_run("a.s1", {}, status="build_failed")], {"status": "not_measured"}, {})
        self.assertEqual(m["status"], "build_failed")
        self.assertEqual(report.check_status(m, CONTRACT)["CHK-002"]["status"], "NOT_RUN")

    def test_script(self):
        s = runset.script(3)
        self.assertIn("xargs -P 3", s)
        self.assertIn("NNC_JOBS=4", s)
        self.assertIn("verilator_coverage --write merged.dat", s)


class RunSetMutationTest(unittest.TestCase):
    """Mutants come from lines executed in any run and are simulated in the first run executing them."""

    def test_mutant_goes_to_the_run_that_executes_its_line(self):
        from nnc import mutate
        from nnc.simhost import RunResult

        class FakeHost:
            name = "fake"

            def run(self, files, script, outputs, timeout_s=0, tag=""):
                self.files, self.script = files, script
                return RunResult(0, "", Path(tmp) / "out")

        rtl_src = "module m_demo(input wire a, output wire y, output wire z);\n" \
                  "  assign y = (a == 1'b1);\n" \
                  "  assign z = (a != 1'b0);\n" \
                  "endmodule\n"

        def base(lines):
            return {"tests": [], "assertions": {}, "coverage": {
                "metrics": {"line": {"files": {"m_demo.sv": {"hit": 1, "total": 3}}}}, "uncovered": [],
                "executed_lines": {"m_demo.sv": lines}}}
        contract = {"top": "m_demo", "interface": {"clock": "clk", "reset": "rst_n", "parameters": [], "ports": []}}
        with tempfile.TemporaryDirectory() as tmp:
            rtl = Path(tmp) / "rtl"
            rtl.mkdir()
            (rtl / "m_demo.sv").write_text(rtl_src, encoding="utf-8")
            sva = Path(tmp) / "sva"
            sva.mkdir()
            test = Path(tmp) / "test_demo.py"
            test.write_text("", encoding="utf-8")
            runs = [{"label": "a.s1", "params": {}, "opts": None, "clock_periods": None, "seed": 1, "baseline": base("2")},
                    {"label": "b.s7", "params": {}, "opts": None, "clock_periods": None, "seed": 7, "baseline": base("3")}]
            host = FakeHost()
            res = mutate.run(host, contract, rtl, sva, test, count=10, runs=runs)
        by_line = {m["line"]: m["run"] for m in res["mutants"]}
        self.assertEqual(set(by_line), {2, 3})
        self.assertEqual(by_line[2], "a.s1")
        self.assertEqual(by_line[3], "b.s7")
        for m in res["mutants"]:
            self.assertEqual(host.files[f"{m['id']}/seed.txt"], "1\n" if m["run"] == "a.s1" else "7\n")
        self.assertIn("SEED=$(cat seed.txt)", host.script)
        self.assertEqual(res["runs"]["available"], ["a.s1", "b.s7"])
        self.assertTrue(all(m["status"] == "not_compiled" for m in res["mutants"]))


class SecondChanceTest(unittest.TestCase):
    def test_survivor_is_rerun_in_other_configurations(self):
        from nnc import mutate
        from nnc.simhost import RunResult

        class FakeHost:
            """First pass: every mutant survives. Second pass: killed only in configuration 'hs1'."""
            name = "fake"
            calls = []

            def run(self, files, script, outputs, timeout_s=0, tag=""):
                out = Path(tmp) / tag
                for key in {k.split("/")[0] for k in files}:
                    (out / key).mkdir(parents=True, exist_ok=True)
                    seed = files[f"{key}/seed.txt"].strip()
                    fails = 1 if tag == "mutate_more" and seed == "5" else 0
                    (out / key / "sim.log").write_text(f"Running tests\nNNC_CHECK CHK-001 hits=3 fails={fails}\n")
                self.calls.append((tag, sorted({k.split('/')[0] for k in files})))
                return RunResult(0, "", out)

        def base():
            return {"tests": [], "assertions": {"CHK-001": {"hits": 3, "fails": 0}}, "coverage": {
                "metrics": {"line": {"files": {"m.sv": {"hit": 1, "total": 1}}}}, "uncovered": [],
                "executed_lines": {"m.sv": "2"}}}
        contract = {"top": "m", "interface": {"clock": "clk", "reset": "rst_n", "parameters": [], "ports": []}}
        with tempfile.TemporaryDirectory() as tmp:
            rtl = Path(tmp) / "rtl"
            rtl.mkdir()
            (rtl / "m.sv").write_text("module m(input wire a, output wire y);\n  assign y = (a == 1'b1);\nendmodule\n")
            (Path(tmp) / "sva").mkdir()
            (Path(tmp) / "t.py").write_text("")
            runs = [{"label": "base.s1", "seed": 1, "baseline": base()},
                    {"label": "base.s2", "seed": 2, "baseline": base()},      # same configuration: no retry
                    {"label": "off.s3", "seed": 3, "baseline": base()},
                    {"label": "hs1.s5", "seed": 5, "baseline": base()}]
            host = FakeHost()
            res = mutate.run(host, contract, rtl, Path(tmp) / "sva", Path(tmp) / "t.py", count=3, runs=runs)
        self.assertEqual(host.calls[0][0], "mutate")
        self.assertEqual(host.calls[1][0], "mutate_more")
        for m in res["mutants"]:
            self.assertEqual(m["status"], "killed")
            self.assertEqual(m["run"], "hs1.s5")
            self.assertEqual(m["also_run"], ["off.s3", "hs1.s5"])
            self.assertEqual(m["killed_by_checks"], ["CHK-001"])
        self.assertEqual(res["score"], 100.0)
        self.assertEqual(res["runs"]["second_chance_sims"], 2 * len(res["mutants"]))


class KitCheckTest(unittest.TestCase):
    def test_compare_outcomes_not_counts(self):
        from nnc import kitcheck
        rec = {"tests": [{"name": "t1", "status": "pass"}, {"name": "t2", "status": "fail"}],
               "assertions": {"CHK-001": {"hits": 5, "fails": 1}, "CHK-002": {"hits": 0, "fails": 0}},
               "not_verifiable": {"CHK-009": "x"}}
        same = json.loads(json.dumps(rec))
        same["assertions"]["CHK-001"] = {"hits": 7, "fails": 3}         # counts differ: same outcome
        self.assertEqual(kitcheck.compare(rec, same), [])
        other = json.loads(json.dumps(rec))
        other["tests"][1]["status"] = "pass"
        other["assertions"]["CHK-002"]["hits"] = 4
        diffs = kitcheck.compare(rec, other)
        self.assertTrue(any(d.startswith("failing_tests") for d in diffs))
        self.assertTrue(any(d.startswith("never_hit") for d in diffs))

    def test_recorded_primary_of_run_set(self):
        from nnc import kitcheck
        with tempfile.TemporaryDirectory() as tmp:
            w = Path(tmp)
            (w / "runs").mkdir()
            (w / "results.json").write_text(json.dumps({"run_set": {"primary": "base.s1", "runs": []}}))
            (w / "runs" / "base.s1.json").write_text(json.dumps({"result": {"tests": [], "seed": 1}}))
            res, name = kitcheck.recorded_result(w)
            self.assertEqual(name, "base.s1")
            self.assertEqual(res["seed"], 1)


if __name__ == "__main__":
    unittest.main()

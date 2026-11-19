"""Phase 12: tool host failures, the host probe, kits per configuration, formal rerun comparison (no tools)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from nnc import formal, kitcheck, sim, simhost, tools

CONTRACT = {
    "top": "m_demo",
    "interface": {"clock": "i_clk", "reset": {"name": "i_rst_n", "active_low": True},
                  "ports": [{"name": "i_clk", "direction": "input", "width": "1"},
                            {"name": "i_rst_n", "direction": "input", "width": "1"}],
                  "parameters": [{"name": "PARA_N", "default": "16"}]},
    "checks": [],
}


def _run(label, n, note="", opts=None):
    cfg, _, seed = label.partition(".s")
    return {"label": label, "config": cfg, "seed": int(seed), "note": note, "params": {"PARA_N": n},
            "opts": opts or {"defines": [], "plusargs": ""}, "clock_periods": {"i_clk": 20}}


class HostRetryTest(unittest.TestCase):
    def _host(self, results):
        h = simhost.WslHost("Test")
        h._launch = mock.Mock(side_effect=results)
        return h

    def test_one_host_failure_is_retried(self):
        bad = simhost.RunResult(1, "NNC_HOST_ERROR wsl.exe rc=1 produced no run log", Path("."), host_error=True)
        good = simhost.RunResult(0, "ok", Path("."))
        h = self._host([bad, good])
        with mock.patch.object(simhost, "HOST_RETRY_WAIT_S", 0):
            res = h.run({}, "true", [], tag="t")
        self.assertEqual((res.output, res.attempts), ("ok", 2))

    def test_two_host_failures_raise_and_record_nothing(self):
        bad = simhost.RunResult(1, "NNC_HOST_ERROR wsl.exe rc=1 produced no run log\nCatastrophic failure",
                                Path("."), host_error=True)
        h = self._host([bad, bad])
        with mock.patch.object(simhost, "HOST_RETRY_WAIT_S", 0), self.assertRaises(simhost.HostError) as e:
            h.run({}, "true", [], tag="formal")
        self.assertIn("ran no command", str(e.exception))

    def test_a_design_failure_is_not_retried(self):
        h = self._host([simhost.RunResult(2, "make failed", Path("."))])
        self.assertEqual(h.run({}, "false", [], tag="t").returncode, 2)
        self.assertEqual(h._launch.call_count, 1)


class ProbeTest(unittest.TestCase):
    def test_parse(self):
        out = ("NNC_PROBE_START\nNNC_TOOL|verilator|/opt/v|Verilator 5.055\nNNC_TOOL|sby||\n"
               "NNC_TOOL|lib.lib||\nNNC_PROBE_END\n")
        got = {c.name: c for c in tools.parse_probe(out)}
        self.assertTrue(got["verilator"].found)
        self.assertEqual(got["verilator"].role, "required")
        self.assertFalse(got["sby"].found)
        self.assertEqual(got["lib.lib"].role, "synthesis")
        self.assertIn("generic", got["lib.lib"].note)

    def test_script_names_every_tool(self):
        s = tools.host_probe_script("/opt/pdk", ["a.lib"])
        for name, _, _ in tools.HOST_TOOLS:
            self.assertIn(f"NNC_TOOL|{name}|", s)
        self.assertIn("/opt/pdk/a.lib", s)


class ConfigKitTest(unittest.TestCase):
    def setUp(self):
        self.runs = [_run("base.s1", 16), _run("base.s2", 16), _run("min.s1", 4, "CFG-MIN"),
                     _run("syn.s1", 16, opts={"defines": ["SYNTH"], "plusargs": "+EN={seed}"})]
        self.files = sim.config_kit_files(CONTRACT, [Path("m_demo.sv")], [Path("nnc_chk_a.sv")],
                                          [Path("test_demo.py")], self.runs, "base.s1")

    def test_folders_and_run_list(self):
        self.assertEqual(sorted(self.files), ["sim/configs/min/Makefile", "sim/configs/min/Makefile.cocotb",
                                              "sim/configs/min/nnc_interface.json", "sim/configs/runs.tsv",
                                              "sim/configs/syn/Makefile", "sim/configs/syn/Makefile.cocotb",
                                              "sim/configs/syn/nnc_interface.json"])
        rows = [l.split("\t") for l in self.files["sim/configs/runs.tsv"].splitlines() if not l.startswith("#")]
        self.assertEqual(rows, [["base.s1", ".", "1"], ["base.s2", ".", "2"], ["min.s1", "configs/min", "1"],
                                ["syn.s1", "configs/syn", "1"]])

    def test_configuration_values(self):
        mk = self.files["sim/configs/min/Makefile.cocotb"]
        self.assertIn("-GPARA_N=4", mk)
        self.assertIn("TOP_DIR := $(abspath ../../..)", mk)
        self.assertIn("$(TOP_DIR)/rtl/m_demo.sv", mk)
        self.assertIn("export NNC_INTERFACE := $(CURDIR)/nnc_interface.json", mk)
        self.assertEqual(json.loads(self.files["sim/configs/min/nnc_interface.json"])["parameters"]["PARA_N"], 4)
        syn = self.files["sim/configs/syn/Makefile.cocotb"]
        self.assertIn("+define+SYNTH", syn)
        self.assertIn("+EN=$(SEED)", syn)
        self.assertIn("CFG-MIN", self.files["sim/configs/min/Makefile"])

    def test_kitcheck_reads_the_run_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sim" / "configs").mkdir(parents=True)
            (root / "sim" / "configs" / "runs.tsv").write_text(self.files["sim/configs/runs.tsv"], encoding="utf-8")
            self.assertEqual(kitcheck.runs(root)[2], ("min.s1", "configs/min", 1))


class RecordedRunTest(unittest.TestCase):
    def test_run_label_must_be_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / "runs").mkdir()
            (work / "results.json").write_text(json.dumps(
                {"run_set": {"primary": "base.s1", "runs": [{"label": "base.s1"}, {"label": "min.s1"}]}}), encoding="utf-8")
            (work / "runs" / "min.s1.json").write_text(json.dumps({"result": {"tests": []}}), encoding="utf-8")
            self.assertEqual(kitcheck.recorded_result(work, "min.s1")[1], "min.s1")
            with self.assertRaises(ValueError):
                kitcheck.recorded_result(work, "odd.s1")

    def test_no_run_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / "results.json").write_text(json.dumps({"seed": 1}), encoding="utf-8")
            with self.assertRaises(ValueError):
                kitcheck.recorded_result(work, "base.s1")


class FormalCompareTest(unittest.TestCase):
    def _res(self, **st):
        return {"checks": {k.replace("_", "-"): {"status": v} for k, v in st.items()}}

    def test_same(self):
        r = self._res(CHK_001="PROVEN", CHK_002="CEX")
        self.assertEqual(formal.compare_recorded(r, r), ([], []))

    def test_counterexample_appears_or_disappears(self):
        fails, _ = formal.compare_recorded(self._res(CHK_001="PROVEN"), self._res(CHK_001="CEX"))
        self.assertEqual(len(fails), 1)
        fails, _ = formal.compare_recorded(self._res(CHK_001="CEX"), self._res(CHK_001="BOUNDED"))
        self.assertEqual(len(fails), 1)

    def test_vacuous_and_error_are_exact(self):
        self.assertTrue(formal.compare_recorded(self._res(CHK_001="VACUOUS"), self._res(CHK_001="BOUNDED"))[0])
        self.assertTrue(formal.compare_recorded(self._res(CHK_001="PROVEN"), self._res(CHK_001="ERROR"))[0])
        self.assertTrue(formal.compare_recorded(self._res(CHK_001="VACUOUS"), self._res(CHK_001="TIMEOUT"))[0])

    def test_time_dependent_changes_are_notes(self):
        fails, notes = formal.compare_recorded(self._res(CHK_001="PROVEN", CHK_002="TIMEOUT", CHK_003="CEX"),
                                               self._res(CHK_001="BOUNDED", CHK_002="PROVEN", CHK_003="TIMEOUT"))
        self.assertEqual(fails, [])
        self.assertEqual(len(notes), 3)

    def test_check_sets_and_configurations(self):
        self.assertTrue(formal.compare_recorded(self._res(CHK_001="PROVEN"), self._res(CHK_002="PROVEN"))[0])
        want = {"checks": {"CHK-001": {"status": "PROVEN", "per_config": {"a": "PROVEN", "b": "VACUOUS"}}}}
        got = {"checks": {"CHK-001": {"status": "PROVEN", "per_config": {"a": "PROVEN", "b": "PROVEN"}}}}
        fails, _ = formal.compare_recorded(want, got)
        self.assertEqual(fails, ["CHK-001 [b]: recorded VACUOUS, rerun PROVEN"])


if __name__ == "__main__":
    unittest.main()

"""Baseline: scripts of the upstream hand-written testbench and the port of its stimulus generator."""
import json
import unittest
from pathlib import Path

from nnc import baseline

ROOT = Path(__file__).resolve().parents[1] / "designs"


class BaselineTest(unittest.TestCase):
    def test_build(self):
        desc = {"top": "tb_x", "tb": ["tb_x.sv"], "rtl": ["a.sv"], "defines": ["SYN"],
                "runs": [{"name": "r1", "params": {"DEPTH": 4}, "plusargs": ["+SEED=1"]},
                         {"name": "r2", "defines": ["B"], "stimulus": {"kind": "apbcdc", "index": 0, "nx": 3}}]}
        files, script, names = baseline.build(desc, Path("/d"), Path("/d/rtl"))
        self.assertEqual(names, ["r1", "r2"])
        self.assertIn("xargs -P 6 -n 1 sh", script)
        r1 = files["runs/r1.sh"]
        self.assertIn("-s tb_x -DSYN -Ptb_x.DEPTH=4 rtl/a.sv tb/tb_x.sv", r1)
        self.assertIn("vvp -n build/r1.vvp +SEED=1", r1)
        self.assertIn("NNC_COMPILE_RC=$rc", r1)
        self.assertIn('echo "NNC_VVP_RC=$?" >> logs/r1.log', r1)
        self.assertIn("-DSYN -DB", files["runs/r2.sh"])
        self.assertIn("+STIM=stim/r2", files["runs/r2.sh"])
        self.assertEqual(len(files["stim/r2_req.txt"].splitlines()), 3)

    def test_apbcdc_stimulus_is_deterministic(self):
        a, b = baseline.apbcdc_stimulus(5, 40), baseline.apbcdc_stimulus(5, 40)
        self.assertEqual(a, b)
        self.assertNotEqual(a, baseline.apbcdc_stimulus(6, 40))
        req, cmp_ = a
        self.assertEqual(len(req.splitlines()), 40)
        self.assertEqual(len(req.splitlines()[0].split()), 7)
        self.assertEqual(len(cmp_.splitlines()[0].split()), 5)

    def test_mutant_copy(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            rtl = Path(tmp) / "rtl"
            rtl.mkdir()
            (rtl / "a.sv").write_text("module a;\n  assign y = p && q;\nendmodule\n", encoding="utf-8")
            m = {"id": "M01", "file": "a.sv", "line": 2, "original": "assign y = p && q;", "mutated": "  assign y = p || q;"}
            baseline.mutant_copy(rtl, m, Path(tmp) / "out")
            self.assertIn("p || q", (Path(tmp) / "out" / "a.sv").read_text(encoding="utf-8"))
            self.assertIn("p && q", (rtl / "a.sv").read_text(encoding="utf-8"))
            with self.assertRaises(ValueError):
                baseline.mutant_copy(rtl, dict(m, line=1), Path(tmp) / "out")

    def test_descriptions_match_files(self):
        for ip in ("sync_fifo", "async_apb_bridge", "apb_tlul_bridge"):
            desc = baseline.load(ROOT / ip)
            for f in desc["tb"]:
                self.assertTrue((ROOT / ip / "baseline" / f).is_file(), f)
            for f in desc["rtl"]:
                self.assertTrue((ROOT / ip / "rtl" / f).is_file(), f)
            self.assertEqual(len({r["name"] for r in desc["runs"]}), len(desc["runs"]))
        self.assertEqual(len(json.loads((ROOT / "async_apb_bridge" / "baseline" / "baseline.json")
                                        .read_text(encoding="utf-8"))["runs"]), 64)


if __name__ == "__main__":
    unittest.main()

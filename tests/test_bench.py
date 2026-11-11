"""Bug benchmark: manifest, patches, verdict and summary (no simulator)."""
import json
import tempfile
import unittest
from pathlib import Path

from nnc import bench, inject


class BenchTest(unittest.TestCase):
    def _design(self, tmp, bugs):
        root = Path(tmp)
        (root / "rtl").mkdir()
        (root / "rtl" / "m.sv").write_text("module m;\n  assign a = b & c;\n  assign d = b;\nendmodule\n",
                                           encoding="utf-8")
        (root / "bugs").mkdir()
        (root / "bugs" / "bugs.json").write_text(json.dumps({"bugs": bugs}), encoding="utf-8")
        return root

    def test_patch_applies_with_inject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._design(tmp, [{"id": "B1", "title": "t", "file": "m.sv", "find": "b & c", "replace": "b | c"}])
            b = bench.load(root)[0]
            patch = bench.make_patch(root / "rtl", b)
            self.assertIn("-  assign a = b & c;", patch)
            self.assertIn("+  assign a = b | c;", patch)
            inject.make_copy(root / "rtl", patch, root / "copy")
            self.assertIn("b | c", (root / "copy" / "m.sv").read_text(encoding="utf-8"))
            self.assertIn("b & c", (root / "rtl" / "m.sv").read_text(encoding="utf-8"))   # original untouched

    def test_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._design(tmp, [{"id": "B1", "title": "t", "file": "m.sv", "find": "assign", "replace": "x"}])
            with self.assertRaisesRegex(bench.BenchError, "matches 2 lines"):
                bench.make_patch(root / "rtl", bench.load(root)[0])
        with tempfile.TemporaryDirectory() as tmp:
            root = self._design(tmp, [{"id": "B1", "title": "t", "file": "m.sv", "find": "b & c", "replace": "x"},
                                      {"id": "B1", "title": "t", "file": "m.sv", "find": "b;", "replace": "c;"}])
            with self.assertRaisesRegex(bench.BenchError, "twice"):
                bench.load(root)

    def test_verdict_and_summary(self):
        self.assertEqual(bench.verdict(["B_test_wrong", "A_rtl_wrong", "A_rtl_wrong"]), "A_rtl_wrong")
        self.assertEqual(bench.verdict(["C_spec_unclear", "A_rtl_wrong"]), "A_rtl_wrong")   # tie: A first
        self.assertIsNone(bench.verdict([]))
        rows = [{"id": "1", "caught": True, "triage_verdict": "A_rtl_wrong", "triage_correct": True, "triage_cost_usd": 2.0},
                {"id": "2", "caught": True, "triage_verdict": "B_test_wrong", "triage_correct": False, "triage_cost_usd": 1.5},
                {"id": "3", "caught": False, "triage_verdict": None, "triage_correct": None}]
        s = bench.summarize(rows)
        self.assertEqual((s["bugs"], s["caught"], s["detection_rate"]), (3, 2, 66.7))
        self.assertEqual((s["triaged"], s["triage_correct"], s["triage_accuracy"], s["triage_cost_usd"]), (2, 1, 50.0, 3.5))


if __name__ == "__main__":
    unittest.main()

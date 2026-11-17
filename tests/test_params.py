import json
import tempfile
import unittest
from pathlib import Path

from nnc import params
from nnc.project import Design, ProjectError

IFACE = {"parameters": [
    {"name": "P_DATA_W", "default": "32", "legal": "8, 16 or 32"},
    {"name": "P_ADDR_W", "default": "32", "legal": "16 to 32"},
    {"name": "P_SRC_W", "default": "8", "legal": "1�16 inclusive"},
    {"name": "P_SRC_ID", "default": "0", "legal": "0 to 2^P_SRC_W - 1"},
    {"name": "P_DEPTH", "default": "8", "legal": "Power of 2, minimum 2, no upper limit"},
    {"name": "P_USER_W", "default": "0", "legal": "0 to P_DATA_W; an integer multiple of 8 is recommended (REF-1)"},
    {"name": "P_N", "default": "1", "legal": "1..8"},
    {"name": "P_M", "default": "2", "legal": "Any integer of 2 or more, no upper limit (DEC-009)"},
    {"name": "P_ODD", "default": "1", "legal": "depends on the bus fabric"},
    {"name": "L_STRB_W", "default": "Derived", "legal": "1, 2 or 4", "derived": "P_DATA_W / 8"},
]}


class ParseLegalTest(unittest.TestCase):
    def cons(self, name):
        return next(r["constraint"] for r in params.table(IFACE) if r["name"] == name)

    def test_forms(self):
        self.assertEqual(self.cons("P_DATA_W")["values"], [8, 16, 32])
        self.assertEqual((self.cons("P_ADDR_W")["min"], self.cons("P_ADDR_W")["max"]), ("16", "32"))
        self.assertEqual((self.cons("P_SRC_W")["min"], self.cons("P_SRC_W")["max"]), ("1", "16"))
        self.assertEqual(self.cons("P_SRC_ID")["max"], "2**P_SRC_W - 1")
        d = self.cons("P_DEPTH")
        self.assertTrue(d["pow2"])
        self.assertEqual(d["min"], "2")
        self.assertNotIn("max", d)
        self.assertEqual(self.cons("P_USER_W")["note"], "an integer multiple of 8 is recommended (REF-1)")
        self.assertEqual(self.cons("P_N")["max"], "8")
        self.assertEqual(self.cons("P_M")["min"], "2")
        self.assertEqual(self.cons("P_ODD")["kind"], "unchecked")

    def test_check(self):
        self.assertEqual(params.check(IFACE, {})["errors"], [])
        res = params.check(IFACE, {"P_DATA_W": 8, "P_USER_W": 9, "P_DEPTH": 12, "P_SRC_W": 2, "P_SRC_ID": 4})
        errs = " | ".join(res["errors"])
        self.assertIn("P_USER_W=9: maximum is 8", errs)       # bound from another parameter
        self.assertIn("P_DEPTH=12: must be a power of 2", errs)
        self.assertIn("P_SRC_ID=4: maximum is 3", errs)       # 2^2 - 1
        self.assertEqual(res["values"]["L_STRB_W"], 1)
        self.assertEqual(res["unchecked"], ["P_ODD"])
        res = params.check(IFACE, {"P_DATA_W": 64})
        self.assertTrue(any("L_STRB_W=8" in e for e in res["errors"]))  # derived value checked too
        with self.assertRaises(ValueError):
            params.check(IFACE, {"L_STRB_W": 2})                     # derived: not overridable


class ChooseTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "gen"
        self.d = Design.init(self.root)
        self.contract = {"top": "gen", "interface": IFACE}
        (self.d.work / "contract.json").write_text(json.dumps(self.contract), encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_choose_refuses_illegal_and_unchecked(self):
        with self.assertRaisesRegex(ValueError, "illegal configuration"):
            params.choose(self.d.work, self.contract, {"P_DATA_W": 12}, by="r")
        with self.assertRaisesRegex(ValueError, "accept-unchecked"):
            params.choose(self.d.work, self.contract, {}, by="r")
        with self.assertRaisesRegex(ValueError, "--by"):
            params.choose(self.d.work, self.contract, {}, by="", accept_unchecked=True)
        doc = params.choose(self.d.work, self.contract, {"P_DATA_W": 16}, by="r", accept_unchecked=True)
        self.assertEqual(doc["values"]["L_STRB_W"], 2)
        self.assertTrue((self.d.work / "final_config.json").is_file())

    def test_design_gates_only_for_generated_rtl(self):
        self.assertNotIn("D1_config", [s.gate for s in self.d.status()])
        with self.assertRaisesRegex(ProjectError, "design gate"):
            self.d.approve("D1_config", by="r")
        self.d.set_config(rtl_origin="generated")
        st = {s.gate: s.state for s in self.d.status()}
        self.assertEqual(st["D1_config"], "BLOCKED")
        self.assertEqual(st["G4_signoff"], "BLOCKED")
        (self.d.work / "rules.json").write_text("{}", encoding="utf-8")
        self.d.approve("G1_rules", by="r")
        self.d.approve("G2_contract", by="r")
        params.choose(self.d.work, self.contract, {}, by="r", accept_unchecked=True)
        self.d.approve("D1_config", by="r")
        st = {s.gate: s.state for s in self.d.status()}
        self.assertEqual(st["D2_rtl"], "PENDING")
        self.assertEqual(st["G3_verif_sources"], "PENDING")    # G3 does not wait for the RTL
        (self.root / "verif" / "tests" / "t.py").write_text("x = 1\n", encoding="utf-8")
        self.d.approve("G3_verif_sources", by="r")
        (self.d.work / "results.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ProjectError, "D2_rtl"):     # G4 needs the RTL gate too
            self.d.approve("G4_signoff", by="r")
        self.assertIn("D2_rtl", self.d.require_gate("G4_signoff", unreviewed=True))

    def test_source_document_change_makes_g1_stale(self):
        spec = self.root / "spec" / "ip.md"
        spec.write_text("# spec\n", encoding="utf-8")
        self.d.add_document("spec/ip.md", "ip_spec", "IP")
        (self.d.work / "rules.json").write_text("{}", encoding="utf-8")
        self.d.approve("G1_rules", by="r")
        self.assertEqual(self.d.status()[0].state, "APPROVED")
        spec.write_text("# spec v2\n", encoding="utf-8")
        st = self.d.status()[0]
        self.assertEqual(st.state, "STALE")
        self.assertIn("source spec/ip.md", st.detail)


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from nnc.project import Design, ProjectError


class DesignGateTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "pilot"
        self.design = Design.init(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def states(self):
        return {s.gate: s.state for s in self.design.status()}

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def test_init_creates_layout_and_rejects_reinit(self):
        for d in ("spec/standards", "rtl", "work", "verif/sva", "verif/tests"):
            self.assertTrue((self.root / d).is_dir(), d)
        with self.assertRaises(ProjectError):
            Design.init(self.root)

    def test_invalid_name(self):
        with self.assertRaises(ProjectError):
            Design.init(Path(self._tmp.name) / "1bad name")

    def test_fresh_design_is_pending_then_blocked(self):
        self.assertEqual(self.states(), {"G1_rules": "PENDING", "G2_contract": "BLOCKED",
                                         "G3_verif_sources": "BLOCKED", "G4_signoff": "BLOCKED"})

    def test_cannot_approve_missing_artifact_or_out_of_order(self):
        with self.assertRaisesRegex(ProjectError, "missing artifacts"):
            self.design.approve("G1_rules", by="reviewer")
        self.write("work/contract.json", "{}")
        with self.assertRaisesRegex(ProjectError, "G1_rules is PENDING"):
            self.design.approve("G2_contract", by="reviewer")

    def test_approval_needs_reviewer(self):
        self.write("work/rules.json", "{}")
        with self.assertRaises(ProjectError):
            self.design.approve("G1_rules", by="  ")

    def test_change_after_approval_makes_gate_stale_and_blocks_later_gates(self):
        self.write("work/rules.json", '{"rules": []}')
        self.design.approve("G1_rules", by="reviewer")
        self.write("work/contract.json", "{}")
        self.design.approve("G2_contract", by="reviewer")
        self.assertEqual(self.states()["G2_contract"], "APPROVED")

        self.write("work/rules.json", '{"rules": [1]}')
        st = self.states()
        self.assertEqual(st["G1_rules"], "STALE")
        self.assertEqual(st["G2_contract"], "BLOCKED")

        self.design.approve("G1_rules", by="reviewer")  # re-review restores the chain
        self.assertEqual(self.states()["G2_contract"], "APPROVED")

    def test_folder_artifact_hash_tracks_file_changes(self):
        for rel in ("work/rules.json", "work/contract.json"):
            self.write(rel, "{}")
        self.design.approve("G1_rules", by="r")
        self.design.approve("G2_contract", by="r")
        self.assertEqual(self.states()["G3_verif_sources"], "PENDING")  # empty folders: nothing to approve
        self.write("verif/tests/test_a.py", "a = 1\n")
        self.design.approve("G3_verif_sources", by="r")
        self.write("verif/sva/chk.sv", "module chk; endmodule\n")
        self.assertEqual(self.states()["G3_verif_sources"], "STALE")

    def test_revoke(self):
        self.write("work/rules.json", "{}")
        self.design.approve("G1_rules", by="r")
        self.design.revoke("G1_rules")
        self.assertEqual(self.states()["G1_rules"], "PENDING")
        with self.assertRaises(ProjectError):
            self.design.revoke("G1_rules")

    def test_state_file_is_json_with_hashes(self):
        self.write("work/rules.json", "{}")
        self.design.approve("G1_rules", by="r", note="ok")
        state = json.loads((self.root / "nnc_state.json").read_text(encoding="utf-8"))
        rec = state["gates"]["G1_rules"]
        self.assertEqual(rec["note"], "ok")
        self.assertEqual(len(rec["hashes"]["work/rules.json"]), 64)


if __name__ == "__main__":
    unittest.main()

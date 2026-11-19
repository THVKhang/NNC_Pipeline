"""Phase 13: formal equivalence of surviving mutants (fake tool host, no tools)."""
import tempfile
import unittest
from pathlib import Path

from nnc import mutequiv
from nnc.simhost import RunResult, SimHost

CONTRACT = {
    "top": "m_demo",
    "interface": {"clock": "i_clk", "reset": {"name": "i_rst_n", "active_low": True},
                  "ports": [{"name": "i_clk", "direction": "input", "width": "1"},
                            {"name": "i_rst_n", "direction": "input", "width": "1"},
                            {"name": "i_d", "direction": "input", "width": "1"},
                            {"name": "o_q", "direction": "output", "width": "1"}],
                  "parameters": [{"name": "PARA_N", "default": "16"}]},
    "checks": [],
}
RTL = """module m_demo #(parameter PARA_N = 16) (input logic i_clk, input logic i_rst_n, input logic i_d, output logic o_q);
  always_ff @(posedge i_clk or negedge i_rst_n)
    if (!i_rst_n) o_q <= 1'b1;
    else          o_q <= i_d;
`ifndef VLSIT_SYNTHESIS
  initial $display("model");
`endif
endmodule
"""


class FakeHost(SimHost):
    name = "fake"

    def __init__(self, prove="PASS", bmc="PASS"):
        self.prove, self.bmc, self.calls = prove, bmc, []

    def run(self, files, script, outputs, timeout_s=1800, tag="run"):
        self.calls.append(files)
        return RunResult(0, f"NNC_MITER_RC=0\nNNC_STATUS_bmc={self.bmc}\nNNC_STATUS_prove={self.prove}\n",
                         Path(tempfile.gettempdir()))


def _mutant(line, mutated, run=None, also=None):
    return {"id": "M1", "file": "m_demo.sv", "line": line, "operator": "one_to_zero", "original": "",
            "mutated": mutated, "status": "survived", "killed_by_tests": [], "killed_by_checks": [],
            **({"run": run, "also_run": also or []} if run else {})}


class MutantEquivTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rtl = Path(self.tmp.name)
        (self.rtl / "m_demo.sv").write_text(RTL, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_sim_only_line_is_not_judged(self):
        self.assertTrue(mutequiv.in_sim_only(RTL, 6))
        self.assertFalse(mutequiv.in_sim_only(RTL, 3))
        host = FakeHost()
        r = mutequiv.check_mutant(host, CONTRACT, self.rtl, _mutant(6, '  initial $display("x");'), None)
        self.assertEqual(r["status"], "SIM_ONLY")
        self.assertEqual(host.calls, [])

    def test_mutant_reaches_the_gate_side_only(self):
        host = FakeHost()
        r = mutequiv.check_mutant(host, CONTRACT, self.rtl, _mutant(3, "    if (!i_rst_n) o_q <= 1'b0;"), None)
        self.assertEqual(r["status"], "PROVEN")
        files = host.calls[0]
        self.assertIn("1'b1", files["gold/m_demo.sv"])
        self.assertIn("o_q <= 1'b0", files["gate/m_demo.sv"])
        self.assertIn("VLSIT_SYNTHESIS", files["nnc_miter.ys"])      # the synthesis branch, as restyle

    def test_every_configuration_it_survived_in(self):
        run_set = {"runs": [{"label": "base.s1", "overrides": {}}, {"label": "base.s2", "overrides": {}},
                            {"label": "min.s1", "overrides": {"PARA_N": 4}}]}
        host = FakeHost(prove="FAIL", bmc="FAIL")
        r = mutequiv.check_mutant(host, CONTRACT, self.rtl, _mutant(3, "    if (!i_rst_n) o_q <= 1'b0;", "base.s1",
                                                                     ["base.s2", "min.s1"]), run_set)
        self.assertEqual(sorted(r["per_config"]), ["base.s1", "min.s1"])     # base.s2: same parameters
        self.assertEqual(r["status"], "CEX")
        self.assertIn("chparam -set PARA_N 4", host.calls[1]["nnc_miter.ys"])

    def test_summary_and_score(self):
        mutation = {"killed": 9, "mutants": [
            {**_mutant(3, "x"), "equivalence": {"status": "PROVEN", "per_config": {}}},
            {**_mutant(3, "y"), "id": "M2", "equivalence": {"status": "CEX", "per_config": {}}},
            {**_mutant(3, "z"), "id": "M3", "status": "killed"}]}
        s = mutequiv.summary(mutation)
        self.assertEqual(s["by_status"], {"CEX": 1, "PROVEN": 1})
        self.assertEqual(s["score_without_equivalent"], 90.0)        # 9 / (9 + 2 - 1)


if __name__ == "__main__":
    unittest.main()

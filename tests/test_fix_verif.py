"""Phase 14: verification fixes by agent A17 — fault text without the RTL, and the weakening check."""
import unittest

from nnc import fix_verif as fv

SVA = """module nnc_chk_rx (input logic i_clk);
  a_CHK_003_deliver : assert property (@(posedge i_clk) disable iff (!i_rst_n) a |-> b);
  a_CHK_005_drop    : assert property (@(posedge i_clk) disable iff (!i_rst_n) c |-> d);
endmodule
"""
COV = "module nnc_cov; c_CHK_003_hit : cover property (@(posedge i_clk) a); endmodule\n"
TEST = """import cocotb

@cocotb.test()
async def test_chk_003(dut):
    \"\"\"CHK-003\"\"\"
    assert dut.o.value == 1

@cocotb.test()
async def test_chk_005(dut):
    \"\"\"CHK-005\"\"\"
    assert dut.p.value == 0
"""
OLD = {"sva/nnc_chk_rx.sv": SVA, "sva/nnc_cov.sv": COV, "tests/test_uart.py": TEST}


class FaultTextTest(unittest.TestCase):
    def test_only_b_and_no_rtl(self):
        analyses = [
            {"failure": "CHK-003 — delivery", "most_likely": "B_test_wrong",
             "spec_says": "REQ-RX-001: a frame starts on a falling edge. Section 5.2.",
             "test_does": "The model starts on any low sample (nnc_chk_rx.sv:64). The RTL in m_uart_lite_rx.sv:74 "
                          "uses r_rxd_prev. The DUT does it right.",
             "options": "Fix the checker: keep the previous sample; m_uart_lite_rx is fine."},
            {"failure": "CHK-009", "most_likely": "A_rtl_wrong", "spec_says": "x", "test_does": "y", "options": "z"},
            {"check": "CHK-010 (a_CHK_010, verif/sva/x.sv)", "most_likely": "B_checker_wrong",
             "spec_says": "s.", "checker_does": "c.", "options": "o."}]
        out = fv.fault_text(analyses, ["m_uart_lite_rx.sv", "m_uart_lite_rx"])
        self.assertEqual([f["id"] for f in out], [1, 2])
        text = " ".join(" ".join(str(v) for v in f.values()) for f in out)
        for leak in ("m_uart_lite_rx", "RTL", "DUT", "r_rxd_prev"):
            self.assertNotIn(leak, text)
        self.assertIn("falling edge", out[0]["spec_says"])
        self.assertIn("any low sample", out[0]["verification_does"])
        self.assertEqual(out[1]["failure"], "formal counterexample on CHK-010")


class WeakeningTest(unittest.TestCase):
    def test_a_correction_passes(self):
        new = {"sva/nnc_chk_rx.sv": SVA.replace("a |-> b", "a && prev |-> b")}
        self.assertEqual(fv.weakening(OLD, new), ([], []))

    def test_removed_assertion_cover_test_or_check(self):
        cases = [
            {"sva/nnc_chk_rx.sv": SVA.replace("  a_CHK_005_drop    : assert property (@(posedge i_clk) disable iff (!i_rst_n) c |-> d);\n", "")},
            {"sva/nnc_cov.sv": COV.replace("c_CHK_003_hit : cover property (@(posedge i_clk) a);", "")},
            {"tests/test_uart.py": TEST.split("@cocotb.test()\nasync def test_chk_005")[0]},
            {"tests/test_uart.py": TEST.replace('"""CHK-005"""', '"""drop"""')},
        ]
        for new in cases:
            block, _ = fv.weakening(OLD, new)
            self.assertTrue(block, new)

    def test_switch_off_assume_skip(self):
        self.assertTrue(fv.weakening(OLD, {"sva/nnc_chk_rx.sv": SVA.replace("endmodule", "initial $assertoff;\nendmodule")})[0])
        self.assertTrue(fv.weakening(OLD, {"sva/nnc_chk_rx.sv": SVA.replace("endmodule", "m: assume property (a);\nendmodule")})[0])
        self.assertTrue(fv.weakening(OLD, {"tests/test_uart.py": TEST.replace("@cocotb.test()\nasync def test_chk_005",
                                                                               "@cocotb.test(skip=True)\nasync def test_chk_005")})[0])

    def test_only_existing_verification_files(self):
        self.assertTrue(fv.weakening(OLD, {"formal/nnc_env.sv": "module nnc_env; endmodule"})[0])
        self.assertTrue(fv.weakening(OLD, {"tests/nnc_cocotb.py": "x = 1\n"})[0])

    def test_warnings(self):
        _, warn = fv.weakening(OLD, {"sva/nnc_chk_rx.sv": SVA.replace("disable iff (!i_rst_n) a", "disable iff (!i_rst_n || x) a"),
                                     "tests/test_uart.py": TEST.replace("    assert dut.p.value == 0\n", "    pass\n")})
        self.assertEqual(len(warn), 2)

    def test_comments_do_not_count(self):
        # an assertion that survives only in a comment is removed
        new = {"sva/nnc_chk_rx.sv": SVA.replace("  a_CHK_005_drop", "  // a_CHK_005_drop")}
        self.assertTrue(fv.weakening(OLD, new)[0])

    def test_still_failing_feedback(self):
        faults = [{"id": 1, "failure": "CHK-002 — reset values"}, {"id": 2, "failure": "CHK-003 — delivery"},
                  {"id": 3, "failure": "test_chk_021_low_at_release — CHK-021"}]
        res = {"assertions": {"CHK-002": {"fails": 1, "first_fail_time": 0}, "CHK-003": {"fails": 0}},
               "tests": [{"name": "test_chk_021_low_at_release", "status": "fail", "message": "expected 0x00"}]}
        left = fv.still_failing(faults, res)
        self.assertEqual([x["id"] for x in left], [1, 3])
        self.assertIn("first at 0 ps", left[0]["report"])
        self.assertIn("expected 0x00", left[1]["report"])

    def test_paths(self):
        self.assertEqual(fv.norm_path("./verif/sva/x.sv"), "sva/x.sv")
        self.assertEqual(fv.norm_path("tests\\t.py"), "tests/t.py")


if __name__ == "__main__":
    unittest.main()

"""Formal stage: SVA subset parsing, translation to immediate form, simulation-only detection, status."""
import json
import tempfile
import unittest
from pathlib import Path

from nnc import formal, gen_env

CHK = """module nnc_chk_demo (input logic clk, input logic rst_n, input logic a, input logic b, input logic [3:0] x);
  int unsigned fails_CHK_001 = 0;
  int unsigned fails_CHK_002 = 0;
  int unsigned fails_CHK_003 = 0;
  // CHK-001: a then b
  a_CHK_001: assert property (@(posedge clk) disable iff (!rst_n) a |=> (b ##1 !b))
    else begin fails_CHK_001++; $display("NNC_FAIL CHK-001 @%0t", $time); end
  a_CHK_002_rd: assert property (@(posedge clk) ((x != 0) |-> $stable(x)))
    else begin fails_CHK_002++; $display("NNC_FAIL CHK-002 @%0t", $time); end
  always_ff @(posedge clk) if (rst_n && a && $isunknown(x)) fails_CHK_003++;
  final begin
    $display("NNC_CHECK CHK-001 hits=%0d fails=%0d", 0, fails_CHK_001);
  end
endmodule
"""


class FormalTest(unittest.TestCase):
    def test_parse(self):
        p = formal.parse_property("CHK-001", "@(posedge clk) disable iff (!rst_n) a |=> (b ##1 !b)")
        self.assertEqual((p.clock, p.disable, p.overlap), ("clk", "!rst_n", False))
        self.assertEqual(p.ante, [(0, "a")])
        self.assertEqual(p.cons, [(0, "b"), (1, "!b")])
        p = formal.parse_property("CHK-002", "@(posedge clk) ((x != 0) |-> $stable(x))")
        self.assertEqual((p.ante, p.cons, p.overlap), ([(0, "x != 0")], [(0, "$stable(x)")], True))
        self.assertIn("##[", formal.parse_property("CHK-9", "@(posedge c) a |-> ##[1:3] b").unsupported)
        self.assertIn("until", formal.parse_property("CHK-9", "@(posedge c) a |-> b until c").unsupported)
        self.assertTrue(formal.parse_property("CHK-9", "@(negedge c) a |-> b").unsupported)
        self.assertEqual(formal.parse_property("CHK-9", "@(posedge c) $isunknown(q) |-> b").ante, [(0, "1'b0")])

    def test_formal_view(self):
        view, props = formal.formal_view(CHK)
        self.assertNotIn("assert property", view)
        self.assertNotIn("$display", view)
        self.assertNotIn("final", view)
        self.assertEqual([(p.check, p.label) for p in props],
                         [("CHK-001", "CHK_001"), ("CHK-002", "CHK_002_rd"), ("CHK-003", "CHK_003_procedural")])
        self.assertIn("`ifdef NNC_FV_CHK_001", view)
        self.assertIn("reg [2:1] nnc_fv_s_CHK_001 = '0;", view)              # |=> plus ##1: two stages
        self.assertIn("if (nnc_fv_ok_CHK_001_1) assert (b);", view)
        self.assertIn("if (nnc_fv_ok_CHK_001_2) assert (!b);", view)
        self.assertIn("cover (nnc_fv_ok_CHK_001_0);", view)                   # vacuity of the antecedent
        self.assertIn("`ifdef NNC_FV_CHK_003 assert (1'b0); `endif", view)    # procedural failure point
        self.assertIsNone(formal.nonsynth(view))

    def test_nonsynth(self):
        self.assertIn("queues", formal.nonsynth("logic [7:0] q[$]; always @(posedge c) q.push_back(d);"))
        self.assertIn("simulation time", formal.nonsynth("time t; always @(posedge c) t = $time;"))
        self.assertIn("event", formal.nonsynth("always @(x) n++;"))
        self.assertIsNone(formal.nonsynth("always @(posedge c) q <= d; always @(*) y = q; // time"))

    def test_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            for task, st in (("bmc", "PASS"), ("prove", "PASS"), ("cover", "PASS")):
                (out / f"CHK_001_{task}").mkdir()
                (out / f"CHK_001_{task}" / "status").write_text(f"{st} 0 0")
            self.assertEqual(formal.parse_status(out, "CHK_001")["status"], "PROVEN")
            (out / "CHK_001_cover" / "status").write_text("FAIL 1 0")
            self.assertEqual(formal.parse_status(out, "CHK_001")["status"], "VACUOUS")
            (out / "CHK_001_cover" / "status").write_text("PASS")
            (out / "CHK_001_prove" / "status").write_text("UNKNOWN")
            self.assertEqual(formal.parse_status(out, "CHK_001")["status"], "BOUNDED")
            (out / "CHK_001_bmc" / "status").write_text("FAIL")
            self.assertEqual(formal.parse_status(out, "CHK_001")["status"], "CEX")
            (out / "CHK_001_bmc" / "status").write_text("TIMEOUT")
            self.assertEqual(formal.parse_status(out, "CHK_001")["status"], "TIMEOUT")

    def test_env_validation(self):
        good = "  // ENV-01: idle in reset (R-1)\n  always @(*) if (!rst_n) assume (!a);\n"
        self.assertEqual(gen_env.validate_body(good), [])
        self.assertTrue(gen_env.validate_body(good + "  always @(posedge c) assert (a);\n"))
        self.assertTrue(gen_env.validate_body(good + "  always @(posedge c) assume (a ##1 b);\n"))
        self.assertTrue(gen_env.validate_body("  always @(*) assume (!a);\n"))            # no ENV label


if __name__ == "__main__":
    unittest.main()

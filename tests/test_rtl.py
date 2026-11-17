import json
import tempfile
import unittest
from pathlib import Path

from nnc import gen_rtl, rtlcheck
from nnc.agents.backend import AgentError, AgentResult, _check_inputs

CONTRACT = {"top": "m_cnt", "interface": {
    "parameters": [{"name": "P_W", "default": "8", "legal": "1 to 32"}],
    "ports": [{"name": "i_clk", "direction": "input", "width": "1", "meaning": "clock"},
              {"name": "i_rst_n", "direction": "input", "width": "1", "meaning": "reset"},
              {"name": "i_en", "direction": "input", "width": "1", "meaning": "count enable"},
              {"name": "o_cnt", "direction": "output", "width": "P_W", "meaning": "count"}],
    "clock": "i_clk", "reset": {"name": "i_rst_n", "active_low": True}}}
RULES = {"rules": [{"id": "CN-1-01", "statement": "The counter increments when enabled.", "doc": "cnt.md",
                    "section": "1", "strength": "MUST", "quote": "counts up"},
                   {"id": "CN-1-02", "statement": "Reset clears the counter.", "doc": "cnt.md", "section": "1"}],
         "questions": [{"rules": ["CN-1-01"], "question": "Wrap or saturate?",
                        "decision": {"answer": "Wrap around.", "by": "r"}}]}

GOOD = """// m_cnt: counter (spec section 1)
module m_cnt #(
  parameter int P_W = 8
) (
  input  logic           i_clk,
  input  logic           i_rst_n,
  input  logic           i_en,
  output logic [P_W-1:0] o_cnt
);
  // REQ: CN-1-01, CN-1-02
  always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) o_cnt <= '0;
    else if (i_en) o_cnt <= o_cnt + 1'b1;
  end
endmodule
"""

BAD = """module m_cnt #(parameter int P_W = 8) (input logic i_clk, input logic i_rst_n, input logic i_en,
  output logic [P_W-1:0] o_cnt);
  logic q = 1'b0;
  logic gclk;
  assign gclk = i_clk & i_en;
  always @(posedge i_clk) q <= ~q;          // REQ: XX-9-99
  always_ff @(posedge gclk) o_cnt = o_cnt + 1;
  always_comb begin
    case (q)
      1'b0: gclk_n <= 1'b1;
    endcase
  end
  initial $display("hi");
  /* verilator lint_off UNUSED */
endmodule
"""


def src(text, rules=frozenset({"CN-1-01", "CN-1-02"})):
    files = {"m_cnt.sv": text, "filelist.f": "m_cnt.sv\n"}
    return rtlcheck.check(None, files, CONTRACT, {"P_W": 8}, set(rules))


class SourceRulesTest(unittest.TestCase):
    def test_good_counter_is_clean(self):
        res = src(GOOD)
        self.assertEqual(res["counts"]["error"], 0, res["findings"])
        self.assertEqual(res["counts"]["warning"], 0, res["findings"])
        self.assertEqual(res["trace"]["coverage"], 100.0)

    def test_bad_counter_findings(self):
        rules = {f["rule"] for f in src(BAD)["findings"] if f["severity"] == "error"}
        msgs = " | ".join(f["message"] for f in src(BAD)["findings"])
        for r in ("RR-10", "RR-11", "RR-20", "RR-21", "RR-30", "RR-40", "RR-42"):
            self.assertIn(r, rules, msgs)
        self.assertIn("gclk is not a clock or reset port", msgs)
        self.assertIn("blocking assignment in always_ff", msgs)
        self.assertIn("XX-9-99", msgs)

    def test_file_and_filelist_rules(self):
        res = rtlcheck.check(None, {"other.sv": GOOD, "filelist.f": "x.sv\n"}, CONTRACT, {"P_W": 8}, set())
        msgs = " | ".join(f["message"] for f in res["findings"])
        self.assertIn("name the file m_cnt.sv", msgs)
        self.assertIn("other.sv is not in filelist.f", msgs)
        self.assertIn("names x.sv, which does not exist", msgs)

    def test_simulation_only_block_is_exempt_but_listed(self):
        text = GOOD.replace("endmodule", "`ifndef SYNTHESIS\n  initial $display(\"model\");\n`endif\nendmodule")
        res = src(text)
        self.assertEqual(res["counts"]["error"], 0, res["findings"])
        self.assertTrue(any(f["severity"] == "info" and "simulation-only" in f["message"] for f in res["findings"]))

    def test_waiver_needs_reason(self):
        text = GOOD.replace("  // REQ:", "  // WAIVER: i_en bit kept for the spec\n  /* verilator lint_off UNUSED */\n  // REQ:")
        res = src(text)
        self.assertEqual(res["counts"]["error"], 0, res["findings"])
        self.assertEqual(len(res["trace"]["waivers"]), 1)

    def test_interface_findings(self):
        ports = {"i_clk": {"direction": "input", "bits": 1}, "i_rst_n": {"direction": "input", "bits": 1},
                 "o_cnt": {"direction": "output", "bits": 4}, "o_extra": {"direction": "output", "bits": 1}}
        msgs = " | ".join(f["message"] for f in rtlcheck.interface_findings(ports, CONTRACT["interface"], {"P_W": 8}, GOOD))
        self.assertIn("port i_en of the contract is missing", msgs)
        self.assertIn("port o_extra is not in the contract", msgs)
        self.assertIn("o_cnt: 4 bits, contract says 8", msgs)
        msgs = " | ".join(f["message"] for f in rtlcheck.interface_findings(
            ports, CONTRACT["interface"], {"P_W": 8}, GOOD.replace("P_W = 8", "P_X = 8")))
        self.assertIn("parameter P_W of the contract is not a parameter", msgs)


class FakeBackend:
    def __init__(self, answers):
        self.answers = list(answers)
        self.tasks = []

    def run(self, task, log_dir):
        _check_inputs(task)
        self.tasks.append(task)
        return AgentResult(self.answers.pop(0), "fake", None, 0.5, {})


class GenRtlTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "cnt"
        (self.root / "spec").mkdir(parents=True)
        (self.root / "verif" / "tests").mkdir(parents=True)
        (self.root / "spec" / "cnt.md").write_text("# Counter\nIt counts up.\n", encoding="utf-8")
        (self.root / "verif" / "tests" / "test_cnt.py").write_text("secret = 1\n", encoding="utf-8")
        self.final = {"values": {"P_W": 8}, "notes": {}}

    def tearDown(self):
        self._tmp.cleanup()

    def test_repairs_until_clean_and_never_sees_verification(self):
        be = FakeBackend([{"files": [{"name": "m_cnt.sv", "content": BAD}], "filelist": ["m_cnt.sv"], "open_points": []},
                          {"files": [{"name": "m_cnt.sv", "content": GOOD}], "filelist": ["m_cnt.sv"],
                           "open_points": ["wrap chosen (decision)"]}])
        rep = gen_rtl.generate(self.root, CONTRACT, RULES, self.final, [self.root / "spec" / "cnt.md"], be,
                               self.root / "logs", None, rounds=2)
        self.assertEqual(rep["status"], "source_clean")
        self.assertEqual(rep["attempts"], 2)
        first, second = be.tasks
        self.assertEqual(set(first.inputs), {"spec/cnt.md", "REQUIREMENTS.md", "INTERFACE.md", "RTL_RULES.md"})
        self.assertIn("current/m_cnt.sv", second.inputs)
        self.assertIn("RR-20", second.instructions)            # problems fed back
        for t in be.tasks:
            self.assertFalse(any("verif" in str(p) for p in t.inputs.values()))
            self.assertNotIn("CHK-", t.instructions)
        req = (self.root / "work" / "rtl_gen" / "REQUIREMENTS.md").read_text(encoding="utf-8")
        self.assertIn("Wrap around.", req)
        md = gen_rtl.to_markdown(rep, "cnt", RULES)
        self.assertIn("D2_rtl", md)

    def test_sandbox_refuses_verification_inputs(self):
        from nnc.agents.backend import AgentTask
        task = AgentTask("A15_x", "x", gen_rtl.SCHEMA, inputs={"t.py": self.root / "verif" / "tests" / "test_cnt.py"},
                         forbidden=[self.root / "verif"], tools=("Read",))
        with self.assertRaises(AgentError):
            _check_inputs(task)

    def test_fault_text_keeps_only_spec_level_rtl_faults(self):
        tri = [{"failure": "test_chk_021_x — CHK-021: AR handshakes expected 42 got 26", "most_likely": "A_rtl_wrong",
                "spec_says": "spec:143 REQ-FUNC-003 exactly one AR. verif/tests/test_x.py:700 counts beats.",
                "rtl_does": "ahb_if.sv:88 reads o_rsp_ready before it is assigned.", "test_does": "secret test"},
               {"failure": "test_b", "most_likely": "B_test_wrong", "spec_says": "s", "rtl_does": "r"}]
        out = gen_rtl.fault_text(tri)
        self.assertEqual(len(out), 1)
        self.assertNotIn("verif/", json.dumps(out))
        self.assertNotIn("secret", json.dumps(out))
        self.assertTrue(out[0]["fault"].startswith("CHK-021"))


if __name__ == "__main__":
    unittest.main()

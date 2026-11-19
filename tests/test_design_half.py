import json
import tempfile
import unittest
from pathlib import Path

from nnc import derive, equiv, export, specdraft
from nnc.project import Design

IFACE = {"parameters": [{"name": "P_W", "default": "8", "legal": "1 to 32"}],
         "ports": [{"name": "i_clk", "direction": "input", "width": "1"},
                   {"name": "i_rst_n", "direction": "input", "width": "1"},
                   {"name": "i_d", "direction": "input", "width": "P_W"},
                   {"name": "o_q", "direction": "output", "width": "P_W"}],
         "clock": "i_clk", "reset": {"name": "i_rst_n", "active_low": True}}

SPEC = """# Counter Design Specification

## 1 Overview
### 1.1 Purpose
The block counts.

## 4 Parameters

| Parameter | Default | Legal values | Description |
|---|---|---|---|
| PARA_W | 8 | 1 to 32 | Width |

## 5 Interface

**`m_cnt`**: all ports (CLK)

| Port | Direction | Width | Signal type | Reset value | Clock domain | Meaning |
|---|---|---|---|---|---|---|
| i_clk | input | 1 | Clock | Not applicable | CLK | Clock |
| i_rst_n | input | 1 | Reset | Not applicable | CLK | Active-low reset |
| i_en | input | 1 | Data | 0 | CLK | Enable |
| o_cnt | output | PARA_W | Data | 0 | CLK | Count |

## 6 Clocks and resets
[REQ-RST-001] The reset shall clear o_cnt.

## 7 Functional description
[REQ-FUNC-001] The block shall increment o_cnt when i_en is 1.
[REQ-FUNC-002] The block shall keep o_cnt when i_en is 0.
[REQ-FUNC-003] The block shall wrap from the maximum value to 0.
[REQ-FUNC-004] The block shall update o_cnt on the rising edge of i_clk.

## 10 Errors and corner cases
There are no errors.

## 11 Configurations
CFG-BASE uses the defaults.

## 12 Verification requirements
The environment shall hold i_en stable around the clock edge.
"""


class EquivTest(unittest.TestCase):
    def test_wrapper_assumes_reset_in_first_step(self):
        w = equiv.wrapper(IFACE, {"P_W": 8}, [IFACE["reset"]])
        self.assertIn("input logic [7:0] in_i_d", w)
        self.assertNotIn("in_o_q", w)                        # outputs are compared inside the miter
        self.assertIn("if (nnc_init) assume (!in_i_rst_n)", w)

    def test_build_reads_both_sides_with_parameters(self):
        files, script = equiv.build({"top": "m_x", "interface": IFACE}, {"P_W": 8}, {"a.sv": "x"}, ["a.sv"],
                                    {"b.sv": "y"}, ["b.sv"], defines=["X_SYNTHESIS"])
        ys = files["nnc_miter.ys"]
        self.assertIn("read_verilog -sv -DX_SYNTHESIS gold/a.sv", ys)
        self.assertIn("read_verilog -sv -DX_SYNTHESIS gate/b.sv", ys)
        self.assertEqual(ys.count("chparam -set P_W 8 m_x"), 2)
        self.assertIn("miter -equiv -flatten -make_assert nnc_gold nnc_gate nnc_miter", ys)
        self.assertIn("prove: abc pdr", files["eq.sby"])

    def test_cex_outputs_names_the_first_difference(self):
        vcd = """$scope module nnc_eq_top $end
$scope module u_miter $end
$var wire 8 a gold_o_q $end
$var wire 8 b gate_o_q $end
$upscope $end
$upscope $end
#0
b0 a
b0 b
#10
b1 a
b0 b
#20
"""
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "t.vcd"
            p.write_text(vcd, encoding="utf-8")
            msg = equiv.cex_outputs(str(p), {"interface": IFACE})
        self.assertIn("step 1", msg)
        self.assertIn("o_q (original 1, rewritten 0)", msg)


class SpecCheckTest(unittest.TestCase):
    def test_minimal_spec_reads(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "cnt.md"
            p.write_text(SPEC, encoding="utf-8")
            res = specdraft.check_spec(p, "m_cnt")
            self.assertEqual(res["ports"], 4)
            self.assertEqual(res["parameters"], 1)
            self.assertEqual(res["requirements"], 5)
            self.assertFalse([f for f in res["findings"] if f["severity"] == "error"], res["findings"])
            p.write_text(SPEC.replace("| 1 to 32 |", "| sensible values |").replace("[REQ-FUNC-002]", "[REQ-FUNC-001]")
                         .replace("| o_cnt | output | PARA_W |", "| o_cnt | output | PARA_Q |"), encoding="utf-8")
            msgs = " | ".join(f["message"] for f in specdraft.check_spec(p, "m_cnt")["findings"])
            self.assertIn("not in a form the flow can check", msgs)
            self.assertIn("defined more than once: REQ-FUNC-001", msgs)
            self.assertIn("width 'PARA_Q'", msgs)


class FaultTextTest(unittest.TestCase):
    def test_formal_fault_hides_the_verification(self):
        from nnc import gen_rtl
        got = gen_rtl.fault_text([
            {"check": "CHK-010 (a_CHK_010, verif/sva/nnc_chk_wr.sv:79-82)", "most_likely": "A_rtl_wrong",
             "spec_says": "spec:527 block is busy OR sw low. The checker nnc_chk_wr.sv:38 uses the same term.",
             "rtl_does": "rtl/m_wr.sv:135 adds a third term. See verif/sva/nnc_chk_wr.sv for the model."},
            {"check": "CHK-008 (a_CHK_008, verif/sva/x.sv:1)", "most_likely": "B_checker_wrong"}])
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["fault"], "formal counterexample on CHK-010")
        self.assertEqual(got[0]["spec_says"], "spec:527 block is busy OR sw low.")
        self.assertEqual(got[0]["rtl_does"], "rtl/m_wr.sv:135 adds a third term.")


class ExportAndDeriveTest(unittest.TestCase):
    def test_export_sources_skip_standards_and_missing(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / "ip"
            (root / "work").mkdir(parents=True)
            (root / "work" / "report.md").write_text("# r\n", encoding="utf-8")
            docs = [{"file": "spec/ip.md", "role": "ip_spec"}, {"file": "spec/standards/arm.md", "role": "standard"}]
            got = export.sources(root, docs, ["spec", "report", "rules"])
            self.assertEqual([n for n, _ in got], ["spec", "report"])
            with self.assertRaises(ValueError):
                export.sources(root, docs, ["standards"])

    def test_derive_carries_identical_approvals_and_leaves_rtl(self):
        with tempfile.TemporaryDirectory() as t:
            src = Design.init(Path(t) / "orig")
            (src.root / "spec" / "ip.md").write_text("# spec\n", encoding="utf-8")
            src.add_document("spec/ip.md", "ip_spec", "IP")
            (src.work / "rules.json").write_text('{"rules": []}', encoding="utf-8")
            (src.work / "contract.json").write_text("{}", encoding="utf-8")
            (src.root / "verif" / "tests" / "test_orig.py").write_text("x = 1\n", encoding="utf-8")
            (src.root / "rtl" / "m.sv").write_text("module m; endmodule\n", encoding="utf-8")
            for g in ("G1_rules", "G2_contract", "G3_verif_sources"):
                src.approve(g, by="r")
            dst = derive.derive(src.root, Path(t) / "gen")
            st = {s.gate: s.state for s in dst.status()}
            self.assertEqual([st[g] for g in ("G1_rules", "G2_contract", "G3_verif_sources")], ["APPROVED"] * 3)
            self.assertEqual(st["D1_config"], "PENDING")
            self.assertFalse(any((dst.root / "rtl").iterdir()))
            state = json.loads((dst.root / "nnc_state.json").read_text(encoding="utf-8"))
            self.assertIn("carried over from orig", state["gates"]["G1_rules"]["note"])
            self.assertEqual(state["config"]["derived_from"], "orig")


if __name__ == "__main__":
    unittest.main()

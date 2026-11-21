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

    def test_configs_and_merge(self):
        runs = [{"config": "base", "params": {}}, {"config": "off", "params": {}},
                {"config": "apb5", "params": {"P_APB5": 1}}]
        self.assertEqual(formal.formal_configs(runs), [{"name": "base", "params": {}},
                                                       {"name": "apb5", "params": {"P_APB5": 1}}])
        self.assertEqual(formal.formal_configs(None), [{"name": "default", "params": {}}])

        def r(**st):
            return {"depth": 20, "checks": {k.replace("_", "-"): {"status": v} for k, v in st.items()},
                    "by_status": {}}
        m = formal.merge_configs({"base": r(CHK_001="PROVEN", CHK_002="VACUOUS", CHK_003="PROVEN", CHK_004="PROVEN"),
                                  "apb5": r(CHK_001="BOUNDED", CHK_002="PROVEN", CHK_003="CEX", CHK_004="VACUOUS")})
        st = {k: v["status"] for k, v in m["checks"].items()}
        self.assertEqual(st, {"CHK-001": "BOUNDED", "CHK-002": "PROVEN", "CHK-003": "CEX", "CHK-004": "PROVEN"})
        self.assertEqual(m["checks"]["CHK-003"]["config"], "apb5")
        self.assertEqual(m["checks"]["CHK-002"]["per_config"], {"base": "VACUOUS", "apb5": "PROVEN"})
        m = formal.merge_configs({"a": r(CHK_001="VACUOUS"), "b": r(CHK_001="VACUOUS")})
        self.assertEqual(m["checks"]["CHK-001"]["status"], "VACUOUS")

    def test_one_config(self):
        rec = {"depth": 20, "by_status": {}, "configs": {}, "checks": {
            "CHK-001": {"status": "BOUNDED", "per_config": {"base": "VACUOUS", "min": "BOUNDED"}},
            "CHK-002": {"status": "PROVEN", "per_config": {"min": "PROVEN"}}}}
        base = formal.one_config(rec, "base")
        self.assertEqual(base["checks"], {"CHK-001": {"status": "VACUOUS", "per_config": {"base": "VACUOUS"}}})
        self.assertEqual((base["by_status"], base["depth"]), ({"VACUOUS": 1}, 20))
        single = {"depth": 20, "by_status": {}, "checks": {"CHK-001": {"status": "PROVEN"}}}  # a run of one config
        got = formal.one_config(single, "base")
        fails, notes = formal.compare_recorded(base, got)
        self.assertEqual(fails, ["CHK-001 [base]: recorded VACUOUS, rerun PROVEN"])
        got["checks"]["CHK-001"] = {"status": "VACUOUS", "per_config": {"base": "VACUOUS"}}
        self.assertEqual(formal.compare_recorded(base, got), ([], []))

    def test_depth_escalation_of_vacuous_checks(self):
        from nnc.simhost import RunResult, SimHost

        class DepthHost(SimHost):
            """CHK-001 is reachable only from depth 80; CHK-002 at any depth."""
            def __init__(self):
                self.depths = []

            def run(self, files, script, outputs, timeout_s=1800, tag="run"):
                out = Path(tempfile.mkdtemp())
                for name, text in files.items():
                    if not name.endswith(".sby"):
                        continue
                    tag_ = name[:-4]
                    depth = int(next(l.split()[1] for l in str(text).splitlines() if l.startswith("depth ")))
                    self.depths.append((tag_, depth))
                    cover = "PASS" if tag_ != "CHK_001" or depth >= 80 else "FAIL"
                    for task, st in (("bmc", "PASS"), ("prove", "PASS"), ("cover", cover)):
                        (out / f"{tag_}_{task}").mkdir()
                        (out / f"{tag_}_{task}" / "status").write_text(st)
                return RunResult(0, "", out)

        contract = {"top": "m_demo", "checks": [], "interface": {
            "clock": "clk", "reset": {"name": "rst_n", "active_low": True}, "parameters": [],
            "ports": [{"name": n, "direction": "input", "width": "1"} for n in ("clk", "rst_n", "a", "b")]}}
        with tempfile.TemporaryDirectory() as tmp:
            rtl, sva = Path(tmp) / "rtl", Path(tmp) / "sva"
            rtl.mkdir()
            sva.mkdir()
            (rtl / "m_demo.sv").write_text("module m_demo(input logic clk, rst_n, a, b); endmodule\n")
            (sva / "nnc_chk_demo.sv").write_text(CHK)
            host = DepthHost()
            res = formal.run(host, contract, rtl, sva, None, depth=20, max_depth=100)
            self.assertEqual(res["checks"]["CHK-001"]["status"], "PROVEN")
            self.assertEqual((res["checks"]["CHK-001"]["depth"], res["checks"]["CHK-001"]["escalated_from"]), (80, 20))
            self.assertNotIn("depth", res["checks"]["CHK-002"])
            self.assertEqual(sorted(d for t, d in host.depths if t == "CHK_001"), [20, 40, 80])
            self.assertEqual([d for t, d in host.depths if t == "CHK_002"], [20])        # only the vacuous one again
            res = formal.run(DepthHost(), contract, rtl, sva, None, depth=20)            # default: no escalation
            self.assertEqual(res["checks"]["CHK-001"]["status"], "VACUOUS")

    def test_slang_frontend_reads_only_the_rtl(self):
        contract = {"top": "m_demo", "checks": [], "interface": {
            "clock": "clk", "reset": {"name": "rst_n", "active_low": True}, "parameters": [],
            "ports": [{"name": n, "direction": "input", "width": "1"} for n in ("clk", "rst_n", "a", "b")]}}
        with tempfile.TemporaryDirectory() as tmp:
            rtl, sva = Path(tmp) / "rtl", Path(tmp) / "sva"
            rtl.mkdir()
            sva.mkdir()
            (rtl / "pkg.sv").write_text("package p; endpackage\n")
            (rtl / "m_demo.sv").write_text("module m_demo(input logic clk, rst_n, a, b); endmodule\n")
            (rtl / "filelist.f").write_text("pkg.sv\nm_demo.sv\n")
            (sva / "nnc_chk_demo.sv").write_text(CHK)
            files, _ = formal.build(contract, rtl, sva, None, defines=["SYNTHESIS"], frontend="slang")
            script = files["CHK_001.sby"]
            self.assertIn("read_slang -DSYNTHESIS --top m_demo pkg.sv m_demo.sv\n", script)
            line = next(l for l in script.splitlines() if l.startswith("read_verilog"))
            self.assertIn("-DNNC_FV_CHK_001", line)
            self.assertIn("nnc_chk_demo.sv", line)
            self.assertNotIn("m_demo.sv", line.replace("nnc_chk_demo.sv", ""))
            plain, _ = formal.build(contract, rtl, sva, None)
            self.assertNotIn("read_slang", plain["CHK_001.sby"])
            with self.assertRaises(ValueError):
                formal.build(contract, rtl, sva, None, frontend="other")

    def test_slang_frontend_sets_dut_parameters_with_G(self):
        """read_slang elaborates the DUT, so a configuration's parameters go to read_slang (-G) and the formal
        top instantiates the DUT without overrides (ot_gpio: "does not have a parameter named ...")."""
        contract = {"top": "m_demo", "checks": [], "interface": {
            "clock": "clk", "reset": {"name": "rst_n", "active_low": True},
            "parameters": [{"name": "W", "default": "1"}],
            "ports": [{"name": n, "direction": "input", "width": "1"} for n in ("clk", "rst_n", "a", "b")]}}
        with tempfile.TemporaryDirectory() as tmp:
            rtl, sva = Path(tmp) / "rtl", Path(tmp) / "sva"
            rtl.mkdir()
            sva.mkdir()
            (rtl / "m_demo.sv").write_text("module m_demo #(parameter W = 1) (input logic clk, rst_n, a, b); endmodule\n")
            (sva / "nnc_chk_demo.sv").write_text(CHK)
            files, _ = formal.build(contract, rtl, sva, None, params={"W": 0}, frontend="slang")
            self.assertIn("read_slang  --top m_demo -G W=0 m_demo.sv\n", files["CHK_001.sby"])
            self.assertIn("chparam -set W 0 nnc_fv_top", files["CHK_001.sby"])
            top = files["src/nnc_fv_top.sv"]
            self.assertIn("  m_demo u_dut (", top)
            self.assertIn("nnc_chk_demo #(.W(W)) u_nnc_chk_demo", top)       # checkers keep the parameter
            plain, _ = formal.build(contract, rtl, sva, None, params={"W": 0})
            self.assertIn("  m_demo #(.W(W)) u_dut (", plain["src/nnc_fv_top.sv"])
            self.assertNotIn("-G", plain["CHK_001.sby"])

    def test_falling_clock_checker_is_simulation_only_with_one_clock(self):
        clocks = formal.clock_names({"clock": "clk", "clocks": [{"name": "clk"}, "clk2"]})
        self.assertEqual(clocks, {"clk", "clk2"})
        self.assertIsNotNone(formal.falling_clock("always_ff @(negedge clk) q <= d;", clocks))
        self.assertIsNone(formal.falling_clock("always_ff @(posedge clk or negedge rst_n) q <= d;", clocks))
        self.assertIsNone(formal.falling_clock("// always_ff @(negedge clk)\n", clocks))
        self.assertIsNone(formal.falling_clock("always_ff @(negedge clk_x) q <= d;", clocks))
        contract = {"top": "m_demo", "checks": [], "interface": {
            "clock": "clk", "reset": {"name": "rst_n", "active_low": True}, "parameters": [],
            "ports": [{"name": n, "direction": "input", "width": "1"} for n in ("clk", "rst_n", "a", "b")]}}
        with tempfile.TemporaryDirectory() as tmp:
            rtl, sva = Path(tmp) / "rtl", Path(tmp) / "sva"
            rtl.mkdir()
            sva.mkdir()
            (rtl / "m_demo.sv").write_text("module m_demo(input logic clk, rst_n, a, b); endmodule\n")
            (sva / "nnc_chk_demo.sv").write_text(CHK.replace("endmodule", "  logic s;\n  always_ff @(negedge clk) s <= a;\nendmodule"))
            files, props = formal.build(contract, rtl, sva, None)
            self.assertNotIn("CHK_001.sby", files)
            self.assertTrue(all("falling clock edge" in p.unsupported for p in props))
            self.assertNotIn("src/nnc_chk_demo.sv", files)

    def test_spec_lint_references(self):
        from nnc import speclint
        files = {"Spec.md": ["l1", "l2", "l3"]}
        self.assertTrue(speclint.ref_ok("spec/Spec.md:2", files))
        self.assertTrue(speclint.ref_ok("Spec.md:1-3", files))
        self.assertFalse(speclint.ref_ok("spec/Spec.md:9", files))
        self.assertFalse(speclint.ref_ok("spec/Other.md:1", files))
        self.assertFalse(speclint.ref_ok("section 10.7", files))

    def test_env_validation(self):
        good = "  // ENV-01: idle in reset (R-1)\n  always @(*) if (!rst_n) assume (!a);\n"
        self.assertEqual(gen_env.validate_body(good), [])
        self.assertTrue(gen_env.validate_body(good + "  always @(posedge c) assert (a);\n"))
        self.assertTrue(gen_env.validate_body(good + "  always @(posedge c) assume (a ##1 b);\n"))
        self.assertTrue(gen_env.validate_body("  always @(*) assume (!a);\n"))            # no ENV label

    def test_env_prompt_shows_rule_conditions(self):
        contract = {"top": "m", "interface": {"clock": "clk", "reset": {"name": "rst_n", "active_low": True},
                                              "parameters": [], "ports": [
            {"name": n, "direction": "input", "width": "1", "meaning": ""} for n in ("clk", "rst_n", "v")]}}
        rules = {"rules": [{"id": "R-1", "statement": "The test bench keeps v = 0.",
                            "condition": "rst_n = 0 and first cycle after release"},
                           {"id": "R-2", "statement": "v is a request.", "condition": ""}]}
        prompt = gen_env.build_prompt(contract, rules)
        self.assertIn("R-1: The test bench keeps v = 0. WHEN rst_n = 0 and first cycle after release\n", prompt)
        self.assertIn("R-2: v is a request.\n", prompt)


if __name__ == "__main__":
    unittest.main()

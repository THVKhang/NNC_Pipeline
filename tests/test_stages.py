"""Unit tests of the deterministic parts of every stage (no LLM, no simulator)."""
import json
import tempfile
import unittest
from pathlib import Path

from nnc import gen_sva, gen_tests, mutate, report, review, sim
from nnc.agents.backend import AgentResult
from nnc.contract import contract_shell, extract_interface, module_header, width_decl
from nnc.ingest import build_index
from nnc.project import Design, ProjectError

MD_SPEC = """---
title: test
---
# Demo bridge spec

## 1. Requirements

| ID | Requirement |
|---|---|
| REQ-FUNC-001 | The bridge shall assert o_ready for one cycle. |
| REQ-FUNC-002 | The bridge may ignore i_prot. |

Plain text that is descriptive. The bridge must keep o_valid high until i_ready.

- first item must hold
- second item is free

```systemverilog
module ignored; endmodule
```

### 1.1 Ports

| Port | Direction | Width | Meaning | Signal type | Reset value |
|---|---|---|---|---|---|
| i_clk | Input | 1 | Clock | Clock | n/a |
| i_rst_n | Input | 1 | Active-low reset | Reset | n/a |
| i_addr | Input | PARA_ADDR_W | Address | Data | n/a |
| o_data | Output (flop) | 32 | Data | Data | 0 |

## 2. Parameters

| Parameter | Default | Legal values |
|---|---|---|
| PARA_ADDR_W | 32 | 16 to 32 |
"""

RTL = """
module m_demo #(
  parameter logic [31:0] PARA_ADDR_W = 32
) (
  input  wire i_clk,
  input  wire i_rst_n, // reset
  input  wire [PARA_ADDR_W-1:0] i_addr,
  output logic [31:0] o_data
);
  always_ff @(posedge i_clk or negedge i_rst_n)
    if (!i_rst_n) o_data <= '0;
    else if (i_addr == 0 && i_rst_n) o_data <= 32'd1;
  assign x = 1'b1;
endmodule
"""


class Workspace(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.spec = self.tmp / "spec.md"
        self.spec.write_text(MD_SPEC, encoding="utf-8")
        self.index = build_index(self.spec)
        self.iface = extract_interface(self.index)

    def tearDown(self):
        self._tmp.cleanup()


class MarkdownIngestTest(Workspace):
    def test_sections_tables_and_sentences(self):
        secs = {s["id"]: s for s in self.index["sections"]}
        self.assertEqual(list(secs), ["front", "T1", "1", "1.1", "2"])
        texts = [s["text"] for s in secs["1"]["sentences"]]
        self.assertEqual(texts[0], "ID: REQ-FUNC-001; Requirement: The bridge shall assert o_ready for one cycle.")
        self.assertIn("The bridge must keep o_valid high until i_ready.", texts)
        self.assertIn("first item must hold", texts)
        self.assertFalse(any("ignored" in t for t in texts))           # code block skipped
        self.assertEqual(len(self.index["tables"]), 3)
        self.assertEqual(self.index["doc"]["location"], "line")
        self.assertIn("PARA_ADDR_W", self.index["signals"])
        self.assertNotIn("REQ", self.index["signals"])                  # not a fragment of REQ-FUNC-001
        self.assertNotIn("FUNC", self.index["signals"])

    def test_interface_from_tables(self):
        self.assertEqual([p["name"] for p in self.iface["ports"]], ["i_clk", "i_rst_n", "i_addr", "o_data"])
        self.assertEqual(self.iface["clock"], "i_clk")
        self.assertEqual(self.iface["reset"], {"name": "i_rst_n", "active_low": True})
        self.assertEqual(self.iface["parameters"][0]["name"], "PARA_ADDR_W")
        self.assertEqual(self.iface["ports"][3]["direction"], "output")

    def test_widths_and_headers(self):
        self.assertEqual(width_decl("1"), "")
        self.assertEqual(width_decl("32"), "[31:0]")
        self.assertEqual(width_decl("PARA_ADDR_W"), "[(PARA_ADDR_W)-1:0]")
        hdr = module_header("chk", self.iface, all_inputs=True)
        self.assertIn("parameter int PARA_ADDR_W = 32", hdr)
        self.assertNotIn("output", hdr)
        self.assertIn("assign o_data = '0;", contract_shell("m_demo", self.iface))


class SimIntegrationTest(Workspace):
    def setUp(self):
        super().setUp()
        (self.tmp / "rtl").mkdir()
        self.rtl = self.tmp / "rtl" / "m_demo.sv"
        self.rtl.write_text(RTL, encoding="utf-8")
        self.contract = {"top": "m_demo", "interface": self.iface, "checks": []}

    def test_dut_ports_and_conformance(self):
        ports = sim.dut_ports([self.rtl], "m_demo")
        self.assertEqual([(p["name"], p["direction"]) for p in ports],
                         [("i_clk", "input"), ("i_rst_n", "input"), ("i_addr", "input"), ("o_data", "output")])
        self.assertEqual(sim.conformance(self.contract, ports), [])
        bad = [p for p in ports if p["name"] != "o_data"] + [{"name": "o_dat", "direction": "output"}]
        issues = sim.conformance(self.contract, bad)
        self.assertEqual(len(issues), 2)

    def test_tb_top_and_inputs(self):
        top = sim.tb_top(self.contract, ["nnc_chk_a"])
        self.assertIn("m_demo #(.PARA_ADDR_W(PARA_ADDR_W)) u_dut", top)
        self.assertIn("nnc_chk_a #(.PARA_ADDR_W(PARA_ADDR_W)) u_nnc_chk_a", top)
        files = sim.build_inputs(self.contract, [self.rtl], [], self.tmp / "test_x.py", {"PARA_ADDR_W": 16})
        self.assertIn("-GPARA_ADDR_W=16", files["Makefile"])
        self.assertEqual(json.loads(files["nnc_interface.json"])["parameters"], {"PARA_ADDR_W": 16})

    def test_parse_results(self):
        out = self.tmp / "out"
        out.mkdir()
        (out / "results.xml").write_text(
            '<testsuites><testsuite><testcase name="test_chk_001_a" classname="t"/>'
            '<testcase name="test_chk_002_b" classname="t"><failure message="boom"/></testcase>'
            '</testsuite></testsuites>', encoding="utf-8")
        (out / "sim.log").write_text(
            "0.00ns INFO cocotb.regression running t.test_chk_002_b (2/2)\nTraceback (most recent call last):\n"
            '  File "t.py", line 3\nAttributeError: no attribute foo\n'
            "NNC_FAIL CHK-010 @120\nNNC_CHECK CHK-010 hits=4 fails=1\nNNC_CHECK CHK-011 hits=0 fails=0\nNNC_MAKE_RC=2\n",
            encoding="utf-8")
        (out / "coverage.info").write_text("SF:/x/rtl/m_demo.sv\nDA:1,3\nDA:2,0\nend_of_record\nSF:/x/nnc_tb_top.sv\nDA:1,5\n",
                                           encoding="utf-8")
        r = sim.parse_results(out, ["m_demo.sv"])
        self.assertEqual([t["status"] for t in r["tests"]], ["pass", "fail"])
        self.assertEqual(r["tests"][1]["exception"], "AttributeError")
        self.assertEqual(r["assertions"]["CHK-010"], {"hits": 4, "fails": 1, "first_fail_time": 120})
        self.assertEqual(r["coverage"]["percent"], 50.0)                 # testbench lines excluded
        self.assertEqual(gen_tests.infrastructure_errors(r)[0].split(":")[0], "test_chk_002_b")
        lib = dict(r["tests"][1], traceback='File "/x/test.py", line 3\nFile "/x/nnc_cocotb.py", line 29\n')
        self.assertEqual(gen_tests.infrastructure_errors({"tests": [lib]}), [])   # helper fault: not the test's
        self.assertEqual(len(gen_tests.library_errors({"tests": [lib]})), 1)

    def test_mutation_candidates(self):
        cands = mutate.candidates([self.rtl])
        ops = {c.operator for c in cands}
        self.assertTrue({"eq_to_ne", "and_to_or", "one_to_zero", "negate_if"} <= ops)
        neg = next(c for c in cands if c.operator == "negate_if" and "i_addr" in c.original)
        self.assertIn("if (!(i_addr == 0 && i_rst_n))", neg.mutated)
        self.assertFalse(any("parameter" in c.original for c in cands))
        picked = mutate.select(cands, 3, seed=7)
        self.assertEqual([m.id for m in picked], ["M01", "M02", "M03"])
        self.assertEqual([m.line for m in picked], [m.line for m in mutate.select(mutate.candidates([self.rtl]), 3, seed=7)])

    def test_mutation_ignores_baseline_failures(self):
        base = mutate.baseline_failures({"tests": [{"name": "t_a", "status": "fail"}, {"name": "t_b", "status": "pass"}],
                                         "assertions": {"CHK-001": {"fails": 3}, "CHK-002": {"fails": 0}}})
        same = {"built": True, "tests": [{"name": "t_a", "status": "fail"}, {"name": "t_b", "status": "pass"}],
                "assertions": {"CHK-001": {"fails": 5}, "CHK-002": {"fails": 0}}}
        self.assertEqual(mutate.classify(same, base)["status"], "survived")   # only baseline failures
        new = {**same, "assertions": {"CHK-001": {"fails": 5}, "CHK-002": {"fails": 1}}}
        self.assertEqual(mutate.classify(new, base), {"status": "killed", "killed_by_tests": [],
                                                      "killed_by_checks": ["CHK-002"]})
        self.assertEqual(mutate.classify({**same, "built": False}, base)["status"], "not_compiled")


class GeneratorValidationTest(Workspace):
    def test_sva_scaffold_and_validation(self):
        checks = [{"id": "CHK-001", "title": "t", "behavior": "b", "rules": []}]
        head, tail = gen_sva.scaffold("apb", self.iface, checks)
        self.assertIn("int unsigned fails_CHK_001 = 0;", head)
        self.assertIn('NNC_CHECK CHK-001 hits=%0d fails=%0d', tail)
        good = ("a_CHK_001: assert property (@(posedge i_clk) disable iff (!i_rst_n) o_data == 0 |-> 1)\n"
                "  else begin fails_CHK_001++; end\n"
                "always_ff @(posedge i_clk) if (i_rst_n) hits_CHK_001 <= hits_CHK_001 + 1;")
        self.assertEqual(gen_sva.validate_body(good, checks), [])
        self.assertTrue(gen_sva.validate_body("module x; endmodule // verilator lint_off", checks))

    def test_tests_validation_and_map(self):
        contract = {"checks": [{"id": "CHK-002", "kind": "test"}, {"id": "CHK-003", "kind": "test"}]}
        code = ('import cocotb\nfrom nnc_cocotb import *\n@cocotb.test()\nasync def test_chk_002_x(dut):\n'
                '    """CHK-002 CHK-003: both."""\n@cocotb.test()\nasync def test_regression_random(dut):\n    pass\n')
        self.assertEqual(gen_tests.validate(code, contract), [])
        self.assertEqual(gen_tests.test_check_map(code)["test_chk_002_x"], ["CHK-002", "CHK-003"])
        self.assertTrue(any("CHK-003" in p for p in gen_tests.validate(code.replace("CHK-003", ""), contract)))
        self.assertTrue(gen_tests.validate("def broken(:", contract))
        self.assertTrue(any("hierarchical" in p for p in gen_tests.validate(code + "x = dut.u_core\n", contract)))


class ReportTest(unittest.TestCase):
    def test_statuses(self):
        contract = {"checks": [
            {"id": "CHK-001", "kind": "assertion", "rules": ["R1"]}, {"id": "CHK-002", "kind": "assertion", "rules": ["R2"]},
            {"id": "CHK-003", "kind": "assertion", "rules": ["R2"]}, {"id": "CHK-004", "kind": "test", "rules": ["R3"]}],
            "not_verified": [{"rule": "R4", "reason": "static_or_structural", "note": ""}]}
        results = {"status": "ran", "assertions": {"CHK-001": {"hits": 5, "fails": 0}, "CHK-002": {"hits": 0, "fails": 0},
                                                   "CHK-003": {"hits": 3, "fails": 0}},
                   "tests": [{"name": "test_errors", "status": "fail"}]}
        st = report.check_status(results, contract, {"test_errors": ["CHK-004"]})
        self.assertEqual({k: v["status"] for k, v in st.items()},
                         {"CHK-001": "PASS", "CHK-002": "NOT_HIT", "CHK-003": "PASS", "CHK-004": "FAIL"})
        rules = {"rules": [{"id": i, "section": "1", "sentences": [], "strength": "MUST", "statement": "s"}
                           for i in ("R1", "R2", "R3", "R4", "R5")]}
        rows = {r["rule"]: r["status"] for r in report.rtm(rules, contract, st)}
        self.assertEqual(rows, {"R1": "VERIFIED", "R2": "PARTIAL", "R3": "FAILED", "R4": "NOT_VERIFIED_BY_SIM",
                                "R5": "UNMAPPED"})
        self.assertEqual(report.check_status(None, contract)["CHK-001"]["status"], "NOT_RUN")
        passed = dict(results, tests=[{"name": "test_errors", "status": "pass"}],
                      not_verifiable={"CHK-004": "needs another build"})
        self.assertEqual(report.check_status(passed, contract, {"test_errors": ["CHK-004"]})["CHK-004"]["status"],
                         "NOT_VERIFIABLE")                              # a passing test is not a proof here


class ReviewApplyTest(unittest.TestCase):
    class Fake:
        name = "fake"

        def run(self, task, log_dir):
            return AgentResult({"verdicts": [
                {"rule": "A-1", "verdict": "keep", "reason": "ok"},
                {"rule": "A-2", "verdict": "fix", "strength": "MUST_NOT", "reason": "restriction"},
                {"rule": "A-3", "verdict": "reject", "reason": "description"},
                {"rule": "A-4", "verdict": "fix", "reason": "nothing changed"},
                {"rule": "Z-9", "verdict": "keep", "reason": "unknown"}],
                "duplicates": [{"keep": "A-1", "merge": ["A-4"], "reason": "same"}],
                "questions": [{"rules": ["A-1", "nope"], "question": "why?"}]}, "fake", None, 0.0, {})

    def test_apply(self):
        rules = [{"id": f"A-{i}", "doc": "d", "section": "1", "strength": "MAY", "actor": "master", "check": "assertion",
                  "statement": f"s{i}", "condition": "", "quote": f"q{i}", "sentences": [f"1:s{i}"]} for i in range(1, 6)]
        with tempfile.TemporaryDirectory() as d:
            res = review.review(rules, self.Fake(), Path(d), workers=1)
        ids = [r["id"] for r in res["rules"]]
        self.assertEqual(ids, ["A-1", "A-2", "A-5"])
        self.assertEqual(res["rules"][1]["strength"], "MUST_NOT")
        self.assertEqual(res["rules"][0]["merged_from"][0]["id"], "A-4")
        self.assertEqual(res["rules"][2]["review"]["verdict"], "unreviewed")
        self.assertEqual([r["id"] for r in res["rejected"]], ["A-3"])
        self.assertEqual(res["questions"][0]["rules"], ["A-1"])
        self.assertIn("Z-9", res["review"]["unknown_ids"])
        review.record_answer(res, 1, "Because the spec says so.", "Designer")
        self.assertEqual(review.decisions(res)[0]["decision"]["by"], "Designer")
        self.assertIn("**Decision** (Designer", review.to_markdown(res))
        with self.assertRaises(ValueError):
            review.record_answer(res, 2, "x", "Designer")             # only one open question
        from nnc.contract import build_prompt
        prompt = build_prompt({"ports": [], "parameters": [], "clock": "c", "reset": None}, "top", [],
                              decisions=review.decisions(res))
        self.assertIn("DESIGNER DECISIONS", prompt)
        self.assertIn("Because the spec says so.", prompt)


class GateConfigTest(unittest.TestCase):
    def test_documents_and_require_gate(self):
        with tempfile.TemporaryDirectory() as d:
            des = Design.init(Path(d) / "x")
            des.add_document("spec/a.md", "ip_spec", "BR")
            with self.assertRaises(ProjectError):
                des.add_document("spec/b.md", "ip_spec", "TL")       # a second ip_spec
            with self.assertRaises(ProjectError):
                des.add_document("spec/c.md", "standard", "BR")      # tag already used
            with self.assertRaises(ProjectError):
                des.require_gate("G2_contract", unreviewed=False)
            self.assertEqual(des.require_gate("G2_contract", unreviewed=True), ["G1_rules", "G2_contract"])


class CoverageClosureTest(unittest.TestCase):
    def test_parse_dat_counts_only_dut_files(self):
        from nnc.coverage import parse_dat, summarize_uncovered
        rec = lambda f, l, page, o, n: (f"C '\x01f\x02/x/{f}\x01l\x02{l}\x01page\x02{page}/m\x01o\x02{o}' {n}\n")
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "coverage.dat"
            p.write_text("# SystemC::Coverage-3\n" + rec("dut.sv", 3, "v_toggle", "a[0]:0->1", 4) +
                         rec("dut.sv", 3, "v_toggle", "a[0]:1->0", 0) + rec("dut.sv", 3, "v_toggle", "a[1]:1->0", 0) +
                         rec("dut.sv", 9, "v_line", "if", 2) + rec("nnc_chk_x.sv", 1, "v_line", "", 0), encoding="utf-8")
            r = parse_dat(p, ["dut.sv"])
        self.assertEqual(r["metrics"]["toggle"]["total"], 3)
        self.assertEqual(r["metrics"]["toggle"]["hit"], 1)
        self.assertEqual(r["metrics"]["block"]["percent"], 100.0)            # the checker point is excluded
        g = summarize_uncovered(r["uncovered"])
        self.assertEqual((g[0]["what"], g[0]["points"]), ("a", 2))

    def test_leak_filter_and_module_validation(self):
        from nnc import closure
        with tempfile.TemporaryDirectory() as d:
            rtl = Path(d) / "m.sv"
            rtl.write_text("module m(input i_wr_en); logic r_wr_ptr_q; // c_comment_only\nendmodule\n", encoding="utf-8")
            private = closure.rtl_private_names([rtl], "The port i_wr_en requests a write.")
        self.assertEqual(private, {"r_wr_ptr_q"})
        self.assertEqual(closure.leaks("Hold i_wr_en high until r_wr_ptr_q wraps", private), ["r_wr_ptr_q"])
        contract = {"checks": [{"id": "CHK-004", "kind": "test"}]}
        good = ('import cocotb\nfrom nnc_cocotb import *\nimport test_x as base\n@cocotb.test()\n'
                'async def test_cov_101_wrap(dut):\n    """COV-101 CHK-004: wrap."""\n    assert 1 == 1\n')
        self.assertEqual(closure.validate_module(good, contract, [{"id": "COV-101"}]), [])
        bad = good.replace("import test_x as base", "from test_x import *").replace("    assert 1 == 1\n", "    pass\n")
        probs = closure.validate_module(bad, contract, [{"id": "COV-101"}, {"id": "COV-102"}])
        self.assertTrue(any("star-import" in p for p in probs) and any("COV-102" in p for p in probs)
                        and any("assert" in p for p in probs))


class SelectionAndSignoffTest(unittest.TestCase):
    def test_not_selected_checks_never_pass(self):
        from nnc.contract import select_checks, selected
        c = {"checks": [{"id": "CHK-001", "kind": "assertion", "rules": ["R1"]},
                        {"id": "CHK-002", "kind": "test", "rules": ["R2"]}], "not_verified": []}
        select_checks(c, ["CHK-001"], "Designer")
        self.assertEqual([x["id"] for x in selected(c)["checks"]], ["CHK-001"])
        results = {"status": "ran", "tests": [{"name": "test_chk_002_x", "status": "pass"}],
                   "assertions": {"CHK-001": {"hits": 3, "fails": 0}}}
        st = report.check_status(results, c)
        self.assertEqual((st["CHK-001"]["status"], st["CHK-002"]["status"]), ("PASS", "NOT_SELECTED"))
        rows = report.rtm({"rules": [{"id": r, "section": "1", "sentences": [], "strength": "MUST", "statement": "s"}
                                     for r in ("R1", "R2")]}, c, st, None)
        self.assertEqual([r["status"] for r in rows], ["VERIFIED", "NOT_SELECTED"])
        with self.assertRaises(ValueError):
            select_checks(c, ["CHK-009"], "Designer")

    def test_signoff_conditions(self):
        rep = {"checks": {"by_status": {"PASS": 3}}, "rules": {"by_status": {"VERIFIED": 3}}, "unreviewed_gates": [],
               "gates": [{"gate": "G1_rules", "state": "APPROVED", "detail": "by Claude (delegated by X)"}],
               "simulation": {"integration": {"ok": True}},
               "mutation": {"threshold": 85.0, "rules_below_threshold": ["R7"], "rules_attributed": 4},
               "coverage_closure": {"metric": "line", "target": 95.0, "status": "target_met"}}
        conds = {name: (ok, note) for name, ok, note in report.signoff_conditions(rep)}
        self.assertIn("delegation", conds["Gates G1-G3 approved"][1])
        self.assertFalse(conds["Per-requirement mutation score >= 85 %"][0])
        self.assertTrue(conds["Coverage target line 95.0 %"][0])


class InjectTest(unittest.TestCase):
    PATCH = ("--- a/rtl/m.sv\n+++ b/rtl/m.sv\n@@ -2,3 +2,2 @@\n assign a = b;\n-assign c = d |\n-            e;\n"
             "+assign c = d;\n")

    def test_patch_applies_to_a_copy_only(self):
        from nnc import inject
        with tempfile.TemporaryDirectory() as d:
            rtl = Path(d) / "rtl"
            rtl.mkdir()
            src = "module m;\nassign a = b;\nassign c = d |\n            e;\nendmodule\n"
            (rtl / "m.sv").write_text(src, encoding="utf-8")
            changed = inject.make_copy(rtl, self.PATCH, Path(d) / "bug" / "rtl")
            self.assertEqual(changed, ["m.sv"])
            self.assertEqual((Path(d) / "bug" / "rtl" / "m.sv").read_text(encoding="utf-8"),
                             "module m;\nassign a = b;\nassign c = d;\nendmodule\n")
            self.assertEqual((rtl / "m.sv").read_text(encoding="utf-8"), src)          # original untouched
            with self.assertRaises(inject.PatchError):
                inject.make_copy(rtl, self.PATCH.replace("assign a = b;", "assign z = y;"), Path(d) / "x")


class HashPortabilityTest(unittest.TestCase):
    def test_line_endings_do_not_change_an_approval(self):
        from nnc.project import hash_path
        with tempfile.TemporaryDirectory() as t:
            a, b = Path(t) / "a" / "x.json", Path(t) / "b" / "x.json"
            a.parent.mkdir()
            b.parent.mkdir()
            a.write_bytes(b'{\r\n  "k": 1\r\n}\r\n')
            b.write_bytes(b'{\n  "k": 1\n}\n')
            self.assertEqual(hash_path(a), hash_path(b))
            self.assertEqual(hash_path(a.parent), hash_path(b.parent))
            b.write_bytes(b'{\n  "k": 2\n}\n')
            self.assertNotEqual(hash_path(a), hash_path(b))


class RenumberTest(unittest.TestCase):
    def test_references_follow_the_new_ids(self):
        from nnc.contract import renumber
        checks = [{"id": "CHK-001", "kind": "test", "rules": ["R1"], "behavior": "uses the tracker of CHK-002"},
                  {"id": "CHK-002", "kind": "assertion", "rules": ["R2"], "behavior": "tracker; see CHK-001",
                   "notes": ["CHK-001 and CHK-009"]}]
        out = renumber(checks, [1, 0])
        self.assertEqual([c["id"] for c in out], ["CHK-001", "CHK-002"])
        self.assertEqual(out[0]["behavior"], "tracker; see CHK-002")       # no chained replacement
        self.assertEqual(out[0]["notes"], ["CHK-002 and CHK-009"])           # unknown ID left as written
        self.assertEqual(out[1]["behavior"], "uses the tracker of CHK-001")
        self.assertEqual(out[1]["rules"], ["R1"])

    def test_ranges_and_slash_lists(self):
        from nnc.contract import rewrite_refs
        m = {"CHK-020": "CHK-023", "CHK-021": "CHK-021", "CHK-022": "CHK-022", "CHK-023": "CHK-019",
             "CHK-015": "CHK-014", "CHK-017": "CHK-017", "CHK-001": "CHK-002", "CHK-002": "CHK-003"}
        self.assertEqual(rewrite_refs("results of CHK-020..CHK-023.", m),
                         "results of CHK-019, CHK-021, CHK-022, CHK-023.")
        self.assertEqual(rewrite_refs("see CHK-001..CHK-002", m), "see CHK-002..CHK-003")
        self.assertEqual(rewrite_refs("trackers CHK-015/017", m), "trackers CHK-014/CHK-017")
        self.assertEqual(rewrite_refs("CHK-020 to CHK-021", m), "CHK-021, CHK-023")


MC_SPEC = """# Two-clock FIFO

## 6. Ports

| Port | Direction | Width | Meaning | Clock domain | Signal type |
|---|---|---|---|---|---|
| i_clk_wr | Input | 1 | Write clock | CLK-WR | Clock (rising edge) |
| i_rst_n_wr | Input | 1 | Write reset | CLK-WR | Reset (active-low level) |
| i_wr_en | Input | 1 | Write request | CLK-WR | Level |
| i_thr | Input | LPARA_OCC_W | Threshold | static | Static |
| i_rst_n_sw | Input | 1 | Software reset request, active-low | CLK-WR | Level (control) |
| i_clk_rd | Input | 1 | Read clock | CLK-RD | Clock (rising edge) |
| i_rst_n_rd | Input | 1 | Read reset | CLK-RD | Reset (active-low level) |
| o_empty | Output | 1 | Empty flag | CLK-RD | Level |

## 8. Parameters

| Parameter | Purpose | Default | Legal values |
|---|---|---|---|
| PARA_FIFO_DEPTH | Entries | 8 | 2 or more |
| LPARA_OCC_W | Occupancy width: clog2(DEPTH + 1) | Derived | At least 2 |
"""


class MultiClockTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        spec = Path(self._tmp.name) / "fifo.md"
        spec.write_text(MC_SPEC, encoding="utf-8")
        self.iface = extract_interface(build_index(spec))
        self.contract = {"top": "m_fifo", "interface": self.iface, "checks": []}

    def tearDown(self):
        self._tmp.cleanup()

    def test_clocks_resets_and_derived_parameter(self):
        from nnc.contract import derived_values, eval_param
        self.assertEqual([c["name"] for c in self.iface["clocks"]], ["i_clk_wr", "i_clk_rd"])
        self.assertEqual([(r["name"], r["clock"]) for r in self.iface["resets"]],
                         [("i_rst_n_wr", "i_clk_wr"), ("i_rst_n_rd", "i_clk_rd")])   # not the software reset
        occ = self.iface["parameters"][1]
        self.assertEqual(occ["derived"], "$clog2(PARA_FIFO_DEPTH + 1)")
        self.assertEqual(derived_values(self.iface, {"PARA_FIFO_DEPTH": 8})["LPARA_OCC_W"], 4)
        self.assertEqual(eval_param("$clog2(PARA_FIFO_DEPTH)", {"PARA_FIFO_DEPTH": 1}), 0)
        self.assertIn("localparam int LPARA_OCC_W = $clog2(PARA_FIFO_DEPTH + 1)", module_header("x", self.iface))

    def test_sim_inputs_and_prompts(self):
        top = sim.tb_top(self.contract, ["nnc_chk_a"])
        self.assertIn("m_fifo #(.PARA_FIFO_DEPTH(PARA_FIFO_DEPTH)) u_dut", top)     # derived not passed
        pv = sim.param_values(self.contract)
        self.assertEqual(pv, {"PARA_FIFO_DEPTH": 8})
        files = sim.build_inputs(self.contract, [], [], Path("test_x.py"), pv,
                                 clock_periods=sim.parse_periods("i_clk_rd=20"))
        cfg = json.loads(files["nnc_interface.json"])
        self.assertEqual(cfg["clocks"], {"i_clk_wr": 10, "i_clk_rd": 20})
        self.assertEqual(cfg["parameters"]["LPARA_OCC_W"], 4)
        self.assertNotIn("LPARA_OCC_W", files["Makefile"])
        with self.assertRaises(ValueError):
            sim.clock_table(self.iface, {"i_clk_x": 5})
        sva_prompt = gen_sva.build_prompt("g", self.iface, [], {})
        self.assertIn("@(posedge i_clk_rd) disable iff (!i_rst_n_rd)   signals: o_empty", sva_prompt)
        self.assertIn("SEVERAL CLOCKS", gen_tests.build_prompt(self.contract, {"rules": []}))

    def test_single_clock_prompts_unchanged(self):
        spec = Path(self._tmp.name) / "one.md"
        spec.write_text(MD_SPEC, encoding="utf-8")
        iface = extract_interface(build_index(spec))
        c = {"top": "m_demo", "interface": iface, "checks": []}
        self.assertNotIn("SEVERAL CLOCKS", gen_sva.build_prompt("g", iface, [], {}))
        self.assertNotIn("CLOCK DOMAINS", gen_tests.build_prompt(c, {"rules": []}))
        self.assertNotIn("clocks", json.loads(sim.build_inputs(c, [], [], Path("t.py"), {})["nnc_interface.json"]))


if __name__ == "__main__":
    unittest.main()

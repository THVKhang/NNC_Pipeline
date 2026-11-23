"""Intake (nnc/intake.py), adaptation (nnc/adapt.py) and the port reader of the simulation (sim.dut_ports) on
hand-made sources, Verilator trees and Yosys netlists (no tool runs)."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from nnc import adapt, contract, intake, sim
from nnc.ingest import build_index


def write(root: Path, rel: str, text: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


class CollectTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        write(self.tmp, "rtl/top.sv", '`include "lib/defs.svh"\nmodule top import my_pkg::*; (input logic clk);\n'
                                      '  sub #(.W(4)) u_sub (.clk(clk));\n  // other u_other (.x());\nendmodule\n')
        write(self.tmp, "rtl/unused.sv", "module unused (input a); endmodule\n")
        write(self.tmp, "libs/a/sub.sv", "module sub #(parameter W = 1) (input clk);\n  leaf u_l (.clk(clk));\n"
                                         "endmodule\nmodule leaf (input clk); endmodule\n")
        write(self.tmp, "libs/a/my_pkg.sv", "package my_pkg; import base_pkg::*; endpackage\n")
        write(self.tmp, "libs/a/base_pkg.sv", "package base_pkg; localparam int X = 1; endpackage\n")
        write(self.tmp, "libs/a/other.sv", "module other (input x); endmodule\n")
        write(self.tmp, "libs/inc/lib/defs.svh", "`define DEFS 1\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_closure_order_and_includes(self):
        col = intake.collect(self.tmp / "rtl", [self.tmp / "libs" / "a", self.tmp / "libs" / "inc"], "top")
        names = [Path(f).name for f in col["files"]]
        self.assertEqual(names[:2], ["base_pkg.sv", "my_pkg.sv"])      # packages first, dependencies first
        self.assertEqual(set(names), {"base_pkg.sv", "my_pkg.sv", "sub.sv", "top.sv"})   # other.sv: a comment
        self.assertNotIn("unused.sv", names)
        self.assertEqual([Path(d).name for d in col["include_dirs"]], ["inc"])  # `include "lib/defs.svh"
        self.assertEqual(col["missing_includes"], [])

    def test_top_detection(self):
        col = intake.collect(self.tmp / "rtl", [self.tmp / "libs" / "a"], None)
        self.assertIsNone(col["top"])                                   # top and unused: two candidates
        self.assertEqual(sorted(col["candidates"]), ["top", "unused"])
        (self.tmp / "rtl" / "unused.sv").unlink()
        self.assertEqual(intake.collect(self.tmp / "rtl", [self.tmp / "libs" / "a"], None)["top"], "top")

    def test_missing_and_vhdl_and_protected(self):
        col = intake.collect(self.tmp / "rtl", [], "top")
        self.assertEqual(col["missing_includes"], ["lib/defs.svh"])
        rep = intake.assess(col, None, [], None, None)
        self.assertEqual(rep["verdict"], "needs_input")
        # the same missing include is only a note when the tools read the RTL (an `ifdef branch not taken)
        ok = {"lint": 0, "json": 0, "yosys": 0, "slang": 0}
        self.assertEqual(intake.assess(col, ok, [], None, None)["verdict"], "ready")
        write(self.tmp, "vh/a.vhd", "entity a is end;")
        self.assertEqual(intake.assess(intake.collect(self.tmp / "vh", [], "a"), None, [], None, None)["verdict"],
                         "unsupported")
        write(self.tmp, "rtl/enc.sv", "`pragma protect begin_protected\nmodule enc; endmodule\n")
        col = intake.collect(self.tmp / "rtl", [self.tmp / "libs" / "a"], "top")
        self.assertEqual(intake.assess(col, None, [], None, None)["verdict"], "unsupported")


def node(addr, type_, **kw):
    return {"addr": addr, "type": type_, "dtypep": addr, **kw}


def tree_with(ports, types):
    stmts = [{"type": "VAR", "name": n, "origName": n, "direction": d, "dtypep": t, "varType": "PORT"}
             for n, d, t in ports]
    stmts.append({"type": "VAR", "name": "W", "origName": "W", "varType": "GPARAM", "dtypep": "(B1)",
                  "valuep": [{"type": "CONST", "name": "32'sh8"}]})
    return {"modulesp": [{"type": "MODULE", "name": "m", "origName": "m", "level": 1, "stmtsp": stmts}],
            "miscsp": [{"type": "TYPETABLE", "typesp": types}]}


TYPES = [
    node("(B1)", "BASICDTYPE", keyword="logic"),
    node("(B8)", "BASICDTYPE", keyword="logic", range="7:0"),
    node("(B3)", "BASICDTYPE", keyword="logic", range="2:0"),
    node("(E3)", "ENUMDTYPE", refDTypep="(B3)", name="op_e"),
    # struct inner_t {logic [2:0] a; logic b;} (4 bits) ; struct outer_t {logic v; inner_t in; logic [7:0] d;}
    node("(SI)", "STRUCTDTYPE", packed=True, name="pkg::inner_t",
         membersp=[{"type": "MEMBERDTYPE", "name": "a", "addr": "(MA)", "dtypep": "(E3)", "lsb": "1"},
                   {"type": "MEMBERDTYPE", "name": "b", "addr": "(MB)", "dtypep": "(B1)"}]),
    node("(SO)", "STRUCTDTYPE", packed=True, name="pkg::outer_t",
         membersp=[{"type": "MEMBERDTYPE", "name": "v", "addr": "(MV)", "dtypep": "(B1)", "lsb": "12"},
                   {"type": "MEMBERDTYPE", "name": "in", "addr": "(MI)", "dtypep": "(SI)", "lsb": "8"},
                   {"type": "MEMBERDTYPE", "name": "d", "addr": "(MD)", "dtypep": "(B8)"}]),
    node("(RO)", "REFDTYPE", refDTypep="(SO)", name="outer_t"),
    node("(PA)", "PACKARRAYDTYPE", refDTypep="(SI)", declRange="[1:0]"),
    node("(UA)", "UNPACKARRAYDTYPE", refDTypep="(B8)", declRange="[0:3]"),
    node("(IF)", "IFACEREFDTYPE", ifaceName="bus_if"),
    node("(RS)", "BASICDTYPE", keyword="string"),
]


class PortsTest(unittest.TestCase):
    def ports(self):
        tree = tree_with([("clk", "INPUT", "(B1)"), ("op", "INPUT", "(E3)"), ("s_i", "INPUT", "(RO)"),
                          ("arr_o", "OUTPUT", "(PA)"), ("mem_i", "INPUT", "(UA)"), ("bus", "INOUT", "(IF)"),
                          ("name", "INPUT", "(RS)")], TYPES)
        return intake.ports_from_tree(tree, "m")

    def test_kinds_widths_fields(self):
        ports, params = self.ports()
        p = {x["name"]: x for x in ports}
        self.assertEqual([(x["name"], x["value"], x["enum"]) for x in params], [("W", 8, False)])
        self.assertEqual((p["clk"]["kind"], p["clk"]["width"]), ("vector", 1))
        self.assertEqual((p["op"]["kind"], p["op"]["width"]), ("vector", 3))        # an enum is a vector
        self.assertEqual(p["s_i"]["width"], 13)
        self.assertEqual(p["s_i"]["fields"], [("v", 12, 1), ("in.a", 9, 3), ("in.b", 8, 1), ("d", 0, 8)])
        self.assertEqual(p["arr_o"]["kind"], "packed_array")
        self.assertEqual(p["arr_o"]["width"], 8)
        self.assertEqual(p["arr_o"]["fields"][:2], [("[0].a", 1, 3), ("[0].b", 0, 1)])
        self.assertEqual(p["arr_o"]["fields"][2], ("[1].a", 5, 3))
        self.assertEqual((p["mem_i"]["kind"], p["mem_i"]["range"], p["mem_i"]["width"]), ("unpacked_array", [0, 3], 8))
        handling = {n: intake.port_handling(x) for n, x in p.items()}
        self.assertEqual(handling, {"clk": "direct", "op": "direct", "s_i": "adapter", "arr_o": "adapter",
                                    "mem_i": "adapter", "bus": "unsupported", "name": "unsupported"})
        rep = intake.assess({"top": "m", "files": ["x.sv"]}, {"lint": 0, "json": 0, "yosys": 0, "slang": 0},
                            ports, None, None)
        self.assertEqual(rep["verdict"], "unsupported")
        rep = intake.assess({"top": "m", "files": ["x.sv"]}, {"lint": 0, "json": 0, "yosys": 0, "slang": 0},
                            [x for x in ports if x["name"] not in ("bus", "name")], None, None)
        self.assertEqual(rep["verdict"], "adapt")
        self.assertEqual(rep["stages"]["formal"], "on (verilog)")

    def test_wrapper(self):
        ports = [x for x in self.ports()[0] if x["name"] not in ("bus", "name")]
        wp = adapt.wrapper_ports(ports)
        names = [w["name"] for w in wp]
        self.assertEqual(names[:6], ["clk", "op", "s_i_v", "s_i_in_a", "s_i_in_b", "s_i_d"])
        self.assertIn("arr_o_1_a", names)
        self.assertIn("mem_i_3", names)
        sv = adapt.wrapper_sv("m", ports, [{"name": "W", "value": 8}])
        self.assertIn("module m_nnc #(", sv)
        self.assertIn("assign nnc_s_i[11:9] = s_i_in_a;", sv)
        self.assertIn("assign arr_o_1_a = nnc_arr_o[7:5];", sv)
        self.assertIn("assign nnc_mem_i[2] = mem_i_2;", sv)
        self.assertIn("m #(.W(W)) u_dut (", sv)
        self.assertIn("if ($bits(u_dut.s_i) != 13) $fatal", sv)
        self.assertIn("`ifndef SYNTHESIS", sv)
        self.assertEqual(sum(w["width"] for w in wp if w["of"] == "s_i"), 13)

    def test_interface_document_reads_back(self):
        """The contract reads the interface document; clocks and resets come from the netlist."""
        ports = [x for x in self.ports()[0] if x["name"] not in ("bus", "name")]
        ports.append({"name": "rst_n", "direction": "input", "kind": "vector", "width": 1, "fields": [], "type": "logic"})
        struct = {"clocks": {"clk": {"bits": 3, "edges": ["rise"]}},
                  "async_resets": {"rst_n": {"bits": 3, "active": ["low"]}}, "sync_resets": {}}
        tmp = Path(tempfile.mkdtemp())
        try:
            f = tmp / "m_nnc_interface.md"
            f.write_text(adapt.interface_md("m", "m_nnc", ports, [{"name": "W", "value": 8}], struct, "spec.md"),
                         encoding="utf-8")
            iface = contract.extract_interface(build_index(f), top="m_nnc")
            self.assertEqual(iface["clock"], "clk")
            self.assertEqual(iface["reset"], {"name": "rst_n", "active_low": True})
            got = {p["name"]: (p["direction"], p["width"]) for p in iface["ports"]}
            want = {w["name"]: (w["direction"], str(w["width"])) for w in adapt.wrapper_ports(ports)}
            self.assertEqual(got, want)
            self.assertEqual([p["name"] for p in iface["parameters"]], ["W"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class StructureTest(unittest.TestCase):
    def test_clocks_resets_constructs(self):
        ports = {"clk": {"direction": "input", "bits": [2]}, "rst_n": {"direction": "input", "bits": [3]},
                 "srst": {"direction": "input", "bits": [4]}}
        cells = {
            "a": {"type": "$adff", "parameters": {"WIDTH": "00000000000000000000000000000100",
                                                  "ARST_POLARITY": "0", "CLK_POLARITY": "1"},
                  "connections": {"CLK": [2], "ARST": [3], "D": [10, 11, 12, 13], "Q": [20, 21, 22, 23]}},
            # yosys-slang: asynchronous reset as an asynchronous load of a constant
            "b": {"type": "$aldff", "parameters": {"WIDTH": 1, "ALOAD_POLARITY": "0", "CLK_POLARITY": "0"},
                  "connections": {"CLK": [2], "ALOAD": [3], "AD": ["1"], "D": [14], "Q": [24]}},
            "c": {"type": "$sdff", "parameters": {"WIDTH": 2, "SRST_POLARITY": "1"},
                  "connections": {"CLK": [30], "SRST": [4], "D": [15, 16], "Q": [25, 26]}},
            "l": {"type": "$dlatch", "parameters": {"WIDTH": 1}, "connections": {"EN": [2], "D": [17], "Q": [27]}},
            "t": {"type": "$tribuf", "parameters": {"WIDTH": 1}, "connections": {"A": [17], "EN": [2], "Y": [28]}},
        }
        s = intake.structure({"modules": {"m": {"ports": ports, "cells": cells}}}, "m")
        self.assertEqual(s["flop_bits"], 7)
        self.assertEqual(s["clocks"], {"clk": {"bits": 5, "edges": ["fall", "rise"], "lanes": [0]}})
        self.assertEqual(s["derived_clock_bits"], 2)
        self.assertEqual(s["async_resets"], {"rst_n": {"bits": 5, "active": ["low"]}})
        self.assertEqual(s["sync_resets"], {"srst": {"bits": 2, "active": ["high"]}})
        self.assertEqual((s["latches"], s["tristate"], s["negedge_bits"]), (1, True, 1))


class DutPortsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_ifdef_ports(self):
        f = write(self.tmp, "a.v", "`define HAS_B\nmodule a (input clk,\n`ifdef FORMAL\n output [3:0] f_dbg,\n`endif\n"
                                   "`ifdef HAS_B\n output b,\n`else\n output c,\n`endif\n"
                                   "`ifndef FORMAL\n output d\n`endif\n);\nendmodule\n")
        self.assertEqual([p["name"] for p in sim.dut_ports([f], "a")], ["clk", "b", "d"])
        self.assertEqual([p["name"] for p in sim.dut_ports([f], "a", ["FORMAL"])], ["clk", "f_dbg", "b"])

    def test_verilog_1995_ports(self):
        f = write(self.tmp, "b.v", "module b (clk, rst_n, q, d);\n  input clk, rst_n;\n  input [7:0] d;\n"
                                   "  output reg [7:0] q;\n  wire x;\nendmodule\n")
        self.assertEqual(sim.dut_ports([f], "b"), [{"name": "clk", "direction": "input"},
                                                  {"name": "rst_n", "direction": "input"},
                                                  {"name": "q", "direction": "output"},
                                                  {"name": "d", "direction": "input"}])

    def test_header_package_import(self):
        # common_cells: `module cc_lzc import cc_pkg::*; #(...) (...)`
        f = write(self.tmp, "c.sv", "module automatic c\n  import p::*, q::t;\n  import r::*;\n #(parameter int W = 2)"
                                    " (input logic [W-1:0] in_i, output t cnt_o);\nendmodule\n")
        self.assertEqual([p["name"] for p in sim.dut_ports([f], "c")], ["in_i", "cnt_o"])


class ClockVectorTest(unittest.TestCase):
    def test_clock_vector_split_per_bit(self):
        # common_cells cc_clk_mux_glitch_free: input [1:0] clks_i, both bits clock flops
        ports = [{"name": "clks_i", "direction": "input", "kind": "vector", "width": 2, "fields": [], "type": "logic"},
                 {"name": "sel_i", "direction": "input", "kind": "vector", "width": 1, "fields": [], "type": "logic"},
                 {"name": "clk_o", "direction": "output", "kind": "vector", "width": 1, "fields": [], "type": "logic"}]
        struct = {"clocks": {"clks_i": {"bits": 4, "edges": ["rise"], "lanes": [0, 1]}}}
        intake.mark_clock_vectors(ports, struct)
        self.assertEqual(ports[0]["kind"], "clock_vector")
        self.assertEqual(intake.port_handling(ports[0]), "adapter")
        self.assertEqual([q["name"] for q in adapt.wrapper_ports(ports)], ["clks_i_0", "clks_i_1", "sel_i", "clk_o"])
        md = adapt.interface_md("m", "m_nnc", ports, [], struct, None)
        self.assertIn("| clks_i_0 | input | 1 | Clock |", md)
        self.assertIn("| clks_i_1 | input | 1 | Clock |", md)
        sv = adapt.wrapper_sv("m", ports, [])
        self.assertIn("assign nnc_clks_i[1:1] = clks_i_1;", sv)


class SmokeStatusTest(unittest.TestCase):
    def test_classes(self):
        from nnc import corpus
        rtl = {"cc_fifo.sv"}
        fail = [{"status": "fail"}]
        self.assertEqual(corpus.smoke_status([{"status": "pass"}], [], rtl), ("pass", None))
        self.assertEqual(corpus.smoke_status(fail, ["%Error: /root/r/rtl/cc_fifo.sv:135: Verilog $stop"], rtl),
                         ("dut_assertion", "cc_fifo.sv:135"))
        # a $stop of the test bench top is not an assertion of the design
        self.assertEqual(corpus.smoke_status(fail, ["%Error: /root/r/nnc_tb_top.sv:3: Verilog $stop"], rtl),
                         ("test_failed", None))
        self.assertEqual(corpus.smoke_status([], ["%Error-BLKANDNBLK: x.v:1: Unsupported: Blocking and ..."], rtl),
                         ("simulator_unsupported", None))
        self.assertEqual(corpus.smoke_status([], ["%Error: x.v:1: syntax error"], rtl), ("build_failed", None))


class PortableTest(unittest.TestCase):
    def test_paths_relative_to_the_design(self):
        base, repo = Path("C:/x/repo/designs/d"), Path("C:/x/repo")
        got = intake.portable({"a": [str(base / "rtl" / "f.sv"), str(base), "plain", str(repo / "lib" / "y.sv")]},
                              base, repo)
        self.assertEqual(got, {"a": ["rtl/f.sv", ".", "plain", "lib/y.sv"]})


class ProbeScriptTest(unittest.TestCase):
    def test_synchronous_resets_are_recognised(self):
        # without opt_dff a synchronous reset stays a $dff behind a $mux and no reset is found (verilog-uart rst)
        script = intake.probe_script("top", ["a.v"], [])
        self.assertEqual(script.count("proc; flatten; opt_dff;"), 2)


class ContractParamTest(unittest.TestCase):
    def test_only_32_bit_integers_pass(self):
        ok = intake.contract_param
        self.assertTrue(ok({"name": "W", "value": 8, "width": 32, "enum": False}))
        self.assertTrue(ok({"name": "N", "value": -3, "width": 32, "enum": False}))
        # verilog-axi M_ADDR_WIDTH: M_COUNT*M_REGIONS*32 bits; common_cells Mode: an enum
        self.assertFalse(ok({"name": "M_ADDR_WIDTH", "value": 24 | 24 << 32, "width": 128, "enum": False}))
        self.assertFalse(ok({"name": "Mode", "value": 1, "width": 1, "enum": True}))
        self.assertFalse(ok({"name": "X", "value": 0xFFFFFFFF, "width": 32, "enum": False}))
        self.assertFalse(ok({"name": "T", "value": None, "width": None, "enum": False}))


class RangeTest(unittest.TestCase):
    def test_negative_bit_indices_round_trip(self):
        # wb2axip axissafety: C_AXIS_USER_WIDTH = 0 declares S_AXIS_TUSER [-1:0]
        from nnc import coverage
        for v in ([3, 4, 5, 9], [-1, 0], [-3, -2, -1], [-5, -4, 0, 1, 2, 7]):
            self.assertEqual(coverage._expand(coverage.line_ranges(v)), set(v))
        with self.assertRaises(ValueError):
            coverage._expand("3-x")


class AdaptWorkspaceTest(unittest.TestCase):
    def test_copies_library_files_and_writes_filelist(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            write(tmp, "d/rtl/top.sv", "module top (input clk); sub u (.clk(clk)); endmodule\n")
            write(tmp, "lib/sub.sv", "module sub (input clk); endmodule\n")
            (tmp / "d" / "spec").mkdir()
            col = intake.collect(tmp / "d" / "rtl", [tmp / "lib"], "top")
            ports = [{"name": "clk", "direction": "input", "kind": "vector", "width": 1, "fields": [], "type": "logic"}]
            rep = {"collect": col, "ports": ports, "parameters": [], "structure": None, "spec": None}
            rep.update(intake.assess(col, {"lint": 0, "json": 0, "yosys": 0, "slang": 0}, ports, None, None))
            a = adapt.adapt(tmp / "d", rep, spec_name=None)
            self.assertTrue((tmp / "d" / "rtl" / "sub.sv").is_file())
            self.assertEqual((tmp / "d" / "rtl" / "filelist.f").read_text().splitlines()[1:], ["top.sv", "sub.sv"])
            self.assertIsNone(a["wrapper"])
            self.assertEqual(a["interface"], "spec/top_interface.md")      # no specification: the port table
            self.assertEqual(json.loads((tmp / "d" / "work" / "adapt.json").read_text())["copied"][0]["file"],
                             "rtl/sub.sv")
            self.assertEqual([p.name for p in sim.rtl_files(tmp / "d" / "rtl")], ["top.sv", "sub.sv"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class CorpusTest(unittest.TestCase):
    def rows(self):
        ok = {"verdict": "ready", "contract_issues": [], "conformance_issues": [], "interface_errors": [],
              "smoke": {"status": "pass", "coverage": {"line": 80.0}}}
        return [
            {"source": "s", "top": "a", "verdict": "ready", "reasons": [], "adapt": dict(ok)},
            {"source": "s", "top": "b", "verdict": "adapt", "reasons": [{"level": "adapt", "message": "x"}],
             "adapt": dict(ok)},
            {"source": "s", "top": "c", "verdict": "ready", "reasons": [],
             "adapt": {**ok, "conformance_issues": ["port d_i of the contract is missing in the DUT"]}},
            {"source": "s", "top": "d", "verdict": "needs_input",
             "reasons": [{"level": "needs_input", "message": "module tc_sync is declared in no file: add the "
                                                            "folder that has it (--lib)"}]},
        ]

    def test_verdicts_summary_compare(self):
        from nnc import corpus
        rows = self.rows()
        self.assertEqual([corpus.final_verdict(r) for r in rows], ["ready", "adapted", "chain_failed", "needs_input"])
        s = corpus.summarize(rows)
        self.assertEqual(s["blocking"], {"flow: port check against the RTL (sim.dut_ports)": 1,
                                         "unit of another library missing": 1})
        self.assertEqual(s["smoke"], {"pass": 3})
        md = corpus.to_markdown({"rows": rows, "summary": s, "manifest": {"sources": [
            {"name": "s", "commit": "0123456789ab", "license": "MIT", "language": "Verilog"}]}})
        self.assertIn("| s | `0123456789` | MIT | Verilog | 4 | 1 | 1 | 1 | 0 | 1 | 3/3 |", md)
        recorded = {"rows": rows}
        got = {"rows": [dict(r) for r in rows]}
        self.assertEqual(corpus.compare(recorded, got), [])
        got["rows"][0] = {**rows[0], "adapt": {**rows[0]["adapt"], "smoke": {"status": "test_failed"}}}
        got["rows"][3] = {**rows[3], "verdict": "ready", "reasons": [], "adapt": rows[0]["adapt"]}
        self.assertEqual(corpus.compare(recorded, got), ["s/a: smoke pass -> test_failed",
                                                         "s/d: verdict needs_input -> ready"])


if __name__ == "__main__":
    unittest.main()

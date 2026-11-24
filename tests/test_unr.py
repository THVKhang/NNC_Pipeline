"""Formal unreachability of toggle points (nnc/unr.py, ROADMAP 19.5): no tool runs here."""
import json
import tempfile
import unittest
from pathlib import Path

from nnc import unr
from nnc.coverage import parse_dat


def rec(h, o, n):
    return f"C '\x01f\x02/x/m.sv\x01l\x023\x01page\x02v_toggle/m\x01o\x02{o}\x01h\x02{h}' {n}\n"


NETLIST = {"modules": {
    "m_top": {"attributes": {"top": "00000000000000000000000000000001"},
              "ports": {"clk": {"direction": "input", "bits": [2]}, "rst_n": {"direction": "input", "bits": [3]},
                        "d": {"direction": "input", "bits": [4, 5]}, "o_q": {"direction": "output", "bits": [6, 7]}},
              "netnames": {"clk": {"bits": [2]}, "rst_n": {"bits": [3]}, "d": {"bits": [4, 5]},
                           "o_q": {"bits": [6, 7], "offset": 0, "upto": 1},
                           "u_rd.cnt": {"bits": [8, 9, 10, 11], "offset": 4},
                           "gen_c[0].u_c.q": {"bits": [12]},
                           "$auto$1": {"bits": [13], "hide_name": 1}},
              "cells": {"$a": {"type": "$adff", "parameters": {"CLK_POLARITY": "1"},
                               "connections": {"CLK": [2], "D": [1], "Q": [8]}},
                        "$b": {"type": "$sdff", "parameters": {"CLK_POLARITY": "00000000000000000000000000000001"},
                               "connections": {"CLK": [2], "D": [1], "Q": [12]}}}},
    "m_sub": {"attributes": {}, "netnames": {}}}}

IFACE = {"clock": "clk", "reset": {"name": "rst_n", "active_low": True},
         "ports": [{"name": n} for n in ("clk", "rst_n", "d", "o_q")]}


class Unr(unittest.TestCase):
    def test_candidates_are_bits_without_a_falling_toggle(self):
        with tempfile.TemporaryDirectory() as d:
            dat = Path(d) / "coverage.dat"
            dat.write_text(rec("nnc_tb_top.u_dut.u_rd", "cnt[5]:0->1", 0) + rec("nnc_tb_top.u_dut.u_rd", "cnt[5]:1->0", 0)
                           + rec("nnc_tb_top.u_dut.u_rd", "cnt[4]:0->1", 3) + rec("nnc_tb_top.u_dut.u_rd", "cnt[4]:1->0", 2)
                           + rec("nnc_tb_top.u_dut", "o_q[1]:0->1", 1) + rec("nnc_tb_top.u_dut", "o_q[1]:1->0", 0)
                           + rec("nnc_tb_top.u_dut.u_rd", "cnt[6]:0->1", 0) + rec("nnc_tb_top.u_dut.u_rd", "cnt[6]:1->0", 0)
                           + rec("nnc_tb_top.u_chk", "x:0->1", 0), encoding="utf-8")
            scope = {"const": {"bits": {"u_rd.cnt": "6"}}}
            self.assertEqual(unr.candidates(dat, ["m.sv"], scope), {"u_rd.cnt": {5}, "o_q": {1}})

    def test_netlist_info_positions_and_clocking(self):
        info = unr.netlist_info(NETLIST)
        self.assertEqual(info["wires"]["u_rd.cnt"], [4, 4, 0])
        self.assertNotIn("$auto$1", info["wires"])
        self.assertEqual(info["ports"]["o_q"], {"direction": "output", "width": 2})
        self.assertEqual((info["clock_nets"], info["negedge"], info["latch"]), (1, False, False))
        self.assertFalse(unr.multiclock(info, 1))
        self.assertTrue(unr.multiclock(info, 2))
        self.assertEqual(unr.position([4, 4, 0], 6), 2)
        self.assertEqual(unr.position([2, 0, 1], 0), 1)        # [0:1]: index 0 is the MSB
        self.assertIsNone(unr.position([4, 4, 0], 3))
        neg = json.loads(json.dumps(NETLIST))
        neg["modules"]["m_top"]["cells"]["$a"]["parameters"]["CLK_POLARITY"] = "0"
        self.assertTrue(unr.multiclock(unr.netlist_info(neg), 1))

    def test_plan_wrapper_and_sby(self):
        info = unr.netlist_info(NETLIST)
        groups, skipped = unr.plan({"u_rd.cnt": {5, 6, 99}, "o_q": {1}, "d": {0}, "gone.x": {0},
                                    "gen_c[0].u_c.q": {0}}, info)
        self.assertEqual(skipped, {"absent": ["gone.x"], "inputs": ["d"]})
        self.assertEqual(groups, [[(0, "gen_c[0].u_c.q", [0]), (1, "o_q", [1]), (2, "u_rd.cnt", [5, 6])]])
        w = unr.wrapper(info, IFACE, groups[0])
        self.assertIn("nnc_unr_dut u_dut (.clk(clk), .rst_n(rst_n), .d(d), .nnc_p0(nnc_s0), .o_q(nnc_s1), "
                      ".nnc_p2(nnc_s2));", w)
        self.assertIn("always @* if (nnc_init) assume (!rst_n);", w)
        self.assertIn("nnc_u2_b5: assert (nnc_s2[1] == nnc_f2[1]);", w)
        self.assertIn("nnc_u1_b1: assert (nnc_s1[0] == nnc_f1[0]);", w)     # o_q is [0:1]
        self.assertIn("nnc_u0_b0: assert (nnc_s0 == nnc_f0);", w)
        self.assertIn("nnc_armed_reach: assert (!nnc_armed);", w)
        self.assertIn("if (clk && !nnc_c0 && nnc_e0 != 2'd2)", w)            # free clocks: count clock edges
        one = unr.wrapper(info, IFACE, groups[0], free_clocks=False)        # one global clock: count steps
        self.assertNotIn("nnc_c0", one)
        self.assertIn("wire nnc_init = (nnc_e != 2'd3);", one)
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "m.sv"
            src.write_text("module m_top; endmodule\n", encoding="utf-8")
            files = unr.build("m_top", IFACE, [src], {"W": 4}, ["X=1"], "verilog", info, groups)
        sby = files["UNR_000.sby"]
        self.assertIn("rename \\gen_c[0].u_c.q nnc_p0\nrename \\u_rd.cnt nnc_p2\ncd ..\nexpose w:nnc_p0 w:nnc_p2\n", sby)
        self.assertIn("multiclock off", sby)
        self.assertIn("read_verilog -sv -DX=1 -I. m.sv\nhierarchy -top m_top -chparam W 4\n", sby)
        self.assertIn("src/nnc_unr_top_000.sv", sby)
        # chunking: more bits than CHUNK go to several tasks
        many = {"u_rd.cnt": set(range(4, 8))}
        old, unr.CHUNK = unr.CHUNK, 3
        try:
            g2, _ = unr.plan(many, info)
        finally:
            unr.CHUNK = old
        self.assertEqual(g2, [[(0, "u_rd.cnt", [4, 5, 6])], [(0, "u_rd.cnt", [7])]])

    def test_statuses_and_record(self):
        text = "nnc_unr_top.nnc_u2_b5 PASS\nnnc_unr_top.nnc_u2_bm1 FAIL\nnoise\n"
        st = unr.parse_statuses(text + "nnc_unr_top.nnc_armed_reach FAIL\n")
        self.assertEqual(st, {(2, 5): "PASS", (2, -1): "FAIL"})
        # the guard did not fail: the checked phase may never be reached, so nothing is concluded
        self.assertEqual(unr.parse_statuses(text + "nnc_unr_top.nnc_armed_reach PASS\n"), {})
        self.assertEqual(unr.parse_statuses(text), {})
        self.assertTrue(unr.vacuous(text + "nnc_unr_top.nnc_armed_reach PASS\n"))
        self.assertFalse(unr.vacuous(text + "nnc_unr_top.nnc_armed_reach FAIL\n"))
        self.assertFalse(unr.vacuous(""))
        # a control bit that the model cannot change: the model does not match the simulation
        g = "nnc_unr_top.nnc_armed_reach FAIL\n"
        self.assertEqual(unr.parse_statuses(text + g + "nnc_unr_top.nnc_control PASS\n"), {})
        self.assertTrue(unr.vacuous(text + g + "nnc_unr_top.nnc_control PASS\n"))
        self.assertEqual(len(unr.parse_statuses(text + g + "nnc_unr_top.nnc_control FAIL\n")), 2)

    def test_control_bit(self):
        with tempfile.TemporaryDirectory() as d:
            dat = Path(d) / "coverage.dat"
            dat.write_text(rec("nnc_tb_top.u_dut.u_rd", "cnt[4]:0->1", 9) + rec("nnc_tb_top.u_dut.u_rd", "cnt[4]:1->0", 8)
                           + rec("nnc_tb_top.u_dut", "o_q[0]:0->1", 30) + rec("nnc_tb_top.u_dut", "o_q[0]:1->0", 2)
                           + rec("nnc_tb_top.u_dut", "d[0]:0->1", 50) + rec("nnc_tb_top.u_dut", "d[0]:1->0", 50),
                           encoding="utf-8")
            self.assertEqual(unr.controls(dat, ["m.sv"]), [("d", 0), ("u_rd.cnt", 4)])
        info = unr.netlist_info(NETLIST)
        self.assertEqual(unr.pick_control([("d", 0), ("u_rd.cnt", 4)], info, set()), ("u_rd.cnt", 4))   # not an input
        self.assertIsNone(unr.pick_control([("u_rd.cnt", 4)], info, {"u_rd.cnt"}))      # a candidate signal
        self.assertIsNone(unr.pick_control([("u_rd.cnt", 5), ("o_q", 0)], info, set()))  # not a flop output
        self.assertEqual(info["state"], {"u_rd.cnt": [0], "gen_c[0].u_c.q": [0]})
        self.assertEqual(info["clock_wires"], ["clk"])
        alias = json.loads(json.dumps(NETLIST))
        alias["modules"]["m_top"]["netnames"]["u_rd.clk"] = {"bits": [2]}              # a clock, under another name
        info2 = unr.netlist_info(alias)
        self.assertEqual(info2["clock_wires"], ["clk", "u_rd.clk"])
        self.assertEqual(unr.pick_control([("u_rd.clk", 0), ("u_rd.cnt", 4)], info2, set()), ("u_rd.cnt", 4))
        groups, _ = unr.plan({"o_q": {1}}, info)
        w = unr.wrapper(info, IFACE, groups[0], True, ("u_rd.cnt", 4))
        self.assertIn(".nnc_pc(nnc_sc)", w)
        self.assertIn("nnc_control: assert (nnc_sc[0] == nnc_fc[0]);", w)
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "m.sv"
            src.write_text("module m_top; endmodule\n", encoding="utf-8")
            sby = unr.build("m_top", IFACE, [src], {}, [], "verilog", info, groups, control=("u_rd.cnt", 4))["UNR_000.sby"]
        self.assertIn("rename \\u_rd.cnt nnc_pc\ncd ..\nexpose w:nnc_pc\n", sby)

    def test_record(self):
        a = {"proven": {"x": "0-3", "y": "1"}, "cex": {}, "open": {"z": "0"}, "absent": [], "inputs": []}
        b = {"proven": {"x": "2-5"}, "cex": {"y": "1"}, "open": {}, "absent": ["w"], "inputs": []}
        rec = {"configs": {"A": a, "B": b}}
        self.assertEqual(unr.proven_bits(rec, ["A", "B"]), {"x": {2, 3}})
        self.assertIsNone(unr.proven_bits(rec, ["A", "C"]))
        c = {"proven": {"w": "0"}, "cex": {}, "open": {}, "absent": [], "inputs": []}
        self.assertEqual(unr.proven_bits({"configs": {"B": b, "C": c}}, ["B", "C"]), {"w": {0}})   # absent in B
        self.assertEqual(unr.undecided(a, {"x": {0, 4}, "z": {0}}), {"x": {4}, "z": {0}})
        m = unr.merge_record(a, {"proven": {"z": "0"}, "cex": {"x": "4"}, "open": {}, "absent": [], "inputs": [],
                                 "tasks": 1})
        self.assertEqual((m["proven"], m["cex"], m["open"]), ({"x": "0-3", "y": "1", "z": "0"}, {"x": "4"}, {}))
        self.assertNotEqual(unr.config_key({"W": 4}, [], "verilog"), unr.config_key({"W": 8}, [], "verilog"))

    def test_proven_bits_leave_the_toggle_coverage(self):
        scope = {"packages": [], "kept": {}, "proven": {"u_rd.cnt": "5-6", "o_q": "1"}}
        with tempfile.TemporaryDirectory() as d:
            dat = Path(d) / "coverage.dat"
            dat.write_text(rec("nnc_tb_top.u_dut.u_rd", "cnt[5]:0->1", 0) + rec("nnc_tb_top.u_dut.u_rd", "cnt[5]:1->0", 0)
                           + rec("nnc_tb_top.u_dut", "o_q[1]:0->1", 1) + rec("nnc_tb_top.u_dut", "o_q[1]:1->0", 0)
                           + rec("nnc_tb_top.u_dut.u_rd", "cnt[4]:0->1", 0), encoding="utf-8")
            r = parse_dat(dat, ["m.sv"], scope)
            # a 1->0 on a proven bit contradicts the proof: every proven bit of that signal counts again
            dat.write_text(dat.read_text(encoding="utf-8") + rec("nnc_tb_top.u_dut.u_rd", "cnt[6]:1->0", 1),
                           encoding="utf-8")
            r2 = parse_dat(dat, ["m.sv"], scope)
        self.assertEqual((r["metrics"]["toggle"]["hit"], r["metrics"]["toggle"]["total"]), (0, 1))
        self.assertEqual(r["scope"]["left_out"], {"toggle": 4})
        self.assertEqual(r["scope"]["proven_unreachable"]["left_out"], 4)
        self.assertEqual(r2["scope"]["proven_unreachable"]["signals_kept_whole"], ["u_rd.cnt"])
        self.assertEqual((r2["metrics"]["toggle"]["hit"], r2["metrics"]["toggle"]["total"]), (1, 4))

    def test_apply_without_record_changes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            scope = {"packages": ["p"], "kept": {}}
            s, info = unr.apply(Path(d), None, {"top": "m", "interface": IFACE}, Path(d), Path(d) / "none.dat", [],
                                scope, [{"name": "a", "params": {}, "defines": []}], "verilog")
        self.assertIs(s, scope)
        self.assertIsNone(info)


if __name__ == "__main__":
    unittest.main()

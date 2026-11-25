"""Formal unreachability of expression points (nnc/unrexpr.py, ROADMAP 24): no tool runs here. The Verilator
trees of tests/data/unrexpr (the design and its instrumented copy) were written by `verilator --json-only
-fno-const -fno-const-before-dfg` and trimmed; coverage.dat holds the expression points of a short simulation
of tb.sv (b stays 0) with --coverage-expr."""
import copy
import json
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

from nnc import coverage as cov
from nnc import unrexpr as ue

DATA = Path(__file__).parent / "data" / "unrexpr"
SRC = (DATA / "m_ex.sv").read_bytes()


def load(name):
    return (json.loads((DATA / f"{name}.tree.json").read_text(encoding="utf-8")),
            json.loads((DATA / f"{name}.meta.json").read_text(encoding="utf-8")))


def wanted(todo):
    w = defaultdict(list)
    for k in todo:
        w[k[1:4]].append(k[4])
    return dict(w)


class UnrExpr(unittest.TestCase):
    def setUp(self):
        self.todo = ue.targets(DATA / "coverage.dat", ["m_ex.sv"])
        self.t0, self.m0 = load("m_ex")
        self.sites, self.why = ue.locate(self.t0, self.m0, wanted(self.todo), {"m_ex.sv": 0})

    def test_targets_are_points_no_run_hit(self):
        self.assertEqual(len(self.todo), 17)
        self.assertIn(("", "m_ex.sv", 20, 17, "(a==1 && b==1) => 1"), self.todo)
        self.assertNotIn(("", "m_ex.sv", 20, 17, "(a==0) => 0"), self.todo)       # hit
        with tempfile.TemporaryDirectory() as d:                                 # summed over instances' runs
            dat = Path(d) / "coverage.dat"
            line = [x for x in (DATA / "coverage.dat").read_text(encoding="utf-8").splitlines()
                    if "(a==1 && b==1) => 1" in x and "l\x0220\x01" in x][0]
            dat.write_text(line + "\n" + line[:line.rindex("'") + 1] + " 3\n"
                           + line.replace("nnc_tb_top.u_dut", "nnc_tb_top") + "\n", encoding="utf-8")
            self.assertEqual(ue.targets(dat, ["m_ex.sv"]), [])

    def test_terms_and_names(self):
        self.assertEqual(ue.terms("((we == 1'h1)==0 && de==1) => 0"), [("(we == 1'h1)", 0), ("de", 1)])
        self.assertIsNone(ue.terms("(a==1 && (b==1) => 1"))
        self.assertIsNone(ue.terms("a==1 => 1"))
        self.assertEqual(ue.condition("(a==0 && b[3]==1) => 1"), "((|(a)) == 1'b0) && ((|(b[3])) == 1'b1)")
        self.assertEqual(ue.selected("$unsigned(1'(x[32'h4 +: 2])) & y & s.f[1] & p::K[1]"), {"x"})
        self.assertEqual(ue.names("in0_i"), ({"in0_i"}, False))                  # digits inside a name
        self.assertEqual(ue.names("$unsigned(2'(x[32'sh1 - 4'd2])) & p::K & s.f"), ({"x", "s"}, False))
        self.assertEqual(ue.names("mubi4_test_true(en)"), ({"mubi4_test_true", "en"}, True))
        # chained constant selects (a struct member's bits, gpio): one select, which Yosys reads
        self.assertEqual(ue.flat_selects("{reg2hw[321:312][3:2][0], tl_i[107:101][3]} & x[2][1]"),
                         "{reg2hw[314], tl_i[104]} & x[2][1]")         # [1] of one bit: kept
        self.assertEqual(ue.flat_selects("a[9:2][5:4] | b[7:0] | c[3:0][4] | d[1:2][0]"),
                         "a[7:6] | b[7:0] | c[3:0][4] | d[1:2][0]")                    # out of range: kept
        self.assertEqual(ue.condition("(r[9:0][3:2][1]==1) => 1"), "((|(r[3])) == 1'b1)")

    def test_locate_keeps_only_terms_with_the_same_meaning_at_module_level(self):
        self.assertEqual(sorted(self.sites), [("m_ex.sv", 20, 17), ("m_ex.sv", 23, 18), ("m_ex.sv", 29, 11),
                                              ("m_ex.sv", 30, 12), ("m_ex.sv", 38, 30), ("m_ex.sv", 44, 20),
                                              ("m_ex.sv", 47, 20)])
        self.assertEqual(self.sites[("m_ex.sv", 38, 30)].combos, ["(q==0) => 1", "(q==1) => 0"])  # NBA: kept
        self.assertEqual(self.sites[("m_ex.sv", 23, 18)].mod_line, 2)            # in a generate block: ports
        # `t = a ^ b; y3 = t & b;` in always_comb: t is written before the expression only, so the expression
        # reads its last value, which is t at module level
        self.assertEqual(self.sites[("m_ex.sv", 30, 12)].combos, ["(t==1 && b==1) => 1"])
        w = {k[1:]: v for k, v in self.why.items()}
        self.assertEqual(w[(18, 14, "(a==0) => 0")], "in a function, task or initial block")
        self.assertEqual(w[(24, 19, "(g==1 && b==1) => 1")],
                         "a term reads a name that is not declared at module level")      # generate-local
        self.assertEqual(w[(34, 41, "(v[i[1:0]+:1]==1 && b==1) => 1")],
                         "a term reads a name that is not declared at module level")      # loop variable
        self.assertEqual(w[(38, 16, "(a==1 && f(b)==1) => 1")], "a term calls a function")
        _s, why = ue.locate(self.t0, self.m0, {("m_ex.sv", 20, 17): ["(a.x[1]==1) => 1"]})
        self.assertEqual(list(why.values()), ["a term selects a member (its bit numbering is not checked)"])
        # bit selects: only where Verilator's index and the source's agree (s_t packed struct, logic [3:0] v)
        self.assertEqual(self.sites[("m_ex.sv", 44, 20)].combos, ["(s[3]==1 && b==1) => 1"])
        self.assertEqual(self.sites[("m_ex.sv", 47, 20)].combos, ["(v[2]==1 && b==1) => 1"])
        no_vec = "a term selects bits of a signal that is not a packed vector [H:0]"
        self.assertEqual(w[(45, 20, "(w[1]==1 && b==1) => 1")], no_vec)                  # logic [8:1]
        self.assertEqual(w[(46, 24, "(pa[$unsigned(3'((32'h2 * 32'sh3)))+:2][0]==1 && b==1) => 1")], no_vec)
        self.assertEqual(len(self.why) + sum(len(s.combos) for s in self.sites.values()), 17)

    def test_instrument_keeps_every_line(self):
        new, bad, spans = ue.instrument({"m_ex.sv": SRC}, self.sites)
        self.assertEqual(bad, {})
        old, lines = SRC.decode().split("\n"), new["m_ex.sv"].decode().split("\n")
        self.assertEqual(len(lines), len(old))
        last = lines[47]
        self.assertTrue(last.endswith("endmodule"))
        self.assertIn("(* keep *) wire nnc_ex0_20_17_0 = ((|(a)) == 1'b1) && ((|(b)) == 1'b1); ", last)
        self.assertIn("(* keep *) wire nnc_ex0_38_30_1 = ((|(q)) == 1'b1); ", last)
        self.assertIn("(* keep *) wire nnc_ex0_44_20_0 = ((|(s[3])) == 1'b1) && ((|(b)) == 1'b1); ", last)
        self.assertEqual([x for i, x in enumerate(lines) if i != 47], [x for i, x in enumerate(old) if i != 47])
        # every declaration's columns, for Verilator's errors
        (line, c0, c1, mk), = [s for s in spans["m_ex.sv"] if s[3] == {"nnc_ex0_23_18_0"}]
        self.assertEqual(line, 48)
        self.assertTrue(last[c0 - 1:c1 - 1].startswith("(* keep *) wire nnc_ex0_23_18_0 ="))
        log = f"%Error: /root/x/src/m_ex.sv:48:{c0 + 30}: Illegal bit select\n%Error: other.sv:48:{c0}: x\n"
        self.assertEqual(ue.error_markers(log, spans), {"nnc_ex0_23_18_0"})
        self.assertEqual(ue.error_files("no netlist: m_ex.sv:48: ERROR: cannot refer | other.sv:3: x",
                                        {"m_ex.sv"}), {"m_ex.sv"})

    def test_markers_go_in_batches_that_keep_each_endmodule_line_short(self):
        # Verilator stops on a line of more than 40000 tokens (ot_gpio: 616 markers on one endmodule line)
        self.assertEqual(ue.tokens("(* keep *) wire m = ((|(a[3])) == 1'b0);"), 23)   # "==" counts 2: an upper bound
        n = {k: sum(ue.tokens(f"(* keep *) wire {s.marker(i)} = {ue.condition(c)}; ") for i, c in enumerate(s.combos))
             for k, s in self.sites.items()}
        self.assertEqual(ue.batches(self.sites), [dict(sorted(self.sites.items()))])        # one module, short
        limit = max(n.values()) + 1
        parts = ue.batches(self.sites, limit)
        self.assertGreater(len(parts), 1)
        self.assertEqual(sorted(k for p in parts for k in p), sorted(self.sites))          # each site once
        for p in parts:
            self.assertLessEqual(sum(n[k] for k in p), limit)
        one = ue.batches(self.sites, 1)                                                     # above the limit: alone
        self.assertEqual([len(p) for p in one], [1] * len(self.sites))
        b = ue.Site("b.sv", 3, 4, 1, ["(x==1) => 1"])                                        # another module: no load
        self.assertEqual(len(ue.batches({**self.sites, ("b.sv", 3, 4): b}, limit)), len(parts))

    def test_the_copy_is_checked(self):
        t1, m1 = load("m_ex_copy")
        # the copy was written with the markers of phase 24, before line 30 could be tried
        self.assertEqual(ue.verify(self.t0, self.m0, t1, m1, self.sites),
                         {"nnc_ex0_30_12_0": "marker not declared at module level in the copy"})
        self.sites.pop(("m_ex.sv", 30, 12))
        self.assertEqual(ue.verify(self.t0, self.m0, t1, m1, self.sites), {})
        # a marker that reads a name the module does not declare
        t2 = copy.deepcopy(t1)
        mod = t2["modulesp"][0]
        for a in mod["stmtsp"]:
            for st in a.get("stmtsp") or []:
                if isinstance(st, dict) and st.get("type") == "ASSIGNW" and \
                        (st.get("lhsp") or [{}])[0].get("name") == "nnc_ex0_20_17_0":
                    st["rhsp"] = [{"type": "VARREF", "name": "g"}]
        self.assertEqual(ue.verify(self.t0, self.m0, t2, m1, self.sites),
                         {"nnc_ex0_20_17_0": "marker reads a name that is not at module level in the copy"})
        # a marker missing from the copy
        t3 = copy.deepcopy(t1)
        t3["modulesp"][0]["stmtsp"] = [s for s in t3["modulesp"][0]["stmtsp"]
                                       if not (s.get("type") == "VAR" and s.get("name") == "nnc_ex0_29_11_1")]
        self.assertEqual(ue.verify(self.t0, self.m0, t3, m1, self.sites)["nnc_ex0_29_11_1"],
                         "marker not declared at module level in the copy")
        # the copy has an IF the original has not: nothing is trusted
        t4 = copy.deepcopy(t1)
        t4["modulesp"][0]["stmtsp"].append({"type": "ALWAYS", "loc": "e,30:3,30:9", "keyword": "always_comb",
                                            "stmtsp": [{"type": "IF", "loc": "e,30:20,30:22"}]})
        self.assertEqual(len(ue.verify(self.t0, self.m0, t4, m1, self.sites)), 8)        # every marker

    def test_writes_after_the_expression_in_a_combinational_block(self):
        # always_comb begin s = a ^ b; y = (s == 1) & b; e[0] = ^s; e[1] = |s & ~e[0];
        #   if (y) begin x = 1; end else begin z = 0; end  for (...) begin w = w | s; end  end
        ref = lambda n: {"type": "VARREF", "name": n}
        sel = lambda n, i: {"type": "SEL", "fromp": [ref(n)], "lsbp": [{"type": "CONST", "name": f"1'h{i}"}],
                            "widthConst": 1}
        expr, not_e0, cond, in_loop = {"type": "EQ"}, {"type": "NOT", "lhsp": [sel("e", 0)]}, ref("y"), {"type": "OR"}
        a1 = {"type": "ASSIGN", "rhsp": [ref("a")], "lhsp": [ref("s")]}
        a2 = {"type": "ASSIGN", "rhsp": [expr], "lhsp": [ref("y")]}
        a3 = {"type": "ASSIGN", "rhsp": [ref("s")], "lhsp": [sel("e", 0)]}
        a4 = {"type": "ASSIGN", "rhsp": [not_e0], "lhsp": [sel("e", 1)]}
        in_then = {"type": "AND"}
        then = {"type": "ASSIGN", "rhsp": [in_then], "lhsp": [ref("x")]}
        els = {"type": "ASSIGN", "rhsp": [], "lhsp": [ref("z")]}
        if_ = {"type": "IF", "condp": [cond], "thensp": [then], "elsesp": [els]}
        lw = {"type": "ASSIGN", "rhsp": [in_loop], "lhsp": [ref("w")]}
        loop = {"type": "WHILE", "condp": [], "stmtsp": [lw]}
        blk = {"type": "BEGIN", "stmtsp": [a1, a2, a3, a4, if_, loop]}
        alw = {"type": "ALWAYS", "keyword": "always_comb", "stmtsp": [blk]}
        base = [{"type": "MODULE"}, alw, blk]
        self.assertEqual(ue.written_after(base + [a2, expr]), {"y": None, "e": {0, 1}, "x": None, "z": None, "w": None})
        self.assertEqual(ue.written_after(base + [a4, not_e0]), {"e": {1}, "x": None, "z": None, "w": None})
        self.assertEqual(ue.written_after(base + [if_, cond]), {"x": None, "z": None, "w": None})   # both branches
        self.assertEqual(ue.written_after(base + [if_, then, in_then]), {"x": None, "w": None})              # not the else
        self.assertEqual(ue.written_after(base + [loop, lw, in_loop]), {"w": None})                 # the loop again
        # bits: a select of a packed vector [H:0] is compared bit by bit, anything else is the whole signal
        types = {"(A)": {"type": "BASICDTYPE", "range": "1:0"}, "(B)": {"type": "BASICDTYPE", "range": "2:1"}}
        self.assertFalse(ue._overlap({1}, ["e[0]", "s"], "e", types, [{"e": "(A)"}]))      # e[1] = ..e[0]..
        self.assertTrue(ue._overlap({0, 1}, ["e[0]"], "e", types, [{"e": "(A)"}]))
        self.assertTrue(ue._overlap({1}, ["e[0]"], "e", types, [{"e": "(B)"}]))             # [2:1]: not compared
        self.assertTrue(ue._overlap(None, ["e[0]"], "e", types, [{"e": "(A)"}]))
        self.assertEqual(ue.term_bits("e[0] | ee[1] | x.e", "e"), {0})
        self.assertIsNone(ue.term_bits("e[0] & e", "e"))
        self.assertEqual(ue.term_bits("(r[9:0][3:2][1] == 1'b0)", "r"), {3})
        self.assertEqual([ue._const({"type": "CONST", "name": n}) for n in ("1'h1", "32'sh5", "4'b1010", "7", "1'hx")],
                         [1, 5, 10, 7, None])

    def test_enum_items_of_module_types_are_module_names(self):
        types = {"(T)": {"type": "ENUMDTYPE", "addr": "(T)", "dtypep": "(T)",
                         "itemsp": [{"type": "ENUMITEM", "name": "ST_IDLE"}, {"type": "ENUMITEM", "name": "ST_RUN"}]},
                 "(R)": {"type": "REFDTYPE", "addr": "(R)", "refDTypep": "(U)"},
                 "(U)": {"type": "ENUMDTYPE", "addr": "(U)", "itemsp": [{"type": "ENUMITEM", "name": "B_ON"}]},
                 "(L)": {"type": "BASICDTYPE", "addr": "(L)", "range": "3:0"}}
        mod = {"type": "MODULE", "stmtsp": [{"type": "TYPEDEF", "name": "st_t", "dtypep": "(T)"},
                                            {"type": "VAR", "name": "b", "dtypep": "(R)"},
                                            {"type": "VAR", "name": "c", "dtypep": "(L)"}]}
        self.assertEqual(ue.enum_names(mod, types), {"ST_IDLE", "ST_RUN", "B_ON"})

    def test_points_of_one_configuration(self):
        # ROADMAP 24.5: merged.dat keeps one record per run-set configuration (C01, C02 in the source path)
        line = [x for x in (DATA / "coverage.dat").read_text(encoding="utf-8").splitlines()
                if "(a==1 && b==1) => 1" in x and "l\x0220\x01" in x][0]
        f = line.split("\x01")[1].split("\x02")[1]
        rec = line[:line.rindex("'") + 1]
        key = ("", "m_ex.sv", 20, 17, "(a==1 && b==1) => 1")
        self.assertEqual(cov.config_folder("/root/nnc_runs/runset_ab12/C02/rtl/m_ex.sv"), "C02")
        self.assertEqual(cov.config_folder("/root/nnc_runs/sim_ab12/rtl/m_ex.sv"), "")
        with tempfile.TemporaryDirectory() as d:
            dat = Path(d) / "coverage.dat"
            dat.write_text(rec.replace(f, "/r/runset_1/C01/rtl/m_ex.sv") + " 0\n"
                           + rec.replace(f, "/r/runset_1/C02/rtl/m_ex.sv") + " 3\n", encoding="utf-8")
            self.assertEqual(ue.targets(dat, ["m_ex.sv"]), [])                 # hit in the run set
            self.assertEqual(ue.targets(dat, ["m_ex.sv"], "C01"), [key])       # never hit in C01
            self.assertEqual(ue.targets(dat, ["m_ex.sv"], "C02"), [])
            base = cov.parse_dat(dat, ["m_ex.sv"], {"packages": [], "kept": {}})["metrics"]["expression"]
            self.assertEqual((base["hit"], base["total"]), (1, 2))
            r = cov.parse_dat(dat, ["m_ex.sv"], {"packages": [], "kept": {}, "proven_exprs_by_config": {"C01": [list(key)]}})
            self.assertEqual((r["metrics"]["expression"]["hit"], r["metrics"]["expression"]["total"]), (1, 1))
            pu = r["scope"]["proven_unreachable"]
            self.assertEqual((pu["expressions_left_out"], pu["expressions_executed"]), (1, 0))
            r = cov.parse_dat(dat, ["m_ex.sv"], {"packages": [], "kept": {}, "proven_exprs_by_config": {"C02": [list(key)]}})
            pu = r["scope"]["proven_unreachable"]                               # hit in C02: counted, reported
            self.assertEqual((pu["expressions_left_out"], pu["expressions_executed"]), (0, 1))
        from nnc import unrbranch as ub
        part = {"A": {"proven": [list(key)]}, "B": {"proven": []}}
        self.assertEqual(ub.proven_by_config(part, ["A", "B"], ["C01", "C02"]), {"C01": [list(key)]})
        self.assertEqual(ub.proven_by_config(part, ["A", "A"], ["C01", "C02"]),          # same proof, two folders
                         {"C01": [list(key)], "C02": [list(key)]})
        self.assertEqual(ub.proven_by_config(part, ["A"], [None]), {})                    # one run, no folder
        self.assertEqual(ub.proven_blocks(part, ["A", "B"]), [])

    def test_lines_of_one_configuration(self):
        from nnc import sim
        with tempfile.TemporaryDirectory() as d:
            info = Path(d) / "merged.info"
            info.write_text("SF:/r/runset_1/C01/rtl/m.sv\nDA:5,0\nDA:6,1\nend_of_record\n"
                            "SF:/r/runset_1/C02/rtl/m.sv\nDA:5,2\nDA:6,0\nend_of_record\n", encoding="utf-8")
            r = sim._line_coverage(info, ["m.sv"], {("C01", "m.sv", 5)})
            self.assertEqual((r["hit"], r["total"], r["left_out_lines"]), (2, 3, 1))
            r = sim._line_coverage(info, ["m.sv"], {("m.sv", 5)})              # a key without folder: no run set
            self.assertEqual((r["hit"], r["total"], r["left_out_lines"]), (2, 4, 0))

    def test_proven_points_leave_the_expression_coverage(self):
        dat = DATA / "coverage.dat"
        base = cov.parse_dat(dat, ["m_ex.sv"], {"packages": [], "kept": {}})
        k_hit = ("", "m_ex.sv", 20, 17, "(a==0) => 0")
        k_new = ("", "m_ex.sv", 20, 17, "(a==1 && b==1) => 1")
        r = cov.parse_dat(dat, ["m_ex.sv"], {"packages": [], "kept": {}, "proven_exprs": [list(k_new), list(k_hit)]})
        e0, e1 = base["metrics"]["expression"], r["metrics"]["expression"]
        self.assertEqual((e1["hit"], e1["total"]), (e0["hit"], e0["total"] - 1))   # the hit one stays counted
        pu = r["scope"]["proven_unreachable"]
        self.assertEqual((pu["expressions_left_out"], pu["expressions_executed"]), (1, 1))


if __name__ == "__main__":
    unittest.main()

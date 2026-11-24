"""Formal unreachability of branches (nnc/unrbranch.py, ROADMAP 23.3): no tool runs here. The Verilator trees
of tests/data/unrbranch (the design and its instrumented copy) were written by `verilator --json-only
-fno-const -fno-const-before-dfg` and trimmed to the fields the module reads."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from nnc import unrbranch as ub

DATA = Path(__file__).parent / "data" / "unrbranch"
SRC = (DATA / "m_br.sv").read_bytes()
WANT = {("m_br.sv", 14, 7, "if"), ("m_br.sv", 15, 12, "if"), ("m_br.sv", 15, 13, "else"),
        ("m_br.sv", 17, 13, "case"), ("m_br.sv", 19, 9, "case"), ("m_br.sv", 26, 17, "case"),
        ("m_br.sv", 27, 7, "case"), ("m_br.sv", 29, 5, "if"), ("m_br.sv", 29, 6, "else"), ("m_br.sv", 10, 5, "if")}


def load(name):
    return (json.loads((DATA / f"{name}.tree.json").read_text(encoding="utf-8")),
            json.loads((DATA / f"{name}.meta.json").read_text(encoding="utf-8")))


def block(h, line, col, o, n, span=None):
    s = f"\x01S\x02{span}" if span else ""
    return (f"C '\x01f\x02/x/m_br.sv\x01l\x02{line}\x01n\x02{col}\x01t\x02line\x01page\x02v_line/m_br"
            f"\x01o\x02{o}{s}\x01h\x02{h}' {n}\n")


class UnrBranch(unittest.TestCase):
    def setUp(self):
        self.t0, self.m0 = load("m_br")
        self.sites, self.why = ub.locate(self.t0, self.m0, WANT, {"m_br.sv": 0})

    def test_targets_are_branches_no_run_executed(self):
        with tempfile.TemporaryDirectory() as d:
            dat = Path(d) / "coverage.dat"
            dat.write_text(block("nnc_tb_top.u_dut", 14, 7, "if", 0, "14") + block("nnc_tb_top.u_dut", 14, 7, "if", 0, "14")
                           + block("nnc_tb_top.u_dut", 15, 13, "else", 4)
                           + block("nnc_tb_top.u_dut.u_a", 19, 9, "case", 0, "19")
                           + block("nnc_tb_top.u_dut.u_b", 19, 9, "case", 2, "19")
                           + block("nnc_tb_top.u_dut", 9, 3, "block", 0, "9-10")       # not a branch
                           + block("nnc_tb_top", 14, 7, "if", 0), encoding="utf-8")   # outside the DUT
            t = ub.targets(dat, ["m_br.sv"])
        self.assertEqual(t, {("", "m_br.sv", 14, 7, "if"): [14], ("u_a", "m_br.sv", 19, 9, "case"): [19]})

    def test_locate_by_line_and_column(self):
        self.assertEqual(set(self.sites), WANT - {("m_br.sv", 10, 5, "if")})
        self.assertEqual(self.why, {("m_br.sv", 10, 5, "if"): "the reset branch"})
        s = self.sites[("m_br.sv", 15, 13, "else")]
        self.assertTrue(s.clocked)
        self.assertIsNotNone(s.reset)                               # asynchronous reset: marker reset there
        self.assertEqual(s.marker, "nnc_br0_15_13_e")
        self.assertFalse(self.sites[("m_br.sv", 29, 5, "if")].clocked)
        # a column that is not the IF's: not found
        _s, why = ub.locate(self.t0, self.m0, {("m_br.sv", 14, 8, "if")})
        self.assertEqual(why[("m_br.sv", 14, 8, "if")], "not in an always block at module level")
        # without a column, the line must hold one IF
        s2, _w = ub.locate(self.t0, self.m0, {("m_br.sv", 14, 0, "if")})
        self.assertEqual(len(s2), 1)

    def test_instrument_keeps_every_line(self):
        new, bad = ub.instrument({"m_br.sv": SRC}, self.sites)
        self.assertEqual(bad, {("m_br.sv", 27, 7, "case"): "empty branch"})
        text = new["m_br.sv"].decode()
        old = SRC.decode().split("\n")
        lines = text.split("\n")
        self.assertEqual(len(lines), len(old))
        self.assertIn("if (!rst_n) begin nnc_br0_14_7_t <= 1'b0;", lines[9])
        self.assertTrue(lines[13].endswith("if (s == 2'd3) begin nnc_br0_14_7_t <= ~nnc_br0_14_7_t; q <= 1'b1; end"))
        self.assertTrue(lines[14].endswith("q <= 1'b0; end else begin nnc_br0_15_13_e <= ~nnc_br0_15_13_e; end"))
        self.assertIn("2'd0: begin nnc_br0_17_13_c <= ~nnc_br0_17_13_c; st <= 2'd1; end", lines[16])
        self.assertIn("default: begin nnc_br0_19_9_c <= ~nnc_br0_19_9_c; st <= 2'd0; end", lines[18])
        self.assertIn("always_comb begin nnc_br0_26_17_c = 1'b0;", lines[22])
        # the end goes after the statement's own semicolon, not the one in the comment
        self.assertIn("q2 = 1'b1; end else begin nnc_br0_29_6_e = 1'b1; end // a comment ; with a semicolon",
                      lines[28])
        for i, (a, b) in enumerate(zip(old, lines)):               # only insertions
            it = iter(b)
            self.assertTrue(all(c in it for c in a), i + 1)

    def test_the_copy_is_checked(self):
        new, bad = ub.instrument({"m_br.sv": SRC}, self.sites)
        for k in bad:
            self.sites.pop(k)
        t1, m1 = load("m_br_copy")
        shift = ub.shifter({"m_br.sv": SRC}, self.sites)
        self.assertEqual(ub.verify(self.t0, self.m0, t1, m1, self.sites, shift), {})
        # a marker that is not the first statement of its branch in the copy
        t2 = copy.deepcopy(t1)
        sites = dict(self.sites)
        s = sites[("m_br.sv", 14, 7, "if")]
        sites[("m_br.sv", 14, 7, "if")] = ub.Site(s.file, s.line, s.col, s.kind, s.clocked, s.always, s.node,
                                                    s.block, 7, s.reset)
        why = ub.verify(self.t0, self.m0, t2, m1, sites, shift)
        self.assertEqual(why, {("m_br.sv", 14, 7, "if"): "marker is not the first statement of the branch in the copy"})
        # the copy has an IF the original has not: nothing is trusted
        t3 = copy.deepcopy(t1)
        t3["modulesp"][0]["stmtsp"].append({"type": "ALWAYS", "loc": "e,30:3,30:9", "keyword": "always_comb",
                                            "stmtsp": [{"type": "IF", "loc": "e,30:20,30:22"}]})
        self.assertEqual(set(ub.verify(self.t0, self.m0, t3, m1, self.sites, shift)), set(self.sites))

    def test_text_scanning(self):
        src = ub._Src(b'x = f(a, ";", b[1:0]) /* ; */ ; y = 1; begin : l1 begin end end : l1 z;\n'
                      b'case (s) A::B: q = 1; endcase')
        self.assertEqual(src.b[:src.scan(0, b";")], b'x = f(a, ";", b[1:0]) /* ; */ ;')
        b = src.b.index(b"begin")
        self.assertEqual(src.b[b:src.block_end(b)], b"begin : l1 begin end end : l1")
        self.assertEqual(src.after_label(b + 5), src.b.index(b"l1") + 2)
        self.assertIsNone(src.stmt_end(src.b.index(b"begin")))       # compound: not wrapped
        self.assertIsNone(src.stmt_end(src.b.index(b"case")))
        i = src.b.index(b"A::B")
        self.assertEqual(src.b[i:src.scan(i, b":")], b"A::B:")           # "::" is not the item's colon
        self.assertEqual(src.b[:src.paren_end(src.b.index(b"(a"))], b'x = f(a, ";", b[1:0])')

    def test_record(self):
        k1, k2, k3 = ("", "m.sv", 3, 5, "if"), ("u", "m.sv", 9, 7, "case"), ("", "m.sv", 4, 5, "else")
        a = {"proven": [list(k1)], "cex": [], "open": [list(k2)], "skipped": {"x": [list(k3)]}, "tasks": 1}
        self.assertEqual(ub.undecided(a, {k1: [3], k2: [9], k3: [4]}), {k2: [9], k3: [4]})
        m = ub.merge(a, {"proven": [list(k2)], "cex": [], "open": [], "skipped": {}, "tasks": 1})
        self.assertEqual((m["proven"], m["open"], m["skipped"], m["tasks"]), ([list(k1), list(k2)], [], {"x": [list(k3)]}, 2))
        b = {"proven": [list(k2)], "cex": [list(k1)]}
        self.assertEqual(ub.proven_blocks({"A": m, "B": b}, ["A", "B"]), [list(k2)])
        self.assertIsNone(ub.proven_blocks({"A": m}, ["A", "B"]))


if __name__ == "__main__":
    unittest.main()

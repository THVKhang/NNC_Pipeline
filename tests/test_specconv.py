"""Word and HTML specifications (nnc/specconv.py): headings, lists and tables reach the index, and the contract
reads the port table; Vietnamese normative words; the scanned-document check of spec-check."""
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from nnc import contract, specconv
from nnc.ingest import NORMATIVE_RE, build_index
from nnc.specdraft import check_spec

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def para(text, style=None, numbered=False):
    ppr = ""
    if style or numbered:
        ppr = "<w:pPr>" + (f'<w:pStyle w:val="{style}"/>' if style else "") + \
              ('<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>' if numbered else "") + "</w:pPr>"
    return f"<w:p>{ppr}<w:r><w:t>{text}</w:t></w:r></w:p>"


def table(rows):
    return "<w:tbl>" + "".join("<w:tr>" + "".join(f"<w:tc>{para(c)}</w:tc>" for c in r) + "</w:tr>" for r in rows) + \
        "</w:tbl>"


PORTS = [["Port", "Direction", "Width", "Signal type", "Reset value", "Clock domain", "Meaning"],
         ["i_clk", "input", "1", "Clock", "Not applicable", "CLK", "Clock"],
         ["i_rst_n", "input", "1", "Reset", "Not applicable", "CLK", "Active-low reset"],
         ["i_d", "input", "8", "Data", "0", "CLK", "Data in"],
         ["o_q", "output", "8", "Data", "0", "CLK", "Data out"]]


class DocxTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_docx_port_table(self):
        body = (para("Demo register", "Heading1") + para("The register shall hold its value.") +
                para("It must not change while i_en is 0.", numbered=True) +
                para("Interface", "Heading1") + para("m_demo: all ports") + table(PORTS))
        styles = (f'<w:styles {W}><w:style w:styleId="Heading1"><w:name w:val="heading 1"/></w:style></w:styles>')
        f = self.tmp / "spec.docx"
        with zipfile.ZipFile(f, "w") as z:
            z.writestr("word/document.xml", f'<w:document {W}><w:body>{body}</w:body></w:document>')
            z.writestr("word/styles.xml", styles)
        md = specconv.to_markdown(f)
        self.assertIn("# Demo register", md)
        self.assertIn("- It must not change while i_en is 0.", md)
        self.assertIn("| i_clk | input | 1 | Clock |", md)
        idx = build_index(f)
        self.assertEqual(idx["doc"]["location"], "line of the converted text")
        self.assertGreaterEqual(idx["stats"]["normative"], 2)
        iface = contract.extract_interface(idx)
        self.assertEqual([p["name"] for p in iface["ports"]], ["i_clk", "i_rst_n", "i_d", "o_q"])
        self.assertEqual(iface["clock"], "i_clk")

    def test_html_port_table(self):
        f = self.tmp / "spec.html"
        rows = "".join("<tr>" + "".join(f"<{'th' if i == 0 else 'td'}>{c}</{'th' if i == 0 else 'td'}>" for c in r)
                       + "</tr>" for i, r in enumerate(PORTS))
        f.write_text("<html><head><style>p{}</style></head><body><h1>Demo</h1><p>The output shall be "
                     "registered.</p><ul><li>One item.</li></ul><h2>Ports</h2><table>" + rows +
                     "</table><pre>code  kept</pre></body></html>", encoding="utf-8")
        md = specconv.to_markdown(f)
        self.assertIn("# Demo", md)
        self.assertIn("- One item.", md)
        self.assertIn("```\ncode  kept\n```", md)
        self.assertNotIn("p{}", md)
        iface = contract.extract_interface(build_index(f))
        self.assertEqual(len(iface["ports"]), 4)

    def test_virtual_clock_for_a_combinational_design(self):
        f = self.tmp / "comb.md"
        f.write_text("# Encoder\n\n## Ports\n\n| Port | Direction | Width | Signal type | Meaning |\n|---|---|---|---|---|\n"
                     "| i_x | input | 8 | Data | value |\n| o_y | output | 3 | Data | index |\n", encoding="utf-8")
        iface = contract.extract_interface(build_index(f))
        self.assertEqual(iface["clock"], contract.VIRTUAL_CLOCK)
        self.assertTrue(iface["ports"][0]["virtual"])
        self.assertEqual([p["name"] for p in contract.dut_ports(iface["ports"])], ["i_x", "o_y"])
        res = check_spec(f, None)
        self.assertTrue(any("virtual clock nnc_clk" in x["message"] for x in res["findings"]))
        self.assertFalse(any("port nnc_clk" in x["message"] for x in res["findings"]))
        self.assertFalse([x for x in res["findings"] if x["severity"] == "error"])


class AsciiDocTest(unittest.TestCase):
    """The shapes of the RISC-V specification (riscv-isa-manual): role spans, instruction macros, tables
    with column and row spans, admonition blocks, includes of AsciiDoc fragments."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_riscv_shapes(self):
        (self.tmp / "img").mkdir()
        (self.tmp / "img" / "op.edn").write_text("[wavedrom, ,svg]\n....\n{reg: [{bits: 7, name: 'opcode'}]}\n....\n",
                                                encoding="utf-8")
        (self.tmp / "m.adoc").write_text(r"""[[ext:m]]
=== ext:m[] Extension
// a comment
////
a comment block
////
include::img/op.edn[]
[#norm:div_op]#insn:div[] and insn:divu[] perform a division
of `rs1` by `rs2`.# (((MUL, DIV))) The quotient is 2^L^-1 or -2^L-1^ {times} 1.

[NOTE]
====
dividend = divisor {times} quotient + remainder.
====

.Semantics for division by zero
[cols="<2,^,^",options="header",]
|===
|Condition |Divisor |insn:div[]
|Division by zero |0 |-1
|===

[cols="^2m,^2m,^2m,^2m"]
|===
    |31 |  20|19 |0
 2+^|funct7  .2+|rs1 |x
 2+^|imm[12\|10:5]    |y
|===
""", encoding="utf-8")
        md = specconv.to_markdown(self.tmp / "m.adoc")
        self.assertIn("### m Extension", md)
        self.assertIn("```wavedrom\n{reg: [{bits: 7, name: 'opcode'}]}\n```", md)
        self.assertIn("`div` and `divu` perform a division of `rs1` by `rs2`. The quotient is 2^(L)-1 or "
                      "-2^(L-1) × 1.", md)
        self.assertNotIn("comment", md)
        self.assertIn("**Note:**\ndividend = divisor × quotient + remainder.", md)
        self.assertIn("**Semantics for division by zero**", md)
        self.assertIn("| Condition | Divisor | `div` |\n|---|---|---|\n| Division by zero | 0 | -1 |", md)
        # a 2-column span, then a 2-row span that keeps its column free in the next row; an escaped pipe
        self.assertIn("| 31 | 20 | 19 | 0 |", md)
        self.assertIn("| funct7 |  | rs1 | x |", md)
        self.assertIn("| imm[12\\|10:5] |  |  | y |", md)

    def test_missing_include_is_named(self):
        (self.tmp / "a.adoc").write_text("== A\n\ninclude::nowhere.adoc[]\n", encoding="utf-8")
        self.assertIn("(included file not available: nowhere.adoc)", specconv.to_markdown(self.tmp / "a.adoc"))

    def test_index_reads_asciidoc(self):
        f = self.tmp / "s.adoc"
        f.write_text("== Division\n\nThe quotient of division by zero must have all bits set.\n", encoding="utf-8")
        idx = build_index(f)
        self.assertTrue(any("must have all bits set" in s["text"] for sec in idx["sections"]
                            for s in sec["sentences"]))


class SetextTest(unittest.TestCase):
    def test_setext_headings_are_sections(self):
        # picorv32's README underlines its section titles; YAML front matter is not a heading
        tmp = Path(tempfile.mkdtemp())
        try:
            f = tmp / "r.md"
            f.write_text("---\ntitle: x\n---\n# Core\n\nText.\n\nPico Co-Processor Interface (PCPI)\n"
                         "----------------------------------\n\nThe core must assert pcpi_ready.\n\n"
                         "| a | b |\n|---|---|\n| 1 | 2 |\n", encoding="utf-8")
            idx = build_index(f)
            self.assertEqual([s["title"] for s in idx["sections"]],
                             ["Front matter", "Core", "Pico Co-Processor Interface (PCPI)"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class NormativeTest(unittest.TestCase):
    def test_vietnamese_keywords(self):
        self.assertTrue(NORMATIVE_RE.search("Tín hiệu phải giữ ổn định."))
        self.assertTrue(NORMATIVE_RE.search("Không được ghi khi FIFO đầy."))
        self.assertFalse(NORMATIVE_RE.search("Đây là mô tả."))


if __name__ == "__main__":
    unittest.main()

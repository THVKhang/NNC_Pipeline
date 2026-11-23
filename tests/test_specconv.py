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


class NormativeTest(unittest.TestCase):
    def test_vietnamese_keywords(self):
        self.assertTrue(NORMATIVE_RE.search("Tín hiệu phải giữ ổn định."))
        self.assertTrue(NORMATIVE_RE.search("Không được ghi khi FIFO đầy."))
        self.assertFalse(NORMATIVE_RE.search("Đây là mô tả."))


if __name__ == "__main__":
    unittest.main()

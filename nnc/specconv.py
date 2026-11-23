"""Word (.docx) and HTML specifications as Markdown text, for the Markdown reader of nnc/ingest.py (no tools,
Python standard library only).

Kept: headings (Word styles Heading 1-9 and Title, HTML h1-h6), paragraphs, list items, tables (as Markdown
tables, so the contract reads a port table from them) and preformatted code. Dropped: images, fields, headers,
footers, comments and tracked deletions. The index keeps the SHA-256 of the original file; locations are lines
of the converted text, which `nnc ingest` can write next to the original (`<name>.converted.md`) for the
reviewer.
"""
from __future__ import annotations

import html
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path

SUFFIXES = (".docx", ".html", ".htm")
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _cell(text: str) -> str:
    return re.sub(r"\s+", " ", text).replace("|", "\\|").strip()


def _table_md(rows: list[list[str]]) -> list[str]:
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        return []
    n = max(len(r) for r in rows)
    rows = [r + [""] * (n - len(r)) for r in rows]
    out = ["| " + " | ".join(_cell(c) for c in rows[0]) + " |", "|" + "---|" * n]
    out += ["| " + " | ".join(_cell(c) for c in r) + " |" for r in rows[1:]]
    return out


# ------------------------------------------------------------------------------------------------ Word
def _docx_text(el) -> str:
    parts = []
    for node in el.iter():
        tag = node.tag
        if tag == _W + "t":
            parts.append(node.text or "")
        elif tag == _W + "tab":
            parts.append(" ")
        elif tag in (_W + "br", _W + "cr"):
            parts.append(" ")
        elif tag == _W + "delText":      # tracked deletion: not part of the document
            continue
    return "".join(parts)


def _docx_heading(p, styles: dict[str, str]) -> int:
    ppr = p.find(_W + "pPr")
    if ppr is None:
        return 0
    st = ppr.find(_W + "pStyle")
    name = styles.get(st.get(_W + "val"), st.get(_W + "val")) if st is not None else ""
    m = re.match(r"(?i)heading\s*(\d)", name or "")
    if m:
        return int(m.group(1))
    if (name or "").lower() == "title":
        return 1
    lvl = ppr.find(_W + "outlineLvl")
    if lvl is not None and str(lvl.get(_W + "val", "")).isdigit():
        return int(lvl.get(_W + "val")) + 1
    return 0


def _docx_is_list(p) -> bool:
    ppr = p.find(_W + "pPr")
    return ppr is not None and ppr.find(_W + "numPr") is not None


def docx_to_markdown(path: Path) -> str:
    import xml.etree.ElementTree as ET
    with zipfile.ZipFile(path) as z:
        body = ET.fromstring(z.read("word/document.xml")).find(_W + "body")
        styles = {}
        if "word/styles.xml" in z.namelist():
            for s in ET.fromstring(z.read("word/styles.xml")).iter(_W + "style"):
                nm = s.find(_W + "name")
                if nm is not None:
                    styles[s.get(_W + "styleId")] = nm.get(_W + "val")
    out: list[str] = []
    for el in body:
        if el.tag == _W + "p":
            text = _docx_text(el).strip()
            if not text:
                continue
            h = _docx_heading(el, styles)
            if h:
                out += ["", "#" * min(h, 6) + " " + text, ""]
            elif _docx_is_list(el):
                out.append("- " + text)
            else:
                out += [text, ""]
        elif el.tag == _W + "tbl":
            rows = [[_docx_text(tc) for tc in tr.findall(_W + "tc")] for tr in el.findall(_W + "tr")]
            out += [""] + _table_md(rows) + [""]
    return _tidy(out)


# ------------------------------------------------------------------------------------------------ HTML
class _Html(HTMLParser):
    BLOCK = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "tr", "table", "br", "caption", "dt", "dd"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.buf: list[str] = []
        self.skip = 0
        self.heading = 0
        self.in_li = False
        self.pre = False
        self.table: list[list[str]] | None = None
        self.row: list[str] | None = None
        self.cell: list[str] | None = None

    def _flush(self):
        text = "".join(self.buf)
        self.buf = []
        if self.pre:
            if text.strip("\n"):
                self.out += ["```"] + text.strip("\n").splitlines() + ["```", ""]
            return
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return
        if self.heading:
            self.out += ["", "#" * self.heading + " " + text, ""]
        elif self.in_li:
            self.out.append("- " + text)
        else:
            self.out += [text, ""]

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "head", "nav", "footer"):
            self.skip += 1
            return
        if self.cell is not None and tag != "td" and tag != "th" and tag != "tr":
            return
        if tag in self.BLOCK:
            self._flush()
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.heading = int(tag[1])
        elif tag == "li":
            self.in_li = True
        elif tag == "pre":
            self.pre = True
        elif tag == "table":
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_endtag(self, tag):
        if tag in ("script", "style", "head", "nav", "footer"):
            self.skip = max(0, self.skip - 1)
            return
        if tag in ("td", "th") and self.cell is not None:
            self.row.append("".join(self.cell))
            self.cell = None
            return
        if self.cell is not None:
            return
        if tag == "tr" and self.row is not None:
            self.table.append(self.row)
            self.row = None
            return
        if tag == "table" and self.table is not None:
            self._flush()
            self.out += [""] + _table_md(self.table) + [""]
            self.table = None
            return
        if tag in self.BLOCK:
            self._flush()
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.heading = 0
        elif tag == "li":
            self.in_li = False
        elif tag == "pre":
            self.pre = False

    def handle_data(self, data):
        if self.skip:
            return
        if self.cell is not None:
            self.cell.append(data)
        else:
            self.buf.append(data)


def html_to_markdown(path: Path) -> str:
    p = _Html()
    p.feed(path.read_text(encoding="utf-8", errors="replace"))
    p._flush()
    return _tidy(p.out)


def _tidy(lines: list[str]) -> str:
    out: list[str] = []
    for line in lines:
        if line == "" and (not out or out[-1] == ""):
            continue
        out.append(html.unescape(line) if "&" in line else line)
    return "\n".join(out).strip() + "\n"


def to_markdown(path: Path) -> str:
    s = Path(path).suffix.lower()
    if s == ".docx":
        return docx_to_markdown(Path(path))
    if s in (".html", ".htm"):
        return html_to_markdown(Path(path))
    raise ValueError(f"no converter for {s}")

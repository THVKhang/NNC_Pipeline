"""Word (.docx), HTML and AsciiDoc specifications as Markdown text, for the Markdown reader of nnc/ingest.py (no
tools, Python standard library only).

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

SUFFIXES = (".docx", ".html", ".htm", ".adoc", ".asciidoc")
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


# --------------------------------------------------------------------------------------------- AsciiDoc
# The RISC-V specifications and many hardware documents are written in AsciiDoc. Kept: section titles, block
# titles (table captions), paragraphs, lists, tables (column and row spans laid out on the grid), admonitions,
# listing, literal and diagram source blocks (as code), and included files found next to the document.
# Dropped: comments, anchors, attribute lines, index terms, images and conditional directives (their content
# is kept).

_ADOC_ATTRS = {"times": "×", "plus": "+", "minus": "−", "nbsp": " ", "cpp": "C++", "ge": "≥", "le": "≤",
               "rarr": "→", "larr": "←", "lt": "<", "gt": ">", "amp": "&", "deg": "°", "pm": "±",
               "empty": "", "sp": " ", "zwsp": "", "quot": '"', "apos": "'", "brvbar": "¦", "vbar": "|"}
_ADOC_ADMONITION = ("NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION")
_ADOC_SPEC = re.compile(r"(?:(\d+)\*)?(?:(\d+)?(?:\.(\d+))?\+)?(?:[<^>])?(?:\.[<^>])?[aehlmsdv]?$")


def _adoc_inline(text: str, attrs: dict[str, str]) -> str:
    t = re.sub(r"\(\(\(.*?\)\)\)", "", text, flags=re.S)                       # index terms
    t = re.sub(r"\(\((.+?)\)\)", r"\1", t, flags=re.S)
    t = re.sub(r"\[[#.][\w:.\-]*\]#((?:(?!\n\n).)*?)#", r"\1", t, flags=re.S)  # [#id]#text# role spans
    t = re.sub(r"\binsn:([\w.]+)\[([^\]]*)\]",
               lambda m: f"`{m.group(1)}" + (f" {m.group(2)}" if m.group(2) else "") + "`", t)
    t = re.sub(r"\b(https?://[^\s\[]+)\[([^\]]*)\]", lambda m: f"{m.group(2) or m.group(1)} ({m.group(1)})", t)
    t = re.sub(r"\b(?:ext|csr|reg|term|kbd|btn|menu|footnote|link|xref|anchor):([^\s\[]*)\[([^\]]*)\]",
               lambda m: m.group(2) or m.group(1), t)
    t = re.sub(r"<<([^,>]+),\s*([^>]+)>>", r"\2", t)
    t = re.sub(r"<<([^>]+)>>", r"\1", t)
    t = re.sub(r"\^([^\^\s]+)\^", r"^(\1)", t)                                  # 2^L-1^ -> 2^(L-1)
    t = re.sub(r"~([^~\s]+)~", r"_(\1)", t)
    t = re.sub(r"\{([\w\-]+)\}", lambda m: attrs.get(m.group(1), _ADOC_ATTRS.get(m.group(1), m.group(0))), t)
    t = re.sub(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])", r"**\1**", t)             # constrained bold
    t = re.sub(r"(?<![\w+])\+([^+\n]+?)\+(?![\w+])", r"\1", t)                  # passthrough
    return t


def _adoc_cols(attr: str) -> int | None:
    m = re.search(r'cols\s*=\s*"([^"]*)"', attr) or re.search(r"cols\s*=\s*'([^']*)'", attr)
    if not m:
        m2 = re.search(r"cols\s*=\s*(\d+)", attr)
        return int(m2.group(1)) if m2 else None
    n = 0
    for part in m.group(1).split(","):
        k = re.match(r"\s*(\d+)\*", part)
        n += int(k.group(1)) if k else 1
    return n


def _adoc_table(body: list[str], attr: str, attrs: dict[str, str]) -> list[str]:
    """Cells of a `|===` table laid out on the grid: a cell spanning n columns is followed by n-1 empty
    cells, a cell spanning rows reserves its column in the rows below."""
    text = "\n".join(body)
    cells: list[tuple[int, int, str]] = []          # (colspan, rowspan, text)
    first_line_cells = 0
    # every unescaped `|` starts a cell; the word right before it (after a space or a line start) is that
    # cell's specifier when it has the form of one (`2+^`, `.2+`, `3*`), else it belongs to the cell before
    seps = []                                       # (start of the specifier, position of `|`, specifier)
    for m in re.finditer(r"(?<!\\)\|", text):
        k = m.start()
        while k > 0 and not text[k - 1].isspace() and text[k - 1] != "|":
            k -= 1
        word = text[k:m.start()]
        is_spec = bool(word) and (k == 0 or text[k - 1].isspace()) and bool(_ADOC_SPEC.match(word))
        seps.append((k if is_spec else m.start(), m.start(), word if is_spec else ""))
    first_line = text.count("\n", 0, seps[0][1]) if seps else 0
    for i, (_, bar, spec) in enumerate(seps):
        end = seps[i + 1][0] if i + 1 < len(seps) else len(text)
        sm = _ADOC_SPEC.match(spec)
        dup = int(sm.group(1) or 1)
        colspan = int(sm.group(2) or 1) if "+" in spec else 1
        rowspan = int(sm.group(3) or 1) if "+" in spec else 1
        cell = _adoc_inline(text[bar + 1:end].strip().replace("\\|", "|"), attrs)
        cells += [(colspan, rowspan, cell)] * dup
        if text.count("\n", 0, bar) == first_line:
            first_line_cells += colspan * dup
    ncols = _adoc_cols(attr) or first_line_cells or 1
    rows: list[list[str]] = []
    row: list[str] = []
    reserved: dict[int, int] = {}                  # column -> rows still taken by a row span from above

    def free(col: int) -> bool:
        return reserved.get(col, 0) == 0

    for colspan, rowspan, cell in cells:
        while True:
            while len(row) < ncols and not free(len(row)):
                row.append("")
            if len(row) < ncols:
                break
            rows.append(row)
            row = []
            reserved = {c: n - 1 for c, n in reserved.items() if n - 1 > 0}
        start = len(row)
        row.append(cell)
        row += [""] * max(0, min(colspan, ncols - start) - 1)
        if rowspan > 1:
            for c in range(start, start + colspan):
                reserved[c] = max(reserved.get(c, 0), rowspan)
        if len(row) >= ncols:
            rows.append(row[:ncols])
            row = []
            reserved = {c: n - 1 for c, n in reserved.items() if n - 1 > 0}
    if any(c for c in row):
        rows.append(row)
    return _table_md(rows)


def adoc_to_markdown(path: Path, _depth: int = 0) -> str:
    path = Path(path)
    raw = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    attrs: dict[str, str] = {}
    lines = raw.split("\n")
    out: list[str] = []
    pending_attr = ""                               # the last [attribute] line, for the next block
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if s.startswith("////"):                    # comment block
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("////"):
                j += 1
            i = j + 1
            continue
        if s.startswith("//"):
            i += 1
            continue
        m = re.match(r"^:([\w\-]+)!?:\s*(.*)$", s)
        if m:                                       # document attribute
            attrs[m.group(1)] = m.group(2)
            i += 1
            continue
        if re.match(r"^(ifdef|ifndef|ifeval|endif)::", s):
            i += 1
            continue
        m = re.match(r"^include::(.+?)\[[^\]]*\]$", s)
        if m:
            inc = (path.parent / _adoc_inline(m.group(1), attrs)).resolve()
            if inc.is_file() and _depth < 5:            # an include inserts AsciiDoc text, whatever its name
                out += ["", adoc_to_markdown(inc, _depth + 1).strip(), ""]
            else:
                out += ["", f"(included file not available: {m.group(1)})", ""]
            i += 1
            continue
        if re.match(r"^\[\[[^\]]*\]\]$", s) or re.match(r"^image::", s) or s == "<<<":
            i += 1
            continue
        if re.match(r"^\[.*\]$", s):
            pending_attr = s
            i += 1
            continue
        m = re.match(r"^(={1,6})\s+(\S.*)$", s)
        if m:
            out += ["", "#" * len(m.group(1)) + " " + _adoc_inline(m.group(2), attrs), ""]
            pending_attr = ""
            i += 1
            continue
        if re.match(r"^\.[^.\s]", s):                # block title (a table caption, for example)
            out += ["", "**" + _adoc_inline(s[1:], attrs) + "**", ""]
            i += 1
            continue
        if s in ("----", "....", "++++", "```") or re.match(r"^(-{4,}|\.{4,}|\+{4,})$", s):
            j = i + 1
            while j < len(lines) and lines[j].strip() != s:
                j += 1
            lang = ""
            mm = re.match(r"^\[(source|wavedrom|listing|literal)\s*,?\s*([\w+\-]*)", pending_attr)
            if mm:
                lang = mm.group(2) if mm.group(1) == "source" else (mm.group(1) if mm.group(1) == "wavedrom" else "")
            out += ["", "```" + lang] + lines[i + 1:j] + ["```", ""]
            pending_attr = ""
            i = j + 1
            continue
        if s in ("====", "****", "____", "--") or re.match(r"^(={4,}|\*{4,}|_{4,})$", s):
            kind = re.match(r"^\[(\w+)", pending_attr)
            if kind and kind.group(1).upper() in _ADOC_ADMONITION:
                out += ["", f"**{kind.group(1).capitalize()}:**"]
            pending_attr = ""
            i += 1                                  # the delimiters go; the content is read as usual
            continue
        if s.startswith("|===") or s.startswith(",===") or s.startswith("!==="):
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith(s[:4]):
                j += 1
            out += [""] + _adoc_table(lines[i + 1:j], pending_attr, attrs) + [""]
            pending_attr = ""
            i = j + 1
            continue
        m = re.match(r"^(NOTE|TIP|IMPORTANT|WARNING|CAUTION):\s+(.*)$", s)
        if m:
            out.append(f"**{m.group(1).capitalize()}:** " + _adoc_inline(m.group(2), attrs))
            i += 1
            continue
        m = re.match(r"^(\*{1,5}|-)\s+(.*)$", s)
        if m:
            depth = len(m.group(1)) - 1 if m.group(1) != "-" else 0
            out.append("  " * depth + "- " + _adoc_inline(m.group(2), attrs))
            i += 1
            continue
        m = re.match(r"^(\.{1,5})\s+(.*)$", s)
        if m:
            out.append("  " * (len(m.group(1)) - 1) + "1. " + _adoc_inline(m.group(2), attrs))
            i += 1
            continue
        m = re.match(r"^(.+?)::\s*(.*)$", s)
        if m and not s.startswith(("http", "include", "image")):
            out.append(f"- **{_adoc_inline(m.group(1), attrs)}**: {_adoc_inline(m.group(2), attrs)}")
            i += 1
            continue
        if s == "+":
            i += 1
            continue
        if s == "":
            out.append("")
            i += 1
            continue
        # a paragraph: its lines up to a blank line or a block start, joined (role spans may cross lines)
        j = i
        para: list[str] = []
        while j < len(lines):
            t = lines[j].strip()
            if t == "" or (j > i and (re.match(r"^(\[.*\]|={1,6}\s|\|===|----|\.\.\.\.|====|\*{1,5}\s|//|include::)", t)
                                      or re.match(r"^\.[^.\s]", t))):
                break
            para.append(t)
            j += 1
        out.append(re.sub(r"[ \t]{2,}", " ", _adoc_inline(" ".join(para), attrs)).strip())
        pending_attr = ""
        i = j
    return _tidy(out)


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
    if s in (".adoc", ".asciidoc"):
        return adoc_to_markdown(Path(path))
    raise ValueError(f"no converter for {s}")

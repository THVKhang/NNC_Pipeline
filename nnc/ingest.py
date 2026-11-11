"""Ingest a specification into a section tree of sentences with stable IDs (no LLM, no tokens).

    PDF/Markdown/text  ->  pages  ->  boilerplate removed  ->  numbered section tree  ->  sentences

The output (spec index) is the only form of the document that agents ever see. Every sentence has an
ID such as `3.1.1:s2`; an extractor cites IDs instead of retyping text, so a quote can never be
invented and output tokens stay small (docs/ARCHITECTURE.md, section 4).

Heuristics, all generic (not tied to one document):
* header/footer: a line (digits normalised) found in the first or last lines of many pages, or a
  line that is the first line of two or more pages (running chapter title);
* table of contents: pages where many lines end in dot leaders are skipped;
* headings: `Chapter N Title`, `Appendix X Title`, `N.N[.N[.N]] Title` (number and title may be on
  separate lines) are accepted only when the number is the next one in document order, which
  rejects TOC entries, cross references and numbers inside tables;
* sentences: split at sentence ends and at bullets, keeping common abbreviations intact;
* normative: a sentence holding a keyword such as must, shall, only, permitted, recommended is a
  candidate rule; every candidate must later be cited by a rule or skipped with a reason.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

INDEX_VERSION = 1

NORMATIVE_RE = re.compile(
    r"\b(must|shall|required|requires|cannot|can only|only when|only if|only in|not permitted|"
    r"is permitted|are permitted|permitted to|prohibited|recommended|recommends|should|must not|"
    r"never|always|illegal|legal|not allowed|is allowed|are allowed|mandatory|optional|"
    # permissions and present-tense behaviour ("can appear before", "remains stable until"): they
    # define legal stimulus and stability checks, so they must get a decision too
    r"can|possible|remain|remains|stable)\b",
    re.IGNORECASE,
)
# Upper-case signal names (AWVALID, ARESETn); not parts of hyphenated IDs such as REQ-FUNC-001.
SIGNAL_RE = re.compile(r"(?<![\w-])[A-Z][A-Z0-9_]{2,}n?(?![\w-])(?:\[\d+:\d+\])?")
SIGNAL_STOP = {"AXI", "AXI3", "AXI4", "AMBA", "ARM", "HIGH", "LOW", "NOTE", "TABLE", "FIGURE", "IHI", "ID", "THE",
               "AND", "FOR", "NOT", "ALL", "ANY", "LICENCE", "LICENSEE", "APB", "AHB"}
BULLETS = "\u2022\u25cf\u25aa\u2023\u2043\ufffd"     # U+FFFD: bullets lost by some PDF fonts
_BULLET_SPLIT = re.compile(rf"\s*[{BULLETS}]\s+")
_ABBREV = ("e.g.", "i.e.", "etc.", "Fig.", "No.", "approx.", "vs.", "cf.")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\"'])")
_DOT_LEADER = re.compile(r"\.{5,}|(?:\. ){4,}")
_CHAPTER = re.compile(r"^(Chapter)\s+(\d+)\s+(\S.{0,70})$")
_APPENDIX = re.compile(r"^(Appendix)\s+([A-Z])\s+(\S.{0,70})$")
_NUMBERED = re.compile(r"^(\d+(?:\.\d+){1,3})(?:\s+(\S.*))?$")
MAX_TITLE = 90
_CONNECTORS = {"of", "and", "or", "for", "to", "the", "a", "an", "in", "on", "with", "by", "from"}
MAX_HEADING_GAP = 1   # headings that may be missed between two accepted ones (each gap is a warning)


class IngestError(Exception):
    pass


@dataclass
class Sentence:
    id: str
    text: str
    page: int
    normative: bool


@dataclass
class Section:
    id: str            # "front", "3", "3.1", "3.1.1", "A"
    title: str
    level: int         # 0 front matter, 1 chapter/appendix, 2.. numbered sections
    parent: str | None
    page_start: int
    page_end: int
    sentences: list[Sentence] = field(default_factory=list)


# --------------------------------------------------------------------------------------------- pages
def find_pdftotext() -> str | None:
    found = shutil.which("pdftotext")
    if found:
        return found
    for cand in (r"C:\Program Files\Git\mingw64\bin\pdftotext.exe", r"C:\Program Files\Git\usr\bin\pdftotext.exe"):
        if Path(cand).is_file():
            return cand
    return None


def read_pages(path: Path) -> list[str]:
    """Pages of a PDF (via poppler pdftotext) or of a text/Markdown file (one page per form feed)."""
    path = Path(path)
    if path.suffix.lower() != ".pdf":
        return path.read_text(encoding="utf-8").split("\f")
    exe = find_pdftotext()
    if not exe:
        raise IngestError("pdftotext not found; install poppler-utils (Linux) or Git for Windows")
    # Run in the file's folder with a relative name: the mingw build cannot open non-ASCII paths.
    proc = subprocess.run([exe, "-enc", "UTF-8", path.name, "-"], cwd=path.parent, capture_output=True,
                          timeout=300)
    if proc.returncode != 0:
        raise IngestError(f"pdftotext failed: {proc.stderr.decode('utf-8', 'replace')[:500]}")
    pages = proc.stdout.decode("utf-8", "replace").split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return pages


# ------------------------------------------------------------------------------------- boilerplate
def _norm(line: str) -> str:
    return re.sub(r"\d+", "#", line.strip())


def boilerplate_lines(pages: list[list[str]]) -> set[str]:
    """Normalised lines that are page furniture (headers, footers, page labels)."""
    edge: Counter[str] = Counter()
    first: Counter[str] = Counter()
    for lines in pages:
        nonempty = [_norm(l) for l in lines if l.strip()]
        if not nonempty:
            continue
        first[nonempty[0]] += 1
        for l in set(nonempty[:3] + nonempty[-6:]):
            edge[l] += 1
    min_edge = max(3, len(pages) // 10)
    out = {l for l, n in edge.items() if n >= min_edge and len(l) <= 100}
    out |= {l for l, n in first.items() if n >= 2 and len(l) <= 60}
    # A bare or titled section number ("#.#", "#.# Title") is a heading, never page furniture.
    return {l for l in out if not _NUMBERED.match(l.replace("#", "1"))}


def is_toc_page(lines: list[str]) -> bool:
    nonempty = [l for l in lines if l.strip()]
    return bool(nonempty) and sum(bool(_DOT_LEADER.search(l)) for l in nonempty) >= max(3, len(nonempty) // 4)


# ---------------------------------------------------------------------------------------- headings
def _key(num: str) -> tuple:
    return tuple(int(x) if x.isdigit() else x for x in num.split("."))


def _successor_gap(prev: tuple, cand: tuple) -> int | None:
    """Number of headings skipped if cand follows prev (0 = the exact next heading), else None.

    cand may be a first child of prev (x.1, or x.2 with one missed), or the next sibling at the level
    of prev or of one of its ancestors.
    """
    if len(cand) == len(prev) + 1 and cand[:-1] == prev and isinstance(cand[-1], int) \
            and 1 <= cand[-1] <= 1 + MAX_HEADING_GAP:
        return cand[-1] - 1
    for k in range(1, len(prev) + 1):
        if len(cand) == k and cand[:k - 1] == prev[:k - 1] and isinstance(cand[k - 1], int) \
                and isinstance(prev[k - 1], int) and 1 <= cand[k - 1] - prev[k - 1] <= 1 + MAX_HEADING_GAP:
            return cand[k - 1] - prev[k - 1] - 1
    return None


def split_glued_title(text: str) -> tuple[str, str]:
    """Split 'System considerations AXI4 defines ...' into title and body.

    Used only when the text after a section number is too long to be a title: the title ends before
    the first word (after the second) that starts with a capital letter or digit, and is at most
    eight words. Imperfect by nature, so the caller records a warning.
    """
    words = text.split()
    cut = min(len(words), 8)
    for k in range(2, min(len(words), 8)):
        if words[k - 1].lower() in _CONNECTORS:   # "Removal of WID": WID belongs to the title
            continue
        if words[k][0].isupper() or words[k][0].isdigit():
            cut = k
            break
    return " ".join(words[:cut]), " ".join(words[cut:])


def _next_chapter(chapter: tuple | None, kind: str, num: str) -> bool:
    """Chapters run 1, 2, 3...; appendices A, B... follow the chapters (or stand alone)."""
    in_appendix = chapter is not None and isinstance(chapter[0], str)
    if kind == "Chapter":
        return not in_appendix and int(num) == (chapter[0] + 1 if chapter else 1)
    return ord(num) == ord(chapter[0]) + 1 if in_appendix else num == "A"


def _good_title(title: str) -> bool:
    return (bool(title) and len(title) <= MAX_TITLE and title[0].isalpha()
            and not title.endswith((".", ",", ";", ":")) and not _DOT_LEADER.search(title) and " = " not in title)


# --------------------------------------------------------------------------------------- sentences
def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    protected = text
    for i, ab in enumerate(_ABBREV):
        protected = protected.replace(ab, f"\x00{i}\x00")
    out: list[str] = []
    for chunk in _BULLET_SPLIT.split(protected):
        for s in _SENT_SPLIT.split(chunk):
            s = s.strip()
            if s:
                out.append(re.sub(r"\x00(\d+)\x00", lambda m: _ABBREV[int(m.group(1))], s))
    return out


# ------------------------------------------------------------------------------------- paged build
def _build_paged(path: Path) -> tuple[list[Section], list[str], int]:
    """PDF or plain text: numbered headings found in page text (see the module docstring)."""
    raw_pages = read_pages(path)
    pages = [p.splitlines() for p in raw_pages]
    furniture = boilerplate_lines(pages)

    sections: list[Section] = [Section("front", "Front matter", 0, None, 1, 1)]
    by_id = {"front": sections[0]}
    buffers: dict[str, list[tuple[int, str]]] = {"front": []}
    warnings: list[str] = []
    current = sections[0]
    chapter: tuple | None = None   # key of the current chapter, e.g. (3,) or ("A",)
    last: tuple | None = None      # key of the last accepted heading

    def open_section(sid: str, title: str, level: int, parent: str | None, page: int) -> None:
        nonlocal current
        if sid in by_id:
            warnings.append(f"duplicate heading {sid} on page {page} ignored")
            return
        sec = Section(sid, title.strip(), level, parent, page, page)
        sections.append(sec)
        by_id[sid] = sec
        buffers[sid] = []
        current = sec

    for pno, lines in enumerate(pages, start=1):
        if is_toc_page(lines):
            continue
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            if not line or _norm(line) in furniture:
                continue
            m = _CHAPTER.match(line) or _APPENDIX.match(line)
            if m:
                kind, num, title = m.groups()
                key = (int(num),) if kind == "Chapter" else (num,)
                if _next_chapter(chapter, kind, num) and _good_title(title):
                    open_section(num, title, 1, None, pno)
                    chapter, last = key, key
                    continue
            m = _NUMBERED.match(line)
            if m and chapter is not None:
                num, title = m.group(1), (m.group(2) or "").strip()
                j = i
                if not title:  # number alone: the title is the next non-empty line
                    while j < len(lines) and not lines[j].strip():
                        j += 1
                    title = lines[j].strip() if j < len(lines) else ""
                    j += 1
                key = _key(num)
                gap = _successor_gap(last, key) if key[0] == chapter[0] and last is not None else None
                body = ""
                if gap is not None and m.group(2) and not _good_title(title) and title[:1].isalpha():
                    title, body = split_glued_title(title)
                    warnings.append(f"heading {num} on page {pno}: title glued to text, split as '{title}'")
                if gap is not None and _good_title(title):
                    if gap:
                        warnings.append(f"heading {num} on page {pno}: {gap} heading(s) before it not found")
                    parent = ".".join(num.split(".")[:-1])
                    if parent not in by_id:
                        warnings.append(f"heading {num} on page {pno} has no parent {parent}")
                        parent = ".".join(str(x) for x in chapter)
                    open_section(num, title, len(key), parent, pno)
                    last = key
                    if not m.group(2):
                        i = j
                    if body:
                        buffers[current.id].append((pno, body))
                    continue
            buffers[current.id].append((pno, line))
            current.page_end = pno

    # Sentences: joined per section; each sentence gets the page where its text starts.
    for sec in sections:
        text_parts: list[str] = []
        page_marks: list[tuple[int, int]] = []  # (char offset, page)
        offset = 0
        for pno, line in buffers[sec.id]:
            page_marks.append((offset, pno))
            text_parts.append(line)
            offset += len(line) + 1
        text = " ".join(text_parts)
        pos = 0
        for n, s in enumerate(split_sentences(text), start=1):
            probe = re.sub(r"\s+", " ", s)[:30]
            found = re.sub(r"\s+", " ", text).find(probe, pos)
            pos = found if found >= 0 else pos
            page = next((p for off, p in reversed(page_marks) if off <= pos), sec.page_start)
            sec.sentences.append(Sentence(f"{sec.id}:s{n}", s, page, bool(NORMATIVE_RE.search(s))))

    return sections, warnings, len(raw_pages)


# ---------------------------------------------------------------------------------------- markdown
_MD_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_MD_NUMBER = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(\S.*)$")
_MD_LIST = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
_MD_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")


def md_inline(text: str) -> str:
    """Plain text of a Markdown fragment: images and HTML removed, links reduced to their text."""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    return re.sub(r"\s+", " ", text).strip()


def _table_cells(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [md_inline(c) for c in re.split(r"(?<!\\)\|", line)]


def _build_markdown(path: Path) -> tuple[list[Section], list[str], int, list[dict]]:
    """Sections from Markdown headings; paragraphs and list items become sentences; every table row
    becomes one sentence 'Header: value; Header: value' so that it stands alone. Locations are line
    numbers. Numbered headings ('### 10.3 Title') keep their number as ID; others get 'T' + path."""
    lines = path.read_text(encoding="utf-8").splitlines()
    sections: list[Section] = [Section("front", "Front matter", 0, None, 1, 1)]
    warnings: list[str] = []
    tables: list[dict] = []
    stack: list[Section] = []            # open headings by level
    counters: dict[int, int] = {}
    units: dict[str, list[tuple[int, str, str]]] = {"front": []}  # section -> (line, kind, text)
    used: set[str] = {"front"}
    min_level = min((len(m.group(1)) for l in lines if (m := _MD_HEADING.match(l))), default=1)

    i = 0
    if lines and lines[0].strip() == "---":                  # YAML front matter
        end = next((k for k in range(1, len(lines)) if lines[k].strip() == "---"), 0)
        i = end + 1
    in_code = in_comment = False
    para: list[str] = []
    para_line = 0

    def current() -> Section:
        return stack[-1] if stack else sections[0]

    def flush() -> None:
        nonlocal para
        if para:
            units[current().id].append((para_line, "text", md_inline(" ".join(para))))
            para = []

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        lno = i + 1
        i += 1
        if in_comment:
            in_comment = "-->" not in line
            continue
        if line.startswith("<!--"):
            in_comment = "-->" not in line
            continue
        if line.startswith("```") or line.startswith("~~~"):
            flush()
            in_code = not in_code
            continue
        if in_code:
            continue
        m = _MD_HEADING.match(line)
        if m:
            flush()
            level = len(m.group(1)) - min_level + 1
            text = md_inline(m.group(2))
            num = _MD_NUMBER.match(text)
            while stack and stack[-1].level >= level:
                stack.pop()
            counters[level] = counters.get(level, 0) + 1
            for deeper in [k for k in counters if k > level]:
                del counters[deeper]
            if num:
                sid, title = num.group(1), num.group(2)
            else:
                sid, title = "T" + ".".join(str(counters.get(k, 1)) for k in range(1, level + 1)), text
            base, n = sid, 2
            while sid in used:
                sid = f"{base}_{n}"
                n += 1
            used.add(sid)
            sec = Section(sid, title, level, stack[-1].id if stack else None, lno, lno)
            sections.append(sec)
            units[sid] = []
            stack.append(sec)
            continue
        if line.startswith("|") and i < len(lines) and _MD_TABLE_SEP.match(lines[i]):
            flush()
            header = _table_cells(line)
            i += 1
            rows: list[list[str]] = []
            row_lines: list[int] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_table_cells(lines[i]))
                row_lines.append(i + 1)
                i += 1
            sec = current()
            tables.append({"section": sec.id, "header": header, "rows": rows, "line": lno, "units": []})
            # Caption: the text line just above the table (blank lines skipped), e.g.
            # "**`m_top`**: write side (CLK-WR)". A heading or another table is not a caption.
            k = lno - 2
            while k >= 0 and not lines[k].strip():
                k -= 1
            above = lines[k].strip() if k >= 0 else ""
            if above and not above.startswith(("|", "#")):
                tables[-1]["caption"] = md_inline(above)
            for rl, row in zip(row_lines, rows):
                cells = [f"{h}: {v}" for h, v in zip(header, row) if v and h]
                if cells:
                    units[sec.id].append((rl, f"row:{len(tables) - 1}", "; ".join(cells)))
            continue
        if not line:
            flush()
            continue
        if line.startswith(">"):
            line = line.lstrip("> ").strip()
            if not line:
                flush()
                continue
        lm = _MD_LIST.match(raw)
        if lm:
            flush()
            para, para_line = [lm.group(1)], lno
            continue
        if not para:
            para_line = lno
        para.append(line)
    flush()

    for sec in sections:
        n = 0
        for lno, kind, text in units[sec.id]:
            pieces = [text] if kind.startswith("row:") else split_sentences(text)
            for piece in pieces:
                n += 1
                st = Sentence(f"{sec.id}:s{n}", piece, lno, bool(NORMATIVE_RE.search(piece)))
                sec.sentences.append(st)
                if kind.startswith("row:"):
                    tables[int(kind[4:])]["units"].append(st.id)
            sec.page_end = max(sec.page_end, lno)
    return sections, warnings, len(lines), tables


# ------------------------------------------------------------------------------------------ common
PORT_RE = re.compile(r"\b(?:[io]|io)_[a-z][a-z0-9_]*\b")
PARAM_RE = re.compile(r"\bPARA_[A-Z0-9_]+\b")


def build_index(path: Path) -> dict:
    path = Path(path)
    if path.suffix.lower() in (".md", ".markdown"):
        sections, warnings, length, tables = _build_markdown(path)
        loc = "line"
    else:
        sections, warnings, length = _build_paged(path)
        tables, loc = [], "page"

    signals: Counter[str] = Counter()
    for sec in sections:
        if sec.level == 0:
            continue
        for st in sec.sentences:
            toks = {t.split("[")[0] for t in SIGNAL_RE.findall(st.text)} | set(PORT_RE.findall(st.text)) \
                | set(PARAM_RE.findall(st.text))
            for tok in toks:
                if tok not in SIGNAL_STOP:
                    signals[tok] += 1

    return {
        "version": INDEX_VERSION,
        "doc": {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "length": length, "location": loc},
        "sections": [asdict(s) for s in sections],
        "tables": tables,
        "signals": dict(sorted((k, v) for k, v in signals.items() if v >= 2)),
        "warnings": warnings,
        "stats": {
            "sections": len(sections) - 1,
            "sentences": sum(len(s.sentences) for s in sections if s.level > 0),
            "normative": sum(st.normative for s in sections if s.level > 0 for st in s.sentences),
            "chars": sum(len(st.text) for s in sections if s.level > 0 for st in s.sentences),
        },
    }


def save_index(index: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

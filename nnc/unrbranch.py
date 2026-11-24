"""Formal proof that uncovered branches cannot be reached (ROADMAP 23.3, code only, no LLM).

A block point of Verilator's line coverage (the `if`, `elsif` or `else` branch of an IF, a `case` item) that
no run executed may be dead code: the `default` of a case over every state, a branch under a parameter. This
module proves such branches with the machinery of nnc/unr.py, on an instrumented copy of the RTL:

1. targets: the block points of the merged coverage.dat with no hit, keyed by instance, file, line, column
   and kind. Verilator writes an `if` or `elsif` point (the then branch; `elsif` when the else is another IF)
   at the column of the `if` token, the `else` point of the same IF one column further, a case item's point at
   its `:` (or its `default`).
2. `verilator --json-only -fno-const -fno-const-before-dfg` of the configuration (without constant folding,
   which would drop a dead branch or turn an IF into a ?:) gives, for each target, the IF or case item at that
   position and the always block around it. A target is tried only inside an always block at module level:
   clocked (every event an edge), or combinational (`always_comb`, `always @*`) with a begin...end body.
3. A copy of the RTL gets one 1-bit marker per branch, written on the lines of the branch so that no line
   number moves:
   - in a clocked block, `m <= ~m;` as the first statement of the branch: the flop toggles each time the
     branch runs, so the branch never runs after the first reset exactly when the flop keeps its value
     (the toggle property of unr.py). In a block with an asynchronous reset (an edge on another signal than
     the clock), the flop needs a constant reset value: `m <= 1'b0;` goes first in the reset branch, the
     then branch of the one IF of the block whose condition reads only signals of the event list (a block
     without such an IF is not tried);
   - in a combinational block, `m = 1'b0;` first in the block and `m = 1'b1;` in the branch: the branch
     never runs after the first reset exactly when the marker stays 0 (unr.py's `zero` assertion).
   A single statement is wrapped in begin...end; an `else` that the code leaves out is written. A branch
   whose single statement is itself compound (an IF, a case, a loop) is not tried.
4. Self-check: `verilator --json-only` of the copy must show every marker as the first statement of the
   same branch, and the same IF and case items on the same lines as the original. A marker that fails is
   left out (its branch stays counted).
5. unr.prove_config proves the markers, with the guard and control assertions of toggle points.

A PROVEN branch (in every configuration of the run set) leaves the block coverage, and so do its lines unless
another point that is kept covers them. A counterexample, no result, or a branch that is not tried stays
counted. The markers are registers that nothing reads; they change nothing else in the design. Like the
toggle proofs, a proof is about the design after the first reset, with every input free.
"""
from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from nnc import coverage as cov

KINDS = cov.BRANCH_KINDS
PREFIX = "nnc_br"
_LOC = re.compile(r"^(\w+),(\d+):(\d+),(\d+):(\d+)$")
_IDENT = re.compile(rb"[A-Za-z_][A-Za-z0-9_$]*")
# a single statement that starts with one of these is compound or a timing control: not wrapped
_COMPOUND = {"if", "else", "case", "casez", "casex", "for", "foreach", "while", "do", "repeat", "forever",
             "fork", "unique", "unique0", "priority", "begin", "end", "randcase", "wait", "assert", "assume",
             "cover", "disable"}


def _loc(n) -> tuple[str, int, int, int, int] | None:
    m = _LOC.match((n.get("loc") or "") if isinstance(n, dict) else "")
    return (m[1], int(m[2]), int(m[3]), int(m[4]), int(m[5])) if m else None


Key = tuple  # (instance relative to the DUT top, file, line, column, kind)


# ------------------------------------------------------------------------------------ targets
point_key = cov.block_key


def targets(dat_path: Path, rtl_names: list[str]) -> dict[Key, list[int]]:
    """{(instance, file, line, column, kind): lines of the block} of the DUT's IF branches and case items that
    no run executed ("" is the DUT top; Verilator's merged instance names keep their *)."""
    hits: dict[Key, int] = defaultdict(int)
    spans: dict[Key, set[int]] = defaultdict(set)
    if not dat_path.is_file():
        return {}
    for kv, name, metric, line, span, count in cov._records(dat_path, set(rtl_names)):
        key = point_key(kv, name, line) if metric == "block" else None
        if key is None:
            continue
        hits[key] += count
        spans[key].update(span)
    return {k: sorted(spans[k]) for k, n in sorted(hits.items()) if n == 0}


# ------------------------------------------------------------------------------------- sites
@dataclass
class Site:
    """One branch of the RTL text: the IF or case item on (file, line), the branch (then/else/item) and its
    always block."""
    file: str
    line: int
    col: int
    kind: str               # if, elsif, else, case
    clocked: bool
    always: tuple           # loc of the ALWAYS node
    node: dict              # the IF or CASEITEM
    block: dict | None      # the BEGIN body of a combinational always
    tag: int = 0            # index of the file (marker names are unique over the design)
    reset: dict | None = None   # the reset IF of a clocked always with an asynchronous reset

    @property
    def marker(self) -> str:
        part = {"if": "t", "elsif": "t", "else": "e", "case": "c"}[self.kind]
        return f"{PREFIX}{self.tag}_{self.line}_{self.col}_{part}"

    @property
    def body(self) -> list:
        key = {"if": "thensp", "elsif": "thensp", "else": "elsesp", "case": "stmtsp"}[self.kind]
        return self.node.get(key) or []


def _always_kind(a: dict) -> str | None:
    """"clocked" (every event an edge), "comb" (always_comb, always @*), or None (anything else)."""
    kw = a.get("keyword")
    items = [s for t in a.get("sentreep") or [] if isinstance(t, dict) for s in (t.get("sensesp") or [])]
    edges = {s.get("edgeType") for s in items}
    if kw == "always_comb" and not items:
        return "comb"
    if kw in ("always", "always_ff") and items and edges <= {"POS", "NEG"}:
        return "clocked"
    if kw == "always" and items and edges <= {"COMBO"}:
        return "comb"
    return None


def _names(n, out: set) -> set:
    if isinstance(n, list):
        for x in n:
            _names(x, out)
    elif isinstance(n, dict):
        if n.get("type") == "VARREF":
            out.add(n.get("name"))
        for k, v in n.items():
            if isinstance(v, (dict, list)) and k != "dtypep":
                _names(v, out)
    return out


def reset_if(a: dict) -> tuple[bool, dict | None]:
    """(asynchronous, its reset IF) of a clocked always: asynchronous when the event list has more than one
    edge; the reset IF is the one statement of the block, an IF whose condition reads only signals of the
    event list."""
    items = [s for t in a.get("sentreep") or [] if isinstance(t, dict) for s in (t.get("sensesp") or [])]
    if len(items) < 2:
        return False, None
    sens = _names([s.get("sensp") for s in items], set())
    body = [x for x in a.get("stmtsp") or [] if isinstance(x, dict)]
    if len(body) == 1 and body[0].get("type") == "BEGIN":
        body = [x for x in body[0].get("stmtsp") or [] if isinstance(x, dict)]
    if len(body) != 1 or body[0].get("type") != "IF":
        return True, None
    cond = _names(body[0].get("condp"), set())
    return True, (body[0] if cond and cond <= sens else None)


def _files(meta: dict) -> dict[str, str]:
    return {fid: Path(f.get("filename", "")).name for fid, f in (meta.get("files") or {}).items()}


def _walk(n, out: list, stop=("FUNC", "TASK", "ALWAYS", "MODULE")):
    """IF and CASEITEM nodes under n (not into functions, tasks or other blocks)."""
    if isinstance(n, list):
        for x in n:
            _walk(x, out, stop)
        return
    if not isinstance(n, dict):
        return
    if n.get("type") in ("IF", "CASEITEM"):
        out.append(n)
    for k, v in n.items():
        if isinstance(v, (dict, list)) and k not in ("dtypep", "sentreep") and not (
                isinstance(v, dict) and v.get("type") in stop):
            if isinstance(v, list):
                _walk([x for x in v if not (isinstance(x, dict) and x.get("type") in stop)], out, stop)
            else:
                _walk(v, out, stop)


def node_col(kind: str, col: int) -> int:
    """Column of the IF or case item token of a coverage point at column `col` (0: unknown)."""
    return col - 1 if kind == "else" and col else col


def locate(tree: dict, meta: dict, wanted: set[tuple[str, int, int, str]],
           file_tags: dict[str, int] | None = None, shift=None) -> tuple[dict[tuple, Site], dict[tuple, str]]:
    """For every wanted (file, line, column, kind): its Site, or why it is not tried. `shift(file, line,
    column)`: the column in this tree of an original column (an instrumented copy)."""
    files = _files(meta)
    nodes: dict[tuple, dict[tuple, tuple]] = defaultdict(dict)       # (file, line, IF|CASEITEM) -> {loc: (node, always, kind)}
    lines_by_file: dict[str, list[int]] = defaultdict(list)
    for mod in tree.get("modulesp") or []:
        if not isinstance(mod, dict) or mod.get("type") != "MODULE":
            continue
        items = [s for s in mod.get("stmtsp") or [] if isinstance(s, dict)]
        for s in items:
            loc = _loc(s)
            if loc:
                lines_by_file[files.get(loc[0], "")].append(loc[1])
        for a in items:
            if a.get("type") != "ALWAYS":
                continue
            kind, aloc = _always_kind(a), _loc(a)
            if kind is None or aloc is None:
                continue
            found: list = []
            _walk(a.get("stmtsp") or [], found)
            for n in found:
                loc = _loc(n)
                if loc is None or loc[0] != aloc[0]:
                    continue
                nodes[(files.get(loc[0], ""), loc[1], n["type"])].setdefault(loc[1:], (n, a, kind))
    for f in lines_by_file:
        lines_by_file[f] = sorted(set(lines_by_file[f]))
    sites: dict[tuple, Site] = {}
    why: dict[tuple, str] = {}
    for want in sorted(wanted):
        f, line, col, kind = want
        typ = "CASEITEM" if kind == "case" else "IF"
        cands = nodes.get((f, line, typ)) or {}
        if col:
            c = node_col(kind, col)
            c = shift(f, line, c) if shift else c
            cands = {loc: v for loc, v in cands.items() if loc[1] == c}
        if not cands:
            why[want] = "not in an always block at module level"
            continue
        if len(cands) > 1:
            why[want] = "several on one line"
            continue
        n, a, akind = next(iter(cands.values()))
        aloc = _loc(a)
        nxt = [x for x in lines_by_file.get(f, []) if x > aloc[1]]
        if nxt and line >= nxt[0]:
            why[want] = "outside the text of its always block"
            continue
        block, rst = None, None
        if akind == "clocked":
            asyn, rst = reset_if(a)
            if asyn and rst is None:
                why[want] = "asynchronous reset without a reset IF"
                continue
            if rst is not None and rst is n and kind in ("if", "elsif"):
                why[want] = "the reset branch"
                continue
        if akind == "comb":
            body = [x for x in a.get("stmtsp") or [] if isinstance(x, dict)]
            if len(body) != 1 or body[0].get("type") != "BEGIN":
                why[want] = "combinational block without begin...end"
                continue
            block = body[0]
        sites[want] = Site(f, line, col, kind, akind == "clocked", aloc, n, block, (file_tags or {}).get(f, 0), rst)
    return sites, why


# ------------------------------------------------------------------------------- the RTL text
class _Src:
    """The bytes of one file, with Verilator's (line, column) positions (1-based, column in bytes)."""

    def __init__(self, data: bytes):
        self.b = data
        self.starts = [0] + [i + 1 for i, c in enumerate(data) if c == 10]

    def off(self, line: int, col: int) -> int:
        return self.starts[line - 1] + col - 1

    def skip(self, i: int) -> int:
        b = self.b
        while i < len(b):
            if b[i] in b" \t\r\n\f\v":
                i += 1
            elif b.startswith(b"//", i):
                j = b.find(b"\n", i)
                i = len(b) if j < 0 else j + 1
            elif b.startswith(b"/*", i):
                j = b.find(b"*/", i + 2)
                i = len(b) if j < 0 else j + 2
            else:
                break
        return i

    def ident(self, i: int) -> str | None:
        m = _IDENT.match(self.b, i)
        return m.group().decode() if m else None

    def _string(self, i: int) -> int:
        j = i + 1
        while j < len(self.b) and self.b[j:j + 1] != b'"':
            j += 2 if self.b[j:j + 1] == b"\\" else 1
        return j + 1

    def _escaped(self, i: int) -> int:
        while i < len(self.b) and self.b[i] not in b" \t\r\n":
            i += 1
        return i

    def scan(self, i: int, stop: bytes) -> int | None:
        """Position after the first `stop` (";" or ":") at bracket depth 0 from i; None when a bracket closes
        first. "::" is not a ":"."""
        b, depth = self.b, 0
        while i < len(b):
            if b.startswith(b"//", i) or b.startswith(b"/*", i):
                i = self.skip(i)
                continue
            c = b[i:i + 1]
            if c == b'"':
                i = self._string(i)
                continue
            if c == b"\\":
                i = self._escaped(i)
                continue
            if c in b"([{":
                depth += 1
            elif c in b")]}":
                depth -= 1
                if depth < 0:
                    return None
            elif depth == 0 and c == stop:
                if stop == b":" and b[i + 1:i + 2] == b":":
                    i += 2
                    continue
                return i + 1
            i += 1
        return None

    def paren_end(self, i: int) -> int | None:
        """Position after the parenthesised condition that follows i."""
        j = self.skip(i)
        if self.b[j:j + 1] != b"(":
            return None
        depth, k = 1, j + 1
        while k < len(self.b) and depth:
            if self.b.startswith(b"//", k) or self.b.startswith(b"/*", k):
                k = self.skip(k)
                continue
            c = self.b[k:k + 1]
            if c == b'"':
                k = self._string(k)
                continue
            if c == b"\\":
                k = self._escaped(k)
                continue
            depth += c in b"([{"
            depth -= c in b")]}"
            k += 1
        return k if depth == 0 else None

    def after_label(self, i: int) -> int:
        """After a `begin` or `end` that ends at i: past an optional `: label`."""
        j = self.skip(i)
        if self.b[j:j + 1] == b":" and self.b[j + 1:j + 2] != b":":
            k = self.skip(j + 1)
            name = self.ident(k)
            if name:
                return k + len(name)
        return i

    def block_end(self, i: int) -> int | None:
        """Position after the `end` (and its label) that closes the `begin` at i."""
        b, depth = self.b, 0
        while i < len(b):
            if b.startswith(b"//", i) or b.startswith(b"/*", i):
                i = self.skip(i)
                continue
            c = b[i:i + 1]
            if c == b'"':
                i = self._string(i)
                continue
            if c == b"\\":
                i = self._escaped(i)
                continue
            w = self.ident(i)
            if w:
                if w in ("begin", "fork"):
                    depth += 1
                elif w in ("end", "join", "join_any", "join_none"):
                    depth -= 1
                    if depth == 0:
                        return self.after_label(i + len(w))
                i += len(w)
                continue
            i += 1
        return None

    def stmt_end(self, i: int) -> int | None:
        """Position after the simple statement that starts at i (None for a compound one)."""
        if self.ident(i) in _COMPOUND or self.b[i:i + 1] in (b"#", b"@", b";", b""):
            return None
        return self.scan(i, b";")


def _token_end(src: _Src, node: dict, word: str | None = None) -> int | None:
    """Position after the token that `node`'s location covers (checked against `word`)."""
    loc = _loc(node)
    if loc is None:
        return None
    start = src.off(loc[1], loc[2])
    if word is not None and src.ident(start) != word:
        return None
    return src.off(loc[3], loc[4])


def _cond_end(src: _Src, node: dict) -> int | None:
    """After the condition of an IF (its location is the `if` token, or `unique`/`priority` before it)."""
    i = _token_end(src, node)
    if i is None:
        return None
    j = src.skip(i)
    if src.ident(j) == "if":
        i = j + 2
    return src.paren_end(i)


def _body_end(src: _Src, nodes: list, start: int | None) -> int | None:
    """End of a branch body: a begin...end block, or one simple statement starting at or after `start`."""
    if len(nodes) == 1 and nodes[0].get("type") == "BEGIN":
        loc = _loc(nodes[0])
        return src.block_end(src.off(loc[1], loc[2])) if loc else None
    if len(nodes) == 1 and start is not None:
        return src.stmt_end(src.skip(start))
    return None


def _put(src: _Src, nodes: list, start: int | None, stmt: str) -> list[tuple[int, int, str]] | str:
    """Edits (offset, order, text) that make `stmt` the first statement of a branch body."""
    if len(nodes) == 1 and nodes[0].get("type") == "BEGIN":
        e = _token_end(src, nodes[0], "begin")
        if e is None:
            return "begin not found"
        return [(src.after_label(e), 1, " " + stmt)]
    if not nodes:
        return "empty branch"
    if len(nodes) > 1 or start is None:
        return "branch body not found"
    j = src.skip(start)
    e = src.stmt_end(j)
    if e is None:
        return "single statement that is compound"
    return [(j, 1, "begin " + stmt + " "), (e, 0, " end")]


def edits_for(src: _Src, s: Site) -> list[tuple[int, int, str]] | str:
    """Edits that put the marker of a site in its branch, declare it and, in a combinational block, clear it
    first in the block; or why the site is not instrumented."""
    m = s.marker
    stmt = f"{m} <= ~{m};" if s.clocked else f"{m} = 1'b1;"
    if s.kind in ("if", "elsif"):
        out = _put(src, s.body, _cond_end(src, s.node), stmt)
    elif s.kind == "case":
        i = _token_end(src, s.node)
        if i is None:
            return "case item not found"
        loc = _loc(s.node)
        start = src.off(loc[1], loc[2])
        if src.ident(start) == "default":
            j = src.skip(i)
            colon = j + 1 if src.b[j:j + 1] == b":" else i
        elif src.b[start:start + 1] == b":":
            colon = start + 1
        else:
            colon = src.scan(start, b":")
        out = _put(src, s.body, colon, stmt)
    else:   # else
        then = s.node.get("thensp") or []
        then_end = _body_end(src, then, _cond_end(src, s.node))
        if then_end is None:
            return "end of the then branch not found"
        if not s.body:
            out = [(then_end, 2, f" else begin {stmt} end")]
        else:
            j = src.skip(then_end)
            if src.ident(j) != "else":
                return "else not found"
            out = _put(src, s.body, j + 4, stmt)
    if isinstance(out, str):
        return out
    a_start = src.off(s.always[1], s.always[2])
    if src.ident(a_start) not in ("always", "always_ff", "always_comb"):
        return "always keyword not found"
    out.append((a_start, 3, f"(* keep *) reg {m}; "))
    if s.reset is not None:
        r = _put(src, s.reset.get("thensp") or [], _cond_end(src, s.reset), f"{m} <= 1'b0;")
        if isinstance(r, str):
            return "reset branch: " + r
        out += r
    if not s.clocked:
        e = _token_end(src, s.block, "begin")
        if e is None:
            return "begin of the combinational block not found"
        out.append((src.after_label(e), 0, f" {m} = 1'b0;"))
    return out


def instrument(texts: dict[str, bytes], sites: dict[tuple, Site]) -> tuple[dict[str, bytes], dict[tuple, str]]:
    """The instrumented texts of the files that have sites, and why a site was left out. No edit adds a line."""
    by_file: dict[str, list] = defaultdict(list)
    why: dict[tuple, str] = {}
    for key, s in sorted(sites.items()):
        if s.file not in texts:
            why[key] = "file not found"
            continue
        e = edits_for(_Src(texts[s.file]), s)
        if isinstance(e, str):
            why[key] = e
        else:
            by_file[s.file].extend(e)
    out: dict[str, bytes] = {}
    for f, edits in by_file.items():
        b = texts[f]
        at: dict[int, list] = defaultdict(list)
        for off, order, text in edits:
            at[off].append((order, text))
        for off in sorted(at, reverse=True):
            b = b[:off] + "".join(t for _o, t in sorted(at[off])).encode() + b[off:]
        out[f] = b
    return out, why


# ------------------------------------------------------------------------------- self-check
def _lhs(n: dict) -> str | None:
    lhs = n.get("lhsp") or []
    return lhs[0].get("name") if lhs and isinstance(lhs[0], dict) and lhs[0].get("type") == "VARREF" else None


def _shape(tree: dict, meta: dict) -> set[tuple[str, int, str]]:
    files = _files(meta)
    out: set[tuple[str, int, str]] = set()
    found: list = []
    _walk(tree.get("modulesp") or [], found, stop=())
    for n in found:
        loc = _loc(n)
        if loc:
            out.add((files.get(loc[0], ""), loc[1], n["type"]))
    return out


def shifter(texts: dict[str, bytes], sites: dict[tuple, Site]):
    """shift(file, line, column): the column in the instrumented text of an original column. Every edit is an
    insertion without a newline, placed before the byte at its offset."""
    ins: dict[str, list[tuple[int, int]]] = defaultdict(list)
    srcs: dict[str, _Src] = {}
    for s in sites.values():
        if s.file in texts:
            src = srcs.setdefault(s.file, _Src(texts[s.file]))
            e = edits_for(src, s)
            if not isinstance(e, str):
                ins[s.file] += [(off, len(text.encode())) for off, _o, text in e]

    def shift(f: str, line: int, col: int) -> int:
        if f not in srcs:
            return col
        start = srcs[f].starts[line - 1]
        off = start + col - 1
        return col + sum(n for o, n in ins[f] if start <= o <= off)
    return shift


def verify(tree0: dict, meta0: dict, tree1: dict, meta1: dict, sites: dict[tuple, Site], shift=None) -> dict[tuple, str]:
    """Why a site's marker is not where it should be in the instrumented design (the IF and case items of
    the copy must be those of the original, on the same lines; each marker the first statement of its
    branch, and in a combinational block cleared first in the block)."""
    if _shape(tree0, meta0) != _shape(tree1, meta1):
        return {k: "the copy has other IF or case items than the original" for k in sites}
    again, why0 = locate(tree1, meta1, set(sites), {k[0]: s.tag for k, s in sites.items()}, shift)
    why: dict[tuple, str] = {}
    for key, s in sites.items():
        t = again.get(key)
        if t is None:
            why[key] = "not found in the copy: " + why0.get(key, "")
            continue
        body = t.body
        first = None
        if len(body) == 1 and body[0].get("type") == "BEGIN":
            st = [x for x in body[0].get("stmtsp") or [] if isinstance(x, dict)]
            first = st[0] if st else None
        want = "ASSIGNDLY" if s.clocked else "ASSIGN"
        if first is None or first.get("type") != want or _lhs(first) != s.marker:
            why[key] = "marker is not the first statement of the branch in the copy"
            continue
        if t.clocked != s.clocked:
            why[key] = "the always block changed"
            continue
        if s.reset is not None:
            rb = (t.reset or {}).get("thensp") or []
            st = ([x for x in rb[0].get("stmtsp") or [] if isinstance(x, dict)]
                  if len(rb) == 1 and rb[0].get("type") == "BEGIN" else [])
            if not any(x.get("type") == "ASSIGNDLY" and _lhs(x) == s.marker for x in st):
                why[key] = "marker is not reset in the reset branch of the copy"
                continue
        if not s.clocked:
            st = [x for x in (t.block or {}).get("stmtsp") or [] if isinstance(x, dict)]
            if not any(x.get("type") == "ASSIGN" and _lhs(x) == s.marker for x in st[:len(sites) + 1]):
                why[key] = "marker is not cleared first in the combinational block"
    return why


# --------------------------------------------------------------------------------- proving
JSON_RUN = ("cd src && verilator --json-only -fno-const -fno-const-before-dfg -Wno-fatal -Wno-lint -Wno-style "
            "--Mdir ../j --top-module {top} "
            "{gen} {defs} +incdir+. {srcs} > ../j.log 2>&1; echo NNC_RC=$? >> ../j.log\n")


def _tree(host, files: dict, top: str, srcs: list[str], params: dict, defines: list[str], tag: str):
    gen = " ".join(f"-G{k}={v}" for k, v in params.items())
    defs = " ".join(f"+define+{d}" for d in defines)
    r = host.run(files, JSON_RUN.format(top=top, gen=gen, defs=defs, srcs=" ".join(srcs)),
                 ["j/*.tree.json", "j/*.tree.meta.json", "j.log"], timeout_s=1800, tag=tag)
    out = Path(r.out_dir)
    trees, metas = sorted((out / "j").glob("*.tree.json")), sorted((out / "j").glob("*.tree.meta.json"))
    if len(trees) != 1 or len(metas) != 1:
        log = out / "j.log"
        tail = log.read_text(encoding="utf-8", errors="replace").splitlines()[-4:] if log.is_file() else []
        return None, None, " | ".join(tail)
    return (json.loads(trees[0].read_text(encoding="utf-8")), json.loads(metas[0].read_text(encoding="utf-8")),
            None)


def wire(inst: str, marker: str) -> str:
    return f"{inst}.{marker}" if inst else marker


def _write_copy(copy_dir: Path, rtl_dir: Path, allf: list[Path], new: dict[str, bytes]) -> None:
    """The instrumented copy: every file of the RTL folder (and the include files of other folders), the
    instrumented ones replaced."""
    if copy_dir.exists():
        shutil.rmtree(copy_dir)
    copy_dir.mkdir(parents=True)
    for f in rtl_dir.iterdir():
        if f.is_file():
            shutil.copy2(f, copy_dir / f.name)
    for f in allf:
        if not (copy_dir / f.name).exists():
            shutil.copy2(f, copy_dir / f.name)
    for name, data in new.items():
        (copy_dir / name).write_bytes(data)


def prove_config(host, contract: dict, rtl_dir: Path, params: dict, defines: list[str], frontend: str,
                 todo: dict[Key, list[int]], copy_dir: Path, *, parallel: int = 4,
                 control_bits: list | None = None, cut: list[str] | tuple = ()) -> dict:
    """Prove the branches `todo` in one configuration: {"proven", "cex", "open": [keys], "skipped":
    {reason: [keys]}, "tasks", "control", "vacuous_tasks", "error"}. `copy_dir`: where the instrumented copy
    of the RTL is written."""
    from nnc import unr
    from nnc.sim import rtl_files
    rec: dict = {"proven": [], "cex": [], "open": [], "skipped": defaultdict(list), "tasks": 0}
    top = contract["top"]
    rtl = rtl_files(rtl_dir)
    allf = unr._all_rtl(rtl)
    srcs = [f.name for f in rtl]
    tags = {f.name: i for i, f in enumerate(allf)}
    tree0, meta0, err = _tree(host, {f"src/{f.name}": f for f in allf}, top, srcs, params, defines, "unrb_tree")
    if tree0 is None:
        rec["error"] = "no Verilator tree: " + (err or "")
        return _done(rec)
    sites, why = locate(tree0, meta0, {k[1:] for k in todo}, tags)
    texts = {f.name: f.read_bytes() for f in allf}
    for attempt in range(2):
        new, bad = instrument(texts, sites)
        why.update(bad)
        for k in bad:
            sites.pop(k, None)
        if not sites:
            break
        _write_copy(copy_dir, rtl_dir, allf, new)
        copied = {f"src/{f.name}": copy_dir / f.name for f in allf}
        tree1, meta1, err = _tree(host, copied, top, srcs, params, defines, "unrb_check")
        bad = (verify(tree0, meta0, tree1, meta1, sites, shifter(texts, sites)) if tree1 is not None
               else {k: "the copy does not elaborate: " + (err or "") for k in sites})
        if not bad:
            break
        why.update(bad)
        for k in bad:
            sites.pop(k, None)
        if attempt == 1:          # the copy without the failed markers failed again: try nothing
            why.update({k: "the copy failed its check twice" for k in sites})
            sites = {}
    for key in todo:
        if key[1:] in why:
            rec["skipped"][why[key[1:]][:120]].append(list(key))
    if not sites:
        return _done(rec)
    cands: dict[str, set[int]] = {}
    owner: dict[str, list[Key]] = defaultdict(list)
    zero: set[str] = set()
    for key in todo:
        s = sites.get(key[1:])
        if s is None:
            continue
        w = wire(key[0], s.marker)
        cands[w] = {0}
        owner[w].append(key)
        if not s.clocked:
            zero.add(s.marker)
    r = unr.prove_config(host, contract, copy_dir, params, defines, frontend, cands, parallel=parallel,
                         control_bits=control_bits, cut=cut, zero=zero)
    for f in ("error", "tasks", "control", "vacuous_tasks", "multiclock"):
        if f in r:
            rec[f] = r[f]
    for w, keys in owner.items():
        st = ("proven" if w in r.get("proven", {}) else "cex" if w in r.get("cex", {}) else
              "open" if w in r.get("open", {}) else None)
        for key in keys:
            if st:
                rec[st].append(list(key))
            elif w in (r.get("inputs") or []):
                rec["skipped"]["marker is an input"].append(list(key))
            else:
                rec["skipped"]["marker not in the netlist (a cut module, or another instance name)"].append(list(key))
    return _done(rec)


def _done(rec: dict) -> dict:
    rec["skipped"] = {k: sorted(v) for k, v in sorted(rec["skipped"].items())}
    for k in ("proven", "cex", "open"):
        rec[k] = sorted(rec[k])
    return rec


# ---------------------------------------------------------------------------------- record
def undecided(conf: dict | None, todo: dict[Key, list[int]]) -> dict[Key, list[int]]:
    """The targets without a PROVEN or counterexample result in this configuration."""
    if not conf:
        return dict(todo)
    done = {tuple(k) for f in ("proven", "cex") for k in conf.get(f) or []}
    return {k: v for k, v in todo.items() if k not in done}


def merge(conf: dict | None, new: dict) -> dict:
    """Add a new run's results to a configuration's branch record (a later result replaces "open" and
    "skipped")."""
    if not conf:
        return new
    decided = {tuple(k) for f in ("proven", "cex") for k in new.get(f) or []}
    out = dict(conf)
    for f in ("proven", "cex"):
        out[f] = sorted({tuple(k) for k in (conf.get(f) or []) + (new.get(f) or [])})
        out[f] = [list(k) for k in out[f]]
    tried = decided | {tuple(k) for k in new.get("open") or []} | {
        tuple(k) for v in (new.get("skipped") or {}).values() for k in v}
    out["open"] = sorted([list(k) for k in conf.get("open") or [] if tuple(k) not in tried]
                         + [list(k) for k in new.get("open") or []])
    sk: dict[str, list] = defaultdict(list)
    for r, ks in (conf.get("skipped") or {}).items():
        sk[r] += [k for k in ks if tuple(k) not in tried]
    for r, ks in (new.get("skipped") or {}).items():
        sk[r] += ks
    out["skipped"] = {r: sorted(v) for r, v in sorted(sk.items()) if v}
    for f in ("error", "control", "vacuous_tasks", "multiclock", "name", "params", "defines"):
        if f in new:
            out[f] = new[f]
    if "error" not in new:              # the error of an earlier run does not describe this one
        out.pop("error", None)
    out["tasks"] = int(conf.get("tasks", 0)) + int(new.get("tasks", 0))
    return out


def proven_blocks(branches: dict, keys: list[str]) -> list[list] | None:
    """Branches PROVEN in every configuration; None when a configuration has no record."""
    confs = [branches.get(k) for k in keys]
    if not confs or any(c is None for c in confs):
        return None
    sets = [{tuple(k) for k in c.get("proven") or []} for c in confs]
    return [list(k) for k in sorted(set.intersection(*sets))]

"""Formal proof that uncovered expression points cannot be reached (ROADMAP 24, code only, no LLM).

Verilator's expression coverage (--coverage-expr) has one point per combination of the terms of a condition:
`(we==0 && de==0) => 0` at the column of the operator. A point that no run hit may be unreachable: a term tied
off in the configuration, two signals that never hold at once. This module proves such points with the
machinery of nnc/unr.py, on an instrumented copy of the RTL, as nnc/unrbranch.py does for branches:

1. targets: the expression points of the merged coverage.dat with no hit, keyed by instance, file, line,
   column and the combination text.
2. `verilator --json-only` of the configuration gives the module of each target and the context of the
   expression at that position. A target is tried only when its terms can be read at module level with the
   same meaning: every name in a term is a signal or parameter declared at module level in every elaboration
   of the module (no loop variable, no name of a generate block, function or local block that would hide it),
   no term calls a function or selects a struct member, a bit select is only on a packed vector `[H:0]` (or a
   packed struct, union or enum over one: there Verilator's printed index and the source's agree; see
   plain_vector), the expression is in an always block or a continuous assignment (not in a
   function, task or initial block) and, in procedural code, no blocking assignment of that block writes a
   term's signal (the value at the expression would differ from the value at module level).
3. A copy of the RTL gets, just before `endmodule` (on the same line, so no line number moves), one marker
   per combination: `(* keep *) wire m = ((|(t1)) == 1'b0) && ((|(t2)) == 1'b1);`. The point can be hit
   only at a time when the combination holds, so it is never hit after the first reset when the marker stays 0.
4. Self-check: `verilator --json-only` of the copy must show every marker at module level of every
   elaboration of its module, driven by a continuous assignment that reads only module-level names, and the
   same IF and case items on the same lines as the original. A marker that fails (or that Verilator reports
   an error on) is left out and its point stays counted.
5. unr.prove_config proves the markers 0 (its `zero` assertion), with the guard and control assertions of
   toggle points.

The marker is stronger than the point (it holds whenever the combination holds, also when the expression is
not evaluated), so a PROVEN marker is sound; a counterexample does not show that the point is reachable, and
the point stays counted. A PROVEN point (in every configuration of the run set) leaves the expression coverage.
Like the other proofs, a proof is about the design after the first reset, with every input free.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from nnc import coverage as cov
from nnc import unrbranch as ub

PREFIX = "nnc_ex"
Key = tuple   # (instance relative to the DUT top, file, line, column, combination text)

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_$]*")
_LITERAL = re.compile(r"(?<![A-Za-z0-9_$])(?:\d*\s*'[sS]?[bBoOdDhH]\s*[0-9a-fA-FxXzZ?_]+|\d*'\s*(?=\()|\d+(?:\.\d+)?)")
_SYSTEM = re.compile(r"\$[A-Za-z_][A-Za-z0-9_$]*")
_PKG = re.compile(r"[A-Za-z_][A-Za-z0-9_$]*\s*::\s*[A-Za-z_][A-Za-z0-9_$]*")
_KEYWORDS = {"inside", "with", "or", "and", "not"}


# ------------------------------------------------------------------------------------ targets
def targets(dat_path: Path, rtl_names: list[str]) -> list[Key]:
    """Keys of the DUT's expression points that no run hit."""
    hits: dict[Key, int] = defaultdict(int)
    if not dat_path.is_file():
        return []
    for kv, name, metric, line, _span, count in cov._records(dat_path, set(rtl_names)):
        if metric != "expression":
            continue
        key = cov.expr_key(kv, name, line)
        if key is not None:
            hits[key] += count
    return sorted(k for k, n in hits.items() if n == 0)


# ---------------------------------------------------------------------------------- the terms
def _split(text: str, sep: str) -> list[str] | None:
    """`text` split at `sep` where no bracket is open; None when brackets do not balance."""
    out, depth, start, i = [], 0, 0, 0
    while i < len(text):
        c = text[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
            if depth < 0:
                return None
        elif depth == 0 and text.startswith(sep, i):
            out.append(text[start:i])
            i += len(sep)
            start = i
            continue
        i += 1
    if depth:
        return None
    out.append(text[start:])
    return out


def _balanced(text: str) -> bool:
    return _split(text, "\0") is not None


def terms(combo: str) -> list[tuple[str, int]] | None:
    """[(term, 0 or 1)] of a combination text `(a==0 && (b == c)==1) => 1`; None when it cannot be read."""
    parts = _split(combo.strip(), " => ")
    if not parts or len(parts) != 2:
        return None
    left = parts[0].strip()
    if not (left.startswith("(") and left.endswith(")")) or not _balanced(left[1:-1]):
        return None
    out = []
    for part in _split(left[1:-1], " && ") or []:
        m = re.fullmatch(r"(.+)==([01])", part.strip(), re.S)
        if not m or not _balanced(m[1]) or not m[1].strip():
            return None
        out.append((m[1].strip(), int(m[2])))
    return out or None


def names(term: str) -> tuple[set[str], bool]:
    """(the names a term reads, whether it calls a function). A package item (`pkg::X`), a system function,
    a literal and a member after `.` are not names of the module."""
    t = _PKG.sub(" ", _SYSTEM.sub(" ", term))
    t = _LITERAL.sub(" ", t)
    found, call = set(), False
    for m in _IDENT.finditer(t):
        before = t[:m.start()].rstrip()
        if before.endswith("."):
            continue
        if m.group() in _KEYWORDS:
            continue
        if t[m.end():].lstrip().startswith("("):
            call = True
        found.add(m.group())
    return found, call


# a name that a select follows: not a member (after "."), not a package item, not inside a literal
_SELECTED = re.compile(r"(?<![A-Za-z0-9_$'.:])([A-Za-z_][A-Za-z0-9_$]*)(?=\s*\[)")
_MEMBER = re.compile(r"\.\s*[A-Za-z_]")
_ZERO_LSB = re.compile(r"\d+:0")


def selected(term: str) -> set[str]:
    """Names in the term that a select follows."""
    return set(_SELECTED.findall(term))


_CHAIN = re.compile(r"(?<![A-Za-z0-9_$.'])([A-Za-z_][A-Za-z0-9_$]*)((?:\[\d+(?::\d+)?\]){2,})")
_SEL = re.compile(r"\[(\d+)(?::(\d+))?\]")


def flat_selects(text: str) -> str:
    """Constant selects that Verilator prints chained (`reg2hw[321:312][3:2][0]`, a struct member's bits) as
    one select (`reg2hw[314]`), which Yosys reads. Each select of a chain is numbered from 0 within the value
    of the one before it (Verilator's SEL), so the offsets add up."""
    def one(m: re.Match) -> str:
        lsb, width = 0, None
        for g in _SEL.finditer(m[2]):
            hi, lo = int(g[1]), int(g[2] if g[2] is not None else g[1])
            if hi < lo or (width is not None and hi >= width):
                return m[0]
            lsb, width = lsb + lo, hi - lo + 1
        return f"{m[1]}[{lsb}]" if width == 1 else f"{m[1]}[{lsb + width - 1}:{lsb}]"
    return _CHAIN.sub(one, text)


def condition(combo: str) -> str | None:
    """The marker's expression: true exactly when the combination holds."""
    ts = terms(combo)
    if ts is None:
        return None
    return " && ".join(f"((|({flat_selects(t)})) == 1'b{v})" for t, v in ts)


def types_of(tree: dict) -> dict[str, dict]:
    """{address: node} of the tree's data types (and every other node with an address)."""
    out: dict[str, dict] = {}
    stack: list = [tree]
    while stack:
        n = stack.pop()
        if isinstance(n, list):
            stack.extend(n)
        elif isinstance(n, dict):
            if "addr" in n:
                out[n["addr"]] = n
            stack.extend(v for v in n.values() if isinstance(v, (list, dict)))
    return out


def plain_vector(types: dict[str, dict], addr: str | None) -> bool:
    """Whether a select on a signal of this data type means the same bits in the source and in Verilator's
    text: a packed vector `[H:0]`, or a packed struct, union or enum over one. Verilator prints a bit select
    in the declared numbering of a vector (`x[1]` is the LSB of `logic [8:1] x`) but on the flattened value of
    a packed array (`p[6+:2][0]` for `p[3][0]` of `logic [3:0][1:0] p`), so any other type is not tried."""
    seen = 0
    while addr and seen < 20:
        seen += 1
        n = types.get(addr)
        if n is None:
            return False
        kind = n.get("type")
        if kind in ("REFDTYPE", "ENUMDTYPE", "CONSTDTYPE", "STRUCTDTYPE", "UNIONDTYPE"):
            if kind in ("STRUCTDTYPE", "UNIONDTYPE") and not n.get("packed"):
                return False
            addr = n.get("refDTypep") or (n.get("dtypep") if kind == "REFDTYPE" else None)
            continue
        if kind == "BASICDTYPE":
            return bool(_ZERO_LSB.fullmatch(str(n.get("range") or "")))
        return False
    return False


# -------------------------------------------------------------------------------- the context
@dataclass
class Site:
    """The expression points of one position (file, line, column), all in one module text."""
    file: str
    line: int
    col: int
    mod_line: int               # line of the module name: the clones of one module text share it
    combos: list[str] = field(default_factory=list)
    tag: int = 0

    def marker(self, i: int) -> str:
        return f"{PREFIX}{self.tag}_{self.line}_{self.col}_{i}"


def _vars(n) -> set[str]:
    return {s.get("name") for s in (n.get("stmtsp") or []) if isinstance(s, dict) and s.get("type") == "VAR"}


def _written_blocking(n, out: set) -> set:
    """Names written by blocking assignments under n."""
    if isinstance(n, list):
        for x in n:
            _written_blocking(x, out)
    elif isinstance(n, dict):
        if n.get("type") == "ASSIGN":
            ub._names(n.get("lhsp"), out)
        for k, v in n.items():
            if isinstance(v, (dict, list)) and k != "dtypep":
                _written_blocking(v, out)
    return out


def _find(n, f_id: str, line: int, col: int, path: list, out: list) -> None:
    """Paths (list of nodes from the module down) of the nodes whose location starts at (line, col)."""
    if isinstance(n, list):
        for x in n:
            _find(x, f_id, line, col, path, out)
        return
    if not isinstance(n, dict):
        return
    loc = ub._loc(n)
    if loc and loc[0] == f_id and loc[1] == line and loc[2] == col and n.get("type") not in ("VAR", "VARREF"):
        out.append(path + [n])
    for k, v in n.items():
        if isinstance(v, (dict, list)) and k not in ("dtypep", "sentreep"):
            _find(v, f_id, line, col, path + [n], out)


def modules_of(tree: dict, meta: dict) -> dict[tuple[str, int], list[dict]]:
    """{(file, line of the module name): [MODULE nodes]}: the elaborations (clones) of each module text."""
    files = ub._files(meta)
    out: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for m in tree.get("modulesp") or []:
        if isinstance(m, dict) and m.get("type") == "MODULE":
            loc = ub._loc(m)
            if loc:
                out[(files.get(loc[0], ""), loc[1])].append(m)
    return out


def locate(tree: dict, meta: dict, wanted: dict[tuple[str, int, int], list[str]],
           file_tags: dict[str, int] | None = None) -> tuple[dict[tuple, Site], dict[tuple, str]]:
    """For every wanted (file, line, column) with its combination texts: its Site (the combinations that can
    be tried), or why a combination is not tried; `why` is keyed (file, line, column, combination)."""
    files = ub._files(meta)
    ids = defaultdict(list)
    for fid, name in files.items():
        ids[name].append(fid)
    mods = modules_of(tree, meta)
    types = types_of(tree)
    sites: dict[tuple, Site] = {}
    why: dict[tuple, str] = {}
    for (f, line, col), combos in sorted(wanted.items()):
        def no(reason, cs=combos):
            for c in cs:
                why[(f, line, col, c)] = reason
        found: list = []
        owners: dict[int, tuple] = {}
        for (mf, mline), clones in mods.items():
            if mf != f:
                continue
            for m in clones:
                n0 = len(found)
                for fid in ids.get(f, []):
                    _find(m.get("stmtsp") or [], fid, line, col, [m], found)
                for p in found[n0:]:
                    owners[id(p[-1])] = (mf, mline)
        if not found:
            no("expression not found in the tree")
            continue
        texts = {owners[id(p[-1])] for p in found}
        if len(texts) != 1:
            no("several modules at this position")
            continue
        mkey = next(iter(texts))
        clones = mods[mkey]
        common = set.intersection(*[_vars(m) for m in clones])
        dtypes = [{s.get("name"): s.get("dtypep") for s in m.get("stmtsp") or []
                   if isinstance(s, dict) and s.get("type") == "VAR"} for m in clones]
        bad_ctx, inner, written = None, set(), set()
        for p in found:
            kinds = [x.get("type") for x in p]
            if any(k in ("FUNC", "TASK", "INITIAL", "INITIALSTATIC", "FINAL") for k in kinds):
                bad_ctx = "in a function, task or initial block"
                break
            alw = [x for x in p if x.get("type") == "ALWAYS"]
            if not alw:
                bad_ctx = "not in an always block or continuous assignment"
                break
            for x in p[1:]:
                if x.get("type") in ("GENBLOCK", "BEGIN", "ALWAYS"):
                    inner |= _vars(x)
            if alw[0].get("keyword") != "cont_assign":
                written |= _written_blocking(alw[0].get("stmtsp") or [], set())
        if bad_ctx:
            no(bad_ctx)
            continue
        ok = []
        for c in combos:
            ts = terms(c)
            if ts is None:
                why[(f, line, col, c)] = "combination text not read"
                continue
            used, call, member, sel = set(), False, False, set()
            for t, _v in ts:
                n, k = names(t)
                used |= n
                call = call or k
                member = member or bool(_MEMBER.search(_LITERAL.sub(" ", t)))
                sel |= selected(t)
            if call:
                why[(f, line, col, c)] = "a term calls a function"
            elif member:
                why[(f, line, col, c)] = "a term selects a member (its bit numbering is not checked)"
            elif not used:
                why[(f, line, col, c)] = "no signal in the terms"
            elif used - common:
                why[(f, line, col, c)] = "a term reads a name that is not declared at module level"
            elif used & inner:
                why[(f, line, col, c)] = "a term reads a name of a local block"
            elif used & written:
                why[(f, line, col, c)] = "a term reads a signal that its block writes with a blocking assignment"
            elif any(not plain_vector(types, d.get(n)) for n in sel for d in dtypes):
                why[(f, line, col, c)] = "a term selects bits of a signal that is not a packed vector [H:0]"
            else:
                ok.append(c)
        if ok:
            sites[(f, line, col)] = Site(f, line, col, mkey[1], sorted(ok), (file_tags or {}).get(f, 0))
    return sites, why


# ------------------------------------------------------------------------------- the RTL text
def endmodule_at(src: ub._Src, line: int) -> int | None:
    """Offset of the `endmodule` that closes the module whose name is on `line`."""
    i = src.starts[line - 1]
    b = src.b
    while i < len(b):
        if b.startswith(b"//", i) or b.startswith(b"/*", i):
            i = src.skip(i)
            continue
        c = b[i:i + 1]
        if c == b'"':
            i = src._string(i)
            continue
        if c == b"\\":
            i = src._escaped(i)
            continue
        w = src.ident(i)
        if w:
            if w == "endmodule" and (i == 0 or not (chr(b[i - 1]).isalnum() or b[i - 1] in b"_$")):
                return i
            i += len(w)
            continue
        i += 1
    return None


def instrument(texts: dict[str, bytes], sites: dict[tuple, Site]
               ) -> tuple[dict[str, bytes], dict[tuple, str], dict[str, list[tuple[int, int, int, set]]]]:
    """(instrumented texts, why a combination was left out, {file: [(line, first column, end column, markers)]}
    of the inserted declarations). No edit adds a line."""
    edits: dict[str, dict[int, list[tuple[str, set]]]] = defaultdict(lambda: defaultdict(list))
    why: dict[tuple, str] = {}
    for key, s in sorted(sites.items()):
        if s.file not in texts:
            for c in s.combos:
                why[(s.file, s.line, s.col, c)] = "file not found"
            continue
        src = ub._Src(texts[s.file])
        at = endmodule_at(src, s.mod_line)
        if at is None:
            for c in s.combos:
                why[(s.file, s.line, s.col, c)] = "endmodule not found"
            continue
        for i, c in enumerate(s.combos):
            edits[s.file][at].append((f"(* keep *) wire {s.marker(i)} = {condition(c)}; ", {s.marker(i)}))
    out: dict[str, bytes] = {}
    spans: dict[str, list] = defaultdict(list)
    for f, at_map in edits.items():
        b = texts[f]
        for off in sorted(at_map, reverse=True):
            b = b[:off] + "".join(d for d, _m in at_map[off]).encode() + b[off:]
        new = ub._Src(b)
        for decls in at_map.values():
            for d, mk in decls:
                i = b.find(d.encode())
                line = max(n for n, s0 in enumerate(new.starts) if s0 <= i) + 1
                col = i - new.starts[line - 1] + 1
                spans[f].append((line, col, col + len(d.encode()), set(mk)))
        out[f] = b
    return out, why, dict(spans)


_ERR = re.compile(r"%Error[^:]*: (?:\S*/)?([^/:\s]+):(\d+):(\d+):")


def error_markers(log: str, spans: dict[str, list]) -> set[str]:
    """Markers whose declaration a Verilator error points into."""
    out = set()
    for m in _ERR.finditer(log):
        f, line, col = m[1], int(m[2]), int(m[3])
        for l2, c0, c1, mks in spans.get(f, []):
            if l2 == line and c0 <= col < c1:
                out |= mks
    return out


_FILE_ERR = re.compile(r"([A-Za-z0-9_.$-]+\.s?v[h]?):\d+")


def error_files(text: str, files: set[str]) -> set[str]:
    """Instrumented files that a Yosys or yosys-slang error names."""
    return {m[1] for m in _FILE_ERR.finditer(text or "") if m[1] in files}


def verify(tree0: dict, meta0: dict, tree1: dict, meta1: dict, sites: dict[tuple, Site]) -> dict[str, str]:
    """{marker: why it is not as it should be in the copy}: every marker at module level of every clone of
    its module, driven by one continuous assignment that reads only module-level names; the IF and case
    items of the copy those of the original."""
    if ub._shape(tree0, meta0) != ub._shape(tree1, meta1):
        return {s.marker(i): "the copy has other IF or case items than the original"
                for s in sites.values() for i in range(len(s.combos))}
    mods = modules_of(tree1, meta1)
    why: dict[str, str] = {}
    for s in sites.values():
        clones = mods.get((s.file, s.mod_line)) or []
        for i in range(len(s.combos)):
            mk = s.marker(i)
            if not clones:
                why[mk] = "module not found in the copy"
                continue
            for m in clones:
                top = _vars(m)
                if mk not in top:
                    why[mk] = "marker not declared at module level in the copy"
                    break
                drivers = []
                for a in m.get("stmtsp") or []:
                    if not isinstance(a, dict) or a.get("type") != "ALWAYS" or a.get("keyword") != "cont_assign":
                        continue
                    for st in a.get("stmtsp") or []:
                        if isinstance(st, dict) and st.get("type") == "ASSIGNW" and ub._lhs(st) == mk:
                            drivers.append(st)
                if len(drivers) != 1:
                    why[mk] = "marker is not driven by one continuous assignment in the copy"
                    break
                read = ub._names(drivers[0].get("rhsp"), set())
                if read - top:
                    why[mk] = "marker reads a name that is not at module level in the copy"
                    break
    return why


# --------------------------------------------------------------------------------- proving
def prove_config(host, contract: dict, rtl_dir: Path, params: dict, defines: list[str], frontend: str,
                 todo: list[Key], copy_dir: Path, *, parallel: int = 4,
                 control_bits: list | None = None, cut: list[str] | tuple = ()) -> dict:
    """Prove the expression points `todo` in one configuration: {"proven", "cex", "open": [keys], "skipped":
    {reason: [keys]}, "tasks", "control", "vacuous_tasks", "error"}."""
    from nnc import unr
    from nnc.sim import rtl_files
    rec: dict = {"proven": [], "cex": [], "open": [], "skipped": defaultdict(list), "tasks": 0}
    top = contract["top"]
    rtl = rtl_files(rtl_dir)
    allf = unr._all_rtl(rtl)
    srcs = [f.name for f in rtl]
    tags = {f.name: i for i, f in enumerate(allf)}
    tree0, meta0, err = ub._tree(host, {f"src/{f.name}": f for f in allf}, top, srcs, params, defines, "unre_tree")
    if tree0 is None:
        rec["error"] = "no Verilator tree: " + (err or "")
        return ub._done(rec)
    wanted: dict[tuple, list[str]] = defaultdict(list)
    for k in todo:
        if k[4] not in wanted[k[1:4]]:
            wanted[k[1:4]].append(k[4])
    sites_all, why = locate(tree0, meta0, wanted, tags)
    texts = {f.name: f.read_bytes() for f in allf}
    for sites in batches(sites_all):
        part = _prove_batch(host, contract, rtl_dir, params, defines, frontend, todo, copy_dir, sites, why, texts,
                            allf, srcs, top, tree0, meta0, parallel=parallel, control_bits=control_bits, cut=cut)
        for f in ("proven", "cex", "open"):
            rec[f] += part[f]
        rec["tasks"] += int(part.get("tasks", 0))
        if part.get("vacuous_tasks"):
            rec["vacuous_tasks"] = rec.get("vacuous_tasks", 0) + int(part["vacuous_tasks"])
        for f in ("control", "multiclock"):
            if f in part:
                rec[f] = part[f]
        if part.get("error"):
            rec["error"] = "; ".join(x for x in (rec.get("error"), str(part["error"])) if x)
        for w, ks in part["skipped"].items():
            rec["skipped"][w] += ks
    done = {tuple(k) for f in ("proven", "cex", "open") for k in rec[f]} | \
        {tuple(k) for v in rec["skipped"].values() for k in v}
    for key in todo:
        if tuple(key) not in done and key[1:] in why:
            rec["skipped"][why[key[1:]][:120]].append(list(key))
    return ub._done(rec)


# Verilator stops on a line of more than 40000 preprocessor tokens; every marker of a module is on its endmodule
# line, so the markers go in batches (one copy and one proof each) of at most this many tokens per line
LINE_TOKENS = 20000
_TOKEN = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*|\d*'[sS]?[bBoOdDhH][0-9a-fA-FxXzZ?_]+|\d+|\S")


def tokens(text: str) -> int:
    return len(_TOKEN.findall(text))


def batches(sites: dict[tuple, Site], limit: int = LINE_TOKENS) -> list[dict[tuple, Site]]:
    """The sites in groups whose markers add at most `limit` tokens to any one endmodule line (a site's markers
    stay together; a site above the limit goes alone, and Verilator's error leaves it out)."""
    out: list[dict[tuple, Site]] = []
    load: list[dict[tuple, int]] = []
    for key, s in sorted(sites.items()):
        n = sum(tokens(f"(* keep *) wire {s.marker(i)} = {condition(c)}; ") for i, c in enumerate(s.combos))
        mod = (s.file, s.mod_line)
        for b, l in zip(out, load):
            if l.get(mod, 0) + n <= limit:
                break
        else:
            b, l = {}, {}
            out.append(b)
            load.append(l)
        b[key] = s
        l[mod] = l.get(mod, 0) + n
    return out


def _prove_batch(host, contract: dict, rtl_dir: Path, params: dict, defines: list[str], frontend: str,
                 todo: list[Key], copy_dir: Path, sites: dict[tuple, Site], why: dict, texts: dict, allf: list,
                 srcs: list[str], top: str, tree0: dict, meta0: dict, *, parallel: int,
                 control_bits: list | None, cut) -> dict:
    """prove_config for one batch of sites; `why` gets the reasons of the combinations left out."""
    from nnc import unr
    rec: dict = {"proven": [], "cex": [], "open": [], "skipped": defaultdict(list), "tasks": 0}
    r: dict = {}

    def drop(markers: dict[str, str]) -> None:
        for key, s in list(sites.items()):
            keep = []
            for i, c in enumerate(s.combos):
                mk = s.marker(i)
                if mk in markers:
                    why[(s.file, s.line, s.col, c)] = markers[mk]
                else:
                    keep.append(c)
            if keep:
                s.combos = keep
            else:
                sites.pop(key)
    for attempt in range(3):
        if not sites:
            break
        new, bad, spans = instrument(texts, sites)
        why.update(bad)
        for k in {k[:3] for k in bad}:
            sites.pop(k, None)
        if not sites:
            break
        ub._write_copy(copy_dir, rtl_dir, allf, new)
        copied = {f"src/{f.name}": copy_dir / f.name for f in allf}
        tree1, meta1, err = _tree(host, copied, top, srcs, params, defines, "unre_check")
        if tree1 is None:
            hit = error_markers(err or "", spans)
            if not hit or attempt == 2:
                first = [x.strip() for x in (err or "").splitlines() if "%Error" in x][:1] or \
                    (err or "").strip().splitlines()[-1:]
                drop({s.marker(i): "the copy does not elaborate: " + " ".join(first)[:80]
                      for s in sites.values() for i in range(len(s.combos))})
                break
            drop({m: "Verilator reports an error on the marker" for m in hit})
            continue
        bad = verify(tree0, meta0, tree1, meta1, sites)
        if not bad:
            break
        drop(bad)
        if attempt == 2:
            drop({s.marker(i): "the copy failed its check three times"
                  for s in sites.values() for i in range(len(s.combos))})
    if not sites:
        return rec
    for attempt in range(3):
        cands: dict[str, set[int]] = {}
        owner: dict[str, list[Key]] = defaultdict(list)
        zero: set[str] = set()
        for key in todo:
            s = sites.get(key[1:4])
            if s is None or key[4] not in s.combos:
                continue
            mk = s.marker(s.combos.index(key[4]))
            w = ub.wire(key[0], mk)
            cands[w] = {0}
            owner[w].append(key)
            zero.add(mk)
        r = unr.prove_config(host, contract, copy_dir, params, defines, frontend, cands, parallel=parallel,
                             control_bits=control_bits, cut=cut, zero=zero)
        # Yosys (or yosys-slang) can refuse a marker that Verilator read: leave out the markers of the files it
        # names, and prove the others (the copy without them is the checked copy with fewer insertions)
        bad_files = error_files(r.get("error") or "", {s.file for s in sites.values()}) \
            if str(r.get("error") or "").startswith("no netlist") else set()
        if not bad_files or attempt == 2:
            break
        drop({s.marker(i): "Yosys does not read the marker: " + str(r["error"])[11:90]
              for s in sites.values() if s.file in bad_files for i in range(len(s.combos))})
        if not sites:
            break
        new, _bad, _spans = instrument(texts, sites)
        ub._write_copy(copy_dir, rtl_dir, allf, new)
    if not sites:
        return rec
    for f in ("error", "tasks", "control", "vacuous_tasks", "multiclock"):
        if f in r:
            rec[f] = r[f]
    for w, keys in owner.items():
        st = ("proven" if w in r.get("proven", {}) else "cex" if w in r.get("cex", {}) else
              "open" if w in r.get("open", {}) else None)
        for key in keys:
            if st:
                rec[st].append(list(key))
            else:
                rec["skipped"]["marker not in the netlist (a cut module, or another instance name)"].append(list(key))
    return ub._done(rec)


def _tree(host, files: dict, top: str, srcs: list[str], params: dict, defines: list[str], tag: str):
    """unrbranch._tree, with the whole log on failure (its errors point at the markers)."""
    import json
    gen = " ".join(f"-G{k}={v}" for k, v in params.items())
    defs = " ".join(f"+define+{d}" for d in defines)
    r = host.run(files, ub.JSON_RUN.format(top=top, gen=gen, defs=defs, srcs=" ".join(srcs)),
                 ["j/*.tree.json", "j/*.tree.meta.json", "j.log"], timeout_s=1800, tag=tag)
    out = Path(r.out_dir)
    trees, metas = sorted((out / "j").glob("*.tree.json")), sorted((out / "j").glob("*.tree.meta.json"))
    if len(trees) != 1 or len(metas) != 1:
        log = out / "j.log"
        return None, None, log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
    return (json.loads(trees[0].read_text(encoding="utf-8")), json.loads(metas[0].read_text(encoding="utf-8")),
            None)

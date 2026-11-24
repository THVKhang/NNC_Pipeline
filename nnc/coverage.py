"""Code coverage of the DUT from Verilator's coverage.dat (no LLM).

Verilator writes one record per coverage point: `C '<key/value pairs>' <count>`, keys separated by
\\x01 and key/value by \\x02 (f = file, l = line, page = v_line/<module>, v_toggle/..., v_expr/...,
o = comment, e.g. the signal and the transition `sig[3]:0->1`). Only points in the DUT RTL files count:
checkers and the testbench top are excluded from every denominator. Unlike metrics are never merged
into one number.

Metrics: `line` comes from the lcov export (lines, as before), `block` is Verilator's own line/branch
points (one per statement block or branch arm), `toggle` is one point per bit and direction of every
DUT signal, `expression` is one point per term combination of a condition (Verilator --coverage-expr).

Scope: Verilator instruments every function of an imported package, also those the design never calls
(OpenTitan's prim_secded_pkg alone has thousands of points). `verilator --json-only` of the DUT alone
gives the package functions the elaborated design keeps (scope_from_tree); with that scope, package
points outside them are left out of every denominator, counted per metric, and the counts over all points
stay in the result. Nothing else is ever left out: no hand exclusion, no waiver file.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

_SPAN = re.compile(r"\d+(-\d+)?(,\d+(-\d+)?)*")    # "S" of a block point: the lines it covers ("1004-1005")
PAGES = {"v_line": "block", "v_branch": "block", "v_toggle": "toggle", "v_expr": "expression", "v_fsm": "fsm"}

SCOPE_RULE = ("left out: never-executed points of package code that the elaborated design does not contain "
              "(Verilator instruments every function of an imported package, called or not), and toggles of "
              "signal bits that Yosys constant propagation proves constant with the run's parameters, except on "
              "signals where the simulator recorded a toggle of such a bit (then the signal counts whole)")
PROVEN_RULE = ("left out: toggle points of signal bits that SymbiYosys proves constant after the first reset for "
               "every input sequence (nnc/unr.py, work/unr.json: PROVEN in every configuration of the run set), "
               "except on signals where the simulator recorded a 1->0 toggle of such a bit")
DUT_HIER = "nnc_tb_top.u_dut"
_TOGGLE = re.compile(r"^(?P<sig>[A-Za-z_][\w$.]*?)(?:\[(?P<idx>\d+)\])?:[01]->[01]$")


# ------------------------------------------------------------------------------------ design scope
def scope_from_tree(tree: dict, meta: dict) -> dict:
    """Package code that the elaborated DUT contains, from `verilator --json-only` of the DUT alone:
    {"packages": [names], "kept": {file: "a-b,c"}}. After elaboration the tree keeps only the package
    functions and tasks that the design calls (directly or through another kept function); `kept` are the
    lines they span. A point whose hierarchy is a package and whose line is outside `kept` is not part of
    the design."""
    files = {k: Path(v.get("filename", "")).name for k, v in (meta.get("files") or {}).items()}
    packages: set[str] = set()
    kept: dict[str, set[int]] = defaultdict(set)
    stack: list = [(tree, False)]
    while stack:
        node, in_pkg = stack.pop()
        if isinstance(node, list):
            stack.extend((v, in_pkg) for v in node)
            continue
        if not isinstance(node, dict):
            continue
        kind = node.get("type")
        if kind == "PACKAGE":
            packages.add(node.get("name", ""))
            in_pkg = True
        if in_pkg and kind in ("FUNC", "TASK"):
            spans: dict[str, list[int]] = defaultdict(list)
            for f, a, b in _locs(node, files):
                spans[f] += [a, b]
            for f, ls in spans.items():
                kept[f].update(range(min(ls), max(ls) + 1))
            continue
        stack.extend((v, in_pkg) for v in node.values() if isinstance(v, (dict, list)))
    out = {"packages": sorted(p for p in packages if p),
           "kept": {f: line_ranges(v) for f, v in sorted(kept.items()) if f}}
    fields = struct_fields(tree)
    if fields:
        out["fields"] = fields
    return out


# ------------------------------------------------------------------------------------ struct fields
_INT_W = {"int": 32, "integer": 32, "byte": 8, "shortint": 16, "longint": 64, "time": 64}


def struct_fields(tree: dict) -> dict[str, list]:
    """Packed-struct field layout of every variable of the elaborated DUT, from `verilator --json-only`:
    {"u_reg.tl_i.a_address": ["u_reg.tl_i", lsb, right index, descending (1/0)]}, paths relative to the DUT
    top. Verilator names a toggle point per field ("tl_i.a_address[3]"); Yosys has one packed net
    ("tl_i"), whose bit lsb + (3 - right) that is. Only fields of a basic type (an enum resolves to one), in
    packed structs nested to any depth, are listed; a field of a packed array or a union is not, and stays
    unmatched."""
    nodes: dict[str, dict] = {}
    stack: list = [tree]
    while stack:
        n = stack.pop()
        if isinstance(n, dict):
            if n.get("addr"):
                nodes[n["addr"]] = n
            stack.extend(v for v in n.values() if isinstance(v, (dict, list)))
        elif isinstance(n, list):
            stack.extend(n)

    def resolve(a):
        n, seen = nodes.get(a), 0
        while n is not None and n.get("type") in ("REFDTYPE", "TYPEDEF", "ENUMDTYPE") and seen < 64:
            nxt = n.get("refDTypep") or (n.get("dtypep") if n.get("type") == "TYPEDEF" else None)
            if not nxt or nxt == n.get("addr"):
                break
            n, seen = nodes.get(nxt), seen + 1
        return n

    def packed_struct(n):
        return n is not None and n.get("type") == "STRUCTDTYPE" and bool(n.get("packed"))

    def leaves(st, prefix: str, base: int, out: dict, depth: int = 0) -> dict:
        for m in st.get("membersp") or []:
            mt = resolve(m.get("refDTypep") or m.get("dtypep"))
            lsb, path = base + int(m.get("lsb", 0) or 0), f"{prefix}.{m.get('name', '')}"
            if packed_struct(mt) and depth < 16:
                leaves(mt, path, lsb, out, depth + 1)
            elif mt is not None and mt.get("type") == "BASICDTYPE":
                r = mt.get("range")
                left, right = (int(x) for x in r.split(":")) if r else (0, 0)
                out[path] = [lsb, right, int(left >= right)]
        return out

    modules = [m for m in tree.get("modulesp") or [] if m.get("type") == "MODULE"]
    by_addr = {m.get("addr"): m for m in modules}
    out: dict[str, list] = {}
    todo = [(modules[0], "", 0)] if modules else []
    while todo:
        mod, path, depth = todo.pop()
        walk: list = [(mod.get("stmtsp") or [], path)]
        while walk:
            n, prefix = walk.pop()
            if isinstance(n, list):
                walk.extend((v, prefix) for v in n)
                continue
            if not isinstance(n, dict):
                continue
            kind = n.get("type")
            if kind == "VAR":
                st = resolve(n.get("dtypep"))
                if packed_struct(st):
                    base = prefix + n.get("name", "")
                    for f, v in leaves(st, base, 0, {}).items():
                        out[f] = [base] + v
                continue
            if kind == "CELL":
                child = by_addr.get(n.get("modp"))
                if child is not None and depth < 64:
                    todo.append((child, prefix + n.get("name", "") + ".", depth + 1))
                continue
            if kind in ("BEGIN", "GENBLOCK") and n.get("name"):
                prefix = prefix + n["name"] + "."
            walk.extend((v, prefix) for k, v in n.items() if isinstance(v, (dict, list)) and k != "dtypep")
    stars: dict[str, list] = {}
    bad: set[str] = set()
    for k, v in out.items():
        s = star_name(k)
        if s != k:
            sv = [star_name(v[0])] + v[1:]
            if stars.setdefault(s, sv) != sv:
                bad.add(s)
    out.update({s: v for s, v in stars.items() if s not in bad and s not in out})
    return out


_INST = re.compile(r"\[\d+\](?=\.)")


def star_name(name: str) -> str:
    """Verilator's name of a point that it merges over the instances of a generate loop: every instance
    index of the path becomes [*] ("gen_f[3].u.q" -> "gen_f[*].u.q"); a bit select at the end stays."""
    return _INST.sub("[*]", name)


def star_regex(name: str) -> re.Pattern:
    """The nets that a name with * can stand for. Verilator merges the points of several instances into one
    and writes * for the part of the path where their names differ ("u_*ata_in.qe", "gen_f[*].q"); every
    merged instance matches, and so may other nets (which only makes a check over all matches stricter)."""
    return re.compile("^" + ".*".join(re.escape(p) for p in name.split("*")) + "$")


def star_members(names, nets: list[str]) -> dict[str, list[str]]:
    """{name with *: the nets of `nets` it matches}, for the names that are not a net themselves."""
    have = set(nets)
    out: dict[str, list[str]] = {}
    for s in sorted(set(names)):
        if "*" in s and s not in have:
            rx = star_regex(s)
            members = [n for n in nets if rx.match(n)]
            if members:
                out[s] = members
    return out


def with_stars(bits: dict[str, set[int]], nets: list[str], names=()) -> dict[str, set[int]]:
    """`bits` plus, for every merged name (the [*] names of `nets` that group several instances, and the
    names with * of `names`), the bits that are in every net it matches (a merged point is constant only if
    it is constant in each instance)."""
    groups: dict[str, list[str]] = defaultdict(list)
    for n in nets:
        s = star_name(n)
        if s != n:
            groups[s].append(n)
    for s, members in star_members(names, nets).items():
        groups.setdefault(s, members)
    out = dict(bits)
    for s, members in groups.items():
        common = set.intersection(*(set(bits.get(m, ())) for m in members))
        if common and s not in out:
            out[s] = common
    return out


def star_signals(path: Path, rtl: set[str], fields: dict | None = None) -> set[str]:
    """The signal names with * of the toggle points of a coverage file."""
    out: set[str] = set()
    for kv, _name, metric, _line, _span, _count in _records(path, rtl):
        if metric == "toggle":
            bit = toggle_bit(kv, fields)
            if bit and "*" in bit[0]:
                out.add(bit[0])
    return out


def merge_fields(maps: list[dict | None]) -> dict:
    """Fields of a run set: an entry is kept only when every configuration that has it agrees on it."""
    out: dict[str, list] = {}
    bad: set[str] = set()
    for m in maps:
        for k, v in (m or {}).items():
            if k in out and out[k] != v:
                bad.add(k)
            out.setdefault(k, v)
    return {k: v for k, v in sorted(out.items()) if k not in bad}


def _locs(node, files: dict[str, str]):
    """(file, first line, last line) of every located node under `node` ("loc": "e,12:3,14:9")."""
    stack = [node]
    while stack:
        x = stack.pop()
        if isinstance(x, dict):
            loc = x.get("loc")
            if isinstance(loc, str) and loc.count(",") == 2:
                f, a, b = loc.split(",")
                try:
                    la, lb = int(a.split(":")[0]), int(b.split(":")[0])
                except ValueError:
                    la = lb = 0
                if f in files and la > 0:
                    yield files[f], la, max(la, lb)
            stack.extend(v for v in x.values() if isinstance(v, (dict, list)))
        elif isinstance(x, list):
            stack.extend(x)


def const_from_netlist(netlist: dict) -> dict | None:
    """Signal bits of the DUT that are constant after Yosys `proc; flatten; opt` (write_json of the top):
    {"nets": [names], "bits": {name: "declared indices"}, "ones": {name: indices whose value is 1}}, names
    relative to the DUT top ("u_rd.w_ptr"). Constant propagation is sound: such a bit holds one value in
    every run, so neither toggle exists (Verilator still records 0->1 once for a constant 1, at time zero,
    because its variables start at 0)."""
    tops = [m for m in (netlist.get("modules") or {}).values() if str((m.get("attributes") or {}).get("top", "0"))
            .strip("0") not in ("",)]
    if len(tops) != 1:
        return None
    nets, bits, ones = [], {}, {}
    for name, net in sorted((tops[0].get("netnames") or {}).items()):
        if net.get("hide_name") or name.startswith("$"):
            continue
        nets.append(name)
        b = net.get("bits") or []
        off, upto, w = int(net.get("offset", 0) or 0), bool(net.get("upto", 0)), len(b)
        idx = lambda i: off + (w - 1 - i if upto else i)
        const = [idx(i) for i, x in enumerate(b) if x in ("0", "1")]
        if const:
            bits[name] = line_ranges(const)
        one = [idx(i) for i, x in enumerate(b) if x == "1"]
        if one:
            ones[name] = line_ranges(one)
    return {"nets": nets, "bits": bits, "ones": ones}


def merge_scopes(scopes: list[dict | None]) -> dict | None:
    """Scope of a merged run set from the scopes of its configurations; None when any is unknown (then
    nothing is left out). Package code: the union of what each configuration contains. Constant bits: a
    bit counts as constant only if it is constant in every configuration that has its signal."""
    if not scopes or any(not s for s in scopes):
        return None
    packages, kept = set(), defaultdict(set)
    for s in scopes:
        packages |= set(s.get("packages") or [])
        for f, text in (s.get("kept") or {}).items():
            kept[f] |= _expand(text)
    out = {"packages": sorted(packages), "kept": {f: line_ranges(v) for f, v in sorted(kept.items())}}
    fields = merge_fields([s.get("fields") for s in scopes])
    if fields:
        out["fields"] = fields
    consts = [s.get("const") for s in scopes]
    if all(consts):
        bits: dict[str, set[int]] = {}
        ones: dict[str, set[int]] = defaultdict(set)
        for c in consts:
            mine = {n: _expand(t) for n, t in (c.get("bits") or {}).items()}
            for n, t in (c.get("ones") or {}).items():
                ones[n] |= _expand(t)
            for n in c.get("nets") or []:
                cur = mine.get(n, set())
                bits[n] = cur if n not in bits else bits[n] & cur
        out["const"] = {"nets": sorted(bits), "bits": {n: line_ranges(v) for n, v in sorted(bits.items()) if v},
                        "ones": {n: line_ranges(v & bits.get(n, set())) for n, v in sorted(ones.items())
                                 if v & bits.get(n, set())}}
    return out


BRANCH_KINDS = ("if", "elsif", "else", "case")


def block_key(kv: dict, name: str, line: int) -> tuple | None:
    """(instance relative to the DUT top, file, line, column, kind) of a block point of the DUT that is an IF
    branch or a case item (nnc/unrbranch.py), else None."""
    h = kv.get("h", "")
    if kv.get("o") not in BRANCH_KINDS or not (h == DUT_HIER or h.startswith(DUT_HIER + ".")):
        return None
    try:
        col = int(kv.get("n", 0) or 0)
    except ValueError:
        col = 0
    return (h[len(DUT_HIER):].lstrip("."), name, line, col, kv["o"])


def expr_key(kv: dict, name: str, line: int) -> tuple | None:
    """(instance relative to the DUT top, file, line, column, term combination) of an expression point of the
    DUT (nnc/unrexpr.py), else None."""
    h = kv.get("h", "")
    if not kv.get("o") or not (h == DUT_HIER or h.startswith(DUT_HIER + ".")):
        return None
    try:
        col = int(kv.get("n", 0) or 0)
    except ValueError:
        col = 0
    return (h[len(DUT_HIER):].lstrip("."), name, line, col, kv["o"])


def toggle_bit(kv: dict, fields: dict | None = None) -> tuple[str, int] | None:
    """(signal relative to the DUT top as in the flattened netlist, bit index) of a toggle point, or None
    (outside the DUT, or an unpacked array element). With `fields` (struct_fields), a struct field point
    ("tl_i.a_address[3]") is the bit of the packed net that holds it ("tl_i", lsb + 3)."""
    h = kv.get("h", "")
    if not (h == DUT_HIER or h.startswith(DUT_HIER + ".")):
        return None
    m = _TOGGLE.match(kv.get("o", ""))
    if not m:
        return None
    rel = h[len(DUT_HIER):].lstrip(".")
    sig, idx = (f"{rel}.{m['sig']}" if rel else m["sig"]), int(m["idx"] or 0)
    f = (fields or {}).get(sig)
    if f:
        base, lsb, right, desc = f
        return base, lsb + (idx - right if desc else right - idx)
    return sig, idx


def _const_bit(kv: dict, const: dict[str, set[int]], fields: dict | None = None) -> tuple[str, int] | None:
    """(signal, index) when this toggle point is a bit that the scope proves constant, else None."""
    bit = toggle_bit(kv, fields)
    return bit if bit and bit[1] in const.get(bit[0], ()) else None


def _proven_disagreeing(path: Path, rtl: set[str], proven: dict[str, set[int]],
                        fields: dict | None = None) -> set[str]:
    """Signals with a recorded 1->0 toggle on a bit that formal proves constant after the first reset. A
    0->1 is the start of a constant 1 (the simulator's variables start at 0); a 1->0 contradicts the proof
    (or comes from random initial values), so none of the signal's proven bits is left out."""
    bad: set[str] = set()
    for kv, _name, metric, _line, _span, count in _records(path, rtl):
        if metric == "toggle" and count > 0 and kv.get("o", "").endswith(":1->0"):
            bit = _const_bit(kv, proven, fields)
            if bit:
                bad.add(bit[0])
    return bad


def _init_rise(kv: dict, bit: tuple[str, int], ones: dict[str, set[int]]) -> bool:
    """The 0->1 point of a constant-1 bit: Verilator's start at 0, not a toggle of the design."""
    return kv.get("o", "").endswith(":0->1") and bit[1] in ones.get(bit[0], ())


def _disagreeing(path: Path, rtl: set[str], const: dict, ones: dict, fields: dict | None = None) -> set[str]:
    """Signals for which the simulator recorded a toggle on a bit the scope proves constant (other than
    the start of a constant 1). The simulator and the netlist disagree on them, so none of their bits is
    left out."""
    bad: set[str] = set()
    for kv, _name, metric, _line, _span, count in _records(path, rtl):
        if metric == "toggle" and count > 0:
            bit = _const_bit(kv, const, fields)
            if bit and not _init_rise(kv, bit, ones):
                bad.add(bit[0])
    return bad


_RANGE = re.compile(r"\s*(-?\d+)(?:-(-?\d+))?\s*")


def _expand(text: str) -> set[int]:
    """Inverse of line_ranges. Bit indices may be negative (`[W-1:0]` with W = 0 is `[-1:0]`): "-1-0",
    "-3--1"."""
    out: set[int] = set()
    for part in filter(None, str(text).split(",")):
        m = _RANGE.fullmatch(part)
        if not m:
            raise ValueError(f"not a range list: {text!r}")
        a = int(m.group(1))
        out.update(range(a, int(m.group(2) or a) + 1))
    return out


def parse_dat(path: Path, rtl_names: list[str], scope: dict | None = None,
              drop_roots: set[str] | None = None) -> dict:
    """{'metrics': {metric: {hit, total, percent, files}}, 'uncovered': [{metric, file, line, what}]}.
    With a `scope` (scope_from_tree), points outside the elaborated design are left out of every count:
    'scope' then gives, per metric, the points left out, and 'out_of_scope_lines' the (file, line) pairs
    whose every block point was left out (for the lcov line metric). A left-out point that was executed
    would contradict the scope: it is counted, and 'scope_conflicts' says how many. `drop_roots`: instance
    paths whose subtrees are left out as well ('dropped' counts them, 'drop_lines' are their lines)."""
    rtl = set(rtl_names)
    stats: dict[str, dict] = {}
    uncovered: list[dict] = []
    if not path.is_file():
        return {"metrics": {}, "uncovered": []}
    pkgs = set((scope or {}).get("packages") or [])
    kept = {f: _expand(t) for f, t in ((scope or {}).get("kept") or {}).items()}
    const = {n: _expand(t) for n, t in (((scope or {}).get("const") or {}).get("bits") or {}).items()}
    ones = {n: _expand(t) for n, t in (((scope or {}).get("const") or {}).get("ones") or {}).items()}
    nets = ((scope or {}).get("const") or {}).get("nets") or []
    fields = (scope or {}).get("fields") or {}
    if const:
        names = star_signals(path, rtl, fields)
        const, ones = with_stars(const, nets, names), with_stars(ones, nets, names)
    disagree = _disagreeing(path, rtl, const, ones, fields) if const else set()
    for n in disagree:
        const.pop(n, None)
    # Bits that formal proves constant after the first reset (nnc/unr.py, work/unr.json)
    proven = {n: _expand(t) for n, t in ((scope or {}).get("proven") or {}).items()}
    proven_disagree = _proven_disagreeing(path, rtl, proven, fields) if proven else set()
    for n in proven_disagree:
        proven.pop(n, None)
    proven_left = 0
    # branches that formal proves are never executed after the first reset (nnc/unrbranch.py)
    pblocks = {tuple(k) for k in (scope or {}).get("proven_blocks") or []}
    blocks_left, blocks_hit = 0, 0
    # term combinations that formal proves never hold after the first reset (nnc/unrexpr.py)
    pexprs = {tuple(k) for k in (scope or {}).get("proven_exprs") or []}
    exprs_left, exprs_hit = 0, 0
    left_out: dict[str, int] = defaultdict(int)
    dropped: dict[str, int] = defaultdict(int)
    conflicts = 0
    out_lines: set[tuple[str, int]] = set()
    in_lines: set[tuple[str, int]] = set()
    drop_lines: set[tuple[str, int]] = set()
    roots = drop_roots or set()
    for kv, name, metric, line, span, count in _records(path, rtl):
        if roots:
            h = kv.get("h", "")
            if h in roots or any(h.startswith(r + ".") for r in roots):
                dropped[metric] += 1
                if metric == "block":
                    drop_lines.update((name, n) for n in span)
                continue
        if pblocks and metric == "block" and block_key(kv, name, line) in pblocks:
            if count == 0:
                left_out[metric] += 1
                blocks_left += 1
                out_lines.update((name, n) for n in span)
                continue
            blocks_hit += 1           # executed although proven unreachable: counted, and reported
        if pexprs and metric == "expression" and expr_key(kv, name, line) in pexprs:
            if count == 0:
                left_out[metric] += 1
                exprs_left += 1
                continue
            exprs_hit += 1
        bit =_const_bit(kv, const, fields) if scope and metric == "toggle" and const else None
        if not bit and proven and metric == "toggle" and _const_bit(kv, proven, fields):
            # never toggled, or the 0->1 start of a constant 1 (a 1->0 put the signal back above)
            if count == 0 or kv.get("o", "").endswith(":0->1"):
                left_out[metric] += 1
                proven_left += 1
                continue
        outside = scope and ((kv.get("h") in pkgs and line not in kept.get(name, ())) or bit)
        if outside:
            if count == 0 or (bit and _init_rise(kv, bit, ones)):
                left_out[metric] += 1
                if metric == "block":
                    out_lines.update((name, n) for n in span)
                continue
            conflicts += 1
        if metric == "block":
            in_lines.update((name, n) for n in span)
        m = stats.setdefault(metric, {"hit": 0, "total": 0, "files": defaultdict(lambda: [0, 0])})
        m["total"] += 1
        m["files"][name][1] += 1
        if count > 0:
            m["hit"] += 1
            m["files"][name][0] += 1
        else:
            uncovered.append({"metric": metric, "file": name, "line": line, "what": kv.get("o", "")})
    metrics = {}
    for metric, m in sorted(stats.items()):
        metrics[metric] = {"hit": m["hit"], "total": m["total"],
                           "percent": round(100.0 * m["hit"] / m["total"], 1) if m["total"] else None,
                           "files": {f: {"hit": h, "total": t} for f, (h, t) in sorted(m["files"].items())}}
    uncovered.sort(key=lambda u: (u["metric"], u["file"], u["line"], u["what"]))
    out = {"metrics": metrics, "uncovered": uncovered}
    if scope:
        out["scope"] = {"rule": SCOPE_RULE, "left_out": dict(sorted(left_out.items())),
                        "scope_conflicts": conflicts, "signals_kept_whole": sorted(disagree)}
        if (scope or {}).get("proven") is not None:
            out["scope"]["proven_unreachable"] = {"rule": PROVEN_RULE, "left_out": proven_left,
                                                  "signals_kept_whole": sorted(proven_disagree)}
        if pblocks:
            out["scope"].setdefault("proven_unreachable", {"rule": PROVEN_RULE})
            out["scope"]["proven_unreachable"]["branches_left_out"] = blocks_left
            out["scope"]["proven_unreachable"]["branches_executed"] = blocks_hit
        if pexprs:
            out["scope"].setdefault("proven_unreachable", {"rule": PROVEN_RULE})
            out["scope"]["proven_unreachable"]["expressions_left_out"] = exprs_left
            out["scope"]["proven_unreachable"]["expressions_executed"] = exprs_hit
        out["out_of_scope_lines"] = out_lines - in_lines
    if drop_roots is not None:
        out["dropped"] = dict(sorted(dropped.items()))
        out["drop_lines"] = drop_lines - in_lines
    return out


_MANGLE = re.compile(r"__[A-Za-z]{1,3}[0-9a-f]{6,}$")    # Verilator's parameter suffix: m__Az3f2a1b9c


def module_roots(path: Path, rtl_names: list[str], modules: list[str]) -> set[str]:
    """Instance paths (coverage hierarchy) of the instances of `modules`."""
    mods, roots = set(modules), set()
    if path.is_file() and mods:
        for kv, *_ in _records(path, set(rtl_names)):
            if _MANGLE.sub("", kv.get("page", "").partition("/")[2]) in mods:
                roots.add(kv.get("h", ""))
    return roots


def without_modules(path: Path, rtl_names: list[str], scope: dict | None, modules: list[str]) -> dict | None:
    """Coverage of the design without the subtrees of `modules` (a designer's list of pre-verified
    modules, as OpenTitan's cover.cfg leaves out its pre-verified primitives): every point whose instance
    is an instance of a listed module or lies under one, after the design scope. None when no listed
    module is instantiated. {'metrics', 'dropped': {metric: points}, 'drop_lines', 'instances'}."""
    roots = module_roots(path, rtl_names, modules)
    if not roots:
        return None
    r = parse_dat(path, rtl_names, scope, drop_roots=roots)
    return {"metrics": {m: {k: v[k] for k in ("hit", "total", "percent")} for m, v in r["metrics"].items()},
            "dropped": r["dropped"], "drop_lines": r["drop_lines"], "instances": len(roots),
            "uncovered": r["uncovered"]}


def _records(path: Path, rtl: set[str]):
    """(key/values, file, metric, line, lines of a block point, count) of every DUT point of coverage.dat."""
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw.startswith("C '"):
            continue
        end = raw.rindex("'")
        try:
            count = int(raw[end + 1:].strip())
        except ValueError:
            continue
        kv = {}
        for part in raw[3:end].split("\x01"):
            if "\x02" in part:
                k, v = part.split("\x02", 1)
                kv[k] = v
        name = Path(kv.get("f", "")).name
        metric = PAGES.get(kv.get("page", "").split("/")[0])
        if name not in rtl or metric is None:
            continue
        line = int(kv.get("l", 0) or 0)
        span = _expand(kv["S"]) if metric == "block" and _SPAN.fullmatch(kv.get("S", "")) else {line}
        yield kv, name, metric, line, span, count


def summarize_uncovered(uncovered: list[dict], limit: int = 200) -> list[dict]:
    """Group the uncovered points by file, line and metric (toggle bits of one signal together)."""
    groups: dict[tuple, list[str]] = defaultdict(list)
    for u in uncovered:
        what = u["what"]
        if u["metric"] == "toggle":                       # "sig[3]:0->1" -> "sig"
            what = what.split(":")[0].split("[")[0]
        groups[(u["metric"], u["file"], u["line"], what)].append(u["what"])
    out = [{"metric": k[0], "file": k[1], "line": k[2], "what": k[3], "points": len(v),
            "detail": sorted(set(v))[:8]} for k, v in groups.items()]
    out.sort(key=lambda g: (g["metric"], -g["points"], g["file"], g["line"]))
    kept, per = [], defaultdict(int)
    for g in out:                                  # at most `limit` groups per metric
        per[g["metric"]] += 1
        if per[g["metric"]] <= limit:
            kept.append(g)
    return kept


def elaborated_files(cov: dict) -> set[str] | None:
    """RTL files that the simulator elaborated (they have toggle or line points); None if unknown."""
    m = cov.get("metrics") or {}
    files = set()
    for k in ("toggle", "line", "block"):
        files |= set((m.get(k) or {}).get("files", {}))
    return files or None


def line_ranges(lines) -> str:
    """Sorted line numbers as compact ranges: [3, 4, 5, 9] -> "3-5,9"."""
    out, nums = [], sorted(set(lines))
    i = 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(str(nums[i]) if i == j else f"{nums[i]}-{nums[j]}")
        i = j + 1
    return ",".join(out)


def executed_lines(cov: dict) -> dict[str, set[int]] | None:
    """{file: lines the regression executed (lcov count > 0)}, or None when not recorded. A line absent
    from lcov is not part of the elaborated design: an inactive `ifdef branch or an unselected generate
    branch."""
    raw = cov.get("executed_lines")
    if not isinstance(raw, dict):
        return None
    out: dict[str, set[int]] = {}
    for name, text in raw.items():
        lines = out.setdefault(name, set())
        for part in filter(None, str(text).split(",")):
            a, _, b = part.partition("-")
            lines.update(range(int(a), int(b or a) + 1))
    return out


def uncovered_lines(cov: dict) -> set[tuple[str, int]]:
    return {(u["file"], u["line"]) for u in cov.get("uncovered", []) if u["metric"] == "line"}

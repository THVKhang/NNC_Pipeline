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
    return {"packages": sorted(p for p in packages if p),
            "kept": {f: line_ranges(v) for f, v in sorted(kept.items()) if f}}


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


def _const_bit(kv: dict, const: dict[str, set[int]]) -> tuple[str, int] | None:
    """(signal, index) when this toggle point is a bit that the scope proves constant, else None."""
    h = kv.get("h", "")
    if not (h == DUT_HIER or h.startswith(DUT_HIER + ".")):
        return None
    m = _TOGGLE.match(kv.get("o", ""))
    if not m:
        return None
    rel = h[len(DUT_HIER):].lstrip(".")
    name = f"{rel}.{m['sig']}" if rel else m["sig"]
    idx = int(m["idx"] or 0)
    return (name, idx) if idx in const.get(name, ()) else None


def _init_rise(kv: dict, bit: tuple[str, int], ones: dict[str, set[int]]) -> bool:
    """The 0->1 point of a constant-1 bit: Verilator's start at 0, not a toggle of the design."""
    return kv.get("o", "").endswith(":0->1") and bit[1] in ones.get(bit[0], ())


def _disagreeing(path: Path, rtl: set[str], const: dict, ones: dict) -> set[str]:
    """Signals for which the simulator recorded a toggle on a bit the scope proves constant (other than
    the start of a constant 1). The simulator and the netlist disagree on them, so none of their bits is
    left out."""
    bad: set[str] = set()
    for kv, _name, metric, _line, _span, count in _records(path, rtl):
        if metric == "toggle" and count > 0:
            bit = _const_bit(kv, const)
            if bit and not _init_rise(kv, bit, ones):
                bad.add(bit[0])
    return bad


def _expand(text: str) -> set[int]:
    out: set[int] = set()
    for part in filter(None, str(text).split(",")):
        a, _, b = part.partition("-")
        out.update(range(int(a), int(b or a) + 1))
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
    disagree = _disagreeing(path, rtl, const, ones) if const else set()
    for n in disagree:
        const.pop(n, None)
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
        bit = _const_bit(kv, const) if scope and metric == "toggle" and const else None
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
            "dropped": r["dropped"], "drop_lines": r["drop_lines"], "instances": len(roots)}


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

"""Code coverage of the DUT from Verilator's coverage.dat (no LLM).

Verilator writes one record per coverage point: `C '<key/value pairs>' <count>`, keys separated by
\\x01 and key/value by \\x02 (f = file, l = line, page = v_line/<module>, v_toggle/..., v_expr/...,
o = comment, e.g. the signal and the transition `sig[3]:0->1`). Only points in the DUT RTL files count:
checkers and the testbench top are excluded from every denominator. Unlike metrics are never merged
into one number.

Metrics: `line` comes from the lcov export (lines, as before), `block` is Verilator's own line/branch
points (one per statement block or branch arm), `toggle` is one point per bit and direction of every
DUT signal, `expression` is one point per term combination of a condition (Verilator --coverage-expr).
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

PAGES = {"v_line": "block", "v_branch": "block", "v_toggle": "toggle", "v_expr": "expression", "v_fsm": "fsm"}


def parse_dat(path: Path, rtl_names: list[str]) -> dict:
    """{'metrics': {metric: {hit, total, percent, files}}, 'uncovered': [{metric, file, line, what}]}."""
    rtl = set(rtl_names)
    stats: dict[str, dict] = {}
    uncovered: list[dict] = []
    if not path.is_file():
        return {"metrics": {}, "uncovered": []}
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
        m = stats.setdefault(metric, {"hit": 0, "total": 0, "files": defaultdict(lambda: [0, 0])})
        m["total"] += 1
        m["files"][name][1] += 1
        if count > 0:
            m["hit"] += 1
            m["files"][name][0] += 1
        else:
            uncovered.append({"metric": metric, "file": name, "line": int(kv.get("l", 0) or 0),
                              "what": kv.get("o", "")})
    metrics = {}
    for metric, m in sorted(stats.items()):
        metrics[metric] = {"hit": m["hit"], "total": m["total"],
                           "percent": round(100.0 * m["hit"] / m["total"], 1) if m["total"] else None,
                           "files": {f: {"hit": h, "total": t} for f, (h, t) in sorted(m["files"].items())}}
    uncovered.sort(key=lambda u: (u["metric"], u["file"], u["line"], u["what"]))
    return {"metrics": metrics, "uncovered": uncovered}


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

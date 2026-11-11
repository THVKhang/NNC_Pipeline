"""Mutation testing (stage 5, code only): can the verification fail?

Mutants are made on a COPY of the RTL (the delivered RTL is never touched) with simple operators on
code lines (comments and declarations excluded). Each mutant runs the full regression on the
simulation host; mutants run in parallel. A mutant is
  killed        a test failed or a checker counted a failure,
  survived      everything passed: a missing check or stimulus (or an equivalent mutant),
  not_compiled  the build failed: it is not counted in the score.
"""
from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from pathlib import Path

from nnc import coverage as coverage_mod
from nnc.agents.backend import AgentTask
from nnc.sim import SIM_SCRIPT, build_inputs, checker_files, param_values, parse_results, rtl_files
from nnc.simhost import SimHost

OPERATORS = [
    ("eq_to_ne", re.compile(r"(?<![=!<>])==(?!=)"), "!="),
    ("ne_to_eq", re.compile(r"!=(?!=)"), "=="),
    ("and_to_or", re.compile(r"&&"), "||"),
    ("or_to_and", re.compile(r"\|\|"), "&&"),
    ("one_to_zero", re.compile(r"1'b1\b"), "1'b0"),
    ("zero_to_one", re.compile(r"1'b0\b"), "1'b1"),
    ("negate_if", re.compile(r"\bif\s*\("), "if (!"),
]
_SKIP_LINE = re.compile(r"^\s*(//|\*|/\*|parameter|localparam|input|output|inout|module|`|import|typedef)")


@dataclass
class Mutant:
    id: str
    file: str
    line: int
    operator: str
    original: str
    mutated: str


def _negate_if(line: str, m: re.Match) -> str | None:
    """if (cond) -> if (!(cond)), with balanced parentheses."""
    start = m.end() - 1
    depth = 0
    for k in range(start, len(line)):
        depth += line[k] == "("
        depth -= line[k] == ")"
        if depth == 0:
            return line[:start] + "(!(" + line[start + 1:k] + "))" + line[k + 1:]
    return None


def candidates(files: list[Path]) -> list[Mutant]:
    out = []
    for f in files:
        in_block = False
        for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            code = line.split("//")[0]
            if "/*" in code:
                in_block = True
            if in_block:
                in_block = "*/" not in code
                continue
            if not code.strip() or _SKIP_LINE.match(code):
                continue
            for name, rx, repl in OPERATORS:
                for m in rx.finditer(code):
                    if name == "negate_if":
                        mutated = _negate_if(line, m)
                        if mutated is None:
                            continue
                    else:
                        mutated = line[:m.start()] + repl + line[m.end():]
                    out.append(Mutant("", f.name, n, name, line.strip(), mutated))
    return out


def select(cands: list[Mutant], count: int, seed: int = 1) -> list[Mutant]:
    """Spread the sample over files and operators, deterministically."""
    rnd = random.Random(seed)
    pool = cands[:]
    rnd.shuffle(pool)
    pool.sort(key=lambda m: (m.operator, m.file))
    buckets: dict[tuple, list[Mutant]] = {}
    for m in pool:
        buckets.setdefault((m.file, m.operator), []).append(m)
    chosen = []
    keys = list(buckets)
    rnd.shuffle(keys)
    while len(chosen) < count and any(buckets.values()):
        for k in keys:
            if buckets[k] and len(chosen) < count:
                chosen.append(buckets[k].pop())
    for i, m in enumerate(chosen, 1):
        m.id = f"M{i:02d}"
    return chosen


def run(host: SimHost, contract: dict, rtl_dir: Path, sva_dir: Path, test_file: Path | list[Path], *, count: int = 12,
        seed: int = 1, parallel: int = 4, timeout_s: int = 7200, clock_periods: dict | None = None,
        baseline: dict | None = None, opts: dict | None = None) -> dict:
    """Mutants are drawn from lines the baseline regression executed: a line never reached (uncovered),
    or a file this configuration does not elaborate (for example a memory macro of another branch),
    would only give survivors that measure coverage, not checking."""
    rtl = rtl_files(rtl_dir)
    pool = candidates(rtl)
    excluded = {"files": [], "lines": 0}
    if baseline and (baseline.get("coverage") or {}).get("metrics"):
        cov = baseline["coverage"]
        elab = coverage_mod.elaborated_files(cov)
        dead = coverage_mod.uncovered_lines(cov)
        ran = coverage_mod.executed_lines(cov)
        if elab is not None:
            excluded["files"] = sorted({m.file for m in pool if m.file not in elab})
        before = len(pool)
        pool = [m for m in pool if m.file not in excluded["files"] and (m.file, m.line) not in dead
                and (ran is None or m.line in ran.get(m.file, ()))]
        excluded["lines"] = before - len(pool)
    mutants = select(pool, count, seed)
    sva = checker_files(sva_dir)
    pv = param_values(contract)
    base = build_inputs(contract, rtl, sva, test_file, pv, coverage=False, clock_periods=clock_periods, opts=opts)
    files: dict[str, object] = {}
    for m in mutants:
        for rel, src in base.items():
            files[f"{m.id}/{rel}"] = src
        text = (rtl_dir / m.file).read_text(encoding="utf-8", errors="replace").splitlines()
        text[m.line - 1] = m.mutated
        files[f"{m.id}/rtl/{m.file}"] = "\n".join(text) + "\n"
    one = SIM_SCRIPT.format(seed=seed, jobs=max(1, 12 // max(1, parallel))).replace("\n", "; ")
    script = (f"ls -d M* | xargs -P {parallel} -I{{}} bash -c 'cd {{}} && {one}'\n")
    res = host.run(files, script, ["M*/sim.log", "M*/results.xml"], timeout_s=timeout_s, tag="mutate")
    base_fail = baseline_failures(baseline)
    results = []
    for m in mutants:
        out = res.out_dir / m.id
        parsed = parse_results(out, [f.name for f in rtl]) if out.is_dir() else {"built": False, "tests": [], "assertions": {}}
        results.append({**m.__dict__, **classify(parsed, base_fail)})
    counted = [r for r in results if r["status"] != "not_compiled"]
    killed = sum(r["status"] == "killed" for r in counted)
    return {"mutants": results, "candidates": len(pool), "count": len(results),
            "killed": killed, "survived": sum(r["status"] == "survived" for r in counted),
            "not_compiled": len(results) - len(counted),
            "score": round(100.0 * killed / len(counted), 1) if counted else None, "seed": seed,
            "excluded_uncovered": excluded, "baseline_failing": {k: sorted(v) for k, v in base_fail.items()}}


def baseline_failures(baseline: dict | None) -> dict[str, set]:
    """Tests and checks that already fail on the unmutated RTL."""
    baseline = baseline or {}
    return {"tests": {t["name"] for t in baseline.get("tests", []) if t.get("status") == "fail"},
            "checks": {c for c, v in (baseline.get("assertions") or {}).items() if (v or {}).get("fails", 0) > 0}}


def classify(parsed: dict, base_fail: dict[str, set]) -> dict:
    """A mutant is killed only by a test or check that PASSES on the unmutated RTL: a failure that is
    already there in the baseline says nothing about the mutant (otherwise a failing regression would
    'kill' every mutant and report 100 %)."""
    failed_tests = [t["name"] for t in parsed["tests"] if t["status"] == "fail" and t["name"] not in base_fail["tests"]]
    failed_checks = [c for c, v in parsed.get("assertions", {}).items()
                     if v["fails"] > 0 and c not in base_fail["checks"]]
    status = ("not_compiled" if not parsed["built"] else "killed" if failed_tests or failed_checks else "survived")
    return {"status": status, "killed_by_tests": failed_tests, "killed_by_checks": failed_checks}


# ------------------------------------------------------------------- per-requirement attribution
ATTR_SYSTEM = (
    "You are a design-verification engineer. You read RTL and requirements to say which requirements a code "
    "line implements. You change nothing. Return the answer in the required JSON structure."
)
ATTR_SCHEMA = {
    "type": "object", "required": ["mutants"], "additionalProperties": False,
    "properties": {"mutants": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["id", "rules", "equivalent", "reason"],
        "properties": {"id": {"type": "string"}, "rules": {"type": "array", "items": {"type": "string"}},
                       "equivalent": {"type": "boolean"}, "reason": {"type": "string"}}}}},
}


def attribute(mutation: dict, files: dict[str, Path], rule_ids: set[str], backend, log_dir: Path, *,
              model: str = "sonnet") -> dict:
    """Agent A12 (sandbox, reads RTL): for every mutant, the rule IDs whose observable behaviour the
    mutated line implements, and whether the mutant is likely equivalent (no observable change for any
    legal stimulus). Code keeps only known rule IDs. The designer reviews equivalence claims; they never
    change the score."""
    listing = [{"id": m["id"], "file": f"rtl/{m['file']}", "line": m["line"], "original": m["original"].strip(),
                "mutated": m["mutated"].strip(), "status": m["status"]} for m in mutation["mutants"]
               if m["status"] != "not_compiled"]
    if not listing:
        return {"mutants": {}, "unknown_ids": []}
    instructions = (
        "FILES\n" + "\n".join(f"  {n}" for n in sorted(files)) + "\n\nMUTANTS (one changed RTL line each)\n" +
        json.dumps(listing, indent=1) +
        "\n\nFor each mutant: read the RTL around the line and rules.json (and contract.json for the checks). Give the "
        "IDs of the rules whose required observable behaviour depends on this line (the requirements the mutant "
        "would break), most specific first, at most 5; an empty list if none. Set equivalent=true only if no legal "
        "stimulus of the specification can make the mutant behave differently at the ports, and explain why in "
        "`reason` (for a non-equivalent mutant, say in one sentence what would change).")
    res = backend.run(AgentTask("A12_mutation_map", instructions, ATTR_SCHEMA, inputs=dict(files),
                                tools=("Read", "Grep", "Glob"), system_prompt=ATTR_SYSTEM, model=model,
                                max_turns=40), log_dir)
    out, unknown = {}, set()
    for m in res.output["mutants"]:
        good = [r for r in m["rules"] if r in rule_ids]
        unknown |= set(m["rules"]) - rule_ids
        out[m["id"]] = {"rules": good, "equivalent": m["equivalent"], "reason": m["reason"]}
    return {"mutants": out, "unknown_ids": sorted(unknown), "model": model,
            "cost_usd": res.cost_usd if hasattr(res, "cost_usd") else None}


def rule_scores(mutation: dict, threshold: float) -> dict[str, dict]:
    """Per rule: compiled mutants attributed to it, killed, score, and whether it meets the threshold."""
    attr = (mutation.get("attribution") or {}).get("mutants", {})
    per: dict[str, dict] = {}
    for m in mutation["mutants"]:
        if m["status"] == "not_compiled":
            continue
        a = attr.get(m["id"], {})
        for r in a.get("rules", []):
            s = per.setdefault(r, {"relevant": 0, "killed": 0, "survived": [], "claimed_equivalent": []})
            s["relevant"] += 1
            s["killed"] += m["status"] == "killed"
            if m["status"] == "survived":
                s["survived"].append(m["id"])
                if a.get("equivalent"):
                    s["claimed_equivalent"].append(m["id"])
    for s in per.values():
        s["score"] = round(100.0 * s["killed"] / s["relevant"], 1)
        s["meets_threshold"] = s["score"] >= threshold
    return dict(sorted(per.items()))

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


def _executes(cov: dict | None, m: Mutant) -> bool | None:
    """Whether the run with coverage `cov` executed the mutant's line (None: no coverage recorded)."""
    if not cov or not cov.get("metrics"):
        return None
    elab = coverage_mod.elaborated_files(cov)
    if elab is not None and m.file not in elab:
        return False
    if (m.file, m.line) in coverage_mod.uncovered_lines(cov):
        return False
    ran = coverage_mod.executed_lines(cov)
    return ran is None or m.line in ran.get(m.file, ())


def run(host: SimHost, contract: dict, rtl_dir: Path, sva_dir: Path, test_file: Path | list[Path], *, count: int = 12,
        seed: int = 1, parallel: int = 4, timeout_s: int = 7200, clock_periods: dict | None = None,
        baseline: dict | None = None, opts: dict | None = None, params: dict | None = None,
        sim_seed: int | None = None, runs: list[dict] | None = None) -> dict:
    """Mutants are drawn from lines the baseline regression executed: a line never reached (uncovered),
    or a file this configuration does not elaborate (for example a memory macro of another branch),
    would only give survivors that measure coverage, not checking.

    `runs` (a run set): [{label, params (overrides), opts, clock_periods, seed, baseline}], primary first.
    A mutant is then drawn from the lines executed by ANY run, and simulated in the first run that
    executed its line, against that run's baseline. Without `runs`, one run is built from `params`,
    `opts`, `clock_periods`, `sim_seed` (default `seed`) and `baseline`. `seed` picks the mutants."""
    if not runs:
        runs = [{"label": "", "params": params or {}, "opts": opts, "clock_periods": clock_periods,
                 "seed": seed if sim_seed is None else sim_seed, "baseline": baseline}]
    rtl = rtl_files(rtl_dir)
    pool = candidates(rtl)
    total = len(pool)
    where: dict[int, dict] = {}
    known = False
    for m in pool:
        for r in runs:
            ex = _executes((r.get("baseline") or {}).get("coverage"), m)
            known = known or ex is not None
            if ex is None or ex:
                where[id(m)] = r
                break
    pool = [m for m in pool if id(m) in where]
    excluded = {"files": sorted({m.file for m in candidates(rtl)} - {m.file for m in pool}) if known else [],
                "lines": total - len(pool)}
    mutants = select(pool, count, seed)
    sva = checker_files(sva_dir)
    rtl_text = {f.name: f.read_text(encoding="utf-8", errors="replace").splitlines() for f in rtl}
    names = [f.name for f in rtl]
    bases: dict[str, dict] = {}

    def simulate(jobs: list[tuple[str, Mutant, dict]], tag: str) -> dict[str, dict]:
        """Simulate each (folder, mutant, run) in parallel; parsed results per folder."""
        files: dict[str, object] = {}
        for key, m, r in jobs:
            if r["label"] not in bases:
                bases[r["label"]] = build_inputs(contract, rtl, sva, test_file, param_values(contract, r.get("params")),
                                                 coverage=False, clock_periods=r.get("clock_periods"), opts=r.get("opts"))
            for rel, src in bases[r["label"]].items():
                files[f"{key}/{rel}"] = src
            text = list(rtl_text[m.file])
            text[m.line - 1] = m.mutated
            files[f"{key}/rtl/{m.file}"] = "\n".join(text) + "\n"
            files[f"{key}/seed.txt"] = f"{r['seed']}\n"
        one = SIM_SCRIPT.format(seed="$(cat seed.txt)", jobs=max(1, 12 // max(1, parallel))).replace("\n", "; ")
        script = f"ls -d M* | xargs -P {parallel} -I{{}} bash -c 'cd {{}} && {one}'\n"
        res = host.run(files, script, ["M*/sim.log", "M*/results.xml"], timeout_s=timeout_s, tag=tag)
        return {key: parse_results(res.out_dir / key, names) if (res.out_dir / key).is_dir()
                else {"built": False, "tests": [], "assertions": {}} for key, _, _ in jobs}

    first = simulate([(m.id, m, where[id(m)]) for m in mutants], "mutate")
    results = []
    for m in mutants:
        r = where[id(m)]
        rec = {**m.__dict__, **classify(first[m.id], baseline_failures(r.get("baseline")))}
        if r["label"]:
            rec["run"] = r["label"]
        results.append(rec)
    # Run set: a survivor gets a second chance in every OTHER configuration (first seed) that executed
    # its line: the run set as a whole is the verification, and a line can be reached in one
    # configuration while the changed term only matters in another (for example a HS_TYPE branch).
    retry: list[tuple[str, Mutant, dict]] = []
    if len(runs) > 1:
        for m, rec in zip(mutants, results):
            if rec["status"] != "survived":
                continue
            seen = {_config(where[id(m)]["label"])}
            for r in runs:
                c = _config(r["label"])
                if c in seen or _executes((r.get("baseline") or {}).get("coverage"), m) is False:
                    continue
                seen.add(c)
                retry.append((f"{m.id}_{len(retry):03d}", m, r))
    if retry:
        again = simulate(retry, "mutate_more")
        by_id = {rec["id"]: rec for rec in results}
        for key, m, r in retry:
            rec = by_id[m.id]
            rec.setdefault("also_run", []).append(r["label"])
            c = classify(again[key], baseline_failures(r.get("baseline")))
            if rec["status"] == "survived" and c["status"] == "killed":
                rec.update(c)
                rec["run"] = r["label"]
    counted = [r for r in results if r["status"] != "not_compiled"]
    killed = sum(r["status"] == "killed" for r in counted)
    out = {"mutants": results, "candidates": len(pool), "count": len(results),
           "killed": killed, "survived": sum(r["status"] == "survived" for r in counted),
           "not_compiled": len(results) - len(counted),
           "score": round(100.0 * killed / len(counted), 1) if counted else None, "seed": seed,
           "excluded_uncovered": excluded,
           "baseline_failing": {k: sorted(v) for k, v in baseline_failures(runs[0].get("baseline")).items()}}
    if runs[0]["label"]:
        used = sorted({r.get("run") for r in results if r.get("run")})
        out["runs"] = {"available": [r["label"] for r in runs], "used": used, "second_chance_sims": len(retry)}
    return out


def _config(label: str) -> str:
    """Configuration name of a run label "<config>.s<seed>"."""
    return label.rsplit(".s", 1)[0]


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
                "mutated": m["mutated"].strip(), "status": m["status"],
                **({"run": m["run"]} if m.get("run") else {})} for m in mutation["mutants"]
               if m["status"] != "not_compiled"]
    if not listing:
        return {"mutants": {}, "unknown_ids": []}
    instructions = (
        "FILES\n" + "\n".join(f"  {n}" for n in sorted(files)) + "\n\nMUTANTS (one changed RTL line each)\n" +
        json.dumps(listing, indent=1) +
        "\n\nFor each mutant: read the RTL around the line and rules.json (and contract.json for the checks). Give the "
        "IDs of the rules whose required observable behaviour depends on this line (the requirements the mutant "
        "would break), most specific first, at most 5; an empty list if none. Set equivalent=true only if no legal "
        "stimulus of the specification can make the mutant behave differently at the ports (in the configuration "
        "of its `run`, when given: see run_set.json), and explain why in "
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

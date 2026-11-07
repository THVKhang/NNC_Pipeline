"""Mutation testing (stage 5, code only): can the verification fail?

Mutants are made on a COPY of the RTL (the delivered RTL is never touched) with simple operators on
code lines (comments and declarations excluded). Each mutant runs the full regression on the
simulation host; mutants run in parallel. A mutant is
  killed        a test failed or a checker counted a failure,
  survived      everything passed: a missing check or stimulus (or an equivalent mutant),
  not_compiled  the build failed: it is not counted in the score.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from pathlib import Path

from nnc.sim import SIM_SCRIPT, build_inputs, param_values, parse_results, rtl_files
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


def run(host: SimHost, contract: dict, rtl_dir: Path, sva_dir: Path, test_file: Path, *, count: int = 12,
        seed: int = 1, parallel: int = 4, timeout_s: int = 7200) -> dict:
    rtl = rtl_files(rtl_dir)
    mutants = select(candidates(rtl), count, seed)
    sva = sorted(sva_dir.glob("nnc_chk_*.sv"))
    pv = param_values(contract)
    base = build_inputs(contract, rtl, sva, test_file, pv, coverage=False)
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
    results = []
    for m in mutants:
        out = res.out_dir / m.id
        parsed = parse_results(out, [f.name for f in rtl]) if out.is_dir() else {"built": False, "tests": [], "assertions": {}}
        failed_tests = [t["name"] for t in parsed["tests"] if t["status"] == "fail"]
        failed_checks = [c for c, v in parsed.get("assertions", {}).items() if v["fails"] > 0]
        status = ("not_compiled" if not parsed["built"] else "killed" if failed_tests or failed_checks else "survived")
        results.append({**m.__dict__, "status": status, "killed_by_tests": failed_tests,
                        "killed_by_checks": failed_checks})
    counted = [r for r in results if r["status"] != "not_compiled"]
    killed = sum(r["status"] == "killed" for r in counted)
    return {"mutants": results, "candidates": len(candidates(rtl)), "count": len(results),
            "killed": killed, "survived": sum(r["status"] == "survived" for r in counted),
            "not_compiled": len(results) - len(counted),
            "score": round(100.0 * killed / len(counted), 1) if counted else None, "seed": seed}

"""Coverage closure (stage `cover`, agents A10 and A11): reach a code-coverage target with tests
derived from the specification, never from the RTL.

The designer chooses a metric (line, block, toggle, expression) and a target after seeing the
measured baseline (`nnc cover <design>` without --target shows it). Each round:

1. A10 (gap analyst, sandbox with the RTL, Read/Grep/Glob only) maps the uncovered points to legal
   stimulus in specification terms: which contract checks and rules the stimulus exercises, described
   with top-level ports and specification words only. It may also claim that points are unreachable by
   legal stimulus, citing rules; a claim is reported for the designer and never removes a point.
2. Code drops every scenario that mentions an RTL-internal name (an identifier of the RTL that is not
   in the specification or the contract): the test writer must not learn the implementation.
3. A11 (test writer, no tools, no RTL) writes a new module `verif/tests/test_<design>_cov<r>.py`. Its
   tests drive the scenarios and assert the expected behaviour of the named contract checks.
4. The regression runs with every module; coverage is measured again.

The loop stops when the target is reached, after `rounds` rounds, after two rounds without gain, or at
the first functional failure (a failure is a verification finding: it goes to triage, the loop does not
"fix" it). New modules change verif/, so Gate 3 must be approved again before the report.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from nnc import gen_tests
from nnc.agents.backend import AgentTask
from nnc.agents.runtime import Usage

PROMPT_VERSION = "closure-v1"
METRICS = ("line", "block", "toggle", "expression", "functional")

ANALYST_SYSTEM = (
    "You are a senior verification engineer closing code coverage. You read the RTL only to understand why "
    "points are not reached; you describe stimulus in the terms of the specification and the top-level ports, "
    "never with internal names, line numbers or values read from the RTL. Return the required JSON structure."
)
ANALYST_SCHEMA = {
    "type": "object", "required": ["scenarios", "unreachable"], "additionalProperties": False,
    "properties": {
        "scenarios": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["id", "points", "checks", "rules", "stimulus"],
            "properties": {"id": {"type": "string", "pattern": "^COV-[0-9]{3}$"},
                           "points": {"type": "array", "items": {"type": "integer"}},
                           "checks": {"type": "array", "items": {"type": "string", "pattern": "^CHK-[0-9]{3}$"}},
                           "rules": {"type": "array", "items": {"type": "string"}},
                           "stimulus": {"type": "string", "minLength": 20}}}},
        "unreachable": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["points", "rules", "reason"],
            "properties": {"points": {"type": "array", "items": {"type": "integer"}},
                           "rules": {"type": "array", "items": {"type": "string"}},
                           "reason": {"type": "string"}}}},
    },
}
WRITER_SYSTEM = gen_tests.SYSTEM_PROMPT


def rtl_private_names(rtl: list[Path], public_text: str) -> set[str]:
    """Identifiers of the RTL (with an underscore, so signal-like) absent from the public documents."""
    names = set()
    for f in rtl:
        text = re.sub(r"//[^\n]*|/\*.*?\*/", " ", f.read_text(encoding="utf-8", errors="replace"), flags=re.S)
        names |= set(re.findall(r"\b[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+\b", text))
    public = set(re.findall(r"\b[A-Za-z][A-Za-z0-9_]*\b", public_text))
    return {n for n in names if n not in public}


def leaks(text: str, private: set[str]) -> list[str]:
    return sorted({w for w in re.findall(r"\b[A-Za-z][A-Za-z0-9_]*\b", text) if w in private})


def baseline(results: dict, metric: str) -> dict | None:
    return ((results.get("coverage") or {}).get("metrics") or {}).get(metric)


def functional_failures(results: dict) -> list[str]:
    bad = [t["name"] for t in results.get("tests", []) if t["status"] == "fail"]
    bad += [c for c, v in results.get("assertions", {}).items() if v["fails"] > 0]
    return bad


def _points(results: dict, metric: str, limit: int = 120) -> list[dict]:
    pts = [u for u in (results.get("coverage") or {}).get("uncovered", []) if u["metric"] == metric]
    return [{"n": i, **{k: u[k] for k in ("file", "line", "what", "points", "detail")}} for i, u in enumerate(pts[:limit])]


def analyse(results: dict, metric: str, files: dict[str, Path], backend, log_dir: Path, round_no: int,
            model: str, previous: list[dict]) -> dict:
    pts = _points(results, metric)
    prev = "\n".join(f"  {s['id']}: {s['stimulus'][:300]}" for s in previous) or "  (none)"
    functional = metric == "functional"
    where = ("FUNCTIONAL COVER POINTS NOT HIT (n = point number; detail = title and condition from the specification)"
             if functional else f"UNCOVERED {metric.upper()} POINTS OF THE DUT (n = point number; file:line in rtl/)")
    first = ("TASK: read each cover point's condition" if functional else "TASK: read the RTL around each point")
    instructions = (
        "FILES IN THIS DIRECTORY\n" + "\n".join(f"  {n}" for n in sorted(files)) +
        f"\n\n{where}\n" + json.dumps(pts, indent=1) +
        "\n\nSCENARIOS OF EARLIER ROUNDS (already turned into tests; do not repeat them)\n" + prev +
        f"\n\n{first}, the contract (contract.json: checks with their behaviour) and the "
        "rules (rules.json). For each group of points that legal stimulus can reach, write one scenario: the "
        "contract checks whose expected behaviour applies (`checks`, at least one), the rule IDs, and `stimulus`: "
        "what to drive on the top-level ports, in which order and state, in the words of the specification. "
        "FORBIDDEN in `stimulus`: internal signal, register, state or module names, RTL line numbers, and any "
        "expected value taken from the RTL (the test writer derives expected values from the contract). If "
        "points cannot be reached by legal stimulus (a constant output required by a rule, an illegal "
        "configuration, a branch for inputs the specification forbids), list them in `unreachable` with the "
        "rules that make them so. Number scenarios COV-" + f"{round_no:01d}" + "01, COV-" + f"{round_no:01d}" +
        "02, ... At most 12 scenarios.")
    task = AgentTask(f"A10_cover_r{round_no}", instructions, ANALYST_SCHEMA, inputs=dict(files),
                     tools=("Read", "Grep", "Glob"), system_prompt=ANALYST_SYSTEM, model=model, max_turns=60)
    res = backend.run(task, log_dir)
    return {"output": res.output, "result": res, "points": pts}


def validate_module(code: str, contract: dict, scenarios: list[dict]) -> list[str]:
    problems = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"syntax error line {e.lineno}: {e.msg}"]
    tests = [n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and any(
        "cocotb.test" in ast.unparse(d) for d in n.decorator_list)]
    ids = {c["id"] for c in contract["checks"]}
    for t in tests:
        doc = ast.get_docstring(t) or ""
        if not t.name.startswith("test_cov_"):
            problems.append(f"{t.name}: closure test names start with test_cov_")
        if not re.search(r"COV-\d{3}", doc) or not (set(re.findall(r"CHK-\d{3}", doc)) & ids):
            problems.append(f"{t.name}: the docstring must start with its COV ID and name the contract checks")
        if not any(isinstance(n, ast.Assert) for n in ast.walk(t)) and "assert" not in ast.unparse(t):
            problems.append(f"{t.name}: a closure test must check expected behaviour (assert)")
    covered = " ".join(ast.get_docstring(t) or "" for t in tests)
    for s in scenarios:
        if s["id"] not in covered:
            problems.append(f"no test implements {s['id']}")
    if re.search(r"\bdut\.u_\w+", code) or "._sub_handles" in code:
        problems.append("hierarchical access into the DUT is not allowed")
    if re.search(r"^\s*from\s+test_\w+\s+import\s+\*", code, re.M):
        problems.append("do not star-import a test module (its tests would run twice); use `import test_x as base`")
    if "nnc_cocotb" not in code:
        problems.append("use the helper library: from nnc_cocotb import *")
    return problems


def write_tests(contract: dict, rules_doc: dict, scenarios: list[dict], base_module: Path, backend, log_dir: Path,
                round_no: int, model: str, usage: Usage, attempts: int = 2,
                run_opts: dict | None = None) -> tuple[str, list[str]]:
    rules_by_id = {r["id"]: r for r in rules_doc["rules"]}
    checks = {c["id"]: c for c in contract["checks"]}
    blocks = []
    for s in scenarios:
        chk = "\n".join(f"    [{c}] {checks[c]['title']}: {checks[c]['behavior']}"
                        + (f"\n      EXPECTED: {checks[c].get('expected')}" if checks[c].get("expected") else "")
                        for c in s["checks"] if c in checks)
        quotes = "\n".join(f"      {r}: {rules_by_id[r]['quote'][:400]}" for r in s["rules"] if r in rules_by_id)
        blocks.append(f"[{s['id']}] STIMULUS: {s['stimulus']}\n  CHECKS (the oracle):\n{chk}\n  SOURCES:\n{quotes}")
    base_code = base_module.read_text(encoding="utf-8")
    prompt = (gen_tests.build_prompt(contract, rules_doc, run_opts).split("TEST CHECKS TO IMPLEMENT")[0] +
              f"COVERAGE-CLOSURE SCENARIOS ({len(scenarios)}): write one @cocotb.test() per scenario, named "
              "test_cov_<nnn>_<short_name>, docstring starting with the COV ID and the CHK IDs it checks. Drive the "
              "stimulus and assert the expected behaviour of the named checks, computed from the contract and the "
              "quotes only. Every test is self-checking.\n" + "\n".join(blocks) +
              f"\n\nBASE TEST MODULE ({base_module.stem}.py): you may reuse its classes and functions with "
              f"`import {base_module.stem} as base` (never a star import).\n```python\n{base_code}\n```\n\n" +
              gen_tests.HELPERS_DOC + "\n" + gen_tests.RULES_TEXT.split("- Add one more test named")[0] +
              "\nReturn the complete new Python module in `code`.")
    history, code, problems = "", "", []
    for a in range(attempts + 1):
        res = backend.run(AgentTask(f"A11_cover_tests_r{round_no}_{a}", prompt + history, gen_tests.SCHEMA,
                                    system_prompt=WRITER_SYSTEM, model=model, max_turns=4), log_dir)
        usage.add(res)
        code = res.output["code"]
        problems = validate_module(code, contract, scenarios)
        if not problems:
            break
        history = ("\n\nYOUR PREVIOUS MODULE FAILED VALIDATION:\n" + "\n".join(problems) +
                   f"\n```python\n{code}\n```\nReturn the corrected complete module.")
    return code, problems


def baseline_section(results: dict, points: dict | None = None) -> list[str]:
    """Every measured metric of the run, the functional points never hit and the uncovered code items
    per metric and file: what the designer reads before choosing (or not) a coverage target."""
    cov = results.get("coverage") or {}
    metrics = cov.get("metrics") or {}
    out = ["## Measured baseline (the designer chooses whether to set a target, and on which metric)", "",
           "| Metric | Covered | Percent |", "|---|---|---|"]
    out += [f"| {m} | {v['hit']}/{v['total']} | {v['percent']} % |" for m, v in metrics.items() if v]
    func = results.get("functional") or {}
    missed = sorted(k for k, n in func.items() if not n)
    if missed:
        out += ["", "### Functional cover points never hit", ""]
        out += [f"- {k}: {(points or {}).get(k, {}).get('title', '')}".rstrip(": ") for k in missed]
    groups: dict = {}
    for u in cov.get("uncovered") or []:
        if u["metric"] == "functional":
            continue                                    # listed above with titles
        g = groups.setdefault((u["metric"], u["file"]), [0, []])
        g[0] += u.get("points", 1)
        g[1].append(u["line"])
    if groups:
        out += ["", "### Uncovered code items (simulator coverage; read with the RTL)", "",
                "| Metric | File | Points | Lines |", "|---|---|---|---|"]
        for (m, f), (n, lines) in sorted(groups.items()):
            shown = ", ".join(str(x) for x in sorted(set(lines), key=lambda x: (str(type(x)), x)))
            out.append(f"| {m} | {f} | {n} | {shown[:300] + (' ...' if len(shown) > 300 else '')} |")
    return out


def to_markdown(cov: dict, results: dict | None = None, points: dict | None = None) -> str:
    out = ["# Coverage closure", "", f"Metric **{cov['metric']}**, target {cov.get('target')} %, status "
           f"**{cov['status']}**.", ""]
    if results:
        out += baseline_section(results, points) + ["", "## Closure", ""]
    out += ["| Round | Coverage | Scenarios | Tests added | Note |", "|---|---|---|---|---|"]
    b = cov.get("baseline") or {}
    out.append(f"| baseline | {b.get('percent')} % ({b.get('hit')}/{b.get('total')}) | | | |")
    for r in cov.get("rounds", []):
        out.append(f"| {r['round']} | {r.get('percent')} % ({r.get('hit')}/{r.get('total')}) | {len(r.get('scenarios', []))} | "
                   f"{', '.join(r.get('tests', []))} | {r.get('note', '')} |")
    if cov.get("unreachable"):
        out += ["", "## Points claimed unreachable by legal stimulus (designer review; still counted)", "",
                "| Points | Rules | Reason |", "|---|---|---|"]
        out += [f"| {', '.join(u['where'])} | {', '.join(u['rules'])} | {u['reason']} |" for u in cov["unreachable"]]
    if cov.get("dropped"):
        out += ["", "## Scenarios dropped (they named RTL-internal identifiers)", ""]
        out += [f"- {d['id']}: {', '.join(d['leaks'])}" for d in cov["dropped"]]
    return "\n".join(x.replace("\n", " ") if x.startswith("|") else x for x in out) + "\n"

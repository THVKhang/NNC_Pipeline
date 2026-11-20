"""Gaps of a specification, found before gate G1 (`nnc spec-lint`, agent A18).

A specification can be complete in shape (`spec-check`) and still leave a behaviour open: two events in
the same cycle, a request while the block is busy, a reset in the middle of a sequence, back-pressure at
the worst moment, a parameter at its extreme. Such a gap surfaces late, as a failure that triage can only
call C (specification unclear): on gen_sync_fifo a second software-reset pulse during a running reset
sequence left the generated RTL, the approved checker and the contract each with a different reading.

Agent A18 reads only the specification (and the standards it cites) and lists, per gap, the scenario,
what the text says and what it does not decide, the lines it relies on, and the question for the
specification owner. Code checks the references: a cited `file:line` must exist, and a gap without any
valid reference is marked unsupported. Nothing is changed: the list goes to the G1 reviewer
(work/spec_lint.md), who answers the questions or amends the specification.
"""
from __future__ import annotations

import re
from pathlib import Path

from nnc.agents.backend import READ_ONLY_TOOLS, AgentTask
from nnc.agents.runtime import Usage

PROMPT_VERSION = "speclint-v1"
CATEGORIES = ("simultaneous_events", "request_while_busy", "reset_during_operation", "back_pressure",
              "parameter_extremes", "error_and_recovery", "initial_state", "contradiction", "other")
SYSTEM_PROMPT = (
    "You are a senior verification engineer reviewing a hardware design specification before anyone writes RTL "
    "or tests from it. You look for behaviour the text leaves open or states twice in different ways. You quote "
    "file:line for every claim. You do not invent requirements. Return the answer in the required JSON structure."
)
SCHEMA = {
    "type": "object", "required": ["gaps"], "additionalProperties": False,
    "properties": {
        "gaps": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["category", "scenario", "spec_says", "open_point", "spec_refs", "question", "readings",
                         "severity"],
            "properties": {
                "category": {"type": "string", "enum": list(CATEGORIES)},
                "scenario": {"type": "string"},
                "spec_says": {"type": "string"},
                "open_point": {"type": "string"},
                "spec_refs": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                "question": {"type": "string"},
                "readings": {"type": "array", "items": {"type": "string"}},
                "severity": {"type": "string", "enum": ["high", "medium", "low"]}}}},
        "notes": {"type": "string"}},
}

TASK = """# Task: find the gaps of the specification of `{ip}`

Files in this folder: `spec/` holds the specification{std}.

Read the whole specification. List every behaviour that two engineers could implement or check in different
ways because the text does not decide it, or decides it twice in different ways. Look in particular for:
- two events in the same cycle (a request and a reset, a read and a write at the boundary, a new request and
  the end of the previous one);
- a request, a pulse or a configuration change that arrives while the block is busy with an earlier one
  (is it ignored, queued, merged, an error?);
- a reset (hardware or software) in the middle of a sequence, and what the outputs show during and after it;
- back-pressure and stalls at the worst moment; full/empty boundaries;
- parameters at their extremes (minimum, maximum, 1, powers of two or not);
- errors: what is reported, when, and how the block recovers;
- values before the first reset, and what the environment is allowed to drive.

For each gap: the category, the scenario (concrete: who drives what, in which cycle), what the text says (with
quotes), what it leaves open, `spec_refs` as `spec/<file>:<line>` (one or more, the lines you rely on), the
question for the specification owner, the plausible readings (two or more), and the severity (high: a
reasonable RTL and a reasonable test would disagree; medium: likely to be read differently; low: wording).
Do not list a gap the text clearly decides. Prefer fewer, concrete gaps to many vague ones.
"""


def ref_ok(ref: str, files: dict[str, list[str]]) -> bool:
    """Is `spec/<file>:<line>` (or a range a-b) a line of a specification file?"""
    m = re.match(r"^\s*(?:spec/)?([^:]+?):(\d+)(?:\s*[-–]\s*(\d+))?", ref)
    if not m:
        return False
    name, a = Path(m.group(1)).name, int(m.group(2))
    lines = files.get(name)
    return bool(lines) and 1 <= a <= len(lines)


def lint(ip: str, docs: list[Path], standards: list[Path], backend, log_dir: Path, *, model: str = "opus") -> dict:
    inputs = {f"spec/{p.name}": p for p in docs}
    inputs.update({f"spec/standards/{p.name}": p for p in standards})
    std = " and, under `spec/standards/`, the standards it cites" if standards else ""
    task = AgentTask("A18_spec_lint", TASK.format(ip=ip, std=std), SCHEMA, inputs=inputs, tools=READ_ONLY_TOOLS,
                     system_prompt=SYSTEM_PROMPT, model=model, max_turns=60)
    res = backend.run(task, log_dir)
    usage = Usage()
    usage.add(res)
    files = {p.name: p.read_text(encoding="utf-8", errors="replace").splitlines() for p in docs + standards}
    gaps = []
    for i, g in enumerate(res.output.get("gaps", []), 1):
        good = [r for r in g["spec_refs"] if ref_ok(r, files)]
        gaps.append({"id": f"GAP-{i:03d}", **g, "refs_checked": len(good), "refs_given": len(g["spec_refs"]),
                     "supported": bool(good)})
    order = {"high": 0, "medium": 1, "low": 2}
    gaps.sort(key=lambda g: (not g["supported"], order[g["severity"]]))
    counts: dict[str, int] = {}
    for g in gaps:
        counts[g["severity"]] = counts.get(g["severity"], 0) + 1
    return {"gaps": gaps, "by_severity": counts, "unsupported": sum(not g["supported"] for g in gaps),
            "usage": usage.as_dict(), "model": model, "prompt_version": PROMPT_VERSION,
            "notes": res.output.get("notes", "")}


def to_markdown(ip: str, rep: dict) -> str:
    out = [f"# Specification gaps: {ip}", "",
           f"Agent A18 read only the specification and listed what it leaves open or states inconsistently "
           f"({rep['by_severity']}; {rep['unsupported']} without a valid line reference). Nothing was changed: "
           "answer each question or amend the specification before approving gate G1.", ""]
    for g in rep["gaps"]:
        out += [f"## {g['id']} [{g['severity']}] {g['category']}" + ("" if g["supported"] else " — **no valid reference**"),
                "", f"**Scenario.** {g['scenario']}", "", f"**The specification says.** {g['spec_says']}", "",
                f"**Left open.** {g['open_point']}", "", f"**Question.** {g['question']}", "",
                "**Readings.**", *[f"- {r}" for r in g["readings"]], "",
                f"References: {', '.join(g['spec_refs'])} ({g['refs_checked']}/{g['refs_given']} checked)", ""]
    out.append(f"Cost: US${rep['usage'].get('cost_usd', 0):.2f}")
    return "\n".join(out) + "\n"

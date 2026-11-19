"""Correct the verification where triage judged it wrong (`nnc fix-verif`, agent A17).

Triage (A9 for simulation, A14 for formal) may judge a failure B: the test or the checker is wrong, not
the RTL. Until now a person fixed such a fault by hand. Here agent A17 proposes the fix, under the same
isolation as every verification generator:
  - it never sees the RTL: the fault text keeps only what the specification says and what the
    verification does; every sentence that names an RTL file, module or "the RTL" is dropped;
  - it may change only existing checker and test files (verif/sva/*.sv, verif/tests/*.py), never the
    formal environment (an assumption is a decision about the environment, verdict E, not a fix);
  - code refuses a weakening (`weakening`): a removed assertion, cover point, test or check reference, a
    new assumption, an assertion switched off, a skipped or expected-to-fail test;
  - the fix is a candidate in work/verif_fix/candidate/, run against the RTL there; `--apply` copies it
    into verif/, records it in NOTICE.md, and gate G3 becomes STALE: a person approves it again.
"""
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

from nnc.agents.backend import READ_ONLY_TOOLS, AgentTask
from nnc.agents.runtime import Usage

PROMPT_VERSION = "fixverif-v1"
SYSTEM_PROMPT = (
    "You are a senior design-verification engineer. You correct testbench code and SVA checkers so that they "
    "follow the specification exactly. You never see the design under test and must not guess its "
    "implementation. You never weaken a check. Return the answer in the required JSON structure."
)
SCHEMA = {
    "type": "object", "required": ["changes", "not_fixed"], "additionalProperties": False,
    "properties": {
        "changes": {"type": "array", "items": {
            "type": "object", "required": ["file", "content", "faults", "why", "spec_refs"], "additionalProperties": False,
            "properties": {"file": {"type": "string"}, "content": {"type": "string", "minLength": 20},
                           "faults": {"type": "array", "items": {"type": "integer"}},
                           "why": {"type": "string"}, "spec_refs": {"type": "array", "items": {"type": "string"}}}}},
        "not_fixed": {"type": "array", "items": {
            "type": "object", "required": ["fault", "reason"], "additionalProperties": False,
            "properties": {"fault": {"type": "integer"}, "reason": {"type": "string"}}}},
        "notes": {"type": "string"}},
}
B_VERDICTS = ("B_test_wrong", "B_checker_wrong")


# ------------------------------------------------------------------------------------------- faults
def fault_text(analyses: list[dict], rtl_names: list[str]) -> list[dict]:
    """Faults judged B, reduced to the specification and the verification side. Sentences naming an RTL
    file, an RTL module, rtl/ or "the RTL"/"the DUT does" are dropped, so nothing of the implementation
    reaches A17."""
    stems = sorted({Path(n).stem for n in rtl_names} | {Path(n).name for n in rtl_names}, key=len, reverse=True)
    hidden = re.compile(r"\brtl/|\bRTL\b|\bDUT\b|\bthe design (?:does|drives|implements)" +
                        "".join(f"|\\b{re.escape(s)}\\b" for s in stems), re.I)

    def clean(text: str) -> str:
        keep = [s for s in re.split(r"(?<=[.;])\s+", text or "") if not hidden.search(s)]
        return " ".join(keep).strip()
    out = []
    for a in analyses:
        if a.get("most_likely") not in B_VERDICTS:
            continue
        title = a.get("failure") or ("formal counterexample on " + re.sub(r"\s*\(.*\)\s*$", "", a.get("check", "")))
        out.append({"id": len(out) + 1, "failure": clean(title)[:300] or title.split(" ")[0],
                    "spec_says": clean(a.get("spec_says", ""))[:2500],
                    "verification_does": clean(a.get("test_does") or a.get("checker_does") or "")[:3000],
                    "what_to_change": clean(a.get("options", ""))[:2000]})
    return out


# ---------------------------------------------------------------------------------------- weakening
_ASSERT = re.compile(r"\b(\w+)\s*:\s*assert\s+property\b")
_COVER = re.compile(r"\b(\w+)\s*:\s*cover\s+property\b")
_CHK = re.compile(r"CHK-\d{3}")
_TEST = re.compile(r"@cocotb\.test\s*\([^)]*\)\s*\n\s*async\s+def\s+(\w+)|@cocotb\.test\s*\n\s*async\s+def\s+(\w+)")
_OFF = re.compile(r"\$assert(?:off|kill|control)\b")
_ASSUME = re.compile(r"\bassume\s+property\b|\bassume\s*\(")
_SKIP = re.compile(r"\bskip\s*=\s*True|\bexpect_fail\s*=\s*True|\bexpect_error\s*=|\bpytest\.skip\b|\braise\s+cocotb\.result\.TestSuccess")


def _strip_sv_comments(t: str) -> str:
    return re.sub(r"//[^\n]*", "", re.sub(r"/\*.*?\*/", "", t, flags=re.S))


def _strip_py_comments(t: str) -> str:
    return re.sub(r"(?m)#[^\n]*$", "", t)


def _disables(t: str) -> list[str]:
    """The conditions of every `disable iff (...)`, in order (balanced parentheses, spaces removed)."""
    out = []
    for m in re.finditer(r"disable\s+iff\s*\(", t):
        depth, i = 1, m.end()
        while i < len(t) and depth:
            depth += {"(": 1, ")": -1}.get(t[i], 0)
            i += 1
        out.append(re.sub(r"\s+", "", t[m.end():i - 1]))
    return out


def _tests(t: str) -> set[str]:
    return {a or b for a, b in _TEST.findall(t)}


def weakening(old: dict[str, str], new: dict[str, str]) -> tuple[list[str], list[str]]:
    """(blocking, warnings) for replacing `old` file texts by `new` ones (keys: verif-relative paths)."""
    block, warn = [], []
    for path, after in new.items():
        before = old.get(path)
        if before is None:
            block.append(f"{path}: not an existing verification file (A17 may only change existing files)")
            continue
        if path.endswith(".sv"):
            b, a = _strip_sv_comments(before), _strip_sv_comments(after)
            for kind, rx in (("assertion", _ASSERT), ("cover point", _COVER)):
                gone = sorted(set(rx.findall(b)) - set(rx.findall(a)))
                if gone:
                    block.append(f"{path}: {kind}(s) removed: {', '.join(gone)}")
            if len(_ASSUME.findall(a)) > len(_ASSUME.findall(b)):
                block.append(f"{path}: a new assumption (assumptions belong to the environment, not to a fix)")
            if len(_OFF.findall(a)) > len(_OFF.findall(b)):
                block.append(f"{path}: an assertion is switched off ($assertoff/$assertkill/$assertcontrol)")
            if _disables(b) != _disables(a):
                warn.append(f"{path}: a `disable iff` condition changed: check it does not hide a failure")
        elif path.endswith(".py"):
            b, a = _strip_py_comments(before), _strip_py_comments(after)
            gone = sorted(_tests(b) - _tests(a))
            if gone:
                block.append(f"{path}: test(s) removed: {', '.join(gone)}")
            if len(_SKIP.findall(a)) > len(_SKIP.findall(b)):
                block.append(f"{path}: a test is skipped or expected to fail")
            n_b, n_a = len(re.findall(r"\bassert\b", b)), len(re.findall(r"\bassert\b", a))
            if n_a < n_b:
                warn.append(f"{path}: {n_b - n_a} fewer `assert` statement(s): check no expected value was dropped")
        else:
            block.append(f"{path}: A17 may change only checkers (.sv) and tests (.py)")
        lost = sorted(set(_CHK.findall(before)) - set(_CHK.findall(after)))
        if lost:
            block.append(f"{path}: check reference(s) removed: {', '.join(lost)}")
    return block, warn


def diff(old: dict[str, str], new: dict[str, str]) -> str:
    out = []
    for path in sorted(new):
        out += difflib.unified_diff(old.get(path, "").splitlines(), new[path].splitlines(),
                                    f"a/verif/{path}", f"b/verif/{path}", lineterm="", n=2)
    return "\n".join(out)


# ------------------------------------------------------------------------------------------- agent
TASK = """# Task: correct the verification of `{top}` where triage found it wrong

Files in this folder:
- `spec/`: the specification.
- `contract.json`: the approved verification contract (checks CHK-xxx, interface, environment rules).
- `rules.json`: the approved rules (requirement IDs and quotes).
- `verif/sva/`: the SVA checkers; `verif/tests/`: the cocotb tests and their helper library
  `nnc_cocotb.py`{env}.
- `FAULTS.json`: the faults. A reviewer judged each one a fault of the VERIFICATION (the test or the
  checker does not follow the specification), not of the design. For each: what the specification says,
  what the verification does, and what should change.

You never see the design under test. Do not guess how it is built: make the verification follow the
specification.

Rules:
1. Change as little as possible. Fix only the listed faults.
2. Never weaken a check. Do not remove or relax an assertion, a cover point, a test or a check
   reference (CHK-xxx). Do not add assumptions or `$assertoff`. Do not skip a test or mark it expected to
   fail. Do not change an expected value unless the specification requires the new one; then quote it.
3. You may change only existing files under `verif/sva/` (.sv) and `verif/tests/` (.py), except
   `nnc_cocotb.py`. Mark each change with a comment
   `NNC verification fix (fix-verif, triage B): <why>`.
4. If a fault cannot be fixed without weakening, or the specification does not decide it, do not change
   anything for it: put it in `not_fixed` with the reason.

Answer with `changes` (for each changed file: its path such as `verif/sva/nnc_chk_rx.sv`, its FULL new
content, the fault ids it fixes, why, and the specification references), and `not_fixed`.
{retry}"""


def propose(top: str, faults: list[dict], inputs: dict[str, Path], backend, log_dir: Path, work_dir: Path, *,
            forbidden: tuple[Path, ...] = (), model: str = "opus", retry: str = "",
            tag: str = "r0") -> tuple[dict, Usage]:
    """One A17 call. `forbidden`: folders (the RTL) whose files the backend refuses as inputs."""
    files = dict(inputs)
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "FAULTS.json").write_text(json.dumps(faults, indent=1), encoding="utf-8")
    files["FAULTS.json"] = work_dir / "FAULTS.json"
    env = "; `verif/formal/nnc_env.sv`: the formal environment (read only)" if any(
        k.startswith("verif/formal/") for k in files) else ""
    task = AgentTask(f"A17_fix_verif_{tag}", TASK.format(top=top, env=env, retry=retry), SCHEMA, inputs=files,
                     forbidden=forbidden, tools=READ_ONLY_TOOLS, system_prompt=SYSTEM_PROMPT, model=model,
                     max_turns=80)
    res = backend.run(task, log_dir)
    usage = Usage()
    usage.add(res)
    return res.output, usage


def still_failing(faults: list[dict], result: dict) -> list[dict]:
    """Faults whose check (CHK-xxx in the failure title) or test still fails in `result`, with what the
    verification reported about it (count, first failure time, message): the feedback for a next attempt."""
    asserts = {k: v for k, v in (result.get("assertions") or {}).items() if v.get("fails")}
    tests = {t["name"]: t for t in result.get("tests", []) if t.get("status") == "fail"}
    out = []
    for f in faults:
        ids = set(_CHK.findall(f["failure"]))
        hit = [f"{c}: {asserts[c]['fails']} assertion failure(s), first at {asserts[c].get('first_fail_time')} ps"
               for c in sorted(ids & set(asserts))]
        hit += [f"{n}: {(t.get('message') or '')[:300]}" for n, t in tests.items()
                if any(c.replace("-", "_").lower() in n.lower() for c in ids) or n in f["failure"]]
        if hit:
            out.append({"id": f["id"], "report": "; ".join(hit)})
    return out


def norm_path(file: str) -> str:
    """A path of the answer, relative to verif/ (a leading ./ or verif/ is dropped)."""
    p = file.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p[len("verif/"):] if p.startswith("verif/") else p


def changed_files(answer: dict, old: dict[str, str]) -> dict[str, str]:
    """{verif-relative path: new text} of the answer."""
    out = {}
    for c in answer.get("changes", []):
        p = norm_path(c["file"])
        out[p] = c["content"] if c["content"].endswith("\n") else c["content"] + "\n"
    return out


def to_markdown(name: str, rep: dict) -> str:
    out = [f"# Verification fix candidate: {name}", "",
           f"Agent A17 (no RTL) proposed changes for {len(rep['faults'])} fault(s) judged B by triage. "
           f"Status: **{rep['status']}**. Nothing in verif/ changes until `nnc fix-verif {name} --apply`, and "
           "then gate G3 must be approved again.", "", "## Faults (as A17 saw them)", ""]
    for f in rep["faults"]:
        out += [f"{f['id']}. **{f['failure']}**", f"   - specification: {f['spec_says'][:600]}",
                f"   - verification: {f['verification_does'][:600]}", ""]
    out += ["## Changes", ""]
    for c in rep.get("changes", []):
        out.append(f"- `verif/{c['file']}` (faults {c['faults']}): {c['why']} — {', '.join(c['spec_refs'])}")
    for n in rep.get("not_fixed", []):
        out.append(f"- not fixed: fault {n['fault']}: {n['reason']}")
    if rep.get("attempts"):
        out += ["", "## Attempts", ""]
        for a in rep["attempts"]:
            res = a.get("after")
            out.append(f"- attempt {a['attempt']}: files {', '.join(a['files']) or 'none'}"
                       + (f"; refused: {'; '.join(a['refused'])}" if a.get("refused") else "")
                       + (f"; after: failing assertions {', '.join(res['failing_assertions']) or 'none'}, failing "
                          f"tests {', '.join(res['failing_tests']) or 'none'}" if res else ""))
    if rep.get("still_failing"):
        out.append(f"- faults still failing after the last attempt: {rep['still_failing']}")
    out += ["", "## Weakening check (code)", ""]
    out += [f"- **blocked:** {b}" for b in rep.get("blocking", [])] or ["- no weakening found"]
    out += [f"- warning: {w}" for w in rep.get("warnings", [])]
    if rep.get("candidate_run"):
        r = rep["candidate_run"]
        out += ["", "## Regression of the candidate on the RTL", "",
                "| | before | candidate |", "|---|---|---|",
                f"| failing tests | {', '.join(r['before']['failing_tests']) or 'none'} | {', '.join(r['after']['failing_tests']) or 'none'} |",
                f"| failing assertions | {', '.join(r['before']['failing_assertions']) or 'none'} | {', '.join(r['after']['failing_assertions']) or 'none'} |",
                f"| tests / assertions | {r['before']['n_tests']} / {r['before']['n_assertions']} | {r['after']['n_tests']} / {r['after']['n_assertions']} |"]
    out += ["", "## Diff", "", "```diff", rep.get("diff", ""), "```", "",
            f"Cost: US${rep.get('usage', {}).get('cost_usd', 0):.2f}"]
    return "\n".join(out) + "\n"

"""RTL generation (agent A15) and RTL repair from specification-level fault reports.

The design half of the flow. A15 writes the synthesizable RTL of the top module from:

    spec/<documents>     the specification (and standards) registered for the design
    REQUIREMENTS.md      the approved rules of G1, with the decisions on open questions
    INTERFACE.md         ports, clocks, resets and parameters of the contract (G2), with the values of the
                         chosen configuration (D1, work/final_config.json)
    RTL_RULES.md         docs/RTL_RULES.md

It never sees the verification: not the check plan of the contract, the SVA, the tests, the results or
the triage of a test (principle PR-1 applied in the other direction; the sandbox refuses inputs from
verif/). The RTL and the verification stay two independent readings of one specification, so a shared
misreading is less likely to hide a bug.

After each answer, code runs nnc/rtlcheck.py (source rules, Verilator -Wall, Yosys structure, the ports of
the contract, synthesis on GF180) and sends errors and warnings back, for at most `rounds` repairs. The RTL
goes to rtl/ (only for a design whose RTL the flow generates) with work/rtl_gen.json and work/rtl_gen.md,
the material of gate D2_rtl.

Repair (`fixes`): when the verification of an approved RTL fails and triage judges a failure *A: RTL
wrong*, A15 receives the current RTL and, for each fault, only what the specification says and what the RTL
does (the `spec_says` and `rtl_does` of the triage, with any line that points into verif/ removed). It
never receives the test or the checker. The repaired RTL goes through the same checks, and D2_rtl becomes
STALE, so a person approves the change.
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from nnc import rtlcheck
from nnc.agents.backend import READ_ONLY_TOOLS, AgentTask
from nnc.agents.runtime import Usage
from nnc.simhost import SimHost

PROMPT_VERSION = "rtl-v1"
RULES_DOC = Path(__file__).resolve().parent.parent / "docs" / "RTL_RULES.md"
SYSTEM_PROMPT = (
    "You are an RTL design engineer. You write synthesizable SystemVerilog that implements a specification "
    "exactly, following the design rules you are given. You work only from the files in the current folder. "
    "Where the specification is silent or ambiguous you choose the most conservative reading and say so. "
    "Return the answer in the required JSON structure."
)
SCHEMA = {
    "type": "object", "required": ["files", "filelist", "open_points"], "additionalProperties": False,
    "properties": {
        "files": {"type": "array", "items": {
            "type": "object", "required": ["name", "content"], "additionalProperties": False,
            "properties": {"name": {"type": "string", "pattern": r"^[A-Za-z_][A-Za-z0-9_]*\.sv$"},
                           "content": {"type": "string", "minLength": 20}}}},
        "remove": {"type": "array", "items": {"type": "string"}},
        "filelist": {"type": "array", "minItems": 1, "items": {"type": "string"}},
        "open_points": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"}},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ------------------------------------------------------------------------------------- inputs
def requirements_md(rules_doc: dict) -> str:
    """The approved rules for the designer of the RTL (no verification plan)."""
    out = ["# Requirements (approved rules, gate G1)", "",
           "Each rule cites the specification. Tag the RTL that implements a rule with `// REQ: <id>`.", ""]
    for r in rules_doc["rules"]:
        where = f"{r.get('doc', '')} {r.get('section', '')}".strip()
        cond = f" Condition: {r['condition']}." if r.get("condition") else ""
        out.append(f"- **{r['id']}** [{r.get('strength', '')}] ({where}) {r['statement']}{cond}")
        if r.get("quote"):
            out.append(f"  - quote: \"{r['quote']}\"")
    decided = [q for q in rules_doc.get("questions", []) if q.get("decision")]
    if decided or rules_doc.get("answered_questions"):
        out += ["", "## Decisions on questions the specification left open", ""]
        for q in decided:
            out.append(f"- Rules {', '.join(q['rules'])}: {q['question']}\n  - **Decision:** {q['decision']['answer']}")
        for q in rules_doc.get("answered_questions") or []:
            out.append(f"- Rules {', '.join(q['rules'])}: {q['question']}\n  - **Answer from the text:** {q['answer']}")
    open_q = [q for q in rules_doc.get("questions", []) if not q.get("decision")]
    if open_q:
        out += ["", "## Questions without a decision (choose the conservative reading and list it in open_points)", ""]
        out += [f"- Rules {', '.join(q['rules'])}: {q['question']}" for q in open_q]
    return "\n".join(out) + "\n"


def interface_md(contract: dict, final: dict) -> str:
    iface, values = contract["interface"], final["values"]
    out = [f"# Interface of the top module `{contract['top']}` (contract, gate G2)", "",
           "The top module must have exactly these parameters and ports (names, directions, widths).", "",
           "## Parameters", "", "| Name | Default (keep it) | Chosen value | Legal values | Derived from |",
           "|---|---|---|---|---|"]
    for p in iface["parameters"]:
        out.append(f"| {p['name']} | {p.get('default', '')} | {values.get(p['name'], '')} | {p.get('legal', '')} | "
                   f"{p.get('derived') or ''} |")
    out += ["", "Overridable parameters are `parameter`s with the default shown; derived ones are `localparam`s "
            "computed by the formula. The RTL must work for every legal value, not only the chosen one (the "
            "checks run with the chosen values).", "",
            "## Ports", "", "| Name | Direction | Width | Reset value | Clock domain | Meaning |", "|---|---|---|---|---|---|"]
    for p in iface["ports"]:
        out.append(f"| {p['name']} | {p['direction']} | {p['width']} | {p.get('reset_value', '')} | "
                   f"{p.get('domain', '')} | {p.get('meaning', '')} |")
    clocks = rtlcheck.clock_names(iface)
    resets = [r for r in iface.get("resets") or [iface.get("reset")] if isinstance(r, dict)]
    out += ["", f"Clocks: {', '.join(clocks)} (relation: {iface.get('clock_relation') or 'single or synchronous'}).",
            "Resets: " + ", ".join(f"{r['name']} (active {'low' if r.get('active_low') else 'high'}"
                                   + (f", clock {r['clock']}" if r.get("clock") else "") + ")" for r in resets if r)]
    if final.get("notes"):
        out += ["", "Notes on the legal values: " + "; ".join(f"{k}: {v}" for k, v in final["notes"].items())]
    return "\n".join(out) + "\n"


def fault_text(analyses: list[dict]) -> list[dict]:
    """Faults judged A (RTL wrong) by triage, reduced to the specification-level description."""
    out = []
    for a in analyses:
        if a.get("most_likely") != "A_rtl_wrong":
            continue

        def clean(text: str) -> str:
            keep = [s for s in re.split(r"(?<=[.;])\s+", text or "") if "verif/" not in s and "test_" not in s]
            return " ".join(keep).strip()
        title = re.sub(r"^test_\w+\s*[—-]\s*", "", a.get("failure", ""))
        out.append({"fault": title[:300], "spec_says": clean(a.get("spec_says", ""))[:2500],
                    "rtl_does": clean(a.get("rtl_does", ""))[:3000]})
    return out


TASK = """# Task: {mode} the RTL of `{top}`

Files in this folder:
- `spec/`: the specification{std}.
- `REQUIREMENTS.md`: the approved requirements (rule IDs), with decisions on open questions.
- `INTERFACE.md`: the exact parameters and ports of the top module, and the chosen configuration.
- `RTL_RULES.md`: the design rules. Follow every rule; the code checks are run on your answer.
{current}
{what}

Answer with:
- `files`: the {files_what} (`name` = `<module>.sv`, `content` = the whole file);
- `remove`: names of files to delete (optional);
- `filelist`: every file of the design in compile order, leaf modules first, `{top}.sv` last;
- `open_points`: each place where the specification was silent or ambiguous and the reading you chose
  (with the section), and anything you could not implement. Empty if none.

Design requirements:
- Implement the specification completely: every requirement of REQUIREMENTS.md that the RTL can implement.
- The top module `{top}` has exactly the parameters and ports of INTERFACE.md.
- The RTL must be correct for every legal parameter value, not only the chosen configuration.
- Tag the code that implements a requirement with `// REQ: <rule id>[, <rule id>]`.
- Use `ifndef SYNTHESIS` only for simulation-only behaviour the specification itself asks for.
"""


def _instructions(contract: dict, docs: list[str], current: list[str], problems: str, fixes: list[dict]) -> str:
    std = " (and standards)" if len(docs) > 1 else ""
    cur = (f"- `current/`: the current RTL ({', '.join(current)}). Keep what is right; change what is needed."
           if current else "")
    if fixes:
        items = "\n".join(f"{i}. **{f['fault']}**\n   - The specification says: {f['spec_says']}\n"
                          f"   - The current RTL does: {f['rtl_does']}" for i, f in enumerate(fixes, 1))
        what = ("## Faults to fix\n\nAn independent verification of the current RTL, generated from the same "
                "specification, found these faults. Each was analysed against the specification and judged an RTL "
                "fault. Check each against the specification yourself, fix it in the RTL with the smallest change "
                "that meets the specification, and do not change behaviour the specification does not ask to "
                f"change. If you disagree that a fault is real, leave the RTL as it is and explain why in "
                f"open_points.\n\n{items}")
        mode, files_what = "Repair", "files you changed or added"
    else:
        what = "## What to do\n\nWrite the complete RTL of the design from the specification."
        mode, files_what = "Write", "RTL files" if not current else "files you changed or added"
        if current:
            mode = "Correct"
    if problems:
        what += ("\n\n## Problems found by the code checks in the current RTL\n\nFix every error and warning "
                 "(see RTL_RULES.md; a lint warning that truly cannot be fixed needs a `lint_off` pragma with a "
                 f"`// WAIVER: <reason>` comment).\n\n{problems}")
    return TASK.format(mode=mode, top=contract["top"], std=std, current=cur, what=what, files_what=files_what)


def _problems(findings: list[dict], limit: int = 60) -> str:
    rows = [f for f in findings if f["severity"] in ("error", "warning")]
    text = "\n".join(f"- [{f['severity']}] {f['rule']} {f['file']}{':' + str(f['line']) if f['line'] else ''} "
                     f"{f['message']}" for f in rows[:limit])
    return text + (f"\n- ... and {len(rows) - limit} more" if len(rows) > limit else "")


def blocking(findings: list[dict]) -> list[dict]:
    """Findings the agent must fix (errors, warnings)."""
    return [f for f in findings if f["severity"] in ("error", "warning")]


# ------------------------------------------------------------------------------------- generation
def generate(d_root: Path, contract: dict, rules_doc: dict, final: dict, docs: list[Path], backend, log_dir: Path,
             host: SimHost | None, *, model: str = "opus", rounds: int = 3, current: dict[str, str] | None = None,
             fixes: list[dict] | None = None, pdk_dir: str = rtlcheck.PDK_DIR, max_turns: int = 60) -> dict:
    """Run A15 until the checks pass or `rounds` repairs are used. Returns the report (files in 'files')."""
    work = d_root / "work" / "rtl_gen"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    (work / "REQUIREMENTS.md").write_text(requirements_md(rules_doc), encoding="utf-8")
    (work / "INTERFACE.md").write_text(interface_md(contract, final), encoding="utf-8")
    rule_ids = {r["id"] for r in rules_doc["rules"]}
    files: dict[str, str] = dict(current or {})
    usage, history = Usage(), []
    fixes = fixes or []
    chk: dict = {}
    status = "failed"
    open_points: list[str] = []
    for attempt in range(rounds + 1):
        problems = _problems(blocking(chk["findings"])) if chk else ""
        cur_dir = work / f"current_r{attempt}"
        inputs = {f"spec/{p.name}": p for p in docs}
        inputs.update({"REQUIREMENTS.md": work / "REQUIREMENTS.md", "INTERFACE.md": work / "INTERFACE.md",
                       "RTL_RULES.md": RULES_DOC})
        for name, text in files.items():
            (cur_dir / name).parent.mkdir(parents=True, exist_ok=True)
            (cur_dir / name).write_text(text, encoding="utf-8")
            inputs[f"current/{name}"] = cur_dir / name
        task = AgentTask(f"A15_rtl{'_fix' if fixes else ''}_r{attempt}",
                         _instructions(contract, [p.name for p in docs], sorted(files), problems,
                                       fixes if attempt == 0 else []),
                         SCHEMA, inputs=inputs, forbidden=[d_root / "verif"], tools=READ_ONLY_TOOLS,
                         system_prompt=SYSTEM_PROMPT, model=model, max_turns=max_turns)
        res = backend.run(task, log_dir)
        usage.add(res)
        out = res.output
        for f in out["files"]:
            files[f["name"]] = f["content"] if f["content"].endswith("\n") else f["content"] + "\n"
        for n in out.get("remove") or []:
            files.pop(n, None)
        files["filelist.f"] = ("// filelist.f - RTL files in compile order (leaf modules first, top last).\n"
                               f"// Generated by NNC (agent A15, {PROMPT_VERSION}).\n" + "\n".join(out["filelist"]) + "\n")
        open_points = out.get("open_points") or []
        chk = rtlcheck.check(host, files, contract, final["values"], rule_ids, pdk_dir=pdk_dir)
        history.append({"attempt": attempt, "counts": chk["counts"], "changed": [f["name"] for f in out["files"]],
                        "cost_usd": res.cost_usd})
        if not blocking(chk["findings"]):
            status = "clean" if host is not None else "source_clean"
            break
    return {"status": status, "attempts": len(history), "history": history, "files": files,
            "findings": chk.get("findings", []), "counts": chk.get("counts", {}), "trace": chk.get("trace", {}),
            "synth": chk.get("synth", {}), "open_points": open_points, "fixes": fixes, "usage": usage.as_dict(),
            "model": model, "prompt_version": PROMPT_VERSION, "config": final.get("values"),
            "unreviewed_note": None, "at": _now()}


def write_rtl(rtl_dir: Path, files: dict[str, str]) -> None:
    """Replace the generated RTL (only .sv files and filelist.f; nothing else is touched)."""
    rtl_dir.mkdir(parents=True, exist_ok=True)
    for f in list(rtl_dir.glob("*.sv")) + [rtl_dir / "filelist.f"]:
        if f.is_file():
            f.unlink()
    for name, text in files.items():
        (rtl_dir / name).write_text(text, encoding="utf-8", newline="\n")


def report_json(rep: dict) -> dict:
    """work/rtl_gen.json: the report without the file contents (rtl/ holds them)."""
    out = {k: v for k, v in rep.items() if k != "files"}
    out["files"] = sorted(rep["files"])
    return out


def to_markdown(rep: dict, design: str, rules_doc: dict) -> str:
    c = rep["counts"]
    out = [f"# RTL generation report: {design}", "",
           f"Status: **{rep['status']}** after {rep['attempts']} attempt(s) (agent A15, {rep['model']}, "
           f"{rep['prompt_version']}); cost US${rep['usage'].get('cost_usd', 0):.2f}.",
           f"Remaining findings: {c.get('error', 0)} errors, {c.get('warning', 0)} warnings, {c.get('info', 0)} notes.",
           "", "This report is the material of gate **D2_rtl**. The code checks below say nothing about whether "
           "the RTL is *correct*: the verification (G3/G4), generated independently of this RTL, decides that.", ""]
    if rep.get("fixes"):
        out += ["## Faults this revision was asked to fix", ""]
        out += [f"- {f['fault']}" for f in rep["fixes"]]
        out.append("")
    s = rep.get("synth") or {}
    out += ["## Synthesis (estimates, RR-43)", ""]
    if s.get("corners"):
        out += ["| Corner | Library | Cell area (um^2) | Longest combinational path (ps) |", "|---|---|---|---|"]
        for k, v in s["corners"].items():
            out.append(f"| {k} | {v['library']} | {v['area_um2']} | {v['comb_delay_ps']} |")
        out += ["", f"Generic cells: {s.get('generic_cells')}. Delay is ABC's estimate without wires, clock-to-output "
                "or setup time: a comparison figure, not a timing sign-off.", ""]
    else:
        out += ["Not run (an earlier check failed) or no liberty files.", ""]
    t = rep.get("trace") or {}
    untagged = sorted({r["id"] for r in rules_doc["rules"]} - set(t.get("tagged", [])))
    out += ["## Traceability (RR-42)", "", f"Rules tagged in the RTL: {len(t.get('tagged', []))} of "
            f"{len(rules_doc['rules'])} ({t.get('coverage')} %). A rule may be untagged because it is about the "
            "environment, the documentation or verification, not the RTL; the reviewer checks the list.", ""]
    if untagged:
        out += ["<details><summary>Untagged rules</summary>", "", ", ".join(untagged), "", "</details>", ""]
    if t.get("waivers"):
        out += ["## Lint waivers (RR-40)", ""] + [f"- {w['file']}:{w['line']} {w['text']}" for w in t["waivers"]] + [""]
    out += ["## Open points stated by the agent", ""]
    out += [f"- {p}" for p in rep.get("open_points") or []] or ["- none"]
    out += ["", "## Findings", ""]
    if rep["findings"]:
        out += ["| Severity | Rule | Where | Message |", "|---|---|---|---|"]
        for f in rep["findings"]:
            where = f"{f['file']}:{f['line']}" if f["line"] else f["file"]
            out.append(f"| {f['severity']} | {f['rule']} | {where} | {f['message'].replace('|', '/')} |")
    else:
        out.append("None.")
    out += ["", "## Attempts", ""]
    out += [f"- {h['attempt']}: {h['counts']} (changed {', '.join(h['changed'])})" for h in rep["history"]]
    out += ["", "## For the reviewer of D2_rtl (rules checked by a person)", "",
            "- RR-03 file headers; RR-24 state machines; RR-32 reset values; RR-33 clock-domain crossings;",
            "  RR-41 widths written with parameters; RR-44 names (docs/RTL_RULES.md).",
            "- The open points above: is each reading the one the specification intends?",
            f"- Then: `nnc gate approve {design} D2_rtl --by \"<name>\" --note \"...\"`.", ""]
    return "\n".join(out)

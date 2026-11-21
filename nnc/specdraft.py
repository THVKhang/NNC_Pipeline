"""Specification drafting from a design description (agent A0) and the shape check of a specification.

`spec-check` (code only): can the flow read this specification? It indexes the file as `nnc ingest` does and
checks what the later stages need: numbered sections, a port table of the top module the contract stage can
read, a parameter table whose legal values `nnc params` can check, requirement sentences with unique IDs,
the sections of docs/SPEC_TEMPLATE.md. It does not judge whether the specification is right.

`spec-draft`: agent A0 writes a first specification in the shape of docs/SPEC_TEMPLATE.md from a short
description written by a person. The shape check runs on each answer and its findings go back to the agent.
Everything the description did not say and A0 had to choose is listed (assumptions, open questions): the
draft is a proposal for the designer, who edits it before the flow starts. Its hash is recorded at gate G1
(golden manifest), so the rules are always tied to the text a person approved.
"""
from __future__ import annotations

import re
from pathlib import Path

from nnc.agents.backend import AgentTask
from nnc.agents.runtime import Usage
from nnc.contract import extract_interface
from nnc.ingest import build_index
from nnc.params import parse_legal

TEMPLATE = Path(__file__).resolve().parent / "data" / "SPEC_TEMPLATE.md"   # package copy of docs/SPEC_TEMPLATE.md
REQUIRED = ("overview", "parameter", "interface", "clock", "functional", "error", "configuration", "verification")
PROMPT_VERSION = "spec-v1"
SYSTEM_PROMPT = (
    "You are a senior digital design engineer writing the design specification of a hardware IP block. "
    "The specification is the only input of an automatic verification flow and of the RTL designer, so every "
    "behaviour must be stated precisely, including errors, back-pressure, reset and parameter extremes. You "
    "never leave a choice implicit: what the description does not decide, you decide conservatively and "
    "list as an assumption. Return the answer in the required JSON structure."
)
SCHEMA = {
    "type": "object", "required": ["markdown", "assumptions", "open_questions"], "additionalProperties": False,
    "properties": {"markdown": {"type": "string", "minLength": 500},
                   "assumptions": {"type": "array", "items": {"type": "string"}},
                   "open_questions": {"type": "array", "items": {"type": "string"}},
                   "notes": {"type": "string"}},
}


def _f(sev: str, msg: str) -> dict:
    return {"severity": sev, "message": msg}


def check_spec(path: Path, top: str | None) -> dict:
    """Findings on the shape of a specification, and what the flow reads from it."""
    out: list[dict] = []
    try:
        idx = build_index(path)
    except Exception as e:  # noqa: BLE001 - any ingest failure is a finding
        return {"findings": [_f("error", f"the file cannot be indexed: {e}")], "ports": 0, "parameters": 0,
                "requirements": 0}
    titles = " | ".join(s.get("title", "").lower() for s in idx.get("sections", []))
    for word in REQUIRED:
        if word not in titles:
            out.append(_f("warning", f"no section about '{word}' (docs/SPEC_TEMPLATE.md)"))
    ports, params = [], []
    try:
        iface = extract_interface(idx, top=top)
        ports, params = iface["ports"], iface["parameters"]
        if top and not any(re.match(rf"\s*{re.escape(top)}\b", t.get("caption") or "") for t in idx.get("tables", [])):
            out.append(_f("warning", f"no port-table caption starting with the top module name `{top}`"))
        if not iface.get("clock") and not iface.get("clocks"):
            out.append(_f("error", "no clock input found in the port table (Signal type 'Clock')"))
        if not iface.get("reset"):
            out.append(_f("warning", "no reset input found in the port table (Signal type 'Reset')"))
        pnames = {p["name"] for p in params}
        for p in ports:
            if not (p["name"].startswith(("i_", "o_"))):
                out.append(_f("warning", f"port {p['name']}: inputs start with i_, outputs with o_"))
            w = p["width"]
            if not (w.isdigit() or all(t in pnames for t in re.findall(r"[A-Za-z_]\w*", w))):
                out.append(_f("error", f"port {p['name']}: width '{w}' is not a number or an expression of parameters"))
            if p["direction"] == "output" and not p.get("reset_value"):
                out.append(_f("warning", f"output {p['name']}: no reset value"))
        for p in params:
            if parse_legal(p.get("legal"))["kind"] == "unchecked":
                out.append(_f("warning", f"parameter {p['name']}: legal values '{p.get('legal')}' are not in a form the "
                                         f"flow can check (docs/SPEC_TEMPLATE.md section 4)"))
    except ValueError as e:
        out.append(_f("error", f"interface: {e}"))
    text = path.read_text(encoding="utf-8", errors="replace")
    defined = re.findall(r"\[(REQ-[A-Z0-9][A-Z0-9_.-]*)\]", text)        # [REQ-x] defines a requirement
    dup = sorted({i for i in defined if defined.count(i) > 1})
    if dup:
        out.append(_f("error", f"requirement IDs defined more than once: {', '.join(dup[:10])}"))
    ids = re.findall(r"\b(REQ-[A-Z0-9][A-Z0-9_.-]*[A-Z0-9])", text)
    if len(ids) < 5:
        out.append(_f("warning", f"only {len(ids)} requirement IDs like [REQ-FUNC-001]"))
    normative = idx["stats"]["normative"]
    if normative < 10:
        out.append(_f("warning", f"only {normative} normative sentences (shall/must/should)"))
    return {"findings": out, "ports": len(ports), "parameters": len(params), "requirements": len(set(ids)),
            "normative": normative, "sections": idx["stats"]["sections"]}


def draft(description: str, ip: str, top: str, backend, log_dir: Path, work: Path, *, model: str = "opus",
          rounds: int = 2) -> dict:
    """A0 writes the specification; the shape check runs on each answer. Returns the report and the text."""
    template = TEMPLATE.read_text(encoding="utf-8")
    base = (f"Write the design specification of the IP `{ip}` (top module `{top}`) from the DESCRIPTION below, "
            f"in the shape of the TEMPLATE (follow its rules for the text). Fill every section; a section that does "
            f"not apply says so in one sentence. Use the top module name `{top}` in the port-table caption. Give "
            "every requirement an ID. Write `markdown` = the whole specification.\n\n"
            f"DESCRIPTION (written by the designer)\n\"\"\"\n{description.strip()}\n\"\"\"\n\nTEMPLATE\n\"\"\"\n{template}\n\"\"\"\n")
    usage, history, extra = Usage(), [], ""
    work.mkdir(parents=True, exist_ok=True)
    spec_path = work / "spec_draft.md"
    res_check: dict = {}
    out: dict = {}
    for attempt in range(rounds + 1):
        res = backend.run(AgentTask(f"A0_spec_r{attempt}", base + extra, SCHEMA, system_prompt=SYSTEM_PROMPT,
                                    model=model, max_turns=4), log_dir)
        usage.add(res)
        out = res.output
        spec_path.write_text(out["markdown"].rstrip() + "\n", encoding="utf-8")
        res_check = check_spec(spec_path, top)
        errs = [f for f in res_check["findings"] if f["severity"] in ("error", "warning")]
        history.append({"attempt": attempt, "errors": sum(f["severity"] == "error" for f in errs),
                        "warnings": sum(f["severity"] == "warning" for f in errs)})
        if not errs:
            break
        extra = ("\n\nYOUR PREVIOUS SPECIFICATION HAS THESE PROBLEMS (the flow could not read it as needed). Return "
                 "the whole corrected specification.\n" + "\n".join(f"- [{f['severity']}] {f['message']}" for f in errs)
                 + f"\n\nPREVIOUS SPECIFICATION\n\"\"\"\n{out['markdown']}\n\"\"\"\n")
    return {"markdown": out.get("markdown", ""), "assumptions": out.get("assumptions", []),
            "open_questions": out.get("open_questions", []), "check": res_check, "history": history,
            "usage": usage.as_dict(), "model": model, "prompt_version": PROMPT_VERSION}


def report_md(rep: dict, ip: str, spec_file: str) -> str:
    c = rep["check"]
    lines = [f"# Specification draft: {ip}", "", f"Agent A0 ({rep['model']}, {rep['prompt_version']}) wrote "
             f"`{spec_file}` from the designer's description in {len(rep['history'])} attempt(s), cost "
             f"US${rep['usage'].get('cost_usd', 0):.2f}.", "",
             "**This is a proposal.** Read it, correct it, and answer the open questions in the text before running "
             "the flow: the verification and the RTL are generated from this text only. Gate G1 records its hash.", "",
             f"Shape check: {c.get('sections')} sections, {c.get('ports')} ports, {c.get('parameters')} parameters, "
             f"{c.get('requirements')} requirement IDs, {c.get('normative')} normative sentences.", ""]
    if c.get("findings"):
        lines += ["Remaining findings:", ""] + [f"- {f['severity']}: {f['message']}" for f in c["findings"]] + [""]
    lines += ["## Assumptions A0 made (the description did not say)", ""]
    lines += [f"- {a}" for a in rep["assumptions"]] or ["- none"]
    lines += ["", "## Open questions for the designer", ""]
    lines += [f"- {q}" for q in rep["open_questions"]] or ["- none"]
    return "\n".join(lines) + "\n"

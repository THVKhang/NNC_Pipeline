"""Rewrite an existing RTL to follow docs/RTL_RULES.md, proven equivalent to the original (`nnc restyle`).

Agent A16 receives the delivered RTL, the rules, the interface and the approved requirements (for the
`// REQ:` tags). It rewrites the RTL without changing its behaviour: same top module, same ports and
parameters, the same value on every output in every cycle. It must not fix anything: a construct that looks
like a bug is reported in `suspected_bugs`, and the decision stays with the designer (the RTL of a
delivered design is never changed by the flow).

Each answer goes through the code checks of nnc/rtlcheck.py and then through a formal sequential
equivalence check against the original (nnc/equiv.py). A rule violation or an output difference goes back
to the agent. The result is written to designs/<ip>/restyle/ (rtl/, restyle.json, restyle.md); rtl/ of the
design is not touched. A person decides whether to adopt it.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from nnc import equiv, rtlcheck
from nnc.agents.backend import READ_ONLY_TOOLS, AgentTask
from nnc.agents.runtime import Usage
from nnc.gen_rtl import RULES_DOC, blocking, interface_md, requirements_md, _problems
from nnc.simhost import SimHost

PROMPT_VERSION = "restyle-v1"
SYSTEM_PROMPT = (
    "You are an RTL design engineer rewriting existing SystemVerilog to follow a set of design rules. You "
    "never change behaviour: every output must keep the same value in every clock cycle for every input "
    "sequence. You do not fix bugs; you report what looks wrong. Return the answer in the required JSON structure."
)
SCHEMA = {
    "type": "object", "required": ["files", "filelist", "suspected_bugs", "open_points"], "additionalProperties": False,
    "properties": {
        "files": {"type": "array", "items": {
            "type": "object", "required": ["name", "content"], "additionalProperties": False,
            "properties": {"name": {"type": "string", "pattern": r"^[A-Za-z_][A-Za-z0-9_]*\.sv$"},
                           "content": {"type": "string", "minLength": 20}}}},
        "remove": {"type": "array", "items": {"type": "string"}},
        "filelist": {"type": "array", "minItems": 1, "items": {"type": "string"}},
        "suspected_bugs": {"type": "array", "items": {
            "type": "object", "required": ["where", "what"], "additionalProperties": False,
            "properties": {"where": {"type": "string"}, "what": {"type": "string"}}}},
        "open_points": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"}},
}

TASK = """# Task: rewrite the RTL of `{top}` to follow RTL_RULES.md, without changing its behaviour

Files in this folder:
- `original/`: the RTL to rewrite ({files}).
- `RTL_RULES.md`: the design rules. Code checks run on your answer.
- `INTERFACE.md`: the parameters and ports of the top module (they must not change).
- `REQUIREMENTS.md`: the approved requirements, for the `// REQ: <rule id>` tags.
{current}
Hard constraints:
- Behaviour is unchanged: for every input sequence after reset, every output has the same value in every
  cycle as in `original/`. A formal equivalence check (gold = original, gate = yours) verifies this.
- Same top module name, ports, parameters and defaults. Submodules may be merged, split or renamed.
- Registers without reset in the original stay without reset; registers with reset keep their reset value.
- Do NOT fix bugs. If something looks wrong (a value read before it is assigned, an unreachable state, a
  width mismatch...), keep the behaviour and report it in `suspected_bugs` (file:line of the original, what).
- Simulation-only code (inside `ifndef/ifdef ...SYNTHESIS`) stays simulation-only, unchanged in behaviour.

Answer with `files` (the {files_what}), `remove`, `filelist` (compile order, `{top}.sv` last),
`suspected_bugs`, and `open_points` (rules you could not meet without changing behaviour, and why).
{problems}"""


def restyle(d_root: Path, contract: dict, rules_doc: dict, values: dict[str, int], original: dict[str, str],
            backend, log_dir: Path, host: SimHost, *, model: str = "opus", rounds: int = 3, depth: int = 20,
            max_turns: int = 60) -> dict:
    out_dir = d_root / "restyle"
    work = out_dir / "work"
    if work.exists():
        shutil.rmtree(work)
    (work / "original").mkdir(parents=True)
    for n, t in original.items():
        (work / "original" / n).write_text(t, encoding="utf-8")
    (work / "REQUIREMENTS.md").write_text(requirements_md(rules_doc), encoding="utf-8")
    (work / "INTERFACE.md").write_text(interface_md(contract, {"values": values}), encoding="utf-8")
    rule_ids = {r["id"] for r in rules_doc["rules"]}
    gold_order = rtlcheck.filelist_findings(original, contract["top"])[1]
    macros = sorted({m for n in gold_order for m, _ in rtlcheck.sim_only(rtlcheck.strip_comments(original[n]))[1]})
    files: dict[str, str] = {}
    usage, history = Usage(), []
    problems, chk, eq = "", {}, {}
    status, bugs, open_points = "failed", [], []
    for attempt in range(rounds + 1):
        inputs = {f"original/{n}": work / "original" / n for n in original}
        inputs.update({"RTL_RULES.md": RULES_DOC, "INTERFACE.md": work / "INTERFACE.md",
                       "REQUIREMENTS.md": work / "REQUIREMENTS.md"})
        cur = work / f"current_r{attempt}"
        for n, t in files.items():
            cur.mkdir(parents=True, exist_ok=True)
            (cur / n).write_text(t, encoding="utf-8")
            inputs[f"current/{n}"] = cur / n
        text = TASK.format(top=contract["top"], files=", ".join(sorted(original)),
                           current=(f"- `current/`: your previous rewrite ({', '.join(sorted(files))}); correct it.\n"
                                    if files else ""),
                           files_what="files you changed or added" if files else "rewritten files",
                           problems=f"\n## Problems in your previous rewrite\n\n{problems}\n" if problems else "")
        res = backend.run(AgentTask(f"A16_restyle_r{attempt}", text, SCHEMA, inputs=inputs,
                                    forbidden=[d_root / "verif"], tools=READ_ONLY_TOOLS, system_prompt=SYSTEM_PROMPT,
                                    model=model, max_turns=max_turns), log_dir)
        usage.add(res)
        o = res.output
        for f in o["files"]:
            files[f["name"]] = f["content"] if f["content"].endswith("\n") else f["content"] + "\n"
        for n in o.get("remove") or []:
            files.pop(n, None)
        files["filelist.f"] = "// filelist.f - restyled RTL (nnc restyle, agent A16)\n" + "\n".join(o["filelist"]) + "\n"
        bugs, open_points = o.get("suspected_bugs") or [], o.get("open_points") or []
        chk = rtlcheck.check(host, files, contract, values, rule_ids)
        entry = {"attempt": attempt, "counts": chk["counts"], "cost_usd": res.cost_usd}
        problems = _problems(blocking(chk["findings"]))
        if not any(f["severity"] == "error" for f in chk["findings"]):
            gate_order = chk["order"]
            eq = equiv.run(host, contract, values, original, gold_order, {n: files[n] for n in gate_order}, gate_order,
                           defines=macros, depth=depth)
            entry["equivalence"] = eq["status"]
            if eq["status"] == "CEX":
                problems += ("\n- [error] EQUIVALENCE: behaviour changed: " + equiv.cex_outputs(eq["trace"], contract)
                             + ". Find the change that causes it and restore the original behaviour.")
            elif eq["status"] == "ERROR":
                problems += "\n- [error] EQUIVALENCE: the equivalence check could not be built: " + eq["detail"][:600]
        history.append(entry)
        if not blocking(chk["findings"]) and eq.get("status") in ("PROVEN", "BOUNDED"):
            status = "clean"
            break
    return {"status": status, "equivalence": {k: v for k, v in eq.items() if k != "out_dir"}, "attempts": len(history),
            "history": history, "files": files, "findings": chk.get("findings", []), "counts": chk.get("counts", {}),
            "trace": chk.get("trace", {}), "synth": chk.get("synth", {}), "suspected_bugs": bugs,
            "open_points": open_points, "usage": usage.as_dict(), "model": model, "prompt_version": PROMPT_VERSION,
            "macros": macros}


def write(d_root: Path, rep: dict, original_check: dict, design: str) -> None:
    out = d_root / "restyle"
    rtl = out / "rtl"
    if rtl.exists():
        shutil.rmtree(rtl)
    rtl.mkdir(parents=True)
    for n, t in rep["files"].items():
        (rtl / n).write_text(t, encoding="utf-8", newline="\n")
    data = {k: v for k, v in rep.items() if k != "files"}
    data["files"] = sorted(rep["files"])
    data["original_counts"] = original_check["counts"]
    (out / "restyle.json").write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    eq = rep["equivalence"]
    oc, nc = original_check["counts"], rep["counts"]
    lines = [f"# Restyled RTL: {design}", "",
             f"Status: **{rep['status']}** after {rep['attempts']} attempt(s) (agent A16, {rep['model']}); cost "
             f"US${rep['usage'].get('cost_usd', 0):.2f}. `rtl/` of the design is unchanged; the rewrite is in "
             "`restyle/rtl/`. Adopting it is the designer's decision.", "",
             "## Equivalence with the original", "",
             f"**{eq.get('status', 'not run')}** (BMC {eq.get('bmc')}, proof {eq.get('prove')}, depth {eq.get('depth')}). "
             "PROVEN: every output equal in every cycle for every input sequence after reset, for this configuration; "
             "registers without reset start at 0 in both versions." + (f" Macros defined: {', '.join(rep['macros'])}."
                                                                         if rep["macros"] else ""), "",
             "## Rule findings (docs/RTL_RULES.md)", "", "| | Errors | Warnings | Notes |", "|---|---|---|---|",
             f"| original | {oc.get('error')} | {oc.get('warning')} | {oc.get('info')} |",
             f"| restyled | {nc.get('error')} | {nc.get('warning')} | {nc.get('info')} |", ""]
    if rep["suspected_bugs"]:
        lines += ["## Suspected bugs in the original (not fixed: behaviour kept)", ""]
        lines += [f"- {b['where']}: {b['what']}" for b in rep["suspected_bugs"]] + [""]
    if rep["open_points"]:
        lines += ["## Open points", ""] + [f"- {p}" for p in rep["open_points"]] + [""]
    if rep["findings"]:
        lines += ["## Remaining findings", ""] + [f"- {f['severity']} {f['rule']} {f['file']}:{f['line']} {f['message']}"
                                                 for f in rep["findings"]] + [""]
    (out / "restyle.md").write_text("\n".join(lines), encoding="utf-8")

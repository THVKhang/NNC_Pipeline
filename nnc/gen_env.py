"""Formal environment generation (agent A13): the input obligations of the DUT's environment.

A formal tool drives the DUT inputs with every possible sequence. Many of them break the protocol the
specification requires from the environment (a requester that drops PSEL in an Access cycle, a
response without a request), and a counterexample built on one is not a design bug. A13 writes these
obligations as assumptions, from the specification only (rules, contract interface, never the RTL),
in the subset the open-source Yosys frontend accepts: immediate `assume` statements in `always`
blocks, with helper registers.

Code writes the header (`module nnc_env` with every interface port as an input, contract parameters)
and checks the body: assumptions only (no assert, no cover, no initial, no $display), at least one,
each labelled `// ENV-nn: <obligation> (<rule ids>)`; then Yosys elaborates it alone and errors go
back to the agent. The file is `verif/formal/nnc_env.sv`, covered by gate G3: a person must approve
the assumptions, because an assumption that is too strong hides real bugs (the formal stage also
reports a check as VACUOUS when its antecedent can no longer occur).
"""
from __future__ import annotations

import re
from pathlib import Path

from nnc.agents.backend import AgentTask
from nnc.agents.runtime import Usage
from nnc.contract import module_header
from nnc.simhost import SimHost

PROMPT_VERSION = "env-v1"
SYSTEM_PROMPT = (
    "You are a formal-verification engineer writing the environment constraints of a block: what the "
    "specification requires from the blocks driving its inputs. You use only the specification text and "
    "the interface you are given; you never assume anything about the implementation. A constraint that is "
    "too strong hides bugs, so you constrain only what the specification obliges. Return the answer in the "
    "required JSON structure."
)
SCHEMA = {
    "type": "object", "required": ["body", "assumptions"], "additionalProperties": False,
    "properties": {
        "body": {"type": "string", "minLength": 20},
        "assumptions": {"type": "array", "items": {
            "type": "object", "required": ["id", "obligation", "rules"], "additionalProperties": False,
            "properties": {"id": {"type": "string"}, "obligation": {"type": "string"},
                           "rules": {"type": "array", "items": {"type": "string"}}}}},
        "notes": {"type": "string"}},
}

RULES_TEXT = """CODING RULES (Yosys `read_verilog -sv -formal`, open-source frontend)
- Write ONLY the module body (the header above exists; no `module`/`endmodule`).
- Constraints are immediate assumptions:  always @(posedge CLK) if (COND) assume (EXPR);
  or combinational: always @(*) assume (EXPR);  Use `$past(x)`, `$stable(x)`, `$rose`, `$fell` only
  inside `always @(posedge CLK)`. Concurrent `assume property`, sequences, `|->`, `##` are NOT accepted.
- Helper registers are allowed (for example "transfer in progress"): declare `reg`/`logic`, update them in
  `always @(posedge CLK)` from interface signals only, with the DUT reset; give them an initial value (= 0).
- Constrain the INPUTS of the DUT. An output may appear in the condition (for example "hold PSEL until
  PREADY"), never as the constrained value.
- Only obligations the specification places on the environment: protocol sequencing, stability while
  waiting, legal encodings, static configuration inputs (stable after reset), reset sequencing. Do NOT
  assume what the DUT must do, and do not exclude inputs the specification calls legal (an error
  response, back-pressure, a protocol error the DUT must detect and report).
- The resets are already assumed active in the initial state; do not repeat that.
{async_rules}- Label each assumption with a comment `// ENV-01: <obligation> (<rule ids>)` and list the same in
  `assumptions`. No assert, cover, initial, $display, hierarchical names, or signals outside the interface.
"""


def header(iface: dict) -> str:
    return ("// Formal environment: obligations of the DUT's environment (agent A13, from the specification).\n"
            "// Reviewed at gate G3: an assumption that is too strong hides real bugs.\n"
            + module_header("nnc_env", iface, all_inputs=True))


ASYNC_RULES = """- ASYNCHRONOUS CLOCKS: the formal tool runs every clock as a free input (any ratio and phase) on a
  global time step, and an input may change between two clock edges. Obligations about WHEN an input may
  change relative to a clock (a reset released synchronously to its clock, two resets asserted together,
  a minimum pulse width) are written on the global clock:
      always @($global_clock) if ($rose(i_rst_n_x)) assume ($rose(i_clk_x));
  `$global_clock`, `$rose`, `$fell`, `$past`, `$stable` are allowed there. Helper registers that follow
  such events are also updated on `always @($global_clock)`.
"""


def build_prompt(contract: dict, rules_doc: dict, feedback: list[dict] | None = None,
                 current: str | None = None) -> str:
    iface = contract["interface"]
    ports = "\n".join(f"  {p['name']} ({p['direction']} of the DUT, width {p['width']}): {p.get('meaning', '')}"
                      for p in iface["ports"])
    clocks = ", ".join(c["name"] for c in iface.get("clocks") or []) or iface.get("clock") or ""
    rules = "\n".join(f"  {r['id']}: {r['statement']}" for r in rules_doc["rules"])
    return (f"INTERFACE (directions as seen by the DUT; constrain the inputs)\n{ports}\n"
            f"Clocks: {clocks}. Clock relation: {iface.get('clock_relation') or 'synchronous'}.\n\n"
            f"EXISTING HEADER\n```systemverilog\n{header(iface)}\n```\n\n"
            f"REQUIREMENTS OF THE SPECIFICATION (rules; the ones about what drives the inputs are the "
            f"environment's obligations)\n{rules}\n\n"
            + RULES_TEXT.replace("{async_rules}", ASYNC_RULES if iface.get("clock_relation") == "async" else "")
            + (_feedback_text(feedback, current) if feedback else ""))


def _feedback_text(feedback: list[dict], current: str | None) -> str:
    """Counterexamples that triage classified E (an environment obligation missing), with the rules it named.
    The agent adds an assumption only where the specification really places the obligation."""
    items = "\n".join(f"- {a['check']}: {a['what_happens'][:900]}\n  Suggested: {a['options'][:700]}" for a in feedback)
    return ("\n\nCOUNTEREXAMPLES CLASSIFIED 'ENVIRONMENT OBLIGATION MISSING' BY TRIAGE (formal run with the current "
            "environment below). For each, check in the rules whether the specification really obliges the "
            "environment; if so, add the assumption (citing the rule), otherwise leave it out: a counterexample on a "
            "legal input sequence is a real finding and must stay.\n" + items +
            (f"\n\nCURRENT ENVIRONMENT BODY (keep what is right, extend it)\n```systemverilog\n{current}\n```" if current else ""))


def validate_body(body: str) -> list[str]:
    problems = []
    code = re.sub(r"//[^\n]*", "", body)
    for word, why in (("assert", "an environment never asserts"), ("cover", "no cover in the environment"),
                      ("initial", "no initial block (give registers an initial value instead)"),
                      ("$display", "no $display"), ("property", "concurrent properties are not accepted"),
                      ("module", "write only the body")):
        if re.search(rf"(?<![\w$]){re.escape(word)}(?!\w)", code):
            problems.append(f"`{word}` found: {why}")
    if "##" in code:
        problems.append("`##` found: no sequence delays")
    if not re.search(r"\bassume\s*\(", code):
        problems.append("no assume statement")
    labels = set(re.findall(r"//\s*(ENV-\d+)", body))
    if not labels:
        problems.append("no `// ENV-nn:` label")
    return problems


def lint(host: SimHost, code: str) -> tuple[bool, str]:
    script = ("yosys -q -p 'read_verilog -sv -formal nnc_env.sv; hierarchy -top nnc_env; proc' > yosys.log 2>&1; "
              "echo NNC_RC=$? >> yosys.log; cat yosys.log")
    res = host.run({"nnc_env.sv": code}, script, [], timeout_s=300, tag="envlint")
    ok = "NNC_RC=0" in res.output
    errs = [ln for ln in res.output.splitlines() if "ERROR" in ln or "rror:" in ln]
    return ok, "\n".join(errs[:20] if errs else res.output.splitlines()[-15:])


def generate(contract: dict, rules_doc: dict, backend, log_dir: Path, host: SimHost | None, out_file: Path, *,
             model: str = "opus", rounds: int = 3, feedback: list[dict] | None = None) -> dict:
    head = header(contract["interface"])
    current = None
    if feedback and out_file.is_file():
        text = out_file.read_text(encoding="utf-8")
        current = text[text.index(");") + 2:text.rindex("endmodule")].strip("\n") if ");" in text else None
    prompt = build_prompt(contract, rules_doc, feedback, current)
    usage, history = Usage(), ""
    status, problems, lint_err, out = "failed", [], "", {}
    for attempt in range(rounds + 1):
        res = backend.run(AgentTask(f"A13_env{'_fb' if feedback else ''}_r{attempt}", prompt + history, SCHEMA,
                                    system_prompt=SYSTEM_PROMPT,
                                    model=model, max_turns=4), log_dir)
        usage.add(res)
        out = res.output
        body = out["body"].strip("\n")
        code = f"{head}\n\n{body}\nendmodule\n"
        problems = validate_body(body)
        unknown = sorted(set(sum((a["rules"] for a in out["assumptions"]), [])) - {r["id"] for r in rules_doc["rules"]})
        if unknown:
            problems.append(f"unknown rule ids {unknown[:8]}")
        ok, lint_err = (True, "") if host is None or problems else lint(host, code)
        if not problems and ok:
            status = "lint_clean" if host else "not_linted"
            break
        history = (f"\n\nYOUR PREVIOUS BODY (attempt {attempt + 1}) FAILED.\n```systemverilog\n{body}\n```\nPROBLEMS:\n"
                   + "\n".join(problems) + (f"\nYOSYS ERRORS:\n{lint_err}" if lint_err else "")
                   + "\nReturn a corrected complete body.")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(code, encoding="utf-8")
    return {"file": str(out_file), "status": status, "attempts": attempt + 1, "problems": problems,
            "lint_errors": lint_err, "assumptions": out.get("assumptions", []), "usage": usage.as_dict(),
            "prompt_version": PROMPT_VERSION}

"""SVA checker generation (stage 3, agent A5), one checker module per check group.

Code writes the fixed parts so they cannot be wrong: the module header (contract parameters, every
interface port as an input), one fail and one hit counter per check, and the final block that prints
`NNC_CHECK <id> hits=<n> fails=<n>` for the report. The agent writes only the body: helper logic,
one labelled assertion per check whose else-branch increments the fail counter, and an always_ff that
increments the hit counter when the antecedent is true. The module is then linted with Verilator; the
errors go back to the agent (no RTL is ever shown) for at most `rounds` repairs.
"""
from __future__ import annotations

import re
from pathlib import Path

from nnc.agents.backend import AgentTask
from nnc.agents.runtime import Usage
from nnc.contract import module_header
from nnc.simhost import SimHost, lint_sv

PROMPT_VERSION = "sva-v1"

SYSTEM_PROMPT = (
    "You are an expert in SystemVerilog Assertions writing interface checkers that must compile in "
    "Verilator 5. You use only the interface signals given and the check text; you never assume "
    "anything about the DUT implementation. Return the answer in the required JSON structure."
)
SCHEMA = {
    "type": "object", "required": ["body"], "additionalProperties": False,
    "properties": {"body": {"type": "string", "minLength": 20}, "notes": {"type": "string"}},
}

RULES_TEXT = """CODING RULES (the simulator is Verilator 5.055)
- Write ONLY the module body. The header, the counters and the final block below already exist; do not
  repeat them and do not write `module`/`endmodule`.
- For every check {id} write exactly:
    a_{u}: assert property (@(posedge {clk}) disable iff ({rst_off}) ANTECEDENT |-> CONSEQUENT)   // or |=>
      else begin fails_{u}++; $display("NNC_FAIL {id} @%0t", $time); end
    always_ff @(posedge {clk}) if (!({rst_off}) && (ANTECEDENT)) hits_{u} <= hits_{u} + 1;
  where {u} is the ID with '-' replaced by '_'. The hit condition is the antecedent: the cycle in which the
  check is really exercised (for an invariant, the cycle where it is meaningful, e.g. the valid signal).
- Checks about values DURING reset: do not use disable iff; antecedent = reset asserted; and count hits.
- Allowed: |->, |=>, ##N with a constant N, $past, $stable, $rose, $fell, $countones, helper registers
  and counters you declare (always_ff on the same clock, reset like the DUT reset). Prefer a helper
  register (e.g. "request outstanding") over a complex sequence.
- Not allowed: cover property with action statements, sequence local variables, ##[m:$], first_match,
  intersect, throughout, $fatal, $error, $stop, $finish, `bind`, hierarchical references, any signal
  that is not in the interface, initial blocks with delays.
- Every helper signal is driven only from interface signals. Declare before use. Use parameters by name.
- Put a comment `// {id}: <title> (<rule ids>)` above each assertion. No comment may start with the
  word "verilator".
"""


def module_name(group: str) -> str:
    return f"nnc_chk_{group}"


def _u(cid: str) -> str:
    return cid.replace("-", "_")


def scaffold(group: str, iface: dict, checks: list[dict]) -> tuple[str, str]:
    """(head, tail): header + counters, and final block + endmodule."""
    head = [module_header(module_name(group), iface, all_inputs=True), ""]
    for c in checks:
        head.append(f"  int unsigned fails_{_u(c['id'])} = 0;")
        head.append(f"  int unsigned hits_{_u(c['id'])} = 0;")
    tail = ["", "  final begin"]
    tail += [f'    $display("NNC_CHECK {c["id"]} hits=%0d fails=%0d", hits_{_u(c["id"])}, fails_{_u(c["id"])});'
             for c in checks]
    tail += ["  end", "endmodule", ""]
    return "\n".join(head), "\n".join(tail)


def _reset_off(iface: dict) -> str:
    r = iface.get("reset")
    if not r:
        return "1'b0"
    return f"!{r['name']}" if r["active_low"] else r["name"]


def build_prompt(group: str, iface: dict, checks: list[dict], rules_by_id: dict) -> str:
    head, tail = scaffold(group, iface, checks)
    ports = "\n".join(f"  {p['name']} ({p['direction']} of the DUT, width {p['width']}): {p['meaning']}"
                      for p in iface["ports"])
    lines = []
    for c in checks:
        quotes = "; ".join(f"{r}: {rules_by_id[r]['quote'][:300]}" for r in c["rules"] if r in rules_by_id)
        lines.append(f"[{c['id']}] {c['title']} (rules {', '.join(c['rules'])})\n  BEHAVIOR: {c['behavior']}\n"
                     f"  SOURCE: {quotes}")
    rules = RULES_TEXT.replace("{clk}", iface["clock"] or "clk").replace("{rst_off}", _reset_off(iface))
    return (f"INTERFACE (all are inputs of the checker; directions are as seen by the DUT)\n{ports}\n\n"
            f"EXISTING CODE (header and counters)\n```systemverilog\n{head}\n```\n"
            f"EXISTING CODE (end)\n```systemverilog\n{tail}\n```\n\n"
            f"CHECKS of group '{group}' ({len(checks)})\n" + "\n".join(lines) + f"\n\n{rules}")


def validate_body(body: str, checks: list[dict]) -> list[str]:
    problems = []
    if re.search(r"^\s*(module|endmodule)\b", body, re.M):
        problems.append("the body must not contain module/endmodule")
    for bad in ("$fatal", "$error", "$stop", "$finish", " bind ", "##[", "first_match", "intersect"):
        if bad in body:
            problems.append(f"forbidden construct {bad.strip()}")
    if re.search(r"//\s*verilator", body, re.I):
        problems.append("a comment starts with the word verilator")
    for c in checks:
        u = _u(c["id"])
        if not re.search(rf"\ba_{u}\s*:", body):
            problems.append(f"missing assertion label a_{u} for {c['id']}")
        if f"fails_{u}++" not in body.replace(" ", ""):
            problems.append(f"{c['id']}: the else branch must do fails_{u}++")
        if not re.search(rf"hits_{u}\s*<=\s*hits_{u}\s*\+\s*1", body):
            problems.append(f"{c['id']}: missing hit counter update hits_{u} <= hits_{u} + 1")
    return problems


def generate(contract: dict, rules_doc: dict, backend, log_dir: Path, host: SimHost | None, out_dir: Path, *,
             model: str | None = "sonnet", rounds: int = 3) -> dict:
    iface = contract["interface"]
    rules_by_id = {r["id"]: r for r in rules_doc["rules"]}
    groups: dict[str, list[dict]] = {}
    for c in contract["checks"]:
        if c["kind"] == "assertion":
            groups.setdefault(c["group"], []).append(c)
    out_dir.mkdir(parents=True, exist_ok=True)
    usage = Usage()
    report = {"modules": [], "usage": None}
    for group, checks in sorted(groups.items()):
        head, tail = scaffold(group, iface, checks)
        prompt = build_prompt(group, iface, checks, rules_by_id)
        history = ""
        status, problems, lint_err = "failed", [], ""
        for attempt in range(rounds + 1):
            task = AgentTask(f"A5_sva_{group}_r{attempt}", prompt + history, SCHEMA, system_prompt=SYSTEM_PROMPT,
                             model=model, max_turns=4)
            res = backend.run(task, log_dir)
            usage.add(res)
            body = res.output["body"].strip("\n")
            code = f"{head}\n\n{body}\n{tail}"
            problems = validate_body(body, checks)
            lint_ok, lint_err = (True, "") if host is None else lint_sv(host, {f"{module_name(group)}.sv": code},
                                                                         module_name(group))
            if not problems and lint_ok:
                status = "lint_clean" if host else "not_linted"
                break
            history = (f"\n\nYOUR PREVIOUS BODY (attempt {attempt + 1}) FAILED.\n```systemverilog\n{body}\n```\n"
                       f"PROBLEMS:\n" + "\n".join(problems) + (f"\nVERILATOR ERRORS:\n{lint_err}" if lint_err else "") +
                       "\nReturn a corrected complete body.")
        path = out_dir / f"{module_name(group)}.sv"
        path.write_text(code, encoding="utf-8")
        report["modules"].append({"group": group, "module": module_name(group), "file": path.name,
                                  "checks": [c["id"] for c in checks], "status": status, "attempts": attempt + 1,
                                  "problems": problems, "lint_errors": lint_err})
    report["usage"] = usage.as_dict()
    report["prompt_version"] = PROMPT_VERSION
    return report

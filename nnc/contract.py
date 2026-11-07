"""Verification contract (stage 2, agent A4): approved rules -> interface + check plan.

* Interface (code, no LLM): ports, directions, widths, clock, reset and parameters come from the
  port and parameter tables of the IP specification. The RTL is never read here (principle PR-1).
* Check plan (A4, deep model): every kept rule is mapped to at least one check, or declared not
  verifiable by simulation with a reason. A check is either an `assertion` (cycle property on the
  interface, written by the SVA writer) or a `test` (stimulus + expected result, written by the
  cocotb test writer). Code validates the mapping; rules left over get one gap-fill call; checks are
  renumbered CHK-001... in a stable order.
Output: work/contract.json (the Gate 2 artifact), work/contract.md (review sheet) and
work/contract_shell.sv (an empty module with the contract interface, for compile checks).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from nnc.agents.backend import AgentTask
from nnc.agents.runtime import Usage

PROMPT_VERSION = "contract-v1"
NOT_VERIFIED = ["not_applicable_to_dut", "static_or_structural", "not_observable_at_interface",
                "design_guideline", "covered_by_other_check"]

SYSTEM_PROMPT = (
    "You are a principal verification engineer. You turn approved specification rules into a precise, "
    "RTL-independent verification plan for one design under test, using only its interface signals. "
    "You never guess implementation details. Return the answer in the required JSON structure."
)

SCHEMA = {
    "type": "object",
    "required": ["checks", "not_verified", "assumptions"],
    "additionalProperties": False,
    "properties": {
        "checks": {"type": "array", "items": {
            "type": "object",
            "required": ["id", "kind", "group", "title", "rules", "behavior", "stimulus", "expected"],
            "additionalProperties": False,
            "properties": {
                "id": {"type": "string", "pattern": r"^CHK-[0-9]{3}$"},
                "kind": {"type": "string", "enum": ["assertion", "test"]},
                "group": {"type": "string", "pattern": r"^[a-z][a-z0-9_]{0,15}$"},
                "title": {"type": "string"},
                "rules": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                "behavior": {"type": "string", "minLength": 10},
                "stimulus": {"type": "string"},
                "expected": {"type": "string"},
            }}},
        "not_verified": {"type": "array", "items": {
            "type": "object", "required": ["rule", "reason", "note"], "additionalProperties": False,
            "properties": {"rule": {"type": "string"}, "reason": {"type": "string", "enum": NOT_VERIFIED},
                           "note": {"type": "string"}}}},
        "assumptions": {"type": "array", "items": {"type": "string"}},
    },
}

TASK_TEXT = """TASK
Write the verification plan of the DUT whose INTERFACE is given, from the RULES.
1. Every rule must appear in at least one check (field "rules") or in "not_verified" with a reason:
   not_applicable_to_dut (binds another component, or a feature the DUT does not have),
   static_or_structural (lint, structure, synthesis, DFT: not a simulation property),
   not_observable_at_interface, design_guideline (advice with nothing to observe),
   covered_by_other_check (say which in "note").
   Standard-protocol rules apply in the DUT's role (for example the rules of a host for a host port);
   rules that bind the other side become stimulus constraints of the tests, not DUT checks.
2. kind = "assertion": a property checked every cycle from INTERFACE signals only, with an exact
   cycle relation in "behavior" (antecedent, consequent, delay; name the ports; e.g. "if o_x=1 and
   i_y=0 at a rising edge, then at the next rising edge o_x=1 and o_d is unchanged"). Leave stimulus
   and expected empty.
   kind = "test": a directed or random scenario: "stimulus" says what the test drives (legal stimulus
   only, unless the rule is about illegal input), "expected" gives exact observable results and cycle
   counts. Group several closely related rules into one test where natural.
3. group: a short lowercase name of the interface or concern the check belongs to (e.g. apb, tlul,
   cross, reset); assertions of one group become one checker module.
4. Use only the interface signal names below, exact parameter names, and values from the rules.
   Reset values and constants are checkable. Write timing relative to the active clock edge.
5. A test runs in ONE simulation of ONE parameter configuration through the interface. Parameter
   sweeps, elaboration errors for illegal parameters, lint, structure and synthesis properties are not
   simulation tests: put such rules in not_verified (static_or_structural) instead of a check.
6. List assumptions you had to make (should be few; prefer not_verified to guessing).
Number checks CHK-001, CHK-002, ... in any order.
"""


# --------------------------------------------------------------------------------------- interface
def _find_table(index: dict, *needles: str) -> dict | None:
    for t in index.get("tables", []):
        head = [h.lower() for h in t["header"]]
        if all(any(n in h for h in head) for n in needles):
            return t
    return None


def _col(header: list[str], *names: str) -> int | None:
    for i, h in enumerate(header):
        if any(n in h.lower() for n in names):
            return i
    return None


def extract_interface(index: dict) -> dict:
    """Ports and parameters from the tables of an IP specification index."""
    pt = _find_table(index, "port", "direction", "width")
    if pt is None:
        raise ValueError("no port table (columns Port, Direction, Width) found in the IP specification")
    h = pt["header"]
    c_name, c_dir, c_w = _col(h, "port"), _col(h, "direction"), _col(h, "width")
    c_type, c_reset, c_mean = _col(h, "signal type", "type"), _col(h, "reset"), _col(h, "meaning", "description")
    ports = []
    for row in pt["rows"]:
        if len(row) <= max(c_name, c_dir, c_w):
            continue
        name = row[c_name].strip()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            continue
        d = row[c_dir].lower()
        direction = "inout" if "inout" in d else "input" if d.startswith("in") else "output" if d.startswith("out") else None
        if direction is None:
            continue
        ports.append({
            "name": name, "direction": direction, "width": row[c_w].strip(),
            "type": row[c_type] if c_type is not None and c_type < len(row) else "",
            "reset_value": row[c_reset] if c_reset is not None and c_reset < len(row) else "",
            "meaning": row[c_mean] if c_mean is not None and c_mean < len(row) else "",
        })
    params = []
    tt = _find_table(index, "parameter", "default")
    if tt is not None:
        ph = tt["header"]
        cn, cd, cr = _col(ph, "parameter"), _col(ph, "default"), _col(ph, "legal", "range")
        for row in tt["rows"]:
            name = row[cn].strip() if cn is not None and cn < len(row) else ""
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
                params.append({"name": name, "default": row[cd].strip() if cd is not None else "",
                               "legal": row[cr].strip() if cr is not None and cr < len(row) else ""})

    def pick(kind: str, names: tuple[str, ...]) -> dict | None:
        for p in ports:
            if p["direction"] == "input" and (kind in p["type"].lower() or any(n in p["name"].lower() for n in names)):
                return p
        return None
    clk = pick("clock", ("clk", "clock"))
    rst = pick("reset", ("rst", "reset"))
    reset = None
    if rst is not None:
        low = bool(re.search(r"(_n\b|_n_|active[- ]low)", rst["name"] + " " + rst["meaning"] + " " + rst["type"], re.I))
        reset = {"name": rst["name"], "active_low": low}
    return {"ports": ports, "parameters": params, "clock": clk["name"] if clk else None, "reset": reset,
            "source_table": {"section": pt["section"], "line": pt["line"]}}


def width_decl(width: str) -> str:
    """'1' -> '', '32' -> '[31:0]', 'PARA_ADDR_W' -> '[PARA_ADDR_W-1:0]'."""
    w = width.strip()
    if w in ("", "1"):
        return ""
    if w.isdigit():
        return f"[{int(w) - 1}:0]"
    return f"[({w})-1:0]"


def _param_default(p: dict) -> str:
    d = p["default"].strip()
    if re.match(r"^\d+$", d):
        return d
    m = re.match(r"^(\d+)'[bdh][0-9a-fA-F_]+$", d)
    return d if m else ("0" if d in ("", "'0") else d)


def module_header(name: str, iface: dict, all_inputs: bool = False) -> str:
    """SystemVerilog header with the contract parameters and ports (all inputs for a checker)."""
    params = ",\n".join(f"  parameter int {p['name']} = {_param_default(p)}" for p in iface["parameters"])
    ports = []
    for p in iface["ports"]:
        direction = "input " if all_inputs or p["direction"] == "input" else p["direction"]
        ports.append(f"  {direction:<6} logic {width_decl(p['width']):<22} {p['name']}")
    head = f"module {name}" + (f" #(\n{params}\n)" if params else "")
    return head + " (\n" + ",\n".join(ports) + "\n);"


def contract_shell(top: str, iface: dict) -> str:
    """Interface-only stand-in of the DUT: outputs tied to 0. For compile checks, never for results."""
    lines = ["// Contract shell: interface of the verification contract with no behaviour.",
             "// Compile checks only; a run against it proves nothing about the DUT.",
             module_header(top, iface)]
    for p in iface["ports"]:
        if p["direction"] == "output":
            lines.append(f"  assign {p['name']} = '0;")
    lines.append("endmodule")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------------------- planning
def _iface_text(iface: dict, top: str) -> str:
    rows = [f"DUT top module: {top}",
            f"Clock: {iface['clock']} (rising edge)",
            f"Reset: {iface['reset']['name']} ({'active low' if iface['reset']['active_low'] else 'active high'})"
            if iface.get("reset") else "Reset: none found",
            "Parameters: " + ", ".join(f"{p['name']}={p['default']} ({p['legal']})" for p in iface["parameters"]),
            "Ports (name | direction | width | type | reset value | meaning):"]
    rows += [f"  {p['name']} | {p['direction']} | {p['width']} | {p['type']} | {p['reset_value']} | {p['meaning']}"
             for p in iface["ports"]]
    return "\n".join(rows)


def _rule_text(r: dict) -> str:
    refs = f" ({', '.join(r['spec_refs'])})" if r.get("spec_refs") else ""
    cond = f" WHEN {r['condition']}" if r.get("condition") else ""
    return (f"[{r['id']}]{refs} {r['strength']} actor={r['actor']} check={r['check']}: {r['statement']}{cond}\n"
            f"    QUOTE ({r.get('doc', '')} {r['section']}): {r['quote'][:700]}")


def _decisions_text(decisions: list[dict] | None) -> str:
    if not decisions:
        return ""
    lines = [f"- [{', '.join(q['rules'])}] Q: {q['question']}\n  DECISION ({q['decision']['by']}): {q['decision']['answer']}"
             for q in decisions]
    return ("\n\nDESIGNER DECISIONS (binding; they settle the open questions about these rules)\n" + "\n".join(lines))


def build_prompt(iface: dict, top: str, rules: list[dict], extra: str = "", decisions: list[dict] | None = None) -> str:
    return (f"INTERFACE\n{_iface_text(iface, top)}\n\nRULES ({len(rules)})\n" +
            "\n".join(_rule_text(r) for r in rules) + _decisions_text(decisions) + f"\n\n{TASK_TEXT}{extra}")


def plan(rules_doc: dict, iface: dict, top: str, backend, log_dir: Path, *, model: str | None = "opus",
         unreviewed_gates: list[str] | None = None) -> dict:
    rules = rules_doc["rules"]
    ids = {r["id"] for r in rules}
    dec = [q for q in rules_doc.get("questions", []) if q.get("decision")]
    usage = Usage()
    res = backend.run(AgentTask("A4_contract", build_prompt(iface, top, rules, decisions=dec), SCHEMA,
                                system_prompt=SYSTEM_PROMPT, model=model, max_turns=4), log_dir)
    usage.add(res)
    checks, not_verified, assumptions = list(res.output["checks"]), list(res.output["not_verified"]), \
        list(res.output["assumptions"])

    def covered() -> set[str]:
        return {x for c in checks for x in c["rules"]} | {n["rule"] for n in not_verified}

    gaps_first = sorted(ids - covered())
    if gaps_first:
        left = [r for r in rules if r["id"] in set(gaps_first)]
        extra = ("\nThese rules were left out of the plan. Add checks or not_verified entries for them only; "
                 "number new checks from CHK-900.\n")
        res2 = backend.run(AgentTask("A4_contract_gapfill", build_prompt(iface, top, left, extra, decisions=dec), SCHEMA,
                                     system_prompt=SYSTEM_PROMPT, model=model, max_turns=4), log_dir)
        usage.add(res2)
        checks += res2.output["checks"]
        not_verified += res2.output["not_verified"]
        assumptions += res2.output["assumptions"]

    unknown = sorted({x for c in checks for x in c["rules"] if x not in ids} | {n["rule"] for n in not_verified if n["rule"] not in ids})
    for c in checks:
        c["rules"] = [x for x in c["rules"] if x in ids]
    checks = [c for c in checks if c["rules"]]
    not_verified = [n for n in not_verified if n["rule"] in ids]
    # Stable numbering: assertions first, by group, then tests, each in the order given.
    order = sorted(range(len(checks)), key=lambda i: (checks[i]["kind"] != "assertion", checks[i]["group"], i))
    renum = []
    for n, i in enumerate(order, 1):
        c = dict(checks[i])
        c["id"] = f"CHK-{n:03d}"
        renum.append(c)
    still = sorted(ids - covered())
    return {
        "top": top,
        "interface": iface,
        "checks": renum,
        "not_verified": not_verified,
        "assumptions": assumptions,
        "decisions": [{"rules": q["rules"], "question": q["question"], **q["decision"]} for q in dec],
        "coverage": {"rules": len(ids), "in_checks": len({x for c in renum for x in c["rules"]}),
                     "not_verified": len({n["rule"] for n in not_verified}),
                     "uncovered_after_first_pass": len(gaps_first), "uncovered": still, "unknown_ids": unknown},
        "contract": {"prompt_version": PROMPT_VERSION, "model": model,
                     "date": datetime.now(timezone.utc).isoformat(timespec="seconds"), "usage": usage.as_dict(),
                     "rules_sha_source": rules_doc.get("sources", []), "unreviewed_gates": unreviewed_gates or []},
    }


def summarize(c: dict) -> str:
    cov = c["coverage"]
    kinds: dict[str, int] = {}
    for ch in c["checks"]:
        kinds[ch["kind"]] = kinds.get(ch["kind"], 0) + 1
    u = c["contract"]["usage"]
    return (f"interface: {len(c['interface']['ports'])} ports, {len(c['interface']['parameters'])} parameters, "
            f"clock {c['interface']['clock']}, reset {c['interface']['reset']}\n"
            f"checks: {len(c['checks'])} {kinds}  rules {cov['rules']}: in checks {cov['in_checks']}, not verified "
            f"{cov['not_verified']}, uncovered {len(cov['uncovered'])} (after first pass {cov['uncovered_after_first_pass']})"
            f", unknown IDs {len(cov['unknown_ids'])}\ncalls: {u['calls']} ({u['cached']} cached)  cost US${u['cost_usd']}")


def to_markdown(c: dict) -> str:
    out = ["# Verification contract (Gate 2)", "", "```", summarize(c), "```", ""]
    if c["contract"]["unreviewed_gates"]:
        out += [f"> **UNREVIEWED:** built while {', '.join(c['contract']['unreviewed_gates'])} was not approved.", ""]
    out += ["## Interface", "", "| Port | Dir | Width | Type |", "|---|---|---|---|"]
    out += [f"| {p['name']} | {p['direction']} | {p['width']} | {p['type']} |" for p in c["interface"]["ports"]]
    out += ["", "## Checks", "", "| ID | Kind | Group | Title | Rules | Behavior / expected |", "|---|---|---|---|---|---|"]
    for ch in c["checks"]:
        text = ch["behavior"] + (f" — STIMULUS: {ch['stimulus']} — EXPECTED: {ch['expected']}" if ch["kind"] == "test" else "")
        out.append(f"| {ch['id']} | {ch['kind']} | {ch['group']} | {ch['title']} | {', '.join(ch['rules'])} | "
                   f"{text.replace('|', chr(92) + '|')} |")
    if c["not_verified"]:
        out += ["", "## Not verified by simulation", "", "| Rule | Reason | Note |", "|---|---|---|"]
        out += [f"| {n['rule']} | {n['reason']} | {n['note'].replace('|', chr(92) + '|')} |" for n in c["not_verified"]]
    if c["assumptions"]:
        out += ["", "## Assumptions", ""] + [f"- {a}" for a in c["assumptions"]]
    return "\n".join(out) + "\n"


def write_outputs(c: dict, work: Path) -> list[Path]:
    paths = [work / "contract.json", work / "contract.md", work / "contract_shell.sv"]
    paths[0].write_text(json.dumps(c, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    paths[1].write_text(to_markdown(c), encoding="utf-8")
    paths[2].write_text(contract_shell(c["top"], c["interface"]), encoding="utf-8")
    return paths

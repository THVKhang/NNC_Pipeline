"""Functional coverage (stage gen-sva, agent A6): cover points from the specification, not the RTL.

Code coverage says which RTL lines ran; functional coverage says which situations of the
specification were exercised (each burst type and length class, each error class, back-pressure on
each channel, full/empty/threshold boundaries, reset during activity...). The agent sees the interface,
the contract checks and the rules, never the RTL. It returns the list of points (ID, title, rules,
checks, condition in words) and the body of one module `nnc_cov.sv`; code writes the header, one hit
counter per point and the final block that prints `NNC_COVER <id> hits=<n>`. The module is linted
with Verilator like the checkers, with at most `rounds` repairs.
"""
from __future__ import annotations

import re
from pathlib import Path

from nnc.agents.backend import AgentTask
from nnc.agents.runtime import Usage
from nnc.contract import module_header, multi_clock
from nnc.gen_sva import _reset_off
from nnc.simhost import SimHost, lint_sv

PROMPT_VERSION = "cov-v1"
MODULE = "nnc_cov"
SYSTEM_PROMPT = (
    "You are a verification engineer defining functional coverage from a specification. You use only the "
    "interface signals and the texts given; you never assume implementation details. The module must compile "
    "in Verilator 5. Return the answer in the required JSON structure."
)
SCHEMA = {
    "type": "object", "required": ["points", "body"], "additionalProperties": False,
    "properties": {
        "points": {"type": "array", "minItems": 1, "items": {
            "type": "object", "additionalProperties": False, "required": ["id", "title", "rules", "checks", "condition"],
            "properties": {"id": {"type": "string", "pattern": "^COVP-[0-9]{3}$"}, "title": {"type": "string"},
                           "rules": {"type": "array", "items": {"type": "string"}},
                           "checks": {"type": "array", "items": {"type": "string"}},
                           "condition": {"type": "string"}}}},
        "body": {"type": "string", "minLength": 20},
    },
}

RULES_TEXT = """CODING RULES (Verilator 5.055)
- Write ONLY the module body: helper registers/counters you need, and for every point one line
    always_ff @(posedge {clk}) if (!({rst_off}) && (CONDITION)) hits_{u} <= hits_{u} + 1;
  where {u} is the point ID with '-' replaced by '_'. The header with every interface signal as an input,
  the counters `int unsigned hits_<u> = 0;` and the final block already exist: do not repeat them.
- A point that needs history (e.g. "a burst of 16 beats completed", "back-pressure for 3+ cycles") uses
  helper registers updated on the same clock and reset as the DUT reset. Declare before use.
- Not allowed: covergroup, cover property, assert, $fatal/$error/$stop/$finish, bind, hierarchical
  references, signals that are not in the interface, initial blocks with delays.
- Put a comment `// <id>: <title>` above each point. No comment may start with the word "verilator".
"""

TASK_TEXT = """TASK
Define the functional cover points that show the verification exercised what the specification makes
important: every operation and response class, every burst type and length class (minimum, typical,
maximum), back-pressure on every channel, boundaries (empty/full/thresholds, address wrap, 4-KiB or word
boundaries), error and recovery cases, reset during activity, and important crosses (operation x response,
size x alignment). Only situations that legal stimulus can produce. 15 to 40 points, IDs COVP-001...
Each point names the rules and contract checks it relates to and states its condition in words; the body
implements exactly these conditions.
"""


def _u(pid: str) -> str:
    return pid.replace("-", "_")


def scaffold(iface: dict, points: list[dict]) -> tuple[str, str]:
    head = [module_header(MODULE, iface, all_inputs=True), ""]
    head += [f"  int unsigned hits_{_u(p['id'])} = 0;" for p in points]
    tail = ["", "  final begin"]
    tail += [f'    $display("NNC_COVER {p["id"]} hits=%0d", hits_{_u(p["id"])});' for p in points]
    tail += ["  end", "endmodule", ""]
    return "\n".join(head), "\n".join(tail)


def build_prompt(contract: dict, rules_doc: dict) -> str:
    iface = contract["interface"]
    used = {r for c in contract["checks"] for r in c["rules"]}
    rules = [r for r in rules_doc["rules"] if r["id"] in used]
    ports = "\n".join(f"  {p['name']} ({p['direction']} of the DUT, width {p['width']}): {p['meaning']}"
                      for p in iface["ports"])
    checks = "\n".join(f"  [{c['id']}] {c['title']}: {c['behavior'][:400]}" for c in contract["checks"])
    rtext = "\n".join(f"  [{r['id']}] {r['statement']}" for r in rules)
    rules_text = RULES_TEXT.replace("{clk}", iface["clock"] or "clk").replace("{rst_off}", _reset_off(iface))
    if multi_clock(iface):
        doms = []
        for c in iface["clocks"]:
            rs = [r for r in iface["resets"] if r["clock"] == c["name"]]
            off = " || ".join(f"!{r['name']}" if r["active_low"] else r["name"] for r in rs) or "1'b0"
            doms.append(f"  @(posedge {c['name']}) with reset-off ({off})")
        rules_text += ("- SEVERAL CLOCKS: count each point on the clock of the domain of its signals:\n" +
                       "\n".join(doms) + "\n")
    return (f"INTERFACE (all are inputs of the module; directions as seen by the DUT)\n{ports}\n\n"
            f"PARAMETERS: {', '.join(p['name'] for p in iface['parameters'])}\n\n"
            f"CONTRACT CHECKS\n{checks}\n\nRULES\n{rtext}\n\n{TASK_TEXT}\n{rules_text}")


def validate(points: list[dict], body: str) -> list[str]:
    problems = []
    ids = [p["id"] for p in points]
    if len(set(ids)) != len(ids):
        problems.append("duplicate point IDs")
    if re.search(r"^\s*(module|endmodule)\b", body, re.M):
        problems.append("the body must not contain module/endmodule")
    for bad in ("covergroup", "cover property", "assert", "$fatal", "$error", "$stop", "$finish", " bind "):
        if bad in body:
            problems.append(f"forbidden construct {bad.strip()}")
    if re.search(r"//\s*verilator", body, re.I):
        problems.append("a comment starts with the word verilator")
    for pid in ids:
        u = _u(pid)
        if not re.search(rf"hits_{u}\s*<=\s*hits_{u}\s*\+\s*1", body):
            problems.append(f"{pid}: missing hit counter update hits_{u} <= hits_{u} + 1")
    return problems


def generate(contract: dict, rules_doc: dict, backend, log_dir: Path, host: SimHost | None, out_dir: Path, *,
             model: str | None = "sonnet", rounds: int = 3) -> dict:
    prompt = build_prompt(contract, rules_doc)
    usage = Usage()
    history, status, problems, lint_err, points, code = "", "failed", [], "", [], ""
    for attempt in range(rounds + 1):
        res = backend.run(AgentTask(f"A6_cov_r{attempt}", prompt + history, SCHEMA, system_prompt=SYSTEM_PROMPT,
                                    model=model, max_turns=4), log_dir)
        usage.add(res)
        points, body = res.output["points"], res.output["body"].strip("\n")
        head, tail = scaffold(contract["interface"], points)
        code = f"{head}\n\n{body}\n{tail}"
        problems = validate(points, body)
        lint_ok, lint_err = (True, "") if host is None else lint_sv(host, {f"{MODULE}.sv": code}, MODULE)
        if not problems and lint_ok:
            status = "lint_clean" if host else "not_linted"
            break
        history = (f"\n\nYOUR PREVIOUS ANSWER (attempt {attempt + 1}) FAILED.\nPOINTS: {[p['id'] for p in points]}\n"
                   f"```systemverilog\n{body}\n```\nPROBLEMS:\n" + "\n".join(problems) +
                   (f"\nVERILATOR ERRORS:\n{lint_err}" if lint_err else "") + "\nReturn corrected points and body.")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{MODULE}.sv").write_text(code, encoding="utf-8")
    known_rules = {r["id"] for r in rules_doc["rules"]}
    known_checks = {c["id"] for c in contract["checks"]}
    pts = [{**p, "rules": [r for r in p["rules"] if r in known_rules],
            "checks": [c for c in p["checks"] if c in known_checks]} for p in points]
    return {"module": MODULE, "file": f"{MODULE}.sv", "points": pts, "status": status, "attempts": attempt + 1,
            "problems": problems, "lint_errors": lint_err, "usage": usage.as_dict(), "prompt_version": PROMPT_VERSION}

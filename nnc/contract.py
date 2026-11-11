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


def _is_port_table(t: dict) -> bool:
    head = [h.lower().strip() for h in t["header"]]
    return (any("port" in h for h in head) and any("width" in h for h in head)
            and any("direction" in h or h == "dir" for h in head))


def _port_tables(index: dict, top: str | None) -> list[dict]:
    """The port table of the top module. A specification may split it over several tables, each with a
    caption starting with the module name (e.g. "**`m_top`**: write side (CLK-WR)") and followed by the
    tables of submodules: with `top`, every port table whose caption starts with it is taken (a caption
    such as "m_mem (instantiated in m_top)" belongs to a submodule); otherwise the first."""
    cands = [t for t in index.get("tables", []) if _is_port_table(t)]
    if top:
        named = [t for t in cands if re.match(rf"\s*{re.escape(top)}\b", t.get("caption") or "")]
        if named:
            return named
    return cands[:1]


def _caption_domain(caption: str) -> str:
    """'m_top: write side (CLK-WR)' -> 'CLK-WR' (a clock domain named at the end of a table caption)."""
    m = re.search(r"\(([^()]+)\)\s*:?\s*$", caption or "")
    return m.group(1).strip() if m else ""


def _plain(cell: str) -> str:
    return cell.replace("`", "").strip()


def extract_interface(index: dict, top: str | None = None) -> dict:
    """Ports and parameters from the tables of an IP specification index."""
    tables = _port_tables(index, top)
    if not tables:
        raise ValueError("no port table (columns Port, Direction or Dir, Width) found in the IP specification")
    pt = tables[0]
    ports = []
    for tbl in tables:
        h = tbl["header"]
        c_name, c_w = _col(h, "port"), _col(h, "width")
        c_dir = next((i for i, x in enumerate(h) if "direction" in x.lower() or x.lower().strip() == "dir"), None)
        c_type, c_reset = _col(h, "signal type", "type"), _col(h, "reset")
        c_mean = _col(h, "meaning", "description", "function")
        c_dom = _col(h, "clock domain", "domain")
        cap_dom = _caption_domain(tbl.get("caption", ""))
        for row in tbl["rows"]:
            if len(row) <= max(c_name, c_dir, c_w):
                continue
            name = _plain(row[c_name])
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
                continue
            d = row[c_dir].lower()
            direction = "inout" if "inout" in d else "input" if d.startswith("in") else "output" if d.startswith("out") else None
            if direction is None or any(p["name"] == name for p in ports):
                continue
            ports.append({
                "name": name, "direction": direction, "width": _plain(row[c_w]),
                "type": row[c_type] if c_type is not None and c_type < len(row) else "",
                "reset_value": row[c_reset] if c_reset is not None and c_reset < len(row) else "",
                "meaning": row[c_mean] if c_mean is not None and c_mean < len(row) else "",
                "domain": _plain(row[c_dom]) if c_dom is not None and c_dom < len(row) else cap_dom,
            })
    params = []
    tt = _find_table(index, "parameter", "default")
    if tt is not None:
        ph = tt["header"]
        cn, cd, cr = _col(ph, "parameter"), _col(ph, "default"), _col(ph, "legal", "range")
        cp = _col(ph, "purpose", "description", "meaning")
        for row in tt["rows"]:
            name = row[cn].strip() if cn is not None and cn < len(row) else ""
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
                params.append({"name": name, "default": row[cd].strip() if cd is not None else "",
                               "legal": row[cr].strip() if cr is not None and cr < len(row) else ""})
                purpose = row[cp] if cp is not None and cp < len(row) else ""
                earlier = [q["name"] for q in params[:-1]]
                expr = derived_expr(params[-1]["default"], purpose, earlier)
                if not expr and not _is_number(params[-1]["default"]):
                    # the formula may sit in another column (Effect): the first that parses as a formula (an
                    # operator or clog2; a bare name, as in a Dependencies column, only says what it depends on)
                    others = [c for i, c in enumerate(row) if i not in (cn, cd, cr, cp)]
                    expr = next((e for e in (derived_expr(params[-1]["default"], c, earlier) for c in others)
                                 if e and re.search(r"[-+*/]|clog2", e)), None)
                    if not expr:
                        params[-1]["unresolved"] = True
                if expr:
                    params[-1]["derived"] = expr
    # A derived constant without a formula the flow can read: harmless when no port width uses it (an
    # internal width such as a bundle size; left out of the interface), fatal when a port needs its value.
    used = " ".join(p["width"] for p in ports)
    for p in [q for q in params if q.get("unresolved")]:
        if re.search(rf"\b{re.escape(p['name'])}\b", used):
            raise ValueError(f"derived parameter {p['name']} sets a port width but its formula is not readable "
                             f"(default {p['default']!r}); write it as an expression of the other parameters "
                             f"in the parameter table")
    params = [q for q in params if not q.get("unresolved")]

    def pick(kind: str, names: tuple[str, ...]) -> dict | None:
        for p in ports:
            if p["direction"] == "input" and (kind in p["type"].lower() or any(n in p["name"].lower() for n in names)):
                return p
        return None

    def active_low(p: dict) -> bool:
        return bool(re.search(r"(_n\b|_n_|active[- ]low)", p["name"] + " " + p["meaning"] + " " + p["type"], re.I))
    clk = pick("clock", ("clk", "clock"))
    rst = pick("reset", ("rst", "reset"))
    reset = None
    if rst is not None:
        reset = {"name": rst["name"], "active_low": active_low(rst)}
    # Every clock and every hardware reset (by the signal-type column when the table has one), each
    # reset tied to the clock of its domain. A request such as a software reset is not of type reset.
    typed = any(_col(t["header"], "signal type", "type") is not None for t in tables)
    clocks = [p for p in ports if p["direction"] == "input" and p["width"] in ("", "1") and
              (re.match(r"\s*(clock|clk)\b", p["type"], re.I) if typed else re.search(r"clk|clock", p["name"], re.I))]
    if clk is not None and clk not in clocks:
        clocks.insert(0, clk)
    resets = [p for p in ports if p["direction"] == "input" and p["width"] in ("", "1") and
              (re.match(r"\s*(reset|rst)\b", p["type"], re.I) if typed else re.search(r"rst|reset", p["name"], re.I))]
    if rst is not None and rst not in resets:
        resets.insert(0, rst)

    def clock_of(r: dict) -> str | None:
        for c in clocks:
            if c["domain"] and r["domain"] and (c["domain"] in r["domain"] or r["domain"] in c["domain"]):
                return c["name"]
        return clk["name"] if clk else None
    return {"ports": ports, "parameters": params, "clock": clk["name"] if clk else None, "reset": reset,
            "clocks": [{"name": c["name"], "domain": c["domain"]} for c in clocks],
            "resets": [{"name": r["name"], "active_low": active_low(r), "clock": clock_of(r)} for r in resets],
            "source_table": {"section": pt["section"], "line": pt["line"]}}


def width_decl(width: str) -> str:
    """'1' -> '', '32' -> '[31:0]', 'PARA_ADDR_W' -> '[PARA_ADDR_W-1:0]'."""
    w = width.strip()
    if w in ("", "1"):
        return ""
    if w.isdigit():
        return f"[{int(w) - 1}:0]"
    return f"[({w})-1:0]"


def _is_number(text: str) -> bool:
    d = text.strip()
    return bool(re.match(r"^\d+$", d) or re.match(r"^\d+'[bdh][0-9a-fA-F_]+$", d) or d in ("", "'0"))


def _param_default(p: dict) -> str:
    d = p["default"].strip()
    if re.match(r"^\d+$", d):
        return d
    m = re.match(r"^(\d+)'[bdh][0-9a-fA-F_]+$", d)
    return d if m else ("0" if d in ("", "'0") else d)


def derived_expr(default: str, purpose: str, earlier: list[str]) -> str | None:
    """SystemVerilog expression of a derived parameter ("Derived" default, a formula such as
    "clog2(DEPTH + 1)" in the purpose text), with short names resolved to the earlier parameters."""
    d = default.strip()
    if re.match(r"^\d+$", d) or re.match(r"^\d+'[bdh][0-9a-fA-F_]+$", d):
        return None
    text = d if re.search(r"clog2|[-+*/]", d) else purpose

    def resolve(w: re.Match) -> str:
        word = w.group(0)
        if word in earlier:
            return word
        hits = [n for n in earlier if n.upper().endswith("_" + word.upper())]
        # "DATA_W" -> PARA_X_DATA_W rather than PARA_X_USER_DATA_W: the shortest name, when it is unique
        best = [n for n in hits if len(n) == min(map(len, hits))] if hits else []
        return best[0] if len(best) == 1 else word

    m = re.search(r"\$?clog2\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)", text)
    if not m:
        plain = text.replace("`", "").strip().rstrip(".")
        w = re.fullmatch(r"(?:ceil(?:ing)?\s+of\s+)?log2\s+of\s+(?:the\s+)?([A-Za-z_][A-Za-z0-9_]*)", plain, re.I)
        if w:                                       # "log2 of the depth" -> $clog2(PARA_..._DEPTH)
            name = resolve(re.match(r".*", w.group(1)))
            return f"$clog2({name})" if name in earlier else None
        if re.fullmatch(r"[A-Za-z0-9_\s()+\-*/]+", plain) and re.search(r"[A-Za-z_]", plain):
            plain = re.sub(r"[A-Za-z_][A-Za-z0-9_]*", resolve, plain)   # "DATA_W / 8" -> PARA_X_DATA_W / 8
            names = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", plain)
            if all(n in earlier for n in names):    # "LPARA_ADDR_W + 1"
                return re.sub(r"\s+", " ", plain)
        return None
    inner = re.sub(r"\s[x×]\s", " * ", m.group(1))
    inner = re.sub(r"[A-Za-z_][A-Za-z0-9_]*", resolve, inner)
    if any(re.match(r"[A-Za-z_]", t) and t not in earlier for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", inner)):
        return None
    return f"$clog2({inner.strip()})"


def eval_param(expr: str, values: dict[str, int]) -> int:
    """Value of a derived-parameter expression for given parameter values ($clog2 as in SV)."""
    def clog2(n: int) -> int:
        return (int(n) - 1).bit_length() if n > 1 else 0
    py = expr.replace("$clog2", "clog2")
    if re.search(r"[^\w\s()+\-*/]", py):
        raise ValueError(f"unsupported expression {expr}")
    return int(eval(py, {"__builtins__": {}}, {"clog2": clog2, **values}))  # noqa: S307 (checked charset)


def derived_values(iface: dict, values: dict[str, int]) -> dict[str, int]:
    out = dict(values)
    for p in iface["parameters"]:
        if p.get("derived"):
            out[p["name"]] = eval_param(p["derived"], out)
    return out


def param_decl(p: dict) -> str:
    """A derived parameter is a localparam (the DUT computes it too; it cannot be overridden)."""
    if p.get("derived"):
        return f"localparam int {p['name']} = {p['derived']}"
    return f"parameter int {p['name']} = {_param_default(p)}"


def module_header(name: str, iface: dict, all_inputs: bool = False) -> str:
    """SystemVerilog header with the contract parameters and ports (all inputs for a checker)."""
    params = ",\n".join(f"  {param_decl(p)}" for p in iface["parameters"])
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
def multi_clock(iface: dict) -> bool:
    return len(iface.get("clocks") or []) > 1 or len(iface.get("resets") or []) > 1


def _domains_text(iface: dict) -> list[str]:
    """Extra interface lines for a design with several clocks or resets (none for one clock and one
    reset, so that single-clock prompts and their cache entries do not change)."""
    if not multi_clock(iface):
        return []
    rows = ["Clock domains (each check is evaluated on the clock of the domain of its signals):"]
    for c in iface["clocks"]:
        rs = [f"{r['name']} ({'active low' if r['active_low'] else 'active high'})" for r in iface["resets"]
              if r["clock"] == c["name"]]
        rows.append(f"  {c['name']} domain {c['domain'] or '?'}: reset {', '.join(rs) or 'none'}")
    if is_async(iface):
        rows.append("  " + ASYNC_NOTE)
    return rows


ASYNC_NOTE = ("The clocks are MUTUALLY ASYNCHRONOUS: no fixed period ratio and no fixed phase. A behavior that "
              "crosses domains (a value or event of one domain becoming visible in the other) has no exact cycle "
              "count: state it as order and a bounded window counted in edges of the destination clock, from "
              "the minimum to the maximum latency the specification allows (synchronizer stages plus any "
              "modelled extra latency), never as 'in the next cycle' of the other clock.")


def is_async(iface: dict) -> bool:
    return iface.get("clock_relation") == "async" and len(iface.get("clocks") or []) > 1


def _iface_text(iface: dict, top: str) -> str:
    rows = [f"DUT top module: {top}",
            f"Clock: {iface['clock']} (rising edge)",
            f"Reset: {iface['reset']['name']} ({'active low' if iface['reset']['active_low'] else 'active high'})"
            if iface.get("reset") else "Reset: none found"] + _domains_text(iface) + [
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


def id_mapping(checks: list[dict], order: list[int]) -> dict[str, str]:
    """Old check ID (as written by the agent) -> CHK-nnn in `order`. An old ID given to two checks
    (first pass and gap fill) is ambiguous and left out (references to it stay as written)."""
    olds = [c.get("id") for c in checks]
    return {old: f"CHK-{n:03d}" for n, i in enumerate(order, 1) if (old := olds[i]) and olds.count(old) == 1}


CHK_REF = re.compile(r"\bCHK-(\d{3})\b(?:(\.\.|–|—| to )(?:CHK-)?(\d{3})\b)?((?:/(?:CHK-)?\d{3}\b)*)")


def _ref(m: re.Match, mapping: dict[str, str]) -> str:
    """One reference: a single ID, a range (`CHK-020..CHK-023`, en dash, " to ") or a slash list
    (`CHK-015/017`). A range is expanded to the new IDs of its members; it stays a range only when those
    are still consecutive."""
    first, sep, last, tail = m.group(1), m.group(2), m.group(3), m.group(4)
    if sep:
        lo, hi = sorted((int(first), int(last)))
        new = sorted({mapping.get(f"CHK-{k:03d}", f"CHK-{k:03d}") for k in range(lo, hi + 1)})
        nums = [int(x[4:]) for x in new]
        out = (f"{new[0]}{sep}{new[-1]}" if nums == list(range(nums[0], nums[0] + len(nums)))
               else ", ".join(new))
    else:
        out = mapping.get(f"CHK-{first}", f"CHK-{first}")
    for d in re.findall(r"(\d{3})", tail):
        out += "/" + mapping.get(f"CHK-{d}", f"CHK-{d}")
    return out


def rewrite_refs(v, mapping: dict[str, str], keep: tuple[str, ...] = ("rules", "id", "rule")):
    """Replace every check ID inside strings (recursively), in one pass so that IDs never chain."""
    if isinstance(v, str):
        return CHK_REF.sub(lambda m: _ref(m, mapping), v)
    if isinstance(v, list):
        return [rewrite_refs(x, mapping, keep) for x in v]
    if isinstance(v, dict):
        return {k: (x if k in keep else rewrite_refs(x, mapping, keep)) for k, x in v.items()}
    return v


def renumber(checks: list[dict], order: list[int]) -> list[dict]:
    """Give the checks the IDs CHK-001... in `order` and rewrite every reference to an old ID inside
    their texts (a check may say "uses the tracker of CHK-015")."""
    mapping = id_mapping(checks, order)
    out = []
    for n, i in enumerate(order, 1):
        c = rewrite_refs(checks[i], mapping)
        c["id"] = f"CHK-{n:03d}"
        out.append(c)
    return out


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
    renum = renumber(checks, order)
    mapping = id_mapping(checks, order)           # notes and assumptions cite checks too
    not_verified = rewrite_refs(not_verified, mapping)
    assumptions = rewrite_refs(assumptions, mapping)
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


def selected(c: dict) -> dict:
    """The contract restricted to the checks selected for this run (all unless `nnc plan --select`)."""
    sel = c.get("selection")
    if not sel or sel.get("mode") != "selected":
        return c
    keep = set(sel["checks"])
    return {**c, "checks": [ch for ch in c["checks"] if ch["id"] in keep]}


def select_checks(c: dict, checks: list[str] | None, by: str, reason: str = "") -> dict:
    """Record the test-plan selection (None = all checks). The selection is part of the Gate 2 artifact."""
    ids = {ch["id"] for ch in c["checks"]}
    if checks is None:
        c["selection"] = {"mode": "all", "checks": sorted(ids), "by": by,
                          "date": datetime.now(timezone.utc).isoformat(timespec="seconds"), "reason": reason}
        return c
    unknown = sorted(set(checks) - ids)
    if unknown:
        raise ValueError(f"unknown check IDs {unknown}")
    c["selection"] = {"mode": "selected", "checks": sorted(set(checks)), "by": by, "reason": reason,
                      "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                      "not_selected": sorted(ids - set(checks))}
    return c


def to_markdown(c: dict) -> str:
    out = ["# Verification contract (Gate 2)", "", "```", summarize(c), "```", ""]
    sel = c.get("selection")
    if sel and sel.get("mode") == "selected":
        out += [f"> **Test plan selection** by {sel['by']} ({sel['date']}): {len(sel['checks'])} of "
                f"{len(c['checks'])} checks selected. Not selected (reported NOT_SELECTED, never PASS): "
                f"{', '.join(sel['not_selected'])}. {sel.get('reason', '')}", ""]
    elif sel:
        out += [f"> **Test plan selection** by {sel['by']} ({sel['date']}): all {len(c['checks'])} applicable checks.", ""]
    if c["contract"]["unreviewed_gates"]:
        out += [f"> **UNREVIEWED:** built while {', '.join(c['contract']['unreviewed_gates'])} was not approved.", ""]
    out += ["## Interface", "", "| Port | Dir | Width | Type |", "|---|---|---|---|"]
    out += [f"| {p['name']} | {p['direction']} | {p['width']} | {p['type']} |" for p in c["interface"]["ports"]]
    out += ["", "## Checks", "", "| ID | Kind | Group | Title | Rules | Behavior / expected |", "|---|---|---|---|---|---|"]
    for ch in c["checks"]:
        text = ch["behavior"] + (f" — STIMULUS: {ch['stimulus']} — EXPECTED: {ch['expected']}" if ch["kind"] == "test" else "")
        mark = "" if not sel or sel.get("mode") != "selected" or ch["id"] in sel["checks"] else " (not selected)"
        out.append(f"| {ch['id']}{mark} | {ch['kind']} | {ch['group']} | {ch['title']} | {', '.join(ch['rules'])} | "
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

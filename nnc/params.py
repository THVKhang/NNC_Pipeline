"""Parameter configuration (code only, no LLM): legal values of the specification, and the chosen configuration.

The contract (G2) lists every parameter with its default and its legal values as the specification writes
them ("1 to 32", "8, 16 or 32", "Power of 2, minimum 2, no upper limit", "0 to PARA_X_DATA_W; a multiple of 8
is recommended"). This module turns that text into a constraint that code can check:

    set      the value must be one of a list            "0 or 1", "0, 1, 2, 3, 4", "8, 16 or 32"
    range    lower and/or upper bound, inclusive         "1 to 32", "1..8", "1-16 inclusive", "Minimum 1",
             (a bound may be an expression of other       "2 or more", "0 to 2^PARA_SRC_W - 1"
             parameters)
    pow2     power of two (with a range or alone)        "Power of 2, minimum 2"

Text after a ';' or in a sentence the parser does not understand is kept as a NOTE: it is shown to the
person who chooses the configuration and recorded as unchecked, never silently dropped. A parameter whose
legal text cannot be parsed at all is UNCHECKED.

Uses:
  * `nnc params <ip>`               table of parameters, defaults, legal text and the parsed constraint;
  * `nnc params <ip> --check`       defaults, every configuration of run_set.json and final_config.json;
  * `nnc params <ip> --choose K=V`  the configuration of the RTL to generate -> work/final_config.json
                                    (gate D1_config of a design whose RTL the flow generates).
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from nnc.contract import eval_param

FINAL_CONFIG = "final_config.json"

_NUM = r"-?\d+"
_TERM = r"[A-Za-z0-9_$()^*/+\- ]+?"


def _expr(text: str) -> str | None:
    """A bound as a Python-evaluable expression of parameter names ('2^X - 1' -> '2**X - 1'), or None."""
    t = text.strip().strip(".").strip()
    t = re.sub(r"\binclusive\b", "", t, flags=re.I).strip()
    if not t or not re.fullmatch(r"[A-Za-z0-9_$()^*/+\- ]+", t):
        return None
    return re.sub(r"\s+", " ", t.replace("^", "**"))


def parse_legal(text: str | None) -> dict:
    """Constraint of one legal-values text: {kind, values?, min?, max?, pow2?, note, parsed}."""
    raw = (text or "").strip()
    out: dict = {"text": raw, "parsed": False, "note": ""}
    if not raw or raw in ("-", "—"):
        out.update(kind="none", parsed=True)
        return out
    head, _, tail = raw.partition(";")
    notes = [tail.strip()] if tail.strip() else []
    t = head.replace("–", " to ").replace("—", " to ").replace("�", " to ")
    t = re.sub(r"\(([A-Z]{2,}-\d+[^)]*)\)", "", t)            # "(DEC-009)": a reference, not a value
    t = re.sub(r"\s+", " ", t).strip().rstrip(".")
    low = t.lower()

    # a list: "0 or 1", "8, 16 or 32", "0, 1, 2, 3, 4"
    if re.fullmatch(rf"{_NUM}(\s*,\s*{_NUM})*(\s*,?\s*or\s+{_NUM})?", t) and ("," in t or " or " in low):
        out.update(kind="set", values=[int(v) for v in re.findall(_NUM, t)], parsed=True)
        out["note"] = "; ".join(notes)
        return out

    c: dict = {"kind": "range"}
    parts = [p.strip() for p in re.split(r",", t) if p.strip()]
    rest = []
    for p in parts:
        pl = p.lower()
        if re.fullmatch(r"(a )?power of (2|two)", pl):
            c["pow2"] = True
            continue
        if re.fullmatch(r"no upper (limit|bound)", pl):
            continue
        m = (re.fullmatch(r"(?:minimum|min\.?|at least)\s+(.+)", p, re.I)
             or re.fullmatch(r"(?:any integer of\s+)?(.+?)\s+or (?:more|greater|above)", p, re.I))
        if m and _expr(m.group(1)):
            c["min"] = _expr(m.group(1))
            continue
        m = re.fullmatch(r"(?:maximum|max\.?|at most)\s+(.+)", p, re.I)
        if m and _expr(m.group(1)):
            c["max"] = _expr(m.group(1))
            continue
        m = (re.fullmatch(rf"({_TERM})\s+to\s+({_TERM})(?:\s+inclusive)?", p, re.I)
             or re.fullmatch(rf"(-?\w+)\s*\.\.\s*({_TERM})", p))
        if m and _expr(m.group(1)) and _expr(m.group(2)):
            c["min"], c["max"] = _expr(m.group(1)), _expr(m.group(2))
            continue
        rest.append(p)
    if "min" in c or "max" in c or c.get("pow2"):
        out.update(c, parsed=True)
        out["note"] = "; ".join(rest + notes)
        return out
    out.update(kind="unchecked", note=raw)
    return out


def _value(expr: str, values: dict[str, int]) -> int:
    """Value of a bound or derived formula: names, integers, + - * / ** ( ) and $clog2 only."""
    if re.search(r"[^\w\s()+\-*/^$]", expr):
        raise ValueError(f"unsupported expression {expr}")
    return eval_param(expr.replace("^", "**"), values)


def check_value(name: str, value: int, cons: dict, values: dict[str, int]) -> list[str]:
    """Violations of one parameter value (empty when legal or not checkable)."""
    errs = []
    kind = cons.get("kind")
    if kind == "set" and value not in cons["values"]:
        errs.append(f"{name}={value}: legal values are {cons['values']} ({cons['text']})")
    if kind == "range":
        for side in ("min", "max"):
            if side not in cons:
                continue
            try:
                bound = _value(cons[side], values)
            except Exception as e:  # noqa: BLE001 - an unknown name in the bound
                errs.append(f"{name}: cannot evaluate the {side}imum '{cons[side]}' ({e})")
                continue
            if (side == "min" and value < bound) or (side == "max" and value > bound):
                errs.append(f"{name}={value}: {side}imum is {bound} ({cons['text']})")
        if cons.get("pow2") and (value < 1 or value & (value - 1)):
            errs.append(f"{name}={value}: must be a power of 2 ({cons['text']})")
    return errs


def table(iface: dict) -> list[dict]:
    """One row per parameter: name, default, derived formula, legal text, constraint."""
    return [{"name": p["name"], "default": p.get("default"), "derived": p.get("derived"),
             "legal": p.get("legal"), "constraint": parse_legal(p.get("legal"))} for p in iface["parameters"]]


def defaults(iface: dict) -> dict[str, int]:
    out = {}
    for p in iface["parameters"]:
        if p.get("derived"):
            continue
        d = str(p.get("default", "")).strip()
        m = re.fullmatch(r"(\d+)'[dD](\d+)", d)
        try:
            out[p["name"]] = int(m.group(2)) if m else int(d, 0)
        except ValueError:
            pass
    return out


def resolve(iface: dict, overrides: dict[str, int]) -> dict[str, int]:
    """Every parameter value of a configuration: defaults, then overrides, then derived parameters."""
    free = {p["name"] for p in iface["parameters"] if not p.get("derived")}
    unknown = sorted(set(overrides) - free)
    if unknown:
        raise ValueError(f"not overridable parameters of the contract: {unknown} (parameters: {sorted(free)})")
    vals = {**defaults(iface), **overrides}
    for p in iface["parameters"]:
        if p.get("derived"):
            try:
                vals[p["name"]] = _value(p["derived"], vals)
            except Exception:  # noqa: BLE001 - reported by check()
                pass
    return vals


def check(iface: dict, overrides: dict[str, int]) -> dict:
    """Check one configuration: {values, errors, unchecked (names), notes ({name: note})}."""
    vals = resolve(iface, overrides)
    errors, unchecked, notes = [], [], {}
    for row in table(iface):
        name, cons = row["name"], row["constraint"]
        if name not in vals:
            errors.append(f"{name}: no value (default '{row['default']}' is not a number"
                          + (f", derived '{row['derived']}' cannot be computed" if row["derived"] else "") + ")")
            continue
        if cons["kind"] == "unchecked":
            unchecked.append(name)
        if cons.get("note"):
            notes[name] = cons["note"]
        errors += check_value(name, vals[name], cons, vals)
    return {"values": vals, "errors": errors, "unchecked": unchecked, "notes": notes}


def parse_assignments(items: list[str]) -> dict[str, int]:
    out = {}
    for kv in items:
        if "=" not in kv:
            raise ValueError(f"expected NAME=VALUE, got '{kv}'")
        k, v = kv.split("=", 1)
        try:
            out[k.strip()] = int(v.strip(), 0)
        except ValueError as e:
            raise ValueError(f"{k.strip()}: value must be an integer, got '{v.strip()}'") from e
    return out


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def choose(work: Path, contract: dict, overrides: dict[str, int], by: str, note: str = "",
           accept_unchecked: bool = False) -> dict:
    """Record the configuration of the RTL to generate (work/final_config.json). Refuses an illegal value;
    a parameter whose legal text could not be parsed needs accept_unchecked (the person has read the text)."""
    if not by.strip():
        raise ValueError("--by <name> is required: the person who chooses the configuration")
    iface = contract["interface"]
    res = check(iface, overrides)
    if res["errors"]:
        raise ValueError("illegal configuration:\n  " + "\n  ".join(res["errors"]))
    if res["unchecked"] and not accept_unchecked:
        raise ValueError(f"the legal values of {res['unchecked']} are free text the flow cannot check; read them "
                         f"('nnc params <ip>') and pass --accept-unchecked")
    contract_hash = hashlib.sha256((work / "contract.json").read_bytes().replace(b"\r\n", b"\n")).hexdigest() \
        if (work / "contract.json").is_file() else None
    doc = {"top": contract.get("top"), "chosen_by": by.strip(), "at": _now(), "note": note,
           "overrides": overrides, "values": res["values"], "unchecked": res["unchecked"], "notes": res["notes"],
           "contract_sha256": contract_hash}
    (work / FINAL_CONFIG).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    return doc


def check_design(root: Path, contract: dict) -> list[tuple[str, dict]]:
    """Defaults, each configuration of run_set.json and final_config.json: [(label, check result)]."""
    iface = contract["interface"]
    out = [("defaults", check(iface, {}))]
    rs = root / "run_set.json"
    if rs.is_file():
        doc = json.loads(rs.read_text(encoding="utf-8"))
        for c in doc.get("configs", []):
            try:
                ov = {k: int(v, 0) if isinstance(v, str) else int(v) for k, v in (c.get("params") or {}).items()}
                out.append((f"run_set:{c.get('name')}", check(iface, ov)))
            except ValueError as e:
                out.append((f"run_set:{c.get('name')}", {"values": {}, "errors": [str(e)], "unchecked": [], "notes": {}}))
    fc = root / "work" / FINAL_CONFIG
    if fc.is_file():
        doc = json.loads(fc.read_text(encoding="utf-8"))
        try:
            out.append(("final_config", check(iface, doc.get("overrides", {}))))
        except ValueError as e:
            out.append(("final_config", {"values": {}, "errors": [str(e)], "unchecked": [], "notes": {}}))
    return out

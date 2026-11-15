"""Configuration awareness of generated verification code (code only).

The run set showed that generated tests and checkers silently assume the default configuration: a
discard point written as 5 (S+3 for S=2 only), a fill target of 5 words (impossible at depth 2), a
check of exactly 8 entries. Two measures:

* `config_text`: the configurations of `run_set.json` are given to the SVA (A5) and test (A7) writers
  up front, with the rule that every quantity that depends on a parameter is computed from it.
* `hardcoded`: after generation, code looks for integer literals equal to the default value (>= 5) of
  an overridable parameter that changes in the run set, outside comments and strings.
  Each is sent back once: replace it by an expression of the parameter, or keep it with the comment
  `nnc-literal-ok` on the same line when the number does not come from the parameter.
"""
from __future__ import annotations

import ast
import io
import re
import tokenize

from nnc.contract import derived_values
from nnc.sim import param_values

OK_MARK = "nnc-literal-ok"


def config_text(contract: dict, runs: list[dict] | None) -> str:
    """Prompt section: every configuration the code must work in."""
    if not runs:
        return ""
    seen, lines = set(), []
    for r in runs:
        if r["config"] in seen:
            continue
        seen.add(r["config"])
        ov = ", ".join(f"{k}={v}" for k, v in (r.get("params") or {}).items()) or "default parameters"
        o = r.get("opts") or {}
        extra = []
        if o.get("defines"):
            extra.append("defines " + ",".join(o["defines"]))
        if o.get("plusargs"):
            extra.append("plusargs " + o["plusargs"])
        if r.get("clock_periods"):
            extra.append("clocks " + ", ".join(f"{k}={v} ns" for k, v in r["clock_periods"].items()))
        lines.append(f"  {r['config']}: {ov}" + (f"; {'; '.join(extra)}" if extra else "")
                     + (f"  ({r['note']})" if r.get("note") else ""))
    return ("CONFIGURATIONS: the same code runs unchanged in every configuration below (one simulation each).\n"
            + "\n".join(lines) + "\n"
            "  Every quantity that depends on a parameter (depth, widths, number of synchronizer stages, latency\n"
            "  windows, counts, fill levels) is computed from the parameter values of the run (PARAMS / module\n"
            "  parameters), never written as the number of the default configuration. A scenario that cannot be\n"
            "  built in a configuration (for example a fill level above the depth) is declared not verifiable\n"
            "  there instead of failing or passing silently.\n")


def varying_defaults(contract: dict, runs: list[dict] | None) -> dict[int, list[str]]:
    """{default value: [parameter names]} for parameters (and derived ones) whose value changes in the run
    set: overridable parameters only, values >= 5 (smaller numbers are everywhere)."""
    if not runs:
        return {}
    iface = contract["interface"]
    base = derived_values(iface, param_values(contract))
    seen: dict[str, set] = {k: {v} for k, v in base.items()}
    for r in runs:
        for k, v in derived_values(iface, param_values(contract, r.get("params"))).items():
            seen.setdefault(k, set()).add(v)
    derived = {p["name"] for p in iface["parameters"] if p.get("derived")}
    out: dict[int, list[str]] = {}
    for k, vals in seen.items():
        v = base.get(k)
        if k not in derived and isinstance(v, int) and v >= 5 and len(vals) > 1:
            out.setdefault(v, []).append(k)
    return out


def _python_literals(code: str) -> list[tuple[int, int]]:
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            if tok.type == tokenize.NUMBER:
                try:
                    v = ast.literal_eval(tok.string)
                except (ValueError, SyntaxError):
                    continue
                if isinstance(v, int) and not isinstance(v, bool):
                    out.append((tok.start[0], v))
    except (tokenize.TokenError, IndentationError):
        pass
    return out


def _sv_literals(code: str) -> list[tuple[int, int]]:
    out = []
    for n, line in enumerate(code.splitlines(), 1):
        text = re.sub(r'"[^"]*"', '""', line.split("//")[0])
        for m in re.finditer(r"(?<![\w'$.])(\d+)(?![\w'.])", text):
            out.append((n, int(m.group(1))))
    return out


def hardcoded(code: str, contract: dict, runs: list[dict] | None, lang: str) -> list[str]:
    """Warnings 'line N: literal V equals the default of P' for literals that probably stand for a
    parameter of a configuration that changes in the run set."""
    vd = varying_defaults(contract, runs)
    if not vd:
        return []
    lines = code.splitlines()
    lits = _python_literals(code) if lang == "python" else _sv_literals(code)
    out, done = [], set()
    for n, v in lits:
        if (n, v) in done:
            continue
        done.add((n, v))
        line = lines[n - 1]
        if any(name in line for name in vd.get(v, [])):
            continue        # the parameter's own declaration or default lookup
        if v in vd and OK_MARK not in line and not line.lstrip().startswith(("#", "//")):
            out.append(f"line {n}: literal {v} equals the default of {', '.join(vd[v])}, which changes in the run "
                       f"set: `{lines[n - 1].strip()[:120]}`")
    return out


def feedback(warnings: list[str]) -> str:
    return ("\n\nPOSSIBLE HARD-CODED CONFIGURATION VALUES (the code must work in every configuration listed above):\n"
            + "\n".join(warnings[:40]) +
            f"\nFor each: replace the number by an expression of the parameter, or, if the number does not come "
            f"from that parameter, keep it and add the comment `{OK_MARK}` on the same line. Return the complete "
            "corrected code.")

"""Sequential equivalence of two RTL versions of one top module (Yosys miter + SymbiYosys).

Used by `nnc restyle`: an RTL rewritten to follow docs/RTL_RULES.md must behave exactly like the original.
Simulation can only sample that; here a formal tool checks every input sequence.

    gold  the original RTL            gate  the rewritten RTL
    miter -equiv: both copies get the same inputs; `trigger` = some output differs
    environment: every reset of the contract is asserted in the first step, then the inputs are free
    initial state: registers without a reset start at 0 in both copies (setundef -zero -init)

Result per run: PROVEN (abc pdr closed the proof: equal for every input sequence of any length),
BOUNDED (no difference within `depth` steps, proof not closed), CEX (a difference; the trace is kept),
ERROR (the miter could not be built). The register-initialisation choice is a limit: two versions that
differ only in the power-up value of a register without reset are reported equal, which the
specification normally allows (such a register is written before it is used). Both versions are read with
the same macros and parameter values; equivalence is checked for that configuration only.
"""
from __future__ import annotations

import re
from pathlib import Path

from nnc.contract import width_decl
from nnc.params import _value
from nnc.simhost import SimHost

SBY = """[tasks]
bmc
prove

[options]
bmc: mode bmc
prove: mode prove
depth {depth}
multiclock {multiclock}
timeout {timeout}

[engines]
bmc: smtbmc yices
prove: abc pdr

[script]
read_rtlil miter.il
read -formal nnc_eq_top.sv
prep -top nnc_eq_top
setundef -zero -init

[files]
miter.il
nnc_eq_top.sv
"""


def _side(tag: str, order: list[str], top: str, params: list[tuple[str, int]], defines: list[str],
          frontend: str = "verilog") -> str:
    """Yosys commands that read one copy and stash it. `frontend` "slang": the yosys-slang plugin, which
    elaborates with the parameter values itself (-G) and reads SystemVerilog Yosys' parser rejects."""
    defs = " ".join(f"-D{d}" for d in defines)
    srcs = " ".join(f"{tag}/{f}" for f in order)
    if frontend == "slang":
        gparams = "".join(f" -G {n}={v}" for n, v in params)
        read = f"read_slang {defs} --top {top}{gparams} {srcs}\n"
    else:
        read = f"read_verilog -sv {defs} {srcs}\n" + "".join(f"chparam -set {n} {v} {top}\n" for n, v in params)
    return (f"{read}hierarchy -check -top {top}\n"
            f"proc\nflatten\nopt_clean\nrename {top} nnc_{tag}\ndesign -stash {tag}\n")


def wrapper(iface: dict, values: dict[str, int], resets: list[dict]) -> str:
    """nnc_eq_top: the miter with every input a free input, resets asserted in the first step."""
    ins = [p for p in iface["ports"] if p["direction"].lower() == "input" and not p.get("virtual")]

    def decl(p: dict) -> str:
        w = str(p["width"]).strip()
        n = int(w) if w.isdigit() else _value(w, values)
        return f"[{n - 1}:0] " if n > 1 else ""
    ports = ",\n".join(f"  input logic {decl(p)}in_{p['name']}" for p in ins)
    conns = ",\n    ".join(f".in_{p['name']}(in_{p['name']})" for p in ins)
    rst = "\n".join(f"  always @(*) if (nnc_init) assume ({'!' if r.get('active_low', True) else ''}in_{r['name']});"
                    for r in resets)
    return (f"module nnc_eq_top (\n{ports}\n);\n  wire trigger;\n  nnc_miter u_miter (\n    {conns},\n"
            f"    .trigger(trigger)\n  );\n  reg nnc_init = 1'b1;\n  always @($global_clock) nnc_init <= 1'b0;\n{rst}\n"
            "endmodule\n")


def build(contract: dict, values: dict[str, int], gold: dict[str, Path | str], gold_order: list[str],
          gate: dict[str, Path | str], gate_order: list[str], *, defines: list[str] | None = None,
          depth: int = 20, timeout_s: int = 900, multiclock: bool = False,
          frontend: str = "verilog") -> tuple[dict, str]:
    if frontend not in ("verilog", "slang"):
        raise ValueError(f"frontend must be 'verilog' or 'slang', not {frontend!r}")
    iface, top = contract["interface"], contract["top"]
    params = [(p["name"], values[p["name"]]) for p in iface["parameters"] if not p.get("derived") and p["name"] in values]
    resets = [r for r in (iface.get("resets") or [iface.get("reset")]) if isinstance(r, dict)]
    ys = (_side("gold", gold_order, top, params, defines or [], frontend)
          + _side("gate", gate_order, top, params, defines or [], frontend)
          + "design -copy-from gold -as nnc_gold nnc_gold\ndesign -copy-from gate -as nnc_gate nnc_gate\n"
          "miter -equiv -flatten -make_assert nnc_gold nnc_gate nnc_miter\nhierarchy -top nnc_miter\n"
          "write_rtlil miter.il\n")
    files: dict[str, object] = {f"gold/{n}": v for n, v in gold.items()}
    files.update({f"gate/{n}": v for n, v in gate.items()})
    files["nnc_miter.ys"] = ys
    files["nnc_eq_top.sv"] = wrapper(iface, values, resets)
    files["eq.sby"] = SBY.format(depth=depth, multiclock="on" if multiclock else "off", timeout=timeout_s)
    # prove (abc pdr) first: it closes the proof or finds a counterexample of any length, often in seconds;
    # bmc runs only when prove concluded nothing (a smtbmc bmc can take the whole timeout on a large miter)
    script = ("yosys -q -s nnc_miter.ys > miter.log 2>&1; echo NNC_MITER_RC=$?; grep -m5 ERROR miter.log; "
              "if [ -f miter.il ]; then sby -f eq.sby prove > prove.log 2>&1; "
              "case \"$(head -1 eq_prove/status 2>/dev/null)\" in PASS*|FAIL*) ;; "
              "*) sby -f eq.sby bmc > bmc.log 2>&1;; esac; fi; "
              "for t in bmc prove; do echo NNC_STATUS_$t=$(cat eq_$t/status 2>/dev/null | head -1); done; "
              "grep -h -m3 -E 'Assert failed|counterexample|summary' bmc.log prove.log 2>/dev/null; "
              "mkdir -p trace; cp eq_prove/engine_0/trace.vcd trace/eq_cex.vcd 2>/dev/null || "
              "cp eq_bmc/engine_0/trace.vcd trace/eq_cex.vcd 2>/dev/null; true")
    return files, script


def run(host: SimHost, contract: dict, values: dict[str, int], gold: dict, gold_order: list[str], gate: dict,
        gate_order: list[str], **kw) -> dict:
    files, script = build(contract, values, gold, gold_order, gate, gate_order, **kw)
    res = host.run(files, script, ["trace/*.vcd", "bmc.log", "prove.log", "miter.log"], timeout_s=3600, tag="equiv")
    text = res.output
    st = {t: (re.search(rf"NNC_STATUS_{t}=(\w*)", text) or [None, ""])[1] for t in ("bmc", "prove")}
    if "NNC_MITER_RC=0" not in text:
        status = "ERROR"
    elif st["prove"].startswith("PASS"):
        status = "PROVEN"
    elif st["bmc"].startswith("FAIL") or st["prove"].startswith("FAIL"):
        status = "CEX"
    elif st["bmc"].startswith("PASS"):
        status = "BOUNDED"
    else:
        status = "ERROR"
    detail = "\n".join(ln for ln in text.splitlines() if "ERROR" in ln or "Assert failed" in ln)[:1500]
    trace = res.out_dir / "trace" / "eq_cex.vcd"
    return {"status": status, "bmc": st["bmc"], "prove": st["prove"], "depth": kw.get("depth", 20),
            "detail": detail, "trace": str(trace) if trace.is_file() else None, "out_dir": str(res.out_dir)}


def _vcd(text: str) -> tuple[dict[str, str], list[tuple[int, dict[str, str]]]]:
    """Minimal VCD reader: ({id: scope.name}, [(time, {id: value})]) with values carried forward."""
    names, scope, steps, cur, t = {}, [], [], {}, None
    for line in text.splitlines():
        tok = line.split()
        if not tok:
            continue
        if tok[0] == "$scope":
            scope.append(tok[2])
        elif tok[0] == "$upscope":
            scope.pop()
        elif tok[0] == "$var":
            names.setdefault(tok[3], ".".join(scope + [tok[4]]))
        elif tok[0].startswith("#"):
            if t is not None:
                steps.append((t, dict(cur)))
            t = int(tok[0][1:])
        elif tok[0][0] in "01xzXZ" and len(tok) == 1:
            cur[tok[0][1:]] = tok[0][0]
        elif tok[0][0] in "bB" and len(tok) == 2:
            cur[tok[1]] = tok[0][1:]
    if t is not None:
        steps.append((t, dict(cur)))
    return names, steps


def cex_outputs(vcd_path: str | None, contract: dict) -> str:
    """The first step after reset at which outputs differ, and which ones (gold_/gate_ wires of the miter)."""
    if not vcd_path or not Path(vcd_path).is_file():
        return "counterexample trace not available"
    names, steps = _vcd(Path(vcd_path).read_text(encoding="utf-8", errors="replace"))
    outs = [p["name"] for p in contract["interface"]["ports"] if p["direction"].lower() == "output"]
    ids = {}
    for i, n in names.items():
        m = re.search(r"u_miter\.(gold|gate)_(\w+)$", n)
        if m and m.group(2) in outs:
            ids.setdefault(m.group(2), {})[m.group(1)] = i
    for k, (_, vals) in enumerate(steps):
        diff = [o for o, s in ids.items() if "gold" in s and "gate" in s and vals.get(s["gold"]) != vals.get(s["gate"])]
        if diff:
            return f"outputs differ at step {k} after reset: " + ", ".join(
                f"{o} (original {vals.get(ids[o]['gold'])}, rewritten {vals.get(ids[o]['gate'])})" for o in diff)
    return f"a difference was found within {len(steps)} steps (see the trace)"

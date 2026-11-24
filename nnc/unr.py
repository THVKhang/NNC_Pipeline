"""Formal proof that uncovered toggle points cannot be reached (ROADMAP 19.5, code only, no LLM).

Constant propagation (coverage.const_from_netlist) leaves out the toggles of bits that are tied to a
constant. It cannot see a bit that is constant because of the design's behaviour: the upper bits of a counter
that never passes 5, a flag that a mode never sets. This module proves such bits with SymbiYosys:

1. candidates: from the merged coverage.dat, every DUT signal bit whose 1->0 toggle was never recorded
   (after the constant-bit scope). Unpacked array elements are not tried.
2. per configuration of the run set (parameters and macros of the simulated build), the flattened Yosys
   netlist (`proc; flatten`) gives the names, widths and clocking; each candidate signal is renamed and
   exposed as a port, and a generated wrapper asserts that every candidate bit keeps, for ever, the value
   it has when the first reset ends.
3. `abc --keep-going pdr` proves or refutes every assertion; `sby --status` gives one result per bit.

The model over-approximates every simulation: all inputs are free, resets included, except that the first
reset is held until every clock has had two rising edges (the harness holds it five cycles of the slowest
clock). Flops without a reset start at any value. A design with one clock, rising edges only and no
latch is checked with one global clock (`multiclock off`); any other with free clocks (`multiclock on`).
So a PROVEN bit cannot toggle after the first reset in any run, and both of its toggle points are left
out of the coverage (the 0->1 of a constant 1 is the simulator's start at 0). A FAIL is a counterexample
with free inputs, not a proof of reachability with legal stimulus: the point stays counted. A bit with no
result (time limit) stays counted.

Results go to work/unr.json, keyed by the SHA-256 of the RTL and by the parameters and macros of each
configuration. Every simulation applies the recorded proofs that match the current RTL; `nnc sim --unr`
also proves the candidates that have no result yet.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from nnc import coverage as cov
from nnc import unrbranch, unrexpr
from nnc.formal import _resets, clock_names
from nnc.sim import rtl_files
from nnc.simhost import SimHost

VERSION = 3          # 1: single-clock results vacuous (no guard); 2: control could be a free input; discarded
CHUNK = 200                 # assertions per SymbiYosys task (one task per group of signals)
TASK_TIMEOUT_S = 1200       # per task; a bit without a result stays counted
RESET_EDGES = 2             # rising edges of every clock while the first reset is held
ENGINE = "abc --keep-going pdr"
_FF = re.compile(r"^\$_?(a?l?dff|sdff|adff|dffe|adffe|sdffe|sdffce|dffsr|dffsre|aldff|aldffe)")
_LATCH = re.compile(r"^\$_?(dlatch|adlatch|dlatchsr)")


# ------------------------------------------------------------------------------------ candidates
def candidates(dat_path: Path, rtl_names: list[str], scope: dict | None = None) -> dict[str, set[int]]:
    """{signal: bit indices} of the DUT whose 1->0 toggle was never recorded, without the bits the
    constant-bit scope already leaves out."""
    const = {n: cov._expand(t) for n, t in (((scope or {}).get("const") or {}).get("bits") or {}).items()}
    fields = (scope or {}).get("fields") or {}
    if const:
        const = cov.with_stars(const, ((scope or {}).get("const") or {}).get("nets") or [],
                               cov.star_signals(dat_path, set(rtl_names), fields))
    fall: dict[tuple[str, int], int] = {}
    for kv, _name, metric, _line, _span, count in cov._records(dat_path, set(rtl_names)):
        if metric != "toggle":
            continue
        bit = cov.toggle_bit(kv, fields)
        if bit is None or bit[1] in const.get(bit[0], ()):
            continue
        if kv.get("o", "").endswith(":1->0"):
            fall[bit] = fall.get(bit, 0) + count
        else:
            fall.setdefault(bit, 0)
    out: dict[str, set[int]] = defaultdict(set)
    for (sig, idx), n in fall.items():
        if n == 0:
            out[sig].add(idx)
    return dict(out)


def controls(dat_path: Path, rtl_names: list[str], limit: int = 500, least: int = 4,
             fields: dict | None = None) -> list[tuple[str, int]]:
    """Bits the simulation toggled at least `least` times in each direction, most toggled first: the control
    assertion of every task (it must FAIL: a model in which such a bit cannot change does not match the
    simulation, and the task concludes nothing)."""
    seen: dict[tuple[str, int], list[int]] = defaultdict(lambda: [0, 0])
    for kv, _name, metric, _line, _span, count in cov._records(dat_path, set(rtl_names)):
        if metric == "toggle":
            bit = cov.toggle_bit(kv, fields)
            if bit is not None:
                seen[bit][kv.get("o", "").endswith(":1->0")] += count
    ok = [(min(r, f), b) for b, (r, f) in seen.items() if min(r, f) >= least]
    return [b for _n, b in sorted(ok, key=lambda x: (-x[0], x[1]))[:limit]]


def rtl_sha256(rtl_dir: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(rtl_files(rtl_dir), key=lambda p: p.name):
        h.update(f.name.encode("utf-8") + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()


def config_key(params: dict, defines: list[str], frontend: str) -> str:
    text = json.dumps({"params": {k: str(v) for k, v in sorted(params.items())},
                       "defines": sorted(defines), "frontend": frontend}, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------------------------------- netlist
def read_commands(top: str, srcs: list[str], params: dict, defines: list[str], frontend: str,
                  cut: list[str] | tuple = ()) -> str:
    """Yosys commands reading the DUT with the run's parameters and macros (run in the folder of the sources).
    `cut`: modules whose instances become formal cut points (every output free in every step)."""
    defs = " ".join(f"-D{d}" for d in defines)
    if frontend == "slang":
        if cut:
            raise ValueError("unr_cut needs the verilog frontend")
        return (f"read_slang {defs} -I . --top {top} " + "".join(f"-G {k}={v} " for k, v in params.items())
                + " ".join(srcs) + f"\nhierarchy -top {top}")
    return (f"read_verilog -sv {defs} -I. " + " ".join(srcs)
            + "".join(f"\nblackbox {m}" for m in cut) + f"\nhierarchy -top {top}"
            + "".join(f" -chparam {k} {v}" for k, v in params.items())
            + ("\ncutpoint -blackbox" if cut else ""))


_COND = re.compile(r"`(?:ifdef|ifndef|elsif)\s+(\w+)")
_MODULE = re.compile(r"^\s*module\s+(?:automatic\s+|static\s+)?(\w+)", re.M)


def cut_check(rtl_dir: Path, cut: dict) -> str | None:
    """Why the cut of config `unr_cut` would be unsound, or None. The proof reads the RTL with the cut's
    macros added (they select the synthesizable code that Yosys can read), then frees every output of the
    cut modules. That over-approximates any behaviour of those modules, the simulation model included, so a
    PROVEN bit holds in the simulated design as long as the macros change nothing outside the cut modules:
    every file that tests one of them must define cut modules only."""
    mods, macros = set(cut.get("modules") or []), set(cut.get("defines") or [])
    if not mods:
        return "unr_cut names no module"
    found: set[str] = set()
    for f in rtl_files(rtl_dir):
        text = f.read_text(encoding="utf-8", errors="replace")
        defined = set(_MODULE.findall(text))
        found |= defined & mods
        if set(_COND.findall(text)) & macros and not defined <= mods:
            return (f"{f.name} tests {', '.join(sorted(set(_COND.findall(text)) & macros))} and defines "
                    f"{', '.join(sorted(defined - mods))}, which is not cut")
    if found != mods:
        return "unr_cut names modules the RTL does not define: " + ", ".join(sorted(mods - found))
    return None


def _top(netlist: dict) -> tuple[str, dict] | None:
    tops = [(n, m) for n, m in (netlist.get("modules") or {}).items()
            if str((m.get("attributes") or {}).get("top", "0")).strip("0") != ""]
    return tops[0] if len(tops) == 1 else None


def netlist_info(netlist: dict) -> dict | None:
    """Ports, wires ({name: [width, offset, upto]}) and clocking of the flattened top."""
    t = _top(netlist)
    if t is None:
        return None
    _, m = t
    ports = {n: {"direction": p.get("direction"), "width": len(p.get("bits") or [])}
             for n, p in (m.get("ports") or {}).items()}
    wires = {}
    for name, net in (m.get("netnames") or {}).items():
        if net.get("hide_name") or name.startswith("$"):
            continue
        wires[name] = [len(net.get("bits") or []), int(net.get("offset", 0) or 0), int(bool(net.get("upto", 0)))]
    clk_nets, negedge, latch, q_bits = set(), False, False, set()
    for c in (m.get("cells") or {}).values():
        typ = c.get("type", "")
        if _LATCH.match(typ):
            latch = True
        elif _FF.match(typ) and "CLK" in (c.get("connections") or {}):
            clk_nets.add(tuple(str(b) for b in c["connections"]["CLK"]))
            q_bits.update(str(b) for b in c["connections"].get("Q") or [])
            pol = str((c.get("parameters") or {}).get("CLK_POLARITY", "1"))
            if pol.strip("0") == "":
                negedge = True
    clk_bits = {b for net in clk_nets for b in net}
    clock_wires = sorted(n for n, net in (m.get("netnames") or {}).items()
                         if n in wires and clk_bits & {str(b) for b in net.get("bits") or []})
    state = {}
    for n, net in (m.get("netnames") or {}).items():
        if n in wires:
            pos = [i for i, b in enumerate(net.get("bits") or []) if str(b) in q_bits]
            if pos:
                state[n] = pos
    return {"ports": ports, "wires": wires, "clock_nets": len(clk_nets), "negedge": negedge, "latch": latch,
            "clock_wires": clock_wires, "state": state}


def multiclock(info: dict, n_clocks: int) -> bool:
    """One global clock only for one clock, rising edges, no latch; else free clocks."""
    return n_clocks > 1 or info["clock_nets"] > 1 or info["negedge"] or info["latch"]


def position(wire: list, idx: int) -> int | None:
    """Position (0 = LSB of the netlist bits) of declared bit `idx`, or None outside the wire."""
    w, off, upto = wire
    i = idx - off
    if not 0 <= i < w:
        return None
    return w - 1 - i if upto else i


# --------------------------------------------------------------------------------------- tasks
def _label(k: int, idx: int) -> str:
    return f"nnc_u{k}_b{idx}" if idx >= 0 else f"nnc_u{k}_bm{-idx}"


GUARD = "nnc_armed_reach"
CONTROL = "nnc_control"
CONTROLS = 4         # control bits per task, of different signals: one of them must FAIL


def _controls(control) -> list[tuple[str, int]]:
    """A control bit, a list of them, or None -> a list."""
    if control is None:
        return []
    return [control] if isinstance(control[0], str) else list(control)


def _csuffix(i: int) -> str:
    return "" if i == 0 else str(i)


def wrapper(info: dict, iface: dict, group: list[tuple[int, str, list[int]]], free_clocks: bool = True,
            control=None, zero: set[str] | frozenset = frozenset()) -> str:
    """The formal top of one task: the DUT with its candidate signals exposed, the reset assumption of the
    first reset, and one assertion per candidate bit. `group`: (k, signal, bit indices).

    With free clocks (`multiclock on`) the first reset lasts until every clock has had RESET_EDGES rising
    edges; with one global clock every step is a clock edge (the clock input cannot be read as data there), so
    it lasts RESET_EDGES + 1 steps. The guard assertion GUARD (`!nnc_armed`) must FAIL: it shows that the
    checked phase is reached, else every PASS of the task would be vacuous. A control assertion (CONTROL,
    CONTROL1, ...) is the same property on a bit the simulation toggled many times (`control`: one bit or a
    list, of different signals); one of them must FAIL too, else the model shows no state that changes after
    the first reset and the task concludes nothing (a bit toggled by the runs of another configuration may be
    constant in this one, hence several). A signal whose last name is in `zero` (the
    combinational markers of nnc/unrbranch.py) is asserted to be 0 instead of keeping its value."""
    ports, wires = info["ports"], info["wires"]
    ins = [(n, p["width"]) for n, p in ports.items() if p["direction"] == "input"]
    decl = lambda w: f"[{w - 1}:0] " if w > 1 else ""
    lines = ["// Generated by NNC (nnc/unr.py): proof that the bits below never change after the first reset.",
             "module nnc_unr_top (", ",\n".join(f"  input logic {decl(w)}{n}" for n, w in ins), ");"]
    conns = [f".{n}({n})" for n, _ in ins]
    for k, sig, _bits in group:
        w = wires[sig][0]
        lines.append(f"  wire {decl(w)}nnc_s{k};")
        conns.append(f".{sig}(nnc_s{k})" if sig in ports else f".nnc_p{k}(nnc_s{k})")
    ctls = _controls(control)
    for i, (csig, _cidx) in enumerate(ctls):
        c = _csuffix(i)
        lines.append(f"  wire {decl(wires[csig][0])}nnc_sc{c};")
        conns.append(f".{csig}(nnc_sc{c})" if csig in ports else f".nnc_pc{c}(nnc_sc{c})")
    lines.append("  nnc_unr_dut u_dut (" + ", ".join(conns) + ");")
    clocks = sorted(c for c in clock_names(iface) if c in ports) if free_clocks else []
    init = []
    for i, c in enumerate(clocks):
        lines += [f"  reg [1:0] nnc_e{i} = 2'd0;", f"  reg nnc_c{i};",
                  f"  always @($global_clock) begin nnc_c{i} <= {c}; "
                  f"if ({c} && !nnc_c{i} && nnc_e{i} != 2'd{RESET_EDGES}) nnc_e{i} <= nnc_e{i} + 2'd1; end"]
        init.append(f"(nnc_e{i} != 2'd{RESET_EDGES})")
    if not clocks:
        n = RESET_EDGES + 1
        lines += ["  reg [1:0] nnc_e = 2'd0;", f"  always @($global_clock) if (nnc_e != 2'd{n}) nnc_e <= nnc_e + 2'd1;"]
        init.append(f"(nnc_e != 2'd{n})")
    lines.append(f"  wire nnc_init = {' || '.join(init)};")
    for r in _resets(iface):
        if r["name"] in ports:
            lines.append(f"  always @* if (nnc_init) assume ({'!' if r.get('active_low', True) else ''}{r['name']});")
    lines.append("  reg nnc_armed = 1'b0;")
    for k, sig, _bits in group:
        lines.append(f"  reg {decl(wires[sig][0])}nnc_f{k};")
    caps = [f"nnc_f{k} <= nnc_s{k};" for k, _s, _b in group]
    for i, (csig, _cidx) in enumerate(ctls):
        c = _csuffix(i)
        lines.append(f"  reg {decl(wires[csig][0])}nnc_fc{c};")
        caps.append(f"nnc_fc{c} <= nnc_sc{c};")
    lines.append("  always @($global_clock) if (!nnc_init && !nnc_armed) begin nnc_armed <= 1'b1; "
                 + " ".join(caps) + " end")
    lines.append(f"  always @* {GUARD}: assert (!nnc_armed);     // must FAIL: the checked phase is reached")
    lines.append("  always @* if (nnc_armed) begin")
    for i, (csig, cidx) in enumerate(ctls):
        c = _csuffix(i)
        p = position(wires[csig], cidx)
        sel = f"[{p}]" if wires[csig][0] > 1 else ""
        lines.append(f"    {CONTROL}{c}: assert (nnc_sc{c}{sel} == nnc_fc{c}{sel});   // one must FAIL: toggled in simulation")
    for k, sig, bits in group:
        for idx in bits:
            p = position(wires[sig], idx)
            sel = f"[{p}]" if wires[sig][0] > 1 else ""
            if sig.rsplit(".", 1)[-1] in zero:
                lines.append(f"    {_label(k, idx)}: assert (nnc_s{k}{sel} == 1'b0);")
            else:
                lines.append(f"    {_label(k, idx)}: assert (nnc_s{k}{sel} == nnc_f{k}{sel});")
    lines += ["  end", "endmodule"]
    return "\n".join(lines) + "\n"


SBY = """[options]
mode prove
multiclock {multiclock}
timeout {timeout}

[engines]
{engine}

[script]
{read}
proc
flatten
cd {top}
{renames}
cd ..
{expose}
rename {top} nnc_unr_dut
read_verilog -sv -formal {wrapper}
prep -top nnc_unr_top

[files]
{files}
"""


def expand_instances(cands: dict[str, set[int]], info: dict) -> tuple[dict[str, set[int]], dict[str, list[str]]]:
    """Candidates whose name Verilator merged over several instances ("gen_f[*].u.q", "u_*ata_in.qe")
    become one candidate per wire of the netlist that the name matches (cov.star_regex); {merged name: those
    wires} to collapse the results."""
    out: dict[str, set[int]] = {}
    stars = cov.star_members(cands, sorted(info["wires"]))
    for sig, bits in cands.items():
        for w in stars.get(sig, [sig]):
            out.setdefault(w, set()).update(bits)
    return out, stars


def collapse_instances(rec: dict, stars: dict[str, list[str]], cands: dict[str, set[int]]) -> None:
    """A merged point is PROVEN only if it is PROVEN in every instance; a counterexample in one instance is
    a counterexample of the merged point; otherwise it has no result. An instance that is an input port makes
    the merged signal an input (not tried). The results of a wire stay only if it is a candidate itself."""
    inputs = set(rec.get("inputs") or [])
    merged: dict[str, dict[str, set[int]]] = {"proven": defaultdict(set), "cex": defaultdict(set), "open": defaultdict(set)}
    member_inputs: set[str] = set()
    for sig, insts in stars.items():
        if any(w in inputs for w in insts):
            member_inputs |= {w for w in insts if w in inputs}
            inputs.add(sig)
            continue
        for idx in cands[sig]:
            st = ["proven" if idx in rec["proven"].get(w, ()) else "cex" if idx in rec["cex"].get(w, ())
                  else "open" for w in insts]
            key = "proven" if all(s == "proven" for s in st) else "cex" if "cex" in st else "open"
            merged[key][sig].add(idx)
    members = {w for insts in stars.values() for w in insts} - set(cands)
    for key in ("proven", "cex", "open"):
        for w in members:
            rec[key].pop(w, None)
        for sig, bits in merged[key].items():
            rec[key][sig] |= bits
    rec["inputs"] = sorted(inputs - (member_inputs - set(cands)))


def plan(cands: dict[str, set[int]], info: dict) -> tuple[list[list[tuple[int, str, list[int]]]], dict]:
    """Groups of (k, signal, bits) of at most CHUNK bits, and the candidates that cannot be tried:
    {"absent": signals not in this netlist, "inputs": input ports (free in the model)}."""
    wires, ports = info["wires"], info["ports"]
    absent, inputs, todo = [], [], []
    for sig in sorted(cands):
        if sig not in wires:
            absent.append(sig)
        elif ports.get(sig, {}).get("direction") == "input":
            inputs.append(sig)
        else:
            bits = sorted(i for i in cands[sig] if position(wires[sig], i) is not None)
            if bits:
                todo.append((sig, bits))
    groups, cur, n = [], [], 0
    for k, (sig, bits) in enumerate(todo):
        while bits:
            take = bits[:CHUNK - n] if n < CHUNK else []
            if not take:
                groups.append(cur)
                cur, n = [], 0
                continue
            cur.append((k, sig, take))
            n += len(take)
            bits = bits[len(take):]
    if cur:
        groups.append(cur)
    return groups, {"absent": absent, "inputs": inputs}


def build(top: str, iface: dict, rtl: list[Path], params: dict, defines: list[str], frontend: str,
          info: dict, groups: list, timeout_s: int = TASK_TIMEOUT_S,
          control=None, cut: list[str] | tuple = (),
          zero: set[str] | frozenset = frozenset()) -> dict[str, object]:
    srcs = [f.name for f in rtl]
    files: dict[str, object] = {f"src/{f.name}": f for f in _all_rtl(rtl)}
    free = multiclock(info, len(clock_names(iface)))
    mc = "on" if free else "off"
    read = read_commands(top, srcs, params, defines, frontend, cut)
    for n, group in enumerate(groups):
        wname = f"nnc_unr_top_{n:03d}.sv"
        files[f"src/{wname}"] = wrapper(info, iface, group, free, control, zero)
        inner = [(f"nnc_p{k}", s) for k, s, _b in group if s not in info["ports"]]
        for i, (csig, _cidx) in enumerate(_controls(control)):
            if csig not in info["ports"]:
                inner.append((f"nnc_pc{_csuffix(i)}", csig))
        inner = list(dict.fromkeys(inner))
        renames = "\n".join(f"rename \\{s} {new}" for new, s in inner)
        expose = ("expose " + " ".join(f"w:{new}" for new, _s in inner)) if inner else ""
        files[f"UNR_{n:03d}.sby"] = SBY.format(multiclock=mc, timeout=timeout_s, engine=ENGINE, read=read, top=top,
                                               renames=renames, expose=expose, wrapper=wname,
                                               files="\n".join(f"src/{s}" for s in
                                                               [p.name for p in _all_rtl(rtl)] + [wname]))
    return files


def _all_rtl(rtl: list[Path]) -> list[Path]:
    """The RTL sources and every other file of their folders (include files)."""
    out = {f.name: f for f in rtl}
    for d in {f.parent for f in rtl}:
        for f in sorted(d.iterdir()):
            if f.is_file() and f.suffix in (".sv", ".v", ".svh", ".vh", ".h", ".inc") and f.name not in out:
                out[f.name] = f
    return list(out.values())


NETLIST_RUN = ("cd src && yosys -q -p '{cmds}; proc; flatten; write_json ../nnc_unr_netlist.json' "
               "> ../nnc_unr_netlist.log 2>&1; echo NNC_RC=$? >> ../nnc_unr_netlist.log\n")
PROVE_RUN = ("ls UNR_*.sby | xargs -P {parallel} -I{{}} sh -c 'sby -f {{}} > \"$(basename {{}} .sby).log\" 2>&1; "
             "sby {{}} --status > \"$(basename {{}} .sby).status\" 2>&1'\n")
_STATUS = re.compile(r"^nnc_unr_top\.nnc_u(\d+)_b(m?)(\d+)\s+(\w+)\s*$")
_GUARD = re.compile(rf"^nnc_unr_top\.({GUARD}|{CONTROL}\d*)\s+(\w+)\s*$")


def parse_statuses(text: str) -> dict[tuple[int, int], str]:
    """{(k, bit): status} of one task; empty when its guard did not FAIL, or none of its controls when it has
    some (nothing is concluded)."""
    out, sentinel = {}, {}
    for line in text.splitlines():
        g = _GUARD.match(line.strip())
        if g:
            sentinel[g.group(1)] = g.group(2)
            continue
        m = _STATUS.match(line.strip())
        if m:
            idx = -int(m.group(3)) if m.group(2) else int(m.group(3))
            out[(int(m.group(1)), idx)] = m.group(4)
    return out if _conclusive(sentinel) else {}


def _conclusive(sentinel: dict) -> bool:
    ctl = [v for k, v in sentinel.items() if k.startswith(CONTROL)]
    return sentinel.get(GUARD) == "FAIL" and (not ctl or "FAIL" in ctl)


def vacuous(text: str) -> bool:
    """The task ran (some status line) but its guard, or every one of its controls, did not FAIL."""
    lines = [ln.strip() for ln in text.splitlines()]
    sentinel = {g.group(1): g.group(2) for ln in lines if (g := _GUARD.match(ln))}
    return any(_STATUS.match(ln) for ln in lines) and not _conclusive(sentinel)


def prove_config(host: SimHost, contract: dict, rtl_dir: Path, params: dict, defines: list[str], frontend: str,
                 cands: dict[str, set[int]], *, parallel: int = 4, timeout_s: int = TASK_TIMEOUT_S,
                 control_bits: list[tuple[str, int]] | None = None, cut: list[str] | tuple = (),
                 zero: set[str] | frozenset = frozenset()) -> dict:
    """Prove the candidates in one configuration: {"proven", "cex", "open": {signal: ranges}, "absent",
    "inputs": [signals], "multiclock", "tasks", "error"}. `zero`: see wrapper."""
    top, iface = contract["top"], contract["interface"]
    rtl = rtl_files(rtl_dir)
    files = {f"src/{f.name}": f for f in _all_rtl(rtl)}
    cmds = read_commands(top, [f.name for f in rtl], params, defines, frontend, cut).replace("\n", "; ")
    r1 = host.run(files, NETLIST_RUN.format(cmds=cmds), ["nnc_unr_netlist.json", "nnc_unr_netlist.log"],
                  timeout_s=1800, tag="unr_netlist")
    nf = Path(r1.out_dir) / "nnc_unr_netlist.json"
    info = netlist_info(json.loads(nf.read_text(encoding="utf-8"))) if nf.is_file() else None
    if info is None:
        log = Path(r1.out_dir) / "nnc_unr_netlist.log"
        tail = log.read_text(encoding="utf-8", errors="replace").splitlines()[-6:] if log.is_file() else []
        return {"error": "no netlist: " + " | ".join(tail), "proven": {}, "cex": {}, "open": {}, "absent": [],
                "inputs": []}
    wanted = cands
    cands, stars = expand_instances(cands, info)
    groups, skipped = plan(cands, info)
    control = pick_controls(control_bits or [], info, set(cands))
    rec = {"proven": defaultdict(set), "cex": defaultdict(set), "open": defaultdict(set), **skipped,
           "multiclock": multiclock(info, len(clock_names(iface))), "tasks": len(groups),
           "control": ", ".join(f"{s}[{i}]" for s, i in control) or None}
    if groups:
        f2 = build(top, iface, rtl, params, defines, frontend, info, groups, timeout_s, control, cut, zero)
        waves = -(-len(groups) // max(1, parallel))
        r2 = host.run(f2, PROVE_RUN.format(parallel=parallel), ["UNR_*.status", "UNR_*.log"],
                      timeout_s=600 + 2 * timeout_s * waves, tag="unr")
        rec["vacuous_tasks"] = 0
        for n, group in enumerate(groups):
            sf = Path(r2.out_dir) / f"UNR_{n:03d}.status"
            text = sf.read_text(encoding="utf-8", errors="replace") if sf.is_file() else ""
            rec["vacuous_tasks"] += vacuous(text)
            st = parse_statuses(text)
            for k, sig, bits in group:
                for idx in bits:
                    s = st.get((k, idx))
                    rec["proven" if s == "PASS" else "cex" if s == "FAIL" else "open"][sig].add(idx)
    if stars:
        collapse_instances(rec, stars, wanted)
        rec["instances"] = {s: len(w) for s, w in sorted(stars.items())}
    for key in ("proven", "cex", "open"):
        rec[key] = {s: cov.line_ranges(v) for s, v in sorted(rec[key].items()) if v}
    return rec


def pick_control(bits: list[tuple[str, int]], info: dict, avoid: set[str]) -> tuple[str, int] | None:
    """The first control bit that is a flop output of this netlist (state: it changes only when the model's clock
    ticks and its logic runs, which a free input or a clock never shows), not a clock net and not a candidate
    signal."""
    clocks = set(info.get("clock_wires") or [])
    state = info.get("state") or {}
    for sig, idx in bits:
        if (sig in info["wires"] and sig not in avoid and sig not in clocks
                and info["ports"].get(sig, {}).get("direction") != "input"
                and position(info["wires"][sig], idx) in state.get(sig, ())):
            return sig, idx
    return None


def pick_controls(bits: list[tuple[str, int]], info: dict, avoid: set[str], n: int = CONTROLS) -> list[tuple[str, int]]:
    """Up to `n` control bits as pick_control chooses them, each of another signal."""
    out: list[tuple[str, int]] = []
    for b in bits:
        if len(out) >= n:
            break
        c = pick_control([b], info, avoid | {s for s, _i in out})
        if c:
            out.append(c)
    return out


# ------------------------------------------------------------------------------------- record
def load(path: Path, rtl_hash: str) -> dict:
    """The record of work/unr.json for this RTL (an empty one when absent, stale or of another version)."""
    try:
        rec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        rec = {}
    if rec.get("version") != VERSION or rec.get("rtl_sha256") != rtl_hash:
        return {"version": VERSION, "rtl_sha256": rtl_hash, "engine": ENGINE, "configs": {}}
    return rec


def proven_bits(rec: dict, keys: list[str]) -> dict[str, set[int]] | None:
    """Bits PROVEN in every configuration that has the signal (a configuration without its signal does not
    count against it); None when a configuration has no record."""
    confs = [rec["configs"].get(k) for k in keys]
    if not confs or any(c is None for c in confs):
        return None
    out: dict[str, set[int]] = {}
    sigs = set().union(*(set(c.get("proven") or {}) for c in confs))
    for s in sigs:
        have = [c for c in confs if s not in (c.get("absent") or [])]
        sets = [cov._expand((c.get("proven") or {}).get(s, "")) for c in have]
        bits = set.intersection(*sets) if sets else set()
        if bits:
            out[s] = bits
    return out


def undecided(rec_conf: dict | None, cands: dict[str, set[int]]) -> dict[str, set[int]]:
    """The candidates without a PROVEN or counterexample result in this configuration. Time limits are retried,
    and so are signals that were not in the netlist (a later version may match their names)."""
    if not rec_conf:
        return {s: set(b) for s, b in cands.items()}
    done: dict[str, set[int]] = defaultdict(set)
    for key in ("proven", "cex"):
        for s, t in (rec_conf.get(key) or {}).items():
            done[s] |= cov._expand(t)
    skip = set(rec_conf.get("inputs") or [])
    out = {s: b - done.get(s, set()) for s, b in cands.items() if s not in skip}
    return {s: b for s, b in out.items() if b}


def merge_record(conf: dict | None, new: dict) -> dict:
    """Add the results of a new proof run to the record of a configuration."""
    if not conf:
        return new
    out = dict(conf)
    for key in ("proven", "cex", "open"):
        acc: dict[str, set[int]] = defaultdict(set)
        for s, t in (conf.get(key) or {}).items():
            acc[s] |= cov._expand(t)
        for s, t in (new.get(key) or {}).items():
            acc[s] |= cov._expand(t)
        out[key] = acc
    for s, t in (new.get("proven") or {}).items():         # a new result replaces an earlier time limit
        out["open"][s] = out["open"].get(s, set()) - cov._expand(t)
    for s, t in (new.get("cex") or {}).items():
        out["open"][s] = out["open"].get(s, set()) - cov._expand(t)
    for key in ("proven", "cex", "open"):
        out[key] = {s: cov.line_ranges(v) for s, v in sorted(out[key].items()) if v}
    found = {s for key in ("proven", "cex", "open") for s in (new.get(key) or {})} | set(new.get("inputs") or [])
    out["absent"] = sorted((set(conf.get("absent") or []) | set(new.get("absent") or [])) - found)
    out["inputs"] = sorted(set(conf.get("inputs") or []) | set(new.get("inputs") or []))
    for key in ("multiclock", "error", "control"):
        if key in new:
            out[key] = new[key]
    out["tasks"] = int(conf.get("tasks", 0)) + int(new.get("tasks", 0))
    # inconclusive bits stay "open" and are tried again: only the latest run's count describes the record
    out["vacuous_tasks"] = int(new.get("vacuous_tasks", conf.get("vacuous_tasks", 0)))
    return out


def _count(m: dict) -> int:
    return sum(len(cov._expand(t)) for t in (m or {}).values())


def _ctl_md(text: str) -> str:
    return ", ".join(f"`{c}`" for c in text.split(", ")) + (" (one must change)" if ", " in text else "")


def to_markdown(name: str, rec: dict, keys: list[str] | None = None) -> str:
    """The record as Markdown; with `keys`, only the configurations of the current run (the others stay in the
    record as a cache and are counted in one line)."""
    L = [f"# Formal unreachability of toggle points: {name}", "",
         "Generated by `nnc sim --unr` (nnc/unr.py, no LLM). Each bit below had no recorded 1->0 toggle. "
         "SymbiYosys (`" + ENGINE + "`) checked whether it can change after the first reset, for every input "
         "sequence (inputs free; the first reset held until every clock has had "
         f"{RESET_EDGES} rising edges). PROVEN bits are left out of the toggle coverage; the others stay counted. "
         "A counterexample uses free inputs, so it does not show that legal stimulus reaches the point. "
         "Every task also asserts that the checked phase is never reached; that guard must fail, else the task "
         "concludes nothing (its bits stay counted). A control assertion states the same property on a flop "
         "output that the simulation toggled many times; it must fail too, else the model does not match the "
         "simulation and the task concludes nothing.", "",
         f"RTL SHA-256 `{rec.get('rtl_sha256', '')[:16]}...`", ""]
    shown = {k: c for k, c in (rec.get("configs") or {}).items() if keys is None or k in keys}
    other = len(rec.get("configs") or {}) - len(shown)
    if other:
        L += [f"{other} record(s) of configurations that are not part of this run are kept in unr.json "
              "(not shown, not applied).", ""]
    for key, conf in sorted(shown.items()):
        L += [f"## Configuration {conf.get('name', key)} (`{key}`)", "",
              f"Parameters {json.dumps(conf.get('params') or {})}; macros {', '.join(conf.get('defines') or []) or 'none'}; "
              + (f"clocks {'free (multiclock on)' if conf.get('multiclock') else 'one global clock'}; "
               if "multiclock" in conf else "")
              + f"{conf.get('tasks') or 0} SymbiYosys task(s)"
              + (f"; control {_ctl_md(conf['control'])}" if conf.get("control") else "") + ".", ""]
        if conf.get("error"):
            L += [f"Error: {conf['error']}", ""]
        L += ["| Result | Bits | Signals |", "|---|---|---|"]
        for key2, label in (("proven", "PROVEN constant"), ("cex", "counterexample"), ("open", "no result (time limit)")):
            m = conf.get(key2) or {}
            L.append(f"| {label} | {_count(m)} | {len(m)} |")
        L.append(f"| not in this netlist | | {len(conf.get('absent') or [])} |")
        if conf.get("vacuous_tasks"):
            L.append(f"| tasks whose guard or control did not fail (nothing concluded) | | {conf['vacuous_tasks']} tasks |")
        L.append(f"| input ports (free in the model) | | {len(conf.get('inputs') or [])} |")
        L.append("")
        if conf.get("proven"):
            L += ["PROVEN constant after the first reset:", ""]
            L += [f"- `{s}` [{t}]" for s, t in sorted(conf["proven"].items())]
            L.append("")
    branches = {k: c for k, c in (rec.get("branches") or {}).items() if keys is None or k in keys}
    if branches:
        L += ["# Branches never executed after the first reset (nnc/unrbranch.py)", "",
              "Each IF branch or case item below had no hit. A marker in an instrumented copy of the RTL (a flop "
              "that toggles when the branch runs, or in a combinational block a signal set to 1 there) was "
              "checked the same way; a copy is used only when Verilator shows every marker as the first "
              "statement of its branch. A branch PROVEN in every configuration leaves the block coverage with "
              "the lines that no other point covers. Key: instance, file, line, column, kind.", ""]
        for key, conf in sorted(branches.items()):
            L += [f"## Configuration {conf.get('name', key)} (`{key}`)", "",
                  f"{conf.get('tasks') or 0} SymbiYosys task(s)"
                  + (f"; control {_ctl_md(conf['control'])}" if conf.get("control") else "") + ".", ""]
            if conf.get("error"):
                L += [f"Error: {conf['error']}", ""]
            L += ["| Result | Branches |", "|---|---|"]
            for k2, label in (("proven", "PROVEN never executed"), ("cex", "counterexample"),
                              ("open", "no result (time limit)")):
                L.append(f"| {label} | {len(conf.get(k2) or [])} |")
            for reason, ks in sorted((conf.get("skipped") or {}).items()):
                L.append(f"| not tried: {reason} | {len(ks)} |")
            if conf.get("vacuous_tasks"):
                L.append(f"| tasks whose guard or control did not fail (nothing concluded) | {conf['vacuous_tasks']} tasks |")
            L.append("")
            if conf.get("proven"):
                L += ["PROVEN never executed after the first reset:", ""]
                L += [f"- `{k[1]}:{k[2]}` {k[4]} (column {k[3]}) in `{k[0] or 'top'}`" for k in conf["proven"]]
                L.append("")
    exprs = {k: c for k, c in (rec.get("expressions") or {}).items() if keys is None or k in keys}
    if exprs:
        L += ["# Expression points never hit after the first reset (nnc/unrexpr.py)", "",
              "Each term combination below had no hit. A marker declared at module level in an instrumented copy "
              "of the RTL (a wire that is 1 exactly when the combination holds) was checked the same way: PROVEN "
              "means the combination never holds after the first reset, so the point can never be hit. A "
              "combination is tried only when its terms read module-level signals with the same meaning as at "
              "the expression. A point PROVEN in every configuration leaves the expression coverage. Key: "
              "instance, file, line, column, combination.", ""]
        for key, conf in sorted(exprs.items()):
            L += [f"## Configuration {conf.get('name', key)} (`{key}`)", "",
                  f"{conf.get('tasks') or 0} SymbiYosys task(s)"
                  + (f"; control {_ctl_md(conf['control'])}" if conf.get("control") else "") + ".", ""]
            if conf.get("error"):
                L += [f"Error: {conf['error']}", ""]
            L += ["| Result | Points |", "|---|---|"]
            for k2, label in (("proven", "PROVEN never hit"), ("cex", "counterexample"),
                              ("open", "no result (time limit)")):
                L.append(f"| {label} | {len(conf.get(k2) or [])} |")
            for reason, ks in sorted((conf.get("skipped") or {}).items()):
                L.append(f"| not tried: {reason} | {len(ks)} |")
            if conf.get("vacuous_tasks"):
                L.append(f"| tasks whose guard or control did not fail (nothing concluded) | {conf['vacuous_tasks']} tasks |")
            L.append("")
            if conf.get("proven"):
                L += ["PROVEN never hit after the first reset:", ""]
                L += [f"- `{k[1]}:{k[2]}` `{k[4]}` (column {k[3]}) in `{k[0] or 'top'}`" for k in conf["proven"]]
                L.append("")
    return "\n".join(L) + "\n"


def apply(work: Path, host: SimHost | None, contract: dict, rtl_dir: Path, dat_path: Path, rtl_names: list[str],
          scope: dict | None, configs: list[dict], frontend: str, *, prove: bool = False, parallel: int = 4,
          say=print, cut: dict | None = None) -> tuple[dict | None, dict | None]:
    """The scope with the recorded (and, with `prove`, newly proven) unreachable bits, and a summary for
    the coverage result. `configs`: [{"name", "params" (values), "defines"}]. `cut` (config unr_cut):
    {"modules": [...], "defines": [...]}, see cut_check."""
    path = work / "unr.json"
    if not prove and not path.is_file():
        return scope, None
    rhash = rtl_sha256(rtl_dir)
    rec = load(path, rhash)
    mods: list[str] = []
    if cut:
        why = cut_check(rtl_dir, cut)
        if why:
            say(f"[unr] unr_cut refused: {why}")
            return scope, {"status": f"unr_cut refused: {why}"[:300]}
        mods = sorted(cut["modules"])
        configs = [{**c, "defines": sorted(set(c["defines"]) | set(cut.get("defines") or []))} for c in configs]
    tag = frontend + ("+cut:" + ",".join(mods) if mods else "")
    keys = [config_key(c["params"], c["defines"], tag) for c in configs]
    if prove and host is not None and dat_path.is_file():
        cands = candidates(dat_path, rtl_names, scope)
        ctl = controls(dat_path, rtl_names, fields=(scope or {}).get("fields"))
        say(f"[unr] {sum(len(b) for b in cands.values())} candidate bit(s) in {len(cands)} signal(s)")
        for c, key in zip(configs, keys):
            if key in rec["configs"]:       # names of an earlier version that are no candidate any more
                old = rec["configs"][key]
                old["absent"] = sorted(set(old.get("absent") or []) & set(cands))
            todo = undecided(rec["configs"].get(key), cands)
            if not todo and key in rec["configs"]:
                continue
            new = prove_config(host, contract, rtl_dir, c["params"], c["defines"], frontend, todo, parallel=parallel,
                               control_bits=ctl, cut=mods)
            new.update(name=c["name"], params={k: str(v) for k, v in c["params"].items()}, defines=c["defines"])
            if mods:
                new["cut"] = mods
            rec["configs"][key] = merge_record(rec["configs"].get(key), new)
            say(f"[unr] {c['name']}: proven {_count(new['proven'])}, counterexample {_count(new['cex'])}, "
                f"no result {_count(new['open'])}" + (f"; {new['error']}" if new.get("error") else ""))
        _prove_branches(rec, keys, configs, host, contract, rtl_dir, dat_path, rtl_names, frontend, parallel,
                        ctl, mods, say)
        _prove_exprs(rec, keys, configs, host, contract, rtl_dir, dat_path, rtl_names, frontend, parallel,
                     ctl, mods, say)
        # a record of another configuration that only holds an error has nothing to reuse
        rec["configs"] = {k: v for k, v in rec["configs"].items()
                          if k in keys or not v.get("error") or _count(v.get("proven")) + _count(v.get("cex"))}
        for part in ("branches", "expressions"):
            rec[part] = {k: v for k, v in (rec.get(part) or {}).items()
                         if k in keys or not v.get("error") or v.get("proven") or v.get("cex")}
        path.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
        (work / "unr.md").write_text(to_markdown(work.parent.name, rec, keys), encoding="utf-8")
    bits = proven_bits(rec, keys)
    blocks = unrbranch.proven_blocks(rec.get("branches") or {}, keys)
    exprs = unrbranch.proven_blocks(rec.get("expressions") or {}, keys)
    if bits is None and not blocks and not exprs:
        return scope, ({"status": "no record for every configuration", "record": "work/unr.json"} if rec["configs"] else None)
    new_scope = dict(scope or {"packages": [], "kept": {}})
    info: dict = {"status": "applied", "record": "work/unr.json"}
    if bits is not None:
        new_scope["proven"] = {s: cov.line_ranges(b) for s, b in sorted(bits.items())}
        info.update(proven_bits=sum(len(b) for b in bits.values()), signals=len(bits))
    if blocks:
        new_scope["proven_blocks"] = blocks
        info["proven_branches"] = len(blocks)
    if exprs:
        new_scope["proven_exprs"] = exprs
        info["proven_expressions"] = len(exprs)
    return new_scope, info


def _prove_branches(rec: dict, keys: list[str], configs: list[dict], host: SimHost, contract: dict, rtl_dir: Path,
                    dat_path: Path, rtl_names: list[str], frontend: str, parallel: int, ctl: list, mods: list[str],
                    say) -> None:
    """Prove, per configuration, the branches that no run executed (nnc/unrbranch.py) into rec["branches"]."""
    import tempfile
    todo_all = unrbranch.targets(dat_path, rtl_names)
    say(f"[unr] {len(todo_all)} branch(es) never executed")
    br = rec.setdefault("branches", {})
    for c, key in zip(configs, keys):
        todo = unrbranch.undecided(br.get(key), todo_all)
        if not todo and key in br:
            continue
        with tempfile.TemporaryDirectory(prefix="nnc_unrb_") as tmp:
            new = unrbranch.prove_config(host, contract, rtl_dir, c["params"], c["defines"], frontend, todo,
                                         Path(tmp) / "rtl", parallel=parallel, control_bits=ctl, cut=mods)
        new.update(name=c["name"], params={k: str(v) for k, v in c["params"].items()}, defines=c["defines"])
        br[key] = unrbranch.merge(br.get(key), new)
        skipped = sum(len(v) for v in (new.get("skipped") or {}).values())
        say(f"[unr] {c['name']} branches: proven {len(new['proven'])}, counterexample {len(new['cex'])}, "
            f"no result {len(new['open'])}, not tried {skipped}" + (f"; {new['error']}" if new.get("error") else ""))


def _prove_exprs(rec: dict, keys: list[str], configs: list[dict], host: SimHost, contract: dict, rtl_dir: Path,
                 dat_path: Path, rtl_names: list[str], frontend: str, parallel: int, ctl: list, mods: list[str],
                 say) -> None:
    """Prove, per configuration, the expression points that no run hit (nnc/unrexpr.py) into
    rec["expressions"]."""
    import tempfile
    todo_all = unrexpr.targets(dat_path, rtl_names)
    say(f"[unr] {len(todo_all)} expression point(s) never hit")
    ex = rec.setdefault("expressions", {})
    for c, key in zip(configs, keys):
        todo = list(unrbranch.undecided(ex.get(key), {k: [] for k in todo_all}))
        if not todo and key in ex:
            continue
        with tempfile.TemporaryDirectory(prefix="nnc_unre_") as tmp:
            new = unrexpr.prove_config(host, contract, rtl_dir, c["params"], c["defines"], frontend, todo,
                                       Path(tmp) / "rtl", parallel=parallel, control_bits=ctl, cut=mods)
        new.update(name=c["name"], params={k: str(v) for k, v in c["params"].items()}, defines=c["defines"])
        ex[key] = unrbranch.merge(ex.get(key), new)
        skipped = sum(len(v) for v in (new.get("skipped") or {}).values())
        say(f"[unr] {c['name']} expressions: proven {len(new['proven'])}, counterexample {len(new['cex'])}, "
            f"no result {len(new['open'])}, not tried {skipped}" + (f"; {new['error']}" if new.get("error") else ""))

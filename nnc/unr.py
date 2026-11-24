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
    fall: dict[tuple[str, int], int] = {}
    for kv, _name, metric, _line, _span, count in cov._records(dat_path, set(rtl_names)):
        if metric != "toggle":
            continue
        bit = cov.toggle_bit(kv)
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


def controls(dat_path: Path, rtl_names: list[str], limit: int = 500, least: int = 4) -> list[tuple[str, int]]:
    """Bits the simulation toggled at least `least` times in each direction, most toggled first: the control
    assertion of every task (it must FAIL: a model in which such a bit cannot change does not match the
    simulation, and the task concludes nothing)."""
    seen: dict[tuple[str, int], list[int]] = defaultdict(lambda: [0, 0])
    for kv, _name, metric, _line, _span, count in cov._records(dat_path, set(rtl_names)):
        if metric == "toggle":
            bit = cov.toggle_bit(kv)
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
def read_commands(top: str, srcs: list[str], params: dict, defines: list[str], frontend: str) -> str:
    """Yosys commands reading the DUT with the run's parameters and macros (run in the folder of the sources)."""
    defs = " ".join(f"-D{d}" for d in defines)
    if frontend == "slang":
        return (f"read_slang {defs} -I . --top {top} " + "".join(f"-G {k}={v} " for k, v in params.items())
                + " ".join(srcs) + f"\nhierarchy -top {top}")
    return (f"read_verilog -sv {defs} -I. " + " ".join(srcs) + f"\nhierarchy -top {top}"
            + "".join(f" -chparam {k} {v}" for k, v in params.items()))


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


def wrapper(info: dict, iface: dict, group: list[tuple[int, str, list[int]]], free_clocks: bool = True,
            control: tuple[str, int] | None = None) -> str:
    """The formal top of one task: the DUT with its candidate signals exposed, the reset assumption of the
    first reset, and one assertion per candidate bit. `group`: (k, signal, bit indices).

    With free clocks (`multiclock on`) the first reset lasts until every clock has had RESET_EDGES rising
    edges; with one global clock every step is a clock edge (the clock input cannot be read as data there), so
    it lasts RESET_EDGES + 1 steps. The guard assertion GUARD (`!nnc_armed`) must FAIL: it shows that the
    checked phase is reached, else every PASS of the task would be vacuous. The control assertion CONTROL is
    the same property on a bit the simulation toggled many times (`control`); it must FAIL too, else the model
    does not match the simulation and the task concludes nothing."""
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
    if control:
        cw = wires[control[0]][0]
        lines.append(f"  wire {decl(cw)}nnc_sc;")
        conns.append(f".{control[0]}(nnc_sc)" if control[0] in ports else ".nnc_pc(nnc_sc)")
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
    if control:
        lines.append(f"  reg {decl(cw)}nnc_fc;")
        caps.append("nnc_fc <= nnc_sc;")
    lines.append("  always @($global_clock) if (!nnc_init && !nnc_armed) begin nnc_armed <= 1'b1; "
                 + " ".join(caps) + " end")
    lines.append(f"  always @* {GUARD}: assert (!nnc_armed);     // must FAIL: the checked phase is reached")
    lines.append("  always @* if (nnc_armed) begin")
    if control:
        p = position(wires[control[0]], control[1])
        sel = f"[{p}]" if cw > 1 else ""
        lines.append(f"    {CONTROL}: assert (nnc_sc{sel} == nnc_fc{sel});   // must FAIL: toggled in simulation")
    for k, sig, bits in group:
        for idx in bits:
            p = position(wires[sig], idx)
            sel = f"[{p}]" if wires[sig][0] > 1 else ""
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
          control: tuple[str, int] | None = None) -> dict[str, object]:
    srcs = [f.name for f in rtl]
    files: dict[str, object] = {f"src/{f.name}": f for f in _all_rtl(rtl)}
    free = multiclock(info, len(clock_names(iface)))
    mc = "on" if free else "off"
    read = read_commands(top, srcs, params, defines, frontend)
    for n, group in enumerate(groups):
        wname = f"nnc_unr_top_{n:03d}.sv"
        files[f"src/{wname}"] = wrapper(info, iface, group, free, control)
        inner = [(f"nnc_p{k}", s) for k, s, _b in group if s not in info["ports"]]
        if control and control[0] not in info["ports"]:
            inner.append(("nnc_pc", control[0]))
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
_GUARD = re.compile(rf"^nnc_unr_top\.({GUARD}|{CONTROL})\s+(\w+)\s*$")


def parse_statuses(text: str) -> dict[tuple[int, int], str]:
    """{(k, bit): status} of one task; empty when its guard, or its control when it has one, did not FAIL
    (nothing is concluded)."""
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
    return sentinel.get(GUARD) == "FAIL" and sentinel.get(CONTROL, "FAIL") == "FAIL"


def vacuous(text: str) -> bool:
    """The task ran (some status line) but its guard or its control did not FAIL."""
    lines = [ln.strip() for ln in text.splitlines()]
    sentinel = {g.group(1): g.group(2) for ln in lines if (g := _GUARD.match(ln))}
    return any(_STATUS.match(ln) for ln in lines) and not _conclusive(sentinel)


def prove_config(host: SimHost, contract: dict, rtl_dir: Path, params: dict, defines: list[str], frontend: str,
                 cands: dict[str, set[int]], *, parallel: int = 4, timeout_s: int = TASK_TIMEOUT_S,
                 control_bits: list[tuple[str, int]] | None = None) -> dict:
    """Prove the candidates in one configuration: {"proven", "cex", "open": {signal: ranges}, "absent",
    "inputs": [signals], "multiclock", "tasks", "error"}."""
    top, iface = contract["top"], contract["interface"]
    rtl = rtl_files(rtl_dir)
    files = {f"src/{f.name}": f for f in _all_rtl(rtl)}
    cmds = read_commands(top, [f.name for f in rtl], params, defines, frontend).replace("\n", "; ")
    r1 = host.run(files, NETLIST_RUN.format(cmds=cmds), ["nnc_unr_netlist.json", "nnc_unr_netlist.log"],
                  timeout_s=1800, tag="unr_netlist")
    nf = Path(r1.out_dir) / "nnc_unr_netlist.json"
    info = netlist_info(json.loads(nf.read_text(encoding="utf-8"))) if nf.is_file() else None
    if info is None:
        log = Path(r1.out_dir) / "nnc_unr_netlist.log"
        tail = log.read_text(encoding="utf-8", errors="replace").splitlines()[-6:] if log.is_file() else []
        return {"error": "no netlist: " + " | ".join(tail), "proven": {}, "cex": {}, "open": {}, "absent": [],
                "inputs": []}
    groups, skipped = plan(cands, info)
    control = pick_control(control_bits or [], info, set(cands))
    rec = {"proven": defaultdict(set), "cex": defaultdict(set), "open": defaultdict(set), **skipped,
           "multiclock": multiclock(info, len(clock_names(iface))), "tasks": len(groups),
           "control": f"{control[0]}[{control[1]}]" if control else None}
    if groups:
        f2 = build(top, iface, rtl, params, defines, frontend, info, groups, timeout_s, control)
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
    """The candidates without a PROVEN or counterexample result in this configuration (time limits are retried)."""
    if not rec_conf:
        return {s: set(b) for s, b in cands.items()}
    done: dict[str, set[int]] = defaultdict(set)
    for key in ("proven", "cex"):
        for s, t in (rec_conf.get(key) or {}).items():
            done[s] |= cov._expand(t)
    skip = set(rec_conf.get("absent") or []) | set(rec_conf.get("inputs") or [])
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
    for key in ("absent", "inputs"):
        out[key] = sorted(set(conf.get(key) or []) | set(new.get(key) or []))
    for key in ("multiclock", "error", "control"):
        if key in new:
            out[key] = new[key]
    out["tasks"] = int(conf.get("tasks", 0)) + int(new.get("tasks", 0))
    # inconclusive bits stay "open" and are tried again: only the latest run's count describes the record
    out["vacuous_tasks"] = int(new.get("vacuous_tasks", conf.get("vacuous_tasks", 0)))
    return out


def _count(m: dict) -> int:
    return sum(len(cov._expand(t)) for t in (m or {}).values())


def to_markdown(name: str, rec: dict) -> str:
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
    for key, conf in sorted((rec.get("configs") or {}).items()):
        L += [f"## Configuration {conf.get('name', key)} (`{key}`)", "",
              f"Parameters {json.dumps(conf.get('params') or {})}; macros {', '.join(conf.get('defines') or []) or 'none'}; "
              + (f"clocks {'free (multiclock on)' if conf.get('multiclock') else 'one global clock'}; "
               if "multiclock" in conf else "")
              + f"{conf.get('tasks') or 0} SymbiYosys task(s)"
              + (f"; control `{conf['control']}`" if conf.get("control") else "") + ".", ""]
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
    return "\n".join(L) + "\n"


def apply(work: Path, host: SimHost | None, contract: dict, rtl_dir: Path, dat_path: Path, rtl_names: list[str],
          scope: dict | None, configs: list[dict], frontend: str, *, prove: bool = False, parallel: int = 4,
          say=print) -> tuple[dict | None, dict | None]:
    """The scope with the recorded (and, with `prove`, newly proven) unreachable bits, and a summary for
    the coverage result. `configs`: [{"name", "params" (values), "defines"}]."""
    path = work / "unr.json"
    if not prove and not path.is_file():
        return scope, None
    rhash = rtl_sha256(rtl_dir)
    rec = load(path, rhash)
    keys = [config_key(c["params"], c["defines"], frontend) for c in configs]
    if prove and host is not None and dat_path.is_file():
        cands = candidates(dat_path, rtl_names, scope)
        ctl = controls(dat_path, rtl_names)
        say(f"[unr] {sum(len(b) for b in cands.values())} candidate bit(s) in {len(cands)} signal(s)")
        for c, key in zip(configs, keys):
            todo = undecided(rec["configs"].get(key), cands)
            if not todo and key in rec["configs"]:
                continue
            new = prove_config(host, contract, rtl_dir, c["params"], c["defines"], frontend, todo, parallel=parallel,
                               control_bits=ctl)
            new.update(name=c["name"], params={k: str(v) for k, v in c["params"].items()}, defines=c["defines"])
            rec["configs"][key] = merge_record(rec["configs"].get(key), new)
            say(f"[unr] {c['name']}: proven {_count(new['proven'])}, counterexample {_count(new['cex'])}, "
                f"no result {_count(new['open'])}" + (f"; {new['error']}" if new.get("error") else ""))
        path.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
        (work / "unr.md").write_text(to_markdown(work.parent.name, rec), encoding="utf-8")
    bits = proven_bits(rec, keys)
    if bits is None:
        return scope, ({"status": "no record for every configuration", "record": "work/unr.json"} if rec["configs"] else None)
    new_scope = {**(scope or {"packages": [], "kept": {}}),
                 "proven": {s: cov.line_ranges(b) for s, b in sorted(bits.items())}}
    return new_scope, {"status": "applied", "record": "work/unr.json", "proven_bits": sum(len(b) for b in bits.values()),
                       "signals": len(bits)}

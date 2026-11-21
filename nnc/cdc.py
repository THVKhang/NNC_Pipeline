"""Structural clock- and reset-domain crossing check of the RTL (`nnc cdc`, no LLM).

RTL rule RR-33 says a signal crosses between clock domains only through the synchronizer structure the
specification describes. This module checks the structure on the flattened Yosys netlist of the DUT
(`proc; flatten; memory; opt_clean`, the parameters of each run-set configuration):

1. Every flop gets the domain of its clock port. Clocks of a design whose contract says
   `clock_relation: async` are separate domains; otherwise all clocks are one synchronous domain. An input
   port belongs to the domain of its contract `domain` column; a port marked ASYNC, or listed in the
   design config `cdc_async_inputs`, is asynchronous to every clock.
2. The combinational cone of each flop's data, enable and synchronous reset gives its sources (flops and
   input ports). A source of another domain is a crossing.
3. A crossing is classified:
   - SYNC: the flop takes the source bit directly (no logic) and a second flop of its domain takes the
     first one directly; the first flop feeds nothing else. Stages are counted.
   - SYNC_MULTIBIT: several bits of one source register cross through separate synchronizers. Correct
     only if at most one bit changes at a time (gray code) or a handshake holds the value: for review.
   - QUALIFIED: data of another domain captured under the control of a signal derived from a synchronizer
     of the destination domain (an async FIFO's read data, a handshake's payload). For review.
   - FIRST_STAGE_READ: the first synchronizer flop also feeds logic before the signal settles. Error.
   - UNSYNC: none of the above. Error (RR-33).
4. Resets (RDC): the asynchronous reset of each flop is traced to its sources. A reset port of another
   domain, or a reset made by logic of another domain, is reported for review; the contract gives each
   reset port its clock.

This is a structural check, not a commercial CDC tool: it finds missing or misused synchronizers. It does not
prove gray coding or handshake protocols; formal checks and simulation keep that job.
"""
from __future__ import annotations

import re
from collections import defaultdict

FF_TYPES = {"$dff", "$dffe", "$adff", "$adffe", "$sdff", "$sdffe", "$sdffce", "$aldff", "$aldffe",
            "$dffsr", "$dffsre"}
DATA_PORTS = ("D", "EN", "SRST")
RESET_PORTS = ("ARST", "CLR", "SET", "AD", "ALOAD")
ASYNC = "ASYNC"
ERRORS = ("UNSYNC", "FIRST_STAGE_READ")


def _top(netlist: dict) -> dict | None:
    mods = netlist.get("modules") or {}
    tops = [m for m in mods.values() if str((m.get("attributes") or {}).get("top", "0")).strip("0")]
    return tops[0] if len(tops) == 1 else None


def domains_of(contract: dict, async_inputs: list[str] | None = None) -> tuple[dict, dict, dict]:
    """(clock port -> domain, input port -> domain, reset port -> domain) from the contract interface."""
    iface = contract["interface"]
    clocks = [c["name"] for c in iface.get("clocks") or []] or ([iface["clock"]] if iface.get("clock") else [])
    separate = str(iface.get("clock_relation") or "").lower() == "async"
    clk_dom = {c: (c if separate else "SYNC") for c in clocks}
    by_label = {}
    for c in iface.get("clocks") or []:
        if c.get("domain"):
            by_label[c["domain"].upper()] = clk_dom.get(c["name"])
    resets = {(_name(r) or ""): r for r in iface.get("resets") or []}
    single = next(iter(set(clk_dom.values()))) if len(set(clk_dom.values())) == 1 else None
    inp, rst = {}, {}
    for p in iface["ports"]:
        if p["direction"].lower() != "input" or p["name"] in clk_dom:
            continue
        label = str(p.get("domain") or "").strip().upper()
        if p["name"] in (async_inputs or []) or label == ASYNC:
            dom = ASYNC
        else:
            dom = by_label.get(label) or single or "UNKNOWN"
        if p["name"] in resets:
            r = resets[p["name"]]
            rst[p["name"]] = clk_dom.get(r.get("clock")) or dom
        else:
            inp[p["name"]] = dom
    return clk_dom, inp, rst


def _name(x):
    return x.get("name") if isinstance(x, dict) else x


def analyse(netlist: dict, contract: dict, async_inputs: list[str] | None = None) -> dict:
    """Crossings and resets of one elaborated configuration (see the module docstring)."""
    top = _top(netlist)
    if top is None:
        return {"status": "error", "error": "no single top module in the netlist"}
    clk_dom, in_dom, rst_dom = domains_of(contract, async_inputs)
    port_of: dict[int, tuple[str, int]] = {}
    out_ports = {}
    for pname, p in (top.get("ports") or {}).items():
        for i, b in enumerate(p.get("bits") or []):
            if isinstance(b, int):
                if p["direction"] == "input":
                    port_of[b] = (pname, i)
        if p["direction"] == "output":
            out_ports[pname] = p.get("bits") or []
    names: dict[int, str] = {}
    for n, net in sorted((top.get("netnames") or {}).items(), key=lambda kv: (kv[1].get("hide_name", 0), len(kv[0]))):
        for i, b in enumerate(net.get("bits") or []):
            if isinstance(b, int) and b not in names:
                names[b] = f"{n}[{i}]" if len(net["bits"]) > 1 else n
    driver: dict[int, str] = {}
    readers: dict[int, list[tuple[str, str]]] = defaultdict(list)
    cells = top.get("cells") or {}
    for cname, c in cells.items():
        dirs = c.get("port_directions") or {}
        for port, bits in (c.get("connections") or {}).items():
            for b in bits:
                if not isinstance(b, int):
                    continue
                if dirs.get(port) == "output":
                    driver[b] = cname
                else:
                    readers[b].append((cname, port))
    ffs = {n: c for n, c in cells.items() if c.get("type") in FF_TYPES}
    ff_q = {}                                            # Q bit -> (ff cell, index)
    for n, c in ffs.items():
        for i, b in enumerate(c["connections"].get("Q") or []):
            if isinstance(b, int):
                ff_q[b] = (n, i)

    def domain(ff: str) -> str:
        clk = (ffs[ff]["connections"].get("CLK") or [None])[0]
        if clk in port_of and port_of[clk][0] in clk_dom:
            return clk_dom[port_of[clk][0]]
        return f"DERIVED:{names.get(clk, clk)}"

    dom = {n: domain(n) for n in ffs}
    memo: dict[int, frozenset] = {}

    def cone(bit) -> frozenset:
        """Sources of a bit: ('ff', cell, i) or ('in', port, i), through combinational cells."""
        if not isinstance(bit, int):
            return frozenset()
        if bit in memo:
            return memo[bit]
        memo[bit] = frozenset()                          # breaks combinational loops
        if bit in ff_q:
            res = frozenset({("ff",) + ff_q[bit]})
        elif bit in port_of:
            res = frozenset({("in",) + port_of[bit]})
        elif bit in driver and driver[bit] not in ffs:
            c = cells[driver[bit]]
            dirs = c.get("port_directions") or {}
            acc: set = set()
            for port, bits in c["connections"].items():
                if dirs.get(port) != "output":
                    for b in bits:
                        acc |= cone(b)
            res = frozenset(acc)
        else:
            res = frozenset()
        memo[bit] = res
        return res

    def src_dom(s) -> str:
        if s[0] == "ff":
            return dom[s[1]]
        p = s[1]
        return clk_dom.get(p) or in_dom.get(p) or rst_dom.get(p) or "UNKNOWN"

    def src_name(s) -> str:
        if s[0] == "in":
            return f"{s[1]}[{s[2]}]" if s[2] else s[1]
        b = ffs[s[1]]["connections"]["Q"][s[2]]
        return names.get(b, f"{s[1]}.Q[{s[2]}]")

    def is_reset_port(s) -> bool:
        return s[0] == "in" and s[1] in rst_dom

    # Synchronizer chains: a flop that takes a bit of another domain directly, followed by flops of its own
    # domain that take the previous stage directly.
    def direct_src(ff: str, i: int):
        d = ffs[ff]["connections"].get("D") or []
        b = d[i] if i < len(d) else None
        if b in ff_q:
            return ("ff",) + ff_q[b]
        if b in port_of:
            return ("in",) + port_of[b]
        return None

    next_stage: dict[tuple[str, int], tuple[str, int]] = {}
    for n, c in ffs.items():
        for i in range(len(c["connections"].get("Q") or [])):
            s = direct_src(n, i)
            if s and s[0] == "ff" and dom[s[1]] == dom[n] and not _gated(c):
                next_stage[(s[1], s[2])] = (n, i)
    sync_out: set[tuple[str, int]] = set()               # stages 2.. of recognised synchronizers
    synced: set[tuple] = set()                           # (source, destination domain) of each synchronizer
    records = []
    multibit: dict[tuple, list] = defaultdict(list)
    for n, c in sorted(ffs.items()):
        q = c["connections"].get("Q") or []
        for i in range(len(q)):
            srcs = set()
            for port in DATA_PORTS:
                bits = c["connections"].get(port) or []
                for b in (bits[i:i + 1] if port == "D" else bits):
                    srcs |= cone(b)
            cross = {s for s in srcs if src_dom(s) != dom[n] and not is_reset_port(s)
                     and src_dom(s) != "UNKNOWN"}
            if not cross:
                continue
            ds = direct_src(n, i)
            rec = {"flop": names.get(q[i], f"{n}[{i}]"), "domain": dom[n],
                   "from": sorted({src_name(s) for s in cross}),
                   "from_domains": sorted({src_dom(s) for s in cross})}
            if ds and set(srcs) == {ds} and ds in cross and not _gated(c):
                # The chain goes on while a stage feeds only the next one; every stage after the first
                # carries the synchronized signal.
                chain = [(n, i)]
                while chain[-1] in next_stage and len(chain) < 8:
                    nxt = next_stage[chain[-1]]
                    if len(chain) > 1:
                        cq = ffs[chain[-1][0]]["connections"]["Q"][chain[-1][1]]
                        if {r[0] for r in readers.get(cq, [])} != {nxt[0]}:
                            break
                    chain.append(nxt)
                stages = len(chain)
                if stages >= 2:
                    first_q = q[i]
                    second = chain[1]
                    others = [r for r in readers.get(first_q, []) if r[0] != second[0]]
                    rec["stages"] = stages
                    if others:
                        rec["kind"] = "FIRST_STAGE_READ"
                        rec["note"] = f"the first stage also feeds {sorted({o[0] for o in others})[:3]}"
                    else:
                        rec["kind"] = "SYNC"
                        sync_out.update(chain[1:])
                        synced.add((ds, dom[n]))
                        if ds[0] == "ff":
                            multibit[(ds[1], dom[n])].append(rec)
                    records.append(rec)
                    continue
            rec["kind"] = "PENDING"
            rec["_srcs"] = srcs
            records.append(rec)
    # Destination-domain flops derived from a synchronizer output (fixed point over the cones).
    # Destination-domain flops derived from a synchronizer output: level 0 the last synchronizer stage,
    # level k a flop whose cone holds a flop of level k-1 of its own domain (fixed point, by rounds).
    level: dict[tuple[str, int], int] = {x: 0 for x in sync_out}
    rnd = 0
    while True:
        rnd += 1
        new = {}
        for n, c in ffs.items():
            for i in range(len(c["connections"].get("Q") or [])):
                if (n, i) in level:
                    continue
                srcs = set()
                for port in DATA_PORTS:
                    bits = c["connections"].get(port) or []
                    for b in (bits[i:i + 1] if port == "D" else bits):
                        srcs |= cone(b)
                if any(s[0] == "ff" and level.get((s[1], s[2]), rnd) < rnd and dom[s[1]] == dom[n] for s in srcs):
                    new[(n, i)] = rnd
        if not new:
            break
        level.update(new)
    for rec in records:
        if rec["kind"] != "PENDING":
            continue
        srcs = rec.pop("_srcs")
        raw = sorted({src_name(s) for s in srcs if (s, rec["domain"]) in synced})
        if raw:
            rec["kind"] = "UNSYNC"
            rec["note"] = "uses the unsynchronized value of " + ", ".join(raw[:3]) + ", which is also synchronized"
            continue
        cand = {(level[(s[1], s[2])], src_name(s)) for s in srcs if s[0] == "ff" and (s[1], s[2]) in level
                and dom[s[1]] == rec["domain"] and _base(src_name(s)) != _base(rec["flop"])}
        if cand:
            best = min(lv for lv, _ in cand)
            rec["kind"] = "QUALIFIED"
            rec["note"] = "captured under control of " + ", ".join(sorted(nm for lv, nm in cand if lv == best)[:3])
        else:
            rec["kind"] = "UNSYNC"
    for (src_ff, d), recs in multibit.items():
        if len(recs) > 1:
            for r in recs:
                r["kind"] = "SYNC_MULTIBIT"
                r["note"] = f"{len(recs)} bits of one register synchronized separately: gray code or handshake needed"
    # Output ports: an output of one domain driven by logic of another (no flop to synchronize into).
    outputs = []
    out_dom = {p["name"]: p for p in contract["interface"]["ports"] if p["direction"].lower() == "output"}
    labels = {str(c.get("domain") or "").upper(): clk_dom.get(c["name"]) for c in contract["interface"].get("clocks") or []}
    for pname, bits in sorted(out_ports.items()):
        want = labels.get(str((out_dom.get(pname) or {}).get("domain") or "").upper())
        if not want:
            continue
        srcs = set()
        for b in bits:
            srcs |= cone(b)
        other = sorted({src_name(s) for s in srcs if s[0] == "ff" and dom[s[1]] != want})
        if other:
            outputs.append({"port": pname, "domain": want, "from": other[:8], "kind": "OUTPUT_FROM_OTHER_DOMAIN"})
    # Resets.
    resets = []
    for n, c in sorted(ffs.items()):
        for port in RESET_PORTS:
            bits = c["connections"].get(port) or []
            srcs = set()
            for b in bits:
                srcs |= cone(b)
            if not srcs:
                continue
            bad = sorted({src_name(s) for s in srcs if src_dom(s) not in (dom[n], "UNKNOWN")})
            if bad:
                resets.append({"flop": names.get((c["connections"].get("Q") or [None])[0], n), "domain": dom[n],
                               "reset_from": bad[:6], "kind": "RESET_FROM_OTHER_DOMAIN"})
            break
    derived_clocks = sorted({d for d in dom.values() if d.startswith("DERIVED:")})
    counts = defaultdict(int)
    for r in records:
        counts[r["kind"]] += 1
    records = _by_register(records)
    counts["OUTPUT_FROM_OTHER_DOMAIN"] = len(outputs)
    counts["RESET_FROM_OTHER_DOMAIN"] = len(resets)
    counts["DERIVED_CLOCK"] = len(derived_clocks)
    return {"status": "ok", "domains": sorted(set(dom.values())), "flops": len(ffs),
            "inputs": {p: d for p, d in sorted(in_dom.items())}, "crossings": records, "outputs": outputs,
            "resets": _group(resets), "derived_clocks": derived_clocks, "counts": dict(sorted(counts.items()))}


def _base(name: str) -> str:
    """Register name without its bit and generate indices: "u_mem.reg_mem[3][7]" -> "u_mem.reg_mem",
    "gen_bit[2].u_sync.q" -> "gen_bit[*].u_sync.q"."""
    return re.sub(r"\[\d+\]", "[*]", re.sub(r"(\[\d+\])+$", "", name))


def _by_register(records: list[dict]) -> list[dict]:
    """One row per (kind, destination register, domain, source registers, stages): bit-level counts stay in
    'counts', the table stays readable."""
    g: dict[tuple, dict] = {}
    for r in records:
        src = tuple(sorted({_base(s) for s in r["from"]}))
        key = (r["kind"], _base(r["flop"]), r["domain"], src, r.get("stages"))
        row = g.setdefault(key, {"kind": r["kind"], "flop": _base(r["flop"]), "domain": r["domain"],
                                 "from": list(src[:6]) + ([f"... {len(src) - 6} more"] if len(src) > 6 else []), "from_domains": r["from_domains"], "bits": 0,
                                 **({"stages": r["stages"]} if r.get("stages") else {}),
                                 **({"note": r["note"]} if r.get("note") else {})})
        row["bits"] += 1
    return sorted(g.values(), key=lambda x: (x["kind"], x["flop"]))


def _gated(c: dict) -> bool:
    """A flop with an enable or a synchronous reset is not a plain synchronizer stage."""
    conn = c.get("connections") or {}
    return bool(conn.get("EN") or conn.get("SRST"))


def _group(resets: list[dict]) -> list[dict]:
    """One row per (domain, reset sources) with the number of flops and a few names."""
    g: dict[tuple, list[str]] = defaultdict(list)
    for r in resets:
        g[(r["domain"], tuple(r["reset_from"]))].append(r["flop"])
    return [{"domain": d, "reset_from": list(src), "flops": len(fl), "examples": sorted(fl)[:4],
             "kind": "RESET_FROM_OTHER_DOMAIN"} for (d, src), fl in sorted(g.items())]


def verdict(results: list[dict]) -> str:
    """'clean', 'review' or 'violations' over the configurations."""
    if any(r.get("status") != "ok" for r in results):
        return "error"
    errs = sum(r["counts"].get(k, 0) for r in results for k in ERRORS) + sum(
        r["counts"].get("DERIVED_CLOCK", 0) for r in results)
    if errs:
        return "violations"
    review = sum(r["counts"].get(k, 0) for r in results
                 for k in ("SYNC_MULTIBIT", "QUALIFIED", "OUTPUT_FROM_OTHER_DOMAIN", "RESET_FROM_OTHER_DOMAIN"))
    return "review" if review else "clean"


def async_inputs_for(entries: list[str], params: dict) -> list[str]:
    """Ports of config cdc_async_inputs that are asynchronous in a configuration: "port" always,
    "port:PARAM=value" only when the parameter has that value (gpio: cio_gpio_i:GpioAsyncOn=1)."""
    out = []
    for e in entries:
        port, _, cond = e.partition(":")
        if cond:
            k, _, v = cond.partition("=")
            if str(params.get(k.strip())) != v.strip():
                continue
        out.append(port.strip())
    return out


def yosys_script(top: str, srcs: list[str], params: dict, defines: list[str], frontend: str) -> str:
    """Yosys commands that write the flattened netlist of the DUT to nnc_cdc.json."""
    ydefs = " ".join(f"-D{d}" for d in defines)
    if frontend == "slang":
        read = (f"read_slang {ydefs} -I rtl --top {top} " + "".join(f"-G {k}={v} " for k, v in params.items())
                + " ".join(srcs))
        hier = f"hierarchy -top {top}"
    else:
        read = f"read_verilog -sv {ydefs} -Irtl " + " ".join(srcs)
        hier = f"hierarchy -top {top}" + "".join(f" -chparam {k} {v}" for k, v in params.items())
    return f"{read}\n{hier}\nproc\nflatten\nmemory\nopt_clean\nwrite_json nnc_cdc.json\n"


def run(host, contract: dict, rtl: list, configs: list[dict], defines: list[str], frontend: str,
        timeout_s: int = 1800) -> list[dict]:
    """Elaborate each configuration ({"name", "params": full parameter values, "async_inputs"}) on the tool
    host and analyse it. Returns [{"config", "params", "result"}]."""
    import json
    files: dict[str, object] = {f"rtl/{f.name}": f for f in rtl}
    srcs = [f"rtl/{f.name}" for f in rtl if f.suffix in (".sv", ".v")]
    lines = []
    for i, c in enumerate(configs):
        files[f"c{i}.ys"] = yosys_script(contract["top"], srcs, c["params"], defines, frontend)
        lines.append(f"mkdir -p c{i} && yosys -q -l c{i}/yosys.log -s c{i}.ys > /dev/null 2>&1; "
                     f"echo NNC_RC=$? >> c{i}/yosys.log; [ -f nnc_cdc.json ] && mv nnc_cdc.json c{i}/")
    res = host.run(files, "\n".join(lines) + "\n", ["c*/nnc_cdc.json", "c*/yosys.log"], timeout_s=timeout_s, tag="cdc")
    out = []
    for i, c in enumerate(configs):
        p = res.out_dir / f"c{i}" / "nnc_cdc.json"
        if p.is_file():
            try:
                result = analyse(json.loads(p.read_text(encoding="utf-8")), contract, c.get("async_inputs"))
            except (ValueError, KeyError) as e:
                result = {"status": "error", "error": f"netlist not readable: {e}"}
        else:
            log = res.out_dir / f"c{i}" / "yosys.log"
            tail = log.read_text(encoding="utf-8", errors="replace").splitlines()[-6:] if log.is_file() else []
            result = {"status": "error", "error": "yosys wrote no netlist: " + " | ".join(tail)[:500]}
        out.append({"config": c["name"], "params": c["params"], "result": result})
    return out


def to_markdown(design: str, configs: list[dict]) -> str:
    out = [f"# Clock and reset domain crossings: {design}", "",
           "Structural check of RR-33 on the flattened Yosys netlist (nnc/cdc.py). SYNC is a synchronizer of two "
           "or more flops; SYNC_MULTIBIT, QUALIFIED, OUTPUT_FROM_OTHER_DOMAIN and RESET_FROM_OTHER_DOMAIN are for "
           "review; UNSYNC, FIRST_STAGE_READ and DERIVED_CLOCK are errors. It does not prove gray coding or "
           "handshakes.", "", f"Verdict: **{verdict([c['result'] for c in configs])}**", ""]
    for c in configs:
        r = c["result"]
        out += [f"## Configuration {c['config']}", ""]
        if r.get("status") != "ok":
            out += [f"Not analysed: {r.get('error', '')}", ""]
            continue
        out += [f"Domains: {', '.join(r['domains']) or '-'}; {r['flops']} flops. Counts: "
                + ", ".join(f"{k} {v}" for k, v in r["counts"].items() if v), ""]
        asyncs = [p for p, d in r["inputs"].items() if d == ASYNC]
        if asyncs:
            out += [f"Asynchronous inputs: {', '.join(asyncs)}", ""]
        rows = [x for x in r["crossings"]]
        if rows:
            out += ["| Kind | Destination register | Bits | Domain | From | Stages | Note |",
                    "|---|---|---|---|---|---|---|"]
            order = {"UNSYNC": 0, "FIRST_STAGE_READ": 1, "SYNC_MULTIBIT": 2, "QUALIFIED": 3, "SYNC": 4}
            for x in sorted(rows, key=lambda x: (order.get(x["kind"], 9), x["flop"])):
                out.append(f"| {x['kind']} | {x['flop']} | {x.get('bits', 1)} | {x['domain']} | {', '.join(x['from'])} | "
                           f"{x.get('stages', '')} | {x.get('note', '')} |")
            out.append("")
        if r["outputs"]:
            out += ["| Output port | Domain | Driven by flops of another domain |", "|---|---|---|"]
            out += [f"| {o['port']} | {o['domain']} | {', '.join(o['from'])} |" for o in r["outputs"]]
            out.append("")
        if r["resets"]:
            out += ["| Domain | Asynchronous reset from | Flops | Examples |", "|---|---|---|---|"]
            out += [f"| {x['domain']} | {', '.join(x['reset_from'])} | {x['flops']} | {', '.join(x['examples'])} |"
                    for x in r["resets"]]
            out.append("")
        if r["derived_clocks"]:
            out += ["Derived clocks (RR-30): " + ", ".join(r["derived_clocks"]), ""]
    return "\n".join(out) + "\n"

"""Checks of generated RTL by code (docs/RTL_RULES.md): source rules, lint, structure, interface, synthesis.

`check(...)` runs every check that can be decided without a person and returns findings:

    {"rule": "RR-20", "severity": "error" | "warning" | "info", "file": "x.sv", "line": 12, "message": "..."}

Errors and warnings go back to the RTL agent; whatever remains after the last attempt is listed for the
reviewer of gate D2_rtl. Nothing here decides whether the RTL is *correct*: that is the job of the
verification (gates G3/G4), which is generated independently of the RTL.

Steps (the host runs Verilator and Yosys, as for simulation):
  source     regex checks on the text with comments removed (RR-01, 10-12, 20-21, 23, 30-31, 40, 42)
  lint       verilator --lint-only -Wall with the chosen parameter values (RR-40)
  structure  Yosys: read, hierarchy, proc, check; latches, loops, multiple or missing drivers (RR-13, 22)
  interface  Yosys write_json of the top with the chosen parameters: port names, directions, widths (RR-02)
  synthesis  Yosys synth + GF180 liberty (typical and slow corners): cell area, estimated delay (RR-43)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from nnc.params import _value
from nnc.simhost import SimHost

PDK_DIR = "/opt/pdk"
CORNERS = {"tt": "gf180mcu_fd_sc_mcu7t5v0__tt_025C_5v00.lib", "ss": "gf180mcu_fd_sc_mcu7t5v0__ss_125C_4v50.lib"}
ALLOWED_SYSFUNCS = {"clog2", "bits", "signed", "unsigned", "high", "low", "size"}
ABC_SCRIPT = "strash\ndch\nmap\ntopo\nstime -p\n"


def _f(rule: str, sev: str, msg: str, file: str = "", line: int = 0) -> dict:
    return {"rule": rule, "severity": sev, "file": file, "line": line, "message": msg}


def strip_comments(text: str) -> str:
    """Remove // and /* */ comments, keeping line breaks so line numbers stay right."""
    def block(m: re.Match) -> str:
        return "\n" * m.group(0).count("\n")
    text = re.sub(r"/\*.*?\*/", block, text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def _line(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


_SIM_REGION = re.compile(r"`ifndef\s+(?P<m1>\w*SYNTHESIS\w*)(?P<b1>(?:(?!`if).)*?)(?=`else|`endif)"
                         r"|`ifdef\s+(?P<m2>\w*SYNTHESIS\w*)(?:(?!`if).)*?`else(?P<b2>(?:(?!`if).)*?)(?=`endif)", re.S)


def sim_only(code: str) -> tuple[str, list[tuple[str, int]]]:
    """Blank the simulation-only branches (`ifndef X_SYNTHESIS ..., or the `else of `ifdef X_SYNTHESIS).

    A model the specification asks for (for example of metastability) may live there: synthesis defines
    the macro, so it never reaches the netlist. Returns (code, [(macro, line)]) for the reviewer."""
    regions = []
    parts, last = [], 0
    for m in _SIM_REGION.finditer(code):
        body = "b1" if m.group("m1") else "b2"
        s, e = m.span(body)
        regions.append((m.group("m1") or m.group("m2"), _line(code, s)))
        parts += [code[last:s], "\n" * code.count("\n", s, e)]
        last = e
    parts.append(code[last:])
    return "".join(parts), regions


def _blocks(code: str) -> list[tuple[str, int, str]]:
    """(kind, start, body) of each always* block: body runs to the next always/assign/endmodule."""
    starts = [(m.group(1) or "", m.start()) for m in re.finditer(r"\balways(_ff|_comb|_latch)?\b", code)]
    stops = sorted([m.start() for m in re.finditer(r"\b(always(_ff|_comb|_latch)?|assign|endmodule|endgenerate)\b", code)]
                   + [len(code)])
    out = []
    for kind, s in starts:
        end = next(x for x in stops if x > s)
        out.append((kind, s, code[s:end]))
    return out


def source_findings(files: dict[str, str], top: str, clocks: list[str], resets: list[str],
                    rule_ids: set[str]) -> tuple[list[dict], dict]:
    """Rules decided on the text. Returns (findings, traceability {tagged ids, unknown ids, waivers})."""
    out: list[dict] = []
    tagged, unknown, waivers = set(), set(), []
    modules = {}
    for name, text in files.items():
        if not name.endswith(".sv"):
            continue
        code, regions = sim_only(strip_comments(text))
        for macro, ln in regions:
            out.append(_f("RR-10", "info", f"simulation-only code (not under {macro}): not synthesized; reviewer: "
                                           f"check it models only what the specification asks for", name, ln))
        mods =re.findall(r"^\s*module\s+(\w+)", code, re.M)
        if len(mods) != 1:
            out.append(_f("RR-01", "error", f"{len(mods)} modules in the file (one module per file)", name))
        elif mods[0] != Path(name).stem:
            out.append(_f("RR-01", "error", f"module {mods[0]} is in {name}; name the file {mods[0]}.sv", name))
        for m in mods:
            modules[m] = name
        is_top = top in mods
        inputs = set(re.findall(r"\binput\b[^;,()]*?(\w+)\s*(?=[,;)]|$)", code, re.M))
        for pat, rule, what in ((r"\binitial\b", "RR-10", "`initial` block"),
                                (r"(?<![\w)\]#])#\s*[\d.]", "RR-10", "delay `#n`"),
                                (r"##", "RR-10", "`##` delay"),
                                (r"\b(force|release|fork|join|join_any|join_none|wait|event|class|program)\b", "RR-10",
                                 "non-synthesizable keyword"),
                                (r"^\s*(logic|reg|bit|wire)\b[^;=(]*\w\s*=[^=]", "RR-10", "initial value in a declaration"),
                                (r"\binout\b", "RR-12", "`inout` port"),
                                (r"'z\b|\d'[bh]z", "RR-12", "tri-state value"),
                                (r"\bcasex\b", "RR-23", "`casex`"),
                                (r"\balways_latch\b", "RR-20", "`always_latch`")):
            for m in re.finditer(pat, code, re.M):
                out.append(_f(rule, "error", what + f": `{m.group(0).strip()[:40]}`", name, _line(code, m.start())))
        for m in re.finditer(r"\$(\w+)", code):
            if m.group(1) not in ALLOWED_SYSFUNCS:
                out.append(_f("RR-11", "error", f"system task/function `${m.group(1)}`", name, _line(code, m.start())))
        for kind, start, body in _blocks(code):
            ln = _line(code, start)
            if kind == "":
                out.append(_f("RR-20", "error", "plain `always`: use always_ff or always_comb", name, ln))
            elif kind == "_ff":
                sens = re.match(r"always_ff\s*@\s*\(([^)]*)\)", body)
                if not sens:
                    out.append(_f("RR-30", "error", "always_ff without an edge sensitivity list", name, ln))
                else:
                    for edge, sig in re.findall(r"\b(posedge|negedge)\s+(\w+)", sens.group(1)):
                        if is_top and sig in clocks and edge != "posedge":
                            out.append(_f("RR-30", "error", f"clock {sig} used on its falling edge", name, ln))
                        elif is_top and sig not in clocks and sig not in resets:
                            out.append(_f("RR-30", "error", f"`{edge} {sig}`: {sig} is not a clock or reset port of the "
                                                            f"contract (derived or gated clock?)", name, ln))
                        elif not is_top and sig not in inputs:
                            # a submodule receives its clocks and resets through its own input ports
                            out.append(_f("RR-30", "error", f"`{edge} {sig}`: {sig} is not an input port of the "
                                                            f"module (derived or gated clock?)", name, ln))
                    rest = body[sens.end():]
                    rest = re.sub(r"\bfor\s*\([^;]*;", "for(;", rest)          # loop index init
                    rest = re.sub(r"<=|==|!=|>=|===|!==", " ", rest)
                    if re.search(r"(?<![<>=!])=(?!=)", rest):
                        out.append(_f("RR-20", "error", "blocking assignment in always_ff", name, ln))
            elif kind == "_comb":
                if re.search(r"(?:;|\bbegin\b|\belse\b|:)\s*[A-Za-z_][\w.]*(?:\[[^\]]*\])*\s*<=", body):
                    out.append(_f("RR-21", "error", "nonblocking assignment in always_comb", name, ln))
                cases = len(re.findall(r"\bcase[z]?\s*\(", body))
                defaults = len(re.findall(r"\bdefault\s*:", body))
                if cases > defaults:
                    out.append(_f("RR-23", "warning", f"{cases - defaults} case statement(s) without default", name, ln))
        for i, raw in enumerate(text.splitlines(), 1):
            for ids in re.findall(r"//.*?\bREQ:\s*([^\n]*)", raw):
                for rid in re.findall(r"[A-Z][A-Z0-9]*-[\w.\-]+", ids):
                    (tagged if rid in rule_ids else unknown).add(rid)
            if re.search(r"lint_off", raw):
                prev = text.splitlines()[i - 2] if i > 1 else ""
                if "WAIVER:" in raw or "WAIVER:" in prev:
                    waivers.append({"file": name, "line": i, "text": (prev.strip() + " " + raw.strip()).strip()[:200]})
                else:
                    out.append(_f("RR-40", "error", "lint_off pragma without a `// WAIVER: <reason>` comment", name, i))
    if top not in modules:
        out.append(_f("RR-02", "error", f"no module named {top} (the contract's top)"))
    for rid in sorted(unknown):
        out.append(_f("RR-42", "error", f"REQ tag {rid} is not an approved rule ID"))
    if rule_ids and not tagged:
        out.append(_f("RR-42", "warning", "no `// REQ: <rule id>` tags"))
    trace = {"tagged": sorted(tagged), "unknown": sorted(unknown), "waivers": waivers,
             "coverage": round(100.0 * len(tagged) / len(rule_ids), 1) if rule_ids else None}
    return out, trace


def filelist_findings(files: dict[str, str], top: str) -> tuple[list[dict], list[str]]:
    """RR-01: filelist.f names every .sv file once, top module file last."""
    svs = sorted(n for n in files if n.endswith(".sv"))
    fl = files.get("filelist.f")
    if fl is None:
        return [_f("RR-01", "error", "no filelist.f")], svs
    order = [ln.strip() for ln in fl.splitlines() if ln.strip() and not ln.strip().startswith(("//", "#"))]
    out = []
    for n in sorted(set(svs) - set(order)):
        out.append(_f("RR-01", "error", f"{n} is not in filelist.f"))
    for n in sorted(set(order) - set(svs)):
        out.append(_f("RR-01", "error", f"filelist.f names {n}, which does not exist"))
    if order and order[-1] != f"{top}.sv":
        out.append(_f("RR-01", "warning", f"filelist.f should end with the top module file {top}.sv"))
    return out, [n for n in order if n in svs] + [n for n in svs if n not in order]


def port_width(width: str, values: dict[str, int]) -> int | None:
    """Bits of a contract port width for the chosen values; None when it cannot be decided. A width of 0 (an
    optional signal switched off) is left to the specification: the RTL may keep a 1-bit placeholder."""
    w = str(width).strip()
    try:
        n = int(w) if w.isdigit() else _value(w, values)
    except Exception:  # noqa: BLE001
        return None
    return n if n > 0 else None


def _gparams(iface: dict, values: dict[str, int]) -> list[tuple[str, int]]:
    return [(p["name"], values[p["name"]]) for p in iface["parameters"] if not p.get("derived") and p["name"] in values]


def lint(host: SimHost, files: dict[str, str], order: list[str], top: str, iface: dict,
         values: dict[str, int]) -> list[dict]:
    """RR-40: verilator -Wall with the chosen parameters."""
    g = " ".join(f"-G{n}={v}" for n, v in _gparams(iface, values))
    script = (f"verilator --lint-only -Wall -Wno-fatal {g} --top-module {top} {' '.join(order)} > lint.log 2>&1; "
              "echo NNC_RC=$? >> lint.log; cat lint.log")
    res = host.run(files, script, [], timeout_s=600, tag="rtllint")
    out = []
    for ln in res.output.splitlines():
        m = re.match(r"%(Warning|Error)(?:-(\w+))?:\s*(?:([\w./]+):(\d+):(?:\d+:)?)?\s*(.*)", ln)
        if m and not (m.group(1) == "Error" and m.group(5).startswith("Exiting due to")):
            sev = "error" if m.group(1) == "Error" else "warning"
            out.append(_f("RR-40", sev, f"{m.group(2) or 'lint'}: {m.group(5)[:300]}", Path(m.group(3) or "").name,
                          int(m.group(4) or 0)))
    if "NNC_RC=0" not in res.output and not any(f["severity"] == "error" for f in out):
        out.append(_f("RR-40", "error", "verilator failed: " + " | ".join(res.output.splitlines()[-5:])[:400]))
    return out


def _yosys_read(order: list[str], files: dict[str, str]) -> str:
    """Yosys read command; the macros that select the synthesis branch of simulation-only code are defined
    (Yosys itself defines SYNTHESIS only)."""
    macros = sorted({m for n in order for m, _ in sim_only(strip_comments(files.get(n, "")))[1]} - {"SYNTHESIS"})
    return f"read_verilog -sv {' '.join('-D' + m for m in macros)} {' '.join(order)}".replace("  ", " ")


def structure(host: SimHost, files: dict[str, str], order: list[str], top: str, iface: dict,
              values: dict[str, int]) -> tuple[list[dict], dict | None]:
    """RR-13/22 (Yosys proc + check) and RR-02 (ports of the elaborated top). Returns (findings, ports)."""
    chp = "".join(f"chparam -set {n} {v} {top}\n" for n, v in _gparams(iface, values))
    ys = (f"{_yosys_read(order, files)}\n{chp}hierarchy -check -top {top}\nproc\nopt_clean\ncheck\n"
          f"select -assert-none t:$dlatch t:$adlatch t:$dlatchsr\nwrite_json nnc_ports.json\n")
    script = ("yosys -s nnc_struct.ys > ys.log 2>&1; echo NNC_RC=$? >> ys.log; "
              "grep -E 'ERROR|Warning|Latch inferred|NNC_RC|Assertion failed' ys.log | head -80")
    res = host.run({**files, "nnc_struct.ys": ys}, script, ["nnc_ports.json"], timeout_s=900, tag="rtlstruct")
    out = []
    for ln in res.output.splitlines():
        if "Latch inferred" in ln:
            out.append(_f("RR-22", "error", "latch inferred: " + ln.split("Latch inferred", 1)[1].strip()[:200]))
        elif "ERROR" in ln:
            rule = "RR-22" if "Assertion failed" in ln or "selection" in ln else "RR-13"
            out.append(_f(rule, "error", "yosys: " + ln.strip()[:300]))
        elif "Warning" in ln and re.search(r"multiple conflicting drivers|logic loop|no driver|is used but has no driver", ln):
            out.append(_f("RR-22", "error", "yosys: " + ln.strip()[:300]))
    ports = None
    pj = res.out_dir / "nnc_ports.json"
    if pj.is_file():
        try:
            mod = json.loads(pj.read_text(encoding="utf-8"))["modules"]
            key = next((k for k in mod if k == top or k.endswith("\\" + top) or k.startswith(f"$paramod\\{top}\\")
                        or k.startswith(f"$paramod${top}")), None)
            if key is None and len(mod) >= 1:
                key = next((k for k, v in mod.items() if v.get("attributes", {}).get("top")), None)
            if key:
                ports = {n: {"direction": p["direction"], "bits": len(p["bits"])} for n, p in mod[key]["ports"].items()}
        except (ValueError, KeyError):
            ports = None
    return out, ports


def interface_findings(ports: dict | None, iface: dict, values: dict[str, int], top_text: str) -> list[dict]:
    """RR-02: ports and parameters of the top against the contract."""
    out = []
    if ports is None:
        return [_f("RR-02", "error", "the top module could not be elaborated, so its ports were not checked")]
    want = {p["name"]: p for p in iface["ports"]}
    for n in sorted(set(want) - set(ports)):
        out.append(_f("RR-02", "error", f"port {n} of the contract is missing"))
    for n in sorted(set(ports) - set(want)):
        out.append(_f("RR-02", "error", f"port {n} is not in the contract"))
    for n in sorted(set(want) & set(ports)):
        d = want[n]["direction"].lower()
        if d != ports[n]["direction"]:
            out.append(_f("RR-02", "error", f"port {n}: direction {ports[n]['direction']}, contract says {d}"))
        bits = port_width(want[n]["width"], values)
        if bits is not None and bits != ports[n]["bits"]:
            out.append(_f("RR-02", "error", f"port {n}: {ports[n]['bits']} bits, contract says {bits} "
                                            f"(width {want[n]['width']})"))
    code = strip_comments(top_text)
    head = code[:code.find(");") if ");" in code else len(code)]
    declared = set(re.findall(r"\bparameter\b\s+(?:int\s+|integer\s+|logic\s*(?:\[[^\]]*\]\s*)?)?(?:unsigned\s+)?(\w+)\s*=",
                              head))
    free = {p["name"] for p in iface["parameters"] if not p.get("derived")}
    for n in sorted(free - declared):
        out.append(_f("RR-02", "error", f"parameter {n} of the contract is not a parameter of the top module"))
    for n in sorted(declared - free):
        out.append(_f("RR-02", "error", f"parameter {n} is not an overridable parameter of the contract"))
    return out


def synthesis(host: SimHost, files: dict[str, str], order: list[str], top: str, iface: dict,
              values: dict[str, int], pdk_dir: str = PDK_DIR) -> tuple[list[dict], dict]:
    """RR-43: generic synthesis, then cell mapping per corner. Area in um^2, delay in ps (estimates)."""
    chp = "".join(f"chparam -set {n} {v} {top}\n" for n, v in _gparams(iface, values))
    ys = [f"{_yosys_read(order, files)}\n{chp}synth -top {top} -flatten\ntee -o generic_stat.txt stat\n"]
    for c, lib in CORNERS.items():
        p = f"{pdk_dir}/{lib}"
        ys.append(f"design -push-copy\nread_liberty -lib {p}\ndfflibmap -liberty {p}\n"
                  f"abc -liberty {p} -script nnc_abc.scr\nopt_clean\ntee -o stat_{c}.txt stat -liberty {p}\ndesign -pop\n")
    have = " && ".join(f"test -f {pdk_dir}/{lib}" for lib in CORNERS.values())
    script = (f"if {have}; then LIB=1; else LIB=0; fi; "
              f"if [ $LIB = 1 ]; then yosys -s nnc_synth.ys > synth.log 2>&1; else "
              f"yosys -s nnc_generic.ys > synth.log 2>&1; fi; echo NNC_RC=$? NNC_LIB=$LIB >> synth.log; "
              "grep -E 'ERROR|Delay =|Chip area|Number of cells|NNC_RC' synth.log | head -40; "
              "for f in generic_stat.txt stat_tt.txt stat_ss.txt; do [ -f $f ] && grep -E 'cells$|Number of cells|Chip area' $f | head -3 | sed \"s/^/$f: /\"; done")
    res = host.run({**files, "nnc_abc.scr": ABC_SCRIPT, "nnc_synth.ys": "".join(ys), "nnc_generic.ys": ys[0]},
                   script, [], timeout_s=1800, tag="rtlsynth")
    text = res.output
    rep: dict = {"liberty": "NNC_LIB=1" in text, "corners": {}}
    out = []
    if "NNC_RC=0" not in text:
        err = [ln for ln in text.splitlines() if "ERROR" in ln][:3]
        out.append(_f("RR-43", "error", "synthesis failed: " + (" | ".join(err) or text[-300:])))
        return out, rep
    m = re.search(r"generic_stat\.txt:\s*(\d+)\s+cells|generic_stat\.txt:.*?Number of cells:\s*(\d+)", text)
    if m:
        rep["generic_cells"] = int(m.group(1) or m.group(2))
    delays = [float(x) for x in re.findall(r"Delay =\s*([\d.]+)\s*ps", text)]
    areas = [float(x) for x in re.findall(r"Chip area for (?:module|top module) [^:]*:\s*([\d.]+)", text)]
    if rep["liberty"]:
        # ABC prints one stime line per mapped module; with -flatten there is one per corner
        for i, c in enumerate(CORNERS):
            rep["corners"][c] = {"library": CORNERS[c], "area_um2": areas[i] if i < len(areas) else None,
                                 "comb_delay_ps": delays[i] if i < len(delays) else None}
    else:
        out.append(_f("RR-43", "info", f"no GF180 liberty files in {pdk_dir}: generic synthesis only"))
    return out, rep


def _name(x) -> str | None:
    return x.get("name") if isinstance(x, dict) else x


def clock_names(iface: dict) -> list[str]:
    """Clock ports of the contract (multi-clock list, else the single clock; a string or {name})."""
    return [n for n in (_name(c) for c in (iface.get("clocks") or [iface.get("clock")])) if n]


def reset_names(iface: dict) -> list[str]:
    return [n for n in (_name(r) for r in (iface.get("resets") or [iface.get("reset")])) if n]


def check(host: SimHost | None, files: dict[str, str], contract: dict, values: dict[str, int],
          rule_ids: set[str], pdk_dir: str = PDK_DIR, synth: bool = True) -> dict:
    """Every check; host None runs the source checks only. Returns {findings, trace, ports, synth, counts}."""
    iface, top = contract["interface"], contract["top"]
    clocks, resets = clock_names(iface), reset_names(iface)
    findings, order = filelist_findings(files, top)
    src, trace = source_findings(files, top, clocks, resets, rule_ids)
    findings += src
    ports, synth_rep = None, {}
    if host is not None and not any(f["rule"] in ("RR-01", "RR-02") and f["severity"] == "error"
                                    and "module" in f["message"] for f in findings):
        findings += lint(host, files, order, top, iface, values)
        st, ports = structure(host, files, order, top, iface, values)
        findings += st
        findings += interface_findings(ports, iface, values, files.get(f"{top}.sv", ""))
        if synth and not any(f["severity"] == "error" and f["rule"] in ("RR-13",) for f in findings):
            sf, synth_rep = synthesis(host, files, order, top, iface, values, pdk_dir)
            findings += sf
    counts = {s: sum(f["severity"] == s for f in findings) for s in ("error", "warning", "info")}
    return {"findings": findings, "trace": trace, "ports": ports, "synth": synth_rep, "counts": counts,
            "order": order}

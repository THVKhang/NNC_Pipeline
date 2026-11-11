"""DUT integration and simulation (stage 4, code only).

1. Interface conformance: the ports of the DUT top module (the only thing read from the RTL) must
   match the contract by name and direction; a mismatch stops the run (never adapt the contract).
2. A testbench top `nnc_tb_top` exposes the contract ports, instantiates the DUT and every checker
   on the same nets, so cocotb sees the DUT ports at the top level.
3. A cocotb Makefile runs Verilator with assertions and line coverage on the simulation host.
4. Evidence is parsed: results.xml (pass/fail per test, exception type), the NNC_CHECK lines printed
   by the checkers' final blocks (hits/fails per assertion), the NNC_FAIL lines (first failure time),
   and line coverage of the RTL files only.
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from nnc import coverage as coverage_mod
from nnc.contract import _param_default, derived_values, multi_clock, param_decl, width_decl
from nnc.simhost import SimHost

# Code coverage of the DUT: lines/blocks, every bit's toggles, condition terms (see nnc/coverage.py).
COVERAGE_ARGS = "--coverage-line --coverage-toggle --coverage-expr"

SIMLIB = Path(__file__).parent / "simlib" / "nnc_cocotb.py"
_PORT_DECL = re.compile(r"\b(input|output|inout)\b\s*(?:wire|logic|reg|var)?\s*(?:signed\s*)?(\[[^\]]*\]\s*)*\s*([A-Za-z_]\w*)")


# ------------------------------------------------------------------------------------- RTL ports
def checker_files(sva_dir: Path) -> list[Path]:
    """Generated checkers (nnc_chk_<group>.sv) and the functional-coverage module (nnc_cov.sv)."""
    return sorted(sva_dir.glob("nnc_chk_*.sv")) + sorted(sva_dir.glob("nnc_cov*.sv"))


def rtl_files(rtl_dir: Path) -> list[Path]:
    """Files of rtl/filelist.f in order (lines relative to rtl/), else every .sv/.v file."""
    fl = rtl_dir / "filelist.f"
    if fl.is_file():
        out = []
        for line in fl.read_text(encoding="utf-8").splitlines():
            line = line.split("//")[0].strip()
            if line and not line.startswith(("+", "-")):
                p = (rtl_dir / line).resolve() if not Path(line).is_absolute() else Path(line)
                if not p.is_file():
                    p = rtl_dir / Path(line).name
                if p.is_file():
                    out.append(p)
        if out:
            return out
    return sorted(list(rtl_dir.glob("*.sv")) + list(rtl_dir.glob("*.v")))


def _strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def dut_ports(files: list[Path], top: str) -> list[dict]:
    """ANSI port list of module `top` (names and directions only)."""
    for f in files:
        text = _strip_comments(f.read_text(encoding="utf-8", errors="replace"))
        m = re.search(rf"\bmodule\s+{re.escape(top)}\b", text)
        if not m:
            continue
        rest = text[m.end():]
        if rest.lstrip().startswith("#"):
            depth, i = 0, rest.index("#")
            j = rest.index("(", i)
            for k in range(j, len(rest)):
                depth += rest[k] == "("
                depth -= rest[k] == ")"
                if depth == 0:
                    rest = rest[k + 1:]
                    break
        start = rest.index("(")
        depth, end = 0, start
        for k in range(start, len(rest)):
            depth += rest[k] == "("
            depth -= rest[k] == ")"
            if depth == 0:
                end = k
                break
        ports, direction = [], None
        for chunk in rest[start + 1:end].split(","):
            m2 = _PORT_DECL.search(chunk)
            if m2:
                direction = m2.group(1)
                ports.append({"name": m2.group(3), "direction": direction})
            else:
                name = chunk.strip().split()[-1] if chunk.strip() else ""
                if direction and re.match(r"^[A-Za-z_]\w*$", name):
                    ports.append({"name": name, "direction": direction})
        return ports
    raise ValueError(f"module {top} not found in the RTL files")


def conformance(contract: dict, ports: list[dict]) -> list[str]:
    want = {p["name"]: p["direction"] for p in contract["interface"]["ports"]}
    have = {p["name"]: p["direction"] for p in ports}
    issues = [f"port {n} of the contract is missing in the DUT" for n in want if n not in have]
    issues += [f"port {n} of the DUT is not in the contract" for n in have if n not in want]
    issues += [f"port {n}: contract direction {want[n]}, DUT direction {have[n]}" for n in want
               if n in have and want[n] != have[n]]
    return issues


# -------------------------------------------------------------------------------------- testbench
def tb_top(contract: dict, checker_modules: list[str]) -> str:
    iface = contract["interface"]
    params = iface["parameters"]
    plist = ",\n".join(f"  {param_decl(p)}" for p in params)
    ports = ",\n".join(f"  {p['direction']:<6} logic {width_decl(p['width']):<22} {p['name']}" for p in iface["ports"])
    pmap = ", ".join(f".{p['name']}({p['name']})" for p in params if not p.get("derived"))
    conns = ",\n    ".join(f".{p['name']}({p['name']})" for p in iface["ports"])
    lines = ["// Generated by NNC: contract ports at the top, DUT and checkers on the same nets.",
             "`timescale 1ns/1ps",
             f"module nnc_tb_top" + (f" #(\n{plist}\n)" if params else "") + f" (\n{ports}\n);",
             f"  {contract['top']}" + (f" #({pmap})" if params else "") + f" u_dut (\n    {conns}\n  );"]
    for m in checker_modules:
        lines.append(f"  {m}" + (f" #({pmap})" if params else "") + f" u_{m} (\n    {conns}\n  );")
    lines.append("endmodule")
    return "\n".join(lines) + "\n"


def sim_options(config: dict) -> dict:
    """Run options of the design configuration: `defines` ("VLSIT_SYNTHESIS,X=1": Verilog macros for the
    DUT build) and `plusargs` ("+AFIFO_MSYNC_SEED={seed} +AFIFO_MSYNC_EN=1": simulator plusargs, {seed}
    becomes the run seed). Both go into the regression and the reproduction kit."""
    defines = [x.strip() for x in str(config.get("defines") or "").replace(";", ",").split(",") if x.strip()]
    return {"defines": defines, "plusargs": str(config.get("plusargs") or "").strip()}


def _define_args(opts: dict | None) -> str:
    return " ".join(f"+define+{d}" for d in (opts or {}).get("defines", []))


def _plusargs(opts: dict | None) -> str:
    return (opts or {}).get("plusargs", "").replace("{seed}", "$(SEED)")


def _opts_lines(opts: dict | None) -> str:
    out = ""
    if _define_args(opts):
        out += f"EXTRA_ARGS += {_define_args(opts)}\n"
    if _plusargs(opts):
        out += f"PLUSARGS += {_plusargs(opts)}\n"
    return out


def makefile(sources: list[str], test_module: str, params: dict[str, int], coverage: bool,
             opts: dict | None = None) -> str:
    gen = " ".join(f"-G{k}={v}" for k, v in params.items())
    return f"""# Generated by NNC. Run: make   (SEED=<n> to change the random seed)
SIM ?= verilator
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = {' '.join('$(CURDIR)/' + s for s in sources)}
COCOTB_TOPLEVEL = nnc_tb_top
COCOTB_TEST_MODULES = {test_module}
EXTRA_ARGS += --assert --timing -Wno-fatal -Wno-WIDTH -Wno-UNOPTFLAT {gen} {COVERAGE_ARGS if coverage else ''}
{_opts_lines(opts)}SEED ?= 1
NNC_JOBS ?= 8
MAKEFLAGS += -j$(NNC_JOBS)
export NNC_SEED = $(SEED)
export COCOTB_RANDOM_SEED = $(SEED)
include $(shell cocotb-config --makefiles)/Makefile.sim
"""


KIT_MAKEFILE = """# Generated by NNC Pipeline (nnc sim) from work/contract.json. Do not edit: the next run rewrites it.
# Reproduces the verification of this design WITHOUT NNC: every EDA command is in a recipe below or in
# cocotb's Makefile.sim (see it with `make -n regression`). Tools: Verilator 5 (--timing), cocotb 2,
# GNU make, Python 3. Run from this folder on Linux or inside WSL.
TOP_DIR   := $(abspath ..)
RTL       := {rtl}
SVA       := {sva}
TESTS     := {tests}
TOP       := {top}
PARAMS    := {gen}
DEFINES   := {defines}
SEED      ?= 1
TC        ?=
COVERAGE  := {coverage}
VERILATOR ?= verilator

.PHONY: help tool-check lint sva-compile regression test coverage-report clean

help:            ## list the targets and their inputs/outputs
\t@echo "Targets (inputs: ../rtl, ../verif/sva, ../verif/tests; outputs in this folder):"
\t@echo "  tool-check       versions of verilator, cocotb, python3"
\t@echo "  lint             verilator --lint-only of the DUT RTL (top $(TOP))"
\t@echo "  sva-compile      checkers + contract shell (syntax/elaboration only, never a DUT result)"
\t@echo "  regression       every test module on the DUT with the checkers -> results.xml, sim log, coverage.dat"
\t@echo "  test TC=<regex>  only the cocotb tests whose name matches, e.g. TC=test_chk_003"
\t@echo "  coverage-report  coverage.dat -> coverage.info (lcov) and annotated sources in coverage_annotated/"
\t@echo "  clean"
\t@echo "Variables: SEED=$(SEED) (random seed), PARAMS=$(PARAMS), DEFINES=$(DEFINES)"

tool-check:
\t$(VERILATOR) --version
\tcocotb-config --version
\tpython3 --version

lint:
\t$(VERILATOR) --lint-only -Wno-fatal --top-module $(TOP) $(PARAMS) $(DEFINES) $(RTL)

sva-compile:
\t$(VERILATOR) --lint-only --timing -Wno-fatal --top-module nnc_tb_top $(PARAMS) contract_shell.sv $(SVA) nnc_tb_top.sv

regression:
\t$(MAKE) -f Makefile.cocotb SEED=$(SEED) COCOTB_TEST_MODULES=$(TESTS)

test:
\t$(MAKE) -f Makefile.cocotb SEED=$(SEED) COCOTB_TEST_MODULES=$(TESTS) COCOTB_TEST_FILTER='$(TC)'

coverage-report:
\tverilator_coverage --write-info coverage.info coverage.dat
\tverilator_coverage --annotate coverage_annotated coverage.dat

clean:
\trm -rf sim_build results.xml coverage.dat coverage.info coverage_annotated __pycache__
"""

KIT_COCOTB = """# Generated by NNC Pipeline: cocotb part of the reproduction kit (called by Makefile).
TOP_DIR := $(abspath ..)
SIM ?= verilator
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = {sources}
COCOTB_TOPLEVEL = nnc_tb_top
COCOTB_TEST_MODULES ?= {tests}
EXTRA_ARGS += --assert --timing -Wno-fatal -Wno-WIDTH -Wno-UNOPTFLAT {gen} {coverage}
{opts}SEED ?= 1
export NNC_SEED = $(SEED)
export COCOTB_RANDOM_SEED = $(SEED)
export PYTHONPATH := $(CURDIR):$(TOP_DIR)/verif/tests:$(PYTHONPATH)
include $(shell cocotb-config --makefiles)/Makefile.sim
"""


def kit_files(contract: dict, rtl: list[Path], sva: list[Path], tests: list[Path], params: dict[str, int],
              clock_periods: dict | None = None, opts: dict | None = None) -> dict[str, str]:
    """Files of the design-root reproduction kit `designs/<ip>/sim/` (paths relative to the design)."""
    from nnc.contract import contract_shell
    gen = " ".join(f"-G{k}={v}" for k, v in params.items())
    rtl_s = " ".join(f"$(TOP_DIR)/rtl/{f.name}" for f in rtl)
    sva_s = " ".join(f"$(TOP_DIR)/verif/sva/{f.name}" for f in sva)
    mods = ",".join(t.stem for t in tests)
    iface = contract["interface"]
    cfg = {"clock": iface["clock"], "reset": iface["reset"], "parameters": derived_values(iface, params),
           "ports": [{"name": p["name"], "direction": p["direction"], "width": p["width"]} for p in iface["ports"]]}
    if multi_clock(iface) or clock_periods:
        cfg["clocks"] = clock_table(iface, clock_periods)
        cfg["resets"] = iface.get("resets") or []
    if iface.get("clock_relation"):
        cfg["clock_relation"] = iface["clock_relation"]
    if opts and (opts.get("defines") or opts.get("plusargs")):
        cfg["run_options"] = {"defines": list(opts.get("defines") or []), "plusargs": opts.get("plusargs") or ""}
    return {
        "sim/Makefile": KIT_MAKEFILE.format(rtl=rtl_s, sva=sva_s, tests=mods, top=contract["top"], gen=gen,
                                            coverage=COVERAGE_ARGS, defines=_define_args(opts)),
        "sim/Makefile.cocotb": KIT_COCOTB.format(sources=f"{rtl_s} {sva_s} $(CURDIR)/nnc_tb_top.sv".strip(),
                                                 tests=mods, gen=gen, coverage=COVERAGE_ARGS,
                                                 opts=_opts_lines(opts)),
        "sim/nnc_tb_top.sv": tb_top(contract, [f.stem for f in sva]),
        "sim/contract_shell.sv": contract_shell(contract["top"], iface),
        "sim/nnc_interface.json": json.dumps(cfg, indent=1) + "\n",
        "sim/nnc_cocotb.py": SIMLIB.read_text(encoding="utf-8"),
    }


def param_values(contract: dict, overrides: dict | None = None) -> dict[str, int]:
    """Values of the overridable parameters for this run (derived ones are computed by the RTL)."""
    vals = {}
    for p in contract["interface"]["parameters"]:
        if p.get("derived"):
            continue
        try:
            vals[p["name"]] = int(_param_default(p), 0)
        except ValueError:
            pass
    vals.update(overrides or {})
    return vals


def clock_table(iface: dict, periods: dict[str, float] | None = None) -> dict[str, float]:
    """Clock name -> period in ns (10 by default; a fraction such as 13.7 is allowed). Synchronous clocks
    start together; asynchronous ones (interface clock_relation "async") start with a random phase."""
    names = [c["name"] for c in iface.get("clocks") or []] or ([iface["clock"]] if iface.get("clock") else [])
    unknown = set(periods or {}) - set(names)
    if unknown:
        raise ValueError(f"clock_periods names unknown clocks {sorted(unknown)}; the clocks are {names}")
    return {n: _ns((periods or {}).get(n, 10)) for n in names}


def _ns(v) -> float:
    """A period in ns: an int when whole, else a float rounded to 1 ps."""
    f = round(float(v), 3)
    if f <= 0:
        raise ValueError(f"clock period must be positive, got {v}")
    return int(f) if f == int(f) else f


def parse_periods(text: str | None) -> dict[str, float]:
    """'i_clk_rd=13.7, i_clk_wr=10' -> {'i_clk_rd': 13.7, 'i_clk_wr': 10}."""
    out = {}
    for part in (text or "").replace(";", ",").split(","):
        if part.strip():
            name, _, val = part.partition("=")
            out[name.strip()] = _ns(val)
    return out


def build_inputs(contract: dict, rtl: list[Path], sva: list[Path], test_file: Path | list[Path], params: dict[str, int],
                 coverage: bool = True, clock_periods: dict[str, float] | None = None,
                 opts: dict | None = None) -> dict[str, object]:
    files: dict[str, object] = {}
    srcs = []
    for f in rtl:
        files[f"rtl/{f.name}"] = f
        srcs.append(f"rtl/{f.name}")
    for f in sva:
        files[f"sva/{f.name}"] = f
        srcs.append(f"sva/{f.name}")
    files["nnc_tb_top.sv"] = tb_top(contract, [f.stem for f in sva])
    srcs.append("nnc_tb_top.sv")
    tests = list(test_file) if isinstance(test_file, (list, tuple)) else [test_file]
    for t in tests:                        # the generated module, then coverage-closure modules if any
        files[t.name] = t
    files["nnc_cocotb.py"] = SIMLIB
    iface = contract["interface"]
    cfg = {"clock": iface["clock"], "reset": iface["reset"], "parameters": derived_values(iface, params),
           "ports": [{"name": p["name"], "direction": p["direction"], "width": p["width"]} for p in iface["ports"]]}
    if multi_clock(iface) or clock_periods:
        cfg["clocks"] = clock_table(iface, clock_periods)
        cfg["resets"] = iface.get("resets") or []
    if iface.get("clock_relation"):
        cfg["clock_relation"] = iface["clock_relation"]
    if opts and (opts.get("defines") or opts.get("plusargs")):
        cfg["run_options"] = {"defines": list(opts.get("defines") or []), "plusargs": opts.get("plusargs") or ""}
    files["nnc_interface.json"] = json.dumps(cfg)
    files["Makefile"] = makefile(srcs, ",".join(t.stem for t in tests), params, coverage, opts)
    return files


SIM_SCRIPT = """make SEED={seed} NNC_JOBS={jobs} > sim.log 2>&1
echo "NNC_MAKE_RC=$?" >> sim.log
if [ -f coverage.dat ]; then verilator_coverage --write-info coverage.info coverage.dat >> sim.log 2>&1; fi
"""


# ---------------------------------------------------------------------------------------- results
_EXC = re.compile(r"^\s*(?:\S+\.)?([A-Z]\w*(?:Error|Exception|Exit|Timeout\w*))\b:?\s*(.*)$")


def parse_results(out_dir: Path, rtl_names: list[str]) -> dict:
    log = (out_dir / "sim.log").read_text(encoding="utf-8", errors="replace") if (out_dir / "sim.log").is_file() else ""
    tests = []
    xml = out_dir / "results.xml"
    if xml.is_file():
        for tc in ET.parse(xml).getroot().iter("testcase"):
            fail = tc.find("failure")
            err = tc.find("error")
            bad = fail if fail is not None else err
            rec = {"name": tc.get("name"), "status": "fail" if bad is not None else
                   ("skip" if tc.find("skipped") is not None else "pass"), "sim_time_ns": tc.get("sim_time_ns")}
            if bad is not None:
                text = (bad.get("message") or "") + "\n" + (bad.text or "")
                rec["message"] = text.strip()[:2000]
            tests.append(rec)
    # Exception type and traceback per failed test, from the cocotb log.
    blocks = re.split(r"(?=\n\s*[\d.]+\w*s?\s+\w+\s+cocotb\.regression\s+running )", log)
    for t in tests:
        if t["status"] != "fail":
            continue
        blk = next((b for b in blocks if f".{t['name']} " in b or f"{t['name']} (" in b), "")
        tb = blk[blk.find("Traceback"):] if "Traceback" in blk else ""
        exc = None
        for line in reversed(tb.splitlines()):
            m = _EXC.match(line.strip())
            if m:
                exc = m.group(1)
                t["message"] = (m.group(2) or t.get("message", ""))[:2000]
                break
        t["exception"] = exc or ("AssertionError" if "AssertionError" in blk else None)
        t["traceback"] = tb[-3000:]
        t["checks"] = sorted(set(re.findall(r"CHK-\d{3}", t["name"].upper().replace("TEST_CHK_", "CHK-") + " " + t.get("message", ""))))
    checks = {}
    for m in re.finditer(r"NNC_CHECK (CHK-\d{3}) hits=(\d+) fails=(\d+)", log):
        checks[m.group(1)] = {"hits": int(m.group(2)), "fails": int(m.group(3))}
    first_fail = {}
    for m in re.finditer(r"NNC_FAIL (CHK-\d{3}) @(\d+)", log):
        first_fail.setdefault(m.group(1), int(m.group(2)))
    for cid, t in first_fail.items():
        checks.setdefault(cid, {"hits": 0, "fails": 0})["first_fail_time"] = t
    not_verifiable = {}
    for m in re.finditer(r"NNC_NOT_VERIFIABLE (CHK-\d{3}) ([^\n]*)", log):
        not_verifiable.setdefault(m.group(1), m.group(2).strip()[:300])
    cov = _line_coverage(out_dir / "coverage.info", rtl_names)
    functional = {m.group(1): int(m.group(2)) for m in re.finditer(r"NNC_COVER (COVP-\d{3}) hits=(\d+)", log)}
    if cov["status"] == "measured":
        dat = coverage_mod.parse_dat(out_dir / "coverage.dat", rtl_names)
        cov["metrics"] = {"line": {k: cov[k] for k in ("hit", "total", "percent", "files")}, **dat["metrics"]}
        cov["uncovered"] = coverage_mod.summarize_uncovered(cov.pop("uncovered_lines") + dat["uncovered"])
    else:
        cov.pop("uncovered_lines", None)
        cov.pop("executed_lines", None)
    if functional:
        hit = sum(v > 0 for v in functional.values())
        cov.setdefault("metrics", {})["functional"] = {
            "hit": hit, "total": len(functional), "percent": round(100.0 * hit / len(functional), 1),
            "files": {"nnc_cov.sv": {"hit": hit, "total": len(functional)}}}
        cov.setdefault("uncovered", []).extend(
            {"metric": "functional", "file": "nnc_cov.sv", "line": 0, "what": pid, "points": 1, "detail": []}
            for pid, n in sorted(functional.items()) if n == 0)
    rc = re.search(r"NNC_MAKE_RC=(\d+)", log)
    built = bool(tests) or "Running tests" in log
    return {"tests": tests, "assertions": checks, "not_verifiable": not_verifiable, "coverage": cov,
            "functional": functional,
            "make_rc": int(rc.group(1)) if rc else None,
            "built": built, "build_errors": [l for l in log.splitlines() if l.startswith("%Error")][:30]}


def _line_coverage(info: Path, rtl_names: list[str]) -> dict:
    if not info.is_file():
        return {"status": "not_measured"}
    hit = total = 0
    per_file: dict[str, list[int]] = {}
    missed = []
    executed: dict[str, list[int]] = {}
    current = None
    for line in info.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("SF:"):
            name = Path(line[3:]).name
            current = name if name in rtl_names else None
        elif line.startswith("DA:") and current:
            no, cnt = line[3:].split(",")[:2]
            total += 1
            hit += int(cnt) > 0
            per_file.setdefault(current, [0, 0])
            per_file[current][0] += int(cnt) > 0
            per_file[current][1] += 1
            if int(cnt) == 0:
                missed.append({"metric": "line", "file": current, "line": int(no), "what": ""})
            else:
                executed.setdefault(current, []).append(int(no))
    return {"status": "measured" if total else "no_rtl_points", "metric": "line", "hit": hit, "total": total,
            "percent": round(100.0 * hit / total, 1) if total else None,
            "files": {k: {"hit": v[0], "total": v[1]} for k, v in per_file.items()}, "uncovered_lines": missed,
            "executed_lines": {k: coverage_mod.line_ranges(v) for k, v in sorted(executed.items())}}


def run(host: SimHost, contract: dict, rtl_dir: Path, sva_dir: Path, test_file: Path | list[Path], *, seed: int = 1,
        params: dict | None = None, clock_periods: dict | None = None, opts: dict | None = None,
        timeout_s: int = 3600) -> dict:
    rtl = rtl_files(rtl_dir)
    if not rtl:
        return {"status": "error", "error": f"no RTL files in {rtl_dir}"}
    try:
        issues = conformance(contract, dut_ports(rtl, contract["top"]))
    except ValueError as e:
        issues = [str(e)]
    base = {"date": datetime.now(timezone.utc).isoformat(timespec="seconds"), "seed": seed,
            "rtl_files": [f.name for f in rtl], "integration": {"ok": not issues, "issues": issues}}
    if issues:
        return {**base, "status": "integration_failed"}
    sva = checker_files(sva_dir)
    pv = param_values(contract, params)
    files = build_inputs(contract, rtl, sva, test_file, pv, clock_periods=clock_periods, opts=opts)
    res = host.run(files, SIM_SCRIPT.format(seed=seed, jobs=8),
                   ["sim.log", "results.xml", "coverage.info", "coverage.dat"], timeout_s=timeout_s, tag="sim")
    parsed = parse_results(res.out_dir, [f.name for f in rtl])
    status = "build_failed" if not parsed["built"] else "ran"
    return {**base, "status": status, "params": pv, "host": host.name, "out_dir": str(res.out_dir), **parsed}

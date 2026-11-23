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


_DIRECTIVE = re.compile(r"`(ifdef|ifndef|elsif|else|endif|define|undef)\b[ \t]*([A-Za-z_]\w*)?")


def preprocess(text: str, defines: list[str] | None = None) -> str:
    """The text of the branches of `ifdef/`ifndef/`elsif/`else/`endif that are compiled, with the macros
    given and those the text itself `defines (names only; macro bodies are not expanded)."""
    defs = {d.split("=")[0] for d in defines or []}
    out, pos = [], 0
    stack: list[list[bool]] = []          # per level: [this branch active, a branch was taken]

    def active() -> bool:
        return all(s[0] for s in stack)

    for m in _DIRECTIVE.finditer(text):
        if active():
            out.append(text[pos:m.start()])
        kind, name = m.group(1), m.group(2) or ""
        pos = m.end()
        if kind in ("ifdef", "ifndef"):
            on = (name in defs) == (kind == "ifdef")
            stack.append([on, on])
        elif kind == "elsif" and stack:
            on = not stack[-1][1] and name in defs
            stack[-1] = [on, stack[-1][1] or on]
        elif kind == "else" and stack:
            stack[-1] = [not stack[-1][1], True]
        elif kind == "endif" and stack:
            stack.pop()
        elif kind == "define" and active():
            defs.add(name)
            eol = text.find("\n", pos)
            pos = len(text) if eol < 0 else eol      # the macro body is not RTL text
        elif kind == "undef" and active():
            defs.discard(name)
    if active():
        out.append(text[pos:])
    return "".join(out)


_BODY_DECL = re.compile(r"\b(input|output|inout)\b([^;]*);")


def _split_top_level(text: str) -> list[str]:
    """Split at commas outside (), [] and {} (a port width such as [f(a, b)-1:0] keeps its comma)."""
    out, depth, cur = [], 0, []
    for ch in text:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return out


def dut_ports(files: list[Path], top: str, defines: list[str] | None = None) -> list[dict]:
    """Port list of module `top` (names and directions only), ANSI or Verilog-1995 style, in the
    `ifdef branches compiled with `defines`."""
    for f in files:
        text = preprocess(_strip_comments(f.read_text(encoding="utf-8", errors="replace")), defines)
        m = re.search(rf"\bmodule\s+(?:(?:static|automatic)\s+)?{re.escape(top)}\b", text)
        if not m:
            continue
        rest = text[m.end():]
        # header package imports: `module m import p::*, q::x; #(...) (...)`
        while True:
            imp = re.match(r"\s*import\b[^;]*;", rest)
            if not imp:
                break
            rest = rest[imp.end():]
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
        ports, direction, bare = [], None, []
        for chunk in _split_top_level(rest[start + 1:end]):
            # `input data_t [3:0] x [2] = 0`: the name is the last identifier once the dimensions and the
            # default are removed, whatever the type (logic, a typedef, pkg::type_t, a type parameter)
            c = re.sub(r"\[[^\]]*\]", " ", chunk.split("=")[0])
            words = re.findall(r"[A-Za-z_$][\w$]*(?:::[A-Za-z_$][\w$]*)*", c)
            if not words:
                continue
            if words[0] in ("input", "output", "inout"):
                direction = words[0]
                if len(words) > 1:
                    ports.append({"name": words[-1], "direction": direction})
            elif direction:
                ports.append({"name": words[-1], "direction": direction})
            elif len(words) == 1:
                bare.append(words[0])
        if bare and not ports:
            # Verilog-1995: `module m(a, b); input a; output [3:0] b;` - directions from the body
            body = rest[end + 1:]
            stop = re.search(r"\bendmodule\b", body)
            body = body[:stop.start()] if stop else body
            dirs = {}
            for d in _BODY_DECL.finditer(body):
                decl = re.sub(r"\[[^\]]*\]", " ", d.group(2))
                for n in decl.split(","):
                    words = [w for w in n.split() if w not in ("wire", "reg", "logic", "signed", "var")]
                    if words and re.match(r"^[A-Za-z_]\w*$", words[-1].split("=")[0].strip()):
                        dirs.setdefault(words[-1].split("=")[0].strip(), d.group(1))
            ports = [{"name": n, "direction": dirs[n]} for n in bare if n in dirs]
        return ports
    raise ValueError(f"module {top} not found in the RTL files")


def conformance(contract: dict, ports: list[dict]) -> list[str]:
    want = {p["name"]: p["direction"] for p in contract["interface"]["ports"] if not p.get("virtual")}
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
    dut_conns = ",\n    ".join(f".{p['name']}({p['name']})" for p in iface["ports"] if not p.get("virtual"))
    lines = ["// Generated by NNC: contract ports at the top, DUT and checkers on the same nets.",
             "`timescale 1ns/1ps",
             f"module nnc_tb_top" + (f" #(\n{plist}\n)" if params else "") + f" (\n{ports}\n);",
             f"  {contract['top']}" + (f" #({pmap})" if params else "") + f" u_dut (\n    {dut_conns}\n  );"]
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


X_RANDOM_ARGS = "--x-assign unique --x-initial unique"
# Seed 0 would let Verilator pick a time-based seed: SEED + 1 keeps every run reproducible.
X_RANDOM_PLUSARGS = "+verilator+rand+reset+2 +verilator+seed+$(shell expr $(SEED) + 1)"


def _opts_lines(opts: dict | None) -> str:
    out = ""
    if (opts or {}).get("x_init") == "random":
        out += f"EXTRA_ARGS += {X_RANDOM_ARGS}\nPLUSARGS += {X_RANDOM_PLUSARGS}\n"
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
EXTRA_ARGS += --assert --timing -Wno-fatal -Wno-WIDTH -Wno-UNOPTFLAT +incdir+$(CURDIR)/rtl {gen} {COVERAGE_ARGS if coverage else ''}
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
\t$(VERILATOR) --lint-only -Wno-fatal --top-module $(TOP) $(PARAMS) $(DEFINES) +incdir+$(TOP_DIR)/rtl $(RTL)

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
EXTRA_ARGS += --assert --timing -Wno-fatal -Wno-WIDTH -Wno-UNOPTFLAT +incdir+$(TOP_DIR)/rtl {gen} {coverage}
{opts}SEED ?= 1
export NNC_SEED = $(SEED)
export COCOTB_RANDOM_SEED = $(SEED)
export PYTHONPATH := $(CURDIR):$(TOP_DIR)/verif/tests:$(PYTHONPATH)
include $(shell cocotb-config --makefiles)/Makefile.sim
"""


def interface_config(iface: dict, params: dict[str, int], clock_periods: dict | None = None,
                     opts: dict | None = None) -> dict:
    """nnc_interface.json of a kit: clock, reset, parameter values (with derived ones), ports, and the
    clock periods and run options of the configuration."""
    cfg = {"clock": iface["clock"], "reset": iface["reset"], "parameters": derived_values(iface, params),
           "ports": [{"name": p["name"], "direction": p["direction"], "width": p["width"]} for p in iface["ports"]]}
    if multi_clock(iface) or clock_periods:
        cfg["clocks"] = clock_table(iface, clock_periods)
        cfg["resets"] = iface.get("resets") or []
    if iface.get("clock_relation"):
        cfg["clock_relation"] = iface["clock_relation"]
    if opts and (opts.get("defines") or opts.get("plusargs")):
        cfg["run_options"] = {"defines": list(opts.get("defines") or []), "plusargs": opts.get("plusargs") or ""}
    return cfg


def kit_files(contract: dict, rtl: list[Path], sva: list[Path], tests: list[Path], params: dict[str, int],
              clock_periods: dict | None = None, opts: dict | None = None) -> dict[str, str]:
    """Files of the design-root reproduction kit `designs/<ip>/sim/` (paths relative to the design)."""
    from nnc.contract import contract_shell
    gen = " ".join(f"-G{k}={v}" for k, v in params.items())
    rtl_s = " ".join(f"$(TOP_DIR)/rtl/{f.name}" for f in rtl)
    sva_s = " ".join(f"$(TOP_DIR)/verif/sva/{f.name}" for f in sva)
    mods = ",".join(t.stem for t in tests)
    iface = contract["interface"]
    cfg = interface_config(iface, params, clock_periods, opts)
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


CONFIG_MAKEFILE = """# Generated by NNC Pipeline (nnc sim / nnc kit). Do not edit: the next run rewrites it.
# Configuration {name} of the run set{note}. Same tests, checkers and test bench as ../../ (the primary
# configuration); only the parameters, macros, plusargs and clock periods differ. Run from this folder:
#   make regression SEED=<n>        (the recorded seeds are in ../runs.tsv)
TOP_DIR   := $(abspath ../../..)
KIT_DIR   := $(abspath ../..)
TESTS     := {tests}
SEED      ?= 1

.PHONY: regression clean
regression:
\t$(MAKE) -f Makefile.cocotb SEED=$(SEED) COCOTB_TEST_MODULES=$(TESTS)

clean:
\trm -rf sim_build results.xml coverage.dat coverage.info __pycache__
"""

CONFIG_COCOTB = """# Generated by NNC Pipeline: cocotb part of configuration {name} (called by Makefile).
TOP_DIR := $(abspath ../../..)
KIT_DIR := $(abspath ../..)
SIM ?= verilator
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = {sources}
COCOTB_TOPLEVEL = nnc_tb_top
COCOTB_TEST_MODULES ?= {tests}
EXTRA_ARGS += --assert --timing -Wno-fatal -Wno-WIDTH -Wno-UNOPTFLAT +incdir+$(TOP_DIR)/rtl {gen} {coverage}
{opts}SEED ?= 1
export NNC_SEED = $(SEED)
export COCOTB_RANDOM_SEED = $(SEED)
export NNC_INTERFACE := $(CURDIR)/nnc_interface.json
export PYTHONPATH := $(KIT_DIR):$(TOP_DIR)/verif/tests:$(PYTHONPATH)
include $(shell cocotb-config --makefiles)/Makefile.sim
"""


def config_kit_files(contract: dict, rtl: list[Path], sva: list[Path], tests: list[Path],
                     runs: list[dict], primary: str) -> dict[str, str]:
    """Kit folders sim/configs/<config>/ for the configurations of a run set other than the primary one,
    and sim/configs/runs.tsv listing every recorded run (label, kit folder, seed). `runs` are the run
    entries of results.json run_set (full parameter values, options and clock periods as simulated)."""
    prim_conf = next((r["config"] for r in runs if r["label"] == primary), None)
    rtl_s = " ".join(f"$(TOP_DIR)/rtl/{f.name}" for f in rtl)
    sva_s = " ".join(f"$(TOP_DIR)/verif/sva/{f.name}" for f in sva)
    mods = ",".join(t.stem for t in tests)
    out: dict[str, str] = {}
    rows = ["# label\tkit folder (relative to sim/)\tseed"]
    for r in runs:
        folder = "." if r["config"] == prim_conf else f"configs/{r['config']}"
        rows.append(f"{r['label']}\t{folder}\t{r['seed']}")
        if folder == "." or f"sim/{folder}/Makefile" in out:
            continue
        gen = " ".join(f"-G{k}={v}" for k, v in r["params"].items())
        note = f" ({r['note']})" if r.get("note") else ""
        out[f"sim/{folder}/Makefile"] = CONFIG_MAKEFILE.format(name=r["config"], note=note, tests=mods)
        out[f"sim/{folder}/Makefile.cocotb"] = CONFIG_COCOTB.format(
            name=r["config"], sources=f"{rtl_s} {sva_s} $(KIT_DIR)/nnc_tb_top.sv", tests=mods, gen=gen,
            coverage=COVERAGE_ARGS, opts=_opts_lines(r.get("opts")))
        out[f"sim/{folder}/nnc_interface.json"] = json.dumps(
            interface_config(contract["interface"], r["params"], r.get("clock_periods"), r.get("opts")), indent=1) + "\n"
    out["sim/configs/runs.tsv"] = "\n".join(rows) + "\n"
    return out


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
                 opts: dict | None = None, frontend: str = "verilog") -> dict[str, object]:
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
    for t in tests:                        # shared test-bench libraries next to them (split mode)
        for lib in Path(t).parent.glob("tb_*.py"):
            files.setdefault(lib.name, lib)
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
    if coverage:
        files["nnc_scope.sh"] = scope_command(contract["top"], rtl, params, opts, frontend) + "\n"
    return files


SIM_SCRIPT = """make SEED={seed} NNC_JOBS={jobs} > sim.log 2>&1
echo "NNC_MAKE_RC=$?" >> sim.log
if [ -f coverage.dat ]; then verilator_coverage --write-info coverage.info coverage.dat >> sim.log 2>&1; fi
if [ -f nnc_scope.sh ]; then bash nnc_scope.sh; fi
"""

SCOPE_DIR = "nnc_scope"


def scope_command(top: str, rtl: list[Path], params: dict[str, int], opts: dict | None,
                  frontend: str = "verilog") -> str:
    """Two tool runs on the DUT alone, with the parameters and macros of the run:
    1. verilator --json-only: the elaborated tree, from which coverage.scope_from_tree reads the package
       code the design contains;
    2. yosys `proc; flatten; opt` (frontend "verilog" or "slang", as for formal): the netlist, from which
       coverage.const_from_netlist reads the signal bits that are constant.
    A failure only means no scope (nothing is left out of the coverage); it never changes a test result."""
    gen = " ".join(f"-G{k}={v}" for k, v in params.items())
    srcs = " ".join(f"rtl/{f.name}" for f in rtl)
    ydefs = " ".join(f"-D{d}" for d in (opts or {}).get("defines", []))
    if frontend == "slang":
        read = f"read_slang {ydefs} -I rtl --top {top} " + "".join(f"-G {k}={v} " for k, v in params.items()) + srcs
        hier = f"hierarchy -top {top}"
    else:
        read = f"read_verilog -sv {ydefs} -Irtl {srcs}"
        hier = f"hierarchy -top {top}" + "".join(f" -chparam {k} {v}" for k, v in params.items())
    return (f"verilator --json-only -Wno-fatal -Wno-lint -Wno-style --Mdir {SCOPE_DIR} --top-module {top} "
            f"{gen} {_define_args(opts)} +incdir+rtl {srcs} > {SCOPE_DIR}.log 2>&1 || true\n"
            f"mkdir -p {SCOPE_DIR} && yosys -q -p '{read}; {hier}; proc; flatten; opt; write_json {SCOPE_DIR}/const.json' "
            f">> {SCOPE_DIR}.log 2>&1 || rm -f {SCOPE_DIR}/const.json")


SCOPE_OUTPUTS = [f"{SCOPE_DIR}/*.tree.json", f"{SCOPE_DIR}/*.tree.meta.json", f"{SCOPE_DIR}/const.json"]


def read_scope(out_dir: Path) -> dict | None:
    """The design scope of a run from its scope output folder, or None when neither tool gave one."""
    d = out_dir / SCOPE_DIR
    if not d.is_dir():
        return None
    s: dict = {"packages": [], "kept": {}}
    trees, metas = sorted(d.glob("*.tree.json")), sorted(d.glob("*.tree.meta.json"))
    found = False
    try:
        if len(trees) == 1 and len(metas) == 1:
            s = coverage_mod.scope_from_tree(json.loads(trees[0].read_text(encoding="utf-8")),
                                             json.loads(metas[0].read_text(encoding="utf-8")))
            found = True
    except (OSError, ValueError):
        pass
    try:
        if (d / "const.json").is_file():
            c = coverage_mod.const_from_netlist(json.loads((d / "const.json").read_text(encoding="utf-8")))
            if c:
                s["const"] = c
                found = True
    except (OSError, ValueError):
        pass
    return s if found else None


# ---------------------------------------------------------------------------------------- results
_EXC = re.compile(r"^\s*(?:\S+\.)?([A-Z]\w*(?:Error|Exception|Exit|Timeout\w*))\b:?\s*(.*)$")


_FROM_DIR = object()


def parse_results(out_dir: Path, rtl_names: list[str], scope=_FROM_DIR, preverified: list[str] | None = None) -> dict:
    """Results of one run folder. `scope`: the design scope for coverage (default: read from the folder)."""
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
    functional = {m.group(1): int(m.group(2)) for m in re.finditer(r"NNC_COVER (COVP-\d{3}) hits=(\d+)", log)}
    cov = coverage_of(out_dir / "coverage.info", out_dir / "coverage.dat", rtl_names, functional,
                      read_scope(out_dir) if scope is _FROM_DIR else scope, preverified)
    rc = re.search(r"NNC_MAKE_RC=(\d+)", log)
    built = bool(tests) or "Running tests" in log
    return {"tests": tests, "assertions": checks, "not_verifiable": not_verifiable, "coverage": cov,
            "functional": functional,
            "make_rc": int(rc.group(1)) if rc else None,
            "built": built, "build_errors": [l for l in log.splitlines() if l.startswith("%Error")][:30]}


def coverage_of(info: Path, dat_path: Path, rtl_names: list[str], functional: dict[str, int],
                scope: dict | None = None, preverified: list[str] | None = None) -> dict:
    """Code coverage (lcov export + coverage.dat) and functional cover points of one run, or of a
    merged run set (verilator_coverage --write of several coverage.dat, cover hits summed). With the
    design `scope` (coverage.scope_from_tree), package code the design does not contain is left out;
    the counts over all points are kept under coverage.design_scope.all_points. `preverified`: modules
    the designer declares verified elsewhere; the coverage without their subtrees goes to
    coverage.without_preverified, next to (never instead of) the coverage of the whole design."""
    dat = coverage_mod.parse_dat(dat_path, rtl_names, scope) if scope else None
    cov = _line_coverage(info, rtl_names, (dat or {}).get("out_of_scope_lines"))
    if cov["status"] == "measured":
        if dat is None:
            dat = coverage_mod.parse_dat(dat_path, rtl_names)
        cov["metrics"] = {"line": {k: cov[k] for k in ("hit", "total", "percent", "files")}, **dat["metrics"]}
        cov["uncovered"] = coverage_mod.summarize_uncovered(cov.pop("uncovered_lines") + dat["uncovered"])
        if scope and "scope" in dat:
            raw_line = _line_coverage(info, rtl_names)
            raw = coverage_mod.parse_dat(dat_path, rtl_names)["metrics"]
            raw["line"] = {k: raw_line[k] for k in ("hit", "total", "percent")}
            left = dict(dat["scope"]["left_out"])
            left["line"] = cov.pop("left_out_lines", 0)
            cov["design_scope"] = {**dat["scope"], "left_out": dict(sorted(left.items())),
                            "all_points": {m: {k: v[k] for k in ("hit", "total", "percent")}
                                           for m, v in sorted(raw.items())}}
        cov.pop("left_out_lines", None)
        w = coverage_mod.without_modules(dat_path, rtl_names, scope, preverified or [])
        if w:
            oos = (dat or {}).get("out_of_scope_lines")
            wl = _line_coverage(info, rtl_names, oos, drop=w["drop_lines"])
            w["metrics"]["line"] = {k: wl[k] for k in ("hit", "total", "percent")}
            w["dropped"]["line"] = wl.get("dropped_lines", 0)
            cov["without_preverified"] = {"modules": sorted(preverified), "instances": w["instances"],
                                          "metrics": dict(sorted(w["metrics"].items())),
                                          "dropped": dict(sorted(w["dropped"].items()))}
    else:
        cov.pop("uncovered_lines", None)
        cov.pop("executed_lines", None)
        cov.pop("left_out_lines", None)
    if functional:
        hit = sum(v > 0 for v in functional.values())
        cov.setdefault("metrics", {})["functional"] = {
            "hit": hit, "total": len(functional), "percent": round(100.0 * hit / len(functional), 1),
            "files": {"nnc_cov.sv": {"hit": hit, "total": len(functional)}}}
        cov.setdefault("uncovered", []).extend(
            {"metric": "functional", "file": "nnc_cov.sv", "line": 0, "what": pid, "points": 1, "detail": []}
            for pid, n in sorted(functional.items()) if n == 0)
    return cov


def _line_coverage(info: Path, rtl_names: list[str], out_of_scope: set | None = None,
                   drop: set | None = None) -> dict:
    """lcov line coverage of the RTL files; lines in `out_of_scope` ((file, line) whose every block
    point is outside the design scope, never executed) are left out and counted, and so are the lines in
    `drop` (lines only of pre-verified subtrees), executed or not."""
    if not info.is_file():
        return {"status": "not_measured"}
    hit = total = left = dropped = 0
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
            if drop and (current, int(no)) in drop:
                dropped += 1
                continue
            if out_of_scope and int(cnt) == 0 and (current, int(no)) in out_of_scope:
                left += 1
                continue
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
            "executed_lines": {k: coverage_mod.line_ranges(v) for k, v in sorted(executed.items())},
            **({"left_out_lines": left} if out_of_scope is not None else {}),
            **({"dropped_lines": dropped} if drop is not None else {})}


def run(host: SimHost, contract: dict, rtl_dir: Path, sva_dir: Path, test_file: Path | list[Path], *, seed: int = 1,
        params: dict | None = None, clock_periods: dict | None = None, opts: dict | None = None,
        timeout_s: int = 3600, frontend: str = "verilog", preverified: list[str] | None = None) -> dict:
    rtl = rtl_files(rtl_dir)
    if not rtl:
        return {"status": "error", "error": f"no RTL files in {rtl_dir}"}
    try:
        issues = conformance(contract, dut_ports(rtl, contract["top"], (opts or {}).get("defines")))
    except ValueError as e:
        issues = [str(e)]
    base = {"date": datetime.now(timezone.utc).isoformat(timespec="seconds"), "seed": seed,
            "rtl_files": [f.name for f in rtl], "integration": {"ok": not issues, "issues": issues}}
    if issues:
        return {**base, "status": "integration_failed"}
    sva = checker_files(sva_dir)
    pv = param_values(contract, params)
    files = build_inputs(contract, rtl, sva, test_file, pv, clock_periods=clock_periods, opts=opts, frontend=frontend)
    res = host.run(files, SIM_SCRIPT.format(seed=seed, jobs=8),
                   ["sim.log", "results.xml", "coverage.info", "coverage.dat", *SCOPE_OUTPUTS],
                   timeout_s=timeout_s, tag="sim")
    parsed = parse_results(res.out_dir, [f.name for f in rtl], preverified=preverified)
    status = "build_failed" if not parsed["built"] else "ran"
    return {**base, "status": status, "params": pv, "host": host.name, "out_dir": str(res.out_dir), **parsed}

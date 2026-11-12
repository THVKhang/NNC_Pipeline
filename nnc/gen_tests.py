"""cocotb test generation (stage 3, agents A6 reference model + A7 test writer as one deep call).

The agent receives the contract interface, every check (tests to write, assertions to exercise) and
the quotes of their rules, never the RTL. It writes one Python module of cocotb tests built on the
helper library nnc_cocotb (clock, reset, seeding, X-safe sampling). Code validates the module
(syntax, one test per test-check, no hierarchical access into the DUT) and sends problems back.
After a simulation, `repair()` may send back infrastructure errors only (Python exceptions other
than AssertionError), so a failing functional check is never "fixed" by editing the test.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from nnc.agents.backend import AgentTask
from nnc.agents.runtime import Usage
from nnc.contract import is_async, multi_clock

PROMPT_VERSION = "tests-v2"
SYSTEM_PROMPT = (
    "You are an expert verification engineer writing cocotb 2.1 testbenches in Python. You derive every "
    "stimulus and expected value from the specification text and the plan you are given; you never assume "
    "implementation details. Your code runs unattended, so every wait is bounded. Return the answer in the "
    "required JSON structure."
)
SCHEMA = {
    "type": "object", "required": ["code"], "additionalProperties": False,
    "properties": {"code": {"type": "string", "minLength": 200}, "notes": {"type": "string"}},
}

HELPERS_DOC = '''HELPER LIBRARY (import it: `from nnc_cocotb import *`)
  CLOCK, RESET, PORTS, PARAMS           interface names; PARAMS = parameter values of this run (dict of int)
  start_clock(dut)                      start the clock; call it at the start of EVERY test
  stop_clock("<name>") / resume_clock("<name>")  stop a running clock (it holds its value) and restart it
  await reset_dut(dut, cycles=5, idle={})  drive inputs idle (0 by default), pulse reset, return mid-cycle
  await next_cycle(dut, n=1)            advance n cycles, returning at a falling edge (mid-cycle)
  val(sig) -> int | None                integer value, None if X/Z
  await wait_until(dut, cond, max_cycles, what)  poll each cycle; raises AssertionError on timeout
  rng(salt) -> random.Random            deterministic per test (salt: int or str) and run (env NNC_SEED)
  not_verifiable(dut, "CHK-nnn", reason)  declare that this run cannot verify the check (see rules)
  plusarg("NAME") -> str | None, DEFINES  simulator plusargs and Verilog defines of this run
  cocotb: `import cocotb`; `@cocotb.test()`; `cocotb.start_soon(coro)`; `dut.<port>.value = int`
'''

RULES_TEXT = """CODING RULES
- Timing model: one cycle = from one falling edge to the next. Drive inputs right after a falling edge
  (helpers return there); sample outputs at the falling edge as well (values are stable mid-cycle).
  A flip-flop output that responds "in the next cycle" is visible at the next falling edge.
- Access only top-level ports: dut.<port name>. No hierarchical access (dut.u_...), no internal signals.
- One @cocotb.test() function per test-check, named test_chk_<nnn>_<short_name>; its docstring starts with
  the check ID(s) it covers, e.g. "CHK-031: ...". A function may cover several closely related checks.
- Add one more test named test_regression_random: broad legal random traffic (all operations, random
  delays and back pressure from the models) for many transactions, so that every ASSERTION check below
  is exercised; it verifies results with the reference model / scoreboard.
- Write protocol models as reusable classes (for example a requester driver and a responder/memory
  model) and a reference model that computes expected results from the specification text only.
- Every check is an `assert <condition>, "CHK-nnn: <what was expected> got <what>"`.
- Every loop that waits on the DUT is bounded (use wait_until or a for-loop with a limit).
- Inputs that the rules call illegal are driven only in tests whose check is about that illegal input.
- Background tasks (models) are started with cocotb.start_soon inside each test; cocotb stops them at
  the end of the test.
- Use only the Python standard library, cocotb and nnc_cocotb.
- One simulation = ONE elaborated parameter configuration (PARAMS). A check that needs other
  configurations, an elaboration failure, a lint or structural inspection, or anything this run cannot
  observe must NOT pass silently: its test calls not_verifiable(dut, "CHK-nnn", "<why>") for that part
  (and still checks whatever this configuration can show). Never claim that another flow does it.
"""


MULTI_CLOCK_DOC = """SEVERAL CLOCKS: CLOCKS = {name: period_ns}; all start together when start_clock is called (synchronous
  clocks). A test does not start at a whole number of ns (cocotb advances one simulator step between
  tests): compute absolute times in integer ps from get_sim_time(unit="ps"), or count clock edges.
  start_clock(dut) starts all of them; reset_dut asserts every hardware reset together and releases each
  at a falling edge of its own clock. next_cycle(dut, n, clock="<name>"), wait_until(..., clock="<name>")
  and clk(dut, "<name>") work on the named clock (default: the first one). Drive and sample the signals
  of a domain at falling edges of that domain's clock; never assume a fixed ratio between the clocks
  beyond CLOCKS of this run. A test that needs another ratio of these synchronous clocks starts them with
  start_clock(dut, periods={"<clock>": ns, ...}) (all start at the same instant, so they stay synchronous).
"""


def _multi_clock_text(iface: dict) -> str:
    if not multi_clock(iface):
        return ""
    lines = ["CLOCK DOMAINS:"]
    for c in iface["clocks"]:
        rs = [r["name"] for r in iface["resets"] if r["clock"] == c["name"]]
        sig = [p["name"] for p in iface["ports"] if p.get("domain") == c["domain"]
               and p["name"] not in {c["name"], *rs}]
        lines.append(f"  {c['name']} ({c['domain']}): reset {', '.join(rs) or 'none'}; signals {', '.join(sig)}")
    return "\n".join(lines) + "\n" + (ASYNC_CLOCK_DOC if is_async(iface) else MULTI_CLOCK_DOC)


ASYNC_CLOCK_DOC = """SEVERAL ASYNCHRONOUS CLOCKS: CLOCKS = {name: period_ns} (a period may be a fraction such as 13.7).
  start_clock(dut) starts every clock after its own random delay below one period (seeded: it differs per
  test and per seed), so there is NO fixed phase and NO fixed ratio between the domains. Compute absolute
  times in integer ps from get_sim_time(unit="ps"), or count edges of one named clock.
  reset_dut asserts every hardware reset together and releases each at a falling edge of its own clock.
  next_cycle(dut, n, clock="<name>"), wait_until(..., clock="<name>") and clk(dut, "<name>") work on the
  named clock. Drive and sample the signals of a domain ONLY at falling edges of that domain's clock; run
  the two sides as separate coroutines (cocotb.start_soon), one per domain, that communicate through
  Python queues or counters, never by assuming which clock edge comes first.
  A cross-domain effect (data written in one domain, flag or count seen in the other) is checked as order
  plus a bounded window in edges of the destination clock: wait_until(..., max_cycles=<upper bound from
  the specification, with margin for synchronizer stages and any modelled extra latency>,
  clock="<destination>"). Never assert an exact cross-domain cycle count unless the specification gives
  one for asynchronous clocks. Exercise several ratios: the run's CLOCKS, and in some tests
  start_clock(dut, periods={...}) with the faster and the slower side swapped and a non-integer ratio.
"""


def run_config_text(run_opts: dict | None) -> str:
    """The build and simulator options of this run (Verilog defines, plusargs), so that a test knows which
    configuration it runs in instead of guessing plusarg names."""
    run_opts = run_opts or {}
    defines, plus = run_opts.get("defines") or [], (run_opts.get("plusargs") or "").strip()
    if not defines and not plus:
        return ""
    return ("RUN CONFIGURATION (this run only; the same for every test of the run):\n"
            f"  Verilog defines of the DUT build: {', '.join(defines) or 'none'}  (helper: DEFINES, a list)\n"
            f"  simulator plusargs: {plus or 'none'}  ({{seed}} is the run seed)\n"
            "  Read them with plusarg(\"NAME\") (the value as a string, None when absent) and DEFINES; use the exact\n"
            "  names above, never guess a name. A check whose expected behavior depends on these options uses the\n"
            "  values of this run; a check that needs other options calls not_verifiable for that part.\n")


def build_prompt(contract: dict, rules_doc: dict, run_opts: dict | None = None) -> str:
    iface = contract["interface"]
    rules_by_id = {r["id"]: r for r in rules_doc["rules"]}
    ports = "\n".join(f"  {p['name']} | {p['direction']} | width {p['width']} | {p['type']} | reset {p['reset_value']} | {p['meaning']}"
                      for p in iface["ports"])
    params = ", ".join(f"{p['name']} (default {p['default']}, legal {p['legal']})" for p in iface["parameters"])

    def block(c):
        quotes = "\n".join(f"      {r}: {rules_by_id[r]['quote'][:500]}" for r in c["rules"] if r in rules_by_id)
        extra = f"\n    STIMULUS: {c['stimulus']}\n    EXPECTED: {c['expected']}" if c["kind"] == "test" else ""
        return f"[{c['id']}] ({c['group']}) {c['title']}\n    BEHAVIOR: {c['behavior']}{extra}\n    SOURCES:\n{quotes}"
    tests = [block(c) for c in contract["checks"] if c["kind"] == "test"]
    asserts = [f"[{c['id']}] {c['title']}: {c['behavior']}" for c in contract["checks"] if c["kind"] == "assertion"]
    reset = iface.get("reset") or {}
    derived = [p["name"] for p in iface["parameters"] if p.get("derived")]
    if derived:
        params += (f"\n  derived (computed by the design, never set): " +
                   ", ".join(f"{p['name']} = {p['derived']}" for p in iface["parameters"] if p.get("derived")) +
                   "; PARAMS holds their values for this run")
    return (f"DUT top: {contract['top']}  clock: {iface['clock']}  reset: {reset.get('name')} "
            f"({'active low' if reset.get('active_low') else 'active high'})\n" + _multi_clock_text(iface) +
            f"PARAMETERS: {params}\n"
            f"PORTS (name | direction | width | type | reset value | meaning)\n{ports}\n\n" +
            (run_config_text(run_opts) + "\n" if run_config_text(run_opts) else "") +
            f"TEST CHECKS TO IMPLEMENT ({len(tests)})\n" + "\n".join(tests) +
            f"\n\nASSERTION CHECKS (checked by SVA during every test; your traffic must exercise them)\n" +
            "\n".join(asserts) + f"\n\nASSUMPTIONS OF THE PLAN\n" + "\n".join(f"- {a}" for a in contract.get("assumptions", [])) +
            f"\n\n{HELPERS_DOC}\n{RULES_TEXT}\nReturn the complete Python module in `code`.")


def validate(code: str, contract: dict) -> list[str]:
    problems = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"syntax error line {e.lineno}: {e.msg}"]
    tests = [n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and any(
        "cocotb.test" in ast.unparse(d) for d in n.decorator_list)]
    docs = " ".join((ast.get_docstring(t) or "") + " " + t.name for t in tests)
    for c in contract["checks"]:
        if c["kind"] == "test" and c["id"] not in docs:
            problems.append(f"no @cocotb.test() covers {c['id']} (put the ID in the docstring)")
    if not any(t.name == "test_regression_random" for t in tests):
        problems.append("missing test_regression_random")
    if re.search(r"\bdut\.u_\w+", code) or "._sub_handles" in code:
        problems.append("hierarchical access into the DUT is not allowed")
    if "nnc_cocotb" not in code:
        problems.append("use the helper library: from nnc_cocotb import *")
    return problems


def _run(prompt: str, name: str, backend, log_dir: Path, model: str, contract: dict, usage: Usage,
         rounds: int) -> tuple[str, list[str], int]:
    history = ""
    code, problems = "", []
    for attempt in range(rounds + 1):
        res = backend.run(AgentTask(f"{name}_r{attempt}", prompt + history, SCHEMA, system_prompt=SYSTEM_PROMPT,
                                    model=model, max_turns=4), log_dir)
        usage.add(res)
        code = res.output["code"]
        problems = validate(code, contract)
        if not problems:
            return code, [], attempt + 1
        history = ("\n\nYOUR PREVIOUS MODULE FAILED VALIDATION:\n" + "\n".join(problems) +
                   f"\n```python\n{code}\n```\nReturn the corrected complete module.")
    return code, problems, rounds + 1


def generate(contract: dict, rules_doc: dict, backend, log_dir: Path, out_file: Path, *, model: str = "opus",
             rounds: int = 2, run_opts: dict | None = None) -> dict:
    usage = Usage()
    code, problems, attempts = _run(build_prompt(contract, rules_doc, run_opts), "A7_tests", backend, log_dir, model,
                                    contract, usage, rounds)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(code, encoding="utf-8")
    return {"file": out_file.name, "status": "valid" if not problems else "invalid", "problems": problems,
            "attempts": attempts, "usage": usage.as_dict(), "prompt_version": PROMPT_VERSION}


def test_check_map(code: str) -> dict[str, list[str]]:
    """Test function name -> check IDs in its name and docstring."""
    out = {}
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return out
    for n in ast.walk(tree):
        if isinstance(n, ast.AsyncFunctionDef) and any("cocotb.test" in ast.unparse(d) for d in n.decorator_list):
            text = (ast.get_docstring(n) or "") + " " + n.name.upper().replace("TEST_CHK_", "CHK-")
            out[n.name] = sorted(set(re.findall(r"CHK-\d{3}", text)))
    return out


def infrastructure_errors(results: dict) -> list[str]:
    """Failures caused by the test code itself (not by a failed check): Python exceptions other than
    AssertionError, and failures without any CHK reference."""
    return [f"{t['name']}: {t.get('exception')}: {t.get('message', '')[:300]}\n{t.get('traceback', '')[-1500:]}"
            for t in results.get("tests", [])
            if t["status"] == "fail" and t.get("exception") and t["exception"] != "AssertionError"
            and not _in_library(t)]


def _in_library(t: dict) -> bool:
    """True when the exception was raised inside nnc_cocotb (a fault of the flow, not of the test)."""
    frames = re.findall(r'File "([^"]+)"', t.get("traceback", ""))
    return bool(frames) and frames[-1].endswith("nnc_cocotb.py")


def library_errors(results: dict) -> list[str]:
    return [f"{t['name']}: {t.get('exception')}: {t.get('message', '')[:300]}" for t in results.get("tests", [])
            if t["status"] == "fail" and t.get("exception") and _in_library(t)]


def repair(contract: dict, rules_doc: dict, backend, log_dir: Path, out_file: Path, errors: list[str], *,
           model: str = "opus", round_no: int = 1, run_opts: dict | None = None) -> dict:
    """Fix test-infrastructure errors (exceptions in the test code). Functional failures are never sent."""
    usage = Usage()
    current = out_file.read_text(encoding="utf-8")
    prompt = (build_prompt(contract, rules_doc, run_opts) + "\n\nTHE MODULE BELOW RAISED PYTHON ERRORS IN SIMULATION "
              "(errors of the test code itself, not failed checks). Fix the test code only; do not weaken any "
              "check or change any expected value.\n```python\n" + current + "\n```\nERRORS:\n" + "\n\n".join(errors[:8]))
    code, problems, attempts = _run(prompt, f"A7_tests_repair{round_no}", backend, log_dir, model, contract, usage, 1)
    if not problems:
        out_file.write_text(code, encoding="utf-8")
    return {"status": "repaired" if not problems else "invalid", "problems": problems, "attempts": attempts,
            "usage": usage.as_dict()}


# ------------------------------------------------------------------------------------------- split mode
# One deep call writing a 1500-line module is expensive to lose (a usage limit or a timeout after 20 minutes
# costs the whole answer) and expensive to repair. In split mode (config tests_mode=split) one call writes
# the shared test-bench library tb_<ip>.py (models, drivers, reference model, scoreboard), then one call
# per group of at most GROUP_SIZE test checks writes test_<ip>_g<n>.py on top of it, in parallel. A lost
# or invalid group costs one small call; a repair touches one group (or the library).
GROUP_SIZE = 5

LIB_RULES = """LIBRARY TASK
- Write ONLY the shared test-bench library module `{lib}` for the tests below. NO @cocotb.test() function.
- It contains everything the tests need: protocol drivers and responder models as classes, monitors, the
  reference model / scoreboard computed from the specification text only, reset/initialisation helpers,
  and helper coroutines that run common sequences (for example "write N words", "full transfer").
- Its module docstring is the API: one line per public class/function with its signature and meaning, so
  that test writers who see only this module can use it correctly.
- It starts with `from nnc_cocotb import *` (and may import cocotb, random, the standard library).
- Every wait is bounded; every check helper raises `AssertionError("CHK-nnn: ...")` with the check ID.
"""

GROUP_RULES = """TEST TASK
- Write the test module for the TEST CHECKS listed above only, on top of the library below (already
  written and fixed: do not copy or redefine its classes; import it with `from {mod} import *`).
- One @cocotb.test() per check (a function may cover several closely related checks), named
  test_chk_<nnn>_<short_name>, docstring starting with the check ID(s).{regression}
- Small local helpers are allowed. Same coding rules as below.
"""


def group_rules(regression: bool) -> str:
    """RULES_TEXT for one group module: the regression test is asked only of the first module."""
    if regression:
        return RULES_TEXT
    a = RULES_TEXT.index("- Add one more test named test_regression_random")
    b = RULES_TEXT.index("- Write protocol models")
    return RULES_TEXT[:a] + RULES_TEXT[b:]


def _check_block(c: dict, rules_by_id: dict) -> str:
    quotes = "\n".join(f"      {r}: {rules_by_id[r]['quote'][:500]}" for r in c["rules"] if r in rules_by_id)
    extra = f"\n    STIMULUS: {c['stimulus']}\n    EXPECTED: {c['expected']}" if c["kind"] == "test" else ""
    return f"[{c['id']}] ({c['group']}) {c['title']}\n    BEHAVIOR: {c['behavior']}{extra}\n    SOURCES:\n{quotes}"


def groups(contract: dict, size: int = GROUP_SIZE) -> list[list[dict]]:
    """Test checks in chunks of at most `size`, keeping the contract groups together where possible."""
    tests = [c for c in contract["checks"] if c["kind"] == "test"]
    tests.sort(key=lambda c: (c["group"], c["id"]))
    out: list[list[dict]] = []
    for c in tests:
        if not out or len(out[-1]) >= size or (out[-1][-1]["group"] != c["group"] and len(out[-1]) >= size - 1):
            out.append([])
        out[-1].append(c)
    return out


def validate_library(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"syntax error line {e.lineno}: {e.msg}"]
    problems = []
    if any(isinstance(n, ast.AsyncFunctionDef) and any("cocotb.test" in ast.unparse(d) for d in n.decorator_list)
           for n in ast.walk(tree)):
        problems.append("the library must not contain @cocotb.test() functions")
    if not ast.get_docstring(tree):
        problems.append("the module docstring (the API of the library) is missing")
    if "nnc_cocotb" not in code:
        problems.append("use the helper library: from nnc_cocotb import *")
    if re.search(r"\bdut\.u_\w+", code) or "._sub_handles" in code:
        problems.append("hierarchical access into the DUT is not allowed")
    return problems


def validate_group(code: str, checks: list[dict], lib_module: str, regression: bool) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"syntax error line {e.lineno}: {e.msg}"]
    tests = [n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and any(
        "cocotb.test" in ast.unparse(d) for d in n.decorator_list)]
    docs = " ".join((ast.get_docstring(t) or "") + " " + t.name for t in tests)
    problems = [f"no @cocotb.test() covers {c['id']} (put the ID in the docstring)" for c in checks if c["id"] not in docs]
    if regression and not any(t.name == "test_regression_random" for t in tests):
        problems.append("missing test_regression_random")
    if not regression and any(t.name == "test_regression_random" for t in tests):
        problems.append("test_regression_random belongs to another module")
    if f"from {lib_module} import" not in code:
        problems.append(f"import the library: from {lib_module} import *")
    if re.search(r"\bdut\.u_\w+", code) or "._sub_handles" in code:
        problems.append("hierarchical access into the DUT is not allowed")
    return problems


def _run_checked(prompt: str, name: str, backend, log_dir: Path, model: str, usage: Usage, rounds: int,
                 check) -> tuple[str, list[str], int]:
    history, code, problems = "", "", []
    for attempt in range(rounds + 1):
        res = backend.run(AgentTask(f"{name}_r{attempt}", prompt + history, SCHEMA, system_prompt=SYSTEM_PROMPT,
                                    model=model, max_turns=4), log_dir)
        usage.add(res)
        code = res.output["code"]
        problems = check(code)
        if not problems:
            return code, [], attempt + 1
        history = ("\n\nYOUR PREVIOUS MODULE FAILED VALIDATION:\n" + "\n".join(problems) +
                   f"\n```python\n{code}\n```\nReturn the corrected complete module.")
    return code, problems, rounds + 1


def _context(contract: dict, run_opts: dict | None) -> str:
    """Interface part of the prompt (no checks)."""
    full = build_prompt({**contract, "checks": []}, {"rules": []}, run_opts)
    return full.split("TEST CHECKS TO IMPLEMENT")[0]


def generate_split(contract: dict, rules_doc: dict, backend, log_dir: Path, tests_dir: Path, design: str, *,
                   model: str = "opus", rounds: int = 2, run_opts: dict | None = None, workers: int = 4) -> dict:
    """Library call, then one call per group of test checks (in parallel)."""
    from concurrent.futures import ThreadPoolExecutor
    lib_mod = f"tb_{design}"
    usage = Usage()
    lib_prompt = (build_prompt(contract, rules_doc, run_opts).replace(
        "Return the complete Python module in `code`.", "") + "\n" + LIB_RULES.format(lib=lib_mod) +
        f"\nReturn the complete library module `{lib_mod}.py` in `code`.")
    lib, lib_problems, lib_attempts = _run_checked(lib_prompt, "A7_tests_lib", backend, log_dir, model, usage, rounds,
                                                   validate_library)
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / f"{lib_mod}.py").write_text(lib, encoding="utf-8")
    report = {"mode": "split", "library": {"file": f"{lib_mod}.py", "status": "valid" if not lib_problems else "invalid",
                                           "problems": lib_problems, "attempts": lib_attempts}, "groups": []}
    if lib_problems:
        report.update({"status": "invalid", "problems": lib_problems, "usage": usage.as_dict(),
                       "prompt_version": PROMPT_VERSION})
        return report
    rules_by_id = {r["id"]: r for r in rules_doc["rules"]}
    asserts = "\n".join(f"[{c['id']}] {c['title']}" for c in contract["checks"] if c["kind"] == "assertion")
    ctx = _context(contract, run_opts)
    gs = groups(contract)
    for old in tests_dir.glob(f"test_{design}_g*.py"):
        old.unlink()

    def one(i: int, checks: list[dict]) -> dict:
        regression = i == 0
        name = f"test_{design}_g{i + 1}"
        prompt = (ctx + f"TEST CHECKS OF THIS MODULE ({len(checks)})\n" +
                  "\n".join(_check_block(c, rules_by_id) for c in checks) +
                  f"\n\nASSERTION CHECKS (SVA, checked during every test)\n{asserts}\n\n" +
                  GROUP_RULES.format(mod=lib_mod, regression=(
                      "\n- Also write test_regression_random: broad legal random traffic for many transactions that "
                      "exercises every assertion check, verified with the library's reference model."
                      if regression else "")) +
                  f"\nLIBRARY `{lib_mod}.py`\n```python\n{lib}\n```\n\n{HELPERS_DOC}\n{group_rules(regression)}\n"
                  f"Return the complete test module `{name}.py` in `code`.")
        u = Usage()
        code, probs, att = _run_checked(prompt, f"A7_tests_g{i + 1}", backend, log_dir, model, u, rounds,
                                        lambda c: validate_group(c, checks, lib_mod, regression))
        (tests_dir / f"{name}.py").write_text(code, encoding="utf-8")
        return {"file": f"{name}.py", "checks": [c["id"] for c in checks], "status": "valid" if not probs else "invalid",
                "problems": probs, "attempts": att, "usage": u}

    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        results = list(ex.map(lambda a: one(*a), enumerate(gs)))
    for r in results:
        usage.merge(r.pop("usage"))
        report["groups"].append(r)
    bad = [p for r in report["groups"] for p in r["problems"]]
    report.update({"status": "valid" if not bad else "invalid", "problems": bad, "usage": usage.as_dict(),
                   "prompt_version": PROMPT_VERSION, "file": f"{lib_mod}.py + {len(gs)} test modules"})
    return report


def repair_split(contract: dict, rules_doc: dict, backend, log_dir: Path, tests_dir: Path, design: str,
                 errors: list[tuple[str, str]], *, model: str = "opus", round_no: int = 1,
                 run_opts: dict | None = None) -> dict:
    """Repair infrastructure errors in split mode. errors: (module file name, error text); the library is
    repaired when the failing frame is in it. Functional failures are never sent."""
    lib_mod = f"tb_{design}"
    lib_path = tests_dir / f"{lib_mod}.py"
    by_file: dict[str, list[str]] = {}
    for f, e in errors:
        by_file.setdefault(f, []).append(e)
    usage, out = Usage(), {}
    for f, errs in sorted(by_file.items()):
        path = tests_dir / f
        is_lib = f == lib_path.name
        if is_lib:
            check = validate_library
        else:
            cur = path.read_text(encoding="utf-8")
            ids = {i for v in test_check_map(cur).values() for i in v}
            mine = [x for x in contract["checks"] if x["kind"] == "test" and x["id"] in ids]
            reg = "test_regression_random" in cur
            check = (lambda c, _m=mine, _r=reg: validate_group(c, _m, lib_mod, _r))
        ctx = (_context(contract, run_opts) + ("" if is_lib else
               f"LIBRARY `{lib_mod}.py` (fixed)\n```python\n{lib_path.read_text(encoding='utf-8')}\n```\n"))
        prompt = (ctx + f"\nTHE MODULE `{f}` BELOW RAISED PYTHON ERRORS IN SIMULATION (errors of the test code itself, "
                  "not failed checks). Fix the code only; do not weaken any check or change any expected value; keep "
                  "every function name.\n```python\n" + path.read_text(encoding="utf-8") + "\n```\nERRORS:\n" +
                  "\n\n".join(errs[:8]) + f"\n\n{HELPERS_DOC}\n{RULES_TEXT}\nReturn the complete module in `code`.")
        code, probs, att = _run_checked(prompt, f"A7_tests_repair{round_no}_{Path(f).stem}", backend, log_dir, model,
                                        usage, 1, check)
        if not probs:
            path.write_text(code, encoding="utf-8")
        out[f] = {"status": "repaired" if not probs else "invalid", "problems": probs, "attempts": att}
    return {"status": "repaired" if all(v["status"] == "repaired" for v in out.values()) else "invalid",
            "modules": out, "usage": usage.as_dict()}


def error_module(t: dict, test_modules: dict[str, str], lib_name: str) -> str:
    """Module to repair for a failed test: the library when the deepest frame is in it, else the test's own."""
    frames = [Path(f).name for f in re.findall(r'File "([^"]+)"', t.get("traceback", ""))]
    if frames and frames[-1] == lib_name:
        return lib_name
    return test_modules.get(t["name"].split("/")[0], next(iter(test_modules.values()), lib_name))

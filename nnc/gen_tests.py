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

PROMPT_VERSION = "tests-v1"
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
  await reset_dut(dut, cycles=5, idle={})  drive inputs idle (0 by default), pulse reset, return mid-cycle
  await next_cycle(dut, n=1)            advance n cycles, returning at a falling edge (mid-cycle)
  val(sig) -> int | None                integer value, None if X/Z
  await wait_until(dut, cond, max_cycles, what)  poll each cycle; raises AssertionError on timeout
  rng(salt) -> random.Random            deterministic per test (salt: int or str) and run (env NNC_SEED)
  not_verifiable(dut, "CHK-nnn", reason)  declare that this run cannot verify the check (see rules)
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


def build_prompt(contract: dict, rules_doc: dict) -> str:
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
    return (f"DUT top: {contract['top']}  clock: {iface['clock']}  reset: {reset.get('name')} "
            f"({'active low' if reset.get('active_low') else 'active high'})\nPARAMETERS: {params}\n"
            f"PORTS (name | direction | width | type | reset value | meaning)\n{ports}\n\n"
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
             rounds: int = 2) -> dict:
    usage = Usage()
    code, problems, attempts = _run(build_prompt(contract, rules_doc), "A7_tests", backend, log_dir, model,
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
           model: str = "opus", round_no: int = 1) -> dict:
    """Fix test-infrastructure errors (exceptions in the test code). Functional failures are never sent."""
    usage = Usage()
    current = out_file.read_text(encoding="utf-8")
    prompt = (build_prompt(contract, rules_doc) + "\n\nTHE MODULE BELOW RAISED PYTHON ERRORS IN SIMULATION "
              "(errors of the test code itself, not failed checks). Fix the test code only; do not weaken any "
              "check or change any expected value.\n```python\n" + current + "\n```\nERRORS:\n" + "\n\n".join(errors[:8]))
    code, problems, attempts = _run(prompt, f"A7_tests_repair{round_no}", backend, log_dir, model, contract, usage, 1)
    if not problems:
        out_file.write_text(code, encoding="utf-8")
    return {"status": "repaired" if not problems else "invalid", "problems": problems, "attempts": attempts,
            "usage": usage.as_dict()}

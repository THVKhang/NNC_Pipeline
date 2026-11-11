"""Helpers for generated cocotb tests (copied next to the tests at simulation time).

The interface comes from nnc_interface.json, written by the flow from the verification contract:
clock, reset, port list and the parameter values of this run. Tests use these helpers so that clock,
reset, seeding and X-safe sampling are the same in every generated test.
"""
import json
import os
import random
import zlib
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge, Timer

_CFG = json.loads((Path(__file__).with_name("nnc_interface.json")).read_text(encoding="utf-8"))
CLOCK = _CFG["clock"]
RESET = _CFG["reset"]                       # {"name": ..., "active_low": bool} or None
PORTS = _CFG["ports"]                       # [{"name", "direction", "width"}]
PARAMS = {k: int(v) for k, v in _CFG["parameters"].items()}
CLOCK_PERIOD_NS = 10
FLUSH_CYCLES = 2   # edges allowed before a reset so that pending assertions of the previous test complete
# Several clocks (synchronous, all started at time 0) and several hardware resets, each tied to the
# clock of its domain. A single-clock design has CLOCKS = {CLOCK: 10} and RESETS = [RESET + clock].
def _num(v):
    """A period in ns: an int when whole (as before), else a float (for example 13.7)."""
    f = float(v)
    return int(f) if f == int(f) else f


CLOCKS = {k: _num(v) for k, v in (_CFG.get("clocks") or {CLOCK: CLOCK_PERIOD_NS}).items()}
RESETS = _CFG.get("resets") or ([{**RESET, "clock": CLOCK}] if RESET else [])
_NOT_DATA = set(CLOCKS) | {r["name"] for r in RESETS} | ({RESET["name"]} if RESET else set())
# "sync": every clock starts at the same instant (fixed phase). "async": every clock starts after its own
# random delay below one period (seeded), so the phase between the domains differs from test to test
# and from seed to seed; nothing may assume an edge of one clock coincides with an edge of another.
CLOCK_RELATION = _CFG.get("clock_relation", "sync")
PHASES_PS: dict = {}     # start delay of each clock in the current test (async only), for the log
# Build and simulator options of this run (nnc config: defines, plusargs).
DEFINES = list((_CFG.get("run_options") or {}).get("defines") or [])


def plusarg(name: str, default=None):
    """Value of the simulator plusarg +NAME=value of this run as a string ("" for a bare +NAME), else default."""
    args = getattr(cocotb, "plusargs", None) or {}
    if name in args:
        v = args[name]
        return "" if v is True else str(v)
    return default


def seed() -> int:
    return int(os.environ.get("NNC_SEED", "1"))


def rng(salt=0) -> random.Random:
    """Deterministic random generator per test (salt: int or str) and run seed (NNC_SEED)."""
    if not isinstance(salt, int):
        salt = zlib.crc32(str(salt).encode("utf-8"))   # stable across runs, unlike hash()
    return random.Random(seed() * 1_000_003 + salt)


def clk(dut, clock: str | None = None):
    """The clock signal (the first clock, or the named one)."""
    return getattr(dut, clock or CLOCK)


_ACTIVE = dict(CLOCKS)   # periods of the clocks started by the current test


_STARTS = 0              # start_clock calls in this simulation (one per test): varies the async phases


def _period_ps(ns) -> int:
    """Period in integer ps, even so that both half periods are whole ps."""
    ps = max(2, int(round(float(ns) * 1000)))
    return ps + (ps & 1)


_CLOCK_OBJS: dict = {}   # name -> cocotb Clock of the current test (for stop_clock / resume_clock)


async def _start_after(name: str, sig, period_ps: int, delay_ps: int):
    await Timer(delay_ps, unit="ps")
    _CLOCK_OBJS[name] = Clock(sig, period_ps, unit="ps")
    _CLOCK_OBJS[name].start()


def stop_clock(name: str | None = None):
    """Stop driving a clock (the first one by default); it keeps its last value. resume_clock restarts it."""
    c = _CLOCK_OBJS.get(name or CLOCK)
    if c is None:
        raise RuntimeError(f"clock {name or CLOCK} is not running (call start_clock first)")
    c.stop()


def resume_clock(name: str | None = None):
    """Restart a clock stopped by stop_clock, with the same period."""
    c = _CLOCK_OBJS.get(name or CLOCK)
    if c is None:
        raise RuntimeError(f"clock {name or CLOCK} was never started")
    c.start()


def start_clock(dut, period_ns: float | None = None, periods: dict | None = None):
    """Start the clock(s). cocotb ends every task of a test when the test ends: call this in each test.
    Synchronous clocks all start at the same instant; asynchronous clocks (CLOCK_RELATION "async") each
    start after a random delay below one period, so their phase differs per test and per seed. `periods`
    ({name: ns}) sets other periods for this test only (default: the periods of the run configuration).
    Returns None: in cocotb 2 Clock.start() gives a Task that never ends, and a test that awaited it
    (e.g. `if inspect.isawaitable(res): await res`) would wait forever while the clock runs."""
    global _ACTIVE, _STARTS
    _STARTS += 1
    if len(CLOCKS) == 1 and not periods:
        _ACTIVE = {CLOCK: period_ns or CLOCKS[CLOCK]}
        _CLOCK_OBJS[CLOCK] = Clock(clk(dut), _period_ps(_ACTIVE[CLOCK]), unit="ps")
        _CLOCK_OBJS[CLOCK].start()
        return None
    _ACTIVE = {**CLOCKS, **{k: _num(v) for k, v in (periods or {}).items()}}
    unknown = set(_ACTIVE) - set(CLOCKS)
    if unknown:
        raise ValueError(f"unknown clocks {sorted(unknown)}; the clocks are {sorted(CLOCKS)}")
    PHASES_PS.clear()
    _CLOCK_OBJS.clear()
    for name, per in _ACTIVE.items():
        sig, pps = getattr(dut, name), _period_ps(per)
        delay = rng(f"clock-phase:{name}:{_STARTS}").randrange(0, pps) if CLOCK_RELATION == "async" else 0
        if delay:
            PHASES_PS[name] = delay
            sig.value = 0
            cocotb.start_soon(_start_after(name, sig, pps, delay))
        else:
            _CLOCK_OBJS[name] = Clock(sig, pps, unit="ps")
            _CLOCK_OBJS[name].start()
    if PHASES_PS:
        dut._log.info("NNC async clock start delays (ps): %s", PHASES_PS)
    return None


async def reset_dut(dut, cycles: int = 5, idle: dict | None = None):
    """Drive every input (except clocks and resets) to its idle value (default 0), assert every
    hardware reset together for `cycles` cycles of the slowest clock, release each at a falling edge of
    its own clock, and return at the next falling edge of the first clock.

    It first lets FLUSH_CYCLES clock edges pass with the inputs left by the previous test: a test that
    stopped at its first failed check may leave an SVA property waiting for its consequent (|=>), and
    asserting reset at once would cancel it (disable iff) and hide the failure from the checkers."""
    idle = idle or {}
    slow = max(_ACTIVE, key=lambda n: _ACTIVE[n])
    await ClockCycles(clk(dut, slow), FLUSH_CYCLES)
    for p in PORTS:
        if p["direction"] == "input" and p["name"] not in _NOT_DATA:
            getattr(dut, p["name"]).value = idle.get(p["name"], 0)
    if RESETS:
        for r in RESETS:
            getattr(dut, r["name"]).value = 0 if r["active_low"] else 1
        await ClockCycles(clk(dut, slow), cycles)
        for r in RESETS:
            await FallingEdge(clk(dut, r.get("clock")))
            getattr(dut, r["name"]).value = 1 if r["active_low"] else 0
    await FallingEdge(clk(dut))


async def next_cycle(dut, n: int = 1, clock: str | None = None):
    """Advance n cycles of the first (or the named) clock; returns at a falling edge (middle of a
    cycle: safe to drive and to sample)."""
    for _ in range(n):
        await FallingEdge(clk(dut, clock))


def val(sig) -> int | None:
    """Integer value of a signal, or None when it holds X or Z."""
    v = sig.value
    return int(v) if v.is_resolvable else None


def not_verifiable(dut, check_id: str, reason: str) -> None:
    """Declare that this run cannot verify check_id (for example a parameter sweep or an elaboration
    error needs other builds). The report then shows NOT_VERIFIABLE instead of PASS: a test must call
    this rather than pass without checking anything."""
    dut._log.warning(f"NNC_NOT_VERIFIABLE {check_id} {reason}")


async def wait_until(dut, cond, max_cycles: int, what: str, clock: str | None = None) -> int:
    """Advance cycle by cycle (falling edges of the first or the named clock) until cond() is true;
    fail after max_cycles. Returns the number of cycles waited."""
    for n in range(max_cycles + 1):
        if cond():
            return n
        await FallingEdge(clk(dut, clock))
    raise AssertionError(f"timeout after {max_cycles} cycles waiting for {what}")


__all__ = ["CLOCK", "RESET", "CLOCKS", "RESETS", "PORTS", "PARAMS", "seed", "rng", "clk", "start_clock",
           "reset_dut", "next_cycle", "val", "wait_until", "not_verifiable", "RisingEdge", "FallingEdge",
           "ClockCycles", "CLOCK_RELATION", "PHASES_PS", "stop_clock", "resume_clock", "DEFINES", "plusarg"]

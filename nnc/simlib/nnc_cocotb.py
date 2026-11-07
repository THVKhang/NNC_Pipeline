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

from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge

_CFG = json.loads((Path(__file__).with_name("nnc_interface.json")).read_text(encoding="utf-8"))
CLOCK = _CFG["clock"]
RESET = _CFG["reset"]                       # {"name": ..., "active_low": bool} or None
PORTS = _CFG["ports"]                       # [{"name", "direction", "width"}]
PARAMS = {k: int(v) for k, v in _CFG["parameters"].items()}
CLOCK_PERIOD_NS = 10
FLUSH_CYCLES = 2   # edges allowed before a reset so that pending assertions of the previous test complete


def seed() -> int:
    return int(os.environ.get("NNC_SEED", "1"))


def rng(salt=0) -> random.Random:
    """Deterministic random generator per test (salt: int or str) and run seed (NNC_SEED)."""
    if not isinstance(salt, int):
        salt = zlib.crc32(str(salt).encode("utf-8"))   # stable across runs, unlike hash()
    return random.Random(seed() * 1_000_003 + salt)


def clk(dut):
    return getattr(dut, CLOCK)


def start_clock(dut, period_ns: int = CLOCK_PERIOD_NS):
    """Start the clock. cocotb ends every task of a test when the test ends: call this in each test."""
    return Clock(clk(dut), period_ns, unit="ns").start()


async def reset_dut(dut, cycles: int = 5, idle: dict | None = None):
    """Drive every input (except clock and reset) to its idle value (default 0), assert the reset for
    `cycles` cycles, release it at a falling edge, and return at the next falling edge.

    It first lets FLUSH_CYCLES clock edges pass with the inputs left by the previous test: a test that
    stopped at its first failed check may leave an SVA property waiting for its consequent (|=>), and
    asserting reset at once would cancel it (disable iff) and hide the failure from the checkers."""
    idle = idle or {}
    await ClockCycles(clk(dut), FLUSH_CYCLES)
    for p in PORTS:
        if p["direction"] == "input" and p["name"] not in (CLOCK, RESET and RESET["name"]):
            getattr(dut, p["name"]).value = idle.get(p["name"], 0)
    if RESET:
        r = getattr(dut, RESET["name"])
        r.value = 0 if RESET["active_low"] else 1
        await ClockCycles(clk(dut), cycles)
        await FallingEdge(clk(dut))
        r.value = 1 if RESET["active_low"] else 0
    await FallingEdge(clk(dut))


async def next_cycle(dut, n: int = 1):
    """Advance n cycles; returns at a falling edge (middle of a cycle: safe to drive and to sample)."""
    for _ in range(n):
        await FallingEdge(clk(dut))


def val(sig) -> int | None:
    """Integer value of a signal, or None when it holds X or Z."""
    v = sig.value
    return int(v) if v.is_resolvable else None


def not_verifiable(dut, check_id: str, reason: str) -> None:
    """Declare that this run cannot verify check_id (for example a parameter sweep or an elaboration
    error needs other builds). The report then shows NOT_VERIFIABLE instead of PASS: a test must call
    this rather than pass without checking anything."""
    dut._log.warning(f"NNC_NOT_VERIFIABLE {check_id} {reason}")


async def wait_until(dut, cond, max_cycles: int, what: str) -> int:
    """Advance cycle by cycle (falling edges) until cond() is true; fail after max_cycles. Returns the
    number of cycles waited."""
    for n in range(max_cycles + 1):
        if cond():
            return n
        await FallingEdge(clk(dut))
    raise AssertionError(f"timeout after {max_cycles} cycles waiting for {what}")


__all__ = ["CLOCK", "RESET", "PORTS", "PARAMS", "seed", "rng", "clk", "start_clock", "reset_dut", "next_cycle",
           "val", "wait_until", "not_verifiable", "RisingEdge", "FallingEdge", "ClockCycles"]

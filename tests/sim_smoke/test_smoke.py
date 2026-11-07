"""Smoke test of cocotb + Verilator + SVA: a legal handshake passes, illegal ones are caught."""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

COUNTERS = ("fails_valid_hold", "hits_valid_hold", "fails_data_stable", "hits_data_stable")


def counts(dut) -> dict:
    return {n: int(getattr(dut.u_chk, n).value) for n in COUNTERS}


def delta(after: dict, before: dict) -> dict:
    return {k: after[k] - before[k] for k in after}


async def start(dut):
    # cocotb cancels every task a test started when that test ends, the clock included,
    # so each test starts its own clock.
    Clock(dut.clk, 10, unit="ns").start()
    dut.rst_n.value = 0
    dut.valid.value = 0
    dut.ready.value = 0
    dut.data.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def drive(dut, cycles):
    """Apply (valid, ready, data) per cycle, then idle for two cycles."""
    for valid, ready, data in cycles:
        dut.valid.value, dut.ready.value, dut.data.value = valid, ready, data
        await RisingEdge(dut.clk)
    dut.valid.value, dut.ready.value = 0, 0
    await ClockCycles(dut.clk, 2)


@cocotb.test()
async def legal_handshake(dut):
    """VALID held with stable data for 3 wait cycles, then READY: no failure, both covers hit."""
    await start(dut)
    before = counts(dut)
    await drive(dut, [(1, 0, 0x5A)] * 3 + [(1, 1, 0x5A)])
    d = delta(counts(dut), before)
    dut._log.info("legal: %s", d)
    assert d["fails_valid_hold"] == 0 and d["fails_data_stable"] == 0, d
    assert d["hits_valid_hold"] >= 3 and d["hits_data_stable"] >= 3, f"cover not reached: {d}"


@cocotb.test()
async def valid_dropped_is_caught(dut):
    """VALID removed before READY: R-3.1-05 must fire."""
    await start(dut)
    before = counts(dut)
    await drive(dut, [(1, 0, 0x11), (0, 0, 0x11)])
    d = delta(counts(dut), before)
    dut._log.info("valid dropped: %s", d)
    assert d["fails_valid_hold"] >= 1, f"R-3.1-05 did not catch the violation: {d}"


@cocotb.test()
async def data_changed_is_caught(dut):
    """Data changed while waiting for READY: R-3.1-03 must fire, R-3.1-05 must not."""
    await start(dut)
    before = counts(dut)
    await drive(dut, [(1, 0, 0x11), (1, 0, 0x22), (1, 1, 0x22)])
    d = delta(counts(dut), before)
    dut._log.info("data changed: %s", d)
    assert d["fails_data_stable"] >= 1, f"R-3.1-03 did not catch the violation: {d}"
    assert d["fails_valid_hold"] == 0, d

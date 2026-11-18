"""cocotb 2.1 coverage-closure tests for m_apb_tlul_bridge (COV-101, COV-102).

Reuses the cycle engine, requester/device models and the port monitor of the base module
(test_apb_tlul_bridge).  The port monitor re-checks CHK-001 .. CHK-017 at every edge; each
test additionally asserts the checks named by its scenario explicitly, edge by edge.

Timing model: one cycle runs from one falling edge to the next; outputs are sampled and
inputs driven at the falling edge, giving "the values at the rising edge E that ends the
cycle".  E0 is the Setup edge of a transfer, E_m the edge m cycles later.
"""
import collections

import cocotb
from cocotb.triggers import RisingEdge, Timer

from nnc_cocotb import *  # noqa: F401,F403
import test_apb_tlul_bridge as base

SRC = base.SRC_ID & base.SRC_MASK


# ======================================================================================
# COV-101: long response delays (8, 9, 12, 20; a_ready back pressure 3 + delay 10; d_error)
# ======================================================================================
@cocotb.test()
async def test_cov_101_long_response_delay(dut):
    """COV-101: CHK-010, CHK-008, CHK-009, CHK-011, CHK-016, CHK-002, CHK-005, CHK-004:
    aligned reads and full-strobe writes with long TL-UL response delays (8, 9, 12, 20 cycles
    after acceptance), a 3-cycle a_ready back-pressure variant with a 10-cycle delay, and a
    long-delay read with d_error=1."""
    c = "COV-101"
    b = await base.start(dut, c, "cov101")
    q = b.r
    T = base.Transfer
    seq = []
    for j in (8, 9, 12, 20):
        seq.append(T(0, base.aligned(q), 0, 0x0, 0, 2, 0, j, "ok", base.nz32(q)))
        seq.append(T(1, base.aligned(q), q.getrandbits(32), 0xF, 0, 2, 0, j, "ok", base.nz32(q)))
    seq.append(T(0, base.aligned(q), 0, 0x0, 0, 2, 3, 10, "ok", base.nz32(q)))
    seq.append(T(1, base.aligned(q), q.getrandbits(32), 0xF, 0, 2, 3, 10, "ok", base.nz32(q)))
    seq.append(T(0, base.aligned(q), 0, 0x0, 0, 2, 0, 12, "derr", base.nz32(q)))
    seq.append(T(0, base.aligned(q), 0, 0x0, 0, 2, 0, 20, "derr", base.nz32(q)))

    await b.run(seq)
    await b.finish()
    assert len(b.done) == len(seq), f"{c}: expected {len(seq)} scored completions got {len(b.done)}"

    for t in seq:
        d = t.desc()
        k, j = t.k, t.j
        A = 2 + k + j
        assert t.access == A, f"CHK-010: {d}: expected o_apb_pready=1 first at E{A} got E{t.access}"
        # CHK-009: a_valid only inside the Access phase before PREADY (E1 .. E(1+k))
        for m in range(1, 2 + k):
            r = t.rec(m)
            assert r["o_tlul_a_valid"] == 1, f"CHK-009: {d}: expected o_tlul_a_valid=1 at E{m} got 0"
            assert r["i_apb_psel"] == 1 and r["i_apb_penable"] == 1 and r["o_apb_pready"] == 0, \
                f"CHK-009: {d}: a_valid=1 at E{m} with psel={r['i_apb_psel']} " \
                f"penable={r['i_apb_penable']} pready={r['o_apb_pready']}"
            exp_ar = 1 if m == 1 + k else 0
            assert r["i_tlul_a_ready"] == exp_ar, \
                f"{c}: {d}: testbench expected a_ready={exp_ar} at E{m} got {r['i_tlul_a_ready']}"
        # CHK-016 (E(2+k)) and CHK-008 (no new request until the APB completion)
        for m in range(2 + k, A + 2):
            r = t.rec(m)
            assert r["o_tlul_a_valid"] == 0, \
                f"{'CHK-016' if m == 2 + k else 'CHK-008'}: {d}: expected o_tlul_a_valid=0 at E{m} got 1"
        # stimulus sanity: no D-channel traffic during the wait, one response at E(1+k+j)
        for m in range(1, 1 + k + j):
            assert t.rec(m)["i_tlul_d_valid"] == 0, f"{c}: {d}: testbench drove d_valid at E{m}"
        rr = t.rec(1 + k + j)
        assert rr["i_tlul_d_valid"] == 1 and rr["o_tlul_d_ready"] == 1, \
            f"CHK-010: {d}: expected counted response at E{1 + k + j} (d_valid=1 d_ready=1) got " \
            f"{rr['i_tlul_d_valid']}/{rr['o_tlul_d_ready']}"
        # CHK-011 / CHK-004: no PREADY and PRDATA held during the long wait
        for m in range(1, A):
            r, p = t.rec(m), t.rec(m - 1)
            assert r["o_apb_pready"] == 0, f"CHK-011: {d}: expected o_apb_pready=0 at E{m} got 1"
            assert r["o_apb_pslverr"] == 0, f"CHK-011: {d}: expected o_apb_pslverr=0 at E{m} got 1"
            assert r["o_apb_prdata"] == p["o_apb_prdata"], \
                f"CHK-004: {d}: expected o_apb_prdata to hold 0x{p['o_apb_prdata']:08x} at E{m} got " \
                f"0x{r['o_apb_prdata']:08x}"
        # CHK-010 / CHK-005: completion one cycle after the counted response
        err = 1 if t.resp == "derr" else 0
        exp_prd = t.d_data if (not t.write and not err) else 0
        rp = t.rec(A)
        assert rp["o_apb_pready"] == 1, f"CHK-010: {d}: expected o_apb_pready=1 at E{A} got 0"
        assert rp["o_apb_pslverr"] == err, \
            f"CHK-010: {d}: expected o_apb_pslverr={err} at E{A} got {rp['o_apb_pslverr']}"
        assert rp["o_apb_prdata"] == exp_prd, \
            f"{'CHK-005' if exp_prd == 0 else 'CHK-010'}: {d}: expected o_apb_prdata=0x{exp_prd:08x} at " \
            f"E{A} got 0x{rp['o_apb_prdata']:08x}"
        # CHK-002: one-cycle pulse; CHK-004 after the pulse
        rn = t.rec(A + 1)
        assert rn["o_apb_pready"] == 0, f"CHK-002: {d}: expected o_apb_pready=0 at E{A + 1} got 1"
        assert rn["o_apb_prdata"] == rp["o_apb_prdata"], \
            f"CHK-004: {d}: expected o_apb_prdata to hold 0x{rp['o_apb_prdata']:08x} at E{A + 1} got " \
            f"0x{rn['o_apb_prdata']:08x}"
        assert len(t.hs) == 1 and t.hs[0]["n"] == t.setup_n + 1 + k, \
            f"CHK-008: {d}: expected exactly one handshake at E{1 + k} got " \
            f"{[h['n'] - t.setup_n for h in t.hs]}"

    js = collections.Counter((t.k, t.j, t.resp, t.write) for t in seq)
    for j in (8, 9, 12, 20):
        assert js[(0, j, "ok", 0)] >= 1 and js[(0, j, "ok", 1)] >= 1, f"{c}: delay bin {j} not covered"
    assert js[(3, 10, "ok", 0)] >= 1 and js[(3, 10, "ok", 1)] >= 1, f"{c}: back-pressure bin not covered"
    assert any(t.resp == "derr" and t.j >= 8 and t.pslverr == 1 for t in seq), \
        f"{c}: long-delay error completion not covered"


# ======================================================================================
# COV-102: stale / orphan response at reset release
# ======================================================================================
async def _cov102_run(dut, label, mode, setup_write, seed):
    """One reset-release run; returns a result dict that the test asserts on.

    mode 'held'  : d_valid=1 (AccessAckData, correct source, no error) during reset and
                   through the first edge after release.
    mode 'pulse' : d_valid=0 in reset, pulsed only in the cycle ending at the first edge
                   after release (AccessAck, d_error=1).
    setup_write  : None = APB idle at that edge; 0/1 = a legal read/write Setup at that edge.
    """
    c = f"COV-102[{label}]"
    b = base.Bench(dut, c, rng(seed))
    b.trace = collections.deque(maxlen=4096)
    q = b.r
    forced = {}
    dev_step = b.dev.step

    def step_with_force(s):
        dev_step(s)
        if forced:
            b.drive(**forced)

    b.dev.step = step_with_force

    sdata = base.nz32(q)
    if mode == "held":
        stale = dict(i_tlul_d_valid=1, i_tlul_d_opcode=1, i_tlul_d_source=SRC, i_tlul_d_error=0,
                     i_tlul_d_data=sdata)
    else:
        stale = dict(i_tlul_d_valid=1, i_tlul_d_opcode=0, i_tlul_d_source=SRC, i_tlul_d_error=1,
                     i_tlul_d_data=sdata)

    first = None
    if setup_write is not None:
        dd = base.nz32(q)
        while dd == sdata:
            dd = base.nz32(q)
        first = base.Transfer(setup_write, base.aligned(q), q.getrandbits(32),
                              0xF if setup_write else 0x0, 0, 0, 0, 1, "ok", dd)

    if mode == "held":
        forced.update(stale)
    await b.power_on(edges=6)          # >= 5 reset edges, release 1 time unit after an edge
    if first is not None:
        b.req.queue.append(first)      # Setup in the first cycle after release
    forced.clear()
    forced.update(stale)
    r1 = await b.cycle()               # cycle ending at E1 (first edge after release)
    await RisingEdge(b.clk)
    await Timer(1, unit="step")
    forced.clear()
    b.drive(i_tlul_d_valid=0)

    w = base.Transfer(1, base.aligned(q), q.getrandbits(32), 0xF, 0, 5 if first is not None else 0,
                      0, 1, "ok", base.nz32(q))
    rd = base.Transfer(0, base.aligned(q), 0, 0x0, 0, 1, 0, 1, "ok", base.nz32(q))
    if first is None:
        await b.idle(5)
    await b.run([w, rd])
    await b.finish()

    recs = list(b.trace)
    i1 = next((i for i, r in enumerate(recs) if r["i_rst_n_core"] == 1), None)
    assert i1 is not None, f"{c}: testbench: no edge after reset release recorded"
    assert recs[i1] is r1, f"{c}: testbench: first post-release record mismatch"
    assert i1 + 1 < len(recs), f"{c}: testbench: no second edge after release recorded"
    exp_dv = 1 if mode == "held" else 0
    for r in recs[:i1]:
        assert r["i_tlul_d_valid"] == exp_dv, f"{c}: testbench: d_valid={r['i_tlul_d_valid']} in reset"
    for r in recs[i1:]:
        assert r["i_rst_n_core"] == 1, f"{c}: testbench: unexpected reset at cycle {r['n']}"
    assert r1["i_tlul_d_valid"] == 1, f"{c}: testbench: stale d_valid not present at E1"
    if first is None:
        for r in recs[i1:i1 + 6]:
            assert r["i_apb_psel"] == 0, f"{c}: testbench: APB not idle at cycle {r['n']}"
    else:
        assert first.setup_n == r1["n"], f"{c}: testbench: Setup not at E1 after release"
        assert r1["i_apb_psel"] == 1 and r1["i_apb_penable"] == 0, f"{c}: testbench: E1 is not a Setup edge"

    return dict(c=c, b=b, recs=recs, i1=i1, first=first, w=w, rd=rd, sdata=sdata,
                write=setup_write, mode=mode)


@cocotb.test()
async def test_cov_102_stale_response_at_reset_release(dut):
    """COV-102: CHK-013, CHK-011, CHK-012, CHK-004, CHK-003, CHK-008, CHK-006, CHK-010:
    stale/orphan d_valid during reset and at the first edge after release (held AccessAckData,
    pulsed AccessAck with d_error), APB idle or a Setup coinciding with that edge; the stale
    response has no APB effect and the following write and read complete normally."""
    start_clock(dut)
    runs = [("run1-held-idle", "held", None, "cov102-1"),
            ("run2-pulse-idle", "pulse", None, "cov102-2"),
            ("run3-held-read-setup", "held", 0, "cov102-3"),
            ("run3-pulse-write-setup", "pulse", 1, "cov102-4")]
    for label, mode, sw, seed in runs:
        res = await _cov102_run(dut, label, mode, sw, seed)
        c = res["c"]
        recs = res["recs"]
        i1 = res["i1"]
        first = res["first"]
        r1, r2 = recs[i1], recs[i1 + 1]

        # CHK-012: reset values at every reset edge (at least 5 edges)
        rst_recs = recs[:i1]
        assert len(rst_recs) >= 5, f"CHK-012: {c}: expected at least 5 reset edges got {len(rst_recs)}"
        for r in rst_recs:
            e = base.reset_value_errors(r)
            assert not e, f"CHK-012: {c}: expected reset values at cycle {r['n']} got {e}"

        # CHK-003: PSLVERR only with PREADY, at every edge
        for r in recs:
            if r["o_apb_pslverr"] == 1:
                assert r["o_apb_pready"] == 1, f"CHK-003: {c}: pslverr=1 without pready at cycle {r['n']}"

        # CHK-013: d_ready constant 1 from the second post-release edge onward
        for r in recs[i1 + 1:]:
            assert r["o_tlul_d_ready"] == 1, \
                f"CHK-013: {c}: expected o_tlul_d_ready=1 at cycle {r['n']} got {r['o_tlul_d_ready']}"

        # CHK-011 / CHK-004: the stale response at E1 has no APB effect at E2
        assert r2["o_apb_pready"] == 0 and r2["o_apb_pslverr"] == 0, \
            f"CHK-011: {c}: stale response at E1 produced pready={r2['o_apb_pready']} " \
            f"pslverr={r2['o_apb_pslverr']} at the next edge"
        assert r2["o_apb_prdata"] == r1["o_apb_prdata"], \
            f"CHK-004: {c}: expected o_apb_prdata to hold 0x{r1['o_apb_prdata']:08x} got " \
            f"0x{r2['o_apb_prdata']:08x}"

        # CHK-011: exactly one PREADY per APB transfer after release (no orphan completion)
        n_xfer = 3 if first is not None else 2
        n_pr = sum(1 for r in recs[i1:] if r["o_apb_pready"] == 1)
        assert n_pr == n_xfer, f"CHK-011: {c}: expected {n_xfer} PREADY pulses after release got {n_pr}"
        assert len(res["b"].done) == n_xfer, \
            f"{c}: expected {n_xfer} scored completions got {len(res['b'].done)}"

        if first is None:
            for r in recs[i1:i1 + 6]:
                assert r["o_apb_pready"] == 0 and r["o_apb_pslverr"] == 0 and r["o_apb_prdata"] == 0 \
                    and r["o_tlul_a_valid"] == 0, \
                    f"CHK-011: {c}: expected pready=0 pslverr=0 prdata=0 a_valid=0 while idle after release " \
                    f"(cycle {r['n']}) got {r['o_apb_pready']}/{r['o_apb_pslverr']}/" \
                    f"0x{r['o_apb_prdata']:08x}/{r['o_tlul_a_valid']}"
        else:
            d = first.desc()
            sw = res["write"]
            # CHK-006 at the Setup edge coinciding with the stale d_valid
            assert r1["o_apb_pready"] == 0 and r1["o_tlul_a_valid"] == 0, \
                f"CHK-006: {c}: {d}: expected pready=0 a_valid=0 at the Setup edge got " \
                f"{r1['o_apb_pready']}/{r1['o_tlul_a_valid']}"
            exp_op = 0 if sw else 4
            assert r2["o_tlul_a_valid"] == 1 and r2["o_apb_pready"] == 0 and r2["o_tlul_d_ready"] == 1, \
                f"CHK-006: {c}: {d}: expected a_valid=1 pready=0 d_ready=1 at E1 of the transfer got " \
                f"{r2['o_tlul_a_valid']}/{r2['o_apb_pready']}/{r2['o_tlul_d_ready']}"
            assert r2["o_tlul_a_opcode"] == exp_op, \
                f"CHK-006: {c}: {d}: expected a_opcode={exp_op} got {r2['o_tlul_a_opcode']}"
            assert r2["o_tlul_a_address"] == (first.addr & ~3), \
                f"CHK-006: {c}: {d}: expected a_address=0x{first.addr:x} got 0x{r2['o_tlul_a_address']:x}"
            if sw:
                assert r2["o_tlul_a_data"] == first.wdata, \
                    f"CHK-006: {c}: {d}: expected a_data=0x{first.wdata:08x} got 0x{r2['o_tlul_a_data']:08x}"
            assert len(first.hs) == 1 and first.hs[0]["n"] == first.setup_n + 1, \
                f"CHK-008: {c}: {d}: expected one handshake at E1 got " \
                f"{[h['n'] - first.setup_n for h in first.hs]}"
            exp_prd = 0 if sw else first.d_data
            assert first.access == 3 and first.pslverr == 0 and first.prdata == exp_prd, \
                f"CHK-010: {c}: {d}: expected pready at E3 pslverr=0 prdata=0x{exp_prd:08x} (stale data " \
                f"0x{res['sdata']:08x} ignored) got E{first.access}/{first.pslverr}/0x{(first.prdata or 0):08x}"

        for t in (res["w"], res["rd"]):
            d = t.desc()
            exp_prd = 0 if t.write else t.d_data
            assert len(t.hs) == 1 and t.hs[0]["n"] == t.setup_n + 1, \
                f"CHK-008: {c}: {d}: expected one handshake at E1 got {[h['n'] - t.setup_n for h in t.hs]}"
            assert t.hs[0]["opcode"] == (0 if t.write else 4) and t.hs[0]["address"] == t.addr, \
                f"CHK-006: {c}: {d}: wrong request opcode/address {t.hs[0]}"
            assert t.access == 3 and t.pslverr == 0 and t.prdata == exp_prd, \
                f"CHK-010: {c}: {d}: expected pready at E3 pslverr=0 prdata=0x{exp_prd:08x} got " \
                f"E{t.access}/{t.pslverr}/0x{(t.prdata or 0):08x}"

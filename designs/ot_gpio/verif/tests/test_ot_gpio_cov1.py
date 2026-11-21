"""cocotb 2.1 coverage-closure tests for ot_gpio_nnc (COV-101, COV-102).

Reuses the environment of the base module (test_ot_gpio.py): TL-UL host with the
CHK-012/CHK-013 monitor, the per-edge sampler with the CHK-001/CHK-005/CHK-008
checks, and the parameter-aware drive timing (GpioAsyncOn=0: every input is driven
just after a rising edge).  All expected values come from the verification
contract (CHK-003, CHK-004, CHK-005, CHK-006, CHK-013, CHK-035) and the quoted
specification text.  Neither scenario depends on a parameter value, so both
run unchanged in every configuration (base, sync_off, straps_off, min).
"""
import cocotb
from cocotb.triggers import FallingEdge

import test_ot_gpio as base
from nnc_cocotb import *  # noqa: F401,F403

M = 0xFFFFFFFF
OP_PUTF, OP_PUTP, OP_GET = base.OP_PUTF, base.OP_PUTP, base.OP_GET

DIRECT_OUT = base.DIRECT_OUT
MASKED_OUT_LOWER = base.MASKED_OUT_LOWER
MASKED_OUT_UPPER = base.MASKED_OUT_UPPER
DIRECT_OE = base.DIRECT_OE
MASKED_OE_LOWER = base.MASKED_OE_LOWER
MASKED_OE_UPPER = base.MASKED_OE_UPPER
INTR_ENABLE = base.INTR_ENABLE

H_RST, H_GPIO, H_OE, H_INTR, H_DINTG = base.H_RST, base.H_GPIO, base.H_OE, base.H_INTR, base.H_DINTG


def hx(v):
    return base.hx(v)


# ---------------------------------------------------------------- CHK-004 shadow model
def is_out_addr(a):
    return (a in (DIRECT_OUT, MASKED_OUT_LOWER, MASKED_OUT_UPPER,
                  DIRECT_OE, MASKED_OE_LOWER, MASKED_OE_UPPER)
            or (0x100 <= a < 0x180 and a % 4 == 0)
            or (0x200 <= a < 0x300 and (a - 0x200) % 8 == 0))


def _masked(cur, data, upper):
    m = (data >> 16) & 0xFFFF
    v = data & 0xFFFF
    if upper:
        m <<= 16
        v <<= 16
    return ((cur & ~m) | (v & m)) & M


def shadow_update(out, oe, a, d):
    """CHK-004 shadow update from address a and write data d."""
    d &= M
    if a == DIRECT_OUT:
        out = d
    elif a == MASKED_OUT_LOWER:
        out = _masked(out, d, False)
    elif a == MASKED_OUT_UPPER:
        out = _masked(out, d, True)
    elif 0x100 <= a < 0x180 and a % 4 == 0:
        i = (a - 0x100) // 4
        out = (out & ~(1 << i) & M) | ((d & 1) << i)
    elif a == DIRECT_OE:
        oe = d
    elif a == MASKED_OE_LOWER:
        oe = _masked(oe, d, False)
    elif a == MASKED_OE_UPPER:
        oe = _masked(oe, d, True)
    elif 0x200 <= a < 0x300 and (a - 0x200) % 8 == 0:
        i = (a - 0x200) // 8
        oe = (oe & ~(1 << i) & M) | ((d & 1) << i)
    return out, oe


def check_chk004_windows(env, writes, rel, end):
    """CHK-004: from reset release until the first output write o_gpio/o_gpio_en = 0;
    from Ed+2 of each write until the next write's A handshake they equal the shadow.
    (Writes are issued one at a time in these tests.)"""
    out = oe = 0
    lo = rel
    for w in sorted(writes, key=lambda r: r.a_edge):
        if not is_out_addr(w.addr):
            continue
        hi = w.a_edge - 1
        env.hist_eq(lo, hi, H_GPIO, out, f"CHK-004: o_gpio must equal shadow DATA_OUT before {w}")
        env.hist_eq(lo, hi, H_OE, oe, f"CHK-004: o_gpio_en must equal shadow DATA_OE before {w}")
        if w.d_error == 0:
            out, oe = shadow_update(out, oe, w.addr, w.data)
        lo = w.d_edge + 2
    env.hist_eq(lo, end, H_GPIO, out, "CHK-004: o_gpio must equal shadow DATA_OUT after last write")
    env.hist_eq(lo, end, H_OE, oe, "CHK-004: o_gpio_en must equal shadow DATA_OE after last write")


def check_no_alert(env, rel, end):
    p = env.alerts(rel, end)
    assert not p, f"{env.chk}: CHK-003: o_alert must never pulse without an alert cause, got pulses at {p}"


def check_no_dintg(env, rel, end):
    env.check_hist(rel, end, H_DINTG, lambda v: v == 0,
                   "CHK-005: o_d_intg_err must be 0 at every edge with rst_ni=1")


# ---------------------------------------------------------------- traffic helper
class Traffic:
    """Issues one request at a time, each with its own a_source, and checks the
    CHK-013 echo (d_source, d_size, d_opcode) of its response."""

    def __init__(self, env, src0):
        self.env = env
        self.src = src0
        self.writes = []
        self.reqs = []

    def next_src(self):
        s = self.src
        self.src = (self.src + 1) & 0xFF
        return s

    async def req(self, op, addr, data=0, mask=0xF, size=2, what=""):
        s = self.next_src()
        r = await self.env.host.access(op, addr, data, mask=mask, size=size, source=s)
        exp_op = 1 if op == OP_GET else 0
        assert r.d_source == s, (f"{self.env.chk}: CHK-013: d_source expected {s} got {r.d_source} "
                                 f"for {r}{what}")
        assert r.d_size == size, (f"{self.env.chk}: CHK-013: d_size expected {size} got {r.d_size} "
                                  f"for {r}{what}")
        assert r.d_opcode == exp_op, (f"{self.env.chk}: CHK-013: d_opcode expected {exp_op} got "
                                      f"{r.d_opcode} for {r}{what}")
        self.reqs.append(r)
        if op in (OP_PUTF, OP_PUTP):
            self.writes.append(r)
        return r

    async def get_full(self, addr, exp, what=""):
        r = await self.req(OP_GET, addr, what=what)
        assert r.d_error == 0, f"{self.env.chk}: full-word Get of 0x{addr:03x}{what} expected d_error=0 got {r.d_error}"
        assert r.d_data is not None and r.d_data == (exp & M), (
            f"{self.env.chk}: full-word Get of 0x{addr:03x}{what} expected {hx(exp)} got {hx(r.d_data)}")
        return r


# ================================================================ COV-101
@cocotb.test()
async def test_cov_101_putpartial_fullword(dut):
    """COV-101: CHK-013, CHK-004, CHK-006, CHK-003 - full-word writes with the
    PutPartialData opcode (a_size=2, mask 1111) behave as normal full-word writes."""
    G = 0x5AC33CA5
    env = await base.setup(dut, "COV-101", gpio=G)
    rel = env.rel_edge
    t = Traffic(env, 0x10)
    m = env.model

    async def put(addr, data, what):
        w = await t.req(OP_PUTP, addr, data, mask=0xF, size=2, what=what)
        assert w.d_error == 0, (f"COV-101: PutPartialData (mask 1111, size 2) of {hx(data)} to "
                                f"0x{addr:03x}{what} expected d_error=0 got {w.d_error}")
        m.write(addr, data)
        # at least 4 idle cycles after the response before anything else
        await env.wait_edge(w.d_edge + 6)
        env.hist_eq(w.d_edge + 2, None, H_GPIO, m.out, f"CHK-004: o_gpio from D+2 after{what}")
        env.hist_eq(w.d_edge + 2, None, H_OE, m.oe, f"CHK-004: o_gpio_en from D+2 after{what}")
        return w

    # (1) DIRECT_OUT
    await put(DIRECT_OUT, 0xA5C30F96, " (step 1, DIRECT_OUT)")
    assert m.out == 0xA5C30F96
    await t.get_full(DIRECT_OUT, 0xA5C30F96, " (step 1)")
    await t.get_full(MASKED_OUT_LOWER, 0x00000F96, " (step 1)")
    await t.get_full(MASKED_OUT_UPPER, 0x0000A5C3, " (step 1)")
    # (2) DIRECT_OE
    await put(DIRECT_OE, 0x3C3CC3C3, " (step 2, DIRECT_OE)")
    assert m.oe == 0x3C3CC3C3
    await t.get_full(DIRECT_OE, 0x3C3CC3C3, " (step 2)")
    # (3) MASKED_OUT_UPPER, mask field all ones
    await put(MASKED_OUT_UPPER, 0xFFFF1234, " (step 3, MASKED_OUT_UPPER)")
    assert m.out == 0x12340F96
    await t.get_full(DIRECT_OUT, 0x12340F96, " (step 3)")
    # (4) per-pin views
    await put(base.PP_IO(0), 0x00000000, " (step 4, PER_PIN_IO_0)")
    await put(base.PP_OE(31), 0x00000000, " (step 4, PER_PIN_OE_31)")
    exp_out = 0x12340F96 & ~1 & M
    exp_oe = 0x3C3CC3C3 & ~(1 << 31) & M
    assert m.out == exp_out and m.oe == exp_oe
    await t.get_full(DIRECT_OUT, exp_out, " (step 4)")
    await t.get_full(DIRECT_OE, exp_oe, " (step 4)")
    # (5) INTR_ENABLE
    await put(INTR_ENABLE, 0x00000000, " (step 5, INTR_ENABLE)")
    await t.get_full(INTR_ENABLE, 0x00000000, " (step 5)")

    await env.idle(8)
    end = env.edge() - 1
    # CHK-004 over the whole run
    check_chk004_windows(env, t.writes, rel, end)
    # CHK-006: shadow_en is 0 from reset (never written to non-zero), so o_intr_gpio stays 0
    for w in t.writes:
        if w.addr == INTR_ENABLE:
            assert w.d_error == 0 and w.data == 0
    env.hist_eq(rel, end, H_INTR, 0, "CHK-006: o_intr_gpio must be 0 while INTR_ENABLE=0")
    # CHK-003
    check_no_alert(env, rel, end)
    check_no_dintg(env, rel, end)
    assert not env.host.out, f"COV-101: CHK-013: unanswered requests remain: {list(env.host.out.values())}"
    env.finish()


# ================================================================ COV-102
@cocotb.test()
async def test_cov_102_mask_size_combinations(dut):
    """COV-102: CHK-035, CHK-013, CHK-004, CHK-003, CHK-005 - mask/size combinations:
    size 0 with mask 1111 rejected without effect; size 2 with partial masks answered once
    with echoed fields; partial writes of the stored value leave DIRECT_OUT unchanged."""
    G = 0x0F0FA5A5
    env = await base.setup(dut, "COV-102", gpio=G)
    rel = env.rel_edge
    t = Traffic(env, 0x40)

    # preload DIRECT_OUT = 0 and DIRECT_OE = 0 with normal full-word writes
    w = await t.req(OP_PUTF, DIRECT_OUT, 0x00000000, what=" (preload DIRECT_OUT)")
    assert w.d_error == 0, f"COV-102: preload DIRECT_OUT expected d_error=0 got {w.d_error}"
    w = await t.req(OP_PUTF, DIRECT_OE, 0x00000000, what=" (preload DIRECT_OE)")
    assert w.d_error == 0, f"COV-102: preload DIRECT_OE expected d_error=0 got {w.d_error}"
    await env.wait_edge(w.d_edge + 4)

    # (a) mask 1111 with a_size=0: inactive lanes marked active -> d_error=1, no change
    ta = env.edge()
    for addr, nm in ((DIRECT_OUT, "DIRECT_OUT"), (DIRECT_OE, "DIRECT_OE")):
        r = await t.req(OP_GET, addr, 0, mask=0xF, size=0, what=f" (a) Get size 0 {nm}")
        assert r.d_error == 1, (f"COV-102: CHK-035: (a) Get a_size=0 mask 1111 at 0x{addr:03x} "
                                f"expected d_error=1 got {r.d_error}")
        await t.get_full(DIRECT_OUT, 0, f" (after (a) Get size 0 at {nm})")
        if addr == DIRECT_OE:
            await t.get_full(DIRECT_OE, 0, " (after (a) Get size 0 at DIRECT_OE)")
        r = await t.req(OP_PUTP, addr, M, mask=0xF, size=0, what=f" (a) PutPartialData size 0 {nm}")
        assert r.d_error == 1, (f"COV-102: CHK-035: (a) PutPartialData a_size=0 mask 1111 at "
                                f"0x{addr:03x} expected d_error=1 got {r.d_error}")
        await env.idle(4)
        await t.get_full(DIRECT_OUT, 0, f" (after (a) PutPartialData size 0 at {nm})")
        await t.get_full(DIRECT_OE, 0, f" (after (a) PutPartialData size 0 at {nm})")
    await env.idle(4)
    ta_end = env.edge() - 1
    env.hist_eq(ta, ta_end, H_GPIO, 0, "CHK-035: o_gpio must not change during (a)")
    env.hist_eq(ta, ta_end, H_OE, 0, "CHK-035: o_gpio_en must not change during (a)")

    # (b) a_size=2 with partial masks: one response with echoed fields (error/data not checked)
    for mk in (0b0011, 0b1100, 0b0001, 0b1000):
        await t.req(OP_GET, DIRECT_OUT, 0, mask=mk, size=2, what=f" (b) Get mask {mk:04b}")
        await t.get_full(DIRECT_OUT, 0, f" (after (b) Get mask {mk:04b})")

    # (c) size-2 partial-mask writes of the value already stored
    V = 0x5A5A5A5A
    w = await t.req(OP_PUTF, DIRECT_OUT, V, what=" (c) full-word write")
    assert w.d_error == 0, f"COV-102: (c) full-word DIRECT_OUT write expected d_error=0 got {w.d_error}"
    await t.get_full(DIRECT_OUT, V, " (after (c) full-word write)")
    for op in (OP_PUTF, OP_PUTP):
        for mk in (0b0011, 0b1100):
            await t.req(op, DIRECT_OUT, V, mask=mk, size=2, what=f" (c) op {op} mask {mk:04b}")
            await t.get_full(DIRECT_OUT, V, f" (after (c) op {op} mask {mk:04b})")
    await t.get_full(DIRECT_OUT, V, " (end of (c))")

    # let any duplicate (orphan) response show up before closing
    await env.idle(16)
    end = env.edge() - 1
    check_chk004_windows(env, t.writes, rel, end)
    check_no_alert(env, rel, end)
    check_no_dintg(env, rel, end)
    for r in t.reqs:
        assert r.done, f"COV-102: CHK-013: request {r} got no response"
    assert not env.host.out, f"COV-102: CHK-013: unanswered requests remain: {list(env.host.out.values())}"
    env.finish()

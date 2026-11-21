"""cocotb 2.1 testbench for ot_gpio_nnc (gpio + TL-UL wrapper).

All stimulus and expected values are derived from the gpio / comportability /
TL-UL specification text and the verification plan (CHK-001..CHK-038).
Timing model: with GpioAsyncOn=1 inputs are driven right after a falling edge
of clk_i; with GpioAsyncOn=0 every input (except rst_ni) is driven just after a
rising edge of clk_i (INT-CLK-002, CHK-011 rule (f)).  Outputs are sampled at
the falling edge after all drives settled (ReadOnly).  A value sampled there is
the value seen at the following rising edge, which is the edge number used for
every timing statement ("edge U").
"""
# NNC verification fix (fix-verif, triage B): with GpioAsyncOn=0 all inputs change only just after rising edges (contract CHK-011 rule (f), INT-CLK-002); edge numbering is unchanged.
from collections import deque

import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, ReadOnly, Timer
from cocotb.utils import get_sim_time

from nnc_cocotb import *  # noqa: F401,F403

M = 0xFFFFFFFF

# ---------------------------------------------------------------- register map
INTR_STATE = 0x00
INTR_ENABLE = 0x04
INTR_TEST = 0x08
ALERT_TEST = 0x0C
DATA_IN = 0x10
DIRECT_OUT = 0x14
MASKED_OUT_LOWER = 0x18
MASKED_OUT_UPPER = 0x1C
DIRECT_OE = 0x20
MASKED_OE_LOWER = 0x24
MASKED_OE_UPPER = 0x28
INTR_CTRL_EN_RISING = 0x2C
INTR_CTRL_EN_FALLING = 0x30
INTR_CTRL_EN_LVLHIGH = 0x34
INTR_CTRL_EN_LVLLOW = 0x38
CTRL_EN_INPUT_FILTER = 0x3C
HW_STRAPS_DATA_IN_VALID = 0x40
HW_STRAPS_DATA_IN = 0x44

OP_PUTF, OP_PUTP, OP_GET = 0, 1, 4


def PP_IO(i):
    return 0x100 + 4 * i


def PP_OE(i):
    return 0x200 + 8 * i


def PP_IC(i):
    return 0x204 + 8 * i


def is_ppio(a):
    return 0x100 <= a < 0x180 and a % 4 == 0


def is_ppoe(a):
    return 0x200 <= a < 0x300 and (a - 0x200) % 8 == 0


def is_ppic(a):
    return 0x200 <= a < 0x300 and (a - 0x200) % 8 == 4


CTRL_REGS = (INTR_CTRL_EN_RISING, INTR_CTRL_EN_FALLING, INTR_CTRL_EN_LVLHIGH,
             INTR_CTRL_EN_LVLLOW, CTRL_EN_INPUT_FILTER)
RW_REGS = (INTR_ENABLE, DIRECT_OUT, DIRECT_OE) + CTRL_REGS
WIDE_REGS = (INTR_STATE, INTR_ENABLE, INTR_TEST, DIRECT_OUT, MASKED_OUT_LOWER,
             MASKED_OUT_UPPER, DIRECT_OE, MASKED_OE_LOWER, MASKED_OE_UPPER) + CTRL_REGS
BITS4 = (0, 15, 16, 31)
ALL_MAPPED = ([a for a in range(0x00, 0x48, 4)] + [PP_IO(i) for i in range(32)]
              + [0x200 + 4 * k for k in range(64)])
UNMAPPED = (0x048, 0x04C, 0x080, 0x0FC, 0x180, 0x1FC, 0x300, 0x3FC)

# history tuple indices
H_RST, H_GPIO, H_OE, H_INTR, H_ALERT, H_INTEG, H_DINTG, H_SV, H_SD, H_DV = range(10)
H_NAMES = {H_RST: "rst_ni", H_GPIO: "o_gpio", H_OE: "o_gpio_en", H_INTR: "o_intr_gpio",
           H_ALERT: "o_alert", H_INTEG: "o_alert_integ_fail", H_DINTG: "o_d_intg_err",
           H_SV: "o_straps_valid", H_SD: "o_straps_data", H_DV: "o_d_valid"}


def hx(v):
    return "X" if v is None else f"0x{v:08x}"


def param(name, default):
    try:
        v = PARAMS.get(name, default)
        return default if v is None else int(v)
    except Exception:
        return default


# ---------------------------------------------------------------- reference model
class RegModel:
    """Register reference model built from the gpio register descriptions."""

    def __init__(self, straps_on):
        self.straps_on = straps_on
        self.reset()

    def reset(self):
        self.en = 0
        self.out = 0
        self.oe = 0
        self.ctrl = [0, 0, 0, 0, 0]  # rising, falling, lvlhigh, lvllow, filter
        self.regwen = 1
        self.state = 0      # None = unknown (hardware events possible)
        self.sv = 0
        self.sd = 0

    @staticmethod
    def _masked(cur, data, upper):
        m = (data >> 16) & 0xFFFF
        d = data & 0xFFFF
        if upper:
            m <<= 16
            d <<= 16
        return ((cur & ~m) | (d & m)) & M

    def write(self, a, data):
        data &= M
        if a == INTR_STATE:
            if self.state is not None:
                self.state &= ~data & M
        elif a == INTR_ENABLE:
            self.en = data
        elif a == INTR_TEST:
            if self.state is not None:
                self.state |= data
        elif a == ALERT_TEST:
            if not (data >> 31) & 1:
                self.regwen = 0
        elif a == DIRECT_OUT:
            self.out = data
        elif a == MASKED_OUT_LOWER:
            self.out = self._masked(self.out, data, False)
        elif a == MASKED_OUT_UPPER:
            self.out = self._masked(self.out, data, True)
        elif a == DIRECT_OE:
            self.oe = data
        elif a == MASKED_OE_LOWER:
            self.oe = self._masked(self.oe, data, False)
        elif a == MASKED_OE_UPPER:
            self.oe = self._masked(self.oe, data, True)
        elif a in CTRL_REGS:
            self.ctrl[CTRL_REGS.index(a)] = data
        elif is_ppio(a):
            i = (a - 0x100) // 4
            self.out = (self.out & ~(1 << i) & M) | ((data & 1) << i)
        elif is_ppoe(a):
            i = (a - 0x200) // 8
            self.oe = (self.oe & ~(1 << i) & M) | ((data & 1) << i)
        elif is_ppic(a):
            i = (a - 0x204) // 8
            for k in range(5):
                self.ctrl[k] = (self.ctrl[k] & ~(1 << i) & M) | (((data >> k) & 1) << i)

    def read(self, a, gin):
        """Expected (value, compare-mask) of a read, or None if not checked."""
        if a == INTR_STATE:
            return None if self.state is None else (self.state, M)
        if a == INTR_ENABLE:
            return (self.en, M)
        if a == INTR_TEST:
            return (0, M)
        if a == ALERT_TEST:
            return (self.regwen << 31, M)
        if a == DATA_IN:
            return (gin & M, M)
        if a == DIRECT_OUT:
            return (self.out, M)
        if a == MASKED_OUT_LOWER:
            return (self.out & 0xFFFF, M)
        if a == MASKED_OUT_UPPER:
            return (self.out >> 16, M)
        if a == DIRECT_OE:
            return (self.oe, M)
        if a == MASKED_OE_LOWER:
            return (self.oe & 0xFFFF, 0xFFFF)
        if a == MASKED_OE_UPPER:
            return (self.oe >> 16, 0xFFFF)
        if a in CTRL_REGS:
            return (self.ctrl[CTRL_REGS.index(a)], M)
        if a == HW_STRAPS_DATA_IN_VALID:
            return (self.sv, M) if self.straps_on else None
        if a == HW_STRAPS_DATA_IN:
            return (self.sd if self.straps_on else 0, M)
        if is_ppio(a):
            i = (a - 0x100) // 4
            return (((((gin >> i) & 1) << 8) | ((self.out >> i) & 1)), M)
        if is_ppoe(a):
            i = (a - 0x200) // 8
            return ((self.oe >> i) & 1, M)
        if is_ppic(a):
            i = (a - 0x204) // 8
            return (sum((((self.ctrl[k] >> i) & 1) << k) for k in range(5)), M)
        return None


# ---------------------------------------------------------------- TL-UL host model
class Req:
    def __init__(self, opcode, addr, data=0, mask=0xF, size=2, source=None,
                 instr=0, flip=0, param=0):
        self.opcode = opcode
        self.addr = addr
        self.data = data & M
        self.mask = mask
        self.size = size
        self.fixed_source = source
        self.source = source
        self.instr = instr
        self.flip = flip
        self.param = param
        self.accepted = False
        self.done = False
        self.aborted = False
        self.a_edge = None
        self.d_edge = None
        self.d_opcode = self.d_param = self.d_size = None
        self.d_source = self.d_sink = self.d_data = self.d_error = None

    def __repr__(self):
        return (f"Req(op={self.opcode}, addr=0x{self.addr:03x}, data=0x{self.data:08x}, "
                f"size={self.size}, mask=0b{self.mask:04b}, src={self.source})")


class TLHost:
    """TL-UL host: A-channel driver (holds requests until a_ready) and D-channel
    receiver (random back-pressure, matching by d_source, CHK-012/013 monitor)."""

    def __init__(self, env, salt):
        self.env = env
        self.dut = env.dut
        self.r = rng(f"{salt}-tlhost")
        self.q = deque()
        self.out = {}
        self.cur = None
        self.quiet = True
        self.hold_d = False
        self.bp = False
        self.bp_prob = 0.25
        self.bp_max = 10
        self.stall = 0
        self.a_gap_max = 0
        self.gap = 0
        self.src_pref = deque([0x00, 0x01, 0x7F, 0xFF])
        self.prev_d = None
        self.used_sources = set()

    def start(self):
        cocotb.start_soon(self._a_loop())
        cocotb.start_soon(self._d_loop())

    def clear(self):
        for rq in self.q:
            rq.aborted = True
        self.q.clear()
        if self.cur is not None:
            self.cur.aborted = True
            self.cur = None
        for rq in self.out.values():
            rq.aborted = True
        self.out.clear()
        self.prev_d = None
        self.stall = 0
        self.gap = 0

    def _pick_source(self, req):
        if req.fixed_source is not None:
            return req.fixed_source if req.fixed_source not in self.out else None
        if self.r.random() < 0.3:
            s = self.src_pref[0]
            self.src_pref.rotate(-1)
            if s not in self.out:
                return s
        for _ in range(64):
            s = self.r.randrange(256)
            if s not in self.out:
                return s
        return None

    async def _a_loop(self):
        d = self.dut
        # NNC verification fix (fix-verif, triage B): with GpioAsyncOn=0 the A channel is driven just after a rising
        # edge (CHK-011 rule (f), INT-CLK-002) and still sampled at the following falling edge, so the driven value
        # is first seen at the next rising edge = edge(), as before.
        sync = not self.env.async_on
        while True:
            if sync:
                await RisingEdge(d.clk_i)
                await Timer(1, "step")
            else:
                await FallingEdge(d.clk_i)
            if self.quiet:
                if self.cur is not None:
                    self.cur.aborted = True
                    self.cur = None
                d.i_a_valid.value = 0
                continue
            if self.cur is None:
                if self.gap > 0:
                    self.gap -= 1
                elif self.q:
                    src = self._pick_source(self.q[0])
                    if src is not None:
                        self.cur = self.q.popleft()
                        self.cur.source = src
            req = self.cur
            if req is None:
                d.i_a_valid.value = 0
                continue
            d.i_a_opcode.value = req.opcode
            d.i_a_param.value = req.param
            d.i_a_size.value = req.size
            d.i_a_source.value = req.source
            d.i_a_address.value = req.addr
            d.i_a_mask.value = req.mask
            d.i_a_data.value = req.data
            d.i_a_instr.value = req.instr
            d.i_a_intg_flip.value = req.flip
            d.i_a_valid.value = 1
            if sync:
                await FallingEdge(d.clk_i)
            await ReadOnly()
            if val(d.rst_ni) == 1 and val(d.o_a_ready) == 1:
                req.accepted = True
                req.a_edge = self.env.edge()
                if req.flip:
                    self.env.flip_seen = True
                self.out[req.source] = req
                self.used_sources.add(req.source)
                self.cur = None
                if self.a_gap_max > 0:
                    self.gap = self.r.randint(0, self.a_gap_max)

    async def _d_loop(self):
        d = self.dut
        env = self.env
        # NNC verification fix (fix-verif, triage B): with GpioAsyncOn=0 i_d_ready is driven just after a rising edge
        # (CHK-011 rule (f), INT-CLK-002); the D channel is still sampled at the following falling edge.
        sync = not env.async_on
        while True:
            if sync:
                await RisingEdge(d.clk_i)
                await Timer(1, "step")
            else:
                await FallingEdge(d.clk_i)
            if self.hold_d:
                rdy = 0
            elif self.bp:
                if self.stall > 0:
                    rdy = 0
                    self.stall -= 1
                else:
                    rdy = 1
                    if self.r.random() < self.bp_prob:
                        self.stall = self.r.randint(0, self.bp_max)
            else:
                rdy = 1
            d.i_d_ready.value = rdy
            if sync:
                await FallingEdge(d.clk_i)
            await ReadOnly()
            rst = val(d.rst_ni)
            dv = val(d.o_d_valid)
            if rst != 1:
                self.prev_d = None
                continue
            f = (val(d.o_d_opcode), val(d.o_d_param), val(d.o_d_size), val(d.o_d_source),
                 val(d.o_d_sink), val(d.o_d_data), val(d.o_d_error))
            if self.prev_d is not None and (dv != 1 or f != self.prev_d):
                env.err(f"CHK-012: D channel must stay valid and stable under back-pressure; "
                        f"got valid={dv} fields={f} expected {self.prev_d} at edge {env.edge()}")
            self.prev_d = f if (dv == 1 and rdy == 0) else None
            if dv == 1 and rdy == 1:
                src = f[3]
                req = self.out.pop(src, None)
                if req is None:
                    if not env.flip_seen:
                        env.err(f"CHK-013: D beat with d_source={src} matches no outstanding "
                                f"request (orphan) at edge {env.edge()}")
                    continue
                (req.d_opcode, req.d_param, req.d_size, req.d_source, req.d_sink,
                 req.d_data, req.d_error) = f
                req.d_edge = env.edge()
                req.done = True
                if not env.flip_seen:
                    if req.opcode == OP_GET:
                        if req.d_opcode != 1 or req.d_size != req.size:
                            env.err(f"CHK-013: Get response expected d_opcode=1 d_size={req.size} "
                                    f"got d_opcode={req.d_opcode} d_size={req.d_size} for {req}")
                    elif req.opcode in (OP_PUTF, OP_PUTP):
                        if req.d_opcode != 0 or req.d_size != req.size:
                            env.err(f"CHK-013: Put response expected d_opcode=0 d_size={req.size} "
                                    f"got d_opcode={req.d_opcode} d_size={req.d_size} for {req}")
                    elif req.d_error != 1:
                        env.err(f"CHK-035: undefined opcode expected d_error=1 got "
                                f"{req.d_error} for {req}")

    # ---- API
    def issue(self, opcode, addr, data=0, mask=0xF, size=2, source=None, instr=0, flip=0):
        req = Req(opcode, addr, data, mask, size, source, instr, flip)
        self.q.append(req)
        return req

    async def wait(self, req, max_cycles=400):
        for _ in range(max_cycles):
            if req.done:
                return req
            await FallingEdge(self.dut.clk_i)
        assert req.done, f"{self.env.chk}: no TL-UL response within {max_cycles} cycles for {req}"
        return req

    async def access(self, opcode, addr, data=0, mask=0xF, size=2, source=None, instr=0,
                     flip=0, max_cycles=400):
        req = self.issue(opcode, addr, data, mask, size, source, instr, flip)
        return await self.wait(req, max_cycles)

    async def read(self, addr, mask=0xF, size=2, instr=0, max_cycles=400):
        """Full-word Get (by default); returns the completed request."""
        return await self.access(OP_GET, addr, 0, mask=mask, size=size, instr=instr,
                                 max_cycles=max_cycles)


# ---------------------------------------------------------------- environment
class Env:
    def __init__(self, dut, chk):
        self.dut = dut
        self.clk = dut.clk_i
        self.chk = chk
        self.async_on = param("GpioAsyncOn", 1) == 1
        self.straps_on = param("GpioAsHwStrapsEn", 1) == 1
        self.r = rng(chk)
        self.n = 0
        self.hist = {}
        self.errors = []
        self.flip_seen = False
        self.seen_reset = False
        self.prev_rst = None
        self.prev_alert = 0
        self.rel_edge = 0
        self.gpio = 0
        self.period = 0
        self.f2r = 0
        self.model = RegModel(self.straps_on)
        self.host = TLHost(self, chk)

    def err(self, msg):
        if len(self.errors) < 50:
            self.errors.append(msg)

    def edge(self):
        """Number of the rising edge that follows the current falling edge."""
        return self.n + 1

    async def _count(self):
        while True:
            await RisingEdge(self.clk)
            self.n += 1

    async def _sample(self):
        d = self.dut
        while True:
            await FallingEdge(self.clk)
            await ReadOnly()
            U = self.n + 1
            rst = val(d.rst_ni)
            s = (rst, val(d.o_gpio), val(d.o_gpio_en), val(d.o_intr_gpio), val(d.o_alert),
                 val(d.o_alert_integ_fail), val(d.o_d_intg_err), val(d.o_straps_valid),
                 val(d.o_straps_data), val(d.o_d_valid))
            self.hist[U] = s
            if rst == 0:
                self.seen_reset = True
                self.flip_seen = False
                for idx in (H_GPIO, H_OE, H_INTR, H_ALERT, H_INTEG, H_DV):
                    if s[idx] != 0:
                        self.err(f"CHK-008: {H_NAMES[idx]} must be 0 while rst_ni=0, got "
                                 f"{hx(s[idx])} at edge {U}")
            elif rst == 1 and self.seen_reset:
                if s[H_INTEG] != 0:
                    self.err(f"CHK-001: o_alert_integ_fail must be 0, got {hx(s[H_INTEG])} at edge {U}")
                if s[H_DINTG] != 0:
                    self.err(f"CHK-005: o_d_intg_err must be 0, got {hx(s[H_DINTG])} at edge {U}")
                if self.prev_alert == 1 and s[H_ALERT] == 1:
                    self.err(f"CHK-002: o_alert must be a single-cycle pulse, high at edges {U-1},{U}")
                if self.prev_rst == 0:
                    self.rel_edge = U
            self.prev_alert = s[H_ALERT] if rst == 1 else 0
            self.prev_rst = rst

    async def start(self):
        cocotb.start_soon(self._count())
        await RisingEdge(self.clk)
        t0 = get_sim_time("step")
        await FallingEdge(self.clk)
        tf = get_sim_time("step")
        await RisingEdge(self.clk)
        t1 = get_sim_time("step")
        self.period = int(t1 - t0)
        self.f2r = int(t1 - tf)
        cocotb.start_soon(self._sample())
        self.host.start()
        await FallingEdge(self.clk)

    async def drive_sync(self, name, value):
        """Drive input `name`. Called at a falling edge; returns the first rising
        edge at which the new value is present.  GpioAsyncOn=1: at once;
        GpioAsyncOn=0: just after the next rising edge, returning at the
        following falling edge."""
        # NNC verification fix (fix-verif, triage B): with GpioAsyncOn=0 every input changes only just after a rising edge (CHK-011 rule (f), INT-CLK-002).
        sig = getattr(self.dut, name)
        if self.async_on:
            sig.value = value
            return self.edge()
        await RisingEdge(self.clk)
        await Timer(1, "step")
        sig.value = value
        await FallingEdge(self.clk)
        return self.edge()

    async def reset(self, cycles=10, gpio=None):
        self.host.quiet = True
        await FallingEdge(self.clk)
        if gpio is not None:
            self.gpio = gpio & M
        # NNC verification fix (fix-verif, triage B): i_strap_en driven just after a rising edge when GpioAsyncOn=0 (CHK-011 rule (f)).
        await self.drive_sync("i_strap_en", 0)
        await reset_dut(self.dut, cycles=cycles, idle={"i_gpio": self.gpio})
        self.host.clear()
        self.model.reset()
        await FallingEdge(self.clk)
        await FallingEdge(self.clk)
        self.host.clear()
        self.host.quiet = False

    async def idle(self, n):
        for _ in range(n):
            await FallingEdge(self.clk)

    async def wait_edge(self, target):
        for _ in range(max(0, target - self.edge()) + 3):
            if self.edge() >= target:
                return
            await FallingEdge(self.clk)
        assert self.edge() >= target, f"{self.chk}: test bench failed to reach edge {target}"

    def pick_off(self):
        for _ in range(100):
            o = self.r.randint(1, self.period - 1)
            if o != self.f2r:
                return o
        return 1

    async def set_gpio(self, value, off=None):
        """Drive i_gpio. Called at a falling edge; returns the first rising edge
        at which the new value is present.  GpioAsyncOn=1: random time in the
        period; GpioAsyncOn=0: synchronously just after the next rising edge
        (returns at the following falling edge)."""
        value &= M
        U = self.edge()
        if not self.async_on:
            # NNC verification fix (fix-verif, triage B): GpioAsyncOn=0: i_gpio changes only just after a rising edge (INT-CLK-002, CHK-011 rule (f), CHK-021 step 3).
            await RisingEdge(self.clk)
            await Timer(1, "step")
            self.dut.i_gpio.value = value
            self.gpio = value
            await FallingEdge(self.clk)
            return self.edge()
        if self.period < 4:
            self.dut.i_gpio.value = value
            self.gpio = value
            return U
        if off is None:
            off = self.pick_off()
        await Timer(off, "step")
        self.dut.i_gpio.value = value
        self.gpio = value
        E = U if off < self.f2r else U + 1
        await FallingEdge(self.clk)
        return E

    async def gpio_pulse(self, v_on, v_off, n, box):
        """Drive v_on for exactly n rising edges, then v_off. box receives E0."""
        off = self.pick_off() if (self.async_on and self.period >= 4) else None
        E0 = await self.set_gpio(v_on, off)
        box.append(E0)
        # NNC verification fix (fix-verif, triage B): with GpioAsyncOn=0 set_gpio drives after the next rising edge (value present one edge later), so the pulse still lasts exactly n edges.
        late = (off is not None and off > self.f2r) or not self.async_on
        await self.wait_edge(E0 + n - (1 if late else 0))
        await self.set_gpio(v_off, off)

    def check_hist(self, lo, hi, idx, pred, what):
        if hi is None:
            hi = self.edge() - 1
        for U in range(lo, hi + 1):
            s = self.hist.get(U)
            if s is None or s[H_RST] != 1:
                continue
            v = s[idx]
            assert v is not None and pred(v), (
                f"{self.chk}: {what}; got {H_NAMES[idx]}={hx(v)} at edge {U} (window {lo}..{hi})")

    def hist_eq(self, lo, hi, idx, exp, what, mask=M):
        self.check_hist(lo, hi, idx, lambda v: (v & mask) == (exp & mask),
                        f"{what} (expected {hx(exp & mask)} under mask {hx(mask)})")

    def alerts(self, lo, hi):
        out = []
        for U in range(lo, hi + 1):
            s = self.hist.get(U)
            if s is not None and s[H_RST] == 1 and s[H_ALERT] == 1:
                out.append(U)
        return out

    async def rd(self, addr, exp=None, mask=M, err=0, size=2, amask=0xF, instr=0, what=""):
        r = await self.host.access(OP_GET, addr, 0, mask=amask, size=size, instr=instr)
        if err is not None:
            assert r.d_error == err, (f"{self.chk}: read of 0x{addr:03x}{what} expected "
                                      f"d_error={err} got {r.d_error}")
        if exp is not None:
            got = None if r.d_data is None else (r.d_data & mask)
            assert got == (exp & mask), (f"{self.chk}: read of 0x{addr:03x}{what} expected "
                                         f"{hx(exp & mask)} (mask {hx(mask)}) got {hx(got)}")
        return r

    async def wr(self, addr, data, err=0, opcode=OP_PUTF, size=2, amask=0xF, update=True, what=""):
        r = await self.host.access(opcode, addr, data, mask=amask, size=size)
        if err is not None:
            assert r.d_error == err, (f"{self.chk}: write of {hx(data)} to 0x{addr:03x}{what} "
                                      f"expected d_error={err} got {r.d_error}")
        if update and err == 0:
            self.model.write(addr, data)
        return r

    async def rdm(self, addr, extra_mask=M, what=""):
        e = self.model.read(addr, self.gpio)
        if e is None:
            return await self.rd(addr, None, what=what)
        exp, mask = e
        return await self.rd(addr, exp, mask & extra_mask, what=what)

    def finish(self):
        if self.errors:
            more = f" (+{len(self.errors) - 1} more: " + " | ".join(self.errors[1:6]) + ")" \
                if len(self.errors) > 1 else ""
            assert False, self.errors[0] + more


async def setup(dut, chk, gpio=0):
    start_clock(dut)
    env = Env(dut, chk)
    await env.start()
    await env.reset(10, gpio=gpio)
    return env


async def normal_traffic(env, ncycles):
    end = env.edge() + ncycles
    for _ in range(ncycles + 1):
        if env.edge() >= end:
            break
        v = env.r.getrandbits(32)
        await env.wr(DIRECT_OUT, v)
        await env.rd(DIRECT_OUT, v, what=" (normal traffic)")


async def check_all_reset_values(env):
    for a in ALL_MAPPED:
        await env.rdm(a, what=" (reset value)")


# ================================================================ alert tests
@cocotb.test()
async def test_chk_014_alert_test_pulse(dut):
    """CHK-014: each ALERT_TEST.fatal_fault write (regwen kept 1) gives exactly one o_alert pulse."""
    env = await setup(dut, "CHK-014")
    start = env.edge()
    for k in range(3):
        await env.idle(64)
        w = await env.wr(ALERT_TEST, 0x80000001)
        await env.wait_edge(w.d_edge + 66)
        p = env.alerts(w.a_edge, w.d_edge + 64)
        assert len(p) == 1, (f"CHK-014: write {k}: exactly one o_alert pulse in the 64-cycle "
                             f"window expected, got pulses at {p} (A {w.a_edge}, D {w.d_edge})")
        assert p[0] <= w.d_edge + 16, (f"CHK-014: pulse expected no later than D+16={w.d_edge + 16}, "
                                       f"got {p[0]}")
    allp = env.alerts(start, env.edge() - 1)
    assert len(allp) == 3, f"CHK-014: exactly 3 o_alert pulses in total expected, got {allp}"
    await env.rd(ALERT_TEST, 0x80000000, what=" (ALERT_TEST)")
    env.finish()


@cocotb.test()
async def test_chk_015_alert_regwen_lock(dut):
    """CHK-015: ALERT_TEST.regwen (rw0c) locks alert testing until reset."""
    env = await setup(dut, "CHK-015")
    await env.rd(ALERT_TEST, 0x80000000, what=" (step 1)")
    await env.wr(ALERT_TEST, 0x00000000)
    await env.rd(ALERT_TEST, 0x00000000, what=" (step 2)")
    w = await env.wr(ALERT_TEST, 0x80000001, what=" (step 3, locked)")
    await env.idle(64)
    p = env.alerts(w.a_edge, env.edge() - 1)
    assert not p, f"CHK-015: no o_alert pulse expected while regwen=0, got pulses at {p}"
    await env.rd(ALERT_TEST, 0x00000000, what=" (step 3 readback)")
    await env.reset(10)
    await env.rd(ALERT_TEST, 0x80000000, what=" (step 4 after reset)")
    w = await env.wr(ALERT_TEST, 0x80000001)
    await env.idle(64)
    p = env.alerts(w.a_edge, env.edge() - 1)
    assert len(p) == 1 and p[0] <= w.d_edge + 16, (
        f"CHK-015: exactly one pulse no later than D+16={w.d_edge + 16} expected after reset, got {p}")
    env.finish()


@cocotb.test()
async def test_chk_016_intg_error_fatal_alert(dut):
    """CHK-016: command integrity error raises the fatal alert, repeated until reset."""
    env = await setup(dut, "CHK-016")
    for kind in ("get", "put"):
        if kind == "put":
            await env.reset(10)
        t0 = env.edge()
        await normal_traffic(env, 100)
        p = env.alerts(t0, env.edge() - 1)
        assert not p, f"CHK-016: no o_alert during normal traffic expected, got {p}"
        if kind == "get":
            req = env.host.issue(OP_GET, DATA_IN, source=0xA5, flip=1)
        else:
            req = env.host.issue(OP_PUTF, DIRECT_OUT, 0x12345678, source=0x5A, flip=1)
        for _ in range(40):
            if req.accepted:
                break
            await FallingEdge(env.clk)
        assert req.accepted, f"CHK-016: flipped {kind} request not accepted within 40 cycles"
        Ea = req.a_edge
        for _ in range(32):
            if req.done:
                break
            await FallingEdge(env.clk)
        await env.idle(512)
        obs_end = env.edge() - 1
        p = env.alerts(Ea, obs_end)
        assert p, f"CHK-016: o_alert pulses expected after the integrity error ({kind}), got none"
        assert p[0] <= Ea + 16, f"CHK-016: first pulse expected at or before Ea+16={Ea + 16}, got {p[0]}"
        for a, b in zip(p, p[1:]):
            assert b - a <= 32, f"CHK-016: 32 edges without o_alert pulse between {a} and {b} ({kind})"
        assert obs_end - p[-1] < 32, (f"CHK-016: no o_alert pulse in the last {obs_end - p[-1]} "
                                      f"edges before reset ({kind})")
        rs = env.edge()
        await env.reset(10)
        for U in range(rs, env.edge()):
            s = env.hist.get(U)
            if s is not None and s[H_RST] == 0:
                assert s[H_ALERT] == 0, f"CHK-016: o_alert=0 expected while rst_ni=0, got 1 at edge {U}"
        t1 = env.edge()
        await env.idle(20)
        await check_all_reset_values(env)
        await normal_traffic(env, max(1, t1 + 256 - env.edge()))
        p = env.alerts(t1, env.edge() - 1)
        assert not p, f"CHK-016: no o_alert expected after reset release, got {p}"
    env.finish()


# ================================================================ filter
@cocotb.test()
async def test_chk_017_input_filter(dut):
    """CHK-017: input noise filter on DATA_IN and interrupt detection, per bit."""
    env = await setup(dut, "CHK-017")
    for i in BITS4:
        j = i ^ 1
        bi, bj = 1 << i, 1 << j
        await env.set_gpio(0)
        await env.idle(30)
        await env.wr(CTRL_EN_INPUT_FILTER, bi)
        await env.wr(INTR_CTRL_EN_RISING, bi | bj)
        await env.wr(INTR_CTRL_EN_FALLING, bi | bj)
        await env.wr(INTR_CTRL_EN_LVLHIGH, 0)
        await env.wr(INTR_CTRL_EN_LVLLOW, 0)
        await env.wr(INTR_ENABLE, bi | bj)
        await env.idle(24)
        await env.wr(INTR_STATE, M)
        await env.idle(2)
        # step 2: 12-cycle pulse on bits i and j
        box = []
        cocotb.start_soon(env.gpio_pulse(bi | bj, 0, 12, box))
        polls = []
        for _ in range(200):
            r = await env.host.read(DATA_IN)
            polls.append(r)
            if box and env.edge() > box[0] + 50:
                break
        assert box, "CHK-017: test bench pulse did not start"
        E0 = box[0]
        st = await env.rd(INTR_STATE, what=" (after short pulse)")
        inwin = 0
        for r in polls:
            assert r.d_error == 0, f"CHK-017: DATA_IN poll expected d_error=0 got {r.d_error}"
            assert r.d_data is not None and (r.d_data >> i) & 1 == 0, (
                f"CHK-017: DATA_IN[{i}] (filter on) expected 0 for a 12-cycle pulse, got "
                f"{hx(r.d_data)} accepted at {r.a_edge} (E0={E0})")
            if E0 + 4 <= r.a_edge <= E0 + 11:
                inwin += 1
                assert (r.d_data >> j) & 1 == 1, (
                    f"CHK-017: DATA_IN[{j}] (filter off) expected 1 for poll accepted at {r.a_edge} "
                    f"(E0={E0}), got {hx(r.d_data)}")
        assert inwin > 0, f"CHK-017: no DATA_IN poll accepted in E0+4..E0+11 (E0={E0})"
        assert st.a_edge >= E0 + 8 and st.d_data is not None and (st.d_data >> i) & 1 == 0 \
            and (st.d_data >> j) & 1 == 1, (
            f"CHK-017: INTR_STATE expected bit {i}=0 and bit {j}=1 after pulse, got {hx(st.d_data)}")
        env.check_hist(E0, None, H_INTR, lambda v: (v >> i) & 1 == 0,
                       f"o_intr_gpio[{i}] must stay 0 for a filtered pulse")
        await env.wr(INTR_STATE, M)
        await env.idle(2)
        # step 3: long change on bit i
        E1 = await env.set_gpio(bi)
        await env.wait_edge(E1 + 24)
        r = await env.rd(DATA_IN, what=" (long change)")
        assert r.a_edge >= E1 + 24 and r.d_data is not None and (r.d_data >> i) & 1 == 1, (
            f"CHK-017: DATA_IN[{i}] expected 1 at/after E1+24 (E1={E1}), got {hx(r.d_data)} at {r.a_edge}")
        await env.wait_edge(E1 + 28)
        s = await env.rd(INTR_STATE, what=" (long change)")
        assert s.a_edge >= E1 + 28 and s.d_data is not None and (s.d_data >> i) & 1 == 1, (
            f"CHK-017: INTR_STATE[{i}] expected 1 at/after E1+28, got {hx(s.d_data)} at {s.a_edge}")
        await env.wait_edge(E1 + 40)
        await env.set_gpio(0)
        await env.idle(40)
        env.check_hist(E1 + 30, None, H_INTR, lambda v: (v >> i) & 1 == 1,
                       f"o_intr_gpio[{i}] expected 1 from E1+30 (E1={E1})")
        await env.wr(INTR_STATE, M)
    await env.wr(CTRL_EN_INPUT_FILTER, 0)
    env.finish()


# ================================================================ gpio outputs
@cocotb.test()
async def test_chk_018_direct_out(dut):
    """CHK-018: DIRECT_OUT writes and reads all 32 bits of DATA_OUT; o_gpio follows."""
    env = await setup(dut, "CHK-018")
    vals = [1 << k for k in range(32)] + [M, 0] + [env.r.getrandbits(32) for _ in range(50)]
    for V in vals:
        w = await env.wr(DIRECT_OUT, V)
        await env.rd(DIRECT_OUT, V, what=" (DIRECT_OUT)")
        await env.rd(MASKED_OUT_LOWER, V & 0xFFFF, what=" (MASKED_OUT_LOWER)")
        await env.rd(MASKED_OUT_UPPER, V >> 16, what=" (MASKED_OUT_UPPER)")
        env.hist_eq(w.d_edge + 2, None, H_GPIO, V, "o_gpio must equal DIRECT_OUT from D+2")
    env.finish()


async def check_out_view(env, w):
    m = env.model
    await env.rd(DIRECT_OUT, m.out, what=" (DIRECT_OUT)")
    await env.rd(MASKED_OUT_LOWER, m.out & 0xFFFF, what=" (MASKED_OUT_LOWER)")
    await env.rd(MASKED_OUT_UPPER, m.out >> 16, what=" (MASKED_OUT_UPPER)")
    env.hist_eq(w.d_edge + 2, None, H_GPIO, m.out, "o_gpio must equal expected DATA_OUT from D+2")


async def check_oe_view(env, w):
    m = env.model
    await env.rd(DIRECT_OE, m.oe, what=" (DIRECT_OE)")
    await env.rd(MASKED_OE_LOWER, m.oe & 0xFFFF, 0xFFFF, what=" (MASKED_OE_LOWER)")
    await env.rd(MASKED_OE_UPPER, m.oe >> 16, 0xFFFF, what=" (MASKED_OE_UPPER)")
    env.hist_eq(w.d_edge + 2, None, H_OE, m.oe, "o_gpio_en must equal expected DATA_OE from D+2")


@cocotb.test()
async def test_chk_019_masked_out(dut):
    """CHK-019: masked writes of DATA_OUT through MASKED_OUT_LOWER / MASKED_OUT_UPPER."""
    env = await setup(dut, "CHK-019")
    w = await env.wr(DIRECT_OUT, 0x12345678)
    await check_out_view(env, w)
    w = await env.wr(MASKED_OUT_LOWER, 0x00FFABCD)
    assert env.model.out == 0x123456CD
    await env.rd(DIRECT_OUT, 0x123456CD, what=" (after step 2)")
    await check_out_view(env, w)
    w = await env.wr(MASKED_OUT_UPPER, 0xF0F0FFFF)
    await env.rd(DIRECT_OUT, 0xF2F456CD, what=" (after step 3)")
    await check_out_view(env, w)
    w = await env.wr(MASKED_OUT_LOWER, 0x0000FFFF)
    await check_out_view(env, w)
    w = await env.wr(MASKED_OUT_UPPER, 0x00000000)
    await env.rd(DIRECT_OUT, 0xF2F456CD, what=" (after mask-0 writes)")
    await env.rd(MASKED_OUT_LOWER, 0x000056CD, what=" (after mask-0 writes)")
    await env.rd(MASKED_OUT_UPPER, 0x0000F2F4, what=" (after mask-0 writes)")
    await check_out_view(env, w)
    for _ in range(100):
        a = env.r.choice((MASKED_OUT_LOWER, MASKED_OUT_UPPER))
        w = await env.wr(a, env.r.getrandbits(32))
        await check_out_view(env, w)
    env.finish()


@cocotb.test()
async def test_chk_020_data_oe(dut):
    """CHK-020: DATA_OE direct and masked writes, reads and o_gpio_en."""
    env = await setup(dut, "CHK-020")
    t0 = env.edge()
    vals = [1 << k for k in range(32)] + [M, 0] + [env.r.getrandbits(32) for _ in range(30)]
    for V in vals:
        w = await env.wr(DIRECT_OE, V)
        await check_oe_view(env, w)
    w = await env.wr(DIRECT_OE, 0x12345678)
    await check_oe_view(env, w)
    w = await env.wr(MASKED_OE_LOWER, 0x00FFABCD)
    await env.rd(DIRECT_OE, 0x123456CD, what=" (after MASKED_OE_LOWER)")
    await check_oe_view(env, w)
    w = await env.wr(MASKED_OE_UPPER, 0xF0F0FFFF)
    await env.rd(DIRECT_OE, 0xF2F456CD, what=" (after MASKED_OE_UPPER)")
    await check_oe_view(env, w)
    w = await env.wr(MASKED_OE_LOWER, 0x0000FFFF)
    w = await env.wr(MASKED_OE_UPPER, 0x00000000)
    await env.rd(DIRECT_OE, 0xF2F456CD, what=" (after mask-0 writes)")
    await check_oe_view(env, w)
    for _ in range(100):
        a = env.r.choice((MASKED_OE_LOWER, MASKED_OE_UPPER))
        w = await env.wr(a, env.r.getrandbits(32))
        await check_oe_view(env, w)
    env.hist_eq(t0, None, H_GPIO, 0, "o_gpio must not be affected by DATA_OE writes")
    env.finish()


@cocotb.test()
async def test_chk_021_data_in_follows_input(dut):
    """CHK-021: DATA_IN with filter off follows i_gpio only (this run's GpioAsyncOn)."""
    env = await setup(dut, "CHK-021")
    await env.wr(CTRL_EN_INPUT_FILTER, 0)
    for oe in (M, 0):
        await env.wr(DIRECT_OE, oe)
        vals = ([1 << k for k in range(32)] + [(~(1 << k)) & M for k in range(32)]
                + [env.r.getrandbits(32) for _ in range(100)])
        for V in vals:
            await env.wr(DIRECT_OUT, (~V) & M)
            E0 = await env.set_gpio(V)
            await env.wait_edge(E0 + 4)
            r = await env.rd(DATA_IN, V, what=f" (DATA_IN must be i_gpio, not DATA_OUT; OE={hx(oe)})")
            assert r.a_edge >= E0 + 4
            for i in BITS4:
                await env.rd(PP_IO(i), (((V >> i) & 1) << 8) | (((~V) >> i) & 1),
                             what=f" (PER_PIN_IO_{i})")
            await env.wait_edge(E0 + 8)
    env.finish()


# ================================================================ interrupts
async def intr_clean(env, gpio):
    for a in (INTR_CTRL_EN_RISING, INTR_CTRL_EN_FALLING, INTR_CTRL_EN_LVLHIGH,
              INTR_CTRL_EN_LVLLOW, CTRL_EN_INPUT_FILTER, INTR_ENABLE):
        await env.wr(a, 0)
    E = await env.set_gpio(gpio)
    await env.wait_edge(E + 10)
    await env.wr(INTR_STATE, M)
    await env.idle(2)


async def edge_case(env, i, rising):
    b = 1 << i
    start, act = (0, b) if rising else (b, 0)
    reg = INTR_CTRL_EN_RISING if rising else INTR_CTRL_EN_FALLING
    nm = "rising" if rising else "falling"
    await intr_clean(env, start)
    await env.wr(reg, b)
    await env.wr(INTR_ENABLE, b)
    E0 = await env.set_gpio(act)
    await env.wait_edge(E0 + 8)
    s = await env.rd(INTR_STATE, b, what=f" ({nm} edge bit {i})")
    assert s.a_edge >= E0 + 8
    await env.wait_edge(E0 + 20)
    env.hist_eq(E0 + 10, None, H_INTR, b, f"o_intr_gpio after {nm} edge on bit {i} from E0+10")
    t = env.edge()
    E = await env.set_gpio(start)
    await env.wait_edge(E + 20)
    await env.rd(INTR_STATE, b, what=f" (still latched after opposite edge, bit {i})")
    env.check_hist(t, None, H_INTR, lambda v: (v >> i) & 1 == 1,
                   f"o_intr_gpio[{i}] must stay 1 (not cleared by hardware)")
    await env.wr(INTR_STATE, (~b) & M)
    await env.rd(INTR_STATE, b, what=f" (W1C of ~bit {i})")
    w = await env.wr(INTR_STATE, b)
    await env.rd(INTR_STATE, 0, what=f" (W1C of bit {i})")
    await env.idle(4)
    env.hist_eq(w.d_edge + 2, None, H_INTR, 0, "o_intr_gpio must be 0 from D+2 after W1C")
    # opposite edge alone must not set the interrupt
    E = await env.set_gpio(act)
    await env.wait_edge(E + 12)
    await env.rd(INTR_STATE, b, what=f" ({nm} edge again, bit {i})")
    await env.wr(INTR_STATE, b)
    E = await env.set_gpio(start)
    await env.wait_edge(E + 20)
    await env.rd(INTR_STATE, 0, what=f" (opposite edge alone must not set bit {i}, {nm} mode)")


@cocotb.test()
async def test_chk_022_edge_interrupts(dut):
    """CHK-022: edge interrupts rising/falling/both; latching, W1C, raw INTR_STATE."""
    env = await setup(dut, "CHK-022")
    bits = list(BITS4) + env.r.sample([k for k in range(32) if k not in BITS4], 4)
    for i in bits:
        b = 1 << i
        await edge_case(env, i, True)
        await edge_case(env, i, False)
        # both edges
        await intr_clean(env, 0)
        await env.wr(INTR_CTRL_EN_RISING, b)
        await env.wr(INTR_CTRL_EN_FALLING, b)
        await env.wr(INTR_ENABLE, b)
        E = await env.set_gpio(b)
        await env.wait_edge(E + 8)
        s1 = await env.rd(INTR_STATE, b, what=f" (both, rising, bit {i})")
        await env.wr(INTR_STATE, b)
        await env.rd(INTR_STATE, 0, what=f" (both, after W1C, bit {i})")
        E = await env.set_gpio(0)
        await env.wait_edge(E + 8)
        s2 = await env.rd(INTR_STATE, b, what=f" (both, falling, bit {i})")
        assert s1.d_data == s2.d_data, (f"CHK-022: INTR_STATE must be identical for both edges, "
                                        f"got {hx(s1.d_data)} and {hx(s2.d_data)}")
        await env.wr(INTR_STATE, b)
        # raw state
        E = await env.set_gpio(b)
        await env.wait_edge(E + 8)
        await env.rd(INTR_STATE, b, what=f" (raw state event, bit {i})")
        w = await env.wr(INTR_ENABLE, 0)
        await env.rd(INTR_STATE, b, b, what=f" (raw, not masked by INTR_ENABLE, bit {i})")
        await env.idle(4)
        env.check_hist(w.d_edge + 2, None, H_INTR, lambda v: (v >> i) & 1 == 0,
                       f"o_intr_gpio[{i}] must be 0 from D+2 after INTR_ENABLE=0")
    env.finish()


async def level_case(env, i, high):
    b = 1 << i
    start, act = (0, b) if high else (b, 0)
    nm = "LVLHIGH" if high else "LVLLOW"
    await intr_clean(env, start)
    await env.wr(INTR_CTRL_EN_LVLHIGH if high else INTR_CTRL_EN_LVLLOW, b)
    await env.wr(INTR_STATE, M)
    await env.wr(INTR_ENABLE, b)
    E0 = await env.set_gpio(act)
    await env.wait_edge(E0 + 8)
    s = await env.rd(INTR_STATE, b, what=f" ({nm} bit {i})")
    assert s.a_edge >= E0 + 8
    await env.wait_edge(E0 + 12)
    env.check_hist(E0 + 10, None, H_INTR, lambda v: (v >> i) & 1 == 1,
                   f"o_intr_gpio[{i}] expected 1 from E0+10 ({nm})")
    w = await env.wr(INTR_STATE, b)
    await env.wait_edge(w.d_edge + 4)
    await env.rd(INTR_STATE, b, b, what=f" (W1C while {nm} holds, bit {i})")
    await env.idle(8)
    env.check_hist(w.d_edge + 4, None, H_INTR, lambda v: (v >> i) & 1 == 1,
                   f"o_intr_gpio[{i}] expected 1 from D+4 after W1C while level holds")
    E = await env.set_gpio(start)
    await env.wait_edge(E + 8)
    w2 = await env.wr(INTR_STATE, b)
    await env.rd(INTR_STATE, 0, what=f" (level removed and W1C, bit {i})")
    await env.wait_edge(w2.d_edge + 2 + 64 + 1)
    env.check_hist(w2.d_edge + 2, w2.d_edge + 2 + 64, H_INTR, lambda v: (v >> i) & 1 == 0,
                   f"o_intr_gpio[{i}] expected 0 for 64 cycles after level removed and W1C")


@cocotb.test()
async def test_chk_023_level_interrupts(dut):
    """CHK-023: level interrupts high/low, and W1C while the level holds."""
    env = await setup(dut, "CHK-023")
    for i in BITS4:
        await level_case(env, i, True)
        await level_case(env, i, False)
    env.finish()


@cocotb.test()
async def test_chk_024_intr_test_and_enable(dut):
    """CHK-024: INTR_TEST forcing and INTR_ENABLE masking per bit."""
    env = await setup(dut, "CHK-024")
    G = env.r.getrandbits(32)
    E = await env.set_gpio(G)
    await env.wait_edge(E + 10)
    await env.wr(INTR_ENABLE, M)
    w = await env.wr(INTR_TEST, 0x80010001)
    await env.rd(INTR_STATE, 0x80010001, what=" (after INTR_TEST)")
    await env.rd(INTR_TEST, 0, what=" (INTR_TEST is wo)")
    await env.idle(2)
    env.hist_eq(w.d_edge + 2, None, H_INTR, 0x80010001, "o_intr_gpio after INTR_TEST from D+2")
    w = await env.wr(INTR_ENABLE, 0x00000001)
    await env.rd(INTR_STATE, 0x80010001, what=" (raw after masking)")
    await env.idle(2)
    env.hist_eq(w.d_edge + 2, None, H_INTR, 0x00000001, "o_intr_gpio masked by INTR_ENABLE from D+2")
    w = await env.wr(INTR_STATE, M)
    await env.rd(INTR_STATE, 0, what=" (after W1C all)")
    await env.idle(2)
    env.hist_eq(w.d_edge + 2, None, H_INTR, 0, "o_intr_gpio after W1C all from D+2")
    w = await env.wr(INTR_ENABLE, 0)
    await env.wr(INTR_CTRL_EN_RISING, M)
    await env.wr(INTR_CTRL_EN_FALLING, M)
    env.model.state = None
    t = env.edge()
    for _ in range(60):
        if env.edge() >= t + 200:
            break
        E = await env.set_gpio(env.r.getrandbits(32))
        await env.wait_edge(E + env.r.randint(8, 12))
    env.hist_eq(w.d_edge + 2, None, H_INTR, 0, "o_intr_gpio must stay 0 with INTR_ENABLE=0")
    await env.wr(INTR_CTRL_EN_RISING, 0)
    await env.wr(INTR_CTRL_EN_FALLING, 0)
    await env.idle(16)
    await env.wr(INTR_STATE, M)
    w = await env.wr(INTR_ENABLE, M)
    await env.wait_edge(w.d_edge + 16)
    env.hist_eq(w.d_edge + 4, None, H_INTR, 0, "o_intr_gpio expected 0 from D+4 after re-enable")
    env.finish()


# ================================================================ per-pin views
@cocotb.test()
async def test_chk_025_per_pin_io(dut):
    """CHK-025: PER_PIN_IO_i aliases DATA_OUT[i] / DATA_IN[i] and affects only GPIO i."""
    G = 0x6B2D94C1
    env = await setup(dut, "CHK-025", gpio=G)
    await env.idle(20)
    R0 = env.r.getrandbits(32)
    EN0 = env.r.getrandbits(32)
    await env.wr(DIRECT_OE, R0)
    await env.wr(INTR_ENABLE, EN0)
    for i in range(32):
        for P in (env.r.getrandbits(32), 0, M):
            await env.wr(DIRECT_OUT, P)
            d = 0 if (P >> i) & 1 else 1
            w = await env.wr(PP_IO(i), d)
            exp = P ^ (1 << i)
            assert env.model.out == exp
            await env.rd(DIRECT_OUT, exp, what=f" (after PER_PIN_IO_{i} write)")
            await env.rd(DIRECT_OE, R0, what=" (DIRECT_OE unchanged)")
            await env.rd(INTR_ENABLE, EN0, what=" (INTR_ENABLE unchanged)")
            for jj in (i, (i + 1) % 32):
                await env.rd(PP_IO(jj), (((G >> jj) & 1) << 8) | ((exp >> jj) & 1),
                             what=f" (PER_PIN_IO_{jj})")
            env.hist_eq(w.d_edge + 2, None, H_GPIO, exp, f"o_gpio after PER_PIN_IO_{i} write")
            n2 = exp ^ (1 << i)
            await env.wr(DIRECT_OUT, n2)
            await env.rd(PP_IO(i), (((G >> i) & 1) << 8) | ((n2 >> i) & 1),
                         what=f" (PER_PIN_IO_{i} after DIRECT_OUT write)")
    env.finish()


@cocotb.test()
async def test_chk_026_per_pin_cfg(dut):
    """CHK-026: PER_PIN_OE_i / PER_PIN_INTR_CTRL_i alias their bit and affect only GPIO i."""
    env = await setup(dut, "CHK-026", gpio=0)
    G = env.r.getrandbits(32)
    E = await env.set_gpio(G)
    await env.wait_edge(E + 8)
    env.model.state = None
    for i in range(32):
        R = env.r.getrandbits(32)
        await env.wr(DIRECT_OE, R)
        bit = ((~R) >> i) & 1
        w = await env.wr(PP_OE(i), bit)
        exp = R ^ (1 << i)
        await env.rd(DIRECT_OE, exp, what=f" (after PER_PIN_OE_{i} write)")
        await env.rd(PP_OE(i), bit, what=f" (PER_PIN_OE_{i})")
        env.hist_eq(w.d_edge + 2, None, H_OE, exp, f"o_gpio_en after PER_PIN_OE_{i} write")
        for a in CTRL_REGS:
            await env.wr(a, env.r.getrandbits(32))
        for v in (0x01, 0x02, 0x04, 0x08, 0x10, 0x1F, 0x00):
            await env.wr(PP_IC(i), v)
            for k in range(5):
                assert (env.model.ctrl[k] >> i) & 1 == (v >> k) & 1
            await env.idle(24)
            for a in CTRL_REGS:
                await env.rdm(a, what=f" (after PER_PIN_INTR_CTRL_{i}={v:#x})")
        for a in CTRL_REGS:
            await env.wr(a, env.r.getrandbits(32))
        await env.rdm(PP_IC(i), what=f" (PER_PIN_INTR_CTRL_{i} view)")
        await env.rdm(PP_OE(i), what=f" (PER_PIN_OE_{i} view)")
    env.finish()


@cocotb.test()
async def test_chk_027_no_per_pin_intr(dut):
    """CHK-027: writes to the per-pin ranges never change INTR_STATE/INTR_ENABLE/INTR_TEST."""
    env = await setup(dut, "CHK-027", gpio=0)
    t0 = env.edge()
    await env.wr(INTR_ENABLE, M)
    for i in BITS4:
        await env.wr(PP_IO(i), M)
        await env.wr(PP_OE(i), M)
        await env.wr(PP_IC(i), 0x00000001)
    await env.idle(8)
    await env.rd(INTR_STATE, 0, what=" (INTR_STATE)")
    await env.rd(INTR_ENABLE, M, what=" (INTR_ENABLE)")
    await env.rd(INTR_TEST, 0, what=" (INTR_TEST)")
    env.hist_eq(t0, None, H_INTR, 0, "o_intr_gpio must stay 0")
    env.finish()


# ================================================================ registers
@cocotb.test()
async def test_chk_028_reset_values(dut):
    """CHK-028: reset values of every register."""
    G = 0xA5A55A5A
    env = await setup(dut, "CHK-028", gpio=G)
    rel = env.rel_edge
    await env.idle(20)
    await check_all_reset_values(env)
    env.hist_eq(rel, None, H_GPIO, 0, "o_gpio must be 0 after reset")
    env.hist_eq(rel, None, H_OE, 0, "o_gpio_en must be 0 after reset")
    env.hist_eq(rel, None, H_INTR, 0, "o_intr_gpio must be 0 after reset")
    p = env.alerts(rel, env.edge() - 1)
    assert not p, f"CHK-028: o_alert must never pulse, got {p}"
    env.finish()


@cocotb.test()
async def test_chk_029_field_access_types(dut):
    """CHK-029: field access types rw, wo, ro, rw0c, reserved bits; RACL off."""
    G = 0x3C3CC3C3
    env = await setup(dut, "CHK-029", gpio=G)
    t0 = env.edge()
    for a in RW_REGS:
        for v in (M, 0, 0xA5A55A5A, 0x5A5AA5A5):
            await env.wr(a, v)
            await env.rd(a, v, what=" (rw readback)")
            if a == CTRL_EN_INPUT_FILTER:
                await env.idle(24)
                await env.rd(DATA_IN, G, what=f" (DATA_IN with filter {hx(v)})")
        await env.wr(a, 0)
        if a == CTRL_EN_INPUT_FILTER:
            await env.idle(24)
    await env.wr(INTR_TEST, 0)
    await env.rd(INTR_TEST, 0, what=" (INTR_TEST wo)")
    await env.wr(ALERT_TEST, 0xFFFFFFFE)
    await env.rd(ALERT_TEST, 0x80000000, what=" (ALERT_TEST wo/reserved/regwen)")
    for v in (M, 0):
        await env.wr(DATA_IN, v, err=None, update=False)
        await env.rd(DATA_IN, G, what=" (DATA_IN ro)")
    b40 = await env.rd(HW_STRAPS_DATA_IN_VALID)
    b44 = await env.rd(HW_STRAPS_DATA_IN)
    await env.wr(HW_STRAPS_DATA_IN_VALID, M, err=None, update=False)
    await env.wr(HW_STRAPS_DATA_IN, M, err=None, update=False)
    if env.straps_on:
        assert b40.d_data is not None
        await env.rd(HW_STRAPS_DATA_IN_VALID, b40.d_data, what=" (ro, unchanged)")
    else:
        await env.rd(HW_STRAPS_DATA_IN, 0, what=" (straps disabled)")
    assert b44.d_data is not None
    await env.rd(HW_STRAPS_DATA_IN, b44.d_data, what=" (ro, unchanged)")
    for i in BITS4:
        await env.wr(PP_IO(i), M)
        await env.wr(PP_OE(i), M)
        await env.wr(PP_IC(i), M)
    await env.idle(24)
    for i in BITS4:
        await env.rd(PP_IO(i), (((G >> i) & 1) << 8) | 1, what=f" (PER_PIN_IO_{i})")
        await env.rd(PP_OE(i), 1, what=f" (PER_PIN_OE_{i})")
        await env.rd(PP_IC(i), 0x1F, what=f" (PER_PIN_INTR_CTRL_{i})")
    await env.wr(MASKED_OUT_LOWER, M)
    await env.rd(MASKED_OUT_LOWER, 0x0000FFFF, what=" (mask field wo)")
    p = env.alerts(t0, env.edge() - 1)
    assert not p, f"CHK-029: no o_alert pulse expected, got {p}"
    env.finish()


# ================================================================ reset
@cocotb.test()
async def test_chk_030_async_short_reset(dut):
    """CHK-030: asynchronous reset assertion, 2-cycle reset, discarding a pending response."""
    env = await setup(dut, "CHK-030")
    d = dut
    for a in (DIRECT_OUT, DIRECT_OE, INTR_ENABLE, INTR_TEST):
        await env.wr(a, M)
    env.host.hold_d = True
    req = env.host.issue(OP_GET, DIRECT_OUT)
    for _ in range(60):
        if req.accepted and val(d.o_d_valid) == 1:
            break
        await FallingEdge(env.clk)
    assert req.accepted and val(d.o_d_valid) == 1, "CHK-030: pending response (o_d_valid=1) not reached"
    env.host.quiet = True
    await RisingEdge(env.clk)
    await Timer(max(1, env.period // 4), "step")
    d.rst_ni.value = 0
    env.host.hold_d = False
    await FallingEdge(env.clk)
    await ReadOnly()
    for nm in ("o_gpio", "o_gpio_en", "o_intr_gpio", "o_d_valid", "o_alert", "o_alert_integ_fail"):
        v = val(getattr(d, nm))
        assert v == 0, f"CHK-030: {nm} must be 0 at the first falling edge after rst_ni fell, got {hx(v)}"
    await RisingEdge(env.clk)
    await RisingEdge(env.clk)
    await FallingEdge(env.clk)
    d.rst_ni.value = 1
    await FallingEdge(env.clk)
    env.host.clear()
    env.model.reset()
    t = env.edge()
    await env.idle(20)
    dv = [U for U in range(t - 1, env.edge()) if env.hist.get(U) and env.hist[U][H_DV] == 1]
    assert not dv, f"CHK-030: pending response must be discarded, got o_d_valid at edges {dv}"
    env.host.quiet = False
    await env.idle(1)
    for a in (DIRECT_OUT, DIRECT_OE, INTR_ENABLE, INTR_STATE):
        await env.rd(a, 0, what=" (after short reset)")
    await env.wr(DIRECT_OUT, 0x5A5A1234)
    await env.rd(DIRECT_OUT, 0x5A5A1234, what=" (normal access after short reset)")
    env.finish()


# ================================================================ straps
async def strap_sequence(env, S, check_on):
    d = env.dut
    # NNC verification fix (fix-verif, triage B): every i_strap_en change goes through drive_sync, i.e. just after a rising edge when GpioAsyncOn=0 (CHK-011 rule (f)); Es is the first edge with i_strap_en=1.
    await env.drive_sync("i_strap_en", 0)
    await env.reset(10)
    await env.idle(10)
    await env.wr(DIRECT_OE, M)
    await env.wr(DIRECT_OUT, 0x0F0F0F0F)
    Eg = await env.set_gpio(S)
    await env.wait_edge(Eg + 26)
    if check_on:
        await env.rd(HW_STRAPS_DATA_IN_VALID, 0, what=" (before strap_en)")
    else:
        await env.rd(HW_STRAPS_DATA_IN, 0, what=" (straps disabled, before strap_en)")
    await env.wait_edge(Eg + 26)
    Es = await env.drive_sync("i_strap_en", 1)
    if check_on:
        env.hist_eq(env.rel_edge, Es - 1, H_SV, 0, "o_straps_valid must be 0 before the trigger")
    await env.wait_edge(Es + 4)
    if check_on:
        await env.rd(HW_STRAPS_DATA_IN_VALID, 1, what=" (after strap_en)")
        await env.rd(HW_STRAPS_DATA_IN, S, what=" (sampled straps)")
    else:
        await env.rd(HW_STRAPS_DATA_IN, 0, what=" (straps disabled, after strap_en)")
    await env.wait_edge(Es + 9)
    if check_on:
        env.hist_eq(Es + 4, None, H_SV, 1, "o_straps_valid from Es+4")
        env.hist_eq(Es + 4, None, H_SD, S, "o_straps_data from Es+4")
    se = 1
    for _ in range(5):
        await env.set_gpio(env.r.getrandbits(32))
        await env.idle(env.r.randint(15, 30))
        se ^= 1
        await env.drive_sync("i_strap_en", se)
        await env.idle(env.r.randint(5, 15))
    if check_on:
        await env.rd(HW_STRAPS_DATA_IN_VALID, 1, what=" (frozen)")
        await env.rd(HW_STRAPS_DATA_IN, S, what=" (frozen)")
        env.hist_eq(Es + 4, None, H_SV, 1, "o_straps_valid must stay 1")
        env.hist_eq(Es + 4, None, H_SD, S, "o_straps_data must stay frozen")
    else:
        await env.rd(HW_STRAPS_DATA_IN, 0, what=" (straps disabled, after toggles)")
    await env.drive_sync("i_strap_en", 0)


@cocotb.test()
async def test_chk_031_strap_sampling(dut):
    """CHK-031: strap sampling with GpioAsHwStrapsEn=1, once per reset, regardless of OE."""
    if param("GpioAsHwStrapsEn", 1) != 1:
        start_clock(dut)
        not_verifiable(dut, "CHK-031", "GpioAsHwStrapsEn=0 in this run: strap sampling is absent")
        return
    env = await setup(dut, "CHK-031")
    for S in (0x3C5AA5C3, 0xC3A55A3C):
        await strap_sequence(env, S, True)
    env.finish()


@cocotb.test()
async def test_chk_032_straps_disabled(dut):
    """CHK-032: HW_STRAPS_DATA_IN reads zero when GpioAsHwStrapsEn=0."""
    if param("GpioAsHwStrapsEn", 1) != 0:
        start_clock(dut)
        not_verifiable(dut, "CHK-032", "GpioAsHwStrapsEn=1 in this run: straps-disabled behaviour absent")
        return
    env = await setup(dut, "CHK-032")
    await strap_sequence(env, 0x3C5AA5C3, False)
    env.finish()


# ================================================================ TL-UL
@cocotb.test()
async def test_chk_033_byte_writes(dut):
    """CHK-033: byte writes rejected on wide registers, accepted on PER_PIN_OE / PER_PIN_INTR_CTRL."""
    env = await setup(dut, "CHK-033", gpio=0)
    # LVLLOW preloaded to 0 (not 0x0F0F0F0F) so that, with i_gpio=0 constant, no event occurs.
    for a, v in ((DIRECT_OUT, 0x5555AAAA), (DIRECT_OE, 0xAAAA5555), (INTR_ENABLE, M),
                 (INTR_CTRL_EN_RISING, 0x0F0F0F0F), (INTR_CTRL_EN_FALLING, 0x0F0F0F0F),
                 (INTR_CTRL_EN_LVLHIGH, 0x0F0F0F0F), (INTR_CTRL_EN_LVLLOW, 0),
                 (CTRL_EN_INPUT_FILTER, 0)):
        await env.wr(a, v)
    await env.wr(INTR_TEST, 0x00000100)
    await env.idle(4)
    await env.rd(INTR_STATE, 0x100, what=" (preload)")
    t0 = env.edge()
    readlist = [INTR_STATE, INTR_ENABLE, INTR_TEST, DIRECT_OUT, MASKED_OUT_LOWER, MASKED_OUT_UPPER,
                DIRECT_OE, MASKED_OE_LOWER, MASKED_OE_UPPER] + list(CTRL_REGS) + [PP_IO(i) for i in BITS4]
    for a in list(WIDE_REGS) + [PP_IO(i) for i in BITS4]:
        await env.wr(a, 0x000000FF, err=1, opcode=OP_PUTP, size=0, amask=0x1, update=False,
                     what=" (byte write to register with fields above bit 7)")
        for b in readlist:
            await env.rdm(b, what=f" (after rejected byte write to 0x{a:03x})")
    await env.idle(2)
    env.hist_eq(t0, None, H_GPIO, 0x5555AAAA, "o_gpio unchanged by rejected byte writes")
    env.hist_eq(t0, None, H_OE, 0xAAAA5555, "o_gpio_en unchanged by rejected byte writes")
    env.hist_eq(t0, None, H_INTR, 0x00000100, "o_intr_gpio unchanged by rejected byte writes")
    env.model.state = None
    for i in BITS4:
        for dv in (0x01, 0x00):
            w = await env.wr(PP_OE(i), dv, opcode=OP_PUTP, size=0, amask=0x1,
                             what=f" (byte write PER_PIN_OE_{i})")
            assert (env.model.oe >> i) & 1 == dv
            await env.rdm(DIRECT_OE, what=f" (after byte PER_PIN_OE_{i}={dv})")
            await env.rdm(PP_OE(i), what=f" (PER_PIN_OE_{i})")
            env.hist_eq(w.d_edge + 2, None, H_OE, env.model.oe, f"o_gpio_en after byte PER_PIN_OE_{i}")
        for dv in (0x1F, 0x00):
            await env.wr(PP_IC(i), dv, opcode=OP_PUTP, size=0, amask=0x1,
                         what=f" (byte write PER_PIN_INTR_CTRL_{i})")
            for a in CTRL_REGS:
                await env.rdm(a, what=f" (after byte PER_PIN_INTR_CTRL_{i}={dv:#x})")
            await env.rdm(PP_IC(i), what=f" (PER_PIN_INTR_CTRL_{i})")
    env.finish()


@cocotb.test()
async def test_chk_034_subword_reads(dut):
    """CHK-034: sub-word reads return the full register in its byte lanes."""
    env = await setup(dut, "CHK-034")
    await env.wr(DIRECT_OUT, 0xF2F456CD)
    for size, addr, mask in ((0, 0x14, 0b0001), (0, 0x17, 0b1000), (1, 0x16, 0b1100), (1, 0x14, 0b0011)):
        r = await env.host.access(OP_GET, addr, 0, mask=mask, size=size)
        assert r.d_error == 0, f"CHK-034: sub-word read size={size} addr=0x{addr:x} expected d_error=0 got {r.d_error}"
        assert r.d_data == 0xF2F456CD, f"CHK-034: sub-word read size={size} addr=0x{addr:x} expected 0xf2f456cd got {hx(r.d_data)}"
        assert r.d_size == size, f"CHK-034: d_size expected {size} got {r.d_size}"
    env.finish()


@cocotb.test()
async def test_chk_035_protocol_errors(dut):
    """CHK-035: TL-UL protocol error cases answered with d_error=1, no effect."""
    env = await setup(dut, "CHK-035")
    await env.wr(DIRECT_OUT, 0)
    t0 = env.edge()
    for op in (2, 3, 5, 6, 7):
        r = await env.host.access(op, DIRECT_OUT, M, mask=0xF, size=2)
        assert r.d_error == 1, f"CHK-035: undefined opcode {op} expected d_error=1 got {r.d_error}"
        await env.rd(DIRECT_OUT, 0, what=f" (after opcode {op})")
    cases = (("b", OP_GET, 0x10, 0, 0xF, 3), ("c", OP_PUTF, 0x16, M, 0xF, 2),
             ("d", OP_GET, 0x15, 0, 0xF, 2), ("e", OP_PUTP, 0x14, M, 0x3, 0))
    for nm, op, addr, data, mask, size in cases:
        r = await env.host.access(op, addr, data, mask=mask, size=size)
        assert r.d_error == 1, f"CHK-035: case ({nm}) expected d_error=1 got {r.d_error}"
        assert r.d_size == size and r.d_source == r.source, (
            f"CHK-035: case ({nm}) expected d_size={size} d_source={r.source} got {r.d_size}/{r.d_source}")
        assert r.d_opcode == (1 if op == OP_GET else 0), f"CHK-035: case ({nm}) d_opcode echo got {r.d_opcode}"
        await env.rd(DIRECT_OUT, 0, what=f" (after case {nm})")
    env.hist_eq(t0, None, H_GPIO, 0, "o_gpio must stay 0")
    p = env.alerts(t0, env.edge() - 1)
    assert not p, f"CHK-035: no o_alert pulse expected, got {p}"
    env.finish()


@cocotb.test()
async def test_chk_036_unmapped(dut):
    """CHK-036: unmapped offsets return d_error=1 and change nothing."""
    G = rng("CHK-036-g").getrandbits(32)
    env = await setup(dut, "CHK-036", gpio=G)
    pre = ((INTR_ENABLE, 0), (DIRECT_OUT, 0x13579BDF), (DIRECT_OE, 0x2468ACE0),
           (INTR_CTRL_EN_RISING, 0x11223344), (INTR_CTRL_EN_FALLING, 0x55667788),
           (INTR_CTRL_EN_LVLHIGH, 0x99AABBCC), (INTR_CTRL_EN_LVLLOW, 0xDDEEFF01),
           (CTRL_EN_INPUT_FILTER, 0x0F1E2D3C))
    for a, v in pre:
        await env.wr(a, v)
    env.model.state = None
    await env.idle(24)
    t0 = env.edge()
    for a in UNMAPPED:
        r = await env.host.access(OP_GET, a, 0)
        assert r.d_error == 1, f"CHK-036: Get to unmapped 0x{a:03x} expected d_error=1 got {r.d_error}"
        r = await env.host.access(OP_PUTF, a, M)
        assert r.d_error == 1, f"CHK-036: PutFullData to unmapped 0x{a:03x} expected d_error=1 got {r.d_error}"
    for a in ALL_MAPPED:
        await env.rdm(a, what=" (after unmapped accesses)")
    env.hist_eq(t0, None, H_GPIO, env.model.out, "o_gpio unchanged")
    env.hist_eq(t0, None, H_OE, env.model.oe, "o_gpio_en unchanged")
    env.finish()


@cocotb.test()
async def test_chk_037_instr_fetch(dut):
    """CHK-037: instruction-fetch reads complete without side effects."""
    env = await setup(dut, "CHK-037")
    await env.wr(DIRECT_OUT, 0xCAFE0001)
    t0 = env.edge()
    for a in (DIRECT_OUT, DATA_IN):
        r = await env.host.access(OP_GET, a, 0, instr=1)
        assert r.done and r.d_source == r.source and r.d_size == 2 and r.d_opcode == 1, (
            f"CHK-037: instruction fetch to 0x{a:03x} expected response with d_source={r.source}, "
            f"d_size=2, d_opcode=1 got {r.d_source}/{r.d_size}/{r.d_opcode}")
    await env.idle(4)
    await env.rd(DIRECT_OUT, 0xCAFE0001, what=" (after instruction fetches)")
    env.hist_eq(t0, None, H_GPIO, 0xCAFE0001, "o_gpio unchanged")
    p = env.alerts(t0, env.edge() - 1)
    assert not p, f"CHK-037: no o_alert expected, got {p}"
    env.finish()


async def wait_all(env, items, limit):
    for _ in range(limit):
        if all(it[0].done for it in items):
            return
        await FallingEdge(env.clk)
    missing = [it[0] for it in items if not it[0].done][:3]
    assert False, f"{env.chk}: every request must get exactly one response; missing {missing}"


def check_items(env, items):
    for req, exp, mask, eerr in items:
        assert req.done, f"{env.chk}: request {req} got no response"
        if eerr is not None:
            assert req.d_error == eerr, f"{env.chk}: {req} expected d_error={eerr} got {req.d_error}"
        if exp is not None and req.d_error == 0:
            got = None if req.d_data is None else req.d_data & mask
            assert got == (exp & mask), (f"{env.chk}: {req} expected {hx(exp & mask)} (mask {hx(mask)}) "
                                         f"got {hx(got)}")


@cocotb.test()
async def test_chk_038_outstanding_backpressure(dut):
    """CHK-038: back-to-back requests and D-channel back-pressure; matching by d_source."""
    env = await setup(dut, "CHK-038")
    h = env.host
    h.bp = True
    h.a_gap_max = 0
    m = env.model
    m.state = None
    G = env.gpio
    r = env.r
    wr_addrs = [INTR_ENABLE, DIRECT_OUT, MASKED_OUT_LOWER, MASKED_OUT_UPPER, DIRECT_OE,
                MASKED_OE_LOWER, MASKED_OE_UPPER] + list(CTRL_REGS)
    rd_addrs = wr_addrs
    items = []
    for _ in range(500):
        if r.random() < 0.5:
            if r.random() < 0.8:
                a = r.choice(wr_addrs)
            else:
                a = r.choice((PP_IO(r.randrange(32)), PP_OE(r.randrange(32)), PP_IC(r.randrange(32))))
            dv = r.getrandbits(32)
            m.write(a, dv)
            items.append((h.issue(OP_PUTF, a, dv), None, M, 0))
        else:
            if r.random() < 0.8:
                a = r.choice(rd_addrs)
            else:
                a = r.choice((PP_IO(r.randrange(32)), PP_OE(r.randrange(32)), PP_IC(r.randrange(32))))
            exp, mask = m.read(a, G)
            if is_ppio(a):
                mask &= ~0x100  # data_in alias not checked while filter settings change
            items.append((h.issue(OP_GET, a), exp, mask, 0))
    await wait_all(env, items, 500 * 40)
    check_items(env, items)
    for s in (0x00, 0x01, 0x7F, 0xFF):
        assert s in h.used_sources, f"CHK-038: a_source 0x{s:02x} expected to be used"
    await env.idle(10)
    env.finish()


# ================================================================ regression
def gen_phase1(env, r):
    m = env.model
    G = env.gpio
    h = env.host
    wr_addrs = [INTR_ENABLE, DIRECT_OUT, MASKED_OUT_LOWER, MASKED_OUT_UPPER, DIRECT_OE,
                MASKED_OE_LOWER, MASKED_OE_UPPER, INTR_CTRL_EN_RISING, INTR_CTRL_EN_FALLING]
    k = r.random()
    if k < 0.30:
        if r.random() < 0.6:
            a = r.choice(wr_addrs)
        else:
            a = r.choice((PP_IO(r.randrange(32)), PP_OE(r.randrange(32)), PP_IC(r.randrange(32))))
        dv = r.getrandbits(32)
        if is_ppic(a):
            dv &= 0x3
        m.write(a, dv)
        return (h.issue(OP_PUTF, a, dv), None, M, 0)
    if k < 0.35:
        dv = r.getrandbits(32) & m.en
        m.write(INTR_TEST, dv)
        return (h.issue(OP_PUTF, INTR_TEST, dv), None, M, 0)
    if k < 0.40:
        dv = r.getrandbits(32)
        m.write(INTR_STATE, dv)
        return (h.issue(OP_PUTF, INTR_STATE, dv), None, M, 0)
    if k < 0.68:
        a = r.choice(ALL_MAPPED)
        e = m.read(a, G)
        exp, mask = e if e is not None else (None, M)
        return (h.issue(OP_GET, a), exp, mask, 0)
    if k < 0.76:
        a = r.choice(ALL_MAPPED)
        e = m.read(a, G)
        exp, mask = e if e is not None else (None, M)
        if r.random() < 0.5:
            off = r.randrange(4)
            return (h.issue(OP_GET, a + off, mask=1 << off, size=0), exp, mask, 0)
        off = r.choice((0, 2))
        return (h.issue(OP_GET, a + off, mask=0x3 << off, size=1), exp, mask, 0)
    if k < 0.82:
        i = r.randrange(32)
        if r.random() < 0.5:
            a, dv = PP_OE(i), r.randrange(2)
        else:
            a, dv = PP_IC(i), r.randrange(4)
        m.write(a, dv)
        return (h.issue(OP_PUTP, a, dv, mask=0x1, size=0), None, M, 0)
    if k < 0.87:
        a = r.choice(list(WIDE_REGS) + [PP_IO(r.randrange(32))])
        return (h.issue(OP_PUTP, a, r.getrandbits(8), mask=0x1, size=0), None, M, 1)
    if k < 0.96:
        a = r.choice(UNMAPPED)
        if r.random() < 0.5:
            return (h.issue(OP_GET, a), None, M, 1)
        return (h.issue(OP_PUTF, a, r.getrandbits(32)), None, M, 1)
    a = r.choice([x for x in ALL_MAPPED if x != ALERT_TEST])
    return (h.issue(r.choice((2, 3, 5, 6, 7)), a, r.getrandbits(32)), None, M, 1)


@cocotb.test()
async def test_regression_random(dut):
    """CHK-038, CHK-022, CHK-014, CHK-016, CHK-031 (and assertion traffic for CHK-001..CHK-013):
    broad legal random traffic with back-pressure, scored against the reference model."""
    r = rng("regression")
    G = r.getrandbits(32)
    env = await setup(dut, "CHK-038", gpio=G)
    h = env.host
    d = dut
    # phase 0: strap sampling
    if env.straps_on:
        env.chk = "CHK-031"
        await env.idle(30)
        # NNC verification fix (fix-verif, triage B): i_strap_en driven via drive_sync (just after a rising edge when GpioAsyncOn=0, CHK-011 rule (f)); Es is the first edge with i_strap_en=1.
        Es = await env.drive_sync("i_strap_en", 1)
        await env.wait_edge(Es + 4)
        await env.rd(HW_STRAPS_DATA_IN_VALID, 1, what=" (regression straps)")
        await env.rd(HW_STRAPS_DATA_IN, G, what=" (regression straps)")
        await env.wait_edge(Es + 9)
        await env.drive_sync("i_strap_en", 0)
        env.hist_eq(Es + 4, None, H_SV, 1, "o_straps_valid from Es+4")
        env.hist_eq(Es + 4, None, H_SD, G, "o_straps_data from Es+4")
        env.model.sv = 1
        env.model.sd = G
    # phase 1: random pipelined register traffic
    env.chk = "CHK-038"
    h.bp = True
    h.a_gap_max = 2
    items = [gen_phase1(env, r) for _ in range(1200)]
    await wait_all(env, items, 1200 * 40)
    check_items(env, items)
    await env.idle(6)
    m = env.model
    U = env.edge() - 1
    env.hist_eq(U - 2, U, H_GPIO, m.out, "o_gpio equals DATA_OUT model")
    env.hist_eq(U - 2, U, H_OE, m.oe, "o_gpio_en equals DATA_OE model")
    env.hist_eq(U - 2, U, H_INTR, m.state & m.en, "o_intr_gpio equals INTR_STATE & INTR_ENABLE")
    # phase 2: interrupt scoreboard with input changes
    env.chk = "CHK-022"
    h.a_gap_max = 0
    await env.wr(CTRL_EN_INPUT_FILTER, 0)
    env.model.state = None
    g = env.gpio
    for _ in range(5):
        rise = r.getrandbits(32)
        fall = r.getrandbits(32)
        hi = r.getrandbits(32) & r.getrandbits(32)
        lo = r.getrandbits(32) & r.getrandbits(32) & ~hi & M
        en = r.getrandbits(32)
        for a, v in ((INTR_CTRL_EN_RISING, rise), (INTR_CTRL_EN_FALLING, fall),
                     (INTR_CTRL_EN_LVLHIGH, hi), (INTR_CTRL_EN_LVLLOW, lo), (INTR_ENABLE, en)):
            await env.wr(a, v)

        def lvl(x, hi=hi, lo=lo):
            return ((hi & x) | (lo & ~x)) & M

        await env.idle(8)
        await env.wr(INTR_STATE, M)
        await env.idle(8)
        pred = lvl(g)
        await env.rd(INTR_STATE, pred, en, what=" (after clear, level bits)")
        env.hist_eq(env.edge() - 2, None, H_INTR, pred & en, "o_intr_gpio = INTR_STATE & INTR_ENABLE")
        for _ in range(6):
            g2 = g ^ (r.getrandbits(32) & r.getrandbits(32))
            E = await env.set_gpio(g2)
            await env.wait_edge(E + 12)
            pred = (pred | (rise & ~g & g2) | (fall & g & ~g2) | lvl(g2)) & M
            await env.rd(INTR_STATE, pred, en, what=" (after input change)")
            env.hist_eq(env.edge() - 2, None, H_INTR, pred & en, "o_intr_gpio = INTR_STATE & INTR_ENABLE")
            wv = r.getrandbits(32)
            ww = await env.wr(INTR_STATE, wv)
            pred = (pred & ~wv & M) | lvl(g2)
            await env.wait_edge(ww.d_edge + 6)
            await env.rd(INTR_STATE, pred, en, what=" (after random W1C)")
            env.hist_eq(ww.d_edge + 4, None, H_INTR, pred & en, "o_intr_gpio after W1C")
            g = g2
    for a in CTRL_REGS:
        await env.wr(a, 0)
    await env.wr(INTR_ENABLE, 0)
    # phase 3: alert test
    env.chk = "CHK-014"
    await env.idle(40)
    w = await env.wr(ALERT_TEST, 0x80000001)
    await env.idle(64)
    p = env.alerts(w.a_edge, env.edge() - 1)
    assert len(p) == 1 and p[0] <= w.d_edge + 16, (
        f"CHK-014: exactly one o_alert pulse no later than D+16={w.d_edge + 16} expected, got {p}")
    # phase 4: integrity error, then reset
    env.chk = "CHK-016"
    await env.idle(40)
    req = h.issue(OP_GET, DATA_IN, flip=1)
    for _ in range(60):
        if req.accepted:
            break
        await FallingEdge(env.clk)
    assert req.accepted, "CHK-016: flipped request not accepted"
    Ea = req.a_edge
    for _ in range(32):
        if req.done:
            break
        await FallingEdge(env.clk)
    await env.idle(128)
    end = env.edge() - 1
    p = env.alerts(Ea, end)
    assert p and p[0] <= Ea + 16, f"CHK-016: first o_alert pulse expected at or before Ea+16={Ea + 16}, got {p[:3]}"
    for a, b in zip(p, p[1:]):
        assert b - a <= 32, f"CHK-016: 32 edges without o_alert pulse between {a} and {b}"
    assert end - p[-1] < 32, "CHK-016: o_alert stopped repeating before reset"
    await env.reset(10)
    env.chk = "CHK-028"
    await env.idle(20)
    await env.rd(DIRECT_OUT, 0, what=" (after reset)")
    await env.rd(INTR_ENABLE, 0, what=" (after reset)")
    await env.rd(ALERT_TEST, 0x80000000, what=" (after reset)")
    t1 = env.edge()
    await env.idle(40)
    assert not env.alerts(t1, env.edge() - 1), "CHK-016: no o_alert expected after reset"
    env.finish()

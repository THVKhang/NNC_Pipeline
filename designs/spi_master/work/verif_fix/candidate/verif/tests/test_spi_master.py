"""cocotb testbench for m_spi_master: CHK-028..CHK-041 and a random regression.

All expected values are derived from the specification text (D = PARA_SPI_CLK_DIV).
"""
import random
from collections import deque

import cocotb
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer

try:
    from cocotb.utils import get_sim_time
except ImportError:  # pragma: no cover
    from cocotb.simtime import get_sim_time  # type: ignore

from nnc_cocotb import *  # noqa: F401,F403

MODES = [(0, 0), (0, 1), (1, 0), (1, 1)]
RST, CS, SCLK, MOSI, RDY, RV, RD, CPOL = range(8)


def clk_div():
    return int(PARAMS.get("PARA_SPI_CLK_DIV", 4))


def lg(D, mult):
    """Long wait of mult*16*D cycles, capped at 2*16*D when D > 16 (run time)."""
    return 16 * D * (mult if D <= 16 else min(mult, 2))


def hx(lst):
    return "[" + ", ".join(("0x%02x" % v) if isinstance(v, int) else str(v) for v in lst) + "]"


# --------------------------------------------------------------------------- transfer record
class Xfer:
    def __init__(self, A, d, last, start, cpol, cpha, D, idx):
        self.A = A
        self.d = d & 0xFF
        self.last = last & 1
        self.start = start
        self.cpol = cpol
        self.cpha = cpha
        self.idx = idx
        if cpha == 0:
            self.samp = {(2 * j + 1) * D: j for j in range(8)}
        else:
            self.samp = {(2 * j + 2) * D: j for j in range(8)}
        self.r = 0
        self.done = False
        self.aborted = False


# --------------------------------------------------------------------------- slave model
class Slave:
    """SPI slave driven only from o_sclk / o_cs_n (SPI-12-07, SPI-12-08)."""

    def __init__(self, env):
        self.env = env
        self.enabled = True
        self.sent = []
        self.rx = []
        self.preload = deque()
        self.rnd = random.Random(env.rnd.getrandbits(32))
        self.prev_cs = 1
        self.prev_sclk = None
        self.e = 0
        self.tx = None
        self.rxb = 0
        self.cpha = 0

    def _new(self):
        self.tx = self.preload.popleft() if self.preload else self.rnd.randrange(256)
        self.rxb = 0

    def _drive(self, bit):
        if self.tx is not None:
            self.env.dut.i_miso.value = (self.tx >> bit) & 1

    def _commit(self):
        self.sent.append(self.tx if self.tx is not None else 0)
        self.rx.append(self.rxb)

    async def run(self):
        dut = self.env.dut
        while True:
            await FallingEdge(dut.i_clk)
            cs = val(dut.o_cs_n)
            sclk = val(dut.o_sclk)
            rst = val(dut.i_rst_n)
            if not self.enabled or cs != 0 or rst != 1:
                self.tx = None
                self.e = 0
                self.prev_cs = cs
                self.prev_sclk = sclk
                continue
            if self.prev_cs != 0:
                self.e = 0
                self.rxb = 0
                b = self.env.burst
                self.cpha = b[1] if b is not None else (val(dut.i_cpha) or 0)
                if self.cpha == 0:
                    self._new()
                    self._drive(7)
                self.prev_cs = 0
                self.prev_sclk = sclk
                continue
            if sclk != self.prev_sclk:
                self.e += 1
                k = (self.e - 1) % 16 + 1
                mosi = val(dut.o_mosi) or 0
                if self.cpha == 0:
                    if k % 2 == 1:
                        self.rxb = ((self.rxb << 1) | mosi) & 0xFF
                        if k == 15:
                            self._commit()
                    elif k == 16:
                        self._new()
                        self._drive(7)
                    else:
                        self._drive(7 - k // 2)
                else:
                    if k % 2 == 1:
                        j = (k - 1) // 2
                        if j == 0:
                            self._new()
                        self._drive(7 - j)
                    else:
                        self.rxb = ((self.rxb << 1) | mosi) & 0xFF
                        if k == 16:
                            self._commit()
            self.prev_sclk = sclk


# --------------------------------------------------------------------------- command driver
class CmdDriver:
    """Requester. gap = number of cycles with o_cmd_ready=1 skipped before presenting
    (gap 0 = present right after the previous handshake, i_cmd_valid continuous)."""

    def __init__(self, env):
        self.env = env
        self.q = deque()
        self.active = False
        self.cur = None
        self.nxt = None
        self.gap_left = 0
        self.mode_done = True
        self.mark = 0
        self.rnd = random.Random(env.rnd.getrandbits(32))

    def push(self, data, last, gap=0, mode=None):
        self.q.append((data & 0xFF, last & 1, int(gap), mode))

    def go(self):
        self.active = True

    def idle(self):
        return self.cur is None and self.nxt is None and not self.q

    def stop(self):
        self.active = False
        self.q.clear()
        self.cur = None
        self.nxt = None

    def _idle_drive(self):
        dut = self.env.dut
        dut.i_cmd_valid.value = 0
        dut.i_cmd_data.value = self.rnd.randrange(256)
        dut.i_cmd_last.value = self.rnd.randrange(2)

    async def run(self):
        dut = self.env.dut
        while True:
            await FallingEdge(dut.i_clk)
            if not self.active:
                continue
            if val(dut.i_rst_n) != 1:
                dut.i_cmd_valid.value = 0
                continue
            if self.cur is not None:
                if len(self.env.cmd_hs) > self.mark:
                    self.cur = None
                else:
                    continue
            if self.nxt is None:
                if not self.q:
                    self._idle_drive()
                    continue
                self.nxt = self.q.popleft()
                self.gap_left = self.nxt[2]
                self.mode_done = self.nxt[3] is None
            data, last, _g, mode = self.nxt
            if not self.mode_done:
                if val(dut.o_cs_n) == 1:
                    dut.i_cpol.value = mode[0]
                    dut.i_cpha.value = mode[1]
                    self.mode_done = True
                else:
                    self._idle_drive()
                    continue
            if self.gap_left > 0:
                if val(dut.o_cmd_ready) == 1:
                    self.gap_left -= 1
                self._idle_drive()
                continue
            dut.i_cmd_valid.value = 1
            dut.i_cmd_data.value = data
            dut.i_cmd_last.value = last
            self.cur = self.nxt
            self.nxt = None
            self.mark = len(self.env.cmd_hs)


# --------------------------------------------------------------------------- response driver
class RspDriver:
    def __init__(self, env):
        self.env = env
        self.mode = "manual"
        self.p = 1.0
        self.rnd = random.Random(env.rnd.getrandbits(32))

    def set(self, mode, p=None):
        self.mode = mode
        if mode == "on":
            self.env.dut.i_rsp_ready.value = 1
        elif mode == "off":
            self.env.dut.i_rsp_ready.value = 0
        elif mode == "rand":
            self.p = p

    async def run(self):
        dut = self.env.dut
        while True:
            await FallingEdge(dut.i_clk)
            if self.mode == "rand":
                dut.i_rsp_ready.value = 1 if self.rnd.random() < self.p else 0


# --------------------------------------------------------------------------- environment / monitor
class Env:
    def __init__(self, dut, salt):
        self.dut = dut
        self.D = clk_div()
        self.rnd = rng(salt)
        self.edge = 0
        self.prev = None
        self.seen_reset = False
        self.cmd_hs = []
        self.rsp_hs = []
        self.cs_fall = []
        self.cs_rise = []
        self.toggles = []
        self.log = {}
        self.errors = []
        self.cov = set()
        self.refq = deque()
        self.cur = None
        self.burst = None
        self.mosi_exp = 0
        self.T = 0
        self.slave = Slave(self)
        self.cmd = CmdDriver(self)
        self.rsp = RspDriver(self)

    def start(self):
        for c in (self._edge_mon(), self._cyc_mon(), self.slave.run(), self.cmd.run(), self.rsp.run()):
            cocotb.start_soon(c)

    def err(self, chk, msg):
        if len(self.errors) < 100:
            self.errors.append(f"{chk}: {msg} (cycle starting at edge {self.edge})")

    def mark(self):
        return (len(self.cmd_hs), len(self.rsp_hs), len(self.slave.sent), len(self.slave.rx))

    def at(self, c, chk):
        s = self.log.get(c)
        assert s is not None, f"{chk}: sample of cycle {c} expected in the log got none (edge {self.edge})"
        return s

    def scoreboard(self, m, chk):
        cmds = [x.d for x in self.cmd_hs[m[0]:]]
        rx = self.slave.rx[m[3]:]
        sent = self.slave.sent[m[2]:]
        rsps = [d for _, d in self.rsp_hs[m[1]:]]
        assert rx == cmds, f"{chk}: MOSI monitor bytes expected {hx(cmds)} got {hx(rx)}"
        assert len(rsps) == len(cmds), \
            f"{chk}: response handshakes expected {len(cmds)} (= command handshakes) got {len(rsps)}"
        assert rsps == sent, f"{chk}: responses expected slave bytes {hx(sent)} got {hx(rsps)}"

    def finish(self):
        self.dut._log.info("coverage: " + ", ".join(sorted(str(c) for c in self.cov)))
        assert not self.errors, " | ".join(self.errors[:6])

    def _sample(self):
        d = self.dut
        return (val(d.i_rst_n), val(d.o_cs_n), val(d.o_sclk), val(d.o_mosi), val(d.o_cmd_ready),
                val(d.o_rsp_valid), val(d.o_rsp_data), val(d.i_cpol))

    def _clear(self):
        if self.cur is not None and not self.cur.done:
            self.cur.aborted = True
        self.cur = None
        self.refq.clear()
        self.burst = None
        self.mosi_exp = 0

    async def _edge_mon(self):
        while True:
            await RisingEdge(self.dut.i_clk)
            self.edge += 1
            self._on_edge(self.edge)

    async def _cyc_mon(self):
        while True:
            await FallingEdge(self.dut.i_clk)
            await ReadOnly()
            self._on_cycle(self.edge)

    def _on_edge(self, E):
        dut = self.dut
        D = self.D
        rst = val(dut.i_rst_n)
        if rst != 1:
            self._clear()
            return
        p = self.prev
        if not self.seen_reset or p is None:
            return
        if p[RST] != 1:
            p = (1, 1, p[CPOL], 0, 1, 0, 0, p[CPOL])
        if None in p:
            return
        cv = val(dut.i_cmd_valid)
        cd = val(dut.i_cmd_data)
        cl = val(dut.i_cmd_last)
        rr = val(dut.i_rsp_ready)
        mi = val(dut.i_miso)
        cpol = val(dut.i_cpol)
        cpha = val(dut.i_cpha)
        if p[RV] == 1 and rr == 1:
            self.rsp_hs.append((E, p[RD]))
            if self.refq:
                exp = self.refq.popleft()
                if exp != p[RD]:
                    self.err("CHK-020", f"response data expected 0x{exp:02x} got 0x{p[RD]:02x}")
            else:
                self.err("CHK-020", "response handshake expected none (model queue empty) got one")
        pushed = False
        x = self.cur
        if x is not None and not x.done:
            off = E - x.A
            j = x.samp.get(off)
            if j is not None:
                x.r |= ((mi or 0) & 1) << (7 - j)
            if off == 16 * D:
                x.done = True
                self.refq.append(x.r)
                pushed = True
                if len(self.refq) == 2:
                    self.cov.add(("held_byte",))
                if len(self.refq) > 2:
                    self.err("CHK-020", f"pending bytes expected <=2 got {len(self.refq)}")
        if cv == 1 and p[RDY] == 1:
            start = p[CS] == 1
            if start or self.burst is None:
                self.burst = ((cpol or 0) & 1, (cpha or 0) & 1)
            if p[RV] != 0 or len(self.refq) > (1 if pushed else 0):
                self.err("CHK-022", "command handshake expected only with no shown/held byte got one")
            if not start and x is not None:
                self.cov.add(("joint",) if E == x.A + 16 * D else ("pause_exit",))
            if start:
                self.cov.add(("mode", self.burst))
            nx = Xfer(E, cd or 0, cl or 0, start, self.burst[0], self.burst[1], D, len(self.cmd_hs))
            self.cmd_hs.append(nx)
            self.cur = nx

    def _on_cycle(self, E):
        s = self._sample()
        self.log[E] = s
        D = self.D
        if s[RST] == 0:
            self.seen_reset = True
            self._clear()
            if None not in s:
                if (s[CS], s[MOSI], s[RV], s[RD], s[RDY]) != (1, 0, 0, 0, 1):
                    self.err("CHK-016", "outputs in reset (cs_n,mosi,rsp_valid,rsp_data,cmd_ready) expected "
                             f"(1,0,0,0,1) got {(s[CS], s[MOSI], s[RV], s[RD], s[RDY])}")
                if s[SCLK] != s[CPOL]:
                    self.err("CHK-017", f"o_sclk in reset expected i_cpol={s[CPOL]} got {s[SCLK]}")
            self.prev = s
            return
        p = self.prev
        self.prev = s
        if not self.seen_reset or s[RST] != 1 or p is None:
            return
        if None in s:
            self.err("CHK-015", f"outputs expected 0/1 got X/Z {s}")
            return
        if p[RST] != 1:
            p = (1, 1, s[CPOL], 0, 1, 0, 0, s[CPOL])
        if None in p:
            return
        x = self.cur
        # o_cs_n
        if p[CS] == 1 and s[CS] == 0:
            self.cs_fall.append(E)
            if not (x is not None and x.A == E and x.start):
                self.err("CHK-006", "o_cs_n fall expected only at a burst-start handshake got one without")
        elif x is not None and x.A == E and x.start and s[CS] != 0:
            self.err("CHK-006", "o_cs_n expected to fall at the burst-start handshake got 1")
        if p[CS] == 0 and s[CS] == 1:
            self.cs_rise.append(E)
            if not (x is not None and x.last == 1 and E == x.A + 17 * D):
                self.err("CHK-007", "o_cs_n rise expected only at A_last+17*D got another edge")
        if s[CS] == 0:
            if x is None:
                self.err("CHK-007", "o_cs_n=0 expected only inside a burst got 0 without burst")
            elif x.last == 1 and E >= x.A + 17 * D:
                self.err("CHK-007", f"o_cs_n expected 1 from A+17*D={x.A + 17 * D} got 0")
        # o_sclk
        if s[CS] == 1:
            if s[SCLK] != s[CPOL]:
                self.err("CHK-026", f"o_sclk expected i_cpol={s[CPOL]} while o_cs_n=1 got {s[SCLK]}")
        elif x is not None:
            off = E - x.A
            k = min(off // D, 16)
            exp = x.cpol ^ (k & 1)
            if s[SCLK] != exp:
                self.err("CHK-023", f"o_sclk expected {exp} (offset {off}, k={k}, CPOL_b={x.cpol}) got {s[SCLK]}")
            if p[CS] == 0 and p[SCLK] != s[SCLK]:
                self.toggles.append(E)
        # o_mosi
        if x is not None:
            off = E - x.A
            if x.cpha == 0:
                if off % (2 * D) == 0 and off // (2 * D) <= 7:
                    self.mosi_exp = (x.d >> (7 - off // (2 * D))) & 1
            elif off >= D and (off - D) % (2 * D) == 0 and (off - D) // (2 * D) <= 7:
                self.mosi_exp = (x.d >> (7 - (off - D) // (2 * D))) & 1
        if s[MOSI] != self.mosi_exp:
            self.err("CHK-011/012/013", f"o_mosi expected {self.mosi_exp} got {s[MOSI]}")
        # response model
        if self.refq:
            if s[RV] != 1 or s[RD] != self.refq[0]:
                self.err("CHK-020", f"o_rsp_valid/o_rsp_data expected 1/0x{self.refq[0]:02x} got {s[RV]}/0x{s[RD]:02x}")
        elif s[RV] != 0:
            self.err("CHK-020", "o_rsp_valid expected 0 (no pending byte) got 1")
        if s[RV] == 1 and s[RDY] == 1:
            self.err("CHK-002", "o_cmd_ready expected 0 while o_rsp_valid=1 got 1")
        # o_cmd_ready model
        if x is None:
            exp_r = 1 - s[RV]
        else:
            off = E - x.A
            if off <= 16 * D - 2:
                exp_r = 0
            elif off == 16 * D - 1:
                exp_r = 1 if (x.last == 0 and s[RV] == 0) else 0
            elif x.last == 0:
                exp_r = 1 - s[RV]
                if off == 16 * D:
                    self.cov.add(("pause_entry",))
            else:
                exp_r = 0 if off < 18 * D - 1 else 1 - s[RV]
        if s[RDY] != exp_r:
            chk = "CHK-003" if x is None or (x.last == 1 and E - x.A >= 17 * D) else (
                "CHK-004" if E - x.A < 16 * D else "CHK-005")
            self.err(chk, f"o_cmd_ready expected {exp_r} got {s[RDY]}")


# --------------------------------------------------------------------------- helpers
async def tick(dut, n=1):
    for _ in range(int(n)):
        await FallingEdge(dut.i_clk)


async def goto(env, E, chk):
    n = E - env.edge
    assert n >= 0, f"{chk}: stimulus edge {E} expected in the future got current edge {env.edge}"
    await tick(env.dut, n)


async def waitc(env, cond, maxc, what, chk):
    for _ in range(int(maxc)):
        if cond():
            return
        await FallingEdge(env.dut.i_clk)
    assert cond(), f"{chk}: {what} expected within {int(maxc)} cycles got timeout"


def bud(env, nbytes, extra=0):
    return int(nbytes * 24 * env.D + 2 * extra + 64 * env.D + 400)


async def wait_idle(env, maxc, chk):
    dut = env.dut
    await waitc(env, lambda: env.cmd.idle() and val(dut.o_cs_n) == 1 and val(dut.o_rsp_valid) == 0
                and val(dut.o_cmd_ready) == 1, maxc, "Idle (o_cs_n=1, o_rsp_valid=0, o_cmd_ready=1)", chk)
    env.cmd.active = False
    # NNC verification fix (fix-verif, triage B): waitc returns in the FallingEdge callback, before _cyc_mon's
    # ReadOnly sample of the same cycle has logged it (e.g. the o_cs_n rise at R = A+17*D). With D = 1 the Idle
    # condition already holds in cycle R (REQ-CMD-007: no blocked cycle; REQ-CMD-008, DEC-016). Let the
    # monitor finish the current cycle and step to the next falling edge before the caller checks env.cs_rise.
    await ReadOnly()
    await FallingEdge(dut.i_clk)


async def set_mode(env, mode, chk):
    dut = env.dut
    await waitc(env, lambda: env.cmd.idle() and val(dut.o_cs_n) == 1, bud(env, 2),
                "o_cs_n=1 before a mode change", chk)
    env.cmd.active = False
    dut.i_cpol.value = mode[0]
    dut.i_cpha.value = mode[1]
    await tick(dut)


async def present(env, data, last, maxc, chk):
    dut = env.dut
    n0 = len(env.cmd_hs)
    dut.i_cmd_valid.value = 1
    dut.i_cmd_data.value = data
    dut.i_cmd_last.value = last
    for _ in range(int(maxc)):
        await FallingEdge(dut.i_clk)
        if len(env.cmd_hs) > n0:
            return env.cmd_hs[n0].A
    assert False, f"{chk}: command 0x{data:02x} expected accepted within {int(maxc)} cycles got no handshake"


async def reset_pulse(env, cycles=3):
    dut = env.dut
    env.cmd.stop()
    dut.i_cmd_valid.value = 0
    dut.i_rst_n.value = 0
    await tick(dut, cycles)
    dut.i_rst_n.value = 1
    await tick(dut)


async def setup(dut, salt, mode=(0, 0), slave=True):
    # NNC verification fix (fix-verif, triage B): i_rst_n was asserted in the same time step as the clock
    # (re)start, so a clock edge coincided with the reset assertion. ENV-007/GAP-001 makes that an illegal case,
    # and ENV-008 requires i_rst_n = 0 before the first rising edge. i_cpol was also changed in that same step
    # while o_cs_n could still be 0. Now: assert i_rst_n first (no clock is running between tests), change
    # i_cpol/i_cpha a quarter period later in a separate time step, and start the clock a quarter period after
    # that. At time zero, i_cpol/i_cpha get their values at once because they must never be X (ENV-008).
    dut.i_rst_n.value = 0
    dut.i_cmd_valid.value = 0
    dut.i_cmd_data.value = 0
    dut.i_cmd_last.value = 0
    dut.i_rsp_ready.value = 0
    dut.i_miso.value = 0
    if val(dut.i_cpol) is None:
        dut.i_cpol.value = mode[0]
    if val(dut.i_cpha) is None:
        dut.i_cpha.value = mode[1]
    q_ps = max(1, int(round(float(CLOCKS[CLOCK]) * 1000)) // 4)
    await Timer(q_ps, "ps")
    dut.i_cpol.value = mode[0]
    dut.i_cpha.value = mode[1]
    await Timer(q_ps, "ps")
    start_clock(dut)
    env = Env(dut, salt)
    env.slave.enabled = slave
    env.start()
    await tick(dut, 3)
    dut.i_rst_n.value = 1  # released at a falling edge
    await RisingEdge(dut.i_clk)
    t0 = get_sim_time("step")
    await RisingEdge(dut.i_clk)
    env.T = int(get_sim_time("step") - t0)
    await FallingEdge(dut.i_clk)
    await tick(dut, 2)
    return env


def phase_of(env, cs):
    x = env.cur
    D = env.D
    if x is None:
        return "idle"
    off = env.edge - x.A
    if cs == 1:
        return "gap" if (x.last == 1 and off < 18 * D) else "idle"
    if off < 16 * D - 1:
        return "transfer"
    if off == 16 * D - 1:
        return "last"
    return "pause" if x.last == 0 else "trail"


def reg_outs(dut):
    return (val(dut.o_cmd_ready), val(dut.o_rsp_valid), val(dut.o_rsp_data), val(dut.o_cs_n), val(dut.o_mosi))


async def glitcher(env, st):
    """Toggle inputs just after the falling edge and restore them at 3/4 period."""
    dut = env.dut
    T = env.T
    q = (T // 4 - 1) if T >= 8 else 1
    names = ("i_cmd_valid", "i_cmd_data", "i_cmd_last", "i_rsp_ready", "i_miso", "i_cpha")
    while True:
        await FallingEdge(dut.i_clk)
        await Timer(1, "step")
        if not st["on"] or val(dut.i_rst_n) != 1:
            continue
        intended = {n: val(getattr(dut, n)) for n in names}
        cpol0 = val(dut.i_cpol)
        o0 = reg_outs(dut)
        s0 = val(dut.o_sclk)
        if None in intended.values() or None in o0 or cpol0 is None:
            continue
        cs0 = o0[3]
        ph = phase_of(env, cs0)
        st["phases"].add((ph, o0[1]))
        for n in names:
            getattr(dut, n).value = intended[n] ^ (0xFF if n == "i_cmd_data" else 1)
        if cs0 == 1:
            dut.i_cpol.value = 1 - cpol0
        await ReadOnly()
        o1 = reg_outs(dut)
        s1 = val(dut.o_sclk)
        if o1 != o0:
            st["err"].append(f"CHK-029: (ready,valid,data,cs_n,mosi) expected {o0} after input toggle in {ph} got {o1}")
        exp = (1 - cpol0) if cs0 == 1 else s0
        if s1 != exp:
            st["err"].append(f"CHK-029: o_sclk expected {exp} after toggle (cs_n={cs0}) in {ph} got {s1}")
        await Timer(q, "step")
        for n in names:
            getattr(dut, n).value = intended[n]
        if cs0 == 1:
            dut.i_cpol.value = cpol0
        await ReadOnly()
        o2 = reg_outs(dut)
        s2 = val(dut.o_sclk)
        if o2 != o0:
            st["err"].append(f"CHK-029: (ready,valid,data,cs_n,mosi) expected {o0} after restore in {ph} got {o2}")
        exp = cpol0 if cs0 == 1 else s0
        if s2 != exp:
            st["err"].append(f"CHK-029: o_sclk expected {exp} after restore in {ph} got {s2}")


class MisoDrv:
    """Drives i_miso = r[7-j] only in the cycle ending at sampling edge j, NOT of the next bit elsewhere."""

    def __init__(self, env):
        self.env = env
        self.plan = deque()
        self.cur = None
        self.rnd = random.Random(env.rnd.getrandbits(32))

    async def run(self):
        env = self.env
        dut = env.dut
        D = env.D
        while True:
            await FallingEdge(dut.i_clk)
            E = env.edge
            hs = env.cmd_hs
            if hs and hs[-1].A == E and (self.cur is None or self.cur[0] != E):
                rb = self.plan.popleft() if self.plan else self.rnd.randrange(256)
                self.cur = (E, rb, hs[-1].cpha)
            v = self.rnd.randrange(2)
            if self.cur is not None:
                A, rb, cpha = self.cur
                off = E - A
                if 0 <= off < 16 * D:
                    offs = [((2 * j + 1) if cpha == 0 else (2 * j + 2)) * D for j in range(8)]
                    nxt = [j for j in range(8) if offs[j] >= off + 1]
                    if nxt:
                        j = nxt[0]
                        bit = (rb >> (7 - j)) & 1
                        v = bit if offs[j] == off + 1 else 1 - bit
                    else:
                        v = 1 - (rb & 1)
            dut.i_miso.value = v


# =========================================================================== tests
@cocotb.test()
async def test_chk_028_no_handshake_no_effect(dut):
    """CHK-028: commands without handshake (reset, o_cmd_ready=0, withdrawn, valid=0) have no effect."""
    env = await setup(dut, "chk028")
    D, r = env.D, env.rnd
    # (a) i_cmd_valid=1 during reset (error test)
    dut.i_rst_n.value = 0
    for _ in range(6):
        dut.i_cmd_valid.value = 1
        dut.i_cmd_data.value = r.randrange(256)
        dut.i_cmd_last.value = r.randrange(2)
        await tick(dut)
        assert val(dut.o_cmd_ready) == 1 and val(dut.o_cs_n) == 1, \
            f"CHK-028: in reset o_cmd_ready=1,o_cs_n=1 expected got {val(dut.o_cmd_ready)},{val(dut.o_cs_n)}"
    n0, r0, f0 = len(env.cmd_hs), len(env.rsp_hs), len(env.cs_fall)
    dut.i_cmd_valid.value = 0
    dut.i_rst_n.value = 1
    env.rsp.set("on")
    for _ in range(18 * D + 10):  # (d) random data with valid=0
        dut.i_cmd_data.value = r.randrange(256)
        dut.i_cmd_last.value = r.randrange(2)
        await tick(dut)
        assert val(dut.o_cs_n) == 1 and val(dut.o_rsp_valid) == 0, \
            "CHK-028: o_cs_n=1 and o_rsp_valid=0 expected after reset without handshake got a change"
    assert len(env.cmd_hs) == n0 and len(env.rsp_hs) == r0 and len(env.cs_fall) == f0, \
        "CHK-028: no acceptance/response expected from commands presented in reset got some"
    m = env.mark()
    await present(env, r.randrange(256), 1, bud(env, 1), "CHK-028")
    dut.i_cmd_valid.value = 0
    await wait_idle(env, bud(env, 1), "CHK-028")
    env.scoreboard(m, "CHK-028")

    # (b) data/last change every cycle while o_cmd_ready=0
    N = 6 if D <= 16 else 3
    for mode in MODES:
        env.rsp.set("on")
        await wait_idle(env, bud(env, 2), "CHK-028")
        await set_mode(env, mode, "CHK-028")
        env.rsp.set("rand", 0.5)
        drv = {}
        m = env.mark()
        for _ in range(bud(env, N + 2, 0) * 3):
            if len(env.cmd_hs) - m[0] >= N:
                break
            d, l = r.randrange(256), r.randrange(2)
            dut.i_cmd_valid.value = 1
            dut.i_cmd_data.value = d
            dut.i_cmd_last.value = l
            drv[env.edge + 1] = (d, l)
            await tick(dut)
        assert len(env.cmd_hs) - m[0] >= N, f"CHK-028: {N} handshakes expected got {len(env.cmd_hs) - m[0]}"
        if env.cmd_hs[-1].last == 0:
            n1 = len(env.cmd_hs)
            d = r.randrange(256)
            for _ in range(bud(env, 2) * 3):
                dut.i_cmd_valid.value = 1
                dut.i_cmd_data.value = d
                dut.i_cmd_last.value = 1
                drv[env.edge + 1] = (d, 1)
                await tick(dut)
                if len(env.cmd_hs) > n1:
                    break
        dut.i_cmd_valid.value = 0
        env.rsp.set("on")
        await wait_idle(env, bud(env, 3), "CHK-028")
        for x in env.cmd_hs[m[0]:]:
            assert (x.d, x.last) == drv[x.A], \
                f"CHK-028: captured (data,last) expected {drv[x.A]} of handshake edge got {(x.d, x.last)}"
            rises = [c for c in env.cs_rise if x.A < c <= x.A + 17 * D]
            if x.last:
                assert rises == [x.A + 17 * D], f"CHK-028: burst end expected at A+17D got rises {rises}"
            else:
                assert not rises, f"CHK-028: no burst end expected for last=0 command got rises {rises}"
        env.scoreboard(m, "CHK-028")

    # (c)+(d) pulses withdrawn while o_cmd_ready=0, random data with valid=0
    env.rsp.set("on")
    await set_mode(env, MODES[0], "CHK-028")
    await wait_idle(env, bud(env, 1), "CHK-028")
    m = env.mark()
    f0 = len(env.cs_fall)
    A = await present(env, r.randrange(256), 1, bud(env, 1), "CHK-028")
    dut.i_cmd_valid.value = 0
    pulses, prevp = 0, False
    for _ in range(18 * D + lg(D, 1)):
        rdy = val(dut.o_cmd_ready)
        dut.i_cmd_data.value = r.randrange(256)
        dut.i_cmd_last.value = r.randrange(2)
        if rdy == 0 and not prevp and r.random() < 0.4:
            dut.i_cmd_valid.value = 1
            pulses += 1
            prevp = True
        else:
            dut.i_cmd_valid.value = 0
            prevp = False
        await tick(dut)
    dut.i_cmd_valid.value = 0
    await tick(dut, 2)
    assert pulses > 0, "CHK-028: withdrawn pulses expected got none"
    assert len(env.cmd_hs) == m[0] + 1, f"CHK-028: 1 handshake expected got {len(env.cmd_hs) - m[0]}"
    assert len(env.cs_fall) == f0 + 1 and env.cs_rise[-1] == A + 17 * D, \
        "CHK-028: only the real burst expected to change o_cs_n got extra changes"
    assert not [t for t in env.toggles if t > A + 16 * D], "CHK-028: no SCLK toggle expected after burst got some"
    assert len(env.rsp_hs) - m[1] == 1, f"CHK-028: 1 response expected got {len(env.rsp_hs) - m[1]}"
    env.scoreboard(m, "CHK-028")
    env.finish()


@cocotb.test()
async def test_chk_029_no_combinational_input_paths(dut):
    """CHK-029: inputs toggled between edges never change registered outputs; o_sclk follows i_cpol only with o_cs_n=1."""
    env = await setup(dut, "chk029")
    D, r = env.D, env.rnd
    if env.T < 6:
        not_verifiable(dut, "CHK-029", f"clock period {env.T} steps leaves no time for toggles between edges")
        env.finish()
        return
    st = {"on": False, "err": [], "phases": set()}
    cocotb.start_soon(glitcher(env, st))
    modes = MODES if D <= 16 else [MODES[0], MODES[3]]
    nb = gs = 0
    for mode in modes:
        for last, g, md in ((0, 1, mode), (0, 0, None), (0, 1 + D, None), (1, 0, None), (1, 2, None)):
            env.cmd.push(r.randrange(256), last, gap=g, mode=md)
            nb += 1
            gs += g
    m = env.mark()
    env.rsp.set("rand", 0.4)
    st["on"] = True
    env.cmd.go()
    await waitc(env, env.cmd.idle, bud(env, nb, gs) + 60 * nb, "all commands accepted", "CHK-029")
    env.rsp.set("on")
    await wait_idle(env, bud(env, 2), "CHK-029")
    await tick(dut, 3)
    st["on"] = False
    await tick(dut)
    assert not st["err"], st["err"][0]
    need = {"idle", "gap", "transfer", "last", "pause", "trail"}
    seen = {p for p, _ in st["phases"]}
    assert need <= seen, f"CHK-029: toggles expected in phases {sorted(need)} got {sorted(seen)}"
    dut._log.info(f"CHK-029 phases with o_rsp_valid=1: {sorted(p for p, v in st['phases'] if v == 1)}")
    env.scoreboard(m, "CHK-029")
    env.finish()


@cocotb.test()
async def test_chk_030_single_byte_bursts(dut):
    """CHK-030: i_cmd_last=1 on the first byte; o_cs_n rise independent of the response stream."""
    env = await setup(dut, "chk030")
    D, r = env.D, env.rnd
    W = lg(D, 4)
    nb = 4 if D <= 16 else 2
    for mode in MODES:
        env.rsp.set("on")
        await set_mode(env, mode, "CHK-030")
        await wait_idle(env, bud(env, 1), "CHK-030")
        m = env.mark()
        for _ in range(nb):
            env.cmd.push(r.randrange(256), 1, gap=0)
        env.cmd.go()
        await wait_idle(env, bud(env, nb), "CHK-030")
        xs = env.cmd_hs[m[0]:]
        assert len(xs) == nb, f"CHK-030: {nb} handshakes expected got {len(xs)}"
        for x in xs:
            assert x.start and x.last == 1 and x.A in env.cs_fall, "CHK-030: burst start at each handshake expected"
            rise = [c for c in env.cs_rise if c > x.A][:1]
            assert rise == [x.A + 17 * D], f"CHK-030: o_cs_n low exactly {17 * D} cycles expected got rise {rise} (A={x.A})"
            env.cov.add(("last_on_first_byte",))
        env.scoreboard(m, "CHK-030")
        # back-pressure
        env.rsp.set("off")
        m = env.mark()
        env.cmd.push(r.randrange(256), 1, gap=0)
        env.cmd.push(r.randrange(256), 1, gap=0)
        env.cmd.go()
        await waitc(env, lambda: val(dut.o_rsp_valid) == 1, bud(env, 1), "o_rsp_valid=1", "CHK-030")
        V = env.edge
        A = env.cmd_hs[m[0]].A
        assert V == A + 16 * D, f"CHK-030: response expected at A+16D={A + 16 * D} got {V}"
        await tick(dut, W)
        R = A + 17 * D
        s = env.at(R, "CHK-030")
        assert R in env.cs_rise and s[CS] == 1 and s[RV] == 1, \
            f"CHK-030: o_cs_n rise at A+17D with o_rsp_valid=1 expected got cs={s[CS]} rv={s[RV]}"
        for c in range(V, env.edge):
            s = env.at(c, "CHK-030")
            assert s[RDY] == 0 and s[RV] == 1, f"CHK-030: cycle {c} o_cmd_ready=0,o_rsp_valid=1 expected got {s[RDY]},{s[RV]}"
            if c >= R:
                assert s[CS] == 1, f"CHK-030: cycle {c} o_cs_n=1 expected got 0"
        assert len(env.cmd_hs) == m[0] + 1, "CHK-030: no burst start expected before response handshake got one"
        dut.i_rsp_ready.value = 1
        await tick(dut)
        H = env.edge
        dut.i_rsp_ready.value = 0
        assert env.rsp_hs[-1][0] == H and H >= R + D - 1, f"CHK-030: response handshake at H>=R+D-1 expected got {env.rsp_hs[-1]}"
        assert val(dut.o_cmd_ready) == 1 and val(dut.o_rsp_valid) == 0, \
            f"CHK-030: o_cmd_ready=1 in cycle starting at H expected got {val(dut.o_cmd_ready)}"
        await tick(dut)
        assert len(env.cmd_hs) == m[0] + 2 and env.cmd_hs[-1].A == H + 1 and val(dut.o_cs_n) == 0, \
            f"CHK-030: next burst accepted at H+1={H + 1} expected got {[x.A for x in env.cmd_hs[m[0]:]]}"
        env.rsp.set("on")
        await wait_idle(env, bud(env, 2), "CHK-030")
        env.scoreboard(m, "CHK-030")
    env.finish()


@cocotb.test()
async def test_chk_031_pause_and_endless_burst(dut):
    """CHK-031: Pause entry/exit, long pause without timeout, endless burst (i_cmd_last=0 forever)."""
    env = await setup(dut, "chk031")
    D, r = env.D, env.rnd
    gaps = [1, lg(D, 2), lg(D, 20)]
    nend = 16 if D <= 16 else 2
    for mi, mode in enumerate(MODES):
        env.rsp.set("on")
        await set_mode(env, mode, "CHK-031")
        await wait_idle(env, bud(env, 1), "CHK-031")
        m = env.mark()
        f0, r0 = len(env.cs_fall), len(env.cs_rise)
        A = await present(env, r.randrange(256), 0, bud(env, 1), "CHK-031")
        dut.i_cmd_valid.value = 0
        for g in gaps:
            await goto(env, A + 16 * D - 1 + g, "CHK-031")
            P = await present(env, r.randrange(256), 0, bud(env, 1, g), "CHK-031")
            dut.i_cmd_valid.value = 0
            hr = [e for e, _ in env.rsp_hs if e > A]
            assert hr, "CHK-031: response handshake of paused transfer expected got none"
            Hr = hr[0]
            expP = max(A + 16 * D - 1 + g, Hr) + 1
            assert P == expP, f"CHK-031: Pause exit handshake expected at {expP} got {P} (gap {g})"
            mo = env.at(A + 16 * D, "CHK-031")[MOSI]
            for c in range(A + 16 * D, P):
                s = env.at(c, "CHK-031")
                assert s[CS] == 0 and s[SCLK] == mode[0] and s[MOSI] == mo, \
                    f"CHK-031: Pause cycle {c} cs=0,sclk={mode[0]},mosi={mo} expected got {s[CS]},{s[SCLK]},{s[MOSI]}"
                assert s[RDY] == 1 - s[RV] and (c < Hr or s[RDY] == 1), \
                    f"CHK-031: Pause cycle {c} o_cmd_ready=NOT o_rsp_valid expected got rdy={s[RDY]} rv={s[RV]}"
            x = env.cmd_hs[-1]
            assert not x.start and (x.cpol, x.cpha) == mode, "CHK-031: same burst and mode after Pause expected"
            await goto(env, P + D + 1, "CHK-031")
            tg = [t for t in env.toggles if A + 16 * D < t <= P + D]
            assert tg == [P + D], f"CHK-031: SCLK edge 1 at P+D={P + D} only expected got {tg}"
            env.cov.add(("pause",))
            A = P
        for _ in range(nend):
            env.cmd.push(r.randrange(256), 0, gap=0)
        env.cmd.go()
        await waitc(env, env.cmd.idle, bud(env, nend + 1), "endless burst commands accepted", "CHK-031")
        env.cmd.active = False
        Al = env.cmd_hs[-1].A
        await goto(env, Al + 16 * D + lg(D, 2), "CHK-031")
        assert val(dut.o_cs_n) == 0 and len(env.cs_fall) == f0 + 1 and len(env.cs_rise) == r0, \
            "CHK-031: o_cs_n expected to stay 0 for an endless burst got a rise"
        assert not [t for t in env.toggles if t > Al + 16 * D], "CHK-031: no SCLK toggle in Pause expected got some"
        env.scoreboard(m, "CHK-031")
        if mi < len(MODES) - 1:
            await reset_pulse(env)
    env.finish()


@cocotb.test()
async def test_chk_032_mode_change_before_burst_start(dut):
    """CHK-032: new i_cpol/i_cpha presented in the cycle before the burst-start acceptance edge are used."""
    env = await setup(dut, "chk032")
    D, r = env.D, env.rnd
    G = 2 + D
    env.rsp.set("on")
    for X in MODES:
        for Y in MODES:
            if X == Y:
                continue
            await set_mode(env, X, "CHK-032")
            await wait_idle(env, bud(env, 1), "CHK-032")
            await tick(dut)
            m = env.mark()
            n0 = len(env.cmd_hs)
            assert val(dut.o_cmd_ready) == 1 and val(dut.o_cs_n) == 1, "CHK-032: Idle expected before the change"
            dut.i_cpol.value = Y[0]
            dut.i_cpha.value = Y[1]
            dut.i_cmd_valid.value = 1
            dut.i_cmd_data.value = r.randrange(256)
            dut.i_cmd_last.value = 0
            await ReadOnly()
            sc = val(dut.o_sclk)
            assert sc == Y[0], f"CHK-032: o_sclk expected new i_cpol={Y[0]} immediately got {sc}"
            await FallingEdge(dut.i_clk)
            dut.i_cmd_valid.value = 0
            assert len(env.cmd_hs) == n0 + 1, "CHK-032: acceptance at the next edge expected got none"
            x1 = env.cmd_hs[n0]
            A = x1.A
            assert x1.start and (x1.cpol, x1.cpha) == Y, f"CHK-032: CPOL_b/CPHA_b={Y} expected got {(x1.cpol, x1.cpha)}"
            await goto(env, A + 16 * D + G, "CHK-032")
            P = await present(env, r.randrange(256), 1, bud(env, 1), "CHK-032")
            dut.i_cmd_valid.value = 0
            await wait_idle(env, bud(env, 2), "CHK-032")
            for c in list(range(A, A + D)) + list(range(A + 16 * D, P)) + list(range(P + 16 * D, P + 17 * D)):
                s = env.at(c, "CHK-032")
                assert s[CS] == 0 and s[SCLK] == Y[0], f"CHK-032: cycle {c} o_sclk=CPOL_b={Y[0]} expected got {s[SCLK]}"
            tg = [t for t in env.toggles if A < t <= P + 17 * D]
            exp = [A + k * D for k in range(1, 17)] + [P + k * D for k in range(1, 17)]
            assert tg == exp, f"CHK-032: SCLK toggles expected {exp[:3]}.. got {tg[:3]}.. ({len(tg)})"
            env.scoreboard(m, "CHK-032")
            env.cov.add(("mode_change", X, Y))
    env.finish()


@cocotb.test()
async def test_chk_033_mode_change_during_burst_ignored(dut):
    """CHK-033: error test; i_cpol/i_cpha complemented during a burst are ignored until o_cs_n rises."""
    env = await setup(dut, "chk033")
    D, r = env.D, env.rnd
    G = 4 + D

    def flip():
        dut.i_cpol.value = 1 - val(dut.i_cpol)
        dut.i_cpha.value = 1 - val(dut.i_cpha)

    for M in MODES:
        d1, d2, s1, s2 = (r.randrange(256) for _ in range(4))
        # NNC verification fix (fix-verif, triage B): warm-up byte, the same in the ref and the err run (see below)
        w = r.randrange(256)
        traces = {}
        for run in ("ref", "err"):
            env.rsp.set("on")
            await set_mode(env, M, "CHK-033")
            await wait_idle(env, bud(env, 1), "CHK-033")
            # NNC verification fix (fix-verif, triage B): with CPHA_b = 1, o_mosi keeps its previous value from the
            # acceptance edge until SCLK edge 1 (REQ-MOSI-004, REQ-MOSI-006, spec 7.5 note). That value comes from
            # earlier traffic, which differed between the ref and err runs. An identical single-byte warm-up
            # burst in mode M before each run gives both runs the same o_mosi state, so the full exact trace
            # comparison stays valid.
            await present(env, w, 1, bud(env, 1), "CHK-033")
            dut.i_cmd_valid.value = 0
            await wait_idle(env, bud(env, 1), "CHK-033")
            m = env.mark()
            env.slave.preload.clear()
            env.slave.preload.extend([s1, s2])
            A = await present(env, d1, 0, bud(env, 1), "CHK-033")
            dut.i_cmd_valid.value = 0
            if run == "err":
                await goto(env, A + 7 * D + D // 2, "CHK-033")
                flip()
            await goto(env, A + 16 * D + G // 2, "CHK-033")
            if run == "err":
                flip()
            await goto(env, A + 16 * D + G, "CHK-033")
            P = await present(env, d2, 1, bud(env, 1), "CHK-033")
            dut.i_cmd_valid.value = 0
            if run == "err":
                await goto(env, P + 16 * D + D // 2, "CHK-033")
                flip()
            R = P + 17 * D
            await goto(env, R + 2, "CHK-033")
            assert R in env.cs_rise, f"CHK-033: o_cs_n rise at {R} expected got {env.cs_rise[-1:]}"
            traces[run] = (P - A, [tuple(env.at(c, "CHK-033")[i] for i in (CS, SCLK, MOSI)) for c in range(A, R)])
            if run == "err":
                cp = val(dut.i_cpol)
                s = env.at(R, "CHK-033")
                assert cp != M[0] and s[SCLK] == cp, f"CHK-033: o_sclk at R expected current i_cpol={cp} got {s[SCLK]}"
                dut.i_cpol.value = 1 - cp
                await ReadOnly()
                sc = val(dut.o_sclk)
                assert sc == 1 - cp, f"CHK-033: o_sclk expected to follow i_cpol={1 - cp} got {sc}"
                await FallingEdge(dut.i_clk)
            await wait_idle(env, bud(env, 1), "CHK-033")
            env.scoreboard(m, "CHK-033")
            assert env.slave.sent[m[2]:] == [s1, s2], "CHK-033: responses expected the slave bytes"
        assert traces["ref"] == traces["err"], \
            "CHK-033: o_cs_n/o_sclk/o_mosi with mode changes expected identical to reference got a difference"
    env.finish()


@cocotb.test()
async def test_chk_034_cpol_follow_in_reset_and_idle(dut):
    """CHK-034: o_sclk follows i_cpol combinationally in reset, Idle and the Idle gap."""
    env = await setup(dut, "chk034")
    D, r = env.D, env.rnd
    q = env.T // 4

    async def tog(where):
        if q >= 1:
            await RisingEdge(dut.i_clk)
            await Timer(q, "step")
        else:
            await FallingEdge(dut.i_clk)
        newp = 1 - val(dut.i_cpol)
        dut.i_cpol.value = newp
        await ReadOnly()
        sc, cs = val(dut.o_sclk), val(dut.o_cs_n)
        assert sc == newp, f"CHK-034: ({where}) o_sclk expected i_cpol={newp} in the same time step got {sc}"
        assert cs == 1, f"CHK-034: ({where}) o_cs_n=1 expected got {cs}"

    await FallingEdge(dut.i_clk)
    dut.i_cmd_valid.value = 0
    dut.i_rst_n.value = 0
    for _ in range(6):
        await tog("reset")
    await FallingEdge(dut.i_clk)
    dut.i_rst_n.value = 1
    n0, f0 = len(env.cmd_hs), len(env.cs_fall)
    for _ in range(6):
        await tog("idle")
    await FallingEdge(dut.i_clk)
    assert len(env.cmd_hs) == n0 and len(env.cs_fall) == f0, "CHK-034: no acceptance expected got one"
    env.rsp.set("on")
    A = await present(env, r.randrange(256), 1, bud(env, 1), "CHK-034")
    dut.i_cmd_valid.value = 0
    await goto(env, A + 17 * D - 1, "CHK-034")
    for _ in range(D):
        await tog("idle gap")
    await FallingEdge(dut.i_clk)
    for _ in range(3):
        await tog("idle")
    await FallingEdge(dut.i_clk)
    await tick(dut, 2)
    assert len(env.cmd_hs) == n0 + 1 and len(env.cs_fall) == f0 + 1, "CHK-034: only one acceptance expected"
    env.finish()


@cocotb.test()
async def test_chk_035_reset_in_each_phase(dut):
    """CHK-035: asynchronous reset in each phase aborts/discards; restart at first edge after release."""
    env = await setup(dut, "chk035")
    D, r = env.D, env.rnd
    phases = ["xfer_mid_half_period", "xfer_after_sclk_edge", "pause", "trail", "idle_gap",
              "shown_byte", "shown_and_held_byte"]
    for i, ph in enumerate(phases):
        env.rsp.set("on")
        await set_mode(env, MODES[i % 4], "CHK-035")
        await wait_idle(env, bud(env, 1), "CHK-035")
        if ph.startswith("shown"):
            env.rsp.set("off")
        if ph in ("xfer_mid_half_period", "xfer_after_sclk_edge", "pause"):
            A = await present(env, r.randrange(256), 0, bud(env, 1), "CHK-035")
            dut.i_cmd_valid.value = 0
            tgt = {"xfer_mid_half_period": A + 3 * D + D // 2, "xfer_after_sclk_edge": A + 5 * D,
                   "pause": A + 16 * D + 3}[ph]
        elif ph in ("trail", "idle_gap", "shown_byte"):
            A = await present(env, r.randrange(256), 1, bud(env, 1), "CHK-035")
            dut.i_cmd_valid.value = 0
            tgt = {"trail": A + 16 * D + D // 2, "idle_gap": A + 17 * D + (D - 1) // 2,
                   "shown_byte": A + 18 * D + 2}[ph]
        else:
            A = await present(env, r.randrange(256), 0, bud(env, 1), "CHK-035")
            n1 = len(env.cmd_hs)
            dut.i_cmd_data.value = r.randrange(256)
            dut.i_cmd_last.value = 0
            await waitc(env, lambda: len(env.cmd_hs) > n1, bud(env, 1), "second command", "CHK-035")
            dut.i_cmd_valid.value = 0
            A2 = env.cmd_hs[n1].A
            assert A2 == A + 16 * D, f"CHK-035: joint at A+16D expected got {A2}"
            tgt = A2 + 16 * D + 3
        await goto(env, tgt, "CHK-035")
        cs, rv = val(dut.o_cs_n), val(dut.o_rsp_valid)
        if ph in ("xfer_mid_half_period", "xfer_after_sclk_edge", "pause", "trail"):
            assert cs == 0, f"CHK-035: phase {ph} expected o_cs_n=0 got {cs}"
        if ph == "idle_gap":
            assert cs == 1, f"CHK-035: Idle gap expected o_cs_n=1 got {cs}"
        if ph == "shown_byte":
            assert rv == 1 and cs == 1, "CHK-035: shown byte in Idle expected"
        if ph == "shown_and_held_byte":
            assert rv == 1 and len(env.refq) == 2, "CHK-035: shown and held byte expected"
        dut.i_cmd_valid.value = 0
        dut.i_rst_n.value = 0
        cp = val(dut.i_cpol)
        await ReadOnly()
        got = (val(dut.o_cs_n), val(dut.o_sclk), val(dut.o_mosi), val(dut.o_rsp_valid),
               val(dut.o_rsp_data), val(dut.o_cmd_ready))
        assert got == (1, cp, 0, 0, 0, 1), \
            f"CHK-035: ({ph}) reset values (cs_n,sclk,mosi,rsp_valid,rsp_data,cmd_ready)=(1,{cp},0,0,0,1) at once expected got {got}"
        await tick(dut, 3)
        env.cmd.stop()
        ns0 = len(env.slave.sent)
        m = env.mark()
        dut.i_rst_n.value = 1
        dut.i_cmd_valid.value = 1
        dut.i_cmd_data.value = r.randrange(256)
        dut.i_cmd_last.value = 1
        env.rsp.set("on")
        Erel = env.edge
        await tick(dut)
        dut.i_cmd_valid.value = 0
        assert len(env.cmd_hs) == m[0] + 1 and env.cmd_hs[m[0]].A == Erel + 1 and val(dut.o_cs_n) == 0, \
            f"CHK-035: ({ph}) acceptance at first edge after release {Erel + 1} expected got none"
        An = env.edge
        await goto(env, An + 16 * D + 2, "CHK-035")
        for c in range(Erel, An + 16 * D):
            assert env.at(c, "CHK-035")[RV] == 0, f"CHK-035: ({ph}) o_rsp_valid=0 until A+16D expected got 1 at {c}"
        exp = env.slave.sent[ns0]
        rs = env.rsp_hs[m[1]:]
        assert rs and rs[0] == (An + 16 * D + 1, exp), f"CHK-035: ({ph}) first response 0x{exp:02x} expected got {rs[:1]}"
        await wait_idle(env, bud(env, 1), "CHK-035")
        env.scoreboard(m, "CHK-035")
        env.cov.add(("reset", ph))
    env.finish()


@cocotb.test()
async def test_chk_036_held_byte_backpressure(dut):
    """CHK-036: held byte created and released; no transfer while held; consumer never takes."""
    env = await setup(dut, "chk036")
    D, r = env.D, env.rnd
    W = lg(D, 10)
    for mode in MODES:
        for variant in ("last0", "last1"):
            env.rsp.set("on")
            await set_mode(env, mode, "CHK-036")
            await wait_idle(env, bud(env, 1), "CHK-036")
            env.rsp.set("off")
            last2 = 1 if (variant == "last1" or D > 16) else 0
            m = env.mark()
            for l in (0, last2, 1):
                env.cmd.push(r.randrange(256), l, gap=0)
            env.cmd.go()
            await waitc(env, lambda: len(env.cmd_hs) >= m[0] + 2, bud(env, 2), "cmd2 handshake", "CHK-036")
            A1, A2 = env.cmd_hs[m[0]].A, env.cmd_hs[m[0] + 1].A
            assert A2 == A1 + 16 * D, f"CHK-036: cmd2 accepted at A1+16D={A1 + 16 * D} expected got {A2}"
            await goto(env, A2 + 16 * D + 1, "CHK-036")
            r1, r2 = env.slave.sent[m[2]], env.slave.sent[m[2] + 1]
            await tick(dut, W)
            for c in range(A1 + 16 * D, env.edge):
                s = env.at(c, "CHK-036")
                assert s[RV] == 1 and s[RD] == r1 and s[RDY] == 0, \
                    f"CHK-036: cycle {c} rsp_valid=1,data=0x{r1:02x},cmd_ready=0 expected got {s[RV]},0x{s[RD]:02x},{s[RDY]}"
                if c >= A2 + 16 * D:
                    if last2 == 0:
                        assert s[CS] == 0 and s[SCLK] == mode[0], f"CHK-036: Pause at cycle {c} expected"
                    elif c >= A2 + 17 * D:
                        assert s[CS] == 1, f"CHK-036: o_cs_n=1 after A2+17D expected at {c}"
            if last2:
                assert A2 + 17 * D in env.cs_rise, "CHK-036: o_cs_n rise at A2+17D expected regardless of held byte"
            assert not [t for t in env.toggles if t > A2 + 16 * D], "CHK-036: no SCLK toggle while held expected"
            assert len(env.cmd_hs) == m[0] + 2, "CHK-036: cmd3 not accepted while a byte is held expected"
            dut.i_rsp_ready.value = 1
            await tick(dut)
            H1 = env.edge
            dut.i_rsp_ready.value = 0
            assert env.rsp_hs[-1] == (H1, r1), f"CHK-036: first handshake with r1 expected got {env.rsp_hs[-1]}"
            assert val(dut.o_rsp_valid) == 1 and val(dut.o_rsp_data) == r2 and val(dut.o_cmd_ready) == 0, \
                "CHK-036: held byte r2 shown, o_rsp_valid=1, o_cmd_ready=0 expected"
            await tick(dut, 3)
            assert val(dut.o_rsp_valid) == 1 and val(dut.o_rsp_data) == r2 and len(env.cmd_hs) == m[0] + 2, \
                "CHK-036: r2 kept shown and no transfer expected"
            dut.i_rsp_ready.value = 1
            await tick(dut)
            H = env.edge
            dut.i_rsp_ready.value = 0
            assert env.rsp_hs[-1] == (H, r2), f"CHK-036: second handshake with r2 expected got {env.rsp_hs[-1]}"
            assert val(dut.o_rsp_valid) == 0 and val(dut.o_cmd_ready) == 1, \
                "CHK-036: o_rsp_valid=0, o_cmd_ready=1 in cycle starting at H expected"
            await tick(dut)
            assert len(env.cmd_hs) == m[0] + 3 and env.cmd_hs[m[0] + 2].A == H + 1, \
                f"CHK-036: cmd3 accepted at H+1={H + 1} expected"
            assert env.cmd_hs[m[0] + 2].start == bool(last2), "CHK-036: cmd3 burst membership expected per cmd2 last"
            env.cov.add(("held_released",))
            env.rsp.set("on")
            await wait_idle(env, bud(env, 2), "CHK-036")
            env.scoreboard(m, "CHK-036")
    # never-take variant
    env.rsp.set("on")
    await wait_idle(env, bud(env, 1), "CHK-036")
    env.rsp.set("off")
    m = env.mark()
    for l in (0, 0, 1):
        env.cmd.push(r.randrange(256), l, gap=0)
    env.cmd.go()
    await waitc(env, lambda: len(env.cmd_hs) >= m[0] + 2, bud(env, 2), "cmd2 handshake", "CHK-036")
    A1, A2 = env.cmd_hs[m[0]].A, env.cmd_hs[m[0] + 1].A
    await goto(env, A2 + 16 * D + 1, "CHK-036")
    r1 = env.slave.sent[m[2]]
    await tick(dut, lg(D, 4))
    for c in range(A1 + 16 * D, env.edge):
        s = env.at(c, "CHK-036")
        assert s[RV] == 1 and s[RD] == r1, f"CHK-036: never-take: r1 shown at {c} expected"
    assert not [t for t in env.toggles if t > A2 + 16 * D] and len(env.cmd_hs) == m[0] + 2, \
        "CHK-036: never-take: no further transfer expected"
    env.finish()


@cocotb.test()
async def test_chk_037_rsp_handshake_at_transfer_end_and_random_ready(dut):
    """CHK-037: response handshake exactly at A+16D loads the new byte; random i_rsp_ready never loses data."""
    env = await setup(dut, "chk037")
    D, r = env.D, env.rnd
    for i, mode in enumerate(MODES):
        last2 = i % 2
        env.rsp.set("on")
        await set_mode(env, mode, "CHK-037")
        await wait_idle(env, bud(env, 1), "CHK-037")
        env.rsp.set("off")
        m = env.mark()
        for l in (0, last2, 1):
            env.cmd.push(r.randrange(256), l, gap=0)
        env.cmd.go()
        await waitc(env, lambda: len(env.cmd_hs) >= m[0] + 2, bud(env, 2), "cmd2 handshake", "CHK-037")
        A1, A2 = env.cmd_hs[m[0]].A, env.cmd_hs[m[0] + 1].A
        assert A2 == A1 + 16 * D, f"CHK-037: continuous burst expected A2={A1 + 16 * D} got {A2}"
        await goto(env, A2 + 16 * D - 1, "CHK-037")
        assert val(dut.o_rsp_valid) == 1 and val(dut.o_cmd_ready) == 0, \
            "CHK-037: o_rsp_valid=1, o_cmd_ready=0 in last cycle expected"
        dut.i_rsp_ready.value = 1
        await tick(dut)
        dut.i_rsp_ready.value = 0
        E = env.edge
        await tick(dut)
        r1, r2 = env.slave.sent[m[2]], env.slave.sent[m[2] + 1]
        assert E == A2 + 16 * D and env.rsp_hs[m[1]] == (E, r1), f"CHK-037: handshake of r1 at A2+16D expected got {env.rsp_hs[m[1]:]}"
        s = env.at(E, "CHK-037")
        assert s[RV] == 1 and s[RD] == r2, f"CHK-037: o_rsp_valid=1 with r2 at A2+16D expected got {s[RV]},0x{s[RD]:02x}"
        assert len(env.cmd_hs) == m[0] + 2 and s[CS] == 0, "CHK-037: no handshake at A2+16D (Pause/Trail) expected"
        env.rsp.set("on")
        await wait_idle(env, bud(env, 2), "CHK-037")
        if last2:
            assert A2 + 17 * D in env.cs_rise, "CHK-037: Trail then o_cs_n rise at A2+17D expected"
        else:
            assert not env.cmd_hs[m[0] + 2].start, "CHK-037: cmd3 in same burst after Pause expected"
        env.scoreboard(m, "CHK-037")
    for p in (0.1, 0.5, 0.9):
        env.rsp.set("on")
        await wait_idle(env, bud(env, 1), "CHK-037")
        m = env.mark()
        nb = gs = 0
        target = 24 if D <= 16 else 3
        while nb < target:
            L = min(r.choice([1, 2, 3, 4] if D <= 16 else [1, 2]), target - nb)
            mode = r.choice(MODES)
            for i in range(L):
                g = r.choice([0, 0, 1, 3])
                env.cmd.push(r.randrange(256), 1 if i == L - 1 else 0, gap=g, mode=mode if i == 0 else None)
                gs += g
            nb += L
        env.rsp.set("rand", p)
        env.cmd.go()
        await waitc(env, env.cmd.idle, bud(env, nb, gs) + 80 * nb, "random traffic accepted", "CHK-037")
        env.rsp.set("on")
        await wait_idle(env, bud(env, 2), "CHK-037")
        env.scoreboard(m, "CHK-037")
    env.finish()


@cocotb.test()
async def test_chk_038_random_traffic_all_modes(dut):
    """CHK-038: all four modes, random data, burst lengths 1/2/>=16 and gaps 0/1/many, scoreboard."""
    env = await setup(dut, "chk038")
    D, r = env.D, env.rnd
    lens = [1, 2] + ([16] if D <= 16 else [])
    gvals = {"0": 0, "1": 1, "many": lg(D, 3)}
    gk = ["0", "1", "many"]
    gi = 0
    env.rsp.set("on")
    for mode in MODES:
        await set_mode(env, mode, "CHK-038")
        await wait_idle(env, bud(env, 1), "CHK-038")
        m = env.mark()
        order = lens[:]
        r.shuffle(order)
        nb = gs = 0
        for L in order:
            for i in range(L):
                k = gk[gi % 3]
                gi += 1
                env.cmd.push(r.randrange(256), 1 if i == L - 1 else 0, gap=gvals[k])
                env.cov.add(("gap", k))
                nb += 1
                gs += gvals[k]
            env.cov.add(("len", L))
        env.cmd.go()
        await wait_idle(env, bud(env, nb, gs), "CHK-038")
        env.scoreboard(m, "CHK-038")
        assert all((x.cpol, x.cpha) == mode for x in env.cmd_hs[m[0]:]), f"CHK-038: mode {mode} expected for all bursts"
        env.cov.add(("cfg_mode", mode))
    for k in gk:
        assert ("gap", k) in env.cov, f"CHK-038: coverage gap {k} expected got none"
    for L in lens:
        assert ("len", L) in env.cov, f"CHK-038: coverage burst length {L} expected got none"
    env.finish()


@cocotb.test()
async def test_chk_039_miso_sampling_edge_precision(dut):
    """CHK-039: i_miso is captured only in the single cycle ending at each sampling edge."""
    env = await setup(dut, "chk039", slave=False)
    D, r = env.D, env.rnd
    md = MisoDrv(env)
    cocotb.start_soon(md.run())
    env.rsp.set("on")
    for mode in MODES:
        await set_mode(env, mode, "CHK-039")
        for nbytes in (1, 2):
            base = [r.randrange(256) for _ in range(nbytes)]
            for pat in (base, [(~b) & 0xFF for b in base]):
                await wait_idle(env, bud(env, 1), "CHK-039")
                m = env.mark()
                md.plan.clear()
                md.plan.extend(pat)
                for i in range(nbytes):
                    env.cmd.push(r.randrange(256), 1 if i == nbytes - 1 else 0, gap=0)
                env.cmd.go()
                await wait_idle(env, bud(env, nbytes), "CHK-039")
                got = [d for _, d in env.rsp_hs[m[1]:]]
                assert got == pat, f"CHK-039: responses expected {hx(pat)} (mode {mode}) got {hx(got)}"
                xs = env.cmd_hs[m[0]:]
                assert len(xs) == nbytes and (nbytes == 1 or xs[1].A == xs[0].A + 16 * D), \
                    "CHK-039: continuous transfers expected"
    env.finish()


@cocotb.test()
async def test_chk_040_continuous_bursts_timing(dut):
    """CHK-040: back-to-back commands give gapless SCLK, exact o_cs_n times and throughput; boundary variants."""
    env = await setup(dut, "chk040")
    D, r = env.D, env.rnd
    n = 16 if D <= 16 else 2
    ns = 4 if D <= 16 else 2
    for mode in MODES:
        env.rsp.set("on")
        await set_mode(env, mode, "CHK-040")
        await wait_idle(env, bud(env, 1), "CHK-040")
        m = env.mark()
        for _b in range(2):
            for i in range(n):
                env.cmd.push(r.randrange(256), 1 if i == n - 1 else 0, gap=0)
        for _ in range(ns):
            env.cmd.push(r.randrange(256), 1, gap=0)
        env.cmd.go()
        await wait_idle(env, bud(env, 2 * n + ns), "CHK-040")
        xs = env.cmd_hs[m[0]:]
        assert len(xs) == 2 * n + ns, f"CHK-040: {2 * n + ns} handshakes expected got {len(xs)}"
        for b in range(2):
            A1 = xs[b * n].A
            got = [xs[b * n + i].A for i in range(n)]
            assert got == [A1 + 16 * i * D for i in range(n)], f"CHK-040: acceptance edges A1+16iD expected got {got}"
            tg = [t for t in env.toggles if A1 < t <= A1 + 16 * n * D]
            assert tg == [A1 + k * D for k in range(1, 16 * n + 1)], f"CHK-040: {16 * n} gapless toggles expected got {len(tg)}"
            R = A1 + 16 * n * D + D
            assert A1 in env.cs_fall and R in env.cs_rise and not [c for c in env.cs_rise if A1 < c < R], \
                f"CHK-040: o_cs_n low exactly {16 * n * D + D} cycles expected"
            nxt = xs[(b + 1) * n].A
            assert nxt == A1 + 16 * n * D + 2 * D, f"CHK-040: next burst at A1+16nD+2D={A1 + 16 * n * D + 2 * D} expected got {nxt}"
        sing = [x.A for x in xs[2 * n:]]
        for a, b in zip(sing, sing[1:]):
            assert b - a == 18 * D, f"CHK-040: single-byte burst period {18 * D} expected got {b - a}"
        env.scoreboard(m, "CHK-040")
        for variant in (1, 2):
            env.rsp.set("on")
            await wait_idle(env, bud(env, 1), "CHK-040")
            env.rsp.set("off")
            m = env.mark()
            for l in (0, 0, 1):
                env.cmd.push(r.randrange(256), l, gap=0)
            env.cmd.go()
            await waitc(env, lambda: val(dut.o_rsp_valid) == 1, bud(env, 1), "o_rsp_valid=1", "CHK-040")
            V = env.edge
            A1 = env.cmd_hs[m[0]].A
            assert V == A1 + 16 * D and len(env.cmd_hs) >= m[0] + 2 and env.cmd_hs[m[0] + 1].A == V, \
                "CHK-040: response at A1+16D and joint expected"
            A2 = V
            he = V + 16 * D - 1 if variant == 1 else V + 16 * D
            await goto(env, he - 1, "CHK-040")
            dut.i_rsp_ready.value = 1
            await tick(dut)
            dut.i_rsp_ready.value = 0
            assert env.rsp_hs[-1][0] == he, f"CHK-040: response handshake at {he} expected got {env.rsp_hs[-1]}"
            await goto(env, A2 + 17 * D + 1, "CHK-040")
            if variant == 1:
                assert len(env.cmd_hs) >= m[0] + 3 and env.cmd_hs[m[0] + 2].A == A2 + 16 * D, \
                    "CHK-040: variant 1 next transfer at A2+16D expected"
                assert A2 + 16 * D in env.toggles and A2 + 17 * D in env.toggles, "CHK-040: no SCLK pause expected"
                env.cov.add(("continuous_join",))
            else:
                assert env.at(A2 + 16 * D - 1, "CHK-040")[RDY] == 0 and len(env.cmd_hs) == m[0] + 2, \
                    "CHK-040: variant 2 o_cmd_ready=0 in last cycle and no handshake at A2+16D expected"
                assert not [t for t in env.toggles if t > A2 + 16 * D] and val(dut.o_cs_n) == 0, \
                    "CHK-040: variant 2 Pause expected"
            env.rsp.set("on")
            await wait_idle(env, bud(env, 3), "CHK-040")
            env.scoreboard(m, "CHK-040")
    env.finish()


@cocotb.test()
async def test_chk_041_divider_timing(dut):
    """CHK-041: SCLK half period equals PARA_SPI_CLK_DIV; a byte takes 16*D cycles."""
    env = await setup(dut, "chk041")
    D = env.D
    exp_byte = {1: 16, 4: 64, 255: 4080}.get(D, 16 * D)
    assert 16 * D == exp_byte, f"CHK-041: byte time {exp_byte} expected got {16 * D}"
    seqs = [[0xA5], [0xA5, 0x5A]] + ([[0x5A], [0x5A, 0xA5]] if D <= 16 else [])
    env.rsp.set("on")
    for mode in MODES:
        await set_mode(env, mode, "CHK-041")
        for seq in seqs:
            await wait_idle(env, bud(env, 1), "CHK-041")
            m = env.mark()
            for i, d in enumerate(seq):
                env.cmd.push(d, 1 if i == len(seq) - 1 else 0, gap=0)
            env.cmd.go()
            await wait_idle(env, bud(env, len(seq)), "CHK-041")
            xs = env.cmd_hs[m[0]:]
            tg = [t for t in env.toggles if xs[0].A < t <= xs[-1].A + 16 * D]
            exp = [x.A + k * D for x in xs for k in range(1, 17)]
            assert tg == exp, f"CHK-041: toggles at A+k*{D} expected got {tg[:4]}.. ({len(tg)})"
            iv = [b - a for a, b in zip(tg, tg[1:])]
            assert all(v == D for v in iv), f"CHK-041: toggle interval {D} expected got {sorted(set(iv))}"
            for x in xs:
                assert env.at(x.A + 16 * D, "CHK-041")[RV] == 1, f"CHK-041: byte complete after {16 * D} cycles expected"
            env.scoreboard(m, "CHK-041")
    env.finish()


@cocotb.test()
async def test_regression_random(dut):
    """CHK-001..CHK-027, CHK-020, CHK-038: broad legal random traffic with random modes, gaps,
    back-pressure and resets; verified by the reference model and scoreboard."""
    env = await setup(dut, "regression")
    D, r = env.D, env.rnd
    target = max(12, 2400 // D)
    done = 0
    for seg in range(1, 400):
        if done >= target:
            break
        nb = gs = 0
        for _b in range(r.randint(1, 3)):
            L = r.choice([1, 1, 2, 3, 5, 16] if D <= 16 else [1, 1, 2])
            mode = r.choice(MODES)
            for i in range(L):
                g = r.choice([0, 0, 0, 1, 2, D + 1, 5 * D])
                env.cmd.push(r.randrange(256), 1 if i == L - 1 else 0, gap=g, mode=mode if i == 0 else None)
                nb += 1
                gs += g
        rm = r.choice(["on", "on", 0.3, 0.7, 0.95])
        m = env.mark()
        if rm == "on":
            env.rsp.set("on")
        else:
            env.rsp.set("rand", rm)
        env.cmd.go()
        if seg % 5 == 0:
            await tick(dut, r.randint(1, nb * 16 * D + 4))
            env.cmd.stop()
            dut.i_cmd_valid.value = 0
            dut.i_rst_n.value = 0
            await tick(dut, r.randint(2, 4))
            dut.i_rst_n.value = 1
            env.rsp.set("on")
            await tick(dut)
            assert val(dut.o_cmd_ready) == 1 and val(dut.o_cs_n) == 1, \
                "CHK-018: o_cmd_ready=1, o_cs_n=1 after reset release expected"
            env.cov.add(("regression_reset",))
        else:
            await waitc(env, env.cmd.idle, bud(env, nb, gs) + 80 * nb, "commands accepted", "CHK-038")
            env.rsp.set("on")
            await wait_idle(env, bud(env, 3), "CHK-038")
            env.scoreboard(m, "CHK-038")
            done += nb
    assert done >= target, f"CHK-038: {target} verified bytes expected got {done}"
    env.finish()

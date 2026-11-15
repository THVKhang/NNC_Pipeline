"""cocotb 2.1 testbench for m_vlsit_afifo_top (asynchronous FIFO, show-ahead, thresholds,
overflow/underflow pulses, four-phase software reset).

Mon     : one recorder per clock domain. At each falling edge (ReadOnly) it samples the ports of
          its domain = the value "at" the next rising edge (plan sampling convention), then records
          the time of that rising edge in integer ps.
Env     : clocks, reset, drivers (wstep/rstep at falling edges), reference model (Q, P of
          CHK-005/CHK-006) and same-domain protocol checks.
Traffic : constrained-random producer/consumer, one coroutine per domain.
Cross-domain effects are checked as order plus a window counted in destination edges.
"""
import bisect
import inspect
from collections import deque

import cocotb
from cocotb.triggers import FallingEdge, First, ReadOnly, RisingEdge
from cocotb.utils import get_sim_time

from nnc_cocotb import *  # noqa: F401,F403

WCLK, RCLK = "i_clk_wr", "i_clk_rd"


def _param(name, default):
    try:
        v = PARAMS.get(name)
        return default if v is None else int(v)
    except Exception:
        return default


DEPTH = _param("PARA_AFIFO_DEPTH", 8)
DW = _param("PARA_AFIFO_DATA_W", 32)
AW = _param("LPARA_ADDR_W", max(1, (DEPTH - 1).bit_length()))
PW = _param("LPARA_PTR_W", AW + 1)
CELL = _param("PARA_AFIFO_CELL_TYPE", 2)
S = {0: 0, 1: 2, 2: 2, 3: 3, 4: 4}.get(CELL, 2)
DMASK = (1 << DW) - 1
TMAX = (1 << PW) - 1
SYN = any(str(x).split("=")[0].strip() == "VLSIT_SYNTHESIS" for x in (DEFINES or []))
_MS_EN = plusarg("AFIFO_MSYNC_EN")
_MS_SEED = plusarg("AFIFO_MSYNC_SEED")
EXACT = SYN or (_MS_EN is not None and _MS_EN.strip() == "0")
LMAX = S if EXACT else S + 2          # latest destination edge after which a crossing is visible
NB = max(32, 4 * LMAX + 16)           # software-reset completion bound from the spec (32 edges of the slower clock) nnc-literal-ok


def thr(v):
    return max(0, min(int(v), TMAX))


def now():
    return int(get_sim_time(unit="ps"))


async def _maybe(x):
    if inspect.isawaitable(x):
        await x


def distinct_note(dut, chk, n=64):
    if (1 << DW) < n:
        not_verifiable(dut, chk, f"PARA_AFIFO_DATA_W={DW}: fewer than {n} distinct words, the identity "
                                 f"of dropped/discarded words is checked by value only")


WSIGS = ("i_rst_n_wr", "i_rst_n_rd", "i_wr_en", "i_wr_data", "i_full_thr", "i_rst_n_sw",
         "o_sw_rst_busy", "o_full", "o_full_thr", "o_overflow")
RSIGS = ("i_rst_n_wr", "i_rst_n_rd", "i_rd_en", "i_empty_thr", "o_rd_data", "o_empty",
         "o_empty_thr", "o_underflow")


class Mon:
    """v[i]: port values at rising edge i (sampled at the preceding falling edge); t[i]: its time (ps)."""

    def __init__(self, dut, clk, sigs, cb):
        self.dut, self.clk, self.sigs, self.cb = dut, getattr(dut, clk), sigs, cb
        self.t, self.v = [], []

    async def run(self):
        d = self.dut
        for _ in range(100_000_000):
            await FallingEdge(self.clk)
            await ReadOnly()
            v = {s: val(getattr(d, s)) for s in self.sigs}
            await RisingEdge(self.clk)
            rw, rr = val(d.i_rst_n_wr), val(d.i_rst_n_rd)
            v["aw"] = v["i_rst_n_wr"] == 1 and rw == 1
            v["ar"] = v["i_rst_n_rd"] == 1 and rr == 1
            v["act"] = v["aw"] and v["ar"]
            self.t.append(now())
            self.v.append(v)
            self.cb(len(self.v) - 1)

    def idx_after(self, t):
        return bisect.bisect_right(self.t, t)

    def coincide(self, t):
        i = bisect.bisect_left(self.t, t)
        return i < len(self.t) and self.t[i] == t

    def ia(self, t, k):
        return self.idx_after(t) + k - 1

    def rel(self, t, k, chk="TB"):
        i = self.ia(t, k)
        assert i < len(self.v), f"{chk}: destination edge {k} after {t} ps recorded got {len(self.v) - self.idx_after(t)} edges"
        return self.v[i]


class Env:
    def __init__(self, dut, periods=None, ft=None, et=None):
        self.dut = dut
        self.custom = periods is not None
        self.per = {k: float(v) for k, v in (periods or CLOCKS).items()}
        self.ft = thr(DEPTH if ft is None else ft)
        self.et = thr(0 if et is None else et)
        self.wclk, self.rclk = getattr(dut, WCLK), getattr(dut, RCLK)
        self.Q, self.P = deque(), deque()
        self.p_t, self.p_cnt = None, 0
        self.sb_on = False  # NNC hand fix (G3, triage B): armed by hw_reset() after both resets are released
        # NNC hand fix (G3, triage B): no check before this test's first hardware reset is asserted; reset_dut
        # first runs a few edges on the state an aborted previous test left (for its pending SVA consequents)
        self.armed = False
        self.nw = self.nr = self.cw = self.cr = 0
        self.wlog, self.rlog = [], []
        self.idle_checks = 0
        self._r = rng("env-words")
        self._wb, self._wc = self._r.getrandbits(max(DW, 1)), 0
        self.wm = Mon(dut, WCLK, WSIGS, self._on_w)
        self.rm = Mon(dut, RCLK, RSIGS, self._on_r)

    # ---------------------------------------------------------------- setup
    def idle(self):
        return {"i_wr_en": 0, "i_rd_en": 0, "i_wr_data": 0, "i_rst_n_sw": 1,
                "i_full_thr": self.ft, "i_empty_thr": self.et}

    def tslow(self):
        return int(max(self.per[WCLK], self.per[RCLK]) * 1000)

    def slow2w(self, n):
        return int(n * self.tslow() / (self.per[WCLK] * 1000.0)) + 2

    def word(self):
        self._wc += 1
        return (self._wb + self._wc * 0x9E3779B1) & DMASK

    async def start(self):
        d = self.dut
        for k, v in self.idle().items():
            # NNC hand fix (G3, triage B): the thresholds change only in reset (reset_dut drives them there);
            # changing them here, before the reset, moved o_full_thr between write edges (CHK-012)
            if k not in ("i_full_thr", "i_empty_thr"):
                getattr(d, k).value = v
        if self.custom:
            await _maybe(start_clock(d, periods=self.per))
        else:
            await _maybe(start_clock(d))
        d._log.info(f"AFIFO TB: DEPTH={DEPTH} DW={DW} PW={PW} CELL={CELL} S={S} SYN={SYN} "
                    f"MSYNC_EN={_MS_EN} MSYNC_SEED={_MS_SEED} exact={EXACT} LMAX={LMAX} "
                    f"clocks={self.per} full_thr={self.ft} empty_thr={self.et}")
        cocotb.start_soon(self.wm.run())
        cocotb.start_soon(self.rm.run())
        cocotb.start_soon(self._rst_watch())
        await self.hw_reset()

    async def hw_reset(self):
        d = self.dut
        await reset_dut(d, cycles=5, idle=self.idle())
        self.armed = True
        for _ in range(2000):
            if val(d.i_rst_n_wr) == 1 and val(d.i_rst_n_rd) == 1:
                break
            await FallingEdge(self.wclk)
        assert val(d.i_rst_n_wr) == 1 and val(d.i_rst_n_rd) == 1, "TB: both hardware resets released"
        self.clear()
        self.sb_on = True
        await FallingEdge(self.rclk)
        await FallingEdge(self.wclk)

    async def _rst_watch(self):
        d = self.dut
        for _ in range(1_000_000):
            await First(FallingEdge(d.i_rst_n_wr), FallingEdge(d.i_rst_n_rd))
            self.armed = True
            self.clear()

    def clear(self):
        self.Q.clear()
        self.P.clear()
        self.p_t = None
        self.cw = self.cr = 0

    # ------------------------------------------------- reference model + checks
    def _on_w(self, i):
        if not self.armed:
            return
        v, t = self.wm.v[i], self.wm.t[i]
        if v["aw"]:
            full, fth, busy, sw, ft = v["o_full"], v["o_full_thr"], v["o_sw_rst_busy"], v["i_rst_n_sw"], v["i_full_thr"]
            if sw == 0 or busy == 1:
                assert full == 1 and fth == int(ft == 0), (
                    f"CHK-009: write block (i_rst_n_sw={sw} busy={busy}) expected o_full=1 o_full_thr={int(ft == 0)} "
                    f"got o_full={full} o_full_thr={fth} at {t} ps")
            if ft == 0:
                assert fth == 1, f"CHK-013: i_full_thr=0 expected o_full_thr=1 got {fth} at {t} ps"
            elif ft > DEPTH and self.sb_on:  # NNC hand fix (G3, formal triage B): occupancy-dependent, see below
                assert fth == 0, f"CHK-013: i_full_thr={ft}>depth expected o_full_thr=0 got {fth} at {t} ps"
            # NNC hand fix (G3, triage B): the state-dependent parts are not checked between a one-domain
            # hardware reset and the next reset of both domains (sb_on=False there, contract CHK-023)
            elif ft == DEPTH and self.sb_on:
                exp = int(full == 1 and sw == 1 and busy == 0)
                assert fth == exp, f"CHK-013: i_full_thr=depth expected o_full_thr={exp} got {fth} at {t} ps"
            if full == 1 and sw == 1 and busy == 0 and self.sb_on:
                assert fth == int(ft <= DEPTH), f"CHK-013: full expected o_full_thr={int(ft <= DEPTH)} got {fth} at {t} ps"
            p = self.wm.v[i - 1] if i > 0 else None
            if p is not None and p["aw"]:
                exp = int(p["i_wr_en"] == 1 and p["o_full"] == 1 and p["i_rst_n_sw"] == 1 and p["o_sw_rst_busy"] == 0)
                assert v["o_overflow"] == exp, f"CHK-008: o_overflow expected {exp} got {v['o_overflow']} at {t} ps"
                if p["o_sw_rst_busy"] == 0:
                    eb = int(p["i_rst_n_sw"] == 0)
                    assert busy == eb, f"CHK-010: o_sw_rst_busy expected {eb} got {busy} at {t} ps"
        if not v["act"]:
            self.clear()
            return
        if not self.sb_on:
            return
        n = len(self.Q)
        assert n <= DEPTH, f"CHK-006: occupancy <= {DEPTH} got {n} at {t} ps"
        if n == DEPTH:
            assert v["o_full"] == 1, f"CHK-006: {DEPTH} unread words expected o_full=1 got {v['o_full']} at {t} ps"
        if v["i_rst_n_sw"] == 0 and v["o_sw_rst_busy"] == 0:
            self.P.extend(self.Q)
            self.Q.clear()
            self.p_t, self.p_cnt = t, 0
        elif v["i_rst_n_sw"] == 1 and v["o_sw_rst_busy"] == 0 and n >= v["i_full_thr"]:
            assert v["o_full_thr"] == 1, (f"CHK-032: occupancy {n} >= i_full_thr {v['i_full_thr']} expected "
                                          f"o_full_thr=1 (never optimistic) got 0 at {t} ps")
        if v["i_wr_en"] == 1 and v["o_full"] == 0:
            dd = v["i_wr_data"]
            self.Q.append(dd)
            self.nw += 1
            self.cw += 1
            self.wlog.append((t, dd))

    def _on_r(self, i):
        if not self.armed:
            return
        v, t = self.rm.v[i], self.rm.t[i]
        if v["ar"]:
            e, eth, et = v["o_empty"], v["o_empty_thr"], v["i_empty_thr"]
            if e == 1:
                assert eth == 1, f"CHK-003: o_empty=1 expected o_empty_thr=1 got {eth} at {t} ps"
            if et is not None and et >= DEPTH and self.sb_on:  # NNC hand fix (G3, formal triage B): as CHK-013
                assert eth == 1, f"CHK-003: i_empty_thr>=depth expected o_empty_thr=1 got {eth} at {t} ps"
            if et == 0:
                assert eth == e, f"CHK-003: i_empty_thr=0 expected o_empty_thr==o_empty={e} got {eth} at {t} ps"
            p = self.rm.v[i - 1] if i > 0 else None
            if p is not None and p["ar"] and v["o_underflow"] == 1:
                assert p["i_rd_en"] == 1 and p["o_empty"] == 1, (
                    f"CHK-002: o_underflow=1 needs i_rd_en=1 and o_empty=1 at the previous read edge "
                    f"got i_rd_en={p['i_rd_en']} o_empty={p['o_empty']} at {t} ps")
        if not v["act"]:
            self.clear()
            return
        if not self.sb_on:
            return
        if self.p_t is not None and t > self.p_t:
            self.p_cnt += 1
            if self.p_cnt >= S + 3:
                self.P.clear()
                self.p_t = None
        occ = len(self.Q) + len(self.P)
        if occ <= v["i_empty_thr"]:
            assert v["o_empty_thr"] == 1, (f"CHK-032: occupancy {occ} <= i_empty_thr {v['i_empty_thr']} expected "
                                           f"o_empty_thr=1 (never optimistic) got 0 at {t} ps")
        if v["o_empty"] == 0:
            head = self.P[0] if self.P else (self.Q[0] if self.Q else None)
            assert head is not None, f"CHK-006: o_empty=0 while no unread word was written at {t} ps"
            dd = v["o_rd_data"]
            assert dd is not None and dd == head, (f"CHK-005: o_rd_data expected head {hex(head)} got "
                                                   f"{'X' if dd is None else hex(dd)} at {t} ps")
            if v["i_rd_en"] == 1:
                if self.P:
                    self.P.popleft()
                else:
                    self.Q.popleft()
                self.nr += 1
                self.cr += 1
                self.rlog.append((t, dd))

    # ---------------------------------------------------------------- drivers
    async def wsync(self):
        await FallingEdge(self.wclk)

    async def rsync(self):
        await FallingEdge(self.rclk)

    async def wstep(self, en=0, data=None, sw=None):
        """Called at a write falling edge: drive, return index of the edge that samples it."""
        d = self.dut
        d.i_wr_en.value = en
        if data is not None:
            d.i_wr_data.value = data & DMASK
        if sw is not None:
            d.i_rst_n_sw.value = sw
        await FallingEdge(self.wclk)
        return len(self.wm.v) - 1

    async def rstep(self, en=0):
        self.dut.i_rd_en.value = en
        await FallingEdge(self.rclk)
        return len(self.rm.v) - 1

    async def widle(self, n):
        for _ in range(n):
            await self.wstep(0)

    async def ridle(self, n):
        for _ in range(n):
            await self.rstep(0)

    async def step_idle(self, side):
        if side == "w":
            await self.wstep(0)
        else:
            await self.rstep(0)

    async def until(self, side, cond, maxc, what):
        for _ in range(maxc):
            if cond():
                return
            await self.step_idle(side)
        assert cond(), what

    async def wait_dst(self, side, mon, t0, n, maxc=20000):
        for _ in range(maxc):
            if len(mon.t) - mon.idx_after(t0) >= n:
                return
            await self.step_idle(side)
        assert False, f"TB: {n} destination edges after {t0} ps not reached"

    def wacc(self, i):
        v = self.wm.v[i]
        return bool(v["act"] and v["i_wr_en"] == 1 and v["o_full"] == 0)

    def racc(self, j):
        v = self.rm.v[j]
        return bool(v["act"] and v["i_rd_en"] == 1 and v["o_empty"] == 0)

    def lat(self, mon, t0, sig, old, new, n, chk, what, stay=True):
        i0 = mon.idx_after(t0)
        assert len(mon.v) >= i0 + n, f"{chk}: {what}: {n} destination edges recorded got {len(mon.v) - i0}"
        seq = [mon.v[i0 + j][sig] for j in range(n)]
        if old == new:
            assert all(x == old for x in seq), f"{chk}: {what}: {sig}={old} at destination edges 1..{n} got {seq}"
            return None, False
        co = mon.coincide(t0)
        assert new in seq, f"{chk}: {what}: {sig} changes to {new} within {n} destination edges got {seq}"
        L = seq.index(new)
        assert all(x == old for x in seq[:L]), f"{chk}: {what}: {sig}={old} before the change got {seq}"
        if stay:
            assert all(x == new for x in seq[L:]), f"{chk}: {what}: {sig} stays {new} after the change got {seq}"
        lo = S - 1 if co else S
        assert lo <= L <= LMAX, (f"{chk}: {what}: {sig} changes after destination edge L in {S}..{LMAX} "
                                 f"({'nominal' if EXACT else 'metastability model'}) got L={L} edges={seq}")
        return L, co


class LevelReader:
    def __init__(self, env):
        self.env, self.en, self.run, self.task = env, 0, True, None

    def start(self):
        self.task = cocotb.start_soon(self.loop())
        return self

    async def loop(self):
        await self.env.rsync()
        for _ in range(50_000_000):
            if not self.run:
                break
            await self.env.rstep(self.en)
        self.env.dut.i_rd_en.value = 0

    async def stop(self):
        self.run = False
        await self.task


class Traffic:
    """Constrained-random producer (write domain) and consumer (read domain)."""

    def __init__(self, env, r, wd=0.5, rd=0.5):
        self.env, self.r = env, r
        self.wd, self.rdn = wd, rd
        self.wgate = self.rgate = False
        self.sw_left = 0
        self.rforce = False
        self.run = False
        self.wt = self.rt = None

    def start(self):
        self.run = True
        self.wt = cocotb.start_soon(self.writer())
        self.rt = cocotb.start_soon(self.reader())

    async def stop(self):
        self.run = False
        if self.wt is not None:
            await self.wt
        if self.rt is not None:
            await self.rt

    async def writer(self):
        e, d = self.env, self.env.dut
        await e.wsync()
        for _ in range(50_000_000):
            if not self.run:
                break
            sw = 1
            if self.sw_left > 0:
                sw = 0
                self.sw_left -= 1
            en = int(self.r.random() < self.wd)
            if self.wgate and val(d.o_full) != 0:
                en = 0
            await e.wstep(en, self.r.getrandbits(DW), sw)
        d.i_wr_en.value = 0
        d.i_rst_n_sw.value = 1

    async def reader(self):
        e, d = self.env, self.env.dut
        await e.rsync()
        for _ in range(50_000_000):
            if not self.run:
                break
            en = 1 if self.rforce else int(self.r.random() < self.rdn)
            if self.rgate and val(d.o_empty) != 0:
                en = 0
            await e.rstep(en)
        d.i_rd_en.value = 0


# ======================================================================= helpers
async def wcycles(env, n):
    for _ in range(max(0, int(n))):
        await FallingEdge(env.wclk)


def chk_w_reset_now(env, chk):
    d = env.dut
    ov, bz, fu, ft = val(d.o_overflow), val(d.o_sw_rst_busy), val(d.o_full), val(d.o_full_thr)
    assert ov == 0 and bz == 0, f"{chk}: at i_rst_n_wr assertion expected o_overflow=0 busy=0 got {ov},{bz}"
    if val(d.i_rst_n_sw) == 1:
        assert fu == 0 and ft == int(env.ft == 0), (f"{chk}: at i_rst_n_wr assertion expected o_full=0 "
                                                    f"o_full_thr={int(env.ft == 0)} got {fu},{ft}")


def chk_r_reset_now(env, chk):
    d = env.dut
    e, et, u = val(d.o_empty), val(d.o_empty_thr), val(d.o_underflow)
    assert e == 1 and et == 1 and u == 0, (f"{chk}: at i_rst_n_rd assertion expected o_empty=1 o_empty_thr=1 "
                                           f"o_underflow=0 got {e},{et},{u}")


def no_err_pulses(env, iw0, ir0, chk):
    for k in range(iw0, len(env.wm.v)):
        assert env.wm.v[k]["o_overflow"] in (0, None) or not env.wm.v[k]["aw"], \
            f"{chk}: o_overflow stays 0 got 1 at {env.wm.t[k]} ps"
    for k in range(ir0, len(env.rm.v)):
        assert env.rm.v[k]["o_underflow"] in (0, None) or not env.rm.v[k]["ar"], \
            f"{chk}: o_underflow stays 0 got 1 at {env.rm.t[k]} ps"


async def drain(env, chk):
    d = env.dut
    await env.rsync()
    for _ in range(8 * DEPTH + 400):  # loop bound: multiplier of DEPTH plus margin nnc-literal-ok
        if len(env.Q) == 0:
            break
        await env.rstep(1 if val(d.o_empty) == 0 else 0)
    assert len(env.Q) == 0, f"{chk}: drain completes got {len(env.Q)} words left"
    await env.rstep(0)


async def xfer_one(env, chk, D):
    """Single write into the empty FIFO, crossing check, read back."""
    d = env.dut
    await env.wsync()
    await env.until("w", lambda: val(d.o_full) == 0 and val(d.o_sw_rst_busy) == 0, 500,
                    f"{chk}: FIFO writable before the single write")
    i = await env.wstep(1, D)
    assert env.wacc(i), f"{chk}: write of {hex(D)} accepted with o_full=0 got o_full={env.wm.v[i]['o_full']}"
    tw = env.wm.t[i]
    await env.wait_dst("w", env.rm, tw, LMAX + 4)
    env.lat(env.rm, tw, "o_empty", 1, 0, LMAX + 4, chk, "o_empty after the single write")
    for k in range(2, LMAX + 5):
        got = env.rm.rel(tw, k, chk)["o_rd_data"]
        assert got == D, f"{chk}: o_rd_data={hex(D)} from read edge 2 after the write got {got} at edge {k}"
    await env.rsync()
    j = await env.rstep(1)
    assert env.racc(j) and env.rm.v[j]["o_rd_data"] == D, f"{chk}: read returns {hex(D)} got {env.rm.v[j]}"
    j = await env.rstep(0)
    assert env.rm.v[j]["o_empty"] == 1 and env.rm.v[j]["o_underflow"] == 0, \
        f"{chk}: after the read o_empty=1 and no underflow got {env.rm.v[j]}"


async def idle_check(env, tr, chk):
    wd, rd = tr.wd, tr.rdn
    tr.wd, tr.rdn = 0.0, 0.0
    await wcycles(env, env.slow2w(LMAX + 8))  # settling margin in slow edges nnc-literal-ok
    d = env.dut
    if val(d.o_sw_rst_busy) == 0 and val(d.i_rst_n_sw) == 1 and tr.sw_left == 0:
        f = val(d.o_full)
        await FallingEdge(env.rclk)
        e = val(d.o_empty)
        assert not (f == 1 and e == 1), f"{chk}: at an idle point o_full and o_empty not both 1 got {f},{e}"
        env.idle_checks += 1
        await FallingEdge(env.wclk)
    tr.wd, tr.rdn = wd, rd


async def random_traffic(env, tr, r, words, chk, idle_checks=0):
    target = env.nw + words
    sched = ["fill", "drain", "same"]
    idle_at = set(r.sample(range(3, 30), idle_checks)) if idle_checks else set()
    last, stall = env.nw, 0
    for it in range(20000):
        if env.nw >= target:
            break
        mode = sched[it] if it < len(sched) else r.choice(["fill", "drain", "mix", "mix", "mix", "same"])
        if mode == "fill":
            tr.wd, tr.rdn = 1.0, 0.0
        elif mode == "drain":
            tr.wd, tr.rdn = 0.0, 1.0
        elif mode == "same":
            tr.wd, tr.rdn = 1.0, 1.0
        else:
            tr.wd, tr.rdn = r.uniform(0.1, 1.0), r.uniform(0.1, 1.0)
        await wcycles(env, env.slow2w(r.randint(2 * DEPTH + 10, 2 * DEPTH + 60)))
        if it in idle_at:
            await idle_check(env, tr, chk)
        if env.nw == last:
            stall += 1
            assert stall < 40, f"{chk}: writes accepted under random traffic got none for 40 phases"
        else:
            last, stall = env.nw, 0
    assert env.nw >= target, f"{chk}: {words} accepted words got {words - (target - env.nw)}"


async def final_drain(env, tr, chk):
    d = env.dut
    tr.wd, tr.rdn, tr.sw_left, tr.rforce = 0.0, 1.0, 0, False
    ok = False
    for _ in range(env.slow2w(8 * DEPTH + 400)):  # loop bound: multiplier of DEPTH plus margin nnc-literal-ok
        await FallingEdge(env.wclk)
        if len(env.Q) == 0 and val(d.o_sw_rst_busy) == 0 and val(d.i_rst_n_sw) == 1:
            ok = True
            break
    assert ok, f"{chk}: final drain empties the FIFO got {len(env.Q)} words busy={val(d.o_sw_rst_busy)}"
    await wcycles(env, env.slow2w(LMAX + 8))  # settling margin in slow edges nnc-literal-ok
    await tr.stop()
    await env.wsync()
    f = val(d.o_full)
    await env.rsync()
    e = val(d.o_empty)
    assert len(env.Q) == 0 and e == 1 and f == 0, \
        f"{chk}: end of drain expected Q empty o_empty=1 o_full=0 got Q={len(env.Q)} o_empty={e} o_full={f}"


async def sw_random(env, tr, r, nseq, chk):
    d = env.dut
    for s in range(nseq):
        mode = ("empty", "partial", "full")[s % 3]
        if mode == "empty":
            tr.wd, tr.rdn = 0.0, 1.0
            for _ in range(env.slow2w(4 * DEPTH + 100)):
                await FallingEdge(env.wclk)
                if len(env.Q) == 0:
                    break
            await wcycles(env, env.slow2w(LMAX + 4))
        elif mode == "full":
            tr.wd, tr.rdn = 1.0, 0.0
            for _ in range(env.slow2w(4 * DEPTH + 100)):
                await FallingEdge(env.wclk)
                if val(d.o_full) == 1:
                    break
        else:
            tr.wd, tr.rdn = 0.6, 0.4
            await wcycles(env, r.randint(3, 3 * DEPTH + 10))
        tr.wd, tr.rdn = r.choice([0.0, 0.3, 0.7, 1.0]), r.choice([0.0, 0.3, 0.7, 1.0])
        tr.rforce = r.random() < 0.5
        tr.sw_left = r.randint(1, 12)
        ok = False
        for _ in range(40):
            await FallingEdge(env.wclk)
            if val(d.o_sw_rst_busy) == 1:
                ok = True
                break
        assert ok, f"{chk}: o_sw_rst_busy rises after i_rst_n_sw=0"
        if r.random() < 0.3:
            await wcycles(env, r.randint(tr.sw_left, tr.sw_left + 8))  # random extra wait in cycles nnc-literal-ok
            if val(d.o_sw_rst_busy) == 1 and tr.sw_left == 0:
                tr.sw_left = r.randint(1, 3)
        done = False
        for _ in range(env.slow2w(3 * NB) + 80):
            await FallingEdge(env.wclk)
            if tr.sw_left == 0 and val(d.i_rst_n_sw) == 1 and val(d.o_sw_rst_busy) == 0:
                done = True
                break
        assert done, f"{chk}: software reset completes (o_sw_rst_busy=0), no deadlock"
        await wcycles(env, env.slow2w(LMAX + 4))
        tr.rforce = False
        await wcycles(env, r.randint(0, 20))


def busy_intervals(env):
    v = env.wm.v
    res, s = [], None
    for i in range(1, len(v)):
        if not (v[i]["aw"] and v[i - 1]["aw"]):
            s = None
            continue
        b, pb = v[i]["o_sw_rst_busy"], v[i - 1]["o_sw_rst_busy"]
        if b == 1 and pb == 0:
            s = i
        elif b == 0 and pb == 1 and s is not None:
            res.append((s - 1, i - 1))
            s = None
    return res


def check_sw_intervals(env, chk):
    wv, wt, rv, rtm = env.wm.v, env.wm.t, env.rm.v, env.rm.t
    ivs = busy_intervals(env)
    nrel = 0
    for E, m in ivs:
        ref = E
        for k in range(E + 1, m + 1):
            if wv[k]["i_rst_n_sw"] == 1 and wv[k - 1]["i_rst_n_sw"] == 0:
                ref = k
        dt = wt[m + 1] - wt[ref]
        assert dt <= (NB + 1) * env.tslow(), (f"{chk}: busy falls within {NB} edges of the slower clock after the "
                                              f"later of busy rise and i_rst_n_sw=1 got {dt} ps at {wt[m]} ps")
        v = wv[m + 1]
        assert v["o_full_thr"] == int(v["i_full_thr"] == 0), f"CHK-011: o_full_thr empty value at busy fall got {v}"
        assert v["o_full"] == (0 if v["i_rst_n_sw"] == 1 else 1), f"CHK-011: o_full at busy fall got {v}"
        b = env.rm.idx_after(wt[E])
        e2 = env.rm.idx_after(wt[m]) + 1
        if e2 < len(rv) and all(rv[a]["i_rd_en"] == 1 and rv[a]["act"] for a in range(b, e2 + 1)):
            rf = next((a for a in range(b + LMAX + 1, e2 + 1) if rv[a]["o_underflow"] == 1), None)
            assert rf is not None and rtm[rf - 2] < wt[m], (f"{chk}: read side released before busy falls "
                                                            f"(underflow resumes) at busy fall {wt[m]} ps")
            nrel += 1
    return ivs, nrel


async def iso_writes(env, r, n, chk):
    d, hist = env.dut, {}
    for _ in range(n):
        await env.wsync()
        await env.until("w", lambda: val(d.o_full) == 0 and len(env.Q) == 0, 500, f"{chk}: FIFO empty before write")
        await env.wait_dst("w", env.rm, now(), 6 + r.randint(0, 3))
        D = env.word()
        i = await env.wstep(1, D)
        assert env.wacc(i), f"{chk}: isolated write accepted got o_full={env.wm.v[i]['o_full']}"
        tw = env.wm.t[i]
        await env.wait_dst("w", env.rm, tw, LMAX + 4)
        L, co = env.lat(env.rm, tw, "o_empty", 1, 0, LMAX + 4, chk, "o_empty after isolated write")
        if not co:
            hist[L] = hist.get(L, 0) + 1
        for k in range(2, LMAX + 5):
            got = env.rm.rel(tw, k, chk)["o_rd_data"]
            assert got == D, f"{chk}: o_rd_data={hex(D)} from read edge 2 got {got} at edge {k}"
        await env.rsync()
        j = await env.rstep(1)
        assert env.racc(j) and env.rm.v[j]["o_rd_data"] == D, f"{chk}: read back {hex(D)} got {env.rm.v[j]}"
        await env.rstep(0)
    return hist


async def iso_reads(env, r, n, chk):
    d, hist = env.dut, {}
    await env.wsync()
    for _ in range(8 * DEPTH + 200):  # loop bound: multiplier of DEPTH plus margin nnc-literal-ok
        if len(env.Q) >= DEPTH:
            break
        await env.wstep(1 if val(d.o_full) == 0 else 0, env.word())
    assert len(env.Q) == DEPTH, f"{chk}: FIFO filled to {DEPTH} got {len(env.Q)}"
    await env.wait_dst("w", env.rm, now(), LMAX + 3)
    for _ in range(n):
        await env.wsync()
        await env.widle(6 + r.randint(0, 3))
        await env.rsync()
        j = await env.rstep(1)
        assert env.racc(j), f"{chk}: isolated read from full accepted got {env.rm.v[j]}"
        await env.rstep(0)  # NNC hand fix (G3, triage B): one isolated read, as in iso_writes
        tr = env.rm.t[j]
        await env.wsync()
        await env.wait_dst("w", env.wm, tr, LMAX + 4)
        L, co = env.lat(env.wm, tr, "o_full", 1, 0, LMAX + 4, chk, "o_full after isolated read from full")
        if not co:
            hist[L] = hist.get(L, 0) + 1
        i = await env.wstep(1, env.word())
        assert env.wacc(i), f"{chk}: refill write accepted"
        i = await env.wstep(0)
        assert env.wm.v[i]["o_full"] == 1, f"{chk}: o_full=1 at once after the refill got 0"
        await env.wait_dst("w", env.rm, env.wm.t[i], LMAX + 3)
    return hist


# --------------------------------------------------------- directed scenarios
async def scen_018(env, chk):
    await env.wsync()
    await env.widle(LMAX + 3)
    iw0, ir0 = len(env.wm.v), len(env.rm.v)
    D = [env.word() for _ in range(DEPTH)]
    for k, w in enumerate(D):
        i = await env.wstep(1, w)
        assert env.wm.v[i]["o_full"] == 0 and env.wacc(i), f"{chk}: D{k} accepted with o_full=0 got {env.wm.v[i]}"
    i = await env.wstep(0)
    v = env.wm.v[i]
    assert v["o_full"] == 1 and v["o_full_thr"] == int(DEPTH >= env.ft), \
        f"{chk}: after the last write o_full=1 o_full_thr={int(DEPTH >= env.ft)} got {v['o_full']},{v['o_full_thr']}"
    await env.wait_dst("w", env.rm, env.wm.t[i - 1], max(5, LMAX + 1))
    await env.rsync()
    for k in range(DEPTH):
        j = await env.rstep(1)
        v = env.rm.v[j]
        assert v["o_empty"] == 0 and v["o_rd_data"] == D[k], \
            f"{chk}: read {k} expected o_empty=0 o_rd_data={hex(D[k])} got {v['o_empty']},{v['o_rd_data']}"
    j = await env.rstep(0)
    v = env.rm.v[j]
    assert v["o_empty"] == 1 and v["o_empty_thr"] == 1, f"{chk}: after the last read o_empty=1 o_empty_thr=1 got {v}"
    no_err_pulses(env, iw0, ir0, chk)
    return D


async def scen_020(env, chk):
    wv = env.wm.v
    await env.wsync()
    await env.widle(LMAX + 3)
    D = []
    for _ in range(DEPTH):
        w = env.word()
        i = await env.wstep(1, w)
        assert env.wacc(i), f"{chk}: fill write accepted"
        D.append(w)
    X, xi = [], []
    for _ in range(5):
        w = env.word()
        i = await env.wstep(1, w)
        X.append(w)
        xi.append(i)
        assert wv[i]["o_full"] == 1 and not env.wacc(i), f"{chk}: o_full=1 at the X edge got {wv[i]}"
    for _ in range(5):
        await env.wstep(0)
    ov = [wv[i + 1]["o_overflow"] for i in xi]
    assert ov == [1] * 5, f"{chk}: o_overflow=1 at the 5 edges after X0..X4 got {ov}"
    for k in range(xi[-1] + 2, len(wv)):
        assert wv[k]["o_overflow"] == 0, f"{chk}: o_overflow back to 0 got 1 at {env.wm.t[k]} ps"
    await env.wait_dst("w", env.rm, env.wm.t[xi[0] - 1], LMAX + 3)
    await env.rsync()
    j = await env.rstep(1)
    assert env.racc(j) and env.rm.v[j]["o_rd_data"] == D[0], f"{chk}: first read returns D0 got {env.rm.v[j]}"
    await env.rstep(0)  # NNC hand fix (G3, triage B): one read at Tr (contract.json:686)
    tr = env.rm.t[j]
    await env.wsync()
    await env.wait_dst("w", env.wm, tr, LMAX + 4)
    env.lat(env.wm, tr, "o_full", 1, 0, LMAX + 4, chk, "o_full after the read of the full FIFO")
    if env.ft == DEPTH:
        env.lat(env.wm, tr, "o_full_thr", 1, 0, LMAX + 4, chk, "o_full_thr after the read of the full FIFO")
    await env.widle(5)
    await env.rsync()
    for k in range(1, DEPTH):
        j = await env.rstep(1)
        assert env.racc(j) and env.rm.v[j]["o_rd_data"] == D[k], f"{chk}: read D{k} got {env.rm.v[j]}"
    j = await env.rstep(0)
    assert env.rm.v[j]["o_empty"] == 1, f"{chk}: empty after D{DEPTH - 1}"
    await env.wsync()
    await env.widle(LMAX + 3)
    Y = env.word()
    i = await env.wstep(1, Y)
    assert env.wacc(i), f"{chk}: Y0 accepted"
    ty = env.wm.t[i]
    await env.wait_dst("w", env.rm, ty, LMAX + 4)
    v2 = env.rm.rel(ty, 2, chk)
    assert v2["o_rd_data"] == Y and v2["o_empty"] == 1, \
        f"{chk}: read edge 2 after Y0 write o_rd_data=Y0 with o_empty=1 got {v2['o_rd_data']},{v2['o_empty']}"
    env.lat(env.rm, ty, "o_empty", 1, 0, LMAX + 4, chk, "o_empty after the write of Y0")
    await env.rsync()
    j = await env.rstep(1)
    assert env.racc(j) and env.rm.v[j]["o_rd_data"] == Y, f"{chk}: Y0 read next got {env.rm.v[j]}"
    await env.rstep(0)
    if (1 << DW) >= 64:
        got = [x for _, x in env.rlog[-(DEPTH + 1):]]
        assert not any(x in got for x in X), f"{chk}: rejected words X0..X4 never read"


async def scen_021(env, chk):
    rv = env.rm.v
    await env.wsync()
    await env.widle(LMAX + 3)
    W = []
    for _ in range(DEPTH):
        w = env.word()
        i = await env.wstep(1, w)
        assert env.wacc(i), f"{chk}: write accepted"
        W.append(w)
    await env.wait_dst("w", env.rm, env.wm.t[i], LMAX + 2)
    await env.rsync()
    for k in range(DEPTH):
        j = await env.rstep(1)
        assert env.racc(j) and rv[j]["o_rd_data"] == W[k], f"{chk}: read W{k} got {rv[j]}"
    await env.rstep(0)
    await env.wsync()
    await env.widle(LMAX + 3)
    w = env.word()
    i = await env.wstep(1, w)
    assert env.wacc(i), f"{chk}: write W{DEPTH} accepted"
    W.append(w)
    await env.wait_dst("w", env.rm, env.wm.t[i], LMAX + 2)
    await env.rsync()
    j = await env.rstep(1)
    assert env.racc(j) and rv[j]["o_rd_data"] == W[DEPTH], f"{chk}: read W{DEPTH} got {rv[j]}"
    await env.rstep(0)
    js = []
    for _ in range(6):
        js.append(await env.rstep(1))
    for _ in range(3):
        await env.rstep(0)
    for j in js:
        assert rv[j]["o_empty"] == 1 and not env.racc(j), f"{chk}: o_empty=1 during underflow requests got {rv[j]}"
        assert rv[j + 1]["o_underflow"] == 1, f"{chk}: o_underflow=1 after each rejected read got {rv[j + 1]}"
    assert rv[js[-1] + 2]["o_underflow"] == 0, f"{chk}: o_underflow back to 0 got 1"
    for k in range(js[0], len(rv)):
        assert rv[k]["o_rd_data"] == W[1], f"{chk}: o_rd_data shows entry 1 (W1={hex(W[1])}) got {rv[k]['o_rd_data']}"
    await env.wsync()
    w = env.word()
    i = await env.wstep(1, w)
    assert env.wacc(i), f"{chk}: write W{DEPTH + 1} accepted"
    W.append(w)
    tw = env.wm.t[i]
    await env.wait_dst("w", env.rm, tw, LMAX + 4)
    assert env.rm.rel(tw, 1, chk)["o_rd_data"] == W[1], f"{chk}: read edge 1 after the write still shows W1"
    for k in range(2, LMAX + 5):
        assert env.rm.rel(tw, k, chk)["o_rd_data"] == w, f"{chk}: o_rd_data=W{DEPTH + 1} from read edge 2 at edge {k}"
    assert env.rm.rel(tw, 2, chk)["o_empty"] == 1, f"{chk}: o_empty still 1 at read edge 2"
    env.lat(env.rm, tw, "o_empty", 1, 0, LMAX + 4, chk, "o_empty after the write")
    await env.rsync()
    j = await env.rstep(1)
    assert env.racc(j) and rv[j]["o_rd_data"] == w, f"{chk}: read returns W{DEPTH + 1} got {rv[j]}"
    j2 = await env.rstep(0)
    assert rv[j2]["o_empty"] == 1 and rv[j2]["o_underflow"] == 0, f"{chk}: after the read o_empty=1, no underflow"


# ========================================================================= tests
@cocotb.test()
async def test_chk_014_nominal_latency(dut):
    """CHK-014: nominal crossing latency S destination edges, data shown before o_empty falls."""
    chk = "CHK-014"
    r = rng("chk014")
    per = {WCLK: 10, RCLK: 14} if r.random() < 0.5 else {WCLK: 14, RCLK: 6}
    env = Env(dut, per, ft=DEPTH, et=0)
    await env.start()
    if S == 0:
        not_verifiable(dut, chk, "PARA_AFIFO_CELL_TYPE=0 is a bypass without stages")
        return
    if not EXACT:
        not_verifiable(dut, chk, "exact latency S needs the metastability model off; window S..S+2 checked")
    d = dut
    for _ in range(10):
        await env.wsync()
        await env.widle(LMAX + 3)
        await env.until("w", lambda: len(env.Q) == 0 and val(d.o_full) == 0, 200, f"{chk}: FIFO empty")
        for _ in range(r.randint(0, 4)):
            await env.wstep(0)
        ws = [env.word()]
        i = await env.wstep(1, ws[0])
        assert env.wacc(i), f"{chk}: write into empty FIFO accepted got o_full={env.wm.v[i]['o_full']}"
        tw = env.wm.t[i]
        await env.wait_dst("w", env.rm, tw, LMAX + 4)
        env.lat(env.rm, tw, "o_empty", 1, 0, LMAX + 4, chk, "o_empty after a write into the empty FIFO")
        for k in range(2, LMAX + 5):
            got = env.rm.rel(tw, k, chk)["o_rd_data"]
            assert got == ws[0], f"{chk}: o_rd_data={hex(ws[0])} from read edge 2 got {got} at edge {k}"
        for _ in range(DEPTH - 1):
            w = env.word()
            i = await env.wstep(1, w)
            assert env.wacc(i), f"{chk}: fill write accepted"
            ws.append(w)
        i = await env.wstep(0)
        assert env.wm.v[i]["o_full"] == 1, f"{chk}: o_full=1 at once after write {DEPTH} got 0"
        await env.wait_dst("w", env.rm, env.wm.t[i - 1], LMAX + 3)
        await env.rsync()
        j = await env.rstep(1)
        assert env.racc(j) and env.rm.v[j]["o_rd_data"] == ws[0], f"{chk}: read at Tr returns first word"
        tr = env.rm.t[j]
        j = await env.rstep(0)
        assert env.rm.v[j]["o_rd_data"] == ws[1], f"{chk}: next word shown from the next read edge got {env.rm.v[j]}"
        await env.wsync()
        await env.wait_dst("w", env.wm, tr, LMAX + 4)
        env.lat(env.wm, tr, "o_full", 1, 0, LMAX + 4, chk, "o_full after a read of the full FIFO")
        await drain(env, chk)


@cocotb.test()
async def test_chk_015_model_latency_window(dut):
    """CHK-015: crossing latency S..S+2 with the metastability model, data correct, flags never early."""
    chk = "CHK-015"
    r = rng("chk015")
    env = Env(dut, {WCLK: 10, RCLK: 13}, ft=DEPTH, et=0)
    await env.start()
    dut._log.info(f"{chk}: metastability seed {_MS_SEED}, enable {_MS_EN}")
    if S == 0:
        not_verifiable(dut, chk, "PARA_AFIFO_CELL_TYPE=0 bypass")
        return
    if SYN:
        not_verifiable(dut, chk, "built with VLSIT_SYNTHESIS: no metastability model, exact latency checked")
    elif EXACT:
        not_verifiable(dut, chk, "model disabled by +AFIFO_MSYNC_EN=0: window S..S+2 not exercised")
    hw = await iso_writes(env, r, 100, chk)
    hr = await iso_reads(env, r, 100, chk)
    dut._log.info(f"{chk}: write->read latency histogram {hw}, read->write {hr}")
    if not EXACT:
        miss = [(n, L) for n, h in (("wr->rd", hw), ("rd->wr", hr)) for L in range(S, S + 3) if L not in h]
        if miss:
            not_verifiable(dut, chk, f"latencies {miss} not seen with this seed; coverage is over the run set")
    await drain(env, chk)


PAIRS16 = [(10, 10), (10, 10.3), (10, 23), (10, 50), (23, 10), (50, 10)]


@cocotb.test()
async def test_chk_016_random_traffic_ratios(dut):
    """CHK-016: random traffic, clock ratios, pointer wrap, scoreboard, idle-point INV-002, coverage."""
    chk = "CHK-016"
    r = rng("chk016")
    w, rr = r.choice(PAIRS16)
    env = Env(dut, {WCLK: w, RCLK: rr}, ft=r.randint(0, TMAX), et=r.randint(0, TMAX))
    await env.start()
    tr = Traffic(env, r)
    tr.start()
    await random_traffic(env, tr, r, 2000, chk, idle_checks=5)
    await final_drain(env, tr, chk)
    assert env.cw == env.cr, f"{chk}: every accepted word read exactly once got {env.cw} writes {env.cr} reads"
    wv, rv = env.wm.v, env.rm.v
    win = 2 * env.tslow()
    wts = [t for t, _ in env.wlog]
    conc = False
    for t, _ in env.rlog:
        k = bisect.bisect_left(wts, t - win)
        if k < len(wts) and wts[k] <= t + win:
            conc = True
            break
    cov = {"full": any(v["aw"] and v["o_full"] == 1 for v in wv),
           "empty": any(v["ar"] and v["o_empty"] == 1 for v in rv),
           "overflow": any(v["aw"] and v["o_overflow"] == 1 for v in wv),
           "underflow": any(v["ar"] and v["o_underflow"] == 1 for v in rv),
           "concurrent": conc}
    dut._log.info(f"{chk}: clocks {w}/{rr} words {env.nw} idle checks {env.idle_checks} coverage {cov}")
    assert all(cov.values()), f"{chk}: coverage full/empty/overflow/underflow/concurrent reached got {cov}"
    assert env.idle_checks >= 1, f"{chk}: at least one idle point checked got {env.idle_checks}"


@cocotb.test()
async def test_chk_017_synthesis_branch_regression(dut):
    """CHK-017: regression of the VLSIT_SYNTHESIS build (random traffic + software resets + latency)."""
    chk = "CHK-017"
    r = rng("chk017")
    env = Env(dut, None, ft=DEPTH, et=0)
    await env.start()
    if not SYN:
        not_verifiable(dut, chk, "this run is not compiled with VLSIT_SYNTHESIS; the same sequence runs on "
                                 "the simulation branch with the run's latency expectation")
    if S == 0:
        not_verifiable(dut, chk, "PARA_AFIFO_CELL_TYPE=0 bypass")
        return
    hw = await iso_writes(env, r, 10, chk)
    hr = await iso_reads(env, r, 10, chk)
    if SYN:
        assert set(hw) <= {S} and set(hr) <= {S}, f"{chk}: exact latency {S} got {hw} {hr}"
    tr = Traffic(env, r)
    tr.start()
    await random_traffic(env, tr, r, 600, chk, idle_checks=2)
    await sw_random(env, tr, r, 10, chk)
    await final_drain(env, tr, chk)
    ivs, _ = check_sw_intervals(env, chk)
    assert len(ivs) >= 10, f"{chk}: 10 software reset sequences completed got {len(ivs)}"


@cocotb.test()
async def test_chk_018_write_n_read_n_show_ahead(dut):
    """CHK-018: write N then read N with show-ahead head check; random gated phase of 200 words."""
    chk = "CHK-018"
    r = rng("chk018")
    env = Env(dut, {WCLK: 10, RCLK: 14}, ft=DEPTH, et=0)
    await env.start()
    iw0, ir0 = len(env.wm.v), len(env.rm.v)
    await scen_018(env, chk)
    tr = Traffic(env, r, 0.5, 0.7)
    tr.wgate = tr.rgate = True   # producer writes only when it saw o_full=0 (no overflow expected)
    n0, r0 = env.nw, env.nr
    tr.start()
    for _ in range(40000):
        await FallingEdge(env.wclk)
        if env.nw >= n0 + 200:
            break
    tr.wd = 0.0
    for _ in range(env.slow2w(8 * DEPTH + 200)):  # loop bound: multiplier of DEPTH plus margin nnc-literal-ok
        await FallingEdge(env.wclk)
        if len(env.Q) == 0:
            break
    await tr.stop()
    assert env.nw - n0 >= 200 and env.nr - r0 == env.nw - n0, \
        f"{chk}: phase 2 every word read once got {env.nw - n0} writes {env.nr - r0} reads"
    no_err_pulses(env, iw0, ir0, chk)


@cocotb.test()
async def test_chk_019_back_to_back_equal_clocks(dut):
    """CHK-019: back-to-back burst with equal clocks across the pointer wrap."""
    chk = "CHK-019"
    env = Env(dut, {WCLK: 10, RCLK: 10}, ft=DEPTH, et=0)
    await env.start()
    d = dut
    n = 3 * DEPTH
    strict = EXACT and DEPTH >= 2 * S + 3
    if not strict:
        not_verifiable(dut, chk, f"no-gap throughput needs nominal latency and DEPTH >= 2*S+3 (DEPTH={DEPTH}, "
                                 f"S={S}, exact={EXACT}); order and integrity still checked")
    words = [(k + 1) & DMASK for k in range(n)]
    iw0, ir0 = len(env.wm.v), len(env.rm.v)
    racc_idx = []

    async def reader():
        await env.rsync()
        started = False
        for _ in range(60 * n + 500):
            if len(racc_idx) >= n:
                break
            e = val(d.o_empty)
            if not started and e == 0:
                started = True
            en = 1 if started else 0
            if not strict and e != 0:
                en = 0
            j = await env.rstep(en)
            if env.racc(j):
                racc_idx.append(j)
        await env.rstep(0)

    rtask = cocotb.start_soon(reader())
    await env.wsync()
    widx, k = [], 0
    for _ in range(60 * n + 500):
        if k >= n:
            break
        if not strict and val(d.o_full) != 0:
            await env.wstep(0)
            continue
        i = await env.wstep(1, words[k])
        if env.wacc(i):
            widx.append(i)
            k += 1
        elif strict:
            break
    await env.wstep(0)
    await rtask
    assert len(widx) == n, f"{chk}: {n} writes accepted got {len(widx)}"
    assert len(racc_idx) == n, f"{chk}: {n} reads accepted got {len(racc_idx)}"
    if strict:
        assert widx == list(range(widx[0], widx[0] + n)), f"{chk}: writes at consecutive edges got gaps"
        assert racc_idx == list(range(racc_idx[0], racc_idx[0] + n)), f"{chk}: reads at consecutive edges got gaps"
    datas = [env.rm.v[j]["o_rd_data"] for j in racc_idx]
    assert datas == words, f"{chk}: o_rd_data 1..{n} in order got {datas}"
    no_err_pulses(env, iw0, ir0, chk)


@cocotb.test()
async def test_chk_020_overflow(dut):
    """CHK-020: writes while full dropped, o_overflow pulses, o_full falls S write edges after the read."""
    chk = "CHK-020"
    env = Env(dut, {WCLK: 10, RCLK: 14}, ft=DEPTH, et=0)
    await env.start()
    distinct_note(dut, chk)
    await scen_020(env, chk)


@cocotb.test()
async def test_chk_021_underflow(dut):
    """CHK-021: underflow leaves the read pointer, show-ahead of entry 1 while empty."""
    chk = "CHK-021"
    env = Env(dut, {WCLK: 10, RCLK: 14}, ft=DEPTH, et=0)
    await env.start()
    distinct_note(dut, chk)
    await scen_021(env, chk)


@cocotb.test()
async def test_chk_022_hw_reset_independent(dut):
    """CHK-022: independent assertion/release of the two hardware resets, clean first transfer."""
    chk = "CHK-022"
    env = Env(dut, {WCLK: 10, RCLK: 14}, ft=4, et=2)
    await env.start()
    d = dut
    for part in (1, 2):
        await env.wsync()
        tA = now()
        if part == 1:
            d.i_rst_n_wr.value = 0
            await ReadOnly()
            chk_w_reset_now(env, chk)
            for _ in range(3):
                await FallingEdge(env.rclk)
            d.i_rst_n_rd.value = 0
            await ReadOnly()
            chk_r_reset_now(env, chk)
            chk_w_reset_now(env, chk)
            for _ in range(5):
                await FallingEdge(env.rclk)
            d.i_rst_n_rd.value = 1
            for _ in range(5):
                await FallingEdge(env.wclk)
            d.i_rst_n_wr.value = 1
        else:
            d.i_rst_n_wr.value = 0
            d.i_rst_n_rd.value = 0
            await ReadOnly()
            chk_w_reset_now(env, chk)
            chk_r_reset_now(env, chk)
            for _ in range(6):
                await FallingEdge(env.wclk)
            d.i_rst_n_wr.value = 1
            for _ in range(3):
                await FallingEdge(env.rclk)
            d.i_rst_n_rd.value = 1
        await env.wsync()
        await env.widle(LMAX + 3)
        await env.rsync()
        await env.ridle(LMAX + 3)
        tB = now()
        for t, v in zip(env.wm.t, env.wm.v):
            if tA < t <= tB:
                assert (v["o_full"], v["o_overflow"], v["o_sw_rst_busy"], v["o_full_thr"]) == (0, 0, 0, int(env.ft == 0)), \
                    f"{chk}: write-domain reset values at {t} ps got {v}"
        for t, v in zip(env.rm.t, env.rm.v):
            if tA < t <= tB:
                assert (v["o_empty"], v["o_empty_thr"], v["o_underflow"]) == (1, 1, 0), \
                    f"{chk}: read-domain reset values at {t} ps got {v}"
        iw0, ir0 = len(env.wm.v), len(env.rm.v)
        await xfer_one(env, chk, env.word())
        no_err_pulses(env, iw0, ir0, chk)


@cocotb.test()
async def test_chk_023_hw_reset_during_sw_reset(dut):
    """CHK-023: hardware reset has priority over the software reset (both domains, then one)."""
    chk = "CHK-023"
    env = Env(dut, {WCLK: 10, RCLK: 14})
    await env.start()
    d = dut
    # Part 1
    await env.wsync()
    for _ in range(min(4, DEPTH)):
        i = await env.wstep(1, env.word())
        assert env.wacc(i), f"{chk}: pre-reset write accepted"
    await env.wait_dst("w", env.rm, env.wm.t[i], LMAX + 3)
    iE = await env.wstep(0, None, 0)
    tE = env.wm.t[iE]
    await env.until("w", lambda: len(env.rm.v) > env.rm.idx_after(tE) and env.rm.v[-1]["o_empty"] == 1, 300,
                    f"{chk}: o_empty=1 after the request")
    await env.widle(5)
    d.i_rst_n_wr.value = 0
    d.i_rst_n_rd.value = 0
    d.i_rst_n_sw.value = 1
    await ReadOnly()
    chk_w_reset_now(env, chk)
    chk_r_reset_now(env, chk)
    for _ in range(5):
        await FallingEdge(env.wclk)
    d.i_rst_n_wr.value = 1
    for _ in range(3):
        await FallingEdge(env.rclk)
    d.i_rst_n_rd.value = 1
    await env.wsync()
    await env.widle(3)
    assert val(d.o_sw_rst_busy) == 0 and val(d.o_full) == 0, f"{chk}: after release busy=0 o_full=0"
    await env.rsync()
    await env.ridle(2)
    assert val(d.o_empty) == 1, f"{chk}: after release o_empty=1"
    await xfer_one(env, chk, env.word())
    # Part 2: write domain only
    await env.wsync()
    for _ in range(min(2, DEPTH)):
        await env.wstep(1, env.word())
    await env.wait_dst("w", env.rm, now(), LMAX + 3)
    await env.wstep(0, None, 0)
    await env.widle(3)
    assert val(d.o_sw_rst_busy) == 1, f"{chk}: software reset in progress (busy=1)"
    env.sb_on = False
    d.i_rst_n_wr.value = 0
    d.i_rst_n_sw.value = 1
    await ReadOnly()
    chk_w_reset_now(env, chk)
    for _ in range(5):
        await FallingEdge(env.wclk)
    d.i_rst_n_wr.value = 1
    await env.wsync()
    await env.widle(20)
    await env.hw_reset()
    await xfer_one(env, chk, env.word())
    # Part 3: read domain only
    await env.wsync()
    for _ in range(min(2, DEPTH)):
        await env.wstep(1, env.word())
    await env.wait_dst("w", env.rm, now(), LMAX + 3)
    iE = await env.wstep(0, None, 0)
    tE = env.wm.t[iE]
    await env.until("w", lambda: len(env.rm.v) > env.rm.idx_after(tE) and env.rm.v[-1]["o_empty"] == 1, 300,
                    f"{chk}: o_empty=1 after the request")
    env.sb_on = False
    await env.rsync()
    d.i_rst_n_rd.value = 0
    await ReadOnly()
    chk_r_reset_now(env, chk)
    for _ in range(4):
        await FallingEdge(env.rclk)
    d.i_rst_n_rd.value = 1
    await env.wsync()
    await env.wstep(0, None, 1)
    await env.widle(20)
    await env.hw_reset()
    await xfer_one(env, chk, env.word())


@cocotb.test()
async def test_chk_024_hw_reset_mid_traffic(dut):
    """CHK-024: both hardware resets in the middle of traffic, clean restart."""
    chk = "CHK-024"
    r = rng("chk024")
    env = Env(dut, {WCLK: 10, RCLK: 14})
    await env.start()
    d = dut
    tr = Traffic(env, r, 0.8, 0.35)
    tr.start()
    target = min(5, DEPTH)
    ok = False
    for _ in range(5000):
        await FallingEdge(env.wclk)
        if len(env.Q) >= target and env.nr > 0:
            ok = True
            break
    assert ok, f"{chk}: FIFO holds {target} words with traffic in flight"
    tr.run = False
    d.i_rst_n_wr.value = 0
    d.i_rst_n_rd.value = 0
    await ReadOnly()
    chk_w_reset_now(env, chk)
    chk_r_reset_now(env, chk)
    await tr.stop()
    for _ in range(4):
        await FallingEdge(env.wclk)
    d.i_rst_n_wr.value = 1
    for _ in range(3):
        await FallingEdge(env.rclk)
    d.i_rst_n_rd.value = 1
    tA = now()
    await env.wsync()
    await env.widle(LMAX + 3)
    await env.rsync()
    await env.ridle(LMAX + 3)
    for t, v in zip(env.wm.t, env.wm.v):
        if t > tA:
            assert v["o_full"] == 0, f"{chk}: o_full=0 after the release got 1 at {t} ps"
    for t, v in zip(env.rm.t, env.rm.v):
        if t > tA:
            assert v["o_empty"] == 1, f"{chk}: o_empty=1 after the release got 0 at {t} ps"
    await xfer_one(env, chk, env.word())
    tr2 = Traffic(env, r)
    tr2.start()
    await random_traffic(env, tr2, r, 200, chk)
    await final_drain(env, tr2, chk)
    assert env.cw == env.cr, f"{chk}: post-reset words read exactly once got {env.cw} writes {env.cr} reads"


@cocotb.test()
async def test_chk_025_srst_partly_filled_held(dut):
    """CHK-025: software reset of a partly filled FIFO with i_rst_n_sw held low."""
    chk = "CHK-025"
    env = Env(dut, {WCLK: 10, RCLK: 14}, ft=6, et=2)
    await env.start()
    distinct_note(dut, chk)
    wv, wt, rv, rtm = env.wm.v, env.wm.t, env.rm.v, env.rm.t
    n0 = min(6, DEPTH)
    await env.wsync()
    D = []
    for _ in range(n0):
        w = env.word()
        i = await env.wstep(1, w)
        assert env.wacc(i), f"{chk}: pre-reset write accepted"
        D.append(w)
    await env.wait_dst("w", env.rm, wt[i], max(5, LMAX + 3))
    rd = LevelReader(env).start()
    rd.en = 1
    iE = await env.wstep(1, env.word(), 0)
    for _ in range(19):
        await env.wstep(1, env.word(), 0)
    iH = await env.wstep(1, env.word(), 1)
    m = None
    for _ in range(env.slow2w(2 * NB) + 60):
        i = await env.wstep(1, env.word(), 1)
        if wv[i]["o_sw_rst_busy"] == 0:
            m = i - 1
            break
    assert m is not None, f"{chk}: o_sw_rst_busy falls after i_rst_n_sw=1"
    for _ in range(9):
        await env.wstep(1, env.word(), 1)
    await env.wstep(0)
    await env.until("w", lambda: len(env.Q) == 0, env.slow2w(8 * DEPTH + 100), f"{chk}: post-reset words drained")  # nnc-literal-ok
    await env.wait_dst("w", env.rm, now(), LMAX + 3)
    await rd.stop()
    ft0 = int(env.ft == 0)
    assert wv[iE]["i_rst_n_sw"] == 0 and wv[iE]["o_sw_rst_busy"] == 0, f"{chk}: first low sample at W0"
    for k in range(iE, m + 1):
        v = wv[k]
        assert v["o_full"] == 1 and v["o_full_thr"] == ft0 and not env.wacc(k), \
            f"{chk}(1): blocked write edge o_full=1 o_full_thr={ft0} no accept got {v} at {wt[k]} ps"
    for k in range(iE, m + 2):
        assert wv[k]["o_overflow"] == 0, f"{chk}(1): no o_overflow pulse while blocked at {wt[k]} ps"
    for k in range(iE + 1, m + 1):
        assert wv[k]["o_sw_rst_busy"] == 1, f"{chk}(2): busy=1 through the hold got 0 at {wt[k]} ps"
    assert m - iH >= S + 1, f"{chk}(5): m >= H+{S + 1} got m-H={m - iH}"
    b = env.rm.idx_after(wt[iE])
    for k in range(1, S + 1):
        a = b + k - 1
        left = n0 - sum(1 for (t, _) in env.rlog if t < rtm[a])
        if left > 0 and rv[a]["i_rd_en"] == 1:
            assert rv[a]["o_empty"] == 0 and env.racc(a), f"{chk}(3): read at read edge {k} after W0 accepted got {rv[a]}"
    blk = b + LMAX
    rf = next((a for a in range(blk + 1, len(rv)) if rv[a]["o_underflow"] == 1), None)
    assert rf is not None, f"{chk}(5): o_underflow pulses come back after the read release"
    R = rf - 2
    assert rtm[R] > wt[iH], f"{chk}(4): o_underflow stays 0 while i_rst_n_sw=0 (resumed at {rtm[rf]} ps)"
    assert rtm[R] < wt[m], f"{chk}(5): read release edge {rtm[R]} ps earlier than busy fall {wt[m]} ps"
    for a in range(blk, R + 1):
        assert rv[a]["o_empty"] == 1 and rv[a]["o_empty_thr"] == 1 and not env.racc(a), \
            f"{chk}(3): read side blocked o_empty=1 o_empty_thr=1 got {rv[a]} at {rtm[a]} ps"
    nrd = sum(1 for t in rtm if wt[iH] < t <= wt[m])
    assert nrd <= NB, f"{chk}(6): busy falls within {NB} read edges after H got {nrd}"
    v = wv[m + 1]
    assert v["o_full"] == 0 and v["o_full_thr"] == ft0 and env.wacc(m + 1), \
        f"{chk}(6,8): at m+1 o_full=0 o_full_thr={ft0} and P0 accepted got {v}"
    P0, tP = v["i_wr_data"], wt[m + 1]
    a1 = env.rm.idx_after(tP)
    for a in range(R + 1, a1 + 1):
        assert rv[a]["o_rd_data"] == D[0] and rv[a]["o_empty"] == 1, \
            f"{chk}(7): o_rd_data=D0 and o_empty=1 before P0 crosses got {rv[a]} at {rtm[a]} ps"
    v2 = rv[a1 + 1]
    assert v2["o_rd_data"] == P0 and v2["o_empty"] == 1, f"{chk}(8): read edge 2 after P0 o_rd_data=P0 o_empty=1 got {v2}"
    seq = [rv[a1 + j]["o_empty"] for j in range(LMAX + 1)]
    assert 0 in seq and S <= seq.index(0) <= LMAX, f"{chk}(8): o_empty falls after read edge {S}..{LMAX} got {seq}"
    post = [x for (t, x) in env.rlog if t > wt[m]]
    assert post and post[0] == P0, f"{chk}(8): first post-reset read returns P0 got {post[:1]}"


@cocotb.test()
async def test_chk_026_srst_one_cycle_pulse_full(dut):
    """CHK-026: one-cycle i_rst_n_sw pulse on a full FIFO in overflow."""
    chk = "CHK-026"
    env = Env(dut, {WCLK: 10, RCLK: 14}, ft=min(6, DEPTH), et=0)
    await env.start()
    distinct_note(dut, chk)
    wv, wt, rv, rtm = env.wm.v, env.wm.t, env.rm.v, env.rm.t
    rd = LevelReader(env).start()
    await env.wsync()
    D = []
    for _ in range(DEPTH):
        w = env.word()
        i = await env.wstep(1, w)
        assert env.wacc(i), f"{chk}: fill write accepted"
        D.append(w)
    iF = i + 1
    for _ in range(4):
        await env.wstep(1, env.word(), 1)
    iW = await env.wstep(1, env.word(), 0)
    m = None
    for _ in range(env.slow2w(2 * NB) + 60):
        i = await env.wstep(1, env.word(), 1)
        if i > iW + 1 and wv[i]["o_sw_rst_busy"] == 0:
            m = i - 1
            rd.en = 1
            break
    assert m is not None, f"{chk}: busy falls after the one-cycle pulse"
    for _ in range(2 * DEPTH):
        await env.wstep(1, env.word(), 1)
    await env.wstep(0)
    await env.until("w", lambda: len(env.Q) == 0, env.slow2w(8 * DEPTH + 100), f"{chk}: post-reset words drained")  # nnc-literal-ok
    await env.wait_dst("w", env.rm, now(), LMAX + 3)
    await rd.stop()
    for k in range(iF, iW):
        v = wv[k]
        assert v["o_full"] == 1 and not env.wacc(k) and v["o_full_thr"] == int(DEPTH >= env.ft), \
            f"{chk}: before the block o_full=1 o_full_thr=1 got {v}"
    for k in range(iF + 1, iW + 1):
        assert wv[k]["o_overflow"] == 1, f"{chk}: o_overflow=1 up to and including W1 got 0 at {wt[k]} ps"
    for k in range(iW + 1, m + 2):
        assert wv[k]["o_overflow"] == 0, f"{chk}: no o_overflow after W1 while blocked got 1 at {wt[k]} ps"
    for k in range(iW, m + 1):
        assert wv[k]["o_full"] == 1 and wv[k]["o_full_thr"] == int(env.ft == 0) and not env.wacc(k), \
            f"{chk}: blocked: o_full=1 o_full_thr=0 got {wv[k]}"
    assert wv[iW]["o_sw_rst_busy"] == 0, f"{chk}: busy=0 at W1"
    for k in range(iW + 1, m + 1):
        assert wv[k]["o_sw_rst_busy"] == 1, f"{chk}: busy=1 from W1+1 got 0 at {wt[k]} ps"
    nrd = sum(1 for t in rtm if wt[iW] < t <= wt[m])
    assert nrd <= NB, f"{chk}: busy falls within {NB} read edges after W1 got {nrd}"
    v = wv[m + 1]
    assert v["o_full"] == 0 and v["o_full_thr"] == int(env.ft == 0) and env.wacc(m + 1), \
        f"{chk}: at the busy fall o_full=0 o_full_thr=0 got {v}"
    P0, tP = v["i_wr_data"], wt[m + 1]
    a1 = env.rm.idx_after(tP)
    blk = env.rm.ia(wt[iW], LMAX + 1)
    for a in range(blk, a1 + S):
        assert rv[a]["o_empty"] == 1, f"{chk}: o_empty=1 from read edge {LMAX + 1} after W1 got 0 at {rtm[a]} ps"
    assert rv[a1]["o_rd_data"] == D[0], f"{chk}: o_rd_data=D0 before P0 crosses got {rv[a1]['o_rd_data']}"
    post = [x for (t, x) in env.rlog if t > wt[iW]]
    assert post and post[0] == P0, f"{chk}: first word read after the release is P0 got {post[:1]}"


@cocotb.test()
async def test_chk_027_read_released_first(dut):
    """CHK-027: read side released before the write side, seen through o_underflow."""
    chk = "CHK-027"
    r = rng("chk027")
    env = Env(dut, {WCLK: 10, RCLK: 6})
    await env.start()
    wv, wt, rv, rtm = env.wm.v, env.wm.t, env.rm.v, env.rm.t
    rd = LevelReader(env).start()
    rd.en = 1
    await env.wsync()
    for _ in range(5):
        await env.widle(r.randint(4, 14))
        iW = await env.wstep(0, None, 0)
        m = None
        for _ in range(NB + 60):
            i = await env.wstep(0, None, 1)
            if i > iW + 1 and wv[i]["o_sw_rst_busy"] == 0:
                m = i - 1
                break
        assert wv[iW + 1]["o_sw_rst_busy"] == 1, f"{chk}: busy rises after W1"
        assert m is not None, f"{chk}: busy falls"
        await env.wait_dst("w", env.rm, wt[m], 14)
        b = env.rm.idx_after(wt[iW])

        def u(k):
            return rv[b + k - 1]["o_underflow"]

        for k in range(2, S + 2):
            assert u(k) == 1, f"{chk}: requests at read edges 1..{S} give o_underflow=1 at edge {k} got {u(k)}"
        assert u(LMAX + 2) == 0, f"{chk}: blocked request gives no underflow at edge {LMAX + 2}"
        rf = next((k for k in range(LMAX + 2, len(rv) - b + 1) if u(k) == 1), None)
        assert rf is not None, f"{chk}: underflow resumes after the read release"
        R = rf - 2
        assert R >= 1 and rtm[b + R - 1] < wt[m], f"{chk}: read release edge R before busy fall got R time {rtm[b + R - 1]} m {wt[m]}"
        last = min(len(rv) - b, rf + 10)
        for k in range(rf, last + 1):
            assert u(k) == 1, f"{chk}: o_underflow=1 at every edge from R+2 got 0 at edge {k}"
        for k in range(1, last + 1):
            assert rv[b + k - 1]["o_empty"] == 1, f"{chk}: o_empty=1 throughout got 0 at edge {k}"
        assert (m + 1) - iW <= NB, f"{chk}: busy falls within {NB} write edges after W1 got {(m + 1) - iW}"
        assert wv[m + 1]["o_full"] == 0, f"{chk}: o_full=0 after the busy fall"
    await rd.stop()


@cocotb.test()
async def test_chk_028_srst_reasserted_in_rel(dut):
    """CHK-028: i_rst_n_sw asserted again in REL: one-cycle busy gap, second sequence, no write accepted."""
    chk = "CHK-028"
    env = Env(dut, {WCLK: 10, RCLK: 12}, ft=DEPTH, et=0)
    await env.start()
    wv, wt, rv, rtm = env.wm.v, env.wm.t, env.rm.v, env.rm.t
    rd = LevelReader(env).start()
    await env.wsync()
    for _ in range(min(3, DEPTH - 1)):
        i = await env.wstep(1, env.word())
        assert env.wacc(i), f"{chk}: initial write accepted"
    await env.wait_dst("w", env.rm, now(), LMAX + 3)
    rd.en = 1
    hold = 20 + 4 * LMAX
    iE = await env.wstep(1, env.word(), 0)
    for _ in range(hold - 1):
        await env.wstep(1, env.word(), 0)
    iH = await env.wstep(1, env.word(), 1)
    g = None
    for _ in range(env.slow2w(2 * NB) + 60):
        i = await env.wstep(1, env.word(), 0)
        if g is None:
            if wv[i]["o_sw_rst_busy"] == 0:
                g = i
        else:
            break
    assert g is not None, f"{chk}: first sequence returns to RUN (busy gap)"
    for _ in range(20):
        await env.wstep(1, env.word(), 0)
    await env.wstep(1, env.word(), 1)
    m2 = None
    for _ in range(env.slow2w(2 * NB) + 60):
        i = await env.wstep(1, env.word(), 1)
        if wv[i]["o_sw_rst_busy"] == 0:
            m2 = i - 1
            break
    assert m2 is not None, f"{chk}: second sequence ends"
    for _ in range(4):
        await env.wstep(1, env.word(), 1)
    await env.wstep(0)
    await env.until("w", lambda: len(env.Q) == 0, env.slow2w(8 * DEPTH + 100), f"{chk}: post-reset words drained")  # nnc-literal-ok
    await env.wait_dst("w", env.rm, now(), LMAX + 3)
    await rd.stop()
    assert wv[iE]["o_sw_rst_busy"] == 0 and wv[iE]["i_rst_n_sw"] == 0, f"{chk}: first low sample"
    assert g > iH and wv[g + 1]["o_sw_rst_busy"] == 1, f"{chk}: busy 1 again right after the gap edge"
    zeros = [k for k in range(iE + 1, m2 + 1) if wv[k]["o_sw_rst_busy"] == 0]
    assert zeros == [g], f"{chk}: busy=0 at exactly one write edge between the sequences got {len(zeros)}"
    for k in range(iE, m2 + 1):
        assert wv[k]["o_full"] == 1 and not env.wacc(k), f"{chk}: o_full=1, no write accepted at {wt[k]} ps"
    for k in range(iE, m2 + 2):
        assert wv[k]["o_overflow"] == 0, f"{chk}: o_overflow stays 0 got 1 at {wt[k]} ps"
    assert wv[m2 + 1]["o_full"] == 0 and env.wacc(m2 + 1), f"{chk}: at m2+1 o_full=0 got {wv[m2 + 1]}"
    bg = env.rm.idx_after(wt[g])
    a0 = env.rm.idx_after(wt[iH])
    assert any(rv[a]["o_underflow"] == 1 for a in range(a0, bg + S + 1)), \
        f"{chk}: o_underflow comes back after the first read release"
    blk2 = bg + LMAX
    assert rv[blk2 + 1]["o_underflow"] == 0, f"{chk}: o_underflow stops from read edge {LMAX + 2} after the second rise"
    r2 = next((a for a in range(blk2 + 1, len(rv)) if rv[a]["o_underflow"] == 1), None)
    assert r2 is not None and rtm[r2 - 2] < wt[m2], f"{chk}: second read release before m2"
    post = [x for (t, x) in env.rlog if t > wt[m2]]
    assert post and post[0] == wv[m2 + 1]["i_wr_data"], f"{chk}: first post-reset word read first got {post[:1]}"


PAIRS29 = [(10, 10.3), (10, 23), (23, 10), (10, 37)]


@cocotb.test()
async def test_chk_029_srst_random_traffic(dut):
    """CHK-029: software resets under random traffic; no blocked access, no data error, no deadlock."""
    chk = "CHK-029"
    r = rng("chk029")
    w, rr = r.choice(PAIRS29)
    env = Env(dut, {WCLK: w, RCLK: rr}, ft=r.randint(0, TMAX), et=r.randint(0, TMAX))
    await env.start()
    dut._log.info(f"{chk}: clocks {w}/{rr}, model seed {_MS_SEED} enable {_MS_EN}")
    tr = Traffic(env, r)
    tr.start()
    await sw_random(env, tr, r, 30, chk)
    await final_drain(env, tr, chk)
    ivs, nrel = check_sw_intervals(env, chk)
    assert len(ivs) >= 30, f"{chk}: at least 30 sequences got {len(ivs)}"
    assert nrel > 0, f"{chk}: release order checked with i_rd_en held in at least one sequence got 0"


@cocotb.test()
async def test_chk_030_after_srst_like_hw_reset(dut):
    """CHK-030: after a software reset the FIFO behaves as after a hardware reset (CHK-018/020/021)."""
    chk = "CHK-030"
    env = Env(dut, {WCLK: 10, RCLK: 14}, ft=DEPTH, et=0)
    await env.start()
    distinct_note(dut, chk)
    d = dut
    wv, wt = env.wm.v, env.wm.t
    await env.wsync()
    for _ in range(min(5, DEPTH)):
        i = await env.wstep(1, env.word())
        assert env.wacc(i), f"{chk}: pre-reset write accepted"
    await env.wait_dst("w", env.rm, wt[i], LMAX + 3)
    iE = await env.wstep(0, None, 0)
    m = None
    for _ in range(env.slow2w(2 * NB) + 60):
        i = await env.wstep(0, None, 1)
        if i > iE + 1 and wv[i]["o_sw_rst_busy"] == 0:
            m = i - 1
            break
    assert m is not None, f"{chk}: software reset completes"
    v = wv[m + 1]
    assert v["o_full"] == 0 and v["o_full_thr"] == int(env.ft == 0), f"{chk}: after the release o_full=0 got {v}"
    await env.rsync()
    await env.ridle(2)
    assert val(d.o_empty) == 1 and val(d.o_empty_thr) == 1, f"{chk}: after the release o_empty=1 o_empty_thr=1"
    assert not any(wt[iE] < t <= wt[m] for t, _ in env.rlog), f"{chk}: no read during the reset"
    D = await scen_018(env, chk)
    post = [x for (t, x) in env.rlog if t > wt[m]]
    assert post and post[0] == D[0], f"{chk}: first post-reset word read first got {post[:1]}"
    await scen_020(env, chk)
    await scen_021(env, chk)


@cocotb.test()
async def test_chk_031_clock_stop_during_srst(dut):
    """CHK-031: the handshake waits while a clock is stopped and completes after the restart."""
    chk = "CHK-031"
    env = Env(dut, {WCLK: 10, RCLK: 14})
    await env.start()
    d = dut
    wv, wt = env.wm.v, env.wm.t
    await env.wsync()
    for _ in range(min(3, DEPTH)):
        await env.wstep(1, env.word())
    iE = await env.wstep(1, env.word(), 0)
    i = await env.wstep(1, env.word(), 1)
    assert wv[i]["o_sw_rst_busy"] == 1, f"{chk}: busy=1 after the pulse"
    await _maybe(stop_clock(RCLK))
    idx = []
    for _ in range(60):
        idx.append(await env.wstep(1, env.word(), 1))
    for k in idx:
        v = wv[k]
        assert v["o_sw_rst_busy"] == 1 and v["o_full"] == 1 and not env.wacc(k) and v["o_overflow"] == 0, \
            f"{chk}: i_clk_rd stopped: busy=1 o_full=1 no write no overflow got {v}"
    await _maybe(resume_clock(RCLK))
    tres = now()
    m = None
    for _ in range(env.slow2w(2 * NB) + 60):
        i = await env.wstep(0)
        if wv[i]["o_sw_rst_busy"] == 0:
            m = i - 1
            break
    assert m is not None and wt[m + 1] - tres <= (NB + 1) * env.tslow(), f"{chk}: busy falls within {NB} slow edges"
    assert wv[m + 1]["o_full"] == 0, f"{chk}: o_full=0 after the restart"
    await env.rsync()
    await env.ridle(LMAX + 3)
    assert val(d.o_empty) == 1, f"{chk}: FIFO empty after the reset"
    await xfer_one(env, chk, env.word())
    # second sequence: stop the write clock
    await env.wsync()
    for _ in range(min(2, DEPTH)):
        await env.wstep(1, env.word())
    await env.wait_dst("w", env.rm, now(), LMAX + 3)
    await env.wstep(0, None, 0)
    await env.wstep(0, None, 1)
    await env.rsync()
    await env.until("r", lambda: val(d.o_empty) == 1, 60, f"{chk}: request reaches the read side")
    await _maybe(stop_clock(WCLK))
    js = []
    for _ in range(60):
        js.append(await env.rstep(1))
    for j in js:
        assert env.rm.v[j]["o_empty"] == 1 and not env.racc(j), f"{chk}: i_clk_wr stopped: o_empty=1, no read"
    d.i_rd_en.value = 0
    await _maybe(resume_clock(WCLK))
    tres = now()
    await env.wsync()
    m = None
    for _ in range(env.slow2w(2 * NB) + 60):
        i = await env.wstep(0)
        if wv[i]["o_sw_rst_busy"] == 0:
            m = i - 1
            break
    assert m is not None and wt[m + 1] - tres <= (NB + 1) * env.tslow(), f"{chk}: busy falls within {NB} slow edges"
    assert wv[m + 1]["o_full"] == 0, f"{chk}: o_full=0 after the restart"
    await env.rsync()
    await env.ridle(LMAX + 3)
    assert val(d.o_empty) == 1, f"{chk}: FIFO empty after the reset"
    await xfer_one(env, chk, env.word())


@cocotb.test()
async def test_chk_032_threshold_flags(dut):
    """CHK-032: o_full_thr / o_empty_thr while filling and draining, for several threshold pairs."""
    chk = "CHK-032"
    # Spec pairs (0,0),(3,5),(8,8),(9,15),(15,1),(6,2) for depth 8 / 4-bit thresholds, expressed with the
    # parameters: (depth, depth), (depth+1, max threshold), (max threshold, 1); fixed spec values clamped by thr().
    pairs = [(0, 0), (3, 5), (DEPTH, DEPTH), (DEPTH + 1, TMAX), (TMAX, 1), (6, 2)]  # spec threshold values nnc-literal-ok
    pairs = [(thr(a), thr(b)) for a, b in pairs]
    env = Env(dut, {WCLK: 10, RCLK: 14}, *pairs[0])
    await env.start()
    d = dut
    for pi, (f0, e0) in enumerate(pairs):
        if pi > 0:
            env.ft, env.et = thr(f0), thr(e0)
            await env.hw_reset()
        ft, et = env.ft, env.et
        await env.wsync()
        await env.widle(2)
        assert val(d.o_full_thr) == int(ft == 0), f"{chk}: after reset o_full_thr=(thr==0) for ft={ft}"
        await env.rsync()
        await env.ridle(1)
        assert val(d.o_empty_thr) == 1, f"{chk}: after reset o_empty_thr=1"
        await env.wsync()
        for k in range(1, DEPTH + 1):
            i = await env.wstep(1, env.word())
            assert env.wacc(i), f"{chk}: write {k} accepted"
            tw = env.wm.t[i]
            i2 = await env.wstep(0)
            assert env.wm.v[i2]["o_full_thr"] == int(k >= ft), \
                f"{chk}: count {k} ft {ft} o_full_thr={int(k >= ft)} at once got {env.wm.v[i2]['o_full_thr']}"
            await env.wait_dst("w", env.rm, tw, LMAX + 4)
            env.lat(env.rm, tw, "o_empty_thr", int(k - 1 <= et), int(k <= et), LMAX + 4, chk,
                    f"o_empty_thr after write to count {k} (et={et})")
        await env.rsync()
        for k in range(DEPTH - 1, -1, -1):
            j = await env.rstep(1)
            assert env.racc(j), f"{chk}: read leaving {k} accepted"
            tr = env.rm.t[j]
            j2 = await env.rstep(0)
            assert env.rm.v[j2]["o_empty_thr"] == int(k <= et), \
                f"{chk}: count {k} et {et} o_empty_thr={int(k <= et)} at once got {env.rm.v[j2]['o_empty_thr']}"
            await env.wsync()
            await env.wait_dst("w", env.wm, tr, LMAX + 4)
            env.lat(env.wm, tr, "o_full_thr", int(k + 1 >= ft), int(k >= ft), LMAX + 4, chk,
                    f"o_full_thr after read to count {k} (ft={ft})")
            await env.rsync()


@cocotb.test()
async def test_regression_random(dut):
    """CHK-001..CHK-013 exercise: random traffic, software resets, hardware reset, random thresholds."""
    chk = "REGRESSION"
    r = rng("regression")
    env = Env(dut, None, ft=r.randint(0, TMAX), et=r.randint(0, TMAX))
    await env.start()
    tr = Traffic(env, r)
    tr.start()
    await random_traffic(env, tr, r, 800, "CHK-016", idle_checks=3)
    await sw_random(env, tr, r, 8, "CHK-029")  # number of software-reset sequences nnc-literal-ok
    await random_traffic(env, tr, r, 300, "CHK-016")
    await tr.stop()
    env.ft, env.et = r.randint(0, TMAX), r.randint(0, TMAX)
    await env.hw_reset()
    tr.start()
    await random_traffic(env, tr, r, 600, "CHK-016", idle_checks=2)
    await sw_random(env, tr, r, 4, "CHK-029")
    await final_drain(env, tr, chk)
    ivs, nrel = check_sw_intervals(env, "CHK-011")
    dut._log.info(f"{chk}: words {env.nw} reads {env.nr} sw sequences {len(ivs)} release-order checks {nrel} "
                  f"idle checks {env.idle_checks}")
    assert len(ivs) >= 12, f"{chk}: 12 software reset sequences completed got {len(ivs)}"

"""cocotb 2.1 testbench for m_vlsit_afifo_top (dual-clock FIFO with software reset).

Structure
- Mon: one monitor per clock domain. At each falling edge it fires an Event, and the drivers drive right
  after it. In ReadOnly it samples every port of its domain, which gives the values that the next rising
  edge samples. It stamps the time of that rising edge and calls the scoreboard in true rising-edge time
  order. Record n of a domain is the n-th rising edge of that clock seen by the monitor.
- SB: reference model of CHK-005/CHK-006: queue Q, pre-reset list P, software-reset discard at read edge
  S+3, and clearing on a hardware reset.
- Writer/Reader: random traffic models. Directed tests drive through TB.w / TB.r, always right after a
  falling edge of the domain that owns the signal.
Cross-domain effects are checked as order plus a window of destination edges: exactly S with the
metastability model off, S..S+2 with the model on (DEC-012).
"""
import inspect
import cocotb
from bisect import bisect_right
from collections import deque, Counter
from cocotb.triggers import FallingEdge, RisingEdge, ReadOnly, Event
from cocotb.utils import get_sim_time
from nnc_cocotb import *

try:
    CLOCKS
except NameError:
    CLOCKS = {"i_clk_wr": 10, "i_clk_rd": 14}


def _par(name, dflt):
    try:
        v = PARAMS.get(name)
        return dflt if v is None else int(v)
    except Exception:
        return dflt


DEPTH = _par("PARA_AFIFO_DEPTH", 8)
DW = _par("PARA_AFIFO_DATA_W", 32)
CT = _par("PARA_AFIFO_CELL_TYPE", 2)
PTR_W = _par("LPARA_PTR_W", (DEPTH - 1).bit_length() + 1)
TMAX = (1 << PTR_W) - 1
MASK = (1 << DW) - 1
S = {0: 0, 1: 2, 2: 2, 3: 3, 4: 4}.get(CT, 2)
SYN = "VLSIT_SYNTHESIS" in list(DEFINES or [])
_EN = plusarg("AFIFO_MSYNC_EN")
MS = (_EN is not None and _EN.strip() not in ("", "0")) and not SYN
EXTRA = 2 if MS else 0
LMAX = S + EXTRA
EXACT = EXTRA == 0
DENS = (0.1, 0.25, 0.5, 0.75, 0.9, 1.0)
WCLK, RCLK = "i_clk_wr", "i_clk_rd"
WR_SIGS = ("i_rst_n_wr", "i_wr_en", "i_wr_data", "i_full_thr", "i_rst_n_sw",
           "o_sw_rst_busy", "o_full", "o_full_thr", "o_overflow")
RD_SIGS = ("i_rst_n_rd", "i_rd_en", "i_empty_thr", "o_rd_data", "o_empty", "o_empty_thr", "o_underflow")


def hx(v):
    return hex(v) if isinstance(v, int) else str(v)


async def _maybe(res):
    if inspect.isawaitable(res):
        await res


def _param(**kw):
    p = getattr(cocotb, "parametrize", None)
    return p(**kw) if p else (lambda f: f)


def note_model(dut, cid, need_off=True):
    seed = plusarg("AFIFO_MSYNC_SEED")
    dut._log.info(f"{cid}: S={S} model={'on' if MS else 'off'} seed={seed} VLSIT_SYNTHESIS={SYN} DEPTH={DEPTH}")
    if need_off and MS:
        not_verifiable(dut, cid, f"this run enables the metastability model (+AFIFO_MSYNC_EN, seed {seed}); "
                       f"the exact {S}-edge cross-domain counts need the model off; only the window "
                       f"{S}..{LMAX} destination edges is checked here")
    if S < 2:
        not_verifiable(dut, cid, "PARA_AFIFO_CELL_TYPE=0 (bypass): the latencies of Sections 10.3/10.4 apply "
                       "to the options 1..4 only")


def lead(E, key, old):
    L = 0
    while L < len(E) and E[L][key] == old:
        L += 1
    return L


def chk_lat(L, cid, what):
    ok = (L == S) if EXACT else (L is not None and S <= L <= LMAX)
    exp = f"{S}" if EXACT else f"{S}..{LMAX}"
    assert ok, f"{cid}: {what}: expected the change after destination edge {exp} got {L}"


def chk_trans(E, key, old, new, cid, what):
    if old == new:
        assert all(e[key] == old for e in E), f"{cid}: {what}: expected constant {old} got {[e[key] for e in E]}"
        return
    L = lead(E, key, old)
    chk_lat(L, cid, what)
    assert all(e[key] == new for e in E[L:]), f"{cid}: {what}: expected {new} after the change got {[e[key] for e in E]}"


def find_fall(W, start):
    for j in range(max(start, 0), len(W) - 1):
        if W[j]["o_sw_rst_busy"] == 1 and W[j + 1]["o_sw_rst_busy"] == 0:
            return j
    return None


async def fall_rec(tb, start, cid, lim=60):
    """Return the record index m of the busy fall (busy=1 at m, 0 at m+1), waiting until the records exist."""
    for _ in range(lim):
        m = find_fall(tb.wr.recs, start)
        if m is not None:
            return m
        await tb.wr.tick()
    assert False, f"{cid}: o_sw_rst_busy fall (1 -> 0) not found in the write-edge records"


def ncount(trs, t0, t1):
    return bisect_right(trs, t1) - bisect_right(trs, t0)


class Mon:
    def __init__(self, dut, clk_name, sigs):
        self.clk = getattr(dut, clk_name)
        self.h = [(s, getattr(dut, s)) for s in sigs]
        self.recs, self.trs, self.cbs = [], [], []
        self.n = 0
        self.ev = Event()
        cocotb.start_soon(self._run())

    async def _run(self):
        while True:
            await FallingEdge(self.clk)
            self.n = len(self.recs)
            ev, self.ev = self.ev, Event()
            ev.set()
            await ReadOnly()
            r = {k: val(h) for k, h in self.h}
            r["i"] = self.n
            r["t"] = get_sim_time(unit="ps")
            self.recs.append(r)
            await RisingEdge(self.clk)
            r["tr"] = get_sim_time(unit="ps")
            self.trs.append(r["tr"])
            for cb in self.cbs:
                cb(r)

    async def tick(self, k=1):
        for _ in range(k):
            await self.ev.wait()
        return self.n


class SB:
    """Reference model of CHK-005 / CHK-006."""

    def __init__(self, tb):
        self.tb = tb
        self.Q, self.P = deque(), deque()
        self.errs, self.reads, self.racc, self.wacc = [], [], [], []
        self.en = True
        self.prev = None
        self.pc = None

    def clear(self):
        self.Q.clear()
        self.P.clear()
        self.prev = None
        self.pc = None

    def err(self, m):
        if len(self.errs) < 30:
            cocotb.log.error(m)
        self.errs.append(m)

    def live(self):
        d = self.tb.dut
        return self.en and val(d.i_rst_n_wr) == 1 and val(d.i_rst_n_rd) == 1

    def on_wr(self, r):
        if r["i_rst_n_wr"] != 1 or not self.live():
            self.clear()
            return
        p, self.prev = self.prev, r
        if p is not None and p["o_sw_rst_busy"] == 0 and r["o_sw_rst_busy"] == 1:
            self.P.extend(self.Q)
            self.Q.clear()
            trs = self.tb.rd.trs
            self.pc = len(trs) - bisect_right(trs, p["tr"])
            if self.pc >= S + 3:
                self.P.clear()
                self.pc = None
        n = len(self.Q)
        if n > DEPTH:
            self.err(f"CHK-006: occupancy {n} > DEPTH at write edge t={r['tr']}ps")
        if n == DEPTH and r["o_full"] != 1:
            self.err(f"CHK-006: occupancy = DEPTH but o_full={r['o_full']} at write edge t={r['tr']}ps")
        if r["i_wr_en"] == 1 and r["o_full"] == 0:
            self.Q.append(r["i_wr_data"])
            self.wacc.append(r)

    def on_rd(self, r):
        if r["i_rst_n_rd"] != 1 or not self.live():
            self.clear()
            return
        if self.pc is not None:
            self.pc += 1
            if self.pc >= S + 3:
                self.P.clear()
                self.pc = None
        if r["o_empty"] == 0:
            src = self.P if self.P else self.Q
            if not src:
                self.err(f"CHK-006: o_empty=0 with nothing written at read edge t={r['tr']}ps")
                return
            h = src[0]
            if r["o_rd_data"] != h:
                self.err(f"CHK-005: o_rd_data expected head {hx(h)} got {hx(r['o_rd_data'])} at t={r['tr']}ps")
            if r["i_rd_en"] == 1:
                src.popleft()
                self.reads.append(h)
                self.racc.append(r)


class Writer:
    def __init__(self, tb, r):
        self.tb, self.r = tb, r
        self.d, self.gate, self.run = 0.0, False, True
        self.plan = deque()

    async def loop(self):
        dut = self.tb.dut
        while True:
            await self.tb.wr.tick()
            sw = self.plan.popleft() if self.plan else 1
            en = 1 if (self.run and self.r.random() < self.d and not (self.gate and val(dut.o_full) == 1)) else 0
            dut.i_rst_n_sw.value = sw
            dut.i_wr_en.value = en
            dut.i_wr_data.value = self.r.getrandbits(DW)


class Reader:
    def __init__(self, tb, r):
        self.tb, self.r = tb, r
        self.d, self.gate, self.run = 0.0, False, True

    async def loop(self):
        dut = self.tb.dut
        while True:
            await self.tb.rd.tick()
            en = 1 if (self.run and self.r.random() < self.d and not (self.gate and val(dut.o_empty) == 1)) else 0
            dut.i_rd_en.value = en


class TB:
    def __init__(self, dut, periods=None):
        self.dut = dut
        self.periods = periods
        per = dict(CLOCKS)
        per.update(periods or {})
        self.pw = float(per.get(WCLK, 10))
        self.pr = float(per.get(RCLK, 14))
        self.slow_ps = int(max(self.pw, self.pr) * 1000)
        self.wr = Mon(dut, WCLK, WR_SIGS)
        self.rd = Mon(dut, RCLK, RD_SIGS)
        self.sb = SB(self)
        self.sb.en = False          # the DUT state is unknown until this test's own reset (init enables it)
        self.wr.cbs.append(self.sb.on_wr)
        self.rd.cbs.append(self.sb.on_rd)
        self.W = self.R = None
        self.ft, self.et = DEPTH & TMAX, 0

    async def init(self, ft=None, et=0):
        d = self.dut
        await _maybe(start_clock(d, periods=self.periods) if self.periods else start_clock(d))
        self.ft = (DEPTH if ft is None else ft) & TMAX
        self.et = et & TMAX
        # The thresholds are static (REQ-FUNC-010, CDC-004): reset_dut drives them together with the reset
        # assertion, never while the FIFO is in use.
        d.i_rst_n_sw.value = 1
        d.i_wr_en.value = 0
        d.i_rd_en.value = 0
        d.i_wr_data.value = 0
        await reset_dut(d, cycles=5, idle={"i_full_thr": self.ft, "i_empty_thr": self.et, "i_rst_n_sw": 1})
        await self.settle(3)
        self.sb.clear()
        self.sb.en = True

    def models(self, r):
        if self.W is None:
            self.W, self.R = Writer(self, r), Reader(self, r)
            cocotb.start_soon(self.W.loop())
            cocotb.start_soon(self.R.loop())
        self.W.run = self.R.run = True
        return self.W, self.R

    async def w(self, en=0, data=0, sw=None):
        n = await self.wr.tick()
        self.dut.i_wr_en.value = en
        self.dut.i_wr_data.value = data & MASK
        if sw is not None:
            self.dut.i_rst_n_sw.value = sw
        return n

    async def r(self, en=0):
        n = await self.rd.tick()
        self.dut.i_rd_en.value = en
        return n

    async def idle(self, nw=0, nr=0):
        if nw:
            await self.wr.tick(nw)
        if nr:
            await self.rd.tick(nr)

    async def settle(self, k):
        tw, tr = self.wr.n + k, self.rd.n + k
        for _ in range(40 * k + 2000):
            if self.wr.n >= tw and self.rd.n >= tr:
                return
            await (self.wr.tick() if self.wr.n < tw else self.rd.tick())
        assert False, "CHK-016: clocks did not advance (settle timeout)"

    async def rec(self, mon, i):
        for _ in range(max(i - len(mon.trs), 0) + 50):   # a record already sampled is returned at once
            if len(mon.trs) > i:
                return mon.recs[i]
            await mon.tick()
        assert False, f"CHK-005: record {i} never sampled"

    async def after(self, mon, t, k):
        for _ in range(4 * k + 2000):
            i0 = bisect_right(mon.trs, t)
            if i0 < len(mon.trs) and len(mon.trs) >= i0 + k:
                return mon.recs[i0:i0 + k]
            await mon.tick()
        assert False, "CHK-005: destination edges did not occur"

    async def write_word(self, data):
        n = await self.w(1, data)
        await self.w(0)
        return n

    async def read_ready(self, cid, maxc=None):
        d = self.dut
        for _ in range(maxc or (LMAX + 40)):
            n = await self.rd.tick()
            if val(d.o_empty) == 0:
                d.i_rd_en.value = 1
                await self.r(0)
                return n
        assert False, f"{cid}: o_empty did not fall within the bound"

    def finish(self):
        e = self.sb.errs
        assert not e, f"CHK-005: {len(e)} scoreboard/flag errors, first: {e[:3]}"


def chk_wr_rst(tb, cid):
    d = tb.dut
    assert val(d.o_overflow) == 0 and val(d.o_sw_rst_busy) == 0, \
        f"{cid}: at the write reset assertion o_overflow=0, o_sw_rst_busy=0 got {val(d.o_overflow)},{val(d.o_sw_rst_busy)}"
    if val(d.i_rst_n_sw) == 1:
        assert val(d.o_full) == 0 and val(d.o_full_thr) == int(tb.ft == 0), \
            f"{cid}: at the write reset o_full=0, o_full_thr={int(tb.ft == 0)} got {val(d.o_full)},{val(d.o_full_thr)}"


def chk_rd_rst(tb, cid):
    d = tb.dut
    got = (val(d.o_empty), val(d.o_empty_thr), val(d.o_underflow))
    assert got == (1, 1, 0), f"{cid}: at the read reset assertion (o_empty,o_empty_thr,o_underflow)=(1,1,0) got {got}"


async def full_reset(tb, cid):
    """Assert both hardware resets at a write edge, release i_rst_n_wr first, then i_rst_n_rd."""
    d = tb.dut
    await tb.wr.tick()
    d.i_rst_n_wr.value = 0
    d.i_rst_n_rd.value = 0
    d.i_rst_n_sw.value = 1
    d.i_wr_en.value = 0
    tb.sb.clear()
    await ReadOnly()
    chk_wr_rst(tb, cid)
    chk_rd_rst(tb, cid)
    await tb.wr.tick(5)
    d.i_rst_n_wr.value = 1
    await tb.rd.tick(3)
    d.i_rst_n_rd.value = 1
    d.i_rd_en.value = 0
    await tb.settle(3)
    tb.sb.clear()
    tb.sb.en = True


async def xfer(tb, cid, D):
    """Write one word into the empty FIFO, check the crossing latency and the show-ahead data, read it back."""
    D &= MASK
    nw = await tb.write_word(D)
    rw = await tb.rec(tb.wr, nw)
    assert rw["o_full"] == 0, f"{cid}: write of {hx(D)} expected accepted (o_full=0) got o_full={rw['o_full']}"
    E = await tb.after(tb.rd, rw["tr"], LMAX + 3)
    L = lead(E, "o_empty", 1)
    chk_lat(L, cid, "o_empty fall after a write into the empty FIFO")
    assert all(e["o_empty"] == 0 for e in E[L:]), f"{cid}: o_empty rose again without a read"
    if S >= 2:
        for k in range(1, L + 1):
            assert E[k]["o_rd_data"] == D, \
                f"{cid}: o_rd_data at read edge {k + 1} after the write expected {hx(D)} got {hx(E[k]['o_rd_data'])}"
    nr = await tb.read_ready(cid)
    rr = await tb.rec(tb.rd, nr)
    assert rr["o_rd_data"] == D, f"{cid}: read returned {hx(rr['o_rd_data'])} expected {hx(D)}"
    rn = await tb.rec(tb.rd, nr + 1)
    assert rn["o_empty"] == 1, f"{cid}: o_empty=1 expected after reading the only word got {rn['o_empty']}"
    return {"nw": nw, "rw": rw, "E": E, "L": L, "nr": nr}


async def fill_tr(tb, cid, r):
    """Fill to DEPTH, read one word at Tr, measure the o_full fall, then drain."""
    D = [r.getrandbits(DW) for _ in range(DEPTH)]
    # Hand fix 2026-11-11: let earlier reads cross to the write domain first. o_full may stay 1 late
    # (REQ-FUNC-008); with DEPTH=2 a read still in the synchronizer made the first fill edge see full.
    await tb.idle(nw=LMAX + 3)
    m0 = len(tb.sb.reads)
    ns = [await tb.w(1, x) for x in D]
    await tb.w(0)
    for k, n in enumerate(ns):
        x = await tb.rec(tb.wr, n)
        assert x["o_full"] == 0, f"{cid}: o_full=0 expected at the edge of word {k} got 1"
    x = await tb.rec(tb.wr, ns[-1] + 1)
    assert x["o_full"] == 1, f"{cid}: o_full=1 expected right after the last free entry got {x['o_full']}"
    await tb.idle(nr=LMAX + 3)
    nt = await tb.r(1)
    await tb.r(0)
    rt = await tb.rec(tb.rd, nt)
    rt1 = await tb.rec(tb.rd, nt + 1)
    assert rt["o_empty"] == 0 and rt["o_rd_data"] == D[0], f"{cid}: read at Tr expected {hx(D[0])} got {hx(rt['o_rd_data'])}"
    if DEPTH > 1:
        assert rt1["o_rd_data"] == D[1], f"{cid}: next word {hx(D[1])} expected at the next read edge got {hx(rt1['o_rd_data'])}"
    E = await tb.after(tb.wr, rt["tr"], LMAX + 4)
    L = lead(E, "o_full", 1)
    chk_lat(L, cid, "o_full fall after a read from the full FIFO")
    assert all(e["o_full"] == 0 for e in E[L:]), f"{cid}: o_full rose again without a write"
    rs = [await tb.r(1) for _ in range(DEPTH - 1)]
    await tb.r(0)
    for k, n in enumerate(rs):
        x = await tb.rec(tb.rd, n)
        assert x["o_empty"] == 0 and x["o_rd_data"] == D[k + 1], \
            f"{cid}: drain word {k + 1} expected {hx(D[k + 1])} got {hx(x['o_rd_data'])} (empty={x['o_empty']})"
    assert tb.sb.reads[m0:] == D, f"{cid}: read sequence differs from the written one"
    return D, rt, E, L


async def scn_fill_drain(tb, cid, r):
    """CHK-018 phase 1."""
    D = [r.getrandbits(DW) for _ in range(DEPTH)]
    m0 = len(tb.sb.reads)
    ns = [await tb.w(1, x) for x in D]
    await tb.w(0)
    for k, n in enumerate(ns):
        x = await tb.rec(tb.wr, n)
        assert x["o_full"] == 0, f"{cid}: o_full=0 expected at the edge accepting D{k} got 1"
    x = await tb.rec(tb.wr, ns[-1] + 1)
    assert x["o_full"] == 1 and x["o_full_thr"] == int(DEPTH >= tb.ft), \
        f"{cid}: after the last write o_full=1, o_full_thr={int(DEPTH >= tb.ft)} got {x['o_full']},{x['o_full_thr']}"
    await tb.idle(nr=5 + EXTRA)
    rs = [await tb.r(1) for _ in range(DEPTH)]
    await tb.r(0)
    for k, n in enumerate(rs):
        x = await tb.rec(tb.rd, n)
        assert x["o_empty"] == 0 and x["o_rd_data"] == D[k], \
            f"{cid}: read edge {k} expected o_empty=0 data {hx(D[k])} got {x['o_empty']},{hx(x['o_rd_data'])}"
    x = await tb.rec(tb.rd, rs[-1] + 1)
    assert x["o_empty"] == 1 and x["o_empty_thr"] == 1, \
        f"{cid}: after the last read o_empty=1,o_empty_thr=1 got {x['o_empty']},{x['o_empty_thr']}"
    assert tb.sb.reads[m0:] == D, f"{cid}: read order differs from write order"


async def scn_020(tb, cid, r):
    """CHK-020: overflow, late o_full fall, rejected words never stored."""
    D = [r.getrandbits(DW) for _ in range(DEPTH)]
    X = [r.getrandbits(DW) for _ in range(5)]
    Y = r.getrandbits(DW)
    m0 = len(tb.sb.reads)
    ns = [await tb.w(1, x) for x in D]
    xs = [await tb.w(1, x) for x in X]
    await tb.w(0)
    await tb.idle(nw=5)
    for n in ns:
        assert (await tb.rec(tb.wr, n))["o_full"] == 0, f"{cid}: o_full=0 expected while filling"
    for k, n in enumerate(xs):
        x = await tb.rec(tb.wr, n)
        assert x["o_full"] == 1, f"{cid}: o_full=1 expected at the edge of X{k} got {x['o_full']}"
        y = await tb.rec(tb.wr, n + 1)
        assert y["o_overflow"] == 1, f"{cid}: o_overflow=1 expected after X{k} got {y['o_overflow']}"
    for n in range(xs[-1] + 2, xs[-1] + 6):
        assert (await tb.rec(tb.wr, n))["o_overflow"] == 0, f"{cid}: o_overflow must return to 0"
    await tb.idle(nr=LMAX + 3)
    nt = await tb.r(1)
    await tb.r(0)
    rt = await tb.rec(tb.rd, nt)
    assert rt["o_empty"] == 0 and rt["o_rd_data"] == D[0], f"{cid}: first read expected {hx(D[0])} got {hx(rt['o_rd_data'])}"
    E = await tb.after(tb.wr, rt["tr"], LMAX + 4)
    L = lead(E, "o_full", 1)
    chk_lat(L, cid, "o_full fall after the freeing read")
    for k, e in enumerate(E):
        cnt = DEPTH if k < L else DEPTH - 1
        assert e["o_full"] == int(k < L) and e["o_full_thr"] == int(cnt >= tb.ft), \
            f"{cid}: write edge {k + 1} after Tr: o_full={int(k < L)} o_full_thr={int(cnt >= tb.ft)} got {e['o_full']},{e['o_full_thr']}"
    rs = [await tb.r(1) for _ in range(DEPTH - 1)]
    await tb.r(0)
    for k, n in enumerate(rs):
        x = await tb.rec(tb.rd, n)
        assert x["o_empty"] == 0 and x["o_rd_data"] == D[k + 1], f"{cid}: read {k + 1} expected {hx(D[k + 1])} got {hx(x['o_rd_data'])}"
    assert tb.sb.reads[m0:] == D, f"{cid}: reads must be D0..D{DEPTH - 1} only, got {[hx(v) for v in tb.sb.reads[m0:]]}"
    ny = await tb.write_word(Y)
    ry = await tb.rec(tb.wr, ny)
    assert ry["o_full"] == 0, f"{cid}: Y0 must be accepted"
    E2 = await tb.after(tb.rd, ry["tr"], LMAX + 2)
    if S >= 2:
        assert E2[0]["o_rd_data"] == (D[0] & MASK), f"{cid}: entry 0 expected to show D0 before Y0 is captured got {hx(E2[0]['o_rd_data'])}"
        assert E2[1]["o_rd_data"] == Y and E2[1]["o_empty"] == 1, \
            f"{cid}: Y0 expected in entry 0 at read edge 2 with o_empty=1 got {hx(E2[1]['o_rd_data'])},{E2[1]['o_empty']}"
    nr = await tb.read_ready(cid)
    assert (await tb.rec(tb.rd, nr))["o_rd_data"] == Y, f"{cid}: Y0 must be read as the next word"


async def scn_021(tb, cid, r):
    """CHK-021: underflow on an empty FIFO with the read pointer at entry 1."""
    Wd = [r.getrandbits(DW) for _ in range(DEPTH + 2)]
    m0 = len(tb.sb.reads)
    for x in Wd[:DEPTH]:
        await tb.w(1, x)
    await tb.w(0)
    await tb.idle(nr=LMAX + 3)
    rs = [await tb.r(1) for _ in range(DEPTH)]
    await tb.r(0)
    for k, n in enumerate(rs):
        x = await tb.rec(tb.rd, n)
        assert x["o_empty"] == 0 and x["o_rd_data"] == Wd[k], f"{cid}: read {k} expected {hx(Wd[k])} got {hx(x['o_rd_data'])}"
    await tb.idle(nw=LMAX + 3)          # hand fix 2026-11-11: the reads cross before the next write (REQ-FUNC-008)
    await xfer(tb, cid, Wd[DEPTH])
    await tb.idle(nr=3)
    us = [await tb.r(1) for _ in range(6)]
    await tb.r(0)
    for n in us:
        x = await tb.rec(tb.rd, n)
        assert x["o_empty"] == 1 and x["o_rd_data"] == Wd[1], \
            f"{cid}: during underflow o_empty=1 and o_rd_data=W1 {hx(Wd[1])} got {x['o_empty']},{hx(x['o_rd_data'])}"
        assert (await tb.rec(tb.rd, n + 1))["o_underflow"] == 1, f"{cid}: o_underflow=1 expected after each rejected read"
    assert (await tb.rec(tb.rd, us[-1] + 2))["o_underflow"] == 0, f"{cid}: o_underflow must return to 0"
    await tb.idle(nr=3)
    W9 = Wd[DEPTH + 1]
    nw = await tb.write_word(W9)
    rw = await tb.rec(tb.wr, nw)
    E = await tb.after(tb.rd, rw["tr"], LMAX + 3)
    for i in range(us[0], E[0]["i"] + 1):
        assert tb.rd.recs[i]["o_rd_data"] == Wd[1], f"{cid}: entry 1 content W1 must not change before W9 is captured"
    if S >= 2:
        assert E[1]["o_rd_data"] == W9 and E[1]["o_empty"] == 1, \
            f"{cid}: read edge 2 after Tw: o_rd_data=W9, o_empty=1 got {hx(E[1]['o_rd_data'])},{E[1]['o_empty']}"
    chk_lat(lead(E, "o_empty", 1), cid, "o_empty fall after W9")
    nr = await tb.read_ready(cid)
    assert (await tb.rec(tb.rd, nr))["o_rd_data"] == W9, f"{cid}: the read must return W9"
    a, b = await tb.rec(tb.rd, nr + 1), await tb.rec(tb.rd, nr + 2)
    assert a["o_empty"] == 1 and a["o_underflow"] == 0 and b["o_underflow"] == 0, f"{cid}: o_empty=1 without underflow after the read"
    assert tb.sb.reads[m0:] == Wd[:DEPTH] + [Wd[DEPTH], W9], f"{cid}: read sequence mismatch"


async def wait_drained(tb, cid, lim=None):
    for _ in range(lim or (60 * DEPTH + 4000)):
        if not tb.sb.Q and not tb.sb.P:
            return
        await tb.rd.tick()
    assert False, f"{cid}: FIFO not drained, {len(tb.sb.Q)} words left"


async def idle_check(tb, cid):
    W, R = tb.W, tb.R
    sv = (W.d, R.d)
    W.d = R.d = 0.0
    await tb.settle(5 + LMAX + 2)
    d = tb.dut
    if val(d.i_rst_n_sw) == 1 and val(d.o_sw_rst_busy) == 0 and not W.plan:
        assert not (val(d.o_full) == 1 and val(d.o_empty) == 1), f"{cid}: INV-002 o_full and o_empty both 1 at an idle point"
    W.d, R.d = sv


async def sw_seq(tb, r, cid):
    W, R = tb.W, tb.R
    d = tb.dut
    mode = r.randrange(3)
    if mode == 0:
        W.d, R.d, R.gate = 0.0, 1.0, False
    elif mode == 2:
        W.d, R.d, W.gate = 1.0, 0.0, False
    if mode != 1:
        await tb.settle(DEPTH + LMAX + 4)
    W.d, R.d = r.choice(DENS), r.choice(DENS)
    W.plan.extend([0] * r.randint(1, 12))
    await tb.wr.tick(len(W.plan) + 1)
    if r.random() < 0.3:
        await tb.wr.tick(r.randint(0, 6))
        if val(d.o_sw_rst_busy) == 1:
            W.plan.extend([0] * r.randint(1, 3))
    lim = int(60 * tb.slow_ps / (tb.pw * 1000)) + 80
    zeros = 0
    for _ in range(lim * 3):
        await tb.wr.tick()
        zeros = zeros + 1 if (not W.plan and val(d.o_sw_rst_busy) == 0) else 0
        if zeros >= 2:
            return
    assert False, f"{cid}: software reset sequence did not complete (deadlock)"


async def run_traffic(tb, r, target, cid, sw=False, nseq=0, idle_chk=True):
    W, R = tb.models(r)
    k0 = len(tb.sb.wacc)
    seqs = 0
    for _ in range(5000):
        if len(tb.sb.wacc) - k0 >= target and seqs >= nseq:
            break
        x = r.random()
        if x < 0.15:
            W.d, R.d = 1.0, 0.0
        elif x < 0.3:
            W.d, R.d = 0.0, 1.0
        else:
            W.d, R.d = r.choice(DENS), r.choice(DENS)
        W.gate = r.random() < 0.5
        R.gate = r.random() < 0.5
        await tb.wr.tick(r.randint(10, 60))
        if sw and r.random() < 0.4:
            await sw_seq(tb, r, cid)
            seqs += 1
        elif idle_chk and r.random() < 0.3:
            await idle_check(tb, cid)
    else:
        assert False, f"{cid}: traffic target not reached"
    W.d, R.d, R.gate = 0.0, 1.0, True
    await wait_drained(tb, cid)
    await tb.settle(LMAX + 4)
    R.d = 0.0
    await tb.settle(2)
    d = tb.dut
    assert val(d.o_empty) == 1 and val(d.o_full) == 0 and not tb.sb.Q, \
        f"{cid}: after the drain o_empty=1, o_full=0, Q empty got {val(d.o_empty)},{val(d.o_full)},{len(tb.sb.Q)}"


def coverage(tb):
    Wr, Rr = tb.wr.recs, tb.rd.recs
    c = {"full": any(x["o_full"] == 1 and x["i_rst_n_sw"] == 1 and x["o_sw_rst_busy"] == 0 and x["i_rst_n_wr"] == 1 for x in Wr),
         "empty": any(x["o_empty"] == 1 and x["i_rst_n_rd"] == 1 for x in Rr),
         "ovf": any(x["o_overflow"] == 1 for x in Wr),
         "udf": any(x["o_underflow"] == 1 for x in Rr)}
    wt = [x["tr"] for x in tb.sb.wacc]
    win = int(max(tb.pw, tb.pr) * 1000)
    same = False
    for x in tb.sb.racc:
        i = bisect_right(wt, x["tr"])
        if (i > 0 and x["tr"] - wt[i - 1] <= win) or (i < len(wt) and wt[i] - x["tr"] <= win):
            same = True
            break
    c["same"] = same
    return c


def check_busy_bounds(tb, cid):
    W = tb.wr.recs
    n, i = 0, 0
    while i < len(W) - 2:
        if W[i]["o_sw_rst_busy"] == 0 and W[i + 1]["o_sw_rst_busy"] == 1 and W[i]["i_rst_n_wr"] == 1:
            m = find_fall(W, i + 1)
            if m is None or "tr" not in W[m]:
                break
            if W[m + 1]["i_rst_n_wr"] == 1 and all(W[k]["i_rst_n_wr"] == 1 for k in range(i, m + 1)):
                lows = [k for k in range(i, m + 1) if W[k]["i_rst_n_sw"] == 0]
                k = min((lows[-1] + 1) if lows else i, m)
                t0 = max(W[i]["tr"], W[k]["tr"])
                assert W[m]["tr"] - t0 <= 32 * tb.slow_ps, \
                    f"{cid}: o_sw_rst_busy fell {W[m]['tr'] - t0} ps after the start, more than 32 slow-clock edges"
                n += 1
            i = m + 1
        else:
            i += 1
    return n


# ----------------------------------------------------------------------------------------------- tests
@cocotb.test()
@_param(per=[(10, 14), (14, 6)])
async def test_chk_014_nominal_latency(dut, per=(10, 14)):
    """CHK-014: nominal crossing latency S edges, data before o_empty falls, o_full fall S write edges after a read."""
    cid = "CHK-014"
    tb = TB(dut, {WCLK: per[0], RCLK: per[1]})
    await tb.init(ft=DEPTH, et=0)
    note_model(dut, cid)
    r = rng(f"chk014_{per}")
    for _ in range(10):
        await tb.idle(nw=r.randint(0, 7), nr=r.randint(0, 5))
        await xfer(tb, cid, r.getrandbits(DW))
        await tb.idle(nw=r.randint(0, 5))
        await fill_tr(tb, cid, r)
    tb.finish()


@cocotb.test()
async def test_chk_015_latency_with_model(dut):
    """CHK-015: crossing latency S..S+2 with the metastability model, flags never early, data correct."""
    cid = "CHK-015"
    tb = TB(dut, {WCLK: 10, RCLK: 13})
    await tb.init(ft=DEPTH, et=0)
    seed = plusarg("AFIFO_MSYNC_SEED")
    dut._log.info(f"{cid}: model={'on' if MS else 'off'} seed={seed}")
    if not MS:
        not_verifiable(dut, cid, "the metastability model is not enabled in this run (or the VLSIT_SYNTHESIS "
                       "build); only the plain latency was measured")
    not_verifiable(dut, cid, f"seeing L=2,3,4 in both directions over the 5-seed run set needs the other seeds; "
                   f"this run covers seed {seed} only")
    r = rng("chk015")
    Lw, Lr = [], []
    for _ in range(100):
        await tb.idle(nr=6 + r.randint(0, 4), nw=r.randint(0, 3))
        x = await xfer(tb, cid, r.getrandbits(DW))
        Lw.append(x["L"])
    for _ in range(DEPTH):
        await tb.w(1, r.getrandbits(DW))
    await tb.w(0)
    await tb.idle(nr=LMAX + 3)
    for _ in range(100):
        await tb.idle(nw=6 + r.randint(0, 4))
        nt = await tb.r(1)
        await tb.r(0)
        rt = await tb.rec(tb.rd, nt)
        assert rt["o_empty"] == 0, f"{cid}: the full FIFO must allow a read"
        E = await tb.after(tb.wr, rt["tr"], LMAX + 3)
        L = lead(E, "o_full", 1)
        chk_lat(L, cid, "o_full fall after an isolated read")
        assert all(e["o_full"] == 0 for e in E[L:]), f"{cid}: o_full rose again"
        Lr.append(L)
        await tb.write_word(r.getrandbits(DW))
        await tb.idle(nr=LMAX + 3)
    dut._log.info(f"{cid}: write->empty latencies {dict(Counter(Lw))}, read->full latencies {dict(Counter(Lr))}")
    for _ in range(4 * DEPTH):
        if not tb.sb.Q:
            break
        await tb.read_ready(cid)
    tb.finish()


PAIRS16 = [(10, 10), (10, 10.3), (10, 23), (10, 50), (23, 10), (50, 10)]


@cocotb.test()
@_param(pair=PAIRS16)
async def test_chk_016_random_ratios(dut, pair=PAIRS16[0]):
    """CHK-016: random traffic for several clock ratios, pointer wrap, order/exactly-once, INV-002 at idle points."""
    cid = "CHK-016"
    tb = TB(dut, {WCLK: pair[0], RCLK: pair[1]})
    r = rng(f"chk016_{pair}")
    await tb.init(ft=r.randint(0, TMAX), et=r.randint(0, TMAX))
    note_model(dut, cid, need_off=False)
    if MS:
        not_verifiable(dut, cid, "the model-off run of the run set is another configuration; this run has the model on")
    else:
        not_verifiable(dut, cid, "the model-on runs with logged seeds are other configurations; this run has the model off")
    if pair == (10, 10):
        dut._log.info(f"{cid}: phase offset set by the random clock start delays (a fixed 3 ns offset cannot be set)")
    k0 = len(tb.sb.wacc)
    await run_traffic(tb, r, 2000, cid)
    assert len(tb.sb.wacc) - k0 >= 2000, f"{cid}: at least 2000 accepted words expected"
    cov = coverage(tb)
    dut._log.info(f"{cid}: coverage {cov}")
    assert all(cov.values()), f"{cid}: coverage not reached: {cov}"
    tb.finish()


@cocotb.test()
async def test_chk_017_synthesis_branch_regression(dut):
    """CHK-017: regression of the VLSIT_SYNTHESIS build (random traffic + software resets + isolated latency)."""
    cid = "CHK-017"
    tb = TB(dut)
    await tb.init(ft=DEPTH, et=0)
    if not SYN:
        not_verifiable(dut, cid, "this run is built without VLSIT_SYNTHESIS: the synthesizable cell branch is not "
                       "elaborated; the same traffic and latency checks run on the simulation branch")
    note_model(dut, cid)
    r = rng("chk017")
    for _ in range(5):
        await xfer(tb, cid, r.getrandbits(DW))
        await fill_tr(tb, cid, r)
    await run_traffic(tb, r, 800, cid, sw=True, nseq=10)
    check_busy_bounds(tb, cid)
    tb.finish()


@cocotb.test()
async def test_chk_018_write_n_read_n(dut):
    """CHK-018: write N then read N with a show-ahead head check, then random fill/drain."""
    cid = "CHK-018"
    tb = TB(dut, {WCLK: 10, RCLK: 14})
    await tb.init(ft=DEPTH, et=0)
    note_model(dut, cid)
    r = rng("chk018")
    w0, r0 = tb.wr.n, tb.rd.n
    await scn_fill_drain(tb, cid, r)
    W, R = tb.models(r)
    W.gate = R.gate = True
    W.d, R.d = 0.5, 0.7
    k0, m0 = len(tb.sb.wacc), len(tb.sb.reads)
    for _ in range(40000):
        if len(tb.sb.wacc) - k0 >= 200:
            break
        await tb.wr.tick()
    else:
        assert False, f"{cid}: 200 words were not accepted"
    W.d = 0.0
    await wait_drained(tb, cid)
    R.d = 0.0
    await tb.settle(3)
    exp = [x["i_wr_data"] for x in tb.sb.wacc[k0:]]
    assert tb.sb.reads[m0:] == exp, f"{cid}: phase 2 reads differ from the writes ({len(tb.sb.reads) - m0} vs {len(exp)})"
    assert all(x["o_overflow"] == 0 for x in tb.wr.recs[w0:]), f"{cid}: o_overflow must stay 0"
    assert all(x["o_underflow"] == 0 for x in tb.rd.recs[r0:]), f"{cid}: o_underflow must stay 0"
    tb.finish()


@cocotb.test()
async def test_chk_019_back_to_back_equal_clocks(dut):
    """CHK-019: back-to-back burst of 24 words with equal clocks, across the pointer wrap."""
    cid = "CHK-019"
    tb = TB(dut, {WCLK: 10, RCLK: 10})
    await tb.init(ft=DEPTH, et=0)
    note_model(dut, cid)
    dut._log.info(f"{cid}: read phase set by the random clock start delays (a fixed 3 ns lag cannot be set)")
    if not EXACT:
        not_verifiable(dut, cid, "with the model on, gaps / o_full can legally appear; zero-gap and no-pulse parts not checked")
    d = dut
    st = {"wdone": False}
    k0, m0 = len(tb.sb.wacc), len(tb.sb.reads)
    w0, r0 = tb.wr.n, tb.rd.n

    async def cons():
        got, started, ns = 0, False, []
        for _ in range(600):
            n = await tb.rd.tick()
            if got >= 24 or (started and st["wdone"] and not tb.sb.Q):
                d.i_rd_en.value = 0
                return ns
            e = val(d.o_empty)
            if not started and e == 0:
                started = True
            d.i_rd_en.value = 1 if started else 0
            if started and e == 0:
                got += 1
                ns.append(n)
        d.i_rd_en.value = 0
        return ns

    t = cocotb.start_soon(cons())
    ws = [await tb.w(1, i + 1) for i in range(24)]
    await tb.w(0)
    st["wdone"] = True
    ns = await t
    await tb.settle(3)
    exp = [x["i_wr_data"] for x in tb.sb.wacc[k0:]]
    assert tb.sb.reads[m0:] == exp, f"{cid}: read order differs from write order"
    if EXACT:
        for n in ws:
            assert tb.wr.recs[n]["o_full"] == 0, f"{cid}: o_full=0 expected at all 24 write edges"
        assert exp == [(i + 1) & MASK for i in range(24)], f"{cid}: 24 writes must be accepted"
        assert len(ns) == 24 and ns == list(range(ns[0], ns[0] + 24)), f"{cid}: 24 reads at consecutive edges expected got {ns}"
        for k, n in enumerate(ns):
            x = tb.rd.recs[n]
            assert x["o_empty"] == 0 and x["o_rd_data"] == (k + 1) & MASK, f"{cid}: read {k} expected {hx(k + 1)} got {hx(x['o_rd_data'])}"
        assert all(x["o_overflow"] == 0 for x in tb.wr.recs[w0:]), f"{cid}: o_overflow must stay 0"
        assert all(x["o_underflow"] == 0 for x in tb.rd.recs[r0:]), f"{cid}: o_underflow must stay 0"
    tb.finish()


@cocotb.test()
async def test_chk_020_overflow(dut):
    """CHK-020: writes while full are dropped; o_full falls S write edges after a read."""
    tb = TB(dut, {WCLK: 10, RCLK: 14})
    await tb.init(ft=DEPTH, et=0)
    note_model(dut, "CHK-020")
    await scn_020(tb, "CHK-020", rng("chk020"))
    tb.finish()


@cocotb.test()
async def test_chk_021_underflow(dut):
    """CHK-021: underflow keeps the read pointer; show-ahead of the storage while empty."""
    tb = TB(dut, {WCLK: 10, RCLK: 14})
    await tb.init(ft=DEPTH, et=0)
    note_model(dut, "CHK-021")
    await scn_021(tb, "CHK-021", rng("chk021"))
    tb.finish()


@cocotb.test()
async def test_chk_022_hw_reset_independent(dut):
    """CHK-022: hardware reset of both domains, independent assertion/release, clean first transfer."""
    cid = "CHK-022"
    tb = TB(dut, {WCLK: 10, RCLK: 14})
    await tb.init(ft=min(4, TMAX), et=2)
    note_model(dut, cid)
    r = rng("chk022")
    d = dut
    for mode in (0, 1):
        if mode == 0:
            await tb.w(0)
            d.i_rst_n_wr.value = 0
            tb.sb.clear()
            await ReadOnly()
            chk_wr_rst(tb, cid)
            wi = tb.wr.n
            await tb.r(0)
            await tb.r(0)
            await tb.r(0)
            d.i_rst_n_rd.value = 0
            await ReadOnly()
            chk_rd_rst(tb, cid)
            ri = tb.rd.n
            await tb.idle(nr=4, nw=4)
            await tb.rd.tick()
            d.i_rst_n_rd.value = 1
            await tb.wr.tick(5)
            d.i_rst_n_wr.value = 1
        else:
            await tb.w(0)
            d.i_rst_n_wr.value = 0
            d.i_rst_n_rd.value = 0
            tb.sb.clear()
            await ReadOnly()
            chk_wr_rst(tb, cid)
            chk_rd_rst(tb, cid)
            wi, ri = tb.wr.n, tb.rd.n
            await tb.idle(nw=5, nr=4)
            await tb.wr.tick()
            d.i_rst_n_wr.value = 1
            await tb.rd.tick(3)
            d.i_rst_n_rd.value = 1
        await tb.settle(4)
        m0 = len(tb.sb.reads)
        x = await xfer(tb, cid, r.getrandbits(DW))
        for i in range(wi, x["nw"] + 1):
            e = tb.wr.recs[i]
            assert (e["o_overflow"], e["o_sw_rst_busy"], e["o_full"], e["o_full_thr"]) == (0, 0, 0, int(tb.ft == 0)), \
                f"{cid}: write-domain reset values expected at every edge before the write got {e}"
        for i in range(ri, x["E"][x["L"] - 1]["i"] + 1):
            e = tb.rd.recs[i]
            assert (e["o_empty"], e["o_empty_thr"], e["o_underflow"]) == (1, 1, 0), \
                f"{cid}: read-domain reset values expected until the write crosses got {e}"
        assert len(tb.sb.reads) - m0 == 1, f"{cid}: exactly one word expected to be read"
        assert all(e["o_overflow"] == 0 for e in tb.wr.recs[wi:]) and all(e["o_underflow"] == 0 for e in tb.rd.recs[ri:]), \
            f"{cid}: no overflow/underflow pulse expected"
    tb.finish()


@cocotb.test()
async def test_chk_023_hw_reset_during_srst(dut):
    """CHK-023: hardware reset has priority over the software reset (both domains, then one domain)."""
    cid = "CHK-023"
    tb = TB(dut, {WCLK: 10, RCLK: 14})
    await tb.init(ft=DEPTH, et=0)
    note_model(dut, cid)
    r = rng("chk023")
    d = dut
    for _ in range(4):
        await tb.w(1, r.getrandbits(DW))
    await tb.w(0)
    await tb.idle(nr=LMAX + 3)
    await tb.w(0, sw=0)
    for _ in range(80):
        await tb.rd.tick()
        if val(d.o_empty) == 1:
            break
    else:
        assert False, f"{cid}: o_empty did not rise during the software reset"
    await tb.idle(nw=4)
    await full_reset(tb, cid)
    assert (val(d.o_sw_rst_busy), val(d.o_full), val(d.o_empty)) == (0, 0, 1), f"{cid}: after release busy=0, o_full=0, o_empty=1"
    m0 = len(tb.sb.reads)
    A = r.getrandbits(DW)
    await xfer(tb, cid, A)
    assert tb.sb.reads[m0:] == [A & MASK], f"{cid}: only A may be read after the reset"
    # Part 2: write-domain reset only, in the middle of a sequence
    await tb.w(0, sw=0)
    await tb.idle(nw=4)
    assert val(d.o_sw_rst_busy) == 1, f"{cid}: sequence expected in progress"
    tb.sb.en = False
    d.i_rst_n_wr.value = 0
    d.i_rst_n_sw.value = 1
    await ReadOnly()
    assert (val(d.o_sw_rst_busy), val(d.o_overflow), val(d.o_full)) == (0, 0, 0), \
        f"{cid}: part 2 at assertion busy=0, overflow=0, full=0 got {(val(d.o_sw_rst_busy), val(d.o_overflow), val(d.o_full))}"
    await tb.wr.tick(4)
    await full_reset(tb, cid)
    await xfer(tb, cid, r.getrandbits(DW))
    # Part 3: read-domain reset only, in the middle of a sequence
    await tb.w(0, sw=0)
    await tb.w(0, sw=1)
    await tb.idle(nr=3)
    tb.sb.en = False
    await tb.rd.tick()
    d.i_rst_n_rd.value = 0
    await ReadOnly()
    assert (val(d.o_empty), val(d.o_underflow)) == (1, 0), f"{cid}: part 3 at assertion o_empty=1, o_underflow=0"
    await tb.rd.tick(4)
    await full_reset(tb, cid)
    await xfer(tb, cid, r.getrandbits(DW))
    tb.finish()


@cocotb.test()
async def test_chk_024_hw_reset_mid_traffic(dut):
    """CHK-024: hardware reset of both domains in the middle of traffic, clean restart."""
    cid = "CHK-024"
    tb = TB(dut, {WCLK: 10, RCLK: 14})
    await tb.init(ft=DEPTH, et=0)
    note_model(dut, cid, need_off=False)
    r = rng("chk024")
    d = dut
    W, R = tb.models(r)
    W.gate = R.gate = True
    tgt = max(1, min(5, DEPTH - 1))     # hand fix 2026-11-11: 5 words need DEPTH > 5 (5 for the default DEPTH 8)
    for _ in range(4000):
        await tb.wr.tick()
        q = len(tb.sb.Q)
        if q == tgt and W.d > 0:
            break
        W.d, R.d = (0.8, 0.3) if q < tgt else (0.3, 0.8)
    else:
        assert False, f"{cid}: the FIFO never held {tgt} words"
    d.i_rst_n_wr.value = 0
    d.i_rst_n_rd.value = 0
    W.run = R.run = False
    tb.sb.clear()
    await ReadOnly()
    chk_wr_rst(tb, cid)
    chk_rd_rst(tb, cid)
    await tb.wr.tick(5)
    d.i_rst_n_wr.value = 1
    wi = tb.wr.n
    await tb.rd.tick(3)
    d.i_rst_n_rd.value = 1
    ri = tb.rd.n
    await tb.settle(5)
    assert all(e["o_full"] == 0 for e in tb.wr.recs[wi:]), f"{cid}: o_full=0 expected after the release"
    k0, m0 = len(tb.sb.wacc), len(tb.sb.reads)
    await run_traffic(tb, r, 200, cid)
    w1 = tb.sb.wacc[k0]
    lim = bisect_right(tb.rd.trs, w1["tr"]) + S
    for e in tb.rd.recs[ri:lim]:
        assert e["o_empty"] == 1, f"{cid}: o_empty=1 expected until the first new write crosses"
    exp = [x["i_wr_data"] for x in tb.sb.wacc[k0:]]
    assert tb.sb.reads[m0:] == exp, f"{cid}: only post-reset words, in order, exactly once"
    tb.finish()


@cocotb.test()
async def test_chk_025_srst_partial_fifo(dut):
    """CHK-025: software reset of a partly filled FIFO with i_rst_n_sw held low (four-phase sequence)."""
    cid = "CHK-025"
    tb = TB(dut, {WCLK: 10, RCLK: 14})
    await tb.init(ft=min(6, TMAX), et=2)
    note_model(dut, cid)
    if min(6, DEPTH) < LMAX:            # hand fix 2026-11-11
        not_verifiable(dut, cid, f"PARA_AFIFO_DEPTH={DEPTH} holds fewer words than the read edges the request "
                       f"may need to cross (up to {LMAX}): reading at every edge empties the FIFO before the block, "
                       "so the scenario cannot be built here; it runs in deeper configurations")
        tb.finish()
        return
    r = rng("chk025")
    d = dut
    D = [r.getrandbits(DW) for _ in range(6)]
    for x in D:
        await tb.w(1, x)
    await tb.w(0)
    await tb.idle(nr=5 + EXTRA)
    m0 = len(tb.sb.reads)
    st = {"done": False}

    async def rdrv():
        for _ in range(8000):
            await tb.rd.tick()
            if st["done"]:
                d.i_rd_en.value = 0
                return
            d.i_rd_en.value = 1

    cocotb.start_soon(rdrv())
    c, seen, fall, w0 = 0x5A000, False, None, None
    for i in range(3000):
        n = await tb.wr.tick()
        b = val(d.o_sw_rst_busy)
        if i == 0:
            w0 = n
        seen |= b == 1
        if seen and b == 0 and fall is None:
            fall = i
        if fall is not None and i >= fall + 10:
            d.i_wr_en.value = 0
            break
        d.i_rst_n_sw.value = 0 if i < 20 else 1
        d.i_wr_en.value = 1
        d.i_wr_data.value = c & MASK
        c += 1
    else:
        assert False, f"{cid}: o_sw_rst_busy did not fall"
    await wait_drained(tb, cid)
    await tb.settle(4)
    st["done"] = True
    await tb.settle(2)
    Wr, Rr, trs = tb.wr.recs, tb.rd.recs, tb.rd.trs
    m = await fall_rec(tb, w0 + 1, cid)
    H = next(i for i in range(w0, len(Wr)) if Wr[i]["i_rst_n_sw"] == 1)
    for i in range(w0, m + 1):
        assert Wr[i]["o_full"] == 1 and Wr[i]["o_full_thr"] == int(tb.ft == 0), f"{cid}: (1) o_full=1, o_full_thr=empty value while blocked"
    for i in range(w0 + 1, m + 2):
        assert Wr[i]["o_overflow"] == 0, f"{cid}: (1) no o_overflow pulse for blocked writes"
    assert Wr[w0]["o_sw_rst_busy"] == 0 and all(Wr[i]["o_sw_rst_busy"] == 1 for i in range(w0 + 1, m + 1)), f"{cid}: (2) busy profile"
    e1 = bisect_right(trs, Wr[w0]["tr"])
    E = Rr[e1:len(trs)]
    L = lead(E, "o_empty", 0)
    chk_lat(L, cid, "(3) read block after the request")
    pre = [x for x in tb.sb.racc[m0:] if x["tr"] <= Wr[m]["tr"]]
    assert tb.sb.reads[m0:m0 + len(pre)] == D[:len(pre)], f"{cid}: (3) pre-reset reads must return D0.. in order"
    assert all(x["i"] < e1 + L for x in pre), f"{cid}: (3) no read accepted from the block on"
    u = next((j for j in range(L, len(E)) if E[j]["o_underflow"] == 1), None)
    assert u is not None, f"{cid}: (5) o_underflow never came back"
    for j in range(L, u):
        assert E[j]["o_empty"] == 1 and E[j]["o_empty_thr"] == 1, f"{cid}: (3) o_empty=1, o_empty_thr=1 while blocked"
    assert E[u - 1]["tr"] > Wr[H]["tr"], f"{cid}: (4) o_underflow must stay 0 while i_rst_n_sw=0"
    R = u - 2
    assert E[R]["tr"] < Wr[m]["tr"] and m >= H + 3, f"{cid}: (5) read release before the busy fall and m >= H+3 (m={m}, H={H})"
    assert Wr[m + 1]["o_full"] == 0 and Wr[m + 1]["o_full_thr"] == int(tb.ft == 0), f"{cid}: (6) o_full=0, o_full_thr=0 at m+1"
    assert ncount(trs, Wr[H]["tr"], Wr[m]["tr"]) <= 32, f"{cid}: (6) busy must fall within 32 read edges after H"
    assert not [x for x in tb.sb.wacc if w0 <= x["i"] <= m and x["tr"] >= Wr[w0]["tr"]], f"{cid}: (1) no write accepted while blocked"
    P0 = Wr[m + 1]["i_wr_data"]
    assert Wr[m + 1]["i_wr_en"] == 1, f"{cid}: (8) P0 must be written at m+1"
    e2 = bisect_right(trs, Wr[m + 1]["tr"])
    for i in range(e1 + R + 1, e2 + 1):
        assert Rr[i]["o_rd_data"] == D[0] and Rr[i]["o_empty"] == 1, f"{cid}: (7) o_rd_data=D0, o_empty=1 before P0 crosses got {hx(Rr[i]['o_rd_data'])}"
    E2 = Rr[e2:e2 + LMAX + 2]
    if S >= 2:
        assert E2[1]["o_rd_data"] == P0 and E2[1]["o_empty"] == 1, f"{cid}: (8) o_rd_data=P0 at read edge 2 with o_empty=1"
    chk_lat(lead(E2, "o_empty", 1), cid, "(8) o_empty fall after P0")
    post = [x for x in tb.sb.racc[m0:] if x["tr"] > Wr[m]["tr"]]
    assert post and post[0]["o_rd_data"] == P0, f"{cid}: (8) the first post-reset read must return P0"
    assert all(e["o_empty_thr"] == 1 for e in Rr[e1:] if e["o_empty"] == 1), f"{cid}: o_empty_thr=1 whenever o_empty=1"
    tb.finish()


@cocotb.test()
async def test_chk_026_srst_pulse_full_overflow(dut):
    """CHK-026: one-cycle i_rst_n_sw pulse on a full FIFO in overflow."""
    cid = "CHK-026"
    tb = TB(dut, {WCLK: 10, RCLK: 14})
    await tb.init(ft=min(6, TMAX), et=0)
    note_model(dut, cid)
    r = rng("chk026")
    d = dut
    D = [r.getrandbits(DW) for _ in range(DEPTH)]
    ns = [await tb.w(1, x) for x in D]
    st = {"rel": False, "done": False}

    async def rdrv():
        for _ in range(8000):
            await tb.rd.tick()
            if st["done"]:
                d.i_rd_en.value = 0
                return
            d.i_rd_en.value = 1 if st["rel"] else 0

    cocotb.start_soon(rdrv())
    c, seen, fall, w1 = 0x7700, False, None, None
    for i in range(3000):
        n = await tb.wr.tick()
        b = val(d.o_sw_rst_busy)
        seen |= b == 1
        if seen and b == 0 and fall is None:
            fall = i
            st["rel"] = True
        if fall is not None and i >= fall + 10:
            d.i_wr_en.value = 0
            break
        if i == 4:
            w1 = n
        d.i_rst_n_sw.value = 0 if i == 4 else 1
        d.i_wr_en.value = 1
        d.i_wr_data.value = c & MASK
        c += 1
    else:
        assert False, f"{cid}: o_sw_rst_busy did not fall"
    await wait_drained(tb, cid)
    await tb.settle(4)
    st["done"] = True
    await tb.settle(2)
    Wr, Rr, trs = tb.wr.recs, tb.rd.recs, tb.rd.trs
    f = ns[-1] + 1
    m = await fall_rec(tb, w1 + 1, cid)
    for i in range(f + 1, w1 + 1):
        assert Wr[i]["o_overflow"] == 1, f"{cid}: o_overflow=1 expected up to and including W1"
    for i in range(w1 + 1, m + 2):
        assert Wr[i]["o_overflow"] == 0, f"{cid}: no o_overflow pulse after W1 while blocked"
    for i in range(f, m + 1):
        assert Wr[i]["o_full"] == 1, f"{cid}: o_full=1 until busy falls"
    for i in range(f, w1):
        assert Wr[i]["o_full_thr"] == int(DEPTH >= tb.ft), f"{cid}: o_full_thr=1 before the block"
    for i in range(w1, m + 1):
        assert Wr[i]["o_full_thr"] == int(tb.ft == 0), f"{cid}: o_full_thr=empty value from the low sample"
    assert Wr[w1]["o_sw_rst_busy"] == 0 and all(Wr[i]["o_sw_rst_busy"] == 1 for i in range(w1 + 1, m + 1)), f"{cid}: busy=1 from W1+1"
    assert ncount(trs, Wr[w1]["tr"], Wr[m]["tr"]) <= 32, f"{cid}: busy must fall within 32 read edges after W1"
    assert Wr[m + 1]["o_full"] == 0 and Wr[m + 1]["o_full_thr"] == int(tb.ft == 0), f"{cid}: o_full=0, o_full_thr=0 at the fall"
    e1 = bisect_right(trs, Wr[w1]["tr"])
    e2 = bisect_right(trs, Wr[m + 1]["tr"])
    chk_lat(lead(Rr[e1:e2], "o_empty", 0), cid, "o_empty rise after W1")
    for i in range(e1 + LMAX, e2 + 2):
        assert Rr[i]["o_empty"] == 1, f"{cid}: o_empty=1 from read edge {LMAX + 1} after W1 until P0 crosses"
    for i in range(e1, e2 + 1):
        assert Rr[i]["o_rd_data"] == D[0], f"{cid}: o_rd_data=D0 before the first post-reset word crosses"
    P0 = Wr[m + 1]["i_wr_data"]
    if S >= 2:
        assert Rr[e2 + 1]["o_rd_data"] == P0, f"{cid}: P0 shown at read edge 2 after its write"
    post = [x for x in tb.sb.racc if x["tr"] > Wr[m]["tr"]]
    assert post and post[0]["o_rd_data"] == P0, f"{cid}: the first word read after the release must be P0"
    assert not [x for x in tb.sb.racc if x["o_rd_data"] in D and x["tr"] > Wr[w1]["tr"] and x["tr"] <= Wr[m]["tr"]], \
        f"{cid}: D0..D7 must be discarded"
    tb.finish()


@cocotb.test()
async def test_chk_027_read_released_first(dut):
    """CHK-027: read side released before write side, seen through the o_underflow pulse train."""
    cid = "CHK-027"
    tb = TB(dut, {WCLK: 10, RCLK: 6})
    await tb.init(ft=DEPTH, et=0)
    note_model(dut, cid)
    r = rng("chk027")
    d = dut

    async def rdrv():
        for _ in range(100000):
            await tb.rd.tick()
            d.i_rd_en.value = 1

    cocotb.start_soon(rdrv())
    for _ in range(5):
        await tb.idle(nr=r.randint(3, 11))
        w1 = await tb.w(0, sw=0)
        await tb.w(0, sw=1)
        for _ in range(100):
            await tb.wr.tick()
            if val(d.o_sw_rst_busy) == 0:
                break
        else:
            assert False, f"{cid}: o_sw_rst_busy did not fall"
        await tb.idle(nr=12, nw=2)
        m = await fall_rec(tb, w1 + 1, cid)
        Wr, trs = tb.wr.recs, tb.rd.trs
        assert m - w1 <= 32, f"{cid}: busy must fall within 32 write edges after W1"
        x = await tb.rec(tb.wr, m + 1)
        assert x["o_full"] == 0, f"{cid}: o_full=0 after the busy fall"
        e1 = bisect_right(trs, Wr[w1]["tr"])
        E = tb.rd.recs[e1:len(trs)]
        j = 1
        while j < len(E) and E[j]["o_underflow"] == 1:
            j += 1
        chk_lat(j - 1, cid, "read block after the request (underflow pulses stop)")
        k = j
        while k < len(E) and E[k]["o_underflow"] == 0:
            k += 1
        assert k < len(E), f"{cid}: o_underflow never came back after the read release"
        assert Wr[w1]["tr"] < E[k - 2]["tr"] < Wr[m]["tr"], f"{cid}: read release edge R must be after W1 and before the busy fall"
        assert all(E[i]["o_underflow"] == 1 for i in range(k, len(E))), f"{cid}: normal underflow after the release"
        assert all(e["o_empty"] == 1 for e in E), f"{cid}: o_empty=1 throughout"
    tb.finish()


@cocotb.test()
async def test_chk_028_srst_reassert_in_rel(dut):
    """CHK-028: i_rst_n_sw asserted again while the write FSM is in REL."""
    cid = "CHK-028"
    tb = TB(dut, {WCLK: 10, RCLK: 12})
    await tb.init(ft=DEPTH, et=0)
    note_model(dut, cid)
    r = rng("chk028")
    d = dut
    st = {"done": False}

    async def rdrv():
        for _ in range(20000):
            await tb.rd.tick()
            if st["done"]:
                d.i_rd_en.value = 0
                return
            d.i_rd_en.value = 1

    cocotb.start_soon(rdrv())
    for _ in range(3):
        await tb.w(1, r.getrandbits(DW))
    await tb.w(0)
    await tb.idle(nr=LMAX + 6)
    c, ph, cnt, fall, w0 = 0x2800, 0, 0, None, None
    for i in range(5000):
        n = await tb.wr.tick()
        b = val(d.o_sw_rst_busy)
        if i == 0:
            w0 = n
        if i < 20:
            sw = 0
        elif i == 20:
            sw = 1
        else:
            if ph == 0 and b == 0:
                ph = 1
            elif ph == 1 and b == 1:
                ph = 2
            if ph == 2:
                cnt += 1
                if cnt > 20:
                    ph = 3
            if ph == 3 and b == 0 and fall is None:
                fall = i
            sw = 0 if ph < 3 else 1
        if fall is not None and i >= fall + 10:
            d.i_wr_en.value = 0
            break
        d.i_rst_n_sw.value = sw
        d.i_wr_en.value = 1
        d.i_wr_data.value = c & MASK
        c += 1
    else:
        assert False, f"{cid}: sequences did not complete"
    await wait_drained(tb, cid)
    await tb.settle(4)
    st["done"] = True
    await tb.settle(2)
    Wr, Rr, trs = tb.wr.recs, tb.rd.recs, tb.rd.trs
    m1 = await fall_rec(tb, w0 + 1, cid)
    assert Wr[m1 + 2]["o_sw_rst_busy"] == 1, f"{cid}: busy must be 0 at exactly one edge between the sequences"
    m2 = await fall_rec(tb, m1 + 2, cid)
    for i in list(range(w0 + 1, m1 + 1)) + list(range(m1 + 2, m2 + 1)):
        assert Wr[i]["o_sw_rst_busy"] == 1, f"{cid}: busy=1 inside the two intervals"
    for i in range(w0, m2 + 1):
        assert Wr[i]["o_full"] == 1, f"{cid}: o_full=1 from the first low sample to m2, including the gap edge"
    for i in range(w0 + 1, m2 + 2):
        assert Wr[i]["o_overflow"] == 0, f"{cid}: o_overflow must stay 0"
    assert Wr[m2 + 1]["o_full"] == 0, f"{cid}: o_full=0 at m2+1"
    for k, (t0, mm) in enumerate(((Wr[w0]["tr"], m1), (Wr[m1 + 1]["tr"], m2))):
        e1 = bisect_right(trs, t0)
        E = Rr[e1:len(trs)]
        j = 1
        while j < len(E) and E[j]["o_underflow"] == 1:
            j += 1
        chk_lat(j - 1, cid, f"read block of sequence {k + 1}")
        u = j
        while u < len(E) and E[u]["o_underflow"] == 0:
            u += 1
        assert u < len(E), f"{cid}: o_underflow did not come back after read release {k + 1}"
        assert E[u - 2]["tr"] < Wr[mm]["tr"], f"{cid}: read release {k + 1} must precede the busy fall"
    P0 = Wr[m2 + 1]["i_wr_data"]
    post = [x for x in tb.sb.racc if x["tr"] > Wr[m2]["tr"]]
    assert post and post[0]["o_rd_data"] == P0, f"{cid}: the first post-reset word must be read first"
    tb.finish()


PAIRS29 = [(10, 10.3), (10, 23), (23, 10), (10, 37)]


@cocotb.test()
@_param(pair=PAIRS29)
async def test_chk_029_srst_random(dut, pair=PAIRS29[0]):
    """CHK-029: software resets under random traffic; no blocked access accepted, no data error, no deadlock."""
    cid = "CHK-029"
    tb = TB(dut, {WCLK: pair[0], RCLK: pair[1]})
    r = rng(f"chk029_{pair}")
    await tb.init(ft=r.randint(0, TMAX), et=r.randint(0, TMAX))
    note_model(dut, cid, need_off=False)
    not_verifiable(dut, cid, f"the other model settings / seeds of the run set are other runs (this run: model "
                   f"{'on' if MS else 'off'}, seed {plusarg('AFIFO_MSYNC_SEED')})")
    await run_traffic(tb, r, 400, cid, sw=True, nseq=30)
    n = check_busy_bounds(tb, cid)
    assert n >= 30, f"{cid}: at least 30 complete sequences expected got {n}"
    tb.finish()


@cocotb.test()
async def test_chk_030_after_srst_like_hw_reset(dut):
    """CHK-030: after a software reset the FIFO behaves like after a hardware reset (CHK-018/020/021 stimulus)."""
    cid = "CHK-030"
    tb = TB(dut, {WCLK: 10, RCLK: 14})
    await tb.init(ft=DEPTH, et=0)
    note_model(dut, cid)
    r = rng("chk030")
    d = dut
    for scn in (scn_fill_drain, scn_020, scn_021):
        for _ in range(5):
            await tb.w(1, r.getrandbits(DW))
        await tb.w(0)
        await tb.idle(nr=LMAX + 3)
        w1 = await tb.w(0, sw=0)
        await tb.w(0, sw=1)
        for _ in range(200):
            await tb.wr.tick()
            if val(d.o_sw_rst_busy) == 0:
                break
        else:
            assert False, f"{cid}: o_sw_rst_busy did not fall"
        m = await fall_rec(tb, w1 + 1, cid)
        x = await tb.rec(tb.wr, m + 1)
        assert x["o_full"] == 0 and x["o_full_thr"] == int(tb.ft == 0), f"{cid}: o_full=0, o_full_thr=(thr==0) right after the release"
        await tb.settle(S + 5)
        assert val(d.o_empty) == 1 and val(d.o_empty_thr) == 1, f"{cid}: o_empty=1, o_empty_thr=1 after the release"
        await scn(tb, cid, r)
    tb.finish()


@cocotb.test()
async def test_chk_031_clock_stop_during_srst(dut):
    """CHK-031: a clock stops during the software reset; the handshake waits and completes."""
    cid = "CHK-031"
    tb = TB(dut, {WCLK: 10, RCLK: 14})
    await tb.init(ft=DEPTH, et=0)
    note_model(dut, cid, need_off=False)
    d = dut
    c = [0x3100]

    def nd():
        c[0] += 1
        return c[0] & MASK

    for _ in range(3):
        await tb.w(1, nd())
    w1 = await tb.w(1, nd(), sw=0)
    await tb.w(1, nd(), sw=1)
    assert val(d.o_sw_rst_busy) == 1, f"{cid}: busy expected 1"
    await _maybe(stop_clock(RCLK))
    s0 = tb.wr.n
    for _ in range(60):
        await tb.w(1, nd())
    await _maybe(resume_clock(RCLK))
    t_res = get_sim_time(unit="ps")
    s1 = tb.wr.n
    for i in range(s0, s1):
        e = await tb.rec(tb.wr, i)
        assert (e["o_sw_rst_busy"], e["o_full"], e["o_overflow"]) == (1, 1, 0), f"{cid}: while i_clk_rd is stopped busy=1, full=1, overflow=0 got {e}"
    for _ in range(400):
        await tb.wr.tick()
        if val(d.o_sw_rst_busy) == 0:
            d.i_wr_en.value = 0
            break
        d.i_wr_data.value = nd()
    else:
        assert False, f"{cid}: busy did not fall after the restart"
    m = await fall_rec(tb, w1 + 1, cid)
    x = await tb.rec(tb.wr, m + 1)
    assert tb.wr.recs[m]["tr"] - t_res <= 32 * tb.slow_ps, f"{cid}: busy must fall within 32 slow edges after the restart"
    assert x["o_full"] == 0, f"{cid}: o_full=0 after the release"
    await tb.settle(S + 5)
    assert val(d.o_empty) == 1 and val(d.o_full) == 0, f"{cid}: FIFO must be empty after the reset"
    await xfer(tb, cid, nd())
    # second sequence: the write clock stops
    for _ in range(3):
        await tb.w(1, nd())
    await tb.w(0)
    await tb.idle(nr=LMAX + 3)
    w2 = await tb.w(0, sw=0)
    await tb.w(0, sw=1)
    for _ in range(40):
        await tb.rd.tick()
        if val(d.o_empty) == 1:
            break
    else:
        assert False, f"{cid}: o_empty did not rise"
    await tb.rd.tick(2)
    await _maybe(stop_clock(WCLK))
    r0 = tb.rd.n
    for _ in range(60):
        await tb.r(1)
    r1 = tb.rd.n
    await _maybe(resume_clock(WCLK))
    t_res = get_sim_time(unit="ps")
    await tb.r(0)
    for i in range(r0, r1 + 1):
        e = await tb.rec(tb.rd, i)
        assert e["o_empty"] == 1, f"{cid}: o_empty=1 and no read while i_clk_wr is stopped"
    for _ in range(400):
        await tb.wr.tick()
        if val(d.o_sw_rst_busy) == 0:
            break
    else:
        assert False, f"{cid}: busy did not fall after the write clock restart"
    m = await fall_rec(tb, w2 + 1, cid)
    await tb.rec(tb.wr, m + 1)
    assert tb.wr.recs[m]["tr"] - t_res <= 32 * tb.slow_ps, f"{cid}: busy must fall within 32 slow edges after the restart"
    await tb.settle(S + 5)
    assert val(d.o_empty) == 1 and val(d.o_full) == 0, f"{cid}: FIFO must be empty after the reset"
    await xfer(tb, cid, nd())
    tb.finish()


THR32 = [(0, 0), (3, 5), (8, 8), (9, 15), (15, 1), (6, 2)]


@cocotb.test()
@_param(thr=THR32)
async def test_chk_032_threshold_flags(dut, thr=THR32[1]):
    """CHK-032: o_full_thr / o_empty_thr while filling and draining across the thresholds."""
    cid = "CHK-032"
    tb = TB(dut, {WCLK: 10, RCLK: 14})
    await tb.init(ft=thr[0], et=thr[1])
    note_model(dut, cid)
    if thr[0] > TMAX or thr[1] > TMAX:
        not_verifiable(dut, cid, f"threshold pair {thr} exceeds the {PTR_W}-bit threshold ports of this configuration")
    ft, et = tb.ft, tb.et
    r = rng(f"chk032_{thr}")
    d = dut
    assert val(d.o_full_thr) == int(ft == 0) and val(d.o_empty_thr) == 1, f"{cid}: after reset o_full_thr=(thr==0), o_empty_thr=1"
    for k in range(1, DEPTH + 1):
        nw = await tb.write_word(r.getrandbits(DW))
        e = await tb.rec(tb.wr, nw + 1)
        assert e["o_full_thr"] == int(k >= ft), f"{cid}: count {k}: o_full_thr={int(k >= ft)} expected at the next write edge got {e['o_full_thr']}"
        E = await tb.after(tb.rd, tb.wr.recs[nw]["tr"], LMAX + 4)
        chk_trans(E, "o_empty_thr", int(k - 1 <= et), int(k <= et), cid, f"o_empty_thr after write to count {k}")
        await tb.idle(nr=2)
    for k in range(DEPTH - 1, -1, -1):
        nr = await tb.r(1)
        await tb.r(0)
        e = await tb.rec(tb.rd, nr)
        assert e["o_empty"] == 0, f"{cid}: read expected to be accepted"
        e1 = await tb.rec(tb.rd, nr + 1)
        assert e1["o_empty_thr"] == int(k <= et), f"{cid}: count {k}: o_empty_thr={int(k <= et)} at the next read edge got {e1['o_empty_thr']}"
        E = await tb.after(tb.wr, e["tr"], LMAX + 4)
        chk_trans(E, "o_full_thr", int(k + 1 >= ft), int(k >= ft), cid, f"o_full_thr after read to count {k}")
        await tb.idle(nw=2)
    tb.finish()


@cocotb.test()
async def test_regression_random(dut):
    """CHK-001..CHK-013 exercised, CHK-005/CHK-006 scoreboard: broad random traffic with software and hardware resets."""
    r = rng("regression")
    tb = TB(dut)
    await tb.init(ft=r.randint(0, TMAX), et=r.randint(0, TMAX))
    note_model(dut, "CHK-005", need_off=False)
    await run_traffic(tb, r, 1200, "CHK-005", sw=True, nseq=6)
    W, R = tb.models(r)
    W.d, R.d = 0.6, 0.6
    W.gate = R.gate = False
    await tb.wr.tick(r.randint(5, 30))
    W.run = R.run = False
    W.plan.clear()
    d = dut
    d.i_rst_n_wr.value = 0
    d.i_rst_n_rd.value = 0
    tb.sb.clear()
    await ReadOnly()
    chk_wr_rst(tb, "CHK-007")
    chk_rd_rst(tb, "CHK-001")
    await tb.wr.tick(4)
    d.i_rst_n_wr.value = 1
    await tb.rd.tick(2)
    d.i_rst_n_rd.value = 1
    await tb.settle(3)
    await run_traffic(tb, r, 600, "CHK-005", sw=True, nseq=3)
    cov = coverage(tb)
    dut._log.info(f"regression coverage {cov}")
    assert cov["full"] and cov["empty"] and cov["ovf"] and cov["udf"], f"CHK-016: regression coverage not reached {cov}"
    check_busy_bounds(tb, "CHK-011")
    tb.finish()

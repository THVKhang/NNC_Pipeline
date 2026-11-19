"""cocotb 2.1 testbench for m_vlsit_sfifo_top (synchronous two-clock FIFO), plan CFG-BASE.

* Inputs are driven right after a falling edge of their own clock; directed tests sample outputs at
  falling edges (= value seen by the next rising edge).
* A passive reference model (Monitor) runs in every test. It wakes on every change of the two clocks
  and three resets, snapshots all ports in ReadOnly, and so knows the exact pre-edge values at each
  rising edge (also at coincident edges). It implements CHK-001, CHK-003..CHK-011 from ports only.
* Tests needing other clock ratios are parametrized (one sub-test per ratio); each sub-test starts its
  clocks while both hardware resets are asserted and ends with both resets asserted.
* All absolute time arithmetic is done in integer picoseconds (the clocks of a sub-test may start at a
  time that is not a whole number of ns).
"""

import inspect
import math
import random
from collections import deque
from types import SimpleNamespace

from nnc_cocotb import *  # noqa: F401,F403

import cocotb
from cocotb.triggers import FallingEdge, First, ReadOnly, RisingEdge, Timer

try:
    from cocotb.triggers import ValueChange as _ValueChange
except ImportError:  # pragma: no cover
    from cocotb.triggers import Edge as _ValueChange

from cocotb.utils import get_sim_time


def _param(name, default):
    try:
        return int(PARAMS.get(name, default))
    except Exception:
        return default


DEPTH = _param("PARA_SFIFO_DEPTH", 8)
DW = _param("PARA_SFIFO_DATA_W", 32)
RETIME = _param("PARA_SFIFO_PTR_RETIME", 0)
OCC_W = _param("LPARA_OCC_W", max(1, DEPTH.bit_length()))
LAT = 1 + RETIME
MASK = (1 << DW) - 1
THR_MAX = (1 << OCC_W) - 1
WR = "i_clk_wr"
RD = "i_clk_rd"


# ------------------------------------------------------------------ time helpers
def now_ps():
    try:
        t = get_sim_time(unit="ps")
    except TypeError:
        t = get_sim_time(units="ps")
    return int(round(float(t)))


def now_ns():
    return now_ps() / 1000.0


def _timer(ns):
    try:
        return Timer(ns, unit="ns")
    except TypeError:
        return Timer(ns, units="ns")


def _timer_ps(ps):
    try:
        return Timer(int(ps), unit="ps")
    except TypeError:
        return Timer(int(ps), units="ps")


async def goto(t):
    """Wait until absolute time t (ns, may be fractional); computed in integer ps."""
    target = int(round(t * 1000.0))
    dt = target - now_ps()
    assert dt >= 0, f"testbench scheduling error: target {t} ns already passed (now {now_ns()} ns)"
    if dt > 0:
        await _timer_ps(dt)


async def run_actions(acts):
    """acts: list of (time_ns, priority, fn), executed in time order (lower priority first)."""
    for t, _p, fn in sorted(acts, key=lambda a: (a[0], a[1])):
        await goto(t)
        fn()


async def _nv(dut, chk, why):
    res = not_verifiable(dut, chk, why)
    if inspect.isawaitable(res):
        await res


def _parse_ratio(ratio):
    a, b = ratio.split("_")
    return int(a), int(b)


def _ratios(values):
    par = getattr(cocotb, "parametrize", None)
    if par is not None:
        return par(ratio=values)

    def deco(f):
        async def wrapper(dut):
            await f(dut, values[0])
        wrapper.__name__ = f.__name__
        wrapper.__qualname__ = f.__qualname__
        wrapper.__doc__ = f.__doc__
        return wrapper
    return deco


# ------------------------------------------------------------------ sampling
def sample(d):
    return SimpleNamespace(full=val(d.o_full), fthr=val(d.o_full_thr), ovf=val(d.o_overflow),
                           busy=val(d.o_sw_rst_busy), empty=val(d.o_empty), ethr=val(d.o_empty_thr),
                           unf=val(d.o_underflow), rdat=val(d.o_rd_data))


_RESET_VALUES = (("full", 0, "o_full"), ("fthr", 0, "o_full_thr"), ("ovf", 0, "o_overflow"),
                 ("busy", 0, "o_sw_rst_busy"), ("empty", 1, "o_empty"), ("ethr", 1, "o_empty_thr"),
                 ("unf", 0, "o_underflow"))


def check_reset_values(s, chk, where):
    for k, v, n in _RESET_VALUES:
        got = getattr(s, k)
        assert got == v, f"{chk}: {n}={v} expected {where}, got {got}"


_SNAP = (("cw", "i_clk_wr"), ("cr", "i_clk_rd"), ("rw", "i_rst_n_wr"), ("rr", "i_rst_n_rd"),
         ("sw", "i_rst_n_sw"), ("we", "i_wr_en"), ("wd", "i_wr_data"), ("re", "i_rd_en"),
         ("ft", "i_full_thr"), ("et", "i_empty_thr"), ("busy", "o_sw_rst_busy"), ("full", "o_full"),
         ("fthr", "o_full_thr"), ("ovf", "o_overflow"), ("empty", "o_empty"), ("ethr", "o_empty_thr"),
         ("unf", "o_underflow"), ("rdat", "o_rd_data"))


def _snap(dut):
    s = {k: val(getattr(dut, n)) for k, n in _SNAP}
    s["rdat_raw"] = str(dut.o_rd_data.value)
    return s


# ------------------------------------------------------------------ reference model
class Monitor:
    """Scoreboard Q, counters WA/RA, write view (CHK-010) and read view (CHK-004)."""

    def __init__(self, dut):
        self.dut = dut
        self.q = deque()
        self.wa = self.ra = 0
        self.rd_pipe = self.wr_pipe = 0
        self.exp_w_occ = 0
        self.thr_valid = False
        self.exp_r_occ = 0
        self.rd_prev_busy = 0
        self.armed = False
        self.reads, self.writes, self.rd_log, self.wr_log = [], [], [], []
        self.n_ovf = self.n_unf = self.n_sw = self.n_coinc = self.n_coinc_ops = 0
        self.last_coinc = None

    def _clear_data(self):
        self.q.clear()
        self.wa = self.ra = 0
        self.rd_pipe = self.wr_pipe = 0

    def _clear_wr(self):
        self.exp_w_occ = 0
        self.thr_valid = False

    def _clear_rd(self):
        self.exp_r_occ = 0
        self.rd_prev_busy = 0

    async def run(self):
        d = self.dut
        sigs = (d.i_clk_wr, d.i_clk_rd, d.i_rst_n_wr, d.i_rst_n_rd, d.i_rst_n_sw)
        await ReadOnly()
        prev = _snap(d)
        for _ in range(100_000_000):
            await First(*[_ValueChange(s) for s in sigs])
            await ReadOnly()
            cur = _snap(d)
            self._step(prev, cur)
            prev = cur

    def _step(self, P, S):
        t = now_ns()
        if not self.armed:
            if S["rw"] == 0 and S["rr"] == 0:
                self.armed = True
                self._clear_wr()
                self._clear_rd()
                self._clear_data()
            return
        wr_rise = P["cw"] == 0 and S["cw"] == 1
        rd_rise = P["cr"] == 0 and S["cr"] == 1
        rw_fell = P["rw"] == 1 and S["rw"] == 0
        rr_fell = P["rr"] == 1 and S["rr"] == 0
        sw_chg = P["sw"] != S["sw"]
        if wr_rise and rd_rise:
            self.last_coinc = t
            self.n_coinc += 1
        self._check_changes(P, S, t, wr_rise, rd_rise, rw_fell, rr_fell, sw_chg)
        both = P["rw"] == 1 and P["rr"] == 1 and S["rw"] == 1 and S["rr"] == 1
        wa0, ra0 = self.wa, self.ra
        rd_acc = wr_acc = False
        if rd_rise and P["rr"] == 1 and S["rr"] == 1:
            rd_acc = self._rd_edge(P, S, t, both, wa0)
        if wr_rise and P["rw"] == 1 and S["rw"] == 1:
            wr_acc = self._wr_edge(P, S, t, both, ra0)
        if rd_acc and wr_acc:
            self.n_coinc_ops += 1
        if sw_chg and not wr_rise and S["rw"] == 1 and S["rr"] == 1 and (S["sw"] == 0 or S["busy"] == 1):
            assert S["full"] == 1, f"CHK-009: o_full=1 expected right after i_rst_n_sw change got {S['full']} at {t} ns"
            exp = 1 if S["ft"] == 0 else 0
            assert S["fthr"] == exp, f"CHK-009: o_full_thr={exp} expected right after i_rst_n_sw change got {S['fthr']} at {t} ns"
        if S["rw"] == 0:
            assert S["ovf"] == 0, f"CHK-011: o_overflow=0 expected while i_rst_n_wr=0 got {S['ovf']} at {t} ns"
            assert S["busy"] == 0, f"CHK-008: o_sw_rst_busy=0 expected while i_rst_n_wr=0 got {S['busy']} at {t} ns"
            if S["sw"] == 1:
                assert S["full"] == 0, f"CHK-021: o_full=0 expected while i_rst_n_wr=0 got {S['full']} at {t} ns"
                assert S["fthr"] == 0, f"CHK-021: o_full_thr=0 expected while i_rst_n_wr=0 got {S['fthr']} at {t} ns"
            self._clear_wr()
        if S["rr"] == 0:
            assert S["empty"] == 1, f"CHK-021: o_empty=1 expected while i_rst_n_rd=0 got {S['empty']} at {t} ns"
            assert S["ethr"] == 1, f"CHK-021: o_empty_thr=1 expected while i_rst_n_rd=0 got {S['ethr']} at {t} ns"
            assert S["unf"] == 0, f"CHK-005: o_underflow=0 expected while i_rst_n_rd=0 got {S['unf']} at {t} ns"
            self._clear_rd()
        if S["rw"] == 0 or S["rr"] == 0:
            self._clear_data()

    def _check_changes(self, P, S, t, wr_rise, rd_rise, rw_fell, rr_fell, sw_chg):
        wr_ok = wr_rise or rw_fell
        for k, n in (("ovf", "o_overflow"), ("busy", "o_sw_rst_busy")):
            if P[k] != S[k]:
                assert wr_ok, f"CHK-001: {n} may change only after an i_clk_wr rising edge or i_rst_n_wr assertion, got {P[k]}->{S[k]} at {t} ns"
        for k, n in (("full", "o_full"), ("fthr", "o_full_thr")):
            if P[k] != S[k]:
                assert wr_ok or sw_chg, f"CHK-001: {n} may change only at i_clk_wr edge, i_rst_n_wr fall or i_rst_n_sw change, got {P[k]}->{S[k]} at {t} ns"
        if P["unf"] != S["unf"]:
            assert rd_rise or rr_fell, f"CHK-001: o_underflow changed {P['unf']}->{S['unf']} without i_clk_rd edge/reset at {t} ns"
        if P["rdat_raw"] != S["rdat_raw"]:
            assert rd_rise, f"CHK-001: o_rd_data changed without an i_clk_rd rising edge at {t} ns"
        for k, n in (("empty", "o_empty"), ("ethr", "o_empty_thr")):
            if P[k] != S[k]:
                blk = wr_rise and P["busy"] == 0 and S["busy"] == 1 and S[k] == 1
                assert rd_rise or rr_fell or blk, f"CHK-001: {n} changed {P[k]}->{S[k]} without a legal cause at {t} ns"

    def _rd_edge(self, P, S, t, both, wa0):
        re = P["re"] == 1
        emp = P["empty"]
        if S["unf"] == 1:
            self.n_unf += 1
            assert re and emp == 1, f"CHK-005: o_underflow=1 only after read on empty FIFO; got i_rd_en={P['re']} o_empty={emp} at {t} ns"
        if P["busy"] == 0:
            exp = 1 if (re and emp == 1) else 0
            assert S["unf"] == exp, f"CHK-005: o_underflow={exp} expected after read edge got {S['unf']} at {t} ns"
        if both and P["busy"] == 1:
            assert emp == 1 and P["ethr"] == 1, \
                f"CHK-003: o_empty=1 and o_empty_thr=1 expected while o_sw_rst_busy=1 got {emp},{P['ethr']} at {t} ns"
        if P["busy"] == 0 and self.rd_prev_busy == 0:
            e_exp = 1 if self.exp_r_occ == 0 else 0
            assert emp == e_exp, f"CHK-004: o_empty={e_exp} expected (read-view occupancy {self.exp_r_occ}) got {emp} at {t} ns"
            et_exp = 1 if self.exp_r_occ <= P["et"] else 0
            assert P["ethr"] == et_exp, \
                f"CHK-004: o_empty_thr={et_exp} expected (occupancy {self.exp_r_occ}, thr {P['et']}) got {P['ethr']} at {t} ns"
        self.rd_prev_busy = P["busy"]
        acc = False
        if both:
            n = len(self.q)
            assert 0 <= n <= DEPTH, f"CHK-007: occupancy within 0..{DEPTH} expected got {n} at {t} ns"
            if n == 0:
                assert emp == 1, f"CHK-007: o_empty=1 expected with no stored word got {emp} at {t} ns"
            if emp == 0:
                assert n > 0, f"CHK-006: o_empty=0 with empty reference queue at {t} ns"
                assert P["rdat"] == self.q[0], \
                    f"CHK-006: o_rd_data=0x{self.q[0]:x} expected got {P['rdat']} at {t} ns"
                if re:
                    self.reads.append(self.q.popleft())
                    self.ra += 1
                    acc = True
            else:
                assert emp == 1, f"CHK-006: o_empty is unknown at read edge {t} ns"
        self.rd_log.append(SimpleNamespace(t=t, busy=P["busy"], sw=P["sw"], re=P["re"], empty=emp,
                                           ethr=P["ethr"], unf=S["unf"], acc=acc))
        if RETIME:
            wa_view = self.rd_pipe
            self.rd_pipe = wa0
        else:
            wa_view = wa0
        self.exp_r_occ = wa_view - self.ra
        return acc

    def _wr_edge(self, P, S, t, both, ra0):
        we = P["we"] == 1
        full, sw, busy = P["full"], P["sw"], P["busy"]
        exp_ovf = 1 if (we and full == 1 and sw == 1 and busy == 0) else 0
        assert S["ovf"] == exp_ovf, f"CHK-011: o_overflow={exp_ovf} expected after write edge got {S['ovf']} at {t} ns"
        if S["ovf"] == 1:
            self.n_ovf += 1
        if busy == 0:
            exp_b = 1 if sw == 0 else 0
            assert S["busy"] == exp_b, f"CHK-008: o_sw_rst_busy={exp_b} expected after edge (i_rst_n_sw={sw}) got {S['busy']} at {t} ns"
        if both and (sw == 0 or busy == 1):
            assert full == 1, f"CHK-009: o_full=1 expected while writes blocked got {full} at {t} ns"
            exp = 1 if P["ft"] == 0 else 0
            assert P["fthr"] == exp, f"CHK-009: o_full_thr={exp} expected while blocked got {P['fthr']} at {t} ns"
        if sw == 1 and busy == 0:
            f_exp = 1 if self.exp_w_occ == DEPTH else 0
            assert full == f_exp, f"CHK-010: o_full={f_exp} expected (write-view occupancy {self.exp_w_occ}) got {full} at {t} ns"
            if self.thr_valid:
                ft_exp = 1 if self.exp_w_occ >= P["ft"] else 0
                assert P["fthr"] == ft_exp, \
                    f"CHK-010: o_full_thr={ft_exp} expected (occupancy {self.exp_w_occ}, thr {P['ft']}) got {P['fthr']} at {t} ns"
        acc = False
        if both:
            n = len(self.q)
            assert n <= DEPTH, f"CHK-007: occupancy <= {DEPTH} expected got {n} at {t} ns"
            if n == DEPTH:
                assert full == 1, f"CHK-007: o_full=1 expected with {DEPTH} stored words got {full} at {t} ns"
            if we and full == 0:
                assert P["wd"] is not None, f"CHK-002: i_wr_data unknown at accepted write {t} ns"
                self.q.append(P["wd"] & MASK)
                self.writes.append(P["wd"] & MASK)
                self.wa += 1
                acc = True
        self.wr_log.append(SimpleNamespace(t=t, busy=busy, sw=sw, we=P["we"], full=full, ovf=S["ovf"], acc=acc))
        if RETIME:
            ra_view = self.wr_pipe
            self.wr_pipe = ra0
        else:
            ra_view = ra0
        self.exp_w_occ = self.wa - ra_view
        self.thr_valid = True
        if busy == 1 and S["busy"] == 0:
            self._clear_data()
            self.exp_w_occ = 0
            self.n_sw += 1
        return acc


# ------------------------------------------------------------------ environment
class Env:
    def __init__(self, dut):
        self.dut = dut
        self.pw = self.pr = None
        self.mon = None

    def idle(self):
        d = self.dut
        d.i_wr_en.value = 0
        d.i_rd_en.value = 0
        d.i_rst_n_sw.value = 1
        d.i_wr_data.value = 0

    async def _measure(self, sig):
        await RisingEdge(sig)
        t0 = now_ps()
        await RisingEdge(sig)
        return (now_ps() - t0) / 1000.0

    async def start(self, periods=None, full_thr=None, empty_thr=0):
        d = self.dut
        self.idle()
        d.i_full_thr.value = DEPTH if full_thr is None else full_thr
        d.i_empty_thr.value = empty_thr
        d.i_rst_n_wr.value = 0
        d.i_rst_n_rd.value = 0
        if periods is None:
            res = start_clock(d)
        else:
            res = start_clock(d, periods={WR: periods[0], RD: periods[1]})
        if inspect.isawaitable(res):
            await res
        self.mon = Monitor(d)
        cocotb.start_soon(self.mon.run())
        if periods is None:
            self.pw = await self._measure(d.i_clk_wr)
            self.pr = await self._measure(d.i_clk_rd)
        else:
            self.pw, self.pr = periods
        return self.mon

    def integral(self):
        return abs(self.pw - round(self.pw)) < 1e-6 and abs(self.pr - round(self.pr)) < 1e-6

    async def next_coincident(self):
        """Time (ns, exact to 1 ps) of a future rising edge common to both clocks."""
        d = self.dut
        pw_ps, pr_ps = int(round(self.pw * 1000)), int(round(self.pr * 1000))
        await RisingEdge(d.i_clk_wr)
        t1 = now_ps()
        await RisingEdge(d.i_clk_rd)
        t2 = now_ps()
        for k in range(1, 4 * int(round(self.pr)) + 4):
            t = t1 + k * pw_ps
            if t > t2 and (t - t2) % pr_ps == 0:
                return t / 1000.0
        raise AssertionError("CHK-013: no coincident rising edge found; clocks are not synchronous")

    async def release(self, order):
        d = self.dut
        if order == "wr_first":
            await FallingEdge(d.i_clk_wr)
            d.i_rst_n_wr.value = 1
            await RisingEdge(d.i_clk_rd)
            await FallingEdge(d.i_clk_rd)
            d.i_rst_n_rd.value = 1
        elif order == "rd_first":
            await FallingEdge(d.i_clk_rd)
            d.i_rst_n_rd.value = 1
            await RisingEdge(d.i_clk_wr)
            await FallingEdge(d.i_clk_wr)
            d.i_rst_n_wr.value = 1
        else:
            if abs(self.pw - self.pr) < 1e-6:
                await FallingEdge(d.i_clk_wr)
            else:
                t = await self.next_coincident()
                await goto(t + 1)
            d.i_rst_n_wr.value = 1
            d.i_rst_n_rd.value = 1

    async def hw_reset(self, full_thr, empty_thr, order="both", hold=3):
        d = self.dut
        await FallingEdge(d.i_clk_wr)
        self.idle()
        d.i_rst_n_wr.value = 0
        d.i_rst_n_rd.value = 0
        await _timer(1)
        d.i_full_thr.value = full_thr
        d.i_empty_thr.value = empty_thr
        for _ in range(hold + 1):
            await RisingEdge(d.i_clk_wr)
        for _ in range(hold + 1):
            await RisingEdge(d.i_clk_rd)
        await self.release(order)

    async def finish(self):
        d = self.dut
        await FallingEdge(d.i_clk_wr)
        self.idle()
        d.i_rst_n_wr.value = 0
        d.i_rst_n_rd.value = 0
        await _timer(1)


# ------------------------------------------------------------------ drivers
async def eq_run(env, n, wr_fn=None, rd_fn=None):
    """Equal clocks: returns samples s[0..n]; s[k] = values before edge E_k; drives E_0..E_{n-1}."""
    d = env.dut
    out = []
    for k in range(n + 1):
        await FallingEdge(d.i_clk_wr)
        s = sample(d)
        out.append(s)
        if k == n:
            d.i_wr_en.value = 0
            d.i_rd_en.value = 0
            break
        w = wr_fn(k, s) if wr_fn is not None else None
        if w is None:
            d.i_wr_en.value = 0
        else:
            d.i_wr_en.value = 1
            d.i_wr_data.value = w & MASK
        d.i_rd_en.value = 1 if (rd_fn is not None and rd_fn(k, s)) else 0
    return out


async def write_words(env, words, max_cycles=None):
    """Writes each word only when the write is sure to be accepted; returns at the write falling
    edge after the last accepting edge."""
    d = env.dut
    max_cycles = max_cycles or (8 * len(words) + 200)
    i = 0
    for _ in range(max_cycles):
        await FallingEdge(d.i_clk_wr)
        if (i < len(words) and val(d.o_full) == 0 and val(d.o_sw_rst_busy) == 0
                and val(d.i_rst_n_sw) == 1):
            d.i_wr_en.value = 1
            d.i_wr_data.value = words[i] & MASK
            i += 1
        else:
            d.i_wr_en.value = 0
            if i >= len(words):
                return
    raise AssertionError(f"CHK-006: only {i} of {len(words)} writes accepted within {max_cycles} write cycles")


async def read_words(env, n, max_cycles=None):
    d = env.dut
    max_cycles = max_cycles or (8 * n + 200)
    got = []
    for _ in range(max_cycles):
        await FallingEdge(d.i_clk_rd)
        if len(got) < n and val(d.o_empty) == 0:
            got.append(val(d.o_rd_data))
            d.i_rd_en.value = 1
        else:
            d.i_rd_en.value = 0
            if len(got) >= n:
                return got
    raise AssertionError(f"CHK-006: only {len(got)} of {n} words became readable within {max_cycles} read cycles")


async def _rand_writer(env, r, stop, sw_prob, max_cycles=2_000_000):
    d = env.dut
    dens = r.uniform(0.1, 1.0)
    sw_left, sw_wait, saw_busy = 0, False, False
    for i in range(max_cycles):
        await FallingEdge(d.i_clk_wr)
        busy = val(d.o_sw_rst_busy)
        if stop[0]:
            d.i_wr_en.value = 0
            d.i_rst_n_sw.value = 1
            return
        if busy == 1:
            saw_busy = True
        if i % 40 == 0:
            dens = r.choice((0.1, 0.25, 0.5, 0.75, 0.9, 1.0))
        if sw_left > 0:
            sw_left -= 1
            d.i_rst_n_sw.value = 0
        else:
            d.i_rst_n_sw.value = 1
            if sw_wait and saw_busy and busy == 0:
                sw_wait = False
            if (not sw_wait) and busy == 0 and r.random() < sw_prob:
                d.i_rst_n_sw.value = 0
                sw_left = r.randint(1, 10) - 1
                sw_wait, saw_busy = True, False
        d.i_wr_en.value = 1 if r.random() < dens else 0
        d.i_wr_data.value = r.getrandbits(DW)
    raise AssertionError("random writer: cycle limit reached")


async def _rand_reader(env, r, stop, max_cycles=2_000_000):
    d = env.dut
    dens = r.uniform(0.1, 1.0)
    for i in range(max_cycles):
        await FallingEdge(d.i_clk_rd)
        if stop[0]:
            d.i_rd_en.value = 0
            return
        if i % 40 == 0:
            dens = r.choice((0.1, 0.25, 0.5, 0.75, 0.9, 1.0))
        d.i_rd_en.value = 1 if r.random() < dens else 0
    raise AssertionError("random reader: cycle limit reached")


async def random_traffic(env, r, duration_ns, sw_prob):
    stop = [False]
    wt = cocotb.start_soon(_rand_writer(env, random.Random(r.getrandbits(32)), stop, sw_prob))
    rt = cocotb.start_soon(_rand_reader(env, random.Random(r.getrandbits(32)), stop))
    await _timer(int(duration_ns))
    stop[0] = True
    await wt
    await rt


async def drain(env, chk):
    d, mon = env.dut, env.mon
    for _ in range(200):
        await FallingEdge(d.i_clk_wr)
        if val(d.o_sw_rst_busy) == 0 and val(d.i_rst_n_sw) == 1:
            break
    else:
        raise AssertionError(f"{chk}: o_sw_rst_busy=0 expected within 200 write cycles before the drain")
    quiet = 0
    for _ in range(64 + 16 * DEPTH):
        await FallingEdge(d.i_clk_rd)
        e = val(d.o_empty)
        d.i_rd_en.value = 1 if e == 0 else 0
        quiet = quiet + 1 if (e == 1 and len(mon.q) == 0) else 0
        if quiet >= 3:
            break
    d.i_rd_en.value = 0
    assert len(mon.q) == 0, f"{chk}: scoreboard empty expected after the drain got {len(mon.q)} words"
    assert val(d.o_empty) == 1, f"{chk}: o_empty=1 expected after the drain got {val(d.o_empty)}"


async def stream_writer(env, stop, log, cnt, max_cycles=200000):
    d = env.dut
    for _ in range(max_cycles):
        await FallingEdge(d.i_clk_wr)
        full, ovf = val(d.o_full), val(d.o_overflow)
        if stop[0]:
            d.i_wr_en.value = 0
            log.append((full, ovf, 0))
            return
        d.i_wr_en.value = 1
        d.i_wr_data.value = cnt[0] & MASK
        log.append((full, ovf, 1))
        if full == 0:
            cnt[0] += 1


async def stream_reader(env, stop, log, words, max_cycles=200000):
    d = env.dut
    for _ in range(max_cycles):
        await FallingEdge(d.i_clk_rd)
        e, u, x = val(d.o_empty), val(d.o_underflow), val(d.o_rd_data)
        if stop[0]:
            d.i_rd_en.value = 0
            log.append((e, u, 0))
            return
        d.i_rd_en.value = 1
        log.append((e, u, 1))
        if e == 0:
            words.append(x)


# ================================================================== tests
@cocotb.test()
async def test_chk_012_strict_later_latency_3_2(dut):
    """CHK-012: o_empty / o_full fall after the first strictly later edge at every alignment of 3:2."""
    d = dut
    pw, pr, L = 8, 12, 24
    env = Env(dut)
    mon = await env.start((pw, pr), DEPTH, 0)
    await env.hw_reset(DEPTH, 0, "both")
    r = rng("chk012")
    tc = await env.next_coincident()

    def next_base():
        k = math.ceil((now_ns() + 2 * L - tc) / L)
        return tc + k * L

    def rd_on():
        d.i_rd_en.value = 1

    def rd_off():
        d.i_rd_en.value = 0

    written = []
    for name, ow, plan_vis in (("A", 0, 24), ("B", 8, 24), ("C", 16, 36)):
        w = r.getrandbits(DW)
        written.append(w)
        base = next_base()
        tw = base + ow
        rd_edges = [base + pr * m for m in range(0, 12)]
        later = [e for e in rd_edges if e > tw + 1e-6]
        vis = later[LAT - 1] + pr
        if RETIME == 0:
            assert abs((vis - base) - plan_vis) < 1e-6, f"CHK-012: testbench timeline error case {name}"
        samples = {}

        def wr_on(w=w):
            d.i_wr_en.value = 1
            d.i_wr_data.value = w

        def wr_off():
            d.i_wr_en.value = 0
        acts = [(tw - pw // 2, 1, wr_on), (tw + pw // 2, 1, wr_off),
                (vis - pr // 2, 1, rd_on), (vis + pr // 2, 1, rd_off)]
        for e in rd_edges:
            if e <= vis + 1e-6:
                acts.append((e - pr // 2, 0, lambda e=e: samples.__setitem__(e, sample(d))))
        await run_actions(acts)
        for e in sorted(samples):
            s = samples[e]
            if e < vis - 1e-6:
                assert s.empty == 1, f"CHK-012: case {name}: o_empty=1 expected at read edge base+{e - base:.0f} got {s.empty}"
            else:
                assert s.empty == 0, f"CHK-012: case {name}: o_empty=0 expected at read edge base+{e - base:.0f} got {s.empty}"
                assert s.rdat == w, f"CHK-012: case {name}: o_rd_data=0x{w:x} expected got {s.rdat}"
        await FallingEdge(d.i_clk_rd)
        assert val(d.o_empty) == 1, f"CHK-012: case {name}: o_empty=1 expected after reading the word"

    words = [r.getrandbits(DW) for _ in range(DEPTH)]
    written += words
    await write_words(env, words)
    assert val(d.o_full) == 1, f"CHK-012: o_full=1 expected after {DEPTH} writes got {val(d.o_full)}"
    for _ in range(3):
        await FallingEdge(d.i_clk_rd)
    for name, orr, plan_vis in (("D", 0, 16), ("E", 12, 24)):
        base = next_base()
        tr = base + orr
        wr_edges = [base + pw * k for k in range(0, 12)]
        later = [e for e in wr_edges if e > tr + 1e-6]
        vis = later[LAT - 1] + pw
        if RETIME == 0:
            assert abs((vis - base) - plan_vis) < 1e-6, f"CHK-012: testbench timeline error case {name}"
        samples, rs = {}, {}
        acts = [(tr - pr // 2, 0, lambda: rs.__setitem__("s", sample(d))),
                (tr - pr // 2, 1, rd_on), (tr + pr // 2, 1, rd_off)]
        for e in wr_edges:
            if e <= vis + 1e-6:
                acts.append((e - pw // 2, 0, lambda e=e: samples.__setitem__(e, sample(d))))
        await run_actions(acts)
        assert rs["s"].empty == 0, f"CHK-012: case {name}: o_empty=0 expected at the read edge got {rs['s'].empty}"
        for e in sorted(samples):
            s = samples[e]
            exp = 1 if e < vis - 1e-6 else 0
            assert s.full == exp, f"CHK-012: case {name}: o_full={exp} expected at write edge base+{e - base:.0f} got {s.full}"
        nw = r.getrandbits(DW)
        written.append(nw)
        await write_words(env, [nw])
        for _ in range(3):
            await FallingEdge(d.i_clk_rd)
    await read_words(env, DEPTH)
    assert mon.reads == written, "CHK-012: read order expected to equal write order"
    await env.finish()


RATIOS_013 = ["10_10", "12_8", "8_12", "8_16", "16_8", "12_28", "28_12", "36_8"]


@cocotb.test()
@_ratios(RATIOS_013)
async def test_chk_013_random_ratios(dut, ratio):
    """CHK-013: constrained-random traffic with scoreboard over clock ratios and reset release phases."""
    pw, pr = _parse_ratio(ratio)
    env = Env(dut)
    mon = await env.start((pw, pr))
    r = rng(f"chk013_{ratio}")
    for order in ("wr_first", "rd_first", "both"):
        ft, et = r.randint(0, THR_MAX), r.randint(0, THR_MAX)
        await env.hw_reset(ft, et, order)
        n0 = len(mon.reads)
        await random_traffic(env, r, 300 * max(pw, pr), sw_prob=0.02)
        await drain(env, "CHK-013")
        dut._log.info(f"CHK-013 {ratio} {order}: reads={len(mon.reads) - n0} ovf={mon.n_ovf} unf={mon.n_unf} "
                      f"sw={mon.n_sw} coincident ops={mon.n_coinc_ops}")
    assert len(mon.reads) > 0, "CHK-013: some words expected to be transferred"
    await env.finish()


@cocotb.test()
async def test_chk_014_first_word_show_ahead(dut):
    """CHK-014: first-word latency with equal clocks, show-ahead, no bubble, o_empty after last read."""
    env = Env(dut)
    mon = await env.start((10, 10), DEPTH, 0)
    await env.hw_reset(DEPTH, 0, "both")
    if RETIME != 0:
        await _nv(dut, "CHK-014", "directed edge timeline written for PARA_SFIFO_PTR_RETIME=0")
        return
    r = rng("chk014")
    D = [r.getrandbits(DW) for _ in range(5)]
    wmap = {0: D[0], 5: D[1], 6: D[2], 7: D[3], 8: D[4]}
    rset = {2, 7, 8, 9, 10}
    s = await eq_run(env, 13, lambda k, _s: wmap.get(k), lambda k, _s: k in rset)
    for k in (0, 1):
        assert s[k].empty == 1, f"CHK-014: o_empty=1 expected at E{k} got {s[k].empty}"
    assert s[2].empty == 0 and s[2].rdat == D[0], f"CHK-014: o_empty=0, o_rd_data=D0 expected at E2 got {s[2].empty},{s[2].rdat}"
    assert s[2].ethr == 0, f"CHK-014: o_empty_thr=0 expected at E2 got {s[2].ethr}"
    assert s[3].empty == 1 and s[3].ethr == 1, f"CHK-014: o_empty=1, o_empty_thr=1 expected at E3 got {s[3].empty},{s[3].ethr}"
    for i, k in enumerate((7, 8, 9, 10)):
        assert s[k].empty == 0, f"CHK-014: o_empty=0 expected at E{k} (no bubble) got {s[k].empty}"
        assert s[k].rdat == D[i + 1], f"CHK-014: o_rd_data=D{i + 1} expected at E{k} got {s[k].rdat}"
    assert s[11].empty == 1, f"CHK-014: o_empty=1 expected at E11 got {s[11].empty}"
    for k, x in enumerate(s):
        assert x.full == 0 and x.ovf == 0 and x.unf == 0, \
            f"CHK-014: o_full=0, o_overflow=0, o_underflow=0 expected at E{k} got {x.full},{x.ovf},{x.unf}"
    assert mon.reads == D, "CHK-014: reads D0..D4 in order expected"
    await env.finish()


@cocotb.test()
async def test_chk_015_full_empty_overflow_underflow(dut):
    """CHK-015: fill to full, overflow pulses, drain to empty, underflow pulses, independent next request."""
    env = Env(dut)
    mon = await env.start((10, 10), DEPTH, 0)
    await env.hw_reset(DEPTH, 0, "both")
    if RETIME != 0:
        await _nv(dut, "CHK-015", "directed edge timeline written for PARA_SFIFO_PTR_RETIME=0")
        return
    r = rng("chk015")
    N = DEPTH
    Dw = [r.getrandbits(DW) for _ in range(N + 6)]
    late = 2 * N + 11
    vis = late + LAT + 1

    def wr_fn(k, _s):
        if k <= N + 4:
            return Dw[k]
        if k == late:
            return Dw[N + 5]
        return None

    def rd_fn(k, s):
        if N + 7 <= k <= 2 * N + 9:
            return True
        if k >= late + 1:
            return s.empty == 0
        return False
    s = await eq_run(env, vis + 3, wr_fn, rd_fn)
    for k in range(0, N):
        assert s[k].full == 0, f"CHK-015: o_full=0 expected at E{k} got {s[k].full}"
    for k in range(N, N + 9):
        assert s[k].full == 1, f"CHK-015: o_full=1 expected at E{k} got {s[k].full}"
    assert s[N + 9].full == 0, f"CHK-015: o_full=0 expected at E{N + 9} got {s[N + 9].full}"
    for k in range(0, N + 1):
        assert s[k].ovf == 0, f"CHK-015: o_overflow=0 expected at E{k} got {s[k].ovf}"
    for k in range(N + 1, N + 6):
        assert s[k].ovf == 1, f"CHK-015: o_overflow=1 expected at E{k} got {s[k].ovf}"
    assert s[N + 6].ovf == 0, f"CHK-015: o_overflow=0 expected at E{N + 6} got {s[N + 6].ovf}"
    for i in range(N):
        k = N + 7 + i
        assert s[k].empty == 0 and s[k].rdat == Dw[i], f"CHK-015: read of D{i} expected at E{k} got {s[k].empty},{s[k].rdat}"
    assert s[2 * N + 7].empty == 1, f"CHK-015: o_empty=1 expected at E{2 * N + 7} got {s[2 * N + 7].empty}"
    for k in (2 * N + 8, 2 * N + 9, 2 * N + 10):
        assert s[k].unf == 1, f"CHK-015: o_underflow=1 expected at E{k} got {s[k].unf}"
    assert s[late].unf == 0, f"CHK-015: o_underflow=0 expected at E{late} got {s[late].unf}"
    for k in range(N + 7, 2 * N + 8):
        assert s[k].unf == 0, f"CHK-015: o_underflow=0 expected at E{k} got {s[k].unf}"
    assert s[vis - 1].empty == 1, f"CHK-015: o_empty=1 expected at E{vis - 1} got {s[vis - 1].empty}"
    assert s[vis].empty == 0 and s[vis].rdat == Dw[N + 5], \
        f"CHK-015: o_empty=0 with o_rd_data=D13 expected at E{vis} got {s[vis].empty},{s[vis].rdat}"
    assert mon.reads == Dw[:N] + [Dw[N + 5]], "CHK-015: reads D0..D7 then D13 expected; D8..D12 never read"
    await env.finish()


@cocotb.test()
async def test_chk_016_no_bypass_simultaneous(dut):
    """CHK-016: no full-FIFO bypass; simultaneous accepted write and read."""
    env = Env(dut)
    mon = await env.start((10, 10), DEPTH, 0)
    await env.hw_reset(DEPTH, 0, "both")
    if RETIME != 0 or DEPTH < 5:
        await _nv(dut, "CHK-016", "directed timeline written for PARA_SFIFO_PTR_RETIME=0 and depth >= 5")
        return
    r = rng("chk016")
    N = DEPTH
    Dw = [r.getrandbits(DW) for _ in range(N)]
    X = [r.getrandbits(DW) for _ in range(3)]
    Y = [r.getrandbits(DW) for _ in range(6)]
    wmap = {k: Dw[k] for k in range(N)}
    wmap.update({N + 1: X[0], N + 2: X[1], N + 3: X[2]})
    for i in range(6):
        wmap[2 * N + 4 + i] = Y[i]

    def rd_fn(k, s):
        if k == N + 1 or (N + 4 <= k < 2 * N) or (2 * N + 4 <= k < 2 * N + 10):
            return True
        if k >= 2 * N + 10:
            return s.empty == 0
        return False
    s = await eq_run(env, 3 * N + 18, lambda k, _s: wmap.get(k), rd_fn)
    assert s[N].full == 1, f"CHK-016: o_full=1 expected at E{N} got {s[N].full}"
    assert s[N + 1].empty == 0 and s[N + 1].rdat == Dw[0] and s[N + 1].full == 1, \
        f"CHK-016: read of D0 with o_full=1 expected at E{N + 1} got {s[N + 1]}"
    assert s[N + 2].ovf == 1 and s[N + 2].full == 1, f"CHK-016: X1 rejected (o_overflow=1) and o_full=1 at E{N + 2} got {s[N + 2]}"
    assert s[N + 3].ovf == 1 and s[N + 3].full == 0, f"CHK-016: o_overflow=1 and o_full=0 expected at E{N + 3} got {s[N + 3]}"
    assert s[N + 4].ovf == 0, f"CHK-016: X3 accepted (no o_overflow) expected at E{N + 4} got {s[N + 4].ovf}"
    for k in range(N + 4, 2 * N):
        assert s[k].empty == 0, f"CHK-016: o_empty=0 expected at read edge E{k} got {s[k].empty}"
    for k in range(2 * N + 4, 2 * N + 10):
        assert s[k].full == 0 and s[k].empty == 0, f"CHK-016: o_full=0 and o_empty=0 expected at E{k} got {s[k].full},{s[k].empty}"
        assert s[k + 1].ovf == 0 and s[k + 1].unf == 0, f"CHK-016: no overflow/underflow expected after E{k}"
    assert mon.reads == Dw + [X[2]] + Y, "CHK-016: read order D0..D7, X3, Y0..Y5 expected (X1, X2 never read)"
    await env.finish()


@cocotb.test()
@_ratios(["10_10", "8_12"])
async def test_chk_017_pointer_wrap(dut, ratio):
    """CHK-017: order and flags over many pointer wraps (equal clocks and 3:2)."""
    d = dut
    pw, pr = _parse_ratio(ratio)
    env = Env(dut)
    mon = await env.start((pw, pr), DEPTH, 0)
    await env.hw_reset(DEPTH, 0, "both")
    r = rng(f"chk017_{ratio}")
    written, got = [], []

    async def put(n):
        ws = [r.getrandbits(DW) for _ in range(n)]
        await write_words(env, ws, 10 * n + 100)
        written.extend(ws)

    async def get(n):
        got.extend(await read_words(env, n, 10 * n + 100))

    total = 0
    for _ in range(100):
        if total > 20 * 2 * DEPTH:
            break
        for L in range(1, DEPTH + 1):
            await put(L)
            if L == DEPTH:
                assert val(d.o_full) == 1, f"CHK-017: o_full=1 expected after filling {DEPTH} words got {val(d.o_full)}"
            await get(L)
            assert val(d.o_empty) == 1, f"CHK-017: o_empty=1 expected after draining got {val(d.o_empty)}"
            total += L
    for _ in range(10):
        await put(DEPTH)
        assert val(d.o_full) == 1, f"CHK-017: o_full=1 expected after fill got {val(d.o_full)}"
        await get(DEPTH)
        assert val(d.o_empty) == 1, f"CHK-017: o_empty=1 expected after drain got {val(d.o_empty)}"
    occ = 0
    for _ in range(40):
        tgt = r.randint(0, DEPTH)
        if tgt > occ:
            await put(tgt - occ)
            if tgt == DEPTH:
                assert val(d.o_full) == 1, f"CHK-017: o_full=1 expected at random fill to {DEPTH}"
        elif tgt < occ:
            await get(occ - tgt)
            if tgt == 0:
                assert val(d.o_empty) == 1, "CHK-017: o_empty=1 expected after random drain to 0"
        occ = tgt
    await get(occ)
    assert got == written, "CHK-017: every word read once, in order, across all wraps"
    assert mon.reads == written, "CHK-017: scoreboard read sequence differs from write sequence"
    await env.finish()


@cocotb.test()
async def test_chk_018_gap_free_equal(dut):
    """CHK-018: gap-free streaming with equal clocks."""
    env = Env(dut)
    mon = await env.start((10, 10), DEPTH, 0)
    await env.hw_reset(DEPTH, 0, "both")
    if DEPTH < 4 + 2 * RETIME:
        await _nv(dut, "CHK-018", "depth below 4 + 2 x PARA_SFIFO_PTR_RETIME")
        return
    n = 200
    s = await eq_run(env, n, lambda k, _s: k & MASK, lambda k, _s: True)
    for k in range(n):
        assert s[k].full == 0, f"CHK-018: o_full=0 expected at E{k} got {s[k].full}"
    for k in range(n + 1):
        assert s[k].ovf == 0, f"CHK-018: o_overflow=0 expected at E{k} got {s[k].ovf}"
    for k in range(LAT + 1):
        assert s[k].empty == 1, f"CHK-018: o_empty=1 expected at E{k} got {s[k].empty}"
    for k in range(1, LAT + 2):
        assert s[k].unf == 1, f"CHK-018: o_underflow=1 expected at E{k} got {s[k].unf}"
    for k in range(LAT + 1, n):
        assert s[k].empty == 0, f"CHK-018: o_empty=0 expected at E{k} (no gap) got {s[k].empty}"
        assert s[k].rdat == (k - LAT - 1) & MASK, f"CHK-018: o_rd_data={k - LAT - 1} expected at E{k} got {s[k].rdat}"
    for k in range(LAT + 2, n + 1):
        assert s[k].unf == 0, f"CHK-018: o_underflow=0 expected at E{k} got {s[k].unf}"
    await drain(env, "CHK-018")
    assert mon.reads == [k & MASK for k in range(n)], "CHK-018: incrementing sequence without loss or duplicate"
    await env.finish()


@cocotb.test()
async def test_chk_019_write_faster(dut):
    """CHK-019: continuous traffic, write clock 8 ns faster than read clock 12 ns (WF-010)."""
    d = dut
    env = Env(dut)
    await env.start((8, 12), DEPTH, 0)
    await env.hw_reset(DEPTH, 0, "both")
    if DEPTH < 4 + 2 * RETIME:
        await _nv(dut, "CHK-019", "depth below 4 + 2 x PARA_SFIFO_PTR_RETIME")
        return
    wlog, rlog, words, cnt = [], [], [], [0]
    wstop, rstop = [False], [False]
    wt = cocotb.start_soon(stream_writer(env, wstop, wlog, cnt))
    rt = cocotb.start_soon(stream_reader(env, rstop, rlog, words))
    for _ in range(320):
        await FallingEdge(d.i_clk_rd)
    n_r_stop = len(rlog) - 1
    wstop[0] = True
    await wt
    for _ in range(40 * DEPTH):
        await FallingEdge(d.i_clk_rd)
        if len(words) >= cnt[0]:
            break
    rstop[0] = True
    await rt
    first = next((i for i, e in enumerate(rlog) if e[0] == 0), None)
    assert first is not None, "CHK-019: o_empty=0 expected at some read edge"
    assert n_r_stop - first >= 300, f"CHK-019: at least 300 read cycles of streaming expected got {n_r_stop - first}"
    for i in range(first, n_r_stop):
        assert rlog[i][0] == 0, f"CHK-019: o_empty=0 expected at read edge #{i} (reader never stalls)"
    for i in range(first + 1, n_r_stop):
        assert rlog[i][1] == 0, f"CHK-019: o_underflow=0 expected at read sample #{i}"
    assert any(e[0] == 1 for e in wlog), "CHK-019: o_full=1 expected at some write edges"
    for i in range(1, len(wlog)):
        if wlog[i - 1][2] == 1:
            assert wlog[i][1] == wlog[i - 1][0], f"CHK-019: o_overflow={wlog[i - 1][0]} expected after write edge #{i - 1}"
    assert words == [k & MASK for k in range(cnt[0])], "CHK-019: incrementing read sequence expected"
    await env.finish()


@cocotb.test()
async def test_chk_020_read_faster(dut):
    """CHK-020: continuous traffic, read clock 8 ns faster than write clock 12 ns (WF-011)."""
    d = dut
    env = Env(dut)
    await env.start((12, 8), DEPTH, 0)
    await env.hw_reset(DEPTH, 0, "both")
    if DEPTH < 4 + 2 * RETIME:
        await _nv(dut, "CHK-020", "depth below 4 + 2 x PARA_SFIFO_PTR_RETIME")
        return
    wlog, rlog, words, cnt = [], [], [], [0]
    wstop, rstop = [False], [False]
    wt = cocotb.start_soon(stream_writer(env, wstop, wlog, cnt))
    rt = cocotb.start_soon(stream_reader(env, rstop, rlog, words))
    for _ in range(310):
        await FallingEdge(d.i_clk_wr)
    n_r_stop = len(rlog) - 1
    wstop[0] = True
    await wt
    for _ in range(40 * DEPTH):
        await FallingEdge(d.i_clk_rd)
        if len(words) >= cnt[0]:
            break
    rstop[0] = True
    await rt
    for i, e in enumerate(wlog):
        assert e[0] == 0, f"CHK-020: o_full=0 expected at write edge #{i}"
        assert e[1] == 0, f"CHK-020: o_overflow=0 expected at write sample #{i}"
    assert cnt[0] >= 300, f"CHK-020: at least 300 accepted writes expected got {cnt[0]}"
    first = next((i for i, e in enumerate(rlog) if e[0] == 0), None)
    assert first is not None, "CHK-020: o_empty=0 expected at some read edge"
    empties = [i for i in range(first + 1, n_r_stop) if rlog[i][0] == 1]
    assert empties, "CHK-020: o_empty=1 expected at some read edges (reader faster)"
    for i in empties:
        if rlog[i][2] == 1 and i + 1 < len(rlog):
            assert rlog[i + 1][1] == 1, f"CHK-020: o_underflow=1 expected after read edge #{i} with o_empty=1"
    assert words == [k & MASK for k in range(cnt[0])], "CHK-020: every written word read once, in order"
    await env.finish()


@cocotb.test()
async def test_chk_021_hw_reset(dut):
    """CHK-021: hardware reset values, asynchronous assertion, synchronous release, pulse clearing."""
    d = dut
    C = "CHK-021"
    env = Env(dut)
    mon = await env.start((10, 10), 0, 0)
    r = rng("chk021")

    def chk_idle(s, where, fthr):
        assert s.full == 0, f"{C}: o_full=0 expected {where} got {s.full}"
        assert s.fthr == fthr, f"{C}: o_full_thr={fthr} expected {where} got {s.fthr}"
        assert s.empty == 1 and s.ethr == 1, f"{C}: o_empty=1, o_empty_thr=1 expected {where} got {s.empty},{s.ethr}"
        assert s.ovf == 0 and s.unf == 0 and s.busy == 0, f"{C}: no pulses and busy=0 expected {where} got {s}"

    async def hold_checks(tag):
        await _timer(1)
        check_reset_values(sample(d), C, f"right after the assertion ({tag})")
        for i in range(3):
            await FallingEdge(d.i_clk_wr)
            check_reset_values(sample(d), C, f"at cycle {i + 1} while asserted ({tag})")

    async def release_seq(order, tag, m0=None, idle_cycles=0):
        await FallingEdge(d.i_clk_wr)
        check_reset_values(sample(d), C, f"just before the release ({tag})")
        if order == "both":
            d.i_rst_n_wr.value = 1
            d.i_rst_n_rd.value = 1
        else:
            if order == "wr_first":
                d.i_rst_n_wr.value = 1
            else:
                d.i_rst_n_rd.value = 1
            await _timer(1)
            chk_idle(sample(d), f"right after the first release ({tag})", 0)
            await FallingEdge(d.i_clk_wr)
            chk_idle(sample(d), f"one cycle after the first release ({tag})", 1 if order == "wr_first" else 0)
            if order == "wr_first":
                d.i_rst_n_rd.value = 1
            else:
                d.i_rst_n_wr.value = 1
        wr_now = order != "wr_first"
        if m0 is not None:
            d.i_wr_en.value = 1
            d.i_wr_data.value = m0
        await _timer(1)
        chk_idle(sample(d), f"right after the final release ({tag})", 0 if wr_now else 1)
        if m0 is None:
            for i in range(idle_cycles):
                await FallingEdge(d.i_clk_wr)
                chk_idle(sample(d), f"idle cycle {i + 1} after release ({tag})", 1)
            return
        for k in range(1, LAT + 3):
            await FallingEdge(d.i_clk_wr)
            s = sample(d)
            d.i_wr_en.value = 0
            d.i_rd_en.value = 1 if k == LAT + 1 else 0
            assert s.full == 0 and s.fthr == 1 and s.ovf == 0 and s.unf == 0 and s.busy == 0, \
                f"{C}: o_full=0, o_full_thr=1, no pulses expected at Ek+{k} ({tag}) got {s}"
            if k == LAT + 1:
                assert s.empty == 0 and s.rdat == m0, f"{C}: o_empty=0 with o_rd_data=M0 expected at Ek+{k} ({tag}) got {s.empty},{s.rdat}"
            else:
                assert s.empty == 1, f"{C}: o_empty=1 expected at Ek+{k} ({tag}) got {s.empty}"
        assert mon.reads and mon.reads[-1] == m0, f"{C}: M0 expected to be read ({tag})"

    for _ in range(4):
        await RisingEdge(d.i_clk_wr)
    for i in range(3):
        await FallingEdge(d.i_clk_wr)
        check_reset_values(sample(d), C, f"at power-up cycle {i}")
    await release_seq("wr_first", "power-up", idle_cycles=4)
    m0 = r.getrandbits(DW)
    s = await eq_run(env, LAT + 3, lambda k, _s: m0 if k == 0 else None, lambda k, _s: k == LAT + 1)
    for k in range(1, LAT + 1):
        assert s[k].empty == 1, f"{C}: o_empty=1 expected at Ek+{k} after power-up got {s[k].empty}"
    assert s[LAT + 1].empty == 0 and s[LAT + 1].rdat == m0, f"{C}: M0 visible at Ek+{LAT + 1} expected after power-up"

    Nw = [r.getrandbits(DW) for _ in range(DEPTH + 1)]
    s = await eq_run(env, DEPTH + 1, lambda k, _s: Nw[k], None)
    assert s[DEPTH].full == 1, f"{C}: o_full=1 expected after {DEPTH} writes got {s[DEPTH].full}"
    assert s[DEPTH + 1].ovf == 1, f"{C}: o_overflow=1 expected before the reset got {s[DEPTH + 1].ovf}"
    d.i_rst_n_wr.value = 0
    d.i_rst_n_rd.value = 0
    await hold_checks("mid-traffic with o_overflow=1")
    m0b = r.getrandbits(DW)
    await release_seq("rd_first", "after mid-traffic reset", m0=m0b)

    s = await eq_run(env, 1, None, lambda k, _s: k == 0)
    assert s[0].empty == 1 and s[1].unf == 1, f"{C}: o_underflow=1 expected before the reset got {s[1].unf}"
    d.i_rst_n_wr.value = 0
    d.i_rst_n_rd.value = 0
    await hold_checks("with o_underflow=1")
    m0c = r.getrandbits(DW)
    await release_seq("both", "after reset during underflow", m0=m0c)
    assert mon.reads == [m0, m0b, m0c], f"{C}: only M0 words expected to be read; N0..N7 never"
    await env.finish()


async def _sw_reader(env, st):
    d = env.dut
    for _ in range(10000):
        await FallingEdge(d.i_clk_rd)
        if st["stop"]:
            d.i_rd_en.value = 0
            return
        b, sw = val(d.o_sw_rst_busy), val(d.i_rst_n_sw)
        d.i_rd_en.value = 1 if (b == 1 and sw == 0) else 0


@cocotb.test()
@_ratios(["10_10", "8_12", "12_8"])
async def test_chk_022_sw_reset_sequence(dut, ratio):
    """CHK-022: software reset with low levels of 1, 3, 10 cycles, blocking, busy, data afterwards."""
    d = dut
    C = "CHK-022"
    pw, pr = _parse_ratio(ratio)
    env = Env(dut)
    mon = await env.start((pw, pr), 4, 1)
    await env.hw_reset(4, 1, "both")
    r = rng(f"chk022_{ratio}")
    for N in (1, 3, 10):
        base_reads = len(mon.reads)
        await write_words(env, [r.getrandbits(DW) for _ in range(5)])
        for _ in range(4):
            await FallingEdge(d.i_clk_rd)
        st = {"stop": False}
        rt = cocotb.start_soon(_sw_reader(env, st))
        await FallingEdge(d.i_clk_wr)
        t_start = now_ns()
        d.i_rst_n_sw.value = 0
        d.i_wr_en.value = 1
        d.i_wr_data.value = r.getrandbits(DW)
        await ReadOnly()
        s = sample(d)
        assert s.full == 1, f"{C}: o_full=1 expected right after i_rst_n_sw falls got {s.full} (N={N})"
        assert s.fthr == 0, f"{C}: o_full_thr=0 expected right after i_rst_n_sw falls got {s.fthr} (N={N})"
        for i in range(N):
            await FallingEdge(d.i_clk_wr)
            s = sample(d)
            assert s.busy == 1, f"{C}: o_sw_rst_busy=1 expected after Es+{i + 1} (N={N}) got {s.busy}"
            assert s.full == 1 and s.ovf == 0, f"{C}: o_full=1, o_overflow=0 expected after Es+{i + 1} got {s.full},{s.ovf}"
            if i < N - 1:
                d.i_wr_data.value = r.getrandbits(DW)
            else:
                d.i_rst_n_sw.value = 1
                d.i_wr_en.value = 0
        ok = False
        for _ in range(64):
            await FallingEdge(d.i_clk_wr)
            s = sample(d)
            assert s.ovf == 0, f"{C}: o_overflow=0 expected during the sequence got {s.ovf}"
            if s.busy == 0:
                ok = True
                break
            assert s.full == 1, f"{C}: o_full=1 expected while busy got {s.full}"
        assert ok, f"{C}: o_sw_rst_busy=0 expected within 64 write cycles after i_rst_n_sw returns to 1 (N={N})"
        assert s.full == 0 and s.fthr == 0, f"{C}: o_full=0, o_full_thr=0 expected after the sequence got {s.full},{s.fthr}"
        st["stop"] = True
        await rt
        t_end = now_ns()
        await FallingEdge(d.i_clk_rd)
        s = sample(d)
        assert s.empty == 1 and s.ethr == 1, f"{C}: o_empty=1, o_empty_thr=1 expected after the sequence got {s.empty},{s.ethr}"
        window = [e for e in mon.rd_log if t_start < e.t <= t_end]
        assert any(e.busy == 1 for e in window), f"{C}: o_sw_rst_busy=1 expected at some read edge (N={N})"
        for e in window:
            if e.busy == 1:
                assert e.empty == 1 and e.ethr == 1 and not e.acc, f"{C}: reads blocked expected at {e.t} ns"
                if e.sw == 0:
                    assert e.unf == 0, f"{C}: o_underflow=0 expected after blocked read at {e.t} ns"
        assert mon.reads[base_reads:] == [], f"{C}: D0..D4 and Z must never be read (N={N})"
        Nw = [r.getrandbits(DW) for _ in range(4)]
        if pw == pr:
            sm = await eq_run(env, LAT + 10, lambda k, _s: Nw[k] if k < 4 else None, lambda k, _s: _s.empty == 0)
            for k in range(0, LAT + 1):
                assert sm[k].empty == 1, f"{C}: o_empty=1 expected at Ek+{k} after N0 write got {sm[k].empty}"
            assert sm[LAT + 1].empty == 0 and sm[LAT + 1].rdat == Nw[0], \
                f"{C}: N0 shown at the second read edge strictly after Ek expected got {sm[LAT + 1].empty},{sm[LAT + 1].rdat}"
        else:
            await write_words(env, Nw)
            await read_words(env, 4)
        assert mon.reads[base_reads:] == Nw, f"{C}: N0..N3 read in order expected (N={N})"
    await env.finish()


@cocotb.test()
async def test_chk_023_hw_reset_priority(dut):
    """CHK-023: hardware reset has priority at every step of the software reset sequence."""
    d = dut
    C = "CHK-023"
    env = Env(dut)
    mon = await env.start((10, 10), DEPTH, 0)
    await env.hw_reset(DEPTH, 0, "both")
    r = rng("chk023")
    await write_words(env, [r.getrandbits(DW) for _ in range(3)])
    for _ in range(3):
        await FallingEdge(d.i_clk_wr)
    await FallingEdge(d.i_clk_wr)
    d.i_rst_n_sw.value = 0
    K = 0
    done = False
    for i in range(80):
        await FallingEdge(d.i_clk_wr)
        b = val(d.o_sw_rst_busy)
        if i == 0:
            d.i_rst_n_sw.value = 1
            assert b == 1, f"{C}: o_sw_rst_busy=1 expected after a one-cycle request got {b}"
        if b == 1:
            K += 1
        else:
            done = True
            break
    assert done and K <= 64, f"{C}: software reset sequence expected to end within 64 cycles (K={K})"
    dut._log.info(f"{C}: busy interval K={K}")
    for k in range(K + 1):
        base_reads = len(mon.reads)
        await write_words(env, [r.getrandbits(DW) for _ in range(3)])
        for _ in range(3):
            await FallingEdge(d.i_clk_wr)
        await FallingEdge(d.i_clk_wr)
        d.i_rst_n_sw.value = 0
        await FallingEdge(d.i_clk_wr)
        d.i_rst_n_sw.value = 1
        assert val(d.o_sw_rst_busy) == 1, f"{C}: o_sw_rst_busy=1 expected after the request (k={k})"
        for _ in range(k):
            await FallingEdge(d.i_clk_wr)
        d.i_rst_n_wr.value = 0
        d.i_rst_n_rd.value = 0
        await _timer(1)
        check_reset_values(sample(d), C, f"right at the hardware reset assertion (k={k})")
        for i in range(3):
            await FallingEdge(d.i_clk_wr)
            check_reset_values(sample(d), C, f"while asserted cycle {i} (k={k})")
        await env.release("both")
        for i in range(12):
            await FallingEdge(d.i_clk_wr)
            s = sample(d)
            assert s.busy == 0, f"{C}: o_sw_rst_busy=0 expected after release (k={k}, cycle {i}) got {s.busy}"
            assert s.empty == 1 and s.full == 0, f"{C}: empty FIFO expected after release (k={k}) got {s.empty},{s.full}"
        nw = r.getrandbits(DW)
        await write_words(env, [nw])
        got = await read_words(env, 1, 50)
        assert got == [nw], f"{C}: new word expected to be read back (k={k}) got {got}"
        assert mon.reads[base_reads:] == [nw], f"{C}: old words must never appear (k={k})"
    await env.finish()


@cocotb.test()
async def test_chk_024_sw_reset_full_and_rerequest(dut):
    """CHK-024: software reset while full; new request during the sequence served as a new sequence."""
    d = dut
    C = "CHK-024"
    env = Env(dut)
    mon = await env.start((10, 10), DEPTH, 0)
    await env.hw_reset(DEPTH, 0, "both")
    r = rng("chk024")
    # (a)
    await write_words(env, [r.getrandbits(DW) for _ in range(DEPTH)])
    assert val(d.o_full) == 1, f"{C}: o_full=1 expected after filling got {val(d.o_full)}"
    for _ in range(3):
        await FallingEdge(d.i_clk_wr)
    base_reads = len(mon.reads)
    await FallingEdge(d.i_clk_wr)
    d.i_rst_n_sw.value = 0
    d.i_wr_en.value = 1
    d.i_wr_data.value = r.getrandbits(DW)
    done = False
    for i in range(80):
        await FallingEdge(d.i_clk_wr)
        s = sample(d)
        if i == 0:
            d.i_rst_n_sw.value = 1
            assert s.busy == 1, f"{C}: o_sw_rst_busy=1 expected after the request got {s.busy}"
        assert s.ovf == 0, f"{C}: o_overflow=0 expected during the sequence got {s.ovf}"
        if s.busy == 0:
            d.i_wr_en.value = 0
            assert s.full == 0, f"{C}: o_full=0 expected after o_sw_rst_busy=0 got {s.full}"
            done = True
            break
        assert s.full == 1, f"{C}: o_full=1 expected during the sequence got {s.full}"
        d.i_wr_data.value = r.getrandbits(DW)
    assert done, f"{C}: o_sw_rst_busy=0 expected within 80 cycles"
    await FallingEdge(d.i_clk_rd)
    assert val(d.o_empty) == 1, f"{C}: o_empty=1 expected after the sequence got {val(d.o_empty)}"
    nw = r.getrandbits(DW)
    await write_words(env, [nw])
    got = await read_words(env, 1, 50)
    assert got == [nw] and mon.reads[base_reads:] == [nw], f"{C}: old words never read; new word read back expected"
    # (b)
    for j in range(1, 13):
        base_reads = len(mon.reads)
        pairs = []

        async def fe_drive(sw):
            await FallingEdge(d.i_clk_wr)
            b = val(d.o_sw_rst_busy)
            d.i_rst_n_sw.value = sw
            pairs.append((b, sw))
            return b
        await fe_drive(0)
        await fe_drive(1)
        for _ in range(j - 1):
            await fe_drive(1)
        for _ in range(20):
            await fe_drive(0)
        await fe_drive(1)
        ok = False
        for _ in range(64):
            if await fe_drive(1) == 0:
                ok = True
                break
        assert ok, f"{C}: o_sw_rst_busy=0 expected within 64 write cycles after the final release (j={j})"
        for i in range(len(pairs) - 1):
            if pairs[i] == (0, 0):
                assert pairs[i + 1][0] == 1, f"{C}: new sequence expected (busy=1) after cycle {i} (j={j})"
        await FallingEdge(d.i_clk_rd)
        assert val(d.o_empty) == 1, f"{C}: empty FIFO expected after the sequences (j={j})"
        nw = r.getrandbits(DW)
        await write_words(env, [nw])
        got = await read_words(env, 1, 50)
        assert got == [nw] and mon.reads[base_reads:] == [nw], f"{C}: write and read after the sequences expected to work (j={j})"
    await env.finish()


@cocotb.test()
async def test_chk_025_thresholds(dut):
    """CHK-025: threshold flags (WF-005) and threshold sweep including values above DEPTH."""
    d = dut
    C = "CHK-025"
    env = Env(dut)
    await env.start((10, 10), 6 if DEPTH >= 6 else DEPTH, 2)
    r = rng("chk025")
    if DEPTH == 8 and RETIME == 0:
        await env.hw_reset(6, 2, "both")
        Dw = [r.getrandbits(DW) for _ in range(8)]
        s = await eq_run(env, 20, lambda k, _s: Dw[k] if k < 8 else None, lambda k, _s: 10 <= k <= 17)
        for k in range(1, 6):
            assert s[k].fthr == 0, f"{C}: o_full_thr=0 expected at E{k} got {s[k].fthr}"
        for k in range(6, 14):
            assert s[k].fthr == 1, f"{C}: o_full_thr=1 expected at E{k} got {s[k].fthr}"
        assert s[14].fthr == 0, f"{C}: o_full_thr=0 expected at E14 got {s[14].fthr}"
        for k in range(1, 4):
            assert s[k].ethr == 1, f"{C}: o_empty_thr=1 expected at E{k} got {s[k].ethr}"
        for k in range(4, 16):
            assert s[k].ethr == 0, f"{C}: o_empty_thr=0 expected at E{k} got {s[k].ethr}"
        assert s[16].ethr == 1, f"{C}: o_empty_thr=1 expected at E16 got {s[16].ethr}"
    else:
        await _nv(dut, C, "phase 1 (WF-005) is written for depth 8 and PARA_SFIFO_PTR_RETIME=0")
    vals = sorted(v for v in set(range(0, DEPTH + 2)) | {THR_MAX} if v <= THR_MAX)
    for v in vals:
        await env.hw_reset(v, v, "both")
        if v == 0:
            await _timer(1)
            assert val(d.o_full_thr) == 0, f"{C}: o_full_thr=0 expected before the first edge after release (v=0)"
        words = [r.getrandbits(DW) for _ in range(DEPTH)]
        n = 2 * DEPTH + 8
        s = await eq_run(env, n, lambda k, _s, w=words: w[k] if k < DEPTH else None,
                         lambda k, _s: DEPTH + 2 <= k < 2 * DEPTH + 2)
        if v > DEPTH:
            for k, x in enumerate(s):
                assert x.fthr == 0 and x.ethr == 1, f"{C}: o_full_thr=0, o_empty_thr=1 expected (v={v}) at E{k} got {x.fthr},{x.ethr}"
        if v == 0:
            for k, x in enumerate(s):
                assert x.fthr == 1, f"{C}: o_full_thr=1 expected (v=0) at E{k} got {x.fthr}"
                assert x.ethr == x.empty, f"{C}: o_empty_thr=1 only at read-view occupancy 0 (v=0) at E{k}"
        if RETIME == 0:
            W = set(range(DEPTH))
            R = set(range(DEPTH + 2, 2 * DEPTH + 2))
            for k in range(n):
                occ_w = sum(1 for x in W if x <= k) - sum(1 for x in R if x < k)
                occ_r = sum(1 for x in W if x < k) - sum(1 for x in R if x <= k)
                ef, ee = (1 if occ_w >= v else 0), (1 if occ_r <= v else 0)
                assert s[k + 1].fthr == ef, f"{C}: o_full_thr={ef} expected at E{k + 1} (occ {occ_w}, v={v}) got {s[k + 1].fthr}"
                assert s[k + 1].ethr == ee, f"{C}: o_empty_thr={ee} expected at E{k + 1} (occ {occ_r}, v={v}) got {s[k + 1].ethr}"
    await env.finish()


@cocotb.test()
async def test_regression_random(dut):
    """CHK-001..CHK-011 (assertion checks): broad random traffic with software and hardware resets,
    random thresholds and back pressure, verified by the reference model / scoreboard."""
    d = dut
    env = Env(dut)
    mon = await env.start(None, DEPTH, 0)
    r = rng("regression")
    orders = ["wr_first", "rd_first"]
    if abs(env.pw - env.pr) < 1e-6 or env.integral():
        orders.append("both")
    period = max(env.pw, env.pr)
    for seg in range(8):
        await env.hw_reset(r.randint(0, THR_MAX), r.randint(0, THR_MAX), r.choice(orders))
        await random_traffic(env, r, int(500 * period), sw_prob=0.01)
        if seg % 2 == 1 or seg == 7:
            await drain(env, "CHK-006")
    dut._log.info(f"regression: writes={len(mon.writes)} reads={len(mon.reads)} ovf={mon.n_ovf} "
                  f"unf={mon.n_unf} sw={mon.n_sw} coincident ops={mon.n_coinc_ops}")
    assert len(mon.reads) > 0 and len(mon.writes) > 0, "CHK-006: traffic expected to transfer words"
    assert val(d.o_empty) == 1, "CHK-006: o_empty=1 expected at the end"
    await env.finish()

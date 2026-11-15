"""cocotb 2.1 testbench for m_vlsit_apbcdc_top (APB clock-domain-crossing bridge).

Every expected value is derived from the specification text:
- each requester Setup (S0 = i_clk_mst edge sampling psel=1, penable=0) gives exactly one
  completer transfer whose fields equal the Setup values;
- the completer response sampled at its completion edge C comes back in a one-cycle PREADY;
- crossing windows are [N+1, N+3] destination edges (N from PARA_APBCDC_CELL_TYPE);
- four-phase: requester PREADY no earlier than the (2N+2)-th i_clk_mst edge after C.
Each domain is driven and sampled only at falling edges of its own clock; the requester and
completer models run as separate coroutines and communicate through shared lists.
"""
import bisect
import inspect

import cocotb
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from cocotb.utils import get_sim_time

from nnc_cocotb import *  # noqa: F401,F403

MST, SLV = "i_clk_mst", "i_clk_slv"
BIG = 50_000_000
SLV_F = ("o_apb_pwrite", "o_apb_paddr", "o_apb_pprot", "o_apb_pstrb",
         "o_apb_pwdata", "o_apb_pauser", "o_apb_pwuser")
SLV_O = ("o_apb_psel", "o_apb_penable", "o_apb_pwakeup") + SLV_F
MST_O = ("o_apb_pready", "o_apb_pslverr", "o_apb_prdata", "o_apb_pruser", "o_apb_pbuser")
IN_PORTS = ("i_apb_psel", "i_apb_penable", "i_apb_pwrite", "i_apb_paddr", "i_apb_pprot",
            "i_apb_pstrb", "i_apb_pwdata", "i_apb_pwakeup", "i_apb_pauser", "i_apb_pwuser",
            "i_apb_pready", "i_apb_prdata", "i_apb_pslverr", "i_apb_pruser", "i_apb_pbuser")


def _p(name, dflt):
    try:
        return int(PARAMS.get(name, dflt))
    except Exception:
        return dflt


AW = _p("PARA_APBCDC_ADDR_W", 32)
DW = _p("PARA_APBCDC_DATA_W", 32)
APB5 = _p("PARA_APBCDC_APB5", 0)
UREQ = _p("PARA_APBCDC_USER_REQ_W", 0)
UDAT = _p("PARA_APBCDC_USER_DATA_W", 0)
URSP = _p("PARA_APBCDC_USER_RESP_W", 0)
HS = _p("PARA_APBCDC_HS_TYPE", 0)
CELL = _p("PARA_APBCDC_CELL_TYPE", 2)
SW = max(1, DW // 8)
N = {0: 0, 1: 2, 2: 2, 3: 3, 4: 4}.get(CELL, 2)


def model_nominal():
    """True when the synchronizer model runs at nominal latency (extra latency 0)."""
    return plusarg("APBCDC_MSYNC_EN") == "0"


def run_clocks():
    c = globals().get("CLOCKS")
    if isinstance(c, dict) and MST in c and SLV in c:
        return {MST: float(c[MST]), SLV: float(c[SLV])}
    return {MST: 10.0, SLV: 23.7}


def ratio(s):
    a, b = s.split(":")
    return {MST: float(a), SLV: float(b)}


def now():
    return int(round(get_sim_time(unit="ps")))


def cnt(lst, a, b):
    """Number of edges with a < t <= b."""
    return bisect.bisect_right(lst, b) - bisect.bisect_right(lst, a)


def wid(sig):
    try:
        return len(sig)
    except TypeError:
        return 1


def _param(**kw):
    if hasattr(cocotb, "parametrize"):
        return cocotb.parametrize(**kw)

    def deco(fn):
        async def wrapper(dut):
            return await fn(dut, **{k: v[0] for k, v in kw.items()})
        wrapper.__name__ = fn.__name__
        wrapper.__qualname__ = fn.__qualname__
        wrapper.__doc__ = fn.__doc__
        return wrapper
    return deco


def kill(task):
    if task.done():
        return
    c = getattr(task, "cancel", None)
    if c is not None:
        c()
    else:
        task.kill()


async def cycles(sig, n):
    for _ in range(n):
        await FallingEdge(sig)


async def _rec(sig, lst):
    for _ in range(BIG):
        await RisingEdge(sig)
        lst.append(now())


# --------------------------------------------------------------------------- environment
class Env:
    def __init__(self, dut, per, salt):
        self.dut, self.salt = dut, str(salt)
        self.Tm = int(round(per[MST] * 1000))
        self.Ts = int(round(per[SLV] * 1000))
        self.em, self.es = [], []
        self.reqs, self.cpls = [], []
        self.slog, self.mlog = [], []
        self.errs = []
        self.nsetup = self.npready = 0
        self.quiet = self.zero = self.ackx = False
        self.uw = {k: wid(getattr(dut, "i_apb_" + k)) for k in ("pauser", "pwuser", "pruser", "pbuser")}
        self.req = Requester(self)
        self.cpl = Completer(self)

    def chk(self, cond, msg):
        if not cond:
            self.errs.append(msg)
            raise AssertionError(msg)

    def done(self):
        assert not self.errs, self.errs[0]

    def measure(self):
        if len(self.em) >= 3:
            self.Tm = self.em[-1] - self.em[-2]
        if len(self.es) >= 3:
            self.Ts = self.es[-1] - self.es[-2]

    def limit(self, w):
        k = 2 if HS else 1
        base = k * (6 * N + 30)
        return int((w + base) * max(1.0, self.Ts / self.Tm)) + base

    def ndone(self):
        return sum(1 for q in self.reqs if "tP" in q)

    def flush(self):
        self.reqs, self.cpls = [], []
        self.nsetup = self.npready = 0
        self.ackx = False
        self.req.state = "idle"
        self.req.wake = 0

    def match(self, ph):
        rs, cs = self.req.state, self.cpl.state
        return {"req_setup": rs == "setup",
                "req_cross": rs == "access" and len(self.cpls) < len(self.reqs),
                "cpl_setup": cs == "setup",
                "access": cs == "access",
                "ack_cross": rs == "access" and self.ackx,
                "pready": rs == "pready"}[ph]

    def item(self, r, write=None, idle=None, w=None, err=0, **kw):
        wr = r.randint(0, 1) if write is None else write

        def v(n):
            if n <= 0:
                return 0
            x = r.random()
            if x < 0.1:
                return 0
            if x < 0.2:
                return (1 << n) - 1
            return r.getrandbits(n)
        t = dict(write=wr, addr=v(AW), prot=r.randint(0, 7), strb=v(SW) if wr else 0,
                 wdata=v(DW), auser=v(self.uw["pauser"]), wuser=v(self.uw["pwuser"]),
                 idle=r.randint(0, 5) if idle is None else idle,
                 w=r.randint(0, 3) if w is None else w, err=err,
                 rdata=v(DW), ruser=v(self.uw["pruser"]), buser=v(self.uw["pbuser"]))
        t.update(kw)
        return t


class Requester:
    """Legal APB requester on the i_clk_mst domain (optional rule breaking per item)."""

    def __init__(self, env):
        self.e, self.d = env, env.dut
        self.r = rng("req" + env.salt)
        self.state, self.wake, self.wake_ctl = "idle", 0, bool(APB5)

    def drv(self, t):
        d = self.d
        d.i_apb_pwrite.value = t["write"]
        d.i_apb_paddr.value = t["addr"]
        d.i_apb_pprot.value = t["prot"]
        d.i_apb_pstrb.value = t["strb"]
        d.i_apb_pwdata.value = t["wdata"]
        d.i_apb_pauser.value = t["auser"]
        d.i_apb_pwuser.value = t["wuser"]

    def idle(self):
        self.d.i_apb_psel.value = 0
        self.d.i_apb_penable.value = 0

    def set_wake(self, v):
        if self.wake_ctl:
            self.d.i_apb_pwakeup.value = v
            self.wake = v

    async def fe(self):
        await FallingEdge(self.d.i_clk_mst)

    async def xfer(self, t):
        e, d = self.e, self.d
        mode, idle = t.get("wake", "none"), t.get("idle", 0)
        if mode == "pre" and idle == 0 and self.wake == 0:
            idle = 1
        if mode != "pre":
            self.set_wake(0)
        for i in range(idle):
            self.idle()
            self.state = "idle"
            if mode == "pre" and i == idle - 1:
                self.set_wake(1)
            await self.fe()
        rec = dict(t)
        rec["item"] = t
        e.reqs.append(rec)
        self.drv(t)
        d.i_apb_psel.value = 1
        d.i_apb_penable.value = 0
        e.nsetup += 1
        e.quiet = False
        self.state = "setup"
        await self.fe()
        rec["tS0"] = e.em[-1]
        e.chk(val(d.o_apb_pready) == 0, "CHK-006/031: o_apb_pready=0 at the Setup edge S0, got %s" % val(d.o_apb_pready))
        if t.get("dup"):
            self.drv(t["dup"])
            await self.fe()
            e.chk(val(d.o_apb_pready) == 0, "CHK-024: o_apb_pready=0 in the repeated Setup cycle")
        d.i_apb_penable.value = 1
        self.state = "access"
        if mode == "access":
            self.set_wake(1)
        lim = t.get("lim") or e.limit(t.get("w", 0))
        for _ in range(lim):
            if t.get("mutate"):
                self.drv(e.item(self.r))
            await self.fe()
            pr = val(d.o_apb_pready)
            if pr == 1:
                break
            e.chk(pr == 0, "CHK-031/032: o_apb_pready=0 while the transfer is pending, got %s" % pr)
            e.chk(val(d.o_apb_pslverr) == 0, "CHK-032/033: o_apb_pslverr=0 while waiting, got %s" % val(d.o_apb_pslverr))
        else:
            e.chk(False, "CHK-032: no o_apb_pready within %d i_clk_mst cycles (transfer %d)" % (lim, len(e.reqs) - 1))
        rec["tP"] = e.em[-1]
        rec["r_rdata"], rec["r_err"] = val(d.o_apb_prdata), val(d.o_apb_pslverr)
        rec["r_ruser"], rec["r_buser"] = val(d.o_apb_pruser), val(d.o_apb_pbuser)
        self.state = "pready"
        e.ackx = False
        await self.fe()
        rec["tEnd"] = e.em[-1]
        e.chk(val(d.o_apb_pready) == 0 and val(d.o_apb_pslverr) == 0,
              "CHK-004/031: o_apb_pready and o_apb_pslverr 0 at the edge after the PREADY cycle, got %s/%s"
              % (val(d.o_apb_pready), val(d.o_apb_pslverr)))
        self.state = "idle"

    async def run(self, items):
        await self.fe()
        for t in items:
            await self.xfer(t)
        self.idle()
        self.set_wake(0)
        await self.fe()


class Completer:
    """APB completer on the i_clk_slv domain; also checks the completer-side protocol."""

    def __init__(self, env):
        self.e, self.d = env, env.dut
        self.r = rng("cpl" + env.salt)
        self.noise, self.wait_wake = True, False
        self.reset_state()

    def reset_state(self):
        self.state, self.cur, self.left, self.drv_rdy, self.t_drv = "idle", None, 0, 0, 0
        self.prev = (0, 0, (0,) * len(SLV_F))

    def set_resp(self, rd, er, ru, bu):
        d = self.d
        d.i_apb_prdata.value = rd
        d.i_apb_pslverr.value = er
        d.i_apb_pruser.value = ru
        d.i_apb_pbuser.value = bu

    def noise_resp(self, rq):
        r, uw = self.r, self.e.uw
        if self.noise:
            self.set_resp(r.getrandbits(DW), r.randint(0, 1), r.getrandbits(uw["pruser"]), r.getrandbits(uw["pbuser"]))
        else:
            self.set_resp(0, 1 if (rq and rq.get("werr")) else 0, 0, 0)

    def close(self):
        """NNC hand fix (G3, triage B): called when the resets are asserted. If i_apb_pready=1 was driven in an
        Access phase and a rising i_clk_slv edge has passed since, that edge is the completion edge C (sampled
        with both resets high); record it, because the run loop would only record it at the next falling edge."""
        e, c = self.e, self.cur
        if c is not None and self.drv_rdy and self.prev[0] == 1 and self.prev[1] == 1 and e.es and e.es[-1] > self.t_drv:
            c["tC"] = e.es[-1]

    async def run(self):
        e, d = self.e, self.d
        for _ in range(BIG):
            await FallingEdge(d.i_clk_slv)
            if not e.es:
                continue
            t = e.es[-1]
            rs, rm = val(d.i_rst_n_slv), val(d.i_rst_n_mst)
            ps, pe, wk = val(d.o_apb_psel), val(d.o_apb_penable), val(d.o_apb_pwakeup)
            f = tuple(val(getattr(d, n)) for n in SLV_F)
            allo = (ps, pe, wk) + f
            e.slog.append((t, ps, pe, wk))
            if e.quiet:
                e.chk(ps == 0, "CHK-027/028: o_apb_psel=0 until the requester's next Setup, got %s" % ps)
            if rs == 0:
                e.chk(all(x == 0 for x in allo), "CHK-010: completer-side outputs 0 while i_rst_n_slv=0, got %s" % (allo,))
            if rs != 1 or rm != 1:
                self.reset_state()
                d.i_apb_pready.value = 0
                continue
            e.chk(None not in allo, "CHK-011: X/Z on a completer-side output %s" % (allo,))
            if e.zero:
                e.chk(all(x == 0 for x in allo), "CHK-027: completer-side outputs unchanged (0) while idle, got %s" % (allo,))
            if not APB5:
                e.chk(wk == 0 and f[5] == 0 and f[6] == 0, "CHK-001/021: APB4 o_apb_pwakeup/pauser/pwuser 0, got %s/%s/%s" % (wk, f[5], f[6]))
            else:
                if UREQ == 0:
                    e.chk(f[5] == 0, "CHK-001: o_apb_pauser=0 with USER_REQ_W=0, got %s" % f[5])
                if UDAT == 0:
                    e.chk(f[6] == 0, "CHK-001: o_apb_pwuser=0 with USER_DATA_W=0, got %s" % f[6])
                if ps == 1:
                    e.chk(wk == 1, "CHK-018/020: o_apb_pwakeup=1 at every edge with o_apb_psel=1, got %s" % wk)
            pps, ppe, pf = self.prev
            e.chk(not (pe == 1 and ps != 1), "CHK-012: o_apb_penable=1 implies o_apb_psel=1")
            if pps == 0 and ps == 1:
                e.chk(pe == 0, "CHK-012: o_apb_penable=0 at the edge that raises o_apb_psel")
            if pps == 1 and ppe == 0:
                e.chk(ps == 1 and pe == 1, "CHK-013: Setup lasts one cycle, got psel=%s penable=%s" % (ps, pe))
            if pps == 1 and ppe == 1:
                if self.drv_rdy:
                    e.chk(ps == 0 and pe == 0, "CHK-015/031: psel=0, penable=0 at C+1, got %s/%s" % (ps, pe))
                else:
                    e.chk(ps == 1 and pe == 1, "CHK-014: Access held while i_apb_pready=0, got %s/%s" % (ps, pe))
            if pps == 1 and not (ppe == 1 and self.drv_rdy):
                e.chk(f == pf, "CHK-016/024: completer-side fields stable during the transfer, %s -> %s" % (pf, f))
            if f != pf:
                e.chk(ps == 1 and pe == 0 and pps == 0, "CHK-017: fields change only at Setup entry")
            if pps == 1 and ppe == 1 and self.drv_rdy and self.cur is not None:
                c = self.cur
                c["tC"] = t
                if not c["ww"]:
                    e.chk(c["nacc"] == c["w"] + 1, "CHK-032: Access lasted %d edges, expected w+1=%d" % (c["nacc"], c["w"] + 1))
                self.state, self.cur = "ackx", None
                e.ackx = True
            rdy = 0
            if ps == 1 and pe == 0:
                e.chk(pps == 0, "CHK-034: o_apb_psel low for at least one edge between transfers")
                n = len(e.cpls)
                e.chk(n < len(e.reqs), "CHK-029: o_apb_psel rise without an outstanding requester Setup (transfer %d)" % n)
                rq = e.reqs[n]
                self.cur = dict(tPsel=t, f=f, nacc=0, w=rq.get("w", 0), rq=rq, ww=bool(rq.get("ww") or self.wait_wake))
                e.cpls.append(self.cur)
                self.left, self.state = self.cur["w"], "setup"
                rdy = self.r.randint(0, 1) if self.noise else 0
                self.noise_resp(rq)
            elif ps == 1 and pe == 1 and self.cur is not None:
                c = self.cur
                self.state = "access"
                c["nacc"] += 1
                rq = c["rq"]
                if c["ww"] and wk != 1:
                    self.noise_resp(rq)
                elif self.left <= 0:
                    rdy = 1
                    c["resp"] = (rq["rdata"], rq["err"], rq["ruser"], rq["buser"])
                    self.set_resp(*c["resp"])
                else:
                    self.left -= 1
                    self.noise_resp(rq)
            else:
                if self.state != "ackx":
                    self.state = "idle"
                rdy = self.r.randint(0, 1) if self.noise else 0
                self.noise_resp(None)
            d.i_apb_pready.value = rdy
            self.drv_rdy = rdy
            self.t_drv = now()  # NNC hand fix (G3, triage B): when drv_rdy was driven, see Completer.close
            self.prev = (ps, pe, f)


async def mst_monitor(e):
    d, prev = e.dut, None
    for _ in range(BIG):
        await FallingEdge(d.i_clk_mst)
        if not e.em:
            continue
        rm, rs = val(d.i_rst_n_mst), val(d.i_rst_n_slv)
        o = tuple(val(getattr(d, n)) for n in MST_O)
        if e.quiet:
            e.chk(o[0] == 0, "CHK-027/028: o_apb_pready=0 until the requester's next Setup, got %s" % o[0])
        if rm == 0:
            e.chk(all(x == 0 for x in o), "CHK-009: requester-side outputs 0 while i_rst_n_mst=0, got %s" % (o,))
        if rm != 1 or rs != 1:
            prev = (0, 0, 0, 0, 0)
            continue
        e.chk(None not in o, "CHK-008: X/Z on a requester-side output %s" % (o,))
        if e.zero:
            e.chk(all(x == 0 for x in o), "CHK-027: requester-side outputs unchanged (0) while idle, got %s" % (o,))
        pr, er, rd, ru, bu = o
        e.mlog.append((e.em[-1], pr))
        e.chk(er == 0 or pr == 1, "CHK-005/033: o_apb_pslverr=1 only with o_apb_pready=1")
        if prev is not None:
            if prev[0] == 1:
                e.chk(pr == 0 and er == 0, "CHK-004: PREADY is a one-cycle pulse")
            if pr == 0:
                e.chk((rd, ru, bu) == tuple(prev[2:]), "CHK-007: response outputs stable outside PREADY, %s -> %s" % (prev[2:], (rd, ru, bu)))
        if not APB5:
            e.chk(ru == 0 and bu == 0, "CHK-001/021: APB4 o_apb_pruser/pbuser 0, got %s/%s" % (ru, bu))
        else:
            if UDAT == 0:
                e.chk(ru == 0, "CHK-001: o_apb_pruser=0 with USER_DATA_W=0")
            if URSP == 0:
                e.chk(bu == 0, "CHK-001: o_apb_pbuser=0 with USER_RESP_W=0")
        if pr == 1:
            e.npready += 1
            e.chk(e.npready <= e.nsetup, "CHK-006: %d PREADY pulses for %d Setup phases" % (e.npready, e.nsetup))
        prev = o


def idle_inputs(dut):
    for n in IN_PORTS:
        getattr(dut, n).value = 0


async def bring_up(dut, periods=None, salt="", reset=True):
    r = start_clock(dut, periods=periods) if periods else start_clock(dut)
    if inspect.isawaitable(r):
        await r
    e = Env(dut, periods or run_clocks(), salt)
    idle_inputs(dut)
    cocotb.start_soon(_rec(dut.i_clk_mst, e.em))
    cocotb.start_soon(_rec(dut.i_clk_slv, e.es))
    if reset:
        await reset_dut(dut, cycles=5)
        await cycles(dut.i_clk_slv, 2)
        await FallingEdge(dut.i_clk_mst)
        e.measure()
    else:
        dut.i_rst_n_mst.value = 0
        dut.i_rst_n_slv.value = 0
        e.quiet = True
    cocotb.start_soon(mst_monitor(e))
    cocotb.start_soon(e.cpl.run())
    return e


async def settle(e):
    await cycles(e.dut.i_clk_slv, 4)
    await FallingEdge(e.dut.i_clk_mst)


def far(e, t, margin=200):
    for lst, T in ((e.em, e.Tm), (e.es, e.Ts)):
        if lst:
            h = T / 2.0
            x = (t - lst[-1]) % h
            if min(x, h - x) < margin:
                return False
    return True


async def mid_time(e, r, poll=None, abort=None, limit=200000):
    """Return at a time that is not aligned to an edge of either clock (optionally when poll())."""
    fast = e.dut.i_clk_mst if e.Tm <= e.Ts else e.dut.i_clk_slv
    hi = max(4, int(min(e.Tm, e.Ts) / 2 // 100) - 3)
    for _ in range(limit):
        await FallingEdge(fast)
        if abort is not None and abort():
            break
        off = r.randint(3, hi) * 100
        if not far(e, now() + off):
            continue
        await Timer(off, unit="ps")
        if poll is None or poll():
            return True
    for _ in range(1000):
        await FallingEdge(fast)
        off = r.randint(3, hi) * 100
        if far(e, now() + off):
            await Timer(off, unit="ps")
            return False
    return False


async def assert_resets(e, chk):
    d = e.dut
    e.cpl.close()  # NNC hand fix (G3, triage B)
    d.i_rst_n_mst.value = 0
    d.i_rst_n_slv.value = 0
    e.quiet = True
    await Timer(100, unit="ps")
    m = [val(getattr(d, n)) for n in MST_O]
    s = [val(getattr(d, n)) for n in SLV_O]
    e.chk(all(x == 0 for x in m), "%s/CHK-009: requester-side outputs 0 right after asynchronous reset assertion, got %s" % (chk, m))
    e.chk(all(x == 0 for x in s), "%s/CHK-010: completer-side outputs 0 right after asynchronous reset assertion, got %s" % (chk, s))


async def release(e, mst_first=True, gap=3):
    d = e.dut
    if mst_first:
        await FallingEdge(d.i_clk_mst)
        d.i_rst_n_mst.value = 1
        await cycles(d.i_clk_slv, gap)
        d.i_rst_n_slv.value = 1
    else:
        await FallingEdge(d.i_clk_slv)
        d.i_rst_n_slv.value = 1
        await cycles(d.i_clk_slv, gap)
        await FallingEdge(d.i_clk_mst)
        d.i_rst_n_mst.value = 1


def score(e, partial=False, kwin=True, jwin=True):
    """Reference model: completer transfer n carries Setup n; PREADY n returns the response at C."""
    reqs = [q for q in e.reqs if "tP" in q] if partial else e.reqs
    if partial:
        e.chk(len(reqs) <= len(e.cpls) <= len(e.reqs), "CHK-028: %d completer transfers for %d Setups (%d complete)" % (len(e.cpls), len(e.reqs), len(reqs)))
    else:
        e.chk(len(e.cpls) == len(reqs), "CHK-029/031: completer transfers %d != requester transfers %d" % (len(e.cpls), len(reqs)))
    for n, q in enumerate(reqs):
        c = e.cpls[n]
        wr = q["write"]
        exp = (wr, q["addr"], q["prot"], q["strb"], q["wdata"] if wr else None,
               q["auser"] if (APB5 and UREQ) else 0,
               (q["wuser"] if wr else None) if (APB5 and UDAT) else 0)
        for i, (x, y) in enumerate(zip(exp, c["f"])):
            if x is not None:
                e.chk(x == y, "CHK-029/031: transfer %d %s expected %#x got %s" % (n, SLV_F[i], x, y))
        e.chk("resp" in c and "tC" in c, "CHK-031: transfer %d has no completion edge C" % n)
        rd, er, ru, bu = c["resp"]
        e.chk(q["r_err"] == er, "CHK-033: transfer %d o_apb_pslverr expected %d got %s" % (n, er, q["r_err"]))
        if not wr:
            e.chk(q["r_rdata"] == rd, "CHK-031/033: transfer %d o_apb_prdata expected %#x got %s" % (n, rd, q["r_rdata"]))
            if APB5 and UDAT:
                e.chk(q["r_ruser"] == ru, "CHK-019: transfer %d o_apb_pruser expected %#x got %s" % (n, ru, q["r_ruser"]))
        if APB5 and URSP:
            e.chk(q["r_buser"] == bu, "CHK-019: transfer %d o_apb_pbuser expected %#x got %s" % (n, bu, q["r_buser"]))
        e.chk(q["tS0"] < c["tPsel"] < c["tC"] < q["tP"], "CHK-029: transfer %d order S0 < psel < C < PREADY violated" % n)
        if n > 0:
            e.chk(c["tPsel"] > reqs[n - 1]["tP"], "CHK-029/034: psel rise of transfer %d before PREADY of transfer %d" % (n, n - 1))
        k = cnt(e.es, q["tS0"], c["tPsel"])
        if kwin:
            e.chk(N + 1 <= k <= N + 3, "CHK-031/023/030: o_apb_psel rose at slv edge k=%d after S0, expected [%d,%d] (transfer %d)" % (k, N + 1, N + 3, n))
        j = cnt(e.em, c["tC"], q["tP"])
        if jwin:
            if HS == 0:
                e.chk(N + 1 <= j <= N + 3, "CHK-031/032/030: o_apb_pready rose at mst edge j=%d after C, expected [%d,%d] (transfer %d)" % (j, N + 1, N + 3, n))
            else:
                e.chk(j >= 2 * N + 2, "CHK-023: four-phase o_apb_pready at mst edge j=%d after C, expected >= %d (transfer %d)" % (j, 2 * N + 2, n))
    return reqs


async def run_score(e, items, **kw):
    await e.req.run(items)
    await settle(e)
    return score(e, **kw)


def hs_j_note(dut, chk):
    if HS:
        not_verifiable(dut, chk, "the j window [N+1,N+3] after C is the two-phase window; this run has HS_TYPE=1 (checked j >= 2N+2 instead)")


# --------------------------------------------------------------------------- tests
@cocotb.test()
async def test_chk_031_single_write_read(dut):
    """CHK-031: single writes/reads without wait states, fields, response and crossing windows."""
    e = await bring_up(dut, salt="031")
    r = rng("chk031")
    e.cpl.noise = False
    items = [e.item(r, write=1, idle=r.randint(2, 5), w=0) for _ in range(50)]
    items += [e.item(r, write=0, idle=r.randint(2, 5), w=0) for _ in range(50)]
    r.shuffle(items)
    ones = lambda n: (1 << n) - 1
    items[0].update(write=1, addr=0, wdata=0, strb=0, prot=0)
    items[1].update(write=1, addr=ones(AW), wdata=ones(DW), strb=ones(SW), prot=7)
    items[2].update(write=0, addr=ones(AW), rdata=ones(DW), strb=0)
    items[3].update(write=0, addr=0, rdata=0, strb=0)
    reqs = await run_score(e, items)
    e.chk(len(reqs) == 100 and len(e.cpls) == 100, "CHK-031: expected 100 transfers on each side, got %d/%d" % (len(reqs), len(e.cpls)))
    for c in e.cpls:
        e.chk(c["nacc"] == 1, "CHK-031: one Access cycle without wait states, got %d" % c["nacc"])
    for q in reqs:
        e.chk(q["r_err"] == 0, "CHK-031: o_apb_pslverr=0, got %s" % q["r_err"])
    e.done()
    hs_j_note(dut, "CHK-031")


@cocotb.test()
async def test_chk_032_wait_states(dut):
    """CHK-032: completer wait states extend the transfer without limit (one w=10000)."""
    e = await bring_up(dut, salt="032")
    r = rng("chk032")
    ws = [0, 1, 2, 5, 17] * 6 + [r.randint(0, 30) for _ in range(29)] + [10000]
    r.shuffle(ws)
    items = [e.item(r, w=w, idle=r.randint(0, 3), err=r.randint(0, 1)) for w in ws]
    await run_score(e, items)
    e.chk(len(e.cpls) == 60, "CHK-032: 60 transfers expected, got %d" % len(e.cpls))
    e.done()
    hs_j_note(dut, "CHK-032")


@cocotb.test()
async def test_chk_033_error_response(dut):
    """CHK-033: PSLVERR forwarded with read data, error during wait ignored, next transfer independent."""
    e = await bring_up(dut, salt="033")
    r = rng("chk033")
    e.cpl.noise = False
    items, prev = [], 0
    for _ in range(100):
        err = 0 if prev else int(r.random() < 0.5)
        it = e.item(r, w=r.randint(0, 5), err=err, idle=r.randint(0, 3))
        if err and it["rdata"] == 0:
            it["rdata"] = 1
        if not err and it["w"] > 0 and r.random() < 0.5:
            it["werr"] = True
        items.append(it)
        prev = err
    reqs = await run_score(e, items)
    for q in reqs:
        e.chk(q["r_err"] == q["err"], "CHK-033: o_apb_pslverr expected %d got %s" % (q["err"], q["r_err"]))
    e.done()


@cocotb.test()
@_param(clocks=["run", "swap"])
async def test_chk_034_back_to_back(dut, clocks):
    """CHK-034: back-to-back Setup accepted in the cycle after PREADY, one transfer at a time."""
    rc = run_clocks()
    per = None if clocks == "run" else {MST: rc[SLV], SLV: rc[MST]}
    e = await bring_up(dut, periods=per, salt="034" + clocks)
    r = rng("chk034" + clocks)
    idles = [0] * 150 + [r.randint(1, 5) for _ in range(50)]
    r.shuffle(idles)
    items = [e.item(r, idle=i, w=r.randint(0, 3), err=r.randint(0, 1)) for i in idles]
    reqs = await run_score(e, items)
    e.chk(len(reqs) == 200 and len(e.cpls) == 200, "CHK-034: 200 transfers each side, got %d/%d" % (len(reqs), len(e.cpls)))
    for n in range(1, 200):
        if items[n]["idle"] == 0:
            a = bisect.bisect_left(e.em, reqs[n]["tS0"])
            b = bisect.bisect_left(e.em, reqs[n - 1]["tEnd"])
            e.chk(a == b + 1, "CHK-034: back-to-back Setup %d not at the edge after the PREADY cycle" % n)
    e.done()


@cocotb.test()
async def test_chk_035_pprot_pstrb(dut):
    """CHK-035: PPROT and PSTRB forwarded unchanged, PSTRB of a read forwarded."""
    e = await bring_up(dut, salt="035")
    r = rng("chk035")
    items = [e.item(r, write=1, prot=p, strb=s, wdata=r.getrandbits(DW), idle=r.randint(0, 2), err=r.randint(0, 1))
             for p in range(8) for s in range(1 << SW)]
    items += [e.item(r, write=0, prot=p, strb=0, idle=r.randint(0, 2), err=r.randint(0, 1)) for p in range(8)]
    items += [e.item(r, write=0, strb=r.randint(1, (1 << SW) - 1), idle=r.randint(0, 2), err=r.randint(0, 1)) for _ in range(16)]
    r.shuffle(items)
    await run_score(e, items)
    e.done()


@cocotb.test()
async def test_chk_022_cfg_min(dut):
    """CHK-022: smallest configuration (ADDR_W=1, DATA_W=8) end to end, bit for bit."""
    e = await bring_up(dut, salt="022")
    r = rng("chk022")
    is_min = AW == 1 and DW == 8
    n = 500 if is_min else 100
    items = []
    for i in range(n):
        wr = i % 2
        it = e.item(r, write=wr, prot=i % 8, w=r.randint(0, 4), err=r.randint(0, 1), idle=r.randint(0, 3))
        it["addr"] = (i // 2) % 2 if AW == 1 else r.getrandbits(AW)
        it["wdata"] = [0, (1 << DW) - 1, r.getrandbits(DW)][i % 3]
        it["rdata"] = [(1 << DW) - 1, r.getrandbits(DW), 0][i % 3]
        if wr:
            it["strb"] = (i // 2) % (1 << SW)
        items.append(it)
    await run_score(e, items)
    e.done()
    if not is_min:
        not_verifiable(dut, "CHK-022", "needs PARA_APBCDC_ADDR_W=1 and DATA_W=8; this run has %d/%d (traffic scored with these widths)" % (AW, DW))


@cocotb.test()
async def test_chk_019_apb5_user(dut):
    """CHK-019: PAUSER/PWUSER with the request, PRUSER/PBUSER with the response."""
    e = await bring_up(dut, periods={MST: 10, SLV: 20}, salt="019")
    if not APB5:
        not_verifiable(dut, "CHK-019", "needs PARA_APBCDC_APB5=1; this run is APB4")
        e.done()
        return
    r = rng("chk019")
    items = []
    for i in range(300):
        it = e.item(r, w=r.randint(0, 4), err=r.randint(0, 1), idle=r.randint(0, 3), wake="pre")
        if i % 10 in (0, 1):
            for k in ("auser", "wuser", "ruser", "buser"):
                it[k] = 0 if i % 10 else (1 << e.uw["p" + k]) - 1
        items.append(it)
    await run_score(e, items)
    e.done()
    miss = [n for n, w in (("PAUSER", UREQ), ("PWUSER/PRUSER", UDAT), ("PBUSER", URSP)) if w == 0]
    if miss:
        not_verifiable(dut, "CHK-019", "width parameter 0 for %s in this run; those outputs only checked to be 0" % miss)


@cocotb.test()
async def test_chk_020_apb5_wakeup(dut):
    """CHK-020: o_apb_pwakeup = synchronized i_apb_pwakeup OR transfer in progress."""
    e = await bring_up(dut, periods={MST: 10, SLV: 20}, salt="020")
    if not APB5:
        not_verifiable(dut, "CHK-020", "needs PARA_APBCDC_APB5=1; this run is APB4")
        e.done()
        return
    d, r = dut, rng("chk020")
    # (a) idle wake-up pulse
    await FallingEdge(d.i_clk_mst)
    e.req.set_wake(1)
    await FallingEdge(d.i_clk_mst)
    w1 = e.em[-1]
    await cycles(d.i_clk_mst, 19)
    e.req.set_wake(0)
    await FallingEdge(d.i_clk_mst)
    w0 = e.em[-1]
    await cycles(d.i_clk_slv, N + 8)
    before = [x for x in e.slog if x[0] <= w1]
    e.chk(before and before[-1][3] == 0, "CHK-020: o_apb_pwakeup=0 before W1")
    tr = next((x[0] for x in e.slog if x[0] > w1 and x[3] == 1), None)
    tf = next((x[0] for x in e.slog if x[0] > w0 and x[3] == 0), None)
    e.chk(tr is not None and tf is not None, "CHK-020: o_apb_pwakeup did not rise and fall")
    k1, k0 = cnt(e.es, w1, tr), cnt(e.es, w0, tf)
    e.chk(N + 1 <= k1 <= N + 3, "CHK-020: o_apb_pwakeup rose at slv edge %d after W1, expected [%d,%d]" % (k1, N + 1, N + 3))
    e.chk(N + 1 <= k0 <= N + 3, "CHK-020: o_apb_pwakeup fell at slv edge %d after W0, expected [%d,%d]" % (k0, N + 1, N + 3))
    for x in e.slog:
        if x[0] > w1:
            e.chk(x[1] == 0, "CHK-020: o_apb_psel=0 during idle wake-up")
            if tr <= x[0] < tf:
                e.chk(x[3] == 1, "CHK-020: o_apb_pwakeup glitch-free between rise and fall")
    # (b) wake one cycle before psel
    await e.req.run([e.item(r, wake="pre", idle=r.randint(1, 4), w=r.randint(0, 4), err=r.randint(0, 1)) for _ in range(50)])
    # (c) wake never driven
    c0 = len(e.reqs)
    idle_c = int((N + 6) * e.Ts / e.Tm) + 2
    await e.req.run([e.item(r, wake="none", idle=idle_c, w=r.randint(0, 4)) for _ in range(50)])
    c1 = len(e.reqs)
    # (d) wake asserted during Access, (e) completer waits for wake-up
    await e.req.run([e.item(r, wake="access", idle=r.randint(1, 4), w=r.randint(0, 4)) for _ in range(20)])
    await e.req.run([e.item(r, wake=r.choice(["none", "pre", "access"]), ww=True, idle=r.randint(1, 4), w=r.randint(0, 3)) for _ in range(20)])
    await settle(e)
    score(e)
    end = now() + 1
    for n in range(c0, c1):
        tc = e.cpls[n]["tC"]
        nxt = e.reqs[n + 1]["tS0"] if n + 1 < len(e.reqs) else end
        after = [x for x in e.slog if tc < x[0] < nxt]
        tz = next((x[0] for x in after if x[3] == 0), None)
        e.chk(tz is not None and cnt(e.es, tc, tz) <= N + 3, "CHK-020: (c) o_apb_pwakeup not 0 within N+3 slv edges after C (transfer %d)" % n)
        e.chk(all(x[3] == 0 for x in after if x[0] >= tz), "CHK-020: (c) o_apb_pwakeup must stay 0 while idle (transfer %d)" % n)
    e.done()


@cocotb.test()
async def test_chk_021_apb4_ignores_apb5(dut):
    """CHK-021: with APB5=0 the APB5 inputs have no effect and the APB5 outputs are 0."""
    e = await bring_up(dut, salt="021")
    if APB5:
        not_verifiable(dut, "CHK-021", "needs PARA_APBCDC_APB5=0; this run is APB5")
        e.done()
        return
    d, r = dut, rng("chk021")
    e.req.wake_ctl = False
    stop = [False]

    async def toggler():
        for _ in range(BIG):
            await FallingEdge(d.i_clk_mst)
            if stop[0]:
                return
            d.i_apb_pwakeup.value = r.randint(0, 1)
    cocotb.start_soon(toggler())
    await run_score(e, [e.item(r, w=r.randint(0, 4), err=r.randint(0, 1)) for _ in range(200)])
    stop[0] = True
    await FallingEdge(d.i_clk_mst)
    sm = [val(getattr(d, n)) for n in MST_O]
    ss = [val(getattr(d, n)) for n in SLV_O]
    d.i_apb_pwakeup.value = 1
    st = [False]

    async def slv_watch():
        for _ in range(BIG):
            await FallingEdge(d.i_clk_slv)
            if st[0]:
                return
            e.chk([val(getattr(d, n)) for n in SLV_O] == ss, "CHK-021: completer-side output changed with i_apb_pwakeup=1 while idle")
    cocotb.start_soon(slv_watch())
    for _ in range(50):
        await FallingEdge(d.i_clk_mst)
        e.chk([val(getattr(d, n)) for n in MST_O] == sm, "CHK-021: requester-side output changed with i_apb_pwakeup=1 while idle")
    st[0] = True
    d.i_apb_pwakeup.value = 0
    await settle(e)
    e.done()


@cocotb.test()
@_param(clocks=["10:20", "20:10"])
async def test_chk_023_four_phase(dut, clocks):
    """CHK-023: four-phase handshake, same function, PREADY only after the handshake closes."""
    e = await bring_up(dut, periods=ratio(clocks), salt="023" + clocks)
    if HS != 1:
        not_verifiable(dut, "CHK-023", "needs PARA_APBCDC_HS_TYPE=1; this run has HS_TYPE=%d" % HS)
        e.done()
        return
    r = rng("chk023" + clocks)
    idles = [0] * 100 + [r.randint(1, 5) for _ in range(100)]
    r.shuffle(idles)
    reqs = await run_score(e, [e.item(r, idle=i, w=r.randint(0, 5), err=r.randint(0, 1)) for i in idles])
    e.chk(len(reqs) == 200 and len(e.cpls) == 200, "CHK-023: 200 transfers each side")
    e.done()


@cocotb.test()
async def test_chk_024_requester_violations(dut):
    """CHK-024: PENABLE without Setup ignored, Setup values used despite later field changes."""
    e = await bring_up(dut, salt="024")
    d, r = dut, rng("chk024")
    await FallingEdge(d.i_clk_mst)
    t0 = now()
    e.req.drv(e.item(r))
    d.i_apb_psel.value = 1
    d.i_apb_penable.value = 1
    await cycles(d.i_clk_mst, 20)
    d.i_apb_psel.value = 0
    d.i_apb_penable.value = 0
    t1 = now()
    await cycles(d.i_clk_slv, N + 14)
    e.chk(all(x[1] == 0 for x in e.slog if x[0] >= t0), "CHK-024: (a) o_apb_psel must stay 0 for PENABLE without Setup")
    e.chk(cnt(e.es, t1, now()) >= N + 13, "CHK-024: (a) observation window too short")
    e.chk(all(p == 0 for (t, p) in e.mlog if t >= t0), "CHK-024: (a) o_apb_pready must stay 0")
    e.chk(len(e.cpls) == 0, "CHK-024: (a) no completer transfer expected")
    items = [e.item(r, mutate=True, w=r.randint(0, 4), err=r.randint(0, 1)) for _ in range(50)]
    items += [e.item(r, dup=e.item(r), w=r.randint(0, 4), err=r.randint(0, 1)) for _ in range(10)]
    items += [e.item(r, w=r.randint(0, 4), err=r.randint(0, 1)) for _ in range(50)]
    await run_score(e, items)
    e.chk(len(e.cpls) == 110, "CHK-024: exactly one completer transfer per Setup, got %d" % len(e.cpls))
    e.done()
    if not (APB5 and UREQ and UDAT):
        not_verifiable(dut, "CHK-024", "PAUSER/PWUSER changes during Access need APB5 with user widths > 0; not present in this run")


async def perf(dut, clocks, chk, want):
    e = await bring_up(dut, periods=ratio(clocks), salt=chk + clocks)
    if HS != want:
        not_verifiable(dut, chk, "needs PARA_APBCDC_HS_TYPE=%d; this run has %d" % (want, HS))
        e.done()
        return
    r = rng(chk + clocks)
    reqs = await run_score(e, [e.item(r, idle=r.randint(1, 5), w=r.randint(0, 8), err=r.randint(0, 1)) for _ in range(200)])
    tm = max(e.Tm, int(round(ratio(clocks)[MST] * 1000)))
    ts = max(e.Ts, int(round(ratio(clocks)[SLV] * 1000)))
    a = N + 3 if HS == 0 else 2 * N + 4
    nom = model_nominal()
    extra = 0 if nom else (2 if HS == 0 else 4) * (tm + ts)
    for n, q in enumerate(reqs):
        start = e.em[bisect.bisect_left(e.em, q["tS0"]) - 1]
        dur = q["tEnd"] - start
        bound = a * tm + (a + q["w"]) * ts + extra
        e.chk(dur <= bound + 2, "%s: transfer %d D=%d ps exceeds bound %d ps (w=%d, %s)" % (chk, n, dur, bound, q["w"], clocks))
    e.done()
    if not nom:
        not_verifiable(dut, chk, "the bound assumes extra synchronizer latency 0 (+APBCDC_MSYNC_EN=0); this run has it enabled, so it was checked with 2 extra destination cycles per crossing")


@cocotb.test()
@_param(clocks=["10:10", "10:20", "20:10", "10:90", "90:10"])
async def test_chk_025_two_phase_duration(dut, clocks):
    """CHK-025: two-phase D <= (N+3) T_mst + (N+3+w) T_slv."""
    await perf(dut, clocks, "CHK-025", 0)


@cocotb.test()
@_param(clocks=["10:10", "10:20", "20:10", "10:90", "90:10"])
async def test_chk_026_four_phase_duration(dut, clocks):
    """CHK-026: four-phase D <= (2N+4) T_mst + (2N+4+w) T_slv."""
    await perf(dut, clocks, "CHK-026", 1)


@cocotb.test()
async def test_chk_027_reset_values(dut):
    """CHK-027: reset values, quiet idle after release, asynchronous reset assertion."""
    e = await bring_up(dut, periods={MST: 10, SLV: 20}, salt="027", reset=False)
    d, r = dut, rng("chk027")
    await cycles(d.i_clk_mst, 12)
    await cycles(d.i_clk_slv, 12)
    e.measure()
    await release(e, True, 3)
    for rep in range(2):
        e.zero = True
        await cycles(d.i_clk_slv, 100)
        e.zero = False
        rd = e.item(r, write=0, idle=2, w=r.randint(0, 2), addr=r.randint(1, (1 << AW) - 1), rdata=r.randint(1, (1 << DW) - 1))
        wr = e.item(r, write=1, idle=2, w=r.randint(0, 2), addr=r.randint(1, (1 << AW) - 1),
                    wdata=r.randint(1, (1 << DW) - 1), rdata=r.randint(1, (1 << DW) - 1))
        await run_score(e, [rd, wr])
        e.flush()
        if rep == 0:
            pre = [val(getattr(d, n)) for n in ("o_apb_prdata", "o_apb_paddr", "o_apb_pwdata", "o_apb_pwrite")]
            e.chk(all(x not in (0, None) for x in pre), "CHK-027: prdata/paddr/pwdata/pwrite nonzero before reset, got %s" % pre)
            await mid_time(e, r)
            await assert_resets(e, "CHK-027")
            await cycles(d.i_clk_slv, 5)
            await release(e, True, 3)
    e.done()


@cocotb.test()
async def test_chk_028_reset_during_traffic(dut):
    """CHK-028: reset during random traffic, lost transfer repeated, staggered release."""
    e = await bring_up(dut, salt="028")
    d, r = dut, rng("chk028")
    slow = d.i_clk_mst if e.Tm >= e.Ts else d.i_clk_slv
    phases = ("req_setup", "req_cross", "cpl_setup", "access", "ack_cross", "pready")
    lost = None
    for it in range(30):
        items = ([lost] if lost else []) + [e.item(r, w=r.randint(0, 6), idle=r.randint(0, 3), err=r.randint(0, 1)) for _ in range(12)]
        task = cocotb.start_soon(e.req.run(items))
        ph, base = phases[it % len(phases)], e.ndone() + r.randint(0, 2)
        await mid_time(e, r, poll=lambda: e.ndone() >= base and e.match(ph), abort=task.done)
        await assert_resets(e, "CHK-028")
        kill(task)
        lost = None
        if e.req.state != "idle" and e.reqs:
            lost = dict(e.reqs[-1]["item"])
            lost["idle"] = 1
        e.req.idle()
        e.req.set_wake(0)
        score(e, partial=True)
        e.flush()
        await cycles(slow, r.randint(3, 10))
        await release(e, mst_first=(it % 2 == 0), gap=r.randint(1, 10))
        await cycles(d.i_clk_slv, 2 * N + 8)
        await cycles(d.i_clk_mst, 2 * N + 8)
    items = ([lost] if lost else []) + [e.item(r, w=r.randint(0, 6), err=r.randint(0, 1)) for _ in range(20)]
    await run_score(e, items)
    e.done()


@cocotb.test()
async def test_chk_029_scoreboard_ratios(dut):
    """CHK-029: random traffic scoreboard with a noisy completer at a randomly chosen clock ratio."""
    choices = ["10:10", "10:20", "20:10", "10:30", "30:10", "10:90", "90:10", "10:14", "14:10", "13.7:10"]
    clocks = rng("chk029_ratio").choice(choices)
    e = await bring_up(dut, periods=ratio(clocks), salt="029")
    r = rng("chk029")
    modes = ["pre", "none", "access"]
    items = [e.item(r, w=r.randint(0, 10), err=r.randint(0, 1), wake=r.choice(modes)) for _ in range(2000)]
    reqs = await run_score(e, items)
    e.chk(len(reqs) == 2000, "CHK-029: 2000 transfers expected, got %d" % len(reqs))
    e.done()


@cocotb.test()
async def test_chk_030_sync_depth(dut):
    """CHK-030: synchronizer depth visible in the crossing latency (k, j in [N+1, N+3])."""
    e = await bring_up(dut, periods={MST: 10, SLV: 20}, salt="030")
    r = rng("chk030")
    await run_score(e, [e.item(r, w=r.randint(0, 3), err=r.randint(0, 1)) for _ in range(100)])
    e.done()
    if CELL != 4:
        not_verifiable(dut, "CHK-030", "needs PARA_APBCDC_CELL_TYPE=4 (N=4); this run has CELL_TYPE=%d (windows checked with N=%d)" % (CELL, N))
    hs_j_note(dut, "CHK-030")


@cocotb.test()
async def test_regression_random(dut):
    """CHK-001..CHK-018, CHK-029: broad legal random traffic with back pressure and noise."""
    e = await bring_up(dut, salt="reg")
    r = rng("regression")
    items = []
    for _ in range(800):
        it = e.item(r, idle=0 if r.random() < 0.3 else r.randint(1, 5), w=r.randint(0, 10),
                    err=r.randint(0, 1), wake=r.choice(["pre", "none", "access"]))
        if it["w"] and r.random() < 0.2:
            it["werr"] = True
        items.append(it)
    reqs = await run_score(e, items)
    e.chk(len(reqs) == 800 and e.npready == 800, "CHK-006/029: 800 PREADY pulses expected, got %d" % e.npready)
    e.done()

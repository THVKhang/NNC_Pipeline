"""cocotb 2.1 testbench for m_vlsit_apbcdc_top (APB bridge between two asynchronous clocks).

Timing model: one agent coroutine per clock domain. At each rising edge it records the edge time
(integer ps); at the following falling edge it samples the outputs of its domain (values after
that rising edge), runs the per-edge checks, and drives its inputs for the next rising edge.
Cross-domain windows (k, j) are counted in destination rising edges strictly after the source
edge time, from the recorded edge-time lists.
"""

import bisect
import collections
import math

import cocotb
from cocotb.triggers import FallingEdge, First, ReadOnly, RisingEdge, Timer

from nnc_cocotb import *  # noqa: F401,F403

try:
    from cocotb.simtime import get_sim_time as _sim_time
except ImportError:  # pragma: no cover
    from cocotb.utils import get_sim_time as _sim_time

MCLK = "i_clk_mst"
SCLK = "i_clk_slv"
MRST = "i_rst_n_mst"
SRST = "i_rst_n_slv"

M_IN = ["psel", "penable", "pwrite", "paddr", "pprot", "pstrb", "pwdata", "pwakeup", "pauser", "pwuser"]
M_OUT = ["pready", "pslverr", "prdata", "pruser", "pbuser"]
S_OUT = ["psel", "penable", "pwrite", "paddr", "pprot", "pstrb", "pwdata", "pwakeup", "pauser", "pwuser"]
S_IN = ["pready", "prdata", "pslverr", "pruser", "pbuser"]
FIELDS = ["pwrite", "paddr", "pprot", "pstrb", "pwdata", "pauser", "pwuser"]

FIELD_TAG = {"penable": "CHK-012/031", "pwrite": "CHK-029/031", "paddr": "CHK-029/031/022",
             "pprot": "CHK-035/031", "pstrb": "CHK-035/031/022", "pwdata": "CHK-029/031/022",
             "pauser": "CHK-019/001", "pwuser": "CHK-019/001", "pwakeup": "CHK-018/020"}
RESP_TAG = {"pready": "CHK-031", "pslverr": "CHK-033/031", "prdata": "CHK-031/033/022",
            "pruser": "CHK-019/001", "pbuser": "CHK-019/001"}


# ----------------------------------------------------------------------------- utilities
def now_ps():
    try:
        return int(_sim_time(unit="ps"))
    except TypeError:
        return int(_sim_time(units="ps"))


def ps_timer(d):
    d = max(1, int(d))
    try:
        return Timer(d, unit="ps")
    except TypeError:
        return Timer(d, units="ps")


def mask(w):
    return (1 << w) - 1 if w > 0 else 0


def _h(x):
    return "X/Z" if x is None else hex(x)


def _width(h):
    try:
        n = len(h)
        if n > 0:
            return n
    except Exception:
        pass
    try:
        return max(1, len(h.value))
    except Exception:
        return 1


def _default_periods():
    try:
        c = dict(CLOCKS)
    except Exception:
        c = {}
    return float(c.get(MCLK, 10)), float(c.get(SCLK, 20))


def start_clocks(dut, periods=None):
    if periods is None:
        start_clock(dut)
        tm, ts = _default_periods()
    else:
        tm, ts = periods
        start_clock(dut, periods={MCLK: tm, SCLK: ts})
    return int(round(tm * 1000)), int(round(ts * 1000))


def val_pick(r, w, p_ext=0.15):
    if w <= 0:
        return 0
    x = r.random()
    if x < p_ext:
        return 0
    if x < 2 * p_ext:
        return mask(w)
    return r.getrandbits(w)


class Cfg:
    def __init__(self):
        try:
            p = dict(PARAMS)
        except Exception:
            p = {}

        def g(k, d):
            try:
                return int(p.get(k, d))
            except (TypeError, ValueError):
                return d
        self.addr_w = g("PARA_APBCDC_ADDR_W", 32)
        self.data_w = g("PARA_APBCDC_DATA_W", 32)
        self.apb5 = g("PARA_APBCDC_APB5", 0)
        self.ureq_w = g("PARA_APBCDC_USER_REQ_W", 0)
        self.udata_w = g("PARA_APBCDC_USER_DATA_W", 0)
        self.uresp_w = g("PARA_APBCDC_USER_RESP_W", 0)
        self.hs = g("PARA_APBCDC_HS_TYPE", 0)
        self.cell = g("PARA_APBCDC_CELL_TYPE", 2)
        self.strb_w = max(1, self.data_w // 8)
        self.N = {0: 0, 1: 2, 2: 2, 3: 3, 4: 4}.get(self.cell, 2)


class Xfer:
    """One requester transfer, filled in by both agents."""

    def __init__(self, item):
        self.f = {k: int(item[k]) for k in FIELDS}
        self.write = self.f["pwrite"] & 1
        self.item = item
        self.s0_t = None
        self.s0_idx = None
        self.psel_idx = None
        self.k = None
        self.c_t = None
        self.c_idx = None
        self.resp = None
        self.w = None
        self.acc_edges = 0
        self.pr_t = None
        self.pr_idx = None
        self.j = None


def rand_item(b, r, write=None, idle=None, wake="auto", ill=None, rep=0):
    c = b.cfg
    wr = r.randint(0, 1) if write is None else int(write)
    if wake == "auto":
        wake = r.choice(["before", "none"]) if c.apb5 else "none"
    return dict(pwrite=wr, paddr=val_pick(r, c.addr_w), pprot=r.randint(0, 7),
                pstrb=val_pick(r, c.strb_w) if wr else 0, pwdata=val_pick(r, c.data_w),
                pauser=val_pick(r, b.wmi["pauser"]), pwuser=val_pick(r, b.wmi["pwuser"]),
                idle=r.randint(0, 5) if idle is None else int(idle), wake=wake, ill=ill, rep=rep)


def make_policy(b, r, wmin=0, wmax=0, err_p=0.0, wseq=None):
    seq = collections.deque(wseq) if wseq else None

    def pol(rec):
        w = seq.popleft() if seq else r.randint(wmin, wmax)
        return dict(w=w, prdata=val_pick(r, b.wsi["prdata"]), pslverr=1 if r.random() < err_p else 0,
                    pruser=val_pick(r, b.wsi["pruser"]), pbuser=val_pick(r, b.wsi["pbuser"]),
                    err_in_wait=False)
    return pol


# ----------------------------------------------------------------------------- bench
class Bench:
    def __init__(self, dut, per, r):
        self.dut = dut
        self.cfg = Cfg()
        self.Tm, self.Ts = per
        self.r = r
        self.mclk = getattr(dut, MCLK)
        self.sclk = getattr(dut, SCLK)
        self.rst_m_h = getattr(dut, MRST)
        self.rst_s_h = getattr(dut, SRST)
        self.mi = {k: getattr(dut, "i_apb_" + k) for k in M_IN}
        self.mo = {k: getattr(dut, "o_apb_" + k) for k in M_OUT}
        self.so = {k: getattr(dut, "o_apb_" + k) for k in S_OUT}
        self.si = {k: getattr(dut, "i_apb_" + k) for k in S_IN}
        self.wmi = {k: _width(h) for k, h in self.mi.items()}
        self.wsi = {k: _width(h) for k, h in self.si.items()}
        self.recs = []
        self.slv_count = 0
        self.epoch = 0
        self.rst_m = False
        self.rst_s = False
        self.m_edges = []
        self.s_edges = []
        self.fail = None
        self.quiet = False
        self.retry_lost = False
        self.wake_random = False
        self.pushed = 0
        self.mst = Requester(self)
        self.slv = Completer(self)

    def any_rst(self):
        return self.rst_m or self.rst_s

    def chk(self):
        if self.fail is not None:
            raise self.fail

    @staticmethod
    def sample(d):
        return {k: val(h) for k, h in d.items()}

    async def _guard(self, coro):
        try:
            await coro
        except AssertionError as e:
            if self.fail is None:
                self.fail = e
            raise

    def start(self):
        cocotb.start_soon(self._guard(self.mst.run()))
        cocotb.start_soon(self._guard(self.slv.run()))

    def push(self, items):
        for it in items:
            self.mst.ops.append(("xfer", it))
            self.pushed += 1

    def push_op(self, op):
        self.mst.ops.append(op)

    def exp_fields(self, rec):
        c, f = self.cfg, rec.f
        e = {"penable": 0, "pwrite": f["pwrite"] & 1, "paddr": f["paddr"] & mask(c.addr_w),
             "pprot": f["pprot"] & 7, "pstrb": f["pstrb"] & mask(c.strb_w)}
        if rec.write:
            e["pwdata"] = f["pwdata"] & mask(c.data_w)
        e["pauser"] = f["pauser"] & mask(c.ureq_w) if (c.apb5 and c.ureq_w > 0) else 0
        if c.apb5 and c.udata_w > 0:
            if rec.write:
                e["pwuser"] = f["pwuser"] & mask(c.udata_w)
        else:
            e["pwuser"] = 0
        if c.apb5:
            e["pwakeup"] = 1
        return e

    def exp_resp(self, rec):
        c, rs = self.cfg, rec.resp
        e = {"pready": 1, "pslverr": rs["pslverr"] & 1}
        if not rec.write:
            e["prdata"] = rs["prdata"] & mask(c.data_w)
        if c.apb5 and c.udata_w > 0:
            if not rec.write:
                e["pruser"] = rs["pruser"] & mask(c.udata_w)
        else:
            e["pruser"] = 0
        e["pbuser"] = rs["pbuser"] & mask(c.uresp_w) if (c.apb5 and c.uresp_w > 0) else 0
        return e

    def hold_reset(self):
        """Assert both resets now (used at time 0)."""
        self.epoch += 1
        self.rst_m = self.rst_s = True
        self.rst_m_h.value = 0
        self.rst_s_h.value = 0
        self.recs = []
        self.slv_count = 0

    async def assert_resets(self, tag):
        """Assert both resets in the current time step and check the asynchronous effect."""
        self.hold_reset()
        await ReadOnly()
        mo = self.sample(self.mo)
        so = self.sample(self.so)
        for k, v in mo.items():
            assert v == 0, f"CHK-009/{tag}: o_apb_{k}=0 in the time step of the asynchronous i_rst_n_mst assertion, got {_h(v)}"
        for k, v in so.items():
            assert v == 0, f"CHK-010/{tag}: o_apb_{k}=0 in the time step of the asynchronous i_rst_n_slv assertion, got {_h(v)}"

    async def release(self, order="mst_first", gap=3):
        if order == "mst_first":
            await FallingEdge(self.mclk)
            self.rst_m_h.value = 1
            self.rst_m = False
            for _ in range(max(1, int(gap))):
                await FallingEdge(self.sclk)
            self.rst_s_h.value = 1
            self.rst_s = False
        else:
            await FallingEdge(self.sclk)
            self.rst_s_h.value = 1
            self.rst_s = False
            for _ in range(int(gap)):
                await FallingEdge(self.sclk)
            await FallingEdge(self.mclk)
            self.rst_m_h.value = 1
            self.rst_m = False


# ----------------------------------------------------------------------------- requester (mst)
class Requester:
    def __init__(self, b):
        self.b = b
        self.ops = collections.deque()
        self.cur = {k: 0 for k in M_IN}
        self.state = "IDLE"
        self.op = None
        self.item = None
        self.rec = None
        self.idle_left = 0
        self.rep_left = 0
        self.s0_pending = False
        self.retry = None
        self.prev = None
        self.epoch = 0
        self.done = 0
        self.wk_sampled = 0
        self.wk_log = []

    def busy(self):
        return (bool(self.ops) or self.op is not None or self.item is not None
                or self.retry is not None or self.state != "IDLE")

    def drive(self):
        b = self.b
        if b.wake_random:
            self.cur["pwakeup"] = b.r.randint(0, 1)
        for k, h in b.mi.items():
            h.value = int(self.cur[k]) & mask(b.wmi[k])

    async def run(self):
        b = self.b
        self.prev = b.sample(b.mo)
        while True:
            await RisingEdge(b.mclk)
            t = now_ps()
            b.m_edges.append(t)
            idx = len(b.m_edges) - 1
            if self.cur["pwakeup"] != self.wk_sampled:
                self.wk_sampled = self.cur["pwakeup"]
                self.wk_log.append((t, idx, self.wk_sampled))
            if self.s0_pending and self.rec is not None and not b.any_rst() and self.epoch == b.epoch:
                self.rec.s0_t = t
                self.rec.s0_idx = idx
            self.s0_pending = False
            await FallingEdge(b.mclk)
            out = b.sample(b.mo)
            self.step(out, idx)
            self.drive()
            self.prev = out

    def _scramble(self):
        b, r, c = self.b, self.b.r, self.b.cfg
        self.cur.update(pwrite=r.randint(0, 1), paddr=r.getrandbits(c.addr_w), pprot=r.randint(0, 7),
                        pstrb=r.getrandbits(c.strb_w), pwdata=r.getrandbits(c.data_w),
                        pauser=r.getrandbits(b.wmi["pauser"]), pwuser=r.getrandbits(b.wmi["pwuser"]))

    def _lose(self):
        if self.item is not None and self.b.retry_lost:
            self.retry = self.item
        self.item = None
        self.rec = None
        self.state = "IDLE"
        self.s0_pending = False
        self.rep_left = 0
        self.cur.update(psel=0, penable=0, pwakeup=0)

    def _peek(self):
        if self.retry is not None:
            return ("xfer", self.retry)
        if self.op is not None:
            return self.op
        return self.ops[0] if self.ops else None

    def _fetch(self):
        if self.retry is not None:
            it = dict(self.retry)
            it["idle"] = 0
            self.retry = None
            self.op = ["xfer", it]
            self.idle_left = 0
            return True
        while self.ops:
            o = self.ops.popleft()
            if o[0] == "call":
                o[1]()
                continue
            self.op = list(o)
            self.idle_left = int(o[1]["idle"]) if o[0] == "xfer" else int(o[1])
            return True
        return False

    def _start(self, it):
        rec = Xfer(it)
        self.b.recs.append(rec)
        self.rec = rec
        self.item = it
        self.op = None
        for k in FIELDS:
            self.cur[k] = int(it[k])
        self.cur["psel"] = 1
        self.cur["penable"] = 0
        if it["wake"] != "before":
            self.cur["pwakeup"] = 0
        self.s0_pending = True
        self.rep_left = int(it.get("rep", 0))
        self.state = "SETUP"

    def _idle_step(self):
        self.cur["psel"] = 0
        self.cur["penable"] = 0
        for _ in range(256):
            if self.op is None and not self._fetch():
                self.cur["pwakeup"] = 0
                return
            kind = self.op[0]
            if kind in ("idle", "raw"):
                if self.idle_left <= 0:
                    self.op = None
                    continue
                self.idle_left -= 1
                if kind == "idle":
                    self.cur["pwakeup"] = int(self.op[2])
                else:
                    self.cur.update(self.op[2])
                return
            it = self.op[1]
            if self.idle_left > 0:
                self.idle_left -= 1
                self.cur["pwakeup"] = 1 if (self.idle_left == 0 and it["wake"] == "before") else 0
                return
            if it["wake"] == "before" and self.cur["pwakeup"] == 0:
                self.cur["pwakeup"] = 1
                return
            self._start(it)
            return

    def _complete(self, out, idx):
        b, c, rec = self.b, self.b.cfg, self.rec
        assert rec is not None and rec.c_t is not None, \
            "CHK-031/029: o_apb_pready rises only after the completer-side completion edge C, got PREADY with no C"
        j = idx - bisect.bisect_right(b.m_edges, rec.c_t) + 1
        rec.j = j
        rec.pr_idx = idx
        rec.pr_t = b.m_edges[idx]
        if c.hs == 0:
            assert c.N + 1 <= j <= c.N + 3, \
                f"CHK-031/032: o_apb_pready rises at the j-th i_clk_mst edge after C with j in [{c.N+1},{c.N+3}], got j={j}"
        else:
            assert j >= 2 * c.N + 2, \
                f"CHK-023: four-phase o_apb_pready no earlier than the {2*c.N+2}-th i_clk_mst edge after C, got j={j}"
        for k, v in b.exp_resp(rec).items():
            assert out[k] == v, \
                f"{RESP_TAG[k]}: o_apb_{k} in the PREADY cycle equals the completer value at C {_h(v)}, got {_h(out[k])}"

    def step(self, out, idx):
        b, c, p = self.b, self.b.cfg, self.prev
        if b.rst_m:
            for k in M_OUT:
                assert out[k] == 0, f"CHK-009: o_apb_{k}=0 while i_rst_n_mst=0, got {_h(out[k])}"
        if b.any_rst() or self.epoch != b.epoch:
            assert out["pready"] == 0, f"CHK-028: o_apb_pready=0 while a reset is asserted, got {_h(out['pready'])}"
            self._lose()
            if not b.any_rst():
                self.epoch = b.epoch
            return
        for k in M_OUT:
            assert out[k] is not None, f"CHK-008: o_apb_{k} has no X/Z bit after reset release, got X/Z"
        if b.quiet:
            for k in M_OUT:
                assert out[k] == p[k], f"CHK-027/021: o_apb_{k} does not change while idle, got {_h(p[k])} -> {_h(out[k])}"
        if not (c.apb5 and c.udata_w > 0):
            assert out["pruser"] == 0, f"CHK-001/021: o_apb_pruser=0 when absent, got {_h(out['pruser'])}"
        if not (c.apb5 and c.uresp_w > 0):
            assert out["pbuser"] == 0, f"CHK-001/021: o_apb_pbuser=0 when absent, got {_h(out['pbuser'])}"
        assert out["pslverr"] == 0 or out["pready"] == 1, \
            "CHK-005/033: o_apb_pslverr=1 only with o_apb_pready=1, got pslverr=1 with pready=0"
        if p["pready"] == 1:
            assert out["pready"] == 0 and out["pslverr"] == 0, \
                f"CHK-004/031: o_apb_pready is a one-cycle pulse, got pready={_h(out['pready'])} pslverr={_h(out['pslverr'])} next cycle"
        if out["pready"] == 0:
            for k in ("prdata", "pruser", "pbuser"):
                assert out[k] == p[k], f"CHK-007: o_apb_{k} stable outside the PREADY cycle, got {_h(p[k])} -> {_h(out[k])}"

        if self.state == "ACCESS":
            if out["pready"] == 1:
                self._complete(out, idx)
                self.state = "RESP"
                return
            if self.item.get("ill") == "chg":
                self._scramble()
            return
        if self.state == "SETUP":
            assert out["pready"] == 0, "CHK-006: o_apb_pready=0 at the edge after a Setup cycle, got 1"
            if self.rep_left > 0:
                self.rep_left -= 1
                self._scramble()
                return
            self.cur["penable"] = 1
            self.state = "ACCESS"
            if self.item.get("ill") == "chg":
                self._scramble()
            if self.item["wake"] == "during":
                self.cur["pwakeup"] = 1
            return
        if self.state == "RESP":
            assert out["pready"] == 0 and out["pslverr"] == 0, "CHK-004: o_apb_pready/pslverr 0 after the PREADY cycle"
            self.done += 1
            self.item = None
            self.rec = None
            self.state = "IDLE"
            nxt = self._peek()
            keep = nxt is not None and nxt[0] == "xfer" and int(nxt[1]["idle"]) == 0 and nxt[1]["wake"] == "before"
            if not keep:
                self.cur["pwakeup"] = 0
        assert out["pready"] == 0, \
            "CHK-006/028/029: o_apb_pready=1 only in the Access phase of an accepted Setup, got 1 while the requester is idle"
        self._idle_step()


# ----------------------------------------------------------------------------- completer (slv)
class Completer:
    def __init__(self, b):
        self.b = b
        self.cur = {k: 0 for k in S_IN}
        self.rec = None
        self.plan = None
        self.acc = 0
        self.prev = None
        self.epoch = 0
        self.noisy = False
        self.policy = None
        self.wait_wakeup = False
        self.c_pending = False
        self.wk_events = []
        self.phase = "IDLE"

    def drive(self):
        for k, h in self.b.si.items():
            h.value = int(self.cur[k]) & mask(self.b.wsi[k])

    async def run(self):
        b = self.b
        self.prev = b.sample(b.so)
        while True:
            await RisingEdge(b.sclk)
            t = now_ps()
            b.s_edges.append(t)
            idx = len(b.s_edges) - 1
            p = self.prev
            if (not b.any_rst() and self.epoch == b.epoch and self.rec is not None
                    and p["psel"] == 1 and p["penable"] == 1 and self.cur["pready"] == 1):
                self.rec.c_t = t
                self.rec.c_idx = idx
                self.rec.resp = {k: int(self.cur[k]) & mask(b.wsi[k]) for k in S_IN}
                self.c_pending = True
            await FallingEdge(b.sclk)
            out = b.sample(b.so)
            self.step(out, idx)
            self.drive()
            self.prev = out

    def _noise(self, err):
        r, w = self.b.r, self.b.wsi
        self.cur["prdata"] = r.getrandbits(w["prdata"])
        self.cur["pruser"] = r.getrandbits(w["pruser"])
        self.cur["pbuser"] = r.getrandbits(w["pbuser"])
        self.cur["pslverr"] = r.randint(0, 1) if err else 0

    def _idle_drive(self):
        if self.noisy:
            self.cur["pready"] = self.b.r.randint(0, 1)
            self._noise(True)
        else:
            self.cur["pready"] = 0
            self.cur["pslverr"] = 0

    def _default_plan(self):
        r, w = self.b.r, self.b.wsi
        return dict(w=0, prdata=r.getrandbits(w["prdata"]), pslverr=0, pruser=r.getrandbits(w["pruser"]),
                    pbuser=r.getrandbits(w["pbuser"]), err_in_wait=False)

    def _new(self, out, idx):
        b, c = self.b, self.b.cfg
        t = b.s_edges[idx]
        i = b.slv_count
        assert i < len(b.recs), \
            "CHK-029/024/028: o_apb_psel rises only with an outstanding requester Setup phase, got a rise with none"
        rec = b.recs[i]
        assert rec.s0_t is not None and rec.s0_t < t, \
            "CHK-029: o_apb_psel rise comes after the Setup edge S0 of its transfer, got a rise before S0"
        if i > 0:
            pv = b.recs[i - 1]
            ok = pv.pr_idx is not None and pv.pr_idx + 1 < len(b.m_edges) and b.m_edges[pv.pr_idx + 1] < t
            assert ok, "CHK-029/034: o_apb_psel rise of transfer n+1 after the o_apb_pready cycle of transfer n, got it earlier"
        k = idx - bisect.bisect_right(b.s_edges, rec.s0_t) + 1
        assert c.N + 1 <= k <= c.N + 3, \
            f"CHK-031/034/023/030: o_apb_psel rises at the k-th i_clk_slv edge after S0 with k in [{c.N+1},{c.N+3}], got k={k}"
        for f, v in b.exp_fields(rec).items():
            assert out[f] == v, f"{FIELD_TAG[f]}: o_apb_{f} at the o_apb_psel rise equals the Setup value {_h(v)}, got {_h(out[f])}"
        b.slv_count += 1
        rec.k = k
        rec.psel_idx = idx
        self.rec = rec
        self.acc = 0
        self.plan = self.policy(rec) if self.policy else self._default_plan()

    def step(self, out, idx):
        b, c, p = self.b, self.b.cfg, self.prev
        sampled_ready = self.cur["pready"]
        if b.rst_s:
            for k in S_OUT:
                assert out[k] == 0, f"CHK-010: o_apb_{k}=0 while i_rst_n_slv=0, got {_h(out[k])}"
        if b.any_rst() or self.epoch != b.epoch:
            assert out["psel"] == 0, f"CHK-028: o_apb_psel=0 while a reset is asserted, got {_h(out['psel'])}"
            self.rec = None
            self.plan = None
            self.c_pending = False
            self.acc = 0
            self.phase = "IDLE"
            if not b.any_rst():
                self.epoch = b.epoch
            self._idle_drive()
            return
        for k in S_OUT:
            assert out[k] is not None, f"CHK-011: o_apb_{k} has no X/Z bit after reset release, got X/Z"
        if b.quiet:
            for k in S_OUT:
                assert out[k] == p[k], f"CHK-027/021: o_apb_{k} does not change while idle, got {_h(p[k])} -> {_h(out[k])}"
        if not c.apb5:
            for k in ("pwakeup", "pauser", "pwuser"):
                assert out[k] == 0, f"CHK-001/021: o_apb_{k}=0 in APB4, got {_h(out[k])}"
        else:
            if c.ureq_w == 0:
                assert out["pauser"] == 0, f"CHK-001: o_apb_pauser=0 when USER_REQ_W=0, got {_h(out['pauser'])}"
            if c.udata_w == 0:
                assert out["pwuser"] == 0, f"CHK-001: o_apb_pwuser=0 when USER_DATA_W=0, got {_h(out['pwuser'])}"
        assert not (out["penable"] == 1 and out["psel"] == 0), "CHK-012: o_apb_penable=1 implies o_apb_psel=1, got psel=0"
        rise = out["psel"] == 1 and p["psel"] == 0
        if rise:
            assert out["penable"] == 0, "CHK-012/031: o_apb_penable=0 at the o_apb_psel rise, got 1"
        if p["psel"] == 1 and p["penable"] == 0:
            assert out["psel"] == 1 and out["penable"] == 1, \
                f"CHK-013/031: Setup lasts one cycle then Access, got psel={_h(out['psel'])} penable={_h(out['penable'])}"
        if p["psel"] == 1 and p["penable"] == 1:
            if sampled_ready:
                assert out["psel"] == 0 and out["penable"] == 0, \
                    f"CHK-015/031: psel/penable 0 after C, got psel={_h(out['psel'])} penable={_h(out['penable'])}"
            else:
                assert out["psel"] == 1 and out["penable"] == 1, \
                    f"CHK-014/032: Access held while i_apb_pready=0, got psel={_h(out['psel'])} penable={_h(out['penable'])}"
            if self.rec is not None:
                self.rec.acc_edges += 1
        changed = [k for k in FIELDS if out[k] != p[k]]
        if changed:
            assert rise, f"CHK-016/017/024: completer-side fields change only at the Setup entry edge, got change of {changed}"
        if c.apb5 and out["psel"] == 1:
            assert out["pwakeup"] == 1, "CHK-018/020: o_apb_pwakeup=1 whenever o_apb_psel=1, got 0"
        if out["pwakeup"] != p["pwakeup"]:
            self.wk_events.append((idx, out["pwakeup"]))
        if self.c_pending:
            self.c_pending = False
            rec = self.rec
            if rec is not None:
                rec.w = rec.acc_edges - 1
                if self.plan is not None and not self.wait_wakeup:
                    assert rec.acc_edges == self.plan["w"] + 1, \
                        f"CHK-032: psel=1,penable=1 at exactly w+1={self.plan['w']+1} slv edges ending at C, got {rec.acc_edges}"
            self.rec = None
            self.plan = None
        if rise:
            self._new(out, idx)
        # decide the inputs for the next rising edge
        r = b.r
        if out["psel"] == 1 and out["penable"] == 0:
            self.phase = "SETUP"
            self._idle_drive()
        elif out["psel"] == 1 and out["penable"] == 1:
            self.phase = "ACCESS"
            self.acc += 1
            if self.plan is None:
                self.plan = self._default_plan()
            pl = self.plan
            ready = self.acc >= pl["w"] + 1
            if self.wait_wakeup and out["pwakeup"] != 1:
                ready = False
            if ready:
                self.cur.update(pready=1, prdata=pl["prdata"], pslverr=pl["pslverr"],
                                pruser=pl["pruser"], pbuser=pl["pbuser"])
            else:
                self.cur["pready"] = 0
                self._noise(self.noisy)
                if pl.get("err_in_wait"):
                    self.cur["pslverr"] = 1
        else:
            self.phase = "IDLE"
            self._idle_drive()
        _ = r


# ----------------------------------------------------------------------------- test helpers
async def bring_up(dut, salt, periods=None):
    per = start_clocks(dut, periods)
    await reset_dut(dut, cycles=10)
    b = Bench(dut, per, rng(salt))
    b.start()
    return b


def budget(b, n, wmax=10, idle=5, extra_slv=0):
    c = b.cfg
    per = ((4 * c.N + 14) * b.Tm + (4 * c.N + 14 + wmax) * b.Ts) / b.Tm + idle + 8
    return int(n * per * 2 + extra_slv * b.Ts / b.Tm * 1.5) + 1000


async def wait_idle(b, max_cycles, what):
    n = int(max_cycles)
    for _ in range(n):
        await FallingEdge(b.mclk)
        b.chk()
        if not b.mst.busy():
            return
    assert False, f"{what}: all requester transfers complete within {n} i_clk_mst cycles, got {len(b.mst.ops)} queued, state {b.mst.state}"


def end_checks(b, expected_done=None, tag="CHK-029"):
    b.chk()
    assert b.slv_count == len(b.recs), \
        f"{tag}: one completer transfer per requester transfer, got {b.slv_count} completer for {len(b.recs)} Setup phases"
    for i, rec in enumerate(b.recs):
        assert rec.pr_idx is not None, f"{tag}: transfer {i} completes with one o_apb_pready, got none"
    if expected_done is not None:
        assert b.mst.done == expected_done, f"{tag}: {expected_done} PREADY completions, got {b.mst.done}"


def safe_delay(b, r):
    h = min(b.Tm, b.Ts) // 2
    lo, hi = 50, max(60, h - 50)
    t0 = now_ps()
    anchors = []
    if b.m_edges:
        anchors.append((b.m_edges[-1], b.Tm))
    if b.s_edges:
        anchors.append((b.s_edges[-1], b.Ts))
    for _ in range(64):
        d = r.randint(lo, hi)
        ok = True
        for a, T in anchors:
            hp = T / 2.0
            x = (t0 + d - a) % hp
            if min(x, hp - x) < 40:
                ok = False
                break
        if ok:
            return d
    return lo


async def quiet_idle(b, n):
    b.slv.noisy = True
    b.quiet = True
    for _ in range(n):
        await FallingEdge(b.sclk)
        b.chk()
    b.quiet = False
    b.slv.noisy = False


# ----------------------------------------------------------------------------- tests
@cocotb.test()
async def test_chk_019_apb5_user_signals(dut):
    """CHK-019: APB5 PAUSER/PWUSER travel with the request, PRUSER/PBUSER with the response."""
    b = await bring_up(dut, "chk019", (10, 20))
    c, r = b.cfg, b.r
    if not c.apb5:
        not_verifiable(dut, "CHK-019", "needs PARA_APBCDC_APB5=1 with user widths above 0; this run is APB4")
        return
    cnt = {"n": 0}

    def pol(rec):
        n = cnt["n"]
        cnt["n"] += 1
        sel = n % 8
        def pk(w):
            return 0 if sel == 0 else (mask(w) if sel == 1 else r.getrandbits(w))
        return dict(w=r.randint(0, 4), prdata=r.getrandbits(b.wsi["prdata"]), pslverr=r.randint(0, 1),
                    pruser=pk(b.wsi["pruser"]), pbuser=pk(b.wsi["pbuser"]), err_in_wait=False)
    b.slv.policy = pol
    items = []
    for i in range(300):
        it = rand_item(b, r, idle=r.randint(1, 4), wake="before")
        if i % 8 == 0:
            it["pauser"], it["pwuser"] = 0, 0
        elif i % 8 == 1:
            it["pauser"], it["pwuser"] = mask(b.wmi["pauser"]), mask(b.wmi["pwuser"])
        items.append(it)
    b.push(items)
    await wait_idle(b, budget(b, 300, 4), "CHK-019")
    end_checks(b, 300, "CHK-019")
    missing = [n for n, w in (("USER_REQ_W", c.ureq_w), ("USER_DATA_W", c.udata_w), ("USER_RESP_W", c.uresp_w)) if w == 0]
    if missing:
        not_verifiable(dut, "CHK-019", f"user widths {missing} are 0 in this run, those signals are absent; "
                                       "the specified 128/32/16 configuration needs another elaboration")


@cocotb.test()
async def test_chk_020_apb5_wakeup(dut):
    """CHK-020: APB5 wake-up propagation, in-progress term, completer waiting for PWAKEUP."""
    b = await bring_up(dut, "chk020", (10, 20))
    c, r = b.cfg, b.r
    N = c.N
    if not c.apb5:
        not_verifiable(dut, "CHK-020", "needs PARA_APBCDC_APB5=1; this run is APB4")
        return
    # (a) idle wake-up
    tail = math.ceil((N + 6) * b.Ts / b.Tm) + 4
    ml0, sl0 = len(b.mst.wk_log), len(b.slv.wk_events)
    b.push_op(("idle", 20, 1))
    b.push_op(("idle", tail, 0))
    await wait_idle(b, 20 + tail + 100, "CHK-020")
    ml = b.mst.wk_log[ml0:]
    sl = b.slv.wk_events[sl0:]
    assert len(ml) == 2 and ml[0][2] == 1 and ml[1][2] == 0, f"CHK-020: (a) W1 then W0 on i_apb_pwakeup, got {ml}"
    assert [v for _, v in sl] == [1, 0], f"CHK-020: (a) o_apb_pwakeup rises once and falls once, got {sl}"
    for (tw, _, _), (si, sv) in zip(ml, sl):
        k = si - bisect.bisect_right(b.s_edges, tw) + 1
        assert N + 1 <= k <= N + 3, f"CHK-020: (a) o_apb_pwakeup={sv} at the k-th i_clk_slv edge with k in [{N+1},{N+3}], got k={k}"
    assert b.slv_count == 0 and not b.recs, "CHK-020: (a) o_apb_psel stays 0 with no transfer, got a transfer"
    # (b) wake one cycle before psel
    b.slv.policy = make_policy(b, r, 0, 4, 0.2)
    b.push([rand_item(b, r, idle=r.randint(1, 4), wake="before") for _ in range(50)])
    await wait_idle(b, budget(b, 50, 4), "CHK-020")
    # (c) wake never driven
    idle_c = math.ceil((N + 4) * b.Ts / b.Tm) + 3
    c0 = len(b.recs)
    b.push([rand_item(b, r, idle=idle_c, wake="none") for _ in range(50)])
    await wait_idle(b, budget(b, 50, 4, idle_c), "CHK-020")
    c1 = len(b.recs)
    ev = b.slv.wk_events
    for n in range(c0, c1):
        rec = b.recs[n]
        falls = [i for (i, v) in ev if v == 0 and i >= rec.c_idx]
        assert falls, f"CHK-020: (c) o_apb_pwakeup returns to 0 after C of transfer {n}, it never did"
        f = falls[0]
        assert f - rec.c_idx <= N + 3, f"CHK-020: (c) o_apb_pwakeup 0 within {N+3} slv edges after C, got {f - rec.c_idx}"
        if n + 1 < c1:
            lim = bisect.bisect_right(b.s_edges, b.recs[n + 1].s0_t)
            early = [i for (i, v) in ev if v == 1 and f < i < lim]
            assert not early, f"CHK-020: (c) o_apb_pwakeup stays 0 while idle, got a rise at slv edges {early}"
    # (d) wake asserted during Access
    b.slv.policy = make_policy(b, r, 1, 4, 0.2)
    b.push([rand_item(b, r, idle=r.randint(2, 4), wake="during") for _ in range(20)])
    await wait_idle(b, budget(b, 20, 4), "CHK-020")
    # (e) completer waits for o_apb_pwakeup
    b.slv.wait_wakeup = True
    b.push([rand_item(b, r, idle=r.randint(1, 4)) for _ in range(20)])
    await wait_idle(b, budget(b, 20, 4), "CHK-020")
    b.slv.wait_wakeup = False
    end_checks(b, 140, "CHK-020")


@cocotb.test()
async def test_chk_021_apb4_ignores_apb5(dut):
    """CHK-021: with APB5=0 the APB5 inputs have no effect and the APB5 outputs are 0."""
    b = await bring_up(dut, "chk021")
    c, r = b.cfg, b.r
    if c.apb5:
        not_verifiable(dut, "CHK-021", "needs PARA_APBCDC_APB5=0; this run is APB5")
        return
    b.wake_random = True
    b.slv.policy = make_policy(b, r, 0, 4, 0.2)
    b.push([rand_item(b, r) for _ in range(200)])
    await wait_idle(b, budget(b, 200, 4), "CHK-021")
    end_checks(b, 200, "CHK-021")
    b.wake_random = False
    b.push_op(("idle", 3, 0))
    await wait_idle(b, 50, "CHK-021")
    b.quiet = True
    b.push_op(("idle", 50, 1))
    await wait_idle(b, 100, "CHK-021")
    b.quiet = False
    b.chk()


@cocotb.test()
async def test_chk_022_cfg_min(dut):
    """CHK-022: smallest configuration (1-bit address, 8-bit data) crosses bit for bit."""
    b = await bring_up(dut, "chk022", (10, 20))
    c, r = b.cfg, b.r
    cnt = {"n": 0}

    def pol(rec):
        n = cnt["n"]
        cnt["n"] += 1
        dw = b.wsi["prdata"]
        return dict(w=r.randint(0, 3), prdata=[0, mask(dw), r.getrandbits(dw)][n % 3],
                    pslverr=1 if r.random() < 0.3 else 0, pruser=0, pbuser=0, err_in_wait=False)
    b.slv.policy = pol
    items = []
    for i in range(500):
        wr = 1 if i % 2 == 0 else 0
        it = rand_item(b, r, write=wr, idle=r.randint(0, 3))
        it["paddr"] = [0, mask(c.addr_w), r.getrandbits(c.addr_w)][i % 3]
        it["pwdata"] = [0, mask(c.data_w), r.getrandbits(c.data_w)][(i // 2) % 3]
        it["pprot"] = (i // 2) % 8
        it["pstrb"] = ((i // 2) % (1 << c.strb_w)) if wr else 0
        items.append(it)
    b.push(items)
    await wait_idle(b, budget(b, 500, 3), "CHK-022")
    end_checks(b, 500, "CHK-022")
    if not (c.addr_w == 1 and c.data_w == 8):
        not_verifiable(dut, "CHK-022", f"CFG-MIN needs ADDR_W=1, DATA_W=8; this run has {c.addr_w}/{c.data_w} "
                                       "(the same stimulus was checked on these widths)")


@cocotb.test()
@cocotb.parametrize(periods=[(10, 20), (20, 10)])
async def test_chk_023_four_phase(dut, periods):
    """CHK-023: four-phase handshake, same function, PREADY only after the handshake closes."""
    b = await bring_up(dut, f"chk023-{periods}", periods)
    c, r = b.cfg, b.r
    if c.hs != 1:
        not_verifiable(dut, "CHK-023", "needs PARA_APBCDC_HS_TYPE=1; this run is two-phase")
        return
    b.slv.policy = make_policy(b, r, 0, 5, 0.3)
    items = []
    for i in range(200):
        b2b = i % 2 == 1
        items.append(rand_item(b, r, idle=0 if b2b else r.randint(1, 5), wake="none" if b2b else "auto"))
    b.push(items)
    await wait_idle(b, budget(b, 200, 5), "CHK-023")
    end_checks(b, 200, "CHK-023")
    for rec in b.recs:
        assert rec.j >= 2 * c.N + 2, f"CHK-023: PREADY no earlier than edge {2*c.N+2} after C, got {rec.j}"


@cocotb.test()
async def test_chk_024_requester_violations(dut):
    """CHK-024: PENABLE without Setup ignored, Access-phase field changes and extended Setup use the first Setup."""
    b = await bring_up(dut, "chk024", (10, 20))
    c, r = b.cfg, b.r
    N = c.N
    n_after = math.ceil((N + 16) * b.Ts / b.Tm) + 2
    s0 = len(b.s_edges)
    b.push_op(("raw", 20, {"psel": 1, "penable": 1, "pwakeup": 0}))
    b.push_op(("idle", n_after, 0))
    await wait_idle(b, 20 + n_after + 100, "CHK-024")
    assert b.slv_count == 0 and not b.recs and b.mst.done == 0, \
        "CHK-024: (a) PENABLE without Setup starts no transfer, got one"
    assert b.slv.prev["psel"] == 0, "CHK-024: (a) o_apb_psel stays 0, got 1"
    assert len(b.s_edges) - s0 >= N + 13, f"CHK-024: (a) observed at least {N+13} slv edges, got {len(b.s_edges)-s0}"
    b.slv.policy = make_policy(b, r, 0, 3, 0.3)
    items = [rand_item(b, r, idle=r.randint(1, 4), ill="chg") for _ in range(50)]
    items += [rand_item(b, r, idle=r.randint(1, 4), rep=1) for _ in range(10)]
    items += [rand_item(b, r) for _ in range(50)]
    b.push(items)
    await wait_idle(b, budget(b, 110, 3), "CHK-024")
    end_checks(b, 110, "CHK-024")


async def _latency_sweep(dut, periods, chk, hs_req):
    b = await bring_up(dut, f"{chk}-{periods}", periods)
    c, r = b.cfg, b.r
    if c.hs != hs_req:
        not_verifiable(dut, chk, f"needs PARA_APBCDC_HS_TYPE={hs_req}; this run has {c.hs}")
        return
    b.slv.policy = make_policy(b, r, 0, 8, 0.2)
    b.push([rand_item(b, r, idle=r.randint(1, 5)) for _ in range(200)])
    await wait_idle(b, budget(b, 200, 8), chk)
    end_checks(b, 200, chk)
    N, Tm, Ts = c.N, b.Tm, b.Ts
    model = len({rec.k for rec in b.recs}) > 1 or (hs_req == 0 and len({rec.j for rec in b.recs}) > 1)
    for i, rec in enumerate(b.recs):
        D = b.m_edges[rec.pr_idx + 1] - b.m_edges[rec.s0_idx - 1]
        w = rec.w
        if hs_req == 0:
            bound = (N + 3) * Tm + (N + 3 + w) * Ts
            if model:
                bound += max(0, rec.k - (N + 1)) * Ts + max(0, rec.j - (N + 1)) * Tm
        else:
            bound = (2 * N + 4) * Tm + (2 * N + 4 + w) * Ts
            if model:
                bound += max(0, rec.k - (N + 1)) * Ts + 2 * Ts + 4 * Tm
        assert D <= bound + 2, f"{chk}: transfer {i} duration D <= {bound} ps (w={w}), got {D} ps"
    if model:
        not_verifiable(dut, chk, "the synchronizer model adds extra latency in this run (crossing counts vary); "
                                 "the bound was checked with the modelled extra cycles allowed, the strict bound "
                                 "needs the extra latency forced to 0")


@cocotb.test()
@cocotb.parametrize(periods=[(10, 10), (10, 20), (20, 10), (10, 90), (90, 10)])
async def test_chk_025_two_phase_duration(dut, periods):
    """CHK-025: two-phase transfer duration D <= (N+3)Tm + (N+3+w)Ts."""
    await _latency_sweep(dut, periods, "CHK-025", 0)


@cocotb.test()
@cocotb.parametrize(periods=[(10, 10), (10, 20), (20, 10), (10, 90), (90, 10)])
async def test_chk_026_four_phase_duration(dut, periods):
    """CHK-026: four-phase transfer duration D <= (2N+4)Tm + (2N+4+w)Ts."""
    await _latency_sweep(dut, periods, "CHK-026", 1)


@cocotb.test()
async def test_chk_027_reset_values(dut):
    """CHK-027: reset values, quiet idle after release, asynchronous reset assertion."""
    for k in M_IN:
        getattr(dut, "i_apb_" + k).value = 0
    for k in S_IN:
        getattr(dut, "i_apb_" + k).value = 0
    getattr(dut, MRST).value = 0
    getattr(dut, SRST).value = 0
    per = start_clocks(dut, (10, 20))
    b = Bench(dut, per, rng("chk027"))
    b.hold_reset()
    b.start()
    c, r = b.cfg, b.r
    for _ in range(11):
        await FallingEdge(b.sclk)
        b.chk()
    await b.release("mst_first", 3)
    await quiet_idle(b, 100)

    def pol(rec):
        return dict(w=r.randint(0, 2), prdata=r.randint(1, mask(b.wsi["prdata"])), pslverr=0,
                    pruser=r.getrandbits(b.wsi["pruser"]), pbuser=r.getrandbits(b.wsi["pbuser"]), err_in_wait=False)
    for rnd in range(2):
        b.slv.policy = pol
        rd = rand_item(b, r, write=0, idle=2)
        rd["paddr"] = r.randint(1, mask(c.addr_w))
        wr = rand_item(b, r, write=1, idle=2)
        wr["paddr"] = r.randint(1, mask(c.addr_w))
        wr["pwdata"] = r.randint(1, mask(c.data_w))
        b.push([rd, wr])
        b.push_op(("idle", 5, 0))
        await wait_idle(b, budget(b, 2, 2), "CHK-027")
        end_checks(b, 2 * (rnd + 1), "CHK-027")
        if rnd == 1:
            break
        so, mo = b.sample(b.so), b.sample(b.mo)
        assert so["pwrite"] == 1 and so["paddr"] != 0 and so["pwdata"] != 0 and mo["prdata"] != 0, \
            f"CHK-027: nonzero o_apb_pwrite/paddr/pwdata/prdata before the reset, got {so['pwrite']}/{_h(so['paddr'])}/{_h(so['pwdata'])}/{_h(mo['prdata'])}"
        await FallingEdge(b.mclk)
        await ps_timer(safe_delay(b, r))
        await b.assert_resets("CHK-027")
        for _ in range(5):
            await FallingEdge(b.sclk)
            b.chk()
        await b.release("mst_first", 3)
        await quiet_idle(b, 100)
    b.chk()


@cocotb.test()
async def test_chk_028_reset_during_traffic(dut):
    """CHK-028: reset during random traffic, transfer lost, clean restart, staggered release."""
    b = await bring_up(dut, "chk028")
    r = b.r
    b.retry_lost = True
    b.slv.noisy = True
    b.slv.policy = make_policy(b, r, 0, 6, 0.3)
    m, s = b.mst, b.slv

    def cond(ph):
        if ph == "req_setup":
            return m.state == "SETUP"
        if ph == "req_cross":
            return m.state == "ACCESS" and m.rec is not None and m.rec.psel_idx is None
        if ph == "slv_setup":
            return s.phase == "SETUP"
        if ph == "slv_wait":
            return s.phase == "ACCESS" and s.plan is not None and s.plan["w"] > 0 and s.acc <= s.plan["w"]
        if ph == "ack_cross":
            return m.state == "ACCESS" and m.rec is not None and m.rec.c_t is not None
        return m.state == "RESP"
    phases = ["req_setup", "req_cross", "slv_setup", "slv_wait", "ack_cross", "pready"]
    slow = b.sclk if b.Ts >= b.Tm else b.mclk
    for n in range(30):
        ph = phases[n % len(phases)]
        hit = False
        for _ in range(20000):
            await First(FallingEdge(b.mclk), FallingEdge(b.sclk))
            b.chk()
            while len(m.ops) < 3:
                b.push([rand_item(b, r)])
            if cond(ph):
                hit = True
                break
        assert hit, f"CHK-028: traffic reaches phase {ph} for reset #{n}, got no such phase in 20000 edges"
        await ps_timer(safe_delay(b, r))
        await b.assert_resets("CHK-028")
        for _ in range(r.randint(3, 10)):
            await FallingEdge(slow)
            b.chk()
        await b.release("mst_first" if n % 2 == 0 else "slv_first", r.randint(0, 10))
    b.push([rand_item(b, r) for _ in range(40)])
    await wait_idle(b, budget(b, 50, 6), "CHK-028")
    end_checks(b, b.pushed, "CHK-028")


@cocotb.test()
async def test_chk_029_scoreboard_ratios(dut):
    """CHK-029: random traffic scoreboard with a noisy completer at one clock ratio per run."""
    choices = [(10, 10), (10, 20), (20, 10), (10, 30), (30, 10), (10, 90), (90, 10), (10, 14), (14, 10), (13.7, 10), None]
    periods = rng("chk029-ratio").choice(choices)
    b = await bring_up(dut, "chk029", periods)
    c, r = b.cfg, b.r
    b.slv.noisy = True
    b.slv.policy = make_policy(b, r, 0, 10, 0.3)
    wakes = ["before", "none", "during"] if c.apb5 else ["none"]
    b.push([rand_item(b, r, wake=r.choice(wakes)) for _ in range(2000)])
    await wait_idle(b, budget(b, 2000, 10), "CHK-029")
    end_checks(b, 2000, "CHK-029")


@cocotb.test()
async def test_chk_030_sync_depth(dut):
    """CHK-030: CELL_TYPE=4 gives N=4, crossing windows [5,7]."""
    b = await bring_up(dut, "chk030", (10, 20))
    c, r = b.cfg, b.r
    b.slv.policy = make_policy(b, r, 0, 3, 0.2)
    b.push([rand_item(b, r) for _ in range(100)])
    await wait_idle(b, budget(b, 100, 3), "CHK-030")
    end_checks(b, 100, "CHK-030")
    if c.cell == 4 and c.hs == 0:
        for rec in b.recs:
            assert 5 <= rec.k <= 7, f"CHK-030: o_apb_psel at slv edge k in [5,7] after S0, got {rec.k}"
            assert 5 <= rec.j <= 7, f"CHK-030: o_apb_pready at mst edge j in [5,7] after C, got {rec.j}"
    else:
        not_verifiable(dut, "CHK-030", f"needs CELL_TYPE=4 and HS_TYPE=0; this run has {c.cell}/{c.hs} "
                                       f"(windows checked for N={c.N})")


@cocotb.test()
async def test_chk_031_single_write_read(dut):
    """CHK-031: single writes and reads without wait states, field/response transport and windows."""
    b = await bring_up(dut, "chk031", (10, 20))
    c, r = b.cfg, b.r
    b.slv.policy = make_policy(b, r, 0, 0, 0.0)
    items = [rand_item(b, r, write=1, idle=r.randint(2, 5)) for _ in range(50)]
    items += [rand_item(b, r, write=0, idle=r.randint(2, 5)) for _ in range(50)]
    r.shuffle(items)
    for i, ones in ((0, False), (1, True), (2, False), (3, True)):
        it = items[i]
        it["paddr"] = mask(c.addr_w) if ones else 0
        it["pprot"] = 7 if ones else 0
        it["pwdata"] = mask(c.data_w) if ones else 0
        it["pstrb"] = (mask(c.strb_w) if ones else 0) if it["pwrite"] else 0
    b.push(items)
    await wait_idle(b, budget(b, 100, 0), "CHK-031")
    end_checks(b, 100, "CHK-031")
    assert len(b.recs) == 100 and b.slv_count == 100, f"CHK-031: 100 transfers on each side, got {len(b.recs)}/{b.slv_count}"
    if c.hs != 0:
        not_verifiable(dut, "CHK-031", "the two-phase PREADY window needs HS_TYPE=0; this run is four-phase")


@cocotb.test()
async def test_chk_032_wait_states(dut):
    """CHK-032: completer wait states extend the transfer without limit (one 10000-cycle wait)."""
    b = await bring_up(dut, "chk032", (10, 20))
    c, r = b.cfg, b.r
    ws = [0, 1, 2, 5, 17] * 4 + [r.choice([r.randint(0, 30), 0, 1, 2, 5, 17]) for _ in range(39)]
    ws.insert(r.randint(5, len(ws)), 10000)
    b.slv.policy = make_policy(b, r, 0, 30, 0.2, wseq=ws)
    b.push([rand_item(b, r, idle=r.randint(0, 4)) for _ in range(60)])
    await wait_idle(b, budget(b, 60, 30, 4, sum(ws)), "CHK-032")
    end_checks(b, 60, "CHK-032")
    assert any(rec.w == 10000 for rec in b.recs), "CHK-032: one transfer with w=10000, got none"
    if c.hs != 0:
        not_verifiable(dut, "CHK-032", "the two-phase PREADY window needs HS_TYPE=0; this run is four-phase")


@cocotb.test()
async def test_chk_033_error_response(dut):
    """CHK-033: PSLVERR forwarded with data, next transfer independent."""
    b = await bring_up(dut, "chk033", (10, 20))
    r = b.r
    st = {"last": False, "err": 0, "eiw": 0}

    def pol(rec):
        w = r.randint(0, 5)
        err = 0 if st["last"] else (1 if r.random() < 0.5 else 0)
        st["last"] = bool(err)
        eiw = (not err) and w > 0 and r.random() < 0.4
        st["err"] += err
        st["eiw"] += int(eiw)
        dw = b.wsi["prdata"]
        pd = r.randint(1, mask(dw)) if err else val_pick(r, dw)
        return dict(w=w, prdata=pd, pslverr=err, pruser=val_pick(r, b.wsi["pruser"]),
                    pbuser=val_pick(r, b.wsi["pbuser"]), err_in_wait=eiw)
    b.slv.policy = pol
    b.push([rand_item(b, r, idle=r.randint(0, 4)) for _ in range(100)])
    await wait_idle(b, budget(b, 100, 5), "CHK-033")
    end_checks(b, 100, "CHK-033")
    assert st["err"] > 0 and st["eiw"] > 0, f"CHK-033: stimulus has errors and errors in wait cycles, got {st}"


@cocotb.test()
@cocotb.parametrize(periods=[(10, 20), (20, 10)])
async def test_chk_034_back_to_back(dut, periods):
    """CHK-034: back-to-back transfers accepted in the cycle after PREADY, one at a time."""
    b = await bring_up(dut, f"chk034-{periods}", periods)
    r = b.r
    b.slv.policy = make_policy(b, r, 0, 3, 0.2)
    idx = list(range(1, 200))
    r.shuffle(idx)
    b2b = set(idx[:150])
    items = [rand_item(b, r, idle=0 if i in b2b else r.randint(1, 5), wake="none") for i in range(200)]
    b.push(items)
    await wait_idle(b, budget(b, 200, 3), "CHK-034")
    end_checks(b, 200, "CHK-034")
    for i in range(1, 200):
        if items[i]["idle"] == 0:
            assert b.recs[i].s0_idx == b.recs[i - 1].pr_idx + 2, \
                f"CHK-034: back-to-back Setup accepted in the cycle after PREADY for transfer {i}, got S0 at {b.recs[i].s0_idx}"


@cocotb.test()
async def test_chk_035_pprot_pstrb(dut):
    """CHK-035: PPROT and PSTRB forwarded unchanged, including nonzero PSTRB on a read."""
    b = await bring_up(dut, "chk035", (10, 20))
    c, r = b.cfg, b.r
    b.slv.policy = make_policy(b, r, 0, 2, 0.3)
    items = []
    for prot in range(8):
        for s in range(1 << c.strb_w):
            it = rand_item(b, r, write=1, idle=r.randint(0, 3))
            it["pprot"], it["pstrb"], it["pwdata"] = prot, s, r.getrandbits(c.data_w)
            items.append(it)
    for prot in range(8):
        it = rand_item(b, r, write=0, idle=r.randint(0, 3))
        it["pprot"] = prot
        items.append(it)
    for _ in range(16):
        it = rand_item(b, r, write=0, idle=r.randint(0, 3))
        it["pstrb"] = r.randint(1, mask(c.strb_w))
        items.append(it)
    r.shuffle(items)
    b.push(items)
    await wait_idle(b, budget(b, len(items), 2), "CHK-035")
    end_checks(b, len(items), "CHK-035")


@cocotb.test()
async def test_regression_random(dut):
    """CHK-001..CHK-018 exercise: broad legal random traffic with a noisy completer and scoreboard."""
    b = await bring_up(dut, "regression")
    c, r = b.cfg, b.r
    b.slv.noisy = True
    b.slv.policy = make_policy(b, r, 0, 10, 0.3)
    wakes = ["before", "none", "during"] if c.apb5 else ["none"]
    items = [rand_item(b, r, idle=0 if r.random() < 0.4 else r.randint(1, 5), wake=r.choice(wakes))
             for _ in range(1500)]
    b.push(items)
    await wait_idle(b, budget(b, 1500, 10), "regression")
    end_checks(b, 1500, "CHK-029")

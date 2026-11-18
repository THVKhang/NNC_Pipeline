"""cocotb 2.1 testbench for m_apb_tlul_bridge.

Covers the test checks CHK-018 .. CHK-031 plus a legal random regression.  The
assertion checks CHK-001 .. CHK-017 are also re-checked here, from ports only, by a
cycle monitor that runs during every test.

Timing model (from the plan):
  * One cycle runs from one falling edge to the next.  At each falling edge the bench
    samples all outputs and then drives all inputs for that cycle.  Together they are
    "the values at the rising edge E that ends the cycle".
  * E0 is the edge that ends the Setup cycle.  E_m is the edge m cycles later.  An Access
    phase of N cycles means o_apb_pready is sampled 1 at E_N.
"""
import collections
import os

import cocotb
from cocotb.triggers import FallingEdge, RisingEdge, Timer

from nnc_cocotb import *  # noqa: F401,F403


# --------------------------------------------------------------------------------------
# Parameters of this run
# --------------------------------------------------------------------------------------
def _param(name, default):
    try:
        v = PARAMS.get(name, default)
    except Exception:  # pragma: no cover - PARAMS missing
        v = default
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


ADDR_W = _param("PARA_ADDR_W", 32)
SRC_W = _param("PARA_SRC_W", 8)
SRC_ID = _param("PARA_SRC_ID", 0)
A_USER_W = _param("PARA_A_USER_W", 1)
D_SINK_W = _param("PARA_D_SINK_W", 1)
D_USER_W = _param("PARA_D_USER_W", 1)

AMASK = (1 << ADDR_W) - 1
SRC_MASK = (1 << SRC_W) - 1
M32 = 0xFFFFFFFF

OUTS = ["o_apb_pready", "o_apb_prdata", "o_apb_pslverr", "o_tlul_a_valid", "o_tlul_a_opcode",
        "o_tlul_a_param", "o_tlul_a_size", "o_tlul_a_source", "o_tlul_a_address",
        "o_tlul_a_mask", "o_tlul_a_data", "o_tlul_a_user", "o_tlul_d_ready"]
AFIELDS = ["o_tlul_a_opcode", "o_tlul_a_param", "o_tlul_a_size", "o_tlul_a_source",
           "o_tlul_a_address", "o_tlul_a_mask", "o_tlul_a_data", "o_tlul_a_user"]
RESET_ZERO = ["o_tlul_a_valid", "o_tlul_d_ready", "o_apb_pready", "o_apb_pslverr",
              "o_apb_prdata", "o_tlul_a_opcode", "o_tlul_a_address", "o_tlul_a_data"]
CONSTS = {"o_tlul_a_param": 0, "o_tlul_a_size": 2, "o_tlul_a_mask": 0xF,
          "o_tlul_a_source": SRC_ID & SRC_MASK, "o_tlul_a_user": 0}
DEFAULT_INPUTS = {
    "i_rst_n_core": 0, "i_apb_psel": 0, "i_apb_penable": 0, "i_apb_pwrite": 0,
    "i_apb_paddr": 0, "i_apb_pprot": 0, "i_apb_pstrb": 0, "i_apb_pwdata": 0,
    "i_tlul_a_ready": 0, "i_tlul_d_valid": 0, "i_tlul_d_opcode": 0,
    "i_tlul_d_source": SRC_ID & SRC_MASK, "i_tlul_d_data": 0, "i_tlul_d_error": 0,
    "i_tlul_d_param": 0, "i_tlul_d_size": 2, "i_tlul_d_sink": 0, "i_tlul_d_user": 0,
}


def aligned(q):
    """Random word-aligned address of PARA_ADDR_W bits."""
    return q.getrandbits(ADDR_W) & AMASK & ~3


def nz32(q):
    v = q.getrandbits(32)
    return v if v else 0xA5A5A5A5


def orphan_fields(q, avoid=None):
    data = q.getrandbits(32)
    if avoid is not None and data == avoid:
        data ^= 1
    src = (SRC_ID & SRC_MASK) if q.random() < 0.5 else q.getrandbits(SRC_W)
    return dict(i_tlul_d_opcode=q.randrange(8), i_tlul_d_source=src,
                i_tlul_d_error=q.getrandbits(1), i_tlul_d_data=data)


# --------------------------------------------------------------------------------------
# Transfer description and reference model (from the specification text only)
# --------------------------------------------------------------------------------------
class Transfer:
    """One APB transfer, plus the device behavior for its TL-UL request.

    k: number of cycles a_ready stays 0 while a_valid=1 (None = never accepts)
    j: response cycle offset after the acceptance cycle (0 = same cycle, None = never)
    resp: 'ok', 'derr' (d_error=1), 'op' (d_opcode=bad_op), 'src' (d_source=bad_src)
    gap: idle cycles (psel=0) between the previous PREADY cycle and this Setup cycle
    """
    _next_id = 0

    def __init__(self, write, addr, wdata=0, strb=0xF, prot=0, gap=1, k=0, j=1, resp="ok",
                 d_data=1, bad_op=None, bad_src=None, tag=None):
        Transfer._next_id += 1
        self.id = Transfer._next_id
        self.write = int(bool(write))
        self.addr = addr & AMASK
        self.wdata = wdata & M32
        self.strb = strb & 0xF
        self.prot = prot & 7
        self.gap = gap
        self.k = k
        self.j = j
        self.resp = resp
        self.d_data = d_data & M32
        self.bad_op = bad_op
        self.bad_src = (bad_src if bad_src is not None else (SRC_ID ^ 1)) & SRC_MASK
        self.tag = tag
        # results
        self.setup_n = None
        self.pready_n = None
        self.access = 0
        self.prdata = None
        self.pslverr = None
        self.hs = []
        self.av_cycles = []
        self.av_unstable = False
        self.resp_n = None
        self.abandoned = False
        self.recs = {}
        self.b2b_prev = None

    def legal(self):
        return (self.addr & 3) == 0 and (not self.write or self.strb == 0xF)

    def kind(self):
        if self.addr & 3:
            return "MIS"
        if self.write and self.strb != 0xF:
            return "ILS"
        return "W" if self.write else "R"

    def desc(self):
        return (f"transfer#{self.id} {'write' if self.write else 'read'} addr=0x{self.addr:x} "
                f"strb=0x{self.strb:x} k={self.k} j={self.j} resp={self.resp}")

    def rec(self, m):
        r = self.recs.get(m)
        assert r is not None, f"testbench: no recorded edge E{m} for {self.desc()}"
        return r


def ref_expect(t):
    """Expected APB completion of a transfer (spec sections 3, 6.3, 10.3, 12)."""
    if not t.legal():
        # REQ-ERR-001/002, REQ-PERF-003: 1 Access cycle, PSLVERR=1, PRDATA=0, no request.
        return dict(legal=False, access=1, pslverr=1, prdata=0)
    good_op = 0 if t.write else 1
    err = (t.resp == "derr") or (t.resp == "op" and t.bad_op != good_op) or \
          (t.resp == "src" and t.bad_src != (SRC_ID & SRC_MASK))
    prdata = 0 if (t.write or err) else t.d_data
    # REQ-PERF-001/002 + back pressure: PREADY at E(2+k+j).
    return dict(legal=True, access=2 + t.k + t.j, pslverr=int(err), prdata=prdata,
                opcode=0 if t.write else 4, address=t.addr & AMASK & ~3,
                hs_n=t.setup_n + 1 + t.k)


# --------------------------------------------------------------------------------------
# Port monitor: the assertion checks CHK-001 .. CHK-017, computed from ports only
# --------------------------------------------------------------------------------------
class Monitor:
    def __init__(self):
        self.prev = None
        self.req_open = 0
        self.pending = 0
        self.exp_get = 0

    def check(self, r):
        p = self.prev
        self.prev = r
        n = r["n"]
        # CHK-017 (in and out of reset)
        for o, v in CONSTS.items():
            assert r[o] == v, f"CHK-017: expected {o}={v} at edge of cycle {n} got {r[o]}"
        assert r["o_tlul_a_opcode"] in (0, 4), \
            f"CHK-017: expected o_tlul_a_opcode in (0,4) at cycle {n} got {r['o_tlul_a_opcode']}"
        assert r["o_tlul_a_address"] & 3 == 0, \
            f"CHK-017: expected o_tlul_a_address[1:0]=0 at cycle {n} got 0x{r['o_tlul_a_address']:x}"
        pv = r["o_apb_pready"]
        # CHK-003 (whatever the reset value)
        if r["o_apb_pslverr"] == 1:
            assert pv == 1, f"CHK-003: o_apb_pslverr=1 requires o_apb_pready=1 at cycle {n} got 0"
        if r["i_rst_n_core"] != 1:
            bad = [f"{o}={r[o]}" for o in RESET_ZERO if r[o] != 0]
            assert not bad, f"CHK-012: expected all reset outputs 0 in reset at cycle {n} got {bad}"
            self.req_open = 0
            self.pending = 0
            return
        av = r["o_tlul_a_valid"]
        ar = r["i_tlul_a_ready"]
        dv = r["i_tlul_d_valid"]
        dr = r["o_tlul_d_ready"]
        psel = r["i_apb_psel"]
        pen = r["i_apb_penable"]
        prst = p is not None and p["i_rst_n_core"] == 1
        if prst:
            if p.get("_setup_legal"):
                exp_op = 0 if p["i_apb_pwrite"] == 1 else 4
                assert av == 1, f"CHK-006: expected o_tlul_a_valid=1 at E1 (cycle {n}) got {av}"
                assert pv == 0, f"CHK-006: expected o_apb_pready=0 at E1 (cycle {n}) got {pv}"
                assert dr == 1, f"CHK-006: expected o_tlul_d_ready=1 at E1 (cycle {n}) got {dr}"
                assert r["o_tlul_a_opcode"] == exp_op, \
                    f"CHK-006: expected a_opcode={exp_op} at E1 (cycle {n}) got {r['o_tlul_a_opcode']}"
                exp_ad = p["i_apb_paddr"] & AMASK & ~3
                assert r["o_tlul_a_address"] == exp_ad, \
                    f"CHK-006: expected a_address=0x{exp_ad:x} at E1 got 0x{r['o_tlul_a_address']:x}"
                if p["i_apb_pwrite"] == 1:
                    assert r["o_tlul_a_data"] == p["i_apb_pwdata"], \
                        f"CHK-006: expected a_data=0x{p['i_apb_pwdata']:08x} at E1 got " \
                        f"0x{r['o_tlul_a_data']:08x}"
            if p.get("_setup_illegal"):
                assert pv == 1 and r["o_apb_pslverr"] == 1 and r["o_apb_prdata"] == 0 and av == 0, \
                    f"CHK-007: expected pready=1 pslverr=1 prdata=0 a_valid=0 at E1 (cycle {n}) got " \
                    f"pready={pv} pslverr={r['o_apb_pslverr']} prdata=0x{r['o_apb_prdata']:x} a_valid={av}"
                r["_ill_e1"] = True
            if p.get("_ill_e1"):
                assert av == 0, f"CHK-007: expected o_tlul_a_valid=0 at E2 (cycle {n}) got {av}"
            e = p.get("_exp10")
            if e is not None:
                assert pv == 1, f"CHK-010: expected o_apb_pready=1 at cycle {n} after counted response got 0"
                assert r["o_apb_pslverr"] == e[0], \
                    f"CHK-010: expected o_apb_pslverr={e[0]} at cycle {n} got {r['o_apb_pslverr']}"
                assert r["o_apb_prdata"] == e[1], \
                    f"CHK-010: expected o_apb_prdata=0x{e[1]:08x} at cycle {n} got 0x{r['o_apb_prdata']:08x}"
            if pv == 1:
                assert p.get("_cause"), \
                    f"CHK-011: o_apb_pready=1 at cycle {n} without counted response or illegal Setup before"
            if p["o_apb_pready"] == 1:
                assert pv == 0, f"CHK-002: expected o_apb_pready=0 at cycle {n} after a PREADY cycle got 1"
            if pv == 0:
                assert r["o_apb_prdata"] == p["o_apb_prdata"], \
                    f"CHK-004: expected o_apb_prdata to hold 0x{p['o_apb_prdata']:08x} at cycle {n} got " \
                    f"0x{r['o_apb_prdata']:08x}"
            assert dr == 1, f"CHK-013: expected o_tlul_d_ready=1 at cycle {n} got {dr}"
            if p["o_tlul_a_valid"] == 1 and p["i_tlul_a_ready"] == 0:
                assert av == 1, f"CHK-015: expected o_tlul_a_valid held 1 at cycle {n} got {av}"
                for f in AFIELDS:
                    assert r[f] == p[f], f"CHK-015: {f} changed while not accepted at cycle {n}: " \
                                         f"{p[f]} -> {r[f]}"
            if p["o_tlul_a_valid"] == 1 and p["i_tlul_a_ready"] == 1:
                assert av == 0, f"CHK-016: expected o_tlul_a_valid=0 after handshake at cycle {n} got {av}"
            if p["o_tlul_a_valid"] == 0 and av == 1:
                ok = (p["i_apb_psel"] == 1 and p["i_apb_penable"] == 0 and (p["i_apb_paddr"] & 3) == 0
                      and (p["i_apb_pwrite"] == 0 or p["i_apb_pstrb"] == 0xF))
                assert ok, f"CHK-014: o_tlul_a_valid rose at cycle {n} without a legal Setup before"
        if pv == 1:
            assert psel == 1 and pen == 1, \
                f"CHK-001: o_apb_pready=1 at cycle {n} with psel={psel} penable={pen}"
            if r["i_apb_pwrite"] == 1 or r["o_apb_pslverr"] == 1:
                assert r["o_apb_prdata"] == 0, \
                    f"CHK-005: expected o_apb_prdata=0 on write/error completion at cycle {n} got " \
                    f"0x{r['o_apb_prdata']:08x}"
        if av == 1:
            assert psel == 1 and pen == 1 and pv == 0, \
                f"CHK-009: o_tlul_a_valid=1 at cycle {n} with psel={psel} penable={pen} pready={pv}"
            assert self.req_open == 0, \
                f"CHK-008: o_tlul_a_valid=1 at cycle {n} while a request is still open"
        setup = psel == 1 and pen == 0
        legal = (r["i_apb_paddr"] & 3) == 0 and (r["i_apb_pwrite"] == 0 or r["i_apb_pstrb"] == 0xF)
        if setup and legal:
            assert pv == 0 and av == 0, \
                f"CHK-006: expected pready=0 and a_valid=0 at Setup edge (cycle {n}) got {pv}/{av}"
        r["_setup_legal"] = setup and legal
        r["_setup_illegal"] = setup and not legal
        hs = av == 1 and ar == 1
        dacc = dv == 1 and dr == 1
        counted = dacc and (self.pending == 1 or hs)
        if counted:
            eg = self.exp_get if self.pending else (r["o_tlul_a_opcode"] >> 2) & 1
            exp_op = 1 if eg else 0
            err = int(r["i_tlul_d_error"] == 1 or r["i_tlul_d_opcode"] != exp_op
                      or r["i_tlul_d_source"] != (SRC_ID & SRC_MASK))
            r["_exp10"] = (err, r["i_tlul_d_data"] if (eg and not err) else 0)
        r["_cause"] = bool(counted or r["_setup_illegal"])
        if self.pending and dacc:
            self.pending = 0
        if hs and not dacc:
            self.pending = 1
            self.exp_get = (r["o_tlul_a_opcode"] >> 2) & 1
        if hs:
            self.req_open = 1
        if pv == 1:
            self.req_open = 0


# --------------------------------------------------------------------------------------
# APB requester model
# --------------------------------------------------------------------------------------
class Requester:
    def __init__(self, b):
        self.b = b
        self.queue = collections.deque()
        self.limit = 300
        self.cur = None
        self.last = None
        self.reset()

    def reset(self):
        b = self.b
        if self.cur is not None:
            self.cur.abandoned = True
        self.cur = None
        if self.last is not None and self.last.pready_n == b.n and self.last in b.score_q:
            # Reset asserted mid-cycle in the PREADY cycle: the completion is never sampled.
            b.score_q.remove(self.last)
            self.last.abandoned = True
        self.state = "idle"
        self.idle_cnt = 0
        self.since_done = 99

    def step(self, s):
        b = self.b
        if b.in_reset:
            b.drive(i_apb_psel=0, i_apb_penable=0)
            return
        pr = s["o_apb_pready"]
        if self.state == "setup":
            self.state = "access"
            b.drive(i_apb_penable=1)
            self.cur.access = 0
        if self.state == "access":
            t = self.cur
            t.access += 1
            assert pr in (0, 1), f"{b.chk}: o_apb_pready is X/Z in Access cycle {t.access} of {t.desc()}"
            if pr == 1:
                t.pready_n = b.n
                t.prdata = s["o_apb_prdata"]
                t.pslverr = s["o_apb_pslverr"]
                self.cur = None
                self.state = "idle"
                self.idle_cnt = 0
                self.since_done = 0
                self.last = t
                b.score_q.append(t)
            elif self.limit and t.access > self.limit:
                raise AssertionError(f"{b.chk}: {t.desc()}: no o_apb_pready within {self.limit} "
                                     f"Access cycles")
            return
        self.since_done += 1
        assert pr == 0, f"{b.chk}: o_apb_pready={pr} at cycle {b.n} with no APB transfer in its Access phase"
        if self.queue and self.idle_cnt >= self.queue[0].gap:
            t = self.queue.popleft()
            self.cur = t
            t.setup_n = b.n
            if self.since_done == 1 and self.last is not None and not self.last.abandoned:
                t.b2b_prev = self.last
            self.state = "setup"
            b.drive(i_apb_psel=1, i_apb_penable=0, i_apb_pwrite=t.write, i_apb_paddr=t.addr,
                    i_apb_pstrb=t.strb, i_apb_pwdata=t.wdata, i_apb_pprot=t.prot)
        else:
            b.drive(i_apb_psel=0, i_apb_penable=0)
            self.idle_cnt += 1


# --------------------------------------------------------------------------------------
# TL-UL device model (REF-005 by default; error injection per transfer)
# --------------------------------------------------------------------------------------
class Device:
    def __init__(self, b):
        self.b = b
        self.side_rng = None
        self.idle_ready = 0
        self.reset()

    def reset(self):
        self.presenting = None
        self.first = None
        self.wait = 0
        self.resp = None
        self.forever = False
        self.a_ready_now = 0
        self.real_d = False

    def busy(self):
        return self.resp is not None or self.forever

    def _side(self):
        q = self.side_rng
        if q is not None:
            self.b.drive(i_tlul_d_param=q.getrandbits(3), i_tlul_d_size=q.getrandbits(2),
                         i_tlul_d_sink=q.getrandbits(D_SINK_W), i_tlul_d_user=q.getrandbits(D_USER_W))

    def _resp_fields(self, t, hs):
        opc = hs["opcode"]
        get = ((opc >> 2) & 1) if opc is not None else (0 if t.write else 1)
        op = 1 if get else 0
        src = hs["source"] if hs["source"] is not None else SRC_ID
        err = 0
        if t.resp == "derr":
            err = 1
        elif t.resp == "op":
            op = t.bad_op
        elif t.resp == "src":
            src = t.bad_src
        return dict(i_tlul_d_opcode=op & 7, i_tlul_d_source=src & SRC_MASK, i_tlul_d_error=err,
                    i_tlul_d_data=t.d_data)

    def step(self, s):
        b = self.b
        self._side()
        if b.in_reset:
            q = b.reset_noise
            if q is not None:
                b.drive(i_tlul_a_ready=q.getrandbits(1), i_tlul_d_valid=q.getrandbits(1),
                        i_tlul_d_opcode=q.getrandbits(3), i_tlul_d_data=q.getrandbits(32),
                        i_tlul_d_error=q.getrandbits(1), i_tlul_d_source=q.getrandbits(SRC_W))
            else:
                b.drive(i_tlul_a_ready=0, i_tlul_d_valid=0)
            self.a_ready_now = 0
            self.real_d = False
            return
        d = None
        if self.resp is not None and self.resp[0] == b.n:
            d = self.resp[1]
            self.resp[2].resp_n = b.n
            self.resp = None
        a_ready = 0
        if s["o_tlul_a_valid"] == 1:
            if self.presenting is None:
                t = b.req.cur
                assert t is not None, \
                    f"{b.chk}: o_tlul_a_valid=1 at cycle {b.n} with no APB transfer in progress"
                self.presenting = t
                self.first = tuple(s[f] for f in AFIELDS)
                self.wait = t.k
            t = self.presenting
            t.av_cycles.append(b.n)
            if tuple(s[f] for f in AFIELDS) != self.first:
                t.av_unstable = True
            if self.wait is None:
                pass
            elif self.wait > 0:
                self.wait -= 1
            else:
                a_ready = 1
                hs = {"n": b.n, "opcode": s["o_tlul_a_opcode"], "address": s["o_tlul_a_address"],
                      "data": s["o_tlul_a_data"], "source": s["o_tlul_a_source"]}
                t.hs.append(hs)
                self.presenting = None
                if t.j is None:
                    self.forever = True
                else:
                    f = self._resp_fields(t, hs)
                    if t.j == 0 and d is None:
                        d = f
                        t.resp_n = b.n
                    else:
                        self.resp = (b.n + max(1, t.j), f, t)
        else:
            self.presenting = None
            a_ready = self.idle_ready
        b.drive(i_tlul_a_ready=a_ready)
        if d is not None:
            b.drive(i_tlul_d_valid=1, **d)
        else:
            b.drive(i_tlul_d_valid=0)
        self.a_ready_now = a_ready
        self.real_d = d is not None


# --------------------------------------------------------------------------------------
# Bench: cycle engine, scoreboard, reset control
# --------------------------------------------------------------------------------------
class Bench:
    def __init__(self, dut, chk, q, keep_recs=True):
        self.dut = dut
        self.clk = dut.i_clk_core
        self.chk = chk
        self.r = q
        self.keep_recs = keep_recs
        self.inp = {}
        self.n = 0
        self.cur_rec = None
        self.trace = collections.deque(maxlen=512)
        self.in_reset = True
        self.score_q = []
        self.done = []
        self.post = {}
        self.capture = None
        self.reset_noise = None
        self.orphan_fn = None
        self.on_orphan = None
        self.orphans = []
        self.extra_check = None
        self.mon = Monitor()
        self.req = Requester(self)
        self.dev = Device(self)

    # ---- low level ----
    def drive(self, **kw):
        for name, v in kw.items():
            v = int(v)
            if self.inp.get(name) != v:
                self.inp[name] = v
                getattr(self.dut, name).value = v

    def sample(self):
        return {o: val(getattr(self.dut, o)) for o in OUTS}

    def rec_at(self, n):
        if not self.trace:
            return None
        i = n - self.trace[0]["n"]
        if 0 <= i < len(self.trace):
            return self.trace[i]
        return None

    def flush(self):
        self._finalize()

    def _finalize(self):
        r = self.cur_rec
        if r is None:
            return
        self.cur_rec = None
        for o in OUTS:
            assert r[o] is not None, f"{self.chk}: output {o} is X/Z at cycle {r['n']}"
        self.trace.append(r)
        self.mon.check(r)
        if self.capture is not None:
            self.capture.append(tuple(r[o] for o in OUTS))
        for fn in self.post.pop(r["n"], []):
            fn(r)
        if self.score_q:
            due = [t for t in self.score_q if t.pready_n + 1 <= r["n"]]
            for t in due:
                self.score_q.remove(t)
                self.score(t)

    def _orphan(self, s):
        if self.orphan_fn is None or self.in_reset:
            return
        res = self.orphan_fn(self, s)
        if not res:
            return
        cat, f = res
        if self.dev.real_d or self.dev.busy() or \
                (s["o_tlul_a_valid"] == 1 and self.dev.a_ready_now == 1):
            return  # would be a counted response, not an orphan
        self.drive(i_tlul_d_valid=1, **f)
        self.orphans.append((self.n, cat))
        if self.on_orphan is not None:
            self.on_orphan(self.n, cat)

    async def cycle(self):
        await FallingEdge(self.clk)
        self._finalize()
        self.n += 1
        s = self.sample()
        self.req.step(s)
        self.dev.step(s)
        self._orphan(s)
        rec = dict(s)
        rec.update(self.inp)
        rec["n"] = self.n
        self.cur_rec = rec
        return rec

    async def cycle_until(self, cond, max_cycles, what):
        for _ in range(max_cycles):
            await self.cycle()
            if cond():
                return self.cur_rec
        raise AssertionError(f"{self.chk}: timeout after {max_cycles} cycles waiting for {what}")

    async def idle(self, n):
        for _ in range(n):
            await self.cycle()

    # ---- reset control ----
    async def _release(self):
        await RisingEdge(self.clk)
        await Timer(1, unit="step")
        self.drive(i_rst_n_core=1)
        self.in_reset = False

    async def power_on(self, edges=5):
        for name, v in DEFAULT_INPUTS.items():
            self.inp[name] = v
            getattr(self.dut, name).value = v
        self.in_reset = True
        await RisingEdge(self.clk)
        await RisingEdge(self.clk)
        for _ in range(edges):
            await self.cycle()
        await self._release()

    async def assert_reset(self):
        """Assert reset now (mid-cycle, asynchronous) for bridge, requester and device."""
        self.in_reset = True
        self.req.reset()
        self.dev.reset()
        self.drive(i_rst_n_core=0, i_apb_psel=0, i_apb_penable=0, i_tlul_a_ready=0, i_tlul_d_valid=0)
        await Timer(1, unit="step")
        s = self.sample()
        if self.cur_rec is not None:
            self.cur_rec.update(s)
            self.cur_rec.update(self.inp)
        return s

    async def reset(self, edges=3):
        if not self.in_reset:
            await self.assert_reset()
        for _ in range(edges - 1):
            await self.cycle()
        await self._release()

    # ---- transfers ----
    async def run(self, transfers, max_cycles=None, tail=2):
        transfers = list(transfers)
        for t in transfers:
            self.req.queue.append(t)
        if max_cycles is None:
            max_cycles = sum((t.gap or 0) + 4 + (t.k or 0) + (t.j or 0) for t in transfers) + 50
        for _ in range(max_cycles):
            if not self.req.queue and self.req.cur is None:
                break
            await self.cycle()
        if self.req.queue or self.req.cur is not None:
            raise AssertionError(f"{self.chk}: transfers not all complete within {max_cycles} cycles "
                                 f"({len(self.req.queue)} still queued)")
        for _ in range(tail):
            await self.cycle()

    async def finish(self, cycles=3):
        for _ in range(cycles):
            await self.cycle()
        self._finalize()
        assert not self.score_q, f"{self.chk}: {len(self.score_q)} completions not scored"

    # ---- scoreboard ----
    def score(self, t):
        c = self.chk
        d = t.desc()
        e = ref_expect(t)
        if self.keep_recs:
            t.recs = {m: self.rec_at(t.setup_n + m) for m in range(0, t.access + 2)}
        assert t.access == e["access"], \
            f"{c}: {d}: expected o_apb_pready=1 first at E{e['access']} got it at E{t.access}"
        assert t.pslverr == e["pslverr"], f"{c}: {d}: expected o_apb_pslverr={e['pslverr']} got {t.pslverr}"
        assert t.prdata == e["prdata"], \
            f"{c}: {d}: expected o_apb_prdata=0x{e['prdata']:08x} got 0x{t.prdata:08x}"
        if e["legal"]:
            assert len(t.hs) == 1, f"{c}: {d}: expected exactly one A-channel handshake got {len(t.hs)}"
            h = t.hs[0]
            assert h["n"] == e["hs_n"], \
                f"{c}: {d}: expected handshake at E{1 + t.k} got E{h['n'] - t.setup_n}"
            assert h["opcode"] == e["opcode"], f"{c}: {d}: expected a_opcode={e['opcode']} got {h['opcode']}"
            assert h["address"] == e["address"], \
                f"{c}: {d}: expected a_address=0x{e['address']:x} got 0x{h['address']:x}"
            if t.write:
                assert h["data"] == t.wdata, \
                    f"{c}: {d}: expected a_data=0x{t.wdata:08x} got 0x{h['data']:08x}"
            exp_av = list(range(t.setup_n + 1, t.setup_n + 2 + t.k))
            assert t.av_cycles == exp_av, \
                f"{c}: {d}: expected o_tlul_a_valid=1 exactly at E1..E{1 + t.k} got at " \
                f"{[x - t.setup_n for x in t.av_cycles]}"
            assert not t.av_unstable, f"{c}: {d}: channel A changed while o_tlul_a_valid=1 and not accepted"
        else:
            assert not t.hs and not t.av_cycles, \
                f"{c}: {d}: illegal transfer expected no TL-UL request got a_valid at " \
                f"{[x - t.setup_n for x in t.av_cycles]}"
            r2 = self.rec_at(t.setup_n + 2)
            if r2 is not None and r2["i_rst_n_core"] == 1:
                assert r2["o_tlul_a_valid"] == 0, f"{c}: {d}: expected o_tlul_a_valid=0 at E2 got 1"
        if self.extra_check is not None:
            self.extra_check(t)
        self.done.append(t)


async def start(dut, chk, salt, keep_recs=True, edges=5):
    start_clock(dut)
    b = Bench(dut, chk, rng(salt), keep_recs)
    await b.power_on(edges)
    return b


def reset_value_errors(s):
    errs = [f"{o}={s[o]}" for o in RESET_ZERO if s[o] != 0]
    errs += [f"{o}={s[o]}" for o, v in CONSTS.items() if s[o] != v]
    return errs


def gen_random(q, illegal, proto):
    write = q.random() < 0.5
    addr = aligned(q)
    if illegal and q.random() < 0.25:
        addr |= q.randrange(1, 4)
    if write:
        strb = 0xF if (not illegal or q.random() < 0.7) else q.randrange(16)
    else:
        strb = 0 if q.random() < 0.4 else q.randrange(1, 16)
    k = 0 if q.random() < 0.4 else q.randrange(9)
    x = q.random()
    j = 0 if x < 0.15 else (1 if x < 0.5 else q.randrange(1, 8))
    resp, bad_op = "ok", None
    x = q.random()
    if x < 0.05:
        resp = "derr"
    elif proto and x < 0.10:
        resp = "op"
        good = 0 if write else 1
        bad_op = q.choice([v for v in range(8) if v != good])
    elif proto and x < 0.15:
        resp = "src"
    gap = q.choice([0, 0, 0, 1, 1, 2, 3, 4, 5])
    return Transfer(write, addr, q.getrandbits(32), strb, q.randrange(8), gap, k, j, resp, nz32(q), bad_op)


# ======================================================================================
# Tests
# ======================================================================================
@cocotb.test()
async def test_chk_018_local_error(dut):
    """CHK-018: unsupported PSTRB and misaligned address give a 1-cycle local error, no request."""
    b = await start(dut, "CHK-018", "chk018")
    q = b.r
    illegal = [Transfer(1, aligned(q), q.getrandbits(32), s, q.randrange(8), 2) for s in range(15)]
    for lo in (1, 2, 3):
        illegal.append(Transfer(0, aligned(q) | lo, q.getrandbits(32), q.randrange(16), q.randrange(8), 2))
        illegal.append(Transfer(1, aligned(q) | lo, q.getrandbits(32), 0xF, q.randrange(8), 2))
    seq, pairs = [], []
    for t in illegal:
        u = Transfer(1, aligned(q), q.getrandbits(32), 0xF, q.randrange(8), 0, 0, 1, "ok", nz32(q))
        seq += [t, u]
        pairs.append((t, u))
    await b.run(seq)
    await b.finish()
    for t, u in pairs:
        d = t.desc()
        r1, r2 = t.rec(1), t.rec(2)
        assert r1["o_apb_pready"] == 1 and r1["o_apb_pslverr"] == 1 and r1["o_apb_prdata"] == 0, \
            f"CHK-018: {d}: expected at E1 pready=1 pslverr=1 prdata=0 got pready={r1['o_apb_pready']} " \
            f"pslverr={r1['o_apb_pslverr']} prdata=0x{r1['o_apb_prdata']:08x}"
        assert r1["o_tlul_a_valid"] == 0 and r2["o_tlul_a_valid"] == 0, \
            f"CHK-018: {d}: expected o_tlul_a_valid=0 at E1 and E2 got {r1['o_tlul_a_valid']}/{r2['o_tlul_a_valid']}"
        assert not t.hs, f"CHK-018: {d}: expected no A-channel handshake got {len(t.hs)}"
        assert u.setup_n - t.setup_n == 2, \
            f"CHK-018: {d}: expected next Setup at E2 (interval 2) got interval {u.setup_n - t.setup_n}"
        assert u.rec(1)["o_tlul_a_valid"] == 1, f"CHK-018: following write expected o_tlul_a_valid=1 at E3"
        assert u.access == 3 and u.pslverr == 0, \
            f"CHK-018: following write expected pready at E5 with pslverr=0 got access={u.access} " \
            f"pslverr={u.pslverr}"


@cocotb.test()
async def test_chk_019_device_error(dut):
    """CHK-019: d_error=1 on read and write maps to PSLVERR=1, PRDATA=0; no stored error."""
    b = await start(dut, "CHK-019", "chk019")
    q = b.r
    seq, pairs = [], []
    for i in range(12):
        w = i % 2
        t = Transfer(w, aligned(q), q.getrandbits(32), 0xF if w else q.randrange(16), q.randrange(8),
                     1 + q.randrange(3), 0, 1, "derr", nz32(q))
        f = Transfer(0, aligned(q), 0, q.randrange(16), q.randrange(8), q.randrange(2), 0, 1, "ok", nz32(q))
        seq += [t, f]
        pairs.append((t, f))
    await b.run(seq)
    await b.finish()
    for t, f in pairs:
        r3 = t.rec(3)
        assert r3["o_apb_pready"] == 1 and r3["o_apb_pslverr"] == 1 and r3["o_apb_prdata"] == 0, \
            f"CHK-019: {t.desc()}: expected at E3 pready=1 pslverr=1 prdata=0 got {r3['o_apb_pready']}/" \
            f"{r3['o_apb_pslverr']}/0x{r3['o_apb_prdata']:08x}"
        assert f.pslverr == 0 and f.prdata == f.d_data, \
            f"CHK-019: read after error expected pslverr=0 prdata=0x{f.d_data:08x} got {f.pslverr}/" \
            f"0x{f.prdata:08x}"


@cocotb.test()
async def test_chk_020_wrong_opcode_source(dut):
    """CHK-020: wrong d_opcode or wrong d_source gives PSLVERR=1, PRDATA=0."""
    b = await start(dut, "CHK-020", "chk020")
    q = b.r
    bad = []
    for op in (0, 2, 3, 4, 5, 6, 7):
        bad.append(Transfer(0, aligned(q), 0, q.randrange(16), q.randrange(8), 2, 0, 1, "op", nz32(q), op))
    for op in (1, 2, 3, 4, 5, 6, 7):
        bad.append(Transfer(1, aligned(q), q.getrandbits(32), 0xF, q.randrange(8), 2, 0, 1, "op", nz32(q), op))
    for w in (0, 1, 0, 1):
        bad.append(Transfer(w, aligned(q), q.getrandbits(32), 0xF, q.randrange(8), 2, 0, 1, "src", nz32(q)))
    seq, pairs = [], []
    for t in bad:
        f = Transfer(0, aligned(q), 0, q.randrange(16), q.randrange(8), q.randrange(2), 0, 1, "ok", nz32(q))
        seq += [t, f]
        pairs.append((t, f))
    await b.run(seq)
    await b.finish()
    for t, f in pairs:
        r3 = t.rec(3)
        assert r3["o_apb_pready"] == 1 and r3["o_apb_pslverr"] == 1 and r3["o_apb_prdata"] == 0, \
            f"CHK-020: {t.desc()} bad_op={t.bad_op}: expected at E3 pready=1 pslverr=1 prdata=0 got " \
            f"{r3['o_apb_pready']}/{r3['o_apb_pslverr']}/0x{r3['o_apb_prdata']:08x}"
        assert f.pslverr == 0 and f.prdata == f.d_data, \
            f"CHK-020: correct read after {t.desc()} expected pslverr=0 prdata=0x{f.d_data:08x} got " \
            f"{f.pslverr}/0x{f.prdata:08x}"


@cocotb.test()
async def test_chk_021_orphan_responses(dut):
    """CHK-021: orphan d_valid pulses (idle, Setup, before acceptance, after PREADY) are discarded."""
    b = await start(dut, "CHK-021", "chk021")
    q = b.r
    oq = rng("chk021-orphan")

    def mk(w, tag=None, gap=2, k=0):
        return Transfer(w, aligned(q), q.getrandbits(32), 0xF if w else q.randrange(16), q.randrange(8),
                        gap, k, 1, "ok", nz32(q), tag=tag)

    seq = [mk(0, gap=1)]
    for i in range(4):
        w = i % 2
        seq.append(mk(w, "a", gap=6))
        seq.append(mk(0 if i < 2 else w, "b"))
        seq.append(mk(0 if i < 2 else w, "c", k=2))
        seq.append(mk(1 - w, "d"))
        seq.append(mk(0, gap=5))
        seq.append(mk(1, gap=0))
        seq.append(mk(0, gap=0))

    def ofn(bb, s):
        rq = bb.req
        t = rq.cur
        if rq.state == "setup" and t is not None and t.tag == "b":
            return ("setup", orphan_fields(oq, t.d_data))
        if rq.state == "access" and t is not None and t.tag == "c" and s["o_tlul_a_valid"] == 1 \
                and bb.dev.a_ready_now == 0:
            return ("before_acc", orphan_fields(oq, t.d_data))
        if t is None and rq.last is not None and rq.last.tag == "d" and rq.since_done <= 3:
            return ("after", orphan_fields(oq))
        if t is None and rq.queue and rq.queue[0].tag == "a" and rq.since_done >= 4:
            return ("idle", orphan_fields(oq))
        return None

    def on_orphan(n, cat):
        if cat not in ("idle", "after"):
            return

        def chk(r1, n=n, cat=cat):
            r0 = b.rec_at(n)
            assert r1["o_apb_pready"] == 0, \
                f"CHK-021: orphan ({cat}) at cycle {n}: expected o_apb_pready=0 at next edge got 1"
            assert r1["o_apb_prdata"] == r0["o_apb_prdata"] and r1["o_apb_pslverr"] == 0, \
                f"CHK-021: orphan ({cat}) at cycle {n}: expected prdata 0x{r0['o_apb_prdata']:08x} and " \
                f"pslverr 0 unchanged got 0x{r1['o_apb_prdata']:08x}/{r1['o_apb_pslverr']}"
        b.post.setdefault(n + 1, []).append(chk)

    b.orphan_fn = ofn
    b.on_orphan = on_orphan
    await b.run(seq)
    b.orphan_fn = None
    await b.finish()
    cats = collections.Counter(c for _, c in b.orphans)
    assert cats["idle"] >= 12 and cats["setup"] >= 4 and cats["before_acc"] >= 8 and cats["after"] >= 16, \
        f"CHK-021: expected orphans in all four timings got {dict(cats)}"
    for t in seq:
        if t.tag in ("b", "c"):
            e = ref_expect(t)
            assert t.access == e["access"] and t.pslverr == 0 and t.prdata == e["prdata"], \
                f"CHK-021: {t.desc()} with orphan: expected access {e['access']} pslverr 0 prdata " \
                f"0x{e['prdata']:08x} got {t.access}/{t.pslverr}/0x{t.prdata:08x}"
    assert len(b.done) == len(seq), f"CHK-021: expected {len(seq)} completions got {len(b.done)}"


@cocotb.test()
async def test_chk_022_no_response_no_timeout(dut):
    """CHK-022: device never responds / never accepts: requester waits; reset recovers."""
    b = await start(dut, "CHK-022", "chk022")
    q = b.r
    b.req.limit = 0
    # (1) read accepted, no response for 1000 cycles
    t = Transfer(0, aligned(q), 0, q.randrange(16), q.randrange(8), 1, 0, None, "ok", nz32(q))
    b.req.queue.append(t)
    await b.cycle_until(lambda: t.setup_n is not None, 20, "Setup of the read")
    for _ in range(1000):
        rec = await b.cycle()
        assert rec["o_apb_pready"] == 0, f"CHK-022: (1) expected o_apb_pready=0 at cycle {b.n} got 1"
        if b.n > t.setup_n + 1:
            assert rec["o_tlul_a_valid"] == 0, \
                f"CHK-022: (1) expected o_tlul_a_valid=0 after the handshake at cycle {b.n} got 1"
    assert len(t.hs) == 1 and t.hs[0]["n"] == t.setup_n + 1, \
        f"CHK-022: (1) expected one handshake at E1 got {[h['n'] - t.setup_n for h in t.hs]}"
    await b.reset(3)
    # (2) write never accepted for 1000 cycles
    t2 = Transfer(1, aligned(q), q.getrandbits(32), 0xF, q.randrange(8), 1, None, 1, "ok", nz32(q))
    b.req.queue.append(t2)
    await b.cycle_until(lambda: t2.setup_n is not None, 20, "Setup of the write")
    first = None
    for _ in range(1000):
        rec = await b.cycle()
        assert rec["o_apb_pready"] == 0, f"CHK-022: (2) expected o_apb_pready=0 at cycle {b.n} got 1"
        assert rec["o_tlul_a_valid"] == 1, f"CHK-022: (2) expected o_tlul_a_valid=1 at cycle {b.n} got 0"
        fields = tuple(rec[f] for f in AFIELDS)
        if first is None:
            first = fields
            assert rec["o_tlul_a_opcode"] == 0 and rec["o_tlul_a_address"] == t2.addr and \
                rec["o_tlul_a_data"] == t2.wdata, f"CHK-022: (2) wrong channel A contents {fields}"
        assert fields == first, f"CHK-022: (2) channel A changed at cycle {b.n}: {first} -> {fields}"
    assert not t2.hs, "CHK-022: (2) expected no handshake"
    await b.reset(3)
    b.req.limit = 300
    t3 = Transfer(1, aligned(q), q.getrandbits(32), 0xF, q.randrange(8), 1, 0, 1, "ok", nz32(q))
    await b.run([t3])
    await b.finish()
    assert t3.access == 3 and t3.pslverr == 0, \
        f"CHK-022: write after reset expected pready at E3 pslverr=0 got access={t3.access} " \
        f"pslverr={t3.pslverr}"


@cocotb.test()
async def test_chk_023_prompt_write(dut):
    """CHK-023: aligned full-strobe write to a prompt device: PutFullData, 3 Access cycles."""
    b = await start(dut, "CHK-023", "chk023")
    q = b.r
    addrs = [0, AMASK & ~3] + [aligned(q) for _ in range(18)]
    seq = [Transfer(1, a, q.getrandbits(32), 0xF, q.randrange(8), 1 + q.randrange(3), 0, 1, "ok", q.getrandbits(32))
           for a in addrs]
    await b.run(seq)
    await b.finish()
    for t in seq:
        d = t.desc()
        r1, r2, r3 = t.rec(1), t.rec(2), t.rec(3)
        exp = dict(o_tlul_a_valid=1, o_tlul_a_opcode=0, o_tlul_a_size=2, o_tlul_a_mask=0xF,
                   o_tlul_a_address=t.addr, o_tlul_a_data=t.wdata, o_tlul_d_ready=1, o_apb_pready=0)
        for o, v in exp.items():
            assert r1[o] == v, f"CHK-023: {d}: expected {o}={v:#x} at E1 got {r1[o]:#x}"
        assert len(t.hs) == 1 and t.hs[0]["n"] == t.setup_n + 1, \
            f"CHK-023: {d}: expected one handshake at E1 got {[h['n'] - t.setup_n for h in t.hs]}"
        assert r2["o_tlul_a_valid"] == 0 and r2["o_apb_pready"] == 0, \
            f"CHK-023: {d}: expected a_valid=0 pready=0 at E2 got {r2['o_tlul_a_valid']}/{r2['o_apb_pready']}"
        assert r3["o_apb_pready"] == 1 and r3["o_apb_pslverr"] == 0 and r3["o_apb_prdata"] == 0, \
            f"CHK-023: {d}: expected pready=1 pslverr=0 prdata=0 at E3 got {r3['o_apb_pready']}/" \
            f"{r3['o_apb_pslverr']}/0x{r3['o_apb_prdata']:08x}"


@cocotb.test()
async def test_chk_024_prompt_read(dut):
    """CHK-024: aligned read to a prompt device gives Get, PRDATA=d_data, PSTRB ignored."""
    b = await start(dut, "CHK-024", "chk024")
    q = b.r
    strbs = list(range(16)) + [q.randrange(16) for _ in range(16)]
    seq = [Transfer(0, aligned(q), q.getrandbits(32), s, q.randrange(8), q.randrange(3), 0, 1, "ok", q.getrandbits(32))
           for s in strbs]
    await b.run(seq)
    await b.finish()
    for t in seq:
        d = t.desc()
        r1, r2, r3 = t.rec(1), t.rec(2), t.rec(3)
        exp = dict(o_tlul_a_valid=1, o_tlul_a_opcode=4, o_tlul_a_size=2, o_tlul_a_mask=0xF,
                   o_tlul_a_address=t.addr, o_apb_pready=0)
        for o, v in exp.items():
            assert r1[o] == v, f"CHK-024: {d}: expected {o}={v:#x} at E1 got {r1[o]:#x}"
        assert len(t.hs) == 1, f"CHK-024: {d}: expected exactly one handshake got {len(t.hs)}"
        assert r2["o_apb_pready"] == 0, f"CHK-024: {d}: expected o_apb_pready=0 at E2 got 1"
        assert r3["o_apb_pready"] == 1 and r3["o_apb_pslverr"] == 0 and r3["o_apb_prdata"] == t.d_data, \
            f"CHK-024: {d}: expected at E3 pready=1 pslverr=0 prdata=0x{t.d_data:08x} got " \
            f"{r3['o_apb_pready']}/{r3['o_apb_pslverr']}/0x{r3['o_apb_prdata']:08x}"


def _seq025(prot):
    q = rng("chk025-seq")
    A = lambda: aligned(q)  # noqa: E731
    return [
        Transfer(1, A(), q.getrandbits(32), 0xF, prot, 2, 0, 1, "ok", nz32(q)),
        Transfer(0, A(), 0, 0x0, prot, 1, 0, 1, "ok", nz32(q)),
        Transfer(1, A(), q.getrandbits(32), 0x3, prot, 0, 0, 1, "ok", nz32(q)),      # illegal strobe
        Transfer(0, A(), 0, 0x5, prot, 1, 2, 3, "ok", nz32(q)),
        Transfer(0, A() | 1, 0, 0x0, prot, 0, 0, 1, "ok", nz32(q)),                  # misaligned
        Transfer(1, A(), q.getrandbits(32), 0xF, prot, 2, 1, 0, "ok", nz32(q)),
        Transfer(0, A(), 0, 0x0, prot, 0, 0, 1, "derr", nz32(q)),                    # d_error
        Transfer(1, A(), q.getrandbits(32), 0xF, prot, 1, 0, 2, "ok", nz32(q)),
        Transfer(0, A(), 0, 0xF, prot, 3, 0, 0, "ok", nz32(q)),
        Transfer(1, A(), q.getrandbits(32), 0xF, prot, 0, 3, 1, "ok", nz32(q)),
        Transfer(0, A(), 0, 0x0, prot, 0, 0, 1, "ok", nz32(q)),
        Transfer(1, A(), q.getrandbits(32), 0xF, prot, 0, 0, 1, "ok", nz32(q)),
    ]


@cocotb.test()
async def test_chk_025_ignored_inputs(dut):
    """CHK-025: PPROT, d_param, d_size, d_sink and d_user have no effect on any output."""
    b = await start(dut, "CHK-025", "chk025")
    traces = []
    for prot in range(8):
        if prot:
            await b.reset(3)
        b.dev.side_rng = rng(f"chk025-side-{prot}")
        b.capture = []
        seq = _seq025(prot)
        await b.run(seq)
        await b.idle(2)
        traces.append(b.capture)
        b.capture = None
        for t in seq:
            assert t.pready_n is not None, f"CHK-025: prot={prot}: {t.desc()} did not complete"
    await b.finish()
    ref = traces[0]
    for prot in range(1, 8):
        tr = traces[prot]
        assert len(tr) == len(ref), \
            f"CHK-025: expected {len(ref)} cycles with pprot={prot} as with pprot=0 got {len(tr)}"
        for i, (x, y) in enumerate(zip(ref, tr)):
            if x != y:
                diff = [f"{OUTS[m]}: {x[m]:#x} vs {y[m]:#x}" for m in range(len(OUTS)) if x[m] != y[m]]
                assert False, f"CHK-025: expected identical outputs, pprot={prot} differs at cycle {i}: {diff}"


@cocotb.test()
async def test_chk_026_backpressure_delay(dut):
    """CHK-026: a_ready delays 0..8 and response delays 1..7: channel A stable, Access = 2+k+j."""
    b = await start(dut, "CHK-026", "chk026")
    q = b.r
    seq = []
    for i in range(63):
        k, j = i % 9, 1 + (i // 9) % 7
        w = q.random() < 0.5
        seq.append(Transfer(w, aligned(q), q.getrandbits(32), 0xF if w else q.randrange(16), q.randrange(8),
                            q.randrange(3), k, j, "ok", nz32(q)))
    for _ in range(30):
        w = q.random() < 0.5
        seq.append(Transfer(w, aligned(q), q.getrandbits(32), 0xF if w else q.randrange(16), q.randrange(8),
                            q.randrange(3), q.randrange(9), q.randrange(1, 8), "ok", nz32(q)))
    q.shuffle(seq)
    await b.run(seq)
    await b.finish()
    for t in seq:
        d = t.desc()
        k, j = t.k, t.j
        r1 = t.rec(1)
        for m in range(1, 2 + k):
            rm = t.rec(m)
            assert rm["o_tlul_a_valid"] == 1, f"CHK-026: {d}: expected o_tlul_a_valid=1 at E{m} got 0"
            for f in ("o_tlul_a_opcode", "o_tlul_a_address", "o_tlul_a_data"):
                assert rm[f] == r1[f], f"CHK-026: {d}: {f} changed at E{m}: {r1[f]:#x} -> {rm[f]:#x}"
        assert t.rec(2 + k)["o_tlul_a_valid"] == 0, f"CHK-026: {d}: expected o_tlul_a_valid=0 at E{2 + k}"
        assert len(t.hs) == 1 and t.hs[0]["n"] == t.setup_n + 1 + k, \
            f"CHK-026: {d}: expected one handshake at E{1 + k} got {[h['n'] - t.setup_n for h in t.hs]}"
        for m in range(1, 2 + k + j):
            assert t.rec(m)["o_apb_pready"] == 0, f"CHK-026: {d}: expected o_apb_pready=0 at E{m} got 1"
        assert t.rec(2 + k + j)["o_apb_pready"] == 1, f"CHK-026: {d}: expected o_apb_pready=1 at E{2 + k + j}"
        exp_prd = 0 if t.write else t.d_data
        assert t.pslverr == 0 and t.prdata == exp_prd, \
            f"CHK-026: {d}: expected pslverr=0 prdata=0x{exp_prd:08x} got {t.pslverr}/0x{t.prdata:08x}"


@cocotb.test()
async def test_chk_027_same_cycle_response(dut):
    """CHK-027: response in the acceptance cycle gives a 2-cycle Access phase (plus a_ready delay)."""
    b = await start(dut, "CHK-027", "chk027")
    q = b.r
    seq = []
    for k in (0, 1, 3):
        for w in (0, 1):
            for _ in range(3):
                seq.append(Transfer(w, aligned(q), q.getrandbits(32), 0xF if w else q.randrange(16),
                                    q.randrange(8), q.randrange(3), k, 0, "ok", nz32(q)))
    await b.run(seq)
    await b.finish()
    for t in seq:
        d = t.desc()
        k = t.k
        assert len(t.hs) == 1 and t.hs[0]["n"] == t.setup_n + 1 + k and t.resp_n == t.setup_n + 1 + k, \
            f"CHK-027: {d}: expected handshake and response at E{1 + k}"
        assert t.rec(1 + k)["o_apb_pready"] == 0, f"CHK-027: {d}: expected o_apb_pready=0 at E{1 + k}"
        r = t.rec(2 + k)
        assert r["o_apb_pready"] == 1 and r["o_tlul_a_valid"] == 0, \
            f"CHK-027: {d}: expected pready=1 and a_valid=0 at E{2 + k} got {r['o_apb_pready']}/" \
            f"{r['o_tlul_a_valid']}"
        exp_prd = 0 if t.write else t.d_data
        assert t.access == 2 + k and t.pslverr == 0 and t.prdata == exp_prd, \
            f"CHK-027: {d}: expected access {2 + k} pslverr 0 prdata 0x{exp_prd:08x} got {t.access}/" \
            f"{t.pslverr}/0x{t.prdata:08x}"


@cocotb.test()
async def test_chk_028_back_to_back(dut):
    """CHK-028: back-to-back pairs of all kinds with PSEL held high and with 1 and 5 idle cycles."""
    b = await start(dut, "CHK-028", "chk028")
    q = b.r
    kinds = ("W", "R", "ILS", "MIS")
    modes = {"prompt": (0, 1, "ok"), "same": (0, 0, "ok"), "derr": (0, 1, "derr")}

    def mk(kind, mode, gap):
        k, j, resp = modes[mode]
        if kind == "W":
            return Transfer(1, aligned(q), q.getrandbits(32), 0xF, q.randrange(8), gap, k, j, resp, nz32(q))
        if kind == "R":
            return Transfer(0, aligned(q), 0, q.randrange(16), q.randrange(8), gap, k, j, resp, nz32(q))
        if kind == "ILS":
            return Transfer(1, aligned(q), q.getrandbits(32), 0x5, q.randrange(8), gap, k, j, resp, nz32(q))
        w = q.getrandbits(1)
        return Transfer(w, aligned(q) | 2, q.getrandbits(32), 0xF if w else q.randrange(16), q.randrange(8),
                        gap, k, j, resp, nz32(q))

    seq, pairs = [], []
    for mode in modes:
        for g in (0, 1, 5):
            for k1 in kinds:
                for k2 in kinds:
                    t1, t2 = mk(k1, mode, 3), mk(k2, mode, g)
                    seq += [t1, t2]
                    pairs.append((mode, g, t1, t2))
    await b.run(seq)
    await b.finish()
    for mode, g, t1, t2 in pairs:
        tag = f"mode={mode} gap={g} {t1.kind()}->{t2.kind()}"
        base = 2 if not t1.legal() else (3 if mode == "same" else 4)
        got = t2.setup_n - t1.setup_n
        assert got == base + g, f"CHK-028: {tag}: expected Setup-to-Setup interval {base + g} got {got}"
        r1 = t2.rec(1)
        if t2.legal():
            assert r1["o_tlul_a_valid"] == 1, f"CHK-028: {tag}: expected o_tlul_a_valid=1 after 2nd Setup"
        else:
            assert r1["o_apb_pready"] == 1 and r1["o_apb_pslverr"] == 1 and r1["o_tlul_a_valid"] == 0, \
                f"CHK-028: {tag}: expected local error completion after 2nd Setup"
        for t in (t1, t2):
            if not t.legal():
                assert not t.av_cycles, f"CHK-028: {tag}: illegal {t.desc()} produced o_tlul_a_valid=1"
        assert t1.pready_n < t2.setup_n, f"CHK-028: {tag}: completions out of order"


@cocotb.test()
async def test_chk_029_random_scoreboard(dut):
    """CHK-029: 10000 constrained-random transfers with errors, orphans, scoreboard and coverage."""
    b = await start(dut, "CHK-029", "chk029", keep_recs=False)
    dut._log.info(f"CHK-029 seed: NNC_SEED={os.environ.get('NNC_SEED', '<unset>')}")
    q = b.r
    oq = rng("chk029-orphan")
    N = 10000
    seq = [gen_random(q, True, True) for _ in range(N)]

    def ofn(bb, s):
        if oq.random() >= 0.05:
            return None
        rq = bb.req
        if rq.state == "setup":
            cat = "setup"
        elif rq.state == "access":
            if s["o_tlul_a_valid"] == 1 and bb.dev.a_ready_now == 0:
                cat = "before_acc"
            else:
                return None
        elif rq.since_done <= 3:
            cat = "after"
        else:
            cat = "idle"
        return cat, orphan_fields(oq)

    b.orphan_fn = ofn
    await b.run(seq)
    b.orphan_fn = None
    await b.finish()
    assert len(b.done) == N, f"CHK-029: expected {N} scored completions got {len(b.done)}"
    wstrb, rd_z, rd_nz = set(), False, False
    errs, kset, jset, pairs = set(), set(), set(), set()
    for t in b.done:
        rw = "W" if t.write else "R"
        if t.write:
            wstrb.add(t.strb)
        elif t.strb == 0:
            rd_z = True
        else:
            rd_nz = True
        if t.addr & 3:
            errs.add(("mis", rw))
        elif t.write and t.strb != 0xF:
            errs.add(("strb", "W"))
        else:
            kset.add(t.k)
            jset.add(t.j)
            if t.resp != "ok":
                errs.add((t.resp, rw))
        if t.b2b_prev is not None:
            pairs.add((t.b2b_prev.kind(), t.kind()))
    assert wstrb == set(range(16)), f"CHK-029: COV-001 write PSTRB bins missing {set(range(16)) - wstrb}"
    assert rd_z and rd_nz, "CHK-029: COV-001 read PSTRB zero/non-zero bins missing"
    need = {(e, rw) for e in ("derr", "op", "src", "mis") for rw in ("R", "W")} | {("strb", "W")}
    assert need <= errs, f"CHK-029: COV-002 error bins missing {need - errs}"
    assert kset >= set(range(9)), f"CHK-029: a_ready wait bins missing {set(range(9)) - kset}"
    assert jset >= set(range(8)), f"CHK-029: d_valid delay bins missing {set(range(8)) - jset}"
    ocats = {c for _, c in b.orphans}
    assert ocats >= {"idle", "setup", "before_acc", "after"}, f"CHK-029: orphan timing bins hit {ocats}"
    kinds = ("W", "R", "ILS", "MIS")
    allp = {(x, y) for x in kinds for y in kinds}
    assert allp <= pairs, f"CHK-029: back-to-back pair bins missing {allp - pairs}"


@cocotb.test()
async def test_chk_030_reset(dut):
    """CHK-030: reset values, d_ready release timing, asynchronous assertion, idle after reset."""
    start_clock(dut)
    c = "CHK-030"
    b = Bench(dut, c, rng("chk030"))
    b.trace = collections.deque(maxlen=4096)
    q = b.r
    b.reset_noise = rng("chk030-noise")
    await b.power_on(edges=6)
    b.reset_noise = None
    b.flush()
    rst_recs = [r for r in b.trace if r["i_rst_n_core"] == 0]
    assert len(rst_recs) >= 5, f"{c}: expected at least 5 reset edges got {len(rst_recs)}"
    for r in rst_recs:
        e = reset_value_errors(r)
        assert not e, f"{c}: expected reset values in reset (cycle {r['n']}) got {e}"

    async def after_release(nidle):
        for i in range(nidle):
            rec = await b.cycle()
            exp_dr = 0 if i == 0 else 1
            assert rec["o_tlul_d_ready"] == exp_dr, \
                f"{c}: expected o_tlul_d_ready={exp_dr} at edge {i + 1} after release got {rec['o_tlul_d_ready']}"
            assert rec["o_apb_pready"] == 0 and rec["o_tlul_a_valid"] == 0, \
                f"{c}: expected pready=0 a_valid=0 while idle after release"

    await after_release(5)
    # step 3
    t1 = Transfer(1, aligned(q), q.getrandbits(32), 0xF, q.randrange(8), 0, 0, 1, "ok", nz32(q))
    await b.run([t1])
    assert t1.access == 3 and t1.pslverr == 0, f"{c}: step 3 write expected pready at E3 got E{t1.access}"
    # step 4: asynchronous reset in A1
    t2 = Transfer(1, aligned(q), q.getrandbits(32), 0xF, q.randrange(8), 1, 3, 1, "ok", nz32(q))
    b.req.queue.append(t2)
    await b.cycle_until(lambda: t2.setup_n is not None and b.n == t2.setup_n + 1, 30, "A1 of the second write")
    assert b.cur_rec["o_tlul_a_valid"] == 1, f"{c}: expected o_tlul_a_valid=1 in A1 of step 4"
    s = await b.assert_reset()
    e = reset_value_errors(s)
    assert not e, f"{c}: step 4: expected reset values 1 time unit after mid-cycle reset got {e}"
    await b.reset(3)
    await after_release(3)
    # step 5: asynchronous reset in the PREADY cycle
    t3 = Transfer(1, aligned(q), q.getrandbits(32), 0xF, q.randrange(8), 1, 0, 1, "ok", nz32(q))
    b.req.queue.append(t3)
    await b.cycle_until(lambda: t3.setup_n is not None and b.cur_rec["o_apb_pready"] == 1, 30,
                        "PREADY of the third write")
    assert b.n == t3.setup_n + 3, f"{c}: step 5 write expected pready at E3 got E{b.n - t3.setup_n}"
    s = await b.assert_reset()
    e = reset_value_errors(s)
    assert not e, f"{c}: step 5: expected reset values 1 time unit after mid-cycle reset got {e}"
    # step 6
    await b.reset(3)
    await after_release(4)
    t4 = Transfer(1, aligned(q), q.getrandbits(32), 0xF, q.randrange(8), 0, 0, 1, "ok", nz32(q))
    await b.run([t4])
    await b.finish()
    assert t4.access == 3 and t4.pslverr == 0, f"{c}: write after reset expected pready at E3 got E{t4.access}"
    assert t2.abandoned and t3.abandoned, f"{c}: transfers interrupted by reset expected abandoned"


@cocotb.test()
async def test_chk_031_reset_abandons_transfer(dut):
    """CHK-031: reset in A1, A2 or A3 abandons the transfer; stale d_valid ignored; next transfers OK."""
    b = await start(dut, "CHK-031", "chk031")
    c = "CHK-031"
    q = b.r
    for write in (1, 0):
        for phase in ("a", "b", "c"):
            tag = f"{'write' if write else 'read'} reset in A{ {'a': 1, 'b': 2, 'c': 3}[phase] }"
            t = Transfer(write, aligned(q), q.getrandbits(32), 0xF if write else q.randrange(16),
                         q.randrange(8), 2, 3 if phase == "a" else 0, 4 if phase == "b" else 1, "ok", nz32(q))
            off = {"a": 1, "b": 2, "c": 3}[phase]
            b.req.queue.append(t)
            await b.cycle_until(lambda: t.setup_n is not None and b.n == t.setup_n + off, 30, tag)
            rec = b.cur_rec
            if phase == "a":
                assert rec["o_tlul_a_valid"] == 1 and b.dev.a_ready_now == 0, f"{c}: {tag}: not in A1 wait"
            elif phase == "b":
                assert len(t.hs) == 1 and t.resp_n is None and rec["o_tlul_a_valid"] == 0, \
                    f"{c}: {tag}: expected accepted request without response"
            else:
                assert rec["o_apb_pready"] == 1, f"{c}: {tag}: expected o_apb_pready=1 in A3"
            await b.assert_reset()
            await b.reset(3)
            stale_n = b.n + 2
            stale_op = 0 if write else 1
            b.orphan_fn = lambda bb, s: ("stale", dict(
                i_tlul_d_opcode=stale_op, i_tlul_d_source=SRC_ID & SRC_MASK, i_tlul_d_error=0,
                i_tlul_d_data=nz32(q))) if bb.n == stale_n else None
            for _ in range(10):
                rec = await b.cycle()
                assert rec["o_apb_pready"] == 0 and rec["o_apb_pslverr"] == 0 and rec["o_apb_prdata"] == 0 \
                    and rec["o_tlul_a_valid"] == 0, \
                    f"{c}: {tag}: expected pready=0 pslverr=0 prdata=0 a_valid=0 after release at cycle {b.n} " \
                    f"got {rec['o_apb_pready']}/{rec['o_apb_pslverr']}/0x{rec['o_apb_prdata']:x}/" \
                    f"{rec['o_tlul_a_valid']}"
            b.orphan_fn = None
            assert any(n == stale_n for n, _ in b.orphans), f"{c}: {tag}: stale d_valid was not driven"
            assert t.abandoned, f"{c}: {tag}: expected the transfer to be abandoned"
            w = Transfer(1, aligned(q), q.getrandbits(32), 0xF, q.randrange(8), 0, 0, 1, "ok", nz32(q))
            r = Transfer(0, aligned(q), 0, q.randrange(16), q.randrange(8), 1, 0, 1, "ok", nz32(q))
            await b.run([w, r])
            assert w.access == 3 and w.pslverr == 0 and len(w.hs) == 1 and w.hs[0]["address"] == w.addr \
                and w.hs[0]["data"] == w.wdata and w.hs[0]["opcode"] == 0, \
                f"{c}: {tag}: write after reset expected PutFullData and pready at E3 got access={w.access}"
            assert r.access == 3 and r.pslverr == 0 and r.prdata == r.d_data and len(r.hs) == 1 \
                and r.hs[0]["opcode"] == 4, \
                f"{c}: {tag}: read after reset expected Get and prdata=0x{r.d_data:08x} at E3 got " \
                f"access={r.access} prdata=0x{(r.prdata or 0):08x}"
    await b.finish()


@cocotb.test()
async def test_regression_random(dut):
    """CHK-001..CHK-017: legal random regression (reads/writes, d_error, random a_ready and
    d_valid delays, same-cycle responses, back-to-back with PSEL held and with gaps), checked by
    the port monitor and the reference-model scoreboard."""
    b = await start(dut, "CHK-029", "regression", keep_recs=False)
    q = b.r
    N = 3000
    seq = [gen_random(q, False, False) for _ in range(N)]
    await b.run(seq)
    await b.finish()
    assert len(b.done) == N, f"CHK-029: expected {N} completions got {len(b.done)}"
    assert all(t.legal() for t in seq), "CHK-029: regression must contain only legal transfers"

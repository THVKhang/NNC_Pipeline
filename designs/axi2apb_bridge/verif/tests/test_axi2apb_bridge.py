"""cocotb 2.1 testbench for m_axi2apb_bridge.

Covers CHK-018 .. CHK-031 and adds a random regression that exercises the
assertion checks CHK-001 .. CHK-017.

Timing model: a single scheduler coroutine drives every input right after each
falling edge. It then waits for ReadOnly and samples every port. That sample
holds the values the next rising edge ("edge e") will see. A transaction
tracker (the CHK-014 tracker) and a scoreboard with an independent
byte-addressed reference model work on these per-edge samples.
"""
import os
from collections import deque

import cocotb
from cocotb.triggers import FallingEdge, ReadOnly

from nnc_cocotb import *  # noqa: F401,F403

# --------------------------------------------------------------------------
# Constants (AXI4 / APB4 encodings from the plan assumptions)
# --------------------------------------------------------------------------
OKAY, SLVERR = 0, 2
FIXED, INCR, WRAP = 0, 1, 2
MAP_LO, MAP_HI = 0x0000_0000, 0x0000_FFFF      # memory-model region of the TB APB fabric
UNMAPPED_BASE = 0x8000_0000
MAX_SIM_CYCLES = 20_000_000

SIG = {
    "rst": "i_rst_n_axi",
    "awid": "i_axi_awid", "awaddr": "i_axi_awaddr", "awlen": "i_axi_awlen",
    "awsize": "i_axi_awsize", "awburst": "i_axi_awburst", "awcache": "i_axi_awcache",
    "awprot": "i_axi_awprot", "awvalid": "i_axi_awvalid", "awready": "o_axi_awready",
    "wdata": "i_axi_wdata", "wstrb": "i_axi_wstrb", "wlast": "i_axi_wlast",
    "wvalid": "i_axi_wvalid", "wready": "o_axi_wready",
    "bid": "o_axi_bid", "bresp": "o_axi_bresp", "bvalid": "o_axi_bvalid", "bready": "i_axi_bready",
    "arid": "i_axi_arid", "araddr": "i_axi_araddr", "arlen": "i_axi_arlen",
    "arsize": "i_axi_arsize", "arburst": "i_axi_arburst", "arcache": "i_axi_arcache",
    "arprot": "i_axi_arprot", "arvalid": "i_axi_arvalid", "arready": "o_axi_arready",
    "rid": "o_axi_rid", "rdata": "o_axi_rdata", "rresp": "o_axi_rresp", "rlast": "o_axi_rlast",
    "rvalid": "o_axi_rvalid", "rready": "i_axi_rready",
    "paddr": "o_apb_paddr", "pwrite": "o_apb_pwrite", "pwdata": "o_apb_pwdata",
    "pstrb": "o_apb_pstrb", "pprot": "o_apb_pprot", "psel": "o_apb_psel",
    "penable": "o_apb_penable", "pready": "i_apb_pready", "prdata": "i_apb_prdata",
    "pslverr": "i_apb_pslverr",
}
APB_PAY = ("paddr", "pwrite", "pwdata", "pstrb", "pprot")
RESET_ZERO = ("bvalid", "rvalid", "bid", "bresp", "rid", "rdata", "rresp", "rlast",
              "psel", "penable", "paddr", "pwrite", "pwdata", "pstrb", "pprot")


def _v(h):
    x = val(h)
    return -1 if x is None else int(x)


def id_width():
    try:
        return int(PARAMS.get("PARA_AXI_ID_W", 4))
    except Exception:
        return 4


def is_mapped(a):
    return MAP_LO <= a <= MAP_HI


# --------------------------------------------------------------------------
# Reference model functions (from the specification text only)
# --------------------------------------------------------------------------
def classify(addr, ln, size, burst, cache):
    """CHK-014 classification: True = supported."""
    if size > 2 or size < 0:
        return False
    if burst == 3:
        return False
    if cache not in (0, 1):
        return False
    if burst == INCR:
        s = 1 << size
        end = (addr & ~(s - 1)) + (ln + 1) * s - 1
        if (addr >> 12) != (end >> 12):
            return False
    return True


def beat_addrs(addr, ln, size, burst):
    """CHK-016 beat-address formula."""
    s = 1 << max(0, size)
    out = []
    for k in range(ln + 1):
        if burst == FIXED:
            a = addr
        elif burst == INCR:
            a = addr if k == 0 else (addr & ~(s - 1)) + k * s
        else:
            t = s * (ln + 1)
            lower = (addr // t) * t
            a = lower + ((addr - lower + k * s) % t)
        out.append(a & 0xFFFFFFFF)
    return out


def legal_lanes(a, size):
    s = 1 << size
    top = (a & ~(s - 1)) + s - 1
    m = 0
    for byte in range(a, top + 1):
        m |= 1 << (byte % 4)
    return m & 0xF


def default_strobes(addr, ln, size, burst):
    return [legal_lanes(a, size) for a in beat_addrs(addr, ln, size, burst)]


def init_byte(a):
    a &= 0xFFFFFFFF
    return ((a * 0x9E3779B1) >> 11) & 0xFF


class ByteMem:
    def __init__(self):
        self.d = {}

    def rd8(self, a):
        return self.d.get(a, init_byte(a))

    def read_word(self, wa):
        wa &= 0xFFFFFFFC
        return sum(self.rd8(wa + i) << (8 * i) for i in range(4))

    def write_word(self, wa, data, strb):
        wa &= 0xFFFFFFFC
        for i in range(4):
            if (strb >> i) & 1:
                self.d[wa + i] = (data >> (8 * i)) & 0xFF


# --------------------------------------------------------------------------
# APB completer / memory model
# --------------------------------------------------------------------------
class ApbCompleter:
    """APB4 completer. Memory in MAP_LO..MAP_HI. Any other PADDR is handled by a
    default completer that answers PREADY=1 in the first ACCESS cycle with PSLVERR=1."""

    def __init__(self, bench):
        self.b = bench
        self.mem = ByteMem()
        self.wait_fn = lambda x: 0
        self.err_fn = lambda x: False
        self.read_fn = None
        self.err_data = 0xDEADBEEF
        self.unmapped_data = 0xFFFFFFFF
        self.garbage = True
        self.seq = 0
        self.cur = None
        self.left = 0
        self.log = []

    def drive(self, e):
        b = self.b
        d = b.dut
        rnd = b.rnd
        psel = _v(d.o_apb_psel)
        pen = _v(d.o_apb_penable)
        pready = 0
        prdata = rnd.getrandbits(32) if self.garbage else 0
        pslverr = rnd.getrandbits(1) if self.garbage else 0
        if b.rst_now == 1 and psel == 1 and pen == 1:
            if self.cur is None:
                x = {k: _v(b.h[k]) for k in APB_PAY}
                x["seq"] = self.seq
                self.seq += 1
                x["mapped"] = is_mapped(x["paddr"])
                self.left = max(0, int(self.wait_fn(x))) if x["mapped"] else 0
                x["waits"] = self.left
                self.cur = x
            if self.left > 0:
                self.left -= 1
            else:
                x = self.cur
                self.cur = None
                pready = 1
                pslverr = 0
                prdata = 0
                if not x["mapped"]:
                    pslverr = 1
                    if x["pwrite"] != 1:
                        prdata = self.unmapped_data
                elif self.err_fn(x):
                    pslverr = 1
                    if x["pwrite"] != 1:
                        prdata = self.err_data
                elif x["pwrite"] == 1:
                    self.mem.write_word(x["paddr"], x["pwdata"], x["pstrb"])
                else:
                    prdata = self.read_fn(x) if self.read_fn else self.mem.read_word(x["paddr"])
                x["pslverr"] = pslverr
                x["prdata"] = prdata
                self.log.append(x)
        else:
            self.cur = None
            self.left = 0
            if psel != 1 and self.garbage:
                pready = rnd.getrandbits(1)
        d.i_apb_pready.value = pready
        d.i_apb_prdata.value = prdata & 0xFFFFFFFF
        d.i_apb_pslverr.value = pslverr


# --------------------------------------------------------------------------
# AXI requester models
# --------------------------------------------------------------------------
class ReadReq:
    kind = "R"

    def __init__(self, id, addr, ln, size, burst, cache, prot, not_before, gap):
        self.id, self.addr, self.len, self.size = id, addr, ln, size
        self.burst, self.cache, self.prot = burst, cache, prot
        self.not_before, self.gap = not_before, gap
        self.hs_edge = None
        self.first_valid = None
        self.aborted = False


class WriteReq:
    kind = "W"

    def __init__(self, id, addr, ln, size, burst, cache, prot, data, strb, w_early,
                 aw_not_before, w_not_before, gap, wgap, w_stop_after):
        self.id, self.addr, self.len, self.size = id, addr, ln, size
        self.burst, self.cache, self.prot = burst, cache, prot
        self.data, self.strb = list(data), list(strb)
        self.w_early = w_early
        self.not_before, self.w_not_before, self.gap = aw_not_before, w_not_before, gap
        self.wgap, self.w_stop_after = wgap, w_stop_after
        self.hs_edge = None
        self.first_valid = None
        self.w_first_valid = None
        self.w_edges = []
        self.w_idx = 0
        self.aborted = False


class ReadMaster:
    def __init__(self, bench):
        self.b = bench
        self.q = deque()
        self.cur = None
        self.gap_left = None
        self.rready_delay = lambda: 0
        self.rready_idle = lambda: 1
        self.r_cnt = None
        self.reqs = []

    def req(self, addr, ln=0, size=2, burst=INCR, cache=0, prot=0, id=None, not_before=0, gap=0):
        b = self.b
        if id is None:
            id = b.rnd.getrandbits(b.idw)
        r = ReadReq(id & b.idmask, addr & 0xFFFFFFFF, ln, size, burst, cache, prot, not_before, gap)
        self.q.append(r)
        self.reqs.append(r)
        return r

    def busy(self):
        return self.cur is not None or bool(self.q)

    def flush(self):
        for r in ([self.cur] if self.cur else []) + list(self.q):
            r.aborted = True
        self.q.clear()
        self.cur = None
        self.gap_left = None
        self.r_cnt = None

    def drive(self, e, prev):
        b = self.b
        d = b.dut
        if (self.cur is not None and prev is not None and prev["rst"] == 1
                and prev["arvalid"] == 1 and prev["arready"] == 1):
            self.cur.hs_edge = prev["cyc"]
            self.cur = None
        if b.rst_now != 1:
            self.flush()
        if self.cur is None and self.q and b.rst_now == 1:
            r = self.q[0]
            if e >= r.not_before:
                if self.gap_left is None:
                    self.gap_left = r.gap
                if self.gap_left > 0:
                    self.gap_left -= 1
                else:
                    self.cur = self.q.popleft()
                    self.gap_left = None
                    self.cur.first_valid = e
        c = self.cur
        if c is not None:
            d.i_axi_arid.value = c.id
            d.i_axi_araddr.value = c.addr
            d.i_axi_arlen.value = c.len & 0xFF
            d.i_axi_arsize.value = c.size & 7
            d.i_axi_arburst.value = c.burst & 3
            d.i_axi_arcache.value = c.cache & 0xF
            d.i_axi_arprot.value = c.prot & 7
            d.i_axi_arvalid.value = 1
        else:
            d.i_axi_arvalid.value = 0
        # R ready policy: hold low for a delay before each beat
        if prev is not None and prev["rvalid"] == 1 and prev["rready"] == 1:
            self.r_cnt = None
        rv = _v(d.o_axi_rvalid)
        if rv == 1 and b.rst_now == 1:
            if self.r_cnt is None:
                self.r_cnt = max(0, int(self.rready_delay()))
            if self.r_cnt > 0:
                rr = 0
                self.r_cnt -= 1
            else:
                rr = 1
        else:
            self.r_cnt = None
            rr = int(self.rready_idle()) & 1
        d.i_axi_rready.value = rr


class WriteMaster:
    def __init__(self, bench):
        self.b = bench
        self.aw_q = deque()
        self.aw_cur = None
        self.aw_gap_left = None
        self.w_q = deque()
        self.w_pres = False
        self.w_gap_left = None
        self.bready_delay = lambda: 0
        self.bready_idle = lambda: 1
        self.b_cnt = None
        self.reqs = []

    def req(self, addr, ln=0, size=2, burst=INCR, cache=0, prot=0, id=None, data=None, strb=None,
            w_early=False, aw_not_before=0, w_not_before=0, gap=0, wgap=None, w_stop_after=None):
        b = self.b
        if id is None:
            id = b.rnd.getrandbits(b.idw)
        if data is None:
            data = [b.rnd.getrandbits(32) for _ in range(ln + 1)]
        if strb is None:
            strb = default_strobes(addr, ln, size, burst)
        q = WriteReq(id & b.idmask, addr & 0xFFFFFFFF, ln, size, burst, cache, prot, data, strb,
                     w_early, aw_not_before, w_not_before, gap, wgap, w_stop_after)
        self.aw_q.append(q)
        self.w_q.append(q)
        self.reqs.append(q)
        return q

    def busy(self):
        return self.aw_cur is not None or bool(self.aw_q) or bool(self.w_q)

    def flush(self):
        for r in ([self.aw_cur] if self.aw_cur else []) + list(self.aw_q) + list(self.w_q):
            r.aborted = True
        self.aw_q.clear()
        self.w_q.clear()
        self.aw_cur = None
        self.aw_gap_left = None
        self.w_pres = False
        self.w_gap_left = None
        self.b_cnt = None

    def drive(self, e, prev):
        b = self.b
        d = b.dut
        ok_prev = prev is not None and prev["rst"] == 1
        if self.aw_cur is not None and ok_prev and prev["awvalid"] == 1 and prev["awready"] == 1:
            self.aw_cur.hs_edge = prev["cyc"]
            self.aw_cur = None
        if self.w_pres and ok_prev and prev["wvalid"] == 1 and prev["wready"] == 1:
            wr = self.w_q[0]
            wr.w_edges.append(prev["cyc"])
            wr.w_idx += 1
            self.w_pres = False
            self.w_gap_left = None
            if wr.w_idx >= len(wr.data):
                self.w_q.popleft()
        if b.rst_now != 1:
            self.flush()
        # ---- AW
        if self.aw_cur is None and self.aw_q and b.rst_now == 1:
            r = self.aw_q[0]
            if e >= r.not_before:
                if self.aw_gap_left is None:
                    self.aw_gap_left = r.gap
                if self.aw_gap_left > 0:
                    self.aw_gap_left -= 1
                else:
                    self.aw_cur = self.aw_q.popleft()
                    self.aw_gap_left = None
                    self.aw_cur.first_valid = e
        c = self.aw_cur
        if c is not None:
            d.i_axi_awid.value = c.id
            d.i_axi_awaddr.value = c.addr
            d.i_axi_awlen.value = c.len & 0xFF
            d.i_axi_awsize.value = c.size & 7
            d.i_axi_awburst.value = c.burst & 3
            d.i_axi_awcache.value = c.cache & 0xF
            d.i_axi_awprot.value = c.prot & 7
            d.i_axi_awvalid.value = 1
        else:
            d.i_axi_awvalid.value = 0
        # ---- W
        if not self.w_pres and self.w_q and b.rst_now == 1:
            wr = self.w_q[0]
            allowed = ((wr.w_early or wr.hs_edge is not None) and e >= wr.w_not_before
                       and (wr.w_stop_after is None or wr.w_idx < wr.w_stop_after))
            if allowed:
                if self.w_gap_left is None:
                    self.w_gap_left = max(0, int(wr.wgap())) if wr.wgap else 0
                if self.w_gap_left > 0:
                    self.w_gap_left -= 1
                else:
                    self.w_pres = True
                    self.w_gap_left = None
                    if wr.w_first_valid is None:
                        wr.w_first_valid = e
        if self.w_pres:
            wr = self.w_q[0]
            k = wr.w_idx
            d.i_axi_wdata.value = wr.data[k] & 0xFFFFFFFF
            d.i_axi_wstrb.value = wr.strb[k] & 0xF
            d.i_axi_wlast.value = 1 if k == len(wr.data) - 1 else 0
            d.i_axi_wvalid.value = 1
        else:
            d.i_axi_wvalid.value = 0
        # ---- B ready policy
        if ok_prev and prev["bvalid"] == 1 and prev["bready"] == 1:
            self.b_cnt = None
        bv = _v(d.o_axi_bvalid)
        if bv == 1 and b.rst_now == 1:
            if self.b_cnt is None:
                self.b_cnt = max(0, int(self.bready_delay()))
            if self.b_cnt > 0:
                br = 0
                self.b_cnt -= 1
            else:
                br = 1
        else:
            self.b_cnt = None
            br = int(self.bready_idle()) & 1
        d.i_axi_bready.value = br


# --------------------------------------------------------------------------
# Transaction tracker (CHK-014) with protocol monitors
# --------------------------------------------------------------------------
class Xfer:
    def __init__(self, s, e):
        self.pay = {k: s[k] for k in APB_PAY}
        self.setup = e
        self.access = 0
        self.done = None
        self.prdata = None
        self.pslverr = None
        self.stable = True
        self.broken = False
        self.txn = None


class Txn:
    def __init__(self, kind, s, e):
        p = "ar" if kind == "R" else "aw"
        self.kind = kind
        self.id = s[p + "id"]
        self.addr = s[p + "addr"]
        self.len = s[p + "len"]
        self.size = s[p + "size"]
        self.burst = s[p + "burst"]
        self.cache = s[p + "cache"]
        self.prot = s[p + "prot"]
        self.h = e
        self.supported = classify(self.addr, self.len, self.size, self.burst, self.cache)
        self.apb, self.r, self.w = [], [], []
        self.b = None
        self.psel_edges = 0
        self.done = None
        self.aborted = False
        self.rvalid_first = None
        self.bvalid_first = None

    def needs_apb(self):
        return self.supported and len(self.apb) < self.len + 1

    def tag(self):
        return (f"{'read' if self.kind == 'R' else 'write'} id={self.id} addr=0x{self.addr:08x} "
                f"len={self.len} size={self.size} burst={self.burst} cache={self.cache} "
                f"prot={self.prot} (AxVALID handshake edge {self.h})")


class Tracker:
    def __init__(self):
        self.prev = None
        self.cur = None
        self.x = None
        self.errors = []
        self.finished = []
        self.by_h = {}
        self.completions = 0
        self.xfers_done = []

    def chk(self, cond, msg):
        if not cond and len(self.errors) < 50:
            self.errors.append(msg)

    def _finish(self, t, e, aborted=False):
        t.done = e
        t.aborted = aborted
        self.finished.append(t)
        if not aborted:
            self.completions += 1

    def step(self, s):
        e = s["cyc"]
        p = self.prev
        if p is not None and p["rst"] != 1:
            for k in RESET_ZERO:
                self.chk(s[k] == 0, f"CHK-017: {k}=0 at edge {e} (edge after reset) got {s[k]}")
            if s["rst"] != 1:
                for k in ("awready", "wready", "arready"):
                    self.chk(s[k] == 0, f"CHK-017: {k}=0 at edge {e} (reset at two edges) got {s[k]}")
        if s["rst"] != 1:
            if self.cur is not None:
                self._finish(self.cur, e, aborted=True)
                self.cur = None
            self.x = None
            self.prev = s
            return

        owner = self.cur
        ar_hs = s["arvalid"] == 1 and s["arready"] == 1
        aw_hs = s["awvalid"] == 1 and s["awready"] == 1
        w_hs = s["wvalid"] == 1 and s["wready"] == 1
        r_hs = s["rvalid"] == 1 and s["rready"] == 1
        b_hs = s["bvalid"] == 1 and s["bready"] == 1
        psel = s["psel"] == 1
        pen = s["penable"] == 1
        self.chk(not (ar_hs and aw_hs), f"CHK-014(a): no simultaneous AR and AW handshake got both at edge {e}")

        # ---- APB static checks
        self.chk(s["paddr"] >= 0 and (s["paddr"] & 3) == 0, f"CHK-004: paddr[1:0]=0 got 0x{s['paddr'] & 0xFFFFFFFF:x} at edge {e}")
        self.chk(not (pen and not psel), f"CHK-001(a): penable=1 implies psel=1 at edge {e}")
        if not psel:
            self.chk(s["penable"] == 0 and all(s[k] == 0 for k in APB_PAY),
                     f"CHK-006: APB outputs 0 when psel=0 at edge {e} got " + str({k: s[k] for k in APB_PAY}))
        elif s["pwrite"] == 0:
            self.chk(s["pstrb"] == 0, f"CHK-005: pstrb=0 on APB read at edge {e} got {s['pstrb']}")

        # ---- APB transfer tracking
        pending_x = None
        x = self.x
        if x is not None and not (psel and pen):
            self.chk(False, f"CHK-001/CHK-002: transfer (SETUP edge {x.setup}) must stay in ACCESS at edge {e} "
                            f"got psel={s['psel']} penable={s['penable']}")
            x.broken = True
            self.x = None
            x = None
        if psel and not pen:
            nx = Xfer(s, e)
            self.x = nx
            if owner is not None and owner.needs_apb():
                owner.apb.append(nx)
                nx.txn = owner
            else:
                pending_x = nx
        elif psel and pen:
            if x is None:
                self.chk(False, f"CHK-001(d): ACCESS at edge {e} not preceded by SETUP or waited ACCESS")
            else:
                x.access += 1
                for k in APB_PAY:
                    if s[k] != x.pay[k]:
                        x.stable = False
                        self.chk(False, f"CHK-002/CHK-003: {k} stable through transfer (SETUP edge {x.setup}) "
                                        f"expected 0x{x.pay[k] & 0xFFFFFFFF:x} got 0x{s[k] & 0xFFFFFFFF:x} at edge {e}")
                if s["pready"] == 1:
                    x.done = e
                    x.prdata = s["prdata"]
                    x.pslverr = s["pslverr"]
                    self.x = None
                    self.xfers_done.append(x)
        if psel:
            if owner is not None:
                owner.psel_edges += 1
                if not owner.supported:
                    self.chk(False, f"CHK-015: psel=0 during unsupported {owner.tag()} got psel=1 at edge {e}")
            elif not (ar_hs or aw_hs):
                self.chk(False, f"CHK-014(e): psel=1 only with an owner got psel=1 at idle edge {e}")

        # ---- W
        done_now = False
        pending_w = None
        if s["wready"] == 1:
            self.chk((owner is not None and owner.kind == "W") or aw_hs,
                     f"CHK-013(a): wready=1 only when owner=WR or at the AW handshake got wready=1 at edge {e}")
        if w_hs:
            wb = dict(edge=e, data=s["wdata"], strb=s["wstrb"], last=s["wlast"])
            if owner is not None and owner.kind == "W" and not b_hs:
                owner.w.append(wb)
                self.chk(len(owner.w) <= owner.len + 1,
                         f"CHK-013(b): at most {owner.len + 1} W handshakes got {len(owner.w)} for {owner.tag()}")
            elif aw_hs:
                pending_w = wb
            else:
                self.chk(False, f"CHK-013: W handshake only inside a write got one at edge {e}")

        # ---- R
        if s["rvalid"] == 1:
            if owner is None or owner.kind != "R":
                self.chk(False, f"CHK-014(c): rvalid=1 only while owner=RD got rvalid=1 at edge {e}")
            else:
                if owner.rvalid_first is None:
                    owner.rvalid_first = e
                k = len(owner.r)
                self.chk(s["rid"] == owner.id, f"CHK-010: rid={owner.id} got {s['rid']} at edge {e}")
                self.chk(s["rlast"] == (1 if k == owner.len else 0),
                         f"CHK-010: rlast={(1 if k == owner.len else 0)} on beat {k} of {owner.tag()} got {s['rlast']}")
                if owner.supported:
                    nd = sum(1 for xx in owner.apb if xx.done is not None)
                    self.chk(nd >= k + 1, f"CHK-011(a): >= {k + 1} APB completions before R beat {k} got {nd} at edge {e}")
                    if nd >= k + 1:
                        xx = owner.apb[k]
                        if xx.pslverr == 1:
                            self.chk(s["rresp"] == SLVERR and s["rdata"] == 0,
                                     f"CHK-011(c): beat {k} with PSLVERR is SLVERR/0 got rresp={s['rresp']} rdata=0x{s['rdata'] & 0xFFFFFFFF:x}")
                        else:
                            self.chk(s["rresp"] == OKAY and s["rdata"] == xx.prdata,
                                     f"CHK-011(b): beat {k} OKAY rdata=0x{xx.prdata:08x} got rresp={s['rresp']} rdata=0x{s['rdata'] & 0xFFFFFFFF:x}")
                else:
                    self.chk(s["rresp"] == SLVERR and s["rdata"] == 0,
                             f"CHK-012: unsupported read beat SLVERR/0 got rresp={s['rresp']} rdata=0x{s['rdata'] & 0xFFFFFFFF:x}")
                if r_hs:
                    owner.r.append(dict(edge=e, id=s["rid"], data=s["rdata"], resp=s["rresp"], last=s["rlast"]))
                    if s["rlast"] == 1:
                        done_now = True

        # ---- B
        if s["bvalid"] == 1:
            if owner is None or owner.kind != "W":
                self.chk(False, f"CHK-014(d): bvalid=1 only while owner=WR got bvalid=1 at edge {e}")
            else:
                if owner.bvalid_first is None:
                    owner.bvalid_first = e
                nw = sum(1 for wb in owner.w if wb["edge"] < e)
                self.chk(nw == owner.len + 1, f"CHK-008(b): {owner.len + 1} W handshakes before bvalid got {nw} at edge {e}")
                self.chk(s["bid"] == owner.id, f"CHK-008(a): bid={owner.id} got {s['bid']} at edge {e}")
                if owner.supported:
                    dn = [xx for xx in owner.apb if xx.done is not None and xx.done < e]
                    self.chk(len(dn) == owner.len + 1,
                             f"CHK-008(c): {owner.len + 1} APB write completions before bvalid got {len(dn)} at edge {e}")
                    exp = SLVERR if any(xx.pslverr == 1 for xx in dn) else OKAY
                    self.chk(s["bresp"] == exp, f"CHK-008(c): bresp={exp} got {s['bresp']} at edge {e}")
                else:
                    self.chk(s["bresp"] == SLVERR, f"CHK-008(d): bresp=SLVERR for unsupported write got {s['bresp']}")
                if b_hs:
                    owner.b = dict(edge=e, id=s["bid"], resp=s["bresp"])
                    done_now = True

        if done_now:
            self._finish(owner, e)
            self.cur = None

        # ---- new address handshake
        if ar_hs or aw_hs:
            if self.cur is not None:
                self.chk(False, f"CHK-014(b): no address handshake while {self.cur.tag()} owns the bridge got one at edge {e}")
                self._finish(self.cur, e, aborted=True)
            kind = "R" if ar_hs else "W"
            t = Txn(kind, s, e)
            self.cur = t
            self.by_h[(kind, e)] = t
            if psel:
                t.psel_edges += 1
            if pending_x is not None:
                if t.needs_apb():
                    t.apb.append(pending_x)
                    pending_x.txn = t
                else:
                    self.chk(False, f"CHK-015/CHK-014(e): no APB SETUP for unsupported {t.tag()} got SETUP at edge {e}")
            if pending_w is not None:
                if kind == "W":
                    t.w.append(pending_w)
                else:
                    self.chk(False, f"CHK-013: W handshake only inside a write got one at AR edge {e}")
        elif pending_x is not None:
            self.chk(False, f"CHK-014(e)/CHK-016: APB SETUP only for a transaction needing a transfer got one at edge {e}")

        # ---- response hold under backpressure
        if p is not None and p["rst"] == 1:
            if p["rvalid"] == 1 and p["rready"] != 1:
                self.chk(s["rvalid"] == 1 and all(s[k] == p[k] for k in ("rid", "rdata", "rresp", "rlast")),
                         f"CHK-009: R beat held while rready=0 (edge {p['cyc']}->{e}) got a change")
            if p["bvalid"] == 1 and p["bready"] != 1:
                self.chk(s["bvalid"] == 1 and all(s[k] == p[k] for k in ("bid", "bresp")),
                         f"CHK-007: B held while bready=0 (edge {p['cyc']}->{e}) got a change")
        self.prev = s


# --------------------------------------------------------------------------
# Bench: scheduler, scoreboard
# --------------------------------------------------------------------------
class Bench:
    def __init__(self, dut, rnd):
        self.dut = dut
        self.rnd = rnd
        self.idw = id_width()
        self.idmask = (1 << self.idw) - 1
        self.clk = getattr(dut, CLOCK)
        self.h = {k: getattr(dut, p) for k, p in SIG.items()}
        self.cycle = 0
        self.last = None
        self.hist = deque(maxlen=6000)
        self.hooks = []
        self.rst_left = 0
        self.rst_now = 1
        self.reset_edges = []
        self.trk = Tracker()
        self.ref = ByteMem()
        self.apb = ApbCompleter(self)
        self.rd = ReadMaster(self)
        self.wr = WriteMaster(self)
        self.sb_idx = 0
        self.scored = []
        self.ref_data_check = True

    async def run(self):
        for _ in range(MAX_SIM_CYCLES):
            await FallingEdge(self.clk)
            e = self.cycle + 1
            prev = self.last
            if self.rst_left > 0:
                self.rst_now = 0
                self.rst_left -= 1
            else:
                self.rst_now = 1
            self.h["rst"].value = self.rst_now
            self.rd.drive(e, prev)
            self.wr.drive(e, prev)
            self.apb.drive(e)
            await ReadOnly()
            s = {k: _v(hh) for k, hh in self.h.items()}
            s["cyc"] = e
            if s["rst"] != 1:
                self.reset_edges.append(e)
            self.trk.step(s)
            for f in self.hooks:
                f(s)
            self.hist.append(s)
            self.last = s
            self.cycle = e

    # ---- helpers
    def snap(self, e):
        if not self.hist:
            return None
        i = e - self.hist[0]["cyc"]
        if 0 <= i < len(self.hist):
            return self.hist[i]
        return None

    def raise_errors(self):
        if self.trk.errors:
            assert False, self.trk.errors[0]

    async def cycles(self, n):
        for _ in range(n):
            await FallingEdge(self.clk)
        self.raise_errors()

    async def wait_for(self, cond, max_cycles, what):
        for _ in range(max_cycles):
            await FallingEdge(self.clk)
            self.raise_errors()
            if cond():
                return
        assert False, f"{what} got timeout after {max_cycles} cycles"

    def txn(self, q):
        if q.hs_edge is None:
            return None
        return self.trk.by_h.get((q.kind, q.hs_edge))

    def is_done(self, q):
        t = self.txn(q)
        return t is not None and t.done is not None

    async def wait_done(self, *reqs, max_cycles=20000, what="transaction completes"):
        await self.wait_for(lambda: all(self.is_done(q) for q in reqs), max_cycles, what)

    def quiet(self):
        return (not self.rd.busy() and not self.wr.busy() and self.trk.cur is None
                and self.last is not None and self.last["rvalid"] != 1 and self.last["bvalid"] != 1)

    async def drain(self, max_cycles, what):
        await self.wait_for(self.quiet, max_cycles, what)

    async def reset(self, n=1):
        k0 = len(self.reset_edges)
        self.rst_left = n
        await self.wait_for(lambda: len(self.reset_edges) >= k0 + n and self.cycle >= self.reset_edges[-1] + 1,
                            n + 10, "reset pulse applied")
        return self.reset_edges[k0], self.reset_edges[-1]

    def preload(self, addr, word):
        self.apb.mem.write_word(addr, word, 0xF)
        self.ref.write_word(addr, word, 0xF)

    # ---- scoreboard
    def score(self):
        while self.sb_idx < len(self.trk.finished):
            t = self.trk.finished[self.sb_idx]
            self.sb_idx += 1
            if t.aborted:
                if t.kind == "W":
                    for k, x in enumerate(t.apb):
                        if x.done is not None and x.pslverr == 0 and is_mapped(x.pay["paddr"]):
                            self.ref.write_word(x.pay["paddr"], x.pay["pwdata"], x.pay["pstrb"])
                continue
            self._score_one(t)
            self.scored.append(t)

    def _score_one(self, t):
        n = t.len + 1
        tag = t.tag()
        if t.kind == "R":
            assert len(t.r) == n, f"CHK-010: {n} R beats for {tag} got {len(t.r)}"
            for k, bt in enumerate(t.r):
                assert bt["id"] == t.id, f"CHK-010: rid={t.id} on beat {k} of {tag} got {bt['id']}"
                assert bt["last"] == (1 if k == n - 1 else 0), \
                    f"CHK-010: rlast only on beat {n - 1} of {tag} got rlast={bt['last']} on beat {k}"
        if not t.supported:
            assert t.psel_edges == 0, f"CHK-015: psel=0 for unsupported {tag} got psel=1 on {t.psel_edges} edges"
            if t.kind == "R":
                for k, bt in enumerate(t.r):
                    assert bt["resp"] == SLVERR and bt["data"] == 0, \
                        f"CHK-012: unsupported beat {k} SLVERR/0 for {tag} got resp={bt['resp']} data=0x{bt['data']:x}"
            else:
                assert len(t.w) == n, f"CHK-013: {n} W beats drained for {tag} got {len(t.w)}"
                assert t.b is not None, f"CHK-008: one B for {tag} got none"
                assert t.b["resp"] == SLVERR, f"CHK-008(d): SLVERR B for {tag} got {t.b['resp']}"
                assert t.b["id"] == t.id, f"CHK-008(a): bid={t.id} for {tag} got {t.b['id']}"
                assert t.bvalid_first > t.w[-1]["edge"], f"CHK-008(b): bvalid after last W for {tag} got edge {t.bvalid_first}"
            return
        addrs = beat_addrs(t.addr, t.len, t.size, t.burst)
        assert len(t.apb) == n, f"CHK-016: {n} APB transfers for {tag} got {len(t.apb)}"
        for k, x in enumerate(t.apb):
            assert x.done is not None, f"CHK-016: APB transfer {k} of {tag} completes got incomplete"
            assert x.pay["pwrite"] == (1 if t.kind == "W" else 0), \
                f"CHK-016: pwrite matches direction for {tag} transfer {k} got {x.pay['pwrite']}"
            assert x.pay["paddr"] == (addrs[k] & 0xFFFFFFFC), \
                f"CHK-016: paddr=0x{addrs[k] & 0xFFFFFFFC:08x} for transfer {k} of {tag} got 0x{x.pay['paddr']:08x}"
            assert x.pay["pprot"] == t.prot, f"CHK-016: pprot={t.prot} for {tag} got {x.pay['pprot']}"
        if t.kind == "R":
            for k, (bt, x) in enumerate(zip(t.r, t.apb)):
                assert x.pay["pstrb"] == 0, f"CHK-005: pstrb=0 on read {tag} got {x.pay['pstrb']}"
                if x.pslverr == 1:
                    assert bt["resp"] == SLVERR and bt["data"] == 0, \
                        f"CHK-011(c): beat {k} SLVERR/0 for {tag} got resp={bt['resp']} data=0x{bt['data']:x}"
                else:
                    assert bt["resp"] == OKAY and bt["data"] == x.prdata, \
                        f"CHK-011(b): beat {k} OKAY data=0x{x.prdata:08x} for {tag} got resp={bt['resp']} data=0x{bt['data']:08x}"
                    if self.ref_data_check and is_mapped(x.pay["paddr"]):
                        exp = self.ref.read_word(x.pay["paddr"])
                        assert bt["data"] == exp, \
                            f"CHK-027: reference model data 0x{exp:08x} at 0x{x.pay['paddr']:08x} beat {k} of {tag} got 0x{bt['data']:08x}"
        else:
            assert len(t.w) == n, f"CHK-013: {n} W beats for {tag} got {len(t.w)}"
            for k, (wb, x) in enumerate(zip(t.w, t.apb)):
                assert x.pay["pwdata"] == wb["data"], \
                    f"CHK-016: pwdata=0x{wb['data']:08x} transfer {k} of {tag} got 0x{x.pay['pwdata']:08x}"
                assert x.pay["pstrb"] == wb["strb"], \
                    f"CHK-016: pstrb={wb['strb']:04b} transfer {k} of {tag} got {x.pay['pstrb']:04b}"
                if x.pslverr != 1 and is_mapped(x.pay["paddr"]):
                    self.ref.write_word(addrs[k], wb["data"], wb["strb"])
            assert t.b is not None, f"CHK-008: one B for {tag} got none"
            exp = SLVERR if any(x.pslverr == 1 for x in t.apb) else OKAY
            assert t.b["resp"] == exp, f"CHK-008(c): bresp={exp} for {tag} got {t.b['resp']}"
            assert t.b["id"] == t.id, f"CHK-008(a): bid={t.id} for {tag} got {t.b['id']}"
            assert t.bvalid_first > max(x.done for x in t.apb), \
                f"CHK-008(c): bvalid after last APB completion for {tag} got edge {t.bvalid_first}"
            assert t.bvalid_first > t.w[-1]["edge"], f"CHK-008(b): bvalid after last W for {tag} got edge {t.bvalid_first}"

    def compare_mem(self, tag):
        keys = set(self.ref.d) | set(self.apb.mem.d)
        for a in sorted(keys):
            assert self.ref.rd8(a) == self.apb.mem.rd8(a), \
                f"{tag}: memory byte 0x{a:08x} expected 0x{self.ref.rd8(a):02x} got 0x{self.apb.mem.rd8(a):02x}"

    def final(self):
        self.raise_errors()
        self.score()
        self.raise_errors()


async def make_bench(dut, salt, reset_cycles=5):
    start_clock(dut)
    await reset_dut(dut, cycles=reset_cycles)
    b = Bench(dut, rng(salt))
    cocotb.start_soon(b.run())
    await b.cycles(2)
    return b


def budget(ln, per=60):
    return 1000 + (ln + 1) * per


# --------------------------------------------------------------------------
# Random traffic generation
# --------------------------------------------------------------------------
def gen_req(r, idw, extras=False):
    if extras and r.random() < 0.03:
        return dict(addr=UNMAPPED_BASE + 4 * r.randrange(0x100), ln=r.randint(0, 3), size=2, burst=INCR,
                    cache=r.choice([0, 1]), prot=r.randrange(8), id=r.getrandbits(idw))
    burst = r.choice([FIXED, INCR, WRAP])
    size = r.choice([0, 1, 2])
    S = 1 << size
    if burst == FIXED:
        ln = r.randint(0, 15)
        addr = r.randrange(0x10000)
    elif burst == WRAP:
        ln = r.choice([1, 3, 7, 15])
        addr = r.randrange(0x10000) & ~(S - 1)
    else:
        x = r.random()
        ln = r.randint(0, 15) if x < 0.7 else (r.randint(16, 63) if x < 0.93 else r.randint(64, 255))
        total = (ln + 1) * S
        page = r.randrange(16) << 12
        base = r.randint(0, (4096 - total) // S) * S
        addr = page + base + (r.randrange(S) if r.random() < 0.3 else 0)
    cache = r.choice([0, 1])
    if extras and r.random() < 0.03:
        cache = r.randint(2, 15)
    return dict(addr=addr, ln=ln, size=size, burst=burst, cache=cache, prot=r.randrange(8), id=r.getrandbits(idw))


def rand_strobes(r, f):
    lanes = default_strobes(f["addr"], f["ln"], f["size"], f["burst"])
    return [m if r.random() < 0.8 else ((m & r.randint(1, 15)) or m) for m in lanes]


def set_random_policies(b, r):
    b.apb.wait_fn = lambda x: r.randint(0, 3)
    b.rd.rready_delay = lambda: r.choice([0, 0, 0, 1, 2, 5])
    b.rd.rready_idle = lambda: r.getrandbits(1)
    b.wr.bready_delay = lambda: r.choice([0, 0, 0, 1, 3, 6])
    b.wr.bready_idle = lambda: r.getrandbits(1)


async def random_traffic(b, r, n, tag, extras=False):
    reset_points = set(r.sample(range(max(1, n // 5), n), 2)) if (extras and n >= 10) else set()
    wgap = lambda: r.choice([0, 0, 0, 1, 3])
    for i in range(n):
        await b.wait_for(lambda: len(b.rd.q) + len(b.wr.aw_q) < 4, 60000,
                         f"{tag}: bridge accepts queued requests")
        f = gen_req(r, b.idw, extras)
        if r.random() < 0.5:
            b.rd.req(**f, gap=r.choice([0, 0, 0, 1, 4]))
        else:
            b.wr.req(**f, strb=rand_strobes(r, f), gap=r.choice([0, 0, 0, 1, 4]),
                     w_early=r.random() < 0.25, wgap=wgap)
        if i in reset_points:
            await b.cycles(r.randint(3, 60))
            await b.reset(r.randint(1, 3))
        if i % 100 == 99:
            b.score()
    await b.drain(300000, f"{tag}: all random transactions complete")
    b.final()


# ==========================================================================
# Tests
# ==========================================================================
def _check_long_wait(b, t, wait, pend, what):
    assert len(t.apb) == 1, f"CHK-018: one APB transfer for {what} got {len(t.apb)}"
    x = t.apb[0]
    assert x.done is not None, f"CHK-018: {what} transfer completes got incomplete"
    assert x.access == wait + 1, f"CHK-018: ACCESS lasts {wait + 1} edges for {what} got {x.access}"
    assert x.done - x.setup == wait + 1, f"CHK-018: completion {wait + 1} edges after SETUP got {x.done - x.setup}"
    assert x.stable and not x.broken, f"CHK-018: APB payload stable and transfer not dropped for {what}"
    for e in range(x.setup + 1, x.done + 1):
        s = b.snap(e)
        assert s is not None, f"CHK-018: history for edge {e} available got none"
        assert s["psel"] == 1 and s["penable"] == 1, \
            f"CHK-018: psel=1 penable=1 at wait edge {e} got psel={s['psel']} penable={s['penable']}"
        for k in APB_PAY:
            assert s[k] == x.pay[k], f"CHK-018: {k} unchanged at edge {e} expected {x.pay[k]} got {s[k]}"
    for e in range(x.setup, x.done):
        s = b.snap(e)
        assert s["rvalid"] == 0 and s["bvalid"] == 0, \
            f"CHK-018: no rvalid/bvalid during wait at edge {e} got rvalid={s['rvalid']} bvalid={s['bvalid']}"
        assert not (s["arvalid"] == 1 and s["arready"] == 1) and not (s["awvalid"] == 1 and s["awready"] == 1), \
            f"CHK-018: no address handshake during wait got one at edge {e}"
    assert pend.first_valid is not None and pend.first_valid + wait // 2 < x.done, \
        f"CHK-018: competing request pending during the wait got first_valid={pend.first_valid}"
    assert pend.hs_edge is not None and pend.hs_edge >= t.done, \
        f"CHK-018: pending request handshake only after {what} completes (edge {t.done}) got {pend.hs_edge}"


@cocotb.test()
async def test_chk_018_long_apb_wait(dut):
    """CHK-018: long APB wait (1000 PREADY=0 cycles) is held with no timeout, then completes normally."""
    b = await make_bench(dut, "chk018")
    r = b.rnd
    WAIT = 1000
    b.apb.wait_fn = lambda x: WAIT if x["paddr"] == 0x5000 else 0
    b.preload(0x5000, 0x0BADF00D)
    rq = b.rd.req(addr=0x5000, ln=0, size=2, burst=INCR, prot=r.randrange(8))
    await b.wait_for(lambda: rq.hs_edge is not None, 100, "CHK-018: AR handshake of the single-beat read")
    pend_w = b.wr.req(addr=0x5100, ln=0, size=2, burst=INCR)
    await b.wait_done(rq, max_cycles=WAIT + 400, what="CHK-018: read completes after the long wait")
    await b.wait_done(pend_w, max_cycles=500, what="CHK-018: pending write completes after the read")
    t = b.txn(rq)
    _check_long_wait(b, t, WAIT, pend_w, "read")
    assert len(t.r) == 1 and t.r[0]["data"] == 0x0BADF00D and t.r[0]["resp"] == OKAY, \
        f"CHK-018: read returns 0x0BADF00D OKAY got {t.r}"
    assert t.rvalid_first >= t.apb[0].done, f"CHK-018: no rvalid before APB completion got edge {t.rvalid_first}"

    wdat = r.getrandbits(32)
    wq = b.wr.req(addr=0x5000, ln=0, size=2, burst=INCR, data=[wdat], strb=[0xF], prot=r.randrange(8))
    await b.wait_for(lambda: wq.hs_edge is not None, 100, "CHK-018: AW handshake of the single-beat write")
    pend_r = b.rd.req(addr=0x5008, ln=0, size=2, burst=INCR)
    await b.wait_done(wq, max_cycles=WAIT + 400, what="CHK-018: write completes after the long wait")
    await b.wait_done(pend_r, max_cycles=500, what="CHK-018: pending read completes after the write")
    t2 = b.txn(wq)
    _check_long_wait(b, t2, WAIT, pend_r, "write")
    x = t2.apb[0]
    assert x.pay["pwdata"] == wdat and x.pay["pstrb"] == 0xF and x.pay["pwrite"] == 1, \
        f"CHK-018: APB write payload WDATA=0x{wdat:08x} got {x.pay}"
    assert t2.b is not None and t2.b["resp"] == OKAY, f"CHK-018: BRESP OKAY got {t2.b}"
    assert t2.bvalid_first > x.done, f"CHK-018: bvalid only after APB completion got {t2.bvalid_first}"
    b.final()


@cocotb.test()
async def test_chk_019_arbitration_round_robin(dut):
    """CHK-019: AR/AW round-robin; AR wins first tie after reset, preference flips after each completion."""
    b = await make_bench(dut, "chk019")
    t0 = b.cycle + 3
    r1 = b.rd.req(addr=0x0100, ln=1, size=2, burst=INCR, not_before=t0)
    r2 = b.rd.req(addr=0x0180, ln=1, size=2, burst=INCR)
    w1 = b.wr.req(addr=0x0200, ln=1, size=2, burst=INCR, aw_not_before=t0)
    w2 = b.wr.req(addr=0x0280, ln=1, size=2, burst=INCR)
    await b.wait_done(r1, r2, w1, w2, max_cycles=3000, what="CHK-019: phases A-C complete")
    T = b.txn
    assert r1.first_valid == t0 and w1.first_valid == t0, \
        f"CHK-019: AR and AW asserted at the same edge got {r1.first_valid}/{w1.first_valid}"
    assert r1.hs_edge < w1.hs_edge, f"CHK-019: phase A AR (R1) granted first got R1={r1.hs_edge} W1={w1.hs_edge}"
    assert w1.hs_edge >= T(r1).done, f"CHK-019: W1 granted only at/after R1 final R (edge {T(r1).done}) got {w1.hs_edge}"
    assert r2.first_valid <= T(r1).done, "CHK-019: R2 pending when R1 completes (stimulus)"
    assert w1.hs_edge < r2.hs_edge, f"CHK-019: phase B W1 granted before R2 got W1={w1.hs_edge} R2={r2.hs_edge}"
    assert w2.first_valid <= T(w1).done, "CHK-019: W2 pending when W1 completes (stimulus)"
    assert r2.hs_edge >= T(w1).done and r2.hs_edge < w2.hs_edge, \
        f"CHK-019: phase C R2 granted before W2 got R2={r2.hs_edge} W2={w2.hs_edge} W1done={T(w1).done}"
    assert w2.hs_edge >= T(r2).done, f"CHK-019: W2 granted after R2 completes got {w2.hs_edge}"
    b.score()

    # Phase D
    await b.reset(2)
    w3 = b.wr.req(addr=0x0300, ln=1, size=2, burst=INCR)
    await b.wait_done(w3, max_cycles=500, what="CHK-019: lone AW W3 is granted and completes")
    assert w3.hs_edge - w3.first_valid <= 50, \
        f"CHK-019: lone W3 granted without waiting for an AR got wait {w3.hs_edge - w3.first_valid}"
    t1 = b.cycle + 3
    r4 = b.rd.req(addr=0x0400, ln=1, size=2, burst=INCR, not_before=t1)
    w4 = b.wr.req(addr=0x0480, ln=1, size=2, burst=INCR, aw_not_before=t1)
    await b.wait_done(r4, w4, max_cycles=1000, what="CHK-019: phase D tie completes")
    assert r4.first_valid == w4.first_valid, "CHK-019: R4/W4 asserted at the same edge"
    assert w4.hs_edge < r4.hs_edge and r4.hs_edge >= T(w4).done, \
        f"CHK-019: phase D tie won by W4 after 1 completion got W4={w4.hs_edge} R4={r4.hs_edge}"
    b.final()


@cocotb.test()
async def test_chk_020_wvalid_before_aw(dut):
    """CHK-020: WVALID before AW keeps WREADY low until the AW handshake; beats are then accepted in order."""
    b = await make_bench(dut, "chk020")
    r = b.rnd
    t0 = b.cycle + 3
    data = [r.getrandbits(32) for _ in range(4)]
    strb = [r.choice([0xF, 0x3, 0xC, 0x1, 0x8]) for _ in range(4)]
    wq = b.wr.req(addr=0x3000, ln=3, size=2, burst=INCR, data=data, strb=strb, w_early=True,
                  w_not_before=t0, aw_not_before=t0 + 10, wgap=lambda: 0)
    await b.wait_done(wq, max_cycles=500, what="CHK-020: early-W write completes")
    assert wq.w_first_valid == t0 and wq.first_valid == t0 + 10, \
        f"CHK-020: W at edge {t0} and AW 10 edges later (stimulus) got {wq.w_first_valid}/{wq.first_valid}"
    aw = wq.hs_edge
    pre = list(range(t0, aw))
    assert len(pre) >= 10, f"CHK-020: at least 10 edges before AW handshake got {len(pre)}"
    for e in pre:
        s = b.snap(e)
        assert s["wvalid"] == 1 and s["wready"] == 0, \
            f"CHK-020: wready=0 while W waits for AW at edge {e} got wready={s['wready']}"
    assert all(e >= aw for e in wq.w_edges), f"CHK-020: no W handshake before AW edge {aw} got {wq.w_edges}"
    t = b.txn(wq)
    assert len(t.w) == 4 and [w["data"] for w in t.w] == data, f"CHK-020: 4 W handshakes in order got {t.w}"
    assert [x.pay["paddr"] for x in t.apb] == [0x3000, 0x3004, 0x3008, 0x300C], \
        f"CHK-020: APB addresses 0x3000..0x300C got {[hex(x.pay['paddr']) for x in t.apb]}"
    for k, x in enumerate(t.apb):
        assert x.pay["pwdata"] == data[k] and x.pay["pstrb"] == strb[k] and x.pay["pwrite"] == 1, \
            f"CHK-020: APB write {k} carries WDATA/WSTRB got {x.pay}"
    assert t.b is not None and t.b["resp"] == OKAY and t.b["id"] == wq.id, f"CHK-020: B OKAY bid={wq.id} got {t.b}"
    assert t.bvalid_first > t.apb[3].done, f"CHK-020: B after 4th APB completion got {t.bvalid_first}"
    b.final()


@cocotb.test()
async def test_chk_021_response_backpressure(dut):
    """CHK-021: RREADY/BREADY backpressure stalls the owning transaction without loss or reordering."""
    b = await make_bench(dut, "chk021")
    r = b.rnd
    b.apb.wait_fn = lambda x: r.randint(0, 3)
    b.rd.rready_delay = lambda: r.randint(0, 50)
    b.wr.bready_delay = lambda: 100
    reads = [b.rd.req(addr=0xA000 + i * 0x100, ln=15, size=2, burst=INCR, prot=r.randrange(8)) for i in range(5)]
    writes = [b.wr.req(addr=0xB000 + i * 0x100, ln=7, size=2, burst=INCR, prot=r.randrange(8)) for i in range(5)]
    await b.drain(60000, "CHK-021: stalled transactions all complete")
    for q in reads:
        t = b.txn(q)
        assert t is not None and t.done is not None, "CHK-021: read completes"
        assert len(t.r) == 16, f"CHK-021: 16 R beats got {len(t.r)}"
        assert [bt["last"] for bt in t.r] == [0] * 15 + [1], f"CHK-021: rlast on beat 15 only got {[bt['last'] for bt in t.r]}"
        assert all(t.r[i]["edge"] < t.r[i + 1]["edge"] for i in range(15)), "CHK-021: R beats in order"
        assert len(t.apb) == 16, f"CHK-021: APB transfers = ARLEN+1 = 16 got {len(t.apb)}"
    for q in writes:
        t = b.txn(q)
        assert t is not None and t.b is not None, "CHK-021: write completes with B"
        assert t.b["edge"] - t.bvalid_first >= 100, \
            f"CHK-021: B held during 100-cycle BREADY stall got {t.b['edge'] - t.bvalid_first}"
        assert len(t.apb) == 8, f"CHK-021: APB transfers = AWLEN+1 = 8 got {len(t.apb)}"
    fin = sorted([t for t in b.trk.finished if not t.aborted], key=lambda t: t.h)
    for a, c in zip(fin, fin[1:]):
        assert c.h >= a.done, f"CHK-021: next address handshake at/after completion edge {a.done} of {a.tag()} got {c.h}"
    b.final()


UNSUP_CASES = ([(0x0, s, l, INCR, 0) for s in range(3, 8) for l in (0, 3)]
               + [(0x0, 2, l, 3, 0) for l in (0, 3)]
               + [(0x0, 2, 1, INCR, c) for c in range(2, 16)]
               + [(0xFFC, 2, 1, INCR, 0), (0xFFF, 0, 1, INCR, 0), (0xF00, 2, 255, INCR, 0)])


@cocotb.test()
async def test_chk_022_unsupported_reads(dut):
    """CHK-022: unsupported reads give no APB and ARLEN+1 SLVERR beats with zero data; recovery is normal."""
    b = await make_bench(dut, "chk022")
    r = b.rnd
    b.rd.rready_delay = lambda: r.randint(0, 3)
    b.rd.rready_idle = lambda: r.getrandbits(1)
    for (addr, size, ln, burst, cache) in UNSUP_CASES:
        bad = b.rd.req(addr=addr, ln=ln, size=size, burst=burst, cache=cache, prot=r.randrange(8))
        good = b.rd.req(addr=0x7100 + 8 * r.randrange(16), ln=1, size=2, burst=INCR, prot=r.randrange(8))
        await b.wait_done(bad, good, max_cycles=budget(ln, 20) + 1000,
                          what=f"CHK-022: unsupported read {(hex(addr), size, ln, burst, cache)} and recovery complete")
        t = b.txn(bad)
        assert not t.supported, f"CHK-022: stimulus is unsupported {t.tag()}"
        assert t.psel_edges == 0, f"CHK-022: psel=0 from AR to final R for {t.tag()} got {t.psel_edges} edges"
        assert len(t.r) == ln + 1, f"CHK-022: {ln + 1} R beats for {t.tag()} got {len(t.r)}"
        for k, bt in enumerate(t.r):
            assert bt["resp"] == SLVERR and bt["data"] == 0 and bt["id"] == bad.id, \
                f"CHK-022: beat {k} SLVERR/0/rid={bad.id} got {bt}"
            assert bt["last"] == (1 if k == ln else 0), f"CHK-022: rlast only on beat {ln} got {bt['last']} on {k}"
        g = b.txn(good)
        assert g.supported and len(g.apb) == 2 and all(bt["resp"] == OKAY for bt in g.r), \
            f"CHK-022: following legal read has 2 APB transfers and OKAY beats got {len(g.apb)} {g.r}"
        b.score()
    b.final()


@cocotb.test()
async def test_chk_023_unsupported_writes(dut):
    """CHK-023: unsupported writes drain AWLEN+1 W beats, no APB, one SLVERR B; recovery is normal."""
    b = await make_bench(dut, "chk023")
    r = b.rnd
    b.wr.bready_delay = lambda: r.randint(0, 3)
    b.wr.bready_idle = lambda: r.getrandbits(1)
    wgap = lambda: r.choice([0, 0, 1, 2, 3])
    for (addr, size, ln, burst, cache) in UNSUP_CASES:
        bad = b.wr.req(addr=addr, ln=ln, size=size, burst=burst, cache=cache, prot=r.randrange(8),
                       wgap=wgap, w_early=r.random() < 0.3)
        good = b.wr.req(addr=0x7100 + 8 * r.randrange(16), ln=1, size=2, burst=INCR, prot=r.randrange(8), wgap=wgap)
        await b.wait_done(bad, good, max_cycles=budget(ln, 30) + 1000,
                          what=f"CHK-023: unsupported write {(hex(addr), size, ln, burst, cache)} and recovery complete")
        t = b.txn(bad)
        assert not t.supported, f"CHK-023: stimulus is unsupported {t.tag()}"
        assert len(t.w) == ln + 1, f"CHK-023: {ln + 1} W handshakes for {t.tag()} got {len(t.w)}"
        assert t.psel_edges == 0, f"CHK-023: psel=0 from AW to B for {t.tag()} got {t.psel_edges} edges"
        assert t.bvalid_first > t.w[-1]["edge"], \
            f"CHK-023: bvalid after the (AWLEN+1)-th W handshake (edge {t.w[-1]['edge']}) got {t.bvalid_first}"
        assert t.b["resp"] == SLVERR and t.b["id"] == bad.id, f"CHK-023: one B SLVERR bid={bad.id} got {t.b}"
        g = b.txn(good)
        assert g.supported and len(g.apb) == 2 and g.b["resp"] == OKAY, \
            f"CHK-023: following legal write has APB writes and OKAY got {len(g.apb)} {g.b}"
        b.score()
    b.final()


@cocotb.test()
async def test_chk_024_read_pslverr(dut):
    """CHK-024: read PSLVERR maps to SLVERR with zero data on that beat only."""
    b = await make_bench(dut, "chk024")
    for k in range(4):
        b.preload(0x2000 + 4 * k, k)
    errset = {0x2004, 0x2100, 0x2200, 0x2204, 0x2208, 0x220C}
    b.apb.err_fn = lambda x: x["pwrite"] != 1 and x["paddr"] in errset
    b.apb.err_data = 0xDEADBEEF
    r1 = b.rd.req(addr=0x2000, ln=3, size=2, burst=INCR)
    await b.wait_done(r1, max_cycles=1000, what="CHK-024: 4-beat read completes")
    t = b.txn(r1)
    assert [x.pay["paddr"] for x in t.apb] == [0x2000, 0x2004, 0x2008, 0x200C], \
        f"CHK-024: APB reads at 0x2000..0x200C got {[hex(x.pay['paddr']) for x in t.apb]}"
    assert t.apb[1].pslverr == 1 and t.apb[1].prdata == 0xDEADBEEF, "CHK-024: error injected on transfer 1 (stimulus)"
    bt = t.r
    assert bt[0]["resp"] == OKAY and bt[0]["data"] == 0, f"CHK-024: beat 0 OKAY PRDATA0 got {bt[0]}"
    assert bt[1]["resp"] == SLVERR and bt[1]["data"] == 0, f"CHK-024: beat 1 SLVERR rdata=0 got {bt[1]}"
    assert bt[2]["resp"] == OKAY and bt[2]["data"] == 2, f"CHK-024: beat 2 OKAY PRDATA2 got {bt[2]}"
    assert bt[3]["resp"] == OKAY and bt[3]["data"] == 3, f"CHK-024: beat 3 OKAY PRDATA3 got {bt[3]}"
    assert [x["last"] for x in bt] == [0, 0, 0, 1], f"CHK-024: rlast on beat 3 only got {[x['last'] for x in bt]}"
    r2 = b.rd.req(addr=0x2100, ln=0, size=2, burst=INCR)
    await b.wait_done(r2, max_cycles=500, what="CHK-024: single-beat error read completes")
    t2 = b.txn(r2)
    assert len(t2.r) == 1 and t2.r[0]["resp"] == SLVERR and t2.r[0]["data"] == 0 and t2.r[0]["last"] == 1, \
        f"CHK-024: single error beat SLVERR/0/rlast got {t2.r}"
    r3 = b.rd.req(addr=0x2200, ln=3, size=2, burst=INCR)
    await b.wait_done(r3, max_cycles=1000, what="CHK-024: all-error read completes")
    t3 = b.txn(r3)
    assert len(t3.r) == 4 and all(x["resp"] == SLVERR and x["data"] == 0 for x in t3.r), \
        f"CHK-024: every beat SLVERR/0 got {t3.r}"
    for tt in (t, t2, t3):
        for x, bb in zip(tt.apb, tt.r):
            assert not (x.pslverr == 1 and bb["resp"] == OKAY), "CHK-024: an erroring beat is never OKAY"
    b.final()


@cocotb.test()
async def test_chk_025_write_pslverr(dut):
    """CHK-025: write PSLVERR accumulates into a final SLVERR BRESP; later beats still run; no carry-over."""
    b = await make_bench(dut, "chk025")
    r = b.rnd
    b.apb.wait_fn = lambda x: r.randint(0, 2)
    for name, idxs in (("transfer0", {0}), ("transfer3", {3}), ("all", {0, 1, 2, 3}), ("none", set())):
        base = b.apb.seq
        b.apb.err_fn = lambda x, base=base, idxs=idxs: x["pwrite"] == 1 and (x["seq"] - base) in idxs
        data = [r.getrandbits(32) for _ in range(4)]
        strb = [r.randint(1, 15) for _ in range(4)]
        wq = b.wr.req(addr=0x4000, ln=3, size=2, burst=INCR, data=data, strb=strb)
        await b.wait_done(wq, max_cycles=1000, what=f"CHK-025: write variant {name} completes")
        t = b.txn(wq)
        assert [x.pay["paddr"] for x in t.apb] == [0x4000, 0x4004, 0x4008, 0x400C], \
            f"CHK-025: {name}: 4 APB writes at 0x4000..0x400C got {[hex(x.pay['paddr']) for x in t.apb]}"
        for k, x in enumerate(t.apb):
            assert x.pay["pwdata"] == data[k] and x.pay["pstrb"] == strb[k], \
                f"CHK-025: {name}: transfer {k} PWDATA/PSTRB match got {x.pay}"
        errs = [k for k, x in enumerate(t.apb) if x.pslverr == 1]
        assert set(errs) == idxs, f"CHK-025: {name}: injected errors on {sorted(idxs)} (stimulus) got {errs}"
        assert t.bvalid_first > t.apb[3].done, f"CHK-025: {name}: B after 4th APB completion got {t.bvalid_first}"
        exp = SLVERR if idxs else OKAY
        assert t.b["resp"] == exp and t.b["id"] == wq.id, f"CHK-025: {name}: BRESP={exp} bid={wq.id} got {t.b}"
    b.final()


@cocotb.test()
async def test_chk_026_unmapped_default_completer(dut):
    """CHK-026: unmapped address answered by the default completer (PREADY=1, PSLVERR=1) gives AXI SLVERR."""
    b = await make_bench(dut, "chk026")
    rq = b.rd.req(addr=UNMAPPED_BASE, ln=1, size=2, burst=INCR)
    await b.wait_done(rq, max_cycles=500, what="CHK-026: unmapped read completes")
    t = b.txn(rq)
    assert [x.pay["paddr"] for x in t.apb] == [0x8000_0000, 0x8000_0004], \
        f"CHK-026: 2 APB reads at 0x80000000/4 got {[hex(x.pay['paddr']) for x in t.apb]}"
    for x in t.apb:
        assert x.access == 1 and x.done - x.setup == 1, \
            f"CHK-026: transfer lasts exactly 2 psel edges got access={x.access}"
    assert len(t.r) == 2 and all(bt["resp"] == SLVERR and bt["data"] == 0 for bt in t.r), \
        f"CHK-026: 2 SLVERR beats with rdata=0 got {t.r}"
    assert [bt["last"] for bt in t.r] == [0, 1], "CHK-026: rlast on beat 1"
    wq = b.wr.req(addr=UNMAPPED_BASE, ln=1, size=2, burst=INCR)
    await b.wait_done(wq, max_cycles=500, what="CHK-026: unmapped write completes")
    t2 = b.txn(wq)
    assert len(t2.apb) == 2 and all(x.pay["pwrite"] == 1 for x in t2.apb), \
        f"CHK-026: 2 APB writes got {len(t2.apb)}"
    for x in t2.apb:
        assert x.access == 1, f"CHK-026: write transfer lasts 2 psel edges got access={x.access}"
    assert t2.b["resp"] == SLVERR, f"CHK-026: BRESP SLVERR got {t2.b}"
    b.final()


@cocotb.test()
async def test_chk_027_random_legal_bursts(dut):
    """CHK-027: random legal FIXED/INCR/WRAP read/write bursts against an independent reference model."""
    b = await make_bench(dut, "chk027", reset_cycles=5)
    r = b.rnd
    set_random_policies(b, r)
    corners = [
        dict(addr=0x1000, ln=255, size=2, burst=INCR),
        dict(addr=0x1F00, ln=63, size=2, burst=INCR),
        dict(addr=0x1FF0, ln=15, size=0, burst=INCR),
        dict(addr=0x2100, ln=15, size=2, burst=FIXED),
        dict(addr=0x2203, ln=15, size=0, burst=FIXED),
        dict(addr=0x2024, ln=15, size=2, burst=WRAP),
        dict(addr=0x2301, ln=1, size=0, burst=WRAP),
    ]
    wrap_exp = [0x2024 + 4 * k for k in range(7)] + [0x2000 + 4 * k for k in range(9)]
    for i, c in enumerate(corners):
        wq = b.wr.req(**c, cache=i % 2, prot=r.randrange(8))
        rq = b.rd.req(**c, cache=1 - (i % 2), prot=r.randrange(8))
        await b.wait_done(wq, rq, max_cycles=budget(c["ln"], 40) * 2,
                          what=f"CHK-027: directed corner {c} completes")
        for q in (wq, rq):
            t = b.txn(q)
            pa = [x.pay["paddr"] for x in t.apb]
            assert len(pa) == c["ln"] + 1, f"CHK-027: {c['ln'] + 1} APB transfers for corner {c} got {len(pa)}"
            if c["addr"] == 0x1000:
                assert pa[-1] == 0x13FC, f"CHK-027: INCR 256 ends at 0x13FC got 0x{pa[-1]:x}"
            if c["addr"] in (0x1F00, 0x1FF0):
                assert pa[-1] == 0x1FFC, f"CHK-027: INCR ends at byte 0x1FFF got paddr 0x{pa[-1]:x}"
            if c["addr"] == 0x2024:
                assert pa == wrap_exp, f"CHK-027: WRAP corner addresses {[hex(a) for a in wrap_exp]} got {[hex(a) for a in pa]}"
            if c["addr"] == 0x2301:
                assert pa == [0x2300, 0x2300], f"CHK-027: WRAP len1 size0 paddr 0x2300 twice got {pa}"
        b.score()
    n = int(os.environ.get("NNC_N_TXN", "2000"))
    await random_traffic(b, r, n, "CHK-027", extras=False)
    b.compare_mem("CHK-027")
    cov = {(t.kind, t.cache) for t in b.scored if t.supported}
    for need in (("R", 0), ("R", 1), ("W", 0), ("W", 1)):
        assert need in cov, f"CHK-027: AxCACHE {need[1]} {need[0]} completes OKAY got coverage {cov}"
    for t in b.scored:
        if t.kind == "R":
            assert all(bt["resp"] == OKAY for bt in t.r), f"CHK-027: legal read OKAY got {t.tag()}"
        else:
            assert t.b["resp"] == OKAY, f"CHK-027: legal write OKAY got {t.tag()}"
    xs, lg = b.trk.xfers_done, b.apb.log
    assert len(xs) == len(lg), f"CHK-027: completer and monitor see the same transfers got {len(xs)}/{len(lg)}"
    for x, l in zip(xs, lg):
        assert x.pay["paddr"] == l["paddr"] and x.access == l["waits"] + 1, \
            f"CHK-027: transfer with {l['waits']} waits has {l['waits'] + 1} ACCESS edges got {x.access}"
    b.final()


@cocotb.test()
async def test_chk_028_subword_unaligned(dut):
    """CHK-028: sub-word/unaligned transfers: PADDR aligned down, PSTRB=WSTRB, no lane rotation."""
    b = await make_bench(dut, "chk028")
    singles = [(0x1000, 0, 0x1), (0x1001, 0, 0x2), (0x1002, 0, 0x4), (0x1003, 0, 0x8),
               (0x1000, 1, 0x3), (0x1002, 1, 0xC)]
    for addr, size, strb in singles:
        wq = b.wr.req(addr=addr, ln=0, size=size, burst=INCR, data=[0xAABBCCDD], strb=[strb])
        await b.wait_done(wq, max_cycles=300, what=f"CHK-028: byte/half write at 0x{addr:x} completes")
        t = b.txn(wq)
        assert len(t.apb) == 1, f"CHK-028: one APB write got {len(t.apb)}"
        x = t.apb[0]
        assert x.pay["paddr"] == addr & ~3, f"CHK-028: paddr=0x{addr & ~3:x} got 0x{x.pay['paddr']:x}"
        assert x.pay["pstrb"] == strb, f"CHK-028: pstrb={strb:04b} got {x.pay['pstrb']:04b}"
        assert x.pay["pwdata"] == 0xAABBCCDD, f"CHK-028: pwdata=0xAABBCCDD got 0x{x.pay['pwdata']:08x}"
        assert t.b["resp"] == OKAY, f"CHK-028: B OKAY got {t.b}"
    b.score()
    b.apb.read_fn = lambda x: 0x11223344
    b.ref_data_check = False
    for addr, size, _ in singles:
        rq = b.rd.req(addr=addr, ln=0, size=size, burst=INCR)
        await b.wait_done(rq, max_cycles=300, what=f"CHK-028: sub-word read at 0x{addr:x} completes")
        t = b.txn(rq)
        x = t.apb[0]
        assert x.pay["paddr"] == addr & ~3 and x.pay["pstrb"] == 0, f"CHK-028: read paddr aligned, pstrb=0 got {x.pay}"
        assert t.r[0]["data"] == 0x11223344 and t.r[0]["resp"] == OKAY, \
            f"CHK-028: rdata=0x11223344 unchanged got 0x{t.r[0]['data']:08x}"
    b.score()
    b.apb.read_fn = None
    b.ref_data_check = True
    strbs = default_strobes(0x1001, 7, 0, INCR)
    assert strbs == [0x2, 0x4, 0x8, 0x1, 0x2, 0x4, 0x8, 0x1], "CHK-028: legal one-hot strobes (stimulus)"
    wq = b.wr.req(addr=0x1001, ln=7, size=0, burst=INCR, strb=strbs)
    await b.wait_done(wq, max_cycles=500, what="CHK-028: INCR byte burst completes")
    t = b.txn(wq)
    exp_pa = [0x1000] * 3 + [0x1004] * 4 + [0x1008]
    assert [x.pay["paddr"] for x in t.apb] == exp_pa, \
        f"CHK-028: byte burst paddr {[hex(a) for a in exp_pa]} got {[hex(x.pay['paddr']) for x in t.apb]}"
    assert [x.pay["pstrb"] for x in t.apb] == strbs, f"CHK-028: byte burst pstrb got {[x.pay['pstrb'] for x in t.apb]}"
    assert [x.pay["pwdata"] for x in t.apb] == wq.data, "CHK-028: pwdata equals WDATA on all 32 bits"
    assert t.b["resp"] == OKAY, f"CHK-028: B OKAY got {t.b}"
    b.final()
    b.compare_mem("CHK-028")


@cocotb.test()
async def test_chk_029_prot_passthrough(dut):
    """CHK-029: AxPROT is copied to PPROT for all values, with no local access control."""
    b = await make_bench(dut, "chk029")
    seen = set()
    for i in range(8):
        for kind, prot in (("R", i), ("W", (i + 4) % 8)):
            if kind == "R":
                q = b.rd.req(addr=0x6000, ln=1, size=2, burst=INCR, prot=prot)
            else:
                q = b.wr.req(addr=0x6000, ln=1, size=2, burst=INCR, prot=prot)
            await b.wait_done(q, max_cycles=300, what=f"CHK-029: {kind} with prot={prot} completes")
            t = b.txn(q)
            assert len(t.apb) == 2, f"CHK-029: 2 APB transfers got {len(t.apb)}"
            for x in t.apb:
                assert x.pay["pprot"] == prot, f"CHK-029: pprot={prot} got {x.pay['pprot']}"
            if kind == "R":
                assert all(bt["resp"] == OKAY for bt in t.r), f"CHK-029: read prot={prot} OKAY got {t.r}"
            else:
                assert t.b["resp"] == OKAY, f"CHK-029: write prot={prot} OKAY got {t.b}"
            seen.add((kind, prot))
            b.score()
    assert len(seen) == 16, "CHK-029: every PROT value used for reads and writes"
    b.final()
    b.compare_mem("CHK-029")


@cocotb.test()
async def test_chk_030_id_echo(dut):
    """CHK-030: ARID/AWID echoed unchanged on R and B, for legal and unsupported requests."""
    b = await make_bench(dut, "chk030")
    r = b.rnd
    W = b.idw
    if W != 4:
        not_verifiable(dut, "CHK-030", f"plan stimulus is for PARA_AXI_ID_W=4; this run elaborates "
                                       f"PARA_AXI_ID_W={W}, so only that width's ID range is checked")
    mx = (1 << W) - 1
    ids = [0, mx, 0x5555 & mx, 0xAAAA & mx, 0x5555 & mx, 0xAAAA & mx] + [r.getrandbits(W) for _ in range(12)]
    b.rd.rready_delay = lambda: r.randint(0, 2)
    b.wr.bready_delay = lambda: r.randint(0, 2)
    reqs = []
    for i, idv in enumerate(ids):
        for kind in r.sample(["R", "W"], 2):
            cache = 2 if r.random() < 0.3 else r.choice([0, 1])
            ln = r.randint(0, 7)
            addr = 0x6800 + 0x40 * i
            if kind == "R":
                reqs.append(b.rd.req(addr=addr, ln=ln, size=2, burst=INCR, cache=cache, id=idv))
            else:
                reqs.append(b.wr.req(addr=addr, ln=ln, size=2, burst=INCR, cache=cache, id=idv))
    await b.drain(30000, "CHK-030: all ID transactions complete")
    nunsup = 0
    for q in reqs:
        t = b.txn(q)
        assert t is not None and t.done is not None and not t.aborted, "CHK-030: transaction completes"
        assert t.id == q.id, f"CHK-030: captured ID {q.id} got {t.id}"
        nunsup += (not t.supported)
        if q.kind == "R":
            assert len(t.r) == q.len + 1 and all(bt["id"] == q.id for bt in t.r), \
                f"CHK-030: rid={q.id} on every beat got {[bt['id'] for bt in t.r]}"
        else:
            assert t.b["id"] == q.id, f"CHK-030: bid={q.id} got {t.b['id']} (resp {t.b['resp']})"
    assert nunsup > 0, "CHK-030: unsupported requests included in the mix"
    b.final()


async def _post_reset_checks(b, last_rst, tag):
    s = b.snap(last_rst + 1)
    assert s is not None, "CHK-031: edge after reset sampled"
    for k in RESET_ZERO:
        assert s[k] == 0, f"CHK-031: {k}=0 at edge after reset ({tag}) got {s[k]}"
    await b.wait_for(lambda: b.cycle >= last_rst + 20, 40, f"CHK-031: 20 idle cycles after reset ({tag})")
    for e in range(last_rst + 1, last_rst + 21):
        s = b.snap(e)
        assert s["psel"] == 0 and s["rvalid"] == 0 and s["bvalid"] == 0, \
            f"CHK-031: no replay ({tag}): psel/rvalid/bvalid=0 at edge {e} got {s['psel']}/{s['rvalid']}/{s['bvalid']}"


async def _tie_after_reset(b, tag):
    t0 = b.cycle + 2
    rq = b.rd.req(addr=0x7400, ln=1, size=2, burst=INCR, not_before=t0)
    wq = b.wr.req(addr=0x7500, ln=1, size=2, burst=INCR, aw_not_before=t0)
    await b.wait_done(rq, wq, max_cycles=2000, what=f"CHK-031: post-reset tie completes ({tag})")
    assert rq.first_valid == wq.first_valid, "CHK-031: AR and AW asserted at the same edge"
    assert rq.hs_edge < wq.hs_edge, f"CHK-031: AR wins first tie after reset ({tag}) got AR={rq.hs_edge} AW={wq.hs_edge}"
    b.score()


@cocotb.test()
async def test_chk_031_reset_mid_transaction(dut):
    """CHK-031, CHK-017: reset mid-transaction cancels work, deselects APB, no replay, AR preference restored."""
    b = await make_bench(dut, "chk031")
    # (d) complete one transaction so the preference becomes AW
    w0 = b.wr.req(addr=0x7800, ln=0, size=2, burst=INCR)
    await b.wait_done(w0, max_cycles=300, what="CHK-031: preliminary write completes")
    # (a) reset during beat 1 ACCESS with PREADY=0
    b.apb.wait_fn = lambda x: 100000 if (x["paddr"] == 0x7004 and x["pwrite"] != 1) else 0
    rq = b.rd.req(addr=0x7000, ln=3, size=2, burst=INCR)
    await b.wait_for(lambda: b.last["psel"] == 1 and b.last["penable"] == 1 and b.last["paddr"] == 0x7004,
                     300, "CHK-031: (a) read reaches beat 1 ACCESS")
    await b.cycles(5)
    assert b.last["penable"] == 1 and b.last["pready"] == 0, "CHK-031: (a) ACCESS waiting with PREADY=0 before reset"
    _, last = await b.reset(1)
    b.apb.wait_fn = lambda x: 0
    t = b.txn(rq)
    assert t.aborted, "CHK-031: (a) interrupted read is cancelled"
    await _post_reset_checks(b, last, "a")
    await _tie_after_reset(b, "a")
    # (b) reset while rvalid=1 and rready=0
    b.rd.rready_delay = lambda: 100000
    rq = b.rd.req(addr=0x7200, ln=7, size=2, burst=INCR)
    await b.wait_for(lambda: b.last["rvalid"] == 1, 300, "CHK-031: (b) rvalid rises")
    await b.cycles(3)
    assert b.last["rvalid"] == 1 and b.last["rready"] == 0, "CHK-031: (b) R beat stalled before reset"
    _, last = await b.reset(1)
    b.rd.rready_delay = lambda: 0
    await _post_reset_checks(b, last, "b")
    await _tie_after_reset(b, "b")
    # make preference AW again before (c)
    w1 = b.wr.req(addr=0x7900, ln=0, size=2, burst=INCR)
    await b.wait_done(w1, max_cycles=300, what="CHK-031: lone write before (c) completes")
    # (c) reset after 2 of 4 W beats
    wq = b.wr.req(addr=0x7300, ln=3, size=2, burst=INCR, w_stop_after=2)
    await b.wait_for(lambda: len(wq.w_edges) >= 2, 300, "CHK-031: (c) 2 W beats accepted")
    await b.cycles(3)
    _, last = await b.reset(1)
    await _post_reset_checks(b, last, "c")
    await _tie_after_reset(b, "c")
    b.final()
    b.compare_mem("CHK-031")


@cocotb.test()
async def test_regression_random(dut):
    """CHK-001, CHK-002, CHK-003, CHK-004, CHK-005, CHK-006, CHK-007, CHK-008, CHK-009, CHK-010, CHK-011,
    CHK-012, CHK-013, CHK-014, CHK-015, CHK-016, CHK-017: broad random regression with scoreboard."""
    b = await make_bench(dut, "regression")
    r = b.rnd
    set_random_policies(b, r)
    n = int(os.environ.get("NNC_N_REGR", "800"))
    await random_traffic(b, r, n, "regression", extras=True)
    # directed extras so that error/unsupported assertions are always exercised
    b.apb.err_fn = lambda x: x["paddr"] == 0xFF00
    qs = [b.rd.req(addr=0x3400, ln=2, size=2, burst=INCR, cache=2),
          b.wr.req(addr=0x3500, ln=2, size=2, burst=INCR, cache=5),
          b.rd.req(addr=UNMAPPED_BASE + 0x40, ln=1, size=2, burst=INCR),
          b.wr.req(addr=UNMAPPED_BASE + 0x80, ln=1, size=2, burst=INCR),
          b.rd.req(addr=0xFF00, ln=1, size=2, burst=INCR),
          b.wr.req(addr=0xFF00, ln=1, size=2, burst=INCR)]
    await b.wait_done(*qs, max_cycles=5000, what="regression: directed extras complete")
    _, last = await b.reset(2)
    s = b.snap(last + 1)
    for k in RESET_ZERO:
        assert s[k] == 0, f"CHK-017: {k}=0 after reset got {s[k]}"
    await b.drain(1000, "regression: idle after final reset")
    b.final()
    b.compare_mem("regression")
    assert len(b.reset_edges) >= 2, "CHK-017: resets exercised in regression"

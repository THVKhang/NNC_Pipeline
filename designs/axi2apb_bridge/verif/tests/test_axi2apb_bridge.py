"""
cocotb 2.1 testbench for m_axi2apb_bridge (AXI4 Subordinate -> APB4 Manager bridge).

Architecture
  * Bench          : one cycle engine. At every falling edge it lets every model drive its inputs, then
                     waits for ReadOnly and samples all ports. Those sampled values are exactly the values the
                     next rising edge sees ("edge N"). Then every monitor/model observes the sample.
  * AxiMaster      : AR / AW / W requester driver plus R / B receivers with configurable READY policies.
  * ApbCompleter   : APB4 completer with a byte-addressed memory, random/directed wait states, optional
                     PSLVERR injection, optional default completer for unmapped addresses, and noise on
                     PRDATA/PSLVERR while PREADY=0 (the spec says these are ignored then).
  * Tracker        : transaction tracker / scoreboard (CHK-014 owner model) with Python versions of the
                     assertion checks CHK-001..CHK-017. It uses an independent reference model (beat-address
                     formula, support classification, byte-addressed reference memory) built from the spec.
"""
import inspect
from collections import deque

import cocotb
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge

from nnc_cocotb import *  # noqa: F401,F403

# --------------------------------------------------------------------------------------------------
# Constants (AXI4 encodings, see plan assumptions)
# --------------------------------------------------------------------------------------------------
OKAY = 0
SLVERR = 2
FIXED, INCR, WRAP, RSVD = 0, 1, 2, 3
M32 = 0xFFFFFFFF


def _param(name, default):
    try:
        return int(PARAMS.get(name, default))
    except Exception:
        return default


IDW = _param("PARA_AXI_ID_W", 4)
ID_MASK = (1 << IDW) - 1

IN_PORTS = [
    "i_axi_awid", "i_axi_awaddr", "i_axi_awlen", "i_axi_awsize", "i_axi_awburst", "i_axi_awcache",
    "i_axi_awprot", "i_axi_awvalid",
    "i_axi_wdata", "i_axi_wstrb", "i_axi_wlast", "i_axi_wvalid", "i_axi_bready",
    "i_axi_arid", "i_axi_araddr", "i_axi_arlen", "i_axi_arsize", "i_axi_arburst", "i_axi_arcache",
    "i_axi_arprot", "i_axi_arvalid", "i_axi_rready",
    "i_apb_pready", "i_apb_prdata", "i_apb_pslverr",
]
OUT_PORTS = [
    "o_axi_awready", "o_axi_wready", "o_axi_bid", "o_axi_bresp", "o_axi_bvalid",
    "o_axi_arready", "o_axi_rid", "o_axi_rdata", "o_axi_rresp", "o_axi_rlast", "o_axi_rvalid",
    "o_apb_paddr", "o_apb_pwrite", "o_apb_pwdata", "o_apb_pstrb", "o_apb_pprot", "o_apb_psel",
    "o_apb_penable",
]
RESET_ZERO = ["bvalid", "rvalid", "bid", "bresp", "rid", "rdata", "rresp", "rlast",
              "psel", "penable", "paddr", "pwrite", "pwdata", "pstrb", "pprot"]
READIES = ("awready", "wready", "arready")
PAY = ("paddr", "pwrite", "pwdata", "pstrb", "pprot")


def _short(n):
    return n.split("_", 2)[2]


def _hx(v):
    return f"{v:#x}" if isinstance(v, int) and v >= 0 else repr(v)


# --------------------------------------------------------------------------------------------------
# Reference model (derived only from the specification text)
# --------------------------------------------------------------------------------------------------
def beat_addrs(addr, size, length, burst):
    """CHK-016 beat-address formula."""
    S = 1 << size
    n = length + 1
    if burst == FIXED:
        return [addr] * n
    if burst == INCR:
        base = addr & ~(S - 1) & M32
        return [addr] + [(base + k * S) & M32 for k in range(1, n)]
    if burst == WRAP:
        T = S * n
        lower = (addr // T) * T
        return [lower + ((addr - lower + k * S) % T) for k in range(n)]
    return [addr] * n


def crosses_4k(addr, size, length):
    S = 1 << size
    end = ((addr & ~(S - 1)) + (length + 1) * S - 1) & M32
    return (addr >> 12) != (end >> 12)


def is_supported(addr, length, size, burst, cache):
    if size > 2:
        return False
    if burst == RSVD:
        return False
    if cache not in (0, 1):
        return False
    if burst == INCR and crosses_4k(addr, size, length):
        return False
    return True


def legal_lanes(addr, size):
    """Byte lanes legal for a beat at addr with 2**size bytes (32-bit bus)."""
    S = 1 << size
    lo = addr & 3
    hi = ((addr & ~(S - 1)) & 3) + S - 1
    m = 0
    for i in range(lo, hi + 1):
        m |= 1 << i
    return m


def init_byte(a):
    return ((a * 2654435761) >> 13) & 0xFF


class RefMemory:
    """Byte-addressed memory (used both as APB completer storage and as independent reference)."""

    def __init__(self):
        self.m = {}

    def rd_byte(self, a):
        return self.m.get(a, init_byte(a))

    def rd_word(self, a):
        a &= 0xFFFFFFFC
        return sum(self.rd_byte(a + i) << (8 * i) for i in range(4))

    def wr(self, a, data, strb):
        a &= 0xFFFFFFFC
        for i in range(4):
            if (strb >> i) & 1:
                self.m[a + i] = (data >> (8 * i)) & 0xFF


# --------------------------------------------------------------------------------------------------
# Transactions
# --------------------------------------------------------------------------------------------------
class Txn:
    def __init__(self, kind, axid, addr, length, size=2, burst=INCR, cache=0, prot=0,
                 data=None, strb=None, delay=0, w_delay=None, w_gaps=None):
        self.kind = kind
        self.id = axid & ID_MASK
        self.addr = addr & M32
        self.length = length
        self.size = size
        self.burst = burst
        self.cache = cache
        self.prot = prot
        self.data = list(data) if data else []
        self.strb = list(strb) if strb else []
        self.delay = delay
        self.w_delay = delay if w_delay is None else w_delay
        self.w_gaps = list(w_gaps) if w_gaps else [0] * (length + 1)
        self.not_before = None
        self.w_not_before = None
        self.w_next = 0
        self.valid_cycle = None
        self.w_valid_cycle = None
        self.a_hs = None
        self.w_hs = []
        self.r = []
        self.b = None
        self.done = False
        self.aborted = False
        self.end = None
        self.rec = None

    @property
    def supported(self):
        return is_supported(self.addr, self.length, self.size, self.burst, self.cache)

    def __repr__(self):
        return (f"{self.kind}(id={self.id:#x}, addr={self.addr:#010x}, len={self.length}, size={self.size}, "
                f"burst={self.burst}, cache={self.cache:#x}, prot={self.prot})")


def make_read(axid, addr, length, size=2, burst=INCR, cache=0, prot=0, delay=0):
    return Txn("R", axid, addr, length, size, burst, cache, prot, delay=delay)


def make_write(r, axid, addr, length, size=2, burst=INCR, cache=0, prot=0, data=None, strb=None,
               delay=0, w_delay=None, w_gaps=None):
    n = length + 1
    if data is None:
        data = [r.getrandbits(32) for _ in range(n)]
    if strb is None:
        if size <= 2 and burst in (FIXED, INCR, WRAP):
            strb = []
            for a in beat_addrs(addr & M32, size, length, burst):
                full = legal_lanes(a, size)
                strb.append(full if r.random() < 0.6 else (r.getrandbits(4) & full))
        else:
            strb = [0xF] * n
    return Txn("W", axid, addr, length, size, burst, cache, prot, data=data, strb=strb,
               delay=delay, w_delay=w_delay, w_gaps=w_gaps)


def rand_legal(r, kind, top=0x10000):
    burst = r.choice([FIXED, INCR, WRAP])
    size = r.randint(0, 2)
    S = 1 << size
    if burst == FIXED:
        L = r.randint(0, 15)
    elif burst == WRAP:
        L = r.choice([1, 3, 7, 15])
    else:
        x = r.random()
        if x < 0.65:
            L = r.randint(0, 15)
        elif x < 0.9:
            L = r.randint(16, 63)
        else:
            L = r.randint(64, 255)
    addr = 0
    ok = False
    for _ in range(200):
        addr = r.randrange(0, top)
        if burst == WRAP:
            addr &= ~(S - 1)
        if burst == INCR and crosses_4k(addr, size, L):
            continue
        ok = True
        break
    if not ok:
        addr &= ~0xFFF
    axid = r.randint(0, ID_MASK)
    cache = r.choice([0, 1])
    prot = r.randint(0, 7)
    if kind == "R":
        return make_read(axid, addr, L, size, burst, cache, prot)
    return make_write(r, axid, addr, L, size, burst, cache, prot)


# --------------------------------------------------------------------------------------------------
# READY policies (RREADY / BREADY)
# --------------------------------------------------------------------------------------------------
class ReadyPolicy:
    def __init__(self, r):
        self.r = r
        self.set("always")

    def set(self, mode, p=0.7, lo=0, hi=0):
        self.mode = mode
        self.p = p
        self.lo = lo
        self.hi = hi
        self.left = self.r.randint(lo, hi) if mode == "hold" else 0

    def value(self):
        m = self.mode
        if m == "always":
            return 1
        if m == "never":
            return 0
        if m == "random":
            return 1 if self.r.random() < self.p else 0
        return 1 if self.left <= 0 else 0

    def observe(self, valid, ready):
        if self.mode != "hold":
            return
        if valid == 1 and ready == 1:
            self.left = self.r.randint(self.lo, self.hi)
        elif valid == 1:
            self.left -= 1


# --------------------------------------------------------------------------------------------------
# AXI requester (driver + response receivers)
# --------------------------------------------------------------------------------------------------
class AxiMaster:
    A_F = ("id", "addr", "len", "size", "burst", "cache", "prot")
    WIDTH = dict(id=IDW, addr=32, len=8, size=3, burst=2, cache=4, prot=3)

    def __init__(self, bench):
        self.bench = bench
        self.r = bench.r
        d = bench.dut
        self.h = {}
        for p in ("ar", "aw"):
            for f in self.A_F:
                self.h[p + f] = getattr(d, f"i_axi_{p}{f}")
            self.h[p + "valid"] = getattr(d, f"i_axi_{p}valid")
        for n in ("wdata", "wstrb", "wlast", "wvalid", "rready", "bready"):
            self.h[n] = getattr(d, "i_axi_" + n)
        self.ar_q = deque()
        self.aw_q = deque()
        self.w_q = deque()
        self.rd_out = deque()
        self.wr_out = deque()
        self.rready = ReadyPolicy(self.r)
        self.bready = ReadyPolicy(self.r)
        self.all = []
        self.stray_r = []
        self.stray_b = []

    def submit(self, t, base):
        t.not_before = base + t.delay
        if t.kind == "R":
            self.ar_q.append(t)
        else:
            t.w_not_before = base + t.w_delay
            self.aw_q.append(t)
            self.w_q.append(t)
        self.all.append(t)

    def _drive_addr(self, p, q, c, in_rst):
        t = q[0] if q else None
        if (not in_rst) and t is not None and c >= t.not_before:
            if t.valid_cycle is None:
                t.valid_cycle = c
            vals = dict(id=t.id, addr=t.addr, len=t.length & 0xFF, size=t.size & 7,
                        burst=t.burst & 3, cache=t.cache & 0xF, prot=t.prot & 7)
            for f in self.A_F:
                self.h[p + f].value = vals[f]
            self.h[p + "valid"].value = 1
        else:
            self.h[p + "valid"].value = 0
            if self.r.random() < 0.3:  # payload is "ignored if VALID=0": drive noise
                for f in self.A_F:
                    self.h[p + f].value = self.r.getrandbits(self.WIDTH[f])

    def drive(self, c, in_rst):
        self._drive_addr("ar", self.ar_q, c, in_rst)
        self._drive_addr("aw", self.aw_q, c, in_rst)
        t = self.w_q[0] if self.w_q else None
        if (not in_rst) and t is not None and c >= t.w_not_before and c >= t.w_next:
            k = len(t.w_hs)
            if t.w_valid_cycle is None:
                t.w_valid_cycle = c
            self.h["wdata"].value = t.data[k] & M32
            self.h["wstrb"].value = t.strb[k] & 0xF
            self.h["wlast"].value = 1 if k == t.length else 0
            self.h["wvalid"].value = 1
        else:
            self.h["wvalid"].value = 0
            if self.r.random() < 0.3:
                self.h["wdata"].value = self.r.getrandbits(32)
                self.h["wstrb"].value = self.r.getrandbits(4)
                self.h["wlast"].value = self.r.getrandbits(1)
        self.h["rready"].value = self.rready.value()
        self.h["bready"].value = self.bready.value()

    def observe(self, c, s):
        if s["rst"] != 1:
            for q in (self.ar_q, self.aw_q, self.w_q, self.rd_out, self.wr_out):
                for t in q:
                    if not t.done:
                        t.aborted = True
                q.clear()
            return
        if s["arvalid"] == 1 and s["arready"] == 1 and self.ar_q:
            t = self.ar_q.popleft()
            t.a_hs = c
            t.rec = self.bench.tracker.cur
            self.rd_out.append(t)
        if s["awvalid"] == 1 and s["awready"] == 1 and self.aw_q:
            t = self.aw_q.popleft()
            t.a_hs = c
            t.rec = self.bench.tracker.cur
            self.wr_out.append(t)
        if s["wvalid"] == 1 and s["wready"] == 1 and self.w_q:
            t = self.w_q[0]
            k = len(t.w_hs)
            t.w_hs.append(c)
            t.w_next = c + 1 + (t.w_gaps[k] if k < len(t.w_gaps) else 0)
            if len(t.w_hs) == t.length + 1:
                self.w_q.popleft()
        if s["rvalid"] == 1 and s["rready"] == 1:
            beat = dict(data=s["rdata"], resp=s["rresp"], id=s["rid"], last=s["rlast"], cycle=c)
            if self.rd_out:
                t = self.rd_out[0]
                t.r.append(beat)
                if beat["last"] == 1:
                    t.done = True
                    t.end = c
                    self.rd_out.popleft()
            else:
                self.stray_r.append(beat)
        self.rready.observe(s["rvalid"], s["rready"])
        if s["bvalid"] == 1 and s["bready"] == 1:
            bb = dict(resp=s["bresp"], id=s["bid"], cycle=c)
            if self.wr_out:
                t = self.wr_out.popleft()
                t.b = bb
                t.done = True
                t.end = c
            else:
                self.stray_b.append(bb)
        self.bready.observe(s["bvalid"], s["bready"])


# --------------------------------------------------------------------------------------------------
# APB completer (memory model / default completer)
# --------------------------------------------------------------------------------------------------
class ApbCompleter:
    def __init__(self, bench):
        self.bench = bench
        self.r = bench.r
        d = bench.dut
        self.h_pready = d.i_apb_pready
        self.h_prdata = d.i_apb_prdata
        self.h_pslverr = d.i_apb_pslverr
        self.mem = RefMemory()
        self.wait_fn = None
        self.resp_fn = None
        self.wmin = 0
        self.wmax = 0
        self.err_prob = 0.0
        self.unmapped_default = False
        self.noise = True
        self.cur = None
        self.log = []
        self.count = 0

    def _unmapped(self, addr):
        return self.unmapped_default and not (0 <= addr <= 0xFFFF)

    def default_resp(self, tr):
        if self._unmapped(tr["addr"]):
            return (0x5A5A5A5A, 1)
        if tr["write"]:
            prdata = self.r.getrandbits(32)
        else:
            prdata = self.mem.rd_word(tr["addr"])
        err = 1 if (self.err_prob > 0 and self.r.random() < self.err_prob) else 0
        return prdata, err

    def drive(self, c, in_rst):
        t = self.cur
        if (not in_rst) and t is not None and t["left"] <= 0:
            self.h_pready.value = 1
            self.h_prdata.value = t["prdata"] & M32
            self.h_pslverr.value = t["pslverr"] & 1
        else:
            self.h_pready.value = 0
            if self.noise:
                self.h_prdata.value = self.r.getrandbits(32)
                self.h_pslverr.value = self.r.getrandbits(1)
            else:
                self.h_prdata.value = 0
                self.h_pslverr.value = 0

    def observe(self, c, s):
        if s["rst"] != 1:
            self.cur = None
            return
        t = self.cur
        if s["psel"] == 1 and s["penable"] == 1 and t is not None:
            t["edges"] += 1
            if s["pready"] == 1:
                self.cur = None
                if s["pwrite"] == 1 and s["pslverr"] == 0:
                    self.mem.wr(s["paddr"], s["pwdata"], s["pstrb"])
                self.log.append(t)
                assert t["edges"] == t["waits"] + 1, (
                    f"CHK-027: a transfer with {t['waits']} wait states has {t['waits'] + 1} ACCESS edges, "
                    f"got {t['edges']} (paddr {_hx(t['addr'])}, cycle {c})")
            else:
                t["left"] -= 1
        elif s["psel"] == 1 and s["penable"] == 0:
            tr = dict(idx=self.count, addr=s["paddr"], write=s["pwrite"], prot=s["pprot"], setup=c, edges=0)
            self.count += 1
            if self._unmapped(tr["addr"]):
                waits = 0
            elif self.wait_fn is not None:
                waits = self.wait_fn(tr)
            else:
                waits = self.r.randint(self.wmin, self.wmax)
            if self.resp_fn is not None:
                prdata, err = self.resp_fn(tr)
            else:
                prdata, err = self.default_resp(tr)
            tr.update(waits=waits, left=waits, prdata=prdata, pslverr=err)
            self.cur = tr


# --------------------------------------------------------------------------------------------------
# Transaction tracker / scoreboard (CHK-001..CHK-017 in Python + reference model)
# --------------------------------------------------------------------------------------------------
class Tracker:
    def __init__(self, bench):
        self.bench = bench
        self.owner = None
        self.cur = None
        self.prev = None
        self.records = []
        self.aborted = []
        self.post_reset = []

    def _new(self, kind, s, c):
        p = "ar" if kind == "RD" else "aw"
        rec = dict(kind=kind, id=s[p + "id"], addr=s[p + "addr"], len=s[p + "len"], size=s[p + "size"],
                   burst=s[p + "burst"], cache=s[p + "cache"], prot=s[p + "prot"], start=c,
                   apb=[], w=[], r=[], b=None, end=None, psel_edges=0,
                   first_rvalid=None, first_bvalid=None)
        rec["supported"] = is_supported(rec["addr"], rec["len"], rec["size"], rec["burst"], rec["cache"])
        rec["exp_addrs"] = (beat_addrs(rec["addr"], rec["size"], rec["len"], rec["burst"])
                            if rec["supported"] else [])
        return rec

    def observe(self, c, s):
        p = self.prev
        self.prev = s
        assert s["paddr"] >= 0 and (s["paddr"] & 3) == 0, (
            f"CHK-004: o_apb_paddr[1:0]==2'b00 at every edge, got paddr={_hx(s['paddr'])} at cycle {c}")
        if p is not None and p["rst"] == 0:
            bad = [(n, _hx(s[n])) for n in RESET_ZERO if s[n] != 0]
            assert not bad, f"CHK-017: all response/APB outputs 0 at the edge after a reset edge, got {bad} at cycle {c}"
            if s["rst"] == 0:
                badr = [(n, _hx(s[n])) for n in READIES if s[n] != 0]
                assert not badr, f"CHK-017: ready outputs 0 when reset is sampled at two consecutive edges, got {badr} at cycle {c}"
            else:
                self.post_reset.append((c, s))
        if s["rst"] != 1:
            if self.cur is not None:
                self.cur["aborted_at"] = c
                self._commit_completed_writes(self.cur)
                self.aborted.append(self.cur)
            self.cur = None
            self.owner = None
            return
        prst = p is not None and p["rst"] == 1
        if s["penable"] == 1:
            assert s["psel"] == 1, f"CHK-001: penable=1 implies psel=1, got psel={s['psel']} at cycle {c}"
        if prst:
            p_setup = p["psel"] == 1 and p["penable"] == 0
            p_access = p["psel"] == 1 and p["penable"] == 1
            if p_setup:
                assert s["psel"] == 1 and s["penable"] == 1, (
                    f"CHK-001: SETUP is followed by ACCESS, got psel={s['psel']} penable={s['penable']} at cycle {c}")
                diff = [f for f in PAY if s[f] != p[f]]
                assert not diff, f"CHK-003: APB payload stable from SETUP into ACCESS, changed {diff} at cycle {c}"
            if p_access and p["pready"] == 1:
                assert s["penable"] == 0, f"CHK-001: penable=0 after a completed ACCESS, got 1 at cycle {c}"
            if p_access and p["pready"] == 0:
                assert s["psel"] == 1 and s["penable"] == 1, (
                    f"CHK-002: ACCESS held while PREADY=0, got psel={s['psel']} penable={s['penable']} at cycle {c}")
                diff = [f for f in PAY if s[f] != p[f]]
                assert not diff, f"CHK-002: APB payload held during wait state, changed {diff} at cycle {c}"
            if s["penable"] == 1:
                assert p["psel"] == 1 and not (p_access and p["pready"] == 1), (
                    f"CHK-001: ACCESS entered only from SETUP or waited ACCESS (cycle {c})")
            if p["bvalid"] == 1 and p["bready"] == 0:
                assert s["bvalid"] == 1 and s["bid"] == p["bid"] and s["bresp"] == p["bresp"], (
                    f"CHK-007: B held under BREADY=0, got bvalid={s['bvalid']} bid={_hx(s['bid'])}/{_hx(p['bid'])} "
                    f"bresp={s['bresp']}/{p['bresp']} at cycle {c}")
            if p["rvalid"] == 1 and p["rready"] == 0:
                diff = [f for f in ("rvalid", "rid", "rdata", "rresp", "rlast") if s[f] != p[f]]
                assert not diff, f"CHK-009: R beat held under RREADY=0, changed {diff} at cycle {c}"
        if s["psel"] == 1 and s["pwrite"] == 0:
            assert s["pstrb"] == 0, f"CHK-005: pstrb=0 on APB reads, got {_hx(s['pstrb'])} at cycle {c}"
        if s["psel"] == 0:
            bad = [(f, _hx(s[f])) for f in ("penable",) + PAY if s[f] != 0]
            assert not bad, f"CHK-006: APB outputs 0 when psel=0, got {bad} at cycle {c}"
        self._track(c, s)

    def _track(self, c, s):
        start_owner = self.owner
        cur = self.cur
        ar_hs = s["arvalid"] == 1 and s["arready"] == 1
        aw_hs = s["awvalid"] == 1 and s["awready"] == 1
        # (a) APB ACCESS edge belongs to the current owner
        if s["psel"] == 1 and s["penable"] == 1:
            assert cur is not None, f"CHK-014: psel=1 (ACCESS) only while a transaction owns the bridge, got no owner at cycle {c}"
            assert cur["supported"], f"CHK-015: no APB activity for unsupported request, got psel=1 at cycle {c}"
            assert cur["apb"] and cur["apb"][-1]["done"] is None, f"CHK-001: ACCESS without an open SETUP at cycle {c}"
            cur["psel_edges"] += 1
            tr = cur["apb"][-1]
            tr["access_edges"] += 1
            for f in PAY:
                if s[f] != tr["vals"][f]:
                    tr["stable"] = False
            if s["pready"] == 1:
                k = len(cur["apb"]) - 1
                tr["done"] = c
                tr["prdata"] = s["prdata"]
                tr["pslverr"] = s["pslverr"]
                exp_w = 1 if cur["kind"] == "WR" else 0
                assert s["pwrite"] == exp_w, f"CHK-016: pwrite={exp_w} for transfer {k}, got {s['pwrite']} at cycle {c}"
                ea = cur["exp_addrs"][k] & 0xFFFFFFFC
                assert s["paddr"] == ea, f"CHK-016: paddr of transfer {k} = {ea:#010x}, got {_hx(s['paddr'])} at cycle {c}"
                assert s["pprot"] == cur["prot"], f"CHK-016: pprot = AxPROT {cur['prot']}, got {_hx(s['pprot'])} at cycle {c}"
        # (b) responses of the current owner
        completed = None
        if s["rvalid"] == 1:
            assert self.owner == "RD" and cur is not None, (
                f"CHK-014: rvalid=1 only while a read owns the bridge (after its AR handshake), owner={self.owner} at cycle {c}")
            k = len(cur["r"])
            if cur["first_rvalid"] is None:
                cur["first_rvalid"] = c
            assert s["rid"] == cur["id"], f"CHK-010: rid = ARID {cur['id']:#x}, got {_hx(s['rid'])} at cycle {c}"
            exp_last = 1 if k == cur["len"] else 0
            assert s["rlast"] == exp_last, f"CHK-010: rlast={exp_last} on beat {k} of ARLEN={cur['len']}, got {s['rlast']} at cycle {c}"
            if cur["supported"]:
                ndone = sum(1 for t in cur["apb"] if t["done"] is not None)
                assert ndone >= k + 1, f"CHK-011: R beat {k} only after {k + 1} APB completions, got {ndone} at cycle {c}"
                t = cur["apb"][k]
                if t["pslverr"] == 0:
                    assert s["rresp"] == OKAY and s["rdata"] == t["prdata"], (
                        f"CHK-011: beat {k} OKAY with rdata=prdata {_hx(t['prdata'])}, got rresp={s['rresp']} "
                        f"rdata={_hx(s['rdata'])} at cycle {c}")
                    if self.bench.ref_check:
                        exp = self.bench.ref.rd_word(cur["exp_addrs"][k])
                        assert s["rdata"] == exp, (
                            f"CHK-027: read beat {k} data equals reference memory {exp:#010x}, got {_hx(s['rdata'])} "
                            f"(addr {cur['exp_addrs'][k]:#010x}, cycle {c})")
                else:
                    assert s["rresp"] == SLVERR and s["rdata"] == 0, (
                        f"CHK-011: beat {k} with PSLVERR returns SLVERR and rdata=0, got rresp={s['rresp']} "
                        f"rdata={_hx(s['rdata'])} at cycle {c}")
            else:
                assert s["rresp"] == SLVERR and s["rdata"] == 0, (
                    f"CHK-012: unsupported read beat is SLVERR with rdata=0, got rresp={s['rresp']} rdata={_hx(s['rdata'])} at cycle {c}")
            if s["rready"] == 1:
                cur["r"].append(dict(data=s["rdata"], resp=s["rresp"], id=s["rid"], last=s["rlast"], cycle=c))
                if s["rlast"] == 1:
                    completed = cur
        if s["bvalid"] == 1:
            assert self.owner == "WR" and cur is not None, (
                f"CHK-014: bvalid=1 only while a write owns the bridge, owner={self.owner} at cycle {c}")
            if cur["first_bvalid"] is None:
                cur["first_bvalid"] = c
            assert s["bid"] == cur["id"], f"CHK-008: bid = AWID {cur['id']:#x}, got {_hx(s['bid'])} at cycle {c}"
            nw = len(cur["w"])
            assert nw == cur["len"] + 1, f"CHK-008: bvalid only after AWLEN+1={cur['len'] + 1} W handshakes, got {nw} at cycle {c}"
            if cur["supported"]:
                done_before = [t for t in cur["apb"] if t["done"] is not None and t["done"] < c]
                assert len(done_before) == cur["len"] + 1, (
                    f"CHK-008: bvalid only after AWLEN+1={cur['len'] + 1} APB write completions, got {len(done_before)} at cycle {c}")
                exp = SLVERR if any(t["pslverr"] == 1 for t in done_before) else OKAY
                assert s["bresp"] == exp, f"CHK-008: bresp={exp} from accumulated PSLVERR, got {s['bresp']} at cycle {c}"
            else:
                assert s["bresp"] == SLVERR, f"CHK-008: unsupported write bresp=SLVERR, got {s['bresp']} at cycle {c}"
            if s["bready"] == 1:
                cur["b"] = dict(resp=s["bresp"], id=s["bid"], cycle=c)
                completed = cur
        if completed is not None:
            self.owner = None
            self.cur = None
            self._finish(completed, c)
        # (c) address handshakes
        assert not (ar_hs and aw_hs), f"CHK-014: AR and AW handshakes never at the same edge (cycle {c})"
        if ar_hs or aw_hs:
            assert self.owner is None, f"CHK-014: no address handshake while {self.owner} owns the bridge (cycle {c})"
            self.owner = "RD" if ar_hs else "WR"
            self.cur = self._new(self.owner, s, c)
        cur = self.cur
        # (d) W channel
        if s["wready"] == 1:
            assert self.owner == "WR" or start_owner == "WR", (
                f"CHK-013: wready=1 only after the AW of the current write is accepted, owner={self.owner} at cycle {c}")
        if s["wvalid"] == 1 and s["wready"] == 1:
            assert self.owner == "WR" and cur is not None, f"CHK-013: W handshake only for an accepted write (cycle {c})"
            cur["w"].append(dict(data=s["wdata"], strb=s["wstrb"], last=s["wlast"], cycle=c))
            assert len(cur["w"]) <= cur["len"] + 1, (
                f"CHK-013: W handshakes never exceed AWLEN+1={cur['len'] + 1}, got {len(cur['w'])} at cycle {c}")
        # (e) APB SETUP edge
        if s["psel"] == 1 and s["penable"] == 0:
            assert cur is not None, f"CHK-014: psel=1 only while a transaction owns the bridge (cycle {c})"
            assert cur["supported"], f"CHK-015: no APB SETUP for an unsupported request (cycle {c})"
            assert len(cur["apb"]) < cur["len"] + 1, (
                f"CHK-016: APB transfers per transaction never exceed AxLEN+1={cur['len'] + 1} (cycle {c})")
            cur["psel_edges"] += 1
            cur["apb"].append(dict(setup=c, vals={f: s[f] for f in PAY}, access_edges=0, done=None,
                                   stable=True, prdata=None, pslverr=None))

    def _commit_completed_writes(self, rec):
        # Triage fix (2026-11-10, NNC_Pipeline): a write cut by reset keeps the APB writes that already
        # completed (one APB write per beat, spec:163/317/328; no rollback, spec:333/575/584). The reference
        # model records them here, with the same pwdata/pstrb = W beat check as _finish.
        if rec.get("kind") != "WR" or not rec.get("supported"):
            return
        for k, tr in enumerate(rec["apb"]):
            if tr["done"] is None or tr["pslverr"] != 0:
                continue
            assert k < len(rec["w"]), f"CHK-016: APB write {k} completed before W beat {k} was accepted"
            w = rec["w"][k]
            assert tr["vals"]["pwdata"] == w["data"] and tr["vals"]["pstrb"] == w["strb"], (
                f"CHK-016: transfer {k} pwdata/pstrb = W beat {k} ({w['data']:#010x}/{w['strb']:#x}), got "
                f"{_hx(tr['vals']['pwdata'])}/{_hx(tr['vals']['pstrb'])}")
            self.bench.ref.wr(rec["exp_addrs"][k], w["data"], w["strb"])

    def _finish(self, rec, c):
        rec["end"] = c
        L = rec["len"]
        if rec["supported"]:
            ndone = sum(1 for t in rec["apb"] if t["done"] is not None)
            assert len(rec["apb"]) == L + 1 and ndone == L + 1, (
                f"CHK-016: exactly AxLEN+1={L + 1} APB transfers, got {len(rec['apb'])} ({ndone} completed) at cycle {c}")
            if rec["kind"] == "WR":
                for k in range(L + 1):
                    tr = rec["apb"][k]
                    w = rec["w"][k]
                    assert tr["vals"]["pwdata"] == w["data"] and tr["vals"]["pstrb"] == w["strb"], (
                        f"CHK-016: transfer {k} pwdata/pstrb = W beat {k} ({w['data']:#010x}/{w['strb']:#x}), got "
                        f"{_hx(tr['vals']['pwdata'])}/{_hx(tr['vals']['pstrb'])}")
                    if tr["pslverr"] == 0:
                        self.bench.ref.wr(rec["exp_addrs"][k], w["data"], w["strb"])
        else:
            assert len(rec["apb"]) == 0, f"CHK-015: no APB transfers for an unsupported request, got {len(rec['apb'])}"
        self.records.append(rec)


# --------------------------------------------------------------------------------------------------
# Cycle engine
# --------------------------------------------------------------------------------------------------
class Bench:
    def __init__(self, dut, salt):
        self.dut = dut
        self.clk = dut.i_clk_axi
        self.r = rng(salt)
        self.cycle = 0
        self.errors = []
        self.rst_left = 0
        self.ref = RefMemory()
        self.ref_check = True
        self.hooks = []
        self.last = None
        self._handles = [(_short(n), getattr(dut, n)) for n in IN_PORTS + OUT_PORTS]
        self._rst = dut.i_rst_n_axi
        self.master = AxiMaster(self)
        self.apb = ApbCompleter(self)
        self.tracker = Tracker(self)
        self._task = None

    def start(self):
        self._task = cocotb.start_soon(self._run())

    def _err(self, msg):
        if len(self.errors) < 50:
            self.errors.append(msg)
            if len(self.errors) <= 5:
                self.dut._log.error(msg)

    def sample(self):
        s = {}
        for k, h in self._handles:
            v = val(h)
            s[k] = -1 if v is None else int(v)
        v = val(self._rst)
        s["rst"] = -1 if v is None else int(v)
        return s

    async def _run(self):
        while True:
            await FallingEdge(self.clk)
            c = self.cycle
            in_rst = self.rst_left > 0
            if in_rst:
                self.rst_left -= 1
            self._rst.value = 0 if in_rst else 1
            try:
                self.master.drive(c, in_rst)
                self.apb.drive(c, in_rst)
            except Exception as e:  # pragma: no cover
                self._err(f"TB drive error at cycle {c}: {e!r}")
            await ReadOnly()
            s = self.sample()
            for fn in (self.tracker.observe, self.apb.observe, self.master.observe) + tuple(self.hooks):
                try:
                    fn(c, s)
                except AssertionError as e:
                    self._err(str(e))
                except Exception as e:
                    self._err(f"TB internal error at cycle {c}: {e!r}")
            self.last = s
            self.cycle += 1

    # ---- test-facing API ------------------------------------------------------------------------
    def submit(self, *txns):
        base = self.cycle
        for t in txns:
            self.master.submit(t, base)

    def check(self):
        assert not self.errors, f"{self.errors[0] if self.errors else ''}  [{len(self.errors)} error(s) total]"

    async def tick(self, n=1):
        for _ in range(n):
            await RisingEdge(self.clk)
            self.check()

    async def wait_for(self, cond, max_cycles, what):
        for _ in range(max_cycles):
            if cond():
                return
            await self.tick()
        assert cond(), f"{what}: timeout after {max_cycles} cycles"

    def budget(self, txns):
        hold = max(self.master.rready.hi, 0) + max(self.master.bready.hi, 0)
        tot = 600
        for t in txns:
            gaps = sum(t.w_gaps) if t.kind == "W" else 0
            tot += 300 + (t.length + 1) * (30 + self.apb.wmax + hold) + gaps + t.delay + t.w_delay
        return tot

    async def wait_done(self, txns, max_cycles=None, what="transactions to complete"):
        if max_cycles is None:
            max_cycles = self.budget(txns)
        await self.wait_for(lambda: all(t.done or t.aborted for t in txns), max_cycles, what)
        ab = [t for t in txns if t.aborted]
        assert not ab, f"{what}: transactions unexpectedly aborted {ab[:3]}"

    async def reset(self, n=1):
        k = len(self.tracker.post_reset)
        self.rst_left = n
        await self.wait_for(lambda: len(self.tracker.post_reset) > k, n + 10, "CHK-017: reset to be applied and released")

    async def final_check(self):
        await self.tick(3)
        self.check()
        assert not self.master.stray_r, f"CHK-010: no R beat without an outstanding read, got {self.master.stray_r[:3]}"
        assert not self.master.stray_b, f"CHK-008: no B without an outstanding write, got {self.master.stray_b[:3]}"
        for a in sorted(set(self.apb.mem.m) | set(self.ref.m)):
            got = self.apb.mem.rd_byte(a)
            exp = self.ref.rd_byte(a)
            assert got == exp, f"CHK-027: APB memory byte {a:#010x} equals reference model {exp:#04x}, got {got:#04x}"


async def make_bench(dut, salt):
    res = start_clock(dut)
    if inspect.isawaitable(res):
        await res
    await reset_dut(dut, cycles=5)
    b = Bench(dut, salt)
    b.start()
    await b.tick(3)
    return b


def rid(b):
    return b.r.randint(0, ID_MASK)


def _paddrs(t):
    return [x["vals"]["paddr"] for x in t.rec["apb"]]


# ==================================================================================================
# Tests
# ==================================================================================================
@cocotb.test()
async def test_chk_018_long_apb_wait(dut):
    """CHK-018: APB ACCESS held for 1000 wait states (read then write), no timeout; pending AXI requests wait."""
    b = await make_bench(dut, "chk018")
    WAIT = 1000
    b.master.rready.set("always")
    b.master.bready.set("always")
    b.apb.wait_fn = lambda tr: WAIT if tr["idx"] in (0, 1) else 0
    b.apb.resp_fn = lambda tr: (0x0BADF00D, 0) if tr["idx"] == 0 else b.apb.default_resp(tr)
    b.ref_check = False
    resp_log = []
    b.hooks.append(lambda c, s: resp_log.append(c) if (s["rvalid"] == 1 or s["bvalid"] == 1) else None)

    rd = make_read(rid(b), 0x00005000, 0, 2, INCR, prot=b.r.randint(0, 7))
    b.submit(rd)
    await b.wait_for(lambda: rd.rec is not None and len(rd.rec["apb"]) == 1 and rd.rec["apb"][0]["access_edges"] >= 1,
                     300, "CHK-018: read transfer to reach ACCESS")
    wr = make_write(b.r, rid(b), 0x00005000, 0, 2, INCR, prot=b.r.randint(0, 7), data=[0x13579BDF], strb=[0xF])
    b.submit(wr)
    await b.wait_done([rd], WAIT + 500, "CHK-018: long-wait read to complete")
    await b.wait_for(lambda: wr.rec is not None and len(wr.rec["apb"]) == 1 and wr.rec["apb"][0]["access_edges"] >= 1,
                     500, "CHK-018: write transfer to reach ACCESS")
    rd2 = make_read(rid(b), 0x00005000, 0, 2, INCR)
    b.submit(rd2)
    await b.wait_done([wr, rd2], WAIT + 800, "CHK-018: long-wait write and following read to complete")
    await b.final_check()

    for name, t, other in (("read", rd, wr), ("write", wr, rd2)):
        assert len(t.rec["apb"]) == 1, f"CHK-018: one APB transfer for single-beat {name}, got {len(t.rec['apb'])}"
        tr = t.rec["apb"][0]
        assert tr["vals"]["paddr"] == 0x5000, f"CHK-018: {name} paddr 0x5000, got {_hx(tr['vals']['paddr'])}"
        assert tr["access_edges"] == WAIT + 1, f"CHK-018: {name} ACCESS lasts exactly {WAIT + 1} edges, got {tr['access_edges']}"
        assert tr["done"] - tr["setup"] == WAIT + 1, (
            f"CHK-018: {name} ACCESS contiguous from SETUP+1 to completion ({WAIT + 1} edges), got {tr['done'] - tr['setup']}")
        assert tr["stable"], f"CHK-018: {name} PADDR/PWRITE/PWDATA/PSTRB/PPROT unchanged during the wait"
        assert other.valid_cycle is not None and other.valid_cycle < tr["done"], (
            f"CHK-018: (stimulus) the other request is pending during the {name} wait")
        assert other.a_hs is not None and other.a_hs >= t.end, (
            f"CHK-018: pending request gets no address handshake before the {name} completes "
            f"(hs {other.a_hs}, {name} end {t.end})")
        window = [x for x in resp_log if tr["setup"] <= x < tr["done"]]
        assert not window, f"CHK-018: no rvalid/bvalid during the {name} wait, got at cycles {window[:5]}"
    assert len(rd.r) == 1 and rd.r[0]["data"] == 0x0BADF00D and rd.r[0]["resp"] == OKAY and rd.r[0]["last"] == 1, (
        f"CHK-018: read returns rdata=0x0BADF00D OKAY rlast=1, got {rd.r}")
    assert rd.r[0]["id"] == rd.id, f"CHK-018: rid={rd.id:#x}, got {_hx(rd.r[0]['id'])}"
    assert wr.b is not None and wr.b["resp"] == OKAY and wr.b["id"] == wr.id, f"CHK-018: write BRESP OKAY with bid, got {wr.b}"
    assert wr.rec["first_bvalid"] > wr.rec["apb"][0]["done"], "CHK-018: bvalid only after the write APB completion"
    assert rd2.r and rd2.r[0]["data"] == 0x13579BDF and rd2.r[0]["resp"] == OKAY, (
        f"CHK-018: the long-wait write was performed (read back 0x13579BDF), got {rd2.r}")


@cocotb.test()
async def test_chk_019_arbitration_round_robin(dut):
    """CHK-019: AR wins the first tie after reset; afterwards the side not served last wins."""
    b = await make_bench(dut, "chk019")
    b.master.rready.set("always")
    b.master.bready.set("always")
    r1 = make_read(rid(b), 0x0100, 1)
    w1 = make_write(b.r, rid(b), 0x0200, 1)
    r2 = make_read(rid(b), 0x0300, 1)
    w2 = make_write(b.r, rid(b), 0x0400, 1)
    b.submit(r1, w1, r2, w2)
    await b.wait_done([r1, w1, r2, w2], what="CHK-019: phases A-C to complete")
    assert r1.valid_cycle == w1.valid_cycle, f"CHK-019: (stimulus) R1/W1 asserted at the same edge, got {r1.valid_cycle}/{w1.valid_cycle}"
    assert r1.a_hs < w1.a_hs, f"CHK-019: phase A AR wins the first tie, got AR hs {r1.a_hs} AW hs {w1.a_hs}"
    assert w1.a_hs >= r1.end, f"CHK-019: phase A W1 granted only at/after R1 final R ({r1.end}), got {w1.a_hs}"
    assert r2.valid_cycle == r1.a_hs + 1 and r2.valid_cycle <= r1.end, "CHK-019: (stimulus) R2 asserted right after R1 AR handshake"
    assert w1.a_hs < r2.a_hs, f"CHK-019: phase B after a read completed AW wins (W1 hs {w1.a_hs}, R2 hs {r2.a_hs})"
    assert w2.valid_cycle == w1.a_hs + 1 and w2.valid_cycle <= w1.end, "CHK-019: (stimulus) W2 asserted right after W1 AW handshake"
    assert r2.a_hs >= w1.end and r2.a_hs < w2.a_hs, (
        f"CHK-019: phase C after a write completed AR wins (R2 hs {r2.a_hs}, W2 hs {w2.a_hs}, W1 end {w1.end})")
    for t in (r1, r2):
        assert all(x["resp"] == OKAY for x in t.r) and len(t.r) == 2, f"CHK-019: read completes OKAY, got {t.r}"
    for t in (w1, w2):
        assert t.b["resp"] == OKAY, f"CHK-019: write completes OKAY, got {t.b}"

    # Phase D
    await b.reset(2)
    await b.tick(5)
    w3 = make_write(b.r, rid(b), 0x0500, 0)
    b.submit(w3)
    await b.wait_done([w3], what="CHK-019: lone W3")
    assert w3.a_hs - w3.valid_cycle <= 32, f"CHK-019: lone AW granted directly, waited {w3.a_hs - w3.valid_cycle} cycles"
    await b.tick(3)
    r4 = make_read(rid(b), 0x0600, 1)
    w4 = make_write(b.r, rid(b), 0x0700, 1)
    b.submit(r4, w4)
    await b.wait_done([r4, w4], what="CHK-019: R4/W4 tie")
    assert r4.valid_cycle == w4.valid_cycle, "CHK-019: (stimulus) R4/W4 asserted at the same edge"
    assert r4.a_hs < w4.a_hs, f"CHK-019: phase D after a write completed AR wins (R4 hs {r4.a_hs}, W4 hs {w4.a_hs})"
    await b.final_check()


@cocotb.test()
async def test_chk_020_wvalid_before_aw(dut):
    """CHK-020: WVALID 10 edges before AWVALID: WREADY held low until AW is accepted, then 4 beats in order."""
    b = await make_bench(dut, "chk020")
    b.master.rready.set("always")
    b.master.bready.set("always")
    hist = []
    b.hooks.append(lambda c, s: hist.append((c, s["wvalid"], s["wready"])))
    w = make_write(b.r, rid(b), 0x00003000, 3, 2, INCR, delay=10, w_delay=0)
    b.submit(w)
    await b.wait_done([w], what="CHK-020: write to complete")
    await b.final_check()
    assert w.valid_cycle == w.w_valid_cycle + 10, (
        f"CHK-020: (stimulus) AWVALID 10 edges after WVALID, got {w.w_valid_cycle}->{w.valid_cycle}")
    pre = [h for h in hist if w.w_valid_cycle <= h[0] < w.a_hs]
    assert len(pre) >= 10, f"CHK-020: at least 10 edges before AW handshake, got {len(pre)}"
    bad = [h[0] for h in pre if h[2] != 0]
    assert not bad, f"CHK-020: wready=0 at all edges before the AW handshake, got wready=1 at {bad[:5]}"
    assert w.w_hs and w.w_hs[0] >= w.a_hs, f"CHK-020: W beat 0 not accepted before AW (W hs {w.w_hs[:1]}, AW hs {w.a_hs})"
    assert len(w.w_hs) == 4 and len(w.rec["w"]) == 4, f"CHK-020: exactly 4 W handshakes, got {len(w.w_hs)}"
    got = [(x["data"], x["strb"]) for x in w.rec["w"]]
    assert got == list(zip(w.data, w.strb)), f"CHK-020: W beats accepted in order, got {got}"
    assert _paddrs(w) == [0x3000, 0x3004, 0x3008, 0x300C], f"CHK-020: APB writes at 0x3000..0x300C, got {[hex(a) for a in _paddrs(w)]}"
    for k, tr in enumerate(w.rec["apb"]):
        assert tr["vals"]["pwrite"] == 1 and tr["vals"]["pwdata"] == w.data[k] and tr["vals"]["pstrb"] == w.strb[k], (
            f"CHK-020: APB write {k} carries WDATA/WSTRB {w.data[k]:#x}/{w.strb[k]:#x}, got {tr['vals']}")
    assert w.b["resp"] == OKAY and w.b["id"] == w.id, f"CHK-020: one OKAY B with bid=AWID, got {w.b}"
    assert w.b["cycle"] > w.rec["apb"][-1]["done"], "CHK-020: B after the 4th APB completion"


@cocotb.test()
async def test_chk_021_response_backpressure(dut):
    """CHK-021: RREADY/BREADY backpressure stalls the owning transaction only, without loss or reordering."""
    b = await make_bench(dut, "chk021")
    b.apb.wmin, b.apb.wmax = 0, 3
    b.master.rready.set("hold", lo=0, hi=50)
    b.master.bready.set("hold", lo=100, hi=100)
    txns = []
    for i in range(4):
        txns.append(make_read(rid(b), b.r.randrange(0, 0x10000 // 64) * 64, 15, 2, INCR, prot=b.r.randint(0, 7)))
        txns.append(make_write(b.r, rid(b), b.r.randrange(0, 0x10000 // 32) * 32, 7, 2, INCR, prot=b.r.randint(0, 7)))
    b.submit(*txns)
    await b.wait_done(txns, what="CHK-021: backpressured traffic to complete")
    await b.final_check()
    for t in txns:
        assert t.rec is not None and len(t.rec["apb"]) == t.length + 1, f"CHK-021: AxLEN+1 APB transfers for {t}"
        if t.kind == "R":
            assert len(t.r) == 16, f"CHK-021: 16 R beats, got {len(t.r)}"
            assert [x["last"] for x in t.r] == [0] * 15 + [1], "CHK-021: rlast on beat 15 only"
            assert [x["data"] for x in t.r] == [x["prdata"] for x in t.rec["apb"]], "CHK-021: R beats in order with APB read data"
            assert all(x["resp"] == OKAY and x["id"] == t.id for x in t.r), "CHK-021: R beats OKAY with RID"
        else:
            assert t.b["resp"] == OKAY and t.b["id"] == t.id, f"CHK-021: B OKAY with bid, got {t.b}"
            assert t.b["cycle"] - t.rec["first_bvalid"] == 100, (
                f"CHK-021: B held through 100 BREADY-low cycles, got {t.b['cycle'] - t.rec['first_bvalid']}")
    recs = sorted([t.rec for t in txns], key=lambda x: x["start"])
    for a, c in zip(recs, recs[1:]):
        assert c["start"] >= a["end"], f"CHK-021: no AR/AW handshake ({c['start']}) before the stalled transaction completes ({a['end']})"


UNSUP_CLASSES = None


def _unsupported_cases():
    cases = []
    for size in range(3, 8):
        for L in (0, 3):
            cases.append(dict(addr=0x0, size=size, burst=INCR, cache=0, L=L))
    for L in (0, 3):
        cases.append(dict(addr=0x0, size=2, burst=RSVD, cache=0, L=L))
    for cache in range(16):
        if cache in (0, 1):
            continue
        cases.append(dict(addr=0x0100, size=2, burst=INCR, cache=cache, L=1))
    cases.append(dict(addr=0x0FFC, size=2, burst=INCR, cache=0, L=1))
    cases.append(dict(addr=0x0FFF, size=0, burst=INCR, cache=0, L=1))
    cases.append(dict(addr=0x0F00, size=2, burst=INCR, cache=0, L=255))
    return cases


@cocotb.test()
async def test_chk_022_unsupported_reads(dut):
    """CHK-022: unsupported reads (size, reserved burst, cache, 4-KiB crossing): no APB, ARLEN+1 SLVERR zero-data beats."""
    b = await make_bench(dut, "chk022")
    b.apb.wmin, b.apb.wmax = 0, 2
    b.master.rready.set("random", p=0.6)
    for cs in _unsupported_cases():
        assert not is_supported(cs["addr"], cs["L"], cs["size"], cs["burst"], cs["cache"]), f"CHK-022: (setup) case unsupported {cs}"
        bad = make_read(rid(b), cs["addr"], cs["L"], cs["size"], cs["burst"], cs["cache"], b.r.randint(0, 7))
        good = make_read(rid(b), b.r.randrange(0, 0x1000) * 16, b.r.randint(0, 3), 2, INCR,
                         b.r.choice([0, 1]), b.r.randint(0, 7))
        b.submit(bad, good)
        await b.wait_done([bad, good], what=f"CHK-022: unsupported read {cs} and legal read")
        L = cs["L"]
        assert bad.rec is not None and bad.rec["psel_edges"] == 0 and not bad.rec["apb"], (
            f"CHK-022: psel=0 from AR handshake to final R for {bad}")
        assert len(bad.r) == L + 1, f"CHK-022: exactly ARLEN+1={L + 1} R beats for {bad}, got {len(bad.r)}"
        for k, x in enumerate(bad.r):
            assert x["resp"] == SLVERR and x["data"] == 0 and x["id"] == bad.id, (
                f"CHK-022: beat {k} SLVERR rdata=0 rid={bad.id:#x}, got {x}")
            assert x["last"] == (1 if k == L else 0), f"CHK-022: rlast only on beat {L}, beat {k} got {x['last']}"
        assert len(good.rec["apb"]) == good.length + 1, f"CHK-022: legal read after recovery makes APB transfers, got {len(good.rec['apb'])}"
        assert len(good.r) == good.length + 1 and all(x["resp"] == OKAY for x in good.r), f"CHK-022: legal read OKAY, got {good.r}"
    await b.final_check()


@cocotb.test()
async def test_chk_023_unsupported_writes(dut):
    """CHK-023: unsupported writes drain AWLEN+1 W beats with no APB, then one SLVERR B."""
    b = await make_bench(dut, "chk023")
    b.apb.wmin, b.apb.wmax = 0, 2
    b.master.bready.set("random", p=0.6)
    for cs in _unsupported_cases():
        L = cs["L"]
        bad = make_write(b.r, rid(b), cs["addr"], L, cs["size"], cs["burst"], cs["cache"], b.r.randint(0, 7),
                         w_gaps=[b.r.randint(0, 3) for _ in range(L + 1)])
        good = make_write(b.r, rid(b), b.r.randrange(0, 0x1000) * 16, b.r.randint(0, 3), 2, INCR,
                          b.r.choice([0, 1]), b.r.randint(0, 7))
        b.submit(bad, good)
        await b.wait_done([bad, good], what=f"CHK-023: unsupported write {cs} and legal write")
        assert len(bad.w_hs) == L + 1 and len(bad.rec["w"]) == L + 1, (
            f"CHK-023: exactly AWLEN+1={L + 1} W handshakes for {bad}, got {len(bad.w_hs)}")
        assert bad.rec["psel_edges"] == 0 and not bad.rec["apb"], f"CHK-023: psel=0 from AW to B for {bad}"
        assert bad.rec["first_bvalid"] > bad.w_hs[-1], (
            f"CHK-023: bvalid rises only after the last W handshake ({bad.w_hs[-1]}), got {bad.rec['first_bvalid']}")
        assert bad.b["resp"] == SLVERR and bad.b["id"] == bad.id, f"CHK-023: one SLVERR B with bid=AWID, got {bad.b}"
        assert len(good.rec["apb"]) == good.length + 1 and good.b["resp"] == OKAY, (
            f"CHK-023: legal write after recovery uses APB and returns OKAY, got {len(good.rec['apb'])} transfers, {good.b}")
    await b.final_check()


@cocotb.test()
async def test_chk_024_read_pslverr(dut):
    """CHK-024: read PSLVERR maps to SLVERR with zero data on that beat only."""
    b = await make_bench(dut, "chk024")
    b.ref_check = False
    b.apb.wmin, b.apb.wmax = 0, 1
    b.master.rready.set("random", p=0.7)

    def resp(tr):
        a = tr["addr"]
        if not tr["write"]:
            if 0x2000 <= a < 0x2010:
                k = (a - 0x2000) // 4
                return (0xDEADBEEF, 1) if k == 1 else (k, 0)
            if a == 0x2100:
                return (0xCAFEBABE, 1)
            if 0x2200 <= a < 0x2210:
                return (0xA5A50000 | (a & 0xFFFF), 1)
        return b.apb.default_resp(tr)

    b.apb.resp_fn = resp
    r1 = make_read(rid(b), 0x2000, 3)
    r2 = make_read(rid(b), 0x2100, 0)
    r3 = make_read(rid(b), 0x2200, 3)
    for t in (r1, r2, r3):
        b.submit(t)
        await b.wait_done([t], what=f"CHK-024: {t}")
    await b.final_check()
    assert _paddrs(r1) == [0x2000, 0x2004, 0x2008, 0x200C], f"CHK-024: 4 APB reads at 0x2000..0x200C, got {[hex(a) for a in _paddrs(r1)]}"
    got = [(x["resp"], x["data"]) for x in r1.r]
    assert got == [(OKAY, 0), (SLVERR, 0), (OKAY, 2), (OKAY, 3)], f"CHK-024: beat responses OKAY/SLVERR(0)/OKAY/OKAY, got {got}"
    assert [x["last"] for x in r1.r] == [0, 0, 0, 1], "CHK-024: rlast on beat 3 only"
    assert len(r2.r) == 1 and r2.r[0]["resp"] == SLVERR and r2.r[0]["data"] == 0 and r2.r[0]["last"] == 1, (
        f"CHK-024: single-beat error read returns SLVERR rdata=0 rlast=1, got {r2.r}")
    assert len(r3.r) == 4 and all(x["resp"] == SLVERR and x["data"] == 0 for x in r3.r), (
        f"CHK-024: all-error read returns SLVERR on every beat, got {r3.r}")
    for t in (r1, r2, r3):
        assert all(x["id"] == t.id for x in t.r), "CHK-024: rid echoed"


@cocotb.test()
async def test_chk_025_write_pslverr(dut):
    """CHK-025: write PSLVERR accumulates into the final BRESP; later beats still run; state clears per transaction."""
    b = await make_bench(dut, "chk025")
    b.apb.wmin, b.apb.wmax = 0, 2
    state = {"err": set()}

    def resp(tr):
        if tr["write"] and 0x4000 <= tr["addr"] < 0x4010:
            k = (tr["addr"] - 0x4000) // 4
            return (b.r.getrandbits(32), 1 if k in state["err"] else 0)
        return b.apb.default_resp(tr)

    b.apb.resp_fn = resp
    for errs in ({0}, {3}, {0, 1, 2, 3}, set()):
        state["err"] = set(errs)
        w = make_write(b.r, rid(b), 0x4000, 3)
        b.submit(w)
        await b.wait_done([w], what=f"CHK-025: write with errors {errs}")
        assert _paddrs(w) == [0x4000, 0x4004, 0x4008, 0x400C], f"CHK-025: all 4 APB writes performed, got {[hex(a) for a in _paddrs(w)]}"
        for k, tr in enumerate(w.rec["apb"]):
            assert tr["vals"]["pwdata"] == w.data[k] and tr["vals"]["pstrb"] == w.strb[k] and tr["vals"]["pwrite"] == 1, (
                f"CHK-025: APB write {k} carries matching PWDATA/PSTRB, got {tr['vals']}")
        exp = SLVERR if errs else OKAY
        assert w.b is not None and w.b["resp"] == exp and w.b["id"] == w.id, f"CHK-025: one B resp={exp} bid=AWID for errors {errs}, got {w.b}"
        assert w.b["cycle"] > w.rec["apb"][-1]["done"], "CHK-025: B after the 4th APB completion"
    await b.final_check()


@cocotb.test()
async def test_chk_026_unmapped_default_completer(dut):
    """CHK-026: unmapped address reaches APB; default completer PSLVERR gives AXI SLVERR."""
    b = await make_bench(dut, "chk026")
    b.apb.unmapped_default = True
    b.master.rready.set("always")
    b.master.bready.set("always")
    rd = make_read(rid(b), 0x80000000, 1)
    wr = make_write(b.r, rid(b), 0x80000000, 1)
    ok = make_read(rid(b), 0x00000100, 1)
    for t in (rd, wr, ok):
        b.submit(t)
        await b.wait_done([t], what=f"CHK-026: {t}")
    await b.final_check()
    assert _paddrs(rd) == [0x80000000, 0x80000004], f"CHK-026: 2 APB reads at 0x8000_0000/4, got {[hex(a) for a in _paddrs(rd)]}"
    for tr in rd.rec["apb"] + wr.rec["apb"]:
        assert tr["access_edges"] == 1 and tr["done"] - tr["setup"] == 1, (
            f"CHK-026: each transfer has psel=1 for exactly 2 edges, got access_edges={tr['access_edges']}")
    assert all(tr["vals"]["pwrite"] == 0 for tr in rd.rec["apb"]), "CHK-026: read transfers have pwrite=0"
    assert [(x["resp"], x["data"], x["last"]) for x in rd.r] == [(SLVERR, 0, 0), (SLVERR, 0, 1)], (
        f"CHK-026: 2 SLVERR beats with rdata=0, rlast on beat 1, got {rd.r}")
    assert _paddrs(wr) == [0x80000000, 0x80000004] and all(tr["vals"]["pwrite"] == 1 for tr in wr.rec["apb"]), (
        "CHK-026: 2 APB writes at 0x8000_0000/4")
    assert wr.b["resp"] == SLVERR and wr.b["id"] == wr.id, f"CHK-026: write returns SLVERR B, got {wr.b}"
    assert all(x["resp"] == OKAY for x in ok.r), "CHK-026: mapped access still OKAY"


async def _run_random(b, n_total, tag, allow_hold=True):
    r = b.r
    out = []
    count = 0
    while count < n_total:
        k = min(r.randint(1, 6), n_total - count)
        batch = []
        for _ in range(k):
            kind = "R" if r.random() < 0.5 else "W"
            t = rand_legal(r, kind)
            t.delay = r.randint(0, 3)
            t.w_delay = t.delay
            if kind == "W":
                if r.random() < 0.2:
                    t.w_delay = 0
                    t.delay = r.randint(1, 8)
                t.w_gaps = [r.choice((0, 0, 0, 1, 2)) for _ in range(t.length + 1)]
            batch.append(t)
        for pol in (b.master.rready, b.master.bready):
            x = r.random()
            if x < 0.4:
                pol.set("random", p=r.uniform(0.3, 1.0))
            elif x < 0.6 and allow_hold:
                pol.set("hold", lo=0, hi=6)
            else:
                pol.set("always")
        b.apb.wmin, b.apb.wmax = 0, 3
        b.submit(*batch)
        await b.wait_done(batch, what=f"{tag}: random batch")
        out += batch
        count += k
    return out


@cocotb.test()
async def test_chk_027_random_legal_bursts(dut):
    """CHK-027: random legal FIXED/INCR/WRAP reads/writes plus directed corners vs an independent model."""
    b = await make_bench(dut, "chk027")
    if IDW != 4:
        not_verifiable(dut, "CHK-027", f"run elaborated with PARA_AXI_ID_W={IDW}; plan targets 4 (checked with this width)")
    b.apb.wmin, b.apb.wmax = 0, 3
    wrap_exp = [0x2024 + 4 * i for i in range(7)] + [0x2000 + 4 * i for i in range(9)]
    corners = [
        ("R", 0x1000, 255, 2, INCR, [0x1000 + 4 * k for k in range(256)]),
        ("W", 0x1000, 255, 2, INCR, [0x1000 + 4 * k for k in range(256)]),
        ("R", 0x1F00, 63, 2, INCR, [0x1F00 + 4 * k for k in range(64)]),
        ("W", 0x1FF0, 15, 0, INCR, [(0x1FF0 + k) & ~3 for k in range(16)]),
        ("R", 0x0500, 15, 2, FIXED, [0x0500] * 16),
        ("W", 0x0503, 15, 0, FIXED, [0x0500] * 16),
        ("W", 0x2024, 15, 2, WRAP, wrap_exp),
        ("R", 0x2024, 15, 2, WRAP, wrap_exp),
        ("W", 0x0101, 1, 0, WRAP, [0x0100, 0x0100]),
        ("R", 0x0101, 1, 0, WRAP, [0x0100, 0x0100]),
    ]
    b.master.rready.set("random", p=0.7)
    b.master.bready.set("random", p=0.7)
    for kind, addr, L, size, burst, exp in corners:
        if kind == "R":
            t = make_read(rid(b), addr, L, size, burst, b.r.choice([0, 1]), b.r.randint(0, 7))
        else:
            t = make_write(b.r, rid(b), addr, L, size, burst, b.r.choice([0, 1]), b.r.randint(0, 7))
        b.submit(t)
        await b.wait_done([t], what=f"CHK-027: corner {t}")
        assert _paddrs(t) == exp, f"CHK-027: corner {t} paddr sequence {[hex(a) for a in exp]}, got {[hex(a) for a in _paddrs(t)]}"
        if kind == "R":
            assert len(t.r) == L + 1 and all(x["resp"] == OKAY for x in t.r), f"CHK-027: corner read OKAY, got {len(t.r)} beats"
        else:
            assert t.b["resp"] == OKAY, f"CHK-027: corner write OKAY, got {t.b}"
    txns = await _run_random(b, 2000, "CHK-027")
    await b.final_check()
    seen = set()
    for t in txns:
        assert t.done and t.rec is not None, f"CHK-027: transaction completed {t}"
        assert len(t.rec["apb"]) == t.length + 1, f"CHK-027: AxLEN+1 APB transfers for {t}"
        assert all(x["vals"]["pwrite"] == (1 if t.kind == "W" else 0) for x in t.rec["apb"]), f"CHK-027: pwrite direction for {t}"
        if t.kind == "R":
            assert len(t.r) == t.length + 1 and all(x["resp"] == OKAY and x["id"] == t.id for x in t.r), (
                f"CHK-027: read {t} returns ARLEN+1 OKAY beats with RID")
        else:
            assert t.b["resp"] == OKAY and t.b["id"] == t.id, f"CHK-027: write {t} returns OKAY B with BID, got {t.b}"
        seen.add((t.kind, t.burst, t.cache))
    for kind in ("R", "W"):
        for burst in (FIXED, INCR, WRAP):
            assert any((kind, burst, c) in seen for c in (0, 1)), f"CHK-027: coverage of {kind} burst {burst}"
        for cache in (0, 1):
            assert any((kind, bu, cache) in seen for bu in (FIXED, INCR, WRAP)), f"CHK-027: AxCACHE {cache:04b} {kind} completes OKAY"


@cocotb.test()
async def test_chk_028_subword_unaligned(dut):
    """CHK-028: sub-word/unaligned: PADDR aligned down, PSTRB = WSTRB, no lane rotation either way."""
    b = await make_bench(dut, "chk028")
    b.ref_check = False
    b.apb.resp_fn = lambda tr: (0x11223344, 0) if not tr["write"] else b.apb.default_resp(tr)
    cases = [(0x1000, 0, 0x1), (0x1001, 0, 0x2), (0x1002, 0, 0x4), (0x1003, 0, 0x8), (0x1000, 1, 0x3), (0x1002, 1, 0xC)]
    for addr, size, strb in cases:
        w = make_write(b.r, rid(b), addr, 0, size, INCR, data=[0xAABBCCDD], strb=[strb])
        b.submit(w)
        await b.wait_done([w], what=f"CHK-028: write {w}")
        assert len(w.rec["apb"]) == 1, "CHK-028: one APB write"
        v = w.rec["apb"][0]["vals"]
        assert v["paddr"] == addr & ~3, f"CHK-028: paddr={addr & ~3:#x} for AWADDR {addr:#x}, got {_hx(v['paddr'])}"
        assert v["pstrb"] == strb, f"CHK-028: pstrb={strb:04b} (WSTRB copy) for AWADDR {addr:#x}, got {_hx(v['pstrb'])}"
        assert v["pwdata"] == 0xAABBCCDD, f"CHK-028: pwdata=0xAABBCCDD unrotated, got {_hx(v['pwdata'])}"
        assert w.b["resp"] == OKAY, f"CHK-028: B OKAY, got {w.b}"
        rd = make_read(rid(b), addr, 0, size, INCR)
        b.submit(rd)
        await b.wait_done([rd], what=f"CHK-028: read {rd}")
        v = rd.rec["apb"][0]["vals"]
        assert v["paddr"] == addr & ~3 and v["pstrb"] == 0, f"CHK-028: read paddr aligned and pstrb=0, got {v}"
        assert rd.r[0]["data"] == 0x11223344 and rd.r[0]["resp"] == OKAY, f"CHK-028: rdata=0x11223344 unchanged, got {rd.r}"
    exp_addr = [0x1000, 0x1000, 0x1000, 0x1004, 0x1004, 0x1004, 0x1004, 0x1008]
    exp_strb = [0b0010, 0b0100, 0b1000, 0b0001, 0b0010, 0b0100, 0b1000, 0b0001]
    strbs = [legal_lanes(a, 0) for a in beat_addrs(0x1001, 0, 7, INCR)]
    assert strbs == exp_strb, f"CHK-028: (setup) one-hot WSTRB per beat, got {strbs}"
    w = make_write(b.r, rid(b), 0x1001, 7, 0, INCR, strb=strbs)
    b.submit(w)
    await b.wait_done([w], what="CHK-028: INCR byte burst")
    assert _paddrs(w) == exp_addr, f"CHK-028: byte burst paddrs {[hex(a) for a in exp_addr]}, got {[hex(a) for a in _paddrs(w)]}"
    assert [x["vals"]["pstrb"] for x in w.rec["apb"]] == exp_strb, "CHK-028: byte burst pstrb sequence"
    assert [x["vals"]["pwdata"] for x in w.rec["apb"]] == w.data, "CHK-028: byte burst pwdata equal to WDATA"
    assert w.b["resp"] == OKAY, "CHK-028: byte burst B OKAY"
    await b.final_check()


@cocotb.test()
async def test_chk_029_pprot_passthrough(dut):
    """CHK-029: AxPROT copied to PPROT for all 8 values; no local access control."""
    b = await make_bench(dut, "chk029")
    seq = []
    for p in range(8):
        seq.append(("R", p))
        seq.append(("W", (p + 5) & 7))
    for (k0, p0), (k1, p1) in zip(seq, seq[1:]):
        assert p0 != p1, "CHK-029: (setup) consecutive PROT values differ"
    for kind, prot in seq:
        if kind == "R":
            t = make_read(rid(b), 0x6000, 1, 2, INCR, 0, prot)
        else:
            t = make_write(b.r, rid(b), 0x6000, 1, 2, INCR, 0, prot)
        b.submit(t)
        await b.wait_done([t], what=f"CHK-029: {t}")
        assert len(t.rec["apb"]) == 2, "CHK-029: 2 APB transfers"
        for tr in t.rec["apb"]:
            assert tr["vals"]["pprot"] == prot, f"CHK-029: pprot={prot:03b} for {t}, got {_hx(tr['vals']['pprot'])}"
        if kind == "R":
            assert all(x["resp"] == OKAY for x in t.r), f"CHK-029: read with prot {prot} OKAY, got {t.r}"
        else:
            assert t.b["resp"] == OKAY, f"CHK-029: write with prot {prot} OKAY, got {t.b}"
    await b.final_check()


@cocotb.test()
async def test_chk_030_id_echo(dut):
    """CHK-030: RID/BID echo the request ID unchanged for legal and unsupported requests."""
    b = await make_bench(dut, "chk030")
    if IDW != 4:
        not_verifiable(dut, "CHK-030", f"run elaborated with PARA_AXI_ID_W={IDW}; plan targets 4 (ID range of this width checked)")
    b.apb.wmin, b.apb.wmax = 0, 2
    b.master.rready.set("random", p=0.7)
    b.master.bready.set("random", p=0.7)
    fixed = [0, ID_MASK, 0x5555 & ID_MASK, 0xAAAA & ID_MASK]
    txns = []

    def mk(kind, axid, bad):
        cache = 0b0010 if bad else b.r.choice([0, 1])
        L = b.r.randint(0, 7)
        addr = b.r.randrange(0, 0x800) * 32
        if kind == "R":
            return make_read(axid, addr, L, 2, INCR, cache, b.r.randint(0, 7))
        return make_write(b.r, axid, addr, L, 2, INCR, cache, b.r.randint(0, 7))

    for axid in fixed:
        for kind in ("R", "W"):
            for bad in (False, True):
                txns.append(mk(kind, axid, bad))
    for _ in range(12):
        txns.append(mk(b.r.choice("RW"), b.r.randint(0, ID_MASK), b.r.random() < 0.35))
    b.r.shuffle(txns)
    for i in range(0, len(txns), 4):
        grp = txns[i:i + 4]
        b.submit(*grp)
        await b.wait_done(grp, what="CHK-030: ID group")
    await b.final_check()
    for t in txns:
        exp = OKAY if t.supported else SLVERR
        if t.kind == "R":
            assert len(t.r) == t.length + 1, f"CHK-030: ARLEN+1 beats for {t}"
            for x in t.r:
                assert x["id"] == t.id, f"CHK-030: rid={t.id:#x} for {t}, got {_hx(x['id'])}"
                assert x["resp"] == exp, f"CHK-030: rresp={exp} for {t}, got {x['resp']}"
        else:
            assert t.b["id"] == t.id, f"CHK-030: bid={t.id:#x} for {t}, got {_hx(t.b['id'])}"
            assert t.b["resp"] == exp, f"CHK-030: bresp={exp} for {t}, got {t.b['resp']}"


async def _reset_and_idle(b, n, victim, tag):
    hist = []

    def hook(c, s):
        hist.append((c, s))

    b.hooks.append(hook)
    await b.reset(n)
    c0, s0 = b.tracker.post_reset[-1]
    for name in RESET_ZERO:
        assert s0[name] == 0, f"CHK-031 ({tag}): {name}=0 at the edge after the reset edge, got {_hx(s0[name])}"
    await b.tick(20)
    b.hooks.remove(hook)
    if n >= 2:
        rst_edges = [s for c, s in hist if s["rst"] == 0]
        for s in rst_edges[1:]:
            assert all(s[x] == 0 for x in READIES), f"CHK-031 ({tag}): readies 0 during a multi-edge reset"
    idle = [(c, s) for c, s in hist if c0 <= c < c0 + 20]
    assert len(idle) >= 20, f"CHK-031 ({tag}): observed 20 idle cycles, got {len(idle)}"
    for c, s in idle:
        assert s["psel"] == 0, f"CHK-031 ({tag}): psel stays 0 after reset (no replay), got 1 at cycle {c}"
        assert s["rvalid"] == 0 and s["bvalid"] == 0, f"CHK-031 ({tag}): no R/B after reset, got rvalid={s['rvalid']} bvalid={s['bvalid']} at {c}"
    assert victim.aborted and not victim.done, f"CHK-031 ({tag}): interrupted transaction is cancelled, not completed"


async def _tie_after_reset(b, tag):
    ra = make_read(rid(b), 0x7100, 1)
    wa = make_write(b.r, rid(b), 0x7200, 1)
    b.submit(ra, wa)
    await b.wait_done([ra, wa], what=f"CHK-031 ({tag}): post-reset tie")
    assert ra.valid_cycle == wa.valid_cycle, f"CHK-031 ({tag}): (stimulus) AR/AW asserted at the same edge"
    assert ra.a_hs < wa.a_hs, f"CHK-031 ({tag}): AR wins the first tie after reset (AR hs {ra.a_hs}, AW hs {wa.a_hs})"
    assert len(ra.r) == 2 and all(x["resp"] == OKAY for x in ra.r), f"CHK-031 ({tag}): new read completes normally, got {ra.r}"
    assert wa.b["resp"] == OKAY, f"CHK-031 ({tag}): new write completes normally, got {wa.b}"


@cocotb.test()
async def test_chk_031_reset_mid_transaction(dut):
    """CHK-031 (+CHK-017): reset in any state cancels work, deselects APB, no replay, arbitration back to AR."""
    b = await make_bench(dut, "chk031")
    b.master.rready.set("always")
    b.master.bready.set("always")
    stall = {"on": True}
    b.apb.wait_fn = lambda tr: 5000 if (stall["on"] and tr["addr"] == 0x7004 and not tr["write"]) else 0

    # (a) reset during beat 1 APB ACCESS with PREADY=0
    rd = make_read(rid(b), 0x7000, 3)
    b.submit(rd)
    await b.wait_for(lambda: rd.rec is not None and len(rd.rec["apb"]) >= 2 and rd.rec["apb"][1]["access_edges"] >= 3,
                     400, "CHK-031 (a): beat 1 ACCESS in wait state")
    assert b.last["psel"] == 1 and b.last["penable"] == 1 and b.last["pready"] == 0, "CHK-031 (a): (stimulus) ACCESS with PREADY=0"
    await _reset_and_idle(b, 1, rd, "a")
    stall["on"] = False
    await _tie_after_reset(b, "a")

    # (b)+(d) complete a read (preference -> AW), then reset while RVALID=1 and RREADY=0
    rl = make_read(rid(b), 0x7300, 0)
    b.submit(rl)
    await b.wait_done([rl], what="CHK-031 (b): lone read")
    assert b.tracker.records[-1]["kind"] == "RD", "CHK-031 (d): (stimulus) last completed transaction is a read"
    b.master.rready.set("never")
    rb = make_read(rid(b), 0x7400, 3)
    b.submit(rb)
    await b.wait_for(lambda: rb.rec is not None and b.last is not None and b.last["rvalid"] == 1, 400,
                     "CHK-031 (b): RVALID with RREADY=0")
    await b.tick(2)
    assert b.last["rvalid"] == 1 and b.last["rready"] == 0, "CHK-031 (b): (stimulus) RVALID=1 RREADY=0 before reset"
    await _reset_and_idle(b, 1, rb, "b")
    b.master.rready.set("always")
    await _tie_after_reset(b, "b/d")

    # (c) reset after 2 of 4 W beats
    wc = make_write(b.r, rid(b), 0x7500, 3, w_gaps=[0, 5000, 0, 0])
    b.submit(wc)
    await b.wait_for(lambda: len(wc.w_hs) >= 2, 400, "CHK-031 (c): 2 W beats accepted")
    await b.tick(3)
    assert len(wc.w_hs) == 2, f"CHK-031 (c): (stimulus) exactly 2 W beats before reset, got {len(wc.w_hs)}"
    await _reset_and_idle(b, 2, wc, "c")
    await _tie_after_reset(b, "c")
    await b.final_check()


@cocotb.test()
async def test_regression_random(dut):
    """CHK-001..CHK-017, CHK-027: broad legal random traffic with random waits, backpressure and PSLVERR."""
    b = await make_bench(dut, "regression")
    b.apb.err_prob = 0.03
    txns = await _run_random(b, 600, "REGRESSION")
    await b.final_check()
    for t in txns:
        assert t.done and t.rec is not None, f"CHK-014: transaction completed {t}"
        assert len(t.rec["apb"]) == t.length + 1, f"CHK-016: AxLEN+1 APB transfers for {t}"
        errs = [x["pslverr"] for x in t.rec["apb"]]
        if t.kind == "R":
            assert len(t.r) == t.length + 1, f"CHK-010: ARLEN+1 R beats for {t}"
            for k, x in enumerate(t.r):
                exp = SLVERR if errs[k] == 1 else OKAY
                assert x["resp"] == exp and x["id"] == t.id, f"CHK-011: beat {k} resp {exp} id {t.id:#x} for {t}, got {x}"
        else:
            exp = SLVERR if any(e == 1 for e in errs) else OKAY
            assert t.b["resp"] == exp and t.b["id"] == t.id, f"CHK-008: B resp {exp} id {t.id:#x} for {t}, got {t.b}"

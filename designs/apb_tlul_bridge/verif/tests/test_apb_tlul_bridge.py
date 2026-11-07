"""cocotb 2.1 testbench for m_apb_tlul_bridge (APB4 completer -> TL-UL host bridge).

All checks use top-level ports only.  Timing model: one step per cycle at the falling
edge.  At that point the outputs are read (they equal the values sampled at the next
rising edge) and the inputs for that rising edge are driven.  Trace record number e
therefore holds the values sampled at rising edge e.
"""

import os
from collections import deque

import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer

from nnc_cocotb import *  # noqa: F401,F403


# ---------------------------------------------------------------------------
# Configuration of this run
# ---------------------------------------------------------------------------
def _param(name, default):
    try:
        return int(PARAMS.get(name, default))
    except Exception:
        return default


ADDR_W = _param("PARA_ADDR_W", 32)
SRC_W = _param("PARA_SRC_W", 8)
SRC_ID = _param("PARA_SRC_ID", 0)
A_USER_W = _param("PARA_A_USER_W", 1)
D_SINK_W = _param("PARA_D_SINK_W", 1)
D_USER_W = _param("PARA_D_USER_W", 1)

ADDR_MASK = (1 << ADDR_W) - 1
ALIGN_MASK = ADDR_MASK & ~3
SRC_MASK = (1 << SRC_W) - 1
WRONG_SRC = (SRC_ID ^ 1) & SRC_MASK
OP_PUT = 0b000   # PutFullData
OP_GET = 0b100   # Get
ACK = 0b000      # AccessAck
ACK_DATA = 0b001 # AccessAckData

OUT = {
    "pready": "o_apb_pready", "prdata": "o_apb_prdata", "pslverr": "o_apb_pslverr",
    "a_valid": "o_tlul_a_valid", "a_opcode": "o_tlul_a_opcode", "a_param": "o_tlul_a_param",
    "a_size": "o_tlul_a_size", "a_source": "o_tlul_a_source", "a_address": "o_tlul_a_address",
    "a_mask": "o_tlul_a_mask", "a_data": "o_tlul_a_data", "a_user": "o_tlul_a_user",
    "d_ready": "o_tlul_d_ready",
}
INP = {
    "psel": "i_apb_psel", "penable": "i_apb_penable", "pwrite": "i_apb_pwrite",
    "paddr": "i_apb_paddr", "pprot": "i_apb_pprot", "pstrb": "i_apb_pstrb",
    "pwdata": "i_apb_pwdata", "a_ready": "i_tlul_a_ready", "d_valid": "i_tlul_d_valid",
    "d_opcode": "i_tlul_d_opcode", "d_source": "i_tlul_d_source", "d_data": "i_tlul_d_data",
    "d_error": "i_tlul_d_error", "d_param": "i_tlul_d_param", "d_size": "i_tlul_d_size",
    "d_sink": "i_tlul_d_sink", "d_user": "i_tlul_d_user",
}
A_FIELDS = ("a_opcode", "a_address", "a_data", "a_param", "a_size", "a_mask", "a_source", "a_user")


def _hx(v):
    return f"{v:#x}" if isinstance(v, int) and v >= 0 else str(v)


def _is_setup(t):
    return t["psel"] == 1 and t["penable"] == 0


def _illegal(t):
    return (t["paddr"] & 3) != 0 or (t["pwrite"] == 1 and t["pstrb"] != 0xF)


def rand_addr(r, aligned=True, low=None):
    a = r.getrandbits(ADDR_W) & ALIGN_MASK
    if not aligned:
        a |= (low if low is not None else r.randint(1, 3))
    return a & ADDR_MASK


# ---------------------------------------------------------------------------
# Transfer object and spec-derived reference model
# ---------------------------------------------------------------------------
class Xfer:
    _count = 0

    def __init__(self, write, addr, pstrb=0xF, wdata=0, pprot=0, gap=0, dev=None, tags=()):
        Xfer._count += 1
        self.id = Xfer._count
        self.write = 1 if write else 0
        self.addr = addr & ADDR_MASK
        self.pstrb = pstrb & 0xF
        self.wdata = wdata & 0xFFFFFFFF
        self.pprot = pprot & 7
        self.gap = gap
        self.dev = dict(dev) if dev else {}
        self.tags = set(tags)
        self.setup_edge = None
        self.done_edge = None
        self.pslverr = None
        self.prdata = None
        self.hs = []
        self.k_used = None
        self.j = None
        self.resp = None
        self.resp_edge = None
        self.abandoned = False

    @property
    def illegal(self):
        return (self.addr & 3) != 0 or (self.write == 1 and self.pstrb != 0xF)

    @property
    def kind(self):
        if (self.addr & 3) != 0:
            return "MIS"
        if self.write and self.pstrb != 0xF:
            return "ILS"
        return "W" if self.write else "R"

    def __repr__(self):
        rw = "WR" if self.write else "RD"
        return (f"Xfer#{self.id}({rw} addr={self.addr:#x} pstrb={self.pstrb:#x} "
                f"wdata={self.wdata:#x} setup=E{self.setup_edge} done={self.done_edge})")


def ref_expected(x):
    """Expected (pslverr, prdata) from the specification.

    Illegal (PSTRB != 4'b1111 on a write, or PADDR[1:0] != 0): PSLVERR=1, PRDATA=0.
    Legal: err = d_error | d_opcode != expected (AccessAckData for Get, AccessAck for Put)
    | d_source != PARA_SRC_ID.  PRDATA = d_data only for an error-free read, else 0.
    """
    if x.illegal:
        return 1, 0
    r = x.resp
    exp_op = ACK if x.write else ACK_DATA
    err = 1 if (r["error"] != 0 or r["opcode"] != exp_op or r["source"] != SRC_ID) else 0
    prdata = r["data"] if (not x.write and not err) else 0
    return err, prdata


def check_xfer(x, cid):
    """Scoreboard check of one completed transfer against the reference model."""
    assert not x.abandoned, f"{cid}: {x} was abandoned by reset, a completion was not expected"
    assert x.setup_edge is not None, f"{cid}: Setup phase of {x} was never driven"
    assert x.done_edge is not None, f"{cid}: o_apb_pready=1 expected for {x}, got no completion"
    lat = x.done_edge - x.setup_edge
    if x.illegal:
        assert len(x.hs) == 0, (f"{cid}: no TL-UL request expected for illegal {x}, "
                                f"got {len(x.hs)} A-channel handshake(s)")
        assert lat == 1, (f"{cid}: local error completion expected at E1 (1 Access cycle) for {x}, "
                          f"got o_apb_pready=1 at E{lat}")
        assert x.pslverr == 1, f"{cid}: o_apb_pslverr=1 expected for illegal {x}, got {x.pslverr}"
        assert x.prdata == 0, f"{cid}: o_apb_prdata=0 expected for illegal {x}, got {_hx(x.prdata)}"
        return
    assert len(x.hs) == 1, f"{cid}: exactly one A-channel handshake expected for {x}, got {len(x.hs)}"
    h = x.hs[0]
    exp_opc = OP_PUT if x.write else OP_GET
    assert h["opcode"] == exp_opc, (f"{cid}: o_tlul_a_opcode={exp_opc:#05b} expected for {x}, "
                                    f"got {_hx(h['opcode'])}")
    assert h["address"] == (x.addr & ALIGN_MASK), (f"{cid}: o_tlul_a_address={x.addr:#x} expected for {x}, "
                                                   f"got {_hx(h['address'])}")
    if x.write:
        assert h["data"] == x.wdata, f"{cid}: o_tlul_a_data={x.wdata:#x} expected for {x}, got {_hx(h['data'])}"
    assert h["source"] == SRC_ID, f"{cid}: o_tlul_a_source={SRC_ID} expected, got {h['source']}"
    assert h["edge"] == x.setup_edge + 1 + x.k_used, (
        f"{cid}: A-channel handshake expected at E1+k=E{1 + x.k_used} for {x}, "
        f"got E{h['edge'] - x.setup_edge}")
    assert x.resp is not None and x.resp_edge is not None, f"{cid}: response of {x} was never delivered"
    assert x.done_edge == x.resp_edge + 1, (
        f"{cid}: o_apb_pready=1 expected one edge after the counted response "
        f"(E{x.resp_edge - x.setup_edge + 1}) for {x}, got E{lat}")
    exp_err, exp_rd = ref_expected(x)
    assert x.pslverr == exp_err, (f"{cid}: o_apb_pslverr={exp_err} expected for {x} "
                                  f"(response {x.resp}), got {x.pslverr}")
    assert x.prdata == exp_rd, (f"{cid}: o_apb_prdata={exp_rd:#x} expected for {x} "
                                f"(response {x.resp}), got {_hx(x.prdata)}")


def check_reset_values(o, cid, where):
    for k in ("a_valid", "d_ready", "pready", "pslverr", "prdata", "a_opcode", "a_address", "a_data"):
        assert o[k] == 0, f"{cid}: {OUT[k]}=0 expected {where}, got {_hx(o[k])}"
    assert o["a_param"] == 0, f"{cid}: o_tlul_a_param=3'b000 expected {where}, got {_hx(o['a_param'])}"
    assert o["a_size"] == 2, f"{cid}: o_tlul_a_size=2'b10 expected {where}, got {_hx(o['a_size'])}"
    assert o["a_mask"] == 0xF, f"{cid}: o_tlul_a_mask=4'b1111 expected {where}, got {_hx(o['a_mask'])}"
    assert o["a_source"] == SRC_ID, f"{cid}: o_tlul_a_source={SRC_ID} expected {where}, got {_hx(o['a_source'])}"
    assert o["a_user"] == 0, f"{cid}: o_tlul_a_user=0 expected {where}, got {_hx(o['a_user'])}"


# ---------------------------------------------------------------------------
# Port-level mirror of assertion checks CHK-001..CHK-017
# ---------------------------------------------------------------------------
class PortChecker:
    def __init__(self):
        self.prev = None
        self.prev2 = None
        self.req_open = False
        self.pending = False
        self.exp_get = 0
        self.hits = {}

    def _hit(self, cid):
        self.hits[cid] = self.hits.get(cid, 0) + 1

    def check(self, c):
        e = c["edge"]
        p = self.prev if (self.prev is not None and self.prev["edge"] == e - 1) else None
        p2 = self.prev2 if (p is not None and self.prev2 is not None and self.prev2["edge"] == e - 2) else None
        rst = c["rst"] == 1

        # CHK-017 constant fields, at every edge
        self._hit("CHK-017")
        assert c["a_param"] == 0, f"CHK-017: o_tlul_a_param=3'b000 expected at edge {e}, got {_hx(c['a_param'])}"
        assert c["a_size"] == 2, f"CHK-017: o_tlul_a_size=2'b10 expected at edge {e}, got {_hx(c['a_size'])}"
        assert c["a_mask"] == 0xF, f"CHK-017: o_tlul_a_mask=4'b1111 expected at edge {e}, got {_hx(c['a_mask'])}"
        assert c["a_source"] == SRC_ID, f"CHK-017: o_tlul_a_source={SRC_ID} expected at edge {e}, got {_hx(c['a_source'])}"
        assert c["a_user"] == 0, f"CHK-017: o_tlul_a_user=0 expected at edge {e}, got {_hx(c['a_user'])}"
        assert c["a_opcode"] in (OP_PUT, OP_GET), (
            f"CHK-017: o_tlul_a_opcode 3'b000 or 3'b100 expected at edge {e}, got {_hx(c['a_opcode'])}")
        assert c["a_address"] >= 0 and (c["a_address"] & 3) == 0, (
            f"CHK-017: o_tlul_a_address[1:0]=2'b00 expected at edge {e}, got {_hx(c['a_address'])}")
        # CHK-003
        if c["pslverr"] != 0:
            self._hit("CHK-003")
            assert c["pready"] == 1, f"CHK-003: o_apb_pslverr=1 only with o_apb_pready=1 at edge {e}, got pready={c['pready']}"

        if not rst:
            self._hit("CHK-012")
            for k in ("a_valid", "d_ready", "pready", "pslverr", "prdata", "a_opcode", "a_address", "a_data"):
                assert c[k] == 0, f"CHK-012: {OUT[k]}=0 expected while i_rst_n_core=0 at edge {e}, got {_hx(c[k])}"
        else:
            if c["pready"] == 1:
                self._hit("CHK-001")
                assert c["psel"] == 1 and c["penable"] == 1, (
                    f"CHK-001: o_apb_pready=1 only in an Access cycle at edge {e}, got psel={c['psel']} penable={c['penable']}")
                if c["pwrite"] == 1 or c["pslverr"] == 1:
                    self._hit("CHK-005")
                    assert c["prdata"] == 0, (f"CHK-005: o_apb_prdata=0 expected on write/error completion at edge {e}, "
                                              f"got {_hx(c['prdata'])}")
            if c["a_valid"] == 1:
                self._hit("CHK-009")
                assert c["psel"] == 1 and c["penable"] == 1 and c["pready"] == 0, (
                    f"CHK-009: o_tlul_a_valid=1 only inside Access before PREADY at edge {e}, got psel={c['psel']} "
                    f"penable={c['penable']} pready={c['pready']}")
                self._hit("CHK-008")
                assert not self.req_open, (f"CHK-008: o_tlul_a_valid=1 at edge {e} while an accepted request has "
                                           f"no APB completion yet (req_open=1)")
            if _is_setup(c) and not _illegal(c):
                assert c["pready"] == 0 and c["a_valid"] == 0, (
                    f"CHK-006: o_apb_pready=0 and o_tlul_a_valid=0 expected at Setup edge {e}, got "
                    f"pready={c['pready']} a_valid={c['a_valid']}")

        if p is not None and p["rst"] == 1 and rst:
            if p["pready"] == 1:
                self._hit("CHK-002")
                assert c["pready"] == 0, f"CHK-002: o_apb_pready one-cycle pulse, expected 0 at edge {e}, got 1"
            if c["pready"] == 0:
                self._hit("CHK-004")
                assert c["prdata"] == p["prdata"], (f"CHK-004: o_apb_prdata held at edge {e} expected {_hx(p['prdata'])}, "
                                                    f"got {_hx(c['prdata'])}")
            self._hit("CHK-013")
            assert c["d_ready"] == 1, f"CHK-013: o_tlul_d_ready=1 expected at edge {e} (reset released), got {c['d_ready']}"
            if p["a_valid"] == 0 and c["a_valid"] == 1:
                self._hit("CHK-014")
                assert _is_setup(p) and not _illegal(p), (
                    f"CHK-014: o_tlul_a_valid rose at edge {e} without a legal Setup at edge {e - 1} "
                    f"(psel={p['psel']} penable={p['penable']} paddr={_hx(p['paddr'])} pwrite={p['pwrite']} pstrb={_hx(p['pstrb'])})")
            if p["a_valid"] == 1 and p["a_ready"] == 0:
                self._hit("CHK-015")
                assert c["a_valid"] == 1, f"CHK-015: o_tlul_a_valid held until accepted, expected 1 at edge {e}, got 0"
                for k in A_FIELDS:
                    assert c[k] == p[k], (f"CHK-015: {OUT[k]} stable while not accepted, expected {_hx(p[k])} "
                                          f"at edge {e}, got {_hx(c[k])}")
            if p["a_valid"] == 1 and p["a_ready"] == 1:
                self._hit("CHK-016")
                assert c["a_valid"] == 0, f"CHK-016: o_tlul_a_valid=0 expected at edge {e} after handshake, got 1"
            if _is_setup(p) and not _illegal(p):
                self._hit("CHK-006")
                exp_opc = OP_PUT if p["pwrite"] == 1 else OP_GET
                assert c["a_valid"] == 1, f"CHK-006: o_tlul_a_valid=1 expected at E1 (edge {e}), got {c['a_valid']}"
                assert c["pready"] == 0, f"CHK-006: o_apb_pready=0 expected at E1 (edge {e}), got {c['pready']}"
                assert c["d_ready"] == 1, f"CHK-006: o_tlul_d_ready=1 expected at E1 (edge {e}), got {c['d_ready']}"
                assert c["a_opcode"] == exp_opc, f"CHK-006: o_tlul_a_opcode={exp_opc:#05b} expected at edge {e}, got {_hx(c['a_opcode'])}"
                assert c["a_address"] == (p["paddr"] & ALIGN_MASK), (
                    f"CHK-006: o_tlul_a_address={_hx(p['paddr'] & ALIGN_MASK)} expected at edge {e}, got {_hx(c['a_address'])}")
                if p["pwrite"] == 1:
                    assert c["a_data"] == p["pwdata"], (f"CHK-006: o_tlul_a_data={_hx(p['pwdata'])} expected at edge {e}, "
                                                        f"got {_hx(c['a_data'])}")
            if p.get("_counted"):
                self._hit("CHK-010")
                assert c["pready"] == 1, f"CHK-010: o_apb_pready=1 expected at edge {e} after counted response, got {c['pready']}"
                assert c["pslverr"] == p["_err"], f"CHK-010: o_apb_pslverr={p['_err']} expected at edge {e}, got {c['pslverr']}"
                assert c["prdata"] == p["_exp_prdata"], (f"CHK-010: o_apb_prdata={_hx(p['_exp_prdata'])} expected at "
                                                         f"edge {e}, got {_hx(c['prdata'])}")
            if c["pready"] == 1:
                self._hit("CHK-011")
                assert p.get("_counted") or (_is_setup(p) and _illegal(p)), (
                    f"CHK-011: o_apb_pready=1 at edge {e} not caused by a counted response or an illegal Setup at edge {e - 1}")
        if (p2 is not None and p2["rst"] == 1 and p["rst"] == 1 and rst
                and _is_setup(p2) and _illegal(p2)):
            self._hit("CHK-007")
            assert p["pready"] == 1 and p["pslverr"] == 1 and p["prdata"] == 0 and p["a_valid"] == 0, (
                f"CHK-007: at E1 (edge {e - 1}) pready=1 pslverr=1 prdata=0 a_valid=0 expected, got pready={p['pready']} "
                f"pslverr={p['pslverr']} prdata={_hx(p['prdata'])} a_valid={p['a_valid']}")
            assert c["a_valid"] == 0, f"CHK-007: o_tlul_a_valid=0 expected at E2 (edge {e}), got 1"

        # state update (port-derived flags)
        if not rst:
            self.req_open = False
            self.pending = False
            c["_counted"] = False
        else:
            dvr = c["d_valid"] == 1 and c["d_ready"] == 1
            hs = c["a_valid"] == 1 and c["a_ready"] == 1
            counted = dvr and (self.pending or hs)
            c["_counted"] = counted
            if counted:
                eg = self.exp_get if self.pending else ((c["a_opcode"] >> 2) & 1)
                exp_op = ACK_DATA if eg else ACK
                err = 1 if (c["d_error"] == 1 or c["d_opcode"] != exp_op or c["d_source"] != SRC_ID) else 0
                c["_err"] = err
                c["_exp_prdata"] = c["d_data"] if (eg and not err) else 0
            if self.pending and dvr:
                self.pending = False
            if hs and not dvr:
                self.pending = True
                self.exp_get = (c["a_opcode"] >> 2) & 1
            if c["pready"] == 1:
                self.req_open = False
            if hs:
                self.req_open = True
        self.prev2 = self.prev
        self.prev = c


# ---------------------------------------------------------------------------
# APB requester model
# ---------------------------------------------------------------------------
class Requester:
    def __init__(self, env):
        self.env = env
        self.queue = deque()
        self.cur = None
        self.state = "idle"
        self.gap = 0
        self.phase = "idle"
        self.done = []
        self.abandoned = []
        self.idle_garbage = False
        self.sig = dict(psel=0, penable=0, pwrite=0, paddr=0, pprot=0, pstrb=0, pwdata=0)

    def add(self, x):
        self.queue.append(x)

    def busy(self):
        return self.cur is not None or len(self.queue) > 0

    def reset_model(self):
        if self.cur is not None:
            self.cur.abandoned = True
            self.abandoned.append(self.cur)
        self.cur = None
        self.state = "idle"
        self.gap = 0
        self.phase = "idle"
        self.sig["psel"] = 0
        self.sig["penable"] = 0

    def _after_done(self):
        if self.queue and self.queue[0].gap == 0:
            self.state = "setup"
        else:
            self.state = "idle"
            self.gap = self.queue[0].gap if self.queue else 0

    def step(self, o, e):
        s = self.sig
        if self.state == "access":
            self.phase = "access"
            s["psel"] = 1
            s["penable"] = 1
            if o["pready"] == 1:
                x = self.cur
                x.done_edge = e
                x.pslverr = o["pslverr"]
                x.prdata = o["prdata"]
                self.done.append(x)
                self.cur = None
                self._after_done()
            return
        assert o["pready"] != 1, (f"CHK-011: o_apb_pready=0 expected at edge {e} (no APB transfer in its Access "
                                  f"phase), got 1")
        if self.state == "setup":
            x = self.queue.popleft()
            self.cur = x
            x.setup_edge = e
            s.update(psel=1, penable=0, pwrite=x.write, paddr=x.addr, pprot=x.pprot,
                     pstrb=x.pstrb, pwdata=x.wdata)
            self.phase = "setup"
            self.state = "access"
            return
        self.phase = "idle"
        s["psel"] = 0
        s["penable"] = 0
        if self.idle_garbage:
            r = self.env.r
            s.update(pwrite=r.getrandbits(1), paddr=r.getrandbits(ADDR_W), pprot=r.getrandbits(3),
                     pstrb=r.getrandbits(4), pwdata=r.getrandbits(32))
        if self.gap > 0:
            self.gap -= 1
        if self.gap == 0 and self.queue:
            self.state = "setup"


# ---------------------------------------------------------------------------
# TL-UL device model
# ---------------------------------------------------------------------------
class Device:
    def __init__(self, env, r, ign_r):
        self.env = env
        self.r = r
        self.ign_r = ign_r
        self.default = dict(k=0, j=1, mode="ok")
        self.policy_fn = None
        self.orphan_fn = None
        self.garbage = False
        self.ready_idle_random = False
        self.ign_random = False
        self.pol = None
        self.pol_x = None
        self.wait = 0
        self.pend = None
        self.hs_log = []
        self.orphans = []
        self.sig = dict(a_ready=0, d_valid=0, d_opcode=0, d_source=0, d_data=0, d_error=0,
                        d_param=0, d_size=2, d_sink=0, d_user=0)

    def reset_model(self):
        self.pol = None
        self.pol_x = None
        self.wait = 0
        self.pend = None
        self.sig["a_ready"] = 0
        self.sig["d_valid"] = 0

    def _policy(self, x):
        p = dict(self.default)
        if self.policy_fn is not None:
            p.update(self.policy_fn(x) or {})
        if x is not None:
            p.update(x.dev)
        return p

    def _make_resp(self, o, pol):
        get = (o["a_opcode"] >> 2) & 1
        exp_op = ACK_DATA if get else ACK
        data = pol.get("data")
        if data is None:
            data = self.r.getrandbits(32) or 1
        mode = pol.get("mode", "ok")
        resp = dict(opcode=exp_op, source=o["a_source"] & SRC_MASK, error=0,
                    data=data & 0xFFFFFFFF, mode=mode)
        if mode == "derr":
            resp["error"] = 1
        elif mode == "badop":
            op = pol.get("op")
            if op is None:
                op = self.r.choice([v for v in range(8) if v != exp_op])
            resp["opcode"] = op & 7
        elif mode == "badsrc":
            resp["source"] = pol.get("src", WRONG_SRC) & SRC_MASK
        return resp

    def _orphan(self, spec):
        r = self.r
        p = dict(opcode=r.choice((0, 1, 0, 1, r.randint(0, 7))),
                 source=SRC_ID if r.random() < 0.6 else r.getrandbits(SRC_W),
                 data=r.getrandbits(32) or 1, error=r.randint(0, 1), cls="orphan")
        if isinstance(spec, dict):
            p.update(spec)
        return p

    def step(self, o, e):
        s = self.sig
        a_ready = 0
        hs = False
        if o["a_valid"] == 1:
            if self.pol is None:
                self.pol_x = self.env.req.cur
                self.pol = self._policy(self.pol_x)
                self.wait = 0
            k = self.pol.get("k", 0)
            if k is not None and self.wait >= k:
                a_ready = 1
                hs = True
            else:
                self.wait += 1
        else:
            self.pol = None
            self.pol_x = None
            if self.ready_idle_random:
                a_ready = self.r.randint(0, 1)
        if hs:
            h = dict(edge=e, opcode=o["a_opcode"], address=o["a_address"], data=o["a_data"],
                     source=o["a_source"])
            self.hs_log.append(h)
            x = self.pol_x
            assert x is not None, f"CHK-014: TL-UL request accepted at edge {e} while no APB transfer was in progress"
            assert self.pend is None, (f"CHK-008: second TL-UL request accepted at edge {e} while the previous "
                                       f"one was still waiting for its response")
            x.hs.append(h)
            x.k_used = self.wait
            j = self.pol.get("j", 1)
            x.j = j
            self.pend = dict(x=x, resp=self._make_resp(o, self.pol), due=(None if j is None else e + j))
            self.pol = None
            self.pol_x = None
        dv = 0
        payload = None
        if self.pend is not None:
            if self.pend["due"] is not None and e >= self.pend["due"]:
                payload = self.pend["resp"]
                dv = 1
                if o["d_ready"] == 1:
                    x = self.pend["x"]
                    x.resp = payload
                    x.resp_edge = e
                    self.pend = None
        elif not hs and self.orphan_fn is not None:
            spec = self.orphan_fn(self.env, e, o, a_ready)
            if spec is not None:
                payload = self._orphan(spec)
                dv = 1
                rec = dict(payload)
                rec["edge"] = e
                self.orphans.append(rec)
        if dv:
            s.update(d_valid=1, d_opcode=payload["opcode"] & 7, d_source=payload["source"] & SRC_MASK,
                     d_data=payload["data"] & 0xFFFFFFFF, d_error=payload["error"] & 1)
        else:
            s["d_valid"] = 0
            if self.garbage:
                r = self.r
                s.update(d_opcode=r.getrandbits(3), d_source=r.getrandbits(SRC_W),
                         d_data=r.getrandbits(32), d_error=r.getrandbits(1))
            else:
                s.update(d_opcode=0, d_source=0, d_data=0, d_error=0)
        if self.ign_random:
            ir = self.ign_r
            s.update(d_param=ir.getrandbits(3), d_size=ir.getrandbits(2),
                     d_sink=ir.getrandbits(D_SINK_W), d_user=ir.getrandbits(D_USER_W))
        else:
            s.update(d_param=0, d_size=2, d_sink=0, d_user=0)
        s["a_ready"] = a_ready


# ---------------------------------------------------------------------------
# Cycle engine
# ---------------------------------------------------------------------------
class Env:
    def __init__(self, dut, salt, keep_trace=True):
        self.dut = dut
        self.salt = salt
        self.r = rng(salt)
        self.req = Requester(self)
        self.dev = Device(self, rng(f"{salt}:dev"), rng(f"{salt}:ign"))
        self.chk = PortChecker()
        self.trace = [] if keep_trace else None
        self.edge = 0
        self.rst = 1
        self.reset_noise = False
        self._release = False
        self._cache = {}
        self.clk = dut.i_clk_core
        self.rst_h = dut.i_rst_n_core
        self.oh = {k: getattr(dut, n) for k, n in OUT.items()}
        self.ih = {k: getattr(dut, n) for k, n in INP.items()}

    def read(self):
        o = {}
        for k, h in self.oh.items():
            v = val(h)
            o[k] = -1 if v is None else v
        return o

    def drive(self, ins):
        for k, v in ins.items():
            if self._cache.get(k) != v:
                self.ih[k].value = v
                self._cache[k] = v

    def _reset_inputs(self):
        ins = dict(psel=0, penable=0, pwrite=0, paddr=0, pprot=0, pstrb=0, pwdata=0,
                   a_ready=0, d_valid=0, d_opcode=0, d_source=0, d_data=0, d_error=0,
                   d_param=0, d_size=2, d_sink=0, d_user=0)
        if self.reset_noise:
            r = self.r
            ins.update(a_ready=r.getrandbits(1), d_valid=r.getrandbits(1), d_opcode=r.getrandbits(3),
                       d_source=r.getrandbits(SRC_W), d_data=r.getrandbits(32), d_error=r.getrandbits(1),
                       d_param=r.getrandbits(3), d_size=r.getrandbits(2), d_sink=r.getrandbits(D_SINK_W),
                       d_user=r.getrandbits(D_USER_W))
        return ins

    async def step(self):
        e = self.edge
        o = self.read()
        if self.rst == 1:
            self.req.step(o, e)
            self.dev.step(o, e)
            ins = dict(self.req.sig)
            ins.update(self.dev.sig)
        else:
            ins = self._reset_inputs()
        self.drive(ins)
        rec = dict(ins)
        rec.update(o)
        rec["rst"] = self.rst
        rec["edge"] = e
        self.chk.check(rec)
        if self.trace is not None:
            self.trace.append(rec)
        if self._release:
            self._release = False
            await RisingEdge(self.clk)
            await Timer(1)
            self.rst_h.value = 1
            self.rst = 1
            await FallingEdge(self.clk)
        else:
            await next_cycle(self.dut)
        self.edge += 1

    async def steps(self, n):
        for _ in range(n):
            await self.step()

    async def run_all(self, max_cycles, what):
        for _ in range(max_cycles):
            if not self.req.busy() and self.dev.pend is None:
                return
            await self.step()
        raise AssertionError(f"{what}: all transfers expected to complete within {max_cycles} cycles, "
                             f"got still pending {self.req.cur}")

    async def run_until(self, cond, max_cycles, what):
        for _ in range(max_cycles):
            o = self.read()
            if cond(o):
                return o
            await self.step()
        raise AssertionError(f"{what}: condition expected within {max_cycles} cycles, got timeout")

    async def assert_reset_now(self):
        """Asynchronous reset assertion at the current (mid-cycle) point; returns outputs 1 step later."""
        self.rst_h.value = 0
        self.rst = 0
        self.req.reset_model()
        self.dev.reset_model()
        self.drive(self._reset_inputs())
        await Timer(1)
        return self.read()

    async def hold_reset(self, edges):
        """Keep reset asserted for `edges` rising edges, then release 1 time unit after the last one."""
        assert self.rst == 0
        for i in range(edges):
            if i == edges - 1:
                self._release = True
            await self.step()


async def make_env(dut, salt, keep_trace=True):
    start_clock(dut)
    await reset_dut(dut)
    return Env(dut, salt, keep_trace=keep_trace)


PROMPT = dict(k=0, j=1, mode="ok")


def _outs_tuple(t):
    return tuple(t[k] for k in OUT)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
@cocotb.test()
async def test_chk_018_local_error(dut):
    """CHK-018: unsupported PSTRB and misaligned PADDR complete locally in 1 Access cycle with PSLVERR."""
    env = await make_env(dut, "chk018")
    r = env.r
    T = env.trace
    illegal = []
    for s in range(15):
        illegal.append(Xfer(1, rand_addr(r), s, r.getrandbits(32), r.randint(0, 7), gap=2))
    for lo in (1, 2, 3):
        illegal.append(Xfer(0, rand_addr(r, False, lo), r.randint(0, 15), r.getrandbits(32), r.randint(0, 7), gap=2))
        illegal.append(Xfer(1, rand_addr(r, False, lo), 0xF, r.getrandbits(32), r.randint(0, 7), gap=2))
    pairs = []
    for x in illegal:
        n = Xfer(1, rand_addr(r), 0xF, r.getrandbits(32), r.randint(0, 7), gap=0, dev=PROMPT)
        env.req.add(x)
        env.req.add(n)
        pairs.append((x, n))
    await env.run_all(len(pairs) * 20, "CHK-018")
    await env.steps(3)
    for x, n in pairs:
        check_xfer(x, "CHK-018")
        check_xfer(n, "CHK-018")
        E0 = x.setup_edge
        t1, t2 = T[E0 + 1], T[E0 + 2]
        assert t1["pready"] == 1 and t1["pslverr"] == 1 and t1["prdata"] == 0, (
            f"CHK-018: at E1 pready=1 pslverr=1 prdata=0 expected for {x}, got pready={t1['pready']} "
            f"pslverr={t1['pslverr']} prdata={_hx(t1['prdata'])}")
        assert t1["a_valid"] == 0 and t2["a_valid"] == 0, (
            f"CHK-018: o_tlul_a_valid=0 at E1 and E2 expected for {x}, got {t1['a_valid']},{t2['a_valid']}")
        assert n.setup_edge == E0 + 2, f"CHK-018: next Setup expected at E2 (interval 2), got E{n.setup_edge - E0}"
        assert T[E0 + 3]["a_valid"] == 1, f"CHK-018: o_tlul_a_valid=1 expected at E3 for following write {n}, got 0"
        assert n.done_edge == E0 + 5 and n.pslverr == 0, (
            f"CHK-018: following write expected to complete at E5 with pslverr=0, got E{n.done_edge - E0} pslverr={n.pslverr}")


@cocotb.test()
async def test_chk_019_device_error(dut):
    """CHK-019: d_error=1 maps to PSLVERR=1, PRDATA=0; no stored error for the next read."""
    env = await make_env(dut, "chk019")
    r = env.r
    T = env.trace
    pairs = []
    for i in range(16):
        w = i % 2
        x = Xfer(w, rand_addr(r), 0xF if w else r.randint(0, 15), r.getrandbits(32), r.randint(0, 7),
                 gap=r.randint(1, 3), dev=dict(k=0, j=1, mode="derr", data=r.getrandbits(32) | 1))
        y = Xfer(0, rand_addr(r), r.randint(0, 15), 0, 0, gap=r.randint(0, 2),
                 dev=dict(k=0, j=1, mode="ok", data=r.getrandbits(32) | 1))
        env.req.add(x)
        env.req.add(y)
        pairs.append((x, y))
    await env.run_all(len(pairs) * 20, "CHK-019")
    await env.steps(3)
    for x, y in pairs:
        check_xfer(x, "CHK-019")
        check_xfer(y, "CHK-019")
        assert x.resp["error"] == 1 and x.resp["data"] != 0
        t3 = T[x.setup_edge + 3]
        assert t3["pready"] == 1 and t3["pslverr"] == 1 and t3["prdata"] == 0, (
            f"CHK-019: at E3 pready=1 pslverr=1 prdata=0 expected for {x}, got pready={t3['pready']} "
            f"pslverr={t3['pslverr']} prdata={_hx(t3['prdata'])}")
        assert y.pslverr == 0 and y.prdata == y.resp["data"], (
            f"CHK-019: following read expected pslverr=0 prdata={y.resp['data']:#x}, got {y.pslverr} {_hx(y.prdata)}")


@cocotb.test()
async def test_chk_020_wrong_opcode_source(dut):
    """CHK-020: wrong d_opcode and wrong d_source give PSLVERR=1, PRDATA=0."""
    env = await make_env(dut, "chk020")
    r = env.r
    T = env.trace
    cases = [(0, "badop", op) for op in (0, 2, 3, 4, 5, 6, 7)]
    cases += [(1, "badop", op) for op in (1, 2, 3, 4, 5, 6, 7)]
    srcs = [WRONG_SRC]
    if SRC_W > 1:
        srcs.append((SRC_ID ^ (1 << (SRC_W - 1))) & SRC_MASK)
    cases += [(w, "badsrc", s) for w in (0, 1) for s in srcs]
    pairs = []
    for (w, m, v) in cases:
        dev = dict(k=0, j=1, mode=m, data=r.getrandbits(32) | 1)
        dev["op" if m == "badop" else "src"] = v
        x = Xfer(w, rand_addr(r), 0xF if w else r.randint(0, 15), r.getrandbits(32), r.randint(0, 7),
                 gap=r.randint(1, 2), dev=dev)
        y = Xfer(0, rand_addr(r), r.randint(0, 15), 0, 0, gap=r.randint(0, 2),
                 dev=dict(k=0, j=1, mode="ok", data=r.getrandbits(32) | 1))
        env.req.add(x)
        env.req.add(y)
        pairs.append((x, y, m, v))
    await env.run_all(len(pairs) * 20, "CHK-020")
    await env.steps(3)
    for x, y, m, v in pairs:
        check_xfer(x, "CHK-020")
        check_xfer(y, "CHK-020")
        if m == "badop":
            assert x.resp["opcode"] == v and x.resp["source"] == SRC_ID and x.resp["error"] == 0
        else:
            assert x.resp["source"] == v and x.resp["error"] == 0
        t3 = T[x.setup_edge + 3]
        assert t3["pready"] == 1 and t3["pslverr"] == 1 and t3["prdata"] == 0, (
            f"CHK-020: at E3 pready=1 pslverr=1 prdata=0 expected for {x} ({m}={v}), got pready={t3['pready']} "
            f"pslverr={t3['pslverr']} prdata={_hx(t3['prdata'])}")
        assert y.pslverr == 0 and y.prdata == y.resp["data"], (
            f"CHK-020: following read expected pslverr=0 prdata={y.resp['data']:#x}, got {y.pslverr} {_hx(y.prdata)}")


@cocotb.test()
async def test_chk_021_orphan_responses(dut):
    """CHK-021: orphan d_valid pulses (idle, Setup, before acceptance, after PREADY) have no APB effect."""
    env = await make_env(dut, "chk021")
    r = env.r
    T = env.trace
    st = {"idle_on": False}

    def hook(env_, e, o, a_ready):
        rq = env_.req
        if rq.phase == "idle":
            last = rq.done[-1] if rq.done else None
            if last is not None and "d" in last.tags and 1 <= e - last.done_edge <= 3:
                return dict(cls="d")
            if st["idle_on"] and e % 2 == 0:
                return dict(cls="a")
            if rq.queue and "a" in rq.queue[0].tags and e % 2 == 0:
                return dict(cls="a")
            return None
        if rq.cur is None:
            last = rq.done[-1] if rq.done else None
            if last is not None and "d" in last.tags and last.done_edge == e:
                return dict(cls="d")
            return None
        x = rq.cur
        if rq.phase == "setup" and "b" in x.tags:
            return dict(cls="b")
        if rq.phase == "access" and o["a_valid"] == 1 and a_ready == 0 and "c" in x.tags:
            return dict(cls="c")
        return None

    env.dev.orphan_fn = hook
    st["idle_on"] = True
    start = env.edge
    await env.steps(8)
    st["idle_on"] = False
    for e in range(start, start + 8):
        assert T[e]["pready"] == 0 and T[e]["prdata"] == 0 and T[e]["pslverr"] == 0, (
            f"CHK-021: idle orphans must have no APB effect at edge {e}, got pready={T[e]['pready']} "
            f"prdata={_hx(T[e]['prdata'])} pslverr={T[e]['pslverr']}")
    xs = []
    for rep in range(3):
        for w in (0, 1):
            def mk(write, gap, tags=(), dev=None):
                d = dict(k=0, j=1, mode="ok", data=r.getrandbits(32) | 1)
                if dev:
                    d.update(dev)
                return Xfer(write, rand_addr(r), 0xF if write else r.randint(0, 15), r.getrandbits(32),
                            r.randint(0, 7), gap=gap, dev=d, tags=tags)
            seq = [mk(0, 1), mk(w, 6, ("a",)), mk(w, 2, ("b",)), mk(w, 2, ("c",), dict(k=2)),
                   mk(w, 1, ("d",)), mk(0, 5), mk(w, 0, ("b", "c"), dict(k=2))]
            for x in seq:
                env.req.add(x)
            xs += seq
    await env.run_all(len(xs) * 25, "CHK-021")
    await env.steps(5)
    for x in xs:
        check_xfer(x, "CHK-021")
        assert x.done_edge - x.setup_edge == 2 + x.k_used + x.j, (
            f"CHK-021: Access phase of {x} expected 2+k+j={2 + x.k_used + x.j} cycles, got {x.done_edge - x.setup_edge}")
        if not x.write:
            assert x.prdata == x.resp["data"] and x.pslverr == 0, (
                f"CHK-021: read {x} expected prdata from real response {x.resp['data']:#x}, got {_hx(x.prdata)}")
    assert len(env.req.done) == len(xs), f"CHK-021: {len(xs)} completions expected, got {len(env.req.done)}"
    classes = set()
    for orp in env.dev.orphans:
        e = orp["edge"]
        classes.add(orp["cls"])
        if e + 1 < len(T):
            nx = T[e + 1]
            assert nx["pready"] == 0, f"CHK-021: orphan at edge {e} ({orp['cls']}) must not give o_apb_pready, got 1 at edge {e + 1}"
            assert nx["prdata"] == T[e]["prdata"], (
                f"CHK-021: o_apb_prdata unchanged after orphan at edge {e} expected {_hx(T[e]['prdata'])}, got {_hx(nx['prdata'])}")
            assert nx["pslverr"] == 0, f"CHK-021: o_apb_pslverr=0 after orphan at edge {e} expected, got {nx['pslverr']}"
    for c in ("a", "b", "c", "d"):
        assert c in classes, f"CHK-021: orphan class ({c}) expected to be injected, got classes {sorted(classes)}"


@cocotb.test()
async def test_chk_022_no_response_no_timeout(dut):
    """CHK-022: a device that never responds/accepts makes the requester wait; reset recovers."""
    env = await make_env(dut, "chk022")
    r = env.r
    T = env.trace
    # (1) read accepted, no response for 1000 cycles
    x = Xfer(0, rand_addr(r), r.randint(0, 15), 0, 0, gap=1, dev=dict(k=0, j=None, mode="ok"))
    env.req.add(x)
    await env.run_until(lambda o: len(x.hs) == 1, 20, "CHK-022 (1): handshake of the read")
    start = env.edge
    await env.steps(1000)
    for e in range(start, env.edge):
        t = T[e]
        assert t["pready"] == 0, f"CHK-022: o_apb_pready=0 expected at edge {e} with no response, got 1"
        assert t["a_valid"] == 0, f"CHK-022: o_tlul_a_valid=0 expected after the handshake at edge {e}, got 1"
    assert len(env.dev.hs_log) == 1, f"CHK-022: exactly one request expected, got {len(env.dev.hs_log)}"
    assert x.done_edge is None, f"CHK-022: no completion expected for {x}"
    await env.assert_reset_now()
    await env.hold_reset(3)
    await env.steps(2)
    # (2) write never accepted for 1000 cycles
    y = Xfer(1, rand_addr(r), 0xF, r.getrandbits(32), r.randint(0, 7), gap=1, dev=dict(k=None, j=1, mode="ok"))
    env.req.add(y)
    await env.run_until(lambda o: o["a_valid"] == 1, 20, "CHK-022 (2): o_tlul_a_valid of the write")
    first = env.edge
    await env.steps(1000)
    ref = T[first]
    assert ref["a_opcode"] == OP_PUT and ref["a_address"] == y.addr and ref["a_data"] == y.wdata, (
        f"CHK-022: channel A of {y} expected PutFullData addr={y.addr:#x} data={y.wdata:#x}, got "
        f"op={_hx(ref['a_opcode'])} addr={_hx(ref['a_address'])} data={_hx(ref['a_data'])}")
    for e in range(first, env.edge):
        t = T[e]
        assert t["a_valid"] == 1, f"CHK-022: o_tlul_a_valid=1 held expected at edge {e}, got 0"
        assert t["pready"] == 0, f"CHK-022: o_apb_pready=0 expected at edge {e}, got 1"
        for k in A_FIELDS:
            assert t[k] == ref[k], f"CHK-022: {OUT[k]} stable expected {_hx(ref[k])} at edge {e}, got {_hx(t[k])}"
    assert len(y.hs) == 0
    await env.assert_reset_now()
    await env.hold_reset(3)
    await env.steps(2)
    z = Xfer(1, rand_addr(r), 0xF, r.getrandbits(32), r.randint(0, 7), gap=1, dev=PROMPT)
    env.req.add(z)
    await env.run_all(30, "CHK-022: write after reset")
    check_xfer(z, "CHK-022")
    assert z.done_edge == z.setup_edge + 3 and z.pslverr == 0, (
        f"CHK-022: write after reset expected pready=1 at E3 with pslverr=0, got E{z.done_edge - z.setup_edge} "
        f"pslverr={z.pslverr}")


@cocotb.test()
async def test_chk_023_write_prompt(dut):
    """CHK-023: aligned full-strobe write to a prompt device: PutFullData at E1, PREADY at E3, PRDATA=0."""
    env = await make_env(dut, "chk023")
    r = env.r
    T = env.trace
    xs = []
    for i in range(20):
        a = 0 if i == 0 else (ALIGN_MASK if i == 1 else rand_addr(r))
        x = Xfer(1, a, 0xF, r.getrandbits(32), r.randint(0, 7), gap=r.randint(1, 3), dev=PROMPT)
        env.req.add(x)
        xs.append(x)
    await env.run_all(20 * 12, "CHK-023")
    await env.steps(3)
    for x in xs:
        check_xfer(x, "CHK-023")
        E0 = x.setup_edge
        t1, t2, t3 = T[E0 + 1], T[E0 + 2], T[E0 + 3]
        assert t1["a_valid"] == 1, f"CHK-023: o_tlul_a_valid=1 at E1 expected for {x}, got 0"
        assert t1["a_opcode"] == OP_PUT, f"CHK-023: o_tlul_a_opcode=3'b000 at E1 expected, got {_hx(t1['a_opcode'])}"
        assert t1["a_size"] == 2 and t1["a_mask"] == 0xF, f"CHK-023: size 2'b10 mask 4'b1111 expected, got {t1['a_size']} {t1['a_mask']}"
        assert t1["a_address"] == x.addr, f"CHK-023: o_tlul_a_address={x.addr:#x} expected, got {_hx(t1['a_address'])}"
        assert t1["a_data"] == x.wdata, f"CHK-023: o_tlul_a_data={x.wdata:#x} expected, got {_hx(t1['a_data'])}"
        assert t1["d_ready"] == 1, f"CHK-023: o_tlul_d_ready=1 at E1 expected, got {t1['d_ready']}"
        hs_edges = [e for e in range(E0, E0 + 4) if T[e]["a_valid"] == 1 and T[e]["a_ready"] == 1]
        assert hs_edges == [E0 + 1], f"CHK-023: exactly one handshake at E1 expected for {x}, got edges {hs_edges}"
        assert t2["a_valid"] == 0, f"CHK-023: o_tlul_a_valid=0 at E2 expected, got 1"
        assert t1["pready"] == 0 and t2["pready"] == 0, f"CHK-023: o_apb_pready=0 at E1,E2 expected, got {t1['pready']},{t2['pready']}"
        assert t3["pready"] == 1 and t3["pslverr"] == 0 and t3["prdata"] == 0, (
            f"CHK-023: at E3 pready=1 pslverr=0 prdata=0 expected, got {t3['pready']} {t3['pslverr']} {_hx(t3['prdata'])}")


@cocotb.test()
async def test_chk_024_read_prompt(dut):
    """CHK-024: aligned reads give Get, PRDATA=d_data, 3 Access cycles, independent of PSTRB."""
    env = await make_env(dut, "chk024")
    r = env.r
    T = env.trace
    xs = []
    for s in list(range(16)) + [r.randint(0, 15) for _ in range(16)]:
        x = Xfer(0, rand_addr(r), s, r.getrandbits(32), r.randint(0, 7), gap=r.randint(0, 2), dev=PROMPT)
        env.req.add(x)
        xs.append(x)
    A, D, WD = rand_addr(r), r.getrandbits(32) | 1, r.getrandbits(32)
    prime = Xfer(0, A, 0, WD, 0, gap=2, dev=dict(k=0, j=1, mode="ok", data=D))
    ind = [Xfer(0, A, s, WD, 0, gap=2, dev=dict(k=0, j=1, mode="ok", data=D)) for s in range(16)]
    env.req.add(prime)
    for x in ind:
        env.req.add(x)
    await env.run_all(60 * 12, "CHK-024")
    await env.steps(3)
    for x in xs + [prime] + ind:
        check_xfer(x, "CHK-024")
        E0 = x.setup_edge
        t1, t2, t3 = T[E0 + 1], T[E0 + 2], T[E0 + 3]
        assert t1["a_valid"] == 1 and t1["a_opcode"] == OP_GET, (
            f"CHK-024: Get at E1 expected for {x}, got a_valid={t1['a_valid']} opcode={_hx(t1['a_opcode'])}")
        assert t1["a_address"] == x.addr and t1["a_size"] == 2 and t1["a_mask"] == 0xF, (
            f"CHK-024: addr={x.addr:#x} size 2 mask F expected, got {_hx(t1['a_address'])} {t1['a_size']} {t1['a_mask']}")
        hs_edges = [e for e in range(E0, E0 + 4) if T[e]["a_valid"] == 1 and T[e]["a_ready"] == 1]
        assert hs_edges == [E0 + 1], f"CHK-024: exactly one handshake at E1 expected for {x}, got {hs_edges}"
        assert t1["pready"] == 0 and t2["pready"] == 0, f"CHK-024: o_apb_pready=0 at E1,E2 expected for {x}"
        assert t3["pready"] == 1 and t3["pslverr"] == 0 and t3["prdata"] == x.resp["data"], (
            f"CHK-024: at E3 pready=1 pslverr=0 prdata={x.resp['data']:#x} expected for {x}, got "
            f"{t3['pready']} {t3['pslverr']} {_hx(t3['prdata'])}")
    ref = None
    for x in ind:
        w = [_outs_tuple(T[x.setup_edge + i]) for i in (1, 2, 3)]
        if ref is None:
            ref = w
        assert w == ref, f"CHK-024: outputs E1..E3 independent of PSTRB expected, differ for pstrb={x.pstrb:#x}"


@cocotb.test()
async def test_chk_025_ignored_inputs(dut):
    """CHK-025: PPROT, d_param, d_size, d_sink and d_user have no effect on any output."""
    env = await make_env(dut, "chk025")
    r = env.r
    T = env.trace
    plan = [(1, "a", 0xF, 0, 1, "ok", 1), (0, "a", 0x0, 1, 2, "ok", 0), (1, "a", 0xF, 2, 0, "ok", 2),
            (0, "a", 0x6, 0, 0, "ok", 0), (1, "a", 0x3, 0, 1, "ok", 1), (0, "a", 0xF, 0, 1, "ok", 0),
            (0, "m", 0x0, 0, 1, "ok", 0), (0, "a", 0x0, 1, 1, "derr", 1), (1, "a", 0xF, 3, 3, "ok", 0),
            (0, "a", 0x0, 0, 1, "ok", 2), (1, "a", 0xF, 0, 1, "ok", 0), (0, "a", 0x0, 2, 0, "ok", 1)]
    fixed = []
    for (w, ak, s, k, j, m, g) in plan:
        fixed.append(dict(write=w, addr=rand_addr(r, ak == "a"), pstrb=s, wdata=r.getrandbits(32), gap=g,
                          dev=dict(k=k, j=j, mode=m, data=r.getrandbits(32) | 1)))
    env.dev.ign_random = True
    ref_outs = None
    for prot in range(8):
        await env.assert_reset_now()
        await env.hold_reset(3)
        start = env.edge
        xs = [Xfer(f["write"], f["addr"], f["pstrb"], f["wdata"], prot, f["gap"], f["dev"]) for f in fixed]
        for x in xs:
            env.req.add(x)
        await env.run_all(400, "CHK-025")
        await env.steps(3)
        for x in xs:
            check_xfer(x, "CHK-025")
        outs = [_outs_tuple(T[e]) for e in range(start, env.edge)]
        if ref_outs is None:
            ref_outs = outs
            continue
        assert len(outs) == len(ref_outs), (f"CHK-025: identical run length expected for pprot={prot}, "
                                            f"got {len(outs)} vs {len(ref_outs)} cycles")
        for i, (a, b) in enumerate(zip(outs, ref_outs)):
            if a != b:
                diff = [n for n, va, vb in zip(OUT.values(), a, b) if va != vb]
                raise AssertionError(f"CHK-025: outputs identical across repeats expected, pprot={prot} cycle {i} "
                                     f"differs in {diff}")


@cocotb.test()
async def test_chk_026_backpressure_delay(dut):
    """CHK-026: channel A stable under a_ready delay k; Access phase = 2+k+j cycles."""
    env = await make_env(dut, "chk026")
    r = env.r
    T = env.trace
    combos = [(k, j) for k in range(9) for j in range(1, 8)]
    r.shuffle(combos)
    combos += [(r.randint(0, 8), r.randint(1, 7)) for _ in range(30)]
    xs = []
    for k, j in combos:
        w = r.randint(0, 1)
        x = Xfer(w, rand_addr(r), 0xF if w else r.randint(0, 15), r.getrandbits(32), r.randint(0, 7),
                 gap=r.randint(0, 3), dev=dict(k=k, j=j, mode="ok"))
        env.req.add(x)
        xs.append(x)
    await env.run_all(len(xs) * 30, "CHK-026")
    await env.steps(3)
    for x in xs:
        check_xfer(x, "CHK-026")
        k, j = x.dev["k"], x.dev["j"]
        E0 = x.setup_edge
        E1 = E0 + 1
        ref = T[E1]
        assert ref["a_opcode"] == (OP_PUT if x.write else OP_GET) and ref["a_address"] == x.addr
        if x.write:
            assert ref["a_data"] == x.wdata, f"CHK-026: o_tlul_a_data={x.wdata:#x} expected, got {_hx(ref['a_data'])}"
        for t in range(k + 1):
            c = T[E1 + t]
            assert c["a_valid"] == 1, f"CHK-026: o_tlul_a_valid=1 expected at E1+{t} for {x} (k={k}), got 0"
            for f in ("a_opcode", "a_address", "a_data"):
                assert c[f] == ref[f], f"CHK-026: {OUT[f]} unchanged expected at E1+{t}, got {_hx(c[f])} vs {_hx(ref[f])}"
            assert c["a_ready"] == (1 if t == k else 0)
        assert x.hs[0]["edge"] == E1 + k, f"CHK-026: handshake expected at E1+{k}, got E{x.hs[0]['edge'] - E0}"
        assert T[E1 + k + 1]["a_valid"] == 0, f"CHK-026: o_tlul_a_valid=0 expected at E2+k for {x}, got 1"
        for e in range(E1, E0 + 2 + k + j):
            assert T[e]["pready"] == 0, f"CHK-026: o_apb_pready=0 expected at E{e - E0} for {x} (k={k} j={j}), got 1"
        assert T[E0 + 2 + k + j]["pready"] == 1, f"CHK-026: o_apb_pready=1 expected at E{2 + k + j} for {x}, got 0"
        assert x.done_edge - E0 == 2 + k + j


@cocotb.test()
async def test_chk_027_same_cycle_response(dut):
    """CHK-027: response in the acceptance cycle gives a 2+k cycle Access phase."""
    env = await make_env(dut, "chk027")
    r = env.r
    T = env.trace
    xs = []
    for rep in range(3):
        for k in (0, 1, 3):
            for w in (0, 1):
                x = Xfer(w, rand_addr(r), 0xF if w else r.randint(0, 15), r.getrandbits(32), r.randint(0, 7),
                         gap=r.randint(0, 2), dev=dict(k=k, j=0, mode="ok"))
                env.req.add(x)
                xs.append(x)
    await env.run_all(len(xs) * 15, "CHK-027")
    await env.steps(3)
    for x in xs:
        check_xfer(x, "CHK-027")
        k = x.dev["k"]
        E0 = x.setup_edge
        h = T[E0 + 1 + k]
        assert h["a_valid"] == 1 and h["a_ready"] == 1 and h["d_valid"] == 1 and h["d_ready"] == 1, (
            f"CHK-027: handshake and response together expected at E1+{k} for {x}")
        for e in range(E0 + 1, E0 + 2 + k):
            assert T[e]["pready"] == 0, f"CHK-027: o_apb_pready=0 expected at E{e - E0} for {x}, got 1"
        t = T[E0 + 2 + k]
        assert t["pready"] == 1, f"CHK-027: o_apb_pready=1 expected at E{2 + k} for {x}, got 0"
        assert t["a_valid"] == 0, f"CHK-027: o_tlul_a_valid=0 expected at E{2 + k} for {x}, got 1"
        exp_rd = 0 if x.write else x.resp["data"]
        assert t["pslverr"] == 0 and t["prdata"] == exp_rd, (
            f"CHK-027: pslverr=0 prdata={exp_rd:#x} expected for {x}, got {t['pslverr']} {_hx(t['prdata'])}")


@cocotb.test()
async def test_chk_028_back_to_back(dut):
    """CHK-028: back-to-back pairs with PSEL held high and with 1/5 idle cycles; Setup-to-Setup intervals."""
    env = await make_env(dut, "chk028")
    r = env.r
    T = env.trace
    modes = {"prompt": dict(k=0, j=1, mode="ok"), "same": dict(k=0, j=0, mode="ok"),
             "derr": dict(k=0, j=1, mode="derr")}

    def make_kind(kind, dev, gap, mis_write):
        if kind == "W":
            return Xfer(1, rand_addr(r), 0xF, r.getrandbits(32), r.randint(0, 7), gap, dev)
        if kind == "R":
            return Xfer(0, rand_addr(r), r.randint(0, 15), r.getrandbits(32), r.randint(0, 7), gap, dev)
        if kind == "ILS":
            return Xfer(1, rand_addr(r), 0x5, r.getrandbits(32), r.randint(0, 7), gap, dev)
        return Xfer(mis_write, rand_addr(r, False, 2), 0xF, r.getrandbits(32), r.randint(0, 7), gap, dev)

    pairs = []
    all_x = []
    idx = 0
    for mode, dev in modes.items():
        for g in (0, 1, 5):
            for k1 in ("W", "R", "ILS", "MIS"):
                for k2 in ("W", "R", "ILS", "MIS"):
                    x1 = make_kind(k1, dev, 3, idx & 1)
                    x2 = make_kind(k2, dev, g, (idx >> 1) & 1)
                    idx += 1
                    env.req.add(x1)
                    env.req.add(x2)
                    all_x += [x1, x2]
                    pairs.append((mode, g, x1, x2))
    await env.run_all(len(all_x) * 20, "CHK-028")
    # Extra idle cycles so that the trace covers the edges after the last completion
    await env.steps(3)
    assert env.req.done == all_x, "CHK-028: every transfer expected to complete once, in order"
    for mode, g, x1, x2 in pairs:
        check_xfer(x1, "CHK-028")
        check_xfer(x2, "CHK-028")
        base = 2 if x1.illegal else (3 if mode == "same" else 4)
        iv = x2.setup_edge - x1.setup_edge
        assert iv == base + g, (f"CHK-028: Setup-to-Setup interval {base + g} expected ({x1.kind}->{x2.kind}, "
                                f"{mode}, gap {g}), got {iv}")
        nx = T[x2.setup_edge + 1]
        if x2.illegal:
            assert nx["pready"] == 1 and nx["pslverr"] == 1 and nx["a_valid"] == 0, (
                f"CHK-028: second illegal Setup expected pready=1 pslverr=1 at next edge, got {nx['pready']} {nx['pslverr']}")
        else:
            assert nx["a_valid"] == 1, f"CHK-028: second legal Setup expected o_tlul_a_valid=1 at next edge, got 0"
        for x in (x1, x2):
            if x.illegal:
                for e in range(x.setup_edge, x.done_edge + 2):
                    assert T[e]["a_valid"] == 0, f"CHK-028: illegal {x} must never produce o_tlul_a_valid=1 (edge {e})"


@cocotb.test()
async def test_chk_029_random_scoreboard(dut):
    """CHK-029: 10000-transfer constrained-random regression with scoreboard, assertions and coverage."""
    env = await make_env(dut, "chk029", keep_trace=False)
    r = env.r
    dut._log.info(f"CHK-029 seed: NNC_SEED={os.environ.get('NNC_SEED', '<unset>')} salt='chk029'")
    env.dev.garbage = True
    env.dev.ready_idle_random = True
    env.req.idle_garbage = True

    def policy(x):
        u = r.random()
        mode = "derr" if u < 0.05 else ("badop" if u < 0.10 else ("badsrc" if u < 0.15 else "ok"))
        return dict(k=0 if r.random() < 0.4 else r.randint(1, 8), j=r.randint(0, 7), mode=mode)

    def orphan(env_, e, o, a_ready):
        if r.random() >= 0.03:
            return None
        rq = env_.req
        if rq.phase == "idle":
            cls = "after_resp" if (rq.done and e - rq.done[-1].done_edge <= 3) else "idle"
        elif rq.phase == "setup":
            cls = "setup"
        elif o["a_valid"] == 1:
            cls = "pre_accept"
        elif o["pready"] == 1:
            cls = "after_resp"
        else:
            cls = "other"
        return dict(cls=cls)

    env.dev.policy_fn = policy
    env.dev.orphan_fn = orphan
    cov = dict(wstrb=set(), rstrb=set(), err=set(), k=set(), j=set(), b2b=set())
    N, B = 10000, 200
    prev = None
    for b in range(N // B):
        xs = []
        for _ in range(B):
            w = r.random() < 0.5
            addr = rand_addr(r, r.random() < 0.75)
            if w:
                s = 0xF if r.random() < 0.6 else r.randint(0, 15)
            else:
                s = 0 if r.random() < 0.4 else r.randint(1, 15)
            gap = 0 if r.random() < 0.4 else r.randint(1, 5)
            x = Xfer(w, addr, s, r.getrandbits(32), r.randint(0, 7), gap)
            env.req.add(x)
            xs.append(x)
        await env.run_all(B * 40, f"CHK-029 batch {b}")
        for x in xs:
            check_xfer(x, "CHK-029")
            rw = "W" if x.write else "R"
            if x.write:
                cov["wstrb"].add(x.pstrb)
            else:
                cov["rstrb"].add("zero" if x.pstrb == 0 else "nonzero")
            if (x.addr & 3) != 0:
                cov["err"].add(("misaligned", rw))
            elif x.write and x.pstrb != 0xF:
                cov["err"].add(("strobe", "W"))
            else:
                cov["k"].add(x.k_used)
                cov["j"].add(x.j)
                if x.resp["mode"] != "ok":
                    cov["err"].add((x.resp["mode"], rw))
            if prev is not None and x.setup_edge == prev.done_edge + 1:
                cov["b2b"].add((prev.kind, x.kind))
            prev = x
        prev = None
    ocls = set(o_["cls"] for o_ in env.dev.orphans)
    assert cov["wstrb"] == set(range(16)), f"CHK-029: COV-001 all 16 write PSTRB values expected, got {sorted(cov['wstrb'])}"
    assert cov["rstrb"] == {"zero", "nonzero"}, f"CHK-029: COV-001 read PSTRB zero/non-zero expected, got {cov['rstrb']}"
    need = {(m, rw) for m in ("derr", "badop", "badsrc", "misaligned") for rw in "RW"} | {("strobe", "W")}
    assert need <= cov["err"], f"CHK-029: COV-002 error kinds expected, missing {sorted(need - cov['err'])}"
    assert cov["k"] == set(range(9)), f"CHK-029: a_ready waits 0..8 expected, got {sorted(cov['k'])}"
    assert cov["j"] == set(range(8)), f"CHK-029: d_valid delays same-cycle and 0..6 expected, got {sorted(cov['j'])}"
    assert {"idle", "setup", "pre_accept", "after_resp"} <= ocls, f"CHK-029: orphan timings expected, got {sorted(ocls)}"
    kinds = ("W", "R", "ILS", "MIS")
    need_b2b = {(a, b) for a in kinds for b in kinds}
    assert need_b2b <= cov["b2b"], f"CHK-029: back-to-back pairs expected, missing {sorted(need_b2b - cov['b2b'])}"
    for i in range(1, 18):
        cid = f"CHK-{i:03d}"
        if cid == "CHK-012":
            continue
        assert env.chk.hits.get(cid, 0) > 0, f"{cid}: assertion antecedent expected to be exercised, got 0 hits"


@cocotb.test()
async def test_chk_030_reset_values(dut):
    """CHK-030: reset values, d_ready release timing, asynchronous assertion, return to idle."""
    start_clock(dut)
    for n in INP.values():
        getattr(dut, n).value = 0
    dut.i_rst_n_core.value = 0
    await next_cycle(dut, 2)
    env = Env(dut, "chk030")
    env.rst = 0
    env.reset_noise = True
    r = env.r
    T = env.trace
    await env.hold_reset(6)
    env.reset_noise = False
    for e in range(0, 6):
        check_reset_values(T[e], "CHK-030", f"at edge {e} while i_rst_n_core=0 (step 1)")
    rel = env.edge
    await env.steps(5)
    assert T[rel]["d_ready"] == 0, f"CHK-030: o_tlul_d_ready=0 at first edge after release expected, got {T[rel]['d_ready']}"
    for e in range(rel, rel + 5):
        assert T[e]["pready"] == 0 and T[e]["a_valid"] == 0, f"CHK-030: idle after release expected at edge {e}"
    x = Xfer(1, rand_addr(r), 0xF, r.getrandbits(32), r.randint(0, 7), gap=1, dev=PROMPT)
    env.req.add(x)
    await env.run_all(30, "CHK-030 step 3")
    check_xfer(x, "CHK-030")
    assert x.done_edge == x.setup_edge + 3 and x.pslverr == 0, (
        f"CHK-030: step 3 write expected pready at E3, got E{x.done_edge - x.setup_edge}")
    await env.steps(2)
    x2 = Xfer(1, rand_addr(r), 0xF, r.getrandbits(32), r.randint(0, 7), gap=1, dev=PROMPT)
    env.req.add(x2)
    o = await env.run_until(lambda o: x2.setup_edge is not None and env.edge == x2.setup_edge + 1, 30,
                            "CHK-030 step 4: A1 of second write")
    assert o["a_valid"] == 1, f"CHK-030: o_tlul_a_valid=1 in A1 before reset expected, got {o['a_valid']}"
    e_as = env.edge
    for e in range(rel + 1, e_as):
        assert T[e]["d_ready"] == 1, f"CHK-030: o_tlul_d_ready=1 expected at edge {e}, got 0"
    snap = await env.assert_reset_now()
    check_reset_values(snap, "CHK-030", "1 time unit after mid-cycle reset assertion in A1 (step 4)")
    await env.hold_reset(3)
    for e in range(e_as, env.edge):
        check_reset_values(T[e], "CHK-030", f"at edge {e} in reset (step 4)")
    assert x2.done_edge is None
    rel2 = env.edge
    await env.steps(3)
    assert T[rel2]["d_ready"] == 0, f"CHK-030: o_tlul_d_ready=0 at first edge after release expected, got 1"
    x3 = Xfer(0, rand_addr(r), r.randint(0, 15), 0, 0, gap=1, dev=PROMPT)
    env.req.add(x3)
    o = await env.run_until(lambda o: o["pready"] == 1, 30, "CHK-030 step 5: PREADY of third transfer")
    assert x3.setup_edge is not None and env.edge == x3.setup_edge + 3
    e_as = env.edge
    for e in range(rel2 + 1, e_as):
        assert T[e]["d_ready"] == 1, f"CHK-030: o_tlul_d_ready=1 expected at edge {e}, got 0"
    snap = await env.assert_reset_now()
    check_reset_values(snap, "CHK-030", "1 time unit after mid-cycle reset assertion in PREADY cycle (step 5)")
    await env.hold_reset(3)
    for e in range(e_as, env.edge):
        check_reset_values(T[e], "CHK-030", f"at edge {e} in reset (step 5)")
    rel3 = env.edge
    await env.steps(3)
    assert T[rel3]["d_ready"] == 0, f"CHK-030: o_tlul_d_ready=0 at first edge after release expected, got 1"
    x4 = Xfer(1, rand_addr(r), 0xF, r.getrandbits(32), 0, gap=1, dev=PROMPT)
    env.req.add(x4)
    await env.run_all(30, "CHK-030 recovery write")
    check_xfer(x4, "CHK-030")
    assert x4.done_edge == x4.setup_edge + 3
    for e in range(rel3 + 1, env.edge):
        assert T[e]["d_ready"] == 1, f"CHK-030: o_tlul_d_ready=1 expected at edge {e}, got 0"


@cocotb.test()
async def test_chk_031_reset_abandons(dut):
    """CHK-031: reset during A1/A2/A3 abandons the transfer; stale response ignored; next transfers normal."""
    env = await make_env(dut, "chk031")
    r = env.r
    T = env.trace
    for w in (1, 0):
        for point in ("a", "b", "c"):
            dev = {"a": dict(k=4, j=1, mode="ok"), "b": dict(k=0, j=3, mode="ok"), "c": dict(PROMPT)}[point]
            x = Xfer(w, rand_addr(r), 0xF if w else r.randint(0, 15), r.getrandbits(32), r.randint(0, 7),
                     gap=1, dev=dev)
            env.req.add(x)
            if point == "a":
                o = await env.run_until(lambda o, x=x: x.setup_edge is not None and env.edge == x.setup_edge + 1,
                                        30, "CHK-031 (a)")
                assert o["a_valid"] == 1 and len(x.hs) == 0
            elif point == "b":
                o = await env.run_until(lambda o, x=x: x.setup_edge is not None and env.edge == x.setup_edge + 2,
                                        30, "CHK-031 (b)")
                assert o["a_valid"] == 0 and len(x.hs) == 1 and x.resp is None
            else:
                o = await env.run_until(lambda o: o["pready"] == 1, 30, "CHK-031 (c)")
            snap = await env.assert_reset_now()
            check_reset_values(snap, "CHK-031", f"after reset assertion in ({point})")
            await env.hold_reset(3)
            rel = env.edge
            stale = dict(opcode=(ACK if w else ACK_DATA), source=SRC_ID, data=r.getrandbits(32) | 1, error=0,
                         cls="stale")
            env.dev.orphan_fn = (lambda env_, e, o_, ar, rel=rel, stale=stale: stale if e == rel + 1 else None)
            await env.steps(10)
            env.dev.orphan_fn = None
            assert any(o_["edge"] == rel + 1 for o_ in env.dev.orphans)
            for e in range(rel, rel + 10):
                t = T[e]
                assert t["pready"] == 0 and t["pslverr"] == 0 and t["prdata"] == 0 and t["a_valid"] == 0, (
                    f"CHK-031: idle after release expected at edge {e} ({point}), got pready={t['pready']} "
                    f"pslverr={t['pslverr']} prdata={_hx(t['prdata'])} a_valid={t['a_valid']}")
            assert x.abandoned and x.done_edge is None and x not in env.req.done, (
                f"CHK-031: no completion expected for abandoned {x}")
            wx = Xfer(1, rand_addr(r), 0xF, r.getrandbits(32), r.randint(0, 7), gap=0, dev=PROMPT)
            rx = Xfer(0, rand_addr(r), r.randint(0, 15), 0, 0, gap=1, dev=PROMPT)
            env.req.add(wx)
            env.req.add(rx)
            await env.run_all(40, f"CHK-031 ({point}) recovery")
            for y in (wx, rx):
                check_xfer(y, "CHK-031")
                assert y.done_edge == y.setup_edge + 3 and y.pslverr == 0, (
                    f"CHK-031: {y} expected pready at E3 with pslverr=0, got E{y.done_edge - y.setup_edge}")
            assert rx.prdata == rx.resp["data"], f"CHK-031: read prdata={rx.resp['data']:#x} expected, got {_hx(rx.prdata)}"
            await env.steps(2)


@cocotb.test()
async def test_regression_random(dut):
    """CHK-001..CHK-017 (port assertion mirror) and scoreboard: broad legal random traffic."""
    env = await make_env(dut, "regression", keep_trace=False)
    r = env.r
    env.dev.garbage = True
    env.dev.ready_idle_random = True
    env.req.idle_garbage = True

    def policy(x):
        return dict(k=0 if r.random() < 0.4 else r.randint(1, 8), j=r.randint(0, 7),
                    mode="derr" if r.random() < 0.05 else "ok")

    env.dev.policy_fn = policy
    N, B = 3000, 250
    for b in range(N // B):
        xs = []
        for _ in range(B):
            w = r.random() < 0.5
            x = Xfer(w, rand_addr(r), 0xF if w else r.randint(0, 15), r.getrandbits(32), r.randint(0, 7),
                     gap=0 if r.random() < 0.4 else r.randint(1, 5))
            env.req.add(x)
            xs.append(x)
        await env.run_all(B * 40, f"regression batch {b}")
        for x in xs:
            check_xfer(x, "CHK-029")
        if b % 4 == 3:
            snap = await env.assert_reset_now()
            check_reset_values(snap, "CHK-012", "after reset assertion in regression")
            await env.hold_reset(3)
            await env.steps(2)
    for i in range(1, 18):
        cid = f"CHK-{i:03d}"
        if cid == "CHK-007":
            continue  # needs illegal requests: exercised by CHK-018/028/029 tests
        assert env.chk.hits.get(cid, 0) > 0, f"{cid}: assertion antecedent expected to be exercised, got 0 hits"

"""cocotb testbench for ot_rv_timer_nnc (rv_timer behind a TL-UL host interface and an alert receiver).

Timing model
- The TlEnv task drives all inputs right after each falling edge of clk_i and samples all outputs in
  the ReadOnly phase of that same time step.  Sample number k therefore shows exactly what the next
  rising edge sees; in this file "edge k" is the rising edge that follows sample k.
- Acceptance edge of a request = edge with i_a_valid=1 and o_a_ready=1.  D beat = edge with
  o_d_valid=1 and i_d_ready=1 (matched by o_d_source).
- Reset is asserted by the env right after a falling edge (middle of the clock period, asynchronous)
  and released right after a rising edge; i_a_valid is 0 during reset and in the first cycle after.

Everything expected is derived from the rv_timer register tables, the TL-UL / comportability rules
and the decisions D-001..D-018 quoted in the plan.
"""

import cocotb
from collections import deque
# NNC verification fix (fix-verif, triage B): Timer is needed for the power-on reset before the first
# clock edge (CHK-006 / D-016 / RT-2-03).
from cocotb.triggers import Event, FallingEdge, ReadOnly, RisingEdge, Timer
from nnc_cocotb import *  # noqa: F401,F403

# ----------------------------------------------------------------------------------------------
# Constants from the rv_timer register table
# ----------------------------------------------------------------------------------------------
M32 = 0xFFFFFFFF
OP_PUTF = 0
OP_PUTP = 1
OP_GET = 4

A_ALERT = 0x000
A_CTRL = 0x004
A_IE = 0x100
A_IS = 0x104
A_IT = 0x108
A_CFG = 0x10C
A_TVL = 0x110
A_TVU = 0x114
A_CML = 0x118
A_CMU = 0x11C

REG_NAME = {
    A_ALERT: "ALERT_TEST", A_CTRL: "CTRL", A_IE: "INTR_ENABLE0", A_IS: "INTR_STATE0",
    A_IT: "INTR_TEST0", A_CFG: "CFG0", A_TVL: "TIMER_V_LOWER0", A_TVU: "TIMER_V_UPPER0",
    A_CML: "COMPARE_LOWER0_0", A_CMU: "COMPARE_UPPER0_0",
}
MAPPED = (A_ALERT, A_CTRL, A_IE, A_IS, A_IT, A_CFG, A_TVL, A_TVU, A_CML, A_CMU)
UNMAPPED = tuple(o for o in range(0, 0x200, 4) if o not in MAPPED)
RESET_VAL = {
    A_ALERT: 0x80000000, A_CTRL: 0x0, A_IE: 0x0, A_IS: 0x0, A_IT: 0x0, A_CFG: 0x00010000,
    A_TVL: 0x0, A_TVU: 0x0, A_CML: M32, A_CMU: M32,
}
# readable / writable field masks of the rw registers
FIELD_MASK = {
    A_CTRL: 0x1, A_IE: 0x1, A_CFG: 0x00FF0FFF, A_TVL: M32, A_TVU: M32, A_CML: M32, A_CMU: M32,
}
WIDE_REGS = (A_ALERT, A_CFG, A_TVL, A_TVU, A_CML, A_CMU)
INTR_AFFECT = (A_CTRL, A_IE, A_IS, A_IT, A_TVL, A_TVU, A_CML, A_CMU)
BAD_MASKS = (0b0101, 0b1001, 0b1010, 0b1011, 0b1101)


def hx(v):
    return "X" if v is None else f"0x{v:08X}"


def nm(a):
    return REG_NAME.get(a, f"offset 0x{a:03X}")


def _collect_strings(x, out):
    if isinstance(x, str):
        out.append(x)
    elif isinstance(x, dict):
        for k in ("name", "port", "signal", "clock", "reset", "clk", "rst"):
            if k in x:
                _collect_strings(x[k], out)
        for v in x.values():
            _collect_strings(v, out)
    elif isinstance(x, (list, tuple)):
        for v in x:
            _collect_strings(v, out)


def _port_handle(dut, spec, default):
    """Resolve a port handle from the helper-library interface description (string or dict)."""
    cands = []
    _collect_strings(spec, cands)
    cands.append(default)
    for n in cands:
        try:
            if hasattr(dut, n):
                return getattr(dut, n)
        except Exception:
            continue
    assert False, f"(test bench) port {default} not found (interface spec {spec!r})"


# ----------------------------------------------------------------------------------------------
# TL-UL request object
# ----------------------------------------------------------------------------------------------
class Req:
    def __init__(self, opcode, addr, data=0, size=2, mask=0xF, instr=0, flip=0, source=None,
                 not_before=0):
        self.opcode = opcode
        self.addr = addr
        self.data = data & M32
        self.size = size
        self.mask = mask
        self.instr = instr
        self.flip = flip
        self.source = source
        self.not_before = not_before
        self.a_edge = None
        self.r_edge = None
        self.resp = None
        self.done = False
        self.discarded = False

    def is_write(self):
        return self.opcode in (OP_PUTF, OP_PUTP)

    def __repr__(self):
        return (f"Req(op={self.opcode}, addr=0x{self.addr:03X}, data={hx(self.data)}, size={self.size}, "
                f"mask={self.mask:04b}, instr={self.instr}, flip={self.flip}, src={self.source})")


def expected_error(r):
    """d_error classification of CHK-011 / D-012 / D-013 / TL-UL protocol checks.
    Returns 1, 0, or None (not classified)."""
    if r.instr or r.flip or r.addr >= 0x200:
        return None
    must1 = False
    active = None
    if r.opcode not in (OP_PUTF, OP_PUTP, OP_GET) or r.size == 3:
        must1 = True
    else:
        n = 1 << r.size
        if r.addr % n:
            must1 = True
        else:
            active = ((1 << n) - 1) << (r.addr & 3)
            if r.mask & ~active & 0xF:
                must1 = True
            if r.opcode == OP_PUTF and (r.mask & active) != active:
                must1 = True
    if (r.addr & ~3) not in MAPPED:
        must1 = True
    if r.opcode in (OP_PUTF, OP_PUTP) and r.size == 0 and r.mask == 1 and r.addr in WIDE_REGS:
        must1 = True
    if must1:
        return 1
    if r.addr in MAPPED and r.size == 2 and r.mask == 0xF:
        return 0
    if r.opcode == OP_PUTP and r.size == 0 and r.mask == 1 and r.addr in (A_CTRL, A_IE, A_IS, A_IT):
        return 0
    if r.opcode == OP_GET and r.size in (0, 1) and active is not None and r.mask == active:
        return 0
    return None


# ----------------------------------------------------------------------------------------------
# TL-UL host driver + monitor + per-edge recorder
# ----------------------------------------------------------------------------------------------
class TlEnv:
    OUTS = ("o_a_ready", "o_d_valid", "o_d_opcode", "o_d_param", "o_d_size", "o_d_source",
            "o_d_sink", "o_d_data", "o_d_error", "o_d_intg_err", "o_alert",
            "o_alert_integ_fail", "o_intr_timer_expired")
    HOLD = ("o_d_opcode", "o_d_param", "o_d_size", "o_d_source", "o_d_sink", "o_d_data",
            "o_d_error")

    def __init__(self, dut, chk):
        self.dut = dut
        self.chk = chk
        self.clk = _port_handle(dut, CLOCK, "clk_i")
        self.rst = _port_handle(dut, RESET, "rst_ni")
        self.sig = {n: getattr(dut, n) for n in self.OUTS}
        self.cyc = 0
        self.queue = deque()
        self.cur = None
        self.outstanding = {}
        self.max_out = 4
        self.d_ready_mode = 1  # 1, 0, or a float probability
        self.rnd = rng("tl_env_" + chk)
        self.prev_rst = 0
        self.prev = None
        self.violations = []
        self.n_viol = 0
        self.intr_hist = [None]
        self.rst_hist = [None]
        self.dvalid_hist = [None]
        self.alert_edges = []
        self.beats = []
        self.rst_samples = {}
        self.reset_log = []
        self.flip_seen = False
        self.ctrl_active = 0
        self.hooks = []
        self.n_integ_fail = 0
        self.n_dintg = 0
        self._ev = Event()
        self._rst_req = None
        self._rst_cnt = 0
        self._release = False
        self._next_src = 0
        self._task = None

    # ---------------- bookkeeping ----------------
    def viol(self, msg):
        self.n_viol += 1
        if len(self.violations) < 50:
            self.violations.append(msg)

    def finish(self):
        more = f" (+{self.n_viol - 1} more: {self.violations[1:4]})" if self.n_viol > 1 else ""
        assert not self.violations, (self.violations[0] + more) if self.violations else ""

    def start(self):
        d = self.dut
        d.i_a_valid.value = 0
        d.i_a_opcode.value = OP_GET
        d.i_a_param.value = 0
        d.i_a_size.value = 2
        d.i_a_source.value = 0
        d.i_a_address.value = 0
        d.i_a_mask.value = 0xF
        d.i_a_data.value = 0
        d.i_a_instr.value = 0
        d.i_a_intg_flip.value = 0
        d.i_d_ready.value = 1
        self._task = cocotb.start_soon(self._run())

    def _busy_sources(self):
        s = set(self.outstanding.keys())
        s.update(q.source for q in self.queue)
        if self.cur is not None:
            s.add(self.cur.source)
        return s

    def issue(self, opcode, addr, data=0, size=2, mask=0xF, instr=0, flip=0, source=None,
              not_before=0):
        busy = self._busy_sources()
        if source is None:
            for _ in range(256):
                s = self._next_src
                self._next_src = (self._next_src + 1) & 0xFF
                if s not in busy:
                    source = s
                    break
            assert source is not None, f"{self.chk}: (test bench) no free a_source"
        else:
            assert source not in busy, f"{self.chk}: (test bench) a_source {source} already in use"
        r = Req(opcode, addr, data, size, mask, instr, flip, source, not_before)
        self.queue.append(r)
        return r

    # ---------------- main loop ----------------
    async def _run(self):
        d = self.dut
        while True:
            await FallingEdge(self.clk)
            self.cyc += 1
            k = self.cyc
            asserting = False
            if self._rst_req is not None and self.cur is None and self._rst_cnt == 0:
                self.rst.value = 0
                self._rst_cnt = self._rst_req
                self._rst_req = None
                self.reset_log.append([k, None])
                asserting = True
            can_drive = (not asserting) and self._rst_cnt == 0 and self.prev_rst == 1
            if self.cur is None:
                if (can_drive and self.queue and len(self.outstanding) < self.max_out
                        and self.queue[0].not_before <= k):
                    r = self.queue.popleft()
                    self._check_host(r, k)
                    self.cur = r
                    d.i_a_opcode.value = r.opcode
                    d.i_a_param.value = 0
                    d.i_a_size.value = r.size
                    d.i_a_source.value = r.source
                    d.i_a_address.value = r.addr
                    d.i_a_mask.value = r.mask
                    d.i_a_data.value = r.data
                    d.i_a_instr.value = r.instr
                    d.i_a_intg_flip.value = r.flip
                    d.i_a_valid.value = 1
                else:
                    d.i_a_valid.value = 0
            m = self.d_ready_mode
            if isinstance(m, float):
                dr = 1 if self.rnd.random() < m else 0
            else:
                dr = 1 if m else 0
            d.i_d_ready.value = dr
            await ReadOnly()
            self._sample(k, dr)
            ev = self._ev
            self._ev = Event()
            ev.set()
            if self._release:
                self._release = False
                await RisingEdge(self.clk)
                self.rst.value = 1

    def _check_host(self, r, k):
        if r.addr >= 0x200:
            self.viol(f"CHK-008: (test bench) a_address < 0x200 expected, got 0x{r.addr:X}")
        if r.mask in BAD_MASKS:
            self.viol(f"CHK-008: (test bench) forbidden a_mask {r.mask:04b}")
        if r.instr and r.opcode in (OP_PUTF, OP_PUTP):
            self.viol("CHK-008: (test bench) instruction-type write presented")
        if r.is_write() and r.addr == A_ALERT and r.data == 1:
            self.viol("CHK-008: (test bench) write of 0x00000001 to ALERT_TEST presented")
        if r.is_write() and r.addr in (A_CFG, A_TVL, A_TVU):
            ctrl_out = any(o.is_write() and o.addr == A_CTRL for o in self.outstanding.values())
            if self.ctrl_active or ctrl_out:
                self.viol(f"CHK-008: (test bench) write to {nm(r.addr)} at edge {k} while active")

    def _check_resp(self, r, k):
        e = r.resp["error"]
        if r.opcode not in (OP_PUTF, OP_PUTP, OP_GET):
            if e != 1:
                self.viol(f"CHK-010: undefined opcode {r.opcode} expected d_error=1, got {e} (edge {k})")
        else:
            exp_op = 1 if r.opcode == OP_GET else 0
            if r.resp["opcode"] != exp_op:
                self.viol(f"CHK-010: d_opcode {exp_op} expected for {r!r}, got {r.resp['opcode']} (edge {k})")
            if r.resp["size"] != r.size:
                self.viol(f"CHK-010: d_size {r.size} expected for {r!r}, got {r.resp['size']} (edge {k})")
        ee = expected_error(r)
        if ee is not None and e != ee:
            self.viol(f"CHK-011: d_error={ee} expected for {r!r}, got {e} (edge {k})")

    def _sample(self, k, dr):
        s = {n: val(self.sig[n]) for n in self.OUTS}
        rst = val(self.rst)
        s["rst"] = rst
        s["dr"] = dr
        self.rst_hist.append(rst)
        self.intr_hist.append(s["o_intr_timer_expired"])
        self.dvalid_hist.append(s["o_d_valid"])
        if rst != 1:
            self.rst_samples[k] = s
            for n in ("o_d_valid", "o_alert", "o_alert_integ_fail", "o_intr_timer_expired"):
                if s[n] != 0:
                    self.viol(f"CHK-006: {n}=0 while rst_ni=0 expected, got {s[n]} at edge {k}")
            for r in list(self.outstanding.values()):
                r.discarded = True
                r.done = True
            self.outstanding.clear()
            if self.cur is not None:
                self.cur.discarded = True
                self.cur.done = True
                self.cur = None
            self.flip_seen = False
            self.ctrl_active = 0
            self.prev = None
            self.prev_rst = 0
            if self._rst_cnt > 0:
                self._rst_cnt -= 1
                if self._rst_cnt == 0:
                    self._release = True
            return
        if self.prev_rst == 0 and self.reset_log and self.reset_log[-1][1] is None:
            self.reset_log[-1][1] = k
        if s["o_alert_integ_fail"] != 0:
            self.n_integ_fail += 1
            self.viol(f"CHK-001: o_alert_integ_fail=0 expected at edge {k}, got {s['o_alert_integ_fail']}")
        if s["o_d_intg_err"] != 0:
            self.n_dintg += 1
            self.viol(f"CHK-013: o_d_intg_err=0 expected at edge {k}, got {s['o_d_intg_err']}")
        al = s["o_alert"]
        if al == 1:
            self.alert_edges.append(k)
            if self.prev is not None and self.prev["o_alert"] == 1:
                self.viol(f"CHK-002: o_alert one-cycle pulse expected, got 1 at edges {k - 1} and {k}")
        elif al != 0:
            self.viol(f"CHK-002: o_alert 0/1 expected at edge {k}, got X")
        p = self.prev
        if p is not None and not self.flip_seen and p["o_d_valid"] == 1 and p["dr"] == 0:
            if s["o_d_valid"] != 1:
                self.viol(f"CHK-012: o_d_valid held at 1 under back-pressure expected at edge {k}, got {s['o_d_valid']}")
            else:
                for n in self.HOLD:
                    if s[n] != p[n]:
                        self.viol(f"CHK-012: {n} stable under back-pressure expected at edge {k}, got {p[n]} -> {s[n]}")
                        break
        # A channel acceptance
        if self.cur is not None and s["o_a_ready"] == 1:
            r = self.cur
            self.cur = None
            r.a_edge = k
            self.outstanding[r.source] = r
            if r.flip:
                self.flip_seen = True
        # D channel beat
        if s["o_d_valid"] == 1 and dr == 1:
            src = s["o_d_source"]
            self.beats.append((k, src))
            r = self.outstanding.pop(src, None) if src is not None else None
            if r is None:
                if not self.flip_seen:
                    self.viol(f"CHK-009: D beat at edge {k} with d_source={src} matches no outstanding request")
            else:
                r.r_edge = k
                r.resp = {"opcode": s["o_d_opcode"], "size": s["o_d_size"], "data": s["o_d_data"],
                          "error": s["o_d_error"], "source": src, "param": s["o_d_param"],
                          "sink": s["o_d_sink"]}
                r.done = True
                if not self.flip_seen and not r.flip:
                    self._check_resp(r, k)
                if r.is_write() and r.addr == A_CTRL and r.resp["error"] == 0 and not r.flip:
                    self.ctrl_active = r.data & 1
        for h in self.hooks:
            h(k, s)
        self.prev_rst = 1
        self.prev = s

    # ---------------- waiting helpers ----------------
    async def edge(self):
        await self._ev.wait()

    async def edges(self, n):
        for _ in range(int(n)):
            await self.edge()

    async def until(self, k):
        for _ in range(max(0, int(k) - self.cyc)):
            await self.edge()

    async def wait_req(self, r, timeout=400):
        for _ in range(timeout):
            if r.done:
                break
            await self.edge()
        assert r.done, f"{self.chk}: response to {r!r} expected within {timeout} cycles, got none"
        return r

    async def wait_intr(self, v, max_cycles, what):
        for _ in range(max_cycles):
            if self.intr_hist[-1] == v:
                return self.cyc
            await self.edge()
        assert self.intr_hist[-1] == v, f"{self.chk}: {what}: o_intr_timer_expired={v} expected within {max_cycles} cycles, got {self.intr_hist[-1]}"
        return self.cyc

    async def reset(self, cycles):
        """Assert rst_ni=0 right after a falling edge for `cycles` rising edges, release it right
        after a rising edge.  Returns (first edge with rst_ni=0, first edge with rst_ni=1)."""
        n0 = len(self.reset_log)
        self._rst_req = cycles
        for _ in range(cycles + 500):
            await self.edge()
            if len(self.reset_log) > n0 and self.reset_log[-1][1] is not None:
                return tuple(self.reset_log[-1])
        assert False, f"{self.chk}: (test bench) reset sequence did not complete"

    # ---------------- transactions ----------------
    async def access(self, opcode, addr, data=0, size=2, mask=0xF, instr=0, flip=0, source=None,
                     not_before=0, timeout=400):
        r = self.issue(opcode, addr, data, size, mask, instr, flip, source, not_before)
        await self.wait_req(r, timeout + max(0, not_before - self.cyc))
        return r

    async def rdr(self, addr, chk=None, size=2, mask=0xF, not_before=0):
        chk = chk or self.chk
        r = await self.access(OP_GET, addr, size=size, mask=mask, not_before=not_before)
        assert not r.discarded, f"{chk}: read of {nm(addr)} expected a response, got discarded by reset"
        assert r.resp["error"] == 0, f"{chk}: read of {nm(addr)} expected d_error=0, got {r.resp['error']}"
        assert r.resp["opcode"] == 1, f"{chk}: read of {nm(addr)} expected d_opcode=1, got {r.resp['opcode']}"
        assert r.resp["data"] is not None, f"{chk}: read of {nm(addr)} expected defined d_data, got X"
        return r.resp["data"], r

    async def rd(self, addr, chk=None, size=2, mask=0xF, not_before=0):
        v, _ = await self.rdr(addr, chk, size, mask, not_before)
        return v

    async def wr(self, addr, data, chk=None, opcode=OP_PUTF, size=2, mask=0xF, not_before=0,
                 expect_err=0):
        chk = chk or self.chk
        r = await self.access(opcode, addr, data, size, mask, not_before=not_before)
        assert not r.discarded, f"{chk}: write to {nm(addr)} expected a response, got discarded by reset"
        if expect_err is not None:
            assert r.resp["error"] == expect_err, (
                f"{chk}: write {hx(data)} to {nm(addr)} (op {opcode}, size {size}, mask {mask:04b}) "
                f"expected d_error={expect_err}, got {r.resp['error']}")
        return r

    # ---------------- history queries ----------------
    def intr_bad(self, lo, hi, v):
        hi = min(hi, self.cyc)
        for k in range(max(lo, 1), hi + 1):
            if self.rst_hist[k] == 1 and self.intr_hist[k] != v:
                return k
        return None

    def intr_first(self, lo, hi, v):
        hi = min(hi, self.cyc)
        for k in range(max(lo, 1), hi + 1):
            if self.rst_hist[k] == 1 and self.intr_hist[k] == v:
                return k
        return None

    def alerts_in(self, lo, hi):
        return [e for e in self.alert_edges if lo <= e <= hi]


# ----------------------------------------------------------------------------------------------
# Reference model of the rv_timer register file / interrupt (specification based)
# ----------------------------------------------------------------------------------------------
class TimerRefModel:
    """IS is 0, 1 or None (unknown, where the specification leaves the behaviour open:
    mtime >= mtimecmp while the timer is inactive)."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.r = {a: RESET_VAL[a] for a in FIELD_MASK}
        self.regwen = 1
        self.IS = 0
        self.settle = 0
        self.busy = 0
        self.tvu0 = 0
        self.tvl0 = 0
        self.act_a = 0
        self.act_P = 0
        self.act_S = 1

    @property
    def active(self):
        return self.r[A_CTRL] & 1

    def cond(self):
        if self.active:
            # by construction while active: COMPARE_UPPER < tvu0 (true) or >= tvu0+2 (false)
            return self.r[A_CMU] < self.tvu0
        mt = (self.r[A_TVU] << 32) | self.r[A_TVL]
        mc = (self.r[A_CMU] << 32) | self.r[A_CML]
        return mt >= mc

    def expect_read(self, addr):
        if addr == A_ALERT:
            return 0x80000000 if self.regwen else 0x0
        if addr == A_IT:
            return 0
        if addr == A_IS:
            return self.IS
        if addr in (A_TVL, A_TVU) and self.active:
            return None
        return self.r[addr]

    def apply_write(self, addr, data):
        """Effect of an error-free write (data = value on the enabled lanes). Returns the number of
        cycles after the D beat after which IS_0 and the interrupt output are stable."""
        data &= M32
        if addr == A_ALERT:
            if not (data >> 31) & 1:
                self.regwen = 0
            return 0
        if addr == A_IT:
            if data & 1:
                self.IS = 1
            return 6
        if addr == A_IS:
            if data & 1:
                c = self.cond()
                if not c:
                    self.IS = 0
                elif self.active:
                    self.IS = 1
                else:
                    self.IS = None
            return 6
        assert addr != A_CTRL, "(test bench) CTRL writes go through activate/deactivate"
        self.r[addr] = data & FIELD_MASK[addr]
        if addr in (A_CML, A_CMU):
            c = self.cond()
            if not c:
                self.IS = 0
            elif self.active:
                self.IS = 1
                return self.act_P + 12
            else:
                self.IS = None
            return 6
        if addr in (A_TVL, A_TVU):
            if self.cond() and self.IS != 1:
                self.IS = None
            return 6
        if addr == A_IE:
            return 6
        return 0

    def activate(self, a_edge):
        self.r[A_CTRL] = 1
        self.tvu0 = self.r[A_TVU]
        self.tvl0 = self.r[A_TVL]
        self.act_a = a_edge
        self.act_P = self.r[A_CFG] & 0xFFF
        self.act_S = (self.r[A_CFG] >> 16) & 0xFF
        if self.cond():
            self.IS = 1
        return self.act_P + 12

    def tv_ok(self, addr, v, r_edge):
        if v is None:
            return False
        S, P = self.act_S, self.act_P
        if addr == A_TVU:
            return v == self.tvu0 if S == 0 else v in (self.tvu0, self.tvu0 + 1)
        if S == 0:
            return v == self.tvl0
        dlt = (v - self.tvl0) & M32
        return dlt % S == 0 and dlt // S <= (r_edge - self.act_a) // (P + 1) + 2


def make_intr_hook(env, M):
    def hook(k, s):
        # NNC verification fix (fix-verif, triage B): RT-2-04 / D-016: while rst_ni is 0 every register
        # holds its reset value, so at the first sample after reset release (k == release edge) the
        # reference model must already be in its reset state (IS_0 = IE_0 = 0, settled at the release
        # edge). Before, the model was reset only after env.reset() returned, i.e. after this hook had
        # compared the release sample against the pre-reset model. The later M.reset() calls in the
        # test are idempotent.
        if env.reset_log and env.reset_log[-1][1] == k:
            busy = M.busy
            M.reset()
            M.busy = busy
            M.settle = k
        if env.flip_seen or M.busy or k < M.settle or M.IS is None:
            return
        exp = M.IS & M.r[A_IE] & 1
        got = s["o_intr_timer_expired"]
        if got != exp:
            env.viol(f"CHK-026: o_intr_timer_expired = IS_0&IE_0 = {exp} expected at edge {k}, got {got}")
    return hook


# NNC verification fix (fix-verif, triage B): CHK-006 / D-016 (RT-8-30) require o_d_valid, o_alert,
# o_alert_integ_fail and o_intr_timer_expired = 0 at EVERY rising edge where rst_ni=0, and RT-2-03
# says rst_ni is "asserted asynchronously". Before, the clock was started at t=0 while rst_ni still had
# its default value 0, which had never been asserted (no falling edge on rst_ni). So the first rising
# clk_i edge at t=0 saw rst_ni=0 with the asynchronously reset flops not yet reset (a_CHK_006 failed
# @0). Now, once per simulation and before the clock starts, rst_ni is driven inactive and then
# active (a real asynchronous assertion edge). Every rising edge with rst_ni=0 is then a reset that
# has really been asserted. The check itself is unchanged (no time-0 exclusion, no disable).
_POWER_ON_RESET_DONE = False


async def _power_on_reset(dut):
    global _POWER_ON_RESET_DONE
    if _POWER_ON_RESET_DONE:
        return
    _POWER_ON_RESET_DONE = True
    rsts = [(getattr(dut, r["name"]), bool(r["active_low"])) for r in RESETS]
    if not rsts:
        rsts = [(_port_handle(dut, RESET, "rst_ni"), True)]
    for h, low in rsts:
        h.value = 1 if low else 0      # inactive level first ...
    await Timer(1, unit="ps")
    for h, low in rsts:
        h.value = 0 if low else 1      # ... then an asynchronous assertion edge, before any clock edge
    await Timer(1, unit="ps")


async def setup(dut, chk, rst_cycles=5):
    # NNC verification fix (fix-verif, triage B): assert reset asynchronously before the first clock
    # edge of the simulation (CHK-006 / D-016 / RT-2-03); see _power_on_reset.
    await _power_on_reset(dut)
    start_clock(dut)
    await reset_dut(dut, cycles=rst_cycles)
    env = TlEnv(dut, chk)
    env.start()
    await env.edges(2)
    dut._log.info(f"{chk}: PARAMS={PARAMS}")
    return env


# ==============================================================================================
# CHK-014
# ==============================================================================================
@cocotb.test()
async def test_chk_014_alert_test_fatal_fault(dut):
    """CHK-014: ALERT_TEST.fatal_fault triggers exactly one alert per write; wo/reserved bits read 0."""
    C = "CHK-014"
    env = await setup(dut, C)
    k0 = env.cyc
    await env.edges(50)
    p = env.alerts_in(k0, env.cyc)
    assert not p, f"{C}: no o_alert pulse during 50 idle cycles expected, got pulses at {p}"
    for i in range(3):
        r = await env.wr(A_ALERT, 0x80000001, C)
        await env.until(r.r_edge + 100)
        p = env.alerts_in(r.a_edge, r.r_edge + 100)
        assert len(p) == 1 and p[0] <= r.r_edge + 16, (
            f"{C}: write {i}: exactly one o_alert pulse in [a={r.a_edge}, r+16={r.r_edge + 16}] and none "
            f"up to r+100 expected, got pulses at {p}")
        v = await env.rd(A_ALERT, C)
        assert v == 0x80000000, f"{C}: ALERT_TEST read 0x80000000 expected, got {hx(v)}"
        await env.edges(100)
    reqs = [env.issue(OP_PUTF, A_ALERT, 0x80000001) for _ in range(3)]
    for r in reqs:
        await env.wait_req(r)
    for r in reqs:
        assert not r.discarded and r.resp["error"] == 0, f"{C}: burst write d_error=0 expected, got {r.resp}"
    for j in (1, 2):
        assert reqs[j].a_edge - reqs[j - 1].a_edge <= 10, (
            f"{C}: (stimulus) burst writes accepted within 10 cycles expected, got edges "
            f"{[q.a_edge for q in reqs]}")
    last = max(q.r_edge for q in reqs)
    await env.until(last + 100)
    n = len(env.alerts_in(reqs[0].a_edge, last + 100))
    assert 1 <= n <= 3, f"{C}: 1..3 o_alert pulses for the closely spaced burst expected, got {n}"
    for data in (0x80000000, 0xFFFFFFFE):
        r = await env.wr(A_ALERT, data, C)
        await env.until(r.r_edge + 100)
        p = env.alerts_in(r.a_edge, r.r_edge + 100)
        assert not p, f"{C}: no o_alert pulse after write {hx(data)} expected, got pulses at {p}"
    v = await env.rd(A_ALERT, C)
    assert v == 0x80000000, f"{C}: ALERT_TEST read 0x80000000 expected, got {hx(v)}"
    assert env.n_integ_fail == 0, f"{C}: o_alert_integ_fail=0 throughout expected, got 1 at {env.n_integ_fail} edges"
    env.finish()


# ==============================================================================================
# CHK-015
# ==============================================================================================
@cocotb.test()
async def test_chk_015_alert_regwen_rw0c(dut):
    """CHK-015: ALERT_TEST.regwen is rw0c and locks alert testing until reset."""
    C = "CHK-015"
    env = await setup(dut, C)
    await env.wr(A_ALERT, 0x80000000, C)
    v = await env.rd(A_ALERT, C)
    assert v == 0x80000000, f"{C}: step 1 ALERT_TEST 0x80000000 expected, got {hx(v)}"
    k1 = env.cyc
    await env.wr(A_ALERT, 0x00000000, C)
    v = await env.rd(A_ALERT, C)
    assert v == 0x0, f"{C}: step 2 ALERT_TEST 0x00000000 expected, got {hx(v)}"
    p = env.alerts_in(k1, env.cyc)
    assert not p, f"{C}: step 2 no o_alert pulse expected, got pulses at {p}"
    r = await env.wr(A_ALERT, 0x80000001, C)
    await env.until(r.r_edge + 100)
    p = env.alerts_in(r.a_edge, r.r_edge + 100)
    assert not p, f"{C}: step 3 no o_alert pulse with regwen=0 expected, got pulses at {p}"
    v = await env.rd(A_ALERT, C)
    assert v == 0x0, f"{C}: step 3 ALERT_TEST 0x00000000 expected, got {hx(v)}"
    await env.wr(A_ALERT, 0x80000000, C)
    v = await env.rd(A_ALERT, C)
    assert v == 0x0, f"{C}: step 4 regwen cannot be set again: 0x00000000 expected, got {hx(v)}"
    await env.reset(5)
    v = await env.rd(A_ALERT, C)
    assert v == 0x80000000, f"{C}: step 6 ALERT_TEST after reset 0x80000000 expected, got {hx(v)}"
    r = await env.wr(A_ALERT, 0x80000001, C)
    await env.until(r.r_edge + 100)
    p = env.alerts_in(r.a_edge, r.r_edge + 100)
    assert len(p) == 1 and p[0] <= r.r_edge + 16, (
        f"{C}: step 6 exactly one o_alert pulse at an edge <= r+16={r.r_edge + 16} expected, got {p}")
    env.finish()


# ==============================================================================================
# CHK-016
# ==============================================================================================
async def _flip_run(env, C, opcode, addr, data, run):
    r = env.issue(opcode, addr, data, flip=1)
    for _ in range(100):
        if r.a_edge is not None:
            break
        await env.edge()
    assert r.a_edge is not None, f"{C}: run {run}: corrupted request accepted within 100 cycles expected, got not accepted"
    a = r.a_edge
    for _ in range(32):  # do not wait more than 32 cycles for the response (D-010)
        if r.done:
            break
        await env.edge()
    await env.edges(1000)
    ka, krel = await env.reset(5)
    p = env.alerts_in(a, ka - 1)
    assert p and p[0] <= a + 16, f"{C}: run {run}: first o_alert pulse in [a={a}, a+16] expected, got {p[:3]}"
    gaps = [(p[i], p[i + 1]) for i in range(len(p) - 1) if p[i + 1] - p[i] > 32]
    assert not gaps, f"{C}: run {run}: a pulse in every 32-edge window expected, got gaps {gaps[:3]}"
    assert p[-1] >= (ka - 1) - 31, (
        f"{C}: run {run}: a pulse in the last 32 edges before reset (edge {ka}) expected, got last pulse {p[-1]}")
    bad = [k for k in range(ka, krel) if env.rst_samples.get(k, {}).get("o_alert") != 0]
    assert not bad, f"{C}: run {run}: o_alert=0 while rst_ni=0 expected, got 1/X at {bad}"
    await env.edges(200)
    p2 = env.alerts_in(krel, krel + 199)
    assert not p2, f"{C}: run {run}: o_alert=0 for 200 cycles after reset release expected, got pulses at {p2}"
    r2 = await env.access(OP_GET, A_CFG)
    assert r2.resp["error"] == 0 and r2.resp["data"] == 0x00010000, (
        f"{C}: run {run}: CFG0 read d_error=0, 0x00010000 expected, got err={r2.resp['error']} data={hx(r2.resp['data'])}")


@cocotb.test()
async def test_chk_016_intg_error_fatal_alert(dut):
    """CHK-016: command integrity error raises a repeating fatal alert until reset."""
    C = "CHK-016"
    env = await setup(dut, C)
    env.d_ready_mode = 1
    await _flip_run(env, C, OP_GET, A_IS, 0, 1)
    await _flip_run(env, C, OP_PUTF, A_IE, 0x1, 2)
    assert env.n_integ_fail == 0, f"{C}: o_alert_integ_fail=0 throughout expected, got 1 at {env.n_integ_fail} edges"
    assert env.n_dintg == 0, f"{C}: o_d_intg_err=0 throughout expected, got 1 at {env.n_dintg} edges"
    env.finish()


# ==============================================================================================
# CHK-017
# ==============================================================================================
@cocotb.test()
async def test_chk_017_unmapped_offsets(dut):
    """CHK-017: unmapped offsets in 0x000..0x1FC return d_error=1 and change nothing."""
    C = "CHK-017"
    env = await setup(dut, C)
    k0 = env.cyc
    for off in UNMAPPED:
        r = await env.access(OP_GET, off)
        assert r.resp["error"] == 1 and r.resp["opcode"] == 1, (
            f"{C}: Get to 0x{off:03X} d_error=1, d_opcode=1 expected, got {r.resp['error']}, {r.resp['opcode']}")
        r = await env.access(OP_PUTF, off, M32)
        assert r.resp["error"] == 1 and r.resp["opcode"] == 0, (
            f"{C}: PutFullData to 0x{off:03X} d_error=1, d_opcode=0 expected, got {r.resp['error']}, {r.resp['opcode']}")
    for a in MAPPED:
        v = await env.rd(a, C)
        assert v == RESET_VAL[a], f"{C}: {nm(a)} unchanged {hx(RESET_VAL[a])} expected, got {hx(v)}"
    p = env.alerts_in(k0, env.cyc)
    assert not p, f"{C}: no o_alert pulse expected, got {p}"
    bad = env.intr_bad(k0, env.cyc, 0)
    assert bad is None, f"{C}: o_intr_timer_expired=0 throughout expected, got 1 at edge {bad}"
    env.finish()


# ==============================================================================================
# CHK-018
# ==============================================================================================
@cocotb.test()
async def test_chk_018_byte_writes(dut):
    """CHK-018: byte writes fail on wide registers and succeed on the 1-bit registers."""
    C = "CHK-018"
    env = await setup(dut, C)
    # NOTE: the second ALERT_TEST byte write carries 0x80000001: byte lane 0 is 0x01 as the plan
    # requires, while a write of exactly 0x00000001 to 0x000 is excluded by CHK-008(3) / D-009.
    errs = [(A_CFG, 0x05), (A_TVL, 0x00), (A_TVU, 0x00), (A_CML, 0x00), (A_CMU, 0x00),
            (A_ALERT, 0x00000000), (A_ALERT, 0x80000001)]
    first_a = None
    last_r = None
    for a, d in errs:
        r = await env.access(OP_PUTP, a, d, size=0, mask=0x1)
        if first_a is None:
            first_a = r.a_edge
        last_r = r.r_edge
        assert r.resp["error"] == 1, f"{C}: byte write to {nm(a)} d_error=1 expected, got {r.resp['error']}"
    exp = {A_CFG: 0x00010000, A_TVL: 0, A_TVU: 0, A_CML: M32, A_CMU: M32, A_ALERT: 0x80000000}
    for a, e in exp.items():
        v = await env.rd(a, C)
        assert v == e, f"{C}: {nm(a)} unchanged {hx(e)} after failed byte write expected, got {hx(v)}"
    await env.until(last_r + 100)
    p = env.alerts_in(first_a, last_r + 100)
    assert not p, f"{C}: no o_alert pulse within 100 cycles expected, got {p}"
    r = await env.wr(A_IE, 0x01, C, opcode=OP_PUTP, size=0, mask=1, expect_err=0)
    v = await env.rd(A_IE, C)
    assert v == 1, f"{C}: INTR_ENABLE0 0x1 after byte write expected, got {hx(v)}"
    r = await env.wr(A_IT, 0x01, C, opcode=OP_PUTP, size=0, mask=1, expect_err=0)
    v = await env.rd(A_IS, C, not_before=r.r_edge + 4)
    assert v == 1, f"{C}: INTR_STATE0 0x1 after INTR_TEST0 byte write expected, got {hx(v)}"
    r = await env.wr(A_IS, 0x01, C, opcode=OP_PUTP, size=0, mask=1, expect_err=0)
    v = await env.rd(A_IS, C, not_before=r.r_edge + 4)
    assert v == 0, f"{C}: INTR_STATE0 0x0 after INTR_STATE0 byte write expected, got {hx(v)}"
    await env.wr(A_CTRL, 0x01, C, opcode=OP_PUTP, size=0, mask=1, expect_err=0)
    v = await env.rd(A_CTRL, C)
    assert v == 1, f"{C}: CTRL 0x1 after byte write expected, got {hx(v)}"
    await env.wr(A_CTRL, 0x00, C, opcode=OP_PUTP, size=0, mask=1, expect_err=0)
    v = await env.rd(A_CTRL, C)
    assert v == 0, f"{C}: CTRL 0x0 after byte write expected, got {hx(v)}"
    env.finish()


# ==============================================================================================
# CHK-019
# ==============================================================================================
@cocotb.test()
async def test_chk_019_protocol_errors(dut):
    """CHK-019: illegal opcode/size/alignment/mask requests get exactly one d_error=1 response."""
    C = "CHK-019"
    env = await setup(dut, C)
    cases = [(op, A_CFG, 2, 0xF) for op in (2, 3, 5, 6, 7)]
    cases += [(OP_GET, A_TVL, 3, 0xF), (OP_PUTF, A_TVL, 3, 0xF), (OP_GET, 0x112, 2, 0xF),
              (OP_GET, 0x111, 1, 0x3), (OP_GET, 0x110, 0, 0x2), (OP_PUTF, A_CML, 2, 0x7)]
    for op, a, sz, mk in cases:
        r = await env.access(op, a, 0, size=sz, mask=mk)
        assert r.resp["error"] == 1, (
            f"{C}: op={op} addr=0x{a:03X} size={sz} mask={mk:04b} d_error=1 expected, got {r.resp['error']}")
        if op == OP_GET:
            assert r.resp["opcode"] == 1 and r.resp["size"] == sz, (
                f"{C}: Get echo d_opcode=1, d_size={sz} expected, got {r.resp['opcode']}, {r.resp['size']}")
        if op == OP_PUTF:
            assert r.resp["opcode"] == 0 and r.resp["size"] == sz, (
                f"{C}: PutFullData echo d_opcode=0, d_size={sz} expected, got {r.resp['opcode']}, {r.resp['size']}")
        await env.edges(4)
        extra = [b for b in env.beats if b[1] == r.source and b[0] > r.r_edge]
        assert not extra, f"{C}: exactly one response for {r!r} expected, got extra beats {extra}"
    v = await env.rd(A_CFG, C)
    assert v == 0x00010000, f"{C}: final CFG0 read 0x00010000 expected, got {hx(v)}"
    env.finish()


# ==============================================================================================
# CHK-020
# ==============================================================================================
@cocotb.test()
async def test_chk_020_subword_reads(dut):
    """CHK-020: aligned sub-word reads return the full register word without error."""
    C = "CHK-020"
    env = await setup(dut, C)
    await env.wr(A_CFG, 0x00AB0123, C)
    await env.wr(A_CML, 0x89ABCDEF, C)
    reads = [(A_CFG + k, 0, 1 << k, 0x00AB0123) for k in range(4)]
    reads += [(A_CML, 1, 0x3, 0x89ABCDEF), (A_CML + 2, 1, 0xC, 0x89ABCDEF)]
    for a, sz, mk, e in reads:
        r = await env.access(OP_GET, a, size=sz, mask=mk)
        rs = r.resp
        assert rs["error"] == 0 and rs["opcode"] == 1 and rs["size"] == sz, (
            f"{C}: Get 0x{a:03X} size {sz}: d_error=0, d_opcode=1, d_size={sz} expected, got "
            f"{rs['error']}, {rs['opcode']}, {rs['size']}")
        assert rs["data"] == e, f"{C}: Get 0x{a:03X} size {sz} full word {hx(e)} expected, got {hx(rs['data'])}"
    env.finish()


# ==============================================================================================
# CHK-021
# ==============================================================================================
@cocotb.test()
async def test_chk_021_instruction_fetch(dut):
    """CHK-021: instruction-fetch Gets are answered and have no side effects (d_error unchecked)."""
    C = "CHK-021"
    env = await setup(dut, C)
    await env.wr(A_CFG, 0x00030005, C)
    await env.wr(A_CML, 0x12345678, C)
    k0 = env.cyc
    for a in MAPPED:
        r = await env.access(OP_GET, a, instr=1)
        rs = r.resp
        assert rs["source"] == r.source and rs["size"] == 2 and rs["opcode"] == 1, (
            f"{C}: fetch of {nm(a)}: d_source={r.source}, d_size=2, d_opcode=1 expected, got "
            f"{rs['source']}, {rs['size']}, {rs['opcode']}")
        await env.edges(3)
        extra = [b for b in env.beats if b[1] == r.source and b[0] > r.r_edge]
        assert not extra, f"{C}: exactly one response per fetch expected, got extra {extra}"
    await env.edges(50)
    p = env.alerts_in(k0, env.cyc)
    assert not p, f"{C}: no o_alert pulse within 50 cycles expected, got {p}"
    assert env.n_dintg == 0, f"{C}: o_d_intg_err=0 expected, got 1 at {env.n_dintg} edges"
    exp = dict(RESET_VAL)
    exp[A_CFG] = 0x00030005
    exp[A_CML] = 0x12345678
    for a in MAPPED:
        v = await env.rd(a, C)
        assert v == exp[a], f"{C}: {nm(a)} {hx(exp[a])} expected after fetches, got {hx(v)}"
    env.finish()


# ==============================================================================================
# CHK-022
# ==============================================================================================
@cocotb.test()
async def test_chk_022_intr_by_tick(dut):
    """CHK-022: IS_0 and the interrupt are raised by a tick when mtime >= mtimecmp and stay latched."""
    C = "CHK-022"
    env = await setup(dut, C)
    for (P, S, Cv) in ((0, 1, 20), (3, 3, 10), (47, 1, 2)):
        tag = f"(P,S,C)=({P},{S},{Cv})"
        m = -(-Cv // S)
        await env.wr(A_CFG, (S << 16) | P, C)
        await env.wr(A_TVL, 0, C)
        await env.wr(A_TVU, 0, C)
        await env.wr(A_CMU, 0, C)
        await env.wr(A_CML, Cv, C)
        await env.wr(A_IE, 1, C)
        rc = await env.wr(A_IS, 1, C)
        w = await env.wr(A_CTRL, 1, C)
        a0, t0 = w.a_edge, w.r_edge
        await env.until(t0 + m * (P + 1) + 50)
        hi0 = a0 + (m - 1) * (P + 1) - 1
        bad = env.intr_bad(rc.r_edge + 6, hi0, 0)
        assert bad is None, f"{C}: {tag} o_intr=0 at every edge before {hi0 + 1} expected, got 1 at edge {bad}"
        dl = t0 + (P + 5) + (m - 1) * (P + 1) + 6
        rise = env.intr_first(a0, dl, 1)
        assert rise is not None, f"{C}: {tag} o_intr=1 at some edge <= {dl} expected, got none"
        wo = await env.wr(A_CTRL, 0, C)
        vis = await env.rd(A_IS, C)
        vtl = await env.rd(A_TVL, C)
        await env.until(wo.r_edge + P + 6)
        wc = await env.wr(A_CMU, M32, C)
        bad = env.intr_bad(rise, wc.a_edge, 1)
        assert bad is None, f"{C}: {tag} o_intr stays 1 from edge {rise} expected, got 0 at edge {bad}"
        assert vis == 1, f"{C}: {tag} INTR_STATE0 0x1 expected, got {hx(vis)}"
        assert vtl >= Cv and vtl % S == 0, f"{C}: {tag} TIMER_V_LOWER0 >= {Cv} and multiple of {S} expected, got {vtl}"
        if (P, S, Cv) == (3, 3, 10):
            assert vtl >= 12, f"{C}: {tag} TIMER_V_LOWER0 >= 12 expected, got {vtl}"
    env.finish()


# ==============================================================================================
# CHK-023 / CHK-024
# ==============================================================================================
async def _flow_023(env, C):
    k0 = env.cyc
    await env.wr(A_CFG, 0x00010007, C)
    await env.wr(A_TVL, 0, C)
    await env.wr(A_TVU, 0, C)
    await env.wr(A_IE, 1, C)
    await env.wr(A_CTRL, 1, C)
    await env.edges(100)
    await env.wr(A_CMU, 0, C)
    wl = await env.wr(A_CML, 0x5, C)
    r = wl.r_edge
    await env.until(r + 14)
    bad = env.intr_bad(k0, wl.a_edge, 0)
    assert bad is None, f"{C}: o_intr=0 until the COMPARE_LOWER0_0 write is accepted expected, got 1 at edge {bad}"
    rise = env.intr_first(wl.a_edge, r + 14, 1)
    assert rise is not None, f"{C}: o_intr=1 at some edge <= r+14={r + 14} expected, got none"
    v = await env.rd(A_IS, C, not_before=r + 12)
    assert v == 1, f"{C}: INTR_STATE0 0x1 expected, got {hx(v)}"


@cocotb.test()
async def test_chk_023_intr_by_compare_write(dut):
    """CHK-023: interrupt raised by a compare write while active within prescale+1+4 cycles."""
    C = "CHK-023"
    env = await setup(dut, C)
    await _flow_023(env, C)
    env.finish()


@cocotb.test()
async def test_chk_024_clear_by_compare_write(dut):
    """CHK-024: compare writes clear/re-raise IS_0; TIMER_V writes do not clear it."""
    C = "CHK-024"
    env = await setup(dut, C)
    await _flow_023(env, C)
    # (a)
    ra = await env.wr(A_CMU, 0x1, C)
    v = await env.rd(A_IS, C, not_before=ra.r_edge + 4)
    assert v == 0, f"{C}: (a) INTR_STATE0 0x0 expected, got {hx(v)}"
    # (b)
    rb = await env.wr(A_CMU, 0x0, C)
    bad = env.intr_bad(ra.r_edge + 4, rb.a_edge, 0)
    assert bad is None, f"{C}: (a) o_intr=0 from r+4 expected, got 1 at edge {bad}"
    v = await env.rd(A_IS, C, not_before=rb.r_edge + 4)
    assert v == 1, f"{C}: (b) INTR_STATE0 0x1 expected, got {hx(v)}"
    # (c)
    rc = await env.wr(A_CML, 0xFFFFFFF0, C)
    bad = env.intr_bad(rb.r_edge + 6, rc.a_edge, 1)
    assert bad is None, f"{C}: (b) o_intr=1 from r+6 expected, got 0 at edge {bad}"
    v = await env.rd(A_IS, C, not_before=rc.r_edge + 4)
    assert v == 0, f"{C}: (c) INTR_STATE0 0x0 expected, got {hx(v)}"
    # (d)
    rdd = await env.wr(A_CML, 0x0, C)
    bad = env.intr_bad(rc.r_edge + 4, rdd.a_edge, 0)
    assert bad is None, f"{C}: (c) o_intr=0 from r+4 expected, got 1 at edge {bad}"
    v = await env.rd(A_IS, C, not_before=rdd.r_edge + 4)
    assert v == 1, f"{C}: (d) INTR_STATE0 0x1 expected, got {hx(v)}"
    # (e)
    tv = 0
    for _ in range(100):
        tv = await env.rd(A_TVL, C)
        if tv > 0x100:
            break
        await env.edges(100)
    assert tv > 0x100, f"{C}: (stimulus) mtime > 0x100 expected, got {hx(tv)}"
    re1 = await env.wr(A_CML, 0x80, C)
    v = await env.rd(A_IS, C, not_before=re1.r_edge + 4)
    assert v == 1, f"{C}: (e) INTR_STATE0 0x1 after COMPARE_LOWER0_0=0x80 (mtime>0x100) expected, got {hx(v)}"
    await env.wr(A_CTRL, 0, C)
    await env.edges(20)
    await env.wr(A_TVL, 0, C)
    rt = await env.wr(A_TVU, 0, C)
    v = await env.rd(A_IS, C, not_before=rt.r_edge + 4)
    assert v == 1, f"{C}: (e) INTR_STATE0 0x1 after TIMER_V writes expected, got {hx(v)}"
    re2 = await env.wr(A_CML, 0x80, C)
    # NNC verification fix (fix-verif, triage B): D-006 (RT-8-08/RT-8-09): after a compare write with
    # mtime >= mtimecmp still true, IS_0 is 1 again within 4 cycles and "a dip in between is not
    # checked". re1 is such a compare write, so the o_intr=1 window restarts after it: (d) is checked
    # over [rdd.r+6, re1.a] and (e) over [re1.r+6, re2.a] (covers the CTRL=0 and TIMER_V writes).
    bad = env.intr_bad(rdd.r_edge + 6, re1.a_edge, 1)
    assert bad is None, f"{C}: (d) o_intr stays 1 from r+6 until the next compare write expected, got 0 at edge {bad}"
    bad = env.intr_bad(re1.r_edge + 6, re2.a_edge, 1)
    assert bad is None, f"{C}: (d)/(e) o_intr stays 1 until the clearing write expected, got 0 at edge {bad}"
    v = await env.rd(A_IS, C, not_before=re2.r_edge + 4)
    assert v == 0, f"{C}: (e) INTR_STATE0 0x0 after COMPARE_LOWER0_0 write expected, got {hx(v)}"
    await env.until(re2.r_edge + 40)
    bad = env.intr_bad(re2.r_edge + 4, env.cyc, 0)
    assert bad is None, f"{C}: (e) o_intr=0 from r+4 expected, got 1 at edge {bad}"
    env.finish()


# ==============================================================================================
# CHK-025
# ==============================================================================================
@cocotb.test()
async def test_chk_025_intr_state_rw1c(dut):
    """CHK-025: INTR_STATE0 is rw1c; an active event re-asserts it; writing 0 has no effect."""
    C = "CHK-025"
    env = await setup(dut, C)
    await env.wr(A_CFG, 0x00010000, C)
    await env.wr(A_TVL, 0, C)
    await env.wr(A_TVU, 0, C)
    await env.wr(A_CMU, 0, C)
    await env.wr(A_CML, 0x10, C)
    await env.wr(A_IE, 1, C)
    await env.wr(A_CTRL, 1, C)
    rise = await env.wait_intr(1, 300, "(stimulus) interrupt after activation")
    await env.wr(A_IS, 0x0, C)
    v = await env.rd(A_IS, C)
    assert v == 1, f"{C}: (a) INTR_STATE0 0x1 after writing 0 expected, got {hx(v)}"
    bad = env.intr_bad(rise, env.cyc, 1)
    assert bad is None, f"{C}: (a) o_intr stays 1 after writing 0 expected, got 0 at edge {bad}"
    for i in range(5):
        w = await env.wr(A_IS, 0x1, C)
        v = await env.rd(A_IS, C, not_before=w.r_edge + 4)
        assert v == 1, f"{C}: (a) W1C #{i}: INTR_STATE0 0x1 (event still active) expected, got {hx(v)}"
        bad = env.intr_bad(w.r_edge + 6, env.cyc, 1)
        assert bad is None, f"{C}: (a) W1C #{i}: o_intr=1 from r+6 expected, got 0 at edge {bad}"
    await env.wr(A_CMU, M32, C)
    await env.wr(A_IT, 0x1, C)
    w = await env.wr(A_IS, 0x1, C)
    v = await env.rd(A_IS, C, not_before=w.r_edge + 4)
    assert v == 0, f"{C}: (b) INTR_STATE0 0x0 expected, got {hx(v)}"
    await env.until(w.r_edge + 110)
    bad = env.intr_bad(w.r_edge + 6, w.r_edge + 110, 0)
    assert bad is None, f"{C}: (b) o_intr=0 from r+6 for 100 cycles expected, got 1 at edge {bad}"
    env.finish()


# ==============================================================================================
# CHK-026
# ==============================================================================================
@cocotb.test()
async def test_chk_026_intr_enable_masking(dut):
    """CHK-026: o_intr = IS_0 AND IE_0; INTR_STATE0 is not qualified by IE_0."""
    C = "CHK-026"
    env = await setup(dut, C)
    k0 = env.cyc
    P = 0
    await env.wr(A_CFG, 0x00010000, C)
    await env.wr(A_TVL, 0, C)
    await env.wr(A_TVU, 0, C)
    await env.wr(A_CMU, 0, C)
    await env.wr(A_CML, 20, C)
    await env.wr(A_IE, 0, C)
    await env.wr(A_IS, 1, C)
    w = await env.wr(A_CTRL, 1, C)
    t0 = w.r_edge
    await env.until(t0 + 20 + 50)
    v = await env.rd(A_IS, C, not_before=t0 + (P + 5) + 19 + 4 + 1)
    assert v == 1, f"{C}: INTR_STATE0 0x1 with IE_0=0 expected, got {hx(v)}"
    await env.wr(A_CTRL, 0, C)
    bad = env.intr_bad(k0, env.cyc, 0)
    assert bad is None, f"{C}: o_intr=0 throughout the IE_0=0 run expected, got 1 at edge {bad}"
    r1 = await env.wr(A_IE, 1, C)
    v1 = await env.rd(A_IS, C)
    r2 = await env.wr(A_IE, 0, C)
    bad = env.intr_bad(r1.r_edge + 2, r2.a_edge, 1)
    assert bad is None, f"{C}: o_intr=1 in [r1+2, a2] expected, got 0 at edge {bad}"
    v2 = await env.rd(A_IS, C)
    r3 = await env.wr(A_IE, 1, C)
    bad = env.intr_bad(r2.r_edge + 2, r3.a_edge, 0)
    assert bad is None, f"{C}: o_intr=0 in [r2+2, a3] expected, got 1 at edge {bad}"
    v3 = await env.rd(A_IS, C)
    await env.until(r3.r_edge + 30)
    bad = env.intr_bad(r3.r_edge + 2, env.cyc, 1)
    assert bad is None, f"{C}: o_intr=1 from r3+2 expected, got 0 at edge {bad}"
    for i, vv in enumerate((v1, v2, v3)):
        assert vv == 1, f"{C}: INTR_STATE0 0x1 after INTR_ENABLE0 write {i + 1} expected, got {hx(vv)}"
    env.finish()


# ==============================================================================================
# CHK-027
# ==============================================================================================
@cocotb.test()
async def test_chk_027_intr_test(dut):
    """CHK-027: INTR_TEST0.T_0 (wo) sets the latched IS_0; reads 0; writing 0 has no effect."""
    C = "CHK-027"
    env = await setup(dut, C)
    await env.wr(A_IE, 1, C)
    r = await env.wr(A_IT, 0x1, C)
    v = await env.rd(A_IS, C, not_before=r.r_edge + 4)
    assert v == 1, f"{C}: step 2 INTR_STATE0 0x1 expected, got {hx(v)}"
    v = await env.rd(A_IT, C)
    assert v == 0, f"{C}: step 2 INTR_TEST0 reads 0x0 expected, got {hx(v)}"
    await env.until(r.r_edge + 106)
    bad = env.intr_bad(r.r_edge + 6, r.r_edge + 106, 1)
    assert bad is None, f"{C}: step 2 o_intr=1 from r+6 for 100 cycles expected, got 0 at edge {bad}"
    rp = await env.wr(A_IS, 0x1, C)
    await env.wr(A_IT, 0x0, C)
    v = await env.rd(A_IS, C, not_before=rp.r_edge + 4)
    assert v == 0, f"{C}: step 4 INTR_STATE0 0x0 expected, got {hx(v)}"
    r5 = await env.wr(A_IT, M32, C)
    bad = env.intr_bad(rp.r_edge + 6, r5.a_edge, 0)
    assert bad is None, f"{C}: step 3 o_intr=0 from r'+6 expected, got 1 at edge {bad}"
    v = await env.rd(A_IT, C)
    assert v == 0, f"{C}: step 5 INTR_TEST0 reads 0x0 expected, got {hx(v)}"
    v = await env.rd(A_IS, C, not_before=r5.r_edge + 4)
    assert v == 1, f"{C}: step 5 INTR_STATE0 0x1 expected, got {hx(v)}"
    r6 = await env.wr(A_IS, 0x1, C)
    rie = await env.wr(A_IE, 0x0, C)
    rit = await env.wr(A_IT, 0x1, C)
    v = await env.rd(A_IS, C, not_before=rit.r_edge + 4)
    assert v == 1, f"{C}: step 6 INTR_STATE0 0x1 expected, got {hx(v)}"
    await env.edges(20)
    lo = max(r6.r_edge + 6, rie.r_edge + 2)
    bad = env.intr_bad(lo, env.cyc, 0)
    assert bad is None, f"{C}: step 6 o_intr stays 0 with IE_0=0 expected, got 1 at edge {bad}"
    env.finish()


# ==============================================================================================
# CHK-028
# ==============================================================================================
@cocotb.test()
async def test_chk_028_reset_values(dut):
    """CHK-028: every register reads its documented reset value at its documented offset."""
    C = "CHK-028"
    env = await setup(dut, C, rst_cycles=10)
    k0 = env.cyc
    for a in MAPPED:
        r = await env.access(OP_GET, a)
        rs = r.resp
        assert rs["error"] == 0 and rs["opcode"] == 1, (
            f"{C}: {nm(a)} Get d_error=0, d_opcode=1 expected, got {rs['error']}, {rs['opcode']}")
        assert rs["data"] == RESET_VAL[a], f"{C}: {nm(a)} reset value {hx(RESET_VAL[a])} expected, got {hx(rs['data'])}"
    bad = env.intr_bad(1, env.cyc, 0)
    assert bad is None, f"{C}: o_intr_timer_expired=0 throughout expected, got 1 at edge {bad}"
    p = env.alerts_in(k0 - 2, env.cyc)
    assert not p, f"{C}: o_alert=0 throughout expected, got pulses at {p}"
    env.finish()


# ==============================================================================================
# CHK-029
# ==============================================================================================
@cocotb.test()
async def test_chk_029_rw_fields(dut):
    """CHK-029: rw fields store data, reserved bits read 0; PutFullData and PutPartialData succeed."""
    C = "CHK-029"
    env = await setup(dut, C)
    R = rng("chk029")
    for a in (A_CFG, A_TVL, A_TVU, A_CML, A_CMU, A_IE):
        pats = [M32, 0x0, 0xA5A5A5A5, 0x5A5A5A5A] + [R.getrandbits(32) for _ in range(8)]
        for i, p in enumerate(pats):
            op = OP_PUTF if i % 2 == 0 else OP_PUTP
            await env.wr(a, p, C, opcode=op)
            v = await env.rd(a, C)
            e = p & FIELD_MASK[a]
            assert v == e, f"{C}: {nm(a)} after write {hx(p)} (op {op}) {hx(e)} expected, got {hx(v)}"
    for p in (0xFFFFFFFE, M32, 0x0):
        await env.wr(A_CTRL, p, C)
        v = await env.rd(A_CTRL, C)
        assert v == p & 1, f"{C}: CTRL after write {hx(p)} {hx(p & 1)} expected, got {hx(v)}"
    env.finish()


# ==============================================================================================
# CHK-030
# ==============================================================================================
@cocotb.test()
async def test_chk_030_async_reset(dut):
    """CHK-030: asynchronous reset with a 2-cycle window restores every register; pending response discarded."""
    C = "CHK-030"
    env = await setup(dut, C)
    # (a)
    await env.wr(A_CFG, 0x00020003, C)
    await env.wr(A_TVL, 0x100, C)
    await env.wr(A_TVU, 0x2, C)
    await env.wr(A_CMU, 0x0, C)
    await env.wr(A_CML, 0x10, C)
    await env.wr(A_IE, 1, C)
    await env.wr(A_IT, 1, C)
    await env.wr(A_CTRL, 1, C)
    await env.wait_intr(1, 200, "(stimulus) interrupt set before reset")
    ka, krel = await env.reset(2)
    for k in range(ka, krel):
        s = env.rst_samples.get(k)
        assert s is not None, f"{C}: (a) sample with rst_ni=0 at edge {k} expected, got none"
        for n in ("o_intr_timer_expired", "o_d_valid", "o_alert"):
            assert s[n] == 0, f"{C}: (a) {n}=0 at edge {k} (rst_ni=0, asserted at {ka}) expected, got {s[n]}"
    for a in MAPPED:
        v = await env.rd(a, C)
        assert v == RESET_VAL[a], f"{C}: (a) {nm(a)} reset value {hx(RESET_VAL[a])} expected, got {hx(v)}"
    await env.edges(50)
    v = await env.rd(A_TVL, C)
    assert v == 0, f"{C}: (a) TIMER_V_LOWER0 0 after 50 cycles (inactive) expected, got {hx(v)}"
    # (b)
    env.d_ready_mode = 0
    r = env.issue(OP_GET, A_CFG)
    # NNC verification fix (fix-verif, triage B): CHK-030(b) step 1 "Send a Get to 0x10C with i_d_ready=0
    # and wait until o_d_valid=1": wait until the Get is accepted and a NEW o_d_valid=1 sample appears
    # after its acceptance edge; the old loop exited at once on the stale o_d_valid=1 sample of the
    # previous TIMER_V_LOWER0 response, so the reset hit before the Get was even driven (D-016).
    for _ in range(100):
        if r.a_edge is not None and env.cyc > r.a_edge and env.dvalid_hist[-1] == 1:
            break
        await env.edge()
    assert r.a_edge is not None, f"{C}: (b) (stimulus) held Get accepted before reset expected, got not accepted"
    assert env.cyc > r.a_edge and env.dvalid_hist[-1] == 1, f"{C}: (b) (stimulus) o_d_valid=1 for the held Get expected, got {env.dvalid_hist[-1]}"
    src = r.source
    ka, krel = await env.reset(3)
    assert r.discarded, f"{C}: (b) pending response discarded by reset expected, got {r.resp}"
    for k in range(ka, krel):
        assert env.rst_samples[k]["o_d_valid"] == 0, f"{C}: (b) o_d_valid=0 while rst_ni=0 expected at edge {k}, got 1"
    env.d_ready_mode = 1
    nb = len(env.beats)
    await env.edges(20)
    assert len(env.beats) == nb, f"{C}: (b) no D beat in 20 idle cycles after reset expected, got {env.beats[nb:]}"
    r2 = await env.access(OP_GET, A_CFG, source=src)
    assert r2.resp["error"] == 0 and r2.resp["data"] == 0x00010000, (
        f"{C}: (b) new Get d_error=0, 0x00010000 expected, got {r2.resp['error']}, {hx(r2.resp['data'])}")
    await env.edges(5)
    cnt = [b for b in env.beats if b[1] == src and b[0] >= krel]
    assert len(cnt) == 1, f"{C}: (b) exactly one response for the new Get expected, got {cnt}"
    env.finish()


# ==============================================================================================
# CHK-031
# ==============================================================================================
@cocotb.test()
async def test_chk_031_tick_and_step(dut):
    """CHK-031: mtime increases by step every prescale+1 cycles while active and stops when inactive."""
    C = "CHK-031"
    env = await setup(dut, C)
    V0 = 0x1000
    for (P, S) in ((0, 1), (0, 0xFF), (1, 1), (3, 5), (47, 1), (0xFFF, 0x80), (10, 0)):
        tag = f"(P,S)=({P},{S})"
        await env.wr(A_CFG, (S << 16) | P, C)
        await env.wr(A_TVU, 0, C)
        await env.wr(A_TVL, V0, C)
        await env.wr(A_CTRL, 1, C)
        nreads = 3 if P == 0xFFF else 10
        reads = []
        for _ in range(nreads):
            await env.edges(20 * (P + 1))
            v, rq = await env.rdr(A_TVL, C)
            reads.append((rq.a_edge, rq.r_edge, v))
        for i, (ai, ri, vi) in enumerate(reads):
            if S == 0:
                assert vi == V0, f"{C}: {tag} read {i}: v=V0={hx(V0)} with step 0 expected, got {hx(vi)}"
            else:
                assert (vi - V0) % S == 0, f"{C}: {tag} read {i}: (v-V0) mod S = 0 expected, got v={hx(vi)}"
            if i:
                assert vi >= reads[i - 1][2], f"{C}: {tag} non-decreasing values expected, got {hx(reads[i - 1][2])} -> {hx(vi)}"
        if S > 0:
            for i in range(len(reads)):
                for j in range(i + 1, len(reads)):
                    ai, ri, vi = reads[i]
                    aj, rj, vj = reads[j]
                    n = (vj - vi) // S
                    lo = (aj - ri) // (P + 1)
                    hi = (rj - ai) // (P + 1) + 1
                    assert lo <= n <= hi, f"{C}: {tag} reads {i},{j}: tick count {lo} <= n <= {hi} expected, got n={n}"
        wo = await env.wr(A_CTRL, 0, C)
        await env.until(wo.r_edge + P + 5)
        v1 = await env.rd(A_TVL, C)
        await env.edges(2 * (P + 1) + 10)
        v2 = await env.rd(A_TVL, C)
        assert v1 == v2, f"{C}: {tag} timer stopped after deactivation expected, got {hx(v1)} then {hx(v2)}"
    env.finish()


# ==============================================================================================
# CHK-032
# ==============================================================================================
@cocotb.test()
async def test_chk_032_inactive_and_first_tick(dut):
    """CHK-032: no counting while inactive; first tick within prescale+1+4 cycles after activation."""
    C = "CHK-032"
    env = await setup(dut, C)
    base = env.cyc - 2
    for t in (10, 50, 100):
        v = await env.rd(A_TVL, C, not_before=base + t)
        assert v == 0, f"{C}: TIMER_V_LOWER0 0 at {t} cycles after reset expected, got {hx(v)}"
    for P in (0, 5, 47):
        await env.wr(A_CFG, (1 << 16) | P, C)
        await env.wr(A_TVL, 0, C)
        await env.wr(A_TVU, 0, C)
        w = await env.wr(A_CTRL, 1, C)
        a0, t0 = w.a_edge, w.r_edge
        v, rq = await env.rdr(A_TVL, C, not_before=t0 + P + 6)
        assert rq.a_edge <= t0 + P + 10, f"{C}: P={P} (stimulus) read accepted by t0+P+10={t0 + P + 10} expected, got {rq.a_edge}"
        ub = (rq.r_edge - a0) // (P + 1) + 1
        assert 1 <= v <= ub, f"{C}: P={P} first tick: 1 <= v <= {ub} expected, got {v}"
        wo = await env.wr(A_CTRL, 0, C)
        await env.until(wo.r_edge + P + 6)
    env.finish()


# ==============================================================================================
# CHK-033
# ==============================================================================================
@cocotb.test()
async def test_chk_033_carry_and_64bit_compare(dut):
    """CHK-033: carry from TIMER_V_LOWER0 into TIMER_V_UPPER0; the compare uses all 64 bits."""
    C = "CHK-033"
    env = await setup(dut, C)
    k0 = env.cyc
    await env.wr(A_CFG, 0x00010000, C)
    await env.wr(A_TVL, 0xFFFFFFF0, C)
    await env.wr(A_TVU, 0x5, C)
    await env.wr(A_CMU, 0x6, C)
    await env.wr(A_CML, 0x10, C)
    await env.wr(A_IE, 1, C)
    w = await env.wr(A_CTRL, 1, C)
    a0, t0 = w.a_edge, w.r_edge
    wo = await env.wr(A_CTRL, 0, C, not_before=t0 + 50)
    assert t0 + 40 <= wo.a_edge <= t0 + 100, f"{C}: (stimulus) CTRL=0 accepted in [t0+40, t0+100] expected, got {wo.a_edge - t0}"
    await env.edges(10)
    vu = await env.rd(A_TVU, C)
    vl = await env.rd(A_TVL, C)
    bad = env.intr_bad(k0, a0 + 30, 0)
    assert bad is None, f"{C}: A: o_intr=0 before a0+31 expected, got 1 at edge {bad}"
    rise = env.intr_first(a0, t0 + 42, 1)
    assert rise is not None, f"{C}: A: o_intr=1 at some edge <= t0+42 expected, got none"
    bad = env.intr_bad(rise, env.cyc, 1)
    assert bad is None, f"{C}: A: o_intr stays 1 expected, got 0 at edge {bad}"
    assert vu == 0x6, f"{C}: A: TIMER_V_UPPER0 0x00000006 after carry expected, got {hx(vu)}"
    assert 0x10 <= vl <= 0x100, f"{C}: A: 0x10 <= TIMER_V_LOWER0 <= 0x100 expected, got {hx(vl)}"
    # Case B
    await env.wr(A_CFG, 0x00300001, C)
    await env.wr(A_TVU, 0, C)
    await env.wr(A_TVL, 0xFFFFFFF0, C)
    w = await env.wr(A_CTRL, 1, C)
    await env.until(w.r_edge + 50)
    await env.wr(A_CTRL, 0, C)
    await env.edges(10)
    vu = await env.rd(A_TVU, C)
    vl = await env.rd(A_TVL, C)
    V = (vu << 32) | vl
    assert V > 0xFFFFFFF0 and (V - 0xFFFFFFF0) % 0x30 == 0, f"{C}: B: V > 0xFFFFFFF0 and (V-0xFFFFFFF0) mod 0x30 = 0 expected, got 0x{V:X}"
    assert vu == 0x1, f"{C}: B: TIMER_V_UPPER0 0x00000001 expected, got {hx(vu)}"
    env.finish()


# ==============================================================================================
# CHK-034
# ==============================================================================================
@cocotb.test()
async def test_chk_034_wrap_2_64(dut):
    """CHK-034: mtime wraps modulo 2^64; mtimecmp = 2^64-step fires before the wrap and stays latched."""
    C = "CHK-034"
    env = await setup(dut, C)
    k0 = env.cyc
    await env.wr(A_CFG, 0x00030000, C)
    await env.wr(A_TVU, M32, C)
    await env.wr(A_TVL, 0xFFFFFFE0, C)
    await env.wr(A_CMU, M32, C)
    await env.wr(A_CML, 0xFFFFFFFD, C)
    await env.wr(A_IE, 1, C)
    w = await env.wr(A_CTRL, 1, C)
    a0, t0 = w.a_edge, w.r_edge
    await env.wr(A_CTRL, 0, C, not_before=t0 + 60)
    await env.edges(10)
    vu = await env.rd(A_TVU, C)
    vl = await env.rd(A_TVL, C)
    vis = await env.rd(A_IS, C)
    bad = env.intr_bad(k0, a0 + 8, 0)
    assert bad is None, f"{C}: A: o_intr=0 before a0+9 expected, got 1 at edge {bad}"
    rise = env.intr_first(a0, t0 + 20, 1)
    assert rise is not None, f"{C}: A: o_intr=1 at some edge <= t0+20 expected, got none"
    rw = await env.wr(A_IS, 0x1, C)
    bad = env.intr_bad(rise, rw.a_edge, 1)
    assert bad is None, f"{C}: A: o_intr still 1 after the wrap expected, got 0 at edge {bad}"
    assert vu == 0x0, f"{C}: A: TIMER_V_UPPER0 0x0 after wrap expected, got {hx(vu)}"
    assert vl < 0x100 and (vl + 0x20) % 3 == 0, f"{C}: A: TIMER_V_LOWER0 < 0x100 and (v+0x20) mod 3 = 0 expected, got {hx(vl)}"
    assert vis == 1, f"{C}: A: INTR_STATE0 0x1 expected, got {hx(vis)}"
    v = await env.rd(A_IS, C, not_before=rw.r_edge + 4)
    assert v == 0, f"{C}: A: INTR_STATE0 0x0 after W1C expected, got {hx(v)}"
    await env.until(rw.r_edge + 30)
    bad = env.intr_bad(rw.r_edge + 6, env.cyc, 0)
    assert bad is None, f"{C}: A: o_intr=0 from r+6 expected, got 1 at edge {bad}"
    # Case B
    await env.wr(A_CFG, 0x00010000, C)
    await env.wr(A_TVU, M32, C)
    await env.wr(A_TVL, M32, C)
    w = await env.wr(A_CTRL, 1, C)
    await env.until(w.r_edge + 30)
    await env.wr(A_CTRL, 0, C)
    await env.edges(10)
    vu = await env.rd(A_TVU, C)
    vl = await env.rd(A_TVL, C)
    assert vu == 0 and vl < 0x100, f"{C}: B: UPPER=0, LOWER<0x100 after wrap expected, got {hx(vu)}, {hx(vl)}"
    env.finish()


# ==============================================================================================
# CHK-035
# ==============================================================================================
@cocotb.test()
async def test_chk_035_outstanding_backpressure(dut):
    """CHK-035: pipelined requests (<=4 outstanding), a_ready stalls and random d_ready back-pressure."""
    C = "CHK-035"
    env = await setup(dut, C)
    env.max_out = 4
    env.d_ready_mode = 0.5
    R = rng("chk035")
    model = dict(RESET_VAL)
    WR = (A_CFG, A_TVL, A_TVU, A_CML, A_CMU, A_IE)
    active = []
    k0 = env.cyc
    nchk = 0

    def retire():
        nonlocal nchk
        keep = []
        for it in active:
            r, a, isw, exp = it
            if not r.done:
                keep.append(it)
                continue
            assert not r.discarded, f"{C}: response for {r!r} expected, got discarded"
            assert r.resp["error"] == 0, f"{C}: {r!r} d_error=0 expected, got {r.resp['error']}"
            if not isw:
                assert r.resp["data"] == exp, f"{C}: read of {nm(a)} {hx(exp)} expected, got {hx(r.resp['data'])}"
            nchk += 1
        active[:] = keep

    for _ in range(2000):
        if R.random() < 0.5:
            a, isw, op, data = R.choice(MAPPED), False, OP_GET, 0
        else:
            a, isw, op, data = R.choice(WR), True, R.choice([OP_PUTF, OP_PUTP]), R.getrandbits(32)
            if a == A_TVU:
                data &= 0x7FFFFFFF  # keeps mtime < mtimecmp: INTR_STATE0 stays at its reset value
            if a == A_CMU:
                data |= 0x80000000
        ok = False
        for _ in range(2000):
            retire()
            conflict = any(x == a and (isw or w) for (_, x, w, _) in active)
            if not conflict and len(active) < 4:
                ok = True
                break
            await env.edge()
        assert ok, f"{C}: request slot free within 2000 cycles expected, got still busy"
        if isw:
            model[a] = data & FIELD_MASK[a]
            exp = None
        else:
            exp = model[a]
        r = env.issue(op, a, data)
        active.append((r, a, isw, exp))
        g = R.choice([0, 0, 0, 0, 1, 2, 3, 6])
        if g:
            await env.edges(g)
    for _ in range(3000):
        retire()
        if not active:
            break
        await env.edge()
    assert not active, f"{C}: all responses received expected, got {len(active)} missing"
    assert nchk == 2000, f"{C}: 2000 checked responses expected, got {nchk}"
    bad = env.intr_bad(k0, env.cyc, 0)
    assert bad is None, f"{C}: o_intr_timer_expired=0 expected, got 1 at edge {bad}"
    p = env.alerts_in(k0, env.cyc)
    assert not p, f"{C}: no o_alert expected, got {p[:5]}"
    env.finish()


# ==============================================================================================
# Random regression
# ==============================================================================================
@cocotb.test()
async def test_regression_random(dut):
    """CHK-001..CHK-013, CHK-035: broad random legal traffic (all operations, errors, bursts, back-pressure,
    timer activity, interrupts, alerts, resets, final integrity fault) checked against TimerRefModel."""
    C = "CHK-035"
    env = await setup(dut, C)
    R = rng("regression")
    M = TimerRefModel()
    env.hooks.append(make_intr_hook(env, M))
    st = {"alert_qual": 0, "last_alert_r": -1000, "since": env.cyc}
    N = 800
    reset_points = {N // 3, (2 * N) // 3}
    regwen_clear_at = (17 * N) // 20
    active_ops = 0

    def check_read(a, r):
        v = r.resp["data"]
        if a in (A_TVL, A_TVU) and M.active:
            assert M.tv_ok(a, v, r.r_edge), (
                f"CHK-031: {nm(a)} read while active within the tick bounds expected (base "
                f"{hx(M.tvu0)}:{hx(M.tvl0)}, P={M.act_P}, S={M.act_S}), got {hx(v)}")
            return
        e = M.expect_read(a)
        if e is None:
            return
        assert v == e, f"{C}: {nm(a)} reference value {hx(e)} expected, got {hx(v)}"

    async def mwrite(a, data, opcode=OP_PUTF, size=2, mask=0xF):
        aff = a in INTR_AFFECT
        if aff:
            M.busy += 1
        r = await env.wr(a, data, C, opcode=opcode, size=size, mask=mask, expect_err=0)
        extra = M.apply_write(a, data)
        if aff:
            M.busy -= 1
            M.settle = max(M.settle, r.r_edge + extra)
        return r

    def cmu_choice():
        if R.random() < 0.5:
            return R.randint(0, M.tvu0 - 1)
        return R.randint(M.tvu0 + 2, M32)

    async def activate():
        P = R.choice([0, 1, 2, 3, 7, 15])
        S = R.choice([0, 1, 2, 3, 0x10, 0xFF])
        tvu0 = R.randint(1, 0x7FFFFFF0)
        await mwrite(A_CFG, (S << 16) | P | (R.getrandbits(32) & ~0x00FF0FFF & M32))
        await mwrite(A_TVU, tvu0)
        await mwrite(A_TVL, R.getrandbits(32))
        M.tvu0 = tvu0
        await mwrite(A_CMU, cmu_choice())
        M.busy += 1
        r = await env.wr(A_CTRL, 1 | (R.getrandbits(32) & ~1 & M32), C)
        extra = M.activate(r.a_edge)
        M.busy -= 1
        M.settle = max(M.settle, r.r_edge + extra)

    async def deactivate():
        M.busy += 1
        r = await env.wr(A_CTRL, R.getrandbits(32) & ~1 & M32, C)
        await env.until(r.r_edge + M.act_P + 6)
        vu, ru = await env.rdr(A_TVU, C)
        check_read(A_TVU, ru)
        vl, rl = await env.rdr(A_TVL, C)
        check_read(A_TVL, rl)
        M.r[A_CTRL] = 0
        M.r[A_TVU] = vu
        M.r[A_TVL] = vl
        M.busy -= 1
        M.settle = max(M.settle, env.cyc + 1)

    async def op_alert(data=None):
        await env.until(st["last_alert_r"] + 40)
        if data is None:
            data = 0x80000001 if R.random() < 0.6 else (0x80000000 | (R.getrandbits(31) & 0x7FFFFFFE))
        qual = bool(M.regwen and (data & 1))
        r = await env.wr(A_ALERT, data, C)
        M.apply_write(A_ALERT, data)
        await env.until(r.r_edge + 36)
        p = env.alerts_in(r.a_edge, r.r_edge + 36)
        if qual:
            assert len(p) == 1 and p[0] <= r.r_edge + 16, f"CHK-014: one o_alert pulse in [a, r+16] expected, got {p}"
            st["alert_qual"] += 1
        else:
            assert not p, f"CHK-015: no o_alert pulse for ALERT_TEST write {hx(data)} (regwen={M.regwen}) expected, got {p}"
        st["last_alert_r"] = r.r_edge

    async def op_read():
        a = R.choice(MAPPED)
        r = await env.access(OP_GET, a, not_before=(M.settle if a == A_IS else 0))
        assert not r.discarded and r.resp["error"] == 0, f"CHK-011: Get of {nm(a)} d_error=0 expected, got {r.resp}"
        check_read(a, r)

    async def op_read_sub():
        a = R.choice(MAPPED)
        if R.random() < 0.5:
            k = R.randrange(4)
            addr, sz, mk = a + k, 0, 1 << k
        else:
            h = R.choice([0, 2])
            addr, sz, mk = a + h, 1, 0x3 << h
        r = await env.access(OP_GET, addr, size=sz, mask=mk, not_before=(M.settle if a == A_IS else 0))
        assert not r.discarded and r.resp["error"] == 0, f"CHK-020: sub-word Get 0x{addr:03X} d_error=0 expected, got {r.resp}"
        check_read(a, r)

    async def op_write_rw():
        cands = [A_CML, A_CMU] + ([] if M.active else [A_CFG, A_TVL, A_TVU])
        a = R.choice(cands)
        data = R.getrandbits(32)
        if M.active and a == A_CMU:
            data = cmu_choice()
        await mwrite(a, data, R.choice([OP_PUTF, OP_PUTP]))

    async def op_small(a, choices):
        if R.random() < 0.3:
            await mwrite(a, R.getrandbits(8), OP_PUTP, 0, 1)
        else:
            await mwrite(a, R.choice(choices), R.choice([OP_PUTF, OP_PUTP]))

    async def op_err():
        kind = R.choice(["unm_get", "unm_put", "badop", "size3", "misal", "badmask", "pf_partial", "byte_wide"])
        if kind == "unm_get":
            args = (OP_GET, R.choice(UNMAPPED), 0, 2, 0xF)
        elif kind == "unm_put":
            args = (R.choice([OP_PUTF, OP_PUTP]), R.choice(UNMAPPED), R.getrandbits(32), 2, 0xF)
        elif kind == "badop":
            a = R.choice([A_CML, A_CMU, A_IE, R.choice(UNMAPPED)])
            args = (R.choice([2, 3, 5, 6, 7]), a, M.r.get(a, R.getrandbits(32)), 2, 0xF)
        elif kind == "size3":
            args = (OP_GET, R.choice(MAPPED), 0, 3, 0xF)
        elif kind == "misal":
            b = R.choice(MAPPED)
            args = R.choice([(OP_GET, b + R.choice([1, 2, 3]), 0, 2, 0xF), (OP_GET, b + 1, 0, 1, 0x6),
                             (OP_GET, b + 3, 0, 1, 0x8)])
        elif kind == "badmask":
            b = R.choice(MAPPED)
            k = R.randrange(4)
            args = (OP_GET, b + k, 0, 0, 1 << ((k + 1) % 4))
        elif kind == "pf_partial":
            a = R.choice([A_CML, A_CMU, A_IE])
            args = (OP_PUTF, a, M.r[a], 2, R.choice([0x7, 0xE, 0x3, 0xC, 0x1, 0x8]))
        else:
            cands = [A_ALERT, A_CML, A_CMU] + ([] if M.active else [A_CFG, A_TVL, A_TVU])
            a = R.choice(cands)
            d = R.getrandbits(8) | (0x80000000 if a == A_ALERT else 0)
            args = (OP_PUTP, a, d, 0, 0x1)
        op, a, d, sz, mk = args
        r = await env.access(op, a, d, size=sz, mask=mk)
        assert not r.discarded and r.resp["error"] == 1, f"CHK-019: {kind} request {r!r} d_error=1 expected, got {r.resp}"

    async def op_instr():
        a = R.choice(MAPPED)
        r = await env.access(OP_GET, a, instr=1)
        assert r.resp["opcode"] == 1 and r.resp["size"] == 2 and r.resp["source"] == r.source, (
            f"CHK-021: fetch response d_opcode=1, d_size=2, d_source echo expected, got {r.resp}")

    async def op_burst():
        n = R.randint(2, 4)
        wc = [A_IE, A_CML] + ([] if M.active else [A_CFG])
        plan = []
        used = set()
        for _ in range(n):
            if R.random() < 0.4:
                ch = [a for a in wc if a not in used]
                if ch:
                    a = R.choice(ch)
                    used.add(a)
                    plan.append(("w", a))
                    continue
            ch = [a for a in MAPPED if a not in used and a != A_IS]
            a = R.choice(ch)
            used.add(a)
            plan.append(("r", a))
        aff = any(kd == "w" and a in INTR_AFFECT for kd, a in plan)
        if aff:
            M.busy += 1
        items = []
        for kd, a in plan:
            if kd == "w":
                data = R.getrandbits(32)
                M.apply_write(a, data)
                items.append((kd, a, env.issue(R.choice([OP_PUTF, OP_PUTP]), a, data)))
            else:
                items.append((kd, a, env.issue(OP_GET, a)))
        for _, _, r in items:
            await env.wait_req(r, 800)
        for kd, a, r in items:
            assert not r.discarded and r.resp["error"] == 0, f"{C}: burst {r!r} d_error=0 expected, got {r.resp}"
            if kd == "r":
                check_read(a, r)
        if aff:
            M.busy -= 1
            M.settle = max(M.settle, max(r.r_edge for _, _, r in items) + (M.act_P if M.active else 0) + 12)

    async def do_reset():
        ka, krel = await env.reset(R.randint(2, 8))
        n = len(env.alerts_in(st["since"], ka))
        assert n == st["alert_qual"], f"CHK-003: o_alert pulses == qualifying writes ({st['alert_qual']}) expected, got {n}"
        M.reset()
        M.settle = krel
        st.update(alert_qual=0, since=krel, last_alert_r=-1000)

    names = ["read", "read_sub", "write_rw", "ie", "is", "it", "alert", "err", "instr", "burst",
             "ctrl", "dready"]
    weights = [20, 6, 14, 5, 5, 4, 2, 10, 3, 6, 3, 2]
    for i in range(N):
        if i in reset_points:
            await do_reset()
            active_ops = 0
            continue
        if i == regwen_clear_at:
            await op_alert(R.choice([0x00000000, 0x7FFFFFFE]))
            continue
        if M.active:
            active_ops += 1
            if active_ops > 60:
                await deactivate()
                active_ops = 0
                continue
        op = R.choices(names, weights)[0]
        if op == "read":
            await op_read()
        elif op == "read_sub":
            await op_read_sub()
        elif op == "write_rw":
            await op_write_rw()
        elif op == "ie":
            await op_small(A_IE, [0, 1, M32, R.getrandbits(32)])
        elif op == "is":
            await op_small(A_IS, [1, 0, M32, 0xFFFFFFFE, R.getrandbits(32)])
        elif op == "it":
            await op_small(A_IT, [1, 0, M32, R.getrandbits(32)])
        elif op == "alert":
            await op_alert()
        elif op == "err":
            await op_err()
        elif op == "instr":
            await op_instr()
        elif op == "burst":
            await op_burst()
        elif op == "ctrl":
            if M.active:
                await deactivate()
            else:
                await activate()
            active_ops = 0
        elif op == "dready":
            env.d_ready_mode = R.choice([1, 0.5, 0.75, 0.3])
        if R.random() < 0.25:
            await env.edges(R.randint(1, 8))
    if M.active:
        await deactivate()
    await env.edges(40)
    n = len(env.alerts_in(st["since"], env.cyc))
    assert n == st["alert_qual"], f"CHK-003: o_alert pulses == qualifying writes ({st['alert_qual']}) expected, got {n}"

    # final command-integrity fault, then reset
    env.d_ready_mode = 1
    r = env.issue(OP_GET, A_IS, flip=1)
    for _ in range(100):
        if r.a_edge is not None:
            break
        await env.edge()
    assert r.a_edge is not None, "CHK-016: corrupted request accepted within 100 cycles expected, got not accepted"
    a = r.a_edge
    for _ in range(32):
        if r.done:
            break
        await env.edge()
    await env.edges(150)
    ka, krel = await env.reset(5)
    p = env.alerts_in(a, ka - 1)
    assert p and p[0] <= a + 16, f"CHK-016: first fatal alert pulse within a+16 expected, got {p[:3]}"
    gaps = [(p[j], p[j + 1]) for j in range(len(p) - 1) if p[j + 1] - p[j] > 32]
    assert not gaps and p[-1] >= ka - 32, f"CHK-016: repeated pulses (gap <= 32) until reset expected, got gaps {gaps[:3]}, last {p[-1]}"
    M.reset()
    M.settle = krel
    v = await env.rd(A_CFG, C)
    assert v == 0x00010000, f"CHK-016: CFG0 0x00010000 after reset expected, got {hx(v)}"
    await env.edges(50)
    p = env.alerts_in(krel, env.cyc)
    assert not p, f"CHK-016: no o_alert after reset expected, got {p}"
    env.finish()

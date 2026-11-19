"""cocotb 2.1 testbench for m_uart_lite (8N1 UART lite, transmit and receive streams).

Sampling convention: at every falling edge of i_clk the monitor takes one sample (in ReadOnly).
Sample n holds the inputs that rising edge n samples and the outputs that are stable before
rising edge n ("the value at edge n" of the plan). Outputs at sample n+1 are the result of edge n.
Inputs driven right after falling edge n are therefore sampled by edge n (index env.n at that time).
"""
import inspect

import cocotb
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer

try:
    from cocotb.simtime import get_sim_time
except ImportError:  # older layout
    from cocotb.utils import get_sim_time

from nnc_cocotb import *  # noqa: F401,F403

OUTS = ("o_txd", "o_tx_ready", "o_rx_valid", "o_rx_data", "o_rx_frame_err", "o_rx_overrun")
RESET_OUT = {"o_txd": 1, "o_tx_ready": 1, "o_rx_valid": 0, "o_rx_data": 0,
             "o_rx_frame_err": 0, "o_rx_overrun": 0}
LOOP_MAX = 10 ** 8


def param_n():
    """Bit period N of this run, taken only from the run's parameter values (never a default)."""
    n = PARAMS.get("PARA_UART_CLKS_PER_BIT") if hasattr(PARAMS, "get") else None
    assert n is not None, "PARAMS does not provide PARA_UART_CLKS_PER_BIT for this run"
    return int(n)


def drv(sig, v):
    sig.value = v


def hx(x):
    return "None" if x is None else f"{x:#04x}"


def fbits(b, stop=1):
    """Frame bits: start 0, data LSB first, stop."""
    return [0] + [(b >> i) & 1 for i in range(8)] + [stop]


def frame_runs(b, n, stop=1):
    return [(v, n) for v in fbits(b, stop)]


def to_runs(levels):
    runs = []
    for v in levels:
        if runs and runs[-1][0] == v:
            runs[-1][1] += 1
        else:
            runs.append([v, 1])
    return [tuple(x) for x in runs]


def pattern_a(D, N, H):
    """Line levels for edges T0..M+1: correct value only at the sample points, complement elsewhere."""
    pts = {0: 0, H: 0}
    for i in range(8):
        pts[H + (i + 1) * N] = (D >> i) & 1
    M = H + 9 * N
    pts[M] = 1
    keys = sorted(pts)
    lv = []
    for e in range(M + 2):
        if e in pts:
            lv.append(pts[e])
        else:
            p = min(keys, key=lambda k: (abs(k - e), k))
            lv.append(1 - pts[p])
    return lv


def pattern_b(D, N, H):
    """Line levels for edges T0..T0+10N-1: correct frame, inverted exactly at S_i and M."""
    bits = fbits(D)
    samp = {H + (i + 1) * N for i in range(9)}
    lv = []
    for e in range(10 * N):
        v = 0 if e <= H else bits[e // N]
        if e in samp:
            v ^= 1
        lv.append(v)
    return lv


def _change(sig):
    vc = getattr(sig, "value_change", None)
    if vc is not None:
        return vc
    from cocotb.triggers import Edge
    return Edge(sig)


class S:
    __slots__ = ("rst", "tv", "td", "rr", "rxd", "rdy", "txd", "rv", "rd", "fe", "ov")


class Env:
    """Drivers, monitor and cycle-exact TX/RX reference model (spec sections 7-8, 10)."""

    def __init__(self, dut):
        self.dut = dut
        self.clk = dut.i_clk
        self.N = param_n()
        self.H = self.N // 2
        self.F = 10 * self.N
        self.LAT = self.H + 9 * self.N + 2
        self.big = self.N > 32
        self.smp = []
        self.n = 0
        self.errors = []
        self.nerr = 0
        self.armed = False
        self.stop_bg = False
        self.accepts, self.loads, self.drops = [], [], []
        self.starts, self.glitches, self.frames, self.resets = [], [], [], []
        self.rst_falls = set()
        self.c1_armed = False
        self.P = 1
        self.t_rise = 0
        self._mreset()

    # ---------------------------------------------------------------- setup
    def cnt(self, full, lo=2):
        return full if not self.big else max(lo, full * 32 // self.N)

    def long(self, k):
        return k * self.N if not self.big else min(k, 12) * self.N

    def idle(self):
        d = self.dut
        d.i_tx_valid.value = 0
        d.i_tx_data.value = 0
        d.i_rx_ready.value = 0
        d.i_rxd.value = 1

    async def start(self):
        d = self.dut
        # NNC hand fix (G3, triage B): ENV-002 requires i_rst_n = 0 from the start of simulation. The generated
        # harness kept i_rst_n = 1 for the first clock edges (un-reset DUT, CHK-002/CHK-010 failures at 0-40 ns).
        # Now i_rst_n falls (an asynchronous reset edge) before the clock starts; reset(5) below is unchanged.
        d.i_rst_n.value = 1
        self.idle()
        await Timer(1, "step")
        d.i_rst_n.value = 0
        await Timer(1, "step")
        res = start_clock(d)
        if inspect.isawaitable(res):
            await res
        await RisingEdge(self.clk)
        t1 = get_sim_time("step")
        await RisingEdge(self.clk)
        t2 = get_sim_time("step")
        self.P = t2 - t1
        self.t_rise = t2
        cocotb.start_soon(self._monitor())
        for name in OUTS:
            cocotb.start_soon(self._chk001(name))
        await FallingEdge(self.clk)
        await self.reset(5)
        await self.fe(2)
        return self

    def err(self, msg):
        self.nerr += 1
        if len(self.errors) < 20:
            self.errors.append(msg)
            self.dut._log.error(msg)

    def finish(self):
        assert self.nerr == 0, f"{self.errors[0] if self.errors else 'CHK-001'} ({self.nerr} monitor errors in total)"

    # ---------------------------------------------------------------- timing helpers
    async def fe(self, k=1):
        for _ in range(k):
            await FallingEdge(self.clk)

    async def until(self, idx):
        for _ in range(max(0, idx - self.n)):
            await FallingEdge(self.clk)

    async def reset(self, cycles=3, on_assert=None, per_cycle=None, on_release=None):
        """Assert i_rst_n 30% of a period after a rising edge, hold `cycles` edges, release at a falling edge.
        Returns R1 (first edge with i_rst_n=1)."""
        d = self.dut
        await RisingEdge(self.clk)
        await Timer(max(1, (self.P * 3) // 10), "step")
        self.rst_falls.add(get_sim_time("step"))
        self.c1_armed = True
        d.i_rst_n.value = 0
        if on_assert:
            on_assert()
        await Timer(1, "step")
        got = {nm: val(getattr(d, nm)) for nm in OUTS}
        assert got == RESET_OUT, f"CHK-002: one time step after i_rst_n fell expected {RESET_OUT} got {got}"
        for i in range(cycles):
            await FallingEdge(self.clk)
            if per_cycle:
                per_cycle(i)
        await FallingEdge(self.clk)
        if on_release:
            on_release()
        d.i_rst_n.value = 1
        return self.n

    # ---------------------------------------------------------------- CHK-001 checker
    async def _chk001(self, name):
        sig = getattr(self.dut, name)
        for _ in range(LOOP_MAX):
            await _change(sig)
            if not self.c1_armed:
                continue
            t = get_sim_time("step")
            if (t - self.t_rise) % self.P != 0 and t not in self.rst_falls:
                self.err(f"CHK-001: {name} changed at time step {t}, which is neither a rising edge of i_clk "
                         f"nor an i_rst_n assertion")

    # ---------------------------------------------------------------- monitor + model
    def _mreset(self):
        self.tx_E0 = None
        self.tx_D = 0
        self.tx_seen = False
        self.p_rdy, self.p_txd = 1, 1
        self.p_rv, self.p_rd, self.p_fe, self.p_ov = 0, 0, 0, 0
        self.lab_rdy = self.lab_txd = "CHK-010"
        self.lab_rx, self.lab_ov = "CHK-009", "CHK-006"
        self.rx_T0 = None
        self.rx_bits = 0
        self.prev_s = 1
        self.pending = None

    async def _monitor(self):
        d = self.dut
        for _ in range(LOOP_MAX):
            await FallingEdge(self.clk)
            await ReadOnly()
            s = S()
            s.rst = val(d.i_rst_n)
            s.tv = val(d.i_tx_valid) or 0
            s.td = val(d.i_tx_data) or 0
            s.rr = val(d.i_rx_ready) or 0
            x = val(d.i_rxd)
            s.rxd = 1 if x is None else x
            s.rdy = val(d.o_tx_ready)
            s.txd = val(d.o_txd)
            s.rv = val(d.o_rx_valid)
            s.rd = val(d.o_rx_data)
            s.fe = val(d.o_rx_frame_err)
            s.ov = val(d.o_rx_overrun)
            n = self.n
            self.smp.append(s)
            if s.rst == 0:
                self.armed = True
                got = (s.txd, s.rdy, s.rv, s.rd, s.fe, s.ov)
                if got != (1, 1, 0, 0, 0, 0):
                    self.err(f"CHK-002: at edge {n} with i_rst_n=0 expected txd/ready/valid/data/err/overrun="
                             f"(1,1,0,0,0,0) got {got}")
                self._mreset()
                self.resets.append(n)
            elif s.rst == 1 and self.armed:
                self._compare(s, n)
                self._step(s, n)
            self.n = n + 1

    def _compare(self, s, n):
        if s.rdy != self.p_rdy:
            self.err(f"{self.lab_rdy}: o_tx_ready at sample {n} expected {self.p_rdy} got {s.rdy}")
        if s.txd != self.p_txd:
            self.err(f"{self.lab_txd}: o_txd at sample {n} expected {self.p_txd} got {s.txd}")
        if (s.rv, s.rd, s.fe) != (self.p_rv, self.p_rd, self.p_fe):
            self.err(f"{self.lab_rx}: o_rx_valid/o_rx_data/o_rx_frame_err at sample {n} expected "
                     f"{self.p_rv}/{hx(self.p_rd)}/{self.p_fe} got {s.rv}/{hx(s.rd)}/{s.fe}")
        if s.ov != self.p_ov:
            self.err(f"{self.lab_ov}: o_rx_overrun at sample {n} expected {self.p_ov} got {s.ov}")

    def _step(self, s, n):
        N = self.N
        # ---- TX (REQ-TX, CHK-010..013)
        if s.tv == 1 and self.p_rdy == 1:
            self.tx_E0, self.tx_D = n, s.td
            self.accepts.append((n, s.td))
        m = n + 1
        if self.tx_E0 is not None and m <= self.tx_E0 + self.F:
            k = m - self.tx_E0 - 1
            j = k // N
            self.p_txd = 0 if j == 0 else (1 if j == 9 else (self.tx_D >> (j - 1)) & 1)
            self.p_rdy = 1 if m == self.tx_E0 + self.F else 0
            self.lab_txd = "CHK-010" if k == 0 else ("CHK-013" if m == self.tx_E0 + self.F else "CHK-011")
            self.lab_rdy = "CHK-010" if k == 0 else "CHK-012"
        else:
            if self.tx_E0 is not None:
                self.tx_seen = True
            self.tx_E0 = None
            self.p_txd, self.p_rdy = 1, 1
            self.lab_txd = self.lab_rdy = "CHK-013" if self.tx_seen else "CHK-010"
        # ---- RX holding register (CHK-003..009)
        ov = 0
        if self.pending is not None and self.pending[0] == n:
            _, b, fe = self.pending
            self.pending = None
            if self.p_rv == 0 or s.rr == 1:
                self.lab_rx = "CHK-003" if self.p_rv == 0 else "CHK-004"
                self.p_rv, self.p_rd, self.p_fe = 1, b, fe
                self.loads.append((n, b, fe))
                self.lab_ov = self.lab_rx
            else:
                ov = 1
                self.drops.append((n, b, fe))
                self.lab_rx = self.lab_ov = "CHK-005"
        else:
            if self.p_rv == 1 and s.rr == 1:
                self.p_rv = 0
                self.lab_rx = "CHK-007"
            elif self.p_rv == 1:
                self.lab_rx = "CHK-008"
            else:
                self.lab_rx = "CHK-009"
            self.lab_ov = "CHK-006"
        self.p_ov = ov
        # ---- RX frame FSM (sections 7.4, 7.5)
        sv = s.rxd
        if self.rx_T0 is None:
            if self.prev_s == 1 and sv == 0:
                self.rx_T0, self.rx_bits = n, 0
                self.starts.append(n)
        else:
            rel = n - self.rx_T0
            if rel == self.H:
                if sv == 1:
                    self.glitches.append(self.rx_T0)
                    self.rx_T0 = None
            elif rel > self.H and (rel - self.H) % N == 0:
                i = (rel - self.H) // N - 1
                if i < 8:
                    self.rx_bits |= sv << i
                else:
                    self.frames.append((self.rx_T0, self.rx_bits, 1 - sv))
                    self.pending = (n + 2, self.rx_bits, 1 - sv)
                    self.rx_T0 = None
        self.prev_s = sv

    # ---------------------------------------------------------------- drivers
    async def rx_runs(self, runs, ready_fn=None):
        """Drive (level, count) runs on i_rxd at falling edges; returns index of the first sample."""
        start = self.n
        d = self.dut
        for v, c in runs:
            d.i_rxd.value = v
            for _ in range(c):
                if self.stop_bg:
                    return start
                if ready_fn is not None:
                    d.i_rx_ready.value = ready_fn(self.n)
                await FallingEdge(self.clk)
        return start

    async def rx_random(self, r, count, gap_max, p_err=0.0, p_gl=0.0, align=None, ready_fn=None):
        sent = []
        prev_err = False
        N = self.N
        for i in range(count):
            if self.stop_bg:
                break
            g = r.randint(0, gap_max)
            if align is not None:
                a = align(i)
                if a is not None:
                    g = a
            if prev_err:
                g = max(g, 1)
            if g:
                await self.rx_runs([(1, g)], ready_fn)
            if r.random() < p_gl:
                L = r.randint(1, self.H)
                await self.rx_runs([(0, L), (1, max(1, self.H + 1 - L))], ready_fn)
            err = r.random() < p_err
            b = r.getrandbits(8)
            T0 = await self.rx_runs(frame_runs(b, N, 0 if err else 1), ready_fn)
            sent.append((T0, b, int(err)))
            prev_err = err
        await self.rx_runs([(1, 2 * N + 4)], ready_fn)
        return sent

    async def tx_b2b(self, data, chk):
        d = self.dut
        base = len(self.accepts)
        i = 0
        d.i_tx_data.value = data[0]
        d.i_tx_valid.value = 1
        for _ in range((len(data) + 2) * self.F + 10):
            await FallingEdge(self.clk)
            if len(self.accepts) - base > i:
                i += 1
                if i == len(data):
                    break
                d.i_tx_data.value = data[i]
        d.i_tx_valid.value = 0
        acc = self.accepts[base:]
        assert len(acc) == len(data), f"{chk}: expected {len(data)} handshakes with i_tx_valid held at 1, got {len(acc)}"
        return acc

    async def tx_one(self, b, chk):
        d = self.dut
        for _ in range(self.F + 4):
            if val(d.o_tx_ready) == 1:
                break
            await FallingEdge(self.clk)
        E0 = self.n
        d.i_tx_data.value = b
        d.i_tx_valid.value = 1
        await FallingEdge(self.clk)
        d.i_tx_valid.value = 0
        assert self.accepts and self.accepts[-1] == (E0, b), \
            f"{chk}: expected handshake of {hx(b)} at edge {E0}, got {self.accepts[-1:]}"
        return E0

    async def tx_random(self, r, count, gap_max, chaos=True):
        d = self.dut
        exp = []

        def gap():
            c = r.random()
            return 0 if c < 0.25 else (1 if c < 0.4 else r.randint(0, gap_max))

        wait = gap()
        for _ in range(count * (self.F + gap_max + 4) + 10):
            if self.stop_bg:
                break
            if chaos:
                d.i_tx_data.value = r.getrandbits(8)
            v = 0
            if len(exp) < count and val(d.o_tx_ready) == 1:
                if wait == 0:
                    b = r.getrandbits(8)
                    d.i_tx_data.value = b
                    v = 1
                    exp.append((self.n, b))
                    wait = gap()
                else:
                    wait -= 1
            d.i_tx_valid.value = v
            if len(exp) >= count and v == 0:
                break
            await FallingEdge(self.clk)
        d.i_tx_valid.value = 0
        return exp

    async def loop_task(self):
        d = self.dut
        for _ in range(LOOP_MAX):
            if self.stop_bg:
                return
            v = val(d.o_txd)
            d.i_rxd.value = 1 if v is None else v
            await FallingEdge(self.clk)

    # ---------------------------------------------------------------- checkers on the trace
    def chk_tx_frame(self, E0, D, chk):
        bits = fbits(D)
        assert E0 + self.F < len(self.smp), f"{chk}: simulation did not reach the end of the frame at E0={E0}"
        for k in range(self.F):
            s = self.smp[E0 + k + 1]
            e = bits[k // self.N]
            assert s.txd == e, f"{chk}: o_txd at E0+{k + 1} (E0={E0}, byte {hx(D)}) expected {e} got {s.txd}"
            er = 1 if k == self.F - 1 else 0
            assert s.rdy == er, f"{chk}: o_tx_ready at E0+{k + 1} (E0={E0}) expected {er} got {s.rdy}"

    def tx_decode(self, a, b):
        out = []
        m = max(a, 1)
        N = self.N
        while m < b:
            if self.smp[m].txd == 0 and self.smp[m - 1].txd == 1:
                if m + self.F > b:
                    break
                byte = sum(self.smp[m + j * N + self.H].txd << (j - 1) for j in range(1, 9))
                out.append((m, byte, self.smp[m + 9 * N + self.H].txd))
                m += self.F
            else:
                m += 1
        return out

    def chk_load(self, T0, byte, fe, chk, lat=None):
        V = T0 + (self.LAT if lat is None else lat)
        assert V + 1 < len(self.smp), f"{chk}: simulation did not reach V+1={V + 1}"
        assert (V, byte, fe) in self.loads, \
            f"{chk}: expected byte {hx(byte)} err={fe} loaded at V={V} (T0={T0}), model loads {self.loads[-3:]}"
        s = self.smp[V + 1]
        assert (s.rv, s.rd, s.fe, s.ov) == (1, byte, fe, 0), \
            f"{chk}: at V+1={V + 1} expected valid=1 data={hx(byte)} err={fe} overrun=0, " \
            f"got valid={s.rv} data={hx(s.rd)} err={s.fe} overrun={s.ov}"
        return V

    def chk_drop(self, T0, held, held_fe, chk):
        V = T0 + self.LAT
        assert V + 2 < len(self.smp), f"{chk}: simulation did not reach V+2={V + 2}"
        assert any(x[0] == V for x in self.drops), f"{chk}: expected an overrun drop at V={V} (T0={T0})"
        s1, s2 = self.smp[V + 1], self.smp[V + 2]
        assert (s1.ov, s1.rv, s1.rd, s1.fe) == (1, 1, held, held_fe), \
            f"{chk}: at V+1={V + 1} expected overrun=1 valid=1 data={hx(held)} err={held_fe}, " \
            f"got overrun={s1.ov} valid={s1.rv} data={hx(s1.rd)} err={s1.fe}"
        assert s2.ov == 0, f"{chk}: o_rx_overrun must be a one-cycle pulse, got 1 at V+2={V + 2}"
        return V

    def chk_rx_stream(self, sent, fb, lb, db, k0, chk):
        fr, ld, dr = self.frames[fb:], self.loads[lb:], self.drops[db:]
        assert fr == sent, f"{chk}: frames confirmed by the model {fr[:4]} differ from the frames sent {sent[:4]}"
        assert len(ld) + len(dr) == len(fr), \
            f"{chk}: deliveries ({len(ld)}) + overrun drops ({len(dr)}) != confirmed frames ({len(fr)})"
        ev = sorted(ld + dr)
        want = [(t + self.LAT, b, e) for t, b, e in fr]
        assert ev == want, f"{chk}: deliveries/drops not at V=T0+{self.LAT} in completion order"
        for v, b, e in ld:
            s = self.smp[v + 1]
            assert (s.rv, s.rd, s.fe, s.ov) == (1, b, e, 0), \
                f"{chk}: delivery at V={v} expected valid=1 data={hx(b)} err={e} at V+1, got {s.rv}/{hx(s.rd)}/{s.fe}/{s.ov}"
        pulses = [k for k in range(k0, self.n) if self.smp[k].ov == 1]
        exp_p = [v + 1 for v, _, _ in dr]
        assert pulses == exp_p, f"{chk}: o_rx_overrun pulses at {pulses[:6]} expected at {exp_p[:6]}"
        return ld, dr


# ====================================================================== reusable scenarios
async def scen_030(env, r, n_rand, chk="CHK-030"):
    env.idle()
    await env.reset()
    await env.fe(2)
    F = env.F
    data = [0x00, 0xFF, 0x55, 0xAA] + [r.getrandbits(8) for _ in range(n_rand)]
    acc = await env.tx_b2b(data, chk)
    await env.fe(F + 4)
    E = [e for e, _ in acc]
    assert [b for _, b in acc] == data, f"{chk}: accepted bytes {[hx(b) for _, b in acc]} expected {[hx(b) for b in data]}"
    for i in range(1, len(E)):
        assert E[i] - E[i - 1] == F, f"{chk}: acceptance {i} expected {F} edges after the previous one, got {E[i] - E[i - 1]}"
    for e, b in acc:
        env.chk_tx_frame(e, b, chk)
    for i in range(len(E) - 1):
        a, b2 = env.smp[E[i] + F], env.smp[E[i] + F + 1]
        assert a.txd == 1 and b2.txd == 0, \
            f"{chk}: back-to-back frames expected stop 1 at {E[i] + F} and start 0 at {E[i] + F + 1}, got {a.txd},{b2.txd}"
    dec = env.tx_decode(E[0] + 1, E[-1] + F + 1)
    assert [x[1] for x in dec] == data and all(x[2] == 1 for x in dec) and [x[0] for x in dec] == [e + 1 for e in E], \
        f"{chk}: decoded o_txd stream {[(x[0], hx(x[1]), x[2]) for x in dec[:4]]} does not match the accepted bytes"
    assert E[-1] + F - E[0] == len(data) * F, f"{chk}: stream length expected {len(data) * F} got {E[-1] + F - E[0]}"


async def scen_023(env, r, n_rand, chk="CHK-023"):
    env.idle()
    await env.reset()
    N, H = env.N, env.H
    M = H + 9 * N
    env.dut.i_rx_ready.value = 1
    data = [0x55, 0xAA, 0x0F, 0xF0, 0x00, 0xFF] + [r.getrandbits(8) for _ in range(n_rand)]
    await env.rx_runs([(1, 2 * N)])
    lb, db, k0 = len(env.loads), len(env.drops), env.n
    exp = []
    for pat in "AB":
        for D in data:
            lv = pattern_a(D, N, H) if pat == "A" else pattern_b(D, N, H)
            T0 = await env.rx_runs(to_runs(lv))
            await env.rx_runs([(1, 2 * N + H + 4)])
            want = (D, 0) if pat == "A" else ((~D) & 0xFF, 1)
            V = env.chk_load(T0, want[0], want[1], f"{chk}: pattern {pat}")
            exp.append((V, want[0], want[1]))
            if pat == "A":
                assert (T0 + M + 1) in env.glitches, \
                    f"{chk}: pattern A, the 0 at M+1={T0 + M + 1} should be detected as a start and rejected as a glitch"
    assert env.loads[lb:] == exp, f"{chk}: expected exactly one delivery per frame, got {len(env.loads) - lb} for {len(exp)}"
    assert len(env.drops) == db and all(s.ov == 0 for s in env.smp[k0:env.n]), f"{chk}: unexpected overrun"


async def scen_024(env, chk="CHK-024"):
    d = env.dut
    N, H, F = env.N, env.H, env.F
    for mode in ("i", "ii"):
        env.idle()
        await env.reset()
        tag = f"{chk} run ({mode})"
        await env.rx_runs([(1, 2 * N)])
        if mode == "i":
            d.i_rx_ready.value = 1
        else:
            T = await env.rx_runs(frame_runs(0x5A, N) + [(1, 2 * N)])
            env.chk_load(T, 0x5A, 0, tag)
        for L in range(1, H + 1):
            nl, nd = len(env.loads), len(env.drops)
            a = env.n
            await env.rx_runs([(1, N)])
            T0 = await env.rx_runs([(0, L), (1, 2 * N)])
            ref = env.smp[a]
            for k in range(a, env.n):
                s = env.smp[k]
                assert (s.rv, s.rd, s.fe, s.ov) == (ref.rv, ref.rd, ref.fe, 0), \
                    f"{tag}(a): {L}-sample low pulse changed receive outputs at sample {k}: " \
                    f"{s.rv}/{hx(s.rd)}/{s.fe}/{s.ov}"
            assert len(env.loads) == nl and len(env.drops) == nd, f"{tag}(a): {L}-sample glitch produced a byte or drop"
            assert T0 in env.glitches, f"{tag}(a): {L}-sample pulse at T0={T0} must be rejected as a glitch at T0+H"
        await env.rx_runs([(1, N)])
        T0 = await env.rx_runs([(0, H + 1), (1, F + 2 * N)])
        if mode == "i":
            env.chk_load(T0, 0xFF, 0, tag + "(b)")
        else:
            env.chk_drop(T0, 0x5A, 0, tag + "(b)")
        await env.rx_runs([(1, N)])
        T0 = await env.rx_runs([(0, H), (1, 1)])
        T0p = await env.rx_runs(frame_runs(0x33, N) + [(1, 2 * N)])
        assert T0 in env.glitches and T0p in env.starts and T0p == T0 + H + 1, \
            f"{tag}(c): expected glitch at T0={T0} and new start at T0+H+1={T0 + H + 1}"
        if mode == "i":
            env.chk_load(T0p, 0x33, 0, tag + "(c)")
        else:
            env.chk_drop(T0p, 0x5A, 0, tag + "(c)")


async def scen_025a(env, r, n_rand, chk="CHK-025"):
    env.idle()
    await env.reset()
    env.dut.i_rx_ready.value = 1
    N = env.N
    data = [0x00, 0xFF, 0x55, 0xAA] + [r.getrandbits(8) for _ in range(n_rand)]
    await env.rx_runs([(1, 2 * N)])
    db = len(env.drops)
    runs = []
    for b in data:
        runs += frame_runs(b, N)
    T1 = await env.rx_runs(runs)
    await env.rx_runs([(1, 2 * N + 4)])
    for k, b in enumerate(data):
        T = T1 + k * env.F
        assert T in env.starts, f"{chk}(a): frame {k} start expected at T0_1+{k * env.F}={T}"
        env.chk_load(T, b, 0, f"{chk}(a)")
    assert len(env.drops) == db, f"{chk}(a): unexpected overrun with i_rx_ready=1"


async def scen_026(env, r, parts="abcde", chk="CHK-026"):
    d = env.dut
    N, F, L = env.N, env.F, env.LAT
    if "a" in parts:
        env.idle()
        await env.reset()
        await env.rx_runs([(1, 2 * N)])
        B = [r.getrandbits(8) for _ in range(4)]
        runs = []
        for b in B:
            runs += frame_runs(b, N)
        T1 = await env.rx_runs(runs)
        await env.rx_runs([(1, 2 * N)])
        env.chk_load(T1, B[0], 0, chk + "(a)")
        for k in range(1, 4):
            env.chk_drop(T1 + k * F, B[0], 0, chk + "(a)")
        t = env.n
        d.i_rx_ready.value = 1
        await env.fe()
        d.i_rx_ready.value = 0
        await env.fe(3)
        s = env.smp[t + 1]
        assert s.rv == 0 and s.rd == B[0] and s.ov == 0, \
            f"{chk}(a): after the take expected valid=0 data={hx(B[0])} got valid={s.rv} data={hx(s.rd)}"
    for sub, off in (("b", 0), ("c", -1)):
        if sub not in parts:
            continue
        env.idle()
        await env.reset()
        await env.rx_runs([(1, 2 * N)])
        B1 = r.getrandbits(8)
        B2 = B1 ^ (1 + r.getrandbits(7))
        T1 = await env.rx_runs(frame_runs(B1, N) + [(1, 2 * N)])
        env.chk_load(T1, B1, 0, f"{chk}({sub})")
        db = len(env.drops)
        T2 = env.n
        V2 = T2 + L
        tk = V2 + off
        await env.rx_runs(frame_runs(B2, N) + [(1, 2 * N)], ready_fn=lambda n, tk=tk: int(n == tk))
        s0, s1 = env.smp[V2], env.smp[V2 + 1]
        if sub == "b":
            assert s0.rv == 1 and s0.rr == 1, f"{chk}(b): precondition valid=1 and ready=1 at V2={V2}"
        else:
            assert s0.rv == 0, f"{chk}(c): expected o_rx_valid=0 at V2={V2} after the take at V2-1, got {s0.rv}"
        assert (s1.rv, s1.rd, s1.ov) == (1, B2, 0), \
            f"{chk}({sub}): at V2+1 expected valid=1 data={hx(B2)} overrun=0 got {s1.rv}/{hx(s1.rd)}/{s1.ov}"
        assert (V2, B2, 0) in env.loads and len(env.drops) == db, f"{chk}({sub}): B2 must be loaded at V2 with no overrun"
    if "d" in parts:
        env.idle()
        await env.reset()
        d.i_rx_ready.value = 1
        fb, lb, db, k0 = len(env.frames), len(env.loads), len(env.drops), env.n
        sent = await env.rx_random(r, env.cnt(10), N)
        ld, dr = env.chk_rx_stream(sent, fb, lb, db, k0, chk + "(d)")
        assert not dr and len(ld) == len(sent), f"{chk}(d): expected every byte delivered and no overrun"
    if "e" in parts:
        env.idle()
        await env.reset()
        rr = rng("026e")
        fb, lb, db, k0 = len(env.frames), len(env.loads), len(env.drops), env.n
        sent = await env.rx_random(r, env.cnt(60), 3 * N, ready_fn=lambda n: rr.getrandbits(1))
        env.chk_rx_stream(sent, fb, lb, db, k0, chk + "(e)")


# ====================================================================== tests
@cocotb.test()
async def test_chk_014_cfg_min(dut):
    """CHK-014: CFG-MIN (N=4, H=2): CHK-030, CHK-023, CHK-024 (L=1..3), CHK-025(a), CHK-026(a,b)."""
    if param_n() != 4:  # nnc-literal-ok (CFG-MIN value of the check itself)
        not_verifiable(dut, "CHK-014", f"needs PARA_UART_CLKS_PER_BIT=4, this run has {param_n()}")
        return
    env = await Env(dut).start()
    assert env.F == 40 and env.H == 2 and env.LAT == 40, f"CHK-014: derived F/H/LAT {env.F}/{env.H}/{env.LAT}"  # nnc-literal-ok
    r = rng(14)
    await scen_030(env, r, 20, "CHK-014")
    await scen_023(env, r, 10, "CHK-014")
    await scen_024(env, "CHK-014")
    await scen_025a(env, r, 6, "CHK-014")
    await scen_026(env, r, "ab", "CHK-014")
    env.finish()


@cocotb.test()
async def test_chk_015_cfg_odd(dut):
    """CHK-015: CFG-ODD (N=5, H=floor(5/2)=2): CHK-030, CHK-023, CHK-024 (L=1..3), CHK-025(a)."""
    if param_n() != 5:  # nnc-literal-ok (CFG-ODD value of the check itself)
        not_verifiable(dut, "CHK-015", f"needs PARA_UART_CLKS_PER_BIT=5, this run has {param_n()}")
        return
    env = await Env(dut).start()
    assert env.F == 50 and env.H == 2 and env.LAT == 49, f"CHK-015: derived F/H/LAT {env.F}/{env.H}/{env.LAT}"  # nnc-literal-ok
    r = rng(15)
    await scen_030(env, r, 20, "CHK-015")
    await scen_023(env, r, 10, "CHK-015")
    await scen_024(env, "CHK-015")
    await scen_025a(env, r, 6, "CHK-015")
    env.finish()


@cocotb.test()
async def test_chk_016_cfg_wide(dut):
    """CHK-016: CFG-WIDE (N=1024): transmit, pattern-A receive, glitch H / pulse H+1, loopback."""
    if param_n() != 1024:  # nnc-literal-ok (CFG-WIDE value of the check itself)
        not_verifiable(dut, "CHK-016", f"needs PARA_UART_CLKS_PER_BIT=1024, this run has {param_n()}")
        return
    env = await Env(dut).start()
    N, H, F, L = env.N, env.H, env.F, env.LAT
    assert F == 10240 and H == 512 and L == 9730, f"CHK-016: derived F/H/LAT {F}/{H}/{L}"  # nnc-literal-ok
    env.idle()
    await env.fe(2)
    acc = await env.tx_b2b([0xA5, 0x5A], "CHK-016")
    await env.fe(F + 4)
    (E0, _), (E1, _) = acc
    assert E1 == E0 + F, f"CHK-016: second acceptance expected at E0+{F} got E0+{E1 - E0}"
    env.chk_tx_frame(E0, 0xA5, "CHK-016")
    env.chk_tx_frame(E1, 0x5A, "CHK-016")
    assert env.smp[E0 + F + 1].txd == 0, "CHK-016: second start bit expected at E0+10N+1"
    dut.i_rx_ready.value = 1
    await env.rx_runs([(1, 2 * N)])
    T0 = await env.rx_runs(to_runs(pattern_a(0x96, N, H)))
    await env.rx_runs([(1, 2 * N + H + 4)])
    V = env.chk_load(T0, 0x96, 0, "CHK-016")
    assert V == T0 + H + 9 * N + 2, f"CHK-016: V expected T0+{H + 9 * N + 2} got T0+{V - T0}"
    nl, nd, a = len(env.loads), len(env.drops), env.n
    await env.rx_runs([(0, H), (1, 2 * N)])
    ref = env.smp[a]
    assert len(env.loads) == nl and len(env.drops) == nd and all(
        (s.rv, s.rd, s.fe, s.ov) == (ref.rv, ref.rd, ref.fe, 0) for s in env.smp[a:env.n]), \
        "CHK-016: the H-sample glitch must produce nothing"
    T0 = await env.rx_runs([(0, H + 1), (1, F + 2 * N)])
    env.chk_load(T0, 0xFF, 0, "CHK-016")
    env.stop_bg = False
    cocotb.start_soon(env.loop_task())
    await env.fe(2)
    acc = await env.tx_b2b([0xC5], "CHK-016")
    await env.fe(F + 8)
    E0 = acc[0][0]
    V = env.chk_load(E0 + 1, 0xC5, 0, "CHK-016")
    assert V == E0 + H + 9 * N + 3, f"CHK-016: loopback delivery expected E0+{H + 9 * N + 3} got E0+{V - E0}"
    env.stop_bg = True
    await env.fe(2)
    env.stop_bg = False
    env.finish()


@cocotb.test()
async def test_chk_017_full_duplex(dut):
    """CHK-017: full duplex, transmit back to back while receive deliveries/takes/overruns run, aligned edges."""
    env = await Env(dut).start()
    env.idle()
    await env.reset()
    await env.fe(2)
    r, rr = rng(17), rng("17r")
    N, F, L = env.N, env.F, env.LAT
    n_tx = env.cnt(40, lo=3)
    data = [r.getrandbits(8) for _ in range(n_tx)]
    base = len(env.accepts)
    fb, lb, db, k0 = len(env.frames), len(env.loads), len(env.drops), env.n
    txt = cocotb.start_soon(env.tx_b2b(data, "CHK-017"))
    for _ in range(F + 4):
        await env.fe()
        if len(env.accepts) > base:
            break
    assert len(env.accepts) > base, "CHK-017: first transmit handshake did not happen"
    E0 = env.accepts[base][0]

    def ready_fn(n):
        if (n - E0) % F == 0:
            return 1
        if (n // (4 * F)) % 2:
            return int(rr.random() < 0.5)
        return 0

    def align(i):
        return (E0 - env.n - L) % F if i % 3 == 0 else None

    sent = await env.rx_random(r, n_tx, N, align=align, ready_fn=ready_fn)
    acc = await txt
    await env.fe(F + 4)
    E = [e for e, _ in acc]
    assert [b for _, b in acc] == data, "CHK-017: transmit bytes not accepted in order"
    for i in range(1, len(E)):
        assert E[i] - E[i - 1] == F, f"CHK-017: acceptances expected every {F} edges, got {E[i] - E[i - 1]}"
    for e, b in acc:
        env.chk_tx_frame(e, b, "CHK-017")
    env.chk_rx_stream(sent, fb, lb, db, k0, "CHK-017")
    Es = set(E)
    assert any(t + L in Es for t, _, _ in sent), "CHK-017: no receive delivery edge V fell on a transmit acceptance edge"
    if not env.big:
        takes = [e for e in E if env.smp[e].rv == 1 and env.smp[e].rr == 1]
        assert takes, "CHK-017: no consumer take fell on a transmit acceptance edge"
    env.finish()


@cocotb.test()
async def test_chk_018_loopback(dut):
    """CHK-018: o_txd looped to i_rxd through a half-cycle delay; V=E0+H+9N+3, bytes intact and in order."""
    env = await Env(dut).start()
    env.idle()
    await env.reset()
    dut.i_rx_ready.value = 1
    await env.fe(2)
    r = rng(18)
    N, H = env.N, env.H
    env.stop_bg = False
    cocotb.start_soon(env.loop_task())
    await env.fe(2)
    data = [0x00, 0xFF, 0x55, 0xAA] + [r.getrandbits(8) for _ in range(env.cnt(28, lo=1))]
    lb, db, k0 = len(env.loads), len(env.drops), env.n
    acc = await env.tx_b2b(data, "CHK-018")
    await env.fe(env.F + env.LAT + 4)
    exp = []
    for e, b in acc:
        assert (e + 1) in env.starts, f"CHK-018: start expected at T0=E0+1={e + 1}"
        V = env.chk_load(e + 1, b, 0, "CHK-018")
        assert V == e + H + 9 * N + 3, f"CHK-018: V expected E0+{H + 9 * N + 3} got E0+{V - e}"
        exp.append((V, b, 0))
    assert env.loads[lb:] == exp, "CHK-018: received bytes not all in order"
    assert len(env.drops) == db and all(s.ov == 0 for s in env.smp[k0:env.n]), "CHK-018: o_rx_overrun must stay 0"
    env.stop_bg = True
    await env.fe(2)
    env.stop_bg = False
    env.finish()


@cocotb.test()
async def test_chk_019_async_reset(dut):
    """CHK-019: asynchronous reset mid transmit frame, mid receive frame and while a byte is held."""
    env = await Env(dut).start()
    N, H = env.N, env.H
    # (a) mid transmit frame
    env.idle()
    await env.fe(2)
    E0 = await env.tx_one(0x00, "CHK-019(a)")
    await env.until(E0 + 4 * N + 3)
    assert val(dut.o_txd) == 0, f"CHK-019(a): precondition o_txd=0 before reset, got {val(dut.o_txd)}"
    na = len(env.accepts)
    R1 = await env.reset(3, on_release=lambda: drv(dut.i_tx_valid, 0))
    await env.fe(12 * N)
    for k in range(R1, R1 + 10 * N + 1):
        s = env.smp[k]
        assert s.txd == 1 and s.rdy == 1, f"CHK-019(a): abandoned frame visible at R1+{k - R1}: txd={s.txd} ready={s.rdy}"
    assert len(env.accepts) == na, "CHK-019(a): no byte may be accepted after release"
    # (b) mid receive frame
    env.idle()
    dut.i_rx_ready.value = 1
    await env.rx_runs([(1, 2 * N)])
    nl, nd = len(env.loads), len(env.drops)
    T0 = env.n
    dut.i_rxd.value = 0
    await env.until(T0 + H + 4 * N)
    assert T0 in env.starts, "CHK-019(b): precondition, receive frame start detected"
    R1 = await env.reset(3, on_assert=lambda: drv(dut.i_rxd, 1))
    await env.fe(12 * N)
    for k in range(R1, R1 + 10 * N + H + 4):
        s = env.smp[k]
        assert (s.rv, s.ov, s.fe) == (0, 0, 0), f"CHK-019(b): discarded frame produced output at R1+{k - R1}"
    assert len(env.loads) == nl and len(env.drops) == nd, "CHK-019(b): discarded frame was delivered"
    # (c) while a byte is held
    env.idle()
    await env.rx_runs([(1, 2 * N)])
    T = await env.rx_runs(frame_runs(0x81, N, 0) + [(1, 2 * N)])
    env.chk_load(T, 0x81, 1, "CHK-019(c)")
    s = env.smp[env.n - 1]
    assert (s.rv, s.rd, s.fe) == (1, 0x81, 1), "CHK-019(c): precondition, 8'h81 held with frame error"
    R1 = await env.reset(3)
    nd = len(env.drops)
    await env.rx_runs([(1, 2 * N)])
    T2 = await env.rx_runs(frame_runs(0x42, N) + [(1, 2 * N)])
    V = env.chk_load(T2, 0x42, 0, "CHK-019(c)")
    assert all(s.rv == 0 for s in env.smp[R1:V + 1]), "CHK-019(c): o_rx_valid must stay 0 after release until V+1"
    assert len(env.drops) == nd and all(s.ov == 0 for s in env.smp[R1:env.n]), "CHK-019(c): no overrun expected"
    env.finish()


@cocotb.test()
async def test_chk_020_reset_idle(dut):
    """CHK-020: no activity during reset; transmitter accepts at R1; receiver idle after release."""
    env = await Env(dut).start()
    N = env.N
    env.idle()
    await env.fe(2)
    k0, na, ns = env.n, len(env.accepts), len(env.starts)
    tog = [1, 0, 1, 0, 1, 1]

    def on_a():
        dut.i_tx_valid.value = 1
        dut.i_tx_data.value = 0xA5

    R1 = await env.reset(6, on_assert=on_a, per_cycle=lambda i: drv(dut.i_rxd, tog[i] if i < len(tog) else 1),
                         on_release=lambda: drv(dut.i_tx_valid, 0))
    await env.fe(12 * N)
    for k in range(k0, env.n):
        s = env.smp[k]
        assert s.rv == 0 and s.ov == 0, f"CHK-020(A): o_rx_valid/o_rx_overrun must stay 0, got {s.rv}/{s.ov} at {k}"
    for k in [x for x in env.resets if x >= k0] + list(range(R1, R1 + 10 * N + 2)):
        s = env.smp[k]
        assert s.txd == 1 and s.rdy == 1, f"CHK-020(A): o_txd/o_tx_ready expected 1/1 at sample {k}, got {s.txd}/{s.rdy}"
    assert len(env.accepts) == na and len(env.starts) == ns, "CHK-020(A): activity accepted or detected during reset"

    def on_r():
        dut.i_tx_valid.value = 1
        dut.i_tx_data.value = 0x3C
        dut.i_rx_ready.value = 1

    R1 = await env.reset(3, on_release=on_r)
    await env.fe()
    dut.i_tx_valid.value = 0
    assert env.accepts and env.accepts[-1] == (R1, 0x3C), f"CHK-020(B): handshake expected at R1={R1}, got {env.accepts[-1:]}"
    await env.until(R1 + 3)
    T0 = await env.rx_runs(frame_runs(0x96, N) + [(1, 2 * N)])
    assert T0 == R1 + 3, "CHK-020(B): frame start not at R1+3"
    await env.fe(env.F)
    s = env.smp[R1 + 1]
    assert s.rdy == 0 and s.txd == 0, f"CHK-020(B): at R1+1 expected ready=0 txd=0 got {s.rdy}/{s.txd}"
    env.chk_tx_frame(R1, 0x3C, "CHK-020(B)")
    env.chk_load(T0, 0x96, 0, "CHK-020(B)")
    env.finish()


@cocotb.test()
async def test_chk_021_low_at_release(dut):
    """CHK-021: line low at reset release is detected as a start at R1; one 8'h00 with frame error."""
    env = await Env(dut).start()
    N = env.N
    env.idle()
    await env.fe(2)
    R1 = await env.reset(3, on_assert=lambda: drv(dut.i_rxd, 0), on_release=lambda: drv(dut.i_rx_ready, 0))
    lb, db = len(env.loads), len(env.drops)
    low = env.long(40)
    for _ in range(low):
        if val(dut.o_rx_valid) == 1:
            dut.i_rx_ready.value = 1
        await env.fe()
    X = env.n
    await env.rx_runs([(1, N)])
    T2 = await env.rx_runs(frame_runs(0xA5, N) + [(1, 2 * N)])
    assert R1 in env.starts, f"CHK-021: T0 expected at R1={R1}"
    V = env.chk_load(R1, 0x00, 1, "CHK-021")
    assert all(s.rv == 0 for s in env.smp[R1:V + 1]), "CHK-021: o_rx_valid must first be 1 at R1+H+9N+3"
    assert all(s.rv == 0 and s.ov == 0 for s in env.smp[V + 2:X]), "CHK-021: second frame or overrun during the low line"
    assert [x for x in env.loads[lb:] if x[0] < X] == [(V, 0, 1)] and len(env.drops) == db, \
        "CHK-021: exactly one byte expected from the low line"
    env.chk_load(T2, 0xA5, 0, "CHK-021")
    env.finish()


@cocotb.test()
async def test_chk_022_rx_basic(dut):
    """CHK-022: directed and random receive frames, V=T0+H+9N+2, taken at V+1."""
    env = await Env(dut).start()
    env.idle()
    await env.reset()
    dut.i_rx_ready.value = 1
    r = rng(22)
    N = env.N
    data = [0x00, 0xFF, 0x55, 0xAA, 0x01, 0x80] + [r.getrandbits(8) for _ in range(env.cnt(20, lo=1))]
    lb, db, k0 = len(env.loads), len(env.drops), env.n
    Ts = []
    for b in data:
        await env.rx_runs([(1, r.randint(2 * N, 3 * N))])
        Ts.append(await env.rx_runs(frame_runs(b, N)))
    await env.rx_runs([(1, 2 * N + 4)])
    exp = []
    for T, b in zip(Ts, data):
        V = env.chk_load(T, b, 0, "CHK-022")
        assert env.smp[V + 2].rv == 0, f"CHK-022: o_rx_valid expected 0 at V+2={V + 2} (taken at V+1)"
        exp.append((V, b, 0))
    assert env.loads[lb:] == exp, f"CHK-022: expected {len(exp)} deliveries in order"
    assert len(env.drops) == db and all(s.ov == 0 and s.fe == 0 for s in env.smp[k0:env.n]), \
        "CHK-022: o_rx_overrun/o_rx_frame_err must stay 0"
    env.finish()


@cocotb.test()
async def test_chk_023_sampling_points(dut):
    """CHK-023: sampling-point test (patterns A and B) at T0, T0+H, T0+H+(i+1)N and M."""
    env = await Env(dut).start()
    await scen_023(env, rng(23), env.cnt(10, lo=1))
    env.finish()


@cocotb.test()
async def test_chk_024_glitch(dut):
    """CHK-024: start-bit glitches of 1..H rejected, H+1 accepted, restart right after a glitch."""
    env = await Env(dut).start()
    await scen_024(env)
    env.finish()


@cocotb.test()
async def test_chk_025_rx_back_to_back(dut):
    """CHK-025: back-to-back receive frames and a new start at M+1."""
    env = await Env(dut).start()
    N, H = env.N, env.H
    await scen_025a(env, rng(25), env.cnt(6, lo=1))
    env.idle()
    await env.reset()
    dut.i_rx_ready.value = 1
    await env.rx_runs([(1, 2 * N)])
    runs = [(v, N) for v in fbits(0xC3)[:9]] + [(1, H + 1)]
    T0 = await env.rx_runs(runs)
    M = T0 + H + 9 * N
    T1 = await env.rx_runs(frame_runs(0x3C, N) + [(1, 2 * N + 4)])
    assert T1 == M + 1 and T1 in env.starts, f"CHK-025(b): start of 8'h3C expected at M+1={M + 1}"
    V = env.chk_load(T0, 0xC3, 0, "CHK-025(b)")
    assert V == M + 2, f"CHK-025(b): 8'hC3 expected at M+2={M + 2} got {V}"
    env.chk_load(T1, 0x3C, 0, "CHK-025(b)")
    env.finish()


@cocotb.test()
async def test_chk_026_rx_ready(dut):
    """CHK-026: i_rx_ready held 0/1/random, overrun, take at V and at V-1."""
    env = await Env(dut).start()
    await scen_026(env, rng(26), "abcde")
    env.finish()


@cocotb.test()
async def test_chk_027_frame_error(dut):
    """CHK-027: frame error with an empty register and with the byte dropped by overrun."""
    env = await Env(dut).start()
    N = env.N
    env.idle()
    await env.reset()
    await env.rx_runs([(1, 2 * N)])
    T0 = await env.rx_runs(frame_runs(0xC3, N, 0) + [(1, 2 * N)])
    V = env.chk_load(T0, 0xC3, 1, "CHK-027(a)")
    t = env.n
    assert all((s.rv, s.rd, s.fe) == (1, 0xC3, 1) for s in env.smp[V + 1:t]), "CHK-027(a): byte not held until the take"
    dut.i_rx_ready.value = 1
    await env.fe()
    dut.i_rx_ready.value = 0
    await env.fe(2)
    s = env.smp[t + 1]
    assert (s.rv, s.rd, s.fe) == (0, 0xC3, 1), f"CHK-027(a): after take expected valid=0 err stays 1, got {s.rv}/{hx(s.rd)}/{s.fe}"
    await env.rx_runs([(1, N)])
    T1 = await env.rx_runs(frame_runs(0x3C, N) + [(1, 2 * N)])
    env.chk_load(T1, 0x3C, 0, "CHK-027(a)")
    # (b)
    env.idle()
    await env.reset()
    await env.rx_runs([(1, 2 * N)])
    T = await env.rx_runs(frame_runs(0x11, N) + [(1, 2 * N)])
    env.chk_load(T, 0x11, 0, "CHK-027(b)")
    k0, lb = env.n, len(env.loads)
    T2 = await env.rx_runs(frame_runs(0xEE, N, 0) + [(1, 2 * N)])
    V = env.chk_drop(T2, 0x11, 0, "CHK-027(b)")
    assert [k for k in range(k0, env.n) if env.smp[k].ov] == [V + 1], "CHK-027(b): overrun expected only at V+1"
    assert all((s.rd, s.fe) == (0x11, 0) for s in env.smp[k0:env.n]), "CHK-027(b): held byte or flag changed"
    t = env.n
    dut.i_rx_ready.value = 1
    await env.fe()
    dut.i_rx_ready.value = 0
    await env.fe(env.F)
    assert env.smp[t + 1].rv == 0, "CHK-027(b): o_rx_valid expected 0 after the take"
    assert len(env.loads) == lb and all(s.rv == 0 for s in env.smp[t + 1:env.n]), "CHK-027(b): 8'hEE must never be delivered"
    env.finish()


@cocotb.test()
async def test_chk_028_idle_break(dut):
    """CHK-028: idle line delivers nothing; a break gives exactly one frame (or one overrun)."""
    env = await Env(dut).start()
    N = env.N
    r = rng(28)
    env.idle()
    await env.reset()
    k0 = env.n
    await env.rx_runs([(1, env.long(30))], ready_fn=lambda n: r.getrandbits(1))
    assert all(s.rv == 0 and s.ov == 0 for s in env.smp[k0:env.n]), "CHK-028(a): idle line produced output"
    # (b)
    env.idle()
    await env.reset()
    dut.i_rx_ready.value = 1
    await env.rx_runs([(1, 2 * N)])
    lb, db = len(env.loads), len(env.drops)
    T0 = await env.rx_runs([(0, env.long(50))])
    X = await env.rx_runs([(1, 1)])
    T1 = await env.rx_runs(frame_runs(0x5A, N) + [(1, 2 * N)])
    V = env.chk_load(T0, 0x00, 1, "CHK-028(b)")
    assert [x for x in env.loads[lb:] if x[0] < X] == [(V, 0, 1)] and len(env.drops) == db, \
        "CHK-028(b): exactly one delivery expected from the break"
    assert all(s.rv == 0 for s in env.smp[V + 2:X + 1]) and all(s.ov == 0 for s in env.smp[T0:env.n]), \
        "CHK-028(b): further valid rise or overrun during the break"
    assert T1 == X + 1 and T1 in env.starts, f"CHK-028(b): 8'h5A start expected at X+1={X + 1}"
    env.chk_load(T1, 0x5A, 0, "CHK-028(b)")
    # (c)
    env.idle()
    await env.reset()
    await env.rx_runs([(1, 2 * N)])
    T = await env.rx_runs(frame_runs(0x77, N) + [(1, 2 * N)])
    env.chk_load(T, 0x77, 0, "CHK-028(c)")
    k0 = env.n
    T0 = await env.rx_runs([(0, env.long(50))])
    await env.rx_runs([(1, 2 * N)])
    V = env.chk_drop(T0, 0x77, 0, "CHK-028(c)")
    assert [k for k in range(k0, env.n) if env.smp[k].ov] == [V + 1], "CHK-028(c): exactly one overrun pulse expected"
    assert all((s.rv, s.rd, s.fe) == (1, 0x77, 0) for s in env.smp[k0:env.n]), "CHK-028(c): 8'h77 must stay held"
    env.finish()


@cocotb.test()
async def test_chk_029_rx_random(dut):
    """CHK-029: random receive regression (gaps, stop errors, glitches, random i_rx_ready) vs the model."""
    env = await Env(dut).start()
    env.idle()
    await env.reset()
    r = rng(29)
    fb, lb, db, k0 = len(env.frames), len(env.loads), len(env.drops), env.n
    sent = await env.rx_random(r, env.cnt(300), 3 * env.N, 0.1, 0.1, ready_fn=lambda n: int(r.random() < 0.5))
    env.chk_rx_stream(sent, fb, lb, db, k0, "CHK-029")
    env.finish()


@cocotb.test()
async def test_chk_030_tx_back_to_back(dut):
    """CHK-030: back-to-back transmit with i_tx_valid held at 1, one byte every 10N cycles."""
    env = await Env(dut).start()
    await scen_030(env, rng(30), env.cnt(20, lo=1))
    env.finish()


@cocotb.test()
async def test_chk_031_tx_gaps(dut):
    """CHK-031: transmit with idle gaps; i_tx_data changes every cycle; only the accepting edge counts."""
    env = await Env(dut).start()
    env.idle()
    await env.reset()
    await env.fe(2)
    r = rng(31)
    F = env.F
    base, k0 = len(env.accepts), env.n
    cnt = env.cnt(50)
    exp = await env.tx_random(r, cnt, 3 * env.N, chaos=True)
    await env.fe(F + 4)
    acc = env.accepts[base:]
    assert acc == exp and len(acc) == cnt, f"CHK-031: accepted {len(acc)} bytes, expected {cnt} matching the handshakes"
    active = set()
    for e, b in acc:
        env.chk_tx_frame(e, b, "CHK-031")
        active.update(range(e + 1, e + F + 1))
    for k in range(k0, env.n):
        if k not in active:
            s = env.smp[k]
            assert s.txd == 1 and s.rdy == 1, f"CHK-031: idle sample {k} expected txd=1 ready=1 got {s.txd}/{s.rdy}"
    dec = env.tx_decode(k0, env.n)
    assert [x[1] for x in dec] == [b for _, b in exp], "CHK-031: decoded o_txd bytes differ from the accepted bytes"
    env.finish()


@cocotb.test()
async def test_chk_032_tx_valid_drop(dut):
    """CHK-032: offers while o_tx_ready=0 are not recorded; held offer accepted at E0+10N; one-cycle pulse."""
    env = await Env(dut).start()
    N, F = env.N, env.F
    r = rng(32)
    # (a)
    env.idle()
    await env.reset()
    await env.fe(2)
    base = len(env.accepts)
    E0 = await env.tx_one(0x12, "CHK-032(a)")
    dut.i_tx_data.value = 0xED
    dut.i_tx_valid.value = 1
    await env.until(E0 + 1 + min(100, F - 1))
    dut.i_tx_valid.value = 0
    await env.until(E0 + F + 1 + 20 * N + 2)
    assert env.accepts[base:] == [(E0, 0x12)], f"CHK-032(a): only 8'h12 may be accepted, got {env.accepts[base:]}"
    for k in range(E0 + F + 1, E0 + F + 1 + 20 * N):
        s = env.smp[k]
        assert s.txd == 1 and s.rdy == 1, f"CHK-032(a): idle expected at E0+{k - E0}, got txd={s.txd} ready={s.rdy}"
    assert [x[1] for x in env.tx_decode(E0 + 1, env.n)] == [0x12], "CHK-032(a): 8'hED must never be sent"
    # (b)
    env.idle()
    await env.reset()
    await env.fe(2)
    base = len(env.accepts)
    E0 = await env.tx_one(0x34, "CHK-032(b)")
    dut.i_tx_data.value = 0xCB
    dut.i_tx_valid.value = 1
    for _ in range(F + 4):
        await env.fe()
        if len(env.accepts) - base >= 2:
            break
    dut.i_tx_valid.value = 0
    await env.fe(2 * F)
    assert env.accepts[base:] == [(E0, 0x34), (E0 + F, 0xCB)], f"CHK-032(b): handshake of 8'hCB expected at E0+{F}, got {env.accepts[base:]}"
    assert env.smp[E0 + F + 1].txd == 0, "CHK-032(b): o_txd expected 0 at E0+10N+1"
    env.chk_tx_frame(E0 + F, 0xCB, "CHK-032(b)")
    assert [x[1] for x in env.tx_decode(E0 + 1, env.n)] == [0x34, 0xCB], "CHK-032(b): 8'hCB must be sent exactly once"
    # (c)
    env.idle()
    await env.reset()
    await env.fe(3)
    base = len(env.accepts)
    b = r.getrandbits(8)
    E0 = await env.tx_one(b, "CHK-032(c)")
    await env.fe(F + 4)
    assert env.accepts[base:] == [(E0, b)], "CHK-032(c): single-cycle pulse must be accepted once"
    env.chk_tx_frame(E0, b, "CHK-032(c)")
    env.finish()


@cocotb.test()
async def test_regression_random(dut):
    """CHK-001..CHK-013 (all assertion checks): random full-duplex traffic with random gaps, back pressure,
    frame errors, glitches and asynchronous resets in the middle of traffic, checked against the models."""
    env = await Env(dut).start()
    r, rt, rr = rng("regr"), rng("regr-tx"), rng("regr-rdy")
    N, F = env.N, env.F

    def rf(n):
        return int(rr.random() < 0.6)

    for phase in range(3):
        env.idle()
        await env.reset(1 + phase)
        await env.fe(2)
        base = len(env.accepts)
        fb, lb, db, k0 = len(env.frames), len(env.loads), len(env.drops), env.n
        txt = cocotb.start_soon(env.tx_random(rt, env.cnt(60), 3 * N, chaos=True))
        sent = await env.rx_random(r, env.cnt(60), 3 * N, 0.1, 0.1, ready_fn=rf)
        exp = await txt
        await env.fe(F + 4)
        acc = env.accepts[base:]
        assert acc == exp, f"CHK-010: accepted transmit bytes {acc[:3]} differ from the handshakes driven {exp[:3]}"
        for e, b in acc:
            env.chk_tx_frame(e, b, "CHK-011")
        env.chk_rx_stream(sent, fb, lb, db, k0, "CHK-006")
    # asynchronous resets in the middle of traffic
    env.idle()
    await env.fe(2)
    env.stop_bg = False
    txt = cocotb.start_soon(env.tx_random(rt, 10 ** 4, 3 * N))
    rxt = cocotb.start_soon(env.rx_random(r, 10 ** 4, 3 * N, 0.1, 0.1, ready_fn=rf))
    await env.fe(r.randint(5 * N, 25 * N))
    await env.reset(r.randint(1, 4))
    await env.fe(r.randint(3 * N, 15 * N))
    await env.reset(2)
    await env.fe(r.randint(N, 5 * N))
    env.stop_bg = True
    await env.fe(3)
    await txt
    await rxt
    env.stop_bg = False
    env.idle()
    await env.fe(F + 2 * N)
    dut.i_rx_ready.value = 1
    E0 = await env.tx_one(0x5A, "CHK-010")
    await env.rx_runs([(1, 2 * N)])
    T = await env.rx_runs(frame_runs(0xC3, N) + [(1, 2 * N + 4)])
    await env.fe(F)
    env.chk_tx_frame(E0, 0x5A, "CHK-011")
    env.chk_load(T, 0xC3, 0, "CHK-003")
    env.finish()

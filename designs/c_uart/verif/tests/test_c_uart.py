"""cocotb 2.1 testbench for the `uart` DUT (AXI-Stream <-> 8N1 UART, prescale = Fclk/(baud*8)).

Timing model: every model and every check works at falling edges (mid-cycle). A shared cycle
counter is incremented on every rising edge, so a value sampled at a falling edge with counter
value N is the DUT state after rising edge N, and an input driven at that falling edge is seen by
the DUT at rising edge N+1.

Reusable models:
  CycleCounter   - rising-edge counter (common time base)
  Trace          - samples all DUT outputs every cycle; checks CHK-002/003/004 continuously
  AxisSink       - m_axis destination with random/forced back pressure; checks CHK-001 continuously
  AxisSource     - legal s_axis source (holds tvalid/tdata until tready)
  UartLineDriver - drives 8N1 frames on rxd
  TxMonitor      - decodes 8N1 frames on txd and measures bit-boundary timing
  UartRefModel   - reference model of expected results (spec text only)
"""

import cocotb
from cocotb.triggers import RisingEdge

from nnc_cocotb import *  # noqa: F401,F403


def _param(name, default):
    try:
        v = PARAMS.get(name, default)
        return int(v) if v is not None else default
    except Exception:
        return default


DW = _param("DATA_WIDTH", 8)
MASK = (1 << DW) - 1
NBITS = DW + 2            # start + DW data bits + stop
BG_LIMIT = 20_000_000     # hard bound for background monitor loops


# --------------------------------------------------------------------------- helpers
def hx(x):
    return "X" if x is None else f"0x{x:02x}"


def frame_bits(word, stop=1):
    """8N1 frame: start 0, data LSB first, stop bit."""
    return [0] + [(word >> i) & 1 for i in range(DW)] + [stop]


def low_to_high(bits):
    return sum(1 for i in range(1, len(bits)) if bits[i - 1] == 0 and bits[i] == 1)


def n_changes(bits):
    return sum(1 for i in range(1, len(bits)) if bits[i - 1] != bits[i])


def mid_stop(t0, bp):
    return t0 + (DW + 1) * bp + bp // 2


def frame_end(t0, bp):
    return t0 + NBITS * bp


async def wait_for(dut, cond, max_cycles, msg):
    """Bounded poll at falling edges."""
    for _ in range(int(max_cycles)):
        if cond():
            return
        await next_cycle(dut)
    assert cond(), msg


# --------------------------------------------------------------------------- models
class CycleCounter:
    def __init__(self, dut):
        self.clk = getattr(dut, CLOCK)
        self.n = 0
        cocotb.start_soon(self._run())

    async def _run(self):
        for _ in range(BG_LIMIT):
            await RisingEdge(self.clk)
            self.n += 1


class Trace:
    """Samples every DUT output at each falling edge and checks the per-cycle assertions."""

    SIGS = ("txd", "tx_busy", "rx_busy", "m_axis_tvalid", "m_axis_tdata",
            "s_axis_tready", "rx_overrun_error", "rx_frame_error")

    def __init__(self, env):
        self.env = env
        self.h = {s: getattr(env.dut, s) for s in self.SIGS}
        self.rec = {}
        self.txd_low = 0
        self.ovr = 0
        self.fe = 0
        cocotb.start_soon(self._run())

    async def _run(self):
        dut = self.env.dut
        prev = None
        for _ in range(BG_LIMIT):
            t = self.env.cyc.n
            s = {k: val(h) for k, h in self.h.items()}
            self.rec[t] = s
            if s["txd"] == 0:
                self.txd_low += 1
                assert s["tx_busy"] == 1, (
                    f"CHK-004: tx_busy=1 whenever txd=0 got tx_busy={s['tx_busy']} at edge {t}")
            if s["rx_overrun_error"] == 1:
                self.ovr += 1
            if s["rx_frame_error"] == 1:
                self.fe += 1
            if prev is not None:
                if prev["rx_overrun_error"] == 1:
                    assert s["rx_overrun_error"] == 0, (
                        f"CHK-002: rx_overrun_error single-cycle pulse got "
                        f"{s['rx_overrun_error']} at edge {t} after 1 at edge {t - 1}")
                if prev["rx_frame_error"] == 1:
                    assert s["rx_frame_error"] == 0, (
                        f"CHK-003: rx_frame_error single-cycle pulse got "
                        f"{s['rx_frame_error']} at edge {t} after 1 at edge {t - 1}")
            prev = s
            await next_cycle(dut)

    def expect(self, chk, sig, a, b, pred, desc):
        if b < a:
            return
        bad = []
        n = 0
        for t in range(a, b + 1):
            s = self.rec.get(t)
            if s is None:
                continue
            n += 1
            if not pred(s[sig]):
                bad.append((t, s[sig]))
        assert n >= (b - a), f"{chk}: trace covering edges {a}..{b} got only {n} samples"
        assert not bad, (f"{chk}: {desc} at every edge {a}..{b} got {sig}={bad[0][1]} at edge "
                         f"{bad[0][0]} ({len(bad)} violating edges)")

    def count(self, sig, a, b, pred):
        return sum(1 for t in range(a, b + 1) if t in self.rec and pred(self.rec[t][sig]))

    def pulses(self, sig):
        return sorted(t for t, s in self.rec.items() if s[sig] == 1)


class AxisSink:
    """m_axis destination. mode: 'on' (tready=1), 'off' (tready=0), 'random'."""

    def __init__(self, env, rnd, mode="on", p_ready=0.5, max_wait=None):
        self.env = env
        self.rnd = rnd
        self.mode = mode
        self.p_ready = p_ready
        self.max_wait = max_wait
        self.handshakes = []   # (rising edge of transfer, data)
        self.rises = []        # edge at which m_axis_tvalid rose
        self.stall_cycles = 0
        cocotb.start_soon(self._run())

    async def _run(self):
        dut = self.env.dut
        prev_v, prev_d, prev_r = 0, None, 1
        pend = None
        for _ in range(BG_LIMIT):
            t = self.env.cyc.n
            v = val(dut.m_axis_tvalid)
            d = val(dut.m_axis_tdata)
            if prev_v == 1 and prev_r == 0:
                assert v == 1 and d == prev_d, (
                    f"CHK-001: m_axis stalled with tvalid=1 tdata={hx(prev_d)} after tready=0 "
                    f"got tvalid={v} tdata={hx(d)} at edge {t}")
            if v == 1 and prev_v != 1:
                self.rises.append(t)
            if v == 1 and pend is None:
                pend = t
            if v != 1:
                pend = None
            if self.mode == "on":
                r = 1
            elif self.mode == "off":
                r = 0
            else:
                r = 1 if self.rnd.random() < self.p_ready else 0
                if (v == 1 and pend is not None and self.max_wait is not None
                        and t - pend >= self.max_wait):
                    r = 1
            dut.m_axis_tready.value = r
            if v == 1 and r == 0:
                self.stall_cycles += 1
            if v == 1 and r == 1:
                self.handshakes.append((t + 1, d))
                pend = None
            prev_v, prev_d, prev_r = v, d, r
            await next_cycle(dut)

    def data(self):
        return [d for _, d in self.handshakes]


class AxisSource:
    """Legal s_axis source: holds tvalid and tdata stable until the edge where tready=1."""

    def __init__(self, env):
        self.env = env
        self.handshakes = []   # (rising edge of transfer, word)

    async def send(self, word, max_cycles, chk):
        dut = self.env.dut
        dut.s_axis_tdata.value = word
        dut.s_axis_tvalid.value = 1
        for _ in range(int(max_cycles)):
            t = self.env.cyc.n
            rdy = val(dut.s_axis_tready)
            await next_cycle(dut)
            if rdy == 1:
                self.handshakes.append((t + 1, word))
                dut.s_axis_tvalid.value = 0
                return t + 1
        dut.s_axis_tvalid.value = 0
        raise AssertionError(f"{chk}: s_axis_tready=1 within {max_cycles} cycles while "
                             f"s_axis_tvalid=1 (word {hx(word)}) got no handshake")


class UartLineDriver:
    """Drives 8N1 frames on rxd, synchronous to clk."""

    def __init__(self, env):
        self.env = env
        self.frames = []   # (t0 = edge counter when start bit was driven, word, stop, bp)

    async def send(self, word, bp, stop=1):
        dut = self.env.dut
        t0 = self.env.cyc.n
        self.frames.append((t0, word, stop, bp))
        for b in frame_bits(word, stop):
            dut.rxd.value = b
            await next_cycle(dut, bp)
        dut.rxd.value = 1
        return t0


class TxMonitor:
    """Decodes txd as 8N1 frames with bit period 8*prescale and records transition timing."""

    def __init__(self, env):
        self.env = env
        self.frames = []
        cocotb.start_soon(self._run())

    async def _run(self):
        dut = self.env.dut
        prev = val(dut.txd)
        col = None
        for _ in range(BG_LIMIT):
            t = self.env.cyc.n
            x = val(dut.txd)
            if col is None:
                if prev == 1 and x == 0:
                    bp = 8 * self.env.prescale
                    col = {"t0": t, "bp": bp, "s": [0]}
            else:
                col["s"].append(x)
                bp = col["bp"]
                if len(col["s"]) >= (DW + 1) * bp + bp // 2 + 1:
                    self.frames.append(self._decode(col))
                    col = None
            prev = x
            await next_cycle(dut)

    @staticmethod
    def _decode(col):
        s, bp = col["s"], col["bp"]
        bits = [s[k * bp + bp // 2] for k in range(NBITS)]
        word = 0
        for i in range(DW):
            b = bits[1 + i]
            if b is None:
                word = None
                break
            word |= (b & 1) << i
        trans = [(i, s[i]) for i in range(1, len(s)) if s[i] != s[i - 1]]
        bad = []
        for i, _ in trans:
            k = int(round(i / bp))
            if not (1 <= k <= DW + 1 and abs(i - k * bp) <= 1):
                bad.append(i)
        return {"t0": col["t0"], "bp": bp, "bits": bits, "word": word, "start": bits[0],
                "stop": bits[-1], "trans": trans, "bad": bad}

    def words(self):
        return [f["word"] for f in self.frames]


class UartRefModel:
    """Expected results, from the specification text only.
    TX: every word taken on an s_axis handshake is sent once, in order.
    RX: a correctly framed word is delivered once; a bad stop bit gives one frame_error pulse
        and the word is discarded; a word received while the previous one is still pending gives
        one overrun_error pulse and the new word is discarded (pending word kept)."""

    def __init__(self):
        self.tx_expected = []
        self.rx_expected = []
        self.n_frame_err = 0
        self.n_overrun = 0

    def tx_accept(self, word):
        self.tx_expected.append(word & MASK)

    def rx_good(self, word, pending):
        if pending:
            self.n_overrun += 1
        else:
            self.rx_expected.append(word & MASK)

    def rx_bad_stop(self, word):
        self.n_frame_err += 1


class Env:
    def __init__(self, dut, salt):
        self.dut = dut
        self.salt = salt
        self.rnd = rng(salt)
        self.prescale = 1

    async def start(self, prescale, sink_mode="on", p_ready=0.5, max_wait=None, reset_cycles=5):
        dut = self.dut
        start_clock(dut)
        self.cyc = CycleCounter(dut)
        self.prescale = prescale
        m_rdy = 0 if sink_mode == "off" else 1
        idle = {"rxd": 1, "s_axis_tvalid": 0, "s_axis_tdata": 0, "m_axis_tready": m_rdy,
                "prescale": prescale}
        await reset_dut(dut, cycles=reset_cycles, idle=idle)
        dut.rxd.value = 1
        dut.s_axis_tvalid.value = 0
        dut.s_axis_tdata.value = 0
        dut.m_axis_tready.value = m_rdy
        dut.prescale.value = prescale
        await next_cycle(dut)
        self.trace = Trace(self)
        self.sink = AxisSink(self, rng(f"{self.salt}_sink"), sink_mode, p_ready, max_wait)
        self.txmon = TxMonitor(self)
        self.src = AxisSource(self)
        self.line = UartLineDriver(self)
        self.t_start = self.cyc.n

    async def set_prescale(self, p, chk):
        dut = self.dut
        await wait_for(dut, lambda: val(dut.tx_busy) == 0 and val(dut.rx_busy) == 0,
                       8 * max(self.prescale, 1) * NBITS * 6 + 100,
                       f"{chk}: tx_busy=0 and rx_busy=0 before changing prescale got busy stuck")
        dut.prescale.value = p
        self.prescale = p
        await next_cycle(dut, 2)


def check_tx_frame(chk, env, f, w, timing):
    bp = f["bp"]
    t0 = f["t0"]
    assert f["start"] == 0, f"{chk}: start bit 0 on txd for frame at {t0} got {f['start']}"
    assert f["stop"] == 1, f"{chk}: stop bit 1 on txd for frame at {t0} got {f['stop']}"
    assert f["word"] == w, f"{chk}: txd frame at {t0} decodes to {hx(w)} got {hx(f['word'])}"
    if not timing:
        return
    exp = frame_bits(w)
    assert not f["bad"], (f"{chk}: txd transitions at k*{bp}+-1 cycles (k=1..{DW + 1}) after "
                          f"start of frame at {t0} got transitions at offsets {f['bad']}")
    assert len(f["trans"]) == n_changes(exp), (
        f"{chk}: {n_changes(exp)} txd transitions in frame {hx(w)} got {len(f['trans'])}")
    rises = sum(1 for _, v in f["trans"] if v == 1)
    assert rises == low_to_high(exp), (
        f"{chk}: {low_to_high(exp)} low-to-high transitions for {hx(w)} got {rises}")
    k1 = exp.index(1)
    i1 = f["trans"][0][0] if f["trans"] else None
    assert i1 is not None and abs(i1 - k1 * bp) <= 1, (
        f"{chk}: first txd rise of {hx(w)} at {k1 * bp}+-1 cycles (start bit {bp} cycles) "
        f"got {i1}")
    env.trace.expect(chk, "txd", t0 + (DW + 1) * bp + 1, t0 + NBITS * bp - 2,
                     lambda v: v == 1, f"txd=1 during stop bit of frame {hx(w)}")


# --------------------------------------------------------------------------- tests
@cocotb.test()
async def test_chk_005_rx_backpressure(dut):
    """CHK-005: each received rxd frame gives exactly one m_axis transfer under back pressure."""
    env = Env(dut, "chk005")
    await env.start(prescale=4, sink_mode="random", p_ready=0.5, max_wait=100)
    bp = 32
    r = env.rnd
    words = [r.randrange(1 << DW) for _ in range(64)]
    for w in words:
        g = r.randint(0, 100)
        if g:
            await next_cycle(dut, g)
        await env.line.send(w, bp)
    await wait_for(dut, lambda: len(env.sink.handshakes) >= len(words), 20 * bp,
                   f"CHK-005: {len(words)} m_axis handshakes got {len(env.sink.handshakes)}")
    await next_cycle(dut, 4 * bp)

    got = env.sink.data()
    assert got == words, f"CHK-005: m_axis words {[hx(w) for w in words]} got {[hx(g) for g in got]}"
    rises = env.sink.rises
    assert len(rises) == len(words), f"CHK-005: m_axis_tvalid rises once per frame ({len(words)}) got {len(rises)}"
    fr = env.line.frames
    for i, t_r in enumerate(rises):
        lo = mid_stop(fr[i][0], bp)
        assert t_r >= lo, f"CHK-005: tvalid rise for frame {i} no earlier than {lo} got {t_r}"
        if i + 1 < len(fr):
            hi = mid_stop(fr[i + 1][0], bp)
            assert t_r < hi, f"CHK-005: tvalid rise for frame {i} before next frame stop ({hi}) got {t_r}"
    assert not env.trace.pulses("rx_overrun_error"), (
        f"CHK-005: rx_overrun_error=0 always got pulses at {env.trace.pulses('rx_overrun_error')[:5]}")
    assert not env.trace.pulses("rx_frame_error"), (
        f"CHK-005: rx_frame_error=0 always got pulses at {env.trace.pulses('rx_frame_error')[:5]}")


@cocotb.test()
async def test_chk_006_rx_busy(dut):
    """CHK-006: rx_busy is high while a reception is in progress and low when idle."""
    env = Env(dut, "chk006")
    await env.start(prescale=2, sink_mode="on")
    bp = 16
    ts = env.t_start
    await next_cycle(dut, 200)
    env.trace.expect("CHK-006", "rx_busy", ts, ts + 199, lambda v: v == 0,
                     "rx_busy=0 during initial idle")
    t0a = await env.line.send(0x00, bp)
    await next_cycle(dut, 300)
    t0b = await env.line.send(0xFF & MASK, bp)
    await next_cycle(dut, 300)
    tend = env.cyc.n - 1
    for t0, tnext in ((t0a, t0b), (t0b, tend + 1)):
        env.trace.expect("CHK-006", "rx_busy", t0 + bp // 2, mid_stop(t0, bp), lambda v: v == 1,
                         f"rx_busy=1 during reception of frame started at {t0}")
        env.trace.expect("CHK-006", "rx_busy", frame_end(t0, bp) + 2 * bp, tnext - 1,
                         lambda v: v == 0, f"rx_busy=0 after frame started at {t0}")
    got = env.sink.data()
    assert got == [0x00, 0xFF & MASK], f"CHK-006: delivered words [0x00, 0xff] got {[hx(g) for g in got]}"


@cocotb.test()
async def test_chk_007_rx_overrun(dut):
    """CHK-007: overrun gives a one-cycle rx_overrun_error pulse; the new word is discarded."""
    env = Env(dut, "chk007")
    await env.start(prescale=2, sink_mode="off")
    bp = 16
    await env.line.send(0x3C, bp)
    await wait_for(dut, lambda: val(dut.m_axis_tvalid) == 1, 4 * bp,
                   "CHK-007: m_axis_tvalid=1 after W1=0x3C got 0")
    t_pres = env.cyc.n
    t2 = await env.line.send(0xC3, bp)
    await next_cycle(dut, 100)
    t_on = env.cyc.n
    env.sink.mode = "on"
    await next_cycle(dut, 50)
    t_on_end = env.cyc.n
    t3 = await env.line.send(0x5A, bp)
    await wait_for(dut, lambda: len(env.sink.handshakes) >= 2, 4 * bp,
                   f"CHK-007: W3 delivered got {len(env.sink.handshakes)} handshakes")
    await next_cycle(dut, 4 * bp)

    env.trace.expect("CHK-007", "m_axis_tvalid", t_pres, t_on - 1, lambda v: v == 1,
                     "m_axis_tvalid=1 while pending and tready=0")
    env.trace.expect("CHK-007", "m_axis_tdata", t_pres, t_on - 1, lambda v: v == 0x3C,
                     "m_axis_tdata=0x3c while pending and tready=0")
    ov = env.trace.pulses("rx_overrun_error")
    lo, hi = mid_stop(t2, bp), frame_end(t2, bp) + 2 * bp
    assert len(ov) == 1 and lo <= ov[0] <= hi, (
        f"CHK-007: exactly one rx_overrun_error pulse in [{lo},{hi}] got pulses at {ov}")
    fe = env.trace.pulses("rx_frame_error")
    assert not fe, f"CHK-007: rx_frame_error=0 throughout got pulses at {fe}"
    hs_on = [(t, d) for t, d in env.sink.handshakes if t_on <= t <= t_on_end + 1]
    assert len(hs_on) == 1 and hs_on[0][1] == 0x3C, (
        f"CHK-007: exactly one handshake with 0x3c when tready raised got {[(t, hx(d)) for t, d in hs_on]}")
    env.trace.expect("CHK-007", "m_axis_tvalid", hs_on[0][0], t3 + (DW + 1) * bp,
                     lambda v: v == 0, "m_axis_tvalid=0 after the single handshake")
    got = env.sink.data()
    assert 0xC3 not in got, f"CHK-007: 0xc3 never transferred got {[hx(g) for g in got]}"
    assert got == [0x3C, 0x5A], f"CHK-007: transfers [0x3c, 0x5a] got {[hx(g) for g in got]}"


@cocotb.test()
async def test_chk_008_rx_frame_error(dut):
    """CHK-008: bad stop bit gives a one-cycle rx_frame_error pulse; the word is discarded."""
    env = Env(dut, "chk008")
    await env.start(prescale=2, sink_mode="on")
    bp = 16
    tb = await env.line.send(0xA5, bp, stop=0)
    dut.rxd.value = 1
    await next_cycle(dut, 200)
    tg = await env.line.send(0x96, bp)
    await wait_for(dut, lambda: len(env.sink.handshakes) >= 1, 4 * bp,
                   "CHK-008: valid frame 0x96 delivered got no handshake")
    await next_cycle(dut, 4 * bp)

    fe = env.trace.pulses("rx_frame_error")
    lo, hi = mid_stop(tb, bp), frame_end(tb, bp) + 2 * bp
    assert len(fe) == 1 and lo <= fe[0] <= hi, (
        f"CHK-008: exactly one rx_frame_error pulse in [{lo},{hi}] got pulses at {fe}")
    env.trace.expect("CHK-008", "m_axis_tvalid", tb, tg + (DW + 1) * bp, lambda v: v == 0,
                     "m_axis_tvalid=0 from bad frame until valid frame")
    ov = env.trace.pulses("rx_overrun_error")
    assert not ov, f"CHK-008: rx_overrun_error=0 throughout got pulses at {ov}"
    got = env.sink.data()
    assert got == [0x96], f"CHK-008: exactly one transfer of 0x96 got {[hx(g) for g in got]}"


@cocotb.test()
async def test_chk_009_tx_handshake_order(dut):
    """CHK-009: TX words accepted only on s_axis handshakes and sent once each, in order."""
    env = Env(dut, "chk009")
    await env.start(prescale=4, sink_mode="on", reset_cycles=2)
    bp = 32
    r = env.rnd
    words = [r.randrange(1 << DW) for _ in range(64)]
    idle_after = 32
    idle_win = None
    for i, w in enumerate(words):
        g = r.randint(0, 200)
        if g:
            await next_cycle(dut, g)
        await env.src.send(w, 4 * NBITS * bp, "CHK-009")
        if i == idle_after - 1:
            await wait_for(dut, lambda: len(env.txmon.frames) >= idle_after, 3 * NBITS * bp,
                           f"CHK-009: {idle_after} frames on txd got {len(env.txmon.frames)}")
            await next_cycle(dut, bp)
            ta = env.cyc.n
            await next_cycle(dut, 2000)
            idle_win = (ta, env.cyc.n - 1)
    await wait_for(dut, lambda: len(env.txmon.frames) >= len(words), 3 * NBITS * bp,
                   f"CHK-009: {len(words)} frames on txd got {len(env.txmon.frames)}")
    await next_cycle(dut, 2 * NBITS * bp)

    hs = [w for _, w in env.src.handshakes]
    assert hs == words, f"CHK-009: source handshakes for all words got {len(hs)}"
    dec = env.txmon.words()
    assert dec == hs, (f"CHK-009: txd words equal handshake words ({len(hs)}) got {len(dec)} frames; "
                       f"first diff {next((i for i in range(min(len(dec), len(hs))) if dec[i] != hs[i]), None)}")
    for f, w in zip(env.txmon.frames, hs):
        check_tx_frame("CHK-009", env, f, w, timing=False)
    env.trace.expect("CHK-009", "txd", idle_win[0], idle_win[1], lambda v: v == 1,
                     "txd=1 during 2000-cycle idle period")


@cocotb.test()
async def test_chk_010_prescale_rate(dut):
    """CHK-010: prescale sets the data rate; one bit is 8*prescale clk cycles on txd and rxd."""
    env = Env(dut, "chk010")
    await env.start(prescale=1, sink_mode="on")
    words = [0x55 & MASK, 0x00, 0xFF & MASK, 0xA3 & MASK]
    unverifiable_k10 = []
    for p in (1, 3, 10):
        await env.set_prescale(p, "CHK-010")
        bp = 8 * p
        nf0 = len(env.txmon.frames)
        nh0 = len(env.sink.handshakes)
        # (a) TX: next word offered once the previous frame is in its stop bit, so the DUT
        # starts it when the previous frame has finished (exposes the k=10 boundary).
        for i, w in enumerate(words):
            await env.src.send(w, 4 * NBITS * bp + 10, "CHK-010")
            need = nf0 + i + 1
            await wait_for(dut, lambda: len(env.txmon.frames) >= need, 3 * NBITS * bp,
                           f"CHK-010: txd frame {i} decoded with prescale={p} got none")
        await next_cycle(dut, 2 * bp)
        fr = env.txmon.frames[nf0:]
        assert len(fr) == len(words), f"CHK-010: {len(words)} txd frames with prescale={p} got {len(fr)}"
        for j, (f, w) in enumerate(zip(fr, words)):
            assert f["bp"] == bp
            check_tx_frame("CHK-010", env, f, w, timing=True)
            if j + 1 < len(fr):
                d = fr[j + 1]["t0"] - f["t0"]
                assert d >= NBITS * bp - 1, (
                    f"CHK-010: stop bit ends at {NBITS * bp}+-1 (prescale={p}) got next start at {d}")
                if d > NBITS * bp + 1:
                    unverifiable_k10.append((p, j, d))
        # (b) RX at the same bit period
        for w in words:
            await env.line.send(w, bp)
            await next_cycle(dut, 4)
        await wait_for(dut, lambda: len(env.sink.handshakes) >= nh0 + len(words), 4 * bp,
                       f"CHK-010: {len(words)} m_axis transfers with prescale={p}")
        await next_cycle(dut, 2 * bp)
        got = env.sink.data()[nh0:]
        assert got == words, (f"CHK-010: rx words {[hx(w) for w in words]} with prescale={p} "
                              f"got {[hx(g) for g in got]}")
    ov = env.trace.pulses("rx_overrun_error")
    fe = env.trace.pulses("rx_frame_error")
    assert not ov, f"CHK-010: rx_overrun_error=0 throughout got pulses at {ov}"
    assert not fe, f"CHK-010: rx_frame_error=0 throughout got pulses at {fe}"
    if unverifiable_k10:
        not_verifiable(dut, "CHK-010",
                       "end-of-stop-bit boundary (k=10) upper bound: the DUT did not start the next "
                       "frame right after the stop bit, and a longer stop bit is indistinguishable "
                       f"from idle on txd (cases {unverifiable_k10}); lower bound was checked")


@cocotb.test()
async def test_chk_011_tx_busy(dut):
    """CHK-011: tx_busy is high while a transmission is in progress and low when idle."""
    env = Env(dut, "chk011")
    await env.start(prescale=2, sink_mode="on")
    bp = 16
    ts = env.t_start
    await next_cycle(dut, 200)
    env.trace.expect("CHK-011", "tx_busy", ts, ts + 199, lambda v: v == 0,
                     "tx_busy=0 during initial idle")
    await env.src.send(0x00, 4 * NBITS * bp, "CHK-011")
    await next_cycle(dut, 400)
    w1, w2 = 0x5A & MASK, 0xC3 & MASK
    await env.src.send(w1, 4 * NBITS * bp, "CHK-011")
    await env.src.send(w2, 4 * NBITS * bp, "CHK-011")
    await wait_for(dut, lambda: len(env.txmon.frames) >= 3, 3 * NBITS * bp,
                   f"CHK-011: 3 txd frames got {len(env.txmon.frames)}")
    await next_cycle(dut, NBITS * bp + 100)
    tend = env.cyc.n - 1

    fr = env.txmon.frames
    assert len(fr) == 3, f"CHK-011: 3 frames on txd got {len(fr)}"
    for f, w in zip(fr, (0x00, w1, w2)):
        assert f["word"] == w, f"CHK-011: txd frame decodes to {hx(w)} got {hx(f['word'])}"
        env.trace.expect("CHK-011", "tx_busy", f["t0"], f["t0"] + NBITS * bp - 2,
                         lambda v: v == 1, f"tx_busy=1 during frame {hx(w)}")
    a, b = fr[1]["t0"], fr[2]["t0"] + NBITS * bp - 2
    lows = env.trace.count("tx_busy", a, b, lambda v: v != 1)
    assert lows <= 1, f"CHK-011: tx_busy=1 across back-to-back frames (<=1 low cycle) got {lows} low cycles"
    a = fr[2]["t0"] + NBITS * bp + 1 + bp
    env.trace.expect("CHK-011", "tx_busy", a, tend, lambda v: v == 0, "tx_busy=0 after last frame")
    env.trace.expect("CHK-011", "txd", a, tend, lambda v: v == 1, "txd=1 after last frame")


async def _tx_traffic(env, r, bp, n, state, model):
    for _ in range(n):
        g = r.choice([0, 0, r.randint(1, 3 * bp), r.randint(0, 15 * bp)])
        if g:
            await next_cycle(env.dut, g)
        w = r.randrange(1 << DW)
        await env.src.send(w, 4 * NBITS * bp + 10, "CHK-009")
        model.tx_accept(w)
    state["done"] = True


@cocotb.test()
async def test_regression_random(dut):
    """CHK-001, CHK-002, CHK-003, CHK-004 (with CHK-005..CHK-011 scoreboard): random concurrent
    TX and RX traffic, random back pressure, overrun and frame-error episodes, several prescales."""
    env = Env(dut, "regression")
    rr = rng("regression_rx")
    tr = rng("regression_tx")
    await env.start(prescale=2, sink_mode="random", p_ready=0.5, max_wait=16)
    model = UartRefModel()
    fe_frames, ov_frames = [], []
    for p in (2, 1, 4, 3):
        await env.set_prescale(p, "CHK-010")
        bp = 8 * p
        env.sink.mode = "random"
        env.sink.p_ready = rr.choice([0.2, 0.5, 0.8, 1.0])
        env.sink.max_wait = 2 * bp
        state = {"done": False}
        cocotb.start_soon(_tx_traffic(env, tr, bp, 30, state, model))
        kinds = ["ok"] * 26 + ["fe", "fe", "ov", "ov"]
        rr.shuffle(kinds)
        for kind in kinds:
            g = rr.randint(0, 2 * bp)
            if g:
                await next_cycle(dut, g)
            w = rr.randrange(1 << DW)
            if kind == "ok":
                await env.line.send(w, bp)
                model.rx_good(w, pending=False)
            elif kind == "fe":
                t0 = await env.line.send(w, bp, stop=0)
                fe_frames.append((t0, bp))
                model.rx_bad_stop(w)
                await next_cycle(dut, 3 * bp)
            else:
                await wait_for(dut, lambda: len(env.sink.handshakes) >= len(model.rx_expected)
                               and val(dut.m_axis_tvalid) == 0, 4 * NBITS * bp,
                               "CHK-005: all previous words delivered before overrun episode")
                env.sink.mode = "off"
                await env.line.send(w, bp)
                model.rx_good(w, pending=False)
                g2 = rr.randint(0, bp)
                if g2:
                    await next_cycle(dut, g2)
                w2 = rr.randrange(1 << DW)
                t0 = await env.line.send(w2, bp)
                ov_frames.append((t0, bp))
                model.rx_good(w2, pending=True)
                await next_cycle(dut, 2 * bp)
                env.sink.mode = "random"
        await wait_for(dut, lambda: state["done"], 40 * NBITS * bp,
                       "CHK-009: TX traffic finished got still running")
        await wait_for(dut, lambda: len(env.txmon.frames) >= len(env.src.handshakes),
                       3 * NBITS * bp, "CHK-009: one txd frame per handshake")
        await wait_for(dut, lambda: len(env.sink.handshakes) >= len(model.rx_expected),
                       4 * NBITS * bp, "CHK-005: all expected words delivered on m_axis")
        await next_cycle(dut, 2 * bp)

    # TX scoreboard
    hs = [w for _, w in env.src.handshakes]
    assert hs == model.tx_expected, "CHK-009: source handshakes match accepted words"
    dec = env.txmon.words()
    assert dec == hs, f"CHK-009: txd words equal handshake words ({len(hs)}) got {len(dec)} frames"
    for f, w in zip(env.txmon.frames, hs):
        check_tx_frame("CHK-010", env, f, w, timing=True)
    # RX scoreboard
    got = env.sink.data()
    assert got == model.rx_expected, (f"CHK-005: m_axis words equal reference ({len(model.rx_expected)}) "
                                      f"got {len(got)}")
    fe = env.trace.pulses("rx_frame_error")
    assert len(fe) == model.n_frame_err, f"CHK-008: {model.n_frame_err} frame_error pulses got {len(fe)}"
    for t in fe:
        assert any(mid_stop(t0, b) <= t <= frame_end(t0, b) + 2 * b for t0, b in fe_frames), (
            f"CHK-008: rx_frame_error pulse inside a bad-stop window got pulse at {t}")
    ov = env.trace.pulses("rx_overrun_error")
    assert len(ov) == model.n_overrun, f"CHK-007: {model.n_overrun} overrun pulses got {len(ov)}"
    for t in ov:
        assert any(mid_stop(t0, b) <= t <= frame_end(t0, b) + 2 * b for t0, b in ov_frames), (
            f"CHK-007: rx_overrun_error pulse inside an overrun-frame window got pulse at {t}")
    # assertion checks were exercised
    assert env.sink.stall_cycles > 0, "CHK-001: back pressure stalls exercised got 0"
    assert env.trace.ovr > 0, "CHK-002: rx_overrun_error pulses exercised got 0"
    assert env.trace.fe > 0, "CHK-003: rx_frame_error pulses exercised got 0"
    assert env.trace.txd_low > 0, "CHK-004: txd low cycles exercised got 0"

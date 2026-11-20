"""cocotb testbench for m_axil_regfile (AXI4-Lite register file).

Cycle model: every interaction happens at falling edges of i_clk ("steps").
At step t the testbench reads the outputs (= the values sampled by the next
rising edge, called edge t) and drives the inputs for edge t.  A transfer
happens at edge t when the valid driven at step t and the ready read at step t
are both 1.  hist[t] = outputs read at step t, hin[t] = inputs driven for edge
t.  A value required "from edge e" is therefore visible in hist[e+1].
"""
import cocotb
from cocotb.triggers import FallingEdge, RisingEdge, Timer
from cocotb.utils import get_sim_time

from nnc_cocotb import *  # noqa: F401,F403

M32 = 0xFFFFFFFF
OKAY = 0
SLVERR = 2

IN_NAMES = (
    "i_s_axi_awvalid", "i_s_axi_awaddr", "i_s_axi_awprot",
    "i_s_axi_wvalid", "i_s_axi_wdata", "i_s_axi_wstrb", "i_s_axi_bready",
    "i_s_axi_arvalid", "i_s_axi_araddr", "i_s_axi_arprot", "i_s_axi_rready",
    "i_status",
)
OUT_MAP = {
    "awready": "o_s_axi_awready", "wready": "o_s_axi_wready",
    "bvalid": "o_s_axi_bvalid", "bresp": "o_s_axi_bresp",
    "arready": "o_s_axi_arready", "rvalid": "o_s_axi_rvalid",
    "rdata": "o_s_axi_rdata", "rresp": "o_s_axi_rresp", "regs": "o_regs",
}
VALIDS0 = {"i_s_axi_awvalid": 0, "i_s_axi_wvalid": 0, "i_s_axi_arvalid": 0}


def param(name, default):
    try:
        return int(PARAMS[name])
    except Exception:
        return default


def merge(old, data, strb):
    res = old
    for i in range(4):
        if (strb >> i) & 1:
            m = 0xFF << (8 * i)  # nnc-literal-ok: 8 bits per byte lane
            res = (res & ~m) | (data & m)
    return res & M32


def word(regs, k):
    return (regs >> (32 * k)) & M32


def hx(v):
    return f"0x{v:x}" if isinstance(v, int) and v >= 0 else str(v)


def sig_width(sig):
    try:
        return len(sig)
    except TypeError:
        return len(sig.value)


def check_zero(o, chk, what):
    for k, n in OUT_MAP.items():
        assert o[k] == 0, f"{chk}: {what}: {n}=0 expected, got {hx(o[k])}"


# ----------------------------------------------------------------------------
# Manager-side protocol models
# ----------------------------------------------------------------------------
class ChanDriver:
    """Request channel (aw / w / ar). Items = [(delay, payload)]; each item is
    presented after `delay` idle cycles counted from the previous transfer of
    this channel; valid and payload stay stable until the transfer."""
    VALID = {"aw": "i_s_axi_awvalid", "w": "i_s_axi_wvalid", "ar": "i_s_axi_arvalid"}

    def __init__(self, env, ch, items, scramble=None):
        self.env, self.ch, self.items = env, ch, list(items)
        self.idx, self.wait, self.active = 0, 0, False
        self.scramble, self.last, self.edges = scramble, None, []

    def done(self):
        return self.idx >= len(self.items)

    def drive(self):
        vname = self.VALID[self.ch]
        if not self.done():
            delay, payload = self.items[self.idx]
            if self.active or self.wait >= delay:
                self.active = True
                self.env.drive(**{vname: 1})
                self.env.drive(**payload)
                return
            self.wait += 1
        self.env.drive(**{vname: 0})
        if self.scramble is not None:
            self.env.drive(**self.scramble(self.last))

    def post(self, tr):
        if tr[self.ch] and not self.done():
            self.edges.append(self.env.t)
            self.last = self.items[self.idx][1]
            self.idx += 1
            self.wait, self.active = 0, False


class ReadyDriver:
    """bready / rready. Policy per response: 'always' (1 before valid), 'never',
    'dep' (= valid), int d (1 from d cycles after valid rose), ('rand', p)."""
    READY = {"b": ("i_s_axi_bready", "bvalid"), "r": ("i_s_axi_rready", "rvalid")}

    def __init__(self, env, ch, policies, rnd=None):
        self.env, self.ch = env, ch
        self.pols = list(policies) if isinstance(policies, list) else [policies]
        self.idx, self.cnt = 0, 0
        self.rnd = rnd if rnd is not None else env.rng

    def done(self):
        return True

    def drive(self):
        rname, vkey = self.READY[self.ch]
        v = self.env.o[vkey]
        if v == 1:
            self.cnt += 1
        p = self.pols[min(self.idx, len(self.pols) - 1)]
        if p == "always":
            r = 1
        elif p == "never":
            r = 0
        elif p == "dep":
            r = 1 if v == 1 else 0
        elif isinstance(p, int):
            r = 1 if (v == 1 and self.cnt - 1 >= p) else 0
        else:
            r = 1 if self.rnd.random() < p[1] else 0
        self.env.drive(**{rname: r})

    def post(self, tr):
        if tr[self.ch]:
            self.idx += 1
            self.cnt = 0


def write_agents(env, writes, bpol="always", scramble=True, rnd=None):
    aw = ChanDriver(env, "aw", [(w.get("awd", 0), {"i_s_axi_awaddr": w["addr"], "i_s_axi_awprot": w.get("prot", 0)})
                                for w in writes], env.scr_aw if scramble else None)
    wd = ChanDriver(env, "w", [(w.get("wd", 0), {"i_s_axi_wdata": w["data"] & M32, "i_s_axi_wstrb": w.get("strb", 0xF)})
                               for w in writes], env.scr_w if scramble else None)
    return [aw, wd, ReadyDriver(env, "b", bpol, rnd)]


def read_agents(env, reads, rpol="always", scramble=True, rnd=None):
    ar = ChanDriver(env, "ar", [(r.get("ard", 0), {"i_s_axi_araddr": r["addr"], "i_s_axi_arprot": r.get("prot", 0)})
                                for r in reads], env.scr_ar if scramble else None)
    return [ar, ReadyDriver(env, "r", rpol, rnd)]


# ----------------------------------------------------------------------------
# Environment: driver of the cycle model + reference model / scoreboard
# ----------------------------------------------------------------------------
class Env:
    def __init__(self, dut, salt):
        self.dut = dut
        self.N = param("PARA_NUM_REGS", 8)
        self.AW = param("PARA_ADDR_W", 8)
        self.AMASK = (1 << self.AW) - 1
        self.NW = 1 << (self.AW - 2)
        self.mapped = [4 * k for k in range(self.N)] + [0x40]
        self.rng = rng(salt)
        self.srng = rng(f"{salt}/scramble")
        self.t = 0
        self.inp = {n: 0 for n in IN_NAMES}
        self.inp["i_rst_n"] = 0
        self.o = {k: 0 for k in OUT_MAP}
        self.hist, self.hin = {}, {}
        self.agents, self.hooks = [], []
        self.wr_recs, self.rd_recs = [], []
        self.R1 = None
        self.period = self.high = None
        self.ctx = "TB"
        self.pred_reset = True
        self.clear_state()

    # -- reference model ------------------------------------------------------
    def clear_state(self):
        self.M = [0] * self.N
        self.aw_held = self.w_held = self.b_pending = False
        self.ar_held = self.r_pending = False
        self.cur_aw = self.cur_w = self.cur_wrec = self.cur_rrec = None
        self.exp_b = self.exp_r = None

    def decode(self, addr):
        w = (addr & self.AMASK) >> 2
        if w < self.N:
            return "reg", w
        if w == 16:
            return "status", None
        return "unmapped", None

    def regs_val(self):
        v = 0
        for k, x in enumerate(self.M):
            v |= x << (32 * k)
        return v

    # -- signal access --------------------------------------------------------
    def drive(self, **kw):
        for n, v in kw.items():
            v = int(v)
            self.inp[n] = v
            getattr(self.dut, n).value = v

    def read_outs(self):
        r = {}
        for k, n in OUT_MAP.items():
            v = val(getattr(self.dut, n))
            r[k] = -1 if v is None else v
        return r

    def sample(self):
        self.o = self.read_outs()
        self.hist[self.t] = self.o

    def msg(self, chk, text):
        return f"{chk}: [{self.ctx} step {self.t}] {text}"

    # -- scramblers for payloads that are not valid ---------------------------
    def scr_aw(self, last):
        excl = None if last is None else (last["i_s_axi_awaddr"] & self.AMASK & ~3)
        ch = [a for a in self.mapped if a != excl] or self.mapped
        return {"i_s_axi_awaddr": self.srng.choice(ch), "i_s_axi_awprot": 0}

    def scr_ar(self, last):
        excl = None if last is None else (last["i_s_axi_araddr"] & self.AMASK & ~3)
        ch = [a for a in self.mapped if a != excl] or self.mapped
        return {"i_s_axi_araddr": self.srng.choice(ch), "i_s_axi_arprot": 0}

    def scr_w(self, last):
        d, s = self.srng.getrandbits(32), self.srng.randrange(16)
        if last is not None:
            if d == last["i_s_axi_wdata"]:
                d ^= M32
            if s == last["i_s_axi_wstrb"]:
                s ^= 0xF
        return {"i_s_axi_wdata": d, "i_s_axi_wstrb": s}

    # -- edge commit: transfers and model update ------------------------------
    def commit(self):
        t, i, o = self.t, self.inp, self.o
        self.hin[t] = dict(i)
        tr = {"aw": False, "w": False, "b": False, "ar": False, "r": False, "ec": False}
        if i["i_rst_n"] == 0:
            self.clear_state()
            self.pred_reset = True
            return tr
        if self.pred_reset:
            self.R1 = t
        self.pred_reset = False
        tr["aw"] = i["i_s_axi_awvalid"] == 1 and o["awready"] == 1
        tr["w"] = i["i_s_axi_wvalid"] == 1 and o["wready"] == 1
        tr["b"] = i["i_s_axi_bready"] == 1 and o["bvalid"] == 1
        tr["ar"] = i["i_s_axi_arvalid"] == 1 and o["arready"] == 1
        tr["r"] = i["i_s_axi_rready"] == 1 and o["rvalid"] == 1
        if tr["b"]:
            if self.cur_wrec is not None:
                self.cur_wrec["Eb"], self.cur_wrec["bresp"] = t, o["bresp"]
            self.aw_held = self.w_held = self.b_pending = False
            self.cur_aw = self.cur_w = self.cur_wrec = None
        if tr["r"]:
            if self.cur_rrec is not None:
                self.cur_rrec.update(Er=t, rdata=o["rdata"], rresp=o["rresp"])
            self.ar_held = self.r_pending = False
            self.cur_rrec = None
        if tr["ar"]:
            addr = i["i_s_axi_araddr"]
            kind, k = self.decode(addr)
            if kind == "reg":
                exp = (self.M[k], OKAY)
            elif kind == "status":
                exp = (i["i_status"] & M32, OKAY)
            else:
                exp = (0, SLVERR)
            self.exp_r = exp
            self.ar_held = self.r_pending = True
            rec = {"Ear": t, "addr": addr, "kind": kind, "k": k, "exp_data": exp[0], "exp_resp": exp[1]}
            self.rd_recs.append(rec)
            self.cur_rrec = rec
        if tr["aw"]:
            self.aw_held, self.cur_aw = True, (t, i["i_s_axi_awaddr"])
        if tr["w"]:
            self.w_held, self.cur_w = True, (t, i["i_s_axi_wdata"], i["i_s_axi_wstrb"])
        if (tr["aw"] or tr["w"]) and self.aw_held and self.w_held and not self.b_pending:
            ea, addr = self.cur_aw
            ew, data, strb = self.cur_w
            kind, k = self.decode(addr)
            if kind == "reg":
                self.M[k] = merge(self.M[k], data, strb)
            self.exp_b = SLVERR if kind == "unmapped" else OKAY
            self.b_pending = True
            rec = {"Ea": ea, "Ew": ew, "Ec": t, "addr": addr, "data": data, "strb": strb,
                   "kind": kind, "k": k, "exp_bresp": self.exp_b}
            self.wr_recs.append(rec)
            self.cur_wrec = rec
            tr["ec"] = True
        return tr

    # -- per-cycle output check against the model ------------------------------
    def check(self):
        o = self.o
        if self.pred_reset:
            for k in ("awready", "wready", "arready", "bvalid", "rvalid"):
                assert o[k] == 0, self.msg("CHK-013", f"{OUT_MAP[k]}=0 in/at end of reset, got {o[k]}")
            for k in ("bresp", "rresp", "rdata", "regs"):
                assert o[k] == 0, self.msg("CHK-014", f"{OUT_MAP[k]}=0 in reset, got {hx(o[k])}")
            return
        e = 0 if self.aw_held else 1
        assert o["awready"] == e, self.msg("CHK-006", f"o_s_axi_awready={e} expected got {o['awready']}")
        e = 0 if self.w_held else 1
        assert o["wready"] == e, self.msg("CHK-007", f"o_s_axi_wready={e} expected got {o['wready']}")
        e = 0 if self.ar_held else 1
        assert o["arready"] == e, self.msg("CHK-001", f"o_s_axi_arready={e} expected got {o['arready']}")
        assert o["bvalid"] == int(self.b_pending), self.msg("CHK-008", f"o_s_axi_bvalid={int(self.b_pending)} expected got {o['bvalid']}")
        assert o["rvalid"] == int(self.r_pending), self.msg("CHK-002", f"o_s_axi_rvalid={int(self.r_pending)} expected got {o['rvalid']}")
        if o["bvalid"] == 1:
            assert o["bresp"] in (0, 2), self.msg("CHK-010", f"bresp OKAY/SLVERR expected got {o['bresp']}")
            assert o["bresp"] == self.exp_b, self.msg("CHK-011", f"bresp={self.exp_b} expected got {o['bresp']}")
        if o["rvalid"] == 1:
            assert o["rresp"] in (0, 2), self.msg("CHK-004", f"rresp OKAY/SLVERR expected got {o['rresp']}")
            assert (o["rdata"], o["rresp"]) == self.exp_r, self.msg(
                "CHK-005", f"rdata/rresp={hx(self.exp_r[0])}/{self.exp_r[1]} expected got {hx(o['rdata'])}/{o['rresp']}")
        er = self.regs_val()
        assert o["regs"] == er, self.msg("CHK-012", f"o_regs={hx(er)} expected got {hx(o['regs'])}")

    # -- stepping --------------------------------------------------------------
    def start(self, *groups):
        ag = []
        for g in groups:
            if isinstance(g, (list, tuple)):
                ag.extend(g)
            else:
                ag.append(g)
        self.agents = ag

    def idle(self):
        return all(a.done() for a in self.agents) and not (
            self.aw_held or self.w_held or self.b_pending or self.ar_held or self.r_pending)

    def quiesce(self):
        self.drive(**VALIDS0)

    async def tick(self, n=1):
        for _ in range(n):
            for a in self.agents:
                a.drive()
            for h in self.hooks:
                h(self)
            tr = self.commit()
            for a in self.agents:
                a.post(tr)
            await next_cycle(self.dut)
            self.t += 1
            self.sample()
            self.check()

    async def run(self, max_cycles, what):
        for _ in range(max_cycles):
            if self.idle():
                break
            await self.tick()
        assert self.idle(), f"{self.ctx}: {what} expected to complete within {max_cycles} cycles, got timeout"
        self.quiesce()

    async def write(self, addr, data, strb=0xF, prot=0, awd=0, wd=0, bpol="always", max_cycles=200):
        n0 = len(self.wr_recs)
        self.start(write_agents(self, [dict(addr=addr, data=data, strb=strb, prot=prot, awd=awd, wd=wd)], bpol))
        await self.run(max_cycles, f"write to {hx(addr)}")
        return self.wr_recs[n0]

    async def read(self, addr, prot=0, ard=0, rpol="always", max_cycles=200):
        n0 = len(self.rd_recs)
        self.start(read_agents(self, [dict(addr=addr, prot=prot, ard=ard)], rpol))
        await self.run(max_cycles, f"read of {hx(addr)}")
        return self.rd_recs[n0]

    # -- clock / reset ---------------------------------------------------------
    async def measure_clock(self):
        clk = self.dut.i_clk
        await RisingEdge(clk)
        t0 = get_sim_time("step")
        await FallingEdge(clk)
        t1 = get_sim_time("step")
        await RisingEdge(clk)
        t2 = get_sim_time("step")
        self.period, self.high = int(t2 - t0), int(t1 - t0)

    async def reset(self, cycles=3, **overrides):
        """Assert reset now, hold >= `cycles` rising edges, release shortly after a
        rising edge. Returns at the falling edge before R1 (R1 = edge self.t)."""
        self.agents = []
        vals = {n: 0 for n in IN_NAMES}
        vals["i_status"] = self.inp["i_status"]
        vals.update(overrides)
        self.drive(i_rst_n=0, **vals)
        self.clear_state()
        self.pred_reset = True
        if self.period is None:
            await self.measure_clock()
        await next_cycle(self.dut)
        self.t += 1
        self.sample()
        self.check()
        for _ in range(max(0, cycles - 1)):
            await self.tick()
        await self.release()

    async def release(self):
        self.commit()  # edge with i_rst_n=0
        await RisingEdge(self.dut.i_clk)
        await Timer(1, "step")
        self.drive(i_rst_n=1)
        await FallingEdge(self.dut.i_clk)
        self.t += 1
        self.sample()
        self.check()

    async def hold_release(self, cycles=2):
        for _ in range(max(0, cycles - 1)):
            await self.tick()
        await self.release()

    async def mid_reset(self, frac, chk="CHK-034"):
        """Drive the current step, then assert i_rst_n=0 at frac*period after the
        next rising edge; check the reset values before the following edge."""
        for a in self.agents:
            a.drive()
        for h in self.hooks:
            h(self)
        tr = self.commit()
        for a in self.agents:
            a.post(tr)
        self.agents = []
        clk = self.dut.i_clk
        await RisingEdge(clk)
        off = max(1, int(self.period * frac))
        crossed = off >= self.high
        if crossed:
            await FallingEdge(clk)
            self.t += 1
            self.sample()
            self.check()
            if off - self.high > 0:
                await Timer(off - self.high, "step")
        else:
            await Timer(off, "step")
        before = self.read_outs()
        self.drive(i_rst_n=0)
        await Timer(1, "step")
        after = self.read_outs()
        check_zero(after, chk, f"right after asynchronous i_rst_n 1->0 at {frac} period after a rising edge")
        if crossed:
            self.commit()
        else:
            self.clear_state()
            self.pred_reset = True
        await FallingEdge(clk)
        self.t += 1
        self.sample()
        self.check()
        self.drive(i_s_axi_bready=0, i_s_axi_rready=0, **VALIDS0)
        return before, after

    async def tick_toggle(self, pa, pb, chk="CHK-037"):
        """Inputs pa right after the falling edge, pb at 3/4 period; outputs must not
        change between rising edges (sampled after each change, before the next
        rising edge, and over the high phase)."""
        clk = self.dut.i_clk
        ref = dict(self.o)
        low = self.period - self.high
        off = max(2, (3 * self.period) // 4 - self.high)
        if off + 2 >= low:
            off = max(2, low // 2)
        for a in self.agents:
            a.drive()
        self.drive(**pa)
        await Timer(1, "step")
        o1 = self.read_outs()
        assert o1 == ref, self.msg(chk, f"no output change after input change at falling edge: {ref} got {o1}")
        await Timer(off - 1, "step")
        self.drive(**pb)
        await Timer(1, "step")
        o2 = self.read_outs()
        assert o2 == ref, self.msg(chk, f"no output change after input change at 3/4 period: {ref} got {o2}")
        rem = low - off - 2
        if rem > 0:
            await Timer(rem, "step")
        o3 = self.read_outs()
        assert o3 == ref, self.msg(chk, f"no output change before rising edge: {ref} got {o3}")
        tr = self.commit()
        for a in self.agents:
            a.post(tr)
        await RisingEdge(clk)
        await Timer(1, "step")
        o4 = self.read_outs()
        await FallingEdge(clk)
        self.t += 1
        self.sample()
        assert self.o == o4, self.msg(chk, f"no output change in high phase: {o4} got {self.o}")
        self.check()


async def setup(dut, salt, ctx, status=0):
    start_clock(dut)
    env = Env(dut, salt)
    env.ctx = ctx
    env.inp["i_status"] = status
    await env.reset(3)
    await env.tick()  # edge R1, idle
    return env


def gen_traffic(env, r, nw, nr, delays=(0, 0, 0, 1, 2, 4)):
    mapped_w = list(range(env.N)) + [16]
    unm_w = list(range(env.N, 16)) + list(range(17, 32))

    def pick():
        x = r.random()
        if x < 0.7:
            return r.choice(mapped_w)
        if x < 0.9 or env.NW <= 32:
            return r.choice(unm_w)
        return r.randrange(32, env.NW)
    writes = []
    for _ in range(nw):
        strb = 0xF if r.random() < 0.5 else r.randrange(16)
        writes.append(dict(word=pick(), data=r.getrandbits(32), strb=strb, awd=r.choice(delays),
                           wd=r.choice(delays), lo=r.randrange(4), prot=r.randrange(8)))  # nnc-literal-ok: 3-bit AxPROT has 8 values
    reads = [dict(word=pick(), ard=r.choice(delays), lo=r.randrange(4), prot=r.randrange(8)) for _ in range(nr)]  # nnc-literal-ok: 3-bit AxPROT has 8 values
    pols = ["always", "dep", 0, 1, 2, 5, ("rand", 0.5)]
    return writes, reads, [r.choice(pols) for _ in range(nw)], [r.choice(pols) for _ in range(nr)]


def to_items(writes, reads, use_lo):
    W = [dict(addr=(x["word"] << 2) | (x["lo"] if use_lo else 0), data=x["data"], strb=x["strb"],
              prot=x["prot"] if use_lo else 0, awd=x["awd"], wd=x["wd"]) for x in writes]
    R = [dict(addr=(x["word"] << 2) | (x["lo"] if use_lo else 0), prot=x["prot"] if use_lo else 0,
              ard=x["ard"]) for x in reads]
    return W, R


# ----------------------------------------------------------------------------
# Tests (CHK-033 first so that it starts at simulation time zero)
# ----------------------------------------------------------------------------
@cocotb.test()
async def test_chk_033_power_on_reset(dut):
    """CHK-033: reset from time zero, reset values, readies from R1, idle response channels after release."""
    at_zero = get_sim_time("step") == 0
    env = Env(dut, "chk033")
    env.ctx = "CHK-033"
    init = {n: 0 for n in IN_NAMES}
    init["i_status"] = 0x12345678
    env.drive(i_rst_n=0, **init)
    start_clock(dut)
    await env.measure_clock()  # 2 rising edges in reset
    await next_cycle(dut)
    env.t += 1
    env.sample()
    check_zero(env.o, "CHK-033", "while i_rst_n=0")
    env.check()
    await env.release()  # 3rd rising edge in reset, release shortly after it
    R1 = env.t
    check_zero(env.hist[R1], "CHK-033", "values sampled at R1")
    env.drive(i_s_axi_bready=1, i_s_axi_rready=1)
    for i in range(1, 6):
        await env.tick()
        o = env.o
        assert (o["awready"], o["wready"], o["arready"]) == (1, 1, 1), \
            f"CHK-033: readies 1 at R1+{i} got {(o['awready'], o['wready'], o['arready'])}"
        assert o["bvalid"] == 0 and o["rvalid"] == 0, f"CHK-033: bvalid=rvalid=0 at R1+{i} got {o['bvalid']},{o['rvalid']}"
        assert o["regs"] == 0, f"CHK-033: o_regs=0 after reset got {hx(o['regs'])}"
    for a, exp in [(4 * k, 0) for k in range(env.N)] + [(0x40, 0x12345678)]:
        rec = await env.read(a)
        h = env.hist[rec["Ear"] + 1]
        assert h["rvalid"] == 1 and h["rdata"] == exp and h["rresp"] == OKAY, \
            f"CHK-033: read {hx(a)}: rvalid=1 rdata={hx(exp)} rresp=0 at Ear+1 got {h['rvalid']} {hx(h['rdata'])} {h['rresp']}"
    if not at_zero:
        not_verifiable(dut, "CHK-033", "test did not start at simulation time zero; reset-from-time-zero part not observable")


@cocotb.test()
async def test_chk_018_r_backpressure(dut):
    """CHK-018: R back-pressure (rready delay 0/1/6/dependent), data held, new AR blocked until Er+1."""
    env = await setup(dut, "chk018", "CHK-018", status=0x18181818)
    k = 1 if env.N > 1 else 0
    addr = 4 * k
    for ci, pol in enumerate(["always", 1, 6, "dep"]):
        old = (0x18A00000 + 0x01010101 * (ci + 1)) & M32
        new = (~old) & M32
        await env.write(addr, old)
        s, nr, nw = env.t, len(env.rd_recs), len(env.wr_recs)
        env.start(read_agents(env, [dict(addr=addr), dict(addr=0x40)], [pol, "always"]),
                  write_agents(env, [dict(addr=addr, data=new, awd=1, wd=1)], "always"))
        await env.run(100, f"case {pol}")
        r1, r2, w = env.rd_recs[nr], env.rd_recs[nr + 1], env.wr_recs[nw]
        ear, er = r1["Ear"], r1["Er"]
        exp_er = ear + 1 + (pol if isinstance(pol, int) else 0)
        assert ear == s, f"CHK-018: [{pol}] AR at {s} got {ear}"
        assert er == exp_er, f"CHK-018: [{pol}] Er={exp_er} got {er}"
        assert w["Ec"] == s + 1, f"CHK-018: [{pol}] write Ec={s + 1} got {w['Ec']}"
        assert word(env.hist[w["Ec"] + 1]["regs"], k) == new, f"CHK-018: [{pol}] register written during hold-back"
        for e in range(ear + 1, er + 1):
            h = env.hist[e]
            assert h["rvalid"] == 1 and h["rdata"] == old and h["rresp"] == OKAY, \
                f"CHK-018: [{pol}] edge {e}: rvalid=1 rdata={hx(old)} (value at Ear) got {h['rvalid']} {hx(h['rdata'])} {h['rresp']}"
            assert h["arready"] == 0, f"CHK-018: [{pol}] arready=0 at edge {e}<=Er got 1"
            assert env.hin[e]["i_s_axi_arvalid"] == 1, f"CHK-018: [{pol}] new AR presented at edge {e}"
        assert r2["Ear"] == er + 1, f"CHK-018: [{pol}] new AR at Er+1={er + 1} got {r2['Ear']}"
        assert env.hist[er + 2]["rvalid"] == 1, f"CHK-018: [{pol}] rvalid=1 at Er+2 got 0"


@cocotb.test()
async def test_chk_019_write_ordering(dut):
    """CHK-019: AW first, W first and same-edge write ordering; answer one cycle after the later transfer."""
    env = await setup(dut, "chk019", "CHK-019")
    for ci, (awd, wd) in enumerate([(0, 1), (0, 5), (1, 0), (5, 0), (0, 0)]):
        k = ci % env.N
        data = (0x19C30000 + 0x0101 * ci + 1) & M32
        if data == env.M[k]:
            data ^= 0xFF
        pre = env.M[k]
        s, nw = env.t, len(env.wr_recs)
        env.start(write_agents(env, [dict(addr=4 * k, data=data, awd=awd, wd=wd)], "always"))
        await env.run(50, f"case {ci}")
        await env.tick(2)
        rec = env.wr_recs[nw]
        ea, ew = s + awd, s + wd
        ec = max(ea, ew)
        tag = f"case AW+{awd}/W+{wd}"
        assert (rec["Ea"], rec["Ew"], rec["Ec"]) == (ea, ew, ec), f"CHK-019: {tag}: Ea,Ew,Ec={(ea, ew, ec)} got {(rec['Ea'], rec['Ew'], rec['Ec'])}"
        assert rec["Eb"] == ec + 1 and rec["bresp"] == OKAY, f"CHK-019: {tag}: Eb=Ec+1 bresp=0 got {rec.get('Eb')} {rec.get('bresp')}"
        for e in range(s, ec + 1):
            assert env.hist[e]["bvalid"] == 0, f"CHK-019: {tag}: bvalid=0 at edge {e}<=Ec got 1"
        assert env.hist[ec + 1]["bvalid"] == 1, f"CHK-019: {tag}: bvalid=1 at Ec+1 got 0"
        if ea != ew:
            first, other = ("awready", "wready") if ea < ew else ("wready", "awready")
            for e in range(min(ea, ew) + 1, rec["Eb"] + 1):
                assert env.hist[e][first] == 0, f"CHK-019: {tag}: {first}=0 at edge {e} got 1"
            for e in range(s, max(ea, ew) + 1):
                assert env.hist[e][other] == 1, f"CHK-019: {tag}: {other}=1 until its transfer, edge {e} got 0"
            if ea < ew:
                assert any(env.hin[e]["i_s_axi_awaddr"] != 4 * k for e in range(ea + 1, ew + 1)), f"CHK-019: {tag}: awaddr changed after AW transfer"
            else:
                assert any(env.hin[e]["i_s_axi_wdata"] != data for e in range(ew + 1, ea + 1)), f"CHK-019: {tag}: wdata changed after W transfer"
        h = env.hist[ec + 2]
        assert h["awready"] == 1 and h["wready"] == 1, f"CHK-019: {tag}: readies 1 at Ec+2 got {h['awready']},{h['wready']}"
        for e in range(s, ec + 1):
            assert word(env.hist[e]["regs"], k) == pre, f"CHK-019: {tag}: REG_{k} unchanged at edge {e}<=Ec"
        for e in range(ec + 1, env.t + 1):
            assert word(env.hist[e]["regs"], k) == data, f"CHK-019: {tag}: REG_{k}={hx(data)} from Ec+1 got {hx(word(env.hist[e]['regs'], k))}"


@cocotb.test()
async def test_chk_020_b_backpressure(dut):
    """CHK-020: B back-pressure (bready delay 0/1/6/dependent); new AW/W blocked until Eb+1."""
    env = await setup(dut, "chk020", "CHK-020")
    k1, k2 = 0, 1 % env.N
    for ci, pol in enumerate(["always", 1, 6, "dep"]):
        d1, d2 = (0x20000000 + 0x111 * (ci + 1)) & M32, (0x2A000000 + 0x222 * (ci + 1)) & M32
        s, nw = env.t, len(env.wr_recs)
        env.start(write_agents(env, [dict(addr=4 * k1, data=d1), dict(addr=4 * k2, data=d2)], [pol, "always"]))
        await env.run(100, f"case {pol}")
        await env.tick(2)
        w1, w2 = env.wr_recs[nw], env.wr_recs[nw + 1]
        ec, eb = w1["Ec"], w1["Eb"]
        exp_eb = ec + 1 + (pol if isinstance(pol, int) else 0)
        assert ec == s, f"CHK-020: [{pol}] Ec={s} got {ec}"
        assert eb == exp_eb, f"CHK-020: [{pol}] Eb={exp_eb} got {eb}"
        r0 = env.hist[ec + 1]["regs"]
        for e in range(ec + 1, eb + 1):
            h = env.hist[e]
            assert h["bvalid"] == 1 and h["bresp"] == OKAY, f"CHK-020: [{pol}] bvalid=1 bresp=0 at edge {e} got {h['bvalid']} {h['bresp']}"
            assert h["awready"] == 0 and h["wready"] == 0, f"CHK-020: [{pol}] awready=wready=0 at edge {e}<=Eb"
            assert env.hin[e]["i_s_axi_awvalid"] == 1 and env.hin[e]["i_s_axi_wvalid"] == 1, f"CHK-020: [{pol}] new AW/W presented at {e}"
        for e in range(ec + 1, eb + 2):
            assert env.hist[e]["regs"] == r0, f"CHK-020: [{pol}] o_regs unchanged during hold-back at edge {e}"
        assert w2["Ea"] == eb + 1 and w2["Ew"] == eb + 1, f"CHK-020: [{pol}] new AW/W at Eb+1={eb + 1} got {w2['Ea']},{w2['Ew']}"
        assert word(env.hist[eb + 2]["regs"], k2) == d2, f"CHK-020: [{pol}] new value from Eb+2"
        assert word(env.hist[eb + 1]["regs"], k2) != d2, f"CHK-020: [{pol}] new value not before Eb+2"


@cocotb.test()
async def test_chk_021_cfg_min_map(dut):
    """CHK-021: CFG-MIN map: REG_0 and STATUS only, 0x00-0x7F."""
    env = await setup(dut, "chk021", "CHK-021", status=0x21C0FFEE)
    if not (env.N == 1 and env.AW == 7):
        not_verifiable(dut, "CHK-021", f"CFG-MIN only; this run has PARA_NUM_REGS={env.N}, PARA_ADDR_W={env.AW}")
        return
    assert sig_width(dut.o_regs) == 32, f"CHK-021: o_regs 32 bits got {sig_width(dut.o_regs)}"
    for w in list(range(1, 32)) + [0]:
        a, regs0 = 4 * w, env.o["regs"]
        wr = await env.write(a, M32)
        rd = await env.read(a)
        if w == 0:
            assert wr["bresp"] == OKAY and env.o["regs"] == M32, f"CHK-021: 0x00 write OKAY, REG_0=0xffffffff got {wr['bresp']} {hx(env.o['regs'])}"
            assert (rd["rdata"], rd["rresp"]) == (M32, OKAY), f"CHK-021: 0x00 read got {hx(rd['rdata'])} {rd['rresp']}"
        elif w == 16:
            assert wr["bresp"] == OKAY and env.o["regs"] == regs0, f"CHK-021: 0x40 write OKAY, no change got {wr['bresp']}"
            assert (rd["rdata"], rd["rresp"]) == (0x21C0FFEE, OKAY), f"CHK-021: 0x40 read returns i_status got {hx(rd['rdata'])}"
        else:
            assert wr["bresp"] == SLVERR and env.o["regs"] == regs0, f"CHK-021: {hx(a)} write SLVERR, no change got {wr['bresp']}"
            assert (rd["rdata"], rd["rresp"]) == (0, SLVERR), f"CHK-021: {hx(a)} read 0/SLVERR got {hx(rd['rdata'])} {rd['rresp']}"
    nr = len(env.rd_recs)
    env.start(read_agents(env, [dict(addr=4 * w) for w in range(32)]))
    await env.run(200, "sweep")
    for w, rec in enumerate(env.rd_recs[nr:]):
        exp = (M32, OKAY) if w == 0 else (0x21C0FFEE, OKAY) if w == 16 else (0, SLVERR)
        assert (rec["rdata"], rec["rresp"]) == exp, f"CHK-021: read {hx(4 * w)} {exp} got {(rec['rdata'], rec['rresp'])}"


@cocotb.test()
async def test_chk_022_full_bank_map(dut):
    """CHK-022: PARA_NUM_REGS=16 map (CFG-FULL-A7, also CFG-MAX): no unmapped address below 0x44."""
    env = await setup(dut, "chk022", "CHK-022", status=0x22446688)
    if env.N != 16:
        not_verifiable(dut, "CHK-022", f"needs PARA_NUM_REGS=16; this run has {env.N}")
        return
    assert sig_width(dut.o_regs) == 512, f"CHK-022: o_regs 512 bits got {sig_width(dut.o_regs)}"
    vals = [(0x22000000 | (k << 16) | (k << 4) | (0xF - k)) & M32 for k in range(16)]
    for k in range(16):
        await env.write(4 * k, vals[k])
    for k in range(16):
        assert word(env.o["regs"], k) == vals[k], f"CHK-022: o_regs word {k}={hx(vals[k])} got {hx(word(env.o['regs'], k))}"
    nr = len(env.rd_recs)
    env.start(read_agents(env, [dict(addr=4 * w) for w in range(32)]))
    await env.run(200, "sweep")
    ok = 0
    for w, rec in enumerate(env.rd_recs[nr:]):
        exp = (vals[w], OKAY) if w < 16 else (0x22446688, OKAY) if w == 16 else (0, SLVERR)
        assert (rec["rdata"], rec["rresp"]) == exp, f"CHK-022: read {hx(4 * w)} {exp} got {(rec['rdata'], rec['rresp'])}"
        ok += rec["rresp"] == OKAY
    assert ok == 17, f"CHK-022: 17 OKAY word indices in 0x00..0x7C got {ok}"


@cocotb.test()
async def test_chk_023_high_bit_decode(dut):
    """CHK-023: PARA_ADDR_W=16: any 1 in bits 15..7 is unmapped (CFG-MAX)."""
    env = await setup(dut, "chk023", "CHK-023", status=0x23232323)
    if not (env.AW == 16 and env.N == 16):
        not_verifiable(dut, "CHK-023", f"CFG-MAX only; this run has PARA_NUM_REGS={env.N}, PARA_ADDR_W={env.AW}")
        return
    vals = [(0x23000000 | (k << 12) | 0x5A0 | k) & M32 for k in range(16)]
    for k in range(16):
        await env.write(4 * k, vals[k])
    addrs = [0x0080, 0x0100, 0x8040, 0xFFFC] + [m | (1 << j) for m in env.mapped for j in range(7, 16)]
    for a in addrs:
        regs0 = env.o["regs"]
        wr = await env.write(a, M32)
        rd = await env.read(a)
        assert wr["bresp"] == SLVERR, f"CHK-023: write {hx(a)} SLVERR got {wr['bresp']}"
        assert (rd["rdata"], rd["rresp"]) == (0, SLVERR), f"CHK-023: read {hx(a)} 0/SLVERR got {hx(rd['rdata'])} {rd['rresp']}"
        assert env.o["regs"] == regs0, f"CHK-023: o_regs unchanged by {hx(a)}"
    for k in range(16):
        rd = await env.read(4 * k)
        assert (rd["rdata"], rd["rresp"]) == (vals[k], OKAY), f"CHK-023: REG_{k}={hx(vals[k])} OKAY got {hx(rd['rdata'])} {rd['rresp']}"


@cocotb.test()
async def test_chk_024_back_to_back(dut):
    """CHK-024: back-to-back writes and reads at full throughput, alone and together."""
    env = await setup(dut, "chk024", "CHK-024", status=0x24242424)
    N, n = env.N, 20
    W = [dict(addr=4 * (i % N), data=(0x24000000 + 0x01010101 * i) & M32) for i in range(n)]
    R = [dict(addr=(4 * (i % N)) if i % 5 else 0x40) for i in range(n)]

    async def do(wr, rd):
        s, nw, nr = env.t, len(env.wr_recs), len(env.rd_recs)
        g = []
        if wr:
            g.append(write_agents(env, W, "always"))
        if rd:
            g.append(read_agents(env, R, "always"))
        env.start(*g)
        await env.run(300, "back-to-back")
        pw = [(x["Ea"] - s, x["Ew"] - s, x["Eb"] - s) for x in env.wr_recs[nw:]]
        pr = [(x["Ear"] - s, x["Er"] - s) for x in env.rd_recs[nr:]]
        return s, pw, pr
    s, pw, _ = await do(True, False)
    assert pw == [(2 * i, 2 * i, 2 * i + 1) for i in range(n)], f"CHK-024: writes AW/W at n+2i, B at n+2i+1 got {pw}"
    assert pw[-1][2] + 1 == 2 * n, f"CHK-024: 20 writes in 40 cycles got {pw[-1][2] + 1}"
    for e in range(s, s + 2 * n):
        exp = 1 - (e - s) % 2
        h = env.hist[e]
        assert h["awready"] == exp and h["wready"] == exp, f"CHK-024: awready/wready alternate, edge {e} expected {exp}"
    s, _, pr = await do(False, True)
    assert pr == [(2 * i, 2 * i + 1) for i in range(n)], f"CHK-024: reads AR at m+2i, R at m+2i+1 got {pr}"
    _, pw2, pr2 = await do(True, True)
    assert pw2 == pw, f"CHK-024: write timing with concurrent reads {pw} got {pw2}"
    assert pr2 == pr, f"CHK-024: read timing with concurrent writes {pr} got {pr2}"


@cocotb.test()
async def test_chk_025_concurrent_same_register(dut):
    """CHK-025: read of register k with Ear = Ec-1, Ec, Ec+1; different-register concurrency."""
    env = await setup(dut, "chk025", "CHK-025", status=0x25252525)
    OLD, NEW = 0x11223344, 0xAABBCCDD
    for ci, (ard, rpol, exp) in enumerate([(1, 2, OLD), (2, "always", OLD), (3, "always", NEW)]):
        await env.write(0x00, OLD)
        s, nw, nr = env.t, len(env.wr_recs), len(env.rd_recs)
        env.start(write_agents(env, [dict(addr=0x00, data=NEW, awd=2, wd=2)], "always"),
                  read_agents(env, [dict(addr=0x00, ard=ard)], [rpol]))
        await env.run(60, f"case {ci + 1}")
        w, r = env.wr_recs[nw], env.rd_recs[nr]
        E = w["Ec"]
        assert E == s + 2, f"CHK-025: case {ci + 1}: Ec={s + 2} got {E}"
        assert r["Ear"] == E + ard - 2, f"CHK-025: case {ci + 1}: Ear={E + ard - 2} got {r['Ear']}"
        if ci == 0:
            assert r["Er"] == E + 2, f"CHK-025: case 1: Er=E+2 got {r['Er'] - E}"
        for e in range(r["Ear"] + 1, r["Er"] + 1):
            h = env.hist[e]
            assert h["rvalid"] == 1 and h["rdata"] == exp and h["rresp"] == OKAY, \
                f"CHK-025: case {ci + 1}: rdata={hx(exp)} rresp=0 at edge {e} got {hx(h['rdata'])} {h['rresp']}"
        assert word(env.hist[E]["regs"], 0) == OLD and word(env.hist[E + 1]["regs"], 0) == NEW, f"CHK-025: case {ci + 1}: register written at Ec"
    if env.N > 1:
        await env.write(0x04, 0x25BBBBBB)
        await env.write(0x00, 0x25000000)
        s = env.t
        env.start(write_agents(env, [dict(addr=0x00, data=0x25AAAAAA)], "always"), read_agents(env, [dict(addr=0x04)]))
        await env.run(20, "different registers")
        w, r = env.wr_recs[-1], env.rd_recs[-1]
        assert w["Ec"] == s and r["Ear"] == s, f"CHK-025: Ec=Ear={s} got {w['Ec']},{r['Ear']}"
        assert (r["rdata"], r["rresp"]) == (0x25BBBBBB, OKAY), f"CHK-025: read of REG_1 returns its value got {hx(r['rdata'])}"
        h = env.hist[s + 1]
        assert h["bvalid"] == 1 and h["rvalid"] == 1, "CHK-025: 1-cycle latency for both"
        assert word(h["regs"], 0) == 0x25AAAAAA and word(env.hist[s]["regs"], 0) == 0x25000000, "CHK-025: REG_0 updated at Ec"
    else:
        s = env.t
        env.start(write_agents(env, [dict(addr=0x00, data=0x25AAAAAA)], "always"), read_agents(env, [dict(addr=0x40)]))
        await env.run(20, "write REG_0 / read STATUS")
        assert env.rd_recs[-1]["rdata"] == 0x25252525 and env.hist[s + 1]["bvalid"] == 1, "CHK-025: status read with concurrent write"
        not_verifiable(dut, "CHK-025", "different read/write register pair needs PARA_NUM_REGS>1 (status used instead)")


@cocotb.test()
async def test_chk_026_backpressure_isolation(dut):
    """CHK-026: B back-pressure does not stall AR/R; R back-pressure does not stall AW/W/B or o_regs."""
    env = await setup(dut, "chk026", "CHK-026", status=0x26262626)
    N = env.N
    for k in range(N):
        await env.write(4 * k, 0x26000000 | (k * 0x1111))
    rd = [dict(addr=4 * (i % N), ard=1 if i == 0 else 0) for i in range(5)]

    def rtrace(m):
        return [(env.hist[m + i]["arready"], env.hist[m + i]["rvalid"],
                 env.hist[m + i]["rdata"] if env.hist[m + i]["rvalid"] else None) for i in range(11)]
    s, nw, nr = env.t, len(env.wr_recs), len(env.rd_recs)
    env.start(write_agents(env, [dict(addr=0x00, data=0x26AA55CC)], [20]), read_agents(env, rd))
    await env.run(100, "(a)")
    w, rs = env.wr_recs[nw], env.rd_recs[nr:nr + 5]
    m = rs[0]["Ear"]
    assert w["Ec"] == s and m == s + 1 and w["Eb"] == s + 21, f"CHK-026: (a) Ec={s} Ear={s + 1} Eb={s + 21} got {w['Ec']},{m},{w['Eb']}"
    assert [(x["Ear"] - m, x["Er"] - m) for x in rs] == [(2 * i, 2 * i + 1) for i in range(5)], "CHK-026: (a) AR at m+2i, R at m+2i+1"
    for e in range(m, rs[-1]["Er"] + 1):
        assert env.hist[e]["bvalid"] == 1, f"CHK-026: (a) B still pending at edge {e}"
    ta, da = rtrace(m), [(x["rdata"], x["rresp"]) for x in rs]
    s2, nr2 = env.t, len(env.rd_recs)
    env.start(read_agents(env, rd))
    await env.run(100, "(a) reference")
    rs2 = env.rd_recs[nr2:]
    m2 = rs2[0]["Ear"]
    assert m2 == s2 + 1 and [(x["Ear"] - m2, x["Er"] - m2) for x in rs2] == [(x["Ear"] - m, x["Er"] - m) for x in rs], "CHK-026: (a) read timing identical to run without pending write"
    assert rtrace(m2) == ta, "CHK-026: (a) arready/rvalid/rdata identical to run without pending write"
    assert [(x["rdata"], x["rresp"]) for x in rs2] == da, "CHK-026: (a) rdata identical"
    s, nw, nr = env.t, len(env.wr_recs), len(env.rd_recs)
    v0 = env.M[0]
    W = [dict(addr=4 * (i % N), data=0x26BB0000 + i, awd=1 if i == 0 else 0, wd=1 if i == 0 else 0) for i in range(5)]
    env.start(read_agents(env, [dict(addr=0x00)], [20]), write_agents(env, W, "always"))
    await env.run(100, "(b)")
    r, ws = env.rd_recs[nr], env.wr_recs[nw:nw + 5]
    n = ws[0]["Ea"]
    assert r["Ear"] == s and n == s + 1, f"CHK-026: (b) Ear={s} first AW={s + 1} got {r['Ear']},{n}"
    for i, x in enumerate(ws):
        assert (x["Ea"], x["Ew"], x["Eb"]) == (n + 2 * i, n + 2 * i, n + 2 * i + 1), f"CHK-026: (b) write {i} at n+2i got {(x['Ea'], x['Ew'], x['Eb'])}"
        assert word(env.hist[x["Ec"] + 1]["regs"], x["k"]) == x["data"], f"CHK-026: (b) o_regs updated from Ec of write {i}"
    for e in range(s + 1, ws[-1]["Eb"] + 2):
        h = env.hist[e]
        assert h["arready"] == 0 and h["rvalid"] == 1 and h["rdata"] == v0, f"CHK-026: (b) arready=0 rvalid=1 rdata={hx(v0)} at edge {e}"
    assert r["Er"] == s + 21, f"CHK-026: (b) Er={s + 21} got {r['Er']}"


@cocotb.test()
async def test_chk_027_map_and_aliasing(dut):
    """CHK-027: unique value in every register and full word-address sweep (no aliasing)."""
    env = await setup(dut, "chk027", "CHK-027", status=0x5747A7A5)
    N = env.N
    assert sig_width(dut.o_regs) == 32 * N, f"CHK-027: o_regs width {32 * N} got {sig_width(dut.o_regs)}"
    vals = [0xA5000000 | (k << 16) | (k << 8) | (0xFF - k) for k in range(N)]  # nnc-literal-ok: byte-lane shift from the spec pattern
    for k in range(N):
        await env.write(4 * k, vals[k])
    regs0 = env.o["regs"]
    for k in range(N):
        assert word(regs0, k) == vals[k], f"CHK-027: o_regs word {k}={hx(vals[k])} got {hx(word(regs0, k))}"
    nr = len(env.rd_recs)
    env.start(read_agents(env, [dict(addr=4 * w) for w in range(env.NW)]))
    await env.run(2 * env.NW + 100, "address sweep")
    recs = env.rd_recs[nr:]
    assert len(recs) == env.NW, f"CHK-027: {env.NW} reads got {len(recs)}"
    ok = 0
    for w, rec in enumerate(recs):
        exp = (vals[w], OKAY) if w < N else (0x5747A7A5, OKAY) if w == 16 else (0, SLVERR)
        assert (rec["rdata"], rec["rresp"]) == exp, f"CHK-027: word {w}: {hx(exp[0])}/{exp[1]} got {hx(rec['rdata'])}/{rec['rresp']}"
        ok += rec["rresp"] == OKAY
    assert ok == N + 1, f"CHK-027: exactly {N + 1} OKAY word indices got {ok}"
    assert env.o["regs"] == regs0, "CHK-027: o_regs unchanged by reads"


@cocotb.test()
async def test_chk_028_status_register(dut):
    """CHK-028: status read samples i_status at Ear, held under back-pressure; status writes ignored, OKAY."""
    env = await setup(dut, "chk028", "CHK-028")
    env.hooks = [lambda e: e.drive(i_status=(0x9E3779B1 * (e.t + 11)) & M32)]
    for k in range(env.N):
        await env.write(4 * k, 0x28000000 | (k << 8) | 0x77)  # nnc-literal-ok: byte-lane shift for a unique data pattern

    def chk_read(rec, hold):
        ear, er = rec["Ear"], rec["Er"]
        sv = env.hin[ear]["i_status"]
        assert env.hin[ear - 1]["i_status"] != sv and env.hin[ear + 1]["i_status"] != sv, "CHK-028: i_status distinct around Ear"
        assert env.hist[ear + 1]["rvalid"] == 1, "CHK-028: rvalid=1 at Ear+1"
        assert er == ear + 1 + hold, f"CHK-028: Er=Ear+{1 + hold} got {er - ear}"
        for e in range(ear + 1, er + 1):
            h = env.hist[e]
            assert h["rdata"] == sv and h["rresp"] == OKAY, f"CHK-028: rdata=i_status at Ear {hx(sv)} at edge {e} got {hx(h['rdata'])} {h['rresp']}"
    chk_read(await env.read(0x40), 0)
    for a in (0x40, 0x41, 0x42, 0x43):
        chk_read(await env.read(a, rpol=5), 5)
    for strb in (0x0, 0x1, 0xA, 0xF):
        regs0 = env.o["regs"]
        wr = await env.write(0x40, M32, strb)
        assert env.hist[wr["Ec"] + 1]["bvalid"] == 1 and wr["bresp"] == OKAY, f"CHK-028: status write strb {strb:x}: bvalid at Ec+1, OKAY got {wr['bresp']}"
        for e in range(wr["Ec"], env.t + 1):
            assert env.hist[e]["regs"] == regs0, f"CHK-028: o_regs unchanged by status write strb {strb:x}"
    chk_read(await env.read(0x40), 0)


@cocotb.test()
async def test_chk_029_unmapped_addresses(dut):
    """CHK-029: unmapped writes/reads answer SLVERR with normal timing, rdata 0, no register change."""
    env = await setup(dut, "chk029", "CHK-029", status=0x29292929)
    N, AW = env.N, env.AW
    for k in range(N):
        await env.write(4 * k, (0x29000000 | ((k + 1) * 0x10101)) & M32)
    addrs = [4 * w for w in range(N, 16)] + [0x44, (1 << AW) - 4]
    if AW > 7:
        addrs += [m | (1 << j) for m in env.mapped for j in range(7, AW)]
    seen = []
    for a in addrs:
        if a not in seen:
            seen.append(a)
    for a in seen:
        regs0 = env.o["regs"]
        wr = await env.write(a, M32)
        ec, eb = wr["Ec"], wr["Eb"]
        assert env.hist[ec + 1]["bvalid"] == 1 and eb == ec + 1 and wr["bresp"] == SLVERR, f"CHK-029: write {hx(a)}: bvalid at Ec+1, SLVERR got {wr['bresp']}"
        assert env.hist[eb + 1]["awready"] == 1 and env.hist[eb + 1]["wready"] == 1, f"CHK-029: readies 1 after B of {hx(a)}"
        for e in range(ec, env.t + 1):
            assert env.hist[e]["regs"] == regs0, f"CHK-029: o_regs unchanged by write {hx(a)}"
        rd = await env.read(a)
        ear = rd["Ear"]
        h = env.hist[ear + 1]
        assert h["rvalid"] == 1 and rd["Er"] == ear + 1, f"CHK-029: read {hx(a)}: rvalid at Ear+1"
        assert (rd["rdata"], rd["rresp"]) == (0, SLVERR), f"CHK-029: read {hx(a)}: 0/SLVERR got {hx(rd['rdata'])}/{rd['rresp']}"
        assert env.hist[rd["Er"] + 1]["arready"] == 1, f"CHK-029: arready 1 after R of {hx(a)}"


@cocotb.test()
async def test_chk_030_unmapped_no_stall(dut):
    """CHK-030: unmapped access does not stall or disturb the other channels or the next transaction."""
    env = await setup(dut, "chk030", "CHK-030", status=0x30303030)
    N = env.N
    ra = 0x04 if N > 1 else 0x00
    touched = sorted(set([0, ra >> 2] + [i % N for i in range(6)]))

    async def preload():
        for k in touched:
            await env.write(4 * k, 0x30000000 | (k << 8) | 0x5A)  # nnc-literal-ok: byte-lane shift for a unique data pattern

    async def go(writes, reads):
        await preload()
        s, nw, nr = env.t, len(env.wr_recs), len(env.rd_recs)
        env.start(write_agents(env, writes), read_agents(env, reads))
        await env.run(100, "stream")
        L = env.t - s
        hs = [env.hist[s + i] for i in range(L + 1)]
        return dict(
            s=s,
            w=[(x["Ea"] - s, x["Ew"] - s, x["Ec"] - s, x["Eb"] - s, x["bresp"]) for x in env.wr_recs[nw:]],
            r=[(x["Ear"] - s, x["Er"] - s, x["rdata"], x["rresp"]) for x in env.rd_recs[nr:]],
            regs=[h["regs"] for h in hs],
            wtr=[(h["awready"], h["wready"], h["bvalid"], h["bresp"] if h["bvalid"] else None) for h in hs],
            rtr=[(h["arready"], h["rvalid"], h["rdata"] if h["rvalid"] else None) for h in hs])
    reads = [dict(addr=ra) for _ in range(6)]
    un = await go([dict(addr=0x44, data=M32), dict(addr=0x00, data=0x3A3A3A3A)], reads)
    mp = await go([dict(addr=0x40, data=M32), dict(addr=0x00, data=0x3A3A3A3A)], reads)
    assert un["w"] == [(0, 0, 0, 1, SLVERR), (2, 2, 2, 3, OKAY)], f"CHK-030: unmapped then mapped write timing got {un['w']}"
    assert word(un["regs"][3], 0) == 0x3A3A3A3A and word(un["regs"][2], 0) == 0x3000005A, "CHK-030: REG_0 updated from n+3"
    assert un["r"] == mp["r"] and un["rtr"] == mp["rtr"], "CHK-030: read stream identical to all-mapped run"
    assert un["regs"] == mp["regs"], "CHK-030: o_regs identical to all-mapped run"
    W = [dict(addr=4 * (i % N), data=0x3B000000 + i) for i in range(6)]
    un2 = await go(W, [dict(addr=0x44), dict(addr=0x00)])
    mp2 = await go(W, [dict(addr=0x40), dict(addr=0x00)])
    assert un2["r"][0] == (0, 1, 0, SLVERR), f"CHK-030: unmapped read AR n, R n+1, 0/SLVERR got {un2['r'][0]}"
    assert un2["r"][1][:2] == (2, 3) and un2["r"][1][3] == OKAY, f"CHK-030: mapped read AR n+2, R n+3 OKAY got {un2['r'][1]}"
    assert un2["r"][1] == mp2["r"][1], "CHK-030: next read identical to all-mapped run"
    assert un2["w"] == mp2["w"] and un2["wtr"] == mp2["wtr"], "CHK-030: write stream timing unchanged by unmapped read"
    assert un2["regs"] == mp2["regs"], "CHK-030: o_regs unchanged by unmapped read"


@cocotb.test()
async def test_chk_031_addr_lsb_and_prot_ignored(dut):
    """CHK-031: addr[1:0] and AxPROT have no effect (run A vs run B, cycle for cycle)."""
    env = await setup(dut, "chk031", "CHK-031")
    writes, reads, bpol, rpol = gen_traffic(env, rng("chk031-sequence"), 110, 110)

    async def one_run(use_lo, length):
        await env.reset(3, i_status=0)
        R1 = env.t
        env.srng = rng("chk031-scramble")
        rr = rng("chk031-ready")
        env.hooks = [lambda e: e.drive(i_status=(((e.t - R1) * 0x01000193) ^ 0x5A5A0000) & M32)]
        W, R = to_items(writes, reads, use_lo)
        nw = len(env.wr_recs)
        env.start(write_agents(env, W, list(bpol), rnd=rr), read_agents(env, R, list(rpol), rnd=rr))
        if length is None:
            await env.run(30000, "run A")
            length = env.t - R1
        else:
            for _ in range(length):
                await env.tick()
            assert env.idle(), "CHK-031: run B finishes in the same number of cycles as run A, got not finished"
            env.quiesce()
        env.hooks = []
        return [env.hist[R1 + i] for i in range(length + 1)], length, env.wr_recs[nw:]
    ha, L, _ = await one_run(False, None)
    hb, _, wrb = await one_run(True, L)
    for i, (a, b) in enumerate(zip(ha, hb)):
        assert a == b, f"CHK-031: outputs at R1+{i} identical: run A {a} got run B {b}"
    for x in wrb:
        if x["kind"] != "unmapped" and "bresp" in x:
            assert x["bresp"] == OKAY, f"CHK-031: mapped write {hx(x['addr'])} with addr[1:0]/prot answers OKAY got {x['bresp']}"


@cocotb.test()
async def test_chk_032_write_strobes(dut):
    """CHK-032: all 16 write-strobe values with byte-distinct data."""
    env = await setup(dut, "chk032", "CHK-032")
    for s in range(16):
        k = s % env.N
        V = (0x3C5A96C3 + s) & M32
        D = (~V) & M32
        await env.write(4 * k, V)
        before = env.o["regs"]
        wr = await env.write(4 * k, D, s)
        exp = merge(V, D, s)
        ec, ew = wr["Ec"], wr["Ew"]
        assert wr["strb"] == s and wr["data"] == D, "CHK-032: strobes/data taken at Ew"
        assert wr["bresp"] == OKAY, f"CHK-032: strb {s:04b}: bresp OKAY got {wr['bresp']}"
        assert env.hist[ec]["regs"] == before, f"CHK-032: strb {s:04b}: no change before Ec"
        after = env.hist[ec + 1]["regs"]
        assert word(after, k) == exp, f"CHK-032: strb {s:04b}: REG_{k}={hx(exp)} got {hx(word(after, k))}"
        mask = M32 << (32 * k)
        assert (after & ~mask) == (before & ~mask), f"CHK-032: strb {s:04b}: other o_regs bits unchanged"
        assert env.hin[ew + 1]["i_s_axi_wdata"] != D or env.hin[ew + 1]["i_s_axi_wstrb"] != s, "CHK-032: wdata/wstrb changed after W"
        rd = await env.read(4 * k)
        assert (rd["rdata"], rd["rresp"]) == (exp, OKAY), f"CHK-032: strb {s:04b}: read {hx(exp)} OKAY got {hx(rd['rdata'])} {rd['rresp']}"


@cocotb.test()
async def test_chk_034_async_reset_mid_cycle(dut):
    """CHK-034: asynchronous reset assertion between rising edges with transactions in progress."""
    env = await setup(dut, "chk034", "CHK-034")
    N = env.N

    async def load_all():
        for k in range(N):
            await env.write(4 * k, (0x34000001 + 0x01020304 * (k + 1)) & M32)
    await load_all()
    env.start(write_agents(env, [dict(addr=0x00, data=0x3434ABCD)], "never"),
              read_agents(env, [dict(addr=4 * (1 if N > 1 else 0))], "never"))
    for _ in range(20):
        if env.o["bvalid"] == 1 and env.o["rvalid"] == 1:
            break
        await env.tick()
    assert env.o["bvalid"] == 1 and env.o["rvalid"] == 1, "CHK-034: (a) B and R pending before reset"
    before, _ = await env.mid_reset(0.25, "CHK-034")
    assert before["bvalid"] == 1 and before["rvalid"] == 1 and before["regs"] != 0, f"CHK-034: (a) state before reset non-idle got {before}"
    await env.hold_release(2)
    await env.tick(2)
    assert env.o["awready"] == 1 and env.o["regs"] == 0, "CHK-034: (a) idle after release"
    await load_all()
    env.start(ChanDriver(env, "aw", [(0, {"i_s_axi_awaddr": 0x00, "i_s_axi_awprot": 0})], env.scr_aw),
              ReadyDriver(env, "b", "always"))
    for _ in range(10):
        await env.tick()
        if env.o["awready"] == 0:
            break
    assert env.aw_held and env.o["awready"] == 0 and env.o["wready"] == 1, "CHK-034: (b) only AW held"
    before, _ = await env.mid_reset(0.75, "CHK-034")
    assert before["awready"] == 0 and before["regs"] != 0, f"CHK-034: (b) state before reset non-idle got {before}"
    await env.hold_release(2)
    await env.tick()
    rec = await env.write(0x00, 0x34343434)
    assert rec["Eb"] == rec["Ec"] + 1, "CHK-034: normal write after reset"


@cocotb.test()
async def test_chk_035_reset_discards_held_state(dut):
    """CHK-035: reset discards held AW, held W, pending B and pending R."""
    env = await setup(dut, "chk035", "CHK-035")
    N = env.N

    def idle_check(tag):
        o = env.o
        assert o["bvalid"] == 0 and o["rvalid"] == 0, f"CHK-035: {tag}: bvalid=rvalid=0 after R1 got {o['bvalid']},{o['rvalid']}"
        assert (o["awready"], o["wready"], o["arready"]) == (1, 1, 1), f"CHK-035: {tag}: readies 1 from R1"
        assert o["regs"] == 0, f"CHK-035: {tag}: o_regs=0 got {hx(o['regs'])}"

    # (a) AW only
    env.start(ChanDriver(env, "aw", [(0, {"i_s_axi_awaddr": 0x04, "i_s_axi_awprot": 0})], env.scr_aw))
    for _ in range(10):
        await env.tick()
        if env.o["awready"] == 0:
            break
    assert env.aw_held, "CHK-035: (a) AW held before reset"
    await env.reset(2)
    env.drive(i_s_axi_bready=1)
    for _ in range(6):
        await env.tick()
        idle_check("(a) idle")
    s = env.t
    wdrv = ChanDriver(env, "w", [(0, {"i_s_axi_wdata": 0xDEADBEEF, "i_s_axi_wstrb": 0xF})], env.scr_w)
    env.start(wdrv, ReadyDriver(env, "b", "always"))
    for _ in range(8):  # nnc-literal-ok: 8 cycles of lone W from the check stimulus
        await env.tick()
        assert env.o["bvalid"] == 0 and env.o["regs"] == 0, "CHK-035: (a) lone W gives no B and no write"
    assert wdrv.edges == [s], f"CHK-035: (a) lone W taken at {s} got {wdrv.edges}"
    for e in range(s + 1, env.t + 1):
        assert env.hist[e]["wready"] == 0, f"CHK-035: (a) wready=0 after lone W at edge {e}"
    s2, nw = env.t, len(env.wr_recs)
    env.start(ChanDriver(env, "aw", [(0, {"i_s_axi_awaddr": 0x08, "i_s_axi_awprot": 0})], env.scr_aw),  # nnc-literal-ok: byte address 0x08 of REG_2 from the check stimulus
              ReadyDriver(env, "b", "always"))
    await env.run(20, "(a) AW to 0x08")
    rec = env.wr_recs[nw]
    assert rec["Ea"] == s2 and rec["Ec"] == s2 and rec["Ew"] == s, "CHK-035: (a) AW to 0x08 taken at next edge (Ec)"
    o = env.hist[s2 + 1]
    assert o["bvalid"] == 1 and o["bresp"] == (OKAY if N > 2 else SLVERR), f"CHK-035: (a) bvalid at Ec+1 got {o['bvalid']} {o['bresp']}"
    if N > 2:
        assert word(o["regs"], 2) == 0xDEADBEEF, f"CHK-035: (a) REG_2=0xdeadbeef got {hx(word(o['regs'], 2))}"
    if N > 1:
        assert word(o["regs"], 1) == 0, "CHK-035: (a) REG_1 stays 0"
    # (b) W only
    env.start(ChanDriver(env, "w", [(0, {"i_s_axi_wdata": 0x5555AAAA, "i_s_axi_wstrb": 0xF})], env.scr_w))
    for _ in range(10):
        await env.tick()
        if env.o["wready"] == 0:
            break
    assert env.w_held, "CHK-035: (b) W held before reset"
    await env.reset(2)
    env.drive(i_s_axi_bready=1)
    await env.tick()
    idle_check("(b) R1+1")
    s = env.t
    adrv = ChanDriver(env, "aw", [(0, {"i_s_axi_awaddr": 0x0C, "i_s_axi_awprot": 0})], env.scr_aw)
    env.start(adrv, ReadyDriver(env, "b", "always"))
    for _ in range(8):  # nnc-literal-ok: 8 cycles of lone AW from the check stimulus
        await env.tick()
        assert env.o["bvalid"] == 0 and env.o["regs"] == 0, "CHK-035: (b) lone AW gives no B and no write"
    assert adrv.edges == [s], f"CHK-035: (b) lone AW taken at {s} got {adrv.edges}"
    s2, nw = env.t, len(env.wr_recs)
    env.start(ChanDriver(env, "w", [(0, {"i_s_axi_wdata": 0x0F0F0F0F, "i_s_axi_wstrb": 0xF})], env.scr_w),
              ReadyDriver(env, "b", "always"))
    await env.run(20, "(b) new W")
    rec = env.wr_recs[nw]
    assert rec["Ec"] == s2 and rec["data"] == 0x0F0F0F0F, "CHK-035: (b) write uses new W"
    if N > 3:
        assert word(env.hist[s2 + 1]["regs"], 3) == 0x0F0F0F0F, "CHK-035: (b) REG_3=0x0f0f0f0f, not 0x5555aaaa"
    # (c) B pending
    env.start(write_agents(env, [dict(addr=0x00, data=0x11111111)], "never"))
    for _ in range(10):
        await env.tick()
        if env.o["bvalid"] == 1:
            break
    assert env.o["bvalid"] == 1, "CHK-035: (c) B pending before reset"
    await env.reset(2)
    env.drive(i_s_axi_bready=1)
    for _ in range(6):
        await env.tick()
        idle_check("(c)")
    # (d) R pending
    env.start(read_agents(env, [dict(addr=0x00)], "never"))
    for _ in range(10):
        await env.tick()
        if env.o["rvalid"] == 1:
            break
    assert env.o["rvalid"] == 1, "CHK-035: (d) R pending before reset"
    await env.reset(2)
    env.drive(i_s_axi_rready=1)
    for _ in range(6):
        await env.tick()
        idle_check("(d)")
    if N <= 3:
        not_verifiable(dut, "CHK-035", f"REG_2/REG_3 data checks need PARA_NUM_REGS>3; this run has {N}")


@cocotb.test()
async def test_chk_036_valids_through_reset(dut):
    """CHK-036: valids held at 1 through reset become new requests at R1+1."""
    env = await setup(dut, "chk036", "CHK-036")
    a = 0x08 if env.N >= 3 else 0x00  # nnc-literal-ok: byte address 0x08 of REG_2 from the check stimulus
    k = a >> 2
    await env.write(a, 0x36363636)
    t0 = env.t
    env.drive(i_rst_n=0, i_s_axi_awvalid=1, i_s_axi_wvalid=1, i_s_axi_arvalid=1, i_s_axi_bready=1,
              i_s_axi_rready=1, i_s_axi_awaddr=a, i_s_axi_araddr=a, i_s_axi_awprot=0, i_s_axi_arprot=0,
              i_s_axi_wstrb=0xF, i_s_axi_wdata=0x0BADF00D)
    env.start()
    await env.tick()
    env.drive(i_s_axi_wdata=0xCAFEF00D)
    await env.tick()
    await env.release()
    R1 = env.t
    for t in range(t0 + 1, R1 + 1):
        check_zero(env.hist[t], "CHK-036", f"edge {t} with i_rst_n=0 / at R1 (no transfer)")
    nw, nr = len(env.wr_recs), len(env.rd_recs)
    await env.tick()  # edge R1
    assert len(env.wr_recs) == nw and len(env.rd_recs) == nr and not env.aw_held, "CHK-036: no transfer at R1"
    assert word(env.o["regs"], k) == 0, "CHK-036: o_regs 0 through R1+1"
    await env.tick()  # edge R1+1
    w, r = env.wr_recs[nw], env.rd_recs[nr]
    assert (w["Ea"], w["Ew"], w["Ec"], r["Ear"]) == (R1 + 1,) * 4, f"CHK-036: AW/W/AR at R1+1 got {(w['Ea'], w['Ew'], r['Ear'])}"
    o = env.o
    assert o["bvalid"] == 1 and o["bresp"] == OKAY, "CHK-036: bvalid=1 bresp=0 at R1+2"
    assert word(o["regs"], k) == 0xCAFEF00D, f"CHK-036: target register 0xcafef00d at R1+2 got {hx(word(o['regs'], k))}"
    assert o["rvalid"] == 1 and o["rdata"] == 0 and o["rresp"] == OKAY, f"CHK-036: rvalid=1 rdata=0 at R1+2 got {hx(o['rdata'])}"
    assert (o["awready"], o["wready"], o["arready"]) == (0, 0, 0), "CHK-036: readies 0 at R1+2"
    await env.tick()  # edge R1+2
    assert w["Eb"] == R1 + 2 and r["Er"] == R1 + 2, "CHK-036: B and R at R1+2"
    assert (env.o["awready"], env.o["wready"], env.o["arready"]) == (1, 1, 1), "CHK-036: readies 1 at R1+3"
    await env.tick()  # edge R1+3
    assert env.wr_recs[nw + 1]["Ec"] == R1 + 3 and env.rd_recs[nr + 1]["Ear"] == R1 + 3, "CHK-036: next AW/W/AR at R1+3"
    env.drive(**VALIDS0)
    await env.run(20, "completion")
    assert env.rd_recs[nr + 1]["rdata"] == 0xCAFEF00D, "CHK-036: second read returns 0xcafef00d"


@cocotb.test()
async def test_chk_037_no_combinational_path(dut):
    """CHK-037 (and CHK-017): outputs change only at rising edges; readies do not depend on valids."""
    start_clock(dut)
    env = Env(dut, "chk037")
    env.ctx = "CHK-037"
    await env.reset(3)
    R1 = env.t
    if env.period < 8 or env.high < 2 or env.period - env.high < 4:  # nnc-literal-ok: minimum clock period in sim steps for intra-cycle sampling
        not_verifiable(dut, "CHK-037", f"clock period {env.period} steps too short for intra-cycle sampling")
        return
    r = env.rng

    def rin(**fixed):
        d = {"i_s_axi_awaddr": r.getrandbits(env.AW), "i_s_axi_awprot": r.randrange(8),  # nnc-literal-ok: 3-bit AxPROT has 8 values
             "i_s_axi_wdata": r.getrandbits(32), "i_s_axi_wstrb": r.randrange(16),
             "i_s_axi_araddr": r.getrandbits(env.AW), "i_s_axi_arprot": r.randrange(8),  # nnc-literal-ok: 3-bit AxPROT has 8 values
             "i_status": r.getrandbits(32)}
        for n in ("i_s_axi_awvalid", "i_s_axi_wvalid", "i_s_axi_arvalid", "i_s_axi_bready", "i_s_axi_rready"):
            d[n] = r.randrange(2)
        d.update(fixed)
        return d

    def rdy(aw, w, ar, tag):
        o = env.o
        assert (o["awready"], o["wready"], o["arready"]) == (aw, w, ar), \
            f"CHK-037: {tag}: readies {(aw, w, ar)} got {(o['awready'], o['wready'], o['arready'])}"
    for _ in range(11):
        await env.tick_toggle(rin(**VALIDS0), rin(**VALIDS0))
        rdy(1, 1, 1, f"valids 0, R1+{env.t - R1}")
        assert env.o["bvalid"] == 0 and env.o["rvalid"] == 0, "CHK-037: idle bvalid=rvalid=0"
    for _ in range(5):
        await env.tick_toggle(rin(), rin(**VALIDS0))
        rdy(1, 1, 1, "idle, valids toggled")
    no_rsp = dict(i_s_axi_bready=0, i_s_axi_rready=0)
    for first in ("aw", "w"):
        env.drive(**rin(i_s_axi_awvalid=int(first == "aw"), i_s_axi_wvalid=int(first == "w"), i_s_axi_arvalid=0, **no_rsp))
        await env.tick()
        assert env.aw_held if first == "aw" else env.w_held, f"CHK-037: {first} held"
        for _ in range(5):
            if first == "aw":
                await env.tick_toggle(rin(), rin(i_s_axi_wvalid=0, i_s_axi_arvalid=0))
                rdy(0, 1, 1, "AW held")
            else:
                await env.tick_toggle(rin(), rin(i_s_axi_awvalid=0, i_s_axi_arvalid=0))
                rdy(1, 0, 1, "W held")
        env.drive(**rin(i_s_axi_awvalid=int(first == "w"), i_s_axi_wvalid=int(first == "aw"), i_s_axi_arvalid=0, **no_rsp))
        await env.tick()
        assert env.b_pending, "CHK-037: B pending"
        for _ in range(5):
            await env.tick_toggle(rin(), rin(i_s_axi_bready=0, i_s_axi_arvalid=0))
            rdy(0, 0, 1, "B pending")
        env.drive(i_s_axi_bready=1, **VALIDS0)
        await env.run(10, "B completion")
    env.drive(**rin(i_s_axi_awvalid=0, i_s_axi_wvalid=0, i_s_axi_arvalid=1, **no_rsp))
    await env.tick()
    assert env.r_pending, "CHK-037: R pending"
    for _ in range(5):
        await env.tick_toggle(rin(), rin(i_s_axi_rready=0, i_s_axi_awvalid=0, i_s_axi_wvalid=0))
        rdy(1, 1, 0, "R pending")
    env.drive(i_s_axi_rready=1, **VALIDS0)
    await env.run(10, "R completion")


@cocotb.test()
async def test_regression_random(dut):
    """CHK-001..CHK-017: broad random legal traffic with back-pressure and resets, scored by the reference model."""
    env = await setup(dut, "regression", "REGRESSION")
    r = rng("regression-traffic")
    sr = rng("regression-status")
    env.hooks = [lambda e: e.drive(i_status=sr.getrandbits(32)) if sr.random() < 0.3 else None]
    for seg in range(12):
        writes, reads, bpol, rpol = gen_traffic(env, r, r.randint(20, 60), r.randint(20, 60))
        W, R = to_items(writes, reads, True)
        env.start(write_agents(env, W, bpol, rnd=r), read_agents(env, R, rpol, rnd=r))
        if seg % 4 == 3:
            await env.tick(r.randint(5, 80))
            if seg % 8 == 3:  # nnc-literal-ok: segment schedule (alternate mid-cycle and synchronous resets)
                await env.mid_reset(r.choice([0.2, 0.3, 0.7, 0.8]), "CHK-013")
                await env.hold_release(r.randint(2, 4))
            else:
                await env.reset(r.randint(2, 4))
            await env.tick()
        else:
            await env.run(20000, f"segment {seg}")
    for k in range(env.N):
        rec = await env.read(4 * k)
        assert (rec["rdata"], rec["rresp"]) == (env.M[k], OKAY), \
            f"CHK-005: final read REG_{k}={hx(env.M[k])} got {hx(rec['rdata'])}"
    assert len(env.wr_recs) > 200 and len(env.rd_recs) > 200, \
        f"CHK-012: regression ran >200 writes and reads got {len(env.wr_recs)}/{len(env.rd_recs)}"

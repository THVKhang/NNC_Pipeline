"""cocotb 2.1 testbench for m_ahb2axi_top (AHB5 subordinate -> AXI4 manager bridge).

Every expected value comes from the specification checks CHK-001..CHK-040.
Sampling model: the monitor samples every port at falling edge + ReadOnly. Inputs are only
driven right after falling edges, so that sample equals the values seen at the next rising edge.
Sample index t == rising-edge index.
"""
import cocotb
from collections import deque
from cocotb.triggers import FallingEdge, RisingEdge, ReadOnly, Timer
from nnc_cocotb import *

IDLE, BUSY, NONSEQ, SEQ = 0, 1, 2, 3
SINGLE, INCR, WRAP4, INCR4, WRAP8, INCR8, WRAP16, INCR16 = range(8)
BLEN = [1, 0, 4, 4, 8, 8, 16, 16]
FIXED = [WRAP4, INCR4, WRAP8, INCR8, WRAP16, INCR16]
WRAPS = (WRAP4, WRAP8, WRAP16)
DEV_NE, DEV_E, WB_A, WB_B = 0b00000, 0b00001, 0b00111, 0b01111
LEGAL_MT = (DEV_NE, DEV_E, WB_A, WB_B)
RESERVED_52 = (4, 5, 8, 9, 10, 11, 12, 13)
OKAY, EXOKAY, SLVERR, DECERR = 0, 1, 2, 3


def P(name):
    try:
        return int(PARAMS.get(name, 1))
    except Exception:
        return 1


SIGS = [("rst", "i_rst_n_core"), ("hsel", "i_ahb_hsel"), ("hready", "i_ahb_hready"),
        ("haddr", "i_ahb_haddr"), ("htrans", "i_ahb_htrans"), ("hwrite", "i_ahb_hwrite"),
        ("hsize", "i_ahb_hsize"), ("hburst", "i_ahb_hburst"), ("hprot", "i_ahb_hprot"),
        ("hns", "i_ahb_hnonsec"), ("hlock", "i_ahb_hmastlock"), ("hwdata", "i_ahb_hwdata"),
        ("hwstrb", "i_ahb_hwstrb"), ("hro", "o_ahb_hreadyout"), ("hresp", "o_ahb_hresp"),
        ("hrdata", "o_ahb_hrdata")]
SIGS += [(n, "o_axi_" + n) for n in ("awid awaddr awlen awsize awburst awlock awcache awprot awvalid "
                                     "wdata wstrb wlast wvalid bready arid araddr arlen arsize arburst "
                                     "arlock arcache arprot arvalid rready").split()]
SIGS += [(n, "i_axi_" + n) for n in "awready wready bid bresp bvalid arready rid rdata rresp rlast rvalid".split()]
AXI_OUTS = [p for _, p in SIGS if p.startswith("o_axi_")]
RST_VAL = dict(hro=1, hresp=0, hrdata=0, awvalid=0, wvalid=0, arvalid=0, bready=0, rready=0, awid=0,
               awaddr=0, awlen=0, awsize=0, awburst=1, awcache=0, awprot=0, wdata=0, wstrb=0, wlast=0,
               arid=0, araddr=0, arlen=0, arsize=0, arburst=1, arcache=0, arprot=0, awlock=0, arlock=0)
STAB = {"aw": ("awid", "awaddr", "awlen", "awsize", "awburst", "awcache", "awprot"),
        "w": ("wdata", "wstrb", "wlast"),
        "ar": ("arid", "araddr", "arlen", "arsize", "arburst", "arcache", "arprot")}


# ----------------------------------------------------------------- reference mappings (spec)
def _b(p, i):
    return (p >> i) & 1


def mapprot(p, ns):  # AxPROT = {~HPROT[0], HNONSEC, HPROT[1]}
    return ((1 - _b(p, 0)) << 2) | ((ns & 1) << 1) | _b(p, 1)


def arcache(p):
    return ((_b(p, 4) & (1 - _b(p, 5))) << 3) | ((_b(p, 4) & _b(p, 5)) << 2) | (_b(p, 3) << 1) | _b(p, 2)


def awcache(p):
    return ((_b(p, 4) & _b(p, 5)) << 3) | ((_b(p, 4) & (1 - _b(p, 5))) << 2) | (_b(p, 3) << 1) | _b(p, 2)


def is_wb(x):
    return ((x['prot'] >> 2) & 31) in (WB_A, WB_B)


def rejected(x):
    sz = x['size']
    return (x['lock'] == 1 or _b(x['prot'], 6) == 1 or sz > 2 or sz < 0 or x['addr'] % (1 << sz) != 0
            or ((x['prot'] >> 2) & 15) in RESERVED_52)


def eligible(G):
    x0 = G[0]
    N = BLEN[x0['burst']] if 0 <= x0['burst'] < 8 else 0
    return (N > 1 and len(G) == N and x0['trans'] == NONSEQ and all(y['trans'] == SEQ for y in G[1:])
            and all(is_wb(y) for y in G) and len({(y['size'], y['prot'], y['ns'], y['burst']) for y in G}) == 1)


def axi_beats(addr, ln, size, burst):
    n, sz = ln + 1, 1 << max(size, 0)
    if burst == 2:
        tot = n * sz
        base = addr & ~(tot - 1)
        return [base + ((addr - base + i * sz) % tot) for i in range(n)]
    return [(addr + i * sz) & 0xFFFFFFFF for i in range(n)]


def lanes(addr, size):
    return (((1 << (1 << size)) - 1) << (addr & 3)) & 0xF


# ----------------------------------------------------------------- monitor + protocol checker
class Mon:
    def __init__(s, dut):
        s.dut = dut
        s.h = [(k, getattr(dut, p)) for k, p in SIGS]
        s.t = 0
        s.last = None
        s.prev = None
        s.viol = {}
        s.trace = None
        s.clear()

    def clear(s):
        s.x, s.aw, s.w, s.b, s.ar, s.r, s.validt = [], [], [], [], [], [], []
        s.cur = None
        s.idle = False
        s.v0 = {'aw': None, 'ar': None}

    def bad(s, k, msg):
        lst = s.viol.setdefault(k, [])
        if len(lst) < 20:
            lst.append((s.t, msg))

    async def run(s):
        clk = s.dut.i_clk_core
        while True:
            await FallingEdge(clk)
            await ReadOnly()
            d = {}
            for k, h in s.h:
                v = val(h)
                d[k] = -1 if v is None else v
            s.t += 1
            d['t'] = s.t
            s.step(d)
            s.prev = d
            s.last = d

    def step(s, d):
        t, p = d['t'], s.prev
        if d['rst'] != 1:
            for k, v in RST_VAL.items():
                if d[k] != v:
                    s.bad('reset_value', f"{k}={d[k]} expected {v}")
            s.cur, s.idle, s.v0 = None, False, {'aw': None, 'ar': None}
            return
        if d['awlock'] != 0 or d['arlock'] != 0:
            s.bad('lock_tied_low', f"awlock={d['awlock']} arlock={d['arlock']}")
        if d['arlen'] != 0 or d['arburst'] != 1:
            s.bad('ar_single_incr', f"arlen={d['arlen']} arburst={d['arburst']}")
        if s.trace is not None:
            s.trace.append((t, d['hro'], d['hresp'], d['awvalid'], d['wvalid'], d['arvalid']))
        if 1 in (d['awvalid'], d['wvalid'], d['arvalid']):
            s.validt.append(t)
        pr = p if (p is not None and p['rst'] == 1) else None
        if pr is not None:
            for ch, keys in STAB.items():
                if pr[ch + 'valid'] == 1 and pr[ch + 'ready'] == 0 and (
                        d[ch + 'valid'] != 1 or any(d[k] != pr[k] for k in keys)):
                    s.bad('stable_' + ch, f"{ch} VALID/payload changed before READY")
            if pr['rvalid'] == 1 and pr['rready'] == 0 and (
                    d['rvalid'] != 1 or any(d[k] != pr[k] for k in ('rid', 'rdata', 'rresp', 'rlast'))):
                s.bad('in_r_stable', "RVALID/payload changed before RREADY")
            if pr['bvalid'] == 1 and pr['bready'] == 0 and (
                    d['bvalid'] != 1 or d['bresp'] != pr['bresp'] or d['bid'] != pr['bid']):
                s.bad('in_b_stable', "BVALID/BRESP changed before BREADY")
            if pr['hsel'] == 1 and pr['hready'] == 0 and pr['htrans'] >= 2 and pr['hresp'] != 1 and (
                    d['htrans'] != pr['htrans'] or d['haddr'] != pr['haddr']):
                s.bad('in_ahb_stable', "HADDR/HTRANS changed during wait state")
            if pr['hresp'] == 1 and pr['hro'] == 0 and not (d['hresp'] == 1 and d['hro'] == 1):
                s.bad('ahb_error_2nd', f"hresp={d['hresp']} hreadyout={d['hro']}")
        if d['hresp'] == 1 and d['hro'] == 1 and not (pr is not None and pr['hresp'] == 1 and pr['hro'] == 0):
            s.bad('ahb_error_1st', "ERROR with HREADYOUT=1 without first cycle")
        c = s.cur
        if c is not None:
            if c['wd0'] is None:
                c['wd0'] = (d['hwdata'], d['hwstrb'])
            if d['hresp'] == 1:
                c['nerr'] += 1
            if d['hro'] == 1:
                c.update(comp=t, hresp=d['hresp'], hrdata=d['hrdata'],
                         err1=pr is not None and pr['hresp'] == 1 and pr['hro'] == 0)
                s.cur = None
        if s.idle:
            if not (d['hro'] == 1 and d['hresp'] == 0):
                s.bad('idle_busy_zero_wait', f"hreadyout={d['hro']} hresp={d['hresp']}")
            s.idle = False
        if d['hsel'] == 1 and d['hready'] == 1:
            if d['htrans'] >= 2:
                x = dict(acc=t, addr=d['haddr'], write=d['hwrite'], size=d['hsize'], burst=d['hburst'],
                         prot=d['hprot'], ns=d['hns'], lock=d['hlock'], trans=d['htrans'], nerr=0,
                         comp=None, hresp=None, hrdata=None, err1=False, wd0=None)
                s.x.append(x)
                s.cur = x
            elif d['htrans'] >= 0:
                s.idle = True
        for ch in ('aw', 'ar'):
            if d[ch + 'valid'] == 1 and s.v0[ch] is None:
                s.v0[ch] = t
        if d['awvalid'] == 1 and d['awready'] == 1:
            s.aw.append(dict(t=t, v0=s.v0['aw'], id=d['awid'], addr=d['awaddr'], len=d['awlen'],
                             size=d['awsize'], burst=d['awburst'], cache=d['awcache'], prot=d['awprot']))
            s.v0['aw'] = None
        if d['wvalid'] == 1 and d['wready'] == 1:
            s.w.append(dict(t=t, data=d['wdata'], strb=d['wstrb'], last=d['wlast']))
        if d['bvalid'] == 1 and d['bready'] == 1:
            s.b.append(dict(t=t, id=d['bid'], resp=d['bresp']))
        if d['arvalid'] == 1 and d['arready'] == 1:
            s.ar.append(dict(t=t, v0=s.v0['ar'], id=d['arid'], addr=d['araddr'], len=d['arlen'],
                             size=d['arsize'], burst=d['arburst'], cache=d['arcache'], prot=d['arprot']))
            s.v0['ar'] = None
        if d['rvalid'] == 1 and d['rready'] == 1:
            s.r.append(dict(t=t, id=d['rid'], data=d['rdata'], resp=d['rresp'], last=d['rlast']))


# ----------------------------------------------------------------- AHB manager driver
def ent(trans=IDLE, addr=0, write=0, size=2, burst=SINGLE, prot=(WB_A << 2) | 3, ns=0, lock=0,
        wdata=0, wstrb=0, sel=1, grp=None):
    return dict(trans=trans, addr=addr & 0xFFFFFFFF, write=write, size=size, burst=burst, prot=prot,
                ns=ns, lock=lock, wdata=wdata, wstrb=wstrb, sel=sel, grp=grp)


def idles(n, sel=1):
    return [ent(sel=sel) for _ in range(n)]


def vchange(sig):
    vc = getattr(sig, "value_change", None)
    if vc is not None:
        return vc
    from cocotb.triggers import Edge
    return Edge(sig)


class Ahb:
    def __init__(s, dut, mon):
        s.dut, s.mon = dut, mon
        s.q = deque()
        s.ap = s.dp = None
        s.pause = False
        s.cancel_on_error = False
        s.mirror = True
        s.drive(None)

    def drive(s, e):
        e = e or ent()
        d = s.dut
        d.i_ahb_hsel.value = e['sel']
        d.i_ahb_htrans.value = e['trans']
        d.i_ahb_haddr.value = e['addr']
        d.i_ahb_hwrite.value = e['write']
        d.i_ahb_hsize.value = e['size']
        d.i_ahb_hburst.value = e['burst']
        d.i_ahb_hprot.value = e['prot']
        d.i_ahb_hnonsec.value = e['ns']
        d.i_ahb_hmastlock.value = e['lock']

    def reset(s):
        s.q.clear()
        s.ap = s.dp = None
        s.drive(None)

    def done(s):
        return not s.q and s.ap is None and s.dp is None

    def set_mirror(s, on):
        s.mirror = on
        if on:
            v = val(s.dut.o_ahb_hreadyout)
            s.dut.i_ahb_hready.value = 1 if v is None else v

    async def mirror_run(s):
        h = s.dut.o_ahb_hreadyout
        s.set_mirror(s.mirror)
        while True:
            await vchange(h)
            if s.mirror:
                v = val(h)
                s.dut.i_ahb_hready.value = 1 if v is None else v

    async def run(s):
        d = s.dut
        while True:
            await FallingEdge(d.i_clk_core)
            if s.pause:
                continue
            if val(d.i_rst_n_core) != 1:
                s.ap = s.dp = None
                s.drive(None)
                continue
            m = s.mon.last
            if m is None or m['rst'] != 1 or m['hready'] == 1:
                ok = m is not None and m['rst'] == 1
                s.dp = s.ap if (ok and s.ap is not None and s.ap['sel'] == 1 and s.ap['trans'] >= 2) else None
                if s.dp is not None and s.dp['write']:
                    d.i_ahb_hwdata.value = s.dp['wdata']
                    d.i_ahb_hwstrb.value = s.dp['wstrb']
                else:
                    d.i_ahb_hwstrb.value = 0
                s.ap = s.q.popleft() if s.q else None
                s.drive(s.ap)
            elif m['hresp'] == 1 and m['hro'] == 0 and s.cancel_on_error and s.dp is not None:
                g = s.dp['grp']
                if s.ap is not None and s.ap['grp'] == g:
                    s.ap = None
                    s.drive(None)
                while s.q and s.q[0]['grp'] == g:
                    s.q.popleft()


# ----------------------------------------------------------------- AXI subordinate model
def rgen(r, spec):
    kind, a = spec
    while True:
        if kind == 'c':
            yield a
        else:
            for _ in range(r.randint(0, a)):
                yield 0
            for _ in range(r.randint(1, 3)):
                yield 1


class Axi:
    def __init__(s, dut, mon, r):
        s.d, s.mon, s.r = dut, mon, r
        s.enabled = True
        s.berr, s.rerr, s.rdata = {}, {}, {}
        s.hold_b = s.hold_r = False
        s.cfg()
        s.reset()

    def cfg(s, ready=(('c', 1),) * 3, bdel=(0, 0), rdel=(0, 0), perr=0.0):
        s.gens = [rgen(s.r, sp) for sp in ready]
        s.bdel, s.rdel, s.perr = bdel, rdel, perr

    def reset(s):
        s.awq, s.wl, s.bq, s.rq = deque(), deque(), deque(), deque()
        s.bcur = s.rcur = None
        s.lt = -1
        s.d.i_axi_bvalid.value = 0
        s.d.i_axi_rvalid.value = 0

    def resp(s, addrs, tbl):
        for a in addrs:
            if a in tbl:
                return tbl.pop(a)
        if s.perr and s.r.random() < s.perr:
            return s.r.choice((EXOKAY, SLVERR, DECERR))
        return OKAY

    async def run(s):
        d = s.d
        while True:
            await FallingEdge(d.i_clk_core)
            if not s.enabled:
                continue
            for g, h in zip(s.gens, (d.i_axi_awready, d.i_axi_wready, d.i_axi_arready)):
                h.value = next(g)
            if val(d.i_rst_n_core) != 1:
                continue
            m = s.mon.last
            if m is not None and m['rst'] == 1 and m['t'] != s.lt:
                s.lt = t = m['t']
                if m['awvalid'] == 1 and m['awready'] == 1:
                    s.awq.append((t, m['awid'], axi_beats(m['awaddr'], m['awlen'], m['awsize'], m['awburst'])))
                if m['wvalid'] == 1 and m['wready'] == 1 and m['wlast'] == 1:
                    s.wl.append(t)
                if m['bvalid'] == 1 and m['bready'] == 1:
                    s.bcur = None
                if m['rvalid'] == 1 and m['rready'] == 1:
                    s.rcur = None
                if m['arvalid'] == 1 and m['arready'] == 1:
                    a = m['araddr']
                    dv = s.rdata.pop(a) if a in s.rdata else s.r.getrandbits(32)
                    s.rq.append((t + s.r.randint(*s.rdel), m['arid'], dv, s.resp([a], s.rerr)))
                while s.awq and s.wl:
                    ta, aid, addrs = s.awq.popleft()
                    tw = s.wl.popleft()
                    s.bq.append((max(ta, tw) + s.r.randint(*s.bdel), aid, s.resp(addrs, s.berr)))
            now = s.mon.t
            if s.bcur is None and s.bq and not s.hold_b and now >= s.bq[0][0]:
                s.bcur = s.bq.popleft()
                d.i_axi_bvalid.value = 1
                d.i_axi_bid.value = s.bcur[1]
                d.i_axi_bresp.value = s.bcur[2]
            elif s.bcur is None:
                d.i_axi_bvalid.value = 0
            if s.rcur is None and s.rq and not s.hold_r and now >= s.rq[0][0]:
                s.rcur = s.rq.popleft()
                d.i_axi_rvalid.value = 1
                d.i_axi_rid.value = s.rcur[1]
                d.i_axi_rdata.value = s.rcur[2]
                d.i_axi_rresp.value = s.rcur[3]
                d.i_axi_rlast.value = 1
            elif s.rcur is None:
                d.i_axi_rvalid.value = 0


# ----------------------------------------------------------------- stimulus generation
_G = [0]


def newgrp():
    _G[0] += 1
    return _G[0]


def rand_addr(r, size):
    c = r.random()
    a = 0 if c < 0.03 else 0xFFFFFFFC if c < 0.06 else r.getrandbits(32)
    return a & ~((1 << size) - 1) & 0xFFFFFFFF


def burst_addrs(r, burst, size, n=None, start=None):
    sz = 1 << size
    N = BLEN[burst] or n or 1
    if burst in WRAPS:
        a0 = rand_addr(r, size) if start is None else start
        tot = N * sz
        base = a0 & ~(tot - 1)
        return [base + ((a0 - base + i * sz) % tot) for i in range(N)]
    if start is None:
        span = N * sz
        c = r.random()
        blk = 0 if c < 0.05 else 0xFFFFFC00 if c < 0.1 else r.getrandbits(22) << 10
        slots = (1024 - span) // sz
        off = r.choice((0, slots)) if r.random() < 0.2 else r.randint(0, slots)
        start = blk + off * sz
    return [(start + i * sz) & 0xFFFFFFFF for i in range(N)]


def mk(r, write, burst=SINGLE, size=2, mt=WB_A, n=None, busy=0.0, start=None, plo=None, ns=None,
       vary=None, k=None):
    g = newgrp()
    addrs = burst_addrs(r, burst, size, n, start)
    if k is not None:
        addrs = addrs[:k]
    plo = r.randrange(4) if plo is None else plo
    ns = r.randrange(2) if ns is None else ns
    out = []
    for i, a in enumerate(addrs):
        p, nsi = (mt << 2) | plo, ns
        if vary == 'ns':
            nsi = ns ^ (i & 1)
        if vary == 'p0':
            p ^= (i & 1)
        e = ent(NONSEQ if i == 0 else SEQ, a, write, size, burst, p, nsi, 0, r.getrandbits(32),
                r.getrandbits(4) & lanes(a, size), grp=g)
        if i > 0 and busy and r.random() < busy:
            for _ in range(r.randint(1, 2)):
                bz = dict(e)
                bz['trans'] = BUSY
                out.append(bz)
        out.append(e)
    return out


def mk_rej(r, write, kind=None, arg=None):
    """Deliberately illegal (rejected) NONSEQ SINGLE transfer."""
    kind = kind or r.choice(('lock', 'p6', 'mt', 'size', 'mis'))
    a = rand_addr(r, 2) & 0xFFFFFF80
    size, lock, p = 2, 0, (WB_A << 2) | r.randrange(4)
    if kind == 'lock':
        lock = 1
    elif kind == 'p6':
        p |= 0x40
    elif kind == 'mt':
        p = ((arg if arg is not None else r.choice(RESERVED_52)) << 2) | r.randrange(4)
    elif kind == 'size':
        size = arg if arg is not None else r.randint(3, 7)
        a &= ~((1 << size) - 1)
    else:
        size, low = arg if arg is not None else r.choice(((1, 1), (1, 3), (2, 1), (2, 2), (2, 3)))
        a = (a & ~3) | low
    return ent(NONSEQ, a, write, size, SINGLE, p, r.randrange(2), lock, r.getrandbits(32),
               r.getrandbits(4), grp=newgrp())


def nbeats(items):
    return sum(1 for e in items if e['trans'] >= 2 and e['sel'] == 1)


def rand_traffic(r, n, rd=True, wr=True, rej=0.0, busy=0.2, bursts=range(8), mts=LEGAL_MT, gap=0.3):
    out, c = [], 0
    while c < n:
        w = (r.random() < 0.5) if (rd and wr) else wr
        if rej and r.random() < rej:
            out.append(mk_rej(r, int(w)))
            c += 1
        else:
            es = mk(r, int(w), r.choice(list(bursts)), r.randrange(3), r.choice(mts), n=r.randint(1, 8), busy=busy)
            out += es
            c += nbeats(es)
        if r.random() < gap:
            out += idles(r.randint(1, 3))
    return out


# ----------------------------------------------------------------- environment helpers
async def waitc(dut, cond, n, what):
    for _ in range(int(n)):
        if cond():
            return
        await FallingEdge(dut.i_clk_core)
    assert cond(), f"timeout after {n} cycles waiting for {what}"


class Env:
    def __init__(s, dut, salt):
        s.dut = dut
        s.r = rng(salt)
        s.mon = Mon(dut)
        s.drv = Ahb(dut, s.mon)
        s.axi = Axi(dut, s.mon, rng(f"{salt}-axi"))

    def quiet(s):
        m, l = s.mon, s.mon.last
        return (l is not None and len(m.b) == len(m.aw) and len(m.r) == len(m.ar)
                and l['awvalid'] != 1 and l['wvalid'] != 1 and l['arvalid'] != 1)

    async def run(s, items, maxc=None):
        s.drv.q.extend(items)
        await waitc(s.dut, s.drv.done, maxc or 400 + 400 * len(items), "AHB transfers to complete")
        await waitc(s.dut, s.quiet, 3000, "AXI responses to drain")


async def setup(dut, salt, **kw):
    start_clock(dut)
    await reset_dut(dut, cycles=5, idle={"i_ahb_hready": 1})
    e = Env(dut, salt)
    e.axi.cfg(**kw)
    for c in (e.mon.run(), e.drv.run(), e.drv.mirror_run(), e.axi.run()):
        cocotb.start_soon(c)
    await next_cycle(dut, 2)
    return e


async def do_reset(e, cycles=4):
    """Coordinated reset of bridge, AHB manager model and AXI subordinate model."""
    d = e.dut
    d.i_rst_n_core.value = 0
    e.axi.reset()
    e.drv.reset()
    await next_cycle(d, max(cycles - 1, 1))
    await RisingEdge(d.i_clk_core)
    d.i_rst_n_core.value = 1
    await next_cycle(d, 1)


async def watch(e, n):
    e.mon.trace = []
    await next_cycle(e.dut, n)
    tr, e.mon.trace = e.mon.trace, None
    return tr


async def idle_window(e, n, tag):
    tr = await watch(e, n)
    assert len(tr) >= n - 1, f"{tag}: expected {n} post-reset cycles got {len(tr)}"
    for (t, hro, hresp, awv, wv, arv) in tr:
        assert awv == 0 and wv == 0 and arv == 0, f"{tag}: no AXI VALID in IDLE window expected got aw={awv} w={wv} ar={arv} @{t}"
        assert hro == 1 and hresp == 0, f"{tag}: HREADYOUT=1/HRESP=0 expected in IDLE window got {hro}/{hresp} @{t}"


def chk_rst_now(dut, tag):
    for k, p in SIGS:
        if k in RST_VAL:
            v = val(getattr(dut, p))
            assert v == RST_VAL[k], f"{tag}: {p} expected reset value {RST_VAL[k]} got {v}"


def check_rot(ids, cnt, ch):
    assert all(0 <= i < cnt for i in ids), f"CHK-009/CHK-032: {ch} IDs expected in 0..{cnt - 1} got {sorted(set(ids))}"
    w = 2 * cnt
    for i in range(len(ids) - w + 1):
        st = set(ids[i:i + w])
        assert len(st) == cnt, f"CHK-032: {ch} handshakes {i}..{i + w - 1} expected all IDs 0..{cnt - 1} got {sorted(st)}"


# ----------------------------------------------------------------- reference model / scoreboard
def check_all(e, tag):
    m = e.mon
    X = m.x
    RD, WR = P("PARA_RD_ID_COUNT"), P("PARA_WR_ID_COUNT")
    for k, v in m.viol.items():
        assert not v, f"{tag}: protocol checker '{k}' expected no violation got {v[:3]}"
    groups, g = [], None
    for x in X:
        x['rej'] = rejected(x)
        if g is None or x['rej'] or x['trans'] == NONSEQ or g[0]['rej'] or g[0]['write'] != x['write']:
            g = [x]
            groups.append(g)
        else:
            g.append(x)
        x['g'] = len(groups) - 1
    for x in X:
        assert x['comp'] is not None, f"{tag}: transfer accepted at edge {x['acc']} expected to complete got none"
        if x['rej']:
            assert x['hresp'] == 1 and x['err1'] and x['nerr'] == 2, (
                f"CHK-017/CHK-030 ({tag}): rejected transfer @{x['acc']} addr={x['addr']:#x} expected two-cycle "
                f"ERROR got hresp={x['hresp']} first_cycle={x['err1']} err_cycles={x['nerr']}")
    # reads
    rds = [x for x in X if not x['write'] and not x['rej']]
    AR, R = m.ar, m.r
    assert len(AR) == len(rds), f"CHK-037/CHK-033 ({tag}): expected {len(rds)} AR handshakes got {len(AR)}"
    assert len(R) == len(AR), f"CHK-033 ({tag}): expected {len(AR)} R handshakes got {len(R)}"
    for i, (x, a, rr) in enumerate(zip(rds, AR, R)):
        exp = (x['addr'], x['size'], 0, 1, mapprot(x['prot'], x['ns']), arcache(x['prot']))
        got = (a['addr'], a['size'], a['len'], a['burst'], a['prot'], a['cache'])
        assert got == exp, f"CHK-037 ({tag}): read #{i} AR (addr,size,len,burst,prot,cache) expected {exp} got {got}"
        assert (a['v0'] or 0) > x['acc'], f"CHK-013 ({tag}): ARVALID expected after acceptance edge {x['acc']} got {a['v0']}"
        assert 0 <= a['id'] < RD, f"CHK-009 ({tag}): ARID expected < {RD} got {a['id']}"
        x['ar'] = a
        assert x['acc'] < rr['t'] <= x['comp'], f"CHK-015 ({tag}): R handshake expected in ({x['acc']},{x['comp']}] got {rr['t']}"
        if rr['resp'] == OKAY:
            assert x['hresp'] == 0 and x['nerr'] == 0 and x['hrdata'] == rr['data'], (
                f"CHK-015/CHK-037 ({tag}): read #{i} expected OKAY hrdata={rr['data']:#x} got hresp={x['hresp']} hrdata={x['hrdata']:#x}")
        else:
            assert x['hresp'] == 1 and x['err1'], f"CHK-029 ({tag}): RRESP={rr['resp']} expected two-cycle ERROR got hresp={x['hresp']}"
    # writes
    wbs = [x for x in X if x['write'] and not x['rej']]
    W, AW, B = m.w, m.aw, m.b
    assert len(W) == len(wbs), f"CHK-033/CHK-040 ({tag}): expected {len(wbs)} W beats got {len(W)}"
    for i, (x, w) in enumerate(zip(wbs, W)):
        assert (w['data'], w['strb']) == x['wd0'], f"CHK-040 ({tag}): W beat #{i} (data,strb) expected {x['wd0']} got {(w['data'], w['strb'])}"
    j = 0
    for k, a in enumerate(AW):
        n = a['len'] + 1
        bt = wbs[j:j + n]
        assert len(bt) == n, f"CHK-010 ({tag}): AW #{k} len={a['len']} expected {n} AHB beats got {len(bt)}"
        assert 0 <= a['id'] < WR, f"CHK-009 ({tag}): AWID expected < {WR} got {a['id']}"
        assert a['burst'] in (1, 2) and a['len'] <= 15, f"CHK-011 ({tag}): AW burst/len illegal got {a['burst']}/{a['len']}"
        assert a['burst'] == 2 or (a['addr'] % 4096) + n * (1 << a['size']) <= 4096, f"CHK-011 ({tag}): AW #{k} crosses 4KiB addr={a['addr']:#x} len={a['len']}"
        exp = axi_beats(a['addr'], a['len'], a['size'], a['burst'])
        for i, x in enumerate(bt):
            e1 = (x['addr'], x['size'], mapprot(x['prot'], x['ns']), awcache(x['prot']))
            g1 = (exp[i], a['size'], a['prot'], a['cache'])
            assert e1 == g1, f"CHK-040/CHK-024 ({tag}): AW #{k} beat {i} (addr,size,prot,cache) expected {e1} got {g1}"
            x['aw'] = k
        for i in range(n):
            assert W[j + i]['last'] == int(i == n - 1), f"CHK-010 ({tag}): AW #{k} beat {i} WLAST expected {int(i == n - 1)} got {W[j + i]['last']}"
        if n > 1:
            G = groups[bt[0]['g']]
            assert all(x['g'] == bt[0]['g'] for x in bt) and eligible(G), f"CHK-023/024/025/026 ({tag}): AW #{k} len={a['len']} expected only for a complete eligible Normal WB fixed burst"
            assert (a['v0'] or 0) > max(x['acc'] for x in G), f"CHK-014/CHK-024 ({tag}): burst AWVALID expected after last beat accept {max(x['acc'] for x in G)} got {a['v0']}"
            if a['burst'] == 2:
                assert n == len(G) and a['addr'] == G[0]['addr'], f"CHK-024 ({tag}): WRAP AW expected whole burst from first beat got len={a['len']} addr={a['addr']:#x}"
        else:
            assert a['burst'] == 1, f"CHK-040 ({tag}): single AW expected AWBURST=INCR got {a['burst']}"
        j += n
    assert j == len(wbs), f"CHK-033 ({tag}): AWs expected to cover {len(wbs)} write beats got {j}"
    assert len(B) == len(AW), f"CHK-033 ({tag}): expected {len(AW)} B handshakes got {len(B)}"
    for x in wbs:
        G = groups[x['g']]
        wbf = is_wb(x) and BLEN[x['burst']] > 1
        if wbf and x is not G[-1]:
            assert x['hresp'] == 0 and x['nerr'] == 0, f"CHK-024/CHK-028 ({tag}): non-terminal WB beat @{x['acc']} expected OKAY got hresp={x['hresp']}"
            continue
        ks = {y['aw'] for y in G} if wbf else {x['aw']}
        tb = max(B[k]['t'] for k in ks)
        err = any(B[k]['resp'] != OKAY for k in ks)
        assert x['comp'] >= tb, f"CHK-016 ({tag}): write @{x['acc']} expected completion at/after B edge {tb} got {x['comp']}"
        assert x['hresp'] == int(err) and (x['err1'] if err else x['nerr'] == 0), (
            f"CHK-016/CHK-028 ({tag}): write @{x['acc']} expected hresp={int(err)} (two-cycle if ERROR) got hresp={x['hresp']} err_cycles={x['nerr']}")
    lastw = None
    for x in X:
        if x['rej']:
            continue
        if x['write']:
            lastw = x
        elif lastw is not None:
            assert AW[lastw['aw']]['t'] <= x['ar']['t'], f"CHK-033 ({tag}): read @{x['acc']} AR at {x['ar']['t']} expected not before AW of earlier write at {AW[lastw['aw']]['t']}"
    return groups


# =================================================================== tests
@cocotb.test()
async def test_chk_021_accept_qualifiers(dut):
    """CHK-021: only HSEL&HREADY&HTRANS[1] address phases create AXI traffic; IDLE/BUSY zero-wait OKAY."""
    e = await setup(dut, 'chk021', ready=(('r', 3),) * 3, bdel=(0, 5), rdel=(0, 5))
    r, m = e.r, e.mon
    t0, nx = m.t, len(m.x)
    items = [ent(IDLE, rand_addr(r, 2), r.randrange(2), r.randrange(3), r.randrange(8),
                 (r.choice(LEGAL_MT) << 2) | r.randrange(4), r.randrange(2)) for _ in range(50)]
    await e.run(items)
    assert len(m.x) == nx, f"CHK-021: IDLE cycles expected no accepted transfer got {len(m.x) - nx}"
    v = [t for t in m.validt if t > t0]
    assert not v, f"CHK-021: IDLE cycles expected no AXI VALID got at edges {v[:5]}"
    t0, nx = m.t, len(m.x)
    items = []
    for _ in range(30):
        x = mk(r, r.randrange(2), SINGLE, r.randrange(3), r.choice(LEGAL_MT))[0]
        x['sel'] = 0
        items.append(x)
    await e.run(items)
    v = [t for t in m.validt if t > t0]
    assert len(m.x) == nx and not v, f"CHK-021: HSEL=0 NONSEQ expected no AXI VALID got {v[:5]}"
    nx, nar, nw = len(m.x), len(m.ar), len(m.w)
    items = []
    for _ in range(24):
        items += mk(r, r.randrange(2), r.choice((INCR, INCR4)), r.randrange(3), r.choice(LEGAL_MT),
                    n=r.randint(1, 6), busy=0.5)
    await e.run(items)
    acc = m.x[nx:]
    assert len(acc) == nbeats(items), f"CHK-021: expected {nbeats(items)} accepted beats got {len(acc)}"
    nrd = sum(1 for x in acc if not x['write'])
    assert len(m.ar) - nar == nrd, f"CHK-021: AR handshakes expected {nrd} got {len(m.ar) - nar}"
    assert len(m.w) - nw == len(acc) - nrd, f"CHK-021: W beats expected {len(acc) - nrd} got {len(m.w) - nw}"
    # (4) external wait states with HSEL=1 NONSEQ held
    e.drv.pause = True
    e.drv.set_mirror(False)
    nx, nar = len(m.x), len(m.ar)
    A = rand_addr(r, 2)
    dut.i_ahb_hready.value = 0
    e.drv.drive(ent(NONSEQ, A, 0, 2, SINGLE, (WB_A << 2) | 1, 0))
    await next_cycle(dut, 3)
    assert len(m.x) == nx, "CHK-021: HREADY=0 cycles expected no acceptance got one"
    dut.i_ahb_hready.value = 1
    await next_cycle(dut, 1)
    tacc = m.last['t']
    e.drv.drive(None)
    e.drv.set_mirror(True)
    e.drv.pause = False
    await waitc(dut, lambda: len(m.x) > nx and m.x[-1]['comp'] is not None, 500, "CHK-021 (4) read completion")
    await waitc(dut, e.quiet, 500, "AXI quiet")
    assert len(m.x) - nx == 1 and m.x[nx]['acc'] == tacc, f"CHK-021: one acceptance at edge {tacc} expected got {[x['acc'] for x in m.x[nx:]]}"
    assert len(m.ar) - nar == 1 and m.ar[-1]['addr'] == A, f"CHK-021: exactly one AR to {A:#x} expected got {len(m.ar) - nar}"
    check_all(e, 'CHK-021')


async def toggler(e, st):
    d = e.dut
    hs = [getattr(d, p) for p in AXI_OUTS]
    rd = [d.i_axi_awready, d.i_axi_wready, d.i_axi_arready]
    while True:
        await FallingEdge(d.i_clk_core)
        await Timer(1, "step")
        if 1 not in (val(d.o_axi_awvalid), val(d.o_axi_wvalid), val(d.o_axi_arvalid)):
            continue
        before = [val(h) for h in hs]
        orig = [val(x) or 0 for x in rd]
        for x, o in zip(rd, orig):
            x.value = 1 - o
        await Timer(1, "step")
        after = [val(h) for h in hs]
        for x, o in zip(rd, orig):
            x.value = o
        st['n'] += 1
        if before != after:
            st['bad'].append([(AXI_OUTS[i], before[i], after[i]) for i in range(len(hs)) if before[i] != after[i]])


@cocotb.test()
async def test_chk_022_no_comb_ready_path(dut):
    """CHK-022: AXI outputs have no combinational dependency on AXI READY inputs."""
    e = await setup(dut, 'chk022', ready=(('r', 4),) * 3, bdel=(0, 6), rdel=(0, 6))
    st = {'n': 0, 'bad': []}
    cocotb.start_soon(toggler(e, st))
    await e.run(rand_traffic(e.r, 400, busy=0.1))
    assert st['n'] > 0, "CHK-022: expected at least one toggle with a VALID high got 0"
    assert not st['bad'], f"CHK-022: AXI outputs expected unchanged by mid-cycle READY toggle got {st['bad'][:3]}"
    check_all(e, 'CHK-022')


@cocotb.test()
async def test_chk_023_device_bursts_singles(dut):
    """CHK-023: Device-nE / Device-E fixed write bursts are serialized as singles waiting for each BRESP."""
    e = await setup(dut, 'chk023', ready=(('c', 1),) * 3, bdel=(0, 20))
    r, m = e.r, e.mon
    items = []
    for mt in (DEV_NE, DEV_E):
        for b in FIXED:
            for sz in range(3):
                items += mk(r, 1, b, sz, mt) + idles(r.randint(0, 2))
    await e.run(items)
    check_all(e, 'CHK-023')
    assert all(a['len'] == 0 for a in m.aw), "CHK-023: every AW expected AWLEN=0 got a burst"
    for k in range(1, len(m.aw)):
        assert m.aw[k]['t'] >= m.b[k - 1]['t'], f"CHK-023: AW #{k} at {m.aw[k]['t']} expected not before B #{k - 1} at {m.b[k - 1]['t']}"
    assert all(x['hresp'] == 0 for x in m.x), "CHK-023: all beats expected OKAY"


@cocotb.test()
async def test_chk_024_wb_burst_aggregation(dut):
    """CHK-024: eligible Normal Write-back fixed write bursts: aggregated or singles, terminal waits for B."""
    e = await setup(dut, 'chk024')
    r, m = e.r, e.mon
    for rdy in (('c', 1), ('r', 6)):
        e.axi.cfg(ready=(rdy,) * 3, bdel=(1, 20))
        items = []
        for b in FIXED:
            for sz in range(3):
                items += mk(r, 1, b, sz, r.choice((WB_A, WB_B)))
        await e.run(items + idles(2))
    G = check_all(e, 'CHK-024')
    cov = {}
    for g in G:
        x0 = g[0]
        N = BLEN[x0['burst']]
        if not x0['write'] or N < 4:
            continue
        assert len(g) == N, f"CHK-024: burst expected {N} beats got {len(g)}"
        aws = sorted({x['aw'] for x in g})
        if len(aws) == 1:
            a = m.aw[aws[0]]
            exp = (N - 1, x0['addr'], 2 if x0['burst'] in WRAPS else 1, x0['size'])
            assert (a['len'], a['addr'], a['burst'], a['size']) == exp, f"CHK-024: aggregated AW expected {exp} got {(a['len'], a['addr'], a['burst'], a['size'])}"
            kind = 'aggregated'
        else:
            assert len(aws) == N and all(m.aw[k]['len'] == 0 for k in aws), f"CHK-024: singles expected {N} AWLEN=0 got {len(aws)}"
            kind = 'singles'
        tp = all(g[i + 1]['acc'] - g[i]['acc'] == 1 for i in range(N - 2))
        cov[(x0['burst'], kind)] = cov.get((x0['burst'], kind), 0) + 1
        cov[('one_beat_per_cycle', tp)] = cov.get(('one_beat_per_cycle', tp), 0) + 1
    dut._log.info(f"CHK-024 coverage: {cov}")


@cocotb.test()
async def test_chk_025_varying_attrs_singles(dut):
    """CHK-025: varying burst-scoped attributes force ordered singles carrying each beat's attributes."""
    e = await setup(dut, 'chk025', ready=(('c', 1),) * 3, bdel=(1, 8))
    r, m = e.r, e.mon
    res = []
    for vary, err in (('ns', False), ('p0', False), ('ns', True)):
        for b in (INCR4, WRAP8):
            es = mk(r, 1, b, 2, WB_A, vary=vary)
            if err:
                e.axi.berr[es[1]['addr']] = SLVERR
            nx = len(m.x)
            await e.run(es + idles(2))
            res.append((m.x[nx:], err))
    check_all(e, 'CHK-025')
    assert all(a['len'] == 0 for a in m.aw), "CHK-025: expected no AW with AWLEN>0 got one"
    for xs, err in res:
        assert xs[-1]['hresp'] == int(err), f"CHK-025: terminal beat expected hresp={int(err)} got {xs[-1]['hresp']}"


@cocotb.test()
async def test_chk_026_early_termination(dut):
    """CHK-026: early-terminated fixed write burst drains its captured prefix as singles."""
    e = await setup(dut, 'chk026', ready=(('r', 4),) * 3, bdel=(0, 10), rdel=(0, 10))
    r, m = e.r, e.mon
    items, cases = [], []
    for b in (INCR8, WRAP16):
        for k in range(1, BLEN[b]):
            es = mk(r, 1, b, 2, WB_A, k=k)
            err = len(cases) % 2 == 1
            if err:
                e.axi.berr[es[r.randrange(k)]['addr']] = r.choice((SLVERR, DECERR))
            term = idles(1) if k % 2 else [mk(r, 0, SINGLE, 2, r.choice(LEGAL_MT))[0]]
            items += es + term + idles(2)
            cases.append((k, err))
    await e.run(items)
    G = check_all(e, 'CHK-026')
    wg = [g for g in G if g[0]['write']]
    assert len(wg) == len(cases), f"CHK-026: expected {len(cases)} write groups got {len(wg)}"
    for g, (k, err) in zip(wg, cases):
        aws = {x['aw'] for x in g}
        assert len(g) == k and len(aws) == k and all(m.aw[a]['len'] == 0 for a in aws), f"CHK-026: k={k} expected {k} AWLEN=0 singles got {len(aws)}"
        assert g[-1]['hresp'] == int(err), f"CHK-026: terminal beat k={k} expected hresp={int(err)} got {g[-1]['hresp']}"


@cocotb.test()
async def test_chk_027_4k_split(dut):
    """CHK-027: defensive 4 KiB split keeps beat order and aggregates responses on the final beat."""
    e = await setup(dut, 'chk027', ready=(('c', 1),) * 3, bdel=(1, 5))
    r, m = e.r, e.mon
    for run_i in (0, 1):
        for start, sz, b in ((0xFE0, 2, INCR16), (0x1FF8, 1, INCR8)):
            es = mk(r, 1, b, sz, WB_A, start=start)
            if run_i:
                e.axi.berr[start] = SLVERR
            nx, naw = len(m.x), len(m.aw)
            await e.run(es + idles(3))
            xs = m.x[nx:]
            covered = [ad for a in m.aw[naw:] for ad in axi_beats(a['addr'], a['len'], a['size'], a['burst'])]
            assert covered == [x['addr'] for x in xs], f"CHK-027: AW beats expected {[hex(x['addr']) for x in xs]} got {[hex(c) for c in covered]}"
            assert xs[-1]['hresp'] == run_i, f"CHK-027: terminal beat expected hresp={run_i} got {xs[-1]['hresp']}"
    check_all(e, 'CHK-027')


@cocotb.test()
async def test_chk_028_bresp_errors(dut):
    """CHK-028: BRESP error mapping, terminal aggregation, Device-E cancel, no retry."""
    e = await setup(dut, 'chk028', ready=(('r', 3),) * 3, bdel=(0, 10))
    r, m = e.r, e.mon
    e.drv.cancel_on_error = True
    for ctrl in (False, True):
        for resp in (SLVERR, DECERR, EXOKAY):
            for _ in range(3):
                es = mk(r, 1, SINGLE, 2, r.choice(LEGAL_MT))
                if not ctrl:
                    e.axi.berr[es[0]['addr']] = resp
                nx = len(m.x)
                await e.run(es + idles(1))
                assert m.x[nx]['hresp'] == int(not ctrl), f"CHK-028(a): BRESP={resp} expected hresp={int(not ctrl)} got {m.x[nx]['hresp']}"
        for b in FIXED:
            es = mk(r, 1, b, 2, r.choice((WB_A, WB_B)))
            if not ctrl:
                e.axi.berr[es[r.randrange(len(es))]['addr']] = r.choice((SLVERR, DECERR, EXOKAY))
            nx = len(m.x)
            await e.run(es + idles(1))
            xs = m.x[nx:]
            assert xs[-1]['hresp'] == int(not ctrl) and all(x['hresp'] == 0 for x in xs[:-1]), f"CHK-028(b): expected terminal hresp={int(not ctrl)} others OKAY got {[x['hresp'] for x in xs]}"
        es = mk(r, 1, INCR4, 2, DEV_E)
        if not ctrl:
            e.axi.berr[es[1]['addr']] = SLVERR
        nx, naw = len(m.x), len(m.aw)
        await e.run(es + idles(2))
        xs = m.x[nx:]
        covered = {ad for a in m.aw[naw:] for ad in axi_beats(a['addr'], a['len'], a['size'], a['burst'])}
        if not ctrl:
            assert len(xs) == 2 and [x['hresp'] for x in xs] == [0, 1], f"CHK-028(c): expected beats [OKAY, ERROR] then cancel got {[x['hresp'] for x in xs]}"
            assert es[2]['addr'] not in covered and es[3]['addr'] not in covered, "CHK-028(c): expected no AXI request for cancelled beats 3..4 got one"
        else:
            assert len(xs) == 4 and all(x['hresp'] == 0 for x in xs), "CHK-028(d): Device-E control expected 4 OKAY beats"
    check_all(e, 'CHK-028')


@cocotb.test()
async def test_chk_029_rresp_errors(dut):
    """CHK-029: non-OKAY RRESP consumed and returned as two-cycle ERROR, no retry."""
    e = await setup(dut, 'chk029', ready=(('r', 3),) * 3, rdel=(0, 20))
    r, m = e.r, e.mon
    for resp in (SLVERR, DECERR, EXOKAY):
        for _ in range(2):
            A = mk(r, 0, SINGLE, 2, r.choice(LEGAL_MT))[0]
            Bx = mk(r, 0, SINGLE, 2, r.choice(LEGAL_MT))[0]
            e.axi.rerr[A['addr']] = resp
            dv = r.getrandbits(32)
            e.axi.rdata[Bx['addr']] = dv
            nx, nar, nr = len(m.x), len(m.ar), len(m.r)
            await e.run([A, Bx] + idles(2))
            xa, xb = m.x[nx], m.x[nx + 1]
            assert len(m.ar) - nar == 2 and len(m.r) - nr == 2, f"CHK-029: expected 2 AR and 2 R got {len(m.ar) - nar}/{len(m.r) - nr}"
            ra = m.r[nr]
            assert ra['resp'] == resp and xa['acc'] < ra['t'] <= xa['comp'], f"CHK-029: R handshake with RRESP={resp} expected in data phase got {ra}"
            assert xa['hresp'] == 1 and xa['err1'], f"CHK-029: expected two-cycle ERROR got hresp={xa['hresp']}"
            assert xb['hresp'] == 0 and xb['hrdata'] == dv, f"CHK-029: next read expected OKAY {dv:#x} got {xb['hresp']}/{xb['hrdata']:#x}"
    check_all(e, 'CHK-029')


@cocotb.test()
async def test_chk_030_rejected_controls(dut):
    """CHK-030: unsupported AHB controls -> two-cycle ERROR, no AXI request, next transfer OK."""
    e = await setup(dut, 'chk030', ready=(('c', 1),) * 3, rdel=(0, 3))
    r, m = e.r, e.mon
    kinds = [('lock', None), ('p6', None)] + [('mt', c) for c in (4, 5, 8, 12)] + \
            [('size', s) for s in range(3, 8)] + [('mis', a) for a in ((1, 1), (1, 3), (2, 1), (2, 2), (2, 3))]
    for kind, arg in kinds:
        for w in (0, 1):
            rj = mk_rej(r, w, kind, arg)
            rd = mk(r, 0, SINGLE, 2, r.choice(LEGAL_MT))[0]
            nx, nar = len(m.x), len(m.ar)
            await e.run([rj] + idles(16) + [rd] + idles(2))
            xr, xd = m.x[nx], m.x[nx + 1]
            assert xr['hresp'] == 1 and xr['err1'] and xr['nerr'] == 2, f"CHK-030: {kind}{arg} w={w} expected two-cycle ERROR got hresp={xr['hresp']} cycles={xr['nerr']}"
            v = [t for t in m.validt if xr['acc'] <= t <= xd['acc']]
            assert not v, f"CHK-030: {kind}{arg} expected no AXI VALID after rejection got at {v[:3]}"
            assert len(m.ar) - nar == 1 and xd['hresp'] == 0, f"CHK-030: following read expected one AR and OKAY got {len(m.ar) - nar}/{xd['hresp']}"
    check_all(e, 'CHK-030')


@cocotb.test()
async def test_chk_031_reject_after_prefix(dut):
    """CHK-031: rejected transfer after a captured write prefix: prefix drained first, then ERROR."""
    e = await setup(dut, 'chk031', ready=(('c', 1),) * 3, bdel=(1, 10))
    r, m = e.r, e.mon
    runs = [(k, w, False) for w in (1, 0) for k in ('lock', 'p6', 'size', 'mis')] + [('lock', 1, True)]
    for kind, w, derr in runs:
        es = mk(r, 1, INCR8, 2, WB_A, k=3)
        arg = 3 if kind == 'size' else (2, r.randint(1, 3)) if kind == 'mis' else None
        rj = mk_rej(r, w, kind, arg)
        if derr:
            e.axi.berr[es[1]['addr']] = DECERR
        nx, naw, nb, nar = len(m.x), len(m.aw), len(m.b), len(m.ar)
        await e.run(es + [rj] + idles(3))
        xs, aws, bs = m.x[nx:nx + 4], m.aw[naw:], m.b[nb:]
        assert len(aws) == 3 and all(a['len'] == 0 for a in aws), f"CHK-031: expected 3 AWLEN=0 got {[a['len'] for a in aws]}"
        assert [a['addr'] for a in aws] == [x['addr'] for x in es], "CHK-031: AW addresses expected beats 1..3 in order"
        assert len(bs) == 3 and xs[2]['comp'] >= bs[2]['t'], f"CHK-031: beat 3 expected completion at/after 3rd B {bs[-1]['t'] if bs else None} got {xs[2]['comp']}"
        assert xs[2]['hresp'] == int(derr), f"CHK-031: beat 3 expected hresp={int(derr)} got {xs[2]['hresp']}"
        assert xs[3]['hresp'] == 1 and xs[3]['err1'] and xs[3]['comp'] - 1 > bs[2]['t'], f"CHK-031: rejected {kind} expected ERROR after B edge {bs[2]['t']} got first error {xs[3]['comp'] - 1}"
        assert len(m.ar) == nar, "CHK-031: expected no AR for the rejected read"
    check_all(e, 'CHK-031')


@cocotb.test()
async def test_chk_032_id_rotation(dut):
    """CHK-032: AXI IDs rotate independently through 0..count-1 per direction."""
    RD, WR = P("PARA_RD_ID_COUNT"), P("PARA_WR_ID_COUNT")
    if (RD, WR) != (5, 8):
        not_verifiable(dut, "CHK-032", f"configuration PARA_RD_ID_COUNT=5/PARA_WR_ID_COUNT=8 is not elaborated "
                                       f"in this run (RD={RD}, WR={WR}); range and rotation checked with this run's counts")
    e = await setup(dut, 'chk032', ready=(('r', 3),) * 3, bdel=(0, 10), rdel=(0, 10))
    r, m = e.r, e.mon
    blocks = [mk(r, 0, SINGLE, r.randrange(3), r.choice(LEGAL_MT)) for _ in range(200)]
    blocks += [mk(r, 1, SINGLE, r.randrange(3), r.choice(LEGAL_MT)) for _ in range(200)]
    blocks += [mk(r, 1, INCR4, 2, WB_A) for _ in range(20)]
    r.shuffle(blocks)
    await e.run([x for b in blocks for x in b])
    check_all(e, 'CHK-032')
    check_rot([a['id'] for a in m.ar], RD, 'AR')
    check_rot([a['id'] for a in m.aw], WR, 'AW')
    dut._log.info(f"CHK-032 coverage AR ids {sorted({a['id'] for a in m.ar})} AW ids {sorted({a['id'] for a in m.aw})}")


@cocotb.test()
async def test_chk_033_mixed_ordering(dut):
    """CHK-033: mixed random traffic keeps order, no loss, no duplication."""
    e = await setup(dut, 'chk033', ready=(('r', 16),) * 3, bdel=(0, 30), rdel=(0, 30), perr=0.03)
    items = rand_traffic(e.r, 3000, rej=0.05, busy=0.15)
    await e.run(items)
    check_all(e, 'CHK-033')
    m = e.mon
    dut._log.info(f"CHK-033: AHB={len(m.x)} AR={len(m.ar)} W={len(m.w)} AW={len(m.aw)} "
                  f"rejected={sum(1 for x in m.x if x['rej'])}")


@cocotb.test()
async def test_chk_034_issue_latency(dut):
    """CHK-034: AR/AW issue latency <= 6 cycles with READY high and idle bridge."""
    e = await setup(dut, 'chk034', ready=(('c', 1),) * 3, bdel=(0, 0), rdel=(0, 0))
    r, m = e.r, e.mon

    async def go(items):
        nx, naw, nar = len(m.x), len(m.aw), len(m.ar)
        await e.run(items + idles(8))
        return m.x[nx:], m.aw[naw:], m.ar[nar:]
    for _ in range(4):
        xs, _, ars = await go(mk(r, 0, SINGLE, r.randrange(3), r.choice(LEGAL_MT)))
        l = ars[0]['t'] - xs[0]['acc']
        assert 1 <= l <= 6, f"CHK-034: single read AR latency expected 1..6 got {l}"
        xs, aws, _ = await go(mk(r, 1, SINGLE, r.randrange(3), r.choice(LEGAL_MT)))
        l = aws[0]['t'] - xs[0]['acc']
        assert 1 <= l <= 6, f"CHK-034: single write AW latency expected 1..6 got {l}"
        xs, aws, _ = await go(mk(r, 1, r.choice((INCR4, INCR8)), 2, DEV_E))
        assert len(aws) == len(xs), f"CHK-034: Device-E expected {len(xs)} AWs got {len(aws)}"
        for x, a in zip(xs, aws):
            assert 1 <= a['t'] - x['acc'] <= 6, f"CHK-034: Device-E beat AW latency expected 1..6 got {a['t'] - x['acc']}"
    for b in (INCR4, INCR8, INCR16):
        xs, aws, _ = await go(mk(r, 1, b, 2, WB_A))
        l = aws[0]['t'] - (xs[-1]['acc'] + 1)
        assert 0 <= l <= 6, f"CHK-034: WB burst first AW expected 0..6 after full capture got {l}"
    for _ in range(2):
        xs, aws, _ = await go(mk(r, 1, INCR8, 2, WB_A, k=3))
        l = aws[0]['t'] - (xs[2]['acc'] + 1)
        assert l <= 6, f"CHK-034: early-terminated burst first AW expected <=6 after termination got {l}"
    check_all(e, 'CHK-034')


@cocotb.test()
async def test_chk_035_stalls_no_timeout(dut):
    """CHK-035: READY stalls and missing responses: stable signals, no timeout, no retry."""
    e = await setup(dut, 'chk035', ready=(('r', 32),) * 3, bdel=(0, 200), rdel=(0, 200))
    r, m = e.r, e.mon
    await e.run(rand_traffic(r, 1000, busy=0.1))
    check_all(e, 'CHK-035(a)')
    assert all(x['hresp'] == 0 for x in m.x), "CHK-035(a): expected no AHB ERROR caused by stalls"
    e.axi.cfg(ready=(('c', 1),) * 3)
    for sub in ('b', 'c'):
        nar, naw, nw = len(m.ar), len(m.aw), len(m.w)
        if sub == 'b':
            e.axi.hold_r = True
            e.drv.q.append(mk(r, 0, SINGLE, 2, WB_A)[0])
            await waitc(dut, lambda: len(m.ar) == nar + 1, 200, "CHK-035(b) AR handshake")
        else:
            e.axi.hold_b = True
            e.drv.q.append(mk(r, 1, SINGLE, 2, DEV_E)[0])
            await waitc(dut, lambda: len(m.w) == nw + 1 and len(m.aw) == naw + 1, 200, "CHK-035(c) AW/W")
        tr = await watch(e, 2000)
        for (t, hro, hresp, awv, wv, arv) in tr:
            assert hro == 0 and hresp == 0, f"CHK-035({sub}): expected HREADYOUT=0 HRESP=0 while waiting got {hro}/{hresp} @{t}"
            assert awv == 0 and wv == 0 and arv == 0, f"CHK-035({sub}): expected no AXI VALID (no retry) got aw={awv} w={wv} ar={arv} @{t}"
        assert len(m.ar) == nar + (sub == 'b') and len(m.aw) == naw + (sub == 'c'), f"CHK-035({sub}): expected no extra AR/AW"
        await do_reset(e, 4)
        e.axi.hold_r = e.axi.hold_b = False
        m.clear()
        await e.run([mk(r, int(sub == 'c'), SINGLE, 2, WB_A)[0]] + idles(2))
        check_all(e, f'CHK-035({sub}) after reset')


@cocotb.test()
async def test_chk_036_protocol_checkers(dut):
    """CHK-036: independent protocol checkers: clean on legal traffic, report injected endpoint violations."""
    e = await setup(dut, 'chk036', ready=(('r', 6),) * 3, bdel=(0, 12), rdel=(0, 12), perr=0.02)
    r, m = e.r, e.mon
    t0 = m.t
    for _ in range(60):
        if m.t - t0 >= 5000:
            break
        await e.run(rand_traffic(r, 100, busy=0.15))
    assert m.t - t0 >= 5000, f"CHK-036: expected >=5000 legal cycles got {m.t - t0}"
    check_all(e, 'CHK-036 legal phase')
    e.axi.enabled = False
    e.axi.reset()
    await next_cycle(dut, 3)
    # (i) RVALID dropped before RREADY
    if m.last['rready'] == 0:
        dut.i_axi_rvalid.value = 1
        dut.i_axi_rid.value = 0
        dut.i_axi_rdata.value = 0x5A5A5A5A
        dut.i_axi_rresp.value = 0
        dut.i_axi_rlast.value = 1
        await next_cycle(dut)
        rr = m.last['rready']
        dut.i_axi_rvalid.value = 0
        await next_cycle(dut, 2)
        if rr == 0:
            assert m.viol.get('in_r_stable'), "CHK-036: injected RVALID drop expected to be reported got none"
        else:
            not_verifiable(dut, "CHK-036", "RREADY was high, RVALID-drop injection became a handshake")
    else:
        not_verifiable(dut, "CHK-036", "RREADY high while idle; RVALID-drop injection impossible")
    # (ii) BRESP changed while BVALID=1 and BREADY=0
    if m.last['bready'] == 0:
        dut.i_axi_bvalid.value = 1
        dut.i_axi_bid.value = 0
        dut.i_axi_bresp.value = OKAY
        await next_cycle(dut)
        br = m.last['bready']
        dut.i_axi_bresp.value = SLVERR
        await next_cycle(dut, 2)
        dut.i_axi_bvalid.value = 0
        await next_cycle(dut, 1)
        if br == 0:
            assert m.viol.get('in_b_stable'), "CHK-036: injected BRESP change expected to be reported got none"
        else:
            not_verifiable(dut, "CHK-036", "BREADY was high, BRESP-change injection became a handshake")
    else:
        not_verifiable(dut, "CHK-036", "BREADY high while idle; BRESP injection impossible")
    # (iii) HADDR changed during a wait state
    e.axi.reset()
    e.axi.cfg(ready=(('c', 1),) * 3, rdel=(8, 8))
    e.axi.enabled = True
    A = mk(r, 0, SINGLE, 2, WB_A)[0]
    Bx = mk(r, 0, SINGLE, 2, WB_A)[0]
    e.drv.q.extend([A, Bx] + idles(2))
    done = False
    for _ in range(100):
        await next_cycle(dut)
        if e.drv.dp is A and e.drv.ap is Bx and m.last['hready'] == 0:
            dut.i_ahb_haddr.value = Bx['addr'] ^ 0x100
            done = True
            break
    assert done, "CHK-036: could not reach an AHB wait state for HADDR injection"
    await waitc(dut, e.drv.done, 300, "AHB idle after injection")
    assert m.viol.get('in_ahb_stable'), "CHK-036: injected HADDR change during wait expected to be reported got none"


@cocotb.test()
async def test_chk_037_read_scoreboard(dut):
    """CHK-037: read conversion and attribute mapping scoreboard."""
    e = await setup(dut, 'chk037', ready=(('r', 10),) * 3, rdel=(0, 10))
    r, m = e.r, e.mon
    items = [ent(NONSEQ, 0, 0, 2, SINGLE, (WB_A << 2) | 1, 0, grp=newgrp()),
             ent(NONSEQ, 0xFFFFFFFC, 0, 2, SINGLE, (DEV_E << 2) | 2, 1, grp=newgrp())]
    items += rand_traffic(r, 2000, wr=False, busy=0.2)
    await e.run(items)
    check_all(e, 'CHK-037')
    assert len(m.ar) == nbeats(items), f"CHK-037: expected {nbeats(items)} ARs got {len(m.ar)}"
    assert all(x['hresp'] == 0 for x in m.x), "CHK-037: all reads expected OKAY"


@cocotb.test()
async def test_chk_038_async_reset(dut):
    """CHK-038: asynchronous reset assertion, inputs ignored during reset, no acceptance before release."""
    e = await setup(dut, 'chk038', ready=(('c', 0), ('c', 1), ('c', 1)))
    r, m = e.r, e.mon
    e.drv.q.append(mk(r, 1, SINGLE, 2, WB_A)[0])
    await waitc(dut, lambda: m.last is not None and m.last['awvalid'] == 1, 100, "CHK-038 pending AWVALID")
    e.drv.pause = True
    e.axi.enabled = False
    e.drv.set_mirror(False)
    await Timer(1, "step")
    dut.i_rst_n_core.value = 0
    await Timer(1, "step")
    chk_rst_now(dut, "CHK-038 (1 step after asynchronous reset assertion)")
    for c in range(8):
        if c > 0:
            await next_cycle(dut)
            chk_rst_now(dut, f"CHK-038 (reset cycle {c})")
        for h in (dut.i_ahb_hready, dut.i_axi_awready, dut.i_axi_wready, dut.i_axi_arready):
            h.value = r.randrange(2)
        dut.i_axi_bvalid.value = 0
        dut.i_axi_rvalid.value = 0
        if c < 4:
            x = mk(r, r.randrange(2), SINGLE, r.randrange(3), r.choice(LEGAL_MT))[0]
            e.drv.drive(x)
            dut.i_ahb_hwdata.value = x['wdata']
        elif c < 6:
            e.drv.drive(None)
        else:
            e.drv.drive(ent(sel=0))
    await RisingEdge(dut.i_clk_core)
    dut.i_rst_n_core.value = 1
    await next_cycle(dut)
    e.axi.reset()
    e.axi.cfg(ready=(('c', 1),) * 3)
    e.axi.enabled = True
    e.drv.reset()
    e.drv.set_mirror(True)
    e.drv.pause = False
    m.clear()
    await idle_window(e, 20, "CHK-038")
    rd = mk(r, 0, SINGLE, 2, WB_A)[0]
    dv = r.getrandbits(32)
    e.axi.rdata[rd['addr']] = dv
    await e.run([rd] + idles(2))
    assert len(m.ar) == 1 and m.x[0]['hresp'] == 0 and m.x[0]['hrdata'] == dv, f"CHK-038: read expected one AR and OKAY {dv:#x} got {len(m.ar)} ARs"
    check_all(e, 'CHK-038')


@cocotb.test()
async def test_chk_039_reset_inflight(dut):
    """CHK-039: coordinated reset during in-flight transactions discards all state."""
    e = await setup(dut, 'chk039', ready=(('c', 1),) * 3, bdel=(0, 3), rdel=(0, 3))
    r, m = e.r, e.mon
    pre = set()

    async def post(tag, A):
        m.clear()
        await idle_window(e, 20, tag)
        dv = r.getrandbits(32)
        e.axi.rdata[A] = dv
        rd = ent(NONSEQ, A, 0, 2, SINGLE, (WB_A << 2) | 1, 0, grp=newgrp())
        wr = mk(r, 1, SINGLE, 2, WB_A)[0]
        while wr['wdata'] in pre:
            wr['wdata'] = r.getrandbits(32)
        await e.run([rd, wr] + idles(2))
        assert len(m.ar) == 1 and m.ar[0]['addr'] == A and m.x[0]['hrdata'] == dv and m.x[0]['hresp'] == 0, f"{tag}: new read expected one AR returning {dv:#x}"
        assert len(m.aw) == 1 and m.aw[0]['len'] == 0 and len(m.w) == 1, f"{tag}: new write expected one AW(len 0)/one W got {len(m.aw)}/{len(m.w)}"
        assert (m.w[0]['data'], m.w[0]['strb']) == (wr['wdata'], wr['wstrb']), f"{tag}: W expected new data got {m.w[0]}"
        assert not any(w['data'] in pre for w in m.w), f"{tag}: expected no pre-reset HWDATA after release"
        check_all(e, tag)
    A = rand_addr(r, 2)
    e.axi.hold_r = True
    e.drv.q.append(ent(NONSEQ, A, 0, 2, SINGLE, (WB_A << 2) | 1, 0, grp=newgrp()))
    await waitc(dut, lambda: len(m.ar) >= 1, 100, "CHK-039(a) AR handshake")
    await do_reset(e, 4)
    e.axi.hold_r = False
    await post("CHK-039(a)", A)
    es = mk(r, 1, INCR8, 2, WB_A)
    pre |= {x['wdata'] for x in es}
    n0 = len(m.x)
    e.drv.q.extend(es)
    await waitc(dut, lambda: len(m.x) - n0 >= 5, 200, "CHK-039(b) five beats")
    await do_reset(e, 4)
    await post("CHK-039(b)", es[0]['addr'])
    x = mk(r, 1, SINGLE, 2, DEV_NE)[0]
    pre.add(x['wdata'])
    e.axi.hold_b = True
    e.drv.q.append(x)
    await waitc(dut, lambda: len(m.w) >= 1 and len(m.aw) >= 1, 100, "CHK-039(c) AW/W handshake")
    await do_reset(e, 4)
    e.axi.hold_b = False
    await post("CHK-039(c)", x['addr'])


@cocotb.test()
async def test_chk_040_write_scoreboard(dut):
    """CHK-040: SINGLE / undefined-INCR write conversion and byte-lane scoreboard."""
    e = await setup(dut, 'chk040', ready=(('r', 10),) * 3, bdel=(0, 10))
    r, m = e.r, e.mon
    items, c = [], 0
    while c < 2000:
        es = mk(r, 1, r.choice((SINGLE, INCR)), r.randrange(3), r.choice(LEGAL_MT), n=r.randint(1, 20), busy=0.2)
        items += es
        c += nbeats(es)
    await e.run(items)
    check_all(e, 'CHK-040')
    assert all(a['len'] == 0 and a['burst'] == 1 for a in m.aw), "CHK-040: every AW expected AWLEN=0 INCR"
    assert len(m.aw) == len(m.w) == len(m.b) == c, f"CHK-040: AW/W/B counts expected {c} got {len(m.aw)}/{len(m.w)}/{len(m.b)}"
    assert all(x['hresp'] == 0 for x in m.x), "CHK-040: all writes expected OKAY"


@cocotb.test()
async def test_regression_random(dut):
    """CHK-001..CHK-020 exercised by broad legal random traffic with scoreboard (CHK-033/037/040 model)."""
    e = await setup(dut, 'regression', ready=(('r', 8),) * 3, bdel=(0, 15), rdel=(0, 15), perr=0.02)
    r, m = e.r, e.mon
    await e.run(rand_traffic(r, 1500, busy=0.15))
    check_all(e, 'regression')
    check_rot([a['id'] for a in m.ar], P("PARA_RD_ID_COUNT"), 'AR')
    check_rot([a['id'] for a in m.aw], P("PARA_WR_ID_COUNT"), 'AW')
    await do_reset(e, 4)
    m.clear()
    await idle_window(e, 10, "regression after reset")
    await e.run(rand_traffic(r, 300, busy=0.15))
    check_all(e, 'regression after reset')
    dut._log.info(f"regression: AHB={len(m.x)} AR={len(m.ar)} AW={len(m.aw)} "
                  f"bursts={sum(1 for a in m.aw if a['len'] > 0)}")

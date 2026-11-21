"""
Coverage-closure tests (COV-101..COV-106) for m_axi2apb_bridge.

All stimulus and expected values come from the plan text (CHK-001/003/004/006/008/010/011/012/013/014/015/016/
022/023). The cycle engine, AXI requester, APB completer and the per-edge checker (Tracker) come from the base
module `test_axi2apb_bridge`. The Tracker checks the per-edge assertions on every cycle. Each test adds directed
end-of-transaction assertions using expected values that were worked out by hand from the CHK-016 beat-address
formula and the CHK-014 support classification.
"""
import cocotb

import test_axi2apb_bridge as base
from nnc_cocotb import *  # noqa: F401,F403

OKAY = base.OKAY
SLVERR = base.SLVERR
FIXED, INCR, WRAP = base.FIXED, base.INCR, base.WRAP


# --------------------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------------------
def _psel_hist(b):
    """Record o_apb_psel at every sampled edge (cycle -> psel)."""
    hist = {}

    def hook(c, s):
        hist[c] = s["psel"]

    b.hooks.append(hook)
    return hist


async def _run_one(b, t, tag):
    """Bridge idle, present one transaction, wait for its completion, then let the bridge return to APB idle."""
    await b.wait_for(lambda: b.tracker.owner is None, 200, f"{tag}: bridge idle before presenting {t}")
    b.submit(t)
    await b.wait_done([t], what=f"{tag}: {t}")
    await b.tick(3)
    s = b.last
    assert s is not None and s["psel"] == 0 and s["penable"] == 0, (
        f"{tag}: APB back to idle after {t}, got psel={s['psel'] if s else None}")
    bad = [(f, s[f]) for f in base.PAY if s[f] != 0]
    assert not bad, f"CHK-006 ({tag}): APB outputs zero when idle, got {bad}"
    assert b.tracker.owner is None, f"{tag}: bridge idle after {t}, owner={b.tracker.owner}"


def _no_apb_window(hist, t, tag):
    assert t.a_hs is not None and t.end is not None, f"{tag}: handshake/end recorded for {t}"
    bad = [c for c in range(t.a_hs, t.end + 1) if hist.get(c) != 0]
    assert not bad, (f"CHK-015 ({tag}): psel=0 from handshake edge {t.a_hs} through completing edge {t.end} "
                     f"for {t}, got psel!=0 at {bad[:5]}")


def _check_unsup_read(t, hist, tag):
    L = t.length
    assert t.rec is not None and not t.rec["supported"], f"{tag}: tracker classifies {t} unsupported"
    assert t.rec["psel_edges"] == 0 and not t.rec["apb"], f"CHK-015/CHK-022 ({tag}): no APB transfer for {t}"
    _no_apb_window(hist, t, tag)
    assert len(t.r) == L + 1, f"CHK-010/CHK-022 ({tag}): exactly ARLEN+1={L + 1} R beats for {t}, got {len(t.r)}"
    for k, x in enumerate(t.r):
        assert x["resp"] == SLVERR and x["data"] == 0, (
            f"CHK-012 ({tag}): beat {k} SLVERR with rdata=0, got resp={x['resp']} data={x['data']:#x}")
        assert x["id"] == t.id, f"CHK-010 ({tag}): beat {k} rid={t.id:#x}, got {x['id']:#x}"
        assert x["last"] == (1 if k == L else 0), f"CHK-010 ({tag}): rlast only on beat {L}, beat {k} got {x['last']}"


def _check_unsup_write(t, hist, tag):
    L = t.length
    assert t.rec is not None and not t.rec["supported"], f"{tag}: tracker classifies {t} unsupported"
    assert len(t.w_hs) == L + 1 and len(t.rec["w"]) == L + 1, (
        f"CHK-013/CHK-023 ({tag}): exactly AWLEN+1={L + 1} W handshakes for {t}, got {len(t.w_hs)}/{len(t.rec['w'])}")
    assert t.rec["psel_edges"] == 0 and not t.rec["apb"], f"CHK-015/CHK-023 ({tag}): no APB transfer for {t}"
    _no_apb_window(hist, t, tag)
    assert t.rec["first_bvalid"] is not None and t.rec["first_bvalid"] > t.w_hs[-1], (
        f"CHK-008/CHK-023 ({tag}): bvalid rises only after the last W handshake ({t.w_hs[-1]}), "
        f"got {t.rec['first_bvalid']}")
    assert t.b is not None and t.b["resp"] == SLVERR and t.b["id"] == t.id, (
        f"CHK-008/CHK-023 ({tag}): one SLVERR B with bid=AWID {t.id:#x}, got {t.b}")


def _check_legal_read(t, exp_paddrs, tag):
    L = t.length
    assert t.rec is not None and t.rec["supported"], f"{tag}: tracker classifies {t} supported"
    got = base._paddrs(t)
    assert got == exp_paddrs, (f"CHK-016 ({tag}): paddr sequence {[hex(a) for a in exp_paddrs]} for {t}, "
                               f"got {[hex(a) for a in got]}")
    assert len(t.rec["apb"]) == L + 1, f"CHK-016 ({tag}): AxLEN+1={L + 1} APB transfers, got {len(t.rec['apb'])}"
    for k, tr in enumerate(t.rec["apb"]):
        v = tr["vals"]
        assert v["pwrite"] == 0 and v["pstrb"] == 0, f"CHK-016 ({tag}): read transfer {k} pwrite=0/pstrb=0, got {v}"
        assert v["pprot"] == t.prot, f"CHK-016 ({tag}): transfer {k} pprot={t.prot}, got {v['pprot']}"
        assert tr["done"] is not None and tr["pslverr"] == 0, f"CHK-011 ({tag}): transfer {k} completed with PSLVERR=0"
    assert len(t.r) == L + 1, f"CHK-010 ({tag}): ARLEN+1={L + 1} R beats, got {len(t.r)}"
    for k, x in enumerate(t.r):
        assert x["resp"] == OKAY and x["data"] == t.rec["apb"][k]["prdata"], (
            f"CHK-011 ({tag}): beat {k} OKAY rdata=prdata {t.rec['apb'][k]['prdata']:#x}, got {x}")
        assert x["id"] == t.id, f"CHK-010 ({tag}): beat {k} rid={t.id:#x}, got {x['id']:#x}"
        assert x["last"] == (1 if k == L else 0), f"CHK-010 ({tag}): rlast only on beat {L}, beat {k} got {x['last']}"


def _check_legal_write(t, exp_paddrs, tag):
    L = t.length
    assert t.rec is not None and t.rec["supported"], f"{tag}: tracker classifies {t} supported"
    got = base._paddrs(t)
    assert got == exp_paddrs, (f"CHK-016 ({tag}): paddr sequence {[hex(a) for a in exp_paddrs]} for {t}, "
                               f"got {[hex(a) for a in got]}")
    assert len(t.w_hs) == L + 1 and len(t.rec["w"]) == L + 1, f"CHK-013 ({tag}): AWLEN+1={L + 1} W handshakes"
    assert len(t.rec["apb"]) == L + 1, f"CHK-016 ({tag}): AxLEN+1={L + 1} APB transfers, got {len(t.rec['apb'])}"
    for k, tr in enumerate(t.rec["apb"]):
        v = tr["vals"]
        assert v["pwrite"] == 1, f"CHK-016 ({tag}): transfer {k} pwrite=1, got {v}"
        assert v["pwdata"] == t.data[k] and v["pstrb"] == t.strb[k], (
            f"CHK-016 ({tag}): transfer {k} pwdata/pstrb = W beat {k} ({t.data[k]:#010x}/{t.strb[k]:#x}), got "
            f"{v['pwdata']:#x}/{v['pstrb']:#x}")
        assert v["pprot"] == t.prot, f"CHK-016 ({tag}): transfer {k} pprot={t.prot}, got {v['pprot']}"
        assert tr["stable"], f"CHK-003 ({tag}): transfer {k} payload stable through the transfer"
    assert t.b is not None and t.b["resp"] == OKAY and t.b["id"] == t.id, (
        f"CHK-008 ({tag}): one OKAY B with bid=AWID {t.id:#x}, got {t.b}")
    assert t.rec["first_bvalid"] > t.rec["apb"][-1]["done"], f"CHK-008 ({tag}): bvalid after the last APB completion"
    assert t.rec["first_bvalid"] > t.w_hs[-1], f"CHK-008 ({tag}): bvalid after the last W handshake"


# --------------------------------------------------------------------------------------------------
# COV-101
# --------------------------------------------------------------------------------------------------
@cocotb.test()
async def test_cov_101_upper_half_reads(dut):
    """COV-101: CHK-016, CHK-011, CHK-010, CHK-004, CHK-006, CHK-001 - supported reads at 0x7FFF_xxxx and back to low region."""
    b = await base.make_bench(dut, "cov101")
    b.master.rready.set("always")
    b.master.bready.set("always")
    b.apb.wmin, b.apb.wmax = 0, 2
    b.apb.unmapped_default = False  # address-agnostic responder
    b.ref_check = False  # PRDATA is generated per transfer (distinct), not taken from the memory model
    used = []

    def resp(tr):
        if tr["write"]:
            return b.apb.default_resp(tr)
        v = ((b.r.getrandbits(16) << 16) | ((tr["idx"] * 0x0101 + 0x1234) & 0xFFFF)) & base.M32
        while v in used:
            v = (v + 0x00010000) & base.M32
        used.append(v)
        return v, 0

    b.apb.resp_fn = resp

    cases = [
        (0x7FFF0010, 3, INCR, [0x7FFF0010, 0x7FFF0014, 0x7FFF0018, 0x7FFF001C]),
        (0x7FFF0100, 1, FIXED, [0x7FFF0100, 0x7FFF0100]),
        (0x7FFF0024, 3, WRAP, [0x7FFF0024, 0x7FFF0028, 0x7FFF002C, 0x7FFF0020]),
        (0x00000100, 0, INCR, [0x00000100]),
    ]
    txns = []
    for addr, L, burst, exp in cases:
        assert base.is_supported(addr, L, 2, burst, 0), f"COV-101: (setup) case supported {addr:#x}/{L}/{burst}"
        t = base.make_read(base.rid(b), addr, L, 2, burst, 0, b.r.randint(0, 7))
        await _run_one(b, t, "COV-101")
        _check_legal_read(t, exp, "COV-101")
        txns.append(t)
    all_prdata = [tr["prdata"] for t in txns for tr in t.rec["apb"]]
    assert len(all_prdata) == 4 + 2 + 4 + 1, f"COV-101: 11 APB read transfers in total, got {len(all_prdata)}"
    assert len(set(all_prdata)) == len(all_prdata), f"COV-101: (stimulus) distinct PRDATA per transfer, got {all_prdata}"
    await b.final_check()


# --------------------------------------------------------------------------------------------------
# COV-102
# --------------------------------------------------------------------------------------------------
@cocotb.test()
async def test_cov_102_upper_half_writes(dut):
    """COV-102: CHK-016, CHK-008, CHK-013, CHK-004, CHK-006, CHK-003 - supported writes at 0x7FFF_xxxx and back to low region."""
    b = await base.make_bench(dut, "cov102")
    b.master.rready.set("always")
    b.master.bready.set("always")
    b.apb.wmin, b.apb.wmax = 0, 2
    b.apb.unmapped_default = False
    b.apb.err_prob = 0.0

    cases = [
        (0x7FFF0010, 3, INCR, [0x7FFF0010, 0x7FFF0014, 0x7FFF0018, 0x7FFF001C]),
        (0x7FFF0200, 1, FIXED, [0x7FFF0200, 0x7FFF0200]),
        (0x7FFF0024, 3, WRAP, [0x7FFF0024, 0x7FFF0028, 0x7FFF002C, 0x7FFF0020]),
        (0x00000200, 0, INCR, [0x00000200]),
    ]
    for addr, L, burst, exp in cases:
        assert base.is_supported(addr, L, 2, burst, 1), f"COV-102: (setup) case supported {addr:#x}/{L}/{burst}"
        n = L + 1
        t = base.make_write(b.r, base.rid(b), addr, L, 2, burst, 1, b.r.randint(0, 7),
                            data=[b.r.getrandbits(32) for _ in range(n)], strb=[0xF] * n)
        await _run_one(b, t, "COV-102")
        _check_legal_write(t, exp, "COV-102")
    await b.final_check()


# --------------------------------------------------------------------------------------------------
# COV-103
# --------------------------------------------------------------------------------------------------
@cocotb.test()
async def test_cov_103_unsupported_large_size_reads(dut):
    """COV-103: CHK-012, CHK-010, CHK-015, CHK-014, CHK-022 - ARSIZE 7/6 with long ARLEN: SLVERR beats, no APB; then legal read."""
    b = await base.make_bench(dut, "cov103")
    b.master.rready.set("always")
    b.master.bready.set("always")
    b.apb.wmin, b.apb.wmax = 0, 2
    hist = _psel_hist(b)

    for size, L in ((7, 7), (7, 15), (6, 15)):
        assert not base.is_supported(0, L, size, INCR, 0), f"COV-103: (setup) size {size} unsupported"
        t = base.make_read(base.rid(b), 0x00000000, L, size, INCR, 0, b.r.randint(0, 7))
        await _run_one(b, t, "COV-103")
        _check_unsup_read(t, hist, f"COV-103 size={size} len={L}")

    good = base.make_read(base.rid(b), 0x00000040, 0, 2, INCR, 0, b.r.randint(0, 7))
    await _run_one(b, good, "COV-103")
    _check_legal_read(good, [0x00000040], "COV-103 legal")
    await b.final_check()


# --------------------------------------------------------------------------------------------------
# COV-104
# --------------------------------------------------------------------------------------------------
@cocotb.test()
async def test_cov_104_unsupported_large_size_writes(dut):
    """COV-104: CHK-008, CHK-013, CHK-015, CHK-014, CHK-023 - AWSIZE 7/6 with long AWLEN: W drained, no APB, SLVERR B; then legal write."""
    b = await base.make_bench(dut, "cov104")
    b.master.rready.set("always")
    b.master.bready.set("always")
    b.apb.wmin, b.apb.wmax = 0, 2
    b.apb.err_prob = 0.0
    hist = _psel_hist(b)

    for size, L in ((7, 7), (7, 15), (6, 15)):
        assert not base.is_supported(0, L, size, INCR, 0), f"COV-104: (setup) size {size} unsupported"
        n = L + 1
        t = base.make_write(b.r, base.rid(b), 0x00000000, L, size, INCR, 0, b.r.randint(0, 7),
                            data=[b.r.getrandbits(32) for _ in range(n)], strb=[0xF] * n)
        await _run_one(b, t, "COV-104")
        _check_unsup_write(t, hist, f"COV-104 size={size} len={L}")

    good = base.make_write(b.r, base.rid(b), 0x00000040, 0, 2, INCR, 0, b.r.randint(0, 7),
                           data=[b.r.getrandbits(32)], strb=[0xF])
    await _run_one(b, good, "COV-104")
    _check_legal_write(good, [0x00000040], "COV-104 legal")
    await b.final_check()


# --------------------------------------------------------------------------------------------------
# COV-105
# --------------------------------------------------------------------------------------------------
@cocotb.test()
async def test_cov_105_top_of_space_4k_cross_reads(dut):
    """COV-105: CHK-012, CHK-010, CHK-015, CHK-022 - 4-KiB-crossing reads wrapping past 0xFFFF_FFFF; then legal read at 0."""
    b = await base.make_bench(dut, "cov105")
    b.master.rready.set("always")
    b.master.bready.set("always")
    b.apb.wmin, b.apb.wmax = 0, 2
    hist = _psel_hist(b)

    for addr, L in ((0xFFFFFFFC, 1), (0xFFFFFF00, 255)):
        assert base.crosses_4k(addr, 2, L), f"COV-105: (setup) {addr:#x}/len {L} crosses 4 KiB"
        assert not base.is_supported(addr, L, 2, INCR, 0), f"COV-105: (setup) {addr:#x}/len {L} unsupported"
        t = base.make_read(base.rid(b), addr, L, 2, INCR, 0, b.r.randint(0, 7))
        await _run_one(b, t, "COV-105")
        _check_unsup_read(t, hist, f"COV-105 addr={addr:#x} len={L}")

    good = base.make_read(base.rid(b), 0x00000000, 0, 2, INCR, 0, b.r.randint(0, 7))
    await _run_one(b, good, "COV-105")
    _check_legal_read(good, [0x00000000], "COV-105 legal")
    await b.final_check()


# --------------------------------------------------------------------------------------------------
# COV-106
# --------------------------------------------------------------------------------------------------
@cocotb.test()
async def test_cov_106_top_of_space_4k_cross_writes(dut):
    """COV-106: CHK-008, CHK-013, CHK-015, CHK-023 - 4-KiB-crossing writes wrapping past 0xFFFF_FFFF; then legal write at 0."""
    b = await base.make_bench(dut, "cov106")
    b.master.rready.set("always")
    b.master.bready.set("always")
    b.apb.wmin, b.apb.wmax = 0, 2
    b.apb.err_prob = 0.0
    hist = _psel_hist(b)

    for addr, L in ((0xFFFFFFFC, 1), (0xFFFFFF00, 255)):
        assert base.crosses_4k(addr, 2, L), f"COV-106: (setup) {addr:#x}/len {L} crosses 4 KiB"
        assert not base.is_supported(addr, L, 2, INCR, 0), f"COV-106: (setup) {addr:#x}/len {L} unsupported"
        n = L + 1
        t = base.make_write(b.r, base.rid(b), addr, L, 2, INCR, 0, b.r.randint(0, 7),
                            data=[b.r.getrandbits(32) for _ in range(n)], strb=[0xF] * n)
        await _run_one(b, t, "COV-106")
        _check_unsup_write(t, hist, f"COV-106 addr={addr:#x} len={L}")

    good = base.make_write(b.r, base.rid(b), 0x00000000, 0, 2, INCR, 0, b.r.randint(0, 7),
                           data=[b.r.getrandbits(32)], strb=[0xF])
    await _run_one(b, good, "COV-106")
    _check_legal_write(good, [0x00000000], "COV-106 legal")
    await b.final_check()

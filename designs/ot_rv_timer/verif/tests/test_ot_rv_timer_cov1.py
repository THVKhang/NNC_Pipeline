"""Coverage-closure tests for ot_rv_timer_nnc (COV-101 .. COV-104).

Reuses the TL-UL host driver / monitor of the base module (test_ot_rv_timer.TlEnv), which already
checks at every edge: CHK-001 (o_alert_integ_fail=0), CHK-006 (outputs inactive during reset),
CHK-009 (every D beat matches one outstanding request), CHK-010 (opcode / size echo), CHK-011
(d_error classification) and CHK-013 (o_d_intg_err=0).  This module adds a host-obligation monitor
(CHK-008 (1), (2), (3)) and drives the idle A-channel fields (i_a_valid=0) directly from the test.

Idle-field timing: fields are written right after a falling edge (same as the base driver), while
no request is queued or being presented, so the driver only writes i_a_valid=0 / i_d_ready in that
step; the values are sampled by the env in the ReadOnly phase of the same step ("edge k").
"""

import cocotb
from cocotb.triggers import FallingEdge
from nnc_cocotb import *  # noqa: F401,F403

import test_ot_rv_timer as base

OP_PUTF = base.OP_PUTF
OP_PUTP = base.OP_PUTP
OP_GET = base.OP_GET
A_ALERT = base.A_ALERT
A_CTRL = base.A_CTRL
A_IE = base.A_IE
A_CFG = base.A_CFG
A_CML = base.A_CML
A_CMU = base.A_CMU
BAD_MASKS = base.BAD_MASKS
hx = base.hx

IN_FIELDS = ("i_a_opcode", "i_a_param", "i_a_size", "i_a_source", "i_a_address", "i_a_mask",
             "i_a_data", "i_a_instr", "i_a_intg_flip")


# ----------------------------------------------------------------------------------------------
# Host-obligation monitor (CHK-008 (1), (2), (3)); also records the idle A-channel samples
# ----------------------------------------------------------------------------------------------
def install_host_monitor(env):
    st = {"prev": None, "idle": []}
    d = env.dut

    def hook(k, s):
        a_valid = val(d.i_a_valid)
        f = {n: val(getattr(d, n)) for n in IN_FIELDS}
        prev = st["prev"]
        if env.reset_log and env.reset_log[-1][1] == k:
            prev = None
            if a_valid != 0:
                env.viol(f"CHK-008: (test bench) i_a_valid=0 at the first edge after reset release "
                         f"expected (edge {k}), got {a_valid}")
        if prev is not None and prev[0] == 1 and prev[1] == 0:
            if a_valid != 1 or f != prev[2]:
                env.viol(f"CHK-008: (test bench) A channel stable while a_valid=1 and a_ready=0 "
                         f"expected at edge {k}, got valid={a_valid} fields {prev[2]} -> {f}")
        if a_valid == 1:
            op = f["i_a_opcode"]
            if f["i_a_param"] != 0:
                env.viol(f"CHK-008: (test bench) i_a_param=0 expected at edge {k}, got {f['i_a_param']}")
            if f["i_a_address"] is None or f["i_a_address"] >= 0x200:
                env.viol(f"CHK-008: (test bench) i_a_address<0x200 expected at edge {k}, got {f['i_a_address']}")
            if f["i_a_mask"] in BAD_MASKS:
                env.viol(f"CHK-008: (test bench) legal a_mask expected at edge {k}, got {f['i_a_mask']:04b}")
            if f["i_a_instr"] == 1 and op in (OP_PUTF, OP_PUTP):
                env.viol(f"CHK-008: (test bench) no instruction-type write expected at edge {k}")
            src = f["i_a_source"]
            if any(o.source == src and o.a_edge is not None and o.a_edge < k
                   for o in env.outstanding.values()):
                env.viol(f"CHK-008: (test bench) unique a_source expected at edge {k}, got {src} in use")
            if op in (OP_PUTF, OP_PUTP) and f["i_a_address"] == A_ALERT and f["i_a_data"] == 1:
                env.viol(f"CHK-008: (test bench) no write of 0x00000001 to 0x000 expected at edge {k}")
        else:
            st["idle"].append((k, a_valid, f))
        st["prev"] = (a_valid, s["o_a_ready"], f)

    env.hooks.append(hook)
    return st


async def idle_drive(env, cycles, **fields):
    """For `cycles` cycles drive the given A-channel fields right after the falling edge while
    i_a_valid stays 0 (no request queued); returns after the env sample of the last cycle."""
    d = env.dut
    for _ in range(int(cycles)):
        await FallingEdge(env.clk)
        assert env.cur is None and not env.queue, (
            f"{env.chk}: (test bench) idle A channel expected while driving idle fields, got a request")
        for n, v in fields.items():
            getattr(d, n).value = v
        await env.edge()


def beats_in(env, lo, hi):
    return [b for b in env.beats if lo <= b[0] <= hi]


def check_one_resp(env, C, r, exp_op, what):
    assert not r.discarded and r.resp is not None, f"{C}: {what}: one response expected, got none"
    rs = r.resp
    assert rs["source"] == r.source, f"{C}: {what}: d_source={r.source} expected, got {rs['source']}"
    assert rs["opcode"] == exp_op, f"{C}: {what}: d_opcode={exp_op} expected, got {rs['opcode']}"
    assert rs["size"] == r.size, f"{C}: {what}: d_size={r.size} expected, got {rs['size']}"


def check_no_extra(env, C, r, what):
    extra = [b for b in env.beats if b[1] == r.source and b[0] > r.r_edge]
    assert not extra, f"{C}: {what}: exactly one D beat expected, got extra beats {extra}"


# ==============================================================================================
# COV-101
# ==============================================================================================
@cocotb.test()
async def test_cov_101_subword_unaligned_writes(dut):
    """COV-101: CHK-009, CHK-010, CHK-008, CHK-013, CHK-011 - size-aligned sub-word writes at
    addresses that are not 4-byte aligned, then full-word reads of INTR_ENABLE0 / COMPARE_LOWER0_0."""
    C = "COV-101"
    env = await base.setup(dut, C)
    install_host_monitor(env)
    env.d_ready_mode = 1
    writes = [
        (OP_PUTP, 0x101, 0x0000FF00, 0, 0b0010),
        (OP_PUTP, 0x102, 0x00FF0000, 0, 0b0100),
        (OP_PUTP, 0x103, 0xFF000000, 0, 0b1000),
        (OP_PUTF, 0x102, 0xFFFF0000, 1, 0b1100),
        (OP_PUTP, 0x11A, 0x12340000, 1, 0b1100),
        (OP_PUTP, 0x119, 0x0000AB00, 0, 0b0010),
    ]
    used = set()
    for i, (op, a, data, sz, mk) in enumerate(writes):
        r = await env.access(op, a, data, size=sz, mask=mk, timeout=400)
        what = f"write {i + 1} (op {op}, 0x{a:03X}, size {sz}, mask {mk:04b})"
        assert r.source not in used, f"{C}: (stimulus) distinct a_source expected, got {r.source} reused"
        used.add(r.source)
        check_one_resp(env, C, r, 0, what)
        dut._log.info(f"{C}: {what}: d_error={r.resp['error']}")
        await env.edges(4)
        check_no_extra(env, C, r, what)
    for a in (A_IE, A_CML):
        r = await env.access(OP_GET, a, size=2, mask=0xF)
        what = f"Get of {base.nm(a)}"
        assert r.source not in used, f"{C}: (stimulus) distinct a_source expected, got {r.source} reused"
        used.add(r.source)
        check_one_resp(env, C, r, 1, what)
        assert r.resp["error"] == 0, f"{C}: {what}: d_error=0 expected, got {r.resp['error']}"
        dut._log.info(f"{C}: {what} returned {hx(r.resp['data'])}")
        await env.edges(4)
        check_no_extra(env, C, r, what)
    assert env.n_dintg == 0, f"{C}: o_d_intg_err=0 throughout expected, got 1 at {env.n_dintg} edges"
    env.finish()


# ==============================================================================================
# COV-102
# ==============================================================================================
@cocotb.test()
async def test_cov_102_idle_bad_masks(dut):
    """COV-102: CHK-008, CHK-009, CHK-003, CHK-013, CHK-011 - non-contiguous / forbidden a_mask
    values on an idle A channel (i_a_valid=0), then a normal CFG0 read."""
    C = "COV-102"
    env = await base.setup(dut, C)
    mon = install_host_monitor(env)
    env.d_ready_mode = 1
    assert not env.outstanding, f"{C}: (stimulus) no outstanding request expected, got {env.outstanding}"
    k0 = env.cyc + 1
    common = dict(i_a_opcode=OP_PUTF, i_a_param=0, i_a_size=2, i_a_address=A_CFG, i_a_data=0,
                  i_a_instr=0, i_a_intg_flip=0, i_a_source=0)
    for i, m in enumerate(BAD_MASKS):
        await idle_drive(env, 1 + (i % 2), i_a_mask=m, **common)
    await idle_drive(env, 2, i_a_mask=0xF, **common)
    k1 = env.cyc
    seen = {f["i_a_mask"] for (k, v, f) in mon["idle"] if k0 <= k <= k1}
    missing = [f"{m:04b}" for m in BAD_MASKS if m not in seen]
    assert not missing, f"{C}: (stimulus) idle masks {missing} applied expected, got not seen"
    vbad = [k for (k, v, f) in mon["idle"] if k0 <= k <= k1 and v != 0]
    assert not vbad, f"{C}: (stimulus) i_a_valid=0 during idle expected, got {vbad}"
    b = beats_in(env, k0, k1)
    assert not b, f"{C}: no D beat during the idle cycles expected, got {b}"
    dv = [k for k in range(k0, k1 + 1) if env.dvalid_hist[k] != 0]
    assert not dv, f"{C}: o_d_valid=0 during the idle cycles expected, got 1/X at edges {dv}"
    r = await env.access(OP_GET, A_CFG, size=2, mask=0xF)
    check_one_resp(env, C, r, 1, "CFG0 Get")
    assert r.resp["error"] == 0, f"{C}: CFG0 Get d_error=0 expected, got {r.resp['error']}"
    await env.edges(20)
    check_no_extra(env, C, r, "CFG0 Get")
    p = env.alerts_in(k0, env.cyc)
    assert not p, f"{C}: no o_alert pulse expected, got pulses at {p}"
    assert env.n_dintg == 0, f"{C}: o_d_intg_err=0 throughout expected, got 1 at {env.n_dintg} edges"
    env.finish()


# ==============================================================================================
# COV-103
# ==============================================================================================
@cocotb.test()
async def test_cov_103_idle_instr_write(dut):
    """COV-103: CHK-008, CHK-009, CHK-003, CHK-001, CHK-011 - instruction-type indication with
    write opcodes on an idle A channel, then a data write and read of INTR_ENABLE0."""
    C = "COV-103"
    env = await base.setup(dut, C)
    mon = install_host_monitor(env)
    env.d_ready_mode = 1
    assert not env.outstanding, f"{C}: (stimulus) no outstanding request expected, got {env.outstanding}"
    k0 = env.cyc + 1
    common = dict(i_a_param=0, i_a_size=2, i_a_mask=0xF, i_a_address=A_IE, i_a_data=0x1,
                  i_a_intg_flip=0, i_a_source=0)
    await idle_drive(env, 3, i_a_opcode=OP_PUTF, i_a_instr=1, **common)
    await idle_drive(env, 3, i_a_opcode=OP_PUTP, i_a_instr=1, **common)
    await idle_drive(env, 2, i_a_opcode=OP_GET, i_a_instr=0, **common)
    k1 = env.cyc
    idle = [(k, v, f) for (k, v, f) in mon["idle"] if k0 <= k <= k1]
    combos = {(f["i_a_instr"], f["i_a_opcode"]) for (k, v, f) in idle}
    for c in ((1, OP_PUTF), (1, OP_PUTP)):
        assert c in combos, f"{C}: (stimulus) idle (instr, opcode)={c} applied expected, got {combos}"
    assert idle and idle[-1][2]["i_a_instr"] == 0, f"{C}: (stimulus) i_a_instr=0 before raising i_a_valid expected"
    vbad = [k for (k, v, f) in idle if v != 0]
    assert not vbad, f"{C}: (stimulus) i_a_valid=0 during idle expected, got {vbad}"
    b = beats_in(env, k0, k1)
    assert not b, f"{C}: no D beat while i_a_valid=0 expected, got {b}"
    w = await env.access(OP_PUTF, A_IE, 0x1, size=2, mask=0xF)
    check_one_resp(env, C, w, 0, "INTR_ENABLE0 write")
    assert w.resp["error"] == 0, f"{C}: INTR_ENABLE0 write d_error=0 expected, got {w.resp['error']}"
    r = await env.access(OP_GET, A_IE, size=2, mask=0xF)
    check_one_resp(env, C, r, 1, "INTR_ENABLE0 read")
    assert r.resp["error"] == 0, f"{C}: INTR_ENABLE0 read d_error=0 expected, got {r.resp['error']}"
    dut._log.info(f"{C}: INTR_ENABLE0 read {hx(r.resp['data'])}")
    await env.edges(20)
    check_no_extra(env, C, w, "INTR_ENABLE0 write")
    check_no_extra(env, C, r, "INTR_ENABLE0 read")
    p = env.alerts_in(k0, env.cyc)
    assert not p, f"{C}: no o_alert pulse expected, got pulses at {p}"
    assert env.n_integ_fail == 0, f"{C}: o_alert_integ_fail=0 expected, got 1 at {env.n_integ_fail} edges"
    env.finish()


# ==============================================================================================
# COV-104
# ==============================================================================================
@cocotb.test()
async def test_cov_104_intg_flip_commands(dut):
    """COV-104: CHK-016, CHK-001, CHK-013, CHK-003, CHK-006 - command-integrity inversion on an
    idle A channel over many command values (no alert), then several corrupted requests each
    followed by the repeating fatal alert, a reset and a CFG0 read."""
    C = "COV-104"
    env = await base.setup(dut, C)
    mon = install_host_monitor(env)
    env.d_ready_mode = 1
    R = rng("cov104")
    # ---------------- (a) flip=1 with i_a_valid=0 ----------------
    assert not env.outstanding, f"{C}: (stimulus) no outstanding request expected, got {env.outstanding}"
    k0 = env.cyc + 1
    for i in range(100):
        await idle_drive(env, 1,
                         i_a_address=(1 << (i % 32)),
                         i_a_opcode=(OP_PUTF, OP_PUTP, OP_GET)[i % 3],
                         i_a_mask=(0b0001, 0b0011, 0b1100, 0b1111)[i % 4],
                         i_a_size=(0, 1, 2)[(i // 3) % 3],
                         i_a_instr=(i // 2) % 2,
                         i_a_intg_flip=1, i_a_param=0, i_a_source=0,
                         i_a_data=R.getrandbits(32))
    await idle_drive(env, 2, i_a_intg_flip=0, i_a_instr=0, i_a_mask=0xF, i_a_opcode=OP_GET,
                     i_a_size=2, i_a_address=A_CFG, i_a_param=0, i_a_data=0, i_a_source=0)
    k1 = env.cyc
    idle = [(k, v, f) for (k, v, f) in mon["idle"] if k0 <= k <= k1]
    bits = set()
    for (k, v, f) in idle:
        if f["i_a_intg_flip"] == 1 and f["i_a_address"]:
            bits.add(f["i_a_address"].bit_length() - 1)
    assert bits == set(range(32)), f"{C}: (a) (stimulus) every address bit walked with flip=1 expected, got {sorted(bits)}"
    vbad = [k for (k, v, f) in idle if v != 0]
    assert not vbad, f"{C}: (a) (stimulus) i_a_valid=0 during idle expected, got {vbad}"
    assert not env.flip_seen, f"{C}: (a) (stimulus) no corrupted request accepted expected"
    b = beats_in(env, k0, k1)
    assert not b, f"{C}: (a) no D beat while i_a_valid=0 expected, got {b}"
    r = await env.access(OP_GET, A_CFG, size=2, mask=0xF)
    check_one_resp(env, C, r, 1, "(a) CFG0 Get")
    assert r.resp["error"] == 0, f"{C}: (a) CFG0 Get d_error=0 expected, got {r.resp['error']}"
    await env.edges(20)
    p = env.alerts_in(k0, env.cyc)
    assert not p, f"{C}: (a) no o_alert pulse without an accepted corrupted request expected, got {p}"

    # ---------------- (b) corrupted requests ----------------
    runs = [(OP_GET, A_ALERT, 0), (OP_GET, A_CTRL, 0), (OP_GET, A_CFG, 0), (OP_GET, A_CMU, 0),
            (OP_PUTF, A_CML, 0x0)]
    WATCH = 220  # >= 200 cycles of o_alert observation after acceptance
    for run, (op, addr, data) in enumerate(runs, 1):
        tag = f"(b) run {run} (op {op}, 0x{addr:03X})"
        r = env.issue(op, addr, data, size=2, mask=0xF, flip=1)
        for _ in range(100):
            if r.a_edge is not None:
                break
            await env.edge()
        assert r.a_edge is not None, f"{C}: {tag}: corrupted request accepted within 100 cycles expected, got not accepted"
        a = r.a_edge
        for _ in range(32):  # D-010: do not wait more than 32 cycles for the response
            if r.done:
                break
            await env.edge()
        await env.until(a + WATCH)
        ka, krel = await env.reset(5)
        p = env.alerts_in(a, ka - 1)
        assert p and p[0] <= a + 16, f"{C}: {tag}: first o_alert pulse in [a={a}, a+16] expected, got {p[:3]}"
        gaps = [(p[i], p[i + 1]) for i in range(len(p) - 1) if p[i + 1] - p[i] > 32]
        assert not gaps, f"{C}: {tag}: a pulse in every 32-edge window expected, got gaps {gaps[:3]}"
        assert p[-1] >= ka - 32, (
            f"{C}: {tag}: a pulse in the last 32 edges before reset (edge {ka}) expected, got last pulse {p[-1]}")
        bad = [k for k in range(ka, krel) if env.rst_samples.get(k, {}).get("o_alert") != 0]
        assert not bad, f"{C}: {tag}: o_alert=0 while rst_ni=0 expected, got 1/X at {bad}"
        await env.edges(200)
        p2 = env.alerts_in(krel, krel + 199)
        assert not p2, f"{C}: {tag}: o_alert=0 for 200 cycles after reset release expected, got pulses at {p2}"
        r2 = await env.access(OP_GET, A_CFG, size=2, mask=0xF)
        assert not r2.discarded and r2.resp is not None, f"{C}: {tag}: CFG0 read response expected, got none"
        assert r2.resp["error"] == 0 and r2.resp["data"] == 0x00010000, (
            f"{C}: {tag}: CFG0 read d_error=0, 0x00010000 expected, got err={r2.resp['error']} "
            f"data={hx(r2.resp['data'])}")
        p3 = env.alerts_in(krel, env.cyc)
        assert not p3, f"{C}: {tag}: no o_alert after reset before the next corrupted request expected, got {p3}"
    assert env.n_integ_fail == 0, f"{C}: o_alert_integ_fail=0 throughout expected, got 1 at {env.n_integ_fail} edges"
    assert env.n_dintg == 0, f"{C}: o_d_intg_err=0 throughout expected, got 1 at {env.n_dintg} edges"
    env.finish()

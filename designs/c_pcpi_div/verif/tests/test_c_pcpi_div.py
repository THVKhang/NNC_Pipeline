"""cocotb testbench for picorv32_pcpi_div (RV32M DIV/DIVU/REM/REMU PCPI co-processor).

Timing model: inputs are driven right after a falling edge and outputs are sampled at the
falling edge.  The output value read at falling edge F_k is the value present at the next
rising edge R_{k+1}; the inputs driven at F_k are also the values sampled at R_{k+1}.
So an output sample and the inputs driven in the same mid-cycle describe the same rising edge.
"""

import cocotb
from nnc_cocotb import *

MASK = 0xFFFFFFFF
OPS = {"DIV": 0b100, "DIVU": 0b101, "REM": 0b110, "REMU": 0b111}
OP_NAMES = list(OPS.keys())
MAX_LAT = 200        # completion timeout (edges after issue)
WAIT_DEADLINE = 16   # pcpi_wait / pcpi_ready must show within the first 16 edges after issue

SPECIALS = [0, 1, 2, 3, 0xFFFFFFFF, 0xFFFFFFFE, 0x80000000, 0x80000001, 0x7FFFFFFF, 0x7FFFFFFE]


# --------------------------------------------------------------------------------------------
# Instruction encoding and reference model (derived from RV32M spec text only)
# --------------------------------------------------------------------------------------------
def encode(op, rd=0, rs1=0, rs2=0):
    """R-type: funct7=0000001, opcode=0110011, funct3 from OPS."""
    return ((0b0000001 << 25) | ((rs2 & 31) << 20) | ((rs1 & 31) << 15)
            | (OPS[op] << 12) | ((rd & 31) << 7) | 0b0110011)


def to_signed(x):
    x &= MASK
    return x - (1 << 32) if x & 0x80000000 else x


def ref_model(op, a, b):
    """Expected pcpi_rd for an RV32M division-type instruction (XLEN=32)."""
    a &= MASK
    b &= MASK
    if op in ("DIVU", "REMU"):
        if b == 0:
            q, r = MASK, a                     # quotient all ones, remainder = dividend
        else:
            q, r = a // b, a % b
    else:
        sa, sb = to_signed(a), to_signed(b)
        if sb == 0:
            q, r = -1, sa                      # quotient -1, remainder = dividend
        elif sa == -(1 << 31) and sb == -1:
            q, r = sa, 0                       # signed overflow
        else:
            q = abs(sa) // abs(sb)             # round toward zero
            if (sa < 0) != (sb < 0):
                q = -q
            r = sa - q * sb                    # remainder takes the dividend's sign
    return (q & MASK) if op in ("DIV", "DIVU") else (r & MASK)


# --------------------------------------------------------------------------------------------
# Random stimulus helpers
# --------------------------------------------------------------------------------------------
def rand_operand(r):
    p = r.random()
    if p < 0.25:
        return r.choice(SPECIALS)
    if p < 0.45:
        v = r.randint(0, 20)
        return v if r.random() < 0.5 else (-v) & MASK
    if p < 0.65:
        v = 1 << r.randint(0, 31)
        k = r.random()
        if k < 0.25:
            v = (v - 1) & MASK
        elif k < 0.5:
            v = (-v) & MASK
        return v & MASK
    return r.getrandbits(32)


def rand_divisor(r, zero_weight=0.03):
    if r.random() < zero_weight:
        return 0
    for _ in range(16):
        v = rand_operand(r)
        if v != 0:
            return v
    return 1


def rand_nonzero(r):
    for _ in range(16):
        v = r.getrandbits(32)
        if v != 0:
            return v
    return 1


def garbage_insn(r):
    """Arbitrary instruction word for idle cycles (pcpi_valid=0), incl. valid DIV encodings."""
    p = r.random()
    if p < 0.4:
        return encode(r.choice(OP_NAMES), r.randint(0, 31), r.randint(0, 31), r.randint(0, 31))
    if p < 0.6:
        # MUL-family encodings (funct3 0..3), not division
        return ((0b0000001 << 25) | (r.getrandbits(5) << 20) | (r.getrandbits(5) << 15)
                | (r.randint(0, 3) << 12) | (r.getrandbits(5) << 7) | 0b0110011)
    return r.getrandbits(32)


# --------------------------------------------------------------------------------------------
# PCPI master model (requester driver + per-edge protocol monitor)
# --------------------------------------------------------------------------------------------
class PcpiMaster:
    def __init__(self, dut, r):
        self.dut = dut
        self.r = r
        self.valid = 0
        self.insn = 0
        self.rs1 = 0
        self.rs2 = 0
        self.n_done = 0
        self.max_lat = 0
        self.min_lat = None

    def drive(self, valid, insn=None, rs1=None, rs2=None):
        if insn is not None:
            self.insn = insn & MASK
        if rs1 is not None:
            self.rs1 = rs1 & MASK
        if rs2 is not None:
            self.rs2 = rs2 & MASK
        self.valid = valid
        self.dut.pcpi_valid.value = valid
        self.dut.pcpi_insn.value = self.insn
        self.dut.pcpi_rs1.value = self.rs1
        self.dut.pcpi_rs2.value = self.rs2

    def reset_inputs_tracking(self):
        """After reset_dut (which drives all inputs to 0)."""
        self.valid = 0
        self.insn = 0
        self.rs1 = 0
        self.rs2 = 0

    def sample(self, chk):
        """Sample outputs for the coming rising edge and apply always-on protocol checks."""
        d = self.dut
        ready = val(d.pcpi_ready)
        wr = val(d.pcpi_wr)
        wait = val(d.pcpi_wait)
        assert ready is not None, f"{chk}: pcpi_ready is 0/1 got X/Z"
        assert wr is not None, f"{chk}: pcpi_wr is 0/1 got X/Z"
        assert not (wr == 1 and ready == 0), \
            f"CHK-002: pcpi_wr=1 only together with pcpi_ready=1 got pcpi_wr=1 pcpi_ready=0"
        if self.valid == 0:
            assert ready == 0 and wr == 0, \
                (f"{chk}: no pcpi_ready/pcpi_wr pulse while pcpi_valid=0 (CHK-003) "
                 f"got pcpi_ready={ready} pcpi_wr={wr}")
        return ready, wr, wait

    async def idle(self, n, chk, garbage=True):
        for _ in range(n):
            await next_cycle(self.dut)
            if garbage:
                self.drive(0, garbage_insn(self.r), self.r.getrandbits(32), self.r.getrandbits(32))
            else:
                self.drive(0)
            self.sample(chk)

    async def execute(self, op, rs1, rs2, chk="CHK-008", fields=None):
        """Issue one instruction at the next mid-cycle; return (pcpi_rd, latency in edges).

        Ends mid-cycle right after the pcpi_valid=0 deassert cycle has been driven/checked.
        """
        r = self.r
        if fields is None:
            fields = (r.randint(0, 31), r.randint(0, 31), r.randint(0, 31))
        insn = encode(op, *fields)
        tag = f"{op} rs1=0x{rs1 & MASK:08X} rs2=0x{rs2 & MASK:08X}"

        # NNC verification fix (fix-verif, triage B): every caller (previous execute() deassert,
        # idle(), setup, CHK-009 idle loop) ends mid-cycle right after driving pcpi_valid=0 for the
        # coming rising edge. Driving pcpi_valid=1 in that same mid-cycle overwrote it, so with
        # gap=0 no rising edge ever sampled pcpi_valid=0 between two instructions (back-to-back
        # spacing 37 edges instead of 38), which contradicts the contract master rule
        # (contract.json:223 "then drive pcpi_valid=0 on the next cycle"; contract.json:327
        # "deasserts pcpi_valid on the following cycle"). Advance one cycle first so the
        # pcpi_valid=0 already driven and checked is really sampled at a rising edge.
        await next_cycle(self.dut)

        # Issue: these inputs are sampled at the issue edge R_1.
        self.drive(1, insn, rs1, rs2)
        ready, wr, wait = self.sample(chk)
        assert ready == 0, \
            f"{chk}: pcpi_ready=0 at the issue edge of {tag} (nothing outstanding before) got 1"

        first_wait = None
        done_at = None
        rd = None
        for j in range(1, MAX_LAT + 1):
            await next_cycle(self.dut)          # inputs held stable
            ready, wr, wait = self.sample(chk)
            if ready == 1:
                assert wr == 1, \
                    f"{chk}: pcpi_wr=1 at the pcpi_ready edge of {tag} got pcpi_wr={wr}"
                rd = val(self.dut.pcpi_rd)
                assert rd is not None, f"{chk}: pcpi_rd known at completion of {tag} got X/Z"
                done_at = j
                break
            assert wait is not None, f"{chk}: pcpi_wait is 0/1 while {tag} runs got X/Z"
            if wait == 1:
                if first_wait is None:
                    first_wait = j
            elif first_wait is not None:
                assert False, \
                    (f"{chk}: pcpi_wait=1 on every edge from first pcpi_wait (edge {first_wait}) "
                     f"until pcpi_ready for {tag} got pcpi_wait=0 at edge {j}")
            if j == WAIT_DEADLINE:
                assert first_wait is not None, \
                    (f"{chk}: pcpi_wait=1 or pcpi_ready=1 within the first {WAIT_DEADLINE} edges "
                     f"after issue of {tag} got neither")
        assert done_at is not None, \
            f"{chk}: pcpi_ready=1 within {MAX_LAT} edges after issue of {tag} got timeout"

        # Next cycle: deassert pcpi_valid; DUT must not pulse ready/wr again.
        await next_cycle(self.dut)
        self.drive(0)
        self.sample(chk)

        self.n_done += 1
        self.max_lat = max(self.max_lat, done_at)
        self.min_lat = done_at if self.min_lat is None else min(self.min_lat, done_at)
        return rd, done_at


async def setup(dut, salt, chk):
    start_clock(dut)
    await reset_dut(dut)
    m = PcpiMaster(dut, rng(salt))
    m.reset_inputs_tracking()
    await m.idle(2, chk)
    return m


async def run_checked(m, op, a, b, chk, expected=None):
    exp = ref_model(op, a, b) if expected is None else expected
    rd, lat = await m.execute(op, a, b, chk=chk)
    assert rd == exp, \
        f"{chk}: {op} rs1=0x{a & MASK:08X} rs2=0x{b & MASK:08X} pcpi_rd=0x{exp:08X} got 0x{rd:08X}"
    if op == "REM" and rd != 0:
        assert (rd >> 31) == ((a & MASK) >> 31), \
            (f"{chk}: nonzero REM result has dividend sign ({(a & MASK) >> 31}) for "
             f"rs1=0x{a & MASK:08X} rs2=0x{b & MASK:08X} got rd=0x{rd:08X}")
    return rd, lat


# --------------------------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------------------------
@cocotb.test()
async def test_chk_004_directed_divide(dut):
    """CHK-004: Directed DIV/DIVU/REM/REMU results incl. rounding toward zero and remainder sign."""
    m = await setup(dut, "chk_004", "CHK-004")
    signed_pairs = [(7, 2), (0xFFFFFFF9, 2), (7, 0xFFFFFFFE), (0xFFFFFFF9, 0xFFFFFFFE),
                    (0xFFFFFFFA, 3), (0, 5), (0x80000000, 1), (0x7FFFFFFF, 0x7FFFFFFF)]
    div_exp = [3, 0xFFFFFFFD, 0xFFFFFFFD, 3, 0xFFFFFFFE, 0, 0x80000000, 1]
    rem_exp = [1, 0xFFFFFFFF, 1, 0xFFFFFFFF, 0, 0, 0, 0]
    unsigned_pairs = [(0xFFFFFFFF, 2), (0x80000000, 0xFFFFFFFF), (7, 2), (5, 7), (0xFFFFFFFF, 1)]
    divu_exp = [0x7FFFFFFF, 0, 3, 0, 0xFFFFFFFF]
    remu_exp = [1, 0x80000000, 1, 5, 0]

    cases = []
    for (a, b), e in zip(signed_pairs, div_exp):
        cases.append(("DIV", a, b, e))
    for (a, b), e in zip(signed_pairs, rem_exp):
        cases.append(("REM", a, b, e))
    for (a, b), e in zip(unsigned_pairs, divu_exp):
        cases.append(("DIVU", a, b, e))
    for (a, b), e in zip(unsigned_pairs, remu_exp):
        cases.append(("REMU", a, b, e))

    for op, a, b, e in cases:
        await run_checked(m, op, a, b, "CHK-004", expected=e)
        await m.idle(m.r.randint(0, 2), "CHK-004")
    dut._log.info(f"CHK-004: {len(cases)} directed cases, latency {m.min_lat}..{m.max_lat}")


@cocotb.test()
async def test_chk_005_random_divide(dut):
    """CHK-005: Constrained-random division (5000 instructions) against the reference model."""
    m = await setup(dut, "chk_005", "CHK-005")
    r = m.r
    n_zero = 0
    n_ovf = 0
    counts = {op: 0 for op in OP_NAMES}
    for _ in range(5000):
        op = r.choice(OP_NAMES)
        a = rand_operand(r)
        b = rand_divisor(r)
        if b == 0:
            n_zero += 1
        if a == 0x80000000 and b == 0xFFFFFFFF and op in ("DIV", "REM"):
            n_ovf += 1
        counts[op] += 1
        await run_checked(m, op, a, b, "CHK-005")
        await m.idle(r.randint(0, 3), "CHK-005")
    dut._log.info(f"CHK-005: done {m.n_done} ops {counts}, div-by-zero {n_zero}, "
                  f"overflow {n_ovf}, latency {m.min_lat}..{m.max_lat}")


@cocotb.test()
async def test_chk_006_divide_by_zero(dut):
    """CHK-006: Division by zero -> quotient all ones, remainder = dividend."""
    m = await setup(dut, "chk_006", "CHK-006")
    dividends = [0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF, 0x12345678]
    for op in OP_NAMES:
        for a in dividends:
            exp = 0xFFFFFFFF if op in ("DIV", "DIVU") else a
            await run_checked(m, op, a, 0, "CHK-006", expected=exp)
            await m.idle(m.r.randint(0, 2), "CHK-006")


@cocotb.test()
async def test_chk_007_signed_overflow(dut):
    """CHK-007: Signed division overflow (0x80000000 / -1) plus unsigned contrast."""
    m = await setup(dut, "chk_007", "CHK-007")
    expected = {"DIV": 0x80000000, "REM": 0x00000000, "DIVU": 0x00000000, "REMU": 0x80000000}
    for _ in range(2):
        for op in ("DIV", "REM", "DIVU", "REMU"):
            await run_checked(m, op, 0x80000000, 0xFFFFFFFF, "CHK-007", expected=expected[op])
            await m.idle(m.r.randint(0, 2), "CHK-007")


@cocotb.test()
async def test_chk_008_pcpi_handshake(dut):
    """CHK-008: PCPI handshake - early pcpi_wait, held until pcpi_ready, pcpi_wr with pcpi_ready."""
    m = await setup(dut, "chk_008", "CHK-008")
    r = m.r
    for rnd in range(3):
        for gap in (0, 1, 5):
            ops = OP_NAMES[:]
            r.shuffle(ops)
            for op in ops:
                a = r.getrandbits(32)
                b = rand_nonzero(r)
                await run_checked(m, op, a, b, "CHK-008")
                await m.idle(gap, "CHK-008")
    dut._log.info(f"CHK-008: {m.n_done} handshakes, latency {m.min_lat}..{m.max_lat}")


@cocotb.test()
async def test_chk_009_idle_after_reset(dut):
    """CHK-009: Idle after synchronous reset - no pcpi_ready/pcpi_wr, pcpi_wait low."""
    start_clock(dut)
    r = rng("chk_009")
    m = PcpiMaster(dut, r)
    dut.resetn.value = 0
    m.drive(0, garbage_insn(r), r.getrandbits(32), r.getrandbits(32))
    for rnd in range(3):
        await next_cycle(dut)
        dut.resetn.value = 0
        for _ in range(5):
            m.drive(0, garbage_insn(r), r.getrandbits(32), r.getrandbits(32))
            await next_cycle(dut)
        # Release reset: inputs driven now are sampled at the first edge with resetn=1.
        dut.resetn.value = 1
        for j in range(50):
            if j > 0:
                await next_cycle(dut)
            m.drive(0, garbage_insn(r), r.getrandbits(32), r.getrandbits(32))
            ready, wr, wait = m.sample("CHK-009")
            assert ready == 0, f"CHK-009: pcpi_ready=0 at idle edge {j} after reset got {ready}"
            assert wr == 0, f"CHK-009: pcpi_wr=0 at idle edge {j} after reset got {wr}"
            if j >= 2:
                assert wait == 0, \
                    f"CHK-009: pcpi_wait=0 at idle edge {j} after reset got {wait}"
        if rnd < 2:
            # Make the DUT busy once, so the next reset starts from a used state.
            await run_checked(m, r.choice(OP_NAMES), r.getrandbits(32), rand_nonzero(r), "CHK-009")
            await m.idle(1, "CHK-009")


@cocotb.test()
async def test_regression_random(dut):
    """CHK-001, CHK-002, CHK-003, CHK-005, CHK-008: broad legal random traffic with scoreboard."""
    m = await setup(dut, "regression", "CHK-005")
    r = m.r
    n_zero = 0
    n_ovf = 0
    n_reset = 0
    for i in range(3000):
        op = r.choice(OP_NAMES)
        p = r.random()
        if p < 0.03:
            a, b = 0x80000000, 0xFFFFFFFF
        elif p < 0.06:
            a, b = rand_operand(r), 0
        else:
            a, b = rand_operand(r), rand_divisor(r, 0.02)
        if b == 0:
            n_zero += 1
        if a == 0x80000000 and b == 0xFFFFFFFF and op in ("DIV", "REM"):
            n_ovf += 1
        await run_checked(m, op, a, b, "CHK-005")
        q = r.random()
        if q < 0.5:
            gap = 0
        elif q < 0.8:
            gap = r.randint(1, 3)
        else:
            gap = r.randint(4, 12)
        await m.idle(gap, "CHK-008")
        if i % 600 == 599:
            await reset_dut(dut, cycles=r.randint(1, 6))
            m.reset_inputs_tracking()
            n_reset += 1
            await m.idle(2, "CHK-009")
    dut._log.info(f"regression: {m.n_done} ops, div-by-zero {n_zero}, overflow {n_ovf}, "
                  f"resets {n_reset}, latency {m.min_lat}..{m.max_lat}")

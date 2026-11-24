# Verification report — c_pcpi_div

Generated 2026-11-24T06:48:18+00:00 by NNC Pipeline.

## Summary

| Item | Result |
|---|---|
| Rules | 23 — {'NOT_VERIFIED_BY_SIM': 16, 'VERIFIED': 7} |
| Checks | 9 — {'PASS': 9} |
| Tests | {'pass': 7} |
| Run set | 2 runs in 2 configurations (base, xrand); primary base.s1 |
| Integration | OK |
| Code coverage (RTL), line | 100.0 % (58/58 lines) |
| Code coverage (RTL), block | 100.0 % (16/16 statement blocks and branch arms) |
| Code coverage (RTL), expression | 100.0 % (37/37 condition terms) |
| Code coverage (RTL), toggle | 100.0 % (604/604 bit toggles 0->1 and 1->0) |
| Code coverage (RTL), functional | 85.7 % (30/35 cover points of the specification) |
| Mutation score | 100.0 % (12 killed / 0 survived / 0 not compiled) |
| Coverage target | not requested (`nnc cover <design> --target <n> --metric <m>`) |
| Clock/reset domain crossings (structural, `nnc cdc`) | clean: no crossing over 1 configuration(s), work/cdc.md |
| Triage | no failure to analyse |
| Agent cost | US$2.8175 in 15 calls (A1 0.0892, A12 0.1633, A17 0.4111, A2 0.0905, A3 0.0393, A4 0.2691, A5 0.0249, A6 0.2412, A7 0.4939, A9 0.995) |

## Sign-off conditions

| Condition | State |
|---|---|
| Gates G1-G3 approved | met — approved on delegation by an agent: a person should confirm |
| Interface conformance of the DUT | met |
| Every selected check PASS (no FAIL, NOT_HIT, NOT_RUN) | met |
| Every planned check selected | met |
| Every rule in a check or declared not verifiable | met |
| Every run of the run set built and ran | met — 2 runs |
| Mutation run | met |
| Per-requirement mutation score >= 85 % | met — 7 rules with attributed mutants |
| Clock/reset domain crossings: no structural violation (RR-33) | met — clean: no crossing (work/cdc.md) |

## Run set

Every check is merged over these runs: PASS when one run verified it and no run failed it; NOT_VERIFIABLE only when every run declared it so.

| Run | Parameters changed | Defines | Plusargs | Status | Tests | Failing assertions | Not verifiable here |
|---|---|---|---|---|---|---|---|
| base.s1 — the design configuration | defaults | — | — | ran | {'pass': 7} | none | 0 |
| xrand.s1 — the design configuration with random initial values of every variable without a reset: a check that passes only because flops start at 0 fails here | defaults | — | — | ran | {'pass': 7} | none | 0 |

## Gates

| Gate | State | Detail |
|---|---|---|
| G1_rules | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-23T09:57:44+00:00 |
| G2_contract | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-23T09:59:43+00:00 |
| G3_verif_sources | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-23T10:18:38+00:00 |
| G4_signoff | PENDING | artifacts ready for review |

## Checks

| Check | Kind | Title | Status | Evidence |
|---|---|---|---|---|
| CHK-001 | assertion | pcpi_wait stays asserted until pcpi_ready | **PASS** | hits 550528, fails 0; hit in 2/2 runs |
| CHK-002 | assertion | pcpi_wr only together with pcpi_ready | **PASS** | hits 16192, fails 0; hit in 2/2 runs |
| CHK-003 | assertion | pcpi_ready only in response to an outstanding pcpi_valid | **PASS** | hits 16192, fails 0; hit in 2/2 runs |
| CHK-004 | test | Directed DIV/DIVU/REM/REMU results incl. rounding toward zero and remainder sign | **PASS** | test_chk_004_directed_divide; verified in base.s1, xrand.s1 |
| CHK-005 | test | Constrained-random division against reference model | **PASS** | test_chk_005_random_divide, test_regression_random; verified in base.s1, xrand.s1 |
| CHK-006 | test | Division by zero | **PASS** | test_chk_006_divide_by_zero; verified in base.s1, xrand.s1 |
| CHK-007 | test | Signed division overflow | **PASS** | test_chk_007_signed_overflow; verified in base.s1, xrand.s1 |
| CHK-008 | test | PCPI handshake: early pcpi_wait, then pcpi_ready with pcpi_wr | **PASS** | test_chk_008_pcpi_handshake, test_regression_random; verified in base.s1, xrand.s1 |
| CHK-009 | test | Idle after reset: no completion without an instruction | **PASS** | test_chk_009_idle_after_reset; verified in base.s1, xrand.s1 |

## Requirement traceability (RTM)

| Rule | Spec ref | Statement | Checks | Mutation | Status |
|---|---|---|---|---|---|
| PD-T1.1-01 |  | The core asserts pcpi_valid, outputs the instruction word on pcpi_insn, and outputs the rs1 and rs2 register values on pcpi_rs1 and pcpi_rs2. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| PD-T1.1-02 |  | An external PCPI core can decode and execute the instruction and assert pcpi_ready when execution is finished. | CHK-003:PASS, CHK-005:PASS, CHK-008:PASS, CHK-009:PASS | 100.0 % (6/6) | **VERIFIED** |
| PD-T1.1-03 |  | The PCPI core can optionally write a result value to pcpi_rd and assert pcpi_wr. | CHK-002:PASS, CHK-004:PASS, CHK-005:PASS, CHK-008:PASS, CHK-009:PASS | 100.0 % (6/6) | **VERIFIED** |
| PD-T1.1-04 |  | The PicoRV32 core decodes the rd field of the instruction and writes the pcpi_rd value to the respective register. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| PD-T1.1-05 |  | An illegal instruction exception is raised and the respective interrupt handler is called. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| PD-T1.1-06 |  | The PCPI core should assert pcpi_wait as soon as the instruction is decoded successfully and keep it asserted until it asserts pcpi_ready. | CHK-001:PASS, CHK-008:PASS | 100.0 % (6/6) | **VERIFIED** |
| PD-T1.1-07 |  | Asserting pcpi_wait prevents the PicoRV32 core from raising an illegal instruction exception. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RVM-T1.1-01 |  | mul multiplies rs1 by rs2 as XLEN-bit values and writes the lower XLEN bits of the product to the destination register. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RVM-T1.1-02 |  | mulh, mulhu and mulhsu return the upper XLEN bits of the 2×XLEN-bit product for signed×signed, unsigned×unsigned and signed rs1×unsigned rs2 respectively. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RVM-T1.1-03 |  | Use mulh (or mulhu/mulhsu if appropriate) rdh,rs1,rs2 followed by mul rdl,rs1,rs2 to obtain both halves. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| RVM-T1.1-04 |  | Source specifiers rs1 and rs2 must be in the same order in both instructions, and rdh must not be the same as rs1 or rs2. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| RVM-T1.1-05 |  | Microarchitectures may fuse the two instructions into a single multiply operation instead of two separate multiplies. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RVM-T1.1-06 |  | mulw multiplies the lower 32 bits of the source registers and writes the sign extension of the lower 32 bits of the result to the destination register. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RVM-T1.1-07 |  | Signed arguments must be proper 32-bit signed values and unsigned arguments must have their upper 32 bits clear. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RVM-T1.2-01 |  | div and divu perform XLEN-bit signed and unsigned division of rs1 by rs2 rounding towards zero; rem and remu return the remainder of the corresponding division. | CHK-004:PASS, CHK-005:PASS, CHK-006:PASS, CHK-007:PASS | 100.0 % (10/10) | **VERIFIED** |
| RVM-T1.2-02 |  | The sign of a nonzero rem result equals the sign of the dividend. | CHK-004:PASS, CHK-005:PASS | 100.0 % (5/5) | **VERIFIED** |
| RVM-T1.2-03 |  | Use div rdq,rs1,rs2 followed by rem rdr,rs1,rs2 (or divu and remu if appropriate). | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| RVM-T1.2-04 |  | rdq must not be the same register as rs1 or rs2. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| RVM-T1.2-05 |  | Microarchitectures may fuse the two instructions into a single divide operation instead of two separate divides. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| RVM-T1.2-06 |  | divw and divuw divide the lower 32 bits of rs1 by those of rs2 as signed and unsigned and write the 32-bit quotient sign-extended to 64 bits in rd; remw and remuw give the corresponding remainders. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RVM-T1.2-07 |  | remw and remuw always sign-extend the 32-bit result to 64 bits, including on a divide by zero. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RVM-T1.2-08 |  | Division by zero returns all bits set (-1 for div/divw, 2^L-1 for divu/divuw) as quotient, and the remainder equals the dividend for rem/remw/remu/remuw. | CHK-006:PASS | 100.0 % (4/4) | **VERIFIED** |
| RVM-T1.2-09 |  | On signed overflow the quotient equals the dividend (-2^(L-1)) and the remainder is zero. | CHK-007:PASS | 100.0 % (4/4) | **VERIFIED** |

## Mutants

| ID | File:line | Operator | Status | Caught by | Rules | Equivalent? |
|---|---|---|---|---|---|---|
| M01 | picorv32.v:2444 | eq_to_ne | killed | test_chk_004_directed_divide, test_chk_005_random_divide, test_chk_006_divide_by_zero, test_chk_007_signed_overflow, tes | PD-T1.1-06, PD-T1.1-02, PD-T1.1-03, RVM-T1.2-01 |  |
| M02 | picorv32.v:2444 | negate_if | killed | CHK-001, test_chk_004_directed_divide, test_chk_005_random_divide, test_chk_006_divide_by_zero, test_chk_007_signed_over | PD-T1.1-06, PD-T1.1-02, PD-T1.1-03, RVM-T1.2-01 |  |
| M03 | picorv32.v:2476 | ne_to_eq | killed | test_chk_004_directed_divide, test_chk_005_random_divide, test_chk_008_pcpi_handshake, test_regression_random | RVM-T1.2-01, RVM-T1.2-09 |  |
| M04 | picorv32.v:2475 | or_to_and | killed | test_chk_004_directed_divide, test_chk_005_random_divide, test_chk_007_signed_overflow, test_chk_008_pcpi_handshake, tes | RVM-T1.2-01, RVM-T1.2-02, RVM-T1.2-09 |  |
| M05 | picorv32.v:2444 | and_to_or | killed | CHK-001, test_chk_004_directed_divide, test_chk_005_random_divide, test_chk_006_divide_by_zero, test_chk_007_signed_over | PD-T1.1-02, PD-T1.1-03, PD-T1.1-06 |  |
| M06 | picorv32.v:2444 | eq_to_ne | killed | test_chk_004_directed_divide, test_chk_005_random_divide, test_chk_006_divide_by_zero, test_chk_007_signed_overflow, tes | PD-T1.1-06, PD-T1.1-02, PD-T1.1-03, RVM-T1.2-01 |  |
| M07 | picorv32.v:2498 | negate_if | killed | test_chk_004_directed_divide, test_chk_005_random_divide, test_chk_006_divide_by_zero, test_chk_007_signed_overflow, tes | RVM-T1.2-01, RVM-T1.2-08, RVM-T1.2-09, RVM-T1.2-02 |  |
| M08 | picorv32.v:2476 | or_to_and | killed | test_chk_004_directed_divide, test_chk_005_random_divide, test_chk_006_divide_by_zero, test_chk_008_pcpi_handshake, test | RVM-T1.2-01, RVM-T1.2-02, RVM-T1.2-08 |  |
| M09 | picorv32.v:2476 | and_to_or | killed | test_chk_004_directed_divide, test_chk_005_random_divide, test_chk_006_divide_by_zero, test_chk_008_pcpi_handshake, test | RVM-T1.2-01, RVM-T1.2-02 |  |
| M10 | picorv32.v:2480 | negate_if | killed | CHK-003, test_chk_004_directed_divide, test_chk_005_random_divide, test_chk_006_divide_by_zero, test_chk_007_signed_over | RVM-T1.2-01, PD-T1.1-03, PD-T1.1-02, PD-T1.1-06, RVM-T1.2-08 |  |
| M11 | picorv32.v:2474 | or_to_and | killed | test_chk_004_directed_divide, test_chk_005_random_divide, test_chk_006_divide_by_zero, test_chk_008_pcpi_handshake, test | RVM-T1.2-01, RVM-T1.2-02, RVM-T1.2-08, RVM-T1.2-09 |  |
| M12 | picorv32.v:2453 | and_to_or | killed | test_chk_004_directed_divide, test_chk_005_random_divide, test_chk_006_divide_by_zero, test_chk_007_signed_overflow, tes | PD-T1.1-06, PD-T1.1-02, PD-T1.1-03 |  |

## Not verified by this run

- Formal proof (`nnc config <ip> formal=on`) was not run.
- Domain crossings were checked structurally (synchronizer structure, `nnc cdc`); gray coding and handshake protocols are not proven by that check.
- Sign-off STA, place and route and DFT are outside this flow (docs/SIGNOFF_SCOPE.md); `nnc rtl-check` gives a synthesis estimate of area and the longest combinational path.
- Rules marked NOT_VERIFIED_BY_SIM carry the contract's reason (static, structural, not observable...).
- Only the configurations of the run set above were simulated; code coverage is merged over its runs, mutation testing used the primary run base.s1.

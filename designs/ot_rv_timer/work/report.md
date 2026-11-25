# Verification report — ot_rv_timer

Generated 2026-11-25T09:42:54+00:00 by NNC Pipeline.

## Summary

| Item | Result |
|---|---|
| Rules | 228 — {'NOT_VERIFIED_BY_SIM': 77, 'VERIFIED': 151} |
| Checks | 35 — {'PASS': 35} |
| Tests | {'pass': 27} |
| Run set | 3 runs in 2 configurations (base, xrand); primary base.s1 |
| Integration | OK |
| Code coverage (RTL), line | 95.1 % (802/843 lines); 2458 points left out (package code the design does not contain), all points 24.3 % (802/3301) |
| Code coverage (RTL), block | 99.3 % (144/145 statement blocks and branch arms); 341 points left out (package code the design does not contain; 19 of them proven never reached after reset by formal, work/unr.md), all points 29.6 % (144/486) |
| Code coverage (RTL), expression | 92.7 % (520/561 condition terms); 5667 points left out (package code the design does not contain; 234 of them proven never reached after reset by formal, work/unr.md), all points 8.3 % (520/6228) |
| Code coverage (RTL), toggle | 98.4 % (10294/10458 bit toggles 0->1 and 1->0); 1318 points left out (constant bits; 232 of them proven constant after reset by formal, work/unr.md), all points 87.7 % (10333/11776) |
| Code coverage (RTL), functional | 97.4 % (38/39 cover points of the specification) |
| Code coverage without the modules the designer declares pre-verified | prim_alert_receiver, prim_alert_sender, prim_count, prim_esc_receiver, prim_esc_sender, prim_lfsr, prim_onehot_check, prim_prince, prim_secded_inv_39_32_dec, prim_secded_inv_39_32_enc, prim_secded_inv_64_57_dec, prim_secded_inv_64_57_enc (7 instances; config `coverage_preverified`) |
| ... without pre-verified modules, block | 99.0 % (100/101) |
| ... without pre-verified modules, expression | 91.3 % (285/312) |
| ... without pre-verified modules, line | 93.4 % (583/624) |
| ... without pre-verified modules, toggle | 98.9 % (9390/9498) |
| Mutation score | 58.3 % (21 killed / 15 survived / 0 not compiled) |
| Surviving mutants, formal equivalence (`nnc mutate-equiv`) | {'CEX': 3, 'ERROR': 1, 'PROVEN': 11}; score without the proven-equivalent mutants 84.0 % |
| Coverage target | expression 90.0 %: **target_met** (baseline 83.7 % -> 91.3 %, work/coverage.md) |
| Clock/reset domain crossings (structural, `nnc cdc`) | clean: no crossing over 1 configuration(s), work/cdc.md |
| Formal (SymbiYosys, depth 32) | {'BOUNDED': 2, 'CEX': 1, 'PROVEN': 7, 'TIMEOUT': 1, 'UNSUPPORTED': 2} — reset assumptions + verif/formal/nnc_env.sv, work/formal.md |
| Triage | 4 failure(s), 4 analysed: work/triage.md |
| Agent cost | US$25.5382 in 73 calls (A1 0.7677, A10 2.5976, A11 0.8472, A12 0.9085, A13 1.3201, A14 3.0479, A17 4.2877, A18 1.0327, A2 0.641, A3 0.9391, A4 1.7633, A5 0.3345, A6 0.4296, A7 4.1614, A9 2.46) |

## Sign-off conditions

| Condition | State |
|---|---|
| Gates G1-G3 approved | met — approved on delegation by an agent: a person should confirm |
| Interface conformance of the DUT | met |
| Every selected check PASS (no FAIL, NOT_HIT, NOT_RUN) | met |
| Every planned check selected | met |
| Every rule in a check or declared not verifiable | met |
| Every run of the run set built and ran | met — 3 runs |
| Mutation run | met |
| Per-requirement mutation score >= 85 % | **not met** — 9 rule(s) below: AH-T1.3.2-01, AH-T1.3.2-02, AH-T1.3.2-03, CP-T1.9.1-04, RT-4.2-03, RT-5-02, RT-5-05, RT-8-16, RT-T6.3-01 |
| Coverage target expression 90.0 % | met — target_met |
| Clock/reset domain crossings: no structural violation (RR-33) | met — clean: no crossing (work/cdc.md) |
| Formal: no counterexample, no vacuous or failed proof | **not met** — CEX 1 |

## Run set

Every check is merged over these runs: PASS when one run verified it and no run failed it; NOT_VERIFIABLE only when every run declared it so.

| Run | Parameters changed | Defines | Plusargs | Status | Tests | Failing assertions | Not verifiable here |
|---|---|---|---|---|---|---|---|
| base.s1 — the only configuration | defaults | — | — | ran | {'pass': 27} | none | 0 |
| base.s2 — the only configuration | defaults | — | — | ran | {'pass': 27} | none | 0 |
| xrand.s1 — the default configuration with random initial values of every variable without a reset (ROADMAP 23.4): a check that passes only because flops start at 0 fails here; its coverage is not merged | defaults | — | — | ran | {'pass': 27} | none | 0 |

## Gates

| Gate | State | Detail |
|---|---|---|
| G1_rules | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-20T11:04:43+00:00 |
| G2_contract | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-20T11:15:13+00:00 |
| G3_verif_sources | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-24T11:30:47+00:00 |
| G4_signoff | PENDING | artifacts ready for review |

## Checks

| Check | Kind | Title | Status | Evidence |
|---|---|---|---|---|
| CHK-001 | assertion | No alert signal-integrity failure | **PASS** | hits 883515, fails 0; hit in 3/3 runs; formal PROVEN |
| CHK-002 | assertion | o_alert is a single-cycle pulse per handshake | **PASS** | hits 1451, fails 0; hit in 3/3 runs; formal PROVEN |
| CHK-003 | assertion | No spurious alerts, no more pulses than test writes | **PASS** | hits 47, fails 0; hit in 3/3 runs; formal BOUNDED |
| CHK-004 | assertion | Interrupt output masked by INTR_ENABLE0.IE_0 | **PASS** | hits 847405, fails 0; hit in 3/3 runs; formal PROVEN |
| CHK-005 | assertion | Latched interrupt falls only after a clearing write or reset | **PASS** | hits 189, fails 0; hit in 3/3 runs; formal BOUNDED |
| CHK-006 | assertion | Outputs inactive during reset | **PASS** | hits 603, fails 0; hit in 3/3 runs; formal UNSUPPORTED |
| CHK-007 | assertion | Outputs change only at rising clock edges | **PASS** | hits 883395, fails 0; hit in 3/3 runs; formal UNSUPPORTED |
| CHK-008 | assertion | Test-bench host obligations (stimulus self-check) | **PASS** | hits 22566, fails 0; hit in 3/3 runs; formal CEX |
| CHK-009 | assertion | Every D-channel beat matches exactly one outstanding request | **PASS** | hits 11503, fails 0; hit in 3/3 runs; formal PROVEN |
| CHK-010 | assertion | Response opcode and size echo | **PASS** | hits 11503, fails 0; hit in 3/3 runs; formal PROVEN |
| CHK-011 | assertion | d_error value for classified requests | **PASS** | hits 11383, fails 0; hit in 3/3 runs; formal TIMEOUT |
| CHK-012 | assertion | D channel holds under back-pressure | **PASS** | hits 9238, fails 0; hit in 3/3 runs; formal PROVEN |
| CHK-013 | assertion | Response integrity never fails | **PASS** | hits 883515, fails 0; hit in 3/3 runs; formal PROVEN |
| CHK-014 | test | ALERT_TEST.fatal_fault triggers one alert per write | **PASS** | test_chk_014_alert_test_fatal_fault; verified in base.s1, base.s2, xrand.s1 |
| CHK-015 | test | ALERT_TEST.regwen rw0c locks alert testing until reset | **PASS** | test_chk_015_alert_regwen_rw0c; verified in base.s1, base.s2, xrand.s1 |
| CHK-016 | test | Command integrity error raises a repeating fatal alert until reset | **PASS** | test_chk_016_intg_error_fatal_alert, test_cov_104_intg_flip_commands; verified in base.s1, base.s2, xrand.s1 |
| CHK-017 | test | Unmapped offsets return error and change nothing | **PASS** | test_chk_017_unmapped_offsets; verified in base.s1, base.s2, xrand.s1 |
| CHK-018 | test | Byte writes per register width | **PASS** | test_chk_018_byte_writes; verified in base.s1, base.s2, xrand.s1 |
| CHK-019 | test | TL-UL protocol error cases | **PASS** | test_chk_019_protocol_errors; verified in base.s1, base.s2, xrand.s1 |
| CHK-020 | test | Sub-word reads return the full word | **PASS** | test_chk_020_subword_reads; verified in base.s1, base.s2, xrand.s1 |
| CHK-021 | test | Instruction-fetch reads | **PASS** | test_chk_021_instruction_fetch; verified in base.s1, base.s2, xrand.s1 |
| CHK-022 | test | Interrupt raised by tick when mtime >= mtimecmp | **PASS** | test_chk_022_intr_by_tick; verified in base.s1, base.s2, xrand.s1 |
| CHK-023 | test | Interrupt raised by a compare write while active | **PASS** | test_chk_023_intr_by_compare_write; verified in base.s1, base.s2, xrand.s1 |
| CHK-024 | test | Clearing by compare writes; mtime write does not clear | **PASS** | test_chk_024_clear_by_compare_write; verified in base.s1, base.s2, xrand.s1 |
| CHK-025 | test | INTR_STATE0 rw1c and event re-assertion | **PASS** | test_chk_025_intr_state_rw1c; verified in base.s1, base.s2, xrand.s1 |
| CHK-026 | test | Interrupt enable masking and raw INTR_STATE0 | **PASS** | test_chk_026_intr_enable_masking; verified in base.s1, base.s2, xrand.s1 |
| CHK-027 | test | INTR_TEST0 sets the latched state (wo field) | **PASS** | test_chk_027_intr_test; verified in base.s1, base.s2, xrand.s1 |
| CHK-028 | test | Reset values and register map | **PASS** | test_chk_028_reset_values; verified in base.s1, base.s2, xrand.s1 |
| CHK-029 | test | rw field access types and reserved bits | **PASS** | test_chk_029_rw_fields; verified in base.s1, base.s2, xrand.s1 |
| CHK-030 | test | Asynchronous reset, short reset window, pending response discarded | **PASS** | test_chk_030_async_reset; verified in base.s1, base.s2, xrand.s1 |
| CHK-031 | test | Tick period, step and counting while active | **PASS** | test_chk_031_tick_and_step; verified in base.s1, base.s2, xrand.s1 |
| CHK-032 | test | Inactive after reset and first-tick latency | **PASS** | test_chk_032_inactive_and_first_tick; verified in base.s1, base.s2, xrand.s1 |
| CHK-033 | test | Carry from lower to upper half and 64-bit compare | **PASS** | test_chk_033_carry_and_64bit_compare; verified in base.s1, base.s2, xrand.s1 |
| CHK-034 | test | Behaviour near 2^64: wrap and intermediate interrupt | **PASS** | test_chk_034_wrap_2_64; verified in base.s1, base.s2, xrand.s1 |
| CHK-035 | test | Outstanding requests and back-pressure | **PASS** | test_chk_035_outstanding_backpressure, test_regression_random; verified in base.s1, base.s2, xrand.s1 |

## Requirement traceability (RTM)

| Rule | Spec ref | Statement | Checks | Mutation | Status |
|---|---|---|---|---|---|
| RT-T2.2-01 |  | Each 64-bit counter increments by the step value whenever the prescaler times out. | CHK-031:PASS | 100.0 % (3/3) | **VERIFIED** |
| RT-T2.2-02 |  | Each timer generates an interrupt if its counter reaches or exceeds the programmed value. | CHK-022:PASS | — | **VERIFIED** |
| RT-T3.1-01 |  | The tick generator creates a tick every time its internal counter hits the CFG0.prescaler value. | CHK-031:PASS | 100.0 % (3/3) | **VERIFIED** |
| RT-T3.1-02 |  | Each tick increments mtime by the CFG0.step value. | CHK-031:PASS, CHK-032:PASS | 100.0 % (3/3) | **VERIFIED** |
| RT-T3.1-03 |  | The timer compares 64-bit mtime with 64-bit mtimecmp and raises an interrupt when mtime is greater than or equal to mtimecmp. | CHK-022:PASS, CHK-023:PASS, CHK-033:PASS | — | **VERIFIED** |
| RT-T3.2.2-01 |  | Each hart has its own tick generator and counter, so the number of prescaler, step, and mtime registers equals the number of harts. | CHK-028:PASS | — | **VERIFIED** |
| RT-T3.2.2-03 |  | The IP is fixed to one hart and one timer per hart. | CHK-017:PASS | 100.0 % (1/1) | **VERIFIED** |
| RT-T3.2.2-04 |  | There are separate interrupts per timer and a set of interrupt enable and state registers per hart. | CHK-028:PASS | — | **VERIFIED** |
| RT-T4.1-01 |  | The prescaler and step fields must be stable for the timer value to increment correctly. | CHK-031:PASS | — | **VERIFIED** |
| RT-T4.1-02 |  | Software should de-activate the timer before changing the prescaler or step fields, then proceed with the change. | CHK-031:PASS | — | **VERIFIED** |
| RT-T4.2-06 |  | mtimecmp shall be written after mtime in order to clear any pending interrupt condition. | CHK-024:PASS | — | **VERIFIED** |
| RT-T4.3-02 |  | Software may set mtimecmp to 0xFFFF_FFFF_FFFF_FFFF to get an intermediate interrupt. | CHK-034:PASS | — | **VERIFIED** |
| RT-T4.3-05 |  | Setting mtimecmp to 0xFFFF_FFFF_FFFF_FFFF - step + 1 works for the intermediate interrupt, since the last mtime before wrap is at least that large. | CHK-034:PASS | — | **VERIFIED** |
| RT-T4.4-01 |  | The RV_TIMER module generates the interrupt when mtime is greater than or equal to mtimecmp. | CHK-022:PASS | 100.0 % (1/1) | **VERIFIED** |
| RT-T4.4-02 |  | The interrupt can be cleared by writing 1 to the Interrupt Status register INTR_STATE0. | CHK-025:PASS | — | **VERIFIED** |
| RT-T4.4-03 |  | The interrupt can be cleared by updating mtimecmp; a write to either COMPARE_LOWER0_0 or COMPARE_UPPER0_0 clears the interrupt source. | CHK-024:PASS | — | **VERIFIED** |
| RT-T5.1-01 |  | ALERT_TEST register must be located at offset 0x0 with length 4 bytes. | CHK-014:PASS, CHK-028:PASS | — | **VERIFIED** |
| RT-T5.1-02 |  | CTRL must be at offset 0x4, length 4, reset to 0x0 with reset mask 0x1. | CHK-028:PASS, CHK-029:PASS | — | **VERIFIED** |
| RT-T5.1-03 |  | INTR_ENABLE0 must be at offset 0x100, length 4, reset to 0x0 with reset mask 0x1. | CHK-028:PASS, CHK-029:PASS | — | **VERIFIED** |
| RT-T5.1-04 |  | INTR_STATE0 must be at offset 0x104, length 4, reset to 0x0 with reset mask 0x1. | CHK-028:PASS | — | **VERIFIED** |
| RT-T5.1-05 |  | INTR_TEST0 must be at offset 0x108, length 4, reset value 0x0 with reset mask 0x1. | CHK-028:PASS | — | **VERIFIED** |
| RT-T5.1-06 |  | CFG0 must be at offset 0x10c, length 4, reset to 0x10000 with reset mask 0xff0fff. | CHK-028:PASS, CHK-029:PASS | — | **VERIFIED** |
| RT-T5.1-07 |  | TIMER_V_LOWER0 at offset 0x110 holds timer value [31:0] as rw field v, reset 0x0, mask 0xffffffff. | CHK-028:PASS, CHK-029:PASS | — | **VERIFIED** |
| RT-T5.1-08 |  | TIMER_V_UPPER0 at offset 0x114 holds timer value [63:32] as rw field v, reset 0x0, mask 0xffffffff. | CHK-028:PASS, CHK-029:PASS | — | **VERIFIED** |
| RT-T5.1-09 |  | COMPARE_LOWER0_0 at offset 0x118 holds compare value [31:0] as rw field v, reset 0xffffffff, mask 0xffffffff. | CHK-028:PASS, CHK-029:PASS | — | **VERIFIED** |
| RT-T5.1-10 |  | COMPARE_UPPER0_0 at offset 0x11c holds compare value [63:32] as rw field v, reset 0xffffffff, mask 0xffffffff. | CHK-028:PASS, CHK-029:PASS | — | **VERIFIED** |
| RT-T5.2-01 |  | ALERT_TEST must reset to 0x80000000 with reset mask 0x80000001. | CHK-015:PASS, CHK-028:PASS | — | **VERIFIED** |
| RT-T5.2.1-01 |  | Writing 0 to regwen disables alert testing until the next reset; regwen can only be cleared, not set, by writes. | CHK-015:PASS | — | **VERIFIED** |
| RT-T5.2.1-03 |  | Writing 1 to fatal_fault triggers one alert event of the fatal kind. | CHK-014:PASS | 100.0 % (1/1) | **VERIFIED** |
| RT-T5.3.1-01 |  | When active_0 is 1 the timer operates; bits 31:1 of CTRL are reserved. | CHK-029:PASS, CHK-031:PASS, CHK-032:PASS | 100.0 % (2/2) | **VERIFIED** |
| RT-T5.4.1-01 |  | IE_0 (bit 0, rw, reset 0x0) is the interrupt enable for the timer; bits 31:1 are reserved. | CHK-004:PASS, CHK-026:PASS, CHK-029:PASS | — | **VERIFIED** |
| RT-T5.5.1-01 |  | IS_0 (bit 0, rw1c, reset 0x0) holds the timer interrupt status and is cleared by writing 1; bits 31:1 are reserved. | CHK-025:PASS | — | **VERIFIED** |
| RT-T5.6.1-01 |  | T_0 (bit 0, wo, reset x) is the interrupt test for timer; bits 31:1 are reserved. | CHK-027:PASS | — | **VERIFIED** |
| RT-T5.7.1-01 |  | CFG0 step (bits 23:16, rw, reset 0x1) is the increment per tick; prescale (bits 11:0, rw, reset 0x0) generates the tick; other bits reserved. | CHK-029:PASS, CHK-031:PASS | 100.0 % (2/2) | **VERIFIED** |
| RT-T6.1-01 |  | The racl_policies input must carry the incoming RACL policy vector from a racl_ctrl instance, with the policy selection vector parameter selecting the policy for each register. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RT-T6.2-01 |  | The module must raise interrupt timer_expired_hart0_timer0 when hart0's timer0 has expired (mtime >= mtimecmp). | CHK-022:PASS | 100.0 % (1/1) | **VERIFIED** |
| RT-T6.3-01 |  | The fatal_fault alert must be triggered when a fatal TL-UL bus integrity fault is detected inside RV_TIMER. | CHK-016:PASS | 66.7 % (2/3) **below** | **VERIFIED** |
| RT-1-01 |  | The design under verification has exactly one hart and one timer (N_HARTS = 1, N_TIMERS = 1). | CHK-017:PASS | — | **VERIFIED** |
| RT-1-02 |  | Every register access is permitted when RACL is disabled. | CHK-011:PASS, CHK-029:PASS, CHK-035:PASS | 100.0 % (2/2) | **VERIFIED** |
| RT-1-04 |  | The alert sender of rv_timer and the alert receiver of the wrapper both use the synchronous clocking scheme, with no synchronizer flops on the differential pairs. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RT-1-06 |  | Every run uses the single fixed configuration; there is no design parameter to vary. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RT-2-02 |  | All inputs are sampled and all outputs change at the rising edge of clk_i, except for the effect of rst_ni. | CHK-007:PASS | — | **VERIFIED** |
| RT-2-03 |  | rst_ni is active-low and may be asserted asynchronously, but its release must be synchronous to clk_i. | CHK-030:PASS | — | **VERIFIED** |
| RT-2-04 |  | Every register holds its reset value as given in the rv_timer specification register tables. | CHK-006:PASS, CHK-028:PASS, CHK-030:PASS | — | **VERIFIED** |
| RT-3-01 |  | i_a_opcode must encode TL-UL request types as Get = 4, PutFullData = 0 and PutPartialData = 1. | CHK-010:PASS | 100.0 % (1/1) | **VERIFIED** |
| RT-3-02 |  | i_a_instr = 1 marks the request as an instruction fetch (a_user.instr_type = MuBi4True); i_a_instr = 0 marks a data access (MuBi4False). | CHK-021:PASS | — | **VERIFIED** |
| RT-3-03 |  | When i_a_intg_flip is 1, the A-channel integrity sent with the request is corrupted. | CHK-016:PASS | — | **VERIFIED** |
| RT-3-04 |  | o_d_opcode must encode TL-UL response types as AccessAck = 0 and AccessAckData = 1. | CHK-010:PASS | 100.0 % (1/1) | **VERIFIED** |
| RT-3-05 |  | o_d_intg_err indicates that the response integrity of the D-channel beat is wrong. | CHK-013:PASS | 100.0 % (2/2) | **VERIFIED** |
| RT-3-06 |  | o_alert indicates that the alert fatal_fault was received. | CHK-014:PASS, CHK-016:PASS | 100.0 % (3/3) | **VERIFIED** |
| RT-3-07 |  | o_alert_integ_fail indicates a signal integrity failure on the alert differential pairs. | CHK-001:PASS | 100.0 % (1/1) | **VERIFIED** |
| RT-4.1-01 |  | The i_a_*, o_a_ready, o_d_* (except o_d_intg_err) and i_d_ready ports must be the same-named fields of the rv_timer TL-UL device interface tl, with TL-UL meaning. | CHK-009:PASS, CHK-010:PASS, CHK-012:PASS | 100.0 % (2/2) | **VERIFIED** |
| RT-4.1-03 |  | a_user.instr_type is MuBi4True when i_a_instr is 1 and MuBi4False when i_a_instr is 0. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| RT-4.1-04 |  | The test bench must follow the TL-UL host rules, including keeping A-channel signals stable while a_valid is 1 and a_ready is 0. | CHK-008:PASS, CHK-035:PASS | — | **VERIFIED** |
| RT-4.1-05 |  | The test bench may send requests listed as TL-UL error cases (unsupported opcode, bad size or mask, misaligned address) as legal stimulus. | CHK-019:PASS | — | **VERIFIED** |
| RT-4.1-06 |  | The device must answer such error-case requests with d_error = 1. | CHK-011:PASS, CHK-019:PASS | 100.0 % (2/2) | **VERIFIED** |
| RT-4.2-01 |  | The wrapper must compute a_user.cmd_intg and a_user.data_intg with the OpenTitan TL-UL host integrity generator, so the request carries correct integrity. | CHK-003:PASS, CHK-013:PASS | 100.0 % (2/2) | **VERIFIED** |
| RT-4.2-02 |  | Bit 0 of a_user.cmd_intg must be inverted. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| RT-4.2-03 |  | Such a request is a fatal TL-UL bus integrity fault that triggers the fatal_fault alert. | CHK-016:PASS | 0.0 % (0/1) **below** | **VERIFIED** |
| RT-4.3-01 |  | o_d_intg_err must be 1 in a cycle where o_d_valid is 1 and the d_user.rsp_intg check fails, and 0 otherwise. | CHK-013:PASS | 100.0 % (2/2) | **VERIFIED** |
| RT-4.3-02 |  | A correct device must never make o_d_intg_err 1. | CHK-013:PASS | 100.0 % (2/2) | **VERIFIED** |
| RT-5-01 |  | rv_timer has one alert, fatal_fault, sent through an alert sender. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RT-5-02 |  | o_alert is the receiver's alert_o output and is 1 for one clock cycle for each alert handshake the receiver detects. | CHK-002:PASS, CHK-014:PASS | 75.0 % (3/4) **below** | **VERIFIED** |
| RT-5-04 |  | A correct sender never makes o_alert_integ_fail 1. | CHK-001:PASS | 100.0 % (1/1) | **VERIFIED** |
| RT-5-05 |  | o_alert pulses repeatedly after a bus integrity fault until rst_ni is asserted, as a fatal alert is repeated until reset. | CHK-016:PASS | 50.0 % (2/4) **below** | **VERIFIED** |
| RT-5-06 |  | A write of 1 to ALERT_TEST.fatal_fault triggers exactly one alert event. | CHK-003:PASS, CHK-014:PASS | 100.0 % (5/5) | **VERIFIED** |
| RT-6-02 |  | o_intr_timer_expired must behave as an event-type interrupt per the comportability specification, with registers INTR_ENABLE0, INTR_STATE0 and INTR_TEST0. | CHK-026:PASS | — | **VERIFIED** |
| RT-7-01 |  | Verification shall cover reset values of every register through the ports. | CHK-028:PASS | 100.0 % (1/1) | **VERIFIED** |
| RT-7-02 |  | Verification shall cover the access type of every register field as given in the register tables (rw, rw1c, wo, rw0c). | CHK-015:PASS, CHK-025:PASS, CHK-027:PASS, CHK-029:PASS | 100.0 % (2/2) | **VERIFIED** |
| RT-7-03 |  | Verification shall cover the tick generator (prescaler) and the step. | CHK-031:PASS | 100.0 % (3/3) | **VERIFIED** |
| RT-7-04 |  | Verification shall cover counting of the 64-bit timer value, including writes to it and the carry from the lower to the upper half. | CHK-031:PASS, CHK-033:PASS, CHK-034:PASS | — | **VERIFIED** |
| RT-7-05 |  | Verification shall cover the compare and the interrupt: state, enable, test, and clearing by writing the compare registers. | CHK-022:PASS, CHK-023:PASS, CHK-024:PASS, CHK-026:PASS, CHK-027:PASS, CHK-033:PASS | — | **VERIFIED** |
| RT-7-06 |  | Verification shall cover ALERT_TEST with its regwen field. | CHK-014:PASS, CHK-015:PASS | — | **VERIFIED** |
| RT-7-07 |  | Verification shall cover bus error responses (unmapped addresses, sub-word writes, instruction fetches, integrity errors) and the fatal_fault alert. | CHK-016:PASS, CHK-017:PASS, CHK-018:PASS, CHK-019:PASS, CHK-021:PASS | — | **VERIFIED** |
| RT-7-08 |  | Behaviour close to 2^64 shall be reached by writing the timer value registers. | CHK-033:PASS, CHK-034:PASS | — | **VERIFIED** |
| RT-8-01 |  | Timer value increases by CFG0.step (modulo 2^64) once every CFG0.prescale + 1 cycles; prescale 0 gives a tick every cycle. | CHK-031:PASS | 100.0 % (3/3) | **VERIFIED** |
| RT-8-02 |  | The first tick shall come no later than CFG0.prescale + 1 + 4 cycles after the write response. | CHK-032:PASS | — | **VERIFIED** |
| RT-8-03 |  | Tests write CFG0 and TIMER_V_* only while CTRL.active_0 = 0; behaviour after such a write while active is not checked. | CHK-008:PASS | — | **VERIFIED** |
| RT-8-04 |  | INTR_STATE0.IS_0 shall read 1 within 4 cycles after a write of 1 to it. | CHK-025:PASS | — | **VERIFIED** |
| RT-8-05 |  | IS_0 shall be 1 no later than 4 cycles after that tick. | CHK-022:PASS | — | **VERIFIED** |
| RT-8-06 |  | IS_0 shall be 1 no later than CFG0.prescale + 1 + 4 cycles after the write response. | CHK-023:PASS | — | **VERIFIED** |
| RT-8-07 |  | o_intr_timer_expired shall equal IS_0 AND IE_0. | CHK-004:PASS, CHK-026:PASS | 100.0 % (1/1) | **VERIFIED** |
| RT-8-08 |  | IS_0 shall be 0 and the interrupt deasserted within 4 cycles. | CHK-024:PASS | — | **VERIFIED** |
| RT-8-09 |  | IS_0 shall be 1 again within 4 cycles; an intermediate dip is not checked. | CHK-024:PASS | — | **VERIFIED** |
| RT-8-10 |  | Write-only fields read 0, reserved bits read 0 and writes to them have no effect. | CHK-014:PASS, CHK-027:PASS, CHK-029:PASS | — | **VERIFIED** |
| RT-8-11 |  | INTR_TEST0 reads 0x0 and ALERT_TEST reads 0x8000_0000. | CHK-027:PASS, CHK-028:PASS | — | **VERIFIED** |
| RT-8-12 |  | Regwen reads 0 until reset; a later write of 0x8000_0001 completes with d_error = 0, triggers no alert. | CHK-003:PASS, CHK-015:PASS | 100.0 % (1/1) | **VERIFIED** |
| RT-8-13 |  | Exactly one o_alert pulse shall occur, no later than 16 cycles after the write response. | CHK-014:PASS | 100.0 % (1/1) | **VERIFIED** |
| RT-8-14 |  | At least one o_alert pulse and no more pulses than writes shall occur. | CHK-003:PASS, CHK-014:PASS | 100.0 % (1/1) | **VERIFIED** |
| RT-8-15 |  | Tests do not use the combined write 0x0000_0001; they write 0x8000_0001. | CHK-008:PASS | — | **VERIFIED** |
| RT-8-16 |  | o_alert shall pulse no later than 16 cycles after acceptance, then at least once every 32 cycles until rst_ni is asserted. | CHK-016:PASS | 0.0 % (0/1) **below** | **VERIFIED** |
| RT-8-17 |  | The test resets the design. | CHK-016:PASS | — | **VERIFIED** |
| RT-8-18 |  | A write with i_a_instr = 1 is not used. | CHK-008:PASS | — | **VERIFIED** |
| RT-8-19 |  | The slave returns d_error = 1 and changes no register. | CHK-011:PASS, CHK-017:PASS | 100.0 % (2/2) | **VERIFIED** |
| RT-8-20 |  | Requests at offset 0x200 and above are not used. | CHK-008:PASS | — | **VERIFIED** |
| RT-8-21 |  | Returns d_error = 1 and changes nothing. | CHK-011:PASS, CHK-018:PASS | — | **VERIFIED** |
| RT-8-22 |  | Completes with d_error = 0 and has the effect of the write. | CHK-011:PASS, CHK-018:PASS | 100.0 % (2/2) | **VERIFIED** |
| RT-8-23 |  | The write succeeds with d_error = 0. | CHK-011:PASS, CHK-029:PASS | 100.0 % (5/5) | **VERIFIED** |
| RT-8-25 |  | Match responses by d_source, use distinct a_source per outstanding request, and do not assume o_a_ready = 1. | CHK-008:PASS, CHK-035:PASS | 100.0 % (1/1) | **VERIFIED** |
| RT-8-26 |  | Returned value lies between values before the request and after the response. | CHK-031:PASS | — | **VERIFIED** |
| RT-8-27 |  | d_error is correct, d_source echoes a_source, d_size echoes a_size, d_opcode is AccessAckData for Get and AccessAck for PutFullData and PutPartialData. | CHK-010:PASS | 100.0 % (2/2) | **VERIFIED** |
| RT-8-28 |  | d_error = 1 is returned. | CHK-011:PASS, CHK-019:PASS | 100.0 % (2/2) | **VERIFIED** |
| RT-8-29 |  | The test bench keeps i_a_valid = 0. | CHK-008:PASS, CHK-030:PASS | — | **VERIFIED** |
| RT-8-30 |  | o_d_valid, o_alert, o_alert_integ_fail and o_intr_timer_expired shall be 0. | CHK-006:PASS | — | **VERIFIED** |
| RT-8-31 |  | The pending response is discarded. | CHK-030:PASS | — | **VERIFIED** |
| RT-8-32 |  | o_d_intg_err and o_alert_integ_fail shall be 0 in every cycle. | CHK-001:PASS, CHK-013:PASS | 100.0 % (3/3) | **VERIFIED** |
| RT-8-33 |  | Reached only by writing the timer value registers while inactive to values near the carry, then counting. | CHK-033:PASS, CHK-034:PASS | — | **VERIFIED** |
| RT-8-34 |  | Tests drive i_a_param = 0. | CHK-008:PASS | — | **VERIFIED** |
| TL-T2.2-01 |  | Existing TL-UL IP blocks may be used directly in devices that do not need the additional sideband signals. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T2.2-03 |  | The bus carries only one request and one response per cycle, and no burst transactions. | CHK-009:PASS | — | **VERIFIED** |
| TL-T2.3-01 |  | Bus primitives, hosts and peripherals developed with the extended specification can be used with blocks using the base specification. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T2.3-02 |  | As a receiver, a baseline block ignores the user signals. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T2.3-03 |  | As a source, a baseline block generates a project-specific default value for the user signals. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.1-02 |  | TL-UL devices tolerate reset windows shorter than 100 cycles. | CHK-030:PASS | — | **VERIFIED** |
| TL-T3.1.3.1-01 |  | Request steering must be a function of the address only; a_source and a_user must not enter into the address calculation. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.3.2-01 |  | A host may use a_source/d_source to ascribe request identifiers, since TL-UL does not guarantee in-order responses. | CHK-035:PASS | 100.0 % (1/1) | **VERIFIED** |
| TL-T3.1.3.2-02 |  | The fabric architect must ensure AIW covers the host outstanding requests and the maximum source ID growth added by bus primitives. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.3.2-03 |  | The fabric must provide enough host ID bits to maintain those ID values. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.3.2.1-01 |  | The primitive shifts a_source left and post-pends sub-source bits; on the response it shifts them off, shifting zeros into the top, and returns the result on d_source. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.3.2.1-02 |  | Assertions should ensure no significant bits of a_source are lost in M:1 sockets. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.3.2.2-01 |  | Hosts may only use the low bits of the source identifier and must not assume all AIW bits are returned intact. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.3.2.3-01 |  | Devices must return the associated a_source on the response d_source. | CHK-009:PASS | 100.0 % (1/1) | **VERIFIED** |
| TL-T3.1.3.3-01 |  | Bus hosts and devices must understand the usage of user bits and apply them appropriately. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.3.3-03 |  | The bus fabric must not rely on user bits for transport and must pass them on blindly; usage must be assigned project-wide. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.3.4-01 |  | a_opcode may designate a write (Put) or read (Get); writes may be full (PutFullData) or partial (PutPartialData). | CHK-029:PASS, CHK-035:PASS | 100.0 % (1/1) | **VERIFIED** |
| TL-T3.1.3.4-02 |  | TL-UL hosts in this project should not use non-contiguous a_mask values such as 0b1001. | CHK-008:PASS | — | **VERIFIED** |
| TL-T3.1.3.4-03 |  | Devices may assert d_error if they do not support a particular subword a_mask. | CHK-018:PASS | — | **VERIFIED** |
| TL-T3.1.3.4-04 |  | For PutFullData, a_size should be 'h2 for a 32b write ('h3 for 64b bus). | CHK-029:PASS | 100.0 % (1/1) | **VERIFIED** |
| TL-T3.1.3.4-05 |  | For PutPartialData, a_size should encode 2^a_size bytes and the a_mask bits should indicate the valid byte lanes. | CHK-029:PASS | 100.0 % (1/1) | **VERIFIED** |
| TL-T3.1.3.4-06 |  | Devices should return an error for undefined request opcodes. | CHK-011:PASS, CHK-019:PASS | — | **VERIFIED** |
| TL-T3.1.3.4-07 |  | Undefined response opcodes d_opcode 3'b01x and 3'b1xx should return an error. | CHK-010:PASS | 100.0 % (1/1) | **VERIFIED** |
| TL-T3.1.3.5-01 |  | TL-UL devices must raise a runtime error via d_error when a request carries a wrong opcode. | CHK-011:PASS, CHK-019:PASS | — | **VERIFIED** |
| TL-T3.1.3.5-02 |  | a_size must not be greater than 2; a request violating this is flagged by the device with d_error. | CHK-011:PASS, CHK-019:PASS | — | **VERIFIED** |
| TL-T3.1.3.5-03 |  | Inactive lanes must be marked with 'b0 in a_mask; violation is flagged by the device with d_error. | CHK-011:PASS, CHK-019:PASS | 100.0 % (1/1) | **VERIFIED** |
| TL-T3.1.3.5-04 |  | PutFullData must mark all active lanes with a 'b1 in a_mask; violation is flagged by the device with d_error. | CHK-011:PASS, CHK-019:PASS | 100.0 % (1/1) | **VERIFIED** |
| TL-T3.1.3.5-05 |  | TL-UL devices must raise a runtime error via d_error for accesses to non-existent addresses. | CHK-011:PASS, CHK-017:PASS | 100.0 % (1/1) | **VERIFIED** |
| TL-T3.1.3.5-07 |  | Register files always assume aligned 32-bit accesses, so accesses to them must be aligned 32-bit. | CHK-019:PASS | — | **VERIFIED** |
| TL-T3.1.3.5-08 |  | A host must discard orphaned responses (no valid request counterpart) and responses with the wrong opcode. | CHK-009:PASS | — | **VERIFIED** |
| TL-T3.1.3.5-10 |  | Devices and hosts may implement additional, more restrictive checks if needed. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.2-01 |  | Each peripheral must specify clocking via a nonempty list of clocking items, each defining clock and reset in fields named clock and reset. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.2-02 |  | Exactly one clocking item dictionary should have boolean field primary set to true. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.2-03 |  | The primary clock is used to clock any device interfaces. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.2-04 |  | Resets within the design are asynchronous active low: assertion is asynchronous to any clock, deassertion is synchronized to the clock of the associated storage element. | CHK-030:PASS | — | **VERIFIED** |
| CP-T1.5.2-05 |  | Security sensitive storage elements need special care, e.g. synchronous reset after chip-wide reset to a randomized value. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.2-06 |  | The clock and reset fields of a clocking item are optional. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.2-07 |  | The primary clock item must have both clock and reset fields. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.3-02 |  | Every peripheral must expose at least one device interface on the chip bus. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.3-03 |  | Peripherals can act as bus host on some occasions, though the processor being primary host is preferred. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.3-04 |  | The bus_interfaces attribute should contain a list of dictionaries describing the interfaces the peripheral exposes. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.3-05 |  | The peripheral must have protocol of tlul since all peripherals use TL-UL. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.3-06 |  | Each bus interface entry must contain a direction of either host or device. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.3-07 |  | All bus hosts must use the same clock as the defined primary host clock. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.3-08 |  | An entry may include a name, which is added as a prefix to the module's top-level port names. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.3-09 |  | The name field must be provided to avoid port name collisions. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.5-01 |  | The module must have an output named intr_name_o for each interrupt name. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.6-01 |  | All lowRISC peripheral designs must conform to the register specification. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8-01 |  | All interrupts shall have common naming, hardware interfaces, and software interfaces. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.1-01 |  | Wired CIP interrupts use active-high level-triggering. | CHK-005:PASS, CHK-022:PASS | 100.0 % (1/1) | **VERIFIED** |
| CP-T1.8.2-01 |  | Each interrupt_list entry must have a required name key of type string. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.2-02 |  | Each interrupt_list entry may have an optional desc string. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.2-03 |  | Each entry may have an optional type, Event or Status, defaulting to Event if unspecified. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.3-01 |  | A peripheral generates a separate wired interrupt for each interrupt source. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.3-02 |  | Peripherals do not send a single combined interrupt for the processor to disambiguate by querying the peripheral. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.4-01 |  | INTR_STATE, INTR_ENABLE and INTR_TEST registers are created at the top of the address map in that order, one bitfield per interrupt. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.4-02 |  | The .hjson must not define more than 32 interrupts per peripheral. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.4-03 |  | INTR_STATE at offset 0x0 holds interrupt state, INTR_ENABLE at 0x4 masks it to intr_o, INTR_TEST at 0x8 is write-only and asserts the interrupt. | CHK-026:PASS, CHK-027:PASS | — | **VERIFIED** |
| CP-T1.8.4-04 |  | INTR_STATE shows raw latched interrupt events and is not qualified by INTR_ENABLE. | CHK-026:PASS | — | **VERIFIED** |
| CP-T1.8.5-02 |  | The interrupt is cleared only by a software W1C write of the INTR_STATE bitfield. | CHK-005:PASS, CHK-025:PASS | — | **VERIFIED** |
| CP-T1.8.5-03 |  | Interrupt requests are triggered while input is true, including immediately after the previous request is acknowledged. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.5.1-01 |  | When the event occurs it is latched into the INTR_STATE bitfield and intr_o is latched high until acknowledged, then low. | CHK-005:PASS, CHK-022:PASS | — | **VERIFIED** |
| CP-T1.8.5.2-01 |  | A status type interrupt must drive a wired level-triggered interrupt directly from the hardware input signal, qualified only by INTR_ENABLE, staying asserted while the input is asserted. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.5.2-02 |  | The wired status interrupt must not deassert until the root cause of the hardware input signal is addressed by software intervention. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.5.2-03 |  | Software cannot acknowledge a status type interrupt through INTR_STATE, which is read-only (ro) in this context. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.5.2-05 |  | Software should mask the interrupt, at the peripheral or further up the tree such as the PLIC. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.5.2-06 |  | Masking at the peripheral can be achieved by clearing the corresponding bit in INTR_ENABLE. | CHK-026:PASS | — | **VERIFIED** |
| CP-T1.8.6-02 |  | The event must set the associated bit in INTR_STATE to 1. | CHK-022:PASS | — | **VERIFIED** |
| CP-T1.8.6-03 |  | A write of 1 to the associated foo bit of INTR_TEST can set the corresponding INTR_STATE bit. | CHK-027:PASS | — | **VERIFIED** |
| CP-T1.8.6-04 |  | The outgoing interrupt intr_foo_o must be the INTR_STATE output ANDed with INTR_ENABLE. | CHK-004:PASS, CHK-026:PASS | 100.0 % (1/1) | **VERIFIED** |
| CP-T1.8.6-05 |  | A write of 1 to an INTR_STATE bit clears the latched value, but INTR_STATE returns to true if the event is still active. | CHK-025:PASS | — | **VERIFIED** |
| CP-T1.8.6-06 |  | Hardware must not clear the latched interrupt state; only software can clear it. | CHK-005:PASS | — | **VERIFIED** |
| CP-T1.9.1-03 |  | A recoverable alert must be one-time triggered: the alert sender transmits a single alert event when the error condition is asserted. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.1-04 |  | A fatal alert must be continuously transmitted by the alert sender until the system is reset. | CHK-016:PASS | 0.0 % (0/1) **below** | **VERIFIED** |
| CP-T1.9.1-05 |  | Fatal alerts should also trigger local security countermeasures. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.1-07 |  | A peripheral may optionally send a regular IRQ for any alert event, if needed by the programming model. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.2-02 |  | Recoverable alerts must be prefixed with recov_ and fatal alerts must be prefixed with fatal_. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.2-03 |  | Alert names may default to just recov and/or fatal, implying no more than one alert of that type is exposed. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.3-01 |  | Every peripheral has a write-only (wo) ALERT_TEST register for software to test alert reporting in the alert handler. | CHK-014:PASS | — | **VERIFIED** |
| CP-T1.9.3-02 |  | Every alert has one field bit in ALERT_TEST, connected to the test input of the corresponding prim_alert_sender. | CHK-014:PASS | — | **VERIFIED** |
| CP-T1.9.4-01 |  | Internal events are sent active-high to the prim_alert_sender within the peripheral. | not verified: covered_by_other_check | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.4-02 |  | One prim_alert_sender must be instantiated per distinct alert event, with IsFatal set to 1 for fatal alerts so the alert is latched until reset. | CHK-016:PASS | — | **VERIFIED** |
| CP-T1.9.4-03 |  | The peripheral maintainer determines distinct alert events; multiple sources can be bundled depending on the required distinction. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.4-04 |  | Each peripheral should bundle alert sources into one or two distinct alerts, for example one fatal and one recoverable. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.4-05 |  | The IP should expose a cause register for disambiguation. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.4-06 |  | Cause registers for recoverable alerts must be clearable by SW or automatically cleared by HW. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.4-07 |  | Cause registers for fatal alerts must not be clearable in any way and must be read-only. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.4-08 |  | The prim_alert_sender converts the event into a differentially encoded signal pair routed to the hardware alert handler. | not verified: covered_by_other_check | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.3-03 |  | The name_reg2hw_t structure contains the signals driven from the register module to the rest of the hardware, including required .q, .qe and .re signals. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.3-04 |  | The name_hw2reg_t structure contains the signals driven from the rest of the hardware to the register module, including required .d and .de signals. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.4.1-01 |  | Accesses to unmapped target addresses fully representable with internal address bits typically return an error. | CHK-017:PASS | 100.0 % (1/1) | **VERIFIED** |
| RG-T1.4.1-02 |  | If the stripped address is mapped, the request is forwarded to the register and no error is returned. | not verified: not_applicable_to_dut | 100.0 % (2/2) | **NOT_VERIFIED_BY_SIM** |
| RG-T1.4.1-03 |  | A request to unmapped address 0x88 typically returns an error. | CHK-017:PASS | 100.0 % (1/1) | **VERIFIED** |
| RG-T1.4.1-04 |  | An error response is returned when TL-UL a_opcode has an illegal value. | CHK-011:PASS, CHK-019:PASS | — | **VERIFIED** |
| RG-T1.4.1-05 |  | A write smaller than the register size must return an error. | CHK-011:PASS, CHK-018:PASS | — | **VERIFIED** |
| RG-T1.4.1-06 |  | Writes smaller than 32b that are not word-aligned must return an error. | not verified: covered_by_other_check | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.4.1-07 |  | Reads smaller than a full word return the full register content and do not signal an error. | CHK-011:PASS, CHK-020:PASS | 100.0 % (1/1) | **VERIFIED** |
| RG-T1.4.1-08 |  | Read response data is always in its byte channel, e.g. a one-byte read to 0x3 returns the full word with the correct byte in bits [31:24]. | CHK-020:PASS | — | **VERIFIED** |
| RG-T1.4.1-09 |  | Windows should follow the error rules based on the declared validbits, though this may be relaxed in some cases. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.1-01 |  | The software-written value takes priority over the hardware update. | not verified: not_observable_at_interface | 100.0 % (1/1) | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.1-02 |  | The hardware can present updated values through de and d. | CHK-031:PASS | — | **VERIFIED** |
| RG-T1.5.1-03 |  | The register content is updated with d. | CHK-031:PASS | 100.0 % (1/1) | **VERIFIED** |
| RG-T1.5.1-05 |  | qe is a registered version of the bus write enable we, aligned with the change in q. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.3-02 |  | A software read returns a hardwired value equal to the register default value. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.4-01 |  | When re indicates the register is being read, the register contents are set to zero. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.6.1-01 |  | The subreg for R0W1C/RW1S/RW1C/RW0C types must handle simultaneous hardware and software write attempts. | CHK-025:PASS | — | **VERIFIED** |
| RG-T1.5.6.1-02 |  | Software has precedence over hardware, as for the RW type. | CHK-025:PASS | — | **VERIFIED** |
| RG-T1.5.6.1-04 |  | Hardware should feed the q value back into d, only setting bits with new events, to avoid collisions with software clearing. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.6.1-05 |  | The software clear must still take effect for one cycle to create a new interrupt edge, then q returns to 1 since d is still 1. | CHK-025:PASS | — | **VERIFIED** |
| RG-T1.5.6.2-01 |  | RW1C, RW1S and similar register types may be created with hwext true. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.6.2-02 |  | The auto-generated hardware is the same as the hwext RW register, with the implementation done outside the generated register block. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.6.2-03 |  | hwqe may be set true for these register types. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AH-T1.3.1-02 |  | Peripherals defining alerts should instantiate one prim_alert_sender module to convert the alert event into a signal to the alert handler. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AH-T1.3.2-01 |  | Alerts are encoded differentially and signaled using a full handshake on the alert_p/n and ack_p/n wires. | CHK-014:PASS | 66.7 % (2/3) **below** | **VERIFIED** |
| AH-T1.3.2-02 |  | The alert sender must keep repeating the native alert message and handshake pattern on its output wires while the alert is true. | CHK-016:PASS | 0.0 % (0/1) **below** | **VERIFIED** |
| AH-T1.3.2-03 |  | The sender waits 2 cycles between handshakes. | CHK-016:PASS | 0.0 % (0/1) **below** | **VERIFIED** |
| AH-T1.3.2-04 |  | The receiver must immediately propagate the first occurrence of an alert to alert_o. | CHK-014:PASS | 100.0 % (1/1) | **VERIFIED** |
| AH-T1.3.4-01 |  | The receiver must assert integ_fail_o when alert_tx_i.alert_p/n is incorrectly encoded. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AH-T1.3.4-02 |  | The sender must set alert_tx_o.alert_p/n to the same continuously toggling value, which triggers integ_fail_o on the receiver. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AH-T1.3.4-03 |  | Such lock-up must always trigger either a signal integrity alert or eventually a pingfail alert. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |

## Mutants

| ID | File:line | Operator | Status | Caught by | Rules | Equivalent? |
|---|---|---|---|---|---|---|
| M01 | prim_mubi_pkg.sv:72 | ne_to_eq | survived |  |  | formal CEX: outputs differ at step 4 after reset: o_d_data (original 11111111111111111111111111111111, mutant 00000000000000000000000000000000), o_d_error (original 1, muta (claimed: mubi4_test_false_loose is only called inside assertions in prim_alert_receiver. It drives no logic and no port, so the change is unobservable.) |
| M02 | tlul_err.sv:28 | eq_to_ne | killed | test_regression_random | TL-T3.1.3.5-04, RT-4.1-06, RT-8-28, TL-T3.1.3.5-03, RG-T1.4.1-07 |  |
| M03 | prim_secded_inv_39_32_enc.sv:17 | one_to_zero | killed | CHK-011, CHK-003, test_chk_014_alert_test_fatal_fault, test_chk_015_alert_regwen_rw0c, test_chk_016_intg_error_fatal_ale | RT-4.2-01, RT-4.3-02, RT-4.3-01, RT-8-32, RT-3-05 |  |
| M04 | prim_subreg.sv:75 | and_to_or | survived |  |  | formal PROVEN (claimed: The line sits in the gen_rc branch, which is elaborated only for SwAccessRC. rv_timer has no RC fields, so the branch never exists and qs=q regardless.) |
| M05 | prim_secded_inv_64_57_enc.sv:17 | one_to_zero | killed | CHK-011, CHK-013, CHK-003, test_chk_014_alert_test_fatal_fault, test_chk_015_alert_regwen_rw0c, test_chk_016_intg_error_ | RT-4.2-01, RT-4.3-02, RT-4.3-01, RT-8-32, RT-3-05 |  |
| M06 | prim_alert_sender.sv:199 | one_to_zero | killed | CHK-001, test_chk_014_alert_test_fatal_fault, test_chk_015_alert_regwen_rw0c, test_chk_016_intg_error_fatal_alert, test_ | RT-5-04, RT-3-07, RT-8-32, AH-T1.3.2-01 |  |
| M07 | prim_subreg_arb.sv:34 | eq_to_ne | killed | test_chk_018_byte_writes, test_chk_020_subword_reads, test_chk_021_instruction_fetch, test_chk_022_intr_by_tick, test_ch | RG-T1.5.1-01, RT-8-23, RT-T5.7.1-01, RT-T5.3.1-01, RT-7-02 |  |
| M08 | tlul_adapter_reg.sv:156 | eq_to_ne | killed | CHK-010, CHK-011, test_chk_014_alert_test_fatal_fault, test_chk_015_alert_regwen_rw0c, test_chk_016_intg_error_fatal_ale | RT-8-27, RT-3-04, RT-3-01, TL-T3.1.3.4-07, RT-4.1-01 |  |
| M09 | tlul_err.sv:79 | one_to_zero | killed | CHK-011, test_chk_014_alert_test_fatal_fault, test_chk_015_alert_regwen_rw0c, test_chk_016_intg_error_fatal_alert, test_ | RT-8-23, RG-T1.4.1-02, TL-T3.1.3.4-04, TL-T3.1.3.4-05, RT-1-02 |  |
| M10 | timer_core.sv:32 | eq_to_ne | killed | test_chk_022_intr_by_tick, test_chk_023_intr_by_compare_write, test_chk_024_clear_by_compare_write, test_chk_031_tick_an | RT-T3.1-01, RT-8-01, RT-T2.2-01, RT-T3.1-02, RT-7-03 |  |
| M11 | rv_timer_reg_top.sv:81 | one_to_zero | survived |  | RT-5-05, RT-8-16, CP-T1.9.1-04, RT-4.2-03, RT-T6.3-01 | formal PROVEN |
| M12 | prim_diff_decode.sv:234 | negate_if | survived |  |  | formal ERROR (claimed: In the synchronous decoder this inverts the reset of diff_pq/level_q. The only effects are that diff_pq/level_q are held at 0 instead of tracking the input. ris) |
| M13 | tlul_adapter_reg.sv:171 | one_to_zero | killed | test_chk_014_alert_test_fatal_fault, test_chk_015_alert_regwen_rw0c, test_chk_016_intg_error_fatal_alert, test_chk_017_u | RT-4.1-01, TL-T3.1.3.2.3-01, RT-8-27, RT-8-25, TL-T3.1.3.2-01 |  |
| M14 | tlul_adapter_reg.sv:221 | or_to_and | survived |  |  | formal CEX: outputs differ at step 4 after reset: o_d_data (original 11111111111111111111111111111111, mutant 00000000000000000000000000000000) |
| M15 | timer_core.sv:28 | negate_if | killed | test_chk_022_intr_by_tick, test_chk_023_intr_by_compare_write, test_chk_024_clear_by_compare_write, test_chk_031_tick_an | RT-T3.1-01, RT-8-01, RT-T2.2-01, RT-7-03, RT-T3.1-02 |  |
| M16 | tlul_err.sv:61 | negate_if | killed | CHK-011, test_chk_014_alert_test_fatal_fault, test_chk_015_alert_regwen_rw0c, test_chk_016_intg_error_fatal_alert, test_ | RG-T1.4.1-02, RT-8-23, RT-1-02, TL-T3.1.3.4-01, RT-8-22 |  |
| M17 | prim_flop.sv:16 | negate_if | killed | test_chk_014_alert_test_fatal_fault, test_chk_015_alert_regwen_rw0c, test_chk_016_intg_error_fatal_alert, test_chk_024_c | RT-5-06, RT-5-02, RT-3-06, AH-T1.3.2-01, RT-5-05 |  |
| M18 | timer_core.sv:35 | one_to_zero | killed | test_chk_022_intr_by_tick, test_chk_023_intr_by_compare_write, test_chk_024_clear_by_compare_write, test_chk_031_tick_an | RT-T3.1-01, RT-8-01, RT-T2.2-01, RT-T3.1-02, RT-7-03 |  |
| M19 | prim_alert_sender.sv:223 | negate_if | survived |  | AH-T1.3.2-01, AH-T1.3.2-03, AH-T1.3.2-02, RT-5-02, RT-5-05 | formal CEX: outputs differ at step 30 after reset: o_alert (original 0, mutant 1) |
| M20 | tlul_adapter_reg.sv:217 | negate_if | killed | CHK-010, CHK-011, test_chk_014_alert_test_fatal_fault, test_chk_015_alert_regwen_rw0c, test_chk_016_intg_error_fatal_ale | RT-8-19, RT-8-28, RT-4.1-06, RT-7-01 |  |
| M21 | prim_secded_inv_64_57_dec.sv:62 | eq_to_ne | survived |  |  | formal PROVEN (claimed: data_o of prim_secded_inv_64_57_dec is left unconnected in every user (tlul_cmd_intg_chk, tlul_rsp_intg_chk). Only syndrome/err_o are used, and they do not depe) |
| M22 | rv_timer_reg_top.sv:583 | zero_to_one | survived |  |  | formal PROVEN (claimed: The mutant makes addrmiss=1 when neither reg_re nor reg_we is active. error_i is only sampled when a request is accepted. In that case reg_re/reg_we is 1, unles) |
| M23 | prim_onehot_check.sv:98 | and_to_or | killed | CHK-003, test_chk_014_alert_test_fatal_fault, test_chk_015_alert_regwen_rw0c, test_chk_021_instruction_fetch, test_chk_0 | RT-8-14, RT-5-06, RT-8-12, RT-T6.3-01 |  |
| M24 | prim_intr_hw.sv:97 | negate_if | killed | CHK-006, test_chk_022_intr_by_tick, test_chk_023_intr_by_compare_write, test_chk_024_clear_by_compare_write, test_chk_02 | RT-8-07, CP-T1.8.6-04, RT-T6.2-01, RT-T4.4-01, CP-T1.8.1-01 |  |
| M25 | prim_alert_receiver.sv:109 | and_to_or | killed | test_chk_014_alert_test_fatal_fault, test_chk_015_alert_regwen_rw0c, test_chk_016_intg_error_fatal_alert, test_regressio | RT-5-02, RT-5-06, AH-T1.3.2-04, RT-3-06 |  |
| M26 | prim_alert_sender.sv:206 | or_to_and | killed | test_chk_014_alert_test_fatal_fault, test_chk_015_alert_regwen_rw0c, test_chk_016_intg_error_fatal_alert, test_regressio | RT-5-06, RT-T5.2.1-03, RT-8-13, RT-T6.3-01, RT-5-05 |  |
| M27 | prim_alert_sender.sv:171 | zero_to_one | survived |  |  | formal PROVEN (claimed: The line is in gen_recov, which is elaborated only for IsFatal=0. rv_timer instantiates the sender with IsFatal=1, so the line does not exist in the design.) |
| M28 | prim_subreg.sv:63 | negate_if | killed | test_chk_015_alert_regwen_rw0c, test_chk_016_intg_error_fatal_alert, test_chk_017_unmapped_offsets, test_chk_018_byte_wr | RT-7-02, RT-8-23, RG-T1.5.1-03, RT-T5.7.1-01, RT-T5.3.1-01 |  |
| M29 | prim_alert_receiver.sv:202 | zero_to_one | survived |  |  | formal PROVEN (claimed: send_ping in the InitReq state only feeds ping_tog_pd, which is forced to 0 by send_init in the same state. The change has no effect.) |
| M30 | prim_secded_inv_39_32_dec.sv:49 | eq_to_ne | survived |  |  | formal PROVEN (claimed: data_o of prim_secded_inv_39_32_dec is left unconnected in tlul_data_integ_dec. Only err_o is used, and it depends on the syndrome, not on data_o.) |
| M31 | prim_alert_receiver.sv:249 | one_to_zero | survived |  |  | formal PROVEN (claimed: The clamp only triggers on a sigint on the alert pair outside InitReq/InitAckWait. In this integration the only sigint is the deliberate one during the post-res) |
| M32 | prim_alert_receiver.sv:226 | or_to_and | survived |  |  | formal PROVEN (claimed: ping_req_i is tied to 0 in the wrapper, so ping_rise and ping_pending_q are always 0. send_ping is 0 under both || and &&.) |
| M33 | rv_timer_reg_top.sv:583 | or_to_and | killed | CHK-011, test_chk_017_unmapped_offsets, test_regression_random | RT-8-19, TL-T3.1.3.5-05, RG-T1.4.1-01, RG-T1.4.1-03, RT-T3.2.2-03 |  |
| M34 | prim_onehot_check.sv:108 | or_to_and | survived |  |  | formal PROVEN (claimed: oh0_err and enable_err are both 0 unless the write-enable vector is multi-hot or a write enable fires without en_i. Both need an internal fault, because write e) |
| M35 | prim_mubi_pkg.sv:44 | eq_to_ne | killed | CHK-011, test_chk_014_alert_test_fatal_fault, test_chk_015_alert_regwen_rw0c, test_chk_016_intg_error_fatal_alert, test_ | RT-8-22, RT-8-23, RT-5-06, RT-5-02, RT-3-06 |  |
| M36 | prim_diff_decode.sv:235 | zero_to_one | survived |  |  | formal PROVEN (claimed: A reset value of 1 for diff_pq in the sender's ping decoder creates a spurious fall event (ping_event=1) in the first cycle after reset. That cycle coincides wi) |

## Not verified by this run

- Formal: the assertions were checked by SymbiYosys under the environment assumptions (work/formal.md); a BOUNDED result holds only up to its depth.
- Domain crossings were checked structurally (synchronizer structure, `nnc cdc`); gray coding and handshake protocols are not proven by that check.
- Sign-off STA, place and route and DFT are outside this flow (docs/SIGNOFF_SCOPE.md); `nnc rtl-check` gives a synthesis estimate of area and the longest combinational path.
- Rules marked NOT_VERIFIED_BY_SIM carry the contract's reason (static, structural, not observable...).
- Only the configurations of the run set above were simulated; code coverage is merged over its runs, mutation testing used the primary run base.s1.

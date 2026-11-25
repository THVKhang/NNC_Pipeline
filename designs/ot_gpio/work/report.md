# Verification report — ot_gpio

Generated 2026-11-25T09:42:14+00:00 by NNC Pipeline.

## Summary

| Item | Result |
|---|---|
| Rules | 268 — {'NOT_VERIFIED_BY_SIM': 80, 'VERIFIED': 188} |
| Checks | 38 — {'PASS': 38} |
| Tests | {'pass': 28} |
| Run set | 6 runs in 5 configurations (base, sync_off, straps_off, min, xrand); primary base.s1 |
| Integration | OK |
| Code coverage (RTL), line | 97.3 % (11212/11520 lines); 9832 points left out (package code the design does not contain), all points 52.5 % (11212/21352) |
| Code coverage (RTL), block | 99.6 % (1090/1094 statement blocks and branch arms); 1358 points left out (package code the design does not contain; 70 of them proven never reached after reset by formal, work/unr.md), all points 44.5 % (1090/2452) |
| Code coverage (RTL), expression | 95.1 % (6600/6938 condition terms); 24968 points left out (package code the design does not contain; 3236 of them proven never reached after reset by formal, work/unr.md), all points 20.7 % (6600/31906) |
| Code coverage (RTL), toggle | 93.9 % (69704/74244 bit toggles 0->1 and 1->0); 8940 points left out (constant bits; 2376 of them proven constant after reset by formal, work/unr.md), all points 84.0 % (69898/83184) |
| Code coverage (RTL), functional | 95.0 % (38/40 cover points of the specification) |
| Code coverage without the modules the designer declares pre-verified | prim_alert_receiver, prim_alert_sender, prim_count, prim_esc_receiver, prim_esc_sender, prim_lfsr, prim_onehot_check, prim_prince, prim_secded_inv_39_32_dec, prim_secded_inv_39_32_enc, prim_secded_inv_64_57_dec, prim_secded_inv_64_57_enc (7 instances; config `coverage_preverified`) |
| ... without pre-verified modules, block | 99.6 % (914/918) |
| ... without pre-verified modules, expression | 97.1 % (5724/5894) |
| ... without pre-verified modules, line | 97.1 % (10336/10644) |
| ... without pre-verified modules, toggle | 94.5 % (62288/65884) |
| Mutation score | 58.3 % (21 killed / 15 survived / 0 not compiled) |
| Surviving mutants, formal equivalence (`nnc mutate-equiv`) | {'CEX': 4, 'ERROR': 2, 'PROVEN': 9}; score without the proven-equivalent mutants 77.8 % |
| Coverage target | toggle 90.0 %: **target_unmet** (baseline 87.5 % -> 87.5 %, work/coverage.md) |
| Earlier closure | functional 100.0 %: target_unmet (baseline 90.0 % -> 95.0 %, work/coverage_functional.md) |
| Clock/reset domain crossings (structural, `nnc cdc`) | clean: SYNC 64 over 4 configuration(s), work/cdc.md |
| Formal (SymbiYosys, depth 32) | {'PROVEN': 10, 'TIMEOUT': 1, 'UNSUPPORTED': 2} — reset assumptions + verif/formal/nnc_env.sv, work/formal.md |
| Triage | no failure to analyse |
| Agent cost | US$22.1904 in 74 calls (A1 0.9059, A10 3.6383, A11 0.6481, A12 1.5812, A13 0.544, A14 0.9184, A17 2.6852, A18 1.1687, A2 0.7038, A3 0.6687, A4 1.7198, A5 0.4537, A6 0.2562, A7 4.0072, A9 2.291) |

## Sign-off conditions

| Condition | State |
|---|---|
| Gates G1-G3 approved | met — approved on delegation by an agent: a person should confirm |
| Interface conformance of the DUT | met |
| Every selected check PASS (no FAIL, NOT_HIT, NOT_RUN) | met |
| Every planned check selected | met |
| Every rule in a check or declared not verifiable | met |
| Every run of the run set built and ran | met — 6 runs |
| Mutation run | met |
| Per-requirement mutation score >= 85 % | **not met** — 13 rule(s) below: AH-T1.3.2-01, AH-T1.3.2-03, GP-10-07, GP-10-08, GP-10-19, GP-3-01, GP-4.1-01, GP-4.1-03, GP-5-02, GP-5-05 |
| Coverage target toggle 90.0 % | **not met** — target_unmet |
| Clock/reset domain crossings: no structural violation (RR-33) | met — clean: SYNC 64 (work/cdc.md) |
| Formal: no counterexample, no vacuous or failed proof | met — {'PROVEN': 10, 'TIMEOUT': 1, 'UNSUPPORTED': 2} (work/formal.md) |

## Run set

Every check is merged over these runs: PASS when one run verified it and no run failed it; NOT_VERIFIABLE only when every run declared it so.

| Run | Parameters changed | Defines | Plusargs | Status | Tests | Failing assertions | Not verifiable here |
|---|---|---|---|---|---|---|---|
| base.s1 — GpioAsyncOn=1, GpioAsHwStrapsEn=1 (defaults) | defaults | — | — | ran | {'pass': 28} | none | 1 |
| base.s2 — GpioAsyncOn=1, GpioAsHwStrapsEn=1 (defaults) | defaults | — | — | ran | {'pass': 28} | none | 1 |
| sync_off.s1 — no input synchronizer | GpioAsyncOn=0 | — | — | ran | {'pass': 28} | none | 1 |
| straps_off.s1 — no strap sampling | GpioAsHwStrapsEn=0 | — | — | ran | {'pass': 28} | none | 1 |
| min.s1 — both off | GpioAsyncOn=0, GpioAsHwStrapsEn=0 | — | — | ran | {'pass': 28} | none | 1 |
| xrand.s1 — the default configuration with random initial values of every variable without a reset (ROADMAP 23.4): a check that passes only because flops start at 0 fails here; its coverage is not merged | defaults | — | — | ran | {'pass': 28} | none | 1 |

## Gates

| Gate | State | Detail |
|---|---|---|
| G1_rules | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-21T01:04:06+00:00 |
| G2_contract | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-21T01:13:18+00:00 |
| G3_verif_sources | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-21T15:49:42+00:00 |
| G4_signoff | PENDING | artifacts ready for review |

## Checks

| Check | Kind | Title | Status | Evidence |
|---|---|---|---|---|
| CHK-001 | assertion | Alert signal integrity never fails | **PASS** | hits 244448, fails 0; hit in 6/6 runs; formal PROVEN |
| CHK-002 | assertion | o_alert is a single-cycle pulse | **PASS** | hits 1035, fails 0; hit in 6/6 runs; formal PROVEN |
| CHK-003 | assertion | No alert without an alert cause | **PASS** | hits 1035, fails 0; hit in 6/6 runs; formal PROVEN |
| CHK-004 | assertion | o_gpio / o_gpio_en follow the DATA_OUT / DATA_OE shadow model | **PASS** | hits 203682, fails 0; hit in 6/6 runs; formal PROVEN |
| CHK-005 | assertion | D-channel response integrity never fails | **PASS** | hits 244448, fails 0; hit in 6/6 runs; formal PROVEN |
| CHK-006 | assertion | Disabled interrupts never assert o_intr_gpio | **PASS** | hits 229229, fails 0; hit in 6/6 runs; formal PROVEN |
| CHK-007 | assertion | Interrupt level is held until software acknowledges it | **PASS** | hits 63080, fails 0; hit in 6/6 runs; formal PROVEN |
| CHK-008 | assertion | Outputs held at zero during reset | **PASS** | hits 2059, fails 0; hit in 6/6 runs; formal PROVEN |
| CHK-009 | assertion | Strap outputs: invalid before the trigger, frozen after sampling | **PASS** | hits 160702, fails 0; hit in 4/6 runs; formal PROVEN |
| CHK-010 | assertion | Outputs change only at rising clock edges | **PASS** | hits 244240, fails 0; hit in 6/6 runs; formal UNSUPPORTED |
| CHK-011 | assertion | Test-bench stimulus legality monitor (host rules and plan constraints) | **PASS** | hits 244448, fails 0; hit in 6/6 runs; formal UNSUPPORTED |
| CHK-012 | assertion | D channel held stable under back-pressure | **PASS** | hits 22579, fails 0; hit in 6/6 runs; formal PROVEN |
| CHK-013 | assertion | Response matches an outstanding request (source/size/opcode echo, no orphans) | **PASS** | hits 59536, fails 0; hit in 6/6 runs; formal TIMEOUT |
| CHK-014 | test | ALERT_TEST.fatal_fault triggers exactly one o_alert pulse | **PASS** | test_chk_014_alert_test_pulse, test_regression_random; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-015 | test | ALERT_TEST.regwen rw0c locks alert testing until reset | **PASS** | test_chk_015_alert_regwen_lock; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-016 | test | Command integrity error raises the fatal alert, repeated until reset | **PASS** | test_chk_016_intg_error_fatal_alert, test_regression_random; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-017 | test | Input noise filter on DATA_IN and interrupt detection | **PASS** | test_chk_017_input_filter; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-018 | test | Direct write of DATA_OUT through DIRECT_OUT | **PASS** | test_chk_018_direct_out; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-019 | test | Masked writes of DATA_OUT through MASKED_OUT_LOWER / MASKED_OUT_UPPER | **PASS** | test_chk_019_masked_out; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-020 | test | DATA_OE: direct and masked writes, reads and o_gpio_en | **PASS** | test_chk_020_data_oe; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-021 | test | DATA_IN with filter off follows i_gpio only (both GpioAsyncOn values) | **PASS** | test_chk_021_data_in_follows_input; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-022 | test | Edge interrupts: rising, falling, both; latching, W1C, raw INTR_STATE | **PASS** | test_chk_022_edge_interrupts, test_regression_random; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-023 | test | Level interrupts: high, low, and W1C while the level holds | **PASS** | test_chk_023_level_interrupts; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-024 | test | INTR_TEST forcing and INTR_ENABLE masking per bit | **PASS** | test_chk_024_intr_test_and_enable; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-025 | test | PER_PIN_IO_i aliases DATA_OUT[i] / DATA_IN[i] and affects only GPIO i | **PASS** | test_chk_025_per_pin_io; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-026 | test | PER_PIN_OE_i / PER_PIN_INTR_CTRL_i alias their bit and affect only GPIO i | **PASS** | test_chk_026_per_pin_cfg; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-027 | test | Interrupt registers have no per-pin view | **PASS** | test_chk_027_no_per_pin_intr; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-028 | test | Reset values of every register | **PASS** | test_chk_028_reset_values; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-029 | test | Field access types: rw, wo, ro, rw0c, reserved bits; RACL off | **PASS** | test_chk_029_field_access_types; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-030 | test | Asynchronous reset assertion, short reset and discarding of a pending response | **PASS** | test_chk_030_async_short_reset; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-031 | test | Strap sampling with GpioAsHwStrapsEn=1 (once per reset, regardless of OE) | **PASS** | test_chk_031_strap_sampling, test_regression_random; verified in base.s1, base.s2, sync_off.s1, xrand.s1 |
| CHK-032 | test | HW_STRAPS_DATA_IN reads zero when GpioAsHwStrapsEn=0 | **PASS** | test_chk_032_straps_disabled; verified in straps_off.s1, min.s1 |
| CHK-033 | test | Aligned byte writes: rejected on wide registers, accepted on PER_PIN_OE / PER_PIN_INTR_CTRL | **PASS** | test_chk_033_byte_writes; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-034 | test | Sub-word reads return the full register | **PASS** | test_chk_034_subword_reads; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-035 | test | TL-UL protocol error cases answered with d_error=1 | **PASS** | test_chk_035_protocol_errors, test_cov_102_mask_size_combinations; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-036 | test | Unmapped offsets return d_error=1 and change nothing | **PASS** | test_chk_036_unmapped; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-037 | test | Instruction-fetch reads complete without side effects | **PASS** | test_chk_037_instr_fetch; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |
| CHK-038 | test | Outstanding requests and back-pressure | **PASS** | test_chk_038_outstanding_backpressure, test_regression_random; verified in base.s1, base.s2, sync_off.s1, straps_off.s1, min.s1, xrand.s1 |

## Requirement traceability (RTM)

| Rule | Spec ref | Statement | Checks | Mutation | Status |
|---|---|---|---|---|---|
| GP-T2.2-01 |  | Each of the 32 independent GPIO bits can be written as a peripheral output via direct write, giving software simultaneous control of all 32 bits. | CHK-018:PASS | 100.0 % (4/4) | **VERIFIED** |
| GP-T2.2-02 |  | Masked write modifies only the selected bits of a 16-bit half, using the user-provided mask and new values, without read-modify-write; unmasked bits keep their output value. | CHK-019:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-T2.2-03 |  | Software can read each of the 32 GPIO bits as peripheral inputs. | CHK-021:PASS | — | **VERIFIED** |
| GP-T2.2-04 |  | Software can configure interrupt event detection for any of the 32 bits as positive edge, negative edge or level detection. | CHK-022:PASS, CHK-023:PASS | — | **VERIFIED** |
| GP-T2.2-05 |  | The input must be stable for 16 module clock cycles before the input register reflects the change and interrupt generation is evaluated. | CHK-017:PASS | 50.0 % (1/2) **below** | **VERIFIED** |
| GP-T2.2-06 |  | A change in output value is reflected in the input register with a corresponding filter delay. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| GP-T3.2.1-01 |  | DIRECT_OUT provides full write and read access to all 32 bits of the DATA_OUT register. | CHK-018:PASS | 100.0 % (3/3) | **VERIFIED** |
| GP-T3.2.1-02 |  | Upper 16 bits of the write are a mask of bits to modify and lower 16 bits are data; hardware updates only masked DATA_OUT bits without read-modify-write. | CHK-019:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-T3.2.1-03 |  | Reads return the upper or lower 16 bits of DATA_OUT in the lower 16 bits, with zeros in the upper 16 mask-field bits. | CHK-019:PASS | — | **VERIFIED** |
| GP-T3.2.1-05 |  | DATA_OE is accessible directly via DIRECT_OE and with masked access via MASKED_OE_UPPER and MASKED_OE_LOWER, with the same semantics as DATA_OUT. | CHK-020:PASS | — | **VERIFIED** |
| GP-T3.2.1-06 |  | The output enable is sent to the pad control block to determine whether the pad drives the DATA_OUT value to the pin. | CHK-004:PASS, CHK-020:PASS | — | **VERIFIED** |
| GP-T3.2.1-07 |  | Output values of unused GPIOs are disconnected and have no effect on the GPIO input regardless of output enable values. | CHK-021:PASS | — | **VERIFIED** |
| GP-T3.2.2-01 |  | The per-pin and 32-bit register views alias the same state, and a write to a per-pin register affects only its own GPIO. | CHK-025:PASS, CHK-026:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-T3.2.2-02 |  | Per-pin view has separate aligned ranges: PER_PIN_IO holds one register per GPIO for DATA_OUT/DATA_IN bit i; configuration range holds consecutive PER_PIN_OE_n and PER_PIN_INTR_CTRL_n registers per GPIO. | CHK-025:PASS, CHK-026:PASS | — | **VERIFIED** |
| GP-T3.2.2-03 |  | A register write must cover all bytes of the register that hold a field. | CHK-033:PASS | — | **VERIFIED** |
| GP-T3.2.2-05 |  | INTR_STATE, INTR_ENABLE and INTR_TEST have no per-pin view. | CHK-027:PASS | — | **VERIFIED** |
| GP-T3.2.3-01 |  | DATA_IN is always readable and reflects the value at the chip input pad regardless of DATA_OE. | CHK-021:PASS | 100.0 % (2/2) | **VERIFIED** |
| GP-T3.2.3-02 |  | GPIO peripheral inputs not connected to a chip input are tied to constant zero. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| GP-T3.2.3-03 |  | Each of the 32 inputs can be independently enabled for the 16-cycle noise filter via CTRL_EN_INPUT_FILTER, applied to both DATA_IN and interrupt detection. | CHK-017:PASS | 66.7 % (2/3) **below** | **VERIFIED** |
| GP-T3.2.3.1-01 |  | GPIO detects strap_en_i low-to-high and one clock cycle later samples the GPIO inputs into HW_STRAPS_DATA_IN. | CHK-031:PASS | — | **VERIFIED** |
| GP-T3.2.3.1-02 |  | All 32 input bits are sampled regardless of output enable, and later input changes are not captured in HW_STRAPS_DATA_IN. | CHK-009:PASS, CHK-031:PASS | — | **VERIFIED** |
| GP-T3.2.4-02 |  | Interrupt state is readable in INTR_STATE only when enabled, and can be triggered only by GPIO input. | CHK-022:PASS, CHK-024:PASS | — | **VERIFIED** |
| GP-T3.2.4-03 |  | Writing 1 to an INTR_STATE bit clears that interrupt. | CHK-022:PASS | — | **VERIFIED** |
| GP-T3.2.4-04 |  | Each bit supports rising-edge, falling-edge, level-high and level-low interrupt detection, selected by the corresponding INTR_CTRL_EN register. | CHK-022:PASS, CHK-023:PASS | — | **VERIFIED** |
| GP-T3.2.4-05 |  | An input may be configured for both rising and falling edge detection, with no hardware indication of which edge caused the interrupt. | CHK-022:PASS | — | **VERIFIED** |
| GP-T3.2.4-06 |  | All inputs pass through the optional noise filter before interrupt detection. | CHK-017:PASS | — | **VERIFIED** |
| GP-T3.2.4-07 |  | Interrupts to the processor are level interrupts; edge detection is converted into a level interrupt. | CHK-022:PASS | — | **VERIFIED** |
| GP-T4.4-01 |  | Each component should be granted access only to the per-pin registers of its own GPIOs, while software managing all GPIOs keeps using the 32-bit registers. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| GP-T4.4-02 |  | A write to PER_PIN_IO_i must cover both bytes 0 and 1, i.e., be at least 16 bits wide. | CHK-025:PASS, CHK-033:PASS | — | **VERIFIED** |
| GP-T4.4-03 |  | A byte write to PER_PIN_IO_i returns an error and has no effect on the register. | CHK-033:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-T4.4-05 |  | PER_PIN_OE_i and PER_PIN_INTR_CTRL_i accept byte writes. | CHK-033:PASS | — | **VERIFIED** |
| GP-T5.1-01 |  | gpio core registers INTR_STATE through HW_STRAPS_DATA_IN must be accessible at offsets 0x0 to 0x44 in 4-byte steps, each 4 bytes long, with the listed functions. | CHK-028:PASS, CHK-029:PASS | 100.0 % (4/4) | **VERIFIED** |
| GP-T5.1-02 |  | PER_PIN_IO_0 to PER_PIN_IO_31 must be at offsets 0x100 to 0x17c in 4-byte steps, each 4 bytes long, giving a per-pin view of output and input data of one GPIO. | CHK-025:PASS, CHK-028:PASS | — | **VERIFIED** |
| GP-T5.1-03 |  | PER_PIN_OE_n and PER_PIN_INTR_CTRL_n for GPIO[n], n=0..31, must alternate at offsets 0x200 to 0x2fc in 4-byte steps, each 4 bytes long. | CHK-026:PASS, CHK-028:PASS | — | **VERIFIED** |
| GP-T5.2.1-01 |  | INTR_STATE.gpio bit is raised when the corresponding GPIO pin detects its configured interrupt mode; the field is rw1c (write 1 clears). | CHK-022:PASS, CHK-028:PASS | — | **VERIFIED** |
| GP-T5.4.1-01 |  | Writing 1 to INTR_TEST.gpio[i] forces INTR_STATE.gpio[i] to 1. | CHK-024:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-T5.5.1-01 |  | Writing 0 to ALERT_TEST.regwen disables alert testing until the next reset. | CHK-015:PASS | — | **VERIFIED** |
| GP-T5.5.1-02 |  | Writing 1 to ALERT_TEST.fatal_fault triggers one alert event of the fatal_fault kind. | CHK-014:PASS | 100.0 % (3/3) | **VERIFIED** |
| GP-T5.8-01 |  | Upper 16 bits of MASKED_OUT_LOWER are a mask; DATA_OUT[i] for i in 0..15 is updated with data[i] only if mask[i] is 1. | CHK-019:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-T5.8-02 |  | Reading MASKED_OUT_LOWER returns upper 16 bits as zero and lower 16 bits as DATA_OUT[15:0]. | CHK-019:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-T5.9-01 |  | Upper 16 bits of MASKED_OUT_UPPER are a mask; DATA_OUT[i] for i in 16..31 is updated from the lower 16 bits only if mask[i] is 1. | CHK-019:PASS | — | **VERIFIED** |
| GP-T5.9-02 |  | Reading MASKED_OUT_UPPER returns upper 16 bits as zero and lower 16 bits as DATA_OUT[31:16]. | CHK-019:PASS | — | **VERIFIED** |
| GP-T5.10-01 |  | Setting direct_oe[i] to 1 enables output mode for GPIO[i]. | CHK-020:PASS | — | **VERIFIED** |
| GP-T5.11-01 |  | Upper 16 bits of MASKED_OE_LOWER are a mask; DATA_OE[i] for i in 0..15 is updated from the lower 16 bits only if mask[i] is 1. | CHK-020:PASS | — | **VERIFIED** |
| GP-T5.11-02 |  | Reading MASKED_OE_LOWER returns upper 16 bits as zero and lower 16 bits as DATA_OE[15:0]. | CHK-020:PASS | — | **VERIFIED** |
| GP-T5.12-01 |  | Upper 16 bits of MASKED_OE_UPPER are a mask; DATA_OE[i] for i in 16..31 is updated from the lower 16 bits only if mask[i] is 1. | CHK-020:PASS | — | **VERIFIED** |
| GP-T5.12-02 |  | Reading MASKED_OE_UPPER returns upper 16 bits as zero and lower 16 bits as DATA_OE[31:16]. | CHK-020:PASS | — | **VERIFIED** |
| GP-T5.13-01 |  | Rising-edge interrupt detection on GPIO[i] is enabled. | CHK-022:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-T5.14-01 |  | Falling-edge interrupt detection on GPIO[i] is enabled. | CHK-022:PASS | — | **VERIFIED** |
| GP-T5.15-01 |  | Level-high interrupt detection on GPIO[i] is enabled. | CHK-023:PASS | — | **VERIFIED** |
| GP-T5.16-01 |  | Level-low interrupt detection on GPIO[i] is enabled. | CHK-023:PASS | — | **VERIFIED** |
| GP-T5.17-01 |  | A value of input bit [i] must be stable for 16 cycles before transitioning. | CHK-017:PASS | 66.7 % (2/3) **below** | **VERIFIED** |
| GP-T5.19-01 |  | GPIO input data is sampled at most once after reset on the first cycle where strap_en_i is high, and stored in HW_STRAPS_DATA_IN. | CHK-031:PASS | — | **VERIFIED** |
| GP-T5.19-02 |  | HW_STRAPS_DATA_IN reads as zero. | CHK-032:PASS | — | **VERIFIED** |
| GP-T5.20-01 |  | PER_PIN_IO bit 8 (data_in) aliases DATA_IN[i] and bit 0 (data_out) aliases DATA_OUT[i] for GPIO[i]. | CHK-025:PASS | — | **VERIFIED** |
| GP-T5.20-02 |  | Writing PER_PIN_IO updates only DATA_OUT[i], without affecting other GPIOs. | CHK-025:PASS | — | **VERIFIED** |
| GP-T5.21-01 |  | PER_PIN_OE_0 bit 0 aliases bit 0 of DIRECT_OE (DATA_OE[0]). | CHK-026:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-T5.21-02 |  | Writing PER_PIN_OE_0 updates only DATA_OE[0], without affecting other GPIOs. | CHK-026:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-T5.22-01 |  | PER_PIN_INTR_CTRL_0 bits 0..4 alias bit 0 of INTR_CTRL_EN_RISING, FALLING, LVLHIGH, LVLLOW and CTRL_EN_INPUT_FILTER respectively. | CHK-026:PASS | — | **VERIFIED** |
| GP-T5.22-02 |  | Writing PER_PIN_INTR_CTRL_0 updates only the configuration of GPIO[0], without affecting other GPIOs. | CHK-026:PASS | — | **VERIFIED** |
| GP-T5.23-01 |  | PER_PIN_OE_i at 0x200+8*i and PER_PIN_INTR_CTRL_i at 0x204+8*i behave like the index-0 registers for GPIO[i], with reset default 0x0. | CHK-026:PASS, CHK-028:PASS | — | **VERIFIED** |
| GP-T6.2-01 |  | On strap_en, gpio must take a snapshot of the input pins and provide the sampled values on sampled_straps. | CHK-031:PASS | — | **VERIFIED** |
| GP-T6.2-02 |  | The behaviour of strap_en after the snapshot event must have no effect on the sampled strap values. | CHK-009:PASS, CHK-031:PASS | — | **VERIFIED** |
| GP-T6.3-01 |  | The corresponding gpio interrupt event must be raised when a GPIO pin detects the configured interrupt mode. | CHK-022:PASS | — | **VERIFIED** |
| GP-T6.4-01 |  | The fatal_fault alert must be triggered when a fatal TL-UL bus integrity fault is detected. | CHK-016:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-1-01 |  | Every register access must be permitted and no access may be rejected for an access-control reason. | CHK-029:PASS | 100.0 % (2/2) | **VERIFIED** |
| GP-1-03 |  | Ping requests must never be issued. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| GP-2-02 |  | TL-UL and strap inputs are sampled and all outputs change only at the rising edge of clk_i, except for the effect of rst_ni. | CHK-010:PASS | — | **VERIFIED** |
| GP-2-03 |  | i_gpio may change at any time relative to clk_i. | CHK-021:PASS | — | **VERIFIED** |
| GP-2-04 |  | The test bench must change i_gpio only synchronously to clk_i, like the other inputs. | CHK-011:PASS, CHK-021:PASS | — | **VERIFIED** |
| GP-2-05 |  | rst_ni is active-low reset, asserted asynchronously and released synchronously to clk_i. | CHK-030:PASS | — | **VERIFIED** |
| GP-2-06 |  | While rst_ni is 0, every register holds its reset value given in the gpio specification register tables. | CHK-008:PASS, CHK-028:PASS, CHK-030:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-3-01 |  | i_a_instr=1 must make the request an instruction fetch (a_user.instr_type = MuBi4True); i_a_instr=0 must make it a data access (MuBi4False). | CHK-037:PASS | 50.0 % (1/2) **below** | **VERIFIED** |
| GP-3-02 |  | When i_a_intg_flip is 1, the A-channel integrity sent with the request must be corrupted. | CHK-016:PASS | — | **VERIFIED** |
| GP-3-03 |  | o_d_intg_err must indicate when the response integrity of the D-channel beat is wrong. | CHK-005:PASS | 100.0 % (2/2) | **VERIFIED** |
| GP-3-04 |  | o_alert must indicate that alert fatal_fault has been received. | CHK-014:PASS | 100.0 % (2/2) | **VERIFIED** |
| GP-3-05 |  | o_alert_integ_fail must indicate a signal integrity failure on the alert differential pairs. | CHK-001:PASS | — | **VERIFIED** |
| GP-3-06 |  | o_gpio (cio_gpio_o) must carry the value of DATA_OUT. | CHK-004:PASS, CHK-018:PASS | — | **VERIFIED** |
| GP-3-07 |  | o_gpio_en (cio_gpio_en_o) must carry the value of DATA_OE. | CHK-004:PASS, CHK-020:PASS | — | **VERIFIED** |
| GP-4.1-01 |  | The i_a_*, o_a_ready, o_d_* (except o_d_intg_err) and i_d_ready ports carry the same-named fields of the gpio TL-UL device interface tl, with TL-UL specification meaning. | CHK-012:PASS, CHK-013:PASS, CHK-038:PASS | 66.7 % (2/3) **below** | **VERIFIED** |
| GP-4.1-02 |  | a_user.rsvd is 0. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| GP-4.1-03 |  | a_user.instr_type is MuBi4True when i_a_instr is 1 and MuBi4False when i_a_instr is 0. | CHK-037:PASS | 50.0 % (1/2) **below** | **VERIFIED** |
| GP-4.1-04 |  | The test bench must follow the TL-UL host rules, for example keeping A-channel signals stable while a_valid is 1 and a_ready is 0. | CHK-011:PASS, CHK-038:PASS | — | **VERIFIED** |
| GP-4.1-06 |  | The device answers such error-case requests with d_error = 1. | CHK-035:PASS | — | **VERIFIED** |
| GP-4.2-01 |  | The wrapper computes correct a_user.cmd_intg and a_user.data_intg for every request, so a request with i_a_intg_flip = 0 carries correct integrity. | CHK-003:PASS | 100.0 % (3/3) | **VERIFIED** |
| GP-4.2-02 |  | Bit 0 of a_user.cmd_intg is inverted. | CHK-016:PASS | 100.0 % (2/2) | **VERIFIED** |
| GP-4.2-03 |  | The command integrity error is treated as a fatal TL-UL bus integrity fault and triggers the fatal_fault alert. | CHK-016:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-4.3-01 |  | o_d_intg_err is 1 in a cycle where o_d_valid is 1 and the d_user.rsp_intg check fails, and 0 otherwise. | CHK-005:PASS | 100.0 % (2/2) | **VERIFIED** |
| GP-4.3-02 |  | A correct device never makes o_d_intg_err 1. | CHK-005:PASS | 100.0 % (2/2) | **VERIFIED** |
| GP-5-01 |  | gpio has a single alert, fatal_fault, which is sent through an alert sender. | CHK-014:PASS | 100.0 % (4/4) | **VERIFIED** |
| GP-5-02 |  | o_alert is the alert_o output of the alert receiver and is 1 for exactly one clock cycle for each detected alert handshake. | CHK-002:PASS, CHK-014:PASS | 66.7 % (2/3) **below** | **VERIFIED** |
| GP-5-03 |  | o_alert_integ_fail is the integ_fail_o output of the alert receiver. | CHK-001:PASS | — | **VERIFIED** |
| GP-5-04 |  | A correct alert sender never makes o_alert_integ_fail 1. | CHK-001:PASS | — | **VERIFIED** |
| GP-5-05 |  | After a bus integrity fault, the fatal alert is repeated so o_alert pulses repeatedly until rst_ni is asserted. | CHK-016:PASS | 66.7 % (2/3) **below** | **VERIFIED** |
| GP-5-06 |  | A write of 1 to ALERT_TEST.fatal_fault triggers exactly one alert event. | CHK-014:PASS | — | **VERIFIED** |
| GP-6-01 |  | i_gpio, o_gpio and o_gpio_en must map to cio_gpio_i, cio_gpio_o and cio_gpio_en_o respectively, with bit i belonging to GPIO[i]. | CHK-004:PASS, CHK-018:PASS, CHK-021:PASS | — | **VERIFIED** |
| GP-6-03 |  | ot_gpio_nnc must not contain a pad model or pin multiplexer; i_gpio is driven only by the test bench and does not depend on o_gpio or o_gpio_en. | CHK-021:PASS | — | **VERIFIED** |
| GP-7-01 |  | o_intr_gpio[i] must be the interrupt output intr_gpio_o[i] of gpio, an event-type interrupt per the comportability specification, associated with bit i of INTR_ENABLE, INTR_STATE and INTR_TEST. | CHK-022:PASS, CHK-024:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-8-01 |  | The wrapper input i_strap_en must be connected to the gpio input strap_en_i. | CHK-031:PASS | — | **VERIFIED** |
| GP-8-02 |  | The wrapper output o_straps_valid must be driven by the valid field of the gpio output sampled_straps_o. | CHK-031:PASS | — | **VERIFIED** |
| GP-8-03 |  | The wrapper output o_straps_data must be driven by the data field of the gpio output sampled_straps_o. | CHK-031:PASS | — | **VERIFIED** |
| GP-9-01 |  | Verification must cover reset values of every register and the access type of every register field as given in the register tables. | CHK-028:PASS, CHK-029:PASS | 100.0 % (6/6) | **VERIFIED** |
| GP-9-02 |  | Verification must cover direct and masked writes of DATA_OUT and DATA_OE and their reads, and the per-pin register view. | CHK-018:PASS, CHK-019:PASS, CHK-020:PASS, CHK-025:PASS | 100.0 % (4/4) | **VERIFIED** |
| GP-9-03 |  | Verification must cover DATA_IN with and without the input filter. | CHK-017:PASS, CHK-021:PASS | — | **VERIFIED** |
| GP-9-04 |  | Verification must cover interrupt detection on rising edge, falling edge, high level and low level, with INTR_STATE, INTR_ENABLE and INTR_TEST. | CHK-022:PASS, CHK-023:PASS, CHK-024:PASS | — | **VERIFIED** |
| GP-9-05 |  | Verification must cover strap sampling with HW_STRAPS_DATA_IN_VALID and HW_STRAPS_DATA_IN. | CHK-031:PASS, CHK-032:PASS | — | **VERIFIED** |
| GP-9-06 |  | Verification must cover bus error responses (unmapped addresses, sub-word writes, instruction fetches, integrity errors) and the fatal_fault alert. | CHK-014:PASS, CHK-016:PASS, CHK-033:PASS, CHK-035:PASS, CHK-036:PASS, CHK-037:PASS | — | **VERIFIED** |
| GP-9-07 |  | The per-pin registers of all 32 GPIOs must behave alike. | CHK-025:PASS, CHK-026:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-9-09 |  | The selection of GPIOs must include GPIO[0], GPIO[15], GPIO[16] and GPIO[31]. | CHK-025:PASS, CHK-026:PASS | — | **VERIFIED** |
| GP-10-01 |  | DATA_OE[i] is set to data bit i where mask bit i is 1 and every other DATA_OE bit is left unchanged, as for DATA_OUT. | CHK-020:PASS | — | **VERIFIED** |
| GP-10-02 |  | Bits 15:0 of the read return the corresponding half of DATA_OUT or DATA_OE; bits 31:16 of MASKED_OUT_* read 0. | CHK-019:PASS, CHK-020:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-10-03 |  | DIRECT_OUT, DIRECT_OE, MASKED_*, INTR_CTRL_EN_*, CTRL_EN_INPUT_FILTER, PER_PIN_OE_i, PER_PIN_INTR_CTRL_i and PER_PIN_IO_i.data_out read 0; o_gpio and o_gpio_en are 0. | CHK-004:PASS, CHK-008:PASS, CHK-028:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-10-04 |  | A configured event sets INTR_STATE[i]. | CHK-022:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-10-05 |  | o_intr_gpio[i] stays 0. | CHK-006:PASS, CHK-024:PASS | — | **VERIFIED** |
| GP-10-06 |  | INTR_STATE[i] reads 1 and o_intr_gpio[i] with INTR_ENABLE[i] = 1 is 1 again within 4 cycles after the write response. | CHK-023:PASS | — | **VERIFIED** |
| GP-10-07 |  | The new value never appears in DATA_IN[i] and creates no interrupt event. | CHK-017:PASS | 50.0 % (1/2) **below** | **VERIFIED** |
| GP-10-08 |  | The new value appears in DATA_IN[i] no later than 24 cycles after the change. | CHK-017:PASS | 66.7 % (2/3) **below** | **VERIFIED** |
| GP-10-09 |  | Tests keep i_gpio[i] constant; DATA_IN[i] and interrupt events are not checked in this window. | CHK-017:PASS | 100.0 % (2/2) | **VERIFIED** |
| GP-10-10 |  | Tests keep i_strap_en = 0 while rst_ni = 0 and at least 4 cycles after release, raise it once, and keep i_gpio constant from 24 cycles before to 8 cycles after the rising edge. | CHK-011:PASS, CHK-031:PASS | — | **VERIFIED** |
| GP-10-11 |  | HW_STRAPS_DATA_IN_VALID reads 1, o_straps_valid = 1, and HW_STRAPS_DATA_IN and o_straps_data equal the sampled i_gpio value. | CHK-031:PASS | — | **VERIFIED** |
| GP-10-12 |  | Both valid indications are 0. | CHK-009:PASS, CHK-031:PASS | — | **VERIFIED** |
| GP-10-13 |  | Later changes of i_gpio or i_strap_en change neither the valid indications nor the strap data. | CHK-009:PASS, CHK-031:PASS | — | **VERIFIED** |
| GP-10-14 |  | HW_STRAPS_DATA_IN reads 0 at all times. | CHK-032:PASS | — | **VERIFIED** |
| GP-10-15 |  | Tests write 0x8000_0001 to keep regwen at 1 and do not use the combined write 0x0000_0001. | CHK-014:PASS | 100.0 % (2/2) | **VERIFIED** |
| GP-10-16 |  | A write of 0x8000_0001 completes with d_error = 0, triggers no alert, and regwen still reads 0. | CHK-015:PASS | — | **VERIFIED** |
| GP-10-17 |  | Exactly one o_alert pulse occurs, no later than 16 cycles after the write response. | CHK-014:PASS | — | **VERIFIED** |
| GP-10-18 |  | ALERT_TEST reads 0x8000_0000. | CHK-015:PASS, CHK-028:PASS | — | **VERIFIED** |
| GP-10-19 |  | Tests do not use a write with i_a_instr = 1; d_error of a request with i_a_instr = 1 is not checked. | CHK-011:PASS, CHK-037:PASS | 50.0 % (1/2) **below** | **VERIFIED** |
| GP-10-20 |  | The response has d_error = 1 and no register changes. | CHK-036:PASS | 100.0 % (2/2) | **VERIFIED** |
| GP-10-21 |  | Requests at offset 0x400 and above are not used. | CHK-011:PASS, CHK-036:PASS | — | **VERIFIED** |
| GP-10-22 |  | The write returns d_error = 1 and changes nothing. | CHK-033:PASS | — | **VERIFIED** |
| GP-10-23 |  | The write completes with d_error = 0 and has the effect of the write. | CHK-033:PASS | — | **VERIFIED** |
| GP-10-24 |  | The write succeeds. | CHK-029:PASS | 100.0 % (2/2) | **VERIFIED** |
| GP-10-26 |  | The test bench matches responses by d_source, uses a distinct a_source per outstanding request, and does not assume o_a_ready = 1. | CHK-011:PASS, CHK-038:PASS | — | **VERIFIED** |
| GP-10-27 |  | d_source echoes a_source, d_size echoes a_size, and d_opcode is AccessAckData for Get and AccessAck for PutFullData and PutPartialData. | CHK-013:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-10-28 |  | d_error = 1. | CHK-013:PASS, CHK-035:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-10-30 |  | The test bench keeps i_a_valid = 0 while rst_ni = 0 and in the first cycle after release. | CHK-011:PASS | — | **VERIFIED** |
| GP-10-31 |  | o_d_valid, o_alert, o_alert_integ_fail, o_intr_gpio, o_gpio and o_gpio_en are 0. | CHK-008:PASS, CHK-030:PASS | 100.0 % (2/2) | **VERIFIED** |
| GP-10-32 |  | The pending response is discarded. | CHK-013:PASS, CHK-030:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-10-33 |  | o_d_intg_err and o_alert_integ_fail are 0 in every cycle. | CHK-001:PASS, CHK-005:PASS | 100.0 % (2/2) | **VERIFIED** |
| GP-10-34 |  | o_alert pulses no later than 16 cycles later and then at least once in every 32 cycles until rst_ni is asserted. | CHK-016:PASS | — | **VERIFIED** |
| GP-10-35 |  | DATA_IN[i] shows the change no later than 4 cycles after the first rising edge after the change, for both values of GpioAsyncOn. | CHK-021:PASS | 100.0 % (1/1) | **VERIFIED** |
| GP-10-36 |  | INTR_STATE[i] is set no later than 4 cycles after it. | CHK-022:PASS | — | **VERIFIED** |
| GP-10-37 |  | o_intr_gpio[i] equals INTR_STATE[i] AND INTR_ENABLE[i]. | CHK-022:PASS, CHK-024:PASS | — | **VERIFIED** |
| GP-10-38 |  | o_gpio and o_gpio_en equal DATA_OUT and DATA_OE no later than 2 cycles after the write response. | CHK-004:PASS, CHK-018:PASS, CHK-020:PASS | — | **VERIFIED** |
| GP-10-39 |  | The register or field is left unchanged. | CHK-029:PASS | 100.0 % (2/2) | **VERIFIED** |
| GP-10-40 |  | The read returns 0. | CHK-029:PASS | — | **VERIFIED** |
| GP-10-41 |  | Reserved bits read 0 and writes to them have no effect. | CHK-029:PASS | — | **VERIFIED** |
| GP-10-43 |  | DATA_IN[i] follows i_gpio[i], not o_gpio[i]. | CHK-021:PASS | 100.0 % (1/1) | **VERIFIED** |
| TL-T2.2-01 |  | Existing TL-UL IP blocks may be used directly in devices that do not need the additional user sideband signals. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| TL-T2.2-03 |  | The bus carries at most one request and one response per cycle, and supports no burst transactions. | CHK-013:PASS, CHK-038:PASS | 100.0 % (1/1) | **VERIFIED** |
| TL-T2.3-01 |  | Bus primitives, hosts and peripherals developed with the extended specification can be used with blocks using the base specification. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| TL-T2.3-02 |  | A baseline block as receiver ignores the user signals. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T2.3-03 |  | A baseline block as source generates a project-specific default value for the user signals. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.1-01 |  | TL-UL host drivers in this library are not required to drive valid signals LOW for at least 100 cycles during reset, unlike the TileLink 1.7.1 requirement. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.1-02 |  | TL-UL devices tolerate shorter reset windows than the TileLink-specified 100 cycles. | CHK-030:PASS | — | **VERIFIED** |
| TL-T3.1.3.1-01 |  | All request steering to a device must be a function of the address only; a_source and a_user do not enter into address calculation. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.3.2-01 |  | A host may use source ID bits to ascribe request identifiers, since TL-UL does not guarantee in-order responses. | CHK-038:PASS | — | **VERIFIED** |
| TL-T3.1.3.2-02 |  | The fabric architect must ensure AIW is large enough for outstanding host requests plus maximum source ID growth added by bus primitives. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.3.2-03 |  | The fabric must provide enough host ID bits to maintain the converted host ID values. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.3.2.1-01 |  | The primitive shifts incoming a_source left and post-pends its sub-source bits. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.3.2.1-02 |  | The sub-source bits are shifted off with zeros shifted into the top, and the result is returned on the originator's d_source. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.3.2.1-03 |  | Assertions should be in place to ensure no significant bits of a_source are lost in M:1 sockets. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.3.2.2-01 |  | Hosts may only use the low bits of the source identifier and must not assume all AIW bits are returned intact. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.3.2.3-01 |  | A device must return the associated a_source value on the response d_source. | CHK-013:PASS | 100.0 % (1/1) | **VERIFIED** |
| TL-T3.1.3.3-02 |  | User bits follow the same timing as source ID bits: a_user matches a_source and d_user matches d_source. | CHK-005:PASS | — | **VERIFIED** |
| TL-T3.1.3.3-03 |  | The bus fabric must not rely on user bits for transport and should pass them on blindly; user bit usage is assigned project-wide. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.3.4-02 |  | TL-UL hosts should not assert non-contiguous a_mask values, only a restricted set of masks. | CHK-011:PASS | — | **VERIFIED** |
| TL-T3.1.3.4-03 |  | A device may assert d_error if it does not support a given contiguous or non-contiguous subword mask. | CHK-033:PASS | — | **VERIFIED** |
| TL-T3.1.3.4-04 |  | a_size should be 'h2 for a 32b write. | CHK-011:PASS | — | **VERIFIED** |
| TL-T3.1.3.4-05 |  | Bus devices should return an error for undefined request opcodes. | CHK-035:PASS | — | **VERIFIED** |
| TL-T3.1.3.5-01 |  | TL-UL devices must raise a runtime error via d_error when a request carries a wrong opcode. | CHK-035:PASS | — | **VERIFIED** |
| TL-T3.1.3.5-02 |  | a_size must not be greater than 2; a request violating this is flagged by the device with d_error. | CHK-035:PASS | — | **VERIFIED** |
| TL-T3.1.3.5-03 |  | TL-UL devices must raise d_error for accesses to non-existent addresses. | CHK-036:PASS | — | **VERIFIED** |
| TL-T3.1.3.5-04 |  | Inactive lanes must be marked with 'b0 in a_mask; otherwise the request has a wrong a_addr/a_size/a_mask combination and raises d_error. | CHK-035:PASS | — | **VERIFIED** |
| TL-T3.1.3.5-06 |  | A non-contiguous a_mask may lead to an error response, depending on device support. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.1.3.5-07 |  | Register files always assume aligned 32-bit accesses; other accesses are in violation. | CHK-033:PASS | — | **VERIFIED** |
| TL-T3.1.3.5-08 |  | The host side must discard orphaned responses and responses with the wrong opcode. | CHK-013:PASS | — | **VERIFIED** |
| CP-T1.5.2-01 |  | Exactly one clocking item dictionary should have the boolean field primary set to true. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.2-03 |  | The clock and reset fields of a clocking item are optional. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.2-04 |  | The primary clock clocking item must have both clock and reset fields. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.2.1-01 |  | Security storage elements should be handled with care regardless of reset methodology, since they might leak sensitive state content. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.3-02 |  | Every peripheral must expose at least one device interface on the chip bus. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.3-03 |  | Peripherals can act as a bus host, though the preferred model is the processor being primary host. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.3-04 |  | The bus_interfaces attribute in the configuration file should contain a list of dictionaries describing the interfaces the peripheral exposes. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.3-05 |  | The peripheral must have a protocol of tlul. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.3-06 |  | Each bus_interfaces entry must contain a direction, which must be either host or device. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.3-07 |  | All bus hosts must use the same clock as the defined primary host clock. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.3-08 |  | An entry must include a name so port names do not collide. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.5.5-01 |  | The module must have an output named intr_name_o for each interrupt name. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.6-01 |  | All lowRISC peripheral designs must conform to the register specification. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8-01 |  | All interrupts shall have common naming, hardware interfaces, and software interfaces. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.1-01 |  | Wired CIP interrupts use active-high level-triggering. | CHK-007:PASS | — | **VERIFIED** |
| CP-T1.8.2-01 |  | The name key, a string naming the interrupt, is required. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.2-02 |  | The desc key, a string describing the interrupt, is optional. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.2-03 |  | The type key is optional, selecting Event or Status, defaulting to Event if unspecified. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.3-01 |  | A peripheral generates a separate wired interrupt for each interrupt source. | CHK-024:PASS | — | **VERIFIED** |
| CP-T1.8.4-01 |  | INTR_STATE, INTR_ENABLE and INTR_TEST registers are created at offsets 0x0, 0x4, 0x8 with one bitfield per interrupt. | CHK-028:PASS | — | **VERIFIED** |
| CP-T1.8.4-02 |  | The .hjson must not define more than 32 interrupts per peripheral. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.4-03 |  | INTR_ENABLE enables/masks the output of INTR_STATE to create the wired interrupt signal intr_o. | CHK-006:PASS, CHK-024:PASS | — | **VERIFIED** |
| CP-T1.8.4-04 |  | INTR_TEST is write-only and asserts the interrupt for testing. | CHK-024:PASS | — | **VERIFIED** |
| CP-T1.8.4-05 |  | INTR_STATE is not qualified by INTR_ENABLE and shows the raw state of latched hardware interrupt events. | CHK-022:PASS | — | **VERIFIED** |
| CP-T1.8.5-01 |  | The current interrupt can only be cleared by handler acknowledgement, a W1C write to INTR_STATE. | CHK-007:PASS, CHK-022:PASS | — | **VERIFIED** |
| CP-T1.8.5.1-01 |  | The event is latched into its INTR_STATE bitfield and intr_o goes high; a software W1C write clears it and intr_o goes low. | CHK-022:PASS | — | **VERIFIED** |
| CP-T1.8.5.2-01 |  | A status type interrupt must be a wired level-triggered signal directly from the hardware input signal, qualified only by INTR_ENABLE, asserted continuously while the input is asserted. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.5.2-03 |  | Software cannot acknowledge a status type interrupt via INTR_STATE, which is read-only (ro) in this context. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.5.2-05 |  | Software should mask the interrupt, at the peripheral or further up the tree such as the PLIC. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.5.2-06 |  | Software can mask at the peripheral by clearing the corresponding bit in INTR_ENABLE. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.8.6-02 |  | The event sets the associated bit in INTR_STATE to 1. | CHK-022:PASS | — | **VERIFIED** |
| CP-T1.8.6-03 |  | A write of 1 to the foo bit of INTR_TEST can set the corresponding INTR_STATE bit. | CHK-024:PASS | — | **VERIFIED** |
| CP-T1.8.6-04 |  | The outgoing interrupt must be INTR_STATE ANDed with INTR_ENABLE. | CHK-006:PASS, CHK-024:PASS | — | **VERIFIED** |
| CP-T1.8.6-05 |  | A write of 1 to an INTR_STATE bit clears the latched value, but if the event is still active the bit returns to true. | CHK-023:PASS | — | **VERIFIED** |
| CP-T1.8.6-06 |  | Hardware must not clear the latched interrupt state; only software can. | CHK-007:PASS, CHK-022:PASS | — | **VERIFIED** |
| CP-T1.9.1-03 |  | A recoverable alert sender must transmit one single alert event when the error condition is asserted. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.1-04 |  | A fatal alert sender must continuously transmit alert events until the system is reset. | CHK-016:PASS | — | **VERIFIED** |
| CP-T1.9.1-05 |  | Fatal alerts should also trigger local security countermeasures. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.1-07 |  | A peripheral may optionally send a regular IRQ for any alert event. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.2-02 |  | Recoverable alerts must be prefixed recov_ and fatal alerts must be prefixed fatal_. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.2-03 |  | Alert names may default to just recov and/or fatal, implying only one alert of that type is exposed. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.3-01 |  | Each peripheral has a write-only ALERT_TEST register for software to test alert reporting. | CHK-014:PASS, CHK-029:PASS | — | **VERIFIED** |
| CP-T1.9.3-02 |  | Each alert has one field bit in ALERT_TEST, connected to the test input of the corresponding prim_alert_sender. | CHK-014:PASS | — | **VERIFIED** |
| CP-T1.9.4-01 |  | Internal events are sent active-high to the prim_alert_sender within the peripheral. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.4-02 |  | One prim_alert_sender must be instantiated per distinct alert event, with IsFatal set to 1 for fatal alerts. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.4-03 |  | The peripheral maintainer determines distinct alert events; multiple may be bundled. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.4-04 |  | Each peripheral should bundle alert sources into one or two distinct alerts, e.g. one fatal and one recoverable. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.4-05 |  | Comportable IPs with multiple bundled alerts should expose a cause register for disambiguation. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.4-06 |  | Recoverable alert cause registers must be clearable by SW or automatically cleared by HW. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.4-07 |  | Fatal alert cause registers must not be clearable and must be read-only. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| CP-T1.9.4-08 |  | The prim_alert_sender converts the event into a differentially encoded signal pair for the alert handler. | not verified: covered_by_other_check | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.4.1-01 |  | Accesses to unmapped addresses representable with the internal address bits typically return an error. | CHK-036:PASS | — | **VERIFIED** |
| RG-T1.4.1-02 |  | If the stripped address maps to a register, the request is forwarded to that register and no error is returned. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.4.1-04 |  | An error response is returned when TL-UL a_opcode has an illegal value. | CHK-035:PASS | — | **VERIFIED** |
| RG-T1.4.1-05 |  | A write smaller than the register size returns an error. | CHK-033:PASS | — | **VERIFIED** |
| RG-T1.4.1-06 |  | Sub-word writes that are not word-aligned return an error. | not verified: covered_by_other_check | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.4.1-07 |  | Reads smaller than a full word return the full register content and do not signal error. | CHK-034:PASS | — | **VERIFIED** |
| RG-T1.4.1-08 |  | Read response data is always in its byte channel, e.g. a byte read at 0x3 returns the full word with the correct byte in bits [31:24]. | CHK-034:PASS | — | **VERIFIED** |
| RG-T1.4.1-09 |  | The error rules above should be followed for windows based on the declared number of validbits, though this may be relaxed in some cases. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.4.1-10 |  | Errors need not be returned for unaligned sub-word writes. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.1-01 |  | Software write enable and write data have the highest priority in modifying register contents. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.1-02 |  | Hardware can present updated values via de and d; when de is true the register content is updated with d. | CHK-022:PASS | — | **VERIFIED** |
| RG-T1.5.1-03 |  | The software-written value is used. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.1-05 |  | qe is a registered version of the bus-side we, aligned with the change in q. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.2-01 |  | No de input is required from peripheral hardware; only d is added to the struct bundle. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.2-02 |  | qe timing is one cycle earlier than in the non-hwext model. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.3-01 |  | RO registers behave as RW registers with no wd and we inputs. | CHK-029:PASS | — | **VERIFIED** |
| RG-T1.5.3-02 |  | A software read returns a hardwired value equal to the register default value. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.4-01 |  | When re indicates the register is being read, the contents are set to zero. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.4-02 |  | RC registers are not recommended, except for backwards compatibility. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.4-03 |  | hwext must not be true for RC registers since re is not exported. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.5-01 |  | hwext should be set to true so outside hardware handles the write event. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.6-01 |  | These types are implemented with special prim_subreg configuration so writing sets values in type-specific ways. | CHK-029:PASS | — | **VERIFIED** |
| RG-T1.5.6.1-01 |  | The subreg must handle simultaneous hardware and software writes, with software taking precedence as for the RW type. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.6.1-03 |  | Hardware should feed the q value back into d, only setting bits with new events, to avoid collisions with software clearing. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.6.1-04 |  | Hardware may drive d and de to clear or set bits as it sees fit, including clearing all events, rather than set-only. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.6.1-05 |  | The software clear must still take effect for one cycle to create a new interrupt edge, after which q returns to 1 since d is still 1. | CHK-023:PASS | — | **VERIFIED** |
| RG-T1.5.6.2-01 |  | RW1C, RW1S and similar register types may be created with hwext true. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RG-T1.5.6.2-02 |  | hwqe may be set true for RW1C, RW1S and similar register types. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AH-T1.3.1-02 |  | Peripherals defining alerts must instantiate a prim_alert_sender to convert the alert event into a signal to the alert handler. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AH-T1.3.2-01 |  | Alerts are differentially encoded and signaled with a full handshake on alert_p/n and ack_p/n, repeated as long as the alert is true. | CHK-014:PASS, CHK-016:PASS | 50.0 % (1/2) **below** | **VERIFIED** |
| AH-T1.3.2-02 |  | The full handshake must back-pressure alert messages correctly so no alert is lost at the asynchronous boundary regardless of clock ratio. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AH-T1.3.2-03 |  | The native alert message is repeated on the output wires as long as the alert event remains true. | CHK-016:PASS | 50.0 % (1/2) **below** | **VERIFIED** |
| AH-T1.3.2-04 |  | The sender waits 2 cycles between handshakes. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AH-T1.3.2-05 |  | The receiver must immediately propagate the first alert occurrence to alert_o after synchronizing the initial level change on alert_tx_i.alert_p/n. | CHK-014:PASS | — | **VERIFIED** |
| AH-T1.3.2-06 |  | The alert sender and receiver modules can be used either synchronously or asynchronously. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AH-T1.3.2-07 |  | The signaling protocol remains the same in both synchronous and asynchronous use; synchronizer flops at the diff pair inputs may be omitted. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AH-T1.3.4-01 |  | The receiver must assert integ_fail_o when alert_tx_i.alert_p/n is incorrectly encoded. | CHK-001:PASS | — | **VERIFIED** |
| AH-T1.3.4-02 |  | The sender must set alert_tx_o.alert_p/n to the same continuously toggling value, causing the receiver to assert integ_fail_o. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AH-T1.3.4-03 |  | A protocol lock-up must always trigger either a signal integrity alert or eventually a pingfail alert. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |

## Mutants

| ID | File:line | Operator | Status | Caught by | Rules | Equivalent? |
|---|---|---|---|---|---|---|
| M01 | prim_alert_receiver.sv:226 | or_to_and | survived |  |  | formal PROVEN (claimed: Line is in the InitAckWait state, which is reached only after init_trig_i is MuBi4True. The wrapper ties init_trig_i to MuBi4False and ping_req_i to 0, so InitA) |
| M02 | prim_filter_ctr.sv:59 | zero_to_one | survived |  | GP-T3.2.3-03, GP-T5.17-01, GP-10-07, GP-T2.2-05, GP-10-08 | formal CEX: outputs differ at step 6 after reset: o_straps_data (original 00000000000000000000000000000000, mutant 00000000010000000000000000010000) |
| M03 | tlul_err.sv:26 | eq_to_ne | survived |  |  | formal PROVEN (claimed: op_full feeds only instr_wr_err, which is nonzero only when instr_type is MuBi4True. In that case tlul_adapter_reg's instr_error is already 1, because en_ifetch) |
| M04 | gpio_reg_top.sv:7140 | one_to_zero | killed | test_chk_014_alert_test_pulse, test_chk_015_alert_regwen_lock, test_chk_016_intg_error_fatal_alert, test_chk_017_input_f | GP-9-01, GP-T5.1-01, GP-T3.2.3-01, GP-9-02, GP-T3.2.1-01 |  |
| M05 | prim_onehot_check.sv:89 | zero_to_one | killed | CHK-003, test_chk_014_alert_test_pulse, test_chk_015_alert_regwen_lock, test_chk_016_intg_error_fatal_alert, test_chk_02 | GP-T6.4-01, GP-4.2-01, GP-4.2-03, GP-5-05, GP-4.2-02 |  |
| M06 | tlul_err.sv:84 | zero_to_one | survived |  |  | formal PROVEN (claimed: This is the default case, which only a_size=3 reaches. mask_chk is also 0 in that case, so a_config_allowed stays 0 and err_o stays 1 whatever addr_sz_chk is.) |
| M07 | prim_subreg_arb.sv:34 | eq_to_ne | killed | test_chk_017_input_filter, test_chk_022_edge_interrupts, test_chk_023_level_interrupts, test_chk_024_intr_test_and_enabl | GP-9-01, GP-10-39, GP-T3.2.1-01, GP-T2.2-01, GP-9-02 |  |
| M08 | prim_onehot_check.sv:96 | and_to_or | survived |  |  | formal PROVEN (claimed: and_tree is used only for the address check. prim_reg_we_check instantiates prim_onehot_check with AddrCheck=0, so addr_err is tied to 0 and and_tree is unused.) |
| M09 | prim_alert_receiver.sv:163 | zero_to_one | killed | test_chk_014_alert_test_pulse, test_chk_015_alert_regwen_lock, test_chk_016_intg_error_fatal_alert, test_regression_rand | GP-5-01, GP-5-02, GP-5-05, AH-T1.3.2-01, AH-T1.3.2-03 |  |
| M10 | prim_secded_inv_64_57_enc.sv:17 | one_to_zero | killed | CHK-005, CHK-003, test_chk_014_alert_test_pulse, test_chk_015_alert_regwen_lock, test_chk_016_intg_error_fatal_alert, te | GP-4.3-01, GP-4.3-02, GP-3-03, GP-4.2-01, GP-10-33 |  |
| M11 | tlul_adapter_reg.sv:171 | one_to_zero | killed | CHK-006, CHK-007, test_chk_014_alert_test_pulse, test_chk_015_alert_regwen_lock, test_chk_016_intg_error_fatal_alert, te | TL-T3.1.3.2.3-01, GP-10-32, GP-10-27, GP-4.1-01, TL-T2.2-03 |  |
| M12 | prim_mubi_pkg.sv:72 | ne_to_eq | survived |  | GP-3-01, GP-4.1-03, GP-10-19 | formal CEX: outputs differ at step 4 after reset: o_d_data (original 11111111111111111111111111111111, mutant 00000000000000000000000000000000), o_d_error (original 1, muta |
| M13 | prim_alert_sender.sv:206 | or_to_and | killed | test_chk_014_alert_test_pulse, test_chk_015_alert_regwen_lock, test_chk_016_intg_error_fatal_alert, test_regression_rand | GP-5-01, GP-T5.5.1-02, GP-4.2-02, GP-3-04, GP-10-15 |  |
| M14 | prim_subreg_arb.sv:34 | one_to_zero | killed | test_chk_017_input_filter, test_chk_022_edge_interrupts, test_chk_023_level_interrupts, test_chk_024_intr_test_and_enabl | GP-9-01, GP-10-39, GP-T3.2.1-01, GP-T2.2-01, GP-9-02 |  |
| M15 | tlul_adapter_reg.sv:219 | zero_to_one | survived |  | GP-4.1-01 | formal CEX: outputs differ at step 0 after reset: o_d_error (original 0, mutant 1) |
| M16 | prim_subreg.sv:59 | negate_if | killed | test_chk_015_alert_regwen_lock, test_chk_017_input_filter, test_chk_021_data_in_follows_input, test_chk_022_edge_interru | GP-9-01, GP-2-06, GP-10-03, GP-10-31, GP-T5.1-01 |  |
| M17 | tlul_err.sv:79 | one_to_zero | killed | test_chk_014_alert_test_pulse, test_chk_015_alert_regwen_lock, test_chk_016_intg_error_fatal_alert, test_chk_017_input_f | GP-10-24, GP-1-01, GP-T2.2-01 |  |
| M18 | gpio_reg_top.sv:80 | or_to_and | survived |  |  | formal PROVEN (claimed: err_q only latches the integrity error. intg_err_o is still the combinational OR of intg_err and reg_we_err, and intg_err is gated by a_valid. The fatal prim_al) |
| M19 | prim_secded_inv_64_57_dec.sv:39 | eq_to_ne | survived |  |  | formal PROVEN (claimed: data_o of the 64_57 decoder is left unconnected in tlul_cmd_intg_chk and tlul_rsp_intg_chk. Only err_o is used, and it depends on the syndrome, not on data_o.) |
| M20 | prim_filter_ctr.sv:74 | eq_to_ne | killed | test_chk_017_input_filter | GP-T3.2.3-03, GP-T5.17-01, GP-10-07, GP-10-08, GP-10-09 |  |
| M21 | prim_alert_receiver.sv:190 | one_to_zero | survived |  | GP-5-05, AH-T1.3.2-01, AH-T1.3.2-03, GP-5-02 | formal CEX: outputs differ at step 30 after reset: o_alert (original 0, mutant 1) |
| M22 | gpio_reg_top.sv:6116 | eq_to_ne | killed | test_chk_014_alert_test_pulse, test_chk_015_alert_regwen_lock, test_chk_016_intg_error_fatal_alert, test_chk_017_input_f | GP-T5.21-01, GP-T5.21-02, GP-9-07, GP-T3.2.2-01, GP-10-20 |  |
| M23 | prim_secded_inv_39_32_dec.sv:51 | eq_to_ne | survived |  |  | formal PROVEN (claimed: data_o of the 39_32 decoder is left unconnected in tlul_data_integ_dec. Only err_o is used, and it does not depend on data_o.) |
| M24 | tlul_adapter_reg.sv:155 | eq_to_ne | killed | CHK-007, CHK-004, test_chk_014_alert_test_pulse, test_chk_015_alert_regwen_lock, test_chk_016_intg_error_fatal_alert, te | GP-9-01, GP-T5.1-01, GP-9-02, GP-T4.4-03, GP-T2.2-01 |  |
| M25 | prim_flop.sv:16 | negate_if | killed | test_chk_014_alert_test_pulse, test_chk_015_alert_regwen_lock, test_chk_016_intg_error_fatal_alert, test_chk_017_input_f | GP-T3.2.3-01, GP-10-35, GP-10-43, GP-5-01, GP-T5.5.1-02 |  |
| M26 | gpio.sv:868 | negate_if | killed | CHK-004, test_chk_019_masked_out, test_chk_020_data_oe, test_chk_025_per_pin_io, test_chk_029_field_access_types, test_c | GP-T5.8-01, GP-T5.8-02, GP-T3.2.1-02, GP-T2.2-02, GP-10-02 |  |
| M27 | prim_intr_hw.sv:97 | negate_if | killed | CHK-008, test_chk_017_input_filter, test_chk_018_direct_out, test_chk_022_edge_interrupts, test_chk_023_level_interrupts | GP-7-01, GP-T5.13-01, GP-10-04, GP-T5.4.1-01, GP-10-31 |  |
| M28 | prim_alert_receiver.sv:178 | negate_if | killed | test_chk_014_alert_test_pulse, test_chk_015_alert_regwen_lock, test_chk_016_intg_error_fatal_alert, test_regression_rand | GP-5-01, GP-T5.5.1-02, GP-5-02, GP-10-15, GP-3-04 |  |
| M29 | tlul_adapter_reg.sv:220 | negate_if | killed | CHK-012, CHK-004, test_chk_014_alert_test_pulse, test_chk_015_alert_regwen_lock, test_chk_016_intg_error_fatal_alert, te | GP-9-01, GP-4.1-01, GP-10-28, GP-T5.1-01, GP-10-20 |  |
| M30 | prim_diff_decode.sv:234 | negate_if | survived |  |  | formal ERROR (claimed: This is the synchronous diff decoder, which is used because AlertAsyncOn=0 in the wrapper. The mutant holds diff_pq and level_q at 0 while rst_ni=1. diff_pq onl) |
| M31 | prim_diff_decode.sv:236 | zero_to_one | survived |  |  | formal PROVEN (claimed: level_q is read only when sigint_o=1. After reset release the pairs hold their reset values (no sigint), and the first clock edge loads level_q from level_o (0)) |
| M32 | prim_filter_ctr.sv:75 | ne_to_eq | killed | test_chk_017_input_filter, test_chk_029_field_access_types, test_chk_036_unmapped | GP-T3.2.3-03, GP-T5.17-01, GP-10-08, GP-10-09, GP-T2.2-05 |  |
| M33 | gpio_reg_top.sv:78 | negate_if | survived |  |  | formal ERROR (claimed: err_q would be held at 0 while rst_ni=1. intg_err_o is still the combinational intg_err | reg_we_err, which is nonzero only during an a_valid cycle with an erro) |
| M34 | prim_mubi_pkg.sv:44 | eq_to_ne | killed | test_chk_014_alert_test_pulse, test_chk_015_alert_regwen_lock, test_chk_016_intg_error_fatal_alert, test_chk_017_input_f | GP-3-01, GP-4.1-03, GP-10-24, GP-1-01, GP-10-19 |  |
| M35 | prim_secded_inv_39_32_enc.sv:15 | one_to_zero | killed | CHK-003, test_chk_014_alert_test_pulse, test_chk_015_alert_regwen_lock, test_chk_016_intg_error_fatal_alert, test_chk_01 | GP-4.3-01, GP-4.3-02, GP-3-03, GP-4.2-01, GP-10-33 |  |
| M36 | gpio.sv:116 | zero_to_one | survived |  |  | formal PROVEN (claimed: The line is in gen_no_strap_sample, which is elaborated only when GpioAsHwStrapsEn=0. Run base.s1 uses GpioAsHwStrapsEn=1, so the line does not exist in that co) |

## Not verified by this run

- Formal: the assertions were checked by SymbiYosys under the environment assumptions (work/formal.md); a BOUNDED result holds only up to its depth.
- Domain crossings were checked structurally (synchronizer structure, `nnc cdc`); gray coding and handshake protocols are not proven by that check.
- Sign-off STA, place and route and DFT are outside this flow (docs/SIGNOFF_SCOPE.md); `nnc rtl-check` gives a synthesis estimate of area and the longest combinational path.
- Rules marked NOT_VERIFIED_BY_SIM carry the contract's reason (static, structural, not observable...).
- Only the configurations of the run set above were simulated; code coverage is merged over its runs, mutation testing used the primary run base.s1.

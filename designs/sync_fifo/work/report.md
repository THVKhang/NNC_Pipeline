# Verification report — sync_fifo

Generated 2026-11-11T07:38:34+00:00 by NNC Pipeline.

## Summary

| Item | Result |
|---|---|
| Rules | 272 — {'NOT_VERIFIED_BY_SIM': 98, 'VERIFIED': 174} |
| Checks | 25 — {'PASS': 25} |
| Tests | {'pass': 25} |
| Integration | OK |
| Code coverage (RTL), line | 99.2 % (236/238 lines) |
| Code coverage (RTL), block | 97.3 % (72/74 statement blocks and branch arms) |
| Code coverage (RTL), expression | 92.8 % (64/69 condition terms) |
| Code coverage (RTL), toggle | 70.6 % (1620/2296 bit toggles 0->1 and 1->0) |
| Code coverage (RTL), functional | 100.0 % (40/40 cover points of the specification) |
| Mutation score | 100.0 % (36 killed / 0 survived / 0 not compiled) |
| Coverage target | not requested (`nnc cover <design> --target <n> --metric <m>`) |
| Triage | no failure to analyse |
| Agent cost | US$15.3406 in 63 calls (A1 0.9003, A12 1.3483, A2 0.6673, A3 0.4066, A4 1.8669, A5 0.4191, A6 0.243, A7 8.496, A9 0.9932) |

## Sign-off conditions

| Condition | State |
|---|---|
| Gates G1-G3 approved | met — approved on delegation by an agent: a person should confirm |
| Interface conformance of the DUT | met |
| Every selected check PASS (no FAIL, NOT_HIT, NOT_RUN) | met |
| Every planned check selected | met |
| Every rule in a check or declared not verifiable | met |
| Mutation run | met |
| Per-requirement mutation score >= 85 % | met — 60 rules with attributed mutants |

## Gates

| Gate | State | Detail |
|---|---|---|
| G1_rules | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-08T05:14:15+00:00 |
| G2_contract | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-08T10:37:14+00:00 |
| G3_verif_sources | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-08T15:30:04+00:00 |
| G4_signoff | PENDING | artifacts ready for review |

## Checks

| Check | Kind | Title | Status | Evidence |
|---|---|---|---|---|
| CHK-001 | assertion | Outputs change only at their own clock edge | **PASS** | hits 18976, fails 0 |
| CHK-002 | assertion | No unknown input when a request is sampled | **PASS** | hits 28418, fails 0 |
| CHK-003 | assertion | Reads blocked while software reset busy | **PASS** | hits 2554, fails 0 |
| CHK-004 | assertion | Read-view occupancy model for o_empty and o_empty_thr | **PASS** | hits 18787, fails 0 |
| CHK-005 | assertion | o_underflow one-cycle pulse | **PASS** | hits 5871, fails 0 |
| CHK-006 | assertion | Scoreboard: order, no loss, no duplication, show-ahead data | **PASS** | hits 11709, fails 0 |
| CHK-007 | assertion | Occupancy bounds and safe-direction flag lag | **PASS** | hits 18962, fails 0 |
| CHK-008 | assertion | o_sw_rst_busy start and idle behavior | **PASS** | hits 16887, fails 0 |
| CHK-009 | assertion | Write block term forces o_full and o_full_thr | **PASS** | hits 2333, fails 0 |
| CHK-010 | assertion | Write-view occupancy model for o_full and o_full_thr | **PASS** | hits 16629, fails 0 |
| CHK-011 | assertion | o_overflow exact one-cycle pulse | **PASS** | hits 18976, fails 0 |
| CHK-012 | test | Strictly-later edge latency of o_empty and o_full fall at 3:2 ratio | **PASS** | test_chk_012_strict_later_latency_3_2 |
| CHK-013 | test | Constrained-random scoreboard traffic over clock ratios and reset release phases | **PASS** | test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1, test_chk_013_random_ratios/ratio=2, test_chk_013_random_ratios/ratio=3, test_chk_013_random_ratios/ratio=4, test_chk_013_random_ratios/ratio=5, test_chk_013_random_ratios/ratio=6, test_chk_013_random_ratios/ratio=7 |
| CHK-014 | test | First word latency, show-ahead and back-to-back reads with equal clocks | **PASS** | test_chk_014_first_word_show_ahead |
| CHK-015 | test | Fill to full, overflow pulses, drain to empty, underflow pulses | **PASS** | test_chk_015_full_empty_overflow_underflow |
| CHK-016 | test | No full-FIFO bypass; simultaneous accepted write and read | **PASS** | test_chk_016_no_bypass_simultaneous |
| CHK-017 | test | Pointer wrap: order and flags over many wraps | **PASS** | test_chk_017_pointer_wrap/ratio=0, test_chk_017_pointer_wrap/ratio=1 |
| CHK-018 | test | Gap-free streaming with equal clocks | **PASS** | test_chk_018_gap_free_equal |
| CHK-019 | test | Continuous traffic, write clock faster (WF-010) | **PASS** | test_chk_019_write_faster |
| CHK-020 | test | Continuous traffic, read clock faster (WF-011) | **PASS** | test_chk_020_read_faster |
| CHK-021 | test | Hardware reset values, asynchronous assertion, release and clearing of pulses | **PASS** | test_chk_021_hw_reset |
| CHK-022 | test | Software reset sequence with low levels of 1, 3 and 10 cycles and traffic | **PASS** | test_chk_022_sw_reset_sequence/ratio=0, test_chk_022_sw_reset_sequence/ratio=1, test_chk_022_sw_reset_sequence/ratio=2 |
| CHK-023 | test | Hardware reset has priority at every step of the software reset sequence | **PASS** | test_chk_023_hw_reset_priority |
| CHK-024 | test | Software reset while full, and a new request during the sequence | **PASS** | test_chk_024_sw_reset_full_and_rerequest |
| CHK-025 | test | Threshold flags (WF-005) and threshold sweep including values above DEPTH | **PASS** | test_chk_025_thresholds |

## Requirement traceability (RTM)

| Rule | Spec ref | Statement | Checks | Mutation | Status |
|---|---|---|---|---|---|
| SF-1.1-01 |  | The FIFO must transfer a stream of data words from the write clock domain to the read clock domain. | CHK-006:PASS, CHK-013:PASS, CHK-014:PASS | — | **VERIFIED** |
| SF-1.1-02 |  | Words must be read in the same order in which they were written (first-in first-out). | CHK-006:PASS, CHK-013:PASS | — | **VERIFIED** |
| SF-1.1-03 |  | The write and read clocks may have different frequencies, provided they are synchronous with a fixed phase relationship from one source. | CHK-012:PASS, CHK-013:PASS, CHK-019:PASS, CHK-020:PASS | — | **VERIFIED** |
| SF-1.1-04 |  | Pointers must cross between clock domains without synchronizers, as ordinary timed paths closed by STA. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-1.1-05 |  | The write and read clocks may be equal (single clock) as a normal use case. | CHK-013:PASS, CHK-014:PASS | — | **VERIFIED** |
| SF-1.1-06 |  | The FIFO must provide write and read requests, full and empty flags, threshold flags, overflow and underflow pulses, show-ahead read, a hardware reset per domain and a software reset with handshake. | not verified: covered_by_other_check | — | **NOT_VERIFIED_BY_SIM** |
| SF-1.1-11 | REQ-FUNC-001, REQ-FUNC-002, REQ-FUNC-003, REQ-FUNC-006 | The FIFO must support any depth of 2 or more, not only powers of two, and any data width of 1 bit or more. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-1.1-12 | REQ-CLK-003, REQ-PERF-003, REQ-PERF-004 | PARA_SFIFO_PTR_RETIME must select either a direct pointer path or one retiming flop in the destination domain. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-1.1-13 | REQ-PERF-001, REQ-PERF-002 | Streaming must be gap-free, with only the initial latency and no gap. | CHK-018:PASS | — | **VERIFIED** |
| SF-1.1-14 | REQ-SRST-001, REQ-SRST-008 | Software reset must use a four-phase handshake between the two domains. | CHK-022:PASS | — | **VERIFIED** |
| SF-1.2-01 | REQ-RTL-002 | The array may be replaced by an SRAM macro with one write port and one read port behind a wrapper. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-1.3-01 | REQ-CLK-001, REQ-CLK-002 | The FIFO must support two synchronous clocks of different frequencies without a synchronizer. | CHK-012:PASS, CHK-013:PASS | — | **VERIFIED** |
| SF-1.3-02 | REQ-FUNC-004, REQ-FUNC-005, REQ-PERF-005 | Full and empty flags must have exact boundaries. | CHK-004:PASS, CHK-010:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-1.3-03 | REQ-FUNC-007 | Full and empty threshold flags must use static thresholds. | CHK-004:PASS, CHK-010:PASS, CHK-025:PASS | — | **VERIFIED** |
| SF-1.3-04 | REQ-FUNC-008, REQ-FUNC-009 | The FIFO must provide overflow and underflow pulses. | CHK-005:PASS, CHK-011:PASS | — | **VERIFIED** |
| SF-1.3-05 | REQ-FUNC-002, REQ-IF-003 | The FIFO must provide show-ahead read. | CHK-006:PASS | — | **VERIFIED** |
| SF-2.1-01 |  | The RTL must follow VLSIT RTL Design Rules v2 (REF-003) as the mandatory coding, hierarchy, reset, CDC and naming baseline. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-2.2-01 |  | REF-001 (the sibling AsyncGrayFIFO specification) must not override this specification; where they differ, this specification prevails. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| SF-2.2-02 |  | Conflicts must be resolved by revising the requirement or choosing a compliant implementation, not by a local RTL exception. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-01 | REQ-FUNC-001 | A write shall be accepted and the word on i_wr_data stored at the next free place. | CHK-006:PASS, CHK-014:PASS | 100.0 % (6/6) | **VERIFIED** |
| SF-3-02 | REQ-FUNC-002 | A read shall be accepted, and the accepted word is the word shown on o_rd_data before that edge. | CHK-006:PASS, CHK-014:PASS | 100.0 % (3/3) | **VERIFIED** |
| SF-3-03 | REQ-FUNC-002 | o_rd_data shall show the next word (show-ahead) without a bubble. | CHK-006:PASS, CHK-014:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-3-04 | REQ-FUNC-003 | Words shall be read in the order written, with no loss and no duplication. | CHK-013:PASS, CHK-017:PASS | 100.0 % (7/7) | **VERIFIED** |
| SF-3-05 | REQ-FUNC-004 | The FIFO shall store up to PARA_SFIFO_DEPTH words and o_full shall be 1 when PARA_SFIFO_DEPTH words are stored. | CHK-007:PASS, CHK-010:PASS, CHK-015:PASS | 100.0 % (2/2) | **VERIFIED** |
| SF-3-06 | REQ-FUNC-004 | o_full may be 1 while a place is free (conservative flag). | not verified: covered_by_other_check | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-07 | REQ-FUNC-004 | A write while o_full is 1 shall store nothing and leave the write pointer unchanged. | CHK-006:PASS, CHK-015:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-3-08 | REQ-FUNC-005 | o_empty shall be 1 whenever no stored word is visible to the read side. | CHK-004:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-3-09 | REQ-FUNC-005 | o_empty may be 1 while a word exists (conservative flag). | not verified: covered_by_other_check | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-10 | REQ-FUNC-005 | o_rd_data shall be valid whenever o_empty is 0; it is not meaningful while o_empty is 1. | CHK-006:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-3-11 | REQ-FUNC-005 | A read while o_empty is 1 shall leave the read pointer unchanged. | CHK-006:PASS | — | **VERIFIED** |
| SF-3-12 | REQ-FUNC-006 | The depth shall be any integer of 2 or more. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-13 | REQ-FUNC-006 | Pointers shall count modulo two times the depth, and the memory address shall be the pointer modulo the depth. | CHK-017:PASS | 100.0 % (4/4) | **VERIFIED** |
| SF-3-14 | REQ-FUNC-007 | o_full_thr shall be 1 when write-side occupancy is greater than or equal to i_full_thr. | CHK-010:PASS, CHK-025:PASS | — | **VERIFIED** |
| SF-3-15 | REQ-FUNC-007 | o_empty_thr shall be 1 when read-side occupancy is less than or equal to i_empty_thr. | CHK-004:PASS, CHK-025:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-3-16 | REQ-FUNC-007 | i_full_thr and i_empty_thr shall be static inputs. | CHK-025:PASS | — | **VERIFIED** |
| SF-3-17 | REQ-FUNC-008 | o_overflow shall pulse for one write-clock cycle in the following cycle and not be sticky. | CHK-011:PASS, CHK-015:PASS | — | **VERIFIED** |
| SF-3-18 | REQ-FUNC-009 | o_underflow shall pulse for one read-clock cycle in the following cycle and not be sticky. | CHK-005:PASS, CHK-015:PASS | — | **VERIFIED** |
| SF-3-19 | REQ-FUNC-010 | A rejected write or read shall not change any pointer, stored word, or the occupancy. | CHK-006:PASS, CHK-015:PASS | — | **VERIFIED** |
| SF-3-20 | REQ-IF-001 | The IP shall expose exactly the ports of Section 6.2, and the port list shall not depend on parameters except for widths. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-21 | REQ-IF-002 | Each listed output shall be driven by a flip-flop; the four flag outputs are combined with the software reset block term by one gate, with no other logic. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-22 | REQ-IF-003 | o_rd_data shall be the memory output register (one read-clock latency) with no logic after it and no reset. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-23 | REQ-CLK-001 | The IP shall operate correctly with two synchronous clocks of any rational frequency ratio, including coinciding edges. | CHK-012:PASS, CHK-013:PASS | — | **VERIFIED** |
| SF-3-24 | REQ-CLK-002 | The IP shall contain no synchronizer and no clock-domain-crossing cell. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-25 | REQ-CLK-002 | Every inter-domain path shall be an ordinary timed path closed by STA with no false-path or asynchronous clock-group exception. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-26 | REQ-CLK-003 | The other domain's pointer shall enter the flag logic directly. | not verified: static_or_structural | 100.0 % (2/2) | **NOT_VERIFIED_BY_SIM** |
| SF-3-27 | REQ-CLK-003 | The other domain's pointer shall first be captured by one flip-flop in the destination domain. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-28 | REQ-CLK-003 | The parameter shall change only flag latency and crossing-path timing, not function. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-29 | REQ-RESET-001 | Both resets shall be active-low with asynchronous assertion. | CHK-021:PASS | 100.0 % (6/6) | **VERIFIED** |
| SF-3-30 | REQ-RESET-001 | Every flop of the domain shall be at reset value: pointers 0, o_full 0, o_empty 1, o_overflow 0, o_underflow 0, FSMs in RUN, o_sw_rst_busy 0, handshake flops 0. | CHK-021:PASS | 100.0 % (6/6) | **VERIFIED** |
| SF-3-31 | REQ-RESET-002 | Release of each hardware reset shall be synchronous to its domain clock and provided outside the IP. | CHK-021:PASS | — | **VERIFIED** |
| SF-3-32 | REQ-RESET-002 | The two resets shall be asserted together, and no operation shall start before both are released. | CHK-013:PASS, CHK-021:PASS | — | **VERIFIED** |
| SF-3-33 | REQ-SRST-001 | i_rst_n_sw = 0 shall request a software reset; one low cycle suffices. | CHK-008:PASS, CHK-022:PASS | 100.0 % (2/2) | **VERIFIED** |
| SF-3-34 | REQ-SRST-001 | A longer low level shall be held until the sequence reaches its hold state. | CHK-022:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-3-35 | REQ-SRST-002 | Writes shall be blocked with no clock delay: o_full 1, o_full_thr showing empty-FIFO value, and no write accepted. | CHK-009:PASS, CHK-022:PASS | — | **VERIFIED** |
| SF-3-36 | REQ-SRST-002 | Writes shall remain blocked until o_sw_rst_busy is 0. | CHK-009:PASS, CHK-022:PASS | — | **VERIFIED** |
| SF-3-37 | REQ-SRST-002 | A blocked write shall not raise o_overflow. | CHK-011:PASS, CHK-022:PASS | — | **VERIFIED** |
| SF-3-38 | REQ-SRST-003 | Reads shall be blocked: o_empty 1, o_empty_thr 1, no read accepted until the read side is released. | CHK-003:PASS, CHK-022:PASS | 100.0 % (9/9) | **VERIFIED** |
| SF-3-39 | REQ-SRST-003 | A blocked read shall not raise o_underflow. | CHK-005:PASS, CHK-022:PASS | — | **VERIFIED** |
| SF-3-40 | REQ-SRST-004 | Read side shall reset its pointer first and acknowledge, then write side resets its pointer; read side is released first, write side last. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-41 | REQ-SRST-004 | The software reset handshake shall be four-phase. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-42 | REQ-SRST-005 | The FIFO shall be empty, both pointers 0, and every stored word discarded. | CHK-022:PASS | 100.0 % (3/3) | **VERIFIED** |
| SF-3-43 | REQ-SRST-005 | The memory content shall not be erased. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-44 | REQ-SRST-006 | o_sw_rst_busy shall be a flip-flop output, 1 from the cycle after the write FSM takes the request until the cycle the write FSM is back in RUN. | CHK-008:PASS, CHK-022:PASS | 100.0 % (2/2) | **VERIFIED** |
| SF-3-45 | REQ-SRST-006 | The FIFO is ready for writes when o_sw_rst_busy is 0 and i_rst_n_sw is 1. | CHK-010:PASS, CHK-022:PASS | — | **VERIFIED** |
| SF-3-46 | REQ-SRST-007 | A hardware reset shall have priority over a software reset and bring both FSMs to RUN. | CHK-023:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-3-47 | REQ-SRST-008 | The request shall be served as a new sequence when the write FSM is back in RUN. | CHK-024:PASS | — | **VERIFIED** |
| SF-3-48 | REQ-SRST-008 | The sequence shall stay in the hold state. | CHK-022:PASS, CHK-024:PASS | 100.0 % (7/7) | **VERIFIED** |
| SF-3-49 | REQ-PARAM-001 | The IP shall accept the parameter values listed in Section 8. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-50 | REQ-PERF-001 | The IP shall accept one write per write-clock cycle and one read per read-clock cycle. | CHK-018:PASS, CHK-019:PASS | — | **VERIFIED** |
| SF-3-51 | REQ-PERF-002 | There shall be only initial latency and no gap: every cycle where the other side is not limiting accepts a read or write. | CHK-018:PASS, CHK-019:PASS, CHK-020:PASS | — | **VERIFIED** |
| SF-3-52 | REQ-PERF-003 | o_empty shall fall after the first strictly later i_clk_rd rising edge (RETIME 0) or the second (RETIME 1), with o_rd_data showing the new word. | CHK-004:PASS, CHK-012:PASS, CHK-014:PASS | 100.0 % (6/6) | **VERIFIED** |
| SF-3-53 | REQ-PERF-004 | o_full shall fall after the first strictly later i_clk_wr rising edge (RETIME 0) or the second (RETIME 1). | CHK-010:PASS, CHK-012:PASS, CHK-015:PASS | 100.0 % (2/2) | **VERIFIED** |
| SF-3-54 | REQ-PERF-005 | o_full shall be 1 the cycle after the write storing the last free place; o_empty shall be 1 the cycle after the read taking the last word. | CHK-004:PASS, CHK-010:PASS, CHK-014:PASS, CHK-015:PASS | — | **VERIFIED** |
| SF-3-55 | REQ-RTL-001 | The RTL shall comply with REF-003 and use the hierarchy of Section 14.2. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-56 | REQ-RTL-002 | The library SRAM shall be instantiated only inside the VLSIT_CELL_SRAM_1W1R wrapper in 000_Common, with instance name u_dont_touch_ plus function name, behaving like the array branch. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-57 | REQ-RTL-003 | The IP shall contain no synchronizer module and no cell wrapper other than the SRAM wrapper; the retiming flop shall be a plain RTL flip-flop. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-58 | REQ-VER-001 | Every waveform of the plan shall exist as an image with WaveJSON source, reproducible by prototype scripts. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-3-59 | REQ-VER-002 | Scoreboard regression shall cover depths 2, 3, 5, 8, 12, both PARA_SFIFO_PTR_RETIME values and several clock ratios including equal, with no error. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-4-01 |  | CFG-BASE must have PARA_SFIFO_PTR_RETIME = 0, PARA_SFIFO_MEM_USE_MACRO = 0, DATA_W 32, DEPTH 8, and be verified by all tests. | not verified: covered_by_other_check | — | **NOT_VERIFIED_BY_SIM** |
| SF-4-02 |  | CFG-RETIME must enable CFG-BASE plus FEAT-007 with PARA_SFIFO_PTR_RETIME = 1 and be verified by TEST-002, 006, 007, 009, 011, 015, 017. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-4-03 |  | CFG-MACRO must enable CFG-BASE plus FEAT-010 with PARA_SFIFO_MEM_USE_MACRO = 1 and be verified by TEST-002 and TEST-012. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-4-04 |  | CFG-ODD must support a DEPTH that is not a power of two, such as 5 or 12, verified by TEST-008. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-4-05 |  | CFG-MIN (DEPTH 2, DATA_W 1, CFG-BASE features, FEAT-007 and FEAT-010 disabled) must be a legal instance and be verified by TEST-013. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-4-06 |  | FEAT-007 and FEAT-010 must be selected by a parameter at elaboration and be present or absent, not run-time disabled. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-4-07 |  | The port list must be identical in every configuration except for port widths. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-5.1-01 |  | Flags are flip-flops computed from the next pointer values (look-ahead), so each flag is exact at its own domain's clock edge and conservative only by the other side's pointer visibility. | CHK-004:PASS, CHK-010:PASS | — | **VERIFIED** |
| SF-5.3-01 |  | The word on i_wr_data is stored at the write pointer address, the write pointer increments, and flags are recomputed for the next cycle. | CHK-006:PASS, CHK-014:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-5.3-02 |  | The read side uses the new write pointer at its next strictly later rising edge, directly or one edge later through the retiming flop. | CHK-004:PASS, CHK-012:PASS, CHK-014:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-5.3-03 |  | The read flag register and memory output register load at the same edge, so o_empty and the read data change together. | CHK-006:PASS, CHK-014:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-5.3-04 |  | The word on o_rd_data is taken, the read pointer increments, and the output register loads the following word; the memory read address is the next read pointer's address. | CHK-006:PASS, CHK-014:PASS | — | **VERIFIED** |
| SF-5.3-05 |  | The read pointer becomes visible to the write side at its next strictly later rising edge, directly or one edge later, where o_full may fall. | CHK-010:PASS, CHK-012:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-5.4-01 |  | Occupancy (write pointer minus read pointer modulo twice the depth) stays between 0 and PARA_SFIFO_DEPTH. | CHK-007:PASS | — | **VERIFIED** |
| SF-5.4-02 |  | No write is accepted while o_full is 1, and no read is accepted while o_empty is 1. | CHK-006:PASS, CHK-016:PASS | — | **VERIFIED** |
| SF-5.4-03 |  | o_full is 1 whenever occupancy is PARA_SFIFO_DEPTH, and o_empty is 1 whenever occupancy is 0. | CHK-004:PASS, CHK-010:PASS | — | **VERIFIED** |
| SF-5.4-04 |  | The write side never sees a read pointer ahead of the real one, and the read side never sees a write pointer ahead of the real one; views only lag. | CHK-007:PASS | — | **VERIFIED** |
| SF-5.4-05 |  | Pointers and flags change only at a rising edge of the clock of their own domain. | CHK-001:PASS | — | **VERIFIED** |
| SF-6.1-01 |  | IF-001 custom FIFO write interface is required in all configurations, acts as slave of the writer in CLK-WR with requests in and status out. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-6.1-02 |  | IF-002 custom FIFO read interface is required in all configurations, acts as slave of the reader in CLK-RD with requests in and data and status out. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-6.1-03 |  | IF-003 software reset interface is required in all configurations, slave of the controller in CLK-WR, with request input and busy output. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-6.1-04 |  | IF-004 clocks and hardware resets are required inputs in all configurations, in domains CLK-WR and CLK-RD. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-6.2-01 |  | The top-level port list must not depend on any parameter value except for port widths. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-6.2-02 |  | o_sw_rst_busy is a flop output that changes only at a rising edge of i_clk_wr and is 0 when writes are possible again. | CHK-001:PASS, CHK-008:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-6.2-04 |  | A reset is a level that stays low for at least one edge of its clock and is released synchronously to that clock outside the IP. | CHK-021:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-6.2-06 |  | A Pulse output is a flop output that is 1 for exactly one clock period after the event edge, returns to 0 by itself and is not sticky. | CHK-005:PASS, CHK-011:PASS | — | **VERIFIED** |
| SF-6.2-08 |  | Static configuration values such as i_full_thr and i_empty_thr must not be changed while the FIFO is in use; they have no clock domain. | CHK-025:PASS | — | **VERIFIED** |
| SF-6.3-01 |  | The write is accepted when i_wr_en = 1, o_full = 0 and writes are not blocked by the software reset. | CHK-006:PASS | — | **VERIFIED** |
| SF-6.3-03 |  | The read is accepted when i_rd_en = 1, o_empty = 0 and reads are not blocked; o_rd_data is valid for the whole cycle before the accepting edge. | CHK-006:PASS | — | **VERIFIED** |
| SF-6.3-04 |  | o_rd_data shows the next word in the next cycle with no bubble. | CHK-006:PASS, CHK-014:PASS | — | **VERIFIED** |
| SF-6.3-05 |  | A flag view may lag real occupancy only in the safe direction (full late to fall, empty late to fall), never in the unsafe direction. | CHK-007:PASS | — | **VERIFIED** |
| SF-6.3-06 |  | A rejected write or read changes no state but raises the one-cycle overflow or underflow pulse. | CHK-005:PASS, CHK-011:PASS, CHK-015:PASS | — | **VERIFIED** |
| SF-6.3-07 | REQ-FUNC-001 | A write into a FIFO that is not full is accepted at the edge, the word is stored and the write pointer increments. | CHK-006:PASS, CHK-014:PASS | — | **VERIFIED** |
| SF-6.3-08 | REQ-FUNC-004, REQ-FUNC-008 | A write while o_full = 1 is dropped and an o_overflow pulse occurs in the next cycle. | CHK-011:PASS, CHK-015:PASS | — | **VERIFIED** |
| SF-6.3-09 | REQ-FUNC-002 | A read from a non-empty FIFO is accepted at the edge, the word is taken and the next word is shown. | CHK-006:PASS, CHK-014:PASS | — | **VERIFIED** |
| SF-6.3-10 | REQ-FUNC-005, REQ-FUNC-009 | A read while o_empty = 1 is dropped and an o_underflow pulse occurs in the next cycle. | CHK-005:PASS, CHK-015:PASS | — | **VERIFIED** |
| SF-6.3-11 | REQ-SRST-002, REQ-SRST-003 | A request during software-reset blocking is dropped, with no o_overflow or o_underflow pulse. | CHK-011:PASS, CHK-022:PASS | — | **VERIFIED** |
| SF-7.2-01 | REQ-CLK-002 | The two clocks i_clk_wr and i_clk_rd shall be declared as related clocks of one source. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-7.3-01 |  | On i_rst_n_wr, write pointer shall be 0, o_full 0, o_full_thr 0, o_overflow 0, write FSM RUN, request 0, busy 0. | CHK-021:PASS | 100.0 % (8/8) | **VERIFIED** |
| SF-7.3-02 |  | On i_rst_n_rd, read pointer shall be 0, o_empty 1, o_empty_thr 1, o_underflow 0, read FSM RUN, acknowledge 0. | CHK-021:PASS | 100.0 % (6/6) | **VERIFIED** |
| SF-7.3-03 |  | The FIFO shall be empty at the end of the software reset sequence. | CHK-022:PASS | — | **VERIFIED** |
| SF-7.3-04 | REQ-RESET-002 | The two hardware resets are asserted together and released synchronously to their own clocks; no operation starts before both are released. | CHK-013:PASS, CHK-021:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-7.3-05 |  | All flip-flops shall reset asynchronously to 0, except flag registers o_empty and o_empty_thr which reset to 1. | CHK-021:PASS | — | **VERIFIED** |
| SF-7.3-07 |  | o_empty shall become 0 only after the corresponding word has been written to memory. | CHK-006:PASS | — | **VERIFIED** |
| SF-7.3-08 | REQ-SRST-007 | A hardware reset shall have priority over a software reset. | CHK-023:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-8-03 |  | PARA_SFIFO_DEPTH (default 8) must be an integer of 2 or more with no upper limit; it sets the number of entries, storage size and pointer width. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-8-04 |  | PARA_SFIFO_DATA_W (default 32) must be 1 or more with no upper limit and sets the width of i_wr_data, o_rd_data and the storage. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-8-05 |  | PARA_SFIFO_PTR_RETIME (default 0) must be 0 or 1: 0 = direct pointer path, 1 = one retiming flop in the destination domain. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-8-07 |  | PARA_SFIFO_MEM_USE_MACRO (default 0) must be 0 or 1: 0 = RTL array storage, 1 = library SRAM wrapper storage. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-8-08 |  | The SRAM wrapper must use the macro model VLSIT_CELL_SRAM_1W1R of 000_Common. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-8-09 |  | LPARA_ADDR_W must be derived as clog2(PARA_SFIFO_DEPTH), at least 1, and sets the memory address width. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-8-10 |  | LPARA_PTR_W must be derived as clog2(2 x PARA_SFIFO_DEPTH), at least 2; the pointer counts 0 to 2 x DEPTH - 1. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-8-11 |  | LPARA_OCC_W must be derived as clog2(PARA_SFIFO_DEPTH + 1), at least 2, and sets the width of i_full_thr and i_empty_thr; occupancy is 0 to DEPTH. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-8-12 |  | The smallest legal instance must elaborate and lint with the same hierarchy. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-8-13 |  | These illegal configurations must not be used; the IP does not check them and its behavior with them is not specified. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-8-14 |  | The depth is legal but gap-free streaming is not guaranteed. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-9-01 |  | The pointer, of width LPARA_PTR_W, must be an unsigned value in the range 0 to 2 x DEPTH - 1 and must return to 0 after 2 x DEPTH - 1. | CHK-017:PASS | 100.0 % (6/6) | **VERIFIED** |
| SF-9-03 |  | Occupancy must equal write pointer minus read pointer if the write pointer is not below the read pointer, otherwise that difference plus 2 x DEPTH, giving a result of 0 to DEPTH. | CHK-004:PASS, CHK-010:PASS | 100.0 % (3/3) | **VERIFIED** |
| SF-9-05 |  | A threshold value above DEPTH must make o_full_thr never 1 and o_empty_thr always 1. | CHK-004:PASS, CHK-010:PASS, CHK-025:PASS | 100.0 % (2/2) | **VERIFIED** |
| SF-9-06 |  | The threshold, of width LPARA_OCC_W, is an unsigned occupancy value from 0 to DEPTH and is zero-extended for the comparison. | CHK-004:PASS, CHK-010:PASS, CHK-025:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-10.1-01 |  | The data path has no mode; acceptance of writes and reads is decided only by the flags. | CHK-006:PASS | — | **VERIFIED** |
| SF-10.1-02 |  | Write reset FSM leaves RUN to REQ when i_rst_n_sw = 0, blocks writes, raises request and drives o_sw_rst_busy 1 until acknowledge is seen. | CHK-008:PASS, CHK-009:PASS, CHK-022:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-10.1-03 |  | Write reset FSM state encodings 5 to 7 recover to RUN. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-10.1-04 |  | In ENUM_ST_PTR the write pointer is reset to 0 for one cycle, request stays 1, and the FSM always moves to HOLD. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-10.1-05 |  | HOLD waits with request 1 until i_rst_n_sw = 1, then REL drops request, keeps o_sw_rst_busy 1 and returns to RUN when acknowledge is 0 and read pointer is 0. | CHK-022:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-10.1-06 |  | Read reset FSM encoding 3 recovers to RUN; in RUN acknowledge is 0 and request seen moves it to RST. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-10.1-07 |  | In ENUM_ST_RST reads are blocked, the read pointer is reset to 0 for one cycle, the FSM goes to ACK and acknowledge rises at the exit edge. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-10.1-08 |  | In ENUM_ST_ACK reads are blocked and acknowledge held at 1 until request is 0 and write pointer is seen as 0, then FSM returns to RUN. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-10.2-01 |  | The write stores i_wr_data at the write address and increments the write pointer; o_empty falls in the read domain and o_full rises at once if it was the last free place. | CHK-010:PASS, CHK-014:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-10.2-02 |  | The read side sees the written word after the first (PTR_RETIME 0) or second (PTR_RETIME 1) read edge strictly after the write edge. | CHK-004:PASS, CHK-012:PASS, CHK-014:PASS | 100.0 % (3/3) | **VERIFIED** |
| SF-10.2-03 |  | The read takes the word of o_rd_data, increments the read pointer and loads the next word into the output register; o_empty rises at once if it was the last word. | CHK-004:PASS, CHK-014:PASS | — | **VERIFIED** |
| SF-10.2-04 |  | o_full falls in the write domain after the first (PTR_RETIME 0) or second (PTR_RETIME 1) write edge strictly after the read edge. | CHK-010:PASS, CHK-012:PASS | 100.0 % (2/2) | **VERIFIED** |
| SF-10.2-05 |  | The write is rejected with no state change and o_overflow pulses in the next cycle. | CHK-011:PASS, CHK-015:PASS | — | **VERIFIED** |
| SF-10.2-06 |  | The read is rejected with no state change and o_underflow pulses in the next cycle. | CHK-005:PASS, CHK-015:PASS | — | **VERIFIED** |
| SF-10.2-07 |  | o_full_thr and o_empty_thr compare the occupancy of the own domain view with the thresholds and update at every edge of the own clock. | CHK-004:PASS, CHK-010:PASS, CHK-025:PASS | — | **VERIFIED** |
| SF-10.2-08 |  | Software reset runs the sequence block, reset read pointer, reset write pointer, release, ending with FIFO empty, pointers 0 and o_sw_rst_busy 0. | CHK-022:PASS | — | **VERIFIED** |
| SF-10.2-09 |  | The state of the domain is cleared asynchronously and immediately, leaving the FIFO empty with reset values. | CHK-021:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-10.3-01 |  | After the initial latency a word is read every cycle with no gap; the latency is one cycle longer with PARA_SFIFO_PTR_RETIME = 1. | CHK-018:PASS | — | **VERIFIED** |
| SF-10.3-02 |  | The reader never stalls; the faster writer is held back by o_full only because the reader is slower. | CHK-019:PASS | — | **VERIFIED** |
| SF-10.3-03 |  | The writer never stalls; the faster reader waits through o_empty and o_underflow only because the writer is slower. | CHK-020:PASS | — | **VERIFIED** |
| SF-10.3-04 |  | Pointer wraps over 0 to 9 and address over 0 to 4. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-10.3-05 |  | The active edge is the rising edge of the signal's own domain clock; inputs are sampled at the edge ending a cycle and flop outputs change after the edge starting it. | CHK-001:PASS | — | **VERIFIED** |
| SF-10.3-06 |  | o_rd_data is meaningful only while o_empty is 0. | CHK-006:PASS | — | **VERIFIED** |
| SF-10.3-07 |  | o_full_thr rises at occupancy 6 and o_empty_thr falls at occupancy 3. | CHK-025:PASS | — | **VERIFIED** |
| SF-10.3-08 |  | Each read request on an empty FIFO gives one o_underflow pulse. | CHK-005:PASS, CHK-015:PASS | — | **VERIFIED** |
| SF-10.3-13 |  | A coinciding edge does not count as strictly later; the pointer written at that edge is seen at the next edge. | CHK-004:PASS, CHK-012:PASS, CHK-014:PASS | 100.0 % (2/2) | **VERIFIED** |
| SF-10.4-01 |  | Simultaneous write and read are independent and both are accepted at the same clock edge when o_full and o_empty allow. | CHK-006:PASS, CHK-016:PASS | — | **VERIFIED** |
| SF-10.4-02 | REQ-PERF-001 | The FIFO accepts one word per write-clock cycle and delivers one word per read-clock cycle (REQ-PERF-001). | CHK-018:PASS | — | **VERIFIED** |
| SF-10.4-04 |  | The first read accepted after the write edge occurs after 2 cycles with PARA_SFIFO_PTR_RETIME = 0 and after 3 cycles with PARA_SFIFO_PTR_RETIME = 1. | CHK-014:PASS, CHK-018:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-10.4-06 |  | o_empty = 1 in the next cycle after the last word is read, for both PARA_SFIFO_PTR_RETIME values. | CHK-004:PASS, CHK-014:PASS | — | **VERIFIED** |
| SF-10.4-07 |  | o_full = 1 in the next cycle after the last free place is written, for both PARA_SFIFO_PTR_RETIME values. | CHK-010:PASS, CHK-015:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-10.4-08 |  | Streaming has no gaps beyond the initial latency. | CHK-018:PASS | — | **VERIFIED** |
| SF-10.4-09 | REQ-PERF-002 | The side that is not rate-limited never stalls (REQ-PERF-002). | CHK-018:PASS, CHK-019:PASS, CHK-020:PASS | — | **VERIFIED** |
| SF-10.4-10 |  | The FIFO remains functionally correct, although a gap may appear. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-10.5-01 |  | The memory is read at the address of the next read pointer. | CHK-006:PASS | — | **VERIFIED** |
| SF-10.5-02 |  | A read of the address written at the same edge returns the old word, and the read side takes a word only after the flag fell. | CHK-006:PASS | — | **VERIFIED** |
| SF-10.5-03 |  | The memory must not be invalid at an address that is read. | CHK-006:PASS | — | **VERIFIED** |
| SF-10.6-02 |  | Write-domain flops load at the edge from next values: a write is accepted when i_wr_en, not block and not full flop; the full flop is set when next occupancy equals DEPTH; the full-threshold flop when it reaches i_full_thr. | CHK-010:PASS | — | **VERIFIED** |
| SF-10.6-03 |  | o_full = block OR full flop; o_full_thr = (i_full_thr equals 0) when block, otherwise the full-threshold flop. | CHK-009:PASS, CHK-010:PASS | — | **VERIFIED** |
| SF-10.6-04 |  | o_overflow is a flop set one cycle after i_wr_en with not block and full flop. | CHK-011:PASS | — | **VERIFIED** |
| SF-10.6-05 |  | Read-domain flops load at the edge from next values: a read is accepted when i_rd_en, not block and not empty flop; the empty flop is set when next occupancy equals 0; the threshold flop when at or below i_empty_thr. | CHK-004:PASS | — | **VERIFIED** |
| SF-10.6-06 |  | o_empty = block OR empty flop; o_empty_thr = 1 when block, otherwise the empty-threshold flop. | CHK-003:PASS, CHK-004:PASS | 100.0 % (7/7) | **VERIFIED** |
| SF-10.6-07 |  | o_underflow is a flop set one cycle after i_rd_en with not block and empty flop. | CHK-005:PASS | — | **VERIFIED** |
| SF-10.6-10 |  | o_full_thr is 0 until the first clock edge after release, then follows the formula even if i_full_thr is 0. | CHK-021:PASS, CHK-025:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-10.7-01 |  | From that cycle writes are blocked and o_full is 1. | CHK-009:PASS, CHK-022:PASS | — | **VERIFIED** |
| SF-10.7-02 |  | The write FSM leaves RUN, o_sw_rst_busy rises in the next cycle, and the request flop is raised. | CHK-008:PASS, CHK-022:PASS | 100.0 % (2/2) | **VERIFIED** |
| SF-10.7-03 |  | The read FSM blocks reads (o_empty = 1), resets the read pointer in state RST for one cycle and raises the acknowledge. | CHK-003:PASS, CHK-022:PASS | 100.0 % (8/8) | **VERIFIED** |
| SF-10.7-04 |  | The write FSM resets the write pointer in state PTR for one cycle and waits in HOLD until i_rst_n_sw is 1. | CHK-022:PASS | 100.0 % (7/7) | **VERIFIED** |
| SF-10.7-05 |  | In REL the request is dropped; the read side leaves ACK when it sees the request at 0 and the write pointer at 0. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-10.7-06 |  | The write side leaves REL when it sees the acknowledge at 0 and the read pointer at 0, returns to RUN, and o_sw_rst_busy falls. | CHK-022:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-10.7-07 |  | The FIFO is ready for writes when o_sw_rst_busy is 0 and i_rst_n_sw is 1. | CHK-010:PASS, CHK-022:PASS | — | **VERIFIED** |
| SF-10.7-08 |  | A one-cycle low pulse on i_rst_n_sw starts the complete software reset sequence. | CHK-022:PASS | 100.0 % (5/5) | **VERIFIED** |
| SF-10.7-09 |  | A hardware reset clears all FSMs. | CHK-023:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-10.7-10 |  | The new low level is served after the write FSM is back in RUN. | CHK-024:PASS | — | **VERIFIED** |
| SF-12-01 |  | The write must be dropped and o_overflow must pulse for one cycle. | CHK-011:PASS, CHK-015:PASS | — | **VERIFIED** |
| SF-12-02 |  | The next request must be handled independently of the rejected write, with no recovery action required. | CHK-013:PASS, CHK-015:PASS | — | **VERIFIED** |
| SF-12-03 |  | The ERR-001 overflow status must be cleared by reset. | CHK-021:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-12-04 |  | The read must be dropped and o_underflow must pulse for one cycle. | CHK-005:PASS, CHK-015:PASS | — | **VERIFIED** |
| SF-12-05 |  | The next request must be handled independently of the rejected read, with no recovery action required. | CHK-013:PASS, CHK-015:PASS | — | **VERIFIED** |
| SF-12-06 |  | The ERR-002 underflow status must be cleared by reset. | CHK-021:PASS | 100.0 % (2/2) | **VERIFIED** |
| SF-12-07 |  | The request must be dropped and no overflow or underflow pulse must be generated. | CHK-005:PASS, CHK-011:PASS, CHK-022:PASS | — | **VERIFIED** |
| SF-12-08 |  | The request may be retried after o_sw_rst_busy = 0. | CHK-022:PASS | — | **VERIFIED** |
| SF-12-10 |  | There must be no sticky error and no error interrupt; the overflow and underflow pulses are the only error status. | CHK-005:PASS, CHK-011:PASS, CHK-015:PASS | — | **VERIFIED** |
| SF-12-11 |  | The pulses for consecutive rejected requests must be consecutive, one per rejected request. | CHK-005:PASS, CHK-011:PASS, CHK-015:PASS | — | **VERIFIED** |
| SF-13-01 | REQ-PERF-001 | The FIFO must sustain a throughput of one word per write cycle and one word per read cycle. | CHK-018:PASS | — | **VERIFIED** |
| SF-13-02 | REQ-PERF-002 | The FIFO must stream without any gap after the initial latency. | CHK-018:PASS, CHK-019:PASS, CHK-020:PASS | — | **VERIFIED** |
| SF-13-03 | REQ-PERF-003 | Empty must fall on the first read edge (PTR_RETIME 0) or second read edge (PTR_RETIME 1) strictly after the write edge. | CHK-004:PASS, CHK-012:PASS | — | **VERIFIED** |
| SF-13-04 | REQ-PERF-004 | Full must fall on the first or second write edge strictly after the read edge, depending on PARA_SFIFO_PTR_RETIME. | CHK-010:PASS, CHK-012:PASS | — | **VERIFIED** |
| SF-14.1-01 |  | The RTL must comply with VLSIT RTL Design Rules v2 (REF-003) without local exceptions. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.1-02 |  | The RTL must follow the REF-003 items listed: one module per file, structural top, ANSI ports, naming prefixes, FSM names and ENUM_ST_* states, PARA_SFIFO_* parameters, name and comment length limits, u_dont_touch_ instance names. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.1-03 |  | Every flop of the control state must have an asynchronous reset; the memory is the only resetless storage. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.1-04 |  | SVA, testbench or prototype code must not be in the synthesis file list. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.1-05 | REQ-RTL-002 | The library SRAM and its macro model must be located in 000_Common, not in the folder of this IP. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2-01 |  | The hierarchy must have top m_vlsit_sfifo_top with instances u_wr, u_rd and u_mem of modules wr, rd and mem. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2-02 |  | m_vlsit_sfifo_ram_macro is instantiated as u_ram_macro in m_vlsit_sfifo_mem only when PARA_SFIFO_MEM_USE_MACRO = 1. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2-03 |  | State ownership: wr owns write pointer, flags, FSM and read-pointer/ack retiming flops; rd owns read-side equivalents; mem owns storage. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2.1-01 |  | Cross-domain inputs i_rd_ptr, i_wr_ptr, i_ack_rd and i_req_wr are captured by one retiming flop when PARA_SFIFO_PTR_RETIME = 1, otherwise used directly. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2.1-02 |  | o_wr_ptr is a flop output that changes only at the write-clock edge that accepts a write, and resets to 0. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2.1-03 |  | o_mem_wr_en is 1 combinationally when a write is accepted, and the memory stores at the same edge as the pointer increments. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2.1-04 |  | o_mem_wr_addr equals the write pointer modulo the depth. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2.1-05 |  | o_mem_wr_data is a copy of i_wr_data in the same cycle. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2.1-06 |  | o_req_wr is a flop output, reset to 0, set with the busy flop and cleared when REL starts. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2.1-07 |  | o_rd_ptr is a flop output that changes only at the read-clock edge that accepts a read, and resets to 0. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2.1-08 |  | o_mem_rd_addr is combinationally the next read pointer modulo the depth (show-ahead), based on the pointer and i_rd_en, valid every cycle. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2.1-09 |  | i_mem_rd_data is the registered memory output, valid one cycle after the address. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2.1-10 |  | o_ack_rd is a flop output reset to 0, and is 1 from the edge that leaves RST until the edge that leaves ACK. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2.1-11 |  | The memory samples i_wr_en, i_wr_addr and i_wr_data at the write-port clock; i_wr_en qualifies address and data. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2.1-12 |  | The memory samples i_rd_addr in every read-clock cycle. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2.1-13 |  | Memory o_rd_data is registered and returns the word at the read address one read-clock cycle later; a word written at the same edge is not seen. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2.1-15 |  | The macro samples write address and data at the write clock when active-low i_wr_en_n is 0. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2.1-16 |  | The memory module ties macro i_rd_en_n to 0. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-14.2.1-17 |  | The macro samples i_rd_addr every cycle and registers o_rd_data one read-clock cycle after the address. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-15.1-01 |  | Each simulation records its seed. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-15.1-02 |  | The environment drives both clocks from one generator with related edges, including coincident edges, and varies the ratio (equal, 3:2, 2:3, 1:2, 2:1, 3:7, 7:3). | CHK-013:PASS | — | **VERIFIED** |
| SF-15.1-03 | REQ-SRST-001, REQ-SRST-006, REQ-SRST-007, REQ-SRST-008 | The software reset shall be verified on the RTL by TEST-009 and TEST-010, since prototype tests did not include it. | CHK-022:PASS, CHK-023:PASS, CHK-024:PASS | 100.0 % (2/2) | **VERIFIED** |
| SF-15.2-01 | REQ-RESET-001, REQ-RESET-002, REQ-SRST-007 | All reset values are correct, the FIFO is empty after release, and no operation occurs before release (TEST-001). | CHK-021:PASS | 100.0 % (8/8) | **VERIFIED** |
| SF-15.2-02 | REQ-FUNC-001, REQ-FUNC-002, REQ-FUNC-003, REQ-FUNC-010, REQ-IF-003 | Data is read in order with no loss or duplicate, and o_rd_data is valid whenever o_empty = 0 (TEST-002). | CHK-013:PASS | — | **VERIFIED** |
| SF-15.2-03 | REQ-FUNC-004, REQ-FUNC-008, REQ-FUNC-010, REQ-PERF-005 | o_full rises in the cycle after the last place is filled, rejected writes give overflow pulses, and nothing is stored (TEST-003). | CHK-015:PASS | — | **VERIFIED** |
| SF-15.2-04 | REQ-FUNC-005, REQ-FUNC-009, REQ-FUNC-010, REQ-PERF-005 | o_empty rises in the cycle after the last read, and rejected reads give underflow pulses (TEST-004). | CHK-015:PASS | — | **VERIFIED** |
| SF-15.2-05 | REQ-FUNC-007 | o_full_thr and o_empty_thr assert at the stated occupancy, and thresholds are static (TEST-005). | CHK-025:PASS | — | **VERIFIED** |
| SF-15.2-06 | REQ-CLK-003, REQ-PERF-003, REQ-PERF-004 | o_empty and o_full fall after the first or second strictly later edge (TEST-006). | CHK-012:PASS | — | **VERIFIED** |
| SF-15.2-07 | REQ-PERF-001, REQ-PERF-002, REQ-PERF-005 | The side that is not rate-limited does not stall, and the table of Section 10.4 is reproduced (TEST-007). | CHK-018:PASS | — | **VERIFIED** |
| SF-15.2-08 | REQ-FUNC-006 | Order and flags are correct at every wrap, and addresses stay within the depth (TEST-008). | CHK-017:PASS | 100.0 % (4/4) | **VERIFIED** |
| SF-15.2-09 | REQ-CLK-001, REQ-RESET-002 | Behavior is correct for every ratio and no operation is lost at coincident edges (TEST-011). | CHK-013:PASS | — | **VERIFIED** |
| SF-15.2-10 | REQ-FUNC-003, REQ-RTL-002 | Results and flag timing are identical for array and SRAM wrapper (TEST-012). | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SF-15.2-11 | REQ-PARAM-001 | Elaboration, lint and simulation pass (TEST-013). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-15.2-12 | REQ-CLK-002, REQ-IF-001, REQ-IF-002, REQ-RTL-001, REQ-RTL-003 | Lint, rule check and port-list review show no violation; every flag, pulse and busy output is a flop (plus block gate) and no synchronizer exists (TEST-014). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-15.2-13 | REQ-CLK-002, REQ-CLK-003 | All crossing paths close, with no asynchronous clock group or false path between the clocks (TEST-015). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-15.2-14 | REQ-FUNC-003, REQ-VER-002 | The scoreboard regression over depths, pointer options, ratios and seeds shows no error (TEST-017). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-15.3-01 |  | Assertions and coverage live outside the synthesis file list. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-15.3-02 |  | Assertions and coverage are disabled. | CHK-006:PASS | — | **VERIFIED** |
| SF-15.3-03 |  | Assertions do not sample o_rd_data while o_empty is 1. | CHK-006:PASS | — | **VERIFIED** |
| SF-15.3-04 |  | An unknown value on an input is flagged as a checker error. | CHK-002:PASS | — | **VERIFIED** |
| SF-15.3-05 | REQ-FUNC-001, REQ-FUNC-004 | No write is accepted while o_full is 1 (SVA-001). | CHK-006:PASS, CHK-016:PASS | — | **VERIFIED** |
| SF-15.3-06 | REQ-FUNC-002, REQ-FUNC-005 | No read is accepted while o_empty is 1 (SVA-002). | CHK-006:PASS | — | **VERIFIED** |
| SF-15.3-07 | REQ-FUNC-010 | A rejected request changes no pointer (SVA-003). | CHK-006:PASS | — | **VERIFIED** |
| SF-15.3-08 | REQ-FUNC-005 | o_empty is 1 whenever the scoreboard is empty (SVA-004). | CHK-007:PASS | — | **VERIFIED** |
| SF-15.3-09 | REQ-FUNC-004 | o_full is 1 whenever the scoreboard holds DEPTH words (SVA-005). | CHK-007:PASS | — | **VERIFIED** |
| SF-15.3-10 | REQ-FUNC-008 | o_overflow is 1 in the cycle after a rejected, unblocked write and only then (SVA-006). | CHK-011:PASS | — | **VERIFIED** |
| SF-15.3-11 | REQ-FUNC-009 | o_underflow is 1 in the cycle after a rejected, unblocked read and only then (SVA-007). | CHK-005:PASS | — | **VERIFIED** |
| SF-15.3-12 | REQ-FUNC-003 | The word read equals the word written, per scoreboard (SVA-008). | CHK-006:PASS | — | **VERIFIED** |
| SF-15.3-13 | REQ-SRST-002, REQ-SRST-003 | No request is accepted and no pulse is raised while blocked by the software reset (SVA-009). | CHK-003:PASS, CHK-009:PASS, CHK-011:PASS, CHK-022:PASS | 100.0 % (1/1) | **VERIFIED** |
| SF-15.3-14 | REQ-SRST-006 | o_sw_rst_busy is 1 exactly while the write FSM is not in RUN, one cycle behind the state (SVA-010). | CHK-008:PASS | — | **VERIFIED** |
| SF-15.3-15 | REQ-FUNC-004, REQ-FUNC-006 | The occupancy is between 0 and DEPTH (SVA-011). | CHK-007:PASS | — | **VERIFIED** |
| SF-16-01 |  | The RTL shall contain no latch, no combinational loop, no tri-state, no clock gating and no derived clock, so that scan insertion is possible. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-16-02 |  | The IP shall have no DFT ports; any test reset override belongs to the SoC wrapper or reset controller. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-17.1.1-01 |  | CLK-WR and CLK-RD must be defined so STA knows their common period and phase, e.g. generated clocks of one master or primary clocks with one common LCM-period waveform. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-17.1.2-01 |  | PARA_SFIFO_PTR_RETIME = 1 must be used, or the clock ratio changed. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-17.1.3-03 |  | set_clock_groups -asynchronous or set_false_path between CLK-WR and CLK-RD must not be used. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SF-17.2-01 |  | The write and read pointer registers should be placed close to the flag logic of the other domain to shorten the crossing paths. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| SF-18-01 | REQ-SRST-005 | The software reset must not erase the FIFO memory contents; no secure clearing or zeroization is provided (REQ-SRST-005). | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| SF-20.2-01 | REQ-FUNC-002 | o_rd_data must always present the word at the read pointer, with no valid output signal. | CHK-006:PASS | — | **VERIFIED** |
| SF-20.2-03 | REQ-PERF-001, REQ-PERF-002 | Continuous write and continuous read must show only the initial latency and no gap (gap-free streaming). | CHK-018:PASS | — | **VERIFIED** |
| SF-20.2-05 | REQ-FUNC-001, REQ-FUNC-002 | There must be no bypass that accepts a write into a full FIFO because a read happens at the same edge. | CHK-006:PASS, CHK-016:PASS | — | **VERIFIED** |

## Mutants

| ID | File:line | Operator | Status | Caught by | Rules | Equivalent? |
|---|---|---|---|---|---|---|
| M01 | m_vlsit_sfifo_rd.sv:180 | and_to_or | killed | CHK-001, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1, test_chk_013_random_ratios/ratio=3, tes | SF-10.7-03, SF-3-38, SF-10.6-06, SF-3-48, SF-10.7-04 |  |
| M02 | m_vlsit_sfifo_wr.sv:153 | zero_to_one | killed | CHK-001 |  | claimed: This is the reset value of the ack retiming flop. It is only used when PARA_SFIFO_PTR_RETIME=1, and the write FSM is in RUN right after reset, where the ack is  |
| M03 | m_vlsit_sfifo_wr.sv:131 | one_to_zero | killed | CHK-010, CHK-004, CHK-001, test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_rando | SF-3-04, SF-9-01, SF-3-01, SF-3-05, SF-10.2-01 |  |
| M04 | m_vlsit_sfifo_rd.sv:136 | negate_if | killed | CHK-006, CHK-007, CHK-004, test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_rando | SF-9-03, SF-9-05, SF-9-06, SF-10.2-02, SF-3-15, SF-3-52 |  |
| M05 | m_vlsit_sfifo_rd.sv:104 | ne_to_eq | killed | CHK-004, CHK-001, test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ | SF-10.2-02, SF-3-52, SF-5.3-02, SF-10.4-04, SF-3-26 |  |
| M06 | m_vlsit_sfifo_rd.sv:126 | one_to_zero | killed | CHK-010, CHK-006, CHK-007, CHK-004, CHK-001, test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0,  | SF-3-02, SF-3-03, SF-5.3-03, SF-3-04, SF-9-01 |  |
| M07 | m_vlsit_sfifo_rd.sv:123 | eq_to_ne | killed | CHK-010, CHK-006, CHK-007, CHK-004, CHK-001, test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0,  | SF-10.7-03, SF-3-38, SF-3-04, SF-3-01, SF-3-48 |  |
| M08 | m_vlsit_sfifo_wr.sv:219 | eq_to_ne | killed | CHK-004, test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1,  | SF-10.7-03, SF-3-38, SF-10.6-06, SF-10.7-04, SF-3-48 |  |
| M09 | m_vlsit_sfifo_mem.sv:52 | negate_if | killed | CHK-006, CHK-001, test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ | SF-3-01, SF-3-02, SF-3-07, SF-5.3-01, SF-3-10 |  |
| M10 | m_vlsit_sfifo_wr.sv:141 | negate_if | killed | CHK-010, test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1,  | SF-9-03, SF-9-05, SF-3-05, SF-10.2-04, SF-3-53 |  |
| M11 | m_vlsit_sfifo_wr.sv:216 | ne_to_eq | killed | test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1, test_chk_ | SF-3-33, SF-3-44, SF-10.1-02, SF-10.7-02, SF-6.2-02 |  |
| M12 | m_vlsit_sfifo_rd.sv:149 | zero_to_one | killed | CHK-001 | SF-3-38, SF-10.6-06, SF-7.3-04, SF-3-52 |  |
| M13 | m_vlsit_sfifo_wr.sv:192 | and_to_or | killed | CHK-001, test_chk_013_random_ratios/ratio=2, test_chk_013_random_ratios/ratio=3, test_chk_013_random_ratios/ratio=5 | SF-10.7-04, SF-3-48, SF-10.7-08, SF-3-42, SF-15.1-03 |  |
| M14 | m_vlsit_sfifo_wr.sv:213 | zero_to_one | killed | test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1, test_chk_ | SF-3-29, SF-3-30, SF-7.3-02, SF-7.3-01, SF-15.2-01 |  |
| M15 | m_vlsit_sfifo_wr.sv:128 | one_to_zero | killed | CHK-001 | SF-3-04, SF-9-01, SF-3-13, SF-15.2-08, SF-3-01 |  |
| M16 | m_vlsit_sfifo_rd.sv:175 | negate_if | killed | CHK-004, test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1,  | SF-10.7-03, SF-3-38, SF-10.6-06, SF-3-52, SF-10.3-13 |  |
| M17 | m_vlsit_sfifo_rd.sv:109 | ne_to_eq | killed | CHK-004, test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1,  | SF-3-38, SF-10.6-06, SF-10.7-03, SF-3-52, SF-10.3-13 |  |
| M18 | m_vlsit_sfifo_rd.sv:123 | one_to_zero | killed | CHK-001 | SF-3-04, SF-9-01, SF-3-13, SF-15.2-08, SF-3-02 |  |
| M19 | m_vlsit_sfifo_rd.sv:180 | eq_to_ne | killed | CHK-001, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1, test_chk_013_random_ratios/ratio=2, tes | SF-10.7-03, SF-3-38, SF-10.7-04, SF-10.7-08, SF-10.6-06 |  |
| M20 | m_vlsit_sfifo_wr.sv:128 | eq_to_ne | killed | CHK-010, CHK-004, CHK-001, test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_rando | SF-3-04, SF-9-01, SF-3-13, SF-15.2-08, SF-3-01 |  |
| M21 | m_vlsit_sfifo_wr.sv:212 | negate_if | killed | CHK-001, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1, test_chk_013_random_ratios/ratio=2, tes | SF-3-29, SF-7.3-01, SF-7.3-02, SF-3-30, SF-15.2-01 |  |
| M22 | m_vlsit_sfifo_wr.sv:110 | ne_to_eq | killed | CHK-001 | SF-3-33, SF-3-44, SF-10.7-02, SF-10.7-08, SF-3-48 |  |
| M23 | m_vlsit_sfifo_rd.sv:147 | zero_to_one | killed | test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1, test_chk_ | SF-12-06, SF-7.3-01, SF-3-29, SF-7.3-02, SF-15.2-01 |  |
| M24 | m_vlsit_sfifo_wr.sv:150 | zero_to_one | killed | test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1, test_chk_ | SF-3-29, SF-7.3-01, SF-3-30, SF-15.2-01, SF-6.2-04 |  |
| M25 | m_vlsit_sfifo_rd.sv:211 | negate_if | killed | CHK-001 | SF-3-04, SF-3-13, SF-9-01, SF-3-01, SF-15.2-08 |  |
| M26 | m_vlsit_sfifo_rd.sv:105 | ne_to_eq | killed | CHK-003, CHK-001, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1, test_chk_013_random_ratios/rat | SF-3-38, SF-10.6-06, SF-10.7-03, SF-15.3-13 |  |
| M27 | m_vlsit_sfifo_rd.sv:145 | one_to_zero | killed | test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1, test_chk_ | SF-3-30, SF-7.3-01, SF-7.3-02, SF-10.2-09, SF-15.2-01 |  |
| M28 | m_vlsit_sfifo_rd.sv:151 | eq_to_ne | killed | CHK-006, CHK-007, CHK-004, test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_rando | SF-10.2-02, SF-3-52, SF-9-03, SF-3-08, SF-1.3-02 |  |
| M29 | m_vlsit_sfifo_wr.sv:192 | eq_to_ne | killed | CHK-001, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1, test_chk_013_random_ratios/ratio=2, tes | SF-10.7-04, SF-3-48, SF-10.7-08, SF-3-42, SF-15.1-03 |  |
| M30 | m_vlsit_sfifo_wr.sv:188 | negate_if | killed | CHK-001, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1, test_chk_013_random_ratios/ratio=2, tes | SF-3-34, SF-3-42, SF-10.7-04, SF-10.7-06, SF-10.1-05 |  |
| M31 | m_vlsit_sfifo_wr.sv:109 | ne_to_eq | killed | CHK-010, CHK-001, test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ | SF-3-53, SF-10.2-04, SF-5.3-05, SF-10.4-07, SF-3-26 |  |
| M32 | m_vlsit_sfifo_rd.sv:201 | zero_to_one | killed | CHK-001 | SF-3-46, SF-7.3-08, SF-10.7-09 |  |
| M33 | m_vlsit_sfifo_wr.sv:151 | zero_to_one | killed | test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1, test_chk_ | SF-12-03, SF-12-06, SF-7.3-01, SF-3-29, SF-15.2-01 |  |
| M34 | m_vlsit_sfifo_rd.sv:190 | negate_if | killed | CHK-001, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1, test_chk_013_random_ratios/ratio=2, tes | SF-3-29, SF-7.3-01, SF-7.3-02, SF-3-30, SF-15.2-01 |  |
| M35 | m_vlsit_sfifo_rd.sv:146 | one_to_zero | killed | test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1, test_chk_ | SF-10.6-10, SF-7.3-01, SF-3-30, SF-15.2-01, SF-7.3-02 |  |
| M36 | m_vlsit_sfifo_rd.sv:203 | eq_to_ne | killed | CHK-001, test_chk_013_random_ratios/ratio=1, test_chk_013_random_ratios/ratio=2, test_chk_013_random_ratios/ratio=3, tes | SF-10.7-03, SF-3-48, SF-10.7-04, SF-3-38, SF-10.7-08 |  |

## Not verified by this run

- Formal proof, CDC/RDC, STA, synthesis and DFT checks are outside this flow.
- Rules marked NOT_VERIFIED_BY_SIM carry the contract's reason (static, structural, not observable...).
- Only the default parameter configuration was simulated unless stated above.

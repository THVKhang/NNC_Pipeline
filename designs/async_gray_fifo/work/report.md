# Verification report — async_gray_fifo

Generated 2026-11-12T07:27:24+00:00 by NNC Pipeline.

## Summary

| Item | Result |
|---|---|
| Rules | 416 — {'FAILED': 77, 'NOT_PROVEN': 20, 'NOT_VERIFIED_BY_SIM': 142, 'PARTIAL': 8, 'VERIFIED': 169} |
| Checks | 32 — {'FAIL': 3, 'NOT_VERIFIABLE': 3, 'PASS': 26} |
| Tests | {'fail': 1, 'pass': 33} |
| Run set | 14 runs in 10 configurations (base, model_off, syn, cell1, cell3, cell4, macro, small, wr_slow, rd_slow); primary base.s1 |
| Integration | OK |
| Code coverage (RTL), line | 99.1 % (2632/2657 lines) |
| Code coverage (RTL), block | 95.7 % (858/897 statement blocks and branch arms) |
| Code coverage (RTL), expression | 98.0 % (980/1000 condition terms) |
| Code coverage (RTL), toggle | 99.5 % (15804/15884 bit toggles 0->1 and 1->0) |
| Code coverage (RTL), functional | 100.0 % (40/40 cover points of the specification) |
| Mutation score | 91.7 % (33 killed / 3 survived / 0 not compiled) |
| Coverage target | not requested (`nnc cover <design> --target <n> --metric <m>`) |
| Formal (SymbiYosys, depth 20) | {'BOUNDED': 8, 'CEX': 2, 'PROVEN': 1, 'UNSUPPORTED': 2} — reset assumptions + verif/formal/nnc_env.sv, work/formal.md |
| Triage | 3 failure(s), 3 analysed: work/triage.md |
| Agent cost | US$48.7894 in 89 calls (A1 1.3607, A12 1.1381, A13 1.2791, A14 4.4505, A2 1.1421, A3 0.556, A4 2.88, A5 0.4355, A6 0.463, A7 21.1682, A9 13.9162); of which US$5.5388 in 3 failed calls (usage limit, timeout, invalid answer) |

## Sign-off conditions

| Condition | State |
|---|---|
| Gates G1-G3 approved | met — approved on delegation by an agent: a person should confirm |
| Interface conformance of the DUT | met |
| Every selected check PASS (no FAIL, NOT_HIT, NOT_RUN) | **not met** — FAIL 3, NOT_VERIFIABLE 3 |
| Every planned check selected | met |
| Every rule in a check or declared not verifiable | met |
| Every run of the run set built and ran | met — 14 runs |
| Mutation run | met |
| Per-requirement mutation score >= 85 % | **not met** — 5 rule(s) below: AF-10.7.4-25, AF-15.2-08, AF-20.2-12, AF-20.2-13, AF-7.3-07 |
| Formal: no counterexample, no vacuous or failed proof | **not met** — CEX 2 |

## Run set

Every check is merged over these runs: PASS when one run verified it and no run failed it; NOT_VERIFIABLE only when every run declared it so.

| Run | Parameters changed | Defines | Plusargs | Status | Tests | Failing assertions | Not verifiable here |
|---|---|---|---|---|---|---|---|
| base.s1 — CFG-BASE, metastability model on | defaults | — | +AFIFO_MSYNC_SEED={seed} +AFIFO_MSYNC_EN=1 | ran | {'pass': 34} | CHK-003, CHK-013 | 17 |
| base.s2 — CFG-BASE, metastability model on | defaults | — | +AFIFO_MSYNC_SEED={seed} +AFIFO_MSYNC_EN=1 | ran | {'pass': 34} | CHK-003, CHK-013 | 17 |
| base.s3 — CFG-BASE, metastability model on | defaults | — | +AFIFO_MSYNC_SEED={seed} +AFIFO_MSYNC_EN=1 | ran | {'pass': 34} | CHK-003, CHK-013 | 17 |
| base.s4 — CFG-BASE, metastability model on | defaults | — | +AFIFO_MSYNC_SEED={seed} +AFIFO_MSYNC_EN=1 | ran | {'pass': 34} | CHK-003, CHK-013 | 17 |
| base.s5 — CFG-BASE, metastability model on | defaults | — | +AFIFO_MSYNC_SEED={seed} +AFIFO_MSYNC_EN=1 | ran | {'pass': 34} | CHK-003, CHK-013 | 17 |
| model_off.s1 — CFG-BASE, model at nominal latency | defaults | — | +AFIFO_MSYNC_SEED={seed} +AFIFO_MSYNC_EN=0 | ran | {'pass': 34} | none | 4 |
| syn.s1 — synthesis branch of the cell wrapper | defaults | VLSIT_SYNTHESIS | +AFIFO_MSYNC_SEED={seed} +AFIFO_MSYNC_EN=1 | ran | {'pass': 34} | none | 3 |
| cell1.s1 — CFG-CELL, two DFF cells | PARA_AFIFO_CELL_TYPE=1 | — | +AFIFO_MSYNC_SEED={seed} +AFIFO_MSYNC_EN=1 | ran | {'pass': 34} | CHK-003, CHK-013 | 17 |
| cell3.s1 — CFG-CELL, 3-FF cell | PARA_AFIFO_CELL_TYPE=3 | — | +AFIFO_MSYNC_SEED={seed} +AFIFO_MSYNC_EN=1 | ran | {'fail': 1, 'pass': 33} | CHK-003, CHK-013 | 17 |
| cell4.s1 — CFG-CELL, 4-FF cell | PARA_AFIFO_CELL_TYPE=4 | — | +AFIFO_MSYNC_SEED={seed} +AFIFO_MSYNC_EN=1 | ran | {'pass': 34} | CHK-003, CHK-013 | 17 |
| macro.s1 — CFG-MACRO, SRAM macro model | PARA_AFIFO_MEM_USE_MACRO=1 | — | +AFIFO_MSYNC_SEED={seed} +AFIFO_MSYNC_EN=1 | ran | {'pass': 34} | CHK-003, CHK-013 | 17 |
| small.s1 — depth 2, data width 1 | PARA_AFIFO_DEPTH=2, PARA_AFIFO_DATA_W=1 | — | +AFIFO_MSYNC_SEED={seed} +AFIFO_MSYNC_EN=1 | ran | {'pass': 34} | CHK-003, CHK-013 | 17 |
| wr_slow.s1 — write 22 ns, read 6 ns (11:3) | defaults | — | +AFIFO_MSYNC_SEED={seed} +AFIFO_MSYNC_EN=1 | ran | {'fail': 1, 'pass': 33} | CHK-003, CHK-013 | 17 |
| rd_slow.s1 — write 6 ns, read 22 ns (3:11) | defaults | — | +AFIFO_MSYNC_SEED={seed} +AFIFO_MSYNC_EN=1 | ran | {'pass': 34} | CHK-003, CHK-013 | 17 |

## Gates

| Gate | State | Detail |
|---|---|---|
| G1_rules | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-10T04:01:18+00:00 |
| G2_contract | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-10T04:18:03+00:00 |
| G3_verif_sources | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-12T07:22:40+00:00 |
| G4_signoff | PENDING | artifacts ready for review |

## Checks

| Check | Kind | Title | Status | Evidence |
|---|---|---|---|---|
| CHK-001 | assertion | Read-domain hardware reset values | **PASS** | hits 4594, fails 0; hit in 14/14 runs; formal BOUNDED |
| CHK-002 | assertion | o_underflow is the registered one-cycle pulse of a non-blocked read while empty | **PASS** | hits 233290, fails 0; hit in 14/14 runs; formal BOUNDED |
| CHK-003 | assertion | o_empty_thr consistency for every 4-bit i_empty_thr | **FAIL** | hits 1523017, fails 534; fails in base.s1, base.s2, base.s3, base.s4, base.s5, cell1.s1, cell3.s1, cell4.s1, macro.s1, small.s1, wr_slow.s1, rd_slow.s1; formal CEX |
| CHK-004 | assertion | Read-domain outputs change only at i_clk_rd edges | **PASS** | hits 1518997, fails 0; hit in 14/14 runs; formal BOUNDED |
| CHK-005 | assertion | Scoreboard: show-ahead data, write order, exactly-once, software-reset discard | **PASS** | hits 817932, fails 0; hit in 14/14 runs; formal UNSUPPORTED |
| CHK-006 | assertion | Flags are never optimistic; occupancy is within 0..PARA_AFIFO_DEPTH | **PASS** | hits 1680955, fails 0; hit in 14/14 runs; formal UNSUPPORTED |
| CHK-007 | assertion | Write-domain hardware reset values | **PASS** | hits 5221, fails 0; hit in 14/14 runs; formal BOUNDED |
| CHK-008 | assertion | o_overflow is the registered one-cycle pulse of a non-blocked write while full | **PASS** | hits 1681616, fails 0; hit in 14/14 runs; formal BOUNDED |
| CHK-009 | assertion | Write block forces o_full=1 and the empty-FIFO o_full_thr with zero latency | **PASS** | hits 88788, fails 0; hit in 14/14 runs; formal PROVEN |
| CHK-010 | assertion | o_sw_rst_busy rises exactly at the first edge sampling i_rst_n_sw=0 | **PASS** | hits 1596416, fails 0; hit in 14/14 runs; formal BOUNDED |
| CHK-011 | assertion | o_sw_rst_busy falls only after i_rst_n_sw=1 plus a crossing round trip; write side is clean at the release | **PASS** | hits 85200, fails 0; hit in 14/14 runs; formal BOUNDED |
| CHK-012 | assertion | Write-domain outputs change only at i_clk_wr edges | **PASS** | hits 1681042, fails 0; hit in 14/14 runs; formal BOUNDED |
| CHK-013 | assertion | o_full_thr consistency for every 4-bit i_full_thr | **FAIL** | hits 1681616, fails 721; fails in base.s1, base.s2, base.s3, base.s4, base.s5, cell1.s1, cell3.s1, cell4.s1, macro.s1, small.s1, wr_slow.s1, rd_slow.s1; formal CEX |
| CHK-014 | test | Nominal crossing latency is exactly S=2 destination edges | **PASS** | test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1; verified in model_off.s1, syn.s1 |
| CHK-015 | test | Crossing latency S..S+2 with the metastability model | **NOT_VERIFIABLE** | test_chk_015_latency_with_model; verified in no run |
| CHK-016 | test | Random traffic, random clock ratios, pointer wrap-around | **NOT_VERIFIABLE** | test_chk_016_random_ratios/pair=0, test_chk_016_random_ratios/pair=1, test_chk_016_random_ratios/pair=2, test_chk_016_random_ratios/pair=3, test_chk_016_random_ratios/pair=4, test_chk_016_random_ratios/pair=5; verified in no run |
| CHK-017 | test | Regression in the build with VLSIT_SYNTHESIS defined | **PASS** | test_chk_017_synthesis_branch_regression; verified in syn.s1 |
| CHK-018 | test | Write N words then read N words, show-ahead head check | **PASS** | test_chk_018_write_n_read_n, test_chk_030_after_srst_like_hw_reset; verified in model_off.s1, syn.s1 |
| CHK-019 | test | Back-to-back burst with equal clocks | **PASS** | test_chk_019_back_to_back_equal_clocks; verified in model_off.s1, syn.s1 |
| CHK-020 | test | Overflow: writes while full are dropped; o_full falls late after a read | **PASS** | test_chk_020_overflow; verified in model_off.s1, syn.s1 |
| CHK-021 | test | Underflow: read pointer unchanged; show-ahead of the storage while empty | **PASS** | test_chk_021_underflow; verified in model_off.s1, syn.s1 |
| CHK-022 | test | Hardware reset of both domains, independent assertion and release | **PASS** | test_chk_022_hw_reset_independent; verified in model_off.s1, syn.s1 |
| CHK-023 | test | Hardware reset during a software reset (both domains, then one domain) | **PASS** | test_chk_023_hw_reset_during_srst; verified in model_off.s1, syn.s1 |
| CHK-024 | test | Hardware reset of both domains in the middle of traffic | **PASS** | test_chk_024_hw_reset_mid_traffic; verified in base.s1, base.s2, base.s3, base.s4, base.s5, model_off.s1, syn.s1, cell1.s1, cell3.s1, cell4.s1, macro.s1, small.s1, wr_slow.s1, rd_slow.s1 |
| CHK-025 | test | Software reset of a partly filled FIFO, i_rst_n_sw held low (four-phase sequence) | **FAIL** | test_chk_025_srst_partial_fifo; failed in cell3.s1, wr_slow.s1 |
| CHK-026 | test | One-cycle i_rst_n_sw pulse on a full FIFO in overflow | **PASS** | test_chk_026_srst_pulse_full_overflow; verified in model_off.s1, syn.s1 |
| CHK-027 | test | Read side released before write side (empty FIFO, reads pending) | **PASS** | test_chk_027_read_released_first; verified in model_off.s1, syn.s1 |
| CHK-028 | test | i_rst_n_sw asserted again while the write FSM is in REL | **PASS** | test_chk_028_srst_reassert_in_rel; verified in model_off.s1, syn.s1 |
| CHK-029 | test | Software reset under random traffic, with and without the metastability model | **NOT_VERIFIABLE** | test_chk_029_srst_random/pair=0, test_chk_029_srst_random/pair=1, test_chk_029_srst_random/pair=2, test_chk_029_srst_random/pair=3; verified in no run |
| CHK-030 | test | FIFO behaves after a software reset as after a hardware reset | **PASS** | test_chk_030_after_srst_like_hw_reset; verified in model_off.s1, syn.s1 |
| CHK-031 | test | A clock stops during the software reset | **PASS** | test_chk_031_clock_stop_during_srst; verified in base.s1, base.s2, base.s3, base.s4, base.s5, model_off.s1, syn.s1, cell1.s1, cell3.s1, cell4.s1, macro.s1, small.s1, wr_slow.s1, rd_slow.s1 |
| CHK-032 | test | Threshold flags while filling and draining across the thresholds | **PASS** | test_chk_032_threshold_flags/thr=0, test_chk_032_threshold_flags/thr=1, test_chk_032_threshold_flags/thr=2, test_chk_032_threshold_flags/thr=3, test_chk_032_threshold_flags/thr=4, test_chk_032_threshold_flags/thr=5; verified in model_off.s1, syn.s1 |

## Requirement traceability (RTM)

| Rule | Spec ref | Statement | Checks | Mutation | Status |
|---|---|---|---|---|---|
| AF-1.1-01 |  | The FIFO transfers a stream of data words from the write clock domain to the unrelated read clock domain. | CHK-005:PASS, CHK-016:NOT_VERIFIABLE | 100.0 % (2/2) | **PARTIAL** |
| AF-1.1-02 |  | Words are read out in the same order in which they were written. | CHK-005:PASS, CHK-018:PASS | 100.0 % (6/6) | **VERIFIED** |
| AF-1.1-03 |  | Write and read pointers cross between clock domains as Gray codes through configurable synchronizers. | CHK-014:PASS | — | **VERIFIED** |
| AF-1.1-04 |  | The IP reports full, empty, full-with-threshold, empty-with-threshold, overflow, and underflow flags to the two domains. | CHK-018:PASS, CHK-020:PASS, CHK-032:PASS | — | **VERIFIED** |
| AF-1.1-07 |  | The synchronizer module instantiates one technology cell wrapper per bit, supporting five cell options (bypass, two D-FF cells, 2-FF, 3-FF, 4-FF), configurable bit width and configurable reset value. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-1.1-09 |  | The FIFO array module provides a pure RTL implementation and a library SRAM (one write port, one read port) replacement branch. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-1.1-10 |  | Software reset is a reset input in the write clock domain using a four-phase handshake that resets both pointers in the right order and blocks both interfaces during the reset. | CHK-025:FAIL | — | **FAILED** |
| AF-1.2-01 |  | The FIFO works with two asynchronous clocks with no restriction on frequency or frequency ratio. | CHK-016:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AF-1.3-02 | REQ-PARAM-001 | The FIFO has a configurable number of entries and data width. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-1.3-06 | REQ-FUNC-013 | The synchronizer has 2, 3, or 4 stages by cell option 1 to 4; option 0 is a bypass without stages. | CHK-014:PASS | — | **VERIFIED** |
| AF-1.3-08 | REQ-FUNC-016 | The FIFO array may use the library SRAM branch when PARA_AFIFO_MEM_USE_MACRO is 1. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-2.1-01 |  | RTL deliverables must follow VLSIT RTL Design Rules v2 (REF-003) as the mandatory RTL coding, hierarchy, reset, CDC and naming baseline. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-01 | REQ-FUNC-001 | The IP shall implement an asynchronous FIFO with independent write clock domain and read clock domain. | CHK-016:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AF-3-02 | REQ-FUNC-002 | Pointers shall cross between the domains as Gray codes only. | CHK-016:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AF-3-03 | REQ-FUNC-002 | Each Gray pointer register shall change at most one bit per clock cycle of its own domain. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-04 | REQ-FUNC-003 | Words shall be read in write order; every accepted write is read exactly once, with no word lost, duplicated or reordered. | CHK-005:PASS, CHK-018:PASS | 100.0 % (4/4) | **VERIFIED** |
| AF-3-05 | REQ-FUNC-004 | The write shall be accepted: i_wr_data is stored in the entry addressed by the write pointer and the write pointer advances by one. | CHK-005:PASS, CHK-018:PASS | 100.0 % (3/3) | **VERIFIED** |
| AF-3-06 | REQ-FUNC-005, REQ-FUNC-017 | The read shall be accepted and the read pointer shall advance by one. | CHK-005:PASS, CHK-018:PASS | — | **VERIFIED** |
| AF-3-07 | REQ-FUNC-006 | Each domain shall hold a binary pointer of LPARA_PTR_W = log2(depth)+1 bits and a Gray pointer register derived from the next binary pointer. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-09 | REQ-FUNC-007 | The depth shall be a power of 2 with a minimum of 2; there is no upper limit. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-10 | REQ-FUNC-008 | o_full shall be 1, generated in the write domain, and never 0 while the FIFO is physically full. | CHK-006:PASS, CHK-018:PASS | 100.0 % (1/1) | **VERIFIED** |
| AF-3-11 | REQ-FUNC-008 | o_full may stay 1 late (pessimistic). | CHK-020:PASS | — | **VERIFIED** |
| AF-3-12 | REQ-FUNC-009 | o_empty shall be 1, generated in the read domain, and never 0 while the FIFO is physically empty. | CHK-006:PASS, CHK-018:PASS | 100.0 % (1/1) | **VERIFIED** |
| AF-3-13 | REQ-FUNC-009 | o_empty may stay 1 late (pessimistic). | CHK-014:PASS | — | **VERIFIED** |
| AF-3-14 | REQ-FUNC-010 | o_full_thr shall be 1 when the write-domain occupancy estimate is greater than or equal to i_full_thr, for every LPARA_PTR_W-bit value. | CHK-013:FAIL, CHK-032:PASS | — | **FAILED** |
| AF-3-15 | REQ-FUNC-010 | o_empty_thr shall be 1 when the read-domain occupancy estimate is less than or equal to i_empty_thr, for every LPARA_PTR_W-bit value. | CHK-003:FAIL, CHK-032:PASS | 100.0 % (1/1) | **FAILED** |
| AF-3-16 | REQ-FUNC-010 | Occupancy estimate is binary write pointer minus binary read pointer, using the synchronized pointer of the other domain; both threshold flags are combinational. | CHK-032:PASS | — | **VERIFIED** |
| AF-3-17 | REQ-FUNC-010 | The thresholds are static and shall not change while the FIFO is in use. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-18 | REQ-FUNC-011 | m_vlsit_afifo_top shall be a structural wrapper instantiating only m_vlsit_afifo_wr, m_vlsit_afifo_rd and m_vlsit_afifo_mem. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-19 | REQ-FUNC-012 | m_vlsit_afifo_wr shall contain write pointer, full/threshold, overflow logic, read Gray pointer synchronizer, write-side software reset FSM, acknowledge synchronizer and memory write port outputs; m_vlsit_afifo_rd the read-side equivalents. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-20 | REQ-FUNC-013 | m_vlsit_afifo_sync shall provide a configurable-width synchronizer with reset value per bit; stages are 2 for options 1 and 2, 3 for option 3, 4 for option 4, 0 for option 0. | CHK-014:PASS | — | **VERIFIED** |
| AF-3-21 | REQ-FUNC-014 | m_vlsit_afifo_sync shall contain no flip-flop or cell of its own and shall instantiate only m_vlsit_afifo_cell_sync, one per bit, in every configuration and both VLSIT_SYNTHESIS branches. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-22 | REQ-FUNC-014 | The wrapper shall select by PARA_AFIFO_CELL_TYPE: 0 bypass (o_q = i_d), 1 two series DFFs, 2 one 2-FF cell, 3 one 3-FF cell, 4 one 4-FF cell. | CHK-014:PASS | — | **VERIFIED** |
| AF-3-23 | REQ-FUNC-014 | Option 0 (bypass) shall not be used for a Gray pointer crossing. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-24 | REQ-FUNC-015 | m_vlsit_afifo_mem shall be an independent module instantiated in m_vlsit_afifo_top, modelled as an SRAM with one write port (write domain) and one read port (read domain). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-25 | REQ-FUNC-016 | m_vlsit_afifo_mem shall provide a generate branch replacing the RTL array with a library 1W1R SRAM through m_vlsit_afifo_ram_macro; the default is the RTL array. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-26 | REQ-FUNC-017 | o_rd_data shall always show the word at the current read pointer, including while empty (show-ahead); after each read-clock edge it is the word at the new read pointer. | CHK-005:PASS, CHK-021:PASS | 100.0 % (2/2) | **VERIFIED** |
| AF-3-27 | REQ-FUNC-017 | The read module shall drive the storage read address of the next read pointer and the storage shall be read every read-clock cycle. | CHK-021:PASS | — | **VERIFIED** |
| AF-3-28 | REQ-FUNC-018 | Full, empty and threshold flags shall be combinational functions of local pointer registers and the synchronized pointer of the other domain. | CHK-012:PASS, CHK-013:FAIL, CHK-018:PASS | — | **FAILED** |
| AF-3-29 | REQ-IF-001 | Module ports shall be as listed in Section 6 and top ports shall not depend on parameter values. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-30 | REQ-CLK-001 | Write and read clocks shall be treated as fully asynchronous with no assumed phase or frequency relation and no frequency restriction. | CHK-016:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AF-3-31 | REQ-CLK-002 | Every clock-domain crossing shall use a Gray pointer registered in its own domain followed directly by m_vlsit_afifo_sync, with no logic before the first stage or between stages. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-32 | REQ-CLK-003 | The read data path from the FIFO array to the read domain shall be valid. | CHK-005:PASS | — | **VERIFIED** |
| AF-3-33 | REQ-CLK-004 | m_vlsit_afifo_wr shall contain only write-clock-domain logic and m_vlsit_afifo_rd only read-clock-domain logic; the array is owned by neither and is instantiated in the top. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-34 | REQ-RESET-001 | i_rst_n_wr shall be already synchronized to i_clk_wr and i_rst_n_rd to i_clk_rd; the IP shall not contain a reset synchronizer. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-35 | REQ-RESET-002, REQ-SRST-012 | The FIFO shall be empty: both pointers 0, full = 0, empty = 1, overflow = 0, underflow = 0. | CHK-001:PASS, CHK-007:PASS, CHK-022:PASS, CHK-024:PASS | 90.0 % (9/10) | **VERIFIED** |
| AF-3-36 | REQ-RESET-002, REQ-SRST-012 | Flops shall use asynchronous-assert active-low reset; the two resets are independent and need not be asserted together. | CHK-001:PASS, CHK-007:PASS, CHK-022:PASS | 100.0 % (5/5) | **VERIFIED** |
| AF-3-37 | REQ-PARAM-001 | The depth shall be configurable by PARA_AFIFO_DEPTH. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-38 | REQ-PARAM-002 | The data width shall be configurable by PARA_AFIFO_DATA_W. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-39 | REQ-PARAM-003 | The RTL shall not contain an elaboration check for illegal parameter values; verification shall use legal values only. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-40 | REQ-ERR-001 | o_overflow shall be raised as a 1-cycle pulse and the write shall not change stored data or the write pointer. | CHK-008:PASS, CHK-020:PASS | 100.0 % (1/1) | **VERIFIED** |
| AF-3-41 | REQ-ERR-002 | o_underflow shall be raised as a 1-cycle pulse, the read pointer unchanged, and o_rd_data keeps showing the word at the current read pointer. | CHK-002:PASS, CHK-021:PASS | 100.0 % (1/1) | **VERIFIED** |
| AF-3-42 | REQ-SRST-001 | A software reset sequence shall start; i_rst_n_sw is active-low in the write domain and may be held for one or more write-clock cycles. | CHK-010:PASS, CHK-025:FAIL, CHK-026:PASS | 100.0 % (1/1) | **FAILED** |
| AF-3-43 | REQ-SRST-002 | The request shall be a register req_wr in m_vlsit_afifo_wr crossing to the read domain via m_vlsit_afifo_sync (width 1, same stage count) with no logic before the first stage. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-44 | REQ-SRST-003 | A read request shall not be accepted, combinationally with zero latency. | CHK-025:FAIL, CHK-029:NOT_VERIFIABLE | 100.0 % (2/2) | **FAILED** |
| AF-3-45 | REQ-SRST-004 | o_empty shall be 1. | CHK-025:FAIL | 100.0 % (1/1) | **FAILED** |
| AF-3-46 | REQ-SRST-005 | It shall reset the read pointer (binary and Gray) to 0 and only then raise ack_rd. | CHK-025:FAIL | 100.0 % (1/1) | **FAILED** |
| AF-3-47 | REQ-SRST-006 | The acknowledge shall cross to the write domain through m_vlsit_afifo_sync (width 1, same stage count) with no logic before the first stage. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-48 | REQ-SRST-007 | It shall reset the write pointer (binary and Gray) to 0. | CHK-025:FAIL | — | **FAILED** |
| AF-3-49 | REQ-SRST-008 | A write request shall not be accepted, combinationally with zero latency from i_rst_n_sw and FSM state. | CHK-009:PASS | — | **VERIFIED** |
| AF-3-50 | REQ-SRST-009 | The handshake shall have four phases: request up, acknowledge up, request down, acknowledge down. | CHK-025:FAIL | 100.0 % (1/1) | **FAILED** |
| AF-3-51 | REQ-SRST-009 | The request shall not fall before i_rst_n_sw = 1 and the write pointer is reset; the acknowledge shall not fall before the request is seen at 0 in the read domain. | CHK-011:PASS, CHK-025:FAIL | 100.0 % (1/1) | **FAILED** |
| AF-3-52 | REQ-SRST-010 | The read reset FSM shall return to RUN only when the synchronized request is 0 and the synchronized write Gray pointer is 0. | CHK-025:FAIL, CHK-029:NOT_VERIFIABLE | — | **FAILED** |
| AF-3-53 | REQ-SRST-010 | The write reset FSM shall return to RUN only when the synchronized acknowledge is 0 and the synchronized read Gray pointer is 0. | CHK-011:PASS, CHK-025:FAIL | 100.0 % (3/3) | **FAILED** |
| AF-3-54 | REQ-SRST-011 | The read FSM shall return to RUN before the write FSM returns to RUN. | CHK-027:PASS | 100.0 % (2/2) | **VERIFIED** |
| AF-3-55 | REQ-SRST-012 | Flags shall be generated by normal FIFO logic; both pointers are 0, so o_empty = 1 and o_full = 0 until the first write crosses to the read domain. | CHK-011:PASS, CHK-025:FAIL, CHK-030:PASS | 100.0 % (3/3) | **FAILED** |
| AF-3-56 | REQ-SRST-013 | The software reset sequence shall complete for any i_rst_n_sw width, any clock frequency and ratio, and with the metastability model enabled. | CHK-025:FAIL, CHK-026:PASS, CHK-029:NOT_VERIFIABLE | 100.0 % (1/1) | **FAILED** |
| AF-3-57 | REQ-SRST-014 | Words in the FIFO are discarded; a read accepted before the request reaches the read domain returns a valid pre-reset word; storage is not cleared. | CHK-005:PASS, CHK-025:FAIL | — | **FAILED** |
| AF-3-58 | REQ-SRST-015 | A hardware reset of a domain shall have priority over software reset, asynchronously resetting that domain's FSM and pointers. | CHK-023:PASS | — | **VERIFIED** |
| AF-3-59 | REQ-SRST-016 | Writes shall stay blocked and a new sequence shall start when the FSM is back in RUN. | CHK-028:PASS | — | **VERIFIED** |
| AF-3-60 | REQ-SRST-017 | o_full shall be 1. | CHK-009:PASS | — | **VERIFIED** |
| AF-3-61 | REQ-SRST-017 | A blocked write or read shall not raise o_overflow or o_underflow. | CHK-008:PASS | — | **VERIFIED** |
| AF-3-62 | REQ-SRST-017 | o_full_thr and o_empty_thr shall take the values of an empty FIFO. | CHK-003:FAIL, CHK-009:PASS, CHK-025:FAIL | 100.0 % (3/3) | **FAILED** |
| AF-3-63 | REQ-SRST-018 | o_sw_rst_busy shall be the direct output of flop reg_sw_rst_busy with no combinational logic, set when the write reset FSM leaves RUN and cleared when it returns to RUN. | CHK-010:PASS, CHK-011:PASS, CHK-012:PASS | — | **VERIFIED** |
| AF-3-64 | REQ-SRST-018 | o_sw_rst_busy shall be 1 in states REQ, PTR, HOLD, REL and 0 in RUN independent of i_rst_n_sw and read FSM state, and 0 after i_rst_n_wr hardware reset. | CHK-007:PASS, CHK-010:PASS | 100.0 % (1/1) | **VERIFIED** |
| AF-3-66 | REQ-RTL-001 | RTL shall comply with REF-003; technology cells and memory macros shall appear only in m_vlsit_afifo_cell_sync and m_vlsit_afifo_ram_macro. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-67 | REQ-RTL-002 | Synthesis, lint, CDC, formal and equivalence flows shall define VLSIT_SYNTHESIS; in that branch m_vlsit_afifo_cell_sync contains only library cell instances and follows REF-003. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-68 | REQ-RTL-003 | Every technology library cell and memory macro instance shall be named u_dont_touch_ (e.g. u_dont_touch_dff_0, u_dont_touch_sync2ff, u_dont_touch_sram); design module instances keep u_. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-71 | REQ-VER-001 | No module other than m_vlsit_afifo_cell_sync shall model metastability; option 0 has no model. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-72 | REQ-VER-002 | m_vlsit_afifo_ram_macro shall instantiate only VLSIT_CELL_SRAM_1W1R in every flow and both branches, matching Section 6.2 interface, with no simulation model of its own. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-73 | REQ-VER-001, REQ-VER-003 | Example technology cell models shall be delivered as synthesizable RTL, one module per file in 000_Common/rtl_cells, following REF-003 except names (pins CK, RN or SN, D, Q). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-75 | REQ-DFT-001 | The IP shall have no DFT port and no test hook. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-3-76 | REQ-PD-001 | The constraint contract of Section 17 shall be delivered with the IP. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-4-01 |  | Each optional feature must be absent from the logic when its parameter is 0, with the generate branch not elaborated. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-4-02 |  | The top-level port list must be the same in every configuration. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-4-03 |  | Parameter values outside those defined in Section 8 must not be used; such illegal combinations are not checked by the IP. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-5.1-01 |  | Flags are pessimistic: full and empty may be late to deassert but must never deassert early. | CHK-006:PASS | — | **VERIFIED** |
| AF-5.3-01 |  | The write domain accepts i_wr_data and drives the memory write port with enable, address (low LPARA_ADDR_W bits of binary write pointer) and data, storing the word. | CHK-005:PASS, CHK-018:PASS | 100.0 % (4/4) | **VERIFIED** |
| AF-5.3-02 |  | The binary write pointer increments, its Gray code is registered, and the Gray pointer crosses to the read domain. | CHK-014:PASS, CHK-018:PASS | — | **VERIFIED** |
| AF-5.3-03 |  | After S read-clock stages of the selected cell the read domain sees the new write Gray pointer and updates empty from it. | CHK-014:PASS | — | **VERIFIED** |
| AF-5.3-04 |  | o_rd_data always shows the word at the read address (show-ahead). | CHK-005:PASS | 100.0 % (2/2) | **VERIFIED** |
| AF-5.3-05 |  | The read domain accepts a read, increments the read pointer so o_rd_data shows the next word, and registers the Gray code. | CHK-005:PASS, CHK-018:PASS | — | **VERIFIED** |
| AF-5.3-06 |  | The read Gray pointer crosses to the write domain, which after the synchronizer latency sees it, updates full and frees the entry for a new write. | CHK-014:PASS, CHK-020:PASS | — | **VERIFIED** |
| AF-5.3-07 |  | i_rst_n_sw starts a handshake blocking both interfaces, resets the read pointer first and the write pointer after the acknowledge, and releases the read side before the write side. | CHK-025:FAIL | — | **FAILED** |
| AF-5.3-09 |  | The read-domain storage output register may capture an unsettled word only while the FIFO is empty, and the word is captured again before o_empty falls. | CHK-014:PASS | — | **VERIFIED** |
| AF-5.4-01 |  | The number of stored words (write pointer minus read pointer modulo 2 x depth) stays between 0 and PARA_AFIFO_DEPTH. | CHK-006:PASS | — | **VERIFIED** |
| AF-5.4-02 |  | full and empty are never both 1. | CHK-016:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AF-5.4-03 |  | A Gray pointer register changes at most one bit per clock cycle. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AF-5.4-04 |  | The write side must not overwrite an entry not yet read, and the read side must not read an entry not yet written, per registered flags. | CHK-005:PASS, CHK-006:PASS | — | **VERIFIED** |
| AF-5.4-05 |  | A rejected write or read leaves pointers and storage unchanged. | CHK-020:PASS, CHK-021:PASS | — | **VERIFIED** |
| AF-5.4-06 |  | At the instant a side leaves software reset, its own pointer and its synchronized copy of the other pointer are both 0. | CHK-025:FAIL | — | **FAILED** |
| AF-6.1-01 |  | IF-001 must be provided as a required custom write interface (enable + data) on the producer side in the CLK-WR domain, with input data and output flags. | CHK-018:PASS | — | **VERIFIED** |
| AF-6.1-02 |  | IF-002 must be provided as a required custom read interface (enable + data) on the consumer side in the CLK-RD domain, with input enable and output data and flags. | CHK-018:PASS | — | **VERIFIED** |
| AF-6.1-04 |  | IF-004 must be provided as a required software reset control (level input request, optional busy output status) in the CLK-WR domain. | CHK-025:FAIL | — | **FAILED** |
| AF-6.2-01 |  | The top-level port list must never depend on a parameter value. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-6.2-02 |  | CLK-type ports are free running, rising-edge active, with no clock gating inside the IP. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-6.2-03 |  | Active-low reset must stay low for at least one clock edge of its domain so the flops are reset; it is released synchronously outside the IP. | CHK-022:PASS | — | **VERIFIED** |
| AF-6.2-04 |  | Each edge with request level 1 and acceptance condition true (not full / not empty) is exactly one transaction; request is level-sampled with no minimum width. | CHK-005:PASS, CHK-019:PASS | — | **VERIFIED** |
| AF-6.2-05 |  | i_wr_data is captured only at the edge where the write is accepted and ignored otherwise. | CHK-005:PASS | — | **VERIFIED** |
| AF-6.2-06 |  | LVL-STS flags are combinational from registers, stay 1 while the condition holds, and change only after a clock edge or synchronizer stage, except for static threshold effects. | CHK-004:PASS, CHK-012:PASS | — | **VERIFIED** |
| AF-6.2-07 |  | REG-STS outputs are driven directly by a flop with no combinational logic and change only at a clock edge of their domain. | CHK-012:PASS | — | **VERIFIED** |
| AF-6.2-08 |  | PULSE outputs are registered, 1 for exactly one clock cycle per event in the cycle after the rejected request, return to 0 by themselves, and are not sticky. | CHK-002:PASS, CHK-008:PASS | — | **VERIFIED** |
| AF-6.2-10 |  | STATIC threshold inputs must not change while the FIFO is in use; they are written once before use, with no synchronizer. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-6.2-11 | REQ-SRST-008 | The IP reacts to the i_rst_n_sw level sampled at i_clk_wr; one reset sequence runs per assertion and ends only after the level is de-asserted. | CHK-025:FAIL, CHK-026:PASS | — | **FAILED** |
| AF-6.2-12 |  | REG-LVL handshake signals come from flops, cross through a 1-bit synchronizer, change only on a handshake step and stay stable until the other side has answered. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AF-6.2-13 |  | Gray pointer registers change by at most one bit per clock edge and enter synchronizers directly with no logic before the first stage. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AF-6.2-15 | REQ-SRST-008 | Writes are blocked from the cycle in which i_rst_n_sw is 0; a one-cycle low pulse or a longer low level starts the reset handshake. | CHK-009:PASS, CHK-026:PASS | — | **VERIFIED** |
| AF-6.2-16 |  | o_sw_rst_busy is set at the edge where the write FSM leaves RUN and cleared at the edge where it returns to RUN, equal to write FSM not in RUN. | CHK-010:PASS, CHK-011:PASS | — | **VERIFIED** |
| AF-6.2-17 |  | o_full is combinational from the write pointer and synchronized read pointer; writes are rejected while it is 1, and it is 1 while the write side is blocked by software reset. | CHK-006:PASS, CHK-009:PASS | — | **VERIFIED** |
| AF-6.2-18 | REQ-FUNC-010 | o_full_thr is a combinational function of i_full_thr and the pointers, 1 when occupancy estimate is greater than or equal to i_full_thr. | CHK-013:FAIL, CHK-032:PASS | — | **FAILED** |
| AF-6.2-19 | REQ-FUNC-017 | o_rd_data shows the word at the current read pointer (show-ahead); an accepted read consumes it and the next word appears. | CHK-004:PASS, CHK-005:PASS | 100.0 % (1/1) | **VERIFIED** |
| AF-6.2-20 |  | o_empty is combinational from read pointer and synchronized write pointer, reads are rejected while it is 1, and it is 1 during the whole software reset. | CHK-006:PASS, CHK-025:FAIL | — | **FAILED** |
| AF-6.2-21 | REQ-FUNC-010 | o_empty_thr is a combinational function of i_empty_thr and the pointers, 1 when occupancy estimate is less than or equal to i_empty_thr. | CHK-003:FAIL, CHK-032:PASS | 100.0 % (1/1) | **FAILED** |
| AF-6.2-22 |  | The Gray pointer registers are updated only at the clock edge that accepts a write or read, respectively. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AF-6.2-23 |  | o_mem_wr_en is 1 combinationally in the cycle when i_wr_en = 1 and o_full = 0. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AF-6.2-24 |  | o_mem_wr_addr is a register output of the low bits of the binary write pointer, and o_mem_wr_data copies i_wr_data in the same cycle. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AF-6.2-25 |  | o_mem_rd_addr is a combinational function of i_rd_en and the empty flag, giving the low bits of the next read pointer. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AF-6.2-26 |  | The storage is read in every read-clock cycle with no read enable; i_mem_rd_data is valid after the edge that captured the address (latency 1) and drives o_rd_data. | CHK-021:PASS | — | **VERIFIED** |
| AF-6.2-27 |  | The sync o_data is a register output delayed by S destination edges after the change (S to S+2 with the metastability model). | CHK-015:NOT_VERIFIABLE | 100.0 % (2/2) | **NOT_PROVEN** |
| AF-6.2-28 |  | The cell resets or sets all stages asynchronously per PARA_AFIFO_CELL_RST_VAL; o_q is the last-stage output, or i_d itself with option 0. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AF-6.2-29 |  | The memory stores i_wr_data at i_wr_addr at the i_clk_wr edge when write enable is 1. | CHK-005:PASS | — | **VERIFIED** |
| AF-6.2-30 |  | The memory samples i_rd_addr every read-clock cycle and o_rd_data registers the word at it with latency 1; the array has no reset. | CHK-021:PASS | — | **VERIFIED** |
| AF-6.2-31 |  | i_rd_en_n of the RAM macro wrapper is tied to 0 by m_vlsit_afifo_mem. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-6.2-32 |  | Each DW bit whose BWEB bit is 0 is written to the word at AW; the wrapper ties BWEB to zero for whole-word write. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-6.2-33 |  | At the CLKR rising edge with REB = 0, QR shows the word at AR after the edge; QR keeps its value while REB = 1. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-6.2-34 |  | The model VLSIT_CELL_SRAM_1W1R returns the old word and the stored word is not corrupted. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-6.2-35 |  | m_vlsit_afifo_ram_macro instantiates VLSIT_CELL_SRAM_1W1R as u_dont_touch_sram and nothing else, in every flow. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-6.3-01 | REQ-FUNC-004 | When i_wr_en = 1 and full = 0, the FIFO accepts the write and stores the word. | CHK-018:PASS | 100.0 % (2/2) | **VERIFIED** |
| AF-6.3-02 | REQ-ERR-001 | A write while full = 1 must be rejected (word not stored) and overflow must be raised. | CHK-008:PASS, CHK-020:PASS | — | **VERIFIED** |
| AF-6.3-03 | REQ-FUNC-005 | When i_rd_en = 1 and empty = 0, the FIFO accepts the read and the read pointer advances. | CHK-018:PASS | — | **VERIFIED** |
| AF-6.3-04 | REQ-ERR-002 | A read while empty = 1 must be rejected (pointer not advanced) and underflow must be raised. | CHK-002:PASS, CHK-021:PASS | — | **VERIFIED** |
| AF-6.3-05 | REQ-FUNC-001 | Simultaneous write and read are allowed; the write and read interfaces operate independently in their different clock domains. | CHK-016:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AF-6.3-06 | REQ-SRST-001 | When i_rst_n_sw is low for one cycle or more, the FIFO performs a four-phase handshake, blocks both interfaces and resets the pointers. | CHK-025:FAIL | — | **FAILED** |
| AF-6.3-07 | REQ-SRST-003, REQ-SRST-008, REQ-SRST-017 | Writes or reads during the software reset must not be accepted and must not generate an error pulse. | CHK-008:PASS, CHK-025:FAIL | — | **FAILED** |
| AF-6.3-08 |  | Interface signals are sampled on the rising edge of the respective domain clock. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-6.3-09 |  | i_wr_data is captured at the accepting edge, so no hold of i_wr_data after that edge is required. | CHK-005:PASS | — | **VERIFIED** |
| AF-7.2-01 |  | The write Gray pointer is registered in CLK-WR, then passes through m_vlsit_afifo_sync (2/3/4 stages) in the read domain, reset by i_rst_n_rd to PARA_AFIFO_SYNC_RST_VAL. | CHK-014:PASS, CHK-022:PASS | — | **VERIFIED** |
| AF-7.2-02 |  | The read Gray pointer is registered in CLK-RD, then passes through m_vlsit_afifo_sync in the write domain, reset by i_rst_n_wr. | CHK-014:PASS, CHK-022:PASS | — | **VERIFIED** |
| AF-7.2-03 |  | Stored data is read by the read domain without a synchronizer and must be stable by the pointer protocol when read. | CHK-005:PASS, CHK-016:NOT_VERIFIABLE | — | **PARTIAL** |
| AF-7.2-04 |  | i_full_thr and i_empty_thr are static, written once before the FIFO is used and not changed while in use, and are not synchronized. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-7.2-05 |  | req_wr is registered in CLK-WR, then passes through a 1-bit m_vlsit_afifo_sync (2/3/4 stages) in the read domain, reset to 0 by i_rst_n_rd. | CHK-025:FAIL | — | **FAILED** |
| AF-7.2-06 |  | ack_rd is registered in CLK-RD, then passes through a 1-bit m_vlsit_afifo_sync in the write domain, reset to 0 by i_rst_n_wr. | CHK-011:PASS, CHK-025:FAIL | — | **FAILED** |
| AF-7.2-07 |  | No combinational logic is allowed between the launch Gray register and the first synchronizer stage, nor between synchronizer stages. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-7.2-10 |  | The software reset is a synchronous reset of pointers and flags performed by each domain's FSM and adds no asynchronous reset or reset-domain crossing. | CHK-004:PASS, CHK-012:PASS | — | **VERIFIED** |
| AF-7.2-11 |  | The two hardware resets are independent inputs and need not be asserted together. | CHK-022:PASS | — | **VERIFIED** |
| AF-7.2-12 |  | The IP neither detects nor repairs the inconsistent pointer state that results from resetting only one domain. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| AF-7.3-01 |  | i_rst_n_wr is active-low, asserts asynchronously, and resets all write-domain state, the read-pointer synchronizer and flags: pointers 0, full 0, overflow 0. | CHK-007:PASS | 100.0 % (7/7) | **VERIFIED** |
| AF-7.3-02 |  | i_rst_n_rd is active-low, asserts asynchronously, and resets all read-domain state, the write-pointer synchronizer and flags: pointers 0, empty 1, underflow 0. | CHK-001:PASS | 85.7 % (6/7) | **VERIFIED** |
| AF-7.3-03 |  | i_rst_n_sw is an active-low synchronous software reset acting through both FSMs, resetting pointers to 0, o_empty to 1, o_full to 0, without clearing storage. | CHK-025:FAIL | 100.0 % (1/1) | **FAILED** |
| AF-7.3-06 |  | FIFO storage is resetless; its content is not consumed until the write pointer proves it was written, and o_rd_data while empty is undefined until written. | CHK-005:PASS, CHK-021:PASS | — | **VERIFIED** |
| AF-7.3-07 |  | i_rst_n_wr and i_rst_n_rd act asynchronously on the FSMs and pointers of their domain at any time, also during a software reset. | CHK-023:PASS | 0.0 % (0/1) **below** | **VERIFIED** |
| AF-7.3-08 |  | The IP does not repair the case where the handshake waits forever for the other domain. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| AF-8-01 |  | Parameters shall be declared as parameter logic [31:0] PARA_AFIFO_ with the three comment lines required by REF-003 PAR-02. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-8-04 |  | PARA_AFIFO_DEPTH (default 8) shall be a power of 2, minimum 2, with no upper limit; LPARA_ADDR_W and LPARA_PTR_W derive from it. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-8-05 |  | PARA_AFIFO_DATA_W (default 32) shall be at least 1, with no upper limit, and sets the width of i_wr_data, o_rd_data and storage. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-8-06 |  | PARA_AFIFO_CELL_TYPE (default 2) shall be 0..4 (0 bypass, 1 two series D flip-flops, 2 one 2-FF cell, 3 one 3-FF cell, 4 one 4-FF cell), with the same value on top, wr, rd, sync, cell_sync and both crossings. | CHK-014:PASS | — | **VERIFIED** |
| AF-8-08 |  | PARA_AFIFO_CELL_RST_VAL (default 0) shall be 0 for a flop with asynchronous reset to 0 or 1 for asynchronous set to 1, taken per synchronizer bit from PARA_AFIFO_SYNC_RST_VAL. | not verified: static_or_structural | 100.0 % (1/1) | **NOT_VERIFIED_BY_SIM** |
| AF-8-09 |  | PARA_AFIFO_MEM_USE_MACRO (default 0) shall be 0 for an RTL array or 1 for the library SRAM wrapper, using the generic macro model until a real macro is mapped. | not verified: static_or_structural | 100.0 % (2/2) | **NOT_VERIFIED_BY_SIM** |
| AF-8-10 |  | PARA_AFIFO_SYNC_W shall be 1 or more and is set by the parent to LPARA_PTR_W, giving the synchronizer width. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-8-11 |  | PARA_AFIFO_SYNC_RST_VAL (default 0) shall be a vector of PARA_AFIFO_SYNC_W bits giving one reset value per bit for every synchronizer stage. | not verified: static_or_structural | 100.0 % (3/3) | **NOT_VERIFIED_BY_SIM** |
| AF-8-12 |  | PARA_AFIFO_SYNC_RST_VAL shall be a legal Gray pointer value, namely 0. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-8-13 |  | LPARA_ADDR_W shall be derived as log2 of PARA_AFIFO_DEPTH, and LPARA_PTR_W shall be derived as LPARA_ADDR_W + 1. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-8-14 |  | Illegal configurations (depth not a power of 2, depth below 2, stage count outside 2..4, option parameter outside 0..1) shall not be used. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-9-01 |  | The binary pointer shall be an unsigned LPARA_PTR_W-bit value ranging 0 to 2 x depth - 1 and wrapping by design, with no extension or truncation. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AF-9-02 |  | The address shall be the low LPARA_ADDR_W bits of the binary pointer (0 to depth - 1), formed by truncating the MSB. | CHK-021:PASS | — | **VERIFIED** |
| AF-9-03 |  | The Gray pointer shall be LPARA_PTR_W bits wide, computed as gray = bin XOR (bin >> 1), changing one bit per increment. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AF-9-04 |  | Gray to binary conversion shall be LPARA_PTR_W bits wide, where bit i of binary equals XOR of Gray bits i..LPARA_PTR_W-1; invalid Gray values cannot occur in the model with one-bit changes. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AF-9-05 |  | The occupancy estimate shall be the binary pointer difference modulo 2 x depth with explicit width cast, and shall differ from true occupancy only by pointer updates still inside the synchronizer (pessimistic). | CHK-032:PASS | — | **VERIFIED** |
| AF-10.1-01 |  | While empty, o_empty must be 1 and reads must be rejected; a read request produces o_underflow. | CHK-002:PASS, CHK-021:PASS, CHK-022:PASS | — | **VERIFIED** |
| AF-10.1-02 |  | In the Partial state, reads and writes must both be accepted. | CHK-016:NOT_VERIFIABLE, CHK-019:PASS | — | **PARTIAL** |
| AF-10.1-03 |  | While full, o_full must be 1 and writes must be rejected; a write request produces o_overflow. | CHK-008:PASS, CHK-020:PASS | — | **VERIFIED** |
| AF-10.1-04 |  | Software reset must block both interfaces, set o_empty = 1, reset pointers by the handshake, and signal o_sw_rst_busy until both reset FSMs are back in RUN, read side first. | CHK-025:FAIL | — | **FAILED** |
| AF-10.2-01 |  | A write must store the data, increment the write pointer and register its Gray value, queuing the word. | CHK-018:PASS | — | **VERIFIED** |
| AF-10.2-02 |  | A read must increment the read pointer and register its Gray value; o_rd_data then shows the next word with no extra latency (show-ahead). | CHK-005:PASS | — | **VERIFIED** |
| AF-10.2-03 |  | The write must be rejected and o_overflow must pulse for one cycle in the cycle after the request. | CHK-008:PASS | — | **VERIFIED** |
| AF-10.2-04 |  | The read must be rejected and o_underflow must pulse for one cycle in the cycle after the request. | CHK-002:PASS | — | **VERIFIED** |
| AF-10.2-05 |  | Software reset must run a four-phase handshake (block, reset read pointer, acknowledge, reset write pointer, release read side, release write side), leaving the FIFO empty with both pointers 0 and flags normal. | CHK-025:FAIL | — | **FAILED** |
| AF-10.3-01 |  | A destination-domain flag, combinational from the synchronized pointer, must reflect a source pointer update after destination edge S. | CHK-014:PASS | — | **VERIFIED** |
| AF-10.3-02 | REQ-VER-001 | The flag must change after destination edge S, S+1, or S+2. | CHK-015:NOT_VERIFIABLE | 100.0 % (4/4) | **NOT_PROVEN** |
| AF-10.3-03 | REQ-FUNC-008, REQ-FUNC-009 | Flags must be pessimistic in between: never report not-full or not-empty prematurely. | CHK-006:PASS | — | **VERIFIED** |
| AF-10.4-01 |  | The write pointer Gray register must update at the same edge as the storage write, and an entry must be rewritten only after the write domain has seen the read pointer pass it. | CHK-005:PASS, CHK-014:PASS | — | **VERIFIED** |
| AF-10.4-03 |  | o_empty must not fall earlier than the second read-clock edge after the write; minimum latency is S >= 2 edges, also for the model. | CHK-014:PASS, CHK-015:NOT_VERIFIABLE | — | **PARTIAL** |
| AF-10.5-01 |  | A valid word must never be read while it is being written. | CHK-005:PASS, CHK-016:NOT_VERIFIABLE | — | **PARTIAL** |
| AF-10.5-02 |  | The value read must not be used because o_empty = 1; the macro model returns the old word. | CHK-005:PASS | — | **VERIFIED** |
| AF-10.5-04 |  | Reads must not be accepted before a write (o_empty = 1); o_rd_data may be undefined while the entry at the read pointer was never written. | CHK-006:PASS, CHK-022:PASS | — | **VERIFIED** |
| AF-10.5-05 | REQ-FUNC-017 | The macro wrapper must present show-ahead behavior, with a synchronous storage read using the next-pointer address. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-10.6.2-01 |  | The write is accepted; the storage array and the write Gray pointer both update at that same write edge. | CHK-014:PASS | — | **VERIFIED** |
| AF-10.6.2-02 |  | o_rd_data shows the new word (show-ahead) before o_empty falls, because the storage is read every cycle with the next read pointer address. | CHK-014:PASS | — | **VERIFIED** |
| AF-10.6.2-03 |  | o_empty falls S read edges after the first capturing edge of the write pointer, combinationally from the synchronized pointer. | CHK-014:PASS | — | **VERIFIED** |
| AF-10.6.2-06 |  | o_full falls late, after the read pointer crosses to the write domain, not at the read edge. | CHK-020:PASS | — | **VERIFIED** |
| AF-10.6.2-08 |  | o_rd_data keeps the old word until the next read edge, which captures the new word while o_empty is still 1. | CHK-021:PASS | — | **VERIFIED** |
| AF-10.6.2-09 |  | i_wr_en, i_wr_data and i_rd_en change only at rising edges of their respective clocks. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-10.6.2-10 |  | Neither o_empty nor o_full may be early; flags are pessimistic. | CHK-006:PASS | — | **VERIFIED** |
| AF-10.6.2-11 |  | o_overflow and o_underflow are registered, one cycle wide, and return to 0 by themselves. | CHK-002:PASS, CHK-008:PASS | — | **VERIFIED** |
| AF-10.6.3-01 |  | Both storage configurations give the same waveforms at every port, and the macro returns the old word when read and write of the same address occur at the same edge. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-10.6.3-03 |  | o_rd_data is never X when a read is accepted. | CHK-005:PASS | — | **VERIFIED** |
| AF-10.6.4-01 |  | Each synchronized bit independently gets a seed-chosen extra delay of 0, 1 or 2 destination cycles. | CHK-015:NOT_VERIFIABLE | 85.7 % (6/7) | **NOT_PROVEN** |
| AF-10.6.4-02 |  | The model output equals the plain chain output. | CHK-015:NOT_VERIFIABLE | 100.0 % (1/1) | **NOT_PROVEN** |
| AF-10.6.4-03 |  | The pending value is replaced by the new input value and the delay restarts. | not verified: not_observable_at_interface | 100.0 % (1/1) | **NOT_VERIFIED_BY_SIM** |
| AF-10.6.4-05 |  | Different bits of the same signal can get different delays. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AF-10.6.4-06 |  | The replacement can make a short pulse disappear on the model output. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AF-10.6.5-03 |  | A word is accepted at every read edge, o_empty stays 0 until the last word is read, and o_rd_data steps through consecutive words in write order. | CHK-019:PASS | — | **VERIFIED** |
| AF-10.6.5-04 |  | A word is accepted at every write edge during the burst and o_full stays 0 for the whole burst. | CHK-019:PASS | — | **VERIFIED** |
| AF-10.6.5-06 |  | Both Gray pointers change by one bit at every edge, and pointer wrap from 15 to 0 with storage address wrap from 7 to 0 has no effect on flow. | CHK-019:PASS | — | **VERIFIED** |
| AF-10.6.5-07 |  | No o_overflow or o_underflow pulse occurs during the burst. | CHK-019:PASS | — | **VERIFIED** |
| AF-10.7-01 |  | The software reset returns the FIFO to the empty state without a hardware reset. | CHK-025:FAIL | — | **FAILED** |
| AF-10.7.1-01 |  | Writes are blocked from the cycle in which i_rst_n_sw = 0, combinationally with zero latency. | CHK-009:PASS | — | **VERIFIED** |
| AF-10.7.1-02 |  | The write reset FSM raises req_wr at the next write edge, and it crosses to the read domain. | CHK-010:PASS, CHK-025:FAIL | — | **FAILED** |
| AF-10.7.1-03 |  | When the synchronized request is 1, reads are blocked (rd_blk) and o_empty = 1. | CHK-025:FAIL | 100.0 % (1/1) | **FAILED** |
| AF-10.7.1-04 |  | The read reset FSM resets the read pointer to 0 and then raises ack_rd, which crosses to the write domain. | CHK-025:FAIL | 100.0 % (1/1) | **FAILED** |
| AF-10.7.1-05 |  | The write pointer is reset only after the acknowledge is seen, never before the read side has stopped using the old pointer. | CHK-025:FAIL, CHK-029:NOT_VERIFIABLE | — | **FAILED** |
| AF-10.7.1-06 |  | The write FSM holds, with writes blocked, until i_rst_n_sw = 1. | CHK-025:FAIL | — | **FAILED** |
| AF-10.7.1-07 |  | The write side drops the request, the read side drops the acknowledge, and each side leaves reset only when its synchronized copy of the other pointer is 0. | CHK-025:FAIL | — | **FAILED** |
| AF-10.7.1-08 |  | The read side leaves reset first; the write side leaves last, after the synchronized acknowledge is 0. | CHK-027:PASS | 100.0 % (2/2) | **VERIFIED** |
| AF-10.7.1-09 |  | Words in the FIFO are discarded, and the storage is not cleared. | CHK-025:FAIL | — | **FAILED** |
| AF-10.7.2-01 |  | A write is accepted only when i_wr_en is 1, wr_blk is 0 and the normal full condition is false. | CHK-005:PASS, CHK-009:PASS | — | **VERIFIED** |
| AF-10.7.2-02 |  | A read is accepted only when i_rd_en is 1, rd_blk is 0 and the normal empty condition is false. | CHK-025:FAIL | — | **FAILED** |
| AF-10.7.2-03 |  | o_full is 1 while wr_blk; otherwise it is the normal full condition. | CHK-009:PASS | — | **VERIFIED** |
| AF-10.7.2-04 |  | o_full_thr and o_empty_thr take the values of an empty FIFO while blocked; otherwise normal. | CHK-003:FAIL, CHK-009:PASS | 100.0 % (3/3) | **FAILED** |
| AF-10.7.2-05 |  | No o_overflow or o_underflow pulse is generated for an access blocked by the software reset. | CHK-008:PASS | — | **VERIFIED** |
| AF-10.7.2-06 |  | o_sw_rst_busy is set when the write FSM leaves RUN and cleared on return to RUN, equal to write FSM not in RUN at every clock edge. | CHK-010:PASS, CHK-011:PASS | — | **VERIFIED** |
| AF-10.7.3-01 |  | The read side must not be released until the synchronized write pointer is 0, so no nonexistent word is read; likewise for the write side and full flag. | CHK-025:FAIL, CHK-029:NOT_VERIFIABLE | — | **FAILED** |
| AF-10.7.4-01 |  | Write interface inputs i_wr_en, i_wr_data and the software reset i_rst_n_sw change only at a rising edge of i_clk_wr. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-10.7.4-06 |  | Writes stay blocked throughout the sequence, including after i_rst_n_sw is released; the write pointer does not move and storage is not written. | CHK-025:FAIL | 100.0 % (2/2) | **FAILED** |
| AF-10.7.4-07 |  | Reads are blocked: i_rd_en is not accepted, o_empty = 1 and o_empty_thr = 1 in the same cycle. | CHK-025:FAIL | 100.0 % (1/1) | **FAILED** |
| AF-10.7.4-08 |  | Reads accepted before the request reaches the read domain are normal reads returning valid pre-reset words. | CHK-005:PASS, CHK-025:FAIL | 100.0 % (1/1) | **FAILED** |
| AF-10.7.4-09 |  | The read pointer is reset before ack_rd rises. | CHK-025:FAIL | 100.0 % (1/1) | **FAILED** |
| AF-10.7.4-11 |  | The write FSM waits in HOLD for i_rst_n_sw = 1, and passes HOLD without waiting if the input is already 1. | CHK-025:FAIL, CHK-027:PASS | 100.0 % (2/2) | **FAILED** |
| AF-10.7.4-12 |  | The write FSM drops the request req_wr to 0 after release of i_rst_n_sw. | CHK-025:FAIL | 100.0 % (1/1) | **FAILED** |
| AF-10.7.4-14 |  | Writes are unblocked, o_full = 0, o_full_thr is normal and o_sw_rst_busy = 0. | CHK-011:PASS, CHK-025:FAIL | 100.0 % (4/4) | **FAILED** |
| AF-10.7.4-15 |  | The first write after the reset is accepted; o_empty and o_empty_thr fall only after the write pointer has crossed to the read domain. | CHK-025:FAIL | — | **FAILED** |
| AF-10.7.4-16 |  | o_overflow does not pulse for a blocked write access. | CHK-008:PASS | — | **VERIFIED** |
| AF-10.7.4-17 |  | A read request on an empty FIFO after the read release is not blocked and o_underflow pulses once. | CHK-027:PASS | 100.0 % (2/2) | **VERIFIED** |
| AF-10.7.4-18 |  | o_overflow pulses, registered one cycle after the rejected write request. | CHK-008:PASS, CHK-026:PASS | — | **VERIFIED** |
| AF-10.7.4-19 |  | The write FSM latches the request at the first write edge, so a one-cycle low pulse on i_rst_n_sw completes the full sequence. | CHK-026:PASS | — | **VERIFIED** |
| AF-10.7.4-20 |  | o_full stays 1 during the whole reset and falls at the write release; o_full_thr follows the empty-FIFO value while blocked. | CHK-009:PASS, CHK-026:PASS | — | **VERIFIED** |
| AF-10.7.4-21 |  | Writes are blocked whenever i_rst_n_sw is 0, including in REL and the cycle reaching RUN; no write is accepted between sequences. | CHK-009:PASS, CHK-028:PASS | — | **VERIFIED** |
| AF-10.7.4-22 |  | A second sequence starts at once after the first and completes the same way; o_sw_rst_busy falls for one write-clock cycle between them while o_full stays 1. | CHK-028:PASS | — | **VERIFIED** |
| AF-10.7.4-23 |  | The testbench keeps traffic idle until both domains are out of reset. | CHK-022:PASS | — | **VERIFIED** |
| AF-10.7.4-24 |  | Both FSMs, both pointers and both request and acknowledge synchronizers go to reset values at once, whatever the handshake state (hardware reset priority). | CHK-023:PASS | — | **VERIFIED** |
| AF-10.7.4-25 |  | After release the FIFO is empty (o_empty = 1, o_full = 0, pointers 0, FSMs in RUN) and works normally. | CHK-023:PASS | 0.0 % (0/1) **below** | **VERIFIED** |
| AF-10.7.5-02 |  | While i_rst_n_sw stays low, the write FSM waits in HOLD and writes stay blocked, while the read side is released. | CHK-025:FAIL | 100.0 % (1/1) | **FAILED** |
| AF-10.7.5-04 |  | The read is accepted as a normal read of pre-reset data, and the word is discarded by the reset. | CHK-005:PASS, CHK-025:FAIL | — | **FAILED** |
| AF-10.7.5-05 |  | The write must be rejected because the write block is combinational from i_rst_n_sw. | CHK-009:PASS, CHK-026:PASS | — | **VERIFIED** |
| AF-10.7.5-06 |  | The access must be rejected without an error pulse; a read of the empty FIFO right after the read release gives a normal underflow pulse. | CHK-025:FAIL, CHK-027:PASS | 100.0 % (2/2) | **FAILED** |
| AF-10.7.5-07 |  | Storage content is not cleared by the software reset; o_rd_data shows the word at address 0 while the FIFO is empty. | CHK-025:FAIL | 100.0 % (1/1) | **FAILED** |
| AF-10.7.5-09 |  | The handshake waits until the clock runs again. | CHK-031:PASS | — | **VERIFIED** |
| AF-10.7.5-10 |  | The four-phase handshake is level based so longer delay only lengthens the sequence, and the multi-bit pointers are protected by the flush check. | CHK-029:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AF-10.7.5-11 |  | Threshold flags show empty-FIFO values: o_full_thr = 0 for i_full_thr > 0 and o_empty_thr = 1. | CHK-003:FAIL, CHK-009:PASS, CHK-025:FAIL | 100.0 % (3/3) | **FAILED** |
| AF-10.7.6-01 |  | o_sw_rst_busy equals 'write FSM not in RUN' at every write-clock edge. | CHK-010:PASS | — | **VERIFIED** |
| AF-10.7.6-02 |  | No write is accepted while wr_blk is active. | CHK-009:PASS | — | **VERIFIED** |
| AF-10.7.6-03 |  | No read is accepted while rd_blk is active. | CHK-025:FAIL | — | **FAILED** |
| AF-10.7.6-04 |  | o_full is 1 and o_full_thr has the value of an empty FIFO while the write side is blocked. | CHK-009:PASS | — | **VERIFIED** |
| AF-10.7.6-05 |  | o_empty is 1 and o_empty_thr is 1 while the read side is blocked. | CHK-003:FAIL, CHK-025:FAIL | 100.0 % (1/1) | **FAILED** |
| AF-10.7.6-06 |  | No read returns a word that was never written, and data of every accepted read equals the written word. | CHK-005:PASS | — | **VERIFIED** |
| AF-10.7.6-07 |  | At each release the own pointer and the synchronized pointer of the other side are 0. | CHK-025:FAIL | — | **FAILED** |
| AF-10.7.6-08 |  | The read release is before the write release and after the request; o_empty = 1 while both pointers are 0 after the read release. | CHK-027:PASS | — | **VERIFIED** |
| AF-10.7.7-01 | REQ-SRST-018 | o_sw_rst_busy is driven directly by flip-flop reg_sw_rst_busy, changes only at a rising edge of i_clk_wr and never glitches. | CHK-012:PASS | — | **VERIFIED** |
| AF-10.7.7-02 |  | o_sw_rst_busy is 0 in RUN and 1 in REQ, PTR, HOLD and REL; FSM follows RUN, REQ, PTR, HOLD, REL, RUN with stated entry conditions and req_wr set in REQ. | CHK-010:PASS, CHK-025:FAIL | — | **FAILED** |
| AF-10.7.7-03 |  | wr_blk follows i_rst_n_sw in the same cycle; o_sw_rst_busy rises at the first write-clock edge after i_rst_n_sw falls. | CHK-009:PASS, CHK-010:PASS | — | **VERIFIED** |
| AF-10.7.7-04 |  | o_sw_rst_busy rises at the same edge as req_wr. | CHK-025:FAIL | 100.0 % (1/1) | **FAILED** |
| AF-10.7.7-05 |  | o_sw_rst_busy stays 1 when i_rst_n_sw returns to 1 (HOLD, REL). | CHK-011:PASS, CHK-025:FAIL | 100.0 % (3/3) | **FAILED** |
| AF-10.7.7-06 |  | o_sw_rst_busy does not follow the read FSM; it falls only when the write side is released, after the read side. | CHK-027:PASS | — | **VERIFIED** |
| AF-10.7.7-07 |  | o_sw_rst_busy, wr_blk and o_full fall at the same edge where the write FSM returns to RUN. | CHK-011:PASS | — | **VERIFIED** |
| AF-10.7.7-08 |  | wr_blk equals o_sw_rst_busy OR (i_rst_n_sw = 0). | CHK-009:PASS | — | **VERIFIED** |
| AF-10.7.7-09 |  | A hardware reset of the write domain clears o_sw_rst_busy asynchronously. | CHK-007:PASS, CHK-023:PASS | 100.0 % (2/2) | **VERIFIED** |
| AF-10.7.7-10 |  | o_sw_rst_busy falls for exactly one write-clock cycle between the two sequences, and writes stay blocked during the gap. | CHK-010:PASS, CHK-028:PASS | — | **VERIFIED** |
| AF-10.7.7-12 |  | A read-domain consumer needing o_sw_rst_busy shall synchronize it itself, or use o_empty, since the IP has no synchronizer for it. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-11-02 |  | Overflow and underflow indications are 1-cycle pulses, with no sticky status register retaining them. | CHK-002:PASS, CHK-008:PASS | — | **VERIFIED** |
| AF-11.2-01 |  | The owner of the i_rst_n_sw control register stops the producer before the reset if the producer should not lose words. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| AF-11.2-02 |  | The owner of the control register drives i_rst_n_sw to 0 for at least one write-clock cycle; it may be held longer. | CHK-026:PASS | — | **VERIFIED** |
| AF-11.2-03 |  | The owner of the control register drives i_rst_n_sw back to 1 after the reset has started. | CHK-025:FAIL, CHK-026:PASS | — | **FAILED** |
| AF-11.2-04 |  | The FIFO is usable again on both sides when o_sw_rst_busy is 0 and i_rst_n_sw is 1. | CHK-025:FAIL | — | **FAILED** |
| AF-11.2-07 |  | Software must not use o_sw_rst_busy = 0 alone as the usable indication while i_rst_n_sw is held at 0, since it is 0 for one write-clock cycle after i_rst_n_sw falls and between sequences while writes are blocked. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| AF-11.2-08 |  | The words in the FIFO at the reset are lost. | CHK-025:FAIL | — | **FAILED** |
| AF-12-01 |  | The FIFO must pulse o_overflow for one cycle, registered, in the cycle after a rejected write request when i_wr_en = 1 while full. | CHK-008:PASS | — | **VERIFIED** |
| AF-12-02 |  | The write must be dropped: storage and write pointer remain unchanged. | CHK-020:PASS | — | **VERIFIED** |
| AF-12-03 |  | o_overflow must self-clear after one cycle and must be cleared by i_rst_n_wr. | CHK-007:PASS, CHK-008:PASS | 100.0 % (2/2) | **VERIFIED** |
| AF-12-04 |  | The FIFO must pulse o_underflow for one cycle, registered, in the cycle after a rejected read request when i_rd_en = 1 while empty. | CHK-002:PASS | — | **VERIFIED** |
| AF-12-05 |  | The read pointer must remain unchanged and o_rd_data must still show the word at the read pointer. | CHK-021:PASS | — | **VERIFIED** |
| AF-12-06 |  | o_underflow must self-clear after one cycle and must be cleared by i_rst_n_rd. | CHK-001:PASS, CHK-002:PASS | 100.0 % (2/2) | **VERIFIED** |
| AF-12-07 |  | The integrator must reset both domains; reset asserted in one domain only leaves inconsistent FIFO state that the IP does not detect. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| AF-12-08 |  | The IP does not detect illegal parameters and behavior is undefined; the configuration must be fixed, so illegal parameters must not be used. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-12-09 |  | The access must not be accepted and no o_overflow or o_underflow pulse must be generated. | CHK-008:PASS, CHK-025:FAIL | — | **FAILED** |
| AF-12-10 |  | The new i_rst_n_sw request must be ignored until the write FSM is back in RUN; a new sequence then starts if i_rst_n_sw is still 0. | CHK-028:PASS | — | **VERIFIED** |
| AF-12-13 |  | No retry or drain is provided by the FIFO; the producer or consumer must react to the o_overflow and o_underflow flags. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| AF-13-01 |  | Flag latency across the crossing must be S destination clock edges when flags are combinational from the synchronized pointer, and up to S+2 edges with the metastability model. | CHK-014:PASS, CHK-015:NOT_VERIFIABLE | — | **PARTIAL** |
| AF-14.1-01 |  | The RTL shall comply with REF-003, which is the mandatory RTL authority. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-14.1-02 |  | Synchronizer flip-flops and technology cells shall exist only in m_vlsit_afifo_cell_sync. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-14.1-04 |  | The memory macro shall exist only in m_vlsit_afifo_ram_macro. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-14.1-05 | REQ-RTL-002 | These flows shall define the macro VLSIT_SYNTHESIS. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-14.1-07 |  | VLSIT_SYNTHESIS shall select branches only in m_vlsit_afifo_cell_sync; m_vlsit_afifo_ram_macro has no branch and always instantiates VLSIT_CELL_SRAM_1W1R. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-14.1-08 |  | The flag, Gray register and pointer registers shall be one-process-per-state elements with separate next-state logic. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-14.1-09 | REQ-FUNC-011 | The software reset FSMs shall be one-process-per-state with separate next-state logic, REF-003 FSM naming, and reside in m_vlsit_afifo_wr and m_vlsit_afifo_rd. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-14.1-10 | REQ-SRST-018 | Request and acknowledge synchronizers shall be m_vlsit_afifo_sync instances with PARA_AFIFO_SYNC_W = 1. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-14.1-11 | REQ-SRST-018 | o_sw_rst_busy shall be the output of its own flip-flop reg_sw_rst_busy, not a decode of the FSM state. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-14.1-12 |  | Names in m_vlsit_afifo_* modules shall use REF-003 NAM-08 abbreviations and be at most 30 characters. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-14.2-01 |  | Library wrappers and example cells shall be in common_rtl/000_Common, and each folder shall have its own filelist.f. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-14.2-02 |  | Instance names shall be u_ followed by the module name with m_ removed; names over 30 characters shall shorten the function part with NAM-08. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-14.2-03 |  | The top shall have no logic; state is owned by m_vlsit_afifo_wr and m_vlsit_afifo_rd. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-14.4-01 |  | m_vlsit_afifo_sync shall instantiate PARA_AFIFO_SYNC_W cell wrappers, one per bit, with PARA_AFIFO_CELL_TYPE and the bit's reset flavour, in both VLSIT_SYNTHESIS branches, and nothing else. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-14.4-02 |  | Input bit i_data[i] shall connect to i_d and o_q shall be o_data[i]. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-14.4-03 |  | Option 0 is a bypass (o_q = i_d, 0 stages); options 1 and 2 give 2 stages, option 3 gives 3, option 4 gives 4, with metastability-model chains in simulation. | CHK-014:PASS | 100.0 % (1/1) | **VERIFIED** |
| AF-14.4-04 |  | PARA_AFIFO_CELL_TYPE above 4 shall not be used; the wrapper gives the option 4 cell and behavior is undefined. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-14.4-05 |  | Every flop of a synchronizer model shall reset to the reset value bit. | CHK-022:PASS | — | **VERIFIED** |
| AF-14.4-06 |  | Option 0 shall not be used for the pointer crossings of this IP because it breaks the read margin of at least 2 destination edges. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-14.4-07 |  | The latencies of Section 10.3 and read margin of Section 10.4 shall hold for options 1 to 4. | CHK-014:PASS, CHK-015:NOT_VERIFIABLE | 100.0 % (2/2) | **PARTIAL** |
| AF-14.4-08 | REQ-RTL-003 | The synthesis branch shall instantiate the cells of 000_Common/rtl_cells named u_dont_touch_. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-14.4-09 | REQ-VER-001 | The simulation branch shall not use the example cells and shall contain the metastability model with random extra latency of REQ-VER-001. | CHK-015:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AF-14.4-10 |  | The synthesis branch shall be verified with VLSIT_SYNTHESIS defined per option, and the simulation branch alone per option (latency 0, 2, 2, 3, 4 and reset value). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-15.1-01 |  | Seeds must be logged for every random run, and every failing seed shall be reproducible. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| AF-15.2-01 | REQ-RESET-001, REQ-RESET-002 | After reset release, empty = 1, full = 0, flags are clear and pointers are 0. | CHK-022:PASS | — | **VERIFIED** |
| AF-15.2-02 | REQ-FUNC-003, REQ-FUNC-004, REQ-FUNC-005, REQ-FUNC-017 | o_rd_data must equal the head word before every read; data returns the same, in the same order, show-ahead. | CHK-018:PASS | — | **VERIFIED** |
| AF-15.2-03 | REQ-ERR-001, REQ-FUNC-008 | When full = 1 and writing continues, overflow is raised and no data or pointer changes. | CHK-020:PASS | — | **VERIFIED** |
| AF-15.2-04 | REQ-ERR-002, REQ-FUNC-009 | When empty = 1 and reading continues, underflow is raised and the pointer is unchanged. | CHK-021:PASS | — | **VERIFIED** |
| AF-15.2-05 | REQ-FUNC-010 | Threshold flags must behave per REQ-FUNC-010 for several i_full_thr and i_empty_thr values. | CHK-032:PASS | — | **VERIFIED** |
| AF-15.2-06 | REQ-CLK-001, REQ-FUNC-001 | With random clock ratios (write faster, read faster, equal, drift) there must be no data error and no flag error. | CHK-016:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AF-15.2-07 | REQ-FUNC-013 | Flag latency must equal S destination clock edges. | CHK-014:PASS | 100.0 % (2/2) | **VERIFIED** |
| AF-15.2-08 | REQ-VER-001 | Each bit output changes at edge S, S+1 or S+2; there is no data error and flags are never optimistic. | CHK-015:NOT_VERIFIABLE | 80.0 % (4/5) **below** | **NOT_PROVEN** |
| AF-15.2-09 | REQ-FUNC-014, REQ-VER-003 | FIFO behaves as the RTL branch; wrapper alone for options 0 to 4 has latency 0, 2, 2, 3, 4 and the listed reset value. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-15.2-10 | REQ-FUNC-016, REQ-VER-002 | Behavior must be the same as the RTL array. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-15.2-13 | REQ-FUNC-003 | Same-cycle write and read, and pointer wrap-around, must cause no error. | CHK-016:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AF-15.2-14 | REQ-RESET-002 | The FIFO must restart cleanly. | CHK-024:PASS | — | **VERIFIED** |
| AF-15.2-19 | REQ-RTL-002, REQ-VER-001 | With the macro the synthesizable branch runs and passes the full regression; without it the model runs. | CHK-017:PASS | 100.0 % (1/1) | **VERIFIED** |
| AF-15.2-20 | REQ-SRST-001 | Handshake order is respected; after release pointers are 0, empty = 1, full = 0, and read is released before write. | CHK-025:FAIL, CHK-026:PASS, CHK-027:PASS | — | **FAILED** |
| AF-15.2-21 | REQ-SRST-003, REQ-SRST-008, REQ-SRST-013, REQ-SRST-017 | No access is accepted while blocked, no data error and no deadlock occur. | CHK-029:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AF-15.2-22 | REQ-SRST-013, REQ-VER-001 | The sequence completes and the flush check is never violated. | CHK-029:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AF-15.2-23 | REQ-RESET-002, REQ-SRST-012, REQ-SRST-014 | Behavior in TEST-002 to TEST-004 must be the same as after a hardware reset. | CHK-030:PASS | — | **VERIFIED** |
| AF-15.2-24 | REQ-SRST-015, REQ-SRST-016 | Behavior must follow DEC-031 and DEC-032. | CHK-023:PASS, CHK-028:PASS | — | **VERIFIED** |
| AF-15.3-02 |  | Full and empty are never both 1. | CHK-016:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AF-15.3-03 | REQ-FUNC-002 | A Gray pointer register changes at most one bit per cycle. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AF-15.3-04 | REQ-ERR-001 | The write pointer and storage remain unchanged. | CHK-020:PASS | — | **VERIFIED** |
| AF-15.3-05 | REQ-CLK-003, REQ-FUNC-003 | The read returns the word written to that entry, with no scoreboard mismatch. | CHK-005:PASS | — | **VERIFIED** |
| AF-15.3-06 | REQ-FUNC-008, REQ-FUNC-009 | Full flag is never 0 when physically full; empty flag is never 0 when physically empty. | CHK-006:PASS | — | **VERIFIED** |
| AF-15.3-07 | REQ-ERR-002 | The read pointer remains unchanged. | CHK-021:PASS | — | **VERIFIED** |
| AF-15.3-08 | REQ-SRST-008 | No write is accepted while wr_blk = 1. | CHK-009:PASS | — | **VERIFIED** |
| AF-15.3-09 | REQ-SRST-003 | No read is accepted while rd_blk = 1. | CHK-025:FAIL, CHK-029:NOT_VERIFIABLE | — | **FAILED** |
| AF-15.3-10 | REQ-SRST-005 | ack_rd rises only when the read pointer is 0 and the read FSM is not in RUN. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AF-15.3-11 | REQ-SRST-009 | req_wr falls only after the acknowledge was seen and i_rst_n_sw = 1; ack_rd falls only after the synchronized request is 0. | CHK-025:FAIL | — | **FAILED** |
| AF-15.3-12 | REQ-SRST-010 | The read pointer and synchronized write pointer are 0. | CHK-011:PASS, CHK-025:FAIL | 100.0 % (3/3) | **FAILED** |
| AF-15.3-13 | REQ-SRST-010 | The write pointer and synchronized read pointer are 0. | CHK-027:PASS | — | **VERIFIED** |
| AF-15.3-14 | REQ-SRST-011 | The read FSM returns to RUN before the write FSM. | CHK-027:PASS, CHK-029:NOT_VERIFIABLE | — | **PARTIAL** |
| AF-15.3-15 | REQ-SRST-013 | Both FSMs return to RUN within a bounded number of cycles. | CHK-025:FAIL, CHK-029:NOT_VERIFIABLE | — | **FAILED** |
| AF-15.3-16 | REQ-SRST-018 | o_sw_rst_busy equals (write FSM not in RUN) and is 0 after hardware reset. | CHK-007:PASS, CHK-010:PASS | — | **VERIFIED** |
| AF-15.3-17 | REQ-SRST-018 | Write block equals o_sw_rst_busy OR (i_rst_n_sw = 0); o_sw_rst_busy rises only at RUN to REQ and falls only at REL to RUN. | CHK-009:PASS, CHK-010:PASS, CHK-011:PASS | 100.0 % (1/1) | **VERIFIED** |
| AF-15.3-19 |  | A read is accepted only when empty = 0. | CHK-006:PASS | — | **VERIFIED** |
| AF-16-02 |  | The RTL must not contain any latch, combinational loop, internal tri-state, or clock gate, so SoC scan insertion remains possible. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-17.1-01 |  | The IP owns the timing constraints of the crossings EXC-001..003, EXC-005 and EXC-006. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-17.1-02 |  | The SoC owns the clock definitions and I/O delays; the IP does not specify them. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-17.1.1-01 |  | i_clk_wr and i_clk_rd are primary clocks, asynchronous to each other for functional paths except the listed exceptions, with no frequency or ratio restriction. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-17.1.3-01 |  | EXC-001: set_max_delay -datapath_only from write Gray pointer registers to first synchronizer stage D pins in m_vlsit_afifo_rd must be 0.9 x i_clk_wr period. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-17.1.3-02 |  | EXC-002: set_max_delay -datapath_only from read Gray pointer registers to first synchronizer stage D pins in m_vlsit_afifo_wr must be 0.9 x i_clk_rd period. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-17.1.3-03 |  | EXC-003: set_max_delay -datapath_only from storage elements or macro output through the read path to storage output register D pins must be at most 1 x i_clk_rd period. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-17.1.3-04 |  | EXC-004: i_full_thr and i_empty_thr are set_false_path static configuration inputs, written once before use and not changed while the FIFO is in use. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-17.1.3-06 |  | EXC-006: set_max_delay -datapath_only from ack_rd register to first stage D pin of the acknowledge synchronizer in m_vlsit_afifo_wr must be 0.9 x i_clk_rd period. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-17.1.3-07 |  | Do not use a whole-domain set_false_path or unqualified set_clock_groups -asynchronous for the two clocks, as it hides the crossings from bounded-delay checks. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-17.1.3-08 |  | The bounded-delay constraints and the CDC analysis shall cover the crossings separately. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-17.2-02 |  | The synchronizer stages of one bit should be placed adjacent to each other. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-17.2-03 |  | dont_touch is applied to the synchronizer instances so the flow does not restructure them. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-18-02 |  | Diagnostics are limited to overflow and underflow flags; recovery is performed by the user logic or by reset. | CHK-020:PASS, CHK-021:PASS | — | **VERIFIED** |
| AF-18-03 |  | The number of synchronizer stages S must be configurable as 2, 3 or 4, with a technology cell option. | CHK-014:PASS | — | **VERIFIED** |
| AF-20.1-01 | REQ-RESET-001 | Both write-domain and read-domain resets are assumed already synchronized to their respective clocks externally; the IP contains no reset synchronizer. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.1-02 |  | The write and read clocks are assumed to be asynchronous to each other. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.1-03 |  | The pointer protocol keeps the read data stable, which the CDC waiver and EXC-003 rely on. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.1-05 |  | No FIFO operation (write or read) starts before both write and read domains have left reset. | CHK-022:PASS | — | **VERIFIED** |
| AF-20.1-06 |  | Both clocks run during the whole software reset; if a clock stops, the handshake waits until it runs again, with no timeout. | CHK-031:PASS | — | **VERIFIED** |
| AF-20.2-01 | REQ-VER-001 | The metastability model is a simulation-only SystemVerilog model, not bound by the RTL rules, and must never be used for synthesis. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-02 | REQ-PARAM-003 | The RTL contains no elaboration check for parameter values; behavior with an illegal parameter value is undefined. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-03 |  | Defaults are 2 synchronizer stages, depth 8, data width 32; depth is a power of 2 with no upper limit, data width minimum 1 with no upper limit. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-04 | REQ-FUNC-017 | o_rd_data must always show the word at the current read pointer (show-ahead read), including while empty; there is no o_rd_valid. | CHK-005:PASS, CHK-021:PASS | — | **VERIFIED** |
| AF-20.2-05 | REQ-FUNC-010 | o_full_thr must be 1 when occupancy >= i_full_thr; all i_full_thr values are accepted with no legal-range restriction. | CHK-013:FAIL, CHK-032:PASS | — | **FAILED** |
| AF-20.2-06 | REQ-FUNC-010 | o_empty_thr must be 1 when occupancy <= i_empty_thr; all i_empty_thr values are accepted with no legal-range restriction. | CHK-003:FAIL, CHK-032:PASS | — | **FAILED** |
| AF-20.2-07 | REQ-FUNC-010 | The threshold inputs i_full_thr and i_empty_thr are static, written once before use. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-08 |  | o_overflow and o_underflow must be registered 1-cycle pulses appearing in the cycle after the rejected request. | CHK-002:PASS, CHK-008:PASS | — | **VERIFIED** |
| AF-20.2-09 |  | An underflow read must not change the read pointer, and o_rd_data keeps showing the word at the read pointer. | CHK-021:PASS | — | **VERIFIED** |
| AF-20.2-10 |  | The write and read domain resets (asynchronous assert, active low) need not be asserted at the same time, and clock frequencies and ratio are unrestricted. | CHK-022:PASS | — | **VERIFIED** |
| AF-20.2-11 |  | Each synchronizer bit has its own reset value (vector). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-12 | REQ-VER-001 | The model randomizes each bit's latency independently as S-1, S or S+1 cycles after the first capturing edge; a new input change during the delay replaces the pending change and restarts the delay. | CHK-015:NOT_VERIFIABLE | 66.7 % (2/3) **below** | **NOT_PROVEN** |
| AF-20.2-13 | REQ-VER-001 | The metastability model is controlled by plusargs for seed and enable. | CHK-015:NOT_VERIFIABLE | 66.7 % (2/3) **below** | **NOT_PROVEN** |
| AF-20.2-14 | REQ-VER-002 | The SRAM wrapper and model implement a generic one-write-port, one-read-port foundry-style interface. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-15 | REQ-CLK-004, REQ-FUNC-011, REQ-FUNC-015 | The FIFO array is a separate module modelled as a one-write, one-read SRAM, and the top instantiates the write module, read module and array module. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-16 | REQ-FUNC-018 | The full, empty and threshold flags must be combinational from the synchronized pointers. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-17 |  | Timing exceptions: set_max_delay 0.9 x write clock period for the write pointer, 0.9 x read clock period for the read pointer, 1 x read clock period for the data path; static thresholds use a false path; no set_min_delay. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-18 | REQ-RTL-002, REQ-VER-001, REQ-VER-002, REQ-VER-003 | The macro VLSIT_SYNTHESIS selects branches only in m_vlsit_afifo_cell_sync: with the macro is the synthesizable model, without is the simulation model; simulation defines it for the synthesizable branch, synthesis and analysis flows define it. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-19 | REQ-FUNC-017 | Storage read is synchronous: the read module drives the next read pointer address, storage is read every read-clock cycle, o_rd_data is the storage output, with no memory read enable. | CHK-021:PASS | — | **VERIFIED** |
| AF-20.2-20 | REQ-SRST-001 | The software reset input i_rst_n_sw is active-low level (0 = reset requested), idle value 1, synchronous to i_clk_wr and sampled at the clock, not an asynchronous reset. | CHK-010:PASS, CHK-026:PASS | — | **VERIFIED** |
| AF-20.2-21 | REQ-SRST-001, REQ-SRST-013 | i_rst_n_sw may be low for one write-clock cycle or any longer time; the FSM latches the request and waits in HOLD while it is low. | CHK-025:FAIL, CHK-026:PASS | — | **FAILED** |
| AF-20.2-22 | REQ-SRST-001, REQ-SRST-013 | o_sw_rst_busy must be driven directly by a flip-flop with no combinational logic on the output path. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-23 | REQ-SRST-017 | o_full must be 1 while the write side is blocked by the software reset and return to normal full logic at write release. | CHK-009:PASS, CHK-011:PASS | — | **VERIFIED** |
| AF-20.2-24 | REQ-SRST-017 | A write or read blocked by the software reset must not raise an o_overflow or o_underflow pulse. | CHK-008:PASS, CHK-025:FAIL | — | **FAILED** |
| AF-20.2-25 | REQ-SRST-017 | While blocked, o_full_thr and o_empty_thr must take the values of an empty FIFO. | CHK-003:FAIL, CHK-009:PASS | 100.0 % (1/1) | **FAILED** |
| AF-20.2-26 | REQ-SRST-008 | The write block is combinational (zero latency) from i_rst_n_sw and the FSM state, adding a combinational path to write accept and memory write enable. | CHK-009:PASS | — | **VERIFIED** |
| AF-20.2-27 | REQ-SRST-015 | Hardware resets have priority over the software reset; a hardware reset of one domain only during the sequence is not repaired. | CHK-023:PASS | — | **VERIFIED** |
| AF-20.2-28 | REQ-SRST-016 | Writes stay blocked and a new sequence starts when the FSM is back in RUN. | CHK-028:PASS | — | **VERIFIED** |
| AF-20.2-29 |  | The request and acknowledge crossings use set_max_delay of 0.9 x the source clock period. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-30 | REQ-SRST-010 | A side is released only when the synchronized pointer of the other side is 0. | CHK-025:FAIL | — | **FAILED** |
| AF-20.2-31 | REQ-SRST-014 | The software reset must not clear the storage; only pointers and flags are reset. | CHK-025:FAIL | — | **FAILED** |
| AF-20.2-33 | REQ-FUNC-013, REQ-FUNC-014, REQ-VER-003 | PARA_AFIFO_CELL_TYPE selects the cell: 0 bypass, 1 two D-FF cells, 2 one 2-FF cell, 3 one 3-FF cell, 4 one 4-FF cell; above 4 gives the 4-FF cell; default 2. | CHK-014:PASS | — | **VERIFIED** |
| AF-20.2-34 | REQ-FUNC-014, REQ-VER-003 | Option 0 (bypass) is not legal for the pointer crossings. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-35 | REQ-FUNC-013, REQ-FUNC-014, REQ-RTL-003, REQ-VER-001 | The metastability model lives only in the simulation branch of m_vlsit_afifo_cell_sync; m_vlsit_afifo_sync only instantiates one cell wrapper per bit, and other modules only instantiate m_vlsit_afifo_sync. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-36 | REQ-RTL-003, REQ-VER-001 | Instance names of cells and macros follow u_dont_touch_. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-37 | REQ-VER-003 | Example cell models are synthesizable RTL, one module per file in 000_Common/rtl_cells, with pins CK, RN or SN, D, Q, exempt from the naming rule; the SRAM model stays simulation-only per DEC-040. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-38 | REQ-VER-002 | VLSIT_CELL_SRAM_1W1R is synthesizable RTL with parameters ADDR_W and DATA_W, bit write mask BWEB, read register QR, no reset; a same-edge read of a written address returns the old word. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-39 |  | Library wrappers, cells and macro models are written in common_rtl/000_Common (rtl_lib and rtl_cells), each folder with its own filelist.f. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-40 |  | RTL module port lists are aligned in four columns and declared in functional groups with a comment per group, clock and reset first. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AF-20.2-41 | REQ-VER-003 | Cell and macro models are named VLSIT_CELL_*, and the header states that the model is synthesizable RTL and a real design uses the synthesis-library cell. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |

## Mutants

| ID | File:line | Operator | Status | Caught by | Rules | Equivalent? |
|---|---|---|---|---|---|---|
| M01 | m_vlsit_afifo_mem.sv:52 | negate_if | killed | CHK-005, test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_with_model, test_c | AF-3-04, AF-1.1-02, AF-1.1-01, AF-5.3-01, AF-3-05 |  |
| M02 | m_vlsit_afifo_rd.sv:151 | negate_if | killed | CHK-002, test_chk_016_random_ratios/pair=0, test_chk_016_random_ratios/pair=1, test_chk_016_random_ratios/pair=2, test_c | AF-7.3-02, AF-3-35, AF-3-36, AF-12-06 |  |
| M03 | m_vlsit_afifo_cell_sync.sv:171 | eq_to_ne | killed | test_chk_015_latency_with_model | AF-10.6.4-01, AF-15.2-08, AF-10.3-02, AF-6.2-27 |  |
| M04 | m_vlsit_afifo_rd.sv:118 | one_to_zero | killed | test_chk_025_srst_partial_fifo | AF-3-62, AF-10.7.2-04, AF-10.7.5-11, AF-3-15, AF-6.2-21 |  |
| M05 | m_vlsit_afifo_rd.sv:169 | eq_to_ne | killed | test_chk_017_synthesis_branch_regression, test_chk_025_srst_partial_fifo, test_chk_026_srst_pulse_full_overflow, test_ch | AF-3-54, AF-10.7.4-17, AF-10.7.1-08, AF-10.7.5-06, AF-10.7.4-11 |  |
| M06 | m_vlsit_afifo_cell_sync.sv:140 | ne_to_eq | killed | CHK-013, CHK-003, test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_with_mode | AF-20.2-12, AF-20.2-13, AF-15.2-07, AF-14.4-07 |  |
| M07 | m_vlsit_afifo_wr.sv:185 | and_to_or | killed | CHK-011, CHK-002, test_chk_017_synthesis_branch_regression, test_chk_025_srst_partial_fifo, test_chk_027_read_released_f | AF-10.7.4-14, AF-10.7.7-05, AF-3-53, AF-3-55, AF-15.3-12 |  |
| M08 | m_vlsit_afifo_wr.sv:209 | negate_if | killed | CHK-007, CHK-010, CHK-005, CHK-006, CHK-002, test_chk_017_synthesis_branch_regression, test_chk_023_hw_reset_during_srst | AF-7.3-01, AF-3-35, AF-3-36, AF-12-03, AF-10.7.7-09 |  |
| M09 | m_vlsit_afifo_rd.sv:169 | and_to_or | killed | CHK-011, CHK-005, CHK-006, CHK-002, test_chk_017_synthesis_branch_regression, test_chk_025_srst_partial_fifo, test_chk_0 | AF-3-54, AF-10.7.4-17, AF-10.7.1-08, AF-10.7.5-06, AF-10.7.4-11 |  |
| M10 | m_vlsit_afifo_rd.sv:191 | zero_to_one | survived |  | AF-7.3-02, AF-3-35, AF-10.7.4-25, AF-7.3-07 |  |
| M11 | m_vlsit_afifo_cell_sync.sv:164 | zero_to_one | killed | CHK-005, CHK-006, CHK-002, test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_ | AF-7.3-02, AF-7.3-01, AF-3-35, AF-8-11, AF-10.6.4-01 |  |
| M12 | VLSIT_CELL_SYNC_2FF_RN.sv:36 | negate_if | killed | CHK-001, test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_with_model, test_c | AF-7.3-01, AF-7.3-02, AF-3-35, AF-15.2-19, AF-14.4-03 |  |
| M13 | VLSIT_CELL_SRAM_1W1R.sv:65 | negate_if | killed | CHK-005, test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_with_model, test_c | AF-1.1-02, AF-3-04, AF-6.2-19, AF-5.3-01, AF-8-09 |  |
| M14 | m_vlsit_afifo_wr.sv:134 | one_to_zero | killed | CHK-006, test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_with_model, test_c | AF-3-04, AF-1.1-02, AF-3-10, AF-3-12, AF-5.3-01 |  |
| M15 | m_vlsit_afifo_wr.sv:204 | eq_to_ne | killed | CHK-002, test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_with_model, test_c | AF-3-42, AF-3-44, AF-10.7.1-03, AF-10.7.4-06, AF-10.7.4-07 |  |
| M16 | m_vlsit_afifo_cell_sync.sv:170 | negate_if | killed | CHK-005, CHK-006, CHK-002, test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_ | AF-10.6.4-01, AF-15.2-08, AF-10.3-02, AF-10.6.4-03 |  |
| M17 | m_vlsit_afifo_rd.sv:93 | ne_to_eq | killed | CHK-005, CHK-006, CHK-002, test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_ | AF-3-62, AF-10.7.2-04, AF-10.7.5-11, AF-10.7.6-05, AF-10.7.4-08 |  |
| M18 | m_vlsit_afifo_wr.sv:210 | zero_to_one | killed | CHK-007, CHK-011, test_chk_022_hw_reset_independent, test_chk_023_hw_reset_during_srst, test_chk_024_hw_reset_mid_traffi | AF-7.3-01, AF-3-35, AF-3-36, AF-10.7.7-09, AF-3-64 |  |
| M19 | m_vlsit_afifo_cell_sync.sv:168 | one_to_zero | killed | CHK-005, CHK-006, test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_with_mode | AF-10.6.4-01, AF-15.2-08, AF-10.3-02, AF-6.2-27 |  |
| M20 | VLSIT_CELL_SYNC_2FF_RN.sv:37 | zero_to_one | killed | CHK-007, test_chk_022_hw_reset_independent, test_regression_random | AF-7.3-01, AF-7.3-02, AF-3-35, AF-8-11, AF-8-08 |  |
| M21 | m_vlsit_afifo_rd.sv:164 | negate_if | killed | CHK-011, CHK-006, CHK-002, test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_ | AF-3-44, AF-3-45, AF-10.7.4-06, AF-10.7.1-04, AF-10.7.5-02 |  |
| M22 | m_vlsit_afifo_cell_sync.sv:162 | eq_to_ne | killed | CHK-005, CHK-006, test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_with_mode | AF-10.6.4-01, AF-10.6.4-02, AF-15.2-08, AF-10.3-02 |  |
| M23 | m_vlsit_afifo_rd.sv:126 | one_to_zero | killed | CHK-005, CHK-006, test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_with_mode | AF-3-05, AF-1.1-02, AF-3-26, AF-5.3-04, AF-6.3-01 |  |
| M24 | m_vlsit_afifo_rd.sv:123 | eq_to_ne | killed | CHK-005, CHK-006, test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_with_mode | AF-10.7.4-09, AF-10.7.4-12, AF-3-46, AF-7.3-03, AF-3-56 |  |
| M25 | m_vlsit_afifo_wr.sv:185 | negate_if | killed | CHK-011, CHK-002, test_chk_017_synthesis_branch_regression, test_chk_025_srst_partial_fifo, test_chk_027_read_released_f | AF-10.7.4-14, AF-10.7.7-05, AF-3-53, AF-3-55, AF-15.3-12 |  |
| M26 | m_vlsit_afifo_rd.sv:152 | zero_to_one | killed | CHK-001, test_chk_022_hw_reset_independent, test_chk_023_hw_reset_during_srst, test_chk_024_hw_reset_mid_traffic, test_r | AF-7.3-02, AF-12-06, AF-3-35, AF-3-36, AF-3-41 |  |
| M27 | m_vlsit_afifo_cell_sync.sv:173 | zero_to_one | survived |  |  | claimed: After a pending change is delivered at sim_cnt==0, sim_nxt already equals sim_cur. A leftover pend=1 reloads that same value and sim_cnt stays 0. A new input ch |
| M28 | VLSIT_CELL_SRAM_1W1R.sv:58 | negate_if | killed | CHK-005, test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_with_model, test_c | AF-1.1-01, AF-1.1-02, AF-3-04, AF-5.3-01, AF-8-09 |  |
| M29 | m_vlsit_afifo_wr.sv:185 | eq_to_ne | killed | test_chk_017_synthesis_branch_regression, test_chk_025_srst_partial_fifo, test_chk_026_srst_pulse_full_overflow, test_ch | AF-10.7.4-14, AF-10.7.7-05, AF-3-53, AF-3-55, AF-15.3-12 |  |
| M30 | m_vlsit_afifo_cell_sync.sv:139 | negate_if | killed | CHK-013, CHK-003, test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_with_mode | AF-20.2-12, AF-20.2-13, AF-15.2-07, AF-14.4-07 |  |
| M31 | m_vlsit_afifo_wr.sv:160 | zero_to_one | killed | CHK-007, test_chk_022_hw_reset_independent, test_chk_023_hw_reset_during_srst, test_chk_024_hw_reset_mid_traffic, test_r | AF-7.3-01, AF-12-03, AF-3-35, AF-3-36, AF-3-40 |  |
| M32 | m_vlsit_afifo_cell_sync.sv:136 | one_to_zero | survived |  | AF-20.2-12, AF-20.2-13, AF-10.6.4-01, AF-15.2-08 |  |
| M33 | m_vlsit_afifo_rd.sv:125 | negate_if | killed | CHK-011, CHK-005, CHK-006, test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_ | AF-3-05, AF-1.1-02, AF-3-26, AF-5.3-04, AF-6.3-01 |  |
| M34 | m_vlsit_afifo_wr.sv:181 | negate_if | killed | CHK-011, test_chk_017_synthesis_branch_regression, test_chk_026_srst_pulse_full_overflow, test_chk_027_read_released_fir | AF-3-51, AF-10.7.4-14, AF-10.7.7-04, AF-3-50, AF-10.7.5-07 |  |
| M35 | m_vlsit_afifo_cell_sync.sv:154 | zero_to_one | killed | CHK-005, CHK-006, CHK-002, test_chk_014_nominal_latency/per=1, test_chk_015_latency_with_model, test_chk_016_random_rati | AF-7.3-02, AF-7.3-01, AF-3-35, AF-8-11, AF-10.6.4-01 |  |
| M36 | m_vlsit_afifo_wr.sv:126 | eq_to_ne | killed | CHK-009, CHK-011, test_chk_025_srst_partial_fifo, test_chk_026_srst_pulse_full_overflow | AF-3-62, AF-10.7.2-04, AF-10.7.5-11, AF-20.2-25, AF-15.3-17 |  |

## Not verified by this run

- Formal: the assertions were checked by SymbiYosys under the environment assumptions (work/formal.md); a BOUNDED result holds only up to its depth. CDC/RDC, STA, synthesis and DFT checks are outside this flow.
- Rules marked NOT_VERIFIED_BY_SIM carry the contract's reason (static, structural, not observable...).
- Only the configurations of the run set above were simulated; code coverage is merged over its runs, mutation testing used the primary run base.s1.

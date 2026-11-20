# Verification report — spi_master

Generated 2026-11-20T08:35:26+00:00 by NNC Pipeline.

## Summary

| Item | Result |
|---|---|
| Rules | 206 — {'NOT_VERIFIED_BY_SIM': 32, 'VERIFIED': 174} |
| Checks | 41 — {'PASS': 41} |
| Tests | {'pass': 15} |
| Run set | 5 runs in 3 configurations (base, min, max); primary base.s1 |
| Integration | OK |
| Code coverage (RTL), line | 94.8 % (438/462 lines) |
| Code coverage (RTL), block | 93.8 % (135/144 statement blocks and branch arms) |
| Code coverage (RTL), expression | 98.2 % (162/165 condition terms) |
| Code coverage (RTL), toggle | 95.2 % (577/606 bit toggles 0->1 and 1->0) |
| Code coverage (RTL), functional | 94.9 % (37/39 cover points of the specification) |
| Mutation score | 91.7 % (33 killed / 3 survived / 0 not compiled) |
| Coverage target | not requested (`nnc cover <design> --target <n> --metric <m>`) |
| Formal (SymbiYosys, depth 32) | {'BOUNDED': 7, 'PROVEN': 6, 'UNSUPPORTED': 14} — reset assumptions + verif/formal/nnc_env.sv, work/formal.md |
| Triage | 7 failure(s), 7 analysed: work/triage.md |
| Agent cost | US$21.9118 in 56 calls (A0 1.0804, A1 0.5201, A12 0.3448, A13 0.1641, A14 1.1931, A15 1.9812, A17 4.0811, A18 0.708, A2 0.4891, A3 0.1925, A4 1.1147, A5 0.8018, A6 0.2656, A7 6.9029, A9 2.0724); of which US$2.5729 in 4 failed calls (usage limit, timeout, invalid answer) |

## Sign-off conditions

| Condition | State |
|---|---|
| Gates G1-G3 approved | met — approved on delegation by an agent: a person should confirm |
| Interface conformance of the DUT | met |
| Every selected check PASS (no FAIL, NOT_HIT, NOT_RUN) | met |
| Every planned check selected | met |
| Every rule in a check or declared not verifiable | met |
| Every run of the run set built and ran | met — 5 runs |
| Mutation run | met |
| Per-requirement mutation score >= 85 % | met — 80 rules with attributed mutants |
| Formal: no counterexample, no vacuous or failed proof | met — {'BOUNDED': 7, 'PROVEN': 6, 'UNSUPPORTED': 14} (work/formal.md) |

## Run set

Every check is merged over these runs: PASS when one run verified it and no run failed it; NOT_VERIFIABLE only when every run declared it so.

| Run | Parameters changed | Defines | Plusargs | Status | Tests | Failing assertions | Not verifiable here |
|---|---|---|---|---|---|---|---|
| base.s1 — CFG-BASE | defaults | — | — | ran | {'pass': 15} | none | 0 |
| base.s2 — CFG-BASE | defaults | — | — | ran | {'pass': 15} | none | 0 |
| min.s1 — CFG-MIN | PARA_SPI_CLK_DIV=1 | — | — | ran | {'pass': 15} | none | 0 |
| min.s2 — CFG-MIN | PARA_SPI_CLK_DIV=1 | — | — | ran | {'pass': 15} | none | 0 |
| max.s1 — CFG-MAX | PARA_SPI_CLK_DIV=255 | — | — | ran | {'pass': 15} | none | 0 |

## Gates

| Gate | State | Detail |
|---|---|---|
| G1_rules | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-19T07:13:20+00:00 |
| G2_contract | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-19T07:19:20+00:00 |
| D1_config | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-19T07:19:21+00:00 |
| D2_rtl | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-19T10:42:33+00:00 |
| G3_verif_sources | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-20T07:06:06+00:00 |
| G4_signoff | PENDING | artifacts ready for review |

## Checks

| Check | Kind | Title | Status | Evidence |
|---|---|---|---|---|
| CHK-001 | assertion | o_cmd_ready changes only at clock edges or reset assertion | **PASS** | hits 25891, fails 0; hit in 5/5 runs; formal UNSUPPORTED |
| CHK-002 | assertion | o_cmd_ready low while a response is shown | **PASS** | hits 232092, fails 0; hit in 5/5 runs; formal UNSUPPORTED |
| CHK-003 | assertion | o_cmd_ready in Idle after o_cs_n rise (blocked D-1 cycles) | **PASS** | hits 178046, fails 0; hit in 5/5 runs; formal UNSUPPORTED |
| CHK-004 | assertion | o_cmd_ready during a transfer and in its last cycle | **PASS** | hits 1433108, fails 0; hit in 5/5 runs; formal UNSUPPORTED |
| CHK-005 | assertion | o_cmd_ready in Pause and Trail | **PASS** | hits 226446, fails 0; hit in 5/5 runs; formal UNSUPPORTED |
| CHK-006 | assertion | o_cs_n falls exactly at a burst-start handshake | **PASS** | hits 186920, fails 0; hit in 5/5 runs; formal PROVEN |
| CHK-007 | assertion | o_cs_n low for whole burst, rises at A_last+17D only | **PASS** | hits 1659554, fails 0; hit in 5/5 runs; formal BOUNDED |
| CHK-008 | assertion | Minimum o_cs_n high gap between bursts | **PASS** | hits 2333, fails 0; hit in 5/5 runs; formal PROVEN |
| CHK-009 | assertion | Lead time: first SCLK edge D cycles after o_cs_n falls | **PASS** | hits 51957, fails 0; hit in 5/5 runs; formal PROVEN |
| CHK-010 | assertion | Pause entry and Pause outputs | **PASS** | hits 180122, fails 0; hit in 5/5 runs; formal PROVEN |
| CHK-011 | assertion | MOSI shift timing, CPHA_b=0 | **PASS** | hits 915699, fails 0; hit in 5/5 runs; formal BOUNDED |
| CHK-012 | assertion | MOSI shift timing, CPHA_b=1 | **PASS** | hits 921901, fails 0; hit in 5/5 runs; formal BOUNDED |
| CHK-013 | assertion | o_mosi changes only at shift edges; holds in Idle/Pause/Trail | **PASS** | hits 47058, fails 0; hit in 5/5 runs; formal BOUNDED |
| CHK-014 | assertion | o_mosi stable at every sampling edge | **PASS** | hits 75678, fails 0; hit in 5/5 runs; formal PROVEN |
| CHK-015 | assertion | Outputs take reset values at once on i_rst_n assertion | **PASS** | hits 924, fails 0; hit in 5/5 runs; formal UNSUPPORTED |
| CHK-016 | assertion | Output values held while in reset | **PASS** | hits 919, fails 0; hit in 5/5 runs; formal UNSUPPORTED |
| CHK-017 | assertion | o_sclk follows i_cpol combinationally during reset | **PASS** | hits 924, fails 0; hit in 5/5 runs; formal UNSUPPORTED |
| CHK-018 | assertion | Ready to accept at first edge after reset release | **PASS** | hits 8874, fails 0; hit in 5/5 runs; formal UNSUPPORTED |
| CHK-019 | assertion | Response outputs change only at clock edges or reset | **PASS** | hits 1846474, fails 0; hit in 5/5 runs; formal UNSUPPORTED |
| CHK-020 | assertion | Response reference model: data, order, timing, depth<=2 | **PASS** | hits 1846172, fails 0; hit in 5/5 runs; formal UNSUPPORTED |
| CHK-021 | assertion | o_rsp_data hold and i_rsp_ready ignored while not valid | **PASS** | hits 1827478, fails 0; hit in 5/5 runs; formal UNSUPPORTED |
| CHK-022 | assertion | No transfer starts while a byte is shown or held | **PASS** | hits 9546, fails 0; hit in 5/5 runs; formal UNSUPPORTED |
| CHK-023 | assertion | SCLK edges at A+k*D with correct levels | **PASS** | hits 1433108, fails 0; hit in 5/5 runs; formal BOUNDED |
| CHK-024 | assertion | No other o_sclk changes while o_cs_n=0 | **PASS** | hits 1508193, fails 0; hit in 5/5 runs; formal BOUNDED |
| CHK-025 | assertion | SCLK at CPOL_b in lead, Pause and Trail | **PASS** | hits 316743, fails 0; hit in 5/5 runs; formal BOUNDED |
| CHK-026 | assertion | o_sclk equals i_cpol while o_cs_n=1 | **PASS** | hits 187844, fails 0; hit in 5/5 runs; formal PROVEN |
| CHK-027 | assertion | No-gap joint between back-to-back transfers | **PASS** | hits 3410, fails 0; hit in 5/5 runs; formal UNSUPPORTED |
| CHK-028 | test | Commands without handshake have no effect | **PASS** | test_chk_028_no_handshake_no_effect; verified in base.s1, base.s2, min.s1, min.s2, max.s1 |
| CHK-029 | test | No combinational input paths to registered outputs | **PASS** | test_chk_029_no_combinational_input_paths; verified in base.s1, base.s2, min.s1, min.s2, max.s1 |
| CHK-030 | test | i_cmd_last=1 on first byte; o_cs_n rise independent of response stream | **PASS** | test_chk_030_single_byte_bursts; verified in base.s1, base.s2, min.s1, min.s2, max.s1 |
| CHK-031 | test | Pause entry/exit, long pause and endless burst | **PASS** | test_chk_031_pause_and_endless_burst; verified in base.s1, base.s2, min.s1, min.s2, max.s1 |
| CHK-032 | test | Mode captured at burst start (change just before acceptance) | **PASS** | test_chk_032_mode_change_before_burst_start; verified in base.s1, base.s2, min.s1, min.s2, max.s1 |
| CHK-033 | test | Error test: mode inputs changed during a burst are ignored | **PASS** | test_chk_033_mode_change_during_burst_ignored; verified in base.s1, base.s2, min.s1, min.s2, max.s1 |
| CHK-034 | test | i_cpol toggled in reset and Idle | **PASS** | test_chk_034_cpol_follow_in_reset_and_idle; verified in base.s1, base.s2, min.s1, min.s2, max.s1 |
| CHK-035 | test | Reset in each phase: abort, discard, immediate restart | **PASS** | test_chk_035_reset_in_each_phase; verified in base.s1, base.s2, min.s1, min.s2, max.s1 |
| CHK-036 | test | Back-pressure: held byte created and released; consumer never takes | **PASS** | test_chk_036_held_byte_backpressure; verified in base.s1, base.s2, min.s1, min.s2, max.s1 |
| CHK-037 | test | Response handshake exactly at A+16D and random i_rsp_ready | **PASS** | test_chk_037_rsp_handshake_at_transfer_end_and_random_ready; verified in base.s1, base.s2, min.s1, min.s2, max.s1 |
| CHK-038 | test | All four modes with random data, burst lengths and gaps | **PASS** | test_chk_038_random_traffic_all_modes, test_regression_random; verified in base.s1, base.s2, min.s1, min.s2, max.s1 |
| CHK-039 | test | MISO sampling-edge precision | **PASS** | test_chk_039_miso_sampling_edge_precision; verified in base.s1, base.s2, min.s1, min.s2, max.s1 |
| CHK-040 | test | Continuous bursts, joint timing and throughput | **PASS** | test_chk_040_continuous_bursts_timing; verified in base.s1, base.s2, min.s1, min.s2, max.s1 |
| CHK-041 | test | Divider timing in the configuration (incl. D=1 and D=255) | **PASS** | test_chk_041_divider_timing; verified in base.s1, base.s2, min.s1, min.s2, max.s1 |

## Requirement traceability (RTM)

| Rule | Spec ref | Statement | Checks | Mutation | Status |
|---|---|---|---|---|---|
| SPI-1.1-01 |  | Each transfer shifts one byte out on o_mosi and one byte in from i_miso. | CHK-011:PASS, CHK-012:PASS, CHK-038:PASS | — | **VERIFIED** |
| SPI-1.1-02 |  | Received bytes are returned on the response stream in order, one per transmitted command byte. | CHK-020:PASS, CHK-038:PASS | 100.0 % (4/4) | **VERIFIED** |
| SPI-1.1-04 |  | The master stops starting new transfers while the response stream is back-pressured. | CHK-022:PASS, CHK-036:PASS | — | **VERIFIED** |
| SPI-1.2-01 |  | Each command produces one 8-bit full-duplex transfer, MSB first. | CHK-011:PASS, CHK-038:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-1.2-02 |  | i_cmd_last = 1 marks the last byte of a burst, and o_cs_n stays low for the whole burst. | CHK-007:PASS | — | **VERIFIED** |
| SPI-1.2-03 |  | SPI modes 0 to 3 are selected by i_cpol and i_cpha. | CHK-038:PASS | — | **VERIFIED** |
| SPI-1.2-04 |  | i_cpol and i_cpha are captured when a burst starts. | CHK-032:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-1.2-05 |  | SCLK frequency is f(i_clk) / (2 x PARA_SPI_CLK_DIV). | CHK-023:PASS, CHK-041:PASS | 100.0 % (3/3) | **VERIFIED** |
| SPI-1.2-07 |  | There is no SCLK gap between back-to-back bytes. | CHK-027:PASS, CHK-040:PASS | — | **VERIFIED** |
| SPI-1.2-08 |  | SCLK pauses at its idle level and o_cs_n stays low. | CHK-010:PASS, CHK-031:PASS | — | **VERIFIED** |
| SPI-1.2-09 |  | No received byte is lost: one byte is shown on the response stream and at most one more is held inside the master. | CHK-020:PASS, CHK-036:PASS | 100.0 % (3/3) | **VERIFIED** |
| SPI-1.2-10 |  | Reset is asynchronous and active-low. | CHK-035:PASS | — | **VERIFIED** |
| SPI-3-01 |  | A transfer whose command is accepted at edge A covers 16·D i_clk cycles, starting at edges A through A + 16·D − 1. | CHK-004:PASS, CHK-023:PASS | 100.0 % (5/5) | **VERIFIED** |
| SPI-3-02 |  | The k-th transition of o_sclk (SCLK edge k) happens at edge A + k·D. | CHK-023:PASS | 100.0 % (5/5) | **VERIFIED** |
| SPI-3-03 |  | Odd SCLK edges (k = 1, 3, …, 15) leave the idle level of o_sclk. Even SCLK edges (k = 2, 4, …, 16) return o_sclk to the idle level. | CHK-023:PASS | — | **VERIFIED** |
| SPI-3-04 |  | The values of i_cpol and i_cpha captured at the first acceptance edge of the burst (CPOL_b, CPHA_b) apply for the current burst. | CHK-032:PASS | — | **VERIFIED** |
| SPI-3-05 |  | o_cs_n is 0 and o_sclk is at the idle level. | CHK-010:PASS, CHK-025:PASS, CHK-031:PASS | — | **VERIFIED** |
| SPI-3-06 |  | o_cs_n stays low for a trail of D cycles after SCLK edge 16 before going high. | CHK-007:PASS | 100.0 % (3/3) | **VERIFIED** |
| SPI-4-02 |  | SCLK frequency shall equal f(i_clk) / (2·D), where D is PARA_SPI_CLK_DIV i_clk cycles per SCLK half period. | CHK-023:PASS, CHK-041:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-4-03 | REQ-PAR-001 | Elaboration of m_spi_master shall fail with an error message. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SPI-4-04 | REQ-PAR-002 | m_spi_master shall exhibit the specified behaviour without any other RTL change. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SPI-5-01 |  | i_rst_n is active-low, asserted asynchronously and released synchronously to i_clk. | CHK-035:PASS | — | **VERIFIED** |
| SPI-5-02 |  | The environment keeps i_cmd_valid at 0 while i_rst_n = 0. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SPI-5-04 |  | o_cmd_ready has reset value 1. | CHK-016:PASS | — | **VERIFIED** |
| SPI-5-05 |  | o_cmd_ready must not depend combinationally on any input. | CHK-001:PASS, CHK-029:PASS | — | **VERIFIED** |
| SPI-5-06 |  | i_cmd_data is captured at the command handshake as the byte to send. | CHK-011:PASS, CHK-012:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-5-07 |  | i_cmd_last is captured at the command handshake; when 1, the byte ends the burst and o_cs_n is released after it. | CHK-007:PASS, CHK-030:PASS | — | **VERIFIED** |
| SPI-5-08 |  | o_rsp_valid has reset value 0. | CHK-016:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-5-09 |  | o_rsp_data carries the byte received during the transfer of the matching command. | CHK-020:PASS, CHK-038:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-5-10 |  | o_rsp_data has reset value 0. | CHK-016:PASS | — | **VERIFIED** |
| SPI-5-11 |  | o_sclk equals i_cpol, following it combinationally, in reset. | CHK-017:PASS, CHK-034:PASS | — | **VERIFIED** |
| SPI-5-12 |  | o_mosi has reset value 0. | CHK-016:PASS | — | **VERIFIED** |
| SPI-5-13 |  | o_cs_n has reset value 1. | CHK-016:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-5-14 |  | i_cpol may change only while o_cs_n = 1. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SPI-5-15 |  | i_cpha = 0 samples on leading edges and i_cpha = 1 samples on trailing edges. | CHK-014:PASS, CHK-032:PASS, CHK-038:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-5-16 |  | i_cpha may change only while o_cs_n = 1. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SPI-6.1-01 | REQ-CLK-001 | All state elements of m_spi_master shall be clocked by the rising edge of i_clk, the only clock of the block. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SPI-6.1-02 | REQ-CLK-002 | o_sclk shall be produced as a data output timed by i_clk. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SPI-6.1-03 | REQ-CLK-002 | o_sclk shall not clock any state element inside the block. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SPI-6.1-04 | REQ-CLK-003 | i_miso shall be treated as synchronous to i_clk and sampled without a synchroniser. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SPI-6.2-01 | REQ-RST-001 | All outputs shall take their reset values at once, without waiting for an edge of i_clk. | CHK-015:PASS, CHK-035:PASS | 100.0 % (5/5) | **VERIFIED** |
| SPI-6.2-02 | REQ-RST-002 | o_cs_n shall be 1. | CHK-016:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-6.2-03 | REQ-RST-003 | o_sclk shall equal the current value of i_cpol and follow every change of i_cpol combinationally. | CHK-017:PASS, CHK-026:PASS, CHK-034:PASS | — | **VERIFIED** |
| SPI-6.2-04 | REQ-RST-004 | o_mosi shall be 0. | CHK-016:PASS | — | **VERIFIED** |
| SPI-6.2-05 | REQ-RST-005 | o_rsp_valid shall be 0 and o_rsp_data shall be 8'h00. | CHK-016:PASS | 100.0 % (3/3) | **VERIFIED** |
| SPI-6.2-06 | REQ-RST-006 | o_cmd_ready shall be 1. | CHK-016:PASS | — | **VERIFIED** |
| SPI-6.2-07 | REQ-RST-007 | The master shall not accept a command. | CHK-016:PASS, CHK-028:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-6.2-08 | REQ-RST-008 | The transfer in progress shall be aborted. | CHK-035:PASS | — | **VERIFIED** |
| SPI-6.2-10 | REQ-RST-009 | That byte shall be discarded without a response handshake. | CHK-035:PASS | 100.0 % (3/3) | **VERIFIED** |
| SPI-6.2-11 | REQ-RST-010 | The master shall be in Idle with the gap requirement met and able to accept a command at the first edge at which i_rst_n is 1. | CHK-018:PASS, CHK-035:PASS | — | **VERIFIED** |
| SPI-6.2-12 | REQ-CS-005, REQ-RST-011 | The minimum o_cs_n high time of REQ-CS-005 shall not be required; after an aborted burst the high time is the reset duration plus time until next acceptance. | CHK-018:PASS, CHK-035:PASS | — | **VERIFIED** |
| SPI-7.1-01 | REQ-CMD-001 | The master accepts a command at an edge only when i_rst_n = 1, i_cmd_valid = 1 and o_cmd_ready = 1 at that edge. | CHK-006:PASS, CHK-028:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.1-02 | REQ-CMD-002 | The master captures i_cmd_data as the byte to send and i_cmd_last as the end-of-burst flag of that transfer. | CHK-007:PASS, CHK-011:PASS, CHK-038:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.1-03 | REQ-CMD-003 | Values of i_cmd_data and i_cmd_last have no effect. | CHK-028:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-7.1-04 | REQ-CMD-004 | The master behaves as if the command had never been presented. | CHK-028:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.1-05 | REQ-CMD-005 | o_cmd_ready changes only at an i_clk edge or when i_rst_n is asserted, and does not depend combinationally on any input. | CHK-001:PASS, CHK-029:PASS | — | **VERIFIED** |
| SPI-7.1-06 | REQ-CMD-006 | o_cmd_ready is 0 in every cycle in which o_rsp_valid = 1. | CHK-002:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-7.1-07 | REQ-CMD-007 | o_cmd_ready is 0 in every cycle starting at an edge from R to R + D − 2 (no such cycle when D = 1). | CHK-003:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.1-08 | REQ-CMD-008 | o_cmd_ready is 1. | CHK-003:PASS, CHK-018:PASS, CHK-030:PASS | — | **VERIFIED** |
| SPI-7.1-09 | REQ-CMD-009 | o_cmd_ready is 0. | CHK-004:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-7.1-10 | REQ-CMD-010 | o_cmd_ready is 1 if the captured i_cmd_last is 0 and o_rsp_valid is 0, and 0 otherwise. | CHK-004:PASS | 100.0 % (4/4) | **VERIFIED** |
| SPI-7.1-11 | REQ-CMD-011 | o_cmd_ready is 1 when o_rsp_valid = 0 and 0 when o_rsp_valid = 1. | CHK-005:PASS | — | **VERIFIED** |
| SPI-7.1-12 | REQ-CMD-012 | o_cmd_ready is 0. | CHK-005:PASS | — | **VERIFIED** |
| SPI-7.2-01 | REQ-CS-001 | o_cs_n changes from 1 to 0 at edge A, starting a burst. | CHK-006:PASS | — | **VERIFIED** |
| SPI-7.2-02 | REQ-CS-002 | o_cs_n stays 0 until edge A + 17·D, where it changes to 1. | CHK-007:PASS | 100.0 % (3/3) | **VERIFIED** |
| SPI-7.2-03 | REQ-CS-001, REQ-CS-002, REQ-CS-003 | o_cs_n changes only at the edges given in REQ-CS-001 and REQ-CS-002 and at the assertion of i_rst_n. | CHK-007:PASS | 100.0 % (3/3) | **VERIFIED** |
| SPI-7.2-04 | REQ-CS-004 | The first SCLK edge of a burst comes exactly D cycles after o_cs_n falls (edge A + D). | CHK-009:PASS | — | **VERIFIED** |
| SPI-7.2-05 | REQ-CS-005 | o_cs_n stays 1 for at least D cycles. | CHK-008:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.2-07 | REQ-CS-007 | The rise of o_cs_n does not depend on the response stream state (o_rsp_valid, i_rsp_ready, a held byte). | CHK-007:PASS, CHK-030:PASS, CHK-036:PASS | — | **VERIFIED** |
| SPI-7.3-01 | REQ-MODE-001 | The master captures i_cpol as CPOL_b and i_cpha as CPHA_b. | CHK-032:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.3-02 | REQ-MODE-002 | CPOL_b and CPHA_b control o_sclk, o_mosi and the sampling of i_miso. | CHK-023:PASS, CHK-025:PASS, CHK-033:PASS | — | **VERIFIED** |
| SPI-7.3-03 | REQ-MODE-003 | Changes of i_cpol or i_cpha have no effect on o_sclk, o_mosi, o_cs_n, i_miso sampling or response data. | CHK-024:PASS, CHK-033:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.3-04 | REQ-MODE-004 | Leading SCLK edges (odd k) are sampling edges and trailing edges (even k) are shift edges. | CHK-011:PASS, CHK-038:PASS | 100.0 % (4/4) | **VERIFIED** |
| SPI-7.3-05 | REQ-MODE-005 | Leading SCLK edges (odd k) are shift edges and trailing edges (even k) are sampling edges. | CHK-012:PASS, CHK-038:PASS | 100.0 % (3/3) | **VERIFIED** |
| SPI-7.4-01 | REQ-SCLK-001 | o_sclk toggles at each of the 16 edges A + k·D, k = 1 to 16. | CHK-023:PASS | 100.0 % (3/3) | **VERIFIED** |
| SPI-7.4-02 | REQ-SCLK-001, REQ-SCLK-002 | o_sclk does not change at any edge other than A + k·D, k = 1 to 16. | CHK-024:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.4-03 | REQ-SCLK-003 | o_sclk equals CPOL_b (lead half period, Pause, Trail). | CHK-025:PASS | — | **VERIFIED** |
| SPI-7.4-04 | REQ-SCLK-004 | o_sclk equals NOT CPOL_b for odd k and CPOL_b for even k. | CHK-023:PASS | — | **VERIFIED** |
| SPI-7.4-05 | REQ-SCLK-005 | o_sclk equals i_cpol and follows changes of i_cpol combinationally. | CHK-026:PASS, CHK-034:PASS | — | **VERIFIED** |
| SPI-7.4-06 | REQ-SCLK-006 | o_sclk takes the value of i_cpol from edge R on. | CHK-026:PASS, CHK-033:PASS | — | **VERIFIED** |
| SPI-7.4-07 | REQ-SCLK-007 | The SCLK period over the joint is 2·D cycles with each half period D cycles. | CHK-027:PASS, CHK-040:PASS | — | **VERIFIED** |
| SPI-7.5-01 | REQ-MOSI-001 | Bits of each byte are sent MSB first: d[7], d[6], …, d[0]. | CHK-011:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.5-02 | REQ-MOSI-002 | o_mosi takes the value d[7] at the acceptance edge A. | CHK-011:PASS | — | **VERIFIED** |
| SPI-7.5-03 | REQ-MOSI-003 | o_mosi takes the value d[7 − j] at edge A + 2·j·D for j = 1 to 7. | CHK-011:PASS | 100.0 % (3/3) | **VERIFIED** |
| SPI-7.5-04 | REQ-MOSI-004 | o_mosi takes the value d[7 − j] at edge A + (2·j + 1)·D for j = 0 to 7. | CHK-012:PASS | 100.0 % (3/3) | **VERIFIED** |
| SPI-7.5-05 | REQ-MOSI-002, REQ-MOSI-004, REQ-MOSI-005 | o_mosi does not change at any edge other than those of REQ-MOSI-002 to REQ-MOSI-004, except at the assertion of i_rst_n. | CHK-013:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.5-06 | REQ-MOSI-006 | o_mosi keeps the last value it was given, which is 0 after reset. | CHK-013:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.5-07 | REQ-MOSI-007 | o_mosi is stable in the cycle before each sampling edge and does not change at any sampling edge. | CHK-014:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-7.5-08 | REQ-MOSI-002 | o_mosi keeps d[0] unless the next command is accepted at that edge, in which case it takes the next d[7]. | CHK-011:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.5-09 |  | o_mosi keeps its previous value from the acceptance edge until SCLK edge 1. | CHK-012:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.6-01 | REQ-MISO-001 | The master captures i_miso as r[7 − j] at edge A + (2·j + 1)·D for j = 0 to 7. | CHK-020:PASS, CHK-038:PASS, CHK-039:PASS | 100.0 % (3/3) | **VERIFIED** |
| SPI-7.6-02 | REQ-MISO-002 | The master captures i_miso as r[7 − j] at edge A + (2·j + 2)·D for j = 0 to 7. | CHK-020:PASS, CHK-038:PASS, CHK-039:PASS | 100.0 % (3/3) | **VERIFIED** |
| SPI-7.6-03 | REQ-MISO-003 | The captured value is i_miso in the cycle ending at that edge, just before o_sclk makes the sampling transition. | CHK-020:PASS, CHK-039:PASS | — | **VERIFIED** |
| SPI-7.6-04 | REQ-MISO-004 | i_miso has no effect. | CHK-039:PASS | — | **VERIFIED** |
| SPI-7.6-05 | REQ-MISO-005 | The received byte r[7:0] of a transfer is made only of the 8 bits captured during that transfer. | CHK-020:PASS, CHK-038:PASS, CHK-039:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.7-01 | REQ-RSP-001 | Each accepted command produces exactly one response carrying the byte received during its transfer. | CHK-020:PASS, CHK-038:PASS | 100.0 % (4/4) | **VERIFIED** |
| SPI-7.7-02 | REQ-RSP-002 | Responses are delivered in command acceptance order, across burst boundaries. | CHK-020:PASS, CHK-038:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-7.7-03 | REQ-RSP-003 | The master loads the received byte into o_rsp_data and sets o_rsp_valid to 1. | CHK-020:PASS, CHK-037:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.7-04 | REQ-RSP-003, REQ-RSP-004 | The received byte becomes the held byte. | CHK-020:PASS, CHK-036:PASS | 100.0 % (3/3) | **VERIFIED** |
| SPI-7.7-05 | REQ-RSP-005 | The held byte is loaded into o_rsp_data and o_rsp_valid stays 1. | CHK-020:PASS, CHK-036:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-7.7-06 | REQ-RSP-006 | o_rsp_valid changes to 0. | CHK-020:PASS, CHK-036:PASS | 100.0 % (3/3) | **VERIFIED** |
| SPI-7.7-07 | REQ-RSP-007 | o_rsp_valid stays 1 and o_rsp_data does not change. | CHK-020:PASS, CHK-021:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-7.7-08 | REQ-RSP-008 | o_rsp_data keeps the last byte loaded into it, or 8'h00 after reset. | CHK-021:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.7-09 | REQ-RSP-009 | o_rsp_valid and o_rsp_data change only at i_clk edges or at the assertion of i_rst_n. | CHK-019:PASS, CHK-029:PASS | — | **VERIFIED** |
| SPI-7.7-10 | REQ-RSP-010 | i_rsp_ready has no effect. | CHK-021:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-7.7-11 | REQ-RSP-011 | The master never overwrites a shown or held byte before it has been taken and never delivers a byte twice. | CHK-020:PASS, CHK-036:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.7-12 | REQ-RSP-012 | At most two received bytes are pending at any time: one shown byte and at most one held byte. | CHK-020:PASS, CHK-036:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.7-13 |  | A new transfer starts only when every earlier received byte has been taken, except the byte of the transfer ending at the same edge. | CHK-022:PASS, CHK-036:PASS | — | **VERIFIED** |
| SPI-7.8-01 | REQ-FLOW-001 | The new transfer uses that edge as its acceptance edge, with SCLK edge 1 D cycles after previous SCLK edge 16. | CHK-027:PASS, CHK-040:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-7.8-02 | REQ-FLOW-002 | The master enters Pause. | CHK-010:PASS, CHK-031:PASS | 100.0 % (4/4) | **VERIFIED** |
| SPI-7.8-03 | REQ-FLOW-003 | o_cs_n stays 0, o_sclk stays at CPOL_b and o_mosi keeps its value. | CHK-010:PASS, CHK-013:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-7.8-04 | REQ-FLOW-004 | Pause lasts until a command is accepted, without any time limit. | CHK-031:PASS | — | **VERIFIED** |
| SPI-7.8-05 | REQ-FLOW-005 | A transfer starts with acceptance edge A = P, in the same burst with the same CPOL_b and CPHA_b. | CHK-031:PASS | — | **VERIFIED** |
| SPI-7.8-06 | REQ-CS-002, REQ-FLOW-006 | The master enters Trail and o_cs_n rises at edge A + 17·D. | CHK-007:PASS | 100.0 % (4/4) | **VERIFIED** |
| SPI-7.8-07 | REQ-FLOW-007 | The master does not start a transfer. | CHK-022:PASS, CHK-036:PASS | — | **VERIFIED** |
| SPI-8-01 |  | SCLK edge 1 (lead) must occur D i_clk cycles after command acceptance, where D = PARA_SPI_CLK_DIV. | CHK-009:PASS | — | **VERIFIED** |
| SPI-8-02 |  | o_cs_n must go low at the acceptance edge itself (0 cycles after command acceptance) for the first byte of a burst. | CHK-006:PASS | — | **VERIFIED** |
| SPI-8-03 |  | o_rsp_valid must become 1 16·D i_clk cycles after command acceptance. | CHK-020:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-8-04 |  | o_cs_n must go high D i_clk cycles after SCLK edge 16 of the last byte (trail). | CHK-007:PASS | 100.0 % (3/3) | **VERIFIED** |
| SPI-8-05 |  | o_cs_n must stay high for at least D i_clk cycles between bursts. | CHK-008:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-8-06 |  | Byte period inside a continuous burst must be 16·D i_clk cycles. | CHK-023:PASS, CHK-027:PASS, CHK-040:PASS | — | **VERIFIED** |
| SPI-8-07 |  | o_cs_n low time of an n-byte continuous burst must be 16·n·D + D i_clk cycles. | CHK-007:PASS, CHK-040:PASS | 100.0 % (3/3) | **VERIFIED** |
| SPI-8-08 |  | Minimum time between first acceptances of consecutive n-byte bursts must be 16·n·D + 2·D i_clk cycles. | CHK-040:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-8-09 |  | The minimum period of single-byte bursts must be 18·D i_clk cycles. | CHK-040:PASS | — | **VERIFIED** |
| SPI-8-10 |  | The next command must be valid in the last cycle of the current transfer. | CHK-040:PASS | — | **VERIFIED** |
| SPI-8-11 |  | o_rsp_valid must be 0 in the last cycle of the current transfer, so the previous response must be taken within 16·D − 1 cycles of becoming valid. | CHK-040:PASS | — | **VERIFIED** |
| SPI-8-12 |  | The next transfer must not start at SCLK edge 16. | CHK-004:PASS, CHK-022:PASS, CHK-036:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-8-13 |  | The burst must enter Pause, or Trail if it was the last byte. | CHK-010:PASS, CHK-030:PASS, CHK-036:PASS | — | **VERIFIED** |
| SPI-8-14 |  | That transfer's byte must become the held byte. | CHK-020:PASS, CHK-036:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-8-15 |  | No new transfer may start until both bytes have been taken. | CHK-022:PASS, CHK-036:PASS | — | **VERIFIED** |
| SPI-8-16 | REQ-RSP-002 | Responses must come out in command order. | CHK-020:PASS, CHK-038:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-10-02 | REQ-ERR-001, REQ-MODE-003 | The master shall keep using CPOL_b and CPHA_b until the end of the burst. | CHK-033:PASS | — | **VERIFIED** |
| SPI-10-03 | REQ-ERR-002, REQ-SCLK-006 | o_sclk shall change to i_cpol at the edge where o_cs_n rises. | CHK-026:PASS, CHK-033:PASS | — | **VERIFIED** |
| SPI-10-04 | REQ-ERR-003 | The command shall wait without effect until a command handshake occurs. | CHK-028:PASS | — | **VERIFIED** |
| SPI-10-05 | REQ-ERR-004, REQ-RST-007 | The master shall not accept the command. | CHK-028:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-10-06 | REQ-ERR-005 | The master shall keep o_rsp_valid = 1 with the same byte. | CHK-020:PASS, CHK-036:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-10-07 | REQ-ERR-005 | The master shall not start any further transfer. | CHK-022:PASS, CHK-036:PASS | — | **VERIFIED** |
| SPI-10-08 | REQ-ERR-006 | o_cs_n shall stay 0 indefinitely. | CHK-031:PASS | — | **VERIFIED** |
| SPI-10-09 | REQ-ERR-007, REQ-RST-008 | o_cs_n shall go to 1 and o_sclk to i_cpol at once, even in the middle of an SCLK half period. | CHK-015:PASS, CHK-035:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-10-10 | REQ-ERR-007, REQ-RST-008 | The partial byte shall be discarded. | CHK-035:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-10-11 | REQ-ERR-008, REQ-RST-002, REQ-RST-006 | The master shall go to the reset state of REQ-RST-002 to REQ-RST-006. | CHK-015:PASS, CHK-035:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-10-12 | REQ-ERR-008, REQ-RST-002, REQ-RST-006 | Pending bytes shall be discarded. | CHK-035:PASS | 100.0 % (3/3) | **VERIFIED** |
| SPI-10-13 | REQ-ERR-009, REQ-RSP-003 | The received byte of that transfer shall load into o_rsp_data at that edge, with o_rsp_valid staying 1. | CHK-020:PASS, CHK-037:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-10-15 |  | The burst never ends; o_cs_n stays 0 and transfers continue as commands arrive. | CHK-031:PASS | — | **VERIFIED** |
| SPI-10-16 |  | The half-period count shall reach 255 without overflow, giving 255-cycle half periods and 4080 cycles per byte. | CHK-041:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-11-01 |  | Verification must run every listed configuration, and since SPI mode is a run-time input, each configuration must be exercised in all four SPI modes. | CHK-038:PASS | — | **VERIFIED** |
| SPI-11-02 |  | With PARA_SPI_CLK_DIV=1, the smallest legal divider, SCLK must be f(i_clk)/2 and operate correctly in all four SPI modes. | CHK-038:PASS, CHK-041:PASS | — | **VERIFIED** |
| SPI-11-03 |  | With PARA_SPI_CLK_DIV=255, the largest legal divider, the half-period counter must work at full width and operate correctly in all four SPI modes with short bursts. | CHK-041:PASS | — | **VERIFIED** |
| SPI-12-01 |  | The environment shall release i_rst_n synchronously to i_clk. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SPI-12-02 |  | Assertion of i_rst_n may be asynchronous. | CHK-035:PASS | — | **VERIFIED** |
| SPI-12-03 |  | The environment shall keep i_cmd_valid = 0 while i_rst_n = 0. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SPI-12-04 |  | The environment shall change i_cpol and i_cpha only while o_cs_n = 1. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SPI-12-05 | REQ-ERR-001 | Error tests may deliberately violate the rule that i_cpol and i_cpha change only while o_cs_n = 1. | CHK-033:PASS | — | **VERIFIED** |
| SPI-12-06 |  | The SPI slave testbench model shall drive i_miso as a function of o_sclk and o_cs_n only. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SPI-12-07 |  | The slave shall put bit 7 on i_miso when o_cs_n falls and the next bit after each trailing SCLK edge. | CHK-038:PASS | — | **VERIFIED** |
| SPI-12-08 |  | The slave shall put bit 7 − j on i_miso after leading SCLK edge 2·j + 1. | CHK-038:PASS | — | **VERIFIED** |
| SPI-12-09 |  | The slave model shall change i_miso only after the i_clk edge at which o_sclk or o_cs_n changed, never altering the value seen at a sampling edge. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SPI-12-10 |  | The environment shall not assert i_rst_n at an i_clk edge; assertion happens between edges. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SPI-12-12 |  | The environment shall drive i_rst_n = 0 from time zero, before the first rising i_clk edge, for at least 2 cycles. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SPI-12-13 |  | i_cpol, i_cpha and every other input shall always be 0 or 1, never X or Z. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SPI-12-15 |  | i_miso shall meet setup and hold time to i_clk at each sampling edge; with D = 1, slave clock-to-output plus board round trip must fit in one period minus setup. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SPI-12-16 | REQ-CMD-004 | The command stream may change i_cmd_valid, i_cmd_data and i_cmd_last before acceptance; stability is not required. | CHK-028:PASS | — | **VERIFIED** |
| SPI-12-17 |  | The response consumer may drive i_rsp_ready with any pattern. | CHK-037:PASS | — | **VERIFIED** |
| SPI-12-18 |  | Verification shall run all four modes in every configuration of section 11, with random bytes on i_cmd_data and from the slave model. | CHK-038:PASS | — | **VERIFIED** |
| SPI-12-19 |  | Verification shall use burst lengths 1, 2 and at least 16, mixing bursts with and without pauses (i_cmd_valid gaps of 0, 1 and many cycles). | CHK-038:PASS | — | **VERIFIED** |
| SPI-12-20 | REQ-RSP-001, REQ-RSP-002, REQ-RSP-011 | A scoreboard shall check each response equals the byte sent by the slave during the matching command, in order, with no loss or duplicate. | CHK-038:PASS | — | **VERIFIED** |
| SPI-12-21 |  | A slave-side monitor shall check MOSI data at every sampling edge and the SCLK edge times (A + k·D). | CHK-011:PASS, CHK-012:PASS, CHK-014:PASS, CHK-023:PASS | — | **VERIFIED** |
| SPI-12-22 |  | The monitor shall also check lead, trail and gap times, the SCLK idle level and that o_mosi never changes at a sampling edge. | CHK-007:PASS, CHK-008:PASS, CHK-009:PASS, CHK-014:PASS, CHK-025:PASS | — | **VERIFIED** |
| SPI-12-23 | REQ-CMD-006, REQ-CMD-012 | Verification shall check o_cmd_ready cycle by cycle against REQ-CMD-006 to REQ-CMD-012, including the blocked first D − 1 Idle cycles. | CHK-001:PASS, CHK-002:PASS, CHK-003:PASS, CHK-004:PASS, CHK-005:PASS | — | **VERIFIED** |
| SPI-12-24 |  | Back-pressure tests shall hold i_rsp_ready = 0 for long periods so that a held byte is created. | CHK-036:PASS | — | **VERIFIED** |
| SPI-12-25 | REQ-ERR-009 | Back-pressure tests shall cover a response handshake exactly at edge A + 16·D (REQ-ERR-009) and random i_rsp_ready patterns. | CHK-037:PASS | — | **VERIFIED** |
| SPI-12-26 |  | Reset tests shall hold i_rsp_ready = 0 before reset where a shown or held byte is wanted, and assert i_rst_n between i_clk edges in each phase (Transfer, Pause, Trail, Idle gap, held byte). | CHK-035:PASS | — | **VERIFIED** |
| SPI-12-27 |  | Reset tests shall check that outputs take reset values at once and no response of the aborted transfer appears. | CHK-035:PASS | — | **VERIFIED** |
| SPI-12-28 | REQ-RST-003, REQ-SCLK-005 | A test shall toggle i_cpol while i_rst_n = 0 and in Idle, and check o_sclk follows it in the same cycle. | CHK-034:PASS | — | **VERIFIED** |
| SPI-12-29 |  | A test shall change i_cpol and i_cpha in the cycle just before a burst-start acceptance edge and check the new values are used. | CHK-032:PASS | — | **VERIFIED** |
| SPI-12-30 | REQ-ERR-001, REQ-ERR-002 | An error test shall change i_cpol and i_cpha during a burst and check the burst finishes in the captured mode. | CHK-033:PASS | — | **VERIFIED** |
| SPI-12-31 |  | Coverage shall include mode × configuration, continuous join, pause entry and exit, held byte created and released, reset in each phase, and i_cmd_last = 1 on the first byte. | CHK-030:PASS, CHK-031:PASS, CHK-035:PASS, CHK-036:PASS, CHK-038:PASS, CHK-040:PASS | — | **VERIFIED** |
| SPI-12-32 | REQ-PAR-001 | REQ-PAR-001 shall be checked by elaborating once with an illegal value, not by simulation. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SPI-13-01 | REQ-IMP-001 | The block shall meet timing at 50 MHz i_clk (20 ns period) in GF180MCU technology at worst-case corner. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SPI-13-02 | REQ-IMP-002 | The RTL shall follow docs/RTL_RULES.md (REF-003). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SPI-13-03 | REQ-IMP-003 | All flip-flops shall be clocked on the rising edge of i_clk and reset asynchronously by i_rst_n. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SPI-13-04 |  | The RTL shall contain no latches, no clock gating and no derived clocks. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SPI-13-05 | REQ-IMP-004 | o_cs_n and o_mosi shall be driven directly by flip-flops. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SPI-13-06 | REQ-IMP-005 | o_sclk shall come from a flip-flop value while o_cs_n = 0. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SPI-13-07 |  | The only combinational path from an input to o_sclk shall be the i_cpol path, used while o_cs_n = 1 or during reset. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SPI-13-08 | REQ-IMP-006 | o_sclk should be free of glitches when o_cs_n changes. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| SPI-13-09 |  | The selection between i_cpol and the internal SCLK value should be built so equal inputs give no static hazard. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| SPI-13-10 | REQ-IMP-007 | o_cmd_ready, o_rsp_valid and o_rsp_data shall be driven by flip-flops or logic of flip-flops only, with no combinational path from any input. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SPI-13-11 | REQ-IMP-008 | i_miso shall be captured directly into a data flip-flop with no synchroniser. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SPI-13-12 |  | The integrator shall constrain the input delay of i_miso. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| SPI-13-13 | REQ-IMP-009 | The half-period counter shall be wide enough for D = 255, at least 8 bits. | CHK-041:PASS | — | **VERIFIED** |
| SPI-14-01 |  | The master shall use exactly D cycles for lead and exactly D cycles for trail. | CHK-007:PASS, CHK-009:PASS, CHK-040:PASS | — | **VERIFIED** |
| SPI-14-02 |  | The gap between transfers shall be at least D cycles, and exactly D cycles when the next command is already waiting. | CHK-008:PASS, CHK-040:PASS | 100.0 % (1/1) | **VERIFIED** |
| SPI-14-03 |  | A command shall be accepted only in Idle (after D − 1 blocked cycles), in Pause, or in the last cycle of a non-last transfer, and only if o_rsp_valid = 0. | CHK-003:PASS, CHK-004:PASS, CHK-005:PASS, CHK-022:PASS | 100.0 % (2/2) | **VERIFIED** |
| SPI-14-04 |  | o_cmd_ready shall have no combinational input path. | CHK-001:PASS, CHK-029:PASS | — | **VERIFIED** |
| SPI-14-05 |  | A transfer shall start only when o_rsp_valid = 0; no byte is lost, as one more byte can be held inside the master. | CHK-022:PASS, CHK-036:PASS | — | **VERIFIED** |
| SPI-14-06 |  | The response shall appear at SCLK edge 16 (A + 16·D) in all modes, also for CPHA = 0 where the last bit is sampled at edge 15. | CHK-020:PASS | — | **VERIFIED** |
| SPI-14-07 |  | o_mosi shall hold its last value, and be 0 after reset. | CHK-012:PASS, CHK-013:PASS | — | **VERIFIED** |
| SPI-14-08 |  | While o_cs_n = 1, o_sclk shall be combinational from i_cpol; while o_cs_n = 0 it shall be registered from the captured CPOL_b. | CHK-026:PASS, CHK-034:PASS | — | **VERIFIED** |
| SPI-14-09 |  | Mode input changes during a burst shall be ignored; captured values shall be used until o_cs_n rises. | CHK-033:PASS | — | **VERIFIED** |
| SPI-14-10 |  | Reset in the middle of a burst shall abort immediately and discard pending bytes; the gap guarantee does not apply across reset. | CHK-035:PASS | — | **VERIFIED** |
| SPI-14-11 |  | An illegal PARA_SPI_CLK_DIV shall cause an elaboration error. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| SPI-14-12 |  | o_rsp_data shall be 8'h00 after reset and otherwise keep the last loaded byte while not valid. | CHK-016:PASS, CHK-021:PASS | — | **VERIFIED** |
| SPI-14-16 | REQ-CMD-006 | For D = 1 in Idle, o_cmd_ready shall equal NOT o_rsp_valid from the cycle o_cs_n rises. | CHK-003:PASS | — | **VERIFIED** |
| SPI-14-20 |  | There is no Pause timeout; o_cs_n shall stay low in Pause until the next command. | CHK-010:PASS, CHK-031:PASS | — | **VERIFIED** |
| SPI-14-21 | REQ-RST-011 | The master shall not enforce o_cs_n high for at least D cycles after reset release; the minimum gap is not guaranteed across reset. | CHK-018:PASS, CHK-035:PASS | — | **VERIFIED** |

## Mutants

| ID | File:line | Operator | Status | Caught by | Rules | Equivalent? |
|---|---|---|---|---|---|---|
| M01 | m_spi_master.sv:215 | eq_to_ne | killed | CHK-023, CHK-025, CHK-020, CHK-022, CHK-011, CHK-012, CHK-014, CHK-010, CHK-007, CHK-004, CHK-005, test_chk_028_no_hands | SPI-3-01, SPI-7.8-01, SPI-7.8-06, SPI-7.8-02, SPI-3-02 |  |
| M02 | m_spi_master.sv:129 | and_to_or | killed | CHK-011, CHK-012, CHK-013, CHK-014, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test | SPI-7.5-03, SPI-7.5-04, SPI-7.5-05, SPI-7.5-07, SPI-1.2-01 |  |
| M03 | m_spi_master.sv:129 | ne_to_eq | killed | CHK-011, CHK-012, CHK-013, CHK-014, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test | SPI-7.5-03, SPI-7.5-04, SPI-7.5-07, SPI-7.3-04, SPI-7.3-05 |  |
| M04 | m_spi_master.sv:253 | negate_if | killed | CHK-007, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test_chk_030_single_byte_bursts | SPI-3-06, SPI-7.2-03, SPI-8-04, SPI-7.2-02, SPI-8-07 |  |
| M05 | m_spi_master.sv:325 | one_to_zero | killed | CHK-020, CHK-022, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test_chk_030_single_by | SPI-7.7-01, SPI-1.1-02, SPI-8-03, SPI-5-09, SPI-7.7-02 |  |
| M06 | m_spi_master.sv:187 | zero_to_one | survived |  |  | formal PROVEN (claimed: r_last is always overwritten at the accepting handshake in Idle before any use. It only affects cmd_ready in XFER and the XFER end, and cmd_ready in Idle does n) |
| M07 | m_spi_master.sv:323 | or_to_and | killed | CHK-020, CHK-022, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test_chk_030_single_by | SPI-7.7-03, SPI-10-13, SPI-7.7-04, SPI-1.2-09, SPI-7.7-11 |  |
| M08 | m_spi_master.sv:117 | eq_to_ne | killed | CHK-020, CHK-022, CHK-011, CHK-012, CHK-013, CHK-014, CHK-004, test_chk_028_no_handshake_no_effect, test_chk_029_no_comb | SPI-3-02, SPI-7.4-01, SPI-7.4-02, SPI-3-01, SPI-1.2-05 |  |
| M09 | m_spi_master.sv:121 | and_to_or | killed | CHK-023, CHK-025, CHK-020, CHK-021, CHK-022, CHK-011, CHK-012, CHK-013, CHK-014, CHK-007, CHK-004, CHK-005, test_chk_028 | SPI-3-01, SPI-7.1-10, SPI-7.7-01, SPI-7.8-06, SPI-7.8-02 |  |
| M10 | m_spi_master.sv:130 | ne_to_eq | killed | CHK-011, CHK-012, CHK-013, CHK-014, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test | SPI-7.5-03, SPI-7.5-08, SPI-7.5-06, SPI-7.5-09, SPI-7.8-03 |  |
| M11 | m_spi_master.sv:320 | negate_if | killed | CHK-020, CHK-021, CHK-018, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test_chk_030_ | SPI-7.7-01, SPI-8-03, SPI-1.1-02, SPI-7.7-02, SPI-8-16 |  |
| M12 | m_spi_master.sv:329 | one_to_zero | killed | test_chk_036_held_byte_backpressure | SPI-1.2-09, SPI-7.7-05, SPI-7.7-06, SPI-8-14, SPI-10-06 |  |
| M13 | m_spi_master.sv:316 | zero_to_one | killed | CHK-020, CHK-015, CHK-016, CHK-018, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test | SPI-6.2-05, SPI-5-08, SPI-6.2-01, SPI-6.2-10, SPI-10-12 |  |
| M14 | m_spi_master.sv:113 | eq_to_ne | killed | CHK-023, CHK-024, CHK-025, CHK-020, CHK-021, CHK-022, CHK-015, CHK-016, CHK-018, CHK-011, CHK-012, CHK-013, CHK-014, CHK | SPI-1.2-05, SPI-4-02, SPI-3-02, SPI-7.4-01, SPI-10-16 |  |
| M15 | m_spi_master.sv:164 | and_to_or | killed | CHK-023, CHK-024, CHK-025, CHK-020, CHK-021, CHK-022, CHK-011, CHK-012, CHK-013, CHK-014, CHK-007, CHK-004, CHK-005, tes | SPI-7.1-10, SPI-7.1-09, SPI-7.1-06, SPI-8-12, SPI-14-03 |  |
| M16 | m_spi_master.sv:315 | negate_if | killed | CHK-020, CHK-021, CHK-022, CHK-015, CHK-016, CHK-018, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational | SPI-6.2-05, SPI-6.2-01, SPI-5-08, SPI-6.2-10, SPI-10-12 |  |
| M17 | m_spi_master.sv:205 | one_to_zero | killed | CHK-003, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test_chk_030_single_byte_bursts | SPI-7.1-07, SPI-7.2-05, SPI-8-05, SPI-14-02, SPI-8-08 |  |
| M18 | m_spi_master.sv:159 | zero_to_one | survived |  |  | formal PROVEN (claimed: The case covers all four r_state values and every branch overwrites cmd_ready, so the default assignment is never visible.) |
| M19 | m_spi_master.sv:140 | eq_to_ne | killed | CHK-011, CHK-012, CHK-013, CHK-014, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test | SPI-7.3-01, SPI-7.3-04, SPI-7.5-04, SPI-7.3-03, SPI-1.2-04 |  |
| M20 | m_spi_master.sv:151 | and_to_or | killed | CHK-020, CHK-021, CHK-022, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test_chk_030_ | SPI-7.7-10, SPI-7.7-04, SPI-7.7-07, SPI-7.7-08, SPI-1.1-02 |  |
| M21 | m_spi_master.sv:215 | negate_if | killed | CHK-023, CHK-025, CHK-020, CHK-022, CHK-011, CHK-012, CHK-014, CHK-010, CHK-007, CHK-004, CHK-005, test_chk_028_no_hands | SPI-3-01, SPI-7.8-01, SPI-7.8-06, SPI-7.8-02, SPI-3-02 |  |
| M22 | m_spi_master.sv:258 | one_to_zero | killed | CHK-007, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test_chk_030_single_byte_bursts | SPI-3-06, SPI-7.2-03, SPI-8-04, SPI-7.2-02, SPI-8-07 |  |
| M23 | m_spi_master.sv:336 | zero_to_one | killed | test_chk_036_held_byte_backpressure | SPI-7.7-06, SPI-7.7-05, SPI-1.2-09, SPI-8-14, SPI-7.7-12 |  |
| M24 | m_spi_master.sv:121 | eq_to_ne | killed | CHK-023, CHK-025, CHK-020, CHK-021, CHK-022, CHK-011, CHK-012, CHK-013, CHK-014, CHK-007, CHK-004, CHK-005, test_chk_028 | SPI-3-01, SPI-7.8-06, SPI-7.8-02, SPI-7.1-10, SPI-7.7-01 |  |
| M25 | m_spi_master.sv:125 | and_to_or | killed | CHK-020, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test_chk_030_single_byte_bursts | SPI-7.6-01, SPI-7.6-02, SPI-7.3-04, SPI-7.3-05, SPI-5-15 |  |
| M26 | m_spi_master.sv:281 | negate_if | killed | CHK-011, CHK-012, CHK-013, CHK-014, CHK-010, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_pa | SPI-7.1-02, SPI-5-06, SPI-7.5-01, SPI-7.1-03, SPI-1.2-01 |  |
| M27 | m_spi_master.sv:180 | one_to_zero | killed | CHK-015, CHK-016, CHK-017, CHK-018, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test | SPI-6.2-02, SPI-5-13, SPI-6.2-01, SPI-10-09, SPI-10-11 |  |
| M28 | m_spi_master.sv:318 | zero_to_one | killed | CHK-020, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test_chk_030_single_byte_bursts | SPI-6.2-10, SPI-10-12, SPI-6.2-05, SPI-6.2-01, SPI-10-10 |  |
| M29 | m_spi_master.sv:125 | eq_to_ne | killed | CHK-020, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test_chk_030_single_byte_bursts | SPI-7.6-01, SPI-7.6-02, SPI-7.3-04, SPI-7.3-05, SPI-5-15 |  |
| M30 | m_spi_master.sv:164 | and_to_or | killed | CHK-023, CHK-024, CHK-025, CHK-020, CHK-021, CHK-022, CHK-011, CHK-012, CHK-013, CHK-014, CHK-010, CHK-007, CHK-004, CHK | SPI-7.1-10, SPI-7.1-09, SPI-7.1-06, SPI-8-12, SPI-14-03 |  |
| M31 | m_spi_master.sv:332 | negate_if | killed | CHK-020, CHK-021, CHK-022, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test_chk_030_ | SPI-7.7-04, SPI-7.7-06, SPI-7.7-07, SPI-7.7-10, SPI-1.1-02 |  |
| M32 | m_spi_master.sv:233 | one_to_zero | killed | CHK-023, CHK-020, CHK-011, CHK-012, CHK-014, CHK-007, CHK-009, CHK-004, CHK-005, test_chk_028_no_handshake_no_effect, te | SPI-1.2-05, SPI-4-02, SPI-3-02, SPI-7.4-01, SPI-10-16 |  |
| M33 | m_spi_master.sv:181 | zero_to_one | survived |  |  | formal PROVEN (claimed: r_sclk reset value 1 or 0 is hidden while o_cs_n=1, because o_sclk = i_cpol in that case. r_sclk is loaded with i_cpol at the burst-start handshake before o_cs_) |
| M34 | m_spi_master.sv:150 | and_to_or | killed | CHK-024, CHK-025, CHK-020, CHK-021, CHK-018, CHK-011, CHK-013, CHK-014, CHK-010, CHK-006, CHK-007, CHK-003, CHK-005, tes | SPI-7.1-01, SPI-6.2-07, SPI-10-05, SPI-7.1-03, SPI-7.1-04 |  |
| M35 | m_spi_master.sv:303 | negate_if | killed | CHK-020, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test_chk_030_single_byte_bursts | SPI-7.6-01, SPI-7.6-02, SPI-6.2-01, SPI-5-09, SPI-7.6-05 |  |
| M36 | m_spi_master.sv:255 | one_to_zero | killed | CHK-007, test_chk_028_no_handshake_no_effect, test_chk_029_no_combinational_input_paths, test_chk_030_single_byte_bursts | SPI-7.2-03, SPI-3-06, SPI-8-04, SPI-7.2-02, SPI-8-07 |  |

## Not verified by this run

- Formal: the assertions were checked by SymbiYosys under the environment assumptions (work/formal.md); a BOUNDED result holds only up to its depth. CDC/RDC, STA, synthesis and DFT checks are outside this flow.
- Rules marked NOT_VERIFIED_BY_SIM carry the contract's reason (static, structural, not observable...).
- Only the configurations of the run set above were simulated; code coverage is merged over its runs, mutation testing used the primary run base.s1.

# Verification report — apb_tlul_bridge

Generated 2026-11-08T10:49:41+00:00 by NNC Pipeline.

## Summary

| Item | Result |
|---|---|
| Rules | 232 — {'NOT_VERIFIED_BY_SIM': 63, 'VERIFIED': 169} |
| Checks | 31 — {'PASS': 31} |
| Tests | {'pass': 17} |
| Integration | OK |
| Code coverage (RTL), line | 96.0 % (192/200 lines) |
| Code coverage (RTL), block | 95.6 % (43/45 statement blocks and branch arms) |
| Code coverage (RTL), expression | 100.0 % (47/47 condition terms) |
| Code coverage (RTL), toggle | 95.9 % (1920/2002 bit toggles 0->1 and 1->0) |
| Code coverage (RTL), functional | 100.0 % (40/40 cover points of the specification) |
| Mutation score | 100.0 % (36 killed / 0 survived / 0 not compiled) |
| Coverage target | functional 100.0 %: **target_met** (baseline 95.0 % -> 100.0 %, work/coverage.md) |
| Triage | no failure to analyse |
| Agent cost | US$18.9336 in 81 calls (A1 0.8682, A10 0.416, A11 1.3515, A12 0.2791, A2 0.7102, A3 0.3887, A4 3.2454, A5 1.0603, A6 0.2892, A7 10.3255) |

## Sign-off conditions

| Condition | State |
|---|---|
| Gates G1-G3 approved | met — approved on delegation by an agent: a person should confirm |
| Interface conformance of the DUT | met |
| Every selected check PASS (no FAIL, NOT_HIT, NOT_RUN) | met |
| Every planned check selected | met |
| Every rule in a check or declared not verifiable | met |
| Mutation run | met |
| Per-requirement mutation score >= 85 % | met — 72 rules with attributed mutants |
| Coverage target functional 100.0 % | met — target_met |

## Gates

| Gate | State | Detail |
|---|---|---|
| G1_rules | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-07T18:06:13+00:00 |
| G2_contract | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-08T10:00:45+00:00 |
| G3_verif_sources | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-08T10:47:56+00:00 |
| G4_signoff | PENDING | artifacts ready for review |

## Checks

| Check | Kind | Title | Status | Evidence |
|---|---|---|---|---|
| CHK-001 | assertion | PREADY only in an APB Access cycle | **PASS** | hits 13715, fails 0 |
| CHK-002 | assertion | PREADY is a one-cycle pulse | **PASS** | hits 13715, fails 0 |
| CHK-003 | assertion | PSLVERR only with PREADY | **PASS** | hits 5019, fails 0 |
| CHK-004 | assertion | PRDATA holds its value outside PREADY | **PASS** | hits 95936, fails 0 |
| CHK-005 | assertion | PRDATA is zero on write and error completions | **PASS** | hits 8852, fails 0 |
| CHK-006 | assertion | Legal Setup launches the request from flops in the first Access cycle | **PASS** | hits 9845, fails 0 |
| CHK-007 | assertion | Illegal Setup completes locally in the first Access cycle with no request | **PASS** | hits 3880, fails 0 |
| CHK-008 | assertion | One request at a time, none before the APB completion | **PASS** | hits 34101, fails 0 |
| CHK-009 | assertion | a_valid only inside an APB Access phase before PREADY | **PASS** | hits 34101, fails 0 |
| CHK-010 | assertion | Accepted TL-UL response is checked and mapped to the APB completion one cycle later | **PASS** | hits 9838, fails 0 |
| CHK-011 | assertion | PREADY only caused by an illegal Setup or a counted response (orphans have no APB effect) | **PASS** | hits 13715, fails 0 |
| CHK-012 | assertion | Output values while reset is asserted | **PASS** | hits 196, fails 0 |
| CHK-013 | assertion | d_ready constant 1 after the first edge following reset release | **PASS** | hits 109651, fails 0 |
| CHK-014 | assertion | A request starts only after a legal Setup | **PASS** | hits 9842, fails 0 |
| CHK-015 | assertion | Channel A held and stable until accepted | **PASS** | hits 24260, fails 0 |
| CHK-016 | assertion | a_valid drops after the handshake (accepted once) | **PASS** | hits 9841, fails 0 |
| CHK-017 | assertion | Constant A-channel fields and legal opcode, size, mask and address | **PASS** | hits 109884, fails 0 |
| CHK-018 | test | Local error for unsupported PSTRB and misaligned address | **PASS** | test_chk_018_local_error |
| CHK-019 | test | Device error response (d_error) on read and write | **PASS** | test_chk_019_device_error |
| CHK-020 | test | Wrong d_opcode and wrong d_source responses | **PASS** | test_chk_020_wrong_opcode_source |
| CHK-021 | test | Orphan responses are discarded | **PASS** | test_chk_021_orphan_responses |
| CHK-022 | test | Device never responds: no timeout, requester waits | **PASS** | test_chk_022_no_response_no_timeout |
| CHK-023 | test | Aligned full-strobe write to a prompt device | **PASS** | test_chk_023_prompt_write |
| CHK-024 | test | Aligned read to a prompt device, PSTRB ignored | **PASS** | test_chk_024_prompt_read |
| CHK-025 | test | Ignored inputs PPROT, d_param, d_size, d_sink, d_user | **PASS** | test_chk_025_ignored_inputs |
| CHK-026 | test | Channel A back pressure and response delay | **PASS** | test_chk_026_backpressure_delay |
| CHK-027 | test | Response in the acceptance cycle | **PASS** | test_chk_027_same_cycle_response |
| CHK-028 | test | Back-to-back transfers with PSEL held high and with gaps | **PASS** | test_chk_028_back_to_back |
| CHK-029 | test | Constrained-random regression with scoreboard and coverage | **PASS** | test_chk_029_random_scoreboard |
| CHK-030 | test | Power-on reset, synchronous release and asynchronous assertion | **PASS** | test_chk_030_reset |
| CHK-031 | test | Reset during a transfer abandons it | **PASS** | test_chk_031_reset_abandons_transfer |

## Requirement traceability (RTM)

| Rule | Spec ref | Statement | Checks | Mutation | Status |
|---|---|---|---|---|---|
| BR-T1-03 | REQ-ERR-001, REQ-ERR-002 | A write with PSTRB other than 4'b1111 must complete with PSLVERR = 1. | CHK-007:PASS, CHK-018:PASS | 100.0 % (4/4) | **VERIFIED** |
| BR-T1-04 | REQ-ERR-001, REQ-ERR-002 | Any access with a misaligned address must complete with PSLVERR = 1. | CHK-007:PASS, CHK-018:PASS | 100.0 % (3/3) | **VERIFIED** |
| BR-T1-05 | REQ-ERR-001, REQ-ERR-002 | No TL-UL request is issued for a write with unsupported PSTRB or for a misaligned access. | CHK-007:PASS, CHK-018:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-1.1-01 |  | Each APB transfer must become exactly one TL-UL request, and the TL-UL response must become the APB completion. | CHK-010:PASS, CHK-011:PASS, CHK-014:PASS, CHK-029:PASS | 100.0 % (6/6) | **VERIFIED** |
| BR-1.1-02 | REQ-FUNC-001, REQ-PERF-001 | The TL-UL request must be launched from flip-flops in the first APB access cycle (early launch). | CHK-006:PASS, CHK-023:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-1.1-04 |  | The bridge does not support partial writes (PSTRB other than 4'b1111), byte or half-word accesses, TL-UL bursts, or multiple outstanding requests. | CHK-008:PASS, CHK-017:PASS | — | **VERIFIED** |
| BR-1.3-01 | REQ-FUNC-002 | An APB4 full-strobe write must be converted to a TL-UL PutFullData request. | CHK-023:PASS | — | **VERIFIED** |
| BR-1.3-02 | REQ-FUNC-003 | An APB4 read must be converted to a TL-UL Get request. | CHK-024:PASS | — | **VERIFIED** |
| BR-1.3-03 | REQ-ERR-001, REQ-ERR-002 | The bridge must give a local error response for an unsupported strobe or misaligned address. | CHK-018:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-1.3-04 | REQ-ERR-003, REQ-ERR-005 | The bridge must check the TL-UL response and map errors to PSLVERR. | CHK-010:PASS, CHK-019:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-1.3-05 | REQ-FUNC-008, REQ-PERF-004 | The bridge must support back-to-back APB transfers with PSEL held high. | CHK-028:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-2.3-01 |  | The bridge must reject a write with PSTRB other than 4'b1111 by responding with PSLVERR. | CHK-007:PASS, CHK-018:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-2.3-02 |  | The bridge must reject a transfer with misaligned PADDR by responding with PSLVERR. | CHK-007:PASS, CHK-018:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-2.3-03 |  | PPROT must be accepted and ignored; it must not affect bridge behavior. | CHK-025:PASS | — | **VERIFIED** |
| BR-2.3-04 |  | The TL-UL host side must use a_size = 2 only, with 32-bit data and no bursts. | CHK-017:PASS | — | **VERIFIED** |
| BR-2.3-05 |  | a_user must be driven to zero, with no integrity. | CHK-017:PASS | — | **VERIFIED** |
| BR-3-01 | REQ-FUNC-001 | The bridge shall capture the request at the rising edge ending the Setup cycle. | CHK-006:PASS, CHK-023:PASS | 100.0 % (4/4) | **VERIFIED** |
| BR-3-02 | REQ-FUNC-001 | The bridge shall present the request on TL-UL channel A from flip-flops in the next cycle (first Access cycle). | CHK-006:PASS, CHK-023:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-3-03 | REQ-FUNC-002 | The bridge shall convert it into one PutFullData (a_opcode = 3'b000) with a_size = 2, a_mask = 4'b1111, a_address = PADDR and a_data = PWDATA. | CHK-006:PASS, CHK-023:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-3-04 | REQ-FUNC-003 | The bridge shall convert it into one TL-UL Get (a_opcode = 3'b100) with a_size = 2, a_mask = 4'b1111 and a_address = PADDR. | CHK-006:PASS, CHK-024:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-3-05 | REQ-FUNC-003 | PSTRB shall be ignored on reads. | CHK-006:PASS, CHK-024:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-3-06 | REQ-FUNC-004 | The bridge shall have at most one TL-UL request outstanding. | CHK-008:PASS, CHK-029:PASS | 100.0 % (4/4) | **VERIFIED** |
| BR-3-07 | REQ-FUNC-004 | The bridge shall start no new TL-UL request before the APB completion of the previous transfer. | CHK-008:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-3-08 | REQ-FUNC-005 | The bridge shall keep o_tlul_a_valid high and channel A stable. | CHK-015:PASS, CHK-026:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-3-09 | REQ-FUNC-006 | The bridge shall return the TL-UL d_data on o_apb_prdata. | CHK-010:PASS, CHK-024:PASS | 100.0 % (6/6) | **VERIFIED** |
| BR-3-10 | REQ-FUNC-006 | The bridge shall drive o_apb_prdata to 0. | CHK-005:PASS, CHK-019:PASS, CHK-023:PASS | — | **VERIFIED** |
| BR-3-11 | REQ-FUNC-007 | The bridge shall discard the response without any effect on the APB side. | CHK-011:PASS, CHK-021:PASS | 100.0 % (6/6) | **VERIFIED** |
| BR-3-12 | REQ-FUNC-008 | The bridge shall detect the Setup phase from levels i_apb_psel = 1 and i_apb_penable = 0, not from an edge of i_apb_psel. | CHK-006:PASS, CHK-028:PASS | 100.0 % (3/3) | **VERIFIED** |
| BR-3-14 | REQ-FUNC-008 | Every combination of read, write and error transfers shall be supported back to back. | CHK-028:PASS | — | **VERIFIED** |
| BR-3-15 | REQ-IF-001 | The bridge shall expose exactly the APB4 Completer signals listed in section 6.2 and no other APB signal. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-3-16 | REQ-IF-002 | The bridge shall expose exactly the TL-UL host signals listed in section 6.2 and no others. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-3-17 | REQ-IF-003 | Such output ports shall be driven directly by a flip-flop Q pin with no combinational logic; never-changing outputs are constant tie-offs. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-3-18 | REQ-IF-004 | The bridge shall assert o_apb_pready for exactly one cycle per transfer, and only in an Access cycle (psel = 1, penable = 1). | CHK-001:PASS, CHK-002:PASS | 100.0 % (3/3) | **VERIFIED** |
| BR-3-19 | REQ-IF-004 | o_apb_pslverr shall be 1 only while o_apb_pready is 1. | CHK-003:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-3-20 | REQ-IF-005 | The bridge shall drive a_param = 3'b000, a_size = 2'b10, a_mask = 4'b1111, a_source = PARA_SRC_ID and a_user = '0. | CHK-017:PASS | — | **VERIFIED** |
| BR-3-21 | REQ-IF-006 | The bridge shall drive o_tlul_d_ready low. | CHK-012:PASS, CHK-030:PASS | 100.0 % (8/8) | **VERIFIED** |
| BR-3-22 | REQ-IF-006 | The bridge shall drive o_tlul_d_ready high and keep it high. | CHK-013:PASS, CHK-030:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-3-23 | REQ-IF-007 | APB-facing and TL-UL-facing logic shall be in two separate modules connected only through the internal interface of section 5.1. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-3-24 | REQ-ERR-001 | The bridge shall issue no TL-UL request and complete with PREADY = 1 and PSLVERR = 1 in the first Access cycle. | CHK-007:PASS, CHK-018:PASS | 100.0 % (4/4) | **VERIFIED** |
| BR-3-25 | REQ-ERR-002 | The bridge shall issue no TL-UL request and complete with PREADY = 1 and PSLVERR = 1 in the first Access cycle. | CHK-007:PASS, CHK-018:PASS | 100.0 % (4/4) | **VERIFIED** |
| BR-3-26 | REQ-ERR-003 | The bridge shall complete the APB transfer with PSLVERR = 1. | CHK-010:PASS, CHK-019:PASS | — | **VERIFIED** |
| BR-3-27 | REQ-ERR-004 | The bridge shall complete the APB transfer with PSLVERR = 1. | CHK-010:PASS, CHK-020:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-3-28 | REQ-ERR-005 | The bridge shall complete the APB transfer with PSLVERR = 1. | CHK-010:PASS, CHK-020:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-3-29 | REQ-CLK-001 | The bridge shall operate in one clock domain, i_clk_core, for both interfaces with no clock-domain crossing. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-3-30 | REQ-RESET-001 | The bridge shall use active-low reset i_rst_n_core with asynchronous assertion. | CHK-030:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-3-31 | REQ-RESET-001 | The bridge shall drive the listed outputs to 0 while reset is asserted. | CHK-012:PASS, CHK-030:PASS | 100.0 % (8/8) | **VERIFIED** |
| BR-3-32 | REQ-RESET-002 | The bridge shall abandon the transfer and send no APB completion for it after reset release. | CHK-011:PASS, CHK-031:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-3-33 | REQ-PARAM-001 | The bridge shall accept only parameter values listed in section 8; an illegal value shall be reported at elaboration. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-3-34 | REQ-PERF-001 | The APB Access phase shall last 3 cycles (2 wait states). | CHK-023:PASS, CHK-024:PASS | — | **VERIFIED** |
| BR-3-35 | REQ-PERF-002 | The APB Access phase shall last 2 cycles (1 wait state). | CHK-027:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-3-36 | REQ-ERR-001, REQ-ERR-002, REQ-PERF-003 | The completion shall last 1 Access cycle with no wait state. | CHK-007:PASS, CHK-018:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-3-37 | REQ-ERR-001, REQ-ERR-002, REQ-PERF-003 | A new Setup phase shall be accepted in the cycle after PREADY. | CHK-018:PASS, CHK-028:PASS | — | **VERIFIED** |
| BR-3-38 | REQ-FUNC-008, REQ-PERF-004 | Setup-to-Setup interval shall be the minimum: 4 cycles with prompt device, 3 with same-cycle response, 2 after local error, with no idle cycle added. | CHK-028:PASS | — | **VERIFIED** |
| BR-3-39 | REQ-RTL-001 | The RTL shall comply with REF-003 and use the hierarchy of section 14.2. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-3-40 | REQ-VER-001 | An APB protocol checker and the REF-005 TL-UL protocol checker shall be bound to the ports. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-3-41 | REQ-DFT-001 | The RTL shall be scan-insertable: no latch, combinational loop, internal tri-state, clock gating, or gated/derived clock. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-4-02 |  | PARA_ADDR_W must not be configured with a value outside the range 16 to 32. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-5.1-02 |  | m_apb_if must assert w_req_launch to m_tlul_if during the Setup phase of a legal request so channel A is loaded at the coming edge. | CHK-006:PASS | — | **VERIFIED** |
| BR-5.1-03 |  | w_resp_rdata must be forced to 0 for writes and for errors. | CHK-005:PASS | — | **VERIFIED** |
| BR-5.3-01 |  | The request is captured at the end of Setup straight into channel A flops, and channel A is valid in the first Access cycle, one cycle after Setup, with no buffer stage. | CHK-006:PASS, CHK-023:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-5.3-02 |  | At the end of the Setup phase a legal request must be loaded into the A-channel flops and reg_a_valid set. | CHK-006:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-5.3-04 |  | In A1, o_tlul_a_valid must be 1 with the converted request and o_tlul_d_ready must be 1. | CHK-006:PASS, CHK-013:PASS, CHK-023:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-5.3-06 |  | At the end of A2 the response is checked and loaded into reg_prdata, reg_pslverr and reg_pready. | CHK-010:PASS | 100.0 % (5/5) | **VERIFIED** |
| BR-5.3-07 |  | In A3, o_apb_pready must be 1 with o_apb_prdata and o_apb_pslverr driven directly from flops, and the transfer ends at the end of A3. | CHK-010:PASS, CHK-023:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-5.3-08 |  | If the device responds in A1, the response must be loaded at the end of A1 and PREADY must be 1 in A2. | CHK-010:PASS, CHK-027:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-5.3-10 |  | The bridge must support back-to-back transfers without an idle cycle, recognizing Setup by levels i_apb_psel=1 and i_apb_penable=0 while the APB FSM is idle, not by a psel rising edge. | CHK-028:PASS | — | **VERIFIED** |
| BR-5.3-11 |  | The APB FSM is in ENUM_ST_DONE in the PREADY cycle and in ENUM_ST_IDLE in the next cycle, so flops and FSMs are free for the next capture. | CHK-028:PASS | — | **VERIFIED** |
| BR-5.3-12 |  | Next transfers must start exactly like the first one when i_apb_psel is released for one or more cycles in between. | CHK-028:PASS | — | **VERIFIED** |
| BR-5.4-01 |  | At most one TL-UL request is outstanding, and its a_source is PARA_SRC_ID. | CHK-008:PASS, CHK-029:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-5.4-02 |  | o_tlul_a_valid must be high only in TL-UL FSM state ENUM_ST_REQ. | CHK-009:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-5.4-03 |  | Channel A must not change while o_tlul_a_valid is high and i_tlul_a_ready is low. | CHK-015:PASS, CHK-026:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-5.4-04 |  | o_apb_pready must be high only in APB FSM state ENUM_ST_DONE, for one cycle. | CHK-002:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-5.4-05 |  | No TL-UL request may be issued for an illegal APB request. | CHK-007:PASS, CHK-014:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-5.4-06 |  | The TL-UL FSM is idle whenever the APB FSM is idle. | CHK-009:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-6.2-01 |  | i_apb_paddr bits [1:0] must be 0. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| BR-6.2-02 |  | i_apb_pstrb must be 4'b1111 for a write. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| BR-6.2-03 |  | o_apb_pready must be high for exactly one cycle per transfer and 0 in reset. | CHK-001:PASS, CHK-002:PASS, CHK-012:PASS | 100.0 % (3/3) | **VERIFIED** |
| BR-6.2-04 |  | o_apb_prdata is valid with o_apb_pready and holds its last value otherwise; reset value is 0. | CHK-004:PASS, CHK-012:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-6.2-05 |  | o_apb_pslverr must not be high unless o_apb_pready is high. | CHK-003:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-6.2-06 |  | o_tlul_a_valid is set at the Setup edge and held until i_tlul_a_ready; it is 0 in reset. | CHK-006:PASS, CHK-012:PASS, CHK-015:PASS, CHK-016:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-6.2-07 |  | o_tlul_a_opcode bit 2 is 1 for Get and bits [1:0] are constant 0; it must be stable while o_tlul_a_valid is high. | CHK-015:PASS, CHK-017:PASS | — | **VERIFIED** |
| BR-6.2-08 |  | o_tlul_a_param must always be 3'b000. | CHK-017:PASS | — | **VERIFIED** |
| BR-6.2-09 |  | o_tlul_a_size must always be 2'b10. | CHK-017:PASS | — | **VERIFIED** |
| BR-6.2-10 |  | o_tlul_a_source must always equal PARA_SRC_ID. | CHK-017:PASS | — | **VERIFIED** |
| BR-6.2-11 |  | o_tlul_a_address bits [1:0] must be constant 0 and the address must be stable while o_tlul_a_valid is high. | CHK-015:PASS, CHK-017:PASS | — | **VERIFIED** |
| BR-6.2-12 |  | o_tlul_a_mask must always be 4'b1111. | CHK-017:PASS | — | **VERIFIED** |
| BR-6.2-13 |  | o_tlul_a_data must be a copy of PWDATA and stable while o_tlul_a_valid is high. | CHK-006:PASS, CHK-015:PASS | — | **VERIFIED** |
| BR-6.2-14 |  | o_tlul_a_user must always be '0. | CHK-017:PASS | — | **VERIFIED** |
| BR-6.2-15 |  | o_tlul_d_ready must be 0 in reset and constant 1 after the first clock edge following reset release. | CHK-012:PASS, CHK-013:PASS | 100.0 % (4/4) | **VERIFIED** |
| BR-6.3-01 |  | Setup phase lasts one cycle with PSEL=1 and PENABLE=0; the Access phase starts next cycle and lasts until PREADY is high. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| BR-6.3-02 |  | PADDR, PWRITE, PWDATA and PSTRB stay unchanged from Setup until PREADY. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| BR-6.3-04 |  | The bridge ignores PSTRB on reads. | CHK-024:PASS | — | **VERIFIED** |
| BR-6.3-05 | REQ-FUNC-008, REQ-PERF-004 | Back-to-back transfers with i_apb_psel held high are accepted exactly like the first transfer with the same results. | CHK-028:PASS | — | **VERIFIED** |
| BR-6.3-06 |  | The bridge issues one TL-UL request at a time. | CHK-008:PASS | — | **VERIFIED** |
| BR-6.3-07 |  | The TL-UL request stays stable until accepted. | CHK-015:PASS, CHK-026:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-6.3-08 | REQ-FUNC-007 | The bridge accepts responses at any time and discards a response not belonging to an accepted request, with no APB effect. | CHK-011:PASS, CHK-021:PASS | 100.0 % (3/3) | **VERIFIED** |
| BR-6.3-09 |  | The bridge supports a TL-UL response in the same cycle as the request acceptance. | CHK-027:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-6.3-10 | REQ-FUNC-002 | The bridge issues PutFullData, size 2, mask 4'b1111 and completes normally. | CHK-023:PASS | — | **VERIFIED** |
| BR-6.3-11 | REQ-ERR-001 | PREADY=1 with PSLVERR=1 in the first Access cycle and no TL-UL request is issued. | CHK-018:PASS | — | **VERIFIED** |
| BR-6.3-12 | REQ-FUNC-003 | The bridge issues Get, size 2, mask 4'b1111 and returns data on PRDATA. | CHK-024:PASS | — | **VERIFIED** |
| BR-6.3-13 | REQ-ERR-002 | PREADY=1 with PSLVERR=1 in the first Access cycle and no TL-UL request is issued. | CHK-018:PASS | — | **VERIFIED** |
| BR-6.3-14 | REQ-ERR-003 | PSLVERR=1 and PRDATA=0. | CHK-010:PASS, CHK-019:PASS | — | **VERIFIED** |
| BR-6.3-15 | REQ-ERR-004, REQ-ERR-005 | PSLVERR=1 and PRDATA=0. | CHK-010:PASS, CHK-020:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-7.2-01 |  | A CDC tool run must report zero crossings, since there is one clock domain and one reset domain. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-7.3-01 |  | i_rst_n_core is active-low, asserted asynchronously, and deasserted synchronously to i_clk_core (synchronous release provided by the SoC reset controller). | CHK-030:PASS | — | **VERIFIED** |
| BR-7.3-02 |  | Every flip-flop, including both FSM state registers and the payload registers, must be asynchronously reset; FSMs go to ENUM_ST_IDLE and all listed registers to 0. | CHK-030:PASS, CHK-031:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-7.3-03 |  | After reset, o_tlul_a_opcode must be 3'b000, o_tlul_a_address 0, o_tlul_a_data 0 and o_tlul_a_valid 0. | CHK-012:PASS, CHK-030:PASS | 100.0 % (7/7) | **VERIFIED** |
| BR-7.3-05 |  | The transfer is abandoned, and the SoC resets the APB Requester and TL-UL device together with the bridge. | CHK-031:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-7.4-01 |  | The IP resides in the SoC always-on domain and has no isolation, retention or power sequencing of its own. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-8-01 |  | PARA_ADDR_W (default 32, legal range 16 to 32) shall set the width of both i_apb_paddr and o_tlul_a_address. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-8-02 |  | PARA_SRC_W (default 8, legal range 1 to 8) shall set the width of o_tlul_a_source and i_tlul_d_source. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-8-03 |  | PARA_SRC_ID shall fit in PARA_SRC_W bits, i.e. lie in the range 0 to 2^PARA_SRC_W - 1. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-8-04 |  | The value of o_tlul_a_source on every request and the expected i_tlul_d_source shall equal PARA_SRC_ID (default 0). | CHK-010:PASS, CHK-017:PASS, CHK-020:PASS | — | **VERIFIED** |
| BR-8-05 |  | o_tlul_a_user shall have width PARA_A_USER_W (default 1, range 1 to 32) and its bits shall always be driven to zero. | CHK-017:PASS | — | **VERIFIED** |
| BR-8-06 |  | PARA_D_SINK_W (default 1, range 1 to 4) shall set the width of i_tlul_d_sink, which has no behavioral effect. | CHK-025:PASS | — | **VERIFIED** |
| BR-8-07 |  | PARA_D_USER_W (default 1, range 1 to 32) shall set the width of i_tlul_d_user, which has no behavioral effect. | CHK-025:PASS | — | **VERIFIED** |
| BR-8-08 |  | m_tlul_if shall use fixed non-overridable constants LPARA_A_SIZE = 2, LPARA_A_MASK = 4'b1111 and LPARA_D_ACK_DATA = 1 (AccessAckData d_opcode). | CHK-010:PASS, CHK-017:PASS, CHK-020:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-8-09 |  | An illegal parameter value shall be reported at elaboration of the verification source set. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-9-01 |  | Byte lane i of the 32-bit data bus carries bits [8i+7:8i], and PSTRB[i] and a_mask[i] refer to the same lane. | not verified: covered_by_other_check | — | **NOT_VERIFIED_BY_SIM** |
| BR-9-02 | REQ-ERR-002 | APB address bits [1:0] shall be 0 (word-aligned byte address). | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| BR-9-03 | REQ-ERR-002 | Bits [PARA_ADDR_W-1:2] of the APB address are copied to a_address[PARA_ADDR_W-1:2], and a_address[1:0] is 2'b00. | CHK-006:PASS | — | **VERIFIED** |
| BR-9-04 | REQ-ERR-002 | A non-zero value in APB address bits [1:0] shall give PSLVERR (REQ-ERR-002). | CHK-007:PASS, CHK-018:PASS | — | **VERIFIED** |
| BR-9-05 |  | a_opcode shall be 3'b000 (PutFullData) for writes and 3'b100 (Get) for reads, with bit 2 as read and bits [1:0] zero. | CHK-017:PASS | — | **VERIFIED** |
| BR-9-07 |  | a_size shall be 2'b10 (4 bytes) and no other value shall ever be generated. | CHK-017:PASS | — | **VERIFIED** |
| BR-9-08 |  | a_mask shall be 4'b1111 and no other value shall ever be generated (DEC-001). | CHK-017:PASS | — | **VERIFIED** |
| BR-9-09 |  | Any d_opcode value other than the expected one shall give PSLVERR. | CHK-010:PASS, CHK-020:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-9-10 |  | Read data shall be forced to 0 for writes and for every error completion. | CHK-005:PASS | — | **VERIFIED** |
| BR-10.1-01 |  | The APB FSM must go to ENUM_ST_BUSY and assert w_req_launch = 1 on a legal request in the Setup phase. | CHK-006:PASS | — | **VERIFIED** |
| BR-10.1-02 |  | The APB FSM must go to ENUM_ST_DONE, set reg_pready and reg_pslverr and clear reg_prdata at the Setup edge on an illegal request. | CHK-007:PASS | — | **VERIFIED** |
| BR-10.1-03 |  | The APB FSM must move to ENUM_ST_DONE, and reg_pready, reg_pslverr and reg_prdata must load the response at that edge. | CHK-010:PASS | 100.0 % (5/5) | **VERIFIED** |
| BR-10.1-04 |  | The TL-UL FSM must hold o_tlul_a_valid = 1 with channel A stable in ENUM_ST_REQ, clear reg_a_valid on acceptance, and go to IDLE with a same-cycle response or WAIT without. | CHK-015:PASS, CHK-016:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-10.1-05 |  | A response must count only in ENUM_ST_WAIT, or in ENUM_ST_REQ together with i_tlul_a_ready = 1. | CHK-010:PASS, CHK-027:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-10.1-06 | REQ-FUNC-007 | An orphan i_tlul_d_valid in any other state must be discarded with no APB effect. | CHK-011:PASS, CHK-021:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-10.3-01 |  | For an illegal request, PREADY and PSLVERR must be asserted in the first Access cycle with no channel A request. | CHK-007:PASS, CHK-018:PASS | — | **VERIFIED** |
| BR-10.3-02 |  | With channel A back pressure, channel A must remain stable and the Access phase is extended. | CHK-026:PASS | — | **VERIFIED** |
| BR-10.3-03 |  | At the end of S, channel A flops must load, reg_a_valid set, APB FSM go to BUSY and TL-UL FSM to REQ, with o_apb_pready and o_tlul_a_valid 0 in S. | CHK-006:PASS | — | **VERIFIED** |
| BR-11-02 |  | The bridge's only status indication is PSLVERR on each transfer; it is otherwise configured only by parameters. | CHK-010:PASS, CHK-018:PASS, CHK-019:PASS | — | **VERIFIED** |
| BR-12-01 |  | The bridge must respond in the first Access cycle with PREADY = 1, PSLVERR = 1 and PRDATA = 0. | CHK-007:PASS, CHK-018:PASS | 100.0 % (4/4) | **VERIFIED** |
| BR-12-02 |  | The bridge must not issue a TL-UL request for a write with PSTRB other than 4'b1111. | CHK-007:PASS, CHK-018:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-12-04 |  | The bridge must respond as for ERR-001: PREADY = 1, PSLVERR = 1 in the first Access cycle, PRDATA = 0, and no TL-UL request. | CHK-007:PASS, CHK-018:PASS | — | **VERIFIED** |
| BR-12-05 |  | The bridge must drive PSLVERR = 1 and PRDATA = 0 together with PREADY. | CHK-010:PASS, CHK-019:PASS | — | **VERIFIED** |
| BR-12-07 |  | The bridge must drive PSLVERR = 1 and PRDATA = 0 together with PREADY, as for ERR-003. | CHK-010:PASS, CHK-020:PASS | 100.0 % (2/2) | **VERIFIED** |
| BR-12-09 |  | The bridge must not assert PREADY; the APB Requester waits, and recovery is by SoC watchdog or reset. | CHK-011:PASS, CHK-022:PASS | — | **VERIFIED** |
| BR-13-01 | REQ-PERF-001 | The access phase of a normal transfer must last 3 cycles (2 wait states). | CHK-023:PASS, CHK-024:PASS | — | **VERIFIED** |
| BR-13-02 | REQ-PERF-002 | The access phase for a same-cycle response must last 2 cycles (1 wait state). | CHK-027:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-13-03 | REQ-PERF-003 | The access phase of a local error must last 1 cycle (0 wait states). | CHK-018:PASS | — | **VERIFIED** |
| BR-13-04 |  | The minimum transfer interval must be 4 cycles for normal, 3 for same-cycle response, and 2 for local error transfers. | CHK-028:PASS, CHK-029:PASS | — | **VERIFIED** |
| BR-14.1-01 |  | The RTL must follow the VLSIT RTL Design Rules v2 (REF-003) as the mandatory RTL coding authority. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-14.1-02 |  | The RTL must comply with the VLSIT RTL Design Rules without local exceptions. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-14.1-03 |  | Every flip-flop, including the payload registers, must have the asynchronous reset of section 7.3. | CHK-030:PASS | — | **VERIFIED** |
| BR-14.1-04 |  | FSM signals must be named reg_fsm_apb_current_state, w_fsm_apb_nxt_state, reg_fsm_tlul_current_state, w_fsm_tlul_nxt_state with ENUM_ST_* members. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-14.1-05 |  | Coding style: one module per file named as the module, structural top, ANSI ports with input wire and output logic, reg_/w_/p_ff_/p_com_ names, PARA_* parameters with three PAR-02 comment lines, names at most 30 characters, comment lines at most 100 characters. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-14.2-01 |  | m_apb_tlul_bridge is the structural top containing only ports, parameters, interconnect wires and the two instances, in CLK-CORE/RST-CORE domains. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-14.2-02 |  | m_apb_if, instance u_apb_if, must contain all APB-facing logic: Setup detect, legality check, APB FSM and response flops reg_pready, reg_pslverr, reg_prdata. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-14.2-03 |  | m_tlul_if, instance u_tlul_if, must contain all TL-UL-facing logic: channel A flops, TL-UL FSM, reg_d_ready and D-channel check. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-14.2-04 | REQ-IF-007 | State is owned by m_apb_if and m_tlul_if; m_apb_if has no TL-UL port and m_tlul_if has no APB port. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-14.3-01 |  | Lint uses the project lint set with default_nettype none checking, waiving only the unused inputs i_apb_pprot, i_tlul_d_param, i_tlul_d_size, i_tlul_d_sink, i_tlul_d_user. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-15.1-01 |  | The environment includes an APB Requester model driving legal/illegal requests with varied idle time, and a TL-UL device model delaying a_ready and d_valid, answering in acceptance cycle, injecting d_error, wrong opcode, wrong source and orphan responses. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| BR-15.1-02 |  | The APB protocol checker and the TL-UL protocol checker of REF-005 are bound at the ports. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-15.1-03 |  | A scoreboard compares each TL-UL request and each APB completion with the APB transfer that caused it. | CHK-029:PASS | — | **VERIFIED** |
| BR-15.1-04 |  | Each simulation run records its seed. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| BR-15.1-05 |  | Every requirement in section 3 is covered by at least one passing test and all coverage bins of 15.3 are hit. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| BR-15.2-02 | REQ-FUNC-001, REQ-FUNC-002, REQ-FUNC-006, REQ-PERF-001 | Bridge issues PutFullData, size 2, mask 4'b1111 with correct address and data, completes in 3 Access cycles, and PRDATA is 0. | CHK-023:PASS | — | **VERIFIED** |
| BR-15.2-03 | REQ-FUNC-002, REQ-FUNC-003 | Scoreboard matches every TL-UL request and APB completion for random aligned reads and writes. | CHK-029:PASS | — | **VERIFIED** |
| BR-15.2-05 | REQ-FUNC-001, REQ-FUNC-003, REQ-FUNC-006, REQ-PERF-001 | Bridge issues Get, ignores PSTRB, PRDATA equals d_data, and completes in 3 Access cycles. | CHK-024:PASS | — | **VERIFIED** |
| BR-15.2-06 | REQ-ERR-003, REQ-FUNC-006 | PSLVERR is 1 and PRDATA is 0. | CHK-019:PASS | — | **VERIFIED** |
| BR-15.2-07 | REQ-ERR-004, REQ-ERR-005 | PSLVERR is 1 and PRDATA is 0. | CHK-020:PASS | — | **VERIFIED** |
| BR-15.2-08 | REQ-FUNC-005 | Channel A is stable while valid and not ready, and the request is accepted once. | CHK-026:PASS | — | **VERIFIED** |
| BR-15.2-09 | REQ-FUNC-007 | Orphan responses are discarded, have no APB effect, and the next transfer is correct. | CHK-021:PASS | — | **VERIFIED** |
| BR-15.2-10 | REQ-PERF-002 | Transfer takes 2 Access cycles. | CHK-027:PASS | — | **VERIFIED** |
| BR-15.2-11 | REQ-RESET-002 | Both FSMs are idle after release and no completion is produced for the abandoned transfer. | CHK-031:PASS | — | **VERIFIED** |
| BR-15.2-12 | REQ-FUNC-004, REQ-PERF-003 | Only one request is outstanding and intervals are as in 10.4. | CHK-029:PASS | — | **VERIFIED** |
| BR-15.2-13 | REQ-PARAM-001 | Legal parameter values elaborate; illegal values are reported. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-15.2-14 | REQ-VER-001 | Both protocol checkers are bound and report no checker error in any run. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-15.2-15 | REQ-CLK-001, REQ-RTL-001 | Lint reports no finding and CDC reports zero crossings. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-15.2-16 | REQ-IF-003, REQ-IF-007 | Every non-constant output is driven by a flip-flop Q pin and module boundaries are as in 14.2. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-15.2-17 | REQ-DFT-001 | Design contains no latch, loop, tri-state or gated clock. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-15.2-18 | REQ-FUNC-008, REQ-PERF-004 | Every transfer completes correctly in order, Setup-to-Setup intervals are as in 10.4, and no TL-UL request is made for illegal ones. | CHK-028:PASS | — | **VERIFIED** |
| BR-15.3-01 | REQ-IF-004 | o_apb_pready is asserted only with i_apb_psel and i_apb_penable, for one cycle; o_apb_pslverr only with o_apb_pready. | CHK-001:PASS, CHK-002:PASS, CHK-003:PASS | 100.0 % (3/3) | **VERIFIED** |
| BR-15.3-02 | REQ-FUNC-005 | Channel A remains stable. | CHK-015:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-15.3-03 | REQ-FUNC-004 | At most one TL-UL request is outstanding. | CHK-008:PASS | — | **VERIFIED** |
| BR-15.3-04 | REQ-FUNC-002, REQ-FUNC-003 | Opcode, size, mask and address are legal per REF-005 legalAOpcode, sizeMatchesMask, addrSizeAligned, contigMask. | CHK-017:PASS | — | **VERIFIED** |
| BR-15.3-05 | REQ-IF-005 | a_param, a_size, a_mask, a_source and a_user are constant. | CHK-017:PASS | — | **VERIFIED** |
| BR-15.3-06 | REQ-IF-006 | o_tlul_d_ready is 0 in reset and 1 from the first edge after release. | CHK-012:PASS, CHK-013:PASS, CHK-030:PASS | 100.0 % (10/10) | **VERIFIED** |
| BR-15.3-07 | REQ-ERR-001, REQ-ERR-002 | No TL-UL request is issued for an illegal APB request. | CHK-007:PASS, CHK-014:PASS | — | **VERIFIED** |
| BR-15.3-08 | REQ-FUNC-001 | o_tlul_a_valid rises in the cycle after the legal Setup phase. | CHK-006:PASS | — | **VERIFIED** |
| BR-15.3-09 | REQ-FUNC-007 | An orphan response never changes o_apb_pready, o_apb_prdata or o_apb_pslverr. | CHK-011:PASS, CHK-021:PASS | — | **VERIFIED** |
| BR-15.3-10 | REQ-FUNC-008 | Next cycle has o_tlul_a_valid = 1 for a legal request or o_apb_pready = 1 for an illegal request. | CHK-006:PASS, CHK-007:PASS, CHK-028:PASS | — | **VERIFIED** |
| BR-15.3-11 | REQ-ERR-001, REQ-ERR-005, REQ-FUNC-002, REQ-FUNC-007, REQ-FUNC-008, REQ-PERF-001, REQ-PERF-002, REQ-PERF-004 | Coverage COV-001 to COV-005 define bins (PSTRB values, error kinds, wait/delay cycles, orphan timing, back-to-back pairs) and all bins must be hit. | CHK-029:PASS | — | **VERIFIED** |
| BR-16-01 | REQ-DFT-001 | All flip-flops in the IP shall be scan-eligible, with no latch, combinational loop, tri-state, clock gating, or derived clock (REQ-DFT-001). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-17.1.2-01 | REQ-IF-003 | Every changing APB4 and TL-UL output must be a flip-flop Q pin, with a timing budget of one cycle minus clock-to-output. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-20-01 |  | The APB Requester starts a transfer with a Setup phase (i_apb_psel = 1, i_apb_penable = 0) and keeps address and control stable until i_apb_pready. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| BR-20-02 |  | The bridge shall support back-to-back transfers with i_apb_psel held high as valid transfers. | CHK-028:PASS | — | **VERIFIED** |
| BR-20-03 |  | The TL-UL device returns exactly one response per request and no response before the request is accepted. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| BR-20-04 |  | Only full-strobe writes (PSTRB = 4'b1111) to word-aligned addresses are accepted and issued to TL-UL. | CHK-018:PASS | — | **VERIFIED** |
| BR-20-05 |  | The bridge returns PSLVERR with no TL-UL request for any write PSTRB other than 4'b1111 and for any misaligned address. | CHK-014:PASS, CHK-018:PASS | — | **VERIFIED** |
| BR-20-06 |  | The bridge never issues TL-UL PutPartialData. | CHK-017:PASS | — | **VERIFIED** |
| BR-20-07 |  | The bridge has no timeout and no drain mechanism; the APB Requester waits indefinitely for a device that never answers. | CHK-022:PASS | — | **VERIFIED** |
| BR-20-08 |  | Every output that can change comes from a flip-flop. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| BR-20-09 |  | Outputs a_param, a_size, a_mask, a_source, a_user, a_opcode[1:0] and a_address[1:0] never change after reset and are constant tie-offs. | CHK-017:PASS | — | **VERIFIED** |
| BR-20-10 |  | The response is checked for d_error, d_opcode and d_source; any failure gives PSLVERR = 1 and PRDATA = 0. | CHK-010:PASS, CHK-019:PASS, CHK-020:PASS | — | **VERIFIED** |
| BR-20-11 |  | o_tlul_d_ready is 0 in reset and 1 from the first clock edge after reset release. | CHK-012:PASS, CHK-013:PASS | 100.0 % (1/1) | **VERIFIED** |
| BR-20-12 | REQ-FUNC-008 | The Setup phase is recognized by levels i_apb_psel = 1 and i_apb_penable = 0, never by an edge of i_apb_psel, with no added idle cycle between back-to-back transfers. | CHK-006:PASS, CHK-028:PASS | — | **VERIFIED** |
| TL-T3.1-01 |  | Burst transactions are not supported; transaction sizes are up to bus width only (byte, 2B, 4B). | CHK-017:PASS | — | **VERIFIED** |
| TL-T3.2-03 |  | The bus carries at most one request (read or write) per cycle. | CHK-008:PASS | — | **VERIFIED** |
| TL-T3.2-04 |  | The bus carries at most one response (read or write) per cycle. | not verified: covered_by_other_check | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.3-01 |  | Bus primitives, hosts and peripherals developed using the extended specification can be used with blocks using the base specification. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| TL-T3.3-02 |  | Baseline receiver blocks ignore the user signals. | CHK-025:PASS | — | **VERIFIED** |
| TL-T3.3-03 |  | Baseline source blocks generate a project-specific default value for the user signals. | CHK-017:PASS | — | **VERIFIED** |
| TL-T4.1.1-01 |  | TL-UL host drivers in this library are not required to drive valid signals LOW for at least 100 cycles while reset is asserted. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| TL-T4.1.1-02 |  | TL-UL devices within the library tolerate reset windows shorter than 100 cycles. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T4.1.3.1-01 |  | All request steering must be made as a function of the address (a_address) only, not a_source or a_user. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T4.1.3.2-01 |  | A host may use a_source/d_source to ascribe request identifiers since TL-UL does not guarantee in-order responses. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| TL-T4.1.3.2.2-01 |  | Hosts may only use the low bits of the source identifier and must not assume all AIW bits are returned intact. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T4.1.3.2.3-01 |  | A device must return the associated a_source value on d_source of the response. | CHK-029:PASS | — | **VERIFIED** |
| TL-T4.1.3.3-01 |  | The bus fabric must not rely on user bits for transport and must pass a_user and d_user on blindly. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T4.1.3.3-02 |  | User bits follow the same timing as source ID bits: a_user matches a_source and d_user matches d_source. | CHK-017:PASS | — | **VERIFIED** |
| TL-T4.1.3.4-02 |  | TL-UL hosts in this project must not use non-contiguous a_mask values. | CHK-017:PASS | — | **VERIFIED** |
| TL-T4.1.3.4-03 |  | A device may assert d_error if it does not support a given contiguous or non-contiguous subword a_mask. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T4.1.3.4-04 |  | For PutFullData, a_size should be 'h2 for a 32b write ('h3 for 64b bus width). | CHK-017:PASS | — | **VERIFIED** |
| TL-T4.1.3.4-05 |  | For PutPartialData, a_size must encode the number of bytes transmitted as 2^a_size. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T4.1.3.4-06 |  | For PutPartialData, the bits of a_mask should indicate valid byte lanes. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T4.1.3.4-07 |  | Bus devices should return an error for undefined a_opcode values. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T4.1.3.4-08 |  | Undefined d_opcode values should return an error. | CHK-020:PASS | — | **VERIFIED** |
| TL-T4.1.3.5-01 |  | TL-UL devices must raise d_error when a request carries a wrong opcode. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T4.1.3.5-02 |  | a_size must not be greater than 2; a request violating this must cause the device to raise d_error. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T4.1.3.5-03 |  | Inactive lanes must be marked with 'b0 in a_mask; violation must cause the device to raise d_error. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T4.1.3.5-04 |  | PutFullData must mark all active lanes with a 'b1 in a_mask; violation must cause the device to raise d_error. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T4.1.3.5-05 |  | TL-UL devices must raise d_error for accesses to non-existent addresses. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T4.1.3.5-06 |  | Depending on device support, a non-contiguous a_mask may lead to d_error. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| TL-T4.1.3.5-07 |  | Register files always assume aligned 32-bit accesses. | CHK-017:PASS | — | **VERIFIED** |
| TL-T4.1.3.5-08 |  | The host side must discard orphaned responses and responses with the wrong opcode. | CHK-020:PASS, CHK-021:PASS | — | **VERIFIED** |

## Mutants

| ID | File:line | Operator | Status | Caught by | Rules | Equivalent? |
|---|---|---|---|---|---|---|
| M01 | m_tlul_if.sv:100 | ne_to_eq | killed | CHK-010, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_orphan_resp | BR-3-27, BR-9-09, BR-6.3-15, BR-12-07, BR-1.3-04 |  |
| M02 | m_apb_if.sv:62 | eq_to_ne | killed | CHK-006, CHK-007, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_or | BR-3-12, BR-1.3-05, BR-3-01, BR-3-02, BR-5.3-01 |  |
| M03 | m_tlul_if.sv:134 | negate_if | killed | CHK-015, CHK-016, CHK-008, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_c | BR-3-08, BR-5.4-03, BR-6.3-07, BR-10.1-04, BR-15.3-02 |  |
| M04 | m_tlul_if.sv:95 | eq_to_ne | killed | CHK-010, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_orphan_resp | BR-3-11, BR-6.3-08, BR-10.1-06, BR-3-09, BR-10.1-03 |  |
| M05 | m_apb_if.sv:116 | one_to_zero | killed | CHK-010, CHK-003, CHK-004, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_c | BR-3-09, BR-5.3-06, BR-10.1-03, BR-1.1-01, BR-5.3-07 |  |
| M06 | m_apb_if.sv:135 | zero_to_one | killed | CHK-012, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_orphan_resp | BR-3-31, BR-6.2-03, BR-3-21, BR-7.3-03, BR-15.3-06 |  |
| M07 | m_tlul_if.sv:181 | one_to_zero | killed | CHK-013, CHK-006, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_or | BR-3-22, BR-5.3-04, BR-6.2-15, BR-15.3-06, BR-20-11 |  |
| M08 | m_apb_if.sv:111 | negate_if | killed | test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_orphan_responses, te | BR-3-24, BR-3-25, BR-12-01, BR-T1-03, BR-2.3-01 |  |
| M09 | m_tlul_if.sv:177 | zero_to_one | killed | CHK-012, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_orphan_resp | BR-3-31, BR-3-21, BR-7.3-03, BR-15.3-06, BR-6.2-06 |  |
| M10 | m_tlul_if.sv:101 | ne_to_eq | killed | CHK-010, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_orphan_resp | BR-3-28, BR-9-09, BR-6.3-15, BR-12-07, BR-8-08 |  |
| M11 | m_apb_if.sv:66 | eq_to_ne | killed | CHK-014, CHK-006, CHK-007, CHK-011, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_sourc | BR-2.3-02, BR-T1-04, BR-T1-05, BR-3-25, BR-1.3-03 |  |
| M12 | m_tlul_if.sv:135 | negate_if | killed | CHK-006, CHK-010, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_or | BR-3-35, BR-6.3-09, BR-10.1-05, BR-5.3-08, BR-13-02 |  |
| M13 | m_tlul_if.sv:89 | eq_to_ne | killed | CHK-006, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_orphan_resp | BR-3-06, BR-3-07, BR-5.4-01, BR-3-01, BR-1.1-01 |  |
| M14 | m_apb_if.sv:112 | one_to_zero | killed | CHK-007, CHK-003, CHK-004, test_chk_018_local_error, test_chk_025_ignored_inputs, test_chk_028_back_to_back, test_chk_02 | BR-3-24, BR-12-01, BR-12-02, BR-T1-03, BR-T1-04 |  |
| M15 | m_apb_if.sv:109 | zero_to_one | killed | CHK-003, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_orphan_resp | BR-3-19, BR-6.2-05, BR-15.3-01, BR-3-18, BR-6.2-03 |  |
| M16 | m_apb_if.sv:92 | negate_if | killed | CHK-006, CHK-007, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_or | BR-3-24, BR-3-25, BR-12-01, BR-3-12, BR-12-02 |  |
| M17 | m_tlul_if.sv:189 | zero_to_one | killed | CHK-012, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_orphan_resp | BR-3-31, BR-6.2-15, BR-3-21, BR-7.3-03, BR-15.3-06 |  |
| M18 | m_apb_if.sv:115 | eq_to_ne | killed | CHK-010, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_orphan_resp | BR-3-09, BR-5.3-06, BR-10.1-03, BR-3-11, BR-1.1-01 |  |
| M19 | m_tlul_if.sv:157 | negate_if | killed | CHK-006, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_orphan_resp | BR-3-03, BR-3-04, BR-3-05, BR-5.3-02, BR-1.1-02 |  |
| M20 | m_tlul_if.sv:153 | eq_to_ne | killed | CHK-014, CHK-006, CHK-009, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_c | BR-5.4-02, BR-5.4-06, BR-3-08, BR-6.3-07, BR-10.1-04 |  |
| M21 | m_apb_if.sv:113 | one_to_zero | killed | CHK-007, test_chk_018_local_error, test_chk_025_ignored_inputs, test_chk_028_back_to_back, test_chk_029_random_scoreboar | BR-3-25, BR-12-01, BR-T1-03, BR-T1-04, BR-3-36 |  |
| M22 | m_apb_if.sv:108 | zero_to_one | killed | test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_orphan_responses, te | BR-3-18, BR-6.2-03, BR-15.3-01, BR-3-11, BR-5.4-04 |  |
| M23 | m_apb_if.sv:125 | negate_if | killed | CHK-010, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_orphan_resp | BR-3-30, BR-7.3-02, BR-3-32, BR-7.3-05, BR-15.3-06 |  |
| M24 | m_tlul_if.sv:178 | zero_to_one | killed | CHK-012, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_orphan_resp | BR-3-31, BR-3-21, BR-6.2-15, BR-7.3-03, BR-15.3-06 |  |
| M25 | m_apb_if.sv:66 | eq_to_ne | killed | CHK-014, CHK-006, CHK-007, CHK-011, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_sourc | BR-2.3-01, BR-T1-03, BR-T1-05, BR-3-24, BR-1.3-03 |  |
| M26 | m_tlul_if.sv:142 | negate_if | killed | CHK-010, test_chk_025_ignored_inputs, test_chk_026_backpressure_delay, test_chk_029_random_scoreboard, test_regression_r | BR-3-09, BR-10.1-03, BR-5.3-06, BR-1.1-01, BR-3-06 |  |
| M27 | m_tlul_if.sv:94 | eq_to_ne | killed | CHK-010, test_chk_025_ignored_inputs, test_chk_027_same_cycle_response, test_chk_028_back_to_back, test_chk_029_random_s | BR-3-35, BR-6.3-09, BR-10.1-05, BR-3-11, BR-6.3-08 |  |
| M28 | m_apb_if.sv:136 | zero_to_one | killed | CHK-012, CHK-003, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_or | BR-3-31, BR-3-19, BR-6.2-05, BR-3-21, BR-15.3-01 |  |
| M29 | m_apb_if.sv:134 | negate_if | killed | CHK-007, CHK-010, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_or | BR-3-31, BR-3-21, BR-6.2-04, BR-7.3-03, BR-15.3-06 |  |
| M30 | m_tlul_if.sv:167 | negate_if | killed | CHK-015, CHK-010, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_or | BR-3-30, BR-7.3-02, BR-3-32, BR-7.3-05, BR-15.3-06 |  |
| M31 | m_apb_if.sv:115 | negate_if | killed | test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_orphan_responses, te | BR-3-09, BR-5.3-06, BR-10.1-03, BR-3-11, BR-3-18 |  |
| M32 | m_tlul_if.sv:130 | negate_if | killed | CHK-014, CHK-006, CHK-009, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_c | BR-3-06, BR-3-07, BR-5.4-01, BR-3-01, BR-1.1-01 |  |
| M33 | m_apb_if.sv:90 | negate_if | killed | CHK-006, CHK-007, CHK-010, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_c | BR-3-12, BR-3-01, BR-3-06, BR-1.1-01, BR-5.4-05 |  |
| M34 | m_tlul_if.sv:176 | negate_if | killed | CHK-012, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_orphan_resp | BR-3-31, BR-3-21, BR-3-22, BR-7.3-03, BR-15.3-06 |  |
| M35 | m_apb_if.sv:96 | negate_if | killed | CHK-006, CHK-010, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_or | BR-3-09, BR-5.3-06, BR-3-11, BR-6.3-08, BR-10.1-06 |  |
| M36 | m_tlul_if.sv:188 | negate_if | killed | CHK-006, test_chk_018_local_error, test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_021_orphan_resp | BR-3-31, BR-3-21, BR-7.3-03, BR-15.3-06, BR-6.2-15 |  |

## Not verified by this run

- Formal proof, CDC/RDC, STA, synthesis and DFT checks are outside this flow.
- Rules marked NOT_VERIFIED_BY_SIM carry the contract's reason (static, structural, not observable...).
- Only the default parameter configuration was simulated unless stated above.

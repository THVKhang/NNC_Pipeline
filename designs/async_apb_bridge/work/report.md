# Verification report — async_apb_bridge

Generated 2026-11-11T06:16:23+00:00 by NNC Pipeline.

## Summary

| Item | Result |
|---|---|
| Rules | 260 — {'NOT_PROVEN': 43, 'NOT_VERIFIED_BY_SIM': 75, 'PARTIAL': 12, 'VERIFIED': 130} |
| Checks | 35 — {'NOT_HIT': 1, 'NOT_VERIFIABLE': 7, 'PASS': 27} |
| Tests | {'pass': 28} |
| Integration | OK |
| Code coverage (RTL), line | 90.8 % (246/271 lines) |
| Code coverage (RTL), block | 87.0 % (67/77 statement blocks and branch arms) |
| Code coverage (RTL), expression | 73.0 % (54/74 condition terms) |
| Code coverage (RTL), toggle | 98.5 % (2315/2350 bit toggles 0->1 and 1->0) |
| Code coverage (RTL), functional | 82.5 % (33/40 cover points of the specification) |
| Mutation score | 72.2 % (26 killed / 10 survived / 0 not compiled) |
| Coverage target | not requested (`nnc cover <design> --target <n> --metric <m>`) |
| Triage | no failure to analyse |
| Agent cost | US$11.8281 in 91 calls (A1 0.9876, A12 0.7593, A2 0.7731, A3 0.4261, A4 1.6549, A5 1.783, A6 1.2864, A7 4.1576) |

## Sign-off conditions

| Condition | State |
|---|---|
| Gates G1-G3 approved | met — approved on delegation by an agent: a person should confirm |
| Interface conformance of the DUT | met |
| Every selected check PASS (no FAIL, NOT_HIT, NOT_RUN) | **not met** — NOT_HIT 1, NOT_VERIFIABLE 7 |
| Every planned check selected | met |
| Every rule in a check or declared not verifiable | met |
| Mutation run | met |
| Per-requirement mutation score >= 85 % | **not met** — 20 rule(s) below: AB2-1.3-04, AB2-1.3-06, AB2-10.1-03, AB2-10.1-08, AB2-10.2-06, AB2-10.2-08, AB2-15.3-15, AB2-15.3-16, AB2-3-25, AB2-3-26 |

## Gates

| Gate | State | Detail |
|---|---|---|
| G1_rules | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-10T19:01:14+00:00 |
| G2_contract | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-10T19:51:49+00:00 |
| G3_verif_sources | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-11T05:55:34+00:00 |
| G4_signoff | PENDING | artifacts ready for review |

## Checks

| Check | Kind | Title | Status | Evidence |
|---|---|---|---|---|
| CHK-001 | assertion | Absent APB5 signals drive zero | **PASS** | hits 315180, fails 0 |
| CHK-002 | assertion | Outputs change only at their own clock edge or on reset assertion | **PASS** | hits 315180, fails 0 |
| CHK-003 | assertion | Requester-side PREADY only in an Access cycle | **PASS** | hits 6270, fails 0 |
| CHK-004 | assertion | Requester-side PREADY is a one-cycle pulse | **PASS** | hits 6270, fails 0 |
| CHK-005 | assertion | PSLVERR only in the PREADY cycle (no sticky error) | **PASS** | hits 1748, fails 0 |
| CHK-006 | assertion | At most one PREADY per accepted Setup phase | **PASS** | hits 12575, fails 0 |
| CHK-007 | assertion | Response outputs stable outside the PREADY cycle | **PASS** | hits 155963, fails 0 |
| CHK-008 | assertion | No unknown requester-side outputs after reset | **PASS** | hits 162232, fails 0 |
| CHK-009 | assertion | Requester-side outputs at reset value while i_rst_n_mst is low | **PASS** | hits 1456, fails 0 |
| CHK-010 | assertion | Completer-side outputs at reset value while i_rst_n_slv is low | **PASS** | hits 870, fails 0 |
| CHK-011 | assertion | No unknown completer-side outputs after reset | **PASS** | hits 152756, fails 0 |
| CHK-012 | assertion | Completer-side PENABLE implies PSEL; PSEL rises in a Setup cycle | **PASS** | hits 47347, fails 0 |
| CHK-013 | assertion | Completer-side Setup phase lasts exactly one cycle | **PASS** | hits 6285, fails 0 |
| CHK-014 | assertion | Access phase held while the completer is not ready (no timeout) | **PASS** | hits 34782, fails 0 |
| CHK-015 | assertion | Completer-side transfer ends at the PREADY edge | **PASS** | hits 6280, fails 0 |
| CHK-016 | assertion | Completer-side request fields stable during a transfer | **PASS** | hits 41067, fails 0 |
| CHK-017 | assertion | Completer-side request fields loaded only at Setup entry | **PASS** | hits 6285, fails 0 |
| CHK-018 | assertion | APB5 o_apb_pwakeup high no later than o_apb_psel and until completion | **NOT_HIT** | hits 0, fails 0 |
| CHK-019 | test | APB5 user signals transported unchanged | **NOT_VERIFIABLE** | test_chk_019_apb5_user_signals |
| CHK-020 | test | APB5 wake-up propagation and in-progress term | **NOT_VERIFIABLE** | test_chk_020_apb5_wakeup |
| CHK-021 | test | APB4 configuration ignores APB5 inputs | **PASS** | test_chk_021_apb4_ignores_apb5 |
| CHK-022 | test | Smallest legal configuration CFG-MIN end to end | **NOT_VERIFIABLE** | test_chk_022_cfg_min |
| CHK-023 | test | Four-phase handshake: same function, PREADY only after the handshake closes | **NOT_VERIFIABLE** | test_chk_023_four_phase/periods=0, test_chk_023_four_phase/periods=1 |
| CHK-024 | test | Requester protocol violations: PENABLE without Setup, field changes during Access, extended Setup | **PASS** | test_chk_024_requester_violations |
| CHK-025 | test | Two-phase transfer duration bound | **NOT_VERIFIABLE** | test_chk_025_two_phase_duration/periods=0, test_chk_025_two_phase_duration/periods=1, test_chk_025_two_phase_duration/periods=2, test_chk_025_two_phase_duration/periods=3, test_chk_025_two_phase_duration/periods=4 |
| CHK-026 | test | Four-phase transfer duration bound | **NOT_VERIFIABLE** | test_chk_026_four_phase_duration/periods=0, test_chk_026_four_phase_duration/periods=1, test_chk_026_four_phase_duration/periods=2, test_chk_026_four_phase_duration/periods=3, test_chk_026_four_phase_duration/periods=4 |
| CHK-027 | test | Reset values, quiet idle after release, asynchronous reset assertion | **PASS** | test_chk_027_reset_values |
| CHK-028 | test | Reset during random traffic: transfer lost, clean restart, staggered release | **PASS** | test_chk_028_reset_during_traffic |
| CHK-029 | test | Random traffic scoreboard across clock ratios with a noisy completer | **PASS** | test_chk_029_scoreboard_ratios |
| CHK-030 | test | Synchronizer depth seen in crossing latency (CELL_TYPE 4) | **NOT_VERIFIABLE** | test_chk_030_sync_depth |
| CHK-031 | test | Single write and read without wait states, two-phase, field and response transport with crossing windows | **PASS** | test_chk_031_single_write_read |
| CHK-032 | test | Completer wait states extend the transfer without limit | **PASS** | test_chk_032_wait_states |
| CHK-033 | test | Error response forwarded with data, next transfer independent | **PASS** | test_chk_033_error_response |
| CHK-034 | test | Back-to-back transfers, one at a time | **PASS** | test_chk_034_back_to_back/periods=0, test_chk_034_back_to_back/periods=1 |
| CHK-035 | test | PPROT and PSTRB forwarded unchanged, including PSTRB of a read | **PASS** | test_chk_035_pprot_pstrb |

## Requirement traceability (RTM)

| Rule | Spec ref | Statement | Checks | Mutation | Status |
|---|---|---|---|---|---|
| AB2-1.1-01 |  | The multi-bit request and response bundles must never be sampled by a synchronizer; only one-bit control signals pass through synchronizers. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-1.1-02 |  | The source must hold the multi-bit request and response bundles stable for the whole handshake. | CHK-024:PASS, CHK-029:PASS | — | **VERIFIED** |
| AB2-1.1-03 |  | The destination must load the multi-bit bundle only after the associated control bit has arrived. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AB2-1.1-04 |  | The timing of the bundle paths must be bounded by set_max_delay constraints (Section 17). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-1.3-01 | REQ-FUNC-001, REQ-FUNC-009 | The bridge must always support APB4 write and read transfers across two asynchronous clocks (FEAT-001, REQ-FUNC-001 to REQ-FUNC-009). | CHK-031:PASS | 100.0 % (9/9) | **VERIFIED** |
| AB2-1.3-02 | REQ-FUNC-005, REQ-FUNC-006 | The bridge must always transport wait states and error responses across the crossing (FEAT-002). | CHK-032:PASS, CHK-033:PASS | — | **VERIFIED** |
| AB2-1.3-03 | REQ-HS-001, REQ-PERF-001 | The bridge must provide the two-phase handshake when PARA_APBCDC_HS_TYPE is 0 (FEAT-003). | CHK-025:NOT_VERIFIABLE, CHK-031:PASS | 100.0 % (2/2) | **PARTIAL** |
| AB2-1.3-04 | REQ-HS-001, REQ-HS-004, REQ-PERF-002 | The bridge must provide the four-phase handshake when PARA_APBCDC_HS_TYPE is 1 (FEAT-004). | CHK-023:NOT_VERIFIABLE | 50.0 % (2/4) **below** | **NOT_PROVEN** |
| AB2-1.3-05 | REQ-CLK-003 | The bridge must support selectable synchronizer depth with PARA_APBCDC_CELL_TYPE 1 to 4; 0 is for simulation only (FEAT-005). | CHK-030:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-1.3-06 | REQ-APB5-001 | The bridge must provide APB5 wake-up signaling when PARA_APBCDC_APB5 is 1 (FEAT-006). | CHK-020:NOT_VERIFIABLE | 0.0 % (0/1) **below** | **NOT_PROVEN** |
| AB2-1.3-07 | REQ-APB5-002 | The bridge must provide the APB5 user signals when PARA_APBCDC_APB5 is 1 and the width is above 0 (FEAT-007). | CHK-019:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-1.3-08 | REQ-TIM-001, REQ-TIM-003 | The IP must always deliver an executable SDC with the crossing constraints (FEAT-008). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-2.2-01 |  | The RTL must comply with REF-003 baseline; conflicts are resolved by revising the requirement or choosing a compliant implementation, not by a local RTL exception. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-2.3-01 |  | The IP implements the AMBA APB Issue D completer role on the requester-side interface and requester role on the completer-side interface, with PSTRB, PPROT, PSLVERR always present and APB5 signals in the APB5 profile. | CHK-003:PASS, CHK-031:PASS | — | **VERIFIED** |
| AB2-3-01 | REQ-FUNC-001 | The bridge shall start exactly one completer-side APB transfer with the same PWRITE, PADDR, PPROT, PSTRB and, for a write, PWDATA as driven in the Setup phase. | CHK-029:PASS, CHK-031:PASS | 100.0 % (11/11) | **VERIFIED** |
| AB2-3-02 | REQ-FUNC-001 | In APB5 the completer-side transfer shall carry the same PAUSER and, for a write, the same PWUSER as the requester-side Setup phase. | CHK-019:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-3-03 | REQ-FUNC-002 | The bridge shall return the completer-side PRDATA of a read and PSLVERR unchanged on the requester side, valid in the cycle where PREADY is high. | CHK-031:PASS, CHK-033:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB2-3-04 | REQ-FUNC-002 | In APB5 the bridge shall return PRUSER of a read and PBUSER unchanged on the requester side, valid when PREADY is high. | CHK-019:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-3-05 | REQ-FUNC-003 | Transfers shall be carried in start order, one completer-side transfer per requester-side transfer, with no loss and no duplicate. | CHK-029:PASS | — | **VERIFIED** |
| AB2-3-06 | REQ-FUNC-003 | No new completer-side transfer shall start before the response of the previous one has been delivered. | CHK-029:PASS | — | **VERIFIED** |
| AB2-3-07 | REQ-FUNC-004 | Requester-side PREADY shall be low from the Setup phase until the response is available. | CHK-006:PASS | — | **VERIFIED** |
| AB2-3-08 | REQ-FUNC-004 | Requester-side PREADY shall then be high for exactly one i_clk_mst cycle, in a cycle in which PSEL and PENABLE are high. | CHK-003:PASS, CHK-004:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB2-3-09 | REQ-FUNC-005 | Requester-side PREADY shall be raised only after the completer-side PREADY was seen, so completer wait states extend the requester-side transfer. | CHK-032:PASS | — | **VERIFIED** |
| AB2-3-10 | REQ-FUNC-005 | The bridge shall wait without limit for the completer response, with no timeout. | CHK-014:PASS, CHK-032:PASS | — | **VERIFIED** |
| AB2-3-11 | REQ-FUNC-006 | Requester-side PSLVERR shall not be high outside the PREADY cycle. | CHK-005:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB2-3-12 | REQ-FUNC-006 | Requester-side PSLVERR shall not be high unless the completer-side PSLVERR was high at the end of the transfer. | CHK-033:PASS | — | **VERIFIED** |
| AB2-3-13 | REQ-FUNC-007, REQ-PERF-003 | The bridge shall accept the Setup phase of a new requester-side transfer in the cycle following the PREADY cycle (back-to-back). | CHK-034:PASS | — | **VERIFIED** |
| AB2-3-14 | REQ-FUNC-008 | On the completer side the bridge shall drive PSEL high for the whole transfer. | CHK-012:PASS, CHK-014:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB2-3-15 | REQ-FUNC-008 | PENABLE shall be low in the Setup cycle and high from the next cycle until the transfer completes. | CHK-012:PASS, CHK-013:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB2-3-16 | REQ-FUNC-008 | The bridge shall keep PADDR, PPROT, PWRITE, PWDATA, PSTRB, PAUSER and PWUSER unchanged from the Setup phase until PREADY is seen high. | CHK-016:PASS | — | **VERIFIED** |
| AB2-3-17 | REQ-FUNC-008 | The bridge shall drive PSEL and PENABLE low when no transfer is in progress. | CHK-015:PASS, CHK-027:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB2-3-18 | REQ-FUNC-009 | PPROT and PSTRB shall be forwarded unchanged. | CHK-035:PASS | — | **VERIFIED** |
| AB2-3-19 | REQ-FUNC-009 | The bridge does not check that PSTRB is low in a read; it forwards what the requester drove. | CHK-035:PASS | — | **VERIFIED** |
| AB2-3-20 | REQ-IF-001 | The IP shall expose exactly the ports of Section 6.2 of the configured revision. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-3-21 | REQ-IF-002 | Every output of both APB interfaces shall be a flip-flop output with no logic after it, so it is glitch-free. | CHK-002:PASS | — | **VERIFIED** |
| AB2-3-22 | REQ-IF-003 | Outputs that need not be valid shall hold a stable value (reset value zero). | CHK-007:PASS, CHK-017:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB2-3-23 | REQ-IF-003 | PSLVERR shall be low when PREADY is low. | CHK-005:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB2-3-24 | REQ-HS-001 | The request bit shall toggle once per transfer and the acknowledge bit shall toggle once per transfer (two-phase handshake). | CHK-029:PASS | — | **VERIFIED** |
| AB2-3-25 | REQ-HS-001 | The four-phase handshake shall sequence request high, acknowledge high, request low, acknowledge low. | CHK-023:NOT_VERIFIABLE | 60.0 % (3/5) **below** | **NOT_PROVEN** |
| AB2-3-26 | REQ-HS-001 | The function seen on the two APB interfaces shall be the same for both handshake types. | CHK-023:NOT_VERIFIABLE | 50.0 % (2/4) **below** | **NOT_PROVEN** |
| AB2-3-27 | REQ-HS-002 | The request bundle in the requester-side hold register shall not change from the request launch edge until the acknowledge was seen. | CHK-024:PASS, CHK-029:PASS | 100.0 % (5/5) | **VERIFIED** |
| AB2-3-28 | REQ-HS-002 | The response bundle in the completer-side hold register shall not change from the acknowledge launch edge until the next request was seen. | CHK-029:PASS | — | **VERIFIED** |
| AB2-3-29 | REQ-HS-003 | The request bit shall be launched at the same edge the request bundle is loaded, and the acknowledge bit at the same edge the response bundle is loaded. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-3-30 | REQ-HS-003 | There shall be no logic between a launch flip-flop and its synchronizer. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-3-31 | REQ-HS-004 | The requester side shall raise PREADY only after the acknowledge returned to 0. | CHK-023:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-3-32 | REQ-CLK-001 | The IP shall be correct for any frequency ratio and phase of i_clk_mst and i_clk_slv, including equal frequency. | CHK-029:PASS | — | **VERIFIED** |
| AB2-3-33 | REQ-CLK-002 | Only the five crossings (request, request bundle, acknowledge, response bundle, wake-up) shall exist between the clock domains. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-3-34 | REQ-CLK-002 | Each control bit shall cross through a synchronizer and no bundle bit shall cross through one. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-3-35 | REQ-CLK-003 | Synchronizer depth shall follow PARA_APBCDC_CELL_TYPE: 1 and 2 two stages, 3 three stages, 4 four stages. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-3-36 | REQ-CLK-003 | The value 0 (no stage) is for simulation only and shall not be used in a netlist. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-3-37 | REQ-RESET-001 | Both resets shall be active-low with asynchronous assertion. | CHK-009:PASS, CHK-027:PASS | 100.0 % (4/4) | **VERIFIED** |
| AB2-3-38 | REQ-RESET-001 | Every flip-flop of the domain shall be at its reset value: payload registers 0, request 0, acknowledge 0, FSMs IDLE, PSEL, PENABLE, PREADY, PSLVERR, PWAKEUP 0. | CHK-009:PASS, CHK-010:PASS, CHK-027:PASS | 83.3 % (5/6) **below** | **VERIFIED** |
| AB2-3-39 | REQ-RESET-002 | The two resets shall be asserted together and each released synchronously to its domain clock, outside the IP. | CHK-028:PASS | — | **VERIFIED** |
| AB2-3-40 | REQ-RESET-002 | A transfer in flight when a reset is asserted is lost. | CHK-028:PASS | — | **VERIFIED** |
| AB2-3-41 | REQ-RESET-002 | Asserting only one reset is not supported. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AB2-3-42 | REQ-APB5-001 | o_apb_pwakeup shall be a flip-flop output that is high whenever the synchronized i_apb_pwakeup is high or a completer-side transfer is in progress. | CHK-020:NOT_VERIFIABLE | 0.0 % (0/2) **below** | **NOT_PROVEN** |
| AB2-3-43 | REQ-APB5-001 | o_apb_pwakeup shall be high no later than o_apb_psel. | CHK-018:NOT_HIT | 50.0 % (1/2) **below** | **NOT_PROVEN** |
| AB2-3-44 | REQ-APB5-002 | PAUSER, PWUSER, PRUSER, PBUSER shall be transported with the same timing rules as the other request and response fields; a signal with width parameter 0 is not present. | CHK-001:PASS, CHK-019:NOT_VERIFIABLE | — | **PARTIAL** |
| AB2-3-45 | REQ-APB5-003 | The APB5 signals shall have no effect: o_apb_pwakeup is 0 and user outputs are 0. | CHK-001:PASS, CHK-021:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB2-3-46 | REQ-PARAM-001 | The IP shall accept the parameter values of Section 8. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-3-48 | REQ-PERF-001 | Duration from first Setup cycle to end of the requester PREADY cycle shall not exceed (N+3) x T_mst + (N+3+w) x T_slv. | CHK-025:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-3-49 | REQ-PERF-002 | Duration from first Setup cycle to end of the requester PREADY cycle shall not exceed (2N+4) x T_mst + (2N+4+w) x T_slv. | CHK-026:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-3-50 | REQ-PERF-003 | The bridge shall carry one transfer at a time. | CHK-034:PASS | — | **VERIFIED** |
| AB2-3-51 | REQ-TIM-001 | The IP shall be delivered with a Synopsys-dialect SDC defining the two clocks, interface budgets and exceptions of the five crossings, with budgets computed from clock periods and synchronizer depth. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-3-52 | REQ-TIM-002 | Each crossing path shall be constrained by set_max_delay with clock latency ignored. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-3-53 | REQ-TIM-002 | No set_clock_groups -asynchronous and no set_false_path, other than the hold-only false path of the crossings, shall exist between the two clocks. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-3-54 | REQ-TIM-003 | The clock latency difference between launch and capture flip-flops of every crossing shall be smaller than the one-destination-period guard band. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-3-55 | REQ-RTL-001 | The RTL shall comply with REF-003 and use the hierarchy of Section 14.2. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-3-56 | REQ-RTL-002 | Synchronizer cells shall be instantiated only inside wrapper m_vlsit_apbcdc_cell_sync, named u_dont_touch_ followed by the function, with a simulation model adding random extra output latency of 0, 1 or 2 destination cycles. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-3-57 | REQ-VER-001 | Every waveform of the Section 10.3 plan shall exist as an image with its WaveJSON source, and the prototype scripts shall reproduce them. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-3-58 | REQ-VER-002 | The random regression shall cover both handshake types, two synchronizer depths, APB4 and APB5, at least ten clock ratios including equal and 9:1 both directions, with wait states and errors, and report no error. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-4-01 |  | CFG-MIN must be based on CFG-APB4 with FEAT-004, FEAT-006 and FEAT-007 disabled, ADDR_W 1 and DATA_W 8, as the smallest legal instance verified by TEST-014. | CHK-022:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-4-02 |  | FEAT-004, FEAT-006 and FEAT-007 must be selected by an elaboration-time parameter and be present or absent, not enabled or disabled at run time. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-5.3-02 |  | With the two-phase handshake reg_req toggles; with the four-phase handshake reg_req rises. | CHK-031:PASS | 100.0 % (3/3) | **VERIFIED** |
| AB2-5.3-03 |  | Loading reg_req_payload and launching the request happen at the same clock edge. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AB2-5.3-04 |  | The slv FSM loads reg_apb_payload from reg_req_payload, which has been stable for at least N destination periods, then raises PSEL (Setup). | CHK-031:PASS | — | **VERIFIED** |
| AB2-5.3-05 |  | PENABLE (Access) is raised one cycle after PSEL. | CHK-013:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB2-5.3-06 |  | The slv FSM waits in ACCESS until the completer drives PREADY. | CHK-014:PASS, CHK-032:PASS | — | **VERIFIED** |
| AB2-5.3-07 |  | At that edge the slv block loads reg_resp_hold with PRDATA, PSLVERR, PRUSER, PBUSER, drops PSEL and PENABLE, and launches the acknowledge (toggle or rise). | CHK-015:PASS, CHK-031:PASS | — | **VERIFIED** |
| AB2-5.3-08 |  | The mst FSM loads the response output registers from reg_resp_hold and raises PREADY for one cycle (state RESP). | CHK-031:PASS | — | **VERIFIED** |
| AB2-5.3-09 |  | The mst FSM first drops the request, waits for the acknowledge to fall, then loads the response and raises PREADY. | CHK-023:NOT_VERIFIABLE | 50.0 % (1/2) **below** | **NOT_PROVEN** |
| AB2-5.3-10 |  | The slv FSM waits in REQ0 for the request to fall and then drops the acknowledge. | CHK-023:NOT_VERIFIABLE | 50.0 % (1/2) **below** | **NOT_PROVEN** |
| AB2-5.3-11 |  | The mst FSM returns to IDLE and captures the next Setup phase driven in the cycle after the PREADY cycle. | CHK-034:PASS | — | **VERIFIED** |
| AB2-5.3-12 |  | i_apb_pwakeup is registered in the mst block, crosses through u_sync_wk, and drives o_apb_pwakeup through a flip-flop in the slv block together with an in-progress term. | CHK-020:NOT_VERIFIABLE | 0.0 % (0/1) **below** | **NOT_PROVEN** |
| AB2-5.4-01 |  | At most one transfer is in flight, and the FSMs are in IDLE only between transfers. | CHK-029:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB2-5.4-02 | REQ-HS-002 | The request and response bundles change only while the handshake is not in the phase in which the other domain may load them. | CHK-029:PASS | — | **VERIFIED** |
| AB2-5.4-03 |  | With the two-phase handshake the request and acknowledge bits are equal; with the four-phase handshake both are 0. | CHK-027:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB2-5.4-04 |  | Requester-side PREADY is high only in state RESP, for one cycle per transfer. | CHK-004:PASS, CHK-006:PASS | — | **VERIFIED** |
| AB2-5.4-05 |  | Completer-side PSEL is high only in states SETUP and ACCESS. | CHK-012:PASS | — | **VERIFIED** |
| AB2-5.4-06 |  | Every flip-flop that drives an APB output is reset to 0. | CHK-009:PASS, CHK-010:PASS, CHK-027:PASS | 85.7 % (6/7) | **VERIFIED** |
| AB2-6.1-01 |  | The IP provides interface IF-001, an AMBA APB4/APB5 Issue D completer interface (requests in, responses out) in CLK-MST, in all configurations. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-6.1-02 |  | The IP provides interface IF-002, an AMBA APB4/APB5 Issue D requester interface (requests out, responses in) in CLK-SLV, in all configurations. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-6.1-03 |  | The IP provides interface IF-003 as receiver of clocks and hardware resets (inputs) for CLK-MST and CLK-SLV, in all configurations. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-6.2-01 |  | o_apb_pslverr is a flop output that is high only in the o_apb_pready cycle, loaded with o_apb_pready and cleared at the next edge; reset value 0. | CHK-005:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB2-6.2-02 |  | o_apb_pwrite is loaded with the request and stays stable until the transfer completes; reset value 0. | CHK-016:PASS | — | **VERIFIED** |
| AB2-6.2-03 |  | o_apb_paddr is loaded with the request and stays stable until the transfer completes; reset value 0. | CHK-016:PASS | — | **VERIFIED** |
| AB2-6.2-04 |  | o_apb_pprot is loaded with the request and stays stable until the transfer completes; reset value 0. | CHK-016:PASS | — | **VERIFIED** |
| AB2-6.2-05 |  | o_apb_pstrb is loaded with the request and stays stable until the transfer completes; reset value 0. | CHK-016:PASS | — | **VERIFIED** |
| AB2-6.2-06 |  | o_apb_pwdata is loaded with the request and stays stable until the transfer completes; reset value 0. | CHK-016:PASS | — | **VERIFIED** |
| AB2-6.2-07 |  | o_apb_pauser is loaded with the request and stays stable until the transfer completes; reset value 0. | CHK-016:PASS, CHK-019:NOT_VERIFIABLE | — | **PARTIAL** |
| AB2-6.2-08 |  | o_apb_pwuser is loaded with the request and stays stable until the transfer completes; reset value 0. | CHK-016:PASS, CHK-019:NOT_VERIFIABLE | — | **PARTIAL** |
| AB2-6.3-01 |  | A transfer starts with a one-cycle Setup phase (PSEL high, PENABLE low), followed by the Access phase (PENABLE high), which ends in the cycle where PREADY is high. | CHK-012:PASS, CHK-013:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB2-6.3-02 |  | After PREADY the bus may return to IDLE or go directly to the Setup phase of the next transfer. | CHK-034:PASS | — | **VERIFIED** |
| AB2-6.3-03 |  | PADDR, PPROT, PENABLE, PWRITE, PAUSER, PSTRB, active PWDATA lanes and PWUSER of a write are valid whenever PSEL is high; the bridge captures them in the Setup cycle. | CHK-031:PASS | — | **VERIFIED** |
| AB2-6.3-04 |  | PREADY is valid when PSEL and PENABLE are high. | CHK-003:PASS | — | **VERIFIED** |
| AB2-6.3-05 |  | PRDATA of a read, PSLVERR, PRUSER of a read and PBUSER are valid when PSEL, PENABLE and PREADY are high. | CHK-008:PASS, CHK-031:PASS | — | **VERIFIED** |
| AB2-6.3-06 |  | PADDR, PPROT, PWRITE, PWDATA, PSTRB, PAUSER and PWUSER must not change between Setup and Access phase and while PREADY is low. | CHK-016:PASS | — | **VERIFIED** |
| AB2-6.3-07 |  | The bridge guarantees stability of the completer-side fields by loading them into reg_apb_payload once, relying on requester stability only in the Setup cycle. | CHK-017:PASS, CHK-024:PASS | — | **VERIFIED** |
| AB2-6.3-09 |  | PSLVERR is valid only in the last cycle of a transfer. | CHK-005:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB2-6.3-10 |  | The bridge forwards PRDATA and PSLVERR together without masking, even for a read with an error. | CHK-033:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB2-6.3-11 |  | PSTRB must be low in a read. | CHK-029:PASS | — | **VERIFIED** |
| AB2-6.3-12 |  | The bridge forwards PSTRB as received. | CHK-035:PASS | — | **VERIFIED** |
| AB2-6.3-13 |  | PWAKEUP must be glitch-free to be sampled asynchronously and must stay high until PREADY when high in the same cycle as PSEL. | CHK-018:NOT_HIT, CHK-020:NOT_VERIFIABLE | 0.0 % (0/1) **below** | **NOT_PROVEN** |
| AB2-6.3-14 |  | PWAKEUP may be asserted before, during or after PSEL. | CHK-020:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-6.3-15 |  | PWAKEUP should be asserted one cycle before PSEL. | CHK-020:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-6.3-16 |  | A completer may wait for PWAKEUP before driving PREADY. | CHK-020:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-6.3-17 |  | PAUSER and PWUSER are valid with PSEL (PWUSER also with PWRITE) and keep their value through Setup and Access phases. | CHK-016:PASS, CHK-019:NOT_VERIFIABLE | — | **PARTIAL** |
| AB2-6.3-18 |  | PRUSER and PBUSER are valid in the PREADY cycle. | CHK-019:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-6.3-19 |  | A domain-crossing bridge should provide all user signals. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| AB2-6.3-20 | REQ-FUNC-001, REQ-FUNC-002 | The bridge performs one completer-side transfer and returns the response. | CHK-031:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB2-6.3-21 | REQ-FUNC-005 | Requester-side PREADY stays low until the completer response. | CHK-032:PASS | — | **VERIFIED** |
| AB2-6.3-22 | REQ-FUNC-006 | The bridge returns PSLVERR with PREADY and forwards the data. | CHK-033:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB2-6.3-23 | REQ-FUNC-007 | The bridge accepts a back-to-back transfer whose Setup phase follows right after PREADY. | CHK-034:PASS | — | **VERIFIED** |
| AB2-6.3-24 | REQ-FUNC-001 | The bridge ignores PENABLE high without a preceding Setup cycle and starts no transfer. | CHK-024:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB2-6.3-25 | REQ-FUNC-001 | The bridge does not detect the change and uses the values captured in the Setup phase. | CHK-024:PASS | — | **VERIFIED** |
| AB2-6.3-26 | REQ-FUNC-005 | The bridge waits without limit for the completer PREADY. | CHK-032:PASS | — | **VERIFIED** |
| AB2-6.3-27 | REQ-RESET-002 | A single reset asserted alone is not supported; both resets must be asserted together, and a transfer in flight is lost on reset. | CHK-028:PASS | — | **VERIFIED** |
| AB2-6.4-01 |  | The IP has no interrupt or event output; errors travel as PSLVERR of the transfer. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-7.2-01 | REQ-CLK-002 | Only the five listed crossings (CDC-001 to CDC-005) join the CLK-MST and CLK-SLV domains; no other path exists between them. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-7.2-02 |  | Each data bundle must be held stable and loaded by the destination only after its control bit arrives, so no bundle bit passes through a synchronizer. | CHK-029:PASS | — | **VERIFIED** |
| AB2-7.2-03 |  | The request bundle reg_req_payload must be held in mst, loaded at the launch edge of the request bit, and loaded into reg_apb_payload in slv at the edge that sees the request event, without a synchronizer. | CHK-017:PASS, CHK-031:PASS | — | **VERIFIED** |
| AB2-7.2-04 |  | The request hold register reg_req_payload and reg_apb_payload must reset to 0. | CHK-027:PASS | 100.0 % (5/5) | **VERIFIED** |
| AB2-7.2-05 |  | reg_req must cross to slv through N-stage synchronizer u_sync_req with no logic between the flop and the first stage, its stages reset to 0 by i_rst_n_slv. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-7.2-06 |  | reg_ack must cross to mst through N-stage synchronizer u_sync_ack with no logic before the first stage, reset to 0 by i_rst_n_mst. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-7.2-07 |  | reg_resp_hold must be held in slv, loaded at the launch edge of the acknowledge bit, and loaded into reg_resp_payload in mst at the edge that sees the acknowledge event, without a synchronizer. | CHK-031:PASS | — | **VERIFIED** |
| AB2-7.2-08 |  | reg_resp_hold and reg_resp_payload must reset to 0. | CHK-027:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB2-7.2-09 |  | reg_wakeup, a registered copy of i_apb_pwakeup, must cross to slv through N-stage synchronizer u_sync_wk, reset to 0 by i_rst_n_slv. | CHK-020:NOT_VERIFIABLE | 0.0 % (0/1) **below** | **NOT_PROVEN** |
| AB2-7.2-11 |  | Release of one reset while the other domain is still in reset is allowed; no request is launched or seen because the mst FSM leaves IDLE only on a Setup phase. | CHK-028:PASS | 0.0 % (0/1) **below** | **VERIFIED** |
| AB2-7.3-01 |  | On i_rst_n_mst assertion (active-low, asynchronous), all mst-block state resets: registers 0, FSM IDLE, o_apb_pready and o_apb_pslverr 0. | CHK-009:PASS, CHK-027:PASS | 100.0 % (3/3) | **VERIFIED** |
| AB2-7.3-02 |  | On i_rst_n_slv assertion (active-low, asynchronous), all slv-block state resets: registers 0, FSM IDLE, including o_apb_psel, o_apb_penable and o_apb_pwakeup. | CHK-010:PASS, CHK-027:PASS | 100.0 % (3/3) | **VERIFIED** |
| AB2-7.3-04 |  | No transfer may start before both resets are released; the requester keeps i_apb_psel low until then. | CHK-027:PASS, CHK-028:PASS | 0.0 % (0/1) **below** | **VERIFIED** |
| AB2-8-02 |  | PARA_APBCDC_ADDR_W, default 32 and legal range 1 to 32, sets the width of PADDR and of the request bundle. | CHK-022:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-8-03 |  | PARA_APBCDC_DATA_W, default 32 and legal values 8, 16 or 32, sets the width of PWDATA and PRDATA; PSTRB has DATA_W/8 bits. | CHK-022:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-8-04 |  | PARA_APBCDC_APB5 selects APB4 (0, default) or APB5 (1); APB5 adds PWAKEUP and the user signals, and user widths apply only when 1. | CHK-001:PASS, CHK-021:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB2-8-05 |  | PARA_APBCDC_USER_REQ_W (0 to 128, default 0) sets the width of PAUSER, only with PARA_APBCDC_APB5 = 1; 0 means no PAUSER. | CHK-001:PASS, CHK-019:NOT_VERIFIABLE | — | **PARTIAL** |
| AB2-8-06 |  | PARA_APBCDC_USER_DATA_W (0 to DATA_W, default 0) sets the width of PWUSER and PRUSER, only with APB5 = 1; 0 means none. | CHK-001:PASS, CHK-019:NOT_VERIFIABLE | — | **PARTIAL** |
| AB2-8-08 |  | PARA_APBCDC_USER_RESP_W (0 to 16, default 0) sets the width of PBUSER, only with PARA_APBCDC_APB5 = 1; 0 means no PBUSER. | CHK-001:PASS, CHK-019:NOT_VERIFIABLE | — | **PARTIAL** |
| AB2-8-09 |  | PARA_APBCDC_HS_TYPE selects two-phase toggle (0, default) or four-phase level (1) handshake; latency and crossing events differ but APB interface function is the same. | CHK-023:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-8-10 |  | PARA_APBCDC_CELL_TYPE (0 to 4, default 2) selects the synchronizer cell option, with N = 2, 2, 3, 4 stages for values 1 to 4. | CHK-030:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-8-11 |  | Value 0 (bypass) is for simulation only and is rejected by the SDC. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-8-12 |  | LPARA_STRB_W is derived as DATA_W / 8, giving 1, 2 or 4. | CHK-022:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-8-13 |  | LPARA_REQ_W equals ADDR_W + 3 + 1 + STRB_W + DATA_W, plus USER_REQ_W and USER_DATA_W in APB5, and is at least 7. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AB2-8-14 |  | LPARA_RESP_W equals DATA_W + 1, plus USER_DATA_W and USER_RESP_W in APB5, and is at least 9. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AB2-8-15 |  | Illegal configurations (bad data/address width, user width over limit or with APB5 = 0, out-of-range options) must not be used; the IP does not check them and behavior is unspecified. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AB2-9-01 |  | The bridge must move the fields unchanged and perform no arithmetic on them. | CHK-029:PASS, CHK-031:PASS | — | **VERIFIED** |
| AB2-9-02 |  | The address is a byte address of width PARA_APBCDC_ADDR_W and is forwarded without extension or truncation. | CHK-022:NOT_VERIFIABLE, CHK-031:PASS | — | **PARTIAL** |
| AB2-9-03 |  | The data word of width PARA_APBCDC_DATA_W is opaque and is forwarded without extension or truncation. | CHK-022:NOT_VERIFIABLE, CHK-031:PASS | — | **PARTIAL** |
| AB2-9-04 |  | Write strobes have width LPARA_STRB_W, one bit per byte lane (bit n for PWDATA bits 8n+7 to 8n), and are forwarded as received without extension or truncation. | CHK-035:PASS | — | **VERIFIED** |
| AB2-9-05 |  | Protection is 3 bits wide, encoded as APB (bit 0 privileged, bit 1 non-secure, bit 2 instruction), and forwarded as received. | CHK-035:PASS | — | **VERIFIED** |
| AB2-9-06 |  | The request bundle of width LPARA_REQ_W packs fields from the least significant bit in order PADDR, PPROT, PWRITE, PSTRB, PWDATA, PAUSER, PWUSER; a zero-width field contributes no bit. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AB2-9-07 |  | The response bundle of width LPARA_RESP_W packs fields from the least significant bit in order PRDATA, PSLVERR, PRUSER, PBUSER; a zero-width field contributes no bit. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AB2-9-08 |  | Request and acknowledge bits are 1 bit wide; in two-phase mode the value toggles per transfer and the request and acknowledge are equal when idle. | CHK-029:PASS | — | **VERIFIED** |
| AB2-9-09 |  | In four-phase mode the request and acknowledge bit is 1 while a phase is requested and 0 when idle. | CHK-023:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-10.1-01 |  | The requester FSM must leave IDLE to WAIT, loading reg_req_payload and toggling reg_req (two-phase) or setting it (four-phase) at the exit edge. | CHK-031:PASS | — | **VERIFIED** |
| AB2-10.1-02 |  | In WAIT the requester must keep o_apb_pready low; on the acknowledge event it goes to RESP (two-phase, raising o_apb_pready) or clears reg_req and goes to CLOSE (four-phase). | CHK-006:PASS, CHK-031:PASS | — | **VERIFIED** |
| AB2-10.1-03 |  | In CLOSE reg_req must be 0; when the synchronized acknowledge falls the FSM loads the response registers, raises o_apb_pready and goes to RESP. | CHK-023:NOT_VERIFIABLE | 50.0 % (1/2) **below** | **NOT_PROVEN** |
| AB2-10.1-04 |  | In RESP o_apb_pready must be high for one cycle, then the FSM returns to IDLE and clears o_apb_pready and o_apb_pslverr at the exit edge. | CHK-004:PASS, CHK-005:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB2-10.1-05 |  | The completer FSM must go to SETUP, loading reg_apb_payload from the request bundle and driving o_apb_psel high at the exit edge. | CHK-017:PASS, CHK-031:PASS | — | **VERIFIED** |
| AB2-10.1-06 |  | In SETUP o_apb_penable must be low; the FSM always moves to ACCESS and sets o_apb_penable high at the exit edge. | CHK-013:PASS | — | **VERIFIED** |
| AB2-10.1-07 |  | On i_apb_pready high the FSM must load reg_resp_hold, drop o_apb_psel and o_apb_penable, toggle (two-phase) or set (four-phase) reg_ack, and go to IDLE (two-phase) or REQ0 (four-phase). | CHK-015:PASS, CHK-031:PASS | — | **VERIFIED** |
| AB2-10.1-08 |  | In REQ0 the FSM must wait for the synchronized request to fall, then clear reg_ack and go to IDLE. | CHK-023:NOT_VERIFIABLE | 50.0 % (1/2) **below** | **NOT_PROVEN** |
| AB2-10.2-01 | REQ-PERF-001, REQ-PERF-002 | The bridge must capture the fields, cross the request, run one APB write on the completer side and return the response, with PREADY for one cycle. | CHK-031:PASS | 100.0 % (9/9) | **VERIFIED** |
| AB2-10.2-02 |  | For a read the bridge must return PRDATA and PRUSER to the requester with PREADY. | CHK-031:PASS | 100.0 % (7/7) | **VERIFIED** |
| AB2-10.2-03 |  | The completer-side Access phase must last w + 1 cycles and requester-side PREADY must follow after the response. | CHK-032:PASS | — | **VERIFIED** |
| AB2-10.2-04 |  | PSLVERR must be carried in the response bundle and be high in the requester-side PREADY cycle. | CHK-033:PASS | — | **VERIFIED** |
| AB2-10.2-05 |  | The mst FSM must be back in IDLE and capture the Setup phase immediately, starting the second transfer at once; one transfer at a time. | CHK-034:PASS | — | **VERIFIED** |
| AB2-10.2-06 |  | o_apb_pwakeup must follow the synchronized wake-up OR the in-progress term and be high before or with o_apb_psel. | CHK-018:NOT_HIT, CHK-020:NOT_VERIFIABLE | 0.0 % (0/2) **below** | **NOT_PROVEN** |
| AB2-10.2-07 |  | PAUSER and PWUSER must cross in the request bundle and PRUSER and PBUSER in the response bundle, with identical values on the other side. | CHK-019:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-10.2-08 |  | State of the domain must clear asynchronously, all registers at reset value, and a transfer in flight is lost. | CHK-027:PASS, CHK-028:PASS | 50.0 % (1/2) **below** | **VERIFIED** |
| AB2-10.2-09 | REQ-PERF-002 | The bridge must use the four-phase handshake and give the same results as OP-001 and OP-002. | CHK-023:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-10.3-02 |  | The slv FSM must see the event at edge N+1 of i_clk_slv, load reg_apb_payload, raise o_apb_psel, then pass SETUP and ACCESS, with o_apb_penable high from the second edge. | CHK-031:PASS | — | **VERIFIED** |
| AB2-10.3-03 |  | At the i_apb_pready edge the response must be held, acknowledge launched, and o_apb_psel and o_apb_penable low. | CHK-015:PASS | — | **VERIFIED** |
| AB2-10.3-04 |  | The mst FSM must load the response and raise o_apb_pready for one cycle, then go to IDLE. | CHK-031:PASS | — | **VERIFIED** |
| AB2-10.4-02 |  | A new Setup phase must not be driven by the requester before PREADY, since APB is non-pipelined. | CHK-029:PASS | — | **VERIFIED** |
| AB2-10.4-03 |  | Duration D from first Setup cycle to end of PREADY cycle must not exceed (N+3)xT_mst + (N+3+w)xT_slv; for equal clocks 2N+6+w cycles. | CHK-025:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-10.4-04 |  | Duration D from first Setup cycle to end of PREADY cycle must not exceed (2N+4)xT_mst + (2N+4+w)xT_slv; for equal clocks 4N+8+w cycles. | CHK-026:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-10.4-05 |  | Throughput is one transfer per duration D, with no pipelining of transfers. | CHK-034:PASS | — | **VERIFIED** |
| AB2-12-01 |  | The bridge must forward the completer PSLVERR so that o_apb_pslverr is high in the o_apb_pready cycle. | CHK-033:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB2-12-02 |  | The next transfer must be independent of a previous transfer that completed with an error. | CHK-033:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB2-12-03 |  | The bridge must wait without limit for PREADY, and the requester sees PREADY low during the wait. | CHK-032:PASS | — | **VERIFIED** |
| AB2-12-05 |  | The in-flight transfer must be lost and all state cleared; both resets must be released and the transfer restarted. | CHK-028:PASS | — | **VERIFIED** |
| AB2-12-06 |  | The bridge must use the values of the Setup cycle and must ignore PENABLE without a Setup; the violation is not detected. | CHK-024:PASS | — | **VERIFIED** |
| AB2-12-08 |  | The bridge must have no sticky error, no error counter and no error output other than PSLVERR. | CHK-005:PASS, CHK-033:PASS | — | **VERIFIED** |
| AB2-13-01 | REQ-PERF-001 | Two-phase transfer duration must be at most (N + 3) x T_mst + (N + 3 + w) x T_slv. | CHK-025:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-13-02 | REQ-PERF-002 | Four-phase transfer duration must be at most (2N + 4) x T_mst + (2N + 4 + w) x T_slv. | CHK-026:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-13-03 | REQ-PERF-003 | Only one transfer is in flight, and the next Setup phase is accepted in the cycle after PREADY. | CHK-034:PASS | — | **VERIFIED** |
| AB2-14.1-01 |  | The RTL must follow the VLSIT RTL Design Rules v2 (REF-003) as the mandatory coding authority. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-14.1-02 |  | The RTL must comply with REF-003 except for the single deviation DEC-021 (PRT-03). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-14.1-03 |  | RTL must use one module per file with file name equal to module name, a structural top, ANSI ports with input wire and output logic, and reg_, w_, p_ff_, p_com_ naming. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-14.1-07 |  | Every flip-flop must have an asynchronous reset to 0. | CHK-027:PASS | — | **VERIFIED** |
| AB2-14.1-08 |  | SVA, testbench or prototype code must not be in the synthesis file list. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-14.1-09 |  | The register and instance names used by the SDC must be kept as named in the RTL. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-14.2-05 |  | There must be no register logic and no protocol adapter other than the two FSMs. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-14.2.1-02 |  | o_req must be a flop output launched at the Setup edge, resetting to 0, toggling per transfer in two-phase and high during the request phase in four-phase. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AB2-14.2.1-03 |  | o_req_payload must be the hold register loaded at the Setup edge, reset 0, valid and stable. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AB2-14.2.1-04 |  | o_wakeup must be a flop output registering i_apb_pwakeup one cycle later, with reset value 0. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AB2-14.2.1-06 |  | i_resp_payload must be valid and stable when the acknowledge event is seen and loaded in CLK-MST at that edge. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AB2-14.2.1-08 |  | i_req_payload must be valid and stable when the request event is seen and loaded in CLK-SLV at that edge. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AB2-14.2.1-10 |  | o_ack must be a flop output launched at the edge that sees i_apb_pready, reset 0, toggling per transfer in two-phase and high during the acknowledge phase in four-phase. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AB2-14.2.1-11 |  | o_resp_payload must be the hold register loaded at the edge that sees i_apb_pready, reset 0, valid and stable. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AB2-14.2.1-12 |  | m_vlsit_apbcdc_sync must sample i_data at every i_clk_dst edge, with o_data from the last stage, N stages later, resetting to 0 on active-low i_rst_n_dst. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AB2-14.2.1-14 |  | Pin and cell names of library cells may keep the library style and are exempt from the naming rule. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-15.1-01 |  | Metastability behaviour, reset in the middle of random traffic and the APB protocol assertions shall be verified on the RTL. | CHK-028:PASS, CHK-029:PASS | — | **VERIFIED** |
| AB2-15.1-03 | REQ-APB5-001 | Every third configuration uses a requester changing fields in the Access phase to check Setup values are used, and every third APB5 configuration uses a requester never driving PWAKEUP. | CHK-020:NOT_VERIFIABLE, CHK-024:PASS | — | **PARTIAL** |
| AB2-15.1-04 | REQ-APB5-001 | All 12 RTL waveforms must match the figure WaveJSON, internal rows included, and assertions must pass in the metastability branch for each scenario. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-15.1-05 |  | The fault of the completer side loading its request register every cycle instead of at the request event must be shown by the structural check (TEST-015) and the SDC (TEST-016). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-15.2-02 | REQ-CLK-003, REQ-PARAM-001 | Elaboration, lint and simulation must pass for the legal parameter extremes. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-15.3-01 |  | Assertions and coverage are disabled while either reset is asserted, except SVA-016 which remains enabled. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| AB2-15.3-02 | REQ-FUNC-004 | When o_apb_pready is high, i_apb_psel and i_apb_penable must be high (SVA-001, never fails). | CHK-003:PASS | — | **VERIFIED** |
| AB2-15.3-03 | REQ-FUNC-004 | o_apb_pready must be high for exactly one cycle per transfer (SVA-002). | CHK-004:PASS, CHK-006:PASS | — | **VERIFIED** |
| AB2-15.3-04 | REQ-FUNC-006 | o_apb_pslverr high must imply o_apb_pready high (SVA-003). | CHK-005:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB2-15.3-05 | REQ-FUNC-002 | The requester-side response must equal the completer-side response of the same transfer (SVA-004, checked by scoreboard). | CHK-029:PASS | — | **VERIFIED** |
| AB2-15.3-06 | REQ-FUNC-008 | o_apb_penable must rise one cycle after o_apb_psel, and o_apb_penable high must imply o_apb_psel high (SVA-005). | CHK-012:PASS, CHK-013:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB2-15.3-07 | REQ-FUNC-008 | Completer-side fields must not change while o_apb_psel is high and i_apb_pready is low (SVA-006). | CHK-016:PASS | — | **VERIFIED** |
| AB2-15.3-08 | REQ-FUNC-008 | o_apb_psel and o_apb_penable must be low when no transfer is in progress and in reset (SVA-007). | CHK-010:PASS, CHK-015:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB2-15.3-09 | REQ-FUNC-001 | Completer-side fields must equal the values of the requester-side Setup cycle (SVA-008, checked by scoreboard). | CHK-029:PASS | — | **VERIFIED** |
| AB2-15.3-10 | REQ-FUNC-003 | The number of completer-side transfers must equal the number of requester-side transfers (SVA-009, scoreboard). | CHK-029:PASS | — | **VERIFIED** |
| AB2-15.3-11 | REQ-FUNC-003 | No second completer-side Setup phase may occur before o_apb_pready of the previous transfer (SVA-010). | CHK-029:PASS | — | **VERIFIED** |
| AB2-15.3-12 | REQ-HS-002 | The request hold register must be stable from request launch until acknowledge is seen, and the response hold register stable from acknowledge launch until the next request is seen (SVA-011). | CHK-029:PASS | — | **VERIFIED** |
| AB2-15.3-13 | REQ-HS-001 | In two-phase handshake the request bit must change exactly once and the acknowledge bit exactly once per transfer (SVA-012). | CHK-029:PASS | — | **VERIFIED** |
| AB2-15.3-14 | REQ-HS-001, REQ-HS-004 | In four-phase handshake the sequence must be request high, acknowledge high, request low, acknowledge low, then o_apb_pready (SVA-013). | CHK-023:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-15.3-15 | REQ-APB5-001 | o_apb_pwakeup must be high no later than o_apb_psel (SVA-014). | CHK-018:NOT_HIT | 50.0 % (1/2) **below** | **NOT_PROVEN** |
| AB2-15.3-16 | REQ-APB5-001 | o_apb_pwakeup must stay high until i_apb_pready when it is high with o_apb_psel (SVA-015). | CHK-018:NOT_HIT | 0.0 % (0/1) **below** | **NOT_PROVEN** |
| AB2-15.3-17 | REQ-RESET-001 | In reset every output must be at its reset value (SVA-016). | CHK-009:PASS, CHK-010:PASS | 100.0 % (6/6) | **VERIFIED** |
| AB2-15.3-18 | REQ-IF-003 | After reset no output may be unknown; o_apb_prdata must not be unknown when o_apb_pready of a read is high (SVA-017). | CHK-008:PASS, CHK-011:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB2-15.3-19 | REQ-PERF-001, REQ-PERF-002 | The duration of every transfer must be within the bound of REQ-PERF-001 or REQ-PERF-002 (SVA-018). | CHK-025:NOT_VERIFIABLE, CHK-026:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-15.4-02 |  | A CDC tool or the structural check of TEST-015 must confirm only control bits pass through synchronizers, no logic precedes a first stage, and no other path joins the domains across the five crossings. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-16-01 |  | The RTL shall contain no latch, no combinational loop, no tri-state, no clock gating and no derived clock, so that scan insertion is possible. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-16-02 |  | The IP shall have no DFT ports; a test reset override belongs to the SoC wrapper or reset controller. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-17.1.2-01 |  | EXC-001 shall constrain reg_req_payload to reg_apb_payload with set_max_delay -ignore_clock_latency of (N - 1) x T_slv and set_false_path -hold, hold not checked. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-17.1.2-02 |  | EXC-002 shall constrain reg_req to u_sync_req cells with maximum delay T_slv, ignoring clock latency, and hold not checked. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-17.1.2-03 |  | EXC-003 shall constrain reg_ack to u_sync_ack cells with maximum delay T_mst, ignoring clock latency, and hold not checked. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-17.1.2-04 |  | EXC-004 shall constrain reg_resp_hold (slv) to reg_resp_payload (mst) with maximum delay (N - 1) x T_mst, ignoring clock latency, hold not checked. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-17.1.2-05 |  | EXC-005 shall constrain reg_wakeup to u_sync_wk cells with maximum delay T_slv, ignoring clock latency, and hold not checked. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-17.1.2-06 |  | Required max transition, max capacitance and max fanout shall follow the project defaults. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-17.1.3-01 | REQ-TIM-002 | The SDC shall not use set_clock_groups -asynchronous, set_false_path, or set_max_delay without the latency option between clk_mst and clk_slv. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-17.1.4-02 |  | The bundle shall be stable at the destination flop before the control bit, having crossed N synchronizer stages, tells the destination FSM to load it. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |
| AB2-17.1.4-04 | REQ-TIM-003 | The post-CTS clock latency difference shall stay below the one destination period guard band (REQ-TIM-003). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-17.2-01 |  | Each launch flop of a crossing control bit and its first synchronizer stage shall be placed adjacent. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-17.2-02 |  | The two bundle registers of each direction should be placed close to each other. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-20.1-01 |  | The clock controller of the slv domain shall act on i_apb_pwakeup (or on a requester signal) before the request arrives, since the bridge cannot see requests while the clock is stopped. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AB2-20.2-01 |  | The APB requester must issue one Setup phase then Access until PREADY, keep fields stable, and keep PSTRB low in a read. | CHK-029:PASS | — | **VERIFIED** |
| AB2-20.2-02 |  | The clock controller using PWAKEUP must keep i_clk_slv running while a request is in flight, since the bridge cannot detect a request on a stopped clock. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AB2-20.2-04 |  | One parameter selects APB4 or APB5; APB5 adds PWAKEUP and user signals with configurable widths; no parity check signals are provided. | CHK-019:NOT_VERIFIABLE, CHK-021:PASS | — | **PARTIAL** |
| AB2-20.2-05 |  | ADDR_W defaults to 32 (range 1 to 32), DATA_W defaults to 32 (8, 16 or 32), PSTRB and PPROT are always present, and user widths default to 0. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB2-20.2-06 | REQ-FUNC-004, REQ-IF-002 | Every APB output must be a flip-flop output; PREADY must be high only in state RESP, i.e. only once the Access phase has been reached. | CHK-002:PASS, CHK-003:PASS | — | **VERIFIED** |
| AB2-20.2-07 | REQ-HS-004 | The response must be delivered only after the handshake has closed (acknowledge low), so the next Setup phase can always be accepted. | CHK-023:NOT_VERIFIABLE | — | **NOT_PROVEN** |
| AB2-20.2-08 | REQ-IF-001 | The RTL top must declare the APB5 ports in every configuration, with user widths of at least 1, unused inputs ignored and unused outputs 0. | CHK-001:PASS, CHK-021:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB2-21-01 |  | Multi-bit bundled data must be held stable while the one-bit control signal crosses the domains. | CHK-024:PASS, CHK-029:PASS | — | **VERIFIED** |
| AB2-21-02 |  | The destination must load the bundled multi-bit data only after the control signal has arrived. | not verified: not_observable_at_interface | — | **NOT_VERIFIED_BY_SIM** |

## Mutants

| ID | File:line | Operator | Status | Caught by | Rules | Equivalent? |
|---|---|---|---|---|---|---|
| M01 | m_vlsit_apbcdc_mst.sv:192 | one_to_zero | survived |  | AB2-3-25, AB2-3-26, AB2-1.3-04, AB2-5.3-09, AB2-10.1-03 |  |
| M02 | m_vlsit_apbcdc_mst.sv:214 | ne_to_eq | survived |  | AB2-3-42, AB2-1.3-06, AB2-5.3-12, AB2-7.2-09, AB2-10.2-06 |  |
| M03 | m_vlsit_apbcdc_slv.sv:179 | one_to_zero | survived |  | AB2-3-25, AB2-3-26, AB2-1.3-04, AB2-5.3-10, AB2-10.1-08 |  |
| M04 | m_vlsit_apbcdc_slv.sv:179 | eq_to_ne | killed | test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_two_phase_duration | AB2-1.3-03, AB2-10.2-02, AB2-3-01, AB2-3-25, AB2-3-08 |  |
| M05 | m_vlsit_apbcdc_mst.sv:137 | eq_to_ne | killed | test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_two_phase_duration | AB2-1.3-03, AB2-10.2-02, AB2-3-01, AB2-6.3-20, AB2-3-08 |  |
| M06 | m_vlsit_apbcdc_slv.sv:134 | ne_to_eq | killed | test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_two_phase_duration | AB2-1.3-01, AB2-3-01, AB2-10.2-01, AB2-5.3-02, AB2-6.3-20 |  |
| M07 | m_vlsit_apbcdc_slv.sv:202 | zero_to_one | killed | CHK-010, CHK-001, test_chk_027_reset_values, test_chk_028_reset_during_traffic | AB2-7.3-02, AB2-15.3-17, AB2-3-38, AB2-5.4-06, AB2-15.3-08 |  |
| M08 | m_vlsit_apbcdc_cell_sync.sv:173 | zero_to_one | survived |  |  | claimed: The sim_pend flag stays set after the delayed value has been copied. On later cycles the pending branch only re-copies sim_nxt, which equals the current value,  |
| M09 | m_vlsit_apbcdc_cell_sync.sv:140 | ne_to_eq | survived |  |  |  |
| M10 | m_vlsit_apbcdc_mst.sv:162 | negate_if | killed | CHK-003, CHK-006, test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_ | AB2-6.3-24, AB2-5.4-01, AB2-10.2-01, AB2-3-01, AB2-1.3-01 |  |
| M11 | m_vlsit_apbcdc_cell_sync.sv:162 | eq_to_ne | killed | test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_two_phase_duration | AB2-3-01, AB2-10.2-01, AB2-10.2-02, AB2-1.3-01, AB2-3-27 |  |
| M12 | m_vlsit_apbcdc_cell_sync.sv:136 | one_to_zero | survived |  |  |  |
| M13 | m_vlsit_apbcdc_cell_sync.sv:162 | negate_if | killed | test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_two_phase_duration | AB2-3-01, AB2-10.2-01, AB2-10.2-02, AB2-1.3-01, AB2-3-27 |  |
| M14 | m_vlsit_apbcdc_slv.sv:159 | negate_if | killed | CHK-017, CHK-003, CHK-006, test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test | AB2-10.2-01, AB2-5.3-02, AB2-3-01, AB2-1.3-01, AB2-3-15 |  |
| M15 | m_vlsit_apbcdc_mst.sv:211 | zero_to_one | killed | CHK-009, CHK-003, CHK-006, test_chk_027_reset_values, test_chk_028_reset_during_traffic | AB2-7.3-01, AB2-15.3-17, AB2-3-37, AB2-5.4-06, AB2-7.2-04 |  |
| M16 | m_vlsit_apbcdc_slv.sv:180 | eq_to_ne | killed | test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_two_phase_duration | AB2-3-26, AB2-3-25, AB2-10.1-08, AB2-5.3-10, AB2-1.3-04 |  |
| M17 | m_vlsit_apbcdc_mst.sv:192 | eq_to_ne | killed | test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_two_phase_duration | AB2-3-25, AB2-3-26, AB2-1.3-04, AB2-5.3-09, AB2-10.1-03 |  |
| M18 | m_vlsit_apbcdc_slv.sv:208 | ne_to_eq | survived |  | AB2-15.3-16, AB2-3-43, AB2-15.3-15, AB2-6.3-13, AB2-10.2-06, AB2-3-42 |  |
| M19 | m_vlsit_apbcdc_slv.sv:199 | zero_to_one | killed | CHK-003, CHK-006, test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_ | AB2-7.2-04, AB2-7.2-08, AB2-3-17, AB2-5.4-03, AB2-10.2-08 |  |
| M20 | m_vlsit_apbcdc_cell_sync.sv:164 | zero_to_one | killed | test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_two_phase_duration | AB2-3-01, AB2-10.2-01, AB2-10.2-02, AB2-1.3-01, AB2-3-27 |  |
| M21 | m_vlsit_apbcdc_mst.sv:208 | negate_if | killed | CHK-009, test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_two_phase | AB2-7.3-01, AB2-3-37, AB2-3-38, AB2-5.4-06, AB2-15.3-17 |  |
| M22 | m_vlsit_apbcdc_cell_sync.sv:171 | eq_to_ne | survived |  |  |  |
| M23 | m_vlsit_apbcdc_cell_sync.sv:168 | one_to_zero | killed | test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_two_phase_duration | AB2-3-01, AB2-10.2-01, AB2-10.2-02, AB2-1.3-01, AB2-3-27 |  |
| M24 | m_vlsit_apbcdc_cell_sync.sv:171 | negate_if | survived |  |  |  |
| M25 | m_vlsit_apbcdc_slv.sv:227 | negate_if | killed | test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_two_phase_duration | AB2-6.3-22, AB2-12-01, AB2-12-02, AB2-6.3-10, AB2-3-03 |  |
| M26 | m_vlsit_apbcdc_mst.sv:210 | zero_to_one | survived |  | AB2-7.3-04, AB2-10.2-08, AB2-3-38, AB2-7.2-11, AB2-5.4-06 |  |
| M27 | m_vlsit_apbcdc_slv.sv:206 | eq_to_ne | killed | CHK-012, CHK-013, CHK-014, CHK-017, test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violati | AB2-3-14, AB2-3-15, AB2-6.3-01, AB2-15.3-06, AB2-5.3-05 |  |
| M28 | m_vlsit_apbcdc_mst.sv:235 | eq_to_ne | killed | CHK-004, CHK-005, test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_ | AB2-3-11, AB2-3-23, AB2-15.3-04, AB2-6.2-01, AB2-6.3-09, AB2-10.1-04 |  |
| M29 | m_vlsit_apbcdc_slv.sv:207 | ne_to_eq | killed | CHK-001, test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_two_phase | AB2-20.2-08, AB2-3-45, AB2-8-04, AB2-3-43, AB2-15.3-15 |  |
| M30 | m_vlsit_apbcdc_slv.sv:200 | zero_to_one | killed | CHK-013, CHK-010, test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_ | AB2-7.3-02, AB2-15.3-17, AB2-3-38, AB2-5.4-06, AB2-15.3-08 |  |
| M31 | m_vlsit_apbcdc_cell_sync.sv:154 | zero_to_one | killed | CHK-003, CHK-006, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_two_phase_duration/periods=0, te | AB2-5.4-03, AB2-7.2-04, AB2-3-38, AB2-3-37, AB2-15.3-18 |  |
| M32 | m_vlsit_apbcdc_mst.sv:200 | negate_if | killed | test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_two_phase_duration | AB2-7.3-01, AB2-3-37, AB2-5.4-06, AB2-7.2-04, AB2-15.3-17 |  |
| M33 | m_vlsit_apbcdc_cell_sync.sv:158 | negate_if | killed | test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_two_phase_duration | AB2-3-01, AB2-10.2-01, AB2-10.2-02, AB2-1.3-01, AB2-3-27 |  |
| M34 | m_vlsit_apbcdc_slv.sv:187 | negate_if | killed | CHK-012, CHK-013, CHK-014, test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test | AB2-7.3-02, AB2-3-38, AB2-15.3-17, AB2-5.4-06, AB2-7.2-04 |  |
| M35 | m_vlsit_apbcdc_mst.sv:236 | zero_to_one | killed | CHK-004, CHK-005, test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_ | AB2-3-11, AB2-3-23, AB2-15.3-04, AB2-6.2-01, AB2-6.3-09, AB2-10.1-04 |  |
| M36 | m_vlsit_apbcdc_slv.sv:138 | eq_to_ne | killed | CHK-016, CHK-017, test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_ | AB2-10.2-01, AB2-5.3-02, AB2-3-01, AB2-1.3-01, AB2-3-22 |  |

## Not verified by this run

- Formal proof, CDC/RDC, STA, synthesis and DFT checks are outside this flow.
- Rules marked NOT_VERIFIED_BY_SIM carry the contract's reason (static, structural, not observable...).
- Only the default parameter configuration was simulated unless stated above.

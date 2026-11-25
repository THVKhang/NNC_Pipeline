# Verification report — ahb2axi_bridge

Generated 2026-11-25T12:45:27+00:00 by NNC Pipeline.

## Summary

| Item | Result |
|---|---|
| Rules | 234 — {'FAILED': 143, 'NOT_PROVEN': 1, 'NOT_VERIFIED_BY_SIM': 57, 'VERIFIED': 33} |
| Checks | 40 — {'FAIL': 26, 'NOT_HIT': 1, 'PASS': 13} |
| Tests | {'fail': 20, 'pass': 1} |
| Run set | 5 runs in 4 configurations (base, ids8, ids35, xrand); primary base.s1 |
| Integration | OK |
| Code coverage (RTL), line | 91.3 % (2733/2992 lines); 185 points left out (package code the design does not contain), all points 86.0 % (2733/3177) |
| Code coverage (RTL), block | 97.3 % (1142/1174 statement blocks and branch arms); 308 points left out (package code the design does not contain; 308 of them proven never reached after reset by formal, work/unr.md), all points 77.1 % (1142/1482) |
| Code coverage (RTL), expression | 86.4 % (1316/1524 condition terms); 306 points left out (package code the design does not contain; 306 of them proven never reached after reset by formal, work/unr.md), all points 71.9 % (1316/1830) |
| Code coverage (RTL), toggle | 91.5 % (23591/25770 bit toggles 0->1 and 1->0); 10224 points left out (constant bits; 3936 of them proven constant after reset by formal, work/unr.md), all points 65.7 % (23645/35994) |
| Code coverage (RTL), functional | 90.0 % (36/40 cover points of the specification) |
| Mutation score | not run |
| Coverage target | not requested (`nnc cover <design> --target <n> --metric <m>`) |
| Clock/reset domain crossings (structural, `nnc cdc`) | clean: no crossing over 3 configuration(s), work/cdc.md |
| Formal (SymbiYosys, depth 20) | {'BOUNDED': 2, 'CEX': 9, 'PROVEN': 8, 'VACUOUS': 1} — reset assumptions + verif/formal/nnc_env.sv, work/formal.md |
| Triage | 26 failure(s), 12 analysed: work/triage.md |
| Agent cost | US$22.2961 in 71 calls (A1 0.871, A13 0.4926, A14 2.8678, A2 0.807, A3 0.3803, A4 1.9029, A5 0.7498, A6 0.3123, A7 8.7386, A9 5.1738); of which US$3.3148 in 5 failed calls (usage limit, timeout, invalid answer) |

## Sign-off conditions

| Condition | State |
|---|---|
| Gates G1-G3 approved | met — approved on delegation by an agent: a person should confirm |
| Interface conformance of the DUT | met |
| Every selected check PASS (no FAIL, NOT_HIT, NOT_RUN) | **not met** — FAIL 26, NOT_HIT 1 |
| Every planned check selected | met |
| Every rule in a check or declared not verifiable | met |
| Every run of the run set built and ran | met — 5 runs |
| Mutation run | **not met** — nnc mutate <design> |
| Clock/reset domain crossings: no structural violation (RR-33) | met — clean: no crossing (work/cdc.md) |
| Formal: no counterexample, no vacuous or failed proof | **not met** — CEX 9, VACUOUS 1 |

## Run set

Every check is merged over these runs: PASS when one run verified it and no run failed it; NOT_VERIFIABLE only when every run declared it so.

| Run | Parameters changed | Defines | Plusargs | Status | Tests | Failing assertions | Not verifiable here |
|---|---|---|---|---|---|---|---|
| base.s1 — defaults (one ID per direction) | defaults | — | — | ran | {'fail': 20, 'pass': 1} | CHK-002, CHK-015, CHK-016, CHK-017, CHK-020 | 1 |
| base.s2 — defaults (one ID per direction) | defaults | — | — | ran | {'fail': 20, 'pass': 1} | CHK-002, CHK-005, CHK-015, CHK-016, CHK-017, CHK-020 | 1 |
| ids8.s1 — eight IDs per direction | PARA_RD_ID_COUNT=8, PARA_WR_ID_COUNT=8 | — | — | ran | {'fail': 20, 'pass': 1} | CHK-002, CHK-015, CHK-016, CHK-017, CHK-020 | 1 |
| ids35.s1 — three read IDs, five write IDs | PARA_RD_ID_COUNT=3, PARA_WR_ID_COUNT=5 | — | — | ran | {'fail': 20, 'pass': 1} | CHK-002, CHK-015, CHK-016, CHK-017, CHK-020 | 1 |
| xrand.s1 — the default configuration with random initial values of every variable without a reset (ROADMAP 23.4): a check that passes only because flops start at 0 fails here; its coverage is not merged | defaults | — | — | ran | {'fail': 20, 'pass': 1} | CHK-002, CHK-012, CHK-015, CHK-016, CHK-017, CHK-020 | 1 |

## Gates

| Gate | State | Detail |
|---|---|---|
| G1_rules | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-12T16:11:43+00:00 |
| G2_contract | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-12T16:22:11+00:00 |
| G3_verif_sources | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-14T15:41:48+00:00 |
| G4_signoff | PENDING | artifacts ready for review |

## Checks

| Check | Kind | Title | Status | Evidence |
|---|---|---|---|---|
| CHK-001 | assertion | AHB ERROR is a two-cycle response | **PASS** | hits 339, fails 0; hit in 5/5 runs; formal CEX |
| CHK-002 | assertion | IDLE and BUSY transfers get zero-wait OKAY | **FAIL** | hits 25488, fails 19; fails in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1; formal CEX |
| CHK-003 | assertion | AXI lock outputs tied low | **PASS** | hits 17333575, fails 0; hit in 5/5 runs; formal PROVEN |
| CHK-004 | assertion | Reads are always single-beat INCR | **PASS** | hits 17333575, fails 0; hit in 5/5 runs; formal PROVEN |
| CHK-005 | assertion | AW VALID and payload stable until AWREADY | **FAIL** | hits 18351, fails 2; fails in base.s2; formal CEX |
| CHK-006 | assertion | W VALID and payload stable until WREADY | **PASS** | hits 17131, fails 0; hit in 5/5 runs; formal PROVEN |
| CHK-007 | assertion | AR VALID and payload stable until ARREADY | **PASS** | hits 17736, fails 0; hit in 5/5 runs; formal PROVEN |
| CHK-008 | assertion | At most one outstanding read and one outstanding write | **PASS** | hits 116044, fails 0; hit in 5/5 runs; formal PROVEN |
| CHK-009 | assertion | AXI IDs stay below the configured ID count | **PASS** | hits 48986, fails 0; hit in 5/5 runs; formal PROVEN |
| CHK-010 | assertion | W beat count and WLAST match AWLEN | **PASS** | hits 6763, fails 0; hit in 5/5 runs; formal BOUNDED |
| CHK-011 | assertion | AW burst shape is legal and never crosses 4 KiB | **PASS** | hits 25114, fails 0; hit in 5/5 runs; formal CEX |
| CHK-012 | assertion | Issued AXI requests use supported sizes and are aligned | **FAIL** | hits 48986, fails 10; fails in xrand.s1; formal CEX |
| CHK-013 | assertion | No AR before the matching AHB read is accepted | **PASS** | hits 23872, fails 0; hit in 5/5 runs; formal BOUNDED |
| CHK-014 | assertion | No AXI write burst before the full AHB fixed burst is accepted | **NOT_HIT** | hits 0, fails 0; hit in 0/5 runs; formal VACUOUS |
| CHK-015 | assertion | AHB read completes only with its R beat and carries RDATA unchanged | **FAIL** | hits 10889, fails 4779; fails in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1; formal CEX |
| CHK-016 | assertion | Waiting-class writes complete only after their BRESP | **FAIL** | hits 12260, fails 12207; fails in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1; formal CEX |
| CHK-017 | assertion | Locally rejected transfers end in ERROR and produce no W data | **FAIL** | hits 6929, fails 5; fails in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1; formal CEX |
| CHK-018 | assertion | AHB outputs hold reset values during reset | **PASS** | hits 564, fails 0; hit in 5/5 runs; formal PROVEN |
| CHK-019 | assertion | AXI VALID/READY outputs suppressed during reset | **PASS** | hits 564, fails 0; hit in 5/5 runs; formal PROVEN |
| CHK-020 | assertion | AXI payload outputs hold reset values during reset | **FAIL** | hits 564, fails 563; fails in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1; formal CEX |
| CHK-021 | test | Only HSEL&HREADY&HTRANS[1] address phases create AXI traffic | **FAIL** | test_chk_021_accept_qualifiers; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-022 | test | AXI outputs have no combinational dependency on READY | **FAIL** | test_chk_022_no_comb_ready_path; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-023 | test | Device and non-bufferable fixed write bursts are serialized as singles | **FAIL** | test_chk_023_device_bursts_singles; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-024 | test | Eligible Normal Write-back fixed write bursts: optional aggregation, early OKAY, terminal waits for B | **FAIL** | test_chk_024_wb_burst_aggregation; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-025 | test | Varying burst-scoped attributes force ordered singles | **FAIL** | test_chk_025_varying_attrs_singles; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-026 | test | Early-terminated fixed write burst drains captured prefix as singles | **FAIL** | test_chk_026_early_termination; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-027 | test | Defensive 4 KiB split preserves order and aggregates responses | **FAIL** | test_chk_027_4k_split; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-028 | test | Write BRESP error mapping and aggregation | **FAIL** | test_chk_028_bresp_errors; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-029 | test | Read RRESP error mapping | **FAIL** | test_chk_029_rresp_errors; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-030 | test | Unsupported AHB controls rejected with ERROR and no AXI request | **PASS** | test_chk_030_rejected_controls; verified in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-031 | test | Rejected transfer after a captured write prefix drains the prefix first | **FAIL** | test_chk_031_reject_after_prefix; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-032 | test | Independent AXI ID rotation per direction with ID count > 1 | **FAIL** | test_chk_032_id_rotation; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-033 | test | Mixed random traffic: ordering, no loss, no duplication | **FAIL** | test_chk_033_mixed_ordering, test_regression_random; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-034 | test | AR/AW issue latency at most 6 cycles under free conditions | **FAIL** | test_chk_034_issue_latency; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-035 | test | READY stalls and missing responses: stable signals, no timeout, no retry | **FAIL** | test_chk_035_stalls_no_timeout; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-036 | test | Independent AHB5/AXI4 protocol compliance with injected endpoint violations | **FAIL** | test_chk_036_protocol_checkers; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-037 | test | Read conversion and attribute mapping scoreboard | **FAIL** | test_chk_037_read_scoreboard; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-038 | test | Asynchronous reset assertion, inputs ignored during reset, no acceptance before release | **FAIL** | test_chk_038_async_reset; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-039 | test | Reset during in-flight transactions discards state | **FAIL** | test_chk_039_reset_inflight; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |
| CHK-040 | test | SINGLE and undefined-INCR write conversion and byte-lane scoreboard | **FAIL** | test_chk_040_write_scoreboard; failed in base.s1, base.s2, ids8.s1, ids35.s1, xrand.s1 |

## Requirement traceability (RTM)

| Rule | Spec ref | Statement | Checks | Mutation | Status |
|---|---|---|---|---|---|
| AA-1.1-01 |  | The bridge must serialize reads and must never issue speculative reads. | CHK-008:PASS, CHK-013:PASS, CHK-015:FAIL | — | **FAILED** |
| AA-1.1-02 |  | The bridge may aggregate eligible bufferable Normal Write-back AHB write bursts into AXI4 bursts of up to 16 beats. | CHK-024:FAIL | — | **FAILED** |
| AA-1.1-03 |  | The bridge must never merge Device writes. | CHK-023:FAIL | — | **FAILED** |
| AA-1.1-04 |  | Reads must always use AXI single-beat transactions. | CHK-004:PASS, CHK-037:FAIL | — | **FAILED** |
| AA-1.3-04 | REQ-FUNC-005, REQ-PERF-001 | The bridge must support conditional aggregation of bufferable Normal Write-back fixed writes up to 16 beats (FEAT-004). | CHK-024:FAIL | — | **FAILED** |
| AA-1.3-05 | REQ-PARAM-001 | Rotating AXI read/write IDs are an optional configuration with ID-count parameters 1..8, default 1. | CHK-032:FAIL | — | **FAILED** |
| AA-1.3-06 | REQ-FUNC-006, REQ-IF-001 | The bridge must convert AHB HWSTRB to AXI WSTRB (FEAT-007). | CHK-040:FAIL | — | **FAILED** |
| AA-2.1-01 |  | The RTL shall follow the VLSIT RTL Design Rules v2 (REF-003) as the mandatory baseline for naming, hierarchy, single-clock, reset and synthesis. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-2.2-01 |  | User-approved decisions in §20 may restrict legal protocol behavior but must not contradict it. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| AA-3-01 | REQ-VER-001 | Verification must be derived from this specification and REF-001/REF-002, not from generated RTL or internal RTL names/structure. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| AA-3-02 | REQ-FUNC-001 | The bridge must convert every accepted supported AHB transfer to AXI4 without loss, duplication or data alteration. | CHK-024:FAIL, CHK-033:FAIL, CHK-037:FAIL, CHK-040:FAIL | — | **FAILED** |
| AA-3-03 | REQ-FUNC-002 | AHB address/control must be sampled only when HSEL=1, HREADY=1 and HTRANS is NONSEQ or SEQ. | CHK-013:PASS, CHK-021:FAIL | — | **FAILED** |
| AA-3-04 | REQ-FUNC-002 | IDLE or BUSY transfers must not issue AXI requests. | CHK-021:FAIL | — | **FAILED** |
| AA-3-05 | REQ-FUNC-003 | Each accepted AHB read must issue exactly one AXI single-beat AR transaction. | CHK-015:FAIL, CHK-037:FAIL | — | **FAILED** |
| AA-3-06 | REQ-FUNC-003 | No read request may be issued before its AHB address is accepted. | CHK-013:PASS | — | **VERIFIED** |
| AA-3-07 | REQ-FUNC-004 | AHB SINGLE and undefined-length INCR transfers and every read beat must map to AXI single-beat transactions. | CHK-037:FAIL, CHK-040:FAIL | — | **FAILED** |
| AA-3-08 | REQ-FUNC-005 | Such a write burst may map to a matching AXI burst only after all data beats are captured and burst-scoped attributes are constant. | CHK-014:NOT_HIT, CHK-024:FAIL | — | **FAILED** |
| AA-3-09 | REQ-FUNC-005 | Otherwise the bridge must issue ordered AXI single-beat writes. | CHK-023:FAIL, CHK-025:FAIL | — | **FAILED** |
| AA-3-10 | REQ-FUNC-005 | Non-bufferable writes must use single-beat AXI transactions. | CHK-023:FAIL | — | **FAILED** |
| AA-3-11 | REQ-FUNC-006 | AXI WDATA/WSTRB must preserve each AHB HWDATA/HWSTRB beat. | CHK-024:FAIL, CHK-040:FAIL | — | **FAILED** |
| AA-3-12 | REQ-FUNC-006 | WLAST must identify the final beat of each AXI write transaction. | CHK-010:PASS | — | **VERIFIED** |
| AA-3-13 | REQ-FUNC-007 | AHB responses must remain in transfer order. | CHK-024:FAIL, CHK-033:FAIL | — | **FAILED** |
| AA-3-14 | REQ-FUNC-007 | All B statuses must be combined and any error reported on the terminal AHB beat. | CHK-024:FAIL, CHK-028:FAIL | — | **FAILED** |
| AA-3-15 | REQ-FUNC-007 | Earlier beats may receive OKAY once safely buffered. | CHK-024:FAIL | — | **FAILED** |
| AA-3-16 | REQ-FUNC-008 | Device memory transfers must not be merged or have their size changed. | CHK-023:FAIL | — | **FAILED** |
| AA-3-17 | REQ-FUNC-008 | Device-E writes must use ordered AXI single-beat transactions and wait for each final-destination BRESP before the AHB response. | CHK-016:FAIL, CHK-023:FAIL | — | **FAILED** |
| AA-3-18 | REQ-FUNC-008 | No early AHB write response is allowed without a visibility guarantee. | CHK-016:FAIL, CHK-023:FAIL | — | **FAILED** |
| AA-3-19 | REQ-FUNC-009 | An early-terminated fixed write burst must never produce an incomplete AXI burst. | CHK-026:FAIL | — | **FAILED** |
| AA-3-20 | REQ-FUNC-009 | Captured but unissued accepted write beats must be emitted as ordered AXI single-beat transactions without reissuing beats already sent. | CHK-026:FAIL | — | **FAILED** |
| AA-3-21 | REQ-FUNC-009 | The terminal AHB response must be held until all corresponding B responses arrive, and any non-OKAY status reported on it. | CHK-016:FAIL, CHK-026:FAIL | — | **FAILED** |
| AA-3-22 | REQ-FUNC-010 | No AXI burst may cross a 4 KiB boundary. | CHK-011:PASS, CHK-027:FAIL | — | **FAILED** |
| AA-3-23 | REQ-FUNC-010 | The bridge must preserve beat order and aggregate all sub-burst responses onto the final AHB beat. | CHK-027:FAIL | — | **FAILED** |
| AA-3-24 | REQ-IF-001 | The single top module m_ahb2axi_top must expose exactly the fixed clock, reset, AHB and AXI ports listed in §6.2. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-3-26 | REQ-CLK-001 | AHB and AXI interfaces must use the same rising-edge clock input i_clk_core. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-3-27 | REQ-CLK-001 | No second clock port or clock-domain crossing is permitted. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-3-28 | REQ-RESET-001 | The bridge must expose one active-low reset input i_rst_n_core and use it directly without an internal reset synchronizer. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-3-29 | REQ-RESET-001 | The SoC reset source must synchronize deassertion to i_clk_core before the reset reaches the IP. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AA-3-30 | REQ-RESET-001 | Reset must clear all bridge/FIFO valid state. | CHK-019:PASS, CHK-038:FAIL, CHK-039:FAIL | — | **FAILED** |
| AA-3-31 | REQ-RESET-001 | No pre-reset response may be returned after reset release. | CHK-039:FAIL | — | **FAILED** |
| AA-3-32 | REQ-ERR-001 | AXI OKAY must map to AHB OKAY. | CHK-015:FAIL, CHK-029:FAIL, CHK-037:FAIL, CHK-040:FAIL | — | **FAILED** |
| AA-3-33 | REQ-ERR-001 | These must map to the AHB two-cycle ERROR response. | CHK-015:FAIL, CHK-028:FAIL, CHK-029:FAIL | — | **FAILED** |
| AA-3-34 | REQ-ERR-002 | Such transfers must return two-cycle AHB ERROR. | CHK-017:FAIL, CHK-030:PASS | — | **FAILED** |
| AA-3-35 | REQ-ERR-002 | No AXI request must be issued for the rejected transfer. | CHK-017:FAIL, CHK-030:PASS | — | **FAILED** |
| AA-3-36 | REQ-PARAM-001 | Read and write ID-count parameters must be in the range 1..8. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-3-37 | REQ-PARAM-001 | Each direction must rotate IDs through 0..count-1. | CHK-009:PASS, CHK-032:FAIL | — | **FAILED** |
| AA-3-39 | REQ-PERF-001 | The bridge may accept one AHB beat per i_clk_core cycle. | CHK-024:FAIL | — | **FAILED** |
| AA-3-40 | REQ-PERF-001 | Terminal completion must wait for all required BRESPs. | CHK-016:FAIL, CHK-024:FAIL | — | **FAILED** |
| AA-3-41 | REQ-PERF-002 | AR/AW handshake must occur within 6 i_clk_core cycles of accepted AHB address. | CHK-034:FAIL | — | **FAILED** |
| AA-3-42 | REQ-PERF-002 | The AW timing target starts after the full burst or its early termination has been captured. | CHK-034:FAIL | — | **FAILED** |
| AA-3-44 | REQ-RTL-001 | RTL must follow REF-003; the single top module contains only structural instances and each module is in a same-named file. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-3-45 | REQ-REG-001 | The IP must have no software-visible CSR interface; all configuration is static at elaboration. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-4-02 |  | A parameter value outside its legal range must be treated as an elaboration error. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-5.1-01 |  | All sequential logic and FIFO clock/reset pins use the shared i_clk_core and i_rst_n_core. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-5.1-02 |  | The combinational AXI adapter uses i_rst_n_core only to suppress AXI VALID/READY during reset. | CHK-019:PASS | — | **VERIFIED** |
| AA-5.1-04 |  | The five FIFO instances have depths 2, 16, 2, 2 and 2 entries respectively, with software-reset inactive and both clock/reset pins tied to shared inputs. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-5.3-01 |  | The bridge issues ARLEN=0 and ARBURST=INCR, accepts one R beat with RLAST=1, and returns HRDATA and HRESP in the AHB data phase. | CHK-037:FAIL | — | **FAILED** |
| AA-5.3-02 |  | The bridge must not accept the next AHB read while the current read is unresolved. | CHK-015:FAIL | — | **FAILED** |
| AA-5.3-03 |  | Issue one AXI write with AWLEN=0, one W beat with WLAST=1, wait for the B response, then return AHB completion/error. | CHK-040:FAIL | — | **FAILED** |
| AA-5.3-04 |  | Fixed non-bufferable bursts are serialized beat by beat. | CHK-023:FAIL | — | **FAILED** |
| AA-5.3-05 |  | Collect all 4/8/16 AHB address/data beats in order. | CHK-024:FAIL | — | **FAILED** |
| AA-5.3-06 |  | If all AXI address attributes are constant, emit one matching INCR/WRAP AXI burst; otherwise emit ordered AXI single-beat writes. | CHK-024:FAIL, CHK-025:FAIL | — | **FAILED** |
| AA-5.3-07 |  | Keep Device-E and non-bufferable writes as single AXI writes. | CHK-023:FAIL | — | **FAILED** |
| AA-5.3-08 |  | Earlier safely buffered Normal Write-back beats may complete OKAY. | CHK-024:FAIL | — | **FAILED** |
| AA-5.4-02 |  | No AXI read address is issued before the corresponding AHB read address is accepted. | CHK-013:PASS | — | **VERIFIED** |
| AA-5.4-03 |  | AHB and AXI transaction order is preserved, with no read speculation or response reordering. | CHK-033:FAIL | — | **FAILED** |
| AA-5.4-04 |  | AXI VALID and payload remain stable until the READY handshake. | CHK-005:FAIL, CHK-006:PASS, CHK-007:PASS | — | **FAILED** |
| AA-5.4-05 |  | An AXI burst is issued only when the complete AHB fixed write burst has been captured. | CHK-014:NOT_HIT, CHK-026:FAIL | — | **FAILED** |
| AA-5.4-06 |  | At most one read and one write transaction are outstanding; a later AHB transaction must not pass a stalled response. | CHK-008:PASS, CHK-033:FAIL | — | **FAILED** |
| AA-5.4-07 |  | WLAST is high exactly on the final AXI W beat; read ARLEN is always zero and expected RLAST is one. | CHK-004:PASS, CHK-010:PASS | — | **VERIFIED** |
| AA-6.1-01 |  | The bridge must provide IF-001, a required AHB5 (IHI 0033 Version C) Subordinate interface, clocked by i_clk_core and reset by i_rst_n_core, in configuration CFG-BASE. | CHK-002:FAIL, CHK-036:FAIL | — | **FAILED** |
| AA-6.1-02 |  | The bridge must provide IF-002, a required AXI4 (IHI 0022 Issue H.c) Manager interface, clocked by i_clk_core and reset by i_rst_n_core, in configuration CFG-BASE. | CHK-036:FAIL | — | **FAILED** |
| AA-6.1-03 |  | The bridge must provide IF-003, a single required active-low shared reset from the reset controller, with asynchronous assert and SoC-synchronized release before the IP boundary. | CHK-038:FAIL | — | **FAILED** |
| AA-6.2-01 |  | AHB and AXI interface signals must use the rising edge of i_clk_core, and i_rst_n_core must be the only reset input. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-T1.7.2.1-01 |  | AHB HCLK and AXI ACLK must both map to the single clock i_clk_core. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-T1.7.2.2-01 |  | The IP must not implement any AHB or AXI USER sideband ports. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-T1.7.2.2-02 |  | i_rst_n_core asserts asynchronously and is deasserted synchronously by the SoC before the IP boundary; it is 1 after release. | CHK-038:FAIL | — | **FAILED** |
| AA-T1.7.2.2-03 |  | i_ahb_hsel is 0, i_ahb_htrans is IDLE, i_ahb_hwrite is 0, i_ahb_hburst is SINGLE and i_ahb_hmastlock is 0 at reset/idle. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AA-T1.7.2.2-04 |  | The bridge ignores i_ahb_hready, i_axi_awready, i_axi_wready and i_axi_arready during bridge reset; they are externally unconstrained. | CHK-038:FAIL | — | **FAILED** |
| AA-T1.7.2.2-05 |  | o_ahb_hreadyout is 1 during reset. | CHK-018:PASS | — | **VERIFIED** |
| AA-T1.7.2.2-06 |  | o_ahb_hresp is 0 (OKAY) at reset. | CHK-018:PASS | — | **VERIFIED** |
| AA-T1.7.2.2-07 |  | An o_ahb_hresp ERROR follows the AHB two-cycle error response. | CHK-001:PASS | — | **VERIFIED** |
| AA-T1.7.2.2-08 |  | o_ahb_hrdata is 0 at reset. | CHK-018:PASS | — | **VERIFIED** |
| AA-T1.7.2.2-09 |  | o_axi_awid, o_axi_awaddr, o_axi_awlen, o_axi_awsize, o_axi_awcache and o_axi_awprot are 0 at reset. | CHK-020:FAIL | — | **FAILED** |
| AA-T1.7.2.2-11 |  | o_axi_awlock and o_axi_arlock are constant 0 (tied low). | CHK-003:PASS | — | **VERIFIED** |
| AA-T1.7.2.2-12 |  | o_axi_awvalid is held high until i_axi_awready. | CHK-005:FAIL | — | **FAILED** |
| AA-T1.7.2.2-13 |  | o_axi_awvalid, o_axi_wvalid, o_axi_bready, o_axi_arvalid and o_axi_rready are 0 at reset. | CHK-019:PASS | — | **VERIFIED** |
| AA-T1.7.2.2-14 |  | o_axi_wdata, o_axi_wstrb and o_axi_wvalid are held until i_axi_wready. | CHK-006:PASS | — | **VERIFIED** |
| AA-T1.7.2.2-15 |  | o_axi_wdata, o_axi_wstrb and o_axi_wlast are 0 at reset. | CHK-020:FAIL | — | **FAILED** |
| AA-T1.7.2.2-16 |  | o_axi_wlast is high only on the final beat of a write burst. | CHK-010:PASS | — | **VERIFIED** |
| AA-T1.7.2.2-17 |  | i_axi_bvalid is 0 during reset. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AA-T1.7.2.2-18 |  | i_axi_bvalid is held until o_axi_bready. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AA-T1.7.2.2-19 |  | o_axi_arid, o_axi_araddr, o_axi_arsize, o_axi_arcache and o_axi_arprot are 0 at reset. | CHK-020:FAIL | — | **FAILED** |
| AA-T1.7.2.2-20 |  | o_axi_arlen is always zero, so every read is a single beat. | CHK-004:PASS | — | **VERIFIED** |
| AA-T1.7.2.2-21 |  | o_axi_arburst is INCR, including at reset. | CHK-004:PASS, CHK-020:FAIL | — | **FAILED** |
| AA-T1.7.2.2-22 |  | o_axi_arvalid is held high until i_axi_arready. | CHK-007:PASS | — | **VERIFIED** |
| AA-T1.7.2.2-23 |  | i_axi_rlast is expected high for each single-beat read. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AA-T1.7.2.2-24 |  | i_axi_rvalid is 0 during reset. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AA-T1.7.2.2-25 |  | i_axi_rvalid is held until o_axi_rready. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AA-T1.7.3.1-01 |  | The bridge accepts a transfer at a rising i_clk_core edge when HSEL, HREADY and HTRANS[1] are all 1. | CHK-021:FAIL, CHK-037:FAIL | — | **FAILED** |
| AA-T1.7.3.1-02 |  | Address/control are taken from the address phase; HWDATA/HWSTRB belong to the corresponding data phase. | CHK-040:FAIL | — | **FAILED** |
| AA-T1.7.3.1-03 |  | BUSY and IDLE transfers must not create AXI traffic. | CHK-002:FAIL, CHK-021:FAIL | — | **FAILED** |
| AA-T1.7.3.1-04 |  | Supported HSIZE encodings are byte, halfword and word (0,1,2), and transfer addresses shall be naturally aligned to HSIZE. | CHK-012:FAIL | — | **FAILED** |
| AA-T1.7.3.1-05 | REQ-FUNC-009 | The bridge returns AHB ERROR with no AXI request for the rejected transfer; any earlier accepted write prefix is drained. | CHK-030:PASS, CHK-031:FAIL | — | **FAILED** |
| AA-T1.7.3.1-06 |  | AHB SINGLE and undefined INCR are converted to AXI single-beat INCR transactions. | CHK-037:FAIL, CHK-040:FAIL | — | **FAILED** |
| AA-T1.7.3.1-07 |  | Each read beat of fixed INCR/WRAP bursts issues its own single-beat AR request. | CHK-037:FAIL | — | **FAILED** |
| AA-T1.7.3.1-08 |  | AXI write burst aggregation is limited to complete legal Normal Write-back fixed write bursts with constant AXI address attributes. | CHK-014:NOT_HIT, CHK-023:FAIL, CHK-024:FAIL, CHK-025:FAIL | — | **FAILED** |
| AA-T1.7.3.1-09 |  | Device writes must never be merged into an AXI burst. | CHK-023:FAIL | — | **FAILED** |
| AA-T1.7.3.1-10 |  | Captured but unissued write beats are drained as ordered AXI singles without reissuing sent beats; no short AXI burst replaces the AHB burst. | CHK-026:FAIL | — | **FAILED** |
| AA-T1.7.3.1-11 |  | AHB managers must not start an incrementing burst that crosses a 1 KiB boundary. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AA-T1.7.3.1-12 |  | The bridge keeps every AXI burst within a 4 KiB boundary, splitting defensively for out-of-profile address sequences. | CHK-011:PASS, CHK-027:FAIL | — | **FAILED** |
| AA-T1.7.3.1-13 |  | HPROT remains constant throughout an AHB burst. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AA-T1.7.3.1-14 |  | The bridge uses ordered AXI singles instead of a burst. | CHK-025:FAIL | — | **FAILED** |
| AA-T1.7.3.1-15 |  | The bridge issues no exclusive requests; HMASTLOCK=1 is rejected with AHB ERROR. | CHK-003:PASS, CHK-030:PASS | — | **VERIFIED** |
| AA-T1.7.3.2-01 |  | AXI4 VALID and payload remain stable until READY handshakes; AXI outputs have no combinational dependency on READY. | CHK-005:FAIL, CHK-006:PASS, CHK-007:PASS, CHK-022:FAIL | — | **FAILED** |
| AA-T1.7.3.2-02 |  | At most one read and one write transaction may be outstanding. | CHK-008:PASS | — | **VERIFIED** |
| AA-T1.7.3.2-03 |  | Reads are single-beat: ARLEN=0, ARBURST=INCR, RLAST=1. | CHK-004:PASS, CHK-037:FAIL | — | **FAILED** |
| AA-T1.7.3.2-04 |  | Writes are single-beat or fixed bursts up to 16 beats. | CHK-011:PASS | — | **VERIFIED** |
| AA-T1.7.3.2-05 |  | AXI ID is 3 bits; each direction rotates through IDs 0..count-1 after each completed transaction. | CHK-032:FAIL | — | **FAILED** |
| AA-T1.7.3.2-06 |  | ID count greater than 1 does not enable concurrent transactions. | CHK-008:PASS | — | **VERIFIED** |
| AA-T1.7.3.3-01 |  | The transfer is rejected with AHB ERROR before any AXI request is issued. | CHK-017:FAIL, CHK-030:PASS | — | **FAILED** |
| AA-T1.7.3.3-02 |  | AxPROT[0]=HPROT[1], AxPROT[1]=HNONSEC, AxPROT[2]=~HPROT[0]. | CHK-037:FAIL, CHK-040:FAIL | — | **FAILED** |
| AA-T1.7.3.3-03 |  | AxCACHE[1]=HPROT[3], AxCACHE[0]=HPROT[2]; HPROT[4]=0 gives AxCACHE[3:2]=00; HPROT[4]=1 sets direction-specific allocate bits per HPROT[5]. | CHK-037:FAIL, CHK-040:FAIL | — | **FAILED** |
| AA-T1.7.3.3-04 | REQ-FUNC-005 | Issue one AXI single per beat, never merge, and wait for final-destination BRESP. | CHK-023:FAIL | — | **FAILED** |
| AA-T1.7.3.3-06 |  | The bridge may aggregate such bursts into an AXI burst. | CHK-024:FAIL | — | **FAILED** |
| AA-T1.7.3.4-01 | REQ-FUNC-003 | One accepted address returns one AXI R beat; no speculative or multi-beat read; AHB waits for R and maps RRESP. | CHK-015:FAIL, CHK-037:FAIL | — | **FAILED** |
| AA-T1.7.3.4-02 | REQ-FUNC-004 | One AHB beat maps to one AXI single with no undefined-length aggregation; wait for BRESP. | CHK-016:FAIL, CHK-040:FAIL | — | **FAILED** |
| AA-T1.7.3.4-03 | REQ-FUNC-005 | A full 4/8/16-beat burst uses one AXI burst only with uniform attributes; prior beats get early OKAY and terminal HRESP reflects final B status. | CHK-024:FAIL | — | **FAILED** |
| AA-T1.7.3.4-04 | REQ-ERR-002 | No AXI request for the rejected transfer; two-cycle AHB ERROR; drain any previously accepted write prefix. | CHK-030:PASS, CHK-031:FAIL | — | **FAILED** |
| AA-T1.7.3.4-05 | REQ-ERR-001 | Non-OKAY maps to AHB ERROR. | CHK-028:FAIL, CHK-029:FAIL | — | **FAILED** |
| AA-6.4-01 |  | The bridge IP includes no interrupt or event output port. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-6.4-02 |  | Supported errors are returned to the AHB master on the AHB response channel (HRESP) rather than via an interrupt or event output. | CHK-028:FAIL, CHK-029:FAIL | — | **FAILED** |
| AA-7.1-01 |  | AHB HCLK and AXI ACLK, and all FIFO instances, must use the same physical i_clk_core input, rising-edge, with no internal clock gating. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-7.2-01 |  | The bridge must operate in the single CLK-CORE domain and must not contain asynchronous crossings, synchronizer chains, Gray pointers or CDC FIFOs. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-7.2-02 |  | Each m_vlsit_sfifo_top write/read clock input must be tied to i_clk_core and its two reset inputs tied to i_rst_n_core. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-7.3-01 |  | Reset values must be HREADYOUT=1, HRESP=OKAY, AWVALID/WVALID/ARVALID=0, BREADY/RREADY=0, and FIFO valid state cleared, for all bridge logic and five FIFOs. | CHK-018:PASS, CHK-019:PASS, CHK-038:FAIL, CHK-039:FAIL | — | **FAILED** |
| AA-7.3-02 |  | The SoC must provide one active-low reset net i_rst_n_core to both protocol sides and all FIFOs, asserted asynchronously and with deassertion synchronized to i_clk_core before the IP. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AA-7.3-03 |  | The RTL must use i_rst_n_core directly and must not contain a reset synchronizer. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-7.3-04 |  | No transaction may be accepted by the bridge until reset is released. | CHK-038:FAIL | — | **FAILED** |
| AA-8-01 |  | PARA_RD_ID_COUNT, the number of read IDs in rotation, must default to 1 and be within the legal range 1..8. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-8-02 |  | The read ID width must remain 3 regardless of PARA_RD_ID_COUNT, and the count must not increase outstanding capacity. | CHK-032:FAIL | — | **FAILED** |
| AA-8-03 |  | PARA_WR_ID_COUNT, the number of write IDs in rotation, must default to 1 and be within the legal range 1..8. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-8-04 |  | The write ID width must remain 3 regardless of PARA_WR_ID_COUNT, and the count must not increase outstanding capacity. | CHK-032:FAIL | — | **FAILED** |
| AA-8-06 |  | AXI address, data and ID widths, FIFO depths and protocol features must not be user-overridable in this revision. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-8-07 |  | Immediately above each RTL parameter, comments // Parameter Description, // Parameter values and // Parameter unit must appear in that order. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-9-01 |  | The AXI address must equal the corresponding accepted AHB address (32-bit byte address). | CHK-037:FAIL, CHK-040:FAIL | — | **FAILED** |
| AA-9-03 |  | The bridge must not byte-swap data between AHB and AXI. | CHK-015:FAIL, CHK-040:FAIL | — | **FAILED** |
| AA-9-04 |  | HSIZE/AxSIZE must encode 0 as 1 byte, 1 as 2 bytes and 2 as 4 bytes. | CHK-012:FAIL, CHK-037:FAIL | — | **FAILED** |
| AA-9-05 |  | The bridge must reject transfers with sizes larger than 4 bytes. | CHK-030:PASS | — | **VERIFIED** |
| AA-9-06 |  | HWSTRB[n] and WSTRB[n] must qualify byte [8n+7:8n] of HWDATA/WDATA respectively. | CHK-040:FAIL | — | **FAILED** |
| AA-9-07 |  | The strobe must be passed from HWSTRB to WSTRB per beat. | CHK-040:FAIL | — | **FAILED** |
| AA-9-09 |  | AXI LEN must equal the beat count minus one. | CHK-010:PASS, CHK-011:PASS | — | **VERIFIED** |
| AA-9-11 |  | AWLEN must be 3, 7 or 15 for an aggregated write burst before boundary split. | CHK-024:FAIL | — | **FAILED** |
| AA-9-13 |  | Each direction (read and write) must rotate its ID independently through the configured count. | CHK-032:FAIL | — | **FAILED** |
| AA-10.1-01 |  | An eligible fixed Normal Write-back write may remain in capture until all expected beats are received. | CHK-024:FAIL, CHK-026:FAIL | — | **FAILED** |
| AA-10.1-03 |  | The bridge must return a two-cycle AHB ERROR response and issue no AXI request for the rejected transfer. | CHK-030:PASS | — | **VERIFIED** |
| AA-10.2-01 |  | The bridge must issue one AR with ARLEN=0, receive one R beat, and complete AHB with HRDATA and HRESP derived from RRESP. | CHK-037:FAIL | — | **FAILED** |
| AA-10.2-02 |  | The bridge must issue one AW with AWLEN=0 and one W beat with WLAST=1, wait for BRESP, and map the response to that AHB transfer. | CHK-016:FAIL, CHK-023:FAIL, CHK-040:FAIL | — | **FAILED** |
| AA-10.2-03 |  | The bridge must issue one AW/W burst of up to 16 beats, splitting at 4 KiB if needed; the terminal AHB beat waits for all corresponding BRESPs. | CHK-024:FAIL, CHK-027:FAIL | — | **FAILED** |
| AA-10.2-04 |  | Earlier accepted beats of an AXI write burst may return OKAY before the BRESPs arrive. | CHK-024:FAIL | — | **FAILED** |
| AA-10.2-05 |  | The bridge must issue ordered AXI singles for remaining captured beats, not reissue completed beats, and aggregate relevant B errors to the terminal AHB beat. | CHK-025:FAIL, CHK-026:FAIL | — | **FAILED** |
| AA-10.2-06 |  | On assertion of i_rst_n_core the bridge must drop in-flight queues and VALID state and drive HREADYOUT=1 during reset. | CHK-018:PASS, CHK-019:PASS, CHK-039:FAIL | — | **FAILED** |
| AA-10.4-01 |  | The bridge must serialize reads and must not accept the next AHB read until the current R data/status returns. | CHK-015:FAIL | — | **FAILED** |
| AA-10.4-02 |  | The bridge can accept one AHB beat per i_clk_core cycle. | CHK-024:FAIL | — | **FAILED** |
| AA-10.4-03 |  | The bridge must wait for each single-beat BRESP and must not acknowledge Device-E before the final destination responds. | CHK-016:FAIL, CHK-023:FAIL | — | **FAILED** |
| AA-10.4-04 |  | The AR/AW handshake should complete within 6 i_clk_core cycles of the accepted AHB address. | CHK-034:FAIL | — | **FAILED** |
| AA-10.4-05 |  | The AW latency bound starts after the complete AHB burst or its early termination is captured, not from the first AHB address; no AXI burst is issued before capture. | CHK-026:FAIL, CHK-034:FAIL | — | **FAILED** |
| AA-10.4-07 |  | Read/write arbitration must follow AHB acceptance order, and no later transaction may bypass an unresolved AHB operation. | CHK-033:FAIL | — | **FAILED** |
| AA-10.5-03 |  | FIFO pointer and validity state must be cleared by the shared reset; payload contents need not be reset. | CHK-039:FAIL | — | **FAILED** |
| AA-12-01 |  | The bridge must reject a transfer with HMASTLOCK=1 using a two-cycle ERROR response and issue no AXI request for it. | CHK-017:FAIL, CHK-030:PASS | — | **FAILED** |
| AA-12-02 |  | The bridge must drain any accepted write prefix before giving the terminal ERROR response for a transfer rejected for HMASTLOCK=1. | CHK-031:FAIL | — | **FAILED** |
| AA-12-03 |  | The bridge must reject a transfer with HPROT[6]=1 or unsupported/reserved HPROT using a two-cycle ERROR response, with no AXI request or side effect for the rejected beat. | CHK-017:FAIL, CHK-030:PASS | — | **FAILED** |
| AA-12-04 |  | The bridge must drain any accepted write prefix when rejecting a beat for HPROT error. | CHK-031:FAIL | — | **FAILED** |
| AA-12-05 |  | The bridge must reject a transfer with HSIZE>2, misalignment or reserved HBURST using a two-cycle ERROR response, with no AXI request or side effect for the rejected beat. | CHK-017:FAIL, CHK-030:PASS | — | **FAILED** |
| AA-12-06 |  | The bridge must drain any accepted write prefix when rejecting a beat for HSIZE, misalignment or reserved HBURST. | CHK-031:FAIL | — | **FAILED** |
| AA-12-07 |  | The bridge must consume the R beat and return a two-cycle AHB ERROR response for the read, reporting the mapped error. | CHK-029:FAIL | — | **FAILED** |
| AA-12-08 |  | The bridge must return a two-cycle ERROR for a single write, or on the terminal AHB beat of a Normal Write-back burst, when BRESP is SLVERR/DECERR/EXOKAY. | CHK-028:FAIL | — | **FAILED** |
| AA-12-09 |  | Earlier buffered beats must remain acknowledged, and the terminal status must reflect all B responses. | CHK-028:FAIL | — | **FAILED** |
| AA-12-10 |  | The bridge must hold VALID and payload stable until the AXI handshake completes. | CHK-005:FAIL, CHK-006:PASS, CHK-007:PASS, CHK-035:FAIL | — | **FAILED** |
| AA-12-11 |  | The bridge must not implement an internal timeout; AHB waits indefinitely and recovery is left to a system-level watchdog/reset. | CHK-035:FAIL | — | **FAILED** |
| AA-12-13 |  | The terminal AHB response must wait for all relevant B responses, aggregate errors, and not reissue completed beats. | CHK-026:FAIL | — | **FAILED** |
| AA-12-14 |  | In-flight state is discarded and the bridge and connected endpoint/interconnect are reset consistently. | CHK-039:FAIL | — | **FAILED** |
| AA-12-16 |  | In the first ERROR cycle HREADYOUT must be low and in the second ERROR cycle HREADYOUT must be high. | CHK-001:PASS | — | **VERIFIED** |
| AA-12-17 |  | AXI errors must not be returned as AHB split responses. | CHK-028:FAIL, CHK-029:FAIL | — | **FAILED** |
| AA-13-01 |  | A single request should be issued within at most 6 i_clk_core cycles; this is a cycle-based design target requiring implementation verification. | CHK-034:FAIL | — | **FAILED** |
| AA-14.1-01 |  | RTL shall be synthesizable SystemVerilog following VLSIT RTL Design Rules v2 using logic declarations, with no package, plain always, always_latch, define/undef, or signed types. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-14.1-04 |  | Parameters use uppercase PARA_ names, localparams use uppercase LPARA_ names, and enum type names end in _type_def. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-14.2-01 |  | m_ahb2axi_top is the single structural top with fixed AHB/AXI ports and instantiates only u_ahb2axi_ctrl. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-14.2-02 |  | m_ahb2axi_ctrl instantiates one m_ahb2axi_ahb_if (u_ahb2axi_ahb_if) and one m_ahb2axi_axi_if (u_ahb2axi_axi_if) plus its control RTL. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-14.2-03 |  | m_ahb2axi_ctrl instantiates five m_vlsit_sfifo_top FIFOs named u_vlsit_sfifo_top_0 through _4, with indexes starting at zero. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-14.2-04 |  | Both clock pins of each FIFO instance tie to i_clk_core and both hardware-reset pins tie to i_rst_n_core. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-14.2-05 |  | Each module is stored in a file with the same basename as the module. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-14.3-03 |  | The FIFO storage implementation must meet the FIFO contract. | not verified: covered_by_other_check | — | **NOT_VERIFIED_BY_SIM** |
| AA-14.3-04 |  | The design must have no latches, inferred tri-states, or technology cells outside dedicated wrappers. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-15.1-01 |  | AHB master and AXI Subordinate BFMs shall be independent of each other. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AA-15.1-02 |  | Expected transactions shall be computed from accepted AHB pin activity and stated mappings, not from RTL hierarchy, internal state or generated names. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AA-15.1-03 |  | All test sources and run commands shall be retained in the verification deliverable. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AA-15.1-04 |  | The verification flow owner shall place all run commands in one Makefile. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AA-15.2-01 | REQ-PERF-002 | AXI VALID and payload shall remain stable during READY stalls; no completion bound is asserted and the bridge has no internal timeout. | CHK-005:FAIL, CHK-035:FAIL | — | **FAILED** |
| AA-15.2-02 |  | Protocol checks shall report no violation on legal traffic and shall report injected endpoint violations. | CHK-036:FAIL | — | **FAILED** |
| AA-15.3-01 |  | AXI VALID and payload must remain stable while READY=0. | CHK-005:FAIL, CHK-006:PASS, CHK-007:PASS | — | **FAILED** |
| AA-15.3-02 |  | No AXI read may be issued before AHB acceptance. | CHK-013:PASS | — | **VERIFIED** |
| AA-15.3-03 |  | ARLEN must be 0 for single-beat reads. | CHK-004:PASS | — | **VERIFIED** |
| AA-15.3-04 |  | WLAST must be asserted at exactly the final W beat. | CHK-010:PASS | — | **VERIFIED** |
| AA-15.3-05 |  | No AW may be issued before the complete aggregated AHB burst is captured. | CHK-014:NOT_HIT | — | **NOT_PROVEN** |
| AA-15.3-06 |  | AHB responses must be returned in order. | CHK-033:FAIL | — | **FAILED** |
| AA-15.3-07 |  | AHB ERROR response must last two cycles. | CHK-001:PASS | — | **VERIFIED** |
| AA-15.3-08 |  | Reset must clear AXI VALID. | CHK-019:PASS | — | **VERIFIED** |
| AA-15.3-09 |  | ID values must remain below the configured ID count. | CHK-009:PASS | — | **VERIFIED** |
| AA-15.3-10 |  | Functional coverage shall cross direction, size, burst type, HPROT memory type, bufferable/non-bufferable, strobe mask, response status, READY stall length, uniform/varying address attributes, early termination, ID count and reset timing. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| AA-15.4-01 |  | Formal checks shall prove ordering, no duplication/loss, no speculative read, no AXI boundary crossing and response mapping. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-15.4-02 |  | Static timing analysis shall treat all bridge and FIFO paths as single-clock synchronous paths under i_clk_core, with no CDC paths or asynchronous clock groups. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-15.4-03 |  | Reset analysis shall verify the one-reset contract, asynchronous assertion, SoC-synchronized deassertion before the IP boundary, and clearing of FIFO valid state. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-17.1.1-01 |  | The SoC integrator shall supply the i_clk_core clock frequency/period and uncertainty before static timing analysis. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AA-17.1.3-02 |  | Asynchronous clock groups or false paths must not be declared between bridge logic and FIFO pointers. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-17.1.3-03 |  | Only justified reset, generated-clock or memory-macro constraints supplied by the selected library and SoC flow shall be applied; no numeric exception is invented. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-17.2-01 |  | The synchronous FIFO storage must be mapped to standard cells or a compatible single-clock memory macro. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-18-01 |  | The bridge must preserve HNONSEC and translate supported HPROT fields per §6.3. | CHK-037:FAIL, CHK-040:FAIL | — | **FAILED** |
| AA-18-02 |  | The bridge must reject Shareable transfers and unsupported HPROT combinations. | CHK-030:PASS | — | **VERIFIED** |
| AA-18-03 |  | The bridge must not implement address-based access control. | CHK-037:FAIL, CHK-040:FAIL | — | **FAILED** |
| AA-18-04 |  | The bridge must reject transfers with HMASTLOCK; exclusive/atomic access is not implemented. | CHK-030:PASS | — | **VERIFIED** |
| AA-18-05 |  | The AXI lock outputs must be tied low. | CHK-003:PASS | — | **VERIFIED** |
| AA-18-08 |  | AXI response errors must be returned on AHB. | CHK-028:FAIL, CHK-029:FAIL | — | **FAILED** |
| AA-18-09 |  | The bridge must not add any timeout or retry. | CHK-035:FAIL | — | **FAILED** |
| AA-20.2-01 |  | The bridge must return AHB ERROR for unsupported size, misaligned address or reserved transfer encodings without issuing any AXI transaction. | CHK-017:FAIL, CHK-030:PASS | — | **FAILED** |
| AA-20.2-03 |  | The AHB transfer remains pending when the AXI response never arrives, with no out-of-band error notification. | CHK-035:FAIL | — | **FAILED** |
| AA-20.3-01 |  | AHB, AXI and all FIFO instances must use one shared rising-edge clock input i_clk_core. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AA-20.3-02 |  | The bridge must reject transfers with HPROT[6] equal to 1. | CHK-017:FAIL, CHK-030:PASS | — | **FAILED** |
| AA-20.3-03 |  | Errors of eligible Normal Write-back bufferable fixed writes must be reported at the terminal AHB beat. | CHK-028:FAIL | — | **FAILED** |
| AA-20.3-04 |  | Device-E and non-bufferable writes must wait for BRESP on each beat. | CHK-016:FAIL, CHK-023:FAIL | — | **FAILED** |
| AA-20.3-05 |  | The bridge must issue a request within 6 i_clk_core cycles when queue space exists and READY is high. | CHK-034:FAIL | — | **FAILED** |
| AA-20.3-06 |  | A non-OKAY AXI response, including unexpected EXOKAY, must map to a two-cycle AHB ERROR response. | CHK-028:FAIL, CHK-029:FAIL | — | **FAILED** |
| AA-21-01 |  | The bridge must not merge Device-E (bufferable Device memory) writes. | CHK-023:FAIL | — | **FAILED** |
| AA-21-02 |  | The bridge must wait for the final-destination BRESP before completing a Device-E write. | CHK-016:FAIL, CHK-023:FAIL | — | **FAILED** |
| AA-21-03 |  | The bridge must not issue an AXI read before its AHB address has been accepted (no speculation). | CHK-013:PASS | — | **VERIFIED** |

## Not verified by this run

- Formal: the assertions were checked by SymbiYosys under the environment assumptions (work/formal.md); a BOUNDED result holds only up to its depth.
- Domain crossings were checked structurally (synchronizer structure, `nnc cdc`); gray coding and handshake protocols are not proven by that check.
- Sign-off STA, place and route and DFT are outside this flow (docs/SIGNOFF_SCOPE.md); `nnc rtl-check` gives a synthesis estimate of area and the longest combinational path.
- Rules marked NOT_VERIFIED_BY_SIM carry the contract's reason (static, structural, not observable...).
- Only the configurations of the run set above were simulated; code coverage is merged over its runs, mutation testing used the primary run base.s1.

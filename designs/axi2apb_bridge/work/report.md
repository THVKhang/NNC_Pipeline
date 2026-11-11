# Verification report — axi2apb_bridge

Generated 2026-11-11T12:49:11+00:00 by NNC Pipeline.

## Summary

| Item | Result |
|---|---|
| Rules | 151 — {'NOT_VERIFIED_BY_SIM': 37, 'VERIFIED': 114} |
| Checks | 31 — {'PASS': 31} |
| Tests | {'pass': 15} |
| Integration | OK |
| Code coverage (RTL), line | 98.9 % (738/746 lines) |
| Code coverage (RTL), block | 95.9 % (209/218 statement blocks and branch arms) |
| Code coverage (RTL), expression | 96.2 % (102/106 condition terms) |
| Code coverage (RTL), toggle | 74.8 % (3506/4690 bit toggles 0->1 and 1->0) |
| Code coverage (RTL), functional | 97.5 % (39/40 cover points of the specification) |
| Mutation score | 88.9 % (32 killed / 4 survived / 0 not compiled) |
| Coverage target | not requested (`nnc cover <design> --target <n> --metric <m>`) |
| Triage | no failure to analyse |
| Agent cost | US$12.406 in 61 calls (A1 0.6369, A12 2.1642, A2 0.5175, A3 0.2907, A4 1.1562, A5 0.4376, A6 0.3396, A7 4.7164, A9 2.1467) |

## Sign-off conditions

| Condition | State |
|---|---|
| Gates G1-G3 approved | met — approved on delegation by an agent: a person should confirm |
| Interface conformance of the DUT | met |
| Every selected check PASS (no FAIL, NOT_HIT, NOT_RUN) | met |
| Every planned check selected | met |
| Every rule in a check or declared not verifiable | met |
| Mutation run | met |
| Per-requirement mutation score >= 85 % | met — 69 rules with attributed mutants |

## Gates

| Gate | State | Detail |
|---|---|---|
| G1_rules | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-08T15:29:08+00:00 |
| G2_contract | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-08T15:29:35+00:00 |
| G3_verif_sources | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-10T03:29:09+00:00 |
| G4_signoff | PENDING | artifacts ready for review |

## Checks

| Check | Kind | Title | Status | Evidence |
|---|---|---|---|---|
| CHK-001 | assertion | APB SETUP/ACCESS phase sequencing | **PASS** | hits 199228, fails 0 |
| CHK-002 | assertion | APB wait-state hold of control and payload | **PASS** | hits 67608, fails 0 |
| CHK-003 | assertion | APB payload stable from SETUP into ACCESS | **PASS** | hits 43874, fails 0 |
| CHK-004 | assertion | PADDR word aligned | **PASS** | hits 319738, fails 0 |
| CHK-005 | assertion | PSTRB zero on APB reads | **PASS** | hits 80013, fails 0 |
| CHK-006 | assertion | APB outputs zero when idle | **PASS** | hits 164383, fails 0 |
| CHK-007 | assertion | B channel hold under BREADY backpressure | **PASS** | hits 1581, fails 0 |
| CHK-008 | assertion | Single B after all W beats and APB writes, with correct BID/BRESP | **PASS** | hits 3007, fails 0 |
| CHK-009 | assertion | R channel hold under RREADY backpressure | **PASS** | hits 21885, fails 0 |
| CHK-010 | assertion | RID echo, RLAST position and R beat count | **PASS** | hits 44851, fails 0 |
| CHK-011 | assertion | Legal read beat data and response from the APB completion | **PASS** | hits 44293, fails 0 |
| CHK-012 | assertion | Unsupported read beats are SLVERR with zero data | **PASS** | hits 558, fails 0 |
| CHK-013 | assertion | WREADY gated by AW acceptance; W beats never exceed AWLEN+1 | **PASS** | hits 22033, fails 0 |
| CHK-014 | assertion | Transaction tracker: one global owner, actions only after the handshake | **PASS** | hits 206035, fails 0 |
| CHK-015 | assertion | No APB activity for unsupported requests | **PASS** | hits 1466, fails 0 |
| CHK-016 | assertion | APB transfer sequence matches AXI beats (direction, address, PPROT, data, strobes, count) | **PASS** | hits 108998, fails 0 |
| CHK-017 | assertion | Synchronous reset values of all outputs | **PASS** | hits 83, fails 0 |
| CHK-018 | test | Long APB wait: access held indefinitely, no timeout | **PASS** | test_chk_018_long_apb_wait |
| CHK-019 | test | AR/AW round-robin: AR wins the first tie, then the side not served last wins | **PASS** | test_chk_019_arbitration_round_robin |
| CHK-020 | test | WVALID before AW: WREADY held low until AW accepted | **PASS** | test_chk_020_wvalid_before_aw |
| CHK-021 | test | RREADY/BREADY backpressure stalls the owning transaction without loss | **PASS** | test_chk_021_response_backpressure |
| CHK-022 | test | Unsupported reads: no APB, ARLEN+1 SLVERR beats with zero data | **PASS** | test_chk_022_unsupported_reads |
| CHK-023 | test | Unsupported writes: drain AWLEN+1 W beats, no APB, one SLVERR B | **PASS** | test_chk_023_unsupported_writes |
| CHK-024 | test | Read PSLVERR maps to SLVERR on that beat only | **PASS** | test_chk_024_read_pslverr |
| CHK-025 | test | Write PSLVERR accumulates into the final BRESP; later beats still run | **PASS** | test_chk_025_write_pslverr |
| CHK-026 | test | Unmapped address answered by default completer gives AXI SLVERR | **PASS** | test_chk_026_unmapped_default_completer |
| CHK-027 | test | Random legal FIXED/INCR/WRAP read/write bursts against an independent model | **PASS** | test_chk_027_random_legal_bursts, test_regression_random |
| CHK-028 | test | Sub-word and unaligned transfers: PADDR align-down, PSTRB copy, no lane rotation | **PASS** | test_chk_028_subword_unaligned |
| CHK-029 | test | AxPROT passes to PPROT for all values; no local PPROT access control | **PASS** | test_chk_029_pprot_passthrough |
| CHK-030 | test | ID echo over the full PARA_AXI_ID_W range | **PASS** | test_chk_030_id_echo |
| CHK-031 | test | Reset mid-transaction cancels work, deselects APB, no replay | **PASS** | test_chk_031_reset_mid_transaction |

## Requirement traceability (RTM)

| Rule | Spec ref | Statement | Checks | Mutation | Status |
|---|---|---|---|---|---|
| AB-1.1-01 |  | The bridge converts transactions from one AXI4 Manager into ordered APB4 transfers through one APB port. | CHK-016:PASS, CHK-027:PASS | — | **VERIFIED** |
| AB-1.1-02 |  | The bridge uses one shared clock and has only one global transaction active at a time. | CHK-014:PASS | — | **VERIFIED** |
| AB-1.1-03 |  | The bridge supports AXI4 read/write channels, FIXED/INCR/WRAP bursts, 32-bit addresses/data, 1/2/4-byte transfers, IDs, PSTRB, PPROT, error propagation and defensive request rejection. | CHK-027:PASS | — | **VERIFIED** |
| AB-1.2-02 |  | AxPROT passes through to PPROT. | CHK-016:PASS, CHK-029:PASS | — | **VERIFIED** |
| AB-2.1-01 |  | The RTL design must follow the VLSIT RTL Design Rules v2 as the mandatory RTL baseline. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-2.2-01 |  | A product choice must not weaken a protocol requirement of the selected standards. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| AB-3-01 | REQ-FUNC-001 | The bridge shall convert each accepted AXI transaction into ordered APB transfers and return its AXI completion. | CHK-027:PASS | 100.0 % (3/3) | **VERIFIED** |
| AB-3-02 | REQ-FUNC-002 | The bridge shall keep at most one global read or write transaction active at any time. | CHK-014:PASS | 100.0 % (4/4) | **VERIFIED** |
| AB-3-03 | REQ-FUNC-003 | The bridge shall arbitrate between AR and AW by round-robin. | CHK-019:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-3-04 | REQ-FUNC-003 | The bridge shall choose AR for the first tie after reset. | CHK-019:PASS, CHK-031:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-3-05 | REQ-FUNC-003 | The bridge shall flip the next tie preference between AR and AW after each completed transaction. | CHK-019:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-3-06 | REQ-IF-001 | The bridge shall accept an AXI transfer only when VALID and READY are both high at rising ACLK. | CHK-013:PASS, CHK-014:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB-3-07 | REQ-IF-002 | The bridge shall support FIXED bursts of 1–16 beats, INCR bursts of 1–256 beats, and WRAP bursts of 2, 4, 8 or 16 beats. | CHK-027:PASS | 100.0 % (4/4) | **VERIFIED** |
| AB-3-08 | REQ-IF-003 | The bridge shall support AxSIZE values 0, 1 and 2 (1, 2, 4 bytes). | CHK-022:PASS, CHK-027:PASS | — | **VERIFIED** |
| AB-3-09 | REQ-IF-003 | The bridge shall reject unsupported size/burst and 4-KiB-crossing transactions without any APB access. | CHK-015:PASS, CHK-022:PASS, CHK-023:PASS | 100.0 % (3/3) | **VERIFIED** |
| AB-3-10 | REQ-IF-004 | The bridge shall align APB PADDR down to a four-byte word boundary. | CHK-004:PASS, CHK-028:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-3-11 | REQ-IF-004 | The bridge shall copy WSTRB to PSTRB. | CHK-016:PASS, CHK-028:PASS | 100.0 % (3/3) | **VERIFIED** |
| AB-3-12 | REQ-IF-004 | The bridge shall drive PSTRB=0 on reads. | CHK-005:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-3-13 | REQ-IF-005 | The bridge shall echo ARID on every R beat. | CHK-010:PASS, CHK-030:PASS | — | **VERIFIED** |
| AB-3-14 | REQ-IF-005 | The bridge shall echo AWID on the corresponding B response. | CHK-008:PASS, CHK-030:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-3-15 | REQ-IF-006 | The bridge shall copy AxPROT to PPROT. | CHK-016:PASS, CHK-029:PASS | — | **VERIFIED** |
| AB-3-16 | REQ-IF-006 | The bridge shall omit AxLOCK, USER, QOS and REGION ports. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-3-17 | REQ-IF-007 | The bridge shall accept only AxCACHE values 0000 and 0001. | CHK-022:PASS, CHK-027:PASS | 100.0 % (3/3) | **VERIFIED** |
| AB-3-18 | REQ-IF-007 | The bridge shall return SLVERR without asserting PSEL. | CHK-015:PASS, CHK-022:PASS, CHK-023:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB-3-19 | REQ-IF-008 | The bridge shall not implement exclusive access. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-3-20 | REQ-IF-008 | Integration shall not send exclusive traffic to the bridge. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AB-3-21 | REQ-IF-009 | The bridge shall hold AXI VALID and payload stable through the handshake. | CHK-007:PASS, CHK-009:PASS | — | **VERIFIED** |
| AB-3-22 | REQ-IF-009 | The bridge shall hold APB control and payload stable while PREADY=0. | CHK-002:PASS, CHK-018:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-3-23 | REQ-CLK-001 | The bridge shall use one shared ACLK/PCLK domain. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-3-24 | REQ-CLK-001 | The bridge shall contain no asynchronous clock crossing. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-3-25 | REQ-RESET-001 | The bridge shall use one active-low reset synchronous to ACLK. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-3-26 | REQ-RESET-001 | The SoC shall supply the reset synchronized to ACLK. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AB-3-27 | REQ-RESET-001 | AXI VALID outputs shall be low while reset is sampled active. | CHK-017:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB-3-28 | REQ-PARAM-001 | PARA_AXI_ID_W shall range from 1 to 16, with default 4. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-3-29 | REQ-PARAM-001 | PARA_AXI_ID_W shall set both read and write ID widths. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-3-30 | REQ-ERR-001 | An unsupported read shall return ARLEN+1 R beats with SLVERR. | CHK-012:PASS, CHK-022:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB-3-31 | REQ-ERR-001 | RLAST shall be asserted only on the final beat of an unsupported read. | CHK-010:PASS, CHK-022:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB-3-32 | REQ-ERR-001 | The bridge shall not perform APB access for an unsupported read. | CHK-015:PASS, CHK-022:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB-3-33 | REQ-ERR-002 | The bridge shall map read PSLVERR to SLVERR on that R beat. | CHK-011:PASS, CHK-024:PASS | — | **VERIFIED** |
| AB-3-34 | REQ-ERR-002 | The bridge shall accumulate write errors into the final BRESP after all declared W beats. | CHK-008:PASS, CHK-025:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-3-35 | REQ-ERR-003 | The bridge shall drain AWLEN+1 W beats for an unsupported write. | CHK-013:PASS, CHK-023:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-3-36 | REQ-ERR-003 | The bridge shall not perform APB access for an unsupported write. | CHK-015:PASS, CHK-023:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-3-37 | REQ-ERR-003 | The bridge shall then return one SLVERR B response. | CHK-008:PASS, CHK-023:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-3-38 | REQ-ERR-004 | The external APB fabric shall provide a default unmapped Completer with PREADY=1 and PSLVERR=1. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AB-3-39 | REQ-ERR-005 | The bridge shall have no APB timeout. | CHK-018:PASS | — | **VERIFIED** |
| AB-3-40 | REQ-ERR-005 | The bridge shall hold the APB access while PREADY=0 and wait indefinitely if PREADY never rises. | CHK-002:PASS, CHK-018:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-3-41 | REQ-ERR-006 | A completed APB transfer with PSLVERR=1 shall cause the associated AXI response to be SLVERR. | CHK-008:PASS, CHK-011:PASS, CHK-024:PASS, CHK-025:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB-3-42 | REQ-CSR-001 | The bridge shall contain no software-visible CSR interface. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-3-43 | REQ-VER-001 | Verification shall derive expected results from this specification and cited standards, never from generated RTL. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AB-3-44 | REQ-VER-002 | Verification deliverables shall retain generated testbench sources and commands. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AB-3-45 | REQ-VER-002 | Verification shall use one Makefile as the documented command entry point. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AB-4-01 |  | CFG-BASE shall provide a full AXI4 Subordinate and an APB4 Manager with legal FIXED/INCR/WRAP bursts and ID echo. | CHK-027:PASS | — | **VERIFIED** |
| AB-4-02 |  | CFG-BASE shall not include CDC, timeout, CSR, exclusive access, or USER/QOS/REGION features (disabled). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-4-04 |  | The AXI ID width may be configured at elaboration. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-5.1-02 |  | m_axi2apb_apb_ctrl arbitrates between AR and AW requests in round-robin order. | CHK-019:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-5.1-03 |  | AXI response backpressure must stall the sequencer that owns the transaction. | CHK-021:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-5.1-04 |  | m_axi2apb_apb_ctrl retains the transaction owner until the final R or B response completes. | CHK-014:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB-5.3-01 |  | The bridge performs one APB read per beat in AXI order, then presents RVALID/RDATA/RRESP/RLAST/RID and holds them until RREADY. | CHK-009:PASS, CHK-011:PASS, CHK-021:PASS, CHK-027:PASS | 100.0 % (4/4) | **VERIFIED** |
| AB-5.3-02 |  | The bridge accepts AW first and then W beats in order. | CHK-013:PASS, CHK-016:PASS, CHK-020:PASS | 100.0 % (3/3) | **VERIFIED** |
| AB-5.3-03 |  | The master may assert WVALID before the AW address is accepted. | CHK-020:PASS | — | **VERIFIED** |
| AB-5.3-04 |  | WREADY must remain low until AW has been accepted. | CHK-013:PASS, CHK-020:PASS | — | **VERIFIED** |
| AB-5.3-05 |  | The bridge performs one APB write per beat and returns B only after the last APB completion. | CHK-008:PASS, CHK-016:PASS, CHK-027:PASS | 100.0 % (4/4) | **VERIFIED** |
| AB-5.4-03 |  | APB payload and control signals must remain stable during wait. | CHK-002:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-5.4-04 |  | IDs are retained and echoed unchanged in the response (RID equals ARID, BID equals AWID). | CHK-008:PASS, CHK-010:PASS, CHK-030:PASS | — | **VERIFIED** |
| AB-5.4-05 |  | The read beat count is ARLEN+1 and the legal write beat count is AWLEN+1. | CHK-008:PASS, CHK-010:PASS, CHK-027:PASS | 100.0 % (4/4) | **VERIFIED** |
| AB-5.4-06 |  | AXI response payload must remain stable while VALID=1 and READY=0. | CHK-007:PASS, CHK-009:PASS | — | **VERIFIED** |
| AB-6.1-01 |  | The bridge must implement the required AXI4 (IHI 0022 H.c) Subordinate interface IF-001 on CLK-AXI in CFG-BASE. | CHK-027:PASS | — | **VERIFIED** |
| AB-6.1-02 |  | The bridge must implement the required APB4 (IHI 0024 D) Manager/Requester interface IF-002 on CLK-AXI with PCLK=ACLK in CFG-BASE. | CHK-001:PASS, CHK-027:PASS | — | **VERIFIED** |
| AB-6.2-01 |  | APB setup phase must have o_apb_psel=1 and o_apb_penable=0; access phase has both 1 and completes when i_apb_pready=1. | CHK-001:PASS | 100.0 % (6/6) | **VERIFIED** |
| AB-6.2-02 |  | o_axi_bid and o_axi_bresp must remain stable until the B handshake completes. | CHK-007:PASS | — | **VERIFIED** |
| AB-6.2-03 |  | o_axi_bid and o_axi_bresp must be 0 in reset. | CHK-017:PASS | — | **VERIFIED** |
| AB-6.2-04 |  | o_axi_rid, o_axi_rdata and o_axi_rresp must remain stable until the R handshake completes. | CHK-009:PASS | — | **VERIFIED** |
| AB-6.2-05 |  | o_axi_rid, o_axi_rdata and o_axi_rresp must be 0 in reset. | CHK-017:PASS | — | **VERIFIED** |
| AB-6.2-06 |  | o_axi_rlast must be high only on the final read beat. | CHK-010:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB-6.2-07 |  | o_apb_paddr, o_apb_pwrite and o_apb_pprot must remain stable through the transfer. | CHK-002:PASS, CHK-003:PASS | — | **VERIFIED** |
| AB-6.2-08 |  | o_apb_paddr, o_apb_pwrite, o_apb_pwdata, o_apb_pstrb and o_apb_pprot must be 0 when idle. | CHK-006:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-6.2-09 |  | o_apb_paddr must be a word-aligned byte address. | CHK-004:PASS | — | **VERIFIED** |
| AB-6.2-10 |  | o_apb_pwdata must remain stable during wait states. | CHK-002:PASS | — | **VERIFIED** |
| AB-6.2-11 |  | o_apb_pstrb must remain stable through the access. | CHK-002:PASS, CHK-003:PASS | — | **VERIFIED** |
| AB-6.2-12 |  | o_apb_pstrb must be zero on reads. | CHK-005:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-6.2-13 |  | o_apb_pprot must be a copy of the corresponding AxPROT. | CHK-016:PASS, CHK-029:PASS | — | **VERIFIED** |
| AB-6.3-01 | REQ-ERR-001, REQ-IF-002 | A legal AXI read (FIXED/INCR/WRAP, size 0–2, cache 0000/0001) must be supported and performed as APB transfers. | CHK-027:PASS | 100.0 % (4/4) | **VERIFIED** |
| AB-6.3-02 | REQ-ERR-001, REQ-IF-002 | The bridge must issue no APB transfer and return ARLEN+1 R beats with RRESP SLVERR. | CHK-012:PASS, CHK-015:PASS, CHK-022:PASS | 100.0 % (3/3) | **VERIFIED** |
| AB-6.3-03 | REQ-ERR-003, REQ-IF-002 | A legal AXI write consists of an AW request followed by the declared number of W beats; W data may arrive before AW. | CHK-020:PASS, CHK-027:PASS | 100.0 % (3/3) | **VERIFIED** |
| AB-6.3-05 | REQ-ERR-003, REQ-IF-002 | The bridge must issue no APB transfer, drain the W beats, then return a B response with SLVERR. | CHK-015:PASS, CHK-023:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB-6.3-07 | REQ-ERR-005, REQ-IF-004 | The bridge must perform one APB transfer per AXI beat. | CHK-016:PASS, CHK-027:PASS | 100.0 % (7/7) | **VERIFIED** |
| AB-6.3-08 | REQ-ERR-005, REQ-IF-004 | The bridge must hold the APB access indefinitely and not time out. | CHK-018:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-6.3-09 | REQ-ERR-002 | The bridge must sample PSLVERR on the completed APB transfer. | CHK-011:PASS, CHK-024:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-6.3-10 | REQ-ERR-002 | The bridge must return the read beat with RRESP SLVERR, treating read data as invalid. | CHK-011:PASS, CHK-024:PASS | — | **VERIFIED** |
| AB-6.3-11 | REQ-ERR-002 | The bridge must accumulate the write error and report it in BRESP. | CHK-008:PASS, CHK-025:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-6.3-12 | REQ-ERR-004 | The external default Completer must respond with PREADY=1 and PSLVERR=1, and the bridge must then return AXI SLVERR. | CHK-026:PASS | — | **VERIFIED** |
| AB-6.3-14 |  | The bridge must reject the request before issuing any APB traffic. | CHK-015:PASS, CHK-022:PASS, CHK-023:PASS | — | **VERIFIED** |
| AB-6.3-15 |  | A burst must not cross a 4-KiB address boundary. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AB-7.2-01 |  | The SoC must provide i_rst_n_axi synchronous to CLK-AXI (i_clk_axi). | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AB-7.3-01 |  | PSEL and PENABLE must be 0 after the active reset edge, and AXI VALID outputs must be 0 during reset. | CHK-017:PASS, CHK-031:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB-7.3-02 |  | Reset is sampled on the rising edge of i_clk_axi, and i_rst_n_axi must be kept active for at least one rising edge. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AB-7.3-03 |  | The SoC owns reset synchronization and must coordinate the reset of the AXI Manager with the APB fabric. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AB-8-01 |  | PARA_AXI_ID_W must be declared as parameter logic [31:0] with default value 4. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-8-02 |  | The comments Parameter Description, Parameter values and Parameter unit must immediately precede the PARA_AXI_ID_W declaration. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-8-03 |  | PARA_AXI_ID_W legal range is 1 to 16 inclusive; any invalid value must cause an elaboration error. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-8-04 |  | PARA_AXI_ID_W must set the width of the AXI read/write ID ports, shared between read and write. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-8-05 |  | Address, data and APB widths must be fixed at 32 bits. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-8-06 |  | CFG-BASE must elaborate with hierarchy m_axi2apb_bridge containing m_axi2apb_rd_seq, m_axi2apb_wr_seq and m_axi2apb_apb_ctrl, and ID widths 1, 4, 16 must pass elaboration, lint and synthesis checks. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-9-02 |  | A burst that crosses a 4-KiB boundary must be rejected. | CHK-022:PASS, CHK-023:PASS | 100.0 % (3/3) | **VERIFIED** |
| AB-9-03 |  | The 32-bit data path must not rotate byte lanes between AXI and APB. | CHK-011:PASS, CHK-016:PASS, CHK-028:PASS | — | **VERIFIED** |
| AB-9-05 |  | The AXI ID must be echoed unchanged in the response without remapping. | CHK-008:PASS, CHK-010:PASS, CHK-030:PASS | — | **VERIFIED** |
| AB-9-06 |  | AxSIZE values other than 0, 1 and 2 must be rejected. | CHK-022:PASS, CHK-023:PASS | — | **VERIFIED** |
| AB-9-08 |  | A reserved AxBURST value must be rejected; FIXED, INCR and WRAP are the legal values. | CHK-022:PASS, CHK-023:PASS | — | **VERIFIED** |
| AB-9-09 |  | AxCACHE encodings other than 0000 and 0001 must be rejected; AxCACHE is used for validation only. | CHK-022:PASS, CHK-023:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB-9-10 |  | AxPROT must be copied directly to PPROT with no translation. | CHK-016:PASS, CHK-029:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-9-11 |  | For subword writes, WSTRB must be copied to PSTRB unchanged. | CHK-016:PASS, CHK-028:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB-9-13 |  | APB PADDR must be word-aligned. | CHK-004:PASS | — | **VERIFIED** |
| AB-10.1-01 |  | In IDLE the bridge arbitrates between AR and AW and selects a transaction upon address handshake. | CHK-019:PASS | 100.0 % (3/3) | **VERIFIED** |
| AB-10.1-03 |  | In WRITE the bridge accepts W, performs an APB write per beat, returns one B, and exits on B handshake. | CHK-027:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-10.1-06 |  | Reset returns the bridge to IDLE, clears local state, deselects APB, and cancels in-flight work. | CHK-017:PASS, CHK-031:PASS | — | **VERIFIED** |
| AB-10.2-01 |  | A read performs an APB read per beat, holds the address for FIXED and follows AXI address rules for INCR and WRAP, returns ARLEN+1 R beats with RID echoed and final RLAST, serialized. | CHK-016:PASS, CHK-027:PASS | 100.0 % (11/11) | **VERIFIED** |
| AB-10.2-02 |  | A write performs an APB write per beat, maps WSTRB to PSTRB, accumulates PSLVERR, and returns one B only after final APB completion, serialized. | CHK-008:PASS, CHK-016:PASS, CHK-027:PASS | 100.0 % (11/11) | **VERIFIED** |
| AB-10.2-03 |  | An unsupported read performs no APB access and returns ARLEN+1 R beats with SLVERR and zero data, honoring RREADY. | CHK-012:PASS, CHK-022:PASS | 100.0 % (3/3) | **VERIFIED** |
| AB-10.2-04 |  | An unsupported write performs no APB access, drains the declared W count, and returns one SLVERR B after the final W. | CHK-008:PASS, CHK-023:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB-10.2-05 |  | PSLVERR on a read beat marks that beat's response as error. | CHK-011:PASS, CHK-024:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-10.2-06 |  | Write PSLVERR accumulates, later beats still execute, and final BRESP is SLVERR. | CHK-008:PASS, CHK-025:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB-10.3-02 |  | The bridge has no internal APB timeout; it must not abort an APB transfer by timeout. | CHK-018:PASS | — | **VERIFIED** |
| AB-10.3-03 |  | Signals are sampled on the rising edge of CLK-AXI. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| AB-10.3-04 |  | APB setup is PSEL=1/PENABLE=0, access is PSEL=1/PENABLE=1, and completion requires PREADY=1. | CHK-001:PASS | 100.0 % (4/4) | **VERIFIED** |
| AB-10.4-01 |  | AR/AW arbitration is round-robin when both are pending. | CHK-019:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-10.4-02 |  | The selected transaction owns the bridge until its final R handshake or B handshake. | CHK-014:PASS, CHK-021:PASS | 100.0 % (4/4) | **VERIFIED** |
| AB-12-01 |  | Respond with ARLEN+1 SLVERR read beats carrying zero data and RLAST on the final beat, without issuing any APB access. | CHK-012:PASS, CHK-022:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-12-02 |  | Do not generate any APB transfer for an unsupported read. | CHK-015:PASS, CHK-022:PASS | 100.0 % (2/2) | **VERIFIED** |
| AB-12-04 |  | Drain the expected count of W beats, then complete the write with a B response of SLVERR, without any APB access. | CHK-008:PASS, CHK-023:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-12-05 |  | Do not generate any APB transfer for an unsupported write. | CHK-015:PASS, CHK-023:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-12-06 |  | Return RRESP=SLVERR with RDATA=0 for the beat, and continue processing the remaining beats. | CHK-011:PASS, CHK-024:PASS | — | **VERIFIED** |
| AB-12-07 |  | Accumulate the error, continue the remaining write beats, and return final BRESP=SLVERR. | CHK-008:PASS, CHK-025:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-12-08 |  | Hold the APB access indefinitely with no timeout until the completer responds or system reset occurs. | CHK-018:PASS | — | **VERIFIED** |
| AB-12-09 |  | Reset deselects the APB completer. | CHK-017:PASS, CHK-031:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-12-10 |  | Default Completer drives PREADY=1 and PSLVERR=1, and the bridge reports an AXI SLVERR response. | CHK-026:PASS | — | **VERIFIED** |
| AB-12-11 |  | Never report an APB failure as AXI OKAY. | CHK-008:PASS, CHK-011:PASS, CHK-024:PASS, CHK-025:PASS | — | **VERIFIED** |
| AB-15.1-02 |  | The RTL must not define expected results; expected results come from the independent reference model. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AB-15.2-01 | REQ-FUNC-001, REQ-IF-002 | The independent model must match the bridge addresses, data and responses for FIXED, INCR and WRAP bursts with legal sizes. | CHK-027:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-15.2-02 | REQ-ERR-005, REQ-IF-009 | Payload must remain stable through APB wait states and RREADY/BREADY stalls, checked by assertions. | CHK-002:PASS, CHK-007:PASS, CHK-009:PASS, CHK-021:PASS | — | **VERIFIED** |
| AB-17.1-01 |  | The SoC integrator must provide clock period, uncertainty, transition, latency, interface delays, loads, PVT/RC corners and timing modes before timing closure. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AB-17.1.3-01 |  | A later timing exception must have exact endpoints, mode, rationale and CDC/RDC evidence. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-17.1.3-02 |  | Broad timing exceptions must not be used. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-18-01 |  | The bridge must map AxPROT to PPROT. | CHK-016:PASS, CHK-029:PASS | — | **VERIFIED** |
| AB-18-02 |  | The bridge must not perform a local access-control check on PPROT; APB Completers enforce PPROT. | CHK-029:PASS | — | **VERIFIED** |
| AB-18-03 |  | The bridge must propagate errors and provide no interrupt or status mechanism. | CHK-024:PASS, CHK-025:PASS, CHK-026:PASS | — | **VERIFIED** |
| AB-20-01 |  | The bridge must support the conversion profile: FIXED/INCR/WRAP burst types, legal lengths, 1/2/4-byte transfer sizes, and PSTRB/PPROT conversion. | CHK-027:PASS | 100.0 % (1/1) | **VERIFIED** |
| AB-20-02 |  | The bridge has no timeout or CSR, so the system must provide a default APB error Completer. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AB-20-04 |  | Any lint finding must be fixed or reported under the skill rules, with no project-specific waivers. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| AB-20-05 |  | The AXI Manager must comply with AXI4 WLAST/AWLEN and WSTRB rules; no RTL recovery is defined for malformed write traffic. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| AB-20-06 |  | Reset must cancel local state without replay or rollback, which requires coordinated system reset. | CHK-031:PASS | — | **VERIFIED** |
| AB-20-07 |  | The APB address map/decoder must provide a match or a default response with PREADY=1 and PSLVERR=1. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |

## Mutants

| ID | File:line | Operator | Status | Caught by | Rules | Equivalent? |
|---|---|---|---|---|---|---|
| M01 | m_axi2apb_rd_seq.sv:374 | or_to_and | killed | CHK-016, CHK-010, test_chk_019_arbitration_round_robin, test_chk_021_response_backpressure, test_chk_022_unsupported_rea | AB-10.2-01, AB-5.4-05, AB-6.2-06, AB-3-31, AB-5.3-01 |  |
| M02 | m_axi2apb_wr_seq.sv:342 | eq_to_ne | killed | CHK-016, CHK-013, test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_020_wvalid_before_aw, test_ | AB-3-11, AB-9-11, AB-10.2-02, AB-5.3-05, AB-5.4-05 |  |
| M03 | m_axi2apb_wr_seq.sv:195 | zero_to_one | killed | test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_020_wvalid_before_aw, test_chk_021_response_b | AB-9-02, AB-3-09, AB-10.2-02, AB-6.3-03, AB-3-01 |  |
| M04 | m_axi2apb_wr_seq.sv:301 | negate_if | killed | CHK-014, CHK-016, test_chk_019_arbitration_round_robin, test_chk_021_response_backpressure, test_chk_023_unsupported_wri | AB-10.1-01, AB-10.4-02, AB-3-02, AB-5.3-02, AB-3-06 |  |
| M05 | m_axi2apb_wr_seq.sv:235 | ne_to_eq | killed | CHK-016, test_chk_027_random_legal_bursts, test_regression_random | AB-3-07, AB-15.2-01, AB-20-01, AB-10.2-02, AB-6.3-07 |  |
| M06 | m_axi2apb_apb_ctrl.sv:181 | negate_if | killed | CHK-016, test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_020_wvalid_before_aw, test_chk_021_r | AB-6.3-07, AB-10.2-01, AB-10.2-02, AB-5.4-03, AB-6.2-01 |  |
| M07 | m_axi2apb_apb_ctrl.sv:265 | eq_to_ne | killed | test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_020_wvalid_before_aw, test_chk_021_response_b | AB-6.3-09, AB-3-41, AB-10.2-05, AB-10.2-06, AB-6.2-01 |  |
| M08 | m_axi2apb_wr_seq.sv:342 | and_to_or | killed | CHK-016, CHK-013, test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_020_wvalid_before_aw, test_ | AB-5.4-05, AB-10.2-02, AB-3-11, AB-9-11, AB-5.3-05 |  |
| M09 | m_axi2apb_apb_ctrl.sv:165 | zero_to_one | survived |  |  | claimed: This is the default assignment at the top of the always_comb. The following case on the APB state overwrites o_apb_pwrite in every branch: SETUP and ACCESS set  |
| M10 | m_axi2apb_rd_seq.sv:123 | one_to_zero | killed | CHK-011, test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_021_response_backpressure, test_chk_ | AB-6.3-01, AB-10.2-01, AB-3-01, AB-3-07, AB-3-17 |  |
| M11 | m_axi2apb_apb_ctrl.sv:259 | one_to_zero | killed | CHK-016, CHK-005, test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_020_wvalid_before_aw, test_ | AB-10.2-02, AB-5.3-05, AB-3-11, AB-3-12, AB-6.2-12 |  |
| M12 | m_axi2apb_rd_seq.sv:312 | zero_to_one | killed | CHK-017, CHK-014, test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_020_wvalid_before_aw, test_ | AB-3-27, AB-7.3-01, AB-5.3-01, AB-10.2-01, AB-3-02 |  |
| M13 | m_axi2apb_wr_seq.sv:183 | or_to_and | survived |  |  | claimed: The OR becomes an AND, so the result differs only for a WRAP burst with exactly one fault: a bad length (not 2/4/8/16) with an aligned address, or a good length |
| M14 | m_axi2apb_apb_ctrl.sv:223 | and_to_or | survived |  |  | claimed: The mutant clears reg_turn_rd while in ACTRD even without rd_done. The value is used only in the IDLE state, and ACTRD always ends with rd_done, which clears it |
| M15 | m_axi2apb_apb_ctrl.sv:137 | or_to_and | killed | test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_020_wvalid_before_aw, test_chk_021_response_b | AB-6.2-01, AB-10.3-04, AB-6.3-07, AB-10.2-01, AB-10.2-02 |  |
| M16 | m_axi2apb_rd_seq.sv:376 | ne_to_eq | killed | CHK-016, CHK-010, test_chk_019_arbitration_round_robin, test_chk_021_response_backpressure, test_chk_022_unsupported_rea | AB-6.2-06, AB-5.4-05, AB-10.2-01, AB-3-31, AB-5.3-01 |  |
| M17 | m_axi2apb_rd_seq.sv:321 | eq_to_ne | killed | CHK-014, CHK-015, CHK-016, test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_021_response_backp | AB-3-32, AB-12-02, AB-6.3-02, AB-10.2-01, AB-6.3-07 |  |
| M18 | m_axi2apb_rd_seq.sv:267 | negate_if | killed | CHK-015, CHK-011, test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_021_response_backpressure,  | AB-6.3-01, AB-6.3-02, AB-12-02, AB-3-30, AB-10.2-03 |  |
| M19 | m_axi2apb_rd_seq.sv:332 | and_to_or | killed | CHK-014, test_chk_019_arbitration_round_robin, test_chk_021_response_backpressure, test_chk_022_unsupported_reads, test_ | AB-10.4-02, AB-5.1-04, AB-5.1-03, AB-3-02, AB-10.2-01 |  |
| M20 | m_axi2apb_wr_seq.sv:311 | one_to_zero | killed | CHK-014, CHK-013, test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_020_wvalid_before_aw, test_ | AB-10.2-02, AB-3-37, AB-5.3-05, AB-12-04, AB-3-14 |  |
| M21 | m_axi2apb_rd_seq.sv:182 | or_to_and | survived |  |  | claimed: The OR becomes an AND, so the result differs only for a WRAP read with exactly one fault: a bad length with an aligned address, or a good length with a misalign |
| M22 | m_axi2apb_wr_seq.sv:301 | eq_to_ne | killed | CHK-014, CHK-016, test_chk_019_arbitration_round_robin, test_chk_021_response_backpressure, test_chk_023_unsupported_wri | AB-10.1-01, AB-10.4-02, AB-3-02, AB-5.3-02, AB-3-06 |  |
| M23 | m_axi2apb_wr_seq.sv:133 | zero_to_one | killed | test_chk_021_response_backpressure, test_chk_023_unsupported_writes, test_chk_027_random_legal_bursts, test_chk_030_id_e | AB-9-02, AB-3-09, AB-3-07, AB-10.2-02, AB-6.3-03 |  |
| M24 | m_axi2apb_wr_seq.sv:308 | negate_if | killed | CHK-015, CHK-016, test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_020_wvalid_before_aw, test_ | AB-3-36, AB-12-05, AB-6.3-05, AB-10.2-02, AB-6.3-07 |  |
| M25 | m_axi2apb_wr_seq.sv:198 | ne_to_eq | killed | test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_020_wvalid_before_aw, test_chk_021_response_b | AB-9-09, AB-3-17, AB-3-18, AB-6.3-05, AB-10.2-04 |  |
| M26 | m_axi2apb_apb_ctrl.sv:96 | negate_if | killed | test_chk_019_arbitration_round_robin, test_chk_031_reset_mid_transaction | AB-3-04, AB-3-05, AB-3-03, AB-5.1-02, AB-10.4-01 |  |
| M27 | m_axi2apb_apb_ctrl.sv:249 | eq_to_ne | killed | CHK-016, test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_021_response_backpressure, test_chk_ | AB-10.2-01, AB-10.2-02, AB-6.3-07, AB-9-10, AB-3-10 |  |
| M28 | m_axi2apb_wr_seq.sv:351 | and_to_or | killed | CHK-008, test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_020_wvalid_before_aw, test_chk_021_r | AB-6.3-11, AB-10.2-06, AB-12-07, AB-3-34, AB-3-41 |  |
| M29 | m_axi2apb_apb_ctrl.sv:211 | zero_to_one | killed | CHK-017, CHK-001, CHK-006, test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_020_wvalid_before_ | AB-6.2-08, AB-7.3-01, AB-6.2-01, AB-10.3-04, AB-12-09 |  |
| M30 | m_axi2apb_rd_seq.sv:318 | one_to_zero | killed | test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_021_response_backpressure, test_chk_026_unmap | AB-10.1-01, AB-5.1-04, AB-10.4-02, AB-6.3-01, AB-3-01 |  |
| M31 | m_axi2apb_apb_ctrl.sv:201 | one_to_zero | killed | CHK-011, CHK-008, CHK-001, CHK-006, test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_020_wvali | AB-6.2-01, AB-10.3-04, AB-3-40, AB-3-22, AB-6.3-08 |  |
| M32 | m_axi2apb_rd_seq.sv:127 | zero_to_one | killed | CHK-011, test_chk_021_response_backpressure, test_chk_022_unsupported_reads, test_chk_027_random_legal_bursts, test_chk_ | AB-9-02, AB-3-09, AB-3-07, AB-6.3-01, AB-10.2-01 |  |
| M33 | m_axi2apb_wr_seq.sv:305 | or_to_and | killed | CHK-008, test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_020_wvalid_before_aw, test_chk_021_r | AB-5.3-02, AB-3-35, AB-10.1-03, AB-6.3-03, AB-10.2-04 |  |
| M34 | m_axi2apb_apb_ctrl.sv:137 | and_to_or | killed | CHK-014, CHK-015, CHK-016, test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_021_response_backp | AB-6.3-07, AB-10.2-01, AB-10.3-04, AB-6.2-01, AB-3-32 |  |
| M35 | m_axi2apb_rd_seq.sv:200 | ne_to_eq | killed | CHK-011, test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_021_response_backpressure, test_chk_ | AB-9-09, AB-3-17, AB-3-18, AB-6.3-02, AB-10.2-03 |  |
| M36 | m_axi2apb_rd_seq.sv:324 | eq_to_ne | killed | CHK-017, CHK-014, test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_020_wvalid_before_aw, test_ | AB-3-30, AB-10.2-03, AB-12-01, AB-5.3-01, AB-3-27 |  |

## Not verified by this run

- Formal proof, CDC/RDC, STA, synthesis and DFT checks are outside this flow.
- Rules marked NOT_VERIFIED_BY_SIM carry the contract's reason (static, structural, not observable...).
- Only the default parameter configuration was simulated (no run_set.json).

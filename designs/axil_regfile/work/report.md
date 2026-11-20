# Verification report — axil_regfile

Generated 2026-11-20T08:35:26+00:00 by NNC Pipeline.

## Summary

| Item | Result |
|---|---|
| Rules | 193 — {'NOT_VERIFIED_BY_SIM': 22, 'VERIFIED': 171} |
| Checks | 37 — {'PASS': 37} |
| Tests | {'pass': 21} |
| Run set | 7 runs in 4 configurations (base, min, max, full_a7); primary base.s1 |
| Integration | OK |
| Code coverage (RTL), line | 100.0 % (565/565 lines) |
| Code coverage (RTL), block | 100.0 % (120/120 statement blocks and branch arms) |
| Code coverage (RTL), expression | 95.7 % (358/374 condition terms) |
| Code coverage (RTL), toggle | 95.8 % (6844/7144 bit toggles 0->1 and 1->0) |
| Code coverage (RTL), functional | 100.0 % (40/40 cover points of the specification) |
| Mutation score | 93.1 % (27 killed / 2 survived / 0 not compiled) |
| Coverage target | not requested (`nnc cover <design> --target <n> --metric <m>`) |
| Formal (SymbiYosys, depth 32) | {'BOUNDED': 1, 'PROVEN': 15, 'UNSUPPORTED': 1} — reset assumptions + verif/formal/nnc_env.sv, work/formal.md |
| Triage | no failure to analyse |
| Agent cost | US$12.5748 in 47 calls (A0 1.2685, A1 0.4836, A12 0.775, A13 0.1795, A15 1.0562, A18 0.5058, A2 0.4543, A3 0.1659, A4 1.0712, A5 0.3848, A6 0.2511, A7 5.9788) |

## Sign-off conditions

| Condition | State |
|---|---|
| Gates G1-G3 approved | met — approved on delegation by an agent: a person should confirm |
| Interface conformance of the DUT | met |
| Every selected check PASS (no FAIL, NOT_HIT, NOT_RUN) | met |
| Every planned check selected | met |
| Every rule in a check or declared not verifiable | met |
| Every run of the run set built and ran | met — 7 runs |
| Mutation run | met |
| Per-requirement mutation score >= 85 % | met — 58 rules with attributed mutants |
| Formal: no counterexample, no vacuous or failed proof | met — {'BOUNDED': 1, 'PROVEN': 15, 'UNSUPPORTED': 1} (work/formal.md) |

## Run set

Every check is merged over these runs: PASS when one run verified it and no run failed it; NOT_VERIFIABLE only when every run declared it so.

| Run | Parameters changed | Defines | Plusargs | Status | Tests | Failing assertions | Not verifiable here |
|---|---|---|---|---|---|---|---|
| base.s1 — CFG-BASE | defaults | — | — | ran | {'pass': 21} | none | 3 |
| base.s2 — CFG-BASE | defaults | — | — | ran | {'pass': 21} | none | 3 |
| min.s1 — CFG-MIN | PARA_NUM_REGS=1, PARA_ADDR_W=7 | — | — | ran | {'pass': 21} | none | 4 |
| min.s2 — CFG-MIN | PARA_NUM_REGS=1, PARA_ADDR_W=7 | — | — | ran | {'pass': 21} | none | 4 |
| max.s1 — CFG-MAX | PARA_NUM_REGS=16, PARA_ADDR_W=16 | — | — | ran | {'pass': 21} | none | 1 |
| max.s2 — CFG-MAX | PARA_NUM_REGS=16, PARA_ADDR_W=16 | — | — | ran | {'pass': 21} | none | 1 |
| full_a7.s1 — CFG-FULL-A7 | PARA_NUM_REGS=16, PARA_ADDR_W=7 | — | — | ran | {'pass': 21} | none | 2 |

## Gates

| Gate | State | Detail |
|---|---|---|
| G1_rules | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-19T10:55:31+00:00 |
| G2_contract | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-19T11:01:13+00:00 |
| D1_config | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-19T11:01:14+00:00 |
| D2_rtl | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-19T11:05:52+00:00 |
| G3_verif_sources | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-20T05:35:47+00:00 |
| G4_signoff | PENDING | artifacts ready for review |

## Checks

| Check | Kind | Title | Status | Evidence |
|---|---|---|---|---|
| CHK-001 | assertion | o_s_axi_arready follows the held-read-address state | **PASS** | hits 93857, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-002 | assertion | o_s_axi_rvalid is exactly predicted: 1 from Ear until Er, otherwise 0 | **PASS** | hits 93857, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-003 | assertion | R response held stable under back-pressure | **PASS** | hits 6093, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-004 | assertion | o_s_axi_rresp never EXOKAY or DECERR | **PASS** | hits 45271, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-005 | assertion | Read data and response match the value sampled at Ear | **PASS** | hits 45271, fails 0; hit in 7/7 runs; formal BOUNDED |
| CHK-006 | assertion | o_s_axi_awready follows the held-write-address state | **PASS** | hits 93857, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-007 | assertion | o_s_axi_wready follows the held-write-data state | **PASS** | hits 93857, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-008 | assertion | o_s_axi_bvalid is exactly predicted: 1 from Ec until Eb, otherwise 0 | **PASS** | hits 93857, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-009 | assertion | B response held stable under back-pressure | **PASS** | hits 5643, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-010 | assertion | o_s_axi_bresp never EXOKAY or DECERR | **PASS** | hits 12335, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-011 | assertion | o_s_axi_bresp matches the decode of the address taken at Ea | **PASS** | hits 12335, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-012 | assertion | o_regs equals the reference register model every cycle | **PASS** | hits 94088, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-013 | assertion | Handshake outputs are 0 while reset is asserted; no transfer while i_rst_n=0 | **PASS** | hits 995, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-014 | assertion | Data outputs and o_regs are 0 while reset is asserted | **PASS** | hits 995, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-015 | assertion | No transfer at R1 | **PASS** | hits 231, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-016 | assertion | Readies are 1 from R1 | **PASS** | hits 231, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-017 | assertion | Outputs change only at a rising edge of i_clk or at reset assertion | **PASS** | hits 94088, fails 0; hit in 7/7 runs; formal UNSUPPORTED |
| CHK-018 | test | R channel back-pressure and blocking of new AR | **PASS** | test_chk_018_r_backpressure; verified in base.s1, base.s2, min.s1, min.s2, max.s1, max.s2, full_a7.s1 |
| CHK-019 | test | Write address/data ordering: AW first, W first, same edge | **PASS** | test_chk_019_write_ordering; verified in base.s1, base.s2, min.s1, min.s2, max.s1, max.s2, full_a7.s1 |
| CHK-020 | test | B channel back-pressure and blocking of new AW/W | **PASS** | test_chk_020_b_backpressure; verified in base.s1, base.s2, min.s1, min.s2, max.s1, max.s2, full_a7.s1 |
| CHK-021 | test | CFG-MIN map (PARA_NUM_REGS=1, PARA_ADDR_W=7) | **PASS** | test_chk_021_cfg_min_map; verified in min.s1, min.s2 |
| CHK-022 | test | PARA_NUM_REGS=16 map (CFG-FULL-A7, also CFG-MAX) | **PASS** | test_chk_022_full_bank_map; verified in max.s1, max.s2, full_a7.s1 |
| CHK-023 | test | PARA_ADDR_W=16 high-bit decode (CFG-MAX) | **PASS** | test_chk_023_high_bit_decode; verified in max.s1, max.s2 |
| CHK-024 | test | Back-to-back throughput, writes and reads alone and together | **PASS** | test_chk_024_back_to_back; verified in base.s1, base.s2, min.s1, min.s2, max.s1, max.s2, full_a7.s1 |
| CHK-025 | test | Concurrent read and write of the same register around Ec | **PASS** | test_chk_025_concurrent_same_register; verified in base.s1, base.s2, max.s1, max.s2, full_a7.s1 |
| CHK-026 | test | Back-pressure on one direction does not stall the other | **PASS** | test_chk_026_backpressure_isolation; verified in base.s1, base.s2, min.s1, min.s2, max.s1, max.s2, full_a7.s1 |
| CHK-027 | test | Register map and aliasing: unique values in every register, full address sweep | **PASS** | test_chk_027_map_and_aliasing; verified in base.s1, base.s2, min.s1, min.s2, max.s1, max.s2, full_a7.s1 |
| CHK-028 | test | Status register: sampling at Ear, hold under back-pressure, writes ignored | **PASS** | test_chk_028_status_register; verified in base.s1, base.s2, min.s1, min.s2, max.s1, max.s2, full_a7.s1 |
| CHK-029 | test | Unmapped addresses: SLVERR, rdata 0, no register change, normal timing | **PASS** | test_chk_029_unmapped_addresses; verified in base.s1, base.s2, min.s1, min.s2, max.s1, max.s2, full_a7.s1 |
| CHK-030 | test | Unmapped access does not stall or disturb other channels or the next transaction | **PASS** | test_chk_030_unmapped_no_stall; verified in base.s1, base.s2, min.s1, min.s2, max.s1, max.s2, full_a7.s1 |
| CHK-031 | test | Address bits [1:0] and AxPROT have no effect | **PASS** | test_chk_031_addr_lsb_and_prot_ignored; verified in base.s1, base.s2, min.s1, min.s2, max.s1, max.s2, full_a7.s1 |
| CHK-032 | test | All 16 write-strobe values with byte-distinct data | **PASS** | test_chk_032_write_strobes; verified in base.s1, base.s2, min.s1, min.s2, max.s1, max.s2, full_a7.s1 |
| CHK-033 | test | Power-on reset and post-reset idle state | **PASS** | test_chk_033_power_on_reset; verified in base.s1, base.s2, min.s1, min.s2, max.s1, max.s2, full_a7.s1 |
| CHK-034 | test | Asynchronous reset assertion mid-cycle with transactions in progress | **PASS** | test_chk_034_async_reset_mid_cycle; verified in base.s1, base.s2, min.s1, min.s2, max.s1, max.s2, full_a7.s1 |
| CHK-035 | test | Reset discards held write address, held write data and pending responses | **PASS** | test_chk_035_reset_discards_held_state; verified in base.s1, base.s2, max.s1, max.s2, full_a7.s1 |
| CHK-036 | test | Valids held at 1 through reset become new requests after R1 | **PASS** | test_chk_036_valids_through_reset; verified in base.s1, base.s2, min.s1, min.s2, max.s1, max.s2, full_a7.s1 |
| CHK-037 | test | No combinational input-to-output path; readies do not wait for valids | **PASS** | test_chk_037_no_combinational_path; verified in base.s1, base.s2, min.s1, min.s2, max.s1, max.s2, full_a7.s1 |

## Requirement traceability (RTM)

| Rule | Spec ref | Statement | Checks | Mutation | Status |
|---|---|---|---|---|---|
| RF-1.1-01 |  | The block provides PARA_NUM_REGS 32-bit read/write control registers and one 32-bit read-only status register. | CHK-027:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-1.1-03 |  | The current value of every read/write register drives o_regs directly. | CHK-012:PASS, CHK-027:PASS | — | **VERIFIED** |
| RF-1.1-04 |  | A read of the status register at byte address 0x40 returns the SoC status word i_status. | CHK-005:PASS, CHK-028:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-1.2-01 |  | The block implements 1 to 16 read/write registers at byte addresses 0x00 + 4k. | CHK-027:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-1.2-02 |  | Each read/write register resets to 0. | CHK-014:PASS, CHK-033:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-1.2-03 |  | Byte-lane writes are controlled by i_s_axi_wstrb. | CHK-012:PASS, CHK-032:PASS | 100.0 % (4/4) | **VERIFIED** |
| RF-1.2-04 |  | The status read returns i_status as sampled when the read address is taken. | CHK-005:PASS, CHK-028:PASS | — | **VERIFIED** |
| RF-1.2-05 |  | An access to an unmapped address answers SLVERR. | CHK-011:PASS, CHK-029:PASS | — | **VERIFIED** |
| RF-1.2-06 |  | An unmapped read returns 0. | CHK-005:PASS, CHK-029:PASS | — | **VERIFIED** |
| RF-1.2-07 |  | The write address and the write data may arrive in either order or at the same edge, and the block must accept all. | CHK-019:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-1.2-08 |  | A read and a write may be in progress at the same time, as the read and write paths work independently. | CHK-024:PASS, CHK-026:PASS | — | **VERIFIED** |
| RF-1.2-09 |  | The write response comes one cycle after the last write handshake, and the read data one cycle after the read address handshake. | CHK-002:PASS, CHK-008:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-1.2-10 |  | Every output is registered, with no combinational path from any input to any output. | CHK-017:PASS, CHK-037:PASS | — | **VERIFIED** |
| RF-1.2-11 |  | The block uses one clock and one active-low reset with asynchronous assertion. | CHK-033:PASS, CHK-034:PASS | — | **VERIFIED** |
| RF-1.3-01 |  | The block never produces response codes EXOKAY (2'b01) or DECERR (2'b11). | CHK-004:PASS, CHK-010:PASS | — | **VERIFIED** |
| RF-1.3-02 |  | i_s_axi_awprot and i_s_axi_arprot are ignored. | CHK-031:PASS | — | **VERIFIED** |
| RF-1.3-03 |  | Address bits [1:0] are ignored and no unaligned-access error is produced. | CHK-031:PASS | — | **VERIFIED** |
| RF-3-01 |  | A transfer occurs at a rising edge of i_clk when valid and ready of a channel are both 1 and i_rst_n is 1; the payload is taken at that edge. | CHK-013:PASS | — | **VERIFIED** |
| RF-3-02 |  | A value required 'from edge n' holds starting in cycle n+1 until another requirement changes it, such as a held state ending or a reset. | not verified: covered_by_other_check | — | **NOT_VERIFIED_BY_SIM** |
| RF-3-03 | REQ-RST-009 | A write address, write data or read address is held in cycle n if its transfer occurred at an edge <= n-1, its B or R transfer has not occurred, and i_rst_n has not been 0 since; reset ends the held state. | CHK-001:PASS, CHK-006:PASS, CHK-007:PASS, CHK-035:PASS | — | **VERIFIED** |
| RF-4-01 |  | PARA_NUM_REGS sets the number of read/write registers, default 8, with legal values 1 to 16. | CHK-027:PASS | — | **VERIFIED** |
| RF-4-02 |  | PARA_ADDR_W sets the width in bits of i_s_axi_awaddr and i_s_axi_araddr, default 8, legal values 7 to 16. | CHK-027:PASS | — | **VERIFIED** |
| RF-4-04 | REQ-PAR-001 | The block must behave as the specification states for every legal combination of PARA_NUM_REGS (1 to 16) and PARA_ADDR_W (7 to 16). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RF-4-05 | REQ-PAR-002 | LPARA_REGS_W shall be a local parameter equal to PARA_NUM_REGS*32 that cannot be overridden from outside the module. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RF-4-06 | REQ-PAR-003 | The RTL should stop elaboration with an error message when PARA_NUM_REGS or PARA_ADDR_W is outside its legal range. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RF-4-07 | REQ-PAR-004 | Behaviour with illegal parameter values is unspecified and must not be verified. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RF-5-01 | REQ-IF-003 | Byte lane i of a register must be bits 8i+7..8i and correspond to i_s_axi_wdata[8i+7:8i] and o_s_axi_rdata[8i+7:8i]. | CHK-012:PASS, CHK-032:PASS | — | **VERIFIED** |
| RF-5-02 | REQ-IF-003 | Byte lane i of a register must be enabled by i_s_axi_wstrb[i]. | CHK-012:PASS, CHK-032:PASS | 100.0 % (4/4) | **VERIFIED** |
| RF-5-03 | REQ-IF-002 | Bits 32k+31..32k of o_regs must carry the current value of read/write register k. | CHK-012:PASS, CHK-027:PASS | — | **VERIFIED** |
| RF-5-04 | REQ-IF-001 | Every output must change value only at a rising edge of i_clk or when i_rst_n is asserted. | CHK-017:PASS, CHK-037:PASS | — | **VERIFIED** |
| RF-5-06 | REQ-IF-004 | The values of i_s_axi_awprot and i_s_axi_arprot must have no effect on any output. | CHK-031:PASS | — | **VERIFIED** |
| RF-6.1-01 | REQ-CLK-001 | Every flip-flop of the block shall be clocked by the rising edge of i_clk. | CHK-017:PASS, CHK-037:PASS | — | **VERIFIED** |
| RF-6.2-01 | REQ-RST-004 | Every output shall take its reset value asynchronously, without waiting for a rising edge of i_clk. | CHK-034:PASS | 100.0 % (7/7) | **VERIFIED** |
| RF-6.2-02 | REQ-RST-001 | o_s_axi_awready, o_s_axi_wready, o_s_axi_arready, o_s_axi_bvalid and o_s_axi_rvalid shall be 0. | CHK-013:PASS | 100.0 % (7/7) | **VERIFIED** |
| RF-6.2-03 | REQ-RST-002 | o_s_axi_bresp, o_s_axi_rresp and o_s_axi_rdata shall be 0. | CHK-014:PASS | 100.0 % (2/2) | **VERIFIED** |
| RF-6.2-04 | REQ-RST-003 | Every bit of o_regs shall be 0. | CHK-014:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-6.2-05 | REQ-RST-005 | No transfer shall happen on any channel, whatever the values of the valid and ready inputs. | CHK-013:PASS, CHK-036:PASS | 100.0 % (3/3) | **VERIFIED** |
| RF-6.2-06 | REQ-RST-006 | No transfer shall happen on any channel at R1, because the ready outputs and bvalid/rvalid are 0 in the cycle ending at R1. | CHK-015:PASS | 100.0 % (5/5) | **VERIFIED** |
| RF-6.2-07 | REQ-RST-007 | o_s_axi_awready, o_s_axi_wready and o_s_axi_arready shall be 1. | CHK-016:PASS, CHK-033:PASS | 100.0 % (2/2) | **VERIFIED** |
| RF-6.2-08 | REQ-RST-008 | o_s_axi_bvalid and o_s_axi_rvalid shall stay 0. | CHK-002:PASS, CHK-008:PASS, CHK-033:PASS | 100.0 % (2/2) | **VERIFIED** |
| RF-6.2-09 | REQ-RST-009 | The held state shall be discarded. | CHK-035:PASS | 100.0 % (4/4) | **VERIFIED** |
| RF-6.2-10 |  | No B or R response shall be given for that transaction, and no register shall be written by it. | CHK-002:PASS, CHK-008:PASS, CHK-035:PASS | 100.0 % (2/2) | **VERIFIED** |
| RF-6.2-11 | REQ-RST-010 | It shall be treated as a new transfer request, taken at the first edge after R1 where the matching ready is 1. | CHK-036:PASS | — | **VERIFIED** |
| RF-7.1-01 | REQ-DEC-001 | Bits [1:0] of i_s_axi_awaddr and i_s_axi_araddr must have no effect on any output. | CHK-031:PASS | — | **VERIFIED** |
| RF-7.1-02 | REQ-DEC-002 | An address with word index k selects read/write register k. | CHK-005:PASS, CHK-011:PASS, CHK-027:PASS | 100.0 % (3/3) | **VERIFIED** |
| RF-7.1-03 | REQ-DEC-003 | The address selects the status register. | CHK-005:PASS, CHK-011:PASS, CHK-028:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-7.1-04 | REQ-DEC-004 | Every other address is unmapped. | CHK-005:PASS, CHK-011:PASS, CHK-029:PASS | — | **VERIFIED** |
| RF-7.1-05 | REQ-DEC-005 | Decode compares all address bits [PARA_ADDR_W-1:2] so no register or status register appears at more than one word index (no aliasing). | CHK-005:PASS, CHK-011:PASS, CHK-027:PASS, CHK-029:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-7.1-06 | REQ-DEC-006 | A write transaction is decoded from the address taken at its AW transfer. | CHK-011:PASS, CHK-012:PASS, CHK-019:PASS | 100.0 % (2/2) | **VERIFIED** |
| RF-7.1-07 | REQ-DEC-007 | A read transaction is decoded from the address taken at its AR transfer. | CHK-005:PASS | — | **VERIFIED** |
| RF-7.2-01 | REQ-WR-001 | o_s_axi_awready shall be 1. | CHK-006:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-7.2-02 | REQ-WR-002 | o_s_axi_awready shall be 0. | CHK-006:PASS | — | **VERIFIED** |
| RF-7.2-03 | REQ-WR-003 | o_s_axi_wready shall be 1. | CHK-007:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-7.2-04 | REQ-WR-004 | o_s_axi_wready shall be 0. | CHK-007:PASS | — | **VERIFIED** |
| RF-7.2-05 | REQ-WR-005 | The block takes the AW and W transfers in either order or at the same edge. | CHK-019:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-7.2-06 | REQ-WR-005 | The block shall not answer a write transaction before it has taken both AW and W transfers. | CHK-008:PASS, CHK-019:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-7.2-07 | REQ-WR-006 | The block shall take no other AW transfer. | CHK-006:PASS, CHK-020:PASS | — | **VERIFIED** |
| RF-7.2-08 | REQ-WR-007 | The block shall take no other W transfer. | CHK-007:PASS, CHK-020:PASS | — | **VERIFIED** |
| RF-7.2-09 | REQ-WR-008 | The strobes and data used are the values of i_s_axi_wstrb and i_s_axi_wdata taken at the W transfer. | CHK-012:PASS, CHK-019:PASS, CHK-032:PASS | 100.0 % (3/3) | **VERIFIED** |
| RF-7.3-01 | REQ-WR-010 | Bits 8i+7..8i of register k take the value of the same bits of the write data taken at Ew. | CHK-012:PASS, CHK-032:PASS | 100.0 % (9/9) | **VERIFIED** |
| RF-7.3-02 | REQ-WR-011 | Byte lanes of register k whose strobe bit is 0 keep their value. | CHK-012:PASS, CHK-032:PASS | 100.0 % (6/6) | **VERIFIED** |
| RF-7.3-03 | REQ-WR-012 | The written value appears on o_regs[32k+31:32k] from edge Ec, in the cycle starting at Ec. | CHK-012:PASS, CHK-019:PASS | — | **VERIFIED** |
| RF-7.3-04 | REQ-WR-013 | A write shall change no bit of o_regs outside bits 32k+31..32k. | CHK-012:PASS, CHK-032:PASS | 100.0 % (2/2) | **VERIFIED** |
| RF-7.3-05 | REQ-WR-014 | A write changes its register only at its edge Ec and only once. | CHK-012:PASS, CHK-019:PASS | 100.0 % (3/3) | **VERIFIED** |
| RF-7.3-06 | REQ-WR-015 | The write shall change no bit of o_regs. | CHK-012:PASS, CHK-028:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-7.3-07 | REQ-WR-016 | The write shall change no bit of o_regs. | CHK-012:PASS, CHK-029:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-7.3-08 | REQ-WR-017 | The write changes no bit of o_regs and answers OKAY. | CHK-011:PASS, CHK-012:PASS, CHK-032:PASS | — | **VERIFIED** |
| RF-7.3-09 | REQ-WR-018 | Bits of o_regs shall not change. | CHK-012:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-7.4-01 | REQ-WR-020 | o_s_axi_bvalid shall be 1 in the cycle starting at Ec. | CHK-008:PASS | 100.0 % (2/2) | **VERIFIED** |
| RF-7.4-02 | REQ-WR-021 | o_s_axi_bvalid stays 1 and o_s_axi_bresp stays unchanged. | CHK-009:PASS, CHK-020:PASS | — | **VERIFIED** |
| RF-7.4-03 | REQ-WR-022 | o_s_axi_bvalid shall be 0. | CHK-008:PASS | 100.0 % (3/3) | **VERIFIED** |
| RF-7.4-04 | REQ-WR-023 | The block gives exactly one B transfer per write transaction. | CHK-008:PASS | 100.0 % (4/4) | **VERIFIED** |
| RF-7.4-05 | REQ-WR-023 | o_s_axi_bvalid shall be 0. | CHK-008:PASS | 100.0 % (3/3) | **VERIFIED** |
| RF-7.4-06 | REQ-WR-024 | o_s_axi_bresp shall be 2'b00 (OKAY). | CHK-011:PASS, CHK-028:PASS | 100.0 % (2/2) | **VERIFIED** |
| RF-7.4-07 | REQ-WR-025 | o_s_axi_bresp shall be 2'b10 (SLVERR). | CHK-011:PASS, CHK-029:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-7.4-08 | REQ-WR-026 | o_s_axi_bresp shall never be 2'b01 or 2'b11. | CHK-010:PASS | — | **VERIFIED** |
| RF-7.4-09 | REQ-WR-027 | The value of o_s_axi_bresp is unspecified and shall not be checked. | CHK-011:PASS | — | **VERIFIED** |
| RF-7.5-01 | REQ-RD-001 | o_s_axi_arready shall be 1. | CHK-001:PASS | — | **VERIFIED** |
| RF-7.5-02 | REQ-RD-002 | o_s_axi_arready shall be 0. | CHK-001:PASS | — | **VERIFIED** |
| RF-7.5-03 | REQ-RD-003 | The block shall take no other AR transfer. | CHK-001:PASS, CHK-018:PASS | — | **VERIFIED** |
| RF-7.5-04 | REQ-RD-004 | o_s_axi_rvalid shall be 1 in the cycle starting at Ear. | CHK-002:PASS | — | **VERIFIED** |
| RF-7.5-05 | REQ-RD-005 | o_s_axi_rvalid stays 1 and o_s_axi_rdata and o_s_axi_rresp stay unchanged. | CHK-003:PASS, CHK-018:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-7.5-06 | REQ-RD-006 | o_s_axi_rvalid shall be 0. | CHK-002:PASS | — | **VERIFIED** |
| RF-7.5-07 | REQ-RD-007 | The block gives exactly one R transfer for each AR transfer. | CHK-002:PASS | — | **VERIFIED** |
| RF-7.5-08 | REQ-RD-007 | o_s_axi_rvalid shall be 0. | CHK-002:PASS | — | **VERIFIED** |
| RF-7.5-09 | REQ-RD-008 | o_s_axi_rdata equals o_regs[32k+31:32k] in the cycle ending at Ear. | CHK-005:PASS | 100.0 % (2/2) | **VERIFIED** |
| RF-7.5-10 | REQ-RD-009 | o_s_axi_rdata equals i_status in the cycle ending at Ear. | CHK-005:PASS, CHK-028:PASS | 100.0 % (2/2) | **VERIFIED** |
| RF-7.5-11 | REQ-RD-010 | The change shall not alter o_s_axi_rdata. | CHK-003:PASS, CHK-028:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-7.5-12 | REQ-RD-011 | o_s_axi_rresp shall be 2'b00 (OKAY). | CHK-005:PASS | — | **VERIFIED** |
| RF-7.5-13 | REQ-RD-012 | o_s_axi_rdata shall be 32'h0000_0000 and o_s_axi_rresp shall be 2'b10 (SLVERR). | CHK-005:PASS, CHK-029:PASS | — | **VERIFIED** |
| RF-7.5-14 | REQ-RD-013 | o_s_axi_rresp shall never be 2'b01 or 2'b11. | CHK-004:PASS | — | **VERIFIED** |
| RF-7.5-15 | REQ-RD-014 | Values of o_s_axi_rdata and o_s_axi_rresp are unspecified and shall not be checked. | CHK-005:PASS | — | **VERIFIED** |
| RF-7.5-16 | REQ-RD-015 | A read shall change no bit of o_regs. | CHK-012:PASS | — | **VERIFIED** |
| RF-7.6-01 | REQ-CC-001, REQ-CC-003, REQ-CC-006 | AR and R channels work independently of AW, W and B: value and timing of arready, rvalid, rdata, rresp are unchanged, except register value per REQ-CC-003 to 006. | CHK-005:PASS, CHK-024:PASS, CHK-025:PASS, CHK-026:PASS | — | **VERIFIED** |
| RF-7.6-02 | REQ-CC-002 | The value and timing of awready, wready, bvalid, bresp and o_regs shall not change. | CHK-012:PASS, CHK-024:PASS, CHK-026:PASS | — | **VERIFIED** |
| RF-7.6-03 | REQ-CC-003 | The read returns the old value of register k before that write. | CHK-005:PASS, CHK-025:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-7.6-04 | REQ-CC-004 | The read returns the value written, unless another write to k with Ec before Ear came in between. | CHK-005:PASS, CHK-025:PASS | — | **VERIFIED** |
| RF-7.6-05 | REQ-CC-005 | The write shall not change o_s_axi_rdata of the read. | CHK-003:PASS, CHK-025:PASS | — | **VERIFIED** |
| RF-7.6-06 | REQ-CC-006 | Read data equals one whole value register k held in the cycle ending at Ear, never a mix of bytes of two values. | CHK-005:PASS, CHK-025:PASS | — | **VERIFIED** |
| RF-8.1-01 | REQ-TIM-001 | The block completes one write transaction every 2 cycles: AW and W transfers at edge n, B transfer at edge n+1, next AW and W at edge n+2. | CHK-024:PASS | — | **VERIFIED** |
| RF-8.1-02 | REQ-TIM-002 | The block completes one read transaction every 2 cycles: AR transfer at edge n, R transfer at edge n+1, next AR at edge n+2. | CHK-024:PASS | — | **VERIFIED** |
| RF-8.1-03 | REQ-RD-001, REQ-TIM-003, REQ-WR-001, REQ-WR-003 | The block's readies must not wait for the matching valid; o_s_axi_awready, o_s_axi_wready and o_s_axi_arready are 1 as REQ-WR-001, REQ-WR-003 and REQ-RD-001 say, regardless of the valids. | CHK-001:PASS, CHK-006:PASS, CHK-007:PASS, CHK-037:PASS | — | **VERIFIED** |
| RF-8.2-01 | REQ-TIM-010 | The block keeps the write response pending for any number of cycles while i_s_axi_bready is 0. | CHK-009:PASS, CHK-020:PASS | 100.0 % (2/2) | **VERIFIED** |
| RF-8.2-02 | REQ-TIM-010 | The block takes no new AW or W transfer while the B response is pending and i_s_axi_bready is 0. | CHK-006:PASS, CHK-007:PASS, CHK-020:PASS | — | **VERIFIED** |
| RF-8.2-03 | REQ-TIM-011 | The block keeps the read data pending for any number of cycles while i_s_axi_rready is 0. | CHK-003:PASS, CHK-018:PASS | — | **VERIFIED** |
| RF-8.2-04 | REQ-TIM-011 | The block takes no new AR transfer while read data is pending and i_s_axi_rready is 0. | CHK-001:PASS, CHK-018:PASS | — | **VERIFIED** |
| RF-8.2-05 | REQ-TIM-012 | Back-pressure on the B channel must not stall the AR or R channel. | CHK-026:PASS | — | **VERIFIED** |
| RF-8.2-06 | REQ-TIM-012 | Back-pressure on the R channel must not stall the AW, W or B channel. | CHK-026:PASS | — | **VERIFIED** |
| RF-8.2-07 | REQ-TIM-013 | The block answers write transactions in the order of their Ec and read transactions in the order of their Ear. | CHK-025:PASS | — | **VERIFIED** |
| RF-9-01 |  | REG_k VALUE (bits 31:0, RW) shall reset to 0x0000_0000, so o_regs[32k+31:32k] is 0 after reset. | CHK-014:PASS, CHK-033:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-9-02 |  | o_regs[32k+31:32k] shall be driven by the current value of REG_k. | CHK-012:PASS, CHK-027:PASS | — | **VERIFIED** |
| RF-9-03 |  | Each byte lane of REG_k shall be written only when the corresponding i_s_axi_wstrb bit is set; other byte lanes shall keep their value. | CHK-012:PASS, CHK-032:PASS | 100.0 % (4/4) | **VERIFIED** |
| RF-9-04 |  | A read of REG_k shall return the current register value with OKAY response. | CHK-005:PASS, CHK-027:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-9-05 |  | A read of STATUS shall return i_status sampled at Ear, with OKAY response. | CHK-005:PASS, CHK-028:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-9-06 |  | A write to STATUS shall change nothing and answer OKAY. | CHK-011:PASS, CHK-012:PASS, CHK-028:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-9-07 |  | A read of the unmapped region below STATUS shall return 0 with SLVERR. | CHK-005:PASS, CHK-029:PASS | — | **VERIFIED** |
| RF-9-08 |  | A write to the unmapped region below STATUS shall change nothing and answer SLVERR. | CHK-011:PASS, CHK-012:PASS, CHK-029:PASS | — | **VERIFIED** |
| RF-9-09 |  | The reserved region from 4*PARA_NUM_REGS to 0x3C shall not exist when PARA_NUM_REGS is 16. | CHK-022:PASS | — | **VERIFIED** |
| RF-9-10 |  | A read of the unmapped region above STATUS shall return 0 with SLVERR. | CHK-005:PASS, CHK-029:PASS | — | **VERIFIED** |
| RF-9-11 |  | A write to the unmapped region above STATUS shall change nothing and answer SLVERR. | CHK-011:PASS, CHK-012:PASS, CHK-029:PASS | — | **VERIFIED** |
| RF-9-12 |  | Address bits [1:0] shall be ignored when decoding register offsets. | CHK-005:PASS, CHK-011:PASS, CHK-031:PASS | — | **VERIFIED** |
| RF-9-13 | REQ-REG-001 | The register map shall match the table exactly for every legal PARA_NUM_REGS and PARA_ADDR_W combination. | CHK-027:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-10.1-01 | REQ-ERR-001 | A write to an unmapped address, detected by decoding the address taken at Ea, must change no register and answer o_s_axi_bresp = 2'b10 (SLVERR) with normal write timing. | CHK-011:PASS, CHK-012:PASS, CHK-029:PASS | — | **VERIFIED** |
| RF-10.1-02 | REQ-ERR-002 | A read from an unmapped address, detected by decoding the address taken at Ear, must return o_s_axi_rdata = 0 and o_s_axi_rresp = 2'b10 (SLVERR) with normal read timing. | CHK-005:PASS, CHK-029:PASS | — | **VERIFIED** |
| RF-10.1-03 | REQ-ERR-003 | A write to the status register must change no register, not affect later status reads other than through i_status, and answer OKAY, for every i_s_axi_wstrb value. | CHK-012:PASS, CHK-028:PASS | — | **VERIFIED** |
| RF-10.1-04 | REQ-ERR-004 | A write with i_s_axi_wstrb = 4'b0000 must answer as a write with strobes to the same address (OKAY for register or status, SLVERR for unmapped) and change no register. | CHK-011:PASS, CHK-012:PASS, CHK-032:PASS | — | **VERIFIED** |
| RF-10.1-05 | REQ-ERR-005 | An address with bits [1:0] not equal to 2'b00 must not be treated as an error. | CHK-031:PASS | — | **VERIFIED** |
| RF-10.1-06 |  | An access with unaligned address bits [1:0] must access the aligned word given by its word index. | CHK-031:PASS | — | **VERIFIED** |
| RF-10.1-07 | REQ-ERR-006 | Any value of i_s_axi_awprot or i_s_axi_arprot must be accepted without error and without effect. | CHK-031:PASS | — | **VERIFIED** |
| RF-10.1-08 | REQ-ERR-007 | An unmapped access must not stall or change the state of the other channels. | CHK-030:PASS | — | **VERIFIED** |
| RF-10.1-09 |  | The next transaction must behave as if the unmapped access had targeted a mapped address. | CHK-030:PASS | — | **VERIFIED** |
| RF-10.1-10 | REQ-ERR-008, REQ-RST-005 | A valid input at 1 while i_rst_n is 0 must have no effect (REQ-RST-005). | CHK-013:PASS, CHK-036:PASS | — | **VERIFIED** |
| RF-10.2-01 | REQ-EXT-001 | Only 0x00 (REG_0) and 0x40 (STATUS) are mapped, o_regs is 32 bits wide, and 0x04 to 0x3C are unmapped. | CHK-021:PASS | — | **VERIFIED** |
| RF-10.2-02 | REQ-EXT-002 | 0x00 to 0x3C are REG_0 to REG_15, 0x40 is STATUS, o_regs is 512 bits wide, and no address below 0x44 is unmapped. | CHK-022:PASS | — | **VERIFIED** |
| RF-10.2-03 | REQ-EXT-003 | The address space is 0x00 to 0x7F and addresses 0x44 to 0x7C are unmapped. | CHK-021:PASS | — | **VERIFIED** |
| RF-10.2-04 | REQ-EXT-004 | Every address with a 1 in any bit from 15 to 7 (e.g. 0x0080, 0x0100, 0x8040, 0xFFFC) is unmapped. | CHK-023:PASS | — | **VERIFIED** |
| RF-10.2-05 | REQ-EXT-005 | Latency, throughput, reset and back-pressure behaviour must be the same for every legal parameter combination. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RF-11-01 |  | CFG-BASE uses PARA_NUM_REGS=8 and PARA_ADDR_W=8 as default and must cover the gap of unmapped addresses 0x20 to 0x3C. | CHK-029:PASS | — | **VERIFIED** |
| RF-11-02 |  | CFG-MIN must be verified with PARA_NUM_REGS=1 and PARA_ADDR_W=7, the smallest legal configuration. | CHK-021:PASS | — | **VERIFIED** |
| RF-11-03 |  | CFG-MAX must be verified with PARA_NUM_REGS=16 and PARA_ADDR_W=16, including aliasing checks with high address bits. | CHK-023:PASS | — | **VERIFIED** |
| RF-11-04 |  | CFG-FULL-A7 uses PARA_NUM_REGS=16 and PARA_ADDR_W=7, a full register bank with the narrowest address bus and no unmapped address below 0x44. | CHK-022:PASS | — | **VERIFIED** |
| RF-11-05 |  | The verification must run every configuration listed in the Configurations table (CFG-BASE, CFG-MIN, CFG-MAX, CFG-FULL-A7), as defined in run_set.json. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RF-12.1-01 | REQ-VER-001 | The manager shall keep valid at 1 and its payload stable from the cycle it rises until the edge of its transfer. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RF-12.1-02 | REQ-VER-002 | The manager may hold i_s_axi_bready and i_s_axi_rready at 0 for any number of cycles, drive them at 1 before the matching valid, and make them depend on the valid. | CHK-018:PASS, CHK-020:PASS | — | **VERIFIED** |
| RF-12.1-03 | REQ-VER-003 | The environment shall release i_rst_n synchronously to i_clk so that the release meets recovery and removal times of the flip-flops. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RF-12.1-05 | REQ-VER-004 | The environment shall drive i_status synchronously to i_clk, changing it only away from rising edges. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RF-12.1-06 | REQ-VER-005 | The testbench shall drive defined values (no X or Z) on all inputs. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RF-12.1-07 |  | The valids may be 0 or 1 during reset. | CHK-036:PASS | — | **VERIFIED** |
| RF-12.1-08 | REQ-VER-006 | The environment shall drive i_rst_n = 0 from time zero, before the first rising edge of i_clk, for at least 2 cycles. | CHK-033:PASS | — | **VERIFIED** |
| RF-12.1-09 | REQ-VER-010 | No output check applies, including REQ-VER-010, before the first assertion of i_rst_n, as outputs are undefined. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RF-12.1-10 | REQ-VER-001, REQ-VER-007 | A reset assertion ends the REQ-VER-001 obligation; the manager may drop that valid or change its payload. | CHK-036:PASS | — | **VERIFIED** |
| RF-12.1-11 | REQ-RST-010, REQ-VER-001 | A valid at 1 after R1 is a new request and carries the REQ-VER-001 obligation from that cycle. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| RF-12.2-02 |  | A reference model shall predict o_regs and the next value of every handshake output. | CHK-012:PASS | — | **VERIFIED** |
| RF-12.2-03 | REQ-VER-010 | The checker shall compare o_regs with the reference model in every cycle, not only after B transfers. | CHK-012:PASS | — | **VERIFIED** |
| RF-12.2-04 | REQ-RD-014, REQ-RST-002, REQ-VER-011, REQ-WR-027 | The checker shall compare o_s_axi_rdata and o_s_axi_rresp only when o_s_axi_rvalid is 1 or i_rst_n is 0, and o_s_axi_bresp only when o_s_axi_bvalid is 1 or i_rst_n is 0. | CHK-005:PASS, CHK-011:PASS, CHK-014:PASS | — | **VERIFIED** |
| RF-12.2-05 | REQ-VER-012 | A protocol checker shall verify o_s_axi_bvalid and o_s_axi_rvalid stay 1 with stable payload until transfer, and no response code is 2'b01 or 2'b11. | CHK-003:PASS, CHK-004:PASS, CHK-009:PASS, CHK-010:PASS | — | **VERIFIED** |
| RF-12.3-01 | REQ-IF-001, REQ-VER-020 | The testbench shall change inputs between rising edges, e.g. at the falling edge, and check no output changes before the next rising edge. | CHK-037:PASS | — | **VERIFIED** |
| RF-12.3-02 | REQ-RST-004, REQ-VER-021 | The testbench shall assert i_rst_n between rising edges while transactions are in progress and check reset values before the next rising edge. | CHK-034:PASS | — | **VERIFIED** |
| RF-12.4-01 | REQ-VER-030 | All 16 values of i_s_axi_wstrb shall be applied, with data differing from the old value in every byte. | CHK-032:PASS | — | **VERIFIED** |
| RF-12.4-02 | REQ-VER-031 | Writes shall be run with address before data (gaps of 1 and 4+ cycles), data before address (same gaps), and both at the same edge. | CHK-019:PASS | — | **VERIFIED** |
| RF-12.4-03 | REQ-VER-032 | The B channel shall be run with i_s_axi_bready delays of 0, 1 and 4 or more cycles, including i_s_axi_bready at 1 before o_s_axi_bvalid rises. | CHK-020:PASS | — | **VERIFIED** |
| RF-12.4-04 | REQ-VER-033 | The R channel shall be run with i_s_axi_rready delays of 0, 1 and 4 or more cycles, including i_s_axi_rready at 1 before o_s_axi_rvalid rises. | CHK-018:PASS | — | **VERIFIED** |
| RF-12.4-05 | REQ-TIM-010, REQ-TIM-011, REQ-VER-034 | New AW, W and AR valids shall be presented to check they are not taken (REQ-TIM-010, REQ-TIM-011). | CHK-018:PASS, CHK-020:PASS | — | **VERIFIED** |
| RF-12.4-06 | REQ-VER-035 | Every mapped register shall be written with a unique value and read back to detect decode aliasing. | CHK-027:PASS | — | **VERIFIED** |
| RF-12.4-07 | REQ-VER-036 | The status register shall be read while i_status changes around Ear and during R back-pressure, and written with several strobe values. | CHK-028:PASS | — | **VERIFIED** |
| RF-12.4-08 | REQ-VER-037 | Unmapped addresses shall be accessed: word indexes PARA_NUM_REGS to 15, 0x44, the highest bus address, and mapped address plus a 1 in bit 7 to PARA_ADDR_W-1 when PARA_ADDR_W > 7. | CHK-029:PASS | — | **VERIFIED** |
| RF-12.4-09 | REQ-VER-038 | Addresses with bits [1:0] not 2'b00 and random i_s_axi_awprot and i_s_axi_arprot values shall be applied. | CHK-031:PASS | — | **VERIFIED** |
| RF-12.4-10 | REQ-VER-039 | A read and a write of the same register shall run with Ear at Ec-1, Ec and Ec+1, and reads and writes of different registers shall run simultaneously. | CHK-025:PASS | — | **VERIFIED** |
| RF-12.4-11 | REQ-VER-040 | Reset shall be asserted with only write address held, only write data held, B response pending, R response pending, and with valids held at 1 through reset. | CHK-035:PASS, CHK-036:PASS | — | **VERIFIED** |
| RF-12.4-12 | REQ-TIM-001, REQ-TIM-002, REQ-VER-041 | Back-to-back writes and reads at full throughput of REQ-TIM-001 and REQ-TIM-002 shall be run, alone and at the same time. | CHK-024:PASS | — | **VERIFIED** |
| RF-13-01 | REQ-IMP-001 | The block shall meet timing at 50 MHz (20 ns clock period) in the GF180MCU technology at the worst-case corner of the sign-off flow. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RF-13-02 | REQ-IMP-002 | The RTL shall follow the coding rules in docs/RTL_RULES.md (REF-002). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RF-13-03 | REQ-IMP-003 | The RTL shall be synthesizable. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RF-13-04 | REQ-IMP-003 | The RTL shall use the single clock i_clk with no clock gating and no latches. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RF-13-05 | REQ-IMP-003 | The RTL shall not rely on initial values. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RF-13-06 | REQ-IMP-004 | Every flip-flop that drives an output or holds transaction state shall be reset asynchronously by i_rst_n to the value giving the reset values of section 5. | CHK-034:PASS | — | **VERIFIED** |
| RF-13-07 | REQ-IF-001, REQ-IMP-005 | Every output shall be driven directly from a flip-flop. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RF-13-08 | REQ-IMP-006 | The RTL shall compile and simulate in Verilator without lint warnings in all configurations of section 11. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RF-13-09 |  | The block should use no more storage than PARA_NUM_REGS x 32 register bits plus flip-flops for held write address and data, read data, and handshake state. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| RF-14-01 | REQ-RST-001, REQ-RST-006, REQ-RST-007 | o_s_axi_awready, o_s_axi_wready and o_s_axi_arready must be 0 during reset and in the cycle that ends at R1, and 1 from R1. | CHK-013:PASS, CHK-015:PASS, CHK-016:PASS, CHK-033:PASS | 100.0 % (8/8) | **VERIFIED** |
| RF-14-02 | REQ-IF-001, REQ-TIM-003 | The readies must be registered and depend only on the held state, not on the valids. | CHK-037:PASS | — | **VERIFIED** |
| RF-14-03 | REQ-WR-020 | bvalid must be 1 from Ec, giving a write response latency of exactly 1 cycle. | CHK-008:PASS | 100.0 % (2/2) | **VERIFIED** |
| RF-14-04 | REQ-RD-004 | rvalid must be 1 from Ear, giving a read data latency of exactly 1 cycle. | CHK-002:PASS | — | **VERIFIED** |
| RF-14-05 | REQ-WR-010 | The register must be written at Ec, the later of the AW and W transfers. | CHK-012:PASS, CHK-019:PASS | — | **VERIFIED** |
| RF-14-06 | REQ-CC-003, REQ-CC-004 | The read must sample the register at Ear: a write at the same edge gives the old value, a write at an earlier Ec gives the new value. | CHK-005:PASS, CHK-025:PASS | — | **VERIFIED** |
| RF-14-07 | REQ-RD-009, REQ-RD-010 | i_status must be sampled at Ear and the sampled value held until Er. | CHK-005:PASS, CHK-028:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-14-08 | REQ-DEC-004, REQ-DEC-005 | Address bits [PARA_ADDR_W-1:2] must be fully decoded; any 1 above bit 6 makes the address unmapped. | CHK-005:PASS, CHK-011:PASS, CHK-029:PASS | 100.0 % (1/1) | **VERIFIED** |
| RF-14-09 | REQ-RD-014, REQ-RST-002, REQ-WR-027 | bresp, rresp and rdata must be 0 during reset; their values while valid is 0 outside reset are not specified or checked. | CHK-014:PASS | — | **VERIFIED** |
| RF-14-10 | REQ-RD-001, REQ-WR-001 | The readies must return to 1 in the cycle after the B or R transfer, with no combinational path from bready or rready. | CHK-001:PASS, CHK-006:PASS, CHK-007:PASS | 100.0 % (2/2) | **VERIFIED** |
| RF-14-11 | REQ-PAR-003, REQ-PAR-004 | The RTL should stop elaboration with an error on illegal parameter values. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| RF-14-12 |  | A reset must end every held state; "after R1" means the most recent R1. | CHK-006:PASS, CHK-035:PASS | 100.0 % (2/2) | **VERIFIED** |
| RF-14-13 | REQ-VER-006 | Reset must be applied from time zero for at least 2 cycles; outputs are undefined and unchecked before the first reset. | CHK-033:PASS | — | **VERIFIED** |
| RF-14-14 | REQ-VER-007 | Reset ends the obligation on a pending request; a valid after R1 must be treated as a new request. | CHK-035:PASS, CHK-036:PASS | — | **VERIFIED** |

## Mutants

| ID | File:line | Operator | Status | Caught by | Rules | Equivalent? |
|---|---|---|---|---|---|---|
| M01 | m_axil_regfile.sv:332 | negate_if | killed | CHK-013, test_chk_033_power_on_reset, test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpress | RF-6.2-02, RF-6.2-03, RF-6.2-01, RF-14-01, RF-6.2-09 |  |
| M02 | m_axil_regfile.sv:232 | one_to_zero | killed | test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpressure, test_chk_024_back_to_back, test_c | RF-7.4-01, RF-14-03, RF-1.2-09, RF-7.4-04, RF-7.2-06 |  |
| M03 | m_axil_regfile_dec.sv:41 | eq_to_ne | killed | test_chk_033_power_on_reset, test_chk_018_r_backpressure, test_chk_024_back_to_back, test_chk_027_map_and_aliasing, test | RF-7.1-03, RF-1.1-04, RF-9-05, RF-9-06, RF-7.5-10 |  |
| M04 | m_axil_regfile.sv:221 | zero_to_one | killed | test_chk_033_power_on_reset, test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpressure, test | RF-6.2-09, RF-14-12, RF-7.2-03, RF-6.2-07, RF-14-01 |  |
| M05 | m_axil_regfile_dec.sv:33 | zero_to_one | killed | CHK-012, test_chk_033_power_on_reset, test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpress | RF-7.1-05, RF-14-08, RF-7.1-02, RF-1.2-01, RF-9-13 |  |
| M06 | m_axil_regfile.sv:280 | eq_to_ne | killed | test_chk_018_r_backpressure, test_chk_024_back_to_back, test_chk_025_concurrent_same_register, test_chk_026_backpressure | RF-7.5-09, RF-9-04, RF-7.1-02, RF-7.6-03, RF-1.1-01 |  |
| M07 | m_axil_regfile.sv:292 | negate_if | killed | CHK-012, test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpressure, test_chk_024_back_to_bac | RF-5-02, RF-7.3-02, RF-9-03, RF-1.2-03, RF-7.3-01 |  |
| M08 | m_axil_regfile.sv:220 | zero_to_one | killed | test_chk_033_power_on_reset, test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpressure, test | RF-6.2-09, RF-14-12, RF-7.2-01, RF-6.2-07, RF-6.2-10 |  |
| M09 | m_axil_regfile.sv:279 | eq_to_ne | killed | CHK-012, test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpressure, test_chk_024_back_to_bac | RF-7.3-04, RF-7.3-05, RF-7.1-02, RF-7.3-09, RF-7.3-01 |  |
| M10 | m_axil_regfile.sv:219 | negate_if | killed | CHK-013, test_chk_033_power_on_reset, test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpress | RF-6.2-02, RF-6.2-01, RF-6.2-09, RF-14-01, RF-6.2-03 |  |
| M11 | m_axil_regfile.sv:245 | zero_to_one | survived |  |  | formal PROVEN (claimed: The reset value of r_aw_okay is only read through wr_okay when aw_hs=0, and that only matters when wr_commit=1, which needs r_aw_held=1. r_aw_held is only set a) |
| M12 | m_axil_regfile.sv:231 | negate_if | killed | test_chk_033_power_on_reset, test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpressure, test | RF-7.4-01, RF-7.4-03, RF-14-03, RF-7.4-04, RF-7.4-05 |  |
| M13 | m_axil_regfile.sv:223 | zero_to_one | killed | CHK-013, test_chk_033_power_on_reset, test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpress | RF-6.2-02, RF-14-01, RF-6.2-06, RF-6.2-05, RF-6.2-01 |  |
| M14 | m_axil_regfile.sv:250 | negate_if | killed | CHK-012, test_chk_019_write_ordering, test_chk_031_addr_lsb_and_prot_ignored, test_chk_035_reset_discards_held_state, te | RF-7.1-06, RF-7.2-09, RF-7.4-07, RF-7.4-06, RF-7.3-05 |  |
| M15 | m_axil_regfile.sv:244 | zero_to_one | survived |  |  | formal PROVEN (claimed: The reset value of r_aw_reg_hit is only used via wr_reg_hit when aw_hs=0, and then only with wr_commit=1, which needs r_aw_held=1. That state is only reached af) |
| M16 | m_axil_regfile.sv:289 | negate_if | killed | CHK-012, test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpressure, test_chk_024_back_to_bac | RF-5-02, RF-7.3-02, RF-9-03, RF-1.2-03, RF-7.3-01 |  |
| M17 | m_axil_regfile.sv:334 | zero_to_one | killed | CHK-013, test_chk_033_power_on_reset, test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpress | RF-6.2-02, RF-14-01, RF-6.2-06, RF-6.2-08, RF-6.2-01 |  |
| M18 | m_axil_regfile.sv:243 | negate_if | killed | CHK-012, test_chk_019_write_ordering, test_chk_031_addr_lsb_and_prot_ignored, test_chk_035_reset_discards_held_state, te | RF-7.2-09, RF-7.3-01, RF-7.1-06, RF-7.4-06, RF-7.3-02 |  |
| M19 | m_axil_regfile.sv:224 | zero_to_one | killed | CHK-013, test_chk_033_power_on_reset, test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpress | RF-6.2-02, RF-14-01, RF-6.2-06, RF-6.2-08, RF-6.2-10 |  |
| M20 | m_axil_regfile.sv:290 | negate_if | killed | CHK-012, test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpressure, test_chk_024_back_to_bac | RF-5-02, RF-7.3-02, RF-9-03, RF-1.2-03, RF-7.3-01 |  |
| M21 | m_axil_regfile.sv:222 | zero_to_one | killed | CHK-013, test_chk_033_power_on_reset, test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpress | RF-6.2-02, RF-14-01, RF-6.2-06, RF-6.2-05, RF-6.2-01 |  |
| M22 | m_axil_regfile.sv:286 | negate_if | killed | CHK-012, test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpressure, test_chk_024_back_to_bac | RF-6.2-04, RF-1.2-02, RF-9-01, RF-6.2-01, RF-7.3-01 |  |
| M23 | m_axil_regfile.sv:235 | zero_to_one | killed | test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpressure, test_chk_024_back_to_back, test_c | RF-7.4-03, RF-7.4-04, RF-14-10, RF-7.4-05, RF-8.2-01 |  |
| M24 | m_axil_regfile.sv:288 | negate_if | killed | CHK-012, test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpressure, test_chk_024_back_to_bac | RF-7.3-05, RF-7.3-04, RF-7.3-06, RF-7.3-07, RF-7.3-01 |  |
| M25 | m_axil_regfile.sv:333 | zero_to_one | killed | CHK-013, test_chk_033_power_on_reset, test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpress | RF-6.2-02, RF-14-01, RF-6.2-06, RF-6.2-05, RF-6.2-01 |  |
| M26 | m_axil_regfile.sv:340 | negate_if | killed | test_chk_033_power_on_reset, test_chk_018_r_backpressure, test_chk_024_back_to_back, test_chk_025_concurrent_same_regist | RF-7.5-09, RF-7.5-10, RF-7.5-11, RF-14-07, RF-7.5-05 |  |
| M27 | m_axil_regfile.sv:291 | negate_if | killed | CHK-012, test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_024_back_to_back, test_chk_025_concurrent_sa | RF-5-02, RF-7.3-02, RF-9-03, RF-1.2-03, RF-7.3-01 |  |
| M28 | m_axil_regfile.sv:234 | negate_if | killed | test_chk_018_r_backpressure, test_chk_019_write_ordering, test_chk_020_b_backpressure, test_chk_024_back_to_back, test_c | RF-7.4-03, RF-7.4-04, RF-14-10, RF-7.4-05, RF-8.2-01 |  |
| M29 | m_axil_regfile.sv:255 | negate_if | killed | CHK-012, test_chk_019_write_ordering, test_chk_031_addr_lsb_and_prot_ignored, test_chk_035_reset_discards_held_state, te | RF-7.2-09, RF-7.3-01, RF-7.2-05, RF-1.2-07, RF-7.3-02 |  |

## Not verified by this run

- Formal: the assertions were checked by SymbiYosys under the environment assumptions (work/formal.md); a BOUNDED result holds only up to its depth. CDC/RDC, STA, synthesis and DFT checks are outside this flow.
- Rules marked NOT_VERIFIED_BY_SIM carry the contract's reason (static, structural, not observable...).
- Only the configurations of the run set above were simulated; code coverage is merged over its runs, mutation testing used the primary run base.s1.

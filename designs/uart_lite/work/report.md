# Verification report — uart_lite

Generated 2026-11-20T05:08:46+00:00 by NNC Pipeline.

## Summary

| Item | Result |
|---|---|
| Rules | 154 — {'NOT_VERIFIED_BY_SIM': 22, 'VERIFIED': 132} |
| Checks | 32 — {'PASS': 32} |
| Tests | {'pass': 20} |
| Run set | 7 runs in 4 configurations (base, min, odd, wide); primary base.s1 |
| Integration | OK |
| Code coverage (RTL), line | 98.7 % (588/596 lines) |
| Code coverage (RTL), block | 97.3 % (144/148 statement blocks and branch arms) |
| Code coverage (RTL), expression | 100.0 % (152/152 condition terms) |
| Code coverage (RTL), toggle | 100.0 % (938/938 bit toggles 0->1 and 1->0) |
| Code coverage (RTL), functional | 97.5 % (39/40 cover points of the specification) |
| Mutation score | 97.2 % (35 killed / 1 survived / 0 not compiled) |
| Coverage target | not requested (`nnc cover <design> --target <n> --metric <m>`) |
| Formal (SymbiYosys, depth 64) | {'BOUNDED': 8, 'PROVEN': 4, 'UNSUPPORTED': 1} — reset assumptions + verif/formal/nnc_env.sv, work/formal.md |
| Triage | 6 failure(s), 6 analysed: work/triage.md |
| Agent cost | US$15.2195 in 43 calls (A0 0.7241, A1 0.4287, A12 0.3706, A13 0.1366, A15 0.9103, A2 0.3682, A3 0.1444, A4 1.0818, A5 0.2327, A6 0.4358, A7 8.6598, A9 1.7268); of which US$2.742 in 1 failed calls (usage limit, timeout, invalid answer) |

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
| Per-requirement mutation score >= 85 % | **not met** — 2 rule(s) below: UL-6.2-05, UL-6.2-12 |
| Formal: no counterexample, no vacuous or failed proof | met — {'BOUNDED': 8, 'PROVEN': 4, 'UNSUPPORTED': 1} (work/formal.md) |

## Run set

Every check is merged over these runs: PASS when one run verified it and no run failed it; NOT_VERIFIABLE only when every run declared it so.

| Run | Parameters changed | Defines | Plusargs | Status | Tests | Failing assertions | Not verifiable here |
|---|---|---|---|---|---|---|---|
| base.s1 — CFG-BASE | defaults | — | — | ran | {'pass': 20} | none | 3 |
| base.s2 — CFG-BASE | defaults | — | — | ran | {'pass': 20} | none | 3 |
| min.s1 — CFG-MIN | PARA_UART_CLKS_PER_BIT=4 | — | — | ran | {'pass': 20} | none | 2 |
| min.s2 — CFG-MIN | PARA_UART_CLKS_PER_BIT=4 | — | — | ran | {'pass': 20} | none | 2 |
| odd.s1 — CFG-ODD | PARA_UART_CLKS_PER_BIT=5 | — | — | ran | {'pass': 20} | none | 2 |
| odd.s2 — CFG-ODD | PARA_UART_CLKS_PER_BIT=5 | — | — | ran | {'pass': 20} | none | 2 |
| wide.s1 — CFG-WIDE | PARA_UART_CLKS_PER_BIT=1024 | — | — | ran | {'pass': 20} | none | 2 |

## Gates

| Gate | State | Detail |
|---|---|---|
| G1_rules | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-17T10:24:39+00:00 |
| G2_contract | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-17T10:30:57+00:00 |
| D1_config | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-17T10:30:58+00:00 |
| D2_rtl | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-18T19:24:52+00:00 |
| G3_verif_sources | APPROVED | by Claude (delegated by GabrielHCMUT) at 2026-11-18T17:16:30+00:00 |
| G4_signoff | PENDING | artifacts ready for review |

## Checks

| Check | Kind | Title | Status | Evidence |
|---|---|---|---|---|
| CHK-001 | assertion | Outputs change only at i_clk rising edges or reset assertion | **PASS** | hits 5335012, fails 0; hit in 7/7 runs; formal UNSUPPORTED |
| CHK-002 | assertion | Output values while reset is asserted, including immediately after asynchronous assertion | **PASS** | hits 1789, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-003 | assertion | Delivery into an empty holding register at V=M+2 | **PASS** | hits 4535, fails 0; hit in 7/7 runs; formal BOUNDED |
| CHK-004 | assertion | Held byte taken at the delivery edge itself loads the new byte, no overrun | **PASS** | hits 14, fails 0; hit in 7/7 runs; formal BOUNDED |
| CHK-005 | assertion | Overrun drop at V keeps the held byte; one-cycle pulse | **PASS** | hits 63, fails 0; hit in 7/7 runs; formal BOUNDED |
| CHK-006 | assertion | o_rx_overrun only after a drop edge, independent of o_rx_valid | **PASS** | hits 5334619, fails 0; hit in 7/7 runs; formal BOUNDED |
| CHK-007 | assertion | Consumer take empties the holding register | **PASS** | hits 4479, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-008 | assertion | Held byte is stable until taken | **PASS** | hits 1901815, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-009 | assertion | Empty register: i_rx_ready has no effect; data and flag keep the last loaded values | **PASS** | hits 3424106, fails 0; hit in 7/7 runs; formal BOUNDED |
| CHK-010 | assertion | Transmit handshake, acceptance condition and idle values | **PASS** | hits 4815904, fails 0; hit in 7/7 runs; formal BOUNDED |
| CHK-011 | assertion | Cycle-exact transmit frame content (8N1, LSB first, N cycles per bit) | **PASS** | hits 521261, fails 0; hit in 7/7 runs; formal BOUNDED |
| CHK-012 | assertion | o_tx_ready timing during a frame | **PASS** | hits 521261, fails 0; hit in 7/7 runs; formal BOUNDED |
| CHK-013 | assertion | No idle cycle between back-to-back frames; idle high after a frame | **PASS** | hits 2153, fails 0; hit in 7/7 runs; formal PROVEN |
| CHK-014 | test | CFG-MIN: PARA_UART_CLKS_PER_BIT=4 | **PASS** | test_chk_014_cfg_min; verified in min.s1, min.s2 |
| CHK-015 | test | CFG-ODD: PARA_UART_CLKS_PER_BIT=5 (H=floor(N/2)=2) | **PASS** | test_chk_015_cfg_odd; verified in odd.s1, odd.s2 |
| CHK-016 | test | CFG-WIDE: PARA_UART_CLKS_PER_BIT=1024 | **PASS** | test_chk_016_cfg_wide; verified in wide.s1 |
| CHK-017 | test | Full duplex: simultaneous and independent transmit and receive | **PASS** | test_chk_017_full_duplex; verified in base.s1, base.s2, min.s1, min.s2, odd.s1, odd.s2, wide.s1 |
| CHK-018 | test | Loopback o_txd to i_rxd through a half-cycle delay | **PASS** | test_chk_018_loopback; verified in base.s1, base.s2, min.s1, min.s2, odd.s1, odd.s2, wide.s1 |
| CHK-019 | test | Asynchronous reset mid transmit frame, mid receive frame and while a byte is held | **PASS** | test_chk_019_async_reset; verified in base.s1, base.s2, min.s1, min.s2, odd.s1, odd.s2, wide.s1 |
| CHK-020 | test | No activity during reset; idle transmitter and receiver after release | **PASS** | test_chk_020_reset_idle; verified in base.s1, base.s2, min.s1, min.s2, odd.s1, odd.s2, wide.s1 |
| CHK-021 | test | Line low at reset release is detected as a start bit | **PASS** | test_chk_021_low_at_release; verified in base.s1, base.s2, min.s1, min.s2, odd.s1, odd.s2, wide.s1 |
| CHK-022 | test | Basic receive of directed and random bytes with exact latency | **PASS** | test_chk_022_rx_basic; verified in base.s1, base.s2, min.s1, min.s2, odd.s1, odd.s2, wide.s1 |
| CHK-023 | test | Sampling-point test at the exact sampling edges | **PASS** | test_chk_014_cfg_min, test_chk_015_cfg_odd, test_chk_023_sampling_points; verified in base.s1, base.s2, min.s1, min.s2, odd.s1, odd.s2, wide.s1 |
| CHK-024 | test | Start-bit glitch rejection and restart after a glitch | **PASS** | test_chk_014_cfg_min, test_chk_015_cfg_odd, test_chk_024_glitch; verified in base.s1, base.s2, min.s1, min.s2, odd.s1, odd.s2, wide.s1 |
| CHK-025 | test | Back-to-back receive frames and a new start at M+1 | **PASS** | test_chk_014_cfg_min, test_chk_015_cfg_odd, test_chk_025_rx_back_to_back; verified in base.s1, base.s2, min.s1, min.s2, odd.s1, odd.s2, wide.s1 |
| CHK-026 | test | i_rx_ready held at 0, held at 1, random, and take at V | **PASS** | test_chk_014_cfg_min, test_chk_026_rx_ready; verified in base.s1, base.s2, min.s1, min.s2, odd.s1, odd.s2, wide.s1 |
| CHK-027 | test | Frame error with an empty register and with the byte dropped by overrun | **PASS** | test_chk_027_frame_error; verified in base.s1, base.s2, min.s1, min.s2, odd.s1, odd.s2, wide.s1 |
| CHK-028 | test | Idle line and break condition | **PASS** | test_chk_028_idle_break; verified in base.s1, base.s2, min.s1, min.s2, odd.s1, odd.s2, wide.s1 |
| CHK-029 | test | Random receive regression against the reference model | **PASS** | test_chk_029_rx_random; verified in base.s1, base.s2, min.s1, min.s2, odd.s1, odd.s2, wide.s1 |
| CHK-030 | test | Back-to-back transmit with i_tx_valid held at 1 | **PASS** | test_chk_014_cfg_min, test_chk_015_cfg_odd, test_chk_030_tx_back_to_back; verified in base.s1, base.s2, min.s1, min.s2, odd.s1, odd.s2, wide.s1 |
| CHK-031 | test | Transmit with idle gaps and i_tx_data changing outside the handshake | **PASS** | test_chk_031_tx_gaps; verified in base.s1, base.s2, min.s1, min.s2, odd.s1, odd.s2, wide.s1 |
| CHK-032 | test | i_tx_valid dropping before a handshake, back-pressure, no extra buffer | **PASS** | test_chk_032_tx_valid_drop; verified in base.s1, base.s2, min.s1, min.s2, odd.s1, odd.s2, wide.s1 |

## Requirement traceability (RTM)

| Rule | Spec ref | Statement | Checks | Mutation | Status |
|---|---|---|---|---|---|
| UL-1.1-01 |  | Serial frames use 8N1: one start bit (0), eight data bits LSB first, no parity, one stop bit (1). | CHK-011:PASS, CHK-022:PASS | 100.0 % (4/4) | **VERIFIED** |
| UL-1.1-02 |  | Each bit period lasts PARA_UART_CLKS_PER_BIT i_clk cycles. | CHK-011:PASS, CHK-022:PASS | 100.0 % (2/2) | **VERIFIED** |
| UL-1.2-01 |  | The serial line is held high when idle. | CHK-010:PASS, CHK-013:PASS | 100.0 % (2/2) | **VERIFIED** |
| UL-1.2-02 |  | PARA_UART_CLKS_PER_BIT is fixed at elaboration and must be within the legal range 4 to 65535. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| UL-1.2-04 |  | No idle bit is inserted between the stop bit and the next start bit. | CHK-013:PASS, CHK-030:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-1.2-05 |  | A one-byte holding register keeps each received byte until it is taken. | CHK-008:PASS, CHK-026:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-1.2-07 |  | The receiver detects a start bit on a falling edge and rechecks the start bit in the middle of the bit, rejecting glitches. | CHK-024:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-1.2-08 |  | The receiver samples each data bit and the stop bit in the middle of the bit. | CHK-023:PASS | — | **VERIFIED** |
| UL-1.2-09 |  | o_rx_frame_err is set and delivered together with the received byte. | CHK-003:PASS, CHK-027:PASS | — | **VERIFIED** |
| UL-1.2-10 |  | o_rx_overrun pulses. | CHK-005:PASS, CHK-026:PASS | — | **VERIFIED** |
| UL-1.2-11 |  | The transmitter and receiver operate simultaneously and independently of each other (full duplex). | CHK-017:PASS | — | **VERIFIED** |
| UL-4-01 |  | PARA_UART_CLKS_PER_BIT defines the bit period N in i_clk cycles for both transmitter and receiver, default 16, legal range 4 to 65535. | CHK-011:PASS, CHK-016:PASS, CHK-022:PASS | — | **VERIFIED** |
| UL-4-02 | REQ-PAR-002 | LPARA_UART_HALF_BIT shall equal floor(PARA_UART_CLKS_PER_BIT / 2), the middle-of-bit sampling offset H, using integer division. | CHK-015:PASS, CHK-023:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-4-03 | REQ-PAR-001 | The block shall behave as specified for every PARA_UART_CLKS_PER_BIT value from 4 to 65535, both odd and even. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| UL-4-04 | REQ-PAR-003 | The block should stop elaboration with an error message when PARA_UART_CLKS_PER_BIT is outside 4 to 65535. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| UL-5-01 |  | i_rst_n is an active-low reset that asserts asynchronously and releases synchronously to i_clk. | CHK-019:PASS | — | **VERIFIED** |
| UL-5-02 |  | When o_tx_ready is 1, the transmitter must accept the byte on i_tx_data at the next i_clk edge. | CHK-010:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-5-03 |  | o_tx_ready must reset to 1. | CHK-002:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-5-04 |  | Bit 0 of i_tx_data must be sent first on o_txd. | CHK-011:PASS | — | **VERIFIED** |
| UL-5-05 |  | o_rx_valid must reset to 0. | CHK-002:PASS | 100.0 % (2/2) | **VERIFIED** |
| UL-5-06 |  | o_rx_valid must be 1 when the holding register holds a byte. | CHK-003:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-5-07 |  | The held byte is taken by the consumer at the edge where i_rx_ready is 1. | CHK-007:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-5-08 |  | o_rx_data must reset to 0. | CHK-002:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-5-09 |  | o_rx_data must present the received byte with bit 0 received first, qualified by o_rx_valid. | CHK-003:PASS, CHK-022:PASS | — | **VERIFIED** |
| UL-5-10 |  | o_rx_frame_err must reset to 0. | CHK-002:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-5-11 |  | o_rx_frame_err must be 1 when the stop bit of the held byte was sampled as 0, qualified by o_rx_valid. | CHK-003:PASS | — | **VERIFIED** |
| UL-5-12 |  | o_rx_overrun must reset to 0. | CHK-002:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-5-13 |  | o_rx_overrun must pulse for one cycle when a received byte is dropped because the holding register is full. | CHK-005:PASS | — | **VERIFIED** |
| UL-5-14 |  | o_txd must reset to 1 and be high when idle. | CHK-002:PASS, CHK-010:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-5-15 |  | i_rxd, asynchronous to i_clk and idle high, must be synchronised inside the block. | CHK-022:PASS | — | **VERIFIED** |
| UL-6.1-01 | REQ-CLK-001 | All state elements shall be clocked only by the rising edge of i_clk, with no other clock, no gated clock and no latch. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| UL-6.2-01 | REQ-RST-001 | Every flip-flop shall take its reset value at once, without waiting for an i_clk edge. | CHK-002:PASS, CHK-019:PASS | 100.0 % (5/5) | **VERIFIED** |
| UL-6.2-02 | REQ-RST-002 | Outputs shall be o_txd = 1, o_tx_ready = 1, o_rx_valid = 0, o_rx_data = 0, o_rx_frame_err = 0, o_rx_overrun = 0. | CHK-002:PASS | 100.0 % (7/7) | **VERIFIED** |
| UL-6.2-03 | REQ-RST-003 | No transmit byte shall be accepted. | CHK-020:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-6.2-04 | REQ-RST-004 | The receiver shall not detect a start bit and shall not deliver a byte. | CHK-020:PASS | 100.0 % (2/2) | **VERIFIED** |
| UL-6.2-05 | REQ-RST-005 | Both i_rxd synchronizer flip-flops and any flip-flop holding the previous synchronised line value shall reset to 1. | CHK-021:PASS | 75.0 % (3/4) **below** | **VERIFIED** |
| UL-6.2-06 | REQ-RST-006 | The frame shall be abandoned and o_txd shall become 1 at once. | CHK-019:PASS | 100.0 % (2/2) | **VERIFIED** |
| UL-6.2-08 | REQ-RST-007 | The partly received frame shall be discarded and shall not produce o_rx_valid, o_rx_frame_err or o_rx_overrun after the release. | CHK-019:PASS | 100.0 % (5/5) | **VERIFIED** |
| UL-6.2-09 | REQ-RST-008 | The held byte shall be discarded. | CHK-019:PASS | 100.0 % (2/2) | **VERIFIED** |
| UL-6.2-10 | REQ-RST-009 | The transmitter shall be idle with o_tx_ready = 1 and shall accept a byte at the first edge after the release. | CHK-020:PASS | 100.0 % (2/2) | **VERIFIED** |
| UL-6.2-11 | REQ-RST-010 | The receiver shall be idle. | CHK-020:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-6.2-12 |  | The previous synchronised value s(R1-1) shall be taken as 1, so s(R1) = 0 is detected as T0. | CHK-021:PASS | 75.0 % (3/4) **below** | **VERIFIED** |
| UL-7.1-01 | REQ-GEN-001 | Frames shall be sent and received in 8N1 format: start bit 0, eight data bits LSB first, stop bit 1, no parity bit. | CHK-011:PASS, CHK-022:PASS | 100.0 % (2/2) | **VERIFIED** |
| UL-7.1-02 | REQ-GEN-002 | The transmitter and receiver shall operate simultaneously and independently. | CHK-017:PASS | — | **VERIFIED** |
| UL-7.1-03 |  | Activity of the transmitter shall not change the timing or outputs of the receiver, and vice versa. | CHK-017:PASS | — | **VERIFIED** |
| UL-7.1-04 | REQ-GEN-003 | Every output port shall be driven directly by a flip-flop clocked by i_clk, with no combinational path from any input to any output. | CHK-001:PASS | — | **VERIFIED** |
| UL-7.2-01 | REQ-TX-001 | The transmitter shall accept a byte at an edge only when i_tx_valid = 1, o_tx_ready = 1 and i_rst_n = 1. | CHK-010:PASS | 100.0 % (2/2) | **VERIFIED** |
| UL-7.2-02 | REQ-TX-002 | The transmitter shall capture i_tx_data at the accepting edge E0; i_tx_data at any other edge shall have no effect. | CHK-011:PASS, CHK-031:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-7.2-03 | REQ-TX-003 | o_tx_ready shall be 1 while the transmitter is idle. | CHK-010:PASS | 100.0 % (3/3) | **VERIFIED** |
| UL-7.2-04 | REQ-TX-004 | o_tx_ready shall be 0 in the cycles after edges E0 to E0+10N-2 inclusive. | CHK-012:PASS | 100.0 % (7/7) | **VERIFIED** |
| UL-7.2-05 | REQ-TX-005 | o_tx_ready shall become 1 at edge E0+10N-1, the last cycle of the stop bit. | CHK-012:PASS | 100.0 % (6/6) | **VERIFIED** |
| UL-7.2-06 | REQ-TX-006 | The transmitter shall not accept a byte and its state shall not depend on i_tx_data. | CHK-010:PASS, CHK-031:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-7.2-07 | REQ-TX-007 | The transmitter shall not require i_tx_valid to stay 1 until a handshake; if it returns to 0 before a handshake, nothing is sent. | CHK-032:PASS | — | **VERIFIED** |
| UL-7.2-08 | REQ-TX-008 | The transmitter shall hold at most one byte, the one being sent, with no additional transmit buffer. | CHK-032:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-7.3-01 | REQ-TX-010 | o_txd in the cycle after edge E0+k shall equal frame bit floor(k/N) of D (bit0=0, bit j=D[j-1], bit9=1) for k from 0 to 10N-1. | CHK-011:PASS | 100.0 % (2/2) | **VERIFIED** |
| UL-7.3-03 | REQ-TX-012 | The start bit of the new frame shall begin at edge E0+10N with no idle cycle after the previous stop bit. | CHK-013:PASS | — | **VERIFIED** |
| UL-7.3-04 | REQ-TX-013 | o_txd shall be 1 from edge E0+10N until the edge after which the next accepted frame starts. | CHK-013:PASS | 100.0 % (2/2) | **VERIFIED** |
| UL-7.3-05 | REQ-TX-014 | o_txd shall be 1 while the transmitter is idle. | CHK-010:PASS | 100.0 % (2/2) | **VERIFIED** |
| UL-7.4-01 | REQ-RX-001 | i_rxd shall pass through a synchronizer of exactly two flip-flops clocked by i_clk, with no logic between them, before other logic uses it. | CHK-022:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-7.4-02 | REQ-RX-002, REQ-RX-005, REQ-RX-013 | The receiver shall be either idle or receiving, and shall be idle after reset, after a glitch and after the stop-bit sample of a frame. | CHK-024:PASS, CHK-025:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-7.4-03 | REQ-RX-003 | The receiver shall detect a start bit at edge T0 if and only if s(T0-1)=1 and s(T0)=0. | CHK-024:PASS, CHK-029:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-7.4-04 | REQ-RX-004 | The receiver shall not need the line high longer than the single sample s(T0-1)=1 before a start bit. | CHK-024:PASS | — | **VERIFIED** |
| UL-7.4-05 | REQ-RX-005 | At T0+H the receiver shall check the start bit; if s(T0+H)=1 it shall treat it as a glitch, return to idle and receive no byte. | CHK-024:PASS | 100.0 % (2/2) | **VERIFIED** |
| UL-7.4-06 | REQ-RX-006 | A glitch shall not change o_rx_valid, o_rx_data or o_rx_frame_err, and shall not make o_rx_overrun pulse. | CHK-006:PASS, CHK-024:PASS | 100.0 % (2/2) | **VERIFIED** |
| UL-7.4-07 | REQ-RX-003, REQ-RX-007 | The receiver shall detect a new start bit at any edge T0' > T0+H at which the start condition holds. | CHK-024:PASS | — | **VERIFIED** |
| UL-7.4-08 | REQ-RX-008 | The receiver shall go on to receive the frame. | CHK-022:PASS | — | **VERIFIED** |
| UL-7.5-01 | REQ-RX-010 | Data bit i (0 to 7) shall be sampled at edge T0+H+(i+1)N, and received byte bit i shall equal s(T0+H+(i+1)N). | CHK-003:PASS, CHK-023:PASS | 100.0 % (4/4) | **VERIFIED** |
| UL-7.5-02 | REQ-RX-011 | The receiver shall sample the stop bit at edge M = T0+H+9N. | CHK-003:PASS, CHK-023:PASS | 100.0 % (3/3) | **VERIFIED** |
| UL-7.5-03 | REQ-RX-012 | Only s(T0-1), s(T0), s(T0+H), the eight data samples and s(M) shall affect a frame result; i_rxd at other edges between T0 and M shall be ignored. | CHK-023:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-7.5-04 | REQ-RX-003, REQ-RX-013 | The receiver shall be idle after sampling at M and shall detect a new start bit at any T0' > M where the start condition holds, including M+1. | CHK-025:PASS | — | **VERIFIED** |
| UL-7.5-05 | REQ-RX-014 | Every confirmed frame shall complete at M regardless of the value of s(M). | CHK-025:PASS, CHK-027:PASS | 100.0 % (3/3) | **VERIFIED** |
| UL-7.5-06 | REQ-RX-015 | The receiver shall keep sampling and receiving frames; a low i_rx_ready shall not stall or delay it. | CHK-026:PASS | — | **VERIFIED** |
| UL-7.6-01 | REQ-RX-020 | The block shall load the frame: o_rx_valid becomes 1, o_rx_data the received byte, o_rx_frame_err the inverse of s(M). | CHK-003:PASS | 100.0 % (4/4) | **VERIFIED** |
| UL-7.6-02 | REQ-RX-021 | The held byte shall be taken and the new frame loaded at the same edge; o_rx_valid stays 1 and no overrun is reported. | CHK-004:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-7.6-03 | REQ-RX-022, REQ-RX-023 | o_rx_valid shall become 0 at that edge. | CHK-007:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-7.6-04 | REQ-RX-024 | o_rx_valid, o_rx_data and o_rx_frame_err shall keep their values. | CHK-008:PASS | — | **VERIFIED** |
| UL-7.6-05 | REQ-RX-025 | o_rx_data and o_rx_frame_err shall change only when a new byte is loaded or on reset, keeping the last loaded values (0 after reset) while o_rx_valid=0. | CHK-009:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-7.6-06 | REQ-RX-026 | i_rx_ready shall have no effect while o_rx_valid=0. | CHK-009:PASS | — | **VERIFIED** |
| UL-7.6-07 | REQ-RX-027 | Bytes shall be delivered in the order in which their frames completed. | CHK-025:PASS, CHK-029:PASS | — | **VERIFIED** |
| UL-7.7-01 | REQ-FE-001 | o_rx_frame_err shall be 1 with a loaded byte if and only if s(M) of that frame was 0. | CHK-003:PASS | — | **VERIFIED** |
| UL-7.7-02 | REQ-FE-002 | The byte shall be delivered, held and taken like any other byte, and o_rx_data shall hold its sampled data bits. | CHK-027:PASS | — | **VERIFIED** |
| UL-7.7-03 | REQ-FE-003, REQ-RX-003 | The receiver shall not detect a new start bit until s is 1 at one edge and 0 at the next, so a line held at 0 produces exactly one frame. | CHK-028:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-7.8-01 | REQ-OVR-001 | The block shall drop the new byte and its frame-error flag. | CHK-005:PASS | — | **VERIFIED** |
| UL-7.8-02 | REQ-OVR-002 | o_rx_overrun shall become 1 at edge V and return to 0 at V+1, being 1 for exactly one cycle. | CHK-005:PASS | — | **VERIFIED** |
| UL-7.8-03 | REQ-OVR-003 | o_rx_valid, o_rx_data and o_rx_frame_err shall keep the held byte unchanged. | CHK-005:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-7.8-04 | REQ-OVR-004 | o_rx_overrun shall be 0 in every cycle except the cycle after an edge at which a byte is dropped. | CHK-006:PASS | 100.0 % (2/2) | **VERIFIED** |
| UL-7.8-05 | REQ-OVR-005 | o_rx_overrun shall not be qualified by o_rx_valid and shall not need a handshake. | CHK-006:PASS | — | **VERIFIED** |
| UL-7.8-06 | REQ-OVR-006 | o_rx_overrun shall not pulse. | CHK-006:PASS, CHK-019:PASS, CHK-024:PASS | — | **VERIFIED** |
| UL-8.1-01 |  | The start bit must appear on o_txd in the first cycle after the accepting handshake edge E0. | CHK-010:PASS, CHK-011:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-8.1-02 |  | The transmit frame must last 10N cycles, with the stop bit ending at edge E0+10N. | CHK-011:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-8.1-03 | REQ-TX-004, REQ-TX-005 | o_tx_ready must be 0 for 10N-1 cycles after E0 and become 1 in the last cycle of the stop bit. | CHK-012:PASS | 100.0 % (7/7) | **VERIFIED** |
| UL-8.1-04 |  | The block must never drop an offered byte while o_tx_ready = 0; the upstream block waits. | CHK-032:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-8.1-05 | REQ-TIM-001 | The transmitter must accept one byte every 10N cycles and produce a continuous stream of frames with no idle cycle between them. | CHK-030:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-8.1-06 | REQ-TIM-002 | Bytes must be sent on o_txd in the order in which they were accepted. | CHK-030:PASS | — | **VERIFIED** |
| UL-8.2-01 |  | Delivery must occur at V = T0 + H + 9N + 2 edges, which is 2 edges after the stop-bit sample M. | CHK-003:PASS, CHK-022:PASS | 100.0 % (6/6) | **VERIFIED** |
| UL-8.2-03 | REQ-TIM-003 | The receiver must accept frames back to back with no idle bit between them. | CHK-025:PASS | — | **VERIFIED** |
| UL-8.4-01 |  | After V, o_rx_overrun must be 1 for one cycle and the held byte must remain unchanged. | CHK-005:PASS | — | **VERIFIED** |
| UL-10.1-01 | REQ-FE-001, REQ-FE-002 | When the stop-bit sample s(M) is 0, the byte is delivered with o_rx_frame_err = 1. | CHK-027:PASS | — | **VERIFIED** |
| UL-10.2-01 | REQ-OVR-001, REQ-OVR-003 | The new byte is dropped, o_rx_overrun pulses for one cycle and the held byte stays. | CHK-005:PASS, CHK-026:PASS | — | **VERIFIED** |
| UL-10.2-02 | REQ-RX-021 | No overrun occurs if the held byte is taken at V itself. | CHK-004:PASS, CHK-026:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-10.2-03 |  | The frame-error flag of a dropped byte is not reported. | CHK-027:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-10.3-01 | REQ-RX-005, REQ-RX-006 | On a start-bit glitch, no byte, no flag and no pulse is produced. | CHK-024:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-10.3-02 |  | A low pulse on i_rxd sampled at fewer than H+1 consecutive edges starting at T0 is always rejected. | CHK-024:PASS | 100.0 % (2/2) | **VERIFIED** |
| UL-10.4-01 | REQ-ERR-001 | The receiver delivers byte 0x00 with o_rx_frame_err = 1, or drops it with an overrun pulse under Section 7.8 rules. | CHK-028:PASS | — | **VERIFIED** |
| UL-10.4-02 |  | The receiver receives no further frame until the line has been sampled as 1 and then as 0. | CHK-028:PASS | — | **VERIFIED** |
| UL-10.4-03 | REQ-ERR-002 | The receiver stays idle and delivers nothing. | CHK-028:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-10.5-01 | REQ-ERR-003, REQ-RST-010 | The receiver detects R1 as T0 and processes the frame under Sections 7.4 to 7.8; a line staying low yields one byte 0x00 with o_rx_frame_err = 1. | CHK-021:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-10.7-01 | REQ-ERR-004 | The transmitter shall not accept the byte and shall not record it. | CHK-032:PASS | — | **VERIFIED** |
| UL-10.7-02 | REQ-ERR-005, REQ-RX-026 | The block shall do nothing. | CHK-009:PASS | — | **VERIFIED** |
| UL-10.7-03 | REQ-ERR-006, REQ-GEN-002 | Transmit handshake and receive delivery or take in the same cycle shall be handled independently. | CHK-017:PASS | — | **VERIFIED** |
| UL-10.8-01 | REQ-ERR-007 | Bit-period and sample-offset counting shall not overflow or wrap early at N = 65535. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| UL-10.8-02 | REQ-PAR-003 | Values of N outside 4 to 65535 are illegal and must not be used. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| UL-11-01 |  | CFG-MIN with PARA_UART_CLKS_PER_BIT=4 is the smallest legal bit period and must be verified for minimum sampling margins. | CHK-014:PASS | — | **VERIFIED** |
| UL-12.1-01 |  | The environment shall release i_rst_n synchronously to i_clk, meeting recovery and removal times. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| UL-12.1-02 |  | The environment shall hold i_rst_n at 0 for at least 2 cycles of i_clk at the start of simulation. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| UL-12.1-03 |  | The environment shall drive i_tx_valid, i_tx_data and i_rx_ready synchronously to i_clk with no X or Z values. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| UL-12.1-04 |  | The testbench shall change i_rxd away from rising edges of i_clk, e.g. on the falling edge or at a non-coincident random offset. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| UL-12.1-05 |  | i_rxd shall not be X or Z after reset release. | not verified: not_applicable_to_dut | — | **NOT_VERIFIED_BY_SIM** |
| UL-12.2-02 | REQ-RX-001 | The synchronizer structure (exactly two flip-flops, no logic between them, REQ-RX-001) shall be checked by lint or structural review. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| UL-12.2-04 |  | The reference model shall compute s(E) from i_rxd and apply Sections 7.4 to 7.8 exactly. | CHK-029:PASS | — | **VERIFIED** |
| UL-12.2-06 | REQ-TX-004, REQ-TX-005, REQ-TX-010 | The checker shall check REQ-TX-004, REQ-TX-005 and REQ-TX-010 cycle by cycle. | CHK-011:PASS, CHK-012:PASS | 100.0 % (4/4) | **VERIFIED** |
| UL-12.3-01 |  | Sampling-point test: drive i_rxd so each bit is correct only at its sampling edge T0+H+(i+1)N and M, wrong at edges just before and after. | CHK-023:PASS | — | **VERIFIED** |
| UL-12.3-02 |  | Glitch test: low pulses on i_rxd of 1 to H samples are rejected and H+1 samples are accepted as a start bit. | CHK-024:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-12.3-03 |  | Loopback test: connect o_txd to i_rxd and check the Section 8.5 latency and byte integrity. | CHK-018:PASS | — | **VERIFIED** |
| UL-12.3-04 |  | Reset tests: assert i_rst_n asynchronously between clock edges in mid-transmit frame, mid-receive frame and while o_rx_valid = 1. | CHK-019:PASS | — | **VERIFIED** |
| UL-12.3-05 | REQ-ERR-001, REQ-ERR-003 | Test line low at reset release (REQ-ERR-003) and break (REQ-ERR-001). | CHK-021:PASS, CHK-028:PASS | — | **VERIFIED** |
| UL-12.4-01 |  | Cover data bytes 0x00, 0xFF, 0x55, 0xAA and random bytes in both directions. | CHK-022:PASS, CHK-030:PASS | — | **VERIFIED** |
| UL-12.4-02 |  | Cover back-to-back transmit with i_tx_valid held at 1, and transmit with idle gaps of various lengths. | CHK-030:PASS, CHK-031:PASS | — | **VERIFIED** |
| UL-12.4-03 |  | Cover back-to-back receive frames with the next start bit right after the stop bit. | CHK-025:PASS | — | **VERIFIED** |
| UL-12.4-04 |  | Cover frame error with o_rx_valid = 0, and frame error with the byte dropped by overrun. | CHK-027:PASS | — | **VERIFIED** |
| UL-12.4-05 |  | Cover overrun, and the case where the held byte is taken at delivery edge V itself (no overrun). | CHK-026:PASS | — | **VERIFIED** |
| UL-12.4-06 |  | Cover i_rx_ready held at 1, toggling at random, and held at 0 for several frames. | CHK-026:PASS | — | **VERIFIED** |
| UL-12.4-07 |  | Cover i_tx_valid dropping before a handshake. | CHK-032:PASS | — | **VERIFIED** |
| UL-12.4-08 |  | Cover transmit and receive active at the same time. | CHK-017:PASS | — | **VERIFIED** |
| UL-13-01 | REQ-IMP-001 | The block shall meet timing at 50 MHz (20 ns period) on GF180MCU for every legal value of PARA_UART_CLKS_PER_BIT. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| UL-13-02 | REQ-IMP-002 | The RTL shall follow docs/RTL_RULES.md. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| UL-13-03 | REQ-IMP-003 | The RTL shall be synthesizable, contain no latches and pass Verilator lint with no warnings. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| UL-13-04 | REQ-IMP-004 | All flip-flops shall use the asynchronous active-low reset i_rst_n. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| UL-13-05 | REQ-IMP-005 | The two i_rxd synchronizer flip-flops should be marked so synthesis does not merge, duplicate or retime them. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| UL-13-06 | REQ-IMP-006 | The bit-period counters should be only as wide as PARA_UART_CLKS_PER_BIT needs, at most 16 bits. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| UL-13-07 |  | The block should use only the storage the specification requires: transmit shift register, receive shift register, holding register, counters and flags. | not verified: design_guideline | — | **NOT_VERIFIED_BY_SIM** |
| UL-14-01 | REQ-RST-003 | o_tx_ready must be 1 (its idle value) while i_rst_n = 0, since no handshake is possible during reset. | CHK-002:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-14-02 |  | The receiver samples the middle of each bit H = floor(N/2) edges after T0, then every N edges. | CHK-015:PASS, CHK-023:PASS | 100.0 % (2/2) | **VERIFIED** |
| UL-14-03 |  | o_rx_valid is delivered at V = M + 2, where M is the sample edge of i_rxd and 2 is the synchronizer latency. | CHK-003:PASS | 100.0 % (3/3) | **VERIFIED** |
| UL-14-04 |  | The new byte is loaded and no overrun occurs. | CHK-004:PASS, CHK-026:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-14-05 |  | A new start requires a 1-to-0 transition on i_rxd, so a break yields only one byte. | CHK-028:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-14-06 |  | The synchronizer resets to 1; a low i_rxd at reset release is detected as a start bit. | CHK-021:PASS | 100.0 % (3/3) | **VERIFIED** |
| UL-14-07 |  | o_rx_data and o_rx_frame_err keep the last loaded values, and are 0 after reset. | CHK-009:PASS | 100.0 % (1/1) | **VERIFIED** |
| UL-14-08 |  | The frame is abandoned, o_txd goes to 1 at once and the byte is lost. | CHK-019:PASS | 100.0 % (2/2) | **VERIFIED** |
| UL-14-09 |  | The frame-error flag of a dropped byte is not reported. | CHK-027:PASS | — | **VERIFIED** |
| UL-14-10 |  | An elaboration error should be raised for illegal parameter values; this is not verified. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| UL-14-11 |  | CFG-ODD (5) and CFG-WIDE (1024) are simulated; CFG-MAX (65535) is not simulated and is covered by elaboration and synthesis only. | CHK-015:PASS, CHK-016:PASS | — | **VERIFIED** |
| UL-14-12 |  | No area budget is required for GF180MCU; area is reported, not checked. | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |
| UL-14-13 |  | The 50 MHz target applies at the slow corner (GF180MCU SS, 125 C, 4.5 V). | not verified: static_or_structural | — | **NOT_VERIFIED_BY_SIM** |

## Mutants

| ID | File:line | Operator | Status | Caught by | Rules | Equivalent? |
|---|---|---|---|---|---|---|
| M01 | m_uart_lite_rx.sv:151 | negate_if | killed | CHK-003, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_020_reset_idle, test_chk_02 | UL-6.2-08, UL-6.2-11, UL-6.2-04, UL-6.2-01 |  |
| M02 | m_uart_lite_tx.sv:75 | and_to_or | killed | CHK-011, CHK-012, CHK-013, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_020_reset | UL-7.2-05, UL-7.2-04, UL-8.1-03, UL-12.2-06 |  |
| M03 | m_uart_lite_tx.sv:69 | one_to_zero | killed | CHK-010, CHK-013, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_020_reset_idle, te | UL-1.2-01, UL-7.3-04, UL-7.3-05, UL-7.2-03 |  |
| M04 | m_uart_lite_rx.sv:72 | one_to_zero | killed | CHK-003, CHK-004, CHK-005, CHK-006, CHK-009, test_chk_018_loopback, test_chk_020_reset_idle, test_chk_021_low_at_release | UL-6.2-05, UL-6.2-12, UL-14-06 |  |
| M05 | m_uart_lite_tx.sv:75 | eq_to_ne | killed | CHK-012, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_020_reset_idle, test_chk_030_tx_back_to_back, test_ch | UL-7.2-05, UL-7.2-04, UL-8.1-03, UL-12.2-06 |  |
| M06 | m_uart_lite_rx.sv:125 | eq_to_ne | killed | CHK-003, CHK-004, CHK-005, CHK-006, CHK-009, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset,  | UL-7.5-02, UL-7.5-01, UL-1.1-01, UL-8.2-01 |  |
| M07 | m_uart_lite_tx.sv:70 | negate_if | killed | CHK-010, CHK-011, CHK-012, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_020_reset | UL-8.1-02, UL-7.2-04, UL-7.2-05, UL-8.1-03, UL-1.1-02 |  |
| M08 | m_uart_lite_tx.sv:61 | zero_to_one | killed | CHK-010, CHK-011, CHK-013, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_020_reset | UL-8.1-01, UL-7.3-01, UL-1.1-01, UL-7.1-01 |  |
| M09 | m_uart_lite_rx.sv:180 | zero_to_one | killed | CHK-002, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_020_reset_idle, test_chk_02 | UL-5-10, UL-6.2-02, UL-14-07, UL-7.6-05, UL-6.2-08 |  |
| M10 | m_uart_lite_rx.sv:71 | negate_if | killed | CHK-003, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_020_reset_idle, test_chk_02 | UL-6.2-05, UL-6.2-12, UL-14-06, UL-6.2-01, UL-7.4-01 |  |
| M11 | m_uart_lite_tx.sv:76 | one_to_zero | killed | CHK-010, CHK-012, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_020_reset_idle, test_chk_030_tx_back_to_back | UL-7.2-05, UL-8.1-03, UL-7.2-03, UL-8.1-05 |  |
| M12 | m_uart_lite_rx.sv:139 | one_to_zero | killed | CHK-003, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_020_reset_idle, test_chk_02 | UL-7.5-05, UL-8.2-01, UL-7.6-01, UL-14-03 |  |
| M13 | m_uart_lite_tx.sv:75 | eq_to_ne | killed | CHK-011, CHK-012, CHK-013, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_020_reset | UL-7.2-05, UL-7.2-04, UL-8.1-03, UL-12.2-06 |  |
| M14 | m_uart_lite_tx.sv:75 | negate_if | killed | CHK-011, CHK-012, CHK-013, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_020_reset | UL-7.2-05, UL-7.2-04, UL-8.1-03, UL-12.2-06 |  |
| M15 | m_uart_lite_tx.sv:62 | zero_to_one | killed | CHK-010, CHK-011, CHK-012, CHK-013, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_ | UL-7.2-04, UL-8.1-03, UL-7.2-01, UL-8.1-04, UL-7.2-08 |  |
| M16 | m_uart_lite_rx.sv:178 | zero_to_one | killed | CHK-002, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_020_reset_idle, test_chk_02 | UL-5-05, UL-6.2-02, UL-6.2-09, UL-6.2-04, UL-6.2-08 |  |
| M17 | m_uart_lite_rx.sv:99 | negate_if | killed | CHK-003, CHK-004, CHK-005, CHK-006, CHK-009, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset,  | UL-7.4-03, UL-7.4-02, UL-1.2-07, UL-7.7-03, UL-14-05 |  |
| M18 | m_uart_lite_tx.sv:86 | one_to_zero | killed | CHK-011, CHK-013, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_020_reset_idle, test_chk_030_tx_back_to_back | UL-7.3-01, UL-1.1-01, UL-7.1-01, UL-1.2-04 |  |
| M19 | m_uart_lite_rx.sv:74 | one_to_zero | survived |  | UL-6.2-05, UL-6.2-12 | formal BOUNDED (claimed: r_rxd_prev is reset to 0 instead of 1, but r_rxd_sync is still reset to 1. So w_rx_start_fall = prev & ~sync is 0 while in reset or in the cycle just after rele) |
| M20 | m_uart_lite_tx.sv:66 | negate_if | killed | CHK-010, CHK-011, CHK-012, CHK-013, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_ | UL-7.3-04, UL-1.2-01, UL-7.3-05, UL-7.2-03, UL-7.2-04 |  |
| M21 | m_uart_lite_rx.sv:181 | zero_to_one | killed | CHK-002, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_020_reset_idle, test_chk_02 | UL-5-12, UL-6.2-02, UL-6.2-08, UL-7.8-04 |  |
| M22 | m_uart_lite_rx.sv:125 | negate_if | killed | CHK-003, CHK-004, CHK-005, CHK-006, CHK-009, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset,  | UL-7.5-02, UL-7.5-01, UL-1.1-01, UL-8.2-01 |  |
| M23 | m_uart_lite_tx.sv:51 | one_to_zero | killed | CHK-002, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_020_reset_idle, test_chk_02 | UL-5-14, UL-6.2-02, UL-6.2-06, UL-14-08, UL-6.2-01 |  |
| M24 | m_uart_lite_rx.sv:73 | one_to_zero | killed | CHK-003, CHK-005, CHK-006, CHK-009, test_chk_018_loopback, test_chk_020_reset_idle, test_chk_021_low_at_release, test_re | UL-6.2-05, UL-14-06, UL-6.2-12, UL-10.5-01 |  |
| M25 | m_uart_lite_tx.sv:56 | negate_if | killed | CHK-010, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_020_reset_idle, test_chk_02 | UL-7.2-01, UL-5-02, UL-7.2-02, UL-7.2-06, UL-6.2-03 |  |
| M26 | m_uart_lite_rx.sv:96 | zero_to_one | killed | CHK-005, CHK-006, CHK-007, CHK-009, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_ | UL-7.8-04, UL-7.4-06, UL-10.4-03, UL-7.6-01, UL-7.5-05 |  |
| M27 | m_uart_lite_rx.sv:119 | negate_if | killed | CHK-003, CHK-004, CHK-005, CHK-006, CHK-009, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset,  | UL-7.5-01, UL-14-02, UL-1.1-02, UL-7.5-03 |  |
| M28 | m_uart_lite_tx.sv:52 | one_to_zero | killed | CHK-002, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_020_reset_idle, test_chk_02 | UL-5-03, UL-6.2-02, UL-14-01, UL-6.2-10, UL-6.2-01 |  |
| M29 | m_uart_lite_rx.sv:191 | one_to_zero | killed | CHK-003, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_020_reset_idle, test_chk_02 | UL-7.6-01, UL-8.2-01, UL-14-03, UL-1.2-05, UL-5-06 |  |
| M30 | m_uart_lite_tx.sv:50 | negate_if | killed | CHK-002, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_020_reset_idle, test_chk_02 | UL-6.2-01, UL-6.2-02, UL-6.2-06, UL-14-08, UL-6.2-10 |  |
| M31 | m_uart_lite_rx.sv:198 | zero_to_one | killed | CHK-007, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_020_reset_idle, test_chk_021_low_at_release, test_chk | UL-7.6-03, UL-5-07, UL-10.2-03, UL-7.8-03 |  |
| M32 | m_uart_lite_rx.sv:187 | negate_if | killed | CHK-004, CHK-007, CHK-008, CHK-009, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_ | UL-7.6-01, UL-7.6-02, UL-14-04, UL-10.2-02, UL-8.2-01 |  |
| M33 | m_uart_lite_rx.sv:177 | negate_if | killed | CHK-003, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_020_reset_idle, test_chk_02 | UL-6.2-02, UL-6.2-08, UL-6.2-09, UL-5-05, UL-5-08 |  |
| M34 | m_uart_lite_rx.sv:108 | negate_if | killed | CHK-003, CHK-005, CHK-006, CHK-009, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset, test_chk_ | UL-7.4-05, UL-10.3-01, UL-10.3-02, UL-7.4-06, UL-12.3-02 |  |
| M35 | m_uart_lite_rx.sv:133 | negate_if | killed | CHK-003, CHK-004, CHK-005, CHK-006, CHK-009, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset,  | UL-7.5-02, UL-8.2-01, UL-14-03, UL-7.5-05 |  |
| M36 | m_uart_lite_rx.sv:106 | negate_if | killed | CHK-003, CHK-004, CHK-005, CHK-006, CHK-009, test_chk_017_full_duplex, test_chk_018_loopback, test_chk_019_async_reset,  | UL-7.4-05, UL-14-02, UL-10.3-02, UL-7.5-01, UL-4-02 |  |

## Not verified by this run

- Formal: the assertions were checked by SymbiYosys under the environment assumptions (work/formal.md); a BOUNDED result holds only up to its depth. CDC/RDC, STA, synthesis and DFT checks are outside this flow.
- Rules marked NOT_VERIFIED_BY_SIM carry the contract's reason (static, structural, not observable...).
- Only the configurations of the run set above were simulated; code coverage is merged over its runs, mutation testing used the primary run base.s1.

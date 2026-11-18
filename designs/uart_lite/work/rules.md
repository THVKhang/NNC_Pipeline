# Rules for review (Gate 1)

```
rules in 168: kept 154 (fixed 16), merged 2, rejected 12, unreviewed 0; open questions 2 (raised 28, answered from the documents 24, duplicates 2)
calls: 13 (0 from cache)  cost US$0.5126
```

Approve with `nnc gate approve <design> G1_rules --by <name>` after reading this sheet.

## Open questions (the designer decides: `nnc answer <design> <n> "<decision>" --by <name>`)

1. ENV-004 requires i_rxd to change away from rising clock edges. The loopback test (UL-12.3-03) connects o_txd to i_rxd, and o_txd changes synchronously with the clock. Is the loopback exempt from ENV-004, or is a delay or falling-edge offset required? (UL-12.1-04, UL-12.3-03) — *The spec does not say whether the loopback test is exempt from ENV-004, or whether a delay or falling-edge offset is needed on the o_txd to i_rxd connection. The designer must decide this.*
   - **Decision** (Claude (delegated by GabrielHCMUT), 2026-11-17T10:24:38+00:00): Not exempt. In the loopback test o_txd reaches i_rxd through a half-cycle delay (i_rxd changes at the falling edge of i_clk), so ENV-004 holds; no other delay is required.
2. UL-12.2-02 asks for lint or structural review of the synchronizer. Who owns that check, and how does it fit the simulation verification flow? (UL-12.2-02) — *The spec says the synchronizer structure is checked by lint or structural review. It does not name an owner or say how that check fits into the simulation verification flow. The designer must decide this.*
   - **Decision** (Claude (delegated by GabrielHCMUT), 2026-11-17T10:24:38+00:00): The synchronizer structure (two flip-flops in series on i_rxd, nothing else in between) is checked on the RTL at gate D2 (docs/RTL_RULES.md RR-33, with nnc rtl-check), not by simulation. Simulation checks only its port-visible effect (the receive latency of D-003).

## Questions answered by the documents

- When a received byte is dropped due to overrun, is the holding register's existing byte and its frame_err kept unchanged, and is the new byte entirely discarded? → Yes. The new byte and its frame-error flag are dropped. The held byte, o_rx_data and o_rx_frame_err stay unchanged. [7.8:s1, 7.8:s3, 10.2:s2, 10.2:s4]
- Is o_rx_overrun a one-cycle pulse, and is it a primary output not listed in the interface rule for the receive stream? → Yes, o_rx_overrun is 1 for exactly one cycle. It is a separate output port, listed in the port table and in the features, and not part of the receive-stream tuple. It is not qualified by o_rx_valid. [5:s11, 7.8:s2, 7.8:s5, 1.2:s8, 1.2:s13]
- Is a byte with a frame error still delivered with o_rx_valid asserted (quote says delivered together with the byte)? → Yes. A frame-error byte is delivered with o_rx_valid=1, held and taken like any other byte. o_rx_frame_err=1 is delivered with it. [7.7:s2, 1.2:s12, 10.1:s2]
- UL-4-01 gives the legal range 4 to 65535 while UL-4-04 only says SHOULD stop elaboration outside it. What is the defined behavior for out-of-range values if the elaboration check is absent? Also, is the 16-bit upper bound consistent with the counter width used for N? → Behaviour for illegal values is unspecified and not verified. The elaboration error is only recommended (should). The range 4 to 65535 fits within a 16-bit counter, and the counters need be at most 16 bits wide. [4:s1, 4:s5, 4:s6, 14:s11, 13:s6]
- For odd N, floor(N/2) puts the sample point one cycle before the true bit center. Is that acceptable for the receiver's timing and tolerance? → Yes. H=floor(N/2) is the defined sampling offset. For odd N it is a defined point (N=5 gives H=2). No tolerance beyond what follows from the sampling points is claimed. [4:s4, 14:s2, 10.8:s4, 1.3:s7]
- Is o_rx_valid/o_rx_data/o_rx_frame_err reset-value assertion meaningful when the reset is asserted asynchronously, and does reset clear them immediately? → Yes. Reset assertion is asynchronous. Every flip-flop takes its reset value at once, without waiting for a clock edge. While reset is low, o_rx_valid, o_rx_data and o_rx_frame_err are 0. [6.2:s2, 6.2:s4, 6.2:s5]
- Are the master/slave/source/destination roles for the tx and rx streams defined (which side drives valid and which drives ready)? → Yes. For transmit, the upstream side drives i_tx_valid and i_tx_data, and the block drives o_tx_ready. For receive, the block drives o_rx_valid and the data, and the consumer drives i_rx_ready. [5:s4, 5:s5, 5:s7, 5:s8, 1.1:s4]
- Does o_rx_frame_err hold its value while o_rx_valid is low, or is it don't-care? → It holds. While o_rx_valid=0, o_rx_data and o_rx_frame_err keep the values of the last loaded byte, or 0 if none has been loaded since reset. [7.6:s6, 7.6:s7, 14:s7]
- REQ-RST-001 says every flip-flop resets asynchronously, but REQ-RST-005/RST-009 and 'first edge after release' imply synchronous release handling. Is i_rst_n release synchronised internally or asserted/released asynchronously relative to i_clk? → Reset assertion is asynchronous. Release is synchronised outside the block by the environment (ENV-001). The block has no reset synchronizer. [6.2:s2, 6.2:s3, 12.1:s1, 12.1:s2, 14:s8]
- Does 'no transmit byte accepted while i_rst_n = 0' with o_tx_ready = 1 conflict with the handshake definition that a transfer happens when i_tx_valid and o_tx_ready are both 1? → No conflict. The handshake definition itself includes i_rst_n=1, so no handshake can occur while reset is low even though o_tx_ready=1. [3:s6, 7.2:s1, 6.2:s6, 14:s1]
- o_tx_ready is 0 in the cycles after E0..E0+10N-2 and 'becomes 1 at edge E0+10N-1'. Is ready first 1 in the cycle after edge E0+10N-1, so a new accept at E0+10N gives back-to-back frames? State the cycle convention precisely. → A registered output that becomes X at edge E has value X in the cycle after edge E. o_tx_ready is 0 in the cycles after E0 to E0+10N-2. It becomes 1 at edge E0+10N-1, so it is 1 in the cycle after that edge, which is the last stop-bit cycle. A new byte can then be accepted at E0+10N, with its start bit beginning there and no idle cycle. [3:s4, 7.2:s5, 7.2:s6, 7.3:s4, 8.3:s14]
- What are the value and constraints of H (half-bit) relative to N, e.g. for odd N or N=1? Does N=1 still work with the 2-flop synchronizer and the delivery at M+2? → H=floor(N/2). For odd N it rounds down (N=5 gives H=2). N=1 is illegal, since the legal range is 4 to 65535, so it is not supported. Delivery is at V=M+2. [4:s2, 4:s4, 4:s1, 4:s6, 10.8:s4, 3:s13]
- What happens to a frame in progress and to the holding register when i_rst_n is asserted? The spec only says a frame cut short by reset must not pulse overrun. Is the TX frame also aborted, and does o_txd return to 1? → A TX frame in progress is abandoned. o_txd becomes 1 at once and the byte is lost. A partly received frame is discarded and gives no valid, frame_err or overrun after release. A held byte is discarded. [6.2:s9, 6.2:s10, 6.2:s11, 14:s9, 7.8:s6]
- If the next frame completes at M' before the previous frame's delivery edge V=M+2 (possible for small N), is delivery of both frames still ordered and each checked at its own V? → Yes. Each frame is delivered at its own V=M+2, in completion order. After M the receiver is idle, so the next start is at T0'>M and the spacing between starts is at least H+9N+1 cycles. With N at least 4, the next frame's M' therefore falls well after V. [7.6:s1, 7.6:s9, 7.5:s6, 7.5:s7, 8.2:s3]
- Are 'master' and 'slave' the correct actor labels for the UART transmitter and receiver? UL-8.1-xx and UL-8.2-xx describe a transmitter and a receiver, not bus master and slave roles. → No. The spec uses transmitter and receiver, with valid/ready streams. Neither master nor slave appears as a role. [1.1:s4, 5:s4, 5:s5, 5:s7, 5:s8]
- UL-8.1-01 says the start bit starts at E0 and also that this is the first cycle after the handshake. Is the start bit visible on o_txd during the cycle that follows E0, or is it visible at E0 itself? → The start bit is on o_txd in the cycle after edge E0 (k=0), which is the first cycle after the handshake. It is a registered output, not visible at E0 itself. [8.1:s1, 7.3:s2, 3:s4, 8.3:s4]
- What are H and M? The quotes don't define H, the half-bit offset, or M, the stop-bit sample point. For odd N, how is H rounded? → H=floor(N/2), the offset of the middle-of-bit sample, so odd N rounds down. M=T0+H+9N is the stop-bit sampling edge. [3:s2, 3:s12, 4:s2]
- Is a dropped byte's frame error never reported on o_rx_frame_err, and is the overrun-with-frame-error case in the stuck-low scenario consistent with it? → Yes. The frame error of a dropped byte is not reported. In the stuck-low case the spec allows either delivery of 0x00 with frame_err=1 or a drop with an overrun pulse, so it is consistent. [10.2:s4, 14:s10, 7.8:s1, 10.4:s1]
- What is the exact definition of 'sampled as 1 then as 0' for re-arming after a stuck-low frame, e.g. is a single 1 sample enough? → A start bit needs s=1 at one edge and s=0 at the next. A single sample of 1 followed by 0 is enough, and no longer high time is needed. [7.4:s4, 7.4:s5, 7.7:s3, 10.4:s2]
- The sampling-point test (UL-12.3-01) needs the wrong value at the edges just before and after the sampling edge. For small N, such as N=1 or 2, does this apply, or are some bits skipped? The spec only says 'where N allows that'. → N=1 and N=2 are illegal, since N is at least 4, so they are not tested. At N=4 the sample is 2 edges after the first edge of the bit and 1 edge before its last, so edges just before and after exist. [4:s1, 4:s6, 10.8:s2, 12.3:s1]
- Does 'all flip-flops use asynchronous reset' also cover the two i_rxd synchronizer flops, and is reset deassertion assumed to be synchronized externally? → Yes. All flip-flops use the asynchronous active-low reset, including both synchronizer flops, which reset to 1. Reset release is synchronised externally by the environment. [13:s4, 6.2:s8, 12.1:s1, 12.1:s2]
- What does 'legal value' of PARA_UART_CLKS_PER_BIT mean (the minimum and maximum)? The quotes don't give the range. → The legal range is 4 to 65535 inclusive. The default is 16. [4:s1, 1.2:s4, 4:s3]
- UL-14-09: what does 'a byte is dropped' mean (overrun when the held byte is not taken?), and how is the frame-error of a dropped byte observed, since the output holds the last loaded values (UL-14-07)? → A byte is dropped when a frame completes at V while o_rx_valid=1 and i_rx_ready=0, which gives an overrun. The frame-error flag of a dropped byte is not reported, so it is not observable. [3:s16, 7.8:s1, 10.2:s1, 10.2:s4, 14:s10]
- UL-14-01 and UL-14-08: is o_tx_ready 1 immediately on reset assertion (asynchronous) or only after the next clock edge? Likewise for o_txd=1 'at once'. → Yes, both are immediate. On reset assertion every flip-flop takes its reset value at once, without a clock edge. So o_tx_ready=1 and o_txd=1 immediately. [6.2:s4, 6.2:s5, 6.2:s9, 14:s1]


## uart_lite_Design_Specification.md

| ID | Spec ref | Str. | Actor | Check | Statement | Review |
|---|---|---|---|---|---|---|
| UL-1.1-01 |  | MUST | system | both | Serial frames use 8N1: one start bit (0), eight data bits LSB first, no parity, one stop bit (1). | keep |
| UL-1.1-02 |  | MUST | system | both | Each bit period lasts PARA_UART_CLKS_PER_BIT i_clk cycles. | keep |
| UL-1.2-01 |  | MUST | system | both | The serial line is held high when idle. *(when: When the serial line is idle)* | keep |
| UL-1.2-02 |  | MUST | system | none | PARA_UART_CLKS_PER_BIT is fixed at elaboration and must be within the legal range 4 to 65535. | keep |
| UL-1.2-04 |  | MUST | system | both | No idle bit is inserted between the stop bit and the next start bit. *(when: When bytes are sent back to back)* | keep |
| UL-1.2-05 |  | MUST | system | both | A one-byte holding register keeps each received byte until it is taken. *(when: After a byte is received)* | keep |
| UL-1.2-07 |  | MUST | system | scenario | The receiver detects a start bit on a falling edge and rechecks the start bit in the middle of the bit, rejecting glitches. | keep |
| UL-1.2-08 |  | MUST | system | scenario | The receiver samples each data bit and the stop bit in the middle of the bit. | keep |
| UL-1.2-09 |  | MUST | system | both | o_rx_frame_err is set and delivered together with the received byte. *(when: When the stop bit is sampled as 0)* | keep |
| UL-1.2-10 |  | MUST | system | both | o_rx_overrun pulses. *(when: When a received byte is dropped because the previous byte has not been taken)* | keep |
| UL-1.2-11 |  | MUST | system | scenario | The transmitter and receiver operate simultaneously and independently of each other (full duplex). | keep |
| UL-4-01 |  | MUST | system | scenario | PARA_UART_CLKS_PER_BIT defines the bit period N in i_clk cycles for both transmitter and receiver, default 16, legal range 4 to 65535. | keep |
| UL-4-02 | REQ-PAR-002 | MUST | system | scenario | LPARA_UART_HALF_BIT shall equal floor(PARA_UART_CLKS_PER_BIT / 2), the middle-of-bit sampling offset H, using integer division. | fix: check both->scenario |
| UL-4-03 | REQ-PAR-001 | MUST | system | scenario | The block shall behave as specified for every PARA_UART_CLKS_PER_BIT value from 4 to 65535, both odd and even. *(when: PARA_UART_CLKS_PER_BIT is any value from 4 to 65535 inclusive, odd or even)* | keep |
| UL-4-04 | REQ-PAR-003 | SHOULD | system | none | The block should stop elaboration with an error message when PARA_UART_CLKS_PER_BIT is outside 4 to 65535. *(when: PARA_UART_CLKS_PER_BIT is less than 4 or greater than 65535)* | keep |
| UL-5-01 |  | MUST | system | scenario | i_rst_n is an active-low reset that asserts asynchronously and releases synchronously to i_clk. *(when: i_rst_n is asserted (low))* | keep |
| UL-5-02 |  | MUST | slave | scenario | When o_tx_ready is 1, the transmitter must accept the byte on i_tx_data at the next i_clk edge. *(when: o_tx_ready is high and i_tx_valid is high at a clock edge)* | keep |
| UL-5-03 |  | MUST | slave | assertion | o_tx_ready must reset to 1. *(when: after reset)* | keep |
| UL-5-04 |  | MUST | slave | scenario | Bit 0 of i_tx_data must be sent first on o_txd. *(when: transmitting a byte)* | fix: actor source->slave |
| UL-5-05 |  | MUST | destination | assertion | o_rx_valid must reset to 0. *(when: after reset)* | keep |
| UL-5-06 |  | MUST | source | scenario | o_rx_valid must be 1 when the holding register holds a byte. *(when: holding register holds a byte)* | fix: actor destination->source |
| UL-5-07 |  | MUST | source | scenario | The held byte is taken by the consumer at the edge where i_rx_ready is 1. *(when: i_rx_ready is high at a clock edge with o_rx_valid high)* | fix: actor destination->source |
| UL-5-08 |  | MUST | source | assertion | o_rx_data must reset to 0. *(when: after reset)* | fix: actor destination->source |
| UL-5-09 |  | MUST | source | scenario | o_rx_data must present the received byte with bit 0 received first, qualified by o_rx_valid. *(when: o_rx_valid is high)* | fix: actor destination->source |
| UL-5-10 |  | MUST | source | assertion | o_rx_frame_err must reset to 0. *(when: after reset)* | fix: actor destination->source |
| UL-5-11 |  | MUST | source | scenario | o_rx_frame_err must be 1 when the stop bit of the held byte was sampled as 0, qualified by o_rx_valid. *(when: o_rx_valid is high)* | fix: actor destination->source |
| UL-5-12 |  | MUST | source | assertion | o_rx_overrun must reset to 0. *(when: after reset)* | fix: actor destination->source |
| UL-5-13 |  | MUST | source | scenario | o_rx_overrun must pulse for one cycle when a received byte is dropped because the holding register is full. *(when: a received byte is dropped because the holding register is full)* | fix: actor destination->source, check both->scenario |
| UL-5-14 |  | MUST | slave | both | o_txd must reset to 1 and be high when idle. *(when: after reset or idle)* | fix: actor source->slave, check assertion->both |
| UL-5-15 |  | MUST | system | scenario | i_rxd, asynchronous to i_clk and idle high, must be synchronised inside the block. | fix: actor destination->system |
| UL-6.1-01 | REQ-CLK-001 | MUST | system | none | All state elements shall be clocked only by the rising edge of i_clk, with no other clock, no gated clock and no latch. | keep |
| UL-6.2-01 | REQ-RST-001 | MUST | system | both | Every flip-flop shall take its reset value at once, without waiting for an i_clk edge. *(when: When i_rst_n becomes 0)* | fix: check assertion->both |
| UL-6.2-02 | REQ-RST-002 | MUST | system | assertion | Outputs shall be o_txd = 1, o_tx_ready = 1, o_rx_valid = 0, o_rx_data = 0, o_rx_frame_err = 0, o_rx_overrun = 0. *(when: While i_rst_n is 0)* | keep |
| UL-6.2-03 | REQ-RST-003 | MUST_NOT | system | both | No transmit byte shall be accepted. *(when: While i_rst_n is 0, even when i_tx_valid = 1 and o_tx_ready = 1)* | keep |
| UL-6.2-04 | REQ-RST-004 | MUST_NOT | system | both | The receiver shall not detect a start bit and shall not deliver a byte. *(when: While i_rst_n is 0)* | keep |
| UL-6.2-05 | REQ-RST-005 | MUST | system | scenario | Both i_rxd synchronizer flip-flops and any flip-flop holding the previous synchronised line value shall reset to 1. *(when: On reset)* | keep |
| UL-6.2-06 | REQ-RST-006 | MUST | system | both | The frame shall be abandoned and o_txd shall become 1 at once. *(when: Reset asserted during a transmission)* | keep; merged UL-6.2-07 |
| UL-6.2-08 | REQ-RST-007 | MUST_NOT | system | scenario | The partly received frame shall be discarded and shall not produce o_rx_valid, o_rx_frame_err or o_rx_overrun after the release. *(when: Reset asserted during a reception)* | fix: strength MUST->MUST_NOT |
| UL-6.2-09 | REQ-RST-008 | MUST | system | scenario | The held byte shall be discarded. *(when: Reset asserted while o_rx_valid = 1)* | keep |
| UL-6.2-10 | REQ-RST-009 | MUST | system | both | The transmitter shall be idle with o_tx_ready = 1 and shall accept a byte at the first edge after the release. *(when: After release of i_rst_n)* | keep |
| UL-6.2-11 | REQ-RST-010 | MUST | system | scenario | The receiver shall be idle. *(when: After release of i_rst_n)* | keep |
| UL-6.2-12 |  | MUST | system | scenario | The previous synchronised value s(R1-1) shall be taken as 1, so s(R1) = 0 is detected as T0. *(when: First edge R1 after reset release)* | keep |
| UL-7.1-01 | REQ-GEN-001 | MUST | system | both | Frames shall be sent and received in 8N1 format: start bit 0, eight data bits LSB first, stop bit 1, no parity bit. | keep |
| UL-7.1-02 | REQ-GEN-002 | MUST | system | scenario | The transmitter and receiver shall operate simultaneously and independently. | keep |
| UL-7.1-03 |  | MUST_NOT | system | scenario | Activity of the transmitter shall not change the timing or outputs of the receiver, and vice versa. | keep |
| UL-7.1-04 | REQ-GEN-003 | MUST | system | both | Every output port shall be driven directly by a flip-flop clocked by i_clk, with no combinational path from any input to any output. | keep |
| UL-7.2-01 | REQ-TX-001 | MUST_NOT | slave | assertion | The transmitter shall accept a byte at an edge only when i_tx_valid = 1, o_tx_ready = 1 and i_rst_n = 1. *(when: at a clock edge)* | fix: strength MUST->MUST_NOT |
| UL-7.2-02 | REQ-TX-002 | MUST | slave | both | The transmitter shall capture i_tx_data at the accepting edge E0; i_tx_data at any other edge shall have no effect. *(when: accepting edge E0)* | keep |
| UL-7.2-03 | REQ-TX-003 | MUST | slave | assertion | o_tx_ready shall be 1 while the transmitter is idle. *(when: transmitter idle, no frame in progress)* | keep |
| UL-7.2-04 | REQ-TX-004 | MUST | slave | assertion | o_tx_ready shall be 0 in the cycles after edges E0 to E0+10N-2 inclusive. *(when: after accepting edge E0)* | keep |
| UL-7.2-05 | REQ-TX-005 | MUST | slave | assertion | o_tx_ready shall become 1 at edge E0+10N-1, the last cycle of the stop bit. *(when: after accepting edge E0)* | keep |
| UL-7.2-06 | REQ-TX-006 | MUST_NOT | slave | both | The transmitter shall not accept a byte and its state shall not depend on i_tx_data. *(when: i_tx_valid is 0 or o_tx_ready is 0 at an edge)* | keep |
| UL-7.2-07 | REQ-TX-007 | MUST_NOT | slave | scenario | The transmitter shall not require i_tx_valid to stay 1 until a handshake; if it returns to 0 before a handshake, nothing is sent. | keep |
| UL-7.2-08 | REQ-TX-008 | MUST | slave | scenario | The transmitter shall hold at most one byte, the one being sent, with no additional transmit buffer. | keep |
| UL-7.3-01 | REQ-TX-010 | MUST | slave | assertion | o_txd in the cycle after edge E0+k shall equal frame bit floor(k/N) of D (bit0=0, bit j=D[j-1], bit9=1) for k from 0 to 10N-1. *(when: byte D accepted at edge E0)* | keep; merged UL-7.3-02 |
| UL-7.3-03 | REQ-TX-012 | MUST | slave | assertion | The start bit of the new frame shall begin at edge E0+10N with no idle cycle after the previous stop bit. *(when: new byte accepted at edge E0+10N)* | keep |
| UL-7.3-04 | REQ-TX-013 | MUST | slave | assertion | o_txd shall be 1 from edge E0+10N until the edge after which the next accepted frame starts. *(when: no byte accepted at edge E0+10N)* | keep |
| UL-7.3-05 | REQ-TX-014 | MUST | slave | assertion | o_txd shall be 1 while the transmitter is idle. *(when: transmitter idle)* | keep |
| UL-7.4-01 | REQ-RX-001 | MUST | slave | scenario | i_rxd shall pass through a synchronizer of exactly two flip-flops clocked by i_clk, with no logic between them, before other logic uses it. | keep |
| UL-7.4-02 | REQ-RX-002, REQ-RX-005, REQ-RX-013 | MUST | slave | scenario | The receiver shall be either idle or receiving, and shall be idle after reset, after a glitch and after the stop-bit sample of a frame. | keep |
| UL-7.4-03 | REQ-RX-003 | MUST | slave | both | The receiver shall detect a start bit at edge T0 if and only if s(T0-1)=1 and s(T0)=0. *(when: receiver idle)* | keep |
| UL-7.4-04 | REQ-RX-004 | MUST_NOT | slave | scenario | The receiver shall not need the line high longer than the single sample s(T0-1)=1 before a start bit. | keep |
| UL-7.4-05 | REQ-RX-005 | MUST | slave | both | At T0+H the receiver shall check the start bit; if s(T0+H)=1 it shall treat it as a glitch, return to idle and receive no byte. *(when: start bit detected at T0)* | keep |
| UL-7.4-06 | REQ-RX-006 | MUST_NOT | slave | assertion | A glitch shall not change o_rx_valid, o_rx_data or o_rx_frame_err, and shall not make o_rx_overrun pulse. *(when: glitch)* | keep |
| UL-7.4-07 | REQ-RX-003, REQ-RX-007 | MUST | slave | scenario | The receiver shall detect a new start bit at any edge T0' > T0+H at which the start condition holds. *(when: after a glitch checked at T0+H)* | keep |
| UL-7.4-08 | REQ-RX-008 | MUST | slave | scenario | The receiver shall go on to receive the frame. *(when: s(T0+H)=0)* | keep |
| UL-7.5-01 | REQ-RX-010 | MUST | slave | both | Data bit i (0 to 7) shall be sampled at edge T0+H+(i+1)N, and received byte bit i shall equal s(T0+H+(i+1)N). *(when: frame detected at T0 and confirmed at T0+H)* | keep |
| UL-7.5-02 | REQ-RX-011 | MUST | slave | both | The receiver shall sample the stop bit at edge M = T0+H+9N. | keep |
| UL-7.5-03 | REQ-RX-012 | MUST | slave | scenario | Only s(T0-1), s(T0), s(T0+H), the eight data samples and s(M) shall affect a frame result; i_rxd at other edges between T0 and M shall be ignored. | keep |
| UL-7.5-04 | REQ-RX-003, REQ-RX-013 | MUST | slave | scenario | The receiver shall be idle after sampling at M and shall detect a new start bit at any T0' > M where the start condition holds, including M+1. *(when: after stop-bit sample at M)* | keep |
| UL-7.5-05 | REQ-RX-014 | MUST | slave | scenario | Every confirmed frame shall complete at M regardless of the value of s(M). *(when: frame confirmed at T0+H)* | keep |
| UL-7.5-06 | REQ-RX-015 | MUST | slave | scenario | The receiver shall keep sampling and receiving frames; a low i_rx_ready shall not stall or delay it. *(when: byte waiting in holding register)* | keep |
| UL-7.6-01 | REQ-RX-020 | MUST | slave | assertion | The block shall load the frame: o_rx_valid becomes 1, o_rx_data the received byte, o_rx_frame_err the inverse of s(M). *(when: at delivery edge V=M+2 with o_rx_valid=0)* | keep |
| UL-7.6-02 | REQ-RX-021 | MUST | slave | assertion | The held byte shall be taken and the new frame loaded at the same edge; o_rx_valid stays 1 and no overrun is reported. *(when: at delivery edge V with o_rx_valid=1 and i_rx_ready=1)* | keep |
| UL-7.6-03 | REQ-RX-022, REQ-RX-023 | MUST | slave | assertion | o_rx_valid shall become 0 at that edge. *(when: held byte taken (o_rx_valid=1, i_rx_ready=1, i_rst_n=1) and no new byte loaded)* | keep |
| UL-7.6-04 | REQ-RX-024 | MUST | slave | assertion | o_rx_valid, o_rx_data and o_rx_frame_err shall keep their values. *(when: o_rx_valid=1 and byte not taken)* | keep |
| UL-7.6-05 | REQ-RX-025 | MUST | slave | assertion | o_rx_data and o_rx_frame_err shall change only when a new byte is loaded or on reset, keeping the last loaded values (0 after reset) while o_rx_valid=0. | keep |
| UL-7.6-06 | REQ-RX-026 | MUST_NOT | slave | assertion | i_rx_ready shall have no effect while o_rx_valid=0. *(when: o_rx_valid=0)* | keep |
| UL-7.6-07 | REQ-RX-027 | MUST | slave | scenario | Bytes shall be delivered in the order in which their frames completed. | keep |
| UL-7.7-01 | REQ-FE-001 | MUST | slave | assertion | o_rx_frame_err shall be 1 with a loaded byte if and only if s(M) of that frame was 0. *(when: byte loaded)* | keep |
| UL-7.7-02 | REQ-FE-002 | MUST | slave | scenario | The byte shall be delivered, held and taken like any other byte, and o_rx_data shall hold its sampled data bits. *(when: frame with frame error)* | keep |
| UL-7.7-03 | REQ-FE-003, REQ-RX-003 | MUST_NOT | slave | scenario | The receiver shall not detect a new start bit until s is 1 at one edge and 0 at the next, so a line held at 0 produces exactly one frame. *(when: after a frame with frame error)* | keep |
| UL-7.8-01 | REQ-OVR-001 | MUST | slave | assertion | The block shall drop the new byte and its frame-error flag. *(when: at delivery edge V with o_rx_valid=1 and i_rx_ready=0)* | keep |
| UL-7.8-02 | REQ-OVR-002 | MUST | slave | assertion | o_rx_overrun shall become 1 at edge V and return to 0 at V+1, being 1 for exactly one cycle. *(when: byte dropped at edge V)* | keep |
| UL-7.8-03 | REQ-OVR-003 | MUST | slave | assertion | o_rx_valid, o_rx_data and o_rx_frame_err shall keep the held byte unchanged. *(when: byte dropped)* | keep |
| UL-7.8-04 | REQ-OVR-004 | MUST | slave | assertion | o_rx_overrun shall be 0 in every cycle except the cycle after an edge at which a byte is dropped. | keep |
| UL-7.8-05 | REQ-OVR-005 | MUST_NOT | slave | assertion | o_rx_overrun shall not be qualified by o_rx_valid and shall not need a handshake. | keep |
| UL-7.8-06 | REQ-OVR-006 | MUST_NOT | slave | assertion | o_rx_overrun shall not pulse. *(when: glitch or frame cut short by reset)* | keep |
| UL-8.1-01 |  | MUST | master | assertion | The start bit must appear on o_txd in the first cycle after the accepting handshake edge E0. *(when: a byte is accepted at edge E0 (handshake))* | keep |
| UL-8.1-02 |  | MUST | master | assertion | The transmit frame must last 10N cycles, with the stop bit ending at edge E0+10N. *(when: a byte is accepted at edge E0)* | keep |
| UL-8.1-03 | REQ-TX-004, REQ-TX-005 | MUST | master | assertion | o_tx_ready must be 0 for 10N-1 cycles after E0 and become 1 in the last cycle of the stop bit. *(when: a byte is accepted at edge E0)* | keep |
| UL-8.1-04 |  | MUST_NOT | master | scenario | The block must never drop an offered byte while o_tx_ready = 0; the upstream block waits. *(when: o_tx_ready = 0 while a byte is offered)* | keep |
| UL-8.1-05 | REQ-TIM-001 | MUST | master | both | The transmitter must accept one byte every 10N cycles and produce a continuous stream of frames with no idle cycle between them. *(when: i_tx_valid is held at 1)* | keep |
| UL-8.1-06 | REQ-TIM-002 | MUST | master | scenario | Bytes must be sent on o_txd in the order in which they were accepted. | keep |
| UL-8.2-01 |  | MUST | slave | assertion | Delivery must occur at V = T0 + H + 9N + 2 edges, which is 2 edges after the stop-bit sample M. *(when: start bit detected at T0)* | keep |
| UL-8.2-03 | REQ-TIM-003 | MUST | slave | scenario | The receiver must accept frames back to back with no idle bit between them. *(when: a stop bit is followed at once by the next start bit, each bit N cycles long)* | keep |
| UL-8.4-01 |  | MUST | slave | both | After V, o_rx_overrun must be 1 for one cycle and the held byte must remain unchanged. *(when: at delivery V the holding register is full and i_rx_ready = 0)* | keep |
| UL-10.1-01 | REQ-FE-001, REQ-FE-002 | MUST | slave | both | When the stop-bit sample s(M) is 0, the byte is delivered with o_rx_frame_err = 1. *(when: stop-bit sample s(M) is 0)* | keep |
| UL-10.2-01 | REQ-OVR-001, REQ-OVR-003 | MUST | slave | both | The new byte is dropped, o_rx_overrun pulses for one cycle and the held byte stays. *(when: a frame completes at delivery edge V with o_rx_valid = 1 and i_rx_ready = 0)* | keep |
| UL-10.2-02 | REQ-RX-021 | MUST_NOT | slave | both | No overrun occurs if the held byte is taken at V itself. *(when: held byte is taken at delivery edge V itself)* | keep |
| UL-10.2-03 |  | MUST_NOT | slave | scenario | The frame-error flag of a dropped byte is not reported. *(when: byte dropped due to overrun)* | keep |
| UL-10.3-01 | REQ-RX-005, REQ-RX-006 | MUST | slave | both | On a start-bit glitch, no byte, no flag and no pulse is produced. *(when: s(T0+H) = 1 after a start-bit detection)* | keep |
| UL-10.3-02 |  | MUST | slave | scenario | A low pulse on i_rxd sampled at fewer than H+1 consecutive edges starting at T0 is always rejected. *(when: low pulse on i_rxd sampled at fewer than H+1 edges in a row, starting at T0)* | keep |
| UL-10.4-01 | REQ-ERR-001 | MUST | slave | scenario | The receiver delivers byte 0x00 with o_rx_frame_err = 1, or drops it with an overrun pulse under Section 7.8 rules. *(when: i_rxd stays 0 from a start bit through the whole frame)* | keep |
| UL-10.4-02 |  | MUST_NOT | slave | scenario | The receiver receives no further frame until the line has been sampled as 1 and then as 0. *(when: after a frame with i_rxd held low, until line sampled as 1 then 0)* | keep |
| UL-10.4-03 | REQ-ERR-002 | MUST | slave | both | The receiver stays idle and delivers nothing. *(when: i_rxd stays 1)* | keep |
| UL-10.5-01 | REQ-ERR-003, REQ-RST-010 | MUST | slave | scenario | The receiver detects R1 as T0 and processes the frame under Sections 7.4 to 7.8; a line staying low yields one byte 0x00 with o_rx_frame_err = 1. *(when: s(R1) = 0 at first edge R1 after release of i_rst_n)* | keep |
| UL-10.7-01 | REQ-ERR-004 | MUST_NOT | slave | both | The transmitter shall not accept the byte and shall not record it. *(when: i_tx_valid = 1 while o_tx_ready = 0)* | keep |
| UL-10.7-02 | REQ-ERR-005, REQ-RX-026 | MUST | slave | both | The block shall do nothing. *(when: i_rx_ready = 1 while o_rx_valid = 0)* | keep |
| UL-10.7-03 | REQ-ERR-006, REQ-GEN-002 | MUST | slave | both | Transmit handshake and receive delivery or take in the same cycle shall be handled independently. *(when: transmit handshake and receive delivery or take in the same cycle)* | keep |
| UL-10.8-01 | REQ-ERR-007 | MUST | slave | scenario | Bit-period and sample-offset counting shall not overflow or wrap early at N = 65535. *(when: N = 65535)* | keep |
| UL-10.8-02 | REQ-PAR-003 | MUST_NOT | system | none | Values of N outside 4 to 65535 are illegal and must not be used. | keep |
| UL-11-01 |  | MUST | system | scenario | CFG-MIN with PARA_UART_CLKS_PER_BIT=4 is the smallest legal bit period and must be verified for minimum sampling margins. *(when: PARA_UART_CLKS_PER_BIT=4 (CFG-MIN))* | keep |
| UL-12.1-01 |  | MUST | system | assertion | The environment shall release i_rst_n synchronously to i_clk, meeting recovery and removal times. *(when: when releasing reset (0 to 1))* | keep |
| UL-12.1-02 |  | MUST | system | assertion | The environment shall hold i_rst_n at 0 for at least 2 cycles of i_clk at the start of simulation. *(when: at the start of a simulation)* | keep |
| UL-12.1-03 |  | MUST | system | assertion | The environment shall drive i_tx_valid, i_tx_data and i_rx_ready synchronously to i_clk with no X or Z values. *(when: after release of i_rst_n)* | keep |
| UL-12.1-04 |  | MUST | system | assertion | The testbench shall change i_rxd away from rising edges of i_clk, e.g. on the falling edge or at a non-coincident random offset. *(when: in simulation)* | keep |
| UL-12.1-05 |  | MUST | system | assertion | i_rxd shall not be X or Z after reset release. *(when: after reset release)* | keep |
| UL-12.2-02 | REQ-RX-001 | MUST | system | none | The synchronizer structure (exactly two flip-flops, no logic between them, REQ-RX-001) shall be checked by lint or structural review. | keep |
| UL-12.2-04 |  | MUST | system | scenario | The reference model shall compute s(E) from i_rxd and apply Sections 7.4 to 7.8 exactly. | keep |
| UL-12.2-06 | REQ-TX-004, REQ-TX-005, REQ-TX-010 | MUST | system | assertion | The checker shall check REQ-TX-004, REQ-TX-005 and REQ-TX-010 cycle by cycle. | keep |
| UL-12.3-01 |  | MUST | system | scenario | Sampling-point test: drive i_rxd so each bit is correct only at its sampling edge T0+H+(i+1)N and M, wrong at edges just before and after. *(when: where N allows)* | keep |
| UL-12.3-02 |  | MUST | system | scenario | Glitch test: low pulses on i_rxd of 1 to H samples are rejected and H+1 samples are accepted as a start bit. | keep |
| UL-12.3-03 |  | MUST | system | scenario | Loopback test: connect o_txd to i_rxd and check the Section 8.5 latency and byte integrity. | keep |
| UL-12.3-04 |  | MUST | system | scenario | Reset tests: assert i_rst_n asynchronously between clock edges in mid-transmit frame, mid-receive frame and while o_rx_valid = 1. | keep |
| UL-12.3-05 | REQ-ERR-001, REQ-ERR-003 | MUST | system | scenario | Test line low at reset release (REQ-ERR-003) and break (REQ-ERR-001). | keep |
| UL-12.4-01 |  | MUST | system | scenario | Cover data bytes 0x00, 0xFF, 0x55, 0xAA and random bytes in both directions. | keep |
| UL-12.4-02 |  | MUST | system | scenario | Cover back-to-back transmit with i_tx_valid held at 1, and transmit with idle gaps of various lengths. | keep |
| UL-12.4-03 |  | MUST | system | scenario | Cover back-to-back receive frames with the next start bit right after the stop bit. | keep |
| UL-12.4-04 |  | MUST | system | scenario | Cover frame error with o_rx_valid = 0, and frame error with the byte dropped by overrun. | keep |
| UL-12.4-05 |  | MUST | system | scenario | Cover overrun, and the case where the held byte is taken at delivery edge V itself (no overrun). | keep |
| UL-12.4-06 |  | MUST | system | scenario | Cover i_rx_ready held at 1, toggling at random, and held at 0 for several frames. | keep |
| UL-12.4-07 |  | MUST | system | scenario | Cover i_tx_valid dropping before a handshake. | keep |
| UL-12.4-08 |  | MUST | system | scenario | Cover transmit and receive active at the same time. | keep |
| UL-13-01 | REQ-IMP-001 | MUST | system | none | The block shall meet timing at 50 MHz (20 ns period) on GF180MCU for every legal value of PARA_UART_CLKS_PER_BIT. *(when: for every legal value of PARA_UART_CLKS_PER_BIT)* | keep |
| UL-13-02 | REQ-IMP-002 | MUST | system | none | The RTL shall follow docs/RTL_RULES.md. | keep |
| UL-13-03 | REQ-IMP-003 | MUST | system | none | The RTL shall be synthesizable, contain no latches and pass Verilator lint with no warnings. | keep |
| UL-13-04 | REQ-IMP-004 | MUST | system | none | All flip-flops shall use the asynchronous active-low reset i_rst_n. | fix: check scenario->none |
| UL-13-05 | REQ-IMP-005 | SHOULD | system | none | The two i_rxd synchronizer flip-flops should be marked so synthesis does not merge, duplicate or retime them. | keep |
| UL-13-06 | REQ-IMP-006 | SHOULD | system | none | The bit-period counters should be only as wide as PARA_UART_CLKS_PER_BIT needs, at most 16 bits. | keep |
| UL-13-07 |  | SHOULD | system | none | The block should use only the storage the specification requires: transmit shift register, receive shift register, holding register, counters and flags. | keep |
| UL-14-01 | REQ-RST-003 | MUST | slave | assertion | o_tx_ready must be 1 (its idle value) while i_rst_n = 0, since no handshake is possible during reset. *(when: while i_rst_n = 0)* | keep |
| UL-14-02 |  | MUST | slave | scenario | The receiver samples the middle of each bit H = floor(N/2) edges after T0, then every N edges. *(when: receiving a frame after start detection at T0)* | keep |
| UL-14-03 |  | MUST | slave | both | o_rx_valid is delivered at V = M + 2, where M is the sample edge of i_rxd and 2 is the synchronizer latency. *(when: stop bit sampled at edge M)* | keep |
| UL-14-04 |  | MUST | slave | scenario | The new byte is loaded and no overrun occurs. *(when: held byte is taken at the same edge at which a new byte completes)* | keep |
| UL-14-05 |  | MUST | slave | scenario | A new start requires a 1-to-0 transition on i_rxd, so a break yields only one byte. *(when: after a frame error with the line still low)* | keep |
| UL-14-06 |  | MUST | slave | scenario | The synchronizer resets to 1; a low i_rxd at reset release is detected as a start bit. *(when: reset and reset release)* | keep |
| UL-14-07 |  | MUST | slave | assertion | o_rx_data and o_rx_frame_err keep the last loaded values, and are 0 after reset. *(when: while o_rx_valid = 0)* | keep |
| UL-14-08 |  | MUST | slave | both | The frame is abandoned, o_txd goes to 1 at once and the byte is lost. *(when: reset asserted during a transmission)* | keep |
| UL-14-09 |  | MUST_NOT | slave | scenario | The frame-error flag of a dropped byte is not reported. *(when: a byte is dropped)* | keep |
| UL-14-10 |  | SHOULD | system | none | An elaboration error should be raised for illegal parameter values; this is not verified. *(when: illegal parameter values)* | keep |
| UL-14-11 |  | MUST | system | scenario | CFG-ODD (5) and CFG-WIDE (1024) are simulated; CFG-MAX (65535) is not simulated and is covered by elaboration and synthesis only. *(when: configurations beyond default and minimum)* | keep |
| UL-14-12 |  | MUST_NOT | system | none | No area budget is required for GF180MCU; area is reported, not checked. | keep |
| UL-14-13 |  | MUST | system | none | The 50 MHz target applies at the slow corner (GF180MCU SS, 125 C, 4.5 V). *(when: 50 MHz target)* | keep |

## Rejected

| ID | Statement | Reason |
|---|---|---|
| UL-1.1-03 | The transmit byte stream uses a valid/ready handshake on i_tx_valid, o_tx_ready and i_tx_data. | Only a description of interface signals; no specific verifiable behaviour beyond naming a handshake. |
| UL-1.1-04 | The receive byte stream uses a valid/ready handshake on o_rx_valid, i_rx_ready, o_rx_data and o_rx_frame_err. | Only a description of interface signals; also lists o_rx_frame_err in the handshake without stating behaviour. |
| UL-1.2-03 | The only transmit storage is the shift register, with no additional transmit buffering. | Structural description (storage), nothing to verify or exercise. |
| UL-1.2-06 | The asynchronous input i_rxd passes through a two-flip-flop synchronizer. | Structural description of a synchronizer; nothing observable to verify at interface (and 1.3-01 says not checked). |
| UL-1.3-01 | The synchronizer must be present by structure; its metastability behaviour is not checked in simulation. | Statement about what is not checked in simulation; nothing to verify or exercise. |
| UL-8.2-02 | The receiver must detect a start bit at the smallest spacing of H + 9N + 1 cycles, so a slightly fast transmitter is accepted. | Quote describes the smallest spacing between detected start bits as a property and tolerance consequence; it is descriptive, and the rule's 'must detect start bit at smallest spacing' is not what the quote states precisely. |
| UL-9-01 | The block must not provide any software-visible registers. | The quote only describes the block (it has no software-visible registers). It gives no behaviour to verify and nothing to exercise, because there is no register interface to check. It is a description, not a testable MUST_NOT requirement. |
| UL-11-02 | The largest legal PARA_UART_CLKS_PER_BIT value (65535) is covered by elaboration and synthesis only, not by simulation; CFG-WIDE uses 1024. | Describes coverage scope (elaboration/synthesis only, not simulation); nothing to verify or exercise in simulation. CFG-WIDE=1024 is just a config description. |
| UL-12.1-06 | The environment need not keep i_tx_valid or i_tx_data stable before a handshake, and may assert i_rx_ready at any time. | ENV-005 says the environment has no obligation. It places no requirement to verify, so it is only a description. There is nothing to check, though a scenario could exercise it. |
| UL-12.2-01 | The synchronizer depth is observable at the ports only as the fixed latency V = M + 2. | Only a description of observability. It gives no testable requirement beyond the latency V, which is defined elsewhere. |
| UL-12.2-03 | The receiver idle/receiving condition and sampling edges are observable only through delivered bytes, flags and pulses. | Only a description of observability, with nothing to verify. |
| UL-12.2-05 | Transmit timing is fully observable on o_txd and o_tx_ready. | Only a description of observability, with nothing to verify. |

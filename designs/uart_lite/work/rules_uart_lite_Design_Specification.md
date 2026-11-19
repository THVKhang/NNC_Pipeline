# Extracted rules - uart_lite_Design_Specification.md

```
rules: 168  by strength {'MUST': 141, 'SHOULD': 5, 'MUST_NOT': 21, 'MAY': 1}  by check {'both': 35, 'none': 19, 'scenario': 71, 'assertion': 43}
normative sentences: 114  cited 113  skipped 1  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 15 (0 from cache)  cost US$0.4286  tokens in 61852 out 22082
```


## 1.1 Purpose

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-1.1-01 | MUST | system | both | Serial frames use 8N1: one start bit (0), eight data bits LSB first, no parity, one stop bit (1). | 1.1:s2, 1.2:s1 (p8) |
| UL-1.1-02 | MUST | system | both | Each bit period lasts PARA_UART_CLKS_PER_BIT i_clk cycles. | 1.1:s3, 1.2:s3 (p8) |
| UL-1.1-03 | MUST | system | both | The transmit byte stream uses a valid/ready handshake on i_tx_valid, o_tx_ready and i_tx_data. | 1.1:s4, 1.2:s5 (p8) |
| UL-1.1-04 | MUST | system | both | The receive byte stream uses a valid/ready handshake on o_rx_valid, i_rx_ready, o_rx_data and o_rx_frame_err. | 1.1:s4, 1.2:s8 (p8) |

## 1.2 Features

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-1.2-01 | MUST | system | both | The serial line is held high when idle. *(when: When the serial line is idle)* | 1.2:s2 (p11) |
| UL-1.2-02 | MUST | system | none | PARA_UART_CLKS_PER_BIT is fixed at elaboration and must be within the legal range 4 to 65535. | 1.2:s4 (p12) |
| UL-1.2-03 | MUST | system | none | The only transmit storage is the shift register, with no additional transmit buffering. | 1.2:s6 (p13) |
| UL-1.2-04 | MUST | system | both | No idle bit is inserted between the stop bit and the next start bit. *(when: When bytes are sent back to back)* | 1.2:s7 (p14) |
| UL-1.2-05 | MUST | system | both | A one-byte holding register keeps each received byte until it is taken. *(when: After a byte is received)* | 1.2:s9 (p15) |
| UL-1.2-06 | MUST | system | none | The asynchronous input i_rxd passes through a two-flip-flop synchronizer. | 1.2:s10 (p16) |
| UL-1.2-07 | MUST | system | scenario | The receiver detects a start bit on a falling edge and rechecks the start bit in the middle of the bit, rejecting glitches. | 1.2:s11 (p17) |
| UL-1.2-08 | MUST | system | scenario | The receiver samples each data bit and the stop bit in the middle of the bit. | 1.2:s11 (p17) |
| UL-1.2-09 | MUST | system | both | o_rx_frame_err is set and delivered together with the received byte. *(when: When the stop bit is sampled as 0)* | 1.2:s12 (p18) |
| UL-1.2-10 | MUST | system | both | o_rx_overrun pulses. *(when: When a received byte is dropped because the previous byte has not been taken)* | 1.2:s13 (p19) |
| UL-1.2-11 | MUST | system | scenario | The transmitter and receiver operate simultaneously and independently of each other (full duplex). | 1.2:s14 (p20) |

## 1.3 Out of scope

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-1.3-01 | MUST | system | none | The synchronizer must be present by structure; its metastability behaviour is not checked in simulation. | 1.3:s9 (p30) |

## 4 Parameters

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-4-01 | MUST | system | scenario | PARA_UART_CLKS_PER_BIT defines the bit period N in i_clk cycles for both transmitter and receiver, default 16, legal range 4 to 65535. | 4:s1 (p66) |
| UL-4-02 | MUST | system | both | LPARA_UART_HALF_BIT shall equal floor(PARA_UART_CLKS_PER_BIT / 2), the middle-of-bit sampling offset H, using integer division. | 4:s2, 4:s4 (p67) |
| UL-4-03 | MUST | system | scenario | The block shall behave as specified for every PARA_UART_CLKS_PER_BIT value from 4 to 65535, both odd and even. *(when: PARA_UART_CLKS_PER_BIT is any value from 4 to 65535 inclusive, odd or even)* | 4:s3 (p69) |
| UL-4-04 | SHOULD | system | none | The block should stop elaboration with an error message when PARA_UART_CLKS_PER_BIT is outside 4 to 65535. *(when: PARA_UART_CLKS_PER_BIT is less than 4 or greater than 65535)* | 4:s5 (p73) |

## 5 Interface

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-5-01 | MUST | system | scenario | i_rst_n is an active-low reset that asserts asynchronously and releases synchronously to i_clk. *(when: i_rst_n is asserted (low))* | 5:s3 (p82) |
| UL-5-02 | MUST | slave | scenario | When o_tx_ready is 1, the transmitter must accept the byte on i_tx_data at the next i_clk edge. *(when: o_tx_ready is high and i_tx_valid is high at a clock edge)* | 5:s4, 5:s5 (p83) |
| UL-5-03 | MUST | slave | assertion | o_tx_ready must reset to 1. *(when: after reset)* | 5:s5 (p84) |
| UL-5-04 | MUST | source | scenario | Bit 0 of i_tx_data must be sent first on o_txd. *(when: transmitting a byte)* | 5:s6 (p85) |
| UL-5-05 | MUST | destination | assertion | o_rx_valid must reset to 0. *(when: after reset)* | 5:s7 (p86) |
| UL-5-06 | MUST | destination | scenario | o_rx_valid must be 1 when the holding register holds a byte. *(when: holding register holds a byte)* | 5:s7 (p86) |
| UL-5-07 | MUST | destination | scenario | The held byte is taken by the consumer at the edge where i_rx_ready is 1. *(when: i_rx_ready is high at a clock edge with o_rx_valid high)* | 5:s8 (p87) |
| UL-5-08 | MUST | destination | assertion | o_rx_data must reset to 0. *(when: after reset)* | 5:s9 (p88) |
| UL-5-09 | MUST | destination | scenario | o_rx_data must present the received byte with bit 0 received first, qualified by o_rx_valid. *(when: o_rx_valid is high)* | 5:s9 (p88) |
| UL-5-10 | MUST | destination | assertion | o_rx_frame_err must reset to 0. *(when: after reset)* | 5:s10 (p89) |
| UL-5-11 | MUST | destination | scenario | o_rx_frame_err must be 1 when the stop bit of the held byte was sampled as 0, qualified by o_rx_valid. *(when: o_rx_valid is high)* | 5:s10 (p89) |
| UL-5-12 | MUST | destination | assertion | o_rx_overrun must reset to 0. *(when: after reset)* | 5:s11 (p90) |
| UL-5-13 | MUST | destination | both | o_rx_overrun must pulse for one cycle when a received byte is dropped because the holding register is full. *(when: a received byte is dropped because the holding register is full)* | 5:s11 (p90) |
| UL-5-14 | MUST | source | assertion | o_txd must reset to 1 and be high when idle. *(when: after reset or idle)* | 5:s12 (p91) |
| UL-5-15 | MUST | destination | scenario | i_rxd, asynchronous to i_clk and idle high, must be synchronised inside the block. | 5:s13 (p92) |

## 6.1 Clocks

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-6.1-01 | MUST | system | none | All state elements shall be clocked only by the rising edge of i_clk, with no other clock, no gated clock and no latch. | 6.1:s7 (p99) |

## 6.2 Resets

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-6.2-01 | MUST | system | assertion | Every flip-flop shall take its reset value at once, without waiting for an i_clk edge. *(when: When i_rst_n becomes 0)* | 6.2:s4 (p104) |
| UL-6.2-02 | MUST | system | assertion | Outputs shall be o_txd = 1, o_tx_ready = 1, o_rx_valid = 0, o_rx_data = 0, o_rx_frame_err = 0, o_rx_overrun = 0. *(when: While i_rst_n is 0)* | 6.2:s5 (p106) |
| UL-6.2-03 | MUST_NOT | system | both | No transmit byte shall be accepted. *(when: While i_rst_n is 0, even when i_tx_valid = 1 and o_tx_ready = 1)* | 6.2:s6 (p108) |
| UL-6.2-04 | MUST_NOT | system | both | The receiver shall not detect a start bit and shall not deliver a byte. *(when: While i_rst_n is 0)* | 6.2:s7 (p110) |
| UL-6.2-05 | MUST | system | scenario | Both i_rxd synchronizer flip-flops and any flip-flop holding the previous synchronised line value shall reset to 1. *(when: On reset)* | 6.2:s8 (p112) |
| UL-6.2-06 | MUST | system | both | The frame shall be abandoned and o_txd shall become 1 at once. *(when: Reset asserted during a transmission)* | 6.2:s9 (p114) |
| UL-6.2-07 | MUST_NOT | system | scenario | The rest of the frame and the byte shall not be sent after the release. *(when: Reset asserted during a transmission)* | 6.2:s9 (p114) |
| UL-6.2-08 | MUST | system | scenario | The partly received frame shall be discarded and shall not produce o_rx_valid, o_rx_frame_err or o_rx_overrun after the release. *(when: Reset asserted during a reception)* | 6.2:s10 (p116) |
| UL-6.2-09 | MUST | system | scenario | The held byte shall be discarded. *(when: Reset asserted while o_rx_valid = 1)* | 6.2:s11 (p118) |
| UL-6.2-10 | MUST | system | both | The transmitter shall be idle with o_tx_ready = 1 and shall accept a byte at the first edge after the release. *(when: After release of i_rst_n)* | 6.2:s12 (p120) |
| UL-6.2-11 | MUST | system | scenario | The receiver shall be idle. *(when: After release of i_rst_n)* | 6.2:s13 (p122) |
| UL-6.2-12 | MUST | system | scenario | The previous synchronised value s(R1-1) shall be taken as 1, so s(R1) = 0 is detected as T0. *(when: First edge R1 after reset release)* | 6.2:s14, 6.2:s15 (p122) |

## 7.1 General

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-7.1-01 | MUST | system | both | Frames shall be sent and received in 8N1 format: start bit 0, eight data bits LSB first, stop bit 1, no parity bit. | 7.1:s1 (p128) |
| UL-7.1-02 | MUST | system | scenario | The transmitter and receiver shall operate simultaneously and independently. | 7.1:s2 (p130) |
| UL-7.1-03 | MUST_NOT | system | scenario | Activity of the transmitter shall not change the timing or outputs of the receiver, and vice versa. | 7.1:s3 (p130) |
| UL-7.1-04 | MUST | system | both | Every output port shall be driven directly by a flip-flop clocked by i_clk, with no combinational path from any input to any output. | 7.1:s4 (p132) |

## 7.2 Transmit stream interface

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-7.2-01 | MUST | slave | assertion | The transmitter shall accept a byte at an edge only when i_tx_valid = 1, o_tx_ready = 1 and i_rst_n = 1. *(when: at a clock edge)* | 7.2:s1 (p136) |
| UL-7.2-02 | MUST | slave | both | The transmitter shall capture i_tx_data at the accepting edge E0; i_tx_data at any other edge shall have no effect. *(when: accepting edge E0)* | 7.2:s2, 7.2:s3 (p138) |
| UL-7.2-03 | MUST | slave | assertion | o_tx_ready shall be 1 while the transmitter is idle. *(when: transmitter idle, no frame in progress)* | 7.2:s4 (p140) |
| UL-7.2-04 | MUST | slave | assertion | o_tx_ready shall be 0 in the cycles after edges E0 to E0+10N-2 inclusive. *(when: after accepting edge E0)* | 7.2:s5 (p142) |
| UL-7.2-05 | MUST | slave | assertion | o_tx_ready shall become 1 at edge E0+10N-1, the last cycle of the stop bit. *(when: after accepting edge E0)* | 7.2:s6 (p144) |
| UL-7.2-06 | MUST_NOT | slave | both | The transmitter shall not accept a byte and its state shall not depend on i_tx_data. *(when: i_tx_valid is 0 or o_tx_ready is 0 at an edge)* | 7.2:s7 (p146) |
| UL-7.2-07 | MUST_NOT | slave | scenario | The transmitter shall not require i_tx_valid to stay 1 until a handshake; if it returns to 0 before a handshake, nothing is sent. | 7.2:s8, 7.2:s9 (p148) |
| UL-7.2-08 | MUST | slave | scenario | The transmitter shall hold at most one byte, the one being sent, with no additional transmit buffer. | 7.2:s10 (p150) |

## 7.3 Transmit serial frame

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-7.3-01 | MUST | slave | assertion | o_txd in the cycle after edge E0+k shall equal frame bit floor(k/N) of D (bit0=0, bit j=D[j-1], bit9=1) for k from 0 to 10N-1. *(when: byte D accepted at edge E0)* | 7.3:s1, 7.3:s2 (p154) |
| UL-7.3-02 | MUST | slave | assertion | Each of the 10 frame bits shall be driven on o_txd for exactly N consecutive cycles. | 7.3:s3 (p158) |
| UL-7.3-03 | MUST | slave | assertion | The start bit of the new frame shall begin at edge E0+10N with no idle cycle after the previous stop bit. *(when: new byte accepted at edge E0+10N)* | 7.3:s4 (p160) |
| UL-7.3-04 | MUST | slave | assertion | o_txd shall be 1 from edge E0+10N until the edge after which the next accepted frame starts. *(when: no byte accepted at edge E0+10N)* | 7.3:s5 (p162) |
| UL-7.3-05 | MUST | slave | assertion | o_txd shall be 1 while the transmitter is idle. *(when: transmitter idle)* | 7.3:s6 (p164) |

## 7.4 Receive line synchronisation and start detection

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-7.4-01 | MUST | slave | scenario | i_rxd shall pass through a synchronizer of exactly two flip-flops clocked by i_clk, with no logic between them, before other logic uses it. | 7.4:s1 (p168) |
| UL-7.4-02 | MUST | slave | scenario | The receiver shall be either idle or receiving, and shall be idle after reset, after a glitch and after the stop-bit sample of a frame. | 7.4:s2, 7.4:s3 (p170) |
| UL-7.4-03 | MUST | slave | both | The receiver shall detect a start bit at edge T0 if and only if s(T0-1)=1 and s(T0)=0. *(when: receiver idle)* | 7.4:s4 (p172) |
| UL-7.4-04 | MUST_NOT | slave | scenario | The receiver shall not need the line high longer than the single sample s(T0-1)=1 before a start bit. | 7.4:s5 (p174) |
| UL-7.4-05 | MUST | slave | both | At T0+H the receiver shall check the start bit; if s(T0+H)=1 it shall treat it as a glitch, return to idle and receive no byte. *(when: start bit detected at T0)* | 7.4:s6, 7.4:s7 (p176) |
| UL-7.4-06 | MUST_NOT | slave | assertion | A glitch shall not change o_rx_valid, o_rx_data or o_rx_frame_err, and shall not make o_rx_overrun pulse. *(when: glitch)* | 7.4:s8 (p178) |
| UL-7.4-07 | MUST | slave | scenario | The receiver shall detect a new start bit at any edge T0' > T0+H at which the start condition holds. *(when: after a glitch checked at T0+H)* | 7.4:s9 (p180) |
| UL-7.4-08 | MUST | slave | scenario | The receiver shall go on to receive the frame. *(when: s(T0+H)=0)* | 7.4:s10 (p182) |

## 7.5 Receive sampling and byte assembly

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-7.5-01 | MUST | slave | both | Data bit i (0 to 7) shall be sampled at edge T0+H+(i+1)N, and received byte bit i shall equal s(T0+H+(i+1)N). *(when: frame detected at T0 and confirmed at T0+H)* | 7.5:s1, 7.5:s2 (p186) |
| UL-7.5-02 | MUST | slave | both | The receiver shall sample the stop bit at edge M = T0+H+9N. | 7.5:s3 (p188) |
| UL-7.5-03 | MUST | slave | scenario | Only s(T0-1), s(T0), s(T0+H), the eight data samples and s(M) shall affect a frame result; i_rxd at other edges between T0 and M shall be ignored. | 7.5:s4, 7.5:s5 (p190) |
| UL-7.5-04 | MUST | slave | scenario | The receiver shall be idle after sampling at M and shall detect a new start bit at any T0' > M where the start condition holds, including M+1. *(when: after stop-bit sample at M)* | 7.5:s6, 7.5:s7 (p192) |
| UL-7.5-05 | MUST | slave | scenario | Every confirmed frame shall complete at M regardless of the value of s(M). *(when: frame confirmed at T0+H)* | 7.5:s8 (p194) |
| UL-7.5-06 | MUST | slave | scenario | The receiver shall keep sampling and receiving frames; a low i_rx_ready shall not stall or delay it. *(when: byte waiting in holding register)* | 7.5:s9, 7.5:s10 (p196) |

## 7.6 Receive stream interface

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-7.6-01 | MUST | slave | assertion | The block shall load the frame: o_rx_valid becomes 1, o_rx_data the received byte, o_rx_frame_err the inverse of s(M). *(when: at delivery edge V=M+2 with o_rx_valid=0)* | 7.6:s1 (p200) |
| UL-7.6-02 | MUST | slave | assertion | The held byte shall be taken and the new frame loaded at the same edge; o_rx_valid stays 1 and no overrun is reported. *(when: at delivery edge V with o_rx_valid=1 and i_rx_ready=1)* | 7.6:s2 (p202) |
| UL-7.6-03 | MUST | slave | assertion | o_rx_valid shall become 0 at that edge. *(when: held byte taken (o_rx_valid=1, i_rx_ready=1, i_rst_n=1) and no new byte loaded)* | 7.6:s3, 7.6:s4 (p204) |
| UL-7.6-04 | MUST | slave | assertion | o_rx_valid, o_rx_data and o_rx_frame_err shall keep their values. *(when: o_rx_valid=1 and byte not taken)* | 7.6:s5 (p208) |
| UL-7.6-05 | MUST | slave | assertion | o_rx_data and o_rx_frame_err shall change only when a new byte is loaded or on reset, keeping the last loaded values (0 after reset) while o_rx_valid=0. | 7.6:s6, 7.6:s7 (p210) |
| UL-7.6-06 | MUST_NOT | slave | assertion | i_rx_ready shall have no effect while o_rx_valid=0. *(when: o_rx_valid=0)* | 7.6:s8 (p212) |
| UL-7.6-07 | MUST | slave | scenario | Bytes shall be delivered in the order in which their frames completed. | 7.6:s9 (p214) |

## 7.7 Frame error

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-7.7-01 | MUST | slave | assertion | o_rx_frame_err shall be 1 with a loaded byte if and only if s(M) of that frame was 0. *(when: byte loaded)* | 7.7:s1 (p218) |
| UL-7.7-02 | MUST | slave | scenario | The byte shall be delivered, held and taken like any other byte, and o_rx_data shall hold its sampled data bits. *(when: frame with frame error)* | 7.7:s2 (p220) |
| UL-7.7-03 | MUST_NOT | slave | scenario | The receiver shall not detect a new start bit until s is 1 at one edge and 0 at the next, so a line held at 0 produces exactly one frame. *(when: after a frame with frame error)* | 7.7:s3 (p222) |

## 7.8 Overrun

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-7.8-01 | MUST | slave | assertion | The block shall drop the new byte and its frame-error flag. *(when: at delivery edge V with o_rx_valid=1 and i_rx_ready=0)* | 7.8:s1 (p226) |
| UL-7.8-02 | MUST | slave | assertion | o_rx_overrun shall become 1 at edge V and return to 0 at V+1, being 1 for exactly one cycle. *(when: byte dropped at edge V)* | 7.8:s2 (p228) |
| UL-7.8-03 | MUST | slave | assertion | o_rx_valid, o_rx_data and o_rx_frame_err shall keep the held byte unchanged. *(when: byte dropped)* | 7.8:s3 (p230) |
| UL-7.8-04 | MUST | slave | assertion | o_rx_overrun shall be 0 in every cycle except the cycle after an edge at which a byte is dropped. | 7.8:s4 (p232) |
| UL-7.8-05 | MUST_NOT | slave | assertion | o_rx_overrun shall not be qualified by o_rx_valid and shall not need a handshake. | 7.8:s5 (p234) |
| UL-7.8-06 | MUST_NOT | slave | assertion | o_rx_overrun shall not pulse. *(when: glitch or frame cut short by reset)* | 7.8:s6 (p236) |

## 8.1 Transmit latency and throughput

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-8.1-01 | MUST | master | assertion | The start bit must appear on o_txd in the first cycle after the accepting handshake edge E0. *(when: a byte is accepted at edge E0 (handshake))* | 8.1:s1 (p242) |
| UL-8.1-02 | MUST | master | assertion | The transmit frame must last 10N cycles, with the stop bit ending at edge E0+10N. *(when: a byte is accepted at edge E0)* | 8.1:s2, 8.1:s3 (p243) |
| UL-8.1-03 | MUST | master | assertion | o_tx_ready must be 0 for 10N-1 cycles after E0 and become 1 in the last cycle of the stop bit. *(when: a byte is accepted at edge E0)* | 8.1:s4 (p244) |
| UL-8.1-04 | MUST_NOT | master | scenario | The block must never drop an offered byte while o_tx_ready = 0; the upstream block waits. *(when: o_tx_ready = 0 while a byte is offered)* | 8.1:s5 (p245) |
| UL-8.1-05 | MUST | master | both | The transmitter must accept one byte every 10N cycles and produce a continuous stream of frames with no idle cycle between them. *(when: i_tx_valid is held at 1)* | 8.1:s6 (p247) |
| UL-8.1-06 | MUST | master | scenario | Bytes must be sent on o_txd in the order in which they were accepted. | 8.1:s7 (p249) |

## 8.2 Receive latency and throughput

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-8.2-01 | MUST | slave | assertion | Delivery must occur at V = T0 + H + 9N + 2 edges, which is 2 edges after the stop-bit sample M. *(when: start bit detected at T0)* | 8.2:s1, 8.2:s2 (p253) |
| UL-8.2-02 | MUST | slave | scenario | The receiver must detect a start bit at the smallest spacing of H + 9N + 1 cycles, so a slightly fast transmitter is accepted. *(when: two start bits are spaced at least H + 9N + 1 cycles apart)* | 8.2:s3, 8.2:s4 (p254) |
| UL-8.2-03 | MUST | slave | scenario | The receiver must accept frames back to back with no idle bit between them. *(when: a stop bit is followed at once by the next start bit, each bit N cycles long)* | 8.2:s7 (p257) |

## 8.4 Receive example (N = 4, H = 2, received byte 0xA5, stop bit 1)

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-8.4-01 | MUST | slave | both | After V, o_rx_overrun must be 1 for one cycle and the held byte must remain unchanged. *(when: at delivery V the holding register is full and i_rx_ready = 0)* | 8.4:s15 (p300) |

## 9 Registers

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-9-01 | MUST_NOT | system | none | The block must not provide any software-visible registers. | 9:s1 (p307) |

## 10.1 Frame error

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-10.1-01 | MUST | slave | both | When the stop-bit sample s(M) is 0, the byte is delivered with o_rx_frame_err = 1. *(when: stop-bit sample s(M) is 0)* | 10.1:s1, 10.1:s2 (p312) |

## 10.2 Overrun

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-10.2-01 | MUST | slave | both | The new byte is dropped, o_rx_overrun pulses for one cycle and the held byte stays. *(when: a frame completes at delivery edge V with o_rx_valid = 1 and i_rx_ready = 0)* | 10.2:s1, 10.2:s2 (p315) |
| UL-10.2-02 | MUST_NOT | slave | both | No overrun occurs if the held byte is taken at V itself. *(when: held byte is taken at delivery edge V itself)* | 10.2:s3 (p315) |
| UL-10.2-03 | MUST_NOT | slave | scenario | The frame-error flag of a dropped byte is not reported. *(when: byte dropped due to overrun)* | 10.2:s4 (p315) |

## 10.3 Glitch on the start bit

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-10.3-01 | MUST | slave | both | On a start-bit glitch, no byte, no flag and no pulse is produced. *(when: s(T0+H) = 1 after a start-bit detection)* | 10.3:s1, 10.3:s2 (p318) |
| UL-10.3-02 | MUST | slave | scenario | A low pulse on i_rxd sampled at fewer than H+1 consecutive edges starting at T0 is always rejected. *(when: low pulse on i_rxd sampled at fewer than H+1 edges in a row, starting at T0)* | 10.3:s3 (p318) |

## 10.4 Line held low (break) and stuck line

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-10.4-01 | MUST | slave | scenario | The receiver delivers byte 0x00 with o_rx_frame_err = 1, or drops it with an overrun pulse under Section 7.8 rules. *(when: i_rxd stays 0 from a start bit through the whole frame)* | 10.4:s1 (p321) |
| UL-10.4-02 | MUST_NOT | slave | scenario | The receiver receives no further frame until the line has been sampled as 1 and then as 0. *(when: after a frame with i_rxd held low, until line sampled as 1 then 0)* | 10.4:s2 (p321) |
| UL-10.4-03 | MUST | slave | both | The receiver stays idle and delivers nothing. *(when: i_rxd stays 1)* | 10.4:s3 (p323) |

## 10.5 Line low at reset release

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-10.5-01 | MUST | slave | scenario | The receiver detects R1 as T0 and processes the frame under Sections 7.4 to 7.8; a line staying low yields one byte 0x00 with o_rx_frame_err = 1. *(when: s(R1) = 0 at first edge R1 after release of i_rst_n)* | 10.5:s1, 10.5:s2 (p326) |

## 10.7 Handshake corner cases

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-10.7-01 | MUST_NOT | slave | both | The transmitter shall not accept the byte and shall not record it. *(when: i_tx_valid = 1 while o_tx_ready = 0)* | 10.7:s1 (p332) |
| UL-10.7-02 | MUST | slave | both | The block shall do nothing. *(when: i_rx_ready = 1 while o_rx_valid = 0)* | 10.7:s3 (p334) |
| UL-10.7-03 | MUST | slave | both | Transmit handshake and receive delivery or take in the same cycle shall be handled independently. *(when: transmit handshake and receive delivery or take in the same cycle)* | 10.7:s4 (p336) |

## 10.8 Parameter extremes

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-10.8-01 | MUST | slave | scenario | Bit-period and sample-offset counting shall not overflow or wrap early at N = 65535. *(when: N = 65535)* | 10.8:s6 (p341) |
| UL-10.8-02 | MUST_NOT | system | none | Values of N outside 4 to 65535 are illegal and must not be used. | 10.8:s7 (p342) |

## 11 Configurations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-11-01 | MUST | system | scenario | CFG-MIN with PARA_UART_CLKS_PER_BIT=4 is the smallest legal bit period and must be verified for minimum sampling margins. *(when: PARA_UART_CLKS_PER_BIT=4 (CFG-MIN))* | 11:s2 (p349) |
| UL-11-02 | MUST | system | none | The largest legal PARA_UART_CLKS_PER_BIT value (65535) is covered by elaboration and synthesis only, not by simulation; CFG-WIDE uses 1024. *(when: PARA_UART_CLKS_PER_BIT=65535 (largest legal value))* | 11:s4 (p351) |

## 12.1 Environment obligations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-12.1-01 | MUST | system | assertion | The environment shall release i_rst_n synchronously to i_clk, meeting recovery and removal times. *(when: when releasing reset (0 to 1))* | 12.1:s1 (p356) |
| UL-12.1-02 | MUST | system | assertion | The environment shall hold i_rst_n at 0 for at least 2 cycles of i_clk at the start of simulation. *(when: at the start of a simulation)* | 12.1:s3 (p358) |
| UL-12.1-03 | MUST | system | assertion | The environment shall drive i_tx_valid, i_tx_data and i_rx_ready synchronously to i_clk with no X or Z values. *(when: after release of i_rst_n)* | 12.1:s4 (p360) |
| UL-12.1-04 | MUST | system | assertion | The testbench shall change i_rxd away from rising edges of i_clk, e.g. on the falling edge or at a non-coincident random offset. *(when: in simulation)* | 12.1:s5 (p362) |
| UL-12.1-05 | MUST | system | assertion | i_rxd shall not be X or Z after reset release. *(when: after reset release)* | 12.1:s5 (p362) |
| UL-12.1-06 | MAY | system | scenario | The environment need not keep i_tx_valid or i_tx_data stable before a handshake, and may assert i_rx_ready at any time. *(when: before a handshake)* | 12.1:s6 (p364) |

## 12.2 Observability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-12.2-01 | MUST | system | scenario | The synchronizer depth is observable at the ports only as the fixed latency V = M + 2. | 12.2:s1 (p367) |
| UL-12.2-02 | MUST | system | none | The synchronizer structure (exactly two flip-flops, no logic between them, REQ-RX-001) shall be checked by lint or structural review. | 12.2:s2 (p367) |
| UL-12.2-03 | MUST | system | scenario | The receiver idle/receiving condition and sampling edges are observable only through delivered bytes, flags and pulses. | 12.2:s3 (p368) |
| UL-12.2-04 | MUST | system | scenario | The reference model shall compute s(E) from i_rxd and apply Sections 7.4 to 7.8 exactly. | 12.2:s4 (p368) |
| UL-12.2-05 | MUST | system | scenario | Transmit timing is fully observable on o_txd and o_tx_ready. | 12.2:s5 (p369) |
| UL-12.2-06 | MUST | system | assertion | The checker shall check REQ-TX-004, REQ-TX-005 and REQ-TX-010 cycle by cycle. | 12.2:s6 (p369) |

## 12.3 Special setups

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-12.3-01 | MUST | system | scenario | Sampling-point test: drive i_rxd so each bit is correct only at its sampling edge T0+H+(i+1)N and M, wrong at edges just before and after. *(when: where N allows)* | 12.3:s1, 12.3:s2 (p372) |
| UL-12.3-02 | MUST | system | scenario | Glitch test: low pulses on i_rxd of 1 to H samples are rejected and H+1 samples are accepted as a start bit. | 12.3:s3 (p373) |
| UL-12.3-03 | MUST | system | scenario | Loopback test: connect o_txd to i_rxd and check the Section 8.5 latency and byte integrity. | 12.3:s4 (p374) |
| UL-12.3-04 | MUST | system | scenario | Reset tests: assert i_rst_n asynchronously between clock edges in mid-transmit frame, mid-receive frame and while o_rx_valid = 1. | 12.3:s5 (p375) |
| UL-12.3-05 | MUST | system | scenario | Test line low at reset release (REQ-ERR-003) and break (REQ-ERR-001). | 12.3:s6 (p376) |

## 12.4 Required coverage

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-12.4-01 | MUST | system | scenario | Cover data bytes 0x00, 0xFF, 0x55, 0xAA and random bytes in both directions. | 12.4:s1 (p379) |
| UL-12.4-02 | MUST | system | scenario | Cover back-to-back transmit with i_tx_valid held at 1, and transmit with idle gaps of various lengths. | 12.4:s2 (p380) |
| UL-12.4-03 | MUST | system | scenario | Cover back-to-back receive frames with the next start bit right after the stop bit. | 12.4:s3 (p381) |
| UL-12.4-04 | MUST | system | scenario | Cover frame error with o_rx_valid = 0, and frame error with the byte dropped by overrun. | 12.4:s4 (p382) |
| UL-12.4-05 | MUST | system | scenario | Cover overrun, and the case where the held byte is taken at delivery edge V itself (no overrun). | 12.4:s5 (p383) |
| UL-12.4-06 | MUST | system | scenario | Cover i_rx_ready held at 1, toggling at random, and held at 0 for several frames. | 12.4:s6 (p384) |
| UL-12.4-07 | MUST | system | scenario | Cover i_tx_valid dropping before a handshake. | 12.4:s7 (p385) |
| UL-12.4-08 | MUST | system | scenario | Cover transmit and receive active at the same time. | 12.4:s8 (p386) |

## 13 Implementation constraints

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-13-01 | MUST | system | none | The block shall meet timing at 50 MHz (20 ns period) on GF180MCU for every legal value of PARA_UART_CLKS_PER_BIT. *(when: for every legal value of PARA_UART_CLKS_PER_BIT)* | 13:s1 (p390) |
| UL-13-02 | MUST | system | none | The RTL shall follow docs/RTL_RULES.md. | 13:s2 (p392) |
| UL-13-03 | MUST | system | none | The RTL shall be synthesizable, contain no latches and pass Verilator lint with no warnings. | 13:s3 (p394) |
| UL-13-04 | MUST | system | scenario | All flip-flops shall use the asynchronous active-low reset i_rst_n. | 13:s4 (p396) |
| UL-13-05 | SHOULD | system | none | The two i_rxd synchronizer flip-flops should be marked so synthesis does not merge, duplicate or retime them. | 13:s5 (p398) |
| UL-13-06 | SHOULD | system | none | The bit-period counters should be only as wide as PARA_UART_CLKS_PER_BIT needs, at most 16 bits. | 13:s6 (p400) |
| UL-13-07 | SHOULD | system | none | The block should use only the storage the specification requires: transmit shift register, receive shift register, holding register, counters and flags. | 13:s8 (p402) |

## 14 Decisions and open questions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| UL-14-01 | MUST | slave | assertion | o_tx_ready must be 1 (its idle value) while i_rst_n = 0, since no handshake is possible during reset. *(when: while i_rst_n = 0)* | 14:s1 (p408) |
| UL-14-02 | MUST | slave | scenario | The receiver samples the middle of each bit H = floor(N/2) edges after T0, then every N edges. *(when: receiving a frame after start detection at T0)* | 14:s2 (p409) |
| UL-14-03 | MUST | slave | both | o_rx_valid is delivered at V = M + 2, where M is the sample edge of i_rxd and 2 is the synchronizer latency. *(when: stop bit sampled at edge M)* | 14:s3 (p410) |
| UL-14-04 | MUST | slave | scenario | The new byte is loaded and no overrun occurs. *(when: held byte is taken at the same edge at which a new byte completes)* | 14:s4 (p411) |
| UL-14-05 | MUST | slave | scenario | A new start requires a 1-to-0 transition on i_rxd, so a break yields only one byte. *(when: after a frame error with the line still low)* | 14:s5 (p412) |
| UL-14-06 | MUST | slave | scenario | The synchronizer resets to 1; a low i_rxd at reset release is detected as a start bit. *(when: reset and reset release)* | 14:s6 (p413) |
| UL-14-07 | MUST | slave | assertion | o_rx_data and o_rx_frame_err keep the last loaded values, and are 0 after reset. *(when: while o_rx_valid = 0)* | 14:s7 (p414) |
| UL-14-08 | MUST | slave | both | The frame is abandoned, o_txd goes to 1 at once and the byte is lost. *(when: reset asserted during a transmission)* | 14:s9 (p416) |
| UL-14-09 | MUST_NOT | slave | scenario | The frame-error flag of a dropped byte is not reported. *(when: a byte is dropped)* | 14:s10 (p417) |
| UL-14-10 | SHOULD | system | none | An elaboration error should be raised for illegal parameter values; this is not verified. *(when: illegal parameter values)* | 14:s11 (p418) |
| UL-14-11 | MUST | system | scenario | CFG-ODD (5) and CFG-WIDE (1024) are simulated; CFG-MAX (65535) is not simulated and is covered by elaboration and synthesis only. *(when: configurations beyond default and minimum)* | 14:s12 (p419) |
| UL-14-12 | MUST_NOT | system | none | No area budget is required for GF180MCU; area is reported, not checked. | 14:s13 (p420) |
| UL-14-13 | MUST | system | none | The 50 MHz target applies at the slow corner (GF180MCU SS, 125 C, 4.5 V). *(when: 50 MHz target)* | 14:s14 (p421) |

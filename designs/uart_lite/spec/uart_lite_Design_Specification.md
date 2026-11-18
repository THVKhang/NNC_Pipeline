# `uart_lite` Design Specification

Revision: `0.1`, `2026-11-17`. Top module: `m_uart_lite`.

## 1 Overview

### 1.1 Purpose
`uart_lite` is a small UART for a single-clock SoC. It sends and receives bytes on a serial line in 8N1 format. The bit period is a fixed number of `i_clk` cycles, set by a parameter. The system side has one valid/ready byte stream for transmit and one for receive.

### 1.2 Features
- 8N1 framing: one start bit (0), eight data bits with the least significant bit first, no parity, one stop bit (1). The line is high when idle.
- Bit period of `PARA_UART_CLKS_PER_BIT` clock cycles. The parameter is fixed at elaboration and its legal range is 4 to 65535.
- Transmit stream input (`i_tx_valid`, `o_tx_ready`, `i_tx_data`) with a valid/ready handshake. The only transmit storage is the shift register.
- Bytes sent back to back have no idle bit between the stop bit and the next start bit.
- Receive stream output (`o_rx_valid`, `i_rx_ready`, `o_rx_data`, `o_rx_frame_err`). A one-byte holding register keeps each received byte until it is taken.
- A two-flip-flop synchronizer on the asynchronous serial input `i_rxd`.
- Start-bit detection on a falling edge, a second start-bit check in the middle of the bit (glitch rejection), and sampling of every data bit and the stop bit in the middle of the bit.
- A frame error flag (stop bit sampled as 0), delivered together with the byte.
- An overrun pulse (`o_rx_overrun`) when a received byte is dropped because the previous byte has not been taken.
- Full duplex: the transmitter and the receiver work at the same time and do not depend on each other.

### 1.3 Out of scope
- Parity, 5/6/7-bit data, two stop bits and any other frame format.
- Changing the baud rate at run time, fractional baud-rate generation and automatic baud detection.
- Hardware flow control (RTS/CTS), XON/XOFF, and a separate break-detect output.
- Majority-vote or oversampling noise filtering beyond the single middle-of-bit sample and the start-bit check.
- Transmit or receive FIFOs deeper than the transmit shift register and the single receive holding register.
- Software-visible registers, a bus interface and interrupts.
- Any stated tolerance to baud-rate mismatch beyond what follows from the sampling points in Section 7.5.
- Metastability modelling. The synchronizer is required by structure, but its metastability behaviour is not checked in simulation.

## 2 References

| ID | Document | Revision | Used for |
|---|---|---|---|
| REF-001 | `uart_lite` design description (designer's input to `nnc spec-draft`) | 2026-11-17 | All functional requirements |
| REF-002 | `docs/RTL_RULES.md` | Current revision in the repository | Coding rules (Section 13) |
| REF-003 | GF180MCU process design kit and standard-cell library | Version used by the project flow | Target technology (Section 13) |

## 3 Terms

| Term | Meaning |
|---|---|
| N | Short name for `PARA_UART_CLKS_PER_BIT`, the bit period in `i_clk` cycles |
| H | Short name for `LPARA_UART_HALF_BIT` = floor(N / 2), the offset of the middle-of-bit sampling point |
| Edge | A rising edge of `i_clk`. Edges are numbered in order, so E+1 is the edge after edge E |
| Cycle after edge E | The clock period that starts at edge E and ends at edge E+1. A registered output that "becomes X at edge E" has value X in the cycle after edge E |
| Value at edge E | The value of a synchronous input sampled at edge E |
| Handshake (transmit) | An edge at which `i_tx_valid` = 1, `o_tx_ready` = 1 and `i_rst_n` = 1. The byte on `i_tx_data` is accepted |
| Accepting edge E0 | The edge at which a transmit handshake takes place |
| Take (receive) | An edge at which `o_rx_valid` = 1, `i_rx_ready` = 1 and `i_rst_n` = 1. The held byte leaves the block |
| Frame | Start bit, 8 data bits and stop bit: 10 bits, each N cycles long |
| s(E) | The value of `i_rxd` captured by the first synchronizer flip-flop at edge E |
| T0 | The edge at which the receiver detects the falling edge of a start bit: s(T0-1) = 1 and s(T0) = 0 while the receiver is idle |
| M | The stop-bit sampling edge of a frame, M = T0 + H + 9N |
| V | The delivery edge of a frame, V = M + 2. The 2 is the synchronizer latency |
| Glitch | A detected falling edge whose start-bit check s(T0 + H) gives 1 |
| Frame error | A completed frame whose stop-bit sample s(M) is 0 |
| Overrun | A completed frame that is dropped because the holding register is full and is not being emptied at its delivery edge V |
| Holding register | The one-byte receive output register behind `o_rx_data`, `o_rx_frame_err` and `o_rx_valid` |

## 4 Parameters

| Parameter | Default | Legal values | Description |
|---|---|---|---|
| PARA_UART_CLKS_PER_BIT | 16 | 4 to 65535 | Bit period in `i_clk` cycles (N), used by the transmitter and the receiver |
| LPARA_UART_HALF_BIT | Derived | - | PARA_UART_CLKS_PER_BIT / 2 with integer division (floor); the middle-of-bit sampling offset H |

[REQ-PAR-001] The block shall behave as specified for every value of `PARA_UART_CLKS_PER_BIT` from 4 to 65535 inclusive, both odd and even.

[REQ-PAR-002] `LPARA_UART_HALF_BIT` shall equal floor(`PARA_UART_CLKS_PER_BIT` / 2).

[REQ-PAR-003] The block should stop elaboration with an error message when `PARA_UART_CLKS_PER_BIT` is less than 4 or greater than 65535. Behaviour for illegal values is not specified and is not verified.

## 5 Interface

**`m_uart_lite`**: all ports (`CLK`)

| Port | Direction | Width | Signal type | Reset value | Clock domain | Meaning |
|---|---|---|---|---|---|---|
| i_clk | input | 1 | Clock | Not applicable | CLK | Clock, rising edge |
| i_rst_n | input | 1 | Reset (asynchronous assertion, synchronous release) | Not applicable | CLK | Active-low reset |
| i_tx_valid | input | 1 | Data | Not applicable | CLK | Transmit stream: `i_tx_data` holds a byte to send |
| o_tx_ready | output | 1 | Data | 1 | CLK | Transmit stream: the transmitter can accept a byte at the next edge |
| i_tx_data | input | 8 | Data | Not applicable | CLK | Transmit stream: byte to send; bit 0 is sent first |
| o_rx_valid | output | 1 | Data | 0 | CLK | Receive stream: the holding register holds a byte |
| i_rx_ready | input | 1 | Data | Not applicable | CLK | Receive stream: the consumer takes the held byte at this edge |
| o_rx_data | output | 8 | Data | 0 | CLK | Receive stream: received byte; bit 0 was received first; qualified by `o_rx_valid` |
| o_rx_frame_err | output | 1 | Data | 0 | CLK | Receive stream: 1 when the stop bit of the held byte was sampled as 0; qualified by `o_rx_valid` |
| o_rx_overrun | output | 1 | Data | 0 | CLK | One-cycle pulse: a received byte was dropped because the holding register was full |
| o_txd | output | 1 | Data | 1 | CLK | Serial transmit line, idle high |
| i_rxd | input | 1 | Data (asynchronous) | Not applicable | ASYNC | Serial receive line, idle high, asynchronous to `i_clk`, synchronised inside the block |

## 6 Clocks and resets

### 6.1 Clocks
The block has one clock, `i_clk`, which defines the clock domain CLK. All flip-flops are clocked on the rising edge of `i_clk`. The target frequency is 50 MHz (Section 13). Every port is synchronous to `i_clk` except `i_rxd`, which is asynchronous and is synchronised inside the block (Section 7.4). The bit rate is f(`i_clk`) / N. For example, at 50 MHz, N = 16 gives 3.125 Mbit/s and N = 434 gives about 115200 bit/s.

[REQ-CLK-001] All state elements of the block shall be clocked by the rising edge of `i_clk` only, with no other clock, no gated clock and no latch.

### 6.2 Resets
`i_rst_n` is active low. Its assertion is asynchronous. Its release is synchronous to `i_clk`: the release is synchronised outside the block (ENV-001), and the block contains no reset synchronizer.

[REQ-RST-001] When `i_rst_n` becomes 0, every flip-flop of the block shall take its reset value at once, without waiting for an edge of `i_clk`.

[REQ-RST-002] While `i_rst_n` is 0, the outputs shall have these values: `o_txd` = 1, `o_tx_ready` = 1, `o_rx_valid` = 0, `o_rx_data` = 0, `o_rx_frame_err` = 0, `o_rx_overrun` = 0.

[REQ-RST-003] While `i_rst_n` is 0, no transmit byte shall be accepted, even when `i_tx_valid` = 1 and `o_tx_ready` = 1.

[REQ-RST-004] While `i_rst_n` is 0, the receiver shall not detect a start bit and shall not deliver a byte.

[REQ-RST-005] Both `i_rxd` synchronizer flip-flops, and any flip-flop that holds the previous synchronised line value, shall reset to 1.

[REQ-RST-006] If reset is asserted during a transmission, the frame shall be abandoned: `o_txd` shall become 1 at once, and the rest of the frame and the byte shall not be sent after the release.

[REQ-RST-007] If reset is asserted during a reception, the partly received frame shall be discarded and shall not produce `o_rx_valid`, `o_rx_frame_err` or `o_rx_overrun` after the release.

[REQ-RST-008] If reset is asserted while `o_rx_valid` = 1, the held byte shall be discarded.

[REQ-RST-009] After the release of `i_rst_n`, the transmitter shall be idle with `o_tx_ready` = 1, and it shall be able to accept a byte at the first edge after the release.

[REQ-RST-010] After the release of `i_rst_n`, the receiver shall be idle. For the first edge R1 after the release, s(R1-1) shall be taken as 1 (the reset value of the synchronizer). So if s(R1) = 0, R1 is detected as T0 (Section 10.5).

## 7 Functional description

### 7.1 General

[REQ-GEN-001] The block shall send and receive frames in 8N1 format: a start bit of value 0, then eight data bits with the least significant bit first, then a stop bit of value 1, with no parity bit.

[REQ-GEN-002] The transmitter and the receiver shall work at the same time and independently. No activity of one shall change the timing or the outputs of the other.

[REQ-GEN-003] Every output port shall be driven directly by a flip-flop clocked by `i_clk`, so there is no combinational path from any input port to any output port.

### 7.2 Transmit stream interface

[REQ-TX-001] The transmitter shall accept a byte at an edge only when, at that edge, `i_tx_valid` = 1, `o_tx_ready` = 1 and `i_rst_n` = 1.

[REQ-TX-002] The transmitter shall capture `i_tx_data` at the accepting edge E0. The value of `i_tx_data` at any other edge shall have no effect.

[REQ-TX-003] While the transmitter is idle (no frame in progress), `o_tx_ready` shall be 1.

[REQ-TX-004] After an accepting edge E0, `o_tx_ready` shall be 0 in the cycles after edges E0 to E0+10N-2 inclusive.

[REQ-TX-005] After an accepting edge E0, `o_tx_ready` shall become 1 at edge E0+10N-1, which is the last cycle of the stop bit.

[REQ-TX-006] If `i_tx_valid` is 0 at an edge, or `o_tx_ready` is 0 at that edge, the transmitter shall not accept a byte and its state shall not depend on `i_tx_data`.

[REQ-TX-007] The transmitter shall not require `i_tx_valid` to stay 1 until a handshake. If `i_tx_valid` returns to 0 before a handshake, nothing is sent.

[REQ-TX-008] The transmitter shall hold at most one byte, the byte being sent, and shall have no transmit buffer beyond it.

### 7.3 Transmit serial frame

Frame bit j (j = 0 to 9) of a byte D is: bit 0 = 0 (start bit); bit j = D[j-1] for j = 1 to 8; bit 9 = 1 (stop bit).

[REQ-TX-010] For a byte D accepted at edge E0, `o_txd` in the cycle after edge E0+k shall equal frame bit floor(k / N) of D, for every k from 0 to 10N-1.

[REQ-TX-011] Each of the 10 frame bits shall be driven on `o_txd` for exactly N consecutive cycles.

[REQ-TX-012] If a new byte is accepted at edge E0+10N, its start bit shall begin at edge E0+10N, with no idle cycle between the stop bit of the previous frame and the new start bit.

[REQ-TX-013] If no byte is accepted at edge E0+10N, `o_txd` shall be 1 from edge E0+10N until the edge after which the next accepted frame starts.

[REQ-TX-014] While the transmitter is idle, `o_txd` shall be 1.

### 7.4 Receive line synchronisation and start detection

[REQ-RX-001] `i_rxd` shall go through a synchronizer of exactly two flip-flops clocked by `i_clk`, with no logic between them, before any other logic of the block uses it.

[REQ-RX-002] The receiver shall be in one of two conditions, idle or receiving. It shall be idle after reset, after a glitch (REQ-RX-005) and after the stop-bit sample of a frame (REQ-RX-013).

[REQ-RX-003] While idle, the receiver shall detect a start bit at edge T0 if and only if s(T0-1) = 1 and s(T0) = 0.

[REQ-RX-004] The receiver shall not need the line to be high for longer than the single sample s(T0-1) = 1 before a start bit.

[REQ-RX-005] At edge T0+H the receiver shall check the start bit. If s(T0+H) = 1, the receiver shall treat the event as a glitch, return to idle and receive no byte.

[REQ-RX-006] A glitch shall not change `o_rx_valid`, `o_rx_data` or `o_rx_frame_err`, and it shall not make `o_rx_overrun` pulse.

[REQ-RX-007] After a glitch checked at edge T0+H, the receiver shall detect a new start bit at any edge T0' > T0+H at which REQ-RX-003 holds.

[REQ-RX-008] If s(T0+H) = 0, the receiver shall go on to receive the frame.

### 7.5 Receive sampling and byte assembly

[REQ-RX-010] For a frame detected at T0 and confirmed at T0+H, the receiver shall sample data bit i (i = 0 to 7) at edge T0+H+(i+1)N. The received byte bit i shall be s(T0+H+(i+1)N).

[REQ-RX-011] The receiver shall sample the stop bit at edge M = T0+H+9N.

[REQ-RX-012] Only the samples s(T0-1), s(T0), s(T0+H), the eight data-bit samples and s(M) shall affect the result of a frame. Values of `i_rxd` at all other edges between T0 and M shall be ignored.

[REQ-RX-013] Once it has sampled the stop bit at M, the receiver shall be idle. It shall detect a new start bit at any edge T0' > M at which REQ-RX-003 holds, including T0' = M+1 when s(M) = 1 and s(M+1) = 0.

[REQ-RX-014] Every frame confirmed at T0+H shall complete at M, whatever the value of s(M).

[REQ-RX-015] The receiver shall keep sampling and receiving frames while a byte is waiting in the holding register. A low `i_rx_ready` shall not stall or delay the receiver.

### 7.6 Receive stream interface

[REQ-RX-020] At the delivery edge V = M+2 of a completed frame, if `o_rx_valid` = 0, the block shall load the frame into the holding register. `o_rx_valid` then becomes 1, `o_rx_data` becomes the received byte and `o_rx_frame_err` becomes the inverse of s(M).

[REQ-RX-021] At the delivery edge V of a completed frame, if `o_rx_valid` = 1 and `i_rx_ready` = 1, the block shall take the held byte and load the new frame into the holding register at the same edge. `o_rx_valid` stays 1 and no overrun is reported.

[REQ-RX-022] The consumer takes a held byte at an edge where `o_rx_valid` = 1, `i_rx_ready` = 1 and `i_rst_n` = 1.

[REQ-RX-023] If a held byte is taken at an edge and no new byte is loaded at that edge, `o_rx_valid` shall become 0 at that edge.

[REQ-RX-024] While `o_rx_valid` = 1 and the byte is not taken, `o_rx_valid`, `o_rx_data` and `o_rx_frame_err` shall keep their values.

[REQ-RX-025] `o_rx_data` and `o_rx_frame_err` shall change only at an edge where a new byte is loaded, or on reset. While `o_rx_valid` = 0 they shall keep the values of the last loaded byte, or 0 if no byte has been loaded since reset.

[REQ-RX-026] `i_rx_ready` shall have no effect while `o_rx_valid` = 0.

[REQ-RX-027] Bytes shall be delivered on the receive stream in the order in which their frames completed.

### 7.7 Frame error

[REQ-FE-001] `o_rx_frame_err` shall be 1 with a loaded byte if and only if the stop-bit sample s(M) of that frame was 0.

[REQ-FE-002] A byte with a frame error shall be delivered, held and taken like any other byte, and `o_rx_data` shall hold its sampled data bits.

[REQ-FE-003] After a frame with a frame error, the receiver shall not detect a new start bit until s has been 1 at one edge and 0 at the next edge (REQ-RX-003), so a line held at 0 produces exactly one frame.

### 7.8 Overrun

[REQ-OVR-001] At the delivery edge V of a completed frame, if `o_rx_valid` = 1 and `i_rx_ready` = 0, the block shall drop the new byte and its frame-error flag.

[REQ-OVR-002] When a byte is dropped at edge V, `o_rx_overrun` shall become 1 at edge V and return to 0 at edge V+1, so it is 1 for exactly one cycle.

[REQ-OVR-003] When a byte is dropped, `o_rx_valid`, `o_rx_data` and `o_rx_frame_err` shall keep the held byte unchanged.

[REQ-OVR-004] `o_rx_overrun` shall be 0 in every cycle except the cycle after an edge at which a byte is dropped.

[REQ-OVR-005] `o_rx_overrun` shall not be qualified by `o_rx_valid` and shall not need a handshake.

[REQ-OVR-006] A glitch, and a frame cut short by reset, shall not make `o_rx_overrun` pulse.

## 8 Timing and protocol

### 8.1 Transmit latency and throughput

- Latency: the start bit starts on `o_txd` at the accepting edge E0, which means in the first cycle after the handshake.
- Frame length: 10N cycles. The stop bit ends at edge E0+10N.
- `o_tx_ready` is 0 for 10N-1 cycles after E0 and becomes 1 in the last cycle of the stop bit (REQ-TX-004, REQ-TX-005).
- Back-pressure: while `o_tx_ready` = 0, the upstream block waits; the block never drops an offered byte.

[REQ-TIM-001] While `i_tx_valid` is held at 1, the transmitter shall accept one byte every 10N cycles and shall produce a continuous stream of frames with no idle cycle between them.

[REQ-TIM-002] Bytes shall be sent on `o_txd` in the order in which they were accepted.

### 8.2 Receive latency and throughput

- Latency: from start-bit detection T0 to delivery V = T0 + H + 9N + 2 edges. Measured from the stop-bit sample M, this is 2 edges: the synchronizer latency.
- Smallest spacing between two detected start bits: H + 9N + 1 cycles (REQ-RX-013). A transmitter that runs slightly fast is therefore accepted.
- Back-pressure: there is one holding register. To avoid an overrun, the consumer has to take a byte before the delivery edge of the next frame.

[REQ-TIM-003] The receiver shall accept frames back to back with no idle bit between them: a stop bit followed at once by the next start bit, each bit N cycles long.

### 8.3 Transmit example (N = 4, D = 0xA5)

D = 0xA5 = 1010_0101b, so data bits sent first to last are 1, 0, 1, 0, 0, 1, 0, 1. The byte is accepted at edge E0.

| Cycle after edge | i_tx_valid | o_tx_ready | o_txd | Frame bit |
|---|---|---|---|---|
| E0-1 | 1 | 1 | 1 | idle (handshake at E0) |
| E0 to E0+3 | x | 0 | 0 | start |
| E0+4 to E0+7 | x | 0 | 1 | D[0] |
| E0+8 to E0+11 | x | 0 | 0 | D[1] |
| E0+12 to E0+15 | x | 0 | 1 | D[2] |
| E0+16 to E0+19 | x | 0 | 0 | D[3] |
| E0+20 to E0+23 | x | 0 | 0 | D[4] |
| E0+24 to E0+27 | x | 0 | 1 | D[5] |
| E0+28 to E0+31 | x | 0 | 0 | D[6] |
| E0+32 to E0+35 | x | 0 | 1 | D[7] |
| E0+36 to E0+38 | x | 0 | 1 | stop |
| E0+39 | 1 | 1 | 1 | stop (last cycle; handshake of the next byte at E0+40) |
| E0+40 | x | 0 | 0 | start of the next byte (if accepted at E0+40) |

If no byte is accepted at E0+40, then after E0+40 `o_tx_ready` = 1 and `o_txd` = 1 (idle).

### 8.4 Receive example (N = 4, H = 2, received byte 0xA5, stop bit 1)

| Edge | s(Edge) | Receiver action | Outputs after the edge |
|---|---|---|---|
| T0-1 | 1 | idle | o_rx_valid = 0 |
| T0 | 0 | start bit detected | o_rx_valid = 0 |
| T0+2 | 0 | start-bit check passes | - |
| T0+6 | 1 | D[0] = 1 | - |
| T0+10 | 0 | D[1] = 0 | - |
| T0+14 | 1 | D[2] = 1 | - |
| T0+18 | 0 | D[3] = 0 | - |
| T0+22 | 0 | D[4] = 0 | - |
| T0+26 | 1 | D[5] = 1 | - |
| T0+30 | 0 | D[6] = 0 | - |
| T0+34 | 1 | D[7] = 1 | - |
| T0+38 (M) | 1 | stop bit sampled; receiver idle | - |
| T0+40 (V) | - | byte loaded | o_rx_valid = 1, o_rx_data = 0xA5, o_rx_frame_err = 0 |
| T0+41 | - | i_rx_ready = 1: byte taken | o_rx_valid = 0 |

If at V the holding register was full and `i_rx_ready` = 0, then after V `o_rx_overrun` = 1 for one cycle and the held byte is unchanged.

### 8.5 Loopback relation (informative)
If `i_rxd` is connected directly to `o_txd`, then T0 = E0+1 and the byte is delivered at edge E0 + H + 9N + 3. With N = 4 this is E0+41.

## 9 Registers

The block has no software-visible registers.

## 10 Errors and corner cases

### 10.1 Frame error
Detection: the stop-bit sample s(M) is 0. Response: the byte is delivered with `o_rx_frame_err` = 1 (REQ-FE-001, REQ-FE-002).

### 10.2 Overrun
Detection: a frame completes and, at its delivery edge V, `o_rx_valid` = 1 and `i_rx_ready` = 0. Response: the new byte is dropped, `o_rx_overrun` pulses for one cycle and the held byte stays (REQ-OVR-001 to REQ-OVR-003). If the held byte is taken at V itself, there is no overrun (REQ-RX-021). The frame-error flag of a dropped byte is not reported.

### 10.3 Glitch on the start bit
Detection: s(T0+H) = 1. Response: no byte, no flag and no pulse (REQ-RX-005, REQ-RX-006). A low pulse on `i_rxd` that is sampled at fewer than H+1 edges in a row, starting at T0, is always rejected.

### 10.4 Line held low (break) and stuck line
[REQ-ERR-001] If `i_rxd` stays 0 from a start bit through the whole frame, the receiver shall deliver the byte 0x00 with `o_rx_frame_err` = 1, or drop it with an overrun pulse under the rules of Section 7.8. After that it shall receive no further frame until the line has been sampled as 1 and then as 0.

[REQ-ERR-002] If `i_rxd` stays 1, the receiver shall stay idle and deliver nothing.

### 10.5 Line low at reset release
[REQ-ERR-003] If s(R1) = 0 at the first edge R1 after the release of `i_rst_n`, the receiver shall detect R1 as T0 (REQ-RST-010) and process the frame under Sections 7.4 to 7.8. A line that stays low therefore produces one byte 0x00 with `o_rx_frame_err` = 1.

### 10.6 Reset during an operation
Section 6.2 covers this (REQ-RST-006 to REQ-RST-008). A frame cut short on `o_txd` may cause a frame error in the remote receiver; that is outside this block.

### 10.7 Handshake corner cases
[REQ-ERR-004] When `i_tx_valid` = 1 while `o_tx_ready` = 0, the transmitter shall not accept the byte and shall not record it. The upstream block has to keep offering it.

[REQ-ERR-005] When `i_rx_ready` = 1 while `o_rx_valid` = 0, the block shall do nothing (REQ-RX-026).

[REQ-ERR-006] A transmit handshake and a receive delivery or take in the same cycle shall be handled independently (REQ-GEN-002).

### 10.8 Parameter extremes
- N = 4 (minimum): H = 2. When the bit period is exact, each sample is taken 2 edges after the first edge of the bit and 1 edge before its last edge. A frame lasts 40 cycles, and the smallest spacing between start bits is 39 cycles.
- N odd (for example 5): H = floor(N/2) = 2, which is exactly the centre of the bit.
- N = 65535 (maximum): H = 32767. A frame lasts 655350 cycles. [REQ-ERR-007] Bit-period and sample-offset counting shall not overflow or wrap early at N = 65535.
- Values outside 4 to 65535 are illegal (REQ-PAR-003).

## 11 Configurations

| ID | Parameter values | Purpose |
|---|---|---|
| CFG-BASE | defaults (PARA_UART_CLKS_PER_BIT=16) | Main configuration |
| CFG-MIN | PARA_UART_CLKS_PER_BIT=4 | Smallest legal bit period; minimum sampling margins |
| CFG-ODD | PARA_UART_CLKS_PER_BIT=5 | Odd bit period; checks H = floor(N/2) |
| CFG-WIDE | PARA_UART_CLKS_PER_BIT=1024 | A wide bit counter. The largest legal value (65535) is covered by elaboration and synthesis only (D-012) |

## 12 Verification requirements

### 12.1 Environment obligations
[ENV-001] The environment shall release `i_rst_n` (0 to 1) synchronously to `i_clk`, meeting recovery and removal times. The block contains no reset synchronizer.

[ENV-002] The environment shall hold `i_rst_n` at 0 for at least 2 cycles of `i_clk` at the start of a simulation.

[ENV-003] After the release of `i_rst_n`, the environment shall drive `i_tx_valid`, `i_tx_data` and `i_rx_ready` synchronously to `i_clk`, with no X or Z values.

[ENV-004] In simulation, the testbench shall change `i_rxd` away from rising edges of `i_clk` (for example on the falling edge or at a random offset that does not coincide with a rising edge), so that s(E) is well defined. `i_rxd` shall not be X or Z after reset release.

[ENV-005] The environment has no obligation to keep `i_tx_valid` or `i_tx_data` stable before a handshake, and no obligation on when `i_rx_ready` is asserted. The block has to handle any pattern.

### 12.2 Observability
- The synchronizer depth can be seen at the ports only as the fixed latency V = M + 2. Its structure (exactly two flip-flops with no logic between them, REQ-RX-001) shall be checked by lint or a structural review.
- The receiver's idle/receiving condition and its sampling edges can be seen only through the delivered bytes, flags and pulses. The reference model shall compute s(E) from `i_rxd` and apply Sections 7.4 to 7.8 exactly.
- The transmit timing can be seen fully on `o_txd` and `o_tx_ready`. The checker shall check REQ-TX-004, REQ-TX-005 and REQ-TX-010 cycle by cycle.

### 12.3 Special setups
- Sampling-point test: drive `i_rxd` so that each bit has its correct value only at the specified sampling edge and the wrong value at the edges just before and after it, where N allows that. This checks the exact sampling edges T0+H+(i+1)N and M.
- Glitch test: low pulses on `i_rxd` lasting 1 to H samples (rejected) and H+1 samples (accepted as a start bit).
- Loopback test: connect `o_txd` to `i_rxd` and check the latency in Section 8.5 and the byte integrity.
- Reset tests: assert `i_rst_n` in the middle of a transmit frame, in the middle of a receive frame and while `o_rx_valid` = 1, with an asynchronous assertion between clock edges.
- Line low at reset release (REQ-ERR-003) and break (REQ-ERR-001).

### 12.4 Required coverage
- Data bytes 0x00, 0xFF, 0x55, 0xAA and random bytes, in both directions.
- Back-to-back transmit with `i_tx_valid` held at 1, and transmit with idle gaps of various lengths.
- Back-to-back receive frames with the next start bit right after the stop bit.
- Frame error with `o_rx_valid` = 0, and frame error with the byte dropped by overrun.
- Overrun, and the case where the held byte is taken at the delivery edge V itself (no overrun).
- `i_rx_ready` held at 1, toggling at random, and held at 0 for several frames.
- `i_tx_valid` that drops before a handshake.
- Transmit and receive active at the same time.

## 13 Implementation constraints

[REQ-IMP-001] The block shall meet timing at 50 MHz (20 ns period) on GF180MCU for every legal value of `PARA_UART_CLKS_PER_BIT`.

[REQ-IMP-002] The RTL shall follow `docs/RTL_RULES.md`.

[REQ-IMP-003] The RTL shall be synthesizable, contain no latches and pass Verilator lint with no warnings.

[REQ-IMP-004] All flip-flops shall use the asynchronous active-low reset `i_rst_n`.

[REQ-IMP-005] The two `i_rxd` synchronizer flip-flops should be marked so that synthesis does not merge, duplicate or retime them.

[REQ-IMP-006] The bit-period counters should be only as wide as `PARA_UART_CLKS_PER_BIT` needs (16 bits at most).

No area budget is given. The block should use only the storage this specification requires: the transmit shift register, the receive shift register, the holding register, counters and flags.

## 14 Decisions and open questions

| ID | Question | Decision | By | Date |
|---|---|---|---|---|
| D-001 | Value of `o_tx_ready` while `i_rst_n` = 0 | 1 (its idle value); no handshake is possible during reset (REQ-RST-003) | Claude (delegated by GabrielHCMUT), confirmed | 2026-11-17 |
| D-002 | Exact middle-of-bit sampling point | H = floor(N/2) edges after T0, then every N edges | Claude (delegated by GabrielHCMUT), confirmed | 2026-11-17 |
| D-003 | Exact cycle of `o_rx_valid` "the cycle after the middle of the stop bit" | Delivery at V = M + 2, where M is the sample edge of `i_rxd` and 2 is the synchronizer latency | Claude (delegated by GabrielHCMUT), confirmed | 2026-11-17 |
| D-004 | Held byte taken at the same edge at which a new byte completes | The new byte is loaded and there is no overrun | Claude (delegated by GabrielHCMUT), confirmed | 2026-11-17 |
| D-005 | Start detection after a frame error with the line still low | A 1-to-0 transition is required, so a break gives one byte | Claude (delegated by GabrielHCMUT), confirmed | 2026-11-17 |
| D-006 | Synchronizer reset value and a low line at reset release | Reset to 1; a low line at release is detected as a start bit | Claude (delegated by GabrielHCMUT), confirmed | 2026-11-17 |
| D-007 | `o_rx_data` and `o_rx_frame_err` while `o_rx_valid` = 0 | Keep the last loaded values; 0 after reset | Claude (delegated by GabrielHCMUT), confirmed | 2026-11-17 |
| D-008 | Reset release synchronisation | Done outside the block (ENV-001) | Claude (delegated by GabrielHCMUT), confirmed | 2026-11-17 |
| D-009 | Reset during a transmission | Frame abandoned, `o_txd` = 1 at once, byte lost | Claude (delegated by GabrielHCMUT), confirmed | 2026-11-17 |
| D-010 | Frame-error flag of a dropped byte | Not reported | Claude (delegated by GabrielHCMUT), confirmed | 2026-11-17 |
| D-011 | Illegal parameter values | Elaboration error recommended (should); not verified | Claude (delegated by GabrielHCMUT), confirmed | 2026-11-17 |
| D-012 | Configurations beyond default and minimum | CFG-ODD (5) and CFG-WIDE (1024) are simulated. CFG-MAX (65535) is not simulated (655350 cycles per frame); the largest value is covered by elaboration and synthesis only | Claude (delegated by GabrielHCMUT) | 2026-11-17 |
| OQ-001 | Is an area budget required for GF180MCU? | No area budget; area is reported, not checked | Claude (delegated by GabrielHCMUT) | 2026-11-17 |
| OQ-002 | Which PVT corner does the 50 MHz target apply to? | The slow corner (GF180MCU SS, 125 C, 4.5 V) | Claude (delegated by GabrielHCMUT) | 2026-11-17 |
| OQ-003 | Is the simulation time of CFG-MAX acceptable in the regression? | No: CFG-MAX is not simulated (D-012) | Claude (delegated by GabrielHCMUT) | 2026-11-17 |

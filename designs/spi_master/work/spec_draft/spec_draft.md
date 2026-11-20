# `spi_master` Design Specification

Revision: `0.1`, `2026-11-19`. Top module: `m_spi_master`.

## 1 Overview

### 1.1 Purpose

`spi_master` is a single-clock SPI master with one slave select. Each transfer shifts one byte out on `o_mosi` and one byte in from `i_miso`. Software sends the bytes to transmit through a valid/ready command stream and gets back each received byte through a valid/ready response stream, in order. The block never drops a received byte: when the response stream is back-pressured, the master stops starting new transfers.

### 1.2 Features

- One 8-bit transfer per command, MSB first, full duplex.
- Bursts of any length: `i_cmd_last` = 1 marks the last byte of a burst. `o_cs_n` stays low for the whole burst.
- SPI modes 0 to 3 are selected by `i_cpol` and `i_cpha`. They are captured when a burst starts.
- SCLK frequency is `f(i_clk) / (2 x PARA_SPI_CLK_DIV)`, with `PARA_SPI_CLK_DIV` from 1 to 255 (fixed at elaboration).
- Slave-select timing in half periods: lead time, trail time and minimum high time between bursts.
- Back-to-back bytes inside a burst have no SCLK gap when the next command is ready in time. Otherwise SCLK pauses at its idle level and `o_cs_n` stays low.
- No received byte is lost under back-pressure: one byte is shown on the response stream and at most one more is held inside the master.
- Asynchronous active-low reset.

### 1.3 Out of scope

- More than one slave select, word lengths other than 8 bits, LSB-first order.
- 3-wire, dual, quad or DDR SPI, and SPI slave operation.
- Changing the SCLK divider at run time, and programmable CS lead, trail or gap times.
- Timeouts, error reporting outputs, interrupts, a register interface and DMA.
- Synchronising `i_miso` or handling metastability on `i_miso`. The slave drives `i_miso` from SCLK, which this block derives from `i_clk`.
- Tri-stating or turning around `o_mosi`, and read-only or write-only transfer types. Every transfer is full duplex.
- Glitch checks at gate level and DFT/scan insertion. These belong to the implementation flow, not to this verification.

## 2 References

| ID | Document | Revision | Used for |
|---|---|---|---|
| REF-001 | Motorola/Freescale SPI Block Guide (S12SPIV4) | V04.01 | Meaning of CPOL/CPHA and SPI modes 0 to 3 (leading/trailing edge, sample/shift) |
| REF-002 | ARM IHI 0051, AMBA 4 AXI4-Stream Protocol Specification | Issue A | Valid/ready handshake meaning only (TVALID/TREADY rules) |
| REF-003 | `docs/RTL_RULES.md` (project coding rules) | Current in repository | RTL coding rules |
| REF-004 | `spi_master` design description (input of `nnc spec-draft`) | 2026-11-19 | Source of this specification |

## 3 Terms

| Term | Meaning |
|---|---|
| D | Value of `PARA_SPI_CLK_DIV`: the number of `i_clk` cycles in one SCLK half period. |
| Edge | A rising edge of `i_clk`. Edge `E + n` is the n-th rising edge after edge E. |
| Cycle starting at edge E | The `i_clk` period between edge E and edge E + 1. "After edge E" means in that cycle. |
| Command handshake | An edge at which `i_rst_n` = 1, `i_cmd_valid` = 1 and `o_cmd_ready` = 1. The command is accepted at that edge. |
| Response handshake | An edge at which `i_rst_n` = 1, `o_rsp_valid` = 1 and `i_rsp_ready` = 1. The shown response is taken at that edge. |
| Transfer | Shifting one byte out and one byte in for one accepted command. A transfer whose command is accepted at edge A covers the 16·D cycles starting at edges A to A + 16·D − 1. |
| A | The acceptance edge of the transfer being described. |
| SCLK edge k | For a transfer with acceptance edge A, the k-th transition of `o_sclk` (k = 1 to 16). It happens at edge A + k·D. |
| Leading / trailing edge | The odd SCLK edges (k = 1, 3, …, 15) are leading edges, which leave the idle level. The even SCLK edges (k = 2, 4, …, 16) are trailing edges, which return to the idle level. |
| Sampling edge / shift edge | The SCLK edges at which the receiver samples data / the transmitter changes data. They depend on CPHA (section 7.3). |
| Last cycle of a transfer | The cycle starting at edge A + 16·D − 1, which ends at SCLK edge 16. |
| Burst | The sequence of transfers from the command that drives `o_cs_n` low up to and including the command with `i_cmd_last` = 1. |
| CPOL_b, CPHA_b | The values of `i_cpol` and `i_cpha` captured at the first acceptance edge of the current burst. |
| Idle | Phase with `o_cs_n` = 1. |
| Pause | Phase inside a burst after a transfer with `i_cmd_last` = 0 ended, when no command was accepted at its SCLK edge 16. `o_cs_n` = 0 and `o_sclk` is at the idle level. |
| Trail | The D cycles after SCLK edge 16 of the last transfer of a burst, before `o_cs_n` goes high. |
| Gap | The time `o_cs_n` stays 1 between two bursts. |
| Shown byte | The byte on `o_rsp_data` while `o_rsp_valid` = 1. |
| Held byte | A received byte that is complete but not yet loaded into `o_rsp_data`, because the shown byte has not been taken. |

## 4 Parameters

| Parameter | Default | Legal values | Description |
|---|---|---|---|
| PARA_SPI_CLK_DIV | 4 | 1 to 255 | Number of `i_clk` cycles in one SCLK half period (D). SCLK frequency = f(`i_clk`) / (2·D). |

The block has no derived parameter visible at its interface.

[REQ-PAR-001] Elaboration of `m_spi_master` shall fail with an error message when `PARA_SPI_CLK_DIV` is less than 1 or greater than 255.

[REQ-PAR-002] Every value of `PARA_SPI_CLK_DIV` from 1 to 255 shall give the behaviour of this specification without any other change to the RTL.

## 5 Interface

**`m_spi_master`**: all ports (`CLK`)

| Port | Direction | Width | Signal type | Reset value | Clock domain | Meaning |
|---|---|---|---|---|---|---|
| i_clk | input | 1 | Clock | Not applicable | CLK | Clock, rising edge |
| i_rst_n | input | 1 | Reset (asynchronous assertion, synchronous release) | Not applicable | CLK | Active-low reset |
| i_cmd_valid | input | 1 | Data | 0 | CLK | Command stream valid. The environment keeps it 0 while `i_rst_n` = 0 |
| o_cmd_ready | output | 1 | Data | 1 | CLK | Command stream ready. Does not depend combinationally on any input |
| i_cmd_data | input | 8 | Data | Not applicable | CLK | Byte to send. Captured at the command handshake |
| i_cmd_last | input | 1 | Data | Not applicable | CLK | 1 = this byte ends the burst, and `o_cs_n` is released after it. Captured at the command handshake |
| o_rsp_valid | output | 1 | Data | 0 | CLK | Response stream valid |
| i_rsp_ready | input | 1 | Data | Not applicable | CLK | Response stream ready |
| o_rsp_data | output | 8 | Data | 0 | CLK | Byte received during the transfer of the matching command |
| o_sclk | output | 1 | Data (SPI serial clock; not used as a clock inside the block) | Equal to `i_cpol` (follows it combinationally) | CLK | SPI serial clock |
| o_mosi | output | 1 | Data | 0 | CLK | SPI master-out slave-in data |
| i_miso | input | 1 | Data | Not applicable | CLK | SPI master-in slave-out data. Sampled by `i_clk` without a synchroniser |
| o_cs_n | output | 1 | Data | 1 | CLK | SPI slave select, active low |
| i_cpol | input | 1 | Data (quasi-static configuration) | Not applicable | CLK | SPI clock polarity (SCLK idle level). May change only while `o_cs_n` = 1 |
| i_cpha | input | 1 | Data (quasi-static configuration) | Not applicable | CLK | SPI clock phase. 0 = sample on leading edges, 1 = sample on trailing edges. May change only while `o_cs_n` = 1 |

## 6 Clocks and resets

### 6.1 Clocks

[REQ-CLK-001] All state elements of `m_spi_master` shall be clocked by the rising edge of `i_clk`, which is the only clock of the block (domain CLK).

[REQ-CLK-002] `o_sclk` shall be produced as a data output timed by `i_clk` and shall not clock any state element inside the block.

[REQ-CLK-003] `i_miso` shall be treated as synchronous to `i_clk` and shall be sampled without a synchroniser, because the slave launches it from `o_sclk`, which is derived from `i_clk`.

All inputs are synchronous to `i_clk`. The block has no clock-domain crossing.

### 6.2 Resets

[REQ-RST-001] When `i_rst_n` changes to 0, all outputs shall take their reset values at once, without waiting for an edge of `i_clk`.

[REQ-RST-002] While `i_rst_n` = 0, `o_cs_n` shall be 1.

[REQ-RST-003] While `i_rst_n` = 0, `o_sclk` shall be equal to the current value of `i_cpol` and shall follow every change of `i_cpol` combinationally.

[REQ-RST-004] While `i_rst_n` = 0, `o_mosi` shall be 0.

[REQ-RST-005] While `i_rst_n` = 0, `o_rsp_valid` shall be 0 and `o_rsp_data` shall be 8'h00.

[REQ-RST-006] While `i_rst_n` = 0, `o_cmd_ready` shall be 1.

[REQ-RST-007] While `i_rst_n` = 0, the master shall not accept a command, whatever the values of `i_cmd_valid` and `o_cmd_ready`.

[REQ-RST-008] Reset asserted during a burst shall abort the transfer in progress, and no response shall be produced for that transfer.

[REQ-RST-009] Reset asserted while a shown byte or a held byte exists shall discard that byte without a response handshake.

[REQ-RST-010] After `i_rst_n` returns to 1, the master shall be in Idle with the gap requirement met: it can accept a command at the first edge at which `i_rst_n` is 1.

[REQ-RST-011] The minimum `o_cs_n` high time of REQ-CS-005 shall not be required across a reset: the high time of `o_cs_n` after an aborted burst is the reset duration plus the time until the next acceptance.

`i_rst_n` is released synchronously to `i_clk` by the environment (ENV-001).

## 7 Functional description

This section uses the terms of section 3. D = `PARA_SPI_CLK_DIV`. The phases of the block are:

| Phase | `o_cs_n` | `o_sclk` | `o_mosi` | `o_cmd_ready` |
|---|---|---|---|---|
| Reset (`i_rst_n` = 0) | 1 | `i_cpol` (combinational) | 0 | 1 |
| Idle | 1 | `i_cpol` (combinational) | Holds last value | 0 in the first D − 1 cycles after `o_cs_n` rose, otherwise NOT `o_rsp_valid` |
| Transfer | 0 | Toggles at edges A + k·D, k = 1 to 16 | Section 7.5 | 0, except in the last cycle: 1 if `i_cmd_last` of this transfer = 0 and `o_rsp_valid` = 0 |
| Pause | 0 | CPOL_b | Holds last value | NOT `o_rsp_valid` |
| Trail | 0 | CPOL_b | Holds last value | 0 |

Phase changes (all at edges, except reset):

| From | Condition | To |
|---|---|---|
| Idle | Command handshake at edge A | Transfer (first of a burst) |
| Transfer | Edge A + 16·D, command handshake at this edge | Transfer (next byte, no gap) |
| Transfer | Edge A + 16·D, no handshake, `i_cmd_last` of this transfer = 0 | Pause |
| Transfer | Edge A + 16·D, `i_cmd_last` of this transfer = 1 | Trail |
| Pause | Command handshake | Transfer |
| Trail | Edge A + 17·D | Idle |
| Any | `i_rst_n` = 0 | Reset |

### 7.1 Command stream

[REQ-CMD-001] The master shall accept a command at an edge only when `i_rst_n` = 1, `i_cmd_valid` = 1 and `o_cmd_ready` = 1 at that edge.

[REQ-CMD-002] At the acceptance edge the master shall capture `i_cmd_data` as the byte to send and `i_cmd_last` as the end-of-burst flag of that transfer.

[REQ-CMD-003] The values of `i_cmd_data` and `i_cmd_last` at edges without a command handshake shall have no effect.

[REQ-CMD-004] If `i_cmd_valid` goes from 1 to 0 without a command handshake, the master shall behave as if the command had never been presented.

[REQ-CMD-005] `o_cmd_ready` shall change only at an edge of `i_clk` or when `i_rst_n` is asserted, and shall not depend combinationally on any input.

[REQ-CMD-006] While `i_rst_n` = 1, `o_cmd_ready` shall be 0 in every cycle in which `o_rsp_valid` = 1.

[REQ-CMD-007] When `o_cs_n` changes from 0 to 1 at edge R, `o_cmd_ready` shall be 0 in every cycle that starts at an edge from R to R + D − 2. When D = 1 there is no such cycle.

[REQ-CMD-008] In Idle, `o_cmd_ready` shall be 1 when `o_rsp_valid` = 0 in every cycle that starts at edge R + D − 1 or later, and in every cycle after reset release until the next acceptance.

[REQ-CMD-009] During a transfer, `o_cmd_ready` shall be 0 in every cycle except the last cycle of the transfer.

[REQ-CMD-010] In the last cycle of a transfer, `o_cmd_ready` shall be 1 if the `i_cmd_last` captured for that transfer is 0 and `o_rsp_valid` is 0, and 0 otherwise.

[REQ-CMD-011] In Pause, `o_cmd_ready` shall be 1 when `o_rsp_valid` = 0 and 0 when `o_rsp_valid` = 1.

[REQ-CMD-012] In Trail, `o_cmd_ready` shall be 0.

### 7.2 Burst framing and slave select

[REQ-CS-001] A command accepted in Idle at edge A shall start a burst: `o_cs_n` shall change from 1 to 0 at edge A.

[REQ-CS-002] `o_cs_n` shall stay 0 from the start of a burst until edge A + 17·D, where A is the acceptance edge of the transfer whose captured `i_cmd_last` is 1. At that edge `o_cs_n` shall change to 1.

[REQ-CS-003] `o_cs_n` shall change only at the edges given in REQ-CS-001 and REQ-CS-002, and at the assertion of `i_rst_n`.

[REQ-CS-004] The first SCLK edge of a burst shall come exactly D cycles after `o_cs_n` falls (edge A + D), so the lead time is one SCLK half period.

[REQ-CS-005] Between two bursts with no reset in between, `o_cs_n` shall stay 1 for at least D cycles.

[REQ-CS-006] `o_cs_n` shall rise exactly D cycles after SCLK edge 16 of the last transfer of the burst, so the trail time is one SCLK half period.

[REQ-CS-007] The rise of `o_cs_n` at the end of a burst shall not depend on the state of the response stream (`o_rsp_valid`, `i_rsp_ready`, a held byte).

REQ-CS-005 follows from REQ-CMD-007: the earliest acceptance after `o_cs_n` rises at edge R is edge R + D.

### 7.3 SPI mode selection

[REQ-MODE-001] At the acceptance edge of the first command of a burst, the master shall capture `i_cpol` as CPOL_b and `i_cpha` as CPHA_b.

[REQ-MODE-002] CPOL_b and CPHA_b shall control `o_sclk`, `o_mosi` and the sampling of `i_miso` for the whole burst, including Pause and Trail.

[REQ-MODE-003] Changes of `i_cpol` or `i_cpha` while `o_cs_n` = 0 shall have no effect on `o_sclk`, `o_mosi`, `o_cs_n`, the sampling of `i_miso` or the response data.

[REQ-MODE-004] With CPHA_b = 0, the leading SCLK edges (odd k) shall be the sampling edges and the trailing SCLK edges (even k) shall be the shift edges.

[REQ-MODE-005] With CPHA_b = 1, the leading SCLK edges (odd k) shall be the shift edges and the trailing SCLK edges (even k) shall be the sampling edges.

| Mode | `i_cpol` | `i_cpha` | Idle `o_sclk` | Leading edges (k odd) | Trailing edges (k even) | `o_mosi` bit 7 launched at | `i_miso` sampled at |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | Rising, sample | Falling, shift | Acceptance edge A | Edges A + (2j+1)·D |
| 1 | 0 | 1 | 0 | Rising, shift | Falling, sample | SCLK edge 1 (A + D) | Edges A + (2j+2)·D |
| 2 | 1 | 0 | 1 | Falling, sample | Rising, shift | Acceptance edge A | Edges A + (2j+1)·D |
| 3 | 1 | 1 | 1 | Falling, shift | Rising, sample | SCLK edge 1 (A + D) | Edges A + (2j+2)·D |

(j = 0 to 7. Bit 7 − j is transmitted and received in step j.)

### 7.4 SCLK generation

[REQ-SCLK-001] For a transfer with acceptance edge A, `o_sclk` shall toggle at each of the 16 edges A + k·D, k = 1 to 16.

[REQ-SCLK-002] While `o_cs_n` = 0, `o_sclk` shall not change at any edge other than those of REQ-SCLK-001.

[REQ-SCLK-003] While `o_cs_n` = 0 and no transfer is between its SCLK edges 1 and 16, `o_sclk` shall equal CPOL_b. This covers the lead half period, Pause and Trail.

[REQ-SCLK-004] After SCLK edge k of a transfer, `o_sclk` shall equal NOT CPOL_b for odd k and CPOL_b for even k.

[REQ-SCLK-005] While `o_cs_n` = 1, `o_sclk` shall equal `i_cpol` and shall follow changes of `i_cpol` combinationally.

[REQ-SCLK-006] When `o_cs_n` rises at edge R, `o_sclk` shall take the value of `i_cpol` from edge R on.

[REQ-SCLK-007] When a transfer starts at SCLK edge 16 of the previous transfer of the same burst, the SCLK period over the joint shall be 2·D cycles with each half period equal to D cycles.

### 7.5 MOSI transmission

The byte to send is d[7:0] = the captured `i_cmd_data`.

[REQ-MOSI-001] The bits of each byte shall be sent in the order d[7], d[6], …, d[0] (MSB first).

[REQ-MOSI-002] With CPHA_b = 0, `o_mosi` shall take the value d[7] at the acceptance edge A.

[REQ-MOSI-003] With CPHA_b = 0, `o_mosi` shall take the value d[7 − j] at edge A + 2·j·D for j = 1 to 7 (SCLK edges 2, 4, …, 14).

[REQ-MOSI-004] With CPHA_b = 1, `o_mosi` shall take the value d[7 − j] at edge A + (2·j + 1)·D for j = 0 to 7 (SCLK edges 1, 3, …, 15).

[REQ-MOSI-005] `o_mosi` shall not change at any edge other than those of REQ-MOSI-002 to REQ-MOSI-004, except at the assertion of `i_rst_n`.

[REQ-MOSI-006] In Idle, Pause and Trail, `o_mosi` shall keep the last value it was given. That value is 0 after reset.

[REQ-MOSI-007] `o_mosi` shall be stable in the cycle before each sampling edge and shall not change at any sampling edge, in all four modes.

With CPHA_b = 0, `o_mosi` keeps d[0] after SCLK edge 16 unless the next command is accepted at that edge, in which case it takes the next d[7] at that edge (REQ-MOSI-002). With CPHA_b = 1, `o_mosi` keeps its previous value from the acceptance edge until SCLK edge 1.

### 7.6 MISO reception

[REQ-MISO-001] With CPHA_b = 0, the master shall capture `i_miso` as received bit r[7 − j] at edge A + (2·j + 1)·D for j = 0 to 7.

[REQ-MISO-002] With CPHA_b = 1, the master shall capture `i_miso` as received bit r[7 − j] at edge A + (2·j + 2)·D for j = 0 to 7.

[REQ-MISO-003] The value captured at a sampling edge shall be the value of `i_miso` in the cycle that ends at that edge, which is the value just before `o_sclk` makes the sampling transition.

[REQ-MISO-004] `i_miso` shall have no effect at any edge other than the sampling edges of a transfer.

[REQ-MISO-005] The received byte r[7:0] of a transfer shall be made of the 8 bits captured during that transfer only.

### 7.7 Response stream

[REQ-RSP-001] Each accepted command shall produce exactly one response carrying the byte received during its transfer.

[REQ-RSP-002] Responses shall be delivered in the order in which the commands were accepted, across burst boundaries.

[REQ-RSP-003] At edge A + 16·D of a transfer, the master shall load the received byte into `o_rsp_data` and set `o_rsp_valid` to 1 if `o_rsp_valid` was 0 in the cycle ending at that edge or a response handshake occurs at that edge.

[REQ-RSP-004] If neither condition of REQ-RSP-003 holds at edge A + 16·D, the received byte shall become the held byte.

[REQ-RSP-005] At the edge where the response handshake of the shown byte occurs, the held byte shall be loaded into `o_rsp_data` and `o_rsp_valid` shall stay 1.

[REQ-RSP-006] At a response handshake where no byte is loaded at the same edge, `o_rsp_valid` shall change to 0.

[REQ-RSP-007] While `o_rsp_valid` = 1 and no response handshake has occurred, `o_rsp_valid` shall stay 1 and `o_rsp_data` shall not change.

[REQ-RSP-008] While `o_rsp_valid` = 0, `o_rsp_data` shall keep the last byte loaded into it, or 8'h00 after reset.

[REQ-RSP-009] `o_rsp_valid` and `o_rsp_data` shall change only at edges of `i_clk` or at the assertion of `i_rst_n`.

[REQ-RSP-010] `i_rsp_ready` shall have no effect while `o_rsp_valid` = 0.

[REQ-RSP-011] The master shall never overwrite a shown byte or a held byte before it has been taken, and shall never deliver a byte twice.

[REQ-RSP-012] At any time, at most two received bytes shall be pending: one shown byte and at most one held byte.

The pending-byte limit holds because REQ-CMD-006 blocks the start of a transfer while `o_rsp_valid` = 1. A new transfer therefore starts only when every earlier received byte has been taken, except the byte of the transfer that ends at the same edge.

### 7.8 Continuation, pause and end of burst

[REQ-FLOW-001] When a command is accepted at edge A + 16·D of a transfer whose captured `i_cmd_last` is 0, the new transfer shall use that edge as its acceptance edge. Its SCLK edge 1 then comes D cycles after SCLK edge 16 of the previous transfer, with no gap.

[REQ-FLOW-002] When a transfer with captured `i_cmd_last` = 0 ends at edge A + 16·D without a command handshake at that edge, the master shall enter Pause.

[REQ-FLOW-003] In Pause, `o_cs_n` shall stay 0, `o_sclk` shall stay at CPOL_b and `o_mosi` shall keep its value.

[REQ-FLOW-004] Pause shall last until a command is accepted, without any time limit.

[REQ-FLOW-005] A command accepted in Pause at edge P shall start a transfer with acceptance edge A = P, in the same burst and with the same CPOL_b and CPHA_b.

[REQ-FLOW-006] When a transfer with captured `i_cmd_last` = 1 ends at edge A + 16·D, the master shall enter Trail, and `o_cs_n` shall rise at edge A + 17·D (REQ-CS-002).

[REQ-FLOW-007] The master shall not start a transfer while a received byte is held.

## 8 Timing and protocol

Latency and throughput (D = `PARA_SPI_CLK_DIV`, all numbers in `i_clk` cycles):

| Item | Value |
|---|---|
| Command acceptance to `o_cs_n` low (first byte of a burst) | 0 (same edge A) |
| Command acceptance to SCLK edge 1 (lead) | D |
| Command acceptance to `o_rsp_valid` = 1 (response register free) | 16·D |
| SCLK edge 16 of last byte to `o_cs_n` high (trail) | D |
| Minimum `o_cs_n` high time between bursts (gap) | D |
| Byte period inside a continuous burst | 16·D |
| `o_cs_n` low time of an n-byte continuous burst | 16·n·D + D |
| Minimum time between first acceptances of consecutive n-byte bursts | 16·n·D + 2·D |
| Minimum period of single-byte bursts (`i_cmd_last` always 1) | 18·D |

At f(`i_clk`) = 50 MHz:

| D | SCLK | Byte period |
|---|---|---|
| 1 | 25 MHz | 0.32 µs |
| 4 | 6.25 MHz | 1.28 µs |
| 255 | about 98.04 kHz | 81.6 µs |

Conditions for a continuous burst (no SCLK pause):
- The next command must be valid in the last cycle of the current transfer.
- `o_rsp_valid` must be 0 in that cycle. This means the response of the previous transfer was taken within 16·D − 1 cycles of becoming valid, for example with `i_rsp_ready` held at 1.

Back-pressure:
- If `o_rsp_valid` = 1 in the last cycle of a transfer, the next transfer is not started at its SCLK edge 16. The burst enters Pause (or Trail if it was the last byte).
- If the shown byte has still not been taken at the end of a running transfer, that transfer's byte becomes the held byte. No new transfer starts until both bytes have been taken.

Ordering: responses come out in command order (REQ-RSP-002).

**Example 1: single-byte burst, D = 1, mode 0.** Command `i_cmd_data` = 8'hA5, `i_cmd_last` = 1. The slave returns 8'h3C. `i_rsp_ready` = 1 throughout. Cycle n is the cycle starting at edge n. Edge 0 is the acceptance edge A. `i_miso` is driven by a mode-0 slave: bit 7 when `o_cs_n` falls, the next bit after each falling SCLK edge.

| Cycle | `i_cmd_valid` | `o_cmd_ready` | `o_cs_n` | `o_sclk` | `o_mosi` | `i_miso` | `o_rsp_valid` | `o_rsp_data` | Note |
|---|---|---|---|---|---|---|---|---|---|
| −1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 00 | Command presented, handshake at edge 0 |
| 0 | 0 | 0 | 0 | 0 | 1 (d7) | 0 (r7) | 0 | 00 | `o_cs_n` falls, d7 launched |
| 1 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 00 | SCLK edge 1 (rising): r7 = 0 captured at edge 1 |
| 2 | 0 | 0 | 0 | 0 | 0 (d6) | 0 (r6) | 0 | 00 | SCLK edge 2 (falling, shift) |
| 3 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 00 | Edge 3: r6 = 0 captured |
| 4 | 0 | 0 | 0 | 0 | 1 (d5) | 1 (r5) | 0 | 00 | |
| 5 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | 00 | Edge 5: r5 = 1 captured |
| 6 | 0 | 0 | 0 | 0 | 0 (d4) | 1 (r4) | 0 | 00 | |
| 7 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 00 | Edge 7: r4 = 1 captured |
| 8 | 0 | 0 | 0 | 0 | 0 (d3) | 1 (r3) | 0 | 00 | |
| 9 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 00 | Edge 9: r3 = 1 captured |
| 10 | 0 | 0 | 0 | 0 | 1 (d2) | 1 (r2) | 0 | 00 | |
| 11 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | 00 | Edge 11: r2 = 1 captured |
| 12 | 0 | 0 | 0 | 0 | 0 (d1) | 0 (r1) | 0 | 00 | |
| 13 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 00 | Edge 13: r1 = 0 captured |
| 14 | 0 | 0 | 0 | 0 | 1 (d0) | 0 (r0) | 0 | 00 | |
| 15 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 00 | Edge 15: r0 = 0 captured. Last cycle; `o_cmd_ready` = 0 because `i_cmd_last` = 1 |
| 16 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 3C | SCLK edge 16. Response loaded. Trail |
| 17 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 3C | `o_cs_n` rises at edge 17 (A + 17·D). Response taken at edge 17. Gap requirement met for D = 1 |

**Example 2: joining two bytes of one burst, D = 1, mode 0.** The transfer N has acceptance edge A and `i_cmd_last` = 0. Command N+1 is valid and the earlier response has been taken.

| Cycle | `i_cmd_valid` | `o_cmd_ready` | `o_sclk` | `o_mosi` | `o_rsp_valid` | Note |
|---|---|---|---|---|---|---|
| A+14 | 1 | 0 | 0 | d0 of N | 0 | |
| A+15 | 1 | 1 | 1 | d0 of N | 0 | Last cycle of N. Handshake at edge A+16 |
| A+16 | x | 0 | 0 | d7 of N+1 | 1 | SCLK edge 16 of N = acceptance edge of N+1. Byte N shown |
| A+17 | x | 0 | 1 | d7 of N+1 | 0 | SCLK edge 1 of N+1. Byte N taken at edge A+17 |
| A+18 | x | 0 | 0 | d6 of N+1 | 0 | SCLK edge 2 of N+1 |

**Example 3: back-pressure, any D.**
1. Byte N is shown at edge A_N + 16·D. Transfer N+1 starts at that edge.
2. `i_rsp_ready` stays 0. At edge A_N + 32·D, byte N+1 becomes the held byte and the burst enters Pause (or Trail), because `o_rsp_valid` = 1 forced `o_cmd_ready` = 0 in the last cycle.
3. When `i_rsp_ready` goes to 1, byte N is taken at edge H. Byte N+1 is loaded at H and `o_rsp_valid` stays 1.
4. Byte N+1 is taken at edge H + 1. After that, `o_cmd_ready` returns to 1 in Pause.

## 9 Registers

The block has no software-visible registers.

## 10 Errors and corner cases

The block has no error output. Every case below has a defined behaviour.

[REQ-ERR-001] When `i_cpol` or `i_cpha` changes while `o_cs_n` = 0 (an environment violation), the master shall not detect or report it and shall keep using CPOL_b and CPHA_b until the end of the burst (REQ-MODE-003).

[REQ-ERR-002] When `i_cpol` differs from CPOL_b at the edge where `o_cs_n` rises, `o_sclk` shall change to `i_cpol` at that edge (REQ-SCLK-006).

[REQ-ERR-003] When `i_cmd_valid` = 1 while `o_cmd_ready` = 0, the command shall wait without effect until a command handshake occurs.

[REQ-ERR-004] When `i_cmd_valid` = 1 while `i_rst_n` = 0, the master shall not accept the command (REQ-RST-007).

[REQ-ERR-005] When the response consumer never takes a response, the master shall keep `o_rsp_valid` = 1 with the same byte and shall not start any further transfer.

[REQ-ERR-006] When a burst is in Pause and no command ever arrives, `o_cs_n` shall stay 0 indefinitely.

[REQ-ERR-007] When `i_rst_n` is asserted during a transfer, `o_cs_n` shall go to 1 and `o_sclk` to `i_cpol` at once, even in the middle of an SCLK half period, and the partial byte shall be discarded (REQ-RST-008).

[REQ-ERR-008] When `i_rst_n` is asserted in Pause, Trail or the Idle gap, the master shall go to the reset state of REQ-RST-002 to REQ-RST-006, and pending bytes shall be discarded.

[REQ-ERR-009] A response handshake at exactly edge A + 16·D of a transfer shall make the received byte of that transfer load into `o_rsp_data` at that edge, with `o_rsp_valid` staying 1 (REQ-RSP-003).

[REQ-ERR-010] A timing violation on `i_miso` (data changing too close to a sampling edge) shall not be detected. The captured bit is then undefined.

Other corner cases:

| Case | Behaviour |
|---|---|
| `i_cmd_last` = 1 on every command | Every byte is its own burst. Minimum period 18·D cycles. |
| `i_cmd_last` = 0 forever | The burst never ends. `o_cs_n` stays 0 and transfers continue as commands arrive. |
| D = 1 | Each SCLK half period is 1 cycle (SCLK = f(`i_clk`)/2). Lead, trail and minimum gap are 1 cycle. `o_cmd_ready` in Idle is 1 from the cycle in which `o_cs_n` rises (REQ-CMD-007 gives no blocked cycle). A shift edge and the next sampling edge are 1 cycle apart. |
| D = 255 | Each half period is 255 cycles and a byte takes 4080 cycles. The half-period count must reach 255 without overflow. |
| Mode change between bursts | Allowed in any Idle cycle, including the cycle just before the acceptance edge. The new values are captured at the acceptance edge. |

## 11 Configurations

| ID | Parameter values | Purpose |
|---|---|---|
| CFG-BASE | defaults (PARA_SPI_CLK_DIV=4) | Main configuration, all four SPI modes |
| CFG-MIN | PARA_SPI_CLK_DIV=1 | Smallest legal divider (SCLK = f(i_clk)/2), all four SPI modes |
| CFG-MAX | PARA_SPI_CLK_DIV=255 | Largest legal divider (half-period count width), all four SPI modes with short bursts |

The verification runs every configuration listed here (`run_set.json`). The SPI mode is a run-time input, so each configuration runs all four modes.

## 12 Verification requirements

Environment obligations (protocol duties of the blocks that drive the inputs):

[ENV-001] The environment shall release `i_rst_n` synchronously to `i_clk`. Assertion may be asynchronous.

[ENV-002] The environment shall keep `i_cmd_valid` = 0 while `i_rst_n` = 0.

[ENV-003] The environment shall change `i_cpol` and `i_cpha` only while `o_cs_n` = 1. Error tests may violate this rule on purpose to check REQ-ERR-001.

[ENV-004] The SPI slave (testbench model) shall drive `i_miso` from `o_sclk` and `o_cs_n` only. With CPHA = 0 it puts bit 7 when `o_cs_n` falls and the next bit after each trailing SCLK edge. With CPHA = 1 it puts bit 7 − j after leading SCLK edge 2·j + 1.

[ENV-005] The slave model shall change `i_miso` only after the `i_clk` edge at which `o_sclk` or `o_cs_n` changed, never in a way that changes the value seen at a sampling edge.

[ENV-006] In silicon, `i_miso` shall meet setup and hold time to `i_clk` at each sampling edge. With D = 1, the slave clock-to-output plus the board round trip must fit in one `i_clk` period minus setup time.

The command stream is not required to keep `i_cmd_valid`, `i_cmd_data` or `i_cmd_last` stable before acceptance (REQ-CMD-004). The response consumer may drive `i_rsp_ready` with any pattern.

Checks and special setups:

[VER-001] The verification shall run all four modes in every configuration of section 11, with random bytes on `i_cmd_data` and from the slave model.

[VER-002] The verification shall use burst lengths 1, 2 and at least 16, and shall mix bursts with and without pauses (`i_cmd_valid` gaps of 0, 1 and many cycles).

[VER-003] A scoreboard shall check that each response equals the byte sent by the slave during the matching command, in order, with no loss or duplicate (REQ-RSP-001, REQ-RSP-002, REQ-RSP-011).

[VER-004] A slave-side monitor shall check MOSI data at every sampling edge and the SCLK edge times (A + k·D). It shall also check the lead, trail and gap times, the SCLK idle level and that `o_mosi` never changes at a sampling edge.

[VER-005] The verification shall check `o_cmd_ready` cycle by cycle against REQ-CMD-006 to REQ-CMD-012, including the blocked first D − 1 Idle cycles.

[VER-006] Back-pressure tests shall hold `i_rsp_ready` = 0 for long periods so that a held byte is created. They shall cover a response handshake exactly at edge A + 16·D (REQ-ERR-009) and random `i_rsp_ready` patterns.

[VER-007] Reset tests shall assert `i_rsp_ready` … shall assert `i_rst_n` between `i_clk` edges in each phase (Transfer, Pause, Trail, Idle gap, with a held byte). They shall check that outputs take reset values at once and that no response of the aborted transfer appears.

[VER-008] A test shall toggle `i_cpol` while `i_rst_n` = 0 and in Idle, and check that `o_sclk` follows it in the same cycle (REQ-SCLK-005, REQ-RST-003).

[VER-009] A test shall change `i_cpol` and `i_cpha` in the cycle just before a burst-start acceptance edge and check that the new values are used.

[VER-010] An error test shall change `i_cpol` and `i_cpha` during a burst and check that the burst finishes in the captured mode (REQ-ERR-001, REQ-ERR-002).

[VER-011] Coverage shall include:
- Mode × configuration.
- Continuous join (Example 2).
- Pause entry and exit.
- Held byte created and released.
- Reset in each phase.
- `i_cmd_last` = 1 on the first byte.

Behaviour visible only through the ports:
- The held byte is seen only through response order and `o_cmd_ready`.
- CPOL_b and CPHA_b are seen only through `o_sclk`, `o_mosi` and the received data when the inputs change during a burst.

REQ-PAR-001 is checked by elaborating once with an illegal value, not by simulation.

## 13 Implementation constraints

[REQ-IMP-001] The block shall meet timing at 50 MHz `i_clk` (20 ns period) in the GF180MCU technology, at worst-case corner.

[REQ-IMP-002] The RTL shall follow `docs/RTL_RULES.md` (REF-003).

[REQ-IMP-003] All flip-flops shall be clocked on the rising edge of `i_clk` and reset asynchronously by `i_rst_n`. The RTL shall contain no latches, no clock gating and no derived clocks.

[REQ-IMP-004] `o_cs_n` and `o_mosi` shall be driven directly by flip-flops.

[REQ-IMP-005] While `o_cs_n` = 0, `o_sclk` shall come from a flip-flop value. The only combinational path from an input to `o_sclk` shall be the `i_cpol` path used while `o_cs_n` = 1 or during reset.

[REQ-IMP-006] `o_sclk` should be free of glitches when `o_cs_n` changes. The selection between `i_cpol` and the internal SCLK value should be built so that equal inputs give no static hazard.

[REQ-IMP-007] `o_cmd_ready`, `o_rsp_valid` and `o_rsp_data` shall be driven by flip-flops or by logic of flip-flops only. They shall have no combinational path from any input.

[REQ-IMP-008] `i_miso` shall be captured directly into a data flip-flop with no synchroniser. The integrator shall constrain the input delay of `i_miso`.

[REQ-IMP-009] The half-period counter shall be wide enough for D = 255 (at least 8 bits).

The area budget has not been given (open question OQ-004). The block is expected to be small: one byte each of shift-out, shift-in, response and held storage, plus counters.

## 14 Decisions and open questions

| ID | Question | Decision | By | Date |
|---|---|---|---|---|
| DEC-001 | Exact lead, trail and minimum gap ("at least one half period") | Exactly D cycles for lead and trail. Gap at least D cycles, exactly D when the next command is waiting | spec-draft (assumption) | 2026-11-19 |
| DEC-002 | When can a command be accepted | Idle (after D − 1 blocked cycles), Pause, or the last cycle of a non-last transfer, and only if `o_rsp_valid` = 0. `o_cmd_ready` has no combinational input path | spec-draft (assumption) | 2026-11-19 |
| DEC-003 | Meaning of "does not start the next transfer if the response is not taken" with no-gap bursts | A transfer starts only when `o_rsp_valid` = 0. The byte ending at the same edge is shown, and one more byte can be held inside the master, so nothing is lost | spec-draft (assumption) | 2026-11-19 |
| DEC-004 | When the response appears | At SCLK edge 16 (A + 16·D) in all modes, also for CPHA = 0 where the last bit is sampled at edge 15 | spec-draft (assumption) | 2026-11-19 |
| DEC-005 | `o_mosi` outside transfers, and with CPHA = 1 before edge 1 | Holds its last value. 0 after reset | spec-draft (assumption) | 2026-11-19 |
| DEC-006 | `o_sclk` idle level "of the current `i_cpol`" during reset and Idle | Combinational from `i_cpol` while `o_cs_n` = 1. Registered from CPOL_b while `o_cs_n` = 0 | spec-draft (assumption) | 2026-11-19 |
| DEC-007 | Mode inputs changed during a burst | Ignored. Captured values are used until `o_cs_n` rises | spec-draft (assumption) | 2026-11-19 |
| DEC-008 | Reset in the middle of a burst | Immediate abort. Pending bytes discarded. Gap guarantee does not apply across reset | spec-draft (assumption) | 2026-11-19 |
| DEC-009 | Illegal `PARA_SPI_CLK_DIV` | Elaboration error | spec-draft (assumption) | 2026-11-19 |
| DEC-010 | Configurations | CFG-BASE and CFG-MIN as asked, plus CFG-MAX (D = 255) for the parameter extreme | spec-draft (assumption) | 2026-11-19 |
| DEC-011 | `o_rsp_data` reset value and value while not valid | 8'h00 after reset. Otherwise keeps the last loaded byte | spec-draft (assumption) | 2026-11-19 |
| OQ-001 | Should a transfer also be allowed to start when the shown byte is taken in the last cycle (combinational `i_rsp_ready` to `o_cmd_ready`) to avoid a pause? | Open. Interim: no (DEC-002) | Designer | 2026-11-19 |
| OQ-002 | Is D = 1 (25 MHz SCLK at 50 MHz) meant for real slaves, given the 20 ns MISO round-trip budget? | Open. Interim: legal and verified in simulation. Silicon timing is an integrator duty (ENV-006) | Designer | 2026-11-19 |
| OQ-003 | Should `o_mosi` be driven to 0 (or 1) in Idle instead of holding its last value? | Open. Interim: hold (DEC-005) | Designer | 2026-11-19 |
| OQ-004 | What is the area budget on GF180MCU? | Open | Designer | 2026-11-19 |
| OQ-005 | Should Pause have a timeout that releases `o_cs_n`? | Open. Interim: no timeout | Designer | 2026-11-19 |
| OQ-006 | Should the master enforce `o_cs_n` high for at least D cycles after reset release? | Open. Interim: no (REQ-RST-011) | Designer | 2026-11-19 |
| OQ-007 | Should CFG-MAX stay in the run set (longer simulation)? | Open. Interim: kept | Designer | 2026-11-19 |

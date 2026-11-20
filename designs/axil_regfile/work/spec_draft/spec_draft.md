# `axil_regfile` Design Specification

Revision: `0.2`, `2026-11-19`. Top module: `m_axil_regfile`.

## 1 Overview

### 1.1 Purpose
`axil_regfile` is a bank of PARA_NUM_REGS 32-bit read/write control registers and one 32-bit read-only status register. A CPU reads and writes them through an AXI4-Lite subordinate port. The current value of every read/write register drives the SoC logic directly on `o_regs`. A read of the status register returns the SoC status word `i_status`.

### 1.2 Features
- AXI4-Lite subordinate port with a 32-bit data bus and a PARA_ADDR_W-bit address bus (7 to 16 bits).
- 1 to 16 read/write registers at byte addresses 0x00 + 4k. Each one resets to 0.
- Byte-lane writes controlled by `i_s_axi_wstrb`.
- A read-only status register at byte address 0x40. It returns `i_status` as sampled when the read address is taken.
- An access to an unmapped address answers SLVERR. An unmapped read returns 0.
- The write address and the write data can arrive in either order or at the same edge.
- The read path and the write path work independently, so a read and a write can be in progress at the same time.
- Fixed latency: one cycle from the last write handshake to the write response, and one cycle from the read address handshake to the read data.
- Every output is registered, so no combinational path runs from an input to an output.
- One clock, and one active-low reset with asynchronous assertion.

### 1.3 Out of scope
- AXI4 full features: bursts, IDs, more than one outstanding transaction per direction, exclusive access, QoS, region, cache and user signals.
- The response codes EXOKAY (`2'b01`) and DECERR (`2'b11`). The block never produces them.
- Protection checking. `i_s_axi_awprot` and `i_s_axi_arprot` are ignored.
- Sub-word addressing. Address bits [1:0] are ignored and there is no unaligned-access error.
- Special register types (write-1-to-clear, self-clearing, set/clear aliases, interrupts) and parity or ECC.
- Clock-domain crossing. `i_status` and every other input are synchronous to `i_clk`.
- Behaviour with illegal parameter values, or when the manager breaks the AXI handshake rules.

## 2 References

| ID | Document | Revision | Used for |
|---|---|---|---|
| REF-001 | ARM IHI 0022, AMBA AXI and ACE Protocol Specification | Issue H or later | AXI4-Lite channel handshake rules and response encodings (OKAY, SLVERR) |
| REF-002 | `docs/RTL_RULES.md` | Current revision of the repository | RTL coding rules |
| REF-003 | AXI4-Lite register file: design description (input of `nnc spec-draft`) | As delivered | Source of the requirements in this specification |

## 3 Terms

| Term | Meaning |
|---|---|
| Manager | The block that drives the AXI4-Lite inputs of this port (the CPU side). |
| AW, W, B, AR, R | The write address, write data, write response, read address and read data channels. |
| Transfer (handshake) | A rising edge of `i_clk` at which the valid and the ready of a channel are both 1 and `i_rst_n` is 1. The channel's payload is taken at that edge. |
| Edge n / cycle n | Edge n is the n-th rising edge of `i_clk`. Cycle n is the clock period between edge n-1 and edge n: it starts at edge n-1 and ends at edge n. "From edge n" means "in cycle n+1 and every later cycle". |
| Ea, Ew | The edge of the AW transfer and the edge of the W transfer of one write transaction. |
| Ec | The completion edge of a write: the later of Ea and Ew. If both transfers happen at the same edge, Ec is that edge. |
| Eb | The edge of the B transfer of a write transaction. |
| Ear, Er | The edge of the AR transfer and the edge of the R transfer of one read transaction. |
| Held write address | In cycle n, a write address is held if its AW transfer happened at an edge e <= n-1 and the B transfer of its transaction has not happened at any edge <= n-1. |
| Held write data | In cycle n, write data is held if its W transfer happened at an edge e <= n-1 and the B transfer of its transaction has not happened at any edge <= n-1. |
| Held read address | In cycle n, a read address is held if its AR transfer happened at an edge e <= n-1 and the R transfer of its transaction has not happened at any edge <= n-1. |
| R1 | The first rising edge of `i_clk` at which `i_rst_n` is 1 after a period with `i_rst_n` at 0. |
| Word index | Bits [PARA_ADDR_W-1:2] of an address, read as an unsigned number. |
| Mapped register | Read/write register k, 0 <= k < PARA_NUM_REGS, at byte address 4k. |
| Status register | The read-only register at byte address 0x40, word index 16. |
| Unmapped address | An address that selects neither a mapped register nor the status register. |
| OKAY, SLVERR | Response codes `2'b00` and `2'b10` on `o_s_axi_bresp` and `o_s_axi_rresp`. |

## 4 Parameters

| Parameter | Default | Legal values | Description |
|---|---|---|---|
| PARA_NUM_REGS | 8 | 1 to 16 | Number of read/write registers |
| PARA_ADDR_W | 8 | 7 to 16 | Width in bits of `i_s_axi_awaddr` and `i_s_axi_araddr`; 7 is the minimum that reaches the status register at 0x40 |
| LPARA_REGS_W | Derived | - | PARA_NUM_REGS*32 |

LPARA_REGS_W is the width of `o_regs` in bits: 32 with PARA_NUM_REGS = 1, 256 with the default, 512 with PARA_NUM_REGS = 16.

[REQ-PAR-001] The block shall behave as this specification states for every combination of PARA_NUM_REGS from 1 to 16 and PARA_ADDR_W from 7 to 16.

[REQ-PAR-002] LPARA_REGS_W shall be a local parameter equal to PARA_NUM_REGS*32 that cannot be overridden from outside the module.

[REQ-PAR-003] The RTL should stop elaboration with an error message when PARA_NUM_REGS or PARA_ADDR_W is outside its legal range.

[REQ-PAR-004] Behaviour with illegal parameter values is not specified and shall not be verified.

## 5 Interface

**`m_axil_regfile`**: all ports (`CLK`)

| Port | Direction | Width | Signal type | Reset value | Clock domain | Meaning |
|---|---|---|---|---|---|---|
| i_clk | input | 1 | Clock | Not applicable | CLK | Clock, rising edge |
| i_rst_n | input | 1 | Reset (asynchronous assertion, synchronous release) | Not applicable | CLK | Active-low reset |
| i_s_axi_awvalid | input | 1 | Control | Not applicable | CLK | Write address valid |
| o_s_axi_awready | output | 1 | Control | 0 | CLK | Write address ready |
| i_s_axi_awaddr | input | PARA_ADDR_W | Data | Not applicable | CLK | Write byte address; bits [1:0] ignored |
| i_s_axi_awprot | input | 3 | Data | Not applicable | CLK | Write protection type; ignored |
| i_s_axi_wvalid | input | 1 | Control | Not applicable | CLK | Write data valid |
| o_s_axi_wready | output | 1 | Control | 0 | CLK | Write data ready |
| i_s_axi_wdata | input | 32 | Data | Not applicable | CLK | Write data; byte lane i is bits 8i+7..8i |
| i_s_axi_wstrb | input | 4 | Data | Not applicable | CLK | Write strobes; bit i enables byte lane i |
| o_s_axi_bvalid | output | 1 | Control | 0 | CLK | Write response valid |
| i_s_axi_bready | input | 1 | Control | Not applicable | CLK | Write response ready |
| o_s_axi_bresp | output | 2 | Data | 0 | CLK | Write response: 2'b00 OKAY or 2'b10 SLVERR |
| i_s_axi_arvalid | input | 1 | Control | Not applicable | CLK | Read address valid |
| o_s_axi_arready | output | 1 | Control | 0 | CLK | Read address ready |
| i_s_axi_araddr | input | PARA_ADDR_W | Data | Not applicable | CLK | Read byte address; bits [1:0] ignored |
| i_s_axi_arprot | input | 3 | Data | Not applicable | CLK | Read protection type; ignored |
| o_s_axi_rvalid | output | 1 | Control | 0 | CLK | Read data valid |
| i_s_axi_rready | input | 1 | Control | Not applicable | CLK | Read data ready |
| o_s_axi_rdata | output | 32 | Data | 0 | CLK | Read data |
| o_s_axi_rresp | output | 2 | Data | 0 | CLK | Read response: 2'b00 OKAY or 2'b10 SLVERR |
| o_regs | output | LPARA_REGS_W | Data | 0 | CLK | Current values of the read/write registers; register k is bits 32k+31..32k |
| i_status | input | 32 | Data | Not applicable | CLK | SoC status word; returned by a read of address 0x40 |

[REQ-IF-001] Every output shall change value only at a rising edge of `i_clk` or when `i_rst_n` is asserted, so that no output depends combinationally on any input in the same cycle.

[REQ-IF-002] Bits 32k+31..32k of `o_regs` shall carry the current value of read/write register k, for every k from 0 to PARA_NUM_REGS-1.

[REQ-IF-003] Byte lane i (i = 0 to 3) of a register shall be bits 8i+7..8i, shall correspond to `i_s_axi_wdata[8i+7:8i]` and `o_s_axi_rdata[8i+7:8i]`, and shall be enabled by `i_s_axi_wstrb[i]`.

[REQ-IF-004] The values of `i_s_axi_awprot` and `i_s_axi_arprot` shall have no effect on any output.

## 6 Clocks and resets

### 6.1 Clocks
The block has one clock, `i_clk`, which defines the clock domain CLK. The target frequency is 50 MHz. Every flip-flop of the block is clocked on the rising edge of `i_clk`. Every input, including `i_status`, is synchronous to `i_clk`. The block has no clock-domain crossing and contains no synchronizer.

[REQ-CLK-001] Every flip-flop of the block shall be clocked by the rising edge of `i_clk`.

### 6.2 Resets
`i_rst_n` is active low. Assertion is asynchronous. Release is synchronous to `i_clk`, and the environment guarantees this (see section 12).

[REQ-RST-001] While `i_rst_n` is 0, `o_s_axi_awready`, `o_s_axi_wready`, `o_s_axi_arready`, `o_s_axi_bvalid` and `o_s_axi_rvalid` shall be 0.

[REQ-RST-002] While `i_rst_n` is 0, `o_s_axi_bresp`, `o_s_axi_rresp` and `o_s_axi_rdata` shall be 0.

[REQ-RST-003] While `i_rst_n` is 0, every bit of `o_regs` shall be 0.

[REQ-RST-004] When `i_rst_n` goes from 1 to 0, every output shall take its reset value without waiting for a rising edge of `i_clk`.

[REQ-RST-005] No transfer shall happen on any channel at an edge where `i_rst_n` is 0, whatever the values of `i_s_axi_awvalid`, `i_s_axi_wvalid`, `i_s_axi_arvalid`, `i_s_axi_bready` and `i_s_axi_rready`.

[REQ-RST-006] No transfer shall happen on any channel at edge R1, because `o_s_axi_awready`, `o_s_axi_wready` and `o_s_axi_arready` are 0 in the cycle that ends at R1 and `o_s_axi_bvalid` and `o_s_axi_rvalid` are 0 in that cycle.

[REQ-RST-007] `o_s_axi_awready`, `o_s_axi_wready` and `o_s_axi_arready` shall be 1 from edge R1, that is, in the cycle that starts at R1.

[REQ-RST-008] `o_s_axi_bvalid` and `o_s_axi_rvalid` shall stay 0 after R1 until a write or read transaction makes them 1 as section 7 states.

[REQ-RST-009] When `i_rst_n` is asserted while a write address, write data, write response or read address is held or pending, the held state shall be discarded. No B or R response shall be given for that transaction after release, and no register shall be written by it after release.

[REQ-RST-010] A valid that the manager holds at 1 through reset and after R1 shall be treated as a new transfer request. It is taken at the first edge after R1 where the matching ready is 1, which is the edge after R1 at the earliest.

## 7 Functional description

### 7.1 Address decode

[REQ-DEC-001] Bits [1:0] of `i_s_axi_awaddr` and `i_s_axi_araddr` shall have no effect on any output.

[REQ-DEC-002] An address whose word index is k, with 0 <= k < PARA_NUM_REGS, shall select read/write register k.

[REQ-DEC-003] An address whose word index is 16 (byte address 0x40 to 0x43) shall select the status register.

[REQ-DEC-004] Every other address shall be unmapped. This includes word indices PARA_NUM_REGS to 15, word indices 17 to 31, and every address with a 1 in any bit from bit 7 to bit PARA_ADDR_W-1.

[REQ-DEC-005] The decode shall compare all bits [PARA_ADDR_W-1:2] of the address, so that no mapped register or status register appears at more than one word index (no aliasing).

[REQ-DEC-006] A write transaction shall be decoded from the address taken at its AW transfer.

[REQ-DEC-007] A read transaction shall be decoded from the address taken at its AR transfer.

### 7.2 Write address and write data acceptance

[REQ-WR-001] In every cycle after R1 in which no write address is held, `o_s_axi_awready` shall be 1.

[REQ-WR-002] In every cycle in which a write address is held, `o_s_axi_awready` shall be 0.

[REQ-WR-003] In every cycle after R1 in which no write data is held, `o_s_axi_wready` shall be 1.

[REQ-WR-004] In every cycle in which write data is held, `o_s_axi_wready` shall be 0.

[REQ-WR-005] The block shall take the AW transfer and the W transfer of one transaction in either order or at the same edge, and shall not answer before it has taken both.

[REQ-WR-006] After an AW transfer, the block shall take no other AW transfer until the edge after Eb of that transaction.

[REQ-WR-007] After a W transfer, the block shall take no other W transfer until the edge after Eb of that transaction.

[REQ-WR-008] The write strobes and write data used by a transaction shall be the values of `i_s_axi_wstrb` and `i_s_axi_wdata` taken at its W transfer.

### 7.3 Register update

[REQ-WR-010] When a write transaction selects read/write register k, then at edge Ec, for each byte lane i with `i_s_axi_wstrb[i]` = 1 (as taken at Ew), bits 8i+7..8i of register k shall take the value of bits 8i+7..8i of the write data taken at Ew.

[REQ-WR-011] When a write transaction selects read/write register k, the byte lanes of register k whose strobe bit is 0 shall keep their value.

[REQ-WR-012] The value written at Ec shall appear on `o_regs[32k+31:32k]` from edge Ec, that is, in the cycle that starts at Ec.

[REQ-WR-013] A write transaction shall change no bit of `o_regs` outside bits 32k+31..32k of the register it selects.

[REQ-WR-014] A write transaction shall change its register only at its edge Ec and only once.

[REQ-WR-015] A write transaction that selects the status register shall change no bit of `o_regs`.

[REQ-WR-016] A write transaction to an unmapped address shall change no bit of `o_regs`.

[REQ-WR-017] A write transaction to read/write register k with `i_s_axi_wstrb` = 4'b0000 shall change no bit of `o_regs` and shall answer OKAY.

[REQ-WR-018] Bits of `o_regs` shall change only at edge Ec of a write transaction that selects them or when `i_rst_n` is asserted.

### 7.4 Write response

[REQ-WR-020] `o_s_axi_bvalid` shall be 1 from edge Ec of a write transaction, that is, in the cycle that starts at Ec.

[REQ-WR-021] Once `o_s_axi_bvalid` is 1, it shall stay 1 and `o_s_axi_bresp` shall stay unchanged until and including the cycle that ends at Eb.

[REQ-WR-022] `o_s_axi_bvalid` shall be 0 from edge Eb, unless `i_rst_n` is asserted earlier.

[REQ-WR-023] The block shall give exactly one B transfer for each write transaction that reaches Ec, and `o_s_axi_bvalid` shall be 0 in every cycle in which no such transaction is waiting for its B transfer.

[REQ-WR-024] `o_s_axi_bresp` shall be 2'b00 (OKAY) for a write transaction that selects a read/write register or the status register.

[REQ-WR-025] `o_s_axi_bresp` shall be 2'b10 (SLVERR) for a write transaction to an unmapped address.

[REQ-WR-026] `o_s_axi_bresp` shall never be 2'b01 or 2'b11 while `o_s_axi_bvalid` is 1.

[REQ-WR-027] While `o_s_axi_bvalid` is 0 and `i_rst_n` is 1, the value of `o_s_axi_bresp` is not specified and shall not be checked.

### 7.5 Read

[REQ-RD-001] In every cycle after R1 in which no read address is held, `o_s_axi_arready` shall be 1.

[REQ-RD-002] In every cycle in which a read address is held, `o_s_axi_arready` shall be 0.

[REQ-RD-003] After an AR transfer, the block shall take no other AR transfer until the edge after Er of that transaction.

[REQ-RD-004] `o_s_axi_rvalid` shall be 1 from edge Ear of a read transaction, that is, in the cycle that starts at Ear.

[REQ-RD-005] Once `o_s_axi_rvalid` is 1, it shall stay 1 and `o_s_axi_rdata` and `o_s_axi_rresp` shall stay unchanged until and including the cycle that ends at Er.

[REQ-RD-006] `o_s_axi_rvalid` shall be 0 from edge Er, unless `i_rst_n` is asserted earlier.

[REQ-RD-007] The block shall give exactly one R transfer for each AR transfer, and `o_s_axi_rvalid` shall be 0 in every cycle in which no read transaction is waiting for its R transfer.

[REQ-RD-008] For a read transaction that selects read/write register k, `o_s_axi_rdata` shall equal the value of `o_regs[32k+31:32k]` in the cycle that ends at Ear.

[REQ-RD-009] For a read transaction that selects the status register, `o_s_axi_rdata` shall equal the value of `i_status` in the cycle that ends at Ear.

[REQ-RD-010] A change of `i_status` after Ear shall not change `o_s_axi_rdata` of the read transaction in progress.

[REQ-RD-011] `o_s_axi_rresp` shall be 2'b00 (OKAY) for a read transaction that selects a read/write register or the status register.

[REQ-RD-012] For a read transaction to an unmapped address, `o_s_axi_rdata` shall be 32'h0000_0000 and `o_s_axi_rresp` shall be 2'b10 (SLVERR).

[REQ-RD-013] `o_s_axi_rresp` shall never be 2'b01 or 2'b11 while `o_s_axi_rvalid` is 1.

[REQ-RD-014] While `o_s_axi_rvalid` is 0 and `i_rst_n` is 1, the values of `o_s_axi_rdata` and `o_s_axi_rresp` are not specified and shall not be checked.

[REQ-RD-015] A read transaction shall change no bit of `o_regs`.

### 7.6 Concurrent read and write

[REQ-CC-001] The AR and R channels shall work independently of the AW, W and B channels. Whether a write is held or waiting for its B transfer shall not change the value or timing of `o_s_axi_arready`, `o_s_axi_rvalid`, `o_s_axi_rdata` or `o_s_axi_rresp`, except for the register value returned as stated in REQ-CC-003 to REQ-CC-006.

[REQ-CC-002] Whether a read is held or waiting for its R transfer shall not change the value or timing of `o_s_axi_awready`, `o_s_axi_wready`, `o_s_axi_bvalid`, `o_s_axi_bresp` or `o_regs`.

[REQ-CC-003] When the AR transfer of a read of register k happens at the same edge as Ec of a write to register k, the read shall return the value of register k before that write (the old value).

[REQ-CC-004] When Ec of a write to register k is before Ear of a read of register k, the read shall return the value written by that write, unless another write to register k with an Ec before Ear came in between.

[REQ-CC-005] When Ec of a write to register k is after Ear of a read of register k, that write shall not change `o_s_axi_rdata` of the read.

[REQ-CC-006] The read data of register k shall always equal one whole value that register k held in the cycle that ends at Ear, and never a mix of the bytes of two values.

## 8 Timing and protocol

### 8.1 Latency and throughput

| Operation | Value | Requirement |
|---|---|---|
| Ec to `o_s_axi_bvalid` = 1 | Exactly 1 cycle: 1 in the cycle that starts at Ec | REQ-WR-020 |
| Ec to new value on `o_regs` | Exactly 1 cycle: visible in the cycle that starts at Ec | REQ-WR-012 |
| Eb to `o_s_axi_awready` and `o_s_axi_wready` = 1 | Exactly 1 cycle: 1 in the cycle that starts at Eb | REQ-WR-001, REQ-WR-003 |
| Earliest Eb | Ec + 1 edge | REQ-WR-020 |
| Write throughput | At most 1 write every 2 cycles (AW and W at edge n, B at edge n+1, next AW and W at edge n+2) | REQ-TIM-001 |
| Ear to `o_s_axi_rvalid` = 1 | Exactly 1 cycle: 1 in the cycle that starts at Ear | REQ-RD-004 |
| Er to `o_s_axi_arready` = 1 | Exactly 1 cycle: 1 in the cycle that starts at Er | REQ-RD-001 |
| Read throughput | At most 1 read every 2 cycles | REQ-TIM-002 |
| Write-to-read visibility | A read with Ear >= Ec + 1 edge returns the new value; a read with Ear = Ec returns the old value | REQ-CC-003, REQ-CC-004 |

[REQ-TIM-001] When the manager drives `i_s_axi_awvalid`, `i_s_axi_wvalid` and `i_s_axi_bready` at 1 continuously, the block shall complete one write transaction every 2 cycles, with the AW and W transfers at edge n, the B transfer at edge n+1, and the next AW and W transfers at edge n+2.

[REQ-TIM-002] When the manager drives `i_s_axi_arvalid` and `i_s_axi_rready` at 1 continuously, the block shall complete one read transaction every 2 cycles, with the AR transfer at edge n, the R transfer at edge n+1, and the next AR transfer at edge n+2.

[REQ-TIM-003] Readies of the block shall not wait for the matching valid. `o_s_axi_awready`, `o_s_axi_wready` and `o_s_axi_arready` shall be 1 whenever REQ-WR-001, REQ-WR-003 and REQ-RD-001 say so, whatever the values of the valids.

### 8.2 Back-pressure and ordering

[REQ-TIM-010] While `i_s_axi_bready` is 0 and `o_s_axi_bvalid` is 1, the block shall keep the response pending and shall take no new AW or W transfer, for any number of cycles.

[REQ-TIM-011] While `i_s_axi_rready` is 0 and `o_s_axi_rvalid` is 1, the block shall keep the read data pending and shall take no new AR transfer, for any number of cycles.

[REQ-TIM-012] Back-pressure on the B channel shall not stall the AR or R channel, and back-pressure on the R channel shall not stall the AW, W or B channel.

[REQ-TIM-013] Because only one write and one read can be in progress, the block shall answer write transactions in the order of their Ec and read transactions in the order of their Ear. The only order defined between reads and writes is the one given in section 7.6.

### 8.3 Cycle-by-cycle examples
Row n shows the values during cycle n, which ends at edge n. A transfer listed in row n happens at edge n. `-` means the value does not matter or is not specified.

Example 1: write to register 1 (address 0x04). The address arrives before the data, `wstrb` = 4'b0011, and the manager holds back the B response for one cycle. Register 1 is 0 at the start.

| Cycle | awvalid | awready | awaddr | wvalid | wready | wdata | wstrb | bvalid | bready | bresp | o_regs[63:32] | Event at the end edge |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 0x04 | 0 | 1 | - | - | 0 | 0 | - | 0x0000_0000 | AW transfer (Ea) |
| 2 | 0 | 0 | - | 1 | 1 | 0xA5A5_1234 | 0x3 | 0 | 0 | - | 0x0000_0000 | W transfer (Ew = Ec); register 1 written |
| 3 | 0 | 0 | - | 0 | 0 | - | - | 1 | 0 | 2'b00 | 0x0000_1234 | Response held back |
| 4 | 0 | 0 | - | 0 | 0 | - | - | 1 | 1 | 2'b00 | 0x0000_1234 | B transfer (Eb) |
| 5 | 0 | 1 | - | 0 | 1 | - | - | 0 | - | - | 0x0000_1234 | Idle; new write can be taken |

Example 2: write to an unmapped address (0x44). The address and the data arrive at the same edge and `bready` is 1.

| Cycle | awvalid | awready | awaddr | wvalid | wready | bvalid | bready | bresp | o_regs | Event at the end edge |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 0x44 | 1 | 1 | 0 | 1 | - | unchanged | AW and W transfers (Ec) |
| 2 | 0 | 0 | - | 0 | 0 | 1 | 1 | 2'b10 | unchanged | B transfer, SLVERR |
| 3 | 0 | 1 | - | 0 | 1 | 0 | 1 | - | unchanged | Idle |

Example 3: read of the status register (0x40), with back-pressure on R while `i_status` changes.

| Cycle | arvalid | arready | araddr | i_status | rvalid | rready | rdata | rresp | Event at the end edge |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 0x40 | 0x1234_5678 | 0 | 0 | - | - | AR transfer (Ear); i_status sampled |
| 2 | 0 | 0 | - | 0x9ABC_DEF0 | 1 | 0 | 0x1234_5678 | 2'b00 | Data held back |
| 3 | 0 | 0 | - | 0x9ABC_DEF0 | 1 | 1 | 0x1234_5678 | 2'b00 | R transfer (Er) |
| 4 | 0 | 1 | - | 0x9ABC_DEF0 | 0 | - | - | - | Idle |

Example 4: reset release while the manager holds `awvalid` at 1.

| Cycle | i_rst_n | awvalid | awready | Event at the end edge |
|---|---|---|---|---|
| 1 | 0 | 1 | 0 | No transfer (reset) |
| 2 | 1 | 1 | 0 | Edge R1; no transfer |
| 3 | 1 | 1 | 1 | AW transfer |

## 9 Registers

| Offset | Name | Field | Bits | Access | Reset | Description |
|---|---|---|---|---|---|---|
| 0x00 + 4k, k = 0 to PARA_NUM_REGS-1 | REG_k | VALUE | 31:0 | RW | 0x0000_0000 | Control value k. Drives `o_regs[32k+31:32k]`. Byte lanes are written under `i_s_axi_wstrb`. Reads return the current value with OKAY. |
| 0x40 | STATUS | VALUE | 31:0 | RO | Not applicable | Read returns `i_status` sampled at Ear, with OKAY. A write changes nothing and answers OKAY. |
| 4*PARA_NUM_REGS to 0x3C | Reserved | - | 31:0 | - | - | Unmapped; does not exist when PARA_NUM_REGS = 16. Read returns 0 with SLVERR. A write changes nothing and answers SLVERR. |
| 0x44 to 2^PARA_ADDR_W - 4 | Reserved | - | 31:0 | - | - | Unmapped. Read returns 0 with SLVERR. A write changes nothing and answers SLVERR. |

Access codes: RW is readable and writable. RO is read-only; a write is ignored and answers OKAY. Offsets are byte addresses with bits [1:0] ignored. For the default configuration (PARA_NUM_REGS = 8, PARA_ADDR_W = 8): REG_0 to REG_7 are at 0x00 to 0x1C, 0x20 to 0x3C is unmapped, STATUS is at 0x40, and 0x44 to 0xFC is unmapped.

[REQ-REG-001] The register map shall be exactly the table above for every legal parameter combination.

## 10 Errors and corner cases

### 10.1 Error conditions

[REQ-ERR-001] A write to an unmapped address shall be detected by the decode of the address taken at Ea, shall change no register, and shall answer `o_s_axi_bresp` = 2'b10 (SLVERR) with the normal write timing.

[REQ-ERR-002] A read from an unmapped address shall be detected by the decode of the address taken at Ear, and shall return `o_s_axi_rdata` = 0 and `o_s_axi_rresp` = 2'b10 (SLVERR) with the normal read timing.

[REQ-ERR-003] A write to the status register shall change no register, shall have no effect on later reads of the status register other than through `i_status`, and shall answer OKAY. This holds for every value of `i_s_axi_wstrb`.

[REQ-ERR-004] A write with `i_s_axi_wstrb` = 4'b0000 shall answer exactly as a write with strobes to the same address (OKAY for a register or status, SLVERR for unmapped) and shall change no register.

[REQ-ERR-005] An address with bits [1:0] not equal to 2'b00 shall not be an error. It shall access the aligned word given by its word index.

[REQ-ERR-006] Any value of `i_s_axi_awprot` or `i_s_axi_arprot` shall be accepted without an error and without an effect.

[REQ-ERR-007] An unmapped access shall not stall or change the state of the other channels. The next transaction shall behave as if the unmapped access had targeted a mapped address.

[REQ-ERR-008] A valid input at 1 while `i_rst_n` is 0 shall have no effect (REQ-RST-005).

[REQ-ERR-009] Reset asserted in the middle of a transaction shall follow REQ-RST-004 and REQ-RST-009.

[REQ-ERR-010] If the manager breaks the handshake rules of section 12.1 (drops a valid or changes a payload before the transfer), the behaviour of the block is not specified and shall not be verified. The block need not detect it.

### 10.2 Parameter extremes

[REQ-EXT-001] With PARA_NUM_REGS = 1, only byte address 0x00 (REG_0) and 0x40 (STATUS) shall be mapped, `o_regs` shall be 32 bits wide, and 0x04 to 0x3C shall be unmapped.

[REQ-EXT-002] With PARA_NUM_REGS = 16, byte addresses 0x00 to 0x3C shall be REG_0 to REG_15, 0x40 shall be STATUS, `o_regs` shall be 512 bits wide, and no address below 0x44 shall be unmapped.

[REQ-EXT-003] With PARA_ADDR_W = 7, the address space shall be 0x00 to 0x7F and the addresses 0x44 to 0x7C shall be unmapped.

[REQ-EXT-004] With PARA_ADDR_W = 16, every address with a 1 in any bit from 15 to 7 (for example 0x0080, 0x0100, 0x8040, 0xFFFC) shall be unmapped.

[REQ-EXT-005] The latency, throughput, reset and back-pressure behaviour shall be the same for every legal parameter combination.

## 11 Configurations

| ID | Parameter values | Purpose |
|---|---|---|
| CFG-BASE | PARA_NUM_REGS=8, PARA_ADDR_W=8 | Main configuration (defaults); covers the gap of unmapped addresses 0x20 to 0x3C |
| CFG-MIN | PARA_NUM_REGS=1, PARA_ADDR_W=7 | Smallest legal: one register, narrowest address bus |
| CFG-MAX | PARA_NUM_REGS=16, PARA_ADDR_W=16 | Largest legal: full register bank, widest address bus, aliasing checks with high address bits |
| CFG-FULL-A7 | PARA_NUM_REGS=16, PARA_ADDR_W=7 | Full register bank with the narrowest address bus; no unmapped address below 0x44 |

The verification runs every configuration listed here (`run_set.json`).

## 12 Verification requirements

### 12.1 Environment obligations

[REQ-VER-001] On the AW, W and AR channels, the manager shall keep a valid at 1, and its payload stable, from the cycle it rises until the edge of its transfer.

[REQ-VER-002] The manager may keep `i_s_axi_bready` and `i_s_axi_rready` at 0 for any number of cycles, may drive them at 1 before the matching valid, and may make them depend on the valid.

[REQ-VER-003] The environment shall release `i_rst_n` (0 to 1) synchronously to `i_clk`, so that the release meets the recovery and removal times of the flip-flops. The testbench shall change `i_rst_n` only away from rising edges of `i_clk`.

[REQ-VER-004] The environment shall drive `i_status` synchronously to `i_clk`. The testbench shall change it only away from rising edges.

[REQ-VER-005] The testbench shall drive defined values (no X or Z) on all inputs while `i_rst_n` is 1. During reset the valids may be 0 or 1.

### 12.2 Observability
The values of the registers can be seen directly on `o_regs`, and also through reads. The held state of the AW, W and AR channels can be seen on `o_s_axi_awready`, `o_s_axi_wready` and `o_s_axi_arready`. A reference model shall predict, at every edge, `o_regs` and the next value of every handshake output.

[REQ-VER-010] The checker shall compare `o_regs` with the reference model in every cycle, not only after B transfers.

[REQ-VER-011] The checker shall compare `o_s_axi_rdata` and `o_s_axi_rresp` only in cycles where `o_s_axi_rvalid` is 1 or `i_rst_n` is 0, and `o_s_axi_bresp` only in cycles where `o_s_axi_bvalid` is 1 or `i_rst_n` is 0 (REQ-WR-027, REQ-RD-014, REQ-RST-002).

[REQ-VER-012] A protocol checker shall check that `o_s_axi_bvalid` and `o_s_axi_rvalid` stay 1, with their payload stable, until their transfer, and that no response code is 2'b01 or 2'b11.

### 12.3 Special setups

[REQ-VER-020] To check REQ-IF-001, the testbench shall change inputs between rising edges (for example at the falling edge), and shall check that no output changes before the next rising edge.

[REQ-VER-021] To check REQ-RST-004, the testbench shall assert `i_rst_n` between rising edges while transactions are in progress, and shall check the reset values before the next rising edge.

### 12.4 Required scenarios

[REQ-VER-030] Every value of `i_s_axi_wstrb` (all 16) shall be applied to a write of a mapped register, with data that differs from the old value in every byte.

[REQ-VER-031] Write transactions shall be run with the address before the data (gaps of 1 and of 4 or more cycles), with the data before the address (same gaps), and with both at the same edge.

[REQ-VER-032] The B channel shall be run with `i_s_axi_bready` delays of 0, 1 and 4 or more cycles, including `i_s_axi_bready` at 1 before `o_s_axi_bvalid` rises.

[REQ-VER-033] The R channel shall be run with `i_s_axi_rready` delays of 0, 1 and 4 or more cycles, including `i_s_axi_rready` at 1 before `o_s_axi_rvalid` rises.

[REQ-VER-034] New AW, W and AR valids shall be presented while a response is held back, to check that they are not taken (REQ-TIM-010, REQ-TIM-011).

[REQ-VER-035] Every mapped register shall be written with a unique value and read back, to detect decode aliasing.

[REQ-VER-036] The status register shall be read while `i_status` changes in the cycles around Ear and during R back-pressure, and shall be written with several strobe values.

[REQ-VER-037] Unmapped addresses shall be accessed: every word index from PARA_NUM_REGS to 15, 0x44, the highest address of the bus, and addresses that equal a mapped address plus a 1 in a bit from 7 to PARA_ADDR_W-1 (when PARA_ADDR_W > 7).

[REQ-VER-038] Addresses with bits [1:0] not 2'b00, and random values of `i_s_axi_awprot` and `i_s_axi_arprot`, shall be applied.

[REQ-VER-039] A read and a write of the same register shall run with Ear at Ec - 1, Ec and Ec + 1, and a read and a write of different registers shall run at the same time.

[REQ-VER-040] Reset shall be asserted with only the write address held, with only the write data held, with a B response pending, with an R response pending, and with valids held at 1 through the reset.

[REQ-VER-041] Back-to-back writes and back-to-back reads at the full throughput of REQ-TIM-001 and REQ-TIM-002 shall be run, alone and at the same time.

## 13 Implementation constraints

[REQ-IMP-001] The block shall meet timing at 50 MHz (20 ns clock period) in the GF180MCU technology at the worst-case corner of the sign-off flow.

[REQ-IMP-002] The RTL shall follow the coding rules in `docs/RTL_RULES.md` (REF-002).

[REQ-IMP-003] The RTL shall be synthesizable, shall use the single clock `i_clk` with no clock gating and no latches, and shall not rely on initial values.

[REQ-IMP-004] Every flip-flop that drives an output, or holds transaction state, shall be reset asynchronously by `i_rst_n` to the value that gives the reset values of section 5.

[REQ-IMP-005] Every output shall be driven directly from a flip-flop (this realises REQ-IF-001).

[REQ-IMP-006] The RTL shall compile and simulate in Verilator without lint warnings in all configurations of section 11.

No area budget is given. The block should use no more storage than the PARA_NUM_REGS x 32 register bits plus the flip-flops needed for the held write address and data, the read data, and the handshake state.

## 14 Decisions and open questions

| ID | Question | Decision | By | Date |
|---|---|---|---|---|
| D-001 | Value of `o_s_axi_awready`, `o_s_axi_wready` and `o_s_axi_arready` during reset (the description allows 0 or 1) | 0 during reset and in the cycle that ends at R1; 1 from R1 (REQ-RST-001, REQ-RST-006, REQ-RST-007) | spec-draft | 2026-11-19 |
| D-002 | Whether readies depend on the valids | No. The readies are registered and depend only on the held state (REQ-TIM-003, REQ-IF-001) | spec-draft | 2026-11-19 |
| D-003 | Write response latency ("at the earliest one cycle") | Exactly 1 cycle: bvalid is 1 from Ec (REQ-WR-020) | spec-draft | 2026-11-19 |
| D-004 | Read data latency ("at the earliest one cycle") | Exactly 1 cycle: rvalid is 1 from Ear (REQ-RD-004) | spec-draft | 2026-11-19 |
| D-005 | Edge at which the register is written | Ec, the later of the AW and W transfers (REQ-WR-010) | spec-draft | 2026-11-19 |
| D-006 | Old or new value when a read and a write of the same register overlap | The read samples at Ear. A write at the same edge gives the old value; a write at an earlier Ec gives the new value (REQ-CC-003, REQ-CC-004) | spec-draft | 2026-11-19 |
| D-007 | When `i_status` is sampled | At Ear, and held until Er (REQ-RD-009, REQ-RD-010) | spec-draft | 2026-11-19 |
| D-008 | Aliasing of address bits above bit 6 | Full decode of bits [PARA_ADDR_W-1:2]; any 1 above bit 6 is unmapped (REQ-DEC-004, REQ-DEC-005) | spec-draft | 2026-11-19 |
| D-009 | Values of bresp, rresp and rdata while their valid is 0 | Not specified outside reset and not checked; 0 during reset (REQ-WR-027, REQ-RD-014, REQ-RST-002) | spec-draft | 2026-11-19 |
| D-010 | When readies return to 1 after a response | In the cycle after the B or R transfer, with no combinational path from bready or rready (REQ-WR-001, REQ-RD-001) | spec-draft | 2026-11-19 |
| D-011 | Illegal parameter values | The RTL should stop elaboration with an error; not verified (REQ-PAR-003, REQ-PAR-004) | spec-draft | 2026-11-19 |
| D-012 | Configurations for PARA_ADDR_W extremes (the description names only PARA_NUM_REGS = 1 and 16) | Added PARA_ADDR_W = 7 and 16 in CFG-MIN, CFG-MAX and CFG-FULL-A7 | spec-draft | 2026-11-19 |
| D-013 | Width of `o_regs` as a table-readable expression | Local parameter LPARA_REGS_W = PARA_NUM_REGS*32 (section 4, REQ-PAR-002) | spec-draft | 2026-11-19 |
| Q-001 | Is a throughput of one write and one read every 2 cycles enough for the CPU? | Open: confirm with the designer | Designer | - |
| Q-002 | Is there an area budget for GF180MCU? | Open: none assumed | Designer | - |
| Q-003 | Should the readies be 0 during reset (D-001), or is a cheaper design with readies at 1 during reset wanted? | Open: 0 is assumed | Designer | - |

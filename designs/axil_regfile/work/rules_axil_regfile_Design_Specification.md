# Extracted rules - axil_regfile_Design_Specification.md

```
rules: 201  by strength {'MUST': 161, 'MAY': 6, 'MUST_NOT': 31, 'SHOULD': 3}  by check {'scenario': 71, 'assertion': 59, 'both': 48, 'none': 23}
normative sentences: 146  cited 145  skipped 1  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 15 (0 from cache)  cost US$0.4838  tokens in 65660 out 26082
```


## 1.1 Purpose

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-1.1-01 | MUST | slave | scenario | The block provides PARA_NUM_REGS 32-bit read/write control registers and one 32-bit read-only status register. | 1.1:s1 (p8) |
| RF-1.1-02 | MUST | slave | scenario | The registers are accessed through an AXI4-Lite subordinate port with a 32-bit data bus and a PARA_ADDR_W-bit address bus. | 1.1:s2, 1.2:s1 (p8) |
| RF-1.1-03 | MUST | slave | assertion | The current value of every read/write register drives o_regs directly. | 1.1:s3 (p8) |
| RF-1.1-04 | MUST | slave | scenario | A read of the status register at byte address 0x40 returns the SoC status word i_status. *(when: A read of byte address 0x40)* | 1.1:s4, 1.2:s5 (p8) |

## 1.2 Features

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-1.2-01 | MUST | slave | scenario | The block implements 1 to 16 read/write registers at byte addresses 0x00 + 4k. | 1.2:s2 (p12) |
| RF-1.2-02 | MUST | slave | both | Each read/write register resets to 0. *(when: On reset)* | 1.2:s3 (p12) |
| RF-1.2-03 | MUST | slave | scenario | Byte-lane writes are controlled by i_s_axi_wstrb. *(when: On a write to a read/write register)* | 1.2:s4 (p13) |
| RF-1.2-04 | MUST | slave | scenario | The status read returns i_status as sampled when the read address is taken. *(when: A status register read)* | 1.2:s6 (p14) |
| RF-1.2-05 | MUST | slave | both | An access to an unmapped address answers SLVERR. *(when: Access to an unmapped address)* | 1.2:s7 (p15) |
| RF-1.2-06 | MUST | slave | both | An unmapped read returns 0. *(when: Read of an unmapped address)* | 1.2:s8 (p15) |
| RF-1.2-07 | MAY | master | scenario | The write address and the write data may arrive in either order or at the same edge, and the block must accept all. | 1.2:s9 (p16) |
| RF-1.2-08 | MAY | master | scenario | A read and a write may be in progress at the same time, as the read and write paths work independently. | 1.2:s10 (p17) |
| RF-1.2-09 | MUST | slave | assertion | The write response comes one cycle after the last write handshake, and the read data one cycle after the read address handshake. | 1.2:s11 (p18) |
| RF-1.2-10 | MUST | slave | assertion | Every output is registered, with no combinational path from any input to any output. | 1.2:s12 (p19) |
| RF-1.2-11 | MUST | system | scenario | The block uses one clock and one active-low reset with asynchronous assertion. | 1.2:s13 (p20) |

## 1.3 Out of scope

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-1.3-01 | MUST_NOT | slave | assertion | The block never produces response codes EXOKAY (2'b01) or DECERR (2'b11). | 1.3:s2, 1.3:s3 (p24) |
| RF-1.3-02 | MUST | slave | scenario | i_s_axi_awprot and i_s_axi_arprot are ignored. | 1.3:s4 (p25) |
| RF-1.3-03 | MUST | slave | scenario | Address bits [1:0] are ignored and no unaligned-access error is produced. | 1.3:s6 (p26) |

## 3 Terms

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-3-01 | MUST | any | assertion | A transfer occurs at a rising edge of i_clk when valid and ready of a channel are both 1 and i_rst_n is 1; the payload is taken at that edge. *(when: A channel's valid and ready are both 1 at a rising edge of i_clk with i_rst_n 1)* | 3:s3 (p45) |
| RF-3-02 | MUST | system | assertion | A value required 'from edge n' holds starting in cycle n+1 until another requirement changes it, such as a held state ending or a reset. *(when: A requirement says a value holds 'from edge n')* | 3:s4 (p46) |
| RF-3-03 | MUST | system | assertion | A write address, write data or read address is held in cycle n if its transfer occurred at an edge <= n-1, its B or R transfer has not occurred, and i_rst_n has not been 0 since; reset ends the held state. *(when: Determining whether a write address, write data or read address is held)* | 3:s9, 3:s10, 3:s11 (p51) |

## 4 Parameters

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-4-01 | MUST | system | scenario | PARA_NUM_REGS sets the number of read/write registers, default 8, with legal values 1 to 16. | 4:s1 (p65) |
| RF-4-02 | MUST | system | scenario | PARA_ADDR_W sets the width in bits of i_s_axi_awaddr and i_s_axi_araddr, default 8, legal values 7 to 16. | 4:s2 (p66) |
| RF-4-03 | MUST | system | assertion | LPARA_REGS_W is derived as PARA_NUM_REGS*32 and is the width of o_regs in bits (32 for 1 register, 256 default, 512 for 16). | 4:s3, 4:s4 (p67) |
| RF-4-04 | MUST | system | scenario | The block must behave as the specification states for every legal combination of PARA_NUM_REGS (1 to 16) and PARA_ADDR_W (7 to 16). *(when: For every combination of PARA_NUM_REGS from 1 to 16 and PARA_ADDR_W from 7 to 16)* | 4:s5 (p71) |
| RF-4-05 | MUST | system | none | LPARA_REGS_W shall be a local parameter equal to PARA_NUM_REGS*32 that cannot be overridden from outside the module. | 4:s6 (p73) |
| RF-4-06 | SHOULD | system | none | The RTL should stop elaboration with an error message when PARA_NUM_REGS or PARA_ADDR_W is outside its legal range. *(when: PARA_NUM_REGS or PARA_ADDR_W is outside its legal range)* | 4:s7 (p75) |
| RF-4-07 | MUST_NOT | system | none | Behaviour with illegal parameter values is unspecified and must not be verified. *(when: Illegal parameter values)* | 4:s8 (p77) |

## 5 Interface

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-5-01 | MUST | slave | scenario | Byte lane i of a register must be bits 8i+7..8i and correspond to i_s_axi_wdata[8i+7:8i] and o_s_axi_rdata[8i+7:8i]. *(when: for byte lane i = 0 to 3)* | 5:s10, 5:s27 (p93) |
| RF-5-02 | MUST | slave | scenario | Byte lane i of a register must be enabled by i_s_axi_wstrb[i]. *(when: for byte lane i = 0 to 3)* | 5:s11, 5:s27 (p94) |
| RF-5-03 | MUST | slave | assertion | Bits 32k+31..32k of o_regs must carry the current value of read/write register k. *(when: for every k from 0 to PARA_NUM_REGS-1)* | 5:s23, 5:s26 (p106) |
| RF-5-04 | MUST | slave | assertion | Every output must change value only at a rising edge of i_clk or when i_rst_n is asserted. | 5:s25 (p109) |
| RF-5-05 | MUST_NOT | slave | assertion | No output may depend combinationally on any input in the same cycle. | 5:s25 (p109) |
| RF-5-06 | MUST | slave | scenario | The values of i_s_axi_awprot and i_s_axi_arprot must have no effect on any output. | 5:s28 (p115) |

## 6.1 Clocks

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-6.1-01 | MUST | system | none | Every flip-flop of the block shall be clocked by the rising edge of i_clk. | 6.1:s3, 6.1:s6 (p120) |

## 6.2 Resets

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-6.2-01 | MUST | slave | scenario | Every output shall take its reset value asynchronously, without waiting for a rising edge of i_clk. *(when: When i_rst_n goes from 1 to 0)* | 6.2:s2, 6.2:s7 (p125) |
| RF-6.2-02 | MUST | slave | assertion | o_s_axi_awready, o_s_axi_wready, o_s_axi_arready, o_s_axi_bvalid and o_s_axi_rvalid shall be 0. *(when: While i_rst_n is 0)* | 6.2:s4 (p127) |
| RF-6.2-03 | MUST | slave | assertion | o_s_axi_bresp, o_s_axi_rresp and o_s_axi_rdata shall be 0. *(when: While i_rst_n is 0)* | 6.2:s5 (p129) |
| RF-6.2-04 | MUST | slave | assertion | Every bit of o_regs shall be 0. *(when: While i_rst_n is 0)* | 6.2:s6 (p131) |
| RF-6.2-05 | MUST_NOT | slave | assertion | No transfer shall happen on any channel, whatever the values of the valid and ready inputs. *(when: At a clock edge where i_rst_n is 0)* | 6.2:s8 (p135) |
| RF-6.2-06 | MUST_NOT | slave | assertion | No transfer shall happen on any channel at R1, because the ready outputs and bvalid/rvalid are 0 in the cycle ending at R1. *(when: At edge R1, the first rising edge after reset release)* | 6.2:s9 (p137) |
| RF-6.2-07 | MUST | slave | assertion | o_s_axi_awready, o_s_axi_wready and o_s_axi_arready shall be 1. *(when: From edge R1, in the cycle starting at R1)* | 6.2:s10 (p139) |
| RF-6.2-08 | MUST | slave | assertion | o_s_axi_bvalid and o_s_axi_rvalid shall stay 0. *(when: After R1, until a write or read transaction makes them 1)* | 6.2:s11 (p141) |
| RF-6.2-09 | MUST | slave | scenario | The held state shall be discarded. *(when: When i_rst_n is asserted while a write address, write data, write response or read address is held or pending)* | 6.2:s12 (p143) |
| RF-6.2-10 | MUST_NOT | slave | scenario | No B or R response shall be given for that transaction, and no register shall be written by it. *(when: After release, for a transaction pending when reset was asserted)* | 6.2:s13 (p143) |
| RF-6.2-11 | MUST | slave | scenario | It shall be treated as a new transfer request, taken at the first edge after R1 where the matching ready is 1. *(when: A valid held at 1 through reset and after R1)* | 6.2:s14, 6.2:s15 (p145) |

## 7.1 Address decode

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-7.1-01 | MUST | slave | both | Bits [1:0] of i_s_axi_awaddr and i_s_axi_araddr must have no effect on any output. | 7.1:s1 (p151) |
| RF-7.1-02 | MUST | slave | both | An address with word index k selects read/write register k. *(when: Address word index k with 0 <= k < PARA_NUM_REGS)* | 7.1:s2 (p153) |
| RF-7.1-03 | MUST | slave | both | The address selects the status register. *(when: Address word index is 16 (byte address 0x40 to 0x43))* | 7.1:s3 (p155) |
| RF-7.1-04 | MUST | slave | both | Every other address is unmapped. *(when: Address is not a read/write register or status register address, including word indices PARA_NUM_REGS to 15, 17 to 31, or any 1 in bit 7 to PARA_ADDR_W-1)* | 7.1:s4, 7.1:s5 (p157) |
| RF-7.1-05 | MUST | slave | both | Decode compares all address bits [PARA_ADDR_W-1:2] so no register or status register appears at more than one word index (no aliasing). | 7.1:s6 (p159) |
| RF-7.1-06 | MUST | slave | scenario | A write transaction is decoded from the address taken at its AW transfer. *(when: Write transaction)* | 7.1:s7 (p161) |
| RF-7.1-07 | MUST | slave | scenario | A read transaction is decoded from the address taken at its AR transfer. *(when: Read transaction)* | 7.1:s8 (p163) |

## 7.2 Write address and write data acceptance

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-7.2-01 | MUST | slave | assertion | o_s_axi_awready shall be 1. *(when: Every cycle after R1 in which no write address is held)* | 7.2:s1 (p167) |
| RF-7.2-02 | MUST | slave | assertion | o_s_axi_awready shall be 0. *(when: A write address is held)* | 7.2:s2 (p169) |
| RF-7.2-03 | MUST | slave | assertion | o_s_axi_wready shall be 1. *(when: Every cycle after R1 in which no write data is held)* | 7.2:s3 (p171) |
| RF-7.2-04 | MUST | slave | assertion | o_s_axi_wready shall be 0. *(when: Write data is held)* | 7.2:s4 (p173) |
| RF-7.2-05 | MUST | slave | scenario | The block takes the AW and W transfers in either order or at the same edge. *(when: One write transaction)* | 7.2:s5 (p175) |
| RF-7.2-06 | MUST_NOT | slave | both | The block shall not answer a write transaction before it has taken both AW and W transfers. *(when: Before both AW and W transfers of the transaction are taken)* | 7.2:s5 (p175) |
| RF-7.2-07 | MUST_NOT | slave | assertion | The block shall take no other AW transfer. *(when: After an AW transfer, until the edge after Eb of that transaction)* | 7.2:s6 (p177) |
| RF-7.2-08 | MUST_NOT | slave | assertion | The block shall take no other W transfer. *(when: After a W transfer, until the edge after Eb of that transaction)* | 7.2:s7 (p179) |
| RF-7.2-09 | MUST | slave | scenario | The strobes and data used are the values of i_s_axi_wstrb and i_s_axi_wdata taken at the W transfer. *(when: Write transaction)* | 7.2:s8 (p181) |

## 7.3 Register update

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-7.3-01 | MUST | slave | both | Bits 8i+7..8i of register k take the value of the same bits of the write data taken at Ew. *(when: Write selects read/write register k, at edge Ec, for each lane i with i_s_axi_wstrb[i]=1)* | 7.3:s1 (p185) |
| RF-7.3-02 | MUST | slave | both | Byte lanes of register k whose strobe bit is 0 keep their value. *(when: Write selects read/write register k)* | 7.3:s2 (p187) |
| RF-7.3-03 | MUST | slave | assertion | The written value appears on o_regs[32k+31:32k] from edge Ec, in the cycle starting at Ec. *(when: Write to register k at edge Ec)* | 7.3:s3 (p189) |
| RF-7.3-04 | MUST_NOT | slave | assertion | A write shall change no bit of o_regs outside bits 32k+31..32k. *(when: Write transaction selecting register k)* | 7.3:s4 (p191) |
| RF-7.3-05 | MUST | slave | assertion | A write changes its register only at its edge Ec and only once. *(when: Write transaction)* | 7.3:s5 (p193) |
| RF-7.3-06 | MUST_NOT | slave | both | The write shall change no bit of o_regs. *(when: Write selects the status register)* | 7.3:s6 (p195) |
| RF-7.3-07 | MUST_NOT | slave | both | The write shall change no bit of o_regs. *(when: Write to an unmapped address)* | 7.3:s7 (p197) |
| RF-7.3-08 | MUST | slave | both | The write changes no bit of o_regs and answers OKAY. *(when: Write to read/write register k with i_s_axi_wstrb = 4'b0000)* | 7.3:s8 (p199) |
| RF-7.3-09 | MUST_NOT | slave | assertion | Bits of o_regs shall not change. *(when: Other than edge Ec of a write selecting them or i_rst_n asserted)* | 7.3:s9 (p201) |

## 7.4 Write response

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-7.4-01 | MUST | slave | assertion | o_s_axi_bvalid shall be 1 in the cycle starting at Ec. *(when: From edge Ec of a write transaction)* | 7.4:s1 (p205) |
| RF-7.4-02 | MUST | slave | assertion | o_s_axi_bvalid stays 1 and o_s_axi_bresp stays unchanged. *(when: Once o_s_axi_bvalid is 1, until and including the cycle ending at Eb)* | 7.4:s2 (p207) |
| RF-7.4-03 | MUST | slave | assertion | o_s_axi_bvalid shall be 0. *(when: From edge Eb, unless i_rst_n asserted earlier)* | 7.4:s3 (p209) |
| RF-7.4-04 | MUST | slave | both | The block gives exactly one B transfer per write transaction. *(when: Each write transaction that reaches Ec)* | 7.4:s4 (p211) |
| RF-7.4-05 | MUST | slave | assertion | o_s_axi_bvalid shall be 0. *(when: No write transaction is waiting for its B transfer)* | 7.4:s4 (p211) |
| RF-7.4-06 | MUST | slave | both | o_s_axi_bresp shall be 2'b00 (OKAY). *(when: Write selects a read/write register or the status register)* | 7.4:s5 (p213) |
| RF-7.4-07 | MUST | slave | both | o_s_axi_bresp shall be 2'b10 (SLVERR). *(when: Write to an unmapped address)* | 7.4:s6 (p215) |
| RF-7.4-08 | MUST_NOT | slave | assertion | o_s_axi_bresp shall never be 2'b01 or 2'b11. *(when: o_s_axi_bvalid is 1)* | 7.4:s7 (p217) |
| RF-7.4-09 | MUST_NOT | any | none | The value of o_s_axi_bresp is unspecified and shall not be checked. *(when: o_s_axi_bvalid is 0 and i_rst_n is 1)* | 7.4:s8 (p219) |

## 7.5 Read

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-7.5-01 | MUST | slave | assertion | o_s_axi_arready shall be 1. *(when: Every cycle after R1 in which no read address is held)* | 7.5:s1 (p223) |
| RF-7.5-02 | MUST | slave | assertion | o_s_axi_arready shall be 0. *(when: A read address is held)* | 7.5:s2 (p225) |
| RF-7.5-03 | MUST_NOT | slave | assertion | The block shall take no other AR transfer. *(when: After an AR transfer, until the edge after Er of that transaction)* | 7.5:s3 (p227) |
| RF-7.5-04 | MUST | slave | assertion | o_s_axi_rvalid shall be 1 in the cycle starting at Ear. *(when: From edge Ear of a read transaction)* | 7.5:s4 (p229) |
| RF-7.5-05 | MUST | slave | assertion | o_s_axi_rvalid stays 1 and o_s_axi_rdata and o_s_axi_rresp stay unchanged. *(when: Once o_s_axi_rvalid is 1, until and including the cycle ending at Er)* | 7.5:s5 (p231) |
| RF-7.5-06 | MUST | slave | assertion | o_s_axi_rvalid shall be 0. *(when: From edge Er, unless i_rst_n asserted earlier)* | 7.5:s6 (p233) |
| RF-7.5-07 | MUST | slave | both | The block gives exactly one R transfer for each AR transfer. *(when: Each AR transfer)* | 7.5:s7 (p235) |
| RF-7.5-08 | MUST | slave | assertion | o_s_axi_rvalid shall be 0. *(when: No read transaction is waiting for its R transfer)* | 7.5:s7 (p235) |
| RF-7.5-09 | MUST | slave | both | o_s_axi_rdata equals o_regs[32k+31:32k] in the cycle ending at Ear. *(when: Read selects read/write register k)* | 7.5:s8 (p237) |
| RF-7.5-10 | MUST | slave | both | o_s_axi_rdata equals i_status in the cycle ending at Ear. *(when: Read selects the status register)* | 7.5:s9 (p239) |
| RF-7.5-11 | MUST_NOT | slave | both | The change shall not alter o_s_axi_rdata. *(when: i_status changes after Ear during the read in progress)* | 7.5:s10 (p241) |
| RF-7.5-12 | MUST | slave | both | o_s_axi_rresp shall be 2'b00 (OKAY). *(when: Read selects a read/write register or the status register)* | 7.5:s11 (p243) |
| RF-7.5-13 | MUST | slave | both | o_s_axi_rdata shall be 32'h0000_0000 and o_s_axi_rresp shall be 2'b10 (SLVERR). *(when: Read to an unmapped address)* | 7.5:s12 (p245) |
| RF-7.5-14 | MUST_NOT | slave | assertion | o_s_axi_rresp shall never be 2'b01 or 2'b11. *(when: o_s_axi_rvalid is 1)* | 7.5:s13 (p247) |
| RF-7.5-15 | MUST_NOT | any | none | Values of o_s_axi_rdata and o_s_axi_rresp are unspecified and shall not be checked. *(when: o_s_axi_rvalid is 0 and i_rst_n is 1)* | 7.5:s14 (p249) |
| RF-7.5-16 | MUST_NOT | slave | assertion | A read shall change no bit of o_regs. *(when: Read transaction)* | 7.5:s15 (p251) |

## 7.6 Concurrent read and write

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-7.6-01 | MUST | slave | both | AR and R channels work independently of AW, W and B: value and timing of arready, rvalid, rdata, rresp are unchanged, except register value per REQ-CC-003 to 006. *(when: A write is held or waiting for its B transfer)* | 7.6:s1, 7.6:s2 (p255) |
| RF-7.6-02 | MUST | slave | both | The value and timing of awready, wready, bvalid, bresp and o_regs shall not change. *(when: A read is held or waiting for its R transfer)* | 7.6:s3 (p257) |
| RF-7.6-03 | MUST | slave | scenario | The read returns the old value of register k before that write. *(when: AR transfer of a read of register k at the same edge as Ec of a write to register k)* | 7.6:s4 (p259) |
| RF-7.6-04 | MUST | slave | scenario | The read returns the value written, unless another write to k with Ec before Ear came in between. *(when: Ec of a write to register k is before Ear of a read of register k)* | 7.6:s5 (p261) |
| RF-7.6-05 | MUST_NOT | slave | scenario | The write shall not change o_s_axi_rdata of the read. *(when: Ec of a write to register k is after Ear of a read of register k)* | 7.6:s6 (p263) |
| RF-7.6-06 | MUST | slave | both | Read data equals one whole value register k held in the cycle ending at Ear, never a mix of bytes of two values. *(when: Read of register k)* | 7.6:s7 (p265) |

## 8.1 Latency and throughput

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-8.1-01 | MUST | slave | both | The block completes one write transaction every 2 cycles: AW and W transfers at edge n, B transfer at edge n+1, next AW and W at edge n+2. *(when: manager drives i_s_axi_awvalid, i_s_axi_wvalid and i_s_axi_bready at 1 continuously)* | 8.1:s10 (p283) |
| RF-8.1-02 | MUST | slave | both | The block completes one read transaction every 2 cycles: AR transfer at edge n, R transfer at edge n+1, next AR at edge n+2. *(when: manager drives i_s_axi_arvalid and i_s_axi_rready at 1 continuously)* | 8.1:s11 (p285) |
| RF-8.1-03 | MUST_NOT | slave | both | The block's readies must not wait for the matching valid; o_s_axi_awready, o_s_axi_wready and o_s_axi_arready are 1 as REQ-WR-001, REQ-WR-003 and REQ-RD-001 say, regardless of the valids. | 8.1:s12 (p287) |

## 8.2 Back-pressure and ordering

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-8.2-01 | MUST | slave | assertion | The block keeps the write response pending for any number of cycles while i_s_axi_bready is 0. *(when: i_s_axi_bready is 0 and o_s_axi_bvalid is 1)* | 8.2:s1 (p291) |
| RF-8.2-02 | MUST_NOT | slave | assertion | The block takes no new AW or W transfer while the B response is pending and i_s_axi_bready is 0. *(when: i_s_axi_bready is 0 and o_s_axi_bvalid is 1)* | 8.2:s1 (p291) |
| RF-8.2-03 | MUST | slave | assertion | The block keeps the read data pending for any number of cycles while i_s_axi_rready is 0. *(when: i_s_axi_rready is 0 and o_s_axi_rvalid is 1)* | 8.2:s2 (p293) |
| RF-8.2-04 | MUST_NOT | slave | assertion | The block takes no new AR transfer while read data is pending and i_s_axi_rready is 0. *(when: i_s_axi_rready is 0 and o_s_axi_rvalid is 1)* | 8.2:s2 (p293) |
| RF-8.2-05 | MUST_NOT | slave | scenario | Back-pressure on the B channel must not stall the AR or R channel. *(when: back-pressure on the B channel)* | 8.2:s3 (p295) |
| RF-8.2-06 | MUST_NOT | slave | scenario | Back-pressure on the R channel must not stall the AW, W or B channel. *(when: back-pressure on the R channel)* | 8.2:s3 (p295) |
| RF-8.2-07 | MUST | slave | both | The block answers write transactions in the order of their Ec and read transactions in the order of their Ear. | 8.2:s4 (p297) |

## 8.3 Cycle-by-cycle examples

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-8.3-01 | MUST | slave | assertion | In the idle cycle after the B transfer, o_s_axi_awready and o_s_axi_wready are 1 so a new write can be taken. *(when: idle after the B transfer, with o_s_axi_bvalid 0)* | 8.3:s10 (p310) |

## 9 Registers

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-9-01 | MUST | slave | both | REG_k VALUE (bits 31:0, RW) shall reset to 0x0000_0000, so o_regs[32k+31:32k] is 0 after reset. *(when: Register REG_k at offset 0x00+4k, k=0..PARA_NUM_REGS-1, is reset)* | 9:s1 (p341) |
| RF-9-02 | MUST | slave | assertion | o_regs[32k+31:32k] shall be driven by the current value of REG_k. *(when: For each k from 0 to PARA_NUM_REGS-1)* | 9:s1 (p341) |
| RF-9-03 | MUST | slave | both | Each byte lane of REG_k shall be written only when the corresponding i_s_axi_wstrb bit is set; other byte lanes shall keep their value. *(when: A write to REG_k)* | 9:s1, 9:s5 (p341) |
| RF-9-04 | MUST | slave | both | A read of REG_k shall return the current register value with OKAY response. *(when: A read of REG_k)* | 9:s1, 9:s5 (p341) |
| RF-9-05 | MUST | slave | both | A read of STATUS shall return i_status sampled at Ear, with OKAY response. *(when: A read of STATUS at offset 0x40)* | 9:s2 (p342) |
| RF-9-06 | MUST | slave | both | A write to STATUS shall change nothing and answer OKAY. *(when: A write to STATUS at offset 0x40)* | 9:s2, 9:s6 (p342) |
| RF-9-07 | MUST | slave | both | A read of the unmapped region below STATUS shall return 0 with SLVERR. *(when: A read from an address from 4*PARA_NUM_REGS to 0x3C (unmapped))* | 9:s3 (p343) |
| RF-9-08 | MUST | slave | both | A write to the unmapped region below STATUS shall change nothing and answer SLVERR. *(when: A write to an address from 4*PARA_NUM_REGS to 0x3C (unmapped))* | 9:s3 (p343) |
| RF-9-09 | MUST | system | scenario | The reserved region from 4*PARA_NUM_REGS to 0x3C shall not exist when PARA_NUM_REGS is 16. *(when: PARA_NUM_REGS = 16)* | 9:s3 (p343) |
| RF-9-10 | MUST | slave | both | A read of the unmapped region above STATUS shall return 0 with SLVERR. *(when: A read from an address from 0x44 to 2^PARA_ADDR_W - 4)* | 9:s4 (p344) |
| RF-9-11 | MUST | slave | both | A write to the unmapped region above STATUS shall change nothing and answer SLVERR. *(when: A write to an address from 0x44 to 2^PARA_ADDR_W - 4)* | 9:s4 (p344) |
| RF-9-12 | MUST | slave | both | Address bits [1:0] shall be ignored when decoding register offsets. *(when: Address decoding)* | 9:s7 (p346) |
| RF-9-13 | MUST | system | scenario | The register map shall match the table exactly for every legal PARA_NUM_REGS and PARA_ADDR_W combination. *(when: For every legal parameter combination)* | 9:s8, 9:s9 (p346) |

## 10.1 Error conditions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-10.1-01 | MUST | slave | both | A write to an unmapped address, detected by decoding the address taken at Ea, must change no register and answer o_s_axi_bresp = 2'b10 (SLVERR) with normal write timing. *(when: write to an unmapped address)* | 10.1:s1 (p354) |
| RF-10.1-02 | MUST | slave | both | A read from an unmapped address, detected by decoding the address taken at Ear, must return o_s_axi_rdata = 0 and o_s_axi_rresp = 2'b10 (SLVERR) with normal read timing. *(when: read from an unmapped address)* | 10.1:s2 (p356) |
| RF-10.1-03 | MUST | slave | scenario | A write to the status register must change no register, not affect later status reads other than through i_status, and answer OKAY, for every i_s_axi_wstrb value. *(when: write to the status register, any value of i_s_axi_wstrb)* | 10.1:s3, 10.1:s4 (p358) |
| RF-10.1-04 | MUST | slave | scenario | A write with i_s_axi_wstrb = 4'b0000 must answer as a write with strobes to the same address (OKAY for register or status, SLVERR for unmapped) and change no register. *(when: write with i_s_axi_wstrb = 4'b0000)* | 10.1:s5 (p360) |
| RF-10.1-05 | MUST_NOT | slave | scenario | An address with bits [1:0] not equal to 2'b00 must not be treated as an error. *(when: address bits [1:0] not equal to 2'b00)* | 10.1:s6 (p362) |
| RF-10.1-06 | MUST | slave | scenario | An access with unaligned address bits [1:0] must access the aligned word given by its word index. *(when: address bits [1:0] not equal to 2'b00)* | 10.1:s7 (p362) |
| RF-10.1-07 | MUST | slave | scenario | Any value of i_s_axi_awprot or i_s_axi_arprot must be accepted without error and without effect. *(when: any value of awprot or arprot)* | 10.1:s8 (p364) |
| RF-10.1-08 | MUST_NOT | slave | scenario | An unmapped access must not stall or change the state of the other channels. *(when: unmapped access)* | 10.1:s9 (p366) |
| RF-10.1-09 | MUST | slave | scenario | The next transaction must behave as if the unmapped access had targeted a mapped address. *(when: transaction following an unmapped access)* | 10.1:s10 (p366) |
| RF-10.1-10 | MUST | slave | both | A valid input at 1 while i_rst_n is 0 must have no effect (REQ-RST-005). *(when: a valid input is 1 while i_rst_n is 0)* | 10.1:s11 (p368) |
| RF-10.1-11 | MUST | slave | scenario | Reset asserted mid-transaction must follow REQ-RST-004 and REQ-RST-009. *(when: reset asserted in the middle of a transaction)* | 10.1:s12 (p370) |
| RF-10.1-12 | MUST_NOT | system | none | Block behaviour under manager handshake violations is unspecified and must not be verified; the block need not detect it. *(when: manager breaks handshake rules of section 12.1 (drops a valid or changes a payload before the transfer))* | 10.1:s13, 10.1:s14 (p372) |

## 10.2 Parameter extremes

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-10.2-01 | MUST | slave | scenario | Only 0x00 (REG_0) and 0x40 (STATUS) are mapped, o_regs is 32 bits wide, and 0x04 to 0x3C are unmapped. *(when: PARA_NUM_REGS = 1)* | 10.2:s1 (p376) |
| RF-10.2-02 | MUST | slave | scenario | 0x00 to 0x3C are REG_0 to REG_15, 0x40 is STATUS, o_regs is 512 bits wide, and no address below 0x44 is unmapped. *(when: PARA_NUM_REGS = 16)* | 10.2:s2 (p378) |
| RF-10.2-03 | MUST | slave | scenario | The address space is 0x00 to 0x7F and addresses 0x44 to 0x7C are unmapped. *(when: PARA_ADDR_W = 7)* | 10.2:s3 (p380) |
| RF-10.2-04 | MUST | slave | scenario | Every address with a 1 in any bit from 15 to 7 (e.g. 0x0080, 0x0100, 0x8040, 0xFFFC) is unmapped. *(when: PARA_ADDR_W = 16)* | 10.2:s4 (p382) |
| RF-10.2-05 | MUST | slave | scenario | Latency, throughput, reset and back-pressure behaviour must be the same for every legal parameter combination. *(when: any legal parameter combination)* | 10.2:s5 (p384) |

## 11 Configurations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-11-01 | MUST | system | scenario | CFG-BASE uses PARA_NUM_REGS=8 and PARA_ADDR_W=8 as default and must cover the gap of unmapped addresses 0x20 to 0x3C. *(when: Configuration CFG-BASE)* | 11:s1 (p390) |
| RF-11-02 | MUST | system | scenario | CFG-MIN must be verified with PARA_NUM_REGS=1 and PARA_ADDR_W=7, the smallest legal configuration. *(when: Configuration CFG-MIN)* | 11:s2 (p391) |
| RF-11-03 | MUST | system | scenario | CFG-MAX must be verified with PARA_NUM_REGS=16 and PARA_ADDR_W=16, including aliasing checks with high address bits. *(when: Configuration CFG-MAX)* | 11:s3 (p392) |
| RF-11-04 | MUST | system | scenario | CFG-FULL-A7 uses PARA_NUM_REGS=16 and PARA_ADDR_W=7, a full register bank with the narrowest address bus and no unmapped address below 0x44. *(when: Configuration CFG-FULL-A7)* | 11:s4 (p393) |
| RF-11-05 | MUST | system | scenario | The verification must run every configuration listed in the Configurations table (CFG-BASE, CFG-MIN, CFG-MAX, CFG-FULL-A7), as defined in run_set.json. | 11:s5 (p395) |

## 12.1 Environment obligations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-12.1-01 | MUST | master | assertion | The manager shall keep valid at 1 and its payload stable from the cycle it rises until the edge of its transfer. *(when: On AW, W and AR channels, once valid rises)* | 12.1:s1 (p401) |
| RF-12.1-02 | MAY | master | scenario | The manager may hold i_s_axi_bready and i_s_axi_rready at 0 for any number of cycles, drive them at 1 before the matching valid, and make them depend on the valid. | 12.1:s2 (p403) |
| RF-12.1-03 | MUST | system | none | The environment shall release i_rst_n synchronously to i_clk so that the release meets recovery and removal times of the flip-flops. *(when: When releasing reset (0 to 1))* | 12.1:s3 (p405) |
| RF-12.1-04 | MUST | system | none | The testbench shall change i_rst_n only away from rising edges of i_clk. | 12.1:s4 (p405) |
| RF-12.1-05 | MUST | system | none | The environment shall drive i_status synchronously to i_clk, changing it only away from rising edges. | 12.1:s5, 12.1:s6 (p407) |
| RF-12.1-06 | MUST | system | assertion | The testbench shall drive defined values (no X or Z) on all inputs. *(when: While i_rst_n is 1)* | 12.1:s7 (p409) |
| RF-12.1-07 | MAY | master | scenario | The valids may be 0 or 1 during reset. *(when: During reset)* | 12.1:s8 (p409) |
| RF-12.1-08 | MUST | system | none | The environment shall drive i_rst_n = 0 from time zero, before the first rising edge of i_clk, for at least 2 cycles. *(when: From start of operation (time zero))* | 12.1:s9 (p411) |
| RF-12.1-09 | MUST_NOT | system | none | No output check applies, including REQ-VER-010, before the first assertion of i_rst_n, as outputs are undefined. *(when: Before the first assertion of i_rst_n)* | 12.1:s10 (p411) |
| RF-12.1-10 | MAY | master | scenario | A reset assertion ends the REQ-VER-001 obligation; the manager may drop that valid or change its payload. *(when: During reset and after R1, for a valid that rose before the reset assertion)* | 12.1:s11 (p413) |
| RF-12.1-11 | MUST | master | assertion | A valid at 1 after R1 is a new request and carries the REQ-VER-001 obligation from that cycle. *(when: A valid at 1 after R1)* | 12.1:s12 (p413) |

## 12.2 Observability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-12.2-01 | MAY | system | none | Register values are observable on o_regs and through reads; held AW, W and AR state is observable on o_s_axi_awready, o_s_axi_wready and o_s_axi_arready. | 12.2:s1, 12.2:s2 (p416) |
| RF-12.2-02 | MUST | system | none | A reference model shall predict o_regs and the next value of every handshake output. *(when: At every edge)* | 12.2:s3 (p416) |
| RF-12.2-03 | MUST | system | assertion | The checker shall compare o_regs with the reference model in every cycle, not only after B transfers. *(when: Every cycle)* | 12.2:s4 (p418) |
| RF-12.2-04 | MUST | system | assertion | The checker shall compare o_s_axi_rdata and o_s_axi_rresp only when o_s_axi_rvalid is 1 or i_rst_n is 0, and o_s_axi_bresp only when o_s_axi_bvalid is 1 or i_rst_n is 0. | 12.2:s5 (p420) |
| RF-12.2-05 | MUST | slave | assertion | A protocol checker shall verify o_s_axi_bvalid and o_s_axi_rvalid stay 1 with stable payload until transfer, and no response code is 2'b01 or 2'b11. *(when: Until the transfer)* | 12.2:s6 (p422) |

## 12.3 Special setups

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-12.3-01 | MUST | system | scenario | The testbench shall change inputs between rising edges, e.g. at the falling edge, and check no output changes before the next rising edge. *(when: To check REQ-IF-001)* | 12.3:s1 (p426) |
| RF-12.3-02 | MUST | system | scenario | The testbench shall assert i_rst_n between rising edges while transactions are in progress and check reset values before the next rising edge. *(when: To check REQ-RST-004, transactions in progress)* | 12.3:s2 (p428) |

## 12.4 Required scenarios

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-12.4-01 | MUST | system | scenario | All 16 values of i_s_axi_wstrb shall be applied, with data differing from the old value in every byte. *(when: Write to a mapped register)* | 12.4:s1 (p432) |
| RF-12.4-02 | MUST | system | scenario | Writes shall be run with address before data (gaps of 1 and 4+ cycles), data before address (same gaps), and both at the same edge. | 12.4:s2 (p434) |
| RF-12.4-03 | MUST | system | scenario | The B channel shall be run with i_s_axi_bready delays of 0, 1 and 4 or more cycles, including i_s_axi_bready at 1 before o_s_axi_bvalid rises. | 12.4:s3 (p436) |
| RF-12.4-04 | MUST | system | scenario | The R channel shall be run with i_s_axi_rready delays of 0, 1 and 4 or more cycles, including i_s_axi_rready at 1 before o_s_axi_rvalid rises. | 12.4:s4 (p438) |
| RF-12.4-05 | MUST | system | scenario | New AW, W and AR valids shall be presented to check they are not taken (REQ-TIM-010, REQ-TIM-011). *(when: While a response is held back)* | 12.4:s5 (p440) |
| RF-12.4-06 | MUST | system | scenario | Every mapped register shall be written with a unique value and read back to detect decode aliasing. | 12.4:s6 (p442) |
| RF-12.4-07 | MUST | system | scenario | The status register shall be read while i_status changes around Ear and during R back-pressure, and written with several strobe values. | 12.4:s7 (p444) |
| RF-12.4-08 | MUST | system | scenario | Unmapped addresses shall be accessed: word indexes PARA_NUM_REGS to 15, 0x44, the highest bus address, and mapped address plus a 1 in bit 7 to PARA_ADDR_W-1 when PARA_ADDR_W > 7. | 12.4:s8 (p446) |
| RF-12.4-09 | MUST | system | scenario | Addresses with bits [1:0] not 2'b00 and random i_s_axi_awprot and i_s_axi_arprot values shall be applied. | 12.4:s9 (p448) |
| RF-12.4-10 | MUST | system | scenario | A read and a write of the same register shall run with Ear at Ec-1, Ec and Ec+1, and reads and writes of different registers shall run simultaneously. | 12.4:s10 (p450) |
| RF-12.4-11 | MUST | system | scenario | Reset shall be asserted with only write address held, only write data held, B response pending, R response pending, and with valids held at 1 through reset. | 12.4:s11 (p452) |
| RF-12.4-12 | MUST | system | scenario | Back-to-back writes and reads at full throughput of REQ-TIM-001 and REQ-TIM-002 shall be run, alone and at the same time. | 12.4:s12 (p454) |

## 13 Implementation constraints

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-13-01 | MUST | system | none | The block shall meet timing at 50 MHz (20 ns clock period) in the GF180MCU technology at the worst-case corner of the sign-off flow. *(when: at worst-case corner of the sign-off flow in GF180MCU)* | 13:s1 (p458) |
| RF-13-02 | MUST | system | none | The RTL shall follow the coding rules in docs/RTL_RULES.md (REF-002). | 13:s2 (p460) |
| RF-13-03 | MUST | system | none | The RTL shall be synthesizable. | 13:s3 (p462) |
| RF-13-04 | MUST | system | none | The RTL shall use the single clock i_clk with no clock gating and no latches. | 13:s3 (p462) |
| RF-13-05 | MUST_NOT | system | none | The RTL shall not rely on initial values. | 13:s3 (p462) |
| RF-13-06 | MUST | system | both | Every flip-flop that drives an output or holds transaction state shall be reset asynchronously by i_rst_n to the value giving the reset values of section 5. *(when: for every flip-flop that drives an output or holds transaction state)* | 13:s4 (p464) |
| RF-13-07 | MUST | system | none | Every output shall be driven directly from a flip-flop. | 13:s5 (p466) |
| RF-13-08 | MUST | system | none | The RTL shall compile and simulate in Verilator without lint warnings in all configurations of section 11. *(when: in all configurations of section 11)* | 13:s6 (p468) |
| RF-13-09 | SHOULD | system | none | The block should use no more storage than PARA_NUM_REGS x 32 register bits plus flip-flops for held write address and data, read data, and handshake state. | 13:s8 (p470) |

## 14 Decisions and open questions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| RF-14-01 | MUST | slave | assertion | o_s_axi_awready, o_s_axi_wready and o_s_axi_arready must be 0 during reset and in the cycle that ends at R1, and 1 from R1. *(when: during reset and in the cycle that ends at R1)* | 14:s1, 14:s21 (p476) |
| RF-14-02 | MUST | slave | both | The readies must be registered and depend only on the held state, not on the valids. | 14:s2 (p477) |
| RF-14-03 | MUST | slave | assertion | bvalid must be 1 from Ec, giving a write response latency of exactly 1 cycle. *(when: write response after the later of the AW and W transfers (Ec))* | 14:s3 (p478) |
| RF-14-04 | MUST | slave | assertion | rvalid must be 1 from Ear, giving a read data latency of exactly 1 cycle. *(when: read response after the address transfer (Ear))* | 14:s4 (p479) |
| RF-14-05 | MUST | slave | both | The register must be written at Ec, the later of the AW and W transfers. *(when: write request)* | 14:s5 (p480) |
| RF-14-06 | MUST | slave | scenario | The read must sample the register at Ear: a write at the same edge gives the old value, a write at an earlier Ec gives the new value. *(when: a read and a write of the same register overlap)* | 14:s6 (p481) |
| RF-14-07 | MUST | slave | both | i_status must be sampled at Ear and the sampled value held until Er. *(when: read of a status register)* | 14:s7 (p482) |
| RF-14-08 | MUST | slave | scenario | Address bits [PARA_ADDR_W-1:2] must be fully decoded; any 1 above bit 6 makes the address unmapped. *(when: address decoding)* | 14:s8 (p483) |
| RF-14-09 | MUST | slave | assertion | bresp, rresp and rdata must be 0 during reset; their values while valid is 0 outside reset are not specified or checked. *(when: during reset)* | 14:s9 (p484) |
| RF-14-10 | MUST | slave | assertion | The readies must return to 1 in the cycle after the B or R transfer, with no combinational path from bready or rready. *(when: after a B or R transfer)* | 14:s10 (p485) |
| RF-14-11 | SHOULD | system | none | The RTL should stop elaboration with an error on illegal parameter values. *(when: illegal parameter values)* | 14:s11 (p486) |
| RF-14-12 | MUST | slave | both | A reset must end every held state; "after R1" means the most recent R1. *(when: reset asserted)* | 14:s14 (p489) |
| RF-14-13 | MUST | master | scenario | Reset must be applied from time zero for at least 2 cycles; outputs are undefined and unchecked before the first reset. *(when: from time zero)* | 14:s15 (p490) |
| RF-14-14 | MUST | slave | scenario | Reset ends the obligation on a pending request; a valid after R1 must be treated as a new request. *(when: request in progress across a reset)* | 14:s18 (p493) |

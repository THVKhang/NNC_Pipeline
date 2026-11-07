# Extracted rules - m_apb_tlul_bridge_Design_Specification.md

```
rules: 245  by strength {'MUST': 226, 'MUST_NOT': 17, 'SHOULD': 1, 'MAY': 1}  by check {'none': 53, 'scenario': 50, 'both': 60, 'assertion': 82}
normative sentences: 140  cited 131  skipped 9  uncovered 0 (after first pass: 1)
invalid sentence IDs returned by the agent: 0
calls: 25 (0 from cache)  cost US$0.7449  tokens in 120003 out 33908
```


## T1 APB4 to TL-UL Bridge Design Specification

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-T1-01 | MUST | system | none | Every mandatory requirement has a stable REQ-- identifier and a verification method. | T1:s3 (p17) |
| BR-T1-02 | MUST | slave | scenario | The bridge accepts only full-strobe writes (PSTRB = 4'b1111) and word-aligned addresses (PADDR[1:0] = 2'b00). | T1:s5 (p19) |
| BR-T1-03 | MUST | slave | both | A write with PSTRB other than 4'b1111 must complete with PSLVERR = 1. *(when: A write has a PSTRB value other than 4'b1111)* | T1:s6 (p19) |
| BR-T1-04 | MUST | slave | both | Any access with a misaligned address must complete with PSLVERR = 1. *(when: An access has a misaligned address)* | T1:s6 (p19) |
| BR-T1-05 | MUST_NOT | slave | both | No TL-UL request is issued for a write with unsupported PSTRB or for a misaligned access. *(when: A write has PSTRB other than 4'b1111, or any access has a misaligned address)* | T1:s6 (p19) |
| BR-T1-06 | MUST | master | none | Software needing byte or half-word writes must use a different bridge. *(when: Software needs byte or half-word writes)* | T1:s7 (p19) |

## 1.1 Purpose and scope

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-1.1-01 | MUST | system | scenario | Each APB transfer must become exactly one TL-UL request, and the TL-UL response must become the APB completion. *(when: For each APB transfer)* | 1.1:s3 (p50) |
| BR-1.1-02 | MUST | slave | scenario | The TL-UL request must be launched from flip-flops in the first APB access cycle (early launch). *(when: First APB access cycle)* | 1.1:s4, 1.3:s3 (p52) |
| BR-1.1-03 | MUST | slave | none | Every output that changes toward either bus must come directly from a flip-flop. | 1.1:s4 (p52) |
| BR-1.1-04 | MUST_NOT | slave | scenario | The bridge does not support partial writes (PSTRB other than 4'b1111), byte or half-word accesses, TL-UL bursts, or multiple outstanding requests. | 1.1:s6 (p56) |

## 1.3 Feature summary

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-1.3-01 | MUST | slave | both | An APB4 full-strobe write must be converted to a TL-UL PutFullData request. *(when: APB write with full strobe)* | 1.3:s1 (p72) |
| BR-1.3-02 | MUST | slave | both | An APB4 read must be converted to a TL-UL Get request. *(when: APB read)* | 1.3:s2 (p73) |
| BR-1.3-03 | MUST | slave | scenario | The bridge must give a local error response for an unsupported strobe or misaligned address. *(when: Unsupported strobe or misaligned address)* | 1.3:s4 (p75) |
| BR-1.3-04 | MUST | slave | scenario | The bridge must check the TL-UL response and map errors to PSLVERR. *(when: TL-UL response received)* | 1.3:s5 (p76) |
| BR-1.3-05 | MUST | slave | scenario | The bridge must support back-to-back APB transfers with PSEL held high. *(when: PSEL held high)* | 1.3:s6 (p77) |

## 2.1 Normative references

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-2.1-01 | MUST | system | none | The RTL design must follow the VLSIT RTL Design Rules v2 (REF-003) as the mandatory coding, hierarchy, reset, CDC and naming baseline. | 2.1:s3 (p87) |

## 2.2 Source-of-truth and conflict handling

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-2.2-01 | MUST | system | none | This specification must stay consistent with REF-001, REF-002 and REF-003. | 2.2:s3 (p96) |
| BR-2.2-02 | MUST | system | none | REF-003 is the mandatory RTL coding baseline and the RTL must comply with it. | 2.2:s4 (p97) |

## 2.3 Compliance declaration

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-2.3-01 | MUST | slave | both | The bridge must reject a write with PSTRB other than 4'b1111 by responding with PSLVERR. *(when: A write transfer with PSTRB other than 4'b1111)* | 2.3:s1 (p106) |
| BR-2.3-02 | MUST | slave | both | The bridge must reject a transfer with misaligned PADDR by responding with PSLVERR. *(when: PADDR is misaligned)* | 2.3:s1 (p106) |
| BR-2.3-03 | MUST | slave | scenario | PPROT must be accepted and ignored; it must not affect bridge behavior. | 2.3:s1 (p106) |
| BR-2.3-04 | MUST | master | assertion | The TL-UL host side must use a_size = 2 only, with 32-bit data and no bursts. | 2.3:s2 (p107) |
| BR-2.3-05 | MUST | master | assertion | a_user must be driven to zero, with no integrity. | 2.3:s2 (p107) |

## 3 Requirements and traceability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-3-01 | MUST | slave | both | The bridge shall capture the request at the rising edge ending the Setup cycle. *(when: APB side idle, i_apb_psel = 1 and i_apb_penable = 0 (Setup phase))* | 3:s1 (p113) |
| BR-3-02 | MUST | slave | both | The bridge shall present the request on TL-UL channel A from flip-flops in the next cycle (first Access cycle). *(when: Captured request is legal)* | 3:s1 (p113) |
| BR-3-03 | MUST | slave | both | The bridge shall convert it into one PutFullData (a_opcode = 3'b000) with a_size = 2, a_mask = 4'b1111, a_address = PADDR and a_data = PWDATA. *(when: APB write with PSTRB = 4'b1111 and PADDR[1:0] = 2'b00)* | 3:s2 (p114) |
| BR-3-04 | MUST | slave | both | The bridge shall convert it into one TL-UL Get (a_opcode = 3'b100) with a_size = 2, a_mask = 4'b1111 and a_address = PADDR. *(when: APB read with PADDR[1:0] = 2'b00)* | 3:s3 (p115) |
| BR-3-05 | MUST | slave | scenario | PSTRB shall be ignored on reads. *(when: APB read)* | 3:s3 (p115) |
| BR-3-06 | MUST | slave | assertion | The bridge shall have at most one TL-UL request outstanding. | 3:s4 (p116) |
| BR-3-07 | MUST | slave | assertion | The bridge shall start no new TL-UL request before the APB completion of the previous transfer. | 3:s4 (p116) |
| BR-3-08 | MUST | slave | assertion | The bridge shall keep o_tlul_a_valid high and channel A stable. *(when: From the cycle after capture until i_tlul_a_ready is sampled high)* | 3:s5 (p117) |
| BR-3-09 | MUST | slave | both | The bridge shall return the TL-UL d_data on o_apb_prdata. *(when: Read completes without error)* | 3:s6 (p118) |
| BR-3-10 | MUST | slave | both | The bridge shall drive o_apb_prdata to 0. *(when: Write completion or any error completion)* | 3:s6 (p118) |
| BR-3-11 | MUST | slave | both | The bridge shall discard the response without any effect on the APB side. *(when: TL-UL response arrives when no request has been accepted (orphan))* | 3:s7 (p119) |
| BR-3-12 | MUST | slave | both | The bridge shall detect the Setup phase from levels i_apb_psel = 1 and i_apb_penable = 0, not from an edge of i_apb_psel. | 3:s8 (p120) |
| BR-3-13 | MUST | slave | both | The bridge shall accept the new transfer. *(when: New Setup phase in the cycle immediately after the PREADY cycle, whether psel stays 1 or returns to 0 for one or more cycles)* | 3:s8 (p120) |
| BR-3-14 | MUST | slave | scenario | Every combination of read, write and error transfers shall be supported back to back. *(when: Back-to-back transfers)* | 3:s8 (p120) |
| BR-3-15 | MUST | slave | scenario | The bridge shall expose exactly the APB4 Completer signals listed in section 6.2 and no other APB signal. | 3:s9 (p121) |
| BR-3-16 | MUST | slave | scenario | The bridge shall expose exactly the TL-UL host signals listed in section 6.2 and no others. | 3:s10 (p122) |
| BR-3-17 | MUST | slave | scenario | Such output ports shall be driven directly by a flip-flop Q pin with no combinational logic; never-changing outputs are constant tie-offs. *(when: Output port changes value during operation)* | 3:s11 (p123) |
| BR-3-18 | MUST | slave | assertion | The bridge shall assert o_apb_pready for exactly one cycle per transfer, and only in an Access cycle (psel = 1, penable = 1). | 3:s12 (p124) |
| BR-3-19 | MUST | slave | assertion | o_apb_pslverr shall be 1 only while o_apb_pready is 1. | 3:s12 (p124) |
| BR-3-20 | MUST | master | assertion | The bridge shall drive a_param = 3'b000, a_size = 2'b10, a_mask = 4'b1111, a_source = PARA_SRC_ID and a_user = '0. *(when: Every request)* | 3:s13 (p125) |
| BR-3-21 | MUST | master | both | The bridge shall drive o_tlul_d_ready low. *(when: In reset)* | 3:s14 (p126) |
| BR-3-22 | MUST | master | both | The bridge shall drive o_tlul_d_ready high and keep it high. *(when: From first clock edge after reset release)* | 3:s14 (p126) |
| BR-3-23 | MUST | system | none | APB-facing and TL-UL-facing logic shall be in two separate modules connected only through the internal interface of section 5.1. | 3:s15 (p127) |
| BR-3-24 | MUST | slave | both | The bridge shall issue no TL-UL request and complete with PREADY = 1 and PSLVERR = 1 in the first Access cycle. *(when: Write has PSTRB other than 4'b1111)* | 3:s16 (p128) |
| BR-3-25 | MUST | slave | both | The bridge shall issue no TL-UL request and complete with PREADY = 1 and PSLVERR = 1 in the first Access cycle. *(when: PADDR[1:0] is not 2'b00 (read or write))* | 3:s17 (p129) |
| BR-3-26 | MUST | slave | both | The bridge shall complete the APB transfer with PSLVERR = 1. *(when: TL-UL response has d_error = 1)* | 3:s18 (p130) |
| BR-3-27 | MUST | slave | both | The bridge shall complete the APB transfer with PSLVERR = 1. *(when: Response d_opcode is not AccessAckData (3'b001) for a read or not AccessAck (3'b000) for a write)* | 3:s19 (p131) |
| BR-3-28 | MUST | slave | both | The bridge shall complete the APB transfer with PSLVERR = 1. *(when: Response d_source differs from PARA_SRC_ID)* | 3:s20 (p132) |
| BR-3-29 | MUST | system | none | The bridge shall operate in one clock domain, i_clk_core, for both interfaces with no clock-domain crossing. | 3:s21 (p133) |
| BR-3-30 | MUST | slave | scenario | The bridge shall use active-low reset i_rst_n_core with asynchronous assertion. | 3:s22 (p134) |
| BR-3-31 | MUST | slave | both | The bridge shall drive the listed outputs to 0 while reset is asserted. *(when: Reset asserted)* | 3:s22 (p134) |
| BR-3-32 | MUST | slave | both | The bridge shall abandon the transfer and send no APB completion for it after reset release. *(when: Reset asserted during a transfer)* | 3:s23 (p135) |
| BR-3-33 | MUST | system | none | The bridge shall accept only parameter values listed in section 8; an illegal value shall be reported at elaboration. | 3:s24 (p136) |
| BR-3-34 | MUST | slave | both | The APB Access phase shall last 3 cycles (2 wait states). *(when: Device accepts request in first cycle and returns response in the following cycle)* | 3:s25 (p137) |
| BR-3-35 | MUST | slave | both | The APB Access phase shall last 2 cycles (1 wait state). *(when: Device returns response in the cycle it accepts the request)* | 3:s26 (p138) |
| BR-3-36 | MUST | slave | both | The completion shall last 1 Access cycle with no wait state. *(when: Local error completion (REQ-ERR-001, REQ-ERR-002))* | 3:s27 (p139) |
| BR-3-37 | MUST | slave | both | A new Setup phase shall be accepted in the cycle after PREADY. *(when: Local error completion)* | 3:s27 (p139) |
| BR-3-38 | MUST | slave | scenario | Setup-to-Setup interval shall be the minimum: 4 cycles with prompt device, 3 with same-cycle response, 2 after local error, with no idle cycle added. *(when: i_apb_psel held high, back-to-back transfers)* | 3:s28 (p140) |
| BR-3-39 | MUST | system | none | The RTL shall comply with REF-003 and use the hierarchy of section 14.2. | 3:s29 (p141) |
| BR-3-40 | MUST | system | none | An APB protocol checker and the REF-005 TL-UL protocol checker shall be bound to the ports. *(when: Every simulation)* | 3:s30 (p142) |
| BR-3-41 | MUST | system | none | The RTL shall be scan-insertable: no latch, combinational loop, internal tri-state, clock gating, or gated/derived clock. | 3:s31 (p143) |

## 4 Features and configurations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-4-01 | MUST | system | none | The data width shall be fixed at 32 bits, with no data-width parameter. | 4:s3 (p154) |
| BR-4-02 | MUST_NOT | system | none | PARA_ADDR_W must not be configured with a value outside the range 16 to 32. | 4:s4 (p154) |

## 5.1 Overview and block responsibilities

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-5.1-01 | MUST | system | none | m_apb_if and m_tlul_if exchange one request bundle and one response bundle through internal wires, and neither module reads a port of the other bus. | 5.1:s4 (p160) |
| BR-5.1-02 | MUST | master | assertion | m_apb_if must assert w_req_launch to m_tlul_if during the Setup phase of a legal request so channel A is loaded at the coming edge. *(when: Setup phase of a legal request)* | 5.1:s10 (p173) |
| BR-5.1-03 | MUST | slave | assertion | w_resp_rdata must be forced to 0 for writes and for errors. *(when: Write response or error response)* | 5.1:s16 (p179) |

## 5.3 Transaction and dataflow

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-5.3-01 | MUST | system | assertion | The request is captured at the end of Setup straight into channel A flops, and channel A is valid in the first Access cycle, one cycle after Setup, with no buffer stage. *(when: Legal request in Setup)* | 5.3:s3, 5.3:s4 (p189) |
| BR-5.3-02 | MUST | system | assertion | At the end of the Setup phase a legal request must be loaded into the A-channel flops and reg_a_valid set. *(when: End of Setup cycle with a legal request)* | 5.3:s7 (p191) |
| BR-5.3-03 | MUST | system | assertion | At the end of the Setup phase an illegal request must load the response flops with PSLVERR = 1 and PREADY = 1. *(when: End of Setup cycle with an illegal request)* | 5.3:s7 (p191) |
| BR-5.3-04 | MUST | master | assertion | In A1, o_tlul_a_valid must be 1 with the converted request and o_tlul_d_ready must be 1. *(when: Access 1 phase)* | 5.3:s8 (p192) |
| BR-5.3-05 | MUST | slave | assertion | When i_tlul_a_ready is 1 the request is accepted at the end of A1. *(when: i_tlul_a_ready = 1 during A1)* | 5.3:s9 (p192) |
| BR-5.3-06 | MUST | system | scenario | At the end of A2 the response is checked and loaded into reg_prdata, reg_pslverr and reg_pready. *(when: End of A2 when response is returned)* | 5.3:s11 (p193) |
| BR-5.3-07 | MUST | system | assertion | In A3, o_apb_pready must be 1 with o_apb_prdata and o_apb_pslverr driven directly from flops, and the transfer ends at the end of A3. *(when: Access 3 phase)* | 5.3:s12, 5.3:s13 (p194) |
| BR-5.3-08 | MUST | system | scenario | If the device responds in A1, the response must be loaded at the end of A1 and PREADY must be 1 in A2. *(when: Device answers in the cycle it accepts the request (A1))* | 5.3:s15 (p197) |
| BR-5.3-09 | MUST | master | assertion | If a_ready is low, o_tlul_a_valid and channel A must stay unchanged and the Access phase is extended; likewise for a late response. *(when: i_tlul_a_ready low or response late)* | 5.3:s16 (p197) |
| BR-5.3-10 | MUST | system | scenario | The bridge must support back-to-back transfers without an idle cycle, recognizing Setup by levels i_apb_psel=1 and i_apb_penable=0 while the APB FSM is idle, not by a psel rising edge. *(when: Back-to-back transfers with i_apb_psel held at 1)* | 5.3:s18, 5.3:s19, 5.3:s20 (p199) |
| BR-5.3-11 | MUST | system | assertion | The APB FSM is in ENUM_ST_DONE in the PREADY cycle and in ENUM_ST_IDLE in the next cycle, so flops and FSMs are free for the next capture. *(when: After the PREADY cycle of a transfer)* | 5.3:s21, 5.3:s22 (p199) |
| BR-5.3-12 | MUST | system | scenario | Next transfers must start exactly like the first one when i_apb_psel is released for one or more cycles in between. *(when: Requester releases i_apb_psel for one or more cycles between transfers)* | 5.3:s23 (p199) |
| BR-5.3-13 | MUST | system | scenario | A write, a read and an illegal write must complete one after the other with i_apb_psel held high. *(when: Write, read and illegal write back to back with i_apb_psel held high)* | 5.3:s24 (p199) |

## 5.4 Invariants

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-5.4-01 | MUST | system | assertion | At most one TL-UL request is outstanding, and its a_source is PARA_SRC_ID. | 5.4:s1 (p203) |
| BR-5.4-02 | MUST | master | assertion | o_tlul_a_valid must be high only in TL-UL FSM state ENUM_ST_REQ. | 5.4:s2 (p204) |
| BR-5.4-03 | MUST | master | assertion | Channel A must not change while o_tlul_a_valid is high and i_tlul_a_ready is low. *(when: o_tlul_a_valid high and i_tlul_a_ready low)* | 5.4:s2 (p204) |
| BR-5.4-04 | MUST | slave | assertion | o_apb_pready must be high only in APB FSM state ENUM_ST_DONE, for one cycle. | 5.4:s3 (p205) |
| BR-5.4-05 | MUST_NOT | master | assertion | No TL-UL request may be issued for an illegal APB request. *(when: Illegal APB request)* | 5.4:s4 (p206) |
| BR-5.4-06 | MUST | system | assertion | The TL-UL FSM is idle whenever the APB FSM is idle. *(when: APB FSM idle)* | 5.4:s5 (p207) |

## 6.1 Interface inventory

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-6.1-01 | MUST | system | none | The bridge must provide the APB4 completer interface IF-001 (REF-001 Issue D APB4 subset) in CLK-CORE, required in all configurations. | 6.1:s1 (p215) |
| BR-6.1-02 | MUST | system | none | The bridge must provide the TL-UL host interface IF-002 (OpenTitan profile, REF-002) in CLK-CORE, required in all configurations. | 6.1:s2 (p216) |
| BR-6.1-03 | MUST | system | none | The bridge must provide the clock and reset input interface IF-003 in CLK-CORE, required in all configurations. | 6.1:s3 (p217) |

## 6.2 Complete port list

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-6.2-01 | MUST | master | assertion | i_apb_paddr bits [1:0] must be 0. *(when: When driving an APB transfer)* | 6.2:s11 (p230) |
| BR-6.2-02 | MUST | master | assertion | i_apb_pstrb must be 4'b1111 for a write. *(when: For an APB write at the Setup edge)* | 6.2:s13 (p232) |
| BR-6.2-03 | MUST | slave | assertion | o_apb_pready must be high for exactly one cycle per transfer and 0 in reset. | 6.2:s15 (p234) |
| BR-6.2-04 | MUST | slave | assertion | o_apb_prdata is valid with o_apb_pready and holds its last value otherwise; reset value is 0. | 6.2:s16 (p235) |
| BR-6.2-05 | MUST_NOT | slave | assertion | o_apb_pslverr must not be high unless o_apb_pready is high. | 6.2:s17 (p236) |
| BR-6.2-06 | MUST | master | assertion | o_tlul_a_valid is set at the Setup edge and held until i_tlul_a_ready; it is 0 in reset. | 6.2:s18 (p237) |
| BR-6.2-07 | MUST | master | assertion | o_tlul_a_opcode bit 2 is 1 for Get and bits [1:0] are constant 0; it must be stable while o_tlul_a_valid is high. | 6.2:s20 (p239) |
| BR-6.2-08 | MUST | master | assertion | o_tlul_a_param must always be 3'b000. | 6.2:s21 (p240) |
| BR-6.2-09 | MUST | master | assertion | o_tlul_a_size must always be 2'b10. | 6.2:s22 (p241) |
| BR-6.2-10 | MUST | master | assertion | o_tlul_a_source must always equal PARA_SRC_ID. | 6.2:s23 (p242) |
| BR-6.2-11 | MUST | master | assertion | o_tlul_a_address bits [1:0] must be constant 0 and the address must be stable while o_tlul_a_valid is high. | 6.2:s24 (p243) |
| BR-6.2-12 | MUST | master | assertion | o_tlul_a_mask must always be 4'b1111. | 6.2:s25 (p244) |
| BR-6.2-13 | MUST | master | assertion | o_tlul_a_data must be a copy of PWDATA and stable while o_tlul_a_valid is high. | 6.2:s26 (p245) |
| BR-6.2-14 | MUST | master | assertion | o_tlul_a_user must always be '0. | 6.2:s27 (p246) |
| BR-6.2-15 | MUST | master | assertion | o_tlul_d_ready must be 0 in reset and constant 1 after the first clock edge following reset release. | 6.2:s29 (p248) |
| BR-6.2-16 | MUST | system | assertion | Levels are held until acknowledged or changed; the only pulse is o_apb_pready, one cycle per transfer; static signals never change after reset. | 6.2:s38 (p258) |
| BR-6.2-17 | MUST | system | none | Unused inputs need a lint waiver. | 6.2:s42 (p258) |

## 6.3 Protocol behavior

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-6.3-01 | MUST | master | assertion | Setup phase lasts one cycle with PSEL=1 and PENABLE=0; the Access phase starts next cycle and lasts until PREADY is high. *(when: APB transfer)* | 6.3:s3 (p262) |
| BR-6.3-02 | MUST | master | assertion | PADDR, PWRITE, PWDATA and PSTRB stay unchanged from Setup until PREADY. *(when: from Setup until PREADY)* | 6.3:s4 (p262) |
| BR-6.3-03 | MUST | slave | assertion | The bridge asserts PSLVERR only together with PREADY. | 6.3:s5 (p262) |
| BR-6.3-04 | MUST | slave | scenario | The bridge ignores PSTRB on reads. *(when: APB read)* | 6.3:s6 (p262) |
| BR-6.3-05 | MUST | slave | scenario | Back-to-back transfers with i_apb_psel held high are accepted exactly like the first transfer with the same results. *(when: next Setup phase right after PREADY with i_apb_psel held at 1)* | 6.3:s7, 6.3:s17 (p262) |
| BR-6.3-06 | MUST | master | assertion | The bridge issues one TL-UL request at a time. | 6.3:s9 (p264) |
| BR-6.3-07 | MUST | master | assertion | The TL-UL request stays stable until accepted. *(when: request issued and not yet accepted)* | 6.3:s10 (p264) |
| BR-6.3-08 | MUST | master | scenario | The bridge accepts responses at any time and discards a response not belonging to an accepted request, with no APB effect. *(when: TL-UL response with no accepted request)* | 6.3:s11, 6.3:s20 (p264) |
| BR-6.3-09 | MUST | master | scenario | The bridge supports a TL-UL response in the same cycle as the request acceptance. *(when: response in same cycle as request acceptance)* | 6.3:s12 (p264) |
| BR-6.3-10 | MUST | master | both | The bridge issues PutFullData, size 2, mask 4'b1111 and completes normally. *(when: Write with PSTRB=4'b1111 and aligned address)* | 6.3:s13 (p268) |
| BR-6.3-11 | MUST | slave | both | PREADY=1 with PSLVERR=1 in the first Access cycle and no TL-UL request is issued. *(when: Write with PSTRB other than 4'b1111 (including 4'b0000))* | 6.3:s14 (p269) |
| BR-6.3-12 | MUST | master | both | The bridge issues Get, size 2, mask 4'b1111 and returns data on PRDATA. *(when: Read with aligned address)* | 6.3:s15 (p270) |
| BR-6.3-13 | MUST | slave | both | PREADY=1 with PSLVERR=1 in the first Access cycle and no TL-UL request is issued. *(when: Read or write with PADDR[1:0] not 2'b00)* | 6.3:s16 (p271) |
| BR-6.3-14 | MUST | slave | both | PSLVERR=1 and PRDATA=0. *(when: TL-UL response with d_error=1)* | 6.3:s18 (p273) |
| BR-6.3-15 | MUST | slave | both | PSLVERR=1 and PRDATA=0. *(when: TL-UL response with wrong d_opcode or d_source)* | 6.3:s19 (p274) |

## 7.2 CDC and RDC

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-7.2-01 | MUST | system | none | A CDC tool run must report zero crossings, since there is one clock domain and one reset domain. | 7.2:s1 (p311) |

## 7.3 Reset domains and sequencing

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-7.3-01 | MUST | system | none | i_rst_n_core is active-low, asserted asynchronously, and deasserted synchronously to i_clk_core (synchronous release provided by the SoC reset controller). | 7.3:s1 (p317) |
| BR-7.3-02 | MUST | master | both | Every flip-flop, including both FSM state registers and the payload registers, must be asynchronously reset; FSMs go to ENUM_ST_IDLE and all listed registers to 0. *(when: When i_rst_n_core is asserted)* | 7.3:s1, 7.3:s2 (p317) |
| BR-7.3-03 | MUST | master | assertion | After reset, o_tlul_a_opcode must be 3'b000, o_tlul_a_address 0, o_tlul_a_data 0 and o_tlul_a_valid 0. *(when: After reset)* | 7.3:s3 (p319) |
| BR-7.3-04 | MUST | master | assertion | o_tlul_d_ready must become 1 at the first clock edge after reset release. *(when: At the first clock edge after reset release)* | 7.3:s3 (p319) |
| BR-7.3-05 | MUST | system | scenario | The transfer is abandoned, and the SoC resets the APB Requester and TL-UL device together with the bridge. *(when: A transfer is in progress when reset asserts)* | 7.3:s4 (p319) |

## 7.4 Power intent (if applicable)

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-7.4-01 | MUST | system | none | The IP resides in the SoC always-on domain and has no isolation, retention or power sequencing of its own. | 7.4:s1 (p323) |

## 8 Parameters and elaboration configurations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-8-01 | MUST | system | scenario | PARA_ADDR_W (default 32, legal range 16 to 32) shall set the width of both i_apb_paddr and o_tlul_a_address. | 8:s3 (p338) |
| BR-8-02 | MUST | system | scenario | PARA_SRC_W (default 8, legal range 1 to 8) shall set the width of o_tlul_a_source and i_tlul_d_source. | 8:s4 (p339) |
| BR-8-03 | MUST | system | scenario | PARA_SRC_ID shall fit in PARA_SRC_W bits, i.e. lie in the range 0 to 2^PARA_SRC_W - 1. | 8:s4, 8:s5 (p339) |
| BR-8-04 | MUST | master | assertion | The value of o_tlul_a_source on every request and the expected i_tlul_d_source shall equal PARA_SRC_ID (default 0). | 8:s5 (p340) |
| BR-8-05 | MUST | master | assertion | o_tlul_a_user shall have width PARA_A_USER_W (default 1, range 1 to 32) and its bits shall always be driven to zero. | 8:s6 (p341) |
| BR-8-06 | MUST | system | scenario | PARA_D_SINK_W (default 1, range 1 to 4) shall set the width of i_tlul_d_sink, which has no behavioral effect. | 8:s7 (p342) |
| BR-8-07 | MUST | system | scenario | PARA_D_USER_W (default 1, range 1 to 32) shall set the width of i_tlul_d_user, which has no behavioral effect. | 8:s8 (p343) |
| BR-8-08 | MUST | master | scenario | m_tlul_if shall use fixed non-overridable constants LPARA_A_SIZE = 2, LPARA_A_MASK = 4'b1111 and LPARA_D_ACK_DATA = 1 (AccessAckData d_opcode). | 8:s11 (p350) |
| BR-8-09 | MUST | system | scenario | An illegal parameter value shall be reported at elaboration of the verification source set. *(when: An illegal parameter value is used)* | 8:s13 (p352) |
| BR-8-10 | MUST_NOT | system | scenario | An illegal parameter value shall not be silently clamped. *(when: An illegal parameter value is used)* | 8:s13 (p352) |

## 9 Data representation and arithmetic

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-9-01 | MUST | system | none | Byte lane i of the 32-bit data bus carries bits [8i+7:8i], and PSTRB[i] and a_mask[i] refer to the same lane. | 9:s3 (p356) |
| BR-9-02 | MUST | master | assertion | APB address bits [1:0] shall be 0 (word-aligned byte address). *(when: APB address presented)* | 9:s4 (p360) |
| BR-9-03 | MUST | slave | assertion | Bits [PARA_ADDR_W-1:2] of the APB address are copied to a_address[PARA_ADDR_W-1:2], and a_address[1:0] is 2'b00. | 9:s4 (p360) |
| BR-9-04 | MUST | slave | both | A non-zero value in APB address bits [1:0] shall give PSLVERR (REQ-ERR-002). *(when: APB address bits [1:0] are non-zero)* | 9:s4 (p360) |
| BR-9-05 | MUST | slave | assertion | a_opcode shall be 3'b000 (PutFullData) for writes and 3'b100 (Get) for reads, with bit 2 as read and bits [1:0] zero. | 9:s5 (p361) |
| BR-9-06 | MUST_NOT | slave | assertion | a_opcode values other than 3'b000 and 3'b100 shall never be generated. | 9:s5 (p361) |
| BR-9-07 | MUST | slave | assertion | a_size shall be 2'b10 (4 bytes) and no other value shall ever be generated. | 9:s6 (p362) |
| BR-9-08 | MUST | slave | assertion | a_mask shall be 4'b1111 and no other value shall ever be generated (DEC-001). | 9:s7 (p363) |
| BR-9-09 | MUST | slave | both | Any d_opcode value other than the expected one shall give PSLVERR. *(when: d_opcode differs from the expected value (3'b000 AccessAck for writes, 3'b001 AccessAckData for reads))* | 9:s8 (p364) |
| BR-9-10 | MUST | slave | assertion | Read data shall be forced to 0 for writes and for every error completion. *(when: write transfer or any error completion)* | 9:s9 (p365) |

## 10.1 Modes and state transitions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-10.1-01 | MUST | master | assertion | The APB FSM must go to ENUM_ST_BUSY and assert w_req_launch = 1 on a legal request in the Setup phase. *(when: APB FSM in ENUM_ST_IDLE, Setup phase (i_apb_psel = 1, i_apb_penable = 0) with a legal request)* | 10.1:s5 (p377) |
| BR-10.1-02 | MUST | master | assertion | The APB FSM must go to ENUM_ST_DONE, set reg_pready and reg_pslverr and clear reg_prdata at the Setup edge on an illegal request. *(when: APB FSM in ENUM_ST_IDLE, Setup phase with an illegal request)* | 10.1:s5 (p377) |
| BR-10.1-03 | MUST | master | assertion | The APB FSM must move to ENUM_ST_DONE, and reg_pready, reg_pslverr and reg_prdata must load the response at that edge. *(when: APB FSM in ENUM_ST_BUSY and w_resp_valid = 1)* | 10.1:s6 (p378) |
| BR-10.1-04 | MUST | master | assertion | The TL-UL FSM must hold o_tlul_a_valid = 1 with channel A stable in ENUM_ST_REQ, clear reg_a_valid on acceptance, and go to IDLE with a same-cycle response or WAIT without. *(when: TL-UL FSM in ENUM_ST_REQ)* | 10.1:s10 (p386) |
| BR-10.1-05 | MUST | master | assertion | A response must count only in ENUM_ST_WAIT, or in ENUM_ST_REQ together with i_tlul_a_ready = 1. | 10.1:s12 (p389) |
| BR-10.1-06 | MUST | master | both | An orphan i_tlul_d_valid in any other state must be discarded with no APB effect. *(when: d_valid arrives in any state other than WAIT or REQ with a_ready)* | 10.1:s13 (p389) |

## 10.3 Cycle-level behavior

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-10.3-01 | MUST | master | both | For an illegal request, PREADY and PSLVERR must be asserted in the first Access cycle with no channel A request. *(when: illegal request (local error))* | 10.3:s6 (p420) |
| BR-10.3-02 | MUST | master | both | With channel A back pressure, channel A must remain stable and the Access phase is extended. *(when: a_ready low)* | 10.3:s8 (p422) |
| BR-10.3-03 | MUST | master | assertion | At the end of S, channel A flops must load, reg_a_valid set, APB FSM go to BUSY and TL-UL FSM to REQ, with o_apb_pready and o_tlul_a_valid 0 in S. *(when: Setup cycle with legal request)* | 10.3:s16 (p432) |

## 11 Register and programming model

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-11-01 | MUST_NOT | system | none | The bridge has no software-visible registers; none are required or provided. | 11:s1 (p464) |
| BR-11-02 | MUST | slave | scenario | The bridge's only status indication is PSLVERR on each transfer; it is otherwise configured only by parameters. *(when: On each transfer)* | 11:s2 (p464) |

## 12 Error handling and recovery

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-12-01 | MUST | slave | assertion | The bridge must respond in the first Access cycle with PREADY = 1, PSLVERR = 1 and PRDATA = 0. *(when: APB write with PSTRB other than 4'b1111 (ERR-001))* | 12:s1 (p470) |
| BR-12-02 | MUST_NOT | slave | assertion | The bridge must not issue a TL-UL request for a write with PSTRB other than 4'b1111. *(when: APB write with PSTRB other than 4'b1111 (ERR-001))* | 12:s1 (p470) |
| BR-12-03 | MUST | slave | scenario | The next transfer must be independent of the error; no error state is stored and reset behavior is not applicable. *(when: After an ERR-001 error transfer)* | 12:s1 (p470) |
| BR-12-04 | MUST | slave | assertion | The bridge must respond as for ERR-001: PREADY = 1, PSLVERR = 1 in the first Access cycle, PRDATA = 0, and no TL-UL request. *(when: PADDR[1:0] is not 2'b00 (ERR-002))* | 12:s2 (p471) |
| BR-12-05 | MUST | slave | assertion | The bridge must drive PSLVERR = 1 and PRDATA = 0 together with PREADY. *(when: i_tlul_d_error = 1 on the accepted response (ERR-003))* | 12:s3 (p472) |
| BR-12-06 | MUST | slave | scenario | The next transfer must be independent of the error, with no stored error state. *(when: After an ERR-003, ERR-004 or ERR-005 error transfer)* | 12:s3, 12:s4, 12:s5 (p472) |
| BR-12-07 | MUST | slave | both | The bridge must drive PSLVERR = 1 and PRDATA = 0 together with PREADY, as for ERR-003. *(when: d_opcode is not equal to the expected opcode (ERR-004))* | 12:s4 (p473) |
| BR-12-08 | MUST | slave | both | The bridge must drive PSLVERR = 1 and PRDATA = 0 together with PREADY, as for ERR-003. *(when: d_source is not equal to PARA_SRC_ID (ERR-005))* | 12:s5 (p474) |
| BR-12-09 | MUST | slave | scenario | The bridge must not assert PREADY; the APB Requester waits, and recovery is by SoC watchdog or reset. *(when: No TL-UL response ever arrives (ERR-006))* | 12:s6 (p475) |
| BR-12-10 | MUST | slave | assertion | All detected errors must give the same result, PSLVERR = 1 with PRDATA = 0, with no priority between them. *(when: Any detected error)* | 12:s7 (p477) |
| BR-12-11 | MUST_NOT | slave | scenario | The bridge RTL must keep no sticky error flag; errors are visible only on PSLVERR. | 12:s9 (p477) |

## 13 Performance, power, and area

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-13-01 | MUST | slave | both | The access phase of a normal transfer must last 3 cycles (2 wait states). *(when: Device accepts in A1 and responds in A2 on a normal transfer)* | 13:s1 (p491) |
| BR-13-02 | MUST | slave | both | The access phase for a same-cycle response must last 2 cycles (1 wait state). *(when: Device responds in the acceptance cycle)* | 13:s2 (p492) |
| BR-13-03 | MUST | slave | both | The access phase of a local error must last 1 cycle (0 wait states). *(when: Illegal strobe or address causes a local error)* | 13:s3 (p493) |
| BR-13-04 | MUST | slave | both | The minimum transfer interval must be 4 cycles for normal, 3 for same-cycle response, and 2 for local error transfers. *(when: Also when i_apb_psel is held high)* | 13:s4 (p494) |

## 14.1 Required coding baseline

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-14.1-01 | MUST | system | none | The RTL must follow the VLSIT RTL Design Rules v2 (REF-003) as the mandatory RTL coding authority. | 14.1:s1 (p505) |
| BR-14.1-02 | MUST | system | none | The RTL must comply with the VLSIT RTL Design Rules without local exceptions. | 14.1:s2 (p505) |
| BR-14.1-03 | MUST | system | scenario | Every flip-flop, including the payload registers, must have the asynchronous reset of section 7.3. | 14.1:s3 (p505) |
| BR-14.1-04 | MUST | system | none | FSM signals must be named reg_fsm_apb_current_state, w_fsm_apb_nxt_state, reg_fsm_tlul_current_state, w_fsm_tlul_nxt_state with ENUM_ST_* members. | 14.1:s3 (p505) |
| BR-14.1-05 | MUST | system | none | Coding style: one module per file named as the module, structural top, ANSI ports with input wire and output logic, reg_/w_/p_ff_/p_com_ names, PARA_* parameters with three PAR-02 comment lines, names at most 30 characters, comment lines at most 100 characters. | 14.1:s3 (p505) |

## 14.2 RTL hierarchy

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-14.2-01 | MUST | system | none | m_apb_tlul_bridge is the structural top containing only ports, parameters, interconnect wires and the two instances, in CLK-CORE/RST-CORE domains. | 14.2:s1 (p511) |
| BR-14.2-02 | MUST | system | none | m_apb_if, instance u_apb_if, must contain all APB-facing logic: Setup detect, legality check, APB FSM and response flops reg_pready, reg_pslverr, reg_prdata. | 14.2:s2 (p512) |
| BR-14.2-03 | MUST | system | none | m_tlul_if, instance u_tlul_if, must contain all TL-UL-facing logic: channel A flops, TL-UL FSM, reg_d_ready and D-channel check. | 14.2:s3 (p513) |
| BR-14.2-04 | MUST | system | none | State is owned by m_apb_if and m_tlul_if; m_apb_if has no TL-UL port and m_tlul_if has no APB port. | 14.2:s4 (p515) |

## 14.3 Synthesis assumptions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-14.3-01 | MUST | system | none | Lint uses the project lint set with default_nettype none checking, waiving only the unused inputs i_apb_pprot, i_tlul_d_param, i_tlul_d_size, i_tlul_d_sink, i_tlul_d_user. *(when: lint)* | 14.3:s6 (p526) |

## 15.1 Scope and strategy

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-15.1-01 | MUST | system | none | The environment includes an APB Requester model driving legal/illegal requests with varied idle time, and a TL-UL device model delaying a_ready and d_valid, answering in acceptance cycle, injecting d_error, wrong opcode, wrong source and orphan responses. *(when: verification environment)* | 15.1:s2 (p532) |
| BR-15.1-02 | MUST | system | none | The APB protocol checker and the TL-UL protocol checker of REF-005 are bound at the ports. | 15.1:s3 (p532) |
| BR-15.1-03 | MUST | system | scenario | A scoreboard compares each TL-UL request and each APB completion with the APB transfer that caused it. | 15.1:s4 (p532) |
| BR-15.1-04 | MUST | system | none | Each simulation run records its seed. | 15.1:s5 (p532) |
| BR-15.1-05 | MUST | system | none | Every requirement in section 3 is covered by at least one passing test and all coverage bins of 15.3 are hit. *(when: acceptance)* | 15.1:s7 (p532) |

## 15.2 Requirement-based test plan

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-15.2-01 | MUST | slave | both | All listed outputs are 0 in reset, including o_tlul_a_opcode, o_tlul_a_address and o_tlul_a_data; o_tlul_d_ready becomes 1 at the first edge after release. *(when: during reset and after reset release)* | 15.2:s1 (p538) |
| BR-15.2-02 | MUST | slave | scenario | Bridge issues PutFullData, size 2, mask 4'b1111 with correct address and data, completes in 3 Access cycles, and PRDATA is 0. *(when: aligned write with PSTRB=4'b1111 to a prompt device)* | 15.2:s2 (p539) |
| BR-15.2-03 | MUST | slave | scenario | Scoreboard matches every TL-UL request and APB completion for random aligned reads and writes. *(when: random aligned reads and writes)* | 15.2:s3 (p540) |
| BR-15.2-04 | MUST | slave | both | No TL-UL request is issued; PREADY and PSLVERR are asserted in the first Access cycle and PRDATA is 0. *(when: write with PSTRB other than 4'b1111, or access with PADDR[1:0] nonzero)* | 15.2:s4, 15.2:s5 (p541) |
| BR-15.2-05 | MUST | slave | scenario | Bridge issues Get, ignores PSTRB, PRDATA equals d_data, and completes in 3 Access cycles. *(when: read, PSTRB zero or nonzero)* | 15.2:s6 (p543) |
| BR-15.2-06 | MUST | slave | both | PSLVERR is 1 and PRDATA is 0. *(when: response with d_error = 1 on read or write)* | 15.2:s7 (p544) |
| BR-15.2-07 | MUST | slave | both | PSLVERR is 1 and PRDATA is 0. *(when: wrong d_opcode or wrong d_source)* | 15.2:s8 (p545) |
| BR-15.2-08 | MUST | slave | both | Channel A is stable while valid and not ready, and the request is accepted once. *(when: random a_ready delays of 0 to 8 cycles)* | 15.2:s9 (p546) |
| BR-15.2-09 | MUST | slave | both | Orphan responses are discarded, have no APB effect, and the next transfer is correct. *(when: d_valid pulses while idle, before acceptance, or after the response)* | 15.2:s10 (p547) |
| BR-15.2-10 | MUST | slave | both | Transfer takes 2 Access cycles. *(when: response in the acceptance cycle)* | 15.2:s11 (p548) |
| BR-15.2-11 | MUST | slave | both | Both FSMs are idle after release and no completion is produced for the abandoned transfer. *(when: reset during A1, A2 or A3)* | 15.2:s12 (p549) |
| BR-15.2-12 | MUST | slave | both | Only one request is outstanding and intervals are as in 10.4. *(when: back-to-back transfers with random idle gaps)* | 15.2:s13 (p550) |
| BR-15.2-13 | MUST | system | scenario | Legal parameter values elaborate; illegal values are reported. *(when: parameter sweep)* | 15.2:s14 (p551) |
| BR-15.2-14 | MUST | system | none | Both protocol checkers are bound and report no checker error in any run. | 15.2:s15 (p552) |
| BR-15.2-15 | MUST | system | none | Lint reports no finding and CDC reports zero crossings. *(when: lint and CDC run)* | 15.2:s16 (p553) |
| BR-15.2-16 | MUST | system | none | Every non-constant output is driven by a flip-flop Q pin and module boundaries are as in 14.2. *(when: structural check)* | 15.2:s17 (p554) |
| BR-15.2-17 | MUST_NOT | system | none | Design contains no latch, loop, tri-state or gated clock. *(when: scan rule check)* | 15.2:s18 (p555) |
| BR-15.2-18 | MUST | slave | both | Every transfer completes correctly in order, Setup-to-Setup intervals are as in 10.4, and no TL-UL request is made for illegal ones. *(when: back-to-back transfers with psel held 1 and only penable changing, with or without idle cycles)* | 15.2:s19 (p556) |

## 15.3 Assertions and coverage

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-15.3-01 | MUST | slave | assertion | o_apb_pready is asserted only with i_apb_psel and i_apb_penable, for one cycle; o_apb_pslverr only with o_apb_pready. | 15.3:s1 (p562) |
| BR-15.3-02 | MUST | slave | assertion | Channel A remains stable. *(when: o_tlul_a_valid high and i_tlul_a_ready low)* | 15.3:s2 (p563) |
| BR-15.3-03 | MUST | slave | assertion | At most one TL-UL request is outstanding. | 15.3:s3 (p564) |
| BR-15.3-04 | MUST | slave | assertion | Opcode, size, mask and address are legal per REF-005 legalAOpcode, sizeMatchesMask, addrSizeAligned, contigMask. | 15.3:s4 (p565) |
| BR-15.3-05 | MUST | slave | assertion | a_param, a_size, a_mask, a_source and a_user are constant. | 15.3:s5 (p566) |
| BR-15.3-06 | MUST | slave | assertion | o_tlul_d_ready is 0 in reset and 1 from the first edge after release. *(when: reset)* | 15.3:s6 (p567) |
| BR-15.3-07 | MUST_NOT | slave | assertion | No TL-UL request is issued for an illegal APB request. *(when: illegal APB request)* | 15.3:s7 (p568) |
| BR-15.3-08 | MUST | slave | assertion | o_tlul_a_valid rises in the cycle after the legal Setup phase. *(when: after a legal Setup phase)* | 15.3:s8 (p569) |
| BR-15.3-09 | MUST_NOT | slave | assertion | An orphan response never changes o_apb_pready, o_apb_prdata or o_apb_pslverr. *(when: orphan response)* | 15.3:s9 (p570) |
| BR-15.3-10 | MUST | slave | assertion | Next cycle has o_tlul_a_valid = 1 for a legal request or o_apb_pready = 1 for an illegal request. *(when: i_apb_psel=1, i_apb_penable=0, APB FSM idle, including directly after a PREADY cycle)* | 15.3:s10 (p571) |
| BR-15.3-11 | MUST | system | none | Coverage COV-001 to COV-005 define bins (PSTRB values, error kinds, wait/delay cycles, orphan timing, back-to-back pairs) and all bins must be hit. *(when: coverage)* | 15.3:s11, 15.3:s12, 15.3:s13, 15.3:s14, 15.3:s15 (p572) |
| BR-15.3-12 | MUST | system | none | Checkers sample channel A only while o_tlul_a_valid is 1. | 15.3:s17 (p578) |

## 15.4 Formal, CDC, and RDC

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-15.4-01 | MUST | system | none | Formal verification is not required; verification is by simulation and assertions only. | 15.4:s1 (p584) |

## 16 DFT and testability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-16-01 | MUST | system | scenario | All flip-flops in the IP shall be scan-eligible, with no latch, combinational loop, tri-state, clock gating, or derived clock (REQ-DFT-001). | 16:s1 (p591) |
| BR-16-02 | MUST | system | none | The SoC controls the scan clock and any reset override in its wrapper or reset controller; the IP has no DFT ports. | 16:s2 (p592) |
| BR-16-03 | MUST | system | scenario | The IP is in the idle state after reset; test-mode entry/exit and safe state are handled by the SoC. *(when: After reset)* | 16:s3 (p593) |
| BR-16-04 | MUST_NOT | system | none | MBIST, memory repair, LBIST, test wrappers/test points, clock-gating test enable, extra ATPG constraints, and DFT insertion artifacts are not required in the IP beyond the general scan rule. | 16:s4, 16:s5, 16:s6, 16:s7, 16:s8 (p594) |

## 17.1 Timing constraints and budgets

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-17.1-01 | MUST | system | none | The SDC delivered with the IP (m_apb_tlul_bridge.sdc) must be the executable form of the timing tables, consistent with the clock, budget and exception tables. | 17.1:s1 (p604) |

## 17.1.2 Interface timing budgets

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-17.1.2-01 | MUST | master | none | Every changing APB4 and TL-UL output must be a flip-flop Q pin, with a timing budget of one cycle minus clock-to-output. | 17.1.2:s3 (p618) |

## 17.1.3 Timing exception inventory

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-17.1.3-01 | MUST_NOT | system | none | No false path, multicycle path, min/max delay or clock group is used; all paths are single-cycle in a single synchronous domain. | 17.1.3:s1 (p624) |

## 17.2 Physical assumptions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-17.2-01 | SHOULD | system | none | The integrator should place the APB pins and the TL-UL pins on the side of their respective buses. *(when: during floorplan and pin placement)* | 17.2:s2 (p631) |
| BR-17.2-02 | MAY | system | none | The integrator may buffer or duplicate the channel-A load enable. *(when: channel-A load enable fans out to about 66 flip-flops)* | 17.2:s5 (p634) |

## 18 Security, safety, and reliability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-18-01 | MUST | slave | scenario | The bridge ignores PPROT; it must not use PPROT for any access-control decision or to alter the TL-UL transfer. | 18:s2 (p644) |

## 20 Assumptions, dependencies, and decisions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| BR-20-01 | MUST | master | assertion | The APB Requester starts a transfer with a Setup phase (i_apb_psel = 1, i_apb_penable = 0) and keeps address and control stable until i_apb_pready. *(when: APB transfer start)* | 20:s1 (p691) |
| BR-20-02 | MUST | slave | scenario | The bridge shall support back-to-back transfers with i_apb_psel held high as valid transfers. *(when: Back-to-back transfers with i_apb_psel held high)* | 20:s1 (p691) |
| BR-20-03 | MUST | slave | assertion | The TL-UL device returns exactly one response per request and no response before the request is accepted. *(when: TL-UL request issued)* | 20:s2 (p692) |
| BR-20-04 | MUST | slave | scenario | Only full-strobe writes (PSTRB = 4'b1111) to word-aligned addresses are accepted and issued to TL-UL. *(when: APB write with PSTRB = 4'b1111 and word-aligned address)* | 20:s6 (p696) |
| BR-20-05 | MUST | slave | both | The bridge returns PSLVERR with no TL-UL request for any write PSTRB other than 4'b1111 and for any misaligned address. *(when: Write with PSTRB other than 4'b1111, including 4'b0000, or misaligned address)* | 20:s6 (p696) |
| BR-20-06 | MUST_NOT | slave | assertion | The bridge never issues TL-UL PutPartialData. | 20:s6 (p696) |
| BR-20-07 | MUST_NOT | slave | scenario | The bridge has no timeout and no drain mechanism; the APB Requester waits indefinitely for a device that never answers. *(when: TL-UL device never answers)* | 20:s8 (p698) |
| BR-20-08 | MUST | slave | none | Every output that can change comes from a flip-flop. | 20:s10 (p700) |
| BR-20-09 | MUST | slave | assertion | Outputs a_param, a_size, a_mask, a_source, a_user, a_opcode[1:0] and a_address[1:0] never change after reset and are constant tie-offs. *(when: After reset)* | 20:s10 (p700) |
| BR-20-10 | MUST | slave | both | The response is checked for d_error, d_opcode and d_source; any failure gives PSLVERR = 1 and PRDATA = 0. *(when: Response fails the d_error, d_opcode or d_source check)* | 20:s13 (p703) |
| BR-20-11 | MUST | slave | assertion | o_tlul_d_ready is 0 in reset and 1 from the first clock edge after reset release. *(when: Reset asserted and after release)* | 20:s15 (p705) |
| BR-20-12 | MUST | slave | both | The Setup phase is recognized by levels i_apb_psel = 1 and i_apb_penable = 0, never by an edge of i_apb_psel, with no added idle cycle between back-to-back transfers. | 20:s19 (p709) |
| BR-20-13 | MUST | master | none | Whether an APB master can issue a first Access cycle without a preceding Setup phase must be checked at integration, since a hang would result. | 20:s25 (p715) |

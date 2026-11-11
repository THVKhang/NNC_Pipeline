# Extracted rules - AsyncGrayFIFO_Design_Specification.md

```
rules: 517  by strength {'MUST': 438, 'MUST_NOT': 61, 'MAY': 15, 'SHOULD': 3}  by check {'none': 138, 'scenario': 164, 'both': 72, 'assertion': 143}
normative sentences: 204  cited 197  skipped 7  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 31 (0 from cache)  cost US$1.3607  tokens in 186341 out 70845
```


## T1 Asynchronous Gray-Code FIFO Design Specification

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-T1-01 | MUST | any | none | A requirement stated with 'shall' is mandatory and must be testable. *(when: Requirement is stated with the term 'shall')* | T1:s7 (p19) |

## 1.1 Purpose and scope

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-1.1-01 | MUST | system | scenario | The FIFO transfers a stream of data words from the write clock domain to the unrelated read clock domain. | 1.1:s1 (p50) |
| AF-1.1-02 | MUST | system | both | Words are read out in the same order in which they were written. | 1.1:s2 (p50) |
| AF-1.1-03 | MUST | system | both | Write and read pointers cross between clock domains as Gray codes through configurable synchronizers. | 1.1:s3 (p50) |
| AF-1.1-04 | MUST | system | both | The IP reports full, empty, full-with-threshold, empty-with-threshold, overflow, and underflow flags to the two domains. | 1.1:s4, 1.1:s11 (p50) |
| AF-1.1-05 | MUST | system | none | The structural top m_vlsit_afifo_top instantiates the write module, the read module, and the FIFO array module. | 1.1:s6 (p54) |
| AF-1.1-06 | MUST | system | none | The write module operates in the write clock domain and the read module in the read clock domain. | 1.1:s7 (p55) |
| AF-1.1-07 | MUST | system | scenario | The synchronizer module instantiates one technology cell wrapper per bit, supporting five cell options (bypass, two D-FF cells, 2-FF, 3-FF, 4-FF), configurable bit width and configurable reset value. | 1.1:s8 (p56) |
| AF-1.1-08 | MUST | system | none | The synchronizer module is the only module instantiating the cell wrapper, and the wrapper is the only module containing cells and the metastability model. | 1.1:s9 (p56) |
| AF-1.1-09 | MUST | system | scenario | The FIFO array module provides a pure RTL implementation and a library SRAM (one write port, one read port) replacement branch. | 1.1:s10 (p57) |
| AF-1.1-10 | MUST | system | scenario | Software reset is a reset input in the write clock domain using a four-phase handshake that resets both pointers in the right order and blocks both interfaces during the reset. | 1.1:s12 (p59) |
| AF-1.1-11 | MUST | system | none | Verification-only models (synchronizer metastability model, SRAM macro model) and example technology cell models are provided. | 1.1:s13, 1.1:s14 (p60) |
| AF-1.1-12 | MUST_NOT | system | none | The IP does not include reset synchronizers; each reset input must already be synchronized to its own clock. | 1.1:s16, 1.1:s17 (p65) |

## 1.2 Deployment assumptions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-1.2-01 | MUST | system | scenario | The FIFO works with two asynchronous clocks with no restriction on frequency or frequency ratio. | 1.2:s3 (p77) |

## 1.3 Feature summary

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-1.3-01 | MUST | system | scenario | The asynchronous FIFO with Gray-coded pointers feature (FEAT-001) is always present. *(when: always)* | 1.3:s1 (p85) |
| AF-1.3-02 | MUST | system | scenario | The FIFO has a configurable number of entries and data width. | 1.3:s2 (p86) |
| AF-1.3-03 | MUST | system | both | The FIFO provides full and empty flags. | 1.3:s3 (p87) |
| AF-1.3-04 | MUST | system | both | The FIFO provides full-with-threshold and empty-with-threshold flags. | 1.3:s4 (p88) |
| AF-1.3-05 | MUST | system | both | The FIFO provides overflow and underflow flags. | 1.3:s5 (p89) |
| AF-1.3-06 | MUST | system | scenario | The synchronizer has 2, 3, or 4 stages by cell option 1 to 4; option 0 is a bypass without stages. *(when: PARA_AFIFO_CELL_TYPE selects 1 to 4)* | 1.3:s6 (p90) |
| AF-1.3-07 | MUST | system | scenario | The technology-cell synchronizer uses one cell wrapper per bit with PARA_AFIFO_CELL_TYPE: 0 bypass, 1 two D-FF cells, 2 one 2-FF cell, 3 one 3-FF cell, 4 one 4-FF cell. | 1.3:s7 (p91) |
| AF-1.3-08 | MAY | system | scenario | The FIFO array may use the library SRAM branch when PARA_AFIFO_MEM_USE_MACRO is 1. *(when: PARA_AFIFO_MEM_USE_MACRO = 1)* | 1.3:s8 (p92) |
| AF-1.3-09 | MUST | system | none | A synchronizer metastability simulation model is delivered as the simulation branch of cell wrapper m_vlsit_afifo_cell_sync. *(when: simulation)* | 1.3:s9 (p93) |
| AF-1.3-10 | MUST | system | none | The SRAM macro model VLSIT_CELL_SRAM_1W1R, a synthesizable RTL stand-in of the library macro, is delivered. *(when: PARA_AFIFO_MEM_USE_MACRO = 1)* | 1.3:s10 (p94) |
| AF-1.3-11 | MUST | system | none | Example technology cell models for simulation are delivered. | 1.3:s11 (p95) |
| AF-1.3-12 | MUST | system | scenario | Software reset uses a four-phase handshake between the two domains. | 1.3:s12 (p96) |

## 2.1 Normative references

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-2.1-01 | MUST | system | none | RTL deliverables must follow VLSIT RTL Design Rules v2 (REF-003) as the mandatory RTL coding, hierarchy, reset, CDC and naming baseline. | 2.1:s3 (p106) |

## 2.2 Source-of-truth and conflict handling

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-2.2-01 | MUST | system | none | The RTL must comply with REF-003 as the mandatory RTL baseline. | 2.2:s2 (p113) |
| AF-2.2-02 | MUST_NOT | system | none | A requirement that conflicts with REF-003 must not be accepted as a local exception; it must be listed as a decision instead. *(when: A requirement conflicts with REF-003)* | 2.2:s3 (p113) |
| AF-2.2-03 | MUST | system | none | The specification defining the IP contract must stay consistent with REF-002 and REF-003. | 2.2:s5 (p114) |

## 3 Requirements and traceability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-3-01 | MUST | system | scenario | The IP shall implement an asynchronous FIFO with independent write clock domain and read clock domain. | 3:s3 (p130) |
| AF-3-02 | MUST | system | both | Pointers shall cross between the domains as Gray codes only. | 3:s4 (p131) |
| AF-3-03 | MUST | system | assertion | Each Gray pointer register shall change at most one bit per clock cycle of its own domain. | 3:s4 (p131) |
| AF-3-04 | MUST | system | both | Words shall be read in write order; every accepted write is read exactly once, with no word lost, duplicated or reordered. | 3:s5 (p132) |
| AF-3-05 | MUST | system | both | The write shall be accepted: i_wr_data is stored in the entry addressed by the write pointer and the write pointer advances by one. *(when: At a write-clock edge when i_wr_en = 1 and full flag is 0)* | 3:s6 (p133) |
| AF-3-06 | MUST | system | both | The read shall be accepted and the read pointer shall advance by one. *(when: At a read-clock edge when i_rd_en = 1 and empty flag is 0)* | 3:s7 (p134) |
| AF-3-07 | MUST | system | none | Each domain shall hold a binary pointer of LPARA_PTR_W = log2(depth)+1 bits and a Gray pointer register derived from the next binary pointer. | 3:s8 (p135) |
| AF-3-08 | MUST | system | none | The Gray pointer register shall be the launch register of the crossing, with no logic between it and the synchronizer. | 3:s8 (p135) |
| AF-3-09 | MUST | system | none | The depth shall be a power of 2 with a minimum of 2; there is no upper limit. | 3:s9 (p136) |
| AF-3-10 | MUST | system | assertion | o_full shall be 1, generated in the write domain, and never 0 while the FIFO is physically full. *(when: When the write domain has no free entry judged from the synchronized read pointer)* | 3:s10 (p137) |
| AF-3-11 | MAY | system | scenario | o_full may stay 1 late (pessimistic). *(when: After a read frees an entry)* | 3:s10 (p137) |
| AF-3-12 | MUST | system | assertion | o_empty shall be 1, generated in the read domain, and never 0 while the FIFO is physically empty. *(when: When the read domain has no word to read judged from the synchronized write pointer)* | 3:s11 (p138) |
| AF-3-13 | MAY | system | scenario | o_empty may stay 1 late (pessimistic). *(when: After a write)* | 3:s11 (p138) |
| AF-3-14 | MUST | system | both | o_full_thr shall be 1 when the write-domain occupancy estimate is greater than or equal to i_full_thr, for every LPARA_PTR_W-bit value. | 3:s12 (p139) |
| AF-3-15 | MUST | system | both | o_empty_thr shall be 1 when the read-domain occupancy estimate is less than or equal to i_empty_thr, for every LPARA_PTR_W-bit value. | 3:s12 (p139) |
| AF-3-16 | MUST | system | assertion | Occupancy estimate is binary write pointer minus binary read pointer, using the synchronized pointer of the other domain; both threshold flags are combinational. | 3:s12 (p139) |
| AF-3-17 | MUST_NOT | system | none | The thresholds are static and shall not change while the FIFO is in use. *(when: While the FIFO is in use)* | 3:s12 (p139) |
| AF-3-18 | MUST | system | none | m_vlsit_afifo_top shall be a structural wrapper instantiating only m_vlsit_afifo_wr, m_vlsit_afifo_rd and m_vlsit_afifo_mem. | 3:s13 (p140) |
| AF-3-19 | MUST | system | none | m_vlsit_afifo_wr shall contain write pointer, full/threshold, overflow logic, read Gray pointer synchronizer, write-side software reset FSM, acknowledge synchronizer and memory write port outputs; m_vlsit_afifo_rd the read-side equivalents. | 3:s14 (p141) |
| AF-3-20 | MUST | system | scenario | m_vlsit_afifo_sync shall provide a configurable-width synchronizer with reset value per bit; stages are 2 for options 1 and 2, 3 for option 3, 4 for option 4, 0 for option 0. | 3:s15 (p142) |
| AF-3-21 | MUST | system | none | m_vlsit_afifo_sync shall contain no flip-flop or cell of its own and shall instantiate only m_vlsit_afifo_cell_sync, one per bit, in every configuration and both VLSIT_SYNTHESIS branches. | 3:s16 (p143) |
| AF-3-22 | MUST | system | scenario | The wrapper shall select by PARA_AFIFO_CELL_TYPE: 0 bypass (o_q = i_d), 1 two series DFFs, 2 one 2-FF cell, 3 one 3-FF cell, 4 one 4-FF cell. | 3:s16 (p143) |
| AF-3-23 | MUST_NOT | system | none | Option 0 (bypass) shall not be used for a Gray pointer crossing. *(when: For a Gray pointer crossing)* | 3:s16 (p143) |
| AF-3-24 | MUST | system | none | m_vlsit_afifo_mem shall be an independent module instantiated in m_vlsit_afifo_top, modelled as an SRAM with one write port (write domain) and one read port (read domain). | 3:s17 (p144) |
| AF-3-25 | MUST | system | none | m_vlsit_afifo_mem shall provide a generate branch replacing the RTL array with a library 1W1R SRAM through m_vlsit_afifo_ram_macro; the default is the RTL array. | 3:s18 (p145) |
| AF-3-26 | MUST | system | both | o_rd_data shall always show the word at the current read pointer, including while empty (show-ahead); after each read-clock edge it is the word at the new read pointer. | 3:s19 (p146) |
| AF-3-27 | MUST | system | scenario | The read module shall drive the storage read address of the next read pointer and the storage shall be read every read-clock cycle. | 3:s19 (p146) |
| AF-3-28 | MUST | system | both | Full, empty and threshold flags shall be combinational functions of local pointer registers and the synchronized pointer of the other domain. | 3:s20 (p147) |
| AF-3-29 | MUST | system | none | Module ports shall be as listed in Section 6 and top ports shall not depend on parameter values. | 3:s21 (p148) |
| AF-3-30 | MUST | system | scenario | Write and read clocks shall be treated as fully asynchronous with no assumed phase or frequency relation and no frequency restriction. | 3:s22 (p149) |
| AF-3-31 | MUST | system | none | Every clock-domain crossing shall use a Gray pointer registered in its own domain followed directly by m_vlsit_afifo_sync, with no logic before the first stage or between stages. | 3:s23 (p150) |
| AF-3-32 | MUST | system | scenario | The read data path from the FIFO array to the read domain shall be valid. *(when: Whenever the pointer protocol allows a read)* | 3:s24 (p151) |
| AF-3-33 | MUST | system | none | m_vlsit_afifo_wr shall contain only write-clock-domain logic and m_vlsit_afifo_rd only read-clock-domain logic; the array is owned by neither and is instantiated in the top. | 3:s25 (p152) |
| AF-3-34 | MUST | system | none | i_rst_n_wr shall be already synchronized to i_clk_wr and i_rst_n_rd to i_clk_rd; the IP shall not contain a reset synchronizer. | 3:s26 (p153) |
| AF-3-35 | MUST | system | both | The FIFO shall be empty: both pointers 0, full = 0, empty = 1, overflow = 0, underflow = 0. *(when: After hardware reset or release of software reset)* | 3:s27 (p154) |
| AF-3-36 | MUST | system | scenario | Flops shall use asynchronous-assert active-low reset; the two resets are independent and need not be asserted together. | 3:s27 (p154) |
| AF-3-37 | MUST | system | none | The depth shall be configurable by PARA_AFIFO_DEPTH. | 3:s28 (p155) |
| AF-3-38 | MUST | system | none | The data width shall be configurable by PARA_AFIFO_DATA_W. | 3:s29 (p156) |
| AF-3-39 | MUST_NOT | system | none | The RTL shall not contain an elaboration check for illegal parameter values; verification shall use legal values only. | 3:s30 (p157) |
| AF-3-40 | MUST | system | both | o_overflow shall be raised as a 1-cycle pulse and the write shall not change stored data or the write pointer. *(when: When a write is requested while the FIFO is full)* | 3:s31 (p158) |
| AF-3-41 | MUST | system | both | o_underflow shall be raised as a 1-cycle pulse, the read pointer unchanged, and o_rd_data keeps showing the word at the current read pointer. *(when: When a read is requested while the FIFO is empty)* | 3:s32 (p159) |
| AF-3-42 | MUST | system | scenario | A software reset sequence shall start; i_rst_n_sw is active-low in the write domain and may be held for one or more write-clock cycles. *(when: i_rst_n_sw = 0 seen at a write-clock edge while the write reset FSM is in RUN)* | 3:s33 (p160) |
| AF-3-43 | MUST | system | none | The request shall be a register req_wr in m_vlsit_afifo_wr crossing to the read domain via m_vlsit_afifo_sync (width 1, same stage count) with no logic before the first stage. | 3:s34 (p161) |
| AF-3-44 | MUST_NOT | system | assertion | A read request shall not be accepted, combinationally with zero latency. *(when: While the synchronized request is 1 or the read reset FSM is not in RUN)* | 3:s35 (p162) |
| AF-3-45 | MUST | system | assertion | o_empty shall be 1. *(when: From the cycle the read side is blocked until it is released)* | 3:s36 (p163) |
| AF-3-46 | MUST | system | both | It shall reset the read pointer (binary and Gray) to 0 and only then raise ack_rd. *(when: When the read reset FSM has seen the request)* | 3:s37 (p164) |
| AF-3-47 | MUST | system | none | The acknowledge shall cross to the write domain through m_vlsit_afifo_sync (width 1, same stage count) with no logic before the first stage. | 3:s38 (p165) |
| AF-3-48 | MUST | system | both | It shall reset the write pointer (binary and Gray) to 0. *(when: When the write reset FSM has seen the synchronized acknowledge)* | 3:s39 (p166) |
| AF-3-49 | MUST_NOT | system | assertion | A write request shall not be accepted, combinationally with zero latency from i_rst_n_sw and FSM state. *(when: From the write-clock cycle with i_rst_n_sw = 0 until the write reset FSM is back in RUN)* | 3:s40 (p167) |
| AF-3-50 | MUST | system | both | The handshake shall have four phases: request up, acknowledge up, request down, acknowledge down. | 3:s41 (p168) |
| AF-3-51 | MUST_NOT | system | assertion | The request shall not fall before i_rst_n_sw = 1 and the write pointer is reset; the acknowledge shall not fall before the request is seen at 0 in the read domain. | 3:s41 (p168) |
| AF-3-52 | MUST | system | assertion | The read reset FSM shall return to RUN only when the synchronized request is 0 and the synchronized write Gray pointer is 0. | 3:s42 (p169) |
| AF-3-53 | MUST | system | assertion | The write reset FSM shall return to RUN only when the synchronized acknowledge is 0 and the synchronized read Gray pointer is 0. | 3:s42 (p169) |
| AF-3-54 | MUST | system | assertion | The read FSM shall return to RUN before the write FSM returns to RUN. *(when: After software reset)* | 3:s43 (p170) |
| AF-3-55 | MUST | system | both | Flags shall be generated by normal FIFO logic; both pointers are 0, so o_empty = 1 and o_full = 0 until the first write crosses to the read domain. *(when: After software reset release)* | 3:s44 (p171) |
| AF-3-56 | MUST | system | scenario | The software reset sequence shall complete for any i_rst_n_sw width, any clock frequency and ratio, and with the metastability model enabled. | 3:s45 (p172) |
| AF-3-57 | MUST | system | scenario | Words in the FIFO are discarded; a read accepted before the request reaches the read domain returns a valid pre-reset word; storage is not cleared. *(when: When software reset starts)* | 3:s46 (p173) |
| AF-3-58 | MUST | system | scenario | A hardware reset of a domain shall have priority over software reset, asynchronously resetting that domain's FSM and pointers. | 3:s47 (p174) |
| AF-3-59 | MUST | system | scenario | Writes shall stay blocked and a new sequence shall start when the FSM is back in RUN. *(when: If i_rst_n_sw = 0 is seen again while the write FSM is in REL)* | 3:s48 (p175) |
| AF-3-60 | MUST | system | assertion | o_full shall be 1. *(when: During software reset while the write side is blocked)* | 3:s49 (p176) |
| AF-3-61 | MUST_NOT | system | assertion | A blocked write or read shall not raise o_overflow or o_underflow. *(when: During software reset)* | 3:s49 (p176) |
| AF-3-62 | MUST | system | assertion | o_full_thr and o_empty_thr shall take the values of an empty FIFO. *(when: During software reset)* | 3:s49 (p176) |
| AF-3-63 | MUST | system | both | o_sw_rst_busy shall be the direct output of flop reg_sw_rst_busy with no combinational logic, set when the write reset FSM leaves RUN and cleared when it returns to RUN. | 3:s50 (p177) |
| AF-3-64 | MUST | system | assertion | o_sw_rst_busy shall be 1 in states REQ, PTR, HOLD, REL and 0 in RUN independent of i_rst_n_sw and read FSM state, and 0 after i_rst_n_wr hardware reset. | 3:s50 (p177) |
| AF-3-65 | MUST | system | assertion | The write block wr_blk shall equal o_sw_rst_busy OR (i_rst_n_sw = 0). | 3:s50 (p177) |
| AF-3-66 | MUST | system | none | RTL shall comply with REF-003; technology cells and memory macros shall appear only in m_vlsit_afifo_cell_sync and m_vlsit_afifo_ram_macro. | 3:s51 (p178) |
| AF-3-67 | MUST | system | none | Synthesis, lint, CDC, formal and equivalence flows shall define VLSIT_SYNTHESIS; in that branch m_vlsit_afifo_cell_sync contains only library cell instances and follows REF-003. | 3:s52 (p179) |
| AF-3-68 | MUST | system | none | Every technology library cell and memory macro instance shall be named u_dont_touch_ (e.g. u_dont_touch_dff_0, u_dont_touch_sync2ff, u_dont_touch_sram); design module instances keep u_. | 3:s53 (p180) |
| AF-3-69 | MUST | system | scenario | m_vlsit_afifo_cell_sync shall contain a metastability model, per bit, applying an independent random latency of S-1, S or S+1 destination cycles to each input change; a new change replaces the pending one and restarts the delay. *(when: Without VLSIT_SYNTHESIS, options 1 to 4)* | 3:s54 (p181) |
| AF-3-70 | MUST | system | scenario | The model shall be controlled by plusargs +AFIFO_MSYNC_SEED (seed) and +AFIFO_MSYNC_EN (0 = nominal latency); default enabled with seed 1; it prints its seed at simulation start. | 3:s54 (p181) |
| AF-3-71 | MUST_NOT | system | none | No module other than m_vlsit_afifo_cell_sync shall model metastability; option 0 has no model. | 3:s54 (p181) |
| AF-3-72 | MUST | system | none | m_vlsit_afifo_ram_macro shall instantiate only VLSIT_CELL_SRAM_1W1R in every flow and both branches, matching Section 6.2 interface, with no simulation model of its own. *(when: For CFG-MACRO)* | 3:s55 (p182) |
| AF-3-73 | MUST | system | none | Example technology cell models shall be delivered as synthesizable RTL, one module per file in 000_Common/rtl_cells, following REF-003 except names (pins CK, RN or SN, D, Q). *(when: For CFG-CELL)* | 3:s56 (p183) |
| AF-3-74 | MUST | system | scenario | m_vlsit_afifo_cell_sync shall contain one behavioral model per option with the same function and stage count as the synthesis cells, including the metastability model for options 1 to 4. *(when: Without VLSIT_SYNTHESIS)* | 3:s56 (p183) |
| AF-3-75 | MUST_NOT | system | none | The IP shall have no DFT port and no test hook. | 3:s59 (p186) |
| AF-3-76 | MUST | system | none | The constraint contract of Section 17 shall be delivered with the IP. | 3:s60 (p187) |

## 4 Features and configurations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-4-01 | MUST | system | scenario | Each optional feature must be absent from the logic when its parameter is 0, with the generate branch not elaborated. *(when: when the parameter enabling an optional feature is 0)* | 4:s5 (p200) |
| AF-4-02 | MUST | system | scenario | The top-level port list must be the same in every configuration. | 4:s6 (p200) |
| AF-4-03 | MUST_NOT | any | none | Parameter values outside those defined in Section 8 must not be used; such illegal combinations are not checked by the IP. | 4:s7 (p200) |

## 5.1 Overview and block responsibilities

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-5.1-01 | MUST | system | assertion | Flags are pessimistic: full and empty may be late to deassert but must never deassert early. | 5.1:s7 (p208) |
| AF-5.1-02 | MUST | system | none | The storage is a separate module instantiated in the top, its write port in the write domain and its read port in the read domain. | 5.1:s7, 5.3:s17, 5.3:s18 (p208) |

## 5.3 Transaction and dataflow

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-5.3-01 | MUST | slave | both | The write domain accepts i_wr_data and drives the memory write port with enable, address (low LPARA_ADDR_W bits of binary write pointer) and data, storing the word. *(when: i_wr_en = 1 and full = 0)* | 5.3:s1, 5.3:s2 (p228) |
| AF-5.3-02 | MUST | slave | both | The binary write pointer increments, its Gray code is registered, and the Gray pointer crosses to the read domain. *(when: on an accepted write)* | 5.3:s3 (p228) |
| AF-5.3-03 | MUST | slave | scenario | After S read-clock stages of the selected cell the read domain sees the new write Gray pointer and updates empty from it. *(when: after a write)* | 5.3:s4, 5.3:s5 (p229) |
| AF-5.3-04 | MUST | slave | assertion | o_rd_data always shows the word at the read address (show-ahead). | 5.3:s6 (p230) |
| AF-5.3-05 | MUST | slave | both | The read domain accepts a read, increments the read pointer so o_rd_data shows the next word, and registers the Gray code. *(when: i_rd_en = 1 and empty = 0)* | 5.3:s7, 5.3:s8 (p230) |
| AF-5.3-06 | MUST | slave | scenario | The read Gray pointer crosses to the write domain, which after the synchronizer latency sees it, updates full and frees the entry for a new write. *(when: after a read)* | 5.3:s9, 5.3:s10, 5.3:s11 (p230) |
| AF-5.3-07 | MUST | slave | scenario | i_rst_n_sw starts a handshake blocking both interfaces, resets the read pointer first and the write pointer after the acknowledge, and releases the read side before the write side. *(when: software reset)* | 5.3:s12, 5.4:s7 (p232) |
| AF-5.3-08 | MUST | slave | assertion | The storage read port is synchronous and is read every read-clock cycle. | 5.3:s15 (p234) |
| AF-5.3-09 | MUST | slave | scenario | The read-domain storage output register may capture an unsettled word only while the FIFO is empty, and the word is captured again before o_empty falls. | 5.3:s16 (p234) |
| AF-5.3-10 | MUST | slave | none | The read data from the storage returns to the read module. | 5.3:s20 (p236) |

## 5.4 Invariants

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-5.4-01 | MUST | system | assertion | The number of stored words (write pointer minus read pointer modulo 2 x depth) stays between 0 and PARA_AFIFO_DEPTH. | 5.4:s1 (p240) |
| AF-5.4-02 | MUST_NOT | slave | assertion | full and empty are never both 1. | 5.4:s2 (p241) |
| AF-5.4-03 | MUST | slave | assertion | A Gray pointer register changes at most one bit per clock cycle. | 5.4:s3 (p242) |
| AF-5.4-04 | MUST_NOT | slave | assertion | The write side must not overwrite an entry not yet read, and the read side must not read an entry not yet written, per registered flags. | 5.4:s4 (p243) |
| AF-5.4-05 | MUST | slave | assertion | A rejected write or read leaves pointers and storage unchanged. *(when: a write rejected (overflow) or read rejected (underflow))* | 5.4:s5 (p244) |
| AF-5.4-06 | MUST | slave | assertion | At the instant a side leaves software reset, its own pointer and its synchronized copy of the other pointer are both 0. *(when: when a side leaves software reset)* | 5.4:s6 (p245) |

## 6.1 Interface inventory

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-6.1-01 | MUST | system | scenario | IF-001 must be provided as a required custom write interface (enable + data) on the producer side in the CLK-WR domain, with input data and output flags. *(when: All configurations)* | 6.1:s1 (p253) |
| AF-6.1-02 | MUST | system | scenario | IF-002 must be provided as a required custom read interface (enable + data) on the consumer side in the CLK-RD domain, with input enable and output data and flags. *(when: All configurations)* | 6.1:s2 (p254) |
| AF-6.1-03 | MUST | system | none | IF-003 must provide the required internal interconnect (wr to mem write port, rd to mem read address, mem to rd read data) spanning CLK-WR and CLK-RD. *(when: All configurations)* | 6.1:s3 (p255) |
| AF-6.1-04 | MUST | system | scenario | IF-004 must be provided as a required software reset control (level input request, optional busy output status) in the CLK-WR domain. *(when: All configurations)* | 6.1:s4 (p256) |

## 6.2 Complete port list

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-6.2-01 | MUST_NOT | system | none | The top-level port list must never depend on a parameter value. | 6.2:s4 (p260) |
| AF-6.2-02 | MUST | system | scenario | CLK-type ports are free running, rising-edge active, with no clock gating inside the IP. | 6.2:s6 (p266) |
| AF-6.2-03 | MUST | any | scenario | Active-low reset must stay low for at least one clock edge of its domain so the flops are reset; it is released synchronously outside the IP. *(when: When an active-low reset is asserted)* | 6.2:s7, 6.2:s20, 6.2:s31 (p267) |
| AF-6.2-04 | MUST | system | both | Each edge with request level 1 and acceptance condition true (not full / not empty) is exactly one transaction; request is level-sampled with no minimum width. *(when: At each rising clock edge where the request is 1 and the acceptance condition holds)* | 6.2:s8, 6.2:s21, 6.2:s32 (p268) |
| AF-6.2-05 | MUST | system | both | i_wr_data is captured only at the edge where the write is accepted and ignored otherwise. | 6.2:s9, 6.2:s22 (p269) |
| AF-6.2-06 | MUST | system | assertion | LVL-STS flags are combinational from registers, stay 1 while the condition holds, and change only after a clock edge or synchronizer stage, except for static threshold effects. | 6.2:s10 (p270) |
| AF-6.2-07 | MUST | system | assertion | REG-STS outputs are driven directly by a flop with no combinational logic and change only at a clock edge of their domain. | 6.2:s11 (p271) |
| AF-6.2-08 | MUST | system | assertion | PULSE outputs are registered, 1 for exactly one clock cycle per event in the cycle after the rejected request, return to 0 by themselves, and are not sticky. *(when: After a rejected write (while full) or read (while empty))* | 6.2:s12, 6.2:s28, 6.2:s37 (p272) |
| AF-6.2-09 | MUST | any | none | The consumer must sample PULSE outputs at every clock edge or count the cycles. | 6.2:s12 (p272) |
| AF-6.2-10 | MUST_NOT | any | assertion | STATIC threshold inputs must not change while the FIFO is in use; they are written once before use, with no synchronizer. *(when: While the FIFO is in use)* | 6.2:s13, 6.2:s23, 6.2:s33 (p273) |
| AF-6.2-11 | MUST | system | scenario | The IP reacts to the i_rst_n_sw level sampled at i_clk_wr; one reset sequence runs per assertion and ends only after the level is de-asserted. *(when: When i_rst_n_sw is low)* | 6.2:s14, 6.2:s24 (p274) |
| AF-6.2-12 | MUST | system | assertion | REG-LVL handshake signals come from flops, cross through a 1-bit synchronizer, change only on a handshake step and stay stable until the other side has answered. | 6.2:s15, 6.2:s44, 6.2:s45, 6.2:s51, 6.2:s52 (p275) |
| AF-6.2-13 | MUST | system | assertion | Gray pointer registers change by at most one bit per clock edge and enter synchronizers directly with no logic before the first stage. | 6.2:s16, 6.2:s39, 6.2:s40, 6.2:s47, 6.2:s48, 6.2:s56 (p276) |
| AF-6.2-14 | MAY | system | none | INT signals may be combinational or registered interconnect between two blocks. | 6.2:s17 (p277) |
| AF-6.2-15 | MUST | system | both | Writes are blocked from the cycle in which i_rst_n_sw is 0; a one-cycle low pulse or a longer low level starts the reset handshake. *(when: From the cycle in which i_rst_n_sw is 0)* | 6.2:s24 (p288) |
| AF-6.2-16 | MUST | system | both | o_sw_rst_busy is set at the edge where the write FSM leaves RUN and cleared at the edge where it returns to RUN, equal to write FSM not in RUN. | 6.2:s25 (p289) |
| AF-6.2-17 | MUST | system | both | o_full is combinational from the write pointer and synchronized read pointer; writes are rejected while it is 1, and it is 1 while the write side is blocked by software reset. *(when: While o_full is 1)* | 6.2:s26 (p290) |
| AF-6.2-18 | MUST | system | assertion | o_full_thr is a combinational function of i_full_thr and the pointers, 1 when occupancy estimate is greater than or equal to i_full_thr. | 6.2:s27 (p291) |
| AF-6.2-19 | MUST | system | both | o_rd_data shows the word at the current read pointer (show-ahead); an accepted read consumes it and the next word appears. *(when: When o_empty = 0)* | 6.2:s34 (p302) |
| AF-6.2-20 | MUST | system | both | o_empty is combinational from read pointer and synchronized write pointer, reads are rejected while it is 1, and it is 1 during the whole software reset. *(when: While o_empty is 1)* | 6.2:s35 (p303) |
| AF-6.2-21 | MUST | system | assertion | o_empty_thr is a combinational function of i_empty_thr and the pointers, 1 when occupancy estimate is less than or equal to i_empty_thr. | 6.2:s36 (p304) |
| AF-6.2-22 | MUST | system | assertion | The Gray pointer registers are updated only at the clock edge that accepts a write or read, respectively. | 6.2:s40, 6.2:s48 (p312) |
| AF-6.2-23 | MUST | system | assertion | o_mem_wr_en is 1 combinationally in the cycle when i_wr_en = 1 and o_full = 0. | 6.2:s41 (p313) |
| AF-6.2-24 | MUST | system | assertion | o_mem_wr_addr is a register output of the low bits of the binary write pointer, and o_mem_wr_data copies i_wr_data in the same cycle. | 6.2:s42, 6.2:s43 (p314) |
| AF-6.2-25 | MUST | system | assertion | o_mem_rd_addr is a combinational function of i_rd_en and the empty flag, giving the low bits of the next read pointer. | 6.2:s49 (p325) |
| AF-6.2-26 | MUST | system | assertion | The storage is read in every read-clock cycle with no read enable; i_mem_rd_data is valid after the edge that captured the address (latency 1) and drives o_rd_data. | 6.2:s50 (p326) |
| AF-6.2-27 | MUST | system | assertion | The sync o_data is a register output delayed by S destination edges after the change (S to S+2 with the metastability model). | 6.2:s57 (p337) |
| AF-6.2-28 | MUST | system | assertion | The cell resets or sets all stages asynchronously per PARA_AFIFO_CELL_RST_VAL; o_q is the last-stage output, or i_d itself with option 0. | 6.2:s60, 6.2:s62 (p344) |
| AF-6.2-29 | MUST | system | assertion | The memory stores i_wr_data at i_wr_addr at the i_clk_wr edge when write enable is 1. *(when: At the i_clk_wr edge with i_wr_en = 1)* | 6.2:s65, 6.2:s66, 6.2:s67 (p353) |
| AF-6.2-30 | MUST | system | assertion | The memory samples i_rd_addr every read-clock cycle and o_rd_data registers the word at it with latency 1; the array has no reset. | 6.2:s69, 6.2:s70, 6.2:s71 (p357) |
| AF-6.2-31 | MUST | system | assertion | i_rd_en_n of the RAM macro wrapper is tied to 0 by m_vlsit_afifo_mem. | 6.2:s78 (p371) |
| AF-6.2-32 | MUST | system | assertion | Each DW bit whose BWEB bit is 0 is written to the word at AW; the wrapper ties BWEB to zero for whole-word write. *(when: At the rising edge of CLKW with WEB = 0)* | 6.2:s83, 6.2:s84 (p377) |
| AF-6.2-33 | MUST | system | assertion | At the CLKR rising edge with REB = 0, QR shows the word at AR after the edge; QR keeps its value while REB = 1. | 6.2:s85, 6.2:s86 (p378) |
| AF-6.2-34 | MUST | system | scenario | The model VLSIT_CELL_SRAM_1W1R returns the old word and the stored word is not corrupted. *(when: Simultaneous read and write of the same address)* | 6.2:s87 (p379) |
| AF-6.2-35 | MUST | system | none | m_vlsit_afifo_ram_macro instantiates VLSIT_CELL_SRAM_1W1R as u_dont_touch_sram and nothing else, in every flow. | 6.2:s90 (p380) |
| AF-6.2-36 | MUST | system | none | VLSIT_CELL_SRAM_1W1R is a synthesizable RTL model with the write port in the CLKW domain with mask BWEB and QR a CLKR-domain register. | 6.2:s91 (p380) |

## 6.3 Protocol behavior

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-6.3-01 | MUST | slave | both | When i_wr_en = 1 and full = 0, the FIFO accepts the write and stores the word. *(when: i_wr_en = 1 and full = 0 and not in software reset)* | 6.3:s3 (p388) |
| AF-6.3-02 | MUST | slave | both | A write while full = 1 must be rejected (word not stored) and overflow must be raised. *(when: i_wr_en = 1 and full = 1)* | 6.3:s4 (p389) |
| AF-6.3-03 | MUST | slave | both | When i_rd_en = 1 and empty = 0, the FIFO accepts the read and the read pointer advances. *(when: i_rd_en = 1 and empty = 0 and not in software reset)* | 6.3:s5 (p390) |
| AF-6.3-04 | MUST | slave | both | A read while empty = 1 must be rejected (pointer not advanced) and underflow must be raised. *(when: i_rd_en = 1 and empty = 1)* | 6.3:s6 (p391) |
| AF-6.3-05 | MAY | any | scenario | Simultaneous write and read are allowed; the write and read interfaces operate independently in their different clock domains. *(when: write and read occur simultaneously in different clock domains)* | 6.3:s7 (p392) |
| AF-6.3-06 | MUST | slave | scenario | When i_rst_n_sw is low for one cycle or more, the FIFO performs a four-phase handshake, blocks both interfaces and resets the pointers. *(when: i_rst_n_sw = 0 (level, one cycle or more))* | 6.3:s8 (p393) |
| AF-6.3-07 | MUST_NOT | slave | both | Writes or reads during the software reset must not be accepted and must not generate an error pulse. *(when: i_wr_en or i_rd_en = 1 during the software reset)* | 6.3:s9 (p394) |
| AF-6.3-08 | MUST | any | assertion | Interface signals are sampled on the rising edge of the respective domain clock. | 6.3:s10 (p396) |
| AF-6.3-09 | MUST | slave | scenario | i_wr_data is captured at the accepting edge, so no hold of i_wr_data after that edge is required. *(when: at the accepting write edge)* | 6.3:s11 (p396) |

## 6.4 Interrupts and events

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-6.4-01 | MUST_NOT | slave | none | The FIFO has no interrupt output. | 6.4:s1 (p400) |
| AF-6.4-02 | MAY | system | none | The integrator derives an interrupt from the overflow and underflow flags. *(when: if an interrupt is required)* | 6.4:s3 (p400) |

## 7.1 Clock domains

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-7.1-01 | MUST | system | none | The write domain CLK-WR is clocked by i_clk_wr on its rising edge, with no clock gating inside the IP. | 7.1:s1 (p408) |
| AF-7.1-02 | MUST | system | none | The read domain CLK-RD is clocked by i_clk_rd on its rising edge, with no clock gating inside the IP. | 7.1:s2 (p409) |

## 7.2 CDC and RDC

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-7.2-01 | MUST | system | both | The write Gray pointer is registered in CLK-WR, then passes through m_vlsit_afifo_sync (2/3/4 stages) in the read domain, reset by i_rst_n_rd to PARA_AFIFO_SYNC_RST_VAL. *(when: Write Gray pointer crossing CLK-WR to CLK-RD (CDC-001))* | 7.2:s1 (p415) |
| AF-7.2-02 | MUST | system | both | The read Gray pointer is registered in CLK-RD, then passes through m_vlsit_afifo_sync in the write domain, reset by i_rst_n_wr. *(when: Read Gray pointer crossing CLK-RD to CLK-WR (CDC-002))* | 7.2:s2 (p416) |
| AF-7.2-03 | MUST | system | both | Stored data is read by the read domain without a synchronizer and must be stable by the pointer protocol when read. *(when: Stored data crossing CLK-WR to CLK-RD (CDC-003))* | 7.2:s3 (p417) |
| AF-7.2-04 | MUST | system | scenario | i_full_thr and i_empty_thr are static, written once before the FIFO is used and not changed while in use, and are not synchronized. | 7.2:s4 (p418) |
| AF-7.2-05 | MUST | system | both | req_wr is registered in CLK-WR, then passes through a 1-bit m_vlsit_afifo_sync (2/3/4 stages) in the read domain, reset to 0 by i_rst_n_rd. *(when: Software reset request crossing CLK-WR to CLK-RD (CDC-005))* | 7.2:s5 (p419) |
| AF-7.2-06 | MUST | system | both | ack_rd is registered in CLK-RD, then passes through a 1-bit m_vlsit_afifo_sync in the write domain, reset to 0 by i_rst_n_wr. *(when: Software reset acknowledge crossing CLK-RD to CLK-WR (CDC-006))* | 7.2:s6 (p420) |
| AF-7.2-07 | MUST_NOT | system | none | No combinational logic is allowed between the launch Gray register and the first synchronizer stage, nor between synchronizer stages. *(when: Between the launch Gray register and the first synchronizer stage, and between stages)* | 7.2:s7 (p422) |
| AF-7.2-08 | MAY | system | none | Logic such as Gray-to-binary conversion and compare may follow the last synchronizer stage. *(when: After the last synchronizer stage)* | 7.2:s8 (p422) |
| AF-7.2-09 | MUST | system | none | The bundled-data assumption of CDC-003 shall be waived with the documented rationale in the CDC tool. | 7.2:s9 (p422) |
| AF-7.2-10 | MUST | system | both | The software reset is a synchronous reset of pointers and flags performed by each domain's FSM and adds no asynchronous reset or reset-domain crossing. *(when: Software reset)* | 7.2:s10 (p424) |
| AF-7.2-11 | MAY | system | scenario | The two hardware resets are independent inputs and need not be asserted together. | 7.2:s12 (p424) |
| AF-7.2-12 | MUST_NOT | system | none | The IP neither detects nor repairs the inconsistent pointer state that results from resetting only one domain. *(when: Only one domain is reset after the FIFO was used)* | 7.2:s13, 7.2:s14 (p424) |

## 7.3 Reset domains and sequencing

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-7.3-01 | MUST | system | both | i_rst_n_wr is active-low, asserts asynchronously, and resets all write-domain state, the read-pointer synchronizer and flags: pointers 0, full 0, overflow 0. *(when: i_rst_n_wr asserted)* | 7.3:s1 (p430) |
| AF-7.3-02 | MUST | system | both | i_rst_n_rd is active-low, asserts asynchronously, and resets all read-domain state, the write-pointer synchronizer and flags: pointers 0, empty 1, underflow 0. *(when: i_rst_n_rd asserted)* | 7.3:s2 (p431) |
| AF-7.3-03 | MUST | system | both | i_rst_n_sw is an active-low synchronous software reset acting through both FSMs, resetting pointers to 0, o_empty to 1, o_full to 0, without clearing storage. *(when: i_rst_n_sw asserted)* | 7.3:s3 (p432) |
| AF-7.3-04 | MUST | system | scenario | Software reset deassertion follows the Section 10.7 handshake, read side first. *(when: Deassertion of the software reset)* | 7.3:s3 (p432) |
| AF-7.3-05 | MUST | system | assertion | Control and validity state (pointers, flags) are reset. *(when: Reset)* | 7.3:s4 (p434) |
| AF-7.3-06 | MUST | system | scenario | FIFO storage is resetless; its content is not consumed until the write pointer proves it was written, and o_rd_data while empty is undefined until written. | 7.3:s5 (p434) |
| AF-7.3-07 | MUST | system | both | i_rst_n_wr and i_rst_n_rd act asynchronously on the FSMs and pointers of their domain at any time, also during a software reset. *(when: Hardware reset asserted, including during a software reset)* | 7.3:s9 (p436) |
| AF-7.3-08 | MUST_NOT | system | none | The IP does not repair the case where the handshake waits forever for the other domain. *(when: Only one domain gets a hardware reset during a software reset)* | 7.3:s10 (p436) |

## 8 Parameters and elaboration configurations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-8-01 | MUST | system | none | Parameters shall be declared as parameter logic [31:0] PARA_AFIFO_ with the three comment lines required by REF-003 PAR-02. | 8:s1 (p445) |
| AF-8-02 | MUST_NOT | system | none | The RTL shall not include an elaboration check for illegal parameter values. | 8:s3 (p447) |
| AF-8-03 | MAY | system | none | $clog2 may be used for the derived widths. | 8:s3 (p447) |
| AF-8-04 | MUST | system | none | PARA_AFIFO_DEPTH (default 8) shall be a power of 2, minimum 2, with no upper limit; LPARA_ADDR_W and LPARA_PTR_W derive from it. | 8:s4 (p451) |
| AF-8-05 | MUST | system | scenario | PARA_AFIFO_DATA_W (default 32) shall be at least 1, with no upper limit, and sets the width of i_wr_data, o_rd_data and storage. | 8:s5 (p452) |
| AF-8-06 | MUST | system | scenario | PARA_AFIFO_CELL_TYPE (default 2) shall be 0..4 (0 bypass, 1 two series D flip-flops, 2 one 2-FF cell, 3 one 3-FF cell, 4 one 4-FF cell), with the same value on top, wr, rd, sync, cell_sync and both crossings. | 8:s6 (p453) |
| AF-8-07 | MUST_NOT | system | none | Option 0 (bypass, no synchronization) shall not be used for the pointer crossings. *(when: for the pointer crossings)* | 8:s6 (p453) |
| AF-8-08 | MUST | system | scenario | PARA_AFIFO_CELL_RST_VAL (default 0) shall be 0 for a flop with asynchronous reset to 0 or 1 for asynchronous set to 1, taken per synchronizer bit from PARA_AFIFO_SYNC_RST_VAL. | 8:s7 (p454) |
| AF-8-09 | MUST | system | scenario | PARA_AFIFO_MEM_USE_MACRO (default 0) shall be 0 for an RTL array or 1 for the library SRAM wrapper, using the generic macro model until a real macro is mapped. | 8:s8 (p455) |
| AF-8-10 | MUST | system | scenario | PARA_AFIFO_SYNC_W shall be 1 or more and is set by the parent to LPARA_PTR_W, giving the synchronizer width. | 8:s9 (p456) |
| AF-8-11 | MUST | system | scenario | PARA_AFIFO_SYNC_RST_VAL (default 0) shall be a vector of PARA_AFIFO_SYNC_W bits giving one reset value per bit for every synchronizer stage. | 8:s10 (p457) |
| AF-8-12 | MUST | system | scenario | PARA_AFIFO_SYNC_RST_VAL shall be a legal Gray pointer value, namely 0. *(when: for the pointer crossings)* | 8:s10 (p457) |
| AF-8-13 | MUST | system | scenario | LPARA_ADDR_W shall be derived as log2 of PARA_AFIFO_DEPTH, and LPARA_PTR_W shall be derived as LPARA_ADDR_W + 1. | 8:s11, 8:s12 (p458) |
| AF-8-14 | MUST_NOT | system | none | Illegal configurations (depth not a power of 2, depth below 2, stage count outside 2..4, option parameter outside 0..1) shall not be used. | 8:s17 (p468) |
| AF-8-15 | MUST_NOT | system | none | The IP shall not check illegal configurations, and behavior with an illegal value is undefined. | 8:s18 (p468) |

## 9 Data representation and arithmetic

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-9-01 | MUST | system | assertion | The binary pointer shall be an unsigned LPARA_PTR_W-bit value ranging 0 to 2 x depth - 1 and wrapping by design, with no extension or truncation. | 9:s1 (p474) |
| AF-9-02 | MUST | system | assertion | The address shall be the low LPARA_ADDR_W bits of the binary pointer (0 to depth - 1), formed by truncating the MSB. | 9:s2 (p475) |
| AF-9-03 | MUST | system | assertion | The Gray pointer shall be LPARA_PTR_W bits wide, computed as gray = bin XOR (bin >> 1), changing one bit per increment. | 9:s3 (p476) |
| AF-9-04 | MUST | system | assertion | Gray to binary conversion shall be LPARA_PTR_W bits wide, where bit i of binary equals XOR of Gray bits i..LPARA_PTR_W-1; invalid Gray values cannot occur in the model with one-bit changes. *(when: After the synchronizer)* | 9:s4 (p477) |
| AF-9-05 | MUST | system | assertion | The occupancy estimate shall be the binary pointer difference modulo 2 x depth with explicit width cast, and shall differ from true occupancy only by pointer updates still inside the synchronizer (pessimistic). | 9:s5 (p478) |
| AF-9-06 | MUST | system | assertion | The data word shall be an unsigned PARA_AFIFO_DATA_W-bit logic vector, bit 0 as LSB, with no interpretation, extension or truncation. | 9:s6 (p479) |
| AF-9-07 | MUST | system | assertion | Flags shall be 1 bit wide, where 1 means the condition is true. | 9:s7 (p480) |
| AF-9-08 | MUST | system | none | All hardware data shall be unsigned 4-state logic vectors, and no signed arithmetic shall be used. | 9:s8, 9:s9 (p482) |

## 10.1 Modes and state transitions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-10.1-01 | MUST | slave | assertion | While empty, o_empty must be 1 and reads must be rejected; a read request produces o_underflow. *(when: FIFO in Empty state (after reset or all words read))* | 10.1:s3 (p492) |
| AF-10.1-02 | MUST | slave | scenario | In the Partial state, reads and writes must both be accepted. *(when: FIFO between empty and full)* | 10.1:s4 (p493) |
| AF-10.1-03 | MUST | slave | assertion | While full, o_full must be 1 and writes must be rejected; a write request produces o_overflow. *(when: FIFO in Full state (all entries used, write view))* | 10.1:s5 (p494) |
| AF-10.1-04 | MUST | slave | scenario | Software reset must block both interfaces, set o_empty = 1, reset pointers by the handshake, and signal o_sw_rst_busy until both reset FSMs are back in RUN, read side first. *(when: i_rst_n_sw = 0 with the write FSM in RUN)* | 10.1:s6 (p495) |

## 10.2 Operations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-10.2-01 | MUST | slave | scenario | A write must store the data, increment the write pointer and register its Gray value, queuing the word. *(when: i_wr_en = 1 and o_full = 0)* | 10.2:s1 (p501) |
| AF-10.2-02 | MUST | slave | scenario | A read must increment the read pointer and register its Gray value; o_rd_data then shows the next word with no extra latency (show-ahead). *(when: i_rd_en = 1 and o_empty = 0)* | 10.2:s2, 10.3:s9 (p502) |
| AF-10.2-03 | MUST | slave | assertion | The write must be rejected and o_overflow must pulse for one cycle in the cycle after the request. *(when: i_wr_en = 1 and o_full = 1)* | 10.2:s3 (p503) |
| AF-10.2-04 | MUST | slave | assertion | The read must be rejected and o_underflow must pulse for one cycle in the cycle after the request. *(when: i_rd_en = 1 and o_empty = 1)* | 10.2:s4 (p504) |
| AF-10.2-05 | MUST | slave | scenario | Software reset must run a four-phase handshake (block, reset read pointer, acknowledge, reset write pointer, release read side, release write side), leaving the FIFO empty with both pointers 0 and flags normal. *(when: i_rst_n_sw = 0 and write FSM in RUN)* | 10.2:s5 (p505) |

## 10.3 Cycle-level behavior

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-10.3-01 | MUST | slave | scenario | A destination-domain flag, combinational from the synchronized pointer, must reflect a source pointer update after destination edge S. *(when: After a source pointer register changes, with S synchronizer stages)* | 10.3:s3, 10.3:s4, 10.3:s5, 10.3:s6 (p513) |
| AF-10.3-02 | MUST | slave | scenario | The flag must change after destination edge S, S+1, or S+2. *(when: With the metastability model)* | 10.3:s7 (p517) |
| AF-10.3-03 | MUST | slave | assertion | Flags must be pessimistic in between: never report not-full or not-empty prematurely. *(when: While the pointer crossing is in progress)* | 10.3:s8 (p517) |

## 10.4 Arbitration, buffering, and throughput

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-10.4-01 | MUST | slave | scenario | The write pointer Gray register must update at the same edge as the storage write, and an entry must be rewritten only after the write domain has seen the read pointer pass it. | 10.4:s4 (p532) |
| AF-10.4-02 | MUST | slave | none | The storage output register must capture the word on every read-clock edge. | 10.4:s5 (p533) |
| AF-10.4-03 | MUST_NOT | slave | assertion | o_empty must not fall earlier than the second read-clock edge after the write; minimum latency is S >= 2 edges, also for the model. *(when: After a write, with nominal synchronizer stages)* | 10.4:s6, 10.4:s8 (p533) |
| AF-10.4-04 | MUST | slave | none | The word must be clean, with the storage-to-output-register path shorter than one read-clock period. *(when: At the edge where o_empty falls)* | 10.4:s7 (p533) |

## 10.5 Memories and storage

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-10.5-01 | MUST_NOT | slave | assertion | A valid word must never be read while it is being written. *(when: A word is valid (o_empty = 0))* | 10.5:s3 (p543) |
| AF-10.5-02 | MUST_NOT | slave | scenario | The value read must not be used because o_empty = 1; the macro model returns the old word. *(when: A read of an address being written while o_empty = 1)* | 10.5:s4 (p543) |
| AF-10.5-03 | MAY | slave | none | A real macro may return an unknown value. *(when: Real macro read of an address being written while empty)* | 10.5:s5 (p543) |
| AF-10.5-04 | MUST_NOT | slave | scenario | Reads must not be accepted before a write (o_empty = 1); o_rd_data may be undefined while the entry at the read pointer was never written. *(when: Before any write)* | 10.5:s7 (p544) |
| AF-10.5-05 | MUST | slave | scenario | The macro wrapper must present show-ahead behavior, with a synchronous storage read using the next-pointer address. *(when: For the macro wrapper)* | 10.5:s10 (p546) |

## 10.6.2 Write and read with the RTL array (CFG-BASE, PARA_AFIFO_MEM_USE_MACRO = 0)

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-10.6.2-01 | MUST | master | both | The write is accepted; the storage array and the write Gray pointer both update at that same write edge. *(when: At a write clock edge where i_wr_en = 1 and o_full = 0)* | 10.6.2:s5, 10.6.2:s23, 10.6.2:s24 (p586) |
| AF-10.6.2-02 | MUST | slave | scenario | o_rd_data shows the new word (show-ahead) before o_empty falls, because the storage is read every cycle with the next read pointer address. *(when: After a write to an empty FIFO)* | 10.6.2:s6, 10.6.2:s7, 10.6.2:s26 (p587) |
| AF-10.6.2-03 | MUST | slave | scenario | o_empty falls S read edges after the first capturing edge of the write pointer, combinationally from the synchronized pointer. *(when: After the write pointer is first captured by the read domain)* | 10.6.2:s7, 10.6.2:s28 (p588) |
| AF-10.6.2-04 | MUST | slave | both | The write is dropped with write pointer and storage unchanged, and o_overflow pulses for one write cycle. *(when: i_wr_en sampled at a write edge while o_full = 1)* | 10.6.2:s9, 10.6.2:s31, 10.6.3:s11 (p590) |
| AF-10.6.2-05 | MUST | slave | both | o_rd_data moves to the next word right after the read edge without extra latency. *(when: After an accepted read)* | 10.6.2:s10, 10.6.2:s27 (p591) |
| AF-10.6.2-06 | MUST | slave | scenario | o_full falls late, after the read pointer crosses to the write domain, not at the read edge. *(when: After the first read from a full FIFO)* | 10.6.2:s11, 10.6.2:s28 (p592) |
| AF-10.6.2-07 | MUST | slave | both | The read is rejected with read pointer and storage unchanged, and o_underflow pulses for one read cycle. *(when: i_rd_en sampled at a read edge while o_empty = 1)* | 10.6.2:s13, 10.6.2:s31, 10.6.3:s15 (p594) |
| AF-10.6.2-08 | MUST | slave | scenario | o_rd_data keeps the old word until the next read edge, which captures the new word while o_empty is still 1. *(when: Write to an empty FIFO at the entry addressed by the read pointer)* | 10.6.2:s14, 10.6.2:s15, 10.6.2:s33 (p595) |
| AF-10.6.2-09 | MUST | master | assertion | i_wr_en, i_wr_data and i_rd_en change only at rising edges of their respective clocks. | 10.6.2:s18, 10.6.2:s20, 10.6.3:s20 (p600) |
| AF-10.6.2-10 | MUST_NOT | slave | assertion | Neither o_empty nor o_full may be early; flags are pessimistic. | 10.6.2:s29 (p608) |
| AF-10.6.2-11 | MUST | slave | assertion | o_overflow and o_underflow are registered, one cycle wide, and return to 0 by themselves. | 10.6.2:s30 (p609) |

## 10.6.3 Write and read with the SRAM macro (CFG-MACRO, PARA_AFIFO_MEM_USE_MACRO = 1)

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-10.6.3-01 | MUST | slave | scenario | Both storage configurations give the same waveforms at every port, and the macro returns the old word when read and write of the same address occur at the same edge. *(when: Array and macro configurations)* | 10.6.3:s21 (p649) |
| AF-10.6.3-02 | MUST | master | none | The testbench ignores o_rd_data while o_empty = 1. *(when: While o_empty = 1)* | 10.6.3:s22 (p649) |
| AF-10.6.3-03 | MUST | slave | assertion | o_rd_data is never X when a read is accepted. *(when: When a read is accepted)* | 10.6.3:s22 (p649) |

## 10.6.4 Metastability model of the synchronizer (simulation branch, REQ-VER-001)

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-10.6.4-01 | MUST | system | scenario | Each synchronized bit independently gets a seed-chosen extra delay of 0, 1 or 2 destination cycles. *(when: Metastability model enabled, a bit changes at the input of the last stage)* | 10.6.4:s3, 10.6.4:s4 (p653) |
| AF-10.6.4-02 | MUST | system | scenario | The model output equals the plain chain output. *(when: Extra delay chosen is 0)* | 10.6.4:s5 (p653) |
| AF-10.6.4-03 | MUST | system | scenario | The pending value is replaced by the new input value and the delay restarts. *(when: Input changes again while a change is pending)* | 10.6.4:s6 (p653) |
| AF-10.6.4-04 | MUST | system | none | The metastability model is controlled by +AFIFO_MSYNC_EN (enable) and +AFIFO_MSYNC_SEED (seed). | 10.6.4:s7 (p653) |
| AF-10.6.4-05 | MAY | system | scenario | Different bits of the same signal can get different delays. | 10.6.4:s28 (p684) |
| AF-10.6.4-06 | MAY | system | scenario | The replacement can make a short pulse disappear on the model output. *(when: A pending change is replaced)* | 10.6.4:s30 (p685) |
| AF-10.6.4-07 | MUST | slave | scenario | FIFO flags stay pessimistic, delayed S, S+1 or S+2 destination edges after the first capturing edge. *(when: With the metastability model, a bit arrives late)* | 10.6.4:s31, 10.6.4:s32 (p685) |

## 10.6.5 Back-to-back write and read

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-10.6.5-01 | MUST | master | scenario | Consumer sets i_rd_en = 1 at the first read edge after seeing o_empty = 0, keeps it, and drops it at the edge of the 24th accepted read. *(when: burst read scenario with consumer)* | 10.6.5:s4, 10.6.5:s13 (p690) |
| AF-10.6.5-02 | MUST | master | assertion | All inputs i_wr_en, i_wr_data and i_rd_en change only at rising edges of their own clock. | 10.6.5:s5, 10.6.5:s19 (p690) |
| AF-10.6.5-03 | MUST | slave | scenario | A word is accepted at every read edge, o_empty stays 0 until the last word is read, and o_rd_data steps through consecutive words in write order. *(when: back-to-back read burst from first to last accepted read)* | 10.6.5:s13, 10.6.5:s23 (p714) |
| AF-10.6.5-04 | MUST | slave | scenario | A word is accepted at every write edge during the burst and o_full stays 0 for the whole burst. *(when: back-to-back write burst with equal clocks and i_wr_en = 1)* | 10.6.5:s21 (p726) |
| AF-10.6.5-05 | MUST | system | scenario | The number of words in the FIFO stays at 4 (write pointer minus read pointer counted at read edges) in steady state. *(when: after start-up delay with equal clocks, until writes stop)* | 10.6.5:s26 (p728) |
| AF-10.6.5-06 | MUST | slave | assertion | Both Gray pointers change by one bit at every edge, and pointer wrap from 15 to 0 with storage address wrap from 7 to 0 has no effect on flow. | 10.6.5:s28 (p729) |
| AF-10.6.5-07 | MUST_NOT | slave | assertion | No o_overflow or o_underflow pulse occurs during the burst. *(when: during the back-to-back burst)* | 10.6.5:s30 (p730) |
| AF-10.6.5-08 | MUST | slave | scenario | With a slower read clock the FIFO fills and o_full stops the producer; with a faster read clock o_empty stops the consumer. *(when: unequal clock frequencies)* | 10.6.5:s33 (p731) |

## 10.6.6 Reproduction

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-10.6.6-01 | MUST | any | none | The tool bin and lib directories of the suite shall both be on PATH. *(when: reproducing waveforms)* | 10.6.6:s2 (p735) |

## 10.7 Software reset

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-10.7-01 | MUST | slave | scenario | The software reset returns the FIFO to the empty state without a hardware reset. *(when: software reset)* | 10.7:s1 (p748) |

## 10.7.1 Principle

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-10.7.1-01 | MUST | slave | assertion | Writes are blocked from the cycle in which i_rst_n_sw = 0, combinationally with zero latency. *(when: from the cycle in which i_rst_n_sw = 0)* | 10.7.1:s2, 10.7.2:s3 (p752) |
| AF-10.7.1-02 | MUST | slave | scenario | The write reset FSM raises req_wr at the next write edge, and it crosses to the read domain. *(when: i_rst_n_sw = 0)* | 10.7.1:s3, 10.7.3:s2 (p752) |
| AF-10.7.1-03 | MUST | slave | assertion | When the synchronized request is 1, reads are blocked (rd_blk) and o_empty = 1. *(when: synchronized request is 1)* | 10.7.1:s5, 10.7.2:s4, 10.7.2:s7 (p753) |
| AF-10.7.1-04 | MUST | slave | scenario | The read reset FSM resets the read pointer to 0 and then raises ack_rd, which crosses to the write domain. *(when: read FSM sees the request)* | 10.7.1:s6, 10.7.3:s4 (p753) |
| AF-10.7.1-05 | MUST_NOT | slave | scenario | The write pointer is reset only after the acknowledge is seen, never before the read side has stopped using the old pointer. *(when: acknowledge not yet seen by write side)* | 10.7.1:s7, 10.7.1:s8, 10.7.3:s5 (p754) |
| AF-10.7.1-06 | MUST | slave | scenario | The write FSM holds, with writes blocked, until i_rst_n_sw = 1. *(when: after write pointer reset)* | 10.7.1:s9, 10.7.3:s6 (p754) |
| AF-10.7.1-07 | MUST | slave | scenario | The write side drops the request, the read side drops the acknowledge, and each side leaves reset only when its synchronized copy of the other pointer is 0. *(when: release)* | 10.7.1:s11, 10.7.3:s7, 10.7.3:s8, 10.7.3:s9 (p755) |
| AF-10.7.1-08 | MUST | slave | scenario | The read side leaves reset first; the write side leaves last, after the synchronized acknowledge is 0. *(when: release)* | 10.7.1:s12, 10.7.1:s13, 10.7.3:s8, 10.7.3:s9 (p755) |
| AF-10.7.1-09 | MUST | slave | scenario | Words in the FIFO are discarded, and the storage is not cleared. *(when: software reset)* | 10.7.1:s15, 10.7.1:s17 (p756) |
| AF-10.7.1-10 | MAY | slave | scenario | Such a read returns a valid pre-reset word, which is discarded anyway. *(when: read accepted between i_rst_n_sw assertion and request arrival in read domain)* | 10.7.1:s16 (p756) |

## 10.7.2 Reset FSMs and block conditions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-10.7.2-01 | MUST | slave | assertion | A write is accepted only when i_wr_en is 1, wr_blk is 0 and the normal full condition is false. | 10.7.2:s5 (p788) |
| AF-10.7.2-02 | MUST | slave | assertion | A read is accepted only when i_rd_en is 1, rd_blk is 0 and the normal empty condition is false. | 10.7.2:s6 (p789) |
| AF-10.7.2-03 | MUST | slave | assertion | o_full is 1 while wr_blk; otherwise it is the normal full condition. *(when: while wr_blk)* | 10.7.2:s8, 10.7.3:s2 (p791) |
| AF-10.7.2-04 | MUST | slave | assertion | o_full_thr and o_empty_thr take the values of an empty FIFO while blocked; otherwise normal. *(when: while wr_blk (write side) or rd_blk (read side))* | 10.7.2:s9 (p792) |
| AF-10.7.2-05 | MUST_NOT | slave | assertion | No o_overflow or o_underflow pulse is generated for an access blocked by the software reset. *(when: access blocked by software reset)* | 10.7.2:s10 (p793) |
| AF-10.7.2-06 | MUST | slave | assertion | o_sw_rst_busy is set when the write FSM leaves RUN and cleared on return to RUN, equal to write FSM not in RUN at every clock edge. | 10.7.2:s11, 10.7.3:s2, 10.7.3:s9 (p794) |
| AF-10.7.2-07 | MUST | slave | scenario | The pointers are reset synchronously by the FSMs. *(when: software reset)* | 10.7.2:s12 (p796) |
| AF-10.7.2-08 | MUST | slave | scenario | The FSM state registers are reset by the hardware resets i_rst_n_wr and i_rst_n_rd. | 10.7.2:s13 (p796) |

## 10.7.3 Behavior per phase and the flush check

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-10.7.3-01 | MUST_NOT | slave | scenario | The read side must not be released until the synchronized write pointer is 0, so no nonexistent word is read; likewise for the write side and full flag. *(when: synchronized write pointer still old non-zero)* | 10.7.3:s12, 10.7.3:s14 (p836) |

## 10.7.4 Waveforms

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-10.7.4-01 | MUST | system | assertion | Write interface inputs i_wr_en, i_wr_data and the software reset i_rst_n_sw change only at a rising edge of i_clk_wr. | 10.7.4:s11 (p849) |
| AF-10.7.4-02 | MUST | system | assertion | Read interface input i_rd_en changes only at a rising edge of i_clk_rd. | 10.7.4:s11 (p849) |
| AF-10.7.4-03 | MUST | system | assertion | Hardware resets are asserted and released at a rising edge of their own clock. | 10.7.4:s11 (p849) |
| AF-10.7.4-04 | MUST | slave | assertion | Writes are blocked with zero latency: i_wr_en is not accepted, o_full = 1 and o_full_thr takes the empty-FIFO value 0. *(when: In the cycle in which i_rst_n_sw falls to 0)* | 10.7.4:s24, 10.7.4:s40 (p878) |
| AF-10.7.4-05 | MUST | slave | assertion | o_sw_rst_busy is 1 from the write FSM leaving RUN until it returns to RUN. *(when: From the write FSM leaving RUN (event 2) until the write FSM returns to RUN (event 13))* | 10.7.4:s25, 10.7.4:s40 (p879) |
| AF-10.7.4-06 | MUST | slave | assertion | Writes stay blocked throughout the sequence, including after i_rst_n_sw is released; the write pointer does not move and storage is not written. *(when: During the software reset sequence until the write release)* | 10.7.4:s25, 10.7.4:s31, 10.7.4:s40 (p879) |
| AF-10.7.4-07 | MUST | slave | assertion | Reads are blocked: i_rd_en is not accepted, o_empty = 1 and o_empty_thr = 1 in the same cycle. *(when: When the reset request becomes visible in the read domain)* | 10.7.4:s26, 10.7.4:s43 (p880) |
| AF-10.7.4-08 | MUST | slave | scenario | Reads accepted before the request reaches the read domain are normal reads returning valid pre-reset words. *(when: Before the request is visible in the read domain)* | 10.7.4:s26, 10.7.4:s42 (p880) |
| AF-10.7.4-09 | MUST | slave | assertion | The read pointer is reset before ack_rd rises. *(when: During the software reset handshake)* | 10.7.4:s27, 10.7.4:s28, 10.7.4:s45 (p881) |
| AF-10.7.4-10 | MUST | slave | assertion | The write pointer is reset only after the acknowledge is seen in the write domain. *(when: During the software reset handshake)* | 10.7.4:s29, 10.7.4:s30, 10.7.4:s45 (p883) |
| AF-10.7.4-11 | MUST | slave | scenario | The write FSM waits in HOLD for i_rst_n_sw = 1, and passes HOLD without waiting if the input is already 1. *(when: After the write pointer is reset)* | 10.7.4:s30, 10.7.4:s61, 10.7.4:s68 (p884) |
| AF-10.7.4-12 | MUST | slave | scenario | The write FSM drops the request req_wr to 0 after release of i_rst_n_sw. *(when: After i_rst_n_sw is released)* | 10.7.4:s31, 10.7.4:s32 (p885) |
| AF-10.7.4-13 | MUST | slave | assertion | The read side is released first (ack_rd = 0, flags live, o_empty = 1) and the write side last, because write release needs ack_rd = 0. *(when: At release)* | 10.7.4:s34, 10.7.4:s36, 10.7.4:s47 (p888) |
| AF-10.7.4-14 | MUST | slave | assertion | Writes are unblocked, o_full = 0, o_full_thr is normal and o_sw_rst_busy = 0. *(when: When the write FSM returns to RUN)* | 10.7.4:s36 (p890) |
| AF-10.7.4-15 | MUST | slave | scenario | The first write after the reset is accepted; o_empty and o_empty_thr fall only after the write pointer has crossed to the read domain. *(when: After the sequence)* | 10.7.4:s37, 10.7.4:s38, 10.7.4:s50, 10.7.4:s51 (p891) |
| AF-10.7.4-16 | MUST_NOT | slave | assertion | o_overflow does not pulse for a blocked write access. *(when: While writes are blocked by the software reset)* | 10.7.4:s40, 10.7.4:s56, 10.7.4:s67 (p896) |
| AF-10.7.4-17 | MUST | slave | scenario | A read request on an empty FIFO after the read release is not blocked and o_underflow pulses once. *(when: After read release with empty FIFO and i_rd_en = 1)* | 10.7.4:s48, 10.7.4:s49 (p900) |
| AF-10.7.4-18 | MUST | slave | assertion | o_overflow pulses, registered one cycle after the rejected write request. *(when: FIFO full, no reset, and producer keeps writing)* | 10.7.4:s55 (p911) |
| AF-10.7.4-19 | MUST | slave | scenario | The write FSM latches the request at the first write edge, so a one-cycle low pulse on i_rst_n_sw completes the full sequence. *(when: i_rst_n_sw low for only one write-clock cycle)* | 10.7.4:s56, 10.7.4:s57, 10.7.4:s58, 10.7.4:s66 (p912) |
| AF-10.7.4-20 | MUST | slave | assertion | o_full stays 1 during the whole reset and falls at the write release; o_full_thr follows the empty-FIFO value while blocked. *(when: During the whole software reset on a full FIFO)* | 10.7.4:s56, 10.7.4:s67 (p912) |
| AF-10.7.4-21 | MUST | slave | assertion | Writes are blocked whenever i_rst_n_sw is 0, including in REL and the cycle reaching RUN; no write is accepted between sequences. *(when: i_rst_n_sw is 0, including when the write FSM is in REL or reaches RUN)* | 10.7.4:s75, 10.7.4:s77, 10.7.4:s82 (p936) |
| AF-10.7.4-22 | MUST | slave | scenario | A second sequence starts at once after the first and completes the same way; o_sw_rst_busy falls for one write-clock cycle between them while o_full stays 1. *(when: i_rst_n_sw asserted again while write FSM is in REL)* | 10.7.4:s78, 10.7.4:s83 (p939) |
| AF-10.7.4-23 | MUST | master | scenario | The testbench keeps traffic idle until both domains are out of reset. *(when: During hardware reset until both domains are out of reset)* | 10.7.4:s86, 10.7.4:s95 (p946) |
| AF-10.7.4-24 | MUST | slave | scenario | Both FSMs, both pointers and both request and acknowledge synchronizers go to reset values at once, whatever the handshake state (hardware reset priority). *(when: Hardware reset asserted during the software reset sequence)* | 10.7.4:s92, 10.7.4:s97 (p958) |
| AF-10.7.4-25 | MUST | slave | scenario | After release the FIFO is empty (o_empty = 1, o_full = 0, pointers 0, FSMs in RUN) and works normally. *(when: After hardware reset release)* | 10.7.4:s93, 10.7.4:s94, 10.7.4:s98 (p959) |

## 10.7.5 Corner cases

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-10.7.5-01 | MUST | system | scenario | A one-cycle low pulse on i_rst_n_sw must be captured by the write FSM at the first write edge where it is 0, and the reset sequence must complete. *(when: i_rst_n_sw is a one-cycle low pulse)* | 10.7.5:s1 (p970) |
| AF-10.7.5-02 | MUST | system | scenario | While i_rst_n_sw stays low, the write FSM waits in HOLD and writes stay blocked, while the read side is released. *(when: i_rst_n_sw stays low for a long time)* | 10.7.5:s2 (p971) |
| AF-10.7.5-03 | MUST | system | scenario | Writes stay blocked and a new sequence starts when the FSM is back in RUN; o_sw_rst_busy falls for one cycle between the two sequences. *(when: i_rst_n_sw asserted again while write FSM is in REL)* | 10.7.5:s3 (p972) |
| AF-10.7.5-04 | MUST | system | scenario | The read is accepted as a normal read of pre-reset data, and the word is discarded by the reset. *(when: A read occurs between the assertion of i_rst_n_sw and the arrival of the request at the read side)* | 10.7.5:s4 (p973) |
| AF-10.7.5-05 | MUST | system | both | The write must be rejected because the write block is combinational from i_rst_n_sw. *(when: A write occurs in the same edge in which i_rst_n_sw falls)* | 10.7.5:s5 (p974) |
| AF-10.7.5-06 | MUST | system | scenario | The access must be rejected without an error pulse; a read of the empty FIFO right after the read release gives a normal underflow pulse. *(when: Read or write attempted during the software reset)* | 10.7.5:s6 (p975) |
| AF-10.7.5-07 | MUST | system | scenario | Storage content is not cleared by the software reset; o_rd_data shows the word at address 0 while the FIFO is empty. *(when: Software reset, FIFO empty)* | 10.7.5:s7 (p976) |
| AF-10.7.5-08 | MUST | system | scenario | Hardware reset has priority over the software reset; a reset of both domains gives a clean restart. *(when: Hardware reset occurs during the software reset)* | 10.7.5:s8 (p977) |
| AF-10.7.5-09 | MUST | system | scenario | The handshake waits until the clock runs again. *(when: A clock stops during the software reset)* | 10.7.5:s9 (p978) |
| AF-10.7.5-10 | MUST | system | scenario | The four-phase handshake is level based so longer delay only lengthens the sequence, and the multi-bit pointers are protected by the flush check. *(when: Extra latency on crossings)* | 10.7.5:s10 (p979) |
| AF-10.7.5-11 | MUST | system | both | Threshold flags show empty-FIFO values: o_full_thr = 0 for i_full_thr > 0 and o_empty_thr = 1. *(when: During the software reset)* | 10.7.5:s11 (p980) |

## 10.7.6 Evidence from the prototype and reproduction

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-10.7.6-01 | MUST | system | assertion | o_sw_rst_busy equals 'write FSM not in RUN' at every write-clock edge. *(when: Every write-clock edge)* | 10.7.6:s7 (p1000) |
| AF-10.7.6-02 | MUST_NOT | system | assertion | No write is accepted while wr_blk is active. *(when: wr_blk is active)* | 10.7.6:s7 (p1000) |
| AF-10.7.6-03 | MUST_NOT | system | assertion | No read is accepted while rd_blk is active. *(when: rd_blk is active)* | 10.7.6:s7 (p1000) |
| AF-10.7.6-04 | MUST | system | assertion | o_full is 1 and o_full_thr has the value of an empty FIFO while the write side is blocked. *(when: Write side blocked)* | 10.7.6:s7 (p1000) |
| AF-10.7.6-05 | MUST | system | assertion | o_empty is 1 and o_empty_thr is 1 while the read side is blocked. *(when: Read side blocked)* | 10.7.6:s7 (p1000) |
| AF-10.7.6-06 | MUST | system | scenario | No read returns a word that was never written, and data of every accepted read equals the written word. | 10.7.6:s7 (p1000) |
| AF-10.7.6-07 | MUST | system | assertion | At each release the own pointer and the synchronized pointer of the other side are 0. *(when: At each release of a side)* | 10.7.6:s7 (p1000) |
| AF-10.7.6-08 | MUST | system | both | The read release is before the write release and after the request; o_empty = 1 while both pointers are 0 after the read release. *(when: After the read release)* | 10.7.6:s7 (p1000) |
| AF-10.7.6-09 | MUST | system | assertion | Both FSMs are in RUN, both pointers are 0, o_empty = 1 and o_full = 0. *(when: After a hardware reset)* | 10.7.6:s7 (p1000) |
| AF-10.7.6-10 | MUST_NOT | system | scenario | The reset sequence must not deadlock; a timeout must detect a deadlock. *(when: Software reset sequence)* | 10.7.6:s7 (p1000) |

## 10.7.7 o_sw_rst_busy in detail

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-10.7.7-01 | MUST | system | assertion | o_sw_rst_busy is driven directly by flip-flop reg_sw_rst_busy, changes only at a rising edge of i_clk_wr and never glitches. | 10.7.7:s2 (p1006) |
| AF-10.7.7-02 | MUST | system | both | o_sw_rst_busy is 0 in RUN and 1 in REQ, PTR, HOLD and REL; FSM follows RUN, REQ, PTR, HOLD, REL, RUN with stated entry conditions and req_wr set in REQ. *(when: Write FSM states RUN, REQ, PTR, HOLD, REL)* | 10.7.7:s3, 10.7.7:s4, 10.7.7:s5, 10.7.7:s6, 10.7.7:s7, 10.7.7:s8, 10.7.7:s9 (p1006) |
| AF-10.7.7-03 | MUST | system | assertion | wr_blk follows i_rst_n_sw in the same cycle; o_sw_rst_busy rises at the first write-clock edge after i_rst_n_sw falls. *(when: i_rst_n_sw falls)* | 10.7.7:s11 (p1021) |
| AF-10.7.7-04 | MUST | system | assertion | o_sw_rst_busy rises at the same edge as req_wr. | 10.7.7:s12 (p1022) |
| AF-10.7.7-05 | MUST | system | assertion | o_sw_rst_busy stays 1 when i_rst_n_sw returns to 1 (HOLD, REL). *(when: After o_sw_rst_busy has risen)* | 10.7.7:s13 (p1023) |
| AF-10.7.7-06 | MUST | system | both | o_sw_rst_busy does not follow the read FSM; it falls only when the write side is released, after the read side. | 10.7.7:s14 (p1024) |
| AF-10.7.7-07 | MUST | system | assertion | o_sw_rst_busy, wr_blk and o_full fall at the same edge where the write FSM returns to RUN. *(when: i_rst_n_sw = 1)* | 10.7.7:s15 (p1025) |
| AF-10.7.7-08 | MUST | system | assertion | wr_blk equals o_sw_rst_busy OR (i_rst_n_sw = 0). *(when: Every cycle)* | 10.7.7:s16 (p1026) |
| AF-10.7.7-09 | MUST | system | assertion | A hardware reset of the write domain clears o_sw_rst_busy asynchronously. *(when: Hardware reset of the write domain, any sequence state)* | 10.7.7:s17 (p1027) |
| AF-10.7.7-10 | MUST | system | assertion | o_sw_rst_busy falls for exactly one write-clock cycle between the two sequences, and writes stay blocked during the gap. *(when: i_rst_n_sw = 0 seen again in REL)* | 10.7.7:s18 (p1028) |
| AF-10.7.7-11 | MUST | system | assertion | o_sw_rst_busy falls at the edge where the write FSM returns to RUN, together with wr_blk and o_full. *(when: Write FSM returns to RUN)* | 10.7.7:s25 (p1041) |
| AF-10.7.7-12 | SHOULD | any | none | A read-domain consumer needing o_sw_rst_busy shall synchronize it itself, or use o_empty, since the IP has no synchronizer for it. *(when: Consumer in the read domain needs o_sw_rst_busy)* | 10.7.7:s45 (p1075) |

## 11 Register and programming model

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-11-01 | MUST_NOT | system | none | The IP has no software-visible register and no CSR workbook; no CSR is exposed by the IP. | 11:s2 (p1079) |
| AF-11-02 | MUST | system | both | Overflow and underflow indications are 1-cycle pulses, with no sticky status register retaining them. *(when: When overflow or underflow is flagged)* | 11:s3 (p1079) |

## 11.2 Software sequences

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-11.2-01 | SHOULD | system | none | The owner of the i_rst_n_sw control register stops the producer before the reset if the producer should not lose words. *(when: Software reset sequence, if the producer should not lose words)* | 11.2:s1 (p1091) |
| AF-11.2-02 | MUST | system | scenario | The owner of the control register drives i_rst_n_sw to 0 for at least one write-clock cycle; it may be held longer. *(when: Software reset sequence)* | 11.2:s1 (p1091) |
| AF-11.2-03 | MUST | system | scenario | The owner of the control register drives i_rst_n_sw back to 1 after the reset has started. *(when: After the reset has started)* | 11.2:s1 (p1091) |
| AF-11.2-04 | MUST | system | both | The FIFO is usable again on both sides when o_sw_rst_busy is 0 and i_rst_n_sw is 1. *(when: o_sw_rst_busy = 0 and i_rst_n_sw = 1)* | 11.2:s2 (p1091) |
| AF-11.2-05 | MUST | system | both | The read side is always released before the write side. *(when: During software reset release)* | 11.2:s2 (p1091) |
| AF-11.2-06 | MUST | system | both | o_sw_rst_busy falls when the write side is released. *(when: During software reset release)* | 11.2:s2 (p1091) |
| AF-11.2-07 | MUST_NOT | system | scenario | Software must not use o_sw_rst_busy = 0 alone as the usable indication while i_rst_n_sw is held at 0, since it is 0 for one write-clock cycle after i_rst_n_sw falls and between sequences while writes are blocked. *(when: While i_rst_n_sw is held at 0)* | 11.2:s3 (p1091) |
| AF-11.2-08 | MUST | system | scenario | The words in the FIFO at the reset are lost. *(when: At software reset)* | 11.2:s4 (p1091) |

## 12 Error handling and recovery

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-12-01 | MUST | slave | assertion | The FIFO must pulse o_overflow for one cycle, registered, in the cycle after a rejected write request when i_wr_en = 1 while full. *(when: i_wr_en = 1 while the FIFO is full (write domain))* | 12:s1 (p1097) |
| AF-12-02 | MUST | slave | assertion | The write must be dropped: storage and write pointer remain unchanged. *(when: i_wr_en = 1 while full)* | 12:s1 (p1097) |
| AF-12-03 | MUST | slave | assertion | o_overflow must self-clear after one cycle and must be cleared by i_rst_n_wr. *(when: o_overflow is asserted)* | 12:s1 (p1097) |
| AF-12-04 | MUST | slave | assertion | The FIFO must pulse o_underflow for one cycle, registered, in the cycle after a rejected read request when i_rd_en = 1 while empty. *(when: i_rd_en = 1 while the FIFO is empty (read domain))* | 12:s2 (p1098) |
| AF-12-05 | MUST | slave | assertion | The read pointer must remain unchanged and o_rd_data must still show the word at the read pointer. *(when: i_rd_en = 1 while empty)* | 12:s2 (p1098) |
| AF-12-06 | MUST | slave | assertion | o_underflow must self-clear after one cycle and must be cleared by i_rst_n_rd. *(when: o_underflow is asserted)* | 12:s2 (p1098) |
| AF-12-07 | MUST | system | none | The integrator must reset both domains; reset asserted in one domain only leaves inconsistent FIFO state that the IP does not detect. *(when: After the FIFO was used)* | 12:s3 (p1099) |
| AF-12-08 | MUST_NOT | system | none | The IP does not detect illegal parameters and behavior is undefined; the configuration must be fixed, so illegal parameters must not be used. *(when: Illegal parameter configuration)* | 12:s4 (p1100) |
| AF-12-09 | MUST | slave | both | The access must not be accepted and no o_overflow or o_underflow pulse must be generated. *(when: i_wr_en or i_rd_en = 1 while blocked by a software reset)* | 12:s5 (p1101) |
| AF-12-10 | MUST | slave | scenario | The new i_rst_n_sw request must be ignored until the write FSM is back in RUN; a new sequence then starts if i_rst_n_sw is still 0. *(when: i_rst_n_sw = 0 while a software reset is already in progress)* | 12:s6 (p1102) |
| AF-12-11 | MUST | slave | scenario | The o_overflow and o_underflow flags belong to different domains and must not interact. | 12:s7 (p1104) |
| AF-12-12 | MUST_NOT | slave | scenario | A simultaneous write and read on the same cycle must not produce both o_overflow and o_underflow for the same event. *(when: Simultaneous write and read in the same cycle)* | 12:s8 (p1104) |
| AF-12-13 | MUST | system | none | No retry or drain is provided by the FIFO; the producer or consumer must react to the o_overflow and o_underflow flags. | 12:s9 (p1104) |

## 13 Performance, power, and area

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-13-01 | MUST | system | scenario | Flag latency across the crossing must be S destination clock edges when flags are combinational from the synchronized pointer, and up to S+2 edges with the metastability model. *(when: Flag latency across the clock-domain crossing is measured per Section 10.3)* | 13:s6 (p1115) |
| AF-13-02 | MUST_NOT | any | none | Timing closure must not be claimed from RTL synthesis alone. *(when: When assessing timing closure)* | 13:s8 (p1118) |

## 14.1 Required coding baseline

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-14.1-01 | MUST | system | none | The RTL shall comply with REF-003, which is the mandatory RTL authority. | 14.1:s1 (p1124) |
| AF-14.1-02 | MUST | system | none | Synchronizer flip-flops and technology cells shall exist only in m_vlsit_afifo_cell_sync. | 14.1:s4 (p1128) |
| AF-14.1-03 | MUST | system | none | m_vlsit_afifo_sync shall contain only instances of m_vlsit_afifo_cell_sync. | 14.1:s4 (p1128) |
| AF-14.1-04 | MUST | system | none | The memory macro shall exist only in m_vlsit_afifo_ram_macro. | 14.1:s5 (p1128) |
| AF-14.1-05 | MUST | system | none | These flows shall define the macro VLSIT_SYNTHESIS. *(when: In synthesis, lint, CDC, formal and equivalence flows)* | 14.1:s8 (p1129) |
| AF-14.1-06 | MUST | system | scenario | m_vlsit_afifo_cell_sync shall instantiate the library cells when VLSIT_SYNTHESIS is defined, and contain the behavioral simulation model with metastability model when it is not. *(when: VLSIT_SYNTHESIS defined)* | 14.1:s9 (p1129) |
| AF-14.1-07 | MUST | system | none | VLSIT_SYNTHESIS shall select branches only in m_vlsit_afifo_cell_sync; m_vlsit_afifo_ram_macro has no branch and always instantiates VLSIT_CELL_SRAM_1W1R. | 14.1:s9 (p1129) |
| AF-14.1-08 | MUST | system | none | The flag, Gray register and pointer registers shall be one-process-per-state elements with separate next-state logic. | 14.1:s10 (p1130) |
| AF-14.1-09 | MUST | system | none | The software reset FSMs shall be one-process-per-state with separate next-state logic, REF-003 FSM naming, and reside in m_vlsit_afifo_wr and m_vlsit_afifo_rd. | 14.1:s11, 14.1:s12 (p1131) |
| AF-14.1-10 | MUST | system | none | Request and acknowledge synchronizers shall be m_vlsit_afifo_sync instances with PARA_AFIFO_SYNC_W = 1. | 14.1:s13 (p1131) |
| AF-14.1-11 | MUST | system | scenario | o_sw_rst_busy shall be the output of its own flip-flop reg_sw_rst_busy, not a decode of the FSM state. | 14.1:s13 (p1131) |
| AF-14.1-12 | MUST | system | none | Names in m_vlsit_afifo_* modules shall use REF-003 NAM-08 abbreviations and be at most 30 characters. | 14.1:s14 (p1132) |

## 14.2 RTL hierarchy

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-14.2-01 | MUST | system | none | Library wrappers and example cells shall be in common_rtl/000_Common, and each folder shall have its own filelist.f. | 14.2:s10, 14.2:s11 (p1146) |
| AF-14.2-02 | MUST | system | none | Instance names shall be u_ followed by the module name with m_ removed; names over 30 characters shall shorten the function part with NAM-08. | 14.2:s16, 14.2:s17 (p1156) |
| AF-14.2-03 | MUST | system | none | The top shall have no logic; state is owned by m_vlsit_afifo_wr and m_vlsit_afifo_rd. | 14.2:s18 (p1156) |

## 14.4 Technology synchronizer cell (example models)

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-14.4-01 | MUST | system | none | m_vlsit_afifo_sync shall instantiate PARA_AFIFO_SYNC_W cell wrappers, one per bit, with PARA_AFIFO_CELL_TYPE and the bit's reset flavour, in both VLSIT_SYNTHESIS branches, and nothing else. | 14.4:s3 (p1173) |
| AF-14.4-02 | MUST | system | assertion | Input bit i_data[i] shall connect to i_d and o_q shall be o_data[i]. | 14.4:s4 (p1173) |
| AF-14.4-03 | MUST | system | scenario | Option 0 is a bypass (o_q = i_d, 0 stages); options 1 and 2 give 2 stages, option 3 gives 3, option 4 gives 4, with metastability-model chains in simulation. *(when: per PARA_AFIFO_CELL_TYPE)* | 14.4:s10, 14.4:s11, 14.4:s12, 14.4:s13, 14.4:s14, 14.4:s18 (p1179) |
| AF-14.4-04 | MUST_NOT | system | none | PARA_AFIFO_CELL_TYPE above 4 shall not be used; the wrapper gives the option 4 cell and behavior is undefined. | 14.4:s15 (p1185) |
| AF-14.4-05 | MUST | system | scenario | Every flop of a synchronizer model shall reset to the reset value bit. | 14.4:s16 (p1185) |
| AF-14.4-06 | MUST_NOT | system | none | Option 0 shall not be used for the pointer crossings of this IP because it breaks the read margin of at least 2 destination edges. *(when: pointer crossings)* | 14.4:s17, 14.4:s21, 14.4:s22 (p1187) |
| AF-14.4-07 | MUST | system | scenario | The latencies of Section 10.3 and read margin of Section 10.4 shall hold for options 1 to 4. *(when: options 1 to 4)* | 14.4:s20 (p1187) |
| AF-14.4-08 | MUST | system | none | The synthesis branch shall instantiate the cells of 000_Common/rtl_cells named u_dont_touch_. *(when: VLSIT_SYNTHESIS defined)* | 14.4:s27 (p1227) |
| AF-14.4-09 | MUST | system | scenario | The simulation branch shall not use the example cells and shall contain the metastability model with random extra latency of REQ-VER-001. *(when: VLSIT_SYNTHESIS not defined)* | 14.4:s28 (p1227) |
| AF-14.4-10 | MUST | system | scenario | The synthesis branch shall be verified with VLSIT_SYNTHESIS defined per option, and the simulation branch alone per option (latency 0, 2, 2, 3, 4 and reset value). | 14.4:s29, 14.4:s30 (p1227) |

## 15.1 Scope and strategy

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-15.1-01 | MUST | system | scenario | Seeds must be logged for every random run, and every failing seed shall be reproducible. *(when: for every random run)* | 15.1:s3 (p1233) |

## 15.2 Requirement-based test plan

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-15.2-01 | MUST | system | both | After reset release, empty = 1, full = 0, flags are clear and pointers are 0. *(when: after reset of both domains is released)* | 15.2:s1 (p1239) |
| AF-15.2-02 | MUST | system | both | o_rd_data must equal the head word before every read; data returns the same, in the same order, show-ahead. *(when: writing N words then reading N words)* | 15.2:s2 (p1240) |
| AF-15.2-03 | MUST | system | both | When full = 1 and writing continues, overflow is raised and no data or pointer changes. *(when: writing while the FIFO is full)* | 15.2:s3 (p1241) |
| AF-15.2-04 | MUST | system | both | When empty = 1 and reading continues, underflow is raised and the pointer is unchanged. *(when: reading while the FIFO is empty)* | 15.2:s4 (p1242) |
| AF-15.2-05 | MUST | system | scenario | Threshold flags must behave per REQ-FUNC-010 for several i_full_thr and i_empty_thr values. *(when: filling and draining across the threshold)* | 15.2:s5 (p1243) |
| AF-15.2-06 | MUST | system | scenario | With random clock ratios (write faster, read faster, equal, drift) there must be no data error and no flag error. *(when: random clock ratios with phase drift)* | 15.2:s6 (p1244) |
| AF-15.2-07 | MUST | system | scenario | Flag latency must equal S destination clock edges. *(when: S = 2, 3, 4)* | 15.2:s7 (p1245) |
| AF-15.2-08 | MUST | system | scenario | Each bit output changes at edge S, S+1 or S+2; there is no data error and flags are never optimistic. *(when: metastability model enabled)* | 15.2:s8 (p1246) |
| AF-15.2-09 | MUST | system | scenario | FIFO behaves as the RTL branch; wrapper alone for options 0 to 4 has latency 0, 2, 2, 3, 4 and the listed reset value. *(when: CFG-CELL, options 1 to 4 in both VLSIT_SYNTHESIS branches and both reset flavours)* | 15.2:s9 (p1247) |
| AF-15.2-10 | MUST | system | scenario | Behavior must be the same as the RTL array. *(when: macro configuration with VLSIT_CELL_SRAM_1W1R in both branches)* | 15.2:s10 (p1248) |
| AF-15.2-11 | MUST | system | none | The testbench configuration list must use only legal values. *(when: testbench configuration list review)* | 15.2:s11 (p1249) |
| AF-15.2-12 | MUST | system | assertion | Gray pointers change only one bit per cycle. | 15.2:s12 (p1250) |
| AF-15.2-13 | MUST | system | scenario | Same-cycle write and read, and pointer wrap-around, must cause no error. *(when: simultaneous write and read, and pointer wrap-around)* | 15.2:s13 (p1251) |
| AF-15.2-14 | MUST | system | scenario | The FIFO must restart cleanly. *(when: reset in mid operation of both domains together)* | 15.2:s14 (p1252) |
| AF-15.2-15 | MUST | system | none | Top instantiates only wr, rd and mem; mem is not inside wr or rd. | 15.2:s15 (p1253) |
| AF-15.2-16 | MUST | system | none | Design follows REF-003 lint rules with no latch, no combinational loop and no tab. *(when: lint)* | 15.2:s16 (p1254) |
| AF-15.2-17 | MUST | system | none | Only approved crossings exist, with no logic before or between synchronizer stages. *(when: CDC analysis)* | 15.2:s17 (p1255) |
| AF-15.2-18 | MUST | system | none | Constraints are applied and exceptions are consistent. *(when: STA with delivered SDC)* | 15.2:s18 (p1256) |
| AF-15.2-19 | MUST | system | scenario | With the macro the synthesizable branch runs and passes the full regression; without it the model runs. *(when: building m_vlsit_afifo_sync, m_vlsit_afifo_cell_sync, m_vlsit_afifo_ram_macro with and without VLSIT_SYNTHESIS)* | 15.2:s19 (p1257) |
| AF-15.2-20 | MUST | system | scenario | Handshake order is respected; after release pointers are 0, empty = 1, full = 0, and read is released before write. *(when: software reset with FIFO empty, partial and full)* | 15.2:s20 (p1258) |
| AF-15.2-21 | MUST | system | both | No access is accepted while blocked, no data error and no deadlock occur. *(when: software reset under random traffic, i_rst_n_sw width 1 to 12 cycles)* | 15.2:s21 (p1259) |
| AF-15.2-22 | MUST | system | both | The sequence completes and the flush check is never violated. *(when: software reset with metastability model and several seeds)* | 15.2:s22 (p1260) |
| AF-15.2-23 | MUST | system | scenario | Behavior in TEST-002 to TEST-004 must be the same as after a hardware reset. *(when: after a software reset)* | 15.2:s23 (p1261) |
| AF-15.2-24 | MUST | system | scenario | Behavior must follow DEC-031 and DEC-032. *(when: i_rst_n_sw re-asserted in REL, or hardware reset of one or both domains during sequence)* | 15.2:s24 (p1262) |
| AF-15.2-25 | MUST | system | none | Crossings are 1-bit synchronized levels with no logic before the first stage. *(when: CDC analysis of CDC-005 and CDC-006)* | 15.2:s25 (p1263) |

## 15.3 Assertions and coverage

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-15.3-01 | MUST | system | none | Assertions are disabled during reset. *(when: during reset)* | 15.3:s2 (p1267) |
| AF-15.3-02 | MUST | system | assertion | Full and empty are never both 1. | 15.3:s3 (p1271) |
| AF-15.3-03 | MUST | system | assertion | A Gray pointer register changes at most one bit per cycle. | 15.3:s4 (p1272) |
| AF-15.3-04 | MUST | system | assertion | The write pointer and storage remain unchanged. *(when: write while full)* | 15.3:s5 (p1273) |
| AF-15.3-05 | MUST | system | both | The read returns the word written to that entry, with no scoreboard mismatch. *(when: read accepted by the read side)* | 15.3:s6 (p1274) |
| AF-15.3-06 | MUST_NOT | system | assertion | Full flag is never 0 when physically full; empty flag is never 0 when physically empty. | 15.3:s7 (p1275) |
| AF-15.3-07 | MUST | system | assertion | The read pointer remains unchanged. *(when: read while empty)* | 15.3:s8 (p1276) |
| AF-15.3-08 | MUST_NOT | system | assertion | No write is accepted while wr_blk = 1. *(when: wr_blk = 1)* | 15.3:s9 (p1277) |
| AF-15.3-09 | MUST_NOT | system | assertion | No read is accepted while rd_blk = 1. *(when: rd_blk = 1)* | 15.3:s10 (p1278) |
| AF-15.3-10 | MUST | system | assertion | ack_rd rises only when the read pointer is 0 and the read FSM is not in RUN. | 15.3:s11 (p1279) |
| AF-15.3-11 | MUST | system | assertion | req_wr falls only after the acknowledge was seen and i_rst_n_sw = 1; ack_rd falls only after the synchronized request is 0. | 15.3:s12 (p1280) |
| AF-15.3-12 | MUST | system | assertion | The read pointer and synchronized write pointer are 0. *(when: read FSM returns to RUN)* | 15.3:s13 (p1281) |
| AF-15.3-13 | MUST | system | assertion | The write pointer and synchronized read pointer are 0. *(when: write FSM returns to RUN)* | 15.3:s14 (p1282) |
| AF-15.3-14 | MUST | system | assertion | The read FSM returns to RUN before the write FSM. *(when: every software reset)* | 15.3:s15 (p1283) |
| AF-15.3-15 | MUST | system | assertion | Both FSMs return to RUN within a bounded number of cycles. *(when: i_rst_n_sw = 1 and both clocks running)* | 15.3:s16 (p1284) |
| AF-15.3-16 | MUST | system | assertion | o_sw_rst_busy equals (write FSM not in RUN) and is 0 after hardware reset. *(when: every write-clock edge)* | 15.3:s17 (p1285) |
| AF-15.3-17 | MUST | system | assertion | Write block equals o_sw_rst_busy OR (i_rst_n_sw = 0); o_sw_rst_busy rises only at RUN to REQ and falls only at REL to RUN. *(when: every cycle)* | 15.3:s18 (p1286) |
| AF-15.3-18 | MUST_NOT | system | none | Resetless storage is not checked for X until its entry has been written. *(when: until the entry has been written)* | 15.3:s26 (p1295) |
| AF-15.3-19 | MUST_NOT | system | assertion | A read is accepted only when empty = 0. *(when: empty = 1)* | 15.3:s27 (p1295) |

## 15.4 Formal, CDC, and RDC

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-15.4-01 | MUST | system | assertion | Formal proves one-bit change of Gray pointers, flags never optimistic, overflow/underflow leave state unchanged, no entry overwritten before read, and SVA-007 to SVA-016. *(when: formal model checking, depth 2, 4, 8)* | 15.4:s1 (p1301) |

## 16 DFT and testability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-16-01 | MUST_NOT | system | scenario | The IP must not provide any DFT port (i_dft_*), test-mode control, MBIST hook, or scan-specific wrapper. | 16:s2 (p1306) |
| AF-16-02 | MUST_NOT | system | scenario | The RTL must not contain any latch, combinational loop, internal tri-state, or clock gate, so SoC scan insertion remains possible. | 16:s3 (p1306) |

## 17.1 Timing constraints and budgets

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-17.1-01 | MUST | system | none | The IP owns the timing constraints of the crossings EXC-001..003, EXC-005 and EXC-006. | 17.1:s1 (p1312) |
| AF-17.1-02 | MUST | system | none | The SoC owns the clock definitions and I/O delays; the IP does not specify them. | 17.1:s2, 17.1:s4 (p1312) |
| AF-17.1-03 | MUST_NOT | system | none | The timing text describes required content only and must not be treated as executable constraints. | 17.1:s5 (p1312) |

## 17.1.1 Clock and analysis scenarios

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-17.1.1-01 | MUST | system | scenario | i_clk_wr and i_clk_rd are primary clocks, asynchronous to each other for functional paths except the listed exceptions, with no frequency or ratio restriction. | 17.1.1:s1, 17.1.1:s2 (p1318) |
| AF-17.1.1-02 | MUST_NOT | system | none | The IP requires no mode-dependent case analysis. | 17.1.1:s4 (p1321) |

## 17.1.3 Timing exception inventory

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-17.1.3-01 | MUST | system | none | EXC-001: set_max_delay -datapath_only from write Gray pointer registers to first synchronizer stage D pins in m_vlsit_afifo_rd must be 0.9 x i_clk_wr period. | 17.1.3:s1 (p1340) |
| AF-17.1.3-02 | MUST | system | none | EXC-002: set_max_delay -datapath_only from read Gray pointer registers to first synchronizer stage D pins in m_vlsit_afifo_wr must be 0.9 x i_clk_rd period. | 17.1.3:s2 (p1341) |
| AF-17.1.3-03 | MUST | system | none | EXC-003: set_max_delay -datapath_only from storage elements or macro output through the read path to storage output register D pins must be at most 1 x i_clk_rd period. | 17.1.3:s3 (p1342) |
| AF-17.1.3-04 | MUST | system | scenario | EXC-004: i_full_thr and i_empty_thr are set_false_path static configuration inputs, written once before use and not changed while the FIFO is in use. | 17.1.3:s4 (p1343) |
| AF-17.1.3-05 | MUST | system | none | EXC-005: set_max_delay -datapath_only from req_wr register to first stage D pin of the request synchronizer in m_vlsit_afifo_rd must be 0.9 x i_clk_wr period. | 17.1.3:s5 (p1344) |
| AF-17.1.3-06 | MUST | system | none | EXC-006: set_max_delay -datapath_only from ack_rd register to first stage D pin of the acknowledge synchronizer in m_vlsit_afifo_wr must be 0.9 x i_clk_rd period. | 17.1.3:s6 (p1345) |
| AF-17.1.3-07 | MUST_NOT | system | none | Do not use a whole-domain set_false_path or unqualified set_clock_groups -asynchronous for the two clocks, as it hides the crossings from bounded-delay checks. | 17.1.3:s7 (p1347) |
| AF-17.1.3-08 | MUST | system | none | The bounded-delay constraints and the CDC analysis shall cover the crossings separately. *(when: If set_clock_groups is the project policy)* | 17.1.3:s8 (p1347) |

## 17.2 Physical assumptions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-17.2-01 | MUST | system | none | Hard/memory macros and views apply only in the macro branch; real macro views are supplied at integration. | 17.2:s1 (p1362) |
| AF-17.2-02 | SHOULD | system | none | The synchronizer stages of one bit should be placed adjacent to each other. | 17.2:s2 (p1363) |
| AF-17.2-03 | MUST | system | none | dont_touch is applied to the synchronizer instances so the flow does not restructure them. | 17.2:s9 (p1371) |

## 18 Security, safety, and reliability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-18-01 | MUST_NOT | system | scenario | The storage must not be cleared by reset; no secure clearing or zeroization is provided. *(when: on reset)* | 18:s3 (p1379) |
| AF-18-02 | MUST | system | scenario | Diagnostics are limited to overflow and underflow flags; recovery is performed by the user logic or by reset. *(when: when an overflow or underflow occurs)* | 18:s7 (p1383) |
| AF-18-03 | MUST | system | scenario | The number of synchronizer stages S must be configurable as 2, 3 or 4, with a technology cell option. | 18:s8 (p1384) |

## 20.1 Assumptions and dependencies

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-20.1-01 | MUST | system | none | Both write-domain and read-domain resets are assumed already synchronized to their respective clocks externally; the IP contains no reset synchronizer. | 20.1:s1 (p1454) |
| AF-20.1-02 | MUST | system | none | The write and read clocks are assumed to be asynchronous to each other. | 20.1:s2 (p1455) |
| AF-20.1-03 | MUST | system | scenario | The pointer protocol keeps the read data stable, which the CDC waiver and EXC-003 rely on. *(when: When the pointer protocol of Section 10.4 is used)* | 20.1:s3 (p1456) |
| AF-20.1-04 | MUST | slave | scenario | o_rd_data shows the storage content at the read pointer while empty; the consumer ignores it when o_empty = 1. *(when: While o_empty = 1)* | 20.1:s7 (p1460) |
| AF-20.1-05 | MUST_NOT | system | assertion | No FIFO operation (write or read) starts before both write and read domains have left reset. *(when: Before both domains have left reset)* | 20.1:s8 (p1461) |
| AF-20.1-06 | MUST | system | scenario | Both clocks run during the whole software reset; if a clock stops, the handshake waits until it runs again, with no timeout. *(when: During the whole software reset)* | 20.1:s9 (p1462) |

## 20.2 Closed decisions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-20.2-01 | MUST | system | none | The metastability model is a simulation-only SystemVerilog model, not bound by the RTL rules, and must never be used for synthesis. | 20.2:s1 (p1468) |
| AF-20.2-02 | MUST_NOT | system | none | The RTL contains no elaboration check for parameter values; behavior with an illegal parameter value is undefined. | 20.2:s2 (p1469) |
| AF-20.2-03 | MUST | system | none | Defaults are 2 synchronizer stages, depth 8, data width 32; depth is a power of 2 with no upper limit, data width minimum 1 with no upper limit. | 20.2:s4 (p1471) |
| AF-20.2-04 | MUST | slave | assertion | o_rd_data must always show the word at the current read pointer (show-ahead read), including while empty; there is no o_rd_valid. *(when: always, including while empty)* | 20.2:s5 (p1472) |
| AF-20.2-05 | MUST | system | both | o_full_thr must be 1 when occupancy >= i_full_thr; all i_full_thr values are accepted with no legal-range restriction. | 20.2:s6 (p1473) |
| AF-20.2-06 | MUST | system | both | o_empty_thr must be 1 when occupancy <= i_empty_thr; all i_empty_thr values are accepted with no legal-range restriction. | 20.2:s6 (p1473) |
| AF-20.2-07 | MUST | master | none | The threshold inputs i_full_thr and i_empty_thr are static, written once before use. | 20.2:s6 (p1473) |
| AF-20.2-08 | MUST | system | assertion | o_overflow and o_underflow must be registered 1-cycle pulses appearing in the cycle after the rejected request. *(when: after a rejected write or read request)* | 20.2:s7, 20.2:s20 (p1474) |
| AF-20.2-09 | MUST | slave | assertion | An underflow read must not change the read pointer, and o_rd_data keeps showing the word at the read pointer. *(when: on an underflow read)* | 20.2:s7 (p1474) |
| AF-20.2-10 | MAY | any | scenario | The write and read domain resets (asynchronous assert, active low) need not be asserted at the same time, and clock frequencies and ratio are unrestricted. | 20.2:s9 (p1476) |
| AF-20.2-11 | MUST | system | scenario | Each synchronizer bit has its own reset value (vector). | 20.2:s10 (p1477) |
| AF-20.2-12 | MUST | system | scenario | The model randomizes each bit's latency independently as S-1, S or S+1 cycles after the first capturing edge; a new input change during the delay replaces the pending change and restarts the delay. *(when: simulation metastability model)* | 20.2:s12 (p1479) |
| AF-20.2-13 | MUST | system | scenario | The metastability model is controlled by plusargs for seed and enable. | 20.2:s12 (p1479) |
| AF-20.2-14 | MUST | system | none | The SRAM wrapper and model implement a generic one-write-port, one-read-port foundry-style interface. | 20.2:s13 (p1480) |
| AF-20.2-15 | MUST | system | none | The FIFO array is a separate module modelled as a one-write, one-read SRAM, and the top instantiates the write module, read module and array module. | 20.2:s14 (p1481) |
| AF-20.2-16 | MUST | system | assertion | The full, empty and threshold flags must be combinational from the synchronized pointers. | 20.2:s16 (p1483) |
| AF-20.2-17 | MUST | system | none | Timing exceptions: set_max_delay 0.9 x write clock period for the write pointer, 0.9 x read clock period for the read pointer, 1 x read clock period for the data path; static thresholds use a false path; no set_min_delay. | 20.2:s18 (p1485) |
| AF-20.2-18 | MUST | system | none | The macro VLSIT_SYNTHESIS selects branches only in m_vlsit_afifo_cell_sync: with the macro is the synthesizable model, without is the simulation model; simulation defines it for the synthesizable branch, synthesis and analysis flows define it. | 20.2:s21, 20.2:s22, 20.2:s43 (p1488) |
| AF-20.2-19 | MUST | system | assertion | Storage read is synchronous: the read module drives the next read pointer address, storage is read every read-clock cycle, o_rd_data is the storage output, with no memory read enable. | 20.2:s23 (p1490) |
| AF-20.2-20 | MUST | master | both | The software reset input i_rst_n_sw is active-low level (0 = reset requested), idle value 1, synchronous to i_clk_wr and sampled at the clock, not an asynchronous reset. | 20.2:s25 (p1492) |
| AF-20.2-21 | MAY | master | scenario | i_rst_n_sw may be low for one write-clock cycle or any longer time; the FSM latches the request and waits in HOLD while it is low. | 20.2:s26 (p1493) |
| AF-20.2-22 | MUST | system | none | o_sw_rst_busy must be driven directly by a flip-flop with no combinational logic on the output path. | 20.2:s26 (p1493) |
| AF-20.2-23 | MUST | system | assertion | o_full must be 1 while the write side is blocked by the software reset and return to normal full logic at write release. *(when: while the write side is blocked by software reset)* | 20.2:s27 (p1494) |
| AF-20.2-24 | MUST_NOT | system | assertion | A write or read blocked by the software reset must not raise an o_overflow or o_underflow pulse. *(when: write or read blocked by software reset)* | 20.2:s28 (p1495) |
| AF-20.2-25 | MUST | system | assertion | While blocked, o_full_thr and o_empty_thr must take the values of an empty FIFO. *(when: while blocked by software reset)* | 20.2:s29 (p1496) |
| AF-20.2-26 | MUST | system | assertion | The write block is combinational (zero latency) from i_rst_n_sw and the FSM state, adding a combinational path to write accept and memory write enable. | 20.2:s30 (p1497) |
| AF-20.2-27 | MUST | system | scenario | Hardware resets have priority over the software reset; a hardware reset of one domain only during the sequence is not repaired. *(when: hardware reset and software reset conflict)* | 20.2:s31 (p1498) |
| AF-20.2-28 | MUST | system | scenario | Writes stay blocked and a new sequence starts when the FSM is back in RUN. *(when: i_rst_n_sw asserted again while write FSM is in REL)* | 20.2:s32 (p1499) |
| AF-20.2-29 | MUST | system | none | The request and acknowledge crossings use set_max_delay of 0.9 x the source clock period. | 20.2:s33 (p1500) |
| AF-20.2-30 | MUST | system | both | A side is released only when the synchronized pointer of the other side is 0. *(when: software reset flush)* | 20.2:s34 (p1501) |
| AF-20.2-31 | MUST_NOT | system | scenario | The software reset must not clear the storage; only pointers and flags are reset. *(when: software reset)* | 20.2:s35 (p1502) |
| AF-20.2-32 | MUST | system | none | Both clocks run during the whole software reset; there is no timeout. *(when: during software reset)* | 20.2:s36 (p1503) |
| AF-20.2-33 | MUST | system | scenario | PARA_AFIFO_CELL_TYPE selects the cell: 0 bypass, 1 two D-FF cells, 2 one 2-FF cell, 3 one 3-FF cell, 4 one 4-FF cell; above 4 gives the 4-FF cell; default 2. | 20.2:s37, 20.2:s39 (p1504) |
| AF-20.2-34 | MUST_NOT | system | none | Option 0 (bypass) is not legal for the pointer crossings. *(when: pointer crossings)* | 20.2:s37 (p1504) |
| AF-20.2-35 | MUST | system | none | The metastability model lives only in the simulation branch of m_vlsit_afifo_cell_sync; m_vlsit_afifo_sync only instantiates one cell wrapper per bit, and other modules only instantiate m_vlsit_afifo_sync. | 20.2:s38, 20.2:s39 (p1505) |
| AF-20.2-36 | MUST | system | none | Instance names of cells and macros follow u_dont_touch_. | 20.2:s38 (p1505) |
| AF-20.2-37 | MUST | system | none | Example cell models are synthesizable RTL, one module per file in 000_Common/rtl_cells, with pins CK, RN or SN, D, Q, exempt from the naming rule; the SRAM model stays simulation-only per DEC-040. | 20.2:s40, 20.2:s42 (p1507) |
| AF-20.2-38 | MUST | system | scenario | VLSIT_CELL_SRAM_1W1R is synthesizable RTL with parameters ADDR_W and DATA_W, bit write mask BWEB, read register QR, no reset; a same-edge read of a written address returns the old word. | 20.2:s41 (p1508) |
| AF-20.2-39 | MUST | system | none | Library wrappers, cells and macro models are written in common_rtl/000_Common (rtl_lib and rtl_cells), each folder with its own filelist.f. | 20.2:s44, 20.2:s46 (p1511) |
| AF-20.2-40 | MUST | system | none | RTL module port lists are aligned in four columns and declared in functional groups with a comment per group, clock and reset first. | 20.2:s45 (p1512) |
| AF-20.2-41 | MUST | system | none | Cell and macro models are named VLSIT_CELL_*, and the header states that the model is synthesizable RTL and a real design uses the synthesis-library cell. | 20.2:s47 (p1514) |

## 21 Glossary

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| AF-21-01 | MUST | system | assertion | A pessimistic flag may be late to deassert but must never deassert early. *(when: For any pessimistic flag)* | 21:s11 (p1534) |

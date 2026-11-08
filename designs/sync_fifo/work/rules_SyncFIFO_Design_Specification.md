# Extracted rules - SyncFIFO_Design_Specification.md

```
rules: 320  by strength {'MUST': 270, 'MAY': 11, 'MUST_NOT': 38, 'SHOULD': 1}  by check {'none': 71, 'scenario': 106, 'both': 72, 'assertion': 71}
normative sentences: 150  cited 137  skipped 13  uncovered 0 (after first pass: 0)
invalid sentence IDs returned by the agent: 0
calls: 24 (0 from cache)  cost US$0.9003  tokens in 135414 out 45860
```


## T1 Synchronous-Clock FIFO Design Specification

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-T1-01 | MUST | system | none | Requirements marked 'shall' are mandatory and must be testable. | T1:s6 (p19) |

## 1.1 Purpose and scope

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-1.1-01 | MUST | system | scenario | The FIFO must transfer a stream of data words from the write clock domain to the read clock domain. | 1.1:s1 (p50) |
| SF-1.1-02 | MUST | system | both | Words must be read in the same order in which they were written (first-in first-out). | 1.1:s2 (p50) |
| SF-1.1-03 | MAY | system | scenario | The write and read clocks may have different frequencies, provided they are synchronous with a fixed phase relationship from one source. | 1.1:s3 (p50) |
| SF-1.1-04 | MUST_NOT | system | none | Pointers must cross between clock domains without synchronizers, as ordinary timed paths closed by STA. *(when: clocks are synchronous)* | 1.1:s4 (p50) |
| SF-1.1-05 | MAY | system | scenario | The write and read clocks may be equal (single clock) as a normal use case. | 1.1:s5 (p50) |
| SF-1.1-06 | MUST | system | scenario | The FIFO must provide write and read requests, full and empty flags, threshold flags, overflow and underflow pulses, show-ahead read, a hardware reset per domain and a software reset with handshake. | 1.1:s6 (p52) |
| SF-1.1-07 | MUST | system | none | Structural top m_vlsit_sfifo_top must instantiate the write module, the read module and the FIFO array module. | 1.1:s8 (p56) |
| SF-1.1-08 | MUST | system | none | The write module in the write clock domain must contain write pointer, full and full-threshold flags, overflow pulse, memory write port and write-side software reset FSM. | 1.1:s9 (p57) |
| SF-1.1-09 | MUST | system | none | The read module in the read clock domain must contain read pointer, empty and empty-threshold flags, underflow pulse, memory read address and read-side software reset FSM. | 1.1:s10 (p58) |
| SF-1.1-10 | MUST | system | none | The FIFO array module must be a pure RTL array or a library SRAM with one write port and one read port. | 1.1:s11 (p59) |
| SF-1.1-11 | MUST | system | scenario | The FIFO must support any depth of 2 or more, not only powers of two, and any data width of 1 bit or more. | 1.1:s12, 1.3:s1 (p60) |
| SF-1.1-12 | MUST | system | scenario | PARA_SFIFO_PTR_RETIME must select either a direct pointer path or one retiming flop in the destination domain. | 1.1:s13, 1.3:s7 (p61) |
| SF-1.1-13 | MUST | system | both | Streaming must be gap-free, with only the initial latency and no gap. *(when: depth at least 4 + 2 x PARA_SFIFO_PTR_RETIME, continuous write and continuous read)* | 1.1:s14, 1.3:s8 (p62) |
| SF-1.1-14 | MUST | system | both | Software reset must use a four-phase handshake between the two domains. | 1.1:s15, 1.3:s9 (p63) |

## 1.2 Deployment assumptions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-1.2-01 | MAY | system | none | The array may be replaced by an SRAM macro with one write port and one read port behind a wrapper. *(when: PARA_SFIFO_MEM_USE_MACRO = 1)* | 1.2:s2, 1.3:s10 (p77) |

## 1.3 Feature summary

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-1.3-01 | MUST | system | scenario | The FIFO must support two synchronous clocks of different frequencies without a synchronizer. | 1.3:s2 (p87) |
| SF-1.3-02 | MUST | system | both | Full and empty flags must have exact boundaries. | 1.3:s3 (p88) |
| SF-1.3-03 | MUST | system | both | Full and empty threshold flags must use static thresholds. | 1.3:s4 (p89) |
| SF-1.3-04 | MUST | system | both | The FIFO must provide overflow and underflow pulses. | 1.3:s5 (p90) |
| SF-1.3-05 | MUST | system | both | The FIFO must provide show-ahead read. | 1.3:s6 (p91) |

## 2.1 Normative references

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-2.1-01 | MUST | system | none | The RTL must follow VLSIT RTL Design Rules v2 (REF-003) as the mandatory coding, hierarchy, reset, CDC and naming baseline. | 2.1:s3, 2.2:s3 (p105) |

## 2.2 Source-of-truth and conflict handling

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-2.2-01 | MUST_NOT | system | none | REF-001 (the sibling AsyncGrayFIFO specification) must not override this specification; where they differ, this specification prevails. | 2.2:s2 (p114) |
| SF-2.2-02 | MUST | system | none | Conflicts must be resolved by revising the requirement or choosing a compliant implementation, not by a local RTL exception. *(when: When a conflict arises between requirements)* | 2.2:s4 (p115) |

## 3 Requirements and traceability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-3-01 | MUST | system | both | A write shall be accepted and the word on i_wr_data stored at the next free place. *(when: rising edge of i_clk_wr with i_wr_en 1, o_full 0 and writes not blocked by software reset)* | 3:s1 (p131) |
| SF-3-02 | MUST | system | both | A read shall be accepted, and the accepted word is the word shown on o_rd_data before that edge. *(when: rising edge of i_clk_rd with i_rd_en 1, o_empty 0 and reads not blocked by software reset)* | 3:s2 (p132) |
| SF-3-03 | MUST | system | both | o_rd_data shall show the next word (show-ahead) without a bubble. *(when: after an accepted read when another word is stored)* | 3:s2 (p132) |
| SF-3-04 | MUST | system | scenario | Words shall be read in the order written, with no loss and no duplication. *(when: every legal depth, data width, clock ratio, PARA_SFIFO_PTR_RETIME and memory option)* | 3:s3 (p133) |
| SF-3-05 | MUST | system | both | The FIFO shall store up to PARA_SFIFO_DEPTH words and o_full shall be 1 when PARA_SFIFO_DEPTH words are stored. *(when: whenever PARA_SFIFO_DEPTH words are stored)* | 3:s4 (p134) |
| SF-3-06 | MAY | system | none | o_full may be 1 while a place is free (conservative flag). *(when: a place is free but not yet visible in the write domain)* | 3:s4 (p134) |
| SF-3-07 | MUST | system | both | A write while o_full is 1 shall store nothing and leave the write pointer unchanged. *(when: write while o_full is 1)* | 3:s4 (p134) |
| SF-3-08 | MUST | system | both | o_empty shall be 1 whenever no stored word is visible to the read side. *(when: no stored word is visible to the read side)* | 3:s5 (p135) |
| SF-3-09 | MAY | system | none | o_empty may be 1 while a word exists (conservative flag). *(when: a word exists but is not yet visible in the read domain)* | 3:s5 (p135) |
| SF-3-10 | MUST | system | both | o_rd_data shall be valid whenever o_empty is 0; it is not meaningful while o_empty is 1. *(when: o_empty is 0)* | 3:s5 (p135) |
| SF-3-11 | MUST | system | both | A read while o_empty is 1 shall leave the read pointer unchanged. *(when: read while o_empty is 1)* | 3:s5 (p135) |
| SF-3-12 | MUST | system | scenario | The depth shall be any integer of 2 or more. | 3:s6 (p136) |
| SF-3-13 | MUST | system | both | Pointers shall count modulo two times the depth, and the memory address shall be the pointer modulo the depth. | 3:s6 (p136) |
| SF-3-14 | MUST | system | both | o_full_thr shall be 1 when write-side occupancy is greater than or equal to i_full_thr. *(when: occupancy seen by write side >= i_full_thr)* | 3:s7 (p137) |
| SF-3-15 | MUST | system | both | o_empty_thr shall be 1 when read-side occupancy is less than or equal to i_empty_thr. *(when: occupancy seen by read side <= i_empty_thr)* | 3:s7 (p137) |
| SF-3-16 | MUST | system | none | i_full_thr and i_empty_thr shall be static inputs. | 3:s7 (p137) |
| SF-3-17 | MUST | system | both | o_overflow shall pulse for one write-clock cycle in the following cycle and not be sticky. *(when: write requested while o_full was 1 and not blocked by software reset)* | 3:s8 (p138) |
| SF-3-18 | MUST | system | both | o_underflow shall pulse for one read-clock cycle in the following cycle and not be sticky. *(when: read requested while o_empty was 1 and not blocked by software reset)* | 3:s9 (p139) |
| SF-3-19 | MUST | system | both | A rejected write or read shall not change any pointer, stored word, or the occupancy. *(when: write or read rejected)* | 3:s10 (p140) |
| SF-3-20 | MUST | system | none | The IP shall expose exactly the ports of Section 6.2, and the port list shall not depend on parameters except for widths. | 3:s11 (p141) |
| SF-3-21 | MUST | system | none | Each listed output shall be driven by a flip-flop; the four flag outputs are combined with the software reset block term by one gate, with no other logic. | 3:s12 (p142) |
| SF-3-22 | MUST | system | scenario | o_rd_data shall be the memory output register (one read-clock latency) with no logic after it and no reset. | 3:s13 (p143) |
| SF-3-23 | MUST | system | scenario | The IP shall operate correctly with two synchronous clocks of any rational frequency ratio, including coinciding edges. *(when: clocks synchronous, any rational ratio, including coincident rising edges)* | 3:s14 (p144) |
| SF-3-24 | MUST_NOT | system | none | The IP shall contain no synchronizer and no clock-domain-crossing cell. | 3:s15 (p145) |
| SF-3-25 | MUST | system | none | Every inter-domain path shall be an ordinary timed path closed by STA with no false-path or asynchronous clock-group exception. | 3:s15 (p145) |
| SF-3-26 | MUST | system | none | The other domain's pointer shall enter the flag logic directly. *(when: PARA_SFIFO_PTR_RETIME = 0)* | 3:s16 (p146) |
| SF-3-27 | MUST | system | none | The other domain's pointer shall first be captured by one flip-flop in the destination domain. *(when: PARA_SFIFO_PTR_RETIME = 1)* | 3:s16 (p146) |
| SF-3-28 | MUST | system | scenario | The parameter shall change only flag latency and crossing-path timing, not function. | 3:s16 (p146) |
| SF-3-29 | MUST | system | scenario | Both resets shall be active-low with asynchronous assertion. | 3:s17 (p147) |
| SF-3-30 | MUST | system | both | Every flop of the domain shall be at reset value: pointers 0, o_full 0, o_empty 1, o_overflow 0, o_underflow 0, FSMs in RUN, o_sw_rst_busy 0, handshake flops 0. *(when: hardware reset asserted)* | 3:s17 (p147) |
| SF-3-31 | MUST | system | none | Release of each hardware reset shall be synchronous to its domain clock and provided outside the IP. | 3:s18 (p148) |
| SF-3-32 | MUST | system | scenario | The two resets shall be asserted together, and no operation shall start before both are released. | 3:s18 (p148) |
| SF-3-33 | MUST | system | scenario | i_rst_n_sw = 0 shall request a software reset; one low cycle suffices. *(when: i_rst_n_sw = 0 in write domain)* | 3:s19 (p149) |
| SF-3-34 | MUST | system | scenario | A longer low level shall be held until the sequence reaches its hold state. *(when: i_rst_n_sw held low longer)* | 3:s19 (p149) |
| SF-3-35 | MUST | system | both | Writes shall be blocked with no clock delay: o_full 1, o_full_thr showing empty-FIFO value, and no write accepted. *(when: from the cycle in which i_rst_n_sw is 0)* | 3:s20 (p150) |
| SF-3-36 | MUST | system | both | Writes shall remain blocked until o_sw_rst_busy is 0. *(when: until o_sw_rst_busy is 0)* | 3:s20 (p150) |
| SF-3-37 | MUST_NOT | system | both | A blocked write shall not raise o_overflow. *(when: write blocked by software reset)* | 3:s20 (p150) |
| SF-3-38 | MUST | system | both | Reads shall be blocked: o_empty 1, o_empty_thr 1, no read accepted until the read side is released. *(when: software reset request reaches the read side)* | 3:s21 (p151) |
| SF-3-39 | MUST_NOT | system | both | A blocked read shall not raise o_underflow. *(when: read blocked by software reset)* | 3:s21 (p151) |
| SF-3-40 | MUST | system | scenario | Read side shall reset its pointer first and acknowledge, then write side resets its pointer; read side is released first, write side last. *(when: software reset sequence)* | 3:s22 (p152) |
| SF-3-41 | MUST | system | scenario | The software reset handshake shall be four-phase. | 3:s22 (p152) |
| SF-3-42 | MUST | system | scenario | The FIFO shall be empty, both pointers 0, and every stored word discarded. *(when: end of software reset sequence)* | 3:s23 (p153) |
| SF-3-43 | MUST_NOT | system | scenario | The memory content shall not be erased. *(when: software reset)* | 3:s23 (p153) |
| SF-3-44 | MUST | system | both | o_sw_rst_busy shall be a flip-flop output, 1 from the cycle after the write FSM takes the request until the cycle the write FSM is back in RUN. | 3:s24 (p154) |
| SF-3-45 | MUST | system | both | The FIFO is ready for writes when o_sw_rst_busy is 0 and i_rst_n_sw is 1. *(when: o_sw_rst_busy 0 and i_rst_n_sw 1)* | 3:s24 (p154) |
| SF-3-46 | MUST | system | scenario | A hardware reset shall have priority over a software reset and bring both FSMs to RUN. *(when: any time)* | 3:s25 (p155) |
| SF-3-47 | MUST | system | scenario | The request shall be served as a new sequence when the write FSM is back in RUN. *(when: request arrives while a sequence is running)* | 3:s26 (p156) |
| SF-3-48 | MUST | system | scenario | The sequence shall stay in the hold state. *(when: low level held in hold state)* | 3:s26 (p156) |
| SF-3-49 | MUST | system | none | The IP shall accept the parameter values listed in Section 8. | 3:s27 (p157) |
| SF-3-50 | MUST | system | scenario | The IP shall accept one write per write-clock cycle and one read per read-clock cycle. | 3:s28 (p158) |
| SF-3-51 | MUST | system | scenario | There shall be only initial latency and no gap: every cycle where the other side is not limiting accepts a read or write. *(when: i_wr_en and i_rd_en held at 1, depth >= 4 + 2 x PARA_SFIFO_PTR_RETIME)* | 3:s29 (p159) |
| SF-3-52 | MUST | system | scenario | o_empty shall fall after the first strictly later i_clk_rd rising edge (RETIME 0) or the second (RETIME 1), with o_rd_data showing the new word. *(when: write into empty FIFO)* | 3:s30 (p160) |
| SF-3-53 | MUST | system | scenario | o_full shall fall after the first strictly later i_clk_wr rising edge (RETIME 0) or the second (RETIME 1). *(when: read from full FIFO)* | 3:s31 (p161) |
| SF-3-54 | MUST | system | both | o_full shall be 1 the cycle after the write storing the last free place; o_empty shall be 1 the cycle after the read taking the last word. | 3:s32 (p162) |
| SF-3-55 | MUST | system | none | The RTL shall comply with REF-003 and use the hierarchy of Section 14.2. | 3:s33 (p163) |
| SF-3-56 | MUST | system | none | The library SRAM shall be instantiated only inside the VLSIT_CELL_SRAM_1W1R wrapper in 000_Common, with instance name u_dont_touch_ plus function name, behaving like the array branch. *(when: CFG-MACRO)* | 3:s34 (p164) |
| SF-3-57 | MUST_NOT | system | none | The IP shall contain no synchronizer module and no cell wrapper other than the SRAM wrapper; the retiming flop shall be a plain RTL flip-flop. | 3:s35 (p165) |
| SF-3-58 | MUST | system | none | Every waveform of the plan shall exist as an image with WaveJSON source, reproducible by prototype scripts. | 3:s36 (p166) |
| SF-3-59 | MUST | system | scenario | Scoreboard regression shall cover depths 2, 3, 5, 8, 12, both PARA_SFIFO_PTR_RETIME values and several clock ratios including equal, with no error. | 3:s37 (p167) |

## 4 Features and configurations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-4-01 | MUST | system | scenario | CFG-BASE must have PARA_SFIFO_PTR_RETIME = 0, PARA_SFIFO_MEM_USE_MACRO = 0, DATA_W 32, DEPTH 8, and be verified by all tests. *(when: CFG-BASE)* | 4:s1 (p175) |
| SF-4-02 | MUST | system | scenario | CFG-RETIME must enable CFG-BASE plus FEAT-007 with PARA_SFIFO_PTR_RETIME = 1 and be verified by TEST-002, 006, 007, 009, 011, 015, 017. *(when: CFG-RETIME)* | 4:s2 (p176) |
| SF-4-03 | MUST | system | scenario | CFG-MACRO must enable CFG-BASE plus FEAT-010 with PARA_SFIFO_MEM_USE_MACRO = 1 and be verified by TEST-002 and TEST-012. *(when: CFG-MACRO)* | 4:s3 (p177) |
| SF-4-04 | MUST | system | scenario | CFG-ODD must support a DEPTH that is not a power of two, such as 5 or 12, verified by TEST-008. *(when: CFG-ODD)* | 4:s4 (p178) |
| SF-4-05 | MUST | system | scenario | CFG-MIN (DEPTH 2, DATA_W 1, CFG-BASE features, FEAT-007 and FEAT-010 disabled) must be a legal instance and be verified by TEST-013. *(when: CFG-MIN with DEPTH 2 and DATA_W 1)* | 4:s5 (p179) |
| SF-4-06 | MUST | system | scenario | FEAT-007 and FEAT-010 must be selected by a parameter at elaboration and be present or absent, not run-time disabled. *(when: FEAT-007 and FEAT-010 selection)* | 4:s6 (p181) |
| SF-4-07 | MUST | system | scenario | The port list must be identical in every configuration except for port widths. *(when: In every configuration)* | 4:s7 (p181) |
| SF-4-08 | MUST_NOT | system | none | Parameter combinations listed as illegal in Section 8 must not be used. | 4:s8 (p181) |

## 5.1 Overview and block responsibilities

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-5.1-01 | MUST | system | scenario | Flags are flip-flops computed from the next pointer values (look-ahead), so each flag is exact at its own domain's clock edge and conservative only by the other side's pointer visibility. | 5.1:s3 (p187) |
| SF-5.1-02 | MUST | master | none | m_vlsit_sfifo_wr owns the write pointer, write acceptance, full and full-threshold flags, overflow pulse, memory write port and write-side software reset FSM, in CLK-WR/RST-WR domain. | 5.1:s4 (p191) |
| SF-5.1-03 | MUST | slave | none | m_vlsit_sfifo_rd owns the read pointer, read acceptance, empty and empty-threshold flags, underflow pulse, memory read address (next read pointer) and read-side reset FSM, in CLK-RD/RST-RD domain. | 5.1:s5 (p192) |
| SF-5.1-04 | MUST | system | none | m_vlsit_sfifo_top is a structural wrapper holding interface, parameters, interconnect and the three instances, with no state or storage. | 5.1:s7 (p194) |

## 5.3 Transaction and dataflow

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-5.3-01 | MUST | system | both | The word on i_wr_data is stored at the write pointer address, the write pointer increments, and flags are recomputed for the next cycle. *(when: At a rising edge of i_clk_wr with i_wr_en = 1, o_full = 0 and no software reset block)* | 5.3:s3 (p204) |
| SF-5.3-02 | MUST | system | both | The read side uses the new write pointer at its next strictly later rising edge, directly or one edge later through the retiming flop. *(when: After the write pointer updates)* | 5.3:s6 (p205) |
| SF-5.3-03 | MUST | system | both | The read flag register and memory output register load at the same edge, so o_empty and the read data change together. *(when: When the read side uses the new write pointer)* | 5.3:s7 (p205) |
| SF-5.3-04 | MUST | system | both | The word on o_rd_data is taken, the read pointer increments, and the output register loads the following word; the memory read address is the next read pointer's address. *(when: At a rising edge of i_clk_rd with i_rd_en = 1 and o_empty = 0)* | 5.3:s9, 5.4:s5 (p206) |
| SF-5.3-05 | MUST | system | scenario | The read pointer becomes visible to the write side at its next strictly later rising edge, directly or one edge later, where o_full may fall. *(when: After the read pointer increments)* | 5.3:s11 (p207) |

## 5.4 Invariants

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-5.4-01 | MUST | system | assertion | Occupancy (write pointer minus read pointer modulo twice the depth) stays between 0 and PARA_SFIFO_DEPTH. | 5.4:s1 (p211) |
| SF-5.4-02 | MUST_NOT | system | assertion | No write is accepted while o_full is 1, and no read is accepted while o_empty is 1. *(when: o_full is 1 (write) or o_empty is 1 (read))* | 5.4:s2 (p212) |
| SF-5.4-03 | MUST | system | assertion | o_full is 1 whenever occupancy is PARA_SFIFO_DEPTH, and o_empty is 1 whenever occupancy is 0. *(when: Occupancy equals PARA_SFIFO_DEPTH or 0)* | 5.4:s3 (p213) |
| SF-5.4-04 | MUST_NOT | system | assertion | The write side never sees a read pointer ahead of the real one, and the read side never sees a write pointer ahead of the real one; views only lag. | 5.4:s4 (p214) |
| SF-5.4-05 | MUST | system | assertion | Pointers and flags change only at a rising edge of the clock of their own domain. | 5.4:s6 (p216) |

## 6.1 Interface inventory

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-6.1-01 | MUST | slave | none | IF-001 custom FIFO write interface is required in all configurations, acts as slave of the writer in CLK-WR with requests in and status out. | 6.1:s1 (p224) |
| SF-6.1-02 | MUST | slave | none | IF-002 custom FIFO read interface is required in all configurations, acts as slave of the reader in CLK-RD with requests in and data and status out. | 6.1:s2 (p225) |
| SF-6.1-03 | MUST | slave | none | IF-003 software reset interface is required in all configurations, slave of the controller in CLK-WR, with request input and busy output. | 6.1:s3 (p226) |
| SF-6.1-04 | MUST | system | none | IF-004 clocks and hardware resets are required inputs in all configurations, in domains CLK-WR and CLK-RD. | 6.1:s4 (p227) |

## 6.2 Complete port list

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-6.2-01 | MUST | system | none | The top-level port list must not depend on any parameter value except for port widths. | 6.2:s5 (p231) |
| SF-6.2-02 | MUST | slave | assertion | o_sw_rst_busy is a flop output that changes only at a rising edge of i_clk_wr and is 0 when writes are possible again. | 6.2:s13 (p243) |
| SF-6.2-03 | MUST | system | none | Clocks are rising-edge active, and the IP performs no clock gating inside. | 6.2:s26 (p260) |
| SF-6.2-04 | MUST | master | scenario | A reset is a level that stays low for at least one edge of its clock and is released synchronously to that clock outside the IP. | 6.2:s27 (p261) |
| SF-6.2-05 | MUST | slave | both | A Level request is sampled at every edge, and each such edge is one transaction; a flag stays 1 as long as its condition holds. *(when: A request is 1 at a clock edge and the acceptance condition holds)* | 6.2:s28 (p262) |
| SF-6.2-06 | MUST | slave | assertion | A Pulse output is a flop output that is 1 for exactly one clock period after the event edge, returns to 0 by itself and is not sticky. | 6.2:s29 (p263) |
| SF-6.2-07 | MUST | slave | assertion | Data signals are valid only while or when their named qualifier is true, e.g. o_rd_data valid when o_empty = 0. | 6.2:s30 (p264) |
| SF-6.2-08 | MUST_NOT | master | none | Static configuration values such as i_full_thr and i_empty_thr must not be changed while the FIFO is in use; they have no clock domain. *(when: While the FIFO is in use)* | 6.2:s31 (p265) |

## 6.3 Protocol behavior

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-6.3-01 | MUST | slave | both | The write is accepted when i_wr_en = 1, o_full = 0 and writes are not blocked by the software reset. *(when: i_wr_en = 1, o_full = 0 and writes not blocked by software reset)* | 6.3:s9 (p276) |
| SF-6.3-02 | MUST_NOT | slave | assertion | A write request is never accepted while o_full = 1. *(when: o_full = 1)* | 6.3:s10 (p276) |
| SF-6.3-03 | MUST | slave | both | The read is accepted when i_rd_en = 1, o_empty = 0 and reads are not blocked; o_rd_data is valid for the whole cycle before the accepting edge. *(when: i_rd_en = 1, o_empty = 0 and reads not blocked)* | 6.3:s13 (p277) |
| SF-6.3-04 | MUST | slave | both | o_rd_data shows the next word in the next cycle with no bubble. *(when: After an accepted read, if another word is visible)* | 6.3:s15 (p278) |
| SF-6.3-05 | MUST_NOT | slave | scenario | A flag view may lag real occupancy only in the safe direction (full late to fall, empty late to fall), never in the unsafe direction. | 6.3:s17 (p279) |
| SF-6.3-06 | MUST | slave | both | A rejected write or read changes no state but raises the one-cycle overflow or underflow pulse. *(when: A write or read is rejected)* | 6.3:s19 (p280) |
| SF-6.3-07 | MUST | slave | both | A write into a FIFO that is not full is accepted at the edge, the word is stored and the write pointer increments. *(when: Write while FIFO is not full)* | 6.3:s20 (p284) |
| SF-6.3-08 | MUST | slave | both | A write while o_full = 1 is dropped and an o_overflow pulse occurs in the next cycle. *(when: i_wr_en = 1 while o_full = 1)* | 6.3:s21 (p285) |
| SF-6.3-09 | MUST | slave | both | A read from a non-empty FIFO is accepted at the edge, the word is taken and the next word is shown. *(when: Read while FIFO is not empty)* | 6.3:s22 (p286) |
| SF-6.3-10 | MUST | slave | both | A read while o_empty = 1 is dropped and an o_underflow pulse occurs in the next cycle. *(when: i_rd_en = 1 while o_empty = 1)* | 6.3:s23 (p287) |
| SF-6.3-11 | MUST | slave | both | A request during software-reset blocking is dropped, with no o_overflow or o_underflow pulse. *(when: Write or read while the software reset blocks that side)* | 6.3:s24 (p288) |
| SF-6.3-12 | MAY | any | none | IP response to a request during hardware reset is not defined. *(when: Request while a hardware reset is asserted)* | 6.3:s25 (p289) |
| SF-6.3-13 | MAY | slave | none | If a threshold input is not static, the flag may take a wrong value for some cycles. *(when: Threshold input changed while the FIFO is in use)* | 6.3:s26 (p290) |

## 7.2 CDC and RDC

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-7.2-01 | MUST | system | none | The two clocks i_clk_wr and i_clk_rd shall be declared as related clocks of one source. *(when: When constraints are declared for the IP)* | 7.2:s1 (p325) |
| SF-7.2-02 | MUST_NOT | system | none | No asynchronous clock group or false path shall be set between i_clk_wr and i_clk_rd. *(when: When constraints are declared for the IP)* | 7.2:s1 (p325) |

## 7.3 Reset domains and sequencing

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-7.3-01 | MUST | slave | both | On i_rst_n_wr, write pointer shall be 0, o_full 0, o_full_thr 0, o_overflow 0, write FSM RUN, request 0, busy 0. *(when: When i_rst_n_wr is asserted)* | 7.3:s1 (p331) |
| SF-7.3-02 | MUST | slave | both | On i_rst_n_rd, read pointer shall be 0, o_empty 1, o_empty_thr 1, o_underflow 0, read FSM RUN, acknowledge 0. *(when: When i_rst_n_rd is asserted)* | 7.3:s2 (p332) |
| SF-7.3-03 | MUST | slave | scenario | The FIFO shall be empty at the end of the software reset sequence. *(when: When i_rst_n_sw is requested low and the sequence completes)* | 7.3:s3 (p333) |
| SF-7.3-04 | MUST | system | scenario | The two hardware resets are asserted together and released synchronously to their own clocks; no operation starts before both are released. | 7.3:s4 (p335) |
| SF-7.3-05 | MUST | slave | scenario | All flip-flops shall reset asynchronously to 0, except flag registers o_empty and o_empty_thr which reset to 1. *(when: On asynchronous reset)* | 7.3:s5 (p335) |
| SF-7.3-06 | MUST | slave | assertion | The read side shall consume a word only when o_empty is 0. *(when: Memory content is not reset)* | 7.3:s6 (p335) |
| SF-7.3-07 | MUST | slave | both | o_empty shall become 0 only after the corresponding word has been written to memory. | 7.3:s6 (p335) |
| SF-7.3-08 | MUST | slave | scenario | A hardware reset shall have priority over a software reset. *(when: Hardware reset and software reset overlap at any time)* | 7.3:s7 (p335) |

## 7.4 Power intent (if applicable)

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-7.4-01 | MUST_NOT | system | none | The IP shall have no isolation, retention or power sequencing of its own; it sits in one always-on power domain. | 7.4:s1 (p339) |

## 8 Parameters and elaboration configurations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-8-01 | MUST_NOT | system | none | The IP does not include an elaboration check for illegal parameter values (REQ-PARAM-001). | 8:s3 (p343) |
| SF-8-02 | MAY | system | none | $clog2 may be used for the derived widths. *(when: when deriving widths)* | 8:s3 (p343) |
| SF-8-03 | MUST | system | scenario | PARA_SFIFO_DEPTH (default 8) must be an integer of 2 or more with no upper limit; it sets the number of entries, storage size and pointer width. | 8:s4 (p347) |
| SF-8-04 | MUST | system | scenario | PARA_SFIFO_DATA_W (default 32) must be 1 or more with no upper limit and sets the width of i_wr_data, o_rd_data and the storage. | 8:s5 (p348) |
| SF-8-05 | MUST | system | scenario | PARA_SFIFO_PTR_RETIME (default 0) must be 0 or 1: 0 = direct pointer path, 1 = one retiming flop in the destination domain. | 8:s6 (p349) |
| SF-8-06 | MUST | system | scenario | PARA_SFIFO_PTR_RETIME changes only flag latency and crossing path timing; the FIFO function is the same for both values. | 8:s6 (p349) |
| SF-8-07 | MUST | system | scenario | PARA_SFIFO_MEM_USE_MACRO (default 0) must be 0 or 1: 0 = RTL array storage, 1 = library SRAM wrapper storage. | 8:s7 (p350) |
| SF-8-08 | MUST | system | none | The SRAM wrapper must use the macro model VLSIT_CELL_SRAM_1W1R of 000_Common. *(when: when PARA_SFIFO_MEM_USE_MACRO is 1 until the real macro is mapped)* | 8:s7 (p350) |
| SF-8-09 | MUST | system | assertion | LPARA_ADDR_W must be derived as clog2(PARA_SFIFO_DEPTH), at least 1, and sets the memory address width. | 8:s8 (p351) |
| SF-8-10 | MUST | system | assertion | LPARA_PTR_W must be derived as clog2(2 x PARA_SFIFO_DEPTH), at least 2; the pointer counts 0 to 2 x DEPTH - 1. | 8:s9 (p352) |
| SF-8-11 | MUST | system | assertion | LPARA_OCC_W must be derived as clog2(PARA_SFIFO_DEPTH + 1), at least 2, and sets the width of i_full_thr and i_empty_thr; occupancy is 0 to DEPTH. | 8:s10 (p353) |
| SF-8-12 | MUST | system | scenario | The smallest legal instance must elaborate and lint with the same hierarchy. *(when: CFG-MIN with PARA_SFIFO_DEPTH = 2 and PARA_SFIFO_DATA_W = 1)* | 8:s15 (p361) |
| SF-8-13 | MUST_NOT | system | none | These illegal configurations must not be used; the IP does not check them and its behavior with them is not specified. *(when: depth below 2, data width 0, or option parameter outside 0..1)* | 8:s16, 8:s17 (p363) |
| SF-8-14 | MAY | system | scenario | The depth is legal but gap-free streaming is not guaranteed. *(when: PARA_SFIFO_DEPTH below 4 + 2 x PARA_SFIFO_PTR_RETIME)* | 8:s18 (p363) |

## 9 Data representation and arithmetic

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-9-01 | MUST | system | assertion | The pointer, of width LPARA_PTR_W, must be an unsigned value in the range 0 to 2 x DEPTH - 1 and must return to 0 after 2 x DEPTH - 1. | 9:s4 (p372) |
| SF-9-02 | MUST_NOT | system | assertion | The pointer must never exceed its range of 2 x DEPTH - 1; increment is explicit with no truncation. | 9:s4 (p372) |
| SF-9-03 | MUST | system | assertion | Occupancy must equal write pointer minus read pointer if the write pointer is not below the read pointer, otherwise that difference plus 2 x DEPTH, giving a result of 0 to DEPTH. | 9:s6 (p374) |
| SF-9-04 | MUST_NOT | system | assertion | Occupancy must not exceed DEPTH, because the full flag blocks writes. | 9:s6 (p374) |
| SF-9-05 | MUST | system | both | A threshold value above DEPTH must make o_full_thr never 1 and o_empty_thr always 1. *(when: When the threshold value is above DEPTH)* | 9:s7 (p375) |
| SF-9-06 | MUST | system | scenario | The threshold, of width LPARA_OCC_W, is an unsigned occupancy value from 0 to DEPTH and is zero-extended for the comparison. | 9:s7 (p375) |

## 10.1 Modes and state transitions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-10.1-01 | MUST | system | assertion | The data path has no mode; acceptance of writes and reads is decided only by the flags. | 10.1:s1 (p382) |
| SF-10.1-02 | MUST | master | scenario | Write reset FSM leaves RUN to REQ when i_rst_n_sw = 0, blocks writes, raises request and drives o_sw_rst_busy 1 until acknowledge is seen. *(when: Write reset FSM in ENUM_ST_RUN and i_rst_n_sw = 0)* | 10.1:s3, 10.1:s4, 10.1:s5 (p384) |
| SF-10.1-03 | MUST | system | scenario | Write reset FSM state encodings 5 to 7 recover to RUN. *(when: Write reset FSM state encoding is 5 to 7)* | 10.1:s3 (p384) |
| SF-10.1-04 | MUST | system | scenario | In ENUM_ST_PTR the write pointer is reset to 0 for one cycle, request stays 1, and the FSM always moves to HOLD. *(when: Write reset FSM in ENUM_ST_PTR after acknowledge seen)* | 10.1:s6 (p390) |
| SF-10.1-05 | MUST | system | scenario | HOLD waits with request 1 until i_rst_n_sw = 1, then REL drops request, keeps o_sw_rst_busy 1 and returns to RUN when acknowledge is 0 and read pointer is 0. *(when: Write reset FSM in HOLD or REL)* | 10.1:s7, 10.1:s8 (p391) |
| SF-10.1-06 | MUST | system | scenario | Read reset FSM encoding 3 recovers to RUN; in RUN acknowledge is 0 and request seen moves it to RST. *(when: Read reset FSM encoding 3, or in RUN)* | 10.1:s9, 10.1:s10 (p394) |
| SF-10.1-07 | MUST | system | scenario | In ENUM_ST_RST reads are blocked, the read pointer is reset to 0 for one cycle, the FSM goes to ACK and acknowledge rises at the exit edge. *(when: Read reset FSM in ENUM_ST_RST)* | 10.1:s11 (p399) |
| SF-10.1-08 | MUST | system | scenario | In ENUM_ST_ACK reads are blocked and acknowledge held at 1 until request is 0 and write pointer is seen as 0, then FSM returns to RUN. *(when: Read reset FSM in ENUM_ST_ACK)* | 10.1:s12 (p400) |

## 10.2 Operations

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-10.2-01 | MUST | system | both | The write stores i_wr_data at the write address and increments the write pointer; o_empty falls in the read domain and o_full rises at once if it was the last free place. *(when: i_wr_en = 1, o_full = 0, no software reset block)* | 10.2:s1 (p406) |
| SF-10.2-02 | MUST | system | both | The read side sees the written word after the first (PTR_RETIME 0) or second (PTR_RETIME 1) read edge strictly after the write edge. *(when: After a write; PARA_SFIFO_PTR_RETIME 0 or 1)* | 10.2:s1, 10.3:s46 (p406) |
| SF-10.2-03 | MUST | system | both | The read takes the word of o_rd_data, increments the read pointer and loads the next word into the output register; o_empty rises at once if it was the last word. *(when: i_rd_en = 1, o_empty = 0, no software reset block)* | 10.2:s2 (p407) |
| SF-10.2-04 | MUST | system | both | o_full falls in the write domain after the first (PTR_RETIME 0) or second (PTR_RETIME 1) write edge strictly after the read edge. *(when: After a read)* | 10.2:s2, 10.3:s48 (p407) |
| SF-10.2-05 | MUST | system | assertion | The write is rejected with no state change and o_overflow pulses in the next cycle. *(when: i_wr_en = 1, o_full = 1, no block)* | 10.2:s3 (p408) |
| SF-10.2-06 | MUST | system | assertion | The read is rejected with no state change and o_underflow pulses in the next cycle. *(when: i_rd_en = 1, o_empty = 1, no block)* | 10.2:s4 (p409) |
| SF-10.2-07 | MUST | system | both | o_full_thr and o_empty_thr compare the occupancy of the own domain view with the thresholds and update at every edge of the own clock. *(when: Static thresholds)* | 10.2:s5 (p410) |
| SF-10.2-08 | MUST | system | scenario | Software reset runs the sequence block, reset read pointer, reset write pointer, release, ending with FIFO empty, pointers 0 and o_sw_rst_busy 0. *(when: i_rst_n_sw = 0)* | 10.2:s6 (p411) |
| SF-10.2-09 | MUST | system | both | The state of the domain is cleared asynchronously and immediately, leaving the FIFO empty with reset values. *(when: i_rst_n_wr = 0 or i_rst_n_rd = 0)* | 10.2:s7 (p412) |

## 10.3 Cycle-level behavior

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-10.3-01 | MUST | system | scenario | After the initial latency a word is read every cycle with no gap; the latency is one cycle longer with PARA_SFIFO_PTR_RETIME = 1. *(when: Equal clocks, continuous write and read)* | 10.3:s12, 10.3:s13, 10.3:s28, 10.3:s29, 10.3:s31 (p427) |
| SF-10.3-02 | MUST | system | scenario | The reader never stalls; the faster writer is held back by o_full only because the reader is slower. *(when: Continuous traffic, write clock 8 ns, read clock 12 ns)* | 10.3:s14, 10.3:s34 (p429) |
| SF-10.3-03 | MUST | system | scenario | The writer never stalls; the faster reader waits through o_empty and o_underflow only because the writer is slower. *(when: Continuous traffic, read clock 8 ns, write clock 12 ns)* | 10.3:s15, 10.3:s37 (p430) |
| SF-10.3-04 | MUST | system | scenario | Pointer wraps over 0 to 9 and address over 0 to 4. *(when: Depth 5)* | 10.3:s16, 10.3:s39 (p431) |
| SF-10.3-05 | MUST | system | assertion | The active edge is the rising edge of the signal's own domain clock; inputs are sampled at the edge ending a cycle and flop outputs change after the edge starting it. | 10.3:s20, 10.3:s21 (p436) |
| SF-10.3-06 | MUST | system | assertion | o_rd_data is meaningful only while o_empty is 0. | 10.3:s37 (p460) |
| SF-10.3-07 | MUST | system | scenario | o_full_thr rises at occupancy 6 and o_empty_thr falls at occupancy 3. *(when: Thresholds 6 and 2, depth 8)* | 10.3:s41 (p468) |
| SF-10.3-08 | MUST | system | assertion | Each read request on an empty FIFO gives one o_underflow pulse. *(when: Read requests on empty FIFO)* | 10.3:s43 (p472) |
| SF-10.3-09 | MUST | system | assertion | The word is stored, write pointer increments, write-domain flags are recomputed, and o_full may rise in the next cycle if it was the last place. *(when: Write edge with i_wr_en = 1, o_full = 0)* | 10.3:s45 (p478) |
| SF-10.3-10 | MUST | system | assertion | With PTR_RETIME 0, o_empty falls and o_rd_data shows the new word after E_r1; with PTR_RETIME 1, after E_r2. *(when: First read edge strictly after write edge)* | 10.3:s46 (p479) |
| SF-10.3-11 | MUST | system | assertion | The word is taken, read pointer increments, next word loaded, and o_empty rises in the next cycle if it was the last word. *(when: Read edge with i_rd_en = 1, o_empty = 0)* | 10.3:s47 (p480) |
| SF-10.3-12 | MUST | system | assertion | With PTR_RETIME 0, o_full falls after E_w1; with PTR_RETIME 1, after E_w2. *(when: First write edge strictly after read edge)* | 10.3:s48 (p481) |
| SF-10.3-13 | MUST | system | scenario | A coinciding edge does not count as strictly later; the pointer written at that edge is seen at the next edge. *(when: Source and destination clock edges coincide)* | 10.3:s49, 10.3:s50 (p483) |

## 10.4 Arbitration, buffering, and throughput

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-10.4-01 | MUST | system | both | Simultaneous write and read are independent and both are accepted at the same clock edge when o_full and o_empty allow. *(when: a write and a read occur at the same clock edge and the flags allow both)* | 10.4:s2 (p487) |
| SF-10.4-02 | MUST | system | assertion | The FIFO accepts one word per write-clock cycle and delivers one word per read-clock cycle (REQ-PERF-001). | 10.4:s4 (p489) |
| SF-10.4-03 | MUST | system | scenario | o_empty falls at the first read edge strictly after the write edge when PARA_SFIFO_PTR_RETIME = 0, and one read period later when PARA_SFIFO_PTR_RETIME = 1. *(when: after a write into an empty FIFO)* | 10.4:s6 (p495) |
| SF-10.4-04 | MUST | system | scenario | The first read accepted after the write edge occurs after 2 cycles with PARA_SFIFO_PTR_RETIME = 0 and after 3 cycles with PARA_SFIFO_PTR_RETIME = 1. *(when: equal clocks)* | 10.4:s7 (p496) |
| SF-10.4-05 | MUST | system | scenario | o_full falls at the first write edge strictly after the read edge when PARA_SFIFO_PTR_RETIME = 0, and one write edge later when PARA_SFIFO_PTR_RETIME = 1. *(when: after a read from a full FIFO)* | 10.4:s8 (p497) |
| SF-10.4-06 | MUST | system | assertion | o_empty = 1 in the next cycle after the last word is read, for both PARA_SFIFO_PTR_RETIME values. *(when: the last word is read)* | 10.4:s9 (p498) |
| SF-10.4-07 | MUST | system | assertion | o_full = 1 in the next cycle after the last free place is written, for both PARA_SFIFO_PTR_RETIME values. *(when: the last free place is written)* | 10.4:s10 (p499) |
| SF-10.4-08 | MUST | system | scenario | Streaming has no gaps beyond the initial latency. *(when: i_wr_en and i_rd_en held at 1)* | 10.4:s11, 10.4:s12 (p501) |
| SF-10.4-09 | MUST | system | scenario | The side that is not rate-limited never stalls (REQ-PERF-002). *(when: depth at least 4 + 2 x PARA_SFIFO_PTR_RETIME, over the tested clock ratios)* | 10.4:s13, 10.4:s14, 10.4:s15, 10.4:s16 (p501) |
| SF-10.4-10 | MUST | system | scenario | The FIFO remains functionally correct, although a gap may appear. *(when: depth is smaller than needed for gap-free streaming)* | 10.4:s18 (p508) |

## 10.5 Memories and storage

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-10.5-01 | MUST | system | assertion | The memory is read at the address of the next read pointer. *(when: every read-clock cycle)* | 10.5:s3 (p517) |
| SF-10.5-02 | MUST | system | scenario | A read of the address written at the same edge returns the old word, and the read side takes a word only after the flag fell. *(when: read and write of the same address at the same edge)* | 10.5:s4 (p517) |
| SF-10.5-03 | MUST_NOT | system | assertion | The memory must not be invalid at an address that is read. *(when: o_empty = 0)* | 10.5:s5 (p517) |

## 10.6 Flags, pointers and thresholds

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-10.6-01 | MUST | system | assertion | Occupancy occ(a,b) = a - b if a is not below b, otherwise a + 2 x DEPTH - b. | 10.6:s1, 10.6:s2 (p521) |
| SF-10.6-02 | MUST | system | assertion | Write-domain flops load at the edge from next values: a write is accepted when i_wr_en, not block and not full flop; the full flop is set when next occupancy equals DEPTH; the full-threshold flop when it reaches i_full_thr. *(when: write domain)* | 10.6:s3, 10.6:s4, 10.6:s5, 10.6:s6, 10.6:s7, 10.6:s8, 10.6:s9, 10.6:s10 (p523) |
| SF-10.6-03 | MUST | system | assertion | o_full = block OR full flop; o_full_thr = (i_full_thr equals 0) when block, otherwise the full-threshold flop. *(when: write domain)* | 10.6:s11, 10.6:s12 (p534) |
| SF-10.6-04 | MUST | system | assertion | o_overflow is a flop set one cycle after i_wr_en with not block and full flop. | 10.6:s13 (p536) |
| SF-10.6-05 | MUST | system | assertion | Read-domain flops load at the edge from next values: a read is accepted when i_rd_en, not block and not empty flop; the empty flop is set when next occupancy equals 0; the threshold flop when at or below i_empty_thr. *(when: read domain)* | 10.6:s14, 10.6:s15, 10.6:s16, 10.6:s17, 10.6:s18, 10.6:s19, 10.6:s20, 10.6:s21 (p538) |
| SF-10.6-06 | MUST | system | assertion | o_empty = block OR empty flop; o_empty_thr = 1 when block, otherwise the empty-threshold flop. *(when: read domain)* | 10.6:s22, 10.6:s23 (p549) |
| SF-10.6-07 | MUST | system | assertion | o_underflow is a flop set one cycle after i_rd_en with not block and empty flop. | 10.6:s24 (p551) |
| SF-10.6-08 | MUST | system | assertion | The memory read address is the next read pointer modulo DEPTH. | 10.6:s25 (p552) |
| SF-10.6-09 | MUST | system | assertion | The write view of occupancy never underestimates the real occupancy and the read view never overestimates it. | 10.6:s26 (p554) |
| SF-10.6-10 | MUST | system | assertion | o_full_thr is 0 until the first clock edge after release, then follows the formula even if i_full_thr is 0. *(when: after reset)* | 10.6:s27 (p554) |

## 10.7 Software reset

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-10.7-01 | MUST | system | assertion | From that cycle writes are blocked and o_full is 1. *(when: i_rst_n_sw driven to 0)* | 10.7:s4, 10.7:s5 (p560) |
| SF-10.7-02 | MUST | system | scenario | The write FSM leaves RUN, o_sw_rst_busy rises in the next cycle, and the request flop is raised. *(when: software reset request)* | 10.7:s6 (p560) |
| SF-10.7-03 | MUST | system | scenario | The read FSM blocks reads (o_empty = 1), resets the read pointer in state RST for one cycle and raises the acknowledge. *(when: read FSM sees the request)* | 10.7:s8 (p561) |
| SF-10.7-04 | MUST | system | scenario | The write FSM resets the write pointer in state PTR for one cycle and waits in HOLD until i_rst_n_sw is 1. *(when: write FSM sees the acknowledge)* | 10.7:s10 (p562) |
| SF-10.7-05 | MUST | system | scenario | In REL the request is dropped; the read side leaves ACK when it sees the request at 0 and the write pointer at 0. *(when: release)* | 10.7:s12, 10.7:s13 (p563) |
| SF-10.7-06 | MUST | system | scenario | The write side leaves REL when it sees the acknowledge at 0 and the read pointer at 0, returns to RUN, and o_sw_rst_busy falls. *(when: write FSM in REL)* | 10.7:s14 (p563) |
| SF-10.7-07 | MUST | system | assertion | The FIFO is ready for writes when o_sw_rst_busy is 0 and i_rst_n_sw is 1. | 10.7:s15 (p565) |
| SF-10.7-08 | MUST | system | scenario | A one-cycle low pulse on i_rst_n_sw starts the complete software reset sequence. *(when: one-cycle low pulse)* | 10.7:s16 (p565) |
| SF-10.7-09 | MUST | system | scenario | A hardware reset clears all FSMs. *(when: hardware reset at any step)* | 10.7:s17 (p565) |
| SF-10.7-10 | MUST | system | scenario | The new low level is served after the write FSM is back in RUN. *(when: new low level during REL)* | 10.7:s18 (p565) |

## 11 Register and programming model

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-11-01 | MUST_NOT | system | none | The IP must not provide software-visible registers; it is configured only by parameters and the static threshold inputs. | 11:s1 (p581) |

## 12 Error handling and recovery

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-12-01 | MUST | system | both | The write must be dropped and o_overflow must pulse for one cycle. *(when: A write is requested while o_full = 1 and writes are not blocked (ERR-001))* | 12:s1 (p587) |
| SF-12-02 | MUST | system | scenario | The next request must be handled independently of the rejected write, with no recovery action required. *(when: After an ERR-001 overflow event)* | 12:s1 (p587) |
| SF-12-03 | MUST | system | both | The ERR-001 overflow status must be cleared by reset. *(when: Reset is applied)* | 12:s1 (p587) |
| SF-12-04 | MUST | system | both | The read must be dropped and o_underflow must pulse for one cycle. *(when: A read is requested while o_empty = 1 and reads are not blocked (ERR-002))* | 12:s2 (p588) |
| SF-12-05 | MUST | system | scenario | The next request must be handled independently of the rejected read, with no recovery action required. *(when: After an ERR-002 underflow event)* | 12:s2 (p588) |
| SF-12-06 | MUST | system | both | The ERR-002 underflow status must be cleared by reset. *(when: Reset is applied)* | 12:s2 (p588) |
| SF-12-07 | MUST | system | both | The request must be dropped and no overflow or underflow pulse must be generated. *(when: A request is made while the software reset blocks the side (ERR-003))* | 12:s3 (p589) |
| SF-12-08 | MAY | master | scenario | The request may be retried after o_sw_rst_busy = 0. *(when: A request was dropped by software reset blocking)* | 12:s3 (p589) |
| SF-12-09 | MUST_NOT | system | none | Behavior is not specified and the condition is not detected; no error interrupt is raised and the integrator must fix the configuration. *(when: Illegal parameter value or threshold changed while in use (ERR-004))* | 12:s4 (p590) |
| SF-12-10 | MUST_NOT | system | both | There must be no sticky error and no error interrupt; the overflow and underflow pulses are the only error status. | 12:s5 (p592) |
| SF-12-11 | MUST | system | both | The pulses for consecutive rejected requests must be consecutive, one per rejected request. *(when: Consecutive requests are rejected)* | 12:s6 (p592) |
| SF-12-12 | MUST_NOT | system | none | There is no ECC or parity data protection, so a corrupted stored word is not detected. *(when: A stored word is corrupted)* | 12:s7 (p592) |

## 13 Performance, power, and area

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-13-01 | MUST | system | both | The FIFO must sustain a throughput of one word per write cycle and one word per read cycle. *(when: Depth is 2 or more)* | 13:s1 (p598) |
| SF-13-02 | MUST | system | both | The FIFO must stream without any gap after the initial latency. *(when: Depth is at least 4 + 2 x PARA_SFIFO_PTR_RETIME)* | 13:s2 (p599) |
| SF-13-03 | MUST | system | both | Empty must fall on the first read edge (PTR_RETIME 0) or second read edge (PTR_RETIME 1) strictly after the write edge. *(when: Any clock ratio)* | 13:s3 (p600) |
| SF-13-04 | MUST | system | both | Full must fall on the first or second write edge strictly after the read edge, depending on PARA_SFIFO_PTR_RETIME. *(when: Any clock ratio)* | 13:s4 (p601) |

## 14.1 Required coding baseline

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-14.1-01 | MUST | system | none | The RTL must comply with VLSIT RTL Design Rules v2 (REF-003) without local exceptions. | 14.1:s1, 14.1:s2 (p612) |
| SF-14.1-02 | MUST | system | none | The RTL must follow the REF-003 items listed: one module per file, structural top, ANSI ports, naming prefixes, FSM names and ENUM_ST_* states, PARA_SFIFO_* parameters, name and comment length limits, u_dont_touch_ instance names. | 14.1:s3 (p612) |
| SF-14.1-03 | MUST | system | scenario | Every flop of the control state must have an asynchronous reset; the memory is the only resetless storage. | 14.1:s4 (p612) |
| SF-14.1-04 | MUST_NOT | system | none | SVA, testbench or prototype code must not be in the synthesis file list. | 14.1:s5 (p612) |
| SF-14.1-05 | MUST | system | none | The library SRAM and its macro model must be located in 000_Common, not in the folder of this IP. | 14.1:s6 (p612) |

## 14.2 RTL hierarchy

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-14.2-01 | MUST | system | none | The hierarchy must have top m_vlsit_sfifo_top with instances u_wr, u_rd and u_mem of modules wr, rd and mem. | 14.2:s1, 14.2:s2, 14.2:s3, 14.2:s4 (p618) |
| SF-14.2-02 | MUST | system | scenario | m_vlsit_sfifo_ram_macro is instantiated as u_ram_macro in m_vlsit_sfifo_mem only when PARA_SFIFO_MEM_USE_MACRO = 1. *(when: only when PARA_SFIFO_MEM_USE_MACRO = 1)* | 14.2:s5 (p622) |
| SF-14.2-03 | MUST | system | none | State ownership: wr owns write pointer, flags, FSM and read-pointer/ack retiming flops; rd owns read-side equivalents; mem owns storage. | 14.2:s6 (p624) |
| SF-14.2-04 | MUST_NOT | system | none | The design must have no register logic and no protocol adapter. | 14.2:s7 (p624) |

## 14.2.1 Ports of the internal modules

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-14.2.1-01 | MUST | system | scenario | Cross-domain inputs i_rd_ptr, i_wr_ptr, i_ack_rd and i_req_wr are captured by one retiming flop when PARA_SFIFO_PTR_RETIME = 1, otherwise used directly. *(when: when PARA_SFIFO_PTR_RETIME = 1)* | 14.2.1:s4, 14.2.1:s10, 14.2.1:s12, 14.2.1:s16 (p634) |
| SF-14.2.1-02 | MUST | system | assertion | o_wr_ptr is a flop output that changes only at the write-clock edge that accepts a write, and resets to 0. | 14.2.1:s5 (p635) |
| SF-14.2.1-03 | MUST | system | assertion | o_mem_wr_en is 1 combinationally when a write is accepted, and the memory stores at the same edge as the pointer increments. | 14.2.1:s6 (p636) |
| SF-14.2.1-04 | MUST | system | assertion | o_mem_wr_addr equals the write pointer modulo the depth. | 14.2.1:s7 (p637) |
| SF-14.2.1-05 | MUST | system | assertion | o_mem_wr_data is a copy of i_wr_data in the same cycle. | 14.2.1:s8 (p638) |
| SF-14.2.1-06 | MUST | system | scenario | o_req_wr is a flop output, reset to 0, set with the busy flop and cleared when REL starts. | 14.2.1:s9 (p639) |
| SF-14.2.1-07 | MUST | system | assertion | o_rd_ptr is a flop output that changes only at the read-clock edge that accepts a read, and resets to 0. | 14.2.1:s13 (p647) |
| SF-14.2.1-08 | MUST | system | assertion | o_mem_rd_addr is combinationally the next read pointer modulo the depth (show-ahead), based on the pointer and i_rd_en, valid every cycle. | 14.2.1:s14 (p648) |
| SF-14.2.1-09 | MUST | system | assertion | i_mem_rd_data is the registered memory output, valid one cycle after the address. | 14.2.1:s15 (p649) |
| SF-14.2.1-10 | MUST | system | assertion | o_ack_rd is a flop output reset to 0, and is 1 from the edge that leaves RST until the edge that leaves ACK. | 14.2.1:s17 (p651) |
| SF-14.2.1-11 | MUST | system | scenario | The memory samples i_wr_en, i_wr_addr and i_wr_data at the write-port clock; i_wr_en qualifies address and data. | 14.2.1:s20, 14.2.1:s21, 14.2.1:s22 (p658) |
| SF-14.2.1-12 | MUST | system | assertion | The memory samples i_rd_addr in every read-clock cycle. | 14.2.1:s24 (p662) |
| SF-14.2.1-13 | MUST | system | assertion | Memory o_rd_data is registered and returns the word at the read address one read-clock cycle later; a word written at the same edge is not seen. | 14.2.1:s25 (p663) |
| SF-14.2.1-14 | MAY | system | none | Macro wrapper pin names follow the library style of VLSIT_CELL_SRAM_1W1R and are exempt from the naming rule. | 14.2.1:s26 (p665) |
| SF-14.2.1-15 | MUST | system | scenario | The macro samples write address and data at the write clock when active-low i_wr_en_n is 0. *(when: CFG-MACRO)* | 14.2.1:s28, 14.2.1:s29, 14.2.1:s30 (p670) |
| SF-14.2.1-16 | MUST | system | assertion | The memory module ties macro i_rd_en_n to 0. *(when: CFG-MACRO)* | 14.2.1:s32 (p674) |
| SF-14.2.1-17 | MUST | system | assertion | The macro samples i_rd_addr every cycle and registers o_rd_data one read-clock cycle after the address. *(when: CFG-MACRO)* | 14.2.1:s33, 14.2.1:s34 (p675) |

## 14.3 Synthesis assumptions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-14.3-01 | MUST | system | none | Synthesis uses top m_vlsit_sfifo_top with the four design files, and the 000_Common wrapper and cell for CFG-MACRO; memory is a flop array by default. | 14.3:s1, 14.3:s5 (p682) |
| SF-14.3-02 | MUST | system | none | Lint uses the project lint set with default_nettype none checking. | 14.3:s6 (p687) |

## 15.1 Scope and strategy

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-15.1-01 | MUST | system | scenario | Each simulation records its seed. | 15.1:s2 (p693) |
| SF-15.1-02 | MUST | system | scenario | The environment drives both clocks from one generator with related edges, including coincident edges, and varies the ratio (equal, 3:2, 2:3, 1:2, 2:1, 3:7, 7:3). | 15.1:s3 (p693) |
| SF-15.1-03 | MUST | system | scenario | The software reset shall be verified on the RTL by TEST-009 and TEST-010, since prototype tests did not include it. *(when: software reset)* | 15.1:s5, 15.2:s9, 15.2:s10 (p695) |

## 15.2 Requirement-based test plan

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-15.2-01 | MUST | system | scenario | All reset values are correct, the FIFO is empty after release, and no operation occurs before release (TEST-001). *(when: hardware reset asserted and released synchronously, including mid-traffic)* | 15.2:s1 (p701) |
| SF-15.2-02 | MUST | system | both | Data is read in order with no loss or duplicate, and o_rd_data is valid whenever o_empty = 0 (TEST-002). *(when: random write and read traffic)* | 15.2:s2 (p702) |
| SF-15.2-03 | MUST | system | both | o_full rises in the cycle after the last place is filled, rejected writes give overflow pulses, and nothing is stored (TEST-003). *(when: FIFO filled and writing continues)* | 15.2:s3 (p703) |
| SF-15.2-04 | MUST | system | both | o_empty rises in the cycle after the last read, and rejected reads give underflow pulses (TEST-004). *(when: reading an empty FIFO or draining a FIFO)* | 15.2:s4 (p704) |
| SF-15.2-05 | MUST | system | scenario | o_full_thr and o_empty_thr assert at the stated occupancy, and thresholds are static (TEST-005). *(when: thresholds swept from 0 to DEPTH while filling and draining)* | 15.2:s5 (p705) |
| SF-15.2-06 | MUST | system | scenario | o_empty and o_full fall after the first or second strictly later edge (TEST-006). *(when: write into empty or read from full FIFO at several ratios and alignments)* | 15.2:s6 (p706) |
| SF-15.2-07 | MUST | system | scenario | The side that is not rate-limited does not stall, and the table of Section 10.4 is reproduced (TEST-007). *(when: continuous write and read, depth at least 4 + 2 x PARA_SFIFO_PTR_RETIME)* | 15.2:s7 (p707) |
| SF-15.2-08 | MUST | system | both | Order and flags are correct at every wrap, and addresses stay within the depth (TEST-008). *(when: depths 2, 3, 5, 7, 12, 16 with many pointer wraps)* | 15.2:s8 (p708) |
| SF-15.2-09 | MUST | system | scenario | Behavior is correct for every ratio and no operation is lost at coincident edges (TEST-011). *(when: equal and listed clock ratios, coincident edges, reset release at different phases)* | 15.2:s11 (p711) |
| SF-15.2-10 | MUST | system | scenario | Results and flag timing are identical for array and SRAM wrapper (TEST-012). *(when: same traffic with array and SRAM wrapper)* | 15.2:s12 (p712) |
| SF-15.2-11 | MUST | system | scenario | Elaboration, lint and simulation pass (TEST-013). *(when: legal extremes: depth 2, 3 and large, data width 1 and large)* | 15.2:s13 (p713) |
| SF-15.2-12 | MUST | system | none | Lint, rule check and port-list review show no violation; every flag, pulse and busy output is a flop (plus block gate) and no synchronizer exists (TEST-014). *(when: static checks)* | 15.2:s14 (p714) |
| SF-15.2-13 | MUST | system | none | All crossing paths close, with no asynchronous clock group or false path between the clocks (TEST-015). *(when: STA with related clocks, several ratios, both pointer options)* | 15.2:s15 (p715) |
| SF-15.2-14 | MUST | system | scenario | The scoreboard regression over depths, pointer options, ratios and seeds shows no error (TEST-017). *(when: scoreboard regression)* | 15.2:s17 (p717) |

## 15.3 Assertions and coverage

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-15.3-01 | MUST | system | none | Assertions and coverage live outside the synthesis file list. | 15.3:s1 (p721) |
| SF-15.3-02 | MUST | system | assertion | Assertions and coverage are disabled. *(when: either hardware reset asserted)* | 15.3:s2 (p721) |
| SF-15.3-03 | MUST_NOT | system | assertion | Assertions do not sample o_rd_data while o_empty is 1. *(when: o_empty is 1)* | 15.3:s3 (p721) |
| SF-15.3-04 | MUST | system | assertion | An unknown value on an input is flagged as a checker error. *(when: a request is sampled with an unknown value on an input)* | 15.3:s4 (p721) |
| SF-15.3-05 | MUST_NOT | slave | assertion | No write is accepted while o_full is 1 (SVA-001). *(when: o_full is 1)* | 15.3:s5 (p725) |
| SF-15.3-06 | MUST_NOT | slave | assertion | No read is accepted while o_empty is 1 (SVA-002). *(when: o_empty is 1)* | 15.3:s6 (p726) |
| SF-15.3-07 | MUST_NOT | slave | assertion | A rejected request changes no pointer (SVA-003). *(when: a request is rejected)* | 15.3:s7 (p727) |
| SF-15.3-08 | MUST | slave | assertion | o_empty is 1 whenever the scoreboard is empty (SVA-004). *(when: scoreboard is empty)* | 15.3:s8 (p728) |
| SF-15.3-09 | MUST | slave | assertion | o_full is 1 whenever the scoreboard holds DEPTH words (SVA-005). *(when: scoreboard holds DEPTH words)* | 15.3:s9 (p729) |
| SF-15.3-10 | MUST | slave | assertion | o_overflow is 1 in the cycle after a rejected, unblocked write and only then (SVA-006). *(when: a write is rejected and unblocked)* | 15.3:s10 (p730) |
| SF-15.3-11 | MUST | slave | assertion | o_underflow is 1 in the cycle after a rejected, unblocked read and only then (SVA-007). *(when: a read is rejected and unblocked)* | 15.3:s11 (p731) |
| SF-15.3-12 | MUST | slave | assertion | The word read equals the word written, per scoreboard (SVA-008). | 15.3:s12 (p732) |
| SF-15.3-13 | MUST_NOT | slave | assertion | No request is accepted and no pulse is raised while blocked by the software reset (SVA-009). *(when: blocked by the software reset)* | 15.3:s13 (p733) |
| SF-15.3-14 | MUST | slave | assertion | o_sw_rst_busy is 1 exactly while the write FSM is not in RUN, one cycle behind the state (SVA-010). | 15.3:s14 (p734) |
| SF-15.3-15 | MUST | slave | assertion | The occupancy is between 0 and DEPTH (SVA-011). | 15.3:s15 (p735) |

## 15.4 Formal, CDC, and RDC

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-15.4-01 | MUST | system | none | Formal analysis is not required in this version; verification is by simulation and assertions. | 15.4:s1 (p747) |
| SF-15.4-02 | MUST | system | none | CDC/RDC analysis is not required because the clocks are synchronous; timed paths are checked by STA (TEST-015). | 15.4:s2 (p748) |

## 16 DFT and testability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-16-01 | MUST_NOT | system | none | The RTL shall contain no latch, no combinational loop, no tri-state, no clock gating and no derived clock, so that scan insertion is possible. | 16:s1 (p754) |
| SF-16-02 | MUST_NOT | system | none | The IP shall have no DFT ports; any test reset override belongs to the SoC wrapper or reset controller. | 16:s2 (p755) |

## 17.1.1 Clock and analysis scenarios

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-17.1.1-01 | MUST | system | scenario | CLK-WR and CLK-RD must be defined so STA knows their common period and phase, e.g. generated clocks of one master or primary clocks with one common LCM-period waveform. *(when: When defining CLK-WR and CLK-RD in the SDC)* | 17.1.1:s3 (p776) |

## 17.1.2 Interface timing budgets

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-17.1.2-01 | MUST | system | scenario | PARA_SFIFO_PTR_RETIME = 1 must be used, or the clock ratio changed. *(when: When the clock ratio makes the interval between a launch edge and a capture edge very small)* | 17.1.2:s9 (p790) |
| SF-17.1.2-02 | MUST | system | none | Required max transition, max capacitance and max fanout follow the project defaults. | 17.1.2:s10 (p790) |

## 17.1.3 Timing exception inventory

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-17.1.3-01 | MUST | system | none | A set_false_path (EXC-001) from ports i_full_thr and i_empty_thr to the write and read domain flag flops removes them from setup and hold checking. *(when: Functional mode)* | 17.1.3:s1 (p796) |
| SF-17.1.3-02 | MUST_NOT | system | scenario | No false path, multicycle path, maximum delay or clock group may be set on the crossing paths; they are ordinary single-cycle paths between related clocks. *(when: On the crossing paths between CLK-WR and CLK-RD)* | 17.1.3:s2 (p798) |
| SF-17.1.3-03 | MUST_NOT | system | scenario | set_clock_groups -asynchronous or set_false_path between CLK-WR and CLK-RD must not be used. | 17.1.3:s3 (p798) |

## 17.2 Physical assumptions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-17.2-01 | SHOULD | system | none | The write and read pointer registers should be placed close to the flag logic of the other domain to shorten the crossing paths. *(when: During floorplan and placement)* | 17.2:s2 (p805) |

## 18 Security, safety, and reliability

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-18-01 | MUST_NOT | system | scenario | The software reset must not erase the FIFO memory contents; no secure clearing or zeroization is provided (REQ-SRST-005). *(when: When a software reset is performed)* | 18:s3 (p819) |
| SF-18-02 | MUST | system | none | The overflow pulse, the underflow pulse and the software reset are the only diagnostics and recovery mechanisms; no other diagnostic, fail-safe state or recovery is provided. | 18:s7 (p823) |

## 20.1 Open items

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-20.1-01 | MUST | system | none | The SRAM wrapper m_vlsit_sfifo_ram_macro must be created in 000_Common/rtl_lib with the RTL, because CFG-MACRO cannot be built without it. *(when: before CFG-MACRO is built)* | 20.1:s3 (p875) |

## 20.2 Assumptions, dependencies and decisions

| ID | Str. | Actor | Check | Statement | Source (p.) |
|---|---|---|---|---|---|
| SF-20.2-01 | MUST | slave | assertion | o_rd_data must always present the word at the read pointer, with no valid output signal. *(when: always (show-ahead read))* | 20.2:s7 (p887) |
| SF-20.2-02 | MUST_NOT | system | none | Sections 7.2 (CDC), 7.4 (power), 11 (registers), 16 (DFT detail) and 18 (security and safety) are not required for the design. | 20.2:s14 (p894) |
| SF-20.2-03 | MUST | system | scenario | Continuous write and continuous read must show only the initial latency and no gap (gap-free streaming). *(when: continuous write and continuous read streaming)* | 20.2:s16 (p896) |
| SF-20.2-04 | MUST | system | both | A request is accepted only if the flag of its own domain allows it at its own edge. *(when: a write or read request is made)* | 20.2:s25 (p905) |
| SF-20.2-05 | MUST_NOT | system | both | There must be no bypass that accepts a write into a full FIFO because a read happens at the same edge. *(when: FIFO full and a read occurs at the same edge as a write)* | 20.2:s25 (p905) |

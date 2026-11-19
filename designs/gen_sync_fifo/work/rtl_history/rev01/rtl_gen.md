# RTL generation report: gen_sync_fifo

Status: **clean** after 1 attempt(s) (agent A15, opus, rtl-v1); cost US$2.11.
Remaining findings: 0 errors, 0 warnings, 0 notes.

This report is the material of gate **D2_rtl**. The code checks below say nothing about whether the RTL is *correct*: the verification (G3/G4), generated independently of this RTL, decides that.

## Synthesis (estimates, RR-43)

| Corner | Library | Cell area (um^2) | Longest combinational path (ps) |
|---|---|---|---|
| tt | gf180mcu_fd_sc_mcu7t5v0__tt_025C_5v00.lib | 37160.3456 | 18167.7 |
| ss | gf180mcu_fd_sc_mcu7t5v0__ss_125C_4v50.lib | 37166.9312 | 33298.42 |

Generic cells: 753. Delay is ABC's estimate without wires, clock-to-output or setup time: a comparison figure, not a timing sign-off.

## Traceability (RR-42)

Rules tagged in the RTL: 148 of 272 (54.4 %). A rule may be untagged because it is about the environment, the documentation or verification, not the RTL; the reviewer checks the list.

<details><summary>Untagged rules</summary>

SF-1.1-03, SF-1.1-05, SF-1.1-13, SF-1.3-02, SF-1.3-03, SF-1.3-04, SF-10.2-02, SF-10.2-04, SF-10.2-07, SF-10.2-08, SF-10.2-09, SF-10.3-01, SF-10.3-02, SF-10.3-03, SF-10.3-04, SF-10.3-05, SF-10.3-06, SF-10.3-07, SF-10.3-08, SF-10.3-13, SF-10.4-01, SF-10.4-02, SF-10.4-04, SF-10.4-06, SF-10.4-07, SF-10.4-08, SF-10.4-09, SF-10.4-10, SF-10.5-03, SF-10.7-07, SF-12-02, SF-12-03, SF-12-05, SF-12-06, SF-12-08, SF-12-10, SF-13-01, SF-13-02, SF-13-03, SF-13-04, SF-14.1-01, SF-14.1-02, SF-14.1-04, SF-14.1-05, SF-15.1-01, SF-15.1-02, SF-15.1-03, SF-15.2-01, SF-15.2-02, SF-15.2-03, SF-15.2-04, SF-15.2-05, SF-15.2-06, SF-15.2-07, SF-15.2-08, SF-15.2-09, SF-15.2-10, SF-15.2-11, SF-15.2-12, SF-15.2-13, SF-15.2-14, SF-15.3-01, SF-15.3-02, SF-15.3-03, SF-15.3-04, SF-15.3-05, SF-15.3-06, SF-15.3-07, SF-15.3-08, SF-15.3-09, SF-15.3-10, SF-15.3-11, SF-15.3-12, SF-15.3-13, SF-15.3-14, SF-15.3-15, SF-16-01, SF-16-02, SF-17.1.1-01, SF-17.1.2-01, SF-17.1.3-03, SF-17.2-01, SF-18-01, SF-2.1-01, SF-2.2-01, SF-2.2-02, SF-20.2-03, SF-3-06, SF-3-09, SF-3-16, SF-3-23, SF-3-31, SF-3-32, SF-3-42, SF-3-45, SF-3-49, SF-3-50, SF-3-51, SF-3-53, SF-3-58, SF-3-59, SF-4-01, SF-4-02, SF-4-03, SF-4-04, SF-4-05, SF-5.3-05, SF-5.4-03, SF-5.4-05, SF-6.2-04, SF-6.2-08, SF-6.3-06, SF-6.3-07, SF-6.3-09, SF-7.2-01, SF-7.3-03, SF-7.3-04, SF-7.3-07, SF-8-03, SF-8-04, SF-8-05, SF-8-12, SF-8-13, SF-8-14

</details>

## Open points stated by the agent

- SRAM cell and wrapper (spec 1.2, 10.5 MEM-002, 14.2, 20.1 OI-003; REQ-RTL-002 / SF-3-56, SF-14.1-05): the folder has neither the cell VLSIT_CELL_SRAM_1W1R nor its model, and the cell's pins are unknown. OI-003 says to create the wrapper with the RTL, so I wrote m_vlsit_sfifo_ram_macro with the port list of 14.2.1. Its body is a stand-in behavioural model: 2^ADDR_W rows, active-low write enable, read register with one cycle of latency, old word returned on a same-edge collision. Before CFG-MACRO is used, someone has to move the wrapper to 000_Common/rtl_lib and replace the body with one instance of VLSIT_CELL_SRAM_1W1R named u_dont_touch_sram. I named the wrapper parameters PARA_SFIFO_RAM_ADDR_W and PARA_SFIFO_RAM_DATA_W myself. In the default configuration the wrapper is not elaborated. It is still in the file list because the generate branch in m_vlsit_sfifo_mem refers to it.
- Software reset request during a running sequence (10.1, 10.7, REQ-SRST-008 / SF-3-47; the G1 decision leaves this unspecified): I added a pending flop. It is set by a low i_rst_n_sw in REL, or by a new falling edge of i_rst_n_sw in REQ or PTR (a second pulse). It starts a new sequence from RUN and is cleared by a hardware reset. A low level that is still present when the FSM reaches HOLD only holds HOLD (SF-3-48). A level held from RUN into REQ/PTR counts as the same request. A second pulse that is still low when the FSM reaches HOLD also leaves a pending request, so one extra sequence runs; this is harmless because writes stay blocked and the FIFO is already flushed.
- Write block term (10.6, REQ-SRST-002, REQ-IF-002): the spec defines block = o_sw_rst_busy OR NOT i_rst_n_sw. I added the pending flop to it, as the cautious choice. In the one RUN cycle before a pending request is taken, busy is 0 as REQ-SRST-006 requires, but o_full stays 1, so a write cannot be accepted and then thrown away by the reset that follows. If no request is pending, the block term is exactly as specified.
- o_sw_rst_busy (REQ-SRST-006, SVA-010): it is a flop loaded with (next write FSM state != RUN). So it is 1 exactly while the FSM is not in RUN: it rises in the cycle after the request is taken and falls in the cycle the FSM is back in RUN. It dips to 0 for one cycle when a new request is served right after REL, as the G1 decision expects.
- o_full_thr while blocked (10.6, DEC-019): the output mux uses (i_full_thr == 0), which needs a small comparator on the static threshold input in front of the 'one gate'. I read this as allowed because the threshold is static and excluded from timing (EXC-001).
- o_empty and o_empty_thr with PARA_SFIFO_PTR_RETIME = 0 (6.2, 10.6): the read block term uses i_req_wr directly. This is a combinational path from a CLK-WR flop through one gate to CLK-RD outputs, as the spec states ('the block term follows the request of the write side with no clock delay'). It is a timed path that STA must close.
- During a software reset sequence the internal full/empty and threshold flops can be loaded from a mixed pair of pointers (one already 0, the other not). The block term hides them at the outputs and stops overflow/underflow pulses. They are correct again once both pointers are 0, before the block ends.
- REF-003 (VLSIT_RTL_Design_Rule.md v2) is not in the folder. The three-line PAR-02 parameter comments, the FIL-05/FIL-06 port layout and grouping, the ENUM type names (t_fsm_srst_wr_e, t_fsm_srst_rd_e) and the `default_nettype none/wire` framing follow my best reading of Sections 8 and 14.1. As Section 8 asks, the derived LPARA_* localparams are in the parameter port list.
- Parameter range (8): the constants are held in 32-bit localparams (2 x DEPTH, 2 x DEPTH - 1). So the design assumes 2 x PARA_SFIFO_DEPTH fits in 32 bits (depth below 2^31). The spec says there is no upper limit, but larger depths are not practical.
- The pointer mod DEPTH address is computed as (ptr >= DEPTH) ? ptr_low - DEPTH_low : ptr_low, in LPARA_ADDR_W bits. This is exact because the result is always below DEPTH (Section 9).
- Not implementable in RTL, so not done: the SDC with related clocks, EXC-001 and no async groups (7.2, 17.1; SF-7.2-01, SF-17.x); the waveform and prototype deliverables (SF-3-58); the regression, assertions and coverage (SF-3-59, SF-15.x); the gap-free depth rule (REQ-PERF-002). The gap-free rule is a measured property of this architecture (OI-002) and must be confirmed on the RTL by TEST-007.
- DEC-014 to DEC-024 are still the spec author's own choices, not confirmed by the designer (Section 20). The RTL implements them as written: look-ahead flags, no full-FIFO bypass (DEC-021), old word returned on a read/write collision (DEC-022), and o_full_thr at 0 until the first edge after reset (DEC-024).

## Findings

None.

## Attempts

- 0: {'error': 0, 'warning': 0, 'info': 0} (changed m_vlsit_sfifo_ram_macro.sv, m_vlsit_sfifo_mem.sv, m_vlsit_sfifo_wr.sv, m_vlsit_sfifo_rd.sv, m_vlsit_sfifo_top.sv)

## For the reviewer of D2_rtl (rules checked by a person)

- RR-03 file headers; RR-24 state machines; RR-32 reset values; RR-33 clock-domain crossings;
  RR-41 widths written with parameters; RR-44 names (docs/RTL_RULES.md).
- The open points above: is each reading the one the specification intends?
- Then: `nnc gate approve gen_sync_fifo D2_rtl --by "<name>" --note "..."`.

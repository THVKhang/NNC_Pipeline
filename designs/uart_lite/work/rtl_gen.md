# RTL generation report: uart_lite

Status: **clean** after 1 attempt(s) (agent A15, opus, rtl-v1); cost US$0.91.
Remaining findings: 0 errors, 0 warnings, 1 notes.

This report is the material of gate **D2_rtl**. The code checks below say nothing about whether the RTL is *correct*: the verification (G3/G4), generated independently of this RTL, decides that.

## Synthesis (estimates, RR-43)

| Corner | Library | Cell area (um^2) | Longest combinational path (ps) |
|---|---|---|---|
| tt | gf180mcu_fd_sc_mcu7t5v0__tt_025C_5v00.lib | 6552.672 | 4097.97 |
| ss | gf180mcu_fd_sc_mcu7t5v0__ss_125C_4v50.lib | 6598.7712 | 7747.83 |

Generic cells: 196. Delay is ABC's estimate without wires, clock-to-output or setup time: a comparison figure, not a timing sign-off.

## Traceability (RR-42)

Rules tagged in the RTL: 124 of 154 (80.5 %). A rule may be untagged because it is about the environment, the documentation or verification, not the RTL; the reviewer checks the list.

<details><summary>Untagged rules</summary>

UL-11-01, UL-12.1-01, UL-12.1-02, UL-12.1-03, UL-12.1-04, UL-12.1-05, UL-12.2-02, UL-12.2-04, UL-12.2-06, UL-12.3-01, UL-12.3-02, UL-12.3-03, UL-12.3-04, UL-12.3-05, UL-12.4-01, UL-12.4-02, UL-12.4-03, UL-12.4-04, UL-12.4-05, UL-12.4-06, UL-12.4-07, UL-12.4-08, UL-13-01, UL-13-02, UL-13-03, UL-13-07, UL-14-11, UL-14-12, UL-14-13, UL-8.1-04

</details>

## Open points stated by the agent

- Spec 4 (REQ-PAR-003) vs RR-11: RR-11 does not allow $error, so the range check for PARA_UART_CLKS_PER_BIT (4 to 65535) uses $error inside a named generate-if wrapped in `ifndef SYNTHESIS` in m_uart_lite.sv. Simulation and lint elaboration stop on an illegal value; synthesis does not check it. This is a SHOULD rule. The reviewer needs to accept this use of the RR-10 exception.
- Spec 4 / INTERFACE.md: the contract lists only PARA_UART_CLKS_PER_BIT. LPARA_UART_HALF_BIT is declared as a localparam in the top module (floor(N/2)) and passed to the receiver as its internal parameter PARA_UART_HALF_BIT. It does not appear on the top module's parameter list.
- Spec 7.4 / 8.2 (D-003): s(E) is the value the first synchronizer flip-flop captures at edge E. Every receiver decision about s(E) (start detect, check at T0+H, data and stop samples) is registered at edge E+2, after the two synchronizer stages. So the delivery and overrun edge is V = M+2, as specified. To detect the falling edge without using the first synchronizer flip-flop in logic, a third flip-flop (r_rxd_prev) stores the previous synchronised value. It resets to 1, as REQ-RST-005 allows.
- Spec 6.2 / 13 (REQ-IMP-004): the spec gives no reset value for internal registers (bit counters, bit indices, TX/RX shift registers, receiver state). Conservative reading: every one of these flip-flops has the asynchronous active-low reset, to 0 or to the idle state.
- Spec 7.2 / 7.3: the transmitter has no separate busy flag. It counts as idle whenever o_tx_ready = 1, which covers true idle and the last stop-bit cycle; in both cases the next state is either a new frame or idle with o_txd = 1. Its counters are not used while o_tx_ready = 1.
- Spec 13 (REQ-IMP-005): the synchronizer flip-flops carry (* keep = "true", async_reg = "true" *). Yosys honours keep, and async_reg is the usual marker for vendor tools. Yosys has no standard attribute that forbids retiming, but it does not retime by default.
- Spec 7.6 (REQ-RX-021 / D-004): if a frame completes at V while the held byte is taken at the same edge, the new byte is loaded and o_rx_valid stays 1. If a take happens with no frame completing, o_rx_valid goes to 0, and o_rx_data / o_rx_frame_err keep their last values (D-007).
- Not implemented in RTL (verification or implementation-flow items): UL-11-01, UL-12.x (testbench, environment and coverage), UL-13-01 / UL-14-13 (50 MHz timing at the slow corner, which needs the synthesis/STA flow; the design is kept to a 16-bit decrement and compare per counter), UL-14-11, UL-14-12.

## Findings

| Severity | Rule | Where | Message |
|---|---|---|---|
| info | RR-10 | m_uart_lite.sv:32 | simulation-only code (not under SYNTHESIS): not synthesized; reviewer: check it models only what the specification asks for |

## Attempts

- 0: {'error': 0, 'warning': 0, 'info': 1} (changed m_uart_lite_tx.sv, m_uart_lite_rx.sv, m_uart_lite.sv)

## For the reviewer of D2_rtl (rules checked by a person)

- RR-03 file headers; RR-24 state machines; RR-32 reset values; RR-33 clock-domain crossings;
  RR-41 widths written with parameters; RR-44 names (docs/RTL_RULES.md).
- The open points above: is each reading the one the specification intends?
- Then: `nnc gate approve uart_lite D2_rtl --by "<name>" --note "..."`.

# RTL generation report: gen_sync_fifo

Status: **clean** after 1 attempt(s) (agent A15, opus, rtl-v1); cost US$0.66.
Remaining findings: 0 errors, 0 warnings, 0 notes.

This report is the material of gate **D2_rtl**. The code checks below say nothing about whether the RTL is *correct*: the verification (G3/G4), generated independently of this RTL, decides that.

## Faults this revision was asked to fix

- formal counterexample on CHK-010
- formal counterexample on CHK-011

## Synthesis (estimates, RR-43)

| Corner | Library | Cell area (um^2) | Longest combinational path (ps) |
|---|---|---|---|
| tt | gf180mcu_fd_sc_mcu7t5v0__tt_025C_5v00.lib | 36863.9936 | 18167.7 |
| ss | gf180mcu_fd_sc_mcu7t5v0__ss_125C_4v50.lib | 36771.7952 | 33298.42 |

Generic cells: 754. Delay is ABC's estimate without wires, clock-to-output or setup time: a comparison figure, not a timing sign-off.

## Traceability (RR-42)

Rules tagged in the RTL: 150 of 272 (55.1 %). A rule may be untagged because it is about the environment, the documentation or verification, not the RTL; the reviewer checks the list.

<details><summary>Untagged rules</summary>

SF-1.1-03, SF-1.1-05, SF-1.1-13, SF-1.3-02, SF-1.3-03, SF-1.3-04, SF-10.2-02, SF-10.2-04, SF-10.2-07, SF-10.2-08, SF-10.2-09, SF-10.3-01, SF-10.3-02, SF-10.3-03, SF-10.3-04, SF-10.3-05, SF-10.3-06, SF-10.3-07, SF-10.3-08, SF-10.3-13, SF-10.4-01, SF-10.4-02, SF-10.4-04, SF-10.4-06, SF-10.4-07, SF-10.4-08, SF-10.4-09, SF-10.4-10, SF-10.5-03, SF-12-02, SF-12-03, SF-12-05, SF-12-06, SF-12-08, SF-12-10, SF-13-01, SF-13-02, SF-13-03, SF-13-04, SF-14.1-01, SF-14.1-02, SF-14.1-04, SF-14.1-05, SF-15.1-01, SF-15.1-02, SF-15.1-03, SF-15.2-01, SF-15.2-02, SF-15.2-03, SF-15.2-04, SF-15.2-05, SF-15.2-06, SF-15.2-07, SF-15.2-08, SF-15.2-09, SF-15.2-10, SF-15.2-11, SF-15.2-12, SF-15.2-13, SF-15.2-14, SF-15.3-01, SF-15.3-02, SF-15.3-03, SF-15.3-04, SF-15.3-05, SF-15.3-06, SF-15.3-07, SF-15.3-08, SF-15.3-09, SF-15.3-10, SF-15.3-11, SF-15.3-12, SF-15.3-13, SF-15.3-14, SF-15.3-15, SF-16-01, SF-16-02, SF-17.1.1-01, SF-17.1.2-01, SF-17.1.3-03, SF-17.2-01, SF-18-01, SF-2.1-01, SF-2.2-01, SF-2.2-02, SF-20.2-03, SF-3-06, SF-3-09, SF-3-16, SF-3-23, SF-3-31, SF-3-32, SF-3-42, SF-3-49, SF-3-50, SF-3-51, SF-3-53, SF-3-58, SF-3-59, SF-4-01, SF-4-02, SF-4-03, SF-4-04, SF-4-05, SF-5.3-05, SF-5.4-03, SF-5.4-05, SF-6.2-04, SF-6.2-08, SF-6.3-06, SF-6.3-07, SF-6.3-09, SF-7.2-01, SF-7.3-03, SF-7.3-04, SF-7.3-07, SF-8-03, SF-8-04, SF-8-05, SF-8-12, SF-8-13, SF-8-14

</details>

## Open points stated by the agent

- Faults 1 and 2 (CHK-010, CHK-011) are both real and have the same cause. Spec 10.6 defines the write block term as only 'o_sw_rst_busy flop OR i_rst_n_sw = 0', and spec 10.7, REQ-SRST-006 and SF-10.7-07 say the FIFO is ready for writes when busy = 0 and i_rst_n_sw = 1. The fix removes reg_sw_rst_pend from w_block in m_vlsit_sfifo_wr.sv. Nothing else changed. o_full, o_full_thr, the write acceptance and o_overflow now all follow the spec's block term, so CHK-010 and CHK-011 should both pass.
- Spec 10.7 / REQ-SRST-008, pending request: the pending flop still moves the write FSM from RUN to REQ, so a request that arrives during a sequence is still served as a new sequence. In that one RUN cycle (busy = 0, i_rst_n_sw = 1) a write is accepted if o_full allows it, and an overflow pulse is raised if the FIFO is full. The new sequence then discards the word. The spec does not say whether a pending request should block writes in that RUN cycle. The approved decision on SF-3-47/SF-10.7-10 says tests must not rely on how pending pulses are remembered. I followed the literal block definition of 10.6, which is the reading the fault report asks for.
- Pending request and the read side: in the pending case the request flop rises at the same write edge as a write-pointer increment. This is safe. The read side blocks as soon as it sees the request, which is no later than it sees the new write pointer. The write FSM resets the pointer in PTR, and the flush checks still wait for both pointers to be 0. Normal requests already behave the same way when a write was accepted in the cycle just before i_rst_n_sw falls.

## Findings

None.

## Attempts

- 0: {'error': 0, 'warning': 0, 'info': 0} (changed m_vlsit_sfifo_wr.sv)

## For the reviewer of D2_rtl (rules checked by a person)

- RR-03 file headers; RR-24 state machines; RR-32 reset values; RR-33 clock-domain crossings;
  RR-41 widths written with parameters; RR-44 names (docs/RTL_RULES.md).
- The open points above: is each reading the one the specification intends?
- Then: `nnc gate approve gen_sync_fifo D2_rtl --by "<name>" --note "..."`.

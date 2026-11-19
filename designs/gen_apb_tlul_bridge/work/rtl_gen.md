# RTL generation report: gen_apb_tlul_bridge

Status: **clean** after 2 attempt(s) (agent A15, opus, rtl-v1); cost US$2.44.
Remaining findings: 0 errors, 0 warnings, 0 notes.

This report is the material of gate **D2_rtl**. The code checks below say nothing about whether the RTL is *correct*: the verification (G3/G4), generated independently of this RTL, decides that.

## Synthesis (estimates, RR-43)

| Corner | Library | Cell area (um^2) | Longest combinational path (ps) |
|---|---|---|---|
| tt | gf180mcu_fd_sc_mcu7t5v0__tt_025C_5v00.lib | 12789.2352 | 9870.56 |
| ss | gf180mcu_fd_sc_mcu7t5v0__ss_125C_4v50.lib | 12789.2352 | 18916.18 |

Generic cells: 189. Delay is ABC's estimate without wires, clock-to-output or setup time: a comparison figure, not a timing sign-off.

## Traceability (RR-42)

Rules tagged in the RTL: 173 of 232 (74.6 %). A rule may be untagged because it is about the environment, the documentation or verification, not the RTL; the reviewer checks the list.

<details><summary>Untagged rules</summary>

BR-15.1-01, BR-15.1-02, BR-15.1-03, BR-15.1-04, BR-15.1-05, BR-15.2-02, BR-15.2-03, BR-15.2-05, BR-15.2-06, BR-15.2-07, BR-15.2-08, BR-15.2-09, BR-15.2-10, BR-15.2-11, BR-15.2-12, BR-15.2-13, BR-15.2-14, BR-15.2-15, BR-15.2-16, BR-15.2-17, BR-15.2-18, BR-15.3-01, BR-15.3-02, BR-15.3-03, BR-15.3-04, BR-15.3-05, BR-15.3-06, BR-15.3-07, BR-15.3-08, BR-15.3-09, BR-15.3-10, BR-15.3-11, BR-20-01, BR-20-03, BR-3-33, BR-3-40, BR-4-02, BR-8-09, TL-T3.2-03, TL-T3.2-04, TL-T3.3-01, TL-T4.1.1-01, TL-T4.1.1-02, TL-T4.1.3.1-01, TL-T4.1.3.2-01, TL-T4.1.3.2.2-01, TL-T4.1.3.3-01, TL-T4.1.3.4-03, TL-T4.1.3.4-05, TL-T4.1.3.4-06, TL-T4.1.3.4-07, TL-T4.1.3.4-08, TL-T4.1.3.5-01, TL-T4.1.3.5-02, TL-T4.1.3.5-03, TL-T4.1.3.5-04, TL-T4.1.3.5-05, TL-T4.1.3.5-06, TL-T4.1.3.5-07

</details>

## Lint waivers (RR-40)

- m_apb_tlul_bridge.sv:50 // WAIVER: PPROT is accepted and ignored (DEC-007, section 14.3) // verilator lint_off UNUSED
- m_apb_tlul_bridge.sv:78 // WAIVER: d_param, d_size, d_sink, d_user present but unused (DEC-006, 14.3) // verilator lint_off UNUSED

## Open points stated by the agent

- REQ-PARAM-001 / BR-3-33, BR-8-09, BR-4-02, BR-8-03 (spec section 8): the spec says an illegal parameter value must be reported 'at elaboration of the verification source set'. The approved decision in REQUIREMENTS.md puts this in a static verification job, using an elaboration-time $fatal in the verification source set. RR-11 also bans system tasks in the RTL. So the RTL adds no parameter-range check, and these rules are left to the verification source set.
- TL-T4.1.3.5-08 (TL-UL reference T4.1.3.5) says a host discards responses with the wrong opcode. The bridge spec (REQ-ERR-004, DEC-008, section 12 ERR-004) instead requires such a response to be accepted and to complete the APB transfer with PSLVERR=1 and PRDATA=0. I followed the bridge spec because silently discarding the response would hang the APB transfer. TL-T4.1.3.5-08 is tagged only where orphan responses are discarded.
- BR-3-18, BR-3-19 (section 3 REQ-IF-004): PREADY is asserted only in an Access cycle because the APB Requester follows REF-001 (ASM-001, section 20). The bridge does not sample PENABLE again in the DONE state. A transfer that starts with PENABLE=1 is never answered; the spec accepts this limitation.
- Verification-only rules BR-3-40, BR-15.x and BR-20-01/BR-20-03 (environment assumptions) cannot be implemented in the RTL and are not tagged.
- Changes to the current RTL: the invalid tag BR-TL-dummy-none in m_tlul_if.sv is replaced by the approved ID TL-T4.1.3.5-08 (host discards orphan responses). I added more valid tags (BR-2.3-03, BR-14.3-01, TL-T3.3-02, BR-6.3-10, BR-6.3-12, BR-12-05, BR-12-07, TL-T3.1-01, TL-T4.1.3.3-02). The logic is unchanged; m_apb_if.sv is unchanged.

## Findings

None.

## Attempts

- 0: {'error': 1, 'warning': 0, 'info': 0} (changed m_apb_if.sv, m_tlul_if.sv, m_apb_tlul_bridge.sv)
- 1: {'error': 0, 'warning': 0, 'info': 0} (changed m_tlul_if.sv, m_apb_tlul_bridge.sv)

## For the reviewer of D2_rtl (rules checked by a person)

- RR-03 file headers; RR-24 state machines; RR-32 reset values; RR-33 clock-domain crossings;
  RR-41 widths written with parameters; RR-44 names (docs/RTL_RULES.md).
- The open points above: is each reading the one the specification intends?
- Then: `nnc gate approve gen_apb_tlul_bridge D2_rtl --by "<name>" --note "..."`.

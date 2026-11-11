# Sign-off packet — sync_fifo

This packet is for the person who decides gate **G4 (sign-off)**: *is this design verified well enough against its specification to release?* It collects only the items that need a human judgement. Everything else is in `work/report.md` (all checks and rules) and `work/triage.md`.

## 1. Summary

- **Requirements (rules):** 272 — NOT_VERIFIED_BY_SIM 98, VERIFIED 174
- **Checks:** 25 — PASS 25
- **Tests:** {'pass': 25}
- **Simulated configuration:** one (parameters {'PARA_SFIFO_DEPTH': 8, 'PARA_SFIFO_DATA_W': 32, 'PARA_SFIFO_PTR_RETIME': 0, 'PARA_SFIFO_MEM_USE_MACRO': 0}, seed 1)
- **Code coverage:** line 99.2 %, block 97.3 %, expression 92.8 %, toggle 70.6 %, functional 100.0 %
- **Mutation score:** 100.0 % (36 of 36 injected faults detected)

## 2. Decisions taken for you

These gates were approved by an AI agent on delegation, not by a qualified person. Read each note.

- **G1_rules** (2026-11-08T05:14:15+00:00): Delegated: 272 rules reviewed; 7 open questions decided from the specification text (Section 10.7, REQ-PERF-002, 15.2) and recorded in rules.md.
- **G2_contract** (2026-11-08T10:37:14+00:00): Range references fixed: CHK-013 now names all 11 assertions (CHK-001..CHK-011); two notes now name the renumbered checks. Checks, kinds, stimulus and rule coverage unchanged. The approved G3 tests were generated from the earlier wording; every test runs with all checkers bound, so behaviour does not depend on this sentence.
- **G3_verif_sources** (2026-11-08T15:30:04+00:00): Checker fix in verif/sva/nnc_chk_sb.sv following triage.md option 1: the reference queue is now empty from the i_clk_wr edge after which o_sw_rst_busy falls (contract CHK-006/CHK-010), not one edge later. Derived from the contract text only; no check removed or relaxed. The designer GabrielHCMUT asked Claude to judge whether to fix it.

## 3. Failures and what they mean

No check fails, and every assertion was exercised.

## 5. What this verification does not cover

**98 requirement(s) cannot be checked by simulation** (static, structural, timing, process...). They need another method: lint, CDC, STA, synthesis, review. First ones:

- SF-1.1-04 (): Pointers must cross between clock domains without synchronizers, as ordinary timed paths closed by STA. — *static_or_structural*
- SF-1.1-06 (): The FIFO must provide write and read requests, full and empty flags, threshold flags, overflow and underflow pulses, show-ahead read, a hardware reset per doma… — *covered_by_other_check*
- SF-1.1-11 (REQ-FUNC-001, REQ-FUNC-002, REQ-FUNC-003, REQ-FUNC-006): The FIFO must support any depth of 2 or more, not only powers of two, and any data width of 1 bit or more. — *static_or_structural*
- SF-1.1-12 (REQ-CLK-003, REQ-PERF-003, REQ-PERF-004): PARA_SFIFO_PTR_RETIME must select either a direct pointer path or one retiming flop in the destination domain. — *not_applicable_to_dut*
- SF-1.2-01 (REQ-RTL-002): The array may be replaced by an SRAM macro with one write port and one read port behind a wrapper. — *not_applicable_to_dut*
- SF-2.1-01 (): The RTL must follow VLSIT RTL Design Rules v2 (REF-003) as the mandatory coding, hierarchy, reset, CDC and naming baseline. — *static_or_structural*
- SF-2.2-01 (): REF-001 (the sibling AsyncGrayFIFO specification) must not override this specification; where they differ, this specification prevails. — *design_guideline*
- SF-2.2-02 (): Conflicts must be resolved by revising the requirement or choosing a compliant implementation, not by a local RTL exception. — *design_guideline*
- SF-3-06 (REQ-FUNC-004): o_full may be 1 while a place is free (conservative flag). — *covered_by_other_check*
- SF-3-09 (REQ-FUNC-005): o_empty may be 1 while a word exists (conservative flag). — *covered_by_other_check*
- SF-3-12 (REQ-FUNC-006): The depth shall be any integer of 2 or more. — *static_or_structural*
- SF-3-20 (REQ-IF-001): The IP shall expose exactly the ports of Section 6.2, and the port list shall not depend on parameters except for widths. — *static_or_structural*
- SF-3-21 (REQ-IF-002): Each listed output shall be driven by a flip-flop; the four flag outputs are combined with the software reset block term by one gate, with no other logic. — *static_or_structural*
- SF-3-22 (REQ-IF-003): o_rd_data shall be the memory output register (one read-clock latency) with no logic after it and no reset. — *static_or_structural*
- SF-3-24 (REQ-CLK-002): The IP shall contain no synchronizer and no clock-domain-crossing cell. — *static_or_structural*
- … 83 more in work/rtm.json

Outside this flow in every case: formal proof, CDC/RDC analysis, static timing, synthesis, DFT.

## 6. Weak spots of the verification itself

Mutation testing changed one RTL line at a time (36 faults). A fault no check notices is a gap, unless it changes nothing visible (an *equivalent* mutant, claimed below by an agent).


Code or cover points never reached (first ones):

- line m_vlsit_sfifo_rd.sv:183
- line m_vlsit_sfifo_wr.sv:195

## 7. Reproduce without NNC

`designs/sync_fifo/sim/` holds a Makefile that runs the same regression with Verilator and cocotb only (Linux or WSL):

```bash
cd designs/sync_fifo/sim
make regression SEED=1 2>&1 | tee sim.log
cd ../../.. && python -m nnc kit-check sync_fifo    # same outcome as the recorded results?
```

## 8. Checklist before signing

Answer every item. Sign only if each one is true, or record why not in the approval note:

- [ ] I have read the delegated decisions of G1_rules and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G2_contract and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G3_verif_sources and agree with them (or I have corrected them).
- [ ] The requirements that simulation cannot check are assigned to another verification method.
- [ ] The unreached code and cover points are unreachable by design or accepted.
- [ ] I reproduced the regression (or CI did) and the outcome matches the report.

Then: `nnc gate approve sync_fifo G4_signoff --by "<your name>" --note "<waivers, open items>"`. The approval is bound to the current results.json: a later run makes it STALE.

# Sign-off packet — gen_sync_fifo

This packet is for the person who decides gate **G4 (sign-off)**: *is this design verified well enough against its specification to release?* It collects only the items that need a human judgement. Everything else is in `work/report.md` (all checks and rules) and `work/triage.md`.

## 1. Summary

- **Requirements (rules):** 272 — FAILED 4, NOT_VERIFIED_BY_SIM 98, VERIFIED 170
- **Checks:** 25 — FAIL 1, PASS 24
- **Tests:** {'fail': 1, 'pass': 24}
- **Simulated configuration:** one (parameters {'PARA_SFIFO_DEPTH': 8, 'PARA_SFIFO_DATA_W': 32, 'PARA_SFIFO_PTR_RETIME': 0, 'PARA_SFIFO_MEM_USE_MACRO': 0}, seed 1)
- **Code coverage:** line 97.3 %, block 94.4 %, expression 97.4 %, toggle 99.5 %, functional 100.0 %
- **Mutation score:** 100.0 % (36 of 36 injected faults detected)

## 2. Decisions taken for you

These gates were approved by an AI agent on delegation, not by a qualified person. Read each note.

- **D1_config** (2026-11-17T10:08:06+00:00): Delegated: default parameter values of the specification; all legal by code check.
- **G1_rules** (2026-11-08T05:14:15+00:00): [carried over from sync_fifo at 2026-11-17T10:08:05+00:00: identical artifacts] Delegated: 272 rules reviewed; 7 open questions decided from the specification text (Section 10.7, REQ-PERF-002, 15.2) and recorded in rules.md.
- **G2_contract** (2026-11-08T10:37:14+00:00): [carried over from sync_fifo at 2026-11-17T10:08:05+00:00: identical artifacts] Range references fixed: CHK-013 now names all 11 assertions (CHK-001..CHK-011); two notes now name the renumbered checks. Checks, kinds, stimulus and rule coverage unchanged. The approved G3 tests were generated from the earlier wording; every test runs with all checkers bound, so behaviour does not depend on this sentence.
- **G3_verif_sources** (2026-11-12T06:00:14+00:00): [carried over from sync_fifo at 2026-11-17T10:08:05+00:00: identical artifacts] Added verif/formal/nnc_env.sv (agent A13, spec only), read: both hardware resets asserted together (SF-3-32, SF-7.3-04), no write/read while the other domain is in reset (same rules), thresholds static while in use. Overflow, underflow, software reset at any time stay free. Tests and checkers unchanged. A person should confirm.

## 3. Failures and what they mean

Checks not passing: CHK-024. The triage agent read the specification, the RTL, the tests and the logs, and gives the most likely cause. It changes nothing; you decide.

### test_chk_024_sw_reset_full_and_rerequest: CHK-008 'o_sw_rst_busy=0 expected after edge (i_rst_n_sw=1) got 1 at 189217.022 ns' (raised by Monitor._wr_edge, test…

- **Most likely:** the specification is unclear or contradicts itself
- **Specification:** These rules point different ways for this stimulus. (1) Supports the check: spec.md:388 (write FSM table) 'ENUM_ST_RUN | ... | i_rst_n_sw = 0: REQ | o_sw_rst_busy 0'. This is the only exit from RUN. spec.md:154 / SF-3-44 REQ-SRST-006: 'The FIFO is ready for writes when o_sw_rst_busy is 0 and i_rst_n_sw is 1' (also spec.md:565). spec.md:925 'Block term: ... busy flop or i_rst_n_sw low (write)'. contract.json:414 CHK-008(b): 'if o_sw_rst_busy=0 and i_rst_n_sw=1, then o_sw_rst_busy=0 after the edg…
- **RTL:** m_vlsit_sfifo_wr.sv:234 w_sw_rst_fall = ~i_rst_n_sw & ~reg_sw_rst_req_d. Lines 242-243: in REQ or PTR, a new falling edge sets reg_sw_rst_pend. Line 246: HOLD keeps pend. Line 202: RUN goes to REQ if (!i_rst_n_sw || reg_sw_rst_pend). Line 269: busy <= (nxt != RUN). Line 135: w_block = busy | ~i_rst_n_sw | reg_sw_rst_pend. Line 285: o_full = w_block | reg_full. The comment at lines 232-233 says this is intended ('A new request ... a new falling edge in REQ or PTR, is remembered and served from R…
- **Options:** Do not weaken CHK-008 or CHK-010. The designer picks one of these: (1) Clarify the spec (recommended first). Decide whether a low that starts in REQ/PTR and is held through HOLD is a 'second pulse' (served again) or part of the current sequence. Decide whether pulses that end before RUN are remembered. If they are remembered, define the hand-over cycle's busy/o_full. Then update spec.md:156, 388, 565, 925 and contract CHK-008 (contract.json:414) and the CHK-024 stimulus (contract.json:783) cons…

### Assertion CHK-010 (nnc_chk_wr.sv a_CHK_010), 1 fail out of 16543 hits, first fail at 189217000 ps (sim.log:187, 230)

- **Most likely:** the specification is unclear or contradicts itself
- **Specification:** contract.json:463 CHK-010: '...cleared ... at the i_clk_wr rising edge after which o_sw_rst_busy goes from 1 to 0 (the occupancy computed at that edge is 0) ... At each i_clk_wr rising edge t' where i_rst_n_sw=1 and o_sw_rst_busy=0 ... o_full == (OCC_W(t) == PARA_SFIFO_DEPTH)'. spec.md:154 REQ-SRST-006: 'The FIFO is ready for writes when o_sw_rst_busy is 0 and i_rst_n_sw is 1.' spec.md:150 REQ-SRST-002: 'Writes remain blocked until o_sw_rst_busy is 0.' spec.md:925: write block term = 'busy flop…
- **RTL:** m_vlsit_sfifo_wr.sv:135 w_block = reg_sw_rst_busy | ~i_rst_n_sw | reg_sw_rst_pend. Line 285: o_full = w_block | reg_full. In the one RUN cycle between E24 (busy 1->0) and E25 (same reconstructed timeline as failure 1, CHK-024(b) j=1), reg_sw_rst_pend=1 was set by the falling edge seen in REQ (wr.sv:243). So o_full=1 although o_sw_rst_busy=0 and i_rst_n_sw=1. o_full_thr = (i_full_thr==0) = 0 (wr.sv:286), which happens to match the model. At E25 the FSM leaves RUN again (wr.sv:202).
- **Options:** This has the same root cause as failure 1, so one decision resolves both. Do not weaken CHK-010. (1) Clarify the spec. Decide whether a pending (remembered) request is legal. If it is, decide how the hand-over cycle looks at the ports: either busy stays 1 from REL straight into the new REQ, or the block term formally includes a pending request. Update spec.md:154, 156, 388, 925, DEC-019, and contract CHK-010/CHK-008/CHK-009 to match. If pend is kept and becomes part of the block definition, the…

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

- line m_vlsit_sfifo_rd.sv:202
- line m_vlsit_sfifo_rd.sv:203
- line m_vlsit_sfifo_wr.sv:226
- line m_vlsit_sfifo_wr.sv:227
- line m_vlsit_sfifo_wr.sv:252
- line m_vlsit_sfifo_wr.sv:253

### Formal check (SymbiYosys)

Every input sequence of up to 20 cycles was searched (one global clock); result {'BOUNDED': 2, 'CEX': 1, 'PROVEN': 6, 'TIMEOUT': 1, 'UNSUPPORTED': 1}. PROVEN holds for every cycle; BOUNDED found no counterexample within the depth. Details: `work/formal.md`.

- **CHK-008 CEX** (trace work/formal/CHK-008.vcd)

Environment assumptions (the formal results hold only for inputs that respect them; an assumption the specification does not require would hide bugs):

- ENV-01: The two hardware resets are asserted together. Once both domains are up,
- ENV-02: No write request until both hardware resets are released. The write domain
- ENV-03: No read request until both hardware resets are released. The read domain
- ENV-04: The static thresholds i_full_thr and i_empty_thr do not change while the

## 7. Reproduce without NNC

`designs/gen_sync_fifo/sim/` holds a Makefile that runs the same regression with Verilator and cocotb only (Linux or WSL):

```bash
cd designs/gen_sync_fifo/sim
make regression SEED=1 2>&1 | tee sim.log
cd ../../.. && python -m nnc kit-check gen_sync_fifo    # same outcome as the recorded results?
```

## 8. Checklist before signing

Answer every item. Sign only if each one is true, or record why not in the approval note:

- [ ] I have read the delegated decisions of D1_config and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G1_rules and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G2_contract and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G3_verif_sources and agree with them (or I have corrected them).
- [ ] The specification question behind “test_chk_024_sw_reset_full_and_rerequest: CHK-008 'o_sw_rst_busy=0 expected after edge (i…” is decided by the specification owner, and the spec, contract or checker is updated.
- [ ] The specification question behind “Assertion CHK-010 (nnc_chk_wr.sv a_CHK_010), 1 fail out of 16543 hits, first fail at 1892…” is decided by the specification owner, and the spec, contract or checker is updated.
- [ ] The requirements that simulation cannot check are assigned to another verification method.
- [ ] The unreached code and cover points are unreachable by design or accepted.
- [ ] Each formal environment assumption (verif/formal/nnc_env.sv) is an obligation the specification really places on the environment.
- [ ] Each formal counterexample or vacuous check is resolved (RTL, checker or environment) or accepted.
- [ ] I reproduced the regression (or CI did) and the outcome matches the report.

Then: `nnc gate approve gen_sync_fifo G4_signoff --by "<your name>" --note "<waivers, open items>"`. The approval is bound to the current results.json: a later run makes it STALE.

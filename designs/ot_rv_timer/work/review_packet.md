# Sign-off packet — ot_rv_timer

This packet is for the person who decides gate **G4 (sign-off)**: *is this design verified well enough against its specification to release?* It collects only the items that need a human judgement. Everything else is in `work/report.md` (all checks and rules) and `work/triage.md`.

## 1. Summary

- **Requirements (rules):** 228 — NOT_VERIFIED_BY_SIM 77, VERIFIED 151
- **Checks:** 35 — PASS 35
- **Tests:** {'pass': 23}
- **Simulated configurations:** 2 runs in 1 configurations (base); see `run_set.json` and the *Run set* table of the report
- **Code coverage:** line 92.3 %, block 87.8 %, expression 61.0 %, toggle 83.1 %, functional 97.4 %
- **Mutation score:** 58.3 % (21 of 36 injected faults detected); 11 survivor(s) proven equivalent by formal, 84.0 % without them; formal on the survivors: {'CEX': 3, 'ERROR': 1, 'PROVEN': 11}

## 2. Decisions taken for you

These gates were approved by an AI agent on delegation, not by a qualified person. Read each note.

- **G1_rules** (2026-11-20T11:04:43+00:00): Not a hardware designer's review. 228 rules kept (54 rejected, 3 merged). 20 spec-lint gaps and the review's open questions answered as spec section 8 decisions D-001..D-020 (made from the documents only; where the documents are silent the verification checks only bounds or the common part of every reading). The last 3 open questions answered: Status interrupts and fatal cause registers out of scope; alert handshake gap checked only through the D-009/D-010 bounds.
- **G2_contract** (2026-11-20T11:15:13+00:00): Not a hardware designer's review. 35 checks (13 assertions, 22 tests) over 151 rules; 77 rules not verified by simulation (mostly standard text outside this IP or obligations of the host). Checks follow spec decisions D-001..D-020: bounds instead of exact cycles where the documents are silent; d_error of instruction fetches and the response to an integrity-fault request are not checked.
- **G3_verif_sources** (2026-11-20T18:07:27+00:00): Not a hardware designer's review. Round 2 after formal: A17 (triage B) - CHK-003 treats a presented (not only accepted) intg-flip request as an alert cause (INT-INTG-002, D-010); CHK-004 stops checking IE_0 after an error-free write to 0x100 of a kind D-013 leaves unchecked (ie_unk) until the next modelled write. Assertions otherwise unchanged; weakening check clean; simulation 23/23. A13 (triage E feedback): ENV-08/ENV-10 track any write to CFG0/TIMER_V_* (RT-8-03); ENV-07 covers every write reaching lanes 0 and 3 of ALERT_TEST (RT-8-15). A13 declined to assume away non-contiguous masks (RT-4.1-05); that question is open.

## 3. Failures and what they mean

No check fails, and every assertion was exercised.

## 4. Hand edits of generated verification code

Generated tests or checkers were edited after triage found them wrong, by hand or by agent A17 (`nnc fix-verif`, which never sees the RTL; code refused any removed or relaxed check; the diff is in work/verif_fix/). An edit must correct the test, never weaken it to hide a design fault.

- - `verif/tests/test_ot_rv_timer.py`: NNC verification fix (fix-verif, triage B): Fault 4 was never fixed: the previous answer changed nothing for CHK-006, so the testbench still started the clock at t=0 while rst_ni held its 2-state default 0. That 0 was never a real (asynchronous) reset assertion: there was no negedge of rst_ni, so the async-reset flops were not reset before the first sampled rising clk_i edge. The SVA a_CHK_006 samples preponed values at that t=0 edge, saw rst_ni=0 with outputs not yet reset, and failed once per seed at time 0. The fix is a power-on reset in setup(), done once per simulation before the clock is started. rst_ni is driven to its inactive level, then to its active level 1 ps later; that negedge asserts the reset asynchronously (RT-2-03). The clock is started only after that, so at every rising edge where rst_ni=0 (including the first one) the reset is really asserted and the outputs must be 0, as D-016/CHK-006 require. The check itself is unchanged: no time-0 exclusion, no disable, no assumption. Later tests skip the power-on pulse so reset_dut's FLUSH_CYCLES behaviour, which lets pending assertions of the previous test complete, is kept. (spec/rv_timer_Design_Specification.md:674 (D-016, RT-8-30): "While rst_ni = 0, o_d_valid, o_alert, o_alert_integ_fail and o_intr_timer_expired shall be 0", spec/rv_timer_Design_Specification.md:548 (RT-2-03): rst_ni "asserted asynchronously and released synchronously", rules.json RT-2-04: "While rst_ni is 0, every register holds its reset value", contract.json:344 (CHK-006): "At every rising edge (and at any other sample point) where rst_ni=0: o_d_valid=0, o_alert=0, o_alert_integ_fail=0 and o_intr_timer_expired=0.")
- - `verif/sva/nnc_chk_reset.sv`: NNC verification fix (fix-verif, triage B): Diagnostic only, as the fault suggested ("add the four output values to the $display"). The CHK-006 failure message now prints rst_ni and the four checked outputs, so the failing output can be identified if a CHK-006 failure occurs again. The assertion property, its enable and its hit/fail counting are unchanged. (spec/rv_timer_Design_Specification.md:674 (D-016, RT-8-30), contract.json:344 (CHK-006))
- - `verif/sva/nnc_chk_alert.sv`: NNC verification fix (fix-verif, triage B): The CHK-003 helper model counted only PutFullData full-word writes to ALERT_TEST as fatal_fault/regwen writes. The specification does not limit the opcode, and a full-word PutPartialData (a_size=2, mask 1111) is a legal 4-byte write that succeeds. So a write of 1 to fatal_fault made with PutPartialData while regwen=1 must count as a qualifying write. wr0_w now accepts opcode 0 or 1, and qual_w and p_clr follow from it. The assertion, the count bound and the 16-cycle bound are unchanged. (rv_timer_Design_Specification.md:625-627 INT-ALERT-003 / RT-5-06, rules.json RT-T5.2.1-03, rv_timer_Design_Specification.md:667 D-009, rv_timer_Design_Specification.md:671 D-013, contract.json CHK-029, TL-T3.1.3.4-05)
- - `verif/sva/nnc_chk_intr.sv`: NNC verification fix (fix-verif, triage B): The CHK-004 IE_0 model updated ie on a byte write (a_size 0, mask 0001) to INTR_ENABLE0 only when the opcode was PutPartialData. D-013 does not restrict the opcode: such a byte write "has the effect of the write". So an error-free PutFullData byte write that sets IE_0=1 left the model at ie=0, and the assertion wrongly required o_intr_timer_expired=0. The byte-write term now uses is_wr (PutFullData or PutPartialData). The update still happens only on a D beat with d_error=0. The assertion itself is unchanged. (rv_timer_Design_Specification.md:671 D-013, rv_timer_Design_Specification.md:663 D-005 / RT-8-07, rules.json CP-T1.8.6-04, TL-T3.1.3.4-04)
- - `verif/sva/nnc_chk_alert.sv`: NNC verification fix (fix-verif, triage B): CHK-003 only stopped checking once a request with i_a_intg_flip=1 was accepted (acc_w). INT-INTG-002 says such a request has a command integrity error that triggers the fatal_fault alert, and it does not say the request must be accepted first. D-010 only gives an upper bound measured from acceptance ('no later than 16 cycles after ... is accepted'), so it does not forbid an earlier alert. D-014 lets the bench present requests while o_a_ready=0. So an alert caused by a flip request that is presented but not yet (or never) accepted is legal, and the old checker reported it as spurious. The fix sets flip_seen, and the same-edge term flip_now_w, at any edge with rst_ni=1, i_a_valid=1 and i_a_intg_flip=1. Every acceptance is also a presentation, so the old trigger is still included. The assertion itself, the count bound, the 16-cycle bound and the cover counter are unchanged, and no assumption was added. (rv_timer_Design_Specification.md:604-606 INT-INTG-002, rv_timer_Design_Specification.md:625-627 INT-ALERT-003, rv_timer_Design_Specification.md:667 D-009 (RT-8-14), rv_timer_Design_Specification.md:668 D-010 (RT-8-16), rv_timer_Design_Specification.md:672 D-014, rv_timer_Design_Specification.md:592-595 INT-TL-003)
- - `verif/sva/nnc_chk_intr.sv`: NNC verification fix (fix-verif, triage B): The CHK-004 ie model was updated only by full-word writes (mask 1111) and aligned byte writes (mask 0001) to 0x100. After an error-free write to 0x100 of any other kind (for example an aligned half-word, or a PutPartialData with a different mask) finished its 2-edge window, the checker still assumed the old ie (0) and required o_intr_timer_expired=0. Per the register-tool rules such a write may be legal and may change IE_0. INT-TL-003 makes it legal stimulus. D-013 says these cases are 'not checked', so the specification does not fix the resulting IE_0. Following the conservative option (2) from the triage, a new flag ie_unk is set at the error-free D beat of a write (intg_flip=0) to 0x100 that is not one of the modelled kinds. It is cleared by reset or by the error-free D beat of the next modelled write, which sets ie again. CHK-004 does not fire while ie_unk=1. All other CHK-004 terms (ie, flip disable, outstanding-write and 2-edge D-beat windows), CHK-005 and the cover counters are unchanged, and no assumption was added. The flip disable here was reviewed and left as it is: a flip request that is not accepted cannot write INTR_ENABLE0/INTR_STATE0, so presentation alone does not affect CHK-004/CHK-005. (rv_timer_Design_Specification.md:663 D-005 (RT-8-07), rv_timer_Design_Specification.md:671 D-013, rv_timer_Design_Specification.md:592-595 INT-TL-003, opentitan_register_tool.md:689-695, CP-T1.8.6-04, RT-T5.4.1-01)

## 5. What this verification does not cover

**77 requirement(s) cannot be checked by simulation** (static, structural, timing, process...). They need another method: lint, CDC, STA, synthesis, review. First ones:

- RT-T6.1-01 (): The racl_policies input must carry the incoming RACL policy vector from a racl_ctrl instance, with the policy selection vector parameter selecting the policy f… — *not_applicable_to_dut*
- RT-1-04 (): The alert sender of rv_timer and the alert receiver of the wrapper both use the synchronous clocking scheme, with no synchronizer flops on the differential pai… — *static_or_structural*
- RT-1-06 (): Every run uses the single fixed configuration; there is no design parameter to vary. — *static_or_structural*
- RT-4.1-03 (): a_user.instr_type is MuBi4True when i_a_instr is 1 and MuBi4False when i_a_instr is 0. — *not_observable_at_interface*
- RT-4.2-02 (): Bit 0 of a_user.cmd_intg must be inverted. — *not_observable_at_interface*
- RT-5-01 (): rv_timer has one alert, fatal_fault, sent through an alert sender. — *static_or_structural*
- TL-T2.2-01 (): Existing TL-UL IP blocks may be used directly in devices that do not need the additional sideband signals. — *not_applicable_to_dut*
- TL-T2.3-01 (): Bus primitives, hosts and peripherals developed with the extended specification can be used with blocks using the base specification. — *not_applicable_to_dut*
- TL-T2.3-02 (): As a receiver, a baseline block ignores the user signals. — *not_applicable_to_dut*
- TL-T2.3-03 (): As a source, a baseline block generates a project-specific default value for the user signals. — *not_applicable_to_dut*
- TL-T3.1.3.1-01 (): Request steering must be a function of the address only; a_source and a_user must not enter into the address calculation. — *not_applicable_to_dut*
- TL-T3.1.3.2-02 (): The fabric architect must ensure AIW covers the host outstanding requests and the maximum source ID growth added by bus primitives. — *not_applicable_to_dut*
- TL-T3.1.3.2-03 (): The fabric must provide enough host ID bits to maintain those ID values. — *not_applicable_to_dut*
- TL-T3.1.3.2.1-01 (): The primitive shifts a_source left and post-pends sub-source bits; on the response it shifts them off, shifting zeros into the top, and returns the result on d… — *not_applicable_to_dut*
- TL-T3.1.3.2.1-02 (): Assertions should ensure no significant bits of a_source are lost in M:1 sockets. — *not_applicable_to_dut*
- … 62 more in work/rtm.json

Outside this flow in every case: formal proof, CDC/RDC analysis, static timing, synthesis, DFT.

## 6. Weak spots of the verification itself

Mutation testing changed one RTL line at a time (36 faults; each in the run that executes its line, a survivor again in every other configuration). A fault no check notices is a gap, unless it changes nothing visible (an *equivalent* mutant, claimed below by an agent).

- M01 `prim_mubi_pkg.sv:72` ne_to_eq (survived in base.s1): **not equivalent (formal counterexample: outputs differ at step 4 after reset: o_d_data (original 11111111111111111111111111111111, mutant 00000000000000000000000000000000), o_d_error (original 1, mutant 0))** — a change of behaviour no check noticed, unless the input sequence breaks an environment rule; agent: claimed equivalent: mubi4_test_false_loose is only called inside assertions in prim_alert_receiver. It drives no logic and no port, so the change is unobservable.
- M04 `prim_subreg.sv:75` and_to_or (survived in base.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: The line sits in the gen_rc branch, which is elaborated only for SwAccessRC. rv_timer has no RC fields, so the branch never exists and qs=q regardless.
- M11 `rv_timer_reg_top.sv:81` one_to_zero (survived in base.s1): **equivalent, proven by formal** (no input sequence changes an output); **gap** — The sticky err_q is never set, so intg_err_o is asserted only while the corrupted request is on the bus. The fatal alert is no longer repeated until reset.
- M12 `prim_diff_decode.sv:234` negate_if (survived in base.s1): formal ERROR (nothing concluded); claimed equivalent: In the synchronous decoder this inverts the reset of diff_pq/level_q. The only effects are that diff_pq/level_q are held at 0 instead of tracking the input. rise_o/fall_o could matter only on the sen…
- M14 `tlul_adapter_reg.sv:221` or_to_and (survived in base.s1): **not equivalent (formal counterexample: outputs differ at step 4 after reset: o_d_data (original 11111111111111111111111111111111, mutant 00000000000000000000000000000000))** — a change of behaviour no check noticed, unless the input sequence breaks an environment rule; agent: **gap** — The mask becomes (error_i && err_internal) || wr_req. For error reads, d_data now carries the register's read data instead of all-ones (for example a Get with a_size=3 to 0x110, or a Get to an unmapp…
- M19 `prim_alert_sender.sv:223` negate_if (survived in base.s1): **not equivalent (formal counterexample: outputs differ at step 30 after reset: o_alert (original 0, mutant 1))** — a change of behaviour no check noticed, unless the input sequence breaks an environment rule; agent: **gap** — The sender leaves AlertHsPhase2 while ack is still high instead of waiting for ack to deassert. The four-phase handshake is cut short and the repeat period of a fatal alert shrinks (6 cycles instead …
- M21 `prim_secded_inv_64_57_dec.sv:62` eq_to_ne (survived in base.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: data_o of prim_secded_inv_64_57_dec is left unconnected in every user (tlul_cmd_intg_chk, tlul_rsp_intg_chk). Only syndrome/err_o are used, and they do not depend on data_o.
- M22 `rv_timer_reg_top.sv:583` zero_to_one (survived in base.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: The mutant makes addrmiss=1 when neither reg_re nor reg_we is active. error_i is only sampled when a request is accepted. In that case reg_re/reg_we is 1, unless err_internal is set, where the respon…
- M27 `prim_alert_sender.sv:171` zero_to_one (survived in base.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: The line is in gen_recov, which is elaborated only for IsFatal=0. rv_timer instantiates the sender with IsFatal=1, so the line does not exist in the design.
- M29 `prim_alert_receiver.sv:202` zero_to_one (survived in base.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: send_ping in the InitReq state only feeds ping_tog_pd, which is forced to 0 by send_init in the same state. The change has no effect.
- M30 `prim_secded_inv_39_32_dec.sv:49` eq_to_ne (survived in base.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: data_o of prim_secded_inv_39_32_dec is left unconnected in tlul_data_integ_dec. Only err_o is used, and it depends on the syndrome, not on data_o.
- M31 `prim_alert_receiver.sv:249` one_to_zero (survived in base.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: The clamp only triggers on a sigint on the alert pair outside InitReq/InitAckWait. In this integration the only sigint is the deliberate one during the post-reset init sequence, where the receiver is…
- M32 `prim_alert_receiver.sv:226` or_to_and (survived in base.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: ping_req_i is tied to 0 in the wrapper, so ping_rise and ping_pending_q are always 0. send_ping is 0 under both || and &&.
- M34 `prim_onehot_check.sv:108` or_to_and (survived in base.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: oh0_err and enable_err are both 0 unless the write-enable vector is multi-hot or a write enable fires without en_i. Both need an internal fault, because write enables require reg_we and an address hi…
- M36 `prim_diff_decode.sv:235` zero_to_one (survived in base.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: A reset value of 1 for diff_pq in the sender's ping decoder creates a spurious fall event (ping_event=1) in the first cycle after reset. That cycle coincides with the receiver's init sigint on the ac…

9 requirement(s) below the mutation threshold of 85.0 %: AH-T1.3.2-01, AH-T1.3.2-02, AH-T1.3.2-03, CP-T1.9.1-04, RT-4.2-03, RT-5-02, RT-5-05, RT-8-16, RT-T6.3-01

Code or cover points never reached (first ones):

- line ot_rv_timer_nnc.sv:23
- line ot_rv_timer_nnc.sv:36
- line ot_rv_timer_nnc.sv:39
- line ot_rv_timer_nnc.sv:42
- line prim_alert_receiver.sv:48
- line prim_alert_receiver.sv:49
- line prim_alert_receiver.sv:98
- line prim_alert_receiver.sv:101
- line prim_alert_receiver.sv:102
- line prim_alert_receiver.sv:104

### Formal check (SymbiYosys)

Every input sequence of up to 32 cycles was searched (one global clock); result {'BOUNDED': 2, 'CEX': 1, 'PROVEN': 7, 'TIMEOUT': 1, 'UNSUPPORTED': 2}. PROVEN holds for every cycle; BOUNDED found no counterexample within the depth. Details: `work/formal.md`.

- **CHK-008 CEX** (trace work/formal/CHK-008.vcd)

Environment assumptions (the formal results hold only for inputs that respect them; an assumption the specification does not require would hide bugs):

- ENV-01: no request is issued while reset is asserted (RT-8-29, RT-2-03, CP-T1.5.2-04)
- ENV-09: no request in the first cycle after reset release (RT-8-29)
- ENV-02: TL-UL host rule - once a_valid is raised it stays raised and all A-channel
- ENV-03: a_param is driven to 0 (RT-8-34)
- ENV-04: requests at offset 0x200 and above are not used (RT-8-20)
- ENV-05: a write (PutFullData / PutPartialData) with i_a_instr = 1 is not used (RT-8-18)
- ENV-06: distinct a_source per outstanding request (RT-8-25, TL-T3.1.3.2-01)
- ENV-07: the combined ALERT_TEST write (fatal_fault = 1 together with regwen = 0) is not used;
- ENV-08: CFG0 and TIMER_V_LOWER0/UPPER0 are written (any write request to these words) only
- ENV-10: the timer is not activated while a CFG0 / TIMER_V_* write is still in flight, so those

## 7. Reproduce without NNC

`designs/ot_rv_timer/sim/` holds a Makefile that runs the same regression with Verilator and cocotb only (Linux or WSL):

```bash
cd designs/ot_rv_timer/sim
make regression SEED=1 2>&1 | tee sim.log
cd ../../.. && python -m nnc kit-check ot_rv_timer    # same outcome as the recorded results?
```

The kit reproduces the primary run base.s1; the other runs differ only by the settings in `run_set.json`.

## 8. Checklist before signing

Answer every item. Sign only if each one is true, or record why not in the approval note:

- [ ] I have read the delegated decisions of G1_rules and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G2_contract and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G3_verif_sources and agree with them (or I have corrected them).
- [ ] Each hand edit of the generated tests and checkers corrects the test and weakens no requirement.
- [ ] The requirements that simulation cannot check are assigned to another verification method.
- [ ] Each surviving mutant is either truly equivalent or a known gap I accept.
- [ ] The unreached code and cover points are unreachable by design or accepted.
- [ ] Each formal environment assumption (verif/formal/nnc_env.sv) is an obligation the specification really places on the environment.
- [ ] Each formal counterexample or vacuous check is resolved (RTL, checker or environment) or accepted.
- [ ] I reproduced the regression (or CI did) and the outcome matches the report.

Then: `nnc gate approve ot_rv_timer G4_signoff --by "<your name>" --note "<waivers, open items>"`. The approval is bound to the current results.json: a later run makes it STALE.

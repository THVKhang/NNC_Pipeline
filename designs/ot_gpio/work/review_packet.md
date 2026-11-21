# Sign-off packet — ot_gpio

This packet is for the person who decides gate **G4 (sign-off)**: *is this design verified well enough against its specification to release?* It collects only the items that need a human judgement. Everything else is in `work/report.md` (all checks and rules) and `work/triage.md`.

## 1. Summary

- **Requirements (rules):** 268 — NOT_VERIFIED_BY_SIM 80, VERIFIED 188
- **Checks:** 38 — PASS 38
- **Tests:** {'pass': 26}
- **Simulated configurations:** 5 runs in 4 configurations (base, sync_off, straps_off, min); see `run_set.json` and the *Run set* table of the report
- **Code coverage:** line 52.5 %, block 44.5 %, expression 20.6 %, toggle 84.0 %, functional 90.0 %
- **Mutation score:** 58.3 % (21 of 36 injected faults detected); 9 survivor(s) proven equivalent by formal, 77.8 % without them; formal on the survivors: {'CEX': 4, 'ERROR': 2, 'PROVEN': 9}

## 2. Decisions taken for you

These gates were approved by an AI agent on delegation, not by a qualified person. Read each note.

- **G1_rules** (2026-11-21T01:04:06+00:00): Not a hardware designer's review. 227 rules kept (45 rejected, 7 merged). 19 spec-lint gaps answered as spec section 10 decisions D-001..D-022 (documents only; where they are silent or disagree, only the common part or a bound is checked). 8 open questions answered on delegation: run set = all four parameter combinations; counting convention for D-018 at the ports; status-type interrupts, pings and sender encoding-error timing out of scope. Where a kept rule conflicts with a decision, the decision limits the check: GP-T5.11-02/GP-T5.12-02 (MASKED_OE read bits 31:16) by D-002, CP-T1.8.4-05 (INTR_STATE not qualified by INTR_ENABLE) by D-004. Open for the G4 reviewer: D-002, D-004.
- **G2_contract** (2026-11-21T01:13:18+00:00): Not a hardware designer's review. 38 checks (13 assertions, 25 tests) over 188 rules; 80 rules not verifiable by simulation (mostly standard text outside this IP, status-type interrupts, pings, obligations of the host). Checks follow D-001..D-022: bounds instead of exact cycles where the documents are silent (filter D-007, latencies D-018); MASKED_OE read bits 31:16 unchecked (D-002); INTR_STATE checked only where both readings of D-004 agree. Run set: base (2 seeds), sync_off, straps_off, min.
- **G3_verif_sources** (2026-11-21T10:56:40+00:00): Not a hardware designer's review. Re-approved after fix-verif from the formal counterexample of CHK-003: a request with i_a_intg_flip=1 counts as an alert cause from i_a_valid=1, not only from its A handshake (INT-INTG-002, INT-TL-003, D-017 gives only an upper bound). Traffic with i_a_intg_flip=0 is still never a cause. Candidate passes 26/26 tests and 13/13 assertions in all 5 runs.

## 3. Failures and what they mean

No check fails, and every assertion was exercised.

## 4. Hand edits of generated verification code

Generated tests or checkers were edited after triage found them wrong, by hand or by agent A17 (`nnc fix-verif`, which never sees the RTL; code refused any removed or relaxed check; the diff is in work/verif_fix/). An edit must correct the test, never weaken it to hide a design fault.

- - `verif/sva/nnc_chk_intr.sv`: NNC verification fix (fix-verif, triage B): CHK-006 updated shadow_en only at the D handshake and checked every bit with shadow_en=0 between the A handshake and the D handshake. During that window, under D-channel back-pressure, the design may already apply the write. No document says whether a write takes effect at A or at D, and D-018 only binds o_intr_gpio outside the 2 cycles after INTR_ENABLE changes. The fix masks only the bits that an outstanding INTR_ENABLE write sets from 0 to 1, from its A handshake until Ed; the existing masks at Ed and Ed+1 are kept. Bits that are 0 in both the old and the new value are still checked on every edge, and so are the bits a write clears (1 to 0) from Ed+2. (D-018 (spec/gpio_Design_Specification.md:1165), D-004 (spec:1151), CP-T1.8.6-04, CP-T1.8.4-03, GP-10-05, contract.json CHK-006)
- - `verif/sva/nnc_chk_reset.sv`: NNC verification fix (fix-verif, triage B): CHK-008 fired at the t=0 clock edge. At that point rst_ni has never been asserted: there was no falling edge and no clock edge processed with rst_ni=0, and no document defines a power-on state. The check now starts at the first reset assertion, which is the first falling edge of rst_ni or the first rising clock edge processed with rst_ni=0. The flag is never cleared, so every later edge with rst_ni=0 is checked, including the first clock edge after rst_ni falls asynchronously (contract CHK-008). The hit counter used the condition `!(!rst_ni) && (!rst_ni)`, which is never true. It now counts the edges where the check is active. The fail message now prints the six output values to show the root cause. (D-016 (spec/gpio_Design_Specification.md:1163), INT-RST-001 (spec:1017-1019), D-003 (spec:1150), GP-10-31, GP-10-03, GP-2-06, contract.json CHK-008)
- - `verif/sva/nnc_chk_tlhost.sv`: NNC verification fix (fix-verif, triage B): Rule (f) compared a 49-bit truncation of a 122-bit concatenation. It covered only i_strap_en, i_gpio, i_d_ready, i_a_intg_flip, i_a_instr and i_a_data[12:0], and silently dropped the other A-channel inputs. The vector is now 121 bits wide and covers every input that rule (f) names: i_a_valid, opcode, param, size, source, address, mask, all of a_data, instr, intg_flip, d_ready, i_gpio and i_strap_en. This strengthens the check. rst_ni is left out on purpose: its assertion is asynchronous by specification (INT-RST-001), and the old checker never covered it either. (contract.json CHK-011 rule (f), INT-CLK-001 (spec:1010-1011), INT-CLK-002 (spec:1013-1015), GP-2-04, INT-RST-001 (spec:1017))
- - `verif/tests/test_ot_gpio.py`: NNC verification fix (fix-verif, triage B): With GpioAsyncOn=0 the test bench drove every input right after the falling edge of clk_i. Contract CHK-011 rule (f) and INT-CLK-002 require these inputs to change only just after rising edges. With GpioAsyncOn=0, the TL-UL A-channel driver (_a_loop), the i_d_ready driver (_d_loop), i_gpio (set_gpio and gpio_pulse) and i_strap_en (Env.reset, strap_sequence and the regression strap phase) now drive 1 step after a rising edge, through the new helper Env.drive_sync. Sampling is unchanged: ReadOnly at the falling edge. Edge numbering stays the same, because a value driven after rising edge N is first sampled at N+1, which equals edge() at the falling edge that follows. In set_gpio, gpio_pulse and the strap code, edge numbers are taken from the value returned after the drive. gpio_pulse still keeps v_on for exactly n edges. Runs with GpioAsyncOn=1 are unchanged: drive_sync drives at once there, and the loops keep the falling-edge drive. No expected value or check was changed. (INT-CLK-001 (spec:1010-1011), INT-CLK-002 (spec:1013-1015), GP-2-02, GP-2-04, contract.json CHK-011 rule (f), contract.json CHK-021 stimulus step 3)
- - `verif/sva/nnc_chk_alert.sv`: NNC verification fix (fix-verif, triage B): CHK-003 counted a request with i_a_intg_flip=1 as an alert cause only once it was accepted (A handshake). The spec does not say that. INT-INTG-002 says that a request with i_a_intg_flip=1 has a command integrity error, which is a fatal TL-UL bus integrity fault that triggers fatal_fault. In TL-UL, a request exists as soon as a_valid=1. INT-TL-003 says a presented request stays stable until accepted. D-017 gives only an upper bound (16 cycles), measured from acceptance; it does not forbid an earlier alert. So the checker now records cause (a) in any cycle with i_a_valid=1 and i_a_intg_flip=1, both in the sticky intg_seen_q and in the same-cycle term. This makes the checker follow the spec without weakening anything the spec requires. Traffic with i_a_intg_flip=0 (INT-INTG-001) still never counts as a cause. Cause (b), CHK-001/002, the assertion, its counters and the CHK-003 reference are unchanged. (spec/gpio_Design_Specification.md:1079-1081 [INT-INTG-002], spec/gpio_Design_Specification.md:1076-1077 [INT-INTG-001], spec/gpio_Design_Specification.md:1067-1068 [INT-TL-003], spec/gpio_Design_Specification.md:1164 D-017, spec/gpio_Design_Specification.md:963 Security Alerts fatal_fault, spec/opentitan_tlul_bus_specification.md:83 a_valid)

## 5. What this verification does not cover

**80 requirement(s) cannot be checked by simulation** (static, structural, timing, process...). They need another method: lint, CDC, STA, synthesis, review. First ones:

- GP-T2.2-06 (): A change in output value is reflected in the input register with a corresponding filter delay. — *not_applicable_to_dut*
- GP-T3.2.3-02 (): GPIO peripheral inputs not connected to a chip input are tied to constant zero. — *not_applicable_to_dut*
- GP-T4.4-01 (): Each component should be granted access only to the per-pin registers of its own GPIOs, while software managing all GPIOs keeps using the 32-bit registers. — *design_guideline*
- GP-1-03 (): Ping requests must never be issued. — *not_observable_at_interface*
- GP-4.1-02 (): a_user.rsvd is 0. — *not_observable_at_interface*
- TL-T2.2-01 (): Existing TL-UL IP blocks may be used directly in devices that do not need the additional user sideband signals. — *design_guideline*
- TL-T2.3-01 (): Bus primitives, hosts and peripherals developed with the extended specification can be used with blocks using the base specification. — *static_or_structural*
- TL-T2.3-02 (): A baseline block as receiver ignores the user signals. — *not_applicable_to_dut*
- TL-T2.3-03 (): A baseline block as source generates a project-specific default value for the user signals. — *not_applicable_to_dut*
- TL-T3.1.1-01 (): TL-UL host drivers in this library are not required to drive valid signals LOW for at least 100 cycles during reset, unlike the TileLink 1.7.1 requirement. — *not_applicable_to_dut*
- TL-T3.1.3.1-01 (): All request steering to a device must be a function of the address only; a_source and a_user do not enter into address calculation. — *not_applicable_to_dut*
- TL-T3.1.3.2-02 (): The fabric architect must ensure AIW is large enough for outstanding host requests plus maximum source ID growth added by bus primitives. — *not_applicable_to_dut*
- TL-T3.1.3.2-03 (): The fabric must provide enough host ID bits to maintain the converted host ID values. — *not_applicable_to_dut*
- TL-T3.1.3.2.1-01 (): The primitive shifts incoming a_source left and post-pends its sub-source bits. — *not_applicable_to_dut*
- TL-T3.1.3.2.1-02 (): The sub-source bits are shifted off with zeros shifted into the top, and the result is returned on the originator's d_source. — *not_applicable_to_dut*
- … 65 more in work/rtm.json

Outside this flow in every case: formal proof, CDC/RDC analysis, static timing, synthesis, DFT.

## 6. Weak spots of the verification itself

Mutation testing changed one RTL line at a time (36 faults; each in the run that executes its line, a survivor again in every other configuration). A fault no check notices is a gap, unless it changes nothing visible (an *equivalent* mutant, claimed below by an agent).

- M01 `prim_alert_receiver.sv:226` or_to_and (survived in base.s1, sync_off.s1, straps_off.s1, min.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: Line is in the InitAckWait state, which is reached only after init_trig_i is MuBi4True. The wrapper ties init_trig_i to MuBi4False and ping_req_i to 0, so InitAckWait is unreachable and ping_rise and…
- M02 `prim_filter_ctr.sv:59` zero_to_one (survived in base.s1, sync_off.s1, straps_off.s1, min.s1): **not equivalent (formal counterexample: outputs differ at step 6 after reset: o_straps_data (original 00000000000000000000000000000000, mutant 00000000010000000000000000010000))** — a change of behaviour no check noticed, unless the input sequence breaks an environment rule; agent: **gap** — The filter's stored value would reset to 1 instead of 0. If CTRL_EN_INPUT_FILTER is enabled within about 15 cycles of reset with i_gpio=0, DATA_IN and edge or level interrupt detection would see a sp…
- M03 `tlul_err.sv:26` eq_to_ne (survived in base.s1, sync_off.s1, straps_off.s1, min.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: op_full feeds only instr_wr_err, which is nonzero only when instr_type is MuBi4True. In that case tlul_adapter_reg's instr_error is already 1, because en_ifetch_i is tied to MuBi4False, so err_intern…
- M06 `tlul_err.sv:84` zero_to_one (survived in base.s1, sync_off.s1, straps_off.s1, min.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: This is the default case, which only a_size=3 reaches. mask_chk is also 0 in that case, so a_config_allowed stays 0 and err_o stays 1 whatever addr_sz_chk is.
- M08 `prim_onehot_check.sv:96` and_to_or (survived in base.s1, sync_off.s1, straps_off.s1, min.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: and_tree is used only for the address check. prim_reg_we_check instantiates prim_onehot_check with AddrCheck=0, so addr_err is tied to 0 and and_tree is unused.
- M12 `prim_mubi_pkg.sv:72` ne_to_eq (survived in base.s1, sync_off.s1, straps_off.s1, min.s1): **not equivalent (formal counterexample: outputs differ at step 4 after reset: o_d_data (original 11111111111111111111111111111111, mutant 00000000000000000000000000000000), o_d_error (original 1, mutant 0))** — a change of behaviour no check noticed, unless the input sequence breaks an environment rule; agent: **gap** — The loose false test on en_ifetch (MuBi4False) would return 0, so instr_error would be 0. An instruction-fetch Get (i_a_instr=1) would then complete with d_error=0 and real data instead of d_error=1.
- M15 `tlul_adapter_reg.sv:219` zero_to_one (survived in base.s1, sync_off.s1, straps_off.s1, min.s1): **not equivalent (formal counterexample: outputs differ at step 0 after reset: o_d_error (original 0, mutant 1))** — a change of behaviour no check noticed, unless the input sequence breaks an environment rule; agent: **gap** — error_q would reset to 1, so o_d_error would be 1 after reset until the first access, whereas it is 0 in the original. This is visible on the port, although d_valid is 0.
- M18 `gpio_reg_top.sv:80` or_to_and (survived in base.s1, sync_off.s1, straps_off.s1, min.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: err_q only latches the integrity error. intg_err_o is still the combinational OR of intg_err and reg_we_err, and intg_err is gated by a_valid. The fatal prim_alert_sender latches the alert request it…
- M19 `prim_secded_inv_64_57_dec.sv:39` eq_to_ne (survived in base.s1, sync_off.s1, straps_off.s1, min.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: data_o of the 64_57 decoder is left unconnected in tlul_cmd_intg_chk and tlul_rsp_intg_chk. Only err_o is used, and it depends on the syndrome, not on data_o.
- M21 `prim_alert_receiver.sv:190` one_to_zero (survived in base.s1, sync_off.s1, straps_off.s1, min.s1): **not equivalent (formal counterexample: outputs differ at step 30 after reset: o_alert (original 0, mutant 1))** — a change of behaviour no check noticed, unless the input sequence breaks an environment rule; agent: **gap** — The receiver would drop ack one cycle early while the alert is still high. The handshake would finish one cycle sooner, so the spacing between repeated o_alert pulses after an integrity error would c…
- M23 `prim_secded_inv_39_32_dec.sv:51` eq_to_ne (survived in base.s1, sync_off.s1, straps_off.s1, min.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: data_o of the 39_32 decoder is left unconnected in tlul_data_integ_dec. Only err_o is used, and it does not depend on data_o.
- M30 `prim_diff_decode.sv:234` negate_if (survived in base.s1, sync_off.s1, straps_off.s1, min.s1): formal ERROR (nothing concluded); claimed equivalent: This is the synchronous diff decoder, which is used because AlertAsyncOn=0 in the wrapper. The mutant holds diff_pq and level_q at 0 while rst_ni=1. diff_pq only affects rise, fall and event, and tho…
- M31 `prim_diff_decode.sv:236` zero_to_one (survived in base.s1, sync_off.s1, straps_off.s1, min.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: level_q is read only when sigint_o=1. After reset release the pairs hold their reset values (no sigint), and the first clock edge loads level_q from level_o (0) before the init sigint starts. The res…
- M33 `gpio_reg_top.sv:78` negate_if (survived in base.s1, sync_off.s1, straps_off.s1, min.s1): formal ERROR (nothing concluded); claimed equivalent: err_q would be held at 0 while rst_ni=1. intg_err_o is still the combinational intg_err | reg_we_err, which is nonzero only during an a_valid cycle with an error. The fatal alert sender latches the r…
- M36 `gpio.sv:116` zero_to_one (survived in base.s1, sync_off.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: The line is in gen_no_strap_sample, which is elaborated only when GpioAsHwStrapsEn=0. Run base.s1 uses GpioAsHwStrapsEn=1, so the line does not exist in that configuration and port behaviour is uncha…

13 requirement(s) below the mutation threshold of 85.0 %: AH-T1.3.2-01, AH-T1.3.2-03, GP-10-07, GP-10-08, GP-10-19, GP-3-01, GP-4.1-01, GP-4.1-03, GP-5-02, GP-5-05, GP-T2.2-05, GP-T3.2.3-03, GP-T5.17-01

Code or cover points never reached (first ones):

- line gpio.sv:42
- line gpio.sv:143
- line gpio_reg_top.sv:25
- line gpio_reg_top.sv:50
- line gpio_reg_top.sv:170
- line gpio_reg_top.sv:176
- line gpio_reg_top.sv:1384
- line gpio_reg_top.sv:1424
- line gpio_reg_top.sv:1464
- line gpio_reg_top.sv:1504

### Formal check (SymbiYosys)

Every input sequence of up to 32 cycles was searched (one global clock); result {'PROVEN': 10, 'TIMEOUT': 1, 'UNSUPPORTED': 2}. PROVEN holds for every cycle; BOUNDED found no counterexample within the depth. Details: `work/formal.md`.


Environment assumptions (the formal results hold only for inputs that respect them; an assumption the specification does not require would hide bugs):

- ENV-01: i_a_valid is 0 while rst_ni = 0 and in the first cycle after release (GP-10-30, TL-T3.1.1-01)
- ENV-02: TL-UL host rule: a pending A request (a_valid=1, a_ready=0) stays valid
- ENV-03: a distinct a_source per outstanding request (GP-10-26, TL-T3.1.3.2-01)
- ENV-04: requests at offset 0x400 and above are not used (GP-10-21)
- ENV-05: no write (PutFullData/PutPartialData) with i_a_instr = 1 (GP-10-19)
- ENV-06: no combined ALERT_TEST (offset 0x0C) write that sets fatal_fault and clears regwen
- ENV-07: i_strap_en = 0 while rst_ni = 0 and for at least 4 cycles after release (GP-10-10)
- ENV-08: at the first rising edge of i_strap_en, i_gpio has been constant for the
- ENV-09: i_gpio stays constant for 8 cycles after that rising edge (GP-10-10, GP-T3.2.3.1-01)
- ENV-10: after a write that may change CTRL_EN_INPUT_FILTER[i] (CTRL_EN_INPUT_FILTER at 0x3C,

## 7. Reproduce without NNC

`designs/ot_gpio/sim/` holds a Makefile that runs the same regression with Verilator and cocotb only (Linux or WSL):

```bash
cd designs/ot_gpio/sim
make regression SEED=1 2>&1 | tee sim.log
cd ../../.. && python -m nnc kit-check ot_gpio    # same outcome as the recorded results?
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
- [ ] I reproduced the regression (or CI did) and the outcome matches the report.

Then: `nnc gate approve ot_gpio G4_signoff --by "<your name>" --note "<waivers, open items>"`. The approval is bound to the current results.json: a later run makes it STALE.

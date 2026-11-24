# Sign-off packet — c_pcpi_div

This packet is for the person who decides gate **G4 (sign-off)**: *is this design verified well enough against its specification to release?* It collects only the items that need a human judgement. Everything else is in `work/report.md` (all checks and rules) and `work/triage.md`.

## 1. Summary

- **Requirements (rules):** 23 — NOT_VERIFIED_BY_SIM 16, VERIFIED 7
- **Checks:** 9 — PASS 9
- **Tests:** {'pass': 7}
- **Simulated configurations:** 2 runs in 2 configurations (base, xrand); see `run_set.json` and the *Run set* table of the report
- **Code coverage:** line 100.0 %, block 100.0 %, expression 100.0 %, toggle 100.0 %, functional 85.7 %
- **Mutation score:** 100.0 % (12 of 12 injected faults detected)

## 2. Decisions taken for you

These gates were approved by an AI agent on delegation, not by a qualified person. Read each note.

- **G1_rules** (2026-11-23T09:57:44+00:00): Not a hardware designer's review. Blind run (ROADMAP 21.6): approved as produced, no rule edited. 23 rules kept, 5 rejected; rules of the M extension and of the CPU side of PCPI that do not apply to a division core are left to the contract. The 4 open questions (16-cycle timeout, pcpi_wait timing, pcpi_wr timing, software register constraints) are left open, not answered.
- **G2_contract** (2026-11-23T09:59:43+00:00): Not a hardware designer's review. Blind run (ROADMAP 21.6): approved as produced. 9 checks (3 assertions, 6 tests); 16 rules not verified (CPU side of PCPI, multiplication, RV64, software guidelines). Assumptions for the G4 reviewer: RV32M encodings from the listing table, result valid with pcpi_ready, 200-cycle completion bound.
- **G3_verif_sources** (2026-11-23T10:18:38+00:00): Not a hardware designer's review. Blind run (ROADMAP 21.6): re-approved after the A17 fix of the one fault triage judged B (test_c_pcpi_div.py execute() issued the next instruction without the one-cycle pcpi_valid=0 the contract requires). The fix adds that cycle; the weakening check found nothing; CHK-001 then passes. Nothing else changed.

## 3. Failures and what they mean

No check fails, and every assertion was exercised.

## 4. Hand edits of generated verification code

Generated tests or checkers were edited after triage found them wrong, by hand or by agent A17 (`nnc fix-verif`, which never sees the RTL; code refused any removed or relaxed check; the diff is in work/verif_fix/). An edit must correct the test, never weaken it to hide a design fault.

- - `verif/tests/test_c_pcpi_div.py`: NNC verification fix (fix-verif, triage B): execute() drove pcpi_valid=1 in the same mid-cycle where the previous deassert (or the last idle cycle) had just driven pcpi_valid=0. That overwrote the 0, so with gap=0 no rising edge ever saw pcpi_valid=0 between two instructions. The test's own model still recorded valid=0, so it missed this. The contract says the master deasserts pcpi_valid on the cycle after pcpi_ready, so this stimulus was illegal and set off the CHK-001 failures. The fix waits one clock cycle (await next_cycle) at the start of execute() before driving the issue. Now the pcpi_valid=0 that was already driven and checked is really sampled at a rising edge, so every instruction is preceded by at least one pcpi_valid=0 edge. CHK-001 in the SVA, the cover points and all expected values are unchanged. (contract.json:223 (CHK-008 stimulus: 'then drive pcpi_valid=0 on the next cycle'), contract.json:327 ('Legal master stimulus ... deasserts pcpi_valid on the following cycle'), spec/c_pcpi_div_Design_Specification.md:62-66 (PD-T1.1-06: keep pcpi_wait asserted until pcpi_ready), spec/c_pcpi_div_Design_Specification.md:48-52 (PD-T1.1-01))

## 5. What this verification does not cover

**16 requirement(s) cannot be checked by simulation** (static, structural, timing, process...). They need another method: lint, CDC, STA, synthesis, review. First ones:

- PD-T1.1-01 (): The core asserts pcpi_valid, outputs the instruction word on pcpi_insn, and outputs the rs1 and rs2 register values on pcpi_rs1 and pcpi_rs2. — *not_applicable_to_dut*
- PD-T1.1-04 (): The PicoRV32 core decodes the rd field of the instruction and writes the pcpi_rd value to the respective register. — *not_applicable_to_dut*
- PD-T1.1-05 (): An illegal instruction exception is raised and the respective interrupt handler is called. — *not_applicable_to_dut*
- PD-T1.1-07 (): Asserting pcpi_wait prevents the PicoRV32 core from raising an illegal instruction exception. — *not_applicable_to_dut*
- RVM-T1.1-01 (): mul multiplies rs1 by rs2 as XLEN-bit values and writes the lower XLEN bits of the product to the destination register. — *not_applicable_to_dut*
- RVM-T1.1-02 (): mulh, mulhu and mulhsu return the upper XLEN bits of the 2×XLEN-bit product for signed×signed, unsigned×unsigned and signed rs1×unsigned rs2 respectively. — *not_applicable_to_dut*
- RVM-T1.1-03 (): Use mulh (or mulhu/mulhsu if appropriate) rdh,rs1,rs2 followed by mul rdl,rs1,rs2 to obtain both halves. — *design_guideline*
- RVM-T1.1-04 (): Source specifiers rs1 and rs2 must be in the same order in both instructions, and rdh must not be the same as rs1 or rs2. — *design_guideline*
- RVM-T1.1-05 (): Microarchitectures may fuse the two instructions into a single multiply operation instead of two separate multiplies. — *not_applicable_to_dut*
- RVM-T1.1-06 (): mulw multiplies the lower 32 bits of the source registers and writes the sign extension of the lower 32 bits of the result to the destination register. — *not_applicable_to_dut*
- RVM-T1.1-07 (): Signed arguments must be proper 32-bit signed values and unsigned arguments must have their upper 32 bits clear. — *not_applicable_to_dut*
- RVM-T1.2-03 (): Use div rdq,rs1,rs2 followed by rem rdr,rs1,rs2 (or divu and remu if appropriate). — *design_guideline*
- RVM-T1.2-04 (): rdq must not be the same register as rs1 or rs2. — *design_guideline*
- RVM-T1.2-05 (): Microarchitectures may fuse the two instructions into a single divide operation instead of two separate divides. — *not_observable_at_interface*
- RVM-T1.2-06 (): divw and divuw divide the lower 32 bits of rs1 by those of rs2 as signed and unsigned and write the 32-bit quotient sign-extended to 64 bits in rd; remw and re… — *not_applicable_to_dut*
- … 1 more in work/rtm.json

Outside this flow in every case: formal proof, CDC/RDC analysis, static timing, synthesis, DFT.

## 6. Weak spots of the verification itself

Mutation testing changed one RTL line at a time (12 faults). A fault no check notices is a gap, unless it changes nothing visible (an *equivalent* mutant, claimed below by an agent).


Code or cover points never reached (first ones):

- functional nnc_cov.sv:0 COVP-005
- functional nnc_cov.sv:0 COVP-009
- functional nnc_cov.sv:0 COVP-029
- functional nnc_cov.sv:0 COVP-030
- functional nnc_cov.sv:0 COVP-033

## 7. Reproduce without NNC

`designs/c_pcpi_div/sim/` holds a Makefile that runs the same regression with Verilator and cocotb only (Linux or WSL):

```bash
cd designs/c_pcpi_div/sim
make regression SEED=1 2>&1 | tee sim.log
cd ../../.. && python -m nnc kit-check c_pcpi_div    # same outcome as the recorded results?
```

The kit reproduces the primary run base.s1; the other runs differ only by the settings in `run_set.json`.

## 8. Checklist before signing

Answer every item. Sign only if each one is true, or record why not in the approval note:

- [ ] I have read the delegated decisions of G1_rules and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G2_contract and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G3_verif_sources and agree with them (or I have corrected them).
- [ ] Each hand edit of the generated tests and checkers corrects the test and weakens no requirement.
- [ ] The requirements that simulation cannot check are assigned to another verification method.
- [ ] The unreached code and cover points are unreachable by design or accepted.
- [ ] I reproduced the regression (or CI did) and the outcome matches the report.

Then: `nnc gate approve c_pcpi_div G4_signoff --by "<your name>" --note "<waivers, open items>"`. The approval is bound to the current results.json: a later run makes it STALE.

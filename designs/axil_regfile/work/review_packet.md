# Sign-off packet — axil_regfile

This packet is for the person who decides gate **G4 (sign-off)**: *is this design verified well enough against its specification to release?* It collects only the items that need a human judgement. Everything else is in `work/report.md` (all checks and rules) and `work/triage.md`.

## 1. Summary

- **Requirements (rules):** 193 — NOT_VERIFIED_BY_SIM 22, VERIFIED 171
- **Checks:** 37 — PASS 37
- **Tests:** {'pass': 21}
- **Simulated configurations:** 7 runs in 4 configurations (base, min, max, full_a7); see `run_set.json` and the *Run set* table of the report
- **Code coverage:** line 100.0 %, block 100.0 %, expression 95.7 %, toggle 97.2 %, functional 100.0 %
- **Mutation score:** 93.1 % (27 of 29 injected faults detected); 2 survivor(s) proven equivalent by formal, 100.0 % without them; formal on the survivors: {'PROVEN': 2}

## 2. Decisions taken for you

These gates were approved by an AI agent on delegation, not by a qualified person. Read each note.

- **D1_config** (2026-11-19T11:01:14+00:00): Delegated: final configuration = specification defaults (PARA_NUM_REGS=8, PARA_ADDR_W=8).
- **D2_rtl** (2026-11-19T11:05:52+00:00): Delegated review of work/rtl_gen.md: clean at the first attempt (0 errors, 0 warnings; 1 note: the simulation-only $error on illegal parameters; 1 waiver for the ignored prot and address bits). Registered outputs, every flop reset, single clock, no CDC; 141/193 rules tagged. The 7 open points follow the specification. OPEN, not resolved by this approval: REQ-IMP-001 timing. ABC estimates the longest combinational path at 16.9 ns (TT) and 31.5 ns (SS 125 C) against a 20 ns period; likely the serial OR-chain read mux and the 32-bit decode compare. Not a sign-off STA figure, but it must be decided by the designer at G4. Correctness is left to the verification. Not a hardware designer's review.
- **G1_rules** (2026-11-19T10:55:31+00:00): Delegated review: 193 rules kept after A2 review (12 fixed, 3 merged, 5 rejected); 0 open questions (27 of 28 answered from the specification, 1 duplicate). Spec decisions Q-001..003 and the 5 spec-lint gaps (D-014..018) were made on delegation before ingest. Not a hardware designer's review.
- **G2_contract** (2026-11-19T11:01:13+00:00): Delegated review: 37 checks (17 assertions, 20 tests) over 171 of 193 rules; 22 not verifiable by simulation (14 static/structural, 6 environment obligations, 1 covered by another check, 1 design guideline). Every check selected. Not a hardware designer's review.
- **G3_verif_sources** (2026-11-20T05:35:47+00:00): Delegated review: 5 SVA checkers + nnc_cov (40 cover points), test_axil_regfile.py (A7, valid at attempt 2), formal env with 4 assumptions: reset from time zero for 2 cycles (REQ-VER-006) and valid/payload stability on AW, W, AR until the transfer, ended by reset (REQ-VER-001, REQ-VER-007). Ready signals, status, addresses, strobes and prot are left free as the specification allows. Not a hardware designer's review.

## 3. Failures and what they mean

No check fails, and every assertion was exercised.

## 5. What this verification does not cover

**22 requirement(s) cannot be checked by simulation** (static, structural, timing, process...). They need another method: lint, CDC, STA, synthesis, review. First ones:

- RF-3-02 (): A value required 'from edge n' holds starting in cycle n+1 until another requirement changes it, such as a held state ending or a reset. — *covered_by_other_check*
- RF-4-04 (REQ-PAR-001): The block must behave as the specification states for every legal combination of PARA_NUM_REGS (1 to 16) and PARA_ADDR_W (7 to 16). — *static_or_structural*
- RF-4-05 (REQ-PAR-002): LPARA_REGS_W shall be a local parameter equal to PARA_NUM_REGS*32 that cannot be overridden from outside the module. — *static_or_structural*
- RF-4-06 (REQ-PAR-003): The RTL should stop elaboration with an error message when PARA_NUM_REGS or PARA_ADDR_W is outside its legal range. — *static_or_structural*
- RF-4-07 (REQ-PAR-004): Behaviour with illegal parameter values is unspecified and must not be verified. — *static_or_structural*
- RF-10.2-05 (REQ-EXT-005): Latency, throughput, reset and back-pressure behaviour must be the same for every legal parameter combination. — *static_or_structural*
- RF-11-05 (): The verification must run every configuration listed in the Configurations table (CFG-BASE, CFG-MIN, CFG-MAX, CFG-FULL-A7), as defined in run_set.json. — *static_or_structural*
- RF-12.1-01 (REQ-VER-001): The manager shall keep valid at 1 and its payload stable from the cycle it rises until the edge of its transfer. — *not_applicable_to_dut*
- RF-12.1-03 (REQ-VER-003): The environment shall release i_rst_n synchronously to i_clk so that the release meets recovery and removal times of the flip-flops. — *not_applicable_to_dut*
- RF-12.1-05 (REQ-VER-004): The environment shall drive i_status synchronously to i_clk, changing it only away from rising edges. — *not_applicable_to_dut*
- RF-12.1-06 (REQ-VER-005): The testbench shall drive defined values (no X or Z) on all inputs. — *not_applicable_to_dut*
- RF-12.1-09 (REQ-VER-010): No output check applies, including REQ-VER-010, before the first assertion of i_rst_n, as outputs are undefined. — *not_applicable_to_dut*
- RF-12.1-11 (REQ-RST-010, REQ-VER-001): A valid at 1 after R1 is a new request and carries the REQ-VER-001 obligation from that cycle. — *not_applicable_to_dut*
- RF-13-01 (REQ-IMP-001): The block shall meet timing at 50 MHz (20 ns clock period) in the GF180MCU technology at the worst-case corner of the sign-off flow. — *static_or_structural*
- RF-13-02 (REQ-IMP-002): The RTL shall follow the coding rules in docs/RTL_RULES.md (REF-002). — *static_or_structural*
- … 7 more in work/rtm.json

Outside this flow in every case: formal proof, CDC/RDC analysis, static timing, synthesis, DFT.

## 6. Weak spots of the verification itself

Mutation testing changed one RTL line at a time (29 faults; each in the run that executes its line, a survivor again in every other configuration). A fault no check notices is a gap, unless it changes nothing visible (an *equivalent* mutant, claimed below by an agent).

- M11 `m_axil_regfile.sv:245` zero_to_one (survived in base.s1, min.s1, max.s1, full_a7.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: The reset value of r_aw_okay is only read through wr_okay when aw_hs=0, and that only matters when wr_commit=1, which needs r_aw_held=1. r_aw_held is only set after an AW transfer, which loads r_aw_o…
- M15 `m_axil_regfile.sv:244` zero_to_one (survived in base.s1, min.s1, max.s1, full_a7.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: The reset value of r_aw_reg_hit is only used via wr_reg_hit when aw_hs=0, and then only with wr_commit=1, which needs r_aw_held=1. That state is only reached after an AW transfer has loaded r_aw_reg_…

### Formal check (SymbiYosys)

Every input sequence of up to 32 cycles was searched (one global clock); result {'BOUNDED': 1, 'PROVEN': 15, 'UNSUPPORTED': 1}. PROVEN holds for every cycle; BOUNDED found no counterexample within the depth. Details: `work/formal.md`.


Environment assumptions (the formal results hold only for inputs that respect them; an assumption the specification does not require would hide bugs):

- ENV-01: i_rst_n is held at 0 from time zero for at least 2 cycles. Cycle 0 is
- ENV-02: Write address channel. When AWVALID is 1 and no AW transfer happens at
- ENV-03: Write data channel. When WVALID is 1 and no W transfer happens at that
- ENV-04: Read address channel. When ARVALID is 1 and no AR transfer happens at

## 7. Reproduce without NNC

`designs/axil_regfile/sim/` holds a Makefile that runs the same regression with Verilator and cocotb only (Linux or WSL):

```bash
cd designs/axil_regfile/sim
make regression SEED=1 2>&1 | tee sim.log
cd ../../.. && python -m nnc kit-check axil_regfile    # same outcome as the recorded results?
```

The kit reproduces the primary run base.s1; the other runs differ only by the settings in `run_set.json`.

## 8. Checklist before signing

Answer every item. Sign only if each one is true, or record why not in the approval note:

- [ ] I have read the delegated decisions of D1_config and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of D2_rtl and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G1_rules and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G2_contract and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G3_verif_sources and agree with them (or I have corrected them).
- [ ] The requirements that simulation cannot check are assigned to another verification method.
- [ ] Each surviving mutant is either truly equivalent or a known gap I accept.
- [ ] Each formal environment assumption (verif/formal/nnc_env.sv) is an obligation the specification really places on the environment.
- [ ] I reproduced the regression (or CI did) and the outcome matches the report.

Then: `nnc gate approve axil_regfile G4_signoff --by "<your name>" --note "<waivers, open items>"`. The approval is bound to the current results.json: a later run makes it STALE.

# Sign-off packet — spi_master

This packet is for the person who decides gate **G4 (sign-off)**: *is this design verified well enough against its specification to release?* It collects only the items that need a human judgement. Everything else is in `work/report.md` (all checks and rules) and `work/triage.md`.

## 1. Summary

- **Requirements (rules):** 206 — NOT_VERIFIED_BY_SIM 32, VERIFIED 174
- **Checks:** 41 — PASS 41
- **Tests:** {'pass': 15}
- **Simulated configurations:** 5 runs in 3 configurations (base, min, max); see `run_set.json` and the *Run set* table of the report
- **Code coverage:** line 94.8 %, block 93.8 %, expression 98.2 %, toggle 95.2 %, functional 94.9 %
- **Mutation score:** 91.7 % (33 of 36 injected faults detected); 3 survivor(s) proven equivalent by formal, 100.0 % without them; formal on the survivors: {'PROVEN': 3}

## 2. Decisions taken for you

These gates were approved by an AI agent on delegation, not by a qualified person. Read each note.

- **D1_config** (2026-11-19T07:19:21+00:00): Delegated: final configuration = specification defaults (D=4).
- **D2_rtl** (2026-11-19T10:42:33+00:00): Delegated review of work/rtl_gen.md: clean after 2 attempts (0 errors, 0 warnings; 1 note: the simulation-only $error on an illegal PARA_SPI_CLK_DIV). 4-state FSM (Idle/Xfer/Pause/Trail), every flop reset, single clock, no CDC; 167/206 rules tagged, untagged ones are sections 11-13 (verification/implementation) and 5-02, 8-10/11. The 5 open points follow the specification (DEC-012..016, ENV-007). GF180 TT 8462 um^2; SS path 10.75 ns < 20 ns. Correctness is left to the verification. Not a hardware designer's review.
- **G1_rules** (2026-11-19T07:13:20+00:00): Delegated review: 206 rules kept after A2 review (18 fixed, 6 merged, 14 rejected); the 3 open questions answered (burst lengths per configuration, reset timing in simulation at a falling edge, SS 125 C corner). Spec decisions OQ-001..007 and the 5 spec-lint gaps (DEC-012..016) were made on delegation before ingest. Not a hardware designer's review.
- **G2_contract** (2026-11-19T07:19:20+00:00): Delegated review: 41 checks (27 assertions, 14 tests) over 174 of 206 rules; 32 rules not verifiable by simulation (18 static/structural, 12 not applicable to the DUT, 2 design guidelines). Every check selected. Not a hardware designer's review.
- **G3_verif_sources** (2026-11-20T07:06:06+00:00): Re-approval after nnc fix-verif --from formal (agent A17, 1 attempt, formal triage B on all 6 counterexamples, min configuration D = 1). Diff read: nnc_chk_mosi.sv and nnc_chk_sclk.sv now load CPHA_b / CPOL_b only at a burst-start handshake (o_cs_n = 1), as the specification defines them (term CPOL_b/CPHA_b, REQ-MODE-001..003, REQ-ERR-001); one line each, nothing removed. The formal environment is unchanged on purpose: ENV-003 is not assumed, so formal still checks that mode changes during a burst have no effect. Candidate: 15/15 tests, 0 failing assertions in 5 runs. Not a hardware designer's review.

## 3. Failures and what they mean

No check fails, and every assertion was exercised.

## 4. Hand edits of generated verification code

Generated tests or checkers were edited after triage found them wrong, by hand or by agent A17 (`nnc fix-verif`, which never sees the RTL; code refused any removed or relaxed check; the diff is in work/verif_fix/). An edit must correct the test, never weaken it to hide a design fault.

- - `verif/sva/nnc_chk_flow.sv`: NNC verification fix (fix-verif, triage B): CHK-010 compared o_sclk in Pause with the current i_cpol input. The spec requires o_sclk = CPOL_b, the value captured at the burst-start acceptance edge. Inputs changed during the burst must have no effect, and test_chk_033 changes them on purpose. The checker now captures CPOL_b when a handshake happens with o_cs_n=1 and compares against that value. The check is still exact and still runs in every test, test 033 included. (REQ-FLOW-003, REQ-MODE-001, REQ-MODE-002, REQ-MODE-003, REQ-ERR-001, REQ-SCLK-003, Section 3 term CPOL_b, contract CHK-010)
- - `verif/sva/nnc_chk_reset.sv`: NNC verification fix (fix-verif, triage B): Fault 5: the previous 'assert final' changed nothing (287 fails before and after), so this simulator evaluated it like a plain immediate assertion, at the first unsettled moment of the time step. CHK-015 now copies all outputs and i_cpol on each 1->0 transition of i_rst_n. It copies them again on every further change in that same time step, so the copy ends up holding the settled values. The copy is judged at the first event of any later time step (at the latest the next i_clk edge, so before any further rising edge). A copy still waiting at the end of simulation is judged in the final block. Same output list, exact values, every 1->0 transition. Fault 6: the one remaining fail per run is at 5000 ps, the first i_clk edge. There i_rst_n has been 0 since time zero with no 1->0 transition, so this edge is the first point where the reset can act on the flops that drive o_cs_n/o_mosi (REQ-IMP-003/004). The check sampled before that edge settled. CHK-016 now starts checking at a 1->0 transition of i_rst_n, or after the first rising edge in reset when the reset is held from time zero (ENV-008). Edges in the exact time step of a 1->0 transition are skipped (ENV-007/GAP-001); CHK-015 checks the same outputs there after settling. All later rising and falling edges in reset are checked with exact values. The hit counter now counts only edges that are actually checked. (REQ-RST-001 (spec:113), REQ-RST-002..006 (spec:115-123), ENV-007 / GAP-001 (spec:454), ENV-008 (spec:456), REQ-IMP-003/004 (spec:504-506), contract.json CHK-015 behavior (line 411), contract.json CHK-016 behavior (line 433), rules.json:5911 decision (reset asserted/released at falling edge))
- - `verif/tests/test_spi_master.py`: NNC verification fix (fix-verif, triage B): Faults 1 and 2: wait_idle returned in the FallingEdge callback, before the ReadOnly cycle monitor had logged the current cycle. With D=1 the Idle condition is already true in the o_cs_n rise cycle R, so the rise at R was not yet in env.cs_rise. wait_idle now waits for ReadOnly and steps to the next falling edge before returning. waitc is unchanged, so callers that depend on its exact timing keep it. The exact checks rises == [A+17D] are unchanged. Fault 3: with CPHA_b=1, o_mosi in the lead cycles A..A+D-1 is the last value from earlier traffic, and that traffic differed between the ref and err runs. An identical single-byte warm-up burst in mode M now runs before each run, so both start from the same o_mosi. The full exact trace comparison over A..R is kept. Faults 6 and 7: setup() asserted i_rst_n in the same time step as the clock (re)start, so a clock edge coincided with the assertion (illegal per ENV-007/GAP-001). It also changed i_cpol in that step while o_cs_n could still be 0. Now i_rst_n is asserted first, i_cpol/i_cpha change a quarter period later in a separate time step, and the clock starts another quarter period later. At time zero, i_cpol/i_cpha get values at once so they are never X (ENV-008). The CHK-016 and CHK-017 checkers are not changed. (REQ-CS-002, REQ-CS-006, REQ-CMD-007, REQ-CMD-008, DEC-016, Section 10 corner case D = 1, Section 8 timing table (18·D single-byte period), REQ-MODE-003, REQ-MOSI-004, REQ-MOSI-006, Section 7.5 note (CPHA_b = 1 keeps previous value until SCLK edge 1), contract CHK-012, contract CHK-028, contract CHK-030, contract CHK-033, ENV-007, GAP-001, DEC-012, ENV-008, GAP-002, REQ-RST-002, REQ-RST-003, REQ-RST-004, REQ-RST-005, REQ-RST-006, contract CHK-016, contract CHK-017)
- - `verif/sva/nnc_chk_mosi.sv`: NNC verification fix (fix-verif, triage B): ph_r (the checker's CPHA_b) was reloaded from i_cpha at every command handshake, including continuation/Pause handshakes while o_cs_n=0. The spec defines CPHA_b as i_cpha captured at the first acceptance edge of the burst and requires it to be used for the whole burst; changes while o_cs_n=0 have no effect (REQ-ERR-001). ph_r is now loaded only on hs && o_cs_n (burst start) and held across continuation and Pause handshakes; d_r, cnt, mp_r and busy stay per-handshake. No assertion, expected value or hit counter was relaxed. (spec:57 CPOL_b, CPHA_b: values captured at the first acceptance edge of the current burst, REQ-MODE-001, REQ-MODE-002, REQ-MODE-003, REQ-FLOW-005, REQ-ERR-001, REQ-MOSI-002, REQ-MOSI-004, REQ-MOSI-007, contract.json assumptions[0] (burst start => CPOL_b/CPHA_b captured), CHK-011, CHK-012, CHK-013, CHK-014)
- - `verif/sva/nnc_chk_sclk.sv`: NNC verification fix (fix-verif, triage B): t_cpol_b (the checker's CPOL_b) was reloaded from i_cpol at every command handshake, including continuation/Pause handshakes while o_cs_n=0. The spec defines CPOL_b as i_cpol captured at the first acceptance edge of the burst and requires it to be used for the whole burst (including Pause and Trail); changes while o_cs_n=0 have no effect. t_cpol_b is now loaded only on hs_cmd && o_cs_n (burst start) and held for the burst; t_act, t_cnt and t_last_b stay per-handshake. This fixes CHK-023, CHK-025 and the CHK-027 use of t_cpol_b. No assertion was relaxed. (spec:57 CPOL_b, CPHA_b: values captured at the first acceptance edge of the current burst, REQ-MODE-001, REQ-MODE-002, REQ-MODE-003, REQ-FLOW-005, REQ-ERR-001, REQ-SCLK-003, REQ-SCLK-004, REQ-FLOW-001, contract.json assumptions[0] (burst start => CPOL_b/CPHA_b captured), CHK-023, CHK-025, CHK-027)

## 5. What this verification does not cover

**32 requirement(s) cannot be checked by simulation** (static, structural, timing, process...). They need another method: lint, CDC, STA, synthesis, review. First ones:

- SPI-4-03 (REQ-PAR-001): Elaboration of m_spi_master shall fail with an error message. — *static_or_structural*
- SPI-4-04 (REQ-PAR-002): m_spi_master shall exhibit the specified behaviour without any other RTL change. — *static_or_structural*
- SPI-5-02 (): The environment keeps i_cmd_valid at 0 while i_rst_n = 0. — *not_applicable_to_dut*
- SPI-5-14 (): i_cpol may change only while o_cs_n = 1. — *not_applicable_to_dut*
- SPI-5-16 (): i_cpha may change only while o_cs_n = 1. — *not_applicable_to_dut*
- SPI-6.1-01 (REQ-CLK-001): All state elements of m_spi_master shall be clocked by the rising edge of i_clk, the only clock of the block. — *static_or_structural*
- SPI-6.1-02 (REQ-CLK-002): o_sclk shall be produced as a data output timed by i_clk. — *static_or_structural*
- SPI-6.1-03 (REQ-CLK-002): o_sclk shall not clock any state element inside the block. — *static_or_structural*
- SPI-6.1-04 (REQ-CLK-003): i_miso shall be treated as synchronous to i_clk and sampled without a synchroniser. — *static_or_structural*
- SPI-12-01 (): The environment shall release i_rst_n synchronously to i_clk. — *not_applicable_to_dut*
- SPI-12-03 (): The environment shall keep i_cmd_valid = 0 while i_rst_n = 0. — *not_applicable_to_dut*
- SPI-12-04 (): The environment shall change i_cpol and i_cpha only while o_cs_n = 1. — *not_applicable_to_dut*
- SPI-12-06 (): The SPI slave testbench model shall drive i_miso as a function of o_sclk and o_cs_n only. — *not_applicable_to_dut*
- SPI-12-09 (): The slave model shall change i_miso only after the i_clk edge at which o_sclk or o_cs_n changed, never altering the value seen at a sampling edge. — *not_applicable_to_dut*
- SPI-12-10 (): The environment shall not assert i_rst_n at an i_clk edge; assertion happens between edges. — *not_applicable_to_dut*
- … 17 more in work/rtm.json

Outside this flow in every case: formal proof, CDC/RDC analysis, static timing, synthesis, DFT.

## 6. Weak spots of the verification itself

Mutation testing changed one RTL line at a time (36 faults; each in the run that executes its line, a survivor again in every other configuration). A fault no check notices is a gap, unless it changes nothing visible (an *equivalent* mutant, claimed below by an agent).

- M06 `m_spi_master.sv:187` zero_to_one (survived in base.s1, min.s1, max.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: r_last is always overwritten at the accepting handshake in Idle before any use. It only affects cmd_ready in XFER and the XFER end, and cmd_ready in Idle does not depend on it. The reset value is not…
- M18 `m_spi_master.sv:159` zero_to_one (survived in base.s1, min.s1, max.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: The case covers all four r_state values and every branch overwrites cmd_ready, so the default assignment is never visible.
- M33 `m_spi_master.sv:181` zero_to_one (survived in base.s1, min.s1, max.s1): **equivalent, proven by formal** (no input sequence changes an output); claimed equivalent: r_sclk reset value 1 or 0 is hidden while o_cs_n=1, because o_sclk = i_cpol in that case. r_sclk is loaded with i_cpol at the burst-start handshake before o_cs_n falls, so the reset value never reach…

Code or cover points never reached (first ones):

- line m_spi_master.sv:167
- line m_spi_master.sv:262
- line m_spi_master.sv:264
- line m_spi_master.sv:265
- line m_spi_master.sv:266
- line m_spi_master.sv:267
- line m_spi_master.sv:84
- line m_spi_master.sv:205
- line m_spi_master.sv:232
- line m_spi_master.sv:233

### Formal check (SymbiYosys)

Every input sequence of up to 32 cycles was searched (one global clock); result {'BOUNDED': 7, 'PROVEN': 6, 'UNSUPPORTED': 14}. PROVEN holds for every cycle; BOUNDED found no counterexample within the depth. Details: `work/formal.md`.


Environment assumptions (the formal results hold only for inputs that respect them; an assumption the specification does not require would hide bugs):

- ENV-01: i_cmd_valid is 0 whenever i_rst_n is 0 (SPI-5-02, SPI-12-03)
- ENV-02: i_rst_n is held at 0 from time zero for at least the first 2 i_clk cycles (SPI-12-12)

## 7. Reproduce without NNC

`designs/spi_master/sim/` holds a Makefile that runs the same regression with Verilator and cocotb only (Linux or WSL):

```bash
cd designs/spi_master/sim
make regression SEED=1 2>&1 | tee sim.log
cd ../../.. && python -m nnc kit-check spi_master    # same outcome as the recorded results?
```

The kit reproduces the primary run base.s1; the other runs differ only by the settings in `run_set.json`.

## 8. Checklist before signing

Answer every item. Sign only if each one is true, or record why not in the approval note:

- [ ] I have read the delegated decisions of D1_config and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of D2_rtl and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G1_rules and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G2_contract and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G3_verif_sources and agree with them (or I have corrected them).
- [ ] Each hand edit of the generated tests and checkers corrects the test and weakens no requirement.
- [ ] The requirements that simulation cannot check are assigned to another verification method.
- [ ] Each surviving mutant is either truly equivalent or a known gap I accept.
- [ ] The unreached code and cover points are unreachable by design or accepted.
- [ ] Each formal environment assumption (verif/formal/nnc_env.sv) is an obligation the specification really places on the environment.
- [ ] I reproduced the regression (or CI did) and the outcome matches the report.

Then: `nnc gate approve spi_master G4_signoff --by "<your name>" --note "<waivers, open items>"`. The approval is bound to the current results.json: a later run makes it STALE.

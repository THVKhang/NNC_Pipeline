# Sign-off packet — async_apb_bridge

This packet is for the person who decides gate **G4 (sign-off)**: *is this design verified well enough against its specification to release?* It collects only the items that need a human judgement. Everything else is in `work/report.md` (all checks and rules) and `work/triage.md`.

## 1. Summary

- **Requirements (rules):** 260 — NOT_VERIFIED_BY_SIM 75, VERIFIED 185
- **Checks:** 35 — PASS 35
- **Tests:** {'pass': 28}
- **Simulated configurations:** 14 runs in 12 configurations (apb4, model_off, syn, 4ph, 4ph_off, apb5, user, sync3, sync4, min, slv_fast, slv_slow); see `run_set.json` and the *Run set* table of the report
- **Code coverage:** line 91.9 %, block 88.8 %, expression 74.8 %, toggle 98.6 %, functional 97.5 %
- **Mutation score:** 83.3 % (30 of 36 injected faults detected)

## 2. Decisions taken for you

These gates were approved by an AI agent on delegation, not by a qualified person. Read each note.

- **G1_rules** (2026-11-10T19:01:14+00:00): Read rules.md: 260 rules kept, 12 merged, 32 rejected (descriptions, scope exclusions, structure, STA/physical items; checked). The 7 open questions were decided on delegation with the cited spec text (formula of LPARA_REQ_W binding; SVA-016 per reset domain, SVA-007 ordinary assertion; DEC-019/DEC-020 binding for verification; DEC-021 ports accepted, APB4 inputs ignored and outputs 0). A person should confirm, especially questions 2 and 6.
- **G2_contract** (2026-11-10T19:51:49+00:00): Re-approval after a flow fix: only the interface parameters changed (checks, rules and plan unchanged). LPARA_STRB_W is now the localparam PARA_APBCDC_DATA_W / 8 (formula read from the Effect column; it was the literal 'Derived', which broke every SVA lint); LPARA_REQ_W and LPARA_RESP_W (internal bundle widths, no port uses them, formula conditional on APB5) are left out of the interface. Earlier note still applies: 35 checks, CHK-019/020/022/023/026/030 expected NOT_VERIFIABLE with the default parameters. A person should confirm.
- **G3_verif_sources** (2026-11-11T05:55:34+00:00): 7 SVA modules lint clean after derived-parameter fix (LPARA_STRB_W = DATA_W/8); every property clocked in one domain; 18 cocotb tests reviewed: cross-domain checks use order + edge windows, NOT_VERIFIABLE for checks needing other parameters. A person should confirm.

## 3. Failures and what they mean

No check fails, and every assertion was exercised.

## 5. What this verification does not cover

**75 requirement(s) cannot be checked by simulation** (static, structural, timing, process...). They need another method: lint, CDC, STA, synthesis, review. First ones:

- AB2-1.1-01 (): The multi-bit request and response bundles must never be sampled by a synchronizer; only one-bit control signals pass through synchronizers. — *static_or_structural*
- AB2-1.1-03 (): The destination must load the multi-bit bundle only after the associated control bit has arrived. — *not_observable_at_interface*
- AB2-1.1-04 (): The timing of the bundle paths must be bounded by set_max_delay constraints (Section 17). — *static_or_structural*
- AB2-1.3-08 (REQ-TIM-001, REQ-TIM-003): The IP must always deliver an executable SDC with the crossing constraints (FEAT-008). — *static_or_structural*
- AB2-2.2-01 (): The RTL must comply with REF-003 baseline; conflicts are resolved by revising the requirement or choosing a compliant implementation, not by a local RTL except… — *static_or_structural*
- AB2-3-20 (REQ-IF-001): The IP shall expose exactly the ports of Section 6.2 of the configured revision. — *static_or_structural*
- AB2-3-29 (REQ-HS-003): The request bit shall be launched at the same edge the request bundle is loaded, and the acknowledge bit at the same edge the response bundle is loaded. — *static_or_structural*
- AB2-3-30 (REQ-HS-003): There shall be no logic between a launch flip-flop and its synchronizer. — *static_or_structural*
- AB2-3-33 (REQ-CLK-002): Only the five crossings (request, request bundle, acknowledge, response bundle, wake-up) shall exist between the clock domains. — *static_or_structural*
- AB2-3-34 (REQ-CLK-002): Each control bit shall cross through a synchronizer and no bundle bit shall cross through one. — *static_or_structural*
- AB2-3-35 (REQ-CLK-003): Synchronizer depth shall follow PARA_APBCDC_CELL_TYPE: 1 and 2 two stages, 3 three stages, 4 four stages. — *static_or_structural*
- AB2-3-36 (REQ-CLK-003): The value 0 (no stage) is for simulation only and shall not be used in a netlist. — *static_or_structural*
- AB2-3-41 (REQ-RESET-002): Asserting only one reset is not supported. — *not_applicable_to_dut*
- AB2-3-46 (REQ-PARAM-001): The IP shall accept the parameter values of Section 8. — *static_or_structural*
- AB2-3-51 (REQ-TIM-001): The IP shall be delivered with a Synopsys-dialect SDC defining the two clocks, interface budgets and exceptions of the five crossings, with budgets computed fr… — *static_or_structural*
- … 60 more in work/rtm.json

Outside this flow in every case: formal proof, CDC/RDC analysis, static timing, synthesis, DFT.

## 6. Weak spots of the verification itself

Mutation testing changed one RTL line at a time (36 faults; each in the run that executes its line, a survivor again in every other configuration). A fault no check notices is a gap, unless it changes nothing visible (an *equivalent* mutant, claimed below by an agent).

- M07 `m_vlsit_apbcdc_cell_sync.sv:171` eq_to_ne (survived in apb4.s1, model_off.s1, 4ph.s1, 4ph_off.s1, apb5.s1, user.s1, sync3.s1, sync4.s1, min.s1, slv_fast.s1, slv_slow.s1): **gap** — The pending-delay countdown is inverted, so an extra delay of 1 becomes 2 cycles and 2 becomes 1. The timing differs for a given seed at the ports but stays inside the legal [N+1,N+3] window, which i…
- M15 `m_vlsit_apbcdc_cell_sync.sv:140` ne_to_eq (survived in apb4.s1, model_off.s1, 4ph.s1, 4ph_off.s1, apb5.s1, user.s1, sync3.s1, sync4.s1, min.s1, slv_fast.s1, slv_slow.s1): claimed equivalent: In run apb4.s1 no +APBCDC_MSYNC_EN plusarg is given, so $value$plusargs fails and this assignment never executes. sim_en stays at its default of 1 and the ports behave identically.
- M20 `m_vlsit_apbcdc_cell_sync.sv:171` negate_if (survived in apb4.s1, model_off.s1, 4ph.s1, 4ph_off.s1, apb5.s1, user.s1, sync3.s1, sync4.s1, min.s1, slv_fast.s1, slv_slow.s1): **gap** — The pending-delay countdown is inverted, so an extra delay of 1 becomes 2 cycles and 2 becomes 1. The timing differs for a given seed at the ports but stays inside the legal window, which is why it s…
- M21 `m_vlsit_apbcdc_cell_sync.sv:136` one_to_zero (survived in apb4.s1, model_off.s1, 4ph.s1, 4ph_off.s1, apb5.s1, user.s1, sync3.s1, sync4.s1, min.s1, slv_fast.s1, slv_slow.s1): **gap** — The default of the model enable is 0, so the model is off with no plusarg and the output is the plain chain output. The random extra latency disappears and the crossing latency is always nominal; thi…
- M27 `m_vlsit_apbcdc_mst.sv:210` zero_to_one (survived in apb4.s1, model_off.s1, syn.s1, 4ph.s1, 4ph_off.s1, apb5.s1, user.s1, sync3.s1, sync4.s1, min.s1, slv_fast.s1, slv_slow.s1): claimed equivalent: In apb4.s1 PARA_APBCDC_APB5=0. reg_wakeup is only reset to 1 during reset and is 0 after the first clock. Its only sink is o_apb_pwakeup, which the slv block gates with APB5!=0, so no output can chan…
- M32 `m_vlsit_apbcdc_cell_sync.sv:173` zero_to_one (survived in apb4.s1, model_off.s1, 4ph.s1, 4ph_off.s1, apb5.s1, user.s1, sync3.s1, sync4.s1, min.s1, slv_fast.s1, slv_slow.s1): claimed equivalent: The line clears pend after a delayed change is applied. Leaving it at 1 is harmless: pend is only stuck after the apply, when cnt is 0 and sim_nxt equals sim_cur. The extra updates rewrite the same v…

3 requirement(s) below the mutation threshold of 85.0 %: AB2-1.3-01, AB2-10.2-01, AB2-10.2-02

Code or cover points never reached (first ones):

- line m_vlsit_apbcdc_mst.sv:92
- line m_vlsit_apbcdc_mst.sv:93
- line m_vlsit_apbcdc_slv.sv:85
- line m_vlsit_apbcdc_slv.sv:86
- line m_vlsit_apbcdc_top.sv:88
- line m_vlsit_apbcdc_top.sv:89
- line m_vlsit_apbcdc_top.sv:104
- line m_vlsit_apbcdc_top.sv:105
- line m_vlsit_apbcdc_mst.sv:98
- line m_vlsit_apbcdc_mst.sv:119

## 7. Reproduce without NNC

`designs/async_apb_bridge/sim/` holds a Makefile that runs the same regression with Verilator and cocotb only (Linux or WSL):

```bash
cd designs/async_apb_bridge/sim
make regression SEED=1 2>&1 | tee sim.log
cd ../../.. && python -m nnc kit-check async_apb_bridge    # same outcome as the recorded results?
```

The kit reproduces the primary run apb4.s1; the other runs differ only by the settings in `run_set.json`.

## 8. Checklist before signing

Answer every item. Sign only if each one is true, or record why not in the approval note:

- [ ] I have read the delegated decisions of G1_rules and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G2_contract and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G3_verif_sources and agree with them (or I have corrected them).
- [ ] The requirements that simulation cannot check are assigned to another verification method.
- [ ] Each surviving mutant is either truly equivalent or a known gap I accept.
- [ ] The unreached code and cover points are unreachable by design or accepted.
- [ ] I reproduced the regression (or CI did) and the outcome matches the report.

Then: `nnc gate approve async_apb_bridge G4_signoff --by "<your name>" --note "<waivers, open items>"`. The approval is bound to the current results.json: a later run makes it STALE.

# Sign-off packet — axi2apb_bridge

This packet is for the person who decides gate **G4 (sign-off)**: *is this design verified well enough against its specification to release?* It collects only the items that need a human judgement. Everything else is in `work/report.md` (all checks and rules) and `work/triage.md`.

## 1. Summary

- **Requirements (rules):** 151 — NOT_VERIFIED_BY_SIM 37, VERIFIED 114
- **Checks:** 31 — PASS 31
- **Tests:** {'pass': 15}
- **Simulated configuration:** one (parameters {'PARA_AXI_ID_W': 4}, seed 1)
- **Code coverage:** line 98.9 %, block 95.9 %, expression 96.2 %, toggle 74.8 %, functional 97.5 %
- **Mutation score:** 88.9 % (32 of 36 injected faults detected)

## 2. Decisions taken for you

These gates were approved by an AI agent on delegation, not by a qualified person. Read each note.

- **G1_rules** (2026-11-08T15:29:08+00:00): Only change: decision 2 (AR/AW tie preference) revised to round-robin after the CHK-019 phase D finding; the designer GabrielHCMUT asked Claude to choose because the arbitration wording was unclear to them. Rules themselves unchanged.
- **G2_contract** (2026-11-08T15:29:35+00:00): Edited at review to follow revised decision 2 (round-robin): CHK-019 title/behavior/expected (phase D: the tie after a lone write is won by R4), CHK-031 stimulus (d) 'complete one read', decision 2 text. No other check changed; both are tests, so SVA checkers are unaffected and only the cocotb module is regenerated.
- **G3_verif_sources** (2026-11-10T03:29:09+00:00): Re-approved after a triage-driven test fix (2026-11-10): triage judged B_test_wrong for test_chk_031 (fix_candidate/triage_chk031_reset.md). The reference model now records APB writes that completed before a reset cut the burst (spec:163/333/584: per-beat writes, no rollback), with the same pwdata/pstrb = W beat check as at B. The final memory comparison stays byte-exact; no check removed or relaxed.

## 3. Failures and what they mean

No check fails, and every assertion was exercised.

## 5. What this verification does not cover

**37 requirement(s) cannot be checked by simulation** (static, structural, timing, process...). They need another method: lint, CDC, STA, synthesis, review. First ones:

- AB-2.1-01 (): The RTL design must follow the VLSIT RTL Design Rules v2 as the mandatory RTL baseline. — *static_or_structural*
- AB-2.2-01 (): A product choice must not weaken a protocol requirement of the selected standards. — *design_guideline*
- AB-3-16 (REQ-IF-006): The bridge shall omit AxLOCK, USER, QOS and REGION ports. — *static_or_structural*
- AB-3-19 (REQ-IF-008): The bridge shall not implement exclusive access. — *static_or_structural*
- AB-3-20 (REQ-IF-008): Integration shall not send exclusive traffic to the bridge. — *not_applicable_to_dut*
- AB-3-23 (REQ-CLK-001): The bridge shall use one shared ACLK/PCLK domain. — *static_or_structural*
- AB-3-24 (REQ-CLK-001): The bridge shall contain no asynchronous clock crossing. — *static_or_structural*
- AB-3-25 (REQ-RESET-001): The bridge shall use one active-low reset synchronous to ACLK. — *static_or_structural*
- AB-3-26 (REQ-RESET-001): The SoC shall supply the reset synchronized to ACLK. — *not_applicable_to_dut*
- AB-3-28 (REQ-PARAM-001): PARA_AXI_ID_W shall range from 1 to 16, with default 4. — *static_or_structural*
- AB-3-29 (REQ-PARAM-001): PARA_AXI_ID_W shall set both read and write ID widths. — *static_or_structural*
- AB-3-38 (REQ-ERR-004): The external APB fabric shall provide a default unmapped Completer with PREADY=1 and PSLVERR=1. — *not_applicable_to_dut*
- AB-3-42 (REQ-CSR-001): The bridge shall contain no software-visible CSR interface. — *static_or_structural*
- AB-3-43 (REQ-VER-001): Verification shall derive expected results from this specification and cited standards, never from generated RTL. — *not_applicable_to_dut*
- AB-3-44 (REQ-VER-002): Verification deliverables shall retain generated testbench sources and commands. — *not_applicable_to_dut*
- … 22 more in work/rtm.json

Outside this flow in every case: formal proof, CDC/RDC analysis, static timing, synthesis, DFT.

## 6. Weak spots of the verification itself

Mutation testing changed one RTL line at a time (36 faults). A fault no check notices is a gap, unless it changes nothing visible (an *equivalent* mutant, claimed below by an agent).

- M09 `m_axi2apb_apb_ctrl.sv:165` zero_to_one: claimed equivalent: This is the default assignment at the top of the always_comb. The following case on the APB state overwrites o_apb_pwrite in every branch: SETUP and ACCESS set it from reg_apb_wr, and the default bra…
- M13 `m_axi2apb_wr_seq.sv:183` or_to_and: claimed equivalent: The OR becomes an AND, so the result differs only for a WRAP burst with exactly one fault: a bad length (not 2/4/8/16) with an aligned address, or a good length with a misaligned address. Both are il…
- M14 `m_axi2apb_apb_ctrl.sv:223` and_to_or: claimed equivalent: The mutant clears reg_turn_rd while in ACTRD even without rd_done. The value is used only in the IDLE state, and ACTRD always ends with rd_done, which clears it anyway. rd_done can only be high while…
- M21 `m_axi2apb_rd_seq.sv:182` or_to_and: claimed equivalent: The OR becomes an AND, so the result differs only for a WRAP read with exactly one fault: a bad length with an aligned address, or a good length with a misaligned address. Both are illegal AXI4 WRAP …

Code or cover points never reached (first ones):

- line m_axi2apb_apb_ctrl.sv:126
- line m_axi2apb_apb_ctrl.sv:127
- line m_axi2apb_apb_ctrl.sv:147
- line m_axi2apb_apb_ctrl.sv:148
- line m_axi2apb_rd_seq.sv:297
- line m_axi2apb_rd_seq.sv:298
- line m_axi2apb_wr_seq.sv:280
- line m_axi2apb_wr_seq.sv:281
- functional nnc_cov.sv:0 COVP-024

## 7. Reproduce without NNC

`designs/axi2apb_bridge/sim/` holds a Makefile that runs the same regression with Verilator and cocotb only (Linux or WSL):

```bash
cd designs/axi2apb_bridge/sim
make regression SEED=1 2>&1 | tee sim.log
cd ../../.. && python -m nnc kit-check axi2apb_bridge    # same outcome as the recorded results?
```

## 8. Checklist before signing

Answer every item. Sign only if each one is true, or record why not in the approval note:

- [ ] I have read the delegated decisions of G1_rules and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G2_contract and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G3_verif_sources and agree with them (or I have corrected them).
- [ ] The requirements that simulation cannot check are assigned to another verification method.
- [ ] Each surviving mutant is either truly equivalent or a known gap I accept.
- [ ] The unreached code and cover points are unreachable by design or accepted.
- [ ] I reproduced the regression (or CI did) and the outcome matches the report.

Then: `nnc gate approve axi2apb_bridge G4_signoff --by "<your name>" --note "<waivers, open items>"`. The approval is bound to the current results.json: a later run makes it STALE.

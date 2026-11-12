# Sign-off packet — apb_tlul_bridge

This packet is for the person who decides gate **G4 (sign-off)**: *is this design verified well enough against its specification to release?* It collects only the items that need a human judgement. Everything else is in `work/report.md` (all checks and rules) and `work/triage.md`.

## 1. Summary

- **Requirements (rules):** 232 — NOT_VERIFIED_BY_SIM 63, VERIFIED 169
- **Checks:** 31 — PASS 31
- **Tests:** {'pass': 17}
- **Simulated configuration:** one (parameters {'PARA_ADDR_W': 32, 'PARA_SRC_W': 8, 'PARA_SRC_ID': 0, 'PARA_A_USER_W': 1, 'PARA_D_SINK_W': 1, 'PARA_D_USER_W': 1}, seed 1)
- **Code coverage:** line 96.0 %, block 95.6 %, expression 100.0 %, toggle 95.9 %, functional 100.0 %
- **Mutation score:** 100.0 % (33 of 33 injected faults detected)

## 2. Decisions taken for you

These gates were approved by an AI agent on delegation, not by a qualified person. Read each note.

- **G1_rules** (2026-11-07T18:06:13+00:00): Delegated review: rules.md read by Claude at the user's request; 5 open questions decided by Claude; not an engineer's review.
- **G2_contract** (2026-11-08T10:00:45+00:00): Re-approved after the renumber fix: cross-references inside CHK-011, CHK-012, CHK-025, CHK-028 and in not_verified notes/assumptions now name the renumbered checks (ranges expanded). Interface gains clock/reset typing; checks, kinds and rule coverage (232 rules, 169 in checks, 63 not verified) unchanged.
- **G3_verif_sources** (2026-11-11T15:38:44+00:00): Added verif/formal/nnc_env.sv (agent A13, from the spec only): 5 environment assumptions, read one by one: requester idle in reset (ENV-01), APB Setup->Access sequencing and PSEL/PENABLE held until PREADY (ENV-02/03), request fields stable until PREADY (ENV-04), TL-UL D beat held until accepted (ENV-05). Orphan responses and error responses stay allowed (the spec makes them legal inputs). Tests and checkers unchanged. A person should confirm the assumptions.

## 3. Failures and what they mean

No check fails, and every assertion was exercised.

## 5. What this verification does not cover

**63 requirement(s) cannot be checked by simulation** (static, structural, timing, process...). They need another method: lint, CDC, STA, synthesis, review. First ones:

- BR-3-15 (REQ-IF-001): The bridge shall expose exactly the APB4 Completer signals listed in section 6.2 and no other APB signal. — *static_or_structural*
- BR-3-16 (REQ-IF-002): The bridge shall expose exactly the TL-UL host signals listed in section 6.2 and no others. — *static_or_structural*
- BR-3-17 (REQ-IF-003): Such output ports shall be driven directly by a flip-flop Q pin with no combinational logic; never-changing outputs are constant tie-offs. — *static_or_structural*
- BR-3-23 (REQ-IF-007): APB-facing and TL-UL-facing logic shall be in two separate modules connected only through the internal interface of section 5.1. — *static_or_structural*
- BR-3-29 (REQ-CLK-001): The bridge shall operate in one clock domain, i_clk_core, for both interfaces with no clock-domain crossing. — *static_or_structural*
- BR-3-33 (REQ-PARAM-001): The bridge shall accept only parameter values listed in section 8; an illegal value shall be reported at elaboration. — *static_or_structural*
- BR-3-39 (REQ-RTL-001): The RTL shall comply with REF-003 and use the hierarchy of section 14.2. — *static_or_structural*
- BR-3-40 (REQ-VER-001): An APB protocol checker and the REF-005 TL-UL protocol checker shall be bound to the ports. — *static_or_structural*
- BR-3-41 (REQ-DFT-001): The RTL shall be scan-insertable: no latch, combinational loop, internal tri-state, clock gating, or gated/derived clock. — *static_or_structural*
- BR-4-02 (): PARA_ADDR_W must not be configured with a value outside the range 16 to 32. — *static_or_structural*
- BR-6.2-01 (): i_apb_paddr bits [1:0] must be 0. — *not_applicable_to_dut*
- BR-6.2-02 (): i_apb_pstrb must be 4'b1111 for a write. — *not_applicable_to_dut*
- BR-6.3-01 (): Setup phase lasts one cycle with PSEL=1 and PENABLE=0; the Access phase starts next cycle and lasts until PREADY is high. — *not_applicable_to_dut*
- BR-6.3-02 (): PADDR, PWRITE, PWDATA and PSTRB stay unchanged from Setup until PREADY. — *not_applicable_to_dut*
- BR-7.2-01 (): A CDC tool run must report zero crossings, since there is one clock domain and one reset domain. — *static_or_structural*
- … 48 more in work/rtm.json

Outside this flow in every case: formal proof, CDC/RDC analysis, static timing, synthesis, DFT.

## 6. Weak spots of the verification itself

Mutation testing changed one RTL line at a time (33 faults). A fault no check notices is a gap, unless it changes nothing visible (an *equivalent* mutant, claimed below by an agent).


Code or cover points never reached (first ones):

- line m_apb_if.sv:100
- line m_apb_tlul_bridge.sv:63
- line m_apb_tlul_bridge.sv:65
- line m_apb_tlul_bridge.sv:69
- line m_tlul_if.sv:54
- line m_tlul_if.sv:56
- line m_tlul_if.sv:60
- line m_tlul_if.sv:145

### Formal check (SymbiYosys)

Every input sequence of up to 20 cycles was searched (one global clock); result {'BOUNDED': 7, 'PROVEN': 10}. PROVEN holds for every cycle; BOUNDED found no counterexample within the depth. Details: `work/formal.md`.


Environment assumptions (the formal results hold only for inputs that respect them; an assumption the specification does not require would hide bugs):

- ENV-01: The APB Requester is reset together with the bridge. While reset is asserted it is idle (PSEL=0, PENABLE=0). (BR-7.3-05, BR-3-32)
- ENV-02: A Setup phase is followed by an Access phase in the next cycle, and the Access phase lasts until PREADY. PSEL and PENABLE stay high until PREADY. (BR-6.3-01, BR-20-01)
- ENV-03: PENABLE is high only in an Access phase. An Access phase follows a one-cycle Setup phase. After PREADY the next cycle is idle or a new Setup phase (back-to-back with PSEL held high), and it is never an Access phase. (BR-6.3-01, BR-20-01, BR-20-02, BR-…
- ENV-04: PADDR, PWRITE, PWDATA and PSTRB stay unchanged from the Setup phase until PREADY. (BR-6.3-02, BR-20-01)
- ENV-05: TL-UL D-channel handshake. When the device has presented a D-channel beat that was not accepted (d_valid=1, d_ready=0), it keeps d_valid high and the D payload stable. (BR-15.1-02, BR-3-40)

## 7. Reproduce without NNC

`designs/apb_tlul_bridge/sim/` holds a Makefile that runs the same regression with Verilator and cocotb only (Linux or WSL):

```bash
cd designs/apb_tlul_bridge/sim
make regression SEED=1 2>&1 | tee sim.log
cd ../../.. && python -m nnc kit-check apb_tlul_bridge    # same outcome as the recorded results?
```

## 8. Checklist before signing

Answer every item. Sign only if each one is true, or record why not in the approval note:

- [ ] I have read the delegated decisions of G1_rules and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G2_contract and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G3_verif_sources and agree with them (or I have corrected them).
- [ ] The requirements that simulation cannot check are assigned to another verification method.
- [ ] The unreached code and cover points are unreachable by design or accepted.
- [ ] Each formal environment assumption (verif/formal/nnc_env.sv) is an obligation the specification really places on the environment.
- [ ] I reproduced the regression (or CI did) and the outcome matches the report.

Then: `nnc gate approve apb_tlul_bridge G4_signoff --by "<your name>" --note "<waivers, open items>"`. The approval is bound to the current results.json: a later run makes it STALE.

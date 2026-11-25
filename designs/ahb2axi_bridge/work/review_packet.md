# Sign-off packet — ahb2axi_bridge

This packet is for the person who decides gate **G4 (sign-off)**: *is this design verified well enough against its specification to release?* It collects only the items that need a human judgement. Everything else is in `work/report.md` (all checks and rules) and `work/triage.md`.

## 1. Summary

- **Requirements (rules):** 234 — FAILED 143, NOT_PROVEN 1, NOT_VERIFIED_BY_SIM 57, VERIFIED 33
- **Checks:** 40 — FAIL 26, NOT_HIT 1, PASS 13
- **Tests:** {'fail': 20, 'pass': 1}
- **Simulated configurations:** 5 runs in 4 configurations (base, ids8, ids35, xrand); see `run_set.json` and the *Run set* table of the report
- **Code coverage:** line 91.3 %, block 97.3 %, expression 86.4 %, toggle 91.5 %, functional 90.0 %

## 2. Decisions taken for you

These gates were approved by an AI agent on delegation, not by a qualified person. Read each note.

- **G1_rules** (2026-11-12T16:11:43+00:00): Delegated review (the user is not a hardware designer). 234 rules kept; the 39 rejected are structural, documentation or licensing statements with no observable behaviour. The six open questions were answered conservatively from §20.3 decisions (DEC-BURST-001, DEC-PERF-002, DEC-ID-001, DEC-BURST-002): nothing the spec leaves open is checked. All six are marked as delegated assumptions to confirm by a qualified human reviewer at G4.
- **G2_contract** (2026-11-12T16:22:11+00:00): Delegated review. Interface (52 ports, 2 parameters) matches the spec port table and the RTL top. 40 checks (20 assertions, 20 tests) cover 177 of 234 rules; 57 are not verifiable by simulation (structural, synthesis, DFT). Checks follow the delegated answers of G1 (optional aggregation CHK-024, conditional 6-cycle bound CHK-034, ID range only CHK-009/032, no fixed split lengths CHK-027). All checks kept (designer choice not made by the user).
- **G3_verif_sources** (2026-11-14T15:41:48+00:00): Generated with the run set (base x2 seeds, ids8, ids35) in the prompts. Reviewed: tests valid at the first attempt, 0 literal exemptions, only top-level ports are touched (no internal signals); checkers (ahb, axi, cross, reset) and coverage lint clean; formal environment ENV-01..: reset idle, AXI subordinate reset with the bridge, HREADY mux, HWDATA stable. A person should confirm.

## 3. Failures and what they mean

Checks not passing: CHK-002, CHK-005, CHK-012, CHK-014, CHK-015, CHK-016, CHK-017, CHK-020, CHK-021, CHK-022, CHK-023, CHK-024, CHK-025, CHK-026, CHK-027, CHK-028, CHK-029, CHK-031, CHK-032, CHK-033, CHK-034, CHK-035, CHK-036, CHK-037, CHK-038, CHK-039, CHK-040. The triage agent read the specification, the RTL, the tests and the logs, and gives the most likely cause. It changes nothing; you decide.

### test_chk_021_accept_qualifiers — CHK-021: AR handshakes expected 42 got 26 (all 4 runs)

- **Most likely:** the RTL is likely wrong
- **Specification:** spec/AHB2AXI_Bridge_Design_Specification.md:143 REQ-FUNC-003 "Each accepted AHB read shall issue exactly one AXI single-beat AR transaction"; :312 "A transfer is accepted at a rising i_clk_core edge when HSEL, HREADY and HTRANS[1] are all 1"; :141 REQ-FUNC-001 "convert every supported AHB transfer accepted by this IP to AXI4 without loss". contract.json:838-840 (CHK-021) "exactly one per accepted beat ... the number of AR handshakes ... equals the number of NONSEQ/SEQ beats accepted".
- **RTL:** rtl/m_ahb2axi_ahb_if.sv:78-107 is one always_comb. Line 81 sets o_rsp_ready=1'b0. Lines 87-88 then compute o_req_valid = hsel & hready & htrans[1] & (~reg_data_phase_valid | o_rsp_ready). The real o_rsp_ready is only assigned later, at line 97, so line 88 always reads 0. The effective condition is o_req_valid = hsel&hready&htrans[1]&~reg_data_phase_valid. When a data phase completes (HREADYOUT=1, lines 92-98) while the next NONSEQ/SEQ address is on the bus (the normal AHB pipeline), the AHB man…
- **Options:** Fix RTL (m_ahb2axi_ahb_if.sv). Compute o_rsp_ready before o_req_valid in p_com_ahb_rsp: move lines 87-88 after lines 91-102, or compute the completion term in a separate always_comb or assign. Then o_req_valid = hsel&hready&htrans[1]&(~reg_data_phase_valid | o_rsp_ready) uses the real value, and a transfer accepted on the completing edge is pushed into the cmd FIFO. Re-run the whole suite after this fix. Most of the failures below are expected to change. No test or spec change is indicated.

### test_chk_022_no_comb_ready_path — timeout after 190000 cycles waiting for AHB transfers to complete (all 4 runs)

- **Most likely:** the RTL is likely wrong
- **Specification:** spec :322 "AXI4 VALID and payload shall remain stable until READY handshakes. AXI outputs have no combinational dependency on AXI READY." (rules AA-T1.7.3.2-01). contract.json:850-852 (CHK-022). The test also needs the bridge to finish legal random traffic: spec :141 REQ-FUNC-001 requires no loss, and :153 and :325 say a transfer stays pending only while the AXI response is missing. Here the AXI model always responds.
- **RTL:** The property under test looks satisfied by construction. m_ahb2axi_axi_if.sv:105-131 maps payload and VALID straight from the controller, and the controller's VALID/payload (m_ahb2axi_ctrl.sv:657-715) depend on state and FIFO flags, not on *_ready. The test never got that far, though. The AHB side deadlocked. Inferred mechanism: the pipelined-transfer drop (m_ahb2axi_ahb_if.sv:81/87-88/97) desynchronises the AHB data phases from the controller FSM. After an early-acked or dropped terminal beat,…
- **Options:** Fix RTL. (1) Fix the o_req_valid/o_rsp_ready ordering in m_ahb2axi_ahb_if.sv:87-98. (2) Gate w_cap_stop with reg_fsm_ctrl_current_state==ENUM_ST_WR_CAPTURE (ctrl.sv:513-516), or at least do not let the ctrl.sv:859-862 assignment override the start block at 818-841. Also clear or qualify reg_burst_count for non-eligible starts so that w_more_fallback_beats (ctrl.sv:542) cannot use a stale count. Then re-run CHK-022 to check the READY-independence property itself. No test change is needed.

### test_chk_023_device_bursts_singles — CHK-033/CHK-040 (CHK-023): expected 336 W beats got 168 (all 4 runs)

- **Most likely:** the RTL is likely wrong
- **Specification:** spec :148 REQ-FUNC-008 "Device-E writes shall use ordered AXI single-beat transactions and shall wait for each final-destination BRESP"; :434 OP-WR-SINGLE "One AWLEN=0, one W beat, WLAST=1 ... Wait for BRESP"; :200 "Fixed non-bufferable bursts are serialized beat by beat"; :146 REQ-FUNC-006 "WDATA/WSTRB shall preserve each AHB HWDATA/HWSTRB beat". contract.json:877-879 (CHK-023) "Each AHB beat produces exactly one AW ... plus one W with o_axi_wlast=1".
- **RTL:** Device-nE (prot[6:2]=00000) and Device-E (00001) beats are not eligible (ctrl.sv:354-370 needs lookup=prot[4]), so each beat goes IDLE→WR_SINGLE→WR_B→AHB_RSP. Beat k completes in AHB_RSP with HREADYOUT=1 while beat k+1 (SEQ) is on the bus. Because of m_ahb2axi_ahb_if.sv:81/87-88/97, o_req_valid=0, so beat k+1 is not written to the wr-cmd FIFO and no data is stored for it (reg_data_store and o_data_valid need reg_data_phase_valid, ahb_if.sv:89, ctrl.sv:782). Beat k+1's data phase then gets the i…
- **Options:** Fix RTL: the ordering fix in m_ahb2axi_ahb_if.sv:87-98. Also fix the ungated w_cap_stop/fallback override in ctrl.sv:513-516 and 859-862, so that non-eligible NONSEQ writes use reg_cmd_addr (ctrl.sv:695-698) and not stale reg_burst_* entries. Re-run CHK-023 to check the AW address, size and per-beat BRESP-wait expectations. No test or spec change.

### test_chk_024_wb_burst_aggregation — timeout after 68400 cycles waiting for AHB transfers to complete (all 4 runs)

- **Most likely:** the RTL is likely wrong
- **Specification:** spec :145 REQ-FUNC-005 (an eligible WB fixed burst may aggregate after all beats are captured, otherwise ordered singles); :147 REQ-FUNC-007 "earlier beats may receive OKAY once safely buffered"; :157/:459 "may accept one AHB beat per i_clk_core cycle while the 16-entry buffer has room"; :202 "the terminal AHB beat waits for the required B response(s)". contract.json:909-911 (CHK-024).
- **RTL:** Beat 1 (NONSEQ, eligible) is early-acked in its first data-phase cycle (ctrl.sv:421, 436-442), so HREADYOUT=1 with beat 2 (SEQ) on the bus. o_req_valid uses the stale o_rsp_ready=0 (ahb_if.sv:81/87-88), so beat 2 is dropped and completes zero-wait. Beat 3 is captured and early-acked, which drops beat 4, and so on. The capture never sees N beats. Separately, w_cap_stop at the start edge (head is NONSEQ, ctrl.sv:513-516) sets reg_burst_term_seen=1 and reg_burst_fallback=1 (ctrl.sv:859-862, overri…
- **Options:** Fix RTL: (1) the ahb_if o_req_valid/o_rsp_ready ordering; (2) gate w_cap_stop to the WR_CAPTURE state and stop it overriding reg_burst_fallback/reg_burst_term_seen at the start edge (ctrl.sv:513-516, 859-862); (3) make sure a terminal response is never left in AHB_RSP without an owning AHB data phase. Re-run CHK-024 and look at the coverage of aggregated vs singles outcomes. The aggregation mandatory-or-optional question (rules.json:7226) can be settled separately in the spec.

### test_chk_025_varying_attrs_singles — timeout after 4400 cycles waiting for AHB transfers to complete (all 4 runs)

- **Most likely:** the RTL is likely wrong
- **Specification:** spec :317 "If a burst-scoped AXI address attribute differs between accepted beats, the bridge uses ordered AXI singles"; :436 OP-WR-FALLBACK "Ordered AXI singles ... Aggregate relevant B errors to the terminal AHB beat"; :147 REQ-FUNC-007. contract.json:925-927 (CHK-025; the stimulus is marked out-of-profile on purpose, and the rule covers the case).
- **RTL:** Same path as CHK-024. The first beat of the WB_A burst is eligible and early-acked (ctrl.sv:421, 436). The pipelined SEQ beat is dropped by ahb_if.sv:87-88, and alternate beats go missing. reg_burst_fallback/term_seen are forced at the start edge by the ungated w_cap_stop (ctrl.sv:513-516, 859-862). The terminal beat is lost, so the drained response is left in AHB_RSP (ctrl.sv:648-651). The timeout value 4400 = 400+400*10 equals the WRAP8 case (8 beats + 2 IDLE). So the first INCR4 run (6 items…
- **Options:** Fix RTL: the same two fixes as CHK-024 (ahb_if ordering; gate w_cap_stop and stop the fallback/term_seen override). Check that the fallback compare at ctrl.sv:850-856 is what selects singles once capture works. If the designer considers varying-attribute bursts out of scope, that must be written into the spec. Otherwise keep the test unchanged.

### test_chk_026_early_termination — timeout after 86000 cycles waiting for AHB transfers to complete (all 4 runs)

- **Most likely:** the RTL is likely wrong
- **Specification:** spec :149 REQ-FUNC-009 "An early-terminated AHB fixed write burst shall never produce an incomplete AXI burst ... emit any captured but unissued accepted write beats as ordered AXI single-beat transactions ... and hold the terminal AHB response until all corresponding B responses arrive"; :317. contract.json:946-947 (CHK-026) "Beat k's AHB data phase completes only at or after the k-th B handshake ... The following transfer after termination is handled normally."
- **RTL:** For k=1 (INCR8, beat 1 then IDLE), beat 1 is eligible with len>1, so w_input_early_ack=1 (ctrl.sv:421). In its first data-phase cycle, w_early_ack_now = w_data_hs & ... & ~w_burst_term (ctrl.sv:436-437). w_burst_term's IDLE clause needs w_wr_cmd_start (ctrl.sv:428-429), and that is still 0 because the cmd FIFO's registered empty flag only clears one edge after the write (m_vlsit_sfifo_rd.sv:151, which uses the pre-edge write pointer). The IDLE termination is therefore missed, and beat k is OKAY…
- **Options:** Fix RTL. Make early-ack termination detection independent of the FIFO empty-flag lag: for example, qualify w_early_ack_now directly on the current HTRANS being SEQ/BUSY for the same burst, instead of on w_wr_cmd_start (ctrl.sv:426-437). Also fix the ahb_if ordering and the w_cap_stop gating. Optionally clarify the spec: add to REQ-FUNC-007/009 that early OKAY on beat k is allowed only when the overlapping address phase is SEQ/BUSY of the same burst.

### Assertion CHK-002 — IDLE and BUSY transfers get zero-wait OKAY: 17 fails / 20390 hits (base.s1 2, base.s2 11, ids8 2, ids35 2); first fail 2668805000 ps

- **Most likely:** the RTL is likely wrong
- **Specification:** spec :142 REQ-FUNC-002 and :312 (IDLE/BUSY create no AXI traffic). The zero-wait OKAY for IDLE/BUSY comes from AHB (REF-001), which rules AA-6.1-01 and AA-T1.7.3.1-03 bind (contract.json:528-535, CHK-002): "if at edge t i_ahb_hsel=1, i_ahb_hready=1 and i_ahb_htrans is IDLE or BUSY, then at edge t+1 o_ahb_hreadyout=1 and o_ahb_hresp=0."
- **RTL:** m_ahb2axi_ahb_if.sv:104-105 forces o_ahb_hreadyout=0 whenever hsel & htrans[1] & ~i_req_ready, even when no data phase of this subordinate is active (reg_data_phase_valid=0). i_req_ready is 0 in every controller state except IDLE/AHB_RSP/WR_CAPTURE (ctrl.sv:564-582). The failing case: the bridge has already completed the AHB side of a write early (an early-acked beat whose termination was missed, ctrl.sv:426-437, or a beat dropped by ahb_if.sv:87-88) and is still draining on AXI. The manager th…
- **Options:** Fix RTL. Remove the unconditional HREADYOUT=0 at ahb_if.sv:104-105. Stall a new address only by extending a pending data phase of this bridge, which means the bridge must not complete the last AHB beat of a write before it can accept the next address. Concretely: fix the early-ack termination detection (ctrl.sv:426-437), and keep the terminal or last-captured beat's data phase open until the drain completes, as REQ-FUNC-009 already requires. The ahb_if ordering fix removes the drop-induced case…

### Assertion CHK-005 — AW VALID and payload stable until AWREADY: 2 fails / 14676 hits (base.s2 only); first fail 4256675000 ps

- **Most likely:** the RTL is likely wrong
- **Specification:** spec :322 "AXI4 VALID and payload shall remain stable until READY handshakes"; :216 "AXI VALID and payload remain stable until READY handshake."; :280 o_axi_awvalid "Hold until AWREADY". rules.json:7444-7445: "VALID and payload must stay stable until the READY handshake."
- **RTL:** In ENUM_ST_WR_SINGLE, the AW payload is chosen by reg_burst_fallback (ctrl.sv:688-699): reg_burst_addr/size/prot[widx] when it is 1, reg_cmd_* when it is 0. reg_burst_fallback is set by `if (w_cap_stop)` at ctrl.sv:859-862 in any state. w_cap_stop (ctrl.sv:513-516) is 1 whenever the wr-cmd FIFO is non-empty and its head is not a SEQ write. If, while AW is pending (AWVALID=1, AWREADY=0) for a SEQ-head command (fallback=0), another write command with a NONSEQ head is already in the 2-deep cmd FIF…
- **Options:** Fix RTL. Gate w_cap_stop (ctrl.sv:513-516), or the fallback update at ctrl.sv:859-862, to ENUM_ST_WR_CAPTURE, so that reg_burst_fallback cannot change while an AW/W from WR_SINGLE is pending. Alternatively, register the AW payload at issue time and hold it until handshake. Fixing the ahb_if ordering removes the desync that exposes this. Re-run base.s2 to confirm.

### Assertion CHK-015 — AHB read completes only with its R beat and carries RDATA unchanged: 3834 fails / 8723 hits; first fail 1050000 ps (test_chk_021)

- **Most likely:** the RTL is likely wrong
- **Specification:** spec :143 REQ-FUNC-003; :198 "accept one R beat (RLAST=1) → return HRDATA and HRESP in the AHB data phase. No next AHB read is accepted while the current read is unresolved."; :458 "AHB does not accept the next read until the current R data/status returns"; :357 "AHB waits for R; map RRESP". contract.json:736 (CHK-015).
- **RTL:** When a read's address phase is pipelined behind a completing transfer, m_ahb2axi_ahb_if.sv:87-88 (which reads o_rsp_ready=0 from line 81 before line 97 assigns it) does not capture it, yet HREADYOUT=1 accepts it on the bus. In its data phase reg_data_phase_valid=0, so lines 82-84 output HREADYOUT=1, HRESP=0, HRDATA=0 with no AR or R ever issued. That gives c15_have=0 and a fail. Once the FSM desyncs, reg_rsp_valid can also be left in ENUM_ST_AHB_RSP (ctrl.sv:648-651), and a later read data phas…
- **Options:** Fix RTL: reorder p_com_ahb_rsp in m_ahb2axi_ahb_if.sv so o_req_valid uses the computed o_rsp_ready. Also make sure reg_rsp_valid cannot be left without an owning AHB data phase (ctrl.sv:440-450, 648-651). No checker or test change.

### Assertion CHK-016 — Waiting-class writes complete only after their BRESP: 9771 fails / 9814 hits; first fail 1270000 ps (test_chk_021)

- **Most likely:** the RTL is likely wrong
- **Specification:** spec :148 REQ-FUNC-008 "Device-E writes ... shall wait for each final-destination BRESP; no early AHB write response is allowed"; :434 OP-WR-SINGLE "Wait for BRESP; map the response to that AHB transfer"; :358 "AHB single/INCR write ... Wait for BRESP"; :149 REQ-FUNC-009 and :202 for the terminal beat. contract.json:756 (CHK-016).
- **RTL:** Pipelined write beats are not captured (m_ahb2axi_ahb_if.sv:87-88 uses the stale o_rsp_ready=0). Their data phase completes zero-wait OKAY (lines 82-83) with no AW/W/B, which is a direct violation for SINGLE/INCR/Device beats. Early ack can also complete the last captured beat of a terminated WB burst before B (ctrl.sv:421, 436-437; termination is missed because of the lagging w_wr_cmd_start in w_burst_term, ctrl.sv:426-432). Separately, for every NONSEQ write the forced reg_burst_fallback (ctr…
- **Options:** Fix RTL: the ahb_if o_req_valid/o_rsp_ready ordering, the w_cap_stop gating so NONSEQ singles use reg_cmd_addr, and the early-ack termination detection. After the fix, re-check that the remaining CHK-016 fails (if any) are not cascades. Optionally (test infrastructure, not weakening) add a diagnostic to the checker that reports the first index desync separately so cascades are visible. Do not relax the check.

### Assertion CHK-017 — Locally rejected transfers end in ERROR and produce no W data: 4 fails / 5549 hits (one per run); first fail 3620270000 ps (test_chk_031)

- **Most likely:** the RTL is likely wrong
- **Specification:** spec :155 REQ-ERR-002 "HMASTLOCK, HPROT[6]=1, reserved/unsupported HPROT combinations, unsupported HSIZE and misaligned transfers shall return two-cycle AHB ERROR; no AXI request shall be issued for the rejected transfer."; :313 "any earlier accepted write prefix is drained under REQ-FUNC-009"; :361. contract.json:775 (CHK-017).
- **RTL:** In test_chk_031 the rejected NONSEQ (lock/p6/size/mis) is driven in the address phase right after beat 3 of an INCR8 WB prefix. When beat 3's data phase completes (early ack or the drained response, HREADYOUT=1), m_ahb2axi_ahb_if.sv:87-88 does not capture the pipelined rejected transfer (o_rsp_ready reads 0 from line 81). It never reaches the controller's local-error path (ctrl.sv:590-596 → ENUM_ST_LOCAL → reg_rsp_err=1 at 940-944). Its data phase then gets HREADYOUT=1, HRESP=0 (ahb_if.sv:82-83…
- **Options:** Fix RTL: the ahb_if ordering fix so that a transfer accepted on a completing edge is captured and routed through f_local_error (ctrl.sv:411-412, 590-596). Re-run test_chk_031/CHK-017 to check the drain-then-ERROR order. No test or spec change.

### Assertion CHK-020 — AXI payload outputs hold reset values during reset: 452 fails / 452 hits (every reset cycle, all runs); first fail 0 ps

- **Most likely:** the RTL is likely wrong
- **Specification:** Port table, reset/idle value column: spec :298 o_axi_arprot "Reset / idle value: 0"; :282 o_axi_wdata "0"; :283 o_axi_wstrb "0"; :272-279, 291-297 (rules AA-T1.7.2.2-09/15/19/21). contract.json:823 (CHK-020) "o_axi_arprot=0 ... o_axi_wdata=0 ...". Counterpoints: :467 "FIFO payload contents need not be reset"; :176/:182 "the combinational AXI adapter uses the reset only to suppress VALID/READY"; :386 and rules.json:7411/7627 list only HREADYOUT/HRESP/VALID/READY as reset values.
- **RTL:** m_ahb2axi_ctrl.sv:677 always drives w_axi_ar_prot = f_axi_prot(reg_cmd_prot[1:0], reg_cmd_nonsec) = {~hprot[0], nonsec, hprot[1]} (ctrl.sv:373-380). With the reset values reg_cmd_prot=0 and reg_cmd_nonsec=0 (ctrl.sv:757-758) this gives 3'b100. m_ahb2axi_axi_if.sv:130 passes o_axi_arprot through with no reset gating, so ARPROT=4 at every reset edge, which explains 100% fails. In addition, o_axi_wdata/wstrb = w_wr_data_rd_data (ctrl.sv:667-668, axi_if.sv:117-118) is the resetless FIFO read regist…
- **Options:** (a) Fix RTL: in ctrl.sv p_com_axi_req, default w_axi_ar_prot/ar_cache/ar_addr/ar_size to 0 and assign the mapped values only in ENUM_ST_RD_AR (ctrl.sv:671-680). Default w_axi_w_data/w_strb to 0 unless w_axi_w_valid (ctrl.sv:667-668). That keeps the payload stable while VALID is high and meets the reset values without adding reset logic to axi_if. (b) Clarify the spec: state whether the 'Reset / idle value' column for Data(valid with VALID) ports is binding during reset. If it is not, remove tho…

## 5. What this verification does not cover

**57 requirement(s) cannot be checked by simulation** (static, structural, timing, process...). They need another method: lint, CDC, STA, synthesis, review. First ones:

- AA-2.1-01 (): The RTL shall follow the VLSIT RTL Design Rules v2 (REF-003) as the mandatory baseline for naming, hierarchy, single-clock, reset and synthesis. — *static_or_structural*
- AA-2.2-01 (): User-approved decisions in §20 may restrict legal protocol behavior but must not contradict it. — *design_guideline*
- AA-3-01 (REQ-VER-001): Verification must be derived from this specification and REF-001/REF-002, not from generated RTL or internal RTL names/structure. — *design_guideline*
- AA-3-24 (REQ-IF-001): The single top module m_ahb2axi_top must expose exactly the fixed clock, reset, AHB and AXI ports listed in §6.2. — *static_or_structural*
- AA-3-26 (REQ-CLK-001): AHB and AXI interfaces must use the same rising-edge clock input i_clk_core. — *static_or_structural*
- AA-3-27 (REQ-CLK-001): No second clock port or clock-domain crossing is permitted. — *static_or_structural*
- AA-3-28 (REQ-RESET-001): The bridge must expose one active-low reset input i_rst_n_core and use it directly without an internal reset synchronizer. — *static_or_structural*
- AA-3-29 (REQ-RESET-001): The SoC reset source must synchronize deassertion to i_clk_core before the reset reaches the IP. — *not_applicable_to_dut*
- AA-3-36 (REQ-PARAM-001): Read and write ID-count parameters must be in the range 1..8. — *static_or_structural*
- AA-3-44 (REQ-RTL-001): RTL must follow REF-003; the single top module contains only structural instances and each module is in a same-named file. — *static_or_structural*
- AA-3-45 (REQ-REG-001): The IP must have no software-visible CSR interface; all configuration is static at elaboration. — *static_or_structural*
- AA-4-02 (): A parameter value outside its legal range must be treated as an elaboration error. — *static_or_structural*
- AA-5.1-01 (): All sequential logic and FIFO clock/reset pins use the shared i_clk_core and i_rst_n_core. — *static_or_structural*
- AA-5.1-04 (): The five FIFO instances have depths 2, 16, 2, 2 and 2 entries respectively, with software-reset inactive and both clock/reset pins tied to shared inputs. — *static_or_structural*
- AA-6.2-01 (): AHB and AXI interface signals must use the rising edge of i_clk_core, and i_rst_n_core must be the only reset input. — *static_or_structural*
- … 42 more in work/rtm.json

**1 requirement(s) only partly or not proven:** AA-15.3-05 (NOT_PROVEN)

Outside this flow in every case: formal proof, CDC/RDC analysis, static timing, synthesis, DFT.

## 6. Weak spots of the verification itself

Code or cover points never reached (first ones):

- line m_ahb2axi_axi_if.sv:19
- line m_ahb2axi_axi_if.sv:22
- line m_ahb2axi_axi_if.sv:44
- line m_ahb2axi_axi_if.sv:47
- line m_ahb2axi_axi_if.sv:66
- line m_ahb2axi_axi_if.sv:90
- line m_ahb2axi_ctrl.sv:57
- line m_ahb2axi_ctrl.sv:60
- line m_ahb2axi_ctrl.sv:82
- line m_ahb2axi_ctrl.sv:85

### Formal check (SymbiYosys)

Every input sequence of up to 20 cycles was searched (one global clock); result {'BOUNDED': 2, 'CEX': 9, 'PROVEN': 8, 'VACUOUS': 1}. PROVEN holds for every cycle; BOUNDED found no counterexample within the depth. Details: `work/formal.md`.

- **CHK-001 CEX** — triage: A_rtl_wrong: Through step 10 the trace contains many AHB transfers, some of them illegal (AHB address/control changes while HREADY=0, for example steps 8->9 and 11->12). There is one B handshake at step 7 with BRESP=3 (DECERR). At step 10 a NONSEQ Device-E write (HPROT=5) is accepted. At step 11 the bridge driv… (trace work/formal/CHK-001_base.vcd)
- **CHK-002 CEX** — triage: A_rtl_wrong: Step 1: NONSEQ INCR8 write, HPROT=28 (Normal Write-back, eligible), accepted. Step 2: IDLE with HSEL=1 and HREADY=1; the write gets its early OKAY (HREADYOUT=1). Step 3: IDLE with HSEL=1 and HREADY=1, which is the antecedent. Step 4: the manager presents a NONSEQ read. The bridge drives o_ahb_hread… (trace work/formal/CHK-002_base.vcd)
- **CHK-005 CEX** — triage: A_rtl_wrong: Long trace (16 steps). AWREADY is 1 at steps 4-9 and 0 from step 10 on. At step 10 a SEQ write with HPROT=89 (HPROT[6]=1, which must be rejected) is accepted, and at step 11 a SEQ write to 0xFFFFFFFD with HSIZE=1 (misaligned, must be rejected) is accepted. Both enter the write command FIFO. The fai… (trace work/formal/CHK-005_base.vcd)
- **CHK-011 CEX** — triage: A_rtl_wrong: Step 1: NONSEQ write, HBURST=5 (INCR8), HPROT=4 (HPROT[6:2]=00001, Device-E, not aggregatable), HADDR=0, HSIZE=2, accepted. Then IDLE. Step 4: the bridge issues AWVALID=1 with o_axi_awaddr=4095 (0xFFF), o_axi_awsize=5, AWLEN=0, AWBURST=INCR, WLAST=1. The checker computes aw_end = 0xFFF + (1<<5) = 4… (trace work/formal/CHK-011_base.vcd)
- **CHK-012 CEX** — triage: A_rtl_wrong: Step 1: NONSEQ SINGLE write, HSIZE=1, HADDR=0, HPROT=0 (Device-nE), accepted. Step 4: AWVALID=1 with o_axi_awsize=4 (16 bytes), awaddr=0, awprot=4, WLAST=1. a_CHK_012 fails at step 4 because awsize > 2. In the same cycle o_axi_arsize=1, showing that reg_cmd_size holds the correct HSIZE=1. (trace work/formal/CHK-012_base.vcd)
- **CHK-014 VACUOUS**
- **CHK-015 CEX** — triage: A_rtl_wrong: Step 1: NONSEQ INCR8 write, HPROT=28 (eligible Normal Write-back), accepted. Step 2: the write data phase completes with an early OKAY (HREADYOUT=1), and in the same cycle the manager drives a NONSEQ read (HSEL=1, HREADY=1, HPROT=0, HSIZE=0), which is accepted on the AHB bus (checker h_acc=1). Step… (trace work/formal/CHK-015_base.vcd)
- **CHK-016 CEX** — triage: A_rtl_wrong: Step 1: NONSEQ INCR8 write, HPROT=28, accepted. Step 2: the step-1 beat gets an early OKAY (HREADYOUT=1), and in the same cycle a NONSEQ SINGLE write (HBURST=0, HPROT=28, HSEL=1, HREADY=1) is accepted on the AHB bus. This is beat j=2 of the waiting class (SINGLE). Step 3: HREADYOUT=1, HRESP=0, so b… (trace work/formal/CHK-016_base.vcd)
- **CHK-017 CEX** — triage: A_rtl_wrong: Step 1: NONSEQ INCR8 write, HSIZE=1, HADDR=0, HPROT=28, accepted. Step 2: the write gets an early OKAY (HREADYOUT=1), and in the same cycle a NONSEQ read with HPROT=32 (HPROT[5:2]=1000, a reserved code, so h_rej=1) is accepted on the AHB bus. Step 3: HREADYOUT=1 with HRESP=0, so the rejected transf… (trace work/formal/CHK-017_base.vcd)
- **CHK-020 CEX** — triage: A_rtl_wrong: i_rst_n_core=0 at steps 0-2 with all inputs quiet. During reset o_axi_arprot=4 (3'b100) while every other AXI payload output is 0 and both bursts are INCR. a_CHK_020 fails at step 0. (trace work/formal/CHK-020_base.vcd)

Environment assumptions (the formal results hold only for inputs that respect them; an assumption the specification does not require would hide bugs):

- ENV-01: While i_rst_n_core is low the AHB manager drives HSEL=0, HTRANS=IDLE, HWRITE=0, HBURST=SINGLE, HMASTLOCK=0 (AA-T1.7.2.2-03)
- ENV-02: The AXI Subordinate (reset consistently with the bridge) keeps BVALID and RVALID low during reset (AA-T1.7.2.2-17, AA-T1.7.2.2-24, AA-12-14)
- ENV-03: During a data phase owned by this Subordinate, the global HREADY equals this Subordinate's HREADYOUT (AHB5 multiplexor) (AA-6.1-01, AA-T1.7.3.1-01, AA-12-16)
- ENV-04: HWDATA/HWSTRB of a write data phase to this Subordinate stay stable while the data phase is extended by HREADY=0 (AA-T1.7.3.1-02, AA-6.1-01)
- ENV-05: SEQ and BUSY are presented to this Subordinate only inside a non-SINGLE burst (first beat of a burst is NONSEQ) (AA-6.1-01, AA-T1.7.3.1-01, AA-3-03)
- ENV-06: BVALID is asserted only after both the AW handshake and the final (WLAST) W handshake of an outstanding write (AA-6.1-02, AA-3-21, AA-T1.7.3.2-02)
- ENV-07: Once asserted, BVALID with BID/BRESP is held stable until BREADY (AA-T1.7.2.2-18, AA-6.1-02)
- ENV-08: BID returns the AWID of the outstanding write transaction (AA-6.1-02, AA-T1.7.3.2-05, AA-9-13)
- ENV-09: RVALID is asserted only after the AR handshake of an outstanding read (AA-6.1-02, AA-5.3-01, AA-T1.7.3.4-01)
- ENV-10: Once asserted, RVALID with RID/RDATA/RRESP/RLAST is held stable until RREADY (AA-T1.7.2.2-25, AA-6.1-02)
- ENV-11: RID returns the ARID of the outstanding read transaction (AA-6.1-02, AA-T1.7.3.2-05, AA-9-13)
- ENV-12: Every R beat of a single-beat read carries RLAST=1 (AA-T1.7.2.2-23, AA-5.4-07, AA-T1.7.3.2-03, AA-5.3-01)

## 7. Reproduce without NNC

`designs/ahb2axi_bridge/sim/` holds a Makefile that runs the same regression with Verilator and cocotb only (Linux or WSL):

```bash
cd designs/ahb2axi_bridge/sim
make regression SEED=1 2>&1 | tee sim.log
cd ../../.. && python -m nnc kit-check ahb2axi_bridge    # same outcome as the recorded results?
```

The kit reproduces the primary run base.s1; the other runs differ only by the settings in `run_set.json`.

## 8. Checklist before signing

Answer every item. Sign only if each one is true, or record why not in the approval note:

- [ ] I have read the delegated decisions of G1_rules and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G2_contract and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G3_verif_sources and agree with them (or I have corrected them).
- [ ] The RTL fault behind “test_chk_021_accept_qualifiers — CHK-021: AR handshakes expected 42 got 26 (all 4 runs)” is fixed, or accepted with a waiver.
- [ ] The RTL fault behind “test_chk_022_no_comb_ready_path — timeout after 190000 cycles waiting for AHB transfers t…” is fixed, or accepted with a waiver.
- [ ] The RTL fault behind “test_chk_023_device_bursts_singles — CHK-033/CHK-040 (CHK-023): expected 336 W beats got …” is fixed, or accepted with a waiver.
- [ ] The RTL fault behind “test_chk_024_wb_burst_aggregation — timeout after 68400 cycles waiting for AHB transfers …” is fixed, or accepted with a waiver.
- [ ] The RTL fault behind “test_chk_025_varying_attrs_singles — timeout after 4400 cycles waiting for AHB transfers …” is fixed, or accepted with a waiver.
- [ ] The RTL fault behind “test_chk_026_early_termination — timeout after 86000 cycles waiting for AHB transfers to …” is fixed, or accepted with a waiver.
- [ ] The RTL fault behind “Assertion CHK-002 — IDLE and BUSY transfers get zero-wait OKAY: 17 fails / 20390 hits (ba…” is fixed, or accepted with a waiver.
- [ ] The RTL fault behind “Assertion CHK-005 — AW VALID and payload stable until AWREADY: 2 fails / 14676 hits (base…” is fixed, or accepted with a waiver.
- [ ] The RTL fault behind “Assertion CHK-015 — AHB read completes only with its R beat and carries RDATA unchanged: …” is fixed, or accepted with a waiver.
- [ ] The RTL fault behind “Assertion CHK-016 — Waiting-class writes complete only after their BRESP: 9771 fails / 98…” is fixed, or accepted with a waiver.
- [ ] The RTL fault behind “Assertion CHK-017 — Locally rejected transfers end in ERROR and produce no W data: 4 fail…” is fixed, or accepted with a waiver.
- [ ] The RTL fault behind “Assertion CHK-020 — AXI payload outputs hold reset values during reset: 452 fails / 452 h…” is fixed, or accepted with a waiver.
- [ ] The requirements that simulation cannot check are assigned to another verification method.
- [ ] The unreached code and cover points are unreachable by design or accepted.
- [ ] Each formal environment assumption (verif/formal/nnc_env.sv) is an obligation the specification really places on the environment.
- [ ] Each formal counterexample or vacuous check is resolved (RTL, checker or environment) or accepted.
- [ ] I reproduced the regression (or CI did) and the outcome matches the report.

Then: `nnc gate approve ahb2axi_bridge G4_signoff --by "<your name>" --note "<waivers, open items>"`. The approval is bound to the current results.json: a later run makes it STALE.

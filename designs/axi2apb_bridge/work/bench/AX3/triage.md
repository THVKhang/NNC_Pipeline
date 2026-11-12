# Failure triage

Failures: 14; analysed: 12. The designer decides; nothing was changed.

## 1. test_chk_018_long_apb_wait: CHK-010: rlast=1 on beat 0 of ARLEN=0, got 0 at cycle 1008

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec/AXI2APB_Bridge_Design_Specification.md:170 "Read count is ARLEN+1; legal write count is AWLEN+1." (rules.json:1784, AB-5.4-05); spec:220 o_axi_rlast "Final read beat marker ... High only on final beat" (rules.json:2019, AB-6.2-06); spec:327 OP-001 Read "ARLEN+1 R beats; RID echo; final RLAST". contract.json:596 CHK-010: "o_axi_rlast == 1 exactly when k == the captured ARLEN (rlast=0 for k < ARLEN)". For ARLEN=0 the one beat (k=0) is the final beat, so RLAST must be 1. |
| RTL does | rtl/m_axi2apb_rd_seq.sv:358 loads the beat counter on AR accept with `reg_rd_beats_left <= {1'b0, i_axi_arlen}`, which is ARLEN, not ARLEN+1. Line 127 computes `w_ar_beats = arlen + 1`, but that value is never used for the counter. Line 326 drives `o_axi_rlast = (reg_rd_beats_left == 9'd1)`. With ARLEN=0 the counter is 0 when the single beat is presented at cycle 1008 after the 1000-cycle APB wait, so rlast=0. Lines 283-286 then send the FSM to REQ, not IDLE, because beats_left != 1. Line 377 decrements 0 to 9'h1FF, so the read would continue for hundreds of extra APB reads and beats. |
| Test does | verif/tests/test_axi2apb_bridge.py:865 issues make_read(id, 0x5000, length=0, size=2, INCR), a single-beat read. The APB completer holds PREADY low for WAIT=1000 cycles (lines 856, 859). The scoreboard captures len from the AR bus at the handshake (line 501). For each rvalid edge it computes k = number of earlier R beats (line 597) and `exp_last = 1 if k == cur['len']` (line 601). It asserts at line 602, so it expects rlast=1 on beat 0. Line 894 also expects rd.r[0]['last']==1. The SVA in verif/sva/nnc_chk_axi_r.sv:137-139 checks the same property independently (`o_axi_rlast == (rbeat_k == cap_len)`), and sim.log:364 shows 'NNC_FAIL CHK-010 @10170000' at the same time. |
| A_rtl_wrong | For: rd_seq.sv:358 loads ARLEN where the spec requires ARLEN+1 beats (spec:170). rd_seq.sv:326 and 283 treat the value 1 as the last beat, so every read is off by one. The write sequencer loads `awlen + LPARA_COUNT_ONE` (wr_seq.sv:339), and the read side's own unused w_ar_beats (rd_seq.sv:127) also adds 1, so the omission looks unintended. All 12 failures fit one pattern: ARLEN=0 gets no RLAST, and ARLEN=N gets RLAST at beat N-1. The Python scoreboard and the SVA checker are separate implementations and both flag it (sim.log:431 CHK-010 fails=18).<br>Against: None found. The RTL comment at rd_seq.sv:336 ('advance only after each R handshake') does not define a different beat-count convention. |
| B_test_wrong | For: None of substance. The expected value comes from ARLEN sampled on the bus at the AR handshake (test py:501).<br>Against: test py:601 matches contract.json:596 and the AXI rule (ARLEN+1 beats, RLAST on the last one) exactly. The SVA (nnc_chk_axi_r.sv:139) uses the same formula and fails at the same times. A single-beat read with RLAST=0 is illegal in AXI. |
| C_spec_unclear | For: None.<br>Against: The spec states ARLEN+1 beats and final-beat RLAST in several places: spec:170, 220, 302 ('AxLEN ... Beats minus one'), 316, 327 and 384. |
| Options | Fix the RTL in rtl/m_axi2apb_rd_seq.sv:358 so the counter loads ARLEN+1, e.g. `reg_rd_beats_left <= w_ar_beats;` or `({1'b0,i_axi_arlen} + 9'd1)`. Lines 283, 291, 326 and 376 can stay as they are (last beat when beats_left==1). After the fix, rerun to confirm that ARLEN=0 gives one beat with RLAST=1 and that the FSM returns to IDLE without the 0→0x1FF underflow. No test or spec change is needed. |

## 2. test_chk_019_arbitration_round_robin: CHK-010: rlast=0 on beat 0 of ARLEN=1, got 1 at cycle 8

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:170 "Read count is ARLEN+1" (AB-5.4-05). spec:220 RLAST "High only on final beat" (AB-6.2-06). contract.json:596 CHK-010: rlast=1 exactly when k == ARLEN, and rlast=0 for k < ARLEN. For ARLEN=1, beat 0 must have RLAST=0 and beat 1 must have RLAST=1. |
| RTL does | rd_seq.sv:358 loads reg_rd_beats_left = ARLEN = 1. On the first R beat (cycle 8), line 326 drives o_axi_rlast = (1 == 1) = 1. Line 283 sends the FSM to IDLE and line 332 asserts o_rd_done, so the read ends after one beat instead of two. |
| Test does | test py:909 r1 = make_read(id, 0x0100, length=1), a 2-beat INCR read, with w1, r2 and w2 submitted together (lines 909-913) to exercise arbitration. The scoreboard at py:601-602 expects rlast=0 on beat k=0 because 0 != ARLEN=1. The SVA nnc_chk_axi_r.sv:139 flags the same thing (sim.log:366). |
| A_rtl_wrong | For: The counter at rd_seq.sv:358 is loaded with ARLEN instead of ARLEN+1, so RLAST comes one beat early and the burst is cut short. wr_seq.sv:339 uses +1 for the same job. All 12 failures share this off-by-one.<br>Against: None found. |
| B_test_wrong | For: None. The failure is in the R-beat bookkeeping, not in the arbitration stimulus.<br>Against: py:601 matches contract.json:596 and spec:170/220, and the independent SVA agrees. |
| C_spec_unclear | For: None.<br>Against: spec:302 defines AxLEN as 'Beats minus one', and spec:327 requires 'ARLEN+1 R beats; ... final RLAST'. |
| Options | Fix the RTL at rd_seq.sv:358 to load ARLEN+1 (use w_ar_beats). The arbitration checks in this test (py:915-919) can only be judged after that fix, because the shortened read changes when the read ends. No test or spec change is needed. |

## 3. test_chk_021_response_backpressure: CHK-010: rlast=0 on beat 14 of ARLEN=15, got 1 at cycle 540

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:170 "Read count is ARLEN+1". spec:220 RLAST "High only on final beat". contract.json:596: rlast=1 exactly when k == ARLEN. For ARLEN=15, beat 14 must have RLAST=0 and beat 15 must have RLAST=1. |
| RTL does | rd_seq.sv:358 loads 15. Line 377 decrements it once per R handshake, so on beat 14 (after 14 handshakes) the counter is 1. Line 326 then asserts o_axi_rlast at cycle 540, one beat early. Lines 283-284 end the burst after 15 beats instead of 16. RREADY backpressure does not affect this: the counter only decrements on rready (line 375). |
| Test does | test_chk_021 (py:987 wait_done) drives reads, including one with ARLEN=15, while RREADY is randomly backpressured. The scoreboard at py:597/601 counts R handshakes k and expects rlast=1 only at k==15. sim.log:367-369 shows the SVA CHK-010 also failing at 16320000, 16330000 and 16340000. |
| A_rtl_wrong | For: There is the same off-by-one in the counter at rd_seq.sv:358 (ARLEN loaded instead of ARLEN+1), so RLAST appears on beat ARLEN-1 regardless of backpressure.<br>Against: None found. Under backpressure the RTL holds rlast stable (CHK-009 has 0 failures in sim.log), so the early value is held, not glitched. |
| B_test_wrong | For: A wrong k under backpressure would be a possible test-side cause, but py:597 counts only completed handshakes (len(cur['r'])).<br>Against: The SVA independently counts rbeat_k only on rvalid&&rready (nnc_chk_axi_r.sv:112-113) and fails at the same time. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit at spec:170, 220 and 327. |
| Options | Fix the RTL at rd_seq.sv:358 so the counter loads ARLEN+1. No test or spec change is needed. |

## 4. test_chk_022_unsupported_reads: CHK-010: rlast=1 on beat 0 of ARLEN=0, got 0 at cycle 4

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:121 REQ-ERR-001 (rules.json:1028, AB-3-31): "unsupported reads return ARLEN+1 SLVERR beats, RLAST only on final beat, no APB". spec:238, 329 and 384 say the same ('ARLEN+1 SLVERR beats, zero data, final RLAST'). contract.json:631 CHK-012: "o_axi_rid and o_axi_rlast are checked by CHK-010, so there are exactly ARLEN+1 beats and RLAST is set only on the last one." |
| RTL does | Unsupported AR goes from IDLE to ENUM_ST_ERR (rd_seq.sv:270). The counter is still loaded with ARLEN (line 358), so for ARLEN=0 it is 0. In ERR state, line 326 drives o_axi_rlast = (0==1) = 0 at cycle 4. Lines 291-294 keep the FSM in ERR because beats_left != 1, and line 377 decrements 0 to 0x1FF. The bridge would return about 512 SLVERR beats instead of 1. |
| Test does | py:1033 submits a `bad` read built from _unsupported_cases() (py:1018-1021 and above: bad size, reserved burst, cache, 4 KiB crossing), together with a legal read (py:1034). The first case failing at cycle 4 has ARLEN=0. The scoreboard at py:601 expects rlast=1 on beat 0, and py:1032 confirms the case is classified unsupported. |
| A_rtl_wrong | For: The ERR path shares the beat counter loaded at rd_seq.sv:358 with ARLEN instead of ARLEN+1. REQ-ERR-001 requires ARLEN+1 beats with final RLAST, and the RTL produces ARLEN beats, or about 512 when ARLEN=0 because of the underflow.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The expectation follows AB-3-31 verbatim. The SVA also fails at the same time (sim.log:370 @16460000). |
| C_spec_unclear | For: The REQ-ERR-001 sentence is ungrammatical ('The bridge shall unsupported reads return').<br>Against: The intent is clear and is repeated at spec:238, 318, 329 and 384: ARLEN+1 SLVERR beats with RLAST on the final one. |
| Options | Fix the RTL at rd_seq.sv:358 to load ARLEN+1. This one change fixes both the legal and the error paths. Optionally, the designer can reword REQ-ERR-001 (spec:121) for grammar; the meaning does not change. No test change is needed. |

## 5. test_chk_024_read_pslverr: CHK-010: rlast=0 on beat 2 of ARLEN=3, got 1 at cycle 23

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:170 "Read count is ARLEN+1". spec:220 RLAST "High only on final beat". spec:349 WF-009 'middle APB read beat returns PSLVERR; later beats continue'. contract.json:596: rlast=1 exactly when k==ARLEN. |
| RTL does | rd_seq.sv:358 loads 3. After 2 R handshakes (line 377) the counter is 1, so on beat 2 at cycle 23 line 326 asserts RLAST and line 283 returns the FSM to IDLE. The 4th beat (and its APB read) is never issued. PSLVERR handling (lines 365-368) does not touch the counter. |
| Test does | test_chk_024 (py:1102) issues reads with ARLEN=3 and PSLVERR injected on chosen beats. py:601 expects rlast=0 on beat 2 because 2 != 3. SVA failure at sim.log:371 (@31240000). |
| A_rtl_wrong | For: The same counter off-by-one (rd_seq.sv:358) appears here. The error injection is incidental: the failing check is the RLAST position, not RRESP, and CHK-011 has 0 failures in sim.log.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The expectation matches the contract and spec, and the SVA confirms it. |
| C_spec_unclear | For: None.<br>Against: WF-009 (spec:349) says later beats continue after PSLVERR, which is consistent with ARLEN+1 beats. |
| Options | Fix the RTL at rd_seq.sv:358 to load ARLEN+1. Then rerun to confirm that the PSLVERR position cases also give the full 4 beats. No test or spec change is needed. |

## 6. test_chk_026_unmapped_default_completer: CHK-010: rlast=0 on beat 0 of ARLEN=1, got 1 at cycle 8

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:170 "Read count is ARLEN+1". spec:220 RLAST "High only on final beat". contract.json:596: rlast=0 for k < ARLEN. |
| RTL does | rd_seq.sv:358 loads ARLEN=1, so the first R beat (cycle 8) has beats_left==1. Line 326 asserts RLAST, and the burst ends after 1 of 2 beats (line 283). |
| Test does | test_chk_026 (py:1157) reads ARLEN=1 to an unmapped address, which the default completer answers. py:601 expects rlast=0 on beat 0. SVA failure at sim.log:372 (@32700000). |
| A_rtl_wrong | For: The same off-by-one at rd_seq.sv:358 causes it. The failure does not depend on address decoding.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The expectation is derived from the ARLEN on the bus and matches the spec. The SVA agrees. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit. |
| Options | Fix the RTL at rd_seq.sv:358 to load ARLEN+1. No test or spec change is needed. |

## 7. test_chk_027_random_legal_bursts: CHK-010: rlast=0 on beat 254 of ARLEN=255, got 1 at cycle 1777

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:302 AxLEN '8 | Beats minus one | 1–256 beats'. spec:170 "Read count is ARLEN+1". spec:220 RLAST "High only on final beat". contract.json:596. |
| RTL does | rd_seq.sv:358 loads 255 (the 9-bit counter would hold 256 but is never given it). After 254 handshakes the counter is 1, so line 326 raises RLAST on beat 254 at cycle 1777. The 256th beat and its APB read are never produced. |
| Test does | test_chk_027 (py:1234) runs corner bursts, including ARLEN=255 INCR. py:601 expects rlast=1 only at k=255. SVA failures at sim.log:373-375. |
| A_rtl_wrong | For: The same off-by-one appears here. reg_rd_beats_left is 9 bits wide (rd_seq.sv:95), which suggests the designer meant it to hold up to 256 = ARLEN+1, but line 358 loads only ARLEN.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: ARLEN=255 is legal per spec:302 (1–256 beats). The expectation matches the contract. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit. |
| Options | Fix the RTL at rd_seq.sv:358 to load ARLEN+1 (w_ar_beats, which is already 9 bits). No test or spec change is needed. |

## 8. test_chk_028_subword_unaligned: CHK-010: rlast=1 on beat 0 of ARLEN=0, got 0 at cycle 16

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:170 "Read count is ARLEN+1", so ARLEN=0 is one beat. spec:220 RLAST "High only on final beat". contract.json:596: rlast=1 when k==ARLEN=0. |
| RTL does | rd_seq.sv:358 loads 0, so at cycle 16 line 326 gives rlast=0. Lines 283-286 then go to REQ, and line 377 underflows the counter to 0x1FF, so the read continues issuing APB reads. |
| Test does | test_chk_028 (py:1279) issues a single-beat subword/unaligned read (ARLEN=0) after a write. py:601 expects rlast=1 on beat 0. SVA failure at sim.log:376 (@50830000). |
| A_rtl_wrong | For: The same off-by-one at rd_seq.sv:358 causes it, and for ARLEN=0 it also underflows the counter.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: A single-beat read must carry RLAST=1 (spec:220). The SVA agrees. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit. |
| Options | Fix the RTL at rd_seq.sv:358 to load ARLEN+1. No test or spec change is needed. |

## 9. test_chk_029_pprot_passthrough: CHK-010: rlast=0 on beat 0 of ARLEN=1, got 1 at cycle 8

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:170 "Read count is ARLEN+1". spec:220 RLAST "High only on final beat". contract.json:596. |
| RTL does | rd_seq.sv:358 loads 1, so line 326 asserts RLAST on beat 0 at cycle 8 and line 283 ends the burst after 1 beat. |
| Test does | test_chk_029 (py:1313) issues ARLEN=1 reads with varied ARPROT to check PPROT. py:601 expects rlast=0 on beat 0. SVA failure at sim.log:378. |
| A_rtl_wrong | For: The same off-by-one at rd_seq.sv:358 causes it. PPROT handling is not involved.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The expectation matches the contract and spec. The SVA agrees. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit. |
| Options | Fix the RTL at rd_seq.sv:358 to load ARLEN+1. No test or spec change is needed. |

## 10. test_chk_030_id_echo: CHK-010: rlast=0 on beat 5 of ARLEN=6, got 1 at cycle 45

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:170 "Read count is ARLEN+1". spec:220 RLAST "High only on final beat". AB-3-13 (rules.json:538) 'echo ARID on every R beat'. contract.json:596. |
| RTL does | RID echo is correct: o_axi_rid = reg_rd_id (rd_seq.sv:308), and the rid check at py:600 passed. The counter loaded at line 358 is 6, so after 5 handshakes it is 1 and line 326 raises RLAST on beat 5 at cycle 45, one beat early. |
| Test does | test_chk_030 (py:1354) sends a group of reads with different IDs and lengths, including ARLEN=6. py:600 checks rid (passes), and py:601-602 expects rlast=0 on beat 5. SVA failures at sim.log:379-381. |
| A_rtl_wrong | For: The same off-by-one at rd_seq.sv:358 causes it. The ID part of CHK-010 passes, and only the RLAST position fails.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The expectation matches the contract and spec. The SVA agrees. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit. |
| Options | Fix the RTL at rd_seq.sv:358 to load ARLEN+1. No test or spec change is needed. |

## 11. test_chk_031_reset_mid_transaction: CHK-010: rlast=0 on beat 0 of ARLEN=1, got 1 at cycle 42

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:170 "Read count is ARLEN+1". spec:220 RLAST "High only on final beat". contract.json:596. |
| RTL does | After reset, the post-reset tie read ra has ARLEN=1. rd_seq.sv:358 loads 1, so line 326 asserts RLAST on its first beat at cycle 42. The reset logic itself (lines 338-348) clears the counter properly, so this is not a reset defect. |
| Test does | py:1394 ra = make_read(id, 0x7100, length=1) and py:1395 wa = make_write(...) are submitted together after the reset (_tie_after_reset, called from test_chk_031). py:601 expects rlast=0 on beat 0 of ARLEN=1. SVA failure at sim.log:382 (@52080000). |
| A_rtl_wrong | For: The same off-by-one at rd_seq.sv:358 causes it. The failure happens on a fresh post-reset read, not on the interrupted one.<br>Against: None found that points to reset behaviour. |
| B_test_wrong | For: None.<br>Against: The expectation matches the contract and spec. The SVA agrees. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit. |
| Options | Fix the RTL at rd_seq.sv:358 to load ARLEN+1. Then rerun to check the rest of CHK-031 (reset cancel and the post-reset arbitration tie). No test or spec change is needed. |

## 12. test_regression_random: CHK-010: rlast=0 on beat 6 of ARLEN=7, got 1 at cycle 51

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:170 "Read count is ARLEN+1". spec:220 RLAST "High only on final beat". contract.json:596. |
| RTL does | rd_seq.sv:358 loads 7. After 6 handshakes the counter is 1, so line 326 raises RLAST on beat 6 at cycle 51 and line 283 ends the burst one beat early. |
| Test does | The random regression issues a legal ARLEN=7 read. py:601 expects rlast=1 only at k=7. The SVA summary sim.log:431 reports 'NNC_CHECK CHK-010 hits=852 fails=18' for the whole run (sim.log:384 @52690000 for this test). sim.log also shows 'CHK-016 hits=874 fails=2'; this may be a side effect of the shortened or underflowed read bursts and needs confirming after the fix. |
| A_rtl_wrong | For: The same off-by-one at rd_seq.sv:358 causes it. Every one of the 18 SVA failures fits it.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The expectation matches the contract and spec. Two independent checkers agree. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit. |
| Options | Fix the RTL at rd_seq.sv:358 to load ARLEN+1. Rerun the regression and check whether the 2 CHK-016 SVA failures go away too; if they do not, triage them separately. No test or spec change is needed. |


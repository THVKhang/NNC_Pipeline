# Failure triage

Failures: 19; analysed: 12. The designer decides; nothing was changed.

## 1. test_chk_012_strict_later_latency_3_2 — CHK-010: o_full=0 expected (write-view occupancy 7) got 1 at 464.0 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec/SyncFIFO_Design_Specification.md:532 (§10.6 write-domain table): "| full flop | next occupancy equals DEPTH |"; :534 "| o_full | block OR full flop |"; :213 "o_full is 1 whenever the occupancy is `PARA_SFIFO_DEPTH`"; :134 REQ-FUNC-004 "o_full shall be 1 whenever PARA_SFIFO_DEPTH words are stored; it may be 1 while a place is free only because the freed place is not yet visible in the write domain (conservative flag)". rules.json:4753 (SF-10.6-02): "the full flop is set when next occupancy equals DEPTH". contract.json:463 CHK-010: "o_full == (OCC_W(t) == PARA_SFIFO_DEPTH) ... Consequences: o_full=1 in the cycle after the write that stores the 8th word". |
| RTL does | rtl/m_vlsit_sfifo_wr.sv:155 `reg_full <= (w_occ_nxt >= PARA_SFIFO_DEPTH - 1);` — the full flop is set when the next occupancy is 7 (DEPTH-1), not 8. o_full = w_wr_blk | reg_full (:232). With i_rst_n_sw=1 and busy=0, the edge that accepts the 7th word sets reg_full=1, so o_full=1 is seen at the next write edge (464 ns) with only 7 words stored. Then w_wr_acc (:117) blocks the 8th write, so the FIFO can hold only 7 words. The read side compares correctly (rtl/m_vlsit_sfifo_rd.sv:151 `reg_empty <= (w_occ_nxt == '0)`). The other flags are not affected: reg_full_thr uses `>= w_full_thr_ext` (:156). |
| Test does | After cases A–C, test_chk_012 calls write_words(env, words) with DEPTH=8 words (verif/tests/test_sync_fifo.py:679-682). Write_words drives one word per write cycle while o_full=0 (:487-491). The passive Monitor counts WA on each accepted write (:329-334). It computes exp_w_occ = WA - RA, with RA taken from read edges strictly earlier (:336-341). At the next write edge it checks o_full == (exp_w_occ == DEPTH) (:316-318). After 7 accepted writes and no reads, exp_w_occ=7, so the expected o_full is 0; the DUT shows 1. The test would also later assert o_full=1 after 8 writes (:682); this can't be met, because the 8th write is refused. |
| A_rtl_wrong | For: Spec :532 and rules.json SF-10.6-02 (:4753) both say the full flop is set when next occupancy *equals DEPTH*. RTL :155 uses `>= DEPTH - 1`, an off-by-one. The read-side twin (rd.sv:151) uses the exact `== 0` compare. The SVA checker verif/sva/nnc_chk_wr.sv:81 uses the same `occ_q == PARA_SFIFO_DEPTH` as the Python model. The same 'occupancy 7' mismatch appears in every test that fills the FIFO, across all clock ratios (sim.log:45-240), so it doesn't depend on the clock ratio or edge alignment.<br>Against: None found in the files. The conservative-flag allowance (spec :134, :279) covers only a lag caused by a read that is not yet visible. Here no read is pending (exp_w_occ includes all RA from earlier read edges), so early assertion at 7 is not covered. |
| B_test_wrong | For: The monitor could be wrong only if its WA/RA bookkeeping miscounted an accept or a read at a coincident edge.<br>Against: The failure also occurs with equal clocks and no reads (CHK-015 fill phase, CHK-016, CHK-017 ratio 10_10), where WA is simply the count of writes. The model (:316-318) matches contract CHK-010 (contract.json:463) and spec :532 word for word. The RTL line :155 shows the cause directly. |
| C_spec_unclear | For: REQ-FUNC-004 (spec :134) allows o_full=1 'while a place is free' in some conditions. Someone could read that as allowing an almost-full flag.<br>Against: The same sentence limits this to 'only because the freed place is not yet visible in the write domain'. Spec :532, :213 and contract CHK-010/CHK-015 ('o_full=0 sampled at E0..E7; o_full=1 sampled at E8') are explicit and agree with each other. |
| Options | Fix RTL (recommended by the evidence): rtl/m_vlsit_sfifo_wr.sv:155 change to `reg_full <= (w_occ_nxt == PARA_SFIFO_DEPTH);` (or `>= PARA_SFIFO_DEPTH`), per spec :532. No test change is needed. Fix test: not justified, because the model matches the spec. Clarify spec: only if the designer really wants an almost-full o_full at DEPTH-1. That would change REQ-FUNC-004, §10.6 :532, CHK-010/CHK-015/CHK-017 and effective capacity (DEPTH-1 words), so it is not advisable. |

## 2. test_chk_013_random_ratios/ratio=0 (10_10) — CHK-010: o_full=0 expected (write-view occupancy 7) got 1 at 1434.001 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec/SyncFIFO_Design_Specification.md:532 "full flop | next occupancy equals DEPTH"; :213 "o_full is 1 whenever the occupancy is PARA_SFIFO_DEPTH"; rules.json:4753 SF-10.6-02; contract.json:463 CHK-010 "o_full == (OCC_W(t) == PARA_SFIFO_DEPTH)". |
| RTL does | rtl/m_vlsit_sfifo_wr.sv:155 `reg_full <= (w_occ_nxt >= PARA_SFIFO_DEPTH - 1)` sets the full flop when the write-view occupancy reaches 7. o_full (:232) is 1 with 7 words stored and no block. |
| Test does | Random writer/reader at 1:1 (test_sync_fifo.py:715-735, :515-567) with sw_prob=0.02. At this write edge sw=1 and busy=0. Monitor exp_w_occ=7 (WA-RA, :336-341), so the expected o_full is 0 (:316-318); the DUT shows 1. |
| A_rtl_wrong | For: Off-by-one compare at wr.sv:155 against spec :532 / SF-10.6-02. Same signature as all other failures.<br>Against: None found. |
| B_test_wrong | For: Random traffic with software resets could in principle confuse the WA/RA clearing (:343-346).<br>Against: The same mismatch appears in directed tests with no software reset and no reads. The occupancy reported is exactly DEPTH-1, which matches the RTL compare. |
| C_spec_unclear | For: The REQ-FUNC-004 conservative allowance (:134).<br>Against: That allowance is limited to reads not yet visible. §10.6 :532 is explicit. |
| Options | Fix RTL at wr.sv:155 (`== PARA_SFIFO_DEPTH`); then re-run. No test change. A spec change would make the FIFO capacity DEPTH-1 and is not advisable. |

## 3. test_chk_013_random_ratios/ratio=1 (12_8) — CHK-010: o_full=0 expected (write-view occupancy 7) got 1 at 1674.002 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :532 "full flop | next occupancy equals DEPTH"; :213; rules.json:4753 SF-10.6-02; contract.json:463 CHK-010. |
| RTL does | rtl/m_vlsit_sfifo_wr.sv:155 `>= PARA_SFIFO_DEPTH - 1`: o_full is set at write-view occupancy 7. |
| Test does | Random traffic, wr 12 ns / rd 8 ns (test_sync_fifo.py:715-735). The Monitor's write-view occupancy is 7 at this edge (:336-341), so the expected o_full is 0 (:317-318). |
| A_rtl_wrong | For: Same off-by-one at wr.sv:155. The spec and SVA (nnc_chk_wr.sv:81) both use == DEPTH.<br>Against: None found. |
| B_test_wrong | For: The strict-earlier RA rule at coincident edges could in theory be miscounted.<br>Against: The value is exactly DEPTH-1 in every failure, including directed tests without reads. The model follows contract CHK-010. |
| C_spec_unclear | For: The conservative-flag wording (:134).<br>Against: It applies only to read visibility lag. §10.6 :532 is explicit. |
| Options | Fix RTL wr.sv:155 to an exact DEPTH compare. No test or spec change is needed. |

## 4. test_chk_013_random_ratios/ratio=2 (8_12) — CHK-010: o_full=0 expected (write-view occupancy 7) got 1 at 2834.003 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :532 "full flop | next occupancy equals DEPTH"; :213; rules.json:4753; contract.json:463 CHK-010. |
| RTL does | rtl/m_vlsit_sfifo_wr.sv:155 sets reg_full at w_occ_nxt >= 7. o_full=1 (:232) with 7 words in the write view. |
| Test does | Random traffic, wr 8 ns / rd 12 ns. The Monitor expects o_full=0 for exp_w_occ=7 (test_sync_fifo.py:316-318). |
| A_rtl_wrong | For: Off-by-one at wr.sv:155 against spec :532.<br>Against: None found. |
| B_test_wrong | For: The model is complex (coincident-edge ordering).<br>Against: Same DEPTH-1 signature in simple equal-clock directed tests. The model matches the contract. |
| C_spec_unclear | For: REQ-FUNC-004 conservative allowance.<br>Against: It is restricted to freed places not yet visible. That is not the case at occupancy 7 with no pending read. |
| Options | Fix RTL wr.sv:155 (`== PARA_SFIFO_DEPTH`). |

## 5. test_chk_013_random_ratios/ratio=3 (8_16) — CHK-010: o_full=0 expected (write-view occupancy 7) got 1 at 3498.004 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :532; :213; rules.json:4753 SF-10.6-02; contract.json:463 CHK-010. |
| RTL does | rtl/m_vlsit_sfifo_wr.sv:155 `reg_full <= (w_occ_nxt >= PARA_SFIFO_DEPTH - 1)`, so the flag is set at 7. |
| Test does | Random traffic, wr 8 / rd 16. Write-view occupancy is 7, so the expected o_full is 0 (test_sync_fifo.py:316-318). |
| A_rtl_wrong | For: Off-by-one compare at wr.sv:155.<br>Against: None found. |
| B_test_wrong | For: Possible model bookkeeping error.<br>Against: Identical DEPTH-1 signature in all 12 failures, including directed tests. |
| C_spec_unclear | For: Conservative-flag wording.<br>Against: Spec §10.6 :532 is explicit. |
| Options | Fix RTL wr.sv:155. |

## 6. test_chk_013_random_ratios/ratio=4 (16_8) — CHK-010: o_full=0 expected (write-view occupancy 7) got 1 at 8986.005 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :532; :213; rules.json:4753; contract.json:463 CHK-010. |
| RTL does | rtl/m_vlsit_sfifo_wr.sv:155: the full flop is set at next occupancy >= DEPTH-1 = 7. |
| Test does | Random traffic, wr 16 / rd 8. The Monitor expects o_full=0 at write-view occupancy 7 (test_sync_fifo.py:316-318). |
| A_rtl_wrong | For: Off-by-one at wr.sv:155 against spec :532.<br>Against: None found. |
| B_test_wrong | For: Possible model bookkeeping error.<br>Against: Same signature everywhere. The model matches CHK-010. |
| C_spec_unclear | For: REQ-FUNC-004 conservative allowance.<br>Against: It is limited to read visibility lag. |
| Options | Fix RTL wr.sv:155. |

## 7. test_chk_013_random_ratios/ratio=5 (12_28) — CHK-010: o_full=0 expected (write-view occupancy 7) got 1 at 9298.006 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :532; :213; rules.json:4753; contract.json:463 CHK-010. |
| RTL does | rtl/m_vlsit_sfifo_wr.sv:155 `>= PARA_SFIFO_DEPTH - 1`. |
| Test does | Random traffic, wr 12 / rd 28. Expected o_full=0 at write-view occupancy 7 (test_sync_fifo.py:316-318). |
| A_rtl_wrong | For: Off-by-one at wr.sv:155.<br>Against: None found. |
| B_test_wrong | For: Possible model bookkeeping error.<br>Against: Same DEPTH-1 signature in directed tests. |
| C_spec_unclear | For: Conservative-flag wording.<br>Against: §10.6 :532 is explicit. |
| Options | Fix RTL wr.sv:155. |

## 8. test_chk_013_random_ratios/ratio=6 (28_12) — CHK-010: o_full=0 expected (write-view occupancy 7) got 1 at 9886.007 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :532; :213; rules.json:4753; contract.json:463 CHK-010. |
| RTL does | rtl/m_vlsit_sfifo_wr.sv:155 sets the full flag at occupancy 7. |
| Test does | Random traffic, wr 28 / rd 12. Expected o_full=0 at occupancy 7 (test_sync_fifo.py:316-318). |
| A_rtl_wrong | For: Off-by-one at wr.sv:155.<br>Against: None found. |
| B_test_wrong | For: Possible model bookkeeping error.<br>Against: Identical signature across all tests. |
| C_spec_unclear | For: Conservative-flag wording.<br>Against: §10.6 :532 is explicit. |
| Options | Fix RTL wr.sv:155. |

## 9. test_chk_013_random_ratios/ratio=7 (36_8) — CHK-010: o_full=0 expected (write-view occupancy 7) got 1 at 31198.008 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :532; :213; rules.json:4753; contract.json:463 CHK-010. |
| RTL does | rtl/m_vlsit_sfifo_wr.sv:155 `>= PARA_SFIFO_DEPTH - 1`. |
| Test does | Random traffic, wr 36 / rd 8 (the fast reader seldom lets the FIFO fill, so the failure comes late, at 31198 ns). Expected o_full=0 at occupancy 7 (test_sync_fifo.py:316-318). |
| A_rtl_wrong | For: Off-by-one at wr.sv:155. The failure appears only once occupancy reaches 7, consistent with the late failure time.<br>Against: None found. |
| B_test_wrong | For: Possible model bookkeeping error.<br>Against: Same DEPTH-1 signature everywhere. |
| C_spec_unclear | For: Conservative-flag wording.<br>Against: §10.6 :532 is explicit. |
| Options | Fix RTL wr.sv:155. |

## 10. test_chk_015_full_empty_overflow_underflow — CHK-010: o_full=0 expected (write-view occupancy 7) got 1 at 31604.01 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :532; contract.json:604 CHK-015 expected: "o_full=0 sampled at E0..E7; o_full=1 sampled at E8 (cycle after the 8th write)"; contract.json:463 CHK-010. |
| RTL does | rtl/m_vlsit_sfifo_wr.sv:155: after the 7th write (E6), reg_full=1, so o_full=1 is sampled at E7 and the write of D7 at E7 is refused (wr.sv:117). |
| Test does | Equal clocks, 10 ns. Write D0..D7 at E0..E7, reader idle (test_sync_fifo.py:783-796). At E7 the Monitor has exp_w_occ=7, expects o_full=0, and sees 1 (:316-318). The directed check at :797-798 (o_full=0 at E0..E7) would fail the same way. |
| A_rtl_wrong | For: This is the simplest case: no reads, equal clocks. 7 words stored, o_full=1. Directly contradicts spec :532 and CHK-015 expected.<br>Against: None found. |
| B_test_wrong | For: None. With no reads, WA=7 is unambiguous.<br>Against: The test follows the contract CHK-015 timeline exactly. |
| C_spec_unclear | For: None.<br>Against: The contract gives explicit edge numbers. |
| Options | Fix RTL wr.sv:155 (`reg_full <= (w_occ_nxt == PARA_SFIFO_DEPTH);`). |

## 11. test_chk_016_no_bypass_simultaneous — CHK-010: o_full=0 expected (write-view occupancy 7) got 1 at 31774.011 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :532; contract.json:618-619 CHK-016: "Write D0..D7 at E0..E7 (FIFO full, o_full=1 at E8)"; contract.json:463 CHK-010. |
| RTL does | rtl/m_vlsit_sfifo_wr.sv:155 sets the full flop when occupancy is 7, so o_full=1 at E7 and D7 is refused. |
| Test does | Equal clocks. Write D0..D7 at E0..E7 (test_sync_fifo.py:837-848). At E7 the Monitor expects o_full=0 (exp_w_occ=7) and sees 1 (:316-318). |
| A_rtl_wrong | For: Fill with no reads; o_full=1 after 7 words. Contradicts spec :532 and CHK-016.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The stimulus and expected values match the contract. |
| C_spec_unclear | For: None.<br>Against: Explicit edge-level expectations in the contract. |
| Options | Fix RTL wr.sv:155. |

## 12. test_chk_017_pointer_wrap/ratio=0 (10_10) — CHK-010: o_full=0 expected (write-view occupancy 7) got 1 at 32484.012 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :532; contract.json:634-635 CHK-017: "o_full=1 in the cycle after each fill to 8 words"; contract.json:463 CHK-010. |
| RTL does | rtl/m_vlsit_sfifo_wr.sv:155 `>= PARA_SFIFO_DEPTH - 1`: o_full rises at 7 stored words. |
| Test does | For L=1..8, put(L) then get(L) (test_sync_fifo.py:884-894). For L=7, after 7 writes the next write edge has exp_w_occ=7, so the expected o_full is 0; the DUT shows 1 (:316-318). L=1..6 pass, which fits a threshold of exactly 7. |
| A_rtl_wrong | For: L=1..6 pass and the first failure is at L=7. This matches the `>= DEPTH-1` compare at wr.sv:155.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The writes happen without concurrent reads (put then get), so WA-RA is unambiguous. |
| C_spec_unclear | For: None.<br>Against: Spec §10.6 :532 is explicit. |
| Options | Fix RTL wr.sv:155. |


# Failure triage

Failures: 33; analysed: 12. The designer decides; nothing was changed.

## 1. test_chk_014_nominal_latency/per=0 — CHK-014: o_full=1 expected right after the last free entry got 0 (all 14 run configs)

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec/AsyncGrayFIFO_Design_Specification.md:131 REQ-FUNC-002 "The pointers shall cross between the two domains as Gray codes only. Each Gray pointer register shall change at most one bit per clock cycle"; :135 REQ-FUNC-006 "a Gray pointer register derived from the next binary pointer"; :476 "Gray pointer | `gray = bin XOR (bin >> 1)`"; :137 REQ-FUNC-008 full flag "shall be 1 whenever the write domain has no free entry ... never be 0 while the FIFO is physically full". contract.json CHK-014 expected: "After the 8th write edge, o_full=1 at once." |
| RTL does | rtl/m_vlsit_afifo_wr.sv:138 `assign w_wgray_nxt = w_wbin_nxt;` — no binary-to-Gray conversion, so reg_wgray (:149-154) and o_wr_gray (:226) hold the BINARY pointer. Compare the read side rtl/m_vlsit_afifo_rd.sv:130 `w_rgray_nxt = w_rbin_nxt ^ (w_rbin_nxt >> 1)`, which does convert. The full compare at wr.sv:106 `reg_wgray == (w_rgray_s ^ LPARA_FULL_MSK)` then compares a binary value to a Gray value. In the failing cycle: xfer() left wptr=rptr=1. After 8 more writes reg_wbin=9 so reg_wgray=4'b1001; w_rgray_s=Gray(1)=4'b0001, ^4'b1100 = 4'b1101 ≠ 1001, so w_full_n=0 and o_full (wr.sv:125) =0 while 8 words are stored. sim_runs/base.s1.log:129-138 also shows NNC_FAIL CHK-013/CHK-006 at these times (571000, 1094000 ps). CHK-013(c) needs o_full_thr==o_full when i_full_thr=8; o_full_thr uses the binary occupancy (wr.sv:120,126) and is 1, o_full is 0. |
| Test does | verif/tests/test_async_gray_fifo.py:696-708 — clocks 10/14 ns, ft=DEPTH, et=0. It calls xfer (single word, :400-419) and then fill_tr (:422-455): idle LMAX+3 write edges (:427), then 8 back-to-back writes (:429). It expects o_full=0 at each accepting edge (:431-433) and o_full=1 at write edge ns[-1]+1 (:434-435). The expectation comes from contract CHK-014 "o_full=1 at once" and REQ-FUNC-008. The write domain knows its own pointer with zero latency, and the read pointer has settled during the idle. |
| A_rtl_wrong | For: wr.sv:138 skips the Gray encoding that spec :135/:476 require and that rd.sv:130 does. A hand calculation of the failing cycle (binary 1001 vs expected 1101) gives o_full=0, which matches the observed value. The failure shows in every config (base, syn, cell1/3/4, macro, small, wr_slow, rd_slow), so it does not depend on the sync cell or the memory branch. That fits a pointer-encoding bug common to all of them.<br>Against: None found. The first xfer (wptr 0->1) passes because 0001 is the same in binary and Gray, which fits the bug. Spec :1272 has an SVA-002 one-bit-change check, but no contract check implements it (AF-3-03 is listed as not_observable_at_interface), so this bug got through to the flag checks. |
| B_test_wrong | For: fill_tr contains a 'Hand fix 2026-11-11' (test:425-427), so the test was recently edited around fill timing.<br>Against: The hand fix only adds idle cycles before the fill. The expected o_full=1 after 8 accepted writes is a zero-latency local condition required by REQ-FUNC-008 (spec:137) and CHK-006(a). The scoreboard/SVA (CHK-006, CHK-013) independently flag the same cycles in base.s1.log:129-138. |
| C_spec_unclear | For: None of substance.<br>Against: The spec states the Gray encoding exactly (:476 `gray = bin XOR (bin >> 1)`) and the full-flag requirement plainly (:137). The contract expected value "o_full=1 at once" is unambiguous. |
| Options | Fix RTL: in rtl/m_vlsit_afifo_wr.sv:138 change to `assign w_wgray_nxt = w_wbin_nxt ^ (w_wbin_nxt >> 1);` (the same as rd.sv:130), then rerun the full regression. Optional strengthening, not a weakening: add an internal assertion that $countones(o_wr_gray ^ $past(o_wr_gray)) <= 1 and that o_wr_gray == bin2gray(reg_wbin) (spec SVA-002, :1272), so this class of bug is caught directly. No test or spec change is indicated. |

## 2. test_chk_014_nominal_latency/per=1 — CHK-014: o_full=1 expected right after the last free entry got 0 (clocks 14/6 ns)

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Same as per=0: spec:131 REQ-FUNC-002 (Gray crossing), :135 REQ-FUNC-006 (Gray register derived from next binary pointer), :476 `gray = bin XOR (bin >> 1)`, :137 REQ-FUNC-008 (full never 0 while physically full). contract.json CHK-014 expected: "After the 8th write edge, o_full=1 at once." |
| RTL does | rtl/m_vlsit_afifo_wr.sv:138 `w_wgray_nxt = w_wbin_nxt` makes the write 'Gray' register binary. wr.sv:106 compares binary reg_wgray with Gray w_rgray_s ^ 4'b1100. After xfer (wptr=rptr=1) plus 8 writes: 4'b1001 vs 4'b1101, so o_full=0 (wr.sv:125). The clock ratio (14/6) has no effect: the mismatch is a value-encoding error, not a timing one. base.s1.log:135-138 shows CHK-013/CHK-006 NNC_FAIL at 1094000/1108000 ps, inside this test. |
| Test does | test:695-708 with per=(14,6): xfer (:400-419) then fill_tr (:422-455). The test expects o_full=1 at the write edge after the 8th accepted write (:434-435), from contract CHK-014 and REQ-FUNC-008. |
| A_rtl_wrong | For: Same root cause as per=0. wr.sv:138 has no Gray conversion, unlike rd.sv:130 and spec :476. The values worked out by hand reproduce o_full=0. The failure does not depend on the clock ratio.<br>Against: None found. |
| B_test_wrong | For: The test was hand-edited (test:425-427).<br>Against: The edit only adds idle time. The expectation is the spec-mandated zero-latency local full condition, and the SVA checkers CHK-006/CHK-013 fail independently in the same cycles. |
| C_spec_unclear | For: None.<br>Against: Spec :476 and :137 are explicit. |
| Options | Fix RTL at rtl/m_vlsit_afifo_wr.sv:138: `assign w_wgray_nxt = w_wbin_nxt ^ (w_wbin_nxt >> 1);`. Rerun. No test or spec change is indicated. |

## 3. test_chk_015_latency_with_model — CHK-015: o_empty=1 expected after reading the only word got 0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:138 REQ-FUNC-009 "The empty flag ... shall never be 0 while the FIFO is physically empty"; :131/:135/:476 Gray crossing with `gray = bin XOR (bin >> 1)`; :477 the read side converts with "Bit i of binary = XOR of Gray bits i..". contract.json CHK-015 expected: "CHK-005 and CHK-006 report no error." CHK-006(b): "if N == 0 and P is empty, then o_empty=1". |
| RTL does | The write side launches a binary pointer (wr.sv:138, :226). The read side treats it as Gray: rd.sv:97 `w_empty_n = (reg_rgray == w_wgray_s)` and rd.sv:104-109 Gray-to-binary. First isolated xfer: wptr 0->1, and 0001 is the same in binary and Gray, so it passes. Second xfer: wptr=2 launches 4'b0010, which is Gray(3). The read side sees occupancy 3-1=2 (rd.sv:112). After the single accepted read, reg_rbin=2, reg_rgray=Gray(2)=4'b0011 ≠ 4'b0010, so o_empty (rd.sv:117) stays 0 with nothing left. base.s1.log:139-142 shows NNC_FAIL CHK-005/CHK-006 at 1740000/1755000 ps, which matches the 1746.68 ns failure. |
| Test does | test:711-752: clocks 10/13 ns, ft=8, et=0. It does 100 isolated xfer() calls (:726-729). xfer (:400-419) writes one word into the empty FIFO, checks latency and data, reads it with read_ready (:414), and asserts o_empty=1 at the next read edge (:417-418). The expectation comes from REQ-FUNC-009 and CHK-006(b): after the only word is read, the FIFO is physically empty. |
| A_rtl_wrong | For: The binary pointer is launched where Gray is required (wr.sv:138 vs spec:476, rd.sv:130). The hand-derived 0010 vs 0011 mismatch explains o_empty=0 on the second transfer. The independent scoreboard (CHK-005/006) flags the same time. The failure also occurs in model_off and syn runs, so the metastability model does not cause it.<br>Against: None found. |
| B_test_wrong | For: Under the metastability model the latency is S..S+2, so a test could sample too early.<br>Against: The failing check is o_empty=1 AFTER a local read. That is a zero-latency local condition, and a slow crossing cannot keep the flag 0 (pessimism only delays the fall of o_empty). The failure is identical with the model off (model_off.s1, syn.s1). |
| C_spec_unclear | For: None.<br>Against: Spec :138 and :476-477 are explicit. |
| Options | Fix RTL at rtl/m_vlsit_afifo_wr.sv:138: `assign w_wgray_nxt = w_wbin_nxt ^ (w_wbin_nxt >> 1);`. Rerun CHK-015 with all 5 seeds to collect the L=2/3/4 coverage. No test change is indicated. |

## 4. test_chk_016_random_ratios/pair=0 (10/10) — CHK-016: FIFO not drained, 25 words left

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:132 REQ-FUNC-003 "Every accepted write shall be read exactly once. No word shall be lost, duplicated, or reordered."; :138 REQ-FUNC-009 (empty only when no word); :131/:476 Gray crossing. contract.json CHK-016 expected: "Every accepted word is read exactly once and in write order. At the end of the drain: o_empty=1, Q is empty, and o_full=0." |
| RTL does | wr.sv:138 launches the binary write pointer as o_wr_gray. On the read side, rd.sv:97 (empty when reg_rgray == w_wgray_s) and rd.sv:104-112 (occupancy from a Gray-to-binary conversion of a binary value) give wrong flags for most pointer values. In the drain, o_empty becomes 1 when reg_rgray equals the binary write pointer, i.e. at rbin = gray2bin(wbin) rather than wbin. The reader can stop with words still in Q, or read past the written data. On the write side, wr.sv:106 misdetects full, so writes can overwrite unread entries or be rejected wrongly. The result is 25 words that never become readable. |
| Test does | test:758-779 with pair (10,10): random ft/et (:765), then run_traffic (:620-651) with random densities and burst phases until 2000 accepted words. The drain at :644-645 sets W.d=0, R.d=1 and calls wait_drained (:574-579), which waits up to 60*DEPTH+4000 read edges for the scoreboard Q/P to empty. The expectation comes from contract CHK-016 / REQ-FUNC-003: every word written gets read. |
| A_rtl_wrong | For: The common root cause wr.sv:138 produces exactly this class of failure, where the empty compare stops at the wrong pointer. Every config fails, including model_off and syn, so it is not metastability. The base.s1.log NNC_FAIL CHK-005/CHK-006 entries (e.g. :143-188) show scoreboard and flag errors throughout the regression.<br>Against: No error message from this exact pair was quoted in the failure text; only the drain timeout appears. The specific 25 count was not reproduced by hand. |
| B_test_wrong | For: wait_drained has a finite limit (test:575) and depends on the reader model actually issuing reads.<br>Against: The limit (≥4480 read edges) is far beyond the time needed to drain 25 words at R.d=1.0. Equivalent drains elsewhere fail for the same root cause, and the other pairs show direct CHK-005/006 data and flag errors. |
| C_spec_unclear | For: None.<br>Against: REQ-FUNC-003 and the Gray encoding (:476) are unambiguous. |
| Options | Fix RTL at rtl/m_vlsit_afifo_wr.sv:138 (`w_wbin_nxt ^ (w_wbin_nxt >> 1)`) and rerun all six pairs. If a drain timeout remains after the fix, inspect the R model gating (R.gate=True at :644) separately. Do not raise or remove the wait_drained limit. |

## 5. test_chk_016_random_ratios/pair=1 (10/10.3) — CHK-005: 9477 scoreboard/flag errors, first: 'CHK-006: occupancy = DEPTH but o_full=0 at write edge', 'occupancy 9 > DEPTH', 'occupancy 10 > DEPTH'

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:137 REQ-FUNC-008 full flag "shall never be 0 while the FIFO is physically full"; :132 REQ-FUNC-003 no word lost/duplicated; :476 Gray encoding. contract.json CHK-006(a): "N <= PARA_AFIFO_DEPTH (8), and if N == PARA_AFIFO_DEPTH, then o_full=1 ... a write never overwrites an unread entry." |
| RTL does | wr.sv:106 full compare uses reg_wgray, which is binary because of wr.sv:138, against the Gray-coded synchronized read pointer. When the true occupancy reaches 8, the binary pattern does not equal rgray_s^1100, so o_full=0 (wr.sv:125). The write at wr.sv:109 is accepted, giving occupancy 9, then 10. Entries get overwritten, which produces the later 'o_rd_data expected head 0xc3962e1c got 0x58399c72' CHK-005 errors. |
| Test does | test:758-779 with pair (10,10.3): random traffic. The scoreboard (tb.finish, test:~360) collects CHK-005/006 errors. The CHK-006(a) expectation comes from the reference queue size N, computed independently of the DUT pointers. |
| A_rtl_wrong | For: The first error is exactly the symptom of a broken full compare: N=DEPTH with o_full=0, then N>DEPTH. That follows directly from wr.sv:106 comparing a binary pointer (wr.sv:138) with a Gray one. Identical in all 14 configs.<br>Against: None found. |
| B_test_wrong | For: The scoreboard counts reads at i_clk_rd edges 'up to the current time'. With near-equal clocks (10/10.3), a read and a write edge very close together could be ordered differently.<br>Against: Being one edge off in the ordering cannot produce occupancy 9 and 10 (> DEPTH) on consecutive edges, followed by data mismatches. A wrong head value (0x58399c72 vs 0xc3962e1c) is real data corruption. |
| C_spec_unclear | For: None.<br>Against: REQ-FUNC-008 and CHK-006(a) are explicit. |
| Options | Fix RTL at rtl/m_vlsit_afifo_wr.sv:138. Rerun. No test or spec change is indicated. |

## 6. test_chk_016_random_ratios/pair=2 (10/23) — CHK-016: FIFO not drained, 684 words left

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:132 REQ-FUNC-003; :137/:138 REQ-FUNC-008/009; :476 Gray encoding. contract.json CHK-016 expected: "At the end of the drain: o_empty=1, Q is empty". |
| RTL does | Same root cause, wr.sv:138. With a fast writer (10 ns) and slow reader (23 ns) the FIFO is often full. The broken full compare (wr.sv:106) lets writes be accepted past DEPTH. The scoreboard Q grows (684 words) far beyond the 8 physical entries, so those words can never be read and the drain cannot finish. The broken empty compare (rd.sv:97 on a binary value) also stops the reader early. |
| Test does | test:758-779, run_traffic (:620-651) then wait_drained (:574-579). Expected value: Q empty after the drain (CHK-016). |
| A_rtl_wrong | For: 684 words left is far more than DEPTH=8, so the DUT accepted writes while physically full (REQ-FUNC-008 violated). That is the expected effect of wr.sv:138 / :106. Seen in every config.<br>Against: None found. |
| B_test_wrong | For: The drain limit is finite (test:575).<br>Against: Q > DEPTH cannot come from the testbench being slow. It means the DUT accepted writes it had no room for. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit. |
| Options | Fix RTL at rtl/m_vlsit_afifo_wr.sv:138 and rerun. No test change is indicated. |

## 7. test_chk_016_random_ratios/pair=3 (10/50) — CHK-016: FIFO not drained, 1359 words left

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:132 REQ-FUNC-003; :137 REQ-FUNC-008 "never be 0 while the FIFO is physically full"; :476. contract.json CHK-016 expected: "Q is empty" after the drain and CHK-006(a) N <= DEPTH. |
| RTL does | wr.sv:138 (binary launched as Gray) makes wr.sv:106 full detection fail. With the writer 5x faster, many writes are accepted while full, so the scoreboard Q reaches 1359 entries against 8 physical entries. The read-side empty compare (rd.sv:97) is also wrong for non-trivial binary values. |
| Test does | test:758-779 with pair (10,50); run_traffic then wait_drained (:574-579). |
| A_rtl_wrong | For: The leftover count grows with the write/read ratio: 25 at 10/10, 684 at 10/23, 1359 at 10/50. That matches over-acceptance of writes caused by a broken full flag, and the root cause is at wr.sv:138.<br>Against: None found. |
| B_test_wrong | For: A slow reader needs a longer drain.<br>Against: Q holds 1359 words with only 8 entries, which is impossible for a correct DUT however long the drain. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit. |
| Options | Fix RTL at rtl/m_vlsit_afifo_wr.sv:138 and rerun. No test change is indicated. |

## 8. test_chk_016_random_ratios/pair=4 (23/10) — CHK-005: 9718 errors, first 'CHK-006: o_empty=0 with nothing written at read edge', then o_rd_data head mismatches

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:138 REQ-FUNC-009 "It shall never be 0 while the FIFO is physically empty."; :132 REQ-FUNC-003; :477 read side converts Gray to binary. contract.json CHK-006(b): "if N == 0 and P is empty, then o_empty=1. So a read is never accepted when nothing was written". |
| RTL does | The read side receives the binary write pointer (wr.sv:138, :226) and compares it as Gray: rd.sv:97 `reg_rgray == w_wgray_s`. With the reader faster than the writer, the FIFO is often empty with rptr == wptr = b. reg_rgray=Gray(b) differs from binary b for most b (e.g. b=2: 0011 vs 0010), so o_empty=0 (rd.sv:117) with nothing written. Reads are then accepted (rd.sv:100), and o_rd_data shows stale entries (head mismatch 0xdb9893ed vs 0x9372d57b). |
| Test does | test:758-779 with pair (23,10). The scoreboard checks CHK-006(b) and CHK-005 at every read edge, with expectations taken from the reference queue. |
| A_rtl_wrong | For: 'o_empty=0 with nothing written' is the exact signature of comparing Gray(rptr) with binary(wptr). It is reproduced by hand for wptr=rptr=2, and it is the same pattern CHK-015 hits.<br>Against: None found. |
| B_test_wrong | For: None specific.<br>Against: The reference queue is independent of the DUT. An o_empty=0 on a physically empty FIFO violates REQ-FUNC-009 directly. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit. |
| Options | Fix RTL at rtl/m_vlsit_afifo_wr.sv:138 and rerun. No test change is indicated. |

## 9. test_chk_016_random_ratios/pair=5 (50/10) — CHK-016: FIFO not drained, 8 words left

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:132 REQ-FUNC-003; :138 REQ-FUNC-009; :476. contract.json CHK-016 expected: "At the end of the drain: o_empty=1, Q is empty". |
| RTL does | wr.sv:138 launches the binary write pointer. In the drain the read side declares empty (rd.sv:97) when reg_rgray equals the binary write pointer, which is not where rptr==wptr. The write side can also stop accepting, or accept wrongly, because of wr.sv:106. As a result 8 words in the scoreboard Q never become readable before the wait_drained limit. |
| Test does | test:758-779 with pair (50,10); run_traffic (:620-651) then wait_drained (:574-579). |
| A_rtl_wrong | For: Same root cause as the other pairs. Every config fails. 8 = DEPTH stranded words fits a broken full/empty compare.<br>Against: The exact cycle at which the 8 words got stranded was not traced in the log. |
| B_test_wrong | For: The drain limit is finite (test:575).<br>Against: About 4480 read edges at R.d=1.0 is far more than enough to drain 8 words from a correct FIFO. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit. |
| Options | Fix RTL at rtl/m_vlsit_afifo_wr.sv:138 and rerun. No test change is indicated. |

## 10. test_chk_017_synthesis_branch_regression — CHK-017: o_full=1 expected right after the last free entry got 0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json CHK-017 expected: "All assertions CHK-001..CHK-013 pass, there is no scoreboard error, and every sequence completes." It reuses the CHK-014 isolated latency measurement. spec:137 REQ-FUNC-008; :476 Gray encoding; :135 REQ-FUNC-006. |
| RTL does | The failure is the same as CHK-014. xfer leaves wptr=rptr=1. fill_tr writes 8 words, so reg_wbin=9 and reg_wgray=4'b1001 (binary, wr.sv:138). wr.sv:106 compares it with Gray(1)^1100=4'b1101, so o_full=0. The bug is in the pointer logic and does not depend on the VLSIT_SYNTHESIS cell branch, which explains why the non-syn configs fail too. |
| Test does | test:782-798: tb.init(ft=DEPTH, et=0). 5 iterations of xfer (:794) then fill_tr (:795). fill_tr asserts o_full=1 at write edge ns[-1]+1 (:434-435). |
| A_rtl_wrong | For: Identical mechanism to CHK-014, from wr.sv:138. The failure appears in syn.s1 and in all non-syn configs, so the synthesis branch is not the cause.<br>Against: None found. |
| B_test_wrong | For: In non-syn builds the test runs on the simulation branch (test:788-790 not_verifiable note).<br>Against: That affects only the coverage claim, not this assertion. o_full=1 after 8 accepted writes is required by REQ-FUNC-008 in every build. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit. |
| Options | Fix RTL at rtl/m_vlsit_afifo_wr.sv:138 and rerun, including the syn.s1 config. No test change is indicated. |

## 11. test_chk_018_write_n_read_n — CHK-018: after the last write o_full=1, o_full_thr=1 got 0,1

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json CHK-018 expected: "After the edge that accepts D7, o_full=1 and o_full_thr=1 (no read yet)." spec:137 REQ-FUNC-008; :476 `gray = bin XOR (bin >> 1)`; :478 occupancy is the binary pointer difference. |
| RTL does | From reset, 8 writes give reg_wbin=8=4'b1000. o_full_thr (wr.sv:126) uses the binary occupancy w_occ = reg_wbin - w_rbin_s = 8 (wr.sv:120), 8>=8, so o_full_thr=1, which is correct. o_full (wr.sv:125) uses wr.sv:106: reg_wgray holds binary 4'b1000 (wr.sv:138) instead of Gray(8)=4'b1100. w_rgray_s=0, 0^1100=1100 ≠ 1000, so o_full=0. The observed '0,1' is what you get with a correct binary path and a broken Gray path. |
| Test does | test:801-829 → scn_fill_drain (:458-480): 10/14 ns clocks, ft=8, 8 consecutive writes from reset (:462). It asserts o_full=0 at each accepting edge (:464-466) and o_full=1, o_full_thr=int(8>=8)=1 at the next edge (:467-469). Derived from contract CHK-018. |
| A_rtl_wrong | For: The split result (o_full=0 but o_full_thr=1) shows the binary occupancy path agrees with the test and only the Gray-compare path is wrong. That points straight at wr.sv:138 vs spec:476 (Gray(8)=1100, binary=1000).<br>Against: None found. |
| B_test_wrong | For: None specific.<br>Against: The test's o_full_thr expectation is met, which shows its pointer and occupancy accounting is right. The o_full expectation follows REQ-FUNC-008. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit. |
| Options | Fix RTL at rtl/m_vlsit_afifo_wr.sv:138: `assign w_wgray_nxt = w_wbin_nxt ^ (w_wbin_nxt >> 1);`. Rerun. No test change is indicated. |

## 12. test_chk_019_back_to_back_equal_clocks — CHK-019: read order differs from write order

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json CHK-019 expected: "o_rd_data is 0x01, 0x02, ..., 0x18 at the consecutive accepted edges, through the pointer wrap (24 > 16)." spec:132 REQ-FUNC-003 "No word shall be lost, duplicated, or reordered"; :131/:476 Gray crossing. |
| RTL does | wr.sv:138 launches the binary write pointer. During the 24-word burst the read side (rd.sv:97, :104-112) interprets binary values as Gray. For example, binary wptr=2 (0010) reads as Gray(3), and wptr=8 (1000) reads as gray2bin=15. So the read side sees words available that are not yet written, or the wrong occupancy, and accepts reads of stale or unwritten entries. The write side full compare (wr.sv:106) is also wrong across the wrap. The read sequence therefore diverges from the write sequence. The pytest repr shows the first 6 elements match, [1..6], and the divergence comes later. |
| Test does | test:832-882: both clocks 10 ns, ft=8. 24 writes of 1..24 (:865). The consumer (:847-862) sets i_rd_en=1 from the first o_empty=0 and counts accepted reads. Expected: tb.sb.reads[m0:] equals the accepted write data in order (:870-871), from REQ-FUNC-003 / contract CHK-019. |
| A_rtl_wrong | For: The order/exactly-once check is compared against the scoreboard's own record of accepted writes (test:870), so it does not depend on stimulus timing. The binary-for-Gray pointer at wr.sv:138 corrupts the empty and full decisions, which leads to reads of wrong entries. The failure is common to all configs.<br>Against: The exact divergence index is truncated in the message, so the precise failing cycle was not traced. |
| B_test_wrong | For: The consumer checks `not tb.sb.Q` (:851) and may stop early, and the 3 ns read-clock lag cannot be set (:839).<br>Against: Stopping early would make reads a prefix of exp. It would not produce a different element order. The phase offset affects only latency, not order. |
| C_spec_unclear | For: None.<br>Against: REQ-FUNC-003 is explicit. |
| Options | Fix RTL at rtl/m_vlsit_afifo_wr.sv:138 and rerun. If the order check still fails after the fix, dump tb.sb.reads vs exp around the first mismatch and check the wrap at pointer 8/16. No test change is indicated now. |


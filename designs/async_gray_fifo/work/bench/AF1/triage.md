# Failure triage

Failures: 33; analysed: 12. The designer decides; nothing was changed.

## 1. test_chk_014_nominal_latency/per=0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec/AsyncGrayFIFO_Design_Specification.md:137 (REQ-FUNC-008, rules.json AF-3-10 l.555): "The full flag ... shall be 1 whenever the write domain has no free entry, judged from the synchronized read pointer. It shall never be 0 while the FIFO is physically full." spec:241 INV-001/AF-5.4-01: occupancy (modulo 2 x depth) stays between 0 and PARA_AFIFO_DEPTH. The designer decision in rules.json:12776 says: "o_full = 1 exactly when the write-domain estimate (write pointer register minus synchronized read pointer, modulo 2 x depth) equals PARA_AFIFO_DEPTH. Any Gray or binary implementation giving these values is compliant." contract.json:561 (CHK-014 expected): "After the 8th write edge, o_full=1 at once." |
| RTL does | rtl/m_vlsit_afifo_wr.sv:35 defines LPARA_FULL_MSK = 32'd1 << (LPARA_PTR_W-1). For DEPTH=8 that is 4'b1000, so only the MSB is set. Line 106 computes w_full_n = (reg_wgray == (w_rgray_s ^ LPARA_FULL_MSK)). The comment at line 104 says "with its two MSBs inverted", but the code inverts only the MSB. Failing cycle: the FIFO is empty and rgray_s=0000. After the 8th accepted write, reg_wbin=8 and reg_wgray=1100. The compare value is 0000^1000=1000, which is not equal, so o_full (line 125) stays 0. In the same cycle w_occ=reg_wbin-w_rbin_s=8 (line 120), so o_full_thr=1 (line 126): the RTL's own binary estimate says full. Gray(n)^1000 = Gray(15-n), so this compare is true only when wbin = 15-rbin (mod 16). The occupancy is then odd and never 8. The read-side empty compare (rtl/m_vlsit_afifo_rd.sv:97, reg_rgray == w_wgray_s) is a plain equality and is not affected. |
| Test does | verif/tests/test_async_gray_fifo.py:696-708 sets clocks 10/14 ns and ft=DEPTH. It runs xfer, then fill_tr. fill_tr (l.422-455) first idles LMAX+3 write edges so that earlier reads have crossed (l.427). It then writes DEPTH random words at consecutive write edges (l.429), checks o_full=0 at each accepting edge (l.431-433), and at record ns[-1]+1 asserts o_full==1 (l.434-435). The expected value comes from contract CHK-014 l.561 and REQ-FUNC-008. Log sim_runs/model_off.s1.log:38-39 shows the independent scoreboard checker also firing: "CHK-006: occupancy = DEPTH but o_full=0 at write edge t=520691.0ps", followed by the CHK-014 assertion. |
| A_rtl_wrong | For: m_vlsit_afifo_wr.sv:35 builds the mask with one bit (1<<(PTR_W-1)). Its own comment at l.104 says the two MSBs must be inverted (the standard Cummings Gray full test cited in spec:1542). At the failing edge o_full_thr=1 (w_occ=8) while o_full=0, so the RTL contradicts itself. The failure happens in all 14 run configurations, including model off, syn, cell1/3/4, macro and small. The scoreboard check CHK-006 (contract l.365) fails at the same edge (model_off.s1.log:38).<br>Against: None found. The stimulus is a plain 8-word fill after an idle period that lets earlier reads cross, so the synchronized read pointer is settled. |
| B_test_wrong | For: The test has hand-edits dated 2026-11-11 (l.425-427) about o_full staying 1 late. A late or early synchronized pointer could in principle affect when o_full is sampled.<br>Against: The hand-edits concern o_full being 1 too long, not o_full being 0. The sampled record is the edge right after the 8th accepted write, with no read in flight (idle LMAX+3 first). Full needs only the local write pointer, so it has zero latency. The expectation matches spec REQ-FUNC-008, contract CHK-014 l.561 and decision rules.json:12776. |
| C_spec_unclear | For: rules.json:12774: "The exact full and empty equations (the MSB-inverted Gray compare or the binary compare) are not written anywhere." The spec gives no Gray formula.<br>Against: The open question was answered in rules.json:12776, which defines o_full by behaviour (estimate == DEPTH). REQ-FUNC-008 ("shall never be 0 while the FIFO is physically full") is unambiguous on its own. |
| Options | Fix RTL: in m_vlsit_afifo_wr.sv:35 set the mask to the top two pointer bits, e.g. LPARA_FULL_MSK = 32'd3 << (LPARA_PTR_W - 32'd2), so line 106 compares against rgray_s with its two MSBs inverted. Alternatively, use (w_occ == PARA_AFIFO_DEPTH) from the binary estimate already computed at line 120. For PTR_W=2 (DEPTH=2) the mask becomes 2'b11. Then re-run the full regression; CHK-006/CHK-020/021/024/026 should clear as well. No test change is needed. Optionally, add the explicit full/empty equation to the spec (Section 10.x) to close the rules.json:12774 question in the document itself. |

## 2. test_chk_014_nominal_latency/per=1

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Same as per=0. spec:137 REQ-FUNC-008: "It shall be 1 whenever the write domain has no free entry ... It shall never be 0 while the FIFO is physically full." rules.json:12776: o_full=1 exactly when the write-domain estimate equals PARA_AFIFO_DEPTH. contract.json:561: "After the 8th write edge, o_full=1 at once." |
| RTL does | rtl/m_vlsit_afifo_wr.sv:35 sets LPARA_FULL_MSK=4'b1000 (one bit). l.106 checks reg_wgray == rgray_s^1000. After 8 writes from an empty FIFO, wgray=1100 and the compare value is 1000, so o_full=0 (l.125), while w_occ=8 and o_full_thr=1 (l.120,126). The clock ratio (14 ns write, 6 ns read) does not matter: the compare is wrong for any settled pointer pair. |
| Test does | Same fill_tr path as per=0 with clocks i_clk_wr=14 ns and i_clk_rd=6 ns (test l.695, contract l.560 setting B). test l.434-435 asserts o_full==1 at the record after the last of DEPTH writes. sim_runs/model_off.s1.log:53-54 shows "CHK-006: occupancy = DEPTH but o_full=0 at write edge t=1002135.0ps" and then the CHK-014 assertion. |
| A_rtl_wrong | For: Same single-bit mask at wr.sv:35/106, which contradicts the comment at l.104. The failure does not depend on the clock ratio and occurs in every run configuration. The independent scoreboard check CHK-006 also flags it (model_off.s1.log:53).<br>Against: None found. |
| B_test_wrong | For: The faster read clock could in principle change the timing of the read pointer synchronization.<br>Against: The fill comes after an idle of LMAX+3 write edges (l.427), and full depends only on the local write pointer. The expected value matches the spec and the contract. |
| C_spec_unclear | For: The Gray full equation is not written in the spec (rules.json:12774).<br>Against: Resolved by the designer decision rules.json:12776 and by REQ-FUNC-008. |
| Options | Same fix as per=0. Correct LPARA_FULL_MSK in m_vlsit_afifo_wr.sv:35 to invert the two MSBs, or compare w_occ == PARA_AFIFO_DEPTH. No test change. Optionally write the full/empty equations into the spec. |

## 3. test_chk_015_latency_with_model

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:581-583 (CHK-015): "For every isolated read, o_full falls after write edge L with L in {2,3,4} ... No latency is below 2 or above 4." This assumes o_full=1 on a full FIFO, which REQ-FUNC-008 requires (spec:137): "It shall never be 0 while the FIFO is physically full." |
| RTL does | After the test fills DEPTH=8 words, reg_wgray=1100 and rgray_s settles to 0000 (or another settled value). wr.sv:106 compares against rgray_s^1000 (mask from l.35), which is not equal, so o_full=0 already before the isolated read. Therefore o_full is 0 at write edge 1 after the read. The check sees no 1->0 transition, so lead() returns L=0. The metastability model is irrelevant here: the failure also occurs in model_off and syn (model_off.s1.log:182: "expected ... 2 got 0"). |
| Test does | test l.711-752: clocks 10/13 ns, ft=DEPTH. After 100 isolated writes, it writes DEPTH words (l.730-732) and idles LMAX+3 read edges. Then, 100 times: idle, one read at Tr (l.736-737), take LMAX+3 write records after Tr (l.740), compute L=lead(E,'o_full',1) (l.741), and call chk_lat (l.742, l.90-93), which requires S<=L<=LMAX. L=0 means o_full was already 0 at the first write edge after Tr. |
| A_rtl_wrong | For: L=0 means o_full was never 1 on the full FIFO. This is the same single-MSB mask defect (wr.sv:35/106) that makes CHK-014/017/018 fail directly. It fails in all 14 runs, including model off, so the metastability model is not the cause. CHK-006 errors appear in the same runs (model_off.s1.log:198, 213).<br>Against: The test does not assert o_full=1 before the read, so the failure message reports a latency, not the missing full. |
| B_test_wrong | For: The test could check o_full=1 before Tr to give a clearer message. Also, if refill after a read were not accepted, the FIFO might not be full; test l.745 writes one word without checking o_full.<br>Against: Every word before the first read is accepted (o_full is 0 throughout), so the FIFO really holds 8 words (the scoreboard Q). The latency expectation follows the contract. The test logic is sound once o_full behaves per spec. |
| C_spec_unclear | For: The exact Gray full equation is not in the spec (rules.json:12774).<br>Against: Behaviour is fixed by REQ-FUNC-008 and rules.json:12776. |
| Options | Fix RTL: correct the full mask in m_vlsit_afifo_wr.sv:35 (two MSBs inverted) or use w_occ==DEPTH, then re-run CHK-015 with the 5 seeds. Optional test improvement (not a weakening): assert o_full==1 at the write edge just before each isolated read, so this root cause shows directly instead of as L=0. |

## 4. test_chk_016_random_ratios/pair=0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:605-607 (CHK-016): "Every accepted word is read exactly once and in write order. At the end of the drain: o_empty=1, Q is empty, and o_full=0." CHK-001..CHK-013 never fail. spec:137 REQ-FUNC-008 (o_full never 0 while physically full). AF-10.4-01 (rules.json:5054): "an entry is rewritten only after the write domain has seen the read pointer pass it." INV-001 (rules.json:2526): occupancy between 0 and DEPTH. |
| RTL does | Because wr.sv:106 uses a one-bit mask (l.35), o_full does not rise at occupancy 8, and w_wr_acc (l.109) keeps accepting writes. Data is overwritten (AF-10.4-01 is violated), and the write pointer can run 16 or more ahead of the read pointer. The read side computes empty as reg_rgray == w_wgray_s (rd.sv:97), which is modulo 2 x DEPTH = 16. When the true occupancy is a multiple of 16, the read side sees empty, so those words can never be read. All the leftover counts are multiples of 16: 416, 384, 896, 1456, 208, 16 (pairs 0-5). This is consistent with pointer aliasing modulo 2 x DEPTH. |
| Test does | test l.758-779 uses pair (10,10), random thresholds, and run_traffic(tb,r,2000) (l.620-651) with random densities, including write-only bursts (W.d=1,R.d=0, l.628-629). At the end it stops writing, reads with density 1.0 (l.644), and wait_drained (l.574-579) waits up to 60*DEPTH+4000 read edges for the scoreboard Q to empty. It then asserts "FIFO not drained, 416 words left". Q only counts writes accepted with o_full=0 (contract CHK-005 l.342). |
| A_rtl_wrong | For: Write-only bursts push the FIFO past 8 because o_full never asserts at 8 (wr.sv:35/106). Logs show many CHK-006 'occupancy = DEPTH but o_full=0' errors during CHK-016 (model_off.s1.log:13650, 29789-29794, 50608). Leftover word counts are exact multiples of 2xDEPTH=16, as expected when the Gray pointers alias modulo 16. The same failure appears in every configuration.<br>Against: None found. The drain loop gives thousands of read edges, so a slow drain cannot explain hundreds of missing words. |
| B_test_wrong | For: The drain timeout (l.575) is finite, and the reader model may gate reads (R.gate).<br>Against: l.644 sets R.d=1.0 and R.gate=True before draining. The leftover counts are multiples of 16 rather than small residuals, and CHK-006 errors appear earlier in the run, which shows the DUT accepted writes beyond DEPTH. |
| C_spec_unclear | For: The full equation is not spelled out in the spec (rules.json:12774).<br>Against: Resolved by rules.json:12776, REQ-FUNC-008, INV-001 and AF-10.4-01. |
| Options | Fix RTL: correct LPARA_FULL_MSK (wr.sv:35) to the top two bits, or compare w_occ==PARA_AFIFO_DEPTH, then re-run all CHK-016 pairs. No test change. To make the root cause show directly, the designer may make the scoreboard CHK-006 errors fail the test at first occurrence instead of at finish(). |

## 5. test_chk_016_random_ratios/pair=1

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Same as pair=0: contract.json:606-607 (every accepted word read exactly once; Q empty at the end of the drain), REQ-FUNC-008 (spec:137), AF-10.4-01 (rules.json:5054), INV-001. |
| RTL does | Same defect at wr.sv:35/106. o_full is not asserted at occupancy 8, writes overwrite unread entries, and the pointers alias modulo 16 at the empty compare (rd.sv:97). 384 = 24 x 16 words are stranded in the reference queue. |
| Test does | Pair (10, 10.3), phase drift. Same run_traffic/wait_drained flow (test l.620-651, l.574-579), which asserts "FIFO not drained, 384 words left". |
| A_rtl_wrong | For: Same mechanism as pair=0. The leftover count is a multiple of 16, the failure is in every configuration, and CHK-006 flag errors appear in the logs.<br>Against: None found. |
| B_test_wrong | For: The drain timeout is finite.<br>Against: Reads run at 100% density during the drain. The missing words are a multiple of 2xDEPTH, which is a pointer-aliasing signature, not slowness. |
| C_spec_unclear | For: The Gray full equation is not in the spec.<br>Against: Behaviour is defined by rules.json:12776 and REQ-FUNC-008. |
| Options | Same as pair=0: fix the mask at wr.sv:35 (two MSBs) or use the binary estimate, then re-run. No test change. |

## 6. test_chk_016_random_ratios/pair=2

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Same as pair=0 (contract.json:606-607; spec:137 REQ-FUNC-008; AF-10.4-01; INV-001). |
| RTL does | Same defect at wr.sv:35/106. With write 10 ns and read 23 ns, the writer outruns the reader, so overrun past 8 is frequent. 896 = 56 x 16 words are stranded by modulo-16 aliasing at rd.sv:97. |
| Test does | Pair (10,23). Same flow, asserting "FIFO not drained, 896 words left" (test l.579). |
| A_rtl_wrong | For: Same mechanism. The faster writer gives a larger loss. The count is a multiple of 16, and the failure is in all configurations.<br>Against: None found. |
| B_test_wrong | For: The drain timeout is finite.<br>Against: The words are permanently lost, as the multiple-of-16 signature shows. A longer wait would not drain them. |
| C_spec_unclear | For: The equation is not written in the spec.<br>Against: Resolved by rules.json:12776. |
| Options | Fix the RTL full mask (wr.sv:35/106), then re-run. No test change. |

## 7. test_chk_016_random_ratios/pair=3

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Same as pair=0 (contract.json:606-607; spec:137; AF-10.4-01; INV-001). |
| RTL does | Same defect at wr.sv:35/106. Write 10 ns and read 50 ns gives the most overrun. 1456 = 91 x 16 words are stranded. |
| Test does | Pair (10,50). Same flow, asserting "FIFO not drained, 1456 words left". |
| A_rtl_wrong | For: Largest loss at the most write-dominant ratio, which is consistent with a missing full flag. The count is a multiple of 16.<br>Against: None found. |
| B_test_wrong | For: The drain timeout is finite.<br>Against: The aliasing signature shows the words are permanently lost. |
| C_spec_unclear | For: The equation is not written in the spec.<br>Against: Resolved by rules.json:12776. |
| Options | Fix the RTL full mask (wr.sv:35/106), then re-run. No test change. |

## 8. test_chk_016_random_ratios/pair=4

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Same as pair=0 (contract.json:606-607; spec:137; AF-10.4-01; INV-001). |
| RTL does | Same defect at wr.sv:35/106. The read side is faster (23/10), so overrun happens only in the write-only burst phases (test l.628-629). 208 = 13 x 16 words are stranded. |
| Test does | Pair (23,10). Same flow, asserting "FIFO not drained, 208 words left". |
| A_rtl_wrong | For: Smaller loss when the reader is faster, but still a multiple of 16. Write-only burst phases overrun the missing full flag.<br>Against: None found. |
| B_test_wrong | For: The drain timeout is finite.<br>Against: The words are permanently lost, as the multiple-of-16 signature shows. |
| C_spec_unclear | For: The equation is not written in the spec.<br>Against: Resolved by rules.json:12776. |
| Options | Fix the RTL full mask (wr.sv:35/106), then re-run. No test change. |

## 9. test_chk_016_random_ratios/pair=5

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Same as pair=0 (contract.json:606-607; spec:137; AF-10.4-01; INV-001). |
| RTL does | Same defect at wr.sv:35/106. Read 5x faster (50/10), so overrun is rare. Exactly 16 (=2xDEPTH) words are stranded: the write pointer ran one full pointer period ahead, and the read side's Gray equality (rd.sv:97) then reports empty. |
| Test does | Pair (50,10). Same flow, asserting "FIFO not drained, 16 words left". |
| A_rtl_wrong | For: A leftover of exactly 16 = 2xDEPTH is the clearest aliasing signature. It happens even with a much faster reader, during the write-only bursts.<br>Against: None found. |
| B_test_wrong | For: The drain timeout is finite.<br>Against: Exactly 2xDEPTH words left is not a timing residue. |
| C_spec_unclear | For: The equation is not written in the spec.<br>Against: Resolved by rules.json:12776. |
| Options | Fix the RTL full mask (wr.sv:35/106), then re-run. No test change. |

## 10. test_chk_017_synthesis_branch_regression

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:617-619 (CHK-017): "Run the CHK-016 random traffic with the CHK-029 random software resets, and the isolated single write/read latency measurement of CHK-014 ... every isolated read from full makes o_full fall exactly after write edge 2." This needs o_full=1 on a full FIFO, which spec:137 REQ-FUNC-008 requires. |
| RTL does | The full compare in m_vlsit_afifo_wr.sv:106 does not depend on the VLSIT_SYNTHESIS cell branch. With the mask from l.35 (4'b1000), o_full stays 0 after the 8th write (wgray=1100 vs 0000^1000), while o_full_thr=1 (w_occ=8). |
| Test does | test l.782-798 uses default clocks and ft=DEPTH. For 5 iterations it runs xfer, then fill_tr. fill_tr's assertion at l.434-435 (o_full==1 after DEPTH writes) fires on the first iteration. |
| A_rtl_wrong | For: Same assertion as CHK-014 with the same root cause (wr.sv:35/106). It fails in syn.s1 and in all non-synthesis builds, so it does not depend on the cell branch.<br>Against: None found. |
| B_test_wrong | For: The test runs on non-VLSIT_SYNTHESIS builds too (it marks those as not_verifiable, l.788-790), so the failure in those runs is not specific to the synthesis branch.<br>Against: The failure also occurs in syn.s1. The fill_tr expectation is correct per spec. |
| C_spec_unclear | For: The Gray full equation is not written in the spec.<br>Against: Resolved by rules.json:12776. |
| Options | Fix the RTL full mask (wr.sv:35/106), then re-run syn.s1 to also exercise the random-traffic and software-reset part, which is never reached now. No test change. |

## 11. test_chk_018_write_n_read_n

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:645-647 (CHK-018): "o_full must rise at the edge of the last free entry ... After the edge that accepts D7, o_full=1 and o_full_thr=1 (no read yet)." spec:137 REQ-FUNC-008. rules.json:12776: o_full=1 exactly when the write-domain estimate equals DEPTH. |
| RTL does | After D0..D7 are accepted, reg_wbin=8, reg_wgray=1100 and w_rgray_s=0000. wr.sv:120 gives w_occ=8, so o_full_thr=(8>=8)=1 (l.126). wr.sv:106 compares 1100 against 0000^1000=1000, so w_full_n=0 and o_full=0 (l.125). The observed values 0,1 match exactly. The two flags in the same module disagree about the same pointer state. |
| Test does | test l.801-829 sets clocks 10/14 ns and ft=DEPTH. scn_fill_drain (l.458-480) writes DEPTH words at consecutive edges with i_rd_en=0 (l.462), checks o_full=0 at each (l.464-466), and at the record after the last write asserts o_full==1 and o_full_thr==int(DEPTH>=ft)=1 (l.467-469). It got 0,1. |
| A_rtl_wrong | For: o_full_thr=1 together with o_full=0 shows that the binary occupancy is 8 but the Gray full compare misses it. The mask at wr.sv:35 has one bit, against the comment at l.104 (two MSBs). It fails in all configurations.<br>Against: None found. |
| B_test_wrong | For: None specific. This is the simplest directed fill with no reads.<br>Against: The expected value follows directly from contract l.647 and REQ-FUNC-008. With no reads, the synchronized read pointer is constant at 0. |
| C_spec_unclear | For: The Gray equation is not written in the spec (rules.json:12774).<br>Against: Resolved by rules.json:12776. |
| Options | Fix RTL: wr.sv:35 should become LPARA_FULL_MSK = 32'd3 << (LPARA_PTR_W-2), i.e. top two bits inverted, or set w_full_n = (w_occ == PARA_AFIFO_DEPTH). No test change. |

## 12. test_chk_019_back_to_back_equal_clocks

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:662-664 (CHK-019): "o_rd_data is 0x01, 0x02, ..., 0x18 at the consecutive accepted edges, through the pointer wrap." Every accepted word must be read in order (CHK-005, contract l.342). spec:137 REQ-FUNC-008 and INV-001 (rules.json:2526): occupancy never above DEPTH. Note contract l.664 also expects "o_full=0 at each of them" for DEPTH=8. That is tied to the default depth: with DEPTH=2 the FIFO legally fills, and the writes must then be held off by o_full. |
| RTL does | Config small.s1 uses PARA_AFIFO_DEPTH=2 and DATA_W=1 (sim_runs/small.s1.log:27), so PTR_W=2 and LPARA_FULL_MSK=2'b10 (wr.sv:35). The correct inversion is 2'b11. With rgray_s=00, wgray after 2 writes is Gray(2)=11, and the compare value is 00^10=10, so o_full=0 at occupancy 2. o_full only fires at wgray=10=Gray(3), occupancy 3. Log small.s1.log:162904-162909: "CHK-006: occupancy = DEPTH but o_full=0" and "occupancy 3 > DEPTH" during CHK-019. Entries are overwritten before they are read, so the read stream differs from the write stream. With DEPTH=8 and equal clocks, the round-trip occupancy never reaches 8, so the bug does not show and the other 13 runs pass. |
| Test does | test l.832-879 sets both clocks to 10 ns and writes 24 words with data i+1, masked to DW=1 so the values alternate 1,0 (l.865). A consumer reads at every edge once o_empty=0 (l.847-862). The test asserts sb.reads == the accepted write data (l.870-871). The order check runs unconditionally. Only the zero-gap and no-o_full parts depend on EXACT (l.872), and those are skipped here because the model is on (log l.162903). |
| A_rtl_wrong | For: The same one-bit full mask (wr.sv:35/106) means DEPTH=2 can hold 3 or more words, so data is overwritten. CHK-006 occupancy-3 errors in this exact test window (small.s1.log:162905-162909). The same signature appears in CHK-023 small.s1 (results.json:664 'occupancy 3 > DEPTH'). It fails only in the one configuration where back-to-back traffic can actually reach DEPTH.<br>Against: The metastability model is on in small.s1 (log l.27 +AFIFO_MSYNC_EN=1), which adds latency jitter. However, extra latency can only make flags more pessimistic, never cause reordering, if full is correct. |
| B_test_wrong | For: DW=1 makes the data alternate 1/0, so the failure message cannot show which word was lost. The test also assumes behaviour tuned to DEPTH=8, and with the model on it is marked partly not verifiable (l.840-841).<br>Against: The failing assertion (l.871) compares the read stream to the accepted-write stream, which is valid for any depth and model setting. Accepted writes are only those with o_full=0, so a correct DUT must match. |
| C_spec_unclear | For: contract CHK-019 expects 'o_full=0 at each of' the 24 writes, which cannot hold for DEPTH=2. The scenario text is written for the default depth.<br>Against: That part is not what failed: it is gated by EXACT, and the order check is depth-independent. REQ-FUNC-008 and INV-001 apply to all depths. |
| Options | Fix RTL: the two-MSB mask in wr.sv:35 (for PTR_W=2 it must be 2'b11), or w_occ==DEPTH. Re-run small.s1. Clarify the contract: state that the CHK-019 'o_full=0 at all 24 writes / zero gaps' expectation applies to DEPTH >= round-trip occupancy (e.g. 8), and what the expectation is for DEPTH=2. Optional test improvement: use data wider than DW or log the index, so a mismatch is diagnosable when DATA_W=1. This does not weaken the check. |


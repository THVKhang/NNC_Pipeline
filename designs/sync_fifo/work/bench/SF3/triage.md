# Failure triage

Failures: 24; analysed: 12. The designer decides; nothing was changed.

## 1. test_chk_012_strict_later_latency_3_2 — CHK-004: o_empty_thr=1 expected (occupancy 0, thr 0) got 0 at 120.0 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec/SyncFIFO_Design_Specification.md:137 REQ-FUNC-007: "o_empty_thr shall be 1 when the occupancy seen by the read side is less than or equal to i_empty_thr." Same at :253 (port table: "Occupancy in the read view is at or below i_empty_thr") and :548 (read-side flop table: "empty-threshold flop | next occupancy is at or below i_empty_thr"). rules.json SF-3-15 (line ~895) quotes REQ-FUNC-007. contract.json:309 CHK-004: "o_empty_thr == (OCC_R(t) <= i_empty_thr, zero-extended)". contract.json:155 gives reset value 1, which matches occupancy 0 <= any threshold. |
| RTL does | rtl/m_vlsit_sfifo_rd.sv:152 `reg_empty_thr <= (w_empty_thr_ext > w_occ_nxt);` is a strict compare (thr > occ, i.e. occ < thr). It does not mean occ <= thr. Line 218 `o_empty_thr = w_rd_blk | reg_empty_thr`. In this test i_empty_thr=0 (test line 629/630). After the hw reset release the occupancy is 0, so at the first i_clk_rd edge after release the flop loads (0 > 0) = 0. o_empty_thr then drops from its reset value 1 to 0 and is sampled 0 at the next read edge (120 ns). For comparison, the write side uses the inclusive form: rtl/m_vlsit_sfifo_wr.sv:156 `reg_full_thr <= (w_occ_nxt >= w_full_thr_ext);`. |
| Test does | Env.start((8,12), DEPTH, 0) and hw_reset(DEPTH, 0, "both") (test_sync_fifo.py:629-630) set i_empty_thr=0, with no traffic yet. The passive Monitor runs at every read edge. In Monitor._rd_edge (test_sync_fifo.py:269-274), with busy=0 at this edge and the previous one, it computes et_exp = 1 if exp_r_occ <= P['et'] else 0. exp_r_occ comes from the WA/RA counters (lines 294-299) and is 0 here, so et_exp=1. It compares this with the pre-edge sampled o_empty_thr, which is 0. |
| A_rtl_wrong | For: The spec says 'less than or equal to' / 'at or below' in three places (spec:137, :253, :548). The RTL uses strict '>' at rd.sv:152. The failure happens exactly at occ == thr (0,0), the one boundary where '<' and '<=' differ. The write-side twin uses the inclusive '>=' (wr.sv:156), so the read side is inconsistent with it. The contract's own directed expectations also need the inclusive form: CHK-014 expects o_empty_thr=1 at E3 with occ 0 and thr 0 (contract.json:571), and CHK-025 expects 'o_empty_thr=1 only while the read-view occupancy is 0' for v=0 (contract.json:806). sim.log:284-295 shows CHK-021 failing with ethr=0 while idle after release.<br>Against: None found in the spec. Nothing in the spec defines o_empty_thr as strictly below the threshold. |
| B_test_wrong | For: The test computes the expected value itself (line 272). If its comparison were wrong it would fail like this.<br>Against: Line 272 (`exp_r_occ <= P['et']`) is a literal translation of CHK-004 and REQ-FUNC-007. The occupancy model is 0 right after release, with no write. This matches spec reset semantics, and CHK-004 o_empty (line 271) passes at the same edge, so the occupancy model agrees with the RTL's empty flag. |
| C_spec_unclear | For: The spec uses two phrasings ('less than or equal to', 'at or below').<br>Against: Both phrasings mean the same inclusive comparison. They are consistent across REQ-FUNC-007, the port table, the flop table and the threshold table (spec:375: a value above DEPTH makes o_empty_thr always 1, which is consistent with <=). There is no ambiguity. |
| Options | Fix RTL (recommended): in rtl/m_vlsit_sfifo_rd.sv:152 change `reg_empty_thr <= (w_empty_thr_ext > w_occ_nxt);` to `reg_empty_thr <= (w_occ_nxt <= w_empty_thr_ext);` (or `w_empty_thr_ext >= w_occ_nxt`), then re-run the whole regression. All listed failures share this one root cause, as do the CHK-021 and later CHK-004 failures in sim.log. Fix test: not justified, because the test matches the spec. Clarify spec: only if the designer really wants strict '<' semantics. That would require rewriting REQ-FUNC-007, spec:253, :548, CHK-004, CHK-014 and CHK-025, and it would conflict with the reset value 1 / the 'always 1 above DEPTH' rule. Not recommended. |

## 2. test_chk_013_random_ratios/ratio=0 (10_10) — CHK-004: o_empty_thr=1 expected (occupancy 0, thr 0) got 0 at 3430.001 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec/SyncFIFO_Design_Specification.md:137 REQ-FUNC-007: "o_empty_thr shall be 1 when the occupancy seen by the read side is less than or equal to i_empty_thr."; spec:548 "empty-threshold flop | next occupancy is at or below i_empty_thr"; contract.json:309 CHK-004 "o_empty_thr == (OCC_R(t) <= i_empty_thr, zero-extended)". |
| RTL does | rtl/m_vlsit_sfifo_rd.sv:152 `reg_empty_thr <= (w_empty_thr_ext > w_occ_nxt);` is strict, so with occupancy 0 and the randomly chosen threshold 0 the flop loads 0, and o_empty_thr (line 218) is 0 when not blocked. |
| Test does | test_sync_fifo.py:727-730: for each release order the test draws ft, et = r.randint(0, THR_MAX) and applies them during hw_reset, then runs random traffic. Here et=0. Monitor._rd_edge line 272 expects o_empty_thr = (exp_r_occ <= et) = (0 <= 0) = 1. exp_r_occ is the read-view occupancy from WA/RA (lines 294-299). |
| A_rtl_wrong | For: The failure is at occ == thr, the only point where '>' and '>=' differ. The spec says inclusive (spec:137, :253, :548). The write side uses the inclusive form (wr.sv:156 `>=`). The same signature appears in every failing test.<br>Against: None in the spec. |
| B_test_wrong | For: The expected value comes from the test's own model.<br>Against: The model at line 272 matches CHK-004 and REQ-FUNC-007 literally. The o_empty check on the same occupancy (line 271) passes, so the occupancy model is consistent with the RTL. |
| C_spec_unclear | For: There are two wordings of the same rule.<br>Against: Both are inclusive. spec:375 (above DEPTH gives always 1) is also consistent with <=. |
| Options | Fix RTL: rd.sv:152 to `reg_empty_thr <= (w_occ_nxt <= w_empty_thr_ext);`. No test change. Clarify spec only if strict semantics are intended, which contradicts the current text and CHK-014/CHK-025. |

## 3. test_chk_013_random_ratios/ratio=1 (12_8) — CHK-004: o_empty_thr=1 expected (occupancy 0, thr 0) got 0 at 3542.002 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:137 REQ-FUNC-007 "o_empty_thr shall be 1 when the occupancy seen by the read side is less than or equal to i_empty_thr"; spec:548 "at or below i_empty_thr"; contract.json:309 CHK-004 "o_empty_thr == (OCC_R(t) <= i_empty_thr)". |
| RTL does | rtl/m_vlsit_sfifo_rd.sv:152 strict compare `w_empty_thr_ext > w_occ_nxt` gives 0 for occ=0, thr=0, so o_empty_thr=0 (line 218) at an unblocked read edge. |
| Test does | test_sync_fifo.py:727-728 picks random et (here 0) in hw_reset. Monitor line 272 expects (0 <= 0) = 1 and gets 0. The failure is at the first edge after release, before any traffic, at time 3542 ns. |
| A_rtl_wrong | For: The failure is at occ == thr. The RTL's strict '>' contradicts the inclusive spec text. The write side uses inclusive '>=' (wr.sv:156).<br>Against: None. |
| B_test_wrong | For: The expected value is computed by the model.<br>Against: The model formula at line 272 equals CHK-004. The o_empty check passes on the same occupancy. |
| C_spec_unclear | For: The spec has more than one phrasing.<br>Against: Every phrasing is inclusive. |
| Options | Fix RTL: rd.sv:152 to an inclusive compare (occ <= thr). No test change needed. |

## 4. test_chk_013_random_ratios/ratio=2 (8_12) — CHK-004: o_empty_thr=1 expected (occupancy 3, thr 3) got 0 at 4130.003 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:137 REQ-FUNC-007 "less than or equal to i_empty_thr"; spec:253 "at or below i_empty_thr"; spec:548 "next occupancy is at or below i_empty_thr"; contract.json:309 CHK-004 "o_empty_thr == (OCC_R(t) <= i_empty_thr, zero-extended)". |
| RTL does | rtl/m_vlsit_sfifo_rd.sv:152 `reg_empty_thr <= (w_empty_thr_ext > w_occ_nxt);`. With the read-view occupancy 3 and threshold 3, (3 > 3) = 0, so o_empty_thr=0. |
| Test does | Random traffic with et=3 drawn at test_sync_fifo.py:727. The monitor occupancy model (lines 294-299: WA counted over strictly earlier write edges minus RA) is 3. Line 272 expects (3 <= 3) = 1. This failure shows the bug is not only a reset/idle effect: it occurs mid-traffic at any occ == thr. |
| A_rtl_wrong | For: There is an exact boundary mismatch at occ == thr == 3. The spec is inclusive in all places. The write side uses inclusive '>=' (wr.sv:156).<br>Against: None in the spec. |
| B_test_wrong | For: The model's occupancy could in principle differ from the RTL view at cross-clock ratios.<br>Against: The o_empty assertion (line 271) and the CHK-006/CHK-007 scoreboard checks on the same occupancy did not fail before this point, which supports the model's occupancy. Only the threshold boundary differs. |
| C_spec_unclear | For: There are two wordings.<br>Against: Both are inclusive. |
| Options | Fix RTL: rd.sv:152 to `(w_occ_nxt <= w_empty_thr_ext)`. Re-run; if any mismatch remains at occ != thr, look at the occupancy model separately. |

## 5. test_chk_013_random_ratios/ratio=3 (8_16) — CHK-004: o_empty_thr=1 expected (occupancy 4, thr 4) got 0 at 14498.004 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:137 REQ-FUNC-007 "o_empty_thr shall be 1 when the occupancy seen by the read side is less than or equal to i_empty_thr"; spec:548; contract.json:309 CHK-004. |
| RTL does | rtl/m_vlsit_sfifo_rd.sv:152 strict '>' gives (4 > 4) = 0, so o_empty_thr=0 at an unblocked read edge. |
| Test does | Random traffic with random et=4 (test_sync_fifo.py:727). Monitor line 272 expects (4 <= 4) = 1 and gets 0. |
| A_rtl_wrong | For: The mismatch is at occ == thr. The RTL uses strict '>' while the spec and the write side (wr.sv:156) are inclusive.<br>Against: None. |
| B_test_wrong | For: The expected value is computed by the model.<br>Against: The formula equals CHK-004/REQ-FUNC-007, and the o_empty check on the same occupancy passes. |
| C_spec_unclear | For: There are multiple phrasings.<br>Against: All are inclusive. |
| Options | Fix RTL: rd.sv:152 to an inclusive compare. No test or spec change. |

## 6. test_chk_013_random_ratios/ratio=5 (12_28) — CHK-004: o_empty_thr=1 expected (occupancy 5, thr 5) got 0 at 29711.006 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:137 REQ-FUNC-007 "less than or equal to i_empty_thr"; spec:548 "at or below"; contract.json:309 CHK-004 "OCC_R(t) <= i_empty_thr". |
| RTL does | rtl/m_vlsit_sfifo_rd.sv:152 strict compare gives (5 > 5) = 0, so o_empty_thr=0. |
| Test does | Random traffic with et=5 (test_sync_fifo.py:727). Monitor line 272 expects 1 at occupancy 5. |
| A_rtl_wrong | For: The mismatch is at occ == thr. The RTL compare is strict against an inclusive spec.<br>Against: None. |
| B_test_wrong | For: The expected value is computed by the model.<br>Against: The model matches the spec, and the o_empty check passes on the same occupancy. |
| C_spec_unclear | For: There are two wordings.<br>Against: Both are inclusive. |
| Options | Fix RTL: rd.sv:152 to `(w_occ_nxt <= w_empty_thr_ext)`. |

## 7. test_chk_013_random_ratios/ratio=6 (28_12) — CHK-004: o_empty_thr=1 expected (occupancy 4, thr 4) got 0 at 41855.007 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:137 REQ-FUNC-007; spec:253; spec:548 (all inclusive: occupancy <= i_empty_thr gives 1); contract.json:309 CHK-004. |
| RTL does | rtl/m_vlsit_sfifo_rd.sv:152 strict compare gives (4 > 4) = 0. |
| Test does | Random traffic with et=4. Monitor line 272 expects (4 <= 4) = 1. |
| A_rtl_wrong | For: The same boundary signature occ == thr appears. The write side uses inclusive '>=' (wr.sv:156).<br>Against: None. |
| B_test_wrong | For: The expected value is computed by the model.<br>Against: The model formula equals the spec. |
| C_spec_unclear | For: There are multiple phrasings.<br>Against: All are inclusive. |
| Options | Fix RTL: rd.sv:152 to an inclusive compare. |

## 8. test_chk_013_random_ratios/ratio=7 (36_8) — CHK-004: o_empty_thr=1 expected (occupancy 2, thr 2) got 0 at 62751.008 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:137 REQ-FUNC-007; spec:548; contract.json:309 CHK-004 "o_empty_thr == (OCC_R(t) <= i_empty_thr)". |
| RTL does | rtl/m_vlsit_sfifo_rd.sv:152 strict compare gives (2 > 2) = 0. |
| Test does | Random traffic with et=2. Monitor line 272 expects (2 <= 2) = 1. |
| A_rtl_wrong | For: The mismatch is at occ == thr. The RTL compare is strict against an inclusive spec.<br>Against: None. |
| B_test_wrong | For: The expected value is computed by the model.<br>Against: The model matches CHK-004. |
| C_spec_unclear | For: There are two wordings.<br>Against: Both are inclusive. |
| Options | Fix RTL: rd.sv:152 to an inclusive compare. |

## 9. test_chk_014_first_word_show_ahead — CHK-004: o_empty_thr=1 expected (occupancy 0, thr 0) got 0 at 62851.009 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:137 REQ-FUNC-007 "less than or equal to i_empty_thr"; contract.json:309 CHK-004. Also the test's own contract, contract.json:571 CHK-014 expected: "o_empty_thr=0 sampled at E2 ... o_empty=1 and o_empty_thr=1 sampled at E3". At E3 the occupancy is 0 with i_empty_thr=0, which requires the inclusive compare. |
| RTL does | rtl/m_vlsit_sfifo_rd.sv:152 strict '>' gives (0 > 0) = 0 at the first read edge after release, so o_empty_thr=0 while idle and empty. |
| Test does | test_sync_fifo.py:742-743 sets equal 10 ns clocks with i_empty_thr=0 and releases both resets. The monitor fails at the first read edge after release (before the directed eq_run checks at lines 752-763), with expectation (0 <= 0) = 1 from line 272. |
| A_rtl_wrong | For: With occ 0 and thr 0, the spec requires 1. The CHK-014 directed expectation at E3 also requires 1. The RTL uses strict '>'.<br>Against: None. |
| B_test_wrong | For: The expected value is computed by the model.<br>Against: The model matches CHK-004, and the directed expectation in contract.json:571 agrees with it. |
| C_spec_unclear | For: None of substance.<br>Against: The spec is inclusive and consistent. |
| Options | Fix RTL: rd.sv:152 to `(w_occ_nxt <= w_empty_thr_ext)`. No test change. |

## 10. test_chk_015_full_empty_overflow_underflow — CHK-004: o_empty_thr=1 expected (occupancy 0, thr 0) got 0 at 62951.01 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:137 REQ-FUNC-007 "o_empty_thr shall be 1 when the occupancy seen by the read side is less than or equal to i_empty_thr"; spec:548; contract.json:309 CHK-004. |
| RTL does | rtl/m_vlsit_sfifo_rd.sv:152 strict compare gives 0 for occ=0, thr=0 at the first read edge after release. |
| Test does | test_sync_fifo.py:772-773 sets 10/10 clocks with i_empty_thr=0. The monitor (line 272) expects 1 at the first idle read edge after release and gets 0. |
| A_rtl_wrong | For: Same root cause: the strict compare at occ == thr == 0.<br>Against: None. |
| B_test_wrong | For: The expected value is computed by the model.<br>Against: The model formula equals the spec. |
| C_spec_unclear | For: None of substance.<br>Against: The spec wording is inclusive throughout. |
| Options | Fix RTL: rd.sv:152 to an inclusive compare. |

## 11. test_chk_016_no_bypass_simultaneous — CHK-004: o_empty_thr=1 expected (occupancy 0, thr 0) got 0 at 63051.011 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:137 REQ-FUNC-007; spec:253 "at or below i_empty_thr"; contract.json:309 CHK-004. |
| RTL does | rtl/m_vlsit_sfifo_rd.sv:152 strict '>' gives o_empty_thr=0 at occupancy 0 with threshold 0. |
| Test does | test_sync_fifo.py:827-828 sets 10/10 clocks with i_empty_thr=0. The monitor (line 272) expects 1 at the first idle read edge after release. |
| A_rtl_wrong | For: Same root cause: the strict compare at occ == thr.<br>Against: None. |
| B_test_wrong | For: The expected value is computed by the model.<br>Against: The model formula equals the spec. |
| C_spec_unclear | For: None of substance.<br>Against: The spec is inclusive. |
| Options | Fix RTL: rd.sv:152 to an inclusive compare. |

## 12. test_chk_017_pointer_wrap/ratio=0 (10_10) — CHK-004: o_empty_thr=1 expected (occupancy 0, thr 0) got 0 at 63151.012 ns

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:137 REQ-FUNC-007; spec:548; contract.json:309 CHK-004. contract.json:634 CHK-017 expects "CHK-010, CHK-004, CHK-006 and CHK-007 hold at every wrap". |
| RTL does | rtl/m_vlsit_sfifo_rd.sv:152 strict '>' gives o_empty_thr=0 at occupancy 0 with threshold 0 (line 218 output). |
| Test does | test_sync_fifo.py:871-872 sets 10/10 clocks with i_empty_thr=0. The monitor (line 272) expects 1 at the first idle read edge after release and gets 0. |
| A_rtl_wrong | For: Same root cause: the strict compare at occ == thr. The write side uses inclusive '>=' (wr.sv:156).<br>Against: None. |
| B_test_wrong | For: The expected value is computed by the model.<br>Against: The model formula equals the spec. |
| C_spec_unclear | For: None of substance.<br>Against: The spec is inclusive. |
| Options | Fix RTL: rd.sv:152 to `reg_empty_thr <= (w_occ_nxt <= w_empty_thr_ext);`, then re-run the full regression (CHK-017 ratio 8_12, CHK-021 and the later failures in sim.log share this signature). |


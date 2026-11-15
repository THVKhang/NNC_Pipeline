# Sign-off packet — async_gray_fifo

This packet is for the person who decides gate **G4 (sign-off)**: *is this design verified well enough against its specification to release?* It collects only the items that need a human judgement. Everything else is in `work/report.md` (all checks and rules) and `work/triage.md`.

## 1. Summary

- **Requirements (rules):** 416 — FAILED 88, NOT_VERIFIED_BY_SIM 142, VERIFIED 186
- **Checks:** 32 — FAIL 9, PASS 23
- **Tests:** {'fail': 8, 'pass': 12}
- **Simulated configurations:** 14 runs in 10 configurations (base, model_off, syn, cell1, cell3, cell4, macro, small, wr_slow, rd_slow); see `run_set.json` and the *Run set* table of the report
- **Code coverage:** line 99.1 %, block 95.7 %, expression 98.0 %, toggle 99.5 %, functional 100.0 %
- **Mutation score:** 100.0 % (12 of 12 injected faults detected)

## 2. Decisions taken for you

These gates were approved by an AI agent on delegation, not by a qualified person. Read each note.

- **G1_rules** (2026-11-10T04:01:18+00:00): Read rules.md: 416 rules kept. The 9 open questions were decided on delegation with the cited spec text (flags as occupancy behavior; INV-002 exempt only during a software-reset sequence per REQ-SRST-004/017; CELL_TYPE 1..4 legal, 0 not verified; SVA-014 bound 8 x (S+2) edges of the slower clock). A person should confirm, especially questions 3 and 9.
- **G2_contract** (2026-11-10T04:18:03+00:00): Read contract.md: 32 checks (13 SVA, 19 tests), interface 18 ports from the two captioned top-level port tables, clock_relation async. Cross-domain checks use windows S..S+2 (REQ-VER-001). CHK-014 (metastability model off) and CHK-017 (VLSIT_SYNTHESIS build) need another run configuration than the one configured (model on, simulation branch); they are kept so the report shows them as not verified in this run rather than dropping them. A person should confirm.
- **G3_verif_sources** (2026-11-14T16:06:38+00:00): Round 5, from the formal counterexample triage (both B_checker_wrong): CHK-012 also allows o_full/o_full_thr to change with i_full_thr (spec:270 AF-6.2-06; the read-side CHK-004 already did); the occupancy-dependent clauses of CHK-013 (wr) and CHK-003 (rd), in the checkers and the tests, are not checked after a one-domain hardware reset until both domains are reset (ASM-005, ERR-003, contract CHK-023). Remaining simulation failures are C (per-bit metastability model) and are left for the spec owner.

## 3. Failures and what they mean

Checks not passing: CHK-003, CHK-013, CHK-014, CHK-016, CHK-017, CHK-018, CHK-020, CHK-024, CHK-029. The triage agent read the specification, the RTL, the tests and the logs, and gives the most likely cause. It changes nothing; you decide.

### test_chk_014_nominal_latency — CHK-013: i_full_thr=depth expected o_full_thr=0 got 1 at 1680691 ps (11 runs)

- **Most likely:** the specification is unclear or contradicts itself
- **Specification:** spec/AsyncGrayFIFO_Design_Specification.md:139 REQ-FUNC-010: "o_full_thr shall be 1 when the write-domain occupancy estimate is greater than or equal to i_full_thr ... The occupancy estimate is the binary write pointer minus the binary read pointer, where the pointer of the other domain is the synchronized one". :137 REQ-FUNC-008: the full flag "shall never be 0 while the FIFO is physically full". rules.json:12922-12923 (AF-3-14/15 decision): the difference is "taken modulo 2 x depth". rules.js…
- **RTL:** rtl/m_vlsit_afifo_wr.sv:106 w_full_n = (reg_wgray == w_rgray_s ^ 4'b1100); :112-117 Gray-to-binary of w_rgray_s; :120 w_occ = reg_wbin - w_rbin_s (4-bit modulo 16); :125 o_full = w_wr_blk | w_full_n; :126 o_full_thr = w_wr_blk ? (i_full_thr==0) : (w_occ >= i_full_thr). With i_full_thr=8, o_full_thr=1 and o_full=0 at the same time needs w_occ in 9..15. That means w_rbin_s is ahead of reg_wbin, which no real read-pointer value can give. w_rgray_s comes from m_vlsit_afifo_sync.sv:46-56: one m_vlsi…
- **Options:** (1) Clarify the spec / fix the model (preferred): rewrite spec 10.6.4 so the metastability model keeps pointer coherence, then change m_vlsit_afifo_cell_sync.sv:149-179 to match. Possible ways: (a) apply the extra delay only to a change that reaches the last stage within one destination cycle of the previous change of the same bus, or (b) model metastability as an old/new choice at the capture edge (at most +1 cycle, and only for the most recent change), so a later change can never overtake an …

### test_chk_016_random_traffic_ratios — CHK-003: i_empty_thr>=depth expected o_empty_thr=1 got 0 at 57093716 ps (10 runs)

- **Most likely:** the specification is unclear or contradicts itself
- **Specification:** spec:139 REQ-FUNC-010: "o_empty_thr shall be 1 when the read-domain occupancy estimate is less than or equal to i_empty_thr ... it is pessimistic ... for the empty side (it can be smaller)". contract.json:287 CHK-003(b): "If i_empty_thr >= PARA_AFIFO_DEPTH, then o_empty_thr=1." spec:138 REQ-FUNC-009: empty "shall never be 0 while the FIFO is physically empty". contract.json:607 CHK-016 expected: "CHK-001..CHK-013 never fail", and the metastability model is on in some runs (:606). The model is p…
- **RTL:** rtl/m_vlsit_afifo_rd.sv:97 w_empty_n = (reg_rgray == w_wgray_s); :104-109 Gray-to-binary; :112 w_occ = w_wbin_s - reg_rbin (mod 16); :118 o_empty_thr = w_rd_blk ? 1 : (w_occ <= i_empty_thr). base.s1 ran with et=13 (log:69). o_empty_thr=0 means w_occ is 14 or 15, i.e. the synchronized write pointer is behind the local read pointer. No past write-pointer value can be behind it, because a read is only accepted when w_wbin_s > rbin. With the per-bit model (cell_sync.sv:158-179) a Gray update can be…
- **Options:** Same decision as for CHK-013 / test_chk_014. (1) Make spec 10.6.4 require a Gray-coherent model, i.e. no reordering of changes across bits: only the latest change near the capture edge may be late, or a bus-level delay. Then change m_vlsit_afifo_cell_sync.sv:149-179. (2) Or state an explicit, enforceable bound that keeps per-bit skew below one source update, and constrain the CHK-016 stimulus to it. (3) No change to the CHK-003 check. Optionally add an internal monitor that checks the decoded w…

### test_chk_017_synthesis_branch_regression — CHK-013: i_full_thr=depth expected o_full_thr=0 got 1 at 68661847 ps (11 runs)

- **Most likely:** the specification is unclear or contradicts itself
- **Specification:** contract.json:614-619 CHK-017: "Compile with VLSIT_SYNTHESIS defined (stand-in cells, no metastability model)... All assertions CHK-001..CHK-013 pass". contract.json:524 CHK-013(c). spec:139 REQ-FUNC-010 and spec:137 REQ-FUNC-008, as for test_chk_014.
- **RTL:** The failing runs are not VLSIT_SYNTHESIS builds. base.s1.log:83-84 shows SYN=False, MSYNC_EN=1 and "NNC_NOT_VERIFIABLE CHK-017 this run is not compiled with VLSIT_SYNTHESIS", so the per-bit metastability model (m_vlsit_afifo_cell_sync.sv:98-183) is active. m_vlsit_afifo_wr.sv:120/126 then give o_full_thr=1 (w_occ ≥ 8) while :106/125 give o_full=0. That needs w_rbin_s > reg_wbin, which only an incoherent synchronized Gray value can produce. SVA: base.s1.log:252 "NNC_FAIL CHK-013 @68662000". In t…
- **Options:** (1) Resolve the per-bit model vs never-optimistic conflict in spec 10.6.4 and m_vlsit_afifo_cell_sync.sv (see test_chk_014). (2) Test-plan clarification, optional and not a weakening: the designer may decide whether test_chk_017 should run on non-SYN builds at all, since contract.json:618 scopes it to VLSIT_SYNTHESIS. CHK-013 itself must stay active in all builds. (3) No RTL change is suggested for the synthesizable branch, which passes.

### test_chk_018_write_n_read_n_show_ahead — CHK-013: i_full_thr=depth expected o_full_thr=0 got 1 at 71078507 ps (11 runs)

- **Most likely:** the specification is unclear or contradicts itself
- **Specification:** contract.json:645-647 CHK-018: "Settings: i_clk_wr 10 ns, i_clk_rd 14 ns ... metastability model off, i_full_thr=8". Expected: "After the edge that accepts D7, o_full=1 and o_full_thr=1", and "CHK-005 and CHK-006 report no error". CHK-013(c) at contract.json:524. REQ-FUNC-010 at spec:139.
- **RTL:** The run had the metastability model on (base.s1.log:98 MSYNC_EN=1), although the contract says model off for CHK-018. With the model on, m_vlsit_afifo_cell_sync.sv:158-179 delays each read-pointer Gray bit independently by 0..2 write cycles. m_vlsit_afifo_wr.sv:120,126 then give w_occ ≥ 8 (o_full_thr=1) while :106,125 give o_full=0. The SVA fires at the same edge (base.s1.log:253 "NNC_FAIL CHK-013 @71079000"). model_off.s1 and syn.s1 pass (results.json, test_chk_018 entry).
- **Options:** (1) Fix the model/spec conflict as for test_chk_014. (2) Separately, the designer may align the run set with contract.json:646 by running CHK-018 with +AFIFO_MSYNC_EN=0 or in syn builds. This is a stimulus-setting fix, not a check relaxation: CHK-013 stays on, and the model-on case is still covered by CHK-016/029. (3) No change to the CHK-013 check.

### test_chk_020_overflow — CHK-013: i_full_thr=depth expected o_full_thr=0 got 1 at 99049215 ps (rd_slow.s1 only)

- **Most likely:** the specification is unclear or contradicts itself
- **Specification:** contract.json:685-687 CHK-020: "metastability model off, i_full_thr=8 ... After Tr: o_full=1 and o_full_thr=1 at write edges 1 and 2 after Tr, and o_full=0 and o_full_thr=0 from write edge 3 on (latency S=2, pessimistic)". CHK-013(c) at contract.json:524. REQ-FUNC-010 at spec:139.
- **RTL:** rd_slow.s1 runs with MSYNC_EN=1 (rd_slow.s1.log:37,109). In the read-the-remaining-7-words phase of scen_020, read Gray updates come on consecutive 14 ns read edges. The per-bit model (m_vlsit_afifo_cell_sync.sv:158-179) can deliver a later read-pointer bit change to the write domain before an earlier one. m_vlsit_afifo_wr.sv:120 then computes w_occ = wbin - (ahead rbin_s) ≥ 9, so o_full_thr=1 (:126) while o_full=0 (:106,125). It fails only with seed/config rd_slow.s1. All other model-on runs, …
- **Options:** (1) Same spec/model decision as test_chk_014: make the model Gray-coherent, update spec 10.6.4 and m_vlsit_afifo_cell_sync.sv:149-179, and keep REQ-FUNC-008/010. (2) Optionally run CHK-020 with the model off, as contract.json:686 states. That is a stimulus setting, not a check change. (3) Keep CHK-013 unchanged.

### test_chk_024_hw_reset_mid_traffic — CHK-013: i_full_thr=depth expected o_full_thr=0 got 1 at 80584778 ps (12 runs)

- **Most likely:** the specification is unclear or contradicts itself
- **Specification:** contract.json:769-771 CHK-024: "Random traffic until the FIFO holds 5 words ... Assert i_rst_n_wr and i_rst_n_rd together ... release i_rst_n_wr and then i_rst_n_rd. Run random traffic again for 200 words." Expected: "Only post-reset words are read, in order and exactly once". CHK-013(c) at contract.json:524. REQ-FUNC-010 at spec:139.
- **RTL:** Both resets are asserted together, so both synchronizers and both pointers reset to 0 (m_vlsit_afifo_wr.sv:141-154, rd.sv:133-146, sync reset value 0 at wr.sv:235 and rd.sv:208). That leaves no one-domain reset skew, so a reset cannot explain w_occ ≥ 9. During the 200-word random-traffic phase after the reset, with MSYNC_EN=1 (base.s1.log:138), the per-bit model (cell_sync.sv:158-179) can reorder read-pointer Gray bits. wr.sv:120,126 then give o_full_thr=1 with o_full=0 (:106,125). The SVA fire…
- **Options:** (1) Fix the model/spec conflict as for test_chk_014. (2) If the designer wants to rule out a reset interaction, add a debug monitor of w_rgray_s against the recent values of reg_rgray after the release. No check change is needed. (3) No change to CHK-013.

### test_chk_029_srst_random_traffic — CHK-032: occupancy 5 <= i_empty_thr 5 expected o_empty_thr=1 (never optimistic) got 0 at 106739668 ps (6 runs)

- **Most likely:** the specification is unclear or contradicts itself
- **Specification:** contract.json:982 CHK-032: "The flag is never on the optimistic side of the true occupancy." spec:139 REQ-FUNC-010: the estimate "is pessimistic ... for the empty side (it can be smaller)". contract.json:933-935 CHK-029: model on in at least 5 runs, "CHK-001..CHK-013 never fail". spec:172 REQ-SRST-013: the sequence must complete "with the metastability model enabled (random extra latency on every crossing)". spec:979 CC-10: "the multi-bit pointers are protected by the flush check (DEC-034)".
- **RTL:** base.s1: clocks 10/37, ft=9, et=5, MSYNC_EN=1 (base.s1.log:172). The TB's true occupancy (Q+P) is 5 ≤ 5, but m_vlsit_afifo_rd.sv:118 gives o_empty_thr=0. So w_rd_blk=0 and w_occ = w_wbin_s - reg_rbin > 5 (rd.sv:112): the synchronized write pointer is ahead of the true write pointer, which is optimistic. With a 10 ns write clock against a 37 ns read clock, several write Gray updates fall within one read cycle. With the per-bit model (cell_sync.sv:158-179), a later bit change can arrive before an…
- **Options:** (1) Spec/model fix as for test_chk_014: a Gray-coherent metastability model, with spec 10.6.4 updated. This also protects the flush checks of REQ-SRST-010 (wr.sv:185, rd.sv:169), which compare a synchronized Gray pointer with 0 and rely on the same coherence (CC-10). (2) To rule out the TB bookkeeping candidate, the designer can log len(P), p_cnt and the read-block state at the failing edge. If P was cleared while the read side was not yet blocked, make the P-clear point follow the contract wit…

### test_regression_random — CHK-032: occupancy 5 >= i_full_thr 5 expected o_full_thr=1 (never optimistic) got 0 at 131612134 ps (11 runs)

- **Most likely:** the specification is unclear or contradicts itself
- **Specification:** spec:139 REQ-FUNC-010: the estimate "is pessimistic for the full side (it can be larger than the true occupancy)". spec:137 REQ-FUNC-008: full "shall never be 0 while the FIFO is physically full". contract.json:982 CHK-032: "The flag is never on the optimistic side of the true occupancy." rules.json:13573: it differs "only by pointer updates still inside the synchronizer".
- **RTL:** base.s1: default clocks 10/13.7, ft=5, et=8, MSYNC_EN=1 (base.s1.log:202). The failure is at 131612 ns, about 8.5 µs into the test, in the first random_traffic phase (:1725) before any software reset. The TB shows 5 unread words with i_rst_n_sw=1 and busy=0, but m_vlsit_afifo_wr.sv:126 gives o_full_thr=0. So w_occ = reg_wbin - w_rbin_s < 5 (:120): the synchronized read pointer is ahead of the true read pointer, which is optimistic. With the per-bit model (cell_sync.sv:158-179), back-to-back rea…
- **Options:** (1) Spec/model fix as for test_chk_014 (Gray-coherent metastability model; update spec 10.6.4 and m_vlsit_afifo_cell_sync.sv:149-179). (2) Optionally have the TB log the decoded synchronized pointers at a CHK-032 failure for direct proof. (3) Keep the CHK-032 checks as they are.

### assertion CHK-003 — o_empty_thr consistency for every 4-bit i_empty_thr (fails=18, hits=201444, first fail 57094000)

- **Most likely:** the specification is unclear or contradicts itself
- **Specification:** contract.json:287 CHK-003: "(a) if o_empty=1, then o_empty_thr=1 ... (b) If i_empty_thr >= PARA_AFIFO_DEPTH, then o_empty_thr=1. (c) If i_empty_thr==0, then o_empty_thr == o_empty." spec:139 REQ-FUNC-010: o_empty_thr is 1 when the read-domain estimate (synchronized write pointer minus read pointer) ≤ i_empty_thr, and the estimate can only be smaller than the true occupancy. spec:653 (AF-10.6.4-01): the metastability model has independent per-bit extra delay.
- **RTL:** rtl/m_vlsit_afifo_rd.sv:112 w_occ = w_wbin_s - reg_rbin; :118 o_empty_thr = w_rd_blk ? 1 : (w_occ <= i_empty_thr). Clause (b) fails when w_occ > i_empty_thr ≥ 8, so w_occ is 9..15. That is impossible for a valid synchronized write pointer, because a read is accepted only when wbin_s > rbin and Gray values decode to pointers that were actually held. w_wgray_s comes from per-bit cells (m_vlsit_afifo_sync.sv:46-56, m_vlsit_afifo_cell_sync.sv:149-182) with independent random 0..2-cycle delays and r…
- **Options:** (1) Decide in spec 10.6.4 that the metastability model must keep multi-bit Gray coherence, so a later change never overtakes an earlier one, and fix m_vlsit_afifo_cell_sync.sv to match. (2) Or, if per-bit independence must stay, add a spec-level bound on the extra delay relative to the source update rate and constrain the model-on stimulus to it. (3) Keep a_CHK_003 unchanged.

### assertion CHK-013 — o_full_thr consistency for every 4-bit i_full_thr (fails=54, hits=223849, first fail 1681000)

- **Most likely:** the specification is unclear or contradicts itself
- **Specification:** contract.json:524 CHK-013: "(a) if i_full_thr==0, then o_full_thr=1; (b) if i_full_thr > PARA_AFIFO_DEPTH (9..15), then o_full_thr=0; (c) if i_full_thr==PARA_AFIFO_DEPTH, then o_full_thr == (o_full AND i_rst_n_sw AND NOT o_sw_rst_busy); (d) if o_full=1, i_rst_n_sw=1 and o_sw_rst_busy=0, then o_full_thr == (i_full_thr <= PARA_AFIFO_DEPTH)." spec:139 REQ-FUNC-010 (estimate = write pointer minus synchronized read pointer, modulo 2×depth per rules.json:12923, and a value above depth means the flag …
- **RTL:** rtl/m_vlsit_afifo_wr.sv:106 w_full_n (Gray compare with MSBs inverted); :120 w_occ = reg_wbin - w_rbin_s; :125 o_full; :126 o_full_thr = w_wr_blk ? (thr==0) : (w_occ >= thr). Every logged failure is clause (c) with thr=8: o_full_thr=1 while o_full=0, which needs w_occ in 9..15, i.e. a synchronized read pointer ahead of the write pointer. The per-bit model (m_vlsit_afifo_cell_sync.sv:158-179) can produce that by reordering Gray bit changes. Example: the read pointer goes 6→7→8, Gray 0101→0100→11…
- **Options:** (1) Clarify spec 10.6.4 so the metastability model keeps Gray-pointer coherence: only the change nearest the capture edge may be late, or the delay is applied per bus. Then fix m_vlsit_afifo_cell_sync.sv:149-179. Also check the flush checks (wr.sv:185, rd.sv:169) under the new model. (2) Or keep per-bit independence and add an explicit, constrained bound (extra delay below the source pointer update interval) to the spec and to the model-on stimulus of CHK-015/016/029. (3) Keep a_CHK_013 unchang…

## 4. Hand edits of generated verification code

Generated tests or checkers were edited by hand after triage found them wrong. An edit must correct the test, never weaken it to hide a design fault.

- **EN:** Apart from `filelist.f`, the files are unchanged copies. The IP has two **asynchronous** clocks (`i_clk_wr`, `i_clk_rd`) and two hardware resets. NNC runs it with `clock_relation=async`: each clock starts after its own seeded random delay, the periods need not be in an integer ratio, and cross-domain behavior is checked as order plus a bounded window. Without `VLSIT_SYNTHESIS` the synchronizer wrapper contains the upstream metastability model (random extra latency of 0 to 2 destination cycles, plusargs `+AFIFO_MSYNC_SEED`, `+AFIFO_MSYNC_EN`). Everything under `work/`, `verif/` and `sim/` was generated by NNC Pipeline (the tests and checkers were regenerated on 2026-11-13 with the run set in the prompts; the hand fixes of 2026-11-11 no longer apply), except these hand fixes made after triage (B: test or checker wrong; the simulation triage and, for 11-13, the formal counterexample triage), each marked `NNC hand fix (G3, triage B)` in the file and recorded at a G3 re-approval of 2026-11-13/14:
- **VI:** Ngoài `filelist.f`, các file là bản sao nguyên vẹn. IP có hai clock **bất đồng bộ** (`i_clk_wr`, `i_clk_rd`) và hai reset phần cứng. NNC chạy với `clock_relation=async`: mỗi clock khởi động sau một khoảng trễ ngẫu nhiên riêng (theo seed), chu kỳ không cần là bội số nguyên của nhau, hành vi qua hai miền được kiểm bằng thứ tự và cửa sổ thời gian có giới hạn. Khi không định nghĩa `VLSIT_SYNTHESIS`, wrapper đồng bộ dùng mô hình metastability của upstream (trễ thêm ngẫu nhiên 0–2 chu kỳ đích). Mọi thứ trong `work/`, `verif/`, `sim/` do NNC Pipeline sinh ra (test và checker được sinh lại ngày 2026-11-13 với run set trong prompt; các chỗ sửa tay ngày 2026-11-11 không còn), trừ 13 chỗ sửa tay sau triage (B: test hoặc checker sai; 3 chỗ do formal tìm ra) ở bảng trên, mỗi chỗ có chú thích `NNC hand fix (G3, triage B)` trong file và được ghi ở lần duyệt lại G3. Không chỗ nào bỏ một check mà contract yêu cầu.

## 5. What this verification does not cover

**142 requirement(s) cannot be checked by simulation** (static, structural, timing, process...). They need another method: lint, CDC, STA, synthesis, review. First ones:

- AF-1.1-07 (): The synchronizer module instantiates one technology cell wrapper per bit, supporting five cell options (bypass, two D-FF cells, 2-FF, 3-FF, 4-FF), configurable… — *static_or_structural*
- AF-1.1-09 (): The FIFO array module provides a pure RTL implementation and a library SRAM (one write port, one read port) replacement branch. — *static_or_structural*
- AF-1.3-02 (REQ-PARAM-001): The FIFO has a configurable number of entries and data width. — *static_or_structural*
- AF-1.3-08 (REQ-FUNC-016): The FIFO array may use the library SRAM branch when PARA_AFIFO_MEM_USE_MACRO is 1. — *not_applicable_to_dut*
- AF-2.1-01 (): RTL deliverables must follow VLSIT RTL Design Rules v2 (REF-003) as the mandatory RTL coding, hierarchy, reset, CDC and naming baseline. — *static_or_structural*
- AF-3-03 (REQ-FUNC-002): Each Gray pointer register shall change at most one bit per clock cycle of its own domain. — *not_observable_at_interface*
- AF-3-07 (REQ-FUNC-006): Each domain shall hold a binary pointer of LPARA_PTR_W = log2(depth)+1 bits and a Gray pointer register derived from the next binary pointer. — *static_or_structural*
- AF-3-09 (REQ-FUNC-007): The depth shall be a power of 2 with a minimum of 2; there is no upper limit. — *static_or_structural*
- AF-3-17 (REQ-FUNC-010): The thresholds are static and shall not change while the FIFO is in use. — *not_applicable_to_dut*
- AF-3-18 (REQ-FUNC-011): m_vlsit_afifo_top shall be a structural wrapper instantiating only m_vlsit_afifo_wr, m_vlsit_afifo_rd and m_vlsit_afifo_mem. — *static_or_structural*
- AF-3-19 (REQ-FUNC-012): m_vlsit_afifo_wr shall contain write pointer, full/threshold, overflow logic, read Gray pointer synchronizer, write-side software reset FSM, acknowledge synchr… — *static_or_structural*
- AF-3-21 (REQ-FUNC-014): m_vlsit_afifo_sync shall contain no flip-flop or cell of its own and shall instantiate only m_vlsit_afifo_cell_sync, one per bit, in every configuration and bo… — *static_or_structural*
- AF-3-23 (REQ-FUNC-014): Option 0 (bypass) shall not be used for a Gray pointer crossing. — *static_or_structural*
- AF-3-24 (REQ-FUNC-015): m_vlsit_afifo_mem shall be an independent module instantiated in m_vlsit_afifo_top, modelled as an SRAM with one write port (write domain) and one read port (r… — *static_or_structural*
- AF-3-25 (REQ-FUNC-016): m_vlsit_afifo_mem shall provide a generate branch replacing the RTL array with a library 1W1R SRAM through m_vlsit_afifo_ram_macro; the default is the RTL arra… — *static_or_structural*
- … 127 more in work/rtm.json

Outside this flow in every case: formal proof, CDC/RDC analysis, static timing, synthesis, DFT.

## 6. Weak spots of the verification itself

Mutation testing changed one RTL line at a time (12 faults; each in the run that executes its line, a survivor again in every other configuration). A fault no check notices is a gap, unless it changes nothing visible (an *equivalent* mutant, claimed below by an agent).


Code or cover points never reached (first ones):

- line m_vlsit_afifo_rd.sv:172
- line m_vlsit_afifo_wr.sv:188
- line VLSIT_CELL_SRAM_1W1R.sv:41
- line VLSIT_CELL_SRAM_1W1R.sv:45
- line m_vlsit_afifo_cell_sync.sv:106
- line m_vlsit_afifo_mem.sv:68
- line m_vlsit_afifo_ram_macro.sv:35

### Formal check (SymbiYosys)

Every input sequence of up to 20 cycles was searched (multiclock (free clocks)); result {'BOUNDED': 2, 'PROVEN': 5, 'UNSUPPORTED': 6}. PROVEN holds for every cycle; BOUNDED found no counterexample within the depth. Details: `work/formal.md`.


Environment assumptions (the formal results hold only for inputs that respect them; an assumption the specification does not require would hide bugs):

- ENV-01: i_full_thr is a static configuration input with a false path and no synchronizer. It is written once before use and does not change after the FIFO has first entered use (both resets released), whatever reset activity follows. (AF-3-17, AF-6.2-10, AF-7…
- ENV-02: i_empty_thr is a static configuration input with a false path and no synchronizer. It is written once before use and does not change after the FIFO has first entered use (both resets released), whatever reset activity follows. (AF-3-17, AF-6.2-10, AF-…
- ENV-03: No write starts until both domains are out of hardware reset. The producer keeps the write interface idle while either reset is asserted. (AF-20.1-05, AF-10.7.4-23, AF-12-07)
- ENV-04: No read starts until both domains are out of hardware reset. The consumer keeps the read interface idle while either reset is asserted. (AF-20.1-05, AF-10.7.4-23, AF-12-07)
- ENV-05: i_rst_n_wr is already synchronized to i_clk_wr. It is released (0->1) only at a rising edge of i_clk_wr, so the releasing edge still samples it low: low for at least one write-clock edge. Assertion stays asynchronous and unconstrained. (AF-6.2-03, AF-…
- ENV-06: i_rst_n_rd is already synchronized to i_clk_rd. It is released (0->1) only at a rising edge of i_clk_rd, so the releasing edge still samples it low: low for at least one read-clock edge. Assertion stays asynchronous and unconstrained. (AF-6.2-03, AF-3…
- ENV-07: The integrator resets both domains (the whole FIFO, with the two reset windows overlapping). After a hardware reset of only one domain, the producer issues no write until both domains have been reset together and both are out of reset. The assertion a…
- ENV-08: The integrator resets both domains (the whole FIFO, with the two reset windows overlapping). After a hardware reset of only one domain, the consumer issues no read until both domains have been reset together and both are out of reset. The assertion an…

## 7. Reproduce without NNC

`designs/async_gray_fifo/sim/` holds a Makefile that runs the same regression with Verilator and cocotb only (Linux or WSL):

```bash
cd designs/async_gray_fifo/sim
make regression SEED=1 2>&1 | tee sim.log
cd ../../.. && python -m nnc kit-check async_gray_fifo    # same outcome as the recorded results?
```

The kit reproduces the primary run base.s1; the other runs differ only by the settings in `run_set.json`.

## 8. Checklist before signing

Answer every item. Sign only if each one is true, or record why not in the approval note:

- [ ] I have read the delegated decisions of G1_rules and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G2_contract and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G3_verif_sources and agree with them (or I have corrected them).
- [ ] The specification question behind “test_chk_014_nominal_latency — CHK-013: i_full_thr=depth expected o_full_thr=0 got 1 at 1…” is decided by the specification owner, and the spec, contract or checker is updated.
- [ ] The specification question behind “test_chk_016_random_traffic_ratios — CHK-003: i_empty_thr>=depth expected o_empty_thr=1 g…” is decided by the specification owner, and the spec, contract or checker is updated.
- [ ] The specification question behind “test_chk_017_synthesis_branch_regression — CHK-013: i_full_thr=depth expected o_full_thr=…” is decided by the specification owner, and the spec, contract or checker is updated.
- [ ] The specification question behind “test_chk_018_write_n_read_n_show_ahead — CHK-013: i_full_thr=depth expected o_full_thr=0 …” is decided by the specification owner, and the spec, contract or checker is updated.
- [ ] The specification question behind “test_chk_020_overflow — CHK-013: i_full_thr=depth expected o_full_thr=0 got 1 at 99049215…” is decided by the specification owner, and the spec, contract or checker is updated.
- [ ] The specification question behind “test_chk_024_hw_reset_mid_traffic — CHK-013: i_full_thr=depth expected o_full_thr=0 got 1…” is decided by the specification owner, and the spec, contract or checker is updated.
- [ ] The specification question behind “test_chk_029_srst_random_traffic — CHK-032: occupancy 5 <= i_empty_thr 5 expected o_empty…” is decided by the specification owner, and the spec, contract or checker is updated.
- [ ] The specification question behind “test_regression_random — CHK-032: occupancy 5 >= i_full_thr 5 expected o_full_thr=1 (neve…” is decided by the specification owner, and the spec, contract or checker is updated.
- [ ] The specification question behind “assertion CHK-003 — o_empty_thr consistency for every 4-bit i_empty_thr (fails=18, hits=2…” is decided by the specification owner, and the spec, contract or checker is updated.
- [ ] The specification question behind “assertion CHK-013 — o_full_thr consistency for every 4-bit i_full_thr (fails=54, hits=223…” is decided by the specification owner, and the spec, contract or checker is updated.
- [ ] Each hand edit of the generated tests and checkers corrects the test and weakens no requirement.
- [ ] The requirements that simulation cannot check are assigned to another verification method.
- [ ] The unreached code and cover points are unreachable by design or accepted.
- [ ] Each formal environment assumption (verif/formal/nnc_env.sv) is an obligation the specification really places on the environment.
- [ ] I reproduced the regression (or CI did) and the outcome matches the report.

Then: `nnc gate approve async_gray_fifo G4_signoff --by "<your name>" --note "<waivers, open items>"`. The approval is bound to the current results.json: a later run makes it STALE.

# Sign-off packet — async_gray_fifo

This packet is for the person who decides gate **G4 (sign-off)**: *is this design verified well enough against its specification to release?* It collects only the items that need a human judgement. Everything else is in `work/report.md` (all checks and rules) and `work/triage.md`.

## 1. Summary

- **Requirements (rules):** 416 — FAILED 77, NOT_PROVEN 20, NOT_VERIFIED_BY_SIM 142, PARTIAL 8, VERIFIED 169
- **Checks:** 32 — FAIL 3, NOT_VERIFIABLE 3, PASS 26
- **Tests:** {'fail': 1, 'pass': 33}
- **Simulated configurations:** 14 runs in 10 configurations (base, model_off, syn, cell1, cell3, cell4, macro, small, wr_slow, rd_slow); see `run_set.json` and the *Run set* table of the report
- **Code coverage:** line 99.1 %, block 95.7 %, expression 98.0 %, toggle 99.5 %, functional 100.0 %
- **Mutation score:** 91.7 % (33 of 36 injected faults detected)

## 2. Decisions taken for you

These gates were approved by an AI agent on delegation, not by a qualified person. Read each note.

- **G1_rules** (2026-11-10T04:01:18+00:00): Read rules.md: 416 rules kept. The 9 open questions were decided on delegation with the cited spec text (flags as occupancy behavior; INV-002 exempt only during a software-reset sequence per REQ-SRST-004/017; CELL_TYPE 1..4 legal, 0 not verified; SVA-014 bound 8 x (S+2) edges of the slower clock). A person should confirm, especially questions 3 and 9.
- **G2_contract** (2026-11-10T04:18:03+00:00): Read contract.md: 32 checks (13 SVA, 19 tests), interface 18 ports from the two captioned top-level port tables, clock_relation async. Cross-domain checks use windows S..S+2 (REQ-VER-001). CHK-014 (metastability model off) and CHK-017 (VLSIT_SYNTHESIS build) need another run configuration than the one configured (model on, simulation branch); they are kept so the report shows them as not verified in this run rather than dropping them. A person should confirm.
- **G3_verif_sources** (2026-11-12T07:22:40+00:00): verif/formal/nnc_env.sv, second formal-triage round (4 counterexamples, all E): thresholds written once before use and never changed afterwards (AF-6.2-10, AF-7.2-04, AF-17.1.3-04: 'written once before use'); after a hardware reset of one domain, no traffic until the two reset windows have overlapped and both are released. The second is an INTERPRETATION of ASM-005 ('one domain reset alone ... inconsistent') with Scenario 4 (overlapping resets released at different times); a non-overlapping sequence of the two resets is treated as 'reset alone'. A qualified person should confirm this reading. Reset release synchronous to its own clock as before.

## 3. Failures and what they mean

Checks not passing: CHK-003, CHK-013, CHK-025. The triage agent read the specification, the RTL, the tests and the logs, and gives the most likely cause. It changes nothing; you decide.

### test_chk_025_srst_partial_fifo — CHK-025 (8): 'o_empty fall after P0: expected the change after destination edge 3..5 got 6' (cell3.s1, S=3). wr_slow.s1 fails …

- **Most likely:** the test or checker is likely wrong
- **Specification:** contract.json:849 (CHK-025 stimulus): "Drive i_wr_en=1 with new distinct data at every write edge from W0 until 10 write cycles after o_sw_rst_busy falls." contract.json:850 (expected 8): "The first post-reset word P0 is accepted at m+1. o_rd_data=P0 from the second read edge after it, while o_empty is still 1; o_empty falls only from read edge 3." This is the model-off number. Spec 10.3 (spec:517, rules.json AF-10.3-02 line 4992): "With the metastability model (REQ-VER-001) the flag changes af…
- **RTL:** The write side increments the pointer on every accepted write (m_vlsit_afifo_wr.sv:129-138; Gray at :138). The reads after P0 give: P0 at m+1 makes wbin 0->1 (Gray 0000->0001, bit0 rises). P1 at m+2 makes Gray 0011 (bit1 rises). P2 at m+3 makes Gray 0010 (bit0 falls). So at the source, bit0 is 1 for only 2 write cycles (20 ns), which is shorter than 2 read periods (28 ns). In the per-bit model (m_vlsit_afifo_cell_sync.sv:149-182), the bit0 rise is detected at the last-stage input (:158). If ext…
- **Options:** (1) Fix the test: for (8), either make P0 isolated in the model-on runs (write P0 alone, then wait at least LMAX+1 read edges before P1), or measure o_empty's fall against the latest bound over the words written back-to-back. That is: o_empty must be 1 through edge S-1 (never early) and must fall by S+2 after P1's write edge, i.e. by S+3 relative to P0, with the bound derived from the spec. Keep the exact S check in model-off runs. This is a correct derivation for non-isolated stimulus, not a l…

### CHK-003 assertion: 534 fails / 1,523,017 hits. First fail 239,353,000 ps (base.s1), during test_chk_016_random_ratios/pair=2 (10 ns write / 23 ns read; base.s1…

- **Most likely:** the specification is unclear or contradicts itself
- **Specification:** contract.json:287: "At every rising edge of i_clk_rd, and while i_rst_n_rd=0: (a) if o_empty=1, then o_empty_thr=1... (b) If i_empty_thr >= PARA_AFIFO_DEPTH, then o_empty_thr=1. (c) If i_empty_thr==0, then o_empty_thr == o_empty." Note the wording 'while i_rst_n_rd=0' is ambiguous: it probably means 'and also while'. REQ-FUNC-010 (spec:139): "o_empty_thr shall be 1 when the read-domain occupancy estimate is less than or equal to i_empty_thr... the empty side (it can be smaller)". rules.json:135…
- **RTL:** m_vlsit_afifo_rd.sv:104-112: w_wbin_s = gray2bin(w_wgray_s); w_occ = w_wbin_s - reg_rbin (4-bit modulo). :117-118: o_empty = w_rd_blk | (reg_rgray==w_wgray_s); o_empty_thr = w_rd_blk ? 1 : (w_occ <= i_empty_thr). By construction (a) and (c) cannot fail. o_empty=1 means blocked or equal pointers (w_occ=0), so o_empty_thr=1. For thr=0, w_occ<=0 holds exactly when the Gray values are equal, i.e. when o_empty=1. So the failing clause must be (b): i_empty_thr in 8..15 while w_occ in 9..15 and not bl…
- **Options:** First confirm the failing clause: add per-clause $display of i_empty_thr, o_empty, o_empty_thr and the internal w_wgray_s/reg_rbin at NNC_FAIL. The expected result is clause (b) with an incoherent w_wgray_s. Then the designer decides: (1) Clarify the spec, deciding whether the metastability model may show a pointer value outside the source sequence. If not (the intent of spec:684), (2) fix the RTL model in m_vlsit_afifo_cell_sync.sv / m_vlsit_afifo_sync.sv. Options: one delay decision per synch…

### CHK-013 assertion: 721 fails / 1,681,616 hits. First fail 9,712,000 ps (base.s1), during test_chk_014_nominal_latency/per=1 (14 ns write / 6 ns read; base.s1.l…

- **Most likely:** the specification is unclear or contradicts itself
- **Specification:** contract.json:524: "(a) if i_full_thr==0, then o_full_thr=1; (b) if i_full_thr > PARA_AFIFO_DEPTH (9..15), then o_full_thr=0; (c) if i_full_thr==PARA_AFIFO_DEPTH, then o_full_thr == (o_full AND i_rst_n_sw AND NOT o_sw_rst_busy); (d) if o_full=1, i_rst_n_sw=1 and o_sw_rst_busy=0, then o_full_thr == (i_full_thr <= PARA_AFIFO_DEPTH)." REQ-FUNC-010 (spec:139): "o_full_thr shall be 1 when the write-domain occupancy estimate is greater than or equal to i_full_thr... a value above the depth makes it n…
- **RTL:** m_vlsit_afifo_wr.sv:106: w_full_n = (reg_wgray == w_rgray_s ^ 1100). :120: w_occ = reg_wbin - gray2bin(w_rgray_s). :125-126: o_full = w_wr_blk | w_full_n; o_full_thr = w_wr_blk ? (i_full_thr==0) : (w_occ >= i_full_thr). By construction (a) and (d) hold, because a non-blocked o_full means w_occ==8. So (b)/(c) can fail only when w_occ is 9..15. Then o_full_thr=1 and o_full=0, which fails (c) with thr=8 and (b) with thr 9..w_occ. Hypothesis for the first fail: with i_full_thr=8, fill_tr drains 7 w…
- **Options:** First, log at each CHK-013 fail: i_full_thr, o_full, o_full_thr, and the internal reg_wbin and w_rgray_s (u_wr). That confirms w_occ>8 from an incoherent w_rgray_s, and which clause fails. Then the same decision as CHK-003 applies, and one fix should cover both. (1) Clarify the spec on whether the metastability model may show a synchronized pointer value outside the source sequence, given REQ-FUNC-008 'never optimistic' and REQ-FUNC-010 'above the depth never 1'. (2) If not allowed, fix the RTL…

## 4. Hand edits of generated verification code

Generated tests or checkers were edited by hand after triage found them wrong. An edit must correct the test, never weaken it to hide a design fault.

- **EN:** Apart from `filelist.f`, the files are unchanged copies. The IP has two **asynchronous** clocks (`i_clk_wr`, `i_clk_rd`) and two hardware resets. NNC runs it with `clock_relation=async`: each clock starts after its own seeded random delay, the periods need not be in an integer ratio, and cross-domain behavior is checked as order plus a bounded window. Without `VLSIT_SYNTHESIS` the synchronizer wrapper contains the upstream metastability model (random extra latency of 0 to 2 destination cycles, plusargs `+AFIFO_MSYNC_SEED`, `+AFIFO_MSYNC_EN`). Everything under `work/`, `verif/` and `sim/` was generated by NNC Pipeline, except four test-bench fixes made by hand after triage (B: test wrong), recorded at the G3 re-approval of 2026-11-11: `TB.rec`, the scoreboard start, the threshold setting in `TB.init` (`verif/tests/test_async_gray_fifo.py`) and the CHK-012 exemption in `verif/sva/nnc_chk_wr.sv`. Four more hand fixes followed the triage (B) of the run set, at the G3 re-approval of the same day: the pre-reset words of the scoreboard checker `verif/sva/nnc_chk_sb.sv` are discarded at read edge S+3 with S taken from `PARA_AFIFO_CELL_TYPE` (it was the literal 5, right for S=2 only); `fill_tr` and the CHK-021 scenario wait LMAX+3 write edges so that earlier reads have crossed before writing (`o_full` may stay 1 late, REQ-FUNC-008); the CHK-024 fill target is min(5, DEPTH-1); CHK-025 is declared not verifiable when the depth is smaller than the crossing window. None of them changes a check in the default configuration.
- **VI:** Ngoài `filelist.f`, các file là bản sao nguyên vẹn. IP có hai clock **bất đồng bộ** (`i_clk_wr`, `i_clk_rd`) và hai reset phần cứng. NNC chạy với `clock_relation=async`: mỗi clock khởi động sau một khoảng trễ ngẫu nhiên riêng (theo seed), chu kỳ không cần là bội số nguyên của nhau, hành vi qua hai miền được kiểm bằng thứ tự và cửa sổ thời gian có giới hạn. Khi không định nghĩa `VLSIT_SYNTHESIS`, wrapper đồng bộ dùng mô hình metastability của upstream (trễ thêm ngẫu nhiên 0–2 chu kỳ đích). Mọi thứ trong `work/`, `verif/`, `sim/` do NNC Pipeline sinh ra, trừ bốn chỗ sửa testbench bằng tay sau triage (B: test sai), ghi ở lần duyệt lại G3 ngày 2026-11-11: `TB.rec`, thời điểm bật scoreboard, việc đặt ngưỡng trong `TB.init` và miễn trừ của CHK-012 trong `nnc_chk_wr.sv`. Bốn chỗ sửa tay nữa sau triage (B) của run set, cũng ghi ở lần duyệt lại G3 cùng ngày: checker scoreboard bỏ các từ trước reset ở cạnh đọc S+3 với S lấy theo `PARA_AFIFO_CELL_TYPE` (trước là số 5 cố định, chỉ đúng khi S=2); `fill_tr` và kịch bản CHK-021 chờ LMAX+3 cạnh ghi để lần đọc trước đi qua miền clock rồi mới ghi; mục tiêu đổ đầy của CHK-024 là min(5, DEPTH-1); CHK-025 khai NOT_VERIFIABLE khi độ sâu nhỏ hơn cửa sổ đồng bộ. Không chỗ nào thay đổi check ở cấu hình mặc định.

## 5. What this verification does not cover

**3 check(s) could not be verified by any simulated configuration:**

- CHK-015: not verifiable in any of the 14 runs: seeing L=2,3,4 in both directions over the 5-seed run set needs the other seeds; this run covers seed 1 only | seeing L=2,3,4 in both directions over the 5-seed run set needs the other seeds; this run covers seed 2 only | seeing L=2,3,4 in both directions over the 5-seed run set needs the other seeds; this run covers seed 3 only | seeing L=2,3,4 in both direc…
- CHK-016: not verifiable in any of the 14 runs: the model-off run of the run set is another configuration; this run has the model on | the model-on runs with logged seeds are other configurations; this run has the model off
- CHK-029: not verifiable in any of the 14 runs: the other model settings / seeds of the run set are other runs (this run: model on, seed 1) | the other model settings / seeds of the run set are other runs (this run: model on, seed 2) | the other model settings / seeds of the run set are other runs (this run: model on, seed 3) | the other model settings / seeds of the run set are other runs (this run: model…

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

**28 requirement(s) only partly or not proven:** AF-1.1-01 (PARTIAL), AF-1.2-01 (NOT_PROVEN), AF-3-01 (NOT_PROVEN), AF-3-02 (NOT_PROVEN), AF-3-30 (NOT_PROVEN), AF-5.4-02 (NOT_PROVEN), AF-6.2-27 (NOT_PROVEN), AF-6.3-05 (NOT_PROVEN), AF-7.2-03 (PARTIAL), AF-10.1-02 (PARTIAL), AF-10.3-02 (NOT_PROVEN), AF-10.4-03 (PARTIAL), AF-10.5-01 (PARTIAL), AF-10.6.4-01 (NOT_PROVEN), AF-10.6.4-02 (NOT_PROVEN), AF-10.7.5-10 (NOT_PROVEN), AF-13-01 (PARTIAL), AF-14.4-07 (PARTIAL), AF-14.4-09 (NOT_PROVEN), AF-15.2-06 (NOT_PROVEN), AF-15.2-08 (NOT_PROVEN), AF-15.2-13 (NOT_PROVEN), AF-15.2-21 (NOT_PROVEN), AF-15.2-22 (NOT_PROVEN), AF-15.3-02 (NOT_PROVEN)

Outside this flow in every case: formal proof, CDC/RDC analysis, static timing, synthesis, DFT.

## 6. Weak spots of the verification itself

Mutation testing changed one RTL line at a time (36 faults; each in the run that executes its line, a survivor again in every other configuration). A fault no check notices is a gap, unless it changes nothing visible (an *equivalent* mutant, claimed below by an agent).

- M10 `m_vlsit_afifo_rd.sv:191` zero_to_one (survived in base.s1, model_off.s1, syn.s1, cell1.s1, cell3.s1, cell4.s1, macro.s1, small.s1, wr_slow.s1, rd_slow.s1): **gap** — The ack flop would reset to 1, so a read-domain hardware reset (alone, or while the write side is already released) presents a false acknowledge. A write FSM in REQ would then move to PTR before the …
- M27 `m_vlsit_afifo_cell_sync.sv:173` zero_to_one (survived in base.s1, model_off.s1, cell1.s1, cell3.s1, cell4.s1, macro.s1, small.s1, wr_slow.s1, rd_slow.s1): claimed equivalent: After a pending change is delivered at sim_cnt==0, sim_nxt already equals sim_cur. A leftover pend=1 reloads that same value and sim_cnt stays 0. A new input change takes priority and rewrites pend, …
- M32 `m_vlsit_afifo_cell_sync.sv:136` one_to_zero (survived in base.s1, model_off.s1, cell1.s1, cell3.s1, cell4.s1, macro.s1, small.s1, wr_slow.s1, rd_slow.s1): **gap** — The model's default enable would be 0, so without +AFIFO_MSYNC_EN the plain nominal-latency chain would be used instead of the random-latency model. The base run presumably passes the plusarg explici…

5 requirement(s) below the mutation threshold of 85.0 %: AF-10.7.4-25, AF-15.2-08, AF-20.2-12, AF-20.2-13, AF-7.3-07

Code or cover points never reached (first ones):

- line m_vlsit_afifo_rd.sv:172
- line m_vlsit_afifo_wr.sv:188
- line VLSIT_CELL_SRAM_1W1R.sv:41
- line VLSIT_CELL_SRAM_1W1R.sv:45
- line m_vlsit_afifo_cell_sync.sv:106
- line m_vlsit_afifo_mem.sv:68
- line m_vlsit_afifo_ram_macro.sv:35

### Formal check (SymbiYosys)

Every input sequence of up to 20 cycles was searched (multiclock (free clocks)); result {'BOUNDED': 8, 'CEX': 2, 'PROVEN': 1, 'UNSUPPORTED': 2}. PROVEN holds for every cycle; BOUNDED found no counterexample within the depth. Details: `work/formal.md`.

- **CHK-003 CEX** (trace work/formal/CHK-003.vcd)
- **CHK-013 CEX** (trace work/formal/CHK-013.vcd)

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
- [ ] The test/checker issue behind “test_chk_025_srst_partial_fifo — CHK-025 (8): 'o_empty fall after P0: expected the change…” is fixed and the run repeated.
- [ ] The specification question behind “CHK-003 assertion: 534 fails / 1,523,017 hits. First fail 239,353,000 ps (base.s1), durin…” is decided by the specification owner, and the spec, contract or checker is updated.
- [ ] The specification question behind “CHK-013 assertion: 721 fails / 1,681,616 hits. First fail 9,712,000 ps (base.s1), during …” is decided by the specification owner, and the spec, contract or checker is updated.
- [ ] Each hand edit of the generated tests and checkers corrects the test and weakens no requirement.
- [ ] The NOT_VERIFIABLE checks are covered elsewhere (another configuration, formal, lab) or accepted as open.
- [ ] The requirements that simulation cannot check are assigned to another verification method.
- [ ] Each surviving mutant is either truly equivalent or a known gap I accept.
- [ ] The unreached code and cover points are unreachable by design or accepted.
- [ ] Each formal environment assumption (verif/formal/nnc_env.sv) is an obligation the specification really places on the environment.
- [ ] Each formal counterexample or vacuous check is resolved (RTL, checker or environment) or accepted.
- [ ] I reproduced the regression (or CI did) and the outcome matches the report.

Then: `nnc gate approve async_gray_fifo G4_signoff --by "<your name>" --note "<waivers, open items>"`. The approval is bound to the current results.json: a later run makes it STALE.

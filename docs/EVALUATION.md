# Evaluation — phases 1 to 4 (2026-11-15)

This page collects the measurements of four steps taken after the first five designs:

1. Configuration-aware generation.
2. Formal checking per run-set configuration.
3. A sixth design, `ahb2axi_bridge`.
4. A comparison with the hand-written testbenches of the upstream repository.

Every number comes from a committed file under `designs/<ip>/work/`. The file is named next to the number.

**Approvals.** Gates G1–G3 were approved by Claude on the user's delegation and are recorded as such. G4 sign-off has **not** been given. It needs a qualified person: see [G4_REVIEW_REQUEST.md](G4_REVIEW_REQUEST.md).

Trang này tổng hợp số đo của bốn giai đoạn. Mọi con số đều lấy từ file trong `designs/<ip>/work/`. G1–G3 do Claude duyệt theo uỷ quyền. G4 **chưa** ai ký và cần một người có chuyên môn.

## Summary per design

| | apb_tlul | axi2apb | sync_fifo | async_apb | async_gray_fifo | ahb2axi (new) |
|---|---|---|---|---|---|---|
| Tests passing | 17/17 | 15/15 | 25/25 | 28/28 | 12/20 | 1/21 |
| Assertions failing | 0/17 | 0/17 | 0/11 | 0/18 | 2/13 (CHK-003, CHK-013) | 6/20 |
| Triage of the failures | — | — | — | — | 10/10 C (specification contradicts itself) | 12/12 A (RTL wrong) |
| Formal (depth 20): PROVEN / BOUNDED / other | 17 / 0 / 0 | 12 / 4 / 1 timeout | 7 / 2 / 1 timeout, 1 sim-only | 15 / 0 / 3 sim-only | 5 / 2 / 6 sim-only | 8 / 2 / **9 CEX**, 1 vacuous |
| Mutation score | 100 % (33/33) | 88.9 % (32/36) | 100 % (36/36) | 91.7 % (11/12) | 100 % (12/12) | not run (RTL fails) |
| Bug benchmark: caught, triage correct | 3/3, 3/3 | 3/3, 3/3 | 3/3, 3/3 | 3/3 | 3/3 | 1/3 (masked, see §3) |
| Hand-written baseline: bugs, mutants | 3/3, 33/33 | no upstream testbench | 3/3, 29/36 | 3/3, 10/12 | no upstream testbench | no upstream testbench |
| Test-bench hand fixes (triage B) | 0 | 4 (1 test model, 3 checker) | 1 (checker) | 1 | 13 | 0 |

Sources:
- tests and assertions: `work/results.json`;
- formal: `work/formal.md`;
- mutation: `work/mutation.json`;
- bug benchmark: `work/bench.md`;
- baseline: `work/baseline.md`;
- hand fixes: each design's `NOTICE.md` and the G3 notes.

For async_apb and async_gray_fifo, mutation used a sample of 12 mutants instead of 36 to save simulation time. Those scores are therefore less precise than the others and cannot be compared one to one with the earlier 36-mutant scores.

## 1. Configuration-aware generation (phase 1)

**What changed.** The generators receive the run set (`run_set.json`: configurations, parameters, defines, seeds). They must write tests and checkers that hold in every configuration, so nothing is tied to the default parameters.
- Numbers derived from parameters (synchronizer stages, depth) must be computed from the parameters.
- A literal is allowed only if it is marked `nnc-literal-ok` with a reason. `nnc/literals.py` checks this.

Both CDC designs were regenerated from G2 with this rule.

**Results:**

| | async_gray_fifo before | async_gray_fifo after | async_apb before | async_apb after |
|---|---|---|---|---|
| Hand fixes to tests/checkers (triage B) | 8 | 13 (10 simulation, 3 formal) | 0 | 1 |
| of which faults visible only in another configuration | 4 | **0** | 0 | 0 |
| Literal exemptions in generated tests | — | 0 | — | 0 |
| Checks PASS / FAIL | 26 / 3 (+3 not verifiable) | 23 / 9 | 35 / 0 | 35 / 0 |

**Reading:**
- **Configuration faults disappeared.** Examples of what no longer occurred: a synchronizer depth written as `S+3` for the default cell, a fill target valid only for depth 8, a window fixed to the default stages. All four faults of that kind in the first FIFO generation are gone.
- **The total number of hand fixes did not drop, so the goal "fewer hand fixes" was not met.** The regenerated FIFO tests are larger. They exercise more reset combinations (one-domain resets, software reset while traffic is pending), and new faults of a different kind appeared:
  - a scoreboard sampled only rising clock edges;
  - a model was not re-armed after a one-domain reset;
  - test-side checks fired before the first reset.

  Three more came from formal counterexamples (CHK-012 and CHK-013 ignored a threshold change and one-domain resets). Each fix is listed in [async_gray_fifo/NOTICE.md](../designs/async_gray_fifo/NOTICE.md). None relaxes what is checked in the states the specification defines.
- **async_apb:** the tests were valid at the first attempt. The one fix closes a scoring window at reset (`Completer.close`).
- **The FIFO FAIL count went from 3 to 9.** The cause is the same specification contradiction as before. REQ-VER-001 lets each synchronizer bit change independently, while spec lines 477 and 684 and DEC-023 say that only valid Gray values reach the destination. The regenerated checks observe that contradiction in more places.
  - Every failure is in a run with the metastability model on.
  - The model-off and synthesis-branch runs pass every test and assertion.
  - Triage judged all 10 analysed failures C: the specification is unclear or contradicts itself.
  - The designer decides; the checks were not relaxed.

## 2. Formal per configuration (phase 2)

**What changed:**
- Formal now runs once per distinct parameter set of the run set and merges the results:
  - a counterexample in any configuration makes the check CEX;
  - otherwise the check gets its weakest result (PROVEN < BOUNDED < TIMEOUT < ERROR);
  - a configuration in which a check is VACUOUS or UNSUPPORTED is not counted for it.
- The prove step uses `abc pdr` before `smtbmc`. PDR finds inductive invariants that plain k-induction misses.

| | PROVEN / BOUNDED before | PROVEN / BOUNDED after | Counterexamples after |
|---|---|---|---|
| apb_tlul | 10 / 7 | **17 / 0** | 0 |
| axi2apb | 9 / 7 | 12 / 4 (1 timeout) | 0 |
| sync_fifo | 4 / 5 | 7 / 2 (1 timeout, 1 sim-only) | 0 |
| async_apb | 2 / 12 | **15 / 0** (3 sim-only) | 0 |
| async_gray_fifo | 1 / 8 (+2 CEX) | 5 / 2 (6 sim-only) | 0 |
| ahb2axi | — | 8 / 2 (1 vacuous) | **9** |

**Reading:**
- **More checks are proven:** on the five earlier designs, PROVEN went from 26 to 56 checks. Most of the gain is checks that were BOUNDED before (no counterexample within 20 cycles, but nothing proven).
- **The FIFO figure is not a pure improvement.** The regenerated read-side checker (`nnc_chk_rd.sv`) measures time, so CHK-001 to CHK-004, including the former counterexample CHK-003, are now simulation-only. They are no longer checked formally. CHK-013 is proven in five configurations and bounded with cell 4 after the hand fix that excludes one-domain resets. That fix follows the reading of ASM-005 and contract CHK-023, which the G4 reviewer must confirm.
- **async_apb configurations 4ph, sync3 and sync4:** CHK-003 to CHK-006 are VACUOUS within depth 20, because a handshake with more synchronizer stages does not complete in 20 cycles. Those configurations do not count for these checks; the other configurations prove them.

## 3. A new design: ahb2axi_bridge (phase 3)

The upstream design is `common_rtl/005_AHB2AXI_Bridge` @ 53407f2. It is an AHB5 subordinate converting to AXI4, with 52 ports and burst aggregation. It comes with lint logs but no testbench. The flow ran with no change to the code:

| Step | Result | Source |
|---|---|---|
| G1 rules | 234 kept, 39 rejected (structural, documentation), 6 open questions answered conservatively and marked for G4 | `nnc_state.json`, `work/rules.md` |
| G2 contract | 40 checks (20 assertions, 20 tests) covering 177 rules; 57 not verifiable by simulation | `work/contract.md` |
| G3 sources | tests valid at the first attempt, 0 literal exemptions, 0 hand fixes | `nnc_state.json` |
| Simulation (4 runs: default ×2 seeds, 8 IDs, 3/5 IDs) | **1/21 tests**, 6/20 assertions fail (CHK-015: 3834 fails, CHK-016: 9771) | `work/results.json` |
| Triage | 12/12 analysed failures A (RTL wrong) | `work/triage.md` |
| Formal | 8 PROVEN, 2 BOUNDED, 1 VACUOUS, **9 CEX**, all judged A | `work/formal.md`, `work/formal_triage.md` |
| Code / functional coverage | line 86.0 %, toggle 65.7 %, functional 36/40 | `work/coverage.md` |
| Report | checks 14 PASS / 25 FAIL / 1 NOT_HIT; rules 34 VERIFIED / 142 FAILED / 57 not verifiable by simulation; agent cost US$21.1 | `work/report.md`, `work/review_packet.md` |
| Bug benchmark | **1/3** caught (AH3) | `work/bench.md` |

**The bug benchmark is masked on this RTL.** A benchmark bug counts as caught only when it causes a failure that does not already occur on the delivered RTL. Here 20 of 21 tests already fail, so:
- **AH1** (WLAST one beat early in an aggregated burst) is never reached: the burst tests hang before any W beat is checked.
- **AH2** (read DECERR returned as OKAY) lands on CHK-015, which already fails 3834 times.
- **AH3** (alignment checks only address bit 0) gives new failures and is caught.

The 1/3 measures the masking, not the strength of the verification. A meaningful benchmark needs RTL on which the verification passes.

**Findings on the delivered RTL.** These are confirmed by simulation, formal counterexamples and the specification text. Details: [fix_candidate/README.md](../designs/ahb2axi_bridge/fix_candidate/README.md).

1. **Pipelined AHB transfers are dropped.** In `m_ahb2axi_ahb_if.sv:87-88`, `o_req_valid` reads `o_rsp_ready` before the same `always_comb` block assigns it. A transfer whose address phase overlaps the end of the previous data phase therefore gets OKAY but no AXI transaction.
2. **Single writes use a stale burst address.** In `m_ahb2axi_ctrl.sv:859-862`, `w_cap_stop` sets `reg_burst_fallback` in every state. This also changes the AW payload while AWVALID is high and AWREADY is low.
3. **HREADYOUT is forced low when the next address cannot be queued.** At `m_ahb2axi_ahb_if.sv:104-105`, this stretches the second AHB ERROR cycle and adds wait states to IDLE/BUSY transfers.
4. **Reset value of `o_axi_arprot` (3'b100).** This is either a fault or a gap in the specification: the reset-value column may or may not bind payload ports (spec lines 176 and 467).

Fix candidates exist for findings 1 and 2. They are checked on a copy with `nnc inject`, and `rtl/` is unchanged.

| RTL | Tests | Failing assertions |
|---|---|---|
| delivered | 1/21 | 6 |
| + fix 1 | 3/21 | 5 |
| + fix 1 + fix 2 | 6/21 | 3 |

After both fixes, 13 tests still hang in burst and reset-in-flight scenarios. The next diagnostic step is a triage run on the patched copy. Whether to apply any fix is the designer's decision.

**Generality.** A new protocol pair (AHB5 → AXI4), a parameterised ID width and a design with real faults went through G1–G3 without changes to the orchestrator or the prompts. The verification was generated from the specification only and found faults the upstream lint flow did not report.

## 4. Baseline: the hand-written testbenches (phase 4)

`nnc baseline <ip>` runs the upstream hand-written testbench as its own script runs it, against:
- the bug-benchmark faults;
- the same mutants as the NNC mutation run.

A fault counts as caught by a side if any of its runs fails.

| Design | Upstream testbench | Bugs caught: hand-written / NNC | Mutants killed: hand-written / NNC |
|---|---|---|---|
| sync_fifo | `002_SyncFIFO/verification`, 8 runs per RTL | 3/3 / 3/3 | **29/36 / 36/36** (7 only by NNC, 0 only by hand-written) |
| apb_tlul_bridge | `example/apb_tlul_bridge/verification`, 2 runs | 3/3 / 3/3 | 33/33 / 33/33 |
| async_apb_bridge | `004_AsyncAPBBridge/verification`, 64 runs | 3/3 / 3/3 | 10/12 / 11/12 (1 only by NNC, 1 by neither) |

**Limits of this comparison:**
- **On no design did the hand-written testbench kill a mutant that NNC missed.** NNC killed 8 more in total (7 on sync_fifo, 1 on async_apb). The one async_apb mutant neither killed (M07, `m_vlsit_apbcdc_cell_sync.sv:171`) is the NNC survivor already listed in its review packet.
- **Few designs have an upstream testbench.** The upstream repository has none for async_gray_fifo (`001` holds RTL, lint and waveforms only) or ahb2axi (`005`), and no copy of axi2apb. Three designs is a small sample.
- **The bug-benchmark faults are not independent of the flow.** They were written for this flow by the same assistant, with knowledge of the RTL. Three per design cannot separate the two testbenches; the mutants are the stronger measure.
- **The mutants are a limited sample.** They are one-line, drawn only from executed lines, at most 36 per design, and some may be equivalent.
- **Effort is not compared:** human hours for the hand-written testbench against agent cost for NNC.

## 5. What a reviewer must still decide

See [G4_REVIEW_REQUEST.md](G4_REVIEW_REQUEST.md). In short:
- the delegated answers of G1;
- the formal environment assumptions;
- the FIFO specification contradiction and the one-domain-reset exclusion (ASM-005);
- the ahb2axi RTL findings and fix candidates;
- the CHK-020 reset-value question.

# Evaluation — phases 1 to 16 and OpenTitan rv_timer and gpio, stability, coverage scope and CDC (2026-11-15; design half 2026-11-18; hardening 2026-11-19; formal depth, spec-lint and two new designs 2026-11-20; OpenTitan rv_timer 2026-11-21)

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

## 6. The design half (phases 5 to 10, 2026-11-16 to 2026-11-18)

Phases 5 to 10 add the design half of the flow (see [ARCHITECTURE.md §19](ARCHITECTURE.md) and [GUIDE.md §6](GUIDE.md)):
- **Phase 5:** checked parameter values and a final configuration (gate D1);
- **Phase 6:** RTL written by agent A15, which never sees the verification. The RTL then goes through code rule checks, Verilator lint and Yosys synthesis on GF180MCU (gate D2);
- **Phase 7:** a closed loop. Simulation or formal failures that triage judges A (RTL wrong) go back to A15 as specification-level text;
- **Phase 8:** `restyle` with a formal equivalence proof;
- **Phase 9:** a specification draft from a short description, and DOCX/PDF export;
- **Phase 10:** a design made from scratch.

### 6.1 Regenerating two verified designs from their specification

`nnc derive <ip> gen_<ip>` copies a verified design without its RTL: the specification, the approved rules, contract and verification (G1–G3), and the upstream hand-written testbench. A15 then writes a new RTL from the specification alone. The same approved verification runs on it unchanged, and so does the upstream testbench.

| | gen_apb_tlul_bridge | gen_sync_fifo |
|---|---|---|
| RTL generation | clean after 2 attempts, US$2.44 | clean after 1 attempt, US$2.11 |
| Synthesis GF180 (cell area; ABC delay at SS) | 12 789 µm²; 18.9 ns | 36 864 µm² (with a stand-in RAM macro) |
| Rules tagged in the RTL | 74.6 % | — |
| Simulation (approved NNC verification) | 17/17 tests, 0/17 assertions failing, line 95.1 % | 24/25 tests, 0/11 assertions failing, line 97.3 % (after repair) |
| Formal (depth 20) | 17 PROVEN | 6 PROVEN, 2 BOUNDED, **1 CEX** (CHK-008), 1 timeout, 1 sim-only |
| Mutation (NNC) | 36/36 | 36/36 |
| Upstream hand-written testbench | passes; mutants 36/36 (NNC 36/36) | passes (8 runs); mutants **31/35 (NNC 35/35)** |
| Closed loop | no failure | 1 repair from formal results (US$0.66), then stopped on a question for the specification owner |

Sources: `designs/gen_*/work/` (`rtl_gen.md`, `results.json`, `formal.md`, `mutation.json`, `baseline.md`, `close_loop.json`, `rtl_history/`).

**The formal check found two RTL faults that simulation missed (gen_sync_fifo).**
- **The fault.** The first RTL added a third input to the write "block" term: a software-reset request that arrives during a running sequence. The specification (§10.6) defines the term with two inputs only, busy flop OR `i_rst_n_sw` = 0. So in the one RUN cycle between two sequences, `o_full` was 1 on an empty FIFO.
- **What caught it.** Simulation saw one assertion failure in 16 543 samples, and triage called it a specification question (C). Formal produced counterexamples for CHK-010 and CHK-011, and formal triage judged both A (RTL wrong) with the spec lines.
- **The repair.** `nnc fix-rtl gen_sync_fifo --from formal` gave A15 only the specification-level text of the two faults. It removed the extra term in one attempt (`work/rtl_history/rev01` keeps the first RTL). After the repair, CHK-010 and CHK-011 no longer give a counterexample and the simulation assertion failure is gone.

**What is left on gen_sync_fifo** is CHK-008 (test `chk_024` part b, and the formal counterexample): a second software-reset pulse during a running sequence.
- The generated RTL remembers the pulse and starts a new sequence after one RUN cycle, which is what REQ-SRST-008 asks for.
- The approved check expects `o_sw_rst_busy` to stay 0. Its contract says tests must not drive such pulses, but the generated stimulus does.
- Simulation triage judges C (specification unclear) and formal triage judges E (an environment assumption is missing).
- The delivered upstream RTL passes this check, so the two RTLs differ in a case the specification leaves open.

The loop stops here by design. Changing the check, the contract or the specification is the specification owner's decision, and nothing was changed. D2 of gen_sync_fifo stays open for the same reason.

**Limits.**
- The two specifications prescribe their microarchitecture in detail (state machines, flop lists, the block term), so a generated RTL is close to the original by construction. This shows the flow can rebuild a specified design. It does not show that A15 designs well from a loose specification. §6.3 is the test of that.
- On both designs the upstream hand-written testbench killed no mutant that NNC missed. NNC killed 4 more on gen_sync_fifo, the same pattern as the delivered RTL (§4).

### 6.2 Restyle with equivalence (apb_tlul_bridge)

`nnc restyle apb_tlul_bridge` asked agent A16 to rewrite the delivered RTL to `docs/RTL_RULES.md` without changing behaviour.
- **Rule findings:** 6 warnings before, 0 after.
- **Equivalence:** a Yosys miter with SymbiYosys gives **PROVEN** (BMC and PDR, depth 20): every output is equal in every cycle for every input sequence after reset, in this configuration.
- **Cost:** 1 attempt, US$0.93.
- **Suspected bugs:** A16 reported 2 in the original (`restyle/restyle.md`); both are robustness observations, and it kept the behaviour.
- **Where it lives:** the rewrite is in `designs/apb_tlul_bridge/restyle/rtl/`. `rtl/` is unchanged, and adopting the rewrite is the designer's decision.
- **Checking the checker:** a hand-made one-line change (a `pstrb` comparison) gave **CEX** with the first differing output named: "outputs differ at step 4: o_apb_pready (original 1, rewritten 0)".

### 6.3 A design from scratch: uart_lite

**Input.** A 30-line description (`spec/design_description.md`): an 8N1 UART with valid/ready byte streams, a 2-flop synchronizer, an overrun pulse and a bit period of 4 to 65 535 clocks. Target: GF180MCU at 50 MHz.

| Step | Result | Cost |
|---|---|---|
| `spec-draft` (A0) | 1 attempt; 12 ports, 77 requirement IDs, 15 assumptions, 7 open questions; then 12 decisions and 3 answers made on delegation | US$0.72 |
| extract + review (G1) | 168 rules, 154 after review | US$0.94 |
| contract (G2) | 32 checks (13 assertions, 19 tests); 22 rules not verifiable by simulation | US$1.08 |
| params (D1) | 4 configurations: N = 16 (default), 4 (min), 5 (odd), 1024 (wide) | — |
| `gen-rtl` (A15, D2) | clean in 1 attempt; 3 files, 367 lines; 6 553 µm², 7.7 ns at SS (budget 20 ns) | US$0.91 |
| verification (G3) | 13 assertions, 40 cover points, 20 tests, 1 environment assumption | US$6.73 |
| closed loop, round 0 | 20/20 tests; 6 assertion failures, all judged B (verification wrong); no RTL repair | US$1.73 |
| after 2 hand fixes (B) | **20/20 tests, 13/13 assertions, 7 runs in 4 configurations**, line 98.7 % | — |
| formal (depth 64, 4 configurations) | no counterexample; 4 PROVEN, 6 BOUNDED, 2 VACUOUS, 1 sim-only | — |
| mutation | **35/36** (M19, the reset value of the start-detect flop, claimed equivalent) | — |

Sources: `designs/uart_lite/work/` (`spec_draft.md`, `rules.md`, `contract.md`, `rtl_gen.md`, `triage.md`, `formal.md`, `mutation.json`, `report.md`), `designs/uart_lite/NOTICE.md`.

**What the design shows.**
- **The RTL was right first time.** Every failure was in the generated verification, not in the RTL:
  - the test harness clocked an un-reset design for three edges;
  - the SVA receiver model started a frame on any low sample instead of a falling edge.
- **Triage named both causes with the lines to change.** Both fixes make the checks follow the specification. Neither relaxes one. They are recorded as hand fixes (`NOTICE.md`, G3 note).
- **Two independent agents met in the middle.** The RTL writer and the verification writer never saw each other's output, and they now agree on all 32 checks. That is the evidence the flow is built to produce. It is not a sign-off.
- **Cost.** About US$12 for the whole design, not counting the delegated decisions.

**Limits.**
- The formal depth of 64 cycles covers a whole frame only for N = 4 and 5. Checks that need two frames (CHK-004, CHK-005) are VACUOUS there and rest on simulation.
- The specification and every open-question answer were decided on delegation, not by a hardware designer.
- G4 is open.

### 6.4 Two faults of the infrastructure

- **WSL crash.** During the uart_lite runs WSL stopped ("Catastrophic failure"). The next formal run reported every check ERROR, and the mutation run reported 36/36 "not compiled", which looked like design results. Both commands now stop with a message naming the tool host instead of writing such results. The runs were repeated after `wsl --shutdown`.
- **Derived designs and the bug benchmark.** The benchmark faults (`bugs/`) are one-line patches of the delivered RTL, so they cannot apply to a generated RTL. `derive` no longer copies them, and `baseline` skips the bug comparison when a design has no benchmark (the mutant comparison still runs).

## 7. Hardening, formal checks of the mutants, verification fixes by an agent (phases 12 to 14, 2026-11-19)

### 7.1 Every recorded run reproduces, and formal reruns

Before phase 12, CI reproduced only the primary run of each design. Every other configuration of a run set existed only as a recorded result.

**Kits per configuration.** `nnc kit` now writes `sim/configs/<config>/` for each other configuration. `sim/configs/runs.tsv` lists every recorded run. The primary kits it rewrites are byte-identical to the committed ones, apart from the shared `nnc_cocotb.py`, which now reads `NNC_INTERFACE`.

**Local runs (WSL, make only, `nnc kit-check --run`).** Every run below gave **SAME OUTCOME**:

| Design | Runs |
|---|---|
| uart_lite | base.s2, min.s1, min.s2, odd.s1, odd.s2, wide.s1 (all 6 non-primary runs) |
| async_apb_bridge | model_off.s1 (plusargs), syn.s1 (synthesis macro), apb5.s1 |
| async_gray_fifo | macro.s1, base.s3 |
| ahb2axi_bridge | ids8.s1 (20 of 21 tests fail on the delivered RTL; the same tests failed) |

**`nnc formal-check`** reruns SymbiYosys with the recorded configuration and writes nothing.

| Design | Result | Time |
|---|---|---|
| gen_apb_tlul_bridge | 17 PROVEN: SAME OUTCOME | 12 s |
| gen_sync_fifo | the CHK-008 counterexample, 1 TIMEOUT, 2 BOUNDED, 6 PROVEN: SAME OUTCOME | 10.5 min |

CI now runs both checks on `main`, on pull requests and weekly:
- `kit-configs`: 4 designs;
- `formal`: 9 designs.

**Tool host.** A WSL that runs no command is now retried once, after 15 s. If it fails again, the stage stops with `host error` and records nothing. `nnc doctor` probes the tools inside WSL: Verilator 5.055, cocotb 2.1, Yosys 0.70, SymbiYosys, ABC, Yices 2.7 and both GF180 liberty files were found.

### 7.2 Surviving mutants, checked by formal

`nnc mutate-equiv` compares each surviving mutant with the RTL (Yosys miter, BMC and PDR, depth = the design's formal depth). The 6 surviving mutants of all designs were checked:

| Design | Mutant | Agent A12 said | Formal | Meaning |
|---|---|---|---|---|
| axi2apb_bridge | M09 `apb_ctrl.sv:165` default `pwrite` | equivalent | **PROVEN** | equivalent |
| axi2apb_bridge | M14 `apb_ctrl.sv:223` `&&`→`\|\|` | equivalent | **PROVEN** | equivalent |
| axi2apb_bridge | M13 `wr_seq.sv:183` `\|\|`→`&&` | equivalent | **CEX** | `o_axi_bresp` SLVERR → OKAY at step 6 |
| axi2apb_bridge | M21 `rd_seq.sv:182` `\|\|`→`&&` | equivalent | **CEX** | `o_axi_rresp` SLVERR → OKAY, `rlast` and `rvalid` change |
| uart_lite | M19 `rx.sv:74` reset value of `r_rxd_prev` | equivalent | PROVEN for N = 16, 4, 5; BOUNDED for N = 1024 | equivalent where proven; the N = 1024 proof did not close within 900 s |
| async_apb_bridge | M07 `cell_sync.sv:171` | gap | SIM_ONLY | the metastability model: formal reads the synthesis branch |

Sources: `designs/<ip>/work/mutation.json` (field `equivalence`), traces in `designs/axi2apb_bridge/work/mutation_equiv/`.

**What the formal check found.** Agent A12 called M13 and M21 equivalent. Its reason: they differ only for a WRAP burst that has a bad length or a misaligned address, which is "illegal AXI". The counterexample is a WRAP burst of 16 beats of 4 bytes that starts at address `0x2`:
- the delivered RTL rejects it with SLVERR, the defensive rejection the specification asks for (AB-1.1-03; AXI A3.4: a WRAP burst starts size-aligned);
- the mutant accepts it.

No test drives such a burst, so the verification has a real gap here. The agent's claim hid it. With M09 and M14 proven equivalent, the axi2apb score without equivalent mutants is 94.1 % (recorded 88.9 %). The test plan was not changed: closing the gap is a G3 decision, and it is now in [G4_REVIEW_REQUEST.md](G4_REVIEW_REQUEST.md).

**Limit.** In this check the inputs are free after reset; the formal environment (`verif/formal/nnc_env.sv`) is not applied. So a CEX may use an input sequence the environment forbids, and a reviewer must read it. Here the input is one the specification says the bridge must reject, so it is legal stimulus for a test.

### 7.3 Verification faults fixed by an agent (phase 14)

**Why.** On uart_lite, round 0 gave 6 assertion failures, all judged B (the verification was wrong). Until now a person fixed them by hand (§6.3). `nnc fix-verif` gives the same job to agent A17.

**How the test was set up.** The two hand fixes were removed again: `work/fix_verif_experiment/rebuild_prefix.py` strips the marked hunks. The result is byte-identical to the output of the generating agents A7 and A5 recorded in the agent logs. In a copy of the design with that verification:
- the regression reproduced the 6 failures: 20/20 tests, CHK-002, -003, -005, -006, -009 and -010 failing in the 7 runs;
- `nnc fix-verif` then ran with the original triage.

**What A17 received.**
- **6 faults.** For each: what the specification says, what the verification does, and what to change. No sentence names an RTL file, module or "the RTL", and the backend refused `rtl/` as an input.
- **Inputs:** the specification, rules, contract and verification files.

| Attempt | A17 changed | Candidate on the RTL (7 runs) | Cost |
|---|---|---|---|
| 0 | `nnc_chk_rx.sv`: the model register `mdl_prev`, reset 1, start on `mdl_prev && !i_rxd` (REQ-RX-003). `test_uart_lite.py`: reset before the clock starts, but only `if sim time == 0` | CHK-003/005/006/009 fixed; CHK-002 and CHK-010 still fail at 0, 20 and 40 ns | US$1.62 |
| 1 (with the feedback "CHK-002: 1 failure, first at 0 ps; ...") | the condition becomes "first `Env.start()` of the simulation". A17 explained why: tests that end as not verifiable for some N let time move on before the first real start | **20/20 tests, 0 failing assertions in all 7 runs** | US$1.17 |

The code check found no weakening and gave no warning. `--apply` copied the 2 files, wrote NOTICE.md and left G3 STALE. Evidence: `designs/uart_lite/work/fix_verif_experiment/` (`verif_fix.md`, `verif_fix.json`, `FAULTS.json`, `results_before.json`).

**Compared with the hand fixes.**
- **The checker fix is the same:** the same register, the same reset value, the same start condition.
- **The harness fix differs.** The hand fix resets before the clock at every `Env.start()`; A17 does it only at the first start. Both satisfy ENV-002, and both make all 32 checks pass.
- **Cost:** about US$2.8 and no person, against two hand edits after reading the triage.

**Limits.**
- One design, with a triage that had already named the causes.
- A17's rule against weakening is checked by code only for structural signs: removed checks, assumptions, skips. An expected value changed to the wrong one would pass the code check. That is why `--apply` reopens G3 and a person reads the diff.

### 7.4 Deeper formal where a check is vacuous (phase 15)

**Why.** On uart_lite, CHK-004 and CHK-005 were VACUOUS at depth 64: their antecedent is a byte delivered while the previous one is still held. That needs two UART frames, and one frame alone takes 10 × `PARA_UART_CLKS_PER_BIT` cycles. A vacuous check proves nothing.

**What changed.** `formal_max_depth=N` (design config). Each check that is VACUOUS at `formal_depth` is run again alone at twice the depth, and again, up to N. Only those checks pay the extra time. uart_lite: `formal_depth=64`, `formal_max_depth=128`.

| | Before (depth 64) | After (escalation to 128) |
|---|---|---|
| Merged over the 4 configurations | 4 PROVEN, 6 BOUNDED, **2 VACUOUS**, 1 sim-only | 4 PROVEN, 8 BOUNDED, **0 VACUOUS**, 1 sim-only |
| CHK-004, CHK-005 | VACUOUS | BOUNDED (no counterexample within 128 cycles, in `min` and `odd`) |

Sources: `designs/uart_lite/work/formal.json`, `formal.md` (rows marked `[depth 128]`).

**What is still vacuous, per configuration.** In `base` (16 cycles per bit) and `wide` (1024) five receive checks (CHK-003/004/005/007/008) stay VACUOUS even at 128 cycles: one frame does not fit. They are covered by `min` (4) and `odd` (5), where a frame is 40 or 50 cycles. The merged result counts a check as vacuous only if it is vacuous everywhere. Reaching them at 16 cycles per bit would need about 400 cycles, which BMC with this solver does not finish in the time limit; simulation covers those configurations.

**CI.** The full rerun of uart_lite (4 configurations, escalation) lost its GitHub-hosted runner after 96 minutes. `nnc formal-check --config NAME` now reruns one configuration and compares only its recorded statuses; CI runs uart_lite as 4 jobs. Local check: `formal-check uart_lite --config min` gave SAME OUTCOME (4 BOUNDED, 8 PROVEN, 1 sim-only) in 22.7 minutes.

### 7.5 Specification gaps before any code (phase 15, `nnc spec-lint`)

**Why.** The gen_sync_fifo counterexample on CHK-008 (§6.1) came from a question the specification never answered: what happens to a second software-reset pulse during a running sequence. It was found after spec, RTL, tests and formal had all been generated.

**What it does.** Agent A18 reads only the specification and lists scenarios it leaves open or states twice in conflicting ways: simultaneous events, a request while busy, reset during an operation, back-pressure, parameter extremes, errors, the initial state, contradictions. Each gap gives a scenario, quotes, the question and the possible readings, with `file:line` references that code checks (a gap without a valid reference is marked). Nothing is changed: the answers are decisions before G1.

| Design | Gaps (high / medium / low) | Notable | Cost |
|---|---|---|---|
| gen_sync_fifo (spec written by hand earlier) | 4 / 7 / 1 | **GAP-002 is the CHK-008 question**, found from the specification alone | US$0.97 |
| spi_master (new, phase 16) | 0 / 2 / 3 | simultaneous events, the initial state, 2 contradictions; answered before G1 | US$0.71 |
| axil_regfile (new, phase 16) | 0 / 2 / 3 | reset ending held states, behaviour before the first reset, "from edge n"; answered as D-014..D-018 and REQ-VER-006/007 | US$0.51 |

**Limit.** A18 finds questions, not answers: a person (here Claude on delegation, labelled) still decides each one, and a gap A18 misses is not reported.


## 8. Two more designs from a short description (phase 16, 2026-11-19 to 2026-11-20)

**Why.** uart_lite (§6.3) was the only design the flow made from scratch. Two more test whether that result repeats: a serial master with timing in i_clk cycles (`spi_master`) and a bus slave with an AXI4-Lite interface (`axil_regfile`). For both, the input is a short description written for this repository. No upstream RTL or testbench exists, so there is no hand-written baseline and no bug benchmark.

| Step | spi_master | axil_regfile |
|---|---|---|
| Description | 31 lines: SPI master, mode 0–3, 8-bit bytes, bursts with `i_cmd_last`, SCLK = i_clk / 2·D | 51 lines: AXI4-Lite slave, 1–16 read/write registers, byte strobes, SLVERR on unmapped addresses |
| `spec-draft` (A0) | 1 attempt; 15 ports, 97 requirement IDs | 2 attempts; 23 ports, 123 requirement IDs |
| `spec-lint` (A18), see §7.5 | 0 / 2 / 3 gaps, answered before G1 | 0 / 2 / 3 gaps, answered before G1 |
| Rules after review (G1) | 206 | 193 |
| Contract (G2) | 41 checks (27 assertions, 14 tests) | 37 checks (17 assertions, 20 tests) |
| Configurations (D1) | base (D = 4), min (D = 1), max (D = 255) | base (8 registers), min (1), max (16, 16-bit address), full_a7 (16, 7-bit address) |
| `gen-rtl` (A15, D2) | clean after 2 attempts; 1 file, 360 lines; 8 462 µm², 10.8 ns at SS | clean after 1 attempt; 2 files, 409 lines; 47 805 µm², **31.5 ns at SS against a 20 ns period** |
| Verification failures | 7 in simulation and 6 formal counterexamples, all judged B (verification wrong), fixed by A17 in 2 rounds | none |
| Agent cost, whole flow | US$21.91 in 56 calls (US$2.57 in 4 failed calls) | US$12.57 in 47 calls |

**Results.**

| | spi_master | axil_regfile |
|---|---|---|
| Tests | 15/15 | 21/21 |
| Assertions failing | 0/27 | 0/17 |
| Run set | 5 runs, 3 configurations | 7 runs, 4 configurations |
| Rules VERIFIED / not verifiable by simulation | 174 / 32 | 171 / 22 |
| Code coverage: line, toggle | 94.8 %, 95.2 % | 100 %, 95.8 % |
| Functional coverage | 37/39 (COVP-013, COVP-014 not hit) | 40/40 |
| Formal, merged: PROVEN / BOUNDED / not checked | 6 / 7 / 14 simulation-only | 15 / 1 / 1 simulation-only |
| Formal counterexamples | 0 (after the A17 round on formal) | 0 |
| Mutation | 91.7 % (33/36); the 3 survivors are proven equivalent | 93.1 % (27/29); the 2 survivors are proven equivalent |
| Hand fixes | 0 | 0 |

Sources: `designs/<ip>/work/report.md`, `formal.md`, `mutation.json`, `rtl_gen.md`, `triage.md`, `spec_lint.md`; `designs/spi_master/NOTICE.md` (the A17 changes).

**spi_master: two rounds of A17.**
- **Simulation (7 failures).** The test helper `wait_idle` returned before the cycle monitor had logged the current cycle; a test compared MOSI traces that depended on earlier traffic; the reset checker sampled before the reset had settled; a checker compared SCLK in pause with the live `i_cpol` instead of the value captured at burst start; `setup()` asserted reset in the same time step as a clock edge, which ENV-007 forbids. Changed: `nnc_chk_flow.sv`, `nnc_chk_reset.sv`, `test_spi_master.py`.
- **Formal (6 counterexamples, CHK-011..014, CHK-023, CHK-025).** The MOSI and SCLK checkers reloaded CPOL_b and CPHA_b at every handshake, also inside a burst. The specification captures them once, at burst start. Changed: `nnc_chk_mosi.sv`, `nnc_chk_sclk.sv`. The formal environment was **not** tightened to hide these traces: applying ENV-003 (`i_cpol`/`i_cpha` change only while `o_cs_n` = 1) as an assumption would have removed REQ-MODE-003 ("changes during a burst have no effect") from the formal check.
- Every change went through the weakening check and a candidate simulation before `--apply`, and G3 was approved again after each round. A17 cost US$4.08 in total.

**Not yet covered.**
- spi_master, COVP-013 and COVP-014: no test completes a burst of 17 bytes or more. SPI-12-19 asks for "at least 16" and the 16-byte burst is covered (COVP-012); the endless-burst test (CHK-031) never ends its burst. The specification does not require longer completed bursts, so this is a stimulus gap, not a failure. `nnc cover spi_master --target 100 --metric functional` would ask for the missing tests.
- spi_master, 14 checks are simulation-only. Their checkers use `$time` to judge timing within a cycle, so formal does not translate them. In configuration `max` (largest D), 3 checks are vacuous at depth 32 and 7 bounded; the merged result counts them from `base` and `min`.
- axil_regfile, REQ-IMP-001 (timing at 50 MHz, worst corner): ABC estimates the longest combinational path at 16.9 ns (TT) and **31.5 ns (SS 125 °C)**, without wires or setup time. The likely path is the read multiplexer. This was left open at D2 and needs STA, which this flow does not have.

**A fault of the mutation stage, found here.** Verilator reports the line coverage of a continuous assignment in an inlined submodule on the declaration line of its target, not on the `assign` line. Since phase 12 the mutation stage only mutates executed lines, so these `assign` lines were excluded even when they ran. `nnc/mutate.py` now counts an `assign` line as executed when the declaration line of its target is executed (`assign_lines`, unit test `AssignLinesTest`). Effect on the candidate pool of every design (the earlier scores were not rerun):

| Design | Candidates | Executed before | Executed now |
|---|---|---|---|
| ahb2axi_bridge | 290 | 220 | 233 |
| apb_tlul_bridge | 36 | 33 | 33 |
| async_apb_bridge | 128 | 69 | 75 |
| async_gray_fifo | 100 | 58 | 64 |
| axi2apb_bridge | 235 | 230 | 230 |
| gen_apb_tlul_bridge | 55 | 50 | 55 |
| gen_sync_fifo | 69 | 44 | 47 |
| sync_fifo | 68 | 54 | 62 |
| uart_lite | 41 | 37 | 39 |
| spi_master | 64 | 54 | 57 |
| axil_regfile | 33 | 26 | 29 |

The scores of spi_master and axil_regfile above were measured with the fix.

**CI.** Both designs are added to the kit, kit-configs and formal jobs (spi_master's formal as one job per configuration).

## 9. An industrial design: OpenTitan rv_timer (2026-11-20 to 2026-11-21)

**Why.** Every earlier design is small and was written for, or next to, this repository. OpenTitan's `rv_timer` is
an open-source industrial IP with a public specification, a TL-UL register interface generated by OpenTitan's
register tool, a differential alert and bus-integrity logic. It tests whether the flow scales to RTL that uses
the full SystemVerilog of a large project (packages, structs, `prim_*` primitives), and to a specification spread
over five documents. The RTL is the design under test and was never shown to the agents that write checks and
tests. OpenTitan's own UVM test bench is not copied (licence and isolation); §11.2 compares with its public numbers.

**Set-up** (`designs/ot_rv_timer/`, Apache-2.0, see its `NOTICE.md`):
- RTL: the 44 OpenTitan files of rv_timer and what it uses, 8 635 lines, unchanged, plus a 127-line wrapper
  `ot_rv_timer_nnc.sv` written here. The wrapper flattens the struct ports, generates the request integrity, checks
  the response integrity and terminates the alert with OpenTitan's `prim_alert_receiver`. It changes no behaviour.
- Golden sources: the rv_timer documentation (678 lines with the wrapper's integration part), and four standards:
  the TL-UL bus specification, comportability, register tool, alert handler (relevant sections only).
- One configuration (rv_timer has no parameter in this integration), two seeds.

| Step | Result |
|---|---|
| `spec-lint` (A18) | 20 gaps (9 high, 8 medium, 3 low), US$1.03 |
| Rules after review (G1) | 228 (54 rejected, 3 merged); gaps and open questions answered as spec decisions **D-001..D-020** (spec §8), made from the documents only; where the documents are silent the checks use bounds |
| Contract (G2) | 35 checks (13 assertions, 22 tests) over 151 rules; 77 rules not verifiable by simulation (mostly host obligations or standard text outside this IP) |
| Simulation failures | 4 (3 tests, assertion CHK-006 at time 0), all judged B (verification wrong); fixed by A17 in 2 rounds |
| Formal counterexamples | 3 at first (CHK-003, CHK-004, CHK-008); CHK-003 and CHK-004 judged B and fixed by A17 in a third round; CHK-008 see below |
| Agent cost, whole flow | US$22.09 in 70 calls (A17 US$4.29, A7 US$4.16, A14 US$3.05) |

**Results** (`work/report.md`, `formal.md`, `mutation.json`):

| | ot_rv_timer |
|---|---|
| Tests | 23/23, both seeds |
| Assertions failing | 0/13 |
| Rules VERIFIED / not verifiable by simulation | 151 / 77 |
| Functional coverage | 38/39 cover points |
| Code coverage: line, toggle | 24.2 %, 80.3 % |
| Formal (depth 32): PROVEN / BOUNDED / TIMEOUT / simulation-only / CEX | 7 / 2 / 1 (CHK-011) / 2 (CHK-006, CHK-007) / **1 (CHK-008)** |
| Mutation | 58.3 % (21/36); of the 15 survivors formal proves 11 equivalent, 3 differ, 1 not checked: **84.0 %** without the equivalent ones |
| Hand fixes | 0 |

The line coverage is low because the OpenTitan files include whole packages (`prim_secded_*`, `prim_mubi_pkg`,
`tlul_pkg`) of which rv_timer calls a few functions; toggle and functional coverage are the meaningful measures.

**CHK-008, the remaining counterexample.** CHK-008 is a self-check of the stimulus (it reads only inputs). Formal
finds a request with the non-contiguous byte mask `0101`. The DUT answers it with `d_error` = 1, as the TL-UL
specification allows. Two passages disagree on whether the test bench may send such a mask: the TL-UL host rule
("hosts in this project do not leverage non-contiguous masks", rule TL-T3.1.3.4-02, checked by CHK-008) and
RT-4.1-05 ("requests that the TL-UL specification lists as error cases ... bad size or mask ... are legal
stimulus"), which the formal environment follows. Triage judged it E (environment assumption missing); agent A13
declined to add the assumption, citing RT-4.1-05 and D-013. By the user's decision the check and the environment
stay as they are, and the question is left to the G4 reviewer ([G4_REVIEW_REQUEST.md](G4_REVIEW_REQUEST.md)).

**Other formal results.**
- CHK-011 (`d_error` for each kind of request) did not finish within 600 s per task: nothing concluded.
- CHK-006 and CHK-007 are simulation-only: their checker samples at the falling clock edge, which the one-clock
  formal model cannot express. Before this phase that gave a tool ERROR; see the fixes below.

**The 3 mutants formal finds different.** The miter of `nnc mutate-equiv` leaves the inputs free after reset; it
does not apply `verif/formal/nnc_env.sv`. All three differences are in cases the specification decisions leave
unchecked:
- M01 (`prim_mubi_pkg.sv:72`): the response to an instruction fetch (`i_a_instr` = 1) changes; D-011 does not
  check `d_error` for instruction fetches.
- M14 (`tlul_adapter_reg.sv:221`): `d_data` of an error response changes; D-015 checks `d_data` only for a Get
  without error.
- M19 (`prim_alert_sender.sv:223`): after requests with a command integrity error, the timing of later alert
  pulses changes; D-010 asks only for a first pulse within 16 cycles and then at least one every 32 cycles.
- M12 (`prim_diff_decode.sv:234`, reset condition inverted) is not checked: the mutant has a reset branch of the
  wrong polarity for its sensitivity list, which the elaborator rejects.

The 9 rules below 85 % per-requirement mutation score (alert handler AH-T1.3.2-01..03, CP-T1.9.1-04, RT-4.2-03,
RT-5-02, RT-5-05, RT-8-16, RT-T6.3-01) are attributed mostly to these alert and integrity survivors.

**Faults of the flow found and fixed here** (each with a unit test):
1. **Formal could not read the OpenTitan RTL.** Yosys' own parser rejects parts of it. Formal now reads the DUT
   with the yosys-slang plugin (config `formal_frontend=slang`, `formal_defines=SYNTHESIS`); the checkers are still
   read by Yosys. Simulation got include directories for `.svh` files.
2. **A checker that samples at the falling clock edge made formal report ERROR.** In a one-clock formal model such
   a checker is now marked simulation-only (`formal.falling_clock`), like a checker with `$time`.
3. **The prompts of A13 (formal environment) and A6 (cover points) dropped the `condition` of each rule.** A13
   therefore never saw "in the first cycle after release" of D-016 and wrote no assumption for it. Both prompts
   now show `WHEN <condition>` (prompt versions env-v2, cov-v2).
4. **`mutate-equiv` used Yosys' parser** and reported ERROR on every OpenTitan mutant. It now uses the formal
   frontend and macros of the design.
5. **`mutate-equiv` lost all results when interrupted** and ran BMC before PDR (BMC of M19 timed out after 15 min;
   PDR found the difference in 7 s). It now writes `work/mutation.json` after each mutant, keeps conclusions of a
   run with the same depth and frontend (`--redo` checks all again), runs PDR first and BMC only when PDR
   concluded nothing, and keeps the PDR trace.
6. The report shows the equivalence summary next to the mutation score.

**CI.** ot_rv_timer is added to the kit, kit-configs and formal jobs.

## 10. Do repeated agent runs agree? (phase 18, uart_lite, 2026-11-21)

Three fresh copies of uart_lite ran ingest, extraction (A1), review (A2), questions (A3) and the contract (A4)
with the same specification, document configuration and models, an empty `work/` and no cache
(`nnc flow <copy> --from ingest --to contract --unreviewed`). The committed `designs/uart_lite` is the fourth run.
Each run picks its own rule and check IDs, so `nnc stability` (nnc/stability.py) compares the specification
sentences the rules cite. Files: [designs/uart_lite/stability/](../designs/uart_lite/stability/README.md).
Cost of the three runs: about US$5.2.

| Measure (Jaccard index unless noted) | Range over the 6 pairs |
|---|---|
| Normative sentences kept | 0.91–0.95 |
| Normative sentences covered by a check | 0.86–0.93 |
| All cited sentences kept | 0.77–0.90 |
| Kept rules whose sentence set is a rule in the other run (fraction) | 0.81–0.93 |
| Same strongest MUST/SHOULD/MAY per sentence (fraction) | 0.99–1.00 |
| Rules / checks per run | 134–154 rules, 32–34 checks (12–13 assertions) |

Each run keeps 105 to 108 of the 114 normative sentences, and the runs agree on more than 9 in 10. Agreement on
which sentences a check covers is lower (86 to 92 normative sentences per run). About one kept rule in six groups
the sentences differently. The strength of a sentence almost never differs. This variation is why the rules (G1)
and the contract (G2) are reviewed for each run; the cache makes a re-run of the same run reproducible, not a new
run identical.

## 11. A second OpenTitan IP: gpio, with four configurations (phase 18, 2026-11-21)

**Why.** rv_timer (§9) is one industrial design with one configuration. gpio checks whether its results repeat
on a second OpenTitan IP that has parameters, so that the run set, formal per configuration and the slang
frontend are exercised together.

**Set-up** (`designs/ot_gpio/`, Apache-2.0, see its `NOTICE.md`):
- RTL: the 45 OpenTitan files of `hw/top_earlgrey/ip_autogen/gpio` and what it uses (commit ee811654, 18 891
  lines), unchanged, plus a 150-line wrapper `ot_gpio_nnc.sv` written here (flat ports, request integrity,
  response integrity check, alert receiver, as for rv_timer).
- Golden sources: the gpio documentation (1 169 lines with the wrapper's integration part and the decisions) and
  the same four standards as rv_timer.
- Run set: the two parameters `GpioAsyncOn` and `GpioAsHwStrapsEn`, all four combinations: base (1, 1; seeds 1
  and 2), sync_off (0, 1), straps_off (1, 0), min (0, 0).

| Step | Result |
|---|---|
| `spec-lint` (A18) | 19 gaps (10 high, 7 medium, 2 low), US$1.17 |
| Rules after review (G1) | 268 of 320 (45 rejected, 7 merged, 41 fixed); 8 open questions, answered with decisions **D-001..D-022** (spec §10), made from the documents only |
| Contract (G2) | 38 checks (13 assertions, 25 tests) over 188 rules; 80 rules not verifiable by simulation |
| Test code | one Python error in the generated tests, repaired by A7 in one round (no RTL, no failed check shown) |
| Simulation failures | 3 assertions (CHK-006, CHK-008, CHK-011), all judged B (verification wrong); fixed by A17 in one round |
| Formal counterexamples | 1 (CHK-003), judged B and fixed by A17 in a second round |
| Agent cost, whole flow | US$17.90 in 70 calls (A7 US$4.01, A17 US$2.69, A9 US$2.29) |

**Results** (`work/report.md`, `formal.md`, `mutation.json`):

| | ot_gpio |
|---|---|
| Tests | 26/26, in all 5 runs |
| Assertions failing | 0/13 |
| Rules VERIFIED / not verifiable by simulation | 188 / 80 |
| Functional coverage | 36/40 cover points |
| Code coverage: line, toggle | 52.5 %, 84.0 % |
| Formal (depth 32, 4 configurations): PROVEN / TIMEOUT / simulation-only / CEX | 10 / 1 (CHK-013) / 2 (CHK-010, CHK-011) / **0** |
| Mutation | 58.3 % (21/36); of the 15 survivors formal proves 9 equivalent, 4 differ, 2 not checked: **77.8 %** without the equivalent ones |
| Hand fixes | 0 |

CHK-009 (strap outputs) is VACUOUS in straps_off and min, as it must be: with `GpioAsHwStrapsEn` = 0 the strap
outputs are not checked (D-009). It is PROVEN in the two configurations with straps.

The 13 rules below 85 % per-requirement mutation score (alert handler AH-T1.3.2-01 and -03, GP-10-07, GP-10-08,
GP-10-19, GP-3-01, GP-4.1-01, GP-4.1-03, GP-5-02, GP-5-05, GP-T2.2-05, GP-T3.2.3-03, GP-T5.17-01) are attributed
mostly to the alert, integrity and filter survivors below.

**The verification faults, all in the verification, none in the RTL.**
- CHK-006 assumed that a write to `INTR_ENABLE` takes effect at its response. The RTL applies it at the request,
  so under D-channel back-pressure a bit being enabled showed early. The checker now skips only bits that an
  outstanding write sets from 0 to 1 (D-018, D-004); bits that stay 0 are still checked on every edge.
- CHK-008 fired at time 0, before any reset had been asserted, and its hit counter could never count. It now
  starts at the first reset assertion.
- CHK-011 (stimulus self-check) found that, with `GpioAsyncOn` = 0, the tests drove inputs after the falling
  edge while the plan asks for changes just after the rising edge. The tests were changed. The checker also
  compared only 49 of 121 input bits (a truncated vector); it now compares all of them, which strengthens it.
- CHK-003 (formal) counted a request with a command integrity error as an alert cause only once accepted. The
  stock OpenTitan integrity check raises the alert while the request is presented (`a_valid` = 1), which no
  rule forbids. The checker now counts the request from `a_valid`.

**The 4 mutants formal finds different** (the miter leaves inputs free and does not apply `nnc_env.sv`):
- M12 (`prim_mubi_pkg.sv:72`): the response to an instruction fetch; D-011 does not check it (as M01 of
  rv_timer).
- M15 (`tlul_adapter_reg.sv:219`, reset value of `error_q`): `o_d_error` in the first cycle after reset, when no
  response is valid; D-015 checks `d_error` only on a response.
- M02 (`prim_filter_ctr.sv:59`, reset value of the filter): `o_straps_data` six cycles after reset; D-008
  samples straps only after `i_gpio` has been stable for 24 cycles, and D-003 leaves the input path unchecked in
  the first 20 cycles.
- M21 (`prim_alert_receiver.sv:190`): the timing of later alert pulses; D-010 and D-017 bound the pulses but do
  not fix their cycle.
- M30 and M33 (reset condition inverted) are not checked, for the same reason as M12 of rv_timer.

These explanations are read from the counterexample summary (output and step) and the mutated line; the traces
are in `work/mutation_equiv/`.

**Fault of the flow found and fixed** (with a unit test): with the slang frontend, formal elaborated the DUT
with its default parameters and the formal top then failed to set them ("does not have a parameter named
'GpioAsHwStrapsEn'"), so every check was ERROR. rv_timer has no parameter and never reached this path. The
configuration's parameters now go to `read_slang -G`, as `mutate-equiv` already did.

**CI.** ot_gpio is added to the kit and kit-configs jobs, and to formal with one job per configuration.

### 11.1 Did the rv_timer results repeat?

| | ot_rv_timer (§9) | ot_gpio |
|---|---|---|
| OpenTitan RTL | 44 files, 8 635 lines | 45 files, 18 891 lines |
| Configurations, runs | 1, 2 | 4, 5 |
| Gaps found by spec-lint; decisions | 20; D-001..D-020 | 19; D-001..D-022 |
| Rules kept / checks (assertions) | 228 / 35 (13) | 268 / 38 (13) |
| Verification faults (B) found by simulation, by formal | 4, 2 | 3, 1 |
| Faults judged A (RTL wrong) | 0 | 0 |
| Formal: PROVEN, CEX left | 7, 1 (stimulus question for G4) | 10, 0 |
| Mutation score; without proven-equivalent mutants | 58.3 %; 84.0 % | 58.3 %; 77.8 % |
| Survivors that differ, all in a case a decision leaves unchecked | 3 | 4 |
| Hand fixes | 0 | 0 |
| Agent cost | US$22.09 | US$17.90 |

The pattern repeats. The RTL is never blamed. Every failure is a verification fault that the agents correct
without changing an expected value. The surviving differences fall where the specification decisions chose not
to check. No hand fix was needed. Formal went further on gpio (no counterexample left).

### 11.2 Comparison with OpenTitan's own test benches (public numbers only)

OpenTitan verifies both IPs with UVM test benches. They are not copied here; only the public nightly report
and the testplans at commit ee811654 are used.

| | gpio | rv_timer |
|---|---|---|
| OpenTitan stage | gpio 1.0.0 D3/V3 (the ip_autogen 2.0.0 is D1/V1) | 1.1.0 D3/V3 |
| UVM DV code (`dv/`, `.sv`/`.svh`) | 25 files, 3 158 lines | 19 files, 1 574 lines |
| Testplan | 11 testpoints + 5 common testplans | 8 testpoints + 5 common testplans |
| Nightly report (2025-02-08, VCS, rev 9f20940d49) | 939/970 tests (96.8 %); all failures in `stress_all_with_rand_reset` | 578/620 (93.2 %) |
| Their coverage: score, line, condition, toggle, branch, assertion, functional | 99.63, 99.06, 99.24, 100.00, 99.80, 99.68, 99.99 | 99.61, 99.36, 98.73, 100.00, 100.00, 100.00, 99.55 |
| This flow: tests, assertions | 26 tests, 13 assertions in 5 runs | 23 tests, 13 assertions in 2 runs |
| This flow, phase 18 (every instrumented point): line, toggle, functional | 52.5 %, 84.0 %, 36/40 | 24.2 %, 80.3 %, 38/39 |
| This flow, phase 19 (design scope, §12): line, block, toggle, functional | 96.5 %, 93.6 %, 87.5 %, 38/40 | 92.3 %, 87.8 %, 83.1 %, 38/39 |
| This flow, phase 19, without OpenTitan's pre-verified primitives (as their cover.cfg): line, block, toggle | 97.0 %, 96.8 %, 89.2 % | 92.8 %, 91.7 %, 85.1 % |

Sources: https://reports.opentitan.org/hw/ip/gpio/dv/latest/report.html and
https://reports.opentitan.org/hw/ip/rv_timer/dv/latest/report.html (a report under the
`top_earlgrey/ip_autogen/gpio` path does not exist); the testplans `gpio_testplan.hjson` and
`rv_timer_testplan.hjson`.

The two sides do not measure the same thing, so the table is not a ranking:
- OpenTitan's coverage is collected on the IP and its own register block, with exclusions they reviewed. In
  phase 18, code coverage here counted every instrumented point, including whole packages of which the IP uses a
  few functions; that is why line coverage was low. Phase 19 counts the elaborated design only (§12), with no
  hand exclusion. Functional coverage counts
  different cover points (theirs from the testplan, ours from the specification rules).
- Their report is from 2025-02-08 and for `hw/ip/gpio`, not for the ip_autogen gpio at ee811654 verified here.
- They report no mutation score and no formal proof of their checks; this flow has no CSR randomisation,
  stress-with-reset or long random regressions.

What the comparison shows: a mature hand-written test bench reaches about 99 % on every metric after years of
work. This flow, from the documents alone and in about a day per IP, reaches every planned check and proves most
assertions, but leaves the coverage gaps that its line and toggle numbers show. A person deciding G4 should read
these numbers as a first pass, not as sign-off quality.

## 12. Coverage of the elaborated design, and closure (phase 19, 2026-11-21)

The sign-off areas the flow covers, and the ones it leaves out, are discussed in
[SIGNOFF_SCOPE.md](SIGNOFF_SCOPE.md). This section measures what changed for code coverage.

**Why the OpenTitan numbers were low.** Verilator instruments every function of every imported package, called or
not. OpenTitan's `prim_secded_pkg` holds 8 136 of gpio's 21 352 line points and 20 848 of its 31 906 expression
points, and the design calls none of its functions: it uses the separate `prim_secded_inv_*` modules. Toggle
coverage also counted bits that cannot change, such as the zero-extended upper bits of sync_fifo's pointer
arithmetic.

**What the flow does now** (nnc/coverage.py, nnc/sim.py). Every simulation run also elaborates the DUT alone, with
that run's parameters and macros, in two tools:
- `verilator --json-only`: the elaborated tree keeps only the package functions the design calls;
- Yosys `proc; flatten; opt` (the formal frontend): the netlist shows the bits that constant propagation proves
  constant.

The following points are left out of every denominator:
- never-executed points of package code outside the kept functions;
- toggles of constant bits.

Each row of the report says how many points were left out, and gives the count over all points. There is no hand
exclusion. Safeguards:
- an executed point that the scope would leave out is counted (`scope_conflicts`);
- when the simulator records a toggle on a bit that the netlist calls constant, the signal is counted whole. This
  happened on gpio's `prim_onehot_check` trees (`or_tree`, `and_tree`): the RTL ties the leaves above
  `OneHotWidth` = 114 to 0, yet Verilator reports toggles on them;
- the 0->1 toggle of a constant-1 bit at time zero is left out: Verilator starts every variable at 0.

`scope_conflicts` is 0 on all 13 designs. The outcomes (tests, failing tests and assertions, never-hit and
NOT_VERIFIABLE checks) of all 13 reruns equal the committed ones. The only difference is gpio's two new closure
tests.

| Design | line | block | toggle | expression | functional | Left out by the scope |
|---|---|---|---|---|---|---|
| ahb2axi_bridge | 86.0 | 77.1 | 65.7 → **75.9** | 71.9 | 90.0 | toggle 4872 |
| apb_tlul_bridge | 96.0 | 95.6 | 95.9 → **99.8** | 100.0 | 100.0 | toggle 88 |
| async_apb_bridge | 91.9 | 88.8 | 98.6 | 74.8 | 97.5 | - |
| async_gray_fifo | 99.1 | 95.7 | 99.5 | 98.0 | 100.0 | - |
| axi2apb_bridge | 98.9 | 95.9 | 74.8 → **86.4** (closure) | 96.2 | 97.5 | toggle 24 |
| axil_regfile | 100.0 | 100.0 | 95.8 → **96.7** | 95.7 | 100.0 | toggle 64 |
| gen_apb_tlul_bridge | 95.1 | 95.7 | 95.6 → **99.8** | 100.0 | 100.0 | toggle 88 |
| gen_sync_fifo | 97.3 | 94.4 | 99.5 → **99.7** | 97.4 | 100.0 | toggle 4 |
| ot_gpio | 52.5 → **96.5** | 44.5 → **93.6** | 84.0 → **87.5** | 20.6 → **64.9** | 90.0 → **95.0** | line 9736, block 1288, expression 21732, toggle 3328 |
| ot_rv_timer | 24.2 → **92.3** | 29.6 → **87.8** | 80.3 → **83.1** | 7.8 → **61.0** | 97.4 | line 2434, block 322, expression 5433, toggle 408 |
| spi_master | 94.8 | 93.8 | 95.2 | 98.2 | 94.9 | - |
| sync_fifo | 99.2 | 97.3 | 70.6 → **87.7** | 92.8 | 100.0 | toggle 448 |
| uart_lite | 98.7 | 97.3 | 100.0 | 100.0 | 97.5 | - |

Percent, before (phase 18, every instrumented point) → after. Source: each design's `work/results.json`
(`coverage.design_scope`). The two asynchronous designs show no constant bits.

**Pre-verified modules.** OpenTitan leaves its pre-verified primitives out of its coverage model (cover.cfg:
`prim_alert_sender`, `prim_alert_receiver`, `prim_onehot_check`, the `prim_secded_inv_*` coders and others). Design
config `coverage_preverified` holds that list for the two OpenTitan designs. The report then adds the coverage
without their subtrees, next to the coverage of the whole design:

| | line | block | toggle | expression |
|---|---|---|---|---|
| gpio, without 7 instances | 97.0 | 96.8 | 89.2 | 69.4 |
| rv_timer, without 7 instances | 92.8 | 91.7 | 85.1 | 83.7 |

**Closure by agents (A10/A11).**

*gpio, functional.* 90.0 % → 95.0 % (38/40). Two tests were added in `verif/tests/test_ot_gpio_cov1.py`:
PutPartialData full-word writes, and mask/size combinations. All 28 tests pass in all 5 runs, and G3 was approved
again on delegation. The two points left are COVP-012 (A handshakes in consecutive cycles) and COVP-013 (two
outstanding requests). The agents claim both unreachable: the register adapter holds `a_ready` low until the
pending response has been taken. That matches OpenTitan's single-outstanding `tlul_adapter_reg`. The points still
count; the claim is in `work/coverage_functional.md` for the reviewer.

*gpio, toggle.* No test added. There were 18 unreachable claims, in `work/coverage.md`:
- RACL disabled;
- wrapper-tied `a_user` fields;
- `d_opcode` bits 1-2;
- the one-hot error tree;
- read-only write enables;
- address bits ≥ 10. These are excluded only by decision D-012 (tests use offsets below 0x400), a decision the
  reviewer should look at.

Several of these signals are constant struct fields. The constant-bit scope does not reach them yet, because
Verilator names a struct member (`tl_i.a_user.rsvd`) where Yosys has one packed net.

*axi2apb_bridge, toggle.* 75.1 % (after the scope) → 86.4 % for a target of 85 %, met in one round. Six tests were added (`verif/tests/test_axi2apb_bridge_cov1.py`). They had never been run before: reads and writes in the upper half of the address space, unsupported AxSIZE with long bursts, and 4-KiB-crossing bursts at the top of the space. Address bits 16 and up had never toggled, so a fault on them would have gone unnoticed. 21/21 tests pass, and G3 was approved again on delegation. Most of what is left is the upper bits of size and wrap arithmetic, which are unreachable.

**Random initial values (step 19.4, 2026-11-24).** A run-set configuration can set `"x_init": "random"`:
Verilator `--x-assign unique --x-initial unique` with `+verilator+rand+reset+2`, seeded by the run seed, so every
variable without a reset starts at a random value instead of 0. A fault that zero initialisation hides (a flop
without a reset whose value reaches an output) then shows.

The first trial failed assertions at time 0 on most designs. These were faults of the harness, not of the
designs. Three fixes:
- *Inputs at time 0.* Under x_init the inputs also start at random levels, so the DUT saw stimulus that no test
  gave. The cocotb helpers now drive every input to 0 when the tests are imported (time 0).
- *Checkers at the first clock edge.* A synchronous reset (or an asynchronous one that saw no edge) takes effect
  only at the first rising edge, and a checker samples that edge with the values from before it. Under x_init the
  test bench top turns the concurrent checkers off (`$assertoff`) until every clock has had its first rising edge
  after time 0 (at most 1 µs). Builds without x_init and formal do not contain this block.
- *The reset edge.* A reset that starts at a random level gave a falling edge at time 0 to one copy of the net and
  not to another: Verilator gives the port of a module it does not inline its own initial value. On
  async_apb_bridge the procedural CHK-010 check (`always @(negedge i_rst_n_slv) #1 ...`) saw the reset while the
  flops did not, and found psel, penable and paddr still random 1 ns later. Under x_init the resets are now
  inactive at time 0 and asserted at 1 ps, when every net has settled, so every flop sees one real edge, as at
  power-up.

An earlier version of this section said that gen_sync_fifo fails `test_chk_024_sw_reset_full_and_rerequest`
under x_init. That was wrong: the zero-initialised record fails it at the same time (189217 ns, triage B/C on
the CHK-008 question).

Trial with the final harness: the first configuration of every design, seeds 1 and 2, on scratch copies.

| Result | Designs |
|---|---|
| Same failing tests and checks as the record | sync_fifo, uart_lite, axil_regfile, spi_master, apb_tlul_bridge, gen_apb_tlul_bridge, gen_sync_fifo, axi2apb_bridge, async_gray_fifo, async_apb_bridge, ot_gpio, ot_rv_timer, c_uart, c_pcpi_div |
| One more failing check | ahb2axi_bridge: CHK-012 (AXI size and alignment), first at 950 ns |

ahb2axi_bridge, CHK-012. The record already fails 20 of 21 tests. One of its triaged faults (A_rtl_wrong, §9 of
`work/triage.md`): during the AHB/FSM desync, `reg_burst_fallback` flips and AWADDR/AWSIZE come from the burst
table `reg_burst_addr`/`reg_burst_size`. The table has no reset, only its indices do. With zero initial values an
entry never written reads as address 0, size 0, which is aligned; with random values it is random, and CHK-012
fails. So this is most likely a new symptom of a fault already recorded, not a new fault. No waveform confirms it,
and no triage was run for it then. The triage of step 23.6 (§15) confirms the recorded fault.

Recorded: uart_lite has a fifth run-set configuration `xrand` (CFG-BASE with x_init, seeds 1 and 2): 9 runs,
20/20 tests, 13 assertions, 0 failures. Every run set counts a configuration as its own copy of the design, so the
coverage denominators grow (line 596 → 745 points) and the percentages stay the same. All 67 recorded runs of the
15 designs give the same results with the new harness (`nnc demo --all-runs`).

**Formal unreachability of toggle points (step 19.5, 2026-11-24).** `nnc sim --unr` (nnc/unr.py) takes every toggle bit that the simulation never brought back from 1 to 0 and asks
SymbiYosys (`abc --keep-going pdr`, one result per assertion) whether the bit can change after the first reset:
- the DUT is the flattened Yosys netlist of each run-set configuration (its parameters and macros);
- every input is free, the reset included, so later resets and any stimulus are covered;
- the first reset is held for two rising edges of every clock; then the value of each bit is captured and the
  assertion is "the bit keeps that value".

A PROVEN bit leaves the toggle denominator, both of its points; it must be PROVEN in every configuration of the
run set. A counterexample or a time limit leaves it counted. If a later simulation records a 1->0 on a proven bit,
its signal counts whole again. Results are in `work/unr.json` (keyed by RTL hash, parameters and macros) and
`work/unr.md`, and every later `nnc sim` applies them without running the prover.

**Soundness checks, and the bug they found.** The first version gave vacuous proofs. With one clock the model
uses a single global clock (`multiclock off`), in which the clock input cannot be read as data, so the counter of
reset edges never counted and the capture never happened: every assertion held trivially. It "proved" that
c_uart's free input `prescale` was constant. Two assertions now go into every task, and a task concludes nothing
unless both FAIL:
- the guard `assert(!armed)`: the checked phase must be reachable;
- the control: the same property on a flop output that the simulation toggled at least 4 times each way
  (for example `uart_rx_inst.bit_cnt[0]`, `u_gpio.u_reg.u_reg_if.outstanding_q[0]`). A model in which such a bit
  cannot change does not match the simulation. An input or a clock is not accepted as the control: it changes
  freely and shows nothing about the state.

With these, c_uart's 48 bits are counterexamples, not proofs. Records of the earlier versions are discarded
(record version 3). All tasks of all designs are conclusive (no task with a passing guard or control).

| Design | Candidates (bits) | PROVEN | Counterexample | No result | Not in netlist (signals) | Toggle before → after |
|---|---|---|---|---|---|---|
| ahb2axi_bridge | 996 | 513 | 32 | 26 | 46 | 75.9 → **84.1** |
| apb_tlul_bridge | 2 | 2 | 0 | 0 | 0 | 99.8 → **100.0** |
| async_apb_bridge | - | - | - | - | - | 98.6 (no netlist) |
| async_gray_fifo | - | - | - | - | - | 99.5 (no netlist) |
| axi2apb_bridge | 359 | 359 | 0 | 0 | 0 | 86.4 → **100.0** |
| axil_regfile | 23 | 5 | 0 | 0 | 1 | 96.7 → **97.2** |
| c_uart | 60 | 0 | 48 | 0 | 0 | 67.6 (unchanged; 74.1 in the 0.7.0 record, see below) |
| gen_apb_tlul_bridge | 2 | 2 | 0 | 0 | 0 | 99.8 → **100.0** |
| gen_sync_fifo | 2 | 2 | 0 | 0 | 0 | 99.7 → **100.0** |
| ot_gpio | 1185 | 237 | 23 | 0 | 128 | 87.5 → **89.6** |
| ot_rv_timer | 962 | 56 | 25 | 0 | 129 | 83.1 → **83.9** |
| spi_master | 0 | - | - | - | - | 95.2 |
| sync_fifo | 114 | 114 | 0 | 0 | 0 | 87.7 → **100.0** |

Counts per configuration (ahb2axi: the smallest over its 3 configurations; the others are equal in every
configuration). The 12 input bits of c_uart are free in the model and are not checked. Source: `work/unr.json`.

What was proven is what one expects of these designs: the upper bits of sizes and masks computed in 32 bits
(`w_ar_size_bytes[8:31]`, sync_fifo's `w_occ_nxt[4:31]`), word-aligned APB addresses (`o_apb_paddr[1:0]`),
response bit 0 that the bridge never sets, gpio's `d_opcode` bits 1-2. Some hit counts go down too: the 0->1
point of a proven bit at reset is left out with the bit, as for constant bits.

The tests, the failing tests and assertions, and the checks of all 13 designs are the same as the record. c_uart
was recorded (0.7.0) before the 19.4 harness changes; rerun without the UNR record it gives 67.6 % (250/370), so the
drop from 74.1 % comes from the harness at time 0, not from this step. Its 3 failing tests and their messages
are unchanged.

Limits:
- signals that Verilator names per struct field (`tl_h2d.a_address`) have no net of that name in Yosys, so they
  are "not in netlist" (gpio 128, rv_timer 129 signals);
- async_gray_fifo and async_apb_bridge: Yosys cannot read their simulation-only synchronizer model
  (`cell_sync.sv:124`), so they have no result;
- the method trusts that Yosys and Verilator give the same meaning to the RTL; the control is the check of that,
  on one bit per task;
- only toggle points. Branches (line/block) under a constant condition are not done yet.

**Still open.** These are phase 23 of the ROADMAP, done in §15.
- Struct fields: both constant bits and UNR.
- UNR for the two asynchronous designs, and for line/block points.
- x_init in the run sets of the other designs.

## 13. Clock and reset domain crossings (phase 20, 2026-11-21)

`nnc cdc <ip>` (nnc/cdc.py) checks RR-33 by structure, on the flattened Yosys netlist of each parameter set of the
run set:
- each flop gets the domain of its clock;
- the cone of its data, enable and synchronous reset gives its sources;
- a source of another domain is a crossing, classified as in the table below;
- asynchronous resets from another domain are listed.

Declared asynchronous inputs come from the contract's `domain` column or from config `cdc_async_inputs`.

| Design | Configurations | Verdict | Crossings (bits, summed over configurations) |
|---|---|---|---|
| async_gray_fifo | 6 | review | SYNC 12, SYNC_MULTIBIT 44, QUALIFIED 161 |
| async_apb_bridge | 7 | review | SYNC 16, QUALIFIED 677 |
| ot_gpio | 4 | clean | SYNC 64 (`i_gpio` with `GpioAsyncOn=1`; none with `GpioAsyncOn=0`) |
| uart_lite | 4 | clean | SYNC 4 (`i_rxd`) |
| the 9 others | 1-4 | clean | no crossing (one clock, or synchronous clocks) |

Source: `work/cdc.json` of each design (`work/cdc.md` lists every row).

How to read the two reviews:
- **async_gray_fifo.** The gray pointers cross bit by bit into the other domain: that is SYNC_MULTIBIT, correct
  only because a gray code changes one bit at a time. The read data is captured under control of the synchronized
  write pointer (`w_wgray_s`): that is QUALIFIED.
- **async_apb_bridge.** The request and response payloads are captured under control of the synchronized
  request and acknowledge (`w_req_s`, `w_ack_s`): QUALIFIED. The handshake bits themselves are SYNC.

That one bit changes at a time, and that a payload is stable while it is captured, are protocol properties. This
check does not prove them; formal and simulation do.

**Does the check find faults?** In a copy of async_gray_fifo, two faults were put into the 2-FF synchronizer
cell, and both were reported as violations:

| Fault | Result |
|---|---|
| output taken from the first stage | FIRST_STAGE_READ on 4 synchronizers, verdict violations |
| no synchronizer (`Q = D`) | 314 UNSYNC bits, verdict violations |

Unit tests (tests/test_cdc.py) cover each class on hand-made netlists, including raw use of a value that is also
synchronized (UNSYNC). CI job `cdc` reruns the check on all 13 designs and compares it with `work/cdc.json`.

**Limits.**
- QUALIFIED is a heuristic: some flop of the cone derives from a synchronizer of the destination domain. It is not
  a proof that the control actually gates the capture. It therefore stays a review item.
- Clocks that the contract calls synchronous are one domain.
- No glitch analysis of combinational logic before a synchronizer: such logic is reported as UNSYNC, because the
  first stage must take the source directly.

## 14. Blind runs on modules the flow was not written for (phase 21.6, 2026-11-23)

The question: with only the documentation a user of the module has, and no hand edit, how far do the agents get?
Three modules of the input corpus (`nnc corpus`), chosen for how much their documentation says. Every
intervention is recorded in `designs/<ip>/work/blind_run.md`. Gates G1-G3 were approved as produced, on the
owner's delegation; open questions were left open. Defaults were kept (formal off, no coverage target).

| Design | Specification given | Rules kept | Checks | Tests | Mutation | Agent cost |
|---|---|---|---|---|---|---|
| c_pcpi_div (`picorv32_pcpi_div`) | PCPI part of the README + RISC-V M extension and RV32M encodings | 23 (7 verified, 16 not for this core) | 9/9 PASS | 7/7 | 100 % (12/12) | US$2.66 |
| c_uart (`uart`, verilog-uart) | the README | 6 | 6/11 PASS | 5/8 | 83.3 % (10/12) | US$2.70 |
| c_axil_ram (`axil_ram`, verilog-axi) | the README sections of the module | 0 | — | — | — | US$0.04 |

What it shows:
- **Where the documentation specifies, the flow verifies.** For the division core the rules of the RISC-V standard
  were extracted, turned into directed and random tests against a reference model, and all passed, with 100 %
  structural coverage and every mutant killed. One test fault (an instruction issued one cycle early) was judged B
  by triage and fixed by A17 without the RTL.
- **Where the documentation is ambiguous, the flow says so.** For the UART the README says that on an overrun "the
  word is discarded" without saying which. The RTL replaces the waiting word on `m_axis` while it is not
  accepted, which breaks the AXI4-Stream rule that the contract checks. Triage judged all four failures C; the
  owner kept them open for the G4 reviewer. The contract also states openly that it assumes an 8N1 frame, which
  the README does not give.
- **Where the documentation says nothing, the flow stops.** The verilog-axi README lists the signals of
  `axil_ram` but states no behaviour: 0 normative sentences, 0 rules. The flow invents nothing; the module needs
  the AXI4-Lite specification as a standard document.

Faults of the flow found while preparing and running them, fixed before the runs continued:
- synchronous resets were never found by the intake (no `opt_dff`), so the contract would have had no reset;
- AsciiDoc specifications (the RISC-V manual) could not be read;
- setext headings (picorv32's README) were not sections;
- `nnc intake` of an adapted design checked the original README for a port table instead of the interface
  document the contract reads.

The corpus was run again after the `opt_dff` change: the same verdicts and smoke results for all 238 modules.

Total agent cost of the three runs: US$5.40.

## 15. The rest of the coverage work: struct fields, cut models, branches, x_init everywhere (phase 23, 2026-11-24)

Phase 19.5 left four things open (end of §12). Steps 23.1 to 23.4 close them. No point was left out by hand: a
point leaves a metric only when SymbiYosys PROVES it unreachable in every configuration of the run set.

**23.1, struct fields.** Verilator names a toggle point per field of a packed struct (`tl_i.a_address[3]`),
Yosys has one net (`tl_i`). `coverage.struct_fields` reads the layout of every struct variable from
`verilator --json-only`, so each field point is matched to its bit of the net, for constant bits and for UNR.
Instances that Verilator merges over a generate loop (`gen_filter[*].u_filter`) count as constant, or PROVEN, only
if every instance in the netlist is. On gpio 2 280 more constant points are matched, and no simulated toggle
contradicts any of them.

**23.2, designs with a simulation-only model.** The synchronizer model of async_gray_fifo and async_apb_bridge
cannot be read by Yosys. Config `unr_cut` names those modules: the proofs read the RTL with the synthesis macros
and make every output of the cut modules free (`cutpoint -blackbox`). A free output allows every behaviour of
every model, the simulated one included, so a PROVEN bit also holds in simulation. `unr.cut_check` refuses a cut
when a file that tests one of these macros defines a module that is not cut. Result: async_gray_fifo 35 bits
PROVEN in all 10 configurations (toggle 99.5 → 99.9 %). async_apb_bridge has no candidate left: its only uncovered
signal is in the cut model.

**23.4, x_init in every run set.** The 14 other designs now have a configuration `xrand` (`"x_init": "random"`, seed 1), so all 15 run sets have
one (uart_lite's, from §12, runs seeds 1 and 2).
Its tests and assertions count; its coverage is not merged, because its toggles before the first reset are not
activity of the design and would cover the points that 19.1 and 19.5 leave out. Checked against the record:
- the old configurations give the same tests, assertions and checks;
- the `xrand` runs add no failing test;
- one assertion fails only under `xrand`: ahb2axi_bridge CHK-012, already reported in §12 (step 23.6).

**23.3, branches never executed.** Each IF branch or case item with no hit gets a marker in an instrumented copy of
the RTL (`nnc/unrbranch.py`):
- in a clocked block, a flop that toggles when the branch runs;
- in a combinational block, a signal set to 1 there.

The copy is used only when Verilator shows every marker as the first statement of its branch. Each marker is then
proved constant after the first reset, as a toggle bit is. A branch PROVEN in every configuration leaves the block
metric, and its lines leave the line metric when no other point covers them. If a simulation ever executes a
PROVEN branch, the result counts it (`branches_executed`); it is 0 on every design.

**Controls on more than one signal.** In spi_master's `min` configuration the control flop of the first version
was constant, so every task was vacuous. A task now has up to 4 control assertions on flops of different
signals, and it concludes only if the guard and at least one control FAIL.

**Closure without the pre-verified modules.** When a design declares `coverage_preverified` (rv_timer: the `prim_*`
modules, as OpenTitan's `cover.cfg` does), `nnc cover` takes its target and its uncovered points from the
coverage without those modules. Before this, the list given to the analyst (capped at 200 groups) held only
`prim_*` expression points.

Results with `nnc sim --unr`, all configurations, 12 parallel jobs. Before = release 0.8.0.

| Design | Toggle bits PROVEN | Branches PROVEN | Toggle % | Block % | Line % |
|---|---|---|---|---|---|
| ahb2axi_bridge | 656 | 102 | 84.1 → **91.5** | 77.1 → **97.1** | 86.0 → **91.3** |
| apb_tlul_bridge | 2 | 2 | 100.0 | 95.6 → **100.0** | 96.0 → **97.0** |
| async_apb_bridge | 0 | 0 | 98.6 | 88.8 | 91.9 |
| async_gray_fifo | 35 | 2 | 99.5 → **99.9** | 95.7 → **97.8** | 99.1 → **99.8** |
| axi2apb_bridge | 359 | 6 | 100.0 | 95.9 → **98.6** | 98.9 → **100.0** |
| axil_regfile | 5 | 0 | 97.2 → **99.2** | 100.0 | 100.0 |
| c_uart | 0 | 2 | 67.6 | 93.2 → **97.6** | 97.6 |
| gen_apb_tlul_bridge | 2 | 2 | 100.0 | 95.7 → **100.0** | 95.1 → **97.0** |
| gen_sync_fifo | 2 | 3 | 100.0 | 94.4 → **100.0** | 97.3 → **100.0** |
| ot_gpio | 297 | 17 | 89.6 → **93.9** | 93.6 → **99.5** | 96.5 → **97.3** |
| ot_rv_timer | 116 | 19 | 83.9 → **90.0** | 87.8 → **99.3** | 92.3 → **94.9** |
| spi_master | 0 | 2 | 95.2 | 93.8 → **97.8** | 94.8 → **98.6** |
| sync_fifo | 114 | 2 | 100.0 | 97.3 → **100.0** | 99.2 → **100.0** |

Source: `work/results.json` (`coverage.unr`, `coverage.design_scope.proven_unreachable`) and `work/unr.md`. The
tests, failing tests, assertions and checks of every design are those of 0.8.0.

What was proven is mostly what one expects:
- branches under a parameter or a tie-off: `if (EnableRacl)` of the gpio and rv_timer register tops,
  `else if (reinit_i)` of `prim_subreg` (tied to 0), the ping handshake of the alert sender and receiver;
- the `default` item of complete FSM case statements (spi_master, sync_fifo, axi2apb_bridge);
- the software-reset FSM of the FIFOs inside ahb2axi_bridge.

**A PROVEN branch is dead in the RTL as delivered, not dead by design.** ahb2axi_bridge shows the difference.
Of its 102 branches, 22 are in `m_ahb2axi_ctrl.sv`: the states WR_BURST and WR_BBURST, the non-fallback exit of
WR_CAPTURE (line 626), and with them `o_axi_awlen` and `o_axi_awburst`, which are proven constant. So this RTL
never issues an AXI burst; every AHB burst is sent as single transfers. The cause is fault 2 of §3:
- the first beat of a burst is NONSEQ;
- it is still at the head of the command queue when the FSM enters WR_CAPTURE;
- so `w_cap_stop` (`htrans != SEQ`) fires at once and sets `reg_burst_fallback`.

The specification asks for burst aggregation, so this code is dead because of a fault. The proof is right, and the
block metric (77.1 → 97.1 %) is the coverage of the RTL as delivered. The reviewer has to judge each exclusion against the
specification: the review packet's checklist has "The unreached code and cover points are unreachable by design or
accepted", and `work/unr.md` lists every PROVEN branch with its file and line. The 20 failing tests of ahb2axi
already show the fault. No PROVEN branch of the other designs is in code that the specification requires.

**23.5, expression closure of ot_rv_timer.** `nnc cover --metric expression --target 90` was run without the
`prim_*` modules declared pre-verified. Agents A10 (analyst, reads the RTL) and A11 (test writer, never sees it)
were used. Cost: US$3.44.

| Round | Expression (without pre-verified) | Scenarios | Tests added |
|---|---|---|---|
| baseline | 83.7 % (273/326) | | |
| 1 | **87.4 %** (285/326) | 4 | `test_cov_101_subword_unaligned_writes`, `test_cov_102_idle_bad_masks`, `test_cov_103_idle_instr_write`, `test_cov_104_intg_flip_commands` |
| 2 | — | 0 | none: no scenario with legal, specification-level stimulus |

- The 4 tests pass: 27/27 tests, 13 assertions, 0 failures. The tests and assertions that were there before are
  unchanged.
- The target of 90 % is not met. The analyst claims 10 groups of points unreachable through the ports. They are
  listed in `work/coverage.md` and still counted. Examples:
  - inputs tied off in the one configuration (`busy_i`, `en_ifetch_i`, the hardware `de` of software-only
    registers);
  - integrity errors that the single-bit `i_a_intg_flip` cannot make (a double error, data integrity);
  - the `reg_we_err` countermeasure, which needs a fault inside the register block.
- These claims are plausible, but no tool has proved them. A formal proof of expression points, as 23.3 does for
  branches, would settle them; it is not done.
- G3 was approved again on the owner's delegation, because closure changed `verif/`.

**23.6, CHK-012 of ahb2axi_bridge under x_init.** The A9 triage agent was run on this one failure only. It used the
same prompt and files as `nnc triage`, plus `run_set.json` and the earlier `triage.md`. The result is in
`work/triage_xrand_chk012.md` (US$1.19). Verdict: **A_rtl_wrong, the recorded fault 2, not a new fault.**
- `w_cap_stop` is not gated by the state, so every NONSEQ write starts with `reg_burst_fallback = 1`, also a SINGLE
  or INCR write that is not eligible for a burst.
- In WR_SINGLE with fallback, AWADDR and AWSIZE come from `reg_burst_addr[widx]` and `reg_burst_size[widx]`
  (`m_ahb2axi_ctrl.sv:688-690`). These arrays have no reset and were never loaded for that transfer.
- With zero initial values the AW carries address 0 and size 0. That address is wrong (spec :411), but it is
  aligned, so CHK-012 holds; the other failing tests already show the wrong address.
- With random initial values the size or the alignment is wrong, and CHK-012 fails: 10 times, all in
  `test_chk_021_accept_qualifiers`, until later bursts have written legal values into the slots.

The agent's options for the designer: gate `w_cap_stop` to WR_CAPTURE, the root fix. As hardening only, reset the
arrays. Nothing was changed. This is the same root cause that makes the AXI burst path dead (above).

Limits:
- a branch inside a module with no clocked block at module level (`cell_sync`) is not tried;
- the cut modules of 23.2 are free, so their own branches are not proved;
- a counterexample or a time limit leaves the branch counted (ahb2axi: 7 counterexamples, 2 time limits).

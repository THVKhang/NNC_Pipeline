# Evaluation — phases 1 to 16 (2026-11-15; design half 2026-11-18; hardening 2026-11-19; formal depth, spec-lint and two new designs 2026-11-20)

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

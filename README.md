# NNC Pipeline — Specification-driven RTL verification with gated AI agents

**EN:** NNC Pipeline reads a hardware specification and the protocol standards on its ports, extracts every rule with a citation, turns the approved rules into a verification contract, generates SystemVerilog assertions, functional cover points and cocotb tests **without ever showing the RTL to the agents that write them**, runs them on the RTL with Verilator, measures code, functional and mutation coverage per requirement, and analyses failures for the designer. A person approves each of four gates; the Python orchestrator enforces them.

**VI:** NNC Pipeline đọc đặc tả phần cứng và các chuẩn giao thức trên cổng của nó, trích mọi luật kèm trích dẫn, chuyển các luật đã duyệt thành verification contract, sinh SystemVerilog Assertion, cover point chức năng và test cocotb **mà không bao giờ cho agent viết chúng xem RTL**, chạy trên RTL bằng Verilator, đo code coverage, functional coverage và mutation theo từng luật, và phân tích lỗi cho người thiết kế. Một người duyệt mỗi gate trong bốn gate; orchestrator Python cưỡng chế chúng.

Status / Trạng thái: working prototype, run end-to-end on six delivered designs, two regenerated from their specification and one designed from a short description (below) · Python 3.11+ standard library (optional: pypandoc for export) · agents through Claude Code (no API key) · Verilator 5 + cocotb 2.

## Flow | Luồng

```
 spec + standards ──[ingest]── sections, sentences with IDs (code)
        │
   [extract] A1 workers: rules cite sentence IDs; quotes rebuilt by code; nothing left uncovered
   [review]  A2 workers: keep / fix / reject, merge duplicates · A3: questions answered from the documents
        ══ G1 rules ══
   [contract] interface from the spec tables (code: clocks, resets, derived parameters) + A4 check plan:
              every rule in a check or with a reason · `nnc plan` selects the test plan
        ══ G2 contract ══                       ─── no RTL beyond this line ───
   [gen-sva]   A5: checker bodies in a fixed scaffold · A6: functional cover points · Verilator lint + repair
   [gen-tests] A7: cocotb tests on a helper library; validation + repair loop
        ══ G3 verification sources ══
   [sim]     interface conformance → DUT + checkers → Verilator/cocotb (WSL on Windows) → evidence + sim/Makefile
   [cover]   baseline of line/block/expression/toggle/functional; closure only towards the designer's target
             (A10 proposes scenarios, filtered of RTL names by code; A11 writes tests without RTL)
   [triage]  A9 (reads RTL): spec says / RTL does / test does / A-B-C → designer decides
   [mutate]  mutants on a copy of the RTL (executed lines) → A12 maps mutants to rules → score per rule ≥ 85 %
   [report]  report.md + rtm.json: rule → check → evidence, sign-off conditions
        ══ G4 sign-off ══
```

| Principle / Nguyên tắc | Enforced by / Cưỡng chế bằng |
|---|---|
| Expected behaviour comes from spec and standards, never from RTL | generator agents run with no tools or in a sandbox without `rtl/`; code refuses RTL inputs; closure scenarios naming RTL-internal identifiers are dropped |
| Every rule cites the source text | agents return sentence IDs; invalid IDs are dropped and counted |
| No normative sentence is silently dropped | coverage ledger + one gap-fill pass; leftovers reported as uncovered |
| An assertion that never fired proves nothing | per-check hit and fail counters; NOT_HIT in the report |
| Only a person approves a gate | gate records hash the artifacts; a change makes the gate STALE; approvals made on delegation are flagged in the report |
| Nothing is reported as passed without a tool run | results are written by code from simulator output only |
| A failing run is never "fixed" by the flow | triage proposes; RTL, tests, assertions and expected values change only on the designer's decision |

## Quick start | Bắt đầu nhanh

```bash
python -m nnc doctor
python -m nnc init my_ip --top m_my_ip
python -m nnc doc add my_ip spec/my_ip_spec.md --role ip_spec --tag IP
python -m nnc doc add my_ip standards/protocol.md --role standard --tag PR
cp rtl/*.sv designs/my_ip/rtl/
python -m nnc flow my_ip                 # stops at G1: read designs/my_ip/work/rules.md
python -m nnc gate approve my_ip G1_rules --by "Your Name"
python -m nnc flow my_ip --from contract # and so on for G2, G3, G4
python -m nnc cover my_ip --target 95 --metric block   # only if you want a coverage target
python -m nnc inject my_ip my_bug.diff   # does the approved verification catch this change?
cd designs/my_ip/sim && make help        # reproduce the regression without the orchestrator
```

In Claude Code: `/nnc-flow my_ip` runs the same steps and presents each gate. Full walk-through: [docs/GUIDE.md](docs/GUIDE.md). Design and measurements: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Evaluation of the latest phases: [docs/EVALUATION.md](docs/EVALUATION.md).

## Results on six designs | Kết quả trên sáu thiết kế

Specifications and RTL from [VLSIT_ASIC_SOC_AI_SKILLS](https://github.com/nguyenquanicd/VLSIT_ASIC_SOC_AI_SKILLS) `common_rtl/` (Apache-2.0; copies unchanged except one line fixed in axi2apb's `m_axi2apb_wr_seq.sv`, see each design's NOTICE). Everything under `work/`, `verif/` and `sim/` was produced by the flow, except the test-bench fixes described below (each recorded at a G3 re-approval). Gates G1–G3 were approved by Claude **on the user's delegation** (recorded as such, with reasons); **G4 sign-off is left to a person**.

| | [apb_tlul_bridge](designs/apb_tlul_bridge) | [axi2apb_bridge](designs/axi2apb_bridge) | [sync_fifo](designs/sync_fifo) |
|---|---|---|---|
| Design | APB4 → TL-UL, 1 clock | AXI4 → APB4, 1 clock, 45 ports | two synchronous clocks, 2 hardware resets + software reset, derived parameters |
| Rules kept / open questions | 232 / 5 | 151 / 4 | 272 / 7 |
| Checks (assertions + tests) | 31 (17 + 14) | 31 (17 + 14) | 25 (11 + 14) |
| First run | **15/15 tests, 17/17 assertions, 0 fails** | 2/15 tests; CHK-016 fails 606× | 25/25 tests; CHK-007 fails 32× |
| Triage verdict | — | **real RTL bug** | **checker wrong**, RTL right |
| After the fixes | — | **15/15 tests, 17/17 assertions, 0 fails** | **25/25 tests, 11/11 assertions, 0 fails** |
| Line / block / expr. / toggle / functional | 96.0 / 95.6 / 100 / 95.9 % / 38 → **40 of 40** after one closure round | 98.9 / 95.9 / 96.2 / 74.8 % / 39 of 40 | 99.2 / 97.3 / 92.8 / 70.6 % / 40 of 40 |
| Mutation (36 mutants, executed lines only) | 100 % (33/33, every candidate), 0 rules below 85 % | 88.9 % (4 survivors), 0 rules below 85 % | 100 %, 0 rules below 85 % |
| Rules VERIFIED / FAILED | 169 / 0 | 114 / 0 | 174 / 0 |
| Agent cost | ≈ US$6–7 for a clean run | US$11.9 | US$15.0 |

A mutant counts as killed only by a test or check that passes on the unmutated RTL. Before this rule the failing first run of axi2apb_bridge reported a meaningless 100 %; on the fixed RTL the 4 survivors point at checks still worth adding (or at equivalent mutants). Mutants are drawn only from lines the regression executed (lcov count > 0): a line inside an inactive `` `ifdef`` or an unselected generate branch is not part of the simulated design.

- **axi2apb_bridge — a bug in the delivered RTL, found and fixed.** Every AXI write issued its first APB transfer at AWADDR + size; the last beat landed outside the burst. Found by an SVA checker and 12 tests that never saw the RTL, traced by triage to `m_axi2apb_wr_seq.sv:344`, and confirmed by the specification's own waveform WF-005 (upstream `rtl_v2/` has the same line). The one-line fix was checked on a copy with `nnc inject`, then applied. The remaining failure exposed an ambiguous arbitration sentence; the decision is round-robin (what the RTL does), so the contract and test were regenerated, not the RTL. A last failure was the test bench's reference model ignoring APB writes that a reset cut short (triage: *test wrong*); fixed without relaxing the check. → [fix_candidate/README.md](designs/axi2apb_bridge/fix_candidate/README.md)
- **sync_fifo — a wrong checker, caught and fixed.** All tests passed; one generated SVA scoreboard cleared its queue one clock edge late after a software reset. Triage said *B: checker wrong* with evidence (the RTL matches the specification and three other checks). The scoreboard now clears in the same cycle; CHK-007 has 0 fails and mutation stays at 100 %. → [work/triage.md](designs/sync_fifo/work/triage.md)
- **apb_tlul_bridge — clean, and an injected bug is caught.** → [work/report.md](designs/apb_tlul_bridge/work/report.md), [bug_demo](designs/apb_tlul_bridge/bug_demo)

### Asynchronous clock domains | Clock bất đồng bộ

`nnc config <ip> clock_relation=async` starts every clock after its own seeded random delay, and the agents write cross-domain checks as order plus a window counted in destination edges. Build defines and simulator plusargs (`defines`, `plusargs`) reach the tests through `plusarg()` and `DEFINES`. Two clock-domain-crossing designs from the same repository, each run over a **run set** (`run_set.json`): the configurations named by its specification, the metastability model on (several seeds) and off, and the synthesis branch. Results are merged per check: PASS needs one run that verified it and no run that failed it.

| | [async_gray_fifo](designs/async_gray_fifo) | [async_apb_bridge](designs/async_apb_bridge) |
|---|---|---|
| Design | Gray-pointer FIFO, independent resets + software reset handshake | APB → APB bridge across domains, two- or four-phase handshake |
| Rules kept / open questions | 416 / 9 | 260 / 7 |
| Checks (assertions + tests) | 32 (13 + 19) | 35 (18 + 17) |
| Run set | 14 runs, 10 configurations: CFG-BASE seeds 1–5, model off, `VLSIT_SYNTHESIS`, cell 1/3/4, SRAM macro, depth 2 × width 1, clock ratios 11:3 and 3:11 | 14 runs, 12 configurations: APB4 seeds 1–3, model off, `VLSIT_SYNTHESIS`, 4-phase (model on/off), APB5, user signals, 3-/4-FF cells, CFG-MIN, completer 3× faster / 9× slower |
| NOT_VERIFIABLE, one run → run set | 17 → **3** (statistics across seeds) | 7 → **0** |
| Result (regenerated with the run set, 2026-11-14) | 23 PASS, 9 FAIL, all in model-on runs → triage **C: the specification contradicts itself** (10/10) | **35/35 checks PASS** in every configuration; rules VERIFIED 185, NOT_PROVEN 0 |
| Line / toggle / functional (merged) | 99.1 / 99.5 % / 40 of 40 | 91.9 / 98.6 % / 39 of 40 |
| Mutation (36), one run → run set | 80.6 → **91.7 %**, rules below 85 %: 14 → 5 | 72.2 → **83.3 %**, rules below 85 %: 18 → 3 |
| Mutation after regeneration (sample of 12) | 100 % (12/12) | 91.7 % (11/12) |
| Test-bench hand fixes (triage B) | 13 (10 simulation, 3 formal) | 1 |
| Agent cost | US$39.5 (of which US$5.5 lost to calls cut by the usage limit) | US$12.5 |

- **async_gray_fifo — a contradiction in the specification.** REQ-VER-001 makes the metastability model delay *each bit independently* and lets a later change replace a pending one. When the source Gray pointer steps twice inside that delay, the synchronized value can be a code that never existed (CHK-003, CHK-013: threshold flags break "never optimistic"), and a short pointer bit can vanish so that `o_empty` falls one edge after the S..S+2 window (CHK-025). Real synchronizers cannot do either. Every model-off and synthesis-branch run passes every test and assertion. The RTL follows the specification, so the decision (a coherent model, or a bound for back-to-back updates) is the designer's; the checks were not relaxed. The first generation needed eight test-bench fixes, four of them for faults only visible in other configurations (a checker discarding pre-reset words at the S=2 edge for every cell type, tests assuming depth 8). Regenerated with the run set in the prompts (2026-11-14), the configuration faults are gone, but 13 fixes of other kinds were needed (reset handling, clock-edge sampling; 3 from formal counterexamples), so the total did not drop; see [docs/EVALUATION.md](docs/EVALUATION.md). → [work/triage.md](designs/async_gray_fifo/work/triage.md)
- **async_apb_bridge — clean in every configuration of its specification.** The 7 checks that needed APB5, user signals, the four-phase handshake, a 4-FF cell, the minimum widths or the model off are now verified in the run that has them.
- **Mutation over a run set:** a mutant runs in the first run that executes its line; a survivor runs again in every other configuration. A four-phase or APB5 term reached in the default run is thus tested where it matters, which is where most of the gain comes from.

### A sixth design: ahb2axi_bridge | Thiết kế thứ sáu

[ahb2axi_bridge](designs/ahb2axi_bridge) (AHB5 → AXI4, 52 ports, burst aggregation; upstream has lint logs but no testbench) went through G1–G3 with no change to the flow: 234 rules, 40 checks, tests valid at the first attempt and no hand fix. On the delivered RTL **1 of 21 tests pass** and formal finds 9 counterexamples; triage judges every analysed failure an RTL fault. Three faults are traced to lines of the RTL (pipelined transfers dropped, single writes using a stale burst address, HREADYOUT held for the next address phase); two fix candidates, checked on a copy with `nnc inject`, raise the result to 6/21. `rtl/` is unchanged: the fix is the designer's decision. → [fix_candidate/README.md](designs/ahb2axi_bridge/fix_candidate/README.md)

### Compared with the hand-written testbenches | So với testbench viết tay

`nnc baseline <ip>` runs the upstream hand-written testbench, as its own script runs it, against the same benchmark bugs and the same mutants. sync_fifo: bugs 3/3 for both, mutants **29/36 hand-written vs 36/36 NNC**; apb_tlul_bridge: 3/3 and 33/33 for both; async_apb_bridge: bugs 3/3 for both, mutants 10/12 vs 11/12. No mutant was killed only by the hand-written testbench. Only three designs have an upstream testbench, and the benchmark bugs were written by the same assistant; see the limits in [docs/EVALUATION.md](docs/EVALUATION.md).

### Bug benchmark and CI | Đo bằng bug cài sẵn và CI

`nnc bench <ip>` runs the hand-written realistic faults of `designs/<ip>/bugs/bugs.json` (one-line changes: a full flag one entry early, an overflow raised for a blocked write, PPROT taken from the wrong channel, a dropped PSLVERR, a burst one beat short, an unchecked source ID, a binary instead of Gray pointer across the clock domains, a two-phase acknowledge detected on the wrong level…) against the approved verification. A bug counts as caught only when a test or check fails that passes on the unmodified RTL. **15 of 15 were caught**, 3 per design, and the triage agent named the RTL as the cause for **15 of 15** (all 141 per-failure analyses said *RTL wrong*; US$12.7 in total, about US$0.84 per bug) ([work/bench.md](designs/async_gray_fifo/work/bench.md)).

### Formal check | Kiểm chứng formal

`nnc config <ip> formal=on`, then `gen-env` and `formal`: SymbiYosys checks every generated assertion, alone, by bounded model checking (depth 20), k-induction and a cover of its antecedent (vacuity). Open-source Yosys does not read clocked concurrent SVA, so the subset the generator emits is translated to immediate assertions by code; the rest is reported, never approximated. The environment (`verif/formal/nnc_env.sv`) holds the obligations of the specification on the input side, written by agent A13 from the specification only and approved at G3; counterexamples are classified by agent A14 (RTL, checker, specification, or a missing environment obligation).

Formal runs once per distinct parameter set of the run set (a counterexample in any configuration counts; otherwise the weakest result), and the prove step tries `abc pdr` before k-induction.

| | apb_tlul | axi2apb | sync_fifo | async_apb | async_gray_fifo | ahb2axi |
|---|---|---|---|---|---|---|
| PROVEN / BOUNDED (depth 20), first version | 10 / 7 | 9 / 7 | 4 / 5 | 2 / 12 | 1 / 8 | — |
| PROVEN / BOUNDED, per configuration + PDR | **17 / 0** | 12 / 4 | 7 / 2 | **15 / 0** | 5 / 2 | 8 / 2 |
| Counterexamples left | 0 | 0 | 0 | 0 | 0 | **9, all judged RTL faults** |
| Not checked | — | 1 timeout | 1 timeout, 1 simulation-only checker | 3 simulation-only | 6 simulation-only (the regenerated read checker uses `time`) | 1 vacuous |

- **The three injected apb_tlul bugs** each gave a counterexample on the right checks.
- **axi2apb: a generated checker was wrong three times**, invisible to simulation because no test drove those requests: a FIXED burst above 16 beats, a 4-KiB range taken from an unaligned start, an unaligned WRAP start. The RTL rejected all three as the specification requires; the checker's classification was fixed (G3, NOTICE).
- **The CDC designs needed environment rounds:** 13 counterexamples came from free clocks and resets (a reset pulse between two clock edges, a reset of one domain only). A14 named the rules; A13 added them (reset released on its own clock, resets asserted together, no traffic after a one-domain reset until both are reset). The two FIFO counterexamples left are in the state the specification calls *inconsistent and not detected* after a one-domain reset: whether the threshold checks should exclude it is a specification question, left to the reviewer.

CI (`.github/workflows/ci.yml`) runs the unit tests, then each design's reproduction kit with `make` only, and `nnc kit-check` compares its outcome with the committed results. No agent runs in CI.

`nnc report` also writes `work/review_packet.md` for the person who signs G4: the delegated decisions, failures with their triage, hand edits, what is not verified and a checklist. **G4 is open on every design**; a request for a qualified reviewer is in [docs/G4_REVIEW_REQUEST.md](docs/G4_REVIEW_REQUEST.md).

Coverage targets are the designer's choice: `cover` shows every baseline, the functional points never hit and the uncovered code items, and runs closure only when a target is set. On apb_tlul_bridge a demonstration target (functional 100 %, set on delegation) was closed in one round: the analyst turned the two missed points (response delayed ≥ 8 cycles, response pending at reset release) into two specification-level scenarios, a writer without RTL access produced `test_apb_tlul_bridge_cov1.py`, and both tests pass (US$1.77).

## Design half | Nửa thiết kế

**EN:** The same gates, extended to a design whose RTL the flow writes (`rtl_origin=generated`). Two gates are added: D1 approves the final parameter values, and D2 approves the generated RTL.

```
 description ──[spec-draft] A0 → spec (SPEC_TEMPLATE), checked by spec-check
        ══ G1 rules ══ ══ G2 contract ══
   [params --choose]   legal values from the spec tables, checked by code      ══ D1 config ══
   [gen-rtl] A15 (never sees verif/) → rtl-check: RTL_RULES, Verilator lint, Yosys structure,
             GF180MCU synthesis (area, ABC delay at TT/SS) → repairs                ══ D2 rtl ══
   [close-loop] sim → triage → fix-rtl (spec-level fault text only; also --from formal)
   [restyle] A16 rewrites to RTL_RULES → Yosys miter + SymbiYosys: PROVEN / CEX
   [export]  spec, rules, contract, reports → DOCX / HTML / PDF
```

| Design | What was tested | Result |
|---|---|---|
| gen_apb_tlul_bridge | A15 rewrote the RTL from the spec; the approved verification and the upstream testbench ran on it | 17/17 tests, 17/17 formal PROVEN, mutation 36/36, upstream testbench passes |
| gen_sync_fifo | the same, on the FIFO | formal found 2 RTL faults that simulation missed, `fix-rtl --from formal` repaired them in 1 attempt; 24/25 tests, the one left is a question for the specification owner (CHK-008) |
| apb_tlul_bridge restyle | rewrite to RTL_RULES without changing behaviour | 6 rule warnings → 0, equivalence **PROVEN** |
| uart_lite (new) | a 30-line description → spec → RTL → verification | RTL right first time; 20/20 tests and 13/13 assertions in 4 configurations (after 2 recorded hand fixes of the generated checker and harness), no formal counterexample, mutation 35/36, about US$12 |

Details: [docs/EVALUATION.md §6](docs/EVALUATION.md), [docs/GUIDE.md §6](docs/GUIDE.md), [docs/RTL_RULES.md](docs/RTL_RULES.md), [docs/SPEC_TEMPLATE.md](docs/SPEC_TEMPLATE.md).

**VI:** Cùng hệ thống gate, mở rộng cho thiết kế mà flow tự viết RTL. Có thêm hai gate: D1 duyệt giá trị tham số cuối cùng, D2 duyệt RTL đã sinh.
- Agent viết RTL không bao giờ thấy phần verification.
- Vòng sửa chỉ gửi cho agent mô tả lỗi ở mức spec.
- `restyle` chứng minh bản viết lại tương đương bằng formal.

Kết quả:
- Sinh lại hai thiết kế đã kiểm chứng: cầu APB đạt hết. FIFO thì formal tìm ra 2 lỗi RTL mà mô phỏng bỏ sót, và vòng sửa đã sửa chúng.
- UART làm từ đầu: RTL đúng ngay lần đầu.

D1/D2 được duyệt theo uỷ quyền. **G4 chưa ai ký.**

## Scope | Phạm vi

NNC Pipeline started as the **verification** half of a specification-to-silicon flow such as [VLSIT_RTL_Generator_AI_Flow](https://github.com/nguyenquanicd/VLSIT_RTL_Generator_AI_Flow). Phases 5 to 10 add the **design** half (see [Design half](#design-half--nửa-thiết-kế)): a specification draft from a short description, a checked parameter configuration, RTL written by an agent that never sees the verification, code rule checks with Verilator lint and Yosys synthesis on GF180MCU, a closed repair loop driven by the specification-level text of failures, a restyle with a formal equivalence proof, and DOCX/PDF export. It does not run STA, place and route, CDC/RDC analysis or DFT.

NNC Pipeline ban đầu là **nửa verification** của một flow từ spec tới silicon. Giai đoạn 5 đến 10 thêm **nửa thiết kế**: soạn nháp spec từ một mô tả ngắn, cấu hình tham số được kiểm tra, RTL do một agent viết mà không bao giờ thấy phần verification, kiểm luật code cùng Verilator lint và tổng hợp Yosys trên GF180MCU, vòng sửa khép kín dựa trên mô tả lỗi ở mức spec, viết lại RTL cho sạch kèm chứng minh tương đương formal, và xuất DOCX/PDF. Hệ thống không chạy STA, place and route, phân tích CDC/RDC hay DFT.

## Repository | Cấu trúc

```
nnc/                 orchestrator: ingest, extract, review, contract, gen_sva, gen_cov, gen_tests, sim, coverage,
                     closure, triage, mutate, report, inject, flow, runset (run sets), bench (bug benchmark),
                     kitcheck (CI comparison), packet (G4 reviewer packet), formal + gen_env (SymbiYosys)
                     design half: params (legal values, D1), gen_rtl + rtlcheck (A15, lint, Yosys/GF180, D2),
                     derive, equiv + restyle (A16, equivalence proof), specdraft (A0), export (DOCX/PDF)
nnc/agents/          Claude Code backend (inline worker / sandboxed deep agent), manual backend, cache, schema validator
nnc/simlib/          helper library copied next to generated cocotb tests (clocks, resets, multi-clock helpers)
.claude/commands/    /nnc-flow, /nnc-gate
designs/<ip>/        spec/, rtl/, work/ (artifacts, review sheets), verif/ (generated checkers, cover points, tests),
                     sim/ (Makefile kit to reproduce the regression), run_set.json, bugs/ (benchmark faults)
.github/workflows/   CI: unit tests and the reproduction kit of every design
tests/               unit tests (no tokens, no simulator) and sim_smoke/ (cocotb + Verilator smoke test)
docs/                ARCHITECTURE.md, GUIDE.md
```

## Limits | Giới hạn

- **EN:** Simulation, plus an optional formal check of the generated assertions (bounded or k-induction, default parameters only, assertions in the translated SVA subset); no CDC/RDC, STA or DFT checks (synthesis gives area and an ABC delay estimate for generated RTL only, not timing sign-off); rules of that kind are listed as not verifiable by simulation. Several clocks may be synchronous (started together) or asynchronous (seeded random phase per clock); metastability itself is modelled only if the RTL has a model. One run is one configuration and one seed; a run set (`run_set.json`) runs several and merges them, and a check that no run can verify is reported NOT_VERIFIABLE. Generated tests and checkers can be wrong (sync_fifo shows one): that is what the gates, the hit counters, triage and the mutation score are for. Model outputs vary between runs; the cache makes a re-run reproducible.
- **VI:** Mô phỏng, cộng thêm kiểm chứng formal tuỳ chọn cho các assertion đã sinh (giới hạn độ sâu hoặc k-induction, chỉ cấu hình tham số mặc định, chỉ tập SVA dịch được); không có CDC/RDC, STA hay DFT (synthesis chỉ cho diện tích và ước lượng trễ của RTL do flow sinh, không phải ký duyệt timing); các luật loại đó được liệt kê là không kiểm được bằng mô phỏng. Nhiều clock có thể đồng bộ (khởi động cùng lúc) hoặc bất đồng bộ (pha ngẫu nhiên theo seed cho từng clock); metastability chỉ được mô hình nếu RTL có mô hình. Mỗi lần chạy là một cấu hình và một seed; run set (`run_set.json`) chạy nhiều cấu hình rồi gộp kết quả, check nào không lần chạy nào kiểm được thì báo NOT_VERIFIABLE. Test và checker do agent sinh có thể sai (sync_fifo là một ví dụ): đó là lý do có gate, bộ đếm hit, triage và mutation score. Kết quả của model có thể khác giữa các lần; cache giúp chạy lại cho cùng kết quả.

## Licence | Giấy phép

MIT ([LICENSE](LICENSE)). Copyrighted standards (for example Arm's AXI specification in `specs/`) and everything quoting them (`designs/axi_std/`) are kept out of git. Third-party design files keep their own licence (see each design's NOTICE).

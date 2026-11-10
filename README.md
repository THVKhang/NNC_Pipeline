# NNC Pipeline — Specification-driven RTL verification with gated AI agents

**EN:** NNC Pipeline reads a hardware specification and the protocol standards on its ports, extracts every rule with a citation, turns the approved rules into a verification contract, generates SystemVerilog assertions, functional cover points and cocotb tests **without ever showing the RTL to the agents that write them**, runs them on the RTL with Verilator, measures code, functional and mutation coverage per requirement, and analyses failures for the designer. A person approves each of four gates; the Python orchestrator enforces them.

**VI:** NNC Pipeline đọc đặc tả phần cứng và các chuẩn giao thức trên cổng của nó, trích mọi luật kèm trích dẫn, chuyển các luật đã duyệt thành verification contract, sinh SystemVerilog Assertion, cover point chức năng và test cocotb **mà không bao giờ cho agent viết chúng xem RTL**, chạy trên RTL bằng Verilator, đo code coverage, functional coverage và mutation theo từng luật, và phân tích lỗi cho người thiết kế. Một người duyệt mỗi gate trong bốn gate; orchestrator Python cưỡng chế chúng.

Status / Trạng thái: working prototype, run end-to-end on three designs (below) · Python 3.11+ standard library only · agents through Claude Code (no API key) · Verilator 5 + cocotb 2.

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

In Claude Code: `/nnc-flow my_ip` runs the same steps and presents each gate. Full walk-through: [docs/GUIDE.md](docs/GUIDE.md). Design and measurements: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Results on three designs | Kết quả trên ba thiết kế

Specifications and RTL from [VLSIT_ASIC_SOC_AI_SKILLS](https://github.com/nguyenquanicd/VLSIT_ASIC_SOC_AI_SKILLS) `common_rtl/` (Apache-2.0; copies unchanged except one line fixed in axi2apb's `m_axi2apb_wr_seq.sv`, see each design's NOTICE). Everything under `work/`, `verif/` and `sim/` was produced by the flow. Gates G1–G3 were approved by Claude **on the user's delegation** (recorded as such, with reasons); **G4 sign-off is left to a person**.

| | [apb_tlul_bridge](designs/apb_tlul_bridge) | [axi2apb_bridge](designs/axi2apb_bridge) | [sync_fifo](designs/sync_fifo) |
|---|---|---|---|
| Design | APB4 → TL-UL, 1 clock | AXI4 → APB4, 1 clock, 45 ports | two synchronous clocks, 2 hardware resets + software reset, derived parameters |
| Rules kept / open questions | 232 / 5 | 151 / 4 | 272 / 7 |
| Checks (assertions + tests) | 31 (17 + 14) | 31 (17 + 14) | 25 (11 + 14) |
| First run | **15/15 tests, 17/17 assertions, 0 fails** | 2/15 tests; CHK-016 fails 606× | 25/25 tests; CHK-007 fails 32× |
| Triage verdict | — | **real RTL bug** | **checker wrong**, RTL right |
| After the fixes | — | **15/15 tests, 17/17 assertions, 0 fails** | **25/25 tests, 11/11 assertions, 0 fails** |
| Line / block / expr. / toggle / functional | 96.0 / 95.6 / 100 / 95.9 % / 38 → **40 of 40** after one closure round | 98.9 / 95.9 / 96.2 / 74.8 % / 39 of 40 | 99.2 / 97.3 / 92.8 / 70.6 % / 40 of 40 |
| Mutation (36 mutants) | 100 %, 0 rules below 85 % | 86.1 % (5 survivors), 0 rules below 85 % | 100 %, 0 rules below 85 % |
| Rules VERIFIED / FAILED | 169 / 0 | 114 / 0 | 174 / 0 |
| Agent cost | ≈ US$6–7 for a clean run | US$11.9 | US$15.0 |

A mutant counts as killed only by a test or check that passes on the unmutated RTL. Before this rule the failing first run of axi2apb_bridge reported a meaningless 100 %; on the fixed RTL the 5 survivors point at checks still worth adding (or at equivalent mutants).

- **axi2apb_bridge — a bug in the delivered RTL, found and fixed.** Every AXI write issued its first APB transfer at AWADDR + size; the last beat landed outside the burst. Found by an SVA checker and 12 tests that never saw the RTL, traced by triage to `m_axi2apb_wr_seq.sv:344`, and confirmed by the specification's own waveform WF-005 (upstream `rtl_v2/` has the same line). The one-line fix was checked on a copy with `nnc inject`, then applied. The remaining failure exposed an ambiguous arbitration sentence; the decision is round-robin (what the RTL does), so the contract and test were regenerated, not the RTL. A last failure was the test bench's reference model ignoring APB writes that a reset cut short (triage: *test wrong*); fixed without relaxing the check. → [fix_candidate/README.md](designs/axi2apb_bridge/fix_candidate/README.md)
- **sync_fifo — a wrong checker, caught and fixed.** All tests passed; one generated SVA scoreboard cleared its queue one clock edge late after a software reset. Triage said *B: checker wrong* with evidence (the RTL matches the specification and three other checks). The scoreboard now clears in the same cycle; CHK-007 has 0 fails and mutation stays at 100 %. → [work/triage.md](designs/sync_fifo/work/triage.md)
- **apb_tlul_bridge — clean, and an injected bug is caught.** → [work/report.md](designs/apb_tlul_bridge/work/report.md), [bug_demo](designs/apb_tlul_bridge/bug_demo)

Coverage targets are the designer's choice: `cover` shows every baseline, the functional points never hit and the uncovered code items, and runs closure only when a target is set. On apb_tlul_bridge a demonstration target (functional 100 %, set on delegation) was closed in one round: the analyst turned the two missed points (response delayed ≥ 8 cycles, response pending at reset release) into two specification-level scenarios, a writer without RTL access produced `test_apb_tlul_bridge_cov1.py`, and both tests pass (US$1.77).

## Scope | Phạm vi

NNC Pipeline covers the **verification** half of a specification-to-silicon flow such as [VLSIT_RTL_Generator_AI_Flow](https://github.com/nguyenquanicd/VLSIT_RTL_Generator_AI_Flow): from an approved specification and an existing RTL to evidence a person can sign off. It does not write specifications or RTL, and it does not run synthesis, STA, formal proof or CDC analysis.

NNC Pipeline đảm nhiệm **nửa verification** của một flow từ spec tới RTL: từ spec đã duyệt và RTL có sẵn tới bằng chứng để người ký duyệt. Nó không viết spec hay RTL, không chạy synthesis, STA, formal hay CDC.

## Repository | Cấu trúc

```
nnc/                 orchestrator: ingest, extract, review, contract, gen_sva, gen_cov, gen_tests, sim, coverage,
                     closure, triage, mutate, report, inject, flow
nnc/agents/          Claude Code backend (inline worker / sandboxed deep agent), manual backend, cache, schema validator
nnc/simlib/          helper library copied next to generated cocotb tests (clocks, resets, multi-clock helpers)
.claude/commands/    /nnc-flow, /nnc-gate
designs/<ip>/        spec/, rtl/, work/ (artifacts, review sheets), verif/ (generated checkers, cover points, tests),
                     sim/ (Makefile kit to reproduce the regression)
tests/               unit tests (no tokens, no simulator) and sim_smoke/ (cocotb + Verilator smoke test)
docs/                ARCHITECTURE.md, GUIDE.md
```

## Limits | Giới hạn

- **EN:** Simulation only: no formal proof, CDC/RDC, STA, synthesis or DFT checks; rules of that kind are listed as not verifiable by simulation. Several clocks are supported only as synchronous clocks started together (any ratio); asynchronous clock domains are not modelled. One parameter configuration and one seed per run. Generated tests and checkers can be wrong (sync_fifo shows one): that is what the gates, the hit counters, triage and the mutation score are for. Model outputs vary between runs; the cache makes a re-run reproducible.
- **VI:** Chỉ mô phỏng: không có formal, CDC/RDC, STA, synthesis hay DFT; các luật loại đó được liệt kê là không kiểm được bằng mô phỏng. Nhiều clock chỉ hỗ trợ dạng đồng bộ, khởi động cùng lúc (tỉ lệ bất kỳ); chưa mô hình clock bất đồng bộ. Mỗi lần chạy một cấu hình tham số và một seed. Test và checker do agent sinh có thể sai (sync_fifo là một ví dụ): đó là lý do có gate, bộ đếm hit, triage và mutation score. Kết quả của model có thể khác giữa các lần; cache giúp chạy lại cho cùng kết quả.

## Licence | Giấy phép

MIT ([LICENSE](LICENSE)). Copyrighted standards (for example Arm's AXI specification in `specs/`) and everything quoting them (`designs/axi_std/`) are kept out of git. Third-party design files keep their own licence (see each design's NOTICE).

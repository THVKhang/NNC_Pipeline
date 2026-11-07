# NNC Pipeline — Specification-driven RTL verification with gated AI agents

**EN:** NNC Pipeline reads a hardware specification and the protocol standards on its ports, extracts every rule with a citation, turns the approved rules into a verification contract, generates SystemVerilog assertions and cocotb tests **without ever showing the RTL to the agents that write them**, runs them on the RTL with Verilator, measures coverage and mutation score, and analyses failures for the designer. A person approves each of four gates; the Python orchestrator enforces them.

**VI:** NNC Pipeline đọc đặc tả phần cứng và các chuẩn giao thức trên cổng của nó, trích mọi luật kèm trích dẫn, chuyển các luật đã duyệt thành verification contract, sinh SystemVerilog Assertion và test cocotb **mà không bao giờ cho agent viết chúng xem RTL**, chạy trên RTL bằng Verilator, đo coverage và mutation score, và phân tích lỗi cho người thiết kế. Một người duyệt mỗi gate trong bốn gate; orchestrator Python cưỡng chế chúng.

Status / Trạng thái: working prototype, validated end-to-end on one design (below) · Python 3.11+ standard library only · agents through Claude Code (no API key) · Verilator 5 + cocotb 2.

## Flow | Luồng

```
 spec + standards ──[ingest]── sections, sentences with IDs (code)
        │
   [extract] A1 workers: rules cite sentence IDs; quotes rebuilt by code; nothing left uncovered
   [review]  A2 workers: keep / fix / reject, merge duplicates · A3: questions answered from the documents
        ══ G1 rules ══
   [contract] interface from the spec tables (code) + A4 check plan: every rule in a check or with a reason
        ══ G2 contract ══                       ─── no RTL beyond this line ───
   [gen-sva]   A5: checker bodies in a fixed scaffold, Verilator lint + repair loop
   [gen-tests] A7: cocotb tests on a helper library; validation + repair loop
        ══ G3 verification sources ══
   [sim]     interface conformance → DUT + checkers → Verilator/cocotb (WSL on Windows) → evidence
   [triage]  A9 (only agent that reads RTL): spec says / RTL does / test does / A-B-C → designer decides
   [mutate]  mutants on a copy of the RTL, regression in parallel → score
   [report]  report.md + rtm.json: rule → check → evidence
        ══ G4 sign-off ══
```

| Principle / Nguyên tắc | Enforced by / Cưỡng chế bằng |
|---|---|
| Expected behaviour comes from spec and standards, never from RTL | generator agents run with no tools or in a sandbox without `rtl/`; code refuses RTL inputs |
| Every rule cites the source text | agents return sentence IDs; invalid IDs are dropped and counted |
| No normative sentence is silently dropped | coverage ledger + one gap-fill pass; leftovers reported as uncovered |
| An assertion that never fired proves nothing | per-check hit and fail counters; NOT_HIT in the report |
| Only a person approves a gate | gate records hash the artifacts; a change makes the gate STALE |
| Nothing is reported as passed without a tool run | results are written by code from simulator output only |

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
```

In Claude Code: `/nnc-flow my_ip` runs the same steps and presents each gate. Full walk-through: [docs/GUIDE.md](docs/GUIDE.md). Design and measurements: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Example: APB4 → TL-UL bridge | Ví dụ: cầu APB4 → TL-UL

[designs/apb_tlul_bridge](designs/apb_tlul_bridge) — specification, RTL and the TL-UL standard from [VLSIT_ASIC_SOC_AI_SKILLS](https://github.com/nguyenquanicd/VLSIT_ASIC_SOC_AI_SKILLS) (Apache-2.0, see its NOTICE). Every file under `work/` and `verif/` was produced by the flow. Gates G1–G3 were approved by Claude **on the user's delegation** (recorded as such, with the five open questions decided in `work/rules.md`); G4 sign-off is left to a person.

| Stage / Giai đoạn | Result / Kết quả |
|---|---|
| Rules | 286 extracted, 232 kept after review; 45 reviewer questions → 39 answered from the documents with citations, 5 genuinely open |
| Contract | 31 checks (17 assertions, 14 tests) built with the 5 designer decisions; every rule in a check or declared not verifiable by simulation (63, with reasons) |
| Generated sources | 4 SVA checkers lint-clean (one after a Verilator repair round); 15 cocotb tests; one test-code error (IndexError) repaired automatically without RTL, no check changed |
| Simulation | 15/15 tests pass; 17/17 assertions hit, 0 fail; RTL line coverage 97.6 %; 169 rules VERIFIED |
| Mutation | 36/36 mutants killed (100 %) |
| Injected bug ([bug_demo](designs/apb_tlul_bridge/bug_demo)) | caught by 2 tests and an assertion; triage points at the exact RTL line and fix |
| Cost | ≈ US$6–7 of Claude Code quota for a clean run (≈ 45 min), most of it for test generation |

Report: [work/report.md](designs/apb_tlul_bridge/work/report.md) · rules: [work/rules.md](designs/apb_tlul_bridge/work/rules.md) · contract: [work/contract.md](designs/apb_tlul_bridge/work/contract.md).

## Repository | Cấu trúc

```
nnc/                 orchestrator: ingest, extract, review, contract, gen_sva, gen_tests, sim, mutate, triage, report, flow
nnc/agents/          Claude Code backend (inline worker / sandboxed deep agent), manual backend, cache, schema validator
nnc/simlib/          helper library copied next to generated cocotb tests
.claude/commands/    /nnc-flow, /nnc-gate
designs/<ip>/        spec/, rtl/, work/ (artifacts, review sheets), verif/ (generated checkers and tests)
tests/               unit tests (no tokens, no simulator) and sim_smoke/ (cocotb + Verilator smoke test)
docs/                ARCHITECTURE.md, GUIDE.md
```

## Limits | Giới hạn

- **EN:** Simulation only: no formal proof, CDC/RDC, STA, synthesis or DFT checks; rules of that kind are listed as not verifiable by simulation. One parameter configuration per run (the default unless overridden). Generated tests and checkers can be wrong: that is what the gates, the hit counters, triage and the mutation score are for. Model outputs vary between runs; the cache makes a re-run reproducible.
- **VI:** Chỉ mô phỏng: không có formal, CDC/RDC, STA, synthesis hay DFT; các luật loại đó được liệt kê là không kiểm được bằng mô phỏng. Mỗi lần chạy một cấu hình tham số. Test và checker do agent sinh có thể sai: đó là lý do có gate, bộ đếm hit, triage và mutation score. Kết quả của model có thể khác giữa các lần; cache giúp chạy lại cho cùng kết quả.

## Licence | Giấy phép

MIT ([LICENSE](LICENSE)). Copyrighted standards (for example Arm's AXI specification in `specs/`) and everything quoting them (`designs/axi_std/`) are kept out of git. Third-party design files keep their own licence (see each design's NOTICE).

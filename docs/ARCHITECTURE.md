# NNC Pipeline — Kiến trúc RTL Verification Flow

> Trạng thái: **toàn bộ flow đã hiện thực và chạy thật end-to-end** trên `designs/apb_tlul_bridge` (mục 13). Mục 11–12 ghi rõ phần nào đã có, phần nào chưa.

## 1. Mục tiêu

Từ **đặc tả (spec) của một IP** và **các chuẩn giao thức** trên cổng của nó, flow:

1. đọc tài liệu và **trích ra các luật (rule)** kèm trích dẫn nguyên văn;
2. chuyển luật thành **verification contract** (interface + hành vi mong đợi) được người duyệt;
3. **sinh mã kiểm chứng**: SVA (assert + đếm hit) và testbench cocotb (stimulus, reference model, scoreboard, functional coverage);
4. **chạy trên RTL thật** (Verilator) và thu bằng chứng: pass/fail, số lần mỗi assertion kích hoạt, code coverage, mutation score;
5. khi có lỗi, đưa ra **bảng phân tích** (spec / RTL / test) để kỹ sư quyết định;
6. xuất **báo cáo + RTM** truy vết luật → câu trích → check → kết quả.

Ngoài phạm vi: sinh RTL, formal proof, STA, sign-off vật lý.

## 2. Nguyên tắc

| ID | Nguyên tắc | Cưỡng chế bằng |
|---|---|---|
| PR-1 | Hành vi mong đợi chỉ lấy từ spec và chuẩn, **không bao giờ từ RTL**. | Agent sinh test chạy không có tool (inline) hoặc trong sandbox không chứa RTL; file trong `rtl/` bị code từ chối (mục 5). |
| PR-2 | Mọi luật phải dẫn về **câu nguyên văn** trong tài liệu nguồn. | Agent trả **ID câu**, câu trích do code ghép lại từ index; ID không tồn tại bị loại và đếm. |
| PR-3 | Không gì được ghi "PASS" nếu không có lệnh đã chạy chứng minh. Thiếu tool → `NOT_RUN`. | Kết quả chỉ được ghi bởi code chạy tool, không bởi LLM. |
| PR-4 | Assertion **không bao giờ kích hoạt** = FAIL. | Mỗi assertion có bộ đếm fail và bộ đếm hit (mục 7); runner kiểm hit > 0. |
| PR-5 | Mỗi gate do **người** duyệt; duyệt ghi hash artifact. Artifact đổi → gate **STALE**, các gate sau **BLOCKED**. | `nnc_state.json` + so hash khi `nnc status`. |
| PR-6 | Lỗi chưa rõ nguyên nhân: không tự sửa RTL hay test; trình bày phân tích, chờ quyết định. | Agent triage chỉ đọc, chỉ sinh báo cáo. |
| PR-7 | Không câu quy phạm nào bị bỏ sót âm thầm. | Sổ đối chiếu: mỗi câu `*` phải được dẫn hoặc bỏ qua có lý do; còn sót → hỏi lại một vòng; vẫn sót → báo `uncovered`. |

PR-1, PR-4, PR-6 lấy từ hai repo tham khảo (VLSIT_RTL_Generator_AI_Flow, VLSIT_ASIC_SOC_AI_SKILLS). Khác biệt: ở đây chúng được **cưỡng chế bằng code**, không chỉ bằng lời dặn trong prompt.

## 3. Kiến trúc tổng thể

```
 spec / standards (PDF, MD, TXT)
   │ [C] ingest: bỏ header/footer/mục lục, cây section, câu có ID, đánh dấu câu quy phạm (*)
   ▼
 [W] A1 Extractor ×N (song song, 1 gói / lần gọi) ─► [C] kiểm ID + sổ đối chiếu ─► [W] Gap-filler
   ▼
 [W] A2 Verifier ×N            (kiểm luật ↔ câu dẫn, strength, actor)
   ▼
 [D] A3 Consolidator / Critic  (gộp trùng, mâu thuẫn, câu hỏi mở; tra cứu bằng tool)
   ══ GATE 1: người duyệt luật ══
 [D] A4 Contract architect     (interface + oracle cho từng luật)
   ══ GATE 2: người duyệt contract ══
   │                ─── từ đây đến tích hợp: KHÔNG có RTL ───
 [C] nnc plan: người chọn check của test plan (mặc định: tất cả; phần bỏ ra → NOT_SELECTED)
 [W] A5 SVA writer ×N  ──► [C] verilator --lint-only với contract shell (vòng sửa ≤ 3)
 [W] A6 Functional coverage: cover point từ spec + contract ──► [C] lint (nnc_cov.sv)
 [D] A7 cocotb test writer + reference model / scoreboard
   ══ GATE 3: người duyệt nguồn kiểm chứng ══
 [C] integrate + regression + code coverage (line, block, toggle, expression) + functional coverage
 [D] A10 gap analyst (thấy RTL) ─► [C] lọc tên nội bộ ─► [W] A11 closure test writer (không RTL)
       └─ chỉ khi người đặt mục tiêu coverage; test mới → GATE 3 phải duyệt lại
 [C] gom lỗi thành cụm ─► [D] A9 Triage / debug (thấy cả RTL) ─► người quyết
 [C] mutation trên dòng đã chạy ─► [D] A12 gán mutant ↔ luật ─► [C] điểm từng luật, ngưỡng 85 %
   ══ GATE 4: sign-off (bảng điều kiện trong report) ══
 [C] report.md + rtm.json · designs/<ip>/sim/Makefile (tái lập không cần NNC)
```

`[C]` code tất định · `[W]` worker: 1 lượt, không tool, chạy song song · `[D]` deep agent: nhiều lượt, có tool đọc trong sandbox.

## 4. Đọc spec: map theo section con + ngữ cảnh cha (không phải RAG top-k)

**Vì sao không dùng RAG thuần cho bước trích luật:** RAG lấy top-k đoạn liên quan nhất và bỏ phần còn lại; trích luật cần **đủ, không sót**. Vì vậy:

1. **Ingest (code, 0 token)** — `nnc/ingest.py`:
   - PDF → text (poppler `pdftotext`); bỏ dòng lặp ở mép nhiều trang (header/footer/số trang) và trang mục lục;
   - dựng **cây section** từ heading đánh số, chỉ nhận heading **đúng thứ tự số** (loại mục lục, tham chiếu chéo, số trong bảng); cho phép sót tối đa 1 heading, mọi bất thường thành `warning`;
   - tách câu (giữ `e.g.`, `i.e.`...; tách bullet), gán **ID cố định** `3.1.1:s2` và số trang;
   - đánh dấu `*` câu có từ khoá quy phạm (*must, shall, only, permitted, recommended, can, remain, stable*...).
2. **Đóng gói (code)**: các section con liên tiếp trong cùng chương được gộp tới ngân sách token (mặc định 3.500); mỗi gói kèm **ngữ cảnh cha**: đường dẫn mục và 3 câu đầu của mục cha không nằm trong gói (đánh dấu "không được dẫn").
3. **Extractor (worker)** trả về luật **chỉ bằng ID câu** + trường cấu trúc (strength, actor, signals, condition, statement ≤ 35 từ, check). Code ghép câu trích → **không thể bịa câu trích**, token output nhỏ.
4. **Sổ đối chiếu (PR-7)** + **gap-filler**: câu `*` chưa được quyết định được gửi lại riêng một lần.
5. **Cache** theo fingerprint (nội dung gói + prompt + schema + model): chạy lại hoặc sửa spec chỉ tốn tiền cho gói thay đổi.

**RAG chỉ dùng ở bước sau**, khi deep agent cần tra cứu: chỉ mục SQLite FTS5 (BM25) + **chỉ mục tên tín hiệu** (`AWVALID` → mọi câu nhắc tới) — với spec phần cứng, tên tín hiệu chính xác hơn embedding. Embedding chỉ thêm khi đo được bỏ sót.

### Kết quả đo trên AXI (ARM IHI 0022C, 132 trang)

| Chỉ số | Giá trị |
|---|---|
| Sau ingest | 148 section, 1.461 câu, 582 câu `*`, ~38k token (bản thô ~75k) |
| Chương 3 (prompt v2) | 49 luật, 53/53 câu `*` được quyết định, 0 ID bịa, **US$0,079**, 25 s |
| Toàn bộ spec | **515 luật**, 582/582 câu `*` (555 dẫn + 32 bỏ qua có lý do), 0 sót, 0 ID bịa, 21 lần gọi, **US$1,04**, 87 s |

Đánh giá tay chương 3: prompt v1 sai strength ở 5/38 luật ("*can … only when*" bị coi là MAY thay vì cấm) và **sót 2 điểm** (payload phải ổn định — nằm trong câu giải thích hình; quyền "write data trước address"). Prompt v2 sửa cả hai. Bài học: phải có **bộ đáp án gán nhãn tay** để đo precision/recall mỗi khi đổi prompt/model (việc tiếp theo).

Hạn chế đã biết: nhãn trong hình vẽ (`ACLK INFORMATION VALID READY Figure 3-1 …`) dính vào câu kế tiếp; bảng bị làm phẳng thành câu; tiêu đề dính câu đầu được tách theo heuristic (có warning).

## 5. Gọi agent qua Claude Code (không cần API key)

Mỗi agent là một lần chạy `claude -p` dùng tài khoản Claude Code đã đăng nhập. `--bare` không dùng được (bắt buộc API key).

| Chế độ | Dùng cho | Cờ chính | Cách ly |
|---|---|---|---|
| **inline** | worker | nội dung qua stdin, `--tools ""`, `--system-prompt` riêng, `--json-schema`, `--strict-mcp-config --disable-slash-commands --no-session-persistence` | Không có tool → không đọc được gì ngoài nội dung được đưa |
| **sandbox** | deep agent | thư mục tạm chỉ chứa file được phép, `--tools Read,Grep,Glob`, `--allowedTools "Read(./**) …"` | `Read` trơn đọc được `../` (đã kiểm); `Read(./**)` bị chặn và ghi vào `permission_denials` |

**Chi phí cố định mỗi lần gọi** (đo 2026-11-07, Claude Code 2.1.319): mặc định ~US$0,33 (system prompt + tool ~20k token) → chế độ inline **US$0,0071** với Sonnet (~1,5k token). Haiku rẻ hơn nữa nhưng **không tuân thủ** yêu cầu trả ID câu trong thử nghiệm → Extractor dùng Sonnet.

**Giới hạn suy nghĩ:** mỗi lần gọi đặt `MAX_THINKING_TOKENS` (mặc định 32 000, đổi bằng biến `NNC_MAX_THINKING_TOKENS`). Lý do đo được: một lần gọi A7 không giới hạn đã dùng hết 128k token output để suy nghĩ, không trả lời gì (US$2,85) rồi chạm hạn mức 5 giờ; thông báo của CLI nay được đưa vào lỗi.

Mọi câu trả lời được validate lại theo schema; log mỗi lần gọi ghi model, token, chi phí, `permission_denials`. Backend **manual** cho phép chạy mọi bước không cần LLM (người điền `output.json`).

## 6. Phân bổ agent

Điều phối là **code Python tất định**, không phải LLM: rẻ, tái lập được, gate được cưỡng chế. Deep agent chỉ dùng ở nơi cần suy luận xuyên nhiều section; việc lặp theo từng mảnh giao cho worker rẻ chạy song song.

| Giai đoạn | Vai trò (module) | Loại | Model mặc định | Số lần gọi (cầu APB→TL-UL) | Được thấy |
|---|---|---|---|---|---|
| ingest | — (`ingest.py`) | code | — | 0 | — |
| extract | A1 Extractor + gap-filler (`extract.py`) | worker inline | Sonnet | 1 / gói (29) | gói section + ngữ cảnh cha |
| review | A2 Verifier + gộp trùng (`review.py`) | worker inline | Sonnet | 1 / cụm luật (23) | luật + câu trích |
| review | A3 Consolidator: giải đáp câu hỏi (`review.resolve_questions`) | worker inline, ngữ cảnh lớn | Sonnet | 1 | mọi câu của spec + chuẩn |
| contract | A4 Contract architect (`contract.py`) | deep (inline, 1 lượt) | Opus | 1 (+ gap-fill) | interface (từ code) + luật |
| gen-sva | A5 SVA writer (`gen_sva.py`) | worker + Verilator lint, sửa ≤ 3 | Sonnet | 1 / nhóm check (4) | phần contract + câu trích; khung code cố định |
| gen-sva | A6 functional coverage (`gen_cov.py`) | worker + Verilator lint, sửa ≤ 3 | Sonnet | 1 | interface + check + luật; khung bộ đếm cố định |
| gen-tests | A7 reference model + test writer (`gen_tests.py`) | deep (inline) + kiểm tra, sửa ≤ 2 | Opus | 1 | contract + câu trích + API thư viện |
| sim | repair hạ tầng test (`gen_tests.repair`) | như trên | Opus | chỉ khi test lỗi Python | lỗi Python (không gửi check thất bại, không RTL) |
| cover | A10 gap analyst (`closure.analyse`) | **deep sandbox** | Opus | 1 / vòng closure | điểm chưa phủ, **RTL** (trừ metric functional), contract, luật |
| cover | A11 closure test writer (`closure.write_tests`) | inline + kiểm tra | Opus | 1 / vòng | kịch bản đã lọc tên nội bộ RTL + check của contract; **không RTL** |
| triage | A9 Debugger (`triage.py`) | **deep sandbox** `Read/Grep/Glob(./**)` | Opus | 1 / lần chạy có lỗi | spec, contract, **RTL**, test, checker, log |
| mutate | A12 gán mutant ↔ luật (`mutate.attribute`) | **deep sandbox** | Sonnet | 1 | mutant, **RTL**, luật, contract; không sửa gì, không đổi điểm |

Ghi chú: A8 "Reviewer" riêng cho mã sinh ra chưa làm — vai trò kiểm tra mã hiện do code đảm nhiệm (lint, validate cấu trúc, bộ đếm hit, mutation) cùng Gate 3. Các agent thấy RTL (A9, A10, A12) đều chạy **sau** khi oracle đã cố định và chỉ đọc; kịch bản của A10 đi qua bộ lọc code (bỏ mọi kịch bản nhắc tên định danh của RTL không có trong spec/contract) trước khi tới A11.

## 7. Lớp mô phỏng

| Thành phần | Công cụ | Ghi chú |
|---|---|---|
| Simulator | **Verilator 5.055** | `assert property` với `|=>`, `$stable`, `disable iff` chạy đúng (smoke test). |
| Testbench | **cocotb 2.1** | Bản đi kèm OSS CAD Suite (Python 3.11 `tabbypy3`). |
| Assertion | SVA trong module checker | Chỉ dùng tín hiệu ở interface của contract. |
| Đếm fail | action block `else` của assert | Chạy đúng, mô phỏng tiếp tục. |
| Đếm hit | `always_ff` trên cùng antecedent | **Verilator bỏ qua action statement của `cover property`** (đã kiểm: hits = 0). `cover property` vẫn giữ cho coverage database. |
| Functional coverage | module `nnc_cov.sv` (A6): mỗi cover point một bộ đếm `always_ff`, in `NNC_COVER COVP-nnn hits=` | Verilator gần như bỏ qua `covergroup`; điểm lấy từ spec, không từ RTL. |
| Code coverage | `--coverage-line --coverage-toggle --coverage-expr`; `coverage.dat` đọc bằng code (`coverage.py`) | Chỉ tính file RTL của DUT (loại checker, tb); từng metric riêng, không gộp: line (lcov), block (nhánh), toggle (mỗi bit, 2 chiều), expression. |
| Coverage closure | `nnc cover --target --metric` | Hiện baseline trước; tối đa 5 vòng, dừng khi đạt, 2 vòng không tăng, hoặc lỗi chức năng đầu tiên (lỗi → triage). Điểm "không thể đạt" chỉ là đề xuất cho người duyệt, không bị trừ khỏi mẫu số. |
| Mutation | bộ sinh mutant Python trên **bản copy** RTL | Chỉ đột biến dòng đã chạy và file đã elaborate (dòng chưa phủ chỉ đo coverage); mutant không compile không tính; A12 gán mutant cho luật → điểm từng luật, ngưỡng `mutation_threshold` (mặc định 85 %). |
| Nhiều clock | `clocks`/`resets` đọc từ bảng port (cột Signal type, Clock domain) | Các clock đồng bộ khởi động cùng lúc; chu kỳ theo `clock_periods`; một test có thể đặt tỉ lệ khác (`start_clock(dut, periods=...)`); SVA mỗi check theo clock của miền tín hiệu. |
| Clock bất đồng bộ | `clock_relation=async` (config) → `contract.json` interface | Mỗi clock khởi động sau một trễ ngẫu nhiên < 1 chu kỳ (seed + số thứ tự test), chu kỳ tính bằng ps nguyên (cho phép 13.7 ns); prompt contract/SVA/test thêm luật CDC: không giả sử cạnh trùng nhau, check qua miền = thứ tự + cửa sổ tính bằng cạnh clock đích; `stop_clock`/`resume_clock` cho test. |
| Tuỳ chọn chạy | `defines`, `plusargs` (config) | `+define+` khi lint/build DUT, plusargs cho simulator (`{seed}` → seed); cùng vào Makefile tái lập. Test đọc được qua `plusarg("NAME")` và `DEFINES` (`nnc_interface.json` → `run_options`); prompt A7 có mục RUN CONFIGURATION ghi đúng tên, cấm đoán. Một lần chạy = một cấu hình; check cần cấu hình khác → `NOT_VERIFIABLE`. |
| Tham số dẫn xuất | `LPARA_* = clog2(...)` trong bảng tham số | Thành `localparam` trong checker/tb, không truyền vào DUT, giá trị tính sẵn cho test (`PARAMS`). |
| Bộ tái lập | `designs/<ip>/sim/Makefile` | `help`, `tool-check`, `lint`, `sva-compile`, `regression`, `test TC=<regex>`, `coverage-report`; mọi lệnh EDA hiện trong recipe (`make -n`). |
| Simulator khác | `SIM=questa` / `SIM=icarus` qua cocotb | Questa: SVA + covergroup đầy đủ nếu có license; Icarus: không có SVA concurrent. |

**Quy tắc cho agent viết SVA/test** (đều phát hiện khi chạy smoke test):
- Không mở đầu comment bằng từ "verilator" — Verilator hiểu là pragma và báo lỗi.
- cocotb huỷ mọi task (kể cả clock) do một test tạo ra khi test đó kết thúc → mỗi test tự khởi động clock.
- Bộ đếm hit dùng `always_ff`, không dùng action block của `cover property`.

Smoke test: [tests/sim_smoke](../tests/sim_smoke) — 2 luật AXI (R-3.1-05 giữ VALID, R-3.1-03 data ổn định), 3 kịch bản (hợp lệ / hạ VALID sớm / đổi data khi chờ), **3/3 pass, đếm fail và hit khớp chính xác**.

## 8. Môi trường

| Thành phần | Vị trí | Phiên bản |
|---|---|---|
| Orchestrator, agent, ingest | Windows (Python 3.11+, Claude Code, `pdftotext` của Git for Windows) | Python 3.13, Claude Code 2.1.319, poppler 4.00 |
| Mô phỏng | WSL2 **Ubuntu 24.04.5**, đĩa ảo tại `E:\WSL\Ubuntu-24.04` | Verilator 5.055, Icarus 14, Yosys 0.70, g++ 13.3, GNU make 4.3, cocotb 2.1 |
| Đường dẫn công cụ | `/opt/oss-cad-suite`, venv `/opt/nnc-venv`; `/etc/profile.d/nnc.sh` thêm vào PATH | |

Lưu ý: `pdftotext` bản mingw không mở được đường dẫn có ký tự không phải ASCII (thư mục `ドキュメント`) → ingest chạy nó trong thư mục của file với tên tương đối. Build mô phỏng nên đặt trong filesystem Linux (`/root/...`), không trong `/mnt/c` (OneDrive, chậm).

## 9. Cấu trúc thư mục

```
NNC_Pipeline/
├── nnc/
│   ├── cli.py              # lệnh: doctor, init, status, config, doc, answer, gate, plan, ingest, extract, review,
│   │                       #   contract, gen-sva, gen-tests, sim, cover, triage, mutate, report, flow, inject
│   ├── flow.py             # các giai đoạn + chuỗi có gate
│   ├── inject.py           # áp patch lên bản copy RTL (chèn bug / thử bản sửa) rồi chạy verification đã duyệt
│   ├── project.py          # workspace, cấu hình, gate, hash
│   ├── ingest.py           # PDF/text theo trang, Markdown theo heading; bảng → câu
│   ├── extract.py review.py contract.py gen_sva.py gen_cov.py gen_tests.py sim.py coverage.py closure.py
│   ├── mutate.py triage.py report.py
│   ├── simhost.py          # chạy EDA trong WSL (Windows) hoặc tại chỗ (Linux)
│   ├── simlib/nnc_cocotb.py  # thư viện cho test cocotb sinh ra
│   └── agents/             # backend claude-cli (inline/sandbox), manual, cache, chạy song song, JSON Schema
├── .claude/commands/       # /nnc-flow, /nnc-gate
├── designs/<ip>/           # spec/, rtl/ (chỉ A9/A10/A12 được đọc), work/, verif/, sim/ (Makefile tái lập), nnc_state.json
├── specs/                  # tài liệu gốc do người dùng thêm (PDF bản quyền: không đưa lên git)
├── tests/                  # unit test (không tốn token) + sim_smoke/
└── docs/                   # ARCHITECTURE.md, GUIDE.md
```

## 10. Thiết kế thử nghiệm

- **Chuẩn giao thức:** AXI (IHI0022C) — đang dùng để đo trích luật.
- **IP đầu tiên:** `apb_tlul_bridge` (VLSIT_ASIC_SOC_AI_SKILLS, Apache-2.0): cầu APB4 → TL-UL, có testbench viết tay làm mốc (36 assertion, bắt 15/15 bug chèn). Tiêu chí P5: flow tự động bắt được ít nhất các bug đó.
- **IP thứ hai và ba (P6):** `axi2apb_bridge` (AXI4 → APB4, 4 file RTL) và `sync_fifo` (FIFO hai clock đồng bộ, 2 miền clock, 3 reset, tham số dẫn xuất, macro SRAM không elaborate) từ `common_rtl/` cùng repo (Apache-2.0), chép nguyên vẹn, xem NOTICE của từng thiết kế. Kết quả ở mục 14.

## 11. Lộ trình

| Phase | Nội dung | Trạng thái |
|---|---|---|
| P0 | Khung repo, CLI, gate, backend agent | Xong |
| P1 | Ingest (PDF + Markdown) + A1 + gap-filler + cache; A2 review; A3 giải đáp câu hỏi | Xong, chạy thật trên AXI và cầu APB→TL-UL |
| P2 | A4 contract (interface từ code) + A5 SVA (lint loop) + A7 cocotb (validate + repair loop) | Xong |
| P3 | Runner WSL/local, kiểm tra conformance, tb top, regression, coverage, bằng chứng | Xong |
| P4 | Mutation song song + A9 triage + report/RTM | Xong (triage kiểm bằng bug chèn, xem mục 13) |
| P5 | `flow` có gate, `/nnc-flow`, tài liệu song ngữ, ví dụ end-to-end | Xong |
| P6 | Nhiều clock/reset, tham số dẫn xuất; code coverage nhiều metric + closure; functional coverage; mutation theo từng luật; chọn test plan; Makefile tái lập; bảng điều kiện sign-off; chạy trên 3 IP | Xong (mục 14) |
| Tiếp | Bộ đáp án gán nhãn tay để đo precision/recall của trích luật; chạy nhiều cấu hình tham số trong một lệnh; nhiều seed; A8 reviewer cho mã sinh; FTS5 cho deep agent tra cứu; clock bất đồng bộ (CDC) | Chưa làm |

## 12. Quyết định

**Đã chốt:** cocotb + Verilator (Questa/Icarus là lựa chọn qua `SIM=`); SV + SVA, không UVM; orchestrator Python; LLM qua Claude Code headless; worker inline không tool, deep agent sandbox `Read(./**)`; Extractor/review/SVA dùng Sonnet, contract/test/triage dùng Opus; trích luật bằng map toàn bộ section + ngữ cảnh cha, RAG chỉ cho tra cứu; khung code cố định (header, bộ đếm, khối final, thư viện helper) để agent chỉ viết phần có trí tuệ.

**Đã chốt thêm (2026-11-08):** ngưỡng mutation theo từng luật mặc định 85 % (như repo tham khảo), đổi bằng `nnc config <ip> mutation_threshold=<n>`; mục tiêu coverage do người đặt sau khi xem baseline, không có ngưỡng mặc định.

**Còn mở:** có license Questa hay không.

## 13. Kết quả end-to-end trên cầu APB4 → TL-UL

Thiết kế: [designs/apb_tlul_bridge](../designs/apb_tlul_bridge) — spec của IP (Markdown, 741 dòng) + chuẩn TL-UL của OpenTitan (727 dòng) + RTL 3 file. Gate G1–G3 được Claude duyệt **theo ủy quyền của người dùng** (ghi rõ trong `nnc_state.json` và báo cáo; 5 câu hỏi mở được quyết định bằng `nnc answer`); G4 sign-off để lại cho người.

| Giai đoạn | Kết quả | Chi phí agent |
|---|---|---|
| ingest | spec: 59 section, 499 câu, 41 bảng; TL-UL: 34 section, 322 câu | 0 |
| extract | 245 + 41 luật; 0 câu quy phạm bị sót; 0 ID bịa | US$0,87 |
| review | 286 → giữ 232 (sửa 59), gộp 9, loại 45; 45 câu hỏi → 39 được tài liệu trả lời (có trích dẫn), 1 trùng, **5 thật sự mở** | US$1,10 |
| contract | interface 32 port / 6 tham số đọc từ bảng; nhận 5 quyết định G1; 31 check (17 assertion, 14 test); 232/232 luật có check hoặc lý do (63 không kiểm được bằng mô phỏng) | US$1,30 |
| gen-sva | 4 checker, 17 assertion, lint sạch (1 module cần 1 vòng sửa theo lỗi Verilator) | US$0,34 |
| gen-tests | 1 module cocotb, 15 test; 1 lỗi code test (IndexError) được sửa tự động không cần RTL, số assert giữ nguyên 155 → G3 thành STALE, được duyệt lại | ~US$3,6 |
| sim | **15/15 test pass; 17/17 assertion hit, 0 fail; line coverage RTL 97,6 %; 169 luật VERIFIED** | 0 |
| mutate | **36/36 mutant bị bắt (100 %)**, toàn bộ vị trí đột biến của RTL | 0 |
| bug chèn tay ([bug_demo](../designs/apb_tlul_bridge/bug_demo)) | bỏ so sánh `d_source`: 2 test + assertion CHK-009 (156 lần) bắt; triage chỉ đúng `m_tlul_if.sv:100` và bản sửa 1 dòng | US$0,63 |

Tổng một lần chạy sạch từ đầu khoảng **US$6–7** quota Claude Code (≈ 45 phút); con số trong báo cáo gồm cả các lần chạy lại khi phát triển flow.

*Cập nhật 2026-11-08:* sau khi sửa lỗi đánh số lại check (mục 14), checker, cover point và test của IP này được sinh lại từ contract đã sửa; số liệu hiện tại (line 96,0 %, 15/15 + 2 test closure, 36/36 mutant) ở mục 14. Bảng trên là lần chạy đầu.

**Lỗi của chính flow được phát hiện nhờ chạy thật, và đã sửa:**
1. Thư viện helper nhận `salt` kiểu int nhưng tài liệu API không nói → 17/18 test lỗi `TypeError`. Sửa thư viện; thêm luật: lỗi phát sinh bên trong `nnc_cocotb.py` là lỗi của flow, **không** gửi cho agent "sửa test".
2. Test khai thừa: một test "pass" cho luật "tham số sai phải bị báo lúc elaboration" mà không kiểm gì. Sửa: contract đưa loại luật này vào not_verified; thêm `not_verifiable()` và trạng thái `NOT_VERIFIABLE` để test không thể pass âm thầm.
3. Assertion bị che: test dừng ở lỗi đầu tiên, reset của test sau huỷ property `|=>` đang chờ → SVA báo 0 lỗi dù có bug. Sửa: `reset_dut` cho 2 cạnh clock trôi qua trước khi reset; demo bug sau đó cho thấy assertion bắt 156 lần.

## 14. Kết quả trên 3 IP (P6, 2026-11-08; cập nhật sau khi sửa 2026-11-10)

Ba thiết kế từ VLSIT_ASIC_SOC_AI_SKILLS (Apache-2.0), RTL và spec chép nguyên vẹn, trừ một dòng đã sửa trong `m_axi2apb_wr_seq.sv` của axi2apb (ghi trong NOTICE); mọi file trong `work/`, `verif/`, `sim/` do flow sinh. Gate G1–G3 do Claude duyệt **theo ủy quyền** (ghi rõ người duyệt "Claude (delegated by GabrielHCMUT)" và lý do trong `nnc_state.json`, báo cáo đánh dấu "a person should confirm"); **G4 để lại cho người**. Mỗi lần chạy: 1 seed, cấu hình mặc định, 36 mutant.

| | apb_tlul_bridge | axi2apb_bridge | sync_fifo |
|---|---|---|---|
| Đầu vào | spec 741 dòng + chuẩn TL-UL; RTL 3 file | spec 616 dòng; RTL 4 file (1 226 dòng) | spec 935 dòng; RTL 6 file, 2 không elaborate (macro SRAM) |
| Đặc điểm | 1 clock | 1 clock, 45 port | **2 clock** đồng bộ, 2 reset cứng + reset mềm, 3 tham số dẫn xuất `LPARA_*` |
| Luật (giữ / vào) | 232 / 286 | 151 / 190 | 272 / 320 |
| Câu hỏi: tài liệu trả lời / mở | 39 / 5 | 30 / 4 | 36 / 7 |
| Check (assertion + test) | 31 (17 + 14) | 31 (17 + 14) | 25 (11 + 14) |
| Luật không kiểm được bằng mô phỏng (có lý do) | 63 | 37 | 98 |
| Sinh nguồn | lint sạch lần 1; test hợp lệ lần 1 | lint sạch lần 1; test hợp lệ lần 1 | 1 checker cần 1 vòng sửa lint; test hợp lệ lần 1; **1 vòng sửa code test** sau mô phỏng (thời gian tính bằng ps), duyệt lại G3 |
| Mô phỏng lần đầu | **15/15 test pass, 17/17 assertion hit, 0 fail** | 2/15 pass; CHK-016 fail 606 lần | 25/25 test pass; CHK-007 fail 32 lần |
| Kết luận triage | — | **bug thật của RTL** (A); sau đó 1 lỗi testbench (B) | **checker sai** (B) |
| Sau khi sửa | — | **15/15 test, 17/17 assertion, 0 fail** | **25/25 test, 11/11 assertion, 0 fail** |
| Line / block / expression / toggle | 96,0 / 95,6 / 100 / 95,9 % | 98,9 / 95,9 / 96,2 / 74,8 % | 99,2 / 97,3 / 92,8 / 70,6 % |
| Functional (điểm từ spec) | 38/40 → **40/40** sau 1 vòng closure (mục tiêu minh hoạ) | 39/40 | 40/40 |
| Mutation (chạy lại 2026-11-11, chỉ dòng đã chạy) | 33/33 (toàn bộ ứng viên); 76 luật có mutant, 0 dưới 85 % | 32/36 = 88,9 % (4 sống sót); 69 luật, 0 dưới 85 % | 36/36 (loại 2 file không elaborate, 14 dòng không chạy); 60 luật, 0 dưới 85 % |
| Luật VERIFIED / FAILED | 169 / 0 | 114 / 0 | 174 / 0 |
| Chi phí agent | US$2,97 cho lần sinh lại từ gen-sva (contract trong cache) | US$11,90 toàn bộ (gồm sinh lại test sau quyết định phân xử) | US$15,04 toàn bộ (gồm triage lại; + US$2,85 một lần gọi hỏng, xem mục 5) |

**axi2apb_bridge — bug thật trong RTL tham khảo, đã sửa.** Mọi giao dịch ghi phát beat đầu ra APB ở AWADDR + size (ví dụ AWADDR 0x3000, 4 beat → PADDR 0x3004…0x3010, beat cuối nằm ngoài burst); đọc thì đúng. Checker SVA độc lập (CHK-016) và 12 test cùng thấy; triage (A9) truy về `m_axi2apb_wr_seq.sv:344` (cập nhật `reg_wr_addr` khi nhận W, trước khi `o_req_addr` gửi beat đó) và bác bỏ B/C có dẫn chứng. Waveform WF-005 của chính spec (AWADDR 0x2000, AWLEN 1 → PADDR 0x2000, 0x2004) xác nhận; `rtl_v2/` ở upstream có cùng dòng. Bản sửa thử trước trên **bản copy** bằng `nnc inject` (14/15, 0 fail assertion), rồi áp vào `rtl/`: địa chỉ tăng khi phản hồi APB của beat trả về. Test còn lại (CHK-019 pha D) lộ một chỗ **spec mơ hồ** về phân xử sau giao dịch không tranh chấp; quyết định ở G1 là **round-robin** (bên vừa được phục vụ bị ưu tiên thấp, đúng như RTL), nên contract và test được sinh lại, RTL phân xử giữ nguyên. Lần chạy kế tiếp lộ hai lỗi phía kiểm thử, đều đã sửa: helper `start_clock()` trả về task clock không bao giờ kết thúc nên test treo (sửa thư viện, không sửa test); mô hình tham chiếu bỏ sót các beat APB đã ghi trước khi reset cắt ngang burst (triage B, spec:163/333/584 không rollback) — sửa mô hình, so sánh bộ nhớ vẫn chính xác từng byte. Chi tiết: [designs/axi2apb_bridge/fix_candidate](../designs/axi2apb_bridge/fix_candidate/README.md).

**apb_tlul_bridge — sạch, và bug chèn vẫn bị bắt.** Với thế hệ nguồn mới, demo bug chèn ([bug_demo](../designs/apb_tlul_bridge/bug_demo/README.md), `nnc inject`) cho 2/17 test fail và assertion CHK-010 fail 2 lần; triage chỉ đúng `m_tlul_if.sv:100` (US$0,60). Báo cáo đáp ứng mọi điều kiện sign-off, chỉ chờ người duyệt G4.

**sync_fifo — checker sai, RTL đúng; đã sửa checker.** Mọi test (kể cả mô hình tham chiếu Python theo port) pass; assertion CHK-007 fail 32 lần, chỉ trong các test có reset mềm. Triage kết luận B: scoreboard SVA (`nnc_chk_sb.sv:51,55`) nhận biết kết thúc reset mềm qua bản đăng ký của `o_sw_rst_busy`, nên xoá hàng đợi muộn một cạnh clock so với CHK-006; RTL đúng theo REQ-SRST-005/006 và CHK-010, CHK-024 cùng xác nhận. Sau khi xem xét, checker được sửa (xoá hàng đợi tổ hợp ngay trong chu kỳ `o_sw_rst_busy` hạ), không nới lỏng điều kiện so sánh: 25/25 test, CHK-007 0 fail, mutation 100 %.

**Coverage.** `nnc cover` in baseline của mọi metric, các cover point chức năng chưa hit (kèm tên) và các mục code chưa phủ theo file; **mục tiêu do người thiết kế đặt**, không có ngưỡng mặc định. Minh hoạ trên apb_tlul_bridge (mục tiêu functional 100 % đặt theo ủy quyền): A10 đổi 2 điểm chưa hit (phản hồi trễ ≥ 8 chu kỳ; phản hồi treo lúc nhả reset) thành 2 kịch bản chỉ dùng tín hiệu của spec/contract, A11 (không RTL) viết `test_apb_tlul_bridge_cov1.py` sau 2 lần thử, 17/17 test pass, 40/40 điểm, 1 vòng, US$1,77; G3 duyệt lại. Toggle thấp ở hai IP mới chủ yếu là bit cao: ở axi2apb là bit cao của địa chỉ 32 bit (`i_axi_awaddr`, `o_apb_paddr`, …) mà test chỉ dùng vùng địa chỉ thấp, và các tín hiệu nội bộ size/mask 32 bit; ở sync_fifo là bit cao của các tín hiệu nội bộ mở rộng độ rộng (`w_wptr_ext`, `w_occ_nxt`, …), hằng 0 theo cấu trúc. Loại thứ nhất đạt được bằng kích thích (nếu người thiết kế đặt mục tiêu toggle), loại thứ hai thì không (danh sách trong `coverage.md`).

**Lỗi của flow lộ ra khi chạy 3 IP, đã sửa:**
1. Đánh số lại check: tham chiếu chéo `CHK-…` trong văn bản check, ghi chú not_verified và giả định giữ ID cũ của agent → nay viết lại trong một lượt; khoảng (`CHK-020..CHK-023`) được mở thành danh sách ID mới, dạng `CHK-015/017` cũng được xử lý. Contract của 3 IP được dựng lại từ cache, G2 duyệt lại.
2. Một lần gọi A7 không giới hạn suy nghĩ tiêu hết 128k token mà không trả lời → giới hạn `MAX_THINKING_TOKENS` (mục 5).
3. Test nhiều clock giả định thời điểm bắt đầu là số nguyên ns (cocotb chuyển test cách nhau 1 bước mô phỏng) → vòng sửa test tự động giải quyết; tài liệu API cho agent nay nói rõ.
4. `coverage.md` khi chưa đặt mục tiêu chỉ hiện line → nay hiện mọi metric và danh sách chưa phủ.
5. Mutation tính mutant là "bị giết" khi có bất kỳ test nào fail, kể cả test đã fail sẵn trên RTL gốc → regression đang fail cho 100 % vô nghĩa (axi2apb lần đầu). Nay chỉ test/check **pass trên RTL gốc** mới giết được mutant; `mutation.json` ghi `baseline_failing`.
6. `start_clock()` trả về task clock của cocotb 2 (không bao giờ kết thúc); test sinh ra `await` nó thì treo tới timeout → nay trả về `None`.
7. Khi WSL không chạy được hoặc bị dừng giữa chừng, log rỗng bị ghi thành `build_failed` không lý do → nay giữ thông báo và mã thoát của `wsl.exe` (`NNC_HOST_ERROR`).

## 15. Clock bất đồng bộ: 2 IP CDC (2026-11-11)

Hai thiết kế CDC từ cùng repo VLSIT (Apache-2.0, RTL và spec chép nguyên vẹn, NOTICE trong từng thư mục). Cấu hình: `clock_relation=async`, mô hình metastability của RTL bật bằng plusarg (`+..._MSYNC_EN=1`, seed theo seed của lần chạy), 1 seed, tham số mặc định, 36 mutant. G1–G3 duyệt theo ủy quyền như mục 14, **G4 để lại cho người**.

| | async_gray_fifo | async_apb_bridge |
|---|---|---|
| Đầu vào | spec 1 542 dòng; RTL 17 file (SRAM macro, 8 cell đồng bộ của thư viện không elaborate) | spec 900 dòng; RTL 14 file |
| Đặc điểm | FIFO con trỏ Gray, clock ghi 10 ns / đọc 13,7 ns, 2 reset cứng độc lập + reset mềm có bắt tay qua miền | Cầu APB → APB qua miền, bắt tay 2 pha (4 pha là tham số), APB5 tắt |
| Luật (giữ / vào) | 416 / 517 | 260 / 304 |
| Câu hỏi: tài liệu trả lời / mở | 51 / 9 | 34 / 7 |
| Check (assertion + test) | 32 (13 + 19) | 35 (18 + 17) |
| Luật không kiểm được bằng mô phỏng | 142 | 75 |
| Mô phỏng | **34/34 test pass**; CHK-003 và CHK-013 fail (34 và 61 lần trên ~100 000 lần kiểm) | **28/28 test pass, 0 assertion fail** (CHK-018 của APB5 không hit) |
| Kết luận triage | **C: spec mâu thuẫn** (xem dưới); trước đó 3 lỗi testbench (B), đã sửa | — |
| NOT_VERIFIABLE (cần cấu hình khác) | 17 | 7 |
| Line / block / expression / toggle / functional | 99,3 / 95,6 / 98,0 / 99,9 % / 40 of 40 | 90,8 / 87,0 / 73,0 / 98,5 % / 33 of 40 |
| Mutation | 80,6 % (29/36); 6 trong 7 mutant sống nằm trong mô hình mô phỏng | 72,2 % (26/36); 9 trong 10 mutant sống tương đương dưới cấu hình này |
| Luật VERIFIED / FAILED | 61 / 12 | 130 / 0 |
| Chi phí agent | US$32,85 (A7 US$21,17 gồm 3 lần sinh test: 2 lần dừng vì hết quota, 1 lần sau khi sửa flow) | US$11,83 |

**async_gray_fifo — spec mâu thuẫn, không phải bug RTL.** REQ-VER-001 bắt mô hình metastability trễ **từng bit độc lập** 0–2 chu kỳ. Khi con trỏ Gray nguồn đổi hai lần trong cửa sổ trễ đó (miền nguồn nhanh hơn), bit đổi sau có thể hiện ra trước bit đổi trước, nên giá trị đã đồng bộ là một mã chưa từng tồn tại ở nguồn; ước lượng số phần tử vượt 0..DEPTH và cờ ngưỡng sai (trái REQ-FUNC-010, INV-001, TEST-008 "flags never optimistic"). Phần cứng thật không làm được như vậy: chỉ bit đang đổi đúng lúc lấy mẫu mới bất định. Triage A9 kết luận C với dẫn chứng (fail chỉ ở tỉ lệ clock mà miền nguồn nhanh hơn); **chạy lại với mô hình tắt (`+AFIFO_MSYNC_EN=0`): 34/34 test, 13/13 assertion, 0 fail**, xác nhận giả thuyết. RTL làm đúng spec nên không sửa; người thiết kế quyết định: (1) mô hình phải giữ mã Gray nhất quán (bit đổi sau không được vượt bit đang chờ, hoặc một trễ cho cả vector), hoặc (2) giữ độc lập từng bit và giới hạn kích thích. CHK-003/013 giữ nguyên, không nới.

Trước đó lần mô phỏng đầu lộ 3 lỗi **testbench** (triage B, đã sửa, không check nào bị nới): helper `TB.rec` trả "never sampled" cho bản ghi cũ hơn 50 cạnh (range âm) làm CHK-031 dừng giữa chừng; scoreboard kiểm trước khi test reset (lan sang CHK-032); `init` đổi ngưỡng tĩnh khi FIFO không ở reset, và checker CHK-012 không miễn cho thay đổi của `i_rst_n_sw`/ngưỡng mà contract cho phép (vẫn kiểm chặt `o_overflow`, `o_sw_rst_busy`). Bản sinh ra được giữ để so sánh; G3 duyệt lại. Một mutant sống đáng thêm kích thích: `reg_req_wr` reset về 1 — cần một test reset cứng **riêng miền ghi** khi FIFO còn dữ liệu và không có reset mềm.

**async_apb_bridge — sạch.** 7 check NOT_VERIFIABLE đều cần tham số khác (APB5=1, HS_TYPE=1, CELL_TYPE=4, cấu hình nhỏ nhất) hoặc cận thời gian chặt khi mô hình metastability bật. Trong 10 mutant sống: 9 không thể đổi port nào dưới cấu hình này (nhánh HS_TYPE≠0, đường wake-up bị chặn bởi APB5=0, gán lặp lại cùng giá trị, trễ của mô hình vẫn trong khoảng 0–2 spec cho phép); 1 là khoảng trống nhỏ: test không kiểm rằng mô hình metastability thật sự bật.

**Lỗi của flow lộ ra, đã sửa:**
1. A7 **đoán tên plusarg** (`meta_on()` thử nhiều tên) vì prompt không có cấu hình chạy → `nnc_interface.json` mang `run_options`, thư viện có `plusarg()`/`DEFINES`, prompt có mục RUN CONFIGURATION (PROMPT_VERSION `tests-v2`); test FIFO sinh lại và dùng đúng `AFIFO_MSYNC_EN`.
2. Tham số dẫn xuất `LPARA_*` có công thức nằm ở cột khác cột default → SVA nhận `= Derived` và mọi checker lint fail → contract đọc công thức ở các cột khác (phải có toán tử hoặc `clog2`); tham số không đọc được mà port dùng → lỗi rõ ràng, không dùng → bỏ.
3. Mutation lấy cả dòng **không thuộc thiết kế đã elaborate** (nhánh `` `ifdef VLSIT_SYNTHESIS`` không biên dịch, nhánh generate không chọn): chỉ loại dòng có điểm coverage = 0, còn dòng không có điểm nào thì giữ → mutant tương đương giả (APB bridge 58,8 %, 6 mutant như vậy). Nay `results.json` ghi `executed_lines` (lcov count > 0, dạng khoảng) và mutation chỉ lấy dòng đã chạy; 3 IP cũ chạy lại theo luật mới.
4. Hết quota 5 giờ giữa lần sinh: agent báo lỗi rõ ("resets 6:50am"), chạy lại sau khi reset là đủ; không cần sửa.

**Giới hạn lúc đó — một cấu hình mỗi lần chạy.** 17 + 7 check NOT_VERIFIABLE và luật NOT_PROVEN tương ứng cần tham số, define hoặc plusarg khác. Đã giải quyết bằng run set (§16).

## 16. Run set, CI, benchmark bug, gói người duyệt (2026-11-11)

**Run set (`designs/<ip>/run_set.json`, `nnc/runset.py`).**
- **Cách chạy:** một regression gồm nhiều cấu hình (tham số, define, plusarg, chu kỳ clock) và nhiều seed. Mỗi cấu hình build một lần trong thư mục riêng; các seed chạy nối tiếp, các cấu hình chạy song song. Coverage được gộp bằng `verilator_coverage --write`.
- **Gộp kết quả không làm yếu kết luận:**
  - Test fail ở bất kỳ lần chạy nào là FAIL. Assertion được cộng hit/fail; chỉ là NOT_HIT nếu không lần nào hit.
  - NOT_VERIFIABLE chỉ khi **mọi** lần chạy đều khai như vậy. PASS cần một lần chạy kiểm được và không lần nào fail.
- **Báo cáo:**
  - Report có bảng *Run set*; mỗi check ghi `verified in …` / `failed in …`.
  - Có thêm điều kiện sign-off "mọi lần chạy đều build được".
  - Kết quả từng lần chạy ở `work/runs/<cấu hình>.s<seed>.json`, log ở `work/sim/runs/`.
- **Lần chạy chính** (cấu hình đầu tiên, seed đầu tiên) dùng cho bộ tái lập `sim/`.
- **Không cần sinh lại test:** test tự đọc tham số, define, plusarg của lần chạy.

| | async_gray_fifo (14 lần chạy, 10 cấu hình) | async_apb_bridge (14 lần chạy, 12 cấu hình) |
|---|---|---|
| NOT_VERIFIABLE: 1 lần chạy → run set | 17 → 3 (CHK-015/016/029: thống kê qua nhiều seed, mỗi lần chạy không tự kết luận được) | 7 → 0 |
| Kết quả | 26 PASS, 3 FAIL (CHK-003/013/025, triage C) | 35/35 PASS, luật VERIFIED 185, NOT_PROVEN 0 |
| Mutation: 1 lần chạy → run set | 80,6 → 91,7 % | 72,2 → 83,3 % |
| Thời gian mô phỏng | ≈ 2,5–3 phút cho cả run set | ≈ 4 phút |

**Lỗi lộ ra khi chạy cấu hình khác (FIFO, triage B, sửa tay, G3 duyệt lại):** code kiểm chứng sinh ra đã ngầm viết cứng cấu hình mặc định.
- Checker scoreboard bỏ từ trước reset ở cạnh 5 (= S+3 chỉ khi S=2), nên fail với cell 4 tầng.
- Test ghi ngay sau khi đọc mà không chờ con trỏ đọc đi qua miền clock (với độ sâu 2, `o_full` bi quan lên sớm, spec cho phép).
- CHK-024 chờ FIFO chứa 5 từ (không thể khi độ sâu là 2).
- CHK-025 cần FIFO sâu hơn cửa sổ đồng bộ.

Không check nào bị nới ở cấu hình mặc định.

Một lỗi mới, CHK-025 ở cell3/wr_slow (`o_empty` hạ ở cạnh S+3), được triage là cùng gốc với mâu thuẫn spec của CHK-003/013: mô hình metastability theo từng bit có thể nuốt một xung bit ngắn của con trỏ khi có hai lần ghi liên tiếp. Sửa test đồng nghĩa với nới cửa sổ mong đợi, nên check được **giữ FAIL** để người viết spec quyết.

**Mutation theo run set.**
- Mutant được lấy từ dòng mà **bất kỳ** lần chạy nào đã đi qua, và chạy ở lần chạy đầu tiên đi qua dòng đó, so với baseline của chính lần chạy đó.
- Mutant sống sót được chạy lại ở **mọi cấu hình khác** đi qua dòng đó (mỗi cấu hình một seed). Lý do: một dòng có thể chạy ở cấu hình mặc định trong khi phần bị đổi chỉ có tác dụng ở cấu hình khác (số hạng HS_TYPE, cổng APB5).
- Lần đầu chưa có vòng chạy lại, agent A12 đã gọi các mutant đó là "tương đương". Thật ra chúng chỉ tương đương **trong cấu hình đó**.

**CI (`.github/workflows/ci.yml`) và `nnc kit-check`.**
- **Unit test:** chạy trên Python 3.11 và 3.12.
- **Bộ tái lập:** với mỗi thiết kế, CI chạy `designs/<ip>/sim` bằng `make` thuần (Verilator của OSS CAD Suite 2026-11-07, cocotb 2.1.0, cố định phiên bản).
- **`kit-check`:** so *kết quả* (không so số đếm) với kết quả đã commit: tập test, test fail, assertion fail, assertion không hit, check NOT_VERIFIABLE.
- **Đã thử trong WSL:** cả 5 thiết kế cho SAME OUTCOME.
- CI không gọi agent nào và không dùng secret.

**Benchmark bug (`nnc bench`, `designs/<ip>/bugs/bugs.json`).**
- **Bộ bug:** 15 lỗi RTL viết tay (3 mỗi thiết kế), mỗi lỗi thay một dòng, giống lỗi thật:
  - cờ full sớm một ô; overflow cả khi bị chặn; so ngưỡng lệch một;
  - PPROT lấy nhầm kênh; mất PSLVERR; burst thiếu một beat;
  - không kiểm source ID; nhận ghi thiếu strobe; trả dữ liệu khi lỗi;
  - full chỉ so MSB của Gray; truyền con trỏ nhị phân thay vì Gray;
  - nhận ack hai pha sai mức; không chuyển PPROT.
- **"Bắt được"** chỉ khi có test/check fail mà trên RTL gốc vẫn pass. Nếu không, FIFO với 3 lỗi có sẵn sẽ "bắt" mọi bug miễn phí. `nnc inject` cũng dùng quy tắc này, và triage chỉ nhận các lỗi mới.
- **Kết quả: 15/15 bị bắt**, mỗi bug làm fail nhiều test/check độc lập.
- **Độ đúng của triage** (`--triage`, ≈ US$2–3 mỗi bug, agent Opus) chưa đo trên bộ này. Bằng chứng trước đó: bug demo TL1 → A (3/3 cụm); bug thật axi2apb → A; checker sai sync_fifo → B.

**Gói người duyệt (`work/review_packet.md`, `nnc/packet.py`).** `nnc report` tạo thêm một tài liệu, chỉ bằng code, chỉ gồm những điểm cần con người phán đoán:
- quyết định gate theo uỷ quyền;
- lỗi kèm kết luận triage;
- chỗ sửa tay;
- điều chưa kiểm được;
- mutant sống sót, kèm cấu hình đã chạy.

Cuối tài liệu là danh sách câu hỏi phải trả lời trước `G4_signoff`.

**Chi phí và quota.**
- Lời gọi agent bị chặn vì hết quota sẽ tự đợi tới giờ reset ghi trong thông báo, rồi gọi lại (`NNC_LIMIT_WAIT`, mặc định 6 giờ).
- Report tách riêng tiền của các lần gọi thất bại. Tổng là US$8,4 trên 5 thiết kế: ba lần sinh test (A7) bị cắt giữa chừng sau khoảng 20 phút, cộng một lần timeout.
- Đề xuất còn để ngỏ: tách A7 thành một module testbench chung cộng các lời gọi nhỏ theo nhóm check, để một lần ngắt chỉ mất một nhóm. Việc này thay đổi bố cục test và cần sinh lại, duyệt lại test của mọi thiết kế.

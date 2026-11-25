# Kế hoạch các giai đoạn tiếp theo (từ 2026-11-21)

Trang này liệt kê các bước của giai đoạn 17 đến 22. Mỗi bước có **điều kiện xong** kiểm được bằng lệnh. Một bước chỉ được đánh dấu xong khi điều kiện đó đúng.

Các ràng buộc sau vẫn giữ nguyên:
- **Không ai ký G4 thay người có chuyên môn.** Claude không ký G4.
- Không sửa RTL, test, assertion hay giá trị kỳ vọng được giao chỉ để cho qua. Không nới check.
- Không báo gì cho tác giả upstream.
- Các tài liệu chuẩn có bản quyền (`specs/*.pdf`, `designs/axi_std/`) không đưa vào git.
- Từ 2026-11-21, người dùng cho phép push thẳng lên `main` mỗi bước đã xong và đã kiểm ("mọi bước chạy qua cứ push lên main nếu hoàn thiện"). Không push việc còn hỏng.

## Giai đoạn 17: đóng gói để người khác cài và chạy được

**Trạng thái (2026-11-21):** 17.1–17.6 xong, xem [CHANGELOG.md](../CHANGELOG.md) mục 0.2.0. Cụ thể:
- wheel có đủ `nnc/data/*.md` và `nnc/simlib/nnc_cocotb.py`;
- cài trong venv sạch trên WSL: `nnc --version` in 0.2.0, `nnc doctor` PASS, và `nnc kit-check ot_rv_timer` chạy từ ngoài repo ra SAME OUTCOME;
- CI có job `install`;
- có lệnh `nnc review-kit` và `nnc summary`.

17.7 xong: CI xanh, `main` đã được đưa lên commit 4666c59 (2026-11-21), theo lời người dùng.

**Mục tiêu.** Một máy mới chạy `pip install` từ repo là có lệnh `nnc` chạy được, không cần mở mã nguồn.

| # | Bước | Điều kiện xong |
|---|---|---|
| 17.1 | Đưa file dữ liệu vào gói. Hiện `nnc/gen_rtl.py` đọc `docs/RTL_RULES.md` và `nnc/specdraft.py` đọc `docs/SPEC_TEMPLATE.md` bằng đường dẫn ra ngoài gói. `nnc/simlib/` lại không có `__init__.py`, nên `nnc_cocotb.py` không vào wheel. Cách sửa: chép hai file `.md` vào `nnc/data/` (bản trong `docs/` vẫn là bản gốc, và một unit test kiểm hai bản giống nhau), đọc qua `importlib.resources`, rồi khai báo `package-data` trong `pyproject.toml`. | `python -m build` tạo wheel. `unzip -l` cho thấy wheel có `nnc/data/*.md` và `nnc/simlib/nnc_cocotb.py`. |
| 17.2 | Kiểm tra cài sạch: tạo venv mới, cài wheel (không dùng `-e`), chạy `nnc doctor` và `nnc kit-check sync_fifo` từ một thư mục ngoài repo. | Cả hai lệnh trả mã 0. Ghi lại lệnh vào CI thành một job `install`. |
| 17.3 | Phiên bản `0.2.0` trong `pyproject.toml`, và `nnc --version`. | `nnc --version` in `0.2.0`. |
| 17.4 | `CHANGELOG.md`: liệt kê theo giai đoạn 1–17, mỗi giai đoạn trỏ tới mục tương ứng trong `docs/EVALUATION.md`. | File có mục `0.2.0`. |
| 17.5 | Bảng thiết kế trong `README.md`: cả 12 thiết kế, mỗi dòng ghi test, formal, mutation và trạng thái G4 (luôn là "chưa ký"). | Số trong bảng khớp `work/report.json` của từng thiết kế. Một unit test so hai nguồn này. |
| 17.6 | Lệnh `nnc review-kit <ip>`: gom vào một thư mục `review_kit/` (hoặc một file `.zip`) mọi thứ người duyệt G4 cần cho một thiết kế, không cần chạy công cụ: review packet, report, spec, rules, contract, formal và triage, mutation kèm kết quả tương đương, NOTICE, trace VCD của các phản ví dụ, và một `CHECKLIST.md` chứa các câu hỏi lấy từ `docs/G4_REVIEW_REQUEST.md`. Lệnh không chép tài liệu chuẩn có bản quyền. | Unit test: kit có đủ các file, không có file nào trong `spec/standards/` mà NOTICE không cho phép chép, và `CHECKLIST.md` có ô ký trống. |
| 17.7 | CI xanh trên nhánh, rồi **hỏi người dùng** trước khi mở PR vào `main`. | CI xanh. Người dùng trả lời. |

## Giai đoạn 18: đo kết quả trên thiết kế công nghiệp thứ hai, đo độ ổn định

**Mục tiêu.** Kiểm xem kết quả của OpenTitan rv_timer có lặp lại được không, và đo xem các agent cho kết quả ổn định đến đâu.

| # | Bước | Điều kiện xong |
|---|---|---|
| 18.1 | Chọn IP OpenTitan thứ hai có tham số, ví dụ `gpio` hoặc `pattgen`, để có nhiều cấu hình. Ghi NOTICE (Apache-2.0) như với rv_timer. | `nnc spec-lint` chạy xong. Các quyết định spec D-xxx được ghi lại. |
| 18.2 | Chạy flow đầy đủ đến G3, kể cả formal (slang) và mutate-equiv. | `work/report.md` có đủ mọi mục. |
| 18.3 | So với testbench UVM của OpenTitan, chỉ dùng số liệu công khai (coverage của họ). Không chép testbench vào repo. | Một bảng so sánh trong EVALUATION. |
| 18.4 | Độ ổn định: chạy lại `extract` và `plan` 3 lần trên cùng một thiết kế nhỏ, rồi đo mức trùng nhau của rules và checks. Đo trước chi phí của một lần chạy và hỏi người dùng nếu vượt ngân sách. | Một bảng độ trùng trong EVALUATION. |

**Trạng thái (2026-11-21):**
- 18.1 xong: `designs/ot_gpio`, gồm 19 gap của spec-lint, quyết định D-001..D-022, 268 rules và 38 checks. G1 và G2 đã duyệt theo uỷ quyền.
- 18.4 xong: [EVALUATION §10](EVALUATION.md), [designs/uart_lite/stability/](../designs/uart_lite/stability/README.md).
- 18.2 xong ([EVALUATION §11](EVALUATION.md)):
  - mô phỏng: 26/26 test và 13/13 assertion ở 5 lần chạy;
  - formal: 10 PROVEN, không còn phản ví dụ;
  - mutation: 58,3 %, bỏ các mutant tương đương thì còn 77,8 %;
  - 4 lỗi verification do A17 sửa, không có sửa tay.
- 18.3 xong: §11.2.
- 18.5 xong: §11.1.
- 17.7 xong.

Chi phí giai đoạn 18: khoảng US$23 (độ ổn định US$5.2, ot_gpio US$17.9). **Dừng và hỏi người dùng nếu tổng vượt khoảng US$50.**

### Việc làm tiếp khi `gen-env` của ot_gpio chạy xong (chi tiết của 18.2)

| # | Bước | Điều kiện xong |
|---|---|---|
| 18.2.1 | Kiểm `verif/formal/nnc_env.sv`: các giả định phải lấy từ D-014, D-016, D-017, D-022 (`i_a_valid` = 0 trong reset và chu kỳ đầu sau reset, `a_param` = 0, không viết lệnh có `i_a_instr` = 1). Không giả định nào được ràng buộc output của DUT. | Lint sạch. Mỗi `assume` trỏ tới một rule hay một quyết định D-xxx. |
| 18.2.2 | Duyệt G3 theo uỷ quyền (`--by "Claude (delegated by GabrielHCMUT)"`, ghi chú "Not a hardware designer's review"). Trước đó đọc lướt SVA và test, so với D-xxx: các cửa sổ "không kiểm" (D-004, D-005, D-007, D-017) phải được tôn trọng. Nếu checker kiểm cái mà quyết định nói là không kiểm thì không duyệt, mà sửa theo loại B. | `nnc status ot_gpio` cho thấy G3 đã duyệt. |
| 18.2.3 | Mô phỏng cả run set: `base` (seed 1, 2), `sync_off`, `straps_off`, `min`. | Có `work/results.json` gộp đủ 5 lần chạy. |
| 18.2.4 | `nnc triage`. Loại B (verification sai): chạy `nnc fix-verif`, nếu chưa được thì sửa tay và ghi vào NOTICE. Loại A (RTL OpenTitan sai): ghi lại, **không sửa RTL**. Loại C (spec không rõ): **dừng và hỏi người dùng**. Loại E: đưa vào bước 18.2.5. | Mọi lỗi đều có loại. Không còn lỗi loại B nào chưa sửa. |
| 18.2.5 | Chạy formal (slang, depth 32) cho từng cấu hình. Phản ví dụ loại E được đưa lại cho A13 (`gen-env`), tối đa 2 vòng. | Có `work/formal.md`. Mọi CEX đều đã được phân loại. |
| 18.2.6 | `nnc mutate`, rồi `nnc mutate-equiv` cho các mutant sống sót. Lệnh này lưu sau từng mutant, nên bị ngắt thì chạy lại để làm tiếp. | `work/mutation.json` có điểm mutation và mục `equivalence`. |
| 18.2.7 | `nnc report`, `nnc review-kit ot_gpio`, `nnc kit ot_gpio`, rồi `kit-check` trên WSL. | `work/report.md` đủ mọi mục. Kit cho kết quả SAME OUTCOME. |
| 18.2.8 | Cập nhật tài liệu: EVALUATION §11 (gpio), ARCHITECTURE §25, một mục ot_gpio trong G4_REVIEW_REQUEST (các câu hỏi cho người duyệt), bảng README (`nnc summary --readme README.md`), CHANGELOG, và ot_gpio trong ma trận CI (kit, kit-configs, formal). | Unit test bảng README qua. Mọi unit test qua. |
| 18.2.9 | Commit và push, chờ CI. **Không ký G4.** | CI xanh trên nhánh. |

### Sau 18.2

| # | Bước | Điều kiện xong |
|---|---|---|
| 18.3 | So với testbench UVM của OpenTitan cho gpio và rv_timer, chỉ dùng số liệu công khai (dashboard coverage, danh sách test trong testplan `.hjson`). Không chép testbench vào repo, chỉ ghi nguồn và commit tham chiếu. Nói rõ hai bên đo những thứ khác nhau: coverage của họ khác mutation score của mình. | Một bảng so sánh trong EVALUATION. |
| 18.5 | So rv_timer với gpio: tỉ lệ lỗi verification loại B, số quyết định D-xxx cần đến, chi phí agent, điểm mutation. Từ đó kết luận kết quả của rv_timer có lặp lại được không. | Một đoạn kết luận trong EVALUATION §11. |
| 17.7 | **Hỏi người dùng** có mở PR từ `feature/phase-12-17` vào `main` không. | Người dùng trả lời. |

## Giai đoạn 19: coverage đúng phạm vi và cao hơn

**Mục tiêu.** Coverage chỉ đếm phần có trong thiết kế, không loại bằng tay, và phần còn thiếu được bù bằng test mới. Xem [SIGNOFF_SCOPE.md](SIGNOFF_SCOPE.md).

| # | Bước | Điều kiện xong |
|---|---|---|
| 19.1 | Phạm vi coverage do công cụ tính: hàm package không được gọi (`verilator --json-only`), bit hằng số (Yosys). Điểm đã chạy thì vẫn tính. Tín hiệu mà hai công cụ mâu thuẫn thì tính nguyên. | Unit test. `scope_conflicts` = 0 trên mọi thiết kế. Báo cáo ghi số trên mọi điểm bên cạnh. |
| 19.2 | Con số phụ "không tính module đã verify riêng" (`coverage_preverified`), theo danh sách cover.cfg của OpenTitan. | Hai IP OpenTitan có thêm dòng trong báo cáo. |
| 19.3 | Closure bằng agent (A10/A11) cho các metric dưới 90 % (mốc V2 của OpenTitan), ưu tiên toggle và functional của gpio và rv_timer. Test mới thêm vào, không bỏ test cũ. G3 duyệt lại theo uỷ quyền. | Metric đạt 90 %, hoặc phần còn lại được giải thích (không đạt được bằng kích thích hợp lệ). |
| 19.4 | Một cấu hình run set với giá trị khởi tạo ngẫu nhiên (`--x-initial unique`, `+verilator+rand+reset+2`) để lộ flop thiếu reset. | Cấu hình chạy trên ít nhất một thiết kế. Kết quả được ghi lại. |
| 19.5 | (Sau) Chứng minh unreachable bằng formal cho các điểm mà lan truyền hằng số không chứng minh được, ví dụ bit cao của phép trừ. | Điểm chỉ bị loại khi có bằng chứng PROVEN. |

**Trạng thái (2026-11-21):** 19.1 và 19.2 xong.
- gpio: line 52,5 % → 96,5 %, block 44,5 % → 93,6 %, toggle 84,0 % → 87,5 %.
- rv_timer: line 24,2 % → 92,3 %, block 29,6 % → 87,8 %, toggle 80,3 % → 83,1 %.
- sync_fifo: toggle 70,6 % → 87,7 %.
- 19.3 làm một phần.
  - gpio: functional 90 → 95 % (2 test). Toggle không thêm được test: 18 lời khẳng định unreachable, người duyệt cần xem.
  - axi2apb: toggle 75,1 → 86,4 % (6 test).
  - rv_timer: chưa chạy closure, vì phần còn thiếu là nhánh có điều kiện hằng, chờ 19.5.
- 19.4: xong (2026-11-24). Sửa ba lỗi của bộ chạy ở thời điểm 0 (input, checker ở cạnh clock đầu, cạnh reset). Thử trên 15 thiết kế: 14 giống bản ghi, ahb2axi_bridge fail thêm CHK-012, nhiều khả năng là triệu chứng mới của lỗi RTL đã có trong bản ghi. uart_lite có cấu hình `xrand` trong run set. gen_sync_fifo không có lỗi riêng của x_init (test đó đã fail trong bản ghi).
- 19.5: xong (2026-11-24). `nnc sim --unr` chứng minh bằng SymbiYosys rằng một bit toggle chưa phủ không thể đổi sau reset đầu tiên (input tự do). Chỉ bit PROVEN trong mọi cấu hình mới bị loại.
  - Mỗi task có guard (pha kiểm phải tới được) và control (một flop mà mô phỏng đã toggle phải đổi được trong model). Nếu một trong hai không FAIL thì task không kết luận gì. Hai cơ chế này bắt được lỗi proof rỗng của bản đầu (một clock: bộ đếm cạnh không bao giờ đếm).
  - Toggle: sync_fifo 87,7 → 100 %, axi2apb 86,4 → 100 %, ahb2axi 75,9 → 84,1 %, gpio 87,5 → 89,6 %, rv_timer 83,1 → 83,9 %. c_uart: 48 counterexample, không loại bit nào. Test và check của 13 thiết kế không đổi.
  - Chưa làm (giai đoạn 23): trường struct, hai thiết kế bất đồng bộ (Yosys không đọc được model đồng bộ chỉ dùng trong mô phỏng), điểm line/block.

## Giai đoạn 20: kiểm tra cắt miền clock/reset (CDC/RDC)

**Mục tiêu.** Biến RR-33 (tín hiệu sang miền khác phải qua bộ đồng bộ) từ "người xem" thành "code kiểm".

| # | Bước | Điều kiện xong |
|---|---|---|
| 20.1 | `nnc cdc`: kiểm cấu trúc trên netlist Yosys cho từng cấu hình. Các loại kết quả: SYNC, SYNC_MULTIBIT, QUALIFIED, UNSYNC, FIRST_STAGE_READ, và reset từ miền khác. | Unit test với netlist dựng tay. |
| 20.2 | Chứng minh bước kiểm bắt được lỗi: làm hỏng bộ đồng bộ trong một bản sao của async_gray_fifo. | Hai lỗi cài vào đều bị báo là vi phạm. |
| 20.3 | Chạy trên 13 thiết kế. Báo cáo có dòng CDC và điều kiện sign-off. CI có job `cdc`. | 11 sạch, 2 cần review (async_gray_fifo, async_apb_bridge), 0 lỗi. Job CI xanh. |

**Trạng thái (2026-11-21):** 20.1–20.3 xong.

## Giai đoạn 21: đầu vào bất kỳ (spec và RTL không do flow viết)

**Câu hỏi.** "Hệ thống có chạy tốt với mọi spec và mọi code đầu vào không?"

**Mục tiêu.** Không công cụ nào hứa được "mọi". Flow được thiết kế để **không input nào cho ra kết quả sai mà không ai biết**:
- mỗi input nhận một trong bốn kết luận trước khi agent chạy;
- input nào cần chỉnh thì được chỉnh bằng code sinh tự động và có ghi lại;
- mức bao phủ được đo trên RTL mã nguồn mở mà flow chưa từng thấy.

Xem [INPUT_SUPPORT.md](INPUT_SUPPORT.md).

| # | Bước | Điều kiện xong |
|---|---|---|
| 21.1 | `nnc intake` (không agent): tìm file mà top cần qua các thư mục thư viện, chạy 4 công cụ (Verilator lint, cây elaborate, Yosys, yosys-slang), phân loại port, tìm clock và reset từ netlist, kiểm spec. Kết luận: ready / adapt / needs_input / unsupported. | Unit test. Cả 13 thiết kế đều ready. |
| 21.2 | `nnc adapt`: chép file thư viện vào rtl/, sinh wrapper chỉ nối dây cho port struct và mảng (dừng ở thời điểm 0 nếu layout đổi), sinh tài liệu interface (vai trò `interface`: contract đọc, agent trích luật không đọc). | gpio gốc của OpenTitan (7 port struct): wrapper lint sạch, mô phỏng chạy, contract đọc lại đúng bảng port. |
| 21.3 | Corpus: 6 kho mã nguồn mở, commit cố định, mỗi module là một top. Chạy intake, adapt, contract, kiểm port và mô phỏng khói (`--smoke`). | `corpus/results.md`. Mỗi lần dừng đều có lý do. Job CI `corpus`. |
| 21.4 | Sửa các lỗi flow mà corpus tìm ra: port trong `` `ifdef ``, port kiểu người dùng, thiết kế không có clock (clock ảo `nnc_clk`), reset bất đồng bộ trong netlist của slang, `import` trong header module, chỉ số bit âm (`[-1:0]`), tham số rộng hơn 32 bit hoặc kiểu enum, vector clock. | 13 thiết kế cũ cho kết quả y hệt (dut_ports, tb_top, interface). |
| 21.5 | Spec: đọc Word `.docx` và HTML (cả bảng), báo lỗi PDF scan, nhận từ khoá bắt buộc tiếng Việt. | Unit test. |
| 21.6 | (Tốn tiền agent, hỏi trước) Chạy mù end-to-end bằng agent trên vài thiết kế của corpus, không chỉnh tay. Ghi mọi lần phải can thiệp. | `work/blind_run.md` của từng thiết kế, EVALUATION §14. |

**Trạng thái:** 21.1–21.6 xong (2026-11-23). Corpus: 238 module, 232 chạy tới testbench. Trong đó 219 đạt mô phỏng khói. 13 bị assertion của chính thiết kế dừng lại, vì input ngẫu nhiên vi phạm luật input của nó. Còn lại: 2 dùng cấu trúc Verilator không hỗ trợ, 3 cần thêm đầu vào, 1 không hỗ trợ (VHDL), 0 lỗi flow. 21.6 (người dùng đồng ý): chạy mù 3 module, tổng 5,40 USD. c_pcpi_div: 9/9 check PASS, mutation 100 %. c_uart: 6/11 PASS; 4 lỗi loại C (README không nói rõ word nào bị bỏ khi overrun), người dùng chọn để mở cho người duyệt G4. c_axil_ram: tài liệu không mô tả hành vi, flow ra 0 luật và dừng. Lỗi flow tìm ra và đã sửa: reset đồng bộ (`opt_dff`), đọc AsciiDoc, tiêu đề setext, intake của thiết kế đã adapt.

## Giai đoạn 22: chạy thử trong một lệnh (Docker, demo không cần agent)

**Câu hỏi.** Người khác (nhà tuyển dụng, người review, một lab) muốn chạy thử dự án. Hiện họ phải tự cài Python,
cocotb, OSS CAD Suite đúng phiên bản, và WSL nếu dùng Windows. Việc này mất từ 30 phút đến vài giờ và dễ lệch
phiên bản.

**Mục tiêu.** Có một image Docker chứa đủ công cụ, đúng phiên bản CI đang dùng (`OSS_CAD_SUITE` 2026-11-07,
cocotb 2.1.0). Lệnh `nnc demo <ip>` chạy lại các bước không cần agent từ những gì đã commit, rồi so với kết quả đã
ghi. Giai đoạn này không tốn tiền agent.

**Không làm.** Không làm platform web cho người lạ tải RTL lên chạy. Lý do: phải trả tiền agent cho họ, phải chạy
code lạ trong sandbox, và người dùng thật của công cụ quen dòng lệnh và CI hơn.

| # | Bước | Điều kiện xong |
|---|---|---|
| 22.1 | `Dockerfile` ở gốc repo. Base `ubuntu:24.04`. OSS CAD Suite tải theo đúng tag của CI và kiểm SHA-256. Python 3.12 và `cocotb==2.1.0`. Cài `nnc` từ wheel của repo, không dùng `-e`. Chạy bằng user thường, không root. File `.dockerignore` loại `.git`, `corpus/.cache`, `designs/*/work/cache`, `specs/` và `designs/axi_std/`. | `docker build` thành công. `docker run <image> nnc doctor` in PASS. `verilator --version` trong image giống job `kit` của CI. |
| 22.2 | Trong container, `simhost` chạy công cụ tại chỗ, không qua WSL. Kiểm lại cách `default_host()` chọn host khi không có WSL. | Trong container, `nnc kit-check sync_fifo` ra SAME OUTCOME. |
| 22.3 | Lệnh `nnc demo <ip>` (không agent), chạy lần lượt: `intake --check`, `make regression` của kit, `kit-check`, `cdc --check`, và `formal-check` nếu có cờ `--formal` (vì formal chạy lâu). In bảng tóm tắt từng bước (SAME / DIFFERENT / thời gian) và đường dẫn tới `work/report.md`. Trả mã 0 chỉ khi mọi bước SAME. Không bao giờ gọi agent: nếu một bước cần agent thì báo và dừng. | Unit test cho danh sách bước và cho mã trả về. Trong container: `nnc demo sync_fifo` và `nnc demo ot_gpio` đều ra SAME, mỗi lệnh dưới 15 phút khi không có `--formal`. |
| 22.4 | **Điểm quyết định (hỏi người dùng).** Có commit cache câu trả lời agent (`designs/*/work/cache/`, khoảng 640 KB mỗi thiết kế, khoảng 8 MB cho 13 thiết kế) để phát lại cả các bước agent từ một bản clone sạch hay không? Trước khi commit phải quét cache: không chứa nội dung chuẩn có bản quyền (axi_std đã bị loại), không chứa token hay email. | Quyết định được ghi ở đây. Nếu đồng ý: `nnc flow sync_fifo` trên bản clone sạch chạy với 0 lần gọi agent và ra đúng các file đã commit. |
| 22.5 | Job CI `docker`: build image, chạy `nnc demo` trên 2 thiết kế bên trong image. Việc đẩy image lên GitHub Container Registry để ai cũng `docker pull` được là công khai ra ngoài, nên **hỏi người dùng trước**. | Job CI xanh. Nếu được phép đẩy: `docker pull ghcr.io/...` rồi `nnc demo sync_fifo` chạy được trên một máy khác. |
| 22.6 | `.devcontainer/devcontainer.json` dùng image này, để mở repo trong GitHub Codespaces hoặc VS Code Dev Containers là có sẵn công cụ. Người dùng tự dùng API key của họ nếu muốn chạy agent. | Container dựng được (kiểm trên CI bằng `devcontainers/ci`). Trong đó, `nnc demo sync_fifo` ra SAME. |
| 22.7 | README có mục "Chạy thử trong một lệnh / Run it in one command" (EN/VI). GUIDE có cách dùng Docker và Codespaces. CHANGELOG có mục 0.6.0. | README có các lệnh đúng như đã chạy ở 22.1–22.6. CI xanh. Push lên `main`. |

**Thứ tự và điểm dừng.**
- Làm 22.1, 22.2, 22.3, 22.5 (phần build và chạy trên CI), 22.6, rồi 22.7, sau đó push lên `main`.
- Hai việc phải dừng để hỏi người dùng: 22.4 (commit cache agent) và phần đẩy image công khai của 22.5.
- Nếu người dùng chưa trả lời, hai việc đó để mở. Phần còn lại vẫn xong và push được.

**Sau giai đoạn 22**, các việc chưa làm, theo thứ tự đề xuất:
1. Trang GitHub Pages: xong (`nnc site`, job CI `pages`, https://thvkhang.github.io/NNC_Pipeline/).
2. 19.4: xong.
3. 19.5: xong (xem giai đoạn 19).
4. 21.6: xong (xem giai đoạn 21).
5. Tiếp theo: giai đoạn 23.

**Trạng thái (2026-11-23):** 22.1–22.7 xong. Những gì đã kiểm:
- Image `Dockerfile` nặng khoảng 3 GB. Các công cụ FPGA flow không dùng đã bị bỏ.
- Trong container: `nnc doctor` PASS. `nnc demo sync_fifo ot_gpio --replay` cho kết quả SAME ở mọi bước, mất khoảng 2 phút.
- `nnc demo sync_fifo --formal` trong container: SAME (7 PROVEN, 2 BOUNDED, 1 TIMEOUT, 1 UNSUPPORTED, giống bản đã ghi), khoảng 11 phút.
- 22.4: người dùng đồng ý ("làm hết tất cả các bước"). Cache câu trả lời agent của 13 thiết kế đã được commit: 788 file, đã quét không có key, email hay đường dẫn máy. axi_std vẫn bị loại.
- Kết quả replay:
  - trích luật và review SAME trên 11 thiết kế có chạy hai bước này;
  - contract SAME trên 9 thiết kế;
  - async_apb_bridge, axi2apb_bridge, gen_apb_tlul_bridge, gen_sync_fifo bị NOT_CACHED ở contract, vì prompt đã đổi sau lần chạy gốc;
  - hai thiết kế `gen_*` không tự trích luật (luật dẫn xuất bằng `nnc derive`), nên bỏ qua.
- Các bước viết code không replay, vì file đã commit có thêm các sửa chữa của A17.
- 22.5: người dùng cho phép đẩy image lên GHCR. Job CI `docker` đẩy image mỗi lần push lên main.

## Giai đoạn 23: phần coverage còn lại sau 19.5, và x_init cho mọi thiết kế

**Mục tiêu.** Làm nốt những chỗ 19.4 và 19.5 chưa làm được. Mỗi bước có điều kiện xong đo được, và không bước nào loại điểm coverage bằng tay.

| # | Bước | Điều kiện xong |
|---|---|---|
| 23.1 | Tên trường struct. Verilator đặt tên riêng cho từng trường của struct (`tl_h2d.a_address`), còn Yosys chỉ có một net packed. Ghép hai cách đặt tên nhờ bố cục struct trong `verilator --json-only`. Dùng cho cả bit hằng (19.1) và UNR (19.5). | Unit test. Trên ot_gpio và ot_rv_timer, số tín hiệu "không có trong netlist" của `work/unr.md` giảm. Outcome không đổi. |
| 23.2 | UNR cho thiết kế có model chỉ dùng trong mô phỏng mà Yosys không đọc được (bộ đồng bộ ngẫu nhiên của async_gray_fifo và async_apb_bridge). Hướng làm: đọc bằng yosys-slang. Nếu dùng macro tổng hợp thì phải chứng minh phần bị thay không ảnh hưởng tới bit cần chứng minh. | Có kết quả UNR, hoặc ghi rõ vì sao không làm được. |
| 23.3 | UNR cho điểm line/block (nhánh chưa chạy). Chèn `assert` vào nhánh đó trong một bản sao của RTL (vị trí lấy từ cây JSON của Verilator), rồi chứng minh bằng SymbiYosys, vẫn có guard và control. Ví dụ: nhánh `if (EnableRacl)` của gpio, `reinit_i`. | Unit test. Điểm chỉ bị loại khi PROVEN. |
| 23.4 | x_init trong run set của mọi thiết kế: thêm cấu hình `xrand` và ghi vào bản ghi. | Mỗi thiết kế thêm 1–2 lần chạy. Kết quả của các cấu hình cũ không đổi. |
| 23.5 | Closure rv_timer (phần còn lại của 19.3) bằng agent A10/A11, làm sau 23.1. | Tốn tiền agent: hỏi người dùng trước. |
| 23.6 | Triage CHK-012 của ahb2axi_bridge dưới x_init, để xác nhận đây là triệu chứng của lỗi RTL đã ghi. | Tốn tiền agent: hỏi người dùng trước. |

**Thứ tự đề xuất.** 23.1 → 23.2 → 23.4 → 23.3. 23.5 và 23.6 chờ người dùng đồng ý chi phí. G4 vẫn chờ người có chuyên môn.

**Trạng thái (2026-11-24).** Kết quả ở EVALUATION §15.
- 23.1, 23.2, 23.4, 23.3: xong.
  - Block coverage: ahb2axi 77,1 → 97,1 %, rv_timer 87,8 → 99,3 %, gpio 93,6 → 99,5 %.
  - Không nhánh PROVEN nào từng chạy trong mô phỏng. Test và check không đổi.
- 23.5 và 23.6: người dùng đã đồng ý chi phí ("ok, xong thì làm tiếp 23.5 và 23.6").
- 23.5: xong, nhưng chưa đạt mục tiêu (US$3,44).
  - Expression của rv_timer (không tính `prim_*`) tăng 83,7 → 87,4 % nhờ 4 test mới; 27/27 test pass.
  - Mục tiêu 90 % chưa đạt: agent cho rằng 10 nhóm điểm không tới được từ port (input bị buộc hằng, lỗi integrity mà port không tạo được). Các điểm này vẫn được tính.
  - Việc có thể làm tiếp: chứng minh formal cho điểm expression, giống cách 23.3 làm cho nhánh.
  - G3 đã duyệt lại (ủy quyền).
- 23.6: xong (US$1,19).
  - Agent triage kết luận A_rtl_wrong, cùng gốc với lỗi RTL số 2 đã ghi: `w_cap_stop` không theo trạng thái, nên lệnh ghi đơn đọc AWADDR/AWSIZE từ bảng burst không có reset.
  - Không phải lỗi mới. Kết quả ở `work/triage_xrand_chk012.md`.
- Lưu ý: đường burst AXI của ahb2axi bị loại vì chết do lỗi RTL đã ghi, không phải do thiết kế. Người duyệt G4 cần xét.

## Giai đoạn 24: chứng minh điểm expression không tới được

**Mục tiêu.** 23.5 để lại các điểm expression mà agent cho là "không tới được từ port", nhưng chưa có công cụ nào chứng minh. Giai đoạn này chứng minh chúng bằng formal, giống cách 23.3 làm cho nhánh. Không tốn tiền agent. Không loại điểm nào bằng tay.

| # | Bước | Điều kiện xong |
|---|---|---|
| 24.1 | `nnc/unrexpr.py`: mỗi tổ hợp term chưa chạy (`(de==1) => 1`) thành một wire đánh dấu ở mức module, trong một bản sao của RTL (chèn trước `endmodule`, không thêm dòng). Wire bằng 1 đúng khi tổ hợp đúng. SymbiYosys chứng minh wire luôn bằng 0 sau reset đầu tiên, vẫn có guard và control. Chỉ thử khi term đọc ở mức module có cùng nghĩa: không biến vòng lặp, không tên cục bộ của generate/function, không gọi hàm, không tín hiệu bị chính khối đó gán blocking. | Unit test. Điểm chỉ bị loại khi PROVEN ở mọi cấu hình. |
| 24.2 | Chạy trên ot_rv_timer. Xem từng nhóm điểm mà 23.5 cho là không tới được: nhóm nào được chứng minh, nhóm nào không. | `work/unr.md` có phần expression. Test và assertion không đổi. Không điểm PROVEN nào từng chạy trong mô phỏng (`expressions_executed` = 0). |
| 24.3 | Chạy trên mọi thiết kế có `work/unr.json`. | Như 24.2, trên mỗi thiết kế. |
| 24.4 | EVALUATION, ARCHITECTURE, GUIDE, CHANGELOG. Push lên `main`. | CI xanh. |

**Trạng thái (2026-11-25).** 24.1–24.4 xong, kết quả ở EVALUATION §16. Không tốn tiền agent.
- rv_timer: 27 điểm PROVEN. Expression (không tính `prim_*`) 87,4 → 91,3 %, `nnc cover` báo `target_met` mà không thêm test. Phần lớn nhóm điểm agent cho là không tới được ở 23.5 nay đã được chứng minh. Nhóm `de` của `prim_subreg_arb.sv:33` có phản ví dụ (các instance gộp chung một điểm), RACL và các hàm `mubi4_*` chưa thử được: vẫn được tính.
- ahb2axi 71,9 → 82,9 %, sync_fifo 92,8 → 98,5 %, axil_regfile 95,7 → 100 %, gpio 64,9 → 85,0 %.
- Mọi thiết kế: `expressions_executed` = 0, test và assertion không đổi.
- Sửa trong lúc chạy: gpio có 616 marker trên một dòng, vượt giới hạn 40 000 token của Verilator. Marker giờ được chia đợt. Yosys không đọc phép chọn bit nối tiếp mà Verilator in cho trường struct (`reg2hw[321:312][3:2][0]`), nên marker gộp lại thành một phép chọn (`reg2hw[314]`).

| # | Việc còn mở | Điều kiện xong |
|---|---|---|
| 24.5 | Chứng minh theo từng cấu hình. Coverage tính mỗi điểm một lần cho mỗi cấu hình. Điểm chạm ở cấu hình này mà không chạm ở cấu hình kia hiện không được thử (async_apb_bridge: 223 điểm). Cần chứng minh điểm đó trong đúng cấu hình nó không chạm, rồi chỉ loại bản ghi của cấu hình đó. Áp dụng cho cả nhánh (23.3). | Unit test. `expressions_executed` = 0. |
| 24.6 | Thử thêm điểm mà 24 bỏ qua: term do khối tổ hợp gán blocking trước biểu thức (không gán lại sau nó), và tên mục enum khai báo ở mức module. | Unit test. `expressions_executed` = 0. |

**Trạng thái (2026-11-25).** 24.5 và 24.6 xong, kết quả ở EVALUATION §17. Không tốn tiền agent.
- async_apb_bridge expression 74,8 → 92,9 %, block 88,8 → 97,3 %. spi_master block và expression 100 %.
- rv_timer (cả thiết kế) 67,7 → 92,7 %, gpio 85,0 → 95,1 %. ahb2axi 82,9 → 86,4 % (FSM soft-reset của FIFO và trạng thái burst chết vì lỗi RTL số 2; người duyệt G4 cần xét).
- Mọi thiết kế: `expressions_executed` = `branches_executed` = 0, test và assertion không đổi.
- Còn chưa thử: term gọi hàm (`mubi4_*`), đọc biến vòng lặp hoặc hằng cục bộ của generate, chọn bit của mảng không phải `[H:0]` (RACL).

## Việc còn mở, chờ người có chuyên môn (G4)

Xem [G4_REVIEW_REQUEST.md](G4_REVIEW_REQUEST.md). Riêng ot_rv_timer còn hai việc:
- CHK-008: TL-UL host có được gửi mask không liền khối (non-contiguous) không;
- CHK-011: formal hết giờ.

# Kế hoạch các giai đoạn tiếp theo (từ 2026-11-21)

Trang này liệt kê các bước của giai đoạn 17 và 18. Mỗi bước có **điều kiện xong** kiểm được bằng lệnh. Một bước chỉ được đánh dấu xong khi điều kiện đó đúng.

Các ràng buộc sau vẫn giữ nguyên:
- **Không ai ký G4 thay người có chuyên môn.** Claude không ký G4.
- Không sửa RTL, test, assertion hay giá trị kỳ vọng được giao chỉ để cho qua. Không nới check.
- Không báo gì cho tác giả upstream.
- Các tài liệu chuẩn có bản quyền (`specs/*.pdf`, `designs/axi_std/`) không đưa vào git.
- Mở PR hay merge thì phải hỏi người dùng trước.

## Giai đoạn 17: đóng gói để người khác cài và chạy được

**Trạng thái (2026-11-21):** 17.1–17.6 xong, xem [CHANGELOG.md](../CHANGELOG.md) mục 0.2.0. Cụ thể:
- wheel có đủ `nnc/data/*.md` và `nnc/simlib/nnc_cocotb.py`;
- cài trong venv sạch trên WSL: `nnc --version` in 0.2.0, `nnc doctor` PASS, và `nnc kit-check ot_rv_timer` chạy từ ngoài repo ra SAME OUTCOME;
- CI có job `install`;
- có lệnh `nnc review-kit` và `nnc summary`.

17.7 (PR vào `main`) chờ người dùng đồng ý.

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
- Còn lại: 17.7 (PR vào `main`), chờ người dùng.

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

## Việc còn mở, chờ người có chuyên môn (G4)

Xem [G4_REVIEW_REQUEST.md](G4_REVIEW_REQUEST.md). Riêng ot_rv_timer còn hai việc:
- CHK-008: TL-UL host có được gửi mask không liền khối (non-contiguous) không;
- CHK-011: formal hết giờ.

# Kế hoạch các giai đoạn tiếp theo (từ 2026-11-21)

Trang này liệt kê các bước của giai đoạn 17 và 18. Mỗi bước có **điều kiện xong** kiểm được bằng lệnh. Một bước chỉ được đánh dấu xong khi điều kiện đó đúng.

Các ràng buộc sau vẫn giữ nguyên:
- **Không ai ký G4 thay người có chuyên môn.** Claude không ký G4.
- Không sửa RTL, test, assertion hay giá trị kỳ vọng được giao chỉ để cho qua. Không nới check.
- Không báo gì cho tác giả upstream.
- Các tài liệu chuẩn có bản quyền (`specs/*.pdf`, `designs/axi_std/`) không đưa vào git.
- Mở PR hay merge thì phải hỏi người dùng trước.

## Giai đoạn 17: đóng gói để người khác cài và chạy được

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

## Việc còn mở, chờ người có chuyên môn (G4)

Xem [G4_REVIEW_REQUEST.md](G4_REVIEW_REQUEST.md). Riêng ot_rv_timer còn hai việc:
- CHK-008: TL-UL host có được gửi mask không liền khối (non-contiguous) không;
- CHK-011: formal hết giờ.

# Bug demonstration / Minh hoạ bắt lỗi

**EN:** One realistic bug was injected into a **copy** of the RTL ([injected_bug.diff](injected_bug.diff)): the response check no longer compares `d_source` with `PARA_SRC_ID`, which breaks REQ-ERR-005. The unchanged checkers and tests of this design were run on the copy, then the triage agent analysed the failures. The delivered RTL in `../rtl/` is the original.

**VI:** Một bug thực tế được chèn vào **bản copy** của RTL ([injected_bug.diff](injected_bug.diff)): bỏ phép so sánh `d_source` với `PARA_SRC_ID`, vi phạm REQ-ERR-005. Checker và test của thiết kế (không sửa) được chạy trên bản copy, rồi agent triage phân tích lỗi. RTL bàn giao trong `../rtl/` là bản gốc.

**Note / Ghi chú:** this demo ran with the previous generation of checkers and tests (unreviewed run, before the Gate 1 decisions); check IDs in `triage.md` refer to that generation. / Demo chạy với thế hệ checker và test trước (lần chạy chưa duyệt, trước các quyết định ở Gate 1); ID check trong `triage.md` thuộc thế hệ đó.

| Step / Bước | Result / Kết quả |
|---|---|
| Simulation ([results.json](results.json)) | 2 of 16 tests failed (`test_chk_021_random_scoreboard`: 209 scoreboard errors; `test_chk_028_wrong_opcode_source`: 33) and the SVA assertion **CHK-009** failed 156 times out of 6 931 activations: a wrong `d_source` completed with PSLVERR = 0 and the read data |
| Triage ([triage.md](triage.md)) | 3 analyses (2 tests + 1 assertion), all *most likely A: RTL wrong*, pointing at `rtl/m_tlul_if.sv:100`, quoting REQ-ERR-005, the `w_resp_err` definition, OP-004 and DEC-008, and giving the one-line fix; B (test wrong) and C (spec unclear) argued and rejected with evidence. US$0.63, 93 s, 22 turns, no access attempt outside the sandbox |

**EN — Found and fixed in the flow by an earlier run of this demo:** the SVA counter showed 0 failures although the bug was present, because a test stopped at its first failed check before the `|=>` consequent edge and the next test's reset cancelled the pending property. `reset_dut` now lets two clock edges pass before asserting reset; in the run above the assertion reports the bug as well.

**VI — Lỗi của flow được phát hiện và sửa nhờ lần chạy demo trước:** bộ đếm SVA báo 0 lỗi dù có bug, vì test dừng ở check thất bại đầu tiên trước cạnh clock mà `|=>` đánh giá, và reset của test sau huỷ property đang chờ. `reset_dut` nay cho 2 cạnh clock trôi qua trước khi reset; trong lần chạy trên, assertion cũng báo được bug.

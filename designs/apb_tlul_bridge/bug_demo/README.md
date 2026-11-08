# Bug demonstration / Minh hoạ bắt lỗi

**EN:** One realistic bug was injected into a **copy** of the RTL ([injected_bug.diff](injected_bug.diff)): the response check no longer compares `d_source` with `PARA_SRC_ID`, which breaks REQ-ERR-005. The approved checkers and tests of this design (unchanged) were run on the copy with `python -m nnc inject apb_tlul_bridge injected_bug.diff`, then the triage agent analysed the failures. The delivered RTL in `../rtl/` is the original.

**VI:** Một bug thực tế được chèn vào **bản copy** của RTL ([injected_bug.diff](injected_bug.diff)): bỏ phép so sánh `d_source` với `PARA_SRC_ID`, vi phạm REQ-ERR-005. Checker và test đã duyệt của thiết kế (không sửa) được chạy trên bản copy bằng `python -m nnc inject apb_tlul_bridge injected_bug.diff`, rồi agent triage phân tích lỗi. RTL bàn giao trong `../rtl/` là bản gốc.

Run of 2026-11-08 with the current generation of checkers and tests (G3 approved, including the closure module). / Lần chạy 2026-11-08 với thế hệ checker và test hiện tại.

| Step / Bước | Result / Kết quả |
|---|---|
| Simulation ([results.json](results.json), [sim.log](sim.log)) | 2 of 17 tests failed (`test_chk_020_wrong_opcode_source`, `test_chk_029_random_scoreboard`: a wrong `d_source` completed with PSLVERR = 0) and the SVA assertion **CHK-010** failed 2 times out of 3 554 activations. Line coverage unchanged (96.0 %). |
| Triage ([triage.md](triage.md)) | 3 analyses (2 tests + 1 assertion), all *most likely A: RTL wrong*, pointing at `rtl/m_tlul_if.sv:100` (line 99-100 of the patched copy), quoting REQ-ERR-005, the internal-signal definition and DEC-008, and giving the one-line fix; B (test wrong) and C (spec unclear) argued and rejected with evidence. US$0.60, 86 s, 24 turns, no access attempt outside the sandbox. |

**EN — Found and fixed in the flow by an earlier run of this demo:** the SVA counter showed 0 failures although the bug was present, because a test stopped at its first failed check before the `|=>` consequent edge and the next test's reset cancelled the pending property. `reset_dut` now lets clock edges pass before asserting reset; in the run above the assertion reports the bug as well.

**VI — Lỗi của flow được phát hiện và sửa nhờ lần chạy demo trước:** bộ đếm SVA báo 0 lỗi dù có bug, vì test dừng ở check thất bại đầu tiên trước cạnh clock mà `|=>` đánh giá, và reset của test sau huỷ property đang chờ. `reset_dut` nay cho vài cạnh clock trôi qua trước khi reset; trong lần chạy trên, assertion cũng báo được bug.

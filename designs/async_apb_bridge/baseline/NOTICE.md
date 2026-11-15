# Third-party material / Tài liệu của bên thứ ba

| Files | Source | Licence |
|---|---|---|
| `tb_apbcdc.sv` | [nguyenquanicd/VLSIT_ASIC_SOC_AI_SKILLS](https://github.com/nguyenquanicd/VLSIT_ASIC_SOC_AI_SKILLS), `common_rtl/004_AsyncAPBBridge/verification/`, commit `53407f297ce20d08533425a05ac2d729bd830481` (2026-11-08) | Apache-2.0 (`../LICENSE-Apache-2.0`) |

**EN:** The testbench files are unchanged copies of the verification the upstream author delivered with the RTL.
NNC Pipeline never shows them to its agents; they are used only by `nnc baseline` to compare the hand-written
testbench with the generated verification on the same faults (`bugs/bugs.json`). `baseline.json` (written for NNC
Pipeline) describes how the upstream script runs them: Icarus Verilog, the 16 configurations of `vlsit_run_sim.py quick`, each in the synthesis branch (`-DVLSIT_SYNTHESIS`) and in the metastable branch with `+APBCDC_MSYNC_SEED` 1, 2 and 3 (64 runs), with the random stimulus of the script (`make_stimulus`, `Random(1000 + n)`, 40 transfers; ported in `nnc/baseline.py`). A run passes with `SIM-BRANCH`, `RESULT PASS` and the assertion line with 0 failures.

**VI:** Các file testbench là bản sao nguyên vẹn của phần kiểm chứng mà tác giả gốc giao kèm RTL. NNC Pipeline không
bao giờ đưa chúng cho agent; chỉ lệnh `nnc baseline` dùng chúng để so sánh testbench viết tay với kiểm chứng được sinh
ra trên cùng các lỗi (`bugs/bugs.json`). `baseline.json` (viết cho NNC Pipeline) mô tả cách script gốc chạy chúng:
Icarus Verilog, 16 cấu hình của `vlsit_run_sim.py quick`, mỗi cấu hình chạy nhánh synthesis (`-DVLSIT_SYNTHESIS`) và nhánh metastable với `+APBCDC_MSYNC_SEED` 1, 2, 3 (64 lần chạy), với kích thích ngẫu nhiên của script (`make_stimulus`, `Random(1000 + n)`, 40 giao dịch; được port sang `nnc/baseline.py`). Đạt khi có `SIM-BRANCH`, `RESULT PASS` và dòng assertion với 0 lỗi.

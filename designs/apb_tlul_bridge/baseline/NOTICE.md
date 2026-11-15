# Third-party material / Tài liệu của bên thứ ba

| Files | Source | Licence |
|---|---|---|
| `tb_apb_tlul_bridge.sv`, `apb_tlul_protocol_assertions.sv` | [nguyenquanicd/VLSIT_ASIC_SOC_AI_SKILLS](https://github.com/nguyenquanicd/VLSIT_ASIC_SOC_AI_SKILLS), `example/apb_tlul_bridge/verification/`, commit `53407f297ce20d08533425a05ac2d729bd830481` (2026-11-08) | Apache-2.0 (`../LICENSE-Apache-2.0`) |

**EN:** The testbench files are unchanged copies of the verification the upstream author delivered with the RTL.
NNC Pipeline never shows them to its agents; they are used only by `nnc baseline` to compare the hand-written
testbench with the generated verification on the same faults (`bugs/bugs.json`). `baseline.json` (written for NNC
Pipeline) describes how the upstream script runs them: Icarus Verilog, `make sim` (default parameters) and `make sim-narrow` (`PARA_ADDR_W=16 PARA_SRC_W=1 PARA_SRC_ID=1`), `+SEED=1 +N=400`; a run passes when it prints `TB PASS` and exits with 0 (`$fatal` otherwise). The RTL of this design was copied from commit `da2bad7`; the clean run of `nnc baseline` shows the testbench of the later commit still passes on it.

**VI:** Các file testbench là bản sao nguyên vẹn của phần kiểm chứng mà tác giả gốc giao kèm RTL. NNC Pipeline không
bao giờ đưa chúng cho agent; chỉ lệnh `nnc baseline` dùng chúng để so sánh testbench viết tay với kiểm chứng được sinh
ra trên cùng các lỗi (`bugs/bugs.json`). `baseline.json` (viết cho NNC Pipeline) mô tả cách script gốc chạy chúng:
Icarus Verilog, `make sim` (tham số mặc định) và `make sim-narrow` (`PARA_ADDR_W=16 PARA_SRC_W=1 PARA_SRC_ID=1`), `+SEED=1 +N=400`; đạt khi in `TB PASS` và thoát với 0 (nếu không thì `$fatal`). RTL của thiết kế này lấy từ commit `da2bad7`; lần chạy sạch của `nnc baseline` cho thấy testbench của commit sau vẫn đạt trên nó.

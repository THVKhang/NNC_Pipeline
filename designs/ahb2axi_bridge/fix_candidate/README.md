# Findings on the delivered RTL / Phát hiện trên RTL bàn giao

**Status (2026-11-15): open, for the designer.** The upstream design (`common_rtl/005_AHB2AXI_Bridge` @ 53407f2) comes with lint logs but no testbench. The approved NNC verification (G3, generated from the specification only) fails on it: **1/21 tests pass**, 6 of 20 assertions fail ([../work/results.json](../work/results.json), triage in [../work/triage.md](../work/triage.md): all 12 analysed failures judged *A: RTL wrong*). `../rtl/` is **not changed**: an RTL fix is the designer's decision. This folder holds two fix candidates, each checked on a patched copy with `nnc inject`.

**Trạng thái (2026-11-15): còn mở, chờ người thiết kế.** Thiết kế gốc có log lint nhưng không có testbench. Bộ kiểm chứng NNC (sinh chỉ từ spec, đã duyệt G3) chạy trên RTL bàn giao: **1/21 test pass**, 6/20 assertion fail; triage kết luận cả 12 lỗi được phân tích là *A: RTL sai*. `../rtl/` **không bị sửa**: sửa RTL là quyết định của người thiết kế. Thư mục này chứa hai bản sửa đề xuất, mỗi bản được kiểm trên bản sao RTL bằng `nnc inject`.

| | Tests passing | Failing assertions | Notes |
|---|---|---|---|
| Delivered RTL | 1/21 | 6 (CHK-002, 005, 015, 016, 017, 020) | CHK-015 3834 fails, CHK-016 9771 fails |
| + fix 1 ([fix1/](fix1/results.json)) | 3/21 | 5 (CHK-002, 015, 016, 017, 020) | CHK-015 4 fails, CHK-016 8 fails; AW addresses of single writes wrong |
| + fix 1 + fix 2 ([fix12/](fix12/results.json)) | 6/21 | 3 (CHK-002 9, CHK-017 4, CHK-020 452) | 13 tests time out (transfers never complete) |

## Fix 1: pipelined AHB transfers are dropped — [ahb_if_rsp_ready_order.diff](ahb_if_rsp_ready_order.diff)

`m_ahb2axi_ahb_if.sv:87-88` computes `o_req_valid = hsel & hready & htrans[1] & (~reg_data_phase_valid | o_rsp_ready)` in the `always_comb` block `p_com_ahb_rsp`, but `o_rsp_ready` is only assigned later in the same block (line 97); at line 88 it still holds the default 0 from line 81. A transfer whose address phase overlaps the completing data phase of the previous one (the normal AHB pipeline) is therefore accepted on the bus (HREADYOUT=1) but never captured: it completes with OKAY and no AXI transaction (REQ-FUNC-001/003: "without loss", "exactly one AR"). The fix moves the assignment after the response block. Simulation and synthesis agree on the faulty reading (blocking assignments in order), so this is not a simulator artefact.

## Fix 2: single writes take a stale burst address — [ctrl_cap_stop_gate.diff](ctrl_cap_stop_gate.diff)

`m_ahb2axi_ctrl.sv:859-862` sets `reg_burst_fallback <= 1` whenever `w_cap_stop` is 1, in every state. `w_cap_stop` is 1 when the head of the write-command FIFO is not a SEQ beat, which is the case for the NONSEQ write being popped in IDLE. That later assignment overrides the `reg_burst_fallback <= 0` of the IDLE pop (line 825), so a single write is issued in `ENUM_ST_WR_SINGLE` with `reg_burst_addr[0]` (line 689; never loaded for a non-eligible write) instead of `reg_cmd_addr`. The fix limits the update to `ENUM_ST_WR_CAPTURE`, where capture stop has a meaning.

## Formal check confirms / Kiểm tra hình thức xác nhận

`nnc formal` (SymbiYosys, depth 20, configurations base/ids8/ids35): 8 PROVEN, 2 BOUNDED, 1 VACUOUS, **9 CEX** ([../work/formal.md](../work/formal.md)). The formal triage ([../work/formal_triage.md](../work/formal_triage.md)) judges all 9 counterexamples *A: RTL wrong* and proposes no checker change. They reduce to three root causes:

| Root cause | Counterexamples | Covered by |
|---|---|---|
| `o_req_valid` reads `o_rsp_ready` before it is assigned (`m_ahb2axi_ahb_if.sv:87-88`) | CHK-015, 016, 017 | fix 1 |
| `w_cap_stop` sets `reg_burst_fallback` in every state (`m_ahb2axi_ctrl.sv:859-862`): single writes use unreset `reg_burst_addr/size[0]` (CHK-011, 012); the AW payload changes while AWVALID=1 and AWREADY=0 (CHK-005) | CHK-005, 011, 012 | fix 2 |
| HREADYOUT forced low when the *next* address cannot be queued (`m_ahb2axi_ahb_if.sv:104-105`): the second ERROR cycle is stretched (CHK-001) and IDLE/BUSY get wait states (CHK-002) | CHK-001, 002 | open (no candidate: the fix needs a one-entry holding register, a design choice) |
| Reset value of `o_axi_arprot` (`m_ahb2axi_ctrl.sv:677`) | CHK-020 | open (see below) |

Some traces also contain AHB manager behaviour that AHB5 forbids (address/control changed while HREADY=0). `verif/formal/nnc_env.sv` does not yet assume address/control stability; the triage notes that the RTL faults above occur without it too. Adding that assumption (an *E* item) is left to the G4 reviewer.

Kiểm tra hình thức cho 9 phản ví dụ, cả 9 được đánh giá *A: RTL sai*, quy về 3 nguyên nhân: hai cái trùng với fix 1 và fix 2, cái mới là `ahb_if.sv:104-105` (kéo HREADYOUT xuống khi địa chỉ *kế tiếp* chưa vào được hàng đợi, làm sai chu kỳ ERROR thứ hai và thêm wait cho IDLE/BUSY). Một số trace có manager AHB vi phạm chuẩn (đổi địa chỉ khi HREADY=0); thêm giả thiết môi trường đó là việc của người duyệt G4.

## Still open after both fixes / Còn mở sau hai bản sửa

- **Hangs (13 tests time out):** AHB transfers never complete in the burst tests (CHK-022/024/026/027/032-036, regression) and in reset-in-flight (CHK-039). The first triage pointed at the early-acknowledge termination detection, which lags the command-FIFO empty flag (`m_ahb2axi_ctrl.sv:426-437`), and at terminal responses left in `ENUM_ST_AHB_RSP` without an owning AHB data phase (lines 440-450, 648-651). Not diagnosed further: a triage run on the patched RTL is the next step.
- **CHK-017 / CHK-031:** a locally rejected beat after a buffered prefix completes before the prefix's B responses (spec REQ-ERR-001: drain, then ERROR).
- **CHK-002:** IDLE/BUSY transfers occasionally get a wait state (`m_ahb2axi_ahb_if.sv:104-105` drives HREADYOUT=0 whenever the command FIFO is full).
- **CHK-020 (C or A):** during reset `o_axi_arprot` is 3'b100 (`f_axi_prot` of zero registers) and `o_axi_wdata/wstrb` show the unreset FIFO register, while the port table gives 0. The specification also says that FIFO payload need not be reset (spec:467) and that the adapter uses reset only for VALID/READY (spec:176): the designer must say whether the reset-value column binds payload ports.

None of the bench faults (`../bugs/bugs.json`) is in this list; they are injected on top of the delivered RTL.

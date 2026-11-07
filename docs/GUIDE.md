# Step-by-step guide | Hướng dẫn từng bước

**EN:** Commands are typed in a terminal at the repository root (`python -m nnc ...`). In Claude Code you can instead type `/nnc-flow <design>`: Claude runs the same commands, presents every review gate and waits for your decision.

**VI:** Lệnh được gõ trong terminal tại thư mục gốc của repository (`python -m nnc ...`). Trong Claude Code có thể gõ `/nnc-flow <design>`: Claude chạy đúng các lệnh này, trình bày từng gate và chờ bạn quyết định.

## 0. Install once | Cài đặt một lần

| Need / Cần | Windows | Linux |
|---|---|---|
| Python 3.11+ | `winget install Python.Python.3.12` | distribution package |
| Claude Code (agents) | VS Code extension or CLI, logged in | CLI, logged in |
| `pdftotext` (PDF specs) | comes with Git for Windows | `apt install poppler-utils` |
| Verilator 5 + cocotb + make | in WSL2 Ubuntu: OSS CAD Suite in `/opt/oss-cad-suite`, `/etc/profile.d/nnc.sh` adds it to PATH | the same, natively |

**EN:** `python -m nnc doctor` lists what is found. On Windows the simulator runs inside WSL (`NNC_WSL_DISTRO`, default `Ubuntu-24.04`); NNC copies the files there and brings the results back.

**VI:** `python -m nnc doctor` liệt kê công cụ có/thiếu. Trên Windows, mô phỏng chạy trong WSL (`NNC_WSL_DISTRO`, mặc định `Ubuntu-24.04`); NNC tự chép file vào đó và lấy kết quả về.

## 1. Create the design workspace | Tạo workspace thiết kế

```bash
python -m nnc init my_ip --top m_my_ip
cp <rtl files> designs/my_ip/rtl/            # + filelist.f in compile order (optional)
python -m nnc doc add my_ip path/to/my_ip_spec.md --role ip_spec --tag IP
python -m nnc doc add my_ip path/to/axi_spec.pdf  --role standard --tag AX --skip "Low-power Interface"
```

**EN:** The IP specification must contain a port table (columns *Port*, *Direction*, *Width*) and, if parameterised, a parameter table (*Parameter*, *Default*): the contract interface is read from them by code. Tags prefix the rule IDs (`IP-3-01`, `AX-3.1-02`). `--sections`/`--skip` take section numbers or parts of titles.

**VI:** Spec của IP phải có bảng port (cột *Port*, *Direction*, *Width*) và bảng tham số nếu có (*Parameter*, *Default*): interface của contract được code đọc từ đó. Tag là tiền tố của ID luật. `--sections`/`--skip` nhận số mục hoặc một phần tiêu đề.

## 2. Rules — Gate 1 | Luật — Gate 1

```bash
python -m nnc flow my_ip            # ingest -> extract -> review, stops at G1
```

**EN:** Read `work/rules.md`: open questions first (only those the documents do not answer), then rejected rules, then the rules. Every rule cites sentence IDs; the quote is rebuilt from the document, never written by the model. Answer open questions by editing the specification and re-running (`nnc flow my_ip`, the cache makes unchanged parts free). Then:

**VI:** Đọc `work/rules.md`: câu hỏi mở trước (chỉ những câu tài liệu chưa trả lời), rồi luật bị loại, rồi các luật. Mỗi luật dẫn ID câu; câu trích do code ghép lại từ tài liệu, không do model viết. Trả lời câu hỏi mở bằng cách sửa spec và chạy lại (phần không đổi lấy từ cache, không tốn phí). Sau đó:

```bash
python -m nnc answer my_ip 1 "Black-box only: tests observe the top-level ports." --by "Your Name"
python -m nnc gate approve my_ip G1_rules --by "Your Name"
```

**EN:** `nnc answer` records your decision on an open question; decisions are part of the Gate 1 artifact and are given to the contract agent as binding input. `gate approve G1_rules` warns about questions left without a decision.

**VI:** `nnc answer` ghi quyết định của bạn cho một câu hỏi mở; quyết định là một phần của artifact Gate 1 và được đưa cho agent contract như đầu vào bắt buộc. `gate approve G1_rules` cảnh báo nếu còn câu hỏi chưa có quyết định.

## 3. Contract — Gate 2 | Contract — Gate 2

```bash
python -m nnc flow my_ip --from contract     # stops at G2
```

**EN:** `work/contract.md` lists the interface (from the spec tables), every check (assertion or test) with the exact cycle behaviour and its rules, the rules not verifiable by simulation with the reason, and the assumptions. Every kept rule is either in a check or has a reason.

**VI:** `work/contract.md` liệt kê interface (từ bảng của spec), mọi check (assertion hoặc test) với hành vi theo chu kỳ và luật nguồn, các luật không kiểm được bằng mô phỏng kèm lý do, và các giả định. Mọi luật đều thuộc một check hoặc có lý do.

## 4. Verification sources — Gate 3 | Mã kiểm chứng — Gate 3

```bash
python -m nnc gate approve my_ip G2_contract --by "Your Name"
python -m nnc flow my_ip --from gen-sva      # gen-sva, gen-tests; stops at G3
```

**EN:** `verif/sva/nnc_chk_<group>.sv` (linted by Verilator, repaired by the agent at most 3 times) and `verif/tests/test_<design>.py` (cocotb). Neither agent sees the RTL.

**VI:** `verif/sva/nnc_chk_<group>.sv` (Verilator lint, agent sửa tối đa 3 lần) và `verif/tests/test_<design>.py` (cocotb). Không agent nào thấy RTL.

## 5. Simulation, triage, mutation, report — Gate 4 | Mô phỏng, triage, mutation, báo cáo — Gate 4

```bash
python -m nnc gate approve my_ip G3_verif_sources --by "Your Name"
python -m nnc flow my_ip --from sim
```

| Output | Meaning / Ý nghĩa |
|---|---|
| `work/results.json` | tests, assertion hits/fails, RTL line coverage, interface conformance |
| `work/triage.md` | per failure: spec says / RTL does / test does / candidates A-B-C / options — **you decide** |
| `work/mutation.json` | mutants on a copy of the RTL: killed / survived / not compiled, score |
| `work/report.md`, `work/rtm.json` | rule → check → evidence, gates, cost |

**EN:** A test that fails because of a Python error in the test code is repaired automatically (at most twice) without showing the RTL; a failed check is never "repaired". Sign off with `nnc gate approve my_ip G4_signoff` only after reading the report.

**VI:** Test lỗi do code Python của test được tự sửa (tối đa 2 lần) mà không cho xem RTL; một check thất bại thì không bao giờ được "sửa". Chỉ ký `G4_signoff` sau khi đọc báo cáo.

## Exploratory run | Chạy thăm dò

```bash
python -m nnc flow my_ip --unreviewed
```

**EN:** Runs everything without stopping at gates. Every artifact and the report are stamped UNREVIEWED with the gates that were bypassed; such a report cannot be signed off.

**VI:** Chạy hết không dừng ở gate. Mọi artifact và báo cáo bị đóng dấu UNREVIEWED kèm các gate đã bỏ qua; báo cáo này không thể ký duyệt.

## Re-run after a change | Chạy lại khi có thay đổi

| Change / Thay đổi | Effect / Hệ quả |
|---|---|
| Specification edited | G1 becomes STALE, later gates BLOCKED; re-run from `ingest`; only changed batches cost tokens |
| RTL edited | gates stay valid (the oracle does not depend on the RTL); re-run from `sim` |
| Test or checker edited by hand | G3 becomes STALE; review and approve again |

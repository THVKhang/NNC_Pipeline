# Findings on the delivered RTL / Phát hiện trên RTL bàn giao

The approved verification of this design ([../work/report.md](../work/report.md)) fails on the RTL as delivered: 13 of 15 tests fail and the assertion CHK-016 fails 606 times. The RTL in `../rtl/` is left unchanged; the decisions below belong to the designer.

Verification đã duyệt của thiết kế này fail trên RTL bàn giao: 13/15 test fail, assertion CHK-016 fail 606 lần. RTL trong `../rtl/` giữ nguyên; các quyết định dưới đây thuộc về người thiết kế.

## 1. Write beats are issued one beat ahead / Beat ghi bị phát sớm một beat

| | |
|---|---|
| Symptom | Every AXI write goes to APB at AWADDR + size for beat 0 (e.g. AWADDR 0x3000, 4 beats → PADDR 0x3004…0x3010; the last one lies outside the burst). Reads are correct. |
| Specification | REQ-IF-002 and OP-002; the spec's own waveform WF-005 (upstream `figures/wf-005.json`): AWADDR 0x2000, AWLEN 1 → PADDR **0x2000, 0x2004**. |
| RTL | `m_axi2apb_wr_seq.sv:344` updates `reg_wr_addr <= w_wr_nxt_addr` when it captures the W beat, before `o_req_addr` (line 294) sends that beat. The read sequencer advances after the beat (`m_axi2apb_rd_seq.sv:374-378`). The same line is in upstream `rtl_v2/`. |
| Found by | the independent SVA checker CHK-016 and 12 cocotb tests; the triage agent ([../work/triage.md](../work/triage.md)) traced all 12 analysed failures to this line, judged *A: RTL wrong*, and argued against B and C. |
| Candidate fix | [wr_addr_advance.diff](wr_addr_advance.diff): advance the address when the beat's APB response returns (`ENUM_ST_WAIT && i_rsp_valid`). |
| Fix checked on a copy | `python -m nnc inject axi2apb_bridge designs/axi2apb_bridge/fix_candidate/wr_addr_advance.diff --out designs/axi2apb_bridge/fix_candidate --no-triage` → [results.json](results.json): 14/15 tests pass, 17/17 assertions hit with **0 failures**, line coverage 98.4 %. |

## 2. Arbitration after a lone transaction: the specification is ambiguous / Phân xử sau một giao dịch đơn lẻ: spec chưa rõ

The one test still failing with the fix is CHK-019 phase D: after reset a lone write completes, then AR and AW arrive together.

| Reading | Next winner | Who follows it |
|---|---|---|
| REQ-FUNC-003 word for word: "choose AR for the first tie after reset, and flip the next tie preference after each completed transaction" (AR → flip → AW) | AW | the contract (CHK-019) and the test |
| Classic round-robin: the side served last gets lower priority (`m_axi2apb_apb_ctrl.sv:216-226`: read done → prefer AW, write done → prefer AR) | AR | the RTL |

How the contract got its reading: at Gate 1 the question "does the preference flip after transactions that had no tie?" was answered from the specification (3:s6, "the spec makes no exception"), and the open question on the turn update was decided **on delegation by Claude** following that answer ([../work/rules.md](../work/rules.md), question 2). A person should confirm or reverse that decision.

The two readings agree whenever reads and writes alternate (phases A–C pass) and differ only after a transaction completes without contention. The designer chooses one reading and records it (`nnc answer`), then either the RTL or the specification sentence changes; the test is regenerated from the new contract only if the specification changes.

Hai cách hiểu trùng nhau khi đọc/ghi luân phiên (phase A–C pass) và chỉ khác khi một giao dịch hoàn tất mà không có tranh chấp. Người thiết kế chọn một cách hiểu và ghi lại (`nnc answer`), rồi sửa RTL hoặc câu trong spec; test chỉ sinh lại nếu spec đổi.

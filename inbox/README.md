# inbox: put a design here | Bỏ thiết kế vào đây

**EN:** One folder per design. `nnc run <name>` (or the **Run** button of `nnc ui`) makes the workspace
`designs/<name>/` from it and runs the whole flow to the report. Everything in this folder except this README is
ignored by git, so licensed specifications stay on your machine.

**VI:** Mỗi thiết kế một thư mục. `nnc run <tên>` (hoặc nút **Run** của `nnc ui`) tạo workspace `designs/<tên>/`
từ thư mục đó và chạy cả flow tới báo cáo. Git bỏ qua mọi thứ trong thư mục này trừ README, nên spec có bản quyền
chỉ nằm trên máy bạn.

```
inbox/my_fifo/
  spec/my_fifo_spec.md        the IP specification, ONE file (.md .txt .pdf .docx .html .adoc)
  standards/axi.pdf           optional: standards the specification refers to
  rtl/*.sv                    the RTL (.sv .v .svh .vh; sub-folders and filelist.f are kept)
  inbox.json                  optional, see below
```

```json
{"top": "m_my_fifo", "tag": "FF", "lib": ["../../shared_rtl"], "defines": ["SYNTHESIS"],
 "standard_tags": {"axi.pdf": "AX"}, "config": {"formal": "on", "clock_periods": "i_clk=10"}}
```

| Key | Meaning / Ý nghĩa | Default |
|---|---|---|
| `top` | top module / module top | found by the intake (the module nothing instantiates) |
| `tag` | prefix of the rule IDs / tiền tố ID luật | `IP` |
| `lib` | library folders, relative to this folder / thư mục thư viện | none |
| `defines` | macros for the tools / macro | none |
| `standard_tags` | tag of each standard / tag của từng chuẩn | `S1`, `S2`, ... |
| `config` | workspace settings, as `nnc config <name> key=value` / cấu hình workspace | none |

```bash
python -m nnc run my_fifo --prepare-only   # check the inputs, no agent, no cost / kiểm đầu vào, không tốn tiền
python -m nnc run my_fifo                  # whole flow, results marked UNREVIEWED / cả flow, kết quả UNREVIEWED
python -m nnc run my_fifo --gated          # stop at each gate for review / dừng ở mỗi gate để duyệt
python -m nnc ui                           # dashboard: http://127.0.0.1:8765
```

**EN:** A run again goes on from where the last one stopped (a gate, a failure), so the answers and approvals
recorded in between are kept. Changed documents start again from `ingest`; a changed RTL from `sim`. The agents
run through the Claude Code CLI and cost money (about 2 USD for a small block); `--backend replay` never calls a
model. Results of a run that did not stop at the gates are marked UNREVIEWED: only a hardware designer can review
the gates and sign off (G4).

**VI:** Chạy lại thì đi tiếp từ chỗ lần trước dừng (một gate, một lỗi), nên các câu trả lời và phê duyệt ghi ở
giữa được giữ. Spec đổi thì chạy lại từ `ingest`; RTL đổi thì từ `sim`. Agent chạy qua Claude Code CLI và tốn tiền
(khoảng 2 USD cho một khối nhỏ); `--backend replay` không bao giờ gọi model. Kết quả của lần chạy không dừng ở gate
bị đánh dấu UNREVIEWED: chỉ người thiết kế phần cứng mới duyệt gate và ký G4 được.

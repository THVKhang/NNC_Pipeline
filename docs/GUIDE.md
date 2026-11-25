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

### Docker and Codespaces | Docker và Codespaces (no install, no agent)

**EN:** The image of the `Dockerfile` holds every tool at the versions CI uses (OSS CAD Suite 2026-11-07, cocotb
2.1.0) and the committed designs. Without an API key it runs `nnc demo`. That command reruns, for a finished
design, the steps that need no agent and compares each one with the recorded outcome:
- the intake;
- the reproduction kit of the primary run;
- the CDC check;
- the formal check, with `--formal`.

With `--replay` it also replays the stages that read the specification (extract, review, contract). They run
from the committed answer cache (`work/cache/agents/`), and the `replay` backend stops instead of calling a model.

```bash
docker pull ghcr.io/thvkhang/nnc_pipeline:latest          # or: docker build -t nnc-pipeline .
docker run --rm ghcr.io/thvkhang/nnc_pipeline              # = nnc demo sync_fifo
docker run --rm ghcr.io/thvkhang/nnc_pipeline nnc demo ot_gpio --replay
docker run --rm ghcr.io/thvkhang/nnc_pipeline nnc demo sync_fifo --formal
docker run --rm -it ghcr.io/thvkhang/nnc_pipeline bash     # every nnc command, the tools on PATH
```

In GitHub Codespaces (*Code → Codespaces → Create*) or VS Code *Reopen in Container*, `.devcontainer/` builds the
same image and installs `nnc` from the checked-out sources. To run the agent stages there, install Claude Code
in the container and log in with your own account; the flow never ships a key.

What a replay shows and what it does not:
- The replay of a stage proves that the committed records come from the recorded answers, with nothing edited
  by hand. It compares every record, leaving out only the date, the usage and the designer's decisions on
  open questions.
- A stage whose prompt changed after the recorded run has no cached answer and is reported NOT_CACHED.
- The stages that write code (checkers, tests, formal environment) are not replayed. Their committed files
  include later corrections by A17, so the first answer is not the committed file.

**VI:** Image từ `Dockerfile` chứa đủ công cụ, đúng phiên bản CI đang dùng (OSS CAD Suite 2026-11-07, cocotb
2.1.0), cùng các thiết kế đã commit. Không cần API key, image chạy được `nnc demo`. Lệnh này chạy lại, cho một
thiết kế đã xong, các bước không cần agent, rồi so từng bước với kết quả đã ghi:
- intake;
- kit tái lập của lần chạy chính;
- kiểm tra CDC;
- formal, nếu thêm `--formal`.

Thêm `--replay` thì phát lại cả các bước đọc spec (trích luật, review, contract). Câu trả lời lấy từ cache đã
commit (`work/cache/agents/`). Backend `replay` dừng lại chứ không bao giờ gọi model.

Trong GitHub Codespaces (*Code → Codespaces → Create*) hoặc VS Code *Reopen in Container*, `.devcontainer/` dựng
cùng image đó và cài `nnc` từ mã nguồn đang mở. Muốn chạy agent trong đó thì cài Claude Code trong container và
đăng nhập bằng tài khoản của bạn; flow không kèm key nào.

Replay chứng minh được gì, và không chứng minh được gì:
- Replay một bước chứng minh bản ghi đã commit đúng là từ câu trả lời đã ghi, không ai sửa tay. Mọi bản ghi
  đều được so, chỉ bỏ qua ngày chạy, chi phí và quyết định của người thiết kế cho các câu hỏi mở.
- Bước nào có prompt đã đổi sau lần chạy gốc thì không có câu trả lời trong cache, và được báo NOT_CACHED.
- Các bước viết code (checker, test, môi trường formal) không được replay. File đã commit của chúng có thêm các
  sửa chữa sau đó của A17, nên câu trả lời đầu tiên không phải là file đã commit.

## 1. Create the design workspace | Tạo workspace thiết kế

```bash
python -m nnc init my_ip --top m_my_ip
cp <rtl files> designs/my_ip/rtl/            # + filelist.f in compile order (optional)
python -m nnc doc add my_ip path/to/my_ip_spec.md --role ip_spec --tag IP
python -m nnc doc add my_ip path/to/axi_spec.pdf  --role standard --tag AX --skip "Low-power Interface"
```

**EN:** The IP specification must contain a port table (columns *Port*, *Direction*, *Width*) and, if parameterised, a parameter table (*Parameter*, *Default*): the contract interface is read from them by code. Tags prefix the rule IDs (`IP-3-01`, `AX-3.1-02`). `--sections`/`--skip` take section numbers or parts of titles.

**VI:** Spec của IP phải có bảng port (cột *Port*, *Direction*, *Width*) và bảng tham số nếu có (*Parameter*, *Default*): interface của contract được code đọc từ đó. Tag là tiền tố của ID luật. `--sections`/`--skip` nhận số mục hoặc một phần tiêu đề.

### Intake of a new input | Kiểm đầu vào mới (no agent)

```bash
python -m nnc intake my_ip                         # -> work/intake.md: ready / adapt / needs_input / unsupported
python -m nnc intake my_ip --lib path/to/other_lib  # units the top needs from other folders
python -m nnc adapt my_ip --lib path/to/other_lib   # copies them, writes the wrapper and the interface document
python -m nnc intake --rtl path/to/any/rtl --top m  # any folder, without a workspace
```

**EN:** Run the intake before any agent. It finds the files the top needs (packages first, include folders), reads the top with Verilator and with both Yosys frontends, lists the ports by kind, and the clocks and resets by the netlist (which inputs clock or reset flops). Specifications may be Markdown, text, PDF (with a text layer), Word `.docx` or HTML; the port table is read from Markdown, Word and HTML. If the verdict is *adapt*, `nnc adapt` writes, without an agent: the library files into `rtl/` (unchanged, with their SHA-256 in `work/adapt.json`); a wiring-only wrapper `<top>_nnc` when the top has struct or array ports (one port per field; at time 0 the simulation stops if a parameter set changes a struct layout); and `spec/<top>_interface.md`, the port table of the verified top, registered as document role `interface` (the contract reads it; the extraction agents do not, because it adds no behaviour). A design without a clock gets the test-bench clock `nnc_clk`, connected to nothing in the DUT. Verdict *needs_input* names what to give (a library folder, a parameter value, the top among several candidates); *unsupported* says why (VHDL, encrypted source, an interface port). What this covers on open-source RTL is measured in [INPUT_SUPPORT.md](INPUT_SUPPORT.md).

**VI:** Chạy intake trước khi dùng agent. Lệnh này tìm các file mà top cần (package trước, thư mục include), đọc top bằng Verilator và bằng cả hai frontend của Yosys, liệt kê port theo loại, và tìm clock, reset từ netlist (input nào làm clock hay reset cho flop). Spec có thể là Markdown, text, PDF (có lớp chữ), Word `.docx` hoặc HTML; bảng port được đọc từ Markdown, Word và HTML. Nếu kết quả là *adapt*, `nnc adapt` tự làm, không cần agent: chép file thư viện vào `rtl/` (giữ nguyên, ghi SHA-256 vào `work/adapt.json`); viết wrapper chỉ nối dây `<top>_nnc` khi top có port struct hoặc mảng (mỗi trường một port; ở thời điểm 0 mô phỏng dừng nếu một bộ tham số làm đổi layout của struct); và `spec/<top>_interface.md`, bảng port của top được verify, đăng ký với vai trò `interface` (contract đọc nó; agent trích luật không đọc, vì nó không thêm hành vi nào). Thiết kế không có clock được thêm clock của testbench `nnc_clk`, không nối vào DUT. Kết quả *needs_input* nói rõ cần đưa thêm gì (thư mục thư viện, giá trị tham số, chọn top giữa nhiều ứng viên); *unsupported* nói lý do (VHDL, mã nguồn mã hoá, port kiểu interface). Mức bao phủ trên RTL mã nguồn mở được đo trong [INPUT_SUPPORT.md](INPUT_SUPPORT.md).

## 2. Rules — Gate 1 | Luật — Gate 1

```bash
python -m nnc flow my_ip            # ingest -> extract -> review, stops at G1
```

**EN:** Read `work/rules.md`: open questions first (only those the documents do not answer), then rejected rules, then the rules. Every rule cites sentence IDs; the quote is rebuilt from the document, never written by the model. Answer each open question either with a recorded decision (`nnc answer`, below) or by editing the specification and re-running (`nnc flow my_ip`; the cache makes unchanged parts free). Then:

**VI:** Đọc `work/rules.md`: câu hỏi mở trước (chỉ những câu tài liệu chưa trả lời), rồi luật bị loại, rồi các luật. Mỗi luật dẫn ID câu; câu trích do code ghép lại từ tài liệu, không do model viết. Trả lời từng câu hỏi mở bằng một quyết định được ghi lại (`nnc answer`, bên dưới) hoặc bằng cách sửa spec rồi chạy lại (phần không đổi lấy từ cache, không tốn phí). Sau đó:

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

```bash
python -m nnc plan my_ip                                   # list the checks / liệt kê check
python -m nnc plan my_ip --all --by "Your Name"            # recommended: every applicable check
python -m nnc plan my_ip --exclude CHK-012,CHK-019 --by "Your Name" --reason "ratio runs later"
```

**EN:** The test-plan selection is part of the contract: changing it makes G2 STALE. Checks left out are generated by nobody and reported `NOT_SELECTED`, never PASS, and the sign-off table lists them.

**VI:** Lựa chọn test plan là một phần của contract: đổi nó làm G2 thành STALE. Check bị bỏ ra không được sinh, báo cáo là `NOT_SELECTED` (không bao giờ PASS) và bảng sign-off liệt kê chúng.

**EN — several clocks:** every port of type *Clock* and *Reset* in the port table is used, each reset with the clock of its *Clock domain*. By default (`clock_relation=sync`) the clocks are synchronous and start together; set their periods with `nnc config my_ip clock_periods="i_clk_wr=10,i_clk_rd=15"` (ns, default 10). Derived parameters (`LPARA_X = clog2(...)` in the parameter table) are computed, never set.

**VI — nhiều clock:** mọi port loại *Clock* và *Reset* trong bảng port đều được dùng, mỗi reset theo clock của *Clock domain* của nó. Mặc định (`clock_relation=sync`) các clock đồng bộ, khởi động cùng lúc; đặt chu kỳ bằng `nnc config my_ip clock_periods="i_clk_wr=10,i_clk_rd=15"` (ns, mặc định 10). Tham số dẫn xuất (`LPARA_X = clog2(...)` trong bảng tham số) được tính, không bao giờ được đặt.

**EN — asynchronous clocks and run options:** for an IP whose clock domains are unrelated (CDC: asynchronous FIFO, bridge between two clocks), set the relation **before the contract stage**:

```bash
python -m nnc config my_ip clock_relation=async clock_periods="i_clk_wr=10,i_clk_rd=13.7"
python -m nnc config my_ip plusargs="+MSYNC_SEED={seed} +MSYNC_EN=1"   # simulator plusargs, {seed} = run seed
python -m nnc config my_ip defines=VLSIT_SYNTHESIS                     # Verilog macros of the DUT build
python -m nnc flow my_ip --from gen-tests --agent-timeout 3600         # a large spec needs more agent time
```

With `async` each clock starts after its own seeded random delay below one period, so the phase between the domains changes from test to test and from seed to seed; periods may be fractional (13.7 ns) so that the ratio is not an integer. The contract, SVA and test agents are told that no edge of one clock may be assumed to coincide with an edge of another: a cross-domain check states an order and a bounded window counted in edges of the destination clock, never an exact cycle. Tests can stop and restart a clock (`stop_clock`, `resume_clock`). The test agent is given the defines and plusargs of the run, and tests read them with `plusarg("NAME")` and `DEFINES` (set them before `gen-tests`; changing them later needs new tests). One run has one configuration (defines, plusargs, parameters): a check that needs another one (synthesis branch, metastability model off) is reported `NOT_VERIFIABLE`, never PASS.

**VI — clock bất đồng bộ và tuỳ chọn chạy:** với IP có các miền clock không liên quan (CDC: FIFO bất đồng bộ, bridge giữa hai clock), đặt quan hệ **trước bước contract** (lệnh như trên). Với `async`, mỗi clock khởi động sau một khoảng trễ ngẫu nhiên riêng (nhỏ hơn một chu kỳ, theo seed), nên lệch pha giữa các miền thay đổi theo test và theo seed; chu kỳ có thể lẻ (13.7 ns) để tỉ lệ không nguyên. Agent contract, SVA và test được dặn: không được giả sử cạnh của hai clock trùng nhau; check qua hai miền phải nói thứ tự và một cửa sổ giới hạn tính bằng cạnh của clock đích, không bao giờ là một chu kỳ chính xác. Test có thể dừng và chạy lại một clock (`stop_clock`, `resume_clock`). `plusargs` truyền cho simulator (`{seed}` thay bằng seed của lần chạy), `defines` là macro Verilog khi build DUT; agent test được cho biết hai giá trị này và test đọc chúng bằng `plusarg("NAME")`, `DEFINES` (đặt trước `gen-tests`; đổi sau đó thì cần sinh lại test); `--agent-timeout` (giây, mặc định 1800) cho agent nhiều thời gian hơn với spec lớn. Mỗi lần chạy chỉ có một cấu hình: check cần cấu hình khác (nhánh synthesis, tắt mô hình metastability) được báo `NOT_VERIFIABLE`, không bao giờ PASS — trừ khi có run set (mục dưới).

### Run set: several configurations and seeds | Nhiều cấu hình và nhiều seed

`designs/<ip>/run_set.json` lists the configurations of the specification. `nnc sim`, `cover` and `inject` then run all of them (each configuration built once, its seeds one after the other, configurations in parallel: `--jobs`, default `NNC_JOBS` or the CPU count; the same setting runs SymbiYosys tasks and mutants in parallel, while `--workers` is the number of parallel agent calls). A configuration with `"x_init": "random"` is tested like the others, but its coverage is not merged: its toggles before the first reset are not design activity and merge the results per check:

```json
{"seeds": [1],
 "configs": [
  {"name": "base", "note": "CFG-BASE, model on", "seeds": [1, 2, 3, 4, 5]},
  {"name": "model_off", "plusargs": "+MSYNC_SEED={seed} +MSYNC_EN=0"},
  {"name": "syn", "defines": "VLSIT_SYNTHESIS"},
  {"name": "cell4", "params": {"PARA_CELL_TYPE": 4}},
  {"name": "slow_rd", "clock_periods": "i_clk_wr=6,i_clk_rd=22"}]}
```

Each configuration starts from the design configuration and overrides only what it names: `params` (contract parameters; derived ones are refused), `defines` and `plusargs` (replaced), `clock_periods` (merged per clock), `seeds`. The first configuration with its first seed is the **primary run**: the reproduction kit `sim/` and mutation testing use it. Merging never weakens a result: a test fails if it failed in any run; an assertion's hits and fails are summed (NOT_HIT only if it was hit in no run); a check is `NOT_VERIFIABLE` only if **every** run declared it so, and PASS needs one run that verified it with no run failing it. Code coverage is the merged `coverage.dat` of all runs. The report gets a *Run set* table, each check says in which runs it was verified or failed, and a sign-off condition requires every run to build. Per-run results are in `work/runs/<config>.s<seed>.json` and logs in `work/sim/runs/`. `--single-run` ignores the file. The tests are not regenerated: they read the parameters, defines and plusargs of their run and decide themselves what they can check.

**VI:** file `designs/<ip>/run_set.json` liệt kê các cấu hình mà spec yêu cầu. Khi có file này, `nnc sim`, `cover` và `inject` chạy hết mọi cấu hình: mỗi cấu hình build một lần, các seed chạy nối tiếp nhau, các cấu hình chạy song song theo `--jobs` (mặc định là `NNC_JOBS`, nếu không có thì bằng số CPU; cùng thiết lập này dùng cho SymbiYosys và mutant, còn `--workers` là số lời gọi agent song song). Cấu hình có `"x_init": "random"` vẫn chạy test như các cấu hình khác, nhưng coverage của nó không được gộp, vì toggle trước reset đầu tiên không phải hoạt động của thiết kế. Sau đó kết quả được gộp theo từng check.
- **Cách khai báo:** mỗi cấu hình kế thừa config của thiết kế và chỉ thay những gì nó ghi: `params` (không nhận tham số dẫn xuất), `defines`, `plusargs`, `clock_periods`, `seeds`.
- **Lần chạy chính:** cấu hình đầu tiên với seed đầu tiên. Bộ tái lập `sim/` và mutation testing dùng lần chạy này.
- **Gộp kết quả không bao giờ làm yếu kết luận:**
  - Một test chỉ cần fail ở một lần chạy là FAIL.
  - Assertion được cộng số lần hit và số lần fail; nó chỉ là NOT_HIT khi không lần chạy nào hit.
  - Một check chỉ là `NOT_VERIFIABLE` khi **mọi** lần chạy đều khai như vậy. Nó là PASS khi có ít nhất một lần chạy kiểm được và không lần nào fail.
- **Coverage** là coverage.dat gộp của tất cả các lần chạy.
- **Report** có bảng *Run set*. Mỗi check ghi rõ nó được kiểm hay bị fail ở lần chạy nào. Có thêm một điều kiện sign-off: mọi lần chạy phải build được.
- **Không cần sinh lại test:** test tự đọc tham số, define và plusarg của lần chạy để biết mình kiểm được gì.
- `--single-run` bỏ qua file run set.

**Configuration-aware generation.** When `run_set.json` exists before `gen-sva`/`gen-tests`, the SVA and test writers get every configuration of it in their prompt, with the rule that a quantity depending on a parameter is computed from it. After generation, code looks for integer literals equal to the default value (≥ 5) of a parameter the run set changes; each is sent back once to be replaced by an expression, or kept with the comment `nnc-literal-ok` when the number does not come from the parameter (`nnc/literals.py`). Formal (`formal=on`) proves each check in every configuration of the run set with a distinct parameter set: a counterexample in any configuration is a CEX, otherwise the weakest status counts (PROVEN < BOUNDED < TIMEOUT); a configuration where the check is vacuous or unsupported is not counted. — **VI:** nếu có `run_set.json` trước khi sinh SVA/test, agent thấy mọi cấu hình trong prompt và phải tính mọi đại lượng phụ thuộc tham số từ chính tham số đó. Sau khi sinh, code tìm các số nguyên trùng giá trị mặc định của tham số mà run set thay đổi; mỗi số bị gửi lại một lần để thay bằng biểu thức (hoặc giữ lại với chú thích `nnc-literal-ok` nếu số đó không đến từ tham số). Formal chứng minh từng check ở mọi cấu hình có đổi tham số và giữ kết quả yếu nhất.

## 4. Verification sources — Gate 3 | Mã kiểm chứng — Gate 3

```bash
python -m nnc gate approve my_ip G2_contract --by "Your Name"
python -m nnc flow my_ip --from gen-sva      # gen-sva, gen-tests; stops at G3
```

**EN:** `verif/sva/nnc_chk_<group>.sv` (linted by Verilator, repaired by the agent at most 3 times), `verif/sva/nnc_cov.sv` (functional cover points from the specification, listed in `work/gen_cov.json`) and `verif/tests/test_<design>.py` (cocotb). None of these agents sees the RTL.

**VI:** `verif/sva/nnc_chk_<group>.sv` (Verilator lint, agent sửa tối đa 3 lần), `verif/sva/nnc_cov.sv` (cover point chức năng lấy từ spec, danh sách ở `work/gen_cov.json`) và `verif/tests/test_<design>.py` (cocotb). Không agent nào trong số này thấy RTL.

## 5. Simulation, triage, mutation, report — Gate 4 | Mô phỏng, triage, mutation, báo cáo — Gate 4

```bash
python -m nnc gate approve my_ip G3_verif_sources --by "Your Name"
python -m nnc flow my_ip --from sim
```

| Output | Meaning / Ý nghĩa |
|---|---|
| `work/results.json` | tests, assertion hits/fails, code coverage of the RTL (line, block, toggle, expression), functional cover points, interface conformance |
| `work/coverage.md` | baseline of every metric, functional points never hit, uncovered code items per file; closure rounds, tests added, points claimed unreachable |
| `work/triage.md` | per failure: spec says / RTL does / test does / candidates A-B-C / options — **you decide** |
| `work/mutation.json` | mutants on executed lines of a copy of the RTL: killed / survived / not compiled, score, rules of each mutant, score per rule |
| `work/report.md`, `work/rtm.json` | sign-off conditions, rule → check → evidence → mutation score, gates, cost (including what failed calls cost) |
| `work/review_packet.md` | for the G4 reviewer: only what needs a human judgement (delegated decisions, failures with their triage, hand edits, what is not verified, surviving mutants) and a checklist |
| `sim/Makefile` | reproduce without NNC (Linux/WSL): `make help`, `make regression`, `make test TC=test_chk_003`, `make coverage-report` |

```bash
python -m nnc cover my_ip                                   # baseline of every metric, no agent
python -m nnc cover my_ip --target 98 --metric line         # closure: new spec-based tests, at most 5 rounds
python -m nnc config my_ip mutation_threshold=85            # per-rule mutation threshold (default 85)
```

**EN:** Coverage closure shows the baseline first; you choose the metric and target. Uncovered points are mapped to legal stimulus by an analyst that may read the RTL; any scenario that names an RTL-internal identifier is dropped by code, and the tests are written by an agent that never sees the RTL, with expected values from the contract. Closure modules (`verif/tests/test_<ip>_cov<n>.py`) change `verif/`, so G3 must be approved again. A functional failure stops the loop and goes to triage. Points the analyst claims unreachable are listed for you and still counted.

**VI:** Coverage closure hiện baseline trước; bạn chọn metric và mục tiêu. Điểm chưa phủ được một agent phân tích (được đọc RTL) đổi thành stimulus hợp lệ; kịch bản nào nhắc tên định danh nội bộ của RTL bị code loại bỏ, và test được viết bởi agent không bao giờ thấy RTL, giá trị mong đợi lấy từ contract. Module closure (`verif/tests/test_<ip>_cov<n>.py`) thay đổi `verif/` nên G3 phải duyệt lại. Lỗi chức năng dừng vòng lặp và chuyển sang triage. Điểm được cho là không thể đạt chỉ được liệt kê để bạn xem, vẫn tính trong mẫu số.

**EN:** A test that fails because of a Python error in the test code is repaired automatically (at most twice) without showing the RTL; a failed check is never "repaired". Sign off with `nnc gate approve my_ip G4_signoff` only after reading the report: its *Sign-off conditions* table shows what is met (all checks PASS, every rule mapped, per-rule mutation ≥ threshold, coverage target).

**VI:** Test lỗi do code Python của test được tự sửa (tối đa 2 lần) mà không cho xem RTL; một check thất bại thì không bao giờ được "sửa". Chỉ ký `G4_signoff` sau khi đọc báo cáo: bảng *Sign-off conditions* cho biết điều kiện nào đạt (mọi check PASS, mọi luật có ánh xạ, mutation từng luật ≥ ngưỡng, mục tiêu coverage).

**Verification faults (triage B) | Lỗi của verification (triage B).** When triage judges a failure B (the test or the checker does not follow the specification), agent A17 can propose the fix:

```
python -m nnc fix-verif my_ip                      # --from formal|all to read work/formal_triage.json too
# read work/verif_fix/verif_fix.md: the faults as A17 saw them, the diff, the weakening check, before/after
python -m nnc fix-verif my_ip --apply --by "Name"  # copies the candidate into verif/, NOTICE.md; G3 becomes STALE
python -m nnc gate approve my_ip G3_verif_sources --by "Name" --note "fix-verif reviewed: ..."
```

How A17 is kept honest:
- **It never sees the RTL.** The fault text keeps only what the specification says and what the verification does. Code drops every sentence that names an RTL file or module, and the backend refuses inputs from `rtl/`.
- **It cannot weaken a check.** Code refuses a removed assertion, cover point, test or CHK reference, a new assumption, `$assertoff`, and a skipped or expected-to-fail test. It also refuses any change to the formal environment or to `nnc_cocotb.py`. A changed `disable iff` or a lost `assert` statement is shown as a warning.
- **The candidate is simulated on the RTL.** When a fault still fails, A17 gets the check, the number of failures and the first failure time, and tries again on its own candidate (`--rounds`, default 2).
- **Nothing changes in `verif/` before `--apply`**, and then G3 must be approved again.

**VI:**
- `fix-verif`: agent A17 sửa test hoặc checker bị triage xếp B. Nó không bao giờ thấy RTL, và code chặn mọi cách nới lỏng check.
- Bản sửa được chạy thử trên RTL. Nếu còn fail, A17 nhận lại kết quả (tên check, số lần fail, thời điểm) và sửa tiếp.
- `--apply` mới chép bản sửa vào `verif/`. Sau đó G3 phải được người duyệt lại.

**Surviving mutants, checked by formal | Mutant sống sót, kiểm bằng formal.** `python -m nnc mutate-equiv my_ip` compares each surviving mutant with the RTL using the Yosys miter that `restyle` uses. It runs in every configuration in which the mutant survived, calls no agent, and adds the results to `work/mutation.json`.
- **PROVEN:** no input sequence after reset changes an output. The mutant is equivalent, and the packet also shows the score without such mutants.
- **CEX:** the first differing outputs are named, and the trace is kept in `work/mutation_equiv/` (on your machine: waveforms are not committed). This is a change of behaviour that no check noticed, unless the input sequence breaks an environment rule: in this check, inputs are free after reset.
- **SIM_ONLY:** the line is simulation-only code, so formal cannot judge it.
- **BOUNDED:** nothing is concluded.

Run `nnc report` afterwards. — **VI:**
- `mutate-equiv` chứng minh bằng formal xem mutant còn sống có thật sự tương đương không, thay cho lời "cho là tương đương" của agent.
- Kết quả CEX kèm đầu ra khác nhau đầu tiên và chuỗi tín hiệu, để người duyệt xem đó là lỗ hổng thật hay đầu vào vi phạm luật môi trường.

**Reviewer packet | Gói cho người duyệt.** `nnc report` also writes `work/review_packet.md`: the delegated gate decisions to confirm, each failure with its triage verdict, hand edits of generated code, what was not verified and why, surviving mutants, and a checklist to answer before `G4_signoff`. Give it to the person who signs. — **VI:** `nnc report` còn tạo `work/review_packet.md`. Đây là tài liệu đưa cho người ký G4: nó chỉ gom những điểm cần con người phán đoán, kèm một danh sách câu hỏi phải trả lời trước khi ký.
- Các quyết định gate do agent đưa ra theo uỷ quyền.
- Từng lỗi, kèm kết luận của triage.
- Các chỗ code sinh ra đã được sửa tay.
- Những gì chưa kiểm được, và lý do.
- Các mutant sống sót.

**Mutation with a run set.** Mutants are drawn from the lines executed by any run; each is simulated in the first run that executed its line (primary first) and judged against that run's baseline. A survivor gets a second chance in every other configuration (first seed) that executed its line: a line can be reached in the default configuration while the changed term only matters in another one (a four-phase handshake term, an APB5 gate). The score is that of the run set as a whole. — **VI:** khi có run set, mutant được lấy từ dòng code mà bất kỳ lần chạy nào đã đi qua, và mô phỏng ở lần chạy đầu tiên đi qua dòng đó. Mutant nào sống sót thì được chạy lại ở mọi cấu hình khác cũng đi qua dòng đó. Như vậy điểm số là điểm của cả run set, không chỉ của cấu hình mặc định.

### Coverage scope | Phạm vi coverage

**EN:** Code coverage counts the elaborated design only. Each simulation run also elaborates the DUT alone,
with that run's parameters, in two tools:
- `verilator --json-only` gives the package functions the design keeps;
- Yosys `proc; flatten; opt` gives the bits that constant propagation proves constant. Yosys reads the RTL
  with `formal_frontend`.

Never-executed points of package functions the design never calls, and toggles of constant bits, are left
out:
- every row of the report says how many points were left out, and gives the count over all points;
- a left-out point that was executed is counted (`scope_conflicts`);
- a signal on which the simulator saw a constant bit toggle counts whole (`signals_kept_whole`).

There is no hand exclusion.

```bash
python -m nnc config my_ip coverage_preverified=prim_alert_sender,prim_onehot_check   # optional
```

`coverage_preverified` lists modules verified elsewhere (OpenTitan's cover.cfg lists its pre-verified
primitives). The report then adds rows with the coverage without their subtrees, next to the coverage of
the whole design, and `nnc cover` takes its target and points from those rows. See docs/SIGNOFF_SCOPE.md.

```bash
python -m nnc sim my_ip --unr               # also prove uncovered toggle bits, branches and expression points unreachable
python -m nnc config my_ip unr_cut=m_cell_sync   # modules Yosys cannot read (simulation-only models): outputs free
```

`--unr` asks SymbiYosys whether each uncovered toggle bit, each IF branch or case item never executed, and each
expression term combination never hit can change or occur after the first reset, with every input free. An
expression point is tried only when its terms read module-level signals with the value they have at the
expression (no loop variable, no function call, no write after it in its block). Toggle bits leave the metric
only when PROVEN in every configuration of the run set. Coverage keeps one record of each branch and expression
point per configuration: each configuration tries the points none of its own runs reached, and a point PROVEN in
a configuration leaves that configuration's record. The results are in `work/unr.md`. A PROVEN point is dead in this RTL, not necessarily by
design: code that a fault makes dead is left out too (ahb2axi_bridge's AXI burst path, EVALUATION §15). Check
each one against the specification before sign-off.

**VI:**
- Coverage chỉ đếm phần có trong thiết kế đã elaborate. Hàm package không bao giờ được gọi và bit luôn bằng
  hằng số (do công cụ chứng minh) bị loại.
- Báo cáo luôn ghi số điểm bị loại và con số tính trên mọi điểm. Không có loại trừ bằng tay.
- `coverage_preverified` cho thêm con số phụ "không tính các module đã verify ở nơi khác". Con số này đứng
  cạnh con số chính, không thay thế nó. `nnc cover` lấy mục tiêu và danh sách điểm từ con số phụ này.
- `--unr`: SymbiYosys kiểm từng bit toggle, từng nhánh IF/case chưa chạy và từng tổ hợp term expression chưa
  gặp, xem nó có xảy ra được sau reset đầu tiên không (mọi input tự do). Bit toggle chỉ bị loại khi PROVEN trong
  mọi cấu hình. Nhánh và điểm expression được tính riêng cho từng cấu hình: mỗi cấu hình thử các điểm mà chính
  nó chưa chạm, và điểm PROVEN ở cấu hình nào thì chỉ bị loại khỏi bản ghi của cấu hình đó. Kết quả ở `work/unr.md`.
- PROVEN nghĩa là chết trong RTL này, chưa chắc là do thiết kế: code chết vì lỗi cũng bị loại (ví dụ đường burst
  AXI của ahb2axi_bridge). Hãy đối chiếu từng điểm với spec trước khi ký.
- `unr_cut`: module Yosys không đọc được (model chỉ dùng trong mô phỏng); output của chúng thành tự do.

### Domain crossings | Kiểm tra cắt miền clock (CDC/RDC)

```bash
python -m nnc cdc my_ip                     # every parameter set of the run set -> work/cdc.md, work/cdc.json
python -m nnc cdc my_ip --check             # rerun and compare with work/cdc.json (CI), write nothing
python -m nnc config my_ip "cdc_async_inputs=i_gpio:GpioAsyncOn=1"   # inputs asynchronous to every clock
```

**EN:** RR-33 checked by structure on the flattened Yosys netlist, read as for formal. Clocks of a
`clock_relation=async` design are separate domains. Ports take the domain of the contract's `domain`
column, ASYNC, or `cdc_async_inputs` (`port` or `port:PARAM=value`). Each crossing is one of:
- **SYNC:** a chain of two or more flops, with no logic before the first and nothing else reading it;
- **SYNC_MULTIBIT** (review): bits of one register synchronized separately;
- **QUALIFIED** (review): data captured under control of a synchronized signal;
- **UNSYNC** (error);
- **FIRST_STAGE_READ** (error).

Asynchronous resets from another domain are listed for review. The report gets a row and a sign-off
condition (no error). Gray coding and handshake protocols are not proven by this check.

**VI:**
- Kiểm cấu trúc: tín hiệu sang miền clock khác có đi qua bộ đồng bộ ≥ 2 flop không.
- Nhiều bit đồng bộ riêng lẻ, hoặc dữ liệu chốt nhờ tín hiệu đã đồng bộ, thì xếp vào loại cần người xem.
- Thiếu bộ đồng bộ là lỗi.
- Bước này không chứng minh gray code hay giao thức handshake.

### Bug benchmark | Đo chất lượng flow bằng bug cài sẵn

```bash
python -m nnc bench my_ip                       # every fault of bugs/bugs.json: caught or not (no agent)
python -m nnc bench my_ip --triage AF1,AF3      # also triage the new failures of these bugs (agent cost)
```

`designs/<ip>/bugs/bugs.json` lists hand-written realistic faults, each a one-line `find`/`replace` in `rtl/` with the requirement it breaks and the expected triage verdict (`A_rtl_wrong`). The benchmark writes `bugs/<id>.diff` (so `nnc inject` reproduces one alone), runs the approved verification on a patched copy (the run set when there is one) and writes `work/bench.md`: a bug is **caught** only if a test or check fails that passes on the unmodified RTL — failures already in the baseline do not count — and the triage verdict (most frequent cause over the new failures) is compared with the expected one. — **VI:** `bugs/bugs.json` liệt kê các lỗi RTL viết tay, giống lỗi người thiết kế thật hay mắc; mỗi lỗi là một dòng `find`/`replace`. Benchmark chạy kiểm chứng đã duyệt trên bản sao RTL có lỗi, rồi ghi `work/bench.md`.
- **Bắt được:** chỉ tính khi có test/check fail mà trên RTL gốc vẫn pass. Lỗi đã có sẵn ở baseline không được tính.
- **Triage đúng:** kết luận phổ biến nhất của triage trùng với kết luận mong đợi (A = RTL sai).

### Formal check | Kiểm chứng formal

```bash
python -m nnc config my_ip formal=on                     # opt in (formal_defines=VLSIT_SYNTHESIS for simulation-only models)
python -m nnc gen-env my_ip                              # agent A13: environment assumptions -> verif/formal/nnc_env.sv
python -m nnc gate approve my_ip G3_verif_sources --by "Your Name"    # after reading every ENV-nn assumption
python -m nnc formal my_ip                               # SymbiYosys per assertion -> work/formal.md (+ formal_triage.md)
```

The open-source Yosys frontends do not accept clocked concurrent SVA, so `nnc/formal.py` **translates** the subset the checker generator emits (`A |-> B`, `A |=> B`, `##N`, `disable iff`, `$past`, `$stable`) into immediate assertions with a shift register per attempt, by code; anything else is reported UNSUPPORTED, never approximated. A failure counter incremented in procedural checker code becomes an assertion at that point. Checkers that only make sense in simulation (event timing with `$time`, scoreboard queues) are left out and listed. Checker variables start at 0 as in simulation; DUT flops keep a free initial value. Each check runs alone: **bmc** (counterexample up to `formal_depth`, default 20), **prove** (k-induction), **cover** (its antecedent can happen under the assumptions: otherwise **VACUOUS**), each limited to `formal_timeout` seconds (default 600). Synchronous designs use one global clock; `clock_relation=async` uses free clocks (every ratio and phase).

The environment: resets are asserted in the initial state (code), and `verif/formal/nnc_env.sv` holds the obligations the specification places on the blocks driving the inputs (A13 writes them from the specification only; they are part of G3 because an assumption the specification does not require hides bugs). A counterexample (CEX, trace in `work/formal/<CHK>.vcd`, written on your machine and not committed, like every waveform) goes to agent A14, which classifies it like triage plus **E: environment obligation missing**. The report gets a formal row and a sign-off condition; the reviewer packet lists every assumption.

**VI:** bật bằng `formal=on`. Yosys mã nguồn mở không đọc được SVA đồng thời có clock, nên `nnc/formal.py` **dịch bằng code** tập con mà generator sinh ra sang assertion tức thời. Phần nằm ngoài tập con báo UNSUPPORTED, không đoán. Mỗi check chạy riêng ba việc:
- **bmc:** tìm phản ví dụ trong N chu kỳ.
- **prove:** chứng minh cho mọi chu kỳ.
- **cover:** điều kiện kích hoạt có xảy ra được không; nếu không thì check là **VACUOUS** (rỗng).

**Depth escalation | Tăng độ sâu.** A check whose antecedent cannot happen within `formal_depth` cycles is VACUOUS, although it may happen later (a UART frame of 16 × 10 cycles does not fit in 64). With `formal_max_depth=N`, every VACUOUS check is run again alone at twice the depth, then twice again, up to N cycles. Its row in `formal.md` gives the depth used (`[depth 128]`). A check still VACUOUS at N stays VACUOUS. Only the vacuous checks are run again, so the cost is theirs alone. **VI:** check VACUOUS có thể chỉ vì độ sâu quá ngắn. Đặt `formal_max_depth=N` thì check đó được chạy lại riêng với độ sâu gấp đôi, cho tới N; bảng ghi rõ độ sâu đã dùng.

```bash
python -m nnc config my_ip formal_max_depth=128
```

Giả định môi trường (`nnc_env.sv`) do A13 viết từ spec và **phải được người duyệt G3 đọc**, vì một giả định spec không đòi hỏi sẽ che bug. Mỗi phản ví dụ được agent A14 phân loại: A (RTL sai), B (checker sai), C (spec không rõ) hoặc **E (môi trường thiếu giả định)**.

### Baseline: the hand-written testbench | So với testbench viết tay

```bash
python -m nnc baseline my_ip                 # bugs of bugs/bugs.json and the mutants of work/mutation.json
python -m nnc baseline my_ip --no-mutants    # bugs only
```

`designs/<ip>/baseline/` holds the testbench the RTL was delivered with (copied with its licence notice) and `baseline.json`, which says how its own script runs it: top, files, defines, pass strings, and the runs (parameters, plusargs). The baseline must pass on the unmodified RTL; then every fault of `bugs/bugs.json` and every mutant of the NNC mutation run (one changed line each) is simulated with it (Icarus Verilog, via WSL on Windows). A fault is caught, a mutant killed, when any run fails. `work/baseline.md` puts the result next to the NNC result: caught by both, by one only, by neither. — **VI:** thư mục `baseline/` chứa testbench viết tay đi kèm RTL và `baseline.json` mô tả cách chạy nó. Lệnh này chạy testbench đó trên RTL gốc (phải pass), trên từng bug cài sẵn và từng mutant của NNC, rồi đặt kết quả cạnh kết quả của NNC trong `work/baseline.md`: lỗi nào cả hai bắt được, lỗi nào chỉ một bên bắt được.

**Which failures triage analyses | Triage phân tích lỗi nào.** One triage call analyses at most 12 failures. A failing assertion is often the cause of several failing tests, so up to half of the places go to failing assertions, and places one kind does not use go to the other (`nnc/triage.py` `select`). `work/triage.md` says how many failures there were and how many were analysed. — **VI:** một lần triage phân tích tối đa 12 lỗi. Vì một assertion fail thường là nguyên nhân của nhiều test fail, tối đa một nửa số chỗ dành cho assertion; chỗ nào loại này không dùng thì nhường cho loại kia.

### Split test generation (experimental) | Sinh test chia nhỏ (thử nghiệm)

`nnc config my_ip tests_mode=split`: one call writes the shared test-bench library `tb_<ip>.py`, then one call per group of at most 5 test checks writes `test_<ip>_g<n>.py` on it, in parallel; a repair touches only the failing module (or the library). Measured on sync_fifo: US$7.2 without retries (library US$2.5 + four groups US$4.6) against US$4.5 for the single call, because every group reads the 1,300-line library; 12/15 tests passed on the first run (three failed in one library helper), against 25/25. Its only gain is that a call cut by the usage limit or a timeout loses one group, not the whole module. The single call stays the default. — **VI:** chế độ chia nhỏ: một lời gọi viết thư viện testbench chung, rồi mỗi nhóm tối đa 5 check viết một module test, chạy song song. Kết quả đo trên sync_fifo:
- Chi phí US$7.2 so với US$4.5 của cách một khối, vì nhóm nào cũng phải đọc lại thư viện.
- 12/15 test pass ở lần chạy đầu, so với 25/25.
- Lợi ích duy nhất: khi một lời gọi bị ngắt, chỉ mất một nhóm.

Vì vậy mặc định vẫn là một khối.

### Continuous integration | CI

`.github/workflows/ci.yml` runs on every push: the unit tests (Python 3.11 and 3.12), then for each design the reproduction kit `designs/<ip>/sim` with `make` only and `nnc kit-check <ip>`, which compares the outcome with the committed results (same tests, same failing tests, same failing and never-hit assertions, same NOT_VERIFIABLE checks; counts may differ). Verilator (OSS CAD Suite 2026-11-07) and cocotb 2.1.0 are pinned. No agent runs in CI. — **VI:** mỗi lần push, CI chạy hai phần, đều không gọi agent nào.
- **Unit test:** chạy trên Python 3.11 và 3.12.
- **Bộ tái lập:** với từng thiết kế, CI chạy bộ tái lập bằng `make` thuần, rồi `nnc kit-check` so kết quả với kết quả đã commit: cùng test fail, cùng assertion fail hoặc không hit.
- Phiên bản Verilator và cocotb được cố định.

**Every configuration, and formal | Mọi cấu hình, và formal.** Two more jobs run on `main`, on pull requests, every Monday and by hand (not on every push to a feature branch, because they take long):
- **kit-configs:** a run set's other configurations each have a kit folder `designs/<ip>/sim/configs/<config>/`. The file `sim/configs/runs.tsv` lists every recorded run (label, folder, seed). `.github/kit_runs.sh <ip> --skip-primary` runs each one with `make` only, and `nnc kit-check <ip> --run <label>` compares it with its own recorded result.
- **formal:** `nnc formal-check <ip>` runs SymbiYosys again with the recorded configuration. It calls no agent and writes nothing. It fails when:
  - a counterexample appears or disappears;
  - a proof becomes or stops being VACUOUS;
  - a check stops translating (UNSUPPORTED);
  - a tool reports an ERROR.

  Changes among PROVEN, BOUNDED and TIMEOUT are printed as notes. They depend on the solver time limit and on how fast the machine is.

  `--config <name>` reruns one formal configuration and compares it with the recorded result of that configuration only. CI runs uart_lite this way, one job per configuration (base, min, odd, wide): run as one job, its rerun starved a hosted runner for 96 minutes until the runner lost contact. **VI:** `--config` chỉ chạy lại một cấu hình. CI chia uart_lite thành 4 job như vậy, vì chạy chung một job thì máy CI bị quá tải và mất kết nối sau 96 phút.

`nnc kit <ip>` rewrites the kit (`sim/` and `sim/configs/`) from `work/results.json` without simulating. `nnc sim` also writes it after every regression.

```
python -m nnc kit uart_lite
bash .github/kit_runs.sh uart_lite --only min.s2      # Linux or inside WSL
python -m nnc kit-check uart_lite --run min.s2
python -m nnc formal-check gen_apb_tlul_bridge
```

**VI:**
- **kit-configs:** mỗi cấu hình khác của run set có một thư mục kit riêng trong `sim/configs/`. CI chạy từng lần chạy đã lưu bằng `make` thuần, rồi so với đúng kết quả đã lưu của lần đó.
- **formal:** `formal-check` chạy lại formal và so với kết quả đã lưu. CI fail khi:
  - phản ví dụ xuất hiện hoặc biến mất;
  - một chứng minh trở thành VACUOUS, hoặc thôi VACUOUS;
  - một check không dịch được nữa;
  - công cụ báo lỗi.

  Đổi giữa PROVEN, BOUNDED và TIMEOUT chỉ được ghi chú, vì nó phụ thuộc giới hạn thời gian của solver và tốc độ máy.

**Tool host | Máy chạy công cụ.** On Windows, `nnc doctor` also runs a short probe inside WSL. It lists Verilator, cocotb, Yosys, SymbiYosys, ABC, Yices and the GF180 liberty files. On Linux, use `--host` to run the same probe. When WSL runs no command at all (no run log), NNC waits 15 s and tries once more. If that also fails, the stage stops with `host error` (exit code 3) and records nothing. **VI:** trên Windows, `doctor` kiểm tra luôn các công cụ bên trong WSL. Khi WSL không chạy được lệnh nào, NNC đợi 15 giây rồi thử lại 1 lần. Nếu vẫn lỗi thì dừng với `host error`, không ghi kết quả nào.

**Usage limit | Hết quota.** When the Claude account's usage limit stops a call ("You've hit your 5-hour limit · resets 6:50am"), the call waits until the stated reset and runs again (at most `NNC_LIMIT_WAIT` seconds in total, default 21600; `0` fails at once). The money already spent by the interrupted call is lost: the report shows it under *failed calls*. — **VI:** khi hết quota, lời gọi agent tự đợi tới giờ reset rồi chạy lại (tối đa `NNC_LIMIT_WAIT` giây, mặc định 6 giờ; `0` = báo lỗi ngay). Tiền đã tốn cho lần gọi bị ngắt thì không lấy lại được; report ghi khoản này ở mục *failed calls*.

## 6. Design half: the flow writes the RTL | Nửa thiết kế: flow viết RTL

Gates of a design whose RTL the flow generates (`rtl_origin=generated`):

```
G1_rules -> G2_contract -> G3_verif_sources ----------> G4_signoff
                       `-> D1_config -> D2_rtl -------'
```

The RTL and the verification are both generated from G2 and never see each other; G4 needs both.

```bash
# from a short description (agent A0 drafts the specification in the shape of docs/SPEC_TEMPLATE.md)
python -m nnc spec-draft my_ip description.md --top m_my_ip --tag MY   # -> spec/, work/spec_draft.md
python -m nnc spec-check my_ip                     # can the flow read it? (port/parameter tables, legal values, IDs)
python -m nnc spec-lint my_ip                      # agent A18: gaps a reader would fill differently -> work/spec_lint.md
# ... edit the draft, then the usual flow up to G2:
python -m nnc flow my_ip                           # ingest .. review (G1), contract (G2), gen-sva/tests (G3)

# D1: the configuration of the RTL
python -m nnc params my_ip                         # parameters, defaults, legal values (parsed from the contract)
python -m nnc params my_ip --choose PARA_X_DEPTH=16 --by "Your Name"   # illegal values are refused
python -m nnc gate approve my_ip D1_config --by "Your Name"

# D2: the RTL (agent A15: spec, approved rules, interface, configuration, docs/RTL_RULES.md; never the verification)
python -m nnc gen-rtl my_ip                        # -> rtl/, work/rtl_gen.md (findings, synthesis, open points)
python -m nnc gate approve my_ip D2_rtl --by "Your Name"     # after reading work/rtl_gen.md

# verification of the generated RTL, with repair of faults judged A
python -m nnc close-loop my_ip --rounds 3          # sim -> triage -> fix-rtl, until no failure or the budget
```

- **Code checks of the RTL** (`nnc rtl-check`, run after every A15 answer): file and filelist rules, the synthesizable subset, `always_ff`/`always_comb` discipline, clock and reset names, Verilator `-Wall`, Yosys latches/loops/drivers, the ports of the contract for the chosen configuration, `// REQ:` tags, and Yosys synthesis on the GF180MCU 7-track library (typical and slow corner: area, estimated delay). The liberty files are downloaded once into `/opt/pdk` on the simulation host; without them only generic synthesis runs.
- **Repair** (`fix-rtl`, `--from sim|formal|all`): A15 receives the current RTL and, per fault that triage judged *A: RTL wrong* (simulation triage, formal counterexample triage, or both), only what the specification says and what the RTL does; any sentence that names a test, a checker or a file in `verif/` is removed. It never sees a test. Every revision is kept in `work/rtl_history/`, and D2 becomes STALE.
- **Trying it on a verified design** (`nnc derive <src> <new>`): copies the specification, rules, contract, verification and baseline testbench, carries G1–G3 over (identical hashes), leaves the RTL behind. Then `params --choose`, D1, `gen-rtl`, `close-loop`, `baseline`.
- **Specification gaps** (`nnc spec-lint`, agent A18, `--lint-model`, default opus): A18 reads only the specification and the standards. It lists the places where two careful readers, say the RTL writer and the checker writer, could build different things. Each gap has a category (events in the same cycle, a request while busy, reset during operation, back-pressure, parameter extremes, error and recovery, initial state, contradiction, other), a severity, the readings it allows, and `file:line` references; code checks every reference and counts the gaps without a valid one. Nothing is changed: the designer answers each gap in the specification (a DEC row or a new requirement) before G1. On gen_sync_fifo it found the cause of the open CHK-008 as GAP-002 (US$0.97); on spi_master, a simulation that starts without a reset (the same kind of fault as the uart_lite hand fix), answered by ENV-008 before any RTL was written.
- **Golden manifest:** a G1 approval records the SHA-256 of every registered document; when the specification changes, G1 becomes STALE.

**VI:** với thiết kế mà flow tự viết RTL, có thêm hai gate:
- **D1_config:** chọn tham số. Code kiểm tra giá trị hợp lệ theo bảng của spec.
- **D2_rtl:** duyệt RTL.

Cách làm việc:
- **Sinh RTL:** agent A15 viết RTL chỉ từ spec, luật đã duyệt, interface, cấu hình và quy tắc RTL, không bao giờ thấy bộ kiểm chứng. Code kiểm tra RTL sau mỗi lần sinh (lint, cấu trúc, cổng, synthesis GF180) và trả lỗi về cho agent sửa.
- **Vòng khép kín `close-loop`:** chạy mô phỏng bằng bộ kiểm chứng đã duyệt. Lỗi nào triage kết luận "RTL sai" thì agent sửa RTL, nhưng chỉ nhận mô tả lỗi ở mức spec, không nhận code test.
- **Ai quyết:** người duyệt quyết định ở D2 và G4.
- **Tìm lỗ hổng spec `spec-lint`:** agent A18 chỉ đọc spec, liệt kê chỗ mà người viết RTL và người viết checker có thể hiểu khác nhau, kèm các cách hiểu và dòng trích dẫn (code kiểm tra trích dẫn). Không sửa gì; người thiết kế trả lời từng chỗ trong spec trước G1.

### Restyle an existing RTL | Viết lại RTL có sẵn theo quy tắc

```bash
python -m nnc rtl-check my_ip                      # rule findings of the delivered RTL (nothing is written)
python -m nnc restyle my_ip                        # agent A16 -> restyle/rtl, restyle/restyle.md
```

A16 rewrites the RTL to follow `docs/RTL_RULES.md` without changing behaviour and reports suspected bugs instead of fixing them. Each rewrite is checked by the code checks and then by **formal sequential equivalence** with the original (`nnc/equiv.py`: a Yosys miter of both versions, every reset asserted in the first step, then SymbiYosys BMC and a PDR proof). PROVEN means every output is equal in every cycle for every input sequence, for that configuration. `rtl/` is never touched: adopting the rewrite is the designer's decision. — **VI:** A16 viết lại RTL cho đúng quy tắc mà không đổi hành vi. Chỗ nghi là lỗi thì agent chỉ báo lại, không tự sửa. Mỗi bản viết lại được chứng minh tương đương với bản gốc bằng formal: mọi output bằng nhau ở mọi chu kỳ, với mọi chuỗi input. Kết quả nằm trong `restyle/`; `rtl/` không bị đụng tới.

### Documents | Xuất tài liệu

```bash
python -m nnc export my_ip --what spec,rules,contract,rtl,report,packet --format docx,html,pdf   # -> export/
```

Pandoc (`pip install -e .[docs]`, or `pandoc` on PATH) writes DOCX and HTML; a headless Edge/Chrome/Chromium prints the PDF (`NNC_BROWSER` to choose). Standards are never exported. — **VI:** xuất spec và các báo cáo ra DOCX/HTML/PDF. Tài liệu chuẩn có bản quyền không bao giờ được xuất.

## Exploratory run | Chạy thăm dò

```bash
python -m nnc flow my_ip --unreviewed
```

**EN:** Runs everything without stopping at gates. Every artifact and the report are stamped UNREVIEWED with the gates that were bypassed; such a report cannot be signed off.

**VI:** Chạy hết không dừng ở gate. Mọi artifact và báo cáo bị đóng dấu UNREVIEWED kèm các gate đã bỏ qua; báo cáo này không thể ký duyệt.

## Re-run after a change | Chạy lại khi có thay đổi

| Change / Thay đổi | Effect / Hệ quả |
|---|---|
| Specification edited | G1 becomes STALE (its approval records the hash of every registered document), later gates BLOCKED; re-run from `ingest`; only changed batches cost tokens |
| RTL edited | delivered RTL: gates stay valid (the oracle does not depend on the RTL); re-run from `sim`. Generated RTL: D2 becomes STALE |
| Chosen configuration changed (`params --choose`) | D1 becomes STALE, then D2 BLOCKED; regenerate or check the RTL |
| Test or checker edited by hand | G3 becomes STALE; review and approve again |

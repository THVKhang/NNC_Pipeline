# Request for a G4 reviewer

**For:** a person with RTL design or verification experience, such as a lecturer, a verification engineer or a senior student in microelectronics.

**Asked of you:** read the review packet of one or more designs, and decide whether the verification evidence is sufficient. Then sign or refuse the G4 gate.

**Why a person is needed.** The project owner is a computer-science student. They delegated gates G1–G3 to an AI assistant, which recorded every decision as *delegated*. Neither the student nor the assistant is qualified to sign off hardware, so **G4 is open on every design**. Nothing in this repository should be read as sign-off until a person approves G4.

**Tiếng Việt.** Đây là lời nhờ một người có kinh nghiệm thiết kế hoặc kiểm chứng RTL (thầy cô, kỹ sư verification…) đọc gói hồ sơ của từng thiết kế và quyết định có ký G4 hay không. Chủ dự án là sinh viên khoa học máy tính, đã uỷ quyền G1–G3 cho trợ lý AI. Không ai trong hai bên đủ chuyên môn để ký phần cứng, nên G4 vẫn để trống ở mọi thiết kế.

## How to review one design

1. Open `designs/<ip>/work/review_packet.md`. It holds only what needs a human judgement:
   - the delegated decisions;
   - each failure with its triage;
   - hand edits of the generated verification;
   - what is not verified;
   - a checklist.
2. For details, use:
   - `work/report.md` (full report);
   - `work/triage.md` and `work/formal_triage.md` (analyses of failures and counterexamples);
   - `verif/formal/nnc_env.sv` (formal assumptions).
3. To reproduce without the AI tools, run `cd designs/<ip>/sim && make` (cocotb + Verilator; see `make help`).
4. Decide:
   - **Approve:** `nnc gate approve <ip> G4_signoff --by "<your name>" --note "<waivers, open items>"`.
   - **Do not approve:** write your corrections and open questions, in an issue or in a note to the owner. A decision on a G1 question can be recorded with `nnc answer <ip> <n> "<decision>" --by "<your name>"`.

## Suggested order and what to decide

| Design | Packet | State | Main questions for you |
|---|---|---|---|
| apb_tlul_bridge | [packet](../designs/apb_tlul_bridge/work/review_packet.md) | all checks pass, formal 17/17 proven | Are the 5 delegated G1 answers right? Are the formal assumptions true obligations? |
| sync_fifo | [packet](../designs/sync_fifo/work/review_packet.md) | all pass; 1 checker fix | Is the checker fix (software reset clears the scoreboard in the same cycle) correct? |
| axi2apb_bridge | [packet](../designs/axi2apb_bridge/work/review_packet.md) | all pass after a one-line RTL fix (`m_axi2apb_wr_seq.sv:344`) | Is the RTL fix right? Is round-robin arbitration the intended reading? Do 4 surviving mutants matter? |
| async_apb_bridge | [packet](../designs/async_apb_bridge/work/review_packet.md) | 35/35 checks pass in 12 configurations; 1 test fix | Is the `Completer.close` fix sound? Are 3 rules below 85 % mutation (AB2-1.3-xx) acceptable? |
| async_gray_fifo | [packet](../designs/async_gray_fifo/work/review_packet.md) | 9 checks fail, model-on runs only; triage C | See below |
| ahb2axi_bridge | [packet](../designs/ahb2axi_bridge/work/review_packet.md) and [findings](../designs/ahb2axi_bridge/fix_candidate/README.md) | 1/21 tests on the delivered RTL; 9 formal counterexamples, all judged RTL faults | See below |

### async_gray_fifo: a specification question

- **The question.**
  - REQ-VER-001 makes the metastability model delay each synchronizer bit independently.
  - Spec lines 477 and 684 and DEC-023 say that only valid Gray values reach the destination.
  - With the model on, the threshold flags (CHK-003, CHK-013, CHK-032) become optimistic.

  Which statement binds? Possible answers: a coherent model; a bound on back-to-back pointer updates; or a statement that the threshold flags may be wrong while the model is on.
- **One-domain resets.**
  - The checkers stop checking after a reset of one domain only, until both domains are reset (hand fixes 8 and 12 in [NOTICE](../designs/async_gray_fifo/NOTICE.md)).
  - This follows ASM-005 ("inconsistent and not detected") and contract CHK-023.
  - Please confirm this reading, or say what should be checked in that state.
- **The 13 hand fixes.** Do they correct the tests without weakening a requirement? (The packet lists each one.)

### ahb2axi_bridge: findings on the delivered RTL

- **Three faults are proposed, with spec references** (`fix_candidate/README.md`):
  - pipelined transfers are dropped: `m_ahb2axi_ahb_if.sv:87-88`;
  - single writes use a stale burst address: `m_ahb2axi_ctrl.sv:859-862`;
  - HREADYOUT is held low for the next address phase: `m_ahb2axi_ahb_if.sv:104-105`.

  Do you agree they are faults? Fix candidates exist for the first two. They were checked on a copy; `rtl/` is unchanged.
- **CHK-020.** Does the port table's reset-value column bind payload outputs such as `o_axi_arprot`? Spec lines 176 and 467 suggest it does not.
- **Six delegated G1 answers** (see `work/rules.md`):
  - aggregation optional;
  - 6-cycle bound only under the stated conditions;
  - read and write outstanding together neither required nor forbidden;
  - ID range only;
  - no fixed split lengths;
  - internal FIFOs checked only through the ports.
- **Formal environment.** Some counterexample traces contain AHB manager behaviour that AHB5 forbids (address and control changed while HREADY=0). Should `nnc_env.sv` assume address/control stability? The faults above occur without such behaviour too.

### Designs whose RTL the flow generated (design half)

These have two more gates, D1 (parameter values) and D2 (generated RTL). Both were approved on delegation, except D2 of gen_sync_fifo. Results: [EVALUATION.md §6](EVALUATION.md).

| Design | Packet | State | Main questions for you |
|---|---|---|---|
| gen_apb_tlul_bridge | [packet](../designs/gen_apb_tlul_bridge/work/review_packet.md), [RTL report](../designs/gen_apb_tlul_bridge/work/rtl_gen.md) | 17/17 tests, 17/17 formal proven, mutation 36/36, upstream testbench passes | Are A15's 4 open points the intended readings (spec over the generic TL-UL text)? Is the RTL acceptable to you under RR-03/24/32/33/41/44, which code does not check? |
| gen_sync_fifo | [packet](../designs/gen_sync_fifo/work/review_packet.md), [RTL report](../designs/gen_sync_fifo/work/rtl_gen.md), [formal triage](../designs/gen_sync_fifo/work/formal_triage.md) | 24/25 tests; CHK-008 fails in simulation and formal; D2 open | See below |
| uart_lite | [packet](../designs/uart_lite/work/review_packet.md), [spec](../designs/uart_lite/spec/uart_lite_Design_Specification.md) | 20/20 tests, 13/13 assertions in 4 configurations; no formal counterexample; mutation 35/36 | Are the delegated spec decisions D-001..D-012 and answers OQ-001..003 sound for a UART? Are the 2 hand fixes ([NOTICE](../designs/uart_lite/NOTICE.md)) corrections, not relaxations? Is M19 really equivalent? |

**gen_sync_fifo, CHK-008.** A second software-reset pulse can arrive while a reset sequence is running. In that case:
- **the generated RTL** remembers the pulse and starts a new sequence after one RUN cycle (REQ-SRST-008);
- **the approved check** expects `o_sw_rst_busy` to stay 0;
- **the contract** says tests must not drive such pulses, but the generated stimulus does;
- **the delivered RTL** passes, so the two RTLs differ in a case the specification leaves open.

Which reading binds? There are three options:
- an environment rule that forbids the pulse (formal triage, E);
- a checker with a pending-request model, which would be stricter (B);
- a specification change (C).

## What the evidence is, and is not

- **It is:**
  - simulation over the configurations of each specification (run sets);
  - assertions generated from the specification only (the generators never saw the RTL);
  - an optional formal check of those assertions (depth 20, plus induction);
  - mutation testing;
  - a bug benchmark.

  Overall numbers: [EVALUATION.md](EVALUATION.md).
- **It is not:** CDC/RDC analysis, STA, DFT or gate-level checks. Synthesis of generated RTL gives only area and an ABC delay estimate. Metastability is only simulated through the RTL's own model.
- **The generated tests and checkers can be wrong.** That is why the hit counters, triage and mutation results are in the packet.

Thank you. Comments by issue or e-mail to the repository owner are welcome even without a signature.

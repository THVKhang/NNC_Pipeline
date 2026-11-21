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
| axi2apb_bridge | [packet](../designs/axi2apb_bridge/work/review_packet.md) | all pass after a one-line RTL fix (`m_axi2apb_wr_seq.sv:344`) | Is the RTL fix right? Is round-robin arbitration the intended reading? Of the 4 surviving mutants, formal proves 2 equivalent (M09, M14). For M13 and M21 it finds a difference: a WRAP burst that starts at an address not aligned to its size is rejected with SLVERR by the RTL and accepted by the mutant. No test drives such a burst. Should the verification cover this defensive rejection (AB-1.1-03)? |
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
| uart_lite | [packet](../designs/uart_lite/work/review_packet.md), [spec](../designs/uart_lite/spec/uart_lite_Design_Specification.md) | 20/20 tests, 13/13 assertions in 4 configurations; no formal counterexample (4 proven, 8 bounded; CHK-004/005 reached only at 128 cycles with 4 or 5 cycles per bit, and 5 receive checks are vacuous with 16 or 1024 cycles per bit, where one frame is longer than the depth); mutation 35/36 | Are the delegated spec decisions D-001..D-012 and answers OQ-001..003 sound for a UART? Are the 2 hand fixes ([NOTICE](../designs/uart_lite/NOTICE.md)) corrections, not relaxations? M19 is proven equivalent by formal for N = 16, 4 and 5; for N = 1024 the proof did not close within the time limit (no difference within 64 cycles). Is that enough? |
| spi_master | [packet](../designs/spi_master/work/review_packet.md), [spec](../designs/spi_master/spec/spi_master_Design_Specification.md), [A17 changes](../designs/spi_master/NOTICE.md) | 15/15 tests, 27/27 assertions in 3 configurations (D = 4, 1, 255); formal 6 proven, 7 bounded, 14 simulation-only, no counterexample; mutation 33/36, the 3 survivors proven equivalent | Are the 5 changes by agent A17 (7 simulation failures and 6 formal counterexamples, all judged verification faults) corrections, not relaxations? Is CPOL_b/CPHA_b "captured once at burst start" the right reading? No test completes a burst of 17 bytes or more (COVP-013/014); the spec asks only for "at least 16". Is that enough? |
| axil_regfile | [packet](../designs/axil_regfile/work/review_packet.md), [spec](../designs/axil_regfile/spec/axil_regfile_Design_Specification.md), [RTL report](../designs/axil_regfile/work/rtl_gen.md) | 21/21 tests, 17/17 assertions in 4 configurations (1, 8 and 16 registers); formal 15 proven, 1 bounded, no counterexample; mutation 27/29, the 2 survivors proven equivalent; no fix of any kind | Are the delegated decisions D-014..D-018 sound for an AXI4-Lite slave? **Timing (REQ-IMP-001, open at D2):** ABC estimates the longest combinational path at 31.5 ns at the SS corner against a 20 ns period (16.9 ns at TT), without wires. Would you accept the RTL pending STA, or ask for a registered read path? |

**gen_sync_fifo, CHK-008.** A second software-reset pulse can arrive while a reset sequence is running. In that case:
- **the generated RTL** remembers the pulse and starts a new sequence after one RUN cycle (REQ-SRST-008);
- **the approved check** expects `o_sw_rst_busy` to stay 0;
- **the contract** says tests must not drive such pulses, but the generated stimulus does;
- **the delivered RTL** passes, so the two RTLs differ in a case the specification leaves open.

Which reading binds? There are three options:
- an environment rule that forbids the pulse (formal triage, E);
- a checker with a pending-request model, which would be stricter (B);
- a specification change (C).

`nnc spec-lint gen_sync_fifo` (agent A18, specification only, US$0.97) lists this case as GAP-002 [high], with three readings: a pending flop latches the pulse, a short pulse is lost, or a pulse in REQ/PTR merges into the running sequence. The generated RTL took the first reading; the delivered RTL and the checker took the second. See [spec_lint.md](../designs/gen_sync_fifo/work/spec_lint.md) for this and 11 other gaps.

### An industrial design: OpenTitan rv_timer

| Design | Packet | State | Main questions for you |
|---|---|---|---|
| ot_rv_timer | [packet](../designs/ot_rv_timer/work/review_packet.md), [spec](../designs/ot_rv_timer/spec/rv_timer_Design_Specification.md) (decisions D-001..D-020 in §8), [formal triage](../designs/ot_rv_timer/work/formal_triage.md), [A17 changes](../designs/ot_rv_timer/NOTICE.md) | 23/23 tests, 13/13 assertions, 2 seeds; formal 7 proven, 2 bounded, 1 timeout (CHK-011), 2 simulation-only, **1 counterexample (CHK-008)**; mutation 21/36, of the 15 survivors 11 proven equivalent (84.0 % without them); no hand fix | The OpenTitan RTL is unchanged; only the wrapper `ot_rv_timer_nnc.sv` was written here. Are the delegated decisions D-001..D-020 sound readings of the OpenTitan documents? Are the A17 changes (4 simulation failures, 2 formal counterexamples, all judged verification faults) corrections, not relaxations? See CHK-008 below. |

**ot_rv_timer, CHK-008: may the test bench send a non-contiguous byte mask?** CHK-008 checks only the stimulus. Formal finds a request with `a_mask` = `0101`; the DUT answers `d_error` = 1, which TL-UL allows. Two passages disagree:
- the TL-UL specification says hosts in OpenTitan "do not leverage non-contiguous masks" (rule TL-T3.1.3.4-02, which CHK-008 checks);
- the rv_timer integration text (RT-4.1-05) says requests the TL-UL specification lists as error cases, "bad size or mask" among them, are legal stimulus. The formal environment follows this.

Triage judged it a missing environment assumption (E). The formal-environment agent declined to add the assumption, citing RT-4.1-05 and D-013. By the project owner's decision nothing was changed. Which reading binds?
- If non-contiguous masks are forbidden, the assumption suggested in `formal_triage.md` (ENV-11) is added.
- If they are legal error stimulus, the mask term of CHK-008 and TL-T3.1.3.4-02 leave the check.

**ot_rv_timer, other open items.**
- CHK-011 (`d_error` for each kind of request) did not finish in formal within 600 s per task. It passes in simulation.
- Three surviving mutants change behaviour, but only in cases the decisions leave unchecked: instruction fetches (M01, D-011), `d_data` of error responses (M14, D-015), and alert timing after an integrity error (M19, D-010). Should any of these become checked?
- Per-requirement mutation is below 85 % for 9 rules, mostly alert and integrity rules.

### A second OpenTitan IP: gpio

| Design | Packet | State | Main questions for you |
|---|---|---|---|
| ot_gpio | [packet](../designs/ot_gpio/work/review_packet.md), [spec](../designs/ot_gpio/spec/gpio_Design_Specification.md) (decisions D-001..D-022 in §10), [triage](../designs/ot_gpio/work/triage.md), [CHK-003 formal counterexample and its fix](../designs/ot_gpio/work/verif_fix/verif_fix.md), [A17 changes](../designs/ot_gpio/NOTICE.md) | 26/26 tests, 13/13 assertions in 5 runs (4 configurations); formal 10 proven, 1 timeout (CHK-013), 2 simulation-only, no counterexample; mutation 21/36, of the 15 survivors 9 proven equivalent (77.8 % without them); no hand fix | The OpenTitan RTL is unchanged; only the wrapper `ot_gpio_nnc.sv` was written here. Are the delegated decisions D-001..D-022 sound readings of the OpenTitan documents? Are the A17 changes (3 simulation failures, 1 formal counterexample, all judged verification faults) corrections, not relaxations? See below. |

**ot_gpio, questions.**
- **CHK-006, when does a register write take effect?** No document says whether a write to `INTR_ENABLE` takes effect at the TL-UL request (A handshake) or at its response (D handshake). The RTL applies it at the request. A17 changed CHK-006 so that bits an outstanding write sets from 0 to 1 are not checked until its response. Is that window acceptable, or should the specification bind the A handshake?
- **CHK-003, may the alert come before the request is accepted?** OpenTitan raises the integrity alert while a request with a bad command integrity is presented (`a_valid` = 1), before it is accepted. D-017 only bounds the alert from acceptance. CHK-003 now counts the request from `a_valid`. Is that the intended reading?
- **D-002, D-004, D-007:** the documents disagree on `MASKED_OE_*` bits 31:16 (text: read 0, field table: rw), on whether `INTR_ENABLE` gates detection or only the output, and do not give the exact input filter threshold. Only what every reading has in common is checked. Should any of these be decided?
- Four surviving mutants change behaviour, each in a case the decisions leave unchecked: instruction fetches (M12, D-011), `d_error` in the first cycle after reset when no response is valid (M15), the input path in the first cycles after reset (M02, D-003/D-008), and the timing of later alert pulses (M21, D-010/D-017). Should any of these become checked?
- Per-requirement mutation is below 85 % for 13 rules, mostly alert, integrity and filter rules. CHK-013 did not finish in formal within 600 s per task; it passes in simulation.

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

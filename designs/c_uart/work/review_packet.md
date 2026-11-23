# Sign-off packet — c_uart

This packet is for the person who decides gate **G4 (sign-off)**: *is this design verified well enough against its specification to release?* It collects only the items that need a human judgement. Everything else is in `work/report.md` (all checks and rules) and `work/triage.md`.

## 1. Summary

- **Requirements (rules):** 6 — FAILED 6
- **Checks:** 11 — FAIL 5, PASS 6
- **Tests:** {'fail': 3, 'pass': 5}
- **Simulated configuration:** one (parameters {'DATA_WIDTH': 8}, seed 1)
- **Code coverage:** line 97.6 %, block 93.2 %, expression 88.9 %, toggle 74.1 %, functional 90.0 %
- **Mutation score:** 83.3 % (10 of 12 injected faults detected)

## 2. Decisions taken for you

These gates were approved by an AI agent on delegation, not by a qualified person. Read each note.

- **G1_rules** (2026-11-23T09:57:44+00:00): Not a hardware designer's review. Blind run (ROADMAP 21.6): approved as produced, no rule edited. 6 rules kept, 4 rejected. The open question (overrun: which word is discarded; busy window) is left open, not answered. The README states no serial frame format (start, data, stop bits), so no rule covers the serial line encoding.
- **G2_contract** (2026-11-23T09:59:43+00:00): Not a hardware designer's review. Blind run (ROADMAP 21.6): approved as produced. 11 checks (4 assertions, 7 tests) cover the 6 rules. The contract assumes an 8N1 frame (start bit 0, 8 data bits LSB first, stop bit 1) and a bit period of 8*prescale cycles: the README does not state the frame format; this assumption is for the G4 reviewer.
- **G3_verif_sources** (2026-11-23T10:10:46+00:00): Not a hardware designer's review. Blind run (ROADMAP 21.6): approved as generated, nothing edited. 8 cocotb tests, 4 checker groups and 40 cover points, lint clean; no test reads a signal inside the DUT. Formal is off (default configuration).

## 3. Failures and what they mean

Checks not passing: CHK-001, CHK-005, CHK-007, CHK-008, CHK-011. The triage agent read the specification, the RTL, the tests and the logs, and gives the most likely cause. It changes nothing; you decide.

### test_chk_007_rx_overrun — CHK-001 (Python sink checker): "m_axis stalled with tvalid=1 tdata=0x3c after tready=0 got tvalid=1 tdata=0xc3 at edge 322" (sim.log:…

- **Most likely:** the specification is unclear or contradicts itself
- **Specification:** spec/c_uart_Design_Specification.md:36-38: "Data is transferred from the source to the destination only when both tvalid and tready are high, otherwise the bus is stalled." spec:42-44: "If the data word currently in the tdata output register is not read before another word is received, then a single cycle pulse will be emitted from overrun_error and the word is discarded." The spec does not say which word is discarded. rules.json:167 (UA-T1.3-07 statement) reads it as "discards the newly receiv…
- **RTL:** rtl/uart_rx.v:120-125: when the stop bit is sampled (bit_cnt==1) and rxd_reg==1, the RTL always runs m_axis_tdata_reg <= data_reg (l.123) and m_axis_tvalid_reg <= 1 (l.124). It only flags overrun_error_reg <= m_axis_tvalid_reg (l.125). Nothing stops the write when a word is already pending (m_axis_tvalid_reg=1, m_axis_tready=0). So at W2's stop-bit sample (edge 322, about t2+153), the pending 0x3C in the output register is replaced by 0xC3 while tvalid stays 1 and tready=0. The old word is the …
- **Options:** (1) Clarify spec: answer rules.json question UA-T1.3-07 by stating which word is discarded on overrun, and whether the AXI stall rule (spec:36-38) applies to m_axis during overrun. (2) If the answer is 'keep the pending word': fix RTL uart_rx.v:122-125 so tdata/tvalid are only loaded when !m_axis_tvalid_reg || m_axis_tready (e.g. `if (m_axis_tvalid_reg && !m_axis_tready) overrun_error_reg <= 1; else begin m_axis_tdata_reg <= data_reg; m_axis_tvalid_reg <= 1; end`). The existing CHK-001/CHK-007 …

### test_chk_008_rx_frame_error — "CHK-008: m_axis_tvalid=0 from bad frame until valid frame at every edge 9..513 got m_axis_tvalid=1 at edge 314 (1 violating edge…

- **Most likely:** the specification is unclear or contradicts itself
- **Specification:** spec/c_uart_Design_Specification.md:44-46: "If the receiver does not get a stop bit of the right level, then a single pulse will be emitted from the frame_error output and the received word will be discarded." (rules.json:180, UA-T1.3-08). The spec says nothing about start-bit detection, break or a line held low after a bad stop bit, or when the receiver may look for the next start bit. contract.json:269-270 (CHK-008) adds: the bad stop bit is "held at 0 for a full bit period", and "m_axis_tval…
- **RTL:** Reconstructed from the RTL with tb=9, bp=16, prescale=2. Start detected at edge 11 (uart_rx.v:132-136, prescale_reg=(2<<2)-2=6), start bit confirmed at edge 18 (l.108-111), data bits at 34..146 (l.116-119). The stop bit is sampled at edge 162 with rxd_reg=0, so frame_error pulses (l.127) and 0xA5 is discarded, as the spec requires. Edge 163: bit_cnt=0, so the idle branch (l.130-137) sees rxd_reg still 0 (the stop bit is held low until the falling edge after 169) and starts a NEW reception on le…
- **Options:** (1) Clarify spec: add a rule on receiver resynchronisation after a frame error, e.g. 'after a frame error the receiver waits for rxd=1 before detecting a new start bit', and say whether start detection is edge- or level-based. (2) If such a rule is adopted: fix RTL. Track rxd high after a frame error, e.g. add an 'wait_idle' flag set at uart_rx.v:127 and cleared when rxd_reg==1, and gate the idle-branch start at l.132 with it, or detect start on a 1->0 transition of rxd_reg. CHK-008 then stands…

### test_regression_random — CHK-001 (Python sink checker): "m_axis stalled with tvalid=1 tdata=0x75 after tready=0 got tvalid=1 tdata=0x5b at edge 522" (sim.log:7…

- **Most likely:** the specification is unclear or contradicts itself
- **Specification:** Same as the first analysis. spec:36-38 "Data is transferred ... only when both tvalid and tready are high, otherwise the bus is stalled." spec:42-44 "... a single cycle pulse will be emitted from overrun_error and the word is discarded." The open question at rules.json:300-301 (which word is discarded) is unanswered (rules.json:304). The contract (contract.json:181, 317) and the reference model (test l.302-304) take 'new word discarded, pending word kept'.
- **RTL:** uart_rx.v:120-125: on a good stop bit the RTL loads m_axis_tdata_reg <= data_reg unconditionally (l.123) and pulses overrun_error if a word was already pending (l.125). In the regression this happens at edge 522 (about 5.2 us into the test, so the first prescale=2 pass). The pending 0x75 is replaced by 0x5b while tvalid=1 and tready=0. The SVA summary shows only one CHK-001 fail for the whole sim (sim.log:139). The regression is the last test, and the sim appears to end at the Python failure be…
- **Options:** Same root cause and decision as test_chk_007_rx_overrun; one decision resolves both. (1) Clarify which word is discarded on overrun, answering the rules.json:300 question. (2) If the pending word is kept: gate the load at uart_rx.v:123-124 on (!m_axis_tvalid_reg || m_axis_tready) and pulse overrun_error otherwise. The regression then needs no change. (3) If the old word is overwritten: update contract.json:181 and the UartRefModel. In rx_good(pending=True), replace the last expected word with t…

### Assertion CHK-001 (SVA a_CHK_001, verif/sva/nnc_chk_axis.sv:25-27): hits=405 fails=1, first fail 254585000 ps (sim.log:94, 139; results.json:92-96)

- **Most likely:** the specification is unclear or contradicts itself
- **Specification:** contract.json:181 (CHK-001, rules UA-T1.3-05 and UA-T1.3-07): "If rst=0, m_axis_tvalid=1 and m_axis_tready=0 at rising edge N ... then at rising edge N+1 m_axis_tvalid=1 and m_axis_tdata equals its value at edge N ... even if another frame finishes on rxd in the meantime (overrun discards the new word)." Source text: spec:36-38 ("otherwise the bus is stalled") and spec:42-44 ("... the word is discarded"). Which word is discarded is not stated; the question at rules.json:300-301 is still open.
- **RTL:** uart_rx.v:101-103 clears tvalid only on a handshake, which is correct for normal stalls (404 of 405 stall cycles pass). uart_rx.v:120-125: when a frame's stop bit is good, l.123 writes m_axis_tdata_reg <= data_reg even if m_axis_tvalid_reg=1 and m_axis_tready=0, and l.125 raises overrun_error. The one failing evaluation is at the W2 (0xC3) stop-bit sample in test_chk_007 (fail time 254585000 ps matches sim.log:41/48), where tdata goes 0x3C -> 0xC3 under stall. COVP-016 'overrun pulse while pend…
- **Options:** (1) Clarify spec: the designer answers the rules.json:300 question and states whether the m_axis stall rule holds during overrun. (2) If the stall rule holds (pending word kept): fix RTL uart_rx.v:122-125 to load tdata/tvalid only when !m_axis_tvalid_reg || m_axis_tready, and otherwise just pulse overrun_error. a_CHK_001 stays unchanged and should then pass. (3) If overwrite is the intended behaviour: change contract.json:181 and the rule statement (rules.json:167) to describe it. Keep a_CHK_00…

## 5. What this verification does not cover

Outside this flow in every case: formal proof, CDC/RDC analysis, static timing, synthesis, DFT.

## 6. Weak spots of the verification itself

Mutation testing changed one RTL line at a time (12 faults). A fault no check notices is a gap, unless it changes nothing visible (an *equivalent* mutant, claimed below by an agent).

- M02 `uart_tx.v:105` zero_to_one: claimed equivalent: data_reg is 9 bits and bit_cnt starts at 9, so there are only 8 shifts at line 105. The bit shifted into data_reg[8] would reach txd only on a 9th shift, which never happens. The stop bit comes from …
- M04 `uart_tx.v:97` one_to_zero: claimed equivalent: The top bit of data_reg (the constant 1 loaded here) is never shifted out. Only 8 shifts occur, which output data bits 0..7, and the stop bit is driven separately by txd_reg<=1. Changing this bit has…

Code or cover points never reached (first ones):

- line uart_rx.v:112
- line uart_rx.v:113
- line uart_rx.v:114
- functional nnc_cov.sv:0 COVP-021
- functional nnc_cov.sv:0 COVP-035
- functional nnc_cov.sv:0 COVP-038
- functional nnc_cov.sv:0 COVP-039

## 7. Reproduce without NNC

`designs/c_uart/sim/` holds a Makefile that runs the same regression with Verilator and cocotb only (Linux or WSL):

```bash
cd designs/c_uart/sim
make regression SEED=1 2>&1 | tee sim.log
cd ../../.. && python -m nnc kit-check c_uart    # same outcome as the recorded results?
```

## 8. Checklist before signing

Answer every item. Sign only if each one is true, or record why not in the approval note:

- [ ] I have read the delegated decisions of G1_rules and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G2_contract and agree with them (or I have corrected them).
- [ ] I have read the delegated decisions of G3_verif_sources and agree with them (or I have corrected them).
- [ ] The specification question behind “test_chk_007_rx_overrun — CHK-001 (Python sink checker): "m_axis stalled with tvalid=1 td…” is decided by the specification owner, and the spec, contract or checker is updated.
- [ ] The specification question behind “test_chk_008_rx_frame_error — "CHK-008: m_axis_tvalid=0 from bad frame until valid frame …” is decided by the specification owner, and the spec, contract or checker is updated.
- [ ] The specification question behind “test_regression_random — CHK-001 (Python sink checker): "m_axis stalled with tvalid=1 tda…” is decided by the specification owner, and the spec, contract or checker is updated.
- [ ] The specification question behind “Assertion CHK-001 (SVA a_CHK_001, verif/sva/nnc_chk_axis.sv:25-27): hits=405 fails=1, fir…” is decided by the specification owner, and the spec, contract or checker is updated.
- [ ] Each surviving mutant is either truly equivalent or a known gap I accept.
- [ ] The unreached code and cover points are unreachable by design or accepted.
- [ ] I reproduced the regression (or CI did) and the outcome matches the report.

Then: `nnc gate approve c_uart G4_signoff --by "<your name>" --note "<waivers, open items>"`. The approval is bound to the current results.json: a later run makes it STALE.

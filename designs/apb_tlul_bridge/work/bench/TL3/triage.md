# Failure triage

Failures: 9; analysed: 9. The designer decides; nothing was changed.

## 1. test_chk_019_device_error — CHK-010: expected o_apb_prdata=0x00000000 at cycle 10 got 0x85e4e086

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec/m_apb_tlul_bridge_Design_Specification.md:118 REQ-FUNC-006: "shall return the TL-UL d_data on o_apb_prdata for a read that completes without error and shall drive o_apb_prdata to 0 for a write completion and for every error completion." spec:403: "w_resp_rdata | (reg_a_rd and not w_resp_err) ? i_tlul_d_data : 32'h0". spec:179: "w_resp_rdata ... Read data, already forced to 0 for writes and for errors". spec:472 ERR-003: "i_tlul_d_error = 1 on the accepted response | PSLVERR = 1, PRDATA = 0, with PREADY". spec:704 DEC-009: "PRDATA is 0 on every error and write completion". rules.json:745-750 (BR-3-10), :3909-3914 (BR-12-05) and :1641-1646 (BR-5.1-03) quote the same text. contract.json:726-728 CHK-019 expects o_apb_prdata=32'h0 at E3 for each d_error transfer. |
| RTL does | rtl/m_tlul_if.sv:106 `assign o_resp_rdata = reg_a_rd ? i_tlul_d_data : '0;`. It gates only on read/write and never uses w_resp_err (computed at :100-101), so the comment at :103 ("read data only for an error-free read, zero otherwise") does not match the code. rtl/m_apb_if.sv:115-118 then loads `w_prdata_nxt = i_resp_rdata` on the response, and the comment at :105 says it is "already zero for writes and errors". In the failing cycle the first transfer is a read (i=0, w=0) answered with d_error=1 and nz32 data. w_resp_err=1, so PSLVERR=1 is correct (the pslverr assert at test:227 passed first). But reg_a_rd=1, so reg_prdata takes d_data 0x85e4e086 and drives it at E3 (cycle 10). |
| Test does | verif/tests/test_apb_tlul_bridge.py:758-765 builds 12 pairs. Each pair is an error transfer with resp='derr' (alternating read/write, i%2, so the first one is a read) and d_data=nz32(q), which is non-zero, followed by an error-free read. The port monitor at test:274-279 computes err from the sampled d_error/d_opcode/d_source and expects prdata = d_data only if exp_get and not err, else 0. That is a direct encoding of contract CHK-010 (contract.json:535). It flags the error at test:229. The expected value 0 is taken from the spec, not from the RTL. The SVA a_CHK_010 (verif/sva/nnc_chk_cross.sv:129-133) and a_CHK_005 (nnc_chk_apb.sv:83) encode the same rule and also failed (7 fails each, first at 1895000 ps = this test's cycle). |
| A_rtl_wrong | For: Spec:403 says w_resp_rdata must be gated by `not w_resp_err`. RTL m_tlul_if.sv:106 omits that term. The RTL's own comments (m_tlul_if.sv:103, m_apb_if.sv:105) describe the intended zeroing. Only read+error cases fail: writes already give 0 via reg_a_rd=0. PSLVERR is correct, so the error detection works and only the data gating is missing. Independent SVA checkers CHK-010 and CHK-005 fail at the same time (TASK.md: first_fail_time 1895000 for both).<br>Against: None found. No spec text allows d_data to pass through on an error completion. |
| B_test_wrong | For: None found. The expected value comes from the contract and spec text.<br>Against: The test expectation (test:279, test:157 ref_expect `prdata = 0 if (t.write or err) else t.d_data`) matches spec:118, :403, :472 and contract CHK-010/CHK-019. The stimulus is legal: correct opcode and source, d_error=1, and a response in the cycle after acceptance. |
| C_spec_unclear | For: spec:235 says PRDATA "holds its last value otherwise", but that only covers non-PREADY cycles.<br>Against: rules.json:7732-7733 clarification answer: "PRDATA is 0 for every error completion, including local errors. The 'holds its last value' text applies only when PREADY is not asserted." REQ-FUNC-006, DEC-008/009 and spec:403 are explicit and consistent. |
| Options | Fix RTL (recommended by evidence): in rtl/m_tlul_if.sv:106, change to `assign o_resp_rdata = (reg_a_rd & ~w_resp_err) ? i_tlul_d_data : '0;` to match spec:403. Alternatively, in rtl/m_apb_if.sv:118, load `i_resp_err ? '0 : i_resp_rdata`, but then the spec:179 wire contract still would not hold, so the m_tlul_if fix is preferred. No test change is needed. A spec change would only be needed if the designer wants d_data to leak on read errors, which contradicts REQ-FUNC-006 and DEC-009 as confirmed on 2026-10-18. |

## 2. test_chk_020_wrong_opcode_source — CHK-010: expected o_apb_prdata=0x00000000 at cycle 11 got 0x5c5f08b5

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:118 REQ-FUNC-006 (PRDATA 0 for every error completion). spec:274: "TL-UL response with a wrong d_opcode or d_source | ... | PSLVERR = 1, PRDATA = 0 | REQ-ERR-004, REQ-ERR-005". spec:410 OP-004: "d_error = 1, a wrong d_opcode or a wrong d_source | Response consumed | PREADY = 1 with PSLVERR = 1, PRDATA = 0". spec:403: w_resp_rdata = (reg_a_rd and not w_resp_err) ? i_tlul_d_data : 0. contract.json:748-750 CHK-020 expects o_apb_prdata=32'h0 at E3. |
| RTL does | rtl/m_tlul_if.sv:99-101: w_resp_err is 1 for a read answered with d_opcode=3'b000, so PSLVERR is 1 (correct). But rtl/m_tlul_if.sv:106 forwards i_tlul_d_data whenever reg_a_rd=1, ignoring w_resp_err. rtl/m_apb_if.sv:118 loads it into reg_prdata, so the APB output at E3 (cycle 11) is the non-zero d_data 0x5c5f08b5. The failing transfer is the first bad transfer: a read with bad_op=0 (AccessAck instead of AccessAckData). |
| Test does | test_apb_tlul_bridge.py:783-794 runs reads with bad opcodes {0,2..7}, writes with bad opcodes {1..7} and source-mismatch reads/writes, all with nz32 d_data. Each is followed by a correct read. The monitor's expected value is computed at test:274-279 from the CHK-010 contract formula: err=1 because d_opcode != 3'b001, so the expected prdata is 0. The check fails at test:229. |
| A_rtl_wrong | For: Same root cause as CHK-019: m_tlul_if.sv:106 lacks the `& ~w_resp_err` term required by spec:403. A read with a wrong opcode is an error completion with reg_a_rd=1, so d_data leaks. Write cases would not fail because reg_a_rd=0, which is consistent with the first failure being the first (read) transfer.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The expected value matches spec:274, :410, :403 and contract CHK-020. The stimulus (wrong opcode, correct source, d_error=0) is exactly what contract.json:749 describes. |
| C_spec_unclear | For: None specific.<br>Against: The spec is explicit and consistent for opcode/source errors (spec:274, :410, :703 DEC-008: "any failure gives PSLVERR = 1 and PRDATA = 0"). |
| Options | Fix RTL: rtl/m_tlul_if.sv:106 → `assign o_resp_rdata = (reg_a_rd & ~w_resp_err) ? i_tlul_d_data : '0;`. This single change addresses all 9 listed failures. No test or spec change is indicated. |

## 3. test_chk_025_ignored_inputs — CHK-010: expected o_apb_prdata=0x00000000 at cycle 39 got 0x4c70e8a7

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:118 REQ-FUNC-006, spec:273/:472 (d_error → PSLVERR=1, PRDATA=0), spec:403 w_resp_rdata gated by not w_resp_err. contract.json:838 CHK-025 stimulus includes "one d_error" transfer, and :839 expects results "equal to the reference model results of CHK-018, CHK-019, CHK-023, CHK-024", which is PRDATA=0 for the d_error transfer. |
| RTL does | rtl/m_tlul_if.sv:106 passes i_tlul_d_data to the APB side for any read response, including one with d_error=1. rtl/m_apb_if.sv:115-118 registers it, so o_apb_prdata=0x4c70e8a7 at the completion edge (cycle 39) of the d_error transfer in the fixed 12-transfer sequence. The d_error transfer is presumably a read; a write would give 0 through reg_a_rd=0. |
| Test does | The test runs the fixed 12-transfer sequence (writes, reads, an illegal strobe, a misaligned access, one d_error) eight times, once per PPROT value, with random d_param/d_size/d_sink/d_user. The per-edge port monitor (test:224-230, expected value from test:274-279 per contract CHK-010) expects prdata=0 for the counted response with d_error=1. The failure is in the first repeat (cycle 39), before any cross-repeat comparison, so it is not about the ignored inputs themselves. |
| A_rtl_wrong | For: Same missing error gating at m_tlul_if.sv:106 versus spec:403. The failure appears at the d_error completion, not as a difference between repeats, so the ignored-input logic is not implicated.<br>Against: I did not read the exact test body (around test_apb_tlul_bridge.py:960-997) to confirm the d_error transfer is a read, but a write could not produce non-zero PRDATA through m_tlul_if.sv:106. |
| B_test_wrong | For: None.<br>Against: The monitor formula is the contract CHK-010 behavior verbatim and is shared with all other tests that pass the error-free cases. |
| C_spec_unclear | For: None.<br>Against: The d_error → PRDATA=0 requirement is explicit (spec:273, :472, :118). |
| Options | Fix RTL at rtl/m_tlul_if.sv:106 (add `& ~w_resp_err`). Then rerun CHK-025 to confirm that the cross-repeat identity check also passes. No test change. |

## 4. test_chk_028_back_to_back — CHK-010: expected o_apb_prdata=0x00000000 at cycle 1035 got 0x61545236

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:896 CHK-028 device modes include "prompt with i_tlul_d_error=1", and :897 expects results "of CHK-018, CHK-019...", i.e. PSLVERR=1 and PRDATA=0 for d_error transfers (CHK-019, contract.json:728). Spec:118 REQ-FUNC-006, spec:403, spec:472 ERR-003. |
| RTL does | In the d_error device mode, a read's completion gets o_apb_prdata = d_data because rtl/m_tlul_if.sv:106 (`reg_a_rd ? i_tlul_d_data : '0`) ignores w_resp_err (:100), and rtl/m_apb_if.sv:118 registers it. At cycle 1035 this gives 0x61545236 instead of 0. The failure is late (cycle 1035) because the prompt and same-cycle modes run first and have no errors. |
| Test does | The test runs every ordered pair of {W, R, ILS, MIS} under prompt, same-cycle and prompt+d_error device modes, with psel held and with gaps. The monitor at test:274-279 computes err=1 from d_error and expects prdata=0 (test:229). |
| A_rtl_wrong | For: The first failure appears only once the d_error mode starts (late cycle number). All earlier error-free back-to-back pairs passed CHK-010, so the timing and level-Setup logic are fine and only the read-error data gating is wrong (m_tlul_if.sv:106 vs spec:403).<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The expected value follows the contract/spec. The stimulus is legal per CHK-028. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit. |
| Options | Fix RTL at rtl/m_tlul_if.sv:106. No test or spec change. |

## 5. test_chk_029_random_scoreboard — CHK-010: expected o_apb_prdata=0x00000000 at cycle 72 got 0x1483030a

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:916-917 CHK-029: injects d_error, wrong opcode and wrong source at about 5% each; expected "o_apb_prdata = d_data for error-free reads, else 0". Spec:118, :403, :410. |
| RTL does | For a random read with an injected response error (d_error, opcode or source), rtl/m_tlul_if.sv:106 forwards d_data and rtl/m_apb_if.sv:118 registers it. At cycle 72 this gives PRDATA=0x1483030a with PSLVERR=1. |
| Test does | 10000-transfer constrained-random run with error injection. The per-edge monitor (test:274-279, test:229) expects prdata=0 when err=1, using the contract CHK-010 formula. The first injected read-error completion fails at cycle 72. |
| A_rtl_wrong | For: Same mechanism: the error gating is missing at m_tlul_if.sv:106. The early failure (cycle 72) matches the ~15% total error injection rate.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The scoreboard rule comes directly from contract.json:917 and spec REQ-FUNC-006. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit. |
| Options | Fix RTL at rtl/m_tlul_if.sv:106. Rerun with the recorded seed to confirm. |

## 6. test_regression_random — CHK-010: expected o_apb_prdata=0x00000000 at cycle 132 got 0x1586cd57

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Spec:118 REQ-FUNC-006, spec:403 (w_resp_rdata gated by not w_resp_err), spec:410 OP-004 (PSLVERR=1, PRDATA=0 for d_error/opcode/source errors). Contract CHK-010 (contract.json:535): prdata = d_data only when exp_get=1 and err=0. |
| RTL does | rtl/m_tlul_if.sv:106 does not gate on w_resp_err. A read error completion at cycle 132 shows d_data 0x1586cd57 on o_apb_prdata through rtl/m_apb_if.sv:118. |
| Test does | The random regression drives random transfers and device responses that include error cases (the error is visible because the monitor computed err=1). The expected value comes from the monitor's CHK-010 formula (test:274-279), and the check fails at test:229. |
| A_rtl_wrong | For: Same signature as the other 6 test failures (non-zero random d_data where 0 is expected, PSLVERR check already passed). Same RTL line.<br>Against: I did not read the body of test_regression_random (test:~1280-1317), so its exact error mix is inferred from the failure. |
| B_test_wrong | For: None.<br>Against: The expected value comes from the shared contract-derived monitor. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit. |
| Options | Fix RTL at rtl/m_tlul_if.sv:106. No test change. |

## 7. test_cov_101_long_response_delay — CHK-010: expected o_apb_prdata=0x00000000 at cycle 196 got 0xefab3694

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Spec:472 ERR-003 (d_error → PSLVERR=1, PRDATA=0), spec:118, spec:403. Contract CHK-010/CHK-005. |
| RTL does | For the long-delay read with d_error=1 (j=12 or 20), the response is counted in ENUM_ST_WAIT (rtl/m_tlul_if.sv:93-95). w_resp_err=1 so PSLVERR=1, but o_resp_rdata = d_data because reg_a_rd=1 (:106). reg_prdata loads it (rtl/m_apb_if.sv:118), so PRDATA=0xefab3694 at cycle 196. The long-delay error-free transfers before it pass. |
| Test does | verif/tests/test_apb_tlul_bridge_cov1.py:36-42: 8 long-delay ok transfers, 2 back-pressure ok transfers, then reads with resp='derr' and j=12 and j=20 (:41-42), d_data=nz32. The base monitor (test_apb_tlul_bridge.py:229) fails first. The test's own check at cov1:84-92 would also expect exp_prd=0 when err=1. |
| A_rtl_wrong | For: All 10 error-free long-delay transfers pass. The failure is at the first derr read (cov1:41), late in the sequence (cycle 196). Same missing gating at m_tlul_if.sv:106.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: cov1:85 `exp_prd = t.d_data if (not t.write and not err) else 0` matches spec:118 and :403. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit. |
| Options | Fix RTL at rtl/m_tlul_if.sv:106. No test change. |

## 8. Assertion CHK-010 (SVA a_CHK_010) — 7 fails / 379 hits, first fail 1895000 ps

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Contract.json:535: "o_apb_prdata = i_tlul_d_data(E) when exp_get=1 and err=0, else 32'h0" where err covers d_error, opcode mismatch and source mismatch. Spec:403: w_resp_rdata = (reg_a_rd and not w_resp_err) ? i_tlul_d_data : 32'h0. Spec:118 REQ-FUNC-006, spec:410 OP-004. |
| RTL does | rtl/m_tlul_if.sv:106 `o_resp_rdata = reg_a_rd ? i_tlul_d_data : '0` lacks the `~w_resp_err` term. On a counted read response with err=1, rtl/m_apb_if.sv:115-118 loads non-zero d_data into reg_prdata. PREADY and PSLVERR are correct (the pslverr part of the property holds); only the prdata clause fails. |
| Test does | verif/sva/nnc_chk_cross.sv:65-73 builds w_counted, w_exp_get and w_err from ports exactly per the contract. :129-133 asserts `w_counted |=> o_apb_pready && o_apb_pslverr==$past(w_err) && o_apb_prdata == (($past(w_exp_get) && !$past(w_err)) ? $past(i_tlul_d_data) : 32'h0)`. The 7 fails match the 7 failing tests, one per test since each cocotb test stops at its first error. The first fail at 1895000 ps lines up with test_chk_019 failing at 1900 ns. |
| A_rtl_wrong | For: The SVA implements the contract text faithfully. 372 of 379 hits pass (all error-free and write cases). The failing cases are exactly read+error responses, which is what the missing term at m_tlul_if.sv:106 predicts.<br>Against: None found. |
| B_test_wrong | For: None. The checker's state machine (pending/exp_get) agrees with the RTL on every other hit.<br>Against: The checker formula is a direct transcription of contract.json:535 and spec:403. |
| C_spec_unclear | For: None.<br>Against: The spec is explicit and was confirmed by the designer (DEC-008/DEC-009, spec:703-704). |
| Options | Fix RTL: rtl/m_tlul_if.sv:106 → `(reg_a_rd & ~w_resp_err) ? i_tlul_d_data : '0`. Do not change the assertion. |

## 9. Assertion CHK-005 (SVA a_CHK_005) — 7 fails / 316 hits, first fail 1895000 ps

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Contract.json:415: "if o_apb_pready=1 and (i_apb_pwrite=1 or o_apb_pslverr=1), then o_apb_prdata=32'h0". Rules BR-3-10 (rules.json:750, REQ-FUNC-006), BR-9-10 (rules.json:3486: "Forced to 0 for writes and for every error completion"), BR-5.1-03 (rules.json:1646: w_resp_rdata "already forced to 0 for writes and for errors"). Spec:704 DEC-009. |
| RTL does | On read completions with a TL-UL error, o_apb_pslverr=1 (rtl/m_apb_if.sv:117 from w_resp_err) while o_apb_prdata=d_data (rtl/m_tlul_if.sv:106 → m_apb_if.sv:118). The PREADY cycle therefore has pslverr=1 with non-zero prdata. Local errors are fine because m_apb_if.sv:114 clears prdata, and writes are fine because reg_a_rd=0. |
| Test does | verif/sva/nnc_chk_apb.sv:83 asserts `(o_apb_pready && (i_apb_pwrite || o_apb_pslverr)) |-> (o_apb_prdata == 32'h0)`, a direct transcription of the contract. The 7 fails match the CHK-010 fails in time (first at 1895000 ps), which shows the same events. The cocotb monitor has the same check at test_apb_tlul_bridge.py:255-258, but it runs after the CHK-010 check in the same edge, so CHK-010 is reported first. |
| A_rtl_wrong | For: The fails coincide exactly with the CHK-010 fails. The PRDATA=0-on-error rule is stated in four separate spec places (lines 118, 179, 403, 472). The missing gate at m_tlul_if.sv:106 explains it. The RTL comment at m_apb_if.sv:104-105 assumes the gating exists upstream.<br>Against: None found. |
| B_test_wrong | For: The checker relies on i_apb_pwrite being held through PREADY (contract.json:1024 BR-6.3-02 stimulus constraint), but that is not related to these fails, which have pslverr=1.<br>Against: The failing condition is the pslverr=1 branch, which does not depend on the pwrite assumption. The checker is a direct copy of the contract text. |
| C_spec_unclear | For: spec:235 "holds its last value otherwise" could be misread as allowing stale data.<br>Against: rules.json:7733 clarifies that 'holds' applies only when PREADY is not asserted and that PRDATA is 0 for every error completion. |
| Options | Fix RTL at rtl/m_tlul_if.sv:106 (add `& ~w_resp_err`). This closes both CHK-005 and CHK-010. Do not change the assertion. Optionally add an explicit spec cross-reference from the m_apb_if comment (m_apb_if.sv:104-105) to spec:403 so the upstream-zeroing assumption is documented. |


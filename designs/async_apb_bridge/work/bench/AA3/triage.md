# Failure triage

Failures: 26; analysed: 12. The designer decides; nothing was changed.

## 1. test_chk_019_apb5_user_signals [apb5.s1, user.s1]: CHK-033/031 o_apb_pslverr in PREADY cycle expected 0x1, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec/AsyncAPBBridge_Design_Specification.md:130 REQ-FUNC-002 "The bridge shall return on the requester-side interface the response of the completer-side transfer unchanged: PRDATA of a read, PSLVERR, ..."; :134 REQ-FUNC-006 "PSLVERR on the requester-side interface shall be high only in the PREADY cycle, and only when the completer-side PSLVERR was high at the end of the completer-side transfer" (rules.json:678-683, AB2-3-11); :247 o_apb_pslverr "Loaded with o_apb_pready, cleared at the next edge"; :531 ERR-001 "Forwarded: o_apb_pslverr high in the o_apb_pready cycle". contract.json:985-987 CHK-033: "In each requester PREADY cycle, o_apb_pslverr equals i_apb_pslverr sampled at C". |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:244 `assign o_apb_pslverr = 1'b0;` — the output is tied to constant 0. The slv side does pack PSLVERR (m_vlsit_apbcdc_slv.sv:144 `w_resp_payload[PARA_APBCDC_DATA_W] = i_apb_pslverr`), and the mst loads it into reg_resp_payload[DATA_W] at the PREADY edge (mst.sv:233-234) and clears it in RESP (mst.sv:235-236), but that bit is never connected to the port. Comment at mst.sv:240-241 says outputs are "sliced from the response output registers ... PRDATA, PSLVERR, ...", so the tie-off disagrees with the block's own comment. So in the PREADY cycle o_apb_pslverr=0 whatever the completer drove. |
| Test does | The CHK-019 policy (test_async_apb_bridge.py:787-794) sets pslverr=r.randint(0,1), so about half the transfers complete with i_apb_pslverr=1. The Completer drives it with pready=1 (:694-696). At completion edge C the response is captured into rec.resp (:558-562). Requester._complete (:459-461) compares out['pslverr'] with exp_resp (:256) `pslverr = rs['pslverr'] & 1`, which is the value sampled at C. So expected=1, observed=0. |
| A_rtl_wrong | For: mst.sv:244 hard-wires o_apb_pslverr to 0 even though the response register holds the PSLVERR bit (mst.sv:233-236) and the slv packs it (slv.sv:144). This contradicts REQ-FUNC-002/006 (spec:130,134), the port table (spec:247) and ERR-001 (spec:531). Every config and every test where the completer drives pslverr=1 fails in the same way; test_chk_031, whose policy uses err_p=0.0 (:1147), passes in apb4.s1.log:582.<br>Against: None found. The assignment cannot be justified as a configuration option: the spec says PSLVERR is 'always present' (spec:123). |
| B_test_wrong | For: The test expectation is derived from the completer value sampled at C (:558-562, :256), which matches the spec. No test issue found.<br>Against: The expected value follows CHK-033's 'o_apb_pslverr equals i_apb_pslverr sampled at C' (contract.json:987) exactly. The sampling of the completer inputs at C is correct, because prdata in the same transfer is checked against the same snapshot and does not fail. |
| C_spec_unclear | For: None — the spec is consistent across REQ-FUNC-002, REQ-FUNC-006, the port table, ERR-001 and OP-004 (spec:424).<br>Against: Several clauses state without ambiguity that PSLVERR is forwarded with PREADY. |
| Options | Fix RTL: in rtl/m_vlsit_apbcdc_mst.sv:244 replace `assign o_apb_pslverr = 1'b0;` with `assign o_apb_pslverr = reg_resp_payload[PARA_APBCDC_DATA_W];`. The existing clear in RESP (mst.sv:235-236) then gives the one-cycle PSLVERR required by CHK-004/005. No test change and no spec change are needed. |

## 2. test_chk_020_apb5_wakeup [apb5.s1, user.s1]: CHK-033/031 o_apb_pslverr in PREADY cycle expected 0x1, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Same as the first failure: spec:130 REQ-FUNC-002 (PSLVERR returned unchanged), spec:134 REQ-FUNC-006 (high in the PREADY cycle when the completer-side PSLVERR was high at the end of the transfer), spec:247, spec:531; contract.json:716 CHK-020 expected "Fields and responses are correct in all phases." |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:244 ties o_apb_pslverr to 1'b0. The captured bit reg_resp_payload[DATA_W] (mst.sv:233-236) is unused. |
| Test does | Phases (b) and (d) use make_policy(b,r,0,4,0.2) and make_policy(b,r,1,4,0.2) (:837, :858). make_policy draws pslverr=1 with p=0.2 (:169). The expected value comes from the response sampled at C (:562) through exp_resp (:256), and the comparison is at :459-461. |
| A_rtl_wrong | For: Same constant-0 assignment at mst.sv:244. The failure message is identical to all other failures in the list, and the test does nothing wake-up-specific when it fails (the failure is in _complete).<br>Against: None. |
| B_test_wrong | For: None found.<br>Against: The expected value follows CHK-033/CHK-031 exactly. The wake-up checks themselves did not fire. |
| C_spec_unclear | For: None.<br>Against: The spec is unambiguous (spec:130,134,247,531). |
| Options | Fix RTL at mst.sv:244: `assign o_apb_pslverr = reg_resp_payload[PARA_APBCDC_DATA_W];`. Then re-run CHK-020 so that the wake-up sub-checks (a)-(e), which are now masked by this failure, get exercised. |

## 3. test_chk_021_apb4_ignores_apb5 [apb4.s1-s3, model_off, syn, 4ph, 4ph_off, sync3, sync4, min, slv_fast, slv_slow]: CHK-033/031 o_apb_pslverr expected 0x1, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:130, :134, :247 as above. contract.json:731 CHK-021 expected "The scoreboard for all APB4 fields and responses passes as in CHK-029"; contract.json:899 CHK-029 "The values of PREADY n (o_apb_prdata for a read, o_apb_pslverr) equal the completer inputs sampled at the completion edge". |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:244 `assign o_apb_pslverr = 1'b0;` in every configuration (APB4 included). PSLVERR is not an APB5-only signal (spec:123 'PSLVERR ... always present'). |
| Test does | make_policy(b,r,0,4,0.2) (:878) gives pslverr=1 on about 20% of transfers (:169). The expected value is rs['pslverr'] sampled at C (:256, :562), and the check is at :460. |
| A_rtl_wrong | For: Constant-0 tie-off at mst.sv:244. It fails in all 12 APB4 elaborations, including HS_TYPE=1 and CELL_TYPE 3/4, so it does not depend on the handshake or synchronizer.<br>Against: None. |
| B_test_wrong | For: None. One could ask whether 'ignores APB5' affects PSLVERR, but PSLVERR is an APB4 signal.<br>Against: PSLVERR is listed as an APB4 signal (spec:58, :123). The exp_resp in the test does not gate pslverr by apb5 (:256), which is correct. |
| C_spec_unclear | For: None.<br>Against: spec:123 explicitly says PSLVERR is always present. |
| Options | Fix RTL at mst.sv:244 to drive reg_resp_payload[PARA_APBCDC_DATA_W]. No test or spec change. |

## 4. test_chk_022_cfg_min [all 14 runs]: CHK-033/031 o_apb_pslverr expected 0x1, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec:130, :134, :247. contract.json:747 CHK-022 stimulus includes "random wait states and errors"; :748 expected "The CHK-029 scoreboard passes." |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:244 constant 0. With DATA_W=8 the PSLVERR bit is reg_resp_payload[8], which is loaded (mst.sv:234) but never output. |
| Test does | The policy at :899-904 sets pslverr=1 with p=0.3. The expected value comes from the C sample (:256, :562), and the check is at :460. |
| A_rtl_wrong | For: mst.sv:244 tie-off. It fails in every run, including min.s1 (ADDR_W=1/DATA_W=8), so the bug does not depend on width.<br>Against: None. |
| B_test_wrong | For: None found.<br>Against: The stimulus deliberately includes errors per contract.json:747, and the expectation matches CHK-029/033. |
| C_spec_unclear | For: None.<br>Against: The spec is clear. |
| Options | Fix RTL at mst.sv:244 (`assign o_apb_pslverr = reg_resp_payload[PARA_APBCDC_DATA_W];`). Re-run min.s1 to confirm the bit-for-bit transport at DATA_W=8. |

## 5. test_chk_023_four_phase/periods=0 [4ph.s1, 4ph_off.s1]: CHK-033/031 o_apb_pslverr expected 0x1, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:772 CHK-023 expected "All field, response and count checks of CHK-031, CHK-033 and CHK-034 pass." spec:134 REQ-FUNC-006, spec:247, spec:406 ENUM_ST_RESP "At the exit edge: o_apb_pready and o_apb_pslverr cleared". |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:244 constant 0. In four-phase mode the response is loaded on leaving CLOSE (mst.sv:184-186, 233-234), but PSLVERR still never reaches the port. |
| Test does | With periods (10,20) and make_policy(b,r,0,5,0.3) (:932), pslverr=1 with p=0.3. The j-window check for hs=1 (:457-458) passed. The failure is in the response comparison at :459-461 against the C-sampled value (:256). |
| A_rtl_wrong | For: mst.sv:244 tie-off. The four-phase timing check (j>=2N+2) at :457 passed before the failing line 460, so the handshake works and only the PSLVERR output is wrong.<br>Against: None. |
| B_test_wrong | For: None.<br>Against: CHK-023 explicitly requires the CHK-033 response checks. |
| C_spec_unclear | For: None.<br>Against: Clear. |
| Options | Fix RTL at mst.sv:244. No change to test or spec. |

## 6. test_chk_023_four_phase/periods=1 [4ph.s1, 4ph_off.s1]: CHK-033/031 o_apb_pslverr expected 0x1, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Same as periods=0: contract.json:772 (CHK-033 response checks must pass under four-phase), spec:134, spec:247. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:244 `assign o_apb_pslverr = 1'b0;`. |
| Test does | With periods (20,10) (:924), the policy is the same as for periods=0 (:932, err_p=0.3). The expected value is the C sample (:562, :256), and the check is at :460. |
| A_rtl_wrong | For: The tie-off is the same. Changing the clock ratio does not change the symptom.<br>Against: None. |
| B_test_wrong | For: None.<br>Against: The expectation is spec-derived. |
| C_spec_unclear | For: None.<br>Against: Clear. |
| Options | Fix RTL at mst.sv:244. |

## 7. test_chk_024_requester_violations [all 14 runs]: CHK-033/031 o_apb_pslverr expected 0x1, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:791 CHK-024 expected "(b) and (c) complete with one PREADY each, with correct response. (d) The scoreboard passes". spec:134, spec:247. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:244 constant 0. |
| Test does | Part (a) passed (assertions at :955-958 come before the traffic). Parts (b)-(d) use make_policy(b,r,0,3,0.3) (:959), so pslverr=1 with p=0.3. The response check at :460 fails against the C-sampled value. |
| A_rtl_wrong | For: mst.sv:244 tie-off. The failure is in the response check, not in field transport, so the handling of illegal requester changes is not the cause.<br>Against: None. |
| B_test_wrong | For: None.<br>Against: The 'correct response' requirement in contract.json:791 includes PSLVERR. |
| C_spec_unclear | For: None.<br>Against: Clear. |
| Options | Fix RTL at mst.sv:244. Re-run to exercise the remaining (b)/(c) field checks fully. |

## 8. test_chk_025_two_phase_duration/periods=0 (10,10) [12 two-phase runs]: CHK-033/031 o_apb_pslverr expected 0x1, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | CHK-025 is a duration check (contract.json:805-807). It uses the common scoreboard, so spec:134 REQ-FUNC-006 and spec:247 also apply. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:244 constant 0. |
| Test does | _latency_sweep uses make_policy(b,r,0,8,0.2) (:974), so pslverr=1 with p=0.2. Every PREADY goes through Requester._complete (:494), which checks the response (:459-461) before the duration bound is ever evaluated (:980-991). |
| A_rtl_wrong | For: mst.sv:244 tie-off. The duration check is never reached; the failure is in the shared response check.<br>Against: None. |
| B_test_wrong | For: One could argue a duration test need not inject errors. But the scoreboard check is a valid spec requirement, so this is not a test defect.<br>Against: The expected value is correct per spec:134. Dropping errors from the stimulus would weaken coverage, which is not allowed. |
| C_spec_unclear | For: None.<br>Against: Clear. |
| Options | Fix RTL at mst.sv:244. After the fix, the CHK-025 duration bound will actually be evaluated. |

## 9. test_chk_025_two_phase_duration/periods=1 (10,20) [12 two-phase runs]: CHK-033/031 o_apb_pslverr expected 0x1, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Same as periods=0: spec:134, spec:247, contract.json:987. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:244 constant 0. |
| Test does | _latency_sweep (:968-991) with err_p=0.2 (:974). The response check is at :460. |
| A_rtl_wrong | For: Same tie-off.<br>Against: None. |
| B_test_wrong | For: None.<br>Against: The expectation is derived from the spec. |
| C_spec_unclear | For: None.<br>Against: Clear. |
| Options | Fix RTL at mst.sv:244. |

## 10. test_chk_025_two_phase_duration/periods=2 (20,10) [12 two-phase runs]: CHK-033/031 o_apb_pslverr expected 0x1, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Same: spec:134, spec:247. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:244 constant 0. |
| Test does | _latency_sweep with err_p=0.2 (:974). The response check is at :460. |
| A_rtl_wrong | For: Same tie-off.<br>Against: None. |
| B_test_wrong | For: None.<br>Against: The expectation is spec-derived. |
| C_spec_unclear | For: None.<br>Against: Clear. |
| Options | Fix RTL at mst.sv:244. |

## 11. test_chk_025_two_phase_duration/periods=3 (10,90) [12 two-phase runs]: CHK-033/031 o_apb_pslverr expected 0x1, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Same: spec:134, spec:247. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:244 constant 0. |
| Test does | _latency_sweep with err_p=0.2 (:974). The response check is at :460. |
| A_rtl_wrong | For: Same tie-off.<br>Against: None. |
| B_test_wrong | For: None.<br>Against: The expectation is spec-derived. |
| C_spec_unclear | For: None.<br>Against: Clear. |
| Options | Fix RTL at mst.sv:244. |

## 12. test_chk_025_two_phase_duration/periods=4 (90,10) [12 two-phase runs]: CHK-033/031 o_apb_pslverr expected 0x1, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Same: spec:134, spec:247. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:244 constant 0. |
| Test does | _latency_sweep with err_p=0.2 (:974). The response check is at :460. |
| A_rtl_wrong | For: Same tie-off. All 12 failures share one root cause.<br>Against: None. |
| B_test_wrong | For: None.<br>Against: The expectation is spec-derived. |
| C_spec_unclear | For: None.<br>Against: Clear. |
| Options | Fix RTL at mst.sv:244 (`assign o_apb_pslverr = reg_resp_payload[PARA_APBCDC_DATA_W];`). Then re-run the whole regression: test_chk_029, test_chk_033 and test_regression_random also fail in apb4.s1.log (:561, :616, :684) and are likely caused by the same bug. |


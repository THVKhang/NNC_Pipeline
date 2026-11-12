# Failure triage

Failures: 21; analysed: 12. The designer decides; nothing was changed.

## 1. test_chk_019_apb5_user_signals [apb5.s1, user.s1]: CHK-031/029 o_apb_pready rises with no completer-side completion edge C

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec/AsyncAPBBridge_Design_Specification.md:404 (mst FSM table, ENUM_ST_WAIT): "Waits for the acknowledge event: two-phase, synchronized acknowledge equal to `reg_req`". :212: "The two-phase request and acknowledge bits are equal when no transfer is in flight". :204: "The acknowledge crosses through `u_sync_ack`. With the two-phase handshake the mst FSM sees the event, loads the response output registers from `reg_resp_hold`, and raises `PREADY`". rules.json AB2-3-07 (REQ-FUNC-004): "PREADY on the requester-side interface shall be low from the Setup phase until the response is available". contract.json:695 (CHK-019 expected): "In the requester PREADY cycle, o_apb_pbuser equals i_apb_pbuser sampled at C ... The windows are those of CHK-031"; contract.json:948 (CHK-031): PREADY "at the j-th rising edge of i_clk_mst after C, with j in [N+1, N+3]". |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:137: `assign w_ack_event = (PARA_APBCDC_HS_TYPE == 32'd0) ? (w_ack_s != reg_req) : w_ack_s;` — the comparison is inverted against its own comment at :135 ("the synchronized acknowledge equals the request bit again") and spec :404. In the failing cycles: idle has reg_req == w_ack_s (both equal, spec :212). At the Setup edge S0, w_launch (:180) toggles reg_req (:191-192, :213), FSM goes IDLE->WAIT (:162-163). In the very next mst cycle w_ack_s still holds the old ack value, so w_ack_s != reg_req is already TRUE → w_ack_event=1 → w_load_resp=1 (:184-185) → reg_pready<=1 (:215) and state->RESP (:166-167). PREADY therefore fires ~1 mst cycle after S0, before the slv block has even raised o_apb_psel, and reg_resp_payload is loaded with the stale reg_resp_hold of the previous transfer (:233-234). The slv-side event detector (rtl/m_vlsit_apbcdc_slv.sv:134, `w_req_s != reg_ack`) is correct per spec :412, so only the mst side is wrong. |
| Test does | verif/tests/test_async_apb_bridge.py:778-806: APB5 config, T_mst=10/T_slv=20, 300 transfers with wake='before', completer policy w=0..4 (:787-795). Requester drives Setup (:400-414), then penable=1 (:506-507). The completer agent records C at the slv rising edge where previous sample had psel=1,penable=1 and its driven pready=1 (:558-563). When the requester samples o_apb_pready=1 in ACCESS (:492-494), _complete asserts rec.c_t is not None (:447-448) — i.e. the expectation that PREADY follows C is derived directly from CHK-031/AB2-3-07. Failure at 303.40 ns (very early: first transfers) with c_t=None: PREADY arrived before any completer completion. |
| A_rtl_wrong | For: m_vlsit_apbcdc_mst.sv:137 uses `!=` while spec :404 and the RTL's own comment :135 say 'equal'. With `!=`, the event is true one cycle after every launch toggle (reg_req just toggled, ack not yet), giving PREADY with no C exactly as observed. All four-phase tests (test_chk_023, test_chk_026, results.json:182-219, :474-571) PASS with the same testbench — four-phase uses the `w_ack_s` branch of :137, which is unaffected. Every two-phase transfer test fails in every two-phase configuration (results.json: 021,022,024,025,027-035, regression).<br>Against: None found in the files; the slv side mirror (slv.sv:134) is coded per spec, isolating the defect to the mst comparator. |
| B_test_wrong | For: The error is raised by the testbench's own C bookkeeping (test_async_apb_bridge.py:558-563); a C-detection bug in the TB would produce the same message.<br>Against: The identical C-detection and _complete code passes in all four-phase runs (test_chk_023/026 pass). The C rule at :558-559 (prev psel=1,penable=1 and driven pready=1) matches the contract C definition (contract.json:947). In periods=4 of CHK-025 C was detected but j=1, also consistent with premature PREADY, not missing detection. |
| C_spec_unclear | For: Spec :141 (REQ-HS-001) only says 'toggles once per transfer' without stating the comparison polarity.<br>Against: Spec :404 states explicitly 'two-phase, synchronized acknowledge equal to `reg_req`', and :212 states the bits are equal when idle; there is no ambiguity. |
| Options | Fix RTL: in rtl/m_vlsit_apbcdc_mst.sv:137 change `(w_ack_s != reg_req)` to `(w_ack_s == reg_req)` so the two-phase acknowledge event fires only once the synchronized ack has caught up with the toggled request (spec :404, :212). No testbench change is indicated; rerun apb5.s1 and user.s1 (and all two-phase configs). Optionally add an SVA in mst (two-phase) that o_apb_pready=1 implies w_ack_s==reg_req, to catch regressions. No spec clarification needed. |

## 2. test_chk_020_apb5_wakeup [apb5.s1, user.s1]: CHK-031/029 o_apb_pready rises with no completer-side completion edge C

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec/AsyncAPBBridge_Design_Specification.md:404: WAIT "Waits for the acknowledge event: two-phase, synchronized acknowledge equal to `reg_req`"; :212 "two-phase request and acknowledge bits are equal when no transfer is in flight"; :204 PREADY raised only after the acknowledge crosses. rules.json AB2-3-07: PREADY "shall be low from the Setup phase until the response is available". contract.json:716 (CHK-020 expected) "(e) All transfers complete. Fields and responses are correct in all phases"; windows of CHK-031 (contract.json:948). |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:137 computes the two-phase event as `w_ack_s != reg_req`. After the Setup edge toggles reg_req (:180, :191-192), the next mst edge sees w_ack_s(old) != reg_req(new) → w_load_resp (:184-185) → reg_pready=1 (:215), state RESP. PREADY is raised ~1 mst cycle after S0 without any completer-side transfer having completed; the response registers are loaded from the stale reg_resp_hold (:233-234). |
| Test does | test_async_apb_bridge.py:814-866. Part (a) (:822-835) is idle-only wake-up (no transfers, so it cannot trigger this). Failure at 1025.67 ns falls in part (b) (:837-839): 50 transfers wake='before', policy w 0..4, T 10/20. The requester waits in ACCESS; on o_apb_pready=1 (:492-494) _complete asserts that C was recorded (:447-448). C is recorded by the completer agent at :558-563 per contract.json:947 definition. |
| A_rtl_wrong | For: Inverted comparator at mst.sv:137 vs spec :404 and RTL comment :135; produces PREADY before C on the first transfer of part (b). Four-phase runs (same TB) pass; all two-phase runs fail with the same message.<br>Against: None in the files. |
| B_test_wrong | For: The assertion is TB bookkeeping (c_t set only at :558-563); wake-up handling (wait_wakeup) could in principle delay the completer's pready.<br>Against: wait_wakeup is False in part (b) (set only at :862 for part (e)); same C detection passes in four-phase tests; the failure mode is identical to non-APB5 tests (021, 022, 025), so it is not wake-up specific. |
| C_spec_unclear | For: REQ-HS-001 (spec :141) does not state polarity.<br>Against: Spec :404 and :212 define the polarity explicitly. |
| Options | Fix RTL: rtl/m_vlsit_apbcdc_mst.sv:137 → `(w_ack_s == reg_req)` for HS_TYPE=0. No test change; rerun apb5.s1/user.s1 to verify parts (b)-(e) of CHK-020 now progress. Spec needs no change. |

## 3. test_chk_021_apb4_ignores_apb5 [apb4.s1-s3, model_off, syn, sync3, sync4, min, slv_fast, slv_slow]: CHK-031/029 o_apb_pready rises with no C

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :404 (two-phase ack event = synchronized ack equal to reg_req); :212; :204. rules.json AB2-3-07 (REQ-FUNC-004) PREADY low from Setup until the response is available. contract.json:731 (CHK-021 expected): "The scoreboard for all APB4 fields and responses passes as in CHK-029"; CHK-029 expected (contract.json:899): "The values of PREADY n ... equal the completer inputs sampled at the completion edge of transfer n". |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:137 `w_ack_event = ... (w_ack_s != reg_req)`. Right after a launch (reg_req toggled at S0, :191-192/:213) the condition is already true, so at the next mst edge w_load_resp=1 (:184-185), reg_pready<=1 (:215) and RESP is entered, before the request has crossed to the slv domain. This is independent of APB5 settings: the random i_apb_pwakeup in this test only feeds reg_wakeup (:214), which is forced to 0 in APB4. |
| Test does | test_async_apb_bridge.py:870-889: APB4, default clocks, wake_random=True (:877), policy w 0..4, err 0.2 (:878), 200 random transfers (:879). Requester checks on PREADY that rec.c_t exists (:445-448); C is the slv edge with prev psel=1,penable=1 and driven pready=1 (:558-563). Failure at 829.96 ns (first transfer(s)). |
| A_rtl_wrong | For: mst.sv:137 polarity contradicts spec :404 and the RTL comment :135; explains PREADY within ~1 mst cycle of S0 in every two-phase config listed (apb4, syn, sync3/4, min, slv_fast/slow, model_off). Four-phase tests pass in the same TB.<br>Against: None in the files. |
| B_test_wrong | For: wake_random toggles i_apb_pwakeup each cycle (:333-334), which is unusual stimulus; message comes from TB bookkeeping.<br>Against: pwakeup has no path to PREADY in RTL (mst.sv:214 only, masked by APB5=0). Tests without random wake-up (022, 025, 027) fail identically, so the stimulus is not the cause. |
| C_spec_unclear | For: None specific.<br>Against: Spec :404 is explicit about 'equal'. |
| Options | Fix RTL: change mst.sv:137 to `(w_ack_s == reg_req)` in the two-phase branch. No test change; rerun all two-phase configurations. No spec change. |

## 4. test_chk_022_cfg_min [all 12 two-phase configs incl. apb5, user, min]: CHK-031/029 o_apb_pready rises with no C

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :404 (two-phase ack event when synchronized ack equals reg_req), :212, :204; rules.json AB2-3-07. contract.json:748 (CHK-022 expected): "The CHK-029 scoreboard passes. o_apb_paddr, o_apb_pstrb, o_apb_pwdata and o_apb_prdata equal the corresponding requester and completer values bit for bit"; contract.json:948 PREADY at j in [N+1,N+3] after C. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:137 evaluates `w_ack_s != reg_req`; this is true immediately after the launch toggle (:191-192), so PREADY (:215) and the response load from stale reg_resp_hold (:233-234) happen one mst cycle after S0, with no completer transfer completed. Width parameters are irrelevant to this path. |
| Test does | test_async_apb_bridge.py:893-920: T 10/20, 500 transfers alternating write/read, corner paddr/pwdata values, policy w 0..3, pslverr 30% (:899-905). On PREADY, _complete (:445-448) requires the C edge recorded by :558-563. Failure at 1127.97 ns (first transfer). |
| A_rtl_wrong | For: Same inverted comparator at mst.sv:137 vs spec :404/:212 and comment :135. Fails uniformly across every two-phase config including min widths; four-phase tests pass with same TB code.<br>Against: None in the files. |
| B_test_wrong | For: Message originates in TB bookkeeping.<br>Against: C detection (:558-563) matches contract definition (contract.json:947) and works in four-phase runs. |
| C_spec_unclear | For: None.<br>Against: Spec :404 explicit. |
| Options | Fix RTL at mst.sv:137 (`!=` → `==` for HS_TYPE=0). No test or spec change. Rerun min.s1 to confirm CFG-MIN bit-for-bit transport after the fix. |

## 5. test_chk_024_requester_violations [all 12 two-phase configs]: CHK-031/029 o_apb_pready rises with no C

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :404, :212, :204 (two-phase acknowledge event = synchronized ack equal to reg_req). rules.json AB2-3-07. contract.json:791 (CHK-024 expected): "(b) and (c) complete with one PREADY each, with correct response. (d) The scoreboard passes". |
| RTL does | Part (a) (PENABLE without Setup) is correctly ignored: w_setup = psel & ~penable (mst.sv:133) is 0, so no launch. Failure is at 2529.28 ns, i.e. in part (b) when the first legal Setup arrives: launch toggles reg_req (:191-192), and at the next mst edge mst.sv:137 `w_ack_s != reg_req` is already true → reg_pready=1 (:215) before the slv side completes. |
| Test does | test_async_apb_bridge.py:945-965: (a) raw psel=1/penable=1 for 20 cycles then idle (:952-958) — these asserts passed; (b) 50 transfers with ill='chg' scrambling fields during Access (:960, :497-498, :508-509), (c) rep=1 extended Setup, (d) 50 legal. On PREADY, _complete requires c_t (:447-448). |
| A_rtl_wrong | For: Part (a) assertions at :955-958 passed (failure time is after them), so the failure is on the first legal transfer — exactly where mst.sv:137 inverted comparator raises PREADY immediately. Same signature as all other two-phase tests; four-phase passes.<br>Against: None in the files. |
| B_test_wrong | For: ill='chg' scrambles fields during Access, unusual stimulus.<br>Against: Field scrambling does not touch psel/penable and has no path to PREADY; non-violating tests (022, 025) fail identically. |
| C_spec_unclear | For: None.<br>Against: Spec :404 explicit. |
| Options | Fix RTL at mst.sv:137 (`w_ack_s == reg_req` for two-phase). No test or spec change; rerun to confirm parts (b)-(d). |

## 6. test_chk_025_two_phase_duration/periods=0 (10:10) [all 12 configs]: CHK-031/029 o_apb_pready rises with no C

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :404, :212, :204; rules.json AB2-3-07. contract.json:805 (CHK-025): D measured from the first Setup cycle to the end of the requester PREADY cycle; the PREADY must be the one for that transfer (CHK-031 window, contract.json:948). |
| RTL does | mst.sv:137 `(w_ack_s != reg_req)` true one cycle after launch toggle (:191-192) → reg_pready (:215) asserted before the request has even crossed (u_sync_req N=2 stages in slv.sv:263-272). |
| Test does | test_async_apb_bridge.py:999-1002 → _latency_sweep :968-995: equal 10 ns clocks, policy w 0..8, 200 transfers. The duration bound check (:980-991) is never reached; the run aborts at _complete :447-448 because PREADY arrives with c_t=None (C recorded at :558-563). |
| A_rtl_wrong | For: Inverted comparator at mst.sv:137 vs spec :404 and comment :135; four-phase duration sweep (test_chk_026, same _latency_sweep code) passes in all 5 periods.<br>Against: None in the files. |
| B_test_wrong | For: Equal clocks with phase alignment could in principle confuse edge ordering in the TB.<br>Against: The same failure occurs at 10:20, 20:10, 10:90; four-phase equal-clock run passes with identical TB. |
| C_spec_unclear | For: None.<br>Against: Spec :404 explicit. |
| Options | Fix RTL at mst.sv:137. No test change. After the fix rerun CHK-025 to actually exercise the duration bound (spec :154 REQ-PERF-001). |

## 7. test_chk_025_two_phase_duration/periods=1 (10:20) [all 12 configs]: CHK-031/029 o_apb_pready rises with no C

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :404, :212, :204; rules.json AB2-3-07; contract.json:805-807 (CHK-025) and :948 (CHK-031 window). |
| RTL does | mst.sv:137 inverted two-phase event: one mst cycle after S0 the toggled reg_req differs from the old w_ack_s, w_load_resp=1 (:184-185), reg_pready=1 (:215). With T_slv=20 the slv side cannot even raise psel (needs N+1..N+3 slv edges) before this PREADY. |
| Test does | _latency_sweep (test_async_apb_bridge.py:968-995) with periods (10,20), w 0..8, 200 transfers; aborts at _complete :447-448 (c_t None). |
| A_rtl_wrong | For: Same as other two-phase failures; spec :404 vs RTL :137. Four-phase counterpart passes.<br>Against: None in the files. |
| B_test_wrong | For: Assertion originates in TB bookkeeping.<br>Against: Same TB passes in four-phase; C definition matches contract.json:947. |
| C_spec_unclear | For: None.<br>Against: Spec :404 explicit. |
| Options | Fix RTL at mst.sv:137 (`==`). No test/spec change. |

## 8. test_chk_025_two_phase_duration/periods=2 (20:10) [all 12 configs]: CHK-031/029 o_apb_pready rises with no C

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :404, :212, :204; rules.json AB2-3-07; contract.json:805-807, :948. |
| RTL does | mst.sv:137 `w_ack_s != reg_req` → PREADY one mst cycle (20 ns) after S0 (:215). With T_slv=10 and N=2 the slv side needs at least 3 slv edges (30 ns) to raise psel, plus Setup/Access, so C is still absent when PREADY is sampled. |
| Test does | _latency_sweep (:968-995) with periods (20,10); aborts at :447-448. |
| A_rtl_wrong | For: Inverted comparator vs spec :404; four-phase counterpart passes.<br>Against: None in the files. |
| B_test_wrong | For: TB-generated message.<br>Against: Identical TB passes four-phase. |
| C_spec_unclear | For: None.<br>Against: Spec :404 explicit. |
| Options | Fix RTL at mst.sv:137. No test/spec change. |

## 9. test_chk_025_two_phase_duration/periods=3 (10:90) [all 12 configs]: CHK-031/029 o_apb_pready rises with no C

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :404, :212, :204; rules.json AB2-3-07; contract.json:805-807, :948. |
| RTL does | mst.sv:137 inverted event → PREADY ~10 ns after S0 (:215), while the slv side (T_slv=90 ns) needs hundreds of ns to complete; reg_resp_payload loaded with stale reg_resp_hold (:233-234). |
| Test does | _latency_sweep (:968-995) with periods (10,90); aborts at :447-448. |
| A_rtl_wrong | For: Inverted comparator vs spec :404/comment :135; four-phase 10:90 run passes.<br>Against: None in the files. |
| B_test_wrong | For: TB-generated message.<br>Against: Same TB passes four-phase. |
| C_spec_unclear | For: None.<br>Against: Spec :404 explicit. |
| Options | Fix RTL at mst.sv:137. No test/spec change. |

## 10. test_chk_025_two_phase_duration/periods=4 (90:10) [all 12 configs]: CHK-031/032 o_apb_pready at j-th i_clk_mst edge after C, expected j in [3,5], got j=1

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | contract.json:948 (CHK-031): "o_apb_pready=0 at every i_clk_mst edge from S0 until it becomes 1 at the j-th rising edge of i_clk_mst after C, with j in [N+1, N+3]"; contract.json:967 (CHK-032) same window. spec :404: two-phase event when "synchronized acknowledge equal to `reg_req`"; the ack must pass through the N-stage u_sync_ack (spec :331 CDC-003), so j >= N+1 = 3. |
| RTL does | mst.sv:137 `(w_ack_s != reg_req)`: the event is true at the first mst edge after S0 (reg_req just toggled, ack synchronizer still old). Because T_slv=10 ns is 9x faster than T_mst=90 ns, the slv side finishes request sync, Setup, Access and C within that one 90 ns mst period, so the TB did record C — but PREADY was raised by the premature (false) event at the first mst edge after C (j=1), not by the synchronized acknowledge (which needs N=2 mst edges through u_sync_ack, mst.sv:268-277). |
| Test does | _latency_sweep (test_async_apb_bridge.py:968-995) with periods (90,10). _complete computes j = idx - bisect_right(m_edges, c_t) + 1 (:449) and asserts N+1 <= j <= N+3 for hs=0 (:453-455), from contract.json:948. |
| A_rtl_wrong | For: j=1 is physically impossible through a 2-stage synchronizer; only explained by an event not derived from the synchronized ack, i.e. the inverted comparator at mst.sv:137. Same root cause as the 'no C' variants at other ratios (C just happens to complete first at 90:10). Four-phase 90:10 run passes.<br>Against: None in the files. |
| B_test_wrong | For: j counting is edge-list based (:449); off-by-one in counting at extreme ratios is conceivable.<br>Against: An off-by-one would give j=2..4, not j=1 vs a minimum of 3; the same j formula passes in four-phase (j>=2N+2 checked at :457) and in the original window checks. |
| C_spec_unclear | For: None.<br>Against: contract.json:948 and spec :404 explicit. |
| Options | Fix RTL at mst.sv:137 (`w_ack_s == reg_req` for HS_TYPE=0); after the fix j will be >= N+1 because the event then depends on the N-stage synchronized ack. No test/spec change. |

## 11. test_chk_027_reset_values [all 12 configs]: CHK-031/029 o_apb_pready rises with no C

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :404, :212 ("two-phase request and acknowledge bits are equal when no transfer is in flight"), :204; rules.json AB2-3-07. contract.json:845 (CHK-027 expected): "The transfers after each release complete with correct fields and response, as in CHK-031". |
| RTL does | Reset and idle parts behave correctly (reg_req and sync stages reset to 0, mst.sv:208-211, :267-277). On the first transfer after release, the launch toggles reg_req 0→1 (:191-192) while w_ack_s=0; mst.sv:137 `w_ack_s != reg_req` is then true, so PREADY (:215) is raised ~1 mst cycle after S0, before C. |
| Test does | test_async_apb_bridge.py:1013-1059: reset, release mst_first, quiet_idle 100 slv cycles (:1029-1030; these passed — the failure is at 11550.92 ns, after ~1000+ ns of quiet idle), then a read and a write with w 0..2 (:1032-1044). _complete asserts c_t is set (:447-448). |
| A_rtl_wrong | For: Reset values and quiet-idle checks passed; failure only on the first transfer after release, matching mst.sv:137 inverted event. Spec :212 says the bits are equal when idle, so the event must be 'equal again', not 'different'.<br>Against: None in the files. |
| B_test_wrong | For: The test re-builds Bench after holding reset and noisy completer during idle (:766-773) could leave stale state.<br>Against: noisy is cleared before transfers (:773); the same failure signature appears in tests without resets (022, 025); four-phase reset behaviour is not exercised here but four-phase transfer tests pass with same agents. |
| C_spec_unclear | For: None.<br>Against: Spec :404 explicit. |
| Options | Fix RTL at mst.sv:137. No test/spec change; rerun to confirm the post-reset transfer pair and the asynchronous reset assertion part (only reached after the first pair completes). |

## 12. test_chk_028_reset_during_traffic [all 12 configs]: CHK-031/029 o_apb_pready rises with no C

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec :404, :212, :204; rules.json AB2-3-07. contract.json:864 (CHK-028 expected): "The interrupted transfer never produces o_apb_pready. Each repeated transfer and all later traffic pass the CHK-029 scoreboard". |
| RTL does | mst.sv:137 `(w_ack_s != reg_req)` makes the two-phase ack event true right after every launch toggle; PREADY (:215) is raised before the completer completes, with stale response data (:233-234). This occurs on normal traffic, before or between the reset injections. |
| Test does | test_async_apb_bridge.py:1063-1106: default config, noisy completer, policy w 0..6; loop waits for phases (req_setup, req_cross, ...) (:1072-1097) and injects resets. A transfer reaching ACCESS with PREADY but no recorded C triggers :447-448. Failure at 12240.84 ns. |
| A_rtl_wrong | For: Same inverted comparator signature as all other two-phase failures; reset handling is not required to explain it. Four-phase variants pass.<br>Against: None in the files. |
| B_test_wrong | For: Reset epochs/_lose() bookkeeping (:365-373, :468-473) could leave a stale rec without c_t after a reset.<br>Against: On reset the requester drops rec (_lose sets rec=None, state IDLE), so a post-reset PREADY would hit the idle check (:523-524), not _complete; the failure occurs in ACCESS with an active rec, matching premature PREADY. Tests without resets fail identically. |
| C_spec_unclear | For: None.<br>Against: Spec :404 explicit. |
| Options | Fix RTL at mst.sv:137 (`==` in the two-phase branch). No test/spec change; rerun to confirm the reset-in-flight scenarios, which are currently masked by this defect. |


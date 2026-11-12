# Failure triage

Failures: 28; analysed: 12. The designer decides; nothing was changed.

## 1. test_chk_019_apb5_user_signals [apb5.s1, user.s1]: CHK-035/031 o_apb_pprot at o_apb_psel rise expected 0x2, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | spec/AsyncAPBBridge_Design_Specification.md:137 REQ-FUNC-009: "`PPROT` and `PSTRB` shall be forwarded unchanged." (rules.json:876 AB2-3-18 / :903 AB2-3-19, "Applies to: All configurations"). Spec:201 "the mst block loads `reg_req_payload` with `PWRITE`, `PADDR`, `PPROT`, `PSTRB`, `PWDATA` ...". Spec:256 o_apb_pprot is "Loaded with the request". Spec:389 the bundle field order is "PADDR, PPROT, PWRITE, ...". rules.json:4258 AB2-9-05 says Protection is "Forwarded as received". contract.json:1020 CHK-035 says "PPROT and PSTRB are copied unchanged", and contract.json:1022 expects "o_apb_pprot ... equal the values sampled at S0". |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:142 `assign w_req_payload[PARA_APBCDC_ADDR_W +: LPARA_PROT_W] = '0;`. The PPROT slice of the request bundle is tied to zero, and i_apb_pprot (declared at mst.sv:81) is never read anywhere in the module. In the failing cycle, the launch edge (mst.sv:224-225) loads reg_req_payload with PPROT=0. The slv side loads that bundle into reg_apb_payload (slv.sv:218-219) and slices it at the right position (slv.sv:237 `o_apb_pprot = reg_apb_payload[PARA_APBCDC_ADDR_W +: LPARA_PROT_W]`). So o_apb_pprot is 0 at every o_apb_psel rise whatever value was driven. Every other field is packed from its input (mst.sv:141, 143-155). |
| Test does | rand_item (test_async_apb_bridge.py:158) draws pprot=r.randint(0,7). _start (:406-407) drives cur['pprot']=it['pprot'] on i_apb_pprot in the Setup cycle. Xfer stores f['pprot'] (:136). exp_fields (:241) expects "pprot": f["pprot"] & 7. _new (:606-607) compares it with o_apb_pprot sampled at the falling edge after the o_apb_psel rise. Here the item drew 0x2 and the DUT output was 0x0. |
| A_rtl_wrong | For: mst.sv:142 drives the PPROT field with the constant '0 instead of i_apb_pprot. i_apb_pprot has no reader in the RTL. The module header comment (mst.sv:139-140) and spec:201/:389 both say PPROT is packed from the Setup cycle. The other fields on the same line pattern use their inputs. The slv-side slice (slv.sv:237) is consistent with the spec field order, so the defect sits only in the mst pack. The same mismatch fails in every configuration and in the dedicated test_chk_035_pprot_pstrb (results.json:1060-1067, all runs fail).<br>Against: None found. No DEC entry or spec text allows PPROT to be dropped or zeroed. DEC-021 (mst.sv:15-17) covers only the APB5 user ports. |
| B_test_wrong | For: None of substance. The expected value is the value the test itself drove on i_apb_pprot at S0.<br>Against: The expectation (test:241) matches REQ-FUNC-009 and CHK-035 (contract.json:1020-1022). The driver puts it['pprot'] on i_apb_pprot in the Setup cycle (test:406-407), and the compare is made at the psel rise, where the spec (spec:256) says the field is valid. The failure is not a timing artefact: the RTL output can never be anything other than 0. |
| C_spec_unclear | For: DEC-028 (spec:871) is marked "Author's choice; to be confirmed by the designer".<br>Against: DEC-028 is only about forwarding a nonzero PSTRB on reads. PPROT forwarding is unconditional in REQ-FUNC-009 (spec:137), the scope table (spec:79), the port table (spec:239, :256), the bundle layout (spec:389) and AB2-9-05. DEC-004 (spec:847), confirmed by the designer, says PPROT is always present. |
| Options | Fix the RTL in rtl/m_vlsit_apbcdc_mst.sv:142 by changing it to `assign w_req_payload[PARA_APBCDC_ADDR_W +: LPARA_PROT_W] = i_apb_pprot;`. No slv change is needed (slv.sv:237 already slices the correct bits). Then rerun all configurations: this one fix should clear every CHK-035/031 pprot failure, including test_chk_031 and test_chk_035. No test change is needed, and the spec only needs changing if the designer actually wants PPROT dropped, which would contradict REQ-FUNC-009. |

## 2. test_chk_020_apb5_wakeup [apb5.s1, user.s1]: CHK-035/031 o_apb_pprot expected 0x5, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Same as the first failure. Spec:137 REQ-FUNC-009 says "`PPROT` and `PSTRB` shall be forwarded unchanged" (All configurations). Spec:201 says PPROT is loaded into reg_req_payload at Setup. Spec:256 says o_apb_pprot is "Loaded with the request". contract.json:1020-1022 CHK-035 expects o_apb_pprot to equal the value sampled at S0. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:142 ties the PPROT bundle bits to '0, so i_apb_pprot is unused. slv.sv:219 loads that bundle and slv.sv:237 drives o_apb_pprot from it, so o_apb_pprot is 0 at the psel rise of this wake-up test's transfer. |
| Test does | The wake-up scenario still drives a normal item from rand_item (test:158, pprot=randint(0,7), here 0x5) on i_apb_pprot at Setup (test:406-407). exp_fields (test:241) expects 0x5, and _new (test:606-607) checks it at the o_apb_psel rise. |
| A_rtl_wrong | For: mst.sv:142 constant '0 for PPROT. The output value is the same in every failing test, and the same defect also fails test_chk_035_pprot_pstrb in all runs (results.json:1060).<br>Against: None found. |
| B_test_wrong | For: None. The failure is not related to the wake-up stimulus: it is a field check.<br>Against: The expected value is what was driven at S0 (test:136, :241, :406-407), which agrees with CHK-035. |
| C_spec_unclear | For: None specific to PPROT.<br>Against: PPROT forwarding is stated without condition at spec:79, :137, :239, :256, :389 and rules.json:4258. |
| Options | Fix the RTL with the same one-line change: in mst.sv:142, replace '0 with i_apb_pprot. Then rerun apb5.s1 and user.s1. This test's wake-up checks (CHK-018/020) are only reached once the field check passes, so check for any remaining failures after the fix. |

## 3. test_chk_021_apb4_ignores_apb5 [all APB4 configs]: CHK-035/031 o_apb_pprot expected 0x4, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Spec:137 REQ-FUNC-009: "`PPROT` and `PSTRB` shall be forwarded unchanged" ("Applies to: All configurations"). Spec:123: "`PSTRB`, `PPROT`, `PSLVERR` always present". Spec:256 says o_apb_pprot is "Loaded with the request", and contract.json:1022 expects it to equal the S0 value. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:142 packs '0 into the PPROT bits. This does not depend on PARA_APBCDC_APB5, so APB4 builds are affected too. o_apb_pprot (slv.sv:237) is 0 at the psel rise. |
| Test does | The APB4 test drives random APB5 inputs (which should be ignored) together with normal items. pprot comes from rand_item (test:158), here 0x4, and is driven at Setup (test:406-407). exp_fields (test:241) expects 0x4 for pprot. The APB5 outputs are checked separately against 0 (test:637-639). The failure is on pprot, not on an APB5 signal. |
| A_rtl_wrong | For: mst.sv:142 tie-off to '0. The failure is on an APB4 base signal that the spec requires in every configuration.<br>Against: None found. |
| B_test_wrong | For: None. The test's APB5-ignore logic is not involved.<br>Against: The expectation is the driven S0 value (test:241), as CHK-035 requires. |
| C_spec_unclear | For: None.<br>Against: Spec:123 says PPROT is always present, and DEC-004 (spec:847), confirmed by the designer, says the same. |
| Options | Fix the RTL in mst.sv:142 (replace '0 with i_apb_pprot), then rerun all APB4 configs to confirm that the APB5-ignore checks pass behind the field check. |

## 4. test_chk_022_cfg_min [all 14 configs]: CHK-035/031 o_apb_pprot expected 0x1, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Spec:137 REQ-FUNC-009 (All configurations): PPROT forwarded unchanged. Spec:389 says the bundle field order is "PADDR, PPROT, PWRITE, ...", so PPROT sits at bit PARA_APBCDC_ADDR_W for every address width. contract.json:1020-1022 expects o_apb_pprot to equal the S0 value. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:142 sets bits [ADDR_W +: 3] to '0 for every ADDR_W/DATA_W. slv.sv:237 slices the same position, so o_apb_pprot is 0. The minimum-width corner (small ADDR_W/DATA_W) does not add a separate slicing error: paddr and pstrb at the same psel rise are not the reported mismatch. |
| Test does | Same flow at the minimum-width corner: rand_item pprot=randint(0,7), here 0x1 (test:158), driven at Setup (test:406-407). The expected value is f['pprot']&7 (test:241), checked at the psel rise (test:606-607). |
| A_rtl_wrong | For: mst.sv:142 constant zero. It fails in every config, including the default ones, so the failure is not specific to the width corner.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The test masks pprot with &7 (test:241), which matches the fixed width LPARA_PROT_W=3 (mst.sv:56). |
| C_spec_unclear | For: None.<br>Against: PPROT forwarding is unconditional (spec:137, rules.json:4258). |
| Options | Fix the RTL in mst.sv:142 (replace '0 with i_apb_pprot). After the fix, rerun to confirm that the minimum-width offsets (LPARA_OFF_WR etc., mst.sv:66-70) also pass for the other fields. |

## 5. test_chk_023_four_phase/periods=0 [4ph.s1, 4ph_off.s1]: CHK-035/031 o_apb_pprot expected 0x2, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Spec:137 REQ-FUNC-009: PPROT forwarded unchanged in all configurations. Spec:201: "the mst block loads `reg_req_payload` with ... `PPROT` ... with the four-phase handshake it rises". contract.json:1022 expects o_apb_pprot to equal the S0 value. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:142 ties PPROT to '0 regardless of PARA_APBCDC_HS_TYPE. The four-phase handshake moves the bundle correctly (mst.sv:224-225 → slv.sv:218-219), but the PPROT bits carry 0, so o_apb_pprot=0 (slv.sv:237). |
| Test does | Four-phase build: the item pprot (here 0x2, test:158) is driven at Setup (test:406-407). The expected value comes from exp_fields (test:241) and is checked at the psel rise (test:606-607). |
| A_rtl_wrong | For: mst.sv:142. The same mismatch appears in the two-phase configs, so the handshake type is not involved.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The expectation is derived from the stimulus and agrees with CHK-035. |
| C_spec_unclear | For: None.<br>Against: Spec:201 explicitly lists PPROT in the captured bundle for both handshakes. |
| Options | Fix the RTL in mst.sv:142 (replace '0 with i_apb_pprot), then rerun 4ph.s1 and 4ph_off.s1. |

## 6. test_chk_023_four_phase/periods=1 [4ph.s1, 4ph_off.s1]: CHK-035/031 o_apb_pprot expected 0x5, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Same as periods=0: spec:137 REQ-FUNC-009 and spec:201 (PPROT is captured in the bundle). contract.json:1020-1022 CHK-035. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:142 drives '0 into the PPROT bits, so o_apb_pprot (slv.sv:237) is 0 at the psel rise. |
| Test does | Same as periods=0 with a different clock-period pair. The item pprot is 0x5 (test:158), driven at Setup (test:406-407) and expected at the psel rise (test:241, :606-607). |
| A_rtl_wrong | For: mst.sv:142 constant zero. The failure does not depend on the clock periods.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The expected value is the driven S0 value. |
| C_spec_unclear | For: None.<br>Against: The PPROT requirement is unambiguous. |
| Options | Fix the RTL in mst.sv:142 (replace '0 with i_apb_pprot). |

## 7. test_chk_024_requester_violations [all 14 configs]: CHK-035/031 o_apb_pprot expected 0x3, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Spec:137 REQ-FUNC-009: PPROT forwarded unchanged. Spec:275-276 say the bridge captures PPROT in the Setup cycle and relies on stability "only for the Setup cycle of the requester side", so changes to the requester inputs after Setup must not matter. contract.json:1022 expects o_apb_pprot to equal the value sampled at S0. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:142 ties PPROT to '0, so o_apb_pprot=0 at the psel rise no matter what was driven at S0 or afterwards. The capture-once mechanism itself (mst.sv:224-225, w_launch only) is correct. |
| Test does | The test scrambles the requester inputs after Setup (_scramble, test:359-363, which includes pprot=randint(0,7)). The expected value is still rec.f['pprot'], taken from the item at _start (test:136, :406-407), here 0x3, and checked at the psel rise (test:241, :606-607). |
| A_rtl_wrong | For: mst.sv:142. The output is 0, which is neither the S0 value nor a scrambled value, so the failure is the tie-off, not a capture-timing problem.<br>Against: None found. |
| B_test_wrong | For: One could check whether the test samples the S0 value correctly when inputs are scrambled.<br>Against: Xfer.f is captured from the item driven in the Setup cycle (test:136, :406-407), before any scramble. A got value of exactly 0 in every config points to the RTL constant. |
| C_spec_unclear | For: None.<br>Against: Spec:275-276 clearly define capture at Setup. |
| Options | Fix the RTL in mst.sv:142 (replace '0 with i_apb_pprot). After the fix, rerun to confirm that the post-Setup scrambles of i_apb_pprot do not leak to o_apb_pprot (CHK-016/017/024). |

## 8. test_chk_025_two_phase_duration/periods=0 [two-phase configs]: CHK-035/031 o_apb_pprot expected 0x6, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Spec:137 REQ-FUNC-009: PPROT forwarded unchanged (All configurations). Spec:201 says PPROT is in reg_req_payload. contract.json:1020-1022 CHK-035. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:142 drives '0 into the PPROT bundle bits, so o_apb_pprot (slv.sv:237) is 0. |
| Test does | Two-phase duration test: the item pprot is 0x6 (test:158), driven at Setup (test:406-407). The expected value comes from exp_fields (test:241) and is checked at the psel rise (test:606-607). The run aborts on the field check before the duration checks. |
| A_rtl_wrong | For: mst.sv:142 constant zero. The failure is independent of the duration and clock periods.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The expected value is the driven S0 value. |
| C_spec_unclear | For: None.<br>Against: The PPROT requirement is unambiguous. |
| Options | Fix the RTL in mst.sv:142 (replace '0 with i_apb_pprot), then rerun so the duration checks are actually exercised. |

## 9. test_chk_025_two_phase_duration/periods=1 [two-phase configs]: CHK-035/031 o_apb_pprot expected 0x7, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Spec:137 REQ-FUNC-009 and spec:201. contract.json:1020-1022 CHK-035: o_apb_pprot equals the S0 value. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:142 sets PPROT to '0, so o_apb_pprot=0 (slv.sv:237). |
| Test does | The item pprot is 0x7 (test:158), driven at Setup (test:406-407) and expected at the psel rise (test:241, :606-607). |
| A_rtl_wrong | For: mst.sv:142 tie-off.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The expectation is derived from the stimulus, as CHK-035 requires. |
| C_spec_unclear | For: None.<br>Against: The requirement is explicit. |
| Options | Fix the RTL in mst.sv:142 (replace '0 with i_apb_pprot). |

## 10. test_chk_025_two_phase_duration/periods=2 [two-phase configs]: CHK-035/031 o_apb_pprot expected 0x7, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Spec:137 REQ-FUNC-009 and spec:201. contract.json:1020-1022 CHK-035. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:142 sets PPROT to '0, so o_apb_pprot=0 (slv.sv:237). |
| Test does | The item pprot is 0x7 (test:158), driven at Setup (test:406-407) and expected at the psel rise (test:241, :606-607). |
| A_rtl_wrong | For: mst.sv:142 tie-off.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The expected value is the driven S0 value. |
| C_spec_unclear | For: None.<br>Against: The requirement is explicit. |
| Options | Fix the RTL in mst.sv:142 (replace '0 with i_apb_pprot). |

## 11. test_chk_025_two_phase_duration/periods=3 [two-phase configs]: CHK-035/031 o_apb_pprot expected 0x7, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Spec:137 REQ-FUNC-009 and spec:201. contract.json:1020-1022 CHK-035. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:142 sets PPROT to '0, so o_apb_pprot=0 (slv.sv:237). |
| Test does | The item pprot is 0x7 (test:158), driven at Setup (test:406-407) and expected at the psel rise (test:241, :606-607). |
| A_rtl_wrong | For: mst.sv:142 tie-off.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The expected value is the driven S0 value. |
| C_spec_unclear | For: None.<br>Against: The requirement is explicit. |
| Options | Fix the RTL in mst.sv:142 (replace '0 with i_apb_pprot). |

## 12. test_chk_025_two_phase_duration/periods=4 [two-phase configs]: CHK-035/031 o_apb_pprot expected 0x4, got 0x0

**Most likely:** A_rtl_wrong

| Part | Content |
|---|---|
| Specification says | Spec:137 REQ-FUNC-009 and spec:201. contract.json:1020-1022 CHK-035. |
| RTL does | rtl/m_vlsit_apbcdc_mst.sv:142 sets PPROT to '0, so o_apb_pprot=0 (slv.sv:237). Earlier transfers that randomly drew pprot=0 pass this check, which is why the failure shows up later in this run (8850 ns). |
| Test does | The item pprot is 0x4 (test:158), driven at Setup (test:406-407) and expected at the psel rise (test:241, :606-607). |
| A_rtl_wrong | For: mst.sv:142 tie-off. The later failure time fits the random pprot happening to be 0 on earlier transfers.<br>Against: None found. |
| B_test_wrong | For: None.<br>Against: The expected value is the driven S0 value. |
| C_spec_unclear | For: None.<br>Against: The requirement is explicit. |
| Options | Fix the RTL in mst.sv:142 (replace '0 with i_apb_pprot). |


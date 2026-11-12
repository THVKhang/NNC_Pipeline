# Bug benchmark — async_apb_bridge

Each row is a hand-written RTL fault run against the approved tests and checkers. *Caught* means a test or check fails that passes on the unmodified RTL. The triage verdict is the most frequent cause given by the triage agent for the new failures (A = RTL wrong).

**Detection:** 3/3 (100.0 %) · **triage correct:** 3/3 (100.0 %), US$2.5583

| Bug | Fault | Spec | Caught | New failures | Triage verdict |
|---|---|---|---|---|---|
| AA1 | PPROT not forwarded (`m_vlsit_apbcdc_mst.sv`) | the request bundle carries PPROT | **yes** | test_chk_019_apb5_user_signals, test_chk_020_apb5_wakeup, test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_023_four_phase/periods=0, test_chk_023_four_phase/periods=1 … | A_rtl_wrong (correct) |
| AA2 | two-phase acknowledge detected on the wrong level (`m_vlsit_apbcdc_mst.sv`) | two-phase: ack event when ack equals req | **yes** | test_chk_019_apb5_user_signals, test_chk_020_apb5_wakeup, test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_024_requester_violations, test_chk_025_two_phase_duration/periods=0 … | A_rtl_wrong (correct) |
| AA3 | PSLVERR dropped on the requester side (`m_vlsit_apbcdc_mst.sv`) | PSLVERR is returned | **yes** | test_chk_019_apb5_user_signals, test_chk_020_apb5_wakeup, test_chk_021_apb4_ignores_apb5, test_chk_022_cfg_min, test_chk_023_four_phase/periods=0, test_chk_023_four_phase/periods=1 … | A_rtl_wrong (correct) |

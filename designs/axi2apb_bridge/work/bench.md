# Bug benchmark — axi2apb_bridge

Each row is a hand-written RTL fault run against the approved tests and checkers. *Caught* means a test or check fails that passes on the unmodified RTL. The triage verdict is the most frequent cause given by the triage agent for the new failures (A = RTL wrong).

**Detection:** 3/3 (100.0 %) · **triage correct:** 3/3 (100.0 %), US$1.9819

| Bug | Fault | Spec | Caught | New failures | Triage verdict |
|---|---|---|---|---|---|
| AX1 | write PPROT taken from the read channel (`m_axi2apb_apb_ctrl.sv`) | PPROT = AWPROT for writes | **yes** | test_chk_018_long_apb_wait, test_chk_021_response_backpressure, test_chk_023_unsupported_writes, test_chk_027_random_legal_bursts, test_chk_029_pprot_passthrough, test_chk_030_id_echo … | A_rtl_wrong (correct) |
| AX2 | PSLVERR of a read dropped (`m_axi2apb_apb_ctrl.sv`) | PSLVERR -> SLVERR on R | **yes** | test_chk_024_read_pslverr, test_chk_026_unmapped_default_completer, test_regression_random, CHK-011 | A_rtl_wrong (correct) |
| AX3 | read burst one beat short (`m_axi2apb_rd_seq.sv`) | ARLEN+1 beats | **yes** | test_chk_018_long_apb_wait, test_chk_019_arbitration_round_robin, test_chk_021_response_backpressure, test_chk_022_unsupported_reads, test_chk_024_read_pslverr, test_chk_026_unmapped_default_completer … | A_rtl_wrong (correct) |

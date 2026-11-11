# Bug benchmark — apb_tlul_bridge

Each row is a hand-written RTL fault run against the approved tests and checkers. *Caught* means a test or check fails that passes on the unmodified RTL. The triage verdict is the most frequent cause given by the triage agent for the new failures (A = RTL wrong).

**Detection:** 3/3 (100.0 %) · triage not run

| Bug | Fault | Spec | Caught | New failures | Triage verdict |
|---|---|---|---|---|---|
| TL1 | response source ID not checked (`m_tlul_if.sv`) | a wrong d_source is an error | **yes** | test_chk_020_wrong_opcode_source, test_chk_029_random_scoreboard, CHK-010 | — |
| TL2 | partial-strobe write accepted (`m_apb_if.sv`) | only full-word writes are legal | **yes** | test_chk_018_local_error, test_chk_025_ignored_inputs, test_chk_028_back_to_back, test_chk_029_random_scoreboard, CHK-014, CHK-007 | — |
| TL3 | read data returned with an error response (`m_tlul_if.sv`) | PRDATA zero on error | **yes** | test_chk_019_device_error, test_chk_020_wrong_opcode_source, test_chk_025_ignored_inputs, test_chk_028_back_to_back, test_chk_029_random_scoreboard, test_regression_random … | — |

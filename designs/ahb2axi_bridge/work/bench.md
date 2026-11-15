# Bug benchmark — ahb2axi_bridge

Each row is a hand-written RTL fault run against the approved tests and checkers. *Caught* means a test or check fails that passes on the unmodified RTL. The triage verdict is the most frequent cause given by the triage agent for the new failures (A = RTL wrong).

**Detection:** 1/3 (33.3 %) · triage not run

| Bug | Fault | Spec | Caught | New failures | Triage verdict |
|---|---|---|---|---|---|
| AH1 | WLAST one beat early in an aggregated write burst (never raised for a one-beat burst) (`m_ahb2axi_ctrl.sv`) | AXI WLAST on the final beat of the burst (AWLEN = beats - 1) | no | — | — |
| AH2 | read DECERR returned as AHB OKAY (`m_ahb2axi_ctrl.sv`) | REQ-ERR-001: SLVERR, DECERR and EXOKAY map to the AHB two-cycle ERROR | no | — | — |
| AH3 | word alignment checks only address bit 0 (`m_ahb2axi_ctrl.sv`) | REQ-ERR-002: a misaligned transfer returns AHB ERROR with no AXI request | **yes** | test_chk_030_rejected_controls, CHK-012, CHK-013 | — |

# Bug benchmark — async_gray_fifo

Each row is a hand-written RTL fault run against the approved tests and checkers. *Caught* means a test or check fails that passes on the unmodified RTL. The triage verdict is the most frequent cause given by the triage agent for the new failures (A = RTL wrong).

**Detection:** 3/3 (100.0 %) · triage not run

| Bug | Fault | Spec | Caught | New failures | Triage verdict |
|---|---|---|---|---|---|
| AF1 | full compares only the MSB of the Gray pointers (`m_vlsit_afifo_wr.sv`) | full: two MSBs inverted (Gray) | **yes** | test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_with_model, test_chk_016_random_ratios/pair=0, test_chk_016_random_ratios/pair=1, test_chk_016_random_ratios/pair=2 … | — |
| AF2 | overflow pulse also for a blocked write (`m_vlsit_afifo_wr.sv`) | REQ-SRST-017 | **yes** | test_chk_026_srst_pulse_full_overflow, test_chk_028_srst_reassert_in_rel, test_chk_031_clock_stop_during_srst, CHK-008 | — |
| AF3 | binary instead of Gray pointer launched across (`m_vlsit_afifo_wr.sv`) | CDC-001: Gray pointer crossing | **yes** | test_chk_014_nominal_latency/per=0, test_chk_014_nominal_latency/per=1, test_chk_015_latency_with_model, test_chk_016_random_ratios/pair=0, test_chk_016_random_ratios/pair=1, test_chk_016_random_ratios/pair=2 … | — |

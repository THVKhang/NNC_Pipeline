# Bug benchmark — async_gray_fifo

Each row is a hand-written RTL fault run against the approved tests and checkers. *Caught* means a test or check fails that passes on the unmodified RTL. The triage verdict is the most frequent cause given by the triage agent for the new failures (A = RTL wrong).

**Detection:** 3/3 (100.0 %) · triage not run

| Bug | Fault | Spec | Caught | New failures | Triage verdict |
|---|---|---|---|---|---|
| AF1 | full compares only the MSB of the Gray pointers (`m_vlsit_afifo_wr.sv`) | full: two MSBs inverted (Gray) | **yes** | test_chk_015_model_latency_window, test_chk_019_back_to_back_equal_clocks, test_chk_021_underflow, test_chk_023_hw_reset_during_sw_reset, test_chk_025_srst_partly_filled_held, test_chk_026_srst_one_cycle_pulse_full … | — |
| AF2 | overflow pulse also for a blocked write (`m_vlsit_afifo_wr.sv`) | REQ-SRST-017 | **yes** | test_chk_025_srst_partly_filled_held, test_chk_026_srst_one_cycle_pulse_full, test_chk_030_after_srst_like_hw_reset, test_chk_031_clock_stop_during_srst, CHK-008 | — |
| AF3 | binary instead of Gray pointer launched across (`m_vlsit_afifo_wr.sv`) | CDC-001: Gray pointer crossing | **yes** | test_chk_015_model_latency_window, test_chk_019_back_to_back_equal_clocks, test_chk_021_underflow, test_chk_023_hw_reset_during_sw_reset, test_chk_025_srst_partly_filled_held, test_chk_026_srst_one_cycle_pulse_full … | — |

# Bug benchmark — sync_fifo

Each row is a hand-written RTL fault run against the approved tests and checkers. *Caught* means a test or check fails that passes on the unmodified RTL. The triage verdict is the most frequent cause given by the triage agent for the new failures (A = RTL wrong).

**Detection:** 3/3 (100.0 %) · triage not run

| Bug | Fault | Spec | Caught | New failures | Triage verdict |
|---|---|---|---|---|---|
| SF1 | full flag one entry early (`m_vlsit_sfifo_wr.sv`) | full when no free entry | **yes** | test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1, test_chk_013_random_ratios/ratio=2, test_chk_013_random_ratios/ratio=3, test_chk_013_random_ratios/ratio=4 … | — |
| SF2 | overflow pulse also for a blocked write (`m_vlsit_sfifo_wr.sv`) | a blocked write raises no overflow | **yes** | test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1, test_chk_013_random_ratios/ratio=2, test_chk_013_random_ratios/ratio=3, test_chk_013_random_ratios/ratio=4, test_chk_013_random_ratios/ratio=5 … | — |
| SF3 | empty threshold compare off by one (`m_vlsit_sfifo_rd.sv`) | o_empty_thr when occupancy <= threshold | **yes** | test_chk_012_strict_later_latency_3_2, test_chk_013_random_ratios/ratio=0, test_chk_013_random_ratios/ratio=1, test_chk_013_random_ratios/ratio=2, test_chk_013_random_ratios/ratio=3, test_chk_013_random_ratios/ratio=5 … | — |

# Formal check — async_gray_fifo

SymbiYosys on the generated assertions, translated to immediate form by `nnc/formal.py`. Depth 20 cycles, multiclock (free clocks), environment: reset assumptions + verif/formal/nnc_env.sv, defines VLSIT_SYNTHESIS.

- **PROVEN**: holds in every reachable state (k-induction).
- **BOUNDED**: no counterexample within 20 cycles from reset; induction inconclusive.
- **CEX**: a counterexample exists. Either a design bug, or an input sequence the environment should forbid (a missing assumption). The trace (VCD) shows which.
- **VACUOUS**: the antecedent cannot occur within the depth under the assumptions: the environment is too strict (or the condition is unreachable); the other results say nothing.
- **UNSUPPORTED**: the assertion uses SVA outside the translated subset, or its checker is simulation-only (event timing, queues); not checked.
- **TIMEOUT**: the solver did not finish within 600 s per task; nothing concluded.

**Result:** {'BOUNDED': 8, 'CEX': 2, 'PROVEN': 1, 'UNSUPPORTED': 2}

| Check | Title | Formal | Detail |
|---|---|---|---|
| CHK-001 | Read-domain hardware reset values | **BOUNDED** |  |
| CHK-002 | o_underflow is the registered one-cycle pulse of a non-blocked read while empty | **BOUNDED** |  |
| CHK-003 | o_empty_thr consistency for every 4-bit i_empty_thr | **CEX** | trace: work/formal/CHK-003.vcd |
| CHK-004 | Read-domain outputs change only at i_clk_rd edges | **BOUNDED** |  |
| CHK-005 | Scoreboard: show-ahead data, write order, exactly-once, software-reset discard | **UNSUPPORTED** | a_CHK_005: checker nnc_chk_sb is simulation-only: queues (`[$]`) |
| CHK-006 | Flags are never optimistic; occupancy is within 0..PARA_AFIFO_DEPTH | **UNSUPPORTED** | a_CHK_006: checker nnc_chk_sb is simulation-only: queues (`[$]`); a_CHK_006_r: checker nnc_chk_sb is simulation-only: queues (`[$]`) |
| CHK-007 | Write-domain hardware reset values | **BOUNDED** |  |
| CHK-008 | o_overflow is the registered one-cycle pulse of a non-blocked write while full | **BOUNDED** |  |
| CHK-009 | Write block forces o_full=1 and the empty-FIFO o_full_thr with zero latency | **PROVEN** |  |
| CHK-010 | o_sw_rst_busy rises exactly at the first edge sampling i_rst_n_sw=0 | **BOUNDED** |  |
| CHK-011 | o_sw_rst_busy falls only after i_rst_n_sw=1 plus a crossing round trip; write side is clean at the release | **BOUNDED** |  |
| CHK-012 | Write-domain outputs change only at i_clk_wr edges | **BOUNDED** |  |
| CHK-013 | o_full_thr consistency for every 4-bit i_full_thr | **CEX** | trace: work/formal/CHK-013.vcd |

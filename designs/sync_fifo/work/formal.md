# Formal check — sync_fifo

SymbiYosys on the generated assertions, translated to immediate form by `nnc/formal.py`. Depth 20 cycles, one global clock, environment: reset assumptions + verif/formal/nnc_env.sv.

- **PROVEN**: holds in every reachable state (k-induction).
- **BOUNDED**: no counterexample within 20 cycles from reset; induction inconclusive.
- **CEX**: a counterexample exists. Either a design bug, or an input sequence the environment should forbid (a missing assumption). The trace (VCD) shows which.
- **VACUOUS**: the antecedent cannot occur within the depth under the assumptions: the environment is too strict (or the condition is unreachable); the other results say nothing.
- **UNSUPPORTED**: the assertion uses SVA outside the translated subset, or its checker is simulation-only (event timing, queues); not checked.
- **TIMEOUT**: the solver did not finish within 600 s per task; nothing concluded.

**Result:** {'BOUNDED': 5, 'PROVEN': 4, 'TIMEOUT': 1, 'UNSUPPORTED': 1}

| Check | Title | Formal | Detail |
|---|---|---|---|
| CHK-001 | Outputs change only at their own clock edge | **UNSUPPORTED** | a_CHK_001: checker nnc_chk_clk is simulation-only: simulation time (`$time`); a_CHK_001_rd: checker nnc_chk_clk is simulation-only: simulation time (`$time`) |
| CHK-002 | No unknown input when a request is sampled | **PROVEN** |  |
| CHK-003 | Reads blocked while software reset busy | **BOUNDED** |  |
| CHK-004 | Read-view occupancy model for o_empty and o_empty_thr | **BOUNDED** |  |
| CHK-005 | o_underflow one-cycle pulse | **BOUNDED** |  |
| CHK-006 | Scoreboard: order, no loss, no duplication, show-ahead data | **TIMEOUT** |  |
| CHK-007 | Occupancy bounds and safe-direction flag lag | **BOUNDED** |  |
| CHK-008 | o_sw_rst_busy start and idle behavior | **PROVEN** |  |
| CHK-009 | Write block term forces o_full and o_full_thr | **PROVEN** |  |
| CHK-010 | Write-view occupancy model for o_full and o_full_thr | **BOUNDED** |  |
| CHK-011 | o_overflow exact one-cycle pulse | **PROVEN** |  |

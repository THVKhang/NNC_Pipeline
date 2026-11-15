# Formal check — async_gray_fifo

SymbiYosys on the generated assertions, translated to immediate form by `nnc/formal.py`. Depth 20 cycles, multiclock (free clocks), environment: reset assumptions + verif/formal/nnc_env.sv, defines VLSIT_SYNTHESIS.

- **PROVEN**: holds in every reachable state (k-induction).
- **BOUNDED**: no counterexample within 20 cycles from reset; induction inconclusive.
- **CEX**: a counterexample exists. Either a design bug, or an input sequence the environment should forbid (a missing assumption). The trace (VCD) shows which.
- **VACUOUS**: the antecedent cannot occur within the depth under the assumptions: the environment is too strict (or the condition is unreachable); the other results say nothing.
- **UNSUPPORTED**: the assertion uses SVA outside the translated subset, or its checker is simulation-only (event timing, queues); not checked.
- **TIMEOUT**: the solver did not finish within 600 s per task; nothing concluded.

**Result:** {'BOUNDED': 2, 'PROVEN': 5, 'UNSUPPORTED': 6}

Configurations (parameters of the run set; a check counts as PROVEN only if proven in every configuration where it is not vacuous):

- base: {'BOUNDED': 1, 'PROVEN': 6, 'UNSUPPORTED': 6}
- cell1: {'BOUNDED': 1, 'PROVEN': 6, 'UNSUPPORTED': 6}
- cell3: {'BOUNDED': 1, 'PROVEN': 6, 'UNSUPPORTED': 6}
- cell4: {'BOUNDED': 2, 'PROVEN': 5, 'UNSUPPORTED': 6}
- macro: {'BOUNDED': 1, 'PROVEN': 6, 'UNSUPPORTED': 6}
- small: {'BOUNDED': 1, 'PROVEN': 6, 'UNSUPPORTED': 6}

| Check | Title | Formal | Detail |
|---|---|---|---|
| CHK-001 | Read-domain hardware reset values | **UNSUPPORTED** | a_CHK_001: checker nnc_chk_rd is simulation-only: simulation time (`time`) (base UNSUPPORTED, cell1 UNSUPPORTED, cell3 UNSUPPORTED, cell4 UNSUPPORTED, macro UNSUPPORTED, small UNSUPPORTED) |
| CHK-002 | o_underflow is the registered one-cycle pulse of a non-blocked read while empty | **UNSUPPORTED** | a_CHK_002: checker nnc_chk_rd is simulation-only: simulation time (`time`) (base UNSUPPORTED, cell1 UNSUPPORTED, cell3 UNSUPPORTED, cell4 UNSUPPORTED, macro UNSUPPORTED, small UNSUPPORTED) |
| CHK-003 | o_empty_thr consistency for every 4-bit i_empty_thr | **UNSUPPORTED** | a_CHK_003: checker nnc_chk_rd is simulation-only: simulation time (`time`) (base UNSUPPORTED, cell1 UNSUPPORTED, cell3 UNSUPPORTED, cell4 UNSUPPORTED, macro UNSUPPORTED, small UNSUPPORTED) |
| CHK-004 | Read-domain outputs change only at i_clk_rd edges | **UNSUPPORTED** | a_CHK_004: checker nnc_chk_rd is simulation-only: simulation time (`time`) (base UNSUPPORTED, cell1 UNSUPPORTED, cell3 UNSUPPORTED, cell4 UNSUPPORTED, macro UNSUPPORTED, small UNSUPPORTED) |
| CHK-005 | Scoreboard: show-ahead data, write order, exactly-once, software-reset discard | **UNSUPPORTED** | a_CHK_005: checker nnc_chk_sb is simulation-only: queues (`[$]`) (base UNSUPPORTED, cell1 UNSUPPORTED, cell3 UNSUPPORTED, cell4 UNSUPPORTED, macro UNSUPPORTED, small UNSUPPORTED) |
| CHK-006 | Flags are never optimistic; occupancy is within 0..PARA_AFIFO_DEPTH | **UNSUPPORTED** | a_CHK_006: checker nnc_chk_sb is simulation-only: queues (`[$]`); a_CHK_006_rd: checker nnc_chk_sb is simulation-only: queues (`[$]`) (base UNSUPPORTED, cell1 UNSUPPORTED, cell3 UNSUPPORTED, cell4 UNS |
| CHK-007 | Write-domain hardware reset values | **PROVEN** | (base PROVEN, cell1 PROVEN, cell3 PROVEN, cell4 PROVEN, macro PROVEN, small PROVEN) |
| CHK-008 | o_overflow is the registered one-cycle pulse of a non-blocked write while full | **PROVEN** | (base PROVEN, cell1 PROVEN, cell3 PROVEN, cell4 PROVEN, macro PROVEN, small PROVEN) |
| CHK-009 | Write block forces o_full=1 and the empty-FIFO o_full_thr with zero latency | **PROVEN** | (base PROVEN, cell1 PROVEN, cell3 PROVEN, cell4 PROVEN, macro PROVEN, small PROVEN) |
| CHK-010 | o_sw_rst_busy rises exactly at the first edge sampling i_rst_n_sw=0 | **PROVEN** | (base PROVEN, cell1 PROVEN, cell3 PROVEN, cell4 PROVEN, macro PROVEN, small PROVEN) |
| CHK-011 | o_sw_rst_busy falls only after i_rst_n_sw=1 plus a crossing round trip; write side is clean at the release | **BOUNDED** | (base BOUNDED, cell1 BOUNDED, cell3 BOUNDED, cell4 BOUNDED, macro BOUNDED, small BOUNDED) |
| CHK-012 | Write-domain outputs change only at i_clk_wr edges | **PROVEN** | (base PROVEN, cell1 PROVEN, cell3 PROVEN, cell4 PROVEN, macro PROVEN, small PROVEN) |
| CHK-013 | o_full_thr consistency for every 4-bit i_full_thr | **BOUNDED** | (base PROVEN, cell1 PROVEN, cell3 PROVEN, cell4 BOUNDED, macro PROVEN, small PROVEN) |

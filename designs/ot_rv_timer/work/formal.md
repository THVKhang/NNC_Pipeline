# Formal check — ot_rv_timer

SymbiYosys on the generated assertions, translated to immediate form by `nnc/formal.py`. Depth 32 cycles, one global clock, environment: reset assumptions + verif/formal/nnc_env.sv, defines SYNTHESIS.

- **PROVEN**: holds in every reachable state (k-induction).
- **BOUNDED**: no counterexample within 32 cycles from reset; induction inconclusive.
- **CEX**: a counterexample exists. Either a design bug, or an input sequence the environment should forbid (a missing assumption). The trace (VCD) shows which.
- **VACUOUS**: the antecedent cannot occur within the depth under the assumptions: the environment is too strict (or the condition is unreachable); the other results say nothing.
- **UNSUPPORTED**: the assertion uses SVA outside the translated subset, or its checker is simulation-only (event timing, queues); not checked.
- **TIMEOUT**: the solver did not finish within 600 s per task; nothing concluded.

**Result:** {'BOUNDED': 2, 'CEX': 1, 'PROVEN': 7, 'TIMEOUT': 1, 'UNSUPPORTED': 2}

| Check | Title | Formal | Detail |
|---|---|---|---|
| CHK-001 | No alert signal-integrity failure | **PROVEN** |  |
| CHK-002 | o_alert is a single-cycle pulse per handshake | **PROVEN** |  |
| CHK-003 | No spurious alerts, no more pulses than test writes | **BOUNDED** |  |
| CHK-004 | Interrupt output masked by INTR_ENABLE0.IE_0 | **PROVEN** |  |
| CHK-005 | Latched interrupt falls only after a clearing write or reset | **BOUNDED** |  |
| CHK-006 | Outputs inactive during reset | **UNSUPPORTED** | a_CHK_006: checker nnc_chk_reset is simulation-only: falling clock edge in a one-clock model (`negedge clk_i`) |
| CHK-007 | Outputs change only at rising clock edges | **UNSUPPORTED** | a_CHK_007: checker nnc_chk_reset is simulation-only: falling clock edge in a one-clock model (`negedge clk_i`) |
| CHK-008 | Test-bench host obligations (stimulus self-check) | **CEX** | trace: work/formal/CHK-008.vcd |
| CHK-009 | Every D-channel beat matches exactly one outstanding request | **PROVEN** |  |
| CHK-010 | Response opcode and size echo | **PROVEN** |  |
| CHK-011 | d_error value for classified requests | **TIMEOUT** |  |
| CHK-012 | D channel holds under back-pressure | **PROVEN** |  |
| CHK-013 | Response integrity never fails | **PROVEN** |  |

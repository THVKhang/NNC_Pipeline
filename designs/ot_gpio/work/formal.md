# Formal check — ot_gpio

SymbiYosys on the generated assertions, translated to immediate form by `nnc/formal.py`. Depth 32 cycles, one global clock, environment: reset assumptions + verif/formal/nnc_env.sv, defines SYNTHESIS.

- **PROVEN**: holds in every reachable state (k-induction).
- **BOUNDED**: no counterexample within 32 cycles from reset; induction inconclusive.
- **CEX**: a counterexample exists. Either a design bug, or an input sequence the environment should forbid (a missing assumption). The trace (VCD) shows which.
- **VACUOUS**: the antecedent cannot occur within the depth under the assumptions: the environment is too strict (or the condition is unreachable); the other results say nothing.
- **UNSUPPORTED**: the assertion uses SVA outside the translated subset, or its checker is simulation-only (event timing, queues); not checked.
- **TIMEOUT**: the solver did not finish within 600 s per task; nothing concluded.

**Result:** {'PROVEN': 10, 'TIMEOUT': 1, 'UNSUPPORTED': 2}

Configurations (parameters of the run set; a check counts as PROVEN only if proven in every configuration where it is not vacuous):

- base: {'PROVEN': 10, 'TIMEOUT': 1, 'UNSUPPORTED': 2}
- sync_off: {'PROVEN': 10, 'TIMEOUT': 1, 'UNSUPPORTED': 2}
- straps_off: {'PROVEN': 9, 'TIMEOUT': 1, 'UNSUPPORTED': 2, 'VACUOUS': 1}
- min: {'PROVEN': 9, 'TIMEOUT': 1, 'UNSUPPORTED': 2, 'VACUOUS': 1}

| Check | Title | Formal | Detail |
|---|---|---|---|
| CHK-001 | Alert signal integrity never fails | **PROVEN** | (base PROVEN, sync_off PROVEN, straps_off PROVEN, min PROVEN) |
| CHK-002 | o_alert is a single-cycle pulse | **PROVEN** | (base PROVEN, sync_off PROVEN, straps_off PROVEN, min PROVEN) |
| CHK-003 | No alert without an alert cause | **PROVEN** | (base PROVEN, sync_off PROVEN, straps_off PROVEN, min PROVEN) |
| CHK-004 | o_gpio / o_gpio_en follow the DATA_OUT / DATA_OE shadow model | **PROVEN** | (base PROVEN, sync_off PROVEN, straps_off PROVEN, min PROVEN) |
| CHK-005 | D-channel response integrity never fails | **PROVEN** | (base PROVEN, sync_off PROVEN, straps_off PROVEN, min PROVEN) |
| CHK-006 | Disabled interrupts never assert o_intr_gpio | **PROVEN** | (base PROVEN, sync_off PROVEN, straps_off PROVEN, min PROVEN) |
| CHK-007 | Interrupt level is held until software acknowledges it | **PROVEN** | (base PROVEN, sync_off PROVEN, straps_off PROVEN, min PROVEN) |
| CHK-008 | Outputs held at zero during reset | **PROVEN** | not translated: a_CHK_008_neg: no single `@(posedge clk)` clocking (base PROVEN, sync_off PROVEN, straps_off PROVEN, min PROVEN) |
| CHK-009 | Strap outputs: invalid before the trigger, frozen after sampling | **PROVEN** | (base PROVEN, sync_off PROVEN, straps_off VACUOUS, min VACUOUS) |
| CHK-010 | Outputs change only at rising clock edges | **UNSUPPORTED** | a_CHK_010: checker nnc_chk_timing is simulation-only: falling clock edge in a one-clock model (`negedge clk_i`) (base UNSUPPORTED, sync_off UNSUPPORTED, straps_off UNSUPPORTED, min UNSUPPORTED) |
| CHK-011 | Test-bench stimulus legality monitor (host rules and plan constraints) | **UNSUPPORTED** | a_CHK_011: checker nnc_chk_tlhost is simulation-only: falling clock edge in a one-clock model (`negedge clk_i`); a_CHK_011_rst: checker nnc_chk_tlhost is simulation-only: falling clock edge in a one-c |
| CHK-012 | D channel held stable under back-pressure | **PROVEN** | (base PROVEN, sync_off PROVEN, straps_off PROVEN, min PROVEN) |
| CHK-013 | Response matches an outstanding request (source/size/opcode echo, no orphans) | **TIMEOUT** | (base TIMEOUT, sync_off TIMEOUT, straps_off TIMEOUT, min TIMEOUT) |

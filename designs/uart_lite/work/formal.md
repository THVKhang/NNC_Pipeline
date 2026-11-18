# Formal check — uart_lite

SymbiYosys on the generated assertions, translated to immediate form by `nnc/formal.py`. Depth 64 cycles, one global clock, environment: reset assumptions + verif/formal/nnc_env.sv.

- **PROVEN**: holds in every reachable state (k-induction).
- **BOUNDED**: no counterexample within 64 cycles from reset; induction inconclusive.
- **CEX**: a counterexample exists. Either a design bug, or an input sequence the environment should forbid (a missing assumption). The trace (VCD) shows which.
- **VACUOUS**: the antecedent cannot occur within the depth under the assumptions: the environment is too strict (or the condition is unreachable); the other results say nothing.
- **UNSUPPORTED**: the assertion uses SVA outside the translated subset, or its checker is simulation-only (event timing, queues); not checked.
- **TIMEOUT**: the solver did not finish within 600 s per task; nothing concluded.

**Result:** {'BOUNDED': 6, 'PROVEN': 4, 'UNSUPPORTED': 1, 'VACUOUS': 2}

Configurations (parameters of the run set; a check counts as PROVEN only if proven in every configuration where it is not vacuous):

- base: {'BOUNDED': 1, 'PROVEN': 6, 'UNSUPPORTED': 1, 'VACUOUS': 5}
- min: {'BOUNDED': 2, 'PROVEN': 8, 'UNSUPPORTED': 1, 'VACUOUS': 2}
- odd: {'BOUNDED': 2, 'PROVEN': 8, 'UNSUPPORTED': 1, 'VACUOUS': 2}
- wide: {'BOUNDED': 5, 'PROVEN': 2, 'UNSUPPORTED': 1, 'VACUOUS': 5}

| Check | Title | Formal | Detail |
|---|---|---|---|
| CHK-001 | Outputs change only at i_clk rising edges or reset assertion | **UNSUPPORTED** | a_CHK_001: checker nnc_chk_gen is simulation-only: simulation time (`time`) (base UNSUPPORTED, min UNSUPPORTED, odd UNSUPPORTED, wide UNSUPPORTED) |
| CHK-002 | Output values while reset is asserted, including immediately after asynchronous assertion | **PROVEN** | (base PROVEN, min PROVEN, odd PROVEN, wide PROVEN) |
| CHK-003 | Delivery into an empty holding register at V=M+2 | **BOUNDED** | (base VACUOUS, min BOUNDED, odd BOUNDED, wide VACUOUS) |
| CHK-004 | Held byte taken at the delivery edge itself loads the new byte, no overrun | **VACUOUS** | (base VACUOUS, min VACUOUS, odd VACUOUS, wide VACUOUS) |
| CHK-005 | Overrun drop at V keeps the held byte; one-cycle pulse | **VACUOUS** | (base VACUOUS, min VACUOUS, odd VACUOUS, wide VACUOUS) |
| CHK-006 | o_rx_overrun only after a drop edge, independent of o_rx_valid | **BOUNDED** | (base PROVEN, min PROVEN, odd PROVEN, wide BOUNDED) |
| CHK-007 | Consumer take empties the holding register | **PROVEN** | (base VACUOUS, min PROVEN, odd PROVEN, wide VACUOUS) |
| CHK-008 | Held byte is stable until taken | **PROVEN** | (base VACUOUS, min PROVEN, odd PROVEN, wide VACUOUS) |
| CHK-009 | Empty register: i_rx_ready has no effect; data and flag keep the last loaded values | **BOUNDED** | (base PROVEN, min PROVEN, odd PROVEN, wide BOUNDED) |
| CHK-010 | Transmit handshake, acceptance condition and idle values | **BOUNDED** | (base PROVEN, min PROVEN, odd PROVEN, wide BOUNDED) |
| CHK-011 | Cycle-exact transmit frame content (8N1, LSB first, N cycles per bit) | **BOUNDED** | (base BOUNDED, min BOUNDED, odd BOUNDED, wide BOUNDED) |
| CHK-012 | o_tx_ready timing during a frame | **BOUNDED** | (base PROVEN, min PROVEN, odd PROVEN, wide BOUNDED) |
| CHK-013 | No idle cycle between back-to-back frames; idle high after a frame | **PROVEN** | (base PROVEN, min PROVEN, odd PROVEN, wide PROVEN) |

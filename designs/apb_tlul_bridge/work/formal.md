# Formal check — apb_tlul_bridge

SymbiYosys on the generated assertions, translated to immediate form by `nnc/formal.py`. Depth 20 cycles, one global clock, environment: reset assumptions + verif/formal/nnc_env.sv.

- **PROVEN**: holds in every reachable state (k-induction).
- **BOUNDED**: no counterexample within 20 cycles from reset; induction inconclusive.
- **CEX**: a counterexample exists. Either a design bug, or an input sequence the environment should forbid (a missing assumption). The trace (VCD) shows which.
- **VACUOUS**: the antecedent cannot occur within the depth under the assumptions: the environment is too strict (or the condition is unreachable); the other results say nothing.
- **UNSUPPORTED**: the assertion uses SVA outside the translated subset, or its checker is simulation-only (event timing, queues); not checked.
- **TIMEOUT**: the solver did not finish within 600 s per task; nothing concluded.

**Result:** {'BOUNDED': 7, 'PROVEN': 10}

| Check | Title | Formal | Detail |
|---|---|---|---|
| CHK-001 | PREADY only in an APB Access cycle | **BOUNDED** |  |
| CHK-002 | PREADY is a one-cycle pulse | **PROVEN** |  |
| CHK-003 | PSLVERR only with PREADY | **PROVEN** |  |
| CHK-004 | PRDATA holds its value outside PREADY | **PROVEN** |  |
| CHK-005 | PRDATA is zero on write and error completions | **BOUNDED** |  |
| CHK-006 | Legal Setup launches the request from flops in the first Access cycle | **BOUNDED** |  |
| CHK-007 | Illegal Setup completes locally in the first Access cycle with no request | **BOUNDED** |  |
| CHK-008 | One request at a time, none before the APB completion | **BOUNDED** |  |
| CHK-009 | a_valid only inside an APB Access phase before PREADY | **PROVEN** |  |
| CHK-010 | Accepted TL-UL response is checked and mapped to the APB completion one cycle later | **BOUNDED** |  |
| CHK-011 | PREADY only caused by an illegal Setup or a counted response (orphans have no APB effect) | **BOUNDED** |  |
| CHK-012 | Output values while reset is asserted | **PROVEN** |  |
| CHK-013 | d_ready constant 1 after the first edge following reset release | **PROVEN** |  |
| CHK-014 | A request starts only after a legal Setup | **PROVEN** |  |
| CHK-015 | Channel A held and stable until accepted | **PROVEN** |  |
| CHK-016 | a_valid drops after the handshake (accepted once) | **PROVEN** |  |
| CHK-017 | Constant A-channel fields and legal opcode, size, mask and address | **PROVEN** |  |

# Formal check — axi2apb_bridge

SymbiYosys on the generated assertions, translated to immediate form by `nnc/formal.py`. Depth 20 cycles, one global clock, environment: reset assumptions + verif/formal/nnc_env.sv.

- **PROVEN**: holds in every reachable state (k-induction).
- **BOUNDED**: no counterexample within 20 cycles from reset; induction inconclusive.
- **CEX**: a counterexample exists. Either a design bug, or an input sequence the environment should forbid (a missing assumption). The trace (VCD) shows which.
- **VACUOUS**: the antecedent cannot occur within the depth under the assumptions: the environment is too strict (or the condition is unreachable); the other results say nothing.
- **UNSUPPORTED**: the assertion uses SVA outside the translated subset, or its checker is simulation-only (event timing, queues); not checked.
- **TIMEOUT**: the solver did not finish within 600 s per task; nothing concluded.

**Result:** {'BOUNDED': 7, 'PROVEN': 9, 'TIMEOUT': 1}

| Check | Title | Formal | Detail |
|---|---|---|---|
| CHK-001 | APB SETUP/ACCESS phase sequencing | **PROVEN** |  |
| CHK-002 | APB wait-state hold of control and payload | **PROVEN** |  |
| CHK-003 | APB payload stable from SETUP into ACCESS | **PROVEN** |  |
| CHK-004 | PADDR word aligned | **PROVEN** |  |
| CHK-005 | PSTRB zero on APB reads | **PROVEN** |  |
| CHK-006 | APB outputs zero when idle | **PROVEN** |  |
| CHK-007 | B channel hold under BREADY backpressure | **PROVEN** |  |
| CHK-008 | Single B after all W beats and APB writes, with correct BID/BRESP | **BOUNDED** |  |
| CHK-009 | R channel hold under RREADY backpressure | **PROVEN** |  |
| CHK-010 | RID echo, RLAST position and R beat count | **BOUNDED** |  |
| CHK-011 | Legal read beat data and response from the APB completion | **BOUNDED** |  |
| CHK-012 | Unsupported read beats are SLVERR with zero data | **BOUNDED** |  |
| CHK-013 | WREADY gated by AW acceptance; W beats never exceed AWLEN+1 | **BOUNDED** |  |
| CHK-014 | Transaction tracker: one global owner, actions only after the handshake | **BOUNDED** |  |
| CHK-015 | No APB activity for unsupported requests | **BOUNDED** |  |
| CHK-016 | APB transfer sequence matches AXI beats (direction, address, PPROT, data, strobes, count) | **TIMEOUT** |  |
| CHK-017 | Synchronous reset values of all outputs | **PROVEN** |  |

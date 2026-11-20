# Formal check — axil_regfile

SymbiYosys on the generated assertions, translated to immediate form by `nnc/formal.py`. Depth 32 cycles, one global clock, environment: reset assumptions + verif/formal/nnc_env.sv. A check VACUOUS at that depth was run again alone at twice the depth, up to 128 cycles (its row gives the depth used).

- **PROVEN**: holds in every reachable state (k-induction).
- **BOUNDED**: no counterexample within 32 cycles from reset; induction inconclusive.
- **CEX**: a counterexample exists. Either a design bug, or an input sequence the environment should forbid (a missing assumption). The trace (VCD) shows which.
- **VACUOUS**: the antecedent cannot occur within the depth under the assumptions: the environment is too strict (or the condition is unreachable); the other results say nothing.
- **UNSUPPORTED**: the assertion uses SVA outside the translated subset, or its checker is simulation-only (event timing, queues); not checked.
- **TIMEOUT**: the solver did not finish within 600 s per task; nothing concluded.

**Result:** {'BOUNDED': 1, 'PROVEN': 15, 'UNSUPPORTED': 1}

Configurations (parameters of the run set; a check counts as PROVEN only if proven in every configuration where it is not vacuous):

- base: {'BOUNDED': 1, 'PROVEN': 15, 'UNSUPPORTED': 1}
- min: {'BOUNDED': 1, 'PROVEN': 15, 'UNSUPPORTED': 1}
- max: {'BOUNDED': 1, 'PROVEN': 15, 'UNSUPPORTED': 1}
- full_a7: {'BOUNDED': 1, 'PROVEN': 15, 'UNSUPPORTED': 1}

| Check | Title | Formal | Detail |
|---|---|---|---|
| CHK-001 | o_s_axi_arready follows the held-read-address state | **PROVEN** | (base PROVEN, min PROVEN, max PROVEN, full_a7 PROVEN) |
| CHK-002 | o_s_axi_rvalid is exactly predicted: 1 from Ear until Er, otherwise 0 | **PROVEN** | (base PROVEN, min PROVEN, max PROVEN, full_a7 PROVEN) |
| CHK-003 | R response held stable under back-pressure | **PROVEN** | (base PROVEN, min PROVEN, max PROVEN, full_a7 PROVEN) |
| CHK-004 | o_s_axi_rresp never EXOKAY or DECERR | **PROVEN** | (base PROVEN, min PROVEN, max PROVEN, full_a7 PROVEN) |
| CHK-005 | Read data and response match the value sampled at Ear | **BOUNDED** | (base BOUNDED, min BOUNDED, max BOUNDED, full_a7 BOUNDED) |
| CHK-006 | o_s_axi_awready follows the held-write-address state | **PROVEN** | (base PROVEN, min PROVEN, max PROVEN, full_a7 PROVEN) |
| CHK-007 | o_s_axi_wready follows the held-write-data state | **PROVEN** | (base PROVEN, min PROVEN, max PROVEN, full_a7 PROVEN) |
| CHK-008 | o_s_axi_bvalid is exactly predicted: 1 from Ec until Eb, otherwise 0 | **PROVEN** | (base PROVEN, min PROVEN, max PROVEN, full_a7 PROVEN) |
| CHK-009 | B response held stable under back-pressure | **PROVEN** | (base PROVEN, min PROVEN, max PROVEN, full_a7 PROVEN) |
| CHK-010 | o_s_axi_bresp never EXOKAY or DECERR | **PROVEN** | (base PROVEN, min PROVEN, max PROVEN, full_a7 PROVEN) |
| CHK-011 | o_s_axi_bresp matches the decode of the address taken at Ea | **PROVEN** | (base PROVEN, min PROVEN, max PROVEN, full_a7 PROVEN) |
| CHK-012 | o_regs equals the reference register model every cycle | **PROVEN** | not translated: a_CHK_012_neg: no single `@(posedge clk)` clocking (base PROVEN, min PROVEN, max PROVEN, full_a7 PROVEN) |
| CHK-013 | Handshake outputs are 0 while reset is asserted; no transfer while i_rst_n=0 | **PROVEN** | not translated: a_CHK_013_n: no single `@(posedge clk)` clocking (base PROVEN, min PROVEN, max PROVEN, full_a7 PROVEN) |
| CHK-014 | Data outputs and o_regs are 0 while reset is asserted | **PROVEN** | not translated: a_CHK_014_n: no single `@(posedge clk)` clocking (base PROVEN, min PROVEN, max PROVEN, full_a7 PROVEN) |
| CHK-015 | No transfer at R1 | **PROVEN** | (base PROVEN, min PROVEN, max PROVEN, full_a7 PROVEN) |
| CHK-016 | Readies are 1 from R1 | **PROVEN** | (base PROVEN, min PROVEN, max PROVEN, full_a7 PROVEN) |
| CHK-017 | Outputs change only at a rising edge of i_clk or at reset assertion | **UNSUPPORTED** | a_CHK_017: checker nnc_chk_timing is simulation-only: simulation time (`time`) (base UNSUPPORTED, min UNSUPPORTED, max UNSUPPORTED, full_a7 UNSUPPORTED) |

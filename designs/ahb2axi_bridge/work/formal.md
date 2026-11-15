# Formal check — ahb2axi_bridge

SymbiYosys on the generated assertions, translated to immediate form by `nnc/formal.py`. Depth 20 cycles, one global clock, environment: reset assumptions + verif/formal/nnc_env.sv, defines VLSIT_SYNTHESIS.

- **PROVEN**: holds in every reachable state (k-induction).
- **BOUNDED**: no counterexample within 20 cycles from reset; induction inconclusive.
- **CEX**: a counterexample exists. Either a design bug, or an input sequence the environment should forbid (a missing assumption). The trace (VCD) shows which.
- **VACUOUS**: the antecedent cannot occur within the depth under the assumptions: the environment is too strict (or the condition is unreachable); the other results say nothing.
- **UNSUPPORTED**: the assertion uses SVA outside the translated subset, or its checker is simulation-only (event timing, queues); not checked.
- **TIMEOUT**: the solver did not finish within 600 s per task; nothing concluded.

**Result:** {'BOUNDED': 2, 'CEX': 9, 'PROVEN': 8, 'VACUOUS': 1}

Configurations (parameters of the run set; a check counts as PROVEN only if proven in every configuration where it is not vacuous):

- base: {'BOUNDED': 2, 'CEX': 9, 'PROVEN': 8, 'VACUOUS': 1}
- ids8: {'BOUNDED': 2, 'CEX': 9, 'PROVEN': 8, 'VACUOUS': 1}
- ids35: {'BOUNDED': 2, 'CEX': 9, 'PROVEN': 8, 'VACUOUS': 1}

| Check | Title | Formal | Detail |
|---|---|---|---|
| CHK-001 | AHB ERROR is a two-cycle response | **CEX** | trace: work/formal/CHK-001_base.vcd (base CEX, ids8 CEX, ids35 CEX) |
| CHK-002 | IDLE and BUSY transfers get zero-wait OKAY | **CEX** | trace: work/formal/CHK-002_base.vcd (base CEX, ids8 CEX, ids35 CEX) |
| CHK-003 | AXI lock outputs tied low | **PROVEN** | (base PROVEN, ids8 PROVEN, ids35 PROVEN) |
| CHK-004 | Reads are always single-beat INCR | **PROVEN** | (base PROVEN, ids8 PROVEN, ids35 PROVEN) |
| CHK-005 | AW VALID and payload stable until AWREADY | **CEX** | trace: work/formal/CHK-005_base.vcd (base CEX, ids8 CEX, ids35 CEX) |
| CHK-006 | W VALID and payload stable until WREADY | **PROVEN** | (base PROVEN, ids8 PROVEN, ids35 PROVEN) |
| CHK-007 | AR VALID and payload stable until ARREADY | **PROVEN** | (base PROVEN, ids8 PROVEN, ids35 PROVEN) |
| CHK-008 | At most one outstanding read and one outstanding write | **PROVEN** | (base PROVEN, ids8 PROVEN, ids35 PROVEN) |
| CHK-009 | AXI IDs stay below the configured ID count | **PROVEN** | (base PROVEN, ids8 PROVEN, ids35 PROVEN) |
| CHK-010 | W beat count and WLAST match AWLEN | **BOUNDED** | (base BOUNDED, ids8 BOUNDED, ids35 BOUNDED) |
| CHK-011 | AW burst shape is legal and never crosses 4 KiB | **CEX** | trace: work/formal/CHK-011_base.vcd (base CEX, ids8 CEX, ids35 CEX) |
| CHK-012 | Issued AXI requests use supported sizes and are aligned | **CEX** | trace: work/formal/CHK-012_base.vcd (base CEX, ids8 CEX, ids35 CEX) |
| CHK-013 | No AR before the matching AHB read is accepted | **BOUNDED** | (base BOUNDED, ids8 BOUNDED, ids35 BOUNDED) |
| CHK-014 | No AXI write burst before the full AHB fixed burst is accepted | **VACUOUS** | (base VACUOUS, ids8 VACUOUS, ids35 VACUOUS) |
| CHK-015 | AHB read completes only with its R beat and carries RDATA unchanged | **CEX** | trace: work/formal/CHK-015_base.vcd (base CEX, ids8 CEX, ids35 CEX) |
| CHK-016 | Waiting-class writes complete only after their BRESP | **CEX** | trace: work/formal/CHK-016_base.vcd (base CEX, ids8 CEX, ids35 CEX) |
| CHK-017 | Locally rejected transfers end in ERROR and produce no W data | **CEX** | trace: work/formal/CHK-017_base.vcd (base CEX, ids8 CEX, ids35 CEX) |
| CHK-018 | AHB outputs hold reset values during reset | **PROVEN** | (base PROVEN, ids8 PROVEN, ids35 PROVEN) |
| CHK-019 | AXI VALID/READY outputs suppressed during reset | **PROVEN** | (base PROVEN, ids8 PROVEN, ids35 PROVEN) |
| CHK-020 | AXI payload outputs hold reset values during reset | **CEX** | trace: work/formal/CHK-020_base.vcd (base CEX, ids8 CEX, ids35 CEX) |

# Formal check — async_apb_bridge

SymbiYosys on the generated assertions, translated to immediate form by `nnc/formal.py`. Depth 20 cycles, multiclock (free clocks), environment: reset assumptions + verif/formal/nnc_env.sv, defines VLSIT_SYNTHESIS.

- **PROVEN**: holds in every reachable state (k-induction).
- **BOUNDED**: no counterexample within 20 cycles from reset; induction inconclusive.
- **CEX**: a counterexample exists. Either a design bug, or an input sequence the environment should forbid (a missing assumption). The trace (VCD) shows which.
- **VACUOUS**: the antecedent cannot occur within the depth under the assumptions: the environment is too strict (or the condition is unreachable); the other results say nothing.
- **UNSUPPORTED**: the assertion uses SVA outside the translated subset, or its checker is simulation-only (event timing, queues); not checked.
- **TIMEOUT**: the solver did not finish within 600 s per task; nothing concluded.

**Result:** {'PROVEN': 15, 'UNSUPPORTED': 3}

Configurations (parameters of the run set; a check counts as PROVEN only if proven in every configuration where it is not vacuous):

- apb4: {'PROVEN': 15, 'UNSUPPORTED': 3}
- 4ph: {'PROVEN': 11, 'UNSUPPORTED': 3, 'VACUOUS': 4}
- apb5: {'PROVEN': 15, 'UNSUPPORTED': 3}
- user: {'PROVEN': 15, 'UNSUPPORTED': 3}
- sync3: {'PROVEN': 11, 'UNSUPPORTED': 3, 'VACUOUS': 4}
- sync4: {'PROVEN': 11, 'UNSUPPORTED': 3, 'VACUOUS': 4}
- min: {'PROVEN': 15, 'UNSUPPORTED': 3}

| Check | Title | Formal | Detail |
|---|---|---|---|
| CHK-001 | Absent APB5 signals drive zero | **PROVEN** | (apb4 PROVEN, 4ph PROVEN, apb5 PROVEN, user PROVEN, sync3 PROVEN, sync4 PROVEN, min PROVEN) |
| CHK-002 | Outputs change only at their own clock edge or on reset assertion | **UNSUPPORTED** | a_CHK_002: checker nnc_chk_glitch is simulation-only: simulation time (`time`); a_CHK_002_slv: checker nnc_chk_glitch is simulation-only: simulation time (`time`) (apb4 UNSUPPORTED, 4ph UNSUPPORTED, a |
| CHK-003 | Requester-side PREADY only in an Access cycle | **PROVEN** | (apb4 PROVEN, 4ph VACUOUS, apb5 PROVEN, user PROVEN, sync3 VACUOUS, sync4 VACUOUS, min PROVEN) |
| CHK-004 | Requester-side PREADY is a one-cycle pulse | **PROVEN** | (apb4 PROVEN, 4ph VACUOUS, apb5 PROVEN, user PROVEN, sync3 VACUOUS, sync4 VACUOUS, min PROVEN) |
| CHK-005 | PSLVERR only in the PREADY cycle (no sticky error) | **PROVEN** | (apb4 PROVEN, 4ph VACUOUS, apb5 PROVEN, user PROVEN, sync3 VACUOUS, sync4 VACUOUS, min PROVEN) |
| CHK-006 | At most one PREADY per accepted Setup phase | **PROVEN** | (apb4 PROVEN, 4ph VACUOUS, apb5 PROVEN, user PROVEN, sync3 VACUOUS, sync4 VACUOUS, min PROVEN) |
| CHK-007 | Response outputs stable outside the PREADY cycle | **PROVEN** | (apb4 PROVEN, 4ph PROVEN, apb5 PROVEN, user PROVEN, sync3 PROVEN, sync4 PROVEN, min PROVEN) |
| CHK-008 | No unknown requester-side outputs after reset | **PROVEN** | (apb4 PROVEN, 4ph PROVEN, apb5 PROVEN, user PROVEN, sync3 PROVEN, sync4 PROVEN, min PROVEN) |
| CHK-009 | Requester-side outputs at reset value while i_rst_n_mst is low | **UNSUPPORTED** | a_CHK_009: checker nnc_chk_rst is simulation-only: delays (`#1`) (apb4 UNSUPPORTED, 4ph UNSUPPORTED, apb5 UNSUPPORTED, user UNSUPPORTED, sync3 UNSUPPORTED, sync4 UNSUPPORTED, min UNSUPPORTED) |
| CHK-010 | Completer-side outputs at reset value while i_rst_n_slv is low | **UNSUPPORTED** | a_CHK_010: checker nnc_chk_rst is simulation-only: delays (`#1`) (apb4 UNSUPPORTED, 4ph UNSUPPORTED, apb5 UNSUPPORTED, user UNSUPPORTED, sync3 UNSUPPORTED, sync4 UNSUPPORTED, min UNSUPPORTED) |
| CHK-011 | No unknown completer-side outputs after reset | **PROVEN** | (apb4 PROVEN, 4ph PROVEN, apb5 PROVEN, user PROVEN, sync3 PROVEN, sync4 PROVEN, min PROVEN) |
| CHK-012 | Completer-side PENABLE implies PSEL; PSEL rises in a Setup cycle | **PROVEN** | (apb4 PROVEN, 4ph PROVEN, apb5 PROVEN, user PROVEN, sync3 PROVEN, sync4 PROVEN, min PROVEN) |
| CHK-013 | Completer-side Setup phase lasts exactly one cycle | **PROVEN** | (apb4 PROVEN, 4ph PROVEN, apb5 PROVEN, user PROVEN, sync3 PROVEN, sync4 PROVEN, min PROVEN) |
| CHK-014 | Access phase held while the completer is not ready (no timeout) | **PROVEN** | (apb4 PROVEN, 4ph PROVEN, apb5 PROVEN, user PROVEN, sync3 PROVEN, sync4 PROVEN, min PROVEN) |
| CHK-015 | Completer-side transfer ends at the PREADY edge | **PROVEN** | (apb4 PROVEN, 4ph PROVEN, apb5 PROVEN, user PROVEN, sync3 PROVEN, sync4 PROVEN, min PROVEN) |
| CHK-016 | Completer-side request fields stable during a transfer | **PROVEN** | (apb4 PROVEN, 4ph PROVEN, apb5 PROVEN, user PROVEN, sync3 PROVEN, sync4 PROVEN, min PROVEN) |
| CHK-017 | Completer-side request fields loaded only at Setup entry | **PROVEN** | (apb4 PROVEN, 4ph PROVEN, apb5 PROVEN, user PROVEN, sync3 PROVEN, sync4 PROVEN, min PROVEN) |
| CHK-018 | APB5 o_apb_pwakeup high no later than o_apb_psel and until completion | **PROVEN** | (apb4 PROVEN, 4ph PROVEN, apb5 PROVEN, user PROVEN, sync3 PROVEN, sync4 PROVEN, min PROVEN) |

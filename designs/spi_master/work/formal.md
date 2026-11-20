# Formal check — spi_master

SymbiYosys on the generated assertions, translated to immediate form by `nnc/formal.py`. Depth 32 cycles, one global clock, environment: reset assumptions + verif/formal/nnc_env.sv. A check VACUOUS at that depth was run again alone at twice the depth, up to 128 cycles (its row gives the depth used).

- **PROVEN**: holds in every reachable state (k-induction).
- **BOUNDED**: no counterexample within 32 cycles from reset; induction inconclusive.
- **CEX**: a counterexample exists. Either a design bug, or an input sequence the environment should forbid (a missing assumption). The trace (VCD) shows which.
- **VACUOUS**: the antecedent cannot occur within the depth under the assumptions: the environment is too strict (or the condition is unreachable); the other results say nothing.
- **UNSUPPORTED**: the assertion uses SVA outside the translated subset, or its checker is simulation-only (event timing, queues); not checked.
- **TIMEOUT**: the solver did not finish within 600 s per task; nothing concluded.

**Result:** {'BOUNDED': 7, 'PROVEN': 6, 'UNSUPPORTED': 14}

Configurations (parameters of the run set; a check counts as PROVEN only if proven in every configuration where it is not vacuous):

- base: {'PROVEN': 13, 'UNSUPPORTED': 14}
- min: {'PROVEN': 13, 'UNSUPPORTED': 14}
- max: {'BOUNDED': 7, 'PROVEN': 3, 'UNSUPPORTED': 14, 'VACUOUS': 3}

| Check | Title | Formal | Detail |
|---|---|---|---|
| CHK-001 | o_cmd_ready changes only at clock edges or reset assertion | **UNSUPPORTED** | a_CHK_001: checker nnc_chk_cmd is simulation-only: simulation time (`$time`) (base UNSUPPORTED, min UNSUPPORTED, max UNSUPPORTED) |
| CHK-002 | o_cmd_ready low while a response is shown | **UNSUPPORTED** | a_CHK_002: checker nnc_chk_cmd is simulation-only: simulation time (`$time`) (base UNSUPPORTED, min UNSUPPORTED, max UNSUPPORTED) |
| CHK-003 | o_cmd_ready in Idle after o_cs_n rise (blocked D-1 cycles) | **UNSUPPORTED** | a_CHK_003: checker nnc_chk_cmd is simulation-only: simulation time (`$time`) (base UNSUPPORTED, min UNSUPPORTED, max UNSUPPORTED) |
| CHK-004 | o_cmd_ready during a transfer and in its last cycle | **UNSUPPORTED** | a_CHK_004: checker nnc_chk_cmd is simulation-only: simulation time (`$time`) (base UNSUPPORTED, min UNSUPPORTED, max UNSUPPORTED) |
| CHK-005 | o_cmd_ready in Pause and Trail | **UNSUPPORTED** | a_CHK_005: checker nnc_chk_cmd is simulation-only: simulation time (`$time`) (base UNSUPPORTED, min UNSUPPORTED, max UNSUPPORTED) |
| CHK-006 | o_cs_n falls exactly at a burst-start handshake | **PROVEN** | (base PROVEN, min PROVEN, max PROVEN) |
| CHK-007 | o_cs_n low for whole burst, rises at A_last+17D only | **BOUNDED** | (base PROVEN, min PROVEN, max BOUNDED) |
| CHK-008 | Minimum o_cs_n high gap between bursts | **PROVEN** | [depth 128] (base PROVEN, min PROVEN, max VACUOUS) |
| CHK-009 | Lead time: first SCLK edge D cycles after o_cs_n falls | **PROVEN** | (base PROVEN, min PROVEN, max PROVEN) |
| CHK-010 | Pause entry and Pause outputs | **PROVEN** | [depth 128] (base PROVEN, min PROVEN, max VACUOUS) |
| CHK-011 | MOSI shift timing, CPHA_b=0 | **BOUNDED** | (base PROVEN, min PROVEN, max BOUNDED) |
| CHK-012 | MOSI shift timing, CPHA_b=1 | **BOUNDED** | (base PROVEN, min PROVEN, max BOUNDED) |
| CHK-013 | o_mosi changes only at shift edges; holds in Idle/Pause/Trail | **BOUNDED** | (base PROVEN, min PROVEN, max BOUNDED) |
| CHK-014 | o_mosi stable at every sampling edge | **PROVEN** | (base PROVEN, min PROVEN, max VACUOUS) |
| CHK-015 | Outputs take reset values at once on i_rst_n assertion | **UNSUPPORTED** | a_CHK_015_procedural: checker nnc_chk_reset is simulation-only: simulation time (`$realtime`) (base UNSUPPORTED, min UNSUPPORTED, max UNSUPPORTED) |
| CHK-016 | Output values held while in reset | **UNSUPPORTED** | a_CHK_016_procedural: checker nnc_chk_reset is simulation-only: simulation time (`$realtime`) (base UNSUPPORTED, min UNSUPPORTED, max UNSUPPORTED) |
| CHK-017 | o_sclk follows i_cpol combinationally during reset | **UNSUPPORTED** | a_CHK_017_procedural: checker nnc_chk_reset is simulation-only: simulation time (`$realtime`) (base UNSUPPORTED, min UNSUPPORTED, max UNSUPPORTED) |
| CHK-018 | Ready to accept at first edge after reset release | **UNSUPPORTED** | a_CHK_018: checker nnc_chk_reset is simulation-only: simulation time (`$realtime`) (base UNSUPPORTED, min UNSUPPORTED, max UNSUPPORTED) |
| CHK-019 | Response outputs change only at clock edges or reset | **UNSUPPORTED** | a_CHK_019: checker nnc_chk_rsp is simulation-only: event-triggered blocks (`always @(`) (base UNSUPPORTED, min UNSUPPORTED, max UNSUPPORTED) |
| CHK-020 | Response reference model: data, order, timing, depth<=2 | **UNSUPPORTED** | a_CHK_020: checker nnc_chk_rsp is simulation-only: event-triggered blocks (`always @(`) (base UNSUPPORTED, min UNSUPPORTED, max UNSUPPORTED) |
| CHK-021 | o_rsp_data hold and i_rsp_ready ignored while not valid | **UNSUPPORTED** | a_CHK_021: checker nnc_chk_rsp is simulation-only: event-triggered blocks (`always @(`) (base UNSUPPORTED, min UNSUPPORTED, max UNSUPPORTED) |
| CHK-022 | No transfer starts while a byte is shown or held | **UNSUPPORTED** | a_CHK_022: checker nnc_chk_rsp is simulation-only: event-triggered blocks (`always @(`) (base UNSUPPORTED, min UNSUPPORTED, max UNSUPPORTED) |
| CHK-023 | SCLK edges at A+k*D with correct levels | **BOUNDED** | (base PROVEN, min PROVEN, max BOUNDED) |
| CHK-024 | No other o_sclk changes while o_cs_n=0 | **BOUNDED** | (base PROVEN, min PROVEN, max BOUNDED) |
| CHK-025 | SCLK at CPOL_b in lead, Pause and Trail | **BOUNDED** | (base PROVEN, min PROVEN, max BOUNDED) |
| CHK-026 | o_sclk equals i_cpol while o_cs_n=1 | **PROVEN** | (base PROVEN, min PROVEN, max PROVEN) |
| CHK-027 | No-gap joint between back-to-back transfers | **UNSUPPORTED** | a_CHK_027: a delay inside parentheses (nested sequence) (base UNSUPPORTED, min UNSUPPORTED, max UNSUPPORTED) |

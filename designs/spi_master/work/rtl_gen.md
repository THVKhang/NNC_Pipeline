# RTL generation report: spi_master

Status: **clean** after 2 attempt(s) (agent A15, opus, rtl-v1); cost US$0.93.
Remaining findings: 0 errors, 0 warnings, 1 notes.

This report is the material of gate **D2_rtl**. The code checks below say nothing about whether the RTL is *correct*: the verification (G3/G4), generated independently of this RTL, decides that.

## Synthesis (estimates, RR-43)

| Corner | Library | Cell area (um^2) | Longest combinational path (ps) |
|---|---|---|---|
| tt | gf180mcu_fd_sc_mcu7t5v0__tt_025C_5v00.lib | 8462.496 | 5084.84 |
| ss | gf180mcu_fd_sc_mcu7t5v0__ss_125C_4v50.lib | 8581.0368 | 10751.3 |

Generic cells: 248. Delay is ABC's estimate without wires, clock-to-output or setup time: a comparison figure, not a timing sign-off.

## Traceability (RR-42)

Rules tagged in the RTL: 167 of 206 (81.1 %). A rule may be untagged because it is about the environment, the documentation or verification, not the RTL; the reviewer checks the list.

<details><summary>Untagged rules</summary>

SPI-11-01, SPI-11-02, SPI-11-03, SPI-12-01, SPI-12-02, SPI-12-03, SPI-12-04, SPI-12-05, SPI-12-06, SPI-12-07, SPI-12-08, SPI-12-09, SPI-12-10, SPI-12-12, SPI-12-13, SPI-12-15, SPI-12-16, SPI-12-17, SPI-12-18, SPI-12-19, SPI-12-20, SPI-12-21, SPI-12-22, SPI-12-23, SPI-12-24, SPI-12-25, SPI-12-26, SPI-12-27, SPI-12-28, SPI-12-29, SPI-12-30, SPI-12-31, SPI-12-32, SPI-13-01, SPI-13-02, SPI-13-12, SPI-5-02, SPI-8-10, SPI-8-11

</details>

## Open points stated by the agent

- RR-40 fix: r_cpol_b (CPOL_b, captured at the first acceptance edge of a burst) is now used to drive the internal SCLK. At every SCLK edge k, r_sclk is loaded with NOT CPOL_b for odd k and CPOL_b for even k (SPI-7.4-04), instead of being toggled. The behaviour is the same as before, but the level is now forced from CPOL_b at each edge rather than built up from a chain of toggles. At burst start r_sclk is still loaded from i_cpol at the acceptance edge, which is the same value captured into CPOL_b (sections 7.3 and 7.4).
- Section 4 / REQ-PAR-001 (SPI-4-03): the elaboration error for an illegal PARA_SPI_CLK_DIV is a generate-time $error inside `ifndef SYNTHESIS`, because RR-11 forbids system tasks in checked code. Simulators and lint tools (Verilator) stop elaboration. Yosys defines SYNTHESIS, so synthesis on its own does not reject an illegal value. Section 12 says this check is done by elaborating once, not by simulation, so I took the elaboration tool to be the one that enforces it.
- Section 13 / REQ-IMP-005/006: o_sclk is built as the hazard-free form (cs_n & i_cpol) | (~cs_n & r_sclk) | (i_cpol & r_sclk). The extra term i_cpol & r_sclk is there only to avoid a glitch. It cannot change o_sclk while o_cs_n = 0, so logically the only path from i_cpol is the one used while o_cs_n = 1. Synthesis may remove this term, which would undo the glitch protection; gate-level glitch checks are out of scope (section 1.3).
- Section 6.2 / ENV-007: if reset is asserted exactly at an i_clk edge, the result is not defined. The spec says this is not a legal case, so the RTL does nothing special for it.
- Section 7.7: the held-byte register is checked only on the response handshake. At SCLK edge 16 a byte is never already held, because a held byte keeps o_rsp_valid = 1, which blocks the start of any transfer (REQ-CMD-006, REQ-FLOW-007). So the RTL has no separate path for 'held byte present at SCLK edge 16'.

## Findings

| Severity | Rule | Where | Message |
|---|---|---|---|
| info | RR-10 | m_spi_master.sv:47 | simulation-only code (not under SYNTHESIS): not synthesized; reviewer: check it models only what the specification asks for |

## Attempts

- 0: {'error': 0, 'warning': 1, 'info': 1} (changed m_spi_master.sv)
- 1: {'error': 0, 'warning': 0, 'info': 1} (changed m_spi_master.sv)

## For the reviewer of D2_rtl (rules checked by a person)

- RR-03 file headers; RR-24 state machines; RR-32 reset values; RR-33 clock-domain crossings;
  RR-41 widths written with parameters; RR-44 names (docs/RTL_RULES.md).
- The open points above: is each reading the one the specification intends?
- Then: `nnc gate approve spi_master D2_rtl --by "<name>" --note "..."`.

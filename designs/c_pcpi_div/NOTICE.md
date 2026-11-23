# Third-party material / Tài liệu của bên thứ ba

Phase 21.6 of docs/ROADMAP.md: a blind end-to-end run of the flow on a module of the input corpus. Only the documentation of the source repository (and, for the standard it names, the public specification) is given to the flow. Every intervention is recorded in `work/blind_run.md`.

**RTL**: [picorv32](https://github.com/YosysHQ/picorv32), commit `ef203c2b0a3fb793280f5114941416c425c5b461`, licence ISC (`LICENSE-ISC`). Copied unchanged:

| File | Path in the source | SHA-256 |
|---|---|---|
| `rtl/picorv32.v` | `picorv32.v` | `fd142889e8178ef67f1cff17cb2d18b3adae56fcae2badf7cbcc4c4f5ac7960e` |

**Specification**: `spec/c_pcpi_div_Design_Specification.md`: Excerpt of README.md, verbatim: lines 84-87, 97-112, 268-272 and 452-485 (the PCPI sentences of the introduction, the module table of picorv32.v, ENABLE_DIV and the PCPI section), under a title line written for NNC Pipeline. The text is unchanged; the first line is a comment naming the source.

**Standards**:

| File | Source | Licence |
|---|---|---|
| `spec/standards/riscv_m_extension.adoc` | [riscv/riscv-isa-manual](https://github.com/riscv/riscv-isa-manual), commit `3142f66fd71c7ea0326b3687072318aedab587f8`: `src/unpriv/m-st-ext.adoc`, unchanged (it includes the two wavedrom files below) | CC-BY-4.0 (`LICENSE-CC-BY-4.0`) |
| `spec/standards/riscv_rv32m_listing.adoc` | Same commit: `src/unpriv/rv-32-64g.adoc`, excerpt (lines 1-58 and 152-165, verbatim) | CC-BY-4.0 (`LICENSE-CC-BY-4.0`) |

The RISC-V Instruction Set Manual, © RISC-V International, licensed under the Creative Commons Attribution 4.0 International License (https://creativecommons.org/licenses/by/4.0/). Changes: the listing file is an excerpt (lines named in its first comment); nothing else is changed.
`spec/standards/images/wavedrom/division-op.edn` and `m-st-ext-for-int-mult.edn`: same commit, `src/unpriv/images/wavedrom/`, unchanged.

## Verification fixes by agent A17 (nnc fix-verif, 2026-11-23, applied by Claude (delegated by GabrielHCMUT))

- `verif/tests/test_c_pcpi_div.py`: NNC verification fix (fix-verif, triage B): execute() drove pcpi_valid=1 in the same mid-cycle where the previous deassert (or the last idle cycle) had just driven pcpi_valid=0. That overwrote the 0, so with gap=0 no rising edge ever saw pcpi_valid=0 between two instructions. The test's own model still recorded valid=0, so it missed this. The contract says the master deasserts pcpi_valid on the cycle after pcpi_ready, so this stimulus was illegal and set off the CHK-001 failures. The fix waits one clock cycle (await next_cycle) at the start of execute() before driving the issue. Now the pcpi_valid=0 that was already driven and checked is really sampled at a rising edge, so every instruction is preceded by at least one pcpi_valid=0 edge. CHK-001 in the SVA, the cover points and all expected values are unchanged. (contract.json:223 (CHK-008 stimulus: 'then drive pcpi_valid=0 on the next cycle'), contract.json:327 ('Legal master stimulus ... deasserts pcpi_valid on the following cycle'), spec/c_pcpi_div_Design_Specification.md:62-66 (PD-T1.1-06: keep pcpi_wait asserted until pcpi_ready), spec/c_pcpi_div_Design_Specification.md:48-52 (PD-T1.1-01))

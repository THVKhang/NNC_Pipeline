# Blind run: c_pcpi_div (ROADMAP 21.6, 2026-11-23)

The flow on a module it was not written for: `picorv32_pcpi_div` of
[picorv32](https://github.com/YosysHQ/picorv32) (commit `ef203c2b0a`, ISC). The specification is the documentation a
user of this core has: the PCPI sections of the README, and the RISC-V standard it implements (the M extension
chapter and the RV32M encodings of the RISC-V Instruction Set Manual, CC-BY-4.0). Agents: Claude Code, default
models. Nothing in `rtl/`, `verif/` or the records was edited by hand.

## Every intervention

| Step | Intervention | By |
|---|---|---|
| Inputs | README excerpt: the PCPI sentences, the module table, ENABLE_DIV and the PCPI section (lines in `NOTICE.md`). Standards: `m-st-ext.adoc` unchanged; the RV32M part of the listing chapter. | Claude (delegated) |
| Intake | Verdict *adapt*: no port table. `nnc adapt` wrote `spec/picorv32_pcpi_div_interface.md`. | code, no choice |
| G1 | Approved as produced: 23 rules kept, 5 rejected. The 4 open questions were left open. | Claude (delegated) |
| G2 | Approved as produced: 9 checks; 16 rules not verified (CPU side of PCPI, multiplication, RV64, software guidelines). Assumptions recorded: RV32M encodings from the listing, result valid with `pcpi_ready`, a 200-cycle completion bound. | Claude (delegated) |
| G3 | Approved as generated: 7 tests, 3 checker groups, 35 cover points. | Claude (delegated) |
| Triage | 1 failure, judged B (the test). The test issued the next instruction without the one cycle of `pcpi_valid` = 0 the contract requires. A17 (no RTL) added that cycle; the weakening check found nothing. Applied, G3 approved again. | Claude (delegated) |

Defaults kept: formal off, no coverage target.

## Outcome

- Tests 7/7 pass; checks 9/9 PASS; 7 rules verified; line, block, expression and toggle coverage 100 %; functional
  85.7 % (30/35); mutation 100 % (12/12).
- Division by zero, signed overflow, rounding toward zero and the sign of the remainder come from the RISC-V
  standard, not from the README, and they are verified against it.
- Agent cost: US$2.66 (US$1.66 in the records, plus US$1.00 for the first triage, whose record the second run
  replaced).

# Blind run: c_uart (ROADMAP 21.6, 2026-11-23)

The flow on a module it was not written for: `uart` of [verilog-uart](https://github.com/alexforencich/verilog-uart)
(commit `1b867e53af`, MIT), with the repository's README as the only specification. Agents: Claude Code, default
models. Nothing in `rtl/`, `verif/` or the records was edited by hand.

## Every intervention

| Step | Intervention | By |
|---|---|---|
| Inputs | The whole README.md is the IP specification (no choice of sections). | Claude (delegated) |
| Intake | Verdict *adapt*: the README has no port table. `nnc adapt` wrote `spec/uart_interface.md` from the port declarations. | code, no choice |
| G1 | Approved as produced: 6 rules kept, 4 rejected. The open question (which word an overrun discards; the busy window) was left open. | Claude (delegated) |
| G2 | Approved as produced: 11 checks. The contract **assumes** an 8N1 frame and a bit period of 8 × prescale cycles: the README states no frame format. | Claude (delegated) |
| G3 | Approved as generated: 8 tests, 4 checker groups, 40 cover points, lint clean. | Claude (delegated) |
| Triage | 4 failures, all judged C (the specification is unclear). Kept open, as the owner decided: nothing changed. | the owner |

Defaults kept: formal off, no coverage target.

## Outcome

- Tests 5/8 pass; checks 6/11 PASS; line coverage 97.6 %; mutation 83.3 % (10/12).
- The failures are one behaviour of the RTL that the README leaves open. When a received word is still waiting on
  `m_axis` (tvalid = 1, tready = 0) and another word arrives, the RTL **replaces** the waiting word and pulses
  `overrun_error`. The README says only that "the word is discarded". Keeping the waiting word stable is the
  AXI4-Stream rule (CHK-001), so the checks fail. A second failure: after a frame whose stop bit is 0, the README
  does not say what the receiver does next. These are for the G4 reviewer (`work/triage.md`).
- Agent cost: US$2.70.

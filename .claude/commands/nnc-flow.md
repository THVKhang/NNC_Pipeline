---
description: Run the NNC verification flow on a design and stop at each review gate
argument-hint: <design> [--from <stage>]
---

# /nnc-flow — gated RTL verification flow

Run the NNC Pipeline on the design `$ARGUMENTS` and guide the user through its review gates. The
orchestrator is the Python CLI; you run it, read what it writes, and present each gate. You never
approve a gate yourself.

## Steps

1. `python -m nnc status <design>` — show configuration, documents and gate states. If no design or
   documents exist, explain `nnc init <design> --top <module>` and `nnc doc add` (role `ip_spec` once,
   `standard` for each protocol document) with an example, then stop.
2. `python -m nnc flow <design> [--from <stage>]` — runs ingest → extract → review and stops at the
   first gate that is not approved. Report each `[stage]` line in one sentence each.
3. At a gate, read the review sheet and present it:
   - **G1_rules** → `work/rules.md`: counts, every *open question* (verbatim, with rule IDs), the
     rejected rules, and 5–10 representative rules. Ask the user to answer the open questions or to
     accept them as open.
   - **G2_contract** → `work/contract.md`: interface, each check (ID, kind, title), the rules declared
     not verifiable and the assumptions.
   - **G3_verif_sources** → `verif/sva/*.sv` and `verif/tests/*.py`, and `work/gen_sva.json`,
     `work/gen_tests.json` (lint status, attempts).
   - **G4_signoff** → `work/report.md` and `work/triage.md`.
   Then ask for a decision with options, effects and a recommendation, for example:
   > 1. Approve G1 as is — the contract will be built from these 232 rules. (Recommended if the open
   >    questions do not change expected behaviour.)
   > 2. Answer the open questions first — I record each answer with
   >    `python -m nnc answer <design> <n> "<decision>" --by "<their name>"`; the contract agent receives them.
   > 3. Reject rules — tell me the IDs; I re-run review after you edit the specification.
4. Only after the user explicitly approves: `python -m nnc gate approve <design> <gate> --by "<their name>"`
   and continue with `python -m nnc flow <design> --from <next stage>`.
5. After `sim`: if `work/triage.md` lists failures, present each analysis (failure, spec says, RTL
   does, test does, candidates A/B/C, options) and wait for the designer's decision. Never change the
   RTL, a test, an assertion or an expected value to make a run pass.

## Rules

- Report only what the files and command outputs show. A missing tool means NOT_RUN, never pass.
- `--unreviewed` runs past gates for exploration only; say so, and say that its report cannot be
  signed off.
- Agent calls use the user's Claude Code quota; mention the cost lines the CLI prints.
- Do not read files under `rtl/` when discussing checks or tests (the oracle comes from the
  specification); reading the RTL is for triage only.

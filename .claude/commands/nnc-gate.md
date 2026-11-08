---
description: Present one NNC review gate (rules, contract, verification sources or sign-off) for decision
argument-hint: <design> <G1_rules|G2_contract|G3_verif_sources|G4_signoff>
---

# /nnc-gate — present a review gate

Arguments: `$ARGUMENTS` (design and gate).

1. Run `python -m nnc status <design>` and confirm the gate is PENDING or STALE (if STALE, say which
   artifact changed since the approval).
2. Read the review sheet of the gate (G1 `work/rules.md`, G2 `work/contract.md` and the test-plan
   selection (`python -m nnc plan <design>`), G3 `verif/` (checkers, `nnc_cov.sv`, test modules incl.
   closure modules) and `work/gen_*.json`, G4 the *Sign-off conditions* table of `work/report.md`, then
   `work/triage.md`, `work/coverage.md` and the per-rule mutation scores).
3. Summarise for a design engineer: what will be fixed by approving, what is still open, what the
   flow could not verify and why. Quote rule and check IDs.
4. Ask for the decision with numbered options, the effect of each and a recommendation.
5. Approve only on the user's explicit words, with their name:
   `python -m nnc gate approve <design> <gate> --by "<name>" --note "<their reason>"`.

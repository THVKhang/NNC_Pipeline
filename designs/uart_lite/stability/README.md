# Stability of the agents on uart_lite (phase 18, 2026-11-21)

**Question.** If the flow runs again on the same specification, does it extract the same rules and plan the same
checks?

**Method.** Three fresh copies of uart_lite were made: the same specification and the same document
configuration, an empty `work/` folder and no agent cache. Each copy ran

    nnc flow uart_lite_rN --from ingest --to contract --unreviewed

This covers ingest, extraction (A1), review (A2), questions (A3) and contract (A4). It ran with the same
models as the committed run, and the open questions were not answered. The committed `designs/uart_lite`
(answered questions, approved gates) is the fourth run. The folders `r1`, `r2` and `r3` keep only what the
comparison reads: `rules.json`, `contract.json` and the sentence index `spec/*.index.json`.

`nnc stability` (nnc/stability.py) compares the runs through the specification sentences that the rules cite,
because each run chooses its own rule and check IDs. Results are in [stability.md](stability.md) and
`stability.json`.

To reproduce the comparison:

    nnc stability designs/uart_lite/stability/r1 designs/uart_lite/stability/r2 designs/uart_lite/stability/r3 designs/uart_lite

**Cost.** About US$5.2 for the three runs: US$1.98, US$1.63 and US$1.56 (extract, review with questions, contract).

**Result.**

| Measure | Range over the 6 pairs |
|---|---|
| Normative sentences kept, Jaccard | 0.91–0.95 |
| Normative sentences covered by a check, Jaccard | 0.86–0.93 |
| All cited sentences kept, Jaccard | 0.77–0.90 |
| Kept rules whose exact sentence set is a rule in the other run | 0.81–0.93 |
| Same strongest strength (MUST/SHOULD/MAY) per sentence | 0.99–1.00 |
| Rules / checks per run | 134–154 rules, 32–34 checks (12–13 assertions) |

What this means:
- Each run keeps 105 to 108 of the 114 normative sentences. The runs agree on more than 9 in 10 of them.
- The runs differ more on which sentences a check covers: 86 to 92 normative sentences per run, with pairwise
  agreement of 0.86 to 0.93.
- About 1 kept rule in 6 is cut differently: the same sentences are grouped into other rules.
- The runs never disagree on the strength of a sentence. In one pair, one sentence in a hundred differs.

The variation is the reason for gate G1 (rules) and gate G2 (contract). A person reviews what this run
produced; nothing assumes that another run would produce the same.

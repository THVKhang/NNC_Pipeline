"""How much do repeated agent runs on the same specification agree? (`nnc stability`, phase 18, no agent)

Rules and checks carry IDs that each run chooses itself, so they are compared through what does not depend on
the run: the specification sentences they cite (`sentences` of a rule, e.g. "7.1:s3").

    sentences kept     sentences cited by the rules the review kept (verdict keep or merge)
    sentences checked  sentences cited by the rules that some check of the contract covers
    rule match         a kept rule of run A whose sentence set is exactly the sentence set of a kept rule of run B
    strength           for each sentence kept in both runs, whether the strongest MUST/SHOULD/MAY citing it is equal

Agreement of two sets is the Jaccard index |A ∩ B| / |A ∪ B|. Every pair of runs is compared.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

ORDER = {"MUST": 3, "MUST_NOT": 3, "SHALL": 3, "SHOULD": 2, "SHOULD_NOT": 2, "MAY": 1}


def _kept(rules: list[dict]) -> list[dict]:
    return [r for r in rules if (r.get("review") or {}).get("verdict", "keep") in ("keep", "merge")]


def summary(work: Path) -> dict:
    rules = json.loads((work / "rules.json").read_text(encoding="utf-8"))["rules"]
    kept = _kept(rules)
    contract = json.loads((work / "contract.json").read_text(encoding="utf-8")) \
        if (work / "contract.json").is_file() else {"checks": []}
    by_id = {r["id"]: r for r in kept}
    checked_rules = {rid for c in contract["checks"] for rid in c.get("rules", [])}
    strength: dict[str, int] = {}
    for r in kept:
        for s in r.get("sentences", []):
            strength[s] = max(strength.get(s, 0), ORDER.get(str(r.get("strength", "")).upper(), 0))
    return {
        "rules": len(rules), "kept": len(kept),
        "checks": len(contract["checks"]),
        "assertions": sum(1 for c in contract["checks"] if c.get("kind") == "assertion"),
        "sentences_kept": {s for r in kept for s in r.get("sentences", [])},
        "sentences_checked": {s for rid in checked_rules if rid in by_id for s in by_id[rid].get("sentences", [])},
        "rule_keys": [frozenset(r.get("sentences", [])) for r in kept if r.get("sentences")],
        "strength": strength,
    }


def jaccard(a: set, b: set) -> float | None:
    return round(len(a & b) / len(a | b), 3) if a | b else None


def pair(a: dict, b: dict) -> dict:
    keys_b = set(b["rule_keys"])
    both = a["strength"].keys() & b["strength"].keys()
    return {
        "sentences_kept": jaccard(a["sentences_kept"], b["sentences_kept"]),
        "sentences_checked": jaccard(a["sentences_checked"], b["sentences_checked"]),
        "rule_match": round(sum(1 for k in a["rule_keys"] if k in keys_b) / len(a["rule_keys"]), 3) if a["rule_keys"] else None,
        "strength_equal": round(sum(1 for s in both if a["strength"][s] == b["strength"][s]) / len(both), 3) if both else None,
    }


def compare(works: dict[str, Path]) -> dict:
    sums = {n: summary(w) for n, w in works.items()}
    pairs = {f"{x} vs {y}": pair(sums[x], sums[y]) for x, y in itertools.combinations(sums, 2)}
    return {"runs": {n: {k: (len(v) if isinstance(v, (set, list, dict)) else v) for k, v in s.items()}
                     for n, s in sums.items()},
            "pairs": pairs}


def to_markdown(res: dict) -> str:
    out = ["| Run | Rules | Kept | Sentences kept | Sentences checked | Checks (assertions) |", "|---|---|---|---|---|---|"]
    for n, s in res["runs"].items():
        out.append(f"| {n} | {s['rules']} | {s['kept']} | {s['sentences_kept']} | {s['sentences_checked']} | "
                   f"{s['checks']} ({s['assertions']}) |")
    out += ["", "| Pair | Sentences kept (Jaccard) | Sentences checked (Jaccard) | Rules with the same sentences | "
                "Same strength |", "|---|---|---|---|---|"]
    for p, v in res["pairs"].items():
        out.append(f"| {p} | {v['sentences_kept']} | {v['sentences_checked']} | {v['rule_match']} | {v['strength_equal']} |")
    return "\n".join(out)

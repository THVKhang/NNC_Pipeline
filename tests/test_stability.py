"""Phase 18: agreement of repeated runs, through the specification sentences rules cite."""
import json
import tempfile
import unittest
from pathlib import Path

from nnc import stability


def _rule(rid, sentences, strength="MUST", verdict="keep"):
    return {"id": rid, "sentences": sentences, "strength": strength, "review": {"verdict": verdict}}


class StabilityTest(unittest.TestCase):
    def _work(self, root, name, rules, checks):
        w = Path(root) / name / "work"
        w.mkdir(parents=True)
        (w / "rules.json").write_text(json.dumps({"rules": rules}), encoding="utf-8")
        (w / "contract.json").write_text(json.dumps({"checks": checks}), encoding="utf-8")
        return w

    def test_compare_two_runs(self):
        with tempfile.TemporaryDirectory() as t:
            a = self._work(t, "a", [_rule("A-1", ["1:s1"]), _rule("A-2", ["1:s2", "1:s3"]),
                                    _rule("A-3", ["2:s1"], verdict="reject")],
                           [{"id": "CHK-001", "kind": "assertion", "rules": ["A-1", "A-2"]}])
            b = self._work(t, "b", [_rule("B-9", ["1:s1"], strength="SHOULD"), _rule("B-8", ["1:s2"]),
                                    _rule("B-7", ["1:s3"])],
                           [{"id": "CHK-001", "kind": "test", "rules": ["B-9"]}])
            res = stability.compare({"a": a, "b": b})
        self.assertEqual(res["runs"]["a"]["kept"], 2)                 # the rejected rule is left out
        self.assertEqual(res["runs"]["a"]["sentences_kept"], 3)
        p = res["pairs"]["a vs b"]
        self.assertEqual(p["sentences_kept"], 1.0)                    # same sentences, cut differently
        self.assertEqual(p["rule_match"], 0.5)                        # only {1:s1} is a rule in both
        self.assertEqual(p["sentences_checked"], round(1 / 3, 3))     # a checks s1..s3, b checks s1
        self.assertEqual(p["strength_equal"], round(2 / 3, 3))        # s1 is MUST in a, SHOULD in b
        self.assertIn("| a vs b | 1.0 |", stability.to_markdown(res))


if __name__ == "__main__":
    unittest.main()

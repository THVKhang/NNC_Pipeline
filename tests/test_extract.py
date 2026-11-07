import re
import tempfile
import unittest
from pathlib import Path

from nnc.agents.backend import AgentResult
from nnc.extract import CachedBackend, extract, make_batches
from nnc.ingest import _successor_gap, build_index, split_glued_title, split_sentences

SPEC = """Front page of the document.
Copyright notice line
3-1
\f
Chapter 1 Handshake
This chapter describes the handshake.
Copyright notice line
3-2
\f
1.1 Valid rules
The master must keep VALID asserted until READY is HIGH. The slave can wait for VALID.
This sentence is descriptive.
Copyright notice line
3-3
\f
1.2

Data rules
Data must remain stable while VALID is HIGH and READY is LOW (e.g. during a wait state).
• the first item must hold • the second item is free text
Copyright notice line
3-4
\f
1.3 Glued title The source must not change ID before the handshake.
Copyright notice line
3-5
"""


class FakeExtractor:
    """Answers like agent A1: one rule per marked sentence; leaves one out and invents one ID on the
    first pass, so the gap-filler and the ID validation are exercised."""

    name = "fake"

    def __init__(self):
        self.calls = []

    def run(self, task, log_dir):
        self.calls.append(task.name)
        marked = re.findall(r"\[([^\]]+:s\d+)\]\*", task.instructions)
        gap_pass = "ONLY the sentences marked" in task.instructions
        if not gap_pass:
            marked = marked[1:]  # leave the first marked sentence uncovered
        rules = [{"sentences": [s], "strength": "MUST", "actor": "master", "signals": ["VALID"], "condition": "",
                  "statement": f"rule for {s}", "check": "assertion"} for s in marked]
        if not gap_pass:
            rules.append({**rules[0], "sentences": ["9.9:s1"]})  # invented ID
        return AgentResult({"rules": rules, "skipped": []}, self.name, None, 0.01,
                           {"input_tokens": 10, "output_tokens": 5})


class IngestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        p = Path(cls._tmp.name) / "spec.txt"
        p.write_text(SPEC, encoding="utf-8")
        cls.index = build_index(p)
        cls.sec = {s["id"]: s for s in cls.index["sections"]}

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_sections_and_titles(self):
        self.assertEqual([s["id"] for s in self.index["sections"]], ["front", "1", "1.1", "1.2", "1.3"])
        self.assertEqual(self.sec["1.2"]["title"], "Data rules")      # number and title on separate lines
        self.assertEqual(self.sec["1.3"]["title"], "Glued title")     # title glued to the first sentence
        self.assertTrue(any("glued" in w for w in self.index["warnings"]))

    def test_furniture_removed(self):
        texts = " ".join(st["text"] for s in self.index["sections"] for st in s["sentences"])
        self.assertNotIn("Copyright notice line", texts)
        self.assertNotIn("3-2", texts)

    def test_sentences_ids_pages_and_normative(self):
        s11 = self.sec["1.1"]["sentences"]
        self.assertEqual([s["id"] for s in s11], ["1.1:s1", "1.1:s2", "1.1:s3"])
        self.assertEqual([s["normative"] for s in s11], [True, True, False])
        self.assertEqual(s11[0]["page"], 3)
        s12 = [s["text"] for s in self.sec["1.2"]["sentences"]]
        self.assertIn("(e.g. during a wait state)", s12[0])            # abbreviation kept
        self.assertEqual(s12[1:], ["the first item must hold", "the second item is free text"])  # bullets split
        self.assertEqual(self.sec["1.3"]["sentences"][0]["text"], "The source must not change ID before the handshake.")

    def test_helpers(self):
        self.assertEqual(_successor_gap((3, 1), (3, 2)), 0)
        self.assertEqual(_successor_gap((3, 1), (3, 1, 1)), 0)
        self.assertEqual(_successor_gap((3, 1, 5), (3, 2)), 0)
        self.assertEqual(_successor_gap((3, 1), (3, 3)), 1)            # one missed heading
        self.assertIsNone(_successor_gap((3, 1), (3, 5)))
        self.assertIsNone(_successor_gap((3, 1), (2, 2)))
        self.assertEqual(split_glued_title("Removal of WID The text starts here"), ("Removal of WID", "The text starts here"))
        self.assertEqual(split_sentences("A is B. C is D."), ["A is B.", "C is D."])


class ExtractTest(IngestTest):
    def test_batches_respect_budget_and_chapters(self):
        self.assertEqual(len(make_batches(self.index, None, budget_tokens=10_000)), 1)
        self.assertGreater(len(make_batches(self.index, None, budget_tokens=10)), 1)
        self.assertEqual(make_batches(self.index, ["1.2"], 10_000)[0].section_ids, ["1.2"])

    def test_extract_gap_fill_invalid_ids_and_quotes(self):
        fake = FakeExtractor()
        with tempfile.TemporaryDirectory() as d:
            res = extract(self.index, fake, Path(d), budget_tokens=10_000, workers=1)
        cov = res["coverage"]
        self.assertEqual(cov["uncovered_after_first_pass"], 1)
        self.assertEqual(cov["uncovered"], [])                          # the gap-filler covered it
        self.assertEqual(cov["invalid_ids"], ["9.9:s1"])                # invented ID dropped
        self.assertEqual(len(fake.calls), 2)
        cited = {s for r in res["rules"] for s in r["sentences"]}
        self.assertEqual(cited, set(cov and [s["id"] for sec in self.index["sections"] if sec["level"]
                                             for s in sec["sentences"] if s["normative"]]))
        r0 = res["rules"][0]
        self.assertEqual(r0["id"], "R-1.1-01")
        self.assertEqual(r0["quote"], "The master must keep VALID asserted until READY is HIGH.")  # rebuilt by code

    def test_cache_skips_repeated_calls(self):
        fake = FakeExtractor()
        with tempfile.TemporaryDirectory() as d:
            cached = CachedBackend(fake, Path(d) / "cache")
            extract(self.index, cached, Path(d), budget_tokens=10_000, workers=1)
            n = len(fake.calls)
            res = extract(self.index, cached, Path(d), budget_tokens=10_000, workers=1)
        self.assertEqual(len(fake.calls), n)
        self.assertEqual(res["extraction"]["usage"]["cached"], res["extraction"]["usage"]["calls"])


if __name__ == "__main__":
    unittest.main()

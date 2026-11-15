"""Triage: which failures are analysed when there are more than the agent call takes."""
import unittest

from nnc import triage


def cl(nt, na):
    return [{"kind": "test", "name": f"t{i}"} for i in range(nt)] + \
           [{"kind": "assertion", "name": f"CHK-{i:03d}"} for i in range(na)]


class SelectTest(unittest.TestCase):
    def names(self, sel):
        return [c["name"] for c in sel]

    def test_all_when_few(self):
        self.assertEqual(len(triage.select(cl(3, 2), 12)), 5)

    def test_half_for_assertions(self):
        sel = triage.select(cl(13, 6), 12)
        self.assertEqual(sum(c["kind"] == "assertion" for c in sel), 6)
        self.assertEqual(sum(c["kind"] == "test" for c in sel), 6)
        self.assertEqual(self.names(sel)[:2], ["t0", "t1"])

    def test_unused_places_go_to_the_other_kind(self):
        sel = triage.select(cl(13, 2), 12)
        self.assertEqual(sum(c["kind"] == "test" for c in sel), 10)
        sel = triage.select(cl(2, 20), 12)
        self.assertEqual(sum(c["kind"] == "assertion" for c in sel), 10)


if __name__ == "__main__":
    unittest.main()

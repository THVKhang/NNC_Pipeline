"""The project page: made from the committed results, self-contained."""
import re
import unittest
from pathlib import Path

from nnc import site, summary

ROOT = Path(__file__).resolve().parents[1]


class SiteTest(unittest.TestCase):
    def test_every_design_of_the_readme_table_is_on_the_page(self):
        page = site.render(ROOT)
        rows = site.design_rows(ROOT / "designs")
        self.assertGreaterEqual(len(rows), 13)
        self.assertEqual(page.count("<tr><td>"), len(rows))
        for r in rows:
            name = re.match(r"\[([^\]]+)\]", r[0]).group(1)
            self.assertIn(f">{name}</a>", page)
        self.assertEqual(len(rows), len(summary.table(ROOT / "designs").splitlines()) - 2)

    def test_self_contained_and_honest(self):
        page = site.render(ROOT)
        self.assertNotIn("<script", page)
        self.assertNotIn("<link", page)
        self.assertNotRegex(page, r'src="https?://')
        self.assertIn("No design is signed off", page)
        self.assertIn("docker run --rm ghcr.io/thvkhang/nnc_pipeline", page)
        self.assertIn('name="viewport"', page)


if __name__ == "__main__":
    unittest.main()

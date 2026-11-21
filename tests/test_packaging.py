"""Phase 17: what an installed nnc needs is inside the package."""
import re
import unittest
from pathlib import Path

import nnc
from nnc import gen_rtl, sim, specdraft

ROOT = Path(__file__).resolve().parent.parent


class PackageDataTest(unittest.TestCase):
    def test_data_files_are_inside_the_package(self):
        pkg = Path(nnc.__file__).resolve().parent
        for f in (gen_rtl.RULES_DOC, specdraft.TEMPLATE, sim.SIMLIB):
            self.assertTrue(f.is_file(), f)
            self.assertTrue(f.resolve().is_relative_to(pkg), f"{f} is outside the package {pkg}")

    def test_package_copies_equal_the_documents(self):
        for name in ("RTL_RULES.md", "SPEC_TEMPLATE.md"):
            self.assertEqual((ROOT / "nnc" / "data" / name).read_bytes(), (ROOT / "docs" / name).read_bytes(),
                             f"nnc/data/{name} differs from docs/{name}: copy docs/{name} to nnc/data/")

    def test_pyproject_declares_the_data_and_the_version(self):
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('"data/*.md"', text)
        self.assertIn('"simlib/*.py"', text)
        self.assertIn('version = { attr = "nnc.__version__" }', text)
        self.assertRegex(nnc.__version__, r"^\d+\.\d+\.\d+$")

    def test_changelog_has_the_current_version(self):
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertTrue(re.search(rf"^## {re.escape(nnc.__version__)}\b", text, re.M),
                        f"CHANGELOG.md has no section for {nnc.__version__}")


class ReadmeTableTest(unittest.TestCase):
    def test_readme_table_matches_the_committed_results(self):
        from nnc import summary
        got = summary.readme_block((ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertIsNotNone(got, "README.md has no nnc-summary block")
        self.assertEqual(got, summary.block(ROOT / "designs"),
                         "README.md design table is out of date: run `nnc summary --readme README.md`")


if __name__ == "__main__":
    unittest.main()

"""Phase 17: nnc review-kit collects the evidence for a G4 reviewer, never a licensed standard, signs nothing."""
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from nnc import reviewkit

REQUEST = """# Request

| Design | Packet | State | Main questions for you |
|---|---|---|---|
| demo | [packet](x) | all pass | Is the reset reading right? |
| demo_other | [packet](y) | fails | Not this one. |

**demo, CHK-002.** A pulse may arrive twice.
- reading one
- reading two

**demo_other, CHK-001.** Not this one either.

### demo: a heading section
Text under the heading.

## What the evidence is
"""


class ReviewKitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        r = self.root = Path(self.tmp.name) / "demo"
        for rel, text in {
            "NOTICE.md": "| `spec/standards/open_std.md` | upstream | Apache-2.0 |\n",
            "LICENSE-Apache-2.0": "licence\n",
            "spec/demo_Design_Specification.md": "# spec\n",
            "spec/standards/open_std.md": "# open\n",
            "spec/standards/licensed_std.md": "# licensed, must not be copied\n",
            "work/review_packet.md": "# packet\n",
            "work/report.md": "# report\n",
            "work/formal/CHK-001.vcd": "$var\n",
            "work/cache/x.json": "{}\n",
            "rtl/m.sv": "module m; endmodule\n",
            "verif/sva/c.sv": "// checker\n",
            "sim/Makefile": "all:\n",
            "sim/sim_build/obj": "binary\n",
            "sim/results.xml": "<x/>\n",
        }.items():
            (r / rel).parent.mkdir(parents=True, exist_ok=True)
            (r / rel).write_text(text, encoding="utf-8")
        self.docs = [{"file": "spec/demo_Design_Specification.md", "role": "ip_spec"},
                     {"file": "spec/standards/open_std.md", "role": "standard"},
                     {"file": "spec/standards/licensed_std.md", "role": "standard"},
                     {"file": "../outside.md", "role": "standard"}]

    def tearDown(self):
        self.tmp.cleanup()

    def test_questions_for_one_design_only(self):
        qs = reviewkit.questions(REQUEST, "demo")
        self.assertEqual(qs[0], "Is the reset reading right?")
        self.assertTrue(any(q.startswith("**demo, CHK-002.**") and "reading two" in q for q in qs))
        self.assertTrue(any(q.startswith("### demo: a heading section") for q in qs))
        self.assertFalse(any("Not this one" in q for q in qs))

    def test_kit_contents(self):
        out = Path(self.tmp.name) / "kit"
        res = reviewkit.build(self.root, self.docs, out, REQUEST, make_zip=True)
        got = {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}
        for want in ("CHECKLIST.md", "MANIFEST.txt", "NOTICE.md", "LICENSE-Apache-2.0", "work/review_packet.md",
                     "work/report.md", "work/formal/CHK-001.vcd", "rtl/m.sv", "verif/sva/c.sv", "sim/Makefile",
                     "spec/demo_Design_Specification.md", "spec/standards/open_std.md"):
            self.assertIn(want, got)
        for never in ("spec/standards/licensed_std.md", "work/cache/x.json", "sim/sim_build/obj", "sim/results.xml"):
            self.assertNotIn(never, got)
        self.assertEqual(res["spec_left_out"], ["spec/standards/licensed_std.md", "../outside.md"])
        check = (out / "CHECKLIST.md").read_text(encoding="utf-8")
        self.assertIn("- [ ] Approve G4", check)
        self.assertIn("Nothing in this kit is signed", check)
        self.assertIn("**not included** (licence, or outside the design folder): `spec/standards/licensed_std.md`", check)
        self.assertIn("A pulse may arrive twice", check)
        self.assertIn("work/report.json | **missing**", check)
        line = next(ln for ln in (out / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() if ln.endswith("  rtl/m.sv"))
        self.assertEqual(line.split()[0], hashlib.sha256((out / "rtl/m.sv").read_bytes()).hexdigest())
        with zipfile.ZipFile(res["zip"]) as z:
            self.assertIn("demo_review_kit/CHECKLIST.md", z.namelist())
            self.assertNotIn("demo_review_kit/spec/standards/licensed_std.md", z.namelist())


if __name__ == "__main__":
    unittest.main()

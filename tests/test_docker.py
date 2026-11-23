"""The Docker image and the CI use the same tool versions; the image never holds what git keeps out."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ci_env(name: str) -> str:
    m = re.search(rf'^\s+{name}:\s*"([^"]+)"', (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"),
                  re.M)
    return m.group(1)


def _arg(name: str) -> str:
    return re.search(rf"^ARG {name}=(\S+)", (ROOT / "Dockerfile").read_text(encoding="utf-8"), re.M).group(1)


class DockerTest(unittest.TestCase):
    def test_same_tool_versions_as_ci(self):
        self.assertEqual(_arg("OSS_CAD_SUITE"), _ci_env("OSS_CAD_SUITE"))
        self.assertEqual(_arg("COCOTB"), _ci_env("COCOTB"))
        self.assertRegex(_arg("OSS_CAD_SUITE_SHA256"), r"^[0-9a-f]{64}$")

    def test_licensed_and_local_files_stay_out(self):
        ignored = (ROOT / ".dockerignore").read_text(encoding="utf-8").split()
        for entry in ("specs", "designs/axi_std", ".git", "corpus/.cache", "designs/*/work/logs",
                      ".claude/settings.local.json"):
            self.assertIn(entry, ignored)
        # the answer cache is committed (nnc demo --replay) and must be in the image
        self.assertNotIn("designs/*/work/cache", ignored)

    def test_devcontainer_builds_the_same_image(self):
        text = (ROOT / ".devcontainer" / "devcontainer.json").read_text(encoding="utf-8")
        cfg = json.loads("\n".join(line for line in text.splitlines() if not line.strip().startswith("//")))
        self.assertEqual(cfg["build"]["dockerfile"], "../Dockerfile")
        self.assertEqual(cfg["remoteUser"], "nnc")


if __name__ == "__main__":
    unittest.main()

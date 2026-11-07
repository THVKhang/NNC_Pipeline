"""Locate the external tools of the flow and report their versions (`nnc doctor`)."""
from __future__ import annotations

import importlib.util
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

MIN_PYTHON = (3, 11)


@dataclass(frozen=True)
class ToolCheck:
    name: str
    role: str           # "orchestrator" (needed for every run) or "simulation"
    path: str | None
    version: str | None
    note: str = ""

    @property
    def found(self) -> bool:
        return self.path is not None


def _version_key(p: Path) -> tuple[int, ...]:
    m = re.search(r"claude-code-(\d+(?:\.\d+)*)", str(p))
    return tuple(int(x) for x in m.group(1).split(".")) if m else ()


def find_claude() -> str | None:
    """Claude Code CLI: $NNC_CLAUDE_BIN, then PATH, then the newest VS Code extension binary."""
    env = os.environ.get("NNC_CLAUDE_BIN")
    if env:
        return env if Path(env).is_file() else None
    on_path = shutil.which("claude")
    if on_path:
        return on_path
    exe = "claude.exe" if os.name == "nt" else "claude"
    ext_root = Path.home() / ".vscode" / "extensions"
    candidates = sorted(ext_root.glob(f"anthropic.claude-code-*/resources/native-binary/{exe}"), key=_version_key)
    return str(candidates[-1]) if candidates else None


def _first_line(argv: list[str]) -> str | None:
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL,
                           encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError):
        return None
    text = (r.stdout or r.stderr).strip()
    return text.splitlines()[0] if text else None


def _simple(name: str, role: str, version_arg: str = "--version", note: str = "") -> ToolCheck:
    path = shutil.which(name)
    return ToolCheck(name, role, path, _first_line([path, version_arg]) if path else None, note)


def check_all() -> list[ToolCheck]:
    checks: list[ToolCheck] = []
    py_ok = sys.version_info[:2] >= MIN_PYTHON
    checks.append(ToolCheck(
        "python", "orchestrator", sys.executable if py_ok else None, platform.python_version(),
        "" if py_ok else f"needs Python {'.'.join(map(str, MIN_PYTHON))}+",
    ))
    claude = find_claude()
    checks.append(ToolCheck("claude", "orchestrator", claude, _first_line([claude, "--version"]) if claude else None,
                            "" if claude else "install Claude Code or set NNC_CLAUDE_BIN; the manual backend still works"))
    from nnc.ingest import find_pdftotext  # local import: ingest imports nothing from here
    pdf = find_pdftotext()
    checks.append(ToolCheck("pdftotext", "orchestrator", pdf, _first_line([pdf, "-v"]) if pdf else None,
                            "" if pdf else "needed to ingest PDF specifications (poppler / Git for Windows)"))
    checks.append(_simple("verilator", "simulation"))
    checks.append(_simple("iverilog", "simulation", "-V", "optional fallback simulator"))
    checks.append(_simple("make", "simulation", note="GNU make, used by cocotb"))
    cocotb = importlib.util.find_spec("cocotb")
    checks.append(ToolCheck("cocotb", "simulation", cocotb.origin if cocotb else None,
                            _first_line([sys.executable, "-c", "import cocotb;print(cocotb.__version__)"]) if cocotb else None))
    if os.name == "nt":
        wsl = shutil.which("wsl")
        checks.append(ToolCheck("wsl", "simulation", wsl, None,
                                "simulation host: tools live in the WSL distro, not on Windows "
                                "(docs/ARCHITECTURE.md section 8)"))
    return checks

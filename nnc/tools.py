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
    from nnc.export import pandoc_path  # local import: export imports nothing from here
    pandoc = pandoc_path()
    checks.append(ToolCheck("pandoc", "export", pandoc, _first_line([pandoc, "--version"]) if pandoc else None,
                            "" if pandoc else "needed by 'nnc export' only"))
    return checks


# Tools on the simulation host (WSL distribution or this machine), probed by running a script there:
# name, role, version command. "required" tools make 'nnc doctor --host' fail when missing.
HOST_TOOLS = [
    ("verilator", "required", "verilator --version"),
    ("verilator_coverage", "required", "verilator_coverage --version"),
    ("make", "required", "make --version"),
    ("python3", "required", "python3 --version"),
    ("cocotb-config", "required", "cocotb-config --version"),
    ("yosys", "rtl/formal", "yosys -V"),
    ("sby", "formal", "sby --help >/dev/null 2>&1 && echo SymbiYosys"),
    ("yosys-abc", "formal", "yosys-abc -q 'version' 2>&1"),
    ("yices-smt2", "formal", "yices-smt2 --version"),
]


def host_probe_script(pdk_dir: str, liberty: list[str]) -> str:
    lines = ["echo NNC_PROBE_START"]
    for name, _, cmd in HOST_TOOLS:
        lines.append(f'p=$(command -v {name}); if [ -n "$p" ]; then v=$({cmd} 2>&1 | head -1); '
                     f'echo "NNC_TOOL|{name}|$p|$v"; else echo "NNC_TOOL|{name}||"; fi')
    for lib in liberty:
        lines.append(f'if [ -f {pdk_dir}/{lib} ]; then echo "NNC_TOOL|{lib}|{pdk_dir}/{lib}|present"; '
                     f'else echo "NNC_TOOL|{lib}||"; fi')
    lines.append("echo NNC_PROBE_END")
    return "\n".join(lines) + "\n"


def parse_probe(output: str) -> list[ToolCheck]:
    roles = {n: r for n, r, _ in HOST_TOOLS}
    out = []
    for line in output.splitlines():
        if not line.startswith("NNC_TOOL|"):
            continue
        _, name, path, version = (line.split("|", 3) + ["", "", ""])[:4]
        role = roles.get(name, "synthesis")
        note = "" if path else ("GF180MCU liberty: gen-rtl synthesis falls back to generic cells"
                                if role == "synthesis" else "")
        out.append(ToolCheck(name, role, path or None, version.strip() or None, note))
    return out


def host_checks(host=None) -> tuple[str, list[ToolCheck], str]:
    """(host name, tools found on the simulation host, problem or ""). Runs one short script there, so
    a WSL that cannot start a session shows up here and not in the middle of a regression."""
    from nnc.rtlcheck import CORNERS, PDK_DIR
    from nnc.simhost import HostError, default_host
    host = host or default_host()
    try:
        res = host.run({}, host_probe_script(PDK_DIR, list(CORNERS.values())), [], timeout_s=120, tag="doctor")
    except HostError as e:
        return host.name, [], str(e)
    if "NNC_PROBE_END" not in res.output:
        return host.name, [], "the probe script did not finish: " + " | ".join(res.output.splitlines()[-5:])
    return host.name, parse_probe(res.output), ""

"""Where EDA commands run: a WSL distribution (Windows) or the local machine (Linux).

A run is: a set of input files, a bash script, and output patterns to bring back. On Windows the
files are staged in an ASCII-only temporary folder (some tools cannot open non-ASCII paths), copied
into the Linux filesystem of the distribution (building under /mnt/c is slow and OneDrive-synced),
the script runs there with the tools of /etc/profile.d/nnc.sh, and the outputs are copied back.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DISTRO = os.environ.get("NNC_WSL_DISTRO", "Ubuntu-24.04")
PROFILE = "/etc/profile.d/nnc.sh"


@dataclass
class RunResult:
    returncode: int
    output: str
    out_dir: Path        # local folder holding the files brought back


def _stage_base() -> Path:
    base = Path(tempfile.gettempdir())
    if not str(base).isascii():
        base = Path(os.environ.get("SystemDrive", "C:") + "\\") / "nnc_tmp"
    base = base / "nnc_runs"
    base.mkdir(parents=True, exist_ok=True)
    return base


def to_wsl_path(p: Path) -> str:
    p = Path(p).resolve()
    drive = p.drive.rstrip(":").lower()
    return f"/mnt/{drive}" + p.as_posix()[len(p.drive):]


def _write_inputs(dst: Path, files: dict[str, object]) -> None:
    for rel, src in files.items():
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(src, Path):
            shutil.copyfile(src, target)
        elif isinstance(src, bytes):
            target.write_bytes(src)
        else:
            target.write_text(str(src), encoding="utf-8", newline="\n")


class SimHost:
    """Base: run(files, script, outputs) on the configured host."""

    name = "base"

    def run(self, files: dict[str, object], script: str, outputs: list[str], timeout_s: int = 1800,
            tag: str = "run") -> RunResult:
        raise NotImplementedError


class WslHost(SimHost):
    name = "wsl"

    def __init__(self, distro: str = DEFAULT_DISTRO):
        self.distro = distro

    def run(self, files, script, outputs, timeout_s=1800, tag="run") -> RunResult:
        stage = _stage_base() / f"{tag}_{uuid.uuid4().hex[:8]}"
        (stage / "in").mkdir(parents=True)
        (stage / "out").mkdir()
        _write_inputs(stage / "in", files)
        remote = f"/root/nnc_runs/{stage.name}"
        copy_back = "\n".join(
            f'for f in {pat}; do [ -e "$f" ] && mkdir -p "$OUT/$(dirname "$f")" && cp -r "$f" "$OUT/$f"; done'
            for pat in outputs)
        wrapper = (
            "#!/bin/bash\n"
            f"[ -f {PROFILE} ] && source {PROFILE}\n"
            f"OUT='{to_wsl_path(stage / 'out')}'\n"
            f"rm -rf {remote} && mkdir -p {remote} && cp -r '{to_wsl_path(stage / 'in')}'/. {remote}/\n"
            f"cd {remote}\n"
            "( set +e\n" + script + "\n) > nnc_run.log 2>&1\n"
            "RC=$?\n"
            "cp nnc_run.log \"$OUT/\"\n"
            f"{copy_back}\n"
            f"rm -rf {remote}\n"
            "exit $RC\n"
        )
        (stage / "run.sh").write_text(wrapper, encoding="utf-8", newline="\n")
        try:
            proc = subprocess.run(["wsl.exe", "-d", self.distro, "-u", "root", "--", "bash", to_wsl_path(stage / "run.sh")],
                                  capture_output=True, timeout=timeout_s)
            rc = proc.returncode
            host_out = (proc.stdout + proc.stderr).replace(b"\x00", b"").decode("utf-8", "replace")
        except subprocess.TimeoutExpired:
            rc, host_out = 124, "timeout"
        log = stage / "out" / "nnc_run.log"
        if log.is_file():
            text = log.read_text(encoding="utf-8", errors="replace")
        else:
            # The wrapper never reached its copy-back (WSL failed to start or was killed):
            # keep wsl.exe's own output so the failure is not an empty log.
            text = f"NNC_HOST_ERROR wsl.exe rc={rc} produced no run log\n{host_out}"
        return RunResult(rc, text, stage / "out")


class LocalHost(SimHost):
    name = "local"

    def run(self, files, script, outputs, timeout_s=1800, tag="run") -> RunResult:
        stage = _stage_base() / f"{tag}_{uuid.uuid4().hex[:8]}"
        work, out = stage / "work", stage / "out"
        work.mkdir(parents=True)
        out.mkdir()
        _write_inputs(work, files)
        try:
            proc = subprocess.run(["bash", "-c", f"[ -f {PROFILE} ] && source {PROFILE}; set +e\n{script}"],
                                  cwd=work, capture_output=True, timeout=timeout_s)
            rc, text = proc.returncode, (proc.stdout + proc.stderr).decode("utf-8", "replace")
        except subprocess.TimeoutExpired:
            rc, text = 124, "timeout"
        (out / "nnc_run.log").write_text(text, encoding="utf-8")
        for pat in outputs:
            for f in work.glob(pat):
                dst = out / f.relative_to(work)
                dst.parent.mkdir(parents=True, exist_ok=True)
                (shutil.copytree if f.is_dir() else shutil.copyfile)(f, dst)
        return RunResult(rc, text, out)


def default_host() -> SimHost:
    if os.name == "nt":
        return WslHost()
    return LocalHost()


def lint_sv(host: SimHost, files: dict[str, object], top: str, timeout_s: int = 300) -> tuple[bool, str]:
    """verilator --lint-only; returns (ok, error lines)."""
    srcs = " ".join(sorted(k for k in files if k.endswith((".sv", ".v"))))
    script = (f"verilator --lint-only --assert --timing -Wno-fatal -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL "
              f"-Wno-UNUSEDPARAM -Wno-PINCONNECTEMPTY --top-module {top} {srcs}\necho NNC_RC=$?")
    res = host.run(files, script, [], timeout_s=timeout_s, tag="lint")
    errors = [l for l in res.output.splitlines() if l.startswith("%Error")]
    ok = "NNC_RC=0" in res.output and not errors
    if not ok and not errors:
        errors = res.output.splitlines()[-20:]
    return ok, "\n".join(errors[:40])

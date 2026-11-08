"""Bug injection: run the approved checkers and tests on a patched copy of the RTL.

`nnc inject <design> <patch.diff> --out <dir>` copies `rtl/` into `<dir>/rtl`, applies a unified diff
to the copy, simulates it with the gated verification sources, and lets the triage agent analyse the
failures. The delivered RTL is never touched. It answers "would this flow catch that bug?" with
evidence, and makes a bug demonstration reproducible by one command.

The diff is matched by file name inside `rtl/` (the directory part of `---`/`+++` is ignored), and
each hunk must match the file exactly (context and removed lines); a hunk that does not match is an
error, never a fuzzy guess.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


class PatchError(ValueError):
    pass


def parse_patch(text: str) -> list[dict]:
    """[{'file': basename, 'hunks': [{'start': int, 'old': [lines], 'new': [lines]}]}]."""
    files: list[dict] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ "):
            target = lines[i + 1][4:].split("\t")[0].strip()
            if target == "/dev/null":
                raise PatchError("file deletion is not supported")
            files.append({"file": Path(target).name, "hunks": []})
            i += 2
            continue
        m = HUNK_RE.match(line)
        if m:
            if not files:
                raise PatchError(f"hunk before any file header: {line}")
            old_n = int(m.group(2)) if m.group(2) is not None else 1
            new_n = int(m.group(4)) if m.group(4) is not None else 1
            hunk = {"start": int(m.group(1)), "old": [], "new": []}
            i += 1
            while i < len(lines) and (len(hunk["old"]) < old_n or len(hunk["new"]) < new_n):
                body = lines[i]
                tag, rest = (body[:1], body[1:]) if body else (" ", "")
                if tag == "\\":  # "\ No newline at end of file"
                    i += 1
                    continue
                if tag not in " -+":
                    raise PatchError(f"malformed hunk line in {files[-1]['file']}: {body!r}")
                if tag in " -":
                    hunk["old"].append(rest)
                if tag in " +":
                    hunk["new"].append(rest)
                i += 1
            if len(hunk["old"]) != old_n or len(hunk["new"]) != new_n:
                raise PatchError(f"truncated hunk in {files[-1]['file']} at line {hunk['start']}")
            files[-1]["hunks"].append(hunk)
            continue
        i += 1
    if not files or not any(f["hunks"] for f in files):
        raise PatchError("no hunk found in the patch")
    return files


def apply_hunks(text: str, hunks: list[dict], name: str) -> str:
    lines = text.splitlines()
    offset = 0
    for h in hunks:
        old = h["old"]
        want = max(h["start"] - 1 + offset, 0)
        candidates = [p for p in range(len(lines) - len(old) + 1) if lines[p:p + len(old)] == old]
        if not candidates:
            raise PatchError(f"{name}: hunk at line {h['start']} does not match the file")
        pos = min(candidates, key=lambda p: abs(p - want))
        lines[pos:pos + len(old)] = h["new"]
        offset += len(h["new"]) - len(old)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def make_copy(rtl_dir: Path, patch_text: str, dest: Path) -> list[str]:
    """Copy rtl_dir to dest and apply the patch to the copy; returns the patched file names."""
    patch = parse_patch(patch_text)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(rtl_dir, dest)
    changed = []
    for f in patch:
        target = dest / f["file"]
        if not target.is_file():
            raise PatchError(f"{f['file']} is not a file of {rtl_dir}")
        original = target.read_text(encoding="utf-8")
        target.write_text(apply_hunks(original, f["hunks"], f["file"]), encoding="utf-8", newline="\n")
        changed.append(f["file"])
    return changed

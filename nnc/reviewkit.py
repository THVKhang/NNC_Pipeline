"""`nnc review-kit <ip>`: one folder (or .zip) with what a G4 reviewer needs for one design (phase 17).

The reviewer should not need NNC, an agent or a simulator to read the evidence. The kit holds:
    CHECKLIST.md      the questions for this design (from docs/G4_REVIEW_REQUEST.md), the sign-off conditions
                      of work/report.json, and an empty decision box
    MANIFEST.txt      SHA-256 of every file of the kit
    work/...          review packet, report, rules, contract, triage, formal and mutation results, traces
    spec/             the IP specification; a standard only when NOTICE.md names it (licence)
    rtl/, verif/      the design under test and the generated verification
    sim/              the reproduction kit (cocotb + Verilator, `make`), without build products
    NOTICE.md, LICENSE-*

Nothing is signed or approved here: the kit is the input of a person's decision.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
import zipfile
from pathlib import Path

import nnc
from nnc import report

WORK_FILES = ["review_packet.md", "report.md", "report.json", "rules.md", "contract.md", "formal.md",
              "formal_triage.md", "triage.md", "spec_lint.md", "mutation.json", "rtl_gen.md", "bench.md",
              "baseline.md", "verif_fix/verif_fix.md"]
TRACE_GLOBS = ["work/formal/*.vcd", "work/mutation_equiv/*.vcd"]
TREES = ["rtl", "verif", "sim", "fix_candidate"]
SKIP_PARTS = {"sim_build", "obj_dir", "runlogs", "__pycache__", "coverage_annotated"}
SKIP_SUFFIXES = {".vcd", ".fst", ".dat", ".info", ".pyc"}
SKIP_NAMES = {"results.xml", "sim.log"}


def _tree(root: Path, rel: str) -> list[str]:
    base = root / rel
    if not base.is_dir():
        return []
    out = []
    for p in sorted(base.rglob("*")):
        r = p.relative_to(root)
        if p.is_file() and not (set(r.parts) & SKIP_PARTS) and p.suffix not in SKIP_SUFFIXES \
                and p.name not in SKIP_NAMES:
            out.append(r.as_posix())
    return out


def spec_files(root: Path, documents: list[dict]) -> tuple[list[str], list[str]]:
    """(copied, left out). The IP specification is copied; a standard only when NOTICE.md names its file,
    i.e. its licence allows redistribution and the repository already carries it."""
    notice = (root / "NOTICE.md").read_text(encoding="utf-8", errors="replace") if (root / "NOTICE.md").is_file() else ""
    copied, left = [], []
    for d in documents:
        f = d["file"]
        p = root / f
        if not p.is_file() or not p.resolve().is_relative_to(root.resolve()):
            left.append(f)
        elif d.get("role") == "ip_spec" or Path(f).name in notice:
            copied.append(f)
        else:
            left.append(f)
    return copied, left


def questions(request_md: str, ip: str) -> list[str]:
    """The text of docs/G4_REVIEW_REQUEST.md about `ip`: the last cell of its table row, and every paragraph or
    section that starts with **<ip>, / **<ip>: or a heading naming it, up to the next paragraph of that kind."""
    out: list[str] = []
    for line in request_md.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.startswith("|") else []
        if cells and cells[0] == ip and len(cells) >= 4:
            out.append(cells[-1])
    block: list[str] | None = None
    blocks: list[list[str]] = []
    for line in request_md.splitlines():
        starts = (line.startswith(f"**{ip},") or line.startswith(f"**{ip}:") or line.startswith(f"**{ip} ")
                  or (line.startswith("### ") and re.search(rf"\b{re.escape(ip)}\b", line)))
        other = line.startswith("**") or line.startswith("#")
        if starts:
            block = [line]
            blocks.append(block)
        elif other:
            block = None
        elif block is not None:
            block.append(line)
    out += ["\n".join(b).strip() for b in blocks]
    return [q for q in out if q]


def checklist(ip: str, rep: dict | None, qs: list[str], copied: list[str], left: list[str]) -> str:
    out = [f"# G4 review kit: {ip}", "",
           f"Made {time.strftime('%Y-%m-%d')} by nnc {nnc.__version__} (`nnc review-kit {ip}`). Nothing in this kit is "
           "signed: G1-G3 were approved on delegation by an AI assistant, and G4 is open until a qualified person "
           "decides. Read `work/review_packet.md` first; its section 8 is the general checklist.", ""]
    out += ["## Questions for this design", ""]
    out += ([q + "\n" for q in qs] if qs else
            ["No design-specific question was recorded in docs/G4_REVIEW_REQUEST.md; use the packet's checklist.", ""])
    out += ["## Sign-off conditions (from work/report.json)", "", "| Condition | State | Detail |", "|---|---|---|"]
    if rep:
        for name, ok, detail in report.signoff_conditions(rep):
            out.append(f"| {name} | {'met' if ok else '**not met**'} | {detail} |")
    else:
        out.append("| work/report.json | **missing** | run `nnc report` |")
    out += ["", "## Specification in this kit", ""]
    out += [f"- included: `{f}`" for f in copied]
    out += [f"- **not included** (licence, or outside the design folder): `{f}`; obtain it from its publisher"
            for f in left]
    out += ["", "## Decision", "",
            "- [ ] Approve G4      - [ ] Do not approve (corrections and questions below)", "",
            "Name: ______________________   Role: ______________________   Date: ______________", "",
            "Waivers, open items, corrections:", "", "", "",
            f"To record an approval: `nnc gate approve {ip} G4_signoff --by \"<your name>\" --note \"<waivers>\"`. "
            "The approval is bound to the current results: a later run makes it STALE.", ""]
    return "\n".join(out)


def build(root: Path, documents: list[dict], out_dir: Path, request_md: str | None = None,
          make_zip: bool = False) -> dict:
    root = Path(root)
    ip = root.name
    files: list[str] = []
    for f in WORK_FILES:
        if (root / "work" / f).is_file():
            files.append(f"work/{f}")
    for g in TRACE_GLOBS:
        files += sorted(p.relative_to(root).as_posix() for p in root.glob(g))
    for t in TREES:
        files += _tree(root, t)
    files += sorted(p.name for p in root.iterdir() if p.is_file() and (p.name == "NOTICE.md" or p.name.startswith("LICENSE")))
    copied, left = spec_files(root, documents)
    files += copied
    files = list(dict.fromkeys(files))
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    for rel in files:
        dst = out_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / rel, dst)
    rep = json.loads((root / "work" / "report.json").read_text(encoding="utf-8")) \
        if (root / "work" / "report.json").is_file() else None
    qs = questions(request_md, ip) if request_md else []
    (out_dir / "CHECKLIST.md").write_text(checklist(ip, rep, qs, copied, left), encoding="utf-8")
    files.append("CHECKLIST.md")
    manifest = "".join(f"{hashlib.sha256((out_dir / r).read_bytes()).hexdigest()}  {r}\n" for r in sorted(files))
    (out_dir / "MANIFEST.txt").write_text(manifest, encoding="utf-8")
    res = {"dir": out_dir, "files": len(files) + 1, "questions": len(qs), "spec_left_out": left, "zip": None}
    if make_zip:
        zpath = out_dir.with_suffix(".zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(out_dir.rglob("*")):
                if p.is_file():
                    z.write(p, f"{ip}_review_kit/{p.relative_to(out_dir).as_posix()}")
        res["zip"] = zpath
    return res

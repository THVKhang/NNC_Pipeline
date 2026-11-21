"""The table of every design in README.md (`nnc summary`), made by code from each design's committed results.

    tests       work/results.json (passing / all, every run of the run set merged)
    checks      work/report.json (checks PASS / all)
    formal      work/formal.json (count per status)
    mutation    work/mutation.json (recorded score; without the mutants formal proved equivalent, if checked)
    G4          the gate state of nnc_state.json; G4 is never signed by the flow

README.md holds the table between the markers below; a unit test fails when it differs from the files.
"""
from __future__ import annotations

import json
from pathlib import Path

from nnc.project import Design

START = "<!-- nnc-summary:start (nnc summary --readme README.md) -->"
END = "<!-- nnc-summary:end -->"
LABEL = {"UNSUPPORTED": "simulation-only", "CEX": "**counterexample**"}
ORDER = ("PROVEN", "BOUNDED", "TIMEOUT", "UNSUPPORTED", "VACUOUS", "CEX", "ERROR")


def _read(p: Path) -> dict | None:
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def row(root: Path) -> list[str] | None:
    work = root / "work"
    res, rep = _read(work / "results.json"), _read(work / "report.json")
    if not res or not rep:
        return None
    tests = {}
    for t in res.get("tests") or []:
        tests[t.get("status", "?")] = tests.get(t.get("status", "?"), 0) + 1
    n_tests = sum(tests.values())
    by = rep["checks"]["by_status"]
    fm = (_read(work / "formal.json") or {}).get("by_status")
    formal = " / ".join(f"{fm[k]} {LABEL.get(k, k.lower())}" for k in ORDER if fm.get(k)) if fm else "not run"
    mu = _read(work / "mutation.json")
    if mu:
        mut = f"{mu.get('score')} % ({mu.get('killed')}/{mu.get('killed', 0) + mu.get('survived', 0)})"
        eq = mu.get("equivalence") or {}
        if eq.get("proven_equivalent"):
            mut += f"; {eq['score_without_equivalent']} % without {eq['proven_equivalent']} proven equivalent"
    else:
        mut = "not run"
    g4 = {s.gate: s.state for s in Design.open(root).status()}.get("G4_signoff", "PENDING")
    return [f"[{root.name}](designs/{root.name})", f"{tests.get('pass', 0)}/{n_tests}",
            f"{by.get('PASS', 0)}/{sum(by.values())}", formal, mut, f"{g4.lower()} (not signed)"
            if g4 != "APPROVED" else "approved"]


def table(designs_root: Path) -> str:
    rows = [r for d in sorted(Path(designs_root).iterdir()) if (d / "nnc_state.json").is_file() and (r := row(d))]
    out = ["| Design | Tests passing | Checks PASS | Formal | Mutation | G4 |", "|---|---|---|---|---|---|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def block(designs_root: Path) -> str:
    return f"{START}\n{table(designs_root)}\n{END}"


def readme_block(readme_text: str) -> str | None:
    i, j = readme_text.find(START), readme_text.find(END)
    return readme_text[i:j + len(END)] if i >= 0 and j > i else None


def write_readme(readme: Path, designs_root: Path) -> bool:
    """Replace the block in README.md; True if it changed."""
    text = readme.read_text(encoding="utf-8")
    old = readme_block(text)
    if old is None:
        raise ValueError(f"{readme} has no {START} ... {END} block")
    new = block(designs_root)
    if old == new:
        return False
    readme.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
    return True

"""Compare a run of the reproduction kit with the recorded results (`nnc kit-check`, used by CI).

The kit `designs/<ip>/sim/` reproduces the regression without NNC (`make regression | tee sim.log`).
This module reads what that run produced (results.xml, sim.log) and compares it with the recorded
results of the same configuration: work/results.json, or for a run set the primary run in
work/runs/<label>.json. It compares outcomes, not counts: the set of tests, the failing tests, the
failing assertions, the assertions never hit, and the checks declared not verifiable. Hit counts may
change with the simulator version; a changed outcome means the committed verification no longer
reproduces.
"""
from __future__ import annotations

import json
from pathlib import Path

from nnc import sim


def outcome(res: dict) -> dict[str, list[str]]:
    a = res.get("assertions") or {}
    return {
        "tests": sorted(t["name"] for t in res.get("tests", [])),
        "failing_tests": sorted(t["name"] for t in res.get("tests", []) if t["status"] == "fail"),
        "failing_assertions": sorted(c for c, v in a.items() if v["fails"] > 0),
        "never_hit": sorted(c for c, v in a.items() if v["hits"] == 0),
        "assertions": sorted(a),
        "not_verifiable": sorted(res.get("not_verifiable") or {}),
    }


def compare(recorded: dict, reproduced: dict) -> list[str]:
    """Human-readable differences between two outcomes; empty when they agree."""
    want, got = outcome(recorded), outcome(reproduced)
    diffs = []
    for k in want:
        if want[k] != got[k]:
            missing = sorted(set(want[k]) - set(got[k]))
            extra = sorted(set(got[k]) - set(want[k]))
            diffs.append(f"{k}: recorded only {missing[:10]}, reproduced only {extra[:10]}")
    return diffs


def recorded_result(work: Path) -> tuple[dict, str]:
    """The recorded result of the configuration the kit reproduces, and its name."""
    res = json.loads((work / "results.json").read_text(encoding="utf-8"))
    rs = res.get("run_set")
    if rs:
        prim = rs["primary"]
        return json.loads((work / "runs" / f"{prim}.json").read_text(encoding="utf-8"))["result"], prim
    return res, f"seed {res.get('seed')}"


def check(design_root: Path, kit_dir: Path | None = None) -> tuple[bool, list[str]]:
    kit = kit_dir or design_root / "sim"
    if not (kit / "results.xml").is_file():
        return False, [f"{kit / 'results.xml'} is missing: run `make regression 2>&1 | tee sim.log` in {kit}"]
    if not (kit / "sim.log").is_file():
        return False, [f"{kit / 'sim.log'} is missing: tee the make output into sim.log (the checkers print there)"]
    rtl = [f.name for f in sim.rtl_files(design_root / "rtl")]
    got = sim.parse_results(kit, rtl)
    want, name = recorded_result(design_root / "work")
    diffs = compare(want, got)
    head = f"{design_root.name}: kit run vs recorded {name}: {len(got['tests'])} tests, " \
           f"{len(got['assertions'])} assertions"
    return not diffs, [head + (" — SAME OUTCOME" if not diffs else " — DIFFERENT")] + diffs

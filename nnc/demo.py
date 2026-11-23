"""`nnc demo <ip>`: rerun the steps of a finished design that need no agent, and compare each with what is
recorded in the repository.

A clean clone holds the outputs of the agent stages (rules, contract, checkers, cover points, tests, the
reproduction kit) but not the agent calls. This command runs what code alone can run on them:

1. intake     the verdict on the specification and RTL (`nnc intake`), compared with work/intake.json;
2. kit        the reproduction kit of the primary run (`make regression` in sim/, staged on the tool host),
              compared with the recorded outcome (`nnc kit-check`): tests, failing tests and assertions,
              assertions never hit, checks not verifiable;
3. cdc        the structural clock/reset domain crossing check, compared with work/cdc.json;
4. formal     (with `--formal`, it takes long) every recorded formal configuration (`nnc formal-check`).

No step calls an agent, so a demo costs no tokens. It exits 0 only if every step that ran gives the
recorded outcome. Used by the Docker image (`docker run ... nnc demo sync_fifo`) and by CI.

With `--replay`, the agent stages that read the specification (extract, review, contract) run again, each in
its own scratch copy of the design, with the answers of the committed cache (designs/<ip>/work/cache/) and
the backend `replay`, which stops instead of calling a model. Each stage's records are compared with the
committed ones, leaving out only what a run changes by itself: its date, its usage (a replay costs nothing)
and the designer's decisions on open questions (recorded by `nnc answer` after the review, not an agent
output). A stage whose prompt or inputs changed after the recorded run has no cached answer: NOT_CACHED.
The stages that write code (checkers, tests) are not replayed: their committed files include later
corrections (A17, triage B), so the first answer is not the committed file.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

STEPS = ("intake", "kit", "cdc", "formal")
REPLAY_STAGES = ("extract", "review", "contract")
_RUN_KEYS = {"date", "usage"}            # when a run happened and what it cost: not part of its result
# files a run of the kit writes into sim/: never staged, so a demo starts from the committed kit only
_KIT_OUTPUTS = {"sim_build", "results.xml", "sim.log", "runlogs", "__pycache__", "coverage.dat", "coverage.info"}


@dataclass
class Step:
    name: str
    status: str                  # SAME, DIFFERENT, SKIPPED, ERROR
    seconds: float = 0.0
    lines: list[str] = field(default_factory=list)


def kit_files(root: Path) -> dict[str, Path]:
    """The files the reproduction kit reads, under the design's own folder name (the kit refers to `..`)."""
    files: dict[str, Path] = {}
    for sub in ("rtl", "verif", "sim"):
        base = root / sub
        if not base.is_dir():
            continue
        for f in sorted(base.rglob("*")):
            rel = f.relative_to(root)
            if f.is_file() and not (set(rel.parts) & _KIT_OUTPUTS) and f.suffix != ".pyc":
                files[f"{root.name}/{rel.as_posix()}"] = f
    return files


def primary_run(root: Path) -> tuple[str, str, int]:
    """(label, kit folder relative to sim/, seed) of the run CI reproduces first."""
    from nnc import kitcheck
    return kitcheck.runs(root)[0]


def kit_script(name: str, folder: str, seed: int) -> str:
    kit = f"{name}/sim" + ("" if folder in ("", ".") else f"/{folder}")
    return (f"cd {kit} && make regression SEED={seed} > sim.log 2>&1\n"
            f"echo NNC_MAKE=$?\n")


def _timed(name: str, fn) -> Step:
    t0 = time.time()
    try:
        status, lines = fn()
    except Exception as e:  # noqa: BLE001 - a demo reports every step, it never stops half way
        status, lines = "ERROR", [f"{type(e).__name__}: {e}"]
    return Step(name, status, round(time.time() - t0, 1), lines)


def _intake(d, host) -> tuple[str, list[str]]:
    from nnc import intake
    from nnc.cli import _intake_inputs
    rec = d.work / "intake.json"
    if not rec.is_file():
        return "SKIPPED", ["work/intake.json is not recorded"]
    inp = _intake_inputs(d, None, as_flow_reads=True)
    rep = intake.run(host, inp["rtl"], top=inp["top"], listed=inp["listed"], defines=inp["defines"],
                     spec=inp["spec"])
    want = json.loads(rec.read_text(encoding="utf-8"))["verdict"]
    line = f"verdict {rep['verdict']} (recorded {want})"
    return ("SAME" if rep["verdict"] == want else "DIFFERENT"), [line]


def _kit(d, host) -> tuple[str, list[str]]:
    from nnc import kitcheck
    label, folder, seed = primary_run(d.root)
    name = d.root.name
    kit_rel = f"{name}/sim" + ("" if folder in ("", ".") else f"/{folder}")
    res = host.run(kit_files(d.root), kit_script(name, folder, seed),
                   [f"{kit_rel}/sim.log", f"{kit_rel}/results.xml"], timeout_s=3600, tag="demo_kit")
    ok, lines = kitcheck.check(d.root, res.out_dir / kit_rel, label or None)
    return ("SAME" if ok else "DIFFERENT"), [f"run {label or 'primary'} (seed {seed})"] + lines


def _cdc(d) -> tuple[str, list[str]]:
    from nnc import flow
    from nnc.cli import cdc_compare
    rec = d.work / "cdc.json"
    if not rec.is_file():
        return "SKIPPED", ["work/cdc.json is not recorded"]
    rep = flow.cdc(d, flow.Options(backend="manual"), write=False)
    diffs = cdc_compare(json.loads(rec.read_text(encoding="utf-8")), rep)
    return ("SAME" if not diffs else "DIFFERENT"), [f"verdict {rep.get('verdict')}"] + diffs


def _formal(d, workers: int) -> tuple[str, list[str]]:
    from nnc import flow
    ok, lines = flow.formal_check(d, flow.Options(backend="manual", workers=workers))
    return ("SAME" if ok else "DIFFERENT"), lines


def run(d, host, *, formal: bool = False, workers: int = 4, replay_agents: bool = False, say=print) -> list[Step]:
    out = []
    for name in STEPS:
        say(f"[demo] {d.name}: {name} ...")
        if name == "intake":
            s = _timed(name, lambda: _intake(d, host))
        elif name == "kit":
            s = _timed(name, lambda: _kit(d, host))
        elif name == "cdc":
            s = _timed(name, lambda: _cdc(d))
        elif formal:
            s = _timed(name, lambda: _formal(d, workers))
        else:
            s = Step(name, "SKIPPED", 0.0, ["add --formal to rerun the formal check (it takes long)"])
        say(f"[demo] {d.name}: {name} {s.status} ({s.seconds} s)")
        out.append(s)
    if replay_agents:
        out += replay(d, say)
    return out


def normalized(x):
    """A record without the date and usage of the run that wrote it, and without the designer's decisions."""
    if isinstance(x, dict):
        drop = _RUN_KEYS | ({"decision"} if "question" in x else set())
        return {k: normalized(v) for k, v in x.items() if k not in drop}
    if isinstance(x, list):
        return [normalized(v) for v in x]
    return x


def _files(root: Path) -> dict[str, bytes]:
    return {f.relative_to(root).as_posix(): f.read_bytes() for f in root.rglob("*")
            if f.is_file() and not ({"cache", "logs", "__pycache__", "sim_build"} & set(f.relative_to(root).parts))}


def compare_records(committed: Path, replayed: Path) -> tuple[list[str], list[str]]:
    """(files compared, differences) between the committed design and a replayed copy: every file the replay
    rewrote. JSON records are compared normalized; Markdown sheets are renderings of them and are skipped;
    any other file must be equal (line endings aside)."""
    import json as _json
    old, new = _files(committed), _files(replayed)
    seen, diffs = [], []
    for rel in sorted(k for k in new if old.get(k) != new[k]):
        if rel.endswith(".md"):
            continue
        seen.append(rel)
        if rel not in old:
            diffs.append(f"{rel}: written by the replay, not committed")
        elif rel.endswith(".json"):
            if normalized(_json.loads(old[rel])) != normalized(_json.loads(new[rel])):
                diffs.append(f"{rel}: differs from the committed record")
        elif old[rel].replace(b"\r\n", b"\n") != new[rel].replace(b"\r\n", b"\n"):
            diffs.append(f"{rel}: differs from the committed file")
    return seen, diffs


def _has_records(work: Path, stage: str) -> bool:
    """The design ran this stage itself: its records are committed (a design made by `nnc derive` has the
    rules of another design and never ran extract or review)."""
    per_doc = any(work.glob("rules_*.json"))
    return {"extract": per_doc, "review": per_doc and (work / "rules.json").is_file(),
            "contract": (work / "contract.json").is_file()}[stage]


def _replay_stage(d, stage: str) -> tuple[str, list[str]]:
    import shutil
    import tempfile
    from nnc import flow
    from nnc.project import Design
    if not _has_records(d.work, stage):
        return "SKIPPED", [f"the design has no committed record of {stage} (its rules come from another design, "
                           "nnc derive)"]
    tmp = Path(tempfile.mkdtemp(prefix="nnc_replay_"))
    try:
        shutil.copytree(d.root, tmp / d.root.name,
                        ignore=shutil.ignore_patterns("logs", "sim_build", "__pycache__", "runlogs"))
        copy = Design.open(tmp / d.root.name)
        try:
            flow.run_flow(copy, flow.Options(backend="replay"), stage, stage)
        except Exception as e:  # noqa: BLE001
            if "ReplayMiss" in f"{type(e).__name__} {e}" or "no cached answer" in str(e):
                return "NOT_CACHED", [str(e).split(": no cached answer")[0][-120:] + ": no cached answer "
                                      "(the prompt or its inputs changed after the recorded run)"]
            raise
        seen, diffs = compare_records(d.root, copy.root)
        if not seen:
            return "DIFFERENT", ["the replay rewrote no record"]
        return ("SAME" if not diffs else "DIFFERENT"), [f"{len(seen)} records: " + ", ".join(seen[:4])
                                                         + (" ..." if len(seen) > 4 else "")] + diffs
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def replay(d, say=print) -> list[Step]:
    if not (d.work / "cache" / "agents").is_dir():
        return [Step(f"replay {s}", "SKIPPED", 0.0, ["no committed answer cache (work/cache/agents)"])
                for s in REPLAY_STAGES]
    out = []
    for stage in REPLAY_STAGES:
        say(f"[demo] {d.name}: replay {stage} ...")
        s = _timed(f"replay {stage}", lambda: _replay_stage(d, stage))
        say(f"[demo] {d.name}: replay {stage} {s.status} ({s.seconds} s)")
        out.append(s)
    return out


def ok(steps: list[Step]) -> bool:
    """Every step that ran gives the recorded outcome (a stage without a cached answer is reported, not a
    failure), and at least one step ran."""
    return all(s.status in ("SAME", "SKIPPED", "NOT_CACHED") for s in steps) and any(s.status == "SAME" for s in steps)


def to_text(name: str, steps: list[Step]) -> str:
    w = max(len(s.name) for s in steps)
    lines = [f"Demo of {name} (no agent): each step rerun and compared with the recorded outcome", ""]
    for s in steps:
        lines.append(f"  {s.name:<{w}}  {s.status:<10}  {s.seconds:>7.1f} s   {s.lines[0] if s.lines else ''}")
        lines += [f"  {'':<{w}}  {'':<10}  {'':>7}     {x}" for x in s.lines[1:6]]
    lines += ["", f"Result: {'every step gives the recorded outcome' if ok(steps) else 'DIFFERENT (see above)'}",
              f"Report of the design: designs/{name}/work/report.md"]
    return "\n".join(lines)

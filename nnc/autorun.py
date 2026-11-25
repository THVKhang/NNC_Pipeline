"""Drop-in runs: a specification and an RTL in one folder, one command to the report (`nnc run`).

    inbox/<name>/spec/        the IP specification: one file (.md .txt .pdf .docx .html .htm .adoc)
    inbox/<name>/standards/   optional: standards the specification refers to (same formats)
    inbox/<name>/rtl/         the RTL (.sv .v .svh .vh .vhd, sub-folders kept; filelist.f optional)
    inbox/<name>/inbox.json   optional: {"top": "m_x", "tag": "IP", "lib": ["../lib"], "defines": ["X"],
                                         "standard_tags": {"axi.pdf": "AX"},
                                         "config": {"formal": "on", "clock_periods": "clk=10"}}
                              ("config": workspace settings, as `nnc config <name> key=value` sets them)

`nnc run <name>` makes the workspace designs/<name> from the folder (or copies the files again into the one a
previous run made), runs the intake, the adaptation when the intake asks for it, then each stage of the flow.
Nothing here decides anything the flow does not: the stages are those of `nnc flow`.

Gates: by default the run does not wait for them, as `nnc flow --unreviewed` (every artifact and the report are
stamped UNREVIEWED with the bypassed gates, and such a report cannot be signed off). With `gated=True` the run
stops before the first gate that is not approved, and says which review sheet to read.

The steps and their states are written to work/run.json while the run goes on; `nnc ui` shows that file.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

from nnc import costmodel, flow
from nnc.agents.runtime import Budget
from nnc.project import Design, ProjectError

SPEC_EXT = (".md", ".markdown", ".txt", ".pdf", ".docx", ".html", ".htm", ".adoc", ".asciidoc")
RTL_EXT = (".sv", ".v", ".svh", ".vh", ".vhd", ".vhdl", ".f", ".svp", ".vp")
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
RUN_FILE = "run.json"
LOG_FILE = "run.log"
HISTORY_DIR = "run_history"
STATES = ("running", "done", "stopped_at_gate", "stopped_budget", "needs_input", "failed")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check_name(name: str) -> str:
    if not NAME_RE.match(name or ""):
        raise ProjectError(f"invalid name '{name}': letters, digits, '_' or '-', starting with a letter")
    return name


def _files(folder: Path, ext: tuple[str, ...]) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in ext
                  and not any(part.startswith(".") for part in p.relative_to(folder).parts))


def read_inbox(folder: Path) -> dict:
    """What an inbox folder holds, checked: {spec, standards, rtl, config, problems}. `problems` lists what is
    missing or wrong, in words for the person who filled the folder; empty when the folder can run."""
    folder = Path(folder)
    problems = []
    cfg = {}
    if (folder / "inbox.json").is_file():
        try:
            cfg = json.loads((folder / "inbox.json").read_text(encoding="utf-8"))
            if not isinstance(cfg, dict):
                raise ValueError("not a JSON object")
        except ValueError as e:
            problems.append(f"inbox.json is not valid: {e}")
            cfg = {}
    specs = _files(folder / "spec", SPEC_EXT)
    if not specs:
        problems.append("no specification in spec/ (one file: " + " ".join(SPEC_EXT) + ")")
    elif len(specs) > 1:
        problems.append(f"spec/ holds {len(specs)} files; keep the IP specification there and move the "
                        "standards it refers to into standards/")
    rtl = _files(folder / "rtl", RTL_EXT)
    if not [p for p in rtl if p.suffix.lower() != ".f"]:
        problems.append("no RTL in rtl/ (" + " ".join(e for e in RTL_EXT if e != ".f") + ")")
    tag = cfg.get("tag", "IP")
    if not re.match(r"^[A-Z][A-Z0-9]{0,7}$", str(tag)):
        problems.append(f"inbox.json: tag '{tag}' must be 1-8 capital letters or digits, starting with a letter")
    return {"folder": folder, "spec": specs[0] if len(specs) == 1 else None,
            "standards": _files(folder / "standards", SPEC_EXT), "rtl": rtl, "config": cfg, "problems": problems}


def list_inbox(inbox: Path) -> list[str]:
    inbox = Path(inbox)
    if not inbox.is_dir():
        return []
    return sorted(p.name for p in inbox.iterdir() if p.is_dir() and NAME_RE.match(p.name))


# ------------------------------------------------------------------------------------------ run record
class Record:
    """work/run.json of one run: the steps, their state and time, and the outcome."""

    def __init__(self, path: Path, design: str, mode: str, backend: str):
        self.path = path
        self.data = {"design": design, "mode": mode, "backend": backend, "started": _now(), "finished": None,
                     "state": "running", "message": "", "pid": os.getpid(), "steps": []}
        self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.data, indent=1) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    def step(self, name: str, state: str, note: str = "", seconds: float | None = None) -> None:
        steps = self.data["steps"]
        entry = next((s for s in steps if s["name"] == name), None)
        if entry is None:
            entry = {"name": name}
            steps.append(entry)
        entry.update({"state": state, "note": note})
        if seconds is not None:
            entry["seconds"] = round(seconds, 1)
        self.save()

    def finish(self, state: str, message: str = "") -> None:
        assert state in STATES
        self.data.update({"state": state, "message": message, "finished": _now()})
        self.save()
        if self.path.parent.name == "work":   # history: every run kept (ROADMAP 26.3)
            base = stamp(self.data["started"])
            hist = self.path.parent / HISTORY_DIR / f"{base}.json"
            hist.parent.mkdir(exist_ok=True)
            n = 1
            while hist.is_file():   # two runs started within the same second
                n += 1
                hist = hist.with_name(f"{base}-{n}.json")
            hist.write_text(json.dumps(self.data, indent=1) + "\n", encoding="utf-8")


def stamp(iso: str) -> str:
    """A run's start time as a file name: 2026-11-25T14:04:50Z -> 20261125T140450Z."""
    return re.sub(r"[^0-9TZ]", "", str(iso))


def history(design_root: Path) -> list[dict]:
    """Every finished run of a workspace, newest first."""
    folder = Path(design_root) / "work" / HISTORY_DIR
    out = []
    def order(p: Path):  # start time, then the -2, -3 of runs started within the same second
        base, _, n = p.stem.partition("-")
        return base, int(n or 1)
    for p in sorted(folder.glob("*.json"), key=order, reverse=True) if folder.is_dir() else []:
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except ValueError:
            continue
    return out


def read_record(design_root: Path) -> dict | None:
    p = Path(design_root) / "work" / RUN_FILE
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
    except ValueError:
        return None


# ------------------------------------------------------------------------------------------ preparation
def prepare(folder: Path, design_root: Path) -> tuple[Design, dict, list[str]]:
    """Make (or update) the workspace from the inbox folder. Returns the design, the inbox contents and the
    lines that say what was done. Files are copied over the workspace's; nothing of the workspace is removed
    (the adaptation adds library files and a wrapper to rtl/ that the inbox does not hold)."""
    box = read_inbox(folder)
    if box["problems"]:
        raise ProjectError("; ".join(box["problems"]))
    check_name(design_root.name)
    cfg = box["config"]
    done = []
    if (design_root / "nnc_state.json").is_file():
        d = Design.open(design_root)
        done.append(f"workspace {design_root} exists: files copied again")
    else:
        d = Design.init(design_root)
        done.append(f"created workspace {design_root}")
    if cfg.get("top"):
        d.set_config(top=str(cfg["top"]))
    if cfg.get("defines"):
        d.set_config(formal_defines=",".join(str(x) for x in cfg["defines"]))
    extra = cfg.get("config") or {}
    if not isinstance(extra, dict) or "documents" in extra:
        raise ProjectError("inbox.json: 'config' must be an object of workspace settings (as 'nnc config' sets "
                           "them), without 'documents'")
    if extra:
        d.set_config(**{str(k): (None if v in ("", None) else str(v)) for k, v in extra.items()})

    src_rtl = Path(folder) / "rtl"
    for p in box["rtl"]:
        dst = d.root / "rtl" / p.relative_to(src_rtl)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dst)
    done.append(f"{len(box['rtl'])} RTL file(s) -> rtl/")

    docs = d.documents()
    spec = box["spec"]
    old = next((x for x in docs if x["role"] == "ip_spec"), None)
    if old and Path(old["file"]).name != spec.name:
        raise ProjectError(f"the workspace already has the specification {old['file']}; give the new one the "
                           f"same file name, or remove designs/{design_root.name} to start again")
    (d.root / "spec").mkdir(exist_ok=True)
    shutil.copyfile(spec, d.root / "spec" / spec.name)
    if not old:
        d.add_document(f"spec/{spec.name}", "ip_spec", str(cfg.get("tag", "IP")))
    done.append(f"specification {spec.name}")

    tags = dict(cfg.get("standard_tags") or {})
    for i, p in enumerate(box["standards"], 1):
        rel = f"spec/standards/{p.name}"
        (d.root / "spec" / "standards").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, d.root / rel)
        if any(x["file"] == rel for x in d.documents()):
            continue
        used = {x["tag"] for x in d.documents()}
        tag = tags.get(p.name) or next(f"S{n}" for n in range(i, 100) if f"S{n}" not in used)
        d.add_document(rel, "standard", tag)
        done.append(f"standard {p.name} (tag {tag})")
    return d, box, done


# ------------------------------------------------------------------------------------------ the run
def _intake(d: Design, libs: list[Path], adapt: bool) -> dict:
    """`nnc intake` (and `nnc adapt` when asked): the same code as the commands, so that the workspace ends as
    after typing them. Returns work/intake.json."""
    from nnc import cli
    argv = ["--root", str(d.root.parent), "adapt" if adapt else "intake", d.name]
    for lib in libs:
        argv += ["--lib", str(lib)]
    p = d.work / "intake.json"
    p.unlink(missing_ok=True)       # never read the verdict of an earlier run
    code = cli.main(argv)
    if not p.is_file():
        raise ProjectError(f"the {'adaptation' if adapt else 'intake'} stopped (exit code {code}) and wrote no "
                           "work/intake.json; see the log")
    return json.loads(p.read_text(encoding="utf-8"))


def _intake_note(rep: dict) -> str:
    col = rep.get("collect") or {}
    why = [str(x.get("message") if isinstance(x, dict) else x) for x in rep.get("reasons") or []
           if not isinstance(x, dict) or x.get("level") != "note"]
    return f"{rep.get('verdict')}: top {col.get('top')}, {len(rep.get('ports') or [])} ports" + \
        (f" ({'; '.join(why[:3])})" if why else "")


def input_hashes(folder: Path) -> dict[str, str]:
    """One hash per kind of input of an inbox folder: the documents (spec/, standards/, inbox.json) and the
    RTL (rtl/)."""
    folder = Path(folder)
    out = {}
    for kind, parts in (("documents", ("spec", "standards", "inbox.json")), ("rtl", ("rtl",))):
        h = hashlib.sha256()
        for part in parts:
            p = folder / part
            files = [p] if p.is_file() else sorted(x for x in p.rglob("*") if x.is_file()) if p.is_dir() else []
            for f in files:
                h.update(f.relative_to(folder).as_posix().encode() + b"\0" + f.read_bytes() + b"\0")
        out[kind] = h.hexdigest()
    return out


def resume_stage(prev: dict | None, now: dict[str, str]) -> tuple[str | None, str]:
    """The stage a run starts from, and why. A run goes on from where the previous one stopped (a gate, a
    failure, an interruption), so that what a person recorded in between (answers to the open questions, gate
    approvals, a selection of checks) is kept. Changed documents start again from `ingest`; a changed RTL from
    `sim` at the latest (the specification side does not read the RTL). None: nothing to do."""
    if not prev or not prev.get("inputs"):
        return "ingest", "first run"
    if prev["inputs"].get("documents") != now["documents"]:
        return "ingest", "the documents changed"
    stopped = next((s["name"] for s in prev.get("steps") or []
                    if s["name"] in flow.STAGES and s.get("state") in ("waiting", "failed", "running", "budget")),
                   None)
    if prev.get("state") in ("needs_input",) or (prev.get("state") != "done" and stopped is None):
        stopped = "ingest"
    if prev["inputs"].get("rtl") != now["rtl"]:
        start = "sim" if stopped is None else min(stopped, "sim", key=flow.STAGES.index)
        return start, "the RTL changed"
    if stopped is None:
        return None, "nothing changed since the last run, which finished"
    return stopped, f"going on from '{stopped}', where the last run stopped"


def estimate_cost(d: Design, start: str | None) -> dict | None:
    """The agent cost of the stages from `start` on (nnc/costmodel.py), from the tokens of the design's rule
    documents; None when nothing will run or a document cannot be read."""
    if start is None:
        return None
    try:
        tokens = costmodel.document_tokens([d.root / doc["file"] for doc in d.rule_documents()])
    except Exception:  # an unreadable document is reported by the ingest stage, not here
        return None
    stages = [s for s in flow.STAGES[flow.STAGES.index(start):]]
    return costmodel.estimate(tokens, stages)


def run(folder: Path, design_root: Path, options: flow.Options, gated: bool = False,
        prepare_only: bool = False, start: str | None = None, max_cost: float | None = None) -> dict:
    """The whole run; returns work/run.json. Never raises for a failure of a step: the failure is recorded.
    `start`: the first stage of the flow (default: from where the last run stopped, see resume_stage).
    `max_cost`: cap in USD on the model calls of this run (cached answers cost nothing); the run stops with
    state stopped_budget before a call that would start above it, and the next run goes on from that stage."""
    design_root = Path(design_root)
    check_name(design_root.name)
    if start is not None and start not in flow.STAGES:
        raise ProjectError(f"unknown stage {start}: one of {', '.join(flow.STAGES)}")
    options.unreviewed = not gated
    options.budget = budget = Budget(max_cost)
    mode = "gated" if gated else "unreviewed"
    prev = read_record(design_root)
    inputs = input_hashes(folder)
    # the record goes in the workspace; before the workspace exists, in the inbox folder
    rec = Record((design_root / "work" / RUN_FILE) if (design_root / "nnc_state.json").is_file()
                 else Path(folder) / ".run.json", design_root.name, mode, options.backend)
    rec.data["inputs"] = inputs
    if start is None:
        start, why = resume_stage(prev, inputs)
        if prev and prev.get("mode") != mode and start is not None and prev.get("state") != "done":
            why += f" (the last run was {prev.get('mode')})"
    else:
        why = "asked for"
    rec.data.update(start=start, start_reason=why, max_cost_usd=max_cost, cost_usd=0.0)
    rec.save()

    def stage(name, fn):
        t = time.monotonic()
        rec.step(name, "running")
        try:
            note = fn()
            note = note if isinstance(note, str) else ""   # a stage runner may return its data
        except Exception as e:  # recorded, then the run stops
            rec.data["cost_usd"] = round(budget.spent, 4)
            if budget.exceeded:
                rec.step(name, "budget", f"cost cap reached: {e}", time.monotonic() - t)
                raise _Budget() from e
            rec.step(name, "failed", f"{type(e).__name__}: {e}", time.monotonic() - t)
            raise
        rec.data["cost_usd"] = round(budget.spent, 4)
        if budget.exceeded:  # a stage may go on past refused calls; its outputs are then incomplete
            rec.step(name, "budget", "cost cap reached during this stage; it runs again next time",
                     time.monotonic() - t)
            raise _Budget()
        rec.step(name, "done", note, time.monotonic() - t)
        return note

    try:
        holder = {}

        def _prep():
            d, box, done = prepare(folder, design_root)
            holder.update(d=d, box=box)
            return "; ".join(done)
        stage("prepare", _prep)
        d, box = holder["d"], holder["box"]
        if rec.path.parent != d.work:  # move the record into the workspace now that it exists
            old = rec.path
            rec.path = d.work / RUN_FILE
            rec.save()
            old.unlink(missing_ok=True)
        libs = [(Path(folder) / x).resolve() for x in box["config"].get("lib") or []]

        rep = {}

        def _in():
            rep.update(_intake(d, libs, adapt=False))
            if not d.config().get("top") and (rep.get("collect") or {}).get("top"):
                d.set_config(top=rep["collect"]["top"])
            return _intake_note(rep)
        stage("intake", _in)
        if rep.get("verdict") == "adapt":
            def _ad():
                rep.clear()
                rep.update(_intake(d, libs, adapt=True))
                return _intake_note(rep)
            stage("adapt", _ad)
        if rep.get("verdict") != "ready":
            rec.finish("needs_input", "the intake says " + _intake_note(rep) + "; read work/intake.md")
            return rec.data
        rec.data["estimate"] = est = estimate_cost(d, start)
        if prepare_only:
            # an inputs record would make the next run skip ahead; a prepare is not a run of the flow
            rec.data["inputs"] = {}
            rec.finish("done", "inputs ready; no agent was called (prepare only)"
                       + (f"; {costmodel.text(est)}" if est else ""))
            return rec.data
        if start is None:
            rec.finish("done", why + "; nothing run (to run again: --from <stage>)")
            return rec.data
        if est and options.backend == "claude":
            options.say(f"[run] from '{start}': {costmodel.text(est)}"
                        + (f"; cap {max_cost:.2f} USD" if max_cost is not None else "; no cost cap (--max-cost)"))

        for name in flow.STAGES[flow.STAGES.index(start):]:
            if name in flow.DESIGN_STAGES and not d.rtl_generated():
                continue
            gate = flow.GATE_BEFORE.get(name)
            if gate and gated and not d.gate_approved(gate):
                rec.step(name, "waiting", f"{gate} needs review")
                rec.finish("stopped_at_gate", f"stopped before '{name}': {gate} needs review. Read the review "
                           f"sheet, approve with 'nnc gate approve {d.name} {gate} --by <name>', then run again")
                return rec.data
            stage(name, lambda name=name: flow.RUNNERS[name](d, options))
        rep_md = d.work / "report.md"
        rec.finish("done", ("report: work/report.md" if rep_md.is_file() else "finished")
                   + (" (UNREVIEWED: gates were not reviewed)" if not gated else ""))
    except _Budget:
        rec.finish("stopped_budget", f"the cost cap of {max_cost:.2f} USD was reached ({budget.spent:.2f} USD "
                   "spent); the answers paid for are cached: raise the cap (--max-cost) and run again to go on")
    except Exception as e:
        rec.finish("failed", f"{type(e).__name__}: {e}")
    return rec.data


class _Budget(Exception):
    """Internal: the cost cap stopped the run."""

"""Command-line interface: `python -m nnc <command>` (or `nnc <command>` after `pip install -e .`)."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from nnc import __version__
from nnc import flow
from nnc.agents.runtime import make_backend
from nnc.extract import extract, make_batches, stem_of, summarize, write_outputs
from nnc.ingest import IngestError, build_index, save_index
from nnc.project import GATES, Design, ProjectError
from nnc.tools import check_all

DEFAULT_DESIGNS_ROOT = Path("designs")


def _design_path(arg: str, root: Path) -> Path:
    """A bare name means designs/<name>; anything with a path separator is used as given."""
    p = Path(arg)
    return p if len(p.parts) > 1 or p.is_absolute() else root / p


def _open(args) -> Design:
    return Design.open(_design_path(args.design, args.root))


def _options(args) -> flow.Options:
    o = flow.Options(backend=getattr(args, "backend", "claude"), unreviewed=getattr(args, "unreviewed", False),
                     workers=getattr(args, "workers", 4), seed=getattr(args, "seed", 1),
                     mutants=getattr(args, "mutants", 12))
    for stage in ("extract", "review", "contract", "sva", "tests", "triage"):
        v = getattr(args, f"{stage}_model", None)
        if v:
            setattr(o, f"{stage}_model", v)
    return o


# ---------------------------------------------------------------------------------- basic commands
def cmd_doctor(args) -> int:
    checks = check_all()
    width = max(len(c.name) for c in checks)
    for c in checks:
        line = f"[{'OK  ' if c.found else 'MISS'}] {c.name:<{width}}  {c.role:<12}  {c.version or '-'}"
        print(line + (f"   ({c.note})" if c.note else ""))
    if not next(c for c in checks if c.name == "python").found:
        print("RESULT: FAIL - Python version too old")
        return 1
    missing = [c.name for c in checks if c.name in ("verilator", "make", "cocotb") and not c.found]
    if missing:
        print(f"RESULT: simulation tools not on this host ({', '.join(missing)}); on Windows they run in WSL")
        return 1 if args.require_sim else 0
    print("RESULT: PASS")
    return 0


def cmd_init(args) -> int:
    design = Design.init(_design_path(args.design, args.root))
    if args.top:
        design.set_config(top=args.top)
    print(f"created design workspace {design.root}")
    print("next: copy the IP specification to spec/, standards to spec/standards/, the RTL to rtl/, then "
          "'nnc doc add' each document")
    return 0


def cmd_status(args) -> int:
    d = _open(args)
    cfg = d.config()
    print(f"design {d.name}  ({d.root})\n  top: {cfg.get('top', '(not set)')}")
    for doc in d.documents():
        print(f"  doc {doc['tag']:<4} {doc['role']:<8} {doc['file']}" + (f"  sections {doc['sections']}" if doc["sections"] else "")
              + (f"  skip {doc['skip']}" if doc["skip"] else ""))
    for st in d.status():
        print(f"  {st.gate:<18} {st.state:<9} {st.detail}")
    for name, path in (("rules", "rules.md"), ("contract", "contract.md"), ("report", "report.md"), ("triage", "triage.md")):
        if (d.work / path).is_file():
            print(f"  {name:<9} work/{path}")
    return 0


def cmd_gate(args) -> int:
    d = _open(args)
    if args.action == "approve":
        if args.gate == "G1_rules" and (d.work / "rules.json").is_file():
            rules = json.loads((d.work / "rules.json").read_text(encoding="utf-8"))
            undecided = [i for i, q in enumerate(rules.get("questions", []), 1) if not q.get("decision")]
            if undecided:
                print(f"warning: open question(s) {undecided} have no decision; the contract will treat them as open")
        st = d.approve(args.gate, args.by, args.note or "")
        print(f"{st.gate}: {st.state} ({st.detail})")
    else:
        d.revoke(args.gate)
        print(f"{args.gate}: approval revoked")
    return 0


def cmd_answer(args) -> int:
    from nnc import review
    d = _open(args)
    path = d.work / "rules.json"
    if not path.is_file():
        raise ProjectError("no work/rules.json: run 'nnc review' first")
    res = review.record_answer(json.loads(path.read_text(encoding="utf-8")), args.number, args.text, args.by)
    review.write_outputs(res, d.work)
    left = sum(1 for q in res["questions"] if not q.get("decision"))
    print(f"recorded decision for question {args.number}; {left} open question(s) without a decision")
    return 0


def cmd_config(args) -> int:
    d = _open(args)
    values = {}
    for kv in args.values:
        if "=" not in kv:
            raise ProjectError(f"expected key=value, got '{kv}'")
        k, v = kv.split("=", 1)
        values[k.strip()] = v.strip() or None
    cfg = d.set_config(**values) if values else d.config()
    print(json.dumps(cfg, indent=1))
    return 0


def cmd_doc(args) -> int:
    d = _open(args)
    src = Path(args.file)
    if not src.is_file():
        raise ProjectError(f"file not found: {src}")
    folder = "spec" if args.role == "ip_spec" else "spec/standards"
    dst = d.root / folder / src.name
    if src.resolve() != dst.resolve():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    entry = d.add_document(f"{folder}/{src.name}", args.role, args.tag,
                           [s.strip() for s in args.sections.split(",")] if args.sections else None,
                           [s.strip() for s in args.skip.split(",")] if args.skip else None)
    print(f"registered {entry['file']} as {entry['role']} (tag {entry['tag']})")
    return 0


# ------------------------------------------------------------------------------- single-doc tools
def _index_path(design: Design, doc: str) -> Path:
    return design.work / "spec" / f"{stem_of(doc)}.index.json"


def cmd_ingest(args) -> int:
    d = _open(args)
    if not args.file:
        flow.stage_ingest(d, _options(args))
        return 0
    src = Path(args.file)
    if not src.is_file():
        raise ProjectError(f"file not found: {src}")
    try:
        index = build_index(src)
    except IngestError as e:
        raise ProjectError(str(e)) from e
    out = _index_path(d, src.name)
    save_index(index, out)
    st = index["stats"]
    print(f"indexed {src.name}: {st['sections']} sections, {st['sentences']} sentences ({st['normative']} normative), "
          f"{len(index['tables'])} tables, ~{st['chars'] // 4} tokens, {len(index['signals'])} signal names")
    for w in index["warnings"]:
        print(f"  warning: {w}")
    print(f"-> {out}")
    return 0


def cmd_extract(args) -> int:
    d = _open(args)
    if not args.doc:
        if args.dry_run:
            raise ProjectError("--dry-run needs a document name")
        flow.stage_extract(d, _options(args))
        return 0
    idx_file = _index_path(d, args.doc)
    if not idx_file.is_file():
        raise ProjectError(f"no index for '{args.doc}' ({idx_file}); run 'nnc ingest' first")
    index = json.loads(idx_file.read_text(encoding="utf-8"))
    prefixes = [p.strip() for p in args.sections.split(",")] if args.sections else None
    skip = [p.strip() for p in args.skip.split(",")] if args.skip else None
    batches = make_batches(index, prefixes, args.budget, skip)
    print(f"{len(batches)} batches, ~{sum(b.est_tokens for b in batches)} prompt tokens, "
          f"{sum(len(b.normative_ids) for b in batches)} normative sentences")
    if args.dry_run:
        for b in batches:
            print(f"  batch {b.index:3d}  ch {b.chapter:<6} ~{b.est_tokens:5d} tok  {len(b.normative_ids):3d} norm  "
                  f"{','.join(b.section_ids)}")
        return 0
    result = extract(index, make_backend(d.work, args.backend), d.work / "logs" / "agents", prefixes=prefixes,
                     skip=skip, model=args.extract_model or "sonnet", budget_tokens=args.budget, workers=args.workers,
                     gap_fill=not args.no_gap_fill, tag=args.tag)
    suffix = "" if not prefixes else "_sec" + "_".join(p.replace(".", "-").replace(" ", "") for p in prefixes)
    jp, mp = write_outputs(result, d.work, stem_of(args.doc) + suffix)
    print(summarize(result))
    print(f"-> {jp}\n-> {mp}")
    return 1 if result["extraction"]["errors"] else 0


# --------------------------------------------------------------------------------- stage commands
def _stage(name: str):
    def run(args) -> int:
        flow.RUNNERS[name](_open(args), _options(args))
        return 0
    return run


def cmd_plan(args) -> int:
    """Show the checks of the contract, or record the test-plan selection (part of Gate 2)."""
    from nnc import contract as contract_mod
    d = _open(args)
    path = d.work / "contract.json"
    if not path.is_file():
        raise ProjectError("no contract yet: run 'nnc flow <design> --from contract'")
    c = json.loads(path.read_text(encoding="utf-8"))
    if not (args.all or args.select or args.exclude):
        sel = c.get("selection") or {"mode": "all (default, not recorded)"}
        print(f"selection: {sel.get('mode')}" + (f" by {sel['by']}" if sel.get("by") else ""))
        for ch in c["checks"]:
            on = sel.get("mode") != "selected" or ch["id"] in sel["checks"]
            print(f"  [{'x' if on else ' '}] {ch['id']} {ch['kind']:<9} {ch['title']}")
        return 0
    if not args.by:
        raise ProjectError("--by <name> is required to record a selection")
    ids = [x["id"] for x in c["checks"]]
    if args.all:
        chosen = None
    elif args.select:
        chosen = [x.strip() for x in args.select.split(",") if x.strip()]
    else:
        drop = {x.strip() for x in args.exclude.split(",") if x.strip()}
        chosen = [i for i in ids if i not in drop]
    contract_mod.select_checks(c, chosen, args.by, args.reason or "")
    contract_mod.write_outputs(c, d.work)
    n = len(ids) if chosen is None else len(chosen)
    print(f"test plan: {n} of {len(ids)} checks selected by {args.by}; contract.json changed, so G2_contract must be "
          f"approved again (then re-run gen-sva and gen-tests)")
    return 0


def cmd_inject(args) -> int:
    d = _open(args)
    out = Path(args.out) if args.out else d.root / "bug_demo"
    res = flow.run_inject(d, _options(args), Path(args.patch), out, do_triage=not args.no_triage)
    return 0 if res["caught"] else 3


def cmd_cover(args) -> int:
    d = _open(args)
    vals = {k: v for k, v in (("coverage_target", args.target), ("coverage_metric", args.metric),
                              ("coverage_rounds", args.rounds)) if v is not None}
    if vals:
        d.set_config(**{k: str(v) for k, v in vals.items()})
    flow.stage_cover(d, _options(args))
    return 0


def cmd_flow(args) -> int:
    d = _open(args)
    last = flow.run_flow(d, _options(args), args.from_stage, args.to_stage)
    print(f"[flow] last stage completed: {last or '(none)'}")
    return 0


# ---------------------------------------------------------------------------------------- parser
def _agent_args(p) -> None:
    p.add_argument("--backend", choices=("claude", "manual"), default="claude")
    p.add_argument("--workers", type=int, default=4, help="parallel agent calls (default 4)")
    for stage, default in (("extract", "sonnet"), ("review", "sonnet"), ("contract", "opus"), ("sva", "sonnet"),
                           ("tests", "opus"), ("triage", "opus")):
        p.add_argument(f"--{stage}-model", help=f"model alias for {stage} (default {default})")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="nnc", description="Specification-driven RTL verification flow.")
    p.add_argument("--version", action="version", version=f"nnc {__version__}")
    p.add_argument("--root", type=Path, default=DEFAULT_DESIGNS_ROOT,
                   help="folder that holds the design workspaces (default: designs)")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("doctor", help="report the tools the flow needs")
    s.add_argument("--require-sim", action="store_true", help="fail when the simulation tools are missing")
    s.set_defaults(func=cmd_doctor)

    s = sub.add_parser("init", help="create a design workspace")
    s.add_argument("design")
    s.add_argument("--top", help="DUT top module name")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("status", help="show configuration, gates and review sheets of a design")
    s.add_argument("design")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("config", help="show or set configuration values (key=value; key= removes)")
    s.add_argument("design")
    s.add_argument("values", nargs="*")
    s.set_defaults(func=cmd_config)

    s = sub.add_parser("doc", help="register a document of the design")
    s.add_argument("action", choices=("add",))
    s.add_argument("design")
    s.add_argument("file")
    s.add_argument("--role", choices=("ip_spec", "standard"), required=True)
    s.add_argument("--tag", required=True, help="rule ID prefix, e.g. BR for the bridge spec, TL for TL-UL")
    s.add_argument("--sections", help="comma-separated section IDs or title parts to extract (default all)")
    s.add_argument("--skip", help="comma-separated section IDs or title parts to leave out")
    s.set_defaults(func=cmd_doc)

    s = sub.add_parser("answer", help="record the designer's decision on an open question of rules.md (Gate 1)")
    s.add_argument("design")
    s.add_argument("number", type=int, help="question number in rules.md")
    s.add_argument("text", help="the decision")
    s.add_argument("--by", required=True, help="who decided")
    s.set_defaults(func=cmd_answer)

    s = sub.add_parser("gate", help="approve or revoke a gate")
    s.add_argument("action", choices=("approve", "revoke"))
    s.add_argument("design")
    s.add_argument("gate", choices=GATES)
    s.add_argument("--by", default="", help="name of the reviewer (required for approve)")
    s.add_argument("--note", help="review note stored with the approval")
    s.set_defaults(func=cmd_gate)

    s = sub.add_parser("ingest", help="index the design documents (or one file) into sections and sentences")
    s.add_argument("design")
    s.add_argument("file", nargs="?", help="index only this file (default: every registered document)")
    s.set_defaults(func=cmd_ingest)

    s = sub.add_parser("extract", help="extract cited rules (all documents, or one with options)")
    s.add_argument("design")
    s.add_argument("doc", nargs="?", help="file name of one indexed document")
    s.add_argument("--sections")
    s.add_argument("--skip")
    s.add_argument("--tag", default="R")
    s.add_argument("--budget", type=int, default=3500, help="spec tokens per batch (default 3500)")
    s.add_argument("--no-gap-fill", action="store_true")
    s.add_argument("--dry-run", action="store_true", help="show batches and token estimate; call no agent")
    _agent_args(s)
    s.set_defaults(func=cmd_extract)

    for name, helptext in (("review", "review rules: verify, merge duplicates, open questions -> rules.json (G1)"),
                           ("contract", "interface + check plan -> contract.json (G2)"),
                           ("gen-sva", "generate and lint the SVA checkers"),
                           ("gen-tests", "generate the cocotb tests"),
                           ("sim", "integrate the DUT and simulate -> results.json"),
                           ("triage", "analyse failures for the designer -> triage.md"),
                           ("mutate", "mutation testing on a copy of the RTL -> mutation.json"),
                           ("report", "report and RTM -> report.md, rtm.json")):
        s = sub.add_parser(name, help=helptext)
        s.add_argument("design")
        s.add_argument("--unreviewed", action="store_true", help="run past an unapproved gate (results marked UNREVIEWED)")
        s.add_argument("--seed", type=int, default=1)
        s.add_argument("--mutants", type=int, default=12)
        _agent_args(s)
        s.set_defaults(func=_stage(name))

    s = sub.add_parser("plan", help="show the contract checks, or select the checks of the test plan (Gate 2)")
    s.add_argument("design")
    g = s.add_mutually_exclusive_group()
    g.add_argument("--all", action="store_true", help="all applicable checks (recommended)")
    g.add_argument("--select", help="comma-separated check IDs to keep")
    g.add_argument("--exclude", help="comma-separated check IDs to leave out")
    s.add_argument("--by", help="name of the person who decides")
    s.add_argument("--reason", help="why (recorded in the contract)")
    s.set_defaults(func=cmd_plan)

    s = sub.add_parser("inject", help="run the approved verification on a patched copy of the RTL (bug injection)")
    s.add_argument("design")
    s.add_argument("patch", help="unified diff against files of rtl/ (matched by file name)")
    s.add_argument("--out", help="output folder (default designs/<ip>/bug_demo)")
    s.add_argument("--no-triage", action="store_true", help="simulate only")
    s.add_argument("--unreviewed", action="store_true", help="run past an unapproved gate (results marked UNREVIEWED)")
    s.add_argument("--seed", type=int, default=1)
    _agent_args(s)
    s.set_defaults(func=cmd_inject)

    s = sub.add_parser("cover", help="code-coverage baseline, and closure towards a target with new spec-based tests")
    s.add_argument("design")
    s.add_argument("--target", type=float, help="target percentage 0-100 (stored in the design configuration)")
    s.add_argument("--metric", choices=("line", "block", "toggle", "expression", "functional"), help="metric (default line)")
    s.add_argument("--rounds", type=int, help="closure rounds at most (default 5)")
    s.add_argument("--unreviewed", action="store_true", help="run past an unapproved gate (results marked UNREVIEWED)")
    s.add_argument("--seed", type=int, default=1)
    _agent_args(s)
    s.set_defaults(func=cmd_cover)

    s = sub.add_parser("flow", help="run the stages in order, stopping at the first gate that needs review")
    s.add_argument("design")
    s.add_argument("--from", dest="from_stage", choices=flow.STAGES, default="ingest")
    s.add_argument("--to", dest="to_stage", choices=flow.STAGES, default="report")
    s.add_argument("--unreviewed", action="store_true", help="do not stop at gates (exploratory run, marked UNREVIEWED)")
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--mutants", type=int, default=12)
    _agent_args(s)
    s.set_defaults(func=cmd_flow)
    return p


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # never crash on a non-ASCII path on a legacy console
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ProjectError, ValueError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

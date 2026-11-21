"""Command-line interface: `python -m nnc <command>` (or `nnc <command>` after `pip install -e .`)."""
from __future__ import annotations

import argparse
import json
import os
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
                     mutants=getattr(args, "mutants", 12), timeout_s=getattr(args, "agent_timeout", 1800),
                     single=getattr(args, "single_run", False))
    o.rtl_rounds = getattr(args, "rtl_rounds", 3)
    for stage in ("extract", "review", "contract", "sva", "tests", "triage", "rtl"):
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
    if args.host or os.name == "nt":
        from nnc.tools import host_checks
        name, found, problem = host_checks()
        print(f"\nsimulation host: {name}")
        if problem:
            print(f"RESULT: FAIL - {problem}")
            return 1
        width = max([len(c.name) for c in found] + [4])
        for c in found:
            line = f"[{'OK  ' if c.found else 'MISS'}] {c.name:<{width}}  {c.role:<10}  {c.version or '-'}"
            print(line + (f"   ({c.note})" if c.note else ""))
        missing = [c.name for c in found if c.role == "required" and not c.found]
        if missing:
            print(f"RESULT: FAIL - the simulation host lacks {', '.join(missing)}")
            return 1
        optional = [c.name for c in found if c.role != "required" and not c.found]
        print("RESULT: PASS" + (f" (without {', '.join(optional)}: the stages that need them will fail)" if optional else ""))
        return 0
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


def cmd_params(args) -> int:
    """Legal parameter values of the contract; check the run set; choose the configuration (gate D1)."""
    from nnc import params
    d = _open(args)
    path = d.work / "contract.json"
    if not path.is_file():
        raise ProjectError("no contract yet: the parameter table comes from contract.json (G2)")
    c = json.loads(path.read_text(encoding="utf-8"))
    if args.choose is not None:
        doc = params.choose(d.work, c, params.parse_assignments(args.choose), args.by or "", args.note or "",
                            args.accept_unchecked)
        print("final configuration -> work/final_config.json")
        for k, v in doc["values"].items():
            print(f"  {k} = {v}" + ("   (override)" if k in doc["overrides"] else ""))
        for k, n in doc["notes"].items():
            print(f"  note {k}: {n}")
        if d.rtl_generated():
            print(f"next: review and 'nnc gate approve {d.name} D1_config --by <name>'")
        return 0
    if args.check:
        bad = 0
        for label, res in params.check_design(d.root, c):
            state = "ILLEGAL" if res["errors"] else "ok"
            extra = f"  unchecked: {res['unchecked']}" if res["unchecked"] else ""
            print(f"  {label:<24} {state}{extra}")
            for e in res["errors"]:
                print(f"      {e}")
            bad += bool(res["errors"])
        return 1 if bad else 0
    for row in params.table(c["interface"]):
        cons = row["constraint"]
        if cons["kind"] == "set":
            shown = "one of " + ", ".join(map(str, cons["values"]))
        elif cons["kind"] == "range":
            shown = " ".join(x for x in (f"min {cons['min']}" if "min" in cons else "",
                                         f"max {cons['max']}" if "max" in cons else "",
                                         "power of 2" if cons.get("pow2") else "") if x)
        else:
            shown = cons["kind"].upper() if cons["kind"] == "unchecked" else "-"
        dflt = f"= {row['derived']}" if row["derived"] else row["default"]
        print(f"  {row['name']:<28} {str(dflt):<26} {shown}" + (f"   note: {cons['note']}" if cons.get("note") else ""))
    return 0


def cmd_bench(args) -> int:
    from nnc import bench
    d = _open(args)
    ids = [b["id"] for b in bench.load(d.root)]
    tri = set(ids) if args.triage == "all" else set() if args.triage == "none" else \
        {x.strip() for x in args.triage.split(",") if x.strip()}
    only = {x.strip() for x in args.only.split(",")} if args.only else None
    res = bench.run(d, _options(args), triage_ids=tri, only=only)
    return 0 if res["summary"]["caught"] == res["summary"]["bugs"] else 3


def cmd_baseline(args) -> int:
    from nnc import baseline
    from nnc.simhost import default_host
    d = _open(args)
    data = baseline.compare(d.root, default_host(), mutants=not args.no_mutants)
    print(f"[baseline] hand-written {data['baseline_caught']}/{data['total']}, NNC {data['nnc_caught']}/{data['total']}"
          f" -> {d.work / 'baseline.md'}")
    mu = data.get("mutation")
    if mu:
        print(f"[baseline] mutants killed: hand-written {mu['baseline_killed']}/{mu['count']}, NNC {mu['nnc_killed']}/{mu['count']}")
    return 0 if data["clean_pass"] else 1


def cmd_kit_check(args) -> int:
    from nnc import kitcheck
    d = _open(args)
    ok, lines = kitcheck.check(d.root, Path(args.kit) if args.kit else None, args.run)
    print("\n".join(lines))
    return 0 if ok else 1


def cmd_formal_check(args) -> int:
    d = _open(args)
    o = flow.Options(workers=args.workers, single=args.single_run)
    ok, lines = flow.formal_check(d, o, only_config=args.config)
    print("\n".join(lines))
    return 0 if ok else 1


def cmd_fix_verif(args) -> int:
    d = _open(args)
    if args.apply:
        if not args.by:
            raise ProjectError("--apply needs --by <name>: who reviewed the candidate")
        files = flow.fix_verif_apply(d, args.by)
        print(f"applied to verif/: {', '.join(files)}; recorded in NOTICE.md. Gate G3_verif_sources is now STALE: "
              f"review the change and approve it again (nnc gate approve {d.name} G3_verif_sources --by ... --note ...)")
        return 0
    rep = flow.fix_verif(d, _options(args), source=args.source, rounds=args.rounds, run=not args.no_run)
    return 0 if rep["status"] in ("candidate", "nothing", "no_change") else 1


def cmd_mutate_equiv(args) -> int:
    d = _open(args)
    flow.mutate_equiv(d, flow.Options(), depth=args.depth, timeout_s=args.timeout, redo=args.redo)
    return 0


def cmd_stability(args) -> int:
    from nnc import stability
    works = {name: _design_path(name, args.root) / "work" for name in args.designs}
    res = stability.compare(works)
    md = stability.to_markdown(res)
    print(md)
    if args.out:
        Path(args.out).write_text(md + "\n", encoding="utf-8")
        Path(args.out).with_suffix(".json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    return 0


def cmd_summary(args) -> int:
    from nnc import summary
    if args.readme:
        changed = summary.write_readme(Path(args.readme), Path(args.root))
        print(f"{args.readme}: design table {'updated' if changed else 'already up to date'}")
    else:
        print(summary.table(Path(args.root)))
    return 0


def cmd_review_kit(args) -> int:
    from nnc import reviewkit
    d = _open(args)
    req = Path(args.request) if args.request else Path(args.root).resolve().parent / "docs" / "G4_REVIEW_REQUEST.md"
    out = Path(args.out) if args.out else d.root / "review_kit"
    res = reviewkit.build(d.root, d.documents(), out,
                          req.read_text(encoding="utf-8") if req.is_file() else None, make_zip=args.zip)
    print(f"review kit of {d.name}: {res['files']} files in {res['dir']}"
          + (f", {res['zip']}" if res["zip"] else "")
          + f"; {res['questions']} design question(s) from {req if req.is_file() else 'no G4 request (not found)'}"
          + (f"; not included (licence): {', '.join(res['spec_left_out'])}" if res["spec_left_out"] else "")
          + ". Nothing is signed: CHECKLIST.md has an empty decision box.")
    return 0


def cmd_kit(args) -> int:
    d = _open(args)
    files = flow.write_kit(d)
    configs = sorted({f.split("/")[2] for f in files if f.startswith("sim/configs/") and f.count("/") >= 3})
    print(f"rewrote the reproduction kit of {d.name} from work/results.json: {len(files)} files"
          + (f"; configurations {', '.join(configs)} in sim/configs/ (runs in sim/configs/runs.tsv)" if configs else ""))
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


def cmd_restyle(args) -> int:
    """A16 rewrites the RTL to follow docs/RTL_RULES.md; formal equivalence with the original; -> restyle/."""
    from nnc import params, restyle, rtlcheck, sim
    from nnc.simhost import default_host
    d = _open(args)
    o = _options(args)
    c = json.loads((d.work / "contract.json").read_text(encoding="utf-8"))
    rules = json.loads((d.work / "rules.json").read_text(encoding="utf-8"))
    fc = d.work / "final_config.json"
    over = json.loads(fc.read_text(encoding="utf-8")).get("overrides", {}) if fc.is_file() else {}
    values = params.resolve(c["interface"], over)
    rtl = sim.rtl_files(d.root / "rtl")
    original = {f.name: f.read_text(encoding="utf-8", errors="replace") for f in rtl}
    original["filelist.f"] = "\n".join(f.name for f in rtl) + "\n"
    host = default_host()
    orig_chk = rtlcheck.check(host, original, c, values, {r["id"] for r in rules["rules"]}, synth=False)
    rep = restyle.restyle(d.root, c, rules, values, original, flow._backend(d, o), flow._logs(d), host,
                          model=o.rtl_model, rounds=o.rtl_rounds, depth=args.depth)
    restyle.write(d.root, rep, orig_chk, d.name)
    eq = rep["equivalence"]
    print(f"[restyle] {rep['status']} after {rep['attempts']} attempt(s); equivalence {eq.get('status')}; findings "
          f"original {orig_chk['counts']} -> restyled {rep['counts']}; {len(rep['suspected_bugs'])} suspected bug(s); "
          f"US${rep['usage'].get('cost_usd', 0):.2f} -> {d.root / 'restyle' / 'restyle.md'}")
    return 0 if rep["status"] == "clean" else 1


def cmd_spec_check(args) -> int:
    from nnc import specdraft
    d = _open(args)
    if args.file:
        path = Path(args.file)
    else:
        ip = next((x for x in d.documents() if x["role"] == "ip_spec"), None)
        if ip is None:
            raise ProjectError("no ip_spec document registered; give the file")
        path = d.root / ip["file"]
    res = specdraft.check_spec(path, d.config().get("top"))
    print(f"{path.name}: {res.get('sections')} sections, {res['ports']} ports, {res['parameters']} parameters, "
          f"{res['requirements']} requirement IDs, {res.get('normative')} normative sentences")
    for f in res["findings"]:
        print(f"  {f['severity']:<7} {f['message']}")
    return 1 if any(f["severity"] == "error" for f in res["findings"]) else 0


def cmd_spec_lint(args) -> int:
    """A18 lists the gaps of the specification (no change) -> work/spec_lint.md for the G1 reviewer."""
    from nnc import speclint
    d = _open(args)
    docs = [d.root / x["file"] for x in d.documents() if x["role"] == "ip_spec"]
    if not docs:
        raise ProjectError("no ip_spec document registered")
    stds = [d.root / x["file"] for x in d.documents() if x["role"] == "standard"
            and (d.root / x["file"]).suffix.lower() in (".md", ".txt")]
    o = _options(args)
    rep = speclint.lint(d.name, docs, stds, flow._backend(d, o), flow._logs(d), model=args.lint_model)
    (d.work / "spec_lint.json").write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
    (d.work / "spec_lint.md").write_text(speclint.to_markdown(d.name, rep), encoding="utf-8")
    print(f"[spec-lint] {len(rep['gaps'])} gap(s) {rep['by_severity']}, {rep['unsupported']} without a valid "
          f"reference; US${rep['usage'].get('cost_usd', 0):.2f} -> work/spec_lint.md")
    for g in rep["gaps"][:12]:
        print(f"  {g['id']} [{g['severity']}] {g['category']}: {g['scenario'][:140]}")
    return 0


def cmd_spec_draft(args) -> int:
    """A0 drafts the specification from a description; registers it as the ip_spec of a new or empty design."""
    from nnc import specdraft
    path = _design_path(args.design, args.root)
    d = Design.open(path) if (path / "nnc_state.json").is_file() else Design.init(path)
    if any(x["role"] == "ip_spec" for x in d.documents()) and not args.replace:
        raise ProjectError(f"{d.name} already has a specification; pass --replace to draft a new one")
    desc = Path(args.description).read_text(encoding="utf-8")
    top = args.top or d.config().get("top") or f"m_{d.name}"
    d.set_config(top=top, rtl_origin="generated")
    o = _options(args)
    rep = specdraft.draft(desc, d.name, top, flow._backend(d, o), flow._logs(d), d.work / "spec_draft",
                          model=args.spec_model, rounds=args.rounds)
    name = f"{d.name}_Design_Specification.md"
    (d.root / "spec").mkdir(parents=True, exist_ok=True)
    (d.root / "spec" / name).write_text(rep["markdown"].rstrip() + "\n", encoding="utf-8")
    (d.root / "spec" / "design_description.md").write_text(desc, encoding="utf-8")
    d.add_document(f"spec/{name}", "ip_spec", args.tag)
    (d.work / "spec_draft.md").write_text(specdraft.report_md(rep, d.name, f"spec/{name}"), encoding="utf-8")
    c = rep["check"]
    print(f"[spec-draft] spec/{name}: {c.get('ports')} ports, {c.get('parameters')} parameters, {c.get('requirements')} "
          f"requirements; {len(rep['assumptions'])} assumptions, {len(rep['open_questions'])} open questions; "
          f"US${rep['usage'].get('cost_usd', 0):.2f} -> work/spec_draft.md")
    print(f"next: read and correct the draft, then 'nnc flow {d.name}' (ingest .. review, gate G1)")
    return 0


def cmd_export(args) -> int:
    from nnc import export
    d = _open(args)
    out = Path(args.out) if args.out else d.root / "export"
    res = export.export(d.root, d.documents(), [w.strip() for w in args.what.split(",")],
                        [f.strip() for f in args.format.split(",")], out)
    for r in res:
        print(f"  {r['doc']:<9} {r['format']:<5} " + (r.get("path") or f"skipped: {r['skipped']}"))
    if not res:
        print("nothing to export: none of the requested documents exists yet")
    return 0 if res and all("path" in r for r in res) else 1


def cmd_derive(args) -> int:
    from nnc import derive
    d = derive.derive(_design_path(args.source, args.root), _design_path(args.design, args.root))
    print(f"created {d.root} (RTL to be generated; spec, rules, contract and verification from {args.source})")
    for st in d.status():
        print(f"  {st.gate:<18} {st.state:<9} {st.detail[:90]}")
    print(f"next: 'nnc params {d.name} --choose ... --by <name>', approve D1_config, then 'nnc gen-rtl {d.name}'")
    return 0


def cmd_fix_rtl(args) -> int:
    d = _open(args)
    n = flow.stage_fix_rtl(d, _options(args), source=args.source)
    return 0 if n else 1


def cmd_close_loop(args) -> int:
    d = _open(args)
    res = flow.close_loop(d, _options(args), rounds=args.rounds)
    return 0 if res["rounds"] and res["rounds"][-1]["failures"] == 0 else 1


def cmd_rtl_check(args) -> int:
    """Code checks of docs/RTL_RULES.md on the RTL of any design (delivered or generated); nothing is written."""
    from nnc import params, rtlcheck
    from nnc.simhost import default_host
    d = _open(args)
    c = json.loads((d.work / "contract.json").read_text(encoding="utf-8"))
    rules = json.loads((d.work / "rules.json").read_text(encoding="utf-8"))
    files = {f.name: f.read_text(encoding="utf-8", errors="replace") for f in (d.root / "rtl").iterdir()
             if f.suffix in (".sv", ".f")}
    fc = d.work / "final_config.json"
    over = json.loads(fc.read_text(encoding="utf-8")).get("overrides", {}) if fc.is_file() else {}
    res = rtlcheck.check(None if args.source_only else default_host(), files, c, params.resolve(c["interface"], over),
                         {r["id"] for r in rules["rules"]}, synth=not args.no_synth)
    for f in res["findings"]:
        where = f"{f['file']}:{f['line']}" if f["line"] else f["file"]
        print(f"  {f['severity']:<7} {f['rule']} {where} {f['message']}")
    for k, v in (res["synth"].get("corners") or {}).items():
        print(f"  synth {k}: area {v['area_um2']} um^2, longest combinational path {v['comb_delay_ps']} ps (estimate)")
    print(f"RESULT: {res['counts']}; REQ tags on {res['trace']['coverage']} % of the rules")
    return 1 if res["counts"]["error"] else 0


def cmd_flow(args) -> int:
    d = _open(args)
    last = flow.run_flow(d, _options(args), args.from_stage, args.to_stage)
    print(f"[flow] last stage completed: {last or '(none)'}")
    return 0


# ---------------------------------------------------------------------------------------- parser
def _agent_args(p) -> None:
    p.add_argument("--backend", choices=("claude", "manual"), default="claude")
    p.add_argument("--workers", type=int, default=4, help="parallel agent calls (default 4)")
    p.add_argument("--agent-timeout", type=int, default=1800,
                   help="seconds one agent call may take (default 1800; a large test plan may need more)")
    for stage, default in (("extract", "sonnet"), ("review", "sonnet"), ("contract", "opus"), ("sva", "sonnet"),
                           ("tests", "opus"), ("triage", "opus"), ("rtl", "opus")):
        p.add_argument(f"--{stage}-model", help=f"model alias for {stage} (default {default})")
    p.add_argument("--rtl-rounds", type=int, default=3, help="repairs of the generated RTL after the code checks (default 3)")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="nnc", description="Specification-driven RTL verification flow.")
    p.add_argument("--version", action="version", version=f"nnc {__version__}")
    p.add_argument("--root", type=Path, default=DEFAULT_DESIGNS_ROOT,
                   help="folder that holds the design workspaces (default: designs)")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("doctor", help="report the tools the flow needs")
    s.add_argument("--require-sim", action="store_true", help="fail when the simulation tools are missing")
    s.add_argument("--host", action="store_true", help="also probe the simulation host (always on Windows, where "
                                                       "the tools run in WSL)")
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
                           ("gen-env", "formal environment assumptions from the spec (agent A13; config formal=on)"),
                           ("gen-rtl", "RTL from the spec, rules, interface and chosen configuration (agent A15; "
                                       "rtl_origin=generated) -> rtl/, work/rtl_gen.md (D2)"),
                           ("formal", "SymbiYosys on the assertions -> formal.md (config formal=on)"),
                           ("sim", "integrate the DUT and simulate -> results.json"),
                           ("triage", "analyse failures for the designer -> triage.md"),
                           ("mutate", "mutation testing on a copy of the RTL -> mutation.json"),
                           ("report", "report and RTM -> report.md, rtm.json")):
        s = sub.add_parser(name, help=helptext)
        s.add_argument("design")
        s.add_argument("--unreviewed", action="store_true", help="run past an unapproved gate (results marked UNREVIEWED)")
        s.add_argument("--seed", type=int, default=1)
        s.add_argument("--single-run", action="store_true", help="ignore run_set.json: one run of the design configuration")
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

    s = sub.add_parser("params", help="parameter table with legal values; --check the run set; --choose the "
                                      "configuration of the RTL to generate (gate D1_config)")
    s.add_argument("design")
    g = s.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true", help="check defaults, run_set.json and final_config.json")
    g.add_argument("--choose", nargs="*", metavar="NAME=VALUE", help="record work/final_config.json (others: default)")
    s.add_argument("--by", help="who chooses (required with --choose)")
    s.add_argument("--note", help="why (recorded)")
    s.add_argument("--accept-unchecked", action="store_true",
                   help="accept parameters whose legal values are free text the flow cannot check")
    s.set_defaults(func=cmd_params)

    s = sub.add_parser("bench", help="bug benchmark: run the faults of bugs/bugs.json against the approved verification")
    s.add_argument("design")
    s.add_argument("--triage", default="none", help="none (default), all, or comma-separated bug IDs to triage (agent cost)")
    s.add_argument("--only", help="comma-separated bug IDs to run")
    s.add_argument("--unreviewed", action="store_true", help="run past an unapproved gate (results marked UNREVIEWED)")
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--single-run", action="store_true", help="ignore run_set.json: one run of the design configuration")
    _agent_args(s)
    s.set_defaults(func=cmd_bench)

    s = sub.add_parser("baseline", help="run the upstream hand-written testbench (designs/<ip>/baseline) on the bench faults")
    s.add_argument("design")
    s.add_argument("--no-mutants", action="store_true", help="only the bench faults, not the mutants of work/mutation.json")
    s.set_defaults(func=cmd_baseline)

    s = sub.add_parser("kit-check", help="compare a run of the reproduction kit (designs/<ip>/sim) with the recorded results")
    s.add_argument("design")
    s.add_argument("--kit", help="kit folder holding results.xml and sim.log (default designs/<ip>/sim, or the "
                                 "folder of --run)")
    s.add_argument("--run", help="compare with this recorded run of the run set (a label of sim/configs/runs.tsv, "
                                 "e.g. min.s2) instead of the primary run")
    s.set_defaults(func=cmd_kit_check)

    s = sub.add_parser("formal-check", help="run formal again with the recorded configuration (no agent, writes "
                                            "nothing) and compare every check with work/formal.json (used by CI)")
    s.add_argument("design")
    s.add_argument("--workers", type=int, default=4, help="parallel SymbiYosys checks (default 4)")
    s.add_argument("--single-run", action="store_true", help="ignore run_set.json (only if the recorded run did)")
    s.add_argument("--config", help="run one formal configuration of the run set and compare it alone (to split "
                                    "a long rerun over several CI jobs)")
    s.set_defaults(func=cmd_formal_check)

    s = sub.add_parser("fix-verif", help="agent A17 (no RTL) corrects the checkers/tests where triage judged the "
                                         "verification wrong (B) -> candidate in work/verif_fix/; --apply copies it "
                                         "into verif/ and G3 must be approved again")
    s.add_argument("design")
    s.add_argument("--from", dest="source", choices=["sim", "formal", "all"], default="sim",
                   help="triage to read: work/triage.json (sim), work/formal_triage.json (formal) or both")
    s.add_argument("--rounds", type=int, default=2, help="new attempts after a refused (weakening) answer (default 2)")
    s.add_argument("--no-run", action="store_true", help="do not simulate the candidate")
    s.add_argument("--apply", action="store_true", help="copy the reviewed candidate into verif/ (G3 becomes STALE)")
    s.add_argument("--by", help="who reviewed the candidate (with --apply)")
    s.add_argument("--unreviewed", action="store_true", help="run past an unapproved gate (results marked UNREVIEWED)")
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--single-run", action="store_true", help="ignore run_set.json when simulating the candidate")
    _agent_args(s)
    s.set_defaults(func=cmd_fix_verif)

    s = sub.add_parser("mutate-equiv", help="formal equivalence of each surviving mutant with the RTL (Yosys miter, "
                                            "no agent): PROVEN equivalent, or CEX with the first differing outputs")
    s.add_argument("design")
    s.add_argument("--depth", type=int, help="BMC depth (default: config formal_depth, else 20)")
    s.add_argument("--timeout", type=int, default=900, help="seconds per SymbiYosys task (default 900)")
    s.add_argument("--redo", action="store_true", help="check every surviving mutant again (default: keep the "
                                                       "conclusions of a run with the same depth and frontend)")
    s.set_defaults(func=cmd_mutate_equiv)

    s = sub.add_parser("kit", help="rewrite the reproduction kit designs/<ip>/sim (and sim/configs/ for a run set) "
                                   "from the recorded results, without simulating")
    s.add_argument("design")
    s.set_defaults(func=cmd_kit)

    s = sub.add_parser("review-kit", help="collect what a G4 reviewer needs for one design into one folder (and a "
                                          ".zip): packet, report, evidence, spec, RTL, verification, kit, CHECKLIST.md")
    s.add_argument("design")
    s.add_argument("--out", help="output folder (default designs/<ip>/review_kit)")
    s.add_argument("--zip", action="store_true", help="also write <out>.zip")
    s.add_argument("--request", help="the G4 request with the design questions (default docs/G4_REVIEW_REQUEST.md "
                                     "next to the designs folder)")
    s.set_defaults(func=cmd_review_kit)

    s = sub.add_parser("summary", help="the table of every design (tests, checks, formal, mutation, G4) from the "
                                       "committed results; --readme rewrites the table block in README.md")
    s.add_argument("--readme", help="README.md to update in place (between the nnc-summary markers)")
    s.set_defaults(func=cmd_summary)

    s = sub.add_parser("stability", help="agreement of repeated runs on one specification: rules and checks "
                                         "compared through the specification sentences they cite (no agent)")
    s.add_argument("designs", nargs="+", help="two or more design folders made from the same specification")
    s.add_argument("--out", help="write the table to this .md (and the numbers to .json)")
    s.set_defaults(func=cmd_stability)

    s = sub.add_parser("inject", help="run the approved verification on a patched copy of the RTL (bug injection)")
    s.add_argument("design")
    s.add_argument("patch", help="unified diff against files of rtl/ (matched by file name)")
    s.add_argument("--out", help="output folder (default designs/<ip>/bug_demo)")
    s.add_argument("--no-triage", action="store_true", help="simulate only")
    s.add_argument("--unreviewed", action="store_true", help="run past an unapproved gate (results marked UNREVIEWED)")
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--single-run", action="store_true", help="ignore run_set.json: one run of the design configuration")
    _agent_args(s)
    s.set_defaults(func=cmd_inject)

    s = sub.add_parser("cover", help="code-coverage baseline, and closure towards a target with new spec-based tests")
    s.add_argument("design")
    s.add_argument("--target", type=float, help="target percentage 0-100 (stored in the design configuration)")
    s.add_argument("--metric", choices=("line", "block", "toggle", "expression", "functional"), help="metric (default line)")
    s.add_argument("--rounds", type=int, help="closure rounds at most (default 5)")
    s.add_argument("--unreviewed", action="store_true", help="run past an unapproved gate (results marked UNREVIEWED)")
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--single-run", action="store_true", help="ignore run_set.json: one run of the design configuration")
    _agent_args(s)
    s.set_defaults(func=cmd_cover)

    s = sub.add_parser("restyle", help="rewrite the RTL to follow docs/RTL_RULES.md, formally equivalent to the "
                                       "original (agent A16) -> restyle/ (rtl/ untouched)")
    s.add_argument("design")
    s.add_argument("--depth", type=int, default=20, help="equivalence BMC depth (default 20)")
    _agent_args(s)
    s.set_defaults(func=cmd_restyle)

    s = sub.add_parser("spec-check", help="can the flow read this specification? (sections, port and parameter "
                                          "tables, legal values, requirement IDs)")
    s.add_argument("design")
    s.add_argument("file", nargs="?", help="a specification file (default: the registered ip_spec)")
    s.set_defaults(func=cmd_spec_check)

    s = sub.add_parser("spec-lint", help="agent A18 lists what the specification leaves open (same-cycle events, "
                                         "requests while busy, reset mid-sequence, extremes) -> work/spec_lint.md (G1)")
    s.add_argument("design")
    s.add_argument("--lint-model", default="opus", help="model alias for A18 (default opus)")
    _agent_args(s)
    s.set_defaults(func=cmd_spec_lint)

    s = sub.add_parser("spec-draft", help="draft a specification in the shape of docs/SPEC_TEMPLATE.md from a design "
                                          "description (agent A0); creates the design if needed (RTL generated)")
    s.add_argument("design")
    s.add_argument("description", help="Markdown or text file: what the block must do")
    s.add_argument("--top", help="top module name (default m_<design>)")
    s.add_argument("--tag", default="SP", help="rule ID prefix for the specification (default SP)")
    s.add_argument("--spec-model", default="opus")
    s.add_argument("--rounds", type=int, default=2, help="repairs after the shape check (default 2)")
    s.add_argument("--replace", action="store_true", help="replace an existing specification")
    _agent_args(s)
    s.set_defaults(func=cmd_spec_draft)

    s = sub.add_parser("export", help="export the specification and reports to DOCX, HTML and PDF -> <design>/export")
    s.add_argument("design")
    s.add_argument("--what", default="spec,rules,contract,rtl,report,packet",
                   help="comma-separated: spec, rules, contract, rtl, report, packet, triage")
    s.add_argument("--format", default="docx,html,pdf", help="comma-separated: docx, html, pdf")
    s.add_argument("--out", help="output folder (default designs/<ip>/export)")
    s.set_defaults(func=cmd_export)

    s = sub.add_parser("derive", help="new workspace whose RTL the flow generates, from a verified design "
                                      "(spec, rules, contract, verification and approvals carried; RTL left behind)")
    s.add_argument("source")
    s.add_argument("design")
    s.set_defaults(func=cmd_derive)

    s = sub.add_parser("fix-rtl", help="repair the generated RTL from the faults triage judged A (agent A15; "
                                       "spec-level fault text only, never the tests)")
    s.add_argument("design")
    s.add_argument("--from", dest="source", choices=["sim", "formal", "all"], default="sim",
                   help="which triage to repair from: simulation (default), formal counterexamples, or both")
    s.add_argument("--unreviewed", action="store_true", help="run past an unapproved gate (results marked UNREVIEWED)")
    _agent_args(s)
    s.set_defaults(func=cmd_fix_rtl)

    s = sub.add_parser("close-loop", help="generated RTL: sim -> triage -> fix-rtl until clean or the repair budget")
    s.add_argument("design")
    s.add_argument("--rounds", type=int, default=3, help="RTL repairs at most (default 3)")
    s.add_argument("--unreviewed", action="store_true", help="run past an unapproved gate (results marked UNREVIEWED)")
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--single-run", action="store_true", help="ignore run_set.json: one run of the design configuration")
    _agent_args(s)
    s.set_defaults(func=cmd_close_loop)

    s = sub.add_parser("rtl-check", help="code checks of docs/RTL_RULES.md on the RTL (lint, structure, ports, synthesis)")
    s.add_argument("design")
    s.add_argument("--source-only", action="store_true", help="text checks only (no Verilator/Yosys)")
    s.add_argument("--no-synth", action="store_true", help="skip synthesis")
    s.set_defaults(func=cmd_rtl_check)

    s = sub.add_parser("flow", help="run the stages in order, stopping at the first gate that needs review")
    s.add_argument("design")
    s.add_argument("--from", dest="from_stage", choices=flow.STAGES, default="ingest")
    s.add_argument("--to", dest="to_stage", choices=flow.STAGES, default="report")
    s.add_argument("--unreviewed", action="store_true", help="do not stop at gates (exploratory run, marked UNREVIEWED)")
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--single-run", action="store_true", help="ignore run_set.json: one run of the design configuration")
    s.add_argument("--mutants", type=int, default=12)
    _agent_args(s)
    s.set_defaults(func=cmd_flow)
    return p


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # never crash on a non-ASCII path on a legacy console
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    from nnc.simhost import HostError
    try:
        return args.func(args)
    except HostError as e:
        print(f"host error: {e}", file=sys.stderr)
        return 3
    except (ProjectError, ValueError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

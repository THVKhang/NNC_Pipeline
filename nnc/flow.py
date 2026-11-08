"""Stage functions of the flow and the gated sequence (`nnc flow`).

    ingest -> extract -> review  ==G1==>  contract  ==G2==>  gen-sva, gen-tests  ==G3==>
    sim (+ test-infrastructure repair) -> triage -> mutate -> report  ==G4==> sign-off

Each stage reads and writes files in the design workspace, so any stage can be re-run alone; the
answer cache makes a re-run free when nothing changed. A stage behind a gate refuses to run until
the gate is approved, unless `unreviewed=True`: then the bypassed gates are written into every
artifact and the report is marked UNREVIEWED.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from nnc import contract as contract_mod
from nnc import extract as extract_mod
from nnc import closure, gen_cov, gen_sva, gen_tests, mutate, report, review, sim, triage
from nnc.agents.runtime import make_backend
from nnc.ingest import build_index, save_index
from nnc.project import Design, ProjectError
from nnc.simhost import default_host

STAGES = ("ingest", "extract", "review", "contract", "gen-sva", "gen-tests", "sim", "cover", "triage", "mutate",
          "report")
GATE_BEFORE = {"contract": "G1_rules", "gen-sva": "G2_contract", "gen-tests": "G2_contract", "sim": "G3_verif_sources",
               "cover": "G3_verif_sources", "triage": "G3_verif_sources", "mutate": "G3_verif_sources", "report": "G3_verif_sources"}


@dataclass
class Options:
    backend: str = "claude"
    unreviewed: bool = False
    extract_model: str = "sonnet"
    review_model: str = "sonnet"
    contract_model: str = "opus"
    sva_model: str = "sonnet"
    tests_model: str = "opus"
    triage_model: str = "opus"
    workers: int = 4
    seed: int = 1
    mutants: int = 12
    repair_rounds: int = 2
    timeout_s: int = 1800
    log: list[str] = field(default_factory=list)

    def say(self, msg: str) -> None:
        self.log.append(msg)
        print(msg, flush=True)


def _read(path: Path) -> dict:
    if not path.is_file():
        raise ProjectError(f"missing {path.name}: run the stage that produces it first")
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def index_path(d: Design, doc: dict) -> Path:
    return d.work / "spec" / f"{extract_mod.stem_of(doc['file'])}.index.json"


def _backend(d: Design, o: Options):
    return make_backend(d.work, o.backend, o.timeout_s)


def _logs(d: Design) -> Path:
    return d.work / "logs" / "agents"


def _gate(d: Design, stage: str, o: Options) -> list[str]:
    gate = GATE_BEFORE.get(stage)
    return d.require_gate(gate, o.unreviewed) if gate else []


# ------------------------------------------------------------------------------------------ stages
def stage_ingest(d: Design, o: Options) -> None:
    docs = d.documents()
    if not docs:
        raise ProjectError("no documents registered: use 'nnc doc add <design> <file> --role ip_spec --tag XX'")
    for doc in docs:
        src = d.root / doc["file"]
        idx = build_index(src)
        save_index(idx, index_path(d, doc))
        st = idx["stats"]
        o.say(f"[ingest] {doc['tag']} {src.name}: {st['sections']} sections, {st['sentences']} sentences, "
              f"{st['normative']} normative, {len(idx['tables'])} tables" + (f", {len(idx['warnings'])} warnings" if idx["warnings"] else ""))


def stage_extract(d: Design, o: Options) -> None:
    backend = _backend(d, o)
    for doc in d.documents():
        idx = _read(index_path(d, doc))
        res = extract_mod.extract(idx, backend, _logs(d), prefixes=doc["sections"] or None, skip=doc["skip"] or None,
                                  model=o.extract_model, workers=o.workers, tag=doc["tag"])
        extract_mod.write_outputs(res, d.work, extract_mod.stem_of(doc["file"]))
        o.say(f"[extract] {doc['tag']}: " + extract_mod.summarize(res).replace("\n", " | "))
        if res["extraction"]["errors"]:
            raise ProjectError(f"extraction errors for {doc['file']}: {res['extraction']['errors'][:2]}")


def stage_review(d: Design, o: Options) -> None:
    files = [d.work / f"rules_{extract_mod.stem_of(doc['file'])}.json" for doc in d.documents()]
    rules, sources = review.load_raw_rules(d.work, files)
    backend = _backend(d, o)
    res = review.review(rules, backend, _logs(d), model=o.review_model, workers=o.workers, sources=sources)
    res = review.resolve_questions(res, [_read(index_path(d, doc)) for doc in d.documents()], backend, _logs(d),
                                   model=o.review_model)
    review.write_outputs(res, d.work)
    o.say("[review] " + review.summarize(res).replace("\n", " | "))
    if res["review"]["errors"]:
        raise ProjectError(f"review errors: {res['review']['errors'][:2]}")


def stage_contract(d: Design, o: Options) -> None:
    bypass = _gate(d, "contract", o)
    ip = next((x for x in d.documents() if x["role"] == "ip_spec"), None)
    if ip is None:
        raise ProjectError("no ip_spec document registered")
    top = d.config().get("top")
    if not top:
        raise ProjectError("set the DUT top module: nnc config <design> top=<module>")
    iface = contract_mod.extract_interface(_read(index_path(d, ip)))
    c = contract_mod.plan(_read(d.work / "rules.json"), iface, top, _backend(d, o), _logs(d), model=o.contract_model,
                          unreviewed_gates=bypass)
    contract_mod.write_outputs(c, d.work)
    o.say("[contract] " + contract_mod.summarize(c).replace("\n", " | "))


def stage_gen_sva(d: Design, o: Options) -> None:
    _gate(d, "gen-sva", o)
    rep = gen_sva.generate(contract_mod.selected(_read(d.work / "contract.json")), _read(d.work / "rules.json"), _backend(d, o), _logs(d),
                           default_host(), d.root / "verif" / "sva", model=o.sva_model)
    _write(d.work / "gen_sva.json", rep)
    for m in rep["modules"]:
        o.say(f"[gen-sva] {m['module']}: {len(m['checks'])} checks, {m['status']} after {m['attempts']} attempt(s)"
              + (f" PROBLEMS {m['problems'][:3]} {m['lint_errors'][:300]}" if m["status"] == "failed" else ""))
    cov = gen_cov.generate(contract_mod.selected(_read(d.work / "contract.json")), _read(d.work / "rules.json"), _backend(d, o), _logs(d),
                           default_host(), d.root / "verif" / "sva", model=o.sva_model)
    _write(d.work / "gen_cov.json", cov)
    o.say(f"[gen-sva] {cov['module']}: {len(cov['points'])} functional cover points, {cov['status']} after "
          f"{cov['attempts']} attempt(s)" + (f" PROBLEMS {cov['problems'][:3]} {cov['lint_errors'][:300]}"
                                             if cov["status"] == "failed" else ""))


def test_file(d: Design) -> Path:
    return d.root / "verif" / "tests" / f"test_{d.name}.py"


def test_files(d: Design) -> list[Path]:
    """The generated test module, then the coverage-closure modules (one per closure round)."""
    return [test_file(d)] + sorted((d.root / "verif" / "tests").glob(f"test_{d.name}_cov*.py"))


def test_map(d: Design) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for f in test_files(d):
        if f.is_file():
            out.update(gen_tests.test_check_map(f.read_text(encoding="utf-8")))
    return out


def stage_gen_tests(d: Design, o: Options) -> None:
    _gate(d, "gen-tests", o)
    rep = gen_tests.generate(contract_mod.selected(_read(d.work / "contract.json")), _read(d.work / "rules.json"), _backend(d, o), _logs(d),
                             test_file(d), model=o.tests_model)
    _write(d.work / "gen_tests.json", rep)
    o.say(f"[gen-tests] {rep['file']}: {rep['status']} after {rep['attempts']} attempt(s)"
          + (f" PROBLEMS {rep['problems'][:4]}" if rep["problems"] else ""))


def _summ_sim(r: dict) -> str:
    if r.get("status") != "ran":
        return f"{r.get('status')}: {r.get('integration', {}).get('issues') or r.get('build_errors', [])[:5]}"
    t: dict[str, int] = {}
    for x in r["tests"]:
        t[x["status"]] = t.get(x["status"], 0) + 1
    a = r["assertions"]
    return (f"tests {t}; assertions {len(a)}: failing {sum(v['fails'] > 0 for v in a.values())}, never hit "
            f"{sum(v['hits'] == 0 for v in a.values())}; line coverage {r['coverage'].get('percent')} %")


def _periods(d: Design) -> dict[str, int]:
    """Design configuration clock_periods ("i_clk_rd=20,i_clk_wr=10"; ns, default 10 each)."""
    return sim.parse_periods(d.config().get("clock_periods"))


def stage_sim(d: Design, o: Options) -> None:
    _gate(d, "sim", o)
    contract = _read(d.work / "contract.json")
    host = default_host()
    res = sim.run(host, contract, d.root / "rtl", d.root / "verif" / "sva", test_files(d), seed=o.seed,
                  clock_periods=_periods(d))
    o.say("[sim] " + _summ_sim(res))
    for rnd in range(1, o.repair_rounds + 1):
        lib = gen_tests.library_errors(res) if res.get("status") == "ran" else []
        if lib:
            o.say(f"[sim] {len(lib)} test(s) failed inside the helper library nnc_cocotb: a fault of the flow, "
                  f"not of the tests; no repair attempted. First: {lib[0][:300]}")
            break
        errs = gen_tests.infrastructure_errors(res) if res.get("status") == "ran" else []
        errs = [e for e in errs if not e.startswith("test_cov_")]      # closure modules are not repaired here
        if not errs:
            break
        o.say(f"[sim] {len(errs)} test(s) raised Python errors in the test code; repair round {rnd} (no RTL, no failed checks sent)")
        rep = gen_tests.repair(contract_mod.selected(contract), _read(d.work / "rules.json"), _backend(d, o), _logs(d), test_file(d), errs,
                               model=o.tests_model, round_no=rnd)
        o.say(f"[sim] repair: {rep['status']}")
        res = sim.run(host, contract, d.root / "rtl", d.root / "verif" / "sva", test_files(d), seed=o.seed,
                      clock_periods=_periods(d))
        o.say("[sim] " + _summ_sim(res))
    _save_sim(d, res)


def _write_kit(d: Design, contract: dict, params: dict | None) -> None:
    """designs/<ip>/sim/: Makefile and inputs that reproduce the regression without NNC."""
    kit = sim.kit_files(contract, sim.rtl_files(d.root / "rtl"), sim.checker_files(d.root / "verif" / "sva"),
                        test_files(d), params if params is not None else sim.param_values(contract), _periods(d))
    for rel, text in kit.items():
        p = d.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))


def _save_sim(d: Design, res: dict) -> None:
    if (d.work / "contract.json").is_file():
        _write_kit(d, _read(d.work / "contract.json"), res.get("params"))
    res["unreviewed_gates"] = d.require_gate("G3_verif_sources", True)
    out = Path(res.pop("out_dir", "")) if res.get("out_dir") else None
    _write(d.work / "results.json", res)
    if out and (out / "sim.log").is_file():
        (d.work / "sim").mkdir(exist_ok=True)
        (d.work / "sim" / "sim.log").write_text((out / "sim.log").read_text(encoding="utf-8", errors="replace"),
                                                encoding="utf-8")


def _coverage_line(res: dict) -> str:
    m = (res.get("coverage") or {}).get("metrics") or {}
    return ", ".join(f"{k} {v['percent']} % ({v['hit']}/{v['total']})" for k, v in m.items() if v.get("total")) or "not measured"


def stage_cover(d: Design, o: Options) -> None:
    """Coverage closure towards the designer's target (config coverage_target / coverage_metric /
    coverage_rounds). Without a target it only shows the measured baseline."""
    _gate(d, "cover", o)
    cfg = d.config()
    results = _read(d.work / "results.json")
    o.say(f"[cover] baseline: {_coverage_line(results)}")
    target = cfg.get("coverage_target")
    metric = cfg.get("coverage_metric", "line")
    rounds = int(cfg.get("coverage_rounds", 5))
    cov = {"metric": metric, "target": float(target) if target not in (None, "") else None,
           "baseline": closure.baseline(results, metric), "rounds": [], "unreachable": [], "dropped": [],
           "prompt_version": closure.PROMPT_VERSION}
    prev_path = d.work / "coverage.json"
    if prev_path.is_file():
        prev = _read(prev_path)
        if prev.get("metric") == metric:
            cov.update({k: prev.get(k, []) for k in ("rounds", "unreachable", "dropped")})
            cov["baseline"] = prev.get("baseline") or cov["baseline"]

    def finish(status: str, note: str = "") -> None:
        cov["status"] = status
        cov["final"] = closure.baseline(results, metric)
        _write(prev_path, cov)
        points = ({p["id"]: p for p in _read(d.work / "gen_cov.json")["points"]}
                  if (d.work / "gen_cov.json").is_file() else {})
        (d.work / "coverage.md").write_text(closure.to_markdown(cov, _read(d.work / "results.json"), points),
                                            encoding="utf-8")
        o.say(f"[cover] {status}{': ' + note if note else ''} -> work/coverage.md")

    if cov["target"] is None:
        return finish("not_requested", f"set a target after reading the baseline: nnc config {d.name} "
                      f"coverage_target=<0-100> coverage_metric=<{'|'.join(closure.METRICS)}>")
    if metric not in closure.METRICS or closure.baseline(results, metric) is None:
        return finish("not_supported", f"metric {metric} is not measured by this simulator run")
    bad = closure.functional_failures(results)
    if bad:
        return finish("stopped_failure", f"functional failures {bad[:5]} must be resolved first (triage)")
    contract, rules_doc = contract_mod.selected(_read(d.work / "contract.json")), _read(d.work / "rules.json")
    rtl = sim.rtl_files(d.root / "rtl")
    public = "\n".join((d.root / doc["file"]).read_text(encoding="utf-8", errors="replace") for doc in d.documents()
                       if (d.root / doc["file"]).suffix.lower() in (".md", ".txt"))
    public += json.dumps(contract) + json.dumps(rules_doc)
    private = closure.rtl_private_names(rtl, public)
    backend, usage, no_gain = _backend(d, o), closure.Usage(), 0
    start = len(test_files(d))                      # closure modules already present + 1
    for rnd in range(start, start + rounds):
        cur = closure.baseline(results, metric)
        if cur["percent"] is not None and cur["percent"] >= cov["target"]:
            break
        files: dict[str, Path] = {"contract.json": d.work / "contract.json", "rules.json": d.work / "rules.json"}
        for doc in d.documents():
            files[f"spec/{Path(doc['file']).name}"] = d.root / doc["file"]
        if metric == "functional":          # cover points come from the specification: no RTL needed
            titles = {p["id"]: p for p in _read(d.work / "gen_cov.json")["points"]} if (d.work / "gen_cov.json").is_file() else {}
            for u in (results.get("coverage") or {}).get("uncovered", []):
                if u["metric"] == "functional" and u["what"] in titles:
                    t = titles[u["what"]]
                    u["detail"] = [f"{t['title']}: {t['condition']}"]
        else:
            for f in rtl:
                files[f"rtl/{f.name}"] = f
        for f in test_files(d):
            files[f"verif/tests/{f.name}"] = f
        prev_sc = [s for r in cov["rounds"] for s in r.get("scenarios", [])]
        an = closure.analyse(results, metric, files, backend, _logs(d), rnd, o.triage_model, prev_sc)
        usage.add(an["result"])
        pts = {p["n"]: p for p in an["points"]}
        for u in an["output"]["unreachable"]:
            cov["unreachable"].append({"round": rnd, "rules": u["rules"], "reason": u["reason"],
                                       "where": [f"{pts[n]['file']}:{pts[n]['line']} {pts[n]['what']}".strip()
                                                 for n in u["points"] if n in pts]})
        keep = []
        for s in an["output"]["scenarios"]:
            lk = closure.leaks(s["stimulus"], private)
            if lk:
                cov["dropped"].append({"round": rnd, "id": s["id"], "leaks": lk})
            else:
                keep.append(s)
        entry = {"round": rnd, "scenarios": keep, "tests": []}
        cov["rounds"].append(entry)
        if not keep:
            entry["note"] = "no scenario with legal, specification-level stimulus"
            o.say(f"[cover] round {rnd}: no usable scenario ({len(an['output']['unreachable'])} unreachable claims)")
            break
        code, problems = closure.write_tests(contract, rules_doc, keep, test_file(d), backend, _logs(d), rnd,
                                             o.tests_model, usage)
        if problems:
            entry["note"] = f"closure module invalid: {problems[:3]}"
            o.say(f"[cover] round {rnd}: {entry['note']}")
            break
        mod = d.root / "verif" / "tests" / f"test_{d.name}_cov{rnd}.py"
        mod.write_text(code, encoding="utf-8")
        entry["tests"] = sorted(n for n in gen_tests.test_check_map(code))
        res = sim.run(default_host(), contract, d.root / "rtl", d.root / "verif" / "sva", test_files(d),
                      seed=o.seed, clock_periods=_periods(d))
        o.say(f"[cover] round {rnd}: {len(keep)} scenarios, {len(entry['tests'])} tests -> {_summ_sim(res)}")
        new = closure.baseline(res, metric) if res.get("status") == "ran" else None
        entry.update({k: (new or {}).get(k) for k in ("percent", "hit", "total")})
        results = res if res.get("status") == "ran" else results
        _save_sim(d, dict(res))
        if res.get("status") != "ran" or closure.functional_failures(res):
            entry["note"] = "functional failure: verification finding, see triage"
            cov["usage"] = usage.as_dict()
            return finish("stopped_failure", f"{closure.functional_failures(res)[:5]}")
        gained = (new or {}).get("hit", 0) - (cur or {}).get("hit", 0)
        no_gain = no_gain + 1 if gained <= 0 else 0
        if no_gain >= 2:
            entry["note"] = "two rounds without gain"
            break
    cov["usage"] = usage.as_dict()
    fin = closure.baseline(results, metric)
    met = fin and fin["percent"] is not None and fin["percent"] >= cov["target"]
    finish("target_met" if met else "target_unmet",
           f"{metric} {fin and fin['percent']} % for target {cov['target']} %; new modules change verif/: "
           f"approve G3_verif_sources again" if cov["rounds"] else "")


def run_inject(d: Design, o: Options, patch: Path, out: Path, do_triage: bool = True) -> dict:
    """Run the approved checkers and tests on a patched COPY of the RTL (nnc inject) and triage the
    failures. Answers "would the flow catch this bug?" with evidence; rtl/ is never touched."""
    from nnc import inject
    _gate(d, "sim", o)
    contract = _read(d.work / "contract.json")
    out.mkdir(parents=True, exist_ok=True)
    changed = inject.make_copy(d.root / "rtl", patch.read_text(encoding="utf-8"), out / "rtl")
    (out / "injected_bug.diff").write_bytes(patch.read_bytes())
    res = sim.run(default_host(), contract, out / "rtl", d.root / "verif" / "sva", test_files(d), seed=o.seed,
                  clock_periods=_periods(d))
    o.say(f"[inject] patched {changed} -> {_summ_sim(res)}")
    log = Path(res.pop("out_dir", "")) if res.get("out_dir") else None
    res["unreviewed_gates"] = d.require_gate("G3_verif_sources", True)
    _write(out / "results.json", res)
    if log and (log / "sim.log").is_file():
        (out / "sim.log").write_bytes((log / "sim.log").read_bytes())
    caught = bool(closure.functional_failures(res)) or res.get("status") != "ran"
    summary = {"patched": changed, "status": res.get("status"), "caught": caught,
               "failing": closure.functional_failures(res)}
    if do_triage and caught and res.get("status") == "ran":
        files: dict[str, Path] = {"contract.json": d.work / "contract.json", "rules.json": d.work / "rules.json",
                                  "results.json": out / "results.json"}
        if (out / "sim.log").is_file():
            files["sim.log"] = out / "sim.log"
        for doc in d.documents():
            files[f"spec/{Path(doc['file']).name}"] = d.root / doc["file"]
        for f in sim.rtl_files(out / "rtl"):
            files[f"rtl/{f.name}"] = f
        for f in sorted((d.root / "verif").rglob("*")):
            if f.is_file() and f.suffix in (".sv", ".py"):
                files[f"verif/{f.relative_to(d.root / 'verif').as_posix()}"] = f
        tri = triage.run(res, contract, files, _backend(d, o), _logs(d), model=o.triage_model)
        _write(out / "triage.json", tri)
        (out / "triage.md").write_text(triage.to_markdown(tri), encoding="utf-8")
        summary["triage"] = {"clusters": tri["clusters"], "most_likely": [a["most_likely"] for a in tri["analyses"]]}
        o.say(f"[inject] triage: {tri['clusters']} failure(s) -> {out / 'triage.md'}")
    _write(out / "inject.json", summary)
    o.say(f"[inject] bug {'CAUGHT' if caught else 'NOT CAUGHT'} by the approved verification")
    return summary


def stage_triage(d: Design, o: Options) -> None:
    _gate(d, "triage", o)
    results, contract = _read(d.work / "results.json"), _read(d.work / "contract.json")
    if not triage.clusters(results, contract):
        o.say("[triage] no failure to analyse")
        _write(d.work / "triage.json", {"analyses": [], "clusters": 0})
        return
    files: dict[str, Path] = {"contract.json": d.work / "contract.json", "rules.json": d.work / "rules.json",
                              "results.json": d.work / "results.json"}
    if (d.work / "sim" / "sim.log").is_file():
        files["sim.log"] = d.work / "sim" / "sim.log"
    for doc in d.documents():
        files[f"spec/{Path(doc['file']).name}"] = d.root / doc["file"]
    for f in sim.rtl_files(d.root / "rtl"):
        files[f"rtl/{f.name}"] = f
    for f in sorted((d.root / "verif").rglob("*")):
        if f.is_file() and f.suffix in (".sv", ".py"):
            files[f"verif/{f.relative_to(d.root / 'verif').as_posix()}"] = f
    tri = triage.run(results, contract, files, _backend(d, o), _logs(d), model=o.triage_model)
    _write(d.work / "triage.json", tri)
    (d.work / "triage.md").write_text(triage.to_markdown(tri), encoding="utf-8")
    o.say(f"[triage] {tri['clusters']} failure(s), {len(tri['analyses'])} analysed -> work/triage.md")


def stage_mutate(d: Design, o: Options) -> None:
    _gate(d, "mutate", o)
    baseline = _read(d.work / "results.json") if (d.work / "results.json").is_file() else None
    res = mutate.run(default_host(), _read(d.work / "contract.json"), d.root / "rtl", d.root / "verif" / "sva",
                     test_files(d), count=o.mutants, seed=o.seed, clock_periods=_periods(d), baseline=baseline)
    ex = res.get("excluded_uncovered") or {}
    o.say(f"[mutate] {res['count']} mutants: killed {res['killed']}, survived {res['survived']}, "
          f"not compiled {res['not_compiled']}; score {res['score']} % (candidates on executed lines only; "
          f"excluded {ex.get('lines', 0)} on unexecuted lines, files not elaborated {ex.get('files') or 'none'})")
    threshold = float(d.config().get("mutation_threshold", 85))
    res["threshold"] = threshold
    files: dict[str, Path] = {"contract.json": d.work / "contract.json", "rules.json": d.work / "rules.json"}
    for f in sim.rtl_files(d.root / "rtl"):
        files[f"rtl/{f.name}"] = f
    rules = {r["id"] for r in _read(d.work / "rules.json")["rules"]}
    res["attribution"] = mutate.attribute(res, files, rules, _backend(d, o), _logs(d), model=o.review_model)
    res["rule_scores"] = mutate.rule_scores(res, threshold)
    weak = [r for r, s in res["rule_scores"].items() if not s["meets_threshold"]]
    _write(d.work / "mutation.json", res)
    o.say(f"[mutate] per-requirement: {len(res['rule_scores'])} rules with attributed mutants, "
          f"{len(weak)} below the {threshold:g} % threshold{': ' + ', '.join(weak[:8]) if weak else ''}")


def agent_costs(d: Design) -> dict:
    total, calls, by_stage = 0.0, 0, {}
    for f in (d.work / "logs" / "agents").glob("*.json"):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        cost = rec.get("cost_usd") or 0.0
        stage = rec.get("task", "").split("_")[0]
        total += cost
        calls += 1
        by_stage[stage] = round(by_stage.get(stage, 0.0) + cost, 4)
    return {"total_usd": round(total, 4), "calls": calls, "by_agent": dict(sorted(by_stage.items()))}


def stage_report(d: Design, o: Options) -> None:
    bypass = d.require_gate("G3_verif_sources", True)
    if not o.unreviewed:
        _gate(d, "report", o)
    contract = _read(d.work / "contract.json")
    results = _read(d.work / "results.json") if (d.work / "results.json").is_file() else None
    mutation = _read(d.work / "mutation.json") if (d.work / "mutation.json").is_file() else None
    tri = _read(d.work / "triage.json") if (d.work / "triage.json").is_file() else None
    tmap = test_map(d)
    clo = _read(d.work / "coverage.json") if (d.work / "coverage.json").is_file() else None
    rep = report.build(d.name, d.status(), _read(d.work / "rules.json"), contract, results, mutation, tri,
                       agent_costs(d), bypass, tmap, clo)
    report.write(rep, contract, mutation, d.work)
    o.say(f"[report] rules {rep['rules']['by_status']} | checks {rep['checks']['by_status']} -> work/report.md")


RUNNERS = {"ingest": stage_ingest, "extract": stage_extract, "review": stage_review, "contract": stage_contract,
           "gen-sva": stage_gen_sva, "gen-tests": stage_gen_tests, "sim": stage_sim, "cover": stage_cover,
           "triage": stage_triage,
           "mutate": stage_mutate, "report": stage_report}


def run_flow(d: Design, o: Options, start: str = "ingest", stop: str = "report") -> str:
    """Run stages in order from start to stop; stop before a stage whose gate is not approved
    (unless unreviewed). Returns the name of the last stage completed."""
    names = STAGES[STAGES.index(start): STAGES.index(stop) + 1]
    done = ""
    for name in names:
        gate = GATE_BEFORE.get(name)
        if gate and not o.unreviewed and not d.gate_approved(gate):
            o.say(f"[flow] stopped before '{name}': {gate} needs review. Read the review sheet, then "
                  f"'nnc gate approve {d.name} {gate} --by <name>' and 'nnc flow {d.name} --from {name}'.")
            return done
        RUNNERS[name](d, o)
        done = name
    return done

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
from nnc import closure, formal, gen_cov, gen_env, gen_sva, gen_tests, mutate, packet, report, review, runset, sim, triage
from nnc.agents.runtime import make_backend
from nnc.ingest import build_index, save_index
from nnc.project import Design, ProjectError
from nnc.simhost import default_host

STAGES = ("ingest", "extract", "review", "contract", "gen-sva", "gen-tests", "gen-env", "sim", "cover", "triage",
          "mutate", "formal", "report")
GATE_BEFORE = {"contract": "G1_rules", "gen-sva": "G2_contract", "gen-tests": "G2_contract", "gen-env": "G2_contract",
               "formal": "G3_verif_sources", "sim": "G3_verif_sources",
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
    single: bool = False          # ignore run_set.json: one run of the design configuration
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
    iface = contract_mod.extract_interface(_read(index_path(d, ip)), top=top)
    if _clock_relation(d) == "async":
        iface["clock_relation"] = "async"
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


def split_mode(d: Design) -> bool:
    """config tests_mode=split: a shared test-bench library plus small test modules (gen_tests)."""
    return str(d.config().get("tests_mode", "")).strip().lower() == "split"


def test_files(d: Design) -> list[Path]:
    """The generated test module(s), then the coverage-closure modules (one per closure round)."""
    tdir = d.root / "verif" / "tests"
    main = sorted(tdir.glob(f"test_{d.name}_g*.py")) if split_mode(d) else [test_file(d)]
    return main + sorted(tdir.glob(f"test_{d.name}_cov*.py"))


def tests_base(d: Design) -> Path:
    """The module closure tests import as `base`: the library in split mode, else the test module."""
    return d.root / "verif" / "tests" / f"tb_{d.name}.py" if split_mode(d) else test_file(d)


def test_map(d: Design) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for f in test_files(d):
        if f.is_file():
            out.update(gen_tests.test_check_map(f.read_text(encoding="utf-8")))
    return out


def stage_gen_tests(d: Design, o: Options) -> None:
    _gate(d, "gen-tests", o)
    if split_mode(d):
        rep = gen_tests.generate_split(contract_mod.selected(_read(d.work / "contract.json")), _read(d.work / "rules.json"),
                                       _backend(d, o), _logs(d), d.root / "verif" / "tests", d.name,
                                       model=o.tests_model, run_opts=sim.sim_options(d.config()), workers=o.workers)
        _write(d.work / "gen_tests.json", rep)
        o.say(f"[gen-tests] split: library {rep['library']['status']}, "
              + ", ".join(f"{g['file']} {g['status']}" for g in rep["groups"])
              + f"; US${rep['usage']['cost_usd']} in {rep['usage']['calls']} calls"
              + (f" PROBLEMS {rep['problems'][:4]}" if rep["problems"] else ""))
        return
    rep = gen_tests.generate(contract_mod.selected(_read(d.work / "contract.json")), _read(d.work / "rules.json"), _backend(d, o), _logs(d),
                             test_file(d), model=o.tests_model, run_opts=sim.sim_options(d.config()))
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


def _periods(d: Design) -> dict[str, float]:
    """Design configuration clock_periods ("i_clk_rd=13.7,i_clk_wr=10"; ns, default 10 each)."""
    return sim.parse_periods(d.config().get("clock_periods"))


def _simkw(d: Design) -> dict:
    """Clock periods and run options (defines, plusargs) of the design configuration, for every run."""
    return {"clock_periods": _periods(d), "opts": sim.sim_options(d.config())}


CLOCK_RELATIONS = ("sync", "async")


def _clock_relation(d: Design) -> str | None:
    """Design configuration clock_relation: "async" when the clocks of the specification are mutually
    asynchronous (written into the contract interface, so every generator and the simulation see it)."""
    rel = (d.config().get("clock_relation") or "").strip().lower()
    if rel and rel not in CLOCK_RELATIONS:
        raise ProjectError(f"clock_relation must be one of {CLOCK_RELATIONS}, got {rel!r}")
    return rel or None


def stage_sim(d: Design, o: Options) -> None:
    _gate(d, "sim", o)
    contract = _read(d.work / "contract.json")
    res = _regression(d, o, contract, d.root / "rtl")
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
        if split_mode(d):
            owner = {}
            for f in test_files(d):
                if f.is_file() and "_cov" not in f.stem:
                    owner.update({n: f.name for n in gen_tests.test_check_map(f.read_text(encoding="utf-8"))})
            bad = {e.split(":")[0] for e in errs}
            pairs = [(gen_tests.error_module(t, owner, f"tb_{d.name}.py"), e) for t in res["tests"]
                     for e in errs if t["name"] in bad and e.startswith(t["name"] + ":")]
            rep = gen_tests.repair_split(contract_mod.selected(contract), _read(d.work / "rules.json"), _backend(d, o),
                                         _logs(d), d.root / "verif" / "tests", d.name, pairs, model=o.tests_model,
                                         round_no=rnd, run_opts=sim.sim_options(d.config()))
        else:
            rep = gen_tests.repair(contract_mod.selected(contract), _read(d.work / "rules.json"), _backend(d, o), _logs(d), test_file(d), errs,
                                   model=o.tests_model, round_no=rnd, run_opts=sim.sim_options(d.config()))
        o.say(f"[sim] repair: {rep['status']}")
        res = _regression(d, o, contract, d.root / "rtl")
        o.say("[sim] " + _summ_sim(res))
    _save_sim(d, res)


def _write_kit(d: Design, contract: dict, params: dict | None, kw: dict | None = None) -> None:
    """designs/<ip>/sim/: Makefile and inputs that reproduce the regression without NNC (the primary run
    of a run set)."""
    kw = kw or _simkw(d)
    kit = sim.kit_files(contract, sim.rtl_files(d.root / "rtl"), sim.checker_files(d.root / "verif" / "sva"),
                        test_files(d), params if params is not None else sim.param_values(contract),
                        kw["clock_periods"], kw["opts"])
    for rel, text in kit.items():
        p = d.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))


def _save_sim(d: Design, res: dict) -> None:
    if (d.work / "contract.json").is_file():
        prim = _primary(res)
        _write_kit(d, _read(d.work / "contract.json"), res.get("params"),
                   prim and {"clock_periods": prim["clock_periods"], "opts": prim["opts"]})
    res["unreviewed_gates"] = d.require_gate("G3_verif_sources", True)
    logs = _run_logs(res)
    detail = res.pop("runs_detail", None)
    runs_dir = d.work / "runs"
    for old in runs_dir.glob("*.json") if runs_dir.is_dir() else []:
        old.unlink()
    for r in detail or []:
        _write(runs_dir / f"{r['label']}.json", {**runset.summary(r), "result": runset.primary_result(r)})
    _write(d.work / "results.json", res)
    _copy_logs(logs, d.work / "sim" / "sim.log", d.work / "sim" / "runs")


def _run_logs(res: dict) -> list[tuple[str, Path]]:
    """(label, sim.log) of every run, primary first; label "" for a single run."""
    out = Path(res.pop("out_dir", "")) if res.get("out_dir") else None
    if res.get("runs_detail"):
        return [(r["label"], Path(r["log"])) for r in res["runs_detail"]]
    return [("", out / "sim.log")] if out else []


def _copy_logs(logs: list[tuple[str, Path]], primary: Path, runs_dir: Path) -> None:
    """The primary log at `primary` (as for a single run), every run's log in runs_dir/<label>.log."""
    for old in runs_dir.glob("*.log") if runs_dir.is_dir() else []:
        old.unlink()
    for i, (label, log) in enumerate(logs):
        if not log.is_file():
            continue
        text = log.read_text(encoding="utf-8", errors="replace")
        if i == 0:
            primary.parent.mkdir(parents=True, exist_ok=True)
            primary.write_text(text, encoding="utf-8")
        if label:
            runs_dir.mkdir(parents=True, exist_ok=True)
            (runs_dir / f"{label}.log").write_text(text, encoding="utf-8")


def run_set_path(d: Design) -> Path:
    return d.root / runset.FILE


def _runs(d: Design, o: Options, contract: dict) -> list[dict] | None:
    """The runs of designs/<ip>/run_set.json, or None for one run of the design configuration."""
    if o.single or not run_set_path(d).is_file():
        return None
    try:
        return runset.load(run_set_path(d), contract, d.config())
    except runset.RunSetError as e:
        raise ProjectError(str(e)) from e


def _regression(d: Design, o: Options, contract: dict, rtl_dir: Path) -> dict:
    """The regression on rtl_dir: every run of the run set (merged), else one run with --seed."""
    runs = _runs(d, o, contract)
    if runs is None:
        return sim.run(default_host(), contract, rtl_dir, d.root / "verif" / "sva", test_files(d), seed=o.seed,
                       **_simkw(d))
    o.say(f"[sim] run set: {len(runs)} run(s) in {len({r['config'] for r in runs})} configuration(s): "
          + ", ".join(r["label"] for r in runs))
    return runset.run(default_host(), contract, rtl_dir, d.root / "verif" / "sva", test_files(d), runs,
                      parallel=o.workers)


def _primary(res: dict | None) -> dict | None:
    """Settings of the primary run of a run-set result (None for a single run)."""
    rs = (res or {}).get("run_set")
    return next((r for r in rs["runs"] if r["label"] == rs["primary"]), None) if rs else None


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
        code, problems = closure.write_tests(contract, rules_doc, keep, tests_base(d), backend, _logs(d), rnd,
                                             o.tests_model, usage, run_opts=sim.sim_options(d.config()))
        if problems:
            entry["note"] = f"closure module invalid: {problems[:3]}"
            o.say(f"[cover] round {rnd}: {entry['note']}")
            break
        mod = d.root / "verif" / "tests" / f"test_{d.name}_cov{rnd}.py"
        mod.write_text(code, encoding="utf-8")
        entry["tests"] = sorted(n for n in gen_tests.test_check_map(code))
        res = _regression(d, o, contract, d.root / "rtl")
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


def formal_enabled(d: Design) -> bool:
    return str(d.config().get("formal", "")).strip().lower() in ("1", "on", "yes", "true")


def env_file(d: Design) -> Path:
    return d.root / "verif" / "formal" / "nnc_env.sv"


def stage_gen_env(d: Design, o: Options) -> None:
    """Agent A13: the environment's obligations as formal assumptions (verif/formal/nnc_env.sv)."""
    if not formal_enabled(d):
        o.say(f"[gen-env] skipped: formal is off (nnc config {d.name} formal=on)")
        return
    _gate(d, "gen-env", o)
    feedback = None
    if (d.work / "formal_triage.json").is_file() and env_file(d).is_file():
        feedback = [a for a in _read(d.work / "formal_triage.json").get("analyses", [])
                    if a.get("most_likely") == "E_environment_missing"] or None
        if feedback:
            o.say(f"[gen-env] {len(feedback)} counterexample(s) classified E by formal triage are given to A13")
    rep = gen_env.generate(contract_mod.selected(_read(d.work / "contract.json")), _read(d.work / "rules.json"),
                           _backend(d, o), _logs(d), default_host(), env_file(d), model=o.contract_model,
                           feedback=feedback)
    _write(d.work / "gen_env.json", rep)
    o.say(f"[gen-env] {len(rep['assumptions'])} assumptions, {rep['status']} after {rep['attempts']} attempt(s)"
          + (f" PROBLEMS {rep['problems'][:3]} {rep['lint_errors'][:300]}" if rep["status"] == "failed" else "")
          + " -> verif/formal/nnc_env.sv (review it at G3)")


def stage_formal(d: Design, o: Options) -> None:
    """SymbiYosys on the approved assertions with the approved environment (no agent)."""
    if not formal_enabled(d):
        o.say(f"[formal] skipped: formal is off (nnc config {d.name} formal=on)")
        return
    _gate(d, "formal", o)
    contract = _read(d.work / "contract.json")
    cfg = d.config()
    defines = [x.strip() for x in str(cfg.get("formal_defines", ",".join(sim.sim_options(cfg)["defines"])))
               .replace(";", ",").split(",") if x.strip()]
    depth = int(cfg.get("formal_depth", formal.DEFAULT_DEPTH))
    res = formal.run(default_host(), contract, d.root / "rtl", d.root / "verif" / "sva", env_file(d),
                     depth=depth, defines=defines, parallel=o.workers,
                     task_timeout_s=int(cfg.get("formal_timeout", formal.DEFAULT_TIMEOUT_S)))
    res["unreviewed_gates"] = d.require_gate("G3_verif_sources", True)
    out = Path(res.pop("out_dir"))
    tdir = d.work / "formal"
    if tdir.is_dir():
        for old in tdir.glob("*.vcd"):
            old.unlink()
    for cid, v in res["checks"].items():
        for i, t in enumerate(v.get("traces", [])[:1]):
            tdir.mkdir(parents=True, exist_ok=True)
            dst = tdir / f"{cid}.vcd"
            dst.write_bytes((out / t).read_bytes())
            v["traces"] = [f"work/formal/{dst.name}"]
    formal.write(d.work, d.name, res, contract)
    o.say(f"[formal] depth {depth}: {res['by_status']} -> work/formal.md")
    traces = {cid: d.root / v["traces"][0] for cid, v in res["checks"].items()
              if v["status"] == "CEX" and v.get("traces") and (d.root / v["traces"][0]).is_file()}
    for stale in (d.work / "formal_triage.json", d.work / "formal_triage.md"):
        if stale.is_file():
            stale.unlink()          # a triage belongs to the counterexamples of this run only
    if traces and str(cfg.get("formal_triage", "on")).lower() not in ("0", "off", "no", "false"):
        files: dict[str, Path] = {"contract.json": d.work / "contract.json", "rules.json": d.work / "rules.json"}
        for doc in d.documents():
            files[f"spec/{Path(doc['file']).name}"] = d.root / doc["file"]
        for f in sim.rtl_files(d.root / "rtl"):
            files[f"rtl/{f.name}"] = f
        for f in sorted((d.root / "verif" / "sva").glob("nnc_chk_*.sv")):
            files[f"verif/sva/{f.name}"] = f
        if env_file(d).is_file():
            files["verif/formal/nnc_env.sv"] = env_file(d)
        tri = formal.triage_cex(res, contract, files, traces, _backend(d, o), _logs(d), model=o.triage_model)
        _write(d.work / "formal_triage.json", tri)
        (d.work / "formal_triage.md").write_text(formal.triage_markdown(d.name, tri), encoding="utf-8")
        o.say(f"[formal] triage of {tri['checks']} counterexample(s): "
              + ", ".join(f"{a['check']} {a['most_likely']}" for a in tri["analyses"]) + " -> work/formal_triage.md")


def run_inject(d: Design, o: Options, patch: Path, out: Path, do_triage: bool = True) -> dict:
    """Run the approved checkers and tests on a patched COPY of the RTL (nnc inject) and triage the
    failures. Answers "would the flow catch this bug?" with evidence; rtl/ is never touched. Only NEW
    failures count (a test or check that passes on the unmodified RTL, work/results.json): a failure
    already present in the baseline says nothing about the bug and is not sent to triage."""
    from nnc import inject
    _gate(d, "sim", o)
    contract = _read(d.work / "contract.json")
    out.mkdir(parents=True, exist_ok=True)
    changed = inject.make_copy(d.root / "rtl", patch.read_text(encoding="utf-8"), out / "rtl")
    (out / "injected_bug.diff").write_bytes(patch.read_bytes())
    res = _regression(d, o, contract, out / "rtl")
    o.say(f"[inject] patched {changed} -> {_summ_sim(res)}")
    logs = _run_logs(res)
    res.pop("runs_detail", None)
    res["unreviewed_gates"] = d.require_gate("G3_verif_sources", True)
    _write(out / "results.json", res)
    _copy_logs(logs, out / "sim.log", out / "runs")
    base = mutate.baseline_failures(_read(d.work / "results.json") if (d.work / "results.json").is_file() else None)
    new_tests = [t["name"] for t in res.get("tests", []) if t["status"] == "fail" and t["name"] not in base["tests"]]
    new_checks = [c for c, v in (res.get("assertions") or {}).items() if v["fails"] > 0 and c not in base["checks"]]
    caught = bool(new_tests or new_checks) or res.get("status") != "ran"
    summary = {"patched": changed, "status": res.get("status"), "caught": caught,
               "failing": closure.functional_failures(res), "new_failing": new_tests + new_checks,
               "baseline_failing": sorted(base["tests"] | base["checks"])}
    if do_triage and caught and res.get("status") == "ran":
        files: dict[str, Path] = {"contract.json": d.work / "contract.json", "rules.json": d.work / "rules.json",
                                  "results.json": out / "results.json"}
        if (out / "sim.log").is_file():
            files["sim.log"] = out / "sim.log"
        for f in sorted((out / "runs").glob("*.log")):
            files[f"sim_runs/{f.name}"] = f
        for doc in d.documents():
            files[f"spec/{Path(doc['file']).name}"] = d.root / doc["file"]
        for f in sim.rtl_files(out / "rtl"):
            files[f"rtl/{f.name}"] = f
        for f in sorted((d.root / "verif").rglob("*")):
            if f.is_file() and f.suffix in (".sv", ".py"):
                files[f"verif/{f.relative_to(d.root / 'verif').as_posix()}"] = f
        only_new = {**res, "tests": [t for t in res.get("tests", []) if t["status"] != "fail" or t["name"] in new_tests],
                    "assertions": {c: v for c, v in (res.get("assertions") or {}).items()
                                   if v["fails"] == 0 or c in new_checks}}
        tri = triage.run(only_new, contract, files, _backend(d, o), _logs(d), model=o.triage_model)
        _write(out / "triage.json", tri)
        (out / "triage.md").write_text(triage.to_markdown(tri), encoding="utf-8")
        summary["triage"] = {"clusters": tri["clusters"], "most_likely": [a["most_likely"] for a in tri["analyses"]],
                             "cost_usd": (tri.get("usage") or {}).get("cost_usd")}
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
    failed = {lbl for t in results.get("tests", []) for lbl in t.get("failed_in", [])}
    failed |= {lbl for a in (results.get("assertions") or {}).values() for lbl, v in (a.get("runs") or {}).items()
               if v["fails"] > 0}
    for lbl in sorted(failed):                          # logs of the runs that failed (run set)
        if (d.work / "sim" / "runs" / f"{lbl}.log").is_file():
            files[f"sim_runs/{lbl}.log"] = d.work / "sim" / "runs" / f"{lbl}.log"
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
    kw: dict = {**_simkw(d), "sim_seed": o.seed, "baseline": baseline}
    rs = (baseline or {}).get("run_set")
    if rs:      # run set: each mutant runs in the first run that executed its line, against that run's baseline
        runs = []
        for r in rs["runs"]:
            f = d.work / "runs" / f"{r['label']}.json"
            if r["status"] == "ran" and f.is_file():
                runs.append({"label": r["label"], "params": r["overrides"], "opts": r["opts"],
                             "clock_periods": r["clock_periods"], "seed": r["seed"], "baseline": _read(f)["result"]})
        kw = {"runs": runs}
        o.say(f"[mutate] run set: {len(runs)} runs; each mutant runs where its line is executed (primary first)")
    res = mutate.run(default_host(), _read(d.work / "contract.json"), d.root / "rtl", d.root / "verif" / "sva",
                     test_files(d), count=o.mutants, seed=o.seed, **kw)
    ex = res.get("excluded_uncovered") or {}
    o.say(f"[mutate] {res['count']} mutants: killed {res['killed']}, survived {res['survived']}, "
          f"not compiled {res['not_compiled']}; score {res['score']} % (candidates on executed lines only; "
          f"excluded {ex.get('lines', 0)} on unexecuted lines, files not elaborated {ex.get('files') or 'none'})")
    threshold = float(d.config().get("mutation_threshold", 85))
    res["threshold"] = threshold
    files: dict[str, Path] = {"contract.json": d.work / "contract.json", "rules.json": d.work / "rules.json"}
    for f in sim.rtl_files(d.root / "rtl"):
        files[f"rtl/{f.name}"] = f
    if res.get("runs") and run_set_path(d).is_file():
        files["run_set.json"] = run_set_path(d)
    rules = {r["id"] for r in _read(d.work / "rules.json")["rules"]}
    res["attribution"] = mutate.attribute(res, files, rules, _backend(d, o), _logs(d), model=o.review_model)
    res["rule_scores"] = mutate.rule_scores(res, threshold)
    weak = [r for r, s in res["rule_scores"].items() if not s["meets_threshold"]]
    _write(d.work / "mutation.json", res)
    o.say(f"[mutate] per-requirement: {len(res['rule_scores'])} rules with attributed mutants, "
          f"{len(weak)} below the {threshold:g} % threshold{': ' + ', '.join(weak[:8]) if weak else ''}")


def agent_costs(d: Design) -> dict:
    """Agent cost from the call logs; `failed_usd` is what calls without a usable answer cost (usage limit
    reached mid-answer, timeout, invalid answer): money spent for nothing."""
    total, calls, by_stage, failed, n_failed = 0.0, 0, {}, 0.0, 0
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
        if rec.get("output") is None or rec.get("error") or rec.get("schema_errors"):
            failed += cost
            n_failed += 1
    return {"total_usd": round(total, 4), "calls": calls, "by_agent": dict(sorted(by_stage.items())),
            "failed_usd": round(failed, 4), "failed_calls": n_failed}


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
    fv = _read(d.work / "formal.json") if (d.work / "formal.json").is_file() and formal_enabled(d) else None
    rep = report.build(d.name, d.status(), _read(d.work / "rules.json"), contract, results, mutation, tri,
                       agent_costs(d), bypass, tmap, clo, fv)
    report.write(rep, contract, mutation, d.work)
    packet.write(d)
    o.say(f"[report] rules {rep['rules']['by_status']} | checks {rep['checks']['by_status']} -> work/report.md, "
          f"work/review_packet.md (for the G4 reviewer)")


RUNNERS = {"ingest": stage_ingest, "extract": stage_extract, "review": stage_review, "contract": stage_contract,
           "gen-sva": stage_gen_sva, "gen-tests": stage_gen_tests, "gen-env": stage_gen_env, "formal": stage_formal,
           "sim": stage_sim, "cover": stage_cover,
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

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
from nnc import gen_sva, gen_tests, mutate, report, review, sim, triage
from nnc.agents.runtime import make_backend
from nnc.ingest import build_index, save_index
from nnc.project import Design, ProjectError
from nnc.simhost import default_host

STAGES = ("ingest", "extract", "review", "contract", "gen-sva", "gen-tests", "sim", "triage", "mutate", "report")
GATE_BEFORE = {"contract": "G1_rules", "gen-sva": "G2_contract", "gen-tests": "G2_contract", "sim": "G3_verif_sources",
               "triage": "G3_verif_sources", "mutate": "G3_verif_sources", "report": "G3_verif_sources"}


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
    rep = gen_sva.generate(_read(d.work / "contract.json"), _read(d.work / "rules.json"), _backend(d, o), _logs(d),
                           default_host(), d.root / "verif" / "sva", model=o.sva_model)
    _write(d.work / "gen_sva.json", rep)
    for m in rep["modules"]:
        o.say(f"[gen-sva] {m['module']}: {len(m['checks'])} checks, {m['status']} after {m['attempts']} attempt(s)"
              + (f" PROBLEMS {m['problems'][:3]} {m['lint_errors'][:300]}" if m["status"] == "failed" else ""))


def test_file(d: Design) -> Path:
    return d.root / "verif" / "tests" / f"test_{d.name}.py"


def stage_gen_tests(d: Design, o: Options) -> None:
    _gate(d, "gen-tests", o)
    rep = gen_tests.generate(_read(d.work / "contract.json"), _read(d.work / "rules.json"), _backend(d, o), _logs(d),
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


def stage_sim(d: Design, o: Options) -> None:
    _gate(d, "sim", o)
    contract = _read(d.work / "contract.json")
    host = default_host()
    res = sim.run(host, contract, d.root / "rtl", d.root / "verif" / "sva", test_file(d), seed=o.seed)
    o.say("[sim] " + _summ_sim(res))
    for rnd in range(1, o.repair_rounds + 1):
        lib = gen_tests.library_errors(res) if res.get("status") == "ran" else []
        if lib:
            o.say(f"[sim] {len(lib)} test(s) failed inside the helper library nnc_cocotb: a fault of the flow, "
                  f"not of the tests; no repair attempted. First: {lib[0][:300]}")
            break
        errs = gen_tests.infrastructure_errors(res) if res.get("status") == "ran" else []
        if not errs:
            break
        o.say(f"[sim] {len(errs)} test(s) raised Python errors in the test code; repair round {rnd} (no RTL, no failed checks sent)")
        rep = gen_tests.repair(contract, _read(d.work / "rules.json"), _backend(d, o), _logs(d), test_file(d), errs,
                               model=o.tests_model, round_no=rnd)
        o.say(f"[sim] repair: {rep['status']}")
        res = sim.run(host, contract, d.root / "rtl", d.root / "verif" / "sva", test_file(d), seed=o.seed)
        o.say("[sim] " + _summ_sim(res))
    res["unreviewed_gates"] = d.require_gate("G3_verif_sources", True)
    out = Path(res.pop("out_dir", "")) if res.get("out_dir") else None
    _write(d.work / "results.json", res)
    if out and (out / "sim.log").is_file():
        (d.work / "sim").mkdir(exist_ok=True)
        (d.work / "sim" / "sim.log").write_text((out / "sim.log").read_text(encoding="utf-8", errors="replace"),
                                                encoding="utf-8")


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
    res = mutate.run(default_host(), _read(d.work / "contract.json"), d.root / "rtl", d.root / "verif" / "sva",
                     test_file(d), count=o.mutants, seed=o.seed)
    _write(d.work / "mutation.json", res)
    o.say(f"[mutate] {res['count']} mutants: killed {res['killed']}, survived {res['survived']}, "
          f"not compiled {res['not_compiled']}; score {res['score']} %")


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
    tmap = gen_tests.test_check_map(test_file(d).read_text(encoding="utf-8")) if test_file(d).is_file() else {}
    rep = report.build(d.name, d.status(), _read(d.work / "rules.json"), contract, results, mutation, tri,
                       agent_costs(d), bypass, tmap)
    report.write(rep, contract, mutation, d.work)
    o.say(f"[report] rules {rep['rules']['by_status']} | checks {rep['checks']['by_status']} -> work/report.md")


RUNNERS = {"ingest": stage_ingest, "extract": stage_extract, "review": stage_review, "contract": stage_contract,
           "gen-sva": stage_gen_sva, "gen-tests": stage_gen_tests, "sim": stage_sim, "triage": stage_triage,
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

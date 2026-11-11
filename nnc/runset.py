"""Run set: one regression over several configurations and seeds (code only, no LLM).

One simulation elaborates one parameter set with one set of macros and plusargs, so a check that needs
another configuration (another parameter value, the synthesis branch, the metastability model off, other
seeds) can only be declared NOT_VERIFIABLE by that run. The designer lists the configurations of the
specification in `designs/<ip>/run_set.json`:

    {"seeds": [1, 2, 3],
     "configs": [
       {"name": "base", "note": "CFG-BASE, metastability model on"},
       {"name": "model_off", "plusargs": "+AFIFO_MSYNC_SEED={seed} +AFIFO_MSYNC_EN=0", "seeds": [1]},
       {"name": "syn", "defines": "VLSIT_SYNTHESIS", "seeds": [1]},
       {"name": "cell4", "params": {"PARA_AFIFO_CELL_TYPE": 4}}]}

Every configuration starts from the design configuration (clock_periods, defines, plusargs) and the
default parameters of the contract, and overrides what it names: `params` (contract parameters),
`defines` and `plusargs` (replace), `clock_periods` (merged per clock), `seeds` (else the top-level list,
else [1]). The first configuration with its first seed is the PRIMARY run: the reproduction kit and
mutation testing use it.

Each configuration is built once in its own folder and its seeds run one after the other; the
configurations run in parallel. The merged result keeps the shape of a single run (results.json):
  test       fail if it failed in any run, else pass if it passed in any run; per-run status kept,
  assertion  hits and fails summed over the runs (FAIL if it failed anywhere, NOT_HIT only if never hit
             in any run), per-run counts kept,
  NOT_VERIFIABLE  only for a check that EVERY run declared not verifiable: one run that verified it is
             enough, and a failure anywhere stays a failure,
  coverage   merged coverage.dat of all runs (verilator_coverage), functional cover hits summed.
Nothing is weakened by merging: a run can only add evidence or add a failure.
"""
from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

from nnc import sim
from nnc.simhost import SimHost

FILE = "run_set.json"
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,40}$")
_FIELDS = {"name", "note", "params", "defines", "plusargs", "clock_periods", "seeds"}


class RunSetError(ValueError):
    pass


def load(path: Path, contract: dict, design_config: dict) -> list[dict]:
    """The runs of the run set, in order (primary first): {label, config, seed, note, params (overrides
    only), opts, clock_periods}. Raises RunSetError on an unknown field, parameter or duplicate name."""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise RunSetError(f"{path.name}: not valid JSON ({e})") from e
    configs = doc.get("configs") if isinstance(doc, dict) else None
    if not configs or not isinstance(configs, list):
        raise RunSetError(f"{path.name}: needs a non-empty list 'configs'")
    extra = set(doc) - {"seeds", "configs", "note"}
    if extra:
        raise RunSetError(f"{path.name}: unknown top-level field(s) {sorted(extra)}")
    params_ok = {p["name"] for p in contract["interface"]["parameters"] if not p.get("derived")}
    default_seeds = _seeds(doc.get("seeds", [1]), "seeds")
    base_opts = sim.sim_options(design_config)
    base_periods = sim.parse_periods(design_config.get("clock_periods"))
    runs, names = [], set()
    for i, c in enumerate(configs, 1):
        if not isinstance(c, dict):
            raise RunSetError(f"{path.name}: configs[{i}] is not an object")
        name = str(c.get("name", ""))
        if not _NAME.match(name):
            raise RunSetError(f"{path.name}: configs[{i}] needs a name of letters, digits, '_', '.', '-'")
        if name in names:
            raise RunSetError(f"{path.name}: configuration name {name!r} is used twice")
        names.add(name)
        bad = set(c) - _FIELDS
        if bad:
            raise RunSetError(f"{path.name}: configuration {name}: unknown field(s) {sorted(bad)}")
        params = c.get("params") or {}
        unknown = set(params) - params_ok
        if unknown:
            raise RunSetError(f"{path.name}: configuration {name}: {sorted(unknown)} are not overridable "
                              f"parameters of the contract ({sorted(params_ok)})")
        try:
            params = {k: int(v, 0) if isinstance(v, str) else int(v) for k, v in params.items()}
        except ValueError as e:
            raise RunSetError(f"{path.name}: configuration {name}: parameter values must be integers") from e
        opts = dict(base_opts)
        if "defines" in c or "plusargs" in c:
            override = sim.sim_options({"defines": _text(c.get("defines", ",".join(base_opts["defines"]))),
                                        "plusargs": c.get("plusargs", base_opts["plusargs"])})
            opts = override
        periods = dict(base_periods)
        cp = c.get("clock_periods")
        if cp:
            periods.update(sim.parse_periods(cp) if isinstance(cp, str) else {k: sim._ns(v) for k, v in cp.items()})
        sim.clock_table(contract["interface"], periods)          # unknown clock names fail here
        for seed in _seeds(c["seeds"], f"{name}.seeds") if "seeds" in c else default_seeds:
            runs.append({"label": f"{name}.s{seed}", "config": name, "seed": seed, "note": c.get("note", ""),
                         "params": params, "opts": opts, "clock_periods": periods})
    return runs


def _text(v) -> str:
    return ",".join(v) if isinstance(v, list) else str(v or "")


def _seeds(v, where: str) -> list[int]:
    if not isinstance(v, list) or not v or not all(isinstance(s, int) and s >= 0 for s in v):
        raise RunSetError(f"run set {where}: a non-empty list of non-negative integers")
    return list(dict.fromkeys(v))


# ------------------------------------------------------------------------------------------- running
RUN_ONE = ("cd {} && for s in $(cat seeds.txt); do "
           "make SEED=$s NNC_JOBS=@JOBS@ > sim.log 2>&1; echo \"NNC_MAKE_RC=$?\" >> sim.log; mkdir -p s$s; "
           "if [ -f coverage.dat ]; then verilator_coverage --write-info coverage.info coverage.dat >> sim.log 2>&1; "
           "mv coverage.dat coverage.info s$s/; fi; "
           "if [ -f results.xml ]; then mv results.xml s$s/; fi; mv sim.log s$s/; done")
MERGE = ("DATS=$(ls C*/s*/coverage.dat 2>/dev/null)\n"
         "if [ -n \"$DATS\" ]; then verilator_coverage --write merged.dat $DATS > merge.log 2>&1; "
         "verilator_coverage --write-info merged.info merged.dat >> merge.log 2>&1; fi\n")


def script(parallel: int) -> str:
    one = RUN_ONE.replace("@JOBS@", str(max(1, 12 // max(1, parallel))))
    return f"ls -d C* | xargs -P {parallel} -I{{}} bash -c '{one}'\n" + MERGE


def run(host: SimHost, contract: dict, rtl_dir: Path, sva_dir: Path, test_file: Path | list[Path],
        runs: list[dict], *, parallel: int = 4, timeout_s: int | None = None) -> dict:
    """Simulate every run of the run set; return the merged result (results.json shape) with the
    per-run results under 'runs_detail' and the folder of the logs under 'out_dir'."""
    rtl = sim.rtl_files(rtl_dir)
    if not rtl:
        return {"status": "error", "error": f"no RTL files in {rtl_dir}"}
    try:
        issues = sim.conformance(contract, sim.dut_ports(rtl, contract["top"]))
    except ValueError as e:
        issues = [str(e)]
    base = {"date": datetime.now(timezone.utc).isoformat(timespec="seconds"), "seed": runs[0]["seed"],
            "rtl_files": [f.name for f in rtl], "integration": {"ok": not issues, "issues": issues}}
    if issues:
        return {**base, "status": "integration_failed"}
    sva = sim.checker_files(sva_dir)
    configs: dict[str, dict] = {}
    for r in runs:
        configs.setdefault(r["config"], {"run": r, "seeds": []})["seeds"].append(r["seed"])
    folder = {name: f"C{i:02d}" for i, name in enumerate(configs, 1)}
    files: dict[str, object] = {}
    for name, c in configs.items():
        r = c["run"]
        pv = sim.param_values(contract, r["params"])
        for rel, src in sim.build_inputs(contract, rtl, sva, test_file, pv, clock_periods=r["clock_periods"],
                                         opts=r["opts"]).items():
            files[f"{folder[name]}/{rel}"] = src
        files[f"{folder[name]}/seeds.txt"] = " ".join(str(s) for s in c["seeds"]) + "\n"
    if timeout_s is None:
        waves = math.ceil(len(configs) / max(1, parallel))
        timeout_s = 3600 * waves * max(len(c["seeds"]) for c in configs.values())
    res = host.run(files, script(parallel),
                   ["C*/s*/sim.log", "C*/s*/results.xml", "C*/s*/coverage.info", "C*/s*/coverage.dat",
                    "merged.info", "merged.dat", "merge.log"], timeout_s=timeout_s, tag="runset")
    names = [f.name for f in rtl]
    detail = []
    for r in runs:
        out = res.out_dir / folder[r["config"]] / f"s{r['seed']}"
        parsed = sim.parse_results(out, names) if out.is_dir() else {
            "tests": [], "assertions": {}, "not_verifiable": {}, "coverage": {"status": "not_measured"},
            "functional": {}, "make_rc": None, "built": False, "build_errors": ["no output: the run did not start"]}
        detail.append({**r, "params": sim.param_values(contract, r["params"]), "overrides": r["params"],
                       "status": "build_failed" if not parsed["built"] else "ran", "log": str(out / "sim.log"),
                       **parsed})
    functional: dict[str, int] = {}
    for d in detail:
        for k, v in d.get("functional", {}).items():
            functional[k] = functional.get(k, 0) + v
    cov = sim.coverage_of(res.out_dir / "merged.info", res.out_dir / "merged.dat", names, functional)
    return {**base, **merge(detail, cov, functional), "host": host.name, "out_dir": str(res.out_dir),
            "runs_detail": detail}


# ------------------------------------------------------------------------------------------- merging
def merge(detail: list[dict], coverage: dict, functional: dict[str, int]) -> dict:
    """Merge per-run results (see the module docstring). Pure function."""
    ran = [d for d in detail if d["status"] == "ran"]
    tests: dict[str, dict] = {}
    for d in ran:
        for t in d["tests"]:
            m = tests.setdefault(t["name"], {"name": t["name"], "runs": {}})
            m["runs"][d["label"]] = t["status"]
            if t["status"] == "fail" and "failed_in" not in m:
                m.update({k: v for k, v in t.items() if k not in ("name", "status", "runs")})
                m["failed_in"] = []
            if t["status"] == "fail":
                m["failed_in"].append(d["label"])
    for m in tests.values():
        sts = set(m["runs"].values())
        m["status"] = "fail" if "fail" in sts else "pass" if "pass" in sts else "skip"
        if m["status"] == "fail":
            m["message"] = f"[failed in {', '.join(m['failed_in'])}] " + m.get("message", "")
    asserts: dict[str, dict] = {}
    for d in ran:
        for cid, v in d["assertions"].items():
            a = asserts.setdefault(cid, {"hits": 0, "fails": 0, "runs": {}})
            a["hits"] += v["hits"]
            a["fails"] += v["fails"]
            a["runs"][d["label"]] = {"hits": v["hits"], "fails": v["fails"]}
            if "first_fail_time" in v and "first_fail_time" not in a:
                a["first_fail_time"], a["first_fail_run"] = v["first_fail_time"], d["label"]
    nv: dict[str, str] = {}
    for cid in sorted({c for d in ran for c in d.get("not_verifiable", {})}):
        if all(cid in d.get("not_verifiable", {}) for d in ran):
            reasons = list(dict.fromkeys(d["not_verifiable"][cid] for d in ran))
            nv[cid] = (f"not verifiable in any of the {len(ran)} runs: " + " | ".join(reasons))[:600]
    primary = detail[0]
    return {
        "status": "ran" if ran else "build_failed",
        "params": primary["params"],
        "tests": sorted(tests.values(), key=lambda t: t["name"]),
        "assertions": dict(sorted(asserts.items())),
        "not_verifiable": nv,
        "not_verifiable_by_run": {d["label"]: d.get("not_verifiable", {}) for d in ran},
        "coverage": {**coverage, "scope": f"merged over {len(ran)} run(s) of the run set"},
        "functional": functional,
        "built": bool(ran),
        "build_errors": [f"{d['label']}: {e}" for d in detail if d["status"] != "ran" for e in d["build_errors"][:5]],
        "run_set": {"primary": primary["label"], "failed_runs": [d["label"] for d in detail if d["status"] != "ran"],
                    "runs": [summary(d) for d in detail]},
    }


def summary(d: dict) -> dict:
    t: dict[str, int] = {}
    for x in d.get("tests", []):
        t[x["status"]] = t.get(x["status"], 0) + 1
    a = d.get("assertions", {})
    return {"label": d["label"], "config": d["config"], "seed": d["seed"], "note": d.get("note", ""),
            "overrides": d.get("overrides", {}), "params": d.get("params"), "opts": d["opts"],
            "clock_periods": d["clock_periods"], "status": d["status"], "tests": dict(sorted(t.items())),
            "assertions_failing": sorted(c for c, v in a.items() if v["fails"] > 0),
            "not_verifiable": sorted(d.get("not_verifiable", {})),
            "coverage_percent": {k: v.get("percent") for k, v in ((d.get("coverage") or {}).get("metrics") or {}).items()}}


def primary_result(detail: dict) -> dict:
    """The primary run in the shape of a single sim.run result (mutation baseline)."""
    keep = ("tests", "assertions", "not_verifiable", "coverage", "functional", "make_rc", "built", "build_errors",
            "status", "params", "seed")
    return {k: detail.get(k) for k in keep}

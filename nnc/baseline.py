"""Baseline: the hand-written testbench of the upstream design, on the same bugs (`nnc baseline`).

To judge the generated verification it is compared with the verification the RTL was delivered with:
the self-checking SystemVerilog testbenches of the upstream repository, run the way their own scripts
run them (Icarus Verilog, their configurations, their pass criteria). `designs/<ip>/baseline/` holds
the copied testbench files (Apache-2.0, see NOTICE there) and `baseline.json`:

    {"source": "...", "top": "tb_sfifo", "tb": ["tb_sfifo.sv"], "rtl": ["m_vlsit_sfifo_mem.sv", ...],
     "defines": ["VLSIT_SYNTHESIS"], "pass": ["RESULT PASS"], "exit_zero": true,
     "runs": [{"name": "d8", "params": {"DEPTH": 8}, "plusargs": ["+SEED=1"], "defines": [...]}]}

A run passes when its log has every `pass` string of the description and of the run (and vvp exits 0 if
`exit_zero`). The baseline is run
on the unmodified RTL (it must pass) and on each fault of `bugs/bugs.json`: a fault is caught when any
run fails. The result sits next to the bug benchmark of the generated verification (work/bench.json).
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from nnc.simhost import SimHost


def load(design_root: Path) -> dict:
    p = design_root / "baseline" / "baseline.json"
    if not p.is_file():
        raise FileNotFoundError(f"no baseline description: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def apbcdc_stimulus(index: int, nx: int) -> tuple[str, str]:
    """Stimulus files of the upstream AsyncAPBBridge regression (port of make_stimulus() in
    common_rtl/004_AsyncAPBBridge/verification/vlsit_run_sim.py, Apache-2.0): requester and completer
    lines of configuration `index`, seeded as there (Random(1000 + index))."""
    rnd = random.Random(1000 + index)
    req, cmp_ = [], []
    for _ in range(nx):
        wr = rnd.randint(0, 1)
        req.append("%d %d %x %x %x %x %x" % (rnd.choice([0, 0, 1, 2, 5]), wr, rnd.randrange(0, 1 << 16, 4),
                                            rnd.randint(1, 3) if wr else 0, rnd.randrange(1 << 16) if wr else 0,
                                            rnd.randrange(16), rnd.randrange(16) if wr else 0))
    for _ in range(nx):
        cmp_.append("%d %d %x %x %x" % (rnd.choice([0, 0, 1, 3, 6]), rnd.randint(0, 1), rnd.randrange(1 << 16),
                                       rnd.randrange(16), rnd.randrange(16)))
    return "\n".join(req) + "\n", "\n".join(cmp_) + "\n"


def build(desc: dict, design_root: Path, rtl_dir: Path) -> tuple[dict, str, list[str]]:
    """Input files, the shell script and the run names."""
    files: dict[str, object] = {}
    rtl = desc["rtl"]
    if rtl == "filelist":                      # a generated RTL: the files of rtl/filelist.f, in order
        from nnc.sim import rtl_files
        rtl = [f.name for f in rtl_files(rtl_dir)]
    for f in rtl:
        files[f"rtl/{f}"] = rtl_dir / f
    for f in desc["tb"]:
        files[f"tb/{f}"] = design_root / "baseline" / f
    srcs = " ".join([f"rtl/{f}" for f in rtl] + [f"tb/{f}" for f in desc["tb"]])
    names = []
    for r in desc["runs"]:
        name = r["name"]
        names.append(name)
        defs = " ".join(f"-D{d}" for d in desc.get("defines", []) + r.get("defines", []))
        pars = " ".join(f"-P{desc['top']}.{k}={v}" for k, v in (r.get("params") or {}).items())
        plus = list(r.get("plusargs") or [])
        st = r.get("stimulus")
        if st and st.get("kind") == "apbcdc":
            req, cmp_ = apbcdc_stimulus(st["index"], st.get("nx", 40))
            files[f"stim/{name}_req.txt"] = req
            files[f"stim/{name}_cmp.txt"] = cmp_
            plus.append(f"+STIM=stim/{name}")
        # one script per run (no shell quoting through xargs); the exit code of vvp is logged for exit_zero
        log = f"logs/{name}.log"
        files[f"runs/{name}.sh"] = (
            f"iverilog -g2012 -o build/{name}.vvp -s {desc['top']} {defs} {pars} {srcs} > {log} 2>&1\n"
            f"rc=$?; echo \"NNC_COMPILE_RC=$rc\" >> {log}; [ $rc -eq 0 ] || exit 0\n"
            f"vvp -n build/{name}.vvp {' '.join(plus)} >> {log} 2>&1\n"
            f"echo \"NNC_VVP_RC=$?\" >> {log}\n")
    script = "mkdir -p build logs\nls runs/*.sh | xargs -P 6 -n 1 sh\n"
    return files, script, names


def run(host: SimHost, design_root: Path, rtl_dir: Path, desc: dict | None = None) -> dict:
    desc = desc or load(design_root)
    files, script, names = build(desc, design_root, rtl_dir)
    res = host.run(files, script, ["logs/*.log"], timeout_s=7200, tag="baseline")
    runs = []
    for n, r in zip(names, desc["runs"]):
        log_p = res.out_dir / "logs" / f"{n}.log"
        log = log_p.read_text(encoding="utf-8", errors="replace") if log_p.is_file() else ""
        ok = bool(log) and all(s in log for s in desc.get("pass", []) + r.get("pass", []))
        if desc.get("exit_zero", True):
            ok = ok and "NNC_VVP_RC=0" in log
        runs.append({"name": n, "ok": ok, "compiled": "NNC_COMPILE_RC=0" in log,
                     "tail": "" if ok else "\n".join(log.splitlines()[-6:])[:600]})
    # a run that does not compile is not a detection: it is reported apart and never counts as caught
    return {"runs": runs, "passed": all(r["ok"] for r in runs),
            "failed": [r["name"] for r in runs if not r["ok"] and r["compiled"]],
            "not_compiled": [r["name"] for r in runs if not r["compiled"]]}


def mutant_copy(rtl_dir: Path, m: dict, dest: Path) -> None:
    """Copy rtl_dir to dest with the mutated line of mutant `m` (an entry of work/mutation.json)."""
    import shutil
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(rtl_dir, dest)
    f = dest / m["file"]
    lines = f.read_text(encoding="utf-8").split("\n")
    if lines[m["line"] - 1].strip() != m["original"].strip():
        raise ValueError(f"{m['id']}: line {m['line']} of {m['file']} is not the recorded original")
    lines[m["line"] - 1] = m["mutated"]
    f.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def compare_mutants(design_root: Path, host: SimHost, desc: dict, log=print) -> dict | None:
    """The upstream testbench on the mutants of the NNC mutation run (work/mutation.json), same mutant set."""
    p = design_root / "work" / "mutation.json"
    if not p.is_file():
        return None
    mut = json.loads(p.read_text(encoding="utf-8"))
    rows = []
    for m in mut["mutants"]:
        if m["status"] not in ("killed", "survived"):
            continue
        out = design_root / "work" / "baseline" / m["id"]
        mutant_copy(design_root / "rtl", m, out / "rtl")
        r = run(host, design_root, out / "rtl", desc)
        st = "not_compiled" if r["not_compiled"] and not r["failed"] else ("killed" if r["failed"] else "survived")
        rows.append({"id": m["id"], "file": m["file"], "line": m["line"], "operator": m["operator"],
                     "baseline": st, "nnc": m["status"]})
        log(f"[baseline] {m['id']} {m['file']}:{m['line']} {m['operator']}: hand-written {st}, NNC {m['status']}")
    valid = [r for r in rows if r["baseline"] != "not_compiled"]
    both = lambda a, b: sum(1 for r in valid if r["baseline"] == a and r["nnc"] == b)
    return {"mutants": rows, "count": len(valid), "not_compiled": len(rows) - len(valid),
            "baseline_killed": sum(r["baseline"] == "killed" for r in valid),
            "nnc_killed": sum(r["nnc"] == "killed" for r in valid),
            "only_baseline": both("killed", "survived"), "only_nnc": both("survived", "killed"),
            "neither": both("survived", "survived")}


def compare(design_root: Path, host: SimHost, log=print, mutants: bool = True) -> dict:
    """Baseline on the unmodified RTL and on every fault of bugs/bugs.json, next to the bench results."""
    from nnc import bench, inject
    desc = load(design_root)
    work = design_root / "work"
    clean = run(host, design_root, design_root / "rtl", desc)
    if clean["not_compiled"]:
        raise RuntimeError(f"baseline does not compile on the unmodified RTL: {clean['not_compiled'][:3]}\n"
                           f"{clean['runs'][0]['tail']}")
    log(f"[baseline] unmodified RTL: {'PASS' if clean['passed'] else 'FAIL ' + str(clean['failed'][:5])} "
        f"({len(clean['runs'])} runs)")
    ours = {b["id"]: b for b in json.loads((work / "bench.json").read_text(encoding="utf-8"))["bugs"]} \
        if (work / "bench.json").is_file() else {}
    rows = []
    for b in bench.load(design_root):
        out = work / "baseline" / b["id"]
        inject.make_copy(design_root / "rtl", bench.make_patch(design_root / "rtl", b), out / "rtl")
        r = run(host, design_root, out / "rtl", desc)
        caught = bool(r["failed"])
        rows.append({"id": b["id"], "title": b["title"], "baseline_caught": caught, "baseline_failed_runs": r["failed"],
                     "baseline_not_compiled": r["not_compiled"], "nnc_caught": (ours.get(b["id"]) or {}).get("caught")})
        log(f"[baseline] {b['id']} {b['title']}: hand-written testbench {'CAUGHT' if caught else 'missed'}"
            f" ({len(r['failed'])}/{len(r['runs'])} runs fail); NNC {'caught' if rows[-1]['nnc_caught'] else '-'}")
    data = {"design": design_root.name, "source": desc.get("source"), "runs_per_rtl": len(clean["runs"]),
            "clean_pass": clean["passed"], "clean_failed": clean["failed"], "bugs": rows,
            "baseline_caught": sum(r["baseline_caught"] for r in rows),
            "nnc_caught": sum(bool(r["nnc_caught"]) for r in rows), "total": len(rows)}
    data["mutation"] = compare_mutants(design_root, host, desc, log) if mutants else None
    (work / "baseline.json").write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    md = [f"# Baseline comparison — {design_root.name}", "",
          f"The upstream hand-written testbench ({desc.get('source')}), run as its own script runs it "
          f"({len(clean['runs'])} runs per RTL), against the same faults as the bug benchmark of the generated "
          "verification. A fault is caught when any run fails.", "",
          f"Unmodified RTL: **{'all runs pass' if clean['passed'] else 'FAILS: ' + ', '.join(clean['failed'][:6])}**", "",
          f"**Caught:** hand-written {data['baseline_caught']}/{len(rows)}, NNC {data['nnc_caught']}/{len(rows)}", "",
          "| Bug | Fault | Hand-written testbench | NNC (generated) |", "|---|---|---|---|"]
    md += [f"| {r['id']} | {r['title']} | {'caught (' + str(len(r['baseline_failed_runs'])) + ' runs)' if r['baseline_caught'] else 'missed'} | "
           f"{'caught' if r['nnc_caught'] else ('missed' if r['nnc_caught'] is False else '—')} |" for r in rows]
    mu = data["mutation"]
    if mu:
        md += ["", "## Mutants", "",
               f"The same mutants as the NNC mutation run (`work/mutation.json`, one changed RTL line each; mutants "
               f"that did not compile in NNC are left out). Killed: hand-written **{mu['baseline_killed']}/{mu['count']}**, "
               f"NNC **{mu['nnc_killed']}/{mu['count']}**; killed only by the hand-written testbench {mu['only_baseline']}, "
               f"only by NNC {mu['only_nnc']}, by neither {mu['neither']}"
               + (f"; {mu['not_compiled']} did not compile under Icarus Verilog." if mu["not_compiled"] else "."), "",
               "| Mutant | Line | Operator | Hand-written | NNC |", "|---|---|---|---|---|"]
        md += [f"| {r['id']} | {r['file']}:{r['line']} | {r['operator']} | {r['baseline']} | {r['nnc']} |"
               for r in mu["mutants"]]
    (work / "baseline.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return data

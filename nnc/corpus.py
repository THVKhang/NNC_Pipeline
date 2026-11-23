"""Input corpus: the intake (and the adaptation) on RTL the flow was not written for (no agent, no tokens).

corpus/corpus.json lists open-source RTL repositories at fixed commits. For each, every module of the listed
folder (or the listed tops) is taken as the top of a design: nnc intake reads it with its folder as library,
and, with `adapt`, a design whose verdict is adapt gets its wrapper and interface document in a scratch
workspace, read again by the intake. The sources are fetched into a cache folder and are never committed; only
the verdicts are (corpus/results.json, docs/INPUT_SUPPORT.md).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from nnc import adapt as adapt_mod, contract, intake, sim
from nnc.ingest import build_index


def _err(e: Exception) -> str:
    """Exception text with the place it was raised (file:line of the deepest frame), for the results."""
    tb = traceback.extract_tb(e.__traceback__)
    at = f" [{Path(tb[-1].filename).name}:{tb[-1].lineno}]" if tb else ""
    return (f"{type(e).__name__}: {e}"[:360] + at)

MANIFEST = Path(__file__).resolve().parent.parent / "corpus" / "corpus.json"


def fetch(src: dict, cache: Path) -> Path:
    """The repository at its commit in cache/<name> (shallow fetch of that commit)."""
    d = cache / src["name"]
    if d.is_dir() and (d / ".git").exists():
        head = subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        if head == src["commit"]:
            return d
        shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True, exist_ok=True)
    for cmd in (["git", "init", "-q"], ["git", "remote", "add", "origin", src["url"]],
                ["git", "fetch", "-q", "--depth", "1", "origin", src["commit"]], ["git", "checkout", "-q", "FETCH_HEAD"]):
        r = subprocess.run(cmd, cwd=d, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"{src['name']}: {' '.join(cmd)} failed: {r.stderr.strip()[:300]}")
    return d


def tops_of(src: dict, root: Path) -> list[str]:
    if isinstance(src.get("tops"), list):
        return src["tops"]
    rtl = root / src["rtl"]
    names = []
    for f in sorted(rtl.iterdir()):
        if f.is_file() and f.suffix.lower() in intake.SV_EXT:
            names += [u["name"] for u in intake.scan(f.read_text(encoding="utf-8", errors="replace"))["units"]
                      if u["kind"] == "module"]
    skip = set(src.get("skip") or [])
    return [n for n in dict.fromkeys(names) if n not in skip]


SMOKE_TEST = '''"""Smoke test written by nnc corpus (not by an agent): clock, reset, random inputs for 200 cycles.
It checks nothing about the behaviour: only that the test bench of the flow builds and runs on this top."""
import cocotb

from nnc_cocotb import PORTS, _NOT_DATA, next_cycle, reset_dut, rng, start_clock


@cocotb.test()
async def test_nnc_smoke(dut):
    start_clock(dut)
    await reset_dut(dut)
    r = rng(1)
    ins = [p for p in PORTS if p["direction"] == "input" and p["name"] not in _NOT_DATA]
    for _ in range(200):
        for p in ins:
            getattr(dut, p["name"]).value = r.getrandbits(int(p["width"]))
        await next_cycle(dut)
'''


# `%Error: .../rtl/cc_fifo.sv:135: Verilog $stop`: an assertion of the design itself stopped the run
_DUT_STOP = re.compile(r"%Error: (?:\S*/)?rtl/([^/:\s]+):(\d+): Verilog \$stop")
_RUN_DIR = re.compile(r"\S*/nnc_runs/[^/\s]+/")     # the scratch folder of one run on the host


def smoke_status(tests: list[dict], build_errors: list[str], rtl_names: set[str]) -> tuple[str, str | None]:
    """(status, place). pass; dut_assertion: an assertion in the RTL stopped the run (the random inputs of the
    generic test break a rule of the design's inputs, such as no push into a full FIFO: the machinery works);
    test_failed; simulator_unsupported: Verilator builds no model of this RTL ("Unsupported: ..."); build_failed."""
    if tests and all(x["status"] == "pass" for x in tests):
        return "pass", None
    for e in build_errors:
        m = _DUT_STOP.search(e)
        if m and m.group(1) in rtl_names:
            return "dut_assertion", f"{m.group(1)}:{m.group(2)}"
    if tests:
        return "test_failed", None
    if any("Unsupported:" in e for e in build_errors):
        return "simulator_unsupported", None
    return "build_failed", None


def _smoke(host, tmp: Path, top: str, iface: dict, src: dict, frontend: str) -> dict:
    """The simulation machinery of the flow (test bench top, Makefile, cocotb, coverage and its design scope)
    on this top, with a generic test: does it build, run and measure coverage?"""
    if not iface.get("clock"):
        return {"status": "no_clock"}
    c = {"top": top, "interface": iface}
    test = tmp / "test_nnc_smoke.py"
    test.write_text(SMOKE_TEST, encoding="utf-8")
    rtl = sim.rtl_files(tmp / "rtl")
    opts = {"defines": list(src.get("defines") or []), "plusargs": ""}
    files = sim.build_inputs(c, rtl, [], test, sim.param_values(c), coverage=True, opts=opts, frontend=frontend)
    for h in (tmp / "rtl").rglob("*"):         # include files in subfolders of rtl/
        if h.is_file() and h.suffix.lower() in intake.HDR_EXT:
            files.setdefault(f"rtl/{h.relative_to(tmp / 'rtl').as_posix()}", h)
    res = host.run(files, sim.SIM_SCRIPT.format(seed=1, jobs=4),
                   ["sim.log", "results.xml", "coverage.info", "coverage.dat", *sim.SCOPE_OUTPUTS],
                   timeout_s=1200, tag="smoke")
    r = sim.parse_results(res.out_dir, [f.name for f in rtl])
    tests = r["tests"]
    cov = (r.get("coverage") or {}).get("metrics") or {}
    errors = [_RUN_DIR.sub("", e) for e in r["build_errors"]]
    status, place = smoke_status(tests, errors, {f.name for f in rtl})
    return {"status": status, "assertion": place, "build_errors": errors[:3],
            "failure": next((t.get("message", "")[:300] for t in tests if t["status"] != "pass"), None),
            "coverage": {k: (v or {}).get("percent") for k, v in cov.items() if k in ("line", "toggle")},
            "design_scope": bool(((r.get("coverage") or {}).get("design_scope") or {}).get("left_out") is not None)}


def _adapt_check(host, rep: dict, src: dict, smoke: bool = False) -> dict:
    """Adapt one design in a scratch workspace; the intake of the verified top must be ready. With `smoke`, the
    simulation machinery runs on it too (_smoke)."""
    tmp = Path(tempfile.mkdtemp(prefix="nnc_corpus_"))
    try:
        (tmp / "rtl").mkdir()
        (tmp / "spec").mkdir()
        # only the files of the closure (a library folder may hold units that do not parse)
        files = [Path(f) for f in rep["collect"]["files"]]
        for f in files:
            shutil.copyfile(f, tmp / "rtl" / f.name)
        for d in rep["collect"].get("include_dirs") or []:
            for h in Path(d).rglob("*"):
                if h.is_file() and h.suffix.lower() in intake.HDR_EXT:
                    rel = h.relative_to(d)
                    (tmp / "rtl" / rel).parent.mkdir(parents=True, exist_ok=True)
                    if not (tmp / "rtl" / rel).exists():
                        shutil.copyfile(h, tmp / "rtl" / rel)
        local = intake.run(None, tmp / "rtl", top=rep["collect"]["top"], listed=[tmp / "rtl" / f.name for f in files])
        local.update({k: rep[k] for k in ("codes", "ports", "parameters", "structure")})
        local.update(intake.assess(local["collect"], local["codes"], local["ports"], local["structure"], None))
        a = adapt_mod.adapt(tmp, local, spec_name=None, interface=True)
        vt = a["verified_top"]
        rep2 = intake.run(host, tmp / "rtl", top=vt, listed=sim.rtl_files(tmp / "rtl"),
                          defines=src.get("defines"), spec=tmp / a["interface"])
        spec_err = [f["message"] for f in (rep2.get("spec") or {}).get("findings", []) if f["severity"] == "error"]
        # the next steps of the flow on this input: the contract reads the interface document, and the
        # simulation compares it with the port list it parses from the RTL (sim.dut_ports)
        try:
            iface = contract.extract_interface(build_index(tmp / a["interface"]), top=vt)
            tree = {p["name"]: p for p in rep2["ports"]}
            contract_issues = [f"{p['name']}: {p['direction']} {p['width']} vs RTL "
                               f"{tree[p['name']]['direction']} {tree[p['name']].get('width')}"
                               for p in iface["ports"] if p["name"] in tree and
                               (p["direction"] != tree[p["name"]]["direction"] or
                                str(p["width"]) != str(tree[p["name"]].get("width")))]
            contract_issues += [f"{n}: not in the contract" for n in tree if n not in {p["name"] for p in iface["ports"]}]
            clock, reset = iface.get("clock"), (iface.get("reset") or {}).get("name")
        except ValueError as e:
            contract_issues, clock, reset = [f"contract: {e}"], None, None
        try:
            conf = (sim.conformance({"interface": iface}, sim.dut_ports(sim.rtl_files(tmp / "rtl"), vt))
                    if clock is not None or not contract_issues else [])
        except (ValueError, NameError) as e:
            conf = [f"dut_ports: {e}"]
        out = {"verified_top": vt, "verdict": rep2["verdict"], "codes": rep2["codes"],
               "interface_errors": spec_err, "contract_issues": contract_issues[:10],
               "conformance_issues": conf[:10], "clock": clock, "reset": reset,
               "reasons": [r["message"] for r in rep2["reasons"] if r["level"] != "note"]}
        if smoke and not contract_issues and not conf and rep2["verdict"] == "ready":
            out["smoke"] = _smoke(host, tmp, vt, iface, src, rep2.get("frontend") or "verilog")
        return out
    except Exception as e:  # noqa: BLE001 - recorded as the result of this design
        return {"verdict": "error", "error": _err(e)}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_one(host, src: dict, root: Path, top: str, do_adapt: bool, smoke: bool = False) -> dict:
    rtl = root / src["rtl"]
    libs = [root / x for x in src.get("libs") or []] + [Path(x) for x in src.get("abs_libs") or []]
    try:
        rep = intake.run(host, rtl, top=top, libs=libs, defines=src.get("defines"), timeout_s=600)
    except Exception as e:  # noqa: BLE001
        return {"source": src["name"], "top": top, "verdict": "error", "error": _err(e)}
    kinds = Counter(p["kind"] for p in rep["ports"])
    s = rep.get("structure") or {}
    row = {"source": src["name"], "top": top, "verdict": rep["verdict"], "codes": rep["codes"],
           "frontend": rep["frontend"], "files": len(rep["collect"].get("files") or []),
           "ports": len(rep["ports"]), "port_kinds": dict(kinds),
           "reasons": [{"level": r["level"], "message": r["message"][:300]} for r in rep["reasons"]],
           "errors": rep.get("errors"),
           "clocks": len(s.get("clocks") or {}), "async_resets": len(s.get("async_resets") or {}),
           "flop_bits": s.get("flop_bits"), "latches": s.get("latches"), "tristate": s.get("tristate")}
    if do_adapt and rep["verdict"] in ("ready", "adapt"):
        row["adapt"] = _adapt_check(host, rep, src, smoke)
    return row


def run(manifest: Path = MANIFEST, cache: Path | None = None, *, host=None, only: list[str] | None = None,
        do_adapt: bool = True, smoke: bool = False, workers: int = 4, say=print) -> dict:
    man = json.loads(manifest.read_text(encoding="utf-8"))
    cache = cache or manifest.parent / ".cache"
    rows = []
    for src in man["sources"]:
        if only and src["name"] not in only:
            continue
        root = fetch(src, cache)
        # dependencies (other repositories at fixed commits): their folders become library folders
        dep_libs = []
        for dep in src.get("deps") or []:
            droot = fetch({**dep, "name": f"{src['name']}__{dep['name']}"}, cache)
            dep_libs += [str(droot / x) for x in dep.get("libs") or ["."]]
        if dep_libs:
            src = {**src, "abs_libs": dep_libs}
        tops = tops_of(src, root)
        say(f"[corpus] {src['name']}: {len(tops)} tops")
        with ThreadPoolExecutor(max_workers=workers) as ex:
            for row in ex.map(lambda t: run_one(host, src, root, t, do_adapt, smoke), tops):
                rows.append(row)
                ad = row.get("adapt") or {}
                sm = (ad.get("smoke") or {}).get("status")
                say(f"  {row['top']:<36} {row['verdict']:<12}" + (f" -> {ad.get('verdict')}" if ad else "")
                    + (f", smoke {sm}" if sm else ""))
    return {"manifest": man, "rows": rows, "summary": summarize(rows)}


def final_verdict(row: dict) -> str:
    """ready / adapted / needs_input / unsupported / error / chain_failed, after the adaptation and the
    contract and port checks of the next steps."""
    ad = row.get("adapt") or {}
    if row["verdict"] in ("ready", "adapt"):
        if (ad.get("verdict") != "ready" or ad.get("interface_errors") or ad.get("contract_issues")
                or ad.get("conformance_issues")):
            return "chain_failed"
        return "ready" if row["verdict"] == "ready" else "adapted"
    return row["verdict"]


def _detail(row: dict) -> list[str]:
    """The reasons that stop a design, as the steps gave them."""
    out = [x["message"] for x in row.get("reasons") or [] if x["level"] in ("needs_input", "unsupported")]
    ad = row.get("adapt") or {}
    if final_verdict(row) == "chain_failed":
        out += list(ad.get("contract_issues") or ad.get("conformance_issues") or ad.get("reasons") or
                    [ad.get("error") or f"verified top: {ad.get('verdict')}"])[:2]
    return out


def _blocking(row: dict) -> list[str]:
    """Classes of the reasons that stop a design (one entry per class)."""
    out = [_reason_class(x["message"]) for x in row.get("reasons") or [] if x["level"] in ("needs_input", "unsupported")]
    ad = row.get("adapt") or {}
    if final_verdict(row) == "chain_failed":
        out.append("flow: contract from the interface document" if ad.get("contract_issues") else
                   "flow: port check against the RTL (sim.dut_ports)" if ad.get("conformance_issues") else
                   "flow: adaptation (" + _reason_class(str((ad.get("reasons") or [ad.get("error")])[0])) + ")")
    return list(dict.fromkeys(out))


def summarize(rows: list[dict]) -> dict:
    by_src: dict[str, Counter] = {}
    for r in rows:
        by_src.setdefault(r["source"], Counter())[final_verdict(r)] += 1
    total = Counter(final_verdict(r) for r in rows)
    blocking = Counter(c for r in rows for c in _blocking(r)[:1])
    smoke = Counter((r.get("adapt") or {}).get("smoke", {}).get("status") for r in rows
                    if (r.get("adapt") or {}).get("smoke"))
    return {"total": dict(total), "by_source": {k: dict(v) for k, v in by_src.items()}, "blocking": dict(blocking),
            "smoke": dict(smoke), "designs": len(rows)}


ORDER = ("ready", "adapted", "needs_input", "unsupported", "chain_failed", "adapt_failed", "error")


def compare(recorded: dict, got: dict) -> list[str]:
    """Differences of verdict and smoke status between a rerun and the recorded results, for the sources
    of the rerun."""
    srcs = {r["source"] for r in got["rows"]}
    old = {(r["source"], r["top"]): r for r in recorded.get("rows", []) if r["source"] in srcs}
    new = {(r["source"], r["top"]): r for r in got["rows"]}
    out = []
    for k in sorted(set(old) | set(new)):
        a, b = old.get(k), new.get(k)
        if a is None or b is None:
            out.append(f"{k[0]}/{k[1]}: {'new design' if a is None else 'design missing in the rerun'}")
            continue
        va, vb = final_verdict(a), final_verdict(b)
        sa = ((a.get("adapt") or {}).get("smoke") or {}).get("status")
        sb = ((b.get("adapt") or {}).get("smoke") or {}).get("status")
        if va != vb:
            out.append(f"{k[0]}/{k[1]}: verdict {va} -> {vb}")
        elif sa != sb and sb is not None:
            out.append(f"{k[0]}/{k[1]}: smoke {sa} -> {sb}")
    return out


def to_markdown(res: dict) -> str:
    """corpus/results.md: the verdict of every design of the corpus."""
    rows, summ, man = res["rows"], res["summary"], res["manifest"]
    L = ["# Input corpus: results", "",
         "Generated by `nnc corpus` from corpus/corpus.json (no agent). Each module of each repository is taken as "
         "the top of a design. Verdicts after `nnc adapt`: **ready** (runs as it is), **adapted** (runs after the "
         "generated wrapper), **needs_input** (the designer must give something: a library, a parameter value), "
         "**unsupported** (the flow cannot run on it, with the reason), **chain_failed** (a step after the intake "
         "failed: a fault of the flow). Smoke (generic test: clock, reset, 200 cycles of random inputs): **pass**, "
         "**dut_assertion** (an assertion of the design stopped the run: random inputs break a rule of its inputs; the "
         "machinery works), **simulator_unsupported** (Verilator builds no model of this RTL), **test_failed**, "
         "**build_failed**. See docs/INPUT_SUPPORT.md.", "",
         "| Source | Commit | Licence | Language | Designs | " + " | ".join(ORDER[:5]) + " | smoke pass |",
         "|---|---|---|---|---|" + "---|" * 6]
    for src in man["sources"]:
        mine = [r for r in rows if r["source"] == src["name"]]
        if not mine:
            continue
        c = Counter(final_verdict(r) for r in mine)
        sm = sum(1 for r in mine if ((r.get("adapt") or {}).get("smoke") or {}).get("status") == "pass")
        smk = sum(1 for r in mine if (r.get("adapt") or {}).get("smoke"))
        L.append(f"| {src['name']} | `{src['commit'][:10]}` | {src['license']} | {src['language']} | {len(mine)} | "
                 + " | ".join(str(c.get(k, 0)) for k in ORDER[:5]) + f" | {sm}/{smk} |")
    t = summ["total"]
    L.append(f"| **all** | | | | **{len(rows)}** | " + " | ".join(f"**{t.get(k, 0)}**" for k in ORDER[:5]) +
             f" | **{summ.get('smoke', {}).get('pass', 0)}/{sum(summ.get('smoke', {}).values())}** |")
    L += ["", "## Why a design stops", "", "| Reason (first one per design) | Designs |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in sorted(summ["blocking"].items(), key=lambda kv: -kv[1])]
    L += ["", "## Every design", "", "| Source | Top | Verdict | Ports (kinds) | Clocks | Frontend | Smoke | Reason |",
          "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        ad = r.get("adapt") or {}
        sm = ad.get("smoke") or {}
        smoke = sm.get("status", "")
        if sm.get("coverage"):
            smoke += " (line " + str(sm["coverage"].get("line")) + " %)"
        kinds = ", ".join(f"{k} {v}" for k, v in sorted((r.get("port_kinds") or {}).items()))
        reason = "; ".join(_detail(r))[:160]
        if not reason and sm.get("assertion"):
            reason = f"assertion of the design at {sm['assertion']} stopped the random test"
        elif not reason and sm.get("status") not in (None, "pass"):
            reason = (sm.get("failure") or "; ".join(sm.get("build_errors") or []))[:160]
        L.append(f"| {r['source']} | {r['top']} | {final_verdict(r)} | {r.get('ports', '')} ({kinds}) | "
                 f"{r.get('clocks', '')} | {r.get('frontend') or ''} | {smoke} | {reason.replace('|', '/')} |")
    return "\n".join(L) + "\n"


def _reason_class(msg: str) -> str:
    for key, label in (("VHDL", "VHDL source"), ("encrypted", "encrypted source"),
                       ("Verilator cannot read", "Verilator rejects the RTL"),
                       ("is declared in no file: add", "unit of another library missing"),
                       ("has no default value", "top parameter without default"),
                       ("has no adapter", "port type without adapter"), ("candidate top", "top ambiguous"),
                       ("package", "missing package"), ("include file", "missing include"),
                       ("specification", "specification")):
        if key in msg:
            return label
    return msg[:60]

"""Formal equivalence of the surviving mutants (`nnc mutate-equiv`, code only, no agent).

A mutant that survives mutation testing is either a gap of the verification or an *equivalent* mutant:
one that changes no output for any input. Agent A12 can only claim the second. Here the claim is
checked: the original RTL and the mutant are compared with the Yosys miter of nnc/equiv.py (the one
`nnc restyle` uses), in every configuration in which the mutant survived.

    PROVEN      no input sequence after reset makes any output differ: the mutant is equivalent in that
                configuration, and the mutation score may leave it out.
    CEX         some input sequence makes an output differ; the first differing outputs are named and the
                trace is kept in work/mutation_equiv/. The verification did not notice a real change of
                behaviour, unless that input sequence breaks a rule of the environment: in this check the
                inputs are free after reset (the formal environment of verif/formal is not applied).
    BOUNDED     no difference within the depth, proof not closed: nothing is concluded.
    SIM_ONLY    the mutated line is simulation-only code (`ifndef *SYNTHESIS): formal reads the synthesis
                branch, so it cannot judge it.
    ERROR       the miter could not be built.
Overall per mutant: CEX if a configuration gives CEX; PROVEN only if every configuration is PROVEN.
"""
from __future__ import annotations

from pathlib import Path

from nnc import equiv, params, rtlcheck, sim
from nnc.contract import is_async
from nnc.simhost import SimHost


def _configs(m: dict, run_set: dict | None) -> list[dict]:
    """[{label, overrides}] of the runs in which mutant `m` survived (distinct parameter sets)."""
    if not run_set or not m.get("run"):
        return [{"label": m.get("run") or "default", "overrides": {}}]
    by_label = {r["label"]: r for r in run_set["runs"]}
    out, seen = [], set()
    for label in [m["run"]] + list(m.get("also_run") or []):
        over = dict((by_label.get(label) or {}).get("overrides") or {})
        key = tuple(sorted(over.items()))
        if key not in seen:
            seen.add(key)
            out.append({"label": label, "overrides": over})
    return out


def in_sim_only(text: str, line: int) -> bool:
    """Is 1-based `line` inside a simulation-only region (blanked by rtlcheck.sim_only)?"""
    blanked = rtlcheck.sim_only(rtlcheck.strip_comments(text))[0].splitlines()
    orig = text.splitlines()
    return 0 < line <= len(orig) and orig[line - 1].strip() != "" and \
        (line > len(blanked) or blanked[line - 1].strip() == "")


def check_mutant(host: SimHost, contract: dict, rtl_dir: Path, m: dict, run_set: dict | None, *,
                 depth: int = 20, timeout_s: int = 900, trace_dir: Path | None = None,
                 frontend: str = "verilog", defines: list[str] | None = None) -> dict:
    """`frontend` and `defines` are those of the formal run (config formal_frontend, formal_defines)."""
    files = sim.rtl_files(rtl_dir)
    original = {f.name: f.read_text(encoding="utf-8", errors="replace") for f in files}
    order = [f.name for f in files]
    if m["file"] not in original:
        return {"status": "ERROR", "detail": f"{m['file']} is not in rtl/ any more", "per_config": {}}
    if in_sim_only(original[m["file"]], m["line"]):
        return {"status": "SIM_ONLY", "per_config": {},
                "detail": "the line is simulation-only code (`ifndef *SYNTHESIS); formal reads the synthesis branch"}
    lines = original[m["file"]].splitlines()
    lines[m["line"] - 1] = m["mutated"]
    mutant = dict(original)
    mutant[m["file"]] = "\n".join(lines) + "\n"
    macros = sorted({mac for n in order for mac, _ in rtlcheck.sim_only(rtlcheck.strip_comments(original[n]))[1]}
                    | set(defines or []))
    per: dict[str, dict] = {}
    for conf in _configs(m, run_set):
        values = params.resolve(contract["interface"], conf["overrides"])
        eq = equiv.run(host, contract, values, original, order, mutant, order, defines=macros, depth=depth,
                       timeout_s=timeout_s, multiclock=is_async(contract["interface"]), frontend=frontend)
        rec = {"status": eq["status"], "overrides": conf["overrides"]}
        if eq["status"] == "CEX":
            rec["first_difference"] = equiv.cex_outputs(eq.get("trace"), contract).replace("rewritten", "mutant")
            if trace_dir is not None and eq.get("trace") and Path(eq["trace"]).is_file():
                trace_dir.mkdir(parents=True, exist_ok=True)
                dst = trace_dir / f"{m['id']}_{conf['label']}.vcd"
                dst.write_bytes(Path(eq["trace"]).read_bytes())
                rec["trace"] = dst.as_posix()
        elif eq["status"] == "ERROR":
            rec["detail"] = eq.get("detail", "")[:600]
        per[conf["label"]] = rec
    sts = [v["status"] for v in per.values()]
    status = ("CEX" if "CEX" in sts else "PROVEN" if sts and all(s == "PROVEN" for s in sts)
              else "ERROR" if "ERROR" in sts else "BOUNDED")
    return {"status": status, "depth": depth, "frontend": frontend, "mutated": m["mutated"], "per_config": per}


FINAL = ("PROVEN", "CEX", "BOUNDED", "SIM_ONLY")


def reusable(m: dict, depth: int, frontend: str) -> bool:
    """Is the recorded result of mutant `m` one this run would compute again (same mutated line, depth and
    frontend, and a conclusion rather than ERROR)? Such a result is kept, so an interrupted run resumes."""
    e = m.get("equivalence") or {}
    return (e.get("status") in FINAL and e.get("depth") == depth and e.get("frontend") == frontend
            and e.get("mutated") == m.get("mutated"))


def run(host: SimHost, contract: dict, rtl_dir: Path, mutation: dict, run_set: dict | None, *,
        depth: int = 20, timeout_s: int = 900, trace_dir: Path | None = None, say=print,
        frontend: str = "verilog", defines: list[str] | None = None, redo: bool = False, save=None) -> dict:
    """Check every surviving mutant; write the result into mutation["mutants"][i]["equivalence"] and a
    summary into mutation["equivalence"]. The recorded kill/survive results are not changed.
    A result that `reusable` accepts is kept unless `redo`; `save(mutation)` is called after each mutant."""
    for m in mutation["mutants"]:
        if m["status"] != "survived":
            continue
        if not redo and reusable(m, depth, frontend):
            say(f"[mutate-equiv] {m['id']} {m['file']}:{m['line']}: {m['equivalence']['status']} (kept from the last run)")
            continue
        if trace_dir is not None and trace_dir.is_dir():
            for old in trace_dir.glob(f"{m['id']}_*.vcd"):
                old.unlink()
        m["equivalence"] = check_mutant(host, contract, rtl_dir, m, run_set, depth=depth, timeout_s=timeout_s,
                                        trace_dir=trace_dir, frontend=frontend, defines=defines)
        e = m["equivalence"]
        diff = next((v.get("first_difference") for v in e["per_config"].values() if v.get("first_difference")), "")
        say(f"[mutate-equiv] {m['id']} {m['file']}:{m['line']}: {e['status']}" + (f" — {diff}" if diff else ""))
        if save is not None:
            mutation["equivalence"] = summary(mutation)
            save(mutation)
    mutation["equivalence"] = summary(mutation)
    return mutation


def summary(mutation: dict) -> dict:
    surv = [m for m in mutation["mutants"] if m["status"] == "survived"]
    counts: dict[str, int] = {}
    for m in surv:
        st = (m.get("equivalence") or {}).get("status", "NOT_CHECKED")
        counts[st] = counts.get(st, 0) + 1
    proven = counts.get("PROVEN", 0)
    killed = mutation.get("killed", 0)
    relevant = killed + len(surv) - proven
    return {"by_status": dict(sorted(counts.items())), "proven_equivalent": proven,
            "score_without_equivalent": round(100 * killed / relevant, 1) if relevant else None}

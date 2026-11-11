"""Reviewer packet for the sign-off gate G4 (`nnc packet`, code only, no LLM).

The report (report.md) lists every check and rule. A person asked to sign off needs something else:
the few things that need a human judgement, each with its evidence and a question to answer. This
module gathers them from the artifacts of the flow, never from a model:
  * decisions taken on delegation by an agent (gate notes),
  * failures with the triage analysis (an RTL bug, a test bug, or a specification question),
  * hand edits of generated verification code (G3 note and the design NOTICE),
  * what this simulation did not verify, and why,
  * weak spots: surviving mutants, rules below the mutation threshold, uncovered code,
  * how to reproduce everything without NNC.
It ends with a checklist; the reviewer's answers are the basis of `nnc gate approve <ip> G4_signoff`.
"""
from __future__ import annotations

import json
from pathlib import Path

CATEGORY = {"A_rtl_wrong": "the RTL is likely wrong", "B_test_wrong": "the test or checker is likely wrong",
            "C_spec_unclear": "the specification is unclear or contradicts itself"}


def _load(p: Path) -> dict | list | None:
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def _cut(text: str, n: int = 400) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def build(d) -> str:
    """Markdown packet of design `d` (nnc.project.Design)."""
    w = d.work
    rep, rtm = _load(w / "report.json"), _load(w / "rtm.json") or []
    if rep is None:
        raise FileNotFoundError("work/report.json is missing: run `nnc report` first")
    tri = _load(w / "triage.json") or {}
    mut = _load(w / "mutation.json") or {}
    gates = d._read_state().get("gates", {})
    sim = rep.get("simulation") or {}
    checks = rep["checks"]["detail"]
    q: list[str] = []                                  # checklist for the reviewer
    out = [f"# Sign-off packet — {d.name}", "",
           "This packet is for the person who decides gate **G4 (sign-off)**: *is this design verified well "
           "enough against its specification to release?* It collects only the items that need a human "
           "judgement. Everything else is in `work/report.md` (all checks and rules) and `work/triage.md`.", ""]
    if rep.get("unreviewed_gates"):
        out += [f"> **Not ready:** gates {', '.join(rep['unreviewed_gates'])} were bypassed. Approve them first.", ""]

    # ------------------------------------------------------------------ 1. summary
    by_rule, by_chk = rep["rules"]["by_status"], rep["checks"]["by_status"]
    out += ["## 1. Summary", "",
            f"- **Requirements (rules):** {rep['rules']['total']} — " + ", ".join(f"{k} {v}" for k, v in by_rule.items()),
            f"- **Checks:** {rep['checks']['total']} — " + ", ".join(f"{k} {v}" for k, v in by_chk.items()),
            f"- **Tests:** {sim.get('tests')}"]
    rs = sim.get("run_set")
    if rs:
        cfgs = list(dict.fromkeys(r["config"] for r in rs["runs"]))
        out.append(f"- **Simulated configurations:** {len(rs['runs'])} runs in {len(cfgs)} configurations "
                   f"({', '.join(cfgs)}); see `run_set.json` and the *Run set* table of the report")
    else:
        out.append(f"- **Simulated configuration:** one (parameters {sim.get('params')}, seed {sim.get('seed')})")
    cov = ((sim.get("coverage") or {}).get("metrics") or {})
    if cov:
        out.append("- **Code coverage:** " + ", ".join(f"{k} {v['percent']} %" for k, v in cov.items() if v.get("total")))
    if rep.get("mutation"):
        m = rep["mutation"]
        out.append(f"- **Mutation score:** {m['score']} % ({m['killed']} of {m['killed'] + m['survived']} injected "
                   f"faults detected)")
    out.append("")

    # ------------------------------------------------------------------ 2. delegated decisions
    out += ["## 2. Decisions taken for you", ""]
    deleg = [(g, r) for g, r in gates.items() if g != "G4_signoff" and "delegated" in r.get("by", "")]
    if deleg:
        out += ["These gates were approved by an AI agent on delegation, not by a qualified person. Read each note.", ""]
        for g, r in deleg:
            out.append(f"- **{g}** ({r['at']}): {_cut(r.get('note'), 900)}")
            q.append(f"I have read the delegated decisions of {g} and agree with them (or I have corrected them).")
        out.append("")
    else:
        out += ["Every earlier gate was approved by a named person.", ""]

    # ------------------------------------------------------------------ 3. failures
    out += ["## 3. Failures and what they mean", ""]
    failing = [c for c, v in checks.items() if v["status"] in ("FAIL", "NOT_HIT", "NOT_RUN")]
    analyses = tri.get("analyses") or []
    if not failing:
        out += ["No check fails, and every assertion was exercised.", ""]
    else:
        out += [f"Checks not passing: {', '.join(failing)}. The triage agent read the specification, the RTL, the "
                "tests and the logs, and gives the most likely cause. It changes nothing; you decide.", ""]
        for a in analyses:
            cat = a.get("most_likely", "")
            out += [f"### {_cut(a.get('failure'), 160)}", "",
                    f"- **Most likely:** {CATEGORY.get(cat, cat)}",
                    f"- **Specification:** {_cut(a.get('spec_says'), 500)}",
                    f"- **RTL:** {_cut(a.get('rtl_does'), 500)}",
                    f"- **Options:** {_cut(a.get('options'), 500)}", ""]
            if cat == "A_rtl_wrong":
                q.append(f"The RTL fault behind “{_cut(a.get('failure'), 90)}” is fixed, or accepted with a waiver.")
            elif cat == "C_spec_unclear":
                q.append(f"The specification question behind “{_cut(a.get('failure'), 90)}” is decided by the "
                         "specification owner, and the spec, contract or checker is updated.")
            else:
                q.append(f"The test/checker issue behind “{_cut(a.get('failure'), 90)}” is fixed and the run repeated.")
        if not analyses:
            q.append("The failing checks are analysed (`nnc triage`).")

    # ------------------------------------------------------------------ 4. hand edits
    notice = d.root / "NOTICE.md"
    edits = [ln.strip() for ln in notice.read_text(encoding="utf-8").splitlines()
             if "hand fix" in ln.lower() or "sửa tay" in ln.lower()] if notice.is_file() else []
    g3 = gates.get("G3_verif_sources", {}).get("note", "")
    if edits or "hand fix" in g3.lower():
        out += ["## 4. Hand edits of generated verification code", "",
                "Generated tests or checkers were edited by hand after triage found them wrong. An edit must "
                "correct the test, never weaken it to hide a design fault.", ""]
        out += [f"- {_cut(e, 2500)}" for e in edits]
        if "hand fix" in g3.lower():
            out.append(f"- Last G3 approval note: {_cut(g3, 700)}")
        out.append("")
        q.append("Each hand edit of the generated tests and checkers corrects the test and weakens no requirement.")

    # ------------------------------------------------------------------ 5. not verified
    out += ["## 5. What this verification does not cover", ""]
    nv = [(c, v) for c, v in checks.items() if v["status"] == "NOT_VERIFIABLE"]
    if nv:
        out += [f"**{len(nv)} check(s) could not be verified by any simulated configuration:**", ""]
        out += [f"- {c}: {_cut(v.get('reason'), 400)}" for c, v in nv]
        out.append("")
        q.append("The NOT_VERIFIABLE checks are covered elsewhere (another configuration, formal, lab) or accepted as open.")
    nvs = [r for r in rtm if r["status"] == "NOT_VERIFIED_BY_SIM"]
    if nvs:
        out += [f"**{len(nvs)} requirement(s) cannot be checked by simulation** (static, structural, timing, "
                "process...). They need another method: lint, CDC, STA, synthesis, review. First ones:", ""]
        out += [f"- {r['rule']} ({', '.join(r['spec_refs'])}): {_cut(r['statement'], 160)} — "
                f"*{_cut((r.get('not_verified') or {}).get('reason'), 140)}*" for r in nvs[:15]]
        if len(nvs) > 15:
            out.append(f"- … {len(nvs) - 15} more in work/rtm.json")
        out.append("")
        q.append("The requirements that simulation cannot check are assigned to another verification method.")
    weak = [r for r in rtm if r["status"] in ("NOT_PROVEN", "PARTIAL", "UNMAPPED")]
    if weak:
        out += [f"**{len(weak)} requirement(s) only partly or not proven:** "
                + ", ".join(f"{r['rule']} ({r['status']})" for r in weak[:25]), ""]
    out += ["Outside this flow in every case: formal proof, CDC/RDC analysis, static timing, synthesis, DFT.", ""]

    # ------------------------------------------------------------------ 6. weak spots
    out += ["## 6. Weak spots of the verification itself", ""]
    attr = (mut.get("attribution") or {}).get("mutants", {})
    surv = [m for m in mut.get("mutants", []) if m["status"] == "survived"]
    if mut:
        out += [f"Mutation testing changed one RTL line at a time ({mut.get('count')} faults"
                + (f", in run {mut['run']}" if mut.get("run") else "")
                + ("; each in the run that executes its line, a survivor again in every other configuration"
                   if mut.get("runs") else "") + "). A fault no check notices "
                "is a gap, unless it changes nothing visible (an *equivalent* mutant, claimed below by an agent).", ""]
        for m in surv:
            a = attr.get(m["id"], {})
            tag = "claimed equivalent: " + _cut(a.get("reason"), 200) if a.get("equivalent") else \
                "**gap** — " + _cut(a.get("reason"), 200)
            where = ", ".join([m["run"]] + m.get("also_run", [])) if m.get("run") else ""
            out.append(f"- {m['id']} `{m['file']}:{m['line']}` {m['operator']}"
                       + (f" (survived in {where})" if where else "") + f": {tag}")
        out.append("")
        below = (rep.get("mutation") or {}).get("rules_below_threshold") or []
        if surv:
            q.append("Each surviving mutant is either truly equivalent or a known gap I accept.")
        if below:
            out += [f"{len(below)} requirement(s) below the mutation threshold of {mut.get('threshold')} %: "
                    + ", ".join(below[:20]) + ("…" if len(below) > 20 else ""), ""]
    unc = [u for u in (sim.get("coverage") or {}).get("uncovered", []) if u["metric"] in ("line", "functional")]
    if unc:
        out += ["Code or cover points never reached (first ones):", ""]
        out += [f"- {u['metric']} {u['file']}:{u['line']} {u.get('what', '')}".rstrip() for u in unc[:10]]
        out.append("")
        q.append("The unreached code and cover points are unreachable by design or accepted.")

    # ------------------------------------------------------------------ 7. reproduce
    out += ["## 7. Reproduce without NNC", "",
            f"`designs/{d.name}/sim/` holds a Makefile that runs the same regression with Verilator and cocotb "
            "only (Linux or WSL):", "", "```bash", f"cd designs/{d.name}/sim", "make regression SEED=1 2>&1 | tee sim.log",
            f"cd ../../.. && python -m nnc kit-check {d.name}    # same outcome as the recorded results?", "```", ""]
    if rs:
        out += [f"The kit reproduces the primary run {rs['primary']}; the other runs differ only by the settings "
                "in `run_set.json`.", ""]
    q.append("I reproduced the regression (or CI did) and the outcome matches the report.")

    # ------------------------------------------------------------------ 8. checklist
    out += ["## 8. Checklist before signing", "",
            "Answer every item. Sign only if each one is true, or record why not in the approval note:", ""]
    out += [f"- [ ] {x}" for x in q]
    out += ["", "Then: `nnc gate approve " + d.name + " G4_signoff --by \"<your name>\" --note \"<waivers, open items>\"`. "
            "The approval is bound to the current results.json: a later run makes it STALE.", ""]
    return "\n".join(out)


def write(d) -> Path:
    path = d.work / "review_packet.md"
    path.write_text(build(d), encoding="utf-8")
    return path

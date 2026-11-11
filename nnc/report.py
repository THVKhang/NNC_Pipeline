"""Report and requirement traceability matrix (stage 6, code only).

Status of a check:
  PASS      assertion: hit at least once and never failed; test: passed
  FAIL      assertion failed at least once; test failed
  NOT_HIT   assertion never active (proves nothing, principle PR-4)
  NOT_RUN   no evidence (not built, test missing, simulation not run)
  NOT_VERIFIABLE  the test declared (not_verifiable) that this run cannot verify it (with a run set:
                  every run declared it; one run that verified it is enough for PASS)
  NOT_SELECTED    left out of the test plan by the designer (`nnc plan --select`); never PASS
Status of a rule: VERIFIED (all its checks PASS), FAILED (any FAIL), PARTIAL (some PASS, rest not
proven), NOT_PROVEN (checks exist, none PASS), NOT_VERIFIED_BY_SIM (declared in the contract with a
reason), NOT_SELECTED (all its checks left out of the test plan), UNMAPPED (no check and no
reason: a contract gap).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


def check_status(results: dict | None, contract: dict, test_map: dict[str, list[str]] | None = None) -> dict[str, dict]:
    """test_map: test function name -> check IDs named in its docstring (gen_tests.test_check_map)."""
    out = {}
    test_map = test_map or {}
    tests = [dict(t, doc=" ".join(test_map.get(t["name"], []))) for t in (results or {}).get("tests", [])]
    asserts = (results or {}).get("assertions", {})
    ran = bool(results) and results.get("status") == "ran"
    sel = contract.get("selection") or {}
    off = set(sel.get("not_selected", [])) if sel.get("mode") == "selected" else set()
    for c in contract["checks"]:
        if c["id"] in off:
            out[c["id"]] = {"status": "NOT_SELECTED", "by": sel.get("by")}
            continue
        if c["kind"] == "assertion":
            v = asserts.get(c["id"])
            if not ran or v is None:
                st = "NOT_RUN"
            elif v["fails"] > 0:
                st = "FAIL"
            elif v["hits"] == 0:
                st = "NOT_HIT"
            else:
                st = "PASS"
            out[c["id"]] = {"status": st, **(v or {})}
        else:
            num = c["id"].split("-")[1]
            mine = [t for t in tests if re.search(rf"chk_{num}(?!\d)", t["name"].lower())
                    or c["id"] in (t.get("doc") or "")]
            nv = (results or {}).get("not_verifiable", {}).get(c["id"])
            if not ran or not mine:
                out[c["id"]] = {"status": "NOT_RUN", "tests": [t["name"] for t in mine]}
            elif any(t["status"] == "fail" for t in mine):
                out[c["id"]] = {"status": "FAIL", "tests": [t["name"] for t in mine]}
            elif nv:  # the test declared that this run cannot verify (part of) the check
                out[c["id"]] = {"status": "NOT_VERIFIABLE", "tests": [t["name"] for t in mine], "reason": nv}
            else:
                out[c["id"]] = {"status": "PASS", "tests": [t["name"] for t in mine]}
            if ran and mine and (results or {}).get("run_set"):
                out[c["id"]].update(_test_runs(c["id"], mine, results))
    return out


def _test_runs(cid: str, mine: list[dict], results: dict) -> dict:
    """Run set: the runs in which the check's tests passed without declaring it not verifiable, and the
    runs in which one of them failed."""
    nv = results.get("not_verifiable_by_run") or {}
    labels = [r["label"] for r in results["run_set"]["runs"] if r["status"] == "ran"]
    verified = [lb for lb in labels if all((t.get("runs") or {}).get(lb) == "pass" for t in mine)
                and cid not in nv.get(lb, {})]
    failed = [lb for lb in labels if any((t.get("runs") or {}).get(lb) == "fail" for t in mine)]
    return {"verified_in": verified, "failed_in": failed}


def _runs_text(d: dict, kind: str) -> str:
    """Evidence suffix of a check under a run set."""
    if kind == "assertion":
        runs = d.get("runs") or {}
        bad = [lb for lb, v in runs.items() if v["fails"] > 0]
        hit = [lb for lb, v in runs.items() if v["hits"] > 0]
        if not runs:
            return ""
        return f"; fails in {', '.join(bad)}" if bad else f"; hit in {len(hit)}/{len(runs)} runs"
    if d.get("failed_in"):
        return f"; failed in {', '.join(d['failed_in'])}"
    if "verified_in" in d:
        return f"; verified in {', '.join(d['verified_in'])}" if d["verified_in"] else "; verified in no run"
    return ""


def rtm(rules_doc: dict, contract: dict, statuses: dict[str, dict], mutation: dict | None = None) -> list[dict]:
    nv = {n["rule"]: n for n in contract.get("not_verified", [])}
    mscore = (mutation or {}).get("rule_scores", {})
    rows = []
    for r in rules_doc["rules"]:
        chks = [c["id"] for c in contract["checks"] if r["id"] in c["rules"]]
        sts = [statuses[c]["status"] for c in chks if c in statuses]
        if chks and all(s == "NOT_SELECTED" for s in sts):
            st = "NOT_SELECTED"
        elif chks:
            sts = [s for s in sts if s != "NOT_SELECTED"]
            if any(s == "FAIL" for s in sts):
                st = "FAILED"
            elif sts and all(s == "PASS" for s in sts):
                st = "VERIFIED"
            elif any(s == "PASS" for s in sts):
                st = "PARTIAL"
            else:
                st = "NOT_PROVEN"
        elif r["id"] in nv:
            st = "NOT_VERIFIED_BY_SIM"
        else:
            st = "UNMAPPED"
        rows.append({"rule": r["id"], "spec_refs": r.get("spec_refs", []), "doc": r.get("doc"),
                     "section": r["section"], "sentences": r["sentences"], "strength": r["strength"],
                     "statement": r["statement"], "checks": chks, "check_status": {c: statuses[c]["status"] for c in chks if c in statuses},
                     "status": st, "not_verified": nv.get(r["id"]), "mutation": mscore.get(r["id"])})
    return rows


def _count(items, key="status") -> dict:
    out: dict[str, int] = {}
    for i in items:
        out[i[key]] = out.get(i[key], 0) + 1
    return dict(sorted(out.items()))


def build(design_name: str, gates: list, rules_doc: dict, contract: dict, results: dict | None,
          mutation: dict | None, triage: dict | None, costs: dict, unreviewed: list[str],
          test_map: dict[str, list[str]] | None = None, closure: dict | None = None) -> dict:
    statuses = check_status(results, contract, test_map)
    rows = rtm(rules_doc, contract, statuses, mutation)
    return {
        "design": design_name, "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "gates": [{"gate": g.gate, "state": g.state, "detail": g.detail} for g in gates],
        "unreviewed_gates": unreviewed,
        "rules": {"total": len(rows), "by_status": _count(rows)},
        "checks": {"total": len(statuses), "by_status": _count(list(statuses.values())), "detail": statuses},
        "simulation": None if not results else {
            "status": results.get("status"), "seed": results.get("seed"), "params": results.get("params"),
            "tests": _count(results.get("tests", [])), "integration": results.get("integration"),
            "coverage": results.get("coverage"), "run_set": results.get("run_set")},
        "mutation": None if not mutation else {
            **{k: mutation[k] for k in ("count", "killed", "survived", "not_compiled", "score")},
            "threshold": mutation.get("threshold"),
            "rules_attributed": len(mutation.get("rule_scores") or {}),
            "rules_below_threshold": sorted(r for r, v in (mutation.get("rule_scores") or {}).items()
                                            if not v["meets_threshold"])},
        "coverage_closure": None if not closure else {k: closure.get(k) for k in
                                                      ("metric", "target", "status", "baseline", "final")},
        "triage": None if not triage else {"clusters": triage.get("clusters"), "analysed": triage.get("analysed")},
        "agent_cost_usd": costs,
        "rtm": rows,
    }


COVERAGE_LABELS = {"line": "lines", "block": "statement blocks and branch arms", "toggle": "bit toggles 0->1 and 1->0",
                   "expression": "condition terms", "fsm": "FSM states/arcs",
                   "functional": "cover points of the specification"}


def _coverage_rows(cov: dict) -> list[str]:
    """One row per code-coverage metric of the DUT RTL (never merged into one number)."""
    metrics = cov.get("metrics") or ({"line": cov} if cov.get("percent") is not None else {})
    if not metrics:
        return [f"| Code coverage (RTL) | {cov.get('status', 'not measured')} |"]
    return [f"| Code coverage (RTL), {m} | {v['percent']} % ({v['hit']}/{v['total']} {COVERAGE_LABELS.get(m, m)}) |"
            for m, v in metrics.items() if v.get("total")]


def _closure_rows(rep: dict) -> list[str]:
    c = rep.get("coverage_closure")
    if not c or c.get("status") in (None, "not_requested"):
        return ["| Coverage target | not requested (`nnc cover <design> --target <n> --metric <m>`) |"]
    b, f = c.get("baseline") or {}, c.get("final") or {}
    return [f"| Coverage target | {c['metric']} {c.get('target')} %: **{c['status']}** (baseline {b.get('percent')} % -> "
            f"{f.get('percent')} %, work/coverage.md) |"]


def signoff_conditions(rep: dict) -> list[tuple[str, bool, str]]:
    """The evidence a person needs before G4: every condition with its state (the person decides)."""
    by = rep["checks"]["by_status"]
    sim = rep.get("simulation") or {}
    mut = rep.get("mutation")
    clo = rep.get("coverage_closure")
    unmapped = rep["rules"]["by_status"].get("UNMAPPED", 0)
    conds = [
        ("Gates G1-G3 approved", not rep["unreviewed_gates"] and all(
            g["state"] == "APPROVED" for g in rep["gates"] if g["gate"] != "G4_signoff"),
         "approved on delegation by an agent: a person should confirm" if any(
             "delegated" in (g.get("detail") or "") for g in rep["gates"]) else ""),
        ("Interface conformance of the DUT", bool((sim.get("integration") or {}).get("ok")), ""),
        ("Every selected check PASS (no FAIL, NOT_HIT, NOT_RUN)", set(by) <= {"PASS", "NOT_VERIFIABLE", "NOT_SELECTED"},
         ", ".join(f"{k} {v}" for k, v in by.items() if k not in ("PASS", "NOT_SELECTED"))),
        ("Every planned check selected", "NOT_SELECTED" not in by,
         f"{by.get('NOT_SELECTED')} check(s) not selected in the test plan" if "NOT_SELECTED" in by else ""),
        ("Every rule in a check or declared not verifiable", unmapped == 0, f"{unmapped} unmapped" if unmapped else ""),
    ]
    rs = sim.get("run_set")
    if rs:
        failed = rs.get("failed_runs") or []
        conds.append(("Every run of the run set built and ran", not failed,
                      f"not run: {', '.join(failed)}" if failed else f"{len(rs['runs'])} runs"))
    conds += [
        ("Mutation run", bool(mut), "" if mut else "nnc mutate <design>"),
    ]
    if mut and mut.get("threshold") is None:
        conds.append(("Per-requirement mutation score", False, "mutants not attributed to rules: re-run nnc mutate"))
    elif mut:
        below = mut.get("rules_below_threshold") or []
        conds.append((f"Per-requirement mutation score >= {mut.get('threshold'):g} %", not below,
                      (f"{len(below)} rule(s) below: {', '.join(below[:10])}" if below else
                       f"{mut.get('rules_attributed')} rules with attributed mutants")))
    if clo and clo.get("status") not in (None, "not_requested"):
        conds.append((f"Coverage target {clo['metric']} {clo.get('target')} %", clo["status"] == "target_met", clo["status"]))
    return conds


def to_markdown(rep: dict, contract: dict, mutation: dict | None) -> str:
    sim = rep["simulation"] or {}
    cov = (sim.get("coverage") or {})
    out = [f"# Verification report — {rep['design']}", "", f"Generated {rep['date']} by NNC Pipeline.", ""]
    if rep["unreviewed_gates"]:
        out += [f"> **UNREVIEWED RUN.** Gates not approved by a person when this ran: {', '.join(rep['unreviewed_gates'])}. "
                "These results are exploratory and cannot be signed off.", ""]
    out += ["## Summary", "", "| Item | Result |", "|---|---|",
            f"| Rules | {rep['rules']['total']} — {rep['rules']['by_status']} |",
            f"| Checks | {rep['checks']['total']} — {rep['checks']['by_status']} |",
            f"| Tests | {sim.get('tests', 'not run')} |",
            *_run_set_summary(sim.get("run_set")),
            f"| Integration | {'OK' if (sim.get('integration') or {}).get('ok') else sim.get('integration')} |",
            *_coverage_rows(cov),
            f"| Mutation score | {str(rep['mutation']['score']) + ' % (' + str(rep['mutation']['killed']) + ' killed / ' + str(rep['mutation']['survived']) + ' survived / ' + str(rep['mutation']['not_compiled']) + ' not compiled)' if rep['mutation'] else 'not run'} |",
            *_closure_rows(rep),
            f"| Triage | {'no failure to analyse' if not rep['triage'] or not rep['triage'].get('clusters') else str(rep['triage']['clusters']) + ' failure(s), ' + str(rep['triage'].get('analysed')) + ' analysed: work/triage.md'} |",
            f"| Agent cost | US${rep['agent_cost_usd']['total_usd']} in {rep['agent_cost_usd']['calls']} calls "
            f"({', '.join(f'{k} {v}' for k, v in rep['agent_cost_usd']['by_agent'].items())})"
            + (f"; of which US${rep['agent_cost_usd']['failed_usd']} in {rep['agent_cost_usd']['failed_calls']} "
               "failed calls (usage limit, timeout, invalid answer)" if rep['agent_cost_usd'].get('failed_usd') else "")
            + " |", "",
            "## Sign-off conditions", "", "| Condition | State |", "|---|---|"]
    out += [f"| {name} | {'met' if ok else '**not met**'}{' — ' + note if note else ''} |"
            for name, ok, note in signoff_conditions(rep)]
    out += _run_set_section(sim.get("run_set"))
    out += ["", "## Gates", "", "| Gate | State | Detail |", "|---|---|---|"]
    out += [f"| {g['gate']} | {g['state']} | {g['detail']} |" for g in rep["gates"]]
    out += ["", "## Checks", "", "| Check | Kind | Title | Status | Evidence |", "|---|---|---|---|---|"]
    for c in contract["checks"]:
        d = rep["checks"]["detail"][c["id"]]
        ev = (f"hits {d.get('hits')}, fails {d.get('fails')}" if c["kind"] == "assertion" else ", ".join(d.get("tests", [])))
        ev += _runs_text(d, c["kind"])
        out.append(f"| {c['id']} | {c['kind']} | {c['title']} | **{d['status']}** | {ev} |")
    out += ["", "## Requirement traceability (RTM)", "",
            "| Rule | Spec ref | Statement | Checks | Mutation | Status |", "|---|---|---|---|---|---|"]
    for r in rep["rtm"]:
        chk = ", ".join(f"{k}:{v}" for k, v in r["check_status"].items()) or (
            f"not verified: {r['not_verified']['reason']}" if r["not_verified"] else "—")
        mu = r.get("mutation")
        mtxt = (f"{mu['score']} % ({mu['killed']}/{mu['relevant']})" + ("" if mu["meets_threshold"] else " **below**")
                if mu else "—")
        out.append(f"| {r['rule']} | {', '.join(r['spec_refs'])} | {r['statement'].replace('|', chr(92) + '|')} | {chk} | {mtxt} | **{r['status']}** |")
    if mutation:
        attr = (mutation.get("attribution") or {}).get("mutants", {})
        out += ["", "## Mutants", "", "| ID | File:line | Operator | Status | Caught by | Rules | Equivalent? |",
                "|---|---|---|---|---|---|---|"]
        for m in mutation["mutants"]:
            a = attr.get(m["id"], {})
            eq = ("claimed: " + a.get("reason", "")[:160]) if a.get("equivalent") else ""
            out.append(f"| {m['id']} | {m['file']}:{m['line']} | {m['operator']} | {m['status']} | "
                       f"{', '.join(m['killed_by_checks'] + m['killed_by_tests'])[:120]} | {', '.join(a.get('rules', []))} | {eq} |")
    out += ["", "## Not verified by this run", "",
            "- Formal proof, CDC/RDC, STA, synthesis and DFT checks are outside this flow.",
            "- Rules marked NOT_VERIFIED_BY_SIM carry the contract's reason (static, structural, not observable...).",
            ("- Only the configurations of the run set above were simulated; code coverage is merged over its runs, "
             f"mutation testing used the primary run {(sim.get('run_set') or {}).get('primary')}."
             if sim.get("run_set") else "- Only the default parameter configuration was simulated (no run_set.json).")]
    return "\n".join(out) + "\n"


def _run_set_summary(rs: dict | None) -> list[str]:
    if not rs:
        return []
    cfgs = list(dict.fromkeys(r["config"] for r in rs["runs"]))
    return [f"| Run set | {len(rs['runs'])} runs in {len(cfgs)} configurations ({', '.join(cfgs)}); primary "
            f"{rs['primary']}{'; NOT RUN: ' + ', '.join(rs['failed_runs']) if rs.get('failed_runs') else ''} |"]


def _run_set_section(rs: dict | None) -> list[str]:
    """One row per run: what it changes from the default configuration and its result."""
    if not rs:
        return []
    out = ["", "## Run set", "", "Every check is merged over these runs: PASS when one run verified it and no run "
           "failed it; NOT_VERIFIABLE only when every run declared it so.", "",
           "| Run | Parameters changed | Defines | Plusargs | Status | Tests | Failing assertions | Not verifiable here |",
           "|---|---|---|---|---|---|---|---|"]
    for r in rs["runs"]:
        ov = ", ".join(f"{k}={v}" for k, v in (r.get("overrides") or {}).items()) or "defaults"
        o = r.get("opts") or {}
        out.append(f"| {r['label']}{' — ' + r['note'] if r.get('note') else ''} | {ov} | "
                   f"{', '.join(o.get('defines') or []) or '—'} | {o.get('plusargs') or '—'} | {r['status']} | "
                   f"{r.get('tests')} | {', '.join(r.get('assertions_failing') or []) or 'none'} | "
                   f"{len(r.get('not_verifiable') or [])} |")
    return out


def write(rep: dict, contract: dict, mutation: dict | None, work: Path) -> list[Path]:
    paths = [work / "report.json", work / "report.md", work / "rtm.json"]
    paths[0].write_text(json.dumps({k: v for k, v in rep.items() if k != "rtm"}, indent=1) + "\n", encoding="utf-8")
    paths[1].write_text(to_markdown(rep, contract, mutation), encoding="utf-8")
    paths[2].write_text(json.dumps(rep["rtm"], indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return paths

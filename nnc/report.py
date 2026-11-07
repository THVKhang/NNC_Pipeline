"""Report and requirement traceability matrix (stage 6, code only).

Status of a check:
  PASS      assertion: hit at least once and never failed; test: passed
  FAIL      assertion failed at least once; test failed
  NOT_HIT   assertion never active (proves nothing, principle PR-4)
  NOT_RUN   no evidence (not built, test missing, simulation not run)
  NOT_VERIFIABLE  the test declared (not_verifiable) that this run cannot verify it
Status of a rule: VERIFIED (all its checks PASS), FAILED (any FAIL), PARTIAL (some PASS, rest not
proven), NOT_PROVEN (checks exist, none PASS), NOT_VERIFIED_BY_SIM (declared in the contract with a
reason), UNMAPPED (no check and no reason: a contract gap).
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
    for c in contract["checks"]:
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
    return out


def rtm(rules_doc: dict, contract: dict, statuses: dict[str, dict]) -> list[dict]:
    nv = {n["rule"]: n for n in contract.get("not_verified", [])}
    rows = []
    for r in rules_doc["rules"]:
        chks = [c["id"] for c in contract["checks"] if r["id"] in c["rules"]]
        sts = [statuses[c]["status"] for c in chks if c in statuses]
        if chks:
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
                     "status": st, "not_verified": nv.get(r["id"])})
    return rows


def _count(items, key="status") -> dict:
    out: dict[str, int] = {}
    for i in items:
        out[i[key]] = out.get(i[key], 0) + 1
    return dict(sorted(out.items()))


def build(design_name: str, gates: list, rules_doc: dict, contract: dict, results: dict | None,
          mutation: dict | None, triage: dict | None, costs: dict, unreviewed: list[str],
          test_map: dict[str, list[str]] | None = None) -> dict:
    statuses = check_status(results, contract, test_map)
    rows = rtm(rules_doc, contract, statuses)
    return {
        "design": design_name, "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "gates": [{"gate": g.gate, "state": g.state, "detail": g.detail} for g in gates],
        "unreviewed_gates": unreviewed,
        "rules": {"total": len(rows), "by_status": _count(rows)},
        "checks": {"total": len(statuses), "by_status": _count(list(statuses.values())), "detail": statuses},
        "simulation": None if not results else {
            "status": results.get("status"), "seed": results.get("seed"), "params": results.get("params"),
            "tests": _count(results.get("tests", [])), "integration": results.get("integration"),
            "coverage": results.get("coverage")},
        "mutation": None if not mutation else {k: mutation[k] for k in ("count", "killed", "survived", "not_compiled", "score")},
        "triage": None if not triage else {"clusters": triage.get("clusters"), "analysed": triage.get("analysed")},
        "agent_cost_usd": costs,
        "rtm": rows,
    }


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
            f"| Integration | {'OK' if (sim.get('integration') or {}).get('ok') else sim.get('integration')} |",
            f"| Line coverage (RTL) | {str(cov.get('percent')) + ' % (' + str(cov.get('hit')) + '/' + str(cov.get('total')) + ')' if cov.get('percent') is not None else cov.get('status', 'not measured')} |",
            f"| Mutation score | {str(rep['mutation']['score']) + ' % (' + str(rep['mutation']['killed']) + ' killed / ' + str(rep['mutation']['survived']) + ' survived / ' + str(rep['mutation']['not_compiled']) + ' not compiled)' if rep['mutation'] else 'not run'} |",
            f"| Triage | {'no failure to analyse' if not rep['triage'] or not rep['triage'].get('clusters') else str(rep['triage']['clusters']) + ' failure(s), ' + str(rep['triage'].get('analysed')) + ' analysed: work/triage.md'} |",
            f"| Agent cost | US${rep['agent_cost_usd']['total_usd']} in {rep['agent_cost_usd']['calls']} calls "
            f"({', '.join(f'{k} {v}' for k, v in rep['agent_cost_usd']['by_agent'].items())}) |", "",
            "## Gates", "", "| Gate | State | Detail |", "|---|---|---|"]
    out += [f"| {g['gate']} | {g['state']} | {g['detail']} |" for g in rep["gates"]]
    out += ["", "## Checks", "", "| Check | Kind | Title | Status | Evidence |", "|---|---|---|---|---|"]
    for c in contract["checks"]:
        d = rep["checks"]["detail"][c["id"]]
        ev = (f"hits {d.get('hits')}, fails {d.get('fails')}" if c["kind"] == "assertion" else ", ".join(d.get("tests", [])))
        out.append(f"| {c['id']} | {c['kind']} | {c['title']} | **{d['status']}** | {ev} |")
    out += ["", "## Requirement traceability (RTM)", "",
            "| Rule | Spec ref | Statement | Checks | Status |", "|---|---|---|---|---|"]
    for r in rep["rtm"]:
        chk = ", ".join(f"{k}:{v}" for k, v in r["check_status"].items()) or (
            f"not verified: {r['not_verified']['reason']}" if r["not_verified"] else "—")
        out.append(f"| {r['rule']} | {', '.join(r['spec_refs'])} | {r['statement'].replace('|', chr(92) + '|')} | {chk} | **{r['status']}** |")
    if mutation:
        out += ["", "## Mutants", "", "| ID | File:line | Operator | Status | Caught by |", "|---|---|---|---|---|"]
        out += [f"| {m['id']} | {m['file']}:{m['line']} | {m['operator']} | {m['status']} | "
                f"{', '.join(m['killed_by_checks'] + m['killed_by_tests'])[:120]} |" for m in mutation["mutants"]]
    out += ["", "## Not verified by this run", "",
            "- Formal proof, CDC/RDC, STA, synthesis and DFT checks are outside this flow.",
            "- Rules marked NOT_VERIFIED_BY_SIM carry the contract's reason (static, structural, not observable...).",
            "- Only the default parameter configuration was simulated unless stated above."]
    return "\n".join(out) + "\n"


def write(rep: dict, contract: dict, mutation: dict | None, work: Path) -> list[Path]:
    paths = [work / "report.json", work / "report.md", work / "rtm.json"]
    paths[0].write_text(json.dumps({k: v for k, v in rep.items() if k != "rtm"}, indent=1) + "\n", encoding="utf-8")
    paths[1].write_text(to_markdown(rep, contract, mutation), encoding="utf-8")
    paths[2].write_text(json.dumps(rep["rtm"], indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return paths

"""Failure triage (stage 5, agent A9): the only agent that sees the RTL, and it changes nothing.

Failures are clustered by code (one cluster per failing test or failing assertion check). One deep
agent per run reads, in a sandbox, the specification, the contract, the RTL, the tests, the checkers
and the failure excerpts, and writes for each cluster the analysis a designer needs to decide
(principle PR-6): what the specification says, what the RTL does, what the test does, the candidate
causes A (RTL wrong), B (test wrong), C (specification silent or contradictory), with evidence, and
the options. Nobody edits RTL or tests from here; the designer decides.
"""
from __future__ import annotations

import json
from pathlib import Path

from nnc.agents.backend import AgentTask
from nnc.agents.runtime import Usage

PROMPT_VERSION = "triage-v1"
SYSTEM_PROMPT = (
    "You are a senior design-verification engineer analysing simulation failures. You read the files in the "
    "current directory with the tools you have. You do not decide; you give the designer the evidence. "
    "Quote files with line numbers. Return the answer in the required JSON structure."
)
SCHEMA = {
    "type": "object", "required": ["analyses"], "additionalProperties": False,
    "properties": {"analyses": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["failure", "spec_says", "rtl_does", "test_does", "candidates", "most_likely", "options"],
        "properties": {
            "failure": {"type": "string"},
            "spec_says": {"type": "string"},
            "rtl_does": {"type": "string"},
            "test_does": {"type": "string"},
            "candidates": {"type": "array", "items": {
                "type": "object", "required": ["cause", "evidence_for", "evidence_against"], "additionalProperties": False,
                "properties": {"cause": {"type": "string", "enum": ["A_rtl_wrong", "B_test_wrong", "C_spec_unclear"]},
                               "evidence_for": {"type": "string"}, "evidence_against": {"type": "string"}}}},
            "most_likely": {"type": "string", "enum": ["A_rtl_wrong", "B_test_wrong", "C_spec_unclear", "undetermined"]},
            "options": {"type": "string"},
        }}}},
}


def clusters(results: dict, contract: dict) -> list[dict]:
    checks = {c["id"]: c for c in contract["checks"]}
    out = []
    for t in results.get("tests", []):
        if t["status"] == "fail":
            out.append({"kind": "test", "name": t["name"], "exception": t.get("exception"),
                        "message": t.get("message", "")[:1500], "traceback": t.get("traceback", "")[-2000:]})
    for cid, v in results.get("assertions", {}).items():
        if v["fails"] > 0:
            c = checks.get(cid, {})
            out.append({"kind": "assertion", "name": cid, "title": c.get("title"), "behavior": c.get("behavior"),
                        "fails": v["fails"], "hits": v["hits"], "first_fail_time": v.get("first_fail_time")})
    return out


def run(results: dict, contract: dict, files: dict[str, Path], backend, log_dir: Path, *,
        model: str = "opus", max_clusters: int = 12) -> dict:
    cl = clusters(results, contract)
    if not cl:
        return {"analyses": [], "clusters": 0, "usage": Usage().as_dict()}
    listing = "\n".join(f"  {name}" for name in sorted(files))
    instructions = (
        "FILES IN THIS DIRECTORY\n" + listing +
        "\n\nFAILURES TO ANALYSE (one analysis each, same order)\n" +
        json.dumps(cl[:max_clusters], indent=1) +
        "\n\nFor each failure: read the check/test, the rule quotes in contract.json and rules.json, the test code, the "
        "checker code and the RTL. Fill spec_says (quote + file:line), rtl_does (file:line + what it does in the "
        "failing cycles), test_does (stimulus, expected value and how it was derived, file:line), the three "
        "candidates with evidence for and against, most_likely, and options (what the designer can decide: fix "
        "RTL / fix test / clarify spec, with the change each needs). Do not propose weakening a check.")
    usage = Usage()
    task = AgentTask("A9_triage", instructions, SCHEMA, inputs=dict(files), tools=("Read", "Grep", "Glob"),
                     system_prompt=SYSTEM_PROMPT, model=model, max_turns=60)
    res = backend.run(task, log_dir)
    usage.add(res)
    return {"analyses": res.output["analyses"], "clusters": len(cl), "analysed": min(len(cl), max_clusters),
            "usage": usage.as_dict(), "prompt_version": PROMPT_VERSION, "denials": res.permission_denials}


def to_markdown(tri: dict) -> str:
    out = ["# Failure triage", "", f"Failures: {tri.get('clusters', 0)}; analysed: {tri.get('analysed', 0)}. "
           "The designer decides; nothing was changed.", ""]
    for i, a in enumerate(tri.get("analyses", []), 1):
        out += [f"## {i}. {a['failure']}", "", f"**Most likely:** {a['most_likely']}", "",
                "| Part | Content |", "|---|---|",
                f"| Specification says | {a['spec_says']} |", f"| RTL does | {a['rtl_does']} |",
                f"| Test does | {a['test_does']} |"]
        for c in a["candidates"]:
            out.append(f"| {c['cause']} | For: {c['evidence_for']}<br>Against: {c['evidence_against']} |")
        out += [f"| Options | {a['options']} |", ""]
    return "\n".join(x.replace("\n", " ") if x.startswith("|") else x for x in out) + "\n"

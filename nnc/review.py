"""Rule review (stage 1, agents A2 Verifier + A3 Consolidator as one worker per chunk).

Input: every raw extraction of the design (work/rules_<doc>.json). For each chunk of rules (same
document and chapter, up to a token budget) a worker:
  * checks each rule against its own quote: keep, fix (strength / actor / check) or reject;
  * groups rules that state the same requirement (one kept, the others merged into it);
  * lists open questions a designer must settle (ambiguity, contradiction).
Code then applies the verdicts. A rule without a verdict is kept and flagged 'unreviewed'; a
verdict for an unknown ID is ignored and counted. Output: work/rules.json (the Gate 1 artifact)
and work/rules.md (the review sheet).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from nnc.agents.backend import AgentTask
from nnc.agents.runtime import Usage, run_parallel
from nnc.extract import ACTORS, CHECKS, STRENGTHS

PROMPT_VERSION = "review-v1"
CHARS_PER_TOKEN = 4.0

SYSTEM_PROMPT = (
    "You are a senior verification engineer reviewing rules extracted from a hardware specification. "
    "Judge every rule only against its own quote. Be strict: a wrong rule costs more than a missing one. "
    "Return the answer in the required JSON structure."
)

SCHEMA = {
    "type": "object",
    "required": ["verdicts", "duplicates", "questions"],
    "additionalProperties": False,
    "properties": {
        "verdicts": {"type": "array", "items": {
            "type": "object", "required": ["rule", "verdict", "reason"], "additionalProperties": False,
            "properties": {
                "rule": {"type": "string"},
                "verdict": {"type": "string", "enum": ["keep", "fix", "reject"]},
                "strength": {"type": "string", "enum": STRENGTHS},
                "actor": {"type": "string", "enum": ACTORS},
                "check": {"type": "string", "enum": CHECKS},
                "reason": {"type": "string"},
            }}},
        "duplicates": {"type": "array", "items": {
            "type": "object", "required": ["keep", "merge", "reason"], "additionalProperties": False,
            "properties": {"keep": {"type": "string"}, "merge": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                           "reason": {"type": "string"}}}},
        "questions": {"type": "array", "items": {
            "type": "object", "required": ["rules", "question"], "additionalProperties": False,
            "properties": {"rules": {"type": "array", "items": {"type": "string"}}, "question": {"type": "string"}}}},
    },
}

TASK_TEXT = """TASK
For EVERY rule above give exactly one verdict:
  keep    the rule is stated by its quote and its fields are right;
  fix     the rule is right but strength, actor or check is wrong: give only the corrected field(s);
          "X can do A only when B" restricts A and is MUST_NOT, not MAY;
          check = assertion only if it is checkable every cycle from interface signals;
  reject  the quote does not state this rule, or it is only a description with nothing to verify or
          to exercise; give the reason.
DUPLICATES: rules in this list that state the same requirement (same behaviour, actor, condition and
strength). Keep the clearest one; list the others in "merge". Never merge rules that differ in channel,
signal, condition or strength.
QUESTIONS: at most 8, only real ambiguities or contradictions a designer must settle before
verification (name the rules). Do not ask about things the quotes answer.
"""


def _rule_line(r: dict) -> str:
    cond = f" WHEN {r['condition']}" if r.get("condition") else ""
    return (f"[{r['id']}] {r['strength']} actor={r['actor']} check={r['check']}: {r['statement']}{cond}\n"
            f"    QUOTE: {r['quote'][:600]}")


def make_chunks(rules: list[dict], budget_tokens: int) -> list[list[dict]]:
    chunks: list[list[dict]] = []
    cur: list[dict] = []
    size = 0
    key = None
    for r in rules:
        k = (r.get("doc"), r["section"].split(".")[0])
        n = len(_rule_line(r))
        if cur and (k != key or (size + n) / CHARS_PER_TOKEN > budget_tokens):
            chunks.append(cur)
            cur, size = [], 0
        cur.append(r)
        size += n
        key = k
    if cur:
        chunks.append(cur)
    return chunks


def _prompt(chunk: list[dict]) -> str:
    doc = chunk[0].get("doc", "")
    body = "\n".join(_rule_line(r) for r in chunk)
    return f"DOCUMENT: {doc}\n\nRULES ({len(chunk)}):\n{body}\n\n{TASK_TEXT}"


def load_raw_rules(work: Path, files: list[Path] | None = None) -> tuple[list[dict], list[str]]:
    files = files or sorted(work.glob("rules_*.json"))
    rules, sources = [], []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        rules.extend(data["rules"])
        sources.append(f.name)
    return rules, sources


def review(rules: list[dict], backend, log_dir: Path, *, model: str | None = "sonnet", budget_tokens: int = 5000,
           workers: int = 4, sources: list[str] | None = None) -> dict:
    by_id = {r["id"]: r for r in rules}
    chunks = make_chunks(rules, budget_tokens)
    items = [(i, AgentTask(name=f"A2_review_c{i:03d}", instructions=_prompt(c), schema=SCHEMA,
                           system_prompt=SYSTEM_PROMPT, model=model, max_turns=4)) for i, c in enumerate(chunks)]
    usage = Usage()
    outcomes = run_parallel(backend, items, log_dir, workers)
    errors = [f"chunk {o.key}: {o.error}" for o in outcomes if o.error]

    verdicts: dict[str, dict] = {}
    merged_into: dict[str, str] = {}
    questions: list[dict] = []
    unknown: list[str] = []
    for o in outcomes:
        usage.add(o.result)
        if o.result is None:
            continue
        allowed = {r["id"] for r in chunks[o.key]}
        for v in o.result.output["verdicts"]:
            (verdicts.__setitem__(v["rule"], v) if v["rule"] in allowed else unknown.append(v["rule"]))
        for d in o.result.output["duplicates"]:
            if d["keep"] not in allowed:
                unknown.append(d["keep"])
                continue
            for m in d["merge"]:
                if m in allowed and m != d["keep"]:
                    merged_into[m] = d["keep"]
                else:
                    unknown.append(m)
        for q in o.result.output["questions"]:
            questions.append({"rules": [r for r in q["rules"] if r in by_id], "question": q["question"]})

    # Resolve merge chains (a -> b -> c) and never merge into a rejected rule.
    def root(rid: str) -> str:
        seen = set()
        while rid in merged_into and rid not in seen:
            seen.add(rid)
            rid = merged_into[rid]
        return rid

    kept, rejected = [], []
    for r in rules:
        v = verdicts.get(r["id"])
        rec = dict(r)
        if v is None:
            rec["review"] = {"verdict": "unreviewed", "reason": "no verdict returned"}
        else:
            rec["review"] = {"verdict": v["verdict"], "reason": v["reason"]}
            if v["verdict"] == "fix":
                changes = {k: v[k] for k in ("strength", "actor", "check") if k in v and v[k] != r.get(k)}
                if changes:
                    rec["review"]["changes"] = {k: [r.get(k), val] for k, val in changes.items()}
                    rec.update(changes)
                else:  # a "fix" that changes nothing is a keep
                    rec["review"]["verdict"] = "keep"
        if v is not None and v["verdict"] == "reject":
            rejected.append(rec)
        else:
            kept.append(rec)
    kept_ids = {r["id"] for r in kept}
    final = []
    for r in kept:
        target = root(r["id"])
        if target != r["id"] and target in kept_ids:
            continue
        final.append(r)
    by_final = {r["id"]: r for r in final}
    for r in kept:
        target = root(r["id"])
        if target != r["id"] and target in by_final:
            by_final[target].setdefault("merged_from", []).append(
                {"id": r["id"], "quote": r["quote"], "sentences": r["sentences"]})

    return {
        "sources": sources or [],
        "review": {
            "prompt_version": PROMPT_VERSION, "model": model, "chunks": len(chunks),
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"), "usage": usage.as_dict(),
            "errors": errors, "unknown_ids": sorted(set(unknown)),
        },
        "counts": {
            "input": len(rules), "kept": len(final), "fixed": sum(1 for r in final if r["review"]["verdict"] == "fix"),
            "merged": len(kept) - len(final), "rejected": len(rejected),
            "unreviewed": sum(1 for r in final if r["review"]["verdict"] == "unreviewed"),
        },
        "rules": final,
        "rejected": rejected,
        "questions": questions,
    }


RESOLVE_SCHEMA = {
    "type": "object", "required": ["questions"], "additionalProperties": False,
    "properties": {"questions": {"type": "array", "items": {
        "type": "object", "required": ["index", "status", "answer", "sentences"], "additionalProperties": False,
        "properties": {
            "index": {"type": "integer"},
            "status": {"type": "string", "enum": ["answered", "open", "duplicate"]},
            "duplicate_of": {"type": "integer"},
            "answer": {"type": "string"},
            "sentences": {"type": "array", "items": {"type": "string"}},
        }}}},
}
RESOLVE_TEXT = """TASK
The QUESTIONS were raised by reviewers who each saw only part of the documents. For each question:
  answered  the DOCUMENTS answer it: give the short answer and cite the sentence IDs that state it;
  duplicate the same question as an earlier one (give duplicate_of = its index);
  open      the documents do not settle it: the designer must decide (answer = what is missing).
Be strict: "answered" only when cited sentences really state the answer; never answer from general
knowledge.
"""


def resolve_questions(result: dict, indexes: list[dict], backend, log_dir: Path, *, model: str | None = "sonnet") -> dict:
    """A3 consolidator pass over all open questions with the full documents in view."""
    qs = result["questions"]
    if not qs:
        return result
    known: dict[str, str] = {}
    docs = []
    for idx in indexes:
        lines = [f"DOCUMENT {idx['doc']['file']}"]
        for s in idx["sections"]:
            if s["level"] == 0 or not s["sentences"]:
                continue
            lines.append(f"## {s['id']} {s['title']}")
            for st in s["sentences"]:
                key = f"{idx['doc']['file']}#{st['id']}"
                known[st["id"]] = key
                lines.append(f"[{st['id']}] {st['text']}")
        docs.append("\n".join(lines))
    qtext = "\n".join(f"Q{i}: {q['question']} (rules {', '.join(q['rules'])})" for i, q in enumerate(qs))
    prompt = "DOCUMENTS\n" + "\n\n".join(docs) + f"\n\nQUESTIONS\n{qtext}\n\n{RESOLVE_TEXT}"
    res = backend.run(AgentTask("A3_resolve_questions", prompt, RESOLVE_SCHEMA, system_prompt=SYSTEM_PROMPT,
                                model=model, max_turns=4), log_dir)
    u = result["review"]["usage"]
    u["calls"] += 1
    u["cached"] += res.backend == "cache"
    u["cost_usd"] = round(u["cost_usd"] + (res.cost_usd or 0.0), 4)
    by_index = {a["index"]: a for a in res.output["questions"]}
    open_q, answered, dupes = [], [], 0
    for i, q in enumerate(qs):
        a = by_index.get(i)
        if a is None:
            open_q.append({**q, "note": "not resolved"})
            continue
        cited = [s for s in a["sentences"] if s in known]
        if a["status"] == "duplicate" and a.get("duplicate_of") is not None and a["duplicate_of"] != i:
            dupes += 1
        elif a["status"] == "answered" and cited:
            answered.append({**q, "answer": a["answer"], "sentences": cited})
        else:  # an answer without a valid citation is not an answer
            open_q.append({**q, "note": a["answer"]})
    result["questions"] = open_q
    result["answered_questions"] = answered
    result["counts"]["questions_raised"] = len(qs)
    result["counts"]["questions_answered"] = len(answered)
    result["counts"]["questions_duplicate"] = dupes
    return result


def record_answer(result: dict, number: int, answer: str, by: str) -> dict:
    """Record the designer's decision on open question `number` (1-based, as in rules.md). Decisions
    are part of the Gate 1 artifact and are given to the contract agent as golden input."""
    qs = result["questions"]
    if not 1 <= number <= len(qs):
        raise ValueError(f"there are {len(qs)} open questions; got {number}")
    if not answer.strip() or not by.strip():
        raise ValueError("an answer needs text and the name of who decided (--by)")
    qs[number - 1]["decision"] = {"answer": answer.strip(), "by": by.strip(),
                                  "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    return result


def decisions(result: dict) -> list[dict]:
    return [q for q in result.get("questions", []) if q.get("decision")]


def summarize(result: dict) -> str:
    c, u = result["counts"], result["review"]["usage"]
    qa = (f" (raised {c['questions_raised']}, answered from the documents {c['questions_answered']}, "
          f"duplicates {c['questions_duplicate']})" if "questions_raised" in c else "")
    line = (f"rules in {c['input']}: kept {c['kept']} (fixed {c['fixed']}), merged {c['merged']}, rejected "
            f"{c['rejected']}, unreviewed {c['unreviewed']}; open questions {len(result['questions'])}{qa}\n"
            f"calls: {u['calls']} ({u['cached']} from cache)  cost US${u['cost_usd']}")
    if result["review"]["errors"]:
        line += "\nERRORS: " + " | ".join(result["review"]["errors"])
    return line


def to_markdown(result: dict) -> str:
    out = ["# Rules for review (Gate 1)", "", "```", summarize(result), "```", "",
           "Approve with `nnc gate approve <design> G1_rules --by <name>` after reading this sheet.", ""]
    if result["questions"]:
        out += ["## Open questions (the designer decides: `nnc answer <design> <n> \"<decision>\" --by <name>`)", ""]
        for i, q in enumerate(result["questions"], 1):
            out.append(f"{i}. {q['question']} ({', '.join(q['rules'])})" + (f" — *{q['note']}*" if q.get("note") else ""))
            if q.get("decision"):
                d = q["decision"]
                out.append(f"   - **Decision** ({d['by']}, {d['at']}): {d['answer']}")
            else:
                out.append("   - **Decision:** none yet")
        out.append("")
    if result.get("answered_questions"):
        out += ["## Questions answered by the documents", ""]
        out += [f"- {q['question']} → {q['answer']} [{', '.join(q['sentences'])}]" for q in result["answered_questions"]]
        out.append("")
    doc = None
    for r in result["rules"]:
        if r.get("doc") != doc:
            doc = r.get("doc")
            out += ["", f"## {doc}", "", "| ID | Spec ref | Str. | Actor | Check | Statement | Review |",
                    "|---|---|---|---|---|---|---|"]
        stmt = r["statement"].replace("|", "\\|")
        cond = f" *(when: {r['condition']})*" if r.get("condition") else ""
        rv = r["review"]["verdict"]
        if rv == "fix":
            rv += ": " + ", ".join(f"{k} {a}->{b}" for k, (a, b) in r["review"].get("changes", {}).items())
        if r.get("merged_from"):
            rv += f"; merged {', '.join(m['id'] for m in r['merged_from'])}"
        out.append(f"| {r['id']} | {', '.join(r.get('spec_refs', []))} | {r['strength']} | {r['actor']} | "
                   f"{r['check']} | {stmt}{cond} | {rv} |")
    if result["rejected"]:
        out += ["", "## Rejected", "", "| ID | Statement | Reason |", "|---|---|---|"]
        out += [f"| {r['id']} | {r['statement'].replace('|', chr(92) + '|')} | {r['review']['reason']} |"
                for r in result["rejected"]]
    return "\n".join(out) + "\n"


def write_outputs(result: dict, work: Path) -> tuple[Path, Path]:
    jp, mp = work / "rules.json", work / "rules.md"
    jp.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    mp.write_text(to_markdown(result), encoding="utf-8")
    return jp, mp

"""Rule extraction (stage 1, agent A1 + gap-filler): spec index -> rules.json.

Design (docs/ARCHITECTURE.md, section 4):
* Map, not retrieval: every section ("child") is processed exactly once, so no rule is lost to a
  top-k cut. Consecutive sections of one chapter are packed into batches up to a token budget.
* Parent context: each batch carries the breadcrumb of its sections and the opening sentences of a
  parent whose own text is not in the batch, marked as context that must not be cited.
* Citations by sentence ID: the agent returns IDs, the quote is rebuilt by code from the index, so a
  quote can never be invented and output tokens stay small.
* Coverage ledger: every sentence with a normative keyword (*) must be cited by a rule or skipped
  with a reason. Sentences left over are sent once more to a gap-filler; whatever is still left is
  reported as uncovered, never dropped silently.
* Cache: answers are stored by task fingerprint (content + prompt + model), so a re-run, or a
  revised specification, only pays for batches whose content changed.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from nnc.agents.backend import AgentTask
from nnc.agents.runtime import CachedBackend, Usage, run_parallel  # noqa: F401  (CachedBackend re-exported)

PROMPT_VERSION = "extract-v2"
CHARS_PER_TOKEN = 4.0  # rough estimate for English technical prose

SYSTEM_PROMPT = (
    "You are a hardware verification engineer. You turn specification text into atomic, verifiable "
    "rules. Work only from the sentences you are given. Cite sentence IDs exactly as written; never "
    "invent an ID, a signal or a requirement. Return the answer in the required JSON structure."
)

STRENGTHS = ["MUST", "MUST_NOT", "SHOULD", "SHOULD_NOT", "MAY"]
ACTORS = ["master", "slave", "interconnect", "source", "destination", "any", "system"]
CHECKS = ["assertion", "scenario", "both", "none"]
SKIP_REASONS = ["descriptive", "example_or_figure", "cross_reference", "informative_note",
                "list_lead_in", "duplicate"]
_ID = r"^[0-9A-Za-z._]+:s[0-9]+$"
SPEC_REF_RE = re.compile(r"\bREQ-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")

SCHEMA = {
    "type": "object",
    "required": ["rules", "skipped"],
    "additionalProperties": False,
    "properties": {
        "rules": {"type": "array", "items": {
            "type": "object",
            "required": ["sentences", "strength", "actor", "signals", "condition", "statement", "check"],
            "additionalProperties": False,
            "properties": {
                "sentences": {"type": "array", "minItems": 1, "items": {"type": "string", "pattern": _ID}},
                "strength": {"type": "string", "enum": STRENGTHS},
                "actor": {"type": "string", "enum": ACTORS},
                "signals": {"type": "array", "items": {"type": "string"}},
                "condition": {"type": "string"},
                "statement": {"type": "string", "minLength": 1},
                "check": {"type": "string", "enum": CHECKS},
            },
        }},
        "skipped": {"type": "array", "items": {
            "type": "object",
            "required": ["sentence", "reason"],
            "additionalProperties": False,
            "properties": {
                "sentence": {"type": "string", "pattern": _ID},
                "reason": {"type": "string", "enum": SKIP_REASONS},
            },
        }},
    },
}

TASK_TEXT = """TASK
1. Write one rule for each atomic requirement, prohibition, permission or recommendation stated in SENTENCES.
   Split a sentence that states several independent requirements into several rules. One rule may cite
   several sentences when they only make sense together (for example a list lead-in and its item).
2. Every sentence marked * MUST be cited by a rule or listed in "skipped" with a reason. Unmarked sentences
   may be cited too when they state a rule.
   - Present-tense descriptions of required behaviour are rules, also inside figure explanations
     (for example "the information remains stable until READY is HIGH").
   - Permissions are rules (MAY): they define legal behaviour a test must exercise
     (for example "write data can appear before the write address").
3. Fields:
   strength  MUST / MUST_NOT / SHOULD / SHOULD_NOT / MAY.
             "can"/"is permitted"/"is possible" = MAY; "recommended" = SHOULD.
             "X can do A only when B" or "A occurs only when B" RESTRICTS A: it is MUST_NOT (A without B),
             never MAY. "X can be A, but only if B" is MUST_NOT (A unless B).
   actor     who the rule binds: master, slave, interconnect, source, destination, any, system.
   signals   exact signal names involved (as written in the text, without bit ranges); [] if none.
   condition when the rule applies, "" if always.
   statement the rule in one sentence of at most 35 words, using exact signal names.
   check     assertion = checkable every cycle on interface signals; scenario = needs a directed test;
             both; none = not verifiable at the interface (design advice, system-level).
4. Use only what SENTENCES state. CONTEXT is for understanding and must not be cited.
"""


# ----------------------------------------------------------------------------------- data shapes
@dataclass
class Batch:
    index: int
    chapter: str
    section_ids: list[str]
    sentence_ids: list[str]
    normative_ids: list[str]
    prompt: str

    @property
    def est_tokens(self) -> int:
        return int(len(self.prompt) / CHARS_PER_TOKEN)


def _chapter(sid: str) -> str:
    return sid.split(".")[0]


def _breadcrumb(sec: dict, by_id: dict) -> str:
    parts = []
    p = sec.get("parent")
    while p:
        parts.append(f"{p} {by_id[p]['title']}")
        p = by_id[p].get("parent")
    return " > ".join(reversed(parts))


def _matches(sec: dict, by_id: dict, selectors: list[str]) -> bool:
    """A selector is a section ID prefix ('3', '13.8') or a case-insensitive part of the title of the
    section or of one of its ancestors ('Theory of Operations')."""
    for sel in selectors:
        if sec["id"] == sel or sec["id"].startswith(sel + "."):
            return True
        s = sec
        while s is not None:
            if sel.lower() in s["title"].lower():
                return True
            s = by_id.get(s["parent"]) if s.get("parent") else None
    return False


def select_sections(index: dict, prefixes: list[str] | None, skip: list[str] | None = None) -> list[dict]:
    """Sections with sentences, front matter excluded, limited by selectors and minus skipped ones."""
    by_id = {s["id"]: s for s in index["sections"]}
    out = []
    for s in index["sections"]:
        if s["level"] == 0 or not s["sentences"]:
            continue
        if prefixes and not _matches(s, by_id, prefixes):
            continue
        if skip and _matches(s, by_id, skip):
            continue
        out.append(s)
    return out


def _section_block(sec: dict, by_id: dict, only: set[str] | None = None) -> str:
    crumb = _breadcrumb(sec, by_id)
    head = f"## {sec['id']} {sec['title']}" + (f"   [in: {crumb}]" if crumb else "")
    lines = [head]
    for st in sec["sentences"]:
        mark = "*" if st["normative"] and (only is None or st["id"] in only) else ""
        lines.append(f"[{st['id']}]{mark} {st['text']}")
    return "\n".join(lines)


def _context_block(secs: list[dict], by_id: dict, n_sentences: int = 3) -> str:
    """Opening sentences of parents whose own text is not part of the batch."""
    in_batch = {s["id"] for s in secs}
    seen, lines = set(), []
    for s in secs:
        p = s.get("parent")
        if p and p not in in_batch and p not in seen and by_id[p]["sentences"]:
            seen.add(p)
            text = " ".join(st["text"] for st in by_id[p]["sentences"][:n_sentences])
            lines.append(f"- {p} {by_id[p]['title']}: {text}")
    return "\n".join(lines) if lines else "- (none)"


def build_prompt(doc: str, secs: list[dict], by_id: dict, only: set[str] | None = None) -> str:
    body = "\n\n".join(_section_block(s, by_id, only) for s in secs)
    note = ""
    if only is not None:
        note = ("\nONLY the sentences marked * still need a decision: cite each one in a rule or skip it. "
                "Do not repeat rules for unmarked sentences.\n")
    return (f"DOCUMENT: {doc}\n\nCONTEXT (do not cite):\n{_context_block(secs, by_id)}\n\n"
            f"SENTENCES (* = contains a normative keyword):\n{body}\n\n{TASK_TEXT}{note}")


def make_batches(index: dict, prefixes: list[str] | None, budget_tokens: int,
                 skip: list[str] | None = None) -> list[Batch]:
    by_id = {s["id"]: s for s in index["sections"]}
    secs = select_sections(index, prefixes, skip)
    groups: list[list[dict]] = []
    cur: list[dict] = []
    cur_chars = 0
    for s in secs:
        size = sum(len(st["text"]) + 12 for st in s["sentences"])
        if cur and (_chapter(s["id"]) != _chapter(cur[0]["id"]) or (cur_chars + size) / CHARS_PER_TOKEN > budget_tokens):
            groups.append(cur)
            cur, cur_chars = [], 0
        cur.append(s)
        cur_chars += size
    if cur:
        groups.append(cur)
    batches = []
    for i, g in enumerate(groups):
        sids = [st["id"] for s in g for st in s["sentences"]]
        norm = [st["id"] for s in g for st in s["sentences"] if st["normative"]]
        batches.append(Batch(i, _chapter(g[0]["id"]), [s["id"] for s in g], sids, norm,
                             build_prompt(index["doc"]["file"], g, by_id)))
    return batches


# --------------------------------------------------------------------------------------- running
def _task(name: str, prompt: str, model: str | None) -> AgentTask:
    return AgentTask(name=name, instructions=prompt, schema=SCHEMA, system_prompt=SYSTEM_PROMPT,
                     model=model, max_turns=4)


def _merge(outcomes, sentence_of: dict, rules: list, skipped: dict, invalid: list, usage: Usage) -> None:
    for oc in outcomes:
        if oc.result is None:
            continue
        usage.add(oc.result)
        allowed = set(oc.key.sentence_ids)
        for r in oc.result.output.get("rules", []):
            good = [s for s in r["sentences"] if s in allowed]
            invalid.extend(s for s in r["sentences"] if s not in allowed)
            if good:
                rules.append({**r, "sentences": sorted(set(good), key=lambda s: sentence_of[s]["order"])})
        for sk in oc.result.output.get("skipped", []):
            if sk["sentence"] in allowed:
                skipped[sk["sentence"]] = sk["reason"]
            else:
                invalid.append(sk["sentence"])


def extract(index: dict, backend, log_dir: Path, *, prefixes: list[str] | None = None, model: str | None = "sonnet",
            budget_tokens: int = 3500, workers: int = 4, gap_fill: bool = True, tag: str = "R",
            skip: list[str] | None = None) -> dict:
    by_id = {s["id"]: s for s in index["sections"]}
    order = 0
    sentence_of: dict[str, dict] = {}
    for s in index["sections"]:
        for st in s["sentences"]:
            sentence_of[st["id"]] = {**st, "section": s["id"], "order": order}
            order += 1

    batches = make_batches(index, prefixes, budget_tokens, skip)
    usage = Usage()
    rules: list[dict] = []
    skipped: dict[str, str] = {}
    invalid: list[str] = []
    errors: list[str] = []

    outcomes = run_parallel(backend, [(b, _task(f"A1_extract_{tag}_b{b.index:03d}", b.prompt, model))
                                      for b in batches], log_dir, workers)
    errors += [f"batch {o.key.index} ({','.join(o.key.section_ids)}): {o.error}" for o in outcomes if o.error]
    _merge(outcomes, sentence_of, rules, skipped, invalid, usage)

    def uncovered() -> list[str]:
        cited = {s for r in rules for s in r["sentences"]}
        return [s for b in batches for s in b.normative_ids if s not in cited and s not in skipped]

    gaps_before = uncovered()
    if gap_fill and gaps_before:
        gap_set = set(gaps_before)
        gap_tasks = []
        for b in batches:
            need = gap_set & set(b.normative_ids)
            if not need:
                continue
            secs = [by_id[sid] for sid in b.section_ids if any(st["id"] in need for st in by_id[sid]["sentences"])]
            prompt = build_prompt(index["doc"]["file"], secs, by_id, only=need)
            gb = Batch(b.index, b.chapter, [s["id"] for s in secs],
                       [st["id"] for s in secs for st in s["sentences"]], sorted(need), prompt)
            gap_tasks.append((gb, _task(f"A1_gapfill_{tag}_b{b.index:03d}", prompt, model)))
        gap_outcomes = run_parallel(backend, gap_tasks, log_dir, workers)
        errors += [f"gap batch {o.key.index}: {o.error}" for o in gap_outcomes if o.error]
        _merge(gap_outcomes, sentence_of, rules, skipped, invalid, usage)

    # Final rule records: ID, quote rebuilt from the index, location.
    rules.sort(key=lambda r: sentence_of[r["sentences"][0]]["order"])
    per_section: dict[str, int] = {}
    out_rules = []
    for r in rules:
        first = sentence_of[r["sentences"][0]]
        sec = first["section"]
        per_section[sec] = per_section.get(sec, 0) + 1
        quote = " ".join(sentence_of[s]["text"] for s in r["sentences"])
        out_rules.append({
            "id": f"{tag}-{sec}-{per_section[sec]:02d}",
            "doc": index["doc"]["file"],
            "section": sec,
            "section_title": by_id[sec]["title"],
            "page": first["page"],
            "quote": quote,
            "spec_refs": sorted(set(SPEC_REF_RE.findall(quote))),
            **r,
        })
    still = uncovered()
    normative_total = sum(len(b.normative_ids) for b in batches)
    cited_norm = {s for r in out_rules for s in r["sentences"]} & {s for b in batches for s in b.normative_ids}
    return {
        "source": {"file": index["doc"]["file"], "sha256": index["doc"]["sha256"], "index_version": index["version"]},
        "extraction": {
            "prompt_version": PROMPT_VERSION, "model": model, "budget_tokens": budget_tokens, "tag": tag,
            "sections": prefixes or "all", "skip": skip or [], "batches": len(batches),
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"), "usage": usage.as_dict(),
            "errors": errors,
        },
        "coverage": {
            "sentences": sum(len(b.sentence_ids) for b in batches),
            "normative_sentences": normative_total,
            "normative_cited": len(cited_norm),
            "normative_skipped": sum(1 for s in skipped if s in {x for b in batches for x in b.normative_ids}),
            "uncovered_after_first_pass": len(gaps_before),
            "uncovered": still,
            "invalid_ids": sorted(set(invalid)),
        },
        "rules": out_rules,
        "skipped": [{"sentence": s, "reason": r, "text": sentence_of[s]["text"]} for s, r in
                    sorted(skipped.items(), key=lambda kv: sentence_of[kv[0]]["order"])],
    }


def summarize(result: dict) -> str:
    c, u = result["coverage"], result["extraction"]["usage"]
    by_strength: dict[str, int] = {}
    by_check: dict[str, int] = {}
    for r in result["rules"]:
        by_strength[r["strength"]] = by_strength.get(r["strength"], 0) + 1
        by_check[r["check"]] = by_check.get(r["check"], 0) + 1
    lines = [
        f"rules: {len(result['rules'])}  by strength {by_strength}  by check {by_check}",
        f"normative sentences: {c['normative_sentences']}  cited {c['normative_cited']}  skipped "
        f"{c['normative_skipped']}  uncovered {len(c['uncovered'])} (after first pass: {c['uncovered_after_first_pass']})",
        f"invalid sentence IDs returned by the agent: {len(c['invalid_ids'])}",
        f"calls: {u['calls']} ({u['cached']} from cache)  cost US${u['cost_usd']}  tokens in "
        f"{u['input_tokens'] + u['cache_creation_input_tokens'] + u['cache_read_input_tokens']} out {u['output_tokens']}",
    ]
    if result["extraction"]["errors"]:
        lines.append("ERRORS: " + " | ".join(result["extraction"]["errors"]))
    return "\n".join(lines)


def to_markdown(result: dict) -> str:
    """Human review sheet for Gate 1."""
    out = [f"# Extracted rules - {result['source']['file']}", "",
           "```", summarize(result), "```", ""]
    current = None
    for r in result["rules"]:
        if r["section"] != current:
            current = r["section"]
            out += ["", f"## {r['section']} {r['section_title']}", "",
                    "| ID | Str. | Actor | Check | Statement | Source (p.) |", "|---|---|---|---|---|---|"]
        stmt = r["statement"].replace("|", "\\|")
        cond = f" *(when: {r['condition']})*" if r["condition"] else ""
        out.append(f"| {r['id']} | {r['strength']} | {r['actor']} | {r['check']} | {stmt}{cond} | "
                   f"{', '.join(r['sentences'])} (p{r['page']}) |")
    if result["coverage"]["uncovered"]:
        out += ["", "## Uncovered normative sentences", ""] + [f"- {s}" for s in result["coverage"]["uncovered"]]
    return "\n".join(out) + "\n"


def write_outputs(result: dict, work: Path, stem: str) -> tuple[Path, Path]:
    work.mkdir(parents=True, exist_ok=True)
    jp, mp = work / f"rules_{stem}.json", work / f"rules_{stem}.md"
    jp.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    mp.write_text(to_markdown(result), encoding="utf-8")
    return jp, mp


def stem_of(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", Path(name).stem)[:60]

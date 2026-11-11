"""Bug benchmark: how good is the approved verification at catching, and the triage at explaining,
known RTL faults? (`nnc bench`, measurement for a study of the flow.)

A design lists hand-written, realistic faults in `designs/<ip>/bugs/bugs.json`:

    {"bugs": [{"id": "SF1", "title": "full one entry early", "file": "m_vlsit_sfifo_wr.sv",
               "find": "reg_full     <= (w_occ_nxt >= PARA_SFIFO_DEPTH);",
               "replace": "reg_full     <= (w_occ_nxt >= PARA_SFIFO_DEPTH - 1);",
               "spec": "REQ-FUNC-008", "expect": "A_rtl_wrong"}]}

`find` must match exactly one line of the file. For each bug the benchmark writes the unified diff
`bugs/<id>.diff` (so `nnc inject` reproduces it alone), runs the gated tests and checkers on a patched
copy of the RTL (the run set when there is one), and records:
  caught    a test or check FAILS that PASSES on the unmodified RTL (failures already present in the
            baseline do not count, so a design with open failures cannot catch every bug for free),
  triage    optional: the triage agent's most likely cause for each new failure; the verdict is the
            most frequent one and is correct when it equals `expect` (A_rtl_wrong for a real fault),
  cost      the agent cost of that triage.
The faults are never shown to a generator agent: the verification sources are the approved ones.
"""
from __future__ import annotations

import difflib
import json
from collections import Counter
from pathlib import Path

MANIFEST = "bugs.json"


class BenchError(ValueError):
    pass


def load(design_root: Path) -> list[dict]:
    p = design_root / "bugs" / MANIFEST
    if not p.is_file():
        raise BenchError(f"no bug list: create {p}")
    bugs = json.loads(p.read_text(encoding="utf-8")).get("bugs") or []
    seen = set()
    for b in bugs:
        for k in ("id", "title", "file", "find", "replace"):
            if not b.get(k):
                raise BenchError(f"bug {b.get('id', '?')}: field {k!r} is required")
        if b["id"] in seen:
            raise BenchError(f"bug id {b['id']} is used twice")
        seen.add(b["id"])
    return bugs


def make_patch(rtl_dir: Path, bug: dict) -> str:
    """Unified diff of the one-line replacement `find` -> `replace` in rtl/<file>."""
    f = rtl_dir / bug["file"]
    if not f.is_file():
        raise BenchError(f"bug {bug['id']}: {f} does not exist")
    lines = f.read_text(encoding="utf-8").splitlines(keepends=True)
    hits = [i for i, ln in enumerate(lines) if bug["find"] in ln]
    if len(hits) != 1:
        raise BenchError(f"bug {bug['id']}: 'find' matches {len(hits)} lines of {bug['file']} (needs exactly 1)")
    new = list(lines)
    new[hits[0]] = lines[hits[0]].replace(bug["find"], bug["replace"])
    if new == lines:
        raise BenchError(f"bug {bug['id']}: the replacement changes nothing")
    return "".join(difflib.unified_diff(lines, new, f"rtl/{bug['file']}", f"rtl/{bug['file']}"))


def verdict(most_likely: list[str]) -> str | None:
    """The most frequent triage cause (ties: A before B before C)."""
    if not most_likely:
        return None
    c = Counter(most_likely)
    return sorted(c, key=lambda k: (-c[k], k))[0]


def summarize(rows: list[dict]) -> dict:
    caught = [r for r in rows if r["caught"]]
    tri = [r for r in rows if r.get("triage_verdict")]
    return {"bugs": len(rows), "caught": len(caught),
            "detection_rate": round(100.0 * len(caught) / len(rows), 1) if rows else None,
            "triaged": len(tri), "triage_correct": sum(r["triage_correct"] for r in tri),
            "triage_accuracy": round(100.0 * sum(r["triage_correct"] for r in tri) / len(tri), 1) if tri else None,
            "triage_cost_usd": round(sum(r.get("triage_cost_usd") or 0 for r in tri), 4)}


def to_markdown(name: str, rows: list[dict], summ: dict) -> str:
    out = [f"# Bug benchmark — {name}", "",
           "Each row is a hand-written RTL fault run against the approved tests and checkers. *Caught* means a "
           "test or check fails that passes on the unmodified RTL. The triage verdict is the most frequent "
           "cause given by the triage agent for the new failures (A = RTL wrong).", "",
           f"**Detection:** {summ['caught']}/{summ['bugs']} ({summ['detection_rate']} %)"
           + (f" · **triage correct:** {summ['triage_correct']}/{summ['triaged']} ({summ['triage_accuracy']} %), "
              f"US${summ['triage_cost_usd']}" if summ["triaged"] else " · triage not run"), "",
           "| Bug | Fault | Spec | Caught | New failures | Triage verdict |", "|---|---|---|---|---|---|"]
    for r in rows:
        fails = ", ".join(r["new_failing"][:6]) + (" …" if len(r["new_failing"]) > 6 else "")
        tv = (f"{r['triage_verdict']} ({'correct' if r['triage_correct'] else 'expected ' + r['expect']})"
              if r.get("triage_verdict") else "—")
        out.append(f"| {r['id']} | {r['title']} (`{r['file']}`) | {r.get('spec') or '—'} | "
                   f"{'**yes**' if r['caught'] else 'no'} | {fails or '—'} | {tv} |")
    return "\n".join(out) + "\n"


def run(d, o, *, triage_ids: set[str] | None = None, only: set[str] | None = None) -> dict:
    """Run every bug of the design (or `only`); triage the new failures of the bugs in `triage_ids`."""
    from nnc import flow
    bugs = [b for b in load(d.root) if not only or b["id"] in only]
    out_root = d.work / "bench"
    rows = []
    for b in bugs:
        patch = d.root / "bugs" / f"{b['id']}.diff"
        patch.write_text(make_patch(d.root / "rtl", b), encoding="utf-8", newline="\n")
        o.say(f"[bench] {b['id']}: {b['title']}")
        res = flow.run_inject(d, o, patch, out_root / b["id"], do_triage=bool(triage_ids) and b["id"] in triage_ids)
        tri = res.get("triage") or {}
        ml = tri.get("most_likely") or []
        v = verdict(ml)
        rows.append({"id": b["id"], "title": b["title"], "file": b["file"], "spec": b.get("spec"),
                     "expect": b.get("expect", "A_rtl_wrong"), "caught": res["caught"],
                     "new_failing": res.get("new_failing", []), "status": res.get("status"),
                     "triage_most_likely": ml, "triage_verdict": v,
                     "triage_correct": v == b.get("expect", "A_rtl_wrong") if v else None,
                     "triage_cost_usd": tri.get("cost_usd")})
    summ = summarize(rows)
    data = {"design": d.name, "summary": summ, "bugs": rows}
    (d.work / "bench.json").write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    (d.work / "bench.md").write_text(to_markdown(d.name, rows, summ), encoding="utf-8")
    o.say(f"[bench] {d.name}: caught {summ['caught']}/{summ['bugs']}"
          + (f", triage correct {summ['triage_correct']}/{summ['triaged']}" if summ["triaged"] else "")
          + " -> work/bench.md")
    return data

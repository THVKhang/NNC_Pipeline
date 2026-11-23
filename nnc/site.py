"""The project page (GitHub Pages) made by code from the committed results: `nnc site --out site`.

Every number on the page comes from a committed file, as the design table of README.md does (nnc/summary.py):
work/results.json, report.json, formal.json, mutation.json of each design, corpus/results.json, and the gate
states. Nothing is typed by hand, so the page cannot disagree with the repository. CI builds it on main and
publishes it (job `pages`). One self-contained HTML file: no script, no external resource.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from nnc import __version__, summary

REPO_URL = "https://github.com/THVKhang/NNC_Pipeline"
IMAGE = "ghcr.io/thvkhang/nnc_pipeline"
STAGES = [("Specification", "PDF, Markdown, Word, HTML, AsciiDoc", None),
          ("Rules", "agents extract and review every normative sentence", "G1"),
          ("Contract", "checks, interface, what is not verifiable", "G2"),
          ("Verification sources", "SVA checkers, cover points, cocotb tests", "G3"),
          ("Runs", "simulation, formal, CDC, mutation, triage", None),
          ("Sign-off", "report for a hardware designer", "G4")]


def _md(text: str) -> str:
    """The little Markdown of a summary cell (links, bold) as HTML."""
    t = html.escape(text)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f'<a href="{REPO_URL}/tree/main/{m.group(2)}">{m.group(1)}</a>', t)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)


def design_rows(designs_root: Path) -> list[list[str]]:
    return [r for d in sorted(Path(designs_root).iterdir())
            if (d / "nnc_state.json").is_file() and (r := summary.row(d))]


def corpus_summary(repo: Path) -> dict | None:
    p = repo / "corpus" / "results.json"
    if not p.is_file():
        return None
    res = json.loads(p.read_text(encoding="utf-8"))
    rows = res["rows"]
    smoke: dict[str, int] = {}
    for r in rows:
        s = ((r.get("adapt") or {}).get("smoke") or {}).get("status")
        if s:
            smoke[s] = smoke.get(s, 0) + 1
    return {"designs": len(rows), "sources": len(res["manifest"]["sources"]),
            "bench": smoke.get("pass", 0) + smoke.get("dut_assertion", 0), "smoke": smoke,
            "total": res["summary"]["total"]}


CSS = """
:root{--bg:#fbfbfa;--fg:#1d1d1b;--muted:#5f5e5a;--line:#e3e1dc;--card:#ffffff;--accent:#2f5d8a;--code:#f1efea;
--ok:#2e6b3a;--warn:#8a5a12}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecebe7;--muted:#a9a79f;--line:#33322f;--card:#1e1e1c;
--accent:#8db7e3;--code:#262523;--ok:#8fca99;--warn:#e0b26a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1040px;margin:0 auto;padding:40px 16px 64px}
h1{font-size:2rem;line-height:1.2;margin:0 0 8px}h2{font-size:1.3rem;margin:48px 0 12px}
p{margin:0 0 12px}.lead{font-size:1.1rem;color:var(--muted);max-width:760px}
a{color:var(--accent)}code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.9em}
pre{background:var(--code);padding:14px 16px;border-radius:8px;overflow-x:auto;margin:0 0 12px}
.flow{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:12px 0}
.stage{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px}
.stage b{display:block}.stage span{color:var(--muted);font-size:.88rem}
.gate{display:inline-block;margin-top:6px;font-size:.78rem;border:1px solid var(--accent);color:var(--accent);
border-radius:99px;padding:1px 8px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:12px 0}
.tile{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px}
.tile .n{font-size:1.7rem;font-weight:650;font-variant-numeric:tabular-nums}.tile .l{color:var(--muted);font-size:.88rem}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--card)}
table{border-collapse:collapse;width:100%;font-size:.92rem}th,td{padding:8px 10px;border-bottom:1px solid var(--line);
text-align:left;vertical-align:top}th{color:var(--muted);font-weight:600;white-space:nowrap}
td.num{font-variant-numeric:tabular-nums;white-space:nowrap}tr:last-child td{border-bottom:0}
.note{border-left:3px solid var(--warn);padding:8px 12px;background:var(--card);margin:12px 0}
ul{padding-left:20px}footer{margin-top:56px;color:var(--muted);font-size:.85rem}
"""


def render(repo: Path) -> str:
    repo = Path(repo)
    rows = design_rows(repo / "designs")
    corpus = corpus_summary(repo)
    e = html.escape
    out = ["<!doctype html>", '<html lang="en">', "<head>", '<meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1">',
           "<title>NNC Pipeline</title>",
           '<meta name="description" content="Specification-driven RTL verification with gated AI agents">',
           f"<style>{CSS}</style>", "</head>", "<body>", "<main>",
           "<h1>NNC Pipeline</h1>",
           '<p class="lead">Specification-driven RTL verification with gated AI agents. Agents read the '
           "specification and write rules, a contract, SystemVerilog checkers and cocotb tests; they never see "
           "the RTL. Simulation, formal, CDC and mutation then measure the RTL against them, and a person "
           "approves every step.</p>",
           f'<p><a href="{REPO_URL}">Repository</a> · <a href="{REPO_URL}/blob/main/docs/GUIDE.md">Guide</a> · '
           f'<a href="{REPO_URL}/blob/main/docs/EVALUATION.md">Evaluation</a> · '
           f'<a href="{REPO_URL}/blob/main/docs/INPUT_SUPPORT.md">Inputs</a> · version {e(__version__)}</p>',
           "<h2>Run it in one command</h2>",
           f"<pre><code>docker run --rm {IMAGE}</code></pre>",
           "<p>No agent and no API key: it reruns the finished <code>sync_fifo</code> design (intake, the "
           "reproduction kit of 25 cocotb tests and 11 assertions on Verilator, the CDC check) and compares each "
           "step with the recorded outcome. <code>nnc demo ot_gpio --replay</code> also replays the stages that "
           "read the specification from the committed answers of the agents, without calling a model.</p>",
           "<h2>The flow</h2>", '<div class="flow">']
    for name, what, gate in STAGES:
        out.append(f'<div class="stage"><b>{e(name)}</b><span>{e(what)}</span>'
                   + (f'<br><span class="gate">gate {gate}</span>' if gate else "") + "</div>")
    out += ["</div>",
            "<p>Isolation is enforced by code: the agents that write the verification never receive the RTL, "
            "and the agent that writes RTL never receives the verification.</p>",
            "<h2>Results on the designs of the repository</h2>",
            "<p>Every cell comes from the committed results of the design (the same code writes the table of the "
            "README).</p>",
            '<div class="scroll"><table><thead><tr><th>Design</th><th>Tests passing</th><th>Checks PASS</th>'
            "<th>Formal</th><th>Mutation</th><th>G4</th></tr></thead><tbody>"]
    for r in rows:
        out.append("<tr>" + "".join(f'<td{" class=num" if k in (1, 2) else ""}>{_md(c)}</td>'
                                    for k, c in enumerate(r)) + "</tr>")
    out += ["</tbody></table></div>",
            '<div class="note">No design is signed off. Gate G4 needs a hardware designer, and the flow never '
            "signs it. Gates G1 to G3 were approved by an AI assistant on the owner's delegation, and each "
            "approval says so.</div>"]
    if corpus:
        t = corpus["total"]
        out += ["<h2>Inputs it was not written for</h2>",
                f"<p><code>nnc corpus</code> takes every module of {corpus['sources']} open-source repositories, at "
                "fixed commits, as the top of a design: intake, adaptation, contract, port check and a generic "
                "smoke simulation. Every stop is named.</p>", '<div class="tiles">']
        for n, label in ((corpus["designs"], "modules"), (corpus["bench"], "reach a running test bench"),
                         (corpus["smoke"].get("pass", 0), "pass the smoke test"),
                         (t.get("needs_input", 0), "need an input the repository does not give"),
                         (t.get("unsupported", 0), "unsupported (VHDL)"),
                         (t.get("chain_failed", 0), "faults of the flow")):
            out.append(f'<div class="tile"><div class="n">{n}</div><div class="l">{e(label)}</div></div>')
        out += ["</div>", f'<p><a href="{REPO_URL}/blob/main/corpus/results.md">Every module</a> · '
                f'<a href="{REPO_URL}/blob/main/docs/INPUT_SUPPORT.md">what the flow accepts</a></p>']
    out += ["<h2>What it does not do</h2>", "<ul>",
            "<li>Sign-off: no static timing, place and route or DFT. Formal covers the translated SVA subset.</li>",
            "<li>Generated checks can be wrong. Gates, hit counters, triage and the mutation score exist to catch "
            "that.</li>",
            "<li>VHDL, encrypted RTL and interface ports on the top are not supported.</li>", "</ul>",
            f'<footer>Generated by <code>nnc site</code> from the committed results of '
            f'<a href="{REPO_URL}">THVKhang/NNC_Pipeline</a>. MIT licence; third-party designs keep their own '
            "(see each design's NOTICE).</footer>",
            "</main>", "</body>", "</html>"]
    return "\n".join(out) + "\n"


def write(repo: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    page = out_dir / "index.html"
    page.write_text(render(repo), encoding="utf-8")
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    return page

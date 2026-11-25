"""A local dashboard of the designs (`nnc ui`): drop a specification and an RTL, run, read the results.

    nnc ui                    # http://127.0.0.1:8765, opens the browser

Home page: every design of designs/ with its numbers (tests, checks, coverage, formal, mutation, gates, last run),
the folders of inbox/ that have not run yet, and a form that uploads a specification, the standards it refers to
and the RTL into inbox/<name>/ (the layout of nnc/autorun.py). A design page shows the run going on (steps,
state, the end of the log, refreshed every few seconds), the gates, the numbers, the reports of work/ rendered
from their Markdown, and a button that starts `nnc run <name>` in a separate process.

Only the standard library; one page per request, no script. The server listens on 127.0.0.1 only and answers
only requests addressed to it by that name (a page of another site cannot post to it). It runs nothing but
`nnc run` on an inbox folder: the committed designs are shown, never re-run from here.
"""
from __future__ import annotations

import email.parser
import email.policy
import html
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from nnc import __version__, autorun
from nnc.project import Design, ProjectError
from nnc.tools import find_claude

MAX_UPLOAD = 256 * 1024 * 1024
LOG_TAIL = 160
TEXT_EXT = (".md", ".json", ".log", ".txt", ".sv", ".v", ".svh", ".vh", ".f", ".py", ".tsv", ".csv", ".sby", ".yml",
            ".yaml", ".info", ".mk")
REPORTS = (("report.md", "Report"), ("review_packet.md", "Review packet"), ("rules.md", "Rules (G1)"),
           ("contract.md", "Contract (G2)"), ("triage.md", "Triage"), ("coverage.md", "Coverage"),
           ("formal.md", "Formal"), ("unr.md", "Unreachable points"), ("cdc.md", "Clock domain crossings"),
           ("intake.md", "Intake"), ("mutation.md", "Mutation"), ("rtl_gen.md", "Generated RTL"))
STATE_LABEL = {"running": "running", "done": "done", "stopped_at_gate": "waiting for a review",
               "needs_input": "needs input", "failed": "failed", "interrupted": "interrupted"}


# ------------------------------------------------------------------------------------------ Markdown
def _esc(s) -> str:
    return html.escape(s if isinstance(s, str) else str(s), quote=True)


def _inline(text: str, link) -> str:
    codes: list[str] = []

    def keep(m):
        codes.append(f"<code>{_esc(m.group(1))}</code>")
        return f"\x00{len(codes) - 1}\x00"
    t = re.sub(r"`([^`]+)`", keep, text)
    t = _esc(t)

    def a(m):
        label, url = m.group(1), html.unescape(m.group(2))
        href = link(url)
        return f'<a href="{_esc(href)}">{label}</a>' if href else label
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", a, t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*([^*\s][^*]*?)\*(?![\w*])", r"<em>\1</em>", t)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], t)


_LIST = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")


def _cells(row: str) -> list[str]:
    row = row.strip()
    row = row[1:] if row.startswith("|") else row
    row = row[:-1] if row.endswith("|") and not row.endswith("\\|") else row
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", row)]


def md_to_html(text: str, link=lambda url: url) -> str:
    """The Markdown the flow writes (headings, paragraphs, lists, tables, code, quotes) as HTML. `link` maps a
    link target to an href, or to None to show the label without a link."""
    lines = text.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    para: list[str] = []

    def flush():
        if para:
            out.append("<p>" + _inline(" ".join(para), link) + "</p>")
            para.clear()
    i = 0
    while i < len(lines):
        ln, s = lines[i], lines[i].strip()
        if s.startswith("```"):
            flush()
            j, buf = i + 1, []
            while j < len(lines) and not lines[j].strip().startswith("```"):
                buf.append(lines[j])
                j += 1
            out.append("<pre><code>" + _esc("\n".join(buf)) + "</code></pre>")
            i = j + 1
            continue
        if s.startswith("<!--"):
            flush()
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*$", ln)
        if m:
            flush()
            n = len(m.group(1))
            out.append(f"<h{n}>{_inline(m.group(2), link)}</h{n}>")
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            flush()
            head = _cells(s)
            align = ["right" if c.endswith(":") and not c.startswith(":") else "" for c in _cells(lines[i + 1])]
            rows = []
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1

            def td(tag, c, k):
                al = f' class="r"' if k < len(align) and align[k] else ""
                return f"<{tag}{al}>{_inline(c, link)}</{tag}>"
            out.append('<div class="tw"><table><thead><tr>' + "".join(td("th", c, k) for k, c in enumerate(head))
                       + "</tr></thead><tbody>" + "".join("<tr>" + "".join(td("td", c, k) for k, c in enumerate(r))
                                                          + "</tr>" for r in rows) + "</tbody></table></div>")
            continue
        if _LIST.match(ln):
            flush()
            items = []
            while i < len(lines):
                m = _LIST.match(lines[i])
                if m:
                    items.append([len(m.group(1).replace("\t", "    ")), m.group(2)[0].isdigit(), m.group(3)])
                elif lines[i].strip() and lines[i][:1] in (" ", "\t") and items:
                    items[-1][2] += " " + lines[i].strip()
                elif not lines[i].strip() and i + 1 < len(lines) and _LIST.match(lines[i + 1]) \
                        and lines[i + 1][:1] in (" ", "\t"):
                    pass
                else:
                    break
                i += 1
            stack: list[tuple[int, str]] = []
            for ind, ordered, txt in items:
                tag = "ol" if ordered else "ul"
                while stack and ind < stack[-1][0]:
                    out.append(f"</li></{stack.pop()[1]}>")
                if stack and ind == stack[-1][0]:
                    out.append("</li>")
                else:
                    out.append(f"<{tag}>")
                    stack.append((ind, tag))
                out.append("<li>" + _inline(txt, link))
            while stack:
                out.append(f"</li></{stack.pop()[1]}>")
            continue
        if s.startswith(">"):
            flush()
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            out.append("<blockquote>" + md_to_html("\n".join(buf), link) + "</blockquote>")
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            flush()
            out.append("<hr>")
            i += 1
            continue
        if not s:
            flush()
        else:
            para.append(s)
        i += 1
    flush()
    return "\n".join(out)


# ------------------------------------------------------------------------------------------ data
def _read(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
    except ValueError:
        return None


def numbers(root: Path) -> dict:
    """The numbers of one workspace, from its files (as nnc/summary.py reads them)."""
    w = root / "work"
    res, rep, fm, mu = _read(w / "results.json"), _read(w / "report.json"), _read(w / "formal.json"), \
        _read(w / "mutation.json")
    out: dict = {}
    if res:
        st = [t.get("status") for t in res.get("tests") or []]
        out["tests"] = (st.count("pass"), len(st))
        cov = res.get("coverage") or {}
        out["coverage"] = {k: v.get("percent") for k, v in (cov.get("metrics") or {}).items()
                           if isinstance(v, dict) and v.get("percent") is not None}
        out["unreviewed"] = res.get("unreviewed_gates") or []
    if rep:
        by = (rep.get("checks") or {}).get("by_status") or {}
        out["checks"] = (by.get("PASS", 0), sum(by.values()), by)
    if fm:
        out["formal"] = fm.get("by_status") or {}
    if mu:
        out["mutation"] = (mu.get("score"), mu.get("killed"), (mu.get("killed") or 0) + (mu.get("survived") or 0))
    try:
        out["gates"] = [(s.gate, s.state, s.detail) for s in Design.open(root).status()]
    except (ProjectError, OSError, ValueError, KeyError):
        out["gates"] = []
    return out


# ------------------------------------------------------------------------------------------ server state
class Dashboard:
    def __init__(self, root: Path, inbox: Path, cwd: Path | None = None):
        self.root, self.inbox = Path(root), Path(inbox)
        self.cwd = Path(cwd or os.getcwd())
        self.procs: dict[str, subprocess.Popen] = {}
        self.lock = threading.Lock()

    def designs(self) -> list[str]:
        if not self.root.is_dir():
            return []
        return sorted(p.name for p in self.root.iterdir() if (p / "nnc_state.json").is_file())

    def running(self, name: str) -> bool:
        p = self.procs.get(name)
        return p is not None and p.poll() is None

    def record(self, name: str) -> dict | None:
        """work/run.json (or the inbox's .run.json before the workspace exists). A run recorded as running
        whose process is gone is shown as interrupted."""
        rec = autorun.read_record(self.root / name) or _read(self.inbox / name / ".run.json")
        if rec and rec.get("state") == "running" and not self.running(name) and not _alive(rec.get("pid")):
            code = self.procs[name].returncode if name in self.procs else None
            rec = dict(rec, state="interrupted", message="the run's process ended before it recorded its end"
                       + (f" (exit code {code})" if code is not None else ""))
        return rec

    def log(self, name: str) -> str:
        p = self.inbox / name / autorun.LOG_FILE
        if not p.is_file():
            return ""
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[-LOG_TAIL:])

    def start(self, name: str, backend: str, gated: bool, jobs: int | None = None) -> None:
        autorun.check_name(name)
        if backend not in ("claude", "replay", "manual"):
            raise ProjectError(f"unknown backend {backend}")
        folder = self.inbox / name
        box = autorun.read_inbox(folder)
        if box["problems"]:
            raise ProjectError("; ".join(box["problems"]))
        with self.lock:
            if self.running(name):
                raise ProjectError(f"{name} is already running")
            argv = [sys.executable, "-m", "nnc", "--root", str(self.root.resolve()), "run", name,
                    "--inbox", str(self.inbox.resolve()), "--backend", backend] + (["--gated"] if gated else []) \
                + (["--jobs", str(jobs)] if jobs else [])
            log = open(folder / autorun.LOG_FILE, "w", encoding="utf-8")
            env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
            flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            self.procs[name] = subprocess.Popen(argv, cwd=self.cwd, stdout=log, stderr=subprocess.STDOUT,
                                                stdin=subprocess.DEVNULL, env=env, creationflags=flags,
                                                start_new_session=os.name != "nt")
            log.close()

    def stop(self, name: str) -> None:
        p = self.procs.get(name)
        if p is None or p.poll() is not None:
            return
        if os.name == "nt":  # the whole tree: the flow starts simulators and agents
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
        else:
            import signal
            os.killpg(p.pid, signal.SIGTERM)

    def save_upload(self, fields: dict[str, list]) -> str:
        """Write the uploaded files into inbox/<name>/; returns the name."""
        name = autorun.check_name((fields.get("name") or [""])[0].strip())
        folder = self.inbox / name
        spec = [f for f in fields.get("spec") or [] if isinstance(f, tuple) and f[0]]
        stds = [f for f in fields.get("standards") or [] if isinstance(f, tuple) and f[0]]
        rtl = [f for f in fields.get("rtl") or [] if isinstance(f, tuple) and f[0]]
        if not folder.is_dir() and (not spec or not rtl):
            raise ProjectError("a new design needs a specification and at least one RTL file")
        if len(spec) > 1:
            raise ProjectError("give one specification file; the standards it refers to go in 'Standards'")
        written = []
        for kind, files, ext in (("spec", spec, autorun.SPEC_EXT), ("standards", stds, autorun.SPEC_EXT),
                                 ("rtl", rtl, autorun.RTL_EXT)):
            for fname, data in files:
                rel = _safe_rel(fname)
                if rel is None or Path(rel).suffix.lower() not in ext:
                    raise ProjectError(f"{fname}: not a {kind} file ({' '.join(ext)})")
                written.append((kind, rel, data))
        if spec and (folder / "spec").is_dir():
            shutil.rmtree(folder / "spec")
        for kind, rel, data in written:
            dst = folder / kind / (Path(rel).name if kind != "rtl" else rel)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
        top = (fields.get("top") or [""])[0].strip()
        cfg_p = folder / "inbox.json"
        cfg = _read(cfg_p) or {}
        if top:
            if not re.match(r"^[A-Za-z_]\w*$", top):
                raise ProjectError(f"invalid top module name '{top}'")
            cfg["top"] = top
            cfg_p.write_text(json.dumps(cfg, indent=1) + "\n", encoding="utf-8")
        return name


def _alive(pid) -> bool:
    """Is a process with this id running? (A run started from a terminal is not a child of the dashboard.)"""
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":  # os.kill(pid, 0) would end the process on Windows
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"], capture_output=True,
                           text=True, errors="replace")
        return f'"{pid}"' in r.stdout
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _safe_rel(fname: str) -> str | None:
    """A file name of an upload as a relative path with no way out of its folder (folder uploads keep their
    sub-folders); None when it is not one."""
    parts = [p for p in re.split(r"[\\/]+", fname) if p not in ("", ".")]
    if not parts or any(p == ".." or not re.match(r"^[\w.+-]+$", p) or p.startswith(".") for p in parts):
        return None
    return "/".join(parts[1:] if len(parts) > 1 else parts)  # a folder upload's first part is the folder


# ------------------------------------------------------------------------------------------ pages
CSS = """
:root{--bg:#f7f7f5;--panel:#fff;--ink:#1d1d1f;--mute:#5f6368;--line:#e2e2de;--accent:#2b59c3;--ok:#1e7a3c;
--warn:#a15c00;--bad:#b3261e;--chip:#eef1f7;--code:#f1f1ee}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#141416;--panel:#1d1d20;--ink:#ececec;
--mute:#a0a0a8;--line:#323238;--accent:#8fb0ff;--ok:#6fcf8f;--warn:#f0b050;--bad:#ff8a80;--chip:#262a33;
--code:#26262a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,
"Segoe UI",Roboto,sans-serif}a{color:var(--accent);text-underline-offset:3px}td{overflow-wrap:anywhere}
.card .v.s{font-size:15px;line-height:1.35}header{background:var(--panel);border-bottom:1px solid var(--line);
padding:12px 16px}header .in{max-width:1180px;margin:0 auto;display:flex;gap:16px;align-items:baseline;flex-wrap:wrap}
header b{font-size:17px}header span{color:var(--mute);font-size:13px}main{max-width:1180px;margin:0 auto;padding:16px}
section{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px;margin:0 0 16px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:0 0 12px}h3{font-size:15px}.mute{color:var(--mute)}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:6px 8px;
border-bottom:1px solid var(--line);vertical-align:top}th{font-weight:600;color:var(--mute);font-size:13px}
td.r,th.r{text-align:right}code{background:var(--code);padding:1px 4px;border-radius:4px;font-size:13px}
pre{background:var(--code);padding:10px;border-radius:6px;overflow-x:auto;font-size:12.5px;line-height:1.45}
pre code{background:none;padding:0}.chip{display:inline-block;padding:1px 8px;border-radius:10px;font-size:12.5px;
background:var(--chip);white-space:nowrap}.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px}.card{border:1px solid
var(--line);border-radius:8px;padding:10px}.card .v{font-size:20px;font-weight:600}.card .k{color:var(--mute);
font-size:12.5px}form.up{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
label{display:block;font-size:13px;color:var(--mute);margin-bottom:3px}input[type=text],select{width:100%;padding:6px 8px;
border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink)}input[type=file]{width:100%;
font-size:13px}button{padding:7px 14px;border-radius:6px;border:1px solid var(--accent);background:var(--accent);
color:var(--panel);font-weight:600;cursor:pointer}button.alt{background:transparent;color:var(--accent)}
button.stop{border-color:var(--bad);background:transparent;color:var(--bad)}.row{display:flex;gap:8px;flex-wrap:wrap;
align-items:center}.md h1{font-size:20px}.md h2{font-size:17px;margin-top:20px}.md h3{font-size:15px}.md table{margin:8px 0}
.note{border-left:3px solid var(--warn);padding:6px 10px;background:var(--code);border-radius:4px;font-size:14px}
blockquote{border-left:3px solid var(--line);margin:0;padding-left:12px;color:var(--mute)}
@media (max-width:640px){main{padding:12px}section{padding:12px}}
"""


def _page(title: str, body: str, refresh: int | None = None) -> bytes:
    meta = f'<meta http-equiv="refresh" content="{refresh}">' if refresh else ""
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width,initial-scale=1">{meta}<title>{_esc(title)}</title><style>{CSS}</style>'
            f'</head><body><header><div class="in"><b><a href="/" style="color:inherit;text-decoration:none">NNC '
            f'Pipeline</a></b><span>specification-driven RTL verification · nnc {__version__} · local dashboard'
            f'</span></div></header><main>{body}</main></body></html>').encode("utf-8")


def _state_chip(state: str | None) -> str:
    if not state:
        return '<span class="chip mute">not run</span>'
    cls = {"done": "ok", "running": "warn", "stopped_at_gate": "warn", "needs_input": "bad", "failed": "bad",
           "interrupted": "bad"}.get(state, "")
    return f'<span class="chip {cls}">{_esc(STATE_LABEL.get(state, state))}</span>'


def _pct(v) -> str:
    return "–" if v is None else f"{v:g} %"


def _formal_text(fm: dict | None) -> str:
    if not fm:
        return "–"
    order = ("PROVEN", "BOUNDED", "TIMEOUT", "UNSUPPORTED", "VACUOUS", "CEX", "ERROR")
    return ", ".join(f"{fm[k]} {k.lower()}" for k in order if fm.get(k)) or "–"


def _gates_text(gates: list) -> str:
    if not gates:
        return "–"
    ok = sum(1 for _g, s, _d in gates if s == "APPROVED")
    g4 = next((s for g, s, _d in gates if g == "G4_signoff"), None)
    return f"{ok}/{len(gates)} approved" + (f" · G4 {g4.lower()}" if g4 and g4 != "APPROVED" else "")


def home(db: Dashboard, msg: str = "") -> bytes:
    names = db.designs()
    inbox_only = [n for n in autorun.list_inbox(db.inbox) if n not in names]
    rows = []
    for n in names + inbox_only:
        num = numbers(db.root / n) if n in names else {}
        rec = db.record(n)
        cov = num.get("coverage") or {}
        cov_t = " · ".join(f"{k[:4]} {_pct(cov[k])}" for k in ("line", "block", "expression", "toggle") if k in cov)
        t = num.get("tests")
        c = num.get("checks")
        m = num.get("mutation")
        src = "inbox" if (db.inbox / n).is_dir() else "designs"
        rows.append(f'<tr><td><a href="/d/{n}">{_esc(n)}</a></td><td class="mute">{src}</td>'
                    f'<td class="r">{f"{t[0]}/{t[1]}" if t else "–"}</td><td class="r">{f"{c[0]}/{c[1]}" if c else "–"}</td>'
                    f'<td>{cov_t or "–"}</td><td>{_formal_text(num.get("formal"))}</td>'
                    f'<td class="r">{_pct(m[0]) if m else "–"}</td><td>{_gates_text(num.get("gates"))}</td>'
                    f'<td>{_state_chip(rec and rec.get("state"))}</td></tr>')
    claude = find_claude()      # as the agent backend finds it (NNC_CLAUDE_BIN, PATH, VS Code extension)
    body = (f'{f"<p class=note>{_esc(msg)}</p>" if msg else ""}'
            '<section><h1>Add a design</h1><p class="mute">Give the specification of the block and its RTL. The '
            'files go to <code>inbox/&lt;name&gt;/</code>; the run makes <code>designs/&lt;name&gt;/</code> and '
            'writes the results there. Without review, every result is marked UNREVIEWED: a hardware designer '
            'still has to review the gates before the report can be signed off.</p>'
            '<form class="up" method="post" action="/upload" enctype="multipart/form-data">'
            '<div><label>Name (letters, digits, _)</label><input type="text" name="name" required '
            'pattern="[A-Za-z][A-Za-z0-9_\\-]*" placeholder="my_fifo"></div>'
            '<div><label>Top module (optional, found by the intake)</label><input type="text" name="top" '
            'placeholder="m_my_fifo"></div>'
            f'<div><label>Specification: one file ({" ".join(autorun.SPEC_EXT)})</label>'
            '<input type="file" name="spec" accept="' + ",".join(autorun.SPEC_EXT) + '"></div>'
            '<div><label>Standards it refers to (optional, several)</label>'
            '<input type="file" name="standards" multiple accept="' + ",".join(autorun.SPEC_EXT) + '"></div>'
            '<div><label>RTL files (several; .sv .v .svh .vh, filelist.f)</label>'
            '<input type="file" name="rtl" multiple></div>'
            '<div><label>Agents</label><select name="backend">'
            '<option value="claude">Claude Code (agent cost)</option>'
            '<option value="replay">replay: cached answers only, no cost</option></select>'
            + ('' if claude else '<div class="mute" style="font-size:12.5px">Claude Code was not found (PATH, '
               'NNC_CLAUDE_BIN, VS Code extension): install it to run the agents</div>') + '</div>'
            '<div><label>Gates</label><select name="gated"><option value="">run to the report (UNREVIEWED)</option>'
            '<option value="1">stop at each gate for review</option></select></div>'
            '<div class="row" style="align-self:end"><button name="go" value="run">Upload and run</button>'
            '<button class="alt" name="go" value="save">Upload only</button></div></form></section>'
            '<section><h2>Designs</h2><div class="tw"><table><thead><tr><th>Design</th><th>From</th>'
            '<th class="r">Tests passing</th><th class="r">Checks PASS</th><th>Coverage</th><th>Formal</th>'
            '<th class="r">Mutation</th><th>Gates</th><th>Last run</th></tr></thead><tbody>'
            + "".join(rows) + '</tbody></table></div><p class="mute">Numbers come from each design\'s '
            '<code>work/</code> files. G4 (sign-off) is for a hardware designer; the flow never signs it.</p>'
            '</section>')
    return _page("NNC dashboard", body)


def _link_for(name: str, base: str):
    """Links of a rendered file: inside the workspace, to its page here; elsewhere, plain text."""
    def link(url: str):
        if re.match(r"^[a-z]+://", url) or url.startswith("mailto:"):
            return url
        if url.startswith("#"):
            return url
        target = posixpath.normpath(posixpath.join(posixpath.dirname(base), url.split("#")[0]))
        if target.startswith("..") or target.startswith("/"):
            return None
        return f"/d/{name}/f/{urllib.parse.quote(target)}"
    return link


def design_page(db: Dashboard, name: str, msg: str = "") -> bytes:
    root = db.root / name
    is_ws = (root / "nnc_state.json").is_file()
    in_box = (db.inbox / name).is_dir()
    if not is_ws and not in_box:
        raise FileNotFoundError(name)
    rec = db.record(name)
    running = db.running(name) or (rec or {}).get("state") == "running"
    parts = [f"<p class=note>{_esc(msg)}</p>" if msg else ""]
    buttons = ""
    if in_box:
        box = autorun.read_inbox(db.inbox / name)
        if db.running(name):
            buttons = (f'<form method="post" action="/stop/{name}"><button class="stop">Stop</button></form>')
        elif not box["problems"]:
            buttons = (f'<form method="post" action="/run/{name}" class="row"><select name="backend">'
                       '<option value="claude">Claude Code (agent cost)</option>'
                       '<option value="replay">replay (no cost)</option></select><select name="gated">'
                       '<option value="">to the report (UNREVIEWED)</option><option value="1">stop at gates</option>'
                       '</select><button>Run</button></form>')
        files = ", ".join(_esc(p.name) for p in ([box["spec"]] if box["spec"] else []) + box["standards"])
        probs = "".join(f"<li class=bad>{_esc(p)}</li>" for p in box["problems"])
        parts.append(f'<section><div class="row" style="justify-content:space-between"><div><h1>{_esc(name)}</h1>'
                     f'<span class="mute">inbox/{_esc(name)}: specification {files or "–"}; {len(box["rtl"])} RTL '
                     f'file(s)</span></div>{buttons}</div>{f"<ul>{probs}</ul>" if probs else ""}</section>')
    else:
        parts.append(f'<section><h1>{_esc(name)}</h1><span class="mute">designs/{_esc(name)} (shown here, not '
                     'run from here)</span></section>')
    if rec:
        steps = "".join(f'<tr><td>{_esc(s["name"])}</td><td>{_state_chip(s.get("state"))}</td>'
                        f'<td class="r">{s.get("seconds", "")}</td><td>{_esc(s.get("note", ""))}</td></tr>'
                        for s in rec.get("steps") or [])
        fin = f', finished {_esc(rec["finished"])}' if rec.get("finished") else ""
        message = f'<p>{_esc(rec["message"])}</p>' if rec.get("message") else ""
        parts.append(f'<section><h2>Run {_state_chip(rec.get("state"))}</h2><p class="mute">started '
                     f'{_esc(str(rec.get("started")))}, mode {_esc(str(rec.get("mode")))}, agents '
                     f'{_esc(str(rec.get("backend")))}{fin}</p>{message}'
                     f'<div class="tw"><table><thead><tr><th>Step</th><th>State</th><th class="r">Seconds</th>'
                     f'<th>Note</th></tr></thead><tbody>{steps}</tbody></table></div></section>')
    log = db.log(name) if in_box else ""
    if log:
        parts.append(f'<section><h2>Log (last {LOG_TAIL} lines{", refreshed every 4 s" if running else ""})</h2>'
                     f'<pre>{_esc(log)}</pre></section>')
    if is_ws:
        num = numbers(root)
        cards = []
        if num.get("tests"):
            t = num["tests"]
            cards.append(("Tests passing", f"{t[0]}/{t[1]}", "ok" if t[0] == t[1] else "warn"))
        if num.get("checks"):
            c = num["checks"]
            cards.append(("Checks PASS", f"{c[0]}/{c[1]}", "ok" if c[0] == c[1] else "warn"))
        for k, v in (num.get("coverage") or {}).items():
            cards.append((f"Coverage {k}", _pct(v), ""))
        if num.get("mutation"):
            m = num["mutation"]
            cards.append(("Mutation score", f"{_pct(m[0])} ({m[1]}/{m[2]})", ""))
        if num.get("formal"):
            cards.append(("Formal", _formal_text(num["formal"]), ""))
        if cards:
            unrev = num.get("unreviewed")
            parts.append('<section><h2>Results</h2>' + (
                f'<p class="note">UNREVIEWED: gates {", ".join(map(_esc, unrev))} were not reviewed by a person.</p>'
                if unrev else "") + '<div class="grid">' + "".join(
                f'<div class="card"><div class="k">{_esc(k)}</div><div class="v {cls}{" s" if len(v) > 14 else ""}">'
                f'{_esc(v)}</div></div>'
                for k, v, cls in cards) + "</div></section>")
        if num.get("gates"):
            parts.append('<section><h2>Gates</h2><div class="tw"><table><thead><tr><th>Gate</th><th>State</th>'
                         '<th>Detail</th></tr></thead><tbody>' + "".join(
                             f'<tr><td>{_esc(g)}</td><td><span class="chip {"ok" if s == "APPROVED" else ""}">'
                             f'{_esc(s)}</span></td><td class="mute">{_esc(d)}</td></tr>' for g, s, d in num["gates"])
                         + '</tbody></table></div><p class="mute">Approve a gate after reading its review sheet: '
                         f'<code>nnc gate approve {_esc(name)} &lt;gate&gt; --by "Your Name"</code>.</p></section>')
        links = [f'<a href="/d/{name}/f/work/{f}">{t}</a>' for f, t in REPORTS if (root / "work" / f).is_file()]
        if links:
            parts.append('<section><h2>Reports</h2><div class="row">' + " · ".join(links) + "</div></section>")
        rep = root / "work" / "report.md"
        if rep.is_file():
            parts.append('<section class="md">' + md_to_html(rep.read_text(encoding="utf-8", errors="replace"),
                                                             _link_for(name, "work/report.md")) + "</section>")
    return _page(f"{name} · NNC", "".join(parts), refresh=4 if running else None)


def file_page(db: Dashboard, name: str, rel: str) -> bytes:
    base = (db.root / name).resolve()
    target = (base / rel).resolve()
    if not target.is_relative_to(base) or not target.is_file() or target.suffix.lower() not in TEXT_EXT:
        raise FileNotFoundError(rel)
    text = target.read_text(encoding="utf-8", errors="replace")
    relp = target.relative_to(base).as_posix()
    if len(text) > 3_000_000:
        text = text[:3_000_000] + "\n... (cut)"
    if target.suffix.lower() == ".md":
        inner = '<section class="md">' + md_to_html(text, _link_for(name, relp)) + "</section>"
    else:
        inner = f"<section><pre>{_esc(text)}</pre></section>"
    return _page(f"{relp} · {name}", f'<p><a href="/d/{name}">← {_esc(name)}</a> · <code>{_esc(relp)}</code></p>'
                 + inner)


# ------------------------------------------------------------------------------------------ HTTP
def parse_multipart(ctype: str, body: bytes) -> dict[str, list]:
    """Form fields of a multipart/form-data body: {name: [text or (filename, bytes)]}."""
    msg = email.parser.BytesParser(policy=email.policy.HTTP).parsebytes(
        b"Content-Type: " + ctype.encode("latin-1") + b"\r\nMIME-Version: 1.0\r\n\r\n" + body)
    out: dict[str, list] = {}
    if not msg.is_multipart():
        return out
    for part in msg.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if not name:
            continue
        fname = part.get_filename()
        data = part.get_payload(decode=True) or b""
        out.setdefault(name, []).append((fname, data) if fname is not None else data.decode("utf-8", "replace"))
    return out


class Handler(BaseHTTPRequestHandler):
    db: Dashboard = None  # set by make_server
    server_version = "nnc-ui"

    def log_message(self, fmt, *args):  # quiet
        pass

    def _local(self) -> bool:
        port = self.server.server_address[1]
        ok = {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"}
        if self.headers.get("Host") not in ok:
            return False
        origin = self.headers.get("Origin")   # a form posted by a page of another site carries its origin
        return origin is None or urllib.parse.urlsplit(origin).netloc in ok

    def _send(self, code: int, body: bytes, ctype: str = "text/html; charset=utf-8", headers: dict | None = None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, to: str):
        self._send(303, b"", headers={"Location": to})

    def _error(self, code: int, text: str):
        self._send(code, _page("Error", f'<section><h1>{code}</h1><p>{_esc(text)}</p><p><a href="/">Back</a></p>'
                                        '</section>'))

    def do_GET(self):
        if not self._local():
            return self._error(403, "only local requests addressed to this server are answered")
        url = urllib.parse.urlsplit(self.path)
        q = urllib.parse.parse_qs(url.query)
        path = urllib.parse.unquote(url.path)
        msg = (q.get("msg") or [""])[0]
        try:
            if path == "/":
                return self._send(200, home(self.db, msg))
            m = re.match(r"^/d/([A-Za-z][A-Za-z0-9_-]*)/?$", path)
            if m:
                return self._send(200, design_page(self.db, m.group(1), msg))
            m = re.match(r"^/d/([A-Za-z][A-Za-z0-9_-]*)/f/(.+)$", path)
            if m:
                return self._send(200, file_page(self.db, m.group(1), m.group(2)))
            if path == "/api/designs":
                data = {n: {"numbers": numbers(self.db.root / n), "run": self.db.record(n)} for n in self.db.designs()}
                return self._send(200, json.dumps(data, default=str).encode(), "application/json")
        except FileNotFoundError:
            pass
        except Exception as e:  # a page that cannot be made says why instead of dropping the connection
            return self._error(500, f"{type(e).__name__}: {e}")
        self._error(404, "not found")

    def do_POST(self):
        if not self._local():
            return self._error(403, "only local requests addressed to this server are answered")
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_UPLOAD:
            return self._error(413, f"upload larger than {MAX_UPLOAD // 2**20} MB")
        body = self.rfile.read(n)
        ctype = self.headers.get("Content-Type", "")
        fields = parse_multipart(ctype, body) if ctype.startswith("multipart/form-data") else \
            {k: v for k, v in urllib.parse.parse_qs(body.decode("utf-8", "replace")).items()}
        def first(k: str) -> str:
            return next((v for v in fields.get(k) or [] if isinstance(v, str)), "")
        path = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
        try:
            if path == "/upload":
                name = self.db.save_upload(fields)
                if first("go") == "run":
                    self.db.start(name, first("backend") or "claude", bool(first("gated")))
                    return self._redirect(f"/d/{name}?msg=" + urllib.parse.quote("started"))
                return self._redirect(f"/d/{name}?msg=" + urllib.parse.quote("files saved in inbox/" + name))
            m = re.match(r"^/(run|stop)/([A-Za-z][A-Za-z0-9_-]*)$", path)
            if m and m.group(1) == "run":
                self.db.start(m.group(2), first("backend") or "claude", bool(first("gated")))
                return self._redirect(f"/d/{m.group(2)}?msg=" + urllib.parse.quote("started"))
            if m:
                self.db.stop(m.group(2))
                return self._redirect(f"/d/{m.group(2)}?msg=" + urllib.parse.quote("stopped"))
        except ProjectError as e:
            back = "/" if path == "/upload" else f"/d/{path.rsplit('/', 1)[-1]}"
            return self._redirect(back + "?msg=" + urllib.parse.quote(f"error: {e}"))
        self._error(404, "not found")


def make_server(db: Dashboard, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    handler = type("BoundHandler", (Handler,), {"db": db})
    srv = ThreadingHTTPServer((host, port), handler)
    srv.daemon_threads = True
    return srv


def serve(root: Path, inbox: Path, port: int = 8765, open_browser: bool = True) -> None:
    db = Dashboard(root, inbox)
    srv = make_server(db, "127.0.0.1", port)
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    print(f"NNC dashboard: {url}  (designs {Path(root).resolve()}, inbox {Path(inbox).resolve()}); Ctrl+C stops it")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()

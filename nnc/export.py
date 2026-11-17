"""Export the documents of a design to DOCX, HTML and PDF (`nnc export`).

Sources are the Markdown files the flow keeps: the IP specification and the review sheets/reports
(rules, contract, RTL generation report, verification report, review packet). Pandoc converts Markdown to
DOCX and to a standalone HTML page (pandoc comes from the `pypandoc_binary` wheel, or a `pandoc` on PATH);
the PDF is printed from that HTML by a headless Chromium browser (Edge or Chrome; NNC_BROWSER overrides).
A format whose tool is missing is skipped with a message: nothing else depends on the export.

Only documents of the design itself are exported. Standards under spec/standards/ are never exported: their
text is licensed.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

SOURCES = {
    "spec": None,                          # the registered ip_spec document
    "rules": "work/rules.md",
    "contract": "work/contract.md",
    "rtl": "work/rtl_gen.md",
    "report": "work/report.md",
    "packet": "work/review_packet.md",
    "triage": "work/triage.md",
}
FORMATS = ("docx", "html", "pdf")
CSS = """body{font-family:Segoe UI,Arial,sans-serif;max-width:60em;margin:2em auto;padding:0 1em;line-height:1.45;color:#222}
table{border-collapse:collapse;margin:1em 0;font-size:.9em}th,td{border:1px solid #bbb;padding:.3em .5em;vertical-align:top}
th{background:#eee}code,pre{font-family:Consolas,monospace;font-size:.9em}pre{background:#f6f6f6;padding:.6em;overflow-x:auto}
h1,h2,h3{line-height:1.2}@media print{body{max-width:none;margin:0}a{color:inherit}}"""
BROWSERS = (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def pandoc_path() -> str | None:
    try:
        import pypandoc
        return pypandoc.get_pandoc_path()
    except (ImportError, OSError):
        return shutil.which("pandoc")


def browser_path() -> str | None:
    env = os.environ.get("NNC_BROWSER")
    if env:
        return env
    for p in BROWSERS:
        if Path(p).is_file():
            return p
    for n in ("msedge", "google-chrome", "chromium", "chromium-browser", "chrome"):
        if shutil.which(n):
            return shutil.which(n)
    return None


def sources(design_root: Path, documents: list[dict], what: list[str]) -> list[tuple[str, Path]]:
    out = []
    for w in what:
        if w not in SOURCES:
            raise ValueError(f"unknown document '{w}'; choose from {', '.join(SOURCES)}")
        if w == "spec":
            ip = next((d for d in documents if d["role"] == "ip_spec"), None)
            if ip and ip["file"].lower().endswith(".md"):
                out.append(("spec", design_root / ip["file"]))
            continue
        p = design_root / SOURCES[w]
        if p.is_file():
            out.append((w, p))
    return out


def export(design_root: Path, documents: list[dict], what: list[str], formats: list[str], out_dir: Path,
           title_prefix: str = "") -> list[dict]:
    """Convert each source; returns [{doc, format, path | skipped}]."""
    bad = [f for f in formats if f not in FORMATS]
    if bad:
        raise ValueError(f"unknown format(s) {bad}; choose from {', '.join(FORMATS)}")
    pandoc, browser = pandoc_path(), browser_path()
    out_dir.mkdir(parents=True, exist_ok=True)
    css = out_dir / "nnc_export.css"
    css.write_text(CSS, encoding="utf-8")
    results = []
    for name, src in sources(design_root, documents, what):
        stem = f"{design_root.name}_{name}"
        title = f"{title_prefix}{design_root.name}: {name}"
        common = [pandoc, str(src), "--from", "gfm+pipe_tables", "--resource-path", str(src.parent),
                  "--metadata", f"title={title}"]
        html = out_dir / f"{stem}.html"
        for fmt in formats:
            if pandoc is None and fmt in ("docx", "html", "pdf"):
                results.append({"doc": name, "format": fmt, "skipped": "pandoc not found (pip install pypandoc_binary)"})
                continue
            if fmt == "docx":
                dst = out_dir / f"{stem}.docx"
                _run(common + ["--toc", "-o", str(dst)])
                results.append({"doc": name, "format": "docx", "path": str(dst)})
            elif fmt in ("html", "pdf") and not html.is_file():
                _run(common + ["--standalone", "--embed-resources", "--css", str(css), "--toc", "-o", str(html)])
            if fmt == "html":
                results.append({"doc": name, "format": "html", "path": str(html)})
            if fmt == "pdf":
                if browser is None:
                    results.append({"doc": name, "format": "pdf", "skipped": "no Edge/Chrome/Chromium (set NNC_BROWSER)"})
                    continue
                dst = out_dir / f"{stem}.pdf"
                if dst.exists():
                    dst.unlink()
                profile = Path(tempfile.mkdtemp(prefix="nnc_browser_"))   # never hand over to a running browser
                try:
                    _run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                          f"--user-data-dir={profile}", f"--print-to-pdf={dst}", html.resolve().as_uri()], timeout=180)
                    _wait_file(dst, 120)
                finally:
                    shutil.rmtree(profile, ignore_errors=True)
                results.append({"doc": name, "format": "pdf", "path": str(dst)} if dst.is_file() else
                               {"doc": name, "format": "pdf", "skipped": "the browser wrote no PDF"})
        if "html" not in formats and html.is_file():
            html.unlink()
    return results


def _wait_file(path: Path, timeout_s: float) -> None:
    """A browser may return before it has written the PDF: wait until the file exists and its size is stable."""
    end, last = time.monotonic() + timeout_s, -1
    while time.monotonic() < end:
        size = path.stat().st_size if path.is_file() else -1
        if size > 0 and size == last:
            return
        last = size
        time.sleep(1.0)


def _run(argv: list[str], timeout: int = 300) -> None:
    proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"{Path(argv[0]).name} failed: {proc.stderr.strip()[-500:]}")

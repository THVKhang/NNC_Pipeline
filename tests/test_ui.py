"""nnc ui (nnc/ui.py): Markdown rendering, pages, uploads, and the local-only rule."""
import http.client
import json
import tempfile
import threading
import unittest
import uuid
from pathlib import Path
from unittest import mock

from nnc import ui
from nnc.project import Design
from tests.test_autorun import make_inbox

REPO = Path(__file__).resolve().parents[1]


def multipart(fields: list[tuple[str, str | tuple[str, bytes]]]) -> tuple[str, bytes]:
    b = uuid.uuid4().hex
    out = b""
    for name, v in fields:
        if isinstance(v, tuple):
            out += (f'--{b}\r\nContent-Disposition: form-data; name="{name}"; filename="{v[0]}"\r\n'
                    "Content-Type: application/octet-stream\r\n\r\n").encode() + v[1] + b"\r\n"
        else:
            out += f'--{b}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{v}\r\n'.encode()
    return f"multipart/form-data; boundary={b}", out + f"--{b}--\r\n".encode()


class MarkdownTest(unittest.TestCase):
    def test_blocks(self):
        md = ("# Title\n\nSome **bold** and `a|b <x>` text,\njoined.\n\n| A | B |\n|---|---:|\n| 1 | `c` |\n\n"
              "- one\n  more\n  - nested\n- two\n\n1. first\n\n```\n<raw> & code\n```\n> quoted\n\n---\n"
              "<!-- hidden\n comment -->\nend")
        h = ui.md_to_html(md)
        self.assertIn("<h1>Title</h1>", h)
        self.assertIn("<p>Some <strong>bold</strong> and <code>a|b &lt;x&gt;</code> text, joined.</p>", h)
        self.assertIn('<th>A</th><th class="r">B</th>', h)
        self.assertIn("<td>1</td><td class=\"r\"><code>c</code></td>", h)
        self.assertIn("<ul><li>one more<ul><li>nested</li></ul></li><li>two</li></ul>", h.replace("\n", ""))
        self.assertIn("<ol><li>first</li></ol>", h.replace("\n", ""))
        self.assertIn("<pre><code>&lt;raw&gt; &amp; code</code></pre>", h)
        self.assertIn("<blockquote><p>quoted</p></blockquote>", h)
        self.assertIn("<hr>", h)
        self.assertNotIn("hidden", h)
        self.assertIn("<p>end</p>", h)

    def test_no_markup_gets_through(self):
        h = ui.md_to_html('<script>alert(1)</script> [x](javascript:alert(1)) "q"')
        self.assertNotIn("<script>", h)
        link = ui._link_for("d", "work/report.md")
        self.assertIsNone(link("../../../etc/passwd"))
        h = ui.md_to_html("[f](formal.md#x) [o](https://example.org) [up](../../README.md)", link)
        self.assertIn('href="/d/d/f/work/formal.md"', h)
        self.assertIn('href="https://example.org"', h)
        self.assertIn("up", h)
        self.assertNotIn("README", h.split("up")[0][-40:])

    def test_link_schemes(self):
        link = ui._link_for("d", "work/report.md")
        self.assertEqual(link("#top"), "#top")
        self.assertEqual(link("javascript:alert(1)"), "/d/d/f/work/javascript%3Aalert%281%29")

    def test_safe_rel(self):
        self.assertEqual(ui._safe_rel("m.sv"), "m.sv")
        self.assertEqual(ui._safe_rel("proj/sub/m.sv"), "sub/m.sv")
        for bad in ("../m.sv", "a/../../m.sv", ".hidden", "", "a b.sv", "C:\\..\\x.sv"):
            self.assertIsNone(ui._safe_rel(bad), bad)


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "designs").mkdir()
        self.db = ui.Dashboard(self.root / "designs", self.root / "inbox", cwd=self.root)
        self.srv = ui.make_server(self.db, "127.0.0.1", 0)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.tmp.cleanup()

    def req(self, method, path, body=None, headers=None, host=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        h = {"Host": host or f"127.0.0.1:{self.port}", **(headers or {})}
        c.request(method, path, body=body, headers=h)
        r = c.getresponse()
        data = r.read().decode("utf-8", "replace")
        c.close()
        return r.status, dict(r.getheaders()), data

    def test_home_and_design_pages(self):
        d = Design.init(self.root / "designs" / "m_x")
        (d.work / "results.json").write_text(json.dumps({
            "tests": [{"name": "t1", "status": "pass"}, {"name": "t2", "status": "fail"}],
            "coverage": {"metrics": {"line": {"percent": 97.5}, "block": {"percent": 90.0}}},
            "unreviewed_gates": ["G1_rules"]}), encoding="utf-8")
        (d.work / "report.json").write_text(json.dumps({"checks": {"by_status": {"PASS": 3, "FAIL": 1}}}),
                                            encoding="utf-8")
        (d.work / "report.md").write_text("# Report of m_x\n\nSee [formal](formal.md).\n", encoding="utf-8")
        (d.work / "formal.md").write_text("# Formal\n", encoding="utf-8")
        make_inbox(self.root, "new_ip")
        st, _h, page = self.req("GET", "/")
        self.assertEqual(st, 200)
        for s in ("m_x", "1/2", "3/4", "line 97.5 %", "new_ip", "not run", "Upload and run"):
            self.assertIn(s, page)
        st, _h, page = self.req("GET", "/d/m_x")
        self.assertEqual(st, 200)
        for s in ("Report of m_x", 'href="/d/m_x/f/work/formal.md"', "UNREVIEWED", "G4_signoff", "97.5 %"):
            self.assertIn(s, page)
        self.assertEqual(self.req("GET", "/d/m_x/f/work/formal.md")[0], 200)
        st, _h, page = self.req("GET", "/d/new_ip")
        self.assertIn('action="/run/new_ip"', page)
        st, _h, data = self.req("GET", "/api/designs")
        self.assertEqual(json.loads(data)["m_x"]["numbers"]["tests"], [1, 2])

    def test_paths_outside_are_not_served(self):
        Design.init(self.root / "designs" / "m_x")
        (self.root / "secret.md").write_text("x", encoding="utf-8")
        for p in ("/d/m_x/f/../../secret.md", "/d/m_x/f/..%2F..%2Fsecret.md", "/d/m_x/f/nnc_state.bin",
                  "/d/..%2Fx", "/d/nope"):
            self.assertEqual(self.req("GET", p)[0], 404, p)

    def test_only_local_requests(self):
        self.assertEqual(self.req("GET", "/", host="evil.example:80")[0], 403)
        st, _h, _ = self.req("POST", "/run/x", body=b"", headers={"Origin": "https://evil.example"})
        self.assertEqual(st, 403)

    def test_upload_then_run(self):
        ctype, body = multipart([("name", "up_ip"), ("top", "m_up"), ("go", "run"), ("backend", "replay"),
                                 ("gated", ""), ("spec", ("up_spec.md", b"# spec\n")),
                                 ("rtl", ("m_up.sv", b"module m_up; endmodule\n")),
                                 ("rtl", ("filelist.f", b"m_up.sv\n"))])
        with mock.patch.object(ui.subprocess, "Popen") as popen:
            popen.return_value.poll.return_value = None
            st, h, _ = self.req("POST", "/upload", body=body, headers={
                "Content-Type": ctype, "Origin": f"http://127.0.0.1:{self.port}"})
        self.assertEqual(st, 303)
        self.assertTrue(h["Location"].startswith("/d/up_ip"))
        f = self.root / "inbox" / "up_ip"
        self.assertEqual((f / "spec" / "up_spec.md").read_bytes(), b"# spec\n")
        self.assertTrue((f / "rtl" / "filelist.f").is_file())
        self.assertEqual(json.loads((f / "inbox.json").read_text(encoding="utf-8")), {"top": "m_up"})
        argv = popen.call_args[0][0]
        self.assertEqual(argv[argv.index("run") + 1], "up_ip")
        self.assertIn("replay", argv)
        self.assertNotIn("--gated", argv)

    def test_bad_uploads_are_refused(self):
        for fields in ([("name", "x1"), ("rtl", ("m.sv", b""))],                     # no specification
                       [("name", "x2"), ("spec", ("s.exe", b"")), ("rtl", ("m.sv", b""))],
                       [("name", "x3"), ("spec", ("s.md", b"")), ("rtl", ("../m.sv", b""))],
                       [("name", "../x"), ("spec", ("s.md", b"")), ("rtl", ("m.sv", b""))]):
            ctype, body = multipart(fields)
            st, h, _ = self.req("POST", "/upload", body=body, headers={"Content-Type": ctype})
            self.assertEqual(st, 303)
            self.assertIn("msg=error", h["Location"])
        self.assertFalse((self.root / "inbox").exists() and any((self.root / "inbox").iterdir()))


class RepoTest(unittest.TestCase):
    def test_the_committed_designs_render(self):
        db = ui.Dashboard(REPO / "designs", REPO / "inbox")
        page = ui.home(db).decode("utf-8")
        self.assertIn("sync_fifo", page)
        self.assertIn("<td>", ui.design_page(db, "sync_fifo").decode("utf-8"))


if __name__ == "__main__":
    unittest.main()

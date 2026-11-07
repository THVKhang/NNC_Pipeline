import json
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from nnc.agents import (
    AgentError,
    AgentTask,
    ClaudeCliBackend,
    ManualBackend,
    ManualTaskPending,
    build_sandbox,
    validate,
)

SCHEMA = {
    "type": "object",
    "required": ["rules"],
    "additionalProperties": False,
    "properties": {
        "rules": {"type": "array", "minItems": 1, "items": {
            "type": "object", "required": ["id", "quote"],
            "properties": {"id": {"type": "string", "pattern": r"^REQ-\d+$"}, "quote": {"type": "string", "minLength": 1}},
        }},
    },
}
GOOD = {"rules": [{"id": "REQ-1", "quote": "The bus width is 32 bits."}]}

# Stands in for the Claude CLI: checks the sandbox and the permission flags, then answers like `claude -p`.
FAKE_CLI = textwrap.dedent("""
    import json, os, sys
    argv = sys.argv[1:]
    stdin = sys.stdin.read()
    report = {"tools": argv[argv.index("--tools") + 1],
              "allowed": argv[argv.index("--allowedTools") + 1] if "--allowedTools" in argv else None,
              "seen": sorted(os.listdir(".")), "stdin": stdin}
    answer = json.loads(os.environ.get("FAKE_ANSWER", "null"))
    print(json.dumps({"is_error": False, "subtype": "success", "num_turns": 1, "total_cost_usd": 0.01,
                      "usage": {"output_tokens": 5}, "permission_denials": [], "result": "",
                      "structured_output": answer if answer is not None else report}))
""")


class SchemaTest(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate(GOOD, SCHEMA), [])

    def test_errors(self):
        self.assertTrue(validate({"rules": []}, SCHEMA))                                   # minItems
        self.assertTrue(validate({"rules": [{"id": "X-1", "quote": "q"}]}, SCHEMA))        # pattern
        self.assertTrue(validate({"rules": [{"id": "REQ-1"}]}, SCHEMA))                    # required
        self.assertTrue(validate({"rules": GOOD["rules"], "extra": 1}, SCHEMA))            # additionalProperties
        self.assertTrue(validate({"x": True}, {"type": "object", "properties": {"x": {"type": "integer"}}}))  # bool is not int


class SandboxTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        (self.tmp / "spec").mkdir()
        (self.tmp / "rtl").mkdir()
        self.spec = self.tmp / "spec" / "spec.md"
        self.spec.write_text("The bus width is 32 bits.\n", encoding="utf-8")
        self.rtl = self.tmp / "rtl" / "dut.sv"
        self.rtl.write_text("module dut; endmodule\n", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def task(self, **kw):
        base = dict(name="A1_extractor", instructions="Extract rules.", schema=SCHEMA,
                    inputs={"spec.md": self.spec}, forbidden=[self.tmp / "rtl"], tools=("Read", "Grep"))
        base.update(kw)
        return AgentTask(**base)

    def fake(self):
        fake = self.tmp / "fake_claude.py"
        fake.write_text(FAKE_CLI, encoding="utf-8")
        return ClaudeCliBackend([sys.executable, str(fake)], sandbox_parent=self.tmp)

    def test_sandbox_holds_only_task_and_inputs(self):
        sb = build_sandbox(self.task(), parent=self.tmp)
        self.assertEqual(sorted(p.name for p in sb.iterdir()), ["TASK.md", "spec.md"])

    def test_rtl_input_is_refused(self):
        with self.assertRaisesRegex(AgentError, "DUT isolation"):
            build_sandbox(self.task(inputs={"dut.sv": self.rtl}), parent=self.tmp)

    def test_escaping_input_name_is_refused(self):
        with self.assertRaises(AgentError):
            build_sandbox(self.task(inputs={"../spec.md": self.spec}), parent=self.tmp)

    def test_write_tools_are_refused(self):
        with self.assertRaisesRegex(AgentError, "read-only"):
            build_sandbox(self.task(tools=("Read", "Bash")), parent=self.tmp)

    def test_inline_task_cannot_take_files(self):
        with self.assertRaisesRegex(AgentError, "inline"):
            self.fake().run(self.task(tools=()), self.tmp / "logs")

    def test_sandbox_mode_runs_in_sandbox_with_scoped_tools(self):
        schema = {"type": "object", "required": ["tools", "seen"]}
        res = self.fake().run(self.task(schema=schema), self.tmp / "logs")
        self.assertEqual(res.output["seen"], ["TASK.md", "spec.md"])
        self.assertEqual(res.output["tools"], "Read,Grep")
        self.assertEqual(res.output["allowed"], "Read(./**) Grep(./**)")
        self.assertIn("TASK.md", res.output["stdin"])
        self.assertTrue(res.log_path.is_file())
        self.assertEqual(res.cost_usd, 0.01)
        self.assertFalse(any(p.name.startswith("nnc_") for p in self.tmp.iterdir()))  # sandbox removed

    def test_inline_mode_has_no_tools_and_sends_content_on_stdin(self):
        schema = {"type": "object", "required": ["tools"]}
        res = self.fake().run(self.task(tools=(), inputs={}, schema=schema, instructions="[s1] text"),
                              self.tmp / "logs")
        self.assertEqual(res.output["tools"], "")
        self.assertIsNone(res.output["allowed"])
        self.assertEqual(res.output["stdin"], "[s1] text")
        self.assertEqual(res.usage, {"output_tokens": 5})

    def test_cli_backend_rejects_answer_that_violates_schema(self):
        os.environ["FAKE_ANSWER"] = json.dumps({"rules": []})
        try:
            with self.assertRaisesRegex(AgentError, "violates the schema"):
                self.fake().run(self.task(), self.tmp / "logs")
        finally:
            del os.environ["FAKE_ANSWER"]

    def test_manual_backend_round_trip_and_stale_answer(self):
        backend = ManualBackend(self.tmp / "manual")
        with self.assertRaises(ManualTaskPending) as cm:
            backend.run(self.task(), self.tmp / "logs")
        task_dir = cm.exception.task_dir
        self.assertTrue((task_dir / "TASK.md").is_file())
        self.assertTrue((task_dir / "inputs" / "spec.md").is_file())

        (task_dir / "output.json").write_text(json.dumps(GOOD), encoding="utf-8")
        self.assertEqual(backend.run(self.task(), self.tmp / "logs").output, GOOD)

        self.spec.write_text("The bus width is 64 bits.\n", encoding="utf-8")  # input changed
        with self.assertRaises(ManualTaskPending):
            backend.run(self.task(), self.tmp / "logs")
        self.assertTrue((task_dir / "output.stale.json").is_file())
        self.assertFalse((task_dir / "output.json").exists())


if __name__ == "__main__":
    unittest.main()

"""Agent backends: how one agent step is executed.

Every agent step is an AgentTask: instructions, the JSON Schema of the answer and, for a tool-using
agent, the files it may read. Information isolation (principle PR-1 of docs/ARCHITECTURE.md) is
decided by code, never by the prompt. Two modes:

* inline (task.tools empty) - the worker mode. All content is in the instructions, sent on stdin;
  the agent gets NO tools (`--tools ""`), so it cannot read anything it was not given. This is
  also the cheapest mode: with a short custom system prompt the fixed cost of one call is about
  1.5k tokens instead of the ~20k of the default Claude Code prompt and tool set (measured
  2026-11-07: US$0.0071 vs US$0.33 per trivial Sonnet call).
* sandbox (task.tools set) - the deep-agent mode. The orchestrator copies exactly the allowed
  files into a fresh folder outside the repository and runs the agent there with only the named
  read-only tools and the path-scoped permissions `Read(./**)` etc. A plain `Read` permission
  lets the agent read files outside the sandbox (verified with Claude Code 2.1.319); the scoped
  rule denies them and reports each attempt in `permission_denials`, which is logged.

ManualBackend writes the same task to a folder for a human (or an interactive Claude Code session)
and collects `output.json` from it on the next run. Every backend validates the answer against the
schema and writes a JSON log of the step with its token usage and cost.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from nnc.agents.schema import validate

TASK_FILE = "TASK.md"
SANDBOX_PROMPT = (
    f"Read {TASK_FILE} in the current directory and carry out the task it describes. "
    "Use only the files in the current directory. Return the answer in the required JSON structure."
)
DEFAULT_SYSTEM_PROMPT = (
    "You are a verification engineer's assistant. Work only from the material you are given. "
    "Never invent facts. Return the answer in the required JSON structure."
)
READ_ONLY_TOOLS = ("Read", "Glob", "Grep")
# Flags that strip what an agent step does not need: MCP servers, skills/commands, saved sessions.
LEAN_FLAGS = ("--strict-mcp-config", "--disable-slash-commands", "--no-session-persistence")


class AgentError(Exception):
    """The agent step failed or returned an invalid answer."""


class ManualTaskPending(Exception):
    """A manual task was written and waits for output.json."""

    def __init__(self, task_dir: Path):
        super().__init__(f"manual task waiting for {task_dir / 'output.json'}")
        self.task_dir = task_dir


@dataclass
class AgentTask:
    name: str                          # step name, for example "A1_extractor"
    instructions: str                  # the user prompt (inline) or the body of TASK.md (sandbox)
    schema: dict                       # JSON Schema of the answer
    inputs: dict[str, Path] = field(default_factory=dict)  # sandbox-relative name -> source file
    forbidden: Sequence[Path] = ()     # folders whose files must never be inputs (the DUT)
    tools: Sequence[str] = ()          # empty: inline worker; else read-only tools of a sandbox agent
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    max_turns: int = 30
    model: str | None = None

    def fingerprint(self) -> str:
        """Hash of everything that defines the task (cache key, stale-answer detection)."""
        h = hashlib.sha256()
        for part in (self.instructions, self.system_prompt, json.dumps(self.schema, sort_keys=True),
                     ",".join(self.tools), self.model or ""):
            h.update(part.encode("utf-8"))
            h.update(b"\0")
        for name in sorted(self.inputs):
            h.update(name.encode("utf-8"))
            h.update(hashlib.sha256(Path(self.inputs[name]).read_bytes()).digest())
        return h.hexdigest()


@dataclass
class AgentResult:
    output: dict
    backend: str
    log_path: Path | None
    cost_usd: float | None = None
    usage: dict = field(default_factory=dict)
    permission_denials: list = field(default_factory=list)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _check_inputs(task: AgentTask) -> None:
    """Refuse any input that is missing, escapes the sandbox, or lies inside a forbidden folder."""
    if task.inputs and not task.tools:
        raise AgentError(f"{task.name}: an inline task has no tools to read input files; put the content in the instructions")
    unknown = [t for t in task.tools if t not in READ_ONLY_TOOLS]
    if unknown:
        raise AgentError(f"{task.name}: only read-only tools are allowed, not {unknown}")
    forbidden = [Path(f).resolve() for f in task.forbidden]
    for name, src in task.inputs.items():
        rel = Path(name)
        if rel.is_absolute() or ".." in rel.parts:
            raise AgentError(f"{task.name}: input name '{name}' must be a relative path inside the sandbox")
        if rel.as_posix() == TASK_FILE:
            raise AgentError(f"{task.name}: input name '{TASK_FILE}' is reserved")
        src_r = Path(src).resolve()
        if not src_r.is_file():
            raise AgentError(f"{task.name}: input file not found: {src}")
        for f in forbidden:
            if src_r == f or f in src_r.parents:
                raise AgentError(f"{task.name}: input {src} is inside forbidden folder {f} (DUT isolation)")


def build_sandbox(task: AgentTask, parent: Path | None = None) -> Path:
    """Create a fresh folder holding TASK.md and copies of the allowed inputs only."""
    _check_inputs(task)
    sandbox = Path(tempfile.mkdtemp(prefix=f"nnc_{task.name}_", dir=parent))
    (sandbox / TASK_FILE).write_text(task.instructions, encoding="utf-8")
    for name, src in task.inputs.items():
        dst = sandbox / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    return sandbox


def _write_log(log_dir: Path, task: AgentTask, record: dict) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = log_dir / f"{task.name}_{stamp}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


class ClaudeCliBackend:
    """Run an agent step with Claude Code in headless mode (uses the logged-in Claude Code account)."""

    name = "claude-cli"

    def __init__(self, command: Sequence[str], timeout_s: int = 1800, keep_sandbox: bool = False,
                 sandbox_parent: Path | None = None):
        self.command = list(command)
        self.timeout_s = timeout_s
        self.keep_sandbox = keep_sandbox
        self.sandbox_parent = sandbox_parent

    def build_argv(self, task: AgentTask) -> list[str]:
        argv = self.command + [
            "-p", "--output-format", "json",
            "--json-schema", json.dumps(task.schema),
            "--system-prompt", task.system_prompt,
            "--max-turns", str(task.max_turns),
            *LEAN_FLAGS,
        ]
        if task.tools:
            argv += ["--tools", ",".join(task.tools),
                     "--allowedTools", " ".join(f"{t}(./**)" for t in task.tools)]
        else:
            argv += ["--tools", ""]
        if task.model:
            argv += ["--model", task.model]
        return argv

    def run(self, task: AgentTask, log_dir: Path) -> AgentResult:
        _check_inputs(task)
        sandbox = build_sandbox(task, self.sandbox_parent) if task.tools else None
        prompt = SANDBOX_PROMPT if task.tools else task.instructions
        record: dict = {"task": task.name, "backend": self.name, "mode": "sandbox" if task.tools else "inline",
                        "model": task.model, "started": _now(), "inputs": sorted(task.inputs),
                        "prompt_chars": len(task.instructions)}
        try:
            t0 = time.monotonic()
            try:
                proc = subprocess.run(
                    self.build_argv(task), cwd=sandbox, input=prompt, capture_output=True, text=True,
                    encoding="utf-8", errors="replace", timeout=self.timeout_s,
                )
            except subprocess.TimeoutExpired as e:
                record["error"] = f"timeout after {self.timeout_s} s"
                _write_log(log_dir, task, record)
                raise AgentError(f"{task.name}: {record['error']}") from e
            record["duration_s"] = round(time.monotonic() - t0, 1)
            record["returncode"] = proc.returncode
            record["stderr"] = proc.stderr[-4000:]
            try:
                reply = json.loads(proc.stdout)
            except json.JSONDecodeError:
                record["stdout"] = proc.stdout[-4000:]
                log = _write_log(log_dir, task, record)
                raise AgentError(f"{task.name}: Claude CLI returned no JSON (rc={proc.returncode}); see {log}")
            denials = reply.get("permission_denials") or []
            output = reply.get("structured_output")
            record.update({
                "is_error": reply.get("is_error"), "subtype": reply.get("subtype"),
                "num_turns": reply.get("num_turns"), "cost_usd": reply.get("total_cost_usd"),
                "usage": reply.get("usage") or {}, "permission_denials": denials, "output": output,
            })
            if proc.returncode != 0 or reply.get("is_error") or not isinstance(output, dict):
                record["result_text"] = str(reply.get("result"))[-4000:]
                log = _write_log(log_dir, task, record)
                raise AgentError(f"{task.name}: agent failed ({reply.get('subtype')}); see {log}")
            errors = validate(output, task.schema)
            if errors:
                record["schema_errors"] = errors
                log = _write_log(log_dir, task, record)
                raise AgentError(f"{task.name}: answer violates the schema ({len(errors)} errors); see {log}")
            log = _write_log(log_dir, task, record)
            return AgentResult(output, self.name, log, reply.get("total_cost_usd"), record["usage"], denials)
        finally:
            if sandbox is not None and not self.keep_sandbox:
                shutil.rmtree(sandbox, ignore_errors=True)


class ManualBackend:
    """Write the task for a human; collect and validate output.json on a later run."""

    name = "manual"

    def __init__(self, tasks_root: Path):
        self.tasks_root = Path(tasks_root)

    def run(self, task: AgentTask, log_dir: Path) -> AgentResult:
        _check_inputs(task)
        task_dir = self.tasks_root / task.name
        fp = task.fingerprint()
        fp_file = task_dir / "fingerprint.txt"
        out_file = task_dir / "output.json"
        same_task = fp_file.is_file() and fp_file.read_text(encoding="utf-8").strip() == fp
        if same_task and out_file.is_file():
            try:
                output = json.loads(out_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                raise AgentError(f"{task.name}: {out_file} is not valid JSON: {e}") from e
            errors = validate(output, task.schema)
            record = {"task": task.name, "backend": self.name, "collected": _now(),
                      "output": output, "schema_errors": errors}
            log = _write_log(log_dir, task, record)
            if errors:
                raise AgentError(f"{task.name}: {out_file} violates the schema: " + "; ".join(errors[:5]))
            return AgentResult(output if isinstance(output, dict) else {}, self.name, log)
        if not same_task:
            if out_file.is_file():  # answer to an older version of the task: keep it, never use it
                out_file.replace(task_dir / "output.stale.json")
            if (task_dir / "inputs").is_dir():
                shutil.rmtree(task_dir / "inputs")
            task_dir.mkdir(parents=True, exist_ok=True)
            (task_dir / TASK_FILE).write_text(task.instructions, encoding="utf-8")
            (task_dir / "schema.json").write_text(json.dumps(task.schema, indent=2) + "\n", encoding="utf-8")
            for name, src in task.inputs.items():
                dst = task_dir / "inputs" / name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
            fp_file.write_text(fp + "\n", encoding="utf-8")
        raise ManualTaskPending(task_dir)

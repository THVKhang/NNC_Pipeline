"""Shared runtime of the agent stages: answer cache, parallel execution, usage accounting."""
from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from nnc.agents.backend import AgentResult, AgentTask, ClaudeCliBackend, ManualBackend
from nnc.tools import find_claude

USAGE_KEYS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


class BudgetExceeded(RuntimeError):
    """The cost cap of a run (`nnc run --max-cost`) is reached: no new model call starts."""


class Budget:
    """What the model calls of one run cost, and an optional cap (ROADMAP 26.2). Checked before each call that
    is not answered from the cache: once the spending reaches the cap, no new call starts. Calls already
    running finish (with --workers 4, up to four), so a run can end a little above the cap."""

    def __init__(self, limit_usd: float | None = None):
        if limit_usd is not None and limit_usd < 0:
            raise ValueError("the cost cap must be 0 or more")
        self.limit = limit_usd
        self.spent = 0.0
        self.calls = 0
        self.refused = 0
        self._lock = threading.Lock()

    @property
    def exceeded(self) -> bool:
        return self.refused > 0

    def before_call(self, name: str) -> None:
        with self._lock:
            if self.limit is not None and self.spent >= self.limit:
                self.refused += 1
                raise BudgetExceeded(f"{name}: the cost cap of {self.limit:.2f} USD is reached "
                                     f"({self.spent:.2f} USD spent); no new agent call")

    def add(self, cost_usd: float | None) -> None:
        with self._lock:
            self.spent += cost_usd or 0.0
            self.calls += 1


class CachedBackend:
    """Reuse an earlier answer to the identical task (same content, prompt, schema and model)."""

    def __init__(self, backend, cache_dir: Path, budget: Budget | None = None):
        self.backend = backend
        self.cache_dir = Path(cache_dir)
        self.name = f"cached-{backend.name}"
        self.budget = budget

    def run(self, task: AgentTask, log_dir: Path) -> AgentResult:
        path = self.cache_dir / f"{task.fingerprint()}.json"
        if path.is_file():
            return AgentResult(json.loads(path.read_text(encoding="utf-8")), "cache", None, 0.0, {})
        if self.budget is not None:
            self.budget.before_call(task.name)
        try:
            res = self.backend.run(task, log_dir)
        except Exception as e:  # a failed call may still have cost (usage limit mid-answer, invalid answer)
            if self.budget is not None:
                self.budget.add(getattr(e, "cost_usd", None))
            raise
        if self.budget is not None:
            self.budget.add(res.cost_usd)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(res.output, ensure_ascii=False) + "\n", encoding="utf-8")
        return res


class ReplayMiss(RuntimeError):
    """`--backend replay` met a task that has no answer in the cache: running it would call a model."""


class ReplayBackend:
    """Behind the cache with `--backend replay`: every task must be answered from the cache. A task that is
    not there stops the flow instead of calling a model, so a replay never costs tokens."""

    name = "replay"

    def run(self, task: AgentTask, log_dir: Path) -> AgentResult:
        raise ReplayMiss(f"{task.name}: no cached answer for this task (fingerprint {task.fingerprint()[:12]}); "
                         "a replay never calls a model. Its inputs or prompt differ from the recorded run.")


def make_backend(work: Path, kind: str = "claude", timeout_s: int = 900, budget: Budget | None = None):
    """The backend of a design: Claude Code CLI, manual, or replay (cache only), always behind the answer
    cache; `budget` counts (and may cap) what the calls cost."""
    if kind == "manual":
        inner = ManualBackend(work / "manual")
    elif kind == "replay":
        inner = ReplayBackend()
    else:
        claude = find_claude()
        if not claude:
            raise RuntimeError("Claude Code CLI not found; use --backend manual or set NNC_CLAUDE_BIN")
        inner = ClaudeCliBackend([claude], timeout_s=timeout_s)
    return CachedBackend(inner, work / "cache" / "agents", budget)


@dataclass
class Usage:
    calls: int = 0
    cached: int = 0
    cost_usd: float = 0.0
    tokens: dict = field(default_factory=lambda: {k: 0 for k in USAGE_KEYS})

    def add(self, res: AgentResult | None) -> None:
        if res is None:
            return
        self.calls += 1
        self.cached += res.backend == "cache"
        self.cost_usd += res.cost_usd or 0.0
        for k in USAGE_KEYS:
            self.tokens[k] += int(res.usage.get(k) or 0)

    def merge(self, other: "Usage") -> None:
        self.calls += other.calls
        self.cached += other.cached
        self.cost_usd += other.cost_usd
        for k in USAGE_KEYS:
            self.tokens[k] += other.tokens.get(k, 0)

    def as_dict(self) -> dict:
        return {"calls": self.calls, "cached": self.cached, "cost_usd": round(self.cost_usd, 4), **self.tokens}

    def line(self) -> str:
        t = self.tokens
        tin = t["input_tokens"] + t["cache_creation_input_tokens"] + t["cache_read_input_tokens"]
        return (f"calls: {self.calls} ({self.cached} from cache)  cost US${self.cost_usd:.4f}  "
                f"tokens in {tin} out {t['output_tokens']}")


@dataclass
class Outcome:
    key: object
    task: AgentTask
    result: AgentResult | None
    error: str | None


def run_parallel(backend, items: list[tuple[object, AgentTask]], log_dir: Path, workers: int = 4) -> list[Outcome]:
    """Run tasks concurrently; one failed task never loses the others."""
    def one(item):
        key, task = item
        try:
            return Outcome(key, task, backend.run(task, log_dir), None)
        except Exception as e:  # noqa: BLE001
            return Outcome(key, task, None, f"{type(e).__name__}: {e}")
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        return list(pool.map(one, items))


def run_one(backend, task: AgentTask, log_dir: Path) -> AgentResult:
    return backend.run(task, log_dir)

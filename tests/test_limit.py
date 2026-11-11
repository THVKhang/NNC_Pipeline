"""Usage-limit handling of the Claude CLI backend: parse the reset time, wait, call again."""
import os
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from nnc.agents import backend as be

TASK = SimpleNamespace(name="A7_tests")
MSG = "You've hit your 5-hour limit · resets 6:50am (Asia/Ho_Chi_Minh)"


class ResetTimeTest(unittest.TestCase):
    def test_parse(self):
        now = datetime(2026, 11, 11, 5, 0)
        self.assertEqual(be.limit_reset_wait(MSG, now), 110 * 60 + 60)
        self.assertEqual(be.limit_reset_wait("You've hit your limit · resets 11pm", now), 18 * 3600 + 60)
        self.assertEqual(be.limit_reset_wait("You've hit your limit · resets 12am", now), 19 * 3600 + 60)
        # a time already past today means tomorrow
        self.assertEqual(be.limit_reset_wait(MSG, datetime(2026, 11, 11, 7, 0)), (23 * 60 + 50) * 60 + 60)
        self.assertIsNone(be.limit_reset_wait("agent failed: schema", now))
        self.assertIsNone(be.limit_reset_wait("", now))


class WaitLoopTest(unittest.TestCase):
    def _backend(self, outcomes):
        b = be.ClaudeCliBackend(["claude"])
        calls = iter(outcomes)

        def once(task, log_dir):
            o = next(calls)
            if isinstance(o, Exception):
                raise o
            return o
        b._run_once = once
        return b

    def test_waits_then_succeeds(self):
        b = self._backend([be.UsageLimitReached("limit", 120.0), "answer"])
        with mock.patch.object(be.time, "sleep") as sleep, mock.patch.dict(os.environ, {"NNC_LIMIT_WAIT": "3600"}):
            self.assertEqual(b.run(TASK, Path(".")), "answer")
        sleep.assert_called_once_with(120.0)

    def test_gives_up_beyond_budget(self):
        b = self._backend([be.UsageLimitReached("limit", 7200.0)])
        with mock.patch.object(be.time, "sleep") as sleep, mock.patch.dict(os.environ, {"NNC_LIMIT_WAIT": "3600"}):
            with self.assertRaises(be.UsageLimitReached):
                b.run(TASK, Path("."))
        sleep.assert_not_called()

    def test_disabled(self):
        b = self._backend([be.UsageLimitReached("limit", 60.0)])
        with mock.patch.object(be.time, "sleep"), mock.patch.dict(os.environ, {"NNC_LIMIT_WAIT": "0"}):
            with self.assertRaises(be.UsageLimitReached):
                b.run(TASK, Path("."))

    def test_limit_error_is_an_agent_error(self):
        self.assertTrue(issubclass(be.UsageLimitReached, be.AgentError))


if __name__ == "__main__":
    unittest.main()

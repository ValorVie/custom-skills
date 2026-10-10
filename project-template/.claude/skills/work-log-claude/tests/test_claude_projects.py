"""Run: uv run --python 3.14 python -m unittest discover -s .claude/skills/work-log-claude/tests"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import work_log_claude  # noqa: E402  (switches Codex inputs off)

CODEX_FIXTURES = work_log_claude.CODEX_SKILL / "tests/fixtures"
START = datetime(2026, 9, 1, tzinfo=timezone.utc)
END = datetime(2026, 9, 30, tzinfo=timezone.utc)


def _row(kind: str, ts: str, content, **extra) -> dict:
    return {"type": kind, "timestamp": ts, "sessionId": "main-1", "entrypoint": "cli",
            "message": {"role": kind, "content": content}, **extra}


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


class ClaudeProjectsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = self.root = Path(self.tmp.name)
        proj = root / "projects/-repo-a"
        _write(proj / "main-1.jsonl", [
            _row("user", "2026-09-10T01:00:00Z", "整理工作日誌", cwd="/repo/a"),
            _row("assistant", "2026-09-10T01:01:00Z",
                 [{"type": "text", "text": "開始"}, {"type": "tool_use", "name": "Bash", "input": {}}],
                 cwd="/repo/a/sub"),
            _row("user", "2026-09-10T01:02:00Z",
                 [{"type": "tool_result", "content": "not a prompt"}], cwd="/repo/a/sub"),
            _row("user", "2026-09-10T01:03:00Z", "<command-name>/x</command-name>", cwd="/repo/a"),
            _row("user", "2026-09-10T01:05:00Z", "\n<pasted_content id=\"1\">\n貼上的需求\n</pasted_content>", cwd="/repo/a"),
            _row("assistant", "2026-09-10T01:10:00Z", [{"type": "text", "text": "已完成"}], cwd="/repo/a"),
            _row("user", "2026-10-10T01:00:00Z", "out of window", cwd="/repo/a"),
        ])
        _write(proj / "main-1/subagents/agent-x.jsonl", [
            _row("user", "2026-09-10T01:04:00Z", "subagent task", cwd="/repo/a"),
            _row("assistant", "2026-09-10T01:08:00Z", [{"type": "text", "text": "done"}], cwd="/repo/a"),
        ])
        _write(proj / "sdk-1.jsonl", [
            {**_row("user", "2026-09-10T02:00:00Z", "You are a memory relevance compressor", cwd="/repo/a"),
             "entrypoint": "sdk-cli", "sessionId": "sdk-1"},
        ])
        _write(root / "projects/-home-x--claude-mem-observer-sessions/o.jsonl", [
            _row("user", "2026-09-10T03:00:00Z", "observer", cwd="/obs"),
        ])

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_codex_fixture_is_ignored(self) -> None:
        day_start = datetime(2026, 3, 10, 16, tzinfo=timezone.utc)
        day_end = datetime(2026, 3, 11, 16, tzinfo=timezone.utc)
        report = work_log_claude.wlp.build_report(
            day_start, day_end, "Asia/Taipei",
            CODEX_FIXTURES / "claude_sample", CODEX_FIXTURES / "codex_sample")
        self.assertEqual(report["summary"]["sources"], ["claude"])
        self.assertEqual({p["short_name"] for p in report["projects"].values()}, {"repo-b"})
        self.assertEqual(report["codex_sessions"], [])

    def test_build_report_is_claude_only(self) -> None:
        report = work_log_claude.wlp.build_report(START, END, "Asia/Taipei", self.root, self.root / "no-codex")
        self.assertEqual(report["summary"]["sources"], ["claude"])
        self.assertEqual([s["session_id"] for s in report["sessions"]], ["main-1"])
        self.assertEqual(report["sessions"][0]["first_prompt"], "整理工作日誌")
        self.assertEqual(report["sessions"][0]["tools_used"], {"Bash": 1})
        self.assertEqual(len(report["subagent_sessions"]), 1)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from source_claude import load_claude_events  # noqa: E402

START = datetime(2026, 9, 1, tzinfo=timezone.utc)
END = datetime(2026, 9, 30, tzinfo=timezone.utc)


def _row(kind: str, ts: str, content, **extra) -> dict:
    return {"type": kind, "timestamp": ts, "sessionId": "main-1", "entrypoint": "cli",
            "message": {"role": kind, "content": content}, **extra}


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


class ClaudeSourceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = self.root = Path(self.tmp.name)
        proj = root / "projects/-repo-a"
        _write(proj / "main-1.jsonl", [
            {"type": "attachment", "timestamp": "2026-09-10T00:59:00Z", "cwd": "/repo/a", "entrypoint": "cli"},
            _row("user", "2026-09-10T01:00:00Z", "整理工作日誌", cwd="/repo/a", world_state="x" * 100_000),
            _row("assistant", "2026-09-10T01:01:00Z",
                 [{"type": "text", "text": "開始"}, {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}],
                 cwd="/repo/a/sub"),
            _row("user", "2026-09-10T01:02:00Z",
                 [{"type": "tool_result", "content": "not a prompt"}], cwd="/repo/a/sub"),
            _row("user", "2026-09-10T01:03:00Z", "<command-name>/x</command-name>", cwd="/repo/a"),
            _row("user", "2026-09-10T01:05:00Z", "\n<pasted_content id=\"1\">\n貼上的需求\n</pasted_content>", cwd="/repo/a"),
            _row("user", "2026-09-10T01:06:00Z", "hook text", cwd="/repo/a", isMeta=True),
            _row("assistant", "2026-09-10T01:10:00Z", [{"type": "text", "text": "已完成"}], cwd="/repo/a"),
            _row("user", "2026-10-10T01:00:00Z", "out of window", cwd="/repo/a"),
        ])
        _write(proj / "main-1/subagents/agent-x.jsonl", [
            _row("user", "2026-09-10T01:04:00Z", "subagent task", cwd="/repo/a"),
        ])
        _write(proj / "sdk-1.jsonl", [
            {**_row("user", "2026-09-10T02:00:00Z", "You are a memory relevance compressor", cwd="/repo/a"),
             "entrypoint": "sdk-cli", "sessionId": "sdk-1"},
        ])
        _write(root / "projects/-home-x--claude-mem-observer-sessions/o.jsonl", [
            _row("user", "2026-09-10T03:00:00Z", "observer", cwd="/obs"),
        ])
        # Old non-Claude-Code layouts must be ignored.
        _write(root / "transcripts/ses_old.jsonl", [
            {"type": "user", "timestamp": "2026-09-10T04:00:00Z", "content": "opencode transcript"},
        ])

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_reads_current_projects_layout(self) -> None:
        events = load_claude_events(self.root, START, END)
        main = [e for e in events if e["session_id"] == "main-1"]
        self.assertEqual(len(main), 7)  # attachment and out-of-window rows dropped
        self.assertEqual({e["project_path"] for e in events}, {"/repo/a"})  # first cwd, not later cd
        self.assertEqual({e["confidence"] for e in events}, {"high"})
        self.assertEqual(
            [e["text"] for e in main if e["event_type"] == "user"],
            ["整理工作日誌", None, None, "<pasted_content id=\"1\">\n貼上的需求\n</pasted_content>", None],
        )
        self.assertEqual(main[1]["raw"]["message"]["content"], [{"type": "tool_use", "name": "Bash"}])

    def test_subagents_are_separate_sessions(self) -> None:
        sub = [e for e in load_claude_events(self.root, START, END) if e["is_subagent"]]
        self.assertEqual([e["session_id"] for e in sub], ["main-1/agent-x"])

    def test_skips_sdk_observer_and_old_layouts(self) -> None:
        paths = {e["evidence_path"] for e in load_claude_events(self.root, START, END)}
        self.assertFalse(any(m in p for p in paths for m in ("sdk-1", "observer", "transcripts")))

    def test_raw_is_compact(self) -> None:
        first = load_claude_events(self.root, START, END)[0]
        self.assertLess(len(json.dumps(first["raw"])), 1024)

    def test_missing_projects_dir_returns_empty(self) -> None:
        self.assertEqual(load_claude_events(self.root / "nope"), [])


if __name__ == "__main__":
    unittest.main()

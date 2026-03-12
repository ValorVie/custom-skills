from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from wl_parser.work_log_parser import _emit_project_bundles  # type: ignore  # noqa: E402
from wl_parser.work_log_parser import build_report, parse_time_shortcut  # type: ignore  # noqa: E402


class ParserTest(unittest.TestCase):
    @patch("wl_parser.work_log_parser.collect_git_data")
    @patch("wl_parser.work_log_parser.load_claude_events")
    @patch("wl_parser.work_log_parser.load_codex_events")
    def test_build_report_exposes_project_level_schema(
        self,
        mock_load_codex_events,
        mock_load_claude_events,
        mock_collect_git_data,
    ) -> None:
        mock_load_codex_events.return_value = [
            {
                "tool": "codex",
                "session_id": "codex-1",
                "project_path": "/tmp/repo-a",
                "cwd": "/tmp/repo-a",
                "timestamp": "2026-03-11T09:00:00+08:00",
                "event_type": "response_item",
                "title": "user",
                "text": "今天完成 parser 與報告輸出",
                "evidence_path": "/tmp/codex-session.jsonl",
                "confidence": "high",
                "raw": {"payload": {"role": "user"}},
            },
            {
                "tool": "codex",
                "session_id": "codex-1",
                "project_path": "/tmp/repo-a",
                "cwd": "/tmp/repo-a",
                "timestamp": "2026-03-11T09:25:00+08:00",
                "event_type": "response_item",
                "title": "assistant",
                "text": "已完成 parser，接下來整理 tests",
                "evidence_path": "/tmp/codex-session.jsonl",
                "confidence": "high",
                "raw": {"payload": {"role": "assistant"}},
            },
        ]
        mock_load_claude_events.return_value = [
            {
                "tool": "claude",
                "session_id": "claude-1",
                "project_path": "/tmp/repo-b",
                "cwd": None,
                "timestamp": "2026-03-11T11:00:00+08:00",
                "event_type": "user",
                "title": "規劃明天的週報匯總",
                "text": "規劃明天的週報匯總",
                "evidence_path": "/tmp/claude-session.jsonl",
                "confidence": "high",
                "raw": {"type": "user"},
            },
            {
                "tool": "claude",
                "session_id": "claude-1",
                "project_path": "/tmp/repo-b",
                "cwd": None,
                "timestamp": "2026-03-11T11:20:00+08:00",
                "event_type": "assistant",
                "title": "下一步整理 repo-b 的測試與 blocking issues",
                "text": "下一步整理 repo-b 的測試與 blocking issues",
                "evidence_path": "/tmp/claude-session.jsonl",
                "confidence": "high",
                "raw": {"type": "assistant"},
            },
        ]

        def _git_data(project_path: str, start: datetime, end: datetime, max_commits: int = 50):
            if project_path == "/tmp/repo-a":
                return [
                    {
                        "hash": "abc1234",
                        "full_hash": "abc1234567890",
                        "message": "功能(report): 新增工作日誌 parser",
                        "date": "2026-03-11 10:00:00 +0800",
                        "files_changed": 2,
                        "insertions": 30,
                        "deletions": 5,
                        "files": ["parser.py", "tests/test_parser.py"],
                    }
                ]
            return []

        mock_collect_git_data.side_effect = _git_data

        report = build_report(
            start=datetime(2026, 3, 11, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 3, 11, 23, 59, tzinfo=timezone.utc),
            timezone_name="Asia/Taipei",
            claude_home=Path("/tmp/claude"),
            codex_home=Path("/tmp/codex"),
            project_filter=None,
        )

        self.assertIn("projects", report)
        self.assertEqual(report["summary"]["project_count"], 2)

        repo_a = report["projects"]["/tmp/repo-a"]
        self.assertEqual(repo_a["short_name"], "repo-a")
        self.assertEqual(repo_a["session_count"], 1)
        self.assertGreaterEqual(repo_a["duration_minutes"], 25)
        self.assertEqual(repo_a["git_commits"][0]["hash"], "abc1234")
        self.assertIn("session_hints", repo_a)
        self.assertIn("今天完成 parser 與報告輸出", repo_a["session_hints"])

        repo_b = report["projects"]["/tmp/repo-b"]
        self.assertEqual(repo_b["short_name"], "repo-b")
        self.assertEqual(repo_b["git_commits"], [])
        self.assertIn("規劃明天的週報匯總", repo_b["session_hints"])

    def test_parse_time_shortcut_this_week(self) -> None:
        start, end = parse_time_shortcut("this-week", "Asia/Taipei")
        self.assertEqual(start.weekday(), 0)
        self.assertGreater(end, start)

    @patch("wl_parser.work_log_parser.collect_git_data")
    @patch("wl_parser.work_log_parser.load_claude_events")
    @patch("wl_parser.work_log_parser.load_codex_events")
    def test_build_report_filters_noise_hints_and_disambiguates_display_names(
        self,
        mock_load_codex_events,
        mock_load_claude_events,
        mock_collect_git_data,
    ) -> None:
        mock_collect_git_data.return_value = []
        mock_load_claude_events.return_value = [
            {
                "tool": "claude",
                "session_id": "claude-1",
                "project_path": "/Users/arlen/repos/work/custom-skills",
                "cwd": None,
                "timestamp": "2026-03-11T11:00:00+08:00",
                "event_type": "user",
                "text": "# AGENTS.md instructions\n整理 custom-skills 文檔與規則",
                "evidence_path": "/tmp/claude-1.jsonl",
                "confidence": "high",
                "raw": {"type": "user"},
            },
            {
                "tool": "claude",
                "session_id": "claude-1",
                "project_path": "/Users/arlen/repos/work/custom-skills",
                "cwd": None,
                "timestamp": "2026-03-11T11:20:00+08:00",
                "event_type": "assistant",
                "text": "Launching skill: brainstorming\n整理 skill 觸發與文件",
                "evidence_path": "/tmp/claude-1.jsonl",
                "confidence": "high",
                "raw": {"type": "assistant"},
            },
            {
                "tool": "claude",
                "session_id": "claude-2",
                "project_path": "/Users/arlen/archive/custom-skills",
                "cwd": None,
                "timestamp": "2026-03-11T12:00:00+08:00",
                "event_type": "user",
                "text": "整理 archive 的 custom-skills 測試樣本",
                "evidence_path": "/tmp/claude-2.jsonl",
                "confidence": "high",
                "raw": {"type": "user"},
            },
            {
                "tool": "claude",
                "session_id": "claude-2",
                "project_path": "/Users/arlen/archive/custom-skills",
                "cwd": None,
                "timestamp": "2026-03-11T12:25:00+08:00",
                "event_type": "assistant",
                "text": "整理 archive custom-skills 的 fixture 與 smoke tests",
                "evidence_path": "/tmp/claude-2.jsonl",
                "confidence": "high",
                "raw": {"type": "assistant"},
            },
        ]
        mock_load_codex_events.return_value = []

        report = build_report(
            start=datetime(2026, 3, 11, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 3, 11, 23, 59, tzinfo=timezone.utc),
            timezone_name="Asia/Taipei",
            claude_home=Path("/tmp/claude"),
            codex_home=Path("/tmp/codex"),
            project_filter=None,
        )

        first = report["projects"]["/Users/arlen/repos/work/custom-skills"]
        second = report["projects"]["/Users/arlen/archive/custom-skills"]
        self.assertEqual(first["session_hints"], ["整理 custom-skills 文檔與規則", "整理 skill 觸發與文件"])
        self.assertEqual(
            second["session_hints"],
            [
                "整理 archive 的 custom-skills 測試樣本",
                "整理 archive custom-skills 的 fixture 與 smoke tests",
            ],
        )
        self.assertNotEqual(first["display_name"], second["display_name"])
        self.assertEqual(first["display_name"], "work/custom-skills")
        self.assertEqual(second["display_name"], "archive/custom-skills")

    def test_emit_project_bundles_includes_display_name_and_session_summaries(self) -> None:
        report = {
            "summary": {"project_count": 1},
            "period": {"start": "2026-03-11T00:00:00+08:00", "end": "2026-03-11T23:59:59+08:00"},
            "projects": {
                "/tmp/repo-a": {
                    "short_name": "repo-a",
                    "display_name": "client/repo-a",
                    "duration_minutes": 30,
                    "session_count": 1,
                    "sources": ["codex"],
                    "time_span": {"start": "2026-03-11T09:00:00+08:00", "end": "2026-03-11T09:30:00+08:00"},
                    "status_counts": {"completed": 1},
                    "session_hints": ["完成 parser"],
                    "files_touched": ["parser.py"],
                    "git_commits": [],
                }
            },
            "sessions": [
                {
                    "session_id": "codex-1",
                    "source": "codex",
                    "project": "/tmp/repo-a",
                    "start": "2026-03-11T09:00:00+08:00",
                    "end": "2026-03-11T09:30:00+08:00",
                    "duration_minutes": 30,
                    "status": "completed",
                    "first_prompt": "完成 parser",
                    "closing_note": "整理 tests",
                    "session_hints": ["完成 parser", "整理 tests"],
                    "commits": [],
                    "tools_used": {"Read": 2},
                    "evidence_paths": ["/tmp/codex-session.jsonl"],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            _emit_project_bundles(report, Path(tmpdir))
            manifest = json.loads((Path(tmpdir) / "manifest.json").read_text(encoding="utf-8"))
            bundle_path = Path(manifest["projects"][0]["path"])
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["projects"][0]["display_name"], "client/repo-a")
        self.assertEqual(bundle["display_name"], "client/repo-a")
        self.assertEqual(bundle["session_summaries"][0]["first_prompt"], "完成 parser")
        self.assertEqual(bundle["session_summaries"][0]["tools_used"], {"Read": 2})

    @patch("wl_parser.work_log_parser.collect_git_data")
    @patch("wl_parser.work_log_parser.load_claude_events")
    @patch("wl_parser.work_log_parser.load_codex_events")
    def test_build_report_excludes_subagents_and_unions_overlapping_main_sessions(
        self,
        mock_load_codex_events,
        mock_load_claude_events,
        mock_collect_git_data,
    ) -> None:
        mock_collect_git_data.return_value = []
        mock_load_claude_events.return_value = []
        mock_load_codex_events.return_value = [
            {
                "tool": "codex",
                "session_id": "main-1",
                "project_path": "/tmp/repo-a",
                "cwd": "/tmp/repo-a",
                "timestamp": "2026-03-11T09:00:00+08:00",
                "event_type": "response_item",
                "title": "user",
                "text": "main session 1",
                "evidence_path": "/tmp/main-1.jsonl",
                "confidence": "high",
                "is_subagent": False,
                "raw": {"payload": {"role": "user"}},
            },
            {
                "tool": "codex",
                "session_id": "main-1",
                "project_path": "/tmp/repo-a",
                "cwd": "/tmp/repo-a",
                "timestamp": "2026-03-11T09:20:00+08:00",
                "event_type": "response_item",
                "title": "assistant",
                "text": "main session 1 working",
                "evidence_path": "/tmp/main-1.jsonl",
                "confidence": "high",
                "is_subagent": False,
                "raw": {"payload": {"role": "assistant"}},
            },
            {
                "tool": "codex",
                "session_id": "main-1",
                "project_path": "/tmp/repo-a",
                "cwd": "/tmp/repo-a",
                "timestamp": "2026-03-11T09:45:00+08:00",
                "event_type": "response_item",
                "title": "assistant",
                "text": "main session 1 complete",
                "evidence_path": "/tmp/main-1.jsonl",
                "confidence": "high",
                "is_subagent": False,
                "raw": {"payload": {"role": "assistant"}},
            },
            {
                "tool": "codex",
                "session_id": "main-2",
                "project_path": "/tmp/repo-a",
                "cwd": "/tmp/repo-a",
                "timestamp": "2026-03-11T09:15:00+08:00",
                "event_type": "response_item",
                "title": "user",
                "text": "main session 2",
                "evidence_path": "/tmp/main-2.jsonl",
                "confidence": "high",
                "is_subagent": False,
                "raw": {"payload": {"role": "user"}},
            },
            {
                "tool": "codex",
                "session_id": "main-2",
                "project_path": "/tmp/repo-a",
                "cwd": "/tmp/repo-a",
                "timestamp": "2026-03-11T09:35:00+08:00",
                "event_type": "response_item",
                "title": "assistant",
                "text": "main session 2 working",
                "evidence_path": "/tmp/main-2.jsonl",
                "confidence": "high",
                "is_subagent": False,
                "raw": {"payload": {"role": "assistant"}},
            },
            {
                "tool": "codex",
                "session_id": "main-2",
                "project_path": "/tmp/repo-a",
                "cwd": "/tmp/repo-a",
                "timestamp": "2026-03-11T10:00:00+08:00",
                "event_type": "response_item",
                "title": "assistant",
                "text": "main session 2 complete",
                "evidence_path": "/tmp/main-2.jsonl",
                "confidence": "high",
                "is_subagent": False,
                "raw": {"payload": {"role": "assistant"}},
            },
            {
                "tool": "codex",
                "session_id": "sub-1",
                "project_path": "/tmp/repo-a",
                "cwd": "/tmp/repo-a",
                "timestamp": "2026-03-11T09:20:00+08:00",
                "event_type": "response_item",
                "title": "user",
                "text": "subagent investigation",
                "evidence_path": "/tmp/sub-1.jsonl",
                "confidence": "high",
                "is_subagent": True,
                "raw": {"payload": {"role": "user"}},
            },
            {
                "tool": "codex",
                "session_id": "sub-1",
                "project_path": "/tmp/repo-a",
                "cwd": "/tmp/repo-a",
                "timestamp": "2026-03-11T09:35:00+08:00",
                "event_type": "response_item",
                "title": "assistant",
                "text": "subagent in progress",
                "evidence_path": "/tmp/sub-1.jsonl",
                "confidence": "high",
                "is_subagent": True,
                "raw": {"payload": {"role": "assistant"}},
            },
            {
                "tool": "codex",
                "session_id": "sub-1",
                "project_path": "/tmp/repo-a",
                "cwd": "/tmp/repo-a",
                "timestamp": "2026-03-11T09:50:00+08:00",
                "event_type": "response_item",
                "title": "assistant",
                "text": "subagent result",
                "evidence_path": "/tmp/sub-1.jsonl",
                "confidence": "high",
                "is_subagent": True,
                "raw": {"payload": {"role": "assistant"}},
            },
        ]

        report = build_report(
            start=datetime(2026, 3, 11, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 3, 11, 23, 59, tzinfo=timezone.utc),
            timezone_name="Asia/Taipei",
            claude_home=Path("/tmp/claude"),
            codex_home=Path("/tmp/codex"),
            project_filter=None,
        )

        self.assertEqual([session["session_id"] for session in report["sessions"]], ["main-1", "main-2"])
        self.assertEqual(report["summary"]["active_sessions"], 2)
        self.assertEqual(report["summary"]["total_duration_minutes"], 60)
        self.assertEqual(report["summary"]["subagent_sessions"], 1)
        self.assertEqual(report["summary"]["subagent_duration_minutes"], 30)
        self.assertEqual(report["projects"]["/tmp/repo-a"]["session_count"], 2)
        self.assertEqual(report["projects"]["/tmp/repo-a"]["duration_minutes"], 60)
        self.assertEqual(
            report["daily_summary"],
            [
                {
                    "date": "2026-03-11",
                    "session_count": 2,
                    "total_duration_minutes": 60,
                    "total_commits": 0,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()

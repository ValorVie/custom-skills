from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from wl_parser.formatters import format_appendix, format_debug, format_full_report, format_obsidian, format_report, format_terminal  # noqa: E402
from wl_parser.formatters import main as formatters_main  # noqa: E402


SAMPLE_REPORT = {
    "period": {
        "start": "2026-03-11T09:00:00+08:00",
        "end": "2026-03-11T18:00:00+08:00",
        "timezone": "Asia/Taipei",
    },
    "summary": {
        "total_duration_minutes": 210,
        "active_sessions": 3,
        "project_count": 2,
        "total_commits": 2,
    },
    "projects": {
        "/Users/arlen/projects/repo-a": {
            "short_name": "repo-a",
            "display_name": "repo-a",
            "session_ids": ["codex-1", "codex-2"],
            "session_count": 2,
            "duration_minutes": 150,
            "session_hints": ["今天完成 parser 與報告輸出", "接下來整理 tests"],
            "git_commits": [
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
            ],
            "files_touched": ["parser.py", "tests/test_parser.py"],
        },
        "/Users/arlen/projects/repo-b": {
            "short_name": "repo-b",
            "display_name": "repo-b",
            "session_ids": ["claude-1"],
            "session_count": 1,
            "duration_minutes": 60,
            "session_hints": ["規劃明天的週報匯總"],
            "git_commits": [
                {
                    "hash": "def5678",
                    "full_hash": "def5678901234",
                    "message": "文件(report): 整理週報摘要",
                    "date": "2026-03-11 11:00:00 +0800",
                    "files_changed": 1,
                    "insertions": 10,
                    "deletions": 0,
                    "files": ["docs/weekly-report.md"],
                }
            ],
            "files_touched": ["docs/weekly-report.md"],
        },
    },
    "sessions": [
        {
            "session_id": "codex-1",
            "source": "codex",
            "project": "/Users/arlen/projects/repo-a",
            "start": "2026-03-10T09:00:00+08:00",
            "end": "2026-03-10T10:30:00+08:00",
            "duration_minutes": 90,
            "first_prompt": "今天完成 parser 與報告輸出",
            "status": "completed",
            "session_hints": ["今天完成 parser 與報告輸出"],
            "tools_used": {"Read": 4, "Edit": 3},
        },
        {
            "session_id": "codex-2",
            "source": "codex",
            "project": "/Users/arlen/projects/repo-a",
            "start": "2026-03-11T10:40:00+08:00",
            "end": "2026-03-11T11:40:00+08:00",
            "duration_minutes": 60,
            "first_prompt": "接下來整理 tests",
            "status": "in_progress",
            "session_hints": ["接下來整理 tests"],
            "tools_used": {"Read": 2},
        },
        {
            "session_id": "claude-1",
            "source": "claude",
            "project": "/Users/arlen/projects/repo-b",
            "start": "2026-03-11T11:00:00+08:00",
            "end": "2026-03-11T12:00:00+08:00",
            "duration_minutes": 60,
            "first_prompt": "規劃明天的週報匯總",
            "status": "completed",
            "session_hints": ["規劃明天的週報匯總"],
            "tools_used": {"Write": 1},
        },
    ],
    "codex_sessions": [{"thread_name": "daily summary", "updated_at": "2026-03-11T10:30:00Z"}],
    "tool_summary": {"Edit": 3, "Read": 6, "Write": 1},
    "token_summary": {
        "total_input": 5000,
        "total_output": 2000,
        "total_cache_creation": 1000,
        "total_cache_read": 8000,
    },
}

SAMPLE_SUMMARY = """### 當日總結

這天主要完成 repo-a 的 parser 與報告輸出，並同步整理 repo-b 的週報摘要。

### 逐專案摘要

#### repo-a
- 完成 parser 與報告輸出

#### repo-b
- 整理週報摘要
"""


class FormatterTest(unittest.TestCase):
    def test_format_terminal_has_title_and_stats(self) -> None:
        output = format_terminal(SAMPLE_REPORT)
        self.assertIn("工作日誌", output)
        self.assertIn("3 個 session", output)
        self.assertIn("2 個專案", output)
        self.assertNotIn("### 當日總結", output)

    def test_format_full_report_has_mechanical_sections_but_no_ai_headings(self) -> None:
        output = format_full_report(SAMPLE_REPORT)
        self.assertIn("### 工時統計", output)
        self.assertIn("### 每日摘要", output)
        self.assertIn("### Commit 明細", output)
        self.assertIn("### Session 明細", output)
        self.assertIn("repo-a", output)
        self.assertIn("功能(report): 新增工作日誌 parser", output)
        self.assertNotIn("### 當日總結", output)
        self.assertNotIn("### 逐專案摘要", output)

    def test_format_obsidian_has_frontmatter_and_full_report(self) -> None:
        output = format_obsidian(SAMPLE_REPORT)
        self.assertTrue(output.startswith("---"))
        self.assertIn("date: 2026-03-11", output)
        self.assertIn("type: work-log", output)
        self.assertIn("### 工時統計", output)
        self.assertNotIn("### Token 消耗", output)

    def test_format_report_keeps_summary_stats_and_daily_only(self) -> None:
        output = format_report(SAMPLE_REPORT, SAMPLE_SUMMARY)
        self.assertIn("### 當日總結", output)
        self.assertIn("### 逐專案摘要", output)
        self.assertIn("### 工時統計", output)
        self.assertIn("### 每日摘要", output)
        self.assertNotIn("### Token 消耗", output)
        self.assertNotIn("### 工具使用", output)
        self.assertNotIn("### Commit 明細", output)
        self.assertNotIn("### Session 明細", output)

    def test_format_appendix_contains_project_evidence_only(self) -> None:
        output = format_appendix(SAMPLE_REPORT)
        self.assertIn("### 專案證據附錄", output)
        self.assertIn("#### repo-a", output)
        self.assertIn("功能(report): 新增工作日誌 parser", output)
        self.assertNotIn("### Token 消耗", output)
        self.assertNotIn("### 工具使用", output)
        self.assertNotIn("### Session 明細", output)

    def test_format_debug_contains_audit_sections(self) -> None:
        output = format_debug(SAMPLE_REPORT)
        self.assertIn("### Token 消耗", output)
        self.assertIn("### 工具使用", output)
        self.assertIn("### Commit 明細", output)
        self.assertIn("### Session 明細", output)

    def test_formatters_cli_reads_json_from_stdin(self) -> None:
        payload = json.dumps(SAMPLE_REPORT, ensure_ascii=False)
        with patch("sys.stdin", StringIO(payload)), patch("sys.stdout", new_callable=StringIO) as stdout:
            formatters_main(["terminal"])
            rendered = stdout.getvalue()
        self.assertIn("工作日誌", rendered)
        self.assertNotIn("### 當日總結", rendered)

    def test_format_full_report_uses_display_name_when_available(self) -> None:
        report = json.loads(json.dumps(SAMPLE_REPORT))
        report["projects"]["/Users/arlen/projects/repo-a"]["display_name"] = "client/repo-a"
        output = format_full_report(report)
        self.assertIn("#### client/repo-a", output)

    def test_format_report_prefers_precomputed_daily_summary_union(self) -> None:
        report = {
            "period": {
                "start": "2026-03-11T00:00:00+08:00",
                "end": "2026-03-12T23:59:59+08:00",
                "timezone": "Asia/Taipei",
            },
            "summary": {
                "total_duration_minutes": 90,
                "active_sessions": 3,
                "project_count": 1,
                "total_commits": 0,
            },
            "projects": {
                "/Users/arlen/projects/repo-a": {
                    "short_name": "repo-a",
                    "display_name": "repo-a",
                    "session_count": 3,
                    "duration_minutes": 90,
                    "session_hints": ["main session 1", "main session 2", "main session 3"],
                    "git_commits": [],
                    "files_touched": [],
                }
            },
            "sessions": [
                {
                    "session_id": "main-1",
                    "source": "codex",
                    "project": "/Users/arlen/projects/repo-a",
                    "start": "2026-03-11T09:00:00+08:00",
                    "end": "2026-03-11T09:45:00+08:00",
                    "duration_minutes": 45,
                    "session_hints": ["main session 1"],
                    "commits": [],
                },
                {
                    "session_id": "main-2",
                    "source": "codex",
                    "project": "/Users/arlen/projects/repo-a",
                    "start": "2026-03-11T09:15:00+08:00",
                    "end": "2026-03-11T10:00:00+08:00",
                    "duration_minutes": 45,
                    "session_hints": ["main session 2"],
                    "commits": [],
                },
                {
                    "session_id": "main-3",
                    "source": "codex",
                    "project": "/Users/arlen/projects/repo-a",
                    "start": "2026-03-12T09:00:00+08:00",
                    "end": "2026-03-12T09:30:00+08:00",
                    "duration_minutes": 30,
                    "session_hints": ["main session 3"],
                    "commits": [],
                },
            ],
            "daily_summary": [
                {
                    "date": "2026-03-11",
                    "session_count": 2,
                    "total_duration_minutes": 60,
                    "total_commits": 0,
                },
                {
                    "date": "2026-03-12",
                    "session_count": 1,
                    "total_duration_minutes": 30,
                    "total_commits": 0,
                }
            ],
        }

        output = format_report(report, SAMPLE_SUMMARY)

        self.assertIn("| 03-11 | 2 | 1.0h | 0 |", output)
        self.assertNotIn("| 03-11 | 2 | 1.5h | 0 |", output)


if __name__ == "__main__":
    unittest.main()

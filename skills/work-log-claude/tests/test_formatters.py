# tests/test_formatters.py
import json
from io import StringIO
from unittest.mock import patch
from wl_parser.formatters import format_terminal, format_full_report, format_obsidian
from wl_parser.formatters import main as formatters_main

SAMPLE_REPORT_V2 = {
    "period": {
        "start": "2026-03-11T14:00:00+08:00",
        "end": "2026-03-11T18:30:00+08:00",
        "timezone": "Asia/Taipei",
    },
    "summary": {
        "total_duration_minutes": 150,
        "active_sessions": 2,
        "project_count": 1,
        "total_commits": 1,
    },
    "projects": {
        "/Users/arlen/project-a": {
            "short_name": "project-a",
            "session_ids": ["s1", "s2"],
            "session_count": 2,
            "duration_minutes": 150,
            "git_commits": [
                {
                    "hash": "abc1234",
                    "full_hash": "abc1234567890",
                    "message": "修正(checkout): 處理折扣為零",
                    "date": "2026-03-11 15:00:00 +0800",
                    "files_changed": 2,
                    "insertions": 30,
                    "deletions": 5,
                }
            ],
            "files_changed_count": 2,
        },
    },
    "sessions": [
        {
            "session_id": "s1",
            "project": "/Users/arlen/project-a",
            "start": "2026-03-11T14:00:00+08:00",
            "end": "2026-03-11T16:30:00+08:00",
            "duration_minutes": 120,
            "first_prompt": "修正折扣計算",
            "commits": ["修正(checkout): 處理折扣為零"],
            "files_changed": ["controller/checkout.php"],
            "files_changed_count": 1,
            "tools_used": {"Edit": 5, "Read": 3, "Bash": 2},
            "status": "completed",
            "tokens": {"input": 5000, "output": 1200, "cache_creation": 3000, "cache_read": 8000},
        },
        {
            "session_id": "s2",
            "project": "/Users/arlen/project-a",
            "start": "2026-03-11T16:30:00+08:00",
            "end": "2026-03-11T18:00:00+08:00",
            "duration_minutes": 30,
            "first_prompt": "繼續重構結帳流程",
            "commits": [],
            "files_changed": ["model/checkout.php"],
            "files_changed_count": 1,
            "tools_used": {"Edit": 3},
            "status": "in_progress",
            "tokens": {"input": 2000, "output": 500, "cache_creation": 1000, "cache_read": 3000},
        },
    ],
    "codex_sessions": [
        {"thread_name": "Fix nginx config", "updated_at": "2026-03-11T08:00:00Z"}
    ],
    "tool_summary": {"Edit": 8, "Read": 3, "Bash": 2},
    "token_summary": {
        "total_input": 7000,
        "total_output": 1700,
        "total_cache_creation": 4000,
        "total_cache_read": 11000,
    },
}

MULTI_DAY_REPORT_V2 = {
    "period": {
        "start": "2026-03-09T00:00:00+08:00",
        "end": "2026-03-11T23:59:59+08:00",
        "timezone": "Asia/Taipei",
    },
    "summary": {
        "total_duration_minutes": 300,
        "active_sessions": 3,
        "project_count": 1,
        "total_commits": 1,
    },
    "projects": {
        "/Users/arlen/project-a": {
            "short_name": "project-a",
            "session_ids": ["s1", "s2", "s3"],
            "session_count": 3,
            "duration_minutes": 300,
            "git_commits": [
                {
                    "hash": "abc1234",
                    "full_hash": "abc1234567890",
                    "message": "修正(checkout): 處理折扣為零",
                    "date": "2026-03-11 15:00:00 +0800",
                    "files_changed": 2,
                    "insertions": 30,
                    "deletions": 5,
                }
            ],
            "files_changed_count": 2,
        },
    },
    "sessions": [
        {
            "session_id": "s1",
            "project": "/Users/arlen/project-a",
            "start": "2026-03-09T10:00:00+08:00",
            "end": "2026-03-09T12:00:00+08:00",
            "duration_minutes": 120,
            "first_prompt": "研究 API 架構",
            "commits": [],
            "files_changed": [],
            "files_changed_count": 0,
            "tools_used": {"Read": 3},
            "status": "in_progress",
            "tokens": {"input": 100, "output": 50, "cache_creation": 0, "cache_read": 0},
        },
        {
            "session_id": "s2",
            "project": "/Users/arlen/project-a",
            "start": "2026-03-11T14:00:00+08:00",
            "end": "2026-03-11T16:00:00+08:00",
            "duration_minutes": 120,
            "first_prompt": "修正折扣計算",
            "commits": ["修正(checkout): 處理折扣為零"],
            "files_changed": ["controller/checkout.php"],
            "files_changed_count": 1,
            "tools_used": {"Edit": 5},
            "status": "completed",
            "tokens": {"input": 100, "output": 50, "cache_creation": 0, "cache_read": 0},
        },
        {
            "session_id": "s3",
            "project": "/Users/arlen/project-a",
            "start": "2026-03-11T16:00:00+08:00",
            "end": "2026-03-11T17:00:00+08:00",
            "duration_minutes": 60,
            "first_prompt": None,
            "commits": [],
            "files_changed": [],
            "files_changed_count": 0,
            "tools_used": {"Read": 1},
            "status": "in_progress",
            "tokens": {"input": 100, "output": 50, "cache_creation": 0, "cache_read": 0},
        },
    ],
    "codex_sessions": [],
    "tool_summary": {"Edit": 5, "Read": 4},
    "token_summary": {"total_input": 300, "total_output": 150, "total_cache_creation": 0, "total_cache_read": 0},
}


# --- format_terminal v2 ---

def test_format_terminal_v2_has_title_and_stats():
    output = format_terminal(SAMPLE_REPORT_V2)
    assert "工作日誌" in output
    assert "2026-03-11" in output
    assert "2.5" in output
    assert "2 個 session" in output
    assert "1 個專案" in output


def test_format_terminal_v2_no_completed_section():
    output = format_terminal(SAMPLE_REPORT_V2)
    assert "完成項目" not in output


def test_format_terminal_v2_no_in_progress_section():
    output = format_terminal(SAMPLE_REPORT_V2)
    assert "進行中" not in output


def test_format_terminal_v2_no_tool_summary():
    output = format_terminal(SAMPLE_REPORT_V2)
    assert "工具使用" not in output


def test_format_terminal_v2_no_token_summary():
    output = format_terminal(SAMPLE_REPORT_V2)
    assert "Token" not in output


def test_format_terminal_v2_daily_summary_multi_day():
    output = format_terminal(MULTI_DAY_REPORT_V2)
    assert "每日摘要" in output
    assert "03-09" in output
    assert "03-11" in output


def test_format_terminal_v2_no_daily_summary_single_day():
    output = format_terminal(SAMPLE_REPORT_V2)
    assert "每日摘要" not in output


# --- format_full_report v2 ---

def test_format_full_report_v2_has_stats():
    output = format_full_report(SAMPLE_REPORT_V2)
    assert "工時統計" in output
    assert "2.5" in output


def test_format_full_report_v2_has_tool_summary():
    output = format_full_report(SAMPLE_REPORT_V2)
    assert "工具使用" in output
    assert "Edit" in output


def test_format_full_report_v2_has_token_summary():
    output = format_full_report(SAMPLE_REPORT_V2)
    assert "Token" in output


def test_format_full_report_v2_has_commit_details():
    output = format_full_report(SAMPLE_REPORT_V2)
    assert "Commit 明細" in output
    assert "project-a" in output
    assert "abc1234" in output
    assert "修正(checkout): 處理折扣為零" in output


def test_format_full_report_v2_has_session_details():
    output = format_full_report(SAMPLE_REPORT_V2)
    assert "Session 明細" in output
    assert "修正折扣計算" in output


def test_format_full_report_v2_has_codex():
    output = format_full_report(SAMPLE_REPORT_V2)
    assert "Fix nginx config" in output


def test_format_full_report_v2_no_completed_section():
    output = format_full_report(SAMPLE_REPORT_V2)
    assert "完成項目" not in output


def test_format_full_report_v2_no_in_progress_section():
    output = format_full_report(SAMPLE_REPORT_V2)
    assert "進行中" not in output


# --- format_obsidian v2 ---

def test_format_obsidian_v2_has_frontmatter():
    output = format_obsidian(SAMPLE_REPORT_V2)
    assert output.startswith("---")
    assert "date: 2026-03-11" in output
    assert "type: work-log" in output
    assert "total_hours: 2.5" in output


def test_format_obsidian_v2_has_project_tags():
    output = format_obsidian(SAMPLE_REPORT_V2)
    assert "project-a" in output


def test_format_obsidian_v2_has_commits_field():
    output = format_obsidian(SAMPLE_REPORT_V2)
    assert "commits: 1" in output


def test_format_obsidian_v2_contains_full_report():
    output = format_obsidian(SAMPLE_REPORT_V2)
    assert "Commit 明細" in output
    assert "Session 明細" in output


# --- CLI ---

def test_formatters_cli_terminal_v2():
    json_input = json.dumps(SAMPLE_REPORT_V2)
    with patch("sys.stdin", StringIO(json_input)):
        with patch("builtins.print") as mock_print:
            formatters_main(["terminal"])
            output = mock_print.call_args[0][0]
            assert "工作日誌" in output
            assert "完成項目" not in output


def test_formatters_cli_full_report_v2():
    json_input = json.dumps(SAMPLE_REPORT_V2)
    with patch("sys.stdin", StringIO(json_input)):
        with patch("builtins.print") as mock_print:
            formatters_main(["full_report"])
            output = mock_print.call_args[0][0]
            assert "Commit 明細" in output


def test_formatters_cli_obsidian_v2():
    json_input = json.dumps(SAMPLE_REPORT_V2)
    with patch("sys.stdin", StringIO(json_input)):
        with patch("builtins.print") as mock_print:
            formatters_main(["obsidian"])
            output = mock_print.call_args[0][0]
            assert "---" in output
            assert "type: work-log" in output

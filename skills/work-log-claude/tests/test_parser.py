# tests/test_parser.py
from pathlib import Path
from datetime import datetime, timezone, timedelta

from wl_parser.work_log_parser import (
    parse_jsonl_file,
    group_by_session,
    calculate_active_duration,
    decode_project_path,
    parse_timestamp,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_jsonl_file_filters_by_type():
    """Only user/assistant records are returned (system/progress skipped)."""
    records = parse_jsonl_file(
        FIXTURES / "sample_session.jsonl",
        start=datetime(2026, 3, 10, 0, 0, tzinfo=timezone.utc),
        end=datetime(2026, 3, 12, 0, 0, tzinfo=timezone.utc),
    )
    types = {r["type"] for r in records}
    assert types <= {"user", "assistant"}, f"Unexpected types: {types - {'user', 'assistant'}}"


def test_parse_jsonl_file_returns_in_range():
    """Returns records with timestamps within the range."""
    records = parse_jsonl_file(
        FIXTURES / "sample_session.jsonl",
        start=datetime(2026, 3, 11, 6, 0, tzinfo=timezone.utc),
        end=datetime(2026, 3, 11, 9, 0, tzinfo=timezone.utc),
    )
    assert len(records) > 0


def test_parse_jsonl_file_skips_out_of_range():
    """Records outside the time range are excluded."""
    records = parse_jsonl_file(
        FIXTURES / "sample_session.jsonl",
        start=datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc),
        end=datetime(2025, 1, 1, 23, 59, tzinfo=timezone.utc),
    )
    assert records == []


def test_parse_jsonl_file_nonexistent():
    """Missing file returns empty list (no exception)."""
    records = parse_jsonl_file(
        Path("/nonexistent/file.jsonl"),
        start=datetime(2026, 3, 11, 0, 0, tzinfo=timezone.utc),
        end=datetime(2026, 3, 11, 23, 59, tzinfo=timezone.utc),
    )
    assert records == []


def test_group_by_session():
    records = [
        {"sessionId": "a", "type": "user"},
        {"sessionId": "a", "type": "assistant"},
        {"sessionId": "b", "type": "user"},
    ]
    groups = group_by_session(records)
    assert len(groups) == 2
    assert len(groups["a"]) == 2
    assert len(groups["b"]) == 1


def test_group_by_session_empty():
    assert group_by_session([]) == {}


def test_calculate_active_duration_with_gap():
    """Gaps exceeding the idle threshold split into separate active segments."""
    timestamps = [
        "2026-03-11T06:00:00Z",   # start seg 1
        "2026-03-11T06:45:00Z",   # +45min (active, within threshold)
        "2026-03-11T08:00:00Z",   # +75min gap (idle! exceeds 60min threshold)
        "2026-03-11T08:20:00Z",   # +20min (active) end seg 2
    ]
    duration = calculate_active_duration(timestamps, idle_threshold_minutes=60)
    # seg1: 06:00 -> 06:45 = 45 min
    # seg2: 08:00 -> 08:20 = 20 min
    # total = 65 min
    assert duration == 65


def test_calculate_active_duration_no_gap():
    timestamps = [
        "2026-03-11T06:00:00Z",
        "2026-03-11T06:30:00Z",
        "2026-03-11T07:00:00Z",
    ]
    duration = calculate_active_duration(timestamps, idle_threshold_minutes=30)
    assert duration == 60


def test_calculate_active_duration_single_record():
    assert calculate_active_duration(["2026-03-11T06:00:00Z"]) == 0


def test_calculate_active_duration_empty():
    assert calculate_active_duration([]) == 0


def test_calculate_active_duration_exact_threshold_not_idle():
    """Exactly 30 minutes gap is NOT idle (threshold is strictly > 30)."""
    timestamps = [
        "2026-03-11T06:00:00Z",
        "2026-03-11T06:30:00Z",  # exactly 30 min — still active
    ]
    duration = calculate_active_duration(timestamps, idle_threshold_minutes=30)
    assert duration == 30  # still one segment


def test_decode_project_path_simple():
    """Simple path with no hyphens in directory names."""
    result = decode_project_path("-Users-arlen-ai-home")
    assert "arlen" in result
    assert result.startswith("/")


def test_decode_project_path_starts_with_slash():
    """Decoded path always starts with /."""
    result = decode_project_path("-home-valor-Code-project")
    assert result.startswith("/")


def test_parse_timestamp_utc():
    dt = parse_timestamp("2026-03-11T06:00:00.000Z")
    assert dt.year == 2026
    assert dt.month == 3
    assert dt.day == 11
    assert dt.tzinfo is not None


def test_parse_timestamp_offset():
    dt = parse_timestamp("2026-03-11T14:00:00+08:00")
    assert dt.year == 2026
    assert dt.month == 3
    assert dt.day == 11
    assert dt.tzinfo is not None


import shutil
from zoneinfo import ZoneInfo
from wl_parser.work_log_parser import build_report, parse_codex_sessions, _get_tz


def test_build_report_from_fixture(tmp_path):
    """Full pipeline test using fixture data."""
    # Set up simulated project structure
    project_dir = tmp_path / "projects" / "-test-project"
    project_dir.mkdir(parents=True)
    shutil.copy(FIXTURES / "sample_session.jsonl", project_dir / "session-001.jsonl")

    # Set up codex fixture
    codex_dir = tmp_path / "codex"
    codex_dir.mkdir()
    shutil.copy(FIXTURES / "sample_codex_index.jsonl", codex_dir / "session_index.jsonl")

    report = build_report(
        start=datetime(2026, 3, 11, 6, 0, tzinfo=timezone.utc),
        end=datetime(2026, 3, 11, 9, 0, tzinfo=timezone.utc),
        timezone_name="Asia/Taipei",
        claude_home=tmp_path,
        codex_home=codex_dir,
        project_filter=None,
    )

    # Structure check
    assert "period" in report
    assert "summary" in report
    assert "sessions" in report
    assert "codex_sessions" in report
    assert "tool_summary" in report
    assert "token_summary" in report

    # Sessions were parsed
    assert report["summary"]["active_sessions"] >= 1

    # Token summary has the right keys
    ts = report["token_summary"]
    assert all(k in ts for k in ["total_input", "total_output", "total_cache_creation", "total_cache_read"])

    # Session structure
    for s in report["sessions"]:
        assert "session_id" in s
        assert "project" in s
        assert "duration_minutes" in s
        assert "status" in s
        assert s["status"] in ("completed", "in_progress")
        assert "tokens" in s
        assert all(k in s["tokens"] for k in ["input", "output", "cache_creation", "cache_read"])


def test_build_report_codex_filtering(tmp_path):
    """Codex sessions filtered to time range."""
    project_dir = tmp_path / "projects" / "-test"
    project_dir.mkdir(parents=True)
    shutil.copy(FIXTURES / "sample_session.jsonl", project_dir / "s.jsonl")

    codex_dir = tmp_path / "codex"
    codex_dir.mkdir()
    shutil.copy(FIXTURES / "sample_codex_index.jsonl", codex_dir / "session_index.jsonl")

    report = build_report(
        start=datetime(2026, 3, 11, 0, 0, tzinfo=timezone.utc),
        end=datetime(2026, 3, 11, 23, 59, tzinfo=timezone.utc),
        timezone_name="Asia/Taipei",
        claude_home=tmp_path,
        codex_home=codex_dir,
        project_filter=None,
    )

    # Only the 2026-03-11 codex session should appear, not the 2026-03-01 one
    assert len(report["codex_sessions"]) == 1
    assert report["codex_sessions"][0]["thread_name"] == "Fix nginx config"


def test_build_report_project_filter(tmp_path):
    """Project filter narrows to matching project name."""
    for name in ["-test-project-a", "-test-project-b"]:
        d = tmp_path / "projects" / name
        d.mkdir(parents=True)
        shutil.copy(FIXTURES / "sample_session.jsonl", d / "s.jsonl")

    report = build_report(
        start=datetime(2026, 3, 11, 6, 0, tzinfo=timezone.utc),
        end=datetime(2026, 3, 11, 9, 0, tzinfo=timezone.utc),
        timezone_name="Asia/Taipei",
        claude_home=tmp_path,
        codex_home=tmp_path,  # no codex data
        project_filter="project-a",
    )

    # Only project-a sessions should be present (not project-b).
    # The filter "-test-project-a" matches "project-a" but not "-test-project-b".
    # decode_project_path("-test-project-a") → "/test/project/a" (no hyphens).
    # Verify no project-b decoded path appears.
    assert len(report["sessions"]) >= 1
    for s in report["sessions"]:
        # The last path component for project-a is "a", not "b"
        assert s["project"].split("/")[-1] != "b"


def test_build_report_no_claude_home(tmp_path):
    """Missing claude_home returns empty report."""
    report = build_report(
        start=datetime(2026, 3, 11, 0, 0, tzinfo=timezone.utc),
        end=datetime(2026, 3, 11, 23, 59, tzinfo=timezone.utc),
        timezone_name="Asia/Taipei",
        claude_home=tmp_path / "nonexistent",
        codex_home=tmp_path / "nonexistent",
        project_filter=None,
    )
    assert report["summary"]["active_sessions"] == 0
    assert report["sessions"] == []


def test_parse_codex_sessions_in_range(tmp_path):
    """Only sessions within range are returned."""
    codex_dir = tmp_path / "codex"
    codex_dir.mkdir()
    shutil.copy(FIXTURES / "sample_codex_index.jsonl", codex_dir / "session_index.jsonl")

    sessions = parse_codex_sessions(
        codex_dir,
        start=datetime(2026, 3, 11, 0, 0, tzinfo=timezone.utc),
        end=datetime(2026, 3, 11, 23, 59, tzinfo=timezone.utc),
    )
    assert len(sessions) == 1
    assert sessions[0]["thread_name"] == "Fix nginx config"


def test_parse_codex_sessions_missing_dir(tmp_path):
    """Missing codex dir returns empty list."""
    sessions = parse_codex_sessions(
        tmp_path / "nonexistent",
        start=datetime(2026, 3, 11, 0, 0, tzinfo=timezone.utc),
        end=datetime(2026, 3, 11, 23, 59, tzinfo=timezone.utc),
    )
    assert sessions == []


def test_get_tz_valid():
    tz = _get_tz("Asia/Taipei")
    assert tz is not None
    # Verify it's UTC+8
    now_utc = datetime(2026, 3, 11, 0, 0, tzinfo=timezone.utc)
    now_taipei = now_utc.astimezone(tz)
    assert now_taipei.hour == 8


def test_get_tz_invalid():
    """Invalid timezone falls back gracefully."""
    tz = _get_tz("Invalid/Zone")
    assert tz is not None  # should fall back to UTC


from wl_parser.work_log_parser import parse_time_shortcut, parse_args


def test_parse_time_shortcut_today():
    start, end = parse_time_shortcut("today", "Asia/Taipei")
    assert start.hour == 0 and start.minute == 0 and start.second == 0
    assert end.hour == 23 and end.minute == 59 and end.second == 59
    # They should be on the same date
    assert start.date() == end.date()


def test_parse_time_shortcut_yesterday():
    start, end = parse_time_shortcut("yesterday", "Asia/Taipei")
    today_start, _ = parse_time_shortcut("today", "Asia/Taipei")
    assert end < today_start
    assert start.hour == 0 and end.hour == 23


def test_parse_time_shortcut_this_week():
    start, end = parse_time_shortcut("this-week", "Asia/Taipei")
    assert start.weekday() == 0  # Monday
    assert start.hour == 0
    assert end.hour == 23


def test_parse_time_shortcut_this_month():
    start, end = parse_time_shortcut("this-month", "Asia/Taipei")
    assert start.day == 1
    assert start.hour == 0
    assert end.hour == 23


def test_parse_time_shortcut_custom_single_date():
    start, end = parse_time_shortcut("2026-03-01", "Asia/Taipei")
    assert start.year == 2026
    assert start.month == 3
    assert start.day == 1
    assert start.hour == 0
    assert end.day == 1
    assert end.hour == 23


def test_parse_time_shortcut_custom_range():
    start, end = parse_time_shortcut("2026-03-01", "Asia/Taipei", end_str="2026-03-11")
    assert start.day == 1
    assert end.day == 11
    assert start.month == 3 and end.month == 3


def test_parse_args_defaults():
    args = parse_args(["today"])
    assert args.time_range == "today"
    assert args.timezone == "Asia/Taipei"
    assert args.project is None


def test_parse_args_with_options():
    args = parse_args(["this-week", "--project", "qdm-base", "--timezone", "UTC"])
    assert args.time_range == "this-week"
    assert args.project == "qdm-base"
    assert args.timezone == "UTC"


def test_parse_args_date_range():
    args = parse_args(["2026-03-01", "2026-03-11"])
    assert args.time_range == "2026-03-01"
    assert args.end_date == "2026-03-11"


from wl_parser.work_log_parser import _to_relative_path, analyze_session, _aggregate_by_project


def test_to_relative_path_within_project():
    assert _to_relative_path("/Users/arlen/proj/src/main.py", "/Users/arlen/proj") == "src/main.py"


def test_to_relative_path_outside_project():
    result = _to_relative_path("/other/path/file.py", "/Users/arlen/proj")
    assert result == "/other/path/file.py"


def test_to_relative_path_exact_project():
    """File at project root."""
    assert _to_relative_path("/Users/arlen/proj/file.py", "/Users/arlen/proj") == "file.py"


def test_analyze_session_has_files_changed_count(tmp_path):
    """analyze_session output includes files_changed_count."""
    records = [
        {"type": "assistant", "timestamp": "2026-03-11T08:00:00Z", "sessionId": "s1",
         "message": {"content": [
             {"type": "tool_use", "name": "Edit", "input": {"file_path": "/test/project/a.py"}},
             {"type": "tool_use", "name": "Write", "input": {"file_path": "/test/project/b.py"}},
         ], "usage": {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}},
        {"type": "assistant", "timestamp": "2026-03-11T08:30:00Z", "sessionId": "s1",
         "message": {"content": [{"type": "text", "text": "Done"}],
                     "usage": {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}},
    ]
    from zoneinfo import ZoneInfo
    result = analyze_session("s1", records, "-test-project", ZoneInfo("UTC"))
    assert result["files_changed_count"] == 2
    assert "files_changed" in result


def test_build_report_excludes_abandoned(tmp_path):
    """Abandoned sessions are filtered out of the report."""
    import json

    project_dir = tmp_path / "projects" / "-test-proj"
    project_dir.mkdir(parents=True)

    # Create a session with only 1 timestamp (duration=0, no tools) → abandoned
    abandoned_session = [
        {"type": "user", "timestamp": "2026-03-11T07:00:00Z", "sessionId": "abandoned-1",
         "message": {"content": "hi"}},
        {"type": "assistant", "timestamp": "2026-03-11T07:00:00Z", "sessionId": "abandoned-1",
         "message": {"content": [{"type": "text", "text": "hello"}],
                     "usage": {"input_tokens": 0, "output_tokens": 0,
                               "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}},
    ]
    with open(project_dir / "session.jsonl", "w") as f:
        for r in abandoned_session:
            f.write(json.dumps(r) + "\n")

    report = build_report(
        start=datetime(2026, 3, 11, 0, 0, tzinfo=timezone.utc),
        end=datetime(2026, 3, 11, 23, 59, tzinfo=timezone.utc),
        timezone_name="UTC",
        claude_home=tmp_path,
        codex_home=tmp_path,
    )
    # The abandoned session should be excluded
    assert report["sessions"] == [], "abandoned sessions should be filtered out entirely"
    for s in report["sessions"]:
        assert s["status"] != "abandoned", "abandoned sessions should be filtered"


def test_aggregate_by_project_groups_correctly():
    sessions = [
        {"session_id": "s1", "project": "/a/proj-x", "duration_minutes": 30, "files_changed_count": 2},
        {"session_id": "s2", "project": "/a/proj-x", "duration_minutes": 45, "files_changed_count": 3},
        {"session_id": "s3", "project": "/b/proj-y", "duration_minutes": 60, "files_changed_count": 1},
    ]
    projects = _aggregate_by_project(sessions)
    assert len(projects) == 2
    assert "/a/proj-x" in projects
    px = projects["/a/proj-x"]
    assert px["short_name"] == "proj-x"
    assert px["session_ids"] == ["s1", "s2"]
    assert px["session_count"] == 2
    assert px["duration_minutes"] == 75


def test_aggregate_by_project_empty():
    assert _aggregate_by_project([]) == {}


def test_aggregate_by_project_single_session():
    sessions = [{"session_id": "s1", "project": "/home/user/app", "duration_minutes": 10, "files_changed_count": 0}]
    projects = _aggregate_by_project(sessions)
    assert len(projects) == 1
    assert projects["/home/user/app"]["short_name"] == "app"
    assert projects["/home/user/app"]["session_count"] == 1


def test_build_report_v2_has_projects(tmp_path):
    """v2 report includes projects aggregation."""
    project_dir = tmp_path / "projects" / "-test-project"
    project_dir.mkdir(parents=True)
    shutil.copy(FIXTURES / "sample_session.jsonl", project_dir / "session-001.jsonl")
    codex_dir = tmp_path / "codex"
    codex_dir.mkdir()
    shutil.copy(FIXTURES / "sample_codex_index.jsonl", codex_dir / "session_index.jsonl")

    report = build_report(
        start=datetime(2026, 3, 11, 6, 0, tzinfo=timezone.utc),
        end=datetime(2026, 3, 11, 9, 0, tzinfo=timezone.utc),
        timezone_name="Asia/Taipei",
        claude_home=tmp_path,
        codex_home=codex_dir,
    )
    assert "projects" in report
    assert isinstance(report["projects"], dict)
    if report["sessions"]:
        assert len(report["projects"]) >= 1
        for path, proj in report["projects"].items():
            assert "short_name" in proj
            assert "session_ids" in proj
            assert "session_count" in proj
            assert "duration_minutes" in proj
            assert "git_commits" in proj
            assert "files_changed_count" in proj


def test_build_report_v2_summary_fields(tmp_path):
    """v2 summary has project_count and total_commits."""
    project_dir = tmp_path / "projects" / "-test-project"
    project_dir.mkdir(parents=True)
    shutil.copy(FIXTURES / "sample_session.jsonl", project_dir / "session-001.jsonl")

    report = build_report(
        start=datetime(2026, 3, 11, 6, 0, tzinfo=timezone.utc),
        end=datetime(2026, 3, 11, 9, 0, tzinfo=timezone.utc),
        timezone_name="Asia/Taipei",
        claude_home=tmp_path,
        codex_home=tmp_path,
    )
    assert "project_count" in report["summary"]
    assert "total_commits" in report["summary"]
    assert isinstance(report["summary"]["project_count"], int)
    assert isinstance(report["summary"]["total_commits"], int)

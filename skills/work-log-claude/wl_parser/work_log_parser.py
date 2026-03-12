# wl_parser/work_log_parser.py
"""Work log parser — reads Claude Code session JSONL files and outputs structured JSON."""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta, date as date_type
from pathlib import Path

from wl_parser.git_collector import collect_git_data
from wl_parser.extractors import (
    extract_commits,
    extract_first_prompt,
    extract_files_changed,
    extract_tool_usage,
    extract_tokens,
    detect_session_status,
)


PROCESSABLE_TYPES = {"user", "assistant"}

# Project directory patterns to exclude (automated observer sessions, not real work)
EXCLUDED_PROJECT_PATTERNS = {"observer", "mem-observer", "claude-mem"}

# First prompt patterns that indicate automated sessions
OBSERVER_PROMPT_PATTERNS = re.compile(
    r"^(You are a Claude-Mem|Hello memory agent)", re.IGNORECASE
)


def parse_timestamp(ts_str: str) -> datetime:
    """Parse ISO-8601 timestamp to aware datetime. Handles 'Z' suffix."""
    ts_str = ts_str.replace("Z", "+00:00")
    return datetime.fromisoformat(ts_str)


def parse_jsonl_file(
    filepath: Path,
    start: datetime,
    end: datetime,
) -> list:
    """Read a JSONL file, return records of type user/assistant within [start, end]."""
    records = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    print(f"Warning: skipping malformed line {line_num} in {filepath}", file=sys.stderr)
                    continue

                rec_type = record.get("type")
                if rec_type not in PROCESSABLE_TYPES:
                    continue

                ts_str = record.get("timestamp")
                if not ts_str:
                    continue

                try:
                    ts = parse_timestamp(ts_str)
                except (ValueError, TypeError):
                    continue

                if start <= ts <= end:
                    records.append(record)
    except PermissionError:
        print(f"Warning: permission denied reading {filepath}", file=sys.stderr)
    except FileNotFoundError:
        pass

    return records


def group_by_session(records: list) -> dict:
    """Group records by sessionId."""
    groups: dict = defaultdict(list)
    for r in records:
        sid = r.get("sessionId", "unknown")
        groups[sid].append(r)
    return dict(groups)


def calculate_active_duration(timestamps: list, idle_threshold_minutes: int = 30) -> int:
    """Calculate active duration in minutes, splitting on idle gaps > threshold.

    Returns total active minutes (sum of active segments).
    Exactly threshold minutes gap is NOT idle (uses strictly greater than).
    """
    if len(timestamps) < 2:
        return 0

    dts = sorted(parse_timestamp(ts) for ts in timestamps)
    threshold = timedelta(minutes=idle_threshold_minutes)

    total_minutes = 0
    segment_start = dts[0]
    prev = dts[0]

    for dt in dts[1:]:
        gap = dt - prev
        if gap > threshold:
            # Close current segment
            total_minutes += int((prev - segment_start).total_seconds() / 60)
            segment_start = dt
        prev = dt

    # Close final segment
    total_minutes += int((prev - segment_start).total_seconds() / 60)

    return total_minutes


def decode_project_path(encoded: str) -> str:
    """Decode project directory name back to filesystem path.

    '-Users-arlen-ai-home' -> '/Users/arlen/ai-home'

    Uses greedy filesystem validation: tries longest matching existing paths first.
    Known limitation: ambiguous for directory names that contain hyphens.
    """
    parts = encoded.lstrip("-").split("-")
    path = "/"
    i = 0
    while i < len(parts):
        # Try joining progressively more parts with hyphens (greedy)
        best = None
        best_j = i + 1
        for j in range(len(parts), i, -1):
            candidate = os.path.join(path, "-".join(parts[i:j]))
            if os.path.exists(candidate):
                best = candidate
                best_j = j
                break
        if best:
            path = best
            i = best_j
        else:
            path = os.path.join(path, parts[i])
            i += 1
    return path


def _to_relative_path(filepath: str, project_path: str) -> str:
    """Convert absolute path to relative path based on project directory."""
    try:
        return str(Path(filepath).relative_to(project_path))
    except ValueError:
        return filepath


def _get_tz(timezone_name: str):
    """Get timezone object using zoneinfo (Python 3.9+ stdlib)."""
    from zoneinfo import ZoneInfo
    try:
        return ZoneInfo(timezone_name)
    except (KeyError, Exception):
        return timezone.utc


def _is_excluded_project(project_name: str) -> bool:
    """Check if a project directory should be excluded (automated observer sessions)."""
    name_lower = project_name.lower()
    return any(pattern in name_lower for pattern in EXCLUDED_PROJECT_PATTERNS)


def _is_observer_session(first_prompt: str | None) -> bool:
    """Check if a session is an automated observer based on its first prompt."""
    if not first_prompt:
        return False
    return bool(OBSERVER_PROMPT_PATTERNS.match(first_prompt))


def scan_session_files(
    claude_home: Path,
    start: datetime,
    project_filter: str | None = None,
) -> list:
    """Scan claude projects for JSONL files modified after start - 24h.

    Returns list of (project_name, filepath) tuples.
    """
    projects_dir = claude_home / "projects"
    if not projects_dir.exists():
        return []

    cutoff = (start - timedelta(hours=24)).timestamp()
    results = []

    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        project_name = project_dir.name

        if project_filter and project_filter not in project_name:
            continue

        for jsonl_file in project_dir.glob("*.jsonl"):
            try:
                if jsonl_file.stat().st_mtime >= cutoff:
                    results.append((project_name, jsonl_file))
            except OSError:
                continue

    return results


def parse_codex_sessions(
    codex_home: Path,
    start: datetime,
    end: datetime,
) -> list:
    """Read Codex session_index.jsonl and filter by time range."""
    index_file = codex_home / "session_index.jsonl"
    if not index_file.exists():
        return []

    sessions = []
    try:
        with open(index_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                updated = entry.get("updated_at")
                if not updated:
                    continue

                try:
                    ts = parse_timestamp(updated)
                except (ValueError, TypeError):
                    continue

                if start <= ts <= end:
                    sessions.append({
                        "thread_name": entry.get("thread_name", ""),
                        "updated_at": updated,
                    })
    except (PermissionError, FileNotFoundError):
        pass

    return sessions


def analyze_session(
    session_id: str,
    records: list,
    project_name: str,
    tz,
) -> dict:
    """Analyze a single session's records and return structured data."""
    timestamps = [r["timestamp"] for r in records if "timestamp" in r]
    timestamps.sort()

    all_commits = []
    for r in records:
        all_commits.extend(extract_commits(r))

    duration = calculate_active_duration(timestamps)
    project_path = decode_project_path(project_name)
    abs_files = extract_files_changed(records)
    rel_files = [_to_relative_path(f, project_path) for f in abs_files]

    return {
        "session_id": session_id,
        "project": project_path,
        "start": timestamps[0] if timestamps else None,
        "end": timestamps[-1] if timestamps else None,
        "duration_minutes": duration,
        "first_prompt": extract_first_prompt(records),
        "commits": all_commits,
        "files_changed": rel_files,
        "files_changed_count": len(rel_files),
        "tools_used": extract_tool_usage(records),
        "status": detect_session_status(records, duration_minutes=duration),
        "tokens": extract_tokens(records),
    }


def _aggregate_by_project(sessions: list) -> dict:
    """Group sessions by project path, return project-keyed dict."""
    projects: dict = defaultdict(lambda: {
        "short_name": "",
        "session_ids": [],
        "session_count": 0,
        "duration_minutes": 0,
        "git_commits": [],
        "files_changed_count": 0,
    })

    for s in sessions:
        path = s.get("project", "unknown")
        p = projects[path]
        if not p["short_name"]:
            p["short_name"] = path.rstrip("/").split("/")[-1] if "/" in path else path
        p["session_ids"].append(s["session_id"])
        p["session_count"] += 1
        p["duration_minutes"] += s.get("duration_minutes", 0)

    return dict(projects)


def build_report(
    start: datetime,
    end: datetime,
    timezone_name: str,
    claude_home: Path,
    codex_home: Path,
    project_filter: str | None = None,
) -> dict:
    """Build complete work log report."""
    tz = _get_tz(timezone_name)

    # Scan and parse Claude Code sessions (skip excluded project dirs)
    all_records = []
    for project_name, filepath in scan_session_files(claude_home, start, project_filter):
        if _is_excluded_project(project_name):
            continue
        records = parse_jsonl_file(filepath, start, end)
        for r in records:
            r["_project"] = project_name
        all_records.extend(records)

    # Group by session
    session_groups = group_by_session(all_records)

    # Analyze each session
    sessions = []
    total_tool_usage: dict = defaultdict(int)
    total_tokens = {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0}

    for sid, records in session_groups.items():
        project_name = records[0].get("_project", "unknown")
        analysis = analyze_session(sid, records, project_name, tz)
        sessions.append(analysis)

        for tool, count in analysis["tools_used"].items():
            total_tool_usage[tool] += count
        for key in total_tokens:
            total_tokens[key] += analysis["tokens"].get(key, 0)

    # Filter out observer sessions (by first_prompt pattern)
    sessions = [s for s in sessions if not _is_observer_session(s.get("first_prompt"))]

    # Filter out abandoned sessions (noise)
    sessions = [s for s in sessions if s["status"] != "abandoned"]

    # Sort sessions by start time
    sessions.sort(key=lambda s: s["start"] or "")

    # Parse Codex sessions
    codex_sessions = parse_codex_sessions(codex_home, start, end)

    total_duration = sum(s["duration_minutes"] for s in sessions)
    active_count = len(sessions)

    # Aggregate sessions by project
    projects = _aggregate_by_project(sessions)

    # Collect git data for each project
    total_commits = 0
    for path, proj in projects.items():
        git_commits = collect_git_data(path, start, end)
        proj["git_commits"] = git_commits
        all_git_files = sum(c.get("files_changed", 0) for c in git_commits)
        proj["files_changed_count"] = all_git_files
        total_commits += len(git_commits)

    start_local = start.astimezone(tz)
    end_local = end.astimezone(tz)

    return {
        "period": {
            "start": start_local.isoformat(),
            "end": end_local.isoformat(),
            "timezone": timezone_name,
        },
        "summary": {
            "total_duration_minutes": total_duration,
            "active_sessions": active_count,
            "project_count": len(projects),
            "total_commits": total_commits,
        },
        "projects": projects,
        "sessions": sessions,
        "codex_sessions": codex_sessions,
        "tool_summary": dict(total_tool_usage),
        "token_summary": {
            "total_input": total_tokens["input"],
            "total_output": total_tokens["output"],
            "total_cache_creation": total_tokens["cache_creation"],
            "total_cache_read": total_tokens["cache_read"],
        },
    }


def parse_time_shortcut(
    shortcut: str,
    timezone_name: str,
    end_str: str | None = None,
) -> tuple:
    """Convert time shortcut or date string to (start, end) datetime range.

    Supported shortcuts: today, yesterday, this-week, this-month
    Custom: YYYY-MM-DD (single day), with optional end_str for range
    """
    tz = _get_tz(timezone_name)
    today = datetime.now(tz).date()

    if shortcut == "today":
        d = today
        start = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=tz)
        end = datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=tz)
    elif shortcut == "yesterday":
        d = today - timedelta(days=1)
        start = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=tz)
        end = datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=tz)
    elif shortcut == "this-week":
        # Monday to today
        monday = today - timedelta(days=today.weekday())
        start = datetime(monday.year, monday.month, monday.day, 0, 0, 0, tzinfo=tz)
        end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=tz)
    elif shortcut == "this-month":
        start = datetime(today.year, today.month, 1, 0, 0, 0, tzinfo=tz)
        end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=tz)
    else:
        # Custom date: YYYY-MM-DD
        d = date_type.fromisoformat(shortcut)
        start = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=tz)
        if end_str:
            d2 = date_type.fromisoformat(end_str)
            end = datetime(d2.year, d2.month, d2.day, 23, 59, 59, tzinfo=tz)
        else:
            end = datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=tz)

    return start, end


def parse_args(argv: list | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Generate work diary report from Claude Code session records"
    )
    parser.add_argument(
        "time_range",
        help="Time range: today|yesterday|this-week|this-month|YYYY-MM-DD"
    )
    parser.add_argument(
        "end_date",
        nargs="?",
        default=None,
        help="End date for custom range (YYYY-MM-DD)"
    )
    parser.add_argument("--timezone", default="Asia/Taipei", help="Timezone name (default: Asia/Taipei)")
    parser.add_argument("--project", default=None, help="Filter by project name substring")
    parser.add_argument("--claude-home", default=str(Path.home() / ".claude"), help="Path to ~/.claude")
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"), help="Path to ~/.codex")
    return parser.parse_args(argv)


def main(argv: list | None = None) -> None:
    """CLI entry point. Outputs JSON to stdout."""
    args = parse_args(argv)
    start, end = parse_time_shortcut(args.time_range, args.timezone, args.end_date)

    report = build_report(
        start=start,
        end=end,
        timezone_name=args.timezone,
        claude_home=Path(args.claude_home),
        codex_home=Path(args.codex_home),
        project_filter=args.project,
    )

    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    print()  # trailing newline


if __name__ == "__main__":
    main()

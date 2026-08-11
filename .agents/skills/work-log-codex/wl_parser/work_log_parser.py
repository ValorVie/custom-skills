"""Build structured work-log JSON from Claude and Codex session history."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date as date_type
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scripts.source_claude import load_claude_events
from scripts.source_codex import load_codex_events
from wl_parser.git_collector import collect_git_data


COMPLETION_KEYWORDS = re.compile(
    r"完成|已完成|已提交|done|completed|committed|finished|shipped",
    re.IGNORECASE,
)
SYSTEM_TAG_PATTERNS = (
    re.compile(r"^<"),
    re.compile(r"\bI'?m using the\b", re.IGNORECASE),
    re.compile(r"^我已讀", re.IGNORECASE),
)
NOISE_HINT_PATTERNS = (
    re.compile(r"^# AGENTS\.md instructions", re.IGNORECASE),
    re.compile(r"^#\s*Find Skills\b", re.IGNORECASE),
    re.compile(r"^#\s*Brainstorming Ideas Into Designs\b", re.IGNORECASE),
    re.compile(
        r"^#{1,3}\s*(Overview|When to Use This Skill|讀取規則|記錄規則|使用方式|Workflow|Commands|Output Rules|References)\b",
        re.IGNORECASE,
    ),
    re.compile(r"^##\s*知識庫與經驗協議\b", re.IGNORECASE),
    re.compile(r"^##\s*Analysis Report:", re.IGNORECASE),
    re.compile(r"^對話開始時，SessionStart hook", re.IGNORECASE),
    re.compile(r"^Invoke the superpowers:", re.IGNORECASE),
    re.compile(r"^Launching skill:", re.IGNORECASE),
    re.compile(r"^Base directory for this skill:", re.IGNORECASE),
    re.compile(r"^Web search results for query:", re.IGNORECASE),
    re.compile(r"^No matching deferred tools found$", re.IGNORECASE),
    re.compile(r"^SessionStart hook", re.IGNORECASE),
    re.compile(r"^This skill helps you", re.IGNORECASE),
    re.compile(r"^Use this skill when", re.IGNORECASE),
    re.compile(r"^Step \d+[:：]", re.IGNORECASE),
    re.compile(r"^ARGUMENTS:", re.IGNORECASE),
    re.compile(r"^Perfect!", re.IGNORECASE),
    re.compile(r"^完美！", re.IGNORECASE),
    re.compile(r"^I now have (?:a|the) complete picture", re.IGNORECASE),
    re.compile(r"^Implement the following plan:", re.IGNORECASE),
    re.compile(r"^使用 \*\*[^*]+\*\* 技能", re.IGNORECASE),
    re.compile(r"^被 AI 找到$", re.IGNORECASE),
    re.compile(r"^---+$"),
    re.compile(r"^```"),
    re.compile(r"^⏺"),
    re.compile(r"^\x1b"),
    re.compile(r"^total \d+$", re.IGNORECASE),
    re.compile(r"^/Users/"),
    re.compile(r"^\[(Confirmed|Inferred|Recommended|Unknown|Assumption)\]"),
)


def parse_timestamp(ts_str: str) -> datetime:
    """Parse ISO-8601 timestamp to aware datetime."""
    parsed = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return parsed


def _get_tz(timezone_name: str):
    from zoneinfo import ZoneInfo

    try:
        return ZoneInfo(timezone_name)
    except (KeyError, Exception):
        return timezone.utc


def parse_time_shortcut(
    shortcut: str,
    timezone_name: str,
    end_str: str | None = None,
) -> tuple[datetime, datetime]:
    """Convert shortcut or YYYY-MM-DD date range into local datetimes."""
    tz = _get_tz(timezone_name)
    today = datetime.now(tz).date()

    if shortcut == "today":
        start = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=tz)
        end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=tz)
    elif shortcut == "yesterday":
        date = today - timedelta(days=1)
        start = datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=tz)
        end = datetime(date.year, date.month, date.day, 23, 59, 59, tzinfo=tz)
    elif shortcut == "this-week":
        monday = today - timedelta(days=today.weekday())
        start = datetime(monday.year, monday.month, monday.day, 0, 0, 0, tzinfo=tz)
        end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=tz)
    elif shortcut == "this-month":
        start = datetime(today.year, today.month, 1, 0, 0, 0, tzinfo=tz)
        end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=tz)
    else:
        date = date_type.fromisoformat(shortcut)
        start = datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=tz)
        if end_str:
            end_date = date_type.fromisoformat(end_str)
            end = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=tz)
        else:
            end = datetime(date.year, date.month, date.day, 23, 59, 59, tzinfo=tz)

    return start, end


def _compact_text(value: str | None, limit: int = 200) -> str | None:
    if not value:
        return None
    normalized = " ".join(value.split())
    if not normalized:
        return None
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1] + "…"


def _first_meaningful_line(text: str | None, limit: int = 200) -> str | None:
    if not text:
        return None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if any(pattern.search(line) for pattern in SYSTEM_TAG_PATTERNS):
            continue
        if any(pattern.search(line) for pattern in NOISE_HINT_PATTERNS):
            continue
        if len(line) > limit:
            return line[: limit - 1] + "…"
        return line
    return None


def _event_role(event: dict[str, Any]) -> str | None:
    event_type = event.get("event_type")
    if event_type in {"user", "assistant"}:
        return event_type

    raw = event.get("raw", {})
    if not isinstance(raw, dict):
        return None

    if event.get("tool") == "codex":
        payload = raw.get("payload", {})
        if isinstance(payload, dict):
            if payload.get("type") == "message":
                role = payload.get("role")
                if isinstance(role, str) and role:
                    return role
        title = event.get("title")
        if isinstance(title, str) and title in {"user", "assistant"}:
            return title
        return None

    message = raw.get("message")
    if isinstance(message, dict):
        role = message.get("role")
        if isinstance(role, str) and role:
            return role
    return None


def _extract_tool_usage(events: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for event in events:
        raw = event.get("raw", {})
        if not isinstance(raw, dict):
            continue

        if event.get("tool") == "claude":
            if event.get("event_type") == "tool_use":
                name = raw.get("tool_name") or raw.get("name")
                if isinstance(name, str) and name:
                    counts[name] += 1
                    continue
            message = raw.get("message")
            content = message.get("content", []) if isinstance(message, dict) else []
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use":
                        name = block.get("name")
                        if isinstance(name, str) and name:
                            counts[name] += 1
        else:
            payload = raw.get("payload", {})
            if isinstance(payload, dict):
                payload_type = payload.get("type")
                if payload_type in {"function_call", "tool_call"}:
                    name = payload.get("name")
                    if isinstance(name, str) and name:
                        counts[name] += 1
                if payload_type == "message":
                    content = payload.get("content", [])
                    if isinstance(content, list):
                        for item in content:
                            if not isinstance(item, dict):
                                continue
                            item_type = item.get("type")
                            if item_type in {"tool_call", "function_call"}:
                                name = item.get("name")
                                if isinstance(name, str) and name:
                                    counts[name] += 1

    return dict(counts)


def _extract_tokens(events: list[dict[str, Any]]) -> dict[str, int]:
    totals = {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0}
    for event in events:
        raw = event.get("raw", {})
        if not isinstance(raw, dict):
            continue

        usage = raw.get("usage")
        if event.get("tool") == "claude" and not isinstance(usage, dict):
            message = raw.get("message")
            if isinstance(message, dict):
                usage = message.get("usage")
        elif event.get("tool") == "codex" and not isinstance(usage, dict):
            payload = raw.get("payload")
            if isinstance(payload, dict):
                usage = payload.get("usage")
        if not isinstance(usage, dict):
            continue

        totals["input"] += int(usage.get("input_tokens", 0) or 0)
        totals["output"] += int(usage.get("output_tokens", 0) or 0)
        totals["cache_creation"] += int(usage.get("cache_creation_input_tokens", 0) or 0)
        totals["cache_read"] += int(usage.get("cache_read_input_tokens", 0) or 0)

    return totals


def _extract_command_strings(value: Any) -> list[str]:
    commands: list[str] = []
    if isinstance(value, str):
        if "git commit" in value:
            commands.append(value)
        return commands
    if isinstance(value, dict):
        for nested in value.values():
            commands.extend(_extract_command_strings(nested))
        return commands
    if isinstance(value, list):
        for nested in value:
            commands.extend(_extract_command_strings(nested))
    return commands


def _extract_commit_messages(events: list[dict[str, Any]]) -> list[str]:
    messages: list[str] = []
    for event in events:
        raw = event.get("raw", {})
        if not isinstance(raw, dict):
            continue
        for command in _extract_command_strings(raw):
            simple = re.search(r'git commit\s+-m\s+["\']([^"\']+)["\']', command)
            if simple:
                msg = simple.group(1).splitlines()[0].strip()
                if msg and msg not in messages:
                    messages.append(msg)
                continue
            heredoc = re.search(
                r"cat\s*<<['\"]?EOF['\"]?\s*(?:\\n|\n)(.+?)(?:\\n|\n).*?EOF",
                command,
                re.DOTALL,
            )
            if heredoc:
                msg = heredoc.group(1).splitlines()[0].strip()
                if msg and msg not in messages:
                    messages.append(msg)
    return messages


def _select_project_path(events: list[dict[str, Any]]) -> str | None:
    candidates = [
        event.get("project_path")
        for event in events
        if isinstance(event.get("project_path"), str) and event.get("project_path")
    ]
    if not candidates:
        return None
    counts = Counter(candidates)
    return counts.most_common(1)[0][0]


def calculate_active_duration(
    timestamps: list[str], idle_threshold_minutes: int = 30
) -> int:
    """Calculate active duration in minutes with idle-gap splitting."""
    if len(timestamps) < 2:
        return 0
    datetimes = sorted(parse_timestamp(value) for value in timestamps)
    threshold = timedelta(minutes=idle_threshold_minutes)

    total_minutes = 0
    segment_start = datetimes[0]
    prev = datetimes[0]
    for current in datetimes[1:]:
        if current - prev > threshold:
            total_minutes += int((prev - segment_start).total_seconds() / 60)
            segment_start = current
        prev = current
    total_minutes += int((prev - segment_start).total_seconds() / 60)
    return total_minutes


def _calculate_duration_for_events(events: list[dict[str, Any]]) -> int:
    timestamps = [event["timestamp"] for event in events if event.get("timestamp")]
    return calculate_active_duration(timestamps)


def _session_is_subagent(events: list[dict[str, Any]]) -> bool:
    return any(bool(event.get("is_subagent")) for event in events)


def _local_date_key(timestamp: str | None, tz) -> str | None:
    if not timestamp:
        return None
    try:
        return parse_timestamp(timestamp).astimezone(tz).strftime("%Y-%m-%d")
    except ValueError:
        return None


def _build_daily_summary(
    sessions: list[dict[str, Any]], events: list[dict[str, Any]], tz
) -> list[dict[str, Any]]:
    session_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    event_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for session in sessions:
        date_key = _local_date_key(session.get("start"), tz)
        if date_key:
            session_groups[date_key].append(session)

    for event in events:
        date_key = _local_date_key(event.get("timestamp"), tz)
        if date_key:
            event_groups[date_key].append(event)

    daily_summary: list[dict[str, Any]] = []
    for date_key in sorted(set(session_groups) | set(event_groups)):
        day_sessions = session_groups.get(date_key, [])
        if not day_sessions:
            continue
        daily_summary.append(
            {
                "date": date_key,
                "session_count": len(day_sessions),
                "total_duration_minutes": _calculate_duration_for_events(event_groups.get(date_key, [])),
                "total_commits": sum(len(session.get("commits", [])) for session in day_sessions),
            }
        )
    return daily_summary


def _session_group_key(event: dict[str, Any]) -> str:
    session_id = event.get("session_id")
    if isinstance(session_id, str) and session_id:
        return f"{event.get('tool', 'unknown')}::{session_id}"
    return f"{event.get('tool', 'unknown')}::{event.get('evidence_path', 'unknown')}"


def _detect_session_status(
    events: list[dict[str, Any]], commits: list[str], duration_minutes: int
) -> str:
    if commits:
        return "completed"
    assistant_texts = [
        event.get("text")
        for event in reversed(events)
        if _event_role(event) == "assistant" and isinstance(event.get("text"), str)
    ]
    if assistant_texts and COMPLETION_KEYWORDS.search(assistant_texts[0] or ""):
        return "completed"
    tool_count = sum(_extract_tool_usage(events).values())
    if tool_count > 0 or duration_minutes > 2:
        return "in_progress"
    return "abandoned"


def _dedupe_strings(values: list[str], limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
        if limit is not None and len(result) >= limit:
            break
    return result


def analyze_session(session_key: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze grouped session events into a compact session record."""
    events = sorted(events, key=lambda item: item.get("timestamp") or "")
    timestamps = [event["timestamp"] for event in events if event.get("timestamp")]
    first_prompt = None
    closing_note = None

    for event in events:
        text = _first_meaningful_line(event.get("text"))
        if not text:
            continue
        role = _event_role(event)
        if role == "user":
            if first_prompt is None:
                first_prompt = text
        elif role == "assistant":
            closing_note = text

    commits = _extract_commit_messages(events)
    duration = calculate_active_duration(timestamps)
    project_path = _select_project_path(events)
    tool_usage = _extract_tool_usage(events)
    status = _detect_session_status(events, commits, duration)
    is_subagent = _session_is_subagent(events)

    return {
        "group_key": session_key,
        "session_id": session_key.split("::", 1)[1],
        "source": events[0].get("tool"),
        "project": project_path or "unknown",
        "start": timestamps[0] if timestamps else None,
        "end": timestamps[-1] if timestamps else None,
        "duration_minutes": duration,
        "is_subagent": is_subagent,
        "first_prompt": first_prompt,
        "closing_note": closing_note,
        "session_hints": _dedupe_strings(
            ([first_prompt] if first_prompt else []) + ([closing_note] if closing_note else []),
            limit=2,
        ),
        "commits": commits,
        "tools_used": tool_usage,
        "status": status,
        "tokens": _extract_tokens(events),
        "evidence_paths": _dedupe_strings(
            [str(event.get("evidence_path")) for event in events if event.get("evidence_path")]
        ),
    }


def _project_short_name(path: str) -> str:
    if not path:
        return "unknown"
    return path.rstrip("/").split("/")[-1] if "/" in path else path


def _path_tail(path: str, depth: int) -> str:
    parts = [part for part in Path(path).parts if part not in {"/", ""}]
    if not parts:
        return "unknown"
    return "/".join(parts[-depth:])


def _assign_display_names(projects: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for path, project in projects.items():
        short_name = project.get("short_name") or _project_short_name(path)
        groups[short_name].append(path)

    for short_name, paths in groups.items():
        if len(paths) == 1:
            projects[paths[0]]["display_name"] = short_name
            continue

        max_depth = max(
            len([part for part in Path(path).parts if part not in {"/", ""}])
            for path in paths
        )
        for depth in range(2, max_depth + 1):
            candidate_map = {path: _path_tail(path, depth) for path in paths}
            if len(set(candidate_map.values())) == len(paths):
                for path, display_name in candidate_map.items():
                    projects[path]["display_name"] = display_name
                break
        else:
            for path in paths:
                projects[path]["display_name"] = path.lstrip("/") or short_name

    return projects


def _aggregate_by_project(sessions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    projects: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "short_name": "",
            "session_ids": [],
            "session_count": 0,
            "duration_minutes": 0,
            "git_commits": [],
            "files_touched": [],
            "session_hints": [],
            "sources": [],
            "status_counts": {"completed": 0, "in_progress": 0, "abandoned": 0},
            "time_span": {"start": None, "end": None},
        }
    )

    for session in sessions:
        path = session.get("project", "unknown") or "unknown"
        project = projects[path]
        if not project["short_name"]:
            project["short_name"] = _project_short_name(path)
        project["session_ids"].append(session["session_id"])
        project["session_count"] += 1
        project["duration_minutes"] += session.get("duration_minutes", 0)
        source = session.get("source")
        if isinstance(source, str) and source and source not in project["sources"]:
            project["sources"].append(source)
        hints = session.get("session_hints", [])
        if isinstance(hints, list):
            project["session_hints"].extend(hints)
        status = session.get("status", "in_progress")
        if status not in project["status_counts"]:
            project["status_counts"][status] = 0
        project["status_counts"][status] += 1

        start = session.get("start")
        end = session.get("end")
        if start and (
            project["time_span"]["start"] is None or start < project["time_span"]["start"]
        ):
            project["time_span"]["start"] = start
        if end and (project["time_span"]["end"] is None or end > project["time_span"]["end"]):
            project["time_span"]["end"] = end

    for project in projects.values():
        project["session_hints"] = _dedupe_strings(project["session_hints"], limit=8)

    return dict(projects)


def _apply_project_union_durations(
    projects: dict[str, dict[str, Any]], events: list[dict[str, Any]]
) -> None:
    events_by_project: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        path = event.get("project_path")
        key = path if isinstance(path, str) and path else "unknown"
        events_by_project[key].append(event)

    for path, project in projects.items():
        project["duration_minutes"] = _calculate_duration_for_events(events_by_project.get(path, []))


def _filter_project_map(
    projects: dict[str, dict[str, Any]], project_filter: str | None
) -> dict[str, dict[str, Any]]:
    if not project_filter:
        return projects
    filtered: dict[str, dict[str, Any]] = {}
    needle = project_filter.lower()
    for path, project in projects.items():
        if needle in path.lower() or needle in project.get("short_name", "").lower():
            filtered[path] = project
    return filtered


def _parse_codex_index_sessions(
    codex_home: Path, start: datetime, end: datetime
) -> list[dict[str, str]]:
    index_file = codex_home / "session_index.jsonl"
    if not index_file.exists():
        return []
    sessions: list[dict[str, str]] = []
    for line in index_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        updated_at = row.get("updated_at")
        if not isinstance(updated_at, str):
            continue
        try:
            updated_dt = parse_timestamp(updated_at)
        except ValueError:
            continue
        if start <= updated_dt <= end:
            title = row.get("thread_name")
            sessions.append(
                {
                    "thread_name": title if isinstance(title, str) else "",
                    "updated_at": updated_at,
                }
            )
    return sessions


def _emit_project_bundles(report: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "summary": report.get("summary", {}),
        "period": report.get("period", {}),
        "projects": [],
    }
    all_sessions = report.get("sessions", [])

    for project_path, project in report.get("projects", {}).items():
        project_sessions = [
            {
                "session_id": session.get("session_id"),
                "source": session.get("source"),
                "start": session.get("start"),
                "end": session.get("end"),
                "duration_minutes": session.get("duration_minutes"),
                "status": session.get("status"),
                "first_prompt": session.get("first_prompt"),
                "closing_note": session.get("closing_note"),
                "session_hints": session.get("session_hints", []),
                "commits": session.get("commits", []),
                "tools_used": session.get("tools_used", {}),
                "evidence_paths": session.get("evidence_paths", []),
            }
            for session in all_sessions
            if session.get("project") == project_path
        ]
        bundle = {
            "project_path": project_path,
            "short_name": project.get("short_name"),
            "display_name": project.get("display_name") or project.get("short_name"),
            "duration_minutes": project.get("duration_minutes"),
            "session_count": project.get("session_count"),
            "sources": project.get("sources", []),
            "time_span": project.get("time_span", {}),
            "status_counts": project.get("status_counts", {}),
            "session_hints": project.get("session_hints", []),
            "session_summaries": project_sessions,
            "files_touched": project.get("files_touched", []),
            "git_commits": project.get("git_commits", []),
        }
        slug_source = project.get("display_name") or project.get("short_name") or "project"
        slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", slug_source).strip("-")
        if not slug:
            slug = "project"
        file_path = output_dir / f"{slug}.json"
        file_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest["projects"].append(
            {
                "short_name": bundle["short_name"],
                "display_name": bundle["display_name"],
                "path": str(file_path),
            }
        )

    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_report(
    start: datetime,
    end: datetime,
    timezone_name: str,
    claude_home: Path,
    codex_home: Path,
    project_filter: str | None = None,
) -> dict[str, Any]:
    """Build the structured report JSON."""
    tz = _get_tz(timezone_name)

    try:
        claude_events = load_claude_events(claude_home)
    except Exception:  # pragma: no cover - defensive loader isolation
        claude_events = []
    try:
        codex_events_raw = load_codex_events(codex_home)
    except Exception:  # pragma: no cover - defensive loader isolation
        codex_events_raw = []
    codex_events = [
        event
        for event in codex_events_raw
        if isinstance(event.get("timestamp"), str)
        and (
            event.get("confidence") == "high"
            or "/sessions/" in str(event.get("evidence_path", ""))
        )
    ]

    all_events = claude_events + codex_events
    filtered_events = []
    for event in all_events:
        timestamp = event.get("timestamp")
        if not isinstance(timestamp, str):
            continue
        try:
            parsed = parse_timestamp(timestamp)
        except ValueError:
            continue
        if start <= parsed <= end:
            filtered_events.append(event)

    session_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in filtered_events:
        session_groups[_session_group_key(event)].append(event)

    sessions = [
        analyze_session(session_key, grouped)
        for session_key, grouped in session_groups.items()
    ]
    sessions = [session for session in sessions if session["status"] != "abandoned"]
    sessions.sort(key=lambda session: session.get("start") or "")

    active_session_keys = {session["group_key"] for session in sessions}
    active_events = [
        event for event in filtered_events if _session_group_key(event) in active_session_keys
    ]
    main_sessions = [session for session in sessions if not session.get("is_subagent")]
    subagent_sessions = [session for session in sessions if session.get("is_subagent")]

    projects = _aggregate_by_project(main_sessions)
    _apply_project_union_durations(projects, active_events)
    projects = _filter_project_map(projects, project_filter)
    projects = _assign_display_names(projects)

    if project_filter:
        allowed_paths = set(projects.keys())
        main_sessions = [session for session in main_sessions if session.get("project") in allowed_paths]
        subagent_sessions = [
            session for session in subagent_sessions if session.get("project") in allowed_paths
        ]
        active_events = [
            event
            for event in active_events
            if (event.get("project_path") or "unknown") in allowed_paths
        ]
        _apply_project_union_durations(projects, active_events)

    total_commits = 0
    for path, project in projects.items():
        git_commits = collect_git_data(path, start, end)
        project["git_commits"] = git_commits
        total_commits += len(git_commits)
        touched_files = _dedupe_strings(
            [file for commit in git_commits for file in commit.get("files", [])],
            limit=20,
        )
        project["files_touched"] = touched_files

    total_tokens = {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0}
    total_tool_usage: Counter[str] = Counter()
    for session in sessions:
        for key in total_tokens:
            total_tokens[key] += int(session.get("tokens", {}).get(key, 0) or 0)
        for tool_name, count in session.get("tools_used", {}).items():
            total_tool_usage[tool_name] += count

    total_duration = _calculate_duration_for_events(active_events)
    daily_summary = _build_daily_summary(main_sessions, active_events, tz)
    subagent_duration = sum(session.get("duration_minutes", 0) for session in subagent_sessions)
    codex_sessions = _parse_codex_index_sessions(codex_home, start, end)
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
            "active_sessions": len(main_sessions),
            "project_count": len(projects),
            "total_commits": total_commits,
            "subagent_sessions": len(subagent_sessions),
            "subagent_duration_minutes": subagent_duration,
            "sources": sorted({source for project in projects.values() for source in project.get("sources", [])}),
        },
        "projects": projects,
        "sessions": main_sessions,
        "subagent_sessions": subagent_sessions,
        "daily_summary": daily_summary,
        "codex_sessions": codex_sessions,
        "tool_summary": dict(total_tool_usage),
        "token_summary": {
            "total_input": total_tokens["input"],
            "total_output": total_tokens["output"],
            "total_cache_creation": total_tokens["cache_creation"],
            "total_cache_read": total_tokens["cache_read"],
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate work log data from Claude and Codex sessions"
    )
    parser.add_argument(
        "time_range",
        help="Time range: today|yesterday|this-week|this-month|YYYY-MM-DD",
    )
    parser.add_argument(
        "end_date",
        nargs="?",
        default=None,
        help="End date for custom range (YYYY-MM-DD)",
    )
    parser.add_argument("--timezone", default="Asia/Taipei")
    parser.add_argument("--project", default=None)
    parser.add_argument("--claude-home", default=str(Path.home() / ".claude"))
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    parser.add_argument("--emit-project-dir", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
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
    if args.emit_project_dir:
        _emit_project_bundles(report, Path(args.emit_project_dir))
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()

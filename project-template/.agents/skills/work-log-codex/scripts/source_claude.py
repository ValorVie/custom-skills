from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any


def _is_subagent_path(file_path: Path) -> bool:
    return "subagents" in file_path.parts


def _read_jsonl(file_path: Path) -> list[dict[str, Any]]:
    if not file_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except JSONDecodeError:
            continue
    return rows


def _extract_text(content: Any) -> str | None:
    if isinstance(content, str):
        return content.strip() or None
    if isinstance(content, (list, dict)):
        for key in ("message", "tool_input", "tool_output", "data"):
            if isinstance(content, dict) and key in content:
                nested = _extract_text(content.get(key))
                if nested:
                    return nested
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        if parts:
            return "\n".join(parts)
    if isinstance(content, dict):
        for key in ("text", "content", "command", "description", "output"):
            value = content.get(key)
            nested = _extract_text(value)
            if nested:
                return nested
        if any(key in content for key in ("tool_input", "tool_output")):
            try:
                return json.dumps(content, ensure_ascii=False, sort_keys=True)
            except TypeError:
                return str(content)
    return None


def _extract_title(text: str | None) -> str | None:
    if not text:
        return None
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    return first_line or None


def load_claude_history_entries(history_file: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for row in _read_jsonl(history_file):
        project = row.get("project")
        if not project:
            continue
        entries.append(
            {
                "display": row.get("display"),
                "project": project,
                "timestamp": row.get("timestamp", 0),
            }
        )
    return entries


def _build_display_project_map(
    history_entries: list[dict[str, Any]],
) -> tuple[dict[str, str], str | None]:
    display_to_project: dict[str, str] = {}
    latest_project: str | None = None
    latest_timestamp = -1

    for entry in history_entries:
        project = entry["project"]
        timestamp = int(entry.get("timestamp") or 0)
        display = entry.get("display")

        if isinstance(display, str) and display.strip():
            display_to_project[display.strip()] = project

        if timestamp >= latest_timestamp:
            latest_timestamp = timestamp
            latest_project = project

    return display_to_project, latest_project


def _match_project_from_text(
    text: str | None, display_to_project: dict[str, str]
) -> str | None:
    if not text:
        return None
    stripped = text.strip()
    if not stripped:
        return None
    return display_to_project.get(stripped)


def _infer_transcript_project(
    rows: list[dict[str, Any]], display_to_project: dict[str, str], latest_project: str | None
) -> tuple[str | None, str]:
    for row in rows:
        text = _extract_text(row.get("content")) or _extract_text(row)
        matched = _match_project_from_text(text, display_to_project)
        if matched:
            return matched, "high"
    if latest_project:
        return latest_project, "low"
    return None, "low"


def _extract_tmp_session_events(root: Path, latest_project: str | None) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    sessions_dir = root / "sessions"
    if not sessions_dir.exists():
        return events

    for file_path in sorted(sessions_dir.glob("*-session.tmp")):
        current_section: str | None = None
        lines = file_path.read_text(encoding="utf-8").splitlines()
        date_text = file_path.stem.replace("-session", "")
        timestamp = f"{date_text}T00:00:00"
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("### "):
                current_section = stripped.removeprefix("### ").strip()
                continue
            if stripped.startswith("-"):
                text = stripped.removeprefix("-").strip()
                if not text or text == "[ ]":
                    continue
                events.append(
                    {
                        "tool": "claude",
                        "session_id": file_path.stem,
                        "project_path": latest_project,
                        "cwd": None,
                        "timestamp": timestamp,
                        "event_type": "session_note",
                        "title": current_section,
                        "text": text,
                        "evidence_path": str(file_path),
                        "confidence": "low",
                        "is_subagent": False,
                        "raw": {"section": current_section, "text": text},
                    }
                )
    return events


def _should_skip_project_file(file_path: Path) -> bool:
    text = str(file_path)
    if "observer-sessions" in text:
        return True
    if file_path.name == "sessions-index.json":
        return True
    return False


def _extract_project_file_events(file_path: Path, latest_project: str | None) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for row in _read_jsonl(file_path):
        text = _extract_text(row.get("message")) or _extract_text(row.get("content")) or _extract_text(row.get("data"))
        cwd = row.get("cwd")
        project_path = cwd if isinstance(cwd, str) and cwd.strip() else latest_project
        confidence = "medium" if project_path else "low"
        events.append(
            {
                "tool": "claude",
                "session_id": row.get("sessionId") or file_path.stem,
                "project_path": project_path,
                "cwd": cwd if isinstance(cwd, str) and cwd.strip() else None,
                "timestamp": row.get("timestamp"),
                "event_type": row.get("type"),
                "title": _extract_title(text),
                "text": text,
                "evidence_path": str(file_path),
                "confidence": confidence,
                "is_subagent": _is_subagent_path(file_path),
                "raw": row,
            }
        )
    return events


def _extract_project_fallback_events(root: Path, latest_project: str | None) -> list[dict[str, Any]]:
    projects_dir = root / "projects"
    if not projects_dir.exists():
        return []

    events: list[dict[str, Any]] = []
    for file_path in sorted(projects_dir.rglob("*.jsonl")):
        if _should_skip_project_file(file_path):
            continue
        events.extend(_extract_project_file_events(file_path, latest_project))
    return events


def _dedupe_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for event in events:
        key = (
            event.get("session_id"),
            event.get("project_path"),
            event.get("timestamp"),
            event.get("event_type"),
            event.get("text"),
            event.get("evidence_path"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)
    return deduped


def load_claude_events(root: Path) -> list[dict[str, Any]]:
    history_entries = load_claude_history_entries(root / "history.jsonl")
    display_to_project, latest_project = _build_display_project_map(history_entries)
    events: list[dict[str, Any]] = []

    transcripts_dir = root / "transcripts"
    if not transcripts_dir.exists():
        events.extend(_extract_tmp_session_events(root, latest_project))
        events.extend(_extract_project_fallback_events(root, latest_project))
        return _dedupe_events(events)

    for file_path in sorted(transcripts_dir.glob("*.jsonl")):
        session_id = file_path.stem
        rows = _read_jsonl(file_path)
        session_project, session_confidence = _infer_transcript_project(
            rows, display_to_project, latest_project
        )
        for row in rows:
            text = _extract_text(row.get("content")) or _extract_text(row)
            matched_project = _match_project_from_text(text, display_to_project)
            project_path = matched_project or session_project
            confidence = "high" if matched_project else session_confidence
            events.append(
                {
                    "tool": "claude",
                    "session_id": session_id,
                    "project_path": project_path,
                    "cwd": row.get("cwd"),
                    "timestamp": row.get("timestamp"),
                    "event_type": row.get("type"),
                    "title": _extract_title(text),
                    "text": text,
                    "evidence_path": str(file_path),
                    "confidence": confidence,
                    "is_subagent": _is_subagent_path(file_path),
                    "raw": row,
                }
            )

    events.extend(_extract_tmp_session_events(root, latest_project))
    events.extend(_extract_project_fallback_events(root, latest_project))

    return _dedupe_events(events)

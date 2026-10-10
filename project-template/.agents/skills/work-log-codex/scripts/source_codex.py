from __future__ import annotations

import json
from datetime import datetime, timedelta
from json import JSONDecodeError
from pathlib import Path
from typing import Any


MAX_EVENT_TEXT_CHARS = 8192
MAX_RAW_ARGUMENT_CHARS = 16384


def _trim_text(value: str | None, limit: int = MAX_EVENT_TEXT_CHARS) -> str | None:
    if not value:
        return None
    if len(value) <= limit:
        return value
    return value[:limit] + "…"


def _parse_timestamp(value: Any) -> datetime | None:
    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 10_000_000_000:
            timestamp /= 1000
        return datetime.fromtimestamp(timestamp).astimezone()
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone() if parsed.tzinfo is None else parsed
    except ValueError:
        return None


def _in_window(value: Any, start: datetime | None, end: datetime | None) -> bool:
    if start is None or end is None:
        return True
    parsed = _parse_timestamp(value)
    if parsed is None:
        return False
    return start <= parsed <= end


def _iter_jsonl(file_path: Path):
    if not file_path.exists():
        return
    with file_path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            row = _safe_json_loads(line)
            if row is not None:
                yield row


def _compact_argument(value: Any) -> Any:
    if isinstance(value, str):
        return _trim_text(value, MAX_RAW_ARGUMENT_CHARS)
    if isinstance(value, dict):
        compact: dict[str, Any] = {}
        for key in ("cmd", "command", "chars", "name", "description"):
            if key in value:
                compact[key] = _compact_argument(value[key])
        return compact
    if isinstance(value, list):
        return [_compact_argument(item) for item in value[:20]]
    return value if isinstance(value, (int, float, bool)) or value is None else None


def _compact_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    compact: dict[str, Any] = {}
    for key in ("type", "role", "name", "usage"):
        if key in payload:
            compact[key] = payload[key]
    for key in ("arguments", "input", "command"):
        if key in payload:
            compact[key] = _compact_argument(payload[key])
    content = payload.get("content")
    if isinstance(content, list):
        compact_content = []
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") not in {"tool_call", "function_call"}:
                continue
            compact_content.append(
                {
                    key: item[key]
                    for key in ("type", "name")
                    if key in item
                }
            )
        if compact_content:
            compact["content"] = compact_content
    return compact


def _compact_raw(row: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    if isinstance(row.get("usage"), dict):
        compact["usage"] = row["usage"]
    payload = _compact_payload(row.get("payload"))
    if payload:
        compact["payload"] = payload
    return compact


def _extract_message_text(payload: dict[str, Any]) -> str | None:
    if payload.get("type") != "message":
        return None
    content = payload.get("content")
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type")
            if item_type in {"input_text", "output_text", "text"}:
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        if parts:
            return "\n".join(parts)

    text = payload.get("text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    return None


def _extract_title(row: dict[str, Any]) -> str | None:
    payload = row.get("payload")
    if isinstance(payload, dict):
        role = payload.get("role")
        if isinstance(role, str) and role:
            return role

        payload_type = payload.get("type")
        if isinstance(payload_type, str) and payload_type:
            return payload_type

    return None


def _extract_text(row: dict[str, Any]) -> str | None:
    payload = row.get("payload")
    if isinstance(payload, dict):
        text = _extract_message_text(payload)
        if text:
            return _trim_text(text)

    return None


def _build_event(
    row: dict[str, Any],
    file_path: Path,
    session_id: str | None,
    cwd: str | None,
    is_subagent: bool,
) -> dict[str, Any]:
    project_path = cwd
    return {
        "tool": "codex",
        "session_id": session_id,
        "project_path": project_path,
        "cwd": cwd,
        "timestamp": row.get("timestamp"),
        "event_type": row.get("type"),
        "title": _extract_title(row),
        "text": _extract_text(row),
        "evidence_path": str(file_path),
        "confidence": "high" if session_id else "medium",
        "is_subagent": is_subagent,
        "raw": _compact_raw(row),
    }


def _safe_json_loads(raw_line: str) -> dict[str, Any] | None:
    try:
        return json.loads(raw_line)
    except JSONDecodeError:
        return None


def _load_history_events(
    root_path: Path,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[dict[str, Any]]:
    history_file = root_path / "history.jsonl"
    if not history_file.exists():
        return []
    events: list[dict[str, Any]] = []
    for row in _iter_jsonl(history_file):
        if not _in_window(row.get("ts"), start, end):
            continue
        text = row.get("text")
        events.append(
            {
                "tool": "codex",
                "session_id": row.get("session_id"),
                "project_path": None,
                "cwd": None,
                "timestamp": row.get("ts"),
                "event_type": "history",
                "title": text.splitlines()[0].strip() if isinstance(text, str) and text.strip() else None,
                "text": text if isinstance(text, str) and text.strip() else None,
                "evidence_path": str(history_file),
                "confidence": "low",
                "is_subagent": False,
                "raw": {
                    "text": _trim_text(text) if isinstance(text, str) else None,
                },
            }
        )
    return events


def _load_index_events(
    root_path: Path,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[dict[str, Any]]:
    index_file = root_path / "session_index.jsonl"
    if not index_file.exists():
        return []
    events: list[dict[str, Any]] = []
    for row in _iter_jsonl(index_file):
        if not _in_window(row.get("updated_at"), start, end):
            continue
        title = row.get("thread_name")
        events.append(
            {
                "tool": "codex",
                "session_id": row.get("id"),
                "project_path": None,
                "cwd": None,
                "timestamp": row.get("updated_at"),
                "event_type": "session_index",
                "title": title if isinstance(title, str) and title.strip() else None,
                "text": title if isinstance(title, str) and title.strip() else None,
                "evidence_path": str(index_file),
                "confidence": "low",
                "is_subagent": False,
                "raw": {
                    "id": row.get("id"),
                    "thread_name": _trim_text(title) if isinstance(title, str) else None,
                },
            }
        )
    return events


def _session_file_date(file_path: Path) -> datetime | None:
    try:
        year, month, day = file_path.parts[-4:-1]
        return datetime(int(year), int(month), int(day)).astimezone()
    except (TypeError, ValueError):
        return None


def _candidate_session_files(
    session_root: Path,
    start: datetime | None,
    end: datetime | None,
) -> list[Path]:
    files: list[Path] = []
    for file_path in session_root.rglob("*.jsonl"):
        if start is None or end is None:
            files.append(file_path)
            continue
        path_date = _session_file_date(file_path)
        if path_date is not None and path_date.date() > (end + timedelta(days=1)).date():
            continue
        if path_date is not None and path_date.date() < (start - timedelta(days=1)).date():
            try:
                if file_path.stat().st_mtime < start.timestamp():
                    continue
            except OSError:
                continue
        files.append(file_path)
    return sorted(files)


def load_codex_events(
    root: Path | str,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[dict[str, Any]]:
    root_path = Path(root)
    events = _load_index_events(root_path, start, end) + _load_history_events(
        root_path, start, end
    )
    session_root = root_path / "sessions"
    if not session_root.exists():
        return events

    for file_path in _candidate_session_files(session_root, start, end):
        session_id: str | None = None
        cwd: str | None = None
        is_subagent = False
        for row in _iter_jsonl(file_path):
            if row.get("type") == "session_meta":
                payload = row.get("payload", {})
                if isinstance(payload, dict):
                    session_id = payload.get("id") or session_id
                    cwd = payload.get("cwd") or cwd
                    source = payload.get("source")
                    is_subagent = isinstance(source, dict) and "subagent" in source

            if _in_window(row.get("timestamp"), start, end):
                events.append(_build_event(row, file_path, session_id, cwd, is_subagent))

    return events

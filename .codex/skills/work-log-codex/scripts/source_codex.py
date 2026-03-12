from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any


def _extract_message_text(payload: dict[str, Any]) -> str | None:
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
            return text

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
        "raw": row,
    }


def _safe_json_loads(raw_line: str) -> dict[str, Any] | None:
    try:
        return json.loads(raw_line)
    except JSONDecodeError:
        return None


def _load_history_events(root_path: Path) -> list[dict[str, Any]]:
    history_file = root_path / "history.jsonl"
    if not history_file.exists():
        return []
    events: list[dict[str, Any]] = []
    for raw_line in history_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        row = _safe_json_loads(line)
        if not row:
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
                "raw": row,
            }
        )
    return events


def _load_index_events(root_path: Path) -> list[dict[str, Any]]:
    index_file = root_path / "session_index.jsonl"
    if not index_file.exists():
        return []
    events: list[dict[str, Any]] = []
    for raw_line in index_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        row = _safe_json_loads(line)
        if not row:
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
                "raw": row,
            }
        )
    return events


def load_codex_events(root: Path | str) -> list[dict[str, Any]]:
    root_path = Path(root)
    events = _load_index_events(root_path) + _load_history_events(root_path)
    session_root = root_path / "sessions"
    if not session_root.exists():
        return events

    for file_path in sorted(session_root.rglob("*.jsonl")):
        session_id: str | None = None
        cwd: str | None = None
        is_subagent = False
        for raw_line in file_path.read_text(encoding="utf-8").splitlines():
            if not raw_line.strip():
                continue

            row = _safe_json_loads(raw_line)
            if not row:
                continue
            if row.get("type") == "session_meta":
                payload = row.get("payload", {})
                if isinstance(payload, dict):
                    session_id = payload.get("id") or session_id
                    cwd = payload.get("cwd") or cwd
                    source = payload.get("source")
                    is_subagent = isinstance(source, dict) and "subagent" in source

            events.append(_build_event(row, file_path, session_id, cwd, is_subagent))

    return events

from __future__ import annotations

import json
from datetime import datetime
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


def _compact_argument(value: Any) -> Any:
    if isinstance(value, str):
        return _trim_text(value, MAX_RAW_ARGUMENT_CHARS)
    if isinstance(value, dict):
        return {
            key: _compact_argument(value[key])
            for key in ("cmd", "command", "description", "name")
            if key in value
        }
    if isinstance(value, list):
        return [_compact_argument(item) for item in value[:20]]
    return value if isinstance(value, (int, float, bool)) or value is None else None


def _compact_raw(row: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {
        key: row[key]
        for key in ("type", "tool_name", "name", "usage")
        if key in row
    }
    if "tool_input" in row:
        compact["tool_input"] = _compact_argument(row["tool_input"])
    message = row.get("message")
    if isinstance(message, dict):
        compact_message = {
            key: message[key]
            for key in ("role", "usage")
            if key in message
        }
        content = message.get("content")
        if isinstance(content, list):
            tool_blocks = [
                {
                    key: block[key]
                    for key in ("type", "name")
                    if key in block
                }
                for block in content
                if isinstance(block, dict) and block.get("type") == "tool_use"
            ]
            if tool_blocks:
                compact_message["content"] = tool_blocks
        if compact_message:
            compact["message"] = compact_message
    return compact


SKIP_DIR_MARKERS = ("observer-sessions",)
# Harness-generated user rows; pasted prompts also start with "<" and must be kept.
HARNESS_PREFIXES = ("<command-", "<local-command-", "<system-reminder>", "<task-notification>")


def _prompt_text(message: dict[str, Any]) -> str | None:
    """Text a human or the model actually wrote; tool results are not prompts."""
    content = message.get("content")
    if isinstance(content, str):
        text = content.strip()
        return None if not text or text.startswith(HARNESS_PREFIXES) else text
    if not isinstance(content, list):
        return None
    parts = [
        block["text"].strip()
        for block in content
        if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str)
    ]
    text = "\n".join(part for part in parts if part)
    return text or None


def _read_session(
    file_path: Path, start: datetime | None, end: datetime | None
) -> list[dict[str, Any]] | None:
    """Return in-window user/assistant rows, or None for an SDK helper session."""
    rows: list[dict[str, Any]] = []
    project: str | None = None
    with file_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except JSONDecodeError:
                continue
            entrypoint = row.get("entrypoint")
            # ponytail: SDK sessions here are memory-plugin helpers ("memory relevance
            # compressor"), not work. If real SDK work appears, add an opt-in flag.
            if isinstance(entrypoint, str) and entrypoint.startswith("sdk"):
                return None
            if project is None and isinstance(row.get("cwd"), str) and row["cwd"]:
                project = row["cwd"]
            if row.get("type") in {"user", "assistant"} and _in_window(row.get("timestamp"), start, end):
                rows.append(row)
    for row in rows:
        row["_project"] = project
    return rows


def load_claude_events(
    root: Path,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[dict[str, Any]]:
    """Read Claude Code 2.x session logs.

    <root>/projects/<cwd-slug>/<session>.jsonl               main session
    <root>/projects/<cwd-slug>/<session>/subagents/*.jsonl   subagent runs
    """
    projects_dir = root / "projects"
    if not projects_dir.is_dir():
        return []
    events: list[dict[str, Any]] = []
    for project_dir in sorted(p for p in projects_dir.iterdir() if p.is_dir()):
        if any(marker in project_dir.name for marker in SKIP_DIR_MARKERS):
            continue
        files = [(f, False) for f in sorted(project_dir.glob("*.jsonl"))]
        files += [(f, True) for f in sorted(project_dir.glob("*/subagents/*.jsonl"))]
        for file_path, is_subagent in files:
            for row in _read_session(file_path, start, end) or []:
                message = row.get("message") if isinstance(row.get("message"), dict) else {}
                text = _trim_text(None if row.get("isMeta") else _prompt_text(message))
                session_id = row.get("sessionId") or file_path.stem
                if is_subagent:
                    # Subagent rows carry the parent's sessionId; keep them apart so the
                    # parent is not reclassified as a subagent session.
                    session_id = f"{session_id}/{file_path.stem}"
                project = row.get("_project")
                events.append(
                    {
                        "tool": "claude",
                        "session_id": session_id,
                        "project_path": project,
                        "cwd": row.get("cwd"),
                        "timestamp": row.get("timestamp"),
                        "event_type": row.get("type"),
                        "title": text.splitlines()[0] if text else None,
                        "text": text,
                        "evidence_path": str(file_path),
                        "confidence": "high" if project else "low",
                        "is_subagent": is_subagent,
                        "raw": _compact_raw(row),
                    }
                )
    return events

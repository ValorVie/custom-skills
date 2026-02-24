"""claude-mem sync server 客戶端工具函式。"""
from __future__ import annotations

import json
import sqlite3
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

import yaml

from .paths import get_ai_dev_config_dir

SYNC_SERVER_CONFIG_NAME = "sync-server.yaml"
CLAUDE_MEM_DB_PATH = Path("~/.claude-mem/claude-mem.db").expanduser()


def get_server_config_path() -> Path:
    return get_ai_dev_config_dir() / SYNC_SERVER_CONFIG_NAME


def load_server_config() -> dict[str, Any]:
    path = get_server_config_path()
    if not path.exists():
        raise FileNotFoundError(
            f"找不到 sync server 設定：{path}。請先執行 `ai-dev mem register`"
        )
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_server_config(config: dict[str, Any]) -> None:
    path = get_server_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def api_request(
    config: dict[str, Any],
    method: str,
    path: str,
    body: dict | None = None,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """對 sync server 發送 HTTP 請求。"""
    url = f"{config['server_url'].rstrip('/')}{path}"
    headers = {"Content-Type": "application/json"}
    if config.get("api_key"):
        headers["X-API-Key"] = config["api_key"]
    if extra_headers:
        headers.update(extra_headers)

    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {error_body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Server 不可達: {e.reason}") from e


def query_local_db(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """唯讀查詢本地 claude-mem SQLite。"""
    db_path = CLAUDE_MEM_DB_PATH
    if not db_path.exists():
        return []
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Direct SQLite import (fallback when claude-mem worker is unavailable)
# ---------------------------------------------------------------------------

# Column lists per table — only insert columns that exist in the local schema.
_SESSION_COLS = [
    "content_session_id", "memory_session_id", "project", "user_prompt",
    "started_at", "started_at_epoch", "completed_at", "completed_at_epoch",
    "status",
]

_OBSERVATION_COLS = [
    "memory_session_id", "project", "text", "type", "title", "subtitle",
    "facts", "narrative", "concepts", "files_read", "files_modified",
    "prompt_number", "discovery_tokens", "created_at", "created_at_epoch",
    "content_hash",
]

_SUMMARY_COLS = [
    "memory_session_id", "project", "request", "investigated", "learned",
    "completed", "next_steps", "files_read", "files_edited", "notes",
    "prompt_number", "discovery_tokens", "created_at", "created_at_epoch",
]

_PROMPT_COLS = [
    "content_session_id", "prompt_number", "prompt_text",
    "created_at", "created_at_epoch",
]


def _pick(row: dict[str, Any], cols: list[str]) -> dict[str, Any]:
    return {c: row.get(c) for c in cols}


def _insert_ignore(
    conn: sqlite3.Connection, table: str, row: dict[str, Any], cols: list[str]
) -> bool:
    data = _pick(row, cols)
    placeholders = ", ".join("?" for _ in data)
    col_names = ", ".join(data.keys())
    try:
        conn.execute(
            f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES ({placeholders})",
            list(data.values()),
        )
        return conn.total_changes > 0
    except sqlite3.Error:
        return False


def _exists(conn: sqlite3.Connection, sql: str, params: tuple) -> bool:
    return conn.execute(sql, params).fetchone() is not None


def import_to_local_db(data: dict[str, list]) -> dict[str, Any]:
    """直接寫入本地 claude-mem SQLite（claude-mem worker 不可用時的 fallback）。"""
    db_path = CLAUDE_MEM_DB_PATH
    if not db_path.exists():
        raise FileNotFoundError(f"claude-mem 資料庫不存在：{db_path}")

    stats: dict[str, int] = {
        "sessionsImported": 0, "sessionsSkipped": 0,
        "observationsImported": 0, "observationsSkipped": 0,
        "summariesImported": 0, "summariesSkipped": 0,
        "promptsImported": 0, "promptsSkipped": 0,
    }

    conn = sqlite3.connect(str(db_path))
    try:
        # sessions — content_session_id UNIQUE
        for row in data.get("sessions", []):
            before = conn.total_changes
            _insert_ignore(conn, "sdk_sessions", row, _SESSION_COLS)
            if conn.total_changes > before:
                stats["sessionsImported"] += 1
            else:
                stats["sessionsSkipped"] += 1

        # observations — dedup by (memory_session_id, title, created_at_epoch)
        for row in data.get("observations", []):
            if _exists(
                conn,
                "SELECT 1 FROM observations WHERE memory_session_id = ? AND title = ? AND created_at_epoch = ?",
                (row.get("memory_session_id"), row.get("title"), row.get("created_at_epoch")),
            ):
                stats["observationsSkipped"] += 1
                continue
            d = _pick(row, _OBSERVATION_COLS)
            placeholders = ", ".join("?" for _ in d)
            col_names = ", ".join(d.keys())
            conn.execute(
                f"INSERT INTO observations ({col_names}) VALUES ({placeholders})",
                list(d.values()),
            )
            stats["observationsImported"] += 1

        # summaries — dedup by memory_session_id
        for row in data.get("summaries", []):
            sid = row.get("session_id") or row.get("memory_session_id")
            if not sid:
                stats["summariesSkipped"] += 1
                continue
            row_copy = dict(row)
            row_copy["memory_session_id"] = sid
            if _exists(
                conn,
                "SELECT 1 FROM session_summaries WHERE memory_session_id = ?",
                (sid,),
            ):
                stats["summariesSkipped"] += 1
                continue
            d = _pick(row_copy, _SUMMARY_COLS)
            placeholders = ", ".join("?" for _ in d)
            col_names = ", ".join(d.keys())
            conn.execute(
                f"INSERT INTO session_summaries ({col_names}) VALUES ({placeholders})",
                list(d.values()),
            )
            stats["summariesImported"] += 1

        # prompts — dedup by (content_session_id, prompt_number)
        for row in data.get("prompts", []):
            if _exists(
                conn,
                "SELECT 1 FROM user_prompts WHERE content_session_id = ? AND prompt_number = ?",
                (row.get("content_session_id"), row.get("prompt_number")),
            ):
                stats["promptsSkipped"] += 1
                continue
            d = _pick(row, _PROMPT_COLS)
            placeholders = ", ".join("?" for _ in d)
            col_names = ", ".join(d.keys())
            conn.execute(
                f"INSERT INTO user_prompts ({col_names}) VALUES ({placeholders})",
                list(d.values()),
            )
            stats["promptsImported"] += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {"stats": stats}

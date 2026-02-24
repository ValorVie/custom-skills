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

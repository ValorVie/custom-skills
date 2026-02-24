"""claude-mem sync server 客戶端工具函式。"""
from __future__ import annotations

import json
import sqlite3
import urllib.request
import urllib.error
import urllib.parse
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


WORKER_URL = "http://localhost:37777"
CHROMA_DIR = Path("~/.claude-mem/chroma").expanduser()
CHROMA_DB_PATH = CHROMA_DIR / "chroma.sqlite3"
CHROMA_COLLECTION = "cm__claude-mem"


def worker_available() -> bool:
    """檢查 claude-mem worker 是否可用。"""
    try:
        req = urllib.request.Request(f"{WORKER_URL}/api/health", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


def _get_indexed_observation_ids() -> set[int]:
    """從 ChromaDB SQLite 讀取已索引的 observation sqlite_ids。"""
    if not CHROMA_DB_PATH.exists():
        return set()
    conn = sqlite3.connect(f"file:{CHROMA_DB_PATH}?mode=ro", uri=True)
    try:
        obs_embeds = conn.execute(
            "SELECT id FROM embedding_metadata "
            "WHERE key='doc_type' AND string_value='observation'"
        ).fetchall()
        if not obs_embeds:
            return set()
        embed_ids = [r[0] for r in obs_embeds]
        placeholders = ",".join("?" * len(embed_ids))
        rows = conn.execute(
            f"SELECT DISTINCT int_value FROM embedding_metadata "
            f"WHERE key='sqlite_id' AND id IN ({placeholders})",
            embed_ids,
        ).fetchall()
        return {r[0] for r in rows if r[0] is not None}
    finally:
        conn.close()


def _build_chroma_documents(obs: dict[str, Any]) -> list[dict[str, Any]]:
    """將一筆 observation 轉換為 worker 格式的 ChromaDB documents。

    格式匹配 worker 的 syncObservation：
    - obs_{id}_narrative → narrative 欄位
    - obs_{id}_fact_{n} → facts JSON array 的第 n 項
    """
    obs_id = obs["id"]
    base_metadata: dict[str, Any] = {
        "doc_type": "observation",
        "sqlite_id": obs_id,
        "project": obs.get("project") or "",
        "title": obs.get("title") or "",
        "subtitle": obs.get("subtitle") or "",
        "type": obs.get("type") or "",
        "created_at_epoch": obs.get("created_at_epoch") or 0,
    }
    if obs.get("memory_session_id"):
        base_metadata["memory_session_id"] = obs["memory_session_id"]
    if obs.get("concepts"):
        base_metadata["concepts"] = obs["concepts"]
    if obs.get("files_read"):
        base_metadata["files_read"] = obs["files_read"]

    docs: list[dict[str, Any]] = []

    # narrative document
    narrative = obs.get("narrative") or ""
    if narrative.strip():
        docs.append({
            "id": f"obs_{obs_id}_narrative",
            "document": narrative,
            "metadata": {**base_metadata, "field_type": "narrative"},
        })

    # fact documents (parse JSON array)
    facts_raw = obs.get("facts") or "[]"
    try:
        facts = json.loads(facts_raw) if isinstance(facts_raw, str) else facts_raw
    except (json.JSONDecodeError, TypeError):
        facts = []
    if isinstance(facts, list):
        for i, fact in enumerate(facts):
            if isinstance(fact, str) and fact.strip():
                docs.append({
                    "id": f"obs_{obs_id}_fact_{i}",
                    "document": fact,
                    "metadata": {**base_metadata, "field_type": "fact"},
                })

    return docs


def reindex_observations() -> dict[str, int]:
    """找出 ChromaDB 中缺失的 observations 並重建索引。

    Returns:
        dict with keys: total, already_indexed, missing, synced, errors, sample_title
    """
    db_path = CLAUDE_MEM_DB_PATH
    if not db_path.exists():
        raise FileNotFoundError(f"claude-mem 資料庫不存在：{db_path}")
    if not CHROMA_DIR.exists():
        raise FileNotFoundError(
            f"ChromaDB 目錄不存在：{CHROMA_DIR}\n"
            "請確認 claude-mem plugin 已啟動且 ChromaDB 已初始化"
        )

    indexed_ids = _get_indexed_observation_ids()

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        all_obs = conn.execute(
            "SELECT id, title, subtitle, narrative, text, facts, concepts, "
            "type, project, memory_session_id, created_at_epoch, files_read "
            "FROM observations ORDER BY id"
        ).fetchall()
    finally:
        conn.close()

    missing = [dict(r) for r in all_obs if r["id"] not in indexed_ids]
    stats: dict[str, Any] = {
        "total": len(all_obs),
        "already_indexed": len(indexed_ids),
        "missing": len(missing),
        "synced": 0,
        "errors": 0,
        "sample_title": "",
    }

    if not missing:
        return stats

    stats["sample_title"] = missing[0].get("title", "")

    # 組裝所有 ChromaDB documents
    all_docs: list[dict[str, Any]] = []
    for obs in missing:
        all_docs.extend(_build_chroma_documents(obs))

    if not all_docs:
        return stats

    # 透過 uv run --with chromadb 寫入
    stats.update(_write_to_chroma(all_docs))
    return stats


def _write_to_chroma(docs: list[dict[str, Any]]) -> dict[str, int]:
    """用 uv run --with chromadb subprocess 寫入 ChromaDB。"""
    import shutil
    import subprocess as sp
    import tempfile

    if not shutil.which("uv"):
        raise FileNotFoundError(
            "找不到 uv 指令。請安裝：https://docs.astral.sh/uv/getting-started/installation/"
        )

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(docs, f, ensure_ascii=False)
        tmp_path = f.name

    chroma_path = str(CHROMA_DIR)
    collection_name = CHROMA_COLLECTION
    script = f"""\
import json, sys
import chromadb

client = chromadb.PersistentClient(path="{chroma_path}")
col = client.get_or_create_collection("{collection_name}")

with open("{tmp_path}", "r") as f:
    items = json.load(f)

synced = errors = 0
for item in items:
    try:
        col.add(
            documents=[item["document"]],
            metadatas=[item["metadata"]],
            ids=[item["id"]],
        )
        synced += 1
    except Exception as e:
        print(f"Error {{item['id']}}: {{e}}", file=sys.stderr)
        errors += 1

print(json.dumps({{"synced": synced, "errors": errors}}))
"""

    result = sp.run(
        ["uv", "run", "--with", "chromadb", "python3", "-c", script],
        capture_output=True, text=True, timeout=300,
    )

    Path(tmp_path).unlink(missing_ok=True)

    if result.returncode == 0:
        try:
            lines = result.stdout.strip().splitlines()
            r = json.loads(lines[-1])
            return {"synced": r.get("synced", 0), "errors": r.get("errors", 0)}
        except (json.JSONDecodeError, ValueError, IndexError):
            return {"synced": 0, "errors": len(docs)}
    else:
        return {"synced": 0, "errors": len(docs)}


def kill_chroma_mcp() -> bool:
    """Kill chroma-mcp 進程（worker 的子進程），讓 worker 自動重啟它。

    Returns:
        True if process was found and killed, False otherwise.
    """
    import os
    import signal
    import subprocess as sp

    # 找 worker PID
    try:
        req = urllib.request.Request(f"{WORKER_URL}/api/health", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            health = json.loads(resp.read().decode("utf-8"))
            worker_pid = health.get("pid")
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return False

    if not worker_pid:
        return False

    # 找 worker 的 chroma-mcp 子進程
    result = sp.run(
        ["ps", "--ppid", str(worker_pid), "-o", "pid,cmd", "--no-headers"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return False

    chroma_pids: list[int] = []
    for line in result.stdout.strip().splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2 and "chroma-mcp" in parts[1]:
            chroma_pids.append(int(parts[0]))

    if not chroma_pids:
        return False

    for pid in chroma_pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass

    return True


def verify_search(sample_title: str, timeout_secs: int = 15) -> bool:
    """驗證 ChromaDB 搜尋是否能找到指定 observation。"""
    import time

    deadline = time.time() + timeout_secs
    while time.time() < deadline:
        try:
            url = (
                f"{WORKER_URL}/api/search?"
                f"query={urllib.parse.quote(sample_title)}&limit=3&type=observation"
            )
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                text = body.get("content", [{}])[0].get("text", "")
                if sample_title[:20] in text or "result" in text.lower():
                    return True
        except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError, IndexError):
            pass
        time.sleep(2)

    return False


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

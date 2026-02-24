# ai-dev mem reindex 實作計畫

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 實作 `ai-dev mem reindex` 指令，修復 pull 匯入的 observations 無法被 ChromaDB 搜尋的問題。

**狀態:** 已棄用 — PersistentClient 方案因 ChromaDB 跨進程寫入不可見而失敗。最終實作改用 worker `/api/memory/save` API，詳見設計文件的「最終實作」章節。

**Architecture (原始，已棄用):** 比對 claude-mem SQLite 與 ChromaDB SQLite 找出缺失項，用 `uv run --with chromadb` subprocess 按 worker 格式寫入 ChromaDB，然後 kill chroma-mcp 進程讓 worker 重啟，最後驗證搜尋是否生效。

**Tech Stack:** Python 3.12+, chromadb (via uv run), SQLite, typer/rich CLI

**Design doc:** `docs/plans/2026-02-24-mem-reindex-design.md`

---

### Task 1: 清理半成品程式碼

先前調試留下的 reindex 程式碼格式不正確（單一 document 而非 narrative+facts），需要完全重寫。

**Files:**
- Modify: `script/utils/mem_sync.py:136-341` (替換 WORKER_URL 到 _reindex_via_subprocess 結尾)
- Modify: `script/commands/mem.py:19-27` (imports)
- Modify: `script/commands/mem.py:293-315` (reindex command)

**Step 1: 重寫 `script/utils/mem_sync.py` 的 reindex 區塊**

替換 `mem_sync.py` 的第 136-341 行（從 `WORKER_URL = ...` 到 `_reindex_via_subprocess` 函式結尾）為以下內容：

```python
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
        dict with keys: total, already_indexed, missing, synced, errors
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
    stats = {
        "total": len(all_obs),
        "already_indexed": len(indexed_ids),
        "missing": len(missing),
        "synced": 0,
        "errors": 0,
    }

    if not missing:
        return stats

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
    import signal

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
    import subprocess as sp

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
            import os
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
            req = urllib.request.Request(
                f"{WORKER_URL}/api/search?"
                + urllib.request.pathname2url(f"query={sample_title}&limit=3&type=observation"),
                method="GET",
            )
            # 手動構建 URL 避免 pathname2url 問題
            url = f"{WORKER_URL}/api/search?query={urllib.parse.quote(sample_title)}&limit=3&type=observation"
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
```

Note: 需要在檔案頂部 import 區加入 `import urllib.parse`。

**Step 2: 更新 `script/commands/mem.py` 的 imports**

替換 `mem.py` 第 19-27 行的 imports：

```python
from ..utils.mem_sync import (
    api_request,
    import_to_local_db,
    kill_chroma_mcp,
    load_server_config,
    query_local_db,
    reindex_observations,
    save_server_config,
    verify_search,
    worker_available,
)
```

**Step 3: 重寫 `script/commands/mem.py` 的 reindex 指令**

替換 `mem.py` 第 293-315 行的 `reindex` 函式：

```python
@app.command()
def reindex() -> None:
    """重建 ChromaDB 搜尋索引（修復 pull 匯入後搜尋不到的問題）。"""
    if not worker_available():
        console.print(
            "[bold red]claude-mem worker 未啟動，無法重建索引[/bold red]\n"
            "[yellow]請先啟動 Claude Code 讓 worker 自動啟動後再試[/yellow]"
        )
        raise typer.Exit(code=1)

    console.print("[cyan]正在掃描缺失的 ChromaDB 索引...[/cyan]")
    try:
        stats = reindex_observations()
    except FileNotFoundError as e:
        console.print(f"[bold red]{e}[/bold red]")
        raise typer.Exit(code=1)

    if stats["missing"] == 0:
        console.print(
            f"[green]索引已完整[/green]（共 {stats['total']} 筆 observations）"
        )
        return

    console.print(
        f"[bold green]寫入完成[/bold green] "
        f"synced={stats['synced']} errors={stats['errors']} "
        f"（共 {stats['total']} 筆，原缺 {stats['missing']} 筆）"
    )

    if stats["synced"] == 0:
        console.print("[bold red]無任何索引寫入成功[/bold red]")
        raise typer.Exit(code=1)

    # Kill chroma-mcp 讓 worker 重啟
    console.print("[cyan]正在重啟 chroma-mcp 進程...[/cyan]")
    if kill_chroma_mcp():
        import time
        time.sleep(3)
        console.print("[green]chroma-mcp 已重啟[/green]")
    else:
        console.print(
            "[yellow]找不到 chroma-mcp 進程，請手動重啟 Claude Code session[/yellow]"
        )
        return

    # 驗證搜尋
    console.print("[cyan]正在驗證搜尋...[/cyan]")
    # 用第一筆缺失 observation 的 title 做驗證
    sample_title = stats.get("sample_title", "")
    if sample_title and verify_search(sample_title):
        console.print("[bold green]驗證成功 — 搜尋索引已生效[/bold green]")
    elif sample_title:
        console.print(
            "[yellow]驗證未通過 — 索引已寫入但搜尋可能需要更多時間。"
            "若仍無法搜尋，請重啟 Claude Code session[/yellow]"
        )
    else:
        console.print("[green]Reindex 完成[/green]")
```

Note: `reindex_observations()` 需要在 stats 中加入 `sample_title`（第一筆缺失 observation 的 title）。在 `reindex_observations()` 函式的 `if not missing: return stats` 之後，加入：

```python
    stats["sample_title"] = missing[0].get("title", "")
```

**Step 4: 驗證修改語法正確**

Run: `python3 -c "import ast; ast.parse(open('script/utils/mem_sync.py').read()); ast.parse(open('script/commands/mem.py').read()); print('OK')"`
Expected: `OK`

**Step 5: Commit**

```bash
git add script/utils/mem_sync.py script/commands/mem.py
git commit -m "重構(mem-sync): 重寫 reindex 匹配 worker ChromaDB document 格式"
```

---

### Task 2: 端對端測試

**Step 1: 清理之前測試產生的錯誤格式 ChromaDB entries**

之前的除錯在 ChromaDB 裡留下了格式不正確的 entries（`obs_1` 而非 `obs_1_narrative`）。先清理：

Run:
```bash
uv run --with chromadb python3 -c "
import chromadb
client = chromadb.PersistentClient(path='$HOME/.claude-mem/chroma')
col = client.get_collection('cm__claude-mem')
# 刪除格式不正確的 obs_N entries（沒有 _narrative/_fact_ 後綴的）
import re
all_items = col.get(include=[])
bad_ids = [i for i in all_items['ids'] if re.match(r'^obs_\d+$', i)]
if bad_ids:
    col.delete(ids=bad_ids)
    print(f'Deleted {len(bad_ids)} malformed entries: {bad_ids[:5]}...')
else:
    print('No malformed entries found')
"
```

**Step 2: 執行 reindex**

Run: `ai-dev mem reindex`

Expected output:
```
正在掃描缺失的 ChromaDB 索引...
寫入完成 synced=N errors=0（共 M 筆，原缺 K 筆）
正在重啟 chroma-mcp 進程...
chroma-mcp 已重啟
正在驗證搜尋...
驗證成功 — 搜尋索引已生效
```

**Step 3: 手動驗證搜尋**

Run: `curl -s "http://localhost:37777/api/search?query=Tool+Decision+Guide&limit=3&type=observation" | python3 -m json.tool`

Expected: 結果中應包含 observation #1 "Tool Decision Guide for Choosing Development Workflows"

**Step 4: Commit**

```bash
git add docs/plans/2026-02-24-mem-reindex-design.md docs/plans/2026-02-24-mem-reindex-impl.md
git commit -m "文件(mem-sync): reindex 設計與實作計畫"
```

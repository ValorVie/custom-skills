# ai-dev mem reindex 設計文件

**日期:** 2026-02-24
**狀態:** 已完成（實作方案已變更，見下方「最終實作」）

## 問題

`ai-dev mem pull` 匯入的 observations 直接寫入 SQLite，繞過了 claude-mem worker 的 `syncObservation()` 流程。導致 FTS5 索引正常（透過 SQLite triggers），但 ChromaDB 向量索引缺失，MCP `search()` 找不到這些 observations。

## Root Cause

Pull 匯入路徑（`import_to_local_db()`）直接 INSERT SQLite，而 ChromaDB sync 只在 worker 的 `syncObservation()` 中觸發。Worker 的 `/api/import` 端點也不觸發 ChromaDB sync。Worker 是第三方 minified plugin，無法修改。

## 方案

### 選擇：D1 — uv run --with chromadb subprocess

`ai-dev mem reindex` 指令：

1. 比對 SQLite observations vs ChromaDB 已索引 IDs，找出缺失項
2. 讀取缺失 observations，組裝成 worker 格式的 documents
3. 寫入暫存 JSON，透過 `uv run --with chromadb` 執行寫入
4. Kill chroma-mcp 進程，等待 worker 自動重啟
5. 驗證搜尋是否生效

### ChromaDB Document 格式

匹配 worker 的 `syncObservation` 產出：

| embedding_id | document 內容 | field_type |
|-------------|--------------|------------|
| `obs_{id}_narrative` | narrative 欄位 | `narrative` |
| `obs_{id}_fact_{n}` | facts JSON array 第 n 項 | `fact` |

每個 document 的 metadata：

```python
{
    "doc_type": "observation",
    "field_type": "narrative" | "fact",
    "sqlite_id": int,
    "project": str,
    "title": str,
    "subtitle": str,
    "type": str,
    "concepts": str,
    "files_read": str,
    "memory_session_id": str,
    "created_at_epoch": int,
}
```

### 錯誤處理

| 情況 | 處理 |
|------|------|
| ChromaDB 目錄不存在 | 報錯退出 |
| `uv` 不在 PATH | 報錯提示安裝 |
| chroma-mcp 找不到 | 寫入後提示重啟 Claude Code |
| Worker 未重啟 chroma-mcp | 超時後提示手動重啟 |
| 驗證搜尋失敗 | 警告但不算失敗 |
| 無缺失 observations | 報告索引已完整 |

### 檔案變動

| 檔案 | 變動 |
|------|------|
| `script/utils/mem_sync.py` | 重寫 `reindex_observations()`、`_reindex_via_subprocess()`，新增 `_kill_and_wait_chroma()` |
| `script/commands/mem.py` | 更新 `reindex` 指令加入 kill + 驗證邏輯 |

---

## 最終實作（方案變更）

### D1 方案失敗原因

實作 D1 後端對端測試發現 **ChromaDB PersistentClient 跨進程寫入的資料對 chroma-mcp 不可見**。即使使用相同 chromadb 版本、kill 並重啟 chroma-mcp，HNSW segment manager 不共享狀態。這是 ChromaDB 的架構限制。

### 最終方案：Worker Save API

改用 worker 的 `POST /api/memory/save` 端點逐筆寫入缺失的 observations：

1. 比對 SQLite observations vs ChromaDB 已索引 IDs（`_get_indexed_observation_ids()`），找出缺失項
2. 對每筆缺失 observation，POST `{text, title, project}` 到 worker `/api/memory/save`
3. Worker 內部自動觸發 `syncObservation()` 完成 ChromaDB 索引

**Trade-off：** 會在 SQLite 建立副本 observation（僅含 narrative + title + project），原始記錄完整保留。

### 整合到 Pull 流程

Reindex 已整合到 `ai-dev mem pull` 流程中：pull 匯入 observations 後自動呼叫 `reindex_observations()`（worker 在線時）。`ai-dev mem reindex` 保留作為手動補救指令。

### 最終檔案變動

| 檔案 | 變動 |
|------|------|
| `script/utils/mem_sync.py` | 簡化 `reindex_observations()` 為 worker save API 呼叫，移除 `_build_chroma_documents`、`_write_to_chroma`、`kill_chroma_mcp`、`verify_search` |
| `script/commands/mem.py` | 簡化 `reindex` 指令，`pull` 指令加入自動 reindex |

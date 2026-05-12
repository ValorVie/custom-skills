## Why

claude-mem-sync 目前的去重機制依賴 `(memory_session_id, title, created_at_epoch)` 組合鍵，無法有效識別「相同內容但不同 metadata」的 observation，導致 push 重複推送、pull 重複匯入、跨裝置同步迴圈等問題。實際已觀察到重複記錄（如 #238/#100 同一 content_hash），造成搜尋結果重複、資料膨脹、同步效率低落。

## What Changes

- 在 PostgreSQL `observations` 表新增 `sync_content_hash TEXT UNIQUE` 欄位，基於 5 個內容欄位（title, narrative, facts, project, type）計算 SHA-256 前 128 bits
- 新增 `POST /api/sync/push-preflight` API，client push 前先查詢 server 上不存在的 hash 差集
- Push 流程加入 content hash 計算、pulled-hashes 排除、preflight 差集過濾
- Pull 流程加入本地 hash 集合比對，過濾已存在的 observations
- Client 維護 `~/.config/ai-dev/pulled-hashes.txt` 記錄外來資料 hash，防止推回迴圈
- 新增 `ai-dev mem cleanup` 子命令掃描並刪除本地重複 observations
- 增強 `ai-dev mem status` 顯示本地去重統計

## Capabilities

### New Capabilities
- `mem-sync-content-hash`: Content hash 計算（Python + TypeScript 跨語言一致）、migration 002 schema 變更、hash 回填與既有重複清理
- `mem-sync-push-preflight`: Push preflight API 差集計算、client 端 pulled-hashes 排除機制
- `mem-sync-pull-dedup`: Pull 端 hash 比對過濾、pulled-hashes 追蹤記錄
- `mem-sync-cleanup`: 本地重複 observations 掃描與清理指令、status 統計增強

### Modified Capabilities
（無現有 spec 需變更 — mem-sync 相關功能尚未建立 OpenSpec specs）

## Impact

- **Server 端：**
  - `services/claude-mem-sync/server/migrations/` — 新增 002_add_sync_content_hash.sql
  - `services/claude-mem-sync/server/src/routes/sync.ts` — push UPSERT 改用 sync_content_hash、新增 preflight endpoint
  - `services/claude-mem-sync/server/src/index.ts` — 啟動時回填 hash 並去重
  - `services/claude-mem-sync/server/src/utils/hash.ts` — 新增 TypeScript hash 工具
  - `services/claude-mem-sync/tests/sync.test.ts` — 新增 dedup 整合測試
- **Client 端：**
  - `script/utils/mem_sync.py` — 新增 compute_content_hash、pulled-hashes 管理函式
  - `script/commands/mem.py` — push/pull 流程重構、新增 cleanup 子命令、status 增強
  - `tests/test_mem_sync_hash.py` — hash 單元測試
  - `tests/test_pulled_hashes.py` — pulled-hashes 管理測試
- **參考文件：**
  - `docs/plans/2026-02-24-claude-mem-sync-server-design.md` — 原始 sync server 架構設計
  - `docs/plans/2026-02-24-claude-mem-sync-server-impl.md` — 原始 sync server 實作計畫
  - `docs/plans/2026-02-24-mem-sync-dedup-design.md` — Content Hash 去重設計
  - `docs/plans/2026-02-24-mem-sync-dedup-impl.md` — Content Hash 去重實作計畫

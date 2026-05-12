## 1. Content Hash 工具函式

- [x] 1.1 Python `compute_content_hash()` 實作與單元測試 (`script/utils/mem_sync.py`, `tests/test_mem_sync_hash.py`)
- [x] 1.2 TypeScript `computeContentHash()` 實作與單元測試 (`server/src/utils/hash.ts`, `tests/hash.test.ts`)
- [x] 1.3 跨語言一致性驗證：Python 產生 known-good hash，TypeScript 測試比對

## 2. Server Schema 與回填

- [x] 2.1 建立 migration 002：`ALTER TABLE observations ADD COLUMN sync_content_hash TEXT` + UNIQUE 索引 (`server/migrations/002_add_sync_content_hash.sql`)
- [x] 2.2 更新 `server/src/index.ts` 執行 migration 002
- [x] 2.3 實作啟動時回填邏輯：計算缺少 hash 的 observations 並填入
- [x] 2.4 實作啟動時去重邏輯：刪除同 hash 的重複行（保留最早 synced_at）
- [x] 2.5 驗證回填冪等性：重啟 server 不重複執行

## 3. Server Push 改造

- [x] 3.1 實作 `POST /api/sync/push-preflight` endpoint (`server/src/routes/sync.ts`)
- [x] 3.2 修改 push endpoint：observations INSERT 改用 `ON CONFLICT (sync_content_hash) DO NOTHING`
- [x] 3.3 加入 fallback：client 未帶 hash 時 server 自動計算
- [x] 3.4 撰寫 preflight 整合測試 (`tests/sync.test.ts`)
- [x] 3.5 撰寫 hash dedup 整合測試：跨裝置同內容 push 被正確跳過

## 4. Server Pull 改造

- [x] 4.1 驗證 pull response 已包含 `sync_content_hash`（SELECT * 自動帶入）
- [x] 4.2 撰寫測試確認 pull response 中每筆 observation 都有 32-char hash

## 5. Client Pulled-Hashes 管理

- [x] 5.1 實作 `load_pulled_hashes()` 和 `append_pulled_hashes()` (`script/utils/mem_sync.py`)
- [x] 5.2 撰寫 pulled-hashes 單元測試 (`tests/test_pulled_hashes.py`)

## 6. Client Push 流程重構

- [x] 6.1 Push 加入 compute_content_hash 為每筆 observation 計算 hash
- [x] 6.2 Push 加入 pulled-hashes 排除邏輯
- [x] 6.3 實作 `push_preflight()` 工具函式 (`script/utils/mem_sync.py`)
- [x] 6.4 Push 串接 preflight 差集過濾（fallback 全量推送）
- [x] 6.5 更新 push 輸出訊息：顯示去重統計

## 7. Client Pull 流程重構

- [x] 7.1 Pull 加入本地 hash 集合計算與過濾
- [x] 7.2 Pull 成功匯入後追加 hash 到 pulled-hashes.txt
- [x] 7.3 更新 pull 輸出訊息：顯示 hash 去重統計

## 8. Cleanup 與 Status 增強

- [x] 8.1 實作 `ai-dev mem cleanup` 子命令 (`script/commands/mem.py`)
- [x] 8.2 增強 `ai-dev mem status`：顯示 local observations、duplicates、pulled hashes 統計

## 9. 整合驗證

- [x] 9.1 手動端對端測試：push → pull → re-push 驗證無重複
- [x] 9.2 執行全部 Python 測試：`python -m pytest tests/test_mem_sync_hash.py tests/test_pulled_hashes.py -v`
- [x] 9.3 執行全部 Server 測試：`bun test` in `services/claude-mem-sync/`

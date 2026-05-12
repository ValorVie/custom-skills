## ADDED Requirements

### Requirement: Content hash 計算跨語言一致

系統 SHALL 提供 Python 和 TypeScript 兩種語言的 content hash 計算函式，對相同輸入產生完全相同的 32 hex chars 輸出。

Hash 計算 SHALL 基於 5 個內容欄位：`title`, `narrative`, `facts`, `project`, `type`。

Hash 計算 SHALL 忽略所有 metadata 欄位：`id`, `memory_session_id`, `created_at_epoch`, `origin_device_id`, `synced_at`。

缺失的欄位 SHALL 以預設值代替：空字串（title, narrative, project, type）或 `"[]"`（facts）。

#### Scenario: 相同內容產生相同 hash
- **WHEN** 兩筆 observation 的 title, narrative, facts, project, type 完全相同
- **THEN** 兩筆的 content hash 完全相同

#### Scenario: 不同內容產生不同 hash
- **WHEN** 兩筆 observation 的 narrative 不同（其餘相同）
- **THEN** 兩筆的 content hash 不同

#### Scenario: metadata 差異不影響 hash
- **WHEN** 兩筆 observation 內容相同但 id, memory_session_id, created_at_epoch 不同
- **THEN** 兩筆的 content hash 完全相同

#### Scenario: Python 與 TypeScript 交叉驗證
- **WHEN** 以相同的測試輸入分別在 Python 和 TypeScript 計算 hash
- **THEN** 兩者輸出完全一致

### Requirement: Server migration 新增 sync_content_hash 欄位

系統 SHALL 在 PostgreSQL `observations` 表新增 `sync_content_hash TEXT` 欄位，並建立 UNIQUE 索引。

Migration SHALL 使用 `IF NOT EXISTS` 確保冪等性。

#### Scenario: Migration 首次執行
- **WHEN** Server 首次啟動並執行 migration 002
- **THEN** `observations` 表新增 `sync_content_hash` 欄位和 UNIQUE 索引

#### Scenario: Migration 重複執行
- **WHEN** Server 重啟並再次執行 migration 002
- **THEN** 不產生錯誤（IF NOT EXISTS）

### Requirement: Server 啟動時回填 hash 並去重

Server SHALL 在啟動時檢查 `sync_content_hash IS NULL` 的 observations，為其計算並填入 hash。

回填完成後，Server SHALL 刪除具有相同 `sync_content_hash` 的重複行，保留 `synced_at` 最早的那筆。

回填 SHALL 是冪等的：如果所有 observations 已有 hash，不執行任何操作。

#### Scenario: 首次啟動回填
- **WHEN** Server 啟動且有 100 筆 observations 缺少 sync_content_hash
- **THEN** 系統為 100 筆計算並填入 hash，並刪除重複行

#### Scenario: 後續啟動跳過
- **WHEN** Server 啟動且所有 observations 已有 sync_content_hash
- **THEN** 不執行回填或去重操作

#### Scenario: 去重保留最早記錄
- **WHEN** 回填後發現 3 筆 observations 有相同 hash，synced_at 分別為 T1 < T2 < T3
- **THEN** 保留 T1 的記錄，刪除 T2 和 T3

### Requirement: Server push 使用 sync_content_hash UPSERT

Server 的 push endpoint SHALL 將 observations 的 `ON CONFLICT` 改為基於 `sync_content_hash`。

如果 client 未提供 `sync_content_hash`（舊版 client），Server SHALL 自動計算 hash 後再插入。

#### Scenario: Push 帶有 sync_content_hash
- **WHEN** Client push observation 附帶 sync_content_hash
- **THEN** Server 使用該 hash 做 UPSERT

#### Scenario: Push 不帶 sync_content_hash（向後相容）
- **WHEN** 舊版 client push observation 不含 sync_content_hash
- **THEN** Server 自動計算 hash 並插入

#### Scenario: 相同 hash 的 observation 被跳過
- **WHEN** Client push 的 observation hash 已存在於 server
- **THEN** Server 回傳 `observationsSkipped += 1`，不產生重複行

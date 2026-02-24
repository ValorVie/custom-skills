## ADDED Requirements

### Requirement: Push preflight API 回傳差集

Server SHALL 提供 `POST /api/sync/push-preflight` endpoint，接受 hash 列表，回傳 server 上不存在的 hash。

Endpoint SHALL 要求 API Key 認證。

#### Scenario: 部分 hash 已存在
- **WHEN** Client 送出 `{ hashes: ["existing_hash", "new_hash"] }`，其中 existing_hash 已在 server
- **THEN** Server 回傳 `{ missing: ["new_hash"] }`

#### Scenario: 所有 hash 已存在
- **WHEN** Client 送出的所有 hash 都已在 server
- **THEN** Server 回傳 `{ missing: [] }`

#### Scenario: 空 hash 列表
- **WHEN** Client 送出 `{ hashes: [] }`
- **THEN** Server 回傳 `{ missing: [] }`

#### Scenario: 未認證請求
- **WHEN** 請求未附帶 X-API-Key header
- **THEN** Server 回傳 HTTP 401

### Requirement: Client push 使用 preflight 減少傳輸

Client 的 push 流程 SHALL 在推送 observations 前先呼叫 preflight API，只推送 server 上不存在的 observations。

如果 preflight API 不可用（網路錯誤），Client SHALL 退回全量推送。

#### Scenario: Preflight 過濾已存在資料
- **WHEN** 本地有 100 筆新 observations，preflight 回報 90 筆已存在
- **THEN** Client 只推送剩餘 10 筆

#### Scenario: Preflight 失敗時退回全量
- **WHEN** Preflight API 回傳錯誤或連線逾時
- **THEN** Client 推送全部 100 筆（依賴 server UNIQUE 約束去重）

### Requirement: Client push 排除 pulled observations

Client push SHALL 排除 `pulled-hashes.txt` 中記錄的 hash，防止推回從其他裝置 pull 來的資料。

#### Scenario: 排除外來資料
- **WHEN** 本地有 50 筆 observations，其中 20 筆的 hash 存在於 pulled-hashes.txt
- **THEN** Client 只處理剩餘 30 筆（進入 preflight 流程）

#### Scenario: pulled-hashes.txt 不存在
- **WHEN** pulled-hashes.txt 檔案不存在
- **THEN** 視為空集合，不排除任何 observation

### Requirement: Pulled-hashes 檔案管理

系統 SHALL 在 `~/.config/ai-dev/pulled-hashes.txt` 維護所有 pull 匯入的 observation content hash。

檔案格式 SHALL 為純文字，一行一個 32 hex chars 的 hash。

寫入 SHALL 為 append-only。

#### Scenario: Pull 後追加 hash
- **WHEN** Pull 成功匯入 5 筆 observations
- **THEN** 5 筆對應的 hash 追加到 pulled-hashes.txt

#### Scenario: 讀取時忽略空行
- **WHEN** pulled-hashes.txt 包含空行
- **THEN** 讀取時跳過空行，只回傳有效 hash

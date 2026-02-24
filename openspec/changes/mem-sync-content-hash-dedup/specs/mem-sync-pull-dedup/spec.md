## ADDED Requirements

### Requirement: Pull 使用 content hash 過濾已存在 observations

Client pull SHALL 在匯入前計算本地所有 observations 的 content hash 集合，並過濾掉 server 回傳中 hash 已存在於本地的 observations。

#### Scenario: 過濾已存在的 observations
- **WHEN** Server 回傳 20 筆 observations，其中 15 筆的 sync_content_hash 已存在於本地
- **THEN** Client 只匯入剩餘 5 筆

#### Scenario: 全部為新資料
- **WHEN** Server 回傳 10 筆 observations，全部 hash 都不在本地
- **THEN** Client 匯入全部 10 筆

#### Scenario: 全部已存在
- **WHEN** Server 回傳 10 筆 observations，全部 hash 都已在本地
- **THEN** Client 不匯入任何 observation，顯示去重統計

### Requirement: Server pull response 包含 sync_content_hash

Server 的 pull endpoint SHALL 在回傳的 observations 中包含 `sync_content_hash` 欄位。

#### Scenario: Pull response 包含 hash
- **WHEN** Client 呼叫 `GET /api/sync/pull?since=0`
- **THEN** 回傳的每筆 observation 都包含非空的 `sync_content_hash` 欄位（32 hex chars）

### Requirement: Pull 匯入後記錄 hash

Client pull SHALL 在成功匯入 observations 後，將匯入的 hash 追加到 `pulled-hashes.txt`。

#### Scenario: 成功匯入後記錄
- **WHEN** Pull 成功匯入 5 筆 observations
- **THEN** 5 筆 hash 被追加到 pulled-hashes.txt

#### Scenario: 匯入失敗不記錄
- **WHEN** Pull 匯入過程中發生錯誤（worker 不可用且 SQLite fallback 失敗）
- **THEN** 不追加 hash 到 pulled-hashes.txt，不更新 last_pull_epoch

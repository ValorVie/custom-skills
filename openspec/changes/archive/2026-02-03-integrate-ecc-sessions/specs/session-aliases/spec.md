## ADDED Requirements

### Requirement: 別名建立

系統 SHALL 允許使用者為 session 建立易記的別名。

#### Scenario: 建立新別名

- **WHEN** 使用者執行 `/sessions alias <id> <name>`
- **THEN** 系統為指定 session 建立別名
- **AND** 別名儲存至 `~/.claude/session-aliases.json`
- **AND** 顯示確認訊息 `✓ Alias created: <name> → <filename>`

#### Scenario: 別名名稱驗證

- **WHEN** 使用者提供的別名包含非法字元
- **THEN** 系統拒絕建立並顯示錯誤訊息
- **AND** 合法字元為英數字、連字號、底線（`[a-zA-Z0-9_-]`）

#### Scenario: 保留名稱

- **WHEN** 使用者提供的別名為保留名稱（list, help, remove, delete, create, set）
- **THEN** 系統拒絕建立並顯示 `'<name>' is a reserved alias name` 錯誤

#### Scenario: 覆蓋既有別名

- **WHEN** 使用者提供的別名已存在
- **THEN** 系統更新別名指向新的 session
- **AND** 保留原始建立時間，更新修改時間

### Requirement: 別名刪除

系統 SHALL 允許使用者刪除既有別名。

#### Scenario: 刪除別名

- **WHEN** 使用者執行 `/sessions alias --remove <name>` 或 `/sessions unalias <name>`
- **THEN** 系統刪除指定別名
- **AND** 顯示確認訊息 `✓ Alias removed: <name>`

#### Scenario: 刪除不存在的別名

- **WHEN** 使用者指定的別名不存在
- **THEN** 系統顯示 `Alias '<name>' not found` 錯誤

### Requirement: 別名列表

系統 SHALL 提供列出所有別名的功能。

#### Scenario: 列出所有別名

- **WHEN** 使用者執行 `/sessions aliases`
- **THEN** 系統列出所有別名
- **AND** 每筆顯示名稱、session 檔案、title
- **AND** 依更新時間由新至舊排序

#### Scenario: 無別名

- **WHEN** 沒有任何別名
- **THEN** 系統顯示 `No aliases found.`

### Requirement: 別名解析

系統 SHALL 在載入 session 時自動嘗試解析別名。

#### Scenario: 別名優先解析

- **WHEN** `/sessions load` 接收到 ID 參數
- **THEN** 系統先嘗試作為別名解析
- **AND** 若別名存在則使用別名指向的 session
- **AND** 若別名不存在則作為 session ID 處理

### Requirement: 別名儲存

系統 SHALL 使用原子寫入確保別名資料完整性。

#### Scenario: 原子寫入流程

- **WHEN** 儲存別名資料
- **THEN** 先寫入暫存檔 `session-aliases.json.tmp`
- **AND** 建立備份 `session-aliases.json.bak`
- **AND** 用 rename 替換原檔案
- **AND** 成功後刪除備份

#### Scenario: 寫入失敗復原

- **WHEN** 寫入過程發生錯誤
- **THEN** 從備份檔案復原
- **AND** 清除暫存檔

#### Scenario: 儲存格式

- **WHEN** 儲存別名檔案
- **THEN** 使用 JSON 格式
- **AND** 包含 `version` 欄位（目前為 `"1.0"`）
- **AND** 包含 `aliases` 物件（key 為別名名稱）
- **AND** 包含 `metadata` 物件（totalCount、lastUpdated）

### Requirement: 別名清理

系統 SHALL 提供清理指向不存在 session 的別名功能。

#### Scenario: 清理無效別名

- **WHEN** 呼叫 cleanup 功能
- **THEN** 系統檢查每個別名對應的 session 是否存在
- **AND** 刪除指向不存在 session 的別名
- **AND** 回報清理結果（檢查總數、刪除數量）

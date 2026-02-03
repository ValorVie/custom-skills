## ADDED Requirements

### Requirement: Session 列表查詢

系統 SHALL 提供 session 歷史列表查詢功能，透過 `/sessions list` 指令操作。

#### Scenario: 列出所有 sessions

- **WHEN** 使用者執行 `/sessions` 或 `/sessions list`
- **THEN** 系統列出 `~/.claude/sessions/` 中所有 session 檔案
- **AND** 每筆顯示 ID、日期、時間、大小、行數、別名
- **AND** 依修改時間由新至舊排序
- **AND** 預設最多顯示 50 筆

#### Scenario: 依日期篩選

- **WHEN** 使用者執行 `/sessions list --date 2026-02-01`
- **THEN** 系統僅列出該日期的 session

#### Scenario: 依 ID 搜尋

- **WHEN** 使用者執行 `/sessions list --search abc`
- **THEN** 系統僅列出 short ID 包含 `abc` 的 session

#### Scenario: 限制數量

- **WHEN** 使用者執行 `/sessions list --limit 10`
- **THEN** 系統最多列出 10 筆 session

#### Scenario: Sessions 目錄不存在

- **WHEN** `~/.claude/sessions/` 目錄不存在
- **THEN** 系統顯示空列表，不產生錯誤

### Requirement: Session 載入

系統 SHALL 提供 session 內容載入功能，透過 `/sessions load` 指令操作。

#### Scenario: 依 short ID 載入

- **WHEN** 使用者執行 `/sessions load a1b2c3d4`
- **THEN** 系統找到 short ID 開頭匹配的 session
- **AND** 顯示 session 的檔名、路徑、統計資訊（行數、項目數、大小）
- **AND** 顯示 session 的 title、started、last updated 等 metadata

#### Scenario: 依別名載入

- **WHEN** 使用者執行 `/sessions load my-alias`
- **THEN** 系統先嘗試將輸入解析為別名
- **AND** 若成功解析則載入對應的 session

#### Scenario: 依日期載入（舊格式）

- **WHEN** 使用者執行 `/sessions load 2026-02-01`
- **THEN** 系統找到 `2026-02-01-session.tmp` 檔案並載入

#### Scenario: Session 不存在

- **WHEN** 使用者提供的 ID 或別名找不到對應 session
- **THEN** 系統顯示 `Session not found: <id>` 錯誤訊息

### Requirement: Session 資訊查詢

系統 SHALL 提供 session 詳細資訊查詢功能，透過 `/sessions info` 指令操作。

#### Scenario: 顯示 session 詳細資訊

- **WHEN** 使用者執行 `/sessions info <id|alias>`
- **THEN** 系統顯示 session 的完整資訊
- **AND** 包含 ID、檔名、日期、修改時間
- **AND** 包含內容統計：行數、總項目數、已完成項目數、進行中項目數、大小
- **AND** 包含別名列表（若有）

### Requirement: Session 檔名格式相容

系統 SHALL 同時支援新舊兩種 session 檔名格式。

#### Scenario: 舊格式支援

- **WHEN** session 檔名為 `YYYY-MM-DD-session.tmp`
- **THEN** 系統正確解析日期
- **AND** short ID 顯示為 `(none)`

#### Scenario: 新格式支援

- **WHEN** session 檔名為 `YYYY-MM-DD-<short-id>-session.tmp`
- **THEN** 系統正確解析日期和 short ID
- **AND** short ID 為 8 個以上英數字元

### Requirement: Session Metadata 解析

系統 SHALL 從 session markdown 內容中解析結構化 metadata。

#### Scenario: 解析 session 內容

- **WHEN** 讀取 session 檔案內容
- **THEN** 系統解析 title（第一個 `#` 標題）
- **AND** 解析日期（`**Date:**` 欄位）
- **AND** 解析開始時間（`**Started:**` 欄位）
- **AND** 解析最後更新時間（`**Last Updated:**` 欄位）
- **AND** 解析已完成項目（`### Completed` 區段的 `- [x]` 項目）
- **AND** 解析進行中項目（`### In Progress` 區段的 `- [ ]` 項目）

### Requirement: /sessions Command 路徑

`/sessions` 指令 SHALL 位於 `commands/claude/sessions.md`，嵌入腳本使用 `CLAUDE_PLUGIN_ROOT` 環境變數定位 lib 模組。

#### Scenario: Plugin 環境

- **WHEN** `CLAUDE_PLUGIN_ROOT` 環境變數存在
- **THEN** 使用 `$CLAUDE_PLUGIN_ROOT/scripts/lib/` 路徑載入模組

#### Scenario: Fallback 環境

- **WHEN** `CLAUDE_PLUGIN_ROOT` 環境變數不存在
- **THEN** 使用 `~/.claude/plugins/ecc-hooks/scripts/lib/` 作為 fallback 路徑

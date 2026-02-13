# opencode-hooks Specification

## ADDED Requirements

### Requirement: file.edited 事件處理

Plugin SHALL 處理 OpenCode 的 `file.edited` 事件，對每個被編輯的檔案執行即時自動化。

#### Scenario: JS/TS 檔案自動格式化
- **WHEN** OpenCode 觸發 `file.edited` 事件且檔案副檔名為 `.ts` / `.tsx` / `.js` / `.jsx`
- **THEN** plugin SHALL 檢查 Prettier 是否已安裝
- **THEN** 若已安裝 SHALL 對該檔案執行 Prettier 格式化
- **THEN** 若未安裝 SHALL 靜默跳過，不產生錯誤

#### Scenario: console.log 警告
- **WHEN** OpenCode 觸發 `file.edited` 事件且檔案為 JS/TS 類型
- **THEN** plugin SHALL 檢查檔案中是否存在 `console.log` 語句
- **THEN** 若存在 SHALL 發出警告訊息，包含檔案路徑和行號

#### Scenario: 編輯追蹤
- **WHEN** OpenCode 觸發 `file.edited` 事件
- **THEN** plugin SHALL 將檔案路徑記錄到 session 級別的編輯追蹤清單

### Requirement: session.idle 事件處理

Plugin SHALL 處理 OpenCode 的 `session.idle` 事件，執行 session 級別的彙總作業。

#### Scenario: 彙總稽核報告
- **WHEN** OpenCode 觸發 `session.idle` 事件
- **THEN** plugin SHALL 彙總 session 中所有 file.edited 追蹤的 console.log 警告
- **THEN** 若有警告 SHALL 輸出完整的檔案清單與問題摘要

#### Scenario: 清除追蹤狀態
- **WHEN** session.idle 事件處理完成
- **THEN** plugin SHALL 清除 session 級別的編輯追蹤清單

### Requirement: file.watcher.updated 事件處理

Plugin SHALL 處理 OpenCode 的 `file.watcher.updated` 事件，偵測外部檔案變更。

#### Scenario: 外部 TypeScript 變更偵測
- **WHEN** OpenCode 觸發 `file.watcher.updated` 事件且檔案為 `.ts` / `.tsx`
- **THEN** plugin SHALL 記錄該外部變更到追蹤清單
- **THEN** plugin SHALL 提示使用者檔案已在外部被修改

### Requirement: permission.asked 事件記錄

Plugin SHALL 處理 OpenCode 的 `permission.asked` 事件，提供非侵入式的稽核記錄。

#### Scenario: 權限請求記錄
- **WHEN** OpenCode 觸發 `permission.asked` 事件
- **THEN** plugin SHALL 記錄權限請求的工具名稱和時間戳
- **THEN** 記錄 SHALL 不影響權限授予或拒絕的流程

### Requirement: todo.updated 事件追蹤

Plugin SHALL 處理 OpenCode 的 `todo.updated` 事件，提供任務進度追蹤。

#### Scenario: 任務進度顯示
- **WHEN** OpenCode 觸發 `todo.updated` 事件
- **THEN** plugin SHALL 計算已完成 / 總計任務數量
- **THEN** plugin SHALL 輸出進度摘要（例如「3/5 tasks completed」）

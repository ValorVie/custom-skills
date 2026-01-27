## ADDED Requirements

### Requirement: PostToolUse 程式碼品質 Hooks

系統 SHALL 在 PostToolUse 事件提供程式碼品質檢查機制。

#### Scenario: PostToolUse Edit 觸發

- **WHEN** Edit 工具完成檔案編輯
- **THEN** 根據檔案副檔名觸發對應的品質檢查 hooks
- **AND** 支援 `.ts/.tsx/.js/.jsx` 觸發 JavaScript/TypeScript hooks
- **AND** 支援 `.php` 觸發 PHP hooks
- **AND** 支援 `.py` 觸發 Python hooks

#### Scenario: Hook 執行順序

- **WHEN** 多個 PostToolUse hooks 符合條件
- **THEN** 依序執行：格式化 → 靜態分析 → debug 警告
- **AND** 前一個 hook 失敗不影響後續 hook 執行

### Requirement: Node.js Hook 實作

PostToolUse 程式碼品質 Hooks SHALL 使用 Node.js 實作。

#### Scenario: Node.js One-liner 格式

- **WHEN** 配置 PostToolUse 品質檢查 hook
- **THEN** 使用 `node -e "..."` 格式執行
- **AND** 從 stdin 讀取 JSON 輸入
- **AND** 解析 `tool_input.file_path` 取得編輯的檔案路徑
- **AND** 將原始輸入輸出至 stdout

#### Scenario: 錯誤處理

- **WHEN** Hook 執行過程發生錯誤
- **THEN** 靜默捕捉錯誤不中斷流程
- **AND** 確保原始輸入正確輸出至 stdout
- **AND** 警告訊息輸出至 stderr

## MODIFIED Requirements

### Requirement: Claude Code Hook 支援

系統 SHALL 提供 Claude Code 事件 Hook 的 Python 及 Node.js 實作。

#### Scenario: 支援的 Hook 事件

- **WHEN** Claude Code 觸發事件
- **THEN** 支援 SessionStart 事件
- **AND** 支援 SessionEnd 事件
- **AND** 支援 PreCompact 事件
- **AND** 支援 PreToolUse 事件
- **AND** 支援 PostToolUse 事件
- **AND** 支援 Stop 事件

#### Scenario: Hook 配置格式

- **WHEN** 配置 Hooks
- **THEN** 使用 `hooks.json` 格式
- **AND** 支援 matcher 條件過濾
- **AND** 支援 command 執行腳本
- **AND** command 可使用 Python 或 Node.js

#### Scenario: 混合語言支援

- **WHEN** 同一 hooks.json 配置多個 hooks
- **THEN** 支援 Python 腳本（memory persistence）
- **AND** 支援 Node.js 腳本（程式碼品質檢查）
- **AND** 兩種語言的 hooks 可並存運作

### Requirement: Hook 跨平台相容

所有 Hook 腳本 SHALL 相容 Windows、macOS 和 Linux。

#### Scenario: Python 跨平台執行

- **WHEN** Hook 腳本執行
- **THEN** 使用 Python 標準庫
- **AND** 避免 shell-specific 語法
- **AND** 使用 `pathlib` 處理路徑

#### Scenario: Node.js 跨平台執行

- **WHEN** Node.js Hook 腳本執行
- **THEN** 使用 Node.js 標準庫（fs, path, child_process）
- **AND** 使用 `path.join()` 處理路徑
- **AND** 避免 shell-specific 語法

#### Scenario: 檔案路徑處理

- **WHEN** 存取檔案路徑
- **THEN** 使用 `os.path` 或 `pathlib`（Python）
- **AND** 使用 `path` 模組（Node.js）
- **AND** 正確處理 Windows 與 Unix 路徑分隔符

#### Scenario: 環境變數存取

- **WHEN** 讀取環境變數
- **THEN** 使用 `os.environ.get()`（Python）
- **AND** 使用 `process.env`（Node.js）
- **AND** 提供合理預設值

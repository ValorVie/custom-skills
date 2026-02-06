## ADDED Requirements

### Requirement: Bun 安裝狀態檢查
系統 SHALL 提供函式檢查 Bun 是否已安裝在系統中。

#### Scenario: Bun 已安裝
- **WHEN** 系統執行 Bun 檢查函式
- **AND** Bun 已安裝在系統 PATH 中
- **THEN** 函式回傳 `True`
- **AND** 回傳 Bun 版本號

#### Scenario: Bun 未安裝
- **WHEN** 系統執行 Bun 檢查函式
- **AND** Bun 未安裝在系統 PATH 中
- **THEN** 函式回傳 `False`
- **AND** 不回傳版本號

### Requirement: Bun 套件版本查詢
系統 SHALL 提供函式查詢特定 Bun 全域套件的版本號。

#### Scenario: 套件已安裝
- **WHEN** 系統查詢已安裝的 Bun 套件版本
- **THEN** 函式回傳該套件的版本號字串

#### Scenario: 套件未安裝
- **WHEN** 系統查詢未安裝的 Bun 套件版本
- **THEN** 函式回傳 `None`

### Requirement: Bun 套件安裝
系統 SHALL 在 `ai-dev install` 指令中支援 Bun 套件的自動安裝。

#### Scenario: Bun 已安裝且套件未安裝
- **WHEN** 使用者執行 `ai-dev install`
- **AND** Bun 已安裝
- **AND** Codex 套件未安裝
- **THEN** 系統顯示 "正在安裝 Bun 套件..."
- **AND** 執行 `bun install -g @openai/codex`

#### Scenario: Bun 已安裝且套件已安裝
- **WHEN** 使用者執行 `ai-dev install`
- **AND** Bun 已安裝
- **AND** Codex 套件已安裝
- **THEN** 系統顯示套件版本和 "檢查更新..."
- **AND** 執行 `bun install -g @openai/codex`

#### Scenario: Bun 未安裝
- **WHEN** 使用者執行 `ai-dev install`
- **AND** Bun 未安裝
- **THEN** 系統顯示 Bun 未安裝的警告訊息
- **AND** 顯示 Bun 安裝指引
- **AND** 繼續執行其他安裝步驟（不中斷流程）

#### Scenario: 使用者選擇跳過 Bun 套件
- **WHEN** 使用者執行 `ai-dev install --skip-bun`
- **THEN** 系統顯示 "跳過 Bun 套件安裝"
- **AND** 不執行任何 Bun 相關操作

### Requirement: Bun 套件更新
系統 SHALL 在 `ai-dev update` 指令中支援 Bun 套件的自動更新。

#### Scenario: Bun 已安裝
- **WHEN** 使用者執行 `ai-dev update`
- **AND** Bun 已安裝
- **THEN** 系統顯示 "正在更新 Bun 套件..."
- **AND** 執行 `bun install -g @openai/codex`

#### Scenario: Bun 未安裝
- **WHEN** 使用者執行 `ai-dev update`
- **AND** Bun 未安裝
- **THEN** 系統顯示 "Bun 未安裝，跳過 Bun 套件更新"
- **AND** 繼續執行其他更新步驟

#### Scenario: 使用者選擇跳過 Bun 套件
- **WHEN** 使用者執行 `ai-dev update --skip-bun`
- **THEN** 系統顯示 "跳過 Bun 套件更新"
- **AND** 不執行任何 Bun 相關操作

### Requirement: Bun 安裝指引
系統 SHALL 在 Bun 未安裝時顯示清晰的安裝指引。

#### Scenario: 顯示跨平台安裝指引
- **WHEN** 系統檢測到 Bun 未安裝
- **THEN** 顯示 macOS/Linux 安裝指令
- **AND** 顯示 Windows PowerShell 安裝指令
- **AND** 提示安裝完成後重新執行 `ai-dev install`

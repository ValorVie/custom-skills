# orchestrate-command Specification

## Purpose
TBD

## Requirements

### Requirement: orchestrate 命令存在

系統 SHALL 在 `commands/claude/orchestrate.md` 和 `commands/opencode/orchestrate.md` 提供 multi-agent orchestration 命令。

#### Scenario: 命令檔案存在
- **WHEN** 檢查命令目錄
- **THEN** `commands/claude/orchestrate.md` SHALL 存在
- **THEN** `commands/opencode/orchestrate.md` SHALL 存在
- **THEN** 兩個版本 SHALL 功能等效，僅工具呼叫格式不同

### Requirement: 預定義工作流模板

orchestrate 命令 SHALL 提供 4 種預定義工作流模板。

#### Scenario: feature 工作流
- **WHEN** 使用者執行 `/orchestrate feature`
- **THEN** 系統 SHALL 依序執行：code-architect（規劃）→ test-specialist（TDD 測試骨架）→ 實作 → reviewer（code review）→ security-reviewer（安全審查）
- **THEN** 每個 agent 之間 SHALL 產生結構化 handoff 文件

#### Scenario: bugfix 工作流
- **WHEN** 使用者執行 `/orchestrate bugfix`
- **THEN** 系統 SHALL 依序執行：診斷 → test-specialist（重現測試）→ 修復 → reviewer（驗證）

#### Scenario: refactor 工作流
- **WHEN** 使用者執行 `/orchestrate refactor`
- **THEN** 系統 SHALL 依序執行：code-architect（分析）→ 重構計畫 → 實作 → reviewer（review）→ test-specialist（回歸測試）

#### Scenario: security 工作流
- **WHEN** 使用者執行 `/orchestrate security`
- **THEN** 系統 SHALL 依序執行：security-reviewer（掃描）→ 修復計畫 → 實作 → security-reviewer（驗證）→ reviewer（code review）

### Requirement: 自訂工作流支援

orchestrate 命令 SHALL 支援使用者定義的自訂工作流。

#### Scenario: 自訂 agent 序列
- **WHEN** 使用者執行 `/orchestrate custom` 並指定 agent 清單
- **THEN** 系統 SHALL 依照指定順序執行 agent
- **THEN** 系統 SHALL 在每個 agent 之間產生 handoff 文件

### Requirement: Handoff 文件格式

orchestrate 命令 SHALL 在 agent 之間傳遞結構化 handoff 文件。

#### Scenario: Handoff 文件內容
- **WHEN** 前一個 agent 完成工作
- **THEN** handoff 文件 SHALL 包含：任務摘要、已完成的變更清單、待處理事項、相關檔案路徑
- **THEN** 下一個 agent SHALL 讀取 handoff 文件作為工作起點

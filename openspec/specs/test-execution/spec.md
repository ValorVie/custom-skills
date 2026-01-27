# Spec: Test Execution

## ADDED Requirements

### Requirement: 執行 pytest 測試
系統 SHALL 提供 `ai-dev test` 命令執行 pytest 測試並輸出原始結果。

#### Scenario: 執行所有測試
- **WHEN** 使用者執行 `ai-dev test`
- **THEN** 系統執行 `pytest` 命令
- **AND** 輸出原始測試結果

#### Scenario: 執行指定路徑的測試
- **WHEN** 使用者執行 `ai-dev test tests/test_foo.py`
- **THEN** 系統僅執行指定路徑的測試

#### Scenario: pytest 未安裝
- **WHEN** 使用者執行 `ai-dev test`
- **AND** pytest 未安裝
- **THEN** 系統顯示錯誤訊息
- **AND** 提示安裝指令 `pip install pytest`

### Requirement: AI 分析測試結果
Claude Code 命令 `/custom-skills-test` SHALL 由 AI 分析測試結果並提供建議。

#### Scenario: AI 分析測試摘要
- **WHEN** 測試執行完成
- **THEN** AI 從輸出中提取通過、失敗、跳過的測試數量
- **AND** 顯示測試摘要

#### Scenario: AI 分析失敗測試
- **WHEN** 有測試失敗
- **THEN** AI 分析失敗測試的錯誤訊息
- **AND** 推測可能的失敗原因
- **AND** 提供修復建議

### Requirement: 支援常用測試選項
系統 SHALL 支援常用的 pytest 選項。

#### Scenario: verbose 模式
- **WHEN** 使用者執行 `ai-dev test --verbose`
- **THEN** 系統顯示每個測試的詳細結果

#### Scenario: fail-fast 模式
- **WHEN** 使用者執行 `ai-dev test --fail-fast`
- **AND** 有測試失敗
- **THEN** 系統在第一個失敗後停止執行

#### Scenario: 關鍵字過濾
- **WHEN** 使用者執行 `ai-dev test -k "test_name"`
- **THEN** 系統僅執行名稱包含 "test_name" 的測試

### Requirement: 回傳適當的 exit code
系統 SHALL 根據測試結果回傳適當的 exit code。

#### Scenario: 所有測試通過
- **WHEN** 所有測試通過
- **THEN** 系統回傳 exit code 0

#### Scenario: 有測試失敗
- **WHEN** 有測試失敗
- **THEN** 系統回傳 exit code 1

### Requirement: Claude Code 命令整合
系統 SHALL 提供 `/custom-skills-test` Claude Code 命令。

#### Scenario: 在 Claude Code 中執行測試
- **WHEN** 使用者在 Claude Code 中執行 `/custom-skills-test`
- **THEN** 系統執行測試
- **AND** AI 分析結果並提供建議

#### Scenario: 傳遞選項給 Claude Code 命令
- **WHEN** 使用者執行 `/custom-skills-test --verbose`
- **THEN** 系統以 verbose 模式執行測試

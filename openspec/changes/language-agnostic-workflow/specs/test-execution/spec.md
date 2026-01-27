# Spec: Test Execution (Delta)

## RENAMED Requirements

### Requirement: Claude Code 命令整合
**FROM:** `/custom-skills-test`
**TO:** `/custom-skills-python-test`

## MODIFIED Requirements

### Requirement: Claude Code 命令整合
系統 SHALL 提供 `/custom-skills-python-test` Claude Code 命令。

#### Scenario: 在 Claude Code 中執行測試
- **WHEN** 使用者在 Claude Code 中執行 `/custom-skills-python-test`
- **THEN** 系統執行 pytest 測試
- **AND** AI 分析結果並提供建議

#### Scenario: 傳遞選項給 Claude Code 命令
- **WHEN** 使用者執行 `/custom-skills-python-test --verbose`
- **THEN** 系統以 verbose 模式執行測試

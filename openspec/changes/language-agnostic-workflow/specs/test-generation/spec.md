# Spec: Test Generation (Delta)

## RENAMED Requirements

### Requirement: Claude Code 命令整合
**FROM:** `/custom-skills-derive-tests`
**TO:** `/custom-skills-python-derive-tests`

## MODIFIED Requirements

### Requirement: Claude Code 命令整合
系統 SHALL 提供 `/custom-skills-python-derive-tests` Claude Code 命令。

#### Scenario: 在 Claude Code 中生成測試
- **WHEN** 使用者在 Claude Code 中執行 `/custom-skills-python-derive-tests specs/`
- **THEN** 系統執行 CLI 讀取 specs
- **AND** AI 生成 pytest 測試程式碼
- **AND** AI 將測試寫入適當位置

#### Scenario: 顯示生成結果摘要
- **WHEN** pytest 測試生成完成
- **THEN** AI 顯示生成的測試檔案清單
- **AND** AI 顯示每個檔案包含的測試數量
- **AND** 提示下一步執行 `/custom-skills-python-test`

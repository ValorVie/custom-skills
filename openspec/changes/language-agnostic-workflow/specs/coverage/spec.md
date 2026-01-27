# Spec: Coverage (Delta)

## RENAMED Requirements

### Requirement: Claude Code 命令整合
**FROM:** `/custom-skills-coverage`
**TO:** `/custom-skills-python-coverage`

## MODIFIED Requirements

### Requirement: Claude Code 命令整合
系統 SHALL 提供 `/custom-skills-python-coverage` Claude Code 命令。

#### Scenario: 在 Claude Code 中執行覆蓋率分析
- **WHEN** 使用者在 Claude Code 中執行 `/custom-skills-python-coverage`
- **THEN** 系統執行覆蓋率分析
- **AND** AI 分析結果並提供建議

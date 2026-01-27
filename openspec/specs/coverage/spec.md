# Spec: Coverage Analysis

## ADDED Requirements

### Requirement: 執行覆蓋率分析
系統 SHALL 提供 `ai-dev coverage` 命令執行覆蓋率分析並輸出原始結果。

#### Scenario: 執行覆蓋率分析
- **WHEN** 使用者執行 `ai-dev coverage`
- **THEN** 系統執行 `pytest --cov --cov-report=term-missing`
- **AND** 輸出原始覆蓋率報告

#### Scenario: 指定原始碼路徑
- **WHEN** 使用者執行 `ai-dev coverage --source script/`
- **THEN** 系統僅分析指定路徑的覆蓋率

#### Scenario: pytest-cov 未安裝
- **WHEN** 使用者執行 `ai-dev coverage`
- **AND** pytest-cov 未安裝
- **THEN** 系統顯示錯誤訊息
- **AND** 提示安裝指令 `pip install pytest-cov`

### Requirement: AI 分析覆蓋率報告
Claude Code 命令 `/custom-skills-coverage` SHALL 由 AI 分析覆蓋率報告並提供建議。

#### Scenario: AI 分析整體覆蓋率
- **WHEN** 覆蓋率分析完成
- **THEN** AI 從輸出中提取整體覆蓋率百分比
- **AND** 顯示整體覆蓋率摘要

#### Scenario: AI 分析各檔案覆蓋率
- **WHEN** 覆蓋率分析完成
- **THEN** AI 以表格顯示各檔案覆蓋率
- **AND** 標示低覆蓋率檔案

#### Scenario: AI 提供改善建議
- **WHEN** 有檔案覆蓋率低於標準
- **THEN** AI 分析未覆蓋的程式碼區塊
- **AND** 提供應撰寫的測試建議

### Requirement: Claude Code 命令整合
系統 SHALL 提供 `/custom-skills-coverage` Claude Code 命令。

#### Scenario: 在 Claude Code 中執行覆蓋率分析
- **WHEN** 使用者在 Claude Code 中執行 `/custom-skills-coverage`
- **THEN** 系統執行覆蓋率分析
- **AND** AI 分析結果並提供建議

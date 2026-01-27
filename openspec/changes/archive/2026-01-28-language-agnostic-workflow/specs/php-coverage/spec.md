# Spec: PHP Coverage

## ADDED Requirements

### Requirement: 執行 PHPUnit 覆蓋率分析
系統 SHALL 提供 `/custom-skills-php-coverage` Claude Code 命令執行覆蓋率分析。

#### Scenario: 執行覆蓋率分析
- **WHEN** 使用者執行 `/custom-skills-php-coverage`
- **THEN** 系統執行 `./vendor/bin/phpunit --coverage-text`
- **AND** 輸出原始覆蓋率報告

#### Scenario: 指定原始碼路徑
- **WHEN** 使用者執行 `/custom-skills-php-coverage --source src/`
- **THEN** 系統僅分析指定路徑的覆蓋率

#### Scenario: 覆蓋率驅動未安裝
- **WHEN** 使用者執行 `/custom-skills-php-coverage`
- **AND** PCOV 或 Xdebug 未安裝
- **THEN** 系統顯示錯誤訊息
- **AND** 提示安裝 PCOV 或 Xdebug

### Requirement: AI 分析 PHP 覆蓋率報告
Claude Code 命令 `/custom-skills-php-coverage` SHALL 由 AI 分析覆蓋率報告並提供建議。

#### Scenario: AI 分析整體覆蓋率
- **WHEN** 覆蓋率分析完成
- **THEN** AI 從輸出中提取整體覆蓋率百分比（Lines、Methods、Classes）
- **AND** 顯示整體覆蓋率摘要

#### Scenario: AI 分析各類別覆蓋率
- **WHEN** 覆蓋率分析完成
- **THEN** AI 以表格顯示各類別覆蓋率
- **AND** 標示低覆蓋率類別

#### Scenario: AI 提供改善建議
- **WHEN** 有類別覆蓋率低於標準
- **THEN** AI 分析未覆蓋的方法
- **AND** 提供應撰寫的測試建議

### Requirement: 支援多種覆蓋率輸出格式
系統 SHALL 支援 PHPUnit 的覆蓋率輸出選項。

#### Scenario: HTML 報告
- **WHEN** 使用者執行 `/custom-skills-php-coverage --html coverage/`
- **THEN** 系統生成 HTML 覆蓋率報告到指定目錄

#### Scenario: Clover XML 報告
- **WHEN** 使用者執行 `/custom-skills-php-coverage --clover coverage.xml`
- **THEN** 系統生成 Clover XML 格式報告

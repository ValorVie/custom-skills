# Spec: PHP Test Execution

## ADDED Requirements

### Requirement: 執行 PHPUnit 測試
系統 SHALL 提供 `/custom-skills-php-test` Claude Code 命令執行 PHPUnit 測試。

#### Scenario: 執行所有測試
- **WHEN** 使用者執行 `/custom-skills-php-test`
- **THEN** 系統執行 `./vendor/bin/phpunit` 命令
- **AND** 輸出原始測試結果

#### Scenario: 執行指定路徑的測試
- **WHEN** 使用者執行 `/custom-skills-php-test tests/Unit/UserTest.php`
- **THEN** 系統僅執行指定路徑的測試

#### Scenario: PHPUnit 未安裝
- **WHEN** 使用者執行 `/custom-skills-php-test`
- **AND** `./vendor/bin/phpunit` 不存在
- **THEN** 系統顯示錯誤訊息
- **AND** 提示安裝指令 `composer require --dev phpunit/phpunit`

### Requirement: AI 分析 PHPUnit 測試結果
Claude Code 命令 `/custom-skills-php-test` SHALL 由 AI 分析測試結果並提供建議。

#### Scenario: AI 分析測試摘要
- **WHEN** PHPUnit 測試執行完成
- **THEN** AI 從輸出中提取通過、失敗、跳過的測試數量
- **AND** 顯示測試摘要

#### Scenario: AI 分析失敗測試
- **WHEN** 有測試失敗
- **THEN** AI 分析失敗測試的錯誤訊息
- **AND** 推測可能的失敗原因
- **AND** 提供修復建議

### Requirement: 支援常用 PHPUnit 選項
系統 SHALL 支援常用的 PHPUnit 選項。

#### Scenario: verbose 模式
- **WHEN** 使用者執行 `/custom-skills-php-test --verbose`
- **THEN** 系統以 `-v` 選項執行 PHPUnit

#### Scenario: stop-on-failure 模式
- **WHEN** 使用者執行 `/custom-skills-php-test --stop-on-failure`
- **AND** 有測試失敗
- **THEN** 系統在第一個失敗後停止執行

#### Scenario: filter 過濾
- **WHEN** 使用者執行 `/custom-skills-php-test --filter "testMethodName"`
- **THEN** 系統僅執行名稱符合的測試

### Requirement: 回傳適當的 exit code
系統 SHALL 根據測試結果回傳適當的 exit code。

#### Scenario: 所有測試通過
- **WHEN** 所有 PHPUnit 測試通過
- **THEN** 系統回傳 exit code 0

#### Scenario: 有測試失敗
- **WHEN** 有 PHPUnit 測試失敗
- **THEN** 系統回傳非零 exit code

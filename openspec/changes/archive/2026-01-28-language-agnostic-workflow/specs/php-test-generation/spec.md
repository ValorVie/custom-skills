# Spec: PHP Test Generation

## ADDED Requirements

### Requirement: AI 理解場景語義並生成 PHPUnit 測試
Claude Code 命令 `/custom-skills-php-derive-tests` SHALL 由 AI 理解 specs 中的 WHEN/THEN 場景語義並生成 PHPUnit 測試。

#### Scenario: AI 解析 WHEN/THEN 格式
- **WHEN** specs 內容包含 WHEN/THEN 場景
- **THEN** AI 識別 WHEN 為前置條件
- **AND** AI 識別 AND 為附加條件
- **AND** AI 識別 THEN 為預期結果

#### Scenario: AI 理解業務語義
- **WHEN** specs 內容描述業務場景
- **THEN** AI 理解場景的業務含義
- **AND** AI 能將業務語義對應到 PHP 程式碼概念

### Requirement: AI 生成 PHPUnit 測試程式碼
Claude Code 命令 `/custom-skills-php-derive-tests` SHALL 由 AI 生成完整可執行的 PHPUnit 測試程式碼。

#### Scenario: 生成測試類別
- **WHEN** specs 包含 `### Requirement:` 區塊
- **THEN** AI 生成對應的 `class {Name}Test extends TestCase` 測試類別
- **AND** 類別包含適當的 namespace

#### Scenario: 生成測試方法
- **WHEN** specs 包含 `#### Scenario:` 區塊
- **THEN** AI 生成對應的 `public function test_{scenario_name}(): void` 測試方法
- **AND** 方法包含 `#[Test]` 或 `@test` 註解

#### Scenario: 填寫 AAA 區塊
- **WHEN** AI 生成測試方法
- **THEN** AI 根據 WHEN 條件填寫 Arrange 區塊
- **AND** AI 根據業務邏輯填寫 Act 區塊
- **AND** AI 根據 THEN 預期填寫 Assert 區塊

### Requirement: AI 決定測試檔案位置
Claude Code 命令 `/custom-skills-php-derive-tests` SHALL 由 AI 決定測試檔案的適當位置。

#### Scenario: 根據專案結構決定位置
- **WHEN** AI 生成測試程式碼
- **THEN** AI 讀取專案的測試目錄結構（通常為 `tests/`）
- **AND** AI 決定測試檔案的適當路徑

#### Scenario: 遵循 PSR-4 命名空間
- **WHEN** AI 生成測試類別
- **THEN** AI 根據 composer.json 的 autoload-dev 設定決定 namespace
- **AND** 檔案路徑與 namespace 一致

#### Scenario: 使用者指定輸出目錄
- **WHEN** 使用者執行 `/custom-skills-php-derive-tests --output tests/Unit/`
- **THEN** AI 將測試檔案寫入指定目錄

### Requirement: 顯示生成結果摘要
系統 SHALL 在測試生成完成後顯示摘要。

#### Scenario: 顯示生成結果
- **WHEN** PHPUnit 測試生成完成
- **THEN** AI 顯示生成的測試檔案清單
- **AND** AI 顯示每個檔案包含的測試數量
- **AND** 提示下一步執行 `/custom-skills-php-test`

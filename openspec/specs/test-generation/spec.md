# Spec: Test Generation

## ADDED Requirements

### Requirement: 讀取 specs 檔案
系統 SHALL 提供 `ai-dev derive-tests` 命令讀取 OpenSpec specs 檔案並輸出內容。

#### Scenario: 讀取目錄下的所有 specs
- **WHEN** 使用者執行 `ai-dev derive-tests specs/`
- **THEN** 系統找到目錄下所有 `.md` 檔案
- **AND** 輸出每個檔案的內容

#### Scenario: 讀取單一 spec 檔案
- **WHEN** 使用者執行 `ai-dev derive-tests specs/feature/spec.md`
- **THEN** 系統輸出該檔案的內容

#### Scenario: 路徑不存在
- **WHEN** 使用者執行 `ai-dev derive-tests nonexistent/`
- **AND** 路徑不存在
- **THEN** 系統顯示錯誤訊息
- **AND** 回傳非零 exit code

### Requirement: AI 理解場景語義
Claude Code 命令 `/custom-skills-derive-tests` SHALL 由 AI 理解 specs 中的 WHEN/THEN 場景語義。

#### Scenario: AI 解析 WHEN/THEN 格式
- **WHEN** specs 內容包含 WHEN/THEN 場景
- **THEN** AI 識別 WHEN 為前置條件
- **AND** AI 識別 AND 為附加條件
- **AND** AI 識別 THEN 為預期結果

#### Scenario: AI 理解業務語義
- **WHEN** specs 內容描述業務場景
- **THEN** AI 理解場景的業務含義
- **AND** AI 能將業務語義對應到程式碼概念

### Requirement: AI 生成測試程式碼
Claude Code 命令 `/custom-skills-derive-tests` SHALL 由 AI 生成完整可執行的 pytest 測試程式碼。

#### Scenario: 生成測試類別
- **WHEN** specs 包含 `### Requirement:` 區塊
- **THEN** AI 生成對應的 `class Test{Name}:` 測試類別
- **AND** 類別 docstring 包含 Requirement 名稱

#### Scenario: 生成測試方法
- **WHEN** specs 包含 `#### Scenario:` 區塊
- **THEN** AI 生成對應的 `def test_{scenario_name}():` 測試方法
- **AND** 方法 docstring 包含 Scenario 名稱

#### Scenario: 填寫 AAA 區塊
- **WHEN** AI 生成測試方法
- **THEN** AI 根據 WHEN 條件填寫 Arrange 區塊
- **AND** AI 根據業務邏輯填寫 Act 區塊
- **AND** AI 根據 THEN 預期填寫 Assert 區塊

### Requirement: AI 決定測試檔案位置
Claude Code 命令 `/custom-skills-derive-tests` SHALL 由 AI 決定測試檔案的適當位置。

#### Scenario: 根據專案結構決定位置
- **WHEN** AI 生成測試程式碼
- **THEN** AI 讀取專案的測試目錄結構
- **AND** AI 決定測試檔案的適當路徑

#### Scenario: 使用者指定輸出目錄
- **WHEN** 使用者執行 `/custom-skills-derive-tests --output tests/`
- **THEN** AI 將測試檔案寫入指定目錄

### Requirement: Claude Code 命令整合
系統 SHALL 提供 `/custom-skills-derive-tests` Claude Code 命令。

#### Scenario: 在 Claude Code 中生成測試
- **WHEN** 使用者在 Claude Code 中執行 `/custom-skills-derive-tests specs/`
- **THEN** 系統執行 CLI 讀取 specs
- **AND** AI 生成測試程式碼
- **AND** AI 將測試寫入適當位置

#### Scenario: 顯示生成結果摘要
- **WHEN** 測試生成完成
- **THEN** AI 顯示生成的測試檔案清單
- **AND** AI 顯示每個檔案包含的測試數量

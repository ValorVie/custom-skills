# standards-profiles Specification

## Purpose
TBD - created by archiving change integrate-ecc-full-expansion. Update Purpose after archive.
## Requirements
### Requirement: 標準體系多 Profile 支援

系統 SHALL 支援多套 coding standards 體系，允許使用者根據專案需求切換。

#### Scenario: UDS 體系（預設）

- **GIVEN** 使用者未指定體系
- **WHEN** 載入標準
- **THEN** 使用 UDS (Universal Dev Standards) 體系
- **AND** 包含繁體中文提交訊息規範
- **AND** 包含完整 SDD/TDD/BDD/ATDD 整合
- **AND** 包含詳盡的 Code Review Checklist

#### Scenario: ECC 體系

- **GIVEN** 使用者執行 `ai-dev standards use ecc`
- **WHEN** 載入標準
- **THEN** 使用 ECC (everything-claude-code) 體系
- **AND** 採用 TypeScript/React 專注的編碼標準
- **AND** 採用實戰導向的 TDD 工作流
- **AND** 採用英文提交訊息類型

#### Scenario: Minimal 體系

- **GIVEN** 使用者執行 `ai-dev standards use minimal`
- **WHEN** 載入標準
- **THEN** 使用 Minimal 體系
- **AND** 僅包含基礎程式碼品質規範
- **AND** 僅包含簡化的測試要求

### Requirement: Profile 設定檔

系統 SHALL 使用 YAML 檔案定義各 Profile 的內容。

#### Scenario: Profile 定義格式

- **WHEN** 定義新 Profile
- **THEN** 建立 `.standards/profiles/<name>.yaml`
- **AND** 包含 `name` 欄位（Profile 名稱）
- **AND** 包含 `description` 欄位（描述）
- **AND** 包含 `includes` 欄位（包含的標準檔案列表）
- **AND** 可選 `inherits` 欄位（繼承的 Profile）
- **AND** 可選 `overrides` 欄位（覆寫的設定）

#### Scenario: Profile 繼承

- **GIVEN** Profile A 定義 `inherits: B`
- **WHEN** 載入 Profile A
- **THEN** 先載入 Profile B 的所有標準
- **AND** 再套用 Profile A 的 includes 與 overrides

#### Scenario: 啟用 Profile

- **WHEN** 使用者執行 `ai-dev standards use <profile>`
- **THEN** 更新 `.standards/active-profile.yaml`
- **AND** 記錄當前啟用的 Profile 名稱

### Requirement: 標準切換 CLI

系統 SHALL 提供 CLI 指令切換與管理標準體系。

#### Scenario: 切換體系

- **WHEN** 使用者執行 `ai-dev standards use ecc`
- **THEN** 驗證 ecc Profile 存在
- **AND** 更新 `active-profile.yaml`
- **AND** 顯示切換成功訊息

#### Scenario: 列出可用體系

- **WHEN** 使用者執行 `ai-dev standards list`
- **THEN** 列出所有可用的 Profile
- **AND** 標示當前啟用的 Profile
- **AND** 顯示每個 Profile 的描述

#### Scenario: 無效 Profile 處理

- **GIVEN** 使用者指定不存在的 Profile
- **WHEN** 執行 `ai-dev standards use invalid`
- **THEN** 顯示錯誤訊息
- **AND** 列出可用的 Profile

### Requirement: 非破壞性切換

標準體系切換 SHALL 為非破壞性操作，不刪除使用者自訂內容。

#### Scenario: 切換保留自訂內容

- **GIVEN** 使用者在 `.standards/` 有自訂檔案
- **WHEN** 切換標準體系
- **THEN** 保留所有自訂檔案
- **AND** 僅變更 `active-profile.yaml`

#### Scenario: 切換可回復

- **GIVEN** 使用者從 UDS 切換到 ECC
- **WHEN** 執行 `ai-dev standards use uds`
- **THEN** 恢復使用 UDS 體系
- **AND** 無需額外設定

### Requirement: 內建 Profile 定義

系統 SHALL 提供三個內建 Profile。

#### Scenario: UDS Profile 內容

- **GIVEN** 預設 UDS Profile
- **THEN** 包含 `commit-message.ai.yaml`（繁體中文類型）
- **AND** 包含 `traditional-chinese.ai.yaml`（語言設定）
- **AND** 包含 `test-driven-development.md`（完整 TDD）
- **AND** 包含 `code-review-checklist.md`（詳盡清單）
- **AND** 包含 `spec-driven-development.md`（SDD 規範）

#### Scenario: ECC Profile 內容

- **GIVEN** ECC Profile
- **THEN** inherits `minimal`
- **AND** overrides commit-message 使用英文類型
- **AND** overrides testing coverage-threshold 為 80%
- **AND** 參考 `sources/ecc/skills/coding-standards/`

#### Scenario: Minimal Profile 內容

- **GIVEN** Minimal Profile
- **THEN** 僅包含 `checkin-standards.md`（基礎）
- **AND** 僅包含 `testing.ai.yaml`（簡化）


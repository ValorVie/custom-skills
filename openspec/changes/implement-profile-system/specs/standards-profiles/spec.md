# Spec Delta: standards-profiles

## Purpose

更新 `standards-profiles` 規格，加入 Profile 定義檔案的詳細格式要求與載入邏輯需求。

---

## MODIFIED Requirements

### Requirement: Profile 設定檔格式

系統 SHALL 使用 YAML 檔案定義各 Profile 的內容，並遵循以下格式規範。

#### Scenario: Profile 定義格式（更新）

- **WHEN** 定義新 Profile
- **THEN** 建立 `profiles/<name>.yaml`
- **AND** 包含必要欄位：
  - `name`：Profile 識別碼（與檔名一致）
  - `display_name`：顯示名稱（供 UI 使用）
  - `description`：描述（10-500 字元）
  - `version`：Profile 定義格式版本（如 `1.0.0`）
  - `includes`：包含的標準檔案列表（至少 1 個）
- **AND** 可選欄位：
  - `inherits`：繼承的 Profile 名稱
  - `overrides`：覆寫的設定（YAML 結構）
  - `author`：作者資訊
  - `created`：建立日期
  - `updated`：更新日期
  - `tags`：標籤列表

#### Scenario: Profile 檔名與 name 一致性

- **GIVEN** Profile 定義檔案 `ecc.yaml`
- **WHEN** 載入 Profile
- **THEN** 檔案中的 `name` 欄位必須為 `ecc`
- **AND** 若不一致，應顯示錯誤訊息

#### Scenario: Profile version 格式驗證

- **GIVEN** Profile 定義檔案
- **WHEN** 載入 Profile
- **THEN** `version` 欄位必須符合語意化版本格式（如 `1.0.0`、`2.1.3`）
- **AND** 若格式錯誤，應顯示警告訊息

#### Scenario: includes 檔案存在性驗證

- **GIVEN** Profile 定義檔案包含 `includes` 欄位
- **WHEN** 載入 Profile
- **THEN** 驗證所有 `includes` 中的檔案存在於 `.standards/` 目錄
- **AND** 若檔案不存在，應顯示警告訊息並跳過該檔案

---

## ADDED Requirements

### Requirement: Profile 載入邏輯

系統 SHALL 提供 Profile 載入與解析邏輯，處理繼承與合併。

#### Scenario: 載入單一 Profile

- **GIVEN** Profile 檔案 `uds.yaml` 存在
- **WHEN** 呼叫 `load_profile("uds")`
- **THEN** 返回解析後的 Profile 字典
- **AND** 包含所有定義的欄位（name, display_name, description, version, includes）

#### Scenario: 載入含繼承的 Profile

- **GIVEN** Profile 檔案 `ecc.yaml` 定義 `inherits: minimal`
- **AND** Profile 檔案 `minimal.yaml` 存在
- **WHEN** 呼叫 `load_profile("ecc")`
- **THEN** 遞迴載入 `minimal.yaml`
- **AND** 合併父子 Profile 的 `includes` 欄位（父 + 子）
- **AND** 合併父子 Profile 的 `overrides` 欄位（子覆蓋父）
- **AND** 其他欄位使用子 Profile 的值

#### Scenario: 偵測循環繼承

- **GIVEN** Profile A 定義 `inherits: B`
- **AND** Profile B 定義 `inherits: A`
- **WHEN** 呼叫 `load_profile("A")`
- **THEN** 拋出 `ValueError` 錯誤
- **AND** 錯誤訊息包含繼承鏈（如 "Circular inheritance: A → B → A"）

#### Scenario: 處理 Profile 不存在

- **GIVEN** Profile 檔案 `invalid.yaml` 不存在
- **WHEN** 呼叫 `load_profile("invalid")`
- **THEN** 拋出 `ValueError` 錯誤
- **AND** 錯誤訊息為 "Profile 'invalid' not found"

### Requirement: Profile 合併邏輯

系統 SHALL 提供 Profile 合併函式，正確處理繼承關係。

#### Scenario: 合併 includes 欄位

- **GIVEN** 父 Profile 包含 `includes: ['a.yaml', 'b.yaml']`
- **AND** 子 Profile 包含 `includes: ['c.yaml']`
- **WHEN** 呼叫 `merge_profiles(parent, child)`
- **THEN** 返回的 `includes` 為 `['a.yaml', 'b.yaml', 'c.yaml']`
- **AND** 順序為父在前、子在後

#### Scenario: 合併 overrides 欄位（深度合併）

- **GIVEN** 父 Profile 包含 `overrides: {setting1: {key1: 'value1'}}`
- **AND** 子 Profile 包含 `overrides: {setting1: {key2: 'value2'}, setting2: 'value'}`
- **WHEN** 呼叫 `merge_profiles(parent, child)`
- **THEN** 返回的 `overrides` 為：
  ```yaml
  setting1:
    key1: 'value1'  # from parent
    key2: 'value2'  # from child
  setting2: 'value' # from child
  ```
- **AND** 使用深度合併（不覆蓋整個 setting1）

#### Scenario: 子 Profile 覆寫父 Profile 的基本欄位

- **GIVEN** 父 Profile `name: minimal`
- **AND** 子 Profile `name: ecc`
- **WHEN** 呼叫 `merge_profiles(parent, child)`
- **THEN** 返回的 `name` 為 `ecc`（子覆蓋父）
- **AND** 同樣規則適用於 `display_name`、`description`、`version` 等欄位

---

## MODIFIED Requirements (Updated Scenarios)

### Requirement: 標準切換 CLI

#### Scenario: 列出可用體系（更新）

- **WHEN** 使用者執行 `ai-dev standards list`
- **THEN** 掃描 `profiles/` 目錄
- **AND** 列出所有 `.yaml` 檔案的名稱（去掉副檔名）
- **AND** 顯示每個 Profile 的 `display_name`（若可載入）
- **AND** 標示當前啟用的 Profile

#### Scenario: 顯示 Profile 詳細資訊（更新）

- **WHEN** 使用者執行 `ai-dev standards show ecc`
- **THEN** 呼叫 `load_profile("ecc")` 載入 Profile
- **AND** 顯示完整資訊：
  - `display_name` 與 `description`
  - `version`
  - `inherits`（若有）
  - `includes` 清單（顯示數量與檔案名稱）
  - `overrides`（若有，使用 JSON 格式美化輸出）
- **AND** 若是目前啟用的 Profile，顯示「(目前啟用)」標記

### Requirement: 內建 Profile 定義

#### Scenario: UDS Profile 內容（更新）

- **GIVEN** 內建 UDS Profile
- **THEN** 定義檔案為 `profiles/uds.yaml`
- **AND** 包含完整欄位：
  - `name: uds`
  - `display_name: "Universal Dev Standards"`
  - `description: "完整的 UDS 標準體系..."`
  - `version: "1.0.0"`
  - `includes:`（至少 10+ 個標準檔案）
- **AND** 無 `inherits` 欄位（根 Profile）

#### Scenario: ECC Profile 內容（更新）

- **GIVEN** 內建 ECC Profile
- **THEN** 定義檔案為 `profiles/ecc.yaml`
- **AND** 包含完整欄位：
  - `name: ecc`
  - `display_name: "Everything Claude Code"`
  - `description: "ECC 標準體系..."`
  - `version: "1.0.0"`
  - `inherits: "minimal"`
  - `includes:`（額外的標準檔案）
  - `overrides:`（覆寫設定，如 commit-message 語言）

#### Scenario: Minimal Profile 內容（更新）

- **GIVEN** 內建 Minimal Profile
- **THEN** 定義檔案為 `profiles/minimal.yaml`
- **AND** 包含完整欄位：
  - `name: minimal`
  - `display_name: "Minimal Standards"`
  - `description: "基礎標準體系..."`
  - `version: "1.0.0"`
  - `includes:`（僅 3-5 個核心標準）
- **AND** 無 `inherits` 欄位（根 Profile）

---

## Notes

- 此 spec delta 保持與現有 `standards-profiles` 規格的相容性
- 新增的欄位（`display_name`、`version`）為必要欄位，確保 Profile 定義的完整性
- 載入邏輯與合併邏輯的需求確保系統能正確處理繼承關係
- 所有錯誤處理場景（循環繼承、檔案不存在）已明確定義

---

## Relationships

- **相關規格**：`tui-standards-profile`（TUI 使用此規格定義的 Profile 載入邏輯）
- **依賴**：無（此規格為基礎規格）
- **影響**：所有使用 Profile 系統的功能（CLI、TUI）

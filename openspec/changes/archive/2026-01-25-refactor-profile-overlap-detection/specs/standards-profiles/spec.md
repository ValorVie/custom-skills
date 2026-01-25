## MODIFIED Requirements

### Requirement: 標準體系多 Profile 支援

系統 SHALL 支援多套 coding standards 體系，允許使用者根據專案需求切換。切換機制基於**重疊檢測**，停用衝突項目而非複製檔案。

#### Scenario: UDS 體系（預設）

- **GIVEN** 使用者選擇 UDS profile
- **WHEN** 執行 `ai-dev standards switch uds`
- **THEN** 更新 `disabled.yaml` 停用 ECC 專屬項目
- **AND** 在重疊群組中選擇 UDS 版本
- **AND** 保留 `.standards/*.ai.yaml` 格式
- **AND** 包含繁體中文提交訊息規範

#### Scenario: ECC 體系

- **GIVEN** 使用者選擇 ECC profile
- **WHEN** 執行 `ai-dev standards switch ecc`
- **THEN** 更新 `disabled.yaml` 停用 UDS 專屬項目
- **AND** 在重疊群組中選擇 ECC 版本
- **AND** 保留 ECC 原生 Markdown 格式（skills, commands, agents, hooks）
- **AND** 採用英文提交訊息類型

#### Scenario: Minimal 體系

- **GIVEN** 使用者選擇 Minimal profile
- **WHEN** 執行 `ai-dev standards switch minimal`
- **THEN** 更新 `disabled.yaml` 停用大部分項目
- **AND** 僅保留核心功能（commit-message, basic testing）

### Requirement: Profile 設定檔

系統 SHALL 使用 YAML 檔案定義各 Profile 的重疊偏好與停用項目。

#### Scenario: Profile 定義格式

- **WHEN** 定義 Profile
- **THEN** 建立 `profiles/<name>.yaml`
- **AND** 包含 `name` 欄位（Profile 名稱）
- **AND** 包含 `display_name` 欄位（顯示名稱）
- **AND** 包含 `description` 欄位（描述）
- **AND** 包含 `overlap_preference` 欄位（重疊群組偏好）
- **AND** 可選 `enable_exclusive` 欄位（獨有項目啟用設定）
- **AND** 可選 `exceptions` 欄位（例外設定）

#### Scenario: 啟用 Profile

- **WHEN** 使用者執行 `ai-dev standards switch <profile>`
- **THEN** 載入 `profiles/overlaps.yaml`
- **AND** 根據 `overlap_preference` 計算停用項目
- **AND** 更新 `.claude/disabled.yaml`
- **AND** 更新 `profiles/active.yaml`

## ADDED Requirements

### Requirement: 重疊定義檔案

系統 SHALL 使用 `profiles/overlaps.yaml` 定義各體系間的功能重疊。

#### Scenario: 重疊群組定義

- **GIVEN** 需要定義重疊群組
- **WHEN** 編輯 `profiles/overlaps.yaml`
- **THEN** 在 `groups` 下定義群組名稱
- **AND** 每個群組包含多個體系的對應項目
- **AND** 每個體系列出其 skills, standards, commands, agents 等

#### Scenario: 獨有項目定義

- **GIVEN** 某些項目無重疊對應
- **WHEN** 編輯 `profiles/overlaps.yaml`
- **THEN** 在 `exclusive` 下定義體系獨有項目
- **AND** 這些項目可在 profile 中選擇啟用或停用

#### Scenario: 自動重疊偵測

- **GIVEN** 使用者執行 `/upstream-compare`
- **WHEN** 分析上游 repo
- **THEN** 輸出 `overlap_analysis` 欄位
- **AND** 識別本地與上游的重疊項目
- **AND** 提供 `overlaps.yaml` 更新建議

### Requirement: disabled.yaml 來源標記

系統 SHALL 在 disabled.yaml 中區分 profile 停用與手動停用。

#### Scenario: Profile 停用標記

- **WHEN** profile 切換停用項目
- **THEN** 將項目記錄在 `_profile_disabled` 欄位
- **AND** 記錄當前 profile 名稱在 `_profile` 欄位

#### Scenario: 手動停用保留

- **GIVEN** 使用者手動停用了某項目
- **WHEN** 切換 profile
- **THEN** 保留 `_manual` 欄位中的項目
- **AND** 不覆蓋使用者的手動停用設定

#### Scenario: 向後相容

- **GIVEN** 現有工具讀取 disabled.yaml
- **WHEN** 讀取 skills, commands, agents, standards 欄位
- **THEN** 取得合併後的停用項目列表（profile + 手動）
- **AND** 無需了解來源細節

### Requirement: 重疊預覽

系統 SHALL 提供切換前的影響預覽功能。

#### Scenario: Dry-run 模式

- **WHEN** 使用者執行 `ai-dev standards switch <profile> --dry-run`
- **THEN** 顯示將被停用的項目列表
- **AND** 顯示將被啟用的項目列表
- **AND** 不實際執行切換

#### Scenario: Show 命令重疊分析

- **WHEN** 使用者執行 `ai-dev standards show <profile>`
- **THEN** 顯示各重疊群組的選擇
- **AND** 顯示獨有功能的啟用狀態
- **AND** 顯示例外設定

## REMOVED Requirements

### Requirement: Profile 繼承

**Reason**: 重疊定義取代繼承機制，更直觀且符合需求本質

**Migration**: 原 `inherits` 欄位改為在 overlaps.yaml 中定義重疊關係

### Requirement: Profile includes

**Reason**: 不再需要列出包含的標準檔案，改為定義重疊偏好

**Migration**: 原 `includes` 欄位移除，由 overlaps.yaml 的 groups 定義

### Requirement: Profile overrides

**Reason**: 不複製 YAML 檔案，故無需覆寫機制

**Migration**: 需要調整行為的 skill 可讀取 active profile 自行調整

### Requirement: 標準檔案複製

**Reason**: 違反各體系原生格式原則

**Migration**: 改為更新 disabled.yaml 停用衝突項目

# Spec: Source Filter

## ADDED Requirements

### Requirement: 篩選列新增來源下拉選單
TUI 篩選列須在現有的 Target 和 Type 選單旁新增 Source 下拉選單。

#### Scenario: 啟動時顯示來源篩選器
- **WHEN** 使用者開啟 TUI
- **THEN** 篩選列顯示 Target、Type、Source 三個下拉選單
- **AND** Source 下拉選單預設為「All」

### Requirement: 來源篩選選項
Source 下拉選單須提供以下選項：
- All（預設）
- universal-dev-standards
- custom-skills
- obsidian-skills
- anthropic-skills
- everything-claude-code
- user

#### Scenario: 顯示所有來源選項
- **WHEN** 使用者點擊 Source 下拉選單
- **THEN** 顯示所有已配置的來源選項
- **AND** 目前選擇的選項有標示

### Requirement: 依來源篩選資源清單
資源清單須依據選擇的來源進行篩選。

#### Scenario: 篩選至單一來源
- **WHEN** 使用者從 Source 下拉選單選擇「custom-skills」
- **THEN** 僅顯示來源為 custom-skills 的資源
- **AND** 其他來源的資源被隱藏

#### Scenario: 顯示所有來源
- **WHEN** 使用者從 Source 下拉選單選擇「All」
- **THEN** 顯示所有來源的資源

### Requirement: 來源篩選與其他篩選器協同運作
Source 篩選器須與 Target 和 Type 篩選器組合使用。

#### Scenario: 組合篩選
- **WHEN** 使用者設定 Target 為「claude」、Type 為「skills」、Source 為「uds」
- **THEN** 僅顯示來自 UDS 來源的 Claude Code skills

#### Scenario: 篩選結果為空
- **WHEN** 使用者選擇的篩選條件組合沒有符合的資源
- **THEN** 顯示空清單
- **AND** 不顯示錯誤訊息

### Requirement: 來源篩選狀態在工作階段內保持
切換 Target 或 Type 時，Source 篩選的選擇須保持不變。

#### Scenario: 切換類型時保持來源篩選
- **WHEN** 使用者選擇 Source 為「custom-skills」
- **AND** 使用者將 Type 從「skills」切換為「agents」
- **THEN** Source 篩選維持「custom-skills」
- **AND** 資源清單更新為顯示 custom-skills 的 agents

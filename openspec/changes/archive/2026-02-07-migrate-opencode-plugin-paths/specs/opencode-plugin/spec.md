## MODIFIED Requirements

### Requirement: Plugin 可被分發

`ai-dev clone` SHALL 將 OpenCode plugin 分發到 `~/.config/opencode/plugins/`。

#### Scenario: clone 分發 plugin
- **WHEN** 執行 `ai-dev clone`
- **THEN** `plugins/ecc-hooks-opencode/` 的內容 SHALL 被複製到 `~/.config/opencode/plugins/`
- **THEN** 分發結果 SHALL 包含 OpenCode 可直接載入的第一層 entry 檔（`*.ts` 或 `*.js`）

## ADDED Requirements

### Requirement: OpenCode plugin 掃描相容性

OpenCode plugin 分發策略 MUST 同時考量官方 `plugins` 主路徑與 legacy `plugin` 相容情境。

#### Scenario: 以 `plugins` 作為主要分發目標
- **WHEN** 系統執行新的 OpenCode plugin 分發
- **THEN** SHALL 以 `~/.config/opencode/plugins/` 作為主要目標路徑
- **THEN** SHALL 不再以 `~/.config/opencode/plugin/ecc-hooks/` 作為預設主路徑

#### Scenario: 舊路徑存在時維持可用
- **WHEN** 使用者環境中存在 legacy `~/.config/opencode/plugin/...`
- **THEN** 系統 SHALL 提供可追蹤的相容處理（搬遷或 fallback）
- **THEN** 系統 SHALL 避免因路徑遷移導致 plugin 無法載入

### Requirement: OpenCode plugin 第一層載入契約

分發後的 OpenCode plugin MUST 符合第一層 entry-file 載入契約，以對齊 OpenCode loader 掃描模式。

#### Scenario: 第一層 entry-file 契約成立
- **WHEN** OpenCode 啟動並掃描 plugin 目錄
- **THEN** `~/.config/opencode/plugins/` 第一層 SHALL 存在可被掃描的 `*.ts` 或 `*.js` 檔案
- **THEN** 系統 SHALL 可從該 entry 檔載入對應 plugin 功能

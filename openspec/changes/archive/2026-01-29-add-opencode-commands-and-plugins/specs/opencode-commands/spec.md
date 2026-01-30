## ADDED Requirements

### Requirement: OpenCode commands 目錄存在
系統 SHALL 在 `commands/opencode/` 目錄下提供與 `commands/claude/` 對等的 command 檔案。

#### Scenario: 目錄結構完整
- **WHEN** 檢查 `commands/opencode/` 目錄
- **THEN** 該目錄 SHALL 包含與 `commands/claude/` 相同數量的 `.md` 檔案（排除 README.md）

#### Scenario: 檔案名稱一致
- **WHEN** 列出 `commands/opencode/` 和 `commands/claude/` 的檔案
- **THEN** 兩個目錄的 `.md` 檔案名稱 SHALL 完全一致（排除 README.md）

### Requirement: OpenCode command frontmatter 格式正確
每個 command 檔案 SHALL 使用 OpenCode 相容的 YAML frontmatter，不包含 Claude Code 特有欄位。

#### Scenario: 移除 Claude 特有欄位
- **WHEN** 解析 `commands/opencode/` 中任一 `.md` 檔案的 frontmatter
- **THEN** frontmatter SHALL 包含 `description` 欄位
- **THEN** frontmatter SHALL NOT 包含 `allowed-tools` 欄位
- **THEN** frontmatter SHALL NOT 包含 `argument-hint` 欄位

#### Scenario: 內容本體保留
- **WHEN** 比較 `commands/opencode/<name>.md` 和 `commands/claude/<name>.md` 的 markdown 本體（frontmatter 以外）
- **THEN** 內容 SHALL 完全一致

### Requirement: OpenCode commands 可被分發
`ai-dev clone` SHALL 將 `commands/opencode/` 分發到 `~/.config/opencode/commands/`。

#### Scenario: clone 分發 commands
- **WHEN** 執行 `ai-dev clone`
- **THEN** `commands/opencode/` 中的所有 `.md` 檔案 SHALL 被複製到 `~/.config/opencode/commands/`

## MODIFIED Requirements

### Requirement: clone 分發目標包含 OpenCode plugin
`ai-dev clone` 的分發邏輯 SHALL 支援將 OpenCode plugin 複製到目標目錄。

#### Scenario: COPY_TARGETS 包含 opencode plugins
- **WHEN** 檢查 `shared.py` 中的 `COPY_TARGETS["opencode"]`
- **THEN** SHALL 包含 `"plugins"` 項目，目標為 `get_opencode_config_dir() / "plugin" / "ecc-hooks"`

#### Scenario: 分發邏輯處理 plugins
- **WHEN** `copy_custom_skills_to_targets()` 執行 opencode 平台分發
- **THEN** SHALL 將 `plugins/ecc-hooks-opencode/` 的內容複製到 OpenCode plugin 目標目錄
- **THEN** 複製 SHALL 包含 `plugin.ts`、`package.json` 和 `scripts/` 子目錄

#### Scenario: paths.py 提供 plugin 路徑
- **WHEN** 呼叫 `get_opencode_plugin_dir()`
- **THEN** SHALL 回傳 `~/.config/opencode/plugin`

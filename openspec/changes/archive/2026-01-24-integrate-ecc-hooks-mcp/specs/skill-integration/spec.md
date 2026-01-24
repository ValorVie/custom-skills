## ADDED Requirements

### Requirement: ECC Hooks 標準 Plugin 結構

系統 SHALL 將 ECC Hooks 重構為符合 Claude Code 官方規範的 plugin 結構。

#### Scenario: Plugin 目錄結構

- **GIVEN** `sources/ecc/hooks/` 目錄
- **WHEN** 重構為標準 plugin 結構
- **THEN** 包含 `.claude-plugin/plugin.json` (Plugin manifest)
- **AND** 包含 `hooks/hooks.json` (Hook 配置)
- **AND** 包含 `scripts/` 目錄存放所有 Python 腳本
- **AND** `scripts/` 下保持 `memory-persistence/` 和 `strategic-compact/` 子目錄結構

#### Scenario: plugin.json 內容

- **GIVEN** 建立 `.claude-plugin/plugin.json`
- **THEN** 包含 `name` 欄位（"ecc-hooks"）
- **AND** 包含 `version` 欄位（語意化版本）
- **AND** 包含 `description` 欄位
- **AND** 包含 `hooks` 欄位指向 `./hooks/hooks.json`

#### Scenario: hooks.json 路徑格式

- **GIVEN** `hooks/hooks.json` 中的命令路徑
- **WHEN** 參照腳本位置
- **THEN** 使用 `${CLAUDE_PLUGIN_ROOT}/scripts/...` 格式
- **AND** 不包含 `sources/ecc/hooks/` 前綴

## ADDED Requirements

### Requirement: ECC Hooks CLI 管理指令

系統 SHALL 提供獨立的 CLI 指令管理 ECC Hooks Plugin。

#### Scenario: ai-dev hooks install

- **WHEN** 執行 `ai-dev hooks install`
- **THEN** 複製 `sources/ecc/hooks/` 到 `~/.claude/plugins/ecc-hooks/`
- **AND** 檢查 Claude Code 是否已安裝
- **AND** 輸出 plugin 安裝成功訊息

#### Scenario: ai-dev hooks uninstall

- **GIVEN** ECC Hooks Plugin 已安裝
- **WHEN** 執行 `ai-dev hooks uninstall`
- **THEN** 刪除 `~/.claude/plugins/ecc-hooks/` 目錄
- **AND** 輸出移除成功訊息

#### Scenario: ai-dev hooks status

- **WHEN** 執行 `ai-dev hooks status`
- **THEN** 顯示 ECC Hooks Plugin 安裝狀態（已安裝/未安裝）
- **AND** 若已安裝，顯示安裝位置
- **AND** 若已安裝，顯示 plugin 版本（從 plugin.json 讀取）

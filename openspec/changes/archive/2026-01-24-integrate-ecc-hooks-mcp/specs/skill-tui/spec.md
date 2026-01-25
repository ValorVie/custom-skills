## ADDED Requirements

### Requirement: TUI ECC Hooks Plugin 區塊

TUI MUST 在主畫面顯示 ECC Hooks Plugin 管理區塊。

#### Scenario: 顯示 plugin 安裝狀態

- **GIVEN** 開啟 TUI 且選擇 Claude Code 作為 Target
- **WHEN** 渲染主畫面
- **THEN** 在 Resources 區塊下方顯示 "ECC Hooks Plugin" 區塊
- **AND** 顯示安裝狀態（Installed / Not Installed）
- **AND** 若已安裝，顯示版本號（從 plugin.json 讀取）
- **AND** 若已安裝，顯示安裝路徑

#### Scenario: plugin 快捷鍵操作

- **GIVEN** TUI 顯示 ECC Hooks Plugin 區塊
- **WHEN** 按下 'I' 鍵
- **THEN** 執行 plugin install 操作
- **AND** 更新狀態顯示

- **WHEN** 按下 'U' 鍵
- **THEN** 執行 plugin uninstall 操作（需確認）
- **AND** 更新狀態顯示

- **WHEN** 按下 'V' 鍵
- **THEN** 在編輯器中開啟 `~/.claude/plugins/ecc-hooks/hooks/hooks.json`

#### Scenario: 非 Claude Code Target 隱藏 plugin 區塊

- **GIVEN** 選擇非 Claude Code 的 Target（如 Antigravity, OpenCode）
- **WHEN** 渲染主畫面
- **THEN** 不顯示 ECC Hooks Plugin 區塊（因 plugin 僅適用於 Claude Code）

### Requirement: MCP 範本路徑顯示

TUI MUST 在 MCP Config 區塊顯示範本來源路徑。

#### Scenario: 顯示 MCP 範本資訊

- **GIVEN** 開啟 TUI 且選擇 Claude Code 作為 Target
- **WHEN** 渲染 MCP Config 區塊
- **THEN** 顯示使用者的 MCP 配置路徑（`~/.claude.json`）
- **AND** 顯示範本來源路徑（`~/.config/custom-skills/sources/ecc/mcp-configs/`）

#### Scenario: MCP 範本快捷鍵

- **GIVEN** TUI 顯示 MCP Config 區塊
- **WHEN** 按下 'T' 鍵
- **THEN** 在編輯器中開啟 `sources/ecc/mcp-configs/mcp-servers.json`

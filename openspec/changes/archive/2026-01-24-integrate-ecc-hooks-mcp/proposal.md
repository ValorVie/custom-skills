# Change: 整合 ECC Hooks 與 MCP 配置到 ai-dev 流程

## Why

目前 `sources/ecc/hooks` 和 `sources/ecc/mcp-configs` 已作為資源存在於專案中，但尚未整合到 ai-dev 的分發流程。使用者需要手動複製這些配置到各自的工具目錄，缺乏自動化且容易出錯。此外，現有結構不符合 Claude Code 官方 plugin 規範。

## What Changes

### 1. 重構為標準 Claude Code Plugin 結構

將 `sources/ecc/hooks/` 重構並分發為符合官方規範的 plugin：

```
~/.claude/plugins/ecc-hooks/
├── .claude-plugin/
│   └── plugin.json              # 新增：Plugin manifest
├── hooks/
│   └── hooks.json               # 移動：Hook 配置
├── scripts/                     # 重構：腳本目錄
│   ├── utils.py
│   ├── memory-persistence/
│   │   ├── session-start.py
│   │   ├── session-end.py
│   │   ├── pre-compact.py
│   │   └── evaluate-session.py
│   └── strategic-compact/
│       └── suggest-compact.py
└── README.md
```

### 2. 擴展 ai-dev install/update 分發目標

- **新增 Hooks 分發邏輯**：建構標準 plugin 結構並分發到 `~/.claude/plugins/ecc-hooks/`
- **新增 MCP 配置範本機制**：將 `sources/ecc/mcp-configs/` 作為範本提供，不自動覆蓋使用者現有配置

### 3. 新增 TUI 整合功能

- 在 TUI 中顯示 Hooks 安裝狀態
- 提供一鍵安裝/更新 Hooks 的功能
- 顯示 MCP 配置範本的複製指引

### 4. 設計原則

- **符合官方規範**：遵循 Claude Code plugin 標準結構
- **非破壞性**：不自動覆蓋使用者的 `~/.claude.json` 或現有 hooks 配置
- **選擇性啟用**：使用者透過 TUI 或 CLI 選擇是否安裝 hooks
- **範本導向**：MCP 配置以範本形式提供，使用者需手動合併

## Impact

- Affected specs: `setup-script`, `skill-tui`, `hook-system`, `skill-integration`
- Affected code:
  - `script/commands/ai_dev.py` (新增 hooks 分發邏輯，含結構轉換)
  - `script/tui/main.py` (新增 Hooks 狀態顯示與操作)
  - `sources/ecc/hooks/hooks.json` (調整路徑變數為 `scripts/` 相對路徑)
- New files:
  - `sources/ecc/hooks/.claude-plugin/plugin.json` (Plugin manifest)

## Design Decision Summary

| 決策點 | 選擇 | 理由 |
|--------|------|------|
| Plugin 結構 | 標準 Claude Code plugin 格式 | 符合官方規範，確保相容性 |
| Hooks 分發方式 | 建構 + 複製到 plugins 目錄 | 需轉換結構以符合規範 |
| MCP 分發方式 | 範本 + 手動合併 | MCP 配置高度個人化，含敏感 token |
| 整合位置 | Stage 3 分發流程 | 與現有架構一致 |
| TUI 整合 | 新增 Hooks 區塊 | 提供可視化管理介面 |

# Proposal: add-mcp-config-viewer

## Summary

在 TUI 介面中新增「MCP Config」區塊，讓使用者能快速檢視各 AI 工具的 MCP Server 設定檔路徑，並可直接在外部編輯器（VS Code 或其他）中開啟設定檔。

## Motivation

目前使用者管理 MCP Server 設定時需要：
1. 記住各工具設定檔的不同路徑
2. 手動在終端機或檔案管理器中導航到該路徑
3. 開啟編輯器進行修改

此功能提供一站式的設定檔存取入口，提升維護效率。

## Scope

### In Scope
- 顯示各 AI 工具的 MCP 設定檔路徑
- 提供「在編輯器中開啟」功能（使用 `code` 或使用者指定的編輯器）
- 整合到現有 TUI 介面

### Out of Scope
- 在 TUI 內直接編輯 MCP 設定檔內容
- 自動偵測或驗證 MCP Server 狀態
- MCP Server 的安裝或移除功能

## Design

### MCP 設定檔位置

| 工具 | 設定檔路徑 | 說明 |
|------|-----------|------|
| Claude Code | `~/.claude.json` (mcpServers 區塊) | 全域 MCP 設定 |
| Antigravity | `~/.gemini/antigravity/mcp_config.json` | MCP 設定檔 |
| OpenCode | `~/.config/opencode/opencode.json` (mcp 區塊) | 整合在主設定中 |

### TUI 介面變更

在 TUI 中新增「MCP Config」區塊，位於資源列表下方或作為獨立頁籤：

```
┌─────────────────────────────────────────────┐
│ [Install] [Maintain] [Status] [Add Skills]  │
├─────────────────────────────────────────────┤
│ Target: [Claude Code ▼]  Type: [Skills ▼]   │
├─────────────────────────────────────────────┤
│ ☑ skill-name-1  (uds)                       │
│ ☐ skill-name-2  (custom)                    │
│ ...                                         │
├─────────────────────────────────────────────┤
│ MCP Config                                  │
│ ┌─────────────────────────────────────────┐ │
│ │ Path: ~/.claude.json                    │ │
│ │ [Open in Editor]                        │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 開啟編輯器邏輯

1. 優先使用環境變數 `EDITOR`
2. 若未設定，嘗試使用 `code` (VS Code)
3. 若 VS Code 不存在，嘗試使用 `open` (macOS) 或 `xdg-open` (Linux)

## Related Specs

- `skill-tui`: 需要擴充 TUI 規格以支援新的 MCP Config 區塊

## Dependencies

- 現有 TUI 架構 (Textual 框架)
- 外部編輯器 (VS Code, Vim, 等)

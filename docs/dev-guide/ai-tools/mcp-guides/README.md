---
tags:
  - ai
  - mcp
  - dev-tools
  - index
date created: 2026-03-02T15:00:00+08:00
date modified: 2026-03-10T23:45:00+08:00
description: MCP Server 個別使用指南索引與工具端設定補充，各服務的深入安裝說明與使用範例
---

# MCP Server 使用指南

本目錄收錄各 MCP Server 的**深入使用指南**，以及像 Codex 這種工具端的 MCP 設定補充。快速安裝設定請參閱上層的 [MCP-SERVER-GUIDE.md](../MCP-SERVER-GUIDE.md)。

---

## 指南清單

| 主題 | 用途 | Stars | 授權 | 指南 |
|------|------|-------|------|------|
| **Codex CLI** | Codex 的 MCP 設定位置、TOML 格式與 CLI 指令 | — | Apache-2.0 | [Codex MCP 指南](CodexCLI-MCP設定指南.md) |
| **Context7** | 即時技術文件查詢 | 47.3k | MIT | [Context7 指南](Context7即時文件查詢.md) |
| **n8n-MCP** | n8n 工作流自動化知識庫 | 14.2k | MIT | [n8n-MCP 指南](n8n-MCP工作流自動化.md) |
| **GitNexus** | 程式碼知識圖譜 | 7.7k | PolyForm NC | [GitNexus 指南](GitNexus程式碼知識圖譜.md) |
| **Postgres MCP Pro** | PostgreSQL 資料庫管理與優化 | 2.2k | MIT | [Postgres MCP 指南](PostgresMCP資料庫管理.md) |
| **idea-reality-mcp** | 產品點子競爭驗證 | 230 | MIT | [idea-reality 指南](idea-reality產品驗證.md) |
| **Context Mode** | MCP 工具輸出壓縮，延長 context window | 1.6k | MIT | [Context Mode 指南](ContextMode上下文壓縮.md) |
| **Playwright MCP** | 瀏覽器自動化，處理 JS 渲染頁面 | — | Apache-2.0 | [Playwright MCP 指南](PlaywrightMCP瀏覽器自動化.md) |
| **AI Browser 工具比較** | 三大 AI 瀏覽器工具比較與選擇指南 | — | — | [AI Browser 指南](AI-Browser瀏覽器工具指南.md) |

## 選擇指南

```
你需要什麼？
    │
    ├─ 想在 Codex 裡正確掛載 MCP → Codex CLI MCP 設定指南
    ├─ 查詢某個套件/框架的最新文件 → Context7
    ├─ 理解程式碼庫的架構和相依性 → GitNexus
    ├─ 管理和優化 PostgreSQL 資料庫 → Postgres MCP Pro
    ├─ 建構 n8n 自動化工作流 → n8n-MCP
    ├─ 驗證產品點子是否已有人做過 → idea-reality-mcp
    ├─ 壓縮 MCP 輸出、延長 context → Context Mode
    ├─ 操作需要 JS 渲染的網頁 → Playwright MCP
    └─ 比較三大 AI 瀏覽器工具 → AI Browser 指南
```

## 相關文件

- [MCP-SERVER-GUIDE.md](../MCP-SERVER-GUIDE.md) — 快速安裝設定與格式對照
- [mcp-configs/](../mcp-configs/) — Claude Code / Codex / OpenCode 設定範本
- [Codex CLI MCP 設定指南](CodexCLI-MCP設定指南.md) — Codex 的設定位置、TOML 格式與 CLI 操作
- [AI 開發環境設定指南](../../AI開發環境設定指南.md) — 完整環境安裝流程

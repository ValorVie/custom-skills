---
tags:
  - ai
  - mcp
  - codex
  - config
  - cli
date created: 2026-03-10T23:45:00+08:00
date modified: 2026-03-10T23:45:00+08:00
description: Codex CLI MCP 設定指南 — 說明全域與專案設定位置、CLI 指令，以及 Codex 專用的 TOML 格式
---

# Codex CLI MCP 設定指南

| 項目 | 內容 |
|------|------|
| **工具** | Codex CLI / Codex App 共用設定 |
| **官方文件** | https://developers.openai.com/codex/mcp/ |
| **設定格式** | TOML |
| **全域設定檔** | `~/.codex/config.toml` |
| **專案設定檔** | `./.codex/config.toml`（僅 trusted project 載入） |

---

## 這份指南解決什麼問題

許多 MCP 教學都以 Claude Code 或 Cursor 為主，範例通常是 JSON 的 `mcpServers`。Codex 不一樣：

- Codex 的 MCP 設定寫在 `config.toml`
- 欄位名稱是 `mcp_servers`
- 本機 stdio MCP 不需要額外宣告 `type = "stdio"`
- 遠端 MCP 不是 `headers` JSON，而是 `url` 搭配 `bearer_token_env_var`

如果直接把 Claude Code 的 JSON 範例貼進 Codex，Codex 不會載入。

---

## 設定檔位置

### 1. 全域設定（最常用）

```text
~/.codex/config.toml
```

適合放你所有專案都會共用的 MCP Server，例如 Context7、Playwright。

### 2. 專案設定（只套用在某個 repo）

```text
./.codex/config.toml
```

適合放只屬於特定專案的 MCP，例如專案專用資料庫、內網服務、測試環境。

> Codex 只會在 trusted project 中讀取專案層級 `.codex/config.toml`。

---

## CLI 管理方式

### 新增本機 stdio MCP

```bash
codex mcp add context7 -- npx -y @upstash/context7-mcp
```

### 新增遠端 HTTP MCP

```bash
codex mcp add context7-remote --url https://mcp.context7.com/mcp --bearer-token-env-var CONTEXT7_API_KEY
```

### 查看與移除

```bash
codex mcp list
codex mcp get context7 --json
codex mcp remove context7
```

---

## 手動設定格式

### 1. 最小可用的本機 stdio MCP

```toml
[mcp_servers.context7]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]
```

### 2. 帶環境變數的本機 MCP

```toml
[mcp_servers.n8n-mcp]
command = "npx"
args = ["-y", "n8n-mcp"]

[mcp_servers.n8n-mcp.env]
MCP_MODE = "stdio"
LOG_LEVEL = "error"
DISABLE_CONSOLE_OUTPUT = "true"
N8N_API_URL = "https://${DOMAIN}"
N8N_API_KEY = "${API_KEY}"
```

### 3. 遠端 HTTP MCP

```toml
[mcp_servers.context7-remote]
url = "https://mcp.context7.com/mcp"
bearer_token_env_var = "CONTEXT7_API_KEY"
```

---

## 和 Claude Code / OpenCode 的差異

| 工具 | 設定檔 | 根欄位 / 根 table | 本機指令格式 |
|------|--------|--------------------|--------------|
| Claude Code | `~/.claude.json` | `mcpServers` | `command` + `args` |
| Codex | `~/.codex/config.toml` | `mcp_servers` | `command` + `args` |
| OpenCode | `~/.config/opencode/opencode.json` | `mcp` | `command` 陣列 |

Codex 和 Claude Code 看起來最像，但仍有三個實際差異：

1. Codex 用 TOML，不是 JSON。
2. Codex 本機 MCP 不需要額外寫 `type = "stdio"`。
3. Codex 遠端 HTTP MCP 優先使用 `bearer_token_env_var`，不是 `headers` 物件。

---

## 推薦做法

1. **優先用 `codex mcp add`**：可避免 TOML 手寫格式錯誤。
2. **共用工具放全域**：例如 Context7、Playwright。
3. **專案私有連線放專案層級**：例如 staging DB、內網 API。
4. **先用 `codex mcp list` 驗證**：確認 Codex 已實際載入，再開始用。

**Recommended**：把常用通用 MCP 寫在 `~/.codex/config.toml`，專案私有設定寫在 `./.codex/config.toml`。這樣既能共用，又不會把敏感設定外溢到所有專案。

---

## 範本檔

完整範例請參閱：

- [codex.toml](../mcp-configs/codex.toml) — 對應本目錄既有 `claude-code.json` 的 Codex 版本
- [MCP-SERVER-GUIDE.md](../MCP-SERVER-GUIDE.md) — 三種工具的快速格式對照

---

## 故障排除

### Q: 我把 `claude-code.json` 直接改副檔名成 `.toml`，為什麼沒用？

**A:** Codex 不是只改副檔名而已。它要的是 TOML table，例如 `[mcp_servers.context7]`，不是 JSON 物件。

### Q: `codex mcp list` 看得到，但工具還是沒有出現？

**A:** 先確認目前是在載入同一份設定檔。若你改的是 `./.codex/config.toml`，專案必須是 trusted project。

### Q: 遠端 MCP 需要 API Token，該寫哪裡？

**A:** 在環境變數放 Token，設定檔只寫變數名稱：

```toml
[mcp_servers.remote-example]
url = "https://mcp.example.com"
bearer_token_env_var = "MCP_API_TOKEN"
```

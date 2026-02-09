# MCP Server 設定指南

MCP (Model Context Protocol) Server 可擴充 AI 開發工具的能力，例如查詢最新文件、安全掃描、資料庫操作等。

本指南涵蓋 **Claude Code** 與 **OpenCode** 兩種工具的 MCP 設定方式。

---

## 目錄

1. [設定檔位置](#設定檔位置)
2. [Claude Code 設定](#claude-code-設定)
3. [OpenCode 設定](#opencode-設定)
4. [可用 MCP Server 清單](#可用-mcp-server-清單)
5. [設定範本](#設定範本)
6. [故障排除](#故障排除)

---

## 設定檔位置

| 工具 | 設定檔路徑 | 格式 |
|------|-----------|------|
| Claude Code | `~/.claude.json` | JSON（`mcpServers` 欄位） |
| OpenCode | `~/.config/opencode/opencode.json` | JSON（`mcp` 欄位） |
| Antigravity | `~/.gemini/antigravity/mcp_config.json` | JSON |
| Gemini CLI | `~/.gemini/settings.json` | JSON |
| Codex | `~/.codex/config.json` | JSON |

---

## Claude Code 設定

### 使用 CLI 新增（推薦）

```bash
# 新增 MCP Server
claude mcp add <name> --scope user -- <command> [args...]

# 範例：新增 Context7
claude mcp add context7 --scope user -- npx @upstash/context7-mcp

# 查看已安裝的 MCP Server
claude mcp list

# 移除 MCP Server
claude mcp remove <name>
```

### 手動編輯設定檔

編輯 `~/.claude.json`，在 `mcpServers` 欄位下新增：

```json
{
  "mcpServers": {
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["@upstash/context7-mcp"],
      "env": {}
    }
  }
}
```

> 完整設定範本請參閱 [mcp-configs/](mcp-configs/) 目錄。

---

## OpenCode 設定

編輯 `~/.config/opencode/opencode.json`，在 `mcp` 欄位下新增。

> OpenCode 的 MCP 格式與 Claude Code **不同**，請注意以下差異。

### 格式差異對照

| 項目 | Claude Code | OpenCode |
|------|------------|----------|
| 設定欄位名 | `mcpServers` | `mcp` |
| 類型值 | `"stdio"` | `"local"` |
| 指令格式 | `command` (string) + `args` (array) | `command` (string array，合併指令與參數) |
| 環境變數 | `env` | `environment` |
| 額外欄位 | — | `enabled`、`timeout`（選填） |

### 範例

```json
{
  "mcp": {
    "context7": {
      "type": "local",
      "command": ["npx", "@upstash/context7-mcp"],
      "environment": {}
    }
  }
}
```

OpenCode 也支援 `remote` 類型（透過 URL 連線遠端 MCP Server）：

```json
{
  "mcp": {
    "remote-server": {
      "type": "remote",
      "url": "https://mcp.example.com/sse",
      "headers": {
        "Authorization": "Bearer ${TOKEN}"
      }
    }
  }
}
```

---

## 可用 MCP Server 清單

> 以下每個 Server 均提供 Claude Code 與 OpenCode 兩種格式的設定。

### Context7 — 技術文件查詢

即時查詢各程式語言與框架的最新官方文件。

**Claude Code：**
```json
"context7": {
  "type": "stdio",
  "command": "npx",
  "args": ["@upstash/context7-mcp"],
  "env": {}
}
```

**OpenCode：**
```json
"context7": {
  "type": "local",
  "command": ["npx", "@upstash/context7-mcp"],
  "environment": {}
}
```

**安裝前置**：Node.js >= 20

### Snyk — 安全漏洞掃描

掃描專案的開源套件漏洞、程式碼安全問題與 IaC 配置。

**Claude Code：**
```json
"snyk": {
  "type": "stdio",
  "command": "/opt/homebrew/bin/snyk",
  "args": ["mcp", "-t", "stdio"],
  "env": {}
}
```

**OpenCode：**
```json
"snyk": {
  "type": "local",
  "command": ["/opt/homebrew/bin/snyk", "mcp", "-t", "stdio"],
  "environment": {}
}
```

**安裝前置**：
```bash
# macOS
brew install snyk-cli

# 或使用 npm
npm install -g snyk

# 認證
snyk auth
```

> `command` 路徑需依實際安裝位置調整，可用 `which snyk` 查詢。

### Playwright — 瀏覽器自動化

讓 AI 透過 Playwright 操作瀏覽器，支援網頁導覽、表單填寫、資料擷取與自動化測試。使用 Accessibility Tree 結構化資料，無需截圖。

**Claude Code：**
```json
"playwright": {
  "type": "stdio",
  "command": "npx",
  "args": ["@playwright/mcp@latest"],
  "env": {}
}
```

**OpenCode：**
```json
"playwright": {
  "type": "local",
  "command": ["npx", "@playwright/mcp@latest"],
  "environment": {}
}
```

**安裝前置**：Node.js >= 18

**Claude Code 快速安裝**：
```bash
claude mcp add playwright npx @playwright/mcp@latest
```

> 更多設定選項（如 headless 模式、自訂 browser profile）請參閱 [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp)。

### n8n MCP — 工作流程自動化

連接 n8n 實例，管理與觸發自動化工作流程。

**Claude Code：**
```json
"n8n-mcp": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "n8n-mcp"],
  "env": {
    "MCP_MODE": "stdio",
    "LOG_LEVEL": "error",
    "DISABLE_CONSOLE_OUTPUT": "true",
    "N8N_API_URL": "https://${DOMAIN}",
    "N8N_API_KEY": "${API_KEY}"
  }
}
```

**OpenCode：**
```json
"n8n-mcp": {
  "type": "local",
  "command": ["npx", "-y", "n8n-mcp"],
  "environment": {
    "MCP_MODE": "stdio",
    "LOG_LEVEL": "error",
    "DISABLE_CONSOLE_OUTPUT": "true",
    "N8N_API_URL": "https://${DOMAIN}",
    "N8N_API_KEY": "${API_KEY}"
  }
}
```

**必要環境變數**：
| 變數 | 說明 |
|------|------|
| `N8N_API_URL` | n8n 實例 URL |
| `N8N_API_KEY` | n8n API 金鑰 |

### PostgreSQL MCP — 資料庫操作

直接在 AI 工具中查詢與管理 PostgreSQL 資料庫。

**Claude Code：**
```json
"postgres-mcp": {
  "type": "stdio",
  "command": "uv",
  "args": ["run", "postgres-mcp", "--access-mode=unrestricted"],
  "env": {
    "DATABASE_URI": "postgresql://${USER}:${PASSWORD}@${IP}:${PORT}/${DB}"
  }
}
```

**OpenCode：**
```json
"postgres-mcp": {
  "type": "local",
  "command": ["uv", "run", "postgres-mcp", "--access-mode=unrestricted"],
  "environment": {
    "DATABASE_URI": "postgresql://${USER}:${PASSWORD}@${IP}:${PORT}/${DB}"
  }
}
```

**必要環境變數**：
| 變數 | 說明 |
|------|------|
| `DATABASE_URI` | PostgreSQL 連線字串 |

**安裝前置**：需要 `uv`

> `--access-mode=unrestricted` 允許完整讀寫。如需限制為唯讀，可改用 `--access-mode=read-only`。

---

## 設定範本

完整的設定檔範本放置於 [mcp-configs/](mcp-configs/) 目錄：

| 檔案 | 說明 |
|------|------|
| [claude-code.json](mcp-configs/claude-code.json) | Claude Code 的 `~/.claude.json` MCP 設定範本 |
| [opencode.json](mcp-configs/opencode.json) | OpenCode 的 MCP 設定範本 |

### 使用方式

1. 複製對應的範本檔案
2. 將 `${...}` 佔位符替換為實際值
3. 合併到你的設定檔中

```bash
# 查看範本
cat docs/dev-guide/ai-tools/mcp-configs/claude-code.json

# 編輯你的 Claude Code 設定
code ~/.claude.json

# 編輯你的 OpenCode 設定
code ~/.config/opencode/opencode.json
```

---

## 故障排除

### MCP Server 連線失敗

```bash
# 確認 MCP Server 指令可正常執行
npx @upstash/context7-mcp --help

# 檢查 Claude Code 已載入的 MCP
claude mcp list

# 移除後重新新增
claude mcp remove context7
claude mcp add context7 --scope user -- npx @upstash/context7-mcp
```

### 環境變數未生效

Claude Code 的 `env` 和 OpenCode 的 `environment` 欄位**不支援** shell 變數展開（如 `$HOME`）。請使用完整的實際值：

```json
// 錯誤
"DATABASE_URI": "postgresql://$DB_USER:$DB_PASS@localhost:5432/mydb"

// 正確
"DATABASE_URI": "postgresql://admin:secret@localhost:5432/mydb"
```

> OpenCode 支援 `{env:VAR_NAME}` 語法在設定檔中引用環境變數，例如 `"N8N_API_KEY": "{env:N8N_API_KEY}"`。

### Snyk 路徑問題

不同安裝方式的 `snyk` 路徑不同：

```bash
# 查詢實際路徑
which snyk

# macOS Homebrew
/opt/homebrew/bin/snyk

# npm 全域安裝
# macOS/Linux
~/.npm-global/bin/snyk
# 或
/usr/local/bin/snyk
```

### OpenCode MCP 不生效

確認設定使用 OpenCode 專用格式，寫在 `opencode.json` 的 `mcp` 欄位（不是 `mcpServers`）：

```json
{
  "mcp": {
    "context7": {
      "type": "local",
      "command": ["npx", "@upstash/context7-mcp"]
    }
  }
}
```

常見錯誤：
- 使用了 `mcpServers`（Claude Code 格式）而非 `mcp`
- 使用了 `"type": "stdio"` 而非 `"type": "local"`
- 使用了 `command` (string) + `args` (array) 而非 `command` (string array)
- 使用了 `env` 而非 `environment`

修改後需重啟 OpenCode。

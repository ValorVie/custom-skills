---
tags:
  - ai
  - mcp
  - documentation
  - context7
date created: 2026-03-02T15:00:00+08:00
date modified: 2026-03-02T15:00:00+08:00
description: Context7 MCP Server 使用指南 — 在 AI 助手中即時查詢任何程式庫的最新文件與程式碼範例
---

# Context7 — 即時技術文件查詢

| 項目 | 內容 |
|------|------|
| **GitHub** | https://github.com/upstash/context7 |
| **Stars** | 47,367 |
| **語言** | TypeScript |
| **授權** | MIT |
| **NPM 套件** | `@upstash/context7-mcp` |

---

## 解決什麼問題

AI 助手的訓練資料有截止日期，查詢到的 API 可能已過時或不存在。Context7 讓 AI 在回答時即時拉取**最新版本的官方文件與程式碼範例**，避免幻覺。

| 沒有 Context7 | 有 Context7 |
|---------------|-------------|
| AI 用訓練資料中的舊 API 回答 | AI 即時查詢最新文件 |
| 版本不匹配，程式碼無法編譯 | 自動對應指定版本 |
| 需要自己去官網查文件再貼回來 | AI 自動拉取並引用 |

---

## 安裝

### 方式一：快速設定（推薦）

```bash
npx ctx7 setup
```

自動完成 OAuth 認證並設定到你選擇的 AI 工具。

### 方式二：Claude Code CLI

```bash
claude mcp add context7 --scope user -- npx -y @upstash/context7-mcp
```

### API Key（選用但推薦）

免費 API Key 可提升速率限制，取得方式：https://context7.com/dashboard

---

## 設定

### Claude Code

```bash
# 本地模式
claude mcp add context7 --scope user -- npx -y @upstash/context7-mcp

# 遠端模式（需 API Key）
claude mcp add --scope user --header "CONTEXT7_API_KEY: YOUR_KEY" --transport http context7 https://mcp.context7.com/mcp
```

手動設定 (`~/.claude.json`)：
```json
{
  "mcpServers": {
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "env": {}
    }
  }
}
```

### Cursor

編輯 `~/.cursor/mcp.json`：
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

遠端模式：
```json
{
  "mcpServers": {
    "context7": {
      "url": "https://mcp.context7.com/mcp",
      "headers": {
        "CONTEXT7_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```

### OpenCode

```json
{
  "mcp": {
    "context7": {
      "type": "remote",
      "url": "https://mcp.context7.com/mcp",
      "headers": {
        "CONTEXT7_API_KEY": "YOUR_API_KEY"
      },
      "enabled": true
    }
  }
}
```

---

## MCP 工具

Context7 提供 2 個 MCP 工具：

### 1. `resolve-library-id` — 解析程式庫 ID

將一般名稱轉換為 Context7 格式的程式庫 ID。

| 參數 | 必填 | 說明 |
|------|------|------|
| `query` | 是 | 你要解決的問題描述 |
| `libraryName` | 是 | 程式庫名稱 |

**回傳結果包含**：
- Library ID（如 `/mongodb/docs`）
- 名稱與簡短描述
- 可用的程式碼片段數量
- 來源信譽度（High/Medium/Low）
- 基準分數（0-100）
- 可用版本列表

### 2. `query-docs` — 查詢文件

用 Library ID 查詢特定文件內容。

| 參數 | 必填 | 說明 |
|------|------|------|
| `libraryId` | 是 | Context7 格式的 ID（如 `/vercel/next.js`） |
| `query` | 是 | 要查詢的具體問題 |

---

## 使用範例

### 自動觸發

在提示詞結尾加上 `use context7`，AI 會自動呼叫 Context7 查詢相關文件：

```
建立一個 Next.js middleware 檢查 JWT cookie，未登入時導向 /login。use context7
```

### 指定程式庫版本

```
如何設定 Next.js 14 的 middleware？use context7
```

### 指定 Library ID

```
用 /supabase/supabase 的文件，實作 Supabase 基本認證
```

### 建議的 IDE 規則

在 `CLAUDE.md` 或 `.cursorrules` 中加入以下規則，讓 AI 自動使用 Context7：

```
當回答程式碼相關問題時，優先使用 Context7 MCP 查詢最新文件，避免使用過時的 API。
```

---

## 最佳實踐

1. **具體描述問題**：「如何用 Express.js 設定 JWT 認證」比「auth」效果好得多
2. **指定版本**：提及版本號可取得更精確的文件
3. **善用 Library ID**：已知套件時直接用 `/org/project` 格式更準確
4. **每個問題最多呼叫 3 次**：API 有呼叫次數建議限制，3 次內找不到就用已有結果

---

## 故障排除

### Q: 查詢不到某個程式庫

**A:** 並非所有程式庫都被索引。嘗試用不同名稱搜尋，或直接到 https://context7.com 檢查是否支援。

### Q: 回傳的文件是舊版本

**A:** 在查詢時明確指定版本號，如 `/vercel/next.js/v14.3.0`。

### Q: 速率限制

**A:** 申請免費 API Key：https://context7.com/dashboard，可顯著提升限制。

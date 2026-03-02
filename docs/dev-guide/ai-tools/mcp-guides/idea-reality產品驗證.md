---
tags:
  - ai
  - mcp
  - validation
  - idea-check
date created: 2026-03-02T15:00:00+08:00
date modified: 2026-03-02T15:00:00+08:00
description: idea-reality-mcp 使用指南 — 在開發前自動驗證產品點子的市場競爭狀態
---

# idea-reality-mcp — 產品點子競爭驗證

| 項目 | 內容 |
|------|------|
| **GitHub** | https://github.com/mnemox-ai/idea-reality-mcp |
| **Stars** | 230 |
| **語言** | Python |
| **授權** | MIT |
| **套件** | `idea-reality-mcp`（uvx / pip） |

---

## 解決什麼問題

開發前最常見的浪費：**花了大量時間做出來，才發現早已有成熟的開源方案或商業產品**。

idea-reality-mcp 讓 AI 助手在你開始寫程式之前，自動掃描 GitHub、Hacker News、npm、PyPI、Product Hunt 五大來源，給出 0-100 的市場飽和度評分和競爭分析。

| 傳統做法 | 使用 idea-reality |
|----------|-------------------|
| 手動 Google 搜尋，容易遺漏 | 同時掃描 5 個結構化資料庫 |
| 主觀判斷「應該沒人做過」 | 0-100 量化分數 + 證據連結 |
| 搜完就忘，下次重來 | 自動整合到開發流程 |

---

## 安裝

### 前置需求

| 需求 | 說明 |
|------|------|
| Python + uv | 執行 MCP Server |
| `GITHUB_TOKEN`（選用） | 提升 GitHub API 速率限制 |
| `PRODUCTHUNT_TOKEN`（選用） | 啟用 Product Hunt 搜尋 |

### Claude Code（推薦）

```bash
claude mcp add idea-reality --scope user -- uvx idea-reality-mcp
```

### 帶環境變數安裝

```bash
claude mcp add idea-reality --scope user -e GITHUB_TOKEN=ghp_xxx -- uvx idea-reality-mcp
```

---

## 設定

### Claude Code

手動設定 (`~/.claude.json`)：
```json
{
  "mcpServers": {
    "idea-reality": {
      "command": "uvx",
      "args": ["idea-reality-mcp"],
      "env": {
        "GITHUB_TOKEN": "ghp_xxx",
        "PRODUCTHUNT_TOKEN": "xxx"
      }
    }
  }
}
```

### Claude Desktop

編輯 `claude_desktop_config.json`：
```json
{
  "mcpServers": {
    "idea-reality": {
      "command": "uvx",
      "args": ["idea-reality-mcp"]
    }
  }
}
```

### Cursor

編輯 `~/.cursor/mcp.json`：
```json
{
  "mcpServers": {
    "idea-reality": {
      "command": "uvx",
      "args": ["idea-reality-mcp"]
    }
  }
}
```

---

## MCP 工具

idea-reality 提供 1 個 MCP 工具：

### `idea_check` — 點子驗證

| 參數 | 必填 | 說明 |
|------|------|------|
| `idea_text` | 是 | 自然語言描述你的產品點子 |
| `depth` | 否 | `"quick"`（GitHub + HN）或 `"deep"`（全部 5 個來源） |

### 回傳結果

| 欄位 | 說明 |
|------|------|
| `reality_signal` | 0-100 分數（越高表示競爭越激烈） |
| `evidence[]` | 有來源的證據清單 |
| `top_similars[]` | 最相似的競爭專案（含 star 數） |
| `pivot_hints[]` | 差異化建議（基於現有方案的缺口） |
| `meta{}` | 搜尋來源、關鍵詞提取方式、版本 |

### 評分機制

**Quick 模式權重**（速度快，適合初步篩選）：
| 來源 | 權重 |
|------|------|
| GitHub repos | 60% |
| GitHub stars | 20% |
| Hacker News | 20% |

**Deep 模式權重**（全面，適合正式決策）：
| 來源 | 權重 |
|------|------|
| GitHub repos | 25% |
| GitHub stars | 10% |
| Hacker News | 15% |
| npm | 20% |
| PyPI | 15% |
| Product Hunt | 15% |

---

## 使用範例

### 對話中直接使用

```
幫我檢查這個點子有沒有人做過：一個把 Figma 設計稿自動轉換成 React 元件的 CLI 工具
```

### 開發前驗證

```
我們準備做一個內部錯誤追蹤系統，先跑一下 reality check
```

### 深度分析

```
用 deep 模式分析：開源的 feature flag 服務
```

### 中文支援

支援中文輸入，內建 150+ 中英術語對照：

```
檢查這個點子：AI 驅動的程式碼審查工具，自動偵測安全漏洞
```

---

## 自動觸發設定

在 `CLAUDE.md` 或 `.cursorrules` 中加入：

```
當開始新專案或討論新功能時，自動使用 idea_check MCP 工具驗證市場競爭狀態。
```

---

## 解讀結果

| 分數範圍 | 意義 | 建議 |
|----------|------|------|
| 0-20 | 幾乎沒有競爭 | 可能是藍海，也可能需求不存在，需進一步驗證 |
| 21-40 | 少量競爭 | 值得投入，注意差異化 |
| 41-60 | 中等競爭 | 需要明確的差異化策略 |
| 61-80 | 競爭激烈 | 需要非常強的差異化，或考慮 pivot |
| 81-100 | 高度飽和 | 除非有顛覆性優勢，否則建議轉向 |

重點不只看分數，更要看 `pivot_hints` 中的差異化建議。

---

## CI 整合

可在 GitHub Actions 中自動驗證 feature proposal：

```yaml
- uses: mnemox-ai/idea-check-action@v1
  with:
    idea: "把 Figma 設計稿轉成 React 元件"
    depth: "deep"
```

詳見 https://github.com/mnemox-ai/idea-check-action

---

## 故障排除

### Q: 搜尋結果為空

**A:** 嘗試用不同的描述方式，避免過於技術化的用語。idea-reality 會從描述中提取關鍵詞搜尋。

### Q: GitHub API 速率限制

**A:** 設定 `GITHUB_TOKEN` 環境變數以大幅提升限制。

### Q: Product Hunt 結果缺失

**A:** Deep 模式才會搜尋 Product Hunt，且需設定 `PRODUCTHUNT_TOKEN`。

---
title: AI Browser 瀏覽器工具指南
type: guide
date: 2026-03-22
author: Arlen
status: draft
tags:
  - ai
  - mcp
  - browser-automation
  - agent-browser
  - chrome-devtools
  - playwright
description: AI 操作瀏覽器的三大工具比較與使用指南 — agent-browser、Chrome DevTools MCP、Playwright MCP
---

# AI Browser 瀏覽器工具指南

## 概述

這份指南說明如何讓 AI Agent 操作瀏覽器。目前主流有三個工具，各有不同的設計理念與適用場景：

| 工具 | 維護者 | 設計理念 | 適用場景 |
|------|--------|----------|----------|
| **agent-browser** | Vercel Labs | AI-first，最省 Token | 日常自動化、抓資料、填表單 |
| **Chrome DevTools MCP** | Google | 深度除錯與效能分析 | Console、Network、效能追蹤 |
| **Playwright MCP** | Microsoft | 完整瀏覽器控制 | 登入態保持、多分頁、Network Mock |

---

## 為什麼 Token 消耗差異這麼大

同一個任務（開 Hacker News，取首頁文章列表）的實測比較：

| 工具 | 回傳資料量 | 約略 Token 數 | 相對倍數 |
|------|-----------|--------------|----------|
| agent-browser | 13.5 KB | ~3,500 | **1x**（基準） |
| Chrome DevTools MCP | 32 KB | ~9,500 | 2.7x |
| Playwright MCP | 58 KB | ~16,000 | 4.5x |

**根本原因：**

Playwright 和 Chrome DevTools MCP 原本是為人設計的工具。它們回傳完整的 Accessibility Tree — 每個靜態文字節點、每個裝飾性元素全部包含在內。

agent-browser 從 AI 的需求出發：

- **只回傳可互動元素**：要點按鈕就只給按鈕，要填表單就只給輸入框
- **無 MCP 工具定義開銷**：MCP Server 需在 context 中註冊 tool schema（Playwright 的 26+ 工具佔 ~13,700 tokens），agent-browser 作為 CLI 工具無此成本
- **最小化動作回應**：點擊按鈕後只回傳 `"Done"`，而非整頁更新

一個複雜任務與瀏覽器來回幾十次，這個差距累積起來非常驚人。10 步驟的工作流程：Playwright 約 114,000 tokens，agent-browser 約 7,000 tokens — **省 93%**。

---

## 快速決策

```
你需要什麼？
    │
    ├─ 開網頁、抓資料、填表單（省 Token）→ agent-browser
    │
    ├─ 看 console 錯誤、分析 network request → Chrome DevTools MCP
    │   └─ 效能追蹤、Lighthouse 審計、記憶體分析 → Chrome DevTools MCP
    │
    └─ 登入態保持、多分頁、network mock → Playwright MCP
        └─ 需要繞過 bot 偵測 → rebrowser（Playwright 變體）
```

**建議：三個都裝，看場景切換。** 日常跑 agent-browser，debug 開 Chrome DevTools MCP，需要登入態或 mock 時用 Playwright。

---

## 前置條件

- Node.js >= 20（Chrome DevTools MCP 要求 v20.19+）
- Chrome 瀏覽器（Chrome DevTools MCP 需要）
- 首次使用 Playwright / agent-browser 會自動下載 Chromium（~200 MB）

---

## 安裝

### 1. agent-browser（Vercel Labs）

| 項目 | 內容 |
|------|------|
| **GitHub** | https://github.com/vercel-labs/agent-browser |
| **NPM 套件** | `agent-browser` |
| **MCP 包裝** | `agent-browser-mcp`（第三方） |
| **授權** | Apache-2.0 |

> **重要：** agent-browser 本質是 CLI 工具，不是 MCP Server。在 Claude Code 中透過 Skill 整合（推薦），或使用第三方 MCP 包裝。

#### Claude Code（推薦：Skill 方式）

```bash
# 安裝 CLI
npm install -g agent-browser
# 下載 Chrome for Testing
agent-browser install

# 安裝 Skill（教 Claude Code 如何使用 agent-browser）
npx skills add https://github.com/vercel-labs/agent-browser --skill agent-browser -g -y
```

安裝後會在專案中建立 `.claude/skills/agent-browser/SKILL.md`，Claude Code 會自動學會 snapshot-ref 互動模式。

#### Claude Code（MCP 方式）

```bash
claude mcp add agent-browser -- npx agent-browser-mcp
```

```json
"agent-browser": {
  "type": "stdio",
  "command": "npx",
  "args": ["agent-browser-mcp"],
  "env": {}
}
```

#### Codex

```bash
codex mcp add agent-browser -- npx agent-browser-mcp
```

```toml
[mcp_servers.agent-browser]
command = "npx"
args = ["agent-browser-mcp"]
```

#### OpenCode

```json
"agent-browser": {
  "type": "local",
  "command": ["npx", "agent-browser-mcp"],
  "environment": {}
}
```

---

### 2. Chrome DevTools MCP（Google）

| 項目 | 內容 |
|------|------|
| **GitHub** | https://github.com/ChromeDevTools/chrome-devtools-mcp |
| **NPM 套件** | `chrome-devtools-mcp` |
| **授權** | Apache-2.0 |
| **狀態** | Public Preview |

#### Claude Code

```bash
claude mcp add chrome-devtools --scope user -- npx -y chrome-devtools-mcp@latest
```

```json
"chrome-devtools": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "chrome-devtools-mcp@latest"],
  "env": {}
}
```

#### Codex

```bash
codex mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest
```

```toml
[mcp_servers.chrome-devtools]
command = "npx"
args = ["-y", "chrome-devtools-mcp@latest"]
```

#### OpenCode

```json
"chrome-devtools": {
  "type": "local",
  "command": ["npx", "-y", "chrome-devtools-mcp@latest"],
  "environment": {}
}
```

#### 啟動選項

| 選項 | 說明 |
|------|------|
| `--headless` | 無頭模式 |
| `--slim` | 精簡模式，僅載入 3 個基本工具 |
| `--channel` | Chrome 通道：stable / canary / beta / dev |
| `--browserUrl` | 連接到已運行的 Chrome 實例 |
| `--wsEndpoint` | 透過 WebSocket 端點連接 |

---

### 3. Playwright MCP（Microsoft）

| 項目 | 內容 |
|------|------|
| **GitHub** | https://github.com/microsoft/playwright-mcp |
| **NPM 套件** | `@playwright/mcp` |
| **授權** | Apache-2.0 |

#### Claude Code

```bash
# 預設（headed 模式）
claude mcp add playwright -- npx @playwright/mcp@latest

# Headless 模式
claude mcp add playwright -- npx @playwright/mcp@latest --headless
```

```json
"playwright": {
  "type": "stdio",
  "command": "npx",
  "args": ["@playwright/mcp@latest"],
  "env": {}
}
```

#### Codex

```bash
codex mcp add playwright -- npx @playwright/mcp@latest
```

```toml
[mcp_servers.playwright]
command = "npx"
args = ["@playwright/mcp@latest"]
```

#### OpenCode

```json
"playwright": {
  "type": "local",
  "command": ["npx", "@playwright/mcp@latest"],
  "environment": {}
}
```

#### 啟動選項

| 選項 | 說明 | 預設值 |
|------|------|--------|
| `--browser` | 瀏覽器：chromium / firefox / webkit / msedge | chromium |
| `--headless` | 無頭模式 | false |
| `--viewport-size` | 視窗大小（寬x高） | 1280x720 |
| `--isolated` | 隔離模式（記憶體內 profile） | false |
| `--storage-state` | 載入預存的 cookie/session | — |
| `--user-data-dir` | 持久化瀏覽器 profile 目錄 | — |

---

## 使用指南

### agent-browser — 日常自動化

適合場景：開網頁抓資料、填表單、點按鈕、E2E 測試。

**核心概念 — Snapshot + Refs：**

agent-browser 只回傳可互動元素，並附上穩定的 `@e` 參考編號：

```
@e1: button "Sign In"
@e2: input[type=email] "Email"
@e3: input[type=password] "Password"
```

然後直接用 ref 操作：`click @e1`、`fill @e2 "user@example.com"`。

**範例：抓取 Hacker News 首頁文章**

```bash
# CLI 方式
agent-browser open "https://news.ycombinator.com"
agent-browser snapshot          # 取得頁面快照
agent-browser get text ".athing"  # 取得文章標題
```

**範例：填寫登入表單**

```bash
agent-browser open "https://example.com/login"
agent-browser snapshot -i       # 只顯示可互動元素
agent-browser fill @e2 "user@example.com"
agent-browser fill @e3 "password123"
agent-browser click @e1
```

**批次操作（減少啟動開銷）：**

```bash
agent-browser batch --json '[
  {"cmd": "open", "args": ["https://example.com"]},
  {"cmd": "snapshot", "args": []},
  {"cmd": "get", "args": ["text", "h1"]}
]'
```

**108+ 指令分類：**

| 類別 | 主要指令 |
|------|---------|
| 導航 | `open`, `close`, `tab`, `tab new`, `window new` |
| 互動 | `click`, `fill`, `type`, `press`, `hover`, `select`, `check` |
| 資訊 | `snapshot`, `get text/html/value/attr/title/url` |
| 等待 | `wait <selector>`, `wait --text`, `wait --url`, `wait --load` |
| 網路 | `network route/unroute/requests/har` |
| 儲存 | `cookies`, `storage local/session` |
| 媒體 | `screenshot`, `pdf`, `eval` |

---

### Chrome DevTools MCP — 除錯與效能分析

適合場景：看 console 錯誤、分析 network request、效能追蹤、Lighthouse 審計、記憶體分析。

**範例：檢查 console 錯誤**

```
navigate_page(url: "https://my-app.dev")
list_console_messages()           # 列出所有 console 訊息
get_console_message(id: "msg-1")  # 取得特定訊息（含 source-mapped stack trace）
```

**範例：分析網路請求**

```
navigate_page(url: "https://my-app.dev/api-page")
list_network_requests()                    # 列出所有請求
get_network_request(requestId: "req-42")   # 取得完整 request/response 詳情
```

**範例：效能追蹤**

```
navigate_page(url: "https://my-app.dev")
performance_start_trace()           # 開始追蹤
# ... 執行操作 ...
performance_stop_trace()            # 停止追蹤
performance_analyze_insight()       # 分析 Core Web Vitals (LCP, INP, CLS)
```

**範例：Lighthouse 審計**

```
navigate_page(url: "https://my-app.dev")
lighthouse_audit()  # accessibility, SEO, best practices 一次跑完
```

**範例：連接已運行的 Chrome（含登入態）**

```bash
# 先以 remote debugging 模式啟動 Chrome
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# 連接到已運行的 Chrome
claude mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest --browserUrl http://localhost:9222
```

**29 個工具分 6 大類：**

| 類別 | 工具數 | 主要功能 |
|------|--------|---------|
| Input Automation | 9 | click, fill, fill_form, hover, press_key, type_text, upload_file... |
| Navigation | 6 | navigate_page, new_page, close_page, list_pages, select_page, wait_for |
| Emulation | 2 | emulate（深色/淺色模式、地理位置、網路條件）, resize_page |
| Performance | 4 | start/stop trace, analyze insight, memory snapshot |
| Network | 2 | list/get network requests（含完整 request/response） |
| Debugging | 6 | evaluate_script, console messages, lighthouse_audit, screenshot, snapshot |

---

### Playwright MCP — 複雜流程控制

適合場景：登入態保持、多分頁操作、network mock、cookie 管理、跨瀏覽器測試。

**範例：持久化登入狀態**

```bash
# 方式一：持久化 profile
claude mcp add playwright -- npx @playwright/mcp@latest --user-data-dir ~/.playwright-mcp/profile

# 方式二：載入預存 cookie
claude mcp add playwright -- npx @playwright/mcp@latest --storage-state ./cookies.json
```

**範例：多分頁操作**

```
browser_navigate(url: "https://app.example.com/dashboard")
browser_tabs(action: "new", url: "https://app.example.com/settings")
browser_tabs(action: "list")       # 列出所有分頁
browser_tabs(action: "select", tabId: 0)  # 切換回第一個分頁
```

**範例：表單填寫與提交**

```
browser_navigate(url: "https://example.com/register")
browser_fill_form(fields: [
  { name: "Name", type: "textbox", ref: "name-ref", value: "Alice" },
  { name: "Email", type: "textbox", ref: "email-ref", value: "alice@example.com" }
])
browser_click(ref: "submit-ref")
```

**範例：用 JavaScript 提取結構化資料**

```javascript
browser_evaluate(() => {
  return Array.from(document.querySelectorAll('.article')).map(el => ({
    title: el.querySelector('h2')?.textContent?.trim(),
    url: el.querySelector('a')?.href
  }));
})
```

**工具分類：**

| 類別 | 主要功能 |
|------|---------|
| 導航 | navigate, navigate_back, snapshot |
| 互動 | click, type, fill_form, select_option, hover, drag, press_key |
| 資料 | evaluate (JS), take_screenshot, console_messages, network_requests |
| 分頁 | tabs (list/new/close/select), close |
| 對話 | handle_dialog, file_upload, wait_for, resize |

> 更完整的 Playwright MCP 使用指南請參閱 [PlaywrightMCP瀏覽器自動化.md](PlaywrightMCP瀏覽器自動化.md)。

---

## 完整功能比較

### 基本資訊

| 項目 | agent-browser | Chrome DevTools MCP | Playwright MCP |
|------|--------------|-------------------|----------------|
| 維護者 | Vercel Labs | Google | Microsoft |
| 類型 | CLI 工具 + 第三方 MCP 包裝 | MCP Server | MCP Server |
| NPM 套件 | `agent-browser` | `chrome-devtools-mcp` | `@playwright/mcp` |
| 工具/指令數 | 108+ CLI 指令 | 29 個 MCP 工具 | 21+ 個 MCP 工具 |
| 瀏覽器支援 | Chromium | Chrome only | Chromium / Firefox / WebKit |
| Node.js 版本 | >= 18 | >= 20.19 | >= 18 |

### Token 效率

| 項目 | agent-browser | Chrome DevTools MCP | Playwright MCP |
|------|--------------|-------------------|----------------|
| 工具定義開銷 | 0 tokens | ~10,000 tokens | ~13,700 tokens |
| 頁面快照大小 | ~1,000 tokens | ~8,000 tokens | ~15,000 tokens |
| 動作回應大小 | 最小（"Done"） | 中等 | 完整頁面更新 |
| 10 步工作流 | ~7,000 tokens | ~50,000 tokens | ~114,000 tokens |

### 功能矩陣

| 功能 | agent-browser | Chrome DevTools MCP | Playwright MCP |
|------|:---:|:---:|:---:|
| 頁面導航 | ✅ | ✅ | ✅ |
| 元素點擊/填表 | ✅ | ✅ | ✅ |
| 截圖 | ✅ | ✅ | ✅ |
| JavaScript 執行 | ✅ | ✅ | ✅ |
| Console 訊息 | ❌ | ✅（含 source map） | ✅（基本） |
| Network 檢視 | ✅（基本） | ✅（完整 req/res） | ✅（基本） |
| 效能追蹤 | ❌ | ✅ | ❌ |
| 記憶體快照 | ❌ | ✅ | ❌ |
| Lighthouse 審計 | ❌ | ✅ | ❌ |
| 裝置/網路模擬 | ❌ | ✅ | ❌ |
| 多分頁操作 | ✅ | ✅ | ✅ |
| Cookie 管理 | ✅ | ❌ | ✅ |
| 登入態保持 | ✅ | ✅（連接已運行 Chrome） | ✅（storage-state） |
| Network Mock | ✅ | ❌ | ✅ |
| 跨瀏覽器 | ❌ | ❌ | ✅ |
| 批次操作 | ✅ | ❌ | ❌ |
| 連接已運行瀏覽器 | ❌ | ✅（原生） | ❌ |

---

## 最佳實踐

### Token 節省策略

1. **日常任務用 agent-browser**：開網頁、抓資料、填表單，Token 消耗僅為 Playwright 的 1/16
2. **需要 debug 時才開 Chrome DevTools MCP**：console、network、效能追蹤
3. **只在需要時才用 Playwright**：登入態保持、多分頁、network mock

### agent-browser 最佳實踐

1. **用 `snapshot -i` 而非 `snapshot`**：只取互動元素，資料量更小
2. **善用 `batch` 指令**：多步驟操作一次送出，避免重複啟動開銷
3. **用 `get text` 精確提取**：比整頁 snapshot 更精簡

### Chrome DevTools MCP 最佳實踐

1. **用 `--slim` 模式減少工具定義開銷**：如果只需要基本功能
2. **用 `--browserUrl` 連接已登入的 Chrome**：避免重新登入
3. **效能追蹤要限定範圍**：start → 操作 → stop → analyze，避免長時間追蹤

### Playwright MCP 最佳實踐

1. **用 `browser_evaluate` 提取資料**：比 `browser_snapshot` 精簡（~0.5 KB vs ~15 KB）
2. **用 `--headless` 減少資源消耗**：不需要看到視窗時
3. **用 `--user-data-dir` 持久化 profile**：避免每次重新登入
4. **避免不必要的 navigate**：每次吃 ~15 KB context

---

## 常見問題

**Q: 三個工具會衝突嗎？**
A: 不會。它們是獨立的 MCP Server / CLI 工具，可以同時安裝。使用時根據場景選擇即可。

**Q: agent-browser 為什麼不直接做成 MCP Server？**
A: 因為 MCP 協議要求在 context 中註冊所有工具的 JSON Schema，這本身就會消耗大量 tokens。agent-browser 作為 CLI 工具透過 Skill 整合，避免了這個開銷。

**Q: Chrome DevTools MCP 可以連接到已登入的網站嗎？**
A: 可以。用 `--browserUrl` 或 `--wsEndpoint` 連接到已運行的 Chrome 實例，包含所有已登入的 session。

**Q: Playwright MCP 的 rebrowser 變體是什麼？**
A: rebrowser 是 Playwright 的一個 fork，專門優化了反偵測能力，適合需要繞過 bot detection 的場景。

**Q: 我只裝一個的話，裝哪個？**
A: agent-browser。它覆蓋大多數日常場景，且 Token 消耗最低。等遇到需要 debug 或複雜流程控制時，再加裝其他工具。

---

## 疑難排解

| 問題 | 原因 | 解決方式 |
|------|------|----------|
| agent-browser 安裝後找不到指令 | 未全域安裝 | `npm install -g agent-browser && agent-browser install` |
| Chrome DevTools MCP 連線失敗 | Chrome 版本太舊 | 更新至最新穩定版 |
| Playwright 首次啟動很慢 | 正在下載 Chromium | 等待下載完成，或手動 `npx playwright install chromium` |
| snapshot 回傳空白 | 頁面尚未載入 | 使用 `wait_for` 或 `wait --load` 等待載入完成 |
| 遇到 CAPTCHA | 偵測到自動化行為 | 降低請求頻率、使用持久化 profile、或手動處理 |
| MCP 工具未出現在工具列表 | 設定格式錯誤 | 檢查平台對應的設定格式（參閱[格式差異對照](#安裝)） |

---

## 相關資源

- [agent-browser GitHub](https://github.com/vercel-labs/agent-browser)
- [agent-browser-mcp GitHub](https://github.com/minhlucvan/agent-browser-mcp)（第三方 MCP 包裝）
- [Chrome DevTools MCP GitHub](https://github.com/ChromeDevTools/chrome-devtools-mcp)
- [Playwright MCP GitHub](https://github.com/microsoft/playwright-mcp)
- [MCP-SERVER-GUIDE.md](../MCP-SERVER-GUIDE.md) — 三平台 MCP 設定快速指南
- [PlaywrightMCP瀏覽器自動化.md](PlaywrightMCP瀏覽器自動化.md) — Playwright MCP 深入指南

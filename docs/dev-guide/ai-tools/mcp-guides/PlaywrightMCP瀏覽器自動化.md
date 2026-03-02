---
tags:
  - ai
  - mcp
  - browser-automation
  - playwright
  - claude-code
date created: 2026-03-02T22:00:00+08:00
date modified: 2026-03-02T22:00:00+08:00
description: Playwright MCP Server 使用指南 — 透過 MCP 協議操作瀏覽器，處理需要 JS 渲染的網頁
---

# Playwright MCP — 瀏覽器自動化

| 項目 | 內容 |
|------|------|
| **GitHub** | https://github.com/microsoft/playwright-mcp |
| **維護者** | Microsoft |
| **語言** | TypeScript |
| **授權** | Apache-2.0 |
| **NPM 套件** | `@playwright/mcp` |

---

## 解決什麼問題

許多網站（Google Search、Threads、SPA 應用）需要 JavaScript 渲染才能顯示內容。Claude Code 的 `WebFetch` 只能抓取靜態 HTML，遇到這類網站會拿到空白或 JS redirect 頁面。

Playwright MCP 提供完整的瀏覽器環境，讓 AI 能像人一樣操作網頁：導航、點擊、填表、提取資料。

| 沒有 Playwright MCP | 有 Playwright MCP |
|---------------------|-------------------|
| `WebFetch` 拿到 JS redirect 頁面 | 完整渲染後的頁面內容 |
| 無法操作動態 UI | 可點擊、填表、滾動 |
| 無法處理 SPA 路由 | 支援 SPA 導航 |

---

## 安裝

### Claude Code CLI（推薦）

```bash
# 預設（headed 模式，可看到瀏覽器視窗）
claude mcp add playwright -- npx @playwright/mcp@latest

# Headless 模式（無視窗，適合自動化任務）
claude mcp add playwright -- npx @playwright/mcp@latest --headless

# 指定瀏覽器
claude mcp add playwright -- npx @playwright/mcp@latest --browser firefox
```

### 手動設定 JSON

編輯 `~/.claude/settings.json` 或專案 `.mcp/settings.json`：

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest", "--headless"]
    }
  }
}
```

### 系統需求

- Node.js 18+
- 首次執行會自動下載 Chromium（約 200 MB）

---

## MCP 工具

Playwright MCP 提供的工具以 `mcp__playwright__` 為前綴。核心工具：

### 導航與頁面操作

| 工具 | 說明 |
|------|------|
| `browser_navigate` | 導航到 URL，回傳頁面 accessibility snapshot（~15 KB） |
| `browser_navigate_back` | 返回上一頁 |
| `browser_snapshot` | 取得當前頁面的 accessibility snapshot |
| `browser_click` | 點擊頁面元素 |
| `browser_type` | 在輸入框中輸入文字 |
| `browser_fill_form` | 一次填入多個表單欄位 |
| `browser_select_option` | 選擇下拉選單選項 |
| `browser_hover` | 滑鼠懸停在元素上 |
| `browser_drag` | 拖放元素 |
| `browser_press_key` | 按下鍵盤按鍵 |

### 資料提取

| 工具 | 說明 |
|------|------|
| `browser_evaluate` | 在頁面中執行 JavaScript，回傳結果 |
| `browser_take_screenshot` | 截圖（PNG/JPEG） |
| `browser_console_messages` | 取得 console 訊息 |
| `browser_network_requests` | 取得網路請求記錄 |

### 分頁管理

| 工具 | 說明 |
|------|------|
| `browser_tabs` | 列出、建立、關閉、切換分頁 |
| `browser_close` | 關閉瀏覽器 |

### 互動

| 工具 | 說明 |
|------|------|
| `browser_handle_dialog` | 處理 alert/confirm/prompt 對話框 |
| `browser_file_upload` | 上傳檔案 |
| `browser_wait_for` | 等待文字出現/消失或指定時間 |
| `browser_resize` | 調整視窗大小 |

---

## 啟動參數

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `--browser` | 瀏覽器引擎：`chromium`、`firefox`、`webkit`、`msedge` | `chromium` |
| `--headless` | 無頭模式（不顯示視窗） | `false`（顯示視窗） |
| `--viewport-size` | 視窗大小，格式 `寬x高` | `1280x720` |
| `--isolated` | 隔離模式（記憶體內 profile，不寫入磁碟） | `false` |
| `--storage-state` | 載入預存的 cookie/session（JSON 檔案路徑） | — |
| `--user-data-dir` | 持久化瀏覽器 profile 目錄 | — |

---

## 使用範例

### 場景一：Google 搜尋特定網站

```
browser_navigate(url: "https://www.google.com/search?q=site:threads.net+推薦+美食")
```

導航後自動回傳 snapshot，包含搜尋結果的文字內容。
接著用 `browser_evaluate` 提取結構化資料：

```javascript
// 提取 Google 搜尋結果中的 Threads 連結
() => {
  const results = [];
  const links = document.querySelectorAll('a[href*="threads.net/@"]');
  for (const link of links) {
    const h3 = link.querySelector('h3');
    if (!h3) continue;
    results.push({
      title: h3.textContent.trim(),
      url: link.href
    });
  }
  return results;
}
```

### 場景二：填寫表單並提交

```
browser_navigate(url: "https://example.com/login")
browser_fill_form(fields: [
  { name: "Email", type: "textbox", ref: "email-ref", value: "user@example.com" },
  { name: "Password", type: "textbox", ref: "password-ref", value: "..." }
])
browser_click(ref: "submit-button-ref")
```

### 場景三：持久化登入狀態

先用 `--user-data-dir` 啟動，登入後 cookie 會自動保存：

```bash
claude mcp add playwright -- npx @playwright/mcp@latest --user-data-dir ~/.playwright-mcp/profile
```

或用 `--storage-state` 載入預存的 cookie：

```bash
claude mcp add playwright -- npx @playwright/mcp@latest --storage-state ./cookies.json
```

---

## 最佳實踐

1. **搜尋任務用 `--headless`**：不需要看到瀏覽器視窗，減少資源消耗
2. **用 `browser_evaluate` 而非 `browser_snapshot`**：navigate 已自動回傳 snapshot，後續提取結構化資料用 JS evaluate，回傳量從 ~15 KB 降到 ~0.5 KB
3. **搭配 Context Mode MCP**：將 evaluate 結果索引到 Context Mode 知識庫，後續查詢用 `search` 而非重新 navigate，大幅節省 context
4. **snapshot 是免費的**：`browser_navigate` 已經回傳了 snapshot，不要浪費——從中提取需要的文字資訊
5. **避免不必要的 navigate**：每次 navigate 吃 ~15 KB context，翻頁或多頁搜尋時代價很高

---

## 注意事項

1. **Context 消耗**：`browser_navigate` 每次回傳 ~15 KB 的 accessibility snapshot，這是無法避免的。長對話中頻繁 navigate 會快速消耗 context window
2. **DOM 選擇器不穩定**：Google、Threads 等網站的 DOM 結構經常變動，`browser_evaluate` 中的選擇器可能隨時失效，需要準備 fallback 策略
3. **CAPTCHA**：Google 偵測到自動化行為時可能觸發 CAPTCHA，此時只能停止並告知使用者
4. **首次啟動較慢**：第一次使用會下載 Chromium，後續啟動速度正常
5. **記憶體使用**：Chromium 進程會佔用 200-500 MB 記憶體，使用完畢後建議用 `browser_close` 關閉

---

## 故障排除

### Q: 報錯 "browser not installed"

**A:** 執行 `mcp__playwright__browser_install` 工具，或手動安裝：
```bash
npx playwright install chromium
```

### Q: navigate 後 snapshot 是空的

**A:** 頁面可能還在載入。用 `browser_wait_for(text: "預期文字")` 等待載入完成後再操作。

### Q: browser_evaluate 回傳空結果

**A:** DOM 選擇器可能已過時。先用 `browser_snapshot` 檢查頁面結構，再調整選擇器。

### Q: 遇到 CAPTCHA 或被封鎖

**A:** 降低請求頻率、使用 `--user-data-dir` 持久化 profile（避免每次都像新用戶），或告知使用者手動處理。

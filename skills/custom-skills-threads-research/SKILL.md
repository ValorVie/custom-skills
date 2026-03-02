---
name: custom-skills-threads-research
description: >
  Search and analyze public Threads (threads.net) posts using Playwright MCP + Context Mode MCP.
  Google Search requires JS rendering, so Playwright handles search; Context Mode handles
  indexing, compression, and querying to minimize context window consumption.
  Supports keyword search via Google (site:threads.net), direct user profile browsing,
  batch multi-keyword research, and structured summarization.
  Use PROACTIVELY when: user mentions Threads, wants to find Threads posts, asks about
  threads.net discussions, wants social media research on Threads, asks for口碑/評價/推薦
  from Threads, or mentions any topic where Threads community opinions would be valuable.
  Also triggers for: "搜尋 Threads", "Threads 上有人說", "threads 口碑", "threads 評價",
  "threads 討論", "threads 推薦", "找 threads 貼文", "site:threads.net".
---

# Threads Research — 公開貼文搜尋與分析

透過 Google 搜尋搜尋 Threads 公開貼文，免登入、免 API key、無額度限制。

## 工具分工

| 工具 | 職責 | 原因 |
|------|------|------|
| **Playwright MCP** | 載入需要 JS 渲染的頁面（Google Search、Threads） | 這些網站不支援純 HTTP 抓取 |
| **Context Mode MCP** | 索引結果 + 按需查詢 | 避免大量資料灌入 context window |

> **核心原則：Playwright 負責抓取，Context Mode 負責儲存與查詢。**
> Playwright 的 `browser_navigate` 會回傳 ~15 KB snapshot 進入 context（無法避免），
> 所以要在 navigate 後立即用 `browser_evaluate` 提取精簡 JSON，
> 再用 Context Mode `index` 儲存，後續查詢用 `search` 而非重新載入頁面。

## MCP 依賴

本 skill 依賴以下兩個 MCP Server，執行前必須確認已安裝。

| MCP Server | 工具前綴 | 角色 | 必要性 |
|------------|----------|------|--------|
| **Playwright** | `mcp__playwright__*` | 載入 JS 渲染頁面（Google Search、Threads） | **必要** |
| **Context Mode** | `mcp__context-mode__*` | 索引結果 + 按需查詢，壓縮 context 消耗 | **必要** |

### 安裝指令

```bash
# Playwright MCP（headless 模式，適合搜尋任務）
claude mcp add playwright -- npx @playwright/mcp@latest --headless

# Context Mode MCP（MCP-only 安裝，推薦）
claude mcp add context-mode -- npx -y context-mode
```

> **參考文件**：
> - Playwright MCP：https://github.com/microsoft/playwright-mcp
> - Context Mode MCP：https://github.com/mksglu/claude-context-mode

### 執行時檢查

執行此 skill 前，確認以下工具可用。如果工具呼叫失敗或不存在，**立即停止並提醒使用者安裝**：

| 檢查項目 | 驗證方式 | 缺失時的提示訊息 |
|----------|----------|------------------|
| Playwright MCP | 呼叫 `mcp__playwright__browser_navigate` 是否可用 | `⚠️ 未偵測到 Playwright MCP。請執行：claude mcp add playwright -- npx @playwright/mcp@latest --headless` |
| Context Mode MCP | 呼叫 `mcp__context-mode__index` 是否可用 | `⚠️ 未偵測到 Context Mode MCP。請執行：claude mcp add context-mode -- npx -y context-mode` |

如果只有 Playwright 可用但 Context Mode 不可用，skill 仍可執行搜尋，但無法索引和查詢（失去後續查詢的 context 節省優勢）。
如果 Playwright 不可用，skill 無法執行（Google Search 需要 JS 渲染）。

## 調用鏈總覽

```
Phase 1: Playwright navigate + evaluate    → 提取結構化 JSON
Phase 2: Context Mode index                → 索引到 FTS5 知識庫
Phase 3: Context Mode search               → 按需查詢
Phase 4: Deep Dive (fetch_and_index 或 Playwright) → 深入閱讀 [按需]
Phase 5: Summarize                         → AI 整理結構化摘要
```

---

## Phase 1: Search — 搜尋貼文

### 模式 A：Google 關鍵字搜尋（預設）

適用於：搜尋任意主題的 Threads 討論。

**Step 1 — Playwright 載入 Google 搜尋結果頁：**

```
browser_navigate(
  url: "https://www.google.com/search?q=site:threads.net+{關鍵字用+連接}"
)
```

搜尋語法技巧：
- 基本搜尋：`site:threads.net 三民區 鍋燒意麵 推薦`
- 指定用戶：`site:threads.net/@username 關鍵字`
- 時間限制：加 `&tbs=qdr:m` (過去一個月) 或 `&tbs=qdr:y` (過去一年)
- 排除關鍵字：`site:threads.net 鍋燒意麵 -廣告`
- URL 中空格用 `+` 連接

**Step 2 — 立即用 `browser_evaluate` 提取結構化資料：**

不要用 `browser_snapshot`（已在 navigate 時回傳了）。
用 JS 提取精簡 JSON，回傳約 500 bytes vs snapshot 的 ~15 KB。

```javascript
// 在 Google 搜尋結果頁執行 — 已驗證可用（2026-03）
() => {
  const results = [];
  const links = document.querySelectorAll('a[href*="threads.net/@"]');
  for (const link of links) {
    const h3 = link.querySelector('h3');
    if (!h3) continue;
    const url = link.href;
    const title = h3.textContent.trim();
    const user = (url.match(/@([^/]+)/) || [])[1] || '';
    results.push({ title, url, user: '@' + user });
  }
  return results;
}
```

> **注意**：snippet（摘要）無法從 evaluate 穩定提取，因為 Google DOM 結構經常變動。
> 但 snapshot 回傳時已包含摘要文字，AI 可以從 snapshot 中讀取摘要，
> 結合 evaluate 的結構化 URL/標題，在 Phase 2 索引時寫入完整資訊。

**Step 3 — 翻頁（如需更多結果）：**

Google 分頁用 `&start=` 參數：
- 第 2 頁：`&start=10`
- 第 3 頁：`&start=20`

每次翻頁都要 `browser_navigate`（~15 KB snapshot），代價較高。
預設搜尋 1 頁（10 筆），使用者明確要求時才翻更多。

### 模式 B：直接瀏覽用戶頁面

適用於：查看特定用戶的最新貼文。

Threads 用戶頁面需要 JS 渲染，直接用 Playwright：

```
browser_navigate(url: "https://www.threads.net/@{username}")
```

然後 `browser_evaluate` 提取貼文列表，或讀取 snapshot 中的內容。

### 模式 C：批量多關鍵字搜尋

適用於：一次搜尋多組關鍵字，例如市場調查、競品分析。

對每組關鍵字依序執行模式 A 的 Step 1-2，所有結果在 Phase 2 索引到同一個 source：

1. 接收關鍵字陣列：`["三民區 鍋燒意麵", "前鎮區 早餐", "鳳山 滷味"]`
2. 對每個關鍵字執行 navigate + evaluate
3. 所有結果在 Phase 2 索引到共用 source（如 `threads-batch-高雄美食`）
4. Phase 3 可跨關鍵字搜尋

---

## Phase 2: Index — 索引到 Context Mode 知識庫

將 Phase 1 提取的結構化資料 + snapshot 中讀到的摘要，整理成 Markdown 格式後索引。

```
index(
  content: "整理後的 Markdown 內容",
  source: "threads-search-{主題}"
)
```

### 索引格式

每筆結果包含：標題、URL、用戶、摘要、地址（如有）、營業時間（如有）、互動數據（如有）。

```markdown
## Threads 搜尋：{關鍵字}（第 N 頁）

### 1. {標題}
- URL: {url}
- 用戶: @{username}
- 摘要: {從 snapshot 中提取的摘要文字}
- 地址: {如有}
- 營業時間: {如有}
- 互動: {讚數、回覆數，如有}

### 2. ...
```

> **重點**：摘要資訊從 `browser_navigate` 回傳的 snapshot 中提取（snapshot 已經在 context 中了，不浪費）。
> 結合 `browser_evaluate` 的結構化 URL/標題/用戶，產出完整的索引內容。

### source 命名規則

| 搜尋類型 | source 標籤格式 | 範例 |
|----------|----------------|------|
| 關鍵字搜尋 | `threads-search-{主題}` | `threads-search-鍋燒意麵` |
| 用戶頁面 | `threads-user-{username}` | `threads-user-kaohsiung_food` |
| 單篇貼文 | `threads-post-{POST_ID}` | `threads-post-DBxpG7DBXfN` |
| 批量搜尋 | `threads-batch-{專案名}` | `threads-batch-高雄美食調查` |

---

## Phase 3: Query — 從知識庫查詢（按需）

索引完成後，使用者的後續問題用 `search` 從知識庫查詢，不需要重新載入頁面。

```
search(
  queries: ["地址 營業時間", "價格 便宜", "推薦 最強 好吃", "互動 讚 回覆 熱門"],
  source: "threads-search-{主題}"
)
```

搜尋技巧：
- 用具體詞彙：「地址 營業時間」比「店家資訊」更精準
- 一次送多個 queries（5-8 個），避免多次呼叫觸發節流
- 用 `source` 參數限定搜尋範圍

---

## Phase 4: Deep Dive — 深入閱讀（按需）

當使用者對特定貼文感興趣，想看完整內容和回覆時觸發。

**優先嘗試 `fetch_and_index`**（Threads 單篇貼文頁面有時不需完整 JS 渲染）：

```
fetch_and_index(
  url: "https://www.threads.net/@username/post/POST_ID",
  source: "threads-post-{POST_ID}"
)
```

如果 `fetch_and_index` 內容為空或不完整，fallback 到 Playwright：

```
browser_navigate(url: "https://www.threads.net/@username/post/POST_ID")
```

然後用 `browser_evaluate` 或讀取 snapshot，將完整內容索引到 Context Mode。

---

## Phase 5: Summarize — 結構化摘要

搜尋和索引完成後，用 `search` 從知識庫收集所有資料，AI 整理成結構化摘要。

### 美食/店家推薦格式

```markdown
## 搜尋摘要：{關鍵字}
共找到 {N} 篇相關貼文

### 推薦排行（依互動熱度）
| 排名 | 店家 | 地點 | 亮點 | 互動 |
|------|------|------|------|------|
| 1 | XX鍋燒 | 三民區XX路 | 湯頭甜、CP值高 | 115讚 138回覆 |

### 有明確地址的店家
| 店家 | 地址 | 營業時間 |
|------|------|----------|
| ... | ... | ... |

### 關鍵發現
- ...
```

### 一般討論格式

```markdown
## 搜尋摘要：{關鍵字}
共找到 {N} 篇相關貼文

### 主要觀點
1. ...（支持：@user1, @user2）
2. ...（支持：@user3）

### 正反意見
- 正面：...
- 負面：...
```

---

## Context 消耗分析

| 步驟 | context 消耗 | 說明 |
|------|:---:|------|
| `browser_navigate` (Google) | ~15 KB | 無法避免，snapshot 自動回傳 |
| `browser_evaluate` (提取 JSON) | ~0.5 KB | 精簡結構化資料 |
| `index` (索引到 Context Mode) | ~0.1 KB | 只回傳確認訊息 |
| `search` (查詢知識庫) | ~1-2 KB | 只回傳匹配片段 |
| **單頁搜尋總計** | **~17 KB** | 其中 15 KB 是不可避免的 navigate snapshot |

對比不用此 skill（直接用 `browser_snapshot` + 手動閱讀）：

| 操作 | 不用此 skill | 用此 skill |
|------|:---:|:---:|
| 搜尋 1 頁 | ~15 KB（且結果用完就沒了） | ~17 KB（但結果可重複查詢） |
| 搜尋 5 頁 | ~75 KB | ~75 KB（但所有結果可交叉查詢） |
| 後續追問 5 次 | 每次 ~15 KB 重新載入 | 每次 ~1 KB（search 知識庫） |
| **長對話總計** | **~150 KB+** | **~80 KB（節省 47%+）** |

> **關鍵優勢不在首次搜尋，而在後續查詢**：
> 索引後的結果可以用 `search` 反覆查詢，不需要重新 navigate。
> 在長對話中，這個優勢會越來越明顯。

---

## 錯誤處理

| 狀況 | 處理方式 |
|------|----------|
| `browser_evaluate` 回傳空陣列 | Google DOM 結構可能變動，直接從 snapshot 文字中手動提取 |
| Google 搜尋無結果 | 放寬關鍵字、移除 `site:` 改用 `threads.net` 作為關鍵字 |
| Threads 頁面 `fetch_and_index` 空內容 | 需 JS 渲染，fallback 到 Playwright |
| `search` 查不到結果 | 嘗試更具體的查詢詞，或檢查 source 標籤是否正確 |
| 搜尋結果過少 | 嘗試不同關鍵字組合，或移除時間限制 |
| 遇到 CAPTCHA | 停止自動化，告知使用者 |

---

## 注意事項

1. **navigate snapshot 無法避免**：Google Search 和 Threads 都需要 JS 渲染，Playwright `browser_navigate` 會自動回傳 snapshot，這是目前架構的已知限制
2. **善用已有 snapshot**：既然 snapshot 已經在 context 中，就要從中提取摘要資訊，不要浪費
3. **索引後用 search 而非重新載入**：後續追問一律用 Context Mode `search`，這是節省 context 的關鍵
4. **資料時效性**：Google 索引有延遲，最新的 Threads 貼文可能搜不到
5. **隱私尊重**：只搜尋公開貼文，不嘗試繞過任何存取限制
6. **知識庫生命週期**：Context Mode 的 FTS5 知識庫存在 tmpdir，session 結束自動清理
7. **語言**：Google 搜尋會根據 IP 和語言設定回傳結果，中文關鍵字通常能得到中文 Threads 貼文

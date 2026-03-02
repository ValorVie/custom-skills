---
tags:
  - ai
  - mcp
  - context-optimization
  - claude-code
date created: 2026-03-02T22:00:00+08:00
date modified: 2026-03-02T22:00:00+08:00
description: Context Mode MCP Server 使用指南 — 壓縮 MCP 工具輸出，延長 Claude Code 的 context window 可用時間
---

# Context Mode — 上下文壓縮

| 項目 | 內容 |
|------|------|
| **GitHub** | https://github.com/mksglu/claude-context-mode |
| **Stars** | 1,606 |
| **語言** | TypeScript |
| **授權** | MIT |
| **NPM 套件** | `context-mode` |

---

## 解決什麼問題

Claude Code 的 200K context window 會被 MCP 工具的原始輸出快速填滿。Playwright snapshot 一次 56 KB、20 個 GitHub issues 一次 59 KB、一份 access log 45 KB。30 分鐘後，40% 的 context 就沒了，model 開始變慢。

Context Mode 是一個 MCP 中介層：工具輸出在沙箱中處理，只有摘要進入 context。

| 沒有 Context Mode | 有 Context Mode |
|-------------------|-----------------|
| 原始輸出直接灌入 context | 在沙箱中處理，只回傳摘要 |
| 30 分鐘後 context 耗盡 40% | 45 分鐘後 context 仍剩 99% |
| 315 KB 工具輸出進入 context | 5.4 KB 摘要進入 context（98% 壓縮） |

---

## 安裝

### 方式一：Plugin Marketplace（推薦）

```bash
/plugin marketplace add mksglu/claude-context-mode
/plugin install context-mode@claude-context-mode
```

重啟 Claude Code 即完成。此方式會同時安裝：
- MCP Server
- PreToolUse hook（自動攔截並路由工具輸出）
- Slash commands（`/context-mode:stats`、`/context-mode:doctor`、`/context-mode:upgrade`）

### 方式二：僅 MCP Server（不含 hook）

```bash
claude mcp add context-mode -- npx -y context-mode
```

> **建議使用此方式。** Hook 會強制攔截所有工具輸出（包括 WebFetch、curl/wget），日常寫程式碼時反而增加摩擦。僅安裝 MCP Server 讓你自行決定何時使用 context-mode 工具。

### 方式三：本地開發

```bash
git clone https://github.com/mksglu/claude-context-mode.git
claude --plugin-dir ./claude-context-mode
```

---

## MCP 工具

Context Mode 提供 6 個 MCP 工具：

### 1. `batch_execute` — 批次執行（核心工具）

一次執行多個命令 + 多個搜尋查詢，大幅減少 tool call 次數。

| 參數 | 必填 | 說明 |
|------|------|------|
| `commands` | 否 | 命令陣列 `[{label, command}]` |
| `queries` | 否 | 搜尋查詢陣列 `["q1", "q2"]` |

```
// 範例：一次收集 git 狀態 + 測試結果 + 搜尋相關 issue
batch_execute(
  commands: [
    {label: "git-status", command: "git status"},
    {label: "test-results", command: "npm test 2>&1"}
  ],
  queries: ["authentication error", "login flow"]
)
```

**壓縮效果**：986 KB → 62 KB

### 2. `execute` — 沙箱執行程式碼

在獨立子程序中執行程式碼，只有 stdout 進入 context。

| 參數 | 必填 | 說明 |
|------|------|------|
| `language` | 是 | 程式語言（javascript, typescript, python, shell, ruby, go, rust, php, perl, r, elixir） |
| `code` | 是 | 要執行的程式碼 |
| `intent` | 否 | 意圖描述（超過 5KB 時用於過濾） |
| `timeout` | 否 | 逾時（毫秒，預設 30000） |

```
// 範例：分析大型 log 檔，只回傳摘要
execute(
  language: "shell",
  code: "cat access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -20"
)
```

**壓縮效果**：56 KB → 299 B

### 3. `execute_file` — 沙箱處理檔案

讀取檔案內容到沙箱中處理，原始檔案內容不進入 context。

| 參數 | 必填 | 說明 |
|------|------|------|
| `path` | 是 | 檔案路徑 |
| `language` | 是 | 處理用的程式語言 |
| `code` | 是 | 處理檔案的程式碼（可用 `FILE_CONTENT` 變數取得內容） |

```
// 範例：分析 CSV 檔案
execute_file(
  path: "analytics.csv",
  language: "python",
  code: "import csv\nreader = csv.reader(FILE_CONTENT.splitlines())\nfor row in list(reader)[:5]: print(row)"
)
```

**壓縮效果**：45 KB → 155 B

### 4. `index` — 索引內容到知識庫

將 Markdown 或文字切塊後存入 SQLite FTS5 知識庫，供後續搜尋。

| 參數 | 必填 | 說明 |
|------|------|------|
| `content` | 二擇一 | 要索引的文字內容 |
| `path` | 二擇一 | 要索引的檔案路徑 |
| `source` | 否 | 來源標籤（方便搜尋時過濾） |

### 5. `search` — 搜尋知識庫

查詢已索引的內容，支援多個查詢一次送出。

| 參數 | 必填 | 說明 |
|------|------|------|
| `queries` | 是 | 查詢陣列 `["q1", "q2", "q3"]` |
| `source` | 否 | 限定來源標籤 |

搜尋三層 fallback：
1. **Porter stemming** — "caching" 匹配 "cached", "caches"
2. **Trigram substring** — "useEff" 匹配 "useEffect"
3. **Levenshtein fuzzy** — "kuberntes" 修正為 "kubernetes"

### 6. `fetch_and_index` — 抓取 URL 並索引

抓取網頁 → 轉 Markdown → 切塊索引。原始網頁內容不進入 context。

| 參數 | 必填 | 說明 |
|------|------|------|
| `url` | 是 | 要抓取的 URL |
| `source` | 否 | 來源標籤 |

---

## 使用範例

### 場景一：分析大量 GitHub Issues

```
// 不用 context-mode：gh issue list 輸出 59 KB 直接灌入 context
// 用 context-mode：

batch_execute(
  commands: [{label: "issues", command: "gh issue list --limit 50 --json title,body,labels"}],
  queries: ["authentication bug", "login error", "token expired"]
)
// → 只回傳與查詢相關的 issue 摘要
```

### 場景二：處理大型 Log

```
execute_file(
  path: "/var/log/access.log",
  language: "python",
  code: """
import re
from collections import Counter
errors = [line for line in FILE_CONTENT.splitlines() if ' 5' in line or ' 4' in line]
paths = Counter(re.search(r'\"\\w+ (.+?) ', line).group(1) for line in errors if re.search(r'\"\\w+ (.+?) ', line))
for path, count in paths.most_common(10):
    print(f'{count:>5} {path}')
"""
)
```

### 場景三：索引文件後按需查詢

```
// 步驟 1：索引
fetch_and_index(url: "https://docs.example.com/api", source: "api-docs")

// 步驟 2：查詢
search(queries: ["authentication endpoint", "rate limiting", "error codes"])
```

---

## Slash Commands

| 指令 | 說明 |
|------|------|
| `/context-mode:stats` | 顯示當前 session 的 context 節省統計 — 每個工具的呼叫次數、token 消耗、壓縮比 |
| `/context-mode:doctor` | 執行診斷 — 檢查 runtime、hooks、FTS5、plugin 版本 |
| `/context-mode:upgrade` | 從 GitHub 拉最新版、重建、遷移快取、修復 hooks |

---

## 架構與運作原理

```
使用者提問
    │
    ▼
Claude Code ──→ MCP 工具呼叫
    │                │
    │          ┌─────┴─────┐
    │          │ PreToolUse │ ← Hook 攔截（僅 plugin 安裝時）
    │          │   Hook     │
    │          └─────┬─────┘
    │                │
    │     ┌──────────┴──────────┐
    │     │  Context Mode MCP   │
    │     │                     │
    │     │  ┌───────────────┐  │
    │     │  │ Sandbox       │  │ ← 原始輸出留在這裡
    │     │  │ (子程序執行)   │  │
    │     │  └───────┬───────┘  │
    │     │          │ stdout   │
    │     │  ┌───────┴───────┐  │
    │     │  │ FTS5 知識庫    │  │ ← 超過 5KB 時索引供搜尋
    │     │  └───────┬───────┘  │
    │     │          │ 摘要     │
    │     └──────────┴──────────┘
    │                │
    ▼                ▼
Context Window ← 只收到摘要（~2% 原始大小）
```

### 沙箱機制

- 每次 `execute` 建立獨立子程序，程序間不共享記憶體
- 輸出上限：100 KB 軟截斷（60% 開頭 + 40% 結尾），100 MB 硬上限
- 支援 credential passthrough：`gh`、`aws`、`gcloud`、`kubectl` 等 CLI 繼承環境變數
- Bun 可用時自動偵測並加速 JS/TS 執行（3-5x）

### 意圖驅動過濾

當輸出超過 5 KB 且提供了 `intent` 參數時：
1. 完整輸出索引到知識庫
2. 用 intent 搜尋匹配片段
3. 只回傳相關內容 + 可搜尋的詞彙表

### 搜尋節流

防止過多搜尋呼叫：
- 第 1-3 次：正常（每查詢 2 筆結果）
- 第 4-8 次：減少（每查詢 1 筆）+ 警告
- 第 9 次以上：阻擋，引導使用 `batch_execute`

---

## 最佳實踐

1. **優先使用 `batch_execute`**：一次呼叫完成多個命令 + 搜尋，比分開呼叫省 token 也省時間
2. **搜尋時多放查詢**：`search(queries: ["q1", "q2", "q3"])` 一次送多個，避免觸發節流
3. **善用 source 標籤**：索引時給 source，搜尋時可限定範圍
4. **日常小檔案直接 Read**：<50 行的檔案用 Read 更直接，不需要繞道沙箱
5. **提供 intent**：給 `execute` 加上 intent 參數，讓過濾更精準

---

## 安裝建議與取捨

### Plugin 安裝 vs MCP-only 安裝

| 面向 | Plugin（含 Hook） | MCP-only |
|------|-------------------|----------|
| **自動攔截** | 所有工具輸出自動路由 | 需手動呼叫 context-mode 工具 |
| **WebFetch** | 被完全 deny | 正常運作 |
| **curl/wget** | 被靜默替換為 echo | 正常運作 |
| **Read/Grep** | 每次注入建議提示 | 正常運作 |
| **Subagent** | 自動注入 routing 指令（~500 tokens） | 不影響 |
| **適用場景** | 資料密集型任務、長時間 session | 日常開發、精確 debug |

**建議**：先用 MCP-only 安裝體驗，確認符合需求後再考慮 plugin 安裝。

### 適用場景

| 場景 | 推薦程度 | 原因 |
|------|----------|------|
| 大量 log/CSV 分析 | 強烈推薦 | 原始資料不需進 context，壓縮效果顯著 |
| 批量讀取 GitHub issues/PR | 推薦 | 索引後按需查詢比全部灌入好 |
| Playwright 測試結果分析 | 推薦 | snapshot 很大，摘要通常夠用 |
| 文件索引與查詢 | 推薦 | FTS5 搜尋品質不錯 |
| 日常寫程式碼 | 不需要 | Read/Edit/Grep 輸出不大，攔截反而添亂 |
| 精確 debug | 不建議 | 壓縮可能丟失關鍵細節 |

---

## 注意事項

1. **資訊損耗**：壓縮的本質是丟棄資訊。model 看到的是摘要而非原始資料，在需要精確對比的任務中可能遺漏關鍵細節
2. **安全性**：沙箱子程序會繼承 GH_TOKEN、AWS 憑證等環境變數，注意 code 參數中的外部輸入
3. **Hook 自修復**：Plugin 安裝時，Hook 啟動會自動修改 `~/.claude/settings.json` 和 `installed_plugins.json`
4. **知識庫生命週期**：SQLite DB 存在 tmpdir，session 結束自動清理，不跨 session 保留

---

## 故障排除

### Q: 安裝後 WebFetch 無法使用

**A:** 這是 Plugin 安裝的 hook 行為，WebFetch 被強制 deny。改用 `fetch_and_index` 或切換到 MCP-only 安裝。

### Q: curl/wget 指令被替換成 echo

**A:** 同上，hook 會攔截 Bash 中的 curl/wget。改用 `execute(language: "shell", code: "curl ...")` 在沙箱中執行。

### Q: 搜尋結果不相關

**A:** 嘗試更具體的查詢詞，或用 `search` 的 `source` 參數限定範圍。搜尋支援 fuzzy 匹配但需至少 3 個字元。

### Q: Subagent 行為異常

**A:** Plugin 安裝會將 Bash subagent 自動升級為 general-purpose 並注入 routing 指令。如果不需要，改用 MCP-only 安裝。

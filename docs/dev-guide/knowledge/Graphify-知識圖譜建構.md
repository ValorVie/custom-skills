# Graphify — 知識圖譜建構

## 概述

Graphify 是一個 AI 編碼助手 skill，將程式碼、文件、論文、圖片等任意輸入轉為知識圖譜。它實作了 [LLM Wiki 設計哲學](2026040910-01-LLM-Wiki-設計哲學.md)中「持久編譯取代即時檢索」的理念，專門應用在程式碼與技術文件領域。

核心定位：**發現你不知道存在的結構。** 透過 AST 解析與 LLM 語意提取，建構跨檔案的概念關係圖譜。

## 前置條件

- Python 3.10+
- Claude Code（或其他支援的 AI 編碼助手：Codex、OpenCode、OpenClaw、Factory Droid、Trae）

## 快速開始

```bash
pip install graphifyy && graphify install
/graphify .                    # 對當前目錄建構圖譜
```

產出：

```
graphify-out/
├── graph.html       # 互動式圖譜 — 點選節點、搜尋、按社群過濾
├── GRAPH_REPORT.md  # 關鍵節點、意外連結、建議問題
├── graph.json       # 持久圖譜 — 數週後查詢無需重新讀取
└── cache/           # SHA256 快取 — 重跑只處理變更檔案
```

## 運作原理

Graphify 分兩個階段運作：

### 第一階段：AST 確定性解析（不需 LLM）

透過 tree-sitter 從程式碼檔案提取結構：類別、函式、匯入、呼叫圖、文件字串、設計理由註解。支援 20 種程式語言：Python、JS、TS、Go、Rust、Java、C、C++、Ruby、C#、Kotlin、Scala、PHP、Swift、Lua、Zig、PowerShell、Elixir、Objective-C、Julia。

### 第二階段：LLM 語意提取（平行子代理）

Claude 子代理平行處理文件、論文、圖片，提取概念、關係、設計理由。結果合併進 NetworkX 圖譜，以 Leiden 社群偵測演算法分群，匯出為互動 HTML、可查詢 JSON、純文字審計報告。

> 分群基於圖拓撲，不使用嵌入。Leiden 透過邊密度找到社群。語意相似度邊（`semantically_similar_to`，標記為 INFERRED）已在圖中，直接影響社群偵測。

### 信心標籤

每條關係都標記來源可靠度：

| 標籤 | 意義 | 信心分數 |
|------|------|----------|
| `EXTRACTED` | 直接從原始碼中找到 | 1.0（固定） |
| `INFERRED` | 合理推斷，附信心分數 | 0.0-1.0 |
| `AMBIGUOUS` | 標記待人工審查 | — |

## 支援的檔案類型

| 類型 | 副檔名 | 提取方式 |
|------|--------|----------|
| 程式碼 | `.py .ts .js .go .rs .java .c .cpp` 等 20 種 | AST (tree-sitter) + 呼叫圖 + 註解理由 |
| 文件 | `.md .txt .rst` | 概念 + 關係 + 設計理由 (Claude) |
| Office | `.docx .xlsx` | 轉 markdown 後提取 (需 `pip install graphifyy[office]`) |
| 論文 | `.pdf` | 引用挖掘 + 概念提取 |
| 圖片 | `.png .jpg .webp .gif` | Claude Vision — 截圖、圖表、任何語言 |

## 指令總覽

### 基礎操作

```bash
/graphify .                        # 對當前目錄建構
/graphify ./raw                    # 對特定資料夾建構
/graphify ./raw --mode deep        # 更積極的推斷邊提取
/graphify ./raw --update           # 增量更新，只處理變更檔案
/graphify ./raw --no-viz           # 跳過 HTML，只產生報告 + JSON
```

### 查詢圖譜

```bash
/graphify query "什麼連接 attention 和 optimizer？"
/graphify query "顯示認證流程" --dfs      # 追蹤特定路徑
/graphify path "DigestAuth" "Response"     # 兩節點間的路徑
/graphify explain "SwinTransformer"        # 解釋特定節點
```

### 匯入外部來源

```bash
/graphify add https://arxiv.org/abs/1706.03762    # 抓取論文並更新圖譜
/graphify add https://x.com/karpathy/status/...   # 抓取推文
```

### 匯出與整合

```bash
/graphify ./raw --wiki             # 產生 agent 可爬的 wiki
/graphify ./raw --obsidian         # 產生 Obsidian vault
/graphify ./raw --svg              # 匯出 SVG
/graphify ./raw --neo4j            # 產生 Neo4j Cypher
/graphify ./raw --mcp              # 啟動 MCP stdio 伺服器
```

### 自動同步

```bash
/graphify ./raw --watch            # 檔案變更時自動同步圖譜
graphify hook install              # Git hooks — commit 與 branch switch 後自動重建
```

## 產出內容

| 產出 | 說明 |
|------|------|
| 關鍵節點 (God Nodes) | 最高度數的概念 — 所有東西都透過它們連接 |
| 意外連結 | 依複合分數排序。跨程式碼與論文的邊排名更高。每項含純文字解釋 |
| 建議問題 | 4-5 個圖譜特別適合回答的問題 |
| 設計理由 (Why) | 從文件字串、行內註解、設計文件提取的 `rationale_for` 節點 |
| 語意相似度邊 | 跨檔案但無結構連接的概念連結 |
| 超邊 (Hyperedges) | 連接 3+ 節點的群組關係 |
| Token 基準 | 自動計算。混合語料庫：**71.5 倍**的每次查詢 token 節省 |

## 常駐模式

建構圖譜後，可安裝常駐指令讓 AI 助手自動參考圖譜：

```bash
graphify claude install     # CLAUDE.md + PreToolUse hook
graphify codex install      # AGENTS.md + hooks
```

安裝後，AI 助手在每次 Glob/Grep 前會先讀取 `GRAPH_REPORT.md`，透過圖譜結構導航而非逐檔案搜尋。

**常駐 vs 明確觸發的差異：**

- **常駐 hook**：提供 `GRAPH_REPORT.md` 一頁摘要（關鍵節點、社群、意外連結），涵蓋日常問題
- **`/graphify` 指令**：逐跳遍歷 `graph.json`，追蹤精確路徑，揭示邊級別細節。用於需要從圖譜中回答特定問題的場合

> 常駐 hook 給助手一張地圖；`/graphify` 指令讓它精確導航地圖。

## 排除檔案

在專案根目錄建立 `.graphifyignore`，語法與 `.gitignore` 相同：

```
vendor/
node_modules/
dist/
*.generated.py
```

## 與 LLM Wiki 哲學的對應

| LLM Wiki 概念 | Graphify 實作 |
|---------------|---------------|
| 原始來源層 | 輸入的程式碼、文件、論文、圖片 |
| Wiki 層 | `graphify-out/`（圖譜 + 報告 + JSON） |
| 模式定義層 | `SKILL.md` + `.graphifyignore` |
| 匯入操作 | `/graphify .` 和 `/graphify add <url>` |
| 查詢操作 | `/graphify query` + `/graphify path` + `/graphify explain` |
| 維護操作 | `--update` 增量更新 + `--watch` 自動同步 |
| 索引 | `GRAPH_REPORT.md`（常駐 hook 使用的入口） |
| 日誌 | SHA256 cache（追蹤已處理檔案） |
| 編譯一次持續維護 | 首次提取建構圖譜，後續查詢讀取緊湊圖譜而非原始檔案 |

## 三工具完整比較

| 面向 | LLM Wiki 哲學 | Personal Wiki Skill | Graphify |
|------|---------------|-------------------|----------|
| 定位 | 設計模式 | 個人資料編譯器 | 程式碼/文件圖譜建構器 |
| 輸入 | 任何來源 | 日記、筆記、訊息 | 程式碼、文件、論文、圖片 |
| 輸出 | markdown wiki | 敘事性文章 + wikilinks | NetworkX 圖譜 + HTML + JSON |
| 處理核心 | LLM 增量編譯 | LLM 逐條理解與綜合 | AST 解析 + LLM 語意提取 |
| 結構發現 | 人工 + LLM 共同演進 | 目錄從資料自然浮現 | Leiden 社群偵測自動分群 |
| 信心標記 | 無（由 LLM 判斷） | 無（由 LLM 寫作品質保證） | EXTRACTED / INFERRED / AMBIGUOUS |
| 增量更新 | 概念層級 | `absorb` 追蹤已吸收條目 | SHA256 快取，只處理變更檔案 |
| 查詢方式 | 讀索引 → 深入頁面 | 讀 `_index.md` → 跟隨 wikilinks | 讀 `GRAPH_REPORT.md` → 圖譜遍歷 |
| 適合 | 任何知識累積場景 | 個人回顧、人生記錄、研究 | 程式碼理解、架構審查、技術研究 |
| 維護成本 | 取決於實作 | 定期 cleanup + breakdown | 自動（watch / git hooks） |

### 何時用哪個

| 場景 | 推薦工具 |
|------|----------|
| 整理個人日記、筆記、訊息成知識庫 | Personal Wiki Skill |
| 理解大型程式碼庫的架構與依賴 | Graphify |
| 研究主題累積（論文、文章、報告） | 兩者皆可，視輸出偏好。想要敘事→ Wiki Skill，想要結構→ Graphify |
| 團隊內部知識管理 | 依知識類型。文化/流程→ Wiki Skill，技術架構→ Graphify |
| 從零開始設計自己的知識管理系統 | 先讀 LLM Wiki 哲學，再選擇適合的實作 |

### 互補使用

兩個工具可以並行運作：

1. **Personal Wiki Skill** 處理敘事性內容 — 人物、事件、決策、模式
2. **Graphify** 處理結構性內容 — 程式碼架構、模組關係、概念圖譜
3. 交叉引用：wiki 文章可以引用 Graphify 發現的架構關係，Graphify 的 `--wiki` 產出可作為 Personal Wiki 的輸入來源

## 隱私

- 程式碼檔案：完全在本地處理（tree-sitter AST），不傳送任何內容到外部
- 文件/論文/圖片：傳送至 AI 平台的模型 API 進行語意提取（使用你自己的 API 金鑰）
- 無遙測、無使用追蹤、無任何分析

## 技術堆疊

NetworkX + Leiden (graspologic) + tree-sitter + vis.js。不需要 Neo4j，不需要伺服器，完全在本地執行。

## 相關資源

- [Graphify GitHub](https://github.com/safishamsi/graphify)
- [LLM Wiki 設計哲學](LLM-Wiki-設計哲學.md)
- [Personal Wiki Skill 指南](Personal-Wiki-Skill-個人知識編譯.md)

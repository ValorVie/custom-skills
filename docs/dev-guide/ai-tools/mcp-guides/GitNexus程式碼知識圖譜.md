---
tags:
  - ai
  - mcp
  - code-intelligence
  - knowledge-graph
date created: 2026-03-02T14:00:00+08:00
date modified: 2026-03-02T15:30:00+08:00
description: GitNexus MCP Server 使用指南 — 將程式碼庫索引為知識圖譜，讓 AI 助手理解架構關係與相依性
---

# GitNexus — 程式碼知識圖譜

| 項目 | 內容 |
|------|------|
| **GitHub** | https://github.com/abhigyanpatwari/GitNexus |
| **Stars** | 7,714 |
| **語言** | TypeScript |
| **授權** | PolyForm Noncommercial |
| **套件** | `gitnexus`（npm） |

---

## 解決什麼問題

AI 程式碼助手在處理大型程式碼庫時**缺乏架構感知**：修改某個函式時不知道誰在呼叫它、除錯時看不到完整執行路徑、重構時不知道哪些檔案緊密耦合。

GitNexus 透過 Tree-sitter 解析原始碼並建構 KuzuDB 知識圖譜，**預計算**叢集、呼叫鏈、相依性，讓 AI 單次查詢即可取得完整上下文。

| 沒有 GitNexus | 有 GitNexus |
|--------------|-------------|
| AI 用 grep 文字匹配找程式碼 | 語義 + 結構 + BM25 混合搜尋 |
| 修改前需手動追蹤影響範圍 | 自動計算 blast radius |
| 重構靠 find-replace | 多檔案協調重構，確保所有參考更新 |
| 多次查詢拼湊上下文 | 單次查詢回傳完整上下文 |

---

## 安裝

### 前置需求

| 需求 | 版本 | 說明 |
|------|------|------|
| Node.js | >= 18 | 執行 CLI 和 MCP Server |
| Git | 任意 | 分析 git diff |

### 方式一：全域安裝（推薦）

```shell
npm install -g gitnexus
```

### 方式二：使用 npx（免安裝）

```shell
npx gitnexus analyze
```

### 驗證安裝

```shell
gitnexus --version
```

### 索引程式碼庫

```shell
# 在 repo 根目錄執行
cd your-project
gitnexus analyze

# 或指定路徑
gitnexus analyze /path/to/repo
```

索引完成後，圖譜資料儲存在 `~/.gitnexus/` 目錄，支援多 repo 全域管理。

### CLI 常用指令

| 指令 | 說明 |
|------|------|
| `gitnexus analyze [path]` | 索引程式碼庫 |
| `gitnexus mcp` | 啟動 MCP Server |
| `gitnexus serve` | 啟動本地 HTTP Server（Web UI） |
| `gitnexus list` | 列出已索引的 repo |
| `gitnexus wiki [path]` | 從圖譜生成 wiki 文件 |

---

## 設定

### Claude Code（推薦）

```bash
claude mcp add gitnexus --scope user -- npx -y gitnexus@latest mcp
```

### Cursor

編輯 `~/.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "gitnexus": {
      "command": "npx",
      "args": ["-y", "gitnexus@latest", "mcp"]
    }
  }
}
```

### Windsurf

編輯 `~/.windsurf/mcp.json`，格式同 Cursor。

### OpenCode

```json
{
  "mcp": {
    "gitnexus": {
      "type": "local",
      "command": ["npx", "-y", "gitnexus@latest", "mcp"]
    }
  }
}
```

### 驗證 MCP 連線

在 AI 助手中測試：

```
請使用 gitnexus 列出已索引的 repo
```

---

## MCP 工具

GitNexus 提供 7 個 MCP 工具：

### 1. `list_repos` — 探索已索引的 repo

列出所有已索引的 repo 及其基本資訊。

### 2. `query` — 混合搜尋

結合 BM25 文字搜尋、語義搜尋和 RRF 排序。

**使用時機**：尋找特定功能的實作位置、探索不熟悉的程式碼區域。

### 3. `context` — 360 度符號視圖

給定一個符號，回傳完整上下文：定義、呼叫者、被呼叫者、相關型別。

**使用時機**：深入理解某個函式或類別的角色。

### 4. `impact` — 影響範圍分析

分析修改某個符號後，哪些程式碼會受影響，按深度分組。

**使用時機**：修改前評估風險、規劃重構範圍。

### 5. `detect_changes` — Git diff 影響映射

讀取 git diff，自動分析所有變更的影響範圍。

**使用時機**：提交前檢查、程式碼審查。

### 6. `rename` — 多檔案協調重構

基於知識圖譜的重新命名，確保所有參考點都被更新。

**使用時機**：安全重構、批量重新命名。

### 7. `cypher` — 原始圖查詢

直接用 Cypher 查詢語言操作知識圖譜。

**使用時機**：自訂查詢、探索圖結構、撰寫複雜分析。

---

## 使用範例

### 新人入職 — 快速理解程式碼庫

```
這個專案的核心模組有哪些？它們之間的關係是什麼？
```

AI 透過 `query` + `context` 工具回傳架構概覽。

### 除錯 — 追蹤呼叫鏈

```
processPayment 函式的完整呼叫鏈是什麼？誰呼叫它、它呼叫誰？
```

### 重構 — 評估影響範圍

```
我想重構 AuthMiddleware，影響範圍有多大？
```

AI 透過 `impact` 工具回傳所有受影響的檔案和函式。

### 提交前檢查

```
分析我目前的 git diff，有沒有遺漏需要同步修改的地方？
```

### 生成架構文件

```shell
gitnexus wiki .
```

或請 AI 基於圖譜生成特定格式的文件。

---

## 進階配置

### Agent Skills（自動安裝）

GitNexus 會自動在 `.claude/skills/` 安裝 4 個技能：

| Skill | 觸發情境 | 功能 |
|-------|----------|------|
| **Exploring** | 瀏覽不熟悉的程式碼 | 透過知識圖譜導航 |
| **Debugging** | 除錯 | 沿呼叫鏈追蹤 bug 來源 |
| **Impact Analysis** | 評估變更 | 自動計算影響半徑 |
| **Refactoring** | 重構 | 利用相依性地圖規劃安全重構 |

### MCP Resources & Prompts

| 類型 | 名稱 | 說明 |
|------|------|------|
| Resource | clusters | 模組叢集資訊 |
| Resource | processes | 執行流程追蹤 |
| Resource | schema | 圖譜結構定義 |
| Prompt | `detect_impact` | 提交前影響分析 |
| Prompt | `generate_map` | 架構文件生成 |

### 兩種部署模式

| | CLI + MCP | Web UI |
|---|---|---|
| **用途** | 本地索引 + AI 編輯器整合 | 瀏覽器內視覺化探索 |
| **規模** | 任意大小 repo | 約 5,000 檔案 |
| **儲存** | KuzuDB 原生（持久化） | KuzuDB WASM（記憶體內） |

### 支援的程式語言

TypeScript, JavaScript, Python, Java, Kotlin, C, C++, C#, Go, Rust, PHP, Swift（共 12 種）

### 授權注意事項

GitNexus 採用 **PolyForm Noncommercial** 授權。個人學習、研究可自由使用；商業用途需取得商業授權。

---

## 故障排除

### Q: 索引時出現 parser unavailable 警告

**A:** 某些語言的 Tree-sitter parser 可能尚未安裝，這是警告而非錯誤，不影響其他語言的索引。

### Q: MCP Server 連線失敗

**A:** 確認 MCP 設定正確：

```shell
claude mcp list
claude mcp remove gitnexus
claude mcp add gitnexus --scope user -- npx -y gitnexus@latest mcp
```

### Q: 索引後 AI 查不到結果

**A:** 可能原因：
1. repo 未索引：執行 `gitnexus list` 確認
2. 索引過期：重新執行 `gitnexus analyze`
3. MCP 未連接：重新啟動 AI 工具

### Q: 索引大型 repo 耗時過長

**A:** 確保 `.gitignore` 已排除 `node_modules/`、`vendor/` 等目錄。索引只需執行一次，後續查詢都是即時的。

### Q: Web UI 載入大型 repo 卡住

**A:** Web UI 受瀏覽器記憶體限制（約 5,000 檔案），大型 repo 請使用 CLI + MCP 模式。

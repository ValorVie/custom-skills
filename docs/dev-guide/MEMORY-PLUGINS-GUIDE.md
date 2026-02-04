# Claude Code 記憶外掛使用指南

本指南說明如何同時使用 **ecc-hooks** 與 **claude-mem** 兩套記憶外掛，以及日常操作注意事項。

---

## 快速參考

| 面向 | ecc-hooks | claude-mem |
|------|-----------|------------|
| 記憶儲存 | 純文字檔 (`~/.claude/sessions/*.tmp`) | SQLite + Chroma 向量資料庫 (`~/.claude-mem/`) |
| 運作方式 | 全自動（Hook 驅動） | 全自動（Hook + Worker 服務） |
| 搜尋能力 | `/sessions` 指令（關鍵字比對） | MCP 工具搜尋（全文 + 語意） |
| 額外功能 | 代碼品質檢查、格式化、debug 警告 | Web UI、漸進式揭露、隱私控制 |
| AI 模型呼叫 | ❌ 無（純本地腳本） | ✅ 每次工具使用 + 每次停止都呼叫 AI |
| 額外成本 | 零 | 視提供商而定（可用 Gemini 免費層） |
| 手動操作 | `/sessions` 指令 | MCP 搜尋工具 |

---

## 兩套並用時的行為

兩個外掛各自獨立運作，**不會互相衝突**。它們掛載在相同的 Claude Code Hook 事件上，但各做各的事：

### 上下文佔用量

兩套並用**不會造成顯著的上下文浪費**，因為注入的內容性質不同且互補：

| 外掛 | SessionStart 注入內容 | 估計 token 佔用 |
|------|----------------------|----------------|
| ecc-hooks | 上一次會話的結構化事實（git 變更、修改檔案、commit 記錄） | ~500-1200 tokens |
| claude-mem | 語意摘要索引（近期會話的結構化摘要） | ~800-1000 tokens |

ecc-hooks 的 SessionStart 會自動載入最近一個 .tmp 檔的完整內容（結構化事實：git 變更摘要、修改檔案清單、commit 記錄、工作目錄狀態），並透過 stdout 注入上下文。內容有 10 KB 上限保護。

兩者內容互補、不重複：ecc-hooks 提供客觀的 git 事實（「改了哪些檔案、提交了什麼」），claude-mem 提供語意摘要（「做了什麼、為什麼做」）。兩套並用時的上下文開銷大約在 **1300-2200 tokens**。

### 上下文預算分析與調優觀察

ecc-hooks 的 .tmp 檔有 **10 KB 上限**（`MAX_CONTEXT_BYTES`，定義於 `session-start.py`）。以下是 10 KB 在不同內容類型下的實際容量：

| 內容類型 | 估計量 |
|---------|--------|
| 純英文字元 | ~10,000 字元 |
| 中英混合（本專案情境） | ~5,000-6,000 字元 |
| Markdown 行數 | ~150-250 行 |
| Token 數（Claude 估算） | ~2,500-3,500 tokens |

**實測數據（2026-02-04）：** 一次正常工作會話（修改 5 個檔案、2 次 commit、1 次 compaction）產出的 .tmp 檔約 **1.8 KB / 47 行**，遠低於 10 KB 上限。

**ecc-hooks 注入內容的價值分層：**

| 價值層級 | 內容 | Token 估算 |
|---------|------|-----------|
| 高（核心） | 專案名稱、修改檔案清單、commit 記錄 | ~500 tokens |
| 中（補充） | diff stat、工作目錄狀態 | ~500-700 tokens |
| 低（冗餘） | 多次 compaction 快照的重複中間狀態 | 視次數而定 |

**日常觀察要點：**

- 觀察 `~/.claude/sessions/*.tmp` 的實際大小，確認是否穩定在 1-3 KB 範圍
- 如果經常觸發 compaction（快照累積），注意 .tmp 檔是否膨脹到 5 KB 以上
- 若發現注入過多導致上下文浪費，可將 `MAX_CONTEXT_BYTES` 從 10 KB 降至 5 KB（約 ~1,500 tokens），修改位於 `plugins/ecc-hooks/scripts/memory-persistence/session-start.py`
- 理想的兩套並用總記憶開銷目標：**2,000-2,500 tokens**（ecc-hooks ~1,500 + claude-mem ~800-1000）

### Hook 生命週期完整對照

兩套外掛掛載在 Claude Code 的 6 種 Hook 事件上，各自負責不同的工作，**沒有功能重疊**：

| Hook 事件 | 觸發時機 | ecc-hooks | claude-mem |
|-----------|---------|-----------|------------|
| **SessionStart** | `startup`、`clear`、`compact` | `session-start.py`：載入上一次會話的結構化事實（git 變更、修改檔案、commit）並注入上下文、偵測套件管理器、顯示別名 | 4 步驟：`smart-install.js`（檢查依賴）→ `worker-service start`（啟動 HTTP 服務）→ `hook context`（注入歷史摘要）→ `hook user-message`（初始化提示） |
| **UserPromptSubmit** | 使用者每次送出訊息 | ❌ 未使用 | 2 步驟：確保 Worker 在線 → `hook session-init`（初始化會話） |
| **PreToolUse** | 工具執行前 | 4 個規則：阻擋 tmux 外 dev server、長時間命令提醒、git push 複審提醒、策略性壓縮建議 | ❌ 未使用 |
| **PreCompact** | 上下文壓縮前 | `pre-compact.py`：保存 git status + diff stat 快照到 .tmp 檔 | ❌ 未使用 |
| **PostToolUse** | 工具執行後 | 11 個規則：PR URL 記錄、JS/TS/PHP/Python 格式化、TS/PHPStan/mypy 靜態分析、debug 程式碼警告 | 確保 Worker 在線 → `hook observation`（記錄工具使用到 SQLite，超時 120 秒） |
| **Stop** | Claude 停止回應 | `check-debug-code.js`：掃描所有修改檔案的 debug 程式碼 | 確保 Worker 在線 → `hook summarize`（生成會話摘要，超時 120 秒） |
| **SessionEnd** | 會話結束 | 2 步驟：`session-end.py`（記錄結構化事實：git 變更、修改檔案、commit、工作狀態）→ `evaluate-session.py`（提取可重用模式） | ❌ 未使用 |

**要點：**

- **獨佔事件**：ecc-hooks 獨佔 `PreToolUse`、`PreCompact`、`SessionEnd`；claude-mem 獨佔 `UserPromptSubmit`
- **共用事件**：`SessionStart`、`PostToolUse`、`Stop` 兩套都掛載，但各做不同的事（代碼品質 vs 記憶儲存）
- **claude-mem 無 SessionEnd**：它在 `Stop` 時就完成摘要，不等到會話結束
- **claude-mem 每個 hook 都先執行 `worker-service start`**：冪等操作，確保 HTTP 服務在線（已在運行則跳過）

### 日常使用：不需要額外操作

兩套系統都是**全自動**的。正常使用 Claude Code 即可，不需要手動觸發任何記憶相關操作。

---

## 主動搜尋歷史記憶

當你需要回顧過去做過什麼時，有兩種方式：

### 方式 1：claude-mem MCP 搜尋（推薦）

claude-mem 提供 3 層漸進式搜尋工作流，Claude 會自動使用這些 MCP 工具：

```
步驟 1: search(query="認證 bug") → 取得索引清單（每筆約 50-100 tokens）
步驟 2: timeline(anchor=ID)      → 查看特定記錄前後的時間脈絡
步驟 3: get_observations([IDs])   → 取得完整詳情（每筆約 500-1000 tokens）
```

直接用自然語言詢問即可，例如：
- 「上次我修那個 API 錯誤時做了什麼？」
- 「過去一週我在這個專案做了哪些變更？」

Claude 會自動呼叫 MCP 搜尋工具來找答案。

### 方式 2：ecc-hooks `/sessions` 指令

```
/sessions list              # 列出最近的會話
/sessions load <id>         # 載入特定會話的上下文
/sessions alias <id> <name> # 為會話建立好記的別名
/sessions query <keyword>   # 搜尋會話內容
```

### 何時用哪個？

| 場景 | 建議方式 |
|------|---------|
| 語意搜尋（「上次修的那個 bug」） | claude-mem MCP |
| 列出最近會話清單 | `/sessions list` |
| 載入特定會話的完整上下文 | `/sessions load` |
| 瀏覽記憶的 Web UI | claude-mem（`http://localhost:37777`） |

---

## 隱私控制

### claude-mem：`<private>` 標籤

在對話中使用 `<private>` 標籤包裹敏感內容，claude-mem 不會儲存該段內容：

```
<private>
這段內容不會被記錄到 claude-mem 的資料庫中。
API_KEY=sk-xxxxx
</private>
```

### ecc-hooks

ecc-hooks 沒有內建隱私過濾機制。會話的 `.tmp` 檔案會記錄完整的會話狀態。如有敏感內容，需手動清理。

---

## 清理與維護

### claude-mem 資料清理

```bash
# 查看資料庫大小
ls -lh ~/.claude-mem/claude-mem.db

# Web UI 管理（推薦）
# 開啟 http://localhost:37777 可以瀏覽和管理所有記憶
```

claude-mem 的 Worker 服務會在 Claude Code 會話啟動時自動啟動，會話結束後會自動停止。如果需要手動管理：

```bash
# 檢查 Worker 狀態
curl -s http://localhost:37777/api/readiness

# 手動停止 Worker（通常不需要）
pkill -f "claude-mem.*worker"
```

### ecc-hooks 會話清理

```bash
# 查看會話檔案
ls -la ~/.claude/sessions/

# 清理超過 30 天的舊會話檔案
find ~/.claude/sessions/ -name "*.tmp" -mtime +30 -delete

# 清理所有會話檔案（完全重置）
rm ~/.claude/sessions/*.tmp
```

### 壓縮上下文提醒

ecc-hooks 會追蹤工具呼叫次數，達到 50 次時會建議執行 compact。看到提醒時，可以執行：

```
/compact
```

這會壓縮 Claude 的上下文視窗。ecc-hooks 會在壓縮前自動保存當前狀態（PreCompact hook）。

---

## 疑難排解

### claude-mem Worker 未啟動

症狀：搜尋工具無回應、Web UI 無法存取。

```bash
# 確認 Node.js 版本 >= 18
node --version

# 確認 Bun 已安裝
bun --version

# 查看 Worker 日誌
cat ~/.claude-mem/logs/worker.log
```

### ecc-hooks 格式化未觸發

症狀：PostToolUse 後沒有自動格式化。

確認對應的格式化工具已安裝：
- JS/TS: `npx prettier --version`
- PHP: `./vendor/bin/pint --version` 或 `php-cs-fixer --version`
- Python: `ruff --version` 或 `black --version`

### 兩套記憶內容是否重複？

**不會重複。** ecc-hooks 注入的是結構化 git 事實（改了哪些檔案、提交了什麼），claude-mem 注入的是語意摘要索引（做了什麼、為什麼做）。兩者內容性質完全不同，互為補充。

如果仍希望精簡，可以在 `~/.claude/settings.json` 停用其中一套，同時保留 ecc-hooks 的代碼品質功能：

```jsonc
// ~/.claude/settings.json
// 停用 claude-mem 但保留 ecc-hooks（含代碼品質）
{
  "enabledPlugins": {
    "ecc-hooks@custom-skills": true,
    "claude-mem@thedotmack": false
  }
}
```

---

## claude-mem AI 呼叫成本與提供商設定

### 成本說明

claude-mem 的記憶處理**需要呼叫外部 AI 模型**，會產生額外的 API 成本。以下是會觸發 AI 呼叫的時機：

| 時機 | Hook 事件 | 說明 |
|------|----------|------|
| 每次工具呼叫後 | PostToolUse | 將工具使用資料送給 AI Agent 做結構化分析和知識提取 |
| Claude 停止回應時 | Stop | 呼叫 AI 生成會話摘要 |

相比之下，**ecc-hooks 完全不呼叫任何外部 AI 模型**，所有操作都是本地腳本執行，零額外成本。

### 切換 AI 提供商

claude-mem 支援 3 種提供商，透過 `~/.claude-mem/settings.json` 設定：

**Claude SDK（預設）：**

使用你現有的 Claude 帳戶憑證，不需要額外設定 API key。品質最高但有成本。

```json
{
  "CLAUDE_MEM_PROVIDER": "claude"
}
```

**Gemini（推薦，可免費）：**

免費層每天 1500 次請求，適合大多數使用場景。

```json
{
  "CLAUDE_MEM_PROVIDER": "gemini",
  "CLAUDE_MEM_GEMINI_API_KEY": "your-api-key",
  "CLAUDE_MEM_GEMINI_MODEL": "gemini-2.5-flash-lite"
}
```

取得免費 API key：https://aistudio.google.com/apikey

**OpenRouter：**

支援多種模型，包含免費模型。

```json
{
  "CLAUDE_MEM_PROVIDER": "openrouter",
  "CLAUDE_MEM_OPENROUTER_API_KEY": "your-api-key"
}
```

取得 API key：https://openrouter.ai/keys

### 提供商比較

| 提供商 | 成本 | 品質 | 適用場景 |
|--------|------|------|---------|
| Claude SDK | 消耗 Anthropic API tokens | 最高 | 重視摘要品質 |
| Gemini | 免費層每天 1500 次 | 良好 | 日常開發（推薦） |
| OpenRouter | 視模型而定，有免費模型 | 視模型而定 | 需要特定模型 |

---

## 設計背景與架構決策

### 上游 ecc-hooks 記憶持久化的原始設計

ecc-hooks 的記憶持久化腳本源自上游 [everything-claude-code](https://github.com/anthropics/everything-claude-code)。經查閱上游完整 git 歷史（`f96ef1e` 初版 → `d85b1ae` 最新版，4 位貢獻者、6 次相關提交），確認記憶腳本**從未實作自動內容收集**，這是設計上的有意選擇，而非未完成的工作。

上游的設計模型是「**手動日記本**」：

| 環節 | 上游設計 | 使用者需要做什麼 |
|------|---------|----------------|
| 建立檔案 | session-end 自動建立空模板 | 不需要 |
| 填寫內容 | 模板留有 `[Session context goes here]` 佔位符 | 在對話中請 Claude 寫入，或自己手動填 |
| 載入舊會話 | session-start 用 stderr 提示「有 N 個舊會話」 | 看到提示後手動執行 `/sessions load` |
| 更新時間戳 | session-end 自動更新 `Last Updated` | 不需要 |

這個模型的根本問題是**依賴使用者養成習慣** — 每次結束前記得請 Claude 寫筆記、每次開始記得載入舊會話。實際上很難持續做到。

### 上游設計 vs claude-mem

| 面向 | 上游 ecc-hooks（原版） | claude-mem |
|------|----------------------|------------|
| 記錄觸發 | 手動（使用者或 Claude 在對話中寫入） | 全自動（PostToolUse + Stop） |
| 記錄內容 | 使用者自己決定 | AI 自動提取結構化知識 |
| 載入觸發 | 手動（看到提示後執行 `/sessions load`） | 全自動（SessionStart 注入摘要） |
| 搜尋能力 | 無 | MCP 工具 + 向量搜尋 |
| 跨會話連續性 | 依賴使用者記得操作 | 自動保持 |

結論：上游原版的「手動日記本」模式在有 claude-mem 的情況下**幾乎沒有獨立使用價值**。

### 改寫後的互補定位

我們將 ecc-hooks 從「手動日記本」改寫為「**自動事實記錄器**」，定位為 claude-mem 的零成本互補層：

| 面向 | ecc-hooks（改寫後） | claude-mem |
|------|---------------------|------------|
| 成本 | 零（純本地 git CLI） | 每次觸發 AI 呼叫 |
| 內容性質 | 客觀事實（git 資料，不會有幻覺） | AI 語意摘要（可能遺漏或曲解） |
| 可靠性 | 不依賴外部服務 | 依賴 Worker 服務 + AI 提供商 |
| 功能範圍 | 記錄「改了什麼」 | 記錄「做了什麼、為什麼做」 |

即使停用 claude-mem（例如為了節省成本），改寫後的 ecc-hooks 仍能提供基本的會話延續能力。兩套並用時，ecc-hooks 提供不可否認的事實基底，claude-mem 提供語意理解層。

---

## 設定檔位置

| 項目 | 路徑 |
|------|------|
| 全域外掛設定 | `~/.claude/settings.json` |
| ecc-hooks 會話資料 | `~/.claude/sessions/*.tmp` |
| claude-mem 資料庫 | `~/.claude-mem/claude-mem.db` |
| claude-mem 設定 | `~/.claude-mem/settings.json` |
| claude-mem 日誌 | `~/.claude-mem/logs/` |
| claude-mem Web UI | `http://localhost:37777` |

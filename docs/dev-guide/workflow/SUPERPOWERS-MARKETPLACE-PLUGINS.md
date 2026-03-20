# Superpowers Marketplace Plugin 分析

> 本文件分析 `obra/superpowers-marketplace` 中所有可用 plugin 的功能、安裝元件與推薦程度。
>
> 與 [SUPERPOWERS-GUIDE.md](SUPERPOWERS-GUIDE.md)（技能體系）互為姊妹文件。

---

## Marketplace 概覽

**來源：** `obra/superpowers-marketplace` (v1.0.13)
**維護者：** Jesse Vincent (jesse@fsck.com)
**安裝方式：** `/plugin marketplace add obra/superpowers-marketplace`

共提供 **9 個 plugin**（含 1 個 dev 分支版本）。

---

## Plugin 總覽

| # | Plugin | 版本 | 安裝元件 | 核心功能 |
|---|--------|------|---------|---------|
| 1 | superpowers | v5.0.5 | 14 skills, 3 commands, 1 agent, 1 hook | 核心技能庫（TDD、除錯、協作流程） |
| 2 | double-shot-latte | v1.2.0 | 1 hook | 攔截「要我繼續嗎？」自動判斷是否繼續 |
| 3 | elements-of-style | v1.0.0 | 1 skill | 英文寫作風格指南（Strunk 1918） |
| 4 | episodic-memory | v1.0.15 | 1 skill, 1 command, 1 agent, 1 hook, 1 MCP | 跨 session 對話語義搜尋 |
| 5 | claude-session-driver | v1.0.1 | 1 skill, 5 hooks, CLI scripts | 透過 tmux 管理多個 Claude worker |
| 6 | superpowers-chrome | v1.8.0 | 1 skill (17 子命令), 1 agent, 1 MCP | Chrome DevTools Protocol 瀏覽器自動化 |
| 7 | superpowers-lab | v0.3.0 | 4 skills | 實驗性技能（重複偵測、MCP CLI、tmux、Slack） |
| 8 | superpowers-developing-for-claude-code | v0.3.1 | 2 skills | Claude Code plugin 開發教學與 42 份官方文件 |
| 9 | superpowers-dev | dev branch | 同 superpowers | superpowers 開發版（不穩定） |

---

## 各 Plugin 詳細分析

### 1. superpowers（核心）

**GitHub：** https://github.com/obra/superpowers
**推薦程度：** 必裝

核心技能庫，完整說明見 [SUPERPOWERS-GUIDE.md](SUPERPOWERS-GUIDE.md)。

#### 安裝元件

| 類型 | 名稱 | 說明 |
|------|------|------|
| **Skills (14)** | using-superpowers | 技能路由入口，判斷調用哪些技能 |
| | brainstorming | 蘇格拉底式需求釐清與設計 |
| | writing-plans | 細粒度任務分解（2-5 分鐘/任務） |
| | using-git-worktrees | 隔離工作區建立與管理 |
| | subagent-driven-development | 子代理逐任務執行 + 雙重審查 |
| | executing-plans | 順序執行計畫任務（無 subagent 備選） |
| | test-driven-development | RED-GREEN-REFACTOR 循環 |
| | systematic-debugging | 四階段根本原因調查 |
| | verification-before-completion | 完成聲明前必須有新鮮證據 |
| | finishing-a-development-branch | 收尾流程（merge/PR/keep/discard） |
| | dispatching-parallel-agents | 平行子代理分派策略 |
| | requesting-code-review | 派遣審查子代理 |
| | receiving-code-review | 技術性評估收到的反饋 |
| | writing-skills | 用 TDD 方法撰寫新技能 |
| **Commands (3)** | /brainstorm | 已棄用，指向 brainstorming skill |
| | /write-plan | 已棄用，指向 writing-plans skill |
| | /execute-plan | 已棄用，指向 executing-plans skill |
| **Agents (1)** | code-reviewer | 程式碼品質審查子代理 |
| **Hooks (1)** | SessionStart | 注入 superpowers context（using-superpowers skill 指引） |

---

### 2. double-shot-latte

**GitHub：** https://github.com/obra/double-shot-latte
**推薦程度：** 強烈推薦

#### 做什麼

當 Claude 停下來問「要我繼續嗎？」時，自動用另一個 Claude 實例（預設 Haiku）判斷是否該繼續工作。如果判斷該繼續，就自動繼續，無需手動輸入 "continue"。

#### 運作機制

1. 攔截 `Stop` 事件
2. 取最近 10 條 transcript 發給 judge Claude
3. Judge 判斷：應該繼續 → 自動繼續；應該停止 → 正常停止
4. 節流保護：每 5 分鐘最多 3 次自動繼續（防止無限循環）

#### 安裝元件

| 類型 | 名稱 | 說明 |
|------|------|------|
| **Hooks (1)** | Stop | 執行 `claude-judge-continuation` 腳本 |

無 skills、commands、agents、MCP。

#### 注意事項

- 每次判斷消耗額外 API 呼叫
- 可透過 `DOUBLE_SHOT_LATTE_MODEL` 環境變數自訂 judge 模型
- 依賴：jq

#### 適用場景

跑長任務（SDD、大型重構、多步驟實作）時效果最好，大幅減少手動中斷。

---

### 3. elements-of-style

**GitHub：** https://github.com/obra/the-elements-of-style
**推薦程度：** 可選（中文為主的專案實用性有限）

#### 做什麼

提供 William Strunk Jr.《The Elements of Style》(1918) 完整 18 條寫作規則作為 AI 寫作指引。

#### 安裝元件

| 類型 | 名稱 | 說明 |
|------|------|------|
| **Skills (1)** | writing-clearly-and-concisely | 寫作規則指引（含 ~12k tokens 完整參考文本） |

無 hooks、commands、agents、MCP。

#### 適用場景

撰寫英文技術文件、README、部落格文章時有用。中文寫作場景不適用。

---

### 4. episodic-memory

**GitHub：** https://github.com/obra/episodic-memory
**推薦程度：** 視需求（與 claude-mem 功能重疊）

#### 做什麼

將過去的 Claude Code 對話索引後支援語義搜尋，可透過自然語言查詢過去的討論、決策與程式碼模式。

#### 運作機制

1. SessionStart 時自動從 `~/.claude/projects` 複製並索引對話
2. 使用 Transformers.js 在本地生成向量嵌入（不上傳雲端）
3. 支援語義搜尋（向量比對）和多概念 AND 搜尋
4. 搜尋結果由 agent 合成為摘要回覆

#### 安裝元件

| 類型 | 名稱 | 說明 |
|------|------|------|
| **Skills (1)** | remembering-conversations | 何時/如何搜尋過去對話的指引 |
| **Commands (1)** | /search-conversations | 搜尋過去對話的 slash command |
| **Agents (1)** | search-conversations | 搜尋並合成結果的子代理 |
| **Hooks (1)** | SessionStart | 非同步索引對話（sync --background） |
| **MCP Servers (1)** | episodic-memory | 提供 `episodic_memory_search` 和 `episodic_memory_show` 工具 |

#### 與 claude-mem 的比較

| 維度 | episodic-memory | claude-mem |
|------|----------------|-----------|
| 搜尋方式 | 向量嵌入語義搜尋 | 結構化觀察記錄 + 關鍵字搜尋 |
| 資料來源 | 自動索引 Claude Code 對話 | 手動/自動記錄觀察 |
| 查詢方式 | 自然語言概念查詢 | ID 查詢、關鍵字搜尋、timeline |
| 本地處理 | 嵌入在本地生成 | 依賴外部 API |
| 適用場景 | 「上次怎麼處理 X 的？」 | 「觀察 #3401 的詳細內容」 |

**結論：** 如果 claude-mem 的搜尋能力已滿足需求，可不裝。若需要更模糊的語義搜尋能力，可補裝。

---

### 5. claude-session-driver

**GitHub：** https://github.com/obra/claude-session-driver
**推薦程度：** 進階用途可選

#### 做什麼

讓一個 Claude session 當「專案經理」，透過 tmux 啟動並管理多個 Claude Code worker session，支援多種協調模式。

#### 協調模式

| 模式 | 說明 |
|------|------|
| Delegate and wait | 指派單一任務，等待結果 |
| Fan out | 平行多 worker 處理獨立任務 |
| Pipeline | 串連 worker，每個接手前一個的輸出 |
| Supervise | 多輪審查 worker 回應 |
| Hand off | 將 worker session 交還人類操作 |

#### 安裝元件

| 類型 | 名稱 | 說明 |
|------|------|------|
| **Skills (1)** | driving-claude-code-sessions | 協調模式指引 |
| **Hooks (5)** | PreToolUse | 工具呼叫前暫停等待審核（120s timeout） |
| | SessionStart | 發送 session 啟動事件 |
| | Stop | 發送停止事件 |
| | UserPromptSubmit | 發送 prompt 提交事件 |
| | SessionEnd | 發送 session 結束事件 |
| **CLI Scripts** | launch-worker.sh | 啟動 worker session |
| | converse.sh | 與 worker 對話 |
| | send-prompt.sh | 發送 prompt 給 worker |
| | wait-for-event.sh | 等待特定事件 |
| | read-events.sh | 讀取事件記錄 |
| | read-turn.sh | 讀取 worker 回應 |
| | stop-worker.sh | 停止 worker |
| | approve-tool.sh | 審核工具呼叫 |

無 commands、agents、MCP。

#### 注意事項

- 依賴：tmux、jq、claude CLI
- Worker 生命週期事件以 JSONL 記錄
- PreToolUse hook 會攔截**所有**工具呼叫（matcher: `*`），可能影響效能

#### 與現有工具的重疊

已有 `claude-devfleet`、`dmux-workflows`、`team-builder` 等多 agent 協調方案，以及 Claude Code 內建 Agent tool。

---

### 6. superpowers-chrome

**GitHub：** https://github.com/obra/superpowers-chrome
**推薦程度：** 視需求（與 Playwright MCP 功能重疊）

#### 做什麼

透過 Chrome DevTools Protocol (CDP) 直接控制瀏覽器，提供 CLI 模式和 MCP Server 模式。

#### 安裝元件

| 類型 | 名稱 | 說明 |
|------|------|------|
| **Skills (1)** | browsing | 瀏覽器自動化指引 + 17 個 CLI 子命令 |
| **Agents (1)** | browser-user | 瀏覽器自動化任務代理 |
| **MCP Servers (1)** | chrome | 單一 `use_browser` 工具（含自動截圖） |

無 hooks、commands。

#### 17 個 CLI 子命令

| 類別 | 命令 |
|------|------|
| 啟動 | `start` |
| 分頁管理 | `tabs`, `new`, `close` |
| 導航 | `navigate`, `wait-for`, `wait-text` |
| 互動 | `click`, `fill`, `select` |
| 擷取 | `eval`, `extract`, `attr`, `html` |
| 匯出 | `screenshot`, `markdown` |
| 進階 | `raw`（直接 CDP 存取） |

#### 與 Playwright MCP 的比較

| 維度 | superpowers-chrome | Playwright MCP |
|------|-------------------|---------------|
| 協定 | Chrome DevTools Protocol | Playwright API |
| 依賴 | 零依賴（內建 WebSocket） | Node.js + Playwright |
| 瀏覽器 | 僅 Chrome/Chromium | Chrome、Firefox、WebKit |
| 工具粒度 | 17 個 CLI 命令 / 單一 MCP 工具 | 每個動作一個 MCP 工具 |
| 適用場景 | 輕量、快速、零設定 | 完整 E2E 測試、多瀏覽器 |

**結論：** 已有 Playwright MCP 時功能重疊，除非需要更輕量的方案。

---

### 7. superpowers-lab

**GitHub：** https://github.com/obra/superpowers-lab
**推薦程度：** 觀望（實驗性）

#### 做什麼

四個實驗性 skill，功能可能隨開發演進。

#### 安裝元件

| 類型 | 名稱 | 說明 |
|------|------|------|
| **Skills (4)** | finding-duplicate-functions | LLM 驅動的語義層級程式碼重複偵測 |
| | mcp-cli | 按需存取 MCP server 的 CLI（不需永久設定） |
| | slack-messaging | 發送 Slack 訊息 |
| | using-tmux-for-interactive-commands | 透過 tmux 自動化互動式 CLI 工具 |

無 hooks、commands、agents、MCP。

#### 注意事項

- 版本 0.3.0，實驗性質
- 依賴：tmux（interactive commands）
- `finding-duplicate-functions` 使用兩階段：傳統提取 + LLM 意圖分群

---

### 8. superpowers-developing-for-claude-code

**GitHub：** https://github.com/obra/superpowers-developing-for-claude-code
**推薦程度：** 推薦（plugin 開發者）

#### 做什麼

提供 Claude Code 擴展開發的完整教學、42 份官方文件、範例 plugin。

#### 安裝元件

| 類型 | 名稱 | 說明 |
|------|------|------|
| **Skills (2)** | working-with-claude-code | 42 份官方文件涵蓋所有 Claude Code 功能 |
| | developing-claude-code-plugins | Plugin 開發工作流與最佳實踐 |

無 hooks、commands、agents、MCP。

#### 包含文件主題

quickstart、CLI reference、hooks、plugins、MCP、settings、security、headless mode、GitHub Actions、GitLab CI/CD、Amazon Bedrock、Google Vertex AI、VS Code、JetBrains、sub-agents 等。

#### 其他元件

- `scripts/update_docs.js` — 從 docs.claude.com 拉取最新文件
- `examples/full-featured-plugin/` — 完整範例 plugin
- `examples/simple-greeter-plugin/` — 最小範例 plugin

---

### 9. superpowers-dev

**推薦程度：** 不推薦

superpowers 的 `dev` 分支版本。**必須先卸載其他版本的 superpowers 才能安裝。** 用於測試尚未發布的功能，不穩定。

---

## 安裝元件統計

| Plugin | Skills | Commands | Hooks | Agents | MCP Servers |
|--------|--------|----------|-------|--------|-------------|
| superpowers | 14 | 3 (已棄用) | 1 | 1 | 0 |
| double-shot-latte | 0 | 0 | 1 | 0 | 0 |
| elements-of-style | 1 | 0 | 0 | 0 | 0 |
| episodic-memory | 1 | 1 | 1 | 1 | 1 |
| claude-session-driver | 1 | 0 | 5 | 0 | 0 |
| superpowers-chrome | 1 | 0 | 0 | 1 | 1 |
| superpowers-lab | 4 | 0 | 0 | 0 | 0 |
| superpowers-developing-for-claude-code | 2 | 0 | 0 | 0 | 0 |
| **合計** | **24** | **4** | **8** | **3** | **2** |

---

## 推薦安裝優先級

| 優先級 | Plugin | 理由 |
|--------|--------|------|
| 必裝 | **superpowers** | 核心基石，所有開發紀律的基礎 |
| 強烈推薦 | **double-shot-latte** | 大幅減少手動 "continue" 中斷，長任務必備 |
| 推薦 | **superpowers-developing-for-claude-code** | 開發 plugin 的完整參考（你在做 custom-skills 專案） |
| 視需求 | **episodic-memory** | 與 claude-mem 有重疊，看是否需要語義搜尋 |
| 視需求 | **elements-of-style** | 主要用中文時實用性有限 |
| 視需求 | **claude-session-driver** | 已有多種 agent 協調方案 |
| 視需求 | **superpowers-chrome** | 已有 Playwright MCP |
| 觀望 | **superpowers-lab** | 實驗性，v0.3.0 |
| 不推薦 | **superpowers-dev** | 開發版，不穩定 |

---

## Hook 衝突注意事項

多個 plugin 註冊相同 hook 事件時需注意：

| Hook 事件 | 註冊的 Plugin | 潛在衝突 |
|-----------|--------------|---------|
| SessionStart | superpowers, episodic-memory, claude-session-driver | 三者同時觸發，增加啟動延遲 |
| Stop | double-shot-latte, claude-session-driver | double-shot-latte 的自動繼續可能與 session-driver 的事件發送衝突 |
| PreToolUse | claude-session-driver | matcher 為 `*`，攔截所有工具呼叫，影響效能 |

**建議：** 不要同時安裝 double-shot-latte 和 claude-session-driver，除非確認 hook 執行順序不衝突。

---

## 參考資源

- [Superpowers Marketplace GitHub](https://github.com/obra/superpowers-marketplace)
- [Superpowers 核心 GitHub](https://github.com/obra/superpowers)
- [SUPERPOWERS-GUIDE.md](SUPERPOWERS-GUIDE.md) — 技能體系詳解
- [TOOL-DECISION-GUIDE.md](TOOL-DECISION-GUIDE.md) — 本專案工具選擇決策指南

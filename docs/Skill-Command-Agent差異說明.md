---
tags:
  - ai
  - claude-code
  - antigravity
  - dev-stack
date created: 2026-01-14T16:30:00+08:00
date modified: 2026-03-20T03:30:00+08:00
description: AI 開發工具擴充機制完整指南：Skill、Command、Agent 的設計哲學、執行模型、Context 繼承與共享、Agent 三層架構（Subagent / Named Agent / Agent Team）
---

# AI 開發工具擴充機制完整指南

在 Claude Code 等 AI 開發工具中，**Skill**、**Command**、**Agent** 是三種根本不同的擴充機制。它們的差異不僅在功能面，更在於**執行模型**與 **context 繼承方式**的本質不同。

---

## 核心概念：執行模型的根本差異

理解三者差異的關鍵在於：**誰在執行、在哪裡執行**。

```
┌──────────────────────────────────────────────────────────┐
│                    主 Claude 對話                          │
│                                                          │
│  ┌─────────┐  ┌─────────┐                               │
│  │  Skill  │  │ Command │  ← 在主 context 內展開執行     │
│  │ (知識)  │  │ (任務)  │    共享完整對話歷史             │
│  └─────────┘  └─────────┘                               │
│                                                          │
│  Agent(prompt="...")  ──→ spawn ──→ ┌──────────────┐     │
│  Agent(prompt="...")  ──→ spawn ──→ │ 獨立子進程    │     │
│  Agent(prompt="...")  ──→ spawn ──→ │ 隔離 context  │     │
│                                     │ 受限工具      │     │
│                         ← 結果 ──── └──────────────┘     │
└──────────────────────────────────────────────────────────┘
```

- **Skill / Command**：Prompt 展開到主對話，由同一個 Claude 執行。像是「讀了一本手冊後照著做」。
- **Agent**：Spawn 出獨立的 Claude 子進程，有自己的 context window、受限的工具集。像是「派一個人去做事，做完回報」。

---

## 快速比較表

| 特性 | Skill | Command | Agent |
|------|-------|---------|-------|
| **本質** | Prompt 模板（知識注入） | Prompt 模板（任務腳本） | 獨立子進程 |
| **觸發方式** | 自動偵測 + 手動 `/skill` | 僅手動 `/command` | 自動分派或手動呼叫 |
| **執行者** | 主對話中的 AI | 主對話中的 AI | 獨立的子 AI 實例 |
| **上下文** | 共享主對話（看得到所有歷史） | 共享主對話 | 完全隔離（只看到 prompt） |
| **工具權限** | 全部（與主 Claude 相同） | 全部 | 按類型受限 |
| **並行能力** | 不可，順序執行 | 不可 | 可同時跑多個 |
| **Context 消耗** | 佔主 context window | 佔主 context window | 不佔主 context |
| **靈活性** | 高（能依上下文調整） | 高 | 低（只看到給它的 prompt） |
| **典型用例** | 編碼標準、審查清單 | git commit、格式化 | 程式碼審核、並行搜尋 |

---

## Skill（技能）

> 像是：**工作手冊** — 教 AI 怎麼思考與做事

### 定義

Skill 是一組**預定義的行為指引與知識**，展開到主對話的 context 中，讓 AI 在特定情境下採用這些規範。

### 執行模型

```
使用者訊息 → AI 偵測到相關情境 → Skill 內容展開到主 context
→ 同一個 Claude 依據 Skill 指引行動
```

Skill 的核心價值是**上下文感知**——它在主對話裡，能看到完整的對話歷史，因此能做流程決策和複雜判斷。這是 Agent 做不到的。

### 特性

- **自動觸發**：AI 偵測到相關情境時自動載入
- **可手動呼叫**：使用 `/skill-name` 主動觸發
- **純文字結構**：Markdown 檔案，包含指引和範例
- **上下文感知**：能存取完整對話歷史，依情境調整行為

### 適用場景

| 場景 | 範例 |
|------|------|
| 建立行為規範 | 程式碼風格、命名慣例、提交格式 |
| 定義工作流程 | TDD 流程、Code Review 清單、SDD 規格 |
| 注入領域知識 | API 文件、框架使用指南 |
| 流程決策引導 | 需要依上下文判斷下一步該做什麼 |
| 防止常見錯誤 | 反幻覺協議、安全檢查 |

### 實際範例

```markdown
# commit-standards.md

## 提交訊息格式
<type>(<scope>): <subject>

## 類型 (Type)
- `feat`: 新功能
- `fix`: 錯誤修復
- `docs`: 文件更新

## 規則
- 主題行最多 72 字元
- 使用祈使語氣
```

**使用情境**：
- 輸入 `git commit` 相關指令時，AI 自動參考此 Skill
- 手動呼叫 `/commit-standards` 查看規範

---

## Command（命令）

> 像是：**巨集指令** — 一鍵執行標準化操作

### 定義

Command 是一個**可重複執行的特定任務腳本**，透過 `/command-name` 觸發。與 Skill 同樣在主 context 中執行，但定位不同——Skill 關注「怎麼做」，Command 關注「做什麼」。

### 執行模型

```
使用者輸入 /command → 展開 prompt 到主 context → 同一個 Claude 執行任務
```

### 特性

- **僅手動觸發**：必須用 `/command` 呼叫
- **支援參數**：使用 `$ARGUMENTS` 接收輸入
- **任務導向**：執行具體、明確的操作
- **可組合**：可以引用 Skill 的規範、呼叫其他工具

### Skill 與 Command 的區別

| | Skill | Command |
|---|---|---|
| 回答的問題 | AI **怎麼做**（how） | 使用者**做什麼**（what） |
| 觸發方式 | 自動 + 手動 | 僅手動 |
| 執行頻率 | 持續影響行為 | 一次性執行 |
| 類比 | 內化的知識 | 可執行的按鈕 |

### 適用場景

| 場景 | 範例 |
|------|------|
| 自動化重複任務 | git commit、部署流程 |
| 標準化操作 | PR 建立、程式碼審查 |
| 快捷指令 | 查詢特定 API、生成模板 |
| 帶參數的操作 | 比較分支差異、搜尋關鍵字 |

### 實際範例

```markdown
# git-commit.md

請執行以下步驟：
1. 執行 `git status` 檢查變更
2. 執行 `git diff --staged` 查看已暫存的變更
3. 根據變更內容，依照 commit-standards Skill 撰寫提交訊息
4. 執行 `git commit`
5. 顯示提交結果
```

```shell
/git-commit
```

---

## Agent（代理）

> 像是：**專業團隊成員** — 獨立工作，完成後回報

### 定義

Agent 是一個**獨立運行的 AI 子進程**，擁有自己的 context window 和受限的工具集。與 Skill/Command 的根本差異在於：Agent 不在主對話中執行，而是被 spawn 成獨立的子進程。

### 執行模型

```
主 Claude ──→ spawn Agent(prompt="分析 auth 模組")
                  │
                  ↓ 獨立的 context window
                  ↓ 受限的工具集
                  ↓ 看不到主對話歷史
                  │
              ← 回傳結果（文字摘要）
```

### Agent 解決了什麼問題？

Skill 更靈活，但 Agent 解決了 Skill **根本做不到**的三件事：

| 能力 | 為什麼 Skill 做不到 |
|------|---------------------|
| **並行執行** | 同時 spawn 3 個 Agent 做不同的事；Skill 只能順序執行 |
| **Context 保護** | Agent 讀了 500 行程式碼，只回傳 10 行結論；用 Skill 那 500 行會直接灌進主 context |
| **工具隔離** | code-reviewer Agent 物理上沒有 Edit 工具，不可能改你的檔案；Skill 只能靠 prompt 約束 |

### Agent 的三層架構

Agent 不只是一種東西——它有三個演進層級：

```
Subagent (基本)          Named Agent (可定址)        Agent Team (協作)
┌─────────────┐         ┌─────────────┐            ┌──────────────────────┐
│ 做完就消亡   │         │ 有名字       │            │ Team Lead（主 Claude）│
│ 不能追問     │         │ 可以追問     │            │  ├─ researcher        │
│ 單向通訊     │         │ 雙向通訊     │            │  ├─ implementer       │
└─────────────┘         └─────────────┘            │  └─ tester            │
                                                    │ 共享 TaskList         │
                                                    │ 互相 SendMessage      │
                                                    └──────────────────────┘
```

#### 1. Subagent（基本款）— Fire-and-Forget

```python
Agent(prompt="搜尋所有用到 auth 的檔案")
# → 執行 → 回傳結果 → 消亡
# 你不能再追問它「那 session 呢？」
```

- 一個任務 → 一個結果 → 結束
- 父→子單向通訊
- 最常見的使用方式

#### 2. Named Agent（可定址）— 可持續對話的顧問

```python
Agent(name="researcher", prompt="調查 auth 模組架構")
# researcher 回傳結果後進入 idle...

# 之後可以繼續追問：
SendMessage(to="researcher", message="那 session 管理呢？")
# researcher 醒來，帶著之前的 context 繼續工作
```

- 有名字 → 可用 `SendMessage` 再次喚醒
- 保留完整 context，記得之前做了什麼
- 本質是「持久化的 Subagent」

#### 3. Agent Team（團隊）— 多 Agent 自主協作

```python
TeamCreate(team_name="feature-x")

# 建立共享任務清單
TaskCreate(title="研究現有 API",  owner="researcher")
TaskCreate(title="實作新端點",    owner="implementer", blocked_by=[1])
TaskCreate(title="寫整合測試",    owner="tester",      blocked_by=[2])

# Spawn 隊員
Agent(team_name="feature-x", name="researcher",   ...)
Agent(team_name="feature-x", name="implementer",  ...)
Agent(team_name="feature-x", name="tester",       ...)
```

Team 帶來的全新能力：

| 能力 | Subagent | Named Agent | Agent Team |
|------|----------|-------------|------------|
| 執行任務 | 一次性 | 可持續 | 可持續 |
| 父↔子通訊 | 單向 | 雙向 | 雙向 |
| **子↔子通訊** | 不可 | 不可 | **可以** |
| **共享任務清單** | 不可 | 不可 | **TaskList** |
| **任務依賴/阻塞** | 不可 | 不可 | **blocked_by** |
| Idle 管理 | 不適用 | 手動 | **自動通知** |
| 協調模式 | Hub-spoke | Hub-spoke | **Mesh** |

### Agent 的工具限制

不同類型的 Agent 擁有不同的工具集，這是**硬性限制**而非 prompt 約束：

| Agent 類型 | 可用工具 | 特點 |
|-----------|---------|------|
| `general-purpose` | 全部 | 最靈活，什麼都能做 |
| `code-reviewer` | Read, Grep, Glob, Bash | 唯讀，物理上不能改檔案 |
| `reviewer` | 全部 | 可以審查也可以修改 |
| `Explore` | 全部（除 Edit, Write） | 快速搜尋，不能修改 |
| `Plan` | 全部（除 Edit, Write） | 規劃設計，不能修改 |

### 適用場景

| 場景 | 推薦的 Agent 層級 |
|------|-------------------|
| 搜尋程式碼、蒐集資料 | **Subagent** — 簡單的 fire-and-forget |
| 並行處理多個獨立任務 | **多個 Subagent** — 同時 spawn |
| 需要多輪交互的調查 | **Named Agent** — 可追問 |
| 跨領域的複雜專案 | **Agent Team** — 成員各司其職 |

### 實際範例

```markdown
# code-reviewer.md

你是程式碼審核專家。

## 職責
- 分析程式碼品質
- 找出潛在的 Bug
- 檢查安全漏洞
- 標注嚴重程度（Critical / Major / Minor）

## 輸出格式
### 審核摘要
- 總變更數：X 個檔案
- 問題數：Critical: X, Major: X, Minor: X

### 詳細問題
#### [Critical] 檔案名稱:行數
問題描述...
建議修改...
```

---

## Context 繼承與共享

理解各機制的 context 行為是正確使用它們的關鍵。核心問題是：**誰看得到什麼、資訊往哪個方向流動**。

### Context 流向全覽

```
┌───────────────────────────────────────────────────────────────┐
│                       主 Claude 對話                            │
│  [使用者訊息] [工具結果] [Skill 展開] [Command 展開] ...       │
│  ──────────────────────────────────────────────────           │
│  ↑ 全部可見、全部共享、雙向影響                                │
│                                                               │
│  向下傳遞給 Agent 的只有：你寫的那段 prompt                    │
│                           ↓                                   │
│              ┌────────────┼────────────┐                      │
│              ↓            ↓            ↓                      │
│         Subagent A   Named Agent B   Named Agent C            │
│         [只有 prompt] [prompt + 自   [prompt + 自              │
│                        己的對話歷史]   己的對話歷史]             │
│                                                               │
│  向上回傳的只有：最終結果摘要（Agent 內部過程全部丟棄）          │
└───────────────────────────────────────────────────────────────┘
```

### 各機制的 Context 行為

#### Skill & Command — 完全融合

```
主 context: [A] [B] [C] [Skill 內容展開] [D] [E]
                         ↑
                    變成 context 的一部分
                    看得到 A B C，之後的 D E 也看得到它
```

- **繼承**：完整繼承主對話所有內容
- **共享**：雙向——Skill/Command 看得到一切，主 Claude 也看得到 Skill/Command 的所有指引
- **代價**：佔用主 context window 額度

#### Subagent — 完全隔離

```
主 context:  [A] [B] [C] ── prompt ──→  Agent context: [prompt]
                          ←── 結果 ───  （內部推理、工具呼叫全部丟棄）
```

| 方向 | 傳了什麼 | 沒傳什麼 |
|------|---------|---------|
| **↓ 父→子** | 你寫的 prompt 字串 | 對話歷史、之前的工具結果、Skill 內容 |
| **↑ 子→父** | 最終回傳的結果文字 | 中間的推理過程、工具呼叫記錄、讀過的檔案內容 |

這就是 **context 保護**的原理——Agent 內部讀了 500 行程式碼做分析，但主 context 只收到 10 行結論。那 500 行隨著 Agent 消亡而消失。

#### Named Agent — 隔離但可累積

```
第一次：  主 ── prompt ──→  Agent: [prompt]
              ←── 結果 ───

第二次：  主 ── message ──→ Agent: [prompt] [結果] [message]
              ←── 結果 ───                  ↑
                                      它記得第一次做了什麼

第三次：  主 ── message ──→ Agent: [prompt] [結果] [message] [結果] [message]
              ←── 結果 ───
```

| 方向 | 行為 |
|------|------|
| **↓ 父→子** | 每次 `SendMessage` 追加到 Agent 自己的 context |
| **↑ 子→父** | 每次只回傳該輪結果 |
| **Agent 內部** | 累積所有互動歷史——它記得之前做了什麼 |
| **父看到的** | 只有每次回傳的結果，看不到 Agent 內部的完整推理 |

關鍵：**Agent 的 context 是單向累積的**——主 Claude 給它的訊息會持續累積，但主 Claude 不會看到 Agent 內部的完整歷史。

#### Agent Team — 隔離 + 訊息傳遞

```
                    ┌─── Team Lead（主 Claude）───┐
                    │                              │
              SendMessage                    SendMessage
                    │                              │
                    ↓                              ↓
            Agent A context:               Agent B context:
            [initial prompt]               [initial prompt]
            [Lead 的訊息]                  [Lead 的訊息]
            [B 的訊息]  ←─ SendMessage ──→ [A 的訊息]
            [自己的工具結果]                [自己的工具結果]
                    │                              │
                    └──── 共享 TaskList（檔案）─────┘
```

| 通訊路徑 | 傳遞的 context | 機制 |
|----------|---------------|------|
| Lead → 成員 | Lead 寫的訊息文字 | `SendMessage` |
| 成員 → Lead | 成員的回覆文字 + idle 通知 | `SendMessage`（自動送達） |
| **成員 ↔ 成員** | **彼此的訊息文字（完整內容）** | **`SendMessage`（直接 DM）** |
| 全體共享 | 任務狀態、負責人 | `TaskList`（檔案系統） |
| Lead 可見 | 成員間 DM 的**摘要** | idle 通知中附帶 |

重點：成員之間的 DM 是**完整內容**互傳，但 Team Lead 只看到**摘要**。

### Context 行為對比表

| | Skill | Command | Subagent | Named Agent | Agent Team 成員 |
|--|-------|---------|----------|-------------|----------------|
| **看到主對話歷史？** | 全部 | 全部 | 否 | 否 | 否 |
| **看到其他 Skill/Command？** | 是 | 是 | 否 | 否 | 否 |
| **主 Claude 看到它的內部？** | 是（同一 context） | 是 | 只看到結果 | 只看到每輪結果 | 回覆 + DM 摘要 |
| **有跨輪記憶？** | 不（靠主 context） | 不 | 不（一次性） | 有（自己累積） | 有（自己累積） |
| **能跟同層溝通？** | 自然（同一 context） | 自然 | 不可 | 不可 | 可（`SendMessage`） |
| **Context 存活時間** | 主對話結束 | 主對話結束 | 任務完成即消亡 | 直到關閉 | 直到 shutdown |
| **消耗主 context？** | 是 | 是 | 否（只有結果） | 否（只有結果） | 否（只有結果 + 摘要） |

### 實務指南：什麼時候該在乎 Context？

| 遇到的問題 | 根本原因 | 解法 |
|-----------|---------|------|
| Agent 不知道前面討論了什麼 | Subagent 看不到主對話 | 在 prompt 裡手動附上必要的背景資訊 |
| Agent 回傳的資訊太少 | 主 Claude 看不到 Agent 內部 | 在 prompt 裡明確要求 Agent 詳細回報 |
| 主 context 快爆了 | Skill 和工具結果佔太多空間 | 改用 Agent，把大量讀取隔離出去 |
| 多個 Agent 各做各的、重複工作 | Subagent 之間看不到彼此 | 用 Named Agent + `SendMessage`，或 Agent Team |
| Agent 每次都從零開始 | Subagent 沒有跨輪記憶 | 改用 Named Agent，保持 context 累積 |
| Team 成員不知道彼此的進度 | 預設 context 隔離 | 善用 TaskList 共享狀態 + `SendMessage` 同步關鍵發現 |

---

## 如何選擇？決策流程圖

```
                      你需要什麼？
                           │
            ┌──────────────┼──────────────┐
            ↓              ↓              ↓
      規範 AI 行為？   執行特定任務？   獨立 / 並行處理？
            │              │              │
            ↓              ↓              ↓
         Skill          Command         Agent
                                          │
                          ┌───────────────┼───────────────┐
                          ↓               ↓               ↓
                    一次性任務？      需要追問？      多人協作？
                          │               │               │
                          ↓               ↓               ↓
                     Subagent       Named Agent      Agent Team
```

### 決策指南

| 你的需求 | 選擇 | 原因 |
|----------|------|------|
| AI 每次都遵循某種規範 | **Skill** | 自動注入，持續影響行為 |
| 一鍵執行標準化操作 | **Command** | 任務導向，支援參數 |
| 需要上下文感知的流程判斷 | **Skill** | 能看到完整對話歷史 |
| 需要深度分析或專業判斷 | **Agent** | 獨立思考，不汙染主 context |
| 同時處理多個獨立任務 | **Agent** | 可並行執行 |
| 保護主 context 不被大量資料淹沒 | **Agent** | 隔離 context，只回傳摘要 |
| 限制 AI 只能讀不能改 | **Agent** | 工具硬性限制 |
| 多個角色需要互相溝通協作 | **Agent Team** | 子↔子通訊 + 共享任務清單 |

### 一句話經驗法則

> - 在想「AI **應該怎麼做**」→ **Skill**（教它方法）
> - 在想「我要**執行什麼**」→ **Command**（給它按鈕）
> - 在想「我需要**派人去做**」→ **Agent**（委託工作）

---

## 組合使用：最強模式

三者的最佳實踐是**組合使用**——Skill 定義策略，Command 觸發流程，Agent 執行戰術。

```
Skill 定義策略       Command 觸發流程        Agent 執行戰術
      │                    │                      │
      ↓                    ↓                      ↓
「怎麼做」           「做什麼」             「誰去做」
  (how)               (what)                (who)
```

### 範例：完整的 Code Review 流程

```
使用者：幫我 review feature-branch

    │
    ↓ 主 AI 分析任務
    │
    ↓ 觸發 code-review-assistant Skill（注入審查標準 — HOW）
    │
    ↓ 分派 code-reviewer Agent（執行深度分析 — WHO）
    │   同時分派 security-reviewer Agent（安全審計 — WHO）
    │          ↑ 並行執行，互不干擾
    ↓
    ↓ Agent 完成後，主 AI 整合結果
    │
    ↓ 使用者確認後，執行 /git-commit Command（提交修改 — WHAT）
```

### 範例：大型功能開發（Agent Team）

```
1. /openspec:proposal 新增用戶登入功能
   → 觸發 spec-driven-dev Skill（定義流程）

2. AI 規劃並建立 proposal
   → TeamCreate(team_name="auth-feature")

3. 分派任務給 Team 成員
   → researcher:   調查現有 auth 架構
   → implementer:  依序實作各端點
   → tester:       撰寫測試案例
   → 成員之間透過 SendMessage 協調

4. 主 Claude 整合所有成果

5. /git-commit 完成提交
```

---

## 各工具的配置位置

### Claude Code

| 類型 | 用戶級別 | 專案級別 |
|------|----------|----------|
| Skill | `~/.claude/skills/<name>/` | `.claude/skills/<name>/` |
| Command | `~/.claude/commands/<name>.md` | `.claude/commands/<name>.md` |
| Agent | `~/.claude/.agent/<name>.md` | `.claude/.agent/<name>.md` |

### Antigravity

| 類型 | 用戶級別 | 專案級別 |
|------|----------|----------|
| Skill | `~/.gemini/antigravity/skills/<name>/` | `.agent/skills/<name>/` |
| Workflow | `~/.gemini/antigravity/global_workflows/` | `.agent/workflows/` |
| Prompt | `~/.gemini/GEMINI.md` | `.agent/*.md` |

### OpenCode

| 類型 | 用戶級別 | 專案級別 |
|------|----------|----------|
| Skill | `~/.claude/skills/<name>/`（共用 Claude Code） | `.opencode/skills/<name>/` |
| Command | `~/.claude/commands/<name>.md`（共用 Claude Code） | `.opencode/commands/<name>.md` |
| Agent | `~/.config/opencode/agent/<name>.md` | `.opencode/agent/<name>.md` |

### Codex

| 類型 | 用戶級別 | 專案級別 |
|------|----------|----------|
| Skill | `~/.codex/skills/<name>/` | `.codex/skills/<name>/` |

### Gemini CLI

| 類型 | 用戶級別 | 專案級別 |
|------|----------|----------|
| Skill | `~/.gemini/skills/<name>/` | N/A |
| Command | `~/.gemini/commands/<name>.md` | N/A |

### 統一管理目錄（custom-skills）

| 類型 | 路徑 |
|------|------|
| Skill | `~/.config/custom-skills/skills/<name>/` |
| Command | `~/.config/custom-skills/commands/<tool>/<name>.md` |
| Agent | `~/.config/custom-skills/agents/<tool>/<name>.md` |
| ECC 資源 | `~/.config/custom-skills/sources/ecc/` |

---

## 總結

| | Skill | Command | Subagent | Named Agent | Agent Team |
|--|-------|---------|----------|-------------|------------|
| 像是 | 工作手冊 | 巨集指令 | 跑腿的 | 顧問 | 專案團隊 |
| 執行在 | 主 context | 主 context | 獨立進程 | 獨立進程 | 多個獨立進程 |
| 何時用 | 規範行為 | 執行任務 | 一次性工作 | 多輪調查 | 跨領域協作 |
| 觸發 | 自動 + 手動 | 僅手動 | 手動/自動 | 手動/自動 | 手動建立 |
| 並行 | 不可 | 不可 | 可 | 可 | 可 + 互通 |
| 對話感知 | 完整 | 完整 | 無 | 自己的歷史 | 自己的 + 隊友訊息 |

---

## 附錄：內建 Agents 清單

### 核心 Agent 類型

| Agent 類型 | 工具權限 | 定位 |
|-----------|---------|------|
| `general-purpose` | 全部 | 通用型，研究與執行皆可 |
| `Explore` | 唯讀（無 Edit/Write） | 快速程式碼探索 |
| `Plan` | 唯讀（無 Edit/Write） | 架構設計與規劃 |
| `code-reviewer` | Read, Grep, Glob, Bash | 程式碼審查（強制唯讀） |
| `reviewer` | 全部 | 審查 + 可修改 |

### 語言專屬 Agents

| Agent | 說明 |
|-------|------|
| `python-reviewer` | PEP 8、型別提示、安全性 |
| `rust-reviewer` | 所有權、生命週期、unsafe |
| `go-reviewer` | 慣用 Go、並行模式、錯誤處理 |
| `java-reviewer` | 分層架構、JPA、Spring Boot |
| `kotlin-reviewer` | 慣用 Kotlin、協程安全、Compose |
| `cpp-reviewer` | 記憶體安全、現代 C++、並行 |

### Build 修復 Agents

| Agent | 說明 |
|-------|------|
| `build-error-resolver` | TypeScript 建置錯誤 |
| `rust-build-resolver` | Cargo 建置與借用檢查器 |
| `go-build-resolver` | Go build/vet/linter |
| `java-build-resolver` | Maven/Gradle 建置 |
| `kotlin-build-resolver` | Kotlin/Gradle 建置 |
| `cpp-build-resolver` | C++/CMake 建置 |

### 專業領域 Agents

| Agent | 說明 |
|-------|------|
| `security-reviewer` | OWASP 安全漏洞掃描 |
| `database-reviewer` | PostgreSQL 查詢最佳化與 schema 設計 |
| `e2e-runner` | Playwright E2E 測試執行 |
| `doc-updater` | 文件與 Codemap 產生 |
| `planner` | 複雜功能規劃 |
| `architect` | 系統架構設計 |
| `refactor-cleaner` | Dead code 清理與合併 |
| `harness-optimizer` | Agent harness 配置最佳化 |

> 詳細說明請參考 `agents/claude/README.md`

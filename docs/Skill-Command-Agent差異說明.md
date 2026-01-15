---
tags:
  - ai
  - claude-code
  - antigravity
  - dev-stack
date created: 2026-01-14T16:30:00+08:00
date modified: 2026-01-14T16:30:00+08:00
description: 說明 AI 開發工具中 Skill、Command、Agent 的差異與使用時機
---

# Skill、Command、Agent 差異說明

在 Claude Code 和 Antigravity 等 AI 開發工具中，**Skill**、**Command**、**Agent** 是三種不同的擴充機制。本文說明它們的差異、適用場景，並提供實際範例。

---

## 快速比較表

| 特性       | Skill       | Command            | Agent        |
| -------- | ----------- | ------------------ | ------------ |
| **觸發方式** | 自動偵測 + 手動呼叫 | 僅手動呼叫 (`/command`) | 自動分派或手動呼叫    |
| **主要用途** | 行為規範、知識注入   | 執行特定任務             | 複雜任務的子處理     |
| **執行者**  | 主對話中的 AI    | 主對話中的 AI           | 獨立的子 AI 實例   |
| **上下文**  | 共享主對話上下文    | 共享主對話上下文           | 獨立上下文（可傳遞部分） |
| **複雜度**  | 低（純文字指引）    | 中（可帶參數）            | 高（獨立思考流程）    |
| **典型用例** | 編碼標準、審查清單   | git commit、程式碼格式化  | 程式碼審核、天氣查詢   |

---

## Skill（技能）

### 定義

Skill 是一組**預定義的行為指引與知識**，讓 AI 在特定情境下自動採用這些規範。可以把 Skill 想像成「AI 的工作手冊」。

### 特性

- **自動觸發**：AI 偵測到相關情境時自動載入
- **可手動呼叫**：使用 `/skill-name` 主動觸發
- **純文字結構**：通常是 Markdown 檔案，包含指引和範例
- **無狀態**：每次觸發都是獨立的

### 目錄結構

```
~/.claude/skills/
└── commit-standards/
    └── commit-standards.md

~/.gemini/antigravity/skills/
└── commit-standards/
    └── commit-standards.md
```

### 適用場景

| 場景 | 範例 |
|------|------|
| 建立編碼規範 | 程式碼風格、命名慣例 |
| 定義工作流程 | TDD 流程、Code Review 清單 |
| 注入領域知識 | API 文件、框架使用指南 |
| 防止常見錯誤 | 反幻覺協議、安全檢查 |

### 實際範例：commit-standards
```markdown
# commit-standards.md

## 提交訊息格式
\```
<type>(<scope>): <subject>

<body>

<footer>
\```

## 類型 (Type)
- `feat`: 新功能
- `fix`: 錯誤修復
- `docs`: 文件更新
- `refactor`: 重構

## 規則
- 主題行最多 72 字元
- 使用祈使語氣：「add」而非「added」
```

**使用情境**：
- 當你輸入 `git commit` 相關指令時，AI 會自動參考此 Skill
- 也可手動呼叫 `/commit-standards` 查看規範

---

## Command（命令）

### 定義

Command 是一個**可重複執行的特定任務腳本**，透過 `/command-name` 觸發。可以把 Command 想像成「AI 的巨集指令」。

### 特性

- **僅手動觸發**：必須用 `/command` 呼叫
- **支援參數**：使用 `$ARGUMENTS` 接收輸入
- **任務導向**：執行具體、明確的操作
- **可組合**：可以呼叫其他工具或 Skill

### 目錄結構

```
~/.claude/commands/
└── code_review.md

# 專案級別
project/.claude/commands/
└── deploy.md
```

### 適用場景

| 場景 | 範例 |
|------|------|
| 自動化重複任務 | git commit、部署流程 |
| 標準化操作 | PR 建立、程式碼審查 |
| 快捷指令 | 查詢特定 API、生成模板 |
| 帶參數的操作 | 比較分支差異、搜尋關鍵字 |

### 實際範例：code_review

```markdown
# code_review.md

對比分支 `$ARGUMENTS` 與 `main` 分支的差異，並提出你的 review 意見。

請檢查以下項目：
1. 程式碼風格是否一致
2. 是否有潛在的安全漏洞
3. 測試覆蓋率是否足夠
4. 是否有效能問題
```

**使用方式**：

```shell
# 注意：參數前要有兩個空格
/code_review  dev-feature

# 或者帶說明
/code_review 請幫我審查 dev-feature
```

### 實際範例：git-commit

```markdown
# git-commit.md

請執行以下步驟：

1. 執行 `git status` 檢查變更
2. 執行 `git diff --staged` 查看已暫存的變更
3. 根據變更內容，依照 commit-standards Skill 撰寫提交訊息
4. 執行 `git commit`
5. 顯示提交結果
```

**使用方式**：

```shell
/git-commit
```

---

## Agent（代理）

### 定義

Agent 是一個**獨立運行的 AI 子實例**，專門處理特定類型的複雜任務。可以把 Agent 想像成「AI 的專業團隊成員」。

### 特性

- **獨立上下文**：有自己的對話歷史和思考流程
- **專業分工**：每個 Agent 專注於特定領域
- **自動分派**：主 AI 可根據任務自動選擇合適的 Agent
- **並行處理**：可同時執行多個 Agent

### 目錄結構

```
~/.claude/.agent/
└── code-reviewer.md

# 專案級別
project/.claude/.agent/
└── security-auditor.md
```

### 適用場景

| 場景 | 範例 |
|------|------|
| 需要專業知識 | 安全審計、效能分析 |
| 複雜多步驟任務 | 完整的 Code Review 流程 |
| 需要獨立思考 | 架構設計、問題診斷 |
| 並行處理 | 同時審查多個檔案 |

### 實際範例：程式碼審核 Agent

```markdown
# code-reviewer.md

你是程式碼審核專家。

## 你的職責
- 分析程式碼品質
- 找出潛在的 Bug
- 建議改進方案
- 檢查安全漏洞

## 審核流程
1. 先理解程式碼的整體架構
2. 逐一檢查每個變更
3. 標注問題的嚴重程度（Critical / Major / Minor）
4. 提供具體的修改建議

## 輸出格式
```
### 審核摘要
- 總變更數：X 個檔案
- 問題數：Critical: X, Major: X, Minor: X

### 詳細問題
#### [Critical] 檔案名稱:行數
問題描述...
建議修改...
```
```

**使用方式**：

```shell
# 查看可用的 Agents
/agents

# 模型會自動分派給合適的 Agent
幫我 code review dev-feature 這個分支
```

### 實際範例：並行 Agent

```shell
# 一個問題觸發多個 Agent
幫我 code review dev-feature 這個分支，還有今天高雄天氣如何。
```

此時主 AI 會：
1. 將 code review 任務分派給「程式碼審核 Agent」
2. 將天氣查詢分派給「天氣預報 Agent」
3. 整合兩者的結果回覆

---

## 如何選擇？決策流程圖

```
                    你需要什麼？
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
    持續的行為規範？   執行特定任務？   複雜的專業任務？
          │              │              │
          ↓              ↓              ↓
       Skill          Command         Agent
```

### 詳細決策指南

| 你的需求 | 選擇 | 原因 |
|----------|------|------|
| 希望 AI 每次都遵循某種規範 | **Skill** | Skill 會自動注入，不需每次呼叫 |
| 需要快速執行一個標準化操作 | **Command** | Command 是任務導向，一鍵完成 |
| 任務需要深度分析或專業判斷 | **Agent** | Agent 有獨立思考能力 |
| 想要傳遞參數執行不同操作 | **Command** | Command 支援 `$ARGUMENTS` |
| 需要同時處理多個獨立任務 | **Agent** | Agent 可並行執行 |
| 定義程式碼風格或提交格式 | **Skill** | 這是行為規範，適合 Skill |
| 一鍵完成 git commit 流程 | **Command** | 這是具體任務，適合 Command |
| 完整審查一個 PR | **Agent** | 需要專業分析，適合 Agent |

---

## 組合使用範例

實務上，這三者常常組合使用：

### 範例：完整的 Code Review 流程

```
使用者：幫我 review feature-branch

    │
    ↓ 主 AI 分析任務
    │
    ↓ 觸發 code-review-assistant Skill（注入審查標準）
    │
    ↓ 分派給 code-reviewer Agent（執行深度分析）
    │
    ↓ Agent 完成後，主 AI 整合結果
    │
    ↓ 使用者確認後，執行 /git-commit Command（提交修改）
```

### 範例：新功能開發流程

```
1. /openspec:proposal 新增用戶登入功能
   → 觸發 spec-driven-dev Skill

2. AI 規劃並建立 proposal
   → 可能使用 planning Agent

3. /openspec:apply add-user-login
   → 觸發 testing-guide Skill（確保測試）
   → 觸發 commit-standards Skill（規範提交）

4. /code_review  main
   → 分派給 code-reviewer Agent

5. /git-commit
   → 執行 Command 完成提交
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

---

## 總結

| 記住這個 | Skill | Command | Agent |
|----------|-------|---------|-------|
| 像是... | 工作手冊 | 巨集指令 | 專業團隊成員 |
| 何時用 | 規範行為 | 執行任務 | 深度分析 |
| 觸發 | 自動 + 手動 | 僅手動 | 自動分派 + 手動 |
| 複雜度 | 簡單 | 中等 | 複雜 |

**經驗法則**：
- 如果你在想「AI 應該怎麼做」→ 用 **Skill**
- 如果你在想「我要執行什麼」→ 用 **Command**
- 如果你在想「我需要專家幫忙」→ 用 **Agent**

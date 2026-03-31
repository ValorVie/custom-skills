# Codex Plugin for Claude Code 完整指南

> 在 Claude Code 中直接使用 OpenAI Codex 進行 code review 或委派任務，實現跨 AI 工具協作。

**來源**：[openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc)
**版本**：1.0.0（2026-03-30 發布）
**授權**：Apache-2.0
**作者**：OpenAI

---

## 目錄

- [概述](#概述)
- [前置需求](#前置需求)
- [安裝流程](#安裝流程)
- [初始設定](#初始設定)
- [指令總覽](#指令總覽)
- [指令詳解](#指令詳解)
  - [codex:review — 標準 Code Review](#codexreview--標準-code-review)
  - [codex:adversarial-review — 挑戰式 Review](#codexadversarial-review--挑戰式-review)
  - [codex:rescue — 委派任務](#codexrescue--委派任務)
  - [codex:status — 查看任務狀態](#codexstatus--查看任務狀態)
  - [codex:result — 取得任務結果](#codexresult--取得任務結果)
  - [codex:cancel — 取消任務](#codexcancel--取消任務)
  - [codex:setup — 環境檢查與設定](#codexsetup--環境檢查與設定)
- [Subagent：codex-rescue](#subagentcodex-rescue)
- [Review Gate（審查門檻）](#review-gate審查門檻)
- [內建 Skills](#內建-skills)
- [Codex 設定整合](#codex-設定整合)
- [典型工作流程](#典型工作流程)
- [架構與技術細節](#架構與技術細節)
- [常見問題](#常見問題)
- [與現有 CODEX-GUIDE 的關係](#與現有-codex-guide-的關係)
- [故障排除](#故障排除)

---

## 概述

`codex-plugin-cc` 是 OpenAI 官方開發的 **Claude Code 插件**，讓你在 Claude Code 的工作流程中直接呼叫 Codex（OpenAI 的 coding agent）。它不是一個獨立工具，而是 Claude Code 的擴展模組。

### 核心價值

| 面向 | 說明 |
|------|------|
| **跨 AI 審查** | 用 Codex（GPT-5.4）對 Claude 的產出做獨立 code review |
| **任務委派** | 將 bug 調查、修復等任務委託給 Codex 在背景執行 |
| **挑戰式審查** | 讓 Codex 挑戰你的設計決策、架構選擇和隱含假設 |
| **審查門檻** | 可選功能：Claude 回應前先過 Codex 品質檢查 |

### 這個插件適合誰？

- 已在使用 Claude Code，想要增加一層獨立審查
- 想讓兩個不同 AI（Claude + Codex）互相質疑設計決策
- 需要把耗時任務委派給 Codex 在背景執行
- 想實驗跨 AI 協作工作流程

---

## 前置需求

| 項目 | 要求 | 備註 |
|------|------|------|
| **Claude Code** | 已安裝並可正常使用 | 需支援插件系統 |
| **Node.js** | >= 18.18.0 | 插件運行所需 |
| **ChatGPT 帳號或 OpenAI API Key** | 免費方案即可 | 用量計入 Codex 使用額度 |
| **Codex CLI** | 全域安裝 | 插件可協助安裝 |

> **額度提醒**：使用此插件會消耗 Codex 的使用額度。詳見 [Codex Pricing](https://developers.openai.com/codex/pricing)。

---

## 安裝流程

### 第一步：新增 Marketplace

在 Claude Code 中執行：

```bash
/plugin marketplace add openai/codex-plugin-cc
```

### 第二步：安裝插件

```bash
/plugin install codex@openai-codex
```

### 第三步：重新載入插件

```bash
/reload-plugins
```

### 第四步：執行初始設定

```bash
/codex:setup
```

此指令會自動檢查：
- Codex CLI 是否已安裝
- 認證狀態是否正常
- 若 Codex 未安裝且 npm 可用，會提議自動安裝

### 手動安裝 Codex CLI（如需）

```bash
npm install -g @openai/codex
```

### Codex 登入（如未登入）

在 Claude Code 中以 `!` 前綴執行（讓指令在當前 session 中運行）：

```bash
!codex login
```

### 驗證安裝

安裝成功後，你應該能看到：

- 以下 slash commands 出現在指令清單中：
  - `/codex:review`
  - `/codex:adversarial-review`
  - `/codex:rescue`
  - `/codex:status`
  - `/codex:result`
  - `/codex:cancel`
  - `/codex:setup`
- `codex:codex-rescue` 出現在 `/agents` 中

### 快速測試

```bash
/codex:review --background
/codex:status
/codex:result
```

---

## 初始設定

### 基本設定

`/codex:setup` 是一站式設定指令，功能包括：

1. **環境檢查**：確認 Codex CLI 是否安裝、版本是否足夠
2. **認證檢查**：確認是否已登入（ChatGPT 帳號或 API Key）
3. **自動安裝**：若 Codex 未安裝，可提議透過 npm 安裝
4. **Review Gate 管理**：開啟或關閉審查門檻功能

### 啟用 / 停用 Review Gate

```bash
# 啟用
/codex:setup --enable-review-gate

# 停用
/codex:setup --disable-review-gate
```

> **警告**：Review Gate 可能產生 Claude ↔ Codex 長時間循環，快速消耗使用額度。僅在主動監控 session 時啟用。

---

## 指令總覽

| 指令 | 用途 | 唯讀？ | 支援背景？ |
|------|------|--------|------------|
| `/codex:review` | 標準 code review | 是 | 是 |
| `/codex:adversarial-review` | 挑戰式設計審查 | 是 | 是 |
| `/codex:rescue` | 委派任務給 Codex | 否（可寫入） | 是 |
| `/codex:status` | 查看任務狀態 | 是 | — |
| `/codex:result` | 取得完成結果 | 是 | — |
| `/codex:cancel` | 取消背景任務 | 是 | — |
| `/codex:setup` | 環境檢查與設定 | 是 | — |

---

## 指令詳解

### `/codex:review` — 標準 Code Review

對當前工作做標準的 Codex code review，等同於在 Codex 中直接執行 `/review`。

#### 語法

```bash
/codex:review [--wait|--background] [--base <ref>] [--scope auto|working-tree|branch]
```

#### 參數

| 參數 | 說明 |
|------|------|
| `--wait` | 在前台等待結果 |
| `--background` | 在背景執行 |
| `--base <ref>` | 指定比較基準（如 `main`、`develop`），做分支 review |
| `--scope` | 審查範圍：`auto`（自動判斷）、`working-tree`（工作目錄）、`branch`（分支差異） |

#### 使用範例

```bash
# 審查當前未提交的變更
/codex:review

# 審查當前分支相對於 main 的所有變更
/codex:review --base main

# 在背景執行（建議多檔案變更時使用）
/codex:review --background

# 審查分支差異並在前台等待
/codex:review --base main --wait
```

#### 行為說明

- **純唯讀**：不會修改任何檔案，不會提出修補
- **自動判斷執行模式**：若未指定 `--wait` 或 `--background`，會先估算審查規模：
  - 1-2 個檔案且無目錄級變更 → 建議前台等待
  - 其他情況（包括不確定）→ 建議背景執行
- **不可自訂 focus text**：若需要自訂審查重點，改用 `/codex:adversarial-review`

#### Review 輸出結構

Codex review 結果遵循結構化 JSON schema：

```json
{
  "verdict": "approve | needs-attention",
  "summary": "審查摘要",
  "findings": [
    {
      "severity": "critical | high | medium | low",
      "title": "發現標題",
      "body": "詳細說明",
      "file": "檔案路徑",
      "line_start": 10,
      "line_end": 25,
      "confidence": 0.95,
      "recommendation": "建議修正方式"
    }
  ],
  "next_steps": ["下一步建議"]
}
```

---

### `/codex:adversarial-review` — 挑戰式 Review

**可引導的挑戰式審查**，質疑實作方式和設計決策。不只找 bug，而是挑戰「這是不是正確的做法」。

#### 語法

```bash
/codex:adversarial-review [--wait|--background] [--base <ref>] [focus text...]
```

#### 與標準 review 的差異

| 面向 | `/codex:review` | `/codex:adversarial-review` |
|------|-----------------|----------------------------|
| **重點** | 實作缺陷（bug、安全、效能） | 設計決策、架構權衡、隱含假設 |
| **自訂 focus** | 不支援 | 支援（可在旗標後加 focus text） |
| **角度** | 「這段 code 有沒有問題？」 | 「這是不是正確的做法？」 |

#### 使用範例

```bash
# 挑戰當前變更的設計方向
/codex:adversarial-review

# 針對特定議題挑戰
/codex:adversarial-review --base main challenge whether this was the right caching and retry design

# 在背景執行，重點關注競態條件
/codex:adversarial-review --background look for race conditions and question the chosen approach
```

#### 最適合的場景

- 發布前的設計決策驗證
- 質疑 auth、資料遺失、rollback、競態條件等風險區域
- 壓力測試假設和 tradeoff
- 確認是否有更安全或更簡單的替代方案

---

### `/codex:rescue` — 委派任務

將調查、修復或其他任務委派給 Codex 執行。透過 `codex:codex-rescue` subagent 轉發。

#### 語法

```bash
/codex:rescue [--background|--wait] [--resume|--fresh] [--model <model|spark>] [--effort <level>] <task description>
```

#### 參數

| 參數 | 說明 |
|------|------|
| `--background` | 在背景執行 |
| `--wait` | 在前台等待（小型、明確的任務預設） |
| `--resume` | 繼續上一次的 Codex 任務 |
| `--fresh` | 強制啟動新的 Codex 執行緒 |
| `--model <name>` | 指定模型（如 `gpt-5.4-mini`），`spark` 會映射為 `gpt-5.3-codex-spark` |
| `--effort <level>` | 推理努力程度：`none`、`minimal`、`low`、`medium`、`high`、`xhigh` |
| `--write` | 預設啟用，允許 Codex 修改檔案（傳 `--read-only` 可關閉） |

#### 使用範例

```bash
# 調查測試失敗原因
/codex:rescue investigate why the tests started failing

# 用最小安全修補修復失敗的測試
/codex:rescue fix the failing test with the smallest safe patch

# 繼續上一次的任務
/codex:rescue --resume apply the top fix from the last run

# 用較小的模型快速處理
/codex:rescue --model spark fix the issue quickly

# 用指定模型和中等推理努力
/codex:rescue --model gpt-5.4-mini --effort medium investigate the flaky integration test

# 在背景執行
/codex:rescue --background investigate the regression
```

#### 自然語言委派

不用 slash command 也可以直接說：

```
Ask Codex to redesign the database connection to be more resilient.
```

#### 任務續接

若同一 repo 有先前的 Codex 任務，插件會詢問是否繼續：
- `Continue current Codex thread` — 延續先前任務
- `Start a new Codex thread` — 開始新任務

觸發續接的語句：「continue」、「keep going」、「resume」、「apply the top fix」、「dig deeper」。

---

### `/codex:status` — 查看任務狀態

顯示當前 repo 中正在執行和最近完成的 Codex 任務。

```bash
# 查看所有任務
/codex:status

# 查看特定任務
/codex:status task-abc123
```

輸出為 Markdown 表格，包含：job ID、類型、狀態、階段、耗時、摘要、後續指令。

---

### `/codex:result` — 取得任務結果

顯示已完成任務的最終輸出。

```bash
# 取得最新完成任務的結果
/codex:result

# 取得特定任務的結果
/codex:result task-abc123
```

結果包含：
- 完整的 verdict / summary / findings / next_steps
- 檔案路徑和行號
- Codex session ID（可在 Codex 中直接重開：`codex resume <session-id>`）

---

### `/codex:cancel` — 取消任務

取消正在執行的背景 Codex 任務。

```bash
# 取消最新的任務
/codex:cancel

# 取消特定任務
/codex:cancel task-abc123
```

---

### `/codex:setup` — 環境檢查與設定

檢查 Codex 安裝和認證狀態，管理 Review Gate。

```bash
# 基本環境檢查
/codex:setup

# 啟用 Review Gate
/codex:setup --enable-review-gate

# 停用 Review Gate
/codex:setup --disable-review-gate
```

---

## Subagent：codex-rescue

插件註冊了一個名為 `codex:codex-rescue` 的 Claude Code subagent。

### 設計理念

它是一個**薄轉發層（thin forwarding wrapper）**，不是獨立的 agent：
- 只做一件事：將使用者的 rescue 請求轉發給 `codex-companion.mjs task`
- 不會自行讀檔、分析程式碼、監控進度或做後續工作
- 唯一允許的 Claude 側工作：用 `gpt-5-4-prompting` skill 優化 prompt

### 主動派遣

subagent 的定義中包含「proactively use」指引：
- 當 Claude 主線程遇到瓶頸或需要第二輪診斷/實作時
- 當有大型 debugging 或 implementation 任務時
- **不會**搶走 Claude 能快速處理的小任務

### 可用 Skills

| Skill | 用途 |
|-------|------|
| `codex-cli-runtime` | 定義如何正確呼叫 `codex-companion.mjs task` |
| `gpt-5-4-prompting` | 將使用者請求優化為更好的 Codex prompt |
| `codex-result-handling` | 正確呈現 Codex 結果的規則 |

---

## Review Gate（審查門檻）

Review Gate 是一個可選的 **Stop Hook**，在 Claude 每次回應前，先讓 Codex 對該回應做一次精簡審查。

### 運作機制

```
Claude 回應 → Stop Hook 攔截 → Codex 審查 → ALLOW / BLOCK
                                                  ↓
                                        BLOCK → Claude 修正後重新回應
                                        ALLOW → 回應送出
```

### 審查邏輯

Codex 審查時遵循以下規則：
- **只審查上一輪 Claude 的回應**，不審查之前的輪次
- **只審查有程式碼變更的回應**，純狀態更新、setup 輸出等不計
- `ALLOW`：沒有程式碼變更，或沒有發現 blocking issue
- `BLOCK`：有程式碼變更且發現需要在 stop 前修正的問題

### 啟用方式

```bash
/codex:setup --enable-review-gate
```

### 注意事項

- Review Gate 會為**每一次 Claude 回應**觸發一次 Codex 審查
- 可能產生 Claude ↔ Codex 的反覆循環
- 會顯著增加 Codex 額度消耗和回應延遲
- **僅在主動監控 session 時啟用**

---

## 內建 Skills

插件包含三個內部 skill（不可由使用者直接呼叫）：

### gpt-5-4-prompting

指導如何為 Codex/GPT-5.4 撰寫高品質 prompt：

- **核心原則**：像 operator 一樣下指令，不是像 collaborator 一樣對話
- **使用 XML tags** 結構化 prompt（`<task>`、`<structured_output_contract>`、`<verification_loop>` 等）
- **每次只做一件事**：拆分不相關的需求為獨立 Codex run
- **明確定義完成標準**：不假設 Codex 會自行推斷
- **優先改善 prompt 品質**，而非提高 reasoning effort

#### Prompt 結構

| Block | 用途 | 適用場景 |
|-------|------|----------|
| `<task>` | 具體任務和上下文 | 所有任務 |
| `<structured_output_contract>` | 輸出格式和結構 | 需要結構化結果 |
| `<default_follow_through_policy>` | 預設行為（而非詢問） | 減少來回 |
| `<verification_loop>` | 驗證要求 | coding、debugging |
| `<grounding_rules>` | 引用和證據要求 | review、research |
| `<completeness_contract>` | 完整性保證 | debugging、implementation |
| `<action_safety>` | 修改範圍限制 | write-capable 任務 |

### codex-cli-runtime

定義 subagent 呼叫 `codex-companion.mjs task` 的正確方式，包含旗標處理、model 映射、resume/fresh 邏輯。

### codex-result-handling

定義如何正確呈現 Codex 輸出：
- 保留原始 verdict、summary、findings 結構
- 保留檔案路徑和行號
- **嚴格禁止**：review 後自動修復問題，必須先詢問使用者
- 若 Codex 執行失敗，回報失敗即可，不自行替代

---

## Codex 設定整合

插件使用你本機的 Codex CLI，因此共用相同的設定。

### 設定檔位置

| 層級 | 路徑 | 說明 |
|------|------|------|
| 使用者層級 | `~/.codex/config.toml` | 全域預設 |
| 專案層級 | `.codex/config.toml` | 專案覆蓋（需 trust 專案） |

### 常用設定範例

```toml
# 預設模型和推理努力
model = "gpt-5.4-mini"
model_reasoning_effort = "xhigh"

# 核准與沙箱
approval_policy = "on-request"
sandbox_mode = "workspace-write"
```

### 設定優先級

1. 指令中明確指定的旗標（如 `--model`、`--effort`）
2. 專案層級 `.codex/config.toml`
3. 使用者層級 `~/.codex/config.toml`
4. Codex 內建預設

> 專案層級設定需要[信任專案](https://developers.openai.com/codex/config-advanced#project-config-files-codexconfigtoml)才會載入。

---

## 典型工作流程

### 流程一：發布前審查

```bash
# 1. 標準 code review
/codex:review --base main --background

# 2. 等待完成
/codex:status

# 3. 取得結果
/codex:result

# 4. （可選）做挑戰式審查
/codex:adversarial-review --base main --background
```

### 流程二：Bug 調查與修復

```bash
# 1. 委派調查任務
/codex:rescue investigate why the build is failing in CI

# 2. 根據結果決定修復方式
/codex:rescue --resume apply the top fix from the last run

# 3. 確認修復結果
/codex:review
```

### 流程三：長時間背景任務

```bash
# 1. 啟動背景任務
/codex:rescue --background investigate the flaky test
/codex:adversarial-review --background

# 2. 繼續在 Claude 中做其他工作...

# 3. 隨時查看進度
/codex:status

# 4. 完成後取得結果
/codex:result
```

### 流程四：Claude + Codex 交叉驗證

```bash
# 1. Claude 完成實作
# ... （正常開發工作）

# 2. 啟用 Review Gate 讓 Codex 自動審查 Claude 的每次回應
/codex:setup --enable-review-gate

# 3. 繼續開發，每次 Claude 回應都會被 Codex 檢查
# ... 

# 4. 開發完成後停用
/codex:setup --disable-review-gate
```

### 流程五：切換到 Codex 繼續工作

```bash
# 1. 在 Claude Code 中委派任務
/codex:rescue --background investigate the regression

# 2. 取得結果和 session ID
/codex:result
# → 輸出包含 session ID

# 3. 在 Codex 中直接重開該 session
codex resume <session-id>
```

---

## 架構與技術細節

### 目錄結構

```
codex-plugin-cc/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace 註冊資訊
├── plugins/codex/
│   ├── .claude-plugin/
│   │   └── plugin.json           # 插件 manifest
│   ├── agents/
│   │   └── codex-rescue.md       # Subagent 定義
│   ├── commands/
│   │   ├── review.md             # /codex:review 指令定義
│   │   ├── adversarial-review.md # /codex:adversarial-review 指令定義
│   │   ├── rescue.md             # /codex:rescue 指令定義
│   │   ├── status.md             # /codex:status 指令定義
│   │   ├── result.md             # /codex:result 指令定義
│   │   ├── cancel.md             # /codex:cancel 指令定義
│   │   └── setup.md              # /codex:setup 指令定義
│   ├── hooks/
│   │   └── hooks.json            # Hook 定義（SessionStart/End、Stop）
│   ├── prompts/
│   │   ├── adversarial-review.md # Adversarial review prompt 模板
│   │   └── stop-review-gate.md   # Review Gate 的 Stop hook prompt
│   ├── schemas/
│   │   └── review-output.schema.json  # Review 輸出的 JSON Schema
│   ├── scripts/
│   │   ├── codex-companion.mjs   # 主橋接腳本（處理所有指令轉發）
│   │   ├── app-server-broker.mjs # App Server 代理
│   │   ├── session-lifecycle-hook.mjs  # Session 生命週期 hook
│   │   ├── stop-review-gate-hook.mjs   # Review Gate stop hook
│   │   └── lib/
│   │       ├── app-server.mjs     # Codex App Server 通訊
│   │       ├── app-server-protocol.d.ts  # App Server TypeScript 型別
│   │       ├── args.mjs           # 參數解析
│   │       ├── broker-endpoint.mjs    # Broker 端點管理
│   │       ├── broker-lifecycle.mjs   # Broker 生命週期
│   │       ├── codex.mjs          # Codex CLI 包裝
│   │       ├── fs.mjs             # 檔案系統工具
│   │       ├── git.mjs            # Git 操作
│   │       ├── job-control.mjs    # 任務控制
│   │       ├── process.mjs        # 程序管理
│   │       ├── prompts.mjs        # Prompt 組裝
│   │       ├── render.mjs         # 輸出渲染
│   │       ├── state.mjs          # 狀態管理
│   │       ├── tracked-jobs.mjs   # 任務追蹤
│   │       └── workspace.mjs      # 工作區管理
│   └── skills/
│       ├── codex-cli-runtime/SKILL.md
│       ├── codex-result-handling/SKILL.md
│       └── gpt-5-4-prompting/
│           ├── SKILL.md
│           └── references/
│               ├── codex-prompt-antipatterns.md
│               ├── codex-prompt-recipes.md
│               └── prompt-blocks.md
└── tests/
    ├── broker-endpoint.test.mjs
    ├── commands.test.mjs
    ├── git.test.mjs
    ├── process.test.mjs
    ├── render.test.mjs
    ├── runtime.test.mjs
    └── state.test.mjs
```

### 通訊架構

```
Claude Code
  ↓ (slash command)
codex-companion.mjs
  ↓ (app-server protocol)
Codex App Server (本機)
  ↓ (API call)
OpenAI API (GPT-5.4)
```

關鍵點：
- 所有程式碼讀寫在**本機**執行
- 只有 prompt 和上下文透過 API 傳送至模型
- 使用 Codex 的 [App Server](https://developers.openai.com/codex/app-server) 協議通訊

### Hook 機制

插件註冊了三個 hook：

| Hook | 觸發時機 | 用途 | Timeout |
|------|----------|------|---------|
| `SessionStart` | Claude Code session 開始 | 初始化 Codex companion 狀態 | 5 秒 |
| `SessionEnd` | Claude Code session 結束 | 清理 Codex companion 資源 | 5 秒 |
| `Stop` | Claude 每次回應前 | Review Gate 審查（可選） | 900 秒（15 分鐘） |

### Claude Code 插件系統概覽

此插件展示了 Claude Code 插件系統的完整能力：

| 元件 | 對應目錄 | 說明 |
|------|----------|------|
| **Manifest** | `.claude-plugin/plugin.json` | 插件基本資訊 |
| **Commands** | `commands/*.md` | Slash commands 定義 |
| **Agents** | `agents/*.md` | Subagent 定義 |
| **Skills** | `skills/*/SKILL.md` | 內部技能 |
| **Hooks** | `hooks/hooks.json` | 生命週期和事件 hook |
| **Prompts** | `prompts/*.md` | Prompt 模板 |
| **Schemas** | `schemas/*.json` | 輸出格式定義 |
| **Scripts** | `scripts/*.mjs` | 運行時腳本 |

---

## 常見問題

### 需要另外的 Codex 帳號嗎？

不需要。如果你已經在本機登入 Codex，插件會直接使用該認證。若尚未使用過 Codex，需要用 ChatGPT 帳號或 API Key 登入。

### 插件是否使用獨立的 Codex 運行環境？

否。插件透過本機的 Codex CLI 和 Codex App Server 運作：
- 使用相同的 Codex 安裝
- 使用相同的認證狀態
- 使用相同的 repository checkout 和本機環境

### 能否使用自訂的 API 端點？

可以。因為插件使用本機 Codex CLI，你現有的 `openai_base_url` 設定會被沿用。在 Codex config 中設定即可。

### Review 要跑多久？

取決於變更規模：
- 1-2 個檔案的小變更：通常 1-3 分鐘
- 多檔案大型變更：可能 5-15 分鐘
- 建議多檔案變更一律使用 `--background`

### Review Gate 和手動 review 有什麼不同？

| 面向 | 手動 `/codex:review` | Review Gate |
|------|---------------------|-------------|
| **觸發** | 使用者主動執行 | 每次 Claude 回應自動觸發 |
| **範圍** | 完整的 git diff review | 只審查上一輪 Claude 的變更 |
| **結果** | 完整報告 | 簡潔的 ALLOW/BLOCK |
| **影響** | 使用者自行決定 | BLOCK 會阻擋 Claude 回應 |
| **用途** | 階段性審查 | 持續性品質門檻 |

---

## 與現有 CODEX-GUIDE 的關係

| 文件 | 涵蓋範圍 |
|------|----------|
| [CODEX-GUIDE.md](CODEX-GUIDE.md) | Codex CLI 本身的安裝、設定、操作模式、沙箱、權限 |
| 本文件 | 在 Claude Code 中透過插件使用 Codex 的方式 |

兩者互補：
- 先依 CODEX-GUIDE 安裝和設定 Codex CLI
- 再依本文件安裝插件，在 Claude Code 中呼叫 Codex

---

## 故障排除

### Codex 未安裝

```bash
# 執行 setup 檢查
/codex:setup

# 手動安裝
npm install -g @openai/codex
```

### 認證失敗

```bash
# 在 Claude Code 中登入 Codex
!codex login

# 再次檢查
/codex:setup
```

### 背景任務卡住

```bash
# 查看狀態
/codex:status

# 若卡住，取消後重試
/codex:cancel
/codex:rescue --fresh <task description>
```

### Review Gate 導致循環

```bash
# 立即停用 Review Gate
/codex:setup --disable-review-gate
```

### 插件指令不出現

```bash
# 重新載入插件
/reload-plugins

# 確認安裝狀態
/codex:setup
```

### 想切換到 Codex 直接操作

```bash
# 取得 session ID
/codex:result

# 在終端中恢復 Codex session
codex resume <session-id>
```

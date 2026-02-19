---
tags:
  - ai
  - onboarding
  - dev-stack
  - vibe-coding
date created: 2026-01-14T16:00:00+08:00
date modified: 2026-02-05T10:00:00+08:00
description: 公司 AI 輔助開發環境的完整設定指南，以 Claude Code 為主力工具，涵蓋新人設定、使用說明與設計理念
---

# AI 開發環境設定指南

本文件是公司開發組的 AI 輔助開發環境完整指南，以 **Claude Code** 為主力開發工具。適用於：
- 🆕 **完全新手**：從未使用過 AI 輔助開發工具
- 🔧 **有經驗的開發者**：已熟悉 AI 工具，需了解公司規範

---

## 目錄

1. [為什麼需要這套 AI 開發 Stack](#為什麼需要這套-ai-開發-stack)
2. [工具總覽與架構](#工具總覽與架構)
3. [前置需求](#前置需求)
4. [Claude Code 安裝與設定](#claude-code-安裝與設定)
5. [每日更新維護](#每日更新維護)
6. [新專案初始化](#新專案初始化)
7. [Claude Code 使用說明](#claude-code-使用說明)
8. [使用 CLI 腳本自動化管理](#使用-cli-腳本自動化管理)
9. [故障排除](#故障排除)
10. [附錄 A：備選 AI 開發工具](#附錄-a備選-ai-開發工具)
11. [附錄 B：目錄結構總覽](#附錄-b目錄結構總覽)
12. [附錄 C：ECC 整合、標準體系、上游追蹤](#附錄-cecc-整合標準體系上游追蹤)

---

## 為什麼需要這套 AI 開發 Stack

### 設計理念

Claude Code 是目前推理能力最強的 AI 編程助手，但**原生狀態下缺乏一致的開發規範**。這套 Stack 以 Claude Code 為核心，搭配 Skills 與 Plugin 生態，解決以下問題：

| 問題 | 解決方案 |
|------|----------|
| AI 回應品質不一致 | 統一 Skills 讓 AI 遵循相同的開發標準 |
| 缺乏程式碼審查機制 | 內建 Code Review、Checkin 等 Skills |
| 提交訊息格式混亂 | Commit Standards 強制規範格式 |
| 需求不明確導致錯誤開發 | OpenSpec 規格驅動開發流程 |
| 不同工具間設定不同步 | 統一 Skills 目錄，跨工具共用 |

### 核心價值

1. **一致性**：所有開發者使用相同的 AI 行為標準
2. **品質保證**：內建測試、審查、提交規範
3. **知識傳承**：Skills 即文件，規範即程式碼
4. **工具中立**：Skills 可在 Claude Code 及其他備選工具間共用

---

## 工具總覽與架構

### 主要 AI 開發工具

| 工具                 | 用途               | 特色                  |
| ------------------ | ---------------- | ------------------- |
| **Claude Code** ⭐主力 | 主力 AI 編程助手       | 最強推理能力、完整 Plugin 生態 |
| **Antigravity**    | VSCode 整合的 AI 助手 | 圖形介面、IDE 整合         |
| **OpenCode**       | 開源 AI 編程助手       | 多模型支援、可自訂 Agent     |
| **oh-my-opencode** | OpenCode 增強套件    | 平行代理、深度探索、免費模型整合    |
| **Codex**          | OpenAI Codex CLI  | GPT-4 整合、程式碼生成      |
| **Gemini CLI**     | Google AI 命令列工具  | 免費額度、程式碼審查          |

> 本指南主要流程以 Claude Code 為主，其他工具的安裝與設定請參閱[附錄 A：備選 AI 開發工具](#附錄-a備選-ai-開發工具)。

### Skills 與 Plugin 架構

```
┌─────────────────────────────────────────────────────────────┐
│                     Skills 來源                             │
├─────────────────────────────────────────────────────────────┤
│  universal-dev-standards  │  everything-claude-code  │      │
│  (開發標準)               │  (ECC: Hooks/Skills/    │      │
│                           │   Agents/Commands)       │      │
├───────────────────────────┼──────────────────────────┤      │
│  superpowers  │  anthropic-skills  │  obsidian-skills │      │
│  (進階工作流) │  (官方 Skills)     │  (Obsidian)      │      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   ~/.config/custom-skills/                  │
│                   (統一 Skills 管理目錄)                     │
│  ├── skills/      # 共用 Skills                             │
│  ├── commands/    # 工具專屬 Commands                       │
│  ├── agents/      # 工具專屬 Agents                         │
│  ├── sources/ecc/ # ECC 資源整合                            │
│  └── upstream/    # 上游追蹤系統                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
      ┌───────────┬───────────┼───────────┬───────────┐
      ↓           ↓           ↓           ↓           ↓
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│~/.claude/│ │~/.gemini/│ │~/.config/│ │~/.codex/ │ │~/.gemini/│
│ skills/  │ │antigrav./│ │opencode/ │ │ skills/  │ │ skills/  │
│commands/ │ │ skills/  │ │ skills/  │ │          │ │commands/ │
│ agents/  │ │workflows/│ │ agents/  │ │          │ │          │
│  Claude  │ │Antigrav. │ │ OpenCode │ │  Codex   │ │Gemini CLI│
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
```

### 關鍵 Skills 說明

#### UDS Skills（核心開發標準）

| Skill | 功能 | 何時觸發 |
|-------|------|----------|
| `ai-collaboration-standards` | 防止 AI 幻覺，確保實證回應 | 分析程式碼、提供建議時 |
| `commit-standards` | 規範提交訊息格式 | git commit 時 |
| `code-review-assistant` | 程式碼審查清單 | 審查 PR 或提交前 |
| `testing-guide` | 測試策略指南 | 撰寫測試時 |
| `spec-driven-dev` | 規格驅動開發工作流 | 規劃功能時 |

#### ECC Skills（進階工作流）

| Skill | 功能 | 何時觸發 |
|-------|------|----------|
| `continuous-learning` | 從會話萃取學習模式 | 完成開發任務後 |
| `eval-harness` | Eval 驅動開發測試框架 | 驗證 AI 回應品質時 |
| `security-review` | OWASP 安全漏洞檢測 | 程式碼安全審查時 |
| `tdd-workflow` | TDD 開發流程整合 | 測試驅動開發時 |

---

## 前置需求

### macOS

```shell
# 1. 安裝 Homebrew (如尚未安裝)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安裝 Node.js (建議使用 nvm 管理版本)
brew install nvm
nvm install node
nvm use node

# 3. 確認 Node.js 版本 >= 20.19.0
node --version

# 4. 安裝 bun
curl -fsSL https://bun.sh/install | bash

# 5. 安裝 Git
brew install git

# 6. 安裝 GitHub CLI (用於 PR 管理)
brew install gh
gh auth login
```

### Windows

```powershell
# 1. 安裝 Node.js
#    下載並安裝: https://nodejs.org/ (選擇 LTS 版本 >= 20.x)

# 2. 確認版本
node --version
npm --version

# 3. 安裝 bun
curl -fsSL https://bun.sh/install | bash

# 4. 安裝 Git
#    下載並安裝: https://git-scm.com/download/win

# 5. 安裝 GitHub CLI
winget install GitHub.cli
gh auth login

# 6. (選用) 安裝 Windows Terminal
winget install Microsoft.WindowsTerminal
```

### 必要帳號與 API Key

| 服務 | 用途 | 必要性 | 取得方式 |
|------|------|--------|----------|
| Anthropic API | Claude Code | **必要** | https://console.anthropic.com/ |
| Google AI | Gemini CLI（備選工具） | 選用 | https://aistudio.google.com/api-keys |

---

## Claude Code 安裝與設定

> ⚠️ **重要**：首次設定請完整執行以下步驟，之後的更新只需執行「每日更新維護」即可。

### 第一步：安裝 Claude Code

**macOS / Linux：**

```shell
curl -fsSL https://claude.ai/install.sh | bash
```

**macOS (Homebrew)：**

```shell
brew install --cask claude-code
```

**Windows (PowerShell)：**

```powershell
irm https://claude.ai/install.ps1 | iex
```

### 第二步：安裝 ai-dev 並執行自動化設定

`ai-dev` CLI 工具會自動完成以下所有操作：安裝全域 NPM 工具、建立目錄結構、Clone Skills 來源、複製 Skills 到 Claude Code。

```shell
# 安裝 ai-dev（需要 uv，安裝方式見「使用 CLI 腳本自動化管理」章節）
uv tool install git+https://github.com/ValorVie/custom-skills.git

# 執行首次安裝（自動化完成目錄建立、repo clone、Skills 複製）
ai-dev install

# 驗證安裝狀態
ai-dev status
```

> 其他 AI 開發工具（OpenCode、Gemini CLI、Codex）會在 `ai-dev install` 過程中一併處理。各工具的詳細說明請參閱[附錄 A](#附錄-a備選-ai-開發工具)。

### 第三步：安裝 Claude Code Plugin

啟動 Claude Code 後執行：

```shell
# 安裝 claude-mem
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem

# 安裝 Superpowers 插件
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace

# 安裝 Code Simplifier
/plugin marketplace add anthropics/claude-plugins-official
/plugin install code-simplifier

# 安裝 Ralph Loop (選用，用於批次任務)
/plugin install ralph-loop@anthropics

# 安裝 custom-skills ecc-hooks 插件
/plugin marketplace add https://github.com/ValorVie/custom-skills.git
/plugin install ecc-hooks@custom-skills
/plugin install auto-skill-hooks@custom-skills

# 安裝 PHP LSP
/plugin install php-lsp

# 安裝更多插件（選用）
/plugin marketplace add wshobson/agents
# 1. 瀏覽可用插件 (共 72 個分類)
/plugin list

# 2. 安裝特定插件 (例如: Python 開發)
/plugin install python-development
# 這會自動載入 3 個代理 + 5 個技能

# 3. 安裝 K8s 相關功能
/plugin install kubernetes-operations
# 這會載入 K8s 專家代理 + 4 個技能

# 安裝更多插件（選用）
/plugin marketplace add anthropics/claude-code
/plugin install frontend-design@claude-code-plugins

# 4. 驗證安裝
/agents  # 查看已載入的代理


# 驗證安裝
/help
```

### 第四步：設定 MCP Server

MCP (Model Context Protocol) Server 可以擴充 AI 工具的能力，例如查詢最新文件、安全掃描等。

```shell
# 安裝 Context7 (文件查詢)
claude mcp add context7 --scope user -- npx @upstash/context7-mcp

# 查看已安裝的 MCP Server
claude mcp list

# 移除 MCP Server
claude mcp remove <name>
```

設定檔位置：`~/.claude.json`

**常用 MCP Server 設定**：

| MCP Server | 用途       | 設定範例                                                                   |
| ---------- | -------- | ---------------------------------------------------------------------- |
| Context7   | 查詢最新技術文件 | 見上方範例                                                                  |
| Snyk       | 安全漏洞掃描   | 見上方範例                                                                  |
| Filesystem | 檔案系統操作   | `"command": "npx", "args": ["-y", "@anthropic/mcp-server-filesystem"]` |

> Antigravity 的 MCP Server 設定請參閱[附錄 A](#附錄-a備選-ai-開發工具)。

### 第五步：選用 SKILLS 
- https://skills.sh/

```shell
# 尋找 Skills 的 SKILL
npx skills add https://github.com/vercel-labs/skills --skill find-skills
```

```shell
npx skills -h
npx skills add vercel-labs/agent-skills
npx skills add vercel-labs/agent-skills -g
npx skills add vercel-labs/agent-skills --agent claude-code cursor
npx skills add vercel-labs/agent-skills --skill pr-review commit
# interactive remove
npx skills remove
# remove by name
npx skills remove web-design
# global skills only
npx skills rm --global frontend-design
# list all installed skills
npx skills list
# list global skills only
npx skills ls -g
# interactive search
npx skills find
# search by keyword
npx skills find typescript
# init new skill
npx skills init my-skill
npx skills check
npx skills update
```

#### 目前安裝
```shell
# 尋找 Skills 的 SKILL (全局)
npx skills add https://github.com/vercel-labs/skills --skill find-skills

# tampermonkey 專案 (專案)
npx skills add henkisdabro/wookstar-claude-code-plugins@tampermonkey

```



---

## 每日更新維護

> 建議每天開始工作前執行一次，確保工具與 Skills 為最新版本。

```shell
# 更新所有工具與 Skills 來源
ai-dev update

# 重新分發 Skills 到各工具目錄
ai-dev clone
```

`ai-dev update` 會自動：更新 Claude Code、更新全域 NPM 工具、拉取所有 Skills 來源 repo 的最新變更。

`ai-dev clone` 會自動：整合 Skills 到統一管理目錄、複製到 Claude Code 及其他已安裝的工具目錄。

> 如需手動更新個別工具，請參閱[附錄 A](#附錄-a備選-ai-開發工具)中各工具的每日更新段落。

---

## 新專案初始化

每當建立新專案時，執行以下步驟來初始化開發環境：

### 步驟 1：初始化 Universal Dev Standards

```shell
cd your-project
uds init
```

這會建立 `.standards/` 目錄，包含：
- 反幻覺協議
- 提交訊息標準
- 程式碼審查清單

### 步驟 2：初始化 OpenSpec

如果專案需要規格驅動開發：

```shell
openspec init
```

初始化完成後，請 AI 協助填寫專案資訊：

```
請閱讀 openspec/config.yaml，並協助我填寫關於我的專案、技術堆疊 (tech stack) 和開發規範 (conventions) 的細節。
```

### 步驟 3：初始化 Claude Code (選用)

```shell
claude
/init
```

這會掃描專案並建立 `CLAUDE.md` 專案指南。

---

## Claude Code 使用說明

### 基礎操作

```shell
# 啟動
claude

# 初始化專案
/init

# 查看狀態（建議關閉 Auto Compact ）
/status

# 壓縮對話（保留重要內容）
/compact 保留前端相關對話

# 清理上下文
/clear

# 提升思考深度（在問題末尾加入）
think < think hard < think harder < ultrathink

# 一次性對話（不進入互動模式）
claude -p "檢查文件依賴項目是否正確"
```

### Skills 使用

當 Claude Code 偵測到相關情境時，Skills 會自動觸發。你也可以主動呼叫：

```shell
# 程式碼審查
/code-review-assistant

# 提交標準
/commit-standards

# 規格驅動開發
/spec-driven-dev
```

### OpenSpec 工作流
完整工作流可參考 [DEVELOPMENT-WORKFLOW](workflow/DEVELOPMENT-WORKFLOW)

```shell
# 建立變更提案
/openspec:proposal 新增用戶登入功能

# 查看變更列表
openspec list

# 驗證規格
openspec validate add-user-login

# 應用變更
/openspec:apply add-user-login

# 封存已完成的變更
/openspec:archive add-user-login
```

### Ralph Loop (批次任務)

```shell
# 批次程式碼審查
/ralph-loop:ralph-loop "根據目前已更改的檔案跟 @IMPLEMENTATION_PLAN.md 計畫比對，review 是否有錯誤或遺漏的部分" --completion-promise "計畫驗證完畢"

# 設定最大迭代次數
/ralph-loop:ralph-loop "..." --max-iterations 20 --completion-promise "完成"
```

---

## 使用 CLI 腳本自動化管理

本專案提供了 `ai-dev` CLI 工具來自動化環境安裝與維護流程。

### 安裝 CLI 工具

**從 GitHub 安裝（推薦）：**

```shell
# 使用 uv（推薦）
uv tool install git+https://github.com/ValorVie/custom-skills.git

# 使用 pipx
pipx install git+https://github.com/ValorVie/custom-skills.git

# 私有倉庫需要 token
uv tool install git+https://<GITHUB_TOKEN>@github.com/ValorVie/custom-skills.git
```

**更新 CLI 工具：**

```shell
uv tool upgrade ai-dev
```

**本地開發安裝：**

```shell
git clone https://github.com/ValorVie/custom-skills.git
cd custom-skills
uv tool install . --force
```

> **注意**：`uv` 會根據版本號判斷是否需要重新安裝。如果修改了程式碼但版本號未變更，可能會使用快取。請先更新 `pyproject.toml` 中的 `version` 欄位後再執行安裝。

### 可用指令

```shell
ai-dev --help
```

| 指令 | 說明 |
|------|------|
| `install` | 首次安裝 AI 開發環境（NPM 套件、目錄、Git 儲存庫、Skills 複製） |
| `update` | 每日更新：更新 NPM 工具與 Git 儲存庫 |
| `status` | 檢查環境狀態與工具版本 |
| `list` | 列出已安裝的 Skills、Commands、Agents |
| `toggle` | 啟用/停用特定工具的特定資源 |
| `tui` | 啟動互動式終端介面 |
| `project` | 專案級別的初始化與更新操作 |
| `clone` | 分發 Skills 內容到各 AI 工具目錄 |
| `standards` | 管理標準體系 profiles（uds/ecc/minimal） |

### Project 指令（專案級操作）

在專案目錄下初始化或更新配置：

```shell
# 初始化專案（整合 openspec init + uds init）
ai-dev project init

# 只初始化特定工具
ai-dev project init --only openspec
ai-dev project init --only uds

# 更新專案配置（整合 openspec update + uds update）
ai-dev project update

# 只更新特定工具
ai-dev project update --only openspec
```

### List 指令

列出各工具已安裝的資源（預設包含停用的資源）：

```shell
# 列出 Claude Code 的 Skills
ai-dev list --target claude --type skills

# 列出 Antigravity 的 Workflows
ai-dev list --target antigravity --type workflows

# 列出 OpenCode 的 Agents
ai-dev list --target opencode --type agents

# 列出 Codex 的 Skills
ai-dev list --target codex --type skills

# 列出 Gemini CLI 的 Skills
ai-dev list --target gemini --type skills

# 隱藏已停用的資源
ai-dev list --hide-disabled
```

### Toggle 指令

啟用或停用特定資源。停用時會將檔案移動到 `~/.config/custom-skills/disabled/` 目錄，啟用時會移回原位置。

```shell
# 停用特定 skill
ai-dev toggle --target claude --type skills --name skill-creator --disable

# 重新啟用
ai-dev toggle --target claude --type skills --name skill-creator --enable

# 查看目前狀態
ai-dev toggle --list
```

**停用機制**：停用的資源會被移動到 `~/.config/custom-skills/disabled/<target>/<type>/` 目錄，啟用時會複製回原位置並刪除 disabled 中的檔案。

> **注意**：停用/啟用後需要重啟對應的 AI 工具才會生效。

**配置檔位置**：`~/.config/custom-skills/toggle-config.yaml`

```yaml
claude:
  skills:
    enabled: true
    disabled:
      - "some-skill-to-disable"
  commands:
    enabled: true
    disabled: []

antigravity:
  skills:
    enabled: true
    disabled: []
  workflows:
    enabled: true
    disabled: []

opencode:
  agents:
    enabled: true
    disabled: []
```

### TUI 互動介面

啟動 TUI 可視化管理介面：

```shell
ai-dev tui
```

**功能**：
- 頂部按鈕列：Install / Update / Status / Add Skills / Quit
- Target 下拉選單：切換目標工具（Claude Code / Antigravity / OpenCode / Codex / Gemini CLI）
- Type 下拉選單：切換資源類型（Skills / Commands / Agents / Workflows）
- Sync to Project：勾選時會同步到 custom-skills 專案目錄（僅開發人員需要）
- 資源列表：Checkbox 勾選啟用/停用
- MCP Config 區塊：顯示目前工具的 MCP 設定檔路徑與快速開啟按鈕

**MCP Config 區塊**：

TUI 底部顯示目前選擇的工具的 MCP 設定檔資訊：

| 工具 | 設定檔路徑 |
|------|-----------|
| Claude Code | `~/.claude.json` |
| Antigravity | `~/.gemini/antigravity/mcp_config.json` |
| OpenCode | `~/.config/opencode/opencode.json` |
| Codex | `~/.codex/config.json` |
| Gemini CLI | `~/.gemini/settings.json` |

點擊「Open in Editor」可在編輯器中開啟設定檔，點擊「Open Folder」可在檔案管理器中開啟。

**快捷鍵**：

| 按鍵 | 功能 |
|------|------|
| `q` | 退出 |
| `Space` | 切換選中項目 |
| `a` | 全選 |
| `n` | 全取消 |
| `s` | 儲存並同步 |
| `p` | 開啟 Add Skills 對話框 |
| `e` | 在編輯器中開啟 MCP 設定檔 |
| `f` | 在檔案管理器中開啟 MCP 設定檔所在目錄 |

**Add Skills 對話框**：
- 輸入套件名稱（如 `vercel-labs/agent-skills`）
- 執行 `npx skills add` 並顯示即時輸出

### 第三方 Skills 管理

使用 `npx skills` 安裝第三方 Skills：

```shell
# 可用指令
npx skills add <package>      # 安裝 skill 套件
npx skills a <package>        # 同上（別名）
npx skills install <package>  # 同上（別名）
npx skills i <package>        # 同上（別名）

# 計畫中
npx skills find <query>       # 搜尋 skills
npx skills update             # 更新已安裝的 skills

# 範例
npx skills add vercel-labs/agent-skills
```

---

## 故障排除

### 常見問題

#### Q: Claude Code 看不到新安裝的 Skills/Plugin

**A:** 重新啟動 Claude Code。Skills 和 Plugin 是在啟動時載入的。

```shell
# 退出後重新啟動
exit
claude
```

#### Q: Skills 目錄找不到

**A:** 確認目錄結構正確：

```shell
# macOS/Linux
ls -la ~/.claude/skills/

# Windows
dir "$env:USERPROFILE\.claude\skills\"
```

#### Q: OpenSpec 指令找不到

**A:** 確認 Node.js 版本 >= 20.19.0，並重新安裝：

```shell
node --version
npm install -g @fission-ai/openspec@latest
openspec --version
```

#### Q: MCP Server 連線失敗

**A:** 檢查設定檔：

```shell
# 編輯 MCP 設定
cat ~/.claude.json

# 或移除後重新新增
claude mcp remove context7
claude mcp add context7 --scope user -- npx @upstash/context7-mcp
```

#### Q: Windows 上出現權限錯誤

**A:** 以系統管理員身份執行 PowerShell，或檢查資料夾權限。

### 取得協助

- 內部：聯繫開發組負責人
- Claude Code 文件：https://docs.anthropic.com/en/docs/claude-code/overview
- OpenSpec 文件：https://github.com/Fission-AI/OpenSpec
- Universal Dev Standards：https://github.com/AsiaOstrich/universal-dev-standards

---

## 附錄 A：備選 AI 開發工具

### OpenCode + oh-my-opencode

#### 安裝

```shell
# 安裝 OpenCode
npm install -g opencode-ai@latest
```

#### 安裝 oh-my-opencode (選用但推薦)

oh-my-opencode 是 OpenCode 的增強套件，提供：
- **Sisyphus Agent**：不間斷執行直到完成任務
- **平行代理**：同時執行多個子任務
- **多模型整合**：整合 Claude、ChatGPT、Gemini 等模型
- **免費模型支援**：可使用 GLM-4.7-free 等免費模型

##### 前置需求：安裝 Bun

**macOS / Linux**

```shell
curl -fsSL https://bun.sh/install | bash
```

**Windows (PowerShell)**

```powershell
powershell -c "irm bun.sh/install.ps1 | iex"
```

##### 安裝 oh-my-opencode

```shell
bunx oh-my-opencode install
```

安裝過程會詢問：
1. **Do you have a Claude Pro/Max subscription?** - 選擇 Yes/No
2. **Do you have a ChatGPT Plus/Pro subscription?** - 選擇 Yes/No
3. **Will you integrate Google Gemini?** - 選擇 Yes/No

安裝完成後，執行認證：

```shell
# 認證各個提供者
opencode auth login  # 選擇 Anthropic → Claude Pro/Max
opencode auth login  # 選擇 OpenAI → ChatGPT Plus/Pro
opencode auth login  # 選擇 Google → OAuth with Antigravity

opencode auth logout

# 查看認證狀態
opencode auth list
```

#### 建立目錄結構

**macOS / Linux**

```shell
mkdir -p ~/.config/opencode/agent
```

**Windows (PowerShell)**

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\opencode\agent"
```

#### 複製 Skills/Commands/Agents

**macOS / Linux**

```shell
# 複製 Agent
cp -r ~/.config/custom-skills/agent/opencode/* ~/.config/opencode/agent
```

**Windows (PowerShell)**

```powershell
# 複製 Agent
Copy-Item -Recurse -Force "$env:USERPROFILE\.config\custom-skills\agent\opencode\*" "$env:USERPROFILE\.config\opencode\agent\"
```

#### 安裝 OpenCode Superpowers

- 直接執行 `ai-dev install` 或 `ai-dev update` 會自動：
  - 將 superpowers clone/pull 至 `~/.config/opencode/superpowers`
  - 建立/刷新 symlink：`~/.config/opencode/plugins/superpowers.js`、`~/.config/opencode/skills/superpowers`
  - 輸出驗證指令：`ls -l ~/.config/opencode/plugins/superpowers.js` 與 `ls -l ~/.config/opencode/skills/superpowers`

- 若想在 OpenCode 內請求安裝 Superpowers 插件
```
Fetch and follow instructions from https://raw.githubusercontent.com/obra/superpowers/refs/heads/main/.opencode/INSTALL.md
```

- 手動安裝

**macOS / Linux**

```shell
mkdir -p ~/.config/opencode/superpowers
git clone https://github.com/obra/superpowers.git ~/.config/opencode/superpowers
mkdir -p ~/.config/opencode/plugins
ln -sf ~/.config/opencode/superpowers/.opencode/plugins/superpowers.js ~/.config/opencode/plugins/superpowers.js
```

**Windows (PowerShell)**

```powershell
$O="$env:USERPROFILE\.config\opencode"
New-Item -ItemType Directory -Force -Path "$O\plugin" | Out-Null
git clone https://github.com/obra/superpowers.git "$O\superpowers"
cmd /c mklink /J "$O\plugin\superpowers.js" "$O\superpowers\.opencode\plugin\superpowers.js"
```

驗證安裝（在 OpenCode 中輸入）：
```
do you have superpowers?
```

#### 公司推薦 Agent 配置

修改設定檔為公司推薦配置：

**macOS / Linux**

```shell
nano ~/.config/opencode/oh-my-opencode.json
```

**Windows (PowerShell)**

```powershell
notepad "$env:USERPROFILE\.config\opencode\oh-my-opencode.json"
```

**公司推薦配置**（使用 GPT-5.2-Codex + 免費 GLM-4.7）：

```json
{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-opencode/master/assets/oh-my-opencode.schema.json",
  "agents": {
    "Sisyphus": {
      "model": "openai/gpt-5.2-codex"
    },
    "librarian": {
      "model": "opencode/glm-4.7-free"
    },
    "explore": {
      "model": "opencode/glm-4.7-free"
    },
    "frontend-ui-ux-engineer": {
      "model": "openai/gpt-5.2-codex"
    },
    "document-writer": {
      "model": "opencode/glm-4.7-free"
    },
    "multimodal-looker": {
      "model": "opencode/glm-4.7-free"
    }
  }
}
```

> **配置說明**：
> - **Sisyphus** 和 **frontend-ui-ux-engineer**：使用 GPT-5.2-Codex 處理核心開發和前端任務
> - 其他 Agent：使用免費的 GLM-4.7 處理輔助任務（搜尋、文件、探索）
> - 此配置平衡了效能與成本

#### 使用說明

##### 基礎操作

```shell
# 啟動
opencode

# 連接 IDE（VSCode 整合）
/connect

# 認證管理
opencode auth list      # 查看認證狀態
opencode auth login     # 新增認證
opencode auth logout    # 登出
```

##### ultrawork 模式

安裝 oh-my-opencode 後，在提示詞中加入 `ultrawork`（或簡寫 `ulw`）即可啟用所有增強功能：

```shell
# 範例：啟用 ultrawork 模式
請幫我重構這個模組 ultrawork

# 或使用簡寫
實作用戶登入功能 ulw
```

**ultrawork 模式功能**：
- **平行代理**：自動將任務分配給多個 Agent 並行處理
- **深度探索**：徹底分析程式碼庫結構
- **不間斷執行**：持續執行直到任務完成
- **背景任務**：長時間任務在背景執行

##### Agent 設定

公司推薦配置的 Agent（已在安裝時設定）：

| Agent | 用途 | 公司推薦模型 |
|-------|------|----------|
| **Sisyphus** | 主力開發 Agent | gpt-5.2-codex |
| **Librarian** | 資料查詢 | glm-4.7-free (免費) |
| **Explore** | 程式碼探索 | glm-4.7-free (免費) |
| **Frontend** | 前端 UI/UX | gpt-5.2-codex |
| **Document-writer** | 文件撰寫 | glm-4.7-free (免費) |
| **Multimodal-looker** | 多模態分析 | glm-4.7-free (免費) |

**設定檔位置**：
- macOS/Linux: `~/.config/opencode/oh-my-opencode.json`
- Windows: `C:\Users\<username>\.config\opencode\oh-my-opencode.json`

##### 自訂 Agent

你可以建立專屬的 Agent 來處理特定任務。

**建立 Agent**：

```shell
# 全域 Agent
~/.config/opencode/agent/review.md

# 專案 Agent
.opencode/agent/review.md
```

**Agent 範例** (`review.md`)：

```markdown
---
description: Reviews code for quality and best practices
mode: subagent
model: anthropic/claude-sonnet-4-20250514
temperature: 0.1
tools:
  write: false
  edit: false
  bash: false
---

You are in code review mode. Focus on:

- Code quality and best practices
- Potential bugs and edge cases
- Performance implications
- Security considerations

Provide constructive feedback without making direct changes.
```

> **注意**：OpenCode 的 Skills 和 Command 路徑沿用 Claude Code 設定（`~/.claude/skills/` 和 `~/.claude/commands/`）。

#### 每日更新

```shell
# macOS / Linux
npm install -g opencode-ai@latest
cd ~/.config/opencode/superpowers && git pull
cp -r ~/.config/custom-skills/agent/opencode/* ~/.config/opencode/agent
```

```powershell
# Windows
npm install -g opencode-ai@latest
Set-Location "$env:USERPROFILE\.config\opencode\superpowers"; git pull
Copy-Item -Recurse -Force "$env:USERPROFILE\.config\custom-skills\agent\opencode\*" "$env:USERPROFILE\.config\opencode\agent\"
```

#### 故障排除

##### Q: OpenCode 無法啟動或找不到指令

**A:** 確認安裝正確：

```shell
npm install -g opencode-ai@latest
opencode --version
```

##### Q: oh-my-opencode 安裝失敗

**A:** 確認 Bun 已正確安裝：

```shell
# 檢查 Bun 版本
bun --version

# 如果沒有安裝，執行：
# macOS/Linux
curl -fsSL https://bun.sh/install | bash

# Windows
powershell -c "irm bun.sh/install.ps1 | iex"

# 重新安裝 oh-my-opencode
bunx oh-my-opencode install
```

##### Q: OpenCode 認證失敗

**A:** 重新執行認證流程：

```shell
# 查看目前認證狀態
opencode auth list

# 登出後重新登入
opencode auth logout
opencode auth login
```

### Antigravity

#### 安裝

Antigravity 是 VSCode 整合的 AI 助手，無需獨立安裝 CLI。請在 VSCode 的延伸模組市場搜尋安裝。

#### 建立目錄結構

**macOS / Linux**

```shell
mkdir -p ~/.gemini/antigravity/skills
mkdir -p ~/.gemini/antigravity/global_workflows
```

**Windows (PowerShell)**

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.gemini\antigravity\skills"
```

#### 複製 Skills/Workflows

**macOS / Linux**

```shell
cp -r ~/.config/custom-skills/skills/* ~/.gemini/antigravity/skills
cp -r ~/.config/custom-skills/command/antigravity/* ~/.gemini/antigravity/global_workflows
```

**Windows (PowerShell)**

```powershell
Copy-Item -Recurse -Force "$env:USERPROFILE\.config\custom-skills\skills\*" "$env:USERPROFILE\.gemini\antigravity\skills\"
Copy-Item -Recurse -Force "$env:USERPROFILE\.config\custom-skills\command\antigravity\*" "$env:USERPROFILE\.gemini\antigravity\global_workflows\"
```

#### MCP Server 設定

**macOS / Linux**

```shell
nano ~/.gemini/mcp_config.json
```

**Windows (PowerShell)**

```powershell
notepad "$env:USERPROFILE\.gemini\antigravity\mcp_config.json"
```

**設定檔內容範例** (`~/.gemini/mcp_config.json`)：

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": [
        "-y",
        "@upstash/context7-mcp@latest"
      ]
    }
  }
}
```

> **注意**：Windows 使用者需將 `command` 路徑調整為 Windows 格式，例如：
> ```json
> "command": "C:\\Users\\username\\AppData\\Roaming\\npm\\snyk.cmd"
> ```

#### 每日更新

```shell
# macOS / Linux
cp -r ~/.config/custom-skills/skills/* ~/.gemini/antigravity/skills
cp -r ~/.config/custom-skills/command/antigravity/* ~/.gemini/antigravity/global_workflows
```

```powershell
# Windows
Copy-Item -Recurse -Force "$env:USERPROFILE\.config\custom-skills\skills\*" "$env:USERPROFILE\.gemini\antigravity\skills\"
Copy-Item -Recurse -Force "$env:USERPROFILE\.config\custom-skills\command\antigravity\*" "$env:USERPROFILE\.gemini\antigravity\global_workflows\"
```

### Codex

#### 自動安裝（推薦）

`ai-dev install` 會自動檢查並安裝 Codex CLI（需要已安裝 Bun）：

```shell
ai-dev install
```

若 Bun 未安裝，系統會顯示安裝指引。你也可以手動安裝 Bun：

```shell
# macOS / Linux
curl -fsSL https://bun.sh/install | bash

# Windows (PowerShell)
powershell -c "irm bun.sh/install.ps1 | iex"
```

#### 手動安裝

如果你想手動安裝 Codex：

```shell
bun install -g @openai/codex
```

#### 複製 Skills

Codex 使用 `~/.codex/skills/` 目錄。Skills 複製方式與其他工具類似。

### Gemini CLI

#### 安裝

```shell
# npm
npm install -g @google/gemini-cli

# macOS 額外安裝 (Homebrew)
brew install gemini-cli
```

#### 複製 Skills/Commands

Gemini CLI 使用 `~/.gemini/skills/` 和 `~/.gemini/commands/` 目錄。

#### MCP Server 設定

設定檔位置：`~/.gemini/settings.json`

---

## 附錄 B：目錄結構總覽

```
~/.claude/
├── CLAUDE.md              # 全域用戶指南
├── skills/                # Claude Code Skills（OpenCode 共用）
│   ├── ai-collaboration-standards/
│   ├── commit-standards/
│   ├── code-review-assistant/
│   └── ...
└── commands/              # 自訂命令（OpenCode 共用）

~/.gemini/
├── GEMINI.md              # 全域用戶指南
├── settings.json          # Gemini CLI 設定
├── mcp_config.json        # Antigravity MCP 設定
├── skills/                # Gemini CLI Skills
├── commands/              # Gemini CLI Commands
└── antigravity/
    ├── skills/            # Antigravity Skills
    └── global_workflows/  # 全域工作流

~/.codex/
├── config.json            # Codex MCP 設定
└── skills/                # Codex Skills

~/.config/
├── custom-skills/         # 統一 Skills 管理（公司自訂）
│   ├── skills/            # 共用 Skills
│   ├── commands/          # 共用 Commands
│   │   ├── claude/
│   │   ├── antigravity/
│   │   └── gemini/
│   ├── agents/            # 共用 Agents
│   │   ├── claude/
│   │   └── opencode/
│   ├── sources/           # 整合的外部來源
│   │   └── ecc/           # Everything Claude Code
│   │       ├── hooks/     # Python 跨平台 hooks
│   │       ├── skills/    # ECC Skills
│   │       ├── agents/    # ECC Agents
│   │       └── commands/  # ECC Commands
│   ├── upstream/          # 上游追蹤系統
│   │   ├── sources.yaml   # 來源註冊表
│   │   └── <repo>/        # 各 repo 同步狀態
│   └── disabled/          # 停用的資源
├── superpowers/           # Superpowers 來源
├── universal-dev-standards/  # UDS 來源
└── opencode/
    ├── opencode.json      # OpenCode 主設定
    ├── oh-my-opencode.json  # oh-my-opencode 設定
    ├── superpowers/       # OpenCode Superpowers 插件
    ├── plugin/            # OpenCode 插件目錄
    └── agent/             # OpenCode 全域 Agent
        └── review.md

project/
├── .claude/               # 專案級 Claude Code 設定
│   ├── commands/
│   └── settings.json
├── .agent/                # 專案級 Antigravity 設定
├── .opencode/             # 專案級 OpenCode 設定
│   └── agent/             # 專案級 Agent
├── .codex/                # 專案級 Codex 設定
├── .standards/            # UDS 專案標準
├── openspec/              # OpenSpec 規格
│   ├── project.md
│   ├── specs/
│   └── changes/
└── CLAUDE.md              # 專案 Claude 指南
```

---

## 附錄 C：ECC 整合、標準體系、上游追蹤

### ECC (Everything Claude Code) 整合

v0.6.0 新增 Everything Claude Code 資源整合，提供進階的 Claude Code 工作流程工具：

| 類型 | 說明 |
|------|------|
| **Hooks** | Python 跨平台 hooks（memory-persistence, strategic-compact） |
| **Skills** | continuous-learning, eval-harness, security-review, tdd-workflow |
| **Agents** | build-error-resolver, e2e-runner, doc-updater, security-reviewer |
| **Commands** | /checkpoint, /build-fix, /e2e, /learn, /coverage, /eval |

詳見 `sources/ecc/README.md`。

### 標準體系切換 (Standards Profiles)

支援在不同標準體系之間切換：

```shell
# 查看目前狀態
ai-dev standards status

# 列出可用 profiles
ai-dev standards list

# 切換 profile（會自動停用重疊資源）
ai-dev standards switch ecc

# 預覽切換影響
ai-dev standards switch ecc --dry-run

# 顯示 profile 內容
ai-dev standards show ecc

# 顯示重疊定義
ai-dev standards overlaps

# 同步檔案狀態
ai-dev standards sync
```

可用 profiles：
- `uds` - Universal Dev Standards 完整版（預設）
- `ecc` - Everything Claude Code 工作流程
- `minimal` - 最小化配置

**Profile 系統特性**：
- **重疊檢測**：定義於 `profiles/overlaps.yaml`，標記功能等效的資源
- **自動停用**：切換 profile 時，自動停用重疊組中非偏好來源的資源
- **手動保護**：手動停用的項目不會被 profile 切換覆蓋
- **同步機制**：`sync` 指令會實際移動檔案到 `.disabled/` 目錄或還原

### 上游追蹤與同步

追蹤第三方 repo 的同步狀態：

```shell
# 使用 Skills 進行上游審核
/custom-skills-upstream-sync      # 生成結構化分析報告
/upstream-compare   # AI 生成整合建議
```

上游追蹤資訊位於 `upstream/` 目錄，包含：
- `sources.yaml` - 上游來源註冊表
- `<repo>/mapping.yaml` - 檔案對照表
- `<repo>/last-sync.yaml` - 最後同步資訊

---

## 更新日誌

| 日期 | 版本 | 變更內容 |
|------|------|----------|
| 2026-02-05 | 2.1.0 | 安裝流程改以 `ai-dev install` 自動化為主，手動步驟精簡；每日更新改用 `ai-dev update` + `ai-dev clone` |
| 2026-02-05 | 2.0.0 | 重構文件結構：以 Claude Code 為主線，其他工具移至備選附錄 |
| 2026-01-25 | 1.7.0 | 新增 Profile 重疊檢測系統說明（`overlaps`, `sync`, `--dry-run` 指令） |
| 2026-01-25 | 1.6.0 | 更新 `update` 指令說明（移除不存在的 `--sync-upstream` 參數）、修正上游同步流程說明 |
| 2026-01-24 | 1.5.0 | 整合 ECC 資源、新增上游追蹤系統、標準體系切換、clone 與 standards 指令 |
| 2026-01-20 | 1.4.0 | CLI 工具打包為 `ai-dev`，支援全域安裝；新增 `project init/update` 專案級指令 |
| 2026-01-19 | 1.3.0 | 新增 CLI 腳本自動化管理說明（list、toggle、tui 指令） |
| 2026-01-15 | 1.2.0 | 補完 custom-skills 倉庫、Command/Agent 複製流程、OpenCode Superpowers 安裝、Windows 指令格式修正 |
| 2026-01-14 | 1.1.1 | 加入公司推薦的 oh-my-opencode Agent 配置 |
| 2026-01-14 | 1.1.0 | 新增 OpenCode 與 oh-my-opencode 完整教學 |
| 2026-01-14 | 1.0.1 | 補充 Antigravity MCP Server 設定說明 |
| 2026-01-14 | 1.0.0 | 首次發布 |

---

## 相關文件

- [Skill-Command-Agent差異說明](Skill-Command-Agent差異說明.md) - 了解三者的差異與使用時機
- [openscode](openscode) - OpenCode 詳細設定與進階用法
- [Dev stack](Dev%20stack.md) - 原始設定腳本參考
- [AI Tools](AI%20Tools.md) - 完整工具清單與進階設定

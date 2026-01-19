---
tags:
  - ai
  - onboarding
  - dev-stack
  - vibe-coding
date created: 2026-01-14T16:00:00+08:00
date modified: 2026-01-15T02:33:30+08:00
description: 公司 AI 輔助開發環境的完整設定指南，涵蓋新人設定、使用說明與設計理念
---

# AI 開發環境設定指南

本文件是公司開發組的 AI 輔助開發環境完整指南，適用於：
- 🆕 **完全新手**：從未使用過 AI 輔助開發工具
- 🔧 **有經驗的開發者**：已熟悉 AI 工具，需了解公司規範

---

## 目錄

1. [為什麼需要這套 AI 開發 Stack](#為什麼需要這套-ai-開發-stack)
2. [工具總覽與架構](#工具總覽與架構)
3. [前置需求](#前置需求)
4. [首次安裝設定](#首次安裝設定)
5. [每日更新維護](#每日更新維護)
6. [新專案初始化](#新專案初始化)
7. [工具使用說明](#工具使用說明)
8. [故障排除](#故障排除)

---

## 為什麼需要這套 AI 開發 Stack

### 設計理念

現代 AI 輔助開發工具（如 Claude Code、Gemini CLI）功能強大，但**原生狀態下缺乏一致的開發規範**。這套 Stack 的目標是：

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
4. **工具中立**：Skills 可在 Claude Code、Antigravity、OpenCode 等工具間共用

---

## 工具總覽與架構

### 主要 AI 開發工具

| 工具                 | 用途               | 特色                  |
| ------------------ | ---------------- | ------------------- |
| **Claude Code**    | 主力 AI 編程助手       | 最強推理能力、完整 Plugin 生態 |
| **Antigravity**    | VSCode 整合的 AI 助手 | 圖形介面、IDE 整合         |
| **OpenCode**       | 開源 AI 編程助手       | 多模型支援、可自訂 Agent     |
| **oh-my-opencode** | OpenCode 增強套件    | 平行代理、深度探索、免費模型整合    |
| **Gemini CLI**     | Google AI 命令列工具  | 免費額度、程式碼審查          |

### Skills 與 Plugin 架構

```
┌─────────────────────────────────────────────────────────────┐
│                     Skills 來源                             │
├─────────────────────────────────────────────────────────────┤
│  universal-dev-standards   │   superpowers   │   openspec   │
│  (開發標準)                │   (進階工作流)   │   (規格驅動)  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   ~/.config/custom-skills/                  │
│                   (統一 Skills 管理目錄)                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
      ┌───────────────────────┼───────────────────────┐
      ↓                       ↓                       ↓
┌─────────────┐      ┌─────────────────┐      ┌─────────────┐
│ ~/.claude/  │      │ ~/.gemini/      │      │ ~/.config/  │
│   skills/   │      │ antigravity/    │      │  opencode/  │
│             │      │   skills/       │      │             │
│ Claude Code │      │  Antigravity    │      │  OpenCode   │
└─────────────┘      └─────────────────┘      └─────────────┘
```

### 關鍵 Skills 說明

| Skill | 功能 | 何時觸發 |
|-------|------|----------|
| `ai-collaboration-standards` | 防止 AI 幻覺，確保實證回應 | 分析程式碼、提供建議時 |
| `commit-standards` | 規範提交訊息格式 | git commit 時 |
| `code-review-assistant` | 程式碼審查清單 | 審查 PR 或提交前 |
| `testing-guide` | 測試策略指南 | 撰寫測試時 |
| `spec-driven-dev` | 規格驅動開發工作流 | 規劃功能時 |

---

## 前置需求

### macOS

```shell
# 1. 安裝 Homebrew (如尚未安裝)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安裝 Node.js (建議使用 nvm 管理版本)
brew install nvm
nvm install 20
nvm use 20

# 3. 確認 Node.js 版本 >= 20.19.0
node --version

# 4. 安裝 Git
brew install git

# 5. 安裝 GitHub CLI (用於 PR 管理)
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

# 3. 安裝 Git
#    下載並安裝: https://git-scm.com/download/win

# 4. 安裝 GitHub CLI
winget install GitHub.cli
gh auth login

# 5. (選用) 安裝 Windows Terminal
winget install Microsoft.WindowsTerminal
```

### 必要帳號與 API Key

| 服務 | 用途 | 取得方式 |
|------|------|----------|
| Anthropic API | Claude Code | https://console.anthropic.com/ |
| Google AI | Gemini CLI | https://aistudio.google.com/api-keys |

---

## 首次安裝設定

> ⚠️ **重要**：首次設定請完整執行以下步驟，之後的更新只需執行「每日更新維護」即可。

### 第一步：安裝全域 CLI 工具

#### macOS / Linux

```shell
# AI 開發工具
npm install -g @anthropic-ai/claude-code
npm install -g @fission-ai/openspec@latest
npm install -g @google/gemini-cli
npm install -g universal-dev-standards
npm install -g opencode-ai@latest

# macOS 額外安裝 (Homebrew)
brew install gemini-cli
```

#### Windows (PowerShell)

```powershell
# AI 開發工具
npm install -g @anthropic-ai/claude-code
npm install -g @fission-ai/openspec@latest
npm install -g @google/gemini-cli
npm install -g universal-dev-standards
npm install -g opencode-ai@latest
```

### 第一步 (續)：安裝 oh-my-opencode (選用但推薦)

oh-my-opencode 是 OpenCode 的增強套件，提供：
- **Sisyphus Agent**：不間斷執行直到完成任務
- **平行代理**：同時執行多個子任務
- **多模型整合**：整合 Claude、ChatGPT、Gemini 等模型
- **免費模型支援**：可使用 GLM-4.7-free 等免費模型

#### 前置需求：安裝 Bun

**macOS / Linux**

```shell
curl -fsSL https://bun.sh/install | bash
```

**Windows (PowerShell)**

```powershell
powershell -c "irm bun.sh/install.ps1 | iex"
```

#### 安裝 oh-my-opencode

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

#### 修改 oh-my-opencode 設定（公司推薦配置）

安裝完成後，請將設定檔修改為公司推薦的 Agent 配置：

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

### 第二步：建立目錄結構

#### macOS / Linux

```shell
# 建立必要資料夾
mkdir -p ~/.claude/skills ~/.claude/commands
mkdir -p ~/.config/custom-skills/skills ~/.config/custom-skills/command
mkdir -p ~/.config/superpowers
mkdir -p ~/.config/universal-dev-standards
mkdir -p ~/.gemini/antigravity/skills
mkdir -p ~/.gemini/antigravity/global_workflows
mkdir -p ~/.config/opencode/agent
mkdir -p ~/.config/custom-skills
```

#### Windows (PowerShell)

```powershell
# 建立必要資料夾
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\commands"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\custom-skills\skills"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\superpowers"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\universal-dev-standards"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.gemini\antigravity\skills"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\opencode\agent"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\custom-skills"
```

### 第三步：Clone Skills 來源

#### macOS / Linux

```shell
cd ~/.config/custom-skills
git clone https://github.com/ValorVie/custom-skills.git .

# Clone Superpowers
cd ~/.config/superpowers
git clone https://github.com/obra/superpowers.git .

# Clone Universal Dev Standards
cd ~/.config/universal-dev-standards
git clone https://github.com/AsiaOstrich/universal-dev-standards.git .

cd ~/.config/
```

#### Windows (PowerShell)

```powershell
Set-Location "$env:USERPROFILE\.config\custom-skills"
git clone https://github.com/ValorVie/custom-skills.git .

# Clone Superpowers
Set-Location "$env:USERPROFILE\.config\superpowers"
git clone https://github.com/obra/superpowers.git .

# Clone Universal Dev Standards
Set-Location "$env:USERPROFILE\.config\universal-dev-standards"
git clone https://github.com/AsiaOstrich/universal-dev-standards.git .
```

### 第四步：複製 Skills 到各工具

#### macOS / Linux

```shell
# 複製到統一管理目錄
cp -r ~/.config/universal-dev-standards/skills/claude-code/* ~/.config/custom-skills/skills

# 清理不需要的檔案
rm -rf ~/.config/custom-skills/skills/tdd-assistant \
       ~/.config/custom-skills/skills/CONTRIBUTING.template.md \
       ~/.config/custom-skills/skills/install.ps1 \
       ~/.config/custom-skills/skills/install.sh \
       ~/.config/custom-skills/skills/README.md

# 複製到 Claude Code
cp -r ~/.config/universal-dev-standards/skills/claude-code/* ~/.claude/skills/
rm -rf ~/.claude/skills/tdd-assistant \
       ~/.claude/skills/CONTRIBUTING.template.md \
       ~/.claude/skills/install.ps1 \
       ~/.claude/skills/install.sh \
       ~/.claude/skills/README.md

# 複製到 Antigravity
cp -r ~/.config/custom-skills/skills/* ~/.gemini/antigravity/skills
```

##### Command
```shell
# Command
cp -r ~/.config/custom-skills/command/claude/* ~/.claude/command
cp -r ~/.config/custom-skills/command/antigravity/* ~/.gemini/antigravity/global_workflows
```


##### Agent

```shell
cp -r ~/.config/custom-skills/agent/opencode/* ~/.config/opencode/agent
```

##### OpenCode Superpowers

安裝 OpenCode 的 Superpowers 插件：
- 請 OpenCode 安裝 Superpowers 插件
```
Fetch and follow instructions from https://raw.githubusercontent.com/obra/superpowers/refs/heads/main/.opencode/INSTALL.md
```

- 手動安裝
```shell
mkdir -p ~/.config/opencode/superpowers
git clone https://github.com/obra/superpowers.git ~/.config/opencode/superpowers
mkdir -p ~/.config/opencode/plugin
ln -sf ~/.config/opencode/superpowers/.opencode/plugin/superpowers.js ~/.config/opencode/plugin/superpowers.js
```

驗證安裝（在 OpenCode 中輸入）：
```
do you have superpowers?
```

#### Windows (PowerShell)

```powershell
# 複製到 Claude Code
Copy-Item -Recurse -Force "$env:USERPROFILE\.config\universal-dev-standards\skills\claude-code\*" "$env:USERPROFILE\.claude\skills\"

# 清理不需要的檔案
Remove-Item -Recurse -Force "$env:USERPROFILE\.claude\skills\tdd-assistant" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:USERPROFILE\.claude\skills\CONTRIBUTING.template.md" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:USERPROFILE\.claude\skills\install.ps1" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:USERPROFILE\.claude\skills\install.sh" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:USERPROFILE\.claude\skills\README.md" -ErrorAction SilentlyContinue


# 複製到統一管理目錄
Copy-Item -Recurse -Force "$env:USERPROFILE\.config\universal-dev-standards\skills\claude-code\*" "$env:USERPROFILE\.config\custom-skills\skills\"

# 清理不需要的檔案
Remove-Item -Recurse -Force "$env:USERPROFILE\.config\custom-skills\skills\tdd-assistant" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:USERPROFILE\.config\custom-skills\skills\CONTRIBUTING.template.md" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:USERPROFILE\.config\custom-skills\skills\install.ps1" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:USERPROFILE\.config\custom-skills\skills\install.sh" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:USERPROFILE\.config\custom-skills\skills\README.md" -ErrorAction SilentlyContinue



# 複製到 Antigravity
Copy-Item -Recurse -Force "$env:USERPROFILE\.config\custom-skills\skills\*" "$env:USERPROFILE\.gemini\antigravity\skills\"
```

##### Command

```powershell
Copy-Item -Recurse -Force "$env:USERPROFILE\.config\custom-skills\command\claude\*" "$env:USERPROFILE\.claude\commands\"

Copy-Item -Recurse -Force "$env:USERPROFILE\.config\custom-skills\command\antigravity\*" "$env:USERPROFILE\.gemini\antigravity\global_workflows\"
```

##### Agent

```powershell
Copy-Item -Recurse -Force "$env:USERPROFILE\.config\custom-skills\agent\opencode\*" "$env:USERPROFILE\.config\opencode\agent\"
```

##### OpenCode Superpowers

安裝 OpenCode 的 Superpowers 插件：
- 請 OpenCode 安裝 Superpowers 插件
```
Fetch and follow instructions from https://raw.githubusercontent.com/obra/superpowers/refs/heads/main/.opencode/INSTALL.md
```
- 手動安裝
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


### 第五步：安裝 Claude Code Plugin

啟動 Claude Code 後執行：

```shell
# 安裝 Superpowers 插件
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace

# 安裝 Code Simplifier
/plugin marketplace update claude-plugins-official
/plugin install code-simplifier

# 安裝 Ralph Loop (選用，用於批次任務)
/plugin install ralph-loop@anthropics

# 驗證安裝
/help
```

### 第六步：設定 MCP Server

MCP (Model Context Protocol) Server 可以擴充 AI 工具的能力，例如查詢最新文件、安全掃描等。

#### Claude Code MCP 設定

```shell
# 安裝 Context7 (文件查詢)
claude mcp add context7 --scope user -- npx @upstash/context7-mcp

# 查看已安裝的 MCP Server
claude mcp list

# 移除 MCP Server
claude mcp remove <name>
```

設定檔位置：`~/.claude.json`

#### Antigravity MCP 設定

Antigravity 使用獨立的設定檔管理 MCP Server。

**macOS / Linux**

```shell
# 建立設定檔
nano ~/.gemini/mcp_config.json
```

**Windows (PowerShell)**

```powershell
# 建立設定檔
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

**常用 MCP Server 設定**：

| MCP Server | 用途       | 設定範例                                                                   |
| ---------- | -------- | ---------------------------------------------------------------------- |
| Context7   | 查詢最新技術文件 | 見上方範例                                                                  |
| Snyk       | 安全漏洞掃描   | 見上方範例                                                                  |
| Filesystem | 檔案系統操作   | `"command": "npx", "args": ["-y", "@anthropic/mcp-server-filesystem"]` |

---

## 每日更新維護

> 建議每天開始工作前執行一次，確保工具與 Skills 為最新版本。

### macOS / Linux

```shell
# 更新全域工具
npm install -g @fission-ai/openspec@latest
npm install -g @anthropic-ai/claude-code
npm install -g @openai/codex@latest
npm install -g @google/gemini-cli
npm install -g universal-dev-standards
npm install -g opencode-ai@latest
uds update

# 更新 Skills 來源
cd ~/.config/superpowers && git pull
cd ~/.config/universal-dev-standards && git pull
cd ~/.config/custom-skills && git pull
cd ~/.config/opencode/superpowers && git pull

# 重新複製 Skills
cp -r ~/.config/universal-dev-standards/skills/claude-code/* ~/.claude/skills/
rm -rf ~/.claude/skills/tdd-assistant \
       ~/.claude/skills/CONTRIBUTING.template.md \
       ~/.claude/skills/install.ps1 \
       ~/.claude/skills/install.sh \
       ~/.claude/skills/README.md

# 複製到統一管理目錄
cp -r ~/.config/universal-dev-standards/skills/claude-code/* ~/.config/custom-skills/skills
rm -rf ~/.config/custom-skills/skills/tdd-assistant \
       ~/.config/custom-skills/skills/CONTRIBUTING.template.md \
       ~/.config/custom-skills/skills/install.ps1 \
       ~/.config/custom-skills/skills/install.sh \
       ~/.config/custom-skills/skills/README.md

# 複製到 Antigravity
cp -r ~/.config/custom-skills/skills/* ~/.gemini/antigravity/skills

# 複製 Command
cp -r ~/.config/custom-skills/command/claude/* ~/.claude/commands
cp -r ~/.config/custom-skills/command/antigravity/* ~/.gemini/antigravity/global_workflows

# 複製 Agent
cp -r ~/.config/custom-skills/agent/opencode/* ~/.config/opencode/agent
```

### Windows (PowerShell)

```powershell
# 更新全域工具
npm install -g @fission-ai/openspec@latest
npm install -g @anthropic-ai/claude-code
npm install -g @google/gemini-cli
npm install -g universal-dev-standards
npm install -g opencode-ai@latest
uds update

# 更新 Skills 來源
Set-Location "$env:USERPROFILE\.config\custom-skills"; git pull
Set-Location "$env:USERPROFILE\.config\superpowers"; git pull
Set-Location "$env:USERPROFILE\.config\opencode\superpowers"; git pull
Set-Location "$env:USERPROFILE\.config\universal-dev-standards"; git pull

# 複製到 Claude Code
Copy-Item -Recurse -Force "$env:USERPROFILE\.config\universal-dev-standards\skills\claude-code\*" "$env:USERPROFILE\.claude\skills\"


# 清理不需要的檔案
Remove-Item -Recurse -Force "$env:USERPROFILE\.claude\skills\tdd-assistant" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:USERPROFILE\.claude\skills\CONTRIBUTING.template.md" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:USERPROFILE\.claude\skills\install.ps1" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:USERPROFILE\.claude\skills\install.sh" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:USERPROFILE\.claude\skills\README.md" -ErrorAction SilentlyContinue


# 複製到統一管理目錄
Copy-Item -Recurse -Force "$env:USERPROFILE\.config\universal-dev-standards\skills\claude-code\*" "$env:USERPROFILE\.config\custom-skills\skills\"

# 清理不需要的檔案
Remove-Item -Recurse -Force "$env:USERPROFILE\.config\custom-skills\skills\tdd-assistant" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:USERPROFILE\.config\custom-skills\skills\CONTRIBUTING.template.md" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:USERPROFILE\.config\custom-skills\skills\install.ps1" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:USERPROFILE\.config\custom-skills\skills\install.sh" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:USERPROFILE\.config\custom-skills\skills\README.md" -ErrorAction SilentlyContinue

# 複製到 Antigravity
Copy-Item -Recurse -Force "$env:USERPROFILE\.config\custom-skills\skills\*" "$env:USERPROFILE\.gemini\antigravity\skills\"

# 複製 Command
Copy-Item -Recurse -Force "$env:USERPROFILE\.config\custom-skills\command\claude\*" "$env:USERPROFILE\.claude\commands\"
Copy-Item -Recurse -Force "$env:USERPROFILE\.config\custom-skills\command\antigravity\*" "$env:USERPROFILE\.gemini\antigravity\global_workflows\"

# 複製 Agent
Copy-Item -Recurse -Force "$env:USERPROFILE\.config\custom-skills\agent\opencode\*" "$env:USERPROFILE\.config\opencode\agent\"
```

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

### 步驟 2：初始化 OpenSpec (選用)

如果專案需要規格驅動開發：

```shell
openspec init
```

初始化完成後，請 AI 協助填寫專案資訊：

```
請閱讀 openspec/project.md，並協助我填寫關於我的專案、技術堆疊 (tech stack) 和開發規範 (conventions) 的細節。
```

### 步驟 3：初始化 Claude Code (選用)

```shell
claude
/init
```

這會掃描專案並建立 `CLAUDE.md` 專案指南。

---

## 工具使用說明

### Claude Code 基礎

```shell
# 啟動
claude

# 初始化專案
/init

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

### OpenCode 基礎

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

### OpenCode + oh-my-opencode 使用

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

### OpenCode Agent 設定

公司推薦配置的 Agent（已在首次安裝時設定）：

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

**公司推薦配置**（已在首次安裝設定）：

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

> **配置策略**：核心開發任務使用付費模型 (GPT-5.2-Codex)，輔助任務使用免費模型 (GLM-4.7-free)

### OpenCode 自訂 Agent

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
ls -la ~/.gemini/antigravity/skills/

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

#### Q: OpenCode 無法啟動或找不到指令

**A:** 確認安裝正確：

```shell
npm install -g opencode-ai@latest
opencode --version
```

#### Q: oh-my-opencode 安裝失敗

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

#### Q: OpenCode 認證失敗

**A:** 重新執行認證流程：

```shell
# 查看目前認證狀態
opencode auth list

# 登出後重新登入
opencode auth logout
opencode auth login
```

### 取得協助

- 內部：聯繫開發組負責人
- Claude Code 文件：https://docs.anthropic.com/en/docs/claude-code/overview
- OpenCode 文件：https://opencode.ai/docs
- oh-my-opencode：https://github.com/code-yeongyu/oh-my-opencode
- OpenSpec 文件：https://github.com/Fission-AI/OpenSpec
- Universal Dev Standards：https://github.com/AsiaOstrich/universal-dev-standards

---

## 使用 CLI 腳本自動化管理

本專案提供了 Python CLI 腳本來自動化環境安裝與維護流程。

### 安裝與啟動

```shell
cd ~/.config/custom-skills
uv run python script/main.py --help
```

### 可用指令

| 指令 | 說明 |
|------|------|
| `install` | 首次安裝 AI 開發環境（NPM 套件、目錄、Git 儲存庫、Skills 複製） |
| `maintain` | 每日維護：更新工具並同步設定 |
| `status` | 檢查環境狀態與工具版本 |
| `list` | 列出已安裝的 Skills、Commands、Agents |
| `toggle` | 啟用/停用特定工具的特定資源 |
| `tui` | 啟動互動式終端介面 |

### List 指令

列出各工具已安裝的資源（預設包含停用的資源）：

```shell
# 列出 Claude Code 的 Skills
uv run python script/main.py list --target claude --type skills

# 列出 Antigravity 的 Workflows
uv run python script/main.py list --target antigravity --type workflows

# 列出 OpenCode 的 Agents
uv run python script/main.py list --target opencode --type agents

# 隱藏已停用的資源
uv run python script/main.py list --hide-disabled
```

### Toggle 指令

啟用或停用特定資源。停用時會將檔案移動到 `~/.config/custom-skills/disabled/` 目錄，啟用時會移回原位置。

```shell
# 停用特定 skill
uv run python script/main.py toggle --target claude --type skills --name skill-creator --disable

# 重新啟用
uv run python script/main.py toggle --target claude --type skills --name skill-creator --enable

# 查看目前狀態
uv run python script/main.py toggle --list
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
uv run python script/main.py tui
```

**功能**：
- 頂部按鈕列：Install / Maintain / Status / Add Skills / Quit
- Target 下拉選單：切換目標工具（Claude Code / Antigravity / OpenCode）
- Type 下拉選單：切換資源類型（Skills / Commands / Agents / Workflows）
- 資源列表：Checkbox 勾選啟用/停用
- 快捷鍵：Space 切換、A 全選、N 全取消、S 儲存、P 新增套件

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

## 附錄：目錄結構總覽

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
├── mcp_config.json        # Antigravity MCP 設定
└── antigravity/
    ├── skills/            # Antigravity Skills
    └── global_workflows/  # 全域工作流

~/.config/
├── custom-skills/         # 統一 Skills 管理（公司自訂）
│   ├── skills/            # 共用 Skills
│   ├── command/           # 共用 Command
│   │   ├── claude/
│   │   └── antigravity/
│   └── agent/             # 共用 Agent
│       └── opencode/
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
├── .standards/            # UDS 專案標準
├── openspec/              # OpenSpec 規格
│   ├── project.md
│   ├── specs/
│   └── changes/
└── CLAUDE.md              # 專案 Claude 指南
```

---

## 更新日誌

| 日期 | 版本 | 變更內容 |
|------|------|----------|
| 2026-01-19 | 1.3.0 | 新增 CLI 腳本自動化管理說明（list、toggle、tui 指令） |
| 2026-01-15 | 1.2.0 | 補完 custom-skills 倉庫、Command/Agent 複製流程、OpenCode Superpowers 安裝、Windows 指令格式修正 |
| 2026-01-14 | 1.1.1 | 加入公司推薦的 oh-my-opencode Agent 配置 |
| 2026-01-14 | 1.1.0 | 新增 OpenCode 與 oh-my-opencode 完整教學 |
| 2026-01-14 | 1.0.1 | 補充 Antigravity MCP Server 設定說明 |
| 2026-01-14 | 1.0.0 | 首次發布 |

---

## 相關文件

- [Skill-Command-Agent差異說明](Skill-Command-Agent差異說明.md) - 了解三者的差異與使用時機
- [openscode](openscode.md) - OpenCode 詳細設定與進階用法
- [Dev stack](Dev%20stack.md) - 原始設定腳本參考
- [AI Tools](AI%20Tools.md) - 完整工具清單與進階設定

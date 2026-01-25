# AI 開發環境設定工具 (ai-dev)

統一的自動化設定與維護 CLI 工具，支援 macOS, Linux 與 Windows。

## 安裝

### 前置需求

請先安裝 `uv` (Python 專案管理工具)：

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 安裝 Claude Code

Claude Code 需要使用 native 安裝方式，不再透過 NPM 安裝：

**macOS / Linux（推薦）：**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**macOS (Homebrew)：**
```bash
brew install --cask claude-code
```

**Windows (WinGet)：**
```powershell
winget install Anthropic.ClaudeCode
```

> 詳細說明請參考 [Claude Code 官方文件](https://code.claude.com/docs)

### 安裝 CLI 工具

**從 GitHub 安裝（推薦）：**

```bash
# 使用 uv
uv tool install git+https://github.com/ValorVie/custom-skills.git

# 使用 pipx
pipx install git+https://github.com/ValorVie/custom-skills.git

# 私有倉庫需要 token
uv tool install git+https://<GITHUB_TOKEN>@github.com/ValorVie/custom-skills.git
```

**更新 CLI 工具：**

```bash
uv tool upgrade ai-dev
```

**本地開發安裝：**

```bash
git clone https://github.com/ValorVie/custom-skills.git
cd custom-skills
uv tool install . --force
```

> **注意**：`uv` 會根據版本號判斷是否需要重新安裝。如果修改了程式碼但版本號未變更，可能會使用快取。請先更新 `pyproject.toml` 中的 `version` 欄位後再執行安裝。

## 使用方式

安裝後，可在任意目錄使用 `ai-dev` 指令。

```bash
# 顯示版本
ai-dev --version
ai-dev -v

# 顯示說明
ai-dev --help
```

### 首次安裝 (Install)

執行以下指令進行全新環境設定：

```bash
ai-dev install
```

這會自動：
1. 檢查 Node.js 與 Git。
2. 檢查 Claude Code CLI 是否已安裝（若無則顯示安裝指引）。
3. 安裝全域 NPM 工具 (`openspec`, `gemini-cli`, `skills` 等)。
4. Clone 必要的設定儲存庫到 `~/.config/` （Stage 1）。
5. 整合 Skills 到 `~/.config/custom-skills/`（Stage 2）。
6. 複製 Skills 與設定到各個 AI 工具的目錄（Stage 3）。
7. 顯示已安裝的 Skills 清單與重複名稱警告。
8. 顯示 `npx skills` 可用指令提示。

> **注意**：Claude Code 需要使用 native 安裝方式，不再透過 NPM 安裝。

#### 可選參數

| 參數 | 說明 |
|------|------|
| `--skip-npm` | 跳過 NPM 套件安裝 |
| `--skip-repos` | 跳過 Git 儲存庫 Clone |
| `--skip-skills` | 跳過複製 Skills |
| `--sync-project/--no-sync-project` | 是否同步到專案目錄（預設：是） |

**範例：**
```bash
# 只 Clone 儲存庫（跳過 NPM 和 Skills 複製）
ai-dev install --skip-npm --skip-skills

# 安裝但不同步到當前專案目錄
ai-dev install --no-sync-project
```

### 每日更新 (Update)

建議每天開始工作前執行，以保持環境最新：

```bash
ai-dev update
```

這會自動：
1. 更新 Claude Code（若已安裝）。
2. 更新全域 NPM 工具。
3. 拉取所有設定儲存庫的最新變更 (`git fetch` + `git reset`)。

> **注意**：此指令不會自動分發 Skills 到各工具目錄。如需分發，請執行 `ai-dev clone`。

#### 可選參數

| 參數 | 說明 |
|------|------|
| `--skip-npm` | 跳過 NPM 套件更新（含 Claude Code） |
| `--skip-repos` | 跳過 Git 儲存庫更新 |

**範例：**
```bash
# 只更新 Git 儲存庫（跳過 NPM）
ai-dev update --skip-npm

# 只更新 NPM 套件（跳過 Git）
ai-dev update --skip-repos

# 更新後分發 Skills
ai-dev update && ai-dev clone
```

### 專案級操作 (Project)

在專案目錄下初始化或更新配置：

```bash
# 初始化專案（整合 openspec init + uds init）
ai-dev project init

# 只初始化特定工具
ai-dev project init --only openspec
ai-dev project init --only uds

# 強制重新初始化
ai-dev project init --force

# 開發者模式：在 custom-skills 專案中反向同步到 project-template/
# （會將專案根目錄的模板檔案同步回 project-template/）
cd ~/custom-skills && ai-dev project init --force

# 更新專案配置（整合 openspec update + uds update）
ai-dev project update

# 只更新特定工具
ai-dev project update --only openspec
```

#### 可選參數

**init:**

| 參數 | 說明 |
|------|------|
| `--only`, `-o` | 只初始化特定工具：`openspec`, `uds` |
| `--force`, `-f` | 強制重新初始化（即使已存在）；在 custom-skills 專案中會反向同步到 `project-template/` |

**update:**

| 參數 | 說明 |
|------|------|
| `--only`, `-o` | 只更新特定工具：`openspec`, `uds` |

### 狀態檢查 (Status)

隨時檢查環境配置狀態：

```bash
ai-dev status
```

這會顯示：
- 核心工具版本 (Node.js, Git)
- NPM 套件安裝狀態（含 `skills` 套件）
- 設定儲存庫狀態

### 列出已安裝資源 (List)

列出各工具已安裝的 Skills、Commands、Agents（預設包含停用的資源）：

```bash
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

#### 可選參數

| 參數 | 說明 |
|------|------|
| `--target`, `-t` | 目標工具：`claude`, `antigravity`, `opencode`, `codex`, `gemini` |
| `--type`, `-T` | 資源類型：`skills`, `commands`, `agents`, `workflows` |
| `--hide-disabled`, `-H` | 隱藏已停用的資源（預設顯示全部） |

### 啟用/停用資源 (Toggle)

啟用或停用特定工具的特定資源。停用時會將檔案移動到 `~/.config/custom-skills/disabled/` 目錄，啟用時會移回原位置。

```bash
# 停用特定 skill
ai-dev toggle --target claude --type skills --name skill-creator --disable

# 重新啟用
ai-dev toggle --target claude --type skills --name skill-creator --enable

# 查看目前狀態
ai-dev toggle --list
```

#### 可選參數

| 參數 | 說明 |
|------|------|
| `--target`, `-t` | 目標工具：`claude`, `antigravity`, `opencode`, `codex`, `gemini` |
| `--type`, `-T` | 資源類型：`skills`, `commands`, `agents`, `workflows` |
| `--name`, `-n` | 資源名稱 |
| `--enable`, `-e` | 啟用資源 |
| `--disable`, `-d` | 停用資源 |
| `--list`, `-l` | 列出目前的開關狀態 |

#### 停用機制

停用資源時，檔案會被移動到 `~/.config/custom-skills/disabled/<target>/<type>/` 目錄：

```
~/.config/custom-skills/disabled/
├── claude/
│   ├── skills/
│   │   └── some-disabled-skill/
│   └── commands/
│       └── some-disabled-command.md
├── antigravity/
│   └── ...
├── opencode/
│   └── ...
├── codex/
│   └── skills/
│       └── ...
└── gemini/
    ├── skills/
    │   └── ...
    └── commands/
        └── ...
```

**注意**：停用/啟用後需要重啟對應的 AI 工具才會生效。

#### 配置檔

Toggle 狀態儲存於 `~/.config/custom-skills/toggle-config.yaml`：

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

codex:
  skills:
    enabled: true
    disabled: []

gemini:
  skills:
    enabled: true
    disabled: []
  commands:
    enabled: true
    disabled: []
```

### 互動式 TUI 介面 (TUI)

啟動視覺化管理介面：

```bash
ai-dev tui
```

**功能：**
- 頂部按鈕列：Install / Update / Status / Add Skills / Quit
- Target 下拉選單：切換目標工具（Claude Code / Antigravity / OpenCode / Codex / Gemini CLI）
- Type 下拉選單：切換資源類型（Skills / Commands / Agents / Workflows）
- Sync to Project：勾選時會同步到 custom-skills 專案目錄（僅開發人員需要）
- 資源列表：Checkbox 勾選啟用/停用
- Add Skills 對話框：輸入套件名稱並執行 `npx skills add`
- MCP Config 區塊：檢視並快速開啟各工具的 MCP 設定檔

**MCP Config 區塊：**

TUI 底部顯示目前選擇的工具的 MCP 設定檔資訊：

| 工具 | 設定檔路徑 |
|------|-----------|
| Claude Code | `~/.claude.json` |
| Antigravity | `~/.gemini/antigravity/mcp_config.json` |
| OpenCode | `~/.config/opencode/opencode.json` |
| Codex | `~/.codex/config.json` |
| Gemini CLI | `~/.gemini/settings.json` |

點擊「Open in Editor」可在 VS Code 中開啟設定檔，點擊「Open Folder」可在檔案管理器中開啟。

**ECC Hooks Plugin 區塊：**

TUI 會顯示 ECC Hooks Plugin 的安裝狀態：
- **已安裝**：顯示安裝路徑與「View Config」按鈕
- **未安裝**：顯示安裝指引

安裝方式：
```bash
npx skills add affaan-m/everything-claude-code
```

**快捷鍵：**

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
| `t` | 切換 Standards Profile |
| `v` | 檢視 ECC Hooks 設定 |

### 第三方 Skills 管理

使用 `npx skills` 安裝第三方 Skills：

```bash
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

## 指令總覽

| 指令 | 說明 |
|------|------|
| `ai-dev install` | 首次安裝 AI 開發環境 |
| `ai-dev update` | 每日更新：更新工具與儲存庫 |
| `ai-dev clone` | 分發 Skills 內容到各 AI 工具目錄 |
| `ai-dev project init` | 初始化專案（openspec + uds） |
| `ai-dev project update` | 更新專案配置 |
| `ai-dev status` | 檢查環境狀態與工具版本 |
| `ai-dev list` | 列出已安裝的 Skills、Commands、Agents |
| `ai-dev toggle` | 啟用/停用特定資源 |
| `ai-dev tui` | 啟動互動式終端介面 |
| `ai-dev standards` | 管理標準體系 profiles |
| `ai-dev hooks` | 管理 Claude Code Hooks（計劃中） |

## 開發

本專案使用 `uv` 管理依賴，設定檔位於 `pyproject.toml`。

```bash
# 新增依賴
uv add <package>

# 同步依賴
uv sync

# 本地安裝測試
uv tool install . --force

# 建置套件
uv build
```

## 資源來源

本專案整合多個上游資源：

| 來源 | 說明 | 目錄 |
|------|------|------|
| [universal-dev-standards](https://github.com/AsiaOstrich/universal-dev-standards) | 開發標準規範 | `.standards/` |
| [everything-claude-code](https://github.com/affaan-m/everything-claude-code) | Hooks, Skills, Agents, Commands | `sources/ecc/` |
| [anthropics/skills](https://github.com/anthropics/skills) | 官方 Skills | `sources/anthropic-skills/` |
| [obra/superpowers](https://github.com/obra/superpowers) | Superpowers Skills | `sources/superpowers/` |
| [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) | Obsidian Skills | `sources/obsidian-skills/` |

### ECC (Everything Claude Code) 資源

ECC 提供進階的 Claude Code 工作流程工具：

- **Hooks**: Python 跨平台 hooks（memory-persistence, strategic-compact）
- **Skills**: continuous-learning, eval-harness, security-review, tdd-workflow
- **Agents**: build-error-resolver, e2e-runner, doc-updater, security-reviewer
- **Commands**: /checkpoint, /build-fix, /e2e, /learn, /test-coverage, /eval

詳見 `sources/ecc/README.md`。

### 標準體系 (Standards Profiles)

支援多種標準體系切換：

```bash
# 查看目前狀態
ai-dev standards status

# 列出可用 profiles
ai-dev standards list

# 切換 profile
ai-dev standards switch ecc

# 顯示 profile 內容
ai-dev standards show ecc
```

可用 profiles：
- `uds` - Universal Dev Standards 完整版（預設）
- `ecc` - Everything Claude Code 工作流程
- `minimal` - 最小化配置

**⚠️ 當前限制（臨時實作）**：
- Profile 切換功能目前僅更新設定檔，**不會載入不同的標準內容**
- 所有 profiles 使用相同的 UDS 標準檔案
- 完整的 Profile 架構（包含 `profiles/*.yaml` 定義檔案與標準來源切換）將在後續版本實作

### 上游追蹤系統

所有第三方 repo 的同步狀態記錄在 `upstream/` 目錄：

```bash
# 使用 Skills 進行上游審核
/upstream-sync      # 生成結構化分析報告
/upstream-compare   # AI 生成整合建議
```

詳見 `upstream/README.md`。

### 第三方資源目錄

除了已整合的上游資源,本專案也提供**第三方資源目錄** (`third-party/`),收錄值得關注但尚未整合的外部專案資訊:

```bash
# 瀏覽第三方資源
cat third-party/README.md

# 查看特定專案資訊
cat third-party/catalog/wshobson-agents.md
```

**第三方資源目錄特色**:
- 📋 **參考資訊庫**: 提供專案概述、功能清單、適用場景
- 📝 **手動安裝指南**: 說明如何從 GitHub 取得並整合到自己環境
- ✅ **評估檢查清單**: 幫助判斷專案是否適合您的需求
- 🔄 **漸進式採用**: 從探索 → 評估 → 整合的清晰路徑

**與 upstream/ 的差異**:
- `third-party/` - 待評估資源,手動探索,僅供參考
- `upstream/` - 已整合資源,自動同步,納入標準工作流

詳見 `third-party/README.md`。

## Claude Code Plugin

本專案包含 ECC Hooks Plugin，提供進階的 Claude Code 工作流程：

### ECC Hooks Plugin 安裝

**方式 1：本地開發測試**

```bash
claude --plugin-dir "/path/to/custom-skills/plugins/ecc-hooks"
```

**方式 2：從 Git URL 安裝**

```bash
# 添加 marketplace
claude plugin marketplace add https://github.com/ValorVie/custom-skills.git

# 安裝 plugin
claude plugin install ecc-hooks@custom-skills
```

**方式 3：在會話中使用 slash command**

```
/plugin install ecc-hooks@custom-skills
```

詳見 `plugins/ecc-hooks/README.md`。

## 未來計畫

### Hooks 選用/開關機制

提供細粒度的 hooks 控制：

- **個別 Hook 開關**：在 TUI 中啟用/停用個別 hook
- **事件類型篩選**：按 SessionStart、PreToolUse 等事件分組管理
- **配置持久化**：更新時保留使用者的開關設定
- **CLI 支援**：`ai-dev hooks enable/disable/list`

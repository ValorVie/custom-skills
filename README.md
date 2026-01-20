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
cd ~/.config/custom-skills
uv tool install . --force
```

## 使用方式

安裝後，可在任意目錄使用 `ai-dev` 指令。

```bash
ai-dev --help
```

### 首次安裝 (Install)

執行以下指令進行全新環境設定：

```bash
ai-dev install
```

這會自動：
1. 檢查 Node.js 與 Git。
2. 安裝全域 NPM 工具 (`claude-code`, `openspec`, `gemini-cli`, `skills` 等)。
3. Clone必要的設定儲存庫 (`custom-skills`, `superpowers`, `obsidian-skills` 等)。
4. 複製 Skills 與設定到各個 AI 工具的目錄。
5. 顯示已安裝的 Skills 清單與重複名稱警告。
6. 顯示 `npx skills` 可用指令提示。

#### 可選參數

| 參數 | 說明 |
|------|------|
| `--skip-npm` | 跳過 NPM 套件安裝 |
| `--skip-repos` | 跳過 Git 儲存庫 Clone |
| `--skip-skills` | 跳過複製 Skills |

**範例：**
```bash
# 只 Clone 儲存庫（跳過 NPM 和 Skills 複製）
ai-dev install --skip-npm --skip-skills
```

### 每日維護 (Maintain)

建議每天開始工作前執行，以保持環境最新：

```bash
ai-dev maintain
```

這會自動：
1. 更新全域 NPM 工具。
2. 拉取所有設定儲存庫的最新變更 (`git fetch` + `git reset`)。
3. 重新同步 Skills 與設定。

#### 可選參數

| 參數 | 說明 |
|------|------|
| `--skip-npm` | 跳過 NPM 套件更新 |
| `--skip-repos` | 跳過 Git 儲存庫更新 |
| `--skip-skills` | 跳過複製 Skills |

**範例：**
```bash
# 只更新 Git 儲存庫（跳過 NPM 和 Skills）
ai-dev maintain --skip-npm --skip-skills

# 只更新 NPM 套件（跳過 Git 和 Skills）
ai-dev maintain --skip-repos --skip-skills
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
| `--force`, `-f` | 強制重新初始化（即使已存在） |

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

# 隱藏已停用的資源
ai-dev list --hide-disabled
```

#### 可選參數

| 參數 | 說明 |
|------|------|
| `--target`, `-t` | 目標工具：`claude`, `antigravity`, `opencode` |
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
| `--target`, `-t` | 目標工具：`claude`, `antigravity`, `opencode` |
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
└── opencode/
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
```

### 互動式 TUI 介面 (TUI)

啟動視覺化管理介面：

```bash
ai-dev tui
```

**功能：**
- 頂部按鈕列：Install / Maintain / Status / Add Skills / Quit
- Target 下拉選單：切換目標工具（Claude Code / Antigravity / OpenCode）
- Type 下拉選單：切換資源類型（Skills / Commands / Agents / Workflows）
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

點擊「Open in Editor」可在 VS Code 中開啟設定檔，點擊「Open Folder」可在檔案管理器中開啟。

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
| `ai-dev maintain` | 每日維護：更新工具並同步設定 |
| `ai-dev project init` | 初始化專案（openspec + uds） |
| `ai-dev project update` | 更新專案配置 |
| `ai-dev status` | 檢查環境狀態與工具版本 |
| `ai-dev list` | 列出已安裝的 Skills、Commands、Agents |
| `ai-dev toggle` | 啟用/停用特定資源 |
| `ai-dev tui` | 啟動互動式終端介面 |

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

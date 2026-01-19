# AI 開發環境設定腳本

統一的自動化設定與維護工具，支援 macOS, Linux 與 Windows。

## 前置需求

請先安裝 `uv` (Python 專案管理工具)：

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 使用方式

所有指令均透過 `main.py` 執行。

### 首次安裝 (Install)

執行以下指令進行全新環境設定：

```bash
uv run script/main.py install
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
uv run script/main.py install --skip-npm --skip-skills
```

### 每日維護 (Maintain)

建議每天開始工作前執行，以保持環境最新：

```bash
uv run script/main.py maintain
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
uv run script/main.py maintain --skip-npm --skip-skills

# 只更新 NPM 套件（跳過 Git 和 Skills）
uv run script/main.py maintain --skip-repos --skip-skills
```

### 狀態檢查 (Status)

隨時檢查環境配置狀態：

```bash
uv run script/main.py status
```

這會顯示：
- 核心工具版本 (Node.js, Git)
- NPM 套件安裝狀態（含 `skills` 套件）
- 設定儲存庫狀態

### 列出已安裝資源 (List)

列出各工具已安裝的 Skills、Commands、Agents：

```bash
# 列出 Claude Code 的 Skills
uv run script/main.py list --target claude --type skills

# 列出 Antigravity 的 Workflows
uv run script/main.py list --target antigravity --type workflows

# 列出 OpenCode 的 Agents
uv run script/main.py list --target opencode --type agents

# 顯示已停用的資源
uv run script/main.py list --show-disabled
```

#### 可選參數

| 參數 | 說明 |
|------|------|
| `--target`, `-t` | 目標工具：`claude`, `antigravity`, `opencode` |
| `--type`, `-T` | 資源類型：`skills`, `commands`, `agents`, `workflows` |
| `--show-disabled`, `-d` | 顯示已停用的資源 |

### 啟用/停用資源 (Toggle)

啟用或停用特定工具的特定資源：

```bash
# 停用特定 skill
uv run script/main.py toggle --target claude --type skills --name skill-creator --disable

# 重新啟用
uv run script/main.py toggle --target claude --type skills --name skill-creator --enable

# 查看目前狀態
uv run script/main.py toggle --list

# 停用但不同步（跳過 copy_skills）
uv run script/main.py toggle --target claude --type skills --name foo --disable --no-sync
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
| `--sync/--no-sync` | 操作後是否同步（預設是） |

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
uv run script/main.py tui
```

**功能：**
- 頂部按鈕列：Install / Maintain / Status / Add Skills / Quit
- Target 下拉選單：切換目標工具（Claude Code / Antigravity / OpenCode）
- Type 下拉選單：切換資源類型（Skills / Commands / Agents / Workflows）
- 資源列表：Checkbox 勾選啟用/停用
- Add Skills 對話框：輸入套件名稱並執行 `npx skills add`

**快捷鍵：**

| 按鍵 | 功能 |
|------|------|
| `q` | 退出 |
| `Space` | 切換選中項目 |
| `a` | 全選 |
| `n` | 全取消 |
| `s` | 儲存並同步 |
| `p` | 開啟 Add Skills 對話框 |

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

## 開發

本專案使用 `uv` 管理依賴，設定檔位於 `pyproject.toml`。

```bash
# 新增依賴
uv add <package>

# 同步依賴
uv sync

# 執行測試 (TODO)
# uv run pytest
```

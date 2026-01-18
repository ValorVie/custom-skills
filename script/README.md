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
2. 安裝全域 NPM 工具 (`claude-code`, `openspec`, `gemini-cli` 等)。
3. Clone必要的設定儲存庫 (`custom-skills`, `superpowers` 等)。
4. 複製 Skills 與設定到各個 AI 工具的目錄。

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

**範例：**
```bash
# 只更新 Git 儲存庫（跳過 NPM）
uv run script/main.py maintain --skip-npm

# 只更新 NPM 套件（跳過 Git）
uv run script/main.py maintain --skip-repos
```

### 狀態檢查 (Status)

隨時檢查環境配置狀態：

```bash
uv run script/main.py status
```

這會顯示：
- 核心工具版本 (Node.js, Git)
- NPM 套件安裝狀態
- 設定儲存庫狀態

## 開發

本專案使用 `uv` 管理依賴，設定檔位於 `pyproject.toml`。

```bash
# 新增依賴
uv add <package>

# 執行測試 (TODO)
# uv run pytest
```

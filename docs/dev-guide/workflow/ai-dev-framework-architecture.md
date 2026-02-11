# ai-dev CLI 框架技術架構

> **版本**: 1.0.0
> **更新日期**: 2026-02-12

---

## 概述

`ai-dev` 是 custom-skills 專案的核心 CLI 工具，負責管理多 AI 工具的 Skills、Commands、Agents、Workflows 的安裝、更新與分發。採用 Python + Typer 框架實作，搭配 Rich 進行終端輸出美化。

---

## 技術堆疊

| 元件 | 技術 | 用途 |
|------|------|------|
| CLI 框架 | [Typer](https://typer.tiangolo.com/) | 指令定義與參數解析 |
| TUI 介面 | [Textual](https://textual.textualize.io/) | 互動式終端 UI |
| 終端輸出 | [Rich](https://rich.readthedocs.io/) | 彩色輸出、表格、進度條 |
| 配置格式 | YAML | sources.yaml、toggle config |
| 套件管理 | [uv](https://docs.astral.sh/uv/) | Python 套件管理 |
| 追蹤機制 | SHA-256 Manifest | 檔案分發追蹤與衝突檢測 |

---

## 專案結構

```
script/
├── main.py                    # 進入點，註冊所有指令
├── commands/                  # 指令實作
│   ├── install.py             # 首次安裝
│   ├── update.py              # 日常更新
│   ├── clone.py               # 分發 Skills
│   ├── status.py              # 環境狀態檢查
│   ├── list.py                # 列出已安裝資源
│   ├── toggle.py              # 啟用/停用資源
│   ├── add_repo.py            # 新增上游 repo
│   ├── add_custom_repo.py     # 新增自訂 repo
│   ├── update_custom_repo.py  # 更新自訂 repo
│   ├── test.py                # 測試
│   ├── coverage.py            # 覆蓋率
│   ├── derive_tests.py        # 測試推導
│   ├── project.py             # 專案子指令群
│   ├── standards.py           # Standards 子指令群
│   └── hooks.py               # Hooks 子指令群
├── utils/                     # 共用工具
│   ├── paths.py               # 路徑定義（所有目錄路徑集中管理）
│   ├── shared.py              # 核心邏輯：REPOS、複製、來源追蹤
│   ├── manifest.py            # Manifest 追蹤系統
│   ├── system.py              # 系統工具（指令執行、OS 偵測）
│   ├── custom_repos.py        # 自訂 repo 管理
│   └── git_helpers.py         # Git 操作輔助
└── tui/                       # TUI 互動介面
    └── app.py
```

---

## 指令架構與職責分工

### 核心指令

```
ai-dev
├── install          # 首次安裝（冪等）
├── update           # 日常更新
├── clone            # 分發到各工具目錄
├── status           # 環境狀態檢查
├── list             # 列出已安裝資源
├── toggle           # 啟用/停用特定資源
├── add-repo         # 新增上游 repo
├── add-custom-repo  # 新增自訂 repo
├── update-custom-repo # 更新自訂 repo 設定
├── test             # 執行測試
├── coverage         # 覆蓋率分析
├── derive-tests     # 測試推導
├── tui              # 互動式 TUI 介面
├── project          # 專案子指令群
├── standards        # Standards 子指令群
└── hooks            # Hooks 子指令群
```

### install vs update 設計決策

這兩個指令有明確的職責分工：

| 面向 | `install` | `update` |
|------|-----------|----------|
| **定位** | 首次環境建置 | 日常更新 |
| **冪等性** | 完全冪等（已存在即跳過） | 冪等（只更新有差異的） |
| **前置檢查** | Node.js、Git、Bun、gh | 無 |
| **目錄建立** | 建立所有必要目錄 | 不建立目錄 |
| **缺失 repo** | 自動 clone | 顯示警告，提示執行 install |
| **已有 repo** | 跳過 | fetch + reset --hard |
| **NPM/Bun 套件** | install | install（同效果） |
| **Skills 分發** | 自動執行 `copy_skills()` | 不執行，提示手動跑 `clone` |
| **Shell completion** | 安裝 | 不處理 |
| **Custom repos** | clone 缺失的 | 缺失時顯示警告 |

**設計原則**：
- `install` 是完整的環境建置，可安全重複執行
- `update` 只負責「拉取最新」，不改變環境結構
- 如果 `update` 發現缺失 repo，應引導使用者回到 `install` 補齊，而非自動 clone（避免模糊職責邊界）

### clone 的雙重行為

`clone` 指令會根據執行位置決定行為：

| 執行位置 | 行為 |
|----------|------|
| 任意目錄 | Stage 3：將 `~/.config/custom-skills/` 分發到各工具目錄 |
| custom-skills 開發目錄 | Stage 2 + Stage 3：先整合外部來源到開發目錄，再分發 |

判斷依據：檢查 `pyproject.toml` 中是否包含 `name = "ai-dev"` 且非 `~/.config/custom-skills/` 本身。

---

## 資源管理系統

### 資源類型

| 類型 | 說明 | 共用/專屬 |
|------|------|-----------|
| Skills | 行為規範與知識 | 共用（所有工具） |
| Commands | 可呼叫的指令 | 工具專屬 |
| Agents | 自主代理定義 | 工具專屬 |
| Workflows | 工作流程 | 工具專屬 |

### 上游來源系統

所有第三方 repo 在 `upstream/sources.yaml` 中註冊：

```yaml
sources:
  <name>:
    repo: <github-org/repo>
    branch: main
    local_path: ~/.config/<name>/
    format: claude-code-native | uds
    install_method: ai-dev | plugin | standards | manual
```

#### install_method 說明

| 方法 | 同步方式 | 範例 |
|------|----------|------|
| `ai-dev` | `ai-dev clone` 自動複製到 skills/ | obsidian-skills、anthropic-skills、auto-skill |
| `plugin` | Claude Code Plugin 安裝 | superpowers |
| `standards` | 同步到 .standards/，需手動 diff 合併 | universal-dev-standards |
| `manual` | 需手動比對與複製 | everything-claude-code |

### 新增上游來源的完整步驟

以 `auto-skill` 為例：

1. **`paths.py`** — 新增路徑函式：
   ```python
   def get_auto_skill_dir() -> Path:
       return get_config_dir() / "auto-skill"
   ```

2. **`shared.py`** — 新增到 REPOS dict（供 install clone）：
   ```python
   "auto_skill": (
       "https://github.com/Toolsai/auto-skill.git",
       get_auto_skill_dir,
   ),
   ```

3. **`shared.py`** — 在複製函式中加入複製邏輯（`integrate_to_dev_project` 和 Stage 2 copy）

4. **`shared.py`** — 在 `SOURCE_NAMES` 和 `get_source_skills()` 加入來源追蹤

5. **`update.py`** — 在 repos list 加入新路徑函式

6. **`sources.yaml`** — 註冊上游來源

### 來源追蹤

`get_source_skills()` 函式追蹤每個 skill 的來源：

```
SOURCE_NAMES = {
    "uds":         "universal-dev-standards",
    "obsidian":    "obsidian-skills",
    "anthropic":   "anthropic-skills",
    "ecc":         "everything-claude-code",
    "auto_skill":  "auto-skill",
    "custom":      "custom-skills",
    "user":        "user",
}
```

優先順序：外部來源 > custom-skills 自有 > 使用者自訂

---

## Manifest 追蹤機制

每個目標工具維護一份 `.manifest.yaml`，記錄：

- 資源名稱與路徑
- 來源（custom-skills、third-party）
- 檔案 SHA-256 hash
- 分發時間戳

用途：
- **衝突檢測**：分發前比對 hash，偵測使用者手動修改
- **孤兒清理**：移除已從來源刪除但仍存在於目標的資源
- **差異追蹤**：判斷是否需要更新

---

## Toggle 機制

使用者可針對特定工具停用特定資源：

```bash
ai-dev toggle --target claude --type skills --name auto-skill --disable
```

配置存儲在 `~/.config/ai-dev/toggle.yaml`，在 Stage 3 分發時檢查。

---

## 三階段複製架構

詳見 [copy-architecture.md](copy-architecture.md)。

```
Stage 1: Clone     GitHub repos → ~/.config/<repo>/
Stage 2: Integrate ~/.config/<repos> → custom-skills/skills/  (僅開發目錄)
Stage 3: Distribute custom-skills/ → ~/.claude/, ~/.gemini/, etc.
```

---

## 自訂 Repo 系統

除了內建的 `REPOS` dict，使用者可透過 `add-custom-repo` 新增私有 repo：

```bash
ai-dev add-custom-repo --name my-skills --url https://github.com/user/my-skills.git
```

配置存儲在 `~/.config/ai-dev/custom-repos.yaml`，在 install/update 時一併處理。

---

## 相關文件

| 文件 | 說明 |
|------|------|
| [copy-architecture.md](copy-architecture.md) | 三階段複製流程詳細說明 |
| [DEVELOPMENT-WORKFLOW.md](DEVELOPMENT-WORKFLOW.md) | 開發工作流程 |
| `upstream/sources.yaml` | 上游來源註冊表 |
| `pyproject.toml` | 專案配置與版本定義 |

---

## 版本歷史

| 版本 | 日期 | 變更 |
|------|------|------|
| 1.0.0 | 2026-02-12 | 初版：框架架構、指令職責分工、資源管理系統、上游來源整合流程 |

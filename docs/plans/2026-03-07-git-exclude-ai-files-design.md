# 設計文件：`.git/info/exclude` AI 文件本地排除管理

**日期：** 2026-03-07
**狀態：** 已核准
**範圍：** ai-dev CLI — `project init`、`init-from`、`clone`、`install` 命令

---

## 背景

當 ai-dev 將 AI 設定檔（`.claude/`、`.standards/`、`CLAUDE.md` 等）複製到目標專案時，這些檔案會被 git 追蹤，導致：

1. PR 中出現大量非程式碼的 AI 設定檔（實測 QDM 專案：453 檔、65,000+ 行）
2. git history 被 AI 設定更新汙染
3. 合併衝突風險增加

### 為什麼不用 .gitignore？

調查確認（詳見 `docs/report/2026-03-07-ai-files-gitignore-compatibility.md`）：

| 工具 | .gitignore 設定載入 | .gitignore 工具讀取 | 結論 |
|------|:---:|:---:|------|
| Claude Code | OK | Grep 跳過，Glob/Read 可 | 可行 |
| Codex CLI | OK | 搜尋跳過，直接讀取可 | 可行 |
| OpenCode | OK | 搜尋跳過，直接讀取可 | 可行 |
| Gemini CLI | OK | read_file 拒絕 | 部分可行 |
| Antigravity | **不載入** | 不索引 | **不可行** |

**Antigravity 無法載入 .gitignore 中的設定檔**，但 `.git/info/exclude` 不被工具的 gitignore parser 讀取，因此所有工具都能正常運作。

### 為什麼選擇 `.git/info/exclude`？

- 效果等同 .gitignore（git 不追蹤）
- 不影響任何 AI 工具的設定載入和檔案讀取
- 本地生效，不進入 git（不會影響其他開發者的 .gitignore）
- 由 ai-dev 命令自動管理，開發者無需手動設定

---

## 設計概覽

### 核心流程

```
開發者安裝 ai-dev → ai-dev project init / init-from
  ├─ 複製 AI 文件到專案（現有行為不變）
  ├─ 詢問使用者是否加入本地排除
  ├─ 寫入 .git/info/exclude（標記區塊）
  └─ 記錄到 .ai-dev-project.yaml
```

### 排除清單來源

基於模板內容（以 qdm-ai-base 為例），**排除所有內容，除了明確保留的項目**：

**排除項（寫入 .git/info/exclude）：**

```gitignore
# Directories
.agent/
.atlas/
.claude/
.codex/
.gemini/
.opencode/
.phpstan/
.standards/
.vscode/settings.json
dev-docs/
openspec/

# GitHub AI-specific (not all of .github/)
.github/copilot-instructions.md
.github/prompts/
.github/skills/

# Files
AGENTS.md
CLAUDE.md
GEMINI.md
INSTRUCTIONS.md
.ai-dev-project.yaml
.gitignore-downstream
atlas.toml
phpstan.admin.neon
phpstan.catalog.neon
project-information.md
```

**保留項（不排除）：**

```
.editorconfig
.gitattributes
.gitignore
```

---

## 模組設計

### 新模組：`script/utils/git_exclude.py`

```python
"""管理 .git/info/exclude 中的 AI 文件排除規則（標記區塊）。"""

MARKER_START = "# >>> ai-dev (managed by ai-dev, DO NOT EDIT)"
MARKER_END = "# <<< ai-dev"
```

#### 主要函數

##### `ensure_ai_exclude()`

```python
def ensure_ai_exclude(
    project_dir: Path,
    patterns: list[str],
    dry_run: bool = False,
) -> tuple[bool, list[str], list[str]]:
    """確保 .git/info/exclude 包含 AI 文件排除規則。

    Args:
        project_dir: 專案根目錄
        patterns: 要排除的 pattern 清單
        dry_run: 只檢查不寫入

    Returns:
        (was_modified, added_patterns, skipped_patterns)
        - added_patterns: 成功加入管理區塊的 patterns
        - skipped_patterns: 因使用者已有而跳過的 patterns
    """
```

**邏輯：**
1. 確認 `.git/` 存在，不存在則跳過 + warning
2. 確保 `.git/info/` 目錄存在（必要時建立）
3. 讀取現有 `.git/info/exclude`
4. 掃描區塊外已存在的 patterns → 這些跳過不重複加入
5. 建構/更新管理區塊
6. 寫回檔案

##### `remove_ai_exclude()`

```python
def remove_ai_exclude(project_dir: Path) -> bool:
    """移除 .git/info/exclude 中的 ai-dev 管理區塊。

    Returns:
        bool: 是否有修改
    """
```

##### `get_current_patterns()`

```python
def get_current_patterns(project_dir: Path) -> list[str] | None:
    """讀取目前管理區塊中的 patterns。

    Returns:
        None 如果沒有管理區塊，否則 pattern 清單
    """
```

### `.git/info/exclude` 檔案結構

```bash
# Manually added by user (preserved unconditionally)
.env
node_modules/

# >>> ai-dev (managed by ai-dev, DO NOT EDIT)
# AI tool config directories
.agent/
.atlas/
.claude/
.codex/
.gemini/
.opencode/
.phpstan/
.standards/
.vscode/settings.json
dev-docs/
openspec/

# GitHub AI-specific paths
.github/copilot-instructions.md
.github/prompts/
.github/skills/

# AI instruction files
AGENTS.md
CLAUDE.md
GEMINI.md
INSTRUCTIONS.md
.ai-dev-project.yaml
.gitignore-downstream
atlas.toml
phpstan.admin.neon
phpstan.catalog.neon
project-information.md
# <<< ai-dev
```

### 內容級比對規則

| 情境 | 處理方式 |
|------|---------|
| Pattern 已在區塊外（使用者手動加的） | 不加入區塊內，記錄為 skipped |
| Pattern 在區塊內已存在 | 不重複（冪等） |
| 新版模板新增 pattern | 下次 update 時加入區塊 |
| 新版模板移除 pattern | 下次 update 時從區塊移除 |
| 使用者區塊外的手動項目 | 永遠不動 |

---

## `.ai-dev-project.yaml` 擴展

在現有 schema 上新增 `git_exclude` 區段：

```yaml
template:
  name: "qdm-ai-base"
  url: "https://github.com/..."
  branch: "main"
  initialized_at: "2026-03-07T15:30:00+08:00"
  last_updated: "2026-03-07T15:30:00+08:00"

managed_files:          # 現有（不動）
  - "CLAUDE.md"
  - ".standards/commit.yaml"

git_exclude:            # 新增
  enabled: true         # 使用者選擇是否啟用
  version: "1"          # 排除規則版本，用於偵測更新
  patterns:             # 目前管理的 patterns
    - ".agent/"
    - ".claude/"
    - ".codex/"
    # ...
  keep_tracked:         # 明確不排除的項目
    - ".editorconfig"
    - ".gitattributes"
    - ".gitignore"
```

**用途：**
- `enabled`: 使用者選「否」時設為 false，後續命令不再詢問
- `version`: 偵測模板排除規則是否有更新
- `patterns`: 記錄當前管理的 patterns，用於 diff 更新
- `keep_tracked`: 記錄不排除項目，防止未來誤加

---

## 命令整合

### 1. `ai-dev project init`

**插入位置：** 檔案複製完成後

```python
# project.py init() — 檔案複製完成後
if is_git_repo(target_dir):
    patterns = derive_exclude_patterns(template_dir, keep_tracked=[...])
    choice = prompt_exclude_choice(patterns)
    if choice == "yes":
        modified, added, skipped = ensure_ai_exclude(target_dir, patterns)
        update_project_tracking(target_dir, git_exclude_enabled=True, patterns=patterns)
    elif choice == "no":
        update_project_tracking(target_dir, git_exclude_enabled=False)
```

### 2. `ai-dev init-from`

**插入位置：** `merge_gitignore_downstream()` 之後

```python
# init_from.py — merge_gitignore_downstream() 之後
if is_git_repo(cwd):
    patterns = derive_exclude_patterns(template_dir, keep_tracked=[...])
    # 首次 init: 詢問使用者
    # --update: 讀取 .ai-dev-project.yaml，自動更新（如果 enabled）
    ...
```

**`--update` 模式特殊邏輯：**
1. 讀取 `.ai-dev-project.yaml` 的 `git_exclude`
2. 如果 `enabled: false` → 跳過
3. 如果 `enabled: true` → 比對 old patterns vs new patterns → 更新區塊

### 3. `ai-dev clone`（`--sync-project` 時）

**插入位置：** `integrate_to_dev_project()` 之後

```python
# clone.py — integrate_to_dev_project() 之後
tracking = read_project_tracking(project_dir)
if tracking and tracking.git_exclude.enabled:
    ensure_ai_exclude(project_dir, tracking.git_exclude.patterns)
```

**注意：** clone 不詢問使用者，只根據已有的 `.ai-dev-project.yaml` 設定行事。

### 4. `ai-dev install`（`--sync-project` 時）

**插入位置：** `copy_skills()` 之後

與 `clone` 相同邏輯：讀取 tracking，如果 enabled 則確認 exclude。

---

## 使用者互動設計

### 首次初始化

```
$ ai-dev project init

✓ AI 文件已複製到專案

? 是否將 AI 文件加入本地排除？(.git/info/exclude)
  這些檔案在本地正常運作，AI 工具可正常讀取
  但不會出現在 git status、commit 或 PR 中

  [1] 是，加入排除（推薦）
  [2] 否，保持 git 追蹤
  [3] 檢視排除清單

> 3

  將排除以下 23 個項目：
    .agent/  .atlas/  .claude/  .codex/  .gemini/  .opencode/
    .phpstan/  .standards/  .vscode/settings.json
    dev-docs/  openspec/
    .github/copilot-instructions.md  .github/prompts/  .github/skills/
    AGENTS.md  CLAUDE.md  GEMINI.md  INSTRUCTIONS.md
    .ai-dev-project.yaml  .gitignore-downstream
    atlas.toml  phpstan.admin.neon  phpstan.catalog.neon
    project-information.md

  保留追蹤（不排除）：
    .editorconfig  .gitattributes  .gitignore

  [1] 是，加入排除（推薦）
  [2] 否，保持 git 追蹤

> 1

✓ 已將 23 個 AI 相關項目加入 .git/info/exclude
ℹ 此設定記錄於 .ai-dev-project.yaml，更新時自動同步
```

### 更新時（--update）

```
$ ai-dev init-from --update

✓ 模板已更新
✓ .git/info/exclude 已同步（新增 2 項，移除 1 項）
  + .github/workflows/ai-review.yml
  + .agents/
  - .atlas/
```

### 手動啟用/停用

```
$ ai-dev project exclude --enable    # 啟用排除
$ ai-dev project exclude --disable   # 停用排除
$ ai-dev project exclude --list      # 檢視目前排除清單
```

---

## 排除清單推導邏輯

### `derive_exclude_patterns()`

```python
def derive_exclude_patterns(
    template_dir: Path,
    keep_tracked: list[str] | None = None,
) -> list[str]:
    """從模板目錄內容推導排除 patterns。

    掃描 template_dir 的第一層內容，排除：
    - keep_tracked 中的項目（預設：.editorconfig, .gitattributes, .gitignore）
    - .git/ 目錄
    - .gitignore-downstream 檔案本身不排除（由 gitignore_downstream 模組處理）
      → 更正：.gitignore-downstream 也排除

    目錄加 '/' 後綴，檔案直接用檔名。
    .github/ 特殊處理：只排除 AI 相關子路徑。
    """
```

**`.github/` 特殊處理：**
- 不排除整個 `.github/`（使用者可能有 workflows、issue templates）
- 只排除模板中 `.github/` 下的具體項目：`copilot-instructions.md`、`prompts/`、`skills/`

---

## 邊界條件

| 狀況 | 處理方式 |
|------|---------|
| 非 git repo（`.git/` 不存在） | 跳過，顯示 `[yellow]非 git 倉庫，跳過本地排除設定[/yellow]` |
| `.git/info/` 目錄不存在 | 建立目錄（`mkdir -p`） |
| `exclude` 檔案不存在 | 建立空檔案後寫入 |
| 已有 ai-dev 管理區塊 | 更新區塊內容（冪等） |
| 使用者已手動加了某些 patterns | 不重複加入區塊內 |
| `--dry-run` 模式 | 只顯示會做什麼，不寫入 |
| `.ai-dev-project.yaml` 不存在 | 跳過 git_exclude 邏輯（非 ai-dev 管理的專案） |
| 使用者之前選了「否」 | 後續命令不再詢問（讀 `git_exclude.enabled: false`） |
| 使用者改主意 | `ai-dev project exclude --enable` 手動啟用 |

---

## 測試計畫

```
tests/test_git_exclude.py

# 基本功能
test_ensure_creates_info_directory        # .git/info/ 不存在時建立
test_ensure_creates_exclude_file          # exclude 檔案不存在時建立
test_ensure_adds_marker_block             # 首次加入管理區塊
test_ensure_updates_existing_block        # 更新已有區塊
test_ensure_preserves_other_entries       # 不動使用者手動項目
test_ensure_skips_duplicate_patterns      # 使用者已有的 pattern 不重複
test_ensure_skips_non_git_repo            # 非 git repo 跳過
test_remove_cleans_block                  # 移除管理區塊
test_remove_preserves_other_entries       # 移除時不動使用者項目
test_idempotent_multiple_calls            # 多次呼叫結果一致

# 推導邏輯
test_derive_patterns_from_template        # 從模板內容推導
test_derive_excludes_keep_tracked         # 保留項不出現在排除清單
test_derive_github_specific_paths         # .github/ 只排除 AI 子路徑

# 整合
test_project_tracking_git_exclude_schema  # .ai-dev-project.yaml 新欄位
test_update_detects_pattern_changes       # 更新時偵測新增/移除
test_get_current_patterns                 # 讀取目前管理的 patterns

# 內容比對
test_skip_pattern_exists_outside_block    # 區塊外已有相同 pattern
test_pattern_removed_from_template        # 模板移除 pattern → 區塊更新
test_pattern_added_to_template            # 模板新增 pattern → 區塊更新
```

---

## 不做的事

- **不整合 rulesync** — 獨立工具，使用者可自行搭配
- **不修改 .gitignore** — 避免 Antigravity 相容性問題
- **不自動 git rm** — 不刪除已追蹤的檔案，只防止未來追蹤
- **不處理全域分發** — 只處理專案層級的排除

---

## 實作順序

1. `script/utils/git_exclude.py` — 核心模組
2. `tests/test_git_exclude.py` — 測試
3. `script/commands/project.py` — 整合 `project init` + `project exclude`
4. `script/commands/init_from.py` — 整合 `init-from` + `init-from --update`
5. `script/commands/clone.py` — 整合 `clone --sync-project`
6. `script/commands/install.py` — 整合 `install --sync-project`
7. `script/utils/project_tracking.py` — 擴展 schema

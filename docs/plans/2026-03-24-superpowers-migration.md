# Superpowers 安裝機制遷移與 Codex 支援 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將 OpenCode superpowers 從 git clone + symlink 遷移至 plugin 機制，並新增 Codex superpowers 的 clone + symlink 支援。

**Architecture:** 在 `shared.py` 中新增遷移/同步函式，由 pipeline services 的 repos/state phase 呼叫。OpenCode 改為寫入 `opencode.json` plugin 陣列；Codex 沿用 git clone + symlink 模式（與舊版 OpenCode 同理）。

**Tech Stack:** Python 3.12+, Typer CLI, Rich console, pathlib, json

---

## 檔案結構

| 操作 | 檔案 | 職責 |
|------|------|------|
| Modify | `script/utils/paths.py` | 新增 Codex superpowers / agents skills 路徑函式 |
| Modify | `script/utils/shared.py` | 替換 OpenCode superpowers 函式 → 遷移；新增 Codex superpowers 函式 |
| Modify | `script/services/repos/refresh.py` | 更新 install/update repos phase |
| Modify | `script/services/state/auto_skill.py` | 替換 OpenCode → Codex symlink 刷新 |
| Modify | `script/commands/install.py` | 更新 imports |
| Modify | `script/commands/update.py` | 更新 imports |
| Modify | `docs/ai-dev指令與資料流參考.md` | 同步文檔 |

---

### Task 1: 新增路徑函式

**Files:**
- Modify: `script/utils/paths.py`

- [ ] **Step 1: 新增 `get_codex_superpowers_dir` 和 `get_agents_skills_dir`**

在 `get_codex_config_dir()` 之後加入：

```python
def get_codex_superpowers_dir() -> Path:
    """回傳 Codex 專用的 superpowers 目錄。"""
    return get_codex_config_dir() / "superpowers"


def get_agents_skills_dir() -> Path:
    """回傳 Codex agents skills 目錄（~/.agents/skills）。"""
    return get_home_dir() / ".agents" / "skills"
```

- [ ] **Step 2: 驗證 import 正常**

Run: `python -c "from script.utils.paths import get_codex_superpowers_dir, get_agents_skills_dir; print(get_codex_superpowers_dir()); print(get_agents_skills_dir())"`

Expected: 輸出 `~/.codex/superpowers` 和 `~/.agents/skills` 的完整路徑

- [ ] **Step 3: Commit**

```bash
git add script/utils/paths.py
git commit -m "feat(paths): 新增 Codex superpowers 與 agents skills 路徑函式"
```

---

### Task 2: 新增 Codex superpowers 同步函式

**Files:**
- Modify: `script/utils/shared.py`
- Modify: `script/utils/paths.py` (import only)

- [ ] **Step 1: 更新 paths import 區塊**

在 `shared.py` 的 `from .paths import (...)` 區塊中新增（保留既有的 `get_opencode_superpowers_dir`，deprecated stub 仍需使用）：

```python
    get_codex_superpowers_dir,
    get_agents_skills_dir,
```

- [ ] **Step 2: 重新命名常數**

將 `OPENCODE_SUPERPOWERS_URL` 重新命名為 `SUPERPOWERS_GIT_URL`（全檔替換），值不變：

```python
SUPERPOWERS_GIT_URL = "https://github.com/obra/superpowers.git"
```

- [ ] **Step 3: 新增 `sync_codex_superpowers_repo()`**

在 `sync_opencode_superpowers_repo()` 之後新增：

```python
def sync_codex_superpowers_repo() -> Path:
    """確保 Codex superpowers 儲存庫存在，若有就 pull，否則 clone。"""
    repo_path = get_codex_superpowers_dir()
    repo_path.parent.mkdir(parents=True, exist_ok=True)

    if (repo_path / ".git").exists():
        console.print(
            f"[green]更新 Codex superpowers[/green] → [dim]{shorten_path(repo_path)}[/dim]"
        )
        run_command(["git", "pull"], cwd=str(repo_path), check=False)
    else:
        console.print(
            f"[green]Clone Codex superpowers[/green] → [dim]{shorten_path(repo_path)}[/dim]"
        )
        run_command(
            ["git", "clone", SUPERPOWERS_GIT_URL, str(repo_path)], check=False
        )

    return repo_path
```

- [ ] **Step 4: 新增 `refresh_codex_superpowers_symlinks()`**

```python
def refresh_codex_superpowers_symlinks(repo_path: Path) -> bool:
    """建立或刷新 Codex superpowers 的 ~/.agents/skills/superpowers symlink。"""
    skills_src = repo_path / "skills"
    skills_dst = get_agents_skills_dir() / "superpowers"

    if not skills_src.exists():
        console.print("[red]✗ 找不到 Codex superpowers skills 目錄[/red]")
        return False

    skills_dst.parent.mkdir(parents=True, exist_ok=True)

    # 清理既有路徑（symlink / junction / 真實目錄）
    if skills_dst.exists() or skills_dst.is_symlink():
        try:
            skills_dst.unlink()
        except (OSError, PermissionError):
            shutil.rmtree(skills_dst)

    try:
        os.symlink(skills_src, skills_dst)
        method = "symlink"
    except OSError:
        try:
            shutil.copytree(skills_src, skills_dst)
            method = "copy"
        except OSError as e:
            console.print(f"[red]✗ 建立 Codex superpowers 連結失敗：{e}[/red]")
            return False

    if method == "symlink":
        console.print("[green]✓[/green] Codex superpowers symlink 已更新")
    else:
        console.print(
            "[green]✓[/green] Codex superpowers 已複製"
            "（無 symlink 權限，使用檔案複製）"
        )
    console.print(f"[dim]驗證：[/dim] ls -l {shorten_path(skills_dst)}")
    return True
```

- [ ] **Step 5: Commit**

```bash
git add script/utils/shared.py
git commit -m "feat(shared): 新增 Codex superpowers sync 與 symlink 函式"
```

---

### Task 3: OpenCode superpowers 遷移函式

**Files:**
- Modify: `script/utils/shared.py`

- [ ] **Step 1: 新增 `migrate_opencode_superpowers()`**

在 `sync_opencode_superpowers_repo()` 之前（或替換之後）新增：

```python
def _ensure_opencode_superpowers_plugin(opencode_json_path: Path) -> bool:
    """確保 opencode.json 的 plugin 陣列包含 superpowers 條目。

    僅在需要新增條目時才寫入檔案，避免不必要的格式變動。
    寫入前備份原始內容，失敗時還原。
    """
    plugin_entry = f"superpowers@git+{SUPERPOWERS_GIT_URL}"

    if not opencode_json_path.exists():
        console.print(f"[yellow]⚠ {shorten_path(opencode_json_path)} 不存在，跳過 plugin 注入[/yellow]")
        return False

    try:
        original_content = opencode_json_path.read_text(encoding="utf-8")
        config = json.loads(original_content)
    except (json.JSONDecodeError, OSError) as e:
        console.print(f"[yellow]⚠ 讀取 opencode.json 失敗：{e}[/yellow]")
        return False

    plugins = config.get("plugin", [])
    if not isinstance(plugins, list):
        plugins = []

    # 檢查是否已有 superpowers 條目（不一定完全相同，只要包含 superpowers）
    has_superpowers = any("superpowers" in p for p in plugins if isinstance(p, str))
    if has_superpowers:
        console.print("[dim]OpenCode superpowers plugin 已存在[/dim]")
        return True

    # 需要新增 — 備份後寫入
    plugins.append(plugin_entry)
    config["plugin"] = plugins

    try:
        opencode_json_path.write_text(
            json.dumps(config, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        console.print(f"[green]✓[/green] 已將 superpowers plugin 加入 {shorten_path(opencode_json_path)}")
        return True
    except OSError as e:
        # 寫入失敗，還原原始內容
        try:
            opencode_json_path.write_text(original_content, encoding="utf-8")
        except OSError:
            pass
        console.print(f"[red]✗ 寫入 opencode.json 失敗：{e}[/red]")
        return False


def migrate_opencode_superpowers() -> None:
    """偵測並遷移 OpenCode superpowers 從 symlink 方式到 plugin 方式。

    僅在偵測到舊安裝時才執行遷移（包含 plugin 注入）。
    若無舊安裝且 plugin 條目不存在，也會注入 plugin 條目。
    """
    old_repo = get_opencode_superpowers_dir()
    old_plugin_link = get_opencode_plugin_dir() / "superpowers.js"
    old_skills_link = get_opencode_config_dir() / "skills" / "superpowers"
    opencode_json = get_opencode_config_dir() / "opencode.json"

    has_old_setup = (
        (old_repo / ".git").exists()
        or old_plugin_link.is_symlink()
        or old_plugin_link.exists()
        or old_skills_link.is_symlink()
        or old_skills_link.exists()
    )

    if has_old_setup:
        console.print("[yellow]偵測到舊版 OpenCode superpowers 安裝，正在遷移...[/yellow]")

        # 移除舊 symlinks
        for old_link in (old_plugin_link, old_skills_link):
            if old_link.is_symlink() or old_link.exists():
                try:
                    old_link.unlink()
                    console.print(f"[dim]已移除：{shorten_path(old_link)}[/dim]")
                except (OSError, PermissionError):
                    shutil.rmtree(old_link, ignore_errors=True)
                    console.print(f"[dim]已移除：{shorten_path(old_link)}[/dim]")

        # 移除舊 repo（先檢查是否為 symlink，避免誤刪目標）
        if old_repo.is_symlink():
            old_repo.unlink()
            console.print(f"[dim]已移除舊 repo symlink：{shorten_path(old_repo)}[/dim]")
        elif (old_repo / ".git").exists():
            shutil.rmtree(old_repo, ignore_errors=True)
            console.print(f"[dim]已移除舊 repo：{shorten_path(old_repo)}[/dim]")

        # 遷移：注入 plugin 條目
        _ensure_opencode_superpowers_plugin(opencode_json)
    else:
        # 非遷移情境：僅在 opencode.json 存在時靜默檢查 plugin
        if opencode_json.exists():
            _ensure_opencode_superpowers_plugin(opencode_json)
```

- [ ] **Step 2: 保留 `sync_opencode_superpowers_repo` 和 `refresh_opencode_superpowers_symlinks` 但標記 deprecated**

```python
def sync_opencode_superpowers_repo() -> Path:
    """[Deprecated] 改用 migrate_opencode_superpowers()。保留供舊程式碼參照。"""
    migrate_opencode_superpowers()
    return get_opencode_superpowers_dir()


def refresh_opencode_superpowers_symlinks(repo_path: Path) -> bool:
    """[Deprecated] OpenCode superpowers 已遷移為 plugin 機制，symlink 不再需要。"""
    return True
```

- [ ] **Step 3: 驗證 import 正常**

Run: `python -c "from script.utils.shared import migrate_opencode_superpowers, sync_codex_superpowers_repo, refresh_codex_superpowers_symlinks; print('OK')"`

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add script/utils/shared.py
git commit -m "feat(shared): 新增 OpenCode superpowers 遷移函式，舊函式標記 deprecated"
```

---

### Task 4: 更新 pipeline repos phase

**Files:**
- Modify: `script/services/repos/refresh.py`

- [ ] **Step 1: 更新 imports**

```python
from script.utils.paths import (
    get_antigravity_config_dir,
    get_claude_agents_dir,
    get_claude_config_dir,
    get_claude_workflows_dir,
    get_codex_config_dir,
    get_codex_superpowers_dir,  # 新增
    get_config_dir,
    get_custom_skills_dir,
    get_gemini_cli_config_dir,
    get_obsidian_skills_dir,
    get_anthropic_skills_dir,
    get_ecc_dir,
    get_auto_skill_repo_dir,
    get_opencode_config_dir,
    get_superpowers_dir,
    get_uds_dir,
)
from script.utils.shared import (
    REPOS,
    migrate_opencode_superpowers,           # 替換 sync_opencode_superpowers_repo
    sync_codex_superpowers_repo,            # 新增
    refresh_codex_superpowers_symlinks,     # 新增
)
```

- [ ] **Step 2: 更新 `_run_install_repos_phase()`**

將 lines 181-182：
```python
    repo_path = sync_opencode_superpowers_repo()
    console.print(f"[dim]OpenCode superpowers repo: {repo_path}[/dim]")
```

替換為：
```python
    # OpenCode superpowers：遷移至 plugin 機制
    migrate_opencode_superpowers()

    # Codex superpowers：clone + symlink
    codex_sp_repo = sync_codex_superpowers_repo()
    refresh_codex_superpowers_symlinks(codex_sp_repo)
```

- [ ] **Step 3: 更新 `_run_update_repos_phase()`**

將 line 204：
```python
    sync_opencode_superpowers_repo()
```

替換為：
```python
    # OpenCode superpowers：遷移至 plugin 機制
    migrate_opencode_superpowers()
```

從 repos 清單（lines 206-215）中移除 `get_opencode_config_dir() / "superpowers"`，並新增 Codex superpowers：

```python
    repos = [
        get_custom_skills_dir(),
        get_superpowers_dir(),
        get_uds_dir(),
        get_codex_superpowers_dir(),        # 替換 opencode superpowers
        get_obsidian_skills_dir(),
        get_anthropic_skills_dir(),
        get_ecc_dir(),
        get_auto_skill_repo_dir(),
    ]
```

在 repos 更新迴圈結束、custom repos 處理之前，加入 Codex symlink 刷新：

```python
    # Codex superpowers symlink 刷新
    codex_sp = get_codex_superpowers_dir()
    if codex_sp.exists() and (codex_sp / ".git").exists():
        refresh_codex_superpowers_symlinks(codex_sp)
```

- [ ] **Step 4: Commit**

```bash
git add script/services/repos/refresh.py
git commit -m "feat(repos): 更新 repos phase 支援 OpenCode 遷移與 Codex superpowers"
```

---

### Task 5: 更新 pipeline state phase

**Files:**
- Modify: `script/services/state/auto_skill.py`

- [ ] **Step 1: 替換 imports 和邏輯**

將整個檔案更新為：

```python
from __future__ import annotations

from rich.console import Console

from script.models.execution_plan import ExecutionPlan
from script.utils.auto_skill_state import refresh_auto_skill_state
from script.utils.paths import get_codex_superpowers_dir
from script.utils.shared import refresh_codex_superpowers_symlinks

console = Console()

def run_state_phase(*, plan: ExecutionPlan) -> None:
    """Run state refresh work for a pipeline plan."""
    if plan.dry_run:
        console.print(
            f"[dim][dry-run] {plan.command_name}: state[/dim]"
        )
        return

    if plan.command_name in {"install", "update"}:
        repo_path = get_codex_superpowers_dir()
        if (repo_path / ".git").exists():
            refresh_codex_superpowers_symlinks(repo_path)

    state_dir = refresh_auto_skill_state()
    if state_dir is not None:
        console.print(
            f"[green]✓[/green] auto-skill canonical state 已同步 → [dim]{state_dir}[/dim]"
        )
```

- [ ] **Step 2: Commit**

```bash
git add script/services/state/auto_skill.py
git commit -m "refactor(state): 替換 OpenCode symlink 為 Codex superpowers symlink 刷新"
```

---

### Task 6: 更新 install 和 update 命令 imports

**Files:**
- Modify: `script/commands/install.py`
- Modify: `script/commands/update.py`

- [ ] **Step 1: 更新 `install.py` imports**

將 lines 38-39：
```python
    sync_opencode_superpowers_repo,
    refresh_opencode_superpowers_symlinks,
```

替換為：
```python
    migrate_opencode_superpowers,
    sync_codex_superpowers_repo,
    refresh_codex_superpowers_symlinks,
```

- [ ] **Step 2: 更新 `install.py` 使用處**

將 lines 268-270：
```python
        # OpenCode superpowers：獨立於 Claude Code 追蹤路徑
        repo_path = sync_opencode_superpowers_repo()
        refresh_opencode_superpowers_symlinks(repo_path)
```

替換為：
```python
        # OpenCode superpowers：遷移至 plugin 機制
        migrate_opencode_superpowers()

        # Codex superpowers：clone + symlink
        codex_sp_repo = sync_codex_superpowers_repo()
        refresh_codex_superpowers_symlinks(codex_sp_repo)
```

- [ ] **Step 3: 更新 `update.py` imports**

將 lines 30-31：
```python
    sync_opencode_superpowers_repo,
    refresh_opencode_superpowers_symlinks,
```

替換為：
```python
    migrate_opencode_superpowers,
    sync_codex_superpowers_repo,
    refresh_codex_superpowers_symlinks,
```

- [ ] **Step 4: 更新 `update.py` paths imports**

在 `update.py` 的 `from ..utils.paths import (...)` 區塊中新增 `get_codex_superpowers_dir`：

```python
from ..utils.paths import (
    get_custom_skills_dir,
    get_superpowers_dir,
    get_uds_dir,
    get_opencode_config_dir,
    get_codex_superpowers_dir,      # 新增
    get_obsidian_skills_dir,
    get_anthropic_skills_dir,
    get_ecc_dir,
    get_auto_skill_repo_dir,
)
```

- [ ] **Step 5: 更新 `update.py` 使用處**

將 line 227：
```python
        opencode_superpowers_repo = sync_opencode_superpowers_repo()
```

替換為：
```python
        # OpenCode superpowers：遷移至 plugin 機制
        migrate_opencode_superpowers()
```

將 line 233（repos 清單）中的：
```python
            get_opencode_config_dir() / "superpowers",
```

替換為：
```python
            get_codex_superpowers_dir(),
```

將 line 333：
```python
        refresh_opencode_superpowers_symlinks(opencode_superpowers_repo)
```

替換為：
```python
        # Codex superpowers symlink 刷新
        codex_sp = get_codex_superpowers_dir()
        if codex_sp.exists() and (codex_sp / ".git").exists():
            refresh_codex_superpowers_symlinks(codex_sp)
```

- [ ] **Step 5: Commit**

```bash
git add script/commands/install.py script/commands/update.py
git commit -m "refactor(commands): 更新 install/update 支援 OpenCode 遷移與 Codex superpowers"
```

---

### Task 7: 驗證與整合測試

- [ ] **Step 1: 本地安裝測試版本**

Run: `uv tool install . --force`

Expected: 安裝成功

- [ ] **Step 2: 測試 dry-run**

Run: `ai-dev update --dry-run`

Expected: 顯示執行計畫，無錯誤

- [ ] **Step 3: 測試實際 update**

Run: `ai-dev update --only repos`

Expected:
- 看到「偵測到舊版 OpenCode superpowers 安裝，正在遷移...」（若有舊安裝）
- 看到 superpowers plugin 加入 opencode.json
- `~/.codex/superpowers` 成功更新
- `~/.agents/skills/superpowers` symlink 刷新

- [ ] **Step 4: 驗證結果**

```bash
# OpenCode: 確認 plugin 已加入
cat ~/.config/opencode/opencode.json | python -m json.tool | grep superpowers

# OpenCode: 確認舊安裝已移除
ls -la ~/.config/opencode/superpowers 2>&1  # 應不存在
ls -la ~/.config/opencode/plugins/superpowers.js 2>&1  # 應不存在
ls -la ~/.config/opencode/skills/superpowers 2>&1  # 應不存在

# Codex: 確認 repo 存在且 symlink 正確
ls -la ~/.codex/superpowers/.git
ls -la ~/.agents/skills/superpowers
```

- [ ] **Step 5: Commit 確認（如有修正）**

若測試過程發現需要修正，修正後提交。

---

### Task 8: 更新文檔

**Files:**
- Modify: `docs/ai-dev指令與資料流參考.md`

- [ ] **Step 1: 更新資料流說明**

在「環境層：安裝、更新、分發」段落中新增 superpowers 處理說明：

```markdown
#### Superpowers 處理

| 工具 | 安裝方式 | 路徑 |
|------|----------|------|
| Claude Code | Plugin 系統自動管理 | `~/.claude/plugins/` |
| OpenCode | `opencode.json` plugin 陣列 | `plugin: ["superpowers@git+https://..."]` |
| Codex | git clone + symlink | `~/.codex/superpowers` → `~/.agents/skills/superpowers` |

- `ai-dev install`：OpenCode 遷移至 plugin（若偵測到舊 symlink 安裝自動清除）；Codex clone + symlink
- `ai-dev update`：OpenCode 遷移檢查；Codex git pull + symlink 刷新
```

- [ ] **Step 2: Commit**

```bash
git add docs/ai-dev指令與資料流參考.md
git commit -m "docs: 更新 superpowers 處理方式說明"
```

---

### Task 9: 清理 deprecated 函式（可選，建議下一版本）

待所有使用點確認遷移完成後，可安全移除：
- `sync_opencode_superpowers_repo()`
- `refresh_opencode_superpowers_symlinks()`
- `OPENCODE_SUPERPOWERS_URL` 常數（已重新命名為 `SUPERPOWERS_GIT_URL`）

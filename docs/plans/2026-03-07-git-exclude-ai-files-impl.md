# `.git/info/exclude` AI 文件本地排除 — 實作計畫

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 讓 ai-dev 在複製 AI 文件到專案時，自動將這些文件加入 `.git/info/exclude`，使 AI 工具正常運作但不汙染 git history 和 PR。

**Architecture:** 新增 `git_exclude.py` 工具模組（參考 `gitignore_downstream.py` 的標記區塊模式），在 4 個命令（`project init`、`init-from`、`clone`、`install`）的檔案複製完成後呼叫。排除清單從模板內容動態推導，狀態記錄於 `.ai-dev-project.yaml`。

**Tech Stack:** Python 3.13、pytest、typer、rich、pyyaml

**設計文件：** `docs/plans/2026-03-07-git-exclude-ai-files-design.md`

---

## Task 1: 核心模組 `git_exclude.py` — 標記區塊管理

**Files:**
- Create: `script/utils/git_exclude.py`
- Test: `tests/test_git_exclude.py`

### Step 1: 寫 failing test — 基本區塊建立

```python
# tests/test_git_exclude.py
"""git_exclude.py 的單元測試。"""

from pathlib import Path

import pytest

from script.utils.git_exclude import (
    MARKER_END,
    MARKER_START,
    ensure_ai_exclude,
    remove_ai_exclude,
    get_current_patterns,
)


def _make_git_repo(tmp_path: Path) -> Path:
    """建立模擬 git repo（含 .git/info/ 目錄）。"""
    git_dir = tmp_path / ".git" / "info"
    git_dir.mkdir(parents=True)
    return tmp_path


class TestEnsureAiExclude:
    """ensure_ai_exclude 測試。"""

    def test_creates_exclude_file_if_missing(self, tmp_path: Path) -> None:
        """exclude 檔案不存在時建立並寫入區塊。"""
        project = _make_git_repo(tmp_path)
        patterns = [".claude/", "CLAUDE.md"]

        modified, added, skipped = ensure_ai_exclude(project, patterns)

        assert modified is True
        assert added == [".claude/", "CLAUDE.md"]
        assert skipped == []

        content = (project / ".git" / "info" / "exclude").read_text()
        assert MARKER_START in content
        assert ".claude/" in content
        assert "CLAUDE.md" in content
        assert MARKER_END in content

    def test_creates_info_directory_if_missing(self, tmp_path: Path) -> None:
        """.git/info/ 不存在時建立。"""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        # 不建立 info/

        patterns = [".claude/"]
        modified, added, skipped = ensure_ai_exclude(tmp_path, patterns)

        assert modified is True
        assert (tmp_path / ".git" / "info" / "exclude").exists()

    def test_skips_non_git_repo(self, tmp_path: Path) -> None:
        """非 git repo 時跳過。"""
        patterns = [".claude/"]
        modified, added, skipped = ensure_ai_exclude(tmp_path, patterns)

        assert modified is False
        assert added == []

    def test_preserves_existing_entries(self, tmp_path: Path) -> None:
        """不動使用者手動項目。"""
        project = _make_git_repo(tmp_path)
        exclude = project / ".git" / "info" / "exclude"
        exclude.write_text(".env\nnode_modules/\n", encoding="utf-8")

        patterns = [".claude/", "CLAUDE.md"]
        ensure_ai_exclude(project, patterns)

        content = exclude.read_text()
        assert ".env" in content
        assert "node_modules/" in content
        assert ".claude/" in content

    def test_skips_patterns_already_outside_block(self, tmp_path: Path) -> None:
        """使用者已手動加的 pattern 不重複。"""
        project = _make_git_repo(tmp_path)
        exclude = project / ".git" / "info" / "exclude"
        exclude.write_text(".claude/\n", encoding="utf-8")

        patterns = [".claude/", ".gemini/", "CLAUDE.md"]
        modified, added, skipped = ensure_ai_exclude(project, patterns)

        assert modified is True
        assert ".claude/" in skipped
        assert ".gemini/" in added
        content = exclude.read_text()
        # .claude/ 只出現一次（區塊外的那個）
        lines = [l.strip() for l in content.splitlines() if l.strip() == ".claude/"]
        assert len(lines) == 1

    def test_updates_existing_block(self, tmp_path: Path) -> None:
        """已有管理區塊時更新內容。"""
        project = _make_git_repo(tmp_path)
        exclude = project / ".git" / "info" / "exclude"
        old_content = (
            ".env\n"
            f"{MARKER_START}\n"
            ".claude/\n"
            f"{MARKER_END}\n"
        )
        exclude.write_text(old_content, encoding="utf-8")

        patterns = [".claude/", ".gemini/", "CLAUDE.md"]
        modified, added, skipped = ensure_ai_exclude(project, patterns)

        assert modified is True
        content = exclude.read_text()
        assert ".gemini/" in content
        assert "CLAUDE.md" in content
        assert content.count(MARKER_START) == 1

    def test_idempotent(self, tmp_path: Path) -> None:
        """多次呼叫結果一致。"""
        project = _make_git_repo(tmp_path)
        patterns = [".claude/", "CLAUDE.md"]

        ensure_ai_exclude(project, patterns)
        content1 = (project / ".git" / "info" / "exclude").read_text()

        ensure_ai_exclude(project, patterns)
        content2 = (project / ".git" / "info" / "exclude").read_text()

        assert content1 == content2

    def test_dry_run_does_not_write(self, tmp_path: Path) -> None:
        """dry_run 模式不寫入。"""
        project = _make_git_repo(tmp_path)
        patterns = [".claude/"]

        modified, added, skipped = ensure_ai_exclude(project, patterns, dry_run=True)

        assert modified is False
        assert added == [".claude/"]
        assert not (project / ".git" / "info" / "exclude").exists()


class TestRemoveAiExclude:
    """remove_ai_exclude 測試。"""

    def test_removes_block(self, tmp_path: Path) -> None:
        """移除管理區塊。"""
        project = _make_git_repo(tmp_path)
        exclude = project / ".git" / "info" / "exclude"
        content = (
            ".env\n\n"
            f"{MARKER_START}\n"
            ".claude/\n"
            f"{MARKER_END}\n"
        )
        exclude.write_text(content, encoding="utf-8")

        result = remove_ai_exclude(project)

        assert result is True
        new_content = exclude.read_text()
        assert MARKER_START not in new_content
        assert ".claude/" not in new_content
        assert ".env" in new_content

    def test_no_block_returns_false(self, tmp_path: Path) -> None:
        """無區塊時回傳 False。"""
        project = _make_git_repo(tmp_path)
        exclude = project / ".git" / "info" / "exclude"
        exclude.write_text(".env\n", encoding="utf-8")

        result = remove_ai_exclude(project)
        assert result is False


class TestGetCurrentPatterns:
    """get_current_patterns 測試。"""

    def test_returns_patterns(self, tmp_path: Path) -> None:
        """回傳目前區塊內的 patterns。"""
        project = _make_git_repo(tmp_path)
        exclude = project / ".git" / "info" / "exclude"
        content = (
            f"{MARKER_START}\n"
            ".claude/\n"
            "CLAUDE.md\n"
            f"{MARKER_END}\n"
        )
        exclude.write_text(content, encoding="utf-8")

        patterns = get_current_patterns(project)
        assert patterns == [".claude/", "CLAUDE.md"]

    def test_returns_none_when_no_block(self, tmp_path: Path) -> None:
        """無區塊時回傳 None。"""
        project = _make_git_repo(tmp_path)
        exclude = project / ".git" / "info" / "exclude"
        exclude.write_text(".env\n", encoding="utf-8")

        assert get_current_patterns(project) is None
```

### Step 2: 跑測試確認失敗

Run: `cd /Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills && uv run pytest tests/test_git_exclude.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'script.utils.git_exclude'`

### Step 3: 實作核心模組

```python
# script/utils/git_exclude.py
"""管理 .git/info/exclude 中的 AI 文件排除規則（標記區塊）。"""

from pathlib import Path

from rich.console import Console

console = Console()

MARKER_START = "# >>> ai-dev (managed by ai-dev, DO NOT EDIT)"
MARKER_END = "# <<< ai-dev"


def _get_exclude_path(project_dir: Path) -> Path | None:
    """取得 .git/info/exclude 路徑，非 git repo 回傳 None。"""
    git_dir = project_dir / ".git"
    if not git_dir.is_dir():
        return None
    info_dir = git_dir / "info"
    info_dir.mkdir(parents=True, exist_ok=True)
    return info_dir / "exclude"


def _find_block(lines: list[str]) -> tuple[int | None, int | None]:
    """尋找管理區塊的起止行號。"""
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        stripped = line.rstrip("\n\r")
        if stripped == MARKER_START:
            start_idx = i
        elif stripped == MARKER_END and start_idx is not None:
            end_idx = i
            break
    return start_idx, end_idx


def _collect_existing_patterns(lines: list[str], start_idx: int | None, end_idx: int | None) -> set[str]:
    """收集區塊外已存在的 patterns（去除註釋和空行）。"""
    existing = set()
    for i, line in enumerate(lines):
        if start_idx is not None and end_idx is not None and start_idx <= i <= end_idx:
            continue
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            existing.add(stripped)
    return existing


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
    """
    exclude_path = _get_exclude_path(project_dir)
    if exclude_path is None:
        return False, [], []

    # 讀取現有內容
    if exclude_path.is_file():
        existing = exclude_path.read_text(encoding="utf-8")
    else:
        existing = ""

    lines = existing.splitlines(keepends=True)
    start_idx, end_idx = _find_block(lines)
    has_block = start_idx is not None and end_idx is not None

    # 收集區塊外已有的 patterns
    outside_patterns = _collect_existing_patterns(lines, start_idx, end_idx)

    # 分類：要加入的 vs 跳過的
    added = []
    skipped = []
    for p in patterns:
        if p.strip() in outside_patterns:
            skipped.append(p)
        else:
            added.append(p)

    if dry_run:
        return False, added, skipped

    # 建構區塊內容
    block_lines = [MARKER_START + "\n"]
    for p in added:
        block_lines.append(p + "\n")
    block_lines.append(MARKER_END + "\n")

    if has_block:
        # 替換既有區塊
        lines[start_idx : end_idx + 1] = block_lines
        result = "".join(lines)
    else:
        # 附加到尾部
        result = existing
        if result and not result.endswith("\n"):
            result += "\n"
        if result:
            result += "\n"
        result += "".join(block_lines)

    if result and not result.endswith("\n"):
        result += "\n"

    exclude_path.write_text(result, encoding="utf-8")
    return True, added, skipped


def remove_ai_exclude(project_dir: Path) -> bool:
    """移除 .git/info/exclude 中的 ai-dev 管理區塊。

    Returns:
        bool: 是否有修改
    """
    exclude_path = _get_exclude_path(project_dir)
    if exclude_path is None or not exclude_path.is_file():
        return False

    existing = exclude_path.read_text(encoding="utf-8")
    lines = existing.splitlines(keepends=True)
    start_idx, end_idx = _find_block(lines)

    if start_idx is None or end_idx is None:
        return False

    del lines[start_idx : end_idx + 1]
    # 移除區塊前的空行
    if start_idx > 0 and start_idx <= len(lines) and lines[start_idx - 1].strip() == "":
        del lines[start_idx - 1]

    result = "".join(lines)
    if result and not result.endswith("\n"):
        result += "\n"

    exclude_path.write_text(result, encoding="utf-8")
    return True


def get_current_patterns(project_dir: Path) -> list[str] | None:
    """讀取目前管理區塊中的 patterns。

    Returns:
        None 如果沒有管理區塊，否則 pattern 清單
    """
    exclude_path = _get_exclude_path(project_dir)
    if exclude_path is None or not exclude_path.is_file():
        return None

    existing = exclude_path.read_text(encoding="utf-8")
    lines = existing.splitlines()
    start_idx, end_idx = _find_block([l + "\n" for l in lines])

    if start_idx is None or end_idx is None:
        return None

    patterns = []
    for line in lines[start_idx + 1 : end_idx]:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            patterns.append(stripped)
    return patterns
```

### Step 4: 跑測試確認通過

Run: `cd /Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills && uv run pytest tests/test_git_exclude.py -v`
Expected: ALL PASS

### Step 5: Commit

```bash
git add script/utils/git_exclude.py tests/test_git_exclude.py
git commit -m "功能(git-exclude): 新增 .git/info/exclude 標記區塊管理模組"
```

---

## Task 2: 排除清單推導函數 `derive_exclude_patterns()`

**Files:**
- Modify: `script/utils/git_exclude.py`
- Modify: `tests/test_git_exclude.py`

### Step 1: 寫 failing test

在 `tests/test_git_exclude.py` 末尾新增：

```python
from script.utils.git_exclude import derive_exclude_patterns


class TestDeriveExcludePatterns:
    """derive_exclude_patterns 測試。"""

    def test_derives_from_template(self, tmp_path: Path) -> None:
        """從模板內容推導排除清單。"""
        template = tmp_path / "template"
        template.mkdir()
        (template / ".claude").mkdir()
        (template / ".standards").mkdir()
        (template / "CLAUDE.md").touch()
        (template / ".editorconfig").touch()
        (template / ".gitattributes").touch()
        (template / ".gitignore").touch()

        patterns = derive_exclude_patterns(template)

        assert ".claude/" in patterns
        assert ".standards/" in patterns
        assert "CLAUDE.md" in patterns
        # 保留項不在排除清單
        assert ".editorconfig" not in patterns
        assert ".gitattributes" not in patterns
        assert ".gitignore" not in patterns

    def test_github_specific_paths(self, tmp_path: Path) -> None:
        """.github/ 只排除 AI 相關子路徑。"""
        template = tmp_path / "template"
        template.mkdir()
        github = template / ".github"
        github.mkdir()
        (github / "skills").mkdir()
        (github / "prompts").mkdir()
        (github / "copilot-instructions.md").touch()

        patterns = derive_exclude_patterns(template)

        assert ".github/skills/" in patterns
        assert ".github/prompts/" in patterns
        assert ".github/copilot-instructions.md" in patterns
        assert ".github/" not in patterns  # 整個 .github/ 不在

    def test_excludes_git_directory(self, tmp_path: Path) -> None:
        """.git 目錄不出現在排除清單。"""
        template = tmp_path / "template"
        template.mkdir()
        (template / ".git").mkdir()
        (template / "CLAUDE.md").touch()

        patterns = derive_exclude_patterns(template)

        assert ".git" not in patterns
        assert ".git/" not in patterns

    def test_custom_keep_tracked(self, tmp_path: Path) -> None:
        """自訂保留項。"""
        template = tmp_path / "template"
        template.mkdir()
        (template / "CLAUDE.md").touch()
        (template / "custom-keep.txt").touch()

        patterns = derive_exclude_patterns(
            template, keep_tracked=[".editorconfig", ".gitattributes", ".gitignore", "custom-keep.txt"]
        )

        assert "CLAUDE.md" in patterns
        assert "custom-keep.txt" not in patterns

    def test_adds_ai_dev_project_yaml(self, tmp_path: Path) -> None:
        """.ai-dev-project.yaml 永遠包含在排除清單。"""
        template = tmp_path / "template"
        template.mkdir()
        (template / "CLAUDE.md").touch()

        patterns = derive_exclude_patterns(template)

        assert ".ai-dev-project.yaml" in patterns
```

### Step 2: 跑測試確認失敗

Run: `uv run pytest tests/test_git_exclude.py::TestDeriveExcludePatterns -v`
Expected: FAIL — `ImportError`

### Step 3: 實作 `derive_exclude_patterns()`

在 `script/utils/git_exclude.py` 新增：

```python
DEFAULT_KEEP_TRACKED = [".editorconfig", ".gitattributes", ".gitignore"]

# .github/ 下需要特別處理的 AI 子路徑
GITHUB_AI_PATHS = ["skills", "prompts", "copilot-instructions.md"]

# 永遠加入排除的項目（即使模板中沒有）
ALWAYS_EXCLUDE = [".ai-dev-project.yaml"]


def derive_exclude_patterns(
    template_dir: Path,
    keep_tracked: list[str] | None = None,
) -> list[str]:
    """從模板目錄內容推導排除 patterns。

    掃描 template_dir 的第一層內容，排除 keep_tracked 中的項目。
    .github/ 特殊處理：只排除 AI 相關子路徑。

    Args:
        template_dir: 模板目錄
        keep_tracked: 不排除的項目清單（預設：.editorconfig, .gitattributes, .gitignore）

    Returns:
        排除 pattern 清單
    """
    if keep_tracked is None:
        keep_tracked = DEFAULT_KEEP_TRACKED

    keep_set = set(keep_tracked)
    patterns = []

    for item in sorted(template_dir.iterdir()):
        name = item.name

        # 跳過 .git 目錄和保留項
        if name == ".git" or name in keep_set:
            continue

        # .github/ 特殊處理
        if name == ".github" and item.is_dir():
            for sub in sorted(item.iterdir()):
                if sub.name in GITHUB_AI_PATHS:
                    if sub.is_dir():
                        patterns.append(f".github/{sub.name}/")
                    else:
                        patterns.append(f".github/{sub.name}")
            continue

        # 一般項目
        if item.is_dir():
            patterns.append(f"{name}/")
        else:
            patterns.append(name)

    # 永遠加入的項目
    for always in ALWAYS_EXCLUDE:
        if always not in patterns:
            patterns.append(always)

    return patterns
```

### Step 4: 跑測試確認通過

Run: `uv run pytest tests/test_git_exclude.py -v`
Expected: ALL PASS

### Step 5: Commit

```bash
git add script/utils/git_exclude.py tests/test_git_exclude.py
git commit -m "功能(git-exclude): 新增排除清單推導函數"
```

---

## Task 3: `.ai-dev-project.yaml` schema 擴展

**Files:**
- Modify: `script/utils/project_tracking.py:53-72`
- Modify: `tests/test_git_exclude.py`

### Step 1: 寫 failing test

在 `tests/test_git_exclude.py` 新增：

```python
from script.utils.project_tracking import (
    load_tracking_file,
    save_tracking_file,
)


class TestProjectTrackingGitExclude:
    """project_tracking git_exclude 擴展測試。"""

    def test_save_and_load_git_exclude(self, tmp_path: Path) -> None:
        """git_exclude 欄位可正常存取。"""
        data = {
            "template": {"name": "test"},
            "managed_files": ["CLAUDE.md"],
            "git_exclude": {
                "enabled": True,
                "version": "1",
                "patterns": [".claude/", "CLAUDE.md"],
                "keep_tracked": [".editorconfig"],
            },
        }
        save_tracking_file(data, tmp_path)
        loaded = load_tracking_file(tmp_path)

        assert loaded is not None
        assert loaded["git_exclude"]["enabled"] is True
        assert loaded["git_exclude"]["patterns"] == [".claude/", "CLAUDE.md"]

    def test_backward_compatible_without_git_exclude(self, tmp_path: Path) -> None:
        """無 git_exclude 欄位時不影響既有功能。"""
        data = {
            "template": {"name": "test"},
            "managed_files": ["CLAUDE.md"],
        }
        save_tracking_file(data, tmp_path)
        loaded = load_tracking_file(tmp_path)

        assert loaded is not None
        assert "git_exclude" not in loaded
```

### Step 2: 跑測試確認通過

Run: `uv run pytest tests/test_git_exclude.py::TestProjectTrackingGitExclude -v`
Expected: PASS（現有的 `save_tracking_file` / `load_tracking_file` 是通用 dict 操作，不做 schema 驗證，所以直接相容）

### Step 3: 在 `project_tracking.py` 新增 helper 函數

在 `script/utils/project_tracking.py` 末尾新增：

```python
def get_git_exclude_config(project_dir: Path | None = None) -> dict | None:
    """取得 git_exclude 設定。

    Returns:
        dict: git_exclude 設定，不存在時回傳 None
    """
    data = load_tracking_file(project_dir)
    if data is None:
        return None
    return data.get("git_exclude")


def update_git_exclude_config(
    enabled: bool,
    patterns: list[str],
    keep_tracked: list[str],
    version: str = "1",
    project_dir: Path | None = None,
) -> None:
    """更新 .ai-dev-project.yaml 中的 git_exclude 設定。"""
    data = load_tracking_file(project_dir)
    if data is None:
        data = {}

    data["git_exclude"] = {
        "enabled": enabled,
        "version": version,
        "patterns": sorted(patterns),
        "keep_tracked": sorted(keep_tracked),
    }
    save_tracking_file(data, project_dir)
```

### Step 4: 補充 test 驗證新 helper

```python
from script.utils.project_tracking import (
    get_git_exclude_config,
    update_git_exclude_config,
)


class TestGitExcludeHelpers:

    def test_update_and_get(self, tmp_path: Path) -> None:
        save_tracking_file({"template": {"name": "test"}, "managed_files": []}, tmp_path)
        update_git_exclude_config(
            enabled=True,
            patterns=[".claude/", "CLAUDE.md"],
            keep_tracked=[".editorconfig"],
            project_dir=tmp_path,
        )
        config = get_git_exclude_config(tmp_path)
        assert config is not None
        assert config["enabled"] is True
        assert ".claude/" in config["patterns"]

    def test_get_returns_none_when_missing(self, tmp_path: Path) -> None:
        save_tracking_file({"template": {"name": "test"}, "managed_files": []}, tmp_path)
        assert get_git_exclude_config(tmp_path) is None
```

### Step 5: 跑測試確認通過

Run: `uv run pytest tests/test_git_exclude.py -v`
Expected: ALL PASS

### Step 6: Commit

```bash
git add script/utils/project_tracking.py tests/test_git_exclude.py
git commit -m "功能(project-tracking): 擴展 git_exclude 設定支援"
```

---

## Task 4: 整合 `project init` 命令

**Files:**
- Modify: `script/commands/project.py:512-533`
- Modify: `script/utils/git_exclude.py` (新增 `prompt_exclude_choice()`)

### Step 1: 在 `git_exclude.py` 新增互動提示函數

```python
import typer


def prompt_exclude_choice(patterns: list[str]) -> str:
    """詢問使用者是否加入本地排除。

    Returns:
        "yes" | "no"
    """
    console.print()
    console.print("[bold]? 是否將 AI 文件加入本地排除？(.git/info/exclude)[/bold]")
    console.print("[dim]  這些檔案在本地正常運作，AI 工具可正常讀取[/dim]")
    console.print("[dim]  但不會出現在 git status、commit 或 PR 中[/dim]")
    console.print()

    choice = typer.prompt(
        "  [1] 是，加入排除（推薦）\n"
        "  [2] 否，保持 git 追蹤\n"
        "  [3] 檢視排除清單\n\n"
        "請選擇",
        default="1",
    )

    if choice == "3":
        console.print()
        console.print(f"[bold]將排除以下 {len(patterns)} 個項目：[/bold]")
        for p in patterns:
            console.print(f"  [dim]{p}[/dim]")
        console.print()
        choice = typer.prompt(
            "  [1] 是，加入排除（推薦）\n"
            "  [2] 否，保持 git 追蹤\n\n"
            "請選擇",
            default="1",
        )

    return "yes" if choice == "1" else "no"


def print_exclude_result(added: list[str], skipped: list[str]) -> None:
    """顯示排除結果。"""
    console.print(
        f"[green]✓ 已將 {len(added)} 個 AI 相關項目加入 .git/info/exclude[/green]"
    )
    if skipped:
        console.print(
            f"[dim]  （{len(skipped)} 個項目已存在，跳過重複）[/dim]"
        )
    console.print("[dim]ℹ 此設定記錄於 .ai-dev-project.yaml，更新時自動同步[/dim]")
```

### Step 2: 修改 `project.py` init() 函數

在 `script/commands/project.py` 的 `init()` 函數中，在 line 533（`"下一步"` 提示之前）插入：

```python
    # 本地排除 AI 文件
    git_dir = target_dir / ".git"
    if git_dir.is_dir():
        from script.utils.git_exclude import (
            derive_exclude_patterns,
            ensure_ai_exclude,
            prompt_exclude_choice,
            print_exclude_result,
        )
        from script.utils.project_tracking import update_git_exclude_config

        patterns = derive_exclude_patterns(template_dir)
        choice = prompt_exclude_choice(patterns)

        if choice == "yes":
            modified, added, skipped = ensure_ai_exclude(target_dir, patterns)
            if modified:
                print_exclude_result(added, skipped)
            update_git_exclude_config(
                enabled=True,
                patterns=patterns,
                keep_tracked=[".editorconfig", ".gitattributes", ".gitignore"],
                project_dir=target_dir,
            )
        else:
            update_git_exclude_config(
                enabled=False,
                patterns=patterns,
                keep_tracked=[".editorconfig", ".gitattributes", ".gitignore"],
                project_dir=target_dir,
            )
            console.print("[dim]ℹ 已記錄選擇，後續可用 ai-dev project exclude --enable 啟用[/dim]")
```

### Step 3: 手動測試

Run: `cd /tmp && mkdir test-project && cd test-project && git init && ai-dev project init`
Expected: 看到排除選擇提示，選 1 後確認 `.git/info/exclude` 有管理區塊

### Step 4: Commit

```bash
git add script/utils/git_exclude.py script/commands/project.py
git commit -m "功能(project-init): 整合 .git/info/exclude 本地排除"
```

---

## Task 5: 整合 `init-from` 命令

**Files:**
- Modify: `script/commands/init_from.py:177-198` (首次 init)
- Modify: `script/commands/init_from.py:261-275` (--update 模式)

### Step 1: 修改首次 init（line 182 之後，line 184 之前）

```python
    # 本地排除 AI 文件
    git_dir = cwd / ".git"
    if git_dir.is_dir():
        from script.utils.git_exclude import (
            derive_exclude_patterns,
            ensure_ai_exclude,
            prompt_exclude_choice,
            print_exclude_result,
            DEFAULT_KEEP_TRACKED,
        )
        from script.utils.project_tracking import update_git_exclude_config

        patterns = derive_exclude_patterns(target_dir)
        choice = prompt_exclude_choice(patterns)

        if choice == "yes":
            modified, added, skipped = ensure_ai_exclude(cwd, patterns)
            if modified:
                print_exclude_result(added, skipped)
            # 記錄於即將建立的 tracking file 中（在 create_tracking_file 之前設定）
            _git_exclude_config = {
                "enabled": True,
                "version": "1",
                "patterns": sorted(patterns),
                "keep_tracked": sorted(DEFAULT_KEEP_TRACKED),
            }
        else:
            _git_exclude_config = {
                "enabled": False,
                "version": "1",
                "patterns": sorted(patterns),
                "keep_tracked": sorted(DEFAULT_KEEP_TRACKED),
            }
```

然後在 `create_tracking_file()` 之後追加：

```python
    # 寫入 git_exclude 設定
    if git_dir.is_dir():
        tracking = load_tracking_file(cwd)
        if tracking and "_git_exclude_config" in dir():
            tracking["git_exclude"] = _git_exclude_config
            save_tracking_file(tracking, cwd)
```

### Step 2: 修改 --update 模式（line 267 之後）

```python
    # 同步 .git/info/exclude
    git_dir = cwd / ".git"
    if git_dir.is_dir():
        from script.utils.project_tracking import get_git_exclude_config
        from script.utils.git_exclude import (
            derive_exclude_patterns,
            ensure_ai_exclude,
            DEFAULT_KEEP_TRACKED,
        )

        exclude_config = get_git_exclude_config(cwd)
        if exclude_config and exclude_config.get("enabled"):
            new_patterns = derive_exclude_patterns(template_dir)
            old_patterns = set(exclude_config.get("patterns", []))
            new_set = set(new_patterns)

            added_new = new_set - old_patterns
            removed = old_patterns - new_set

            modified, added, skipped = ensure_ai_exclude(cwd, new_patterns)
            if modified:
                changes = []
                if added_new:
                    changes.append(f"新增 {len(added_new)} 項")
                if removed:
                    changes.append(f"移除 {len(removed)} 項")
                if changes:
                    console.print(f"[green]✓ .git/info/exclude 已同步（{', '.join(changes)}）[/green]")

            # 更新 tracking
            from script.utils.project_tracking import update_git_exclude_config
            update_git_exclude_config(
                enabled=True,
                patterns=new_patterns,
                keep_tracked=DEFAULT_KEEP_TRACKED,
                project_dir=cwd,
            )
```

### Step 3: 手動測試

Run: 在有 `.ai-dev-project.yaml` 的專案中執行 `ai-dev init-from --update`
Expected: 看到 exclude 同步訊息

### Step 4: Commit

```bash
git add script/commands/init_from.py
git commit -m "功能(init-from): 整合 .git/info/exclude 本地排除"
```

---

## Task 6: 整合 `clone` 和 `install` 命令

**Files:**
- Modify: `script/commands/clone.py:131-138`
- Modify: `script/commands/install.py:306`

### Step 1: 修改 `clone.py`

在 `clone.py` line 132（`"分發完成"` 之前）插入：

```python
    # 確認專案層級的 .git/info/exclude
    if is_dev_dir and dev_project_root:
        from script.utils.project_tracking import get_git_exclude_config
        from script.utils.git_exclude import ensure_ai_exclude

        exclude_config = get_git_exclude_config(dev_project_root)
        if exclude_config and exclude_config.get("enabled"):
            patterns = exclude_config.get("patterns", [])
            if patterns:
                modified, _, _ = ensure_ai_exclude(dev_project_root, patterns)
                if modified:
                    console.print("[dim]✓ .git/info/exclude 已確認同步[/dim]")
```

### Step 2: 修改 `install.py`

在 `install.py` line 306（`copy_skills()` 之後）插入相同邏輯：

```python
    # 確認專案層級的 .git/info/exclude
    if sync_project:
        cwd = Path.cwd()
        from script.utils.project_tracking import get_git_exclude_config
        from script.utils.git_exclude import ensure_ai_exclude

        exclude_config = get_git_exclude_config(cwd)
        if exclude_config and exclude_config.get("enabled"):
            patterns = exclude_config.get("patterns", [])
            if patterns:
                modified, _, _ = ensure_ai_exclude(cwd, patterns)
                if modified:
                    console.print("[dim]✓ .git/info/exclude 已確認同步[/dim]")
```

### Step 3: 手動測試

Run: `ai-dev clone` 在有 `.ai-dev-project.yaml` 的開發專案中
Expected: 看到 exclude 確認訊息

### Step 4: Commit

```bash
git add script/commands/clone.py script/commands/install.py
git commit -m "功能(clone/install): 整合 .git/info/exclude 確認同步"
```

---

## Task 7: `project exclude` 子命令

**Files:**
- Modify: `script/commands/project.py`

### Step 1: 新增子命令

在 `script/commands/project.py` 新增 `exclude` 命令：

```python
@app.command()
def exclude(
    enable: bool = typer.Option(None, "--enable", help="啟用本地排除"),
    disable: bool = typer.Option(None, "--disable", help="停用本地排除"),
    show: bool = typer.Option(False, "--list", "-l", help="檢視目前排除清單"),
):
    """管理 AI 文件的本地排除設定 (.git/info/exclude)。"""
    from script.utils.project_tracking import (
        get_git_exclude_config,
        update_git_exclude_config,
        load_tracking_file,
    )
    from script.utils.git_exclude import (
        ensure_ai_exclude,
        remove_ai_exclude,
        get_current_patterns,
        derive_exclude_patterns,
        print_exclude_result,
        DEFAULT_KEEP_TRACKED,
    )

    cwd = Path.cwd()

    if show:
        patterns = get_current_patterns(cwd)
        if patterns:
            console.print(f"[bold]目前排除 {len(patterns)} 個項目：[/bold]")
            for p in patterns:
                console.print(f"  {p}")
        else:
            console.print("[dim]尚未設定本地排除[/dim]")
        return

    tracking = load_tracking_file(cwd)
    if tracking is None:
        console.print("[yellow]此專案未使用 ai-dev 模板管理[/yellow]")
        raise typer.Exit(1)

    if enable:
        config = get_git_exclude_config(cwd)
        patterns = config["patterns"] if config and config.get("patterns") else []
        if not patterns:
            # 嘗試從模板推導
            template_name = tracking.get("template", {}).get("name", "")
            template_dir = Path.home() / ".config" / template_name
            if template_dir.exists():
                patterns = derive_exclude_patterns(template_dir)

        if patterns:
            modified, added, skipped = ensure_ai_exclude(cwd, patterns)
            if modified:
                print_exclude_result(added, skipped)
            update_git_exclude_config(
                enabled=True,
                patterns=patterns,
                keep_tracked=DEFAULT_KEEP_TRACKED,
                project_dir=cwd,
            )
        else:
            console.print("[yellow]無法推導排除清單[/yellow]")

    elif disable:
        removed = remove_ai_exclude(cwd)
        if removed:
            console.print("[yellow]已移除 .git/info/exclude 中的 ai-dev 管理區塊[/yellow]")
        update_git_exclude_config(
            enabled=False,
            patterns=get_git_exclude_config(cwd).get("patterns", []) if get_git_exclude_config(cwd) else [],
            keep_tracked=DEFAULT_KEEP_TRACKED,
            project_dir=cwd,
        )
        console.print("[dim]ℹ 已停用本地排除[/dim]")

    else:
        console.print("[dim]使用 --enable、--disable 或 --list[/dim]")
```

### Step 2: 手動測試

```bash
ai-dev project exclude --list
ai-dev project exclude --disable
ai-dev project exclude --enable
```

### Step 3: Commit

```bash
git add script/commands/project.py
git commit -m "功能(project-exclude): 新增手動管理本地排除子命令"
```

---

## 完成摘要

| Task | 內容 | 檔案 |
|------|------|------|
| 1 | 核心模組：標記區塊管理 | `git_exclude.py` + tests |
| 2 | 排除清單推導 | `git_exclude.py` + tests |
| 3 | project_tracking schema 擴展 | `project_tracking.py` + tests |
| 4 | 整合 `project init` | `project.py` |
| 5 | 整合 `init-from` + `--update` | `init_from.py` |
| 6 | 整合 `clone` + `install` | `clone.py` + `install.py` |
| 7 | `project exclude` 子命令 | `project.py` |

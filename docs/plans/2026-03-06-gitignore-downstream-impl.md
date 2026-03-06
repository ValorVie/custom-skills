# .gitignore-downstream 實作計畫

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 讓模版 repo 透過 `.gitignore-downstream` 宣告下游專案應忽略的路徑，`init-from` 自動在目標 `.gitignore` 管理標記區塊。

**Architecture:** 新增 `gitignore_downstream.py` 模組處理標記區塊的插入/替換/移除，`smart_merge.py` 排除該檔案不複製，`init_from.py` 在合併流程後呼叫區塊合併。

**Tech Stack:** Python 3.13, pathlib, pytest

**Design:** `docs/plans/2026-03-06-gitignore-downstream-design.md`

---

### Task 1: gitignore_downstream 模組 — 核心邏輯

**Files:**
- Create: `script/utils/gitignore_downstream.py`
- Test: `tests/test_gitignore_downstream.py`

**Step 1: Write the failing tests**

建立 `tests/test_gitignore_downstream.py`：

```python
"""gitignore_downstream.py 的單元測試。"""

from pathlib import Path

import pytest

from script.utils.gitignore_downstream import (
    MARKER_END,
    MARKER_START,
    merge_gitignore_downstream,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ── merge_gitignore_downstream ───────────────────────────────────────────────


class TestMergeGitignoreDownstream:
    """merge_gitignore_downstream 整合測試。"""

    def test_no_downstream_file_skips(self, tmp_path: Path) -> None:
        """模版無 .gitignore-downstream 時不動目標。"""
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        target_dir = tmp_path / "target"
        target_dir.mkdir()
        _write(target_dir / ".gitignore", "node_modules\n")

        result = merge_gitignore_downstream(
            template_dir=template_dir,
            target_dir=target_dir,
            template_name="my-template",
        )

        assert result is False
        assert (target_dir / ".gitignore").read_text() == "node_modules\n"

    def test_first_init_creates_block(self, tmp_path: Path) -> None:
        """首次初始化：目標有 .gitignore，附加標記區塊。"""
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        _write(template_dir / ".gitignore-downstream", ".atlas/\n")

        target_dir = tmp_path / "target"
        target_dir.mkdir()
        _write(target_dir / ".gitignore", "node_modules\n")

        result = merge_gitignore_downstream(
            template_dir=template_dir,
            target_dir=target_dir,
            template_name="my-template",
        )

        assert result is True
        content = (target_dir / ".gitignore").read_text()
        assert "node_modules" in content
        assert MARKER_START.format(name="my-template") in content
        assert ".atlas/" in content
        assert MARKER_END.format(name="my-template") in content

    def test_first_init_no_existing_gitignore(self, tmp_path: Path) -> None:
        """目標無 .gitignore 時建立新檔。"""
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        _write(template_dir / ".gitignore-downstream", ".atlas/\n")

        target_dir = tmp_path / "target"
        target_dir.mkdir()

        result = merge_gitignore_downstream(
            template_dir=template_dir,
            target_dir=target_dir,
            template_name="my-template",
        )

        assert result is True
        content = (target_dir / ".gitignore").read_text()
        assert MARKER_START.format(name="my-template") in content
        assert ".atlas/" in content

    def test_update_replaces_existing_block(self, tmp_path: Path) -> None:
        """--update：替換既有標記區塊。"""
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        _write(template_dir / ".gitignore-downstream", ".atlas/\n.stubs/\n")

        target_dir = tmp_path / "target"
        target_dir.mkdir()
        existing = (
            "node_modules\n"
            f"{MARKER_START.format(name='my-template')}\n"
            ".atlas/\n"
            f"{MARKER_END.format(name='my-template')}\n"
        )
        _write(target_dir / ".gitignore", existing)

        result = merge_gitignore_downstream(
            template_dir=template_dir,
            target_dir=target_dir,
            template_name="my-template",
        )

        assert result is True
        content = (target_dir / ".gitignore").read_text()
        assert ".stubs/" in content
        assert content.count(MARKER_START.format(name="my-template")) == 1

    def test_downstream_deleted_removes_block(self, tmp_path: Path) -> None:
        """模版刪除 .gitignore-downstream 時，移除目標區塊。"""
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        # 無 .gitignore-downstream

        target_dir = tmp_path / "target"
        target_dir.mkdir()
        existing = (
            "node_modules\n"
            f"{MARKER_START.format(name='my-template')}\n"
            ".atlas/\n"
            f"{MARKER_END.format(name='my-template')}\n"
        )
        _write(target_dir / ".gitignore", existing)

        result = merge_gitignore_downstream(
            template_dir=template_dir,
            target_dir=target_dir,
            template_name="my-template",
            remove_if_missing=True,
        )

        assert result is True
        content = (target_dir / ".gitignore").read_text()
        assert "node_modules" in content
        assert MARKER_START.format(name="my-template") not in content
        assert ".atlas/" not in content

    def test_preserves_trailing_newline(self, tmp_path: Path) -> None:
        """確保合併後檔案以換行結尾。"""
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        _write(template_dir / ".gitignore-downstream", ".atlas/")

        target_dir = tmp_path / "target"
        target_dir.mkdir()
        _write(target_dir / ".gitignore", "node_modules\n")

        merge_gitignore_downstream(
            template_dir=template_dir,
            target_dir=target_dir,
            template_name="my-template",
        )

        content = (target_dir / ".gitignore").read_text()
        assert content.endswith("\n")
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_gitignore_downstream.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'script.utils.gitignore_downstream'`

**Step 3: Write the implementation**

建立 `script/utils/gitignore_downstream.py`：

```python
"""
gitignore-downstream：將模版的 .gitignore-downstream 合併為目標 .gitignore 中的標記區塊。
"""

from pathlib import Path

from rich.console import Console

console = Console()

DOWNSTREAM_FILENAME = ".gitignore-downstream"

MARKER_START = "# >>> {name} (managed by ai-dev init-from, DO NOT EDIT)"
MARKER_END = "# <<< {name}"


def merge_gitignore_downstream(
    template_dir: Path,
    target_dir: Path,
    template_name: str,
    remove_if_missing: bool = False,
) -> bool:
    """將模版的 .gitignore-downstream 合併到目標 .gitignore 的標記區塊。

    Args:
        template_dir: 模版本地目錄
        target_dir: 目標專案目錄
        template_name: 模版名稱（用於標記）
        remove_if_missing: 若模版已無 downstream 檔案，是否移除既有區塊

    Returns:
        bool: 是否有修改 .gitignore
    """
    downstream_file = template_dir / DOWNSTREAM_FILENAME
    gitignore_path = target_dir / ".gitignore"
    start_marker = MARKER_START.format(name=template_name)
    end_marker = MARKER_END.format(name=template_name)

    # 讀取 downstream 內容
    if downstream_file.is_file():
        downstream_content = downstream_file.read_text(encoding="utf-8").strip()
    else:
        downstream_content = None

    # 模版無 downstream 且不需移除 → 跳過
    if downstream_content is None and not remove_if_missing:
        return False

    # 讀取現有 .gitignore
    if gitignore_path.is_file():
        existing = gitignore_path.read_text(encoding="utf-8")
    else:
        existing = ""

    lines = existing.splitlines(keepends=True)

    # 尋找既有區塊
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        stripped = line.rstrip("\n\r")
        if stripped == start_marker:
            start_idx = i
        elif stripped == end_marker and start_idx is not None:
            end_idx = i
            break

    has_block = start_idx is not None and end_idx is not None

    if downstream_content is None:
        # 模版已刪除 downstream → 移除區塊
        if has_block:
            del lines[start_idx : end_idx + 1]
            # 移除區塊前的空行
            if start_idx > 0 and start_idx <= len(lines) and lines[start_idx - 1].strip() == "":
                del lines[start_idx - 1]
            result = "".join(lines)
            if result and not result.endswith("\n"):
                result += "\n"
            gitignore_path.write_text(result, encoding="utf-8")
            console.print(f"  [yellow]已移除 .gitignore 中的 {template_name} 區塊[/yellow]")
            return True
        return False

    # 建構區塊
    block = f"{start_marker}\n{downstream_content}\n{end_marker}\n"

    if has_block:
        # 替換既有區塊
        lines[start_idx : end_idx + 1] = [block]
        result = "".join(lines)
    else:
        # 附加到尾部
        result = existing
        if result and not result.endswith("\n"):
            result += "\n"
        if result:
            result += "\n"
        result += block

    if result and not result.endswith("\n"):
        result += "\n"

    gitignore_path.write_text(result, encoding="utf-8")
    if has_block:
        console.print(f"  [cyan]已更新 .gitignore 中的 {template_name} 區塊[/cyan]")
    else:
        console.print(f"  [green]已新增 .gitignore 中的 {template_name} 區塊[/green]")
    return True
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_gitignore_downstream.py -v`
Expected: All 7 tests PASS

**Step 5: Commit**

```bash
git add script/utils/gitignore_downstream.py tests/test_gitignore_downstream.py
git commit -m "功能(gitignore): 新增 gitignore_downstream 模組與測試"
```

---

### Task 2: smart_merge 排除 .gitignore-downstream

**Files:**
- Modify: `script/utils/smart_merge.py:17`
- Test: `tests/test_smart_merge.py`（既有測試不壞）

**Step 1: Modify EXCLUDE_PATHS**

在 `script/utils/smart_merge.py:17`，將：

```python
EXCLUDE_PATHS = {".git", ".gitkeep", "README.md", "LICENSE"}
```

改為：

```python
EXCLUDE_PATHS = {".git", ".gitkeep", ".gitignore-downstream", "README.md", "LICENSE"}
```

**Step 2: Run existing tests**

Run: `uv run pytest tests/test_smart_merge.py -v`
Expected: All existing tests PASS

**Step 3: Commit**

```bash
git add script/utils/smart_merge.py
git commit -m "雜項(smart-merge): 排除 .gitignore-downstream 不複製到目標"
```

---

### Task 3: init_from 整合 gitignore_downstream

**Files:**
- Modify: `script/commands/init_from.py:1-14`（import）
- Modify: `script/commands/init_from.py:169-187`（首次初始化，merge 後）
- Modify: `script/commands/init_from.py:246-259`（--update 模式，merge 後）

**Step 1: Add import**

在 `script/commands/init_from.py` 的 import 區加入：

```python
from ..utils.gitignore_downstream import merge_gitignore_downstream
```

**Step 2: 首次初始化——在 merge_template 後、create_tracking_file 前呼叫**

在 `init_from.py` 約第 174 行（`merge_template` 之後）加入：

```python
    # 合併 .gitignore-downstream
    merge_gitignore_downstream(
        template_dir=target_dir,
        target_dir=cwd,
        template_name=final_name,
    )
```

**Step 3: --update 模式——在 merge_template 後加入**

在 `_run_update_mode` 的 `merge_template` 之後（約第 251 行）加入：

```python
    # 合併 .gitignore-downstream（支援新增/更新/移除）
    merge_gitignore_downstream(
        template_dir=template_dir,
        target_dir=cwd,
        template_name=template_name,
        remove_if_missing=True,
    )
```

**Step 4: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add script/commands/init_from.py
git commit -m "功能(init-from): 整合 .gitignore-downstream 區塊合併"
```

---

### Task 4: 在 qdm-ai-base 模版新增 .gitignore-downstream

**Files:**
- Create: `~/Documents/syncthing/backup/Sympasoft/SympasoftCode/qdm-ai-base/.gitignore-downstream`

**Step 1: 建立檔案**

```gitignore
# Atlas 靜態分析產出（由模版管理，下游不需追蹤）
.atlas/
```

**Step 2: Commit（在 qdm-ai-base repo 內）**

```bash
cd ~/Documents/syncthing/backup/Sympasoft/SympasoftCode/qdm-ai-base
git add .gitignore-downstream
git commit -m "功能: 新增 .gitignore-downstream 供下游專案使用"
```

# Auto-Skill Canonical State Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 將 `auto-skill` 改為由 `~/.config/ai-dev/skills/auto-skill` 管理 canonical state，並在 `clone` 階段以 `symlink/junction` 投影到多個 AI 工具目錄，失敗時 fallback copy。

**Architecture:** 保持 ai-dev 現有三階段架構不變，新增 `auto-skill` 的 path/state/projection 抽象。`update` 負責 refresh canonical state，`clone` 負責投影到各工具目錄。

**Tech Stack:** Python 3.13、pytest、typer、rich、pyyaml

**設計文件：** `docs/plans/2026-03-12-auto-skill-canonical-state-design.md`

---

## Task 1: 新增 auto-skill canonical state 路徑 helper

**Files:**
- Modify: `script/utils/paths.py`
- Test: `tests/test_paths.py`

### Step 1: 寫 failing test

```python
def test_get_auto_skill_state_dir_is_under_ai_dev_config(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert get_auto_skill_state_dir() == tmp_path / ".config" / "ai-dev" / "skills" / "auto-skill"
```

### Step 2: Run test to verify it fails

Run: `cd /Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills && uv run pytest tests/test_paths.py -v`
Expected: FAIL，因為 `get_auto_skill_state_dir()` 尚不存在

### Step 3: 寫最小實作

在 `script/utils/paths.py` 新增：

```python
def get_auto_skill_state_dir() -> Path:
    return get_ai_dev_dir() / "skills" / "auto-skill"
```

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/test_paths.py -v`
Expected: PASS

### Step 5: Commit

```bash
git add script/utils/paths.py tests/test_paths.py
git commit -m "功能(paths): 新增 auto-skill canonical state 路徑"
```

---

## Task 2: 建立 auto-skill state refresh helper

**Files:**
- Create: `script/utils/auto_skill_state.py`
- Modify: `script/utils/shared.py`
- Test: `tests/test_auto_skill_state.py`

### Step 1: 寫 failing test

```python
def test_refresh_auto_skill_state_applies_clone_policy(tmp_path):
    template_dir = tmp_path / "template"
    upstream_dir = tmp_path / "upstream"
    state_dir = tmp_path / "state"
    ...
    refresh_auto_skill_state(template_dir, upstream_dir, state_dir)
    assert (state_dir / "SKILL.md").exists()
    assert (state_dir / "experience" / "_index.json").exists()
```

### Step 2: Run test to verify it fails

Run: `cd /Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills && uv run pytest tests/test_auto_skill_state.py -v`
Expected: FAIL，因為 helper 尚不存在

### Step 3: 寫最小實作

- 讀取 template `skills/auto-skill/.clonepolicy.json`
- 以 smart-merge 規則將 template 與上游來源合併到 canonical state
- 保留 `.git`、`assets` 之類不應進 state 的內容過濾規則

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/test_auto_skill_state.py -v`
Expected: PASS

### Step 5: Commit

```bash
git add script/utils/auto_skill_state.py script/utils/shared.py tests/test_auto_skill_state.py
git commit -m "功能(auto-skill): 新增 canonical state refresh 流程"
```

---

## Task 3: 將 update 接入 canonical state refresh

**Files:**
- Modify: `script/commands/update.py`
- Modify: `script/utils/shared.py`
- Test: `tests/test_update_command.py`

### Step 1: 寫 failing test

```python
def test_update_refreshes_auto_skill_state(monkeypatch, tmp_path):
    ...
    result = runner.invoke(app, ["update", "--skip-npm"])
    assert result.exit_code == 0
    assert state_dir.exists()
```

### Step 2: Run test to verify it fails

Run: `cd /Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills && uv run pytest tests/test_update_command.py -v`
Expected: FAIL，因為 update 尚未更新 canonical state

### Step 3: 寫最小實作

- 在 repo 更新完成後呼叫 canonical state refresh
- 補 console 訊息，區分 repo 更新與 state refresh
- 保持 `update` 不做最終工具分發

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/test_update_command.py -v`
Expected: PASS

### Step 5: Commit

```bash
git add script/commands/update.py script/utils/shared.py tests/test_update_command.py
git commit -m "功能(update): 更新後同步 auto-skill canonical state"
```

---

## Task 4: 建立 auto-skill projection helper

**Files:**
- Create: `script/utils/auto_skill_projection.py`
- Test: `tests/test_auto_skill_projection.py`

### Step 1: 寫 failing test

```python
def test_project_auto_skill_creates_symlink_when_supported(tmp_path):
    source_dir = tmp_path / "state"
    target_dir = tmp_path / "tool" / "skills" / "auto-skill"
    ...
    result = project_auto_skill(source_dir, target_dir)
    assert result.mode in {"symlink", "junction"}
```

### Step 2: Run test to verify it fails

Run: `cd /Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills && uv run pytest tests/test_auto_skill_projection.py -v`
Expected: FAIL，因為 projection helper 尚不存在

### Step 3: 寫最小實作

- 若 target 已正確指向 source，直接回傳成功
- 若 target 為舊 link / broken link / 實體目錄，先清理
- 建立相對 symlink；Windows 使用 junction
- 若 link 失敗，fallback copy

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/test_auto_skill_projection.py -v`
Expected: PASS

### Step 5: Commit

```bash
git add script/utils/auto_skill_projection.py tests/test_auto_skill_projection.py
git commit -m "功能(auto-skill): 新增多工具投影 helper"
```

---

## Task 5: 將 clone / distribute 接入 auto-skill projection

**Files:**
- Modify: `script/utils/shared.py`
- Modify: `script/commands/clone.py`
- Test: `tests/test_clone_command.py`

### Step 1: 寫 failing test

```python
def test_clone_projects_auto_skill_from_canonical_state(tmp_path):
    ...
    copy_skills(sync_project=False)
    assert (target_root / "skills" / "auto-skill").exists()
```

### Step 2: Run test to verify it fails

Run: `cd /Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills && uv run pytest tests/test_clone_command.py -v`
Expected: FAIL，因為 clone 仍使用 `copytree`

### Step 3: 寫最小實作

- 保留原有一般資源分發
- 將 `auto-skill` 從一般 copy 分支抽出
- 改為使用 canonical state + projection helper
- console 顯示採用 `symlink`、`junction` 或 `copy`

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/test_clone_command.py -v`
Expected: PASS

### Step 5: Commit

```bash
git add script/utils/shared.py script/commands/clone.py tests/test_clone_command.py
git commit -m "功能(clone): 改用 canonical state 投影 auto-skill"
```

---

## Task 6: 補齊文件與回歸驗證

**Files:**
- Modify: `docs/dev-guide/README.md`
- Modify: `skills/custom-skills-dev/references/copy-architecture.md`
- Modify: `CHANGELOG.md`

### Step 1: 更新文件

- 說明 `auto-skill` 已有獨立 canonical state
- 補充 `update` 與 `clone` 的責任分界
- 補充 projection 模式與 fallback 行為

### Step 2: Run verification

Run:

```bash
cd /Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills
uv run pytest -q
uv tool install . --force
ai-dev clone --help
ai-dev update --help
```

Expected:

- 測試通過
- CLI 指令可正常載入

### Step 3: Commit

```bash
git add docs/dev-guide/README.md skills/custom-skills-dev/references/copy-architecture.md CHANGELOG.md
git commit -m "文件(auto-skill): 補充 canonical state 與投影流程"
```

---

## 執行方式

Plan complete and saved to `docs/plans/2026-03-12-auto-skill-canonical-state-impl.md`.

兩種執行方式：

1. **Subagent-Driven（同 session）**
   - 我在這個 session 逐 task 實作與驗證

2. **Parallel Session（分離 session）**
   - 在新 session / worktree 中使用 `executing-plans`

本次直接採 **Subagent-Driven（同 session）**。

# Auto-Skill Canonical State Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 將 auto-skill 改為 canonical state + projection 模型，避免各工具目錄漂移。

**Architecture:** 新增 `paths`、`auto_skill_state`、`auto_skill_projection` 三個層次；`update` 負責 refresh state，`clone` 負責投影。

**Tech Stack:** Python 3.13、pytest、typer、rich

**設計文件：** `docs/plans/2026-03-12-auto-skill-canonical-state-design.md`

---

## Task 1: 路徑抽象

**Files:**
- Modify: `script/utils/paths.py`
- Test: `tests/test_paths.py`

### Step 1: 新增 canonical path helper

- `get_auto_skill_dir()` 改回傳 canonical state
- `get_auto_skill_repo_dir()` 新增 upstream repo 路徑

### Step 2: 驗證

Run: `uv run pytest tests/test_paths.py -q`
Expected: PASS

---

## Task 2: canonical state refresh

**Files:**
- Create: `script/utils/auto_skill_state.py`
- Test: `tests/test_auto_skill_state.py`

### Step 1: 合併 template + upstream 到 canonical state

- 排除 `.git`、`assets`、`README.md`
- 沿用 clone policy 規則
- 衝突保留既有 state

### Step 2: 驗證

Run: `uv run pytest tests/test_auto_skill_state.py -q`
Expected: PASS

---

## Task 3: projection helper

**Files:**
- Create: `script/utils/auto_skill_projection.py`
- Test: `tests/test_auto_skill_projection.py`

### Step 1: 建立 link/copy fallback

- POSIX：relative symlink
- Windows：junction 優先
- 失敗：copytree

### Step 2: 驗證

Run: `uv run pytest tests/test_auto_skill_projection.py -q`
Expected: PASS

---

## Task 4: 接入 `shared.py` / `update.py`

**Files:**
- Modify: `script/utils/shared.py`
- Modify: `script/commands/update.py`

### Step 1: 接入 canonical state refresh

- `REPOS["auto_skill"]` 改用 upstream repo 路徑
- `update` 完成後 refresh canonical state
- `clone` 分發時改投影 canonical state

### Step 2: 驗證

Run:

```bash
uv run pytest tests/test_clone_policy.py -q
uv run pytest -q
python3 -m compileall script
```

Expected:

- clone policy 測試通過
- 全量測試通過
- Python compile 無錯

---

## 執行方式

本次直接在同一個 session / worktree 內執行。

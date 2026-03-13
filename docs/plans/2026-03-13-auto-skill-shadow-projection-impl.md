# Auto-Skill Shadow Projection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 將 `auto-skill` 從 direct canonical projection 改為 per-target shadow projection，讓 legacy 遷移與後續更新都尊重 `.clonepolicy.json`。

**Architecture:** 保留 canonical state 在 `~/.config/ai-dev/skills/auto-skill`。`clone` 時針對各 target 建立或更新 `~/.config/ai-dev/projections/<target>/auto-skill`，再將工具目錄投影到該 shadow。`update` 僅刷新 canonical state。

**Tech Stack:** Python 3.13、pytest、typer、rich、pyyaml

---

### Task 1: 補齊 projection 路徑與 metadata 路徑 helper

**Files:**
- Modify: `script/utils/paths.py`
- Test: `tests/test_paths.py`

**Step 1: Write the failing test**

新增測試驗證：
- `get_auto_skill_projection_root()`
- `get_auto_skill_shadow_dir("claude")`
- `get_auto_skill_shadow_state_path("claude")`
- `get_auto_skill_backup_dir("claude")`

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_paths.py -v`

**Step 3: Write minimal implementation**

在 `paths.py` 新增 projection/shadow/backup helper。

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_paths.py -v`

---

### Task 2: 先寫 shadow projection failing tests

**Files:**
- Modify: `tests/test_auto_skill_projection.py`

**Step 1: Write the failing test**

新增案例：
- `legacy_dir` 遷移到 `shadow_link`
- `shadow_link` 更新時保留 `skip-if-exists`
- revision 未變時等冪

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_auto_skill_projection.py -v`

**Step 3: No implementation yet**

保持紅燈，確認失敗訊息正確。

**Step 4: Run test to verify it still fails correctly**

Run: `uv run pytest tests/test_auto_skill_projection.py -v`

---

### Task 3: 實作 shadow projection 狀態機

**Files:**
- Modify: `script/utils/auto_skill_projection.py`
- Test: `tests/test_auto_skill_projection.py`

**Step 1: Write minimal implementation**

新增：
- target 狀態判斷
- legacy backup
- temp shadow rebuild
- revision metadata
- shadow link/copy projection

**Step 2: Run targeted tests**

Run: `uv run pytest tests/test_auto_skill_projection.py -v`

**Step 3: Refactor**

把 policy 載入、metadata 讀寫、shadow replace 拆成小 helper。

**Step 4: Re-run tests**

Run: `uv run pytest tests/test_auto_skill_projection.py -v`

---

### Task 4: 將 `copy_custom_skills_to_targets()` 接到 shadow projection

**Files:**
- Modify: `script/utils/shared.py`
- Test: `tests/test_clone_policy.py`

**Step 1: Write the failing test**

新增整合測試驗證：
- `copy_custom_skills_to_targets(sync_project=False)` 後，target `auto-skill` 指向 shadow，不再直指 canonical。

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_clone_policy.py -k auto_skill -v`

**Step 3: Write minimal implementation**

讓 `_copy_with_log()` 對 `auto-skill` 傳入 target key 與 policy source dir，並把 manifest source path 記錄為 shadow。

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_clone_policy.py -k auto_skill -v`

---

### Task 5: 補 update/clone 模擬環境驗證

**Files:**
- Create or Modify: `tests/test_auto_skill_state.py`
- Create or Modify: `tests/test_auto_skill_projection.py`

**Step 1: Write integration-style tests**

模擬環境驗證：
- `update` 只刷新 canonical state，不動 target
- `clone` 會把 legacy/canonical target 轉成 shadow projection

**Step 2: Run targeted tests**

Run: `uv run pytest tests/test_auto_skill_state.py tests/test_auto_skill_projection.py tests/test_clone_policy.py -v`

**Step 3: Add regression coverage**

補 broken link / fallback copy 案例。

**Step 4: Re-run tests**

Run: `uv run pytest tests/test_auto_skill_state.py tests/test_auto_skill_projection.py tests/test_clone_policy.py -v`

---

### Task 6: 文件與最終驗證

**Files:**
- Modify: `README.md`

**Step 1: Update docs**

補上 canonical + shadow + target projection 三層說明。

**Step 2: Run final verification**

Run:

```bash
uv run pytest tests/test_paths.py tests/test_auto_skill_state.py tests/test_auto_skill_projection.py tests/test_clone_policy.py -v
uv run pytest -q
```

**Step 3: Simulated environment run**

在 temp HOME 下建立假的 `custom-skills` / target 目錄，直接呼叫 projection helper 或分發入口，驗證 legacy -> shadow link 的完整流程。


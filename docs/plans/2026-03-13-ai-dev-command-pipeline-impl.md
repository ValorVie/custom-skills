# ai-dev Command Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 讓 `ai-dev install`、`update`、`clone` 共享一致的 phase pipeline、統一 flags 與 machine-readable command manifest，同時重整相關程式結構。

**Architecture:** 保留高階命令名稱，新增 `tools / repos / state / targets` phase model 與 `ExecutionPlan`。CLI entry 只負責解析參數與建 plan，實際流程下沉到 `services/pipeline/` 與各 domain service，並以 Python registry 形式提供 command manifest 作為文件與測試契約來源。

**Tech Stack:** Python 3.13、Typer、Rich、pytest

**設計文件：** `docs/plans/2026-03-13-ai-dev-command-pipeline-design.md`

---

### Task 1: 建立 phase 與 execution plan 基礎模型

**Files:**
- Create: `script/models/command_spec.py`
- Create: `script/models/execution_plan.py`
- Create: `tests/test_execution_plan.py`

**Step 1: Write the failing test**

```python
def test_execution_plan_keeps_order_and_selected_targets():
    plan = ExecutionPlan(
        command_name="update",
        phases=("tools", "repos", "state"),
        targets=("claude", "codex"),
        dry_run=True,
    )

    assert plan.phases == ("tools", "repos", "state")
    assert plan.targets == ("claude", "codex")
    assert plan.requires_targets is False
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_execution_plan.py -q`  
Expected: FAIL，因為模型檔案尚不存在

**Step 3: Write minimal implementation**

```python
@dataclass(frozen=True)
class ExecutionPlan:
    command_name: str
    phases: tuple[str, ...]
    targets: tuple[str, ...]
    dry_run: bool = False

    @property
    def requires_targets(self) -> bool:
        return "targets" in self.phases
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_execution_plan.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add script/models/command_spec.py script/models/execution_plan.py tests/test_execution_plan.py
git commit -m "功能(cli): 新增 phase 與 execution plan 模型"
```

### Task 2: 建立 machine-readable command manifest registry

**Files:**
- Create: `script/cli/command_manifest.py`
- Create: `tests/test_command_manifest.py`
- Modify: `script/main.py`

**Step 1: Write the failing test**

```python
def test_command_manifest_contains_top_level_pipeline_commands():
    manifest = build_command_manifest()
    paths = {spec.path for spec in manifest.commands}

    assert ("install",) in paths
    assert ("update",) in paths
    assert ("clone",) in paths
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_command_manifest.py -q`  
Expected: FAIL，因為 registry 尚不存在

**Step 3: Write minimal implementation**

```python
PIPELINE_PHASES = ("tools", "repos", "state", "targets")

COMMAND_SPECS = (
    CommandSpec(path=("install",), default_phases=PIPELINE_PHASES, ...),
    CommandSpec(path=("update",), default_phases=("tools", "repos", "state"), ...),
    CommandSpec(path=("clone",), default_phases=("state", "targets"), ...),
)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_command_manifest.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add script/cli/command_manifest.py script/main.py tests/test_command_manifest.py
git commit -m "功能(cli): 新增 command manifest registry"
```

### Task 3: 建立共用 flags 解析與 phase/target 驗證

**Files:**
- Create: `script/cli/phase_selection.py`
- Create: `script/cli/target_selection.py`
- Create: `tests/test_phase_selection.py`

**Step 1: Write the failing test**

```python
def test_parse_only_and_skip_into_execution_plan():
    spec = get_command_spec(("clone",))
    plan = build_execution_plan(
        spec,
        only="targets",
        skip=None,
        target="claude,codex",
        dry_run=True,
    )

    assert plan.phases == ("targets",)
    assert plan.targets == ("claude", "codex")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_phase_selection.py -q`  
Expected: FAIL，因為 phase/target selection 尚不存在

**Step 3: Write minimal implementation**

```python
def build_execution_plan(spec, only, skip, target, dry_run):
    phases = resolve_phases(spec.default_phases, only=only, skip=skip)
    targets = resolve_targets(spec.allowed_targets, target=target, phases=phases)
    return ExecutionPlan(...)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_phase_selection.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add script/cli/phase_selection.py script/cli/target_selection.py tests/test_phase_selection.py
git commit -m "功能(cli): 統一 phase 與 target 參數解析"
```

### Task 4: 抽出 pipeline/domain service 骨架

**Files:**
- Create: `script/services/pipeline/install_pipeline.py`
- Create: `script/services/pipeline/update_pipeline.py`
- Create: `script/services/pipeline/clone_pipeline.py`
- Create: `script/services/tools/update.py`
- Create: `script/services/repos/refresh.py`
- Create: `script/services/state/auto_skill.py`
- Create: `script/services/targets/distribute.py`
- Create: `tests/test_pipeline_services.py`

**Step 1: Write the failing test**

```python
def test_update_pipeline_runs_requested_phases_in_order(monkeypatch):
    calls = []
    monkeypatch.setattr("script.services.pipeline.update_pipeline.run_tools_phase", lambda **_: calls.append("tools"))
    monkeypatch.setattr("script.services.pipeline.update_pipeline.run_repos_phase", lambda **_: calls.append("repos"))
    monkeypatch.setattr("script.services.pipeline.update_pipeline.run_state_phase", lambda **_: calls.append("state"))

    execute_update_plan(ExecutionPlan(command_name="update", phases=("tools", "repos", "state"), targets=(), dry_run=False))

    assert calls == ["tools", "repos", "state"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_pipeline_services.py -q`  
Expected: FAIL，因為 pipeline service 尚不存在

**Step 3: Write minimal implementation**

```python
def execute_update_plan(plan: ExecutionPlan) -> None:
    for phase in plan.phases:
        ...
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_pipeline_services.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add script/services/pipeline script/services/tools script/services/repos script/services/state script/services/targets tests/test_pipeline_services.py
git commit -m "重構(cli): 建立高階命令 pipeline 與 domain service 骨架"
```

### Task 5: 將 `install` 改寫為新 pipeline 入口

**Files:**
- Modify: `script/commands/install.py`
- Modify: `tests/test_install_command.py`

**Step 1: Write the failing test**

```python
def test_install_accepts_only_skip_target_flags(runner):
    result = runner.invoke(app, ["install", "--only", "repos,state", "--skip", "tools", "--dry-run"])
    assert result.exit_code == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_install_command.py -q`  
Expected: FAIL，因為 `install` 尚未支援新 flags

**Step 3: Write minimal implementation**

```python
spec = get_command_spec(("install",))
plan = build_execution_plan(spec, only=only, skip=skip, target=target, dry_run=dry_run)
execute_install_plan(plan)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_install_command.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add script/commands/install.py tests/test_install_command.py
git commit -m "重構(install): 改用 phase pipeline 與統一 flags"
```

### Task 6: 將 `update` 改寫為新 pipeline 入口

**Files:**
- Modify: `script/commands/update.py`
- Modify: `tests/test_update_command.py` 或新增 `tests/test_update_command.py`

**Step 1: Write the failing test**

```python
def test_update_default_plan_excludes_targets(runner):
    result = runner.invoke(app, ["update", "--dry-run"])
    assert "tools" in result.stdout
    assert "repos" in result.stdout
    assert "state" in result.stdout
    assert "targets" not in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_update_command.py -q`  
Expected: FAIL，因為 `update` 尚未輸出/使用新 execution plan

**Step 3: Write minimal implementation**

```python
spec = get_command_spec(("update",))
plan = build_execution_plan(...)
execute_update_plan(plan)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_update_command.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add script/commands/update.py tests/test_update_command.py
git commit -m "重構(update): 改用 phase pipeline 與統一 flags"
```

### Task 7: 將 `clone` 改寫為新 pipeline 入口

**Files:**
- Modify: `script/commands/clone.py`
- Modify: `tests/test_clone_command.py`

**Step 1: Write the failing test**

```python
def test_clone_rejects_target_without_targets_phase(runner):
    result = runner.invoke(app, ["clone", "--only", "state", "--target", "claude"])
    assert result.exit_code != 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_clone_command.py -q`  
Expected: FAIL，因為 `clone` 尚未使用統一 phase/target 驗證

**Step 3: Write minimal implementation**

```python
spec = get_command_spec(("clone",))
plan = build_execution_plan(...)
execute_clone_plan(plan, force=force, backup=backup, skip_conflicts=skip_conflicts)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_clone_command.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add script/commands/clone.py tests/test_clone_command.py
git commit -m "重構(clone): 改用 phase pipeline 與統一 flags"
```

### Task 8: 將既有實作搬入 domain services 並縮減 `shared.py`

**Files:**
- Modify: `script/utils/shared.py`
- Modify: `script/services/tools/update.py`
- Modify: `script/services/repos/refresh.py`
- Modify: `script/services/state/auto_skill.py`
- Modify: `script/services/targets/distribute.py`
- Test: `tests/test_install_command.py`
- Test: `tests/test_update_command.py`
- Test: `tests/test_clone_command.py`

**Step 1: Write the failing test**

```python
def test_clone_pipeline_still_calls_distribution_logic(monkeypatch):
    calls = []
    monkeypatch.setattr("script.services.targets.distribute.copy_skills", lambda **_: calls.append("copy"))
    ...
    assert calls == ["copy"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_clone_command.py tests/test_update_command.py tests/test_install_command.py -q`  
Expected: FAIL，因為搬移後尚未完成串接

**Step 3: Write minimal implementation**

```python
def run_targets_phase(...):
    return copy_skills(...)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_clone_command.py tests/test_update_command.py tests/test_install_command.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add script/utils/shared.py script/services/tools/update.py script/services/repos/refresh.py script/services/state/auto_skill.py script/services/targets/distribute.py tests/test_install_command.py tests/test_update_command.py tests/test_clone_command.py
git commit -m "重構(cli): 將高階命令執行邏輯下沉至 domain services"
```

### Task 9: 讓參考文件與 command manifest 建立自動校驗

**Files:**
- Modify: `docs/ai-dev指令與資料流參考.md`
- Create: `tests/test_ai_dev_command_reference.py`

**Step 1: Write the failing test**

```python
def test_reference_doc_lists_manifest_top_level_commands():
    doc = Path("docs/ai-dev指令與資料流參考.md").read_text(encoding="utf-8")
    manifest = build_command_manifest()
    for spec in manifest.commands:
        if len(spec.path) == 1:
            assert spec.path[0] in doc
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_ai_dev_command_reference.py -q`  
Expected: FAIL，因為文件與 manifest 尚未建立對應規則

**Step 3: Write minimal implementation**

```python
PIPELINE_COMMAND_REFERENCE = ...
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_ai_dev_command_reference.py -q`  
Expected: PASS

**Step 5: Commit**

```bash
git add docs/ai-dev指令與資料流參考.md tests/test_ai_dev_command_reference.py
git commit -m "測試(docs): 新增命令參考文件與 manifest 一致性檢查"
```

### Task 10: 跑回歸驗證並更新相關文件

**Files:**
- Modify: `README.md`
- Modify: `docs/ai-dev指令與資料流參考.md`
- Modify: `docs/report/2026-03-13-ai-dev-command-surface-optimization-assessment.md`

**Step 1: Run focused regression**

Run:

```bash
uv run pytest tests/test_execution_plan.py tests/test_command_manifest.py tests/test_phase_selection.py tests/test_install_command.py tests/test_update_command.py tests/test_clone_command.py -q
```

Expected: PASS

**Step 2: Run broader regression**

Run:

```bash
uv run pytest -q
```

Expected: PASS

**Step 3: Update docs**

- README 的高階命令說明改為 phase/flags 模型
- `docs/ai-dev指令與資料流參考.md` 補齊 top-level 命令細部語意
- 優化評估報告補上「P0 已落地」註記

**Step 4: Commit**

```bash
git add README.md docs/ai-dev指令與資料流參考.md docs/report/2026-03-13-ai-dev-command-surface-optimization-assessment.md
git commit -m "文件(ai-dev): 同步命令 pipeline 與 manifest 契約"
```

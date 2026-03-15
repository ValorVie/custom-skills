# ai-dev 命令契約最終狀態 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 一次完成 ai-dev 命令分類基線、scope/target 契約收斂、重副作用顯式化，以及 top-level 命令語意表補齊。

**Architecture:** 以現有 `install / update / clone` phase pipeline 為基礎，先補齊長期維護文件與 taxonomy，再逐組調整 `needs_scope_fix`、`split`、`clarify` 命令。每個命令修改都以測試先行，並在完成後同步更新 `docs/ai-dev指令與資料流參考.md` 與 `docs/ai-dev命令分類與設計壓力參考.md`。

**Tech Stack:** Python 3、Typer、pytest、Markdown 文件、ai-dev CLI

---

### Task 1: 建立命令分類基線文件

**Files:**
- Create: `docs/ai-dev命令分類與設計壓力參考.md`
- Create: `docs/report/2026-03-13-ai-dev-command-classification-assessment.md`
- Modify: `docs/ai-dev指令與資料流參考.md`

**Step 1: 撰寫先失敗的文件校驗測試**

```python
def test_ai_dev_command_taxonomy_reference_exists():
    taxonomy = Path("docs/ai-dev命令分類與設計壓力參考.md")
    assert taxonomy.exists()


def test_ai_dev_command_taxonomy_mentions_design_pressure_groups():
    content = Path("docs/ai-dev命令分類與設計壓力參考.md").read_text()
    for phrase in ("keep", "clarify", "needs_scope_fix", "split"):
        assert phrase in content
```

**Step 2: 執行測試確認失敗**

Run: `uv run pytest tests/test_ai_dev_command_reference.py -k taxonomy -v`  
Expected: FAIL，因為 taxonomy/reference 文件尚不存在。

**Step 3: 以最小內容建立 taxonomy 與 assessment 文件**

```markdown
# ai-dev 命令分類與設計壓力參考

## 分類維度
- side_effect_class
- scope
- target_mode
- design_pressure

## 命令分類總表
| command_path | design_pressure |
|--------------|-----------------|
| clone | keep |
| install | clarify |
```

```markdown
# ai-dev 命令分類評估

## 結論
- `keep`: `clone`
- `clarify`: `install`, `update`
- `needs_scope_fix`: `standards switch`
- `split`: `init-from`
```

**Step 4: 擴充為正式內容並同步更新實作真相文件**

Run: `sed -n '1,240p' docs/ai-dev指令與資料流參考.md`  
Expected: 找出 top-level 命令語意表插入位置，完成 taxonomy/reference/assessment 三份文件的正式內容。

**Step 5: 執行測試確認通過**

Run: `uv run pytest tests/test_ai_dev_command_reference.py -k taxonomy -v`  
Expected: PASS

**Step 6: Commit**

```bash
git add docs/ai-dev命令分類與設計壓力參考.md docs/report/2026-03-13-ai-dev-command-classification-assessment.md docs/ai-dev指令與資料流參考.md tests/test_ai_dev_command_reference.py
git commit -m "docs(ai-dev): 建立命令分類與設計壓力基線"
```

### Task 2: 補齊 top-level 命令細部語意表

**Files:**
- Modify: `docs/ai-dev指令與資料流參考.md`
- Modify: `tests/test_ai_dev_command_reference.py`

**Step 1: 撰寫先失敗的文件內容測試**

```python
def test_top_level_command_sections_are_detailed():
    content = Path("docs/ai-dev指令與資料流參考.md").read_text()
    for heading in ("install", "update", "clone", "status", "list", "toggle", "init-from"):
        assert heading in content
    assert "side_effect_class" in content
    assert "target_mode" in content
```

**Step 2: 執行測試確認失敗**

Run: `uv run pytest tests/test_ai_dev_command_reference.py -k detailed -v`  
Expected: FAIL，因為 top-level 細部語意表仍不足。

**Step 3: 補入正式語意表**

```markdown
| command | intent | side_effect_class | target_mode | writes_state |
|---------|--------|-------------------|-------------|--------------|
| install | 初始化環境 | multi_stage_pipeline + system_level_operation | explicit_multi | ~/.config/* |
```

**Step 4: 執行測試確認通過**

Run: `uv run pytest tests/test_ai_dev_command_reference.py -k detailed -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add docs/ai-dev指令與資料流參考.md tests/test_ai_dev_command_reference.py
git commit -m "docs(ai-dev): 補齊 top-level 命令語意表"
```

### Task 3: 統一 `list` 的 read-only target 契約

**Files:**
- Modify: `script/commands/list.py`
- Modify: `docs/ai-dev指令與資料流參考.md`
- Modify: `docs/ai-dev命令分類與設計壓力參考.md`
- Test: `tests/test_list_command.py`

**Step 1: 寫失敗測試**

```python
def test_list_without_target_lists_all_targets(runner):
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Claude" in result.stdout
    assert "Codex" in result.stdout
```

**Step 2: 執行測試確認現況**

Run: `uv run pytest tests/test_list_command.py -v`  
Expected: FAIL 或缺少覆蓋此契約的測試。

**Step 3: 寫最小實作**

```python
selected_targets = [target] if target else list(ALL_TARGETS)
for current in selected_targets:
    render_target_listing(current)
```

**Step 4: 更新文件**

```markdown
- `list`
  - `--target` 可省略
  - 未指定時代表所有 targets
```

**Step 5: 執行測試確認通過**

Run: `uv run pytest tests/test_list_command.py -v`  
Expected: PASS

**Step 6: Commit**

```bash
git add script/commands/list.py tests/test_list_command.py docs/ai-dev指令與資料流參考.md docs/ai-dev命令分類與設計壓力參考.md
git commit -m "fix(list): 統一 read-only target 契約"
```

### Task 4: 修正 `standards switch` 只改 project state

**Files:**
- Modify: `script/commands/standards.py`
- Modify: `docs/ai-dev指令與資料流參考.md`
- Modify: `docs/ai-dev命令分類與設計壓力參考.md`
- Test: `tests/test_standards_command.py`

**Step 1: 寫失敗測試**

```python
def test_standards_switch_does_not_sync_target_by_default(monkeypatch, runner):
    synced = []
    monkeypatch.setattr("script.commands.standards.sync_standards_to_target", lambda *args, **kwargs: synced.append(args))
    result = runner.invoke(app, ["standards", "switch", "uds"])
    assert result.exit_code == 0
    assert synced == []
```

**Step 2: 執行測試確認失敗**

Run: `uv run pytest tests/test_standards_command.py -k switch_does_not_sync -v`  
Expected: FAIL，現況仍會順手同步 target。

**Step 3: 寫最小實作**

```python
def switch(...):
    update_profile(...)
    typer.echo("已更新 project standards 狀態")
```

**Step 4: 更新文件**

```markdown
- `standards switch`
  - 僅更新 `.standards` 狀態
  - 不再自動同步 target
```

**Step 5: 執行測試確認通過**

Run: `uv run pytest tests/test_standards_command.py -k switch_does_not_sync -v`  
Expected: PASS

**Step 6: Commit**

```bash
git add script/commands/standards.py tests/test_standards_command.py docs/ai-dev指令與資料流參考.md docs/ai-dev命令分類與設計壓力參考.md
git commit -m "fix(standards): 移除 switch 的隱含 target 同步"
```

### Task 5: 修正 `standards sync` 的顯式 target 契約

**Files:**
- Modify: `script/commands/standards.py`
- Modify: `docs/ai-dev指令與資料流參考.md`
- Modify: `docs/ai-dev命令分類與設計壓力參考.md`
- Test: `tests/test_standards_command.py`

**Step 1: 寫失敗測試**

```python
def test_standards_sync_requires_target(runner):
    result = runner.invoke(app, ["standards", "sync"])
    assert result.exit_code != 0
    assert "--target" in result.stdout
```

**Step 2: 執行測試確認失敗**

Run: `uv run pytest tests/test_standards_command.py -k sync_requires_target -v`  
Expected: FAIL，現況可能仍使用預設 `claude`。

**Step 3: 寫最小實作**

```python
if not target:
    raise typer.BadParameter("`--target` is required for standards sync")
```

**Step 4: 更新文件**

```markdown
- `standards sync`
  - `--target` 必填
  - 不再預設 `claude`
```

**Step 5: 執行測試確認通過**

Run: `uv run pytest tests/test_standards_command.py -k sync_requires_target -v`  
Expected: PASS

**Step 6: Commit**

```bash
git add script/commands/standards.py tests/test_standards_command.py docs/ai-dev指令與資料流參考.md docs/ai-dev命令分類與設計壓力參考.md
git commit -m "fix(standards): 要求 sync 顯式指定 target"
```

### Task 6: 修正 `hooks` 的 scope 揭露

**Files:**
- Modify: `script/commands/hooks.py`
- Modify: `docs/ai-dev指令與資料流參考.md`
- Modify: `docs/ai-dev命令分類與設計壓力參考.md`
- Test: `tests/test_hooks_command.py`

**Step 1: 寫失敗測試**

```python
def test_hooks_install_requires_supported_target(runner):
    result = runner.invoke(app, ["hooks", "install"])
    assert result.exit_code != 0
    assert "--target" in result.stdout


def test_hooks_install_rejects_unknown_target(runner):
    result = runner.invoke(app, ["hooks", "install", "--target", "codex"])
    assert result.exit_code != 0
    assert "claude" in result.stdout
```

**Step 2: 執行測試確認失敗**

Run: `uv run pytest tests/test_hooks_command.py -v`  
Expected: FAIL 或缺少這些契約測試。

**Step 3: 寫最小實作**

```python
SUPPORTED_HOOK_TARGETS = ("claude",)

if target is None:
    raise typer.BadParameter("`--target` is required")
if target not in SUPPORTED_HOOK_TARGETS:
    raise typer.BadParameter("currently only supports `claude`")
```

**Step 4: 更新文件**

```markdown
- `hooks`
  - 需顯式 `--target`
  - 目前僅支援 `claude`
```

**Step 5: 執行測試確認通過**

Run: `uv run pytest tests/test_hooks_command.py -v`  
Expected: PASS

**Step 6: Commit**

```bash
git add script/commands/hooks.py tests/test_hooks_command.py docs/ai-dev指令與資料流參考.md docs/ai-dev命令分類與設計壓力參考.md
git commit -m "fix(hooks): 顯式揭露 target scope"
```

### Task 7: 拆分 `init-from` 的首次初始化與更新工作流

**Files:**
- Modify: `script/commands/init_from.py`
- Modify: `script/main.py`
- Modify: `docs/ai-dev指令與資料流參考.md`
- Modify: `docs/ai-dev命令分類與設計壓力參考.md`
- Modify: `docs/report/2026-03-13-ai-dev-command-classification-assessment.md`
- Test: `tests/test_init_from_command.py`

**Step 1: 寫失敗測試**

```python
def test_init_from_update_is_explicit_subcommand(runner):
    result = runner.invoke(app, ["init-from", "update"])
    assert result.exit_code == 0


def test_init_from_no_longer_uses_update_flag(runner):
    result = runner.invoke(app, ["init-from", "--update"])
    assert result.exit_code != 0
```

**Step 2: 執行測試確認失敗**

Run: `uv run pytest tests/test_init_from_command.py -v`  
Expected: FAIL，現況仍以 `--update` 承載第二種工作流。

**Step 3: 寫最小實作**

```python
@app.command("update")
def init_from_update(...):
    return run_init_from_update(...)
```

```python
if update:
    raise typer.BadParameter("use `ai-dev init-from update` instead")
```

**Step 4: 更新文件**

```markdown
- `init-from`
  - `ai-dev init-from <template>`: 首次初始化
  - `ai-dev init-from update`: 更新既有專案
```

**Step 5: 執行測試確認通過**

Run: `uv run pytest tests/test_init_from_command.py -v`  
Expected: PASS

**Step 6: Commit**

```bash
git add script/commands/init_from.py script/main.py tests/test_init_from_command.py docs/ai-dev指令與資料流參考.md docs/ai-dev命令分類與設計壓力參考.md docs/report/2026-03-13-ai-dev-command-classification-assessment.md
git commit -m "refactor(init-from): 拆分初始化與更新工作流"
```

### Task 8: 讓 `sync init` 的 bootstrap 路徑顯式化

**Files:**
- Modify: `script/commands/sync.py`
- Modify: `docs/ai-dev指令與資料流參考.md`
- Modify: `docs/ai-dev命令分類與設計壓力參考.md`
- Test: `tests/test_sync_command.py`

**Step 1: 寫失敗測試**

```python
def test_sync_init_requires_explicit_bootstrap_mode_for_first_sync(runner):
    result = runner.invoke(app, ["sync", "init"])
    assert result.exit_code != 0
    assert "bootstrap" in result.stdout
```

**Step 2: 執行測試確認失敗**

Run: `uv run pytest tests/test_sync_command.py -k bootstrap -v`  
Expected: FAIL，現況重副作用 bootstrap 路徑尚未顯式化。

**Step 3: 寫最小實作**

```python
if bootstrap_required and mode != "bootstrap":
    raise typer.BadParameter("use `--mode bootstrap` for first-time sync init")
```

**Step 4: 更新文件**

```markdown
- `sync init`
  - 首次 bootstrap 必須顯式 `--mode bootstrap`
  - 一般初始化與重副作用 bootstrap 路徑分離
```

**Step 5: 執行測試確認通過**

Run: `uv run pytest tests/test_sync_command.py -k bootstrap -v`  
Expected: PASS

**Step 6: Commit**

```bash
git add script/commands/sync.py tests/test_sync_command.py docs/ai-dev指令與資料流參考.md docs/ai-dev命令分類與設計壓力參考.md
git commit -m "refactor(sync): 顯式化 init bootstrap 模式"
```

### Task 9: 讓 `mem pull` 的 post-process 顯式化

**Files:**
- Modify: `script/commands/mem.py`
- Modify: `docs/ai-dev指令與資料流參考.md`
- Modify: `docs/ai-dev命令分類與設計壓力參考.md`
- Test: `tests/test_mem_command.py`

**Step 1: 寫失敗測試**

```python
def test_mem_pull_does_not_reindex_without_explicit_flag(monkeypatch, runner):
    calls = []
    monkeypatch.setattr("script.commands.mem.reindex_memories", lambda *args, **kwargs: calls.append("reindex"))
    result = runner.invoke(app, ["mem", "pull"])
    assert result.exit_code == 0
    assert calls == []
```

**Step 2: 執行測試確認失敗**

Run: `uv run pytest tests/test_mem_command.py -k pull_does_not_reindex -v`  
Expected: FAIL，現況可能會隱含 post-process。

**Step 3: 寫最小實作**

```python
if reindex:
    reindex_memories(...)
if cleanup:
    cleanup_memories(...)
```

**Step 4: 更新文件**

```markdown
- `mem pull`
  - 預設只做 pull
  - `--reindex` / `--cleanup` 控制後處理
```

**Step 5: 執行測試確認通過**

Run: `uv run pytest tests/test_mem_command.py -k pull_does_not_reindex -v`  
Expected: PASS

**Step 6: Commit**

```bash
git add script/commands/mem.py tests/test_mem_command.py docs/ai-dev指令與資料流參考.md docs/ai-dev命令分類與設計壓力參考.md
git commit -m "refactor(mem): 顯式化 pull 後處理流程"
```

### Task 10: 為 `toggle` 補 dry-run / preview

**Files:**
- Modify: `script/commands/toggle.py`
- Modify: `docs/ai-dev指令與資料流參考.md`
- Modify: `docs/ai-dev命令分類與設計壓力參考.md`
- Test: `tests/test_toggle_command.py`

**Step 1: 寫失敗測試**

```python
def test_toggle_dry_run_does_not_mutate_state(runner, state_path):
    before = state_path.read_text()
    result = runner.invoke(app, ["toggle", "--target", "claude", "--dry-run", "skills", "demo"])
    after = state_path.read_text()
    assert result.exit_code == 0
    assert before == after
    assert "dry-run" in result.stdout.lower()
```

**Step 2: 執行測試確認失敗**

Run: `uv run pytest tests/test_toggle_command.py -k dry_run -v`  
Expected: FAIL，現況缺少 preview 契約。

**Step 3: 寫最小實作**

```python
if dry_run:
    typer.echo(f"[dry-run] would toggle {resource}:{name} on {target}")
    return
```

**Step 4: 更新文件**

```markdown
- `toggle`
  - 支援 `--dry-run`
  - 預覽 target 變更但不實際寫入
```

**Step 5: 執行測試確認通過**

Run: `uv run pytest tests/test_toggle_command.py -k dry_run -v`  
Expected: PASS

**Step 6: Commit**

```bash
git add script/commands/toggle.py tests/test_toggle_command.py docs/ai-dev指令與資料流參考.md docs/ai-dev命令分類與設計壓力參考.md
git commit -m "feat(toggle): 新增 dry-run 預覽模式"
```

### Task 11: 為 `status` 補 section/filter 查詢

**Files:**
- Modify: `script/commands/status.py`
- Modify: `docs/ai-dev指令與資料流參考.md`
- Modify: `docs/ai-dev命令分類與設計壓力參考.md`
- Test: `tests/test_status_command.py`

**Step 1: 寫失敗測試**

```python
def test_status_section_filters_output(runner):
    result = runner.invoke(app, ["status", "--section", "repos"])
    assert result.exit_code == 0
    assert "repos" in result.stdout.lower()
    assert "npm" not in result.stdout.lower()
```

**Step 2: 執行測試確認失敗**

Run: `uv run pytest tests/test_status_command.py -k section -v`  
Expected: FAIL，現況仍只有全量聚合輸出。

**Step 3: 寫最小實作**

```python
SECTIONS = {"tools": render_tools, "repos": render_repos, "sync": render_sync}
selected = [section] if section else list(SECTIONS)
for name in selected:
    SECTIONS[name]()
```

**Step 4: 更新文件**

```markdown
- `status`
  - 支援 `--section tools|repos|sync|project`
  - 可分區查看狀態
```

**Step 5: 執行測試確認通過**

Run: `uv run pytest tests/test_status_command.py -k section -v`  
Expected: PASS

**Step 6: Commit**

```bash
git add script/commands/status.py tests/test_status_command.py docs/ai-dev指令與資料流參考.md docs/ai-dev命令分類與設計壓力參考.md
git commit -m "feat(status): 新增 section 查詢能力"
```

### Task 12: 為 `mem auto` 補 system-level 揭露與 dry-run

**Files:**
- Modify: `script/commands/mem.py`
- Modify: `docs/ai-dev指令與資料流參考.md`
- Modify: `docs/ai-dev命令分類與設計壓力參考.md`
- Test: `tests/test_mem_command.py`

**Step 1: 寫失敗測試**

```python
def test_mem_auto_dry_run_reports_scheduler_side_effects(runner):
    result = runner.invoke(app, ["mem", "auto", "--dry-run"])
    assert result.exit_code == 0
    assert "launchd" in result.stdout.lower() or "cron" in result.stdout.lower()
```

**Step 2: 執行測試確認失敗**

Run: `uv run pytest tests/test_mem_command.py -k auto_dry_run -v`  
Expected: FAIL，現況系統層副作用不夠顯性。

**Step 3: 寫最小實作**

```python
if dry_run:
    typer.echo("dry-run: would install launchd/cron schedule for mem sync")
    return
```

**Step 4: 更新文件**

```markdown
- `mem auto`
  - 支援 `--dry-run`
  - 明確揭露會安裝 launchd 或 cron 排程
```

**Step 5: 執行測試確認通過**

Run: `uv run pytest tests/test_mem_command.py -k auto_dry_run -v`  
Expected: PASS

**Step 6: Commit**

```bash
git add script/commands/mem.py tests/test_mem_command.py docs/ai-dev指令與資料流參考.md docs/ai-dev命令分類與設計壓力參考.md
git commit -m "feat(mem): 為 auto 補 system dry-run 揭露"
```

### Task 13: 補 taxonomy / reference drift 檢查

**Files:**
- Modify: `tests/test_ai_dev_command_reference.py`
- Modify: `docs/ai-dev命令分類與設計壓力參考.md`
- Modify: `docs/ai-dev指令與資料流參考.md`

**Step 1: 寫失敗測試**

```python
def test_scope_fix_commands_are_documented_in_taxonomy():
    content = Path("docs/ai-dev命令分類與設計壓力參考.md").read_text()
    for command in ("list", "standards switch", "standards sync", "hooks"):
        assert command in content


def test_split_commands_are_documented_in_taxonomy():
    content = Path("docs/ai-dev命令分類與設計壓力參考.md").read_text()
    for command in ("init-from", "sync init", "mem pull"):
        assert command in content
```

**Step 2: 執行測試確認失敗**

Run: `uv run pytest tests/test_ai_dev_command_reference.py -k taxonomy_commands -v`  
Expected: FAIL，若 taxonomy 內容與最終實作不齊。

**Step 3: 寫最小實作**

```markdown
| command_path | design_pressure |
|--------------|-----------------|
| list | needs_scope_fix |
| init-from | split |
```

**Step 4: 執行測試確認通過**

Run: `uv run pytest tests/test_ai_dev_command_reference.py -k taxonomy_commands -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_ai_dev_command_reference.py docs/ai-dev命令分類與設計壓力參考.md docs/ai-dev指令與資料流參考.md
git commit -m "test(ai-dev): 驗證 taxonomy 與 reference 一致性"
```

### Task 14: 全量驗證與收尾

**Files:**
- Modify: `README.md`
- Modify: `docs/ai-dev指令與資料流參考.md`
- Modify: `docs/ai-dev命令分類與設計壓力參考.md`
- Modify: `docs/report/2026-03-13-ai-dev-command-classification-assessment.md`

**Step 1: 補最後的 README / 參考文件連結**

```markdown
- `docs/ai-dev指令與資料流參考.md`
- `docs/ai-dev命令分類與設計壓力參考.md`
```

**Step 2: 執行 targeted 測試**

Run: `uv run pytest tests/test_ai_dev_command_reference.py tests/test_list_command.py tests/test_standards_command.py tests/test_hooks_command.py tests/test_init_from_command.py tests/test_sync_command.py tests/test_mem_command.py tests/test_toggle_command.py tests/test_status_command.py -v`  
Expected: PASS

**Step 3: 執行全量測試**

Run: `uv run pytest -q`  
Expected: PASS

**Step 4: 檢查工作樹狀態**

Run: `git status --short`  
Expected: 僅包含本輪預期修改。

**Step 5: 最終 commit**

```bash
git add README.md docs/ai-dev指令與資料流參考.md docs/ai-dev命令分類與設計壓力參考.md docs/report/2026-03-13-ai-dev-command-classification-assessment.md script/commands tests
git commit -m "refactor(ai-dev): 收斂命令契約與顯式副作用模型"
```

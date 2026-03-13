# ai-dev 指令面整理與 maintain 命令重構 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 將 `custom-skills` repo 自維護責任從 `project init --force`、`clone --sync-project`、`install --sync-project` 中抽離，建立 `maintain clone` / `maintain template`，並整理 ai-dev 命令面責任邊界。

**Architecture:** 新增 `maintain` 命令群，將 repo 自維護工作集中到 `script/commands/maintain.py` 與對應 utils。`project` 回歸一般專案 scaffold / hydrate / reconcile，`clone` 回歸全域分發，`project-template` 同步則改由 allowlist manifest 驅動，不再依賴 `project init --force` 的硬編碼特例。

**Tech Stack:** Python 3.13、Typer、Rich、PyYAML、pytest

**設計文件：** `docs/plans/2026-03-13-ai-dev-command-surface-design.md`

---

## Task 1: 建立 `project-template` allowlist manifest 基礎設施

**Files:**
- Create: `project-template.manifest.yaml`
- Create: `script/utils/project_template_manifest.py`
- Test: `tests/test_project_template_manifest.py`

**Step 1: Write the failing test**

```python
def test_load_project_template_manifest_reads_include_and_exclude(tmp_path: Path):
    manifest_path = tmp_path / "project-template.manifest.yaml"
    manifest_path.write_text(
        "version: 1\ninclude:\n  - AGENTS.md\n  - .standards/\nexclude:\n  - .claude/settings.local.json\n",
        encoding="utf-8",
    )

    data = load_project_template_manifest(manifest_path)

    assert data["version"] == 1
    assert "AGENTS.md" in data["include"]
    assert ".claude/settings.local.json" in data["exclude"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_project_template_manifest.py -v`
Expected: FAIL，因為 manifest loader 尚不存在

**Step 3: Write minimal implementation**

```python
def load_project_template_manifest(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {
        "version": int(data.get("version", 1)),
        "include": list(data.get("include", [])),
        "exclude": list(data.get("exclude", [])),
    }
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_project_template_manifest.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add project-template.manifest.yaml script/utils/project_template_manifest.py tests/test_project_template_manifest.py
git commit -m "功能(maintain): 新增 project-template allowlist manifest"
```

---

## Task 2: 實作 `maintain template` 的同步核心

**Files:**
- Create: `script/utils/project_template_sync.py`
- Test: `tests/test_project_template_sync.py`

**Step 1: Write the failing test**

```python
def test_sync_project_template_only_copies_manifest_included_items(tmp_path: Path):
    repo_root = tmp_path / "repo"
    template_dir = repo_root / "project-template"
    repo_root.mkdir()
    template_dir.mkdir()

    (repo_root / "AGENTS.md").write_text("root agents\n", encoding="utf-8")
    (repo_root / ".standards").mkdir()
    (repo_root / ".standards" / "testing.ai.yaml").write_text("x: 1\n", encoding="utf-8")
    (repo_root / "README.md").write_text("ignore me\n", encoding="utf-8")

    manifest = {"version": 1, "include": ["AGENTS.md", ".standards/"], "exclude": []}

    result = sync_project_template(repo_root=repo_root, template_dir=template_dir, manifest=manifest, check=False)

    assert (template_dir / "AGENTS.md").exists()
    assert (template_dir / ".standards" / "testing.ai.yaml").exists()
    assert not (template_dir / "README.md").exists()
    assert result.copied == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_project_template_sync.py -v`
Expected: FAIL，因為同步器尚不存在

**Step 3: Write minimal implementation**

```python
for entry in manifest["include"]:
    src = repo_root / normalized_path
    dst = template_dir / normalized_path
    ...
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_project_template_sync.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add script/utils/project_template_sync.py tests/test_project_template_sync.py
git commit -m "功能(maintain): 新增 project-template 同步器"
```

---

## Task 3: 新增 `ai-dev maintain template` 命令

**Files:**
- Create: `script/commands/maintain.py`
- Modify: `script/main.py`
- Test: `tests/test_maintain_command.py`

**Step 1: Write the failing test**

```python
def test_maintain_template_invokes_template_sync(runner, tmp_path, monkeypatch):
    called = {}

    def fake_sync(*, repo_root, template_dir, manifest, check):
        called["repo_root"] = repo_root
        return SimpleNamespace(copied=1, updated=0, skipped=0)

    monkeypatch.setattr(maintain_command, "sync_project_template", fake_sync)

    result = runner.invoke(app, ["maintain", "template"])

    assert result.exit_code == 0
    assert "template" in result.stdout.lower()
    assert called["repo_root"] == Path.cwd().resolve()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_maintain_command.py -v`
Expected: FAIL，因為 `maintain` 命令群尚不存在

**Step 3: Write minimal implementation**

```python
app = typer.Typer(help="維護 custom-skills 專案本身")

@app.command()
def template(check: bool = typer.Option(False, "--check")):
    ...
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_maintain_command.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add script/commands/maintain.py script/main.py tests/test_maintain_command.py
git commit -m "功能(maintain): 新增 template 子命令"
```

---

## Task 4: 移除 `project init --force` 的反向同步特例

**Files:**
- Modify: `script/commands/project.py`
- Modify: `README.md`
- Test: `tests/test_project_command.py`

**Step 1: Write the failing test**

```python
def test_project_init_force_in_custom_skills_repo_does_not_switch_to_template_sync(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = tmp_path / "repo"
    project_root.mkdir()
    (project_root / "pyproject.toml").write_text('name = "ai-dev"\n', encoding="utf-8")

    monkeypatch.setattr(project_command, "get_project_template_dir", lambda: template_dir)

    result = runner.invoke(app, ["project", "init", "--force", str(project_root)])

    assert result.exit_code == 0
    assert "反向同步模式" not in result.stdout
    assert (project_root / ".ai-dev-project.yaml").exists()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_project_command.py -v`
Expected: FAIL，因為目前 `--force` 仍會觸發模板反向同步

**Step 3: Write minimal implementation**

```python
# 刪除或移除這段分支
if force and _is_custom_skills_project(target_dir):
    ...
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_project_command.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add script/commands/project.py tests/test_project_command.py README.md
git commit -m "重構(project): 移除 init force 模板反向同步特例"
```

---

## Task 5: 實作 `maintain clone`，承接外部來源整合

**Files:**
- Modify: `script/utils/shared.py`
- Modify: `script/commands/maintain.py`
- Test: `tests/test_maintain_command.py`

**Step 1: Write the failing test**

```python
def test_maintain_clone_invokes_integrate_to_dev_project(monkeypatch):
    called = {}

    def fake_integrate(path):
        called["path"] = path

    monkeypatch.setattr(maintain_command, "integrate_to_dev_project", fake_integrate)

    result = runner.invoke(app, ["maintain", "clone"])

    assert result.exit_code == 0
    assert called["path"] == Path.cwd().resolve()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_maintain_command.py -v`
Expected: FAIL，因為 `maintain clone` 尚不存在

**Step 3: Write minimal implementation**

```python
@app.command()
def clone():
    project_root = get_project_root()
    if not _is_custom_skills_project(project_root):
        ...
    integrate_to_dev_project(project_root)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_maintain_command.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add script/commands/maintain.py script/utils/shared.py tests/test_maintain_command.py
git commit -m "功能(maintain): 新增 clone 子命令"
```

---

## Task 6: 讓 `clone` 回歸純分發責任

**Files:**
- Modify: `script/commands/clone.py`
- Modify: `README.md`
- Test: `tests/test_clone_command.py` or `tests/test_clone.py`

**Step 1: Write the failing test**

```python
def test_clone_no_longer_integrates_dev_project(monkeypatch):
    called = {"integrate": 0}

    def fake_integrate(path):
        called["integrate"] += 1

    monkeypatch.setattr(clone_command, "integrate_to_dev_project", fake_integrate)

    result = runner.invoke(app, ["clone"])

    assert result.exit_code == 0
    assert called["integrate"] == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_clone*.py -v`
Expected: FAIL，因為 `clone` 目前仍在開發目錄下整合 repo

**Step 3: Write minimal implementation**

```python
# 移除 is_dev_dir / integrate_to_dev_project 分支
copy_skills(sync_project=False, ...)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_clone*.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add script/commands/clone.py README.md
git commit -m "重構(clone): 收斂為純分發責任"
```

---

## Task 7: 移除 `install --sync-project` 的 repo 副作用

**Files:**
- Modify: `script/commands/install.py`
- Modify: `script/utils/shared.py`
- Modify: `README.md`
- Test: `tests/test_install_command.py`

**Step 1: Write the failing test**

```python
def test_install_does_not_pass_sync_project_to_copy_skills(monkeypatch):
    captured = {}

    def fake_copy_skills(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(install_command, "copy_skills", fake_copy_skills)

    result = runner.invoke(app, ["install", "--skip-npm", "--skip-bun", "--skip-repos"])

    assert result.exit_code == 0
    assert captured["sync_project"] is False
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_install_command.py -v`
Expected: FAIL，因為目前 `install` 仍沿用 `sync_project` 旗標

**Step 3: Write minimal implementation**

```python
copy_skills(sync_project=False)
```

必要時將 `--sync-project` 標記 deprecated，第一版先保留但忽略。

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_install_command.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add script/commands/install.py script/utils/shared.py README.md
git commit -m "重構(install): 移除專案同步副作用"
```

---

## Task 8: 補齊文件、help text 與回歸測試

**Files:**
- Modify: `README.md`
- Modify: `script/commands/project.py`
- Modify: `script/commands/clone.py`
- Modify: `script/commands/install.py`
- Modify: `script/commands/maintain.py`
- Test: `tests/test_project_command.py`
- Test: `tests/test_maintain_command.py`
- Test: 相關 clone/install 測試

**Step 1: Write the failing test**

```python
def test_help_text_does_not_describe_project_init_force_as_template_sync():
    result = runner.invoke(app, ["project", "init", "--help"])
    assert "反向同步到 project-template" not in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_project_command.py tests/test_maintain_command.py -v`
Expected: FAIL，因為 help 與 README 仍描述舊語意

**Step 3: Write minimal implementation**

- 更新 command help
- 更新 README 的命令分類與流程說明
- 新增 `maintain` 章節

**Step 4: Run test to verify it passes**

Run: `uv run pytest -q`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md script/commands/project.py script/commands/clone.py script/commands/install.py script/commands/maintain.py tests/
git commit -m "文件(ai-dev): 更新命令面與 maintain 工作流"
```

---

## 驗證清單

1. `uv run pytest tests/test_project_command.py tests/test_maintain_command.py -v`
2. `uv run pytest tests/test_project_template_manifest.py tests/test_project_template_sync.py -v`
3. `uv run pytest -q`
4. `uv run ai-dev maintain template --check`
5. `uv run ai-dev maintain clone`
6. `uv run ai-dev clone --help`
7. `uv run ai-dev project init --help`

---

## 交付順序建議

1. Manifest 與 template sync 基礎設施
2. `maintain template`
3. 移除 `project init --force` 特例
4. `maintain clone`
5. 收斂 `clone`
6. 收斂 `install`
7. 文件與回歸測試

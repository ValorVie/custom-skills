# Project AI Projection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 讓 ai-dev 以 manifest-based 方式將 AI 設定投影到專案內，並透過 `.git/info/exclude` 隱藏生成檔，同時保留 `.ai-dev-project.yaml` 作為專案意圖檔。

**Architecture:** 延用現有 target manifest 思維，新增 project projection manifest 與專用投影/重整流程。`project init` 只負責建立專案意圖並串接初次 hydrate，`hydrate/reconcile/doctor` 則負責生成、比對與修復專案內 AI 檔。

**Tech Stack:** Python 3.13、pytest、typer、rich、pyyaml

**設計文件：** `docs/plans/2026-03-10-project-ai-projection-design.md`

---

## Task 1: 收斂 `.ai-dev-project.yaml` 為專案意圖檔

**Files:**
- Modify: `script/utils/project_tracking.py`
- Test: `tests/test_project_tracking.py`

### Step 1: 寫 failing test — 新 schema 仍可建立與讀取

```python
def test_create_tracking_file_writes_project_intent_fields(tmp_path: Path):
    create_tracking_file(
        name="qdm-ai-base",
        url="https://github.com/ValorVie/qdm-ai-base.git",
        branch="main",
        managed_files=["AGENTS.md", ".claude/settings.local.json"],
        project_dir=tmp_path,
    )

    data = load_tracking_file(tmp_path)
    assert data["managed_by"] == "ai-dev"
    assert data["schema_version"] == "2"
    assert "project_id" in data
    assert data["projection"]["allow_local_generation"] is True
```

### Step 2: Run test to verify it fails

Run: `cd /Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills && uv run pytest tests/test_project_tracking.py -v`
Expected: FAIL，因為 `create_tracking_file()` 尚未寫入 `managed_by`、`schema_version`、`projection`

### Step 3: 寫最小實作

```python
data = {
    "managed_by": "ai-dev",
    "schema_version": "2",
    "project_id": project_id,
    "template": {...},
    "projection": {
        "targets": ["claude", "codex", "gemini"],
        "profile": "default",
        "allow_local_generation": True,
    },
    "managed_files": sorted(managed_files),
}
```

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/test_project_tracking.py -v`
Expected: PASS

### Step 5: Commit

```bash
git add tests/test_project_tracking.py script/utils/project_tracking.py
git commit -m "功能(project): 收斂專案意圖追蹤結構"
```

---

## Task 2: 新增 project projection manifest 模組

**Files:**
- Create: `script/utils/project_projection_manifest.py`
- Modify: `script/utils/paths.py`
- Test: `tests/test_project_projection_manifest.py`

### Step 1: 寫 failing test — manifest 路徑與讀寫 roundtrip

```python
def test_write_and_read_project_projection_manifest(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    manifest = {
        "managed_by": "ai-dev",
        "schema_version": "1",
        "project_id": "demo-project",
        "files": {"AGENTS.md": {"kind": "managed_block", "hash": "sha256:test"}},
    }

    write_project_manifest("demo-project", manifest)
    loaded = read_project_manifest("demo-project")

    assert loaded is not None
    assert loaded["project_id"] == "demo-project"
```

### Step 2: Run test to verify it fails

Run: `cd /Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills && uv run pytest tests/test_project_projection_manifest.py -v`
Expected: FAIL，因為模組與 helper 尚不存在

### Step 3: 寫最小實作

```python
def get_project_manifest_dir() -> Path:
    return get_ai_dev_config_dir() / "manifests" / "projects"


def get_project_manifest_path(project_id: str) -> Path:
    return get_project_manifest_dir() / f"{project_id}.yaml"
```

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/test_project_projection_manifest.py -v`
Expected: PASS

### Step 5: Commit

```bash
git add script/utils/paths.py script/utils/project_projection_manifest.py tests/test_project_projection_manifest.py
git commit -m "功能(project): 新增專案投影 manifest 模組"
```

---

## Task 3: 實作根目錄單檔的 managed block 寫入器

**Files:**
- Create: `script/utils/project_blocks.py`
- Test: `tests/test_project_blocks.py`

### Step 1: 寫 failing test — 首次寫入與二次更新都保留區塊外內容

```python
def test_upsert_managed_block_preserves_user_content(tmp_path: Path):
    target = tmp_path / "AGENTS.md"
    target.write_text("# User header\n", encoding="utf-8")

    upsert_managed_block(target, "ai-dev-project", "generated line")
    upsert_managed_block(target, "ai-dev-project", "new generated line")

    content = target.read_text(encoding="utf-8")
    assert "# User header" in content
    assert "new generated line" in content
    assert "generated line" not in content
```

### Step 2: Run test to verify it fails

Run: `cd /Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills && uv run pytest tests/test_project_blocks.py -v`
Expected: FAIL，因為 block helper 尚不存在

### Step 3: 寫最小實作

```python
MARKER_TEMPLATE_START = "<!-- >>> ai-dev:{block_id} -->"
MARKER_TEMPLATE_END = "<!-- <<< ai-dev:{block_id} -->"


def upsert_managed_block(path: Path, block_id: str, content: str) -> None:
    ...
```

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/test_project_blocks.py -v`
Expected: PASS

### Step 5: Commit

```bash
git add script/utils/project_blocks.py tests/test_project_blocks.py
git commit -m "功能(project): 新增專案單檔 managed block 工具"
```

---

## Task 4: 建立 project hydrate/reconcile 核心流程

**Files:**
- Create: `script/utils/project_projection.py`
- Modify: `script/utils/git_exclude.py`
- Modify: `script/utils/project_tracking.py`
- Modify: `script/utils/project_projection_manifest.py`
- Test: `tests/test_project_projection.py`

### Step 1: 寫 failing test — hydrate 會生成檔案並更新本機 manifest

```python
def test_hydrate_project_generates_files_and_manifest(tmp_path: Path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".git" / "info").mkdir(parents=True)

    write_project_intent(...)
    result = hydrate_project(project_root)

    assert result.generated
    assert (project_root / "AGENTS.md").exists()
    assert (project_root / ".git" / "info" / "exclude").exists()
```

### Step 2: Run test to verify it fails

Run: `cd /Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills && uv run pytest tests/test_project_projection.py -v`
Expected: FAIL，因為 hydrate/reconcile 尚未實作

### Step 3: 寫最小實作

```python
def hydrate_project(project_root: Path) -> HydrateResult:
    intent = load_tracking_file(project_root)
    patterns = derive_exclude_patterns(get_project_template_dir())
    ensure_ai_exclude(project_root, patterns)
    ...
    write_project_manifest(project_id, manifest_payload)
    return HydrateResult(generated=True, conflicts=[])
```

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/test_project_projection.py -v`
Expected: PASS

### Step 5: Commit

```bash
git add script/utils/project_projection.py script/utils/git_exclude.py script/utils/project_tracking.py script/utils/project_projection_manifest.py tests/test_project_projection.py
git commit -m "功能(project): 新增專案 hydrate 與 reconcile 流程"
```

---

## Task 5: 將 `project` CLI 改為 intent + hydrate/reconcile/doctor 模式

**Files:**
- Modify: `script/commands/project.py`
- Test: `tests/test_project_command.py`

### Step 1: 寫 failing test — `project init` 會建立意圖檔並串接 hydrate

```python
def test_project_init_creates_intent_and_hydrates(runner, tmp_path):
    result = runner.invoke(app, ["init", str(tmp_path)])

    assert result.exit_code == 0
    assert (tmp_path / ".ai-dev-project.yaml").exists()
    assert (tmp_path / "AGENTS.md").exists()
```

### Step 2: Run test to verify it fails

Run: `cd /Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills && uv run pytest tests/test_project_command.py -v`
Expected: FAIL，因為 CLI 尚未提供新命令責任切分

### Step 3: 寫最小實作

```python
@app.command()
def hydrate(...):
    ...


@app.command()
def reconcile(...):
    ...


@app.command()
def doctor(...):
    ...
```

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/test_project_command.py -v`
Expected: PASS

### Step 5: Commit

```bash
git add script/commands/project.py tests/test_project_command.py
git commit -m "功能(project): 重構專案命令責任邊界"
```

---

## Task 6: 補整合測試與回歸測試

**Files:**
- Modify: `tests/test_git_exclude.py`
- Modify: `tests/test_project_tracking.py`
- Modify: `tests/test_project_projection.py`
- Modify: `tests/test_project_command.py`

### Step 1: 寫 failing test — `git status` 不顯示生成檔

```python
def test_generated_project_ai_files_are_hidden_from_git_status(tmp_path: Path):
    project = init_git_repo(tmp_path / "project")
    hydrate_project(project)

    output = subprocess.run(
        ["git", "status", "--short"],
        cwd=project,
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    assert "AGENTS.md" not in output
    assert ".claude/" not in output
```

### Step 2: Run test to verify it fails

Run: `cd /Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills && uv run pytest tests/test_git_exclude.py tests/test_project_tracking.py tests/test_project_projection.py tests/test_project_command.py -v`
Expected: FAIL，因為 end-to-end 邊界尚未完全補齊

### Step 3: 寫最小實作

```python
# 補齊 hydrate/reconcile/doctor 中缺失的 exclude、manifest、managed block 邏輯
```

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/test_git_exclude.py tests/test_project_tracking.py tests/test_project_projection.py tests/test_project_command.py -v`
Expected: PASS

### Step 5: Commit

```bash
git add tests/test_git_exclude.py tests/test_project_tracking.py tests/test_project_projection.py tests/test_project_command.py
git commit -m "測試(project): 補齊專案投影整合與回歸測試"
```

---

## Task 7: 最終驗證與文件更新

**Files:**
- Modify: `docs/plans/2026-03-10-project-ai-projection-design.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`

### Step 1: 執行完整測試

Run: `cd /Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills && uv run pytest tests/test_git_exclude.py tests/test_project_tracking.py tests/test_project_projection_manifest.py tests/test_project_blocks.py tests/test_project_projection.py tests/test_project_command.py -v`
Expected: PASS

### Step 2: 執行手動驗證

Run: `cd /Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills && uv run ai-dev project init /tmp/ai-dev-project-demo`
Expected:
- `/tmp/ai-dev-project-demo/.ai-dev-project.yaml` 已建立
- `/tmp/ai-dev-project-demo/AGENTS.md` 與 `.claude/` 已生成
- `git status --short` 不顯示生成檔

### Step 3: 更新文件

```markdown
- README：說明 `project init / hydrate / reconcile / doctor / exclude`
- CHANGELOG：記錄 project projection manifest 與命令責任切分
```

### Step 4: Commit

```bash
git add README.md CHANGELOG.md docs/plans/2026-03-10-project-ai-projection-design.md
git commit -m "文件(project): 更新專案 AI 投影使用說明"
```

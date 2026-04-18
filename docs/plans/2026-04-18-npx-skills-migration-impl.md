# npx skills 整合與 UDS 子目錄化 — 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 讓 ai-dev 以 YAML 驅動自動安裝/更新 npx skills，把 24 個 UDS 鏡像移到 `skills/uds/`，移除 12 個改由 npx 維護的本地鏡像，並保證舊使用者可半自動遷移。

**Architecture:** 新增 `npx-skills` pipeline phase 與 `script/services/npx_skills/` 模組，專案 `upstream/npx-skills.yaml` 為權威來源，由 `repos` phase 同步到 `~/.config/ai-dev/npx-skills.yaml`。`get_source_skills()` 與 `copy_custom_skills_to_targets()` 改為支援 `skills/uds/<name>` 巢狀結構並在 target 端扁平化。

**Tech Stack:** Python 3.11+, Typer, PyYAML, Rich, npx skills CLI v1.x

**Design Spec:** `docs/plans/2026-04-18-npx-skills-migration-design.md`

---

## File Structure

### 新增
- `script/services/npx_skills/__init__.py` — 匯出 `run_npx_skills_phase`、`ensure_user_yaml`、`NpxSkillsConfig`
- `script/services/npx_skills/install.py` — YAML 載入、add/update 執行器、progress 輸出
- `script/services/npx_skills/config.py` — `NpxSkillsConfig` dataclass 與 YAML 解析
- `tests/services/npx_skills/test_config.py` — YAML 解析測試
- `tests/services/npx_skills/test_install.py` — add/update 流程測試（用 subprocess mock）
- `skills/uds/` — 24 個 UDS skill 的新家

### 修改
- `script/cli/command_manifest.py` — `PIPELINE_PHASES` 加 `"npx-skills"`；install/update 的 default/allowed phases 納入
- `script/services/pipeline/install_pipeline.py` — 分派 `npx-skills` 到 `run_npx_skills_phase(..., mode="add")`
- `script/services/pipeline/update_pipeline.py` — 分派 `npx-skills` 到 `run_npx_skills_phase(..., mode="update")`
- `script/services/repos/refresh.py` — repos phase 末尾複製 `upstream/npx-skills.yaml` 到 `~/.config/ai-dev/`
- `script/services/tools/update.py` — 偵測 ai-dev 本體升級後退出
- `script/main.py` — 新增 `install-npx-skills` 命令
- `script/utils/shared.py` — `copy_custom_skills_to_targets()` 對 `skills/uds/` 扁平化展開
- `upstream/npx-skills.yaml` — 格式對齊設計稿

### 刪除（Task 10）
- `skills/claude-api/`, `skills/skill-creator/`
- `skills/defuddle/`, `skills/json-canvas/`, `skills/obsidian-bases/`, `skills/obsidian-cli/`, `skills/obsidian-markdown/`
- `skills/codebase-onboarding/`, `skills/context-budget/`, `skills/mcp-server-patterns/`, `skills/safety-guard/`, `skills/security-scan/`

---

## Task 1: 對齊 upstream/npx-skills.yaml 格式

**Files:**
- Modify: `upstream/npx-skills.yaml`

- [ ] **Step 1：重寫 yaml 符合設計欄位**

```yaml
# npx skills 安裝清單（權威來源）
# 由 ai-dev 的 repos phase 同步到 ~/.config/ai-dev/npx-skills.yaml
# 由 npx-skills phase 讀取執行 npx skills add/update
version: 1

defaults:
  agents: "*"           # 對應 npx skills -a '*'
  scope: global         # 對應 -g
  yes: true             # 對應 --yes

packages:
  - repo: anthropics/skills
    source: anthropic-official
    rationale: Anthropic 官方維護
    skills:
      - claude-api
      - skill-creator

  - repo: kepano/obsidian-skills
    source: kepano-obsidian
    rationale: Obsidian 官方作者維護
    skills:
      - defuddle
      - json-canvas
      - obsidian-bases
      - obsidian-cli
      - obsidian-markdown

  - repo: affaan-m/everything-claude-code
    source: everything-claude-code
    rationale: 本地比對後無實質客製，改用上游
    skills:
      - codebase-onboarding
      - context-budget
      - mcp-server-patterns
      - safety-guard
      - security-scan
```

- [ ] **Step 2：提交**

```bash
git add upstream/npx-skills.yaml
git commit -m "chore(upstream): 對齊 npx-skills.yaml 格式為 defaults+packages 結構"
```

---

## Task 2: NpxSkillsConfig dataclass 與 YAML 解析

**Files:**
- Create: `script/services/npx_skills/__init__.py`
- Create: `script/services/npx_skills/config.py`
- Create: `tests/services/npx_skills/__init__.py`
- Create: `tests/services/npx_skills/test_config.py`

- [ ] **Step 1：寫失敗測試**

```python
# tests/services/npx_skills/test_config.py
from pathlib import Path
import textwrap

from script.services.npx_skills.config import NpxSkillsConfig, SkillEntry


def test_load_parses_packages_and_defaults(tmp_path: Path):
    yaml_file = tmp_path / "npx-skills.yaml"
    yaml_file.write_text(textwrap.dedent("""
        version: 1
        defaults:
          agents: "*"
          scope: global
          yes: true
        packages:
          - repo: anthropics/skills
            source: anthropic-official
            skills: [claude-api, skill-creator]
    """).strip())

    config = NpxSkillsConfig.load(yaml_file)

    assert config.version == 1
    assert config.defaults.agents == "*"
    assert config.defaults.scope == "global"
    assert config.defaults.yes is True
    assert len(config.entries) == 2
    assert config.entries[0] == SkillEntry(
        repo="anthropics/skills",
        skill="claude-api",
        source="anthropic-official",
    )


def test_load_missing_file_raises(tmp_path: Path):
    import pytest
    with pytest.raises(FileNotFoundError):
        NpxSkillsConfig.load(tmp_path / "missing.yaml")
```

- [ ] **Step 2：執行測試確認失敗**

```bash
.venv/bin/pytest tests/services/npx_skills/test_config.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'script.services.npx_skills'`

- [ ] **Step 3：實作 config.py**

```python
# script/services/npx_skills/config.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class NpxDefaults:
    agents: str = "*"
    scope: str = "global"
    yes: bool = True


@dataclass(frozen=True)
class SkillEntry:
    repo: str
    skill: str
    source: str


@dataclass(frozen=True)
class NpxSkillsConfig:
    version: int
    defaults: NpxDefaults
    entries: tuple[SkillEntry, ...]

    @classmethod
    def load(cls, path: Path) -> NpxSkillsConfig:
        if not path.exists():
            raise FileNotFoundError(f"npx-skills.yaml not found: {path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        defaults_raw = data.get("defaults", {}) or {}
        defaults = NpxDefaults(
            agents=defaults_raw.get("agents", "*"),
            scope=defaults_raw.get("scope", "global"),
            yes=bool(defaults_raw.get("yes", True)),
        )
        entries: list[SkillEntry] = []
        for pkg in data.get("packages", []) or []:
            repo = pkg["repo"]
            source = pkg.get("source", repo)
            for skill in pkg.get("skills", []) or []:
                entries.append(SkillEntry(repo=repo, skill=skill, source=source))
        return cls(
            version=int(data.get("version", 1)),
            defaults=defaults,
            entries=tuple(entries),
        )
```

```python
# script/services/npx_skills/__init__.py
from script.services.npx_skills.config import (
    NpxDefaults,
    NpxSkillsConfig,
    SkillEntry,
)

__all__ = ["NpxDefaults", "NpxSkillsConfig", "SkillEntry"]
```

- [ ] **Step 4：執行測試確認通過**

```bash
.venv/bin/pytest tests/services/npx_skills/test_config.py -v
```

Expected: PASS（2 個測試）

- [ ] **Step 5：提交**

```bash
git add script/services/npx_skills/__init__.py script/services/npx_skills/config.py tests/services/npx_skills/
git commit -m "feat(npx-skills): add NpxSkillsConfig yaml loader"
```

---

## Task 3: ensure_user_yaml() 同步邏輯

**Files:**
- Modify: `script/services/npx_skills/config.py`
- Create: `tests/services/npx_skills/test_ensure_user.py`

- [ ] **Step 1：寫失敗測試**

```python
# tests/services/npx_skills/test_ensure_user.py
from pathlib import Path

from script.services.npx_skills.config import ensure_user_yaml


def test_ensure_copies_project_to_user(tmp_path: Path):
    project = tmp_path / "project.yaml"
    project.write_text("version: 1\n")
    user = tmp_path / "user" / "npx-skills.yaml"

    result = ensure_user_yaml(project_path=project, user_path=user)

    assert result == user
    assert user.exists()
    assert user.read_text() == "version: 1\n"


def test_ensure_overwrites_user_when_project_newer(tmp_path: Path):
    project = tmp_path / "project.yaml"
    project.write_text("version: 2\n")
    user = tmp_path / "user" / "npx-skills.yaml"
    user.parent.mkdir(parents=True)
    user.write_text("version: 1\n")

    ensure_user_yaml(project_path=project, user_path=user)

    assert user.read_text() == "version: 2\n"
```

- [ ] **Step 2：執行測試確認失敗**

```bash
.venv/bin/pytest tests/services/npx_skills/test_ensure_user.py -v
```

Expected: FAIL with `ImportError: cannot import name 'ensure_user_yaml'`

- [ ] **Step 3：加入 ensure_user_yaml 到 config.py 尾端**

```python
def ensure_user_yaml(*, project_path: Path, user_path: Path) -> Path:
    """Copy project yaml to user-level location, overwriting any existing file."""
    if not project_path.exists():
        raise FileNotFoundError(f"project npx-skills.yaml missing: {project_path}")
    user_path.parent.mkdir(parents=True, exist_ok=True)
    user_path.write_bytes(project_path.read_bytes())
    return user_path
```

- [ ] **Step 4：更新 `__init__.py` 匯出**

```python
# script/services/npx_skills/__init__.py
from script.services.npx_skills.config import (
    NpxDefaults,
    NpxSkillsConfig,
    SkillEntry,
    ensure_user_yaml,
)

__all__ = [
    "NpxDefaults",
    "NpxSkillsConfig",
    "SkillEntry",
    "ensure_user_yaml",
]
```

- [ ] **Step 5：執行測試確認通過**

```bash
.venv/bin/pytest tests/services/npx_skills/ -v
```

Expected: 4 tests PASS

- [ ] **Step 6：提交**

```bash
git add script/services/npx_skills/ tests/services/npx_skills/
git commit -m "feat(npx-skills): add ensure_user_yaml for project-to-user sync"
```

---

## Task 4: install.py — add/update 執行器

**Files:**
- Create: `script/services/npx_skills/install.py`
- Create: `tests/services/npx_skills/test_install.py`

- [ ] **Step 1：寫失敗測試**

```python
# tests/services/npx_skills/test_install.py
from pathlib import Path
from unittest.mock import patch, MagicMock

from script.services.npx_skills.config import (
    NpxSkillsConfig,
    NpxDefaults,
    SkillEntry,
)
from script.services.npx_skills.install import build_add_command, build_update_command


def test_build_add_command_includes_global_and_agents():
    entry = SkillEntry(repo="anthropics/skills", skill="claude-api", source="anthropic")
    defaults = NpxDefaults(agents="*", scope="global", yes=True)

    cmd = build_add_command(entry, defaults)

    assert cmd == [
        "npx", "skills", "add",
        "anthropics/skills@claude-api",
        "-g", "-a", "*", "--yes",
    ]


def test_build_add_command_project_scope_omits_global():
    entry = SkillEntry(repo="x/y", skill="z", source="x")
    defaults = NpxDefaults(agents="claude", scope="project", yes=False)

    cmd = build_add_command(entry, defaults)

    assert "-g" not in cmd
    assert "--yes" not in cmd
    assert cmd == [
        "npx", "skills", "add",
        "x/y@z",
        "-a", "claude",
    ]


def test_build_update_command_uses_skill_only():
    entry = SkillEntry(repo="anthropics/skills", skill="claude-api", source="anthropic")
    defaults = NpxDefaults()

    cmd = build_update_command(entry, defaults)

    assert cmd == ["npx", "skills", "update", "claude-api", "-y"]
```

- [ ] **Step 2：執行測試確認失敗**

```bash
.venv/bin/pytest tests/services/npx_skills/test_install.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3：實作 install.py**

```python
# script/services/npx_skills/install.py
from __future__ import annotations

from pathlib import Path
from typing import Literal

from rich.console import Console

from script.services.npx_skills.config import (
    NpxDefaults,
    NpxSkillsConfig,
    SkillEntry,
    ensure_user_yaml,
)
from script.utils.system import run_command

console = Console()

Mode = Literal["add", "update"]


def build_add_command(entry: SkillEntry, defaults: NpxDefaults) -> list[str]:
    cmd = ["npx", "skills", "add", f"{entry.repo}@{entry.skill}"]
    if defaults.scope == "global":
        cmd.append("-g")
    cmd += ["-a", defaults.agents]
    if defaults.yes:
        cmd.append("--yes")
    return cmd


def build_update_command(entry: SkillEntry, defaults: NpxDefaults) -> list[str]:
    # npx skills update 以 skill 名稱為參數，-y 跳過確認
    return ["npx", "skills", "update", entry.skill, "-y"]


def run_npx_skills_phase(
    *,
    mode: Mode,
    project_yaml: Path,
    user_yaml: Path,
    dry_run: bool = False,
) -> None:
    """執行 npx-skills phase。mode=add 用於 install；mode=update 用於 update。"""
    ensure_user_yaml(project_path=project_yaml, user_path=user_yaml)
    config = NpxSkillsConfig.load(user_yaml)
    total = len(config.entries)

    console.print(
        f"[bold cyan][npx-skills][/bold cyan] 讀取 {user_yaml} "
        f"({total} 個 skill, {len({e.repo for e in config.entries})} 個 package)"
    )

    for idx, entry in enumerate(config.entries, start=1):
        prefix = f"[{idx}/{total}]"
        if mode == "add":
            cmd = build_add_command(entry, config.defaults)
        else:
            cmd = build_update_command(entry, config.defaults)

        console.print(f"{prefix} {entry.repo}@{entry.skill}")
        if dry_run:
            console.print(f"  [dim][dry-run] {' '.join(cmd)}[/dim]")
            continue
        result = run_command(cmd, check=False)
        if result.returncode == 0:
            console.print(f"  [green]✓[/green] 完成")
        else:
            console.print(f"  [yellow]⚠[/yellow] 退出碼 {result.returncode}（可能已裝）")
```

- [ ] **Step 4：更新 `__init__.py`**

```python
from script.services.npx_skills.config import (
    NpxDefaults,
    NpxSkillsConfig,
    SkillEntry,
    ensure_user_yaml,
)
from script.services.npx_skills.install import (
    build_add_command,
    build_update_command,
    run_npx_skills_phase,
)

__all__ = [
    "NpxDefaults", "NpxSkillsConfig", "SkillEntry", "ensure_user_yaml",
    "build_add_command", "build_update_command", "run_npx_skills_phase",
]
```

- [ ] **Step 5：執行測試確認通過**

```bash
.venv/bin/pytest tests/services/npx_skills/ -v
```

Expected: 7 tests PASS

- [ ] **Step 6：提交**

```bash
git add script/services/npx_skills/install.py script/services/npx_skills/__init__.py tests/services/npx_skills/test_install.py
git commit -m "feat(npx-skills): add install/update phase runner"
```

---

## Task 5: command_manifest.py 加入 npx-skills phase

**Files:**
- Modify: `script/cli/command_manifest.py`

- [ ] **Step 1：修改檔案**

替換 `PIPELINE_PHASES` 與 install/update 的 phases 定義：

```python
# script/cli/command_manifest.py
PIPELINE_PHASES = ("tools", "repos", "state", "npx-skills", "targets")
TARGETS = ("claude", "codex", "gemini", "opencode", "antigravity")
PIPELINE_FLAGS = ("only", "skip", "target", "dry_run")


def build_command_manifest() -> CommandManifest:
    return CommandManifest(
        commands=(
            CommandSpec(
                path=("install",),
                kind="top_level",
                default_phases=PIPELINE_PHASES,
                allowed_phases=PIPELINE_PHASES,
                allowed_targets=TARGETS,
                flags=PIPELINE_FLAGS,
                state_writers=(
                    "~/.config/custom-skills/",
                    "~/.config/ai-dev/skills/auto-skill",
                    "~/.config/ai-dev/npx-skills.yaml",
                    "~/.config/ai-dev/projections/<target>/auto-skill",
                ),
            ),
            CommandSpec(
                path=("update",),
                kind="top_level",
                default_phases=("tools", "repos", "state", "npx-skills"),
                allowed_phases=("tools", "repos", "state", "npx-skills"),
                allowed_targets=TARGETS,
                flags=PIPELINE_FLAGS,
                state_writers=(
                    "~/.config/custom-skills/",
                    "~/.config/ai-dev/skills/auto-skill",
                    "~/.config/ai-dev/npx-skills.yaml",
                ),
            ),
            CommandSpec(
                path=("clone",),
                kind="top_level",
                default_phases=("state", "targets"),
                allowed_phases=("state", "targets"),
                allowed_targets=TARGETS,
                flags=PIPELINE_FLAGS,
                state_writers=(
                    "~/.config/ai-dev/skills/auto-skill",
                    "~/.config/ai-dev/projections/<target>/auto-skill",
                ),
            ),
        )
    )
```

- [ ] **Step 2：驗證 phase 解析不壞**

```bash
.venv/bin/python -c "
from script.cli.command_manifest import build_command_manifest, PIPELINE_PHASES
m = build_command_manifest()
print('PIPELINE_PHASES:', PIPELINE_PHASES)
for spec in m.commands:
    print(spec.path, 'default:', spec.default_phases)
"
```

Expected 輸出：`PIPELINE_PHASES: ('tools', 'repos', 'state', 'npx-skills', 'targets')`；install 預設含全部 5 phase；update 預設 4 phase（無 targets）。

- [ ] **Step 3：提交**

```bash
git add script/cli/command_manifest.py
git commit -m "feat(cli): add npx-skills phase to install/update pipelines"
```

---

## Task 6: install/update pipeline 分派 npx-skills

**Files:**
- Modify: `script/services/pipeline/install_pipeline.py`
- Modify: `script/services/pipeline/update_pipeline.py`

- [ ] **Step 1：修改 install_pipeline.py**

```python
# script/services/pipeline/install_pipeline.py
from __future__ import annotations

from pathlib import Path

from rich.console import Console

from script.models.execution_plan import ExecutionPlan
from script.services.npx_skills import run_npx_skills_phase
from script.services.repos.refresh import run_repos_phase
from script.services.state.auto_skill import run_state_phase
from script.services.targets.distribute import run_targets_phase
from script.services.tools.update import run_install_postflight, run_tools_phase
from script.utils.paths import get_config_dir, get_custom_skills_dir

console = Console()


def execute_install_plan(plan: ExecutionPlan) -> None:
    if plan.dry_run:
        target_text = ", ".join(plan.targets) if plan.targets else "all"
        console.print(
            f"[bold blue][dry-run][/bold blue] install phases={', '.join(plan.phases)} targets={target_text}"
        )
        return

    console.print("[bold blue]開始安裝...[/bold blue]")
    for phase in plan.phases:
        if phase == "tools":
            run_tools_phase(plan=plan)
        elif phase == "repos":
            run_repos_phase(plan=plan)
        elif phase == "state":
            run_state_phase(plan=plan)
        elif phase == "npx-skills":
            run_npx_skills_phase(
                mode="add",
                project_yaml=get_custom_skills_dir() / "upstream" / "npx-skills.yaml",
                user_yaml=get_config_dir() / "npx-skills.yaml",
                dry_run=False,
            )
        elif phase == "targets":
            run_targets_phase(plan=plan)
        else:
            raise ValueError(f"Unsupported install phase: {phase}")

    run_install_postflight()
    console.print()
    console.print("[bold green]安裝完成！[/bold green]")
```

- [ ] **Step 2：修改 update_pipeline.py**

```python
# script/services/pipeline/update_pipeline.py
from __future__ import annotations

from rich.console import Console

from script.models.execution_plan import ExecutionPlan
from script.services.npx_skills import run_npx_skills_phase
from script.services.repos.refresh import run_repos_phase
from script.services.state.auto_skill import run_state_phase
from script.services.tools.update import run_tools_phase
from script.utils.paths import get_config_dir, get_custom_skills_dir

console = Console()


def execute_update_plan(plan: ExecutionPlan) -> None:
    if plan.dry_run:
        console.print(
            f"[bold blue][dry-run][/bold blue] update phases={', '.join(plan.phases)}"
        )
        return

    console.print("[bold blue]開始更新...[/bold blue]")
    for phase in plan.phases:
        if phase == "tools":
            run_tools_phase(plan=plan)
        elif phase == "repos":
            run_repos_phase(plan=plan)
        elif phase == "state":
            run_state_phase(plan=plan)
        elif phase == "npx-skills":
            run_npx_skills_phase(
                mode="update",
                project_yaml=get_custom_skills_dir() / "upstream" / "npx-skills.yaml",
                user_yaml=get_config_dir() / "npx-skills.yaml",
                dry_run=False,
            )
        else:
            raise ValueError(f"Unsupported update phase: {phase}")

    console.print("[bold green]更新完成！[/bold green]")
    console.print()
    console.print("[dim]提示：如需分發 Skills 到各工具目錄，請執行：ai-dev clone[/dim]")
```

- [ ] **Step 3：手動冒煙測試 dry-run**

```bash
.venv/bin/ai-dev update --dry-run --only npx-skills
```

Expected：輸出 `[dry-run] update phases=npx-skills`，無錯誤。

- [ ] **Step 4：提交**

```bash
git add script/services/pipeline/install_pipeline.py script/services/pipeline/update_pipeline.py
git commit -m "feat(pipeline): wire npx-skills phase into install/update"
```

---

## Task 7: 新增 install-npx-skills 命令

**Files:**
- Modify: `script/main.py`

- [ ] **Step 1：探索 main.py 結構**

```bash
.venv/bin/python -c "
import script.main as m
for c in m.app.registered_commands:
    print(c.name)
"
```

記下既有命令命名慣例後再加新命令。

- [ ] **Step 2：新增 install-npx-skills 命令**

在 `script/main.py` 適當位置（其他 install/update 命令附近）加入：

```python
@app.command("install-npx-skills")
def install_npx_skills_cmd(
    dry_run: bool = typer.Option(False, "--dry-run", help="顯示將執行的命令但不實際執行"),
) -> None:
    """安裝 upstream/npx-skills.yaml 列出的 skill（等同 install --only npx-skills）。"""
    from script.services.npx_skills import run_npx_skills_phase
    from script.utils.paths import get_config_dir, get_custom_skills_dir

    run_npx_skills_phase(
        mode="add",
        project_yaml=get_custom_skills_dir() / "upstream" / "npx-skills.yaml",
        user_yaml=get_config_dir() / "npx-skills.yaml",
        dry_run=dry_run,
    )
```

- [ ] **Step 3：冒煙測試**

```bash
.venv/bin/ai-dev install-npx-skills --dry-run
```

Expected：列出 12 個 skill 與將執行的 npx 命令，無實際執行。

- [ ] **Step 4：提交**

```bash
git add script/main.py
git commit -m "feat(cli): add ai-dev install-npx-skills command"
```

---

## Task 8: repos phase 同步 npx-skills.yaml 到 user-level

**Files:**
- Modify: `script/services/repos/refresh.py`

- [ ] **Step 1：找到 repos phase 結尾**

```bash
.venv/bin/grep -n "_run_update_repos_phase\|run_repos_phase" script/services/repos/refresh.py | head -5
```

- [ ] **Step 2：在 phase 尾端加入同步邏輯**

在 `run_repos_phase` 函式完成所有 git 操作後（函式尾端 return 前）加入：

```python
# 同步 npx-skills.yaml 從專案到 user-level
try:
    from script.services.npx_skills import ensure_user_yaml
    from script.utils.paths import get_config_dir, get_custom_skills_dir

    project_yaml = get_custom_skills_dir() / "upstream" / "npx-skills.yaml"
    user_yaml = get_config_dir() / "npx-skills.yaml"
    if project_yaml.exists():
        ensure_user_yaml(project_path=project_yaml, user_path=user_yaml)
        console.print(f"[dim]同步 {user_yaml.name} 到 user-level[/dim]")
except Exception as exc:  # noqa: BLE001
    console.print(f"[yellow]警告：npx-skills.yaml 同步失敗：{exc}[/yellow]")
```

- [ ] **Step 3：冒煙測試**

```bash
rm -f ~/.config/ai-dev/npx-skills.yaml
.venv/bin/ai-dev update --only repos
ls -l ~/.config/ai-dev/npx-skills.yaml
```

Expected：`~/.config/ai-dev/npx-skills.yaml` 存在，內容等同 `upstream/npx-skills.yaml`。

- [ ] **Step 4：提交**

```bash
git add script/services/repos/refresh.py
git commit -m "feat(repos): sync upstream/npx-skills.yaml to ~/.config/ai-dev"
```

---

## Task 9: tools phase 偵測 ai-dev 本體升級後退出（M4）

**Files:**
- Modify: `script/services/tools/update.py`

- [ ] **Step 1：探索 ai-dev 本體升級位置**

```bash
.venv/bin/grep -n "custom-skills\|ai-dev.*install\|editable\|pip install" script/services/tools/update.py | head -10
```

確認 `run_tools_phase` 內升級 ai-dev 本身的指令位置（預期為 `pip install -e` 或 `uv sync` 附近）。

- [ ] **Step 2：在 run_tools_phase 起頭記錄版本**

```python
# script/services/tools/update.py 頂端新增：
from script.utils.paths import get_custom_skills_dir


def _read_ai_dev_version() -> str | None:
    try:
        pyproject = get_custom_skills_dir() / "pyproject.toml"
        if not pyproject.exists():
            return None
        import tomllib
        return tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]
    except Exception:
        return None
```

- [ ] **Step 3：修改 run_tools_phase**

在 `run_tools_phase` 函式最開頭記錄版本、執行升級後比對：

```python
def run_tools_phase(plan: ExecutionPlan) -> None:
    version_before = _read_ai_dev_version()

    # ...現有升級邏輯不動...

    version_after = _read_ai_dev_version()
    if version_before and version_after and version_before != version_after:
        console.print()
        console.print(
            f"[bold yellow]⚠  ai-dev 本體已升級 {version_before} → {version_after}[/bold yellow]"
        )
        console.print("[yellow]請重新執行原本的命令，以確保後續 phase 使用新程式。[/yellow]")
        import sys
        sys.exit(0)
```

- [ ] **Step 4：冒煙測試（非破壞性）**

```bash
# 在未升級版本的情況下跑，應無警告
.venv/bin/ai-dev update --only tools --dry-run
```

Expected：無升級提示（因為沒實際變動版本）。

- [ ] **Step 5：提交**

```bash
git add script/services/tools/update.py
git commit -m "feat(tools): exit early when ai-dev itself was upgraded (M4)"
```

---

## Task 10: shared.py 支援 skills/uds/ 扁平化分發

**Files:**
- Modify: `script/utils/shared.py`

- [ ] **Step 1：定位 skills 分發迴圈**

在 `copy_custom_skills_to_targets()` 內找到 L1204 附近：

```python
if resource_type == "skills":
    for item in src.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            ...
```

- [ ] **Step 2：改為遞迴展開指定子目錄**

加一個輔助函式於 `shared.py`（靠近 L1100 工具函式區）：

```python
SKILL_SUBDIRS = ("uds",)  # 將來可擴充為其他子目錄分類

def _iter_skill_source_dirs(src: Path):
    """回傳所有應被視為 skill 的來源目錄（扁平化 skills/<name>/ 與 skills/<subdir>/<name>/）。"""
    for item in src.iterdir():
        if not item.is_dir() or item.name.startswith("."):
            continue
        if item.name in SKILL_SUBDIRS:
            # 展開子目錄
            for child in item.iterdir():
                if child.is_dir() and not child.name.startswith("."):
                    yield child
        else:
            yield item
```

把 L1204 起的迴圈改為：

```python
if resource_type == "skills":
    for item in _iter_skill_source_dirs(src):
        if _load_clone_policy(item, show_warning=False) is not None:
            continue
        if record_method:
            record_method(item.name, item, source="custom-skills")
```

也要修改 L1005、L1038、L1054 等其他對 `src.iterdir()` 且 `resource_type == "skills"` 的地方。以 Grep 再掃一次確認覆蓋全部位置。

- [ ] **Step 3：加入測試（單元）**

Create `tests/utils/test_iter_skill_source_dirs.py`:

```python
from pathlib import Path

from script.utils.shared import _iter_skill_source_dirs


def test_flat_and_uds_subdir(tmp_path: Path):
    (tmp_path / "flat-skill").mkdir()
    (tmp_path / "uds").mkdir()
    (tmp_path / "uds" / "uds-skill-a").mkdir()
    (tmp_path / "uds" / "uds-skill-b").mkdir()
    (tmp_path / ".hidden").mkdir()

    names = sorted(d.name for d in _iter_skill_source_dirs(tmp_path))

    assert names == ["flat-skill", "uds-skill-a", "uds-skill-b"]
```

- [ ] **Step 4：執行測試**

```bash
.venv/bin/pytest tests/utils/test_iter_skill_source_dirs.py -v
```

Expected：PASS

- [ ] **Step 5：冒煙測試 clone dry-run**

```bash
# 先製造一個假 uds 子目錄驗證（不提交）
mkdir -p /tmp/test-uds-skill/SKILL.md || true
.venv/bin/ai-dev clone --dry-run
```

Expected：不報錯。

- [ ] **Step 6：提交**

```bash
git add script/utils/shared.py tests/utils/test_iter_skill_source_dirs.py
git commit -m "feat(clone): support skills/uds/ subdir with flat target distribution"
```

---

## Task 11: 遷移 24 個 UDS skill 到 skills/uds/

**Files:**
- Move: 24 個 skill 從 `skills/` 到 `skills/uds/`

- [ ] **Step 1：建立目錄並 git mv**

```bash
mkdir -p skills/uds
for s in \
  ai-collaboration-standards ai-friendly-architecture ai-instruction-standards \
  atdd-assistant bdd-assistant changelog-guide checkin-assistant \
  code-review-assistant commit-standards docs-generator documentation-guide \
  error-code-guide forward-derivation git-workflow-guide logging-guide \
  methodology-system project-structure-guide refactoring-assistant \
  release-standards requirement-assistant reverse-engineer spec-driven-dev \
  test-coverage-assistant testing-guide; do
  git mv "skills/$s" "skills/uds/$s"
done
```

- [ ] **Step 2：驗證結構**

```bash
ls skills/uds/ | wc -l  # 應為 24
ls skills/ | grep -c "^uds$"  # 應為 1
```

- [ ] **Step 3：冒煙測試 clone dry-run**

```bash
.venv/bin/ai-dev clone --dry-run --target claude
```

Expected：dry-run 輸出含 24 個 uds skill 名稱（扁平化後）。

- [ ] **Step 4：提交**

```bash
git commit -m "refactor(skills): move 24 UDS mirrored skills under skills/uds/"
```

---

## Task 12: 安裝 npx 版並移除 12 個本地鏡像

**Files:**
- Delete: 12 個 skill 目錄

- [ ] **Step 1：確保 ai-dev 已 pip install -e（或 bun 對應）最新版**

```bash
# 視專案設定，常見為：
.venv/bin/pip install -e .
# 或
uv sync
```

- [ ] **Step 2：執行 install-npx-skills**

```bash
.venv/bin/ai-dev install-npx-skills
```

Expected：輸出 12 行 skill 安裝進度，每行最後 ✓。

- [ ] **Step 3：驗證 target 端已被 npx 版覆蓋**

```bash
cat ~/.claude/skills/claude-api/SKILL.md | head -5
cat ~/.claude/skills/skill-creator/SKILL.md | head -5
```

Expected：看到 `name: claude-api`／`skill-creator` 等欄位，且若 npx 版有 `version` 欄位則顯示為上游版本。

- [ ] **Step 4：git rm 12 個本地 skill**

```bash
git rm -r \
  skills/claude-api skills/skill-creator \
  skills/defuddle skills/json-canvas skills/obsidian-bases \
  skills/obsidian-cli skills/obsidian-markdown \
  skills/codebase-onboarding skills/context-budget \
  skills/mcp-server-patterns skills/safety-guard skills/security-scan
```

- [ ] **Step 5：驗證清除**

```bash
ls skills/ | grep -cE "^(claude-api|skill-creator|defuddle|json-canvas|obsidian-bases|obsidian-cli|obsidian-markdown|codebase-onboarding|context-budget|mcp-server-patterns|safety-guard|security-scan)$"
```

Expected：0

- [ ] **Step 6：ai-dev clone --dry-run 確認不再嘗試複製這 12 個**

```bash
.venv/bin/ai-dev clone --dry-run --target claude
```

Expected：輸出不含這 12 個 skill 名稱作為待複製項目。

- [ ] **Step 7：寫遷移 marker**

```bash
touch ~/.config/ai-dev/.npx-migration-v1-done
```

- [ ] **Step 8：提交**

```bash
git commit -m "chore(skills): remove 12 local mirrors now managed via npx skills"
```

---

## Task 13: 更新文件

**Files:**
- Modify: `docs/ai-dev指令與資料流參考.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/report/2026-04-18-npx-skills-coverage-audit.md`

- [ ] **Step 1：ai-dev 資料流參考新增 npx-skills phase**

編輯 `docs/ai-dev指令與資料流參考.md`，在 pipeline phases 表格加入：

```markdown
| `npx-skills` | install、update | 讀 `~/.config/ai-dev/npx-skills.yaml`；`install` 模式跑 `npx skills add`、`update` 模式跑 `npx skills update`。首次會自動從 `upstream/npx-skills.yaml` 同步到 user-level |
```

同時新增 `install-npx-skills` 命令條目。

- [ ] **Step 2：CHANGELOG.md 新增條目**

在 `## [Unreleased]` 下加入：

```markdown
### Added
- `ai-dev install-npx-skills` 命令：依 `upstream/npx-skills.yaml` 批次安裝 npx skills
- 新 pipeline phase `npx-skills`，整合進 install/update 預設流程
- `upstream/npx-skills.yaml`：定義由 npx 維護的官方/權威 skill 清單
- `skills/uds/` 子目錄：明確標示 UDS 鏡像 skill 來源

### Changed
- `copy_custom_skills_to_targets` 支援 `skills/uds/` 扁平化展開
- `tools` phase 偵測到 ai-dev 本體升級後退出，提示重新執行

### Removed
- 12 個本地 skill 鏡像（改由 npx skills 安裝）：claude-api, skill-creator, defuddle, json-canvas, obsidian-bases, obsidian-cli, obsidian-markdown, codebase-onboarding, context-budget, mcp-server-patterns, safety-guard, security-scan
```

- [ ] **Step 3：更新盤點報告狀態**

在 `docs/report/2026-04-18-npx-skills-coverage-audit.md` 結尾加入：

```markdown
---

## 執行結果（2026-04-18）

- A 組 7 個與 B 組 5 個共 12 個 skill 已改用 npx 維護（見 `upstream/npx-skills.yaml`）
- C 組 24 個 UDS 鏡像已移至 `skills/uds/`
- 實作計畫：`docs/plans/2026-04-18-npx-skills-migration-impl.md`
- 設計稿：`docs/plans/2026-04-18-npx-skills-migration-design.md`
```

- [ ] **Step 4：提交**

```bash
git add docs/ai-dev指令與資料流參考.md CHANGELOG.md docs/report/2026-04-18-npx-skills-coverage-audit.md
git commit -m "docs: 更新 ai-dev 資料流、CHANGELOG 與 npx skills 盤點報告"
```

---

## Task 14: 端到端驗證

- [ ] **Step 1：乾淨環境模擬**

```bash
# 備份現有 user-level state
cp -r ~/.config/ai-dev ~/.config/ai-dev.backup.$(date +%Y%m%d)
rm -f ~/.config/ai-dev/npx-skills.yaml ~/.config/ai-dev/.npx-migration-v1-done
```

- [ ] **Step 2：跑完整 install**

```bash
.venv/bin/ai-dev install
```

Expected：依序跑 `tools → repos → state → npx-skills → targets`，最後提示安裝完成。

- [ ] **Step 3：檢查所有目標目錄存在 npx 版 skill**

```bash
for target in ~/.claude/skills ~/.codex/skills ~/.config/gemini/skills; do
  echo "=== $target ==="
  ls "$target" 2>/dev/null | grep -E "^(claude-api|skill-creator|defuddle|obsidian-markdown)$"
done
```

Expected：各 target 皆含對應 skill 目錄。

- [ ] **Step 4：跑 update 確認 npx-skills phase 用 update 模式**

```bash
.venv/bin/ai-dev update --only npx-skills
```

Expected：輸出顯示 12 個 skill 跑 `npx skills update`，無錯誤。

- [ ] **Step 5：`--skip` 逃生閥測試**

```bash
.venv/bin/ai-dev update --skip npx-skills --dry-run
```

Expected：輸出 phases 不含 `npx-skills`。

---

## Self-Review Checklist（寫完後自我檢查）

- [ ] 每個 yaml 欄位在 Task 1 已定義且對應 dataclass
- [ ] Task 2 的 `SkillEntry` 結構與 Task 4 的 `build_add_command` 參數一致
- [ ] Task 5 的 `PIPELINE_PHASES` tuple 順序與 Task 6 的 dispatch 迴圈順序一致
- [ ] Task 10 的 `SKILL_SUBDIRS = ("uds",)` 與 Task 11 搬移目標 `skills/uds/` 一致
- [ ] Task 12 移除的 12 個 skill 名稱與 Task 1 yaml 內 skills 列表完全一致
- [ ] 無 TBD/TODO/占位敘述
- [ ] 每個測試步驟都有實際程式碼
- [ ] 每個 commit 訊息符合 commit-message.ai.yaml 規範（英文類型 + 中文訊息或通用短句）

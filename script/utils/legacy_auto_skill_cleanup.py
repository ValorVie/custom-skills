"""偵測並安全移除已退役的 auto-skill 安裝。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Callable, Literal

import typer
from rich.console import Console

console = Console()

PLUGIN_ID = "auto-skill-hooks@custom-skills"
CleanupStatus = Literal[
    "not-found", "dry-run", "non-interactive", "declined", "removed"
]
Confirm = Callable[..., bool]
PluginUninstaller = Callable[[tuple[str, ...], Path], None]

LEGACY_PROTOCOL_RE = re.compile(
    r"(?m)^## 任務啟動協議 \(強制\)\s*\n"
    r"(?:\s*\n)?"
    r"[*-] 當開啟新任務或觸發任何技能時，必須先讀取並執行 "
    r"`?auto-skill`? 技能的 `?SKILL\.md`?。\s*\n?"
)
LEGACY_ROUTING_RE = re.compile(
    r"(?m)^- `?auto-skill`? 只負責知識與經驗載入，不構成啟動高階工作流、"
    r"修改 tracker 或執行(?:\n  )?其他具副作用操作的授權。\s*\n?"
)


@dataclass(frozen=True)
class CleanupPath:
    label: str
    path: Path


@dataclass(frozen=True)
class CleanupPlan:
    scope: str
    paths: tuple[CleanupPath, ...]
    instruction_files: tuple[Path, ...]
    plugin_scopes: tuple[str, ...] = ()
    plugin_backup_paths: tuple[CleanupPath, ...] = ()

    @property
    def found(self) -> bool:
        return bool(self.paths or self.instruction_files or self.plugin_scopes)


@dataclass(frozen=True)
class CleanupResult:
    status: CleanupStatus
    backup_dir: Path | None = None
    removed_paths: tuple[Path, ...] = ()
    edited_files: tuple[Path, ...] = ()
    plugin_removed: bool = False


def _lexists(path: Path) -> bool:
    return os.path.lexists(path)


def _clean_instruction_text(text: str) -> str:
    return LEGACY_ROUTING_RE.sub("", LEGACY_PROTOCOL_RE.sub("", text))


def _has_legacy_instruction(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    return _clean_instruction_text(text) != text


def _existing(label: str, path: Path) -> CleanupPath | None:
    return CleanupPath(label, path) if _lexists(path) else None


def _dedupe(items: list[CleanupPath]) -> tuple[CleanupPath, ...]:
    seen: set[str] = set()
    result: list[CleanupPath] = []
    for item in items:
        key = os.path.abspath(item.path)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return tuple(result)


def _read_user_plugin(home: Path) -> tuple[tuple[str, ...], tuple[CleanupPath, ...]]:
    config_path = home / ".claude" / "plugins" / "installed_plugins.json"
    if not config_path.is_file():
        return (), ()
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return (), ()

    entries = data.get("plugins", {}).get(PLUGIN_ID, [])
    if not isinstance(entries, list):
        return (), ()
    user_entries = [entry for entry in entries if entry.get("scope", "user") == "user"]
    if not user_entries:
        return (), ()

    plugin_root = (home / ".claude" / "plugins").resolve(strict=False)
    backup_paths = [CleanupPath("claude-plugin-registry", config_path)]
    for index, entry in enumerate(user_entries, start=1):
        raw_path = entry.get("installPath")
        if not isinstance(raw_path, str):
            continue
        install_path = Path(raw_path).expanduser()
        try:
            inside_plugin_root = install_path.resolve(strict=False).is_relative_to(
                plugin_root
            )
        except OSError:
            inside_plugin_root = False
        if inside_plugin_root and _lexists(install_path):
            backup_paths.append(
                CleanupPath(f"claude-plugin-install-{index}", install_path)
            )
    return ("user",), _dedupe(backup_paths)


def _global_plan(home: Path) -> CleanupPlan:
    paths: list[CleanupPath] = []
    fixed_paths = (
        (
            "distribution-source",
            home / ".config" / "custom-skills" / "skills" / "auto-skill",
        ),
        ("canonical-state", home / ".config" / "ai-dev" / "skills" / "auto-skill"),
        ("upstream-repo", home / ".config" / "auto-skill"),
        ("claude-projection", home / ".claude" / "skills" / "auto-skill"),
        ("shared-agent-projection", home / ".agents" / "skills" / "auto-skill"),
        ("legacy-codex-projection", home / ".codex" / "skills" / "auto-skill"),
        ("agy-projection", home / ".gemini" / "skills" / "auto-skill"),
        (
            "antigravity-projection",
            home / ".gemini" / "antigravity" / "global_skills" / "auto-skill",
        ),
        (
            "opencode-projection",
            home / ".config" / "opencode" / "skills" / "auto-skill",
        ),
        ("kiro-projection", home / ".kiro" / "skills" / "auto-skill"),
        (
            "claude-plugin-cache",
            home
            / ".claude"
            / "plugins"
            / "cache"
            / "custom-skills"
            / "auto-skill-hooks",
        ),
        (
            "claude-plugin-data-marketplace",
            home
            / ".claude"
            / "plugins"
            / "data"
            / "custom-skills"
            / "auto-skill-hooks",
        ),
        (
            "claude-plugin-data",
            home / ".claude" / "plugins" / "data" / "auto-skill-hooks",
        ),
        (
            "claude-plugin-data-qualified",
            home / ".claude" / "plugins" / "data" / "auto-skill-hooks@custom-skills",
        ),
    )
    for label, path in fixed_paths:
        item = _existing(label, path)
        if item:
            paths.append(item)

    projection_root = home / ".config" / "ai-dev" / "projections"
    if projection_root.is_dir():
        for target_dir in sorted(projection_root.iterdir(), key=lambda path: path.name):
            for suffix, label in (
                ("auto-skill", "shadow"),
                ("auto-skill.state.json", "shadow-state"),
            ):
                item = _existing(f"{label}-{target_dir.name}", target_dir / suffix)
                if item:
                    paths.append(item)

    instruction_candidates = (
        home / ".claude" / "CLAUDE.md",
        home / ".codex" / "instructions.md",
        home / ".gemini" / "GEMINI.md",
        home / ".cursor" / "rules" / "global.mdc",
    )
    instruction_files = tuple(
        path for path in instruction_candidates if _has_legacy_instruction(path)
    )
    plugin_scopes, plugin_backup_paths = _read_user_plugin(home)
    return CleanupPlan(
        scope="global",
        paths=_dedupe(paths),
        instruction_files=instruction_files,
        plugin_scopes=plugin_scopes,
        plugin_backup_paths=plugin_backup_paths,
    )


def _project_plan(project_dir: Path) -> CleanupPlan:
    project_dir = project_dir.absolute()
    relative_paths = (
        "skills/auto-skill",
        ".claude/skills/auto-skill",
        ".agents/skills/auto-skill",
        ".codex/skills/auto-skill",
        ".gemini/skills/auto-skill",
        ".agent/skills/auto-skill",
        ".opencode/skills/auto-skill",
        ".kiro/skills/auto-skill",
    )
    paths = [
        item
        for relative in relative_paths
        if (item := _existing(relative, project_dir / relative)) is not None
    ]
    instruction_candidates = (
        *(
            project_dir / name
            for name in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", "INSTRUCTIONS.md")
        ),
        project_dir / ".claude" / "CLAUDE.md",
        project_dir / ".codex" / "instructions.md",
        project_dir / ".gemini" / "GEMINI.md",
    )
    instruction_files = tuple(
        path for path in instruction_candidates if _has_legacy_instruction(path)
    )
    return CleanupPlan(
        scope=f"project:{project_dir}",
        paths=_dedupe(paths),
        instruction_files=instruction_files,
    )


def _kind(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if path.is_dir():
        return "directory"
    return "file"


def _copy_to_backup(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        destination.symlink_to(os.readlink(source), target_is_directory=source.is_dir())
    elif source.is_dir():
        shutil.copytree(source, destination, symlinks=True)
    else:
        shutil.copy2(source, destination)


def _backup_plan(plan: CleanupPlan, home: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S_%f")
    backup_dir = (
        home / ".config" / "ai-dev" / "backups" / "auto-skill-removal" / timestamp
    )
    items: list[tuple[CleanupPath, str]] = [
        *((item, "delete") for item in plan.paths),
        *(
            (CleanupPath(f"instruction-{index}", path), "edit")
            for index, path in enumerate(plan.instruction_files, start=1)
        ),
        *((item, "plugin-backup") for item in plan.plugin_backup_paths),
    ]
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, (item, action) in enumerate(items, start=1):
        key = os.path.abspath(item.path)
        if key in seen or not _lexists(item.path):
            continue
        seen.add(key)
        safe_label = re.sub(r"[^a-zA-Z0-9._-]+", "-", item.label).strip("-")
        relative_backup = Path("items") / f"{index:02d}-{safe_label}"
        _copy_to_backup(item.path, backup_dir / relative_backup)
        entry = {
            "label": item.label,
            "original": str(item.path),
            "backup": relative_backup.as_posix(),
            "kind": _kind(item.path),
            "action": action,
        }
        if item.path.is_symlink():
            entry["link_target"] = os.readlink(item.path)
        entries.append(entry)

    backup_dir.mkdir(parents=True, exist_ok=True)
    audit = {
        "schema_version": 1,
        "scope": plan.scope,
        "created_at": datetime.now().astimezone().isoformat(),
        "plugin": PLUGIN_ID if plan.plugin_scopes else None,
        "plugin_scopes": list(plan.plugin_scopes),
        "entries": entries,
    }
    (backup_dir / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return backup_dir


def _default_plugin_uninstaller(scopes: tuple[str, ...], cwd: Path) -> None:
    if shutil.which("claude") is None:
        raise RuntimeError(
            f"偵測到 {PLUGIN_ID}，但找不到 claude 指令，無法安全解除安裝"
        )
    for scope in scopes:
        completed = subprocess.run(
            ["claude", "plugin", "uninstall", PLUGIN_ID, "--scope", scope],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()
            raise RuntimeError(
                f"解除安裝 {PLUGIN_ID} 失敗（scope={scope}）：{detail or 'unknown error'}"
            )


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _display_path(path: Path, home: Path) -> str:
    try:
        return f"~/{path.relative_to(home).as_posix()}"
    except ValueError:
        return str(path)


def _execute_cleanup(
    plan: CleanupPlan,
    *,
    home: Path,
    dry_run: bool,
    interactive: bool | None,
    confirm: Confirm,
    plugin_uninstaller: PluginUninstaller,
) -> CleanupResult:
    if not plan.found:
        return CleanupResult(status="not-found")

    mode = "全域" if plan.scope == "global" else "專案"
    console.print(f"[yellow]auto-skill 功能已移除，偵測到{mode}舊安裝：[/yellow]")
    for item in plan.paths:
        console.print(f"  [yellow]-[/yellow] {_display_path(item.path, home)}")
    for path in plan.instruction_files:
        console.print(f"  [yellow]-[/yellow] {_display_path(path, home)}（舊啟動規則）")
    if plan.plugin_scopes:
        console.print(f"  [yellow]-[/yellow] Claude plugin: {PLUGIN_ID}")

    if dry_run:
        console.print("[dim][dry-run] 僅顯示舊安裝，不會備份、刪除或解除安裝。[/dim]")
        return CleanupResult(status="dry-run")

    if interactive is None:
        interactive = sys.stdin.isatty()
    if not interactive:
        console.print(
            "[yellow]非互動模式不會自動刪除；已保留舊安裝。"
            "請在互動式終端重新執行此命令。[/yellow]"
        )
        return CleanupResult(status="non-interactive")

    if not confirm("是否先備份再刪除上述 auto-skill 舊安裝？", default=False):
        console.print("[dim]已保留 auto-skill 舊安裝。[/dim]")
        return CleanupResult(status="declined")

    backup_dir = _backup_plan(plan, home)
    console.print(f"[dim]備份目錄：{_display_path(backup_dir, home)}[/dim]")

    if plan.plugin_scopes:
        plugin_uninstaller(plan.plugin_scopes, home)

    removed: list[Path] = []
    for item in plan.paths:
        if _lexists(item.path):
            _remove_path(item.path)
            removed.append(item.path)

    edited: list[Path] = []
    for path in plan.instruction_files:
        text = path.read_text(encoding="utf-8")
        cleaned = _clean_instruction_text(text)
        if cleaned != text:
            path.write_text(cleaned, encoding="utf-8")
            edited.append(path)

    console.print("[green]已移除 auto-skill 舊安裝；需要還原時請使用上述備份。[/green]")
    return CleanupResult(
        status="removed",
        backup_dir=backup_dir,
        removed_paths=tuple(removed),
        edited_files=tuple(edited),
        plugin_removed=bool(plan.plugin_scopes),
    )


def cleanup_global_auto_skill(
    *,
    home: Path | None = None,
    dry_run: bool = False,
    interactive: bool | None = None,
    confirm: Confirm = typer.confirm,
    plugin_uninstaller: PluginUninstaller = _default_plugin_uninstaller,
) -> CleanupResult:
    """清理使用者層級的 auto-skill；沒有互動確認時只回報。"""
    home = (home or Path.home()).absolute()
    return _execute_cleanup(
        _global_plan(home),
        home=home,
        dry_run=dry_run,
        interactive=interactive,
        confirm=confirm,
        plugin_uninstaller=plugin_uninstaller,
    )


def cleanup_project_auto_skill(
    project_dir: Path,
    *,
    home: Path | None = None,
    interactive: bool | None = None,
    confirm: Confirm = typer.confirm,
) -> CleanupResult:
    """清理專案層級的 auto-skill；沒有互動確認時只回報。"""
    home = (home or Path.home()).absolute()
    return _execute_cleanup(
        _project_plan(project_dir),
        home=home,
        dry_run=False,
        interactive=interactive,
        confirm=confirm,
        plugin_uninstaller=_default_plugin_uninstaller,
    )

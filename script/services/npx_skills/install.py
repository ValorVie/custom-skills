from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console

from script.services.npx_skills.config import (
    NpxDefaults,
    NpxSkillsConfig,
    SkillEntry,
    ensure_user_yaml,
)
from script.services.npx_skills.first_party_overlay import FirstPartyStateStore
from script.services.npx_skills.first_party_reconcile import FirstPartyReconciler
from script.services.npx_skills.migration import (
    FIRST_PARTY_SOURCE,
    manifest_names_for_detach,
)
from script.utils.system import check_command_exists, run_command
from script.utils.paths import (
    get_npx_first_party_backup_dir,
    get_npx_first_party_guard_path,
    get_npx_first_party_overlay_dir,
    get_npx_first_party_transaction_dir,
)

console = Console()

Mode = Literal["add", "update"]


def group_entries_by_repo(
    entries: Sequence[SkillEntry],
) -> tuple[tuple[SkillEntry, ...], ...]:
    """依 manifest 順序分組，同一 repository 只執行一次 npx command。"""
    grouped: dict[str, list[SkillEntry]] = {}
    for entry in entries:
        grouped.setdefault(entry.repo, []).append(entry)
    return tuple(tuple(group) for group in grouped.values())


def _single_repo(entries: Sequence[SkillEntry]) -> str:
    if not entries:
        raise ValueError("npx command 至少需要一個 skill")
    repositories = {entry.repo for entry in entries}
    if len(repositories) != 1:
        raise ValueError("同一個 npx command 只能處理同一個 repository")
    return entries[0].repo


def build_add_command(
    entries: Sequence[SkillEntry], defaults: NpxDefaults
) -> list[str]:
    repo = _single_repo(entries)
    cmd = ["npx", "skills", "add", repo]
    for entry in entries:
        cmd += ["--skill", entry.skill]
    if defaults.scope == "global":
        cmd.append("-g")
    cmd += ["-a", *defaults.agents]
    if defaults.yes:
        cmd.append("--yes")
    return cmd


def build_update_command(
    entries: Sequence[SkillEntry], defaults: NpxDefaults
) -> list[str]:
    _single_repo(entries)
    # 第三方 packages 保留原生 update；第一方不走這個入口。
    cmd = ["npx", "skills", "update", *(entry.skill for entry in entries)]
    if defaults.scope == "global":
        cmd.append("-g")
    if defaults.yes:
        cmd.append("-y")
    return cmd


def _create_first_party_reconciler(guard_path: Path) -> FirstPartyReconciler:
    return FirstPartyReconciler(
        state_store=FirstPartyStateStore(
            guard_path,
            get_npx_first_party_overlay_dir(),
        ),
        backup_root=get_npx_first_party_backup_dir(),
        transaction_root=get_npx_first_party_transaction_dir(),
        output_func=console.print,
    )


def _run_first_party_group(
    entries: Sequence[SkillEntry],
    defaults: NpxDefaults,
    *,
    dry_run: bool,
    guard_path: Path,
) -> tuple[tuple[str, ...], bool]:
    reconciler = _create_first_party_reconciler(guard_path)
    result = reconciler.reconcile(entries, defaults, dry_run=dry_run)
    for backup in result.backup_paths:
        console.print(f"  [yellow]保留本機內容備份：{backup}[/yellow]")
    return result.successful_names, bool(result.failed_names or result.aborted)


def run_npx_skills_phase(
    *,
    mode: Mode,
    project_yaml: Path,
    user_yaml: Path,
    dry_run: bool = False,
    first_party_guard_path: Path | None = None,
) -> None:
    """執行 npx-skills phase。mode=add 用於 install；mode=update 用於 update。"""
    if not check_command_exists("npx"):
        console.print(
            "[red]✗ npx 未安裝，略過 npx-skills phase。請先安裝 Node.js（或 npm/npx）。[/red]"
        )
        return

    if not project_yaml.exists():
        console.print(
            f"[yellow]⚠ 找不到 {project_yaml}，略過 npx-skills phase。[/yellow]\n"
            "[dim]   custom-skills clone 可能過時，請執行 "
            "`cd ~/.config/custom-skills && git pull` 後重試。[/dim]"
        )
        return

    config_path = project_yaml
    if not dry_run:
        config_path = ensure_user_yaml(project_path=project_yaml, user_path=user_yaml)
    config = NpxSkillsConfig.load(config_path)
    groups = group_entries_by_repo(config.entries)
    total_skills = len(config.entries)
    total_packages = len(groups)

    console.print(
        f"[bold cyan][npx-skills][/bold cyan] 讀取 {config_path} "
        f"({total_skills} 個 skill, {total_packages} 個 package)"
    )

    successful_names: list[str] = []
    verified_first_party: list[str] = []
    failed_packages: list[tuple[str, int]] = []
    guard_path = first_party_guard_path or get_npx_first_party_guard_path()
    for idx, group in enumerate(groups, start=1):
        prefix = f"[{idx}/{total_packages}]"
        repo = group[0].repo
        skill_names = [entry.skill for entry in group]
        console.print(f"{prefix} {repo} ({len(skill_names)} 個 skills)")
        is_first_party = all(entry.source == FIRST_PARTY_SOURCE for entry in group)
        if is_first_party:
            try:
                group_successful, group_failed = _run_first_party_group(
                    group,
                    config.defaults,
                    dry_run=dry_run,
                    guard_path=guard_path,
                )
            except (OSError, RuntimeError, ValueError) as exc:
                console.print(f"  [red]✗ 第一方 reconcile 失敗：{exc}[/red]")
                group_successful = ()
                group_failed = True
            successful_names.extend(group_successful)
            verified_first_party.extend(group_successful)
            if group_failed and not dry_run:
                failed_packages.append((repo, 1))
            elif not dry_run:
                console.print("  [green]✓[/green] 完成")
            continue

        if dry_run:
            if mode == "add":
                cmd = build_add_command(group, config.defaults)
            else:
                cmd = build_update_command(group, config.defaults)
            console.print(f"  [dim][dry-run] {' '.join(cmd)}[/dim]")
            continue

        if mode == "add":
            cmd = build_add_command(group, config.defaults)
        else:
            cmd = build_update_command(group, config.defaults)

        result = run_command(cmd, check=False)
        if result.returncode == 0:
            successful_names.extend(entry.skill for entry in group)
            console.print("  [green]✓[/green] 完成")
        else:
            failed_packages.append((repo, result.returncode))
            hint = ""
            if mode == "update":
                hint = "（skill 可能尚未安裝，請先執行 ai-dev install-npx-skills）"
            console.print(f"  [red]✗[/red] 退出碼 {result.returncode}{hint}")

    # add 成功項目與 reconcile 驗證完成的第一方項目才可 detach，避免 clone
    # conflict 誤判與 upstream prescan 重新記錄。
    cleanup_names = set(successful_names if mode == "add" else ())
    cleanup_names.update(manifest_names_for_detach(verified_first_party))
    if not dry_run and cleanup_names:
        from script.services.npx_skills.manifest_sync import (
            cleanup_skills_from_manifests,
        )

        removed = cleanup_skills_from_manifests(sorted(cleanup_names))
        if removed:
            total_removed = sum(len(v) for v in removed.values())
            console.print(
                f"[dim]已從 {len(removed)} 個 target manifest 移除 "
                f"{total_removed} 個條目（改由 npx 管理）[/dim]"
            )

    if failed_packages:
        console.print("[red]npx-skills phase 有失敗 package：[/red]")
        for repo, returncode in failed_packages:
            console.print(f"  [red]- {repo}: exit {returncode}[/red]")
        raise typer.Exit(code=1)

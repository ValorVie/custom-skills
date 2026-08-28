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
from script.services.npx_skills.migration import (
    FIRST_PARTY_SOURCE,
    MigrationRecord,
    VerificationResult,
    backup_and_remove_legacy_paths,
    classify_legacy_skill,
    legacy_name_for,
    manifest_names_for_detach,
    read_npx_lock,
    verify_npx_installations,
)
from script.utils.system import check_command_exists, run_command

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
    cmd += ["-a", defaults.agents]
    if defaults.yes:
        cmd.append("--yes")
    return cmd


def build_update_command(
    entries: Sequence[SkillEntry], defaults: NpxDefaults
) -> list[str]:
    _single_repo(entries)
    # update 支援一次傳入多個 skill；agents 綁定由安裝時決定。
    cmd = ["npx", "skills", "update", *(entry.skill for entry in entries)]
    if defaults.scope == "global":
        cmd.append("-g")
    if defaults.yes:
        cmd.append("-y")
    return cmd


def _preview_first_party_group(
    entries: Sequence[SkillEntry],
) -> tuple[MigrationRecord, ...]:
    from script.utils.manifest import read_manifest
    from script.utils.shared import get_target_path

    lock = read_npx_lock()
    records: list[MigrationRecord] = []
    for target in ("claude", "antigravity", "opencode", "codex", "agy"):
        target_root = get_target_path(target, "skills")
        if target_root is None:
            continue
        manifest = read_manifest(target)
        for entry in entries:
            records.append(
                classify_legacy_skill(
                    target=target,
                    canonical_id=entry.skill,
                    legacy_name=legacy_name_for(entry.skill),
                    target_root=target_root,
                    manifest=manifest,
                    npx_lock=lock,
                    expected_repo=entry.repo,
                )
            )
    return tuple(records)


def _verify_first_party_group(
    entries: Sequence[SkillEntry],
) -> VerificationResult:
    claude_skills = Path.home() / ".claude" / "skills"
    return verify_npx_installations(entries, agent_roots=(claude_skills,))


def _display_unsafe_records(records: Sequence[MigrationRecord]) -> None:
    for record in records:
        if record.safe_to_install:
            continue
        console.print(
            f"  [red]- {record.target}/{record.legacy_name}: {record.state.value}[/red]"
        )
        for relative in record.changed_files:
            console.print(f"      [red]{relative}[/red]")


def run_npx_skills_phase(
    *,
    mode: Mode,
    project_yaml: Path,
    user_yaml: Path,
    dry_run: bool = False,
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
    for idx, group in enumerate(groups, start=1):
        prefix = f"[{idx}/{total_packages}]"
        repo = group[0].repo
        skill_names = [entry.skill for entry in group]
        console.print(f"{prefix} {repo} ({len(skill_names)} 個 skills)")
        if dry_run:
            if mode == "add":
                cmd = build_add_command(group, config.defaults)
            else:
                cmd = build_update_command(group, config.defaults)
            console.print(f"  [dim][dry-run] {' '.join(cmd)}[/dim]")
            continue

        is_first_party = all(entry.source == FIRST_PARTY_SOURCE for entry in group)
        active_group = group
        migration_records: tuple[MigrationRecord, ...] = ()
        if mode == "add" and is_first_party:
            migration_records = _preview_first_party_group(group)
            unsafe = tuple(
                record for record in migration_records if not record.safe_to_install
            )
            if unsafe:
                console.print(
                    "  [yellow]⚠ 第一方 skill migration preflight 有阻擋項目；"
                    "只安裝其餘安全 skills。[/yellow]"
                )
                _display_unsafe_records(unsafe)
                failed_packages.append((repo, 1))
                unsafe_ids = {record.canonical_id for record in unsafe}
                active_group = tuple(
                    entry for entry in group if entry.skill not in unsafe_ids
                )
                if not active_group:
                    continue

        if mode == "add":
            cmd = build_add_command(active_group, config.defaults)
        else:
            cmd = build_update_command(active_group, config.defaults)

        result = run_command(cmd, check=False)
        if result.returncode == 0:
            if mode == "add" and is_first_party:
                verification = _verify_first_party_group(active_group)
                if verification.failures:
                    console.print("  [red]✗ npx 安裝讀回驗證失敗：[/red]")
                    for failure in verification.failures:
                        console.print(f"      [red]{failure}[/red]")
                    failed_packages.append((repo, 1))
                    continue
                legacy_failures = backup_and_remove_legacy_paths(
                    migration_records,
                    verified_names=verification.verified_names,
                )
                if legacy_failures:
                    console.print("  [red]✗ legacy path cleanup 失敗：[/red]")
                    for failure in legacy_failures:
                        console.print(f"      [red]{failure}[/red]")
                    failed_packages.append((repo, 1))
                    continue
                verified_first_party.extend(verification.verified_names)
            successful_names.extend(entry.skill for entry in active_group)
            console.print("  [green]✓[/green] 完成")
        else:
            failed_packages.append((repo, result.returncode))
            hint = ""
            if mode == "update":
                hint = "（skill 可能尚未安裝，請先執行 ai-dev install-npx-skills）"
            console.print(
                f"  [red]✗[/red] 退出碼 {result.returncode}{hint}"
            )

    # add 模式執行完畢後，把 npx 接管的 skill 從 ai-dev manifest 移除，
    # 避免 clone 的 conflict 誤判與 upstream prescan 重新記錄。
    if mode == "add" and not dry_run and successful_names:
        from script.services.npx_skills.manifest_sync import cleanup_skills_from_manifests

        cleanup_names = set(successful_names)
        cleanup_names.update(manifest_names_for_detach(verified_first_party))
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

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
from script.utils.system import check_command_exists, run_command

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
    # npx skills update 僅支援 -g / -p / -y（不支援 -a）；agents 綁定由安裝時決定。
    cmd = ["npx", "skills", "update", entry.skill]
    if defaults.scope == "global":
        cmd.append("-g")
    if defaults.yes:
        cmd.append("-y")
    return cmd


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
        elif mode == "update":
            console.print(
                f"  [yellow]⚠[/yellow] 退出碼 {result.returncode}"
                "（skill 可能尚未安裝，請先執行 ai-dev install-npx-skills）"
            )
        else:
            console.print(
                f"  [yellow]⚠[/yellow] 退出碼 {result.returncode}（可能已裝或來源不符）"
            )

    # add 模式執行完畢後，把 npx 接管的 skill 從 ai-dev manifest 移除，
    # 避免 clone 的 conflict 誤判與 upstream prescan 重新記錄。
    if mode == "add" and not dry_run:
        from script.services.npx_skills.manifest_sync import cleanup_skills_from_manifests

        npx_names = [entry.skill for entry in config.entries]
        removed = cleanup_skills_from_manifests(npx_names)
        if removed:
            total_removed = sum(len(v) for v in removed.values())
            console.print(
                f"[dim]已從 {len(removed)} 個 target manifest 移除 "
                f"{total_removed} 個條目（改由 npx 管理）[/dim]"
            )

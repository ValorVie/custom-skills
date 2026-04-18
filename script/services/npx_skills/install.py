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

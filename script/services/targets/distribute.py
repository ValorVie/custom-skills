from __future__ import annotations

import typer
from rich.console import Console

from script.models.execution_plan import ExecutionPlan
from script.utils.paths import get_custom_skills_dir
from script.utils.shared import copy_custom_skills_to_targets, shorten_path

console = Console()

def run_targets_phase(
    *,
    plan: ExecutionPlan,
    force: bool = False,
    skip_conflicts: bool = False,
    backup: bool = False,
) -> None:
    """Run target distribution work for a pipeline plan."""
    if plan.dry_run:
        target_text = ", ".join(plan.targets) if plan.targets else "all"
        console.print(
            f"[dim][dry-run] {plan.command_name}: targets → {target_text}[/dim]"
        )
        return

    custom_skills_dir = get_custom_skills_dir()
    if not custom_skills_dir.exists():
        console.print(
            f"[bold red]錯誤：來源目錄不存在 ({shorten_path(custom_skills_dir)})[/bold red]"
        )
        console.print("[dim]請先執行 ai-dev install 或 ai-dev update[/dim]")
        raise typer.Exit(code=1)

    console.print("[bold blue]分發 Skills 到各工具目錄...[/bold blue]")
    copy_custom_skills_to_targets(
        sync_project=False,
        force=force,
        skip_conflicts=skip_conflicts,
        backup=backup,
        selected_targets=plan.targets or None,
        refresh_state=False,
    )

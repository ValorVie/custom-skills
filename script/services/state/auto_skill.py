from __future__ import annotations

from rich.console import Console

from script.models.execution_plan import ExecutionPlan
from script.utils.auto_skill_state import refresh_auto_skill_state
from script.utils.paths import get_codex_superpowers_dir
from script.utils.shared import refresh_codex_superpowers_symlinks

console = Console()


def run_state_phase(*, plan: ExecutionPlan) -> None:
    """Run state refresh work for a pipeline plan."""
    if plan.dry_run:
        console.print(
            f"[dim][dry-run] {plan.command_name}: state[/dim]"
        )
        return

    if plan.command_name in {"install", "update"}:
        repo_path = get_codex_superpowers_dir()
        if (repo_path / ".git").exists():
            refresh_codex_superpowers_symlinks(repo_path)

    state_dir = refresh_auto_skill_state()
    if state_dir is not None:
        console.print(
            f"[green]✓[/green] auto-skill canonical state 已同步 → [dim]{state_dir}[/dim]"
        )

from __future__ import annotations

from rich.console import Console

from script.models.execution_plan import ExecutionPlan
from script.utils.auto_skill_state import refresh_auto_skill_state
console = Console()


def run_state_phase(*, plan: ExecutionPlan) -> None:
    """Run state refresh work for a pipeline plan."""
    if plan.dry_run:
        console.print(
            f"[dim][dry-run] {plan.command_name}: state[/dim]"
        )
        return

    state_dir = refresh_auto_skill_state()
    if state_dir is not None:
        console.print(
            f"[green]✓[/green] auto-skill canonical state 已同步 → [dim]{state_dir}[/dim]"
        )

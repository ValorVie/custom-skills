from __future__ import annotations

from rich.console import Console

from script.models.execution_plan import ExecutionPlan
from script.services.state.auto_skill import run_state_phase
from script.services.targets.distribute import run_targets_phase

console = Console()

def execute_clone_plan(
    plan: ExecutionPlan,
    *,
    force: bool = False,
    skip_conflicts: bool = False,
    backup: bool = False,
) -> None:
    if plan.dry_run:
        target_text = ", ".join(plan.targets) if plan.targets else "all"
        console.print(
            f"[bold blue][dry-run][/bold blue] clone phases={', '.join(plan.phases)} targets={target_text}"
        )
        return

    for phase in plan.phases:
        if phase == "state":
            run_state_phase(plan=plan)
        elif phase == "targets":
            run_targets_phase(
                plan=plan,
                force=force,
                skip_conflicts=skip_conflicts,
                backup=backup,
            )
        else:
            raise ValueError(f"Unsupported clone phase: {phase}")

    console.print("[bold green]分發完成！[/bold green]")

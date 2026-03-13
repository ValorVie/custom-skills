from __future__ import annotations

from rich.console import Console

from script.models.execution_plan import ExecutionPlan
from script.services.repos.refresh import run_repos_phase
from script.services.state.auto_skill import run_state_phase
from script.services.tools.update import run_tools_phase

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
        else:
            raise ValueError(f"Unsupported update phase: {phase}")

    console.print("[bold green]更新完成！[/bold green]")
    console.print()
    console.print("[dim]提示：如需分發 Skills 到各工具目錄，請執行：ai-dev clone[/dim]")

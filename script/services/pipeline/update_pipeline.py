from __future__ import annotations

from rich.console import Console

from script.models.execution_plan import ExecutionPlan
from script.services.npx_skills import run_npx_skills_phase
from script.services.repos.refresh import run_repos_phase
from script.services.state.auto_skill import run_state_phase
from script.services.tools.update import run_tools_phase
from script.utils.paths import get_ai_dev_config_dir, get_custom_skills_dir

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
        elif phase == "npx-skills":
            run_npx_skills_phase(
                mode="update",
                project_yaml=get_custom_skills_dir() / "upstream" / "npx-skills.yaml",
                user_yaml=get_ai_dev_config_dir() / "npx-skills.yaml",
                dry_run=False,
            )
        else:
            raise ValueError(f"Unsupported update phase: {phase}")

    console.print("[bold green]更新完成！[/bold green]")
    console.print()
    console.print("[dim]提示：如需分發 Skills 到各工具目錄，請執行：ai-dev clone[/dim]")

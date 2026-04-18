from __future__ import annotations

from rich.console import Console

from script.models.execution_plan import ExecutionPlan
from script.services.npx_skills import run_npx_skills_phase
from script.services.repos.refresh import run_repos_phase
from script.services.state.auto_skill import run_state_phase
from script.services.targets.distribute import run_targets_phase
from script.services.tools.update import run_install_postflight, run_tools_phase
from script.utils.paths import get_npx_skills_project_yaml, get_npx_skills_user_yaml

console = Console()


def execute_install_plan(plan: ExecutionPlan) -> None:
    if plan.dry_run:
        target_text = ", ".join(plan.targets) if plan.targets else "all"
        console.print(
            f"[bold blue][dry-run][/bold blue] install phases={', '.join(plan.phases)} targets={target_text}"
        )
        return

    console.print("[bold blue]開始安裝...[/bold blue]")
    for phase in plan.phases:
        if phase == "tools":
            run_tools_phase(plan=plan)
        elif phase == "repos":
            run_repos_phase(plan=plan)
        elif phase == "state":
            run_state_phase(plan=plan)
        elif phase == "npx-skills":
            run_npx_skills_phase(
                mode="add",
                project_yaml=get_npx_skills_project_yaml(),
                user_yaml=get_npx_skills_user_yaml(),
                dry_run=plan.dry_run,
            )
        elif phase == "targets":
            run_targets_phase(plan=plan)
        else:
            raise ValueError(f"Unsupported install phase: {phase}")

    run_install_postflight()
    console.print()
    console.print("[bold green]安裝完成！[/bold green]")

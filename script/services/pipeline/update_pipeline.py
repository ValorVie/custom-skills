from __future__ import annotations

from script.models.execution_plan import ExecutionPlan
from script.services.repos.refresh import run_repos_phase
from script.services.state.auto_skill import run_state_phase
from script.services.tools.update import run_tools_phase


def execute_update_plan(plan: ExecutionPlan) -> None:
    for phase in plan.phases:
        if phase == "tools":
            run_tools_phase(plan=plan)
        elif phase == "repos":
            run_repos_phase(plan=plan)
        elif phase == "state":
            run_state_phase(plan=plan)
        else:
            raise ValueError(f"Unsupported update phase: {phase}")

from __future__ import annotations

from script.models.execution_plan import ExecutionPlan
from script.services.state.auto_skill import run_state_phase
from script.services.targets.distribute import run_targets_phase


def execute_clone_plan(plan: ExecutionPlan) -> None:
    for phase in plan.phases:
        if phase == "state":
            run_state_phase(plan=plan)
        elif phase == "targets":
            run_targets_phase(plan=plan)
        else:
            raise ValueError(f"Unsupported clone phase: {phase}")

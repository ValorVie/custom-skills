from __future__ import annotations

from script.models.execution_plan import ExecutionPlan


def run_state_phase(*, plan: ExecutionPlan) -> None:
    """Run state refresh work for a pipeline plan."""


from __future__ import annotations

from script.models.execution_plan import ExecutionPlan


def run_targets_phase(*, plan: ExecutionPlan) -> None:
    """Run target distribution work for a pipeline plan."""


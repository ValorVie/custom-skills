from __future__ import annotations

from script.models.execution_plan import ExecutionPlan


def run_repos_phase(*, plan: ExecutionPlan) -> None:
    """Run repo refresh work for a pipeline plan."""


from script.models.execution_plan import ExecutionPlan
from script.services.pipeline.update_pipeline import execute_update_plan


def test_update_pipeline_runs_requested_phases_in_order(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        "script.services.pipeline.update_pipeline.run_tools_phase",
        lambda **_: calls.append("tools"),
    )
    monkeypatch.setattr(
        "script.services.pipeline.update_pipeline.run_repos_phase",
        lambda **_: calls.append("repos"),
    )
    monkeypatch.setattr(
        "script.services.pipeline.update_pipeline.run_state_phase",
        lambda **_: calls.append("state"),
    )

    execute_update_plan(
        ExecutionPlan(
            command_name="update",
            phases=("tools", "repos", "state"),
            targets=(),
            dry_run=False,
        )
    )

    assert calls == ["tools", "repos", "state"]

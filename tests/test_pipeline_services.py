import pytest
import typer

from script.models.execution_plan import ExecutionPlan
from script.services.pipeline.clone_pipeline import execute_clone_plan
from script.services.pipeline.install_pipeline import execute_install_plan
from script.services.pipeline.update_pipeline import execute_update_plan


def test_update_pipeline_runs_migration_then_requested_phases_in_order(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        "script.services.pipeline.update_pipeline.migrate_legacy_codex_skills",
        lambda **_: calls.append("migration"),
    )
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

    assert calls == ["migration", "tools", "repos", "state"]


def test_install_pipeline_previews_migration_during_dry_run(monkeypatch) -> None:
    dry_run_values: list[bool] = []
    monkeypatch.setattr(
        "script.services.pipeline.install_pipeline.migrate_legacy_codex_skills",
        lambda *, dry_run: dry_run_values.append(dry_run),
    )

    execute_install_plan(
        ExecutionPlan(
            command_name="install",
            phases=("repos", "targets"),
            targets=(),
            dry_run=True,
        )
    )

    assert dry_run_values == [True]


def test_clone_pipeline_runs_migration_before_other_work(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        "script.services.pipeline.clone_pipeline.migrate_legacy_codex_skills",
        lambda **_: calls.append("migration"),
    )
    monkeypatch.setattr(
        "script.services.pipeline.clone_pipeline._build_source_summary",
        lambda _plan: [],
    )

    execute_clone_plan(
        ExecutionPlan(
            command_name="clone",
            phases=(),
            targets=(),
            dry_run=False,
        )
    )

    assert calls == ["migration"]


def test_update_pipeline_stops_before_phases_on_migration_conflict(monkeypatch) -> None:
    monkeypatch.setattr(
        "script.services.pipeline.update_pipeline.migrate_legacy_codex_skills",
        lambda **_: (_ for _ in ()).throw(typer.Exit(code=1)),
    )
    monkeypatch.setattr(
        "script.services.pipeline.update_pipeline.run_tools_phase",
        lambda **_: (_ for _ in ()).throw(AssertionError("phase must not run")),
    )

    with pytest.raises(typer.Exit) as exc_info:
        execute_update_plan(
            ExecutionPlan(
                command_name="update",
                phases=("tools",),
                targets=(),
                dry_run=False,
            )
        )

    assert exc_info.value.exit_code == 1

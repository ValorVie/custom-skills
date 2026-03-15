from typer.testing import CliRunner

from script.main import app
from script.commands import update as update_command
from script.models.execution_plan import ExecutionPlan

runner = CliRunner()


def test_update_help_exposes_pipeline_flags():
    result = runner.invoke(app, ["update", "--help"])

    assert result.exit_code == 0, result.stdout
    assert "--only" in result.stdout
    assert "--skip" in result.stdout
    assert "--target" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--skip-npm" not in result.stdout
    assert "--skip-bun" not in result.stdout
    assert "--skip-repos" not in result.stdout


def test_update_builds_execution_plan_and_calls_pipeline(monkeypatch):
    captured: dict[str, object] = {}
    plan = ExecutionPlan(
        command_name="update",
        phases=("tools", "repos", "state"),
        targets=(),
        dry_run=True,
    )

    monkeypatch.setattr(
        update_command,
        "build_execution_plan",
        lambda spec, **kwargs: captured.update({"spec": spec, "kwargs": kwargs}) or plan,
    )
    monkeypatch.setattr(
        update_command,
        "execute_update_plan",
        lambda incoming_plan: captured.update({"plan": incoming_plan}),
    )

    result = runner.invoke(app, ["update", "--dry-run"])

    assert result.exit_code == 0, result.stdout
    assert captured["kwargs"] == {
        "only": None,
        "skip": None,
        "target": None,
        "dry_run": True,
    }
    assert captured["plan"] == plan


def test_update_reports_invalid_phase_without_traceback():
    result = runner.invoke(app, ["update", "--only", "targets"])

    assert result.exit_code != 0
    assert "Unknown phases: targets" in result.output
    assert "Traceback" not in result.output

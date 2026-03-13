from pathlib import Path

from typer.testing import CliRunner

from script.main import app
from script.commands import clone as clone_command
from script.models.execution_plan import ExecutionPlan

runner = CliRunner()


def test_clone_help_exposes_pipeline_flags():
    result = runner.invoke(app, ["clone", "--help"])

    assert result.exit_code == 0, result.stdout
    assert "--only" in result.stdout
    assert "--skip" in result.stdout
    assert "--target" in result.stdout
    assert "--dry-run" in result.stdout


def test_clone_builds_execution_plan_and_calls_pipeline(monkeypatch):
    captured: dict[str, object] = {}
    plan = ExecutionPlan(
        command_name="clone",
        phases=("targets",),
        targets=("claude", "codex"),
        dry_run=False,
    )

    monkeypatch.setattr(
        clone_command,
        "build_execution_plan",
        lambda spec, **kwargs: captured.update({"spec": spec, "kwargs": kwargs}) or plan,
    )
    monkeypatch.setattr(
        clone_command,
        "execute_clone_plan",
        lambda incoming_plan, **kwargs: captured.update({"plan": incoming_plan, "extra": kwargs}),
    )

    result = runner.invoke(app, ["clone", "--only", "targets", "--target", "claude,codex"])

    assert result.exit_code == 0, result.stdout
    assert captured["kwargs"] == {
        "only": "targets",
        "skip": None,
        "target": "claude,codex",
        "dry_run": False,
    }
    assert captured["plan"] == plan
    assert captured["extra"] == {
        "force": False,
        "skip_conflicts": False,
        "backup": False,
    }

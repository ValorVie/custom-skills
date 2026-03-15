from typer.testing import CliRunner

from script.main import app
from script.commands import install as install_command
from script.models.execution_plan import ExecutionPlan

runner = CliRunner()


def test_install_help_exposes_pipeline_flags():
    result = runner.invoke(app, ["install", "--help"])

    assert result.exit_code == 0, result.stdout
    assert "--only" in result.stdout
    assert "--skip" in result.stdout
    assert "--target" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--skip-npm" not in result.stdout
    assert "--skip-bun" not in result.stdout
    assert "--skip-repos" not in result.stdout


def test_install_builds_execution_plan_and_calls_pipeline(monkeypatch):
    captured: dict[str, object] = {}
    plan = ExecutionPlan(
        command_name="install",
        phases=("repos", "state"),
        targets=(),
        dry_run=True,
    )

    monkeypatch.setattr(
        install_command,
        "build_execution_plan",
        lambda spec, **kwargs: captured.update({"spec": spec, "kwargs": kwargs}) or plan,
    )
    monkeypatch.setattr(
        install_command,
        "execute_install_plan",
        lambda incoming_plan: captured.update({"plan": incoming_plan}),
    )

    result = runner.invoke(app, ["install", "--only", "repos,state", "--dry-run"])

    assert result.exit_code == 0, result.stdout
    assert captured["kwargs"] == {
        "only": "repos,state",
        "skip": None,
        "target": None,
        "dry_run": True,
    }
    assert captured["plan"] == plan

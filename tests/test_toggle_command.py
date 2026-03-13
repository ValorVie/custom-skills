from typer.testing import CliRunner

from script.main import app
from script.commands import toggle as toggle_cmd


runner = CliRunner()


def test_toggle_requires_target():
    result = runner.invoke(app, ["toggle", "--type", "skills", "--name", "demo", "--disable"])

    assert result.exit_code == 1
    assert "請指定目標工具" in result.stdout


def test_toggle_dry_run_does_not_mutate_state(monkeypatch):
    monkeypatch.setattr(toggle_cmd, "load_toggle_config", lambda: {})
    monkeypatch.setattr(
        toggle_cmd,
        "disable_resource",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not disable")),
    )
    monkeypatch.setattr(
        toggle_cmd,
        "enable_resource",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not enable")),
    )

    result = runner.invoke(
        app,
        [
            "toggle",
            "--target",
            "claude",
            "--type",
            "skills",
            "--name",
            "demo",
            "--disable",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "dry-run" in result.stdout.lower()

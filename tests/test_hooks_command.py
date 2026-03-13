from typer.testing import CliRunner

from script.main import app
from script.commands import hooks as hooks_cmd


runner = CliRunner()


def test_hooks_install_requires_target():
    result = runner.invoke(app, ["hooks", "install"])

    assert result.exit_code != 0
    assert "--target" in result.output


def test_hooks_install_rejects_unknown_target():
    result = runner.invoke(app, ["hooks", "install", "--target", "codex"])

    assert result.exit_code != 0
    assert "claude" in result.stdout


def test_hooks_status_prints_status(monkeypatch):
    called = []

    monkeypatch.setattr(
        hooks_cmd,
        "show_ecc_hooks_status",
        lambda: called.append("shown"),
    )

    result = runner.invoke(app, ["hooks", "status", "--target", "claude"])

    assert result.exit_code == 0
    assert called == ["shown"]


def test_hooks_uninstall_cancel_no_change(monkeypatch):
    monkeypatch.setattr(
        hooks_cmd,
        "get_ecc_hooks_status",
        lambda: {"installed": True},
    )
    monkeypatch.setattr(hooks_cmd.typer, "confirm", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(
        hooks_cmd,
        "uninstall_ecc_hooks_plugin",
        lambda: (_ for _ in ()).throw(AssertionError("should not uninstall")),
    )

    result = runner.invoke(app, ["hooks", "uninstall", "--target", "claude"])

    assert result.exit_code == 0
    assert "Cancelled" in result.stdout

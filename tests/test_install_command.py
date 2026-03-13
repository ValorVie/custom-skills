from typer.testing import CliRunner

from script.main import app
from script.commands import install as install_command

runner = CliRunner()


def test_install_help_no_longer_exposes_sync_project_flag():
    result = runner.invoke(app, ["install", "--help"])

    assert result.exit_code == 0, result.stdout
    assert "--sync-project" not in result.stdout


def test_install_does_not_sync_project_side_effects(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(install_command, "check_command_exists", lambda _: True)
    monkeypatch.setattr(install_command, "check_bun_installed", lambda: False)
    monkeypatch.setattr(install_command, "show_claude_status", lambda: None)
    monkeypatch.setattr(install_command, "get_all_skill_names", lambda: [])
    monkeypatch.setattr(install_command, "show_skills_npm_hint", lambda: None)
    monkeypatch.setattr(install_command, "_is_completion_installed", lambda _: True)

    called: dict[str, object] = {}

    def fake_copy_skills(**kwargs):
        called.update(kwargs)

    monkeypatch.setattr(install_command, "copy_skills", fake_copy_skills)

    result = runner.invoke(
        app,
        ["install", "--skip-npm", "--skip-bun", "--skip-repos"],
    )

    assert result.exit_code == 0, result.stdout
    assert called == {"sync_project": False}


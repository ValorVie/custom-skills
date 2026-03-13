from pathlib import Path

from typer.testing import CliRunner

from script.main import app
from script.commands import clone as clone_command

runner = CliRunner()


def test_clone_help_no_longer_exposes_sync_project_flag():
    result = runner.invoke(app, ["clone", "--help"])

    assert result.exit_code == 0, result.stdout
    assert "--sync-project" not in result.stdout


def test_clone_only_distributes_to_targets(tmp_path: Path, monkeypatch):
    source_dir = tmp_path / "custom-skills"
    source_dir.mkdir()

    called: dict[str, object] = {}

    monkeypatch.setattr(clone_command, "get_custom_skills_dir", lambda: source_dir)

    def fake_copy_skills(**kwargs):
        called.update(kwargs)

    monkeypatch.setattr(clone_command, "copy_skills", fake_copy_skills)

    result = runner.invoke(app, ["clone"])

    assert result.exit_code == 0, result.stdout
    assert called == {
        "sync_project": False,
        "force": False,
        "skip_conflicts": False,
        "backup": False,
    }


from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from script.main import app
from script.commands import maintain as maintain_command

runner = CliRunner()


def test_maintain_template_invokes_template_sync(
    tmp_path: Path, monkeypatch
):
    repo_root = tmp_path / "repo"
    template_dir = repo_root / "project-template"
    repo_root.mkdir()
    template_dir.mkdir()

    called: dict[str, object] = {}

    monkeypatch.setattr(maintain_command, "_resolve_repo_root", lambda: repo_root)
    monkeypatch.setattr(
        maintain_command,
        "load_project_template_manifest",
        lambda path: {"version": 1, "include": ["AGENTS.md"], "exclude": []},
    )

    def fake_sync(*, repo_root, template_dir, manifest, check):
        called["repo_root"] = repo_root
        called["template_dir"] = template_dir
        called["manifest"] = manifest
        called["check"] = check
        return SimpleNamespace(copied=1, updated=0, skipped=0, missing=[])

    monkeypatch.setattr(maintain_command, "sync_project_template", fake_sync)

    result = runner.invoke(app, ["maintain", "template"])

    assert result.exit_code == 0, result.stdout
    assert called["repo_root"] == repo_root
    assert called["template_dir"] == template_dir
    assert called["manifest"] == {"version": 1, "include": ["AGENTS.md"], "exclude": []}
    assert called["check"] is False
    assert "project-template" in result.stdout


def test_maintain_clone_invokes_integrate_to_dev_project(
    tmp_path: Path, monkeypatch
):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    called: dict[str, object] = {}

    monkeypatch.setattr(maintain_command, "_resolve_repo_root", lambda: repo_root)

    def fake_integrate(path):
        called["path"] = path

    monkeypatch.setattr(maintain_command, "integrate_to_dev_project", fake_integrate)

    result = runner.invoke(app, ["maintain", "clone"])

    assert result.exit_code == 0, result.stdout
    assert called["path"] == repo_root
    assert "開發目錄" in result.stdout

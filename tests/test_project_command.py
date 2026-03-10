"""project 命令的整合測試。"""

from pathlib import Path
import subprocess

import pytest
from typer.testing import CliRunner

from script.commands import project as project_command
from script.main import app
from script.utils import project_projection_manifest as ppm
from script.utils.project_blocks import read_managed_block
from script.utils.project_tracking import save_tracking_file

runner = CliRunner()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_template(base: Path) -> Path:
    template_dir = base / "template"
    _write(template_dir / "AGENTS.md", "# Project instructions\n")
    _write(template_dir / ".claude" / "commands" / "review.md", "review command\n")
    _write(template_dir / ".github" / "skills" / "demo" / "SKILL.md", "demo skill\n")
    _write(template_dir / ".github" / "prompts" / "review.md", "review prompt\n")
    _write(template_dir / ".github" / "copilot-instructions.md", "copilot\n")
    _write(template_dir / ".github" / "workflows" / "ci.yml", "name: CI\n")
    _write(template_dir / ".standards" / "testing.ai.yaml", "testing: true\n")
    return template_dir


def test_project_init_creates_intent_and_hydrates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = tmp_path / "project"
    (project_root / ".git" / "info").mkdir(parents=True)
    manifest_dir = tmp_path / "manifests" / "projects"

    monkeypatch.setattr(project_command, "get_project_template_dir", lambda: template_dir)
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    result = runner.invoke(app, ["project", "init", str(project_root)])

    assert result.exit_code == 0, result.stdout
    assert (project_root / ".ai-dev-project.yaml").exists()
    assert (project_root / ".standards" / "testing.ai.yaml").exists()
    assert read_managed_block(project_root / "AGENTS.md", "ai-dev-project") == "# Project instructions"
    assert (project_root / ".claude" / "commands" / "review.md").exists()
    assert (project_root / ".github" / "workflows" / "ci.yml").exists()
    assert (project_root / ".github" / "skills" / "demo" / "SKILL.md").exists()
    assert "衝突：" not in result.stdout


def test_project_hydrate_command_uses_existing_intent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = tmp_path / "project"
    (project_root / ".git" / "info").mkdir(parents=True)
    manifest_dir = tmp_path / "manifests" / "projects"
    save_tracking_file(
        {
            "managed_by": "ai-dev",
            "schema_version": "2",
            "project_id": "demo-project",
            "template": {
                "name": "project-template",
                "url": "local://project-template",
                "branch": "main",
            },
            "projection": {
                "targets": ["claude", "codex", "gemini"],
                "profile": "default",
                "allow_local_generation": True,
            },
            "managed_files": [],
        },
        project_root,
    )

    monkeypatch.setattr(project_command, "get_project_template_dir", lambda: template_dir)
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    result = runner.invoke(app, ["project", "hydrate", str(project_root)])

    assert result.exit_code == 0, result.stdout
    assert read_managed_block(project_root / "AGENTS.md", "ai-dev-project") == "# Project instructions"
    assert (project_root / ".claude" / "commands" / "review.md").exists()


def test_project_doctor_reports_ok_for_hydrated_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = tmp_path / "project"
    (project_root / ".git" / "info").mkdir(parents=True)
    manifest_dir = tmp_path / "manifests" / "projects"
    save_tracking_file(
        {
            "managed_by": "ai-dev",
            "schema_version": "2",
            "project_id": "demo-project",
            "template": {
                "name": "project-template",
                "url": "local://project-template",
                "branch": "main",
            },
            "projection": {
                "targets": ["claude", "codex", "gemini"],
                "profile": "default",
                "allow_local_generation": True,
            },
            "managed_files": [],
        },
        project_root,
    )

    monkeypatch.setattr(project_command, "get_project_template_dir", lambda: template_dir)
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    hydrate_result = runner.invoke(app, ["project", "hydrate", str(project_root)])
    assert hydrate_result.exit_code == 0, hydrate_result.stdout

    result = runner.invoke(app, ["project", "doctor", str(project_root)])

    assert result.exit_code == 0, result.stdout
    assert "OK" in result.stdout


def test_project_init_hides_generated_ai_files_from_git_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = tmp_path / "project"
    project_root.mkdir()
    manifest_dir = tmp_path / "manifests" / "projects"
    subprocess.run(["git", "init"], cwd=project_root, check=True, capture_output=True)

    monkeypatch.setattr(project_command, "get_project_template_dir", lambda: template_dir)
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    result = runner.invoke(app, ["project", "init", str(project_root)])
    assert result.exit_code == 0, result.stdout

    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    assert "AGENTS.md" not in status
    assert ".claude/" not in status
    assert ".ai-dev-project.yaml" not in status
    assert ".standards/" in status

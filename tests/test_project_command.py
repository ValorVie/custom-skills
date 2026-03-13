"""project 命令的整合測試。"""

from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from script.commands import project as project_command
from script.main import app
from script.utils import project_projection_manifest as ppm
from script.utils.project_blocks import read_managed_block
from script.utils.project_projection import PROJECT_TEMPLATE_NAME, PROJECT_TEMPLATE_URL
from script.utils.project_tracking import load_tracking_file, save_tracking_file

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


def _seed_project_intent(project_root: Path, project_id: str = "demo-project") -> None:
    save_tracking_file(
        {
            "project_id": project_id,
            "template": {
                "name": PROJECT_TEMPLATE_NAME,
                "url": PROJECT_TEMPLATE_URL,
                "branch": "main",
            },
            "managed_files": [],
        },
        project_root,
    )


def test_project_init_creates_intent_and_hydrates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = tmp_path / "project"
    (project_root / ".git" / "info").mkdir(parents=True)
    manifest_dir = tmp_path / "manifests" / "projects"

    monkeypatch.setattr(project_command, "get_project_template_dir", lambda: template_dir)
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)
    monkeypatch.setattr(project_command, "prompt_exclude_choice", lambda patterns: "yes")

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
    _seed_project_intent(project_root)

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
    _seed_project_intent(project_root)

    monkeypatch.setattr(project_command, "get_project_template_dir", lambda: template_dir)
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    hydrate_result = runner.invoke(app, ["project", "hydrate", str(project_root)])
    assert hydrate_result.exit_code == 0, hydrate_result.stdout

    result = runner.invoke(app, ["project", "doctor", str(project_root)])

    assert result.exit_code == 0, result.stdout
    assert "OK" in result.stdout


def test_project_doctor_allows_disabled_exclude(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = tmp_path / "project"
    (project_root / ".git" / "info").mkdir(parents=True)
    manifest_dir = tmp_path / "manifests" / "projects"
    _seed_project_intent(project_root)

    tracking = load_tracking_file(project_root)
    assert tracking is not None
    tracking["git_exclude"] = {
        "enabled": False,
        "version": "1",
        "patterns": [".claude/", "AGENTS.md"],
        "keep_tracked": [".editorconfig", ".gitattributes", ".gitignore"],
    }
    save_tracking_file(tracking, project_root)

    monkeypatch.setattr(project_command, "get_project_template_dir", lambda: template_dir)
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    hydrate_result = runner.invoke(app, ["project", "hydrate", str(project_root)])
    assert hydrate_result.exit_code == 0, hydrate_result.stdout
    assert not (project_root / ".git" / "info" / "exclude").exists()

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
    monkeypatch.setattr(project_command, "prompt_exclude_choice", lambda patterns: "yes")

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


def test_project_init_force_in_custom_skills_repo_does_not_switch_to_template_sync(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = tmp_path / "repo"
    project_root.mkdir()
    (project_root / "pyproject.toml").write_text('name = "ai-dev"\n', encoding="utf-8")
    manifest_dir = tmp_path / "manifests" / "projects"

    monkeypatch.setattr(project_command, "get_project_template_dir", lambda: template_dir)
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)
    monkeypatch.setattr(project_command, "prompt_exclude_choice", lambda patterns: "yes")

    result = runner.invoke(app, ["project", "init", "--force", str(project_root)])

    assert result.exit_code == 0, result.stdout
    assert "反向同步模式" not in result.stdout
    assert (project_root / ".ai-dev-project.yaml").exists()


def test_project_init_interactively_merges_file_and_preserves_existing_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    _write(template_dir / ".gitignore", "node_modules/\n.env\n")
    project_root = tmp_path / "project"
    (project_root / ".git" / "info").mkdir(parents=True)
    _write(project_root / ".gitignore", "node_modules/\n.venv/\n")
    _write(project_root / ".standards" / "custom.ai.yaml", "custom: true\n")
    manifest_dir = tmp_path / "manifests" / "projects"

    monkeypatch.setattr(project_command, "get_project_template_dir", lambda: template_dir)
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)
    monkeypatch.setattr(project_command, "prompt_exclude_choice", lambda patterns: "yes")

    with patch("script.utils.smart_merge.Prompt.ask", return_value="I"):
        result = runner.invoke(app, ["project", "init", str(project_root)])

    assert result.exit_code == 0, result.stdout
    assert (project_root / ".ai-dev-project.yaml").exists()
    assert project_root.joinpath(".gitignore").read_text(encoding="utf-8") == (
        "node_modules/\n.venv/\n.env\n"
    )
    assert (project_root / ".standards" / "custom.ai.yaml").exists()
    assert (project_root / ".standards" / "testing.ai.yaml").exists()
    assert "專案已初始化" not in result.stdout


def test_project_init_force_overwrites_existing_file_and_preserves_existing_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    _write(template_dir / ".editorconfig", "root = true\n")
    project_root = tmp_path / "project"
    (project_root / ".git" / "info").mkdir(parents=True)
    _write(project_root / ".editorconfig", "root = false\n")
    _write(project_root / ".standards" / "custom.ai.yaml", "custom: true\n")
    manifest_dir = tmp_path / "manifests" / "projects"

    monkeypatch.setattr(project_command, "get_project_template_dir", lambda: template_dir)
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)
    monkeypatch.setattr(project_command, "prompt_exclude_choice", lambda patterns: "yes")

    result = runner.invoke(app, ["project", "init", "--force", str(project_root)])

    assert result.exit_code == 0, result.stdout
    assert project_root.joinpath(".editorconfig").read_text(encoding="utf-8") == "root = true\n"
    assert (project_root / ".standards" / "custom.ai.yaml").exists()
    assert (project_root / ".standards" / "testing.ai.yaml").exists()


def test_project_init_recursively_merges_files_within_existing_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    _write(template_dir / ".standards" / "git-workflow.ai.yaml", "workflow: template\n")
    project_root = tmp_path / "project"
    (project_root / ".git" / "info").mkdir(parents=True)
    _write(project_root / ".standards" / "testing.ai.yaml", "testing: false\n")
    _write(project_root / ".standards" / "custom.ai.yaml", "custom: true\n")
    manifest_dir = tmp_path / "manifests" / "projects"

    monkeypatch.setattr(project_command, "get_project_template_dir", lambda: template_dir)
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)
    monkeypatch.setattr(project_command, "prompt_exclude_choice", lambda patterns: "yes")

    with patch("script.utils.smart_merge.Prompt.ask", return_value="O"):
        result = runner.invoke(app, ["project", "init", str(project_root)])

    assert result.exit_code == 0, result.stdout
    assert "跳過 .standards/" not in result.stdout
    assert ".standards/testing.ai.yaml" in result.stdout
    assert project_root.joinpath(".standards", "testing.ai.yaml").read_text(
        encoding="utf-8"
    ) == "testing: true\n"
    assert project_root.joinpath(".standards", "git-workflow.ai.yaml").read_text(
        encoding="utf-8"
    ) == "workflow: template\n"
    assert (project_root / ".standards" / "custom.ai.yaml").exists()


def test_project_init_respects_exclude_prompt_choice_no(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = tmp_path / "project"
    (project_root / ".git" / "info").mkdir(parents=True)
    manifest_dir = tmp_path / "manifests" / "projects"

    monkeypatch.setattr(project_command, "get_project_template_dir", lambda: template_dir)
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)
    monkeypatch.setattr(project_command, "prompt_exclude_choice", lambda patterns: "no")

    result = runner.invoke(app, ["project", "init", str(project_root)])

    assert result.exit_code == 0, result.stdout
    assert not (project_root / ".git" / "info" / "exclude").exists()
    tracking = load_tracking_file(project_root)
    assert tracking is not None
    assert tracking["git_exclude"]["enabled"] is False
    assert "後續可用 ai-dev project exclude --enable 啟用" in result.stdout


def test_project_init_without_git_repo_warns_and_records_disabled_exclude(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template_dir = _make_template(tmp_path)
    project_root = tmp_path / "project"
    project_root.mkdir()
    manifest_dir = tmp_path / "manifests" / "projects"
    prompt_called = {"value": False}

    monkeypatch.setattr(project_command, "get_project_template_dir", lambda: template_dir)
    monkeypatch.setattr(ppm, "get_project_manifest_dir", lambda: manifest_dir)

    def _unexpected_prompt(patterns):
        prompt_called["value"] = True
        return "yes"

    monkeypatch.setattr(project_command, "prompt_exclude_choice", _unexpected_prompt)

    result = runner.invoke(app, ["project", "init", str(project_root)])

    assert result.exit_code == 0, result.stdout
    assert prompt_called["value"] is False
    tracking = load_tracking_file(project_root)
    assert tracking is not None
    assert tracking["git_exclude"]["enabled"] is False
    assert "尚未偵測到 .git/" in result.stdout
    assert "建議先執行 `git init`" in result.stdout
    assert "ai-dev project exclude --enable" in result.stdout

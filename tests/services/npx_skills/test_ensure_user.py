from pathlib import Path

from script.services.npx_skills.config import ensure_user_yaml


def test_ensure_copies_project_to_user(tmp_path: Path):
    project = tmp_path / "project.yaml"
    project.write_text("version: 1\n")
    user = tmp_path / "user" / "npx-skills.yaml"

    result = ensure_user_yaml(project_path=project, user_path=user)

    assert result == user
    assert user.exists()
    assert user.read_text() == "version: 1\n"


def test_ensure_overwrites_user_when_project_newer(tmp_path: Path):
    project = tmp_path / "project.yaml"
    project.write_text("version: 2\n")
    user = tmp_path / "user" / "npx-skills.yaml"
    user.parent.mkdir(parents=True)
    user.write_text("version: 1\n")

    ensure_user_yaml(project_path=project, user_path=user)

    assert user.read_text() == "version: 2\n"

from pathlib import Path

import pytest

from script.utils import auto_skill_projection as projection
from script.utils.auto_skill_projection import project_auto_skill
from script.utils.system import get_os


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.mark.skipif(get_os() == "windows", reason="Windows 使用 junction，檢查方式不同")
def test_project_auto_skill_creates_symlink(tmp_path: Path):
    source = tmp_path / "state"
    target = tmp_path / "tool" / "skills" / "auto-skill"
    _write(source / "SKILL.md", "auto skill\n")

    result = project_auto_skill(source, target)

    assert result.mode == "symlink"
    assert result.changed is True
    assert target.is_symlink()
    assert target.resolve() == source.resolve()


def test_project_auto_skill_falls_back_to_copy(tmp_path: Path, monkeypatch):
    source = tmp_path / "state"
    target = tmp_path / "tool" / "skills" / "auto-skill"
    _write(source / "SKILL.md", "auto skill\n")

    monkeypatch.setattr(projection, "_create_directory_link", lambda *_args, **_kwargs: None)

    result = project_auto_skill(source, target)

    assert result.mode == "copy"
    assert result.changed is True
    assert (target / "SKILL.md").read_text(encoding="utf-8") == "auto skill\n"


@pytest.mark.skipif(get_os() == "windows", reason="Windows 使用 junction，檢查方式不同")
def test_project_auto_skill_is_idempotent_for_existing_symlink(tmp_path: Path):
    source = tmp_path / "state"
    target = tmp_path / "tool" / "skills" / "auto-skill"
    _write(source / "SKILL.md", "auto skill\n")

    first = project_auto_skill(source, target)
    second = project_auto_skill(source, target)

    assert first.mode == "symlink"
    assert second.mode == "symlink"
    assert second.changed is False

"""clone 整合測試：有/無 .ai-dev-project.yaml 時的分發行為差異。"""

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from script.utils.project_tracking import create_tracking_file
from script.utils.shared import _copy_dir_with_managed_skip


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ── _copy_dir_with_managed_skip ───────────────────────────────────────────────


def test_copy_dir_skips_managed_files(tmp_path: Path):
    """managed_files 中的檔案應被跳過。"""
    src = tmp_path / "src"
    dst = tmp_path / "project" / "skills"
    project_root = tmp_path / "project"
    project_root.mkdir()

    _write(src / "skill-a" / "SKILL.md", "skill a")
    _write(src / "skill-b" / "SKILL.md", "skill b")

    # skill-b/SKILL.md 已由模板管理
    managed = {"skills/skill-b/SKILL.md"}

    _copy_dir_with_managed_skip(
        src_dir=src,
        dst_dir=dst,
        project_root=project_root,
        managed_files=managed,
        template_name="qdm-ai-base",
    )

    assert (dst / "skill-a" / "SKILL.md").exists()
    assert not (dst / "skill-b" / "SKILL.md").exists()


def test_copy_dir_copies_unmanaged_files(tmp_path: Path):
    """非 managed 的檔案應正常複製。"""
    src = tmp_path / "src"
    dst = tmp_path / "project" / "skills"
    project_root = tmp_path / "project"
    project_root.mkdir()

    _write(src / "skill-a" / "SKILL.md", "skill a")
    managed: set[str] = set()

    _copy_dir_with_managed_skip(
        src_dir=src,
        dst_dir=dst,
        project_root=project_root,
        managed_files=managed,
        template_name="qdm-ai-base",
    )

    assert (dst / "skill-a" / "SKILL.md").exists()


# ── 有 .ai-dev-project.yaml 時 ────────────────────────────────────────────────


def test_sync_to_project_skips_when_tracking_exists(tmp_path: Path):
    """有 .ai-dev-project.yaml 時，clone 跳過 managed_files。"""
    project_root = tmp_path / "project"
    project_root.mkdir()

    # 建立追蹤檔，CLAUDE.md 由模板管理
    create_tracking_file(
        name="qdm-ai-base",
        url="https://github.com/test/test.git",
        branch="main",
        managed_files=["skills/managed-skill/SKILL.md"],
        project_dir=project_root,
    )

    # 建立來源目錄
    src_skills = tmp_path / "src" / "skills"
    _write(src_skills / "managed-skill" / "SKILL.md", "managed content")
    _write(src_skills / "free-skill" / "SKILL.md", "free content")

    dst_skills = project_root / "skills"

    _copy_dir_with_managed_skip(
        src_dir=src_skills,
        dst_dir=dst_skills,
        project_root=project_root,
        managed_files={"skills/managed-skill/SKILL.md"},
        template_name="qdm-ai-base",
    )

    # managed-skill 被跳過
    assert not (dst_skills / "managed-skill" / "SKILL.md").exists()
    # free-skill 正常複製
    assert (dst_skills / "free-skill" / "SKILL.md").exists()


def test_sync_to_project_no_tracking_copies_all(tmp_path: Path):
    """無 .ai-dev-project.yaml 時，clone 正常複製所有檔案。"""
    project_root = tmp_path / "project"
    project_root.mkdir()

    src_skills = tmp_path / "src" / "skills"
    _write(src_skills / "some-skill" / "SKILL.md", "content")
    dst_skills = project_root / "skills"

    # 無 managed_files
    _copy_dir_with_managed_skip(
        src_dir=src_skills,
        dst_dir=dst_skills,
        project_root=project_root,
        managed_files=set(),
        template_name="",
    )

    assert (dst_skills / "some-skill" / "SKILL.md").exists()

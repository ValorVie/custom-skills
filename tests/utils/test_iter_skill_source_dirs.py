"""Tests for ``_iter_skill_source_dirs``.

驗證 skills 來源目錄掃描能同時扁平化「skills/<name>/」與
「skills/<subdir>/<name>/」兩種結構，並忽略隱藏目錄。
"""

from pathlib import Path

from script.utils.shared import _iter_skill_source_dirs


def test_flat_and_uds_subdir(tmp_path: Path) -> None:
    (tmp_path / "flat-skill").mkdir()
    (tmp_path / "uds").mkdir()
    (tmp_path / "uds" / "uds-skill-a").mkdir()
    (tmp_path / "uds" / "uds-skill-b").mkdir()
    (tmp_path / ".hidden").mkdir()

    names = sorted(d.name for d in _iter_skill_source_dirs(tmp_path))

    assert names == ["flat-skill", "uds-skill-a", "uds-skill-b"]


def test_hidden_subdirs_skipped(tmp_path: Path) -> None:
    (tmp_path / "uds").mkdir()
    (tmp_path / "uds" / ".hidden-skill").mkdir()
    (tmp_path / "uds" / "real-skill").mkdir()

    names = [d.name for d in _iter_skill_source_dirs(tmp_path)]

    assert names == ["real-skill"]

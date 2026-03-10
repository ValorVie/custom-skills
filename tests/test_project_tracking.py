"""project_tracking.py 的單元測試。"""

from pathlib import Path
import re

import pytest

from script.utils.project_tracking import (
    create_tracking_file,
    get_managed_files,
    is_file_managed,
    load_tracking_file,
    save_tracking_file,
    update_tracking_file,
)


def _expected_project_id(path: Path) -> str:
    return re.sub(r"[^a-z0-9]+", "-", path.name.strip().lower()).strip("-")


def test_load_tracking_file_not_exist(tmp_path: Path):
    """不存在時回傳 None。"""
    result = load_tracking_file(tmp_path)
    assert result is None


def test_create_and_load_tracking_file(tmp_path: Path):
    """建立後可讀取，內容正確。"""
    create_tracking_file(
        name="qdm-ai-base",
        url="https://github.com/ValorVie/qdm-ai-base.git",
        branch="main",
        managed_files=["CLAUDE.md", ".standards/commit.yaml"],
        project_dir=tmp_path,
    )

    data = load_tracking_file(tmp_path)
    assert data is not None
    assert data["managed_by"] == "ai-dev"
    assert data["schema_version"] == "2"
    assert data["project_id"] == _expected_project_id(tmp_path)
    assert data["template"]["name"] == "qdm-ai-base"
    assert data["template"]["branch"] == "main"
    assert data["template"]["url"] == "https://github.com/ValorVie/qdm-ai-base.git"
    assert "initialized_at" not in data["template"]
    assert "last_updated" not in data["template"]
    assert data["projection"]["targets"] == ["claude", "codex", "gemini"]
    assert data["projection"]["profile"] == "default"
    assert data["projection"]["allow_local_generation"] is True
    assert ".standards/commit.yaml" in data["managed_files"]
    assert "CLAUDE.md" in data["managed_files"]


def test_managed_files_sorted(tmp_path: Path):
    """managed_files 應依字母排序。"""
    create_tracking_file(
        name="test",
        url="https://github.com/test/test.git",
        branch="main",
        managed_files=["z.md", "a.md", "m.md"],
        project_dir=tmp_path,
    )
    data = load_tracking_file(tmp_path)
    assert data["managed_files"] == ["a.md", "m.md", "z.md"]


def test_load_tracking_file_backfills_schema_defaults(tmp_path: Path):
    """舊版檔案載入時自動補齊 schema v2 預設欄位。"""
    tracking = tmp_path / ".ai-dev-project.yaml"
    tracking.write_text(
        "template:\n  name: legacy\nmanaged_files:\n  - CLAUDE.md\n",
        encoding="utf-8",
    )

    data = load_tracking_file(tmp_path)

    assert data is not None
    assert data["managed_by"] == "ai-dev"
    assert data["schema_version"] == "2"
    assert data["project_id"] == _expected_project_id(tmp_path)
    assert data["projection"]["allow_local_generation"] is True


def test_get_managed_files_no_tracking(tmp_path: Path):
    """沒有追蹤檔案時回傳空清單。"""
    result = get_managed_files(tmp_path)
    assert result == []


def test_get_managed_files_with_tracking(tmp_path: Path):
    """有追蹤檔案時回傳清單。"""
    create_tracking_file(
        name="test",
        url="https://github.com/test/test.git",
        branch="main",
        managed_files=["CLAUDE.md", ".gemini/settings.json"],
        project_dir=tmp_path,
    )
    result = get_managed_files(tmp_path)
    assert "CLAUDE.md" in result
    assert ".gemini/settings.json" in result


def test_is_file_managed_true(tmp_path: Path):
    """已管理的檔案回傳模板名稱。"""
    create_tracking_file(
        name="qdm-ai-base",
        url="https://github.com/ValorVie/qdm-ai-base.git",
        branch="main",
        managed_files=["CLAUDE.md"],
        project_dir=tmp_path,
    )
    result = is_file_managed("CLAUDE.md", tmp_path)
    assert result == "qdm-ai-base"


def test_is_file_managed_false(tmp_path: Path):
    """未管理的檔案回傳 None。"""
    create_tracking_file(
        name="qdm-ai-base",
        url="https://github.com/ValorVie/qdm-ai-base.git",
        branch="main",
        managed_files=["CLAUDE.md"],
        project_dir=tmp_path,
    )
    result = is_file_managed("OTHER.md", tmp_path)
    assert result is None


def test_is_file_managed_no_tracking(tmp_path: Path):
    """沒有追蹤檔案時回傳 None。"""
    result = is_file_managed("CLAUDE.md", tmp_path)
    assert result is None


def test_update_tracking_file(tmp_path: Path):
    """更新後 managed_files 應變更，且 template 保持意圖資料。"""
    create_tracking_file(
        name="test",
        url="https://github.com/test/test.git",
        branch="main",
        managed_files=["CLAUDE.md"],
        project_dir=tmp_path,
    )
    initial = load_tracking_file(tmp_path)

    update_tracking_file(managed_files=["CLAUDE.md", "NEW.md"], project_dir=tmp_path)

    updated = load_tracking_file(tmp_path)
    assert "NEW.md" in updated["managed_files"]
    assert updated["project_id"] == _expected_project_id(tmp_path)
    assert updated["template"] == initial["template"]
    assert "initialized_at" not in updated["template"]
    assert "last_updated" not in updated["template"]


def test_save_tracking_file_strips_runtime_template_fields(tmp_path: Path):
    """save_tracking_file 應清除 runtime timestamp 欄位。"""
    save_tracking_file(
        {
            "template": {
                "name": "test",
                "url": "https://github.com/test/test.git",
                "branch": "main",
                "initialized_at": "2026-03-10T00:00:00+08:00",
                "last_updated": "2026-03-10T00:00:01+08:00",
            },
            "managed_files": ["CLAUDE.md"],
        },
        tmp_path,
    )

    data = load_tracking_file(tmp_path)

    assert data is not None
    assert "initialized_at" not in data["template"]
    assert "last_updated" not in data["template"]


def test_update_tracking_file_not_exist(tmp_path: Path):
    """追蹤檔案不存在時應拋出 FileNotFoundError。"""
    with pytest.raises(FileNotFoundError):
        update_tracking_file(managed_files=["CLAUDE.md"], project_dir=tmp_path)


def test_skipped_files_not_tracked(tmp_path: Path):
    """跳過的檔案不應出現在 managed_files 中（由呼叫端負責不傳入）。"""
    create_tracking_file(
        name="test",
        url="https://github.com/test/test.git",
        branch="main",
        managed_files=["CLAUDE.md"],  # 跳過的 OTHER.md 未包含
        project_dir=tmp_path,
    )
    result = get_managed_files(tmp_path)
    assert "OTHER.md" not in result

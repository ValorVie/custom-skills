"""project_blocks.py 的單元測試。"""

from pathlib import Path

from script.utils.project_blocks import (
    get_block_markers,
    read_managed_block,
    remove_managed_block,
    upsert_managed_block,
)


def test_upsert_managed_block_preserves_user_content(tmp_path: Path):
    """首次寫入與更新都保留區塊外內容。"""
    target = tmp_path / "AGENTS.md"
    target.write_text("# User header\n", encoding="utf-8")

    upsert_managed_block(target, "ai-dev-project", "generated line")
    upsert_managed_block(target, "ai-dev-project", "new generated line")

    content = target.read_text(encoding="utf-8")

    assert "# User header" in content
    assert "new generated line" in content
    assert read_managed_block(target, "ai-dev-project") == "new generated line"


def test_upsert_managed_block_creates_file_when_missing(tmp_path: Path):
    """目標不存在時建立新檔。"""
    target = tmp_path / "AGENTS.md"

    upsert_managed_block(target, "ai-dev-project", "generated line")

    content = target.read_text(encoding="utf-8")
    start_marker, end_marker = get_block_markers("ai-dev-project")

    assert content == f"{start_marker}\ngenerated line\n{end_marker}\n"


def test_read_managed_block_returns_current_content(tmp_path: Path):
    """可讀出目前區塊內容。"""
    target = tmp_path / "AGENTS.md"
    upsert_managed_block(target, "ai-dev-project", "line 1\nline 2")

    content = read_managed_block(target, "ai-dev-project")

    assert content == "line 1\nline 2"


def test_remove_managed_block_preserves_user_content(tmp_path: Path):
    """移除區塊時保留使用者內容。"""
    target = tmp_path / "AGENTS.md"
    target.write_text("# User header\n", encoding="utf-8")
    upsert_managed_block(target, "ai-dev-project", "generated line")

    removed = remove_managed_block(target, "ai-dev-project")

    assert removed is True
    assert target.read_text(encoding="utf-8") == "# User header\n"

"""project_blocks.py 的單元測試。"""

from pathlib import Path

from script.utils.project_blocks import (
    get_block_markers,
    read_managed_block,
    remove_managed_block,
    upsert_managed_block,
)


def test_upsert_managed_block_preserves_user_content(tmp_path: Path):
    """首次寫入與更新都保留區塊外內容，且 managed block 置頂。"""
    target = tmp_path / "AGENTS.md"
    target.write_text("# User header\n", encoding="utf-8")

    upsert_managed_block(target, "ai-dev-project", "generated line")
    upsert_managed_block(target, "ai-dev-project", "new generated line")

    content = target.read_text(encoding="utf-8")
    start_marker, end_marker = get_block_markers("ai-dev-project")

    assert content.startswith(
        f"{start_marker}\nnew generated line\n{end_marker}\n\n"
    )
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


def test_upsert_managed_block_moves_existing_block_to_top(tmp_path: Path):
    """既有 block 不在頂部時，更新後應搬到檔案最上方。"""
    target = tmp_path / "AGENTS.md"
    start_marker, end_marker = get_block_markers("ai-dev-project")
    target.write_text(
        "# User header\n\n"
        f"{start_marker}\nold generated line\n{end_marker}\n",
        encoding="utf-8",
    )

    upsert_managed_block(target, "ai-dev-project", "new generated line")

    content = target.read_text(encoding="utf-8")
    assert content.startswith(
        f"{start_marker}\nnew generated line\n{end_marker}\n\n# User header\n"
    )


def test_get_block_markers_with_labels():
    """帶 label 的 marker 包含語義文字。"""
    start, end = get_block_markers(
        "ai-dev-project", open_label="rules here", close_label="end of rules"
    )

    assert start == "<!-- >>> ai-dev:ai-dev-project | rules here -->"
    assert end == "<!-- <<< ai-dev:ai-dev-project | end of rules -->"


def test_get_block_markers_without_labels():
    """不帶 label 時保持舊格式（向下相容）。"""
    start, end = get_block_markers("ai-dev-project")

    assert start == "<!-- >>> ai-dev:ai-dev-project -->"
    assert end == "<!-- <<< ai-dev:ai-dev-project -->"


def test_upsert_with_labels_produces_labeled_markers(tmp_path: Path):
    """帶 label 的 upsert 產出帶語義的 marker。"""
    target = tmp_path / "CLAUDE.md"

    upsert_managed_block(
        target, "ai-dev-project", "content",
        open_label="⚠️ 必須遵守", close_label="規則結束",
    )

    text = target.read_text(encoding="utf-8")
    assert "<!-- >>> ai-dev:ai-dev-project | ⚠️ 必須遵守 -->" in text
    assert "<!-- <<< ai-dev:ai-dev-project | 規則結束 -->" in text
    assert read_managed_block(target, "ai-dev-project") == "content"


def test_upsert_with_labels_finds_old_format_block(tmp_path: Path):
    """帶 label 的 upsert 能正確找到並替換舊格式（無 label）的 block。"""
    target = tmp_path / "CLAUDE.md"
    # 先用舊格式建立
    upsert_managed_block(target, "ai-dev-project", "old content")
    assert "<!-- >>> ai-dev:ai-dev-project -->" in target.read_text(encoding="utf-8")

    # 再用新格式更新
    upsert_managed_block(
        target, "ai-dev-project", "new content",
        open_label="⚠️ 必須遵守",
    )

    text = target.read_text(encoding="utf-8")
    assert "<!-- >>> ai-dev:ai-dev-project | ⚠️ 必須遵守 -->" in text
    assert "<!-- >>> ai-dev:ai-dev-project -->" not in text  # 舊格式已被替換
    assert read_managed_block(target, "ai-dev-project") == "new content"


def test_read_and_remove_work_with_labeled_markers(tmp_path: Path):
    """read 和 remove 在帶 label 的 marker 上正常運作。"""
    target = tmp_path / "CLAUDE.md"
    target.write_text("# User content\n", encoding="utf-8")

    upsert_managed_block(
        target, "ai-dev-project", "managed content",
        open_label="rules", close_label="end",
    )

    assert read_managed_block(target, "ai-dev-project") == "managed content"

    removed = remove_managed_block(target, "ai-dev-project")
    assert removed is True
    assert target.read_text(encoding="utf-8") == "# User content\n"

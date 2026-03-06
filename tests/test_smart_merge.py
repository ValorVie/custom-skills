"""smart_merge.py 的單元測試。"""

from pathlib import Path
from unittest.mock import patch

import pytest

from script.utils.smart_merge import (
    MergeStats,
    _compute_incremental_lines,
    merge_file,
    merge_template,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ── MergeStats ──────────────────────────────────────────────────────────────


def test_merge_stats_total_managed():
    stats = MergeStats()
    stats.new = 2
    stats.overwritten = 1
    stats.appended = 1
    stats.incremental = 1
    stats.skipped = 3
    assert stats.total_managed() == 5


# ── merge_file ───────────────────────────────────────────────────────────────


def test_merge_file_new(tmp_path: Path):
    """目標不存在時直接複製。"""
    src = tmp_path / "src" / "CLAUDE.md"
    dst = tmp_path / "dst" / "CLAUDE.md"
    _write(src, "template content")

    stats = MergeStats()
    result = merge_file(src, dst, "CLAUDE.md", stats=stats)

    assert result == "new"
    assert dst.read_text() == "template content"
    assert stats.new == 1


def test_merge_file_identical(tmp_path: Path):
    """內容相同時跳過。"""
    src = tmp_path / "src" / "a.md"
    dst = tmp_path / "dst" / "a.md"
    _write(src, "same content")
    _write(dst, "same content")

    stats = MergeStats()
    result = merge_file(src, dst, "a.md", stats=stats)

    assert result == "identical"
    assert stats.identical == 1


def test_merge_file_force_overwrite(tmp_path: Path):
    """--force 時直接覆蓋。"""
    src = tmp_path / "src" / "a.md"
    dst = tmp_path / "dst" / "a.md"
    _write(src, "new content")
    _write(dst, "old content")

    stats = MergeStats()
    result = merge_file(src, dst, "a.md", force=True, stats=stats)

    assert result == "overwritten"
    assert dst.read_text() == "new content"
    assert stats.overwritten == 1


def test_merge_file_skip_conflicts(tmp_path: Path):
    """--skip-conflicts 時跳過衝突。"""
    src = tmp_path / "src" / "a.md"
    dst = tmp_path / "dst" / "a.md"
    _write(src, "new content")
    _write(dst, "old content")

    stats = MergeStats()
    result = merge_file(src, dst, "a.md", skip_conflicts=True, stats=stats)

    assert result == "skipped"
    assert dst.read_text() == "old content"  # 未被修改
    assert stats.skipped == 1


def test_merge_file_interactive_overwrite(tmp_path: Path):
    """互動模式選 O（覆蓋）。"""
    src = tmp_path / "src" / "a.md"
    dst = tmp_path / "dst" / "a.md"
    _write(src, "new")
    _write(dst, "old")

    stats = MergeStats()
    with patch("script.utils.smart_merge.Prompt.ask", return_value="O"):
        result = merge_file(src, dst, "a.md", stats=stats)

    assert result == "overwritten"
    assert dst.read_text() == "new"


def test_merge_file_interactive_append(tmp_path: Path):
    """互動模式選 A（附加）。"""
    src = tmp_path / "src" / "a.md"
    dst = tmp_path / "dst" / "a.md"
    _write(src, "appended")
    _write(dst, "existing\n")

    stats = MergeStats()
    with patch("script.utils.smart_merge.Prompt.ask", return_value="A"):
        result = merge_file(src, dst, "a.md", stats=stats)

    assert result == "appended"
    assert "existing" in dst.read_text()
    assert "appended" in dst.read_text()
    assert stats.appended == 1


def test_merge_file_interactive_skip(tmp_path: Path):
    """互動模式選 S（跳過）。"""
    src = tmp_path / "src" / "a.md"
    dst = tmp_path / "dst" / "a.md"
    _write(src, "new")
    _write(dst, "old")

    stats = MergeStats()
    with patch("script.utils.smart_merge.Prompt.ask", return_value="S"):
        result = merge_file(src, dst, "a.md", stats=stats)

    assert result == "skipped"
    assert dst.read_text() == "old"  # 未被修改


def test_merge_file_interactive_incremental(tmp_path: Path):
    """互動模式選 I（增量附加）：只附加目標檔案中不存在的行。"""
    src = tmp_path / "src" / ".gitignore"
    dst = tmp_path / "dst" / ".gitignore"
    _write(src, "node_modules/\n.env\n.DS_Store\n__pycache__/\n")
    _write(dst, "node_modules/\n.env\nvendor/\n")

    stats = MergeStats()
    with patch("script.utils.smart_merge.Prompt.ask", return_value="I"):
        result = merge_file(src, dst, ".gitignore", stats=stats)

    assert result == "incremental"
    content = dst.read_text()
    # 原有內容保留
    assert "node_modules/" in content
    assert ".env" in content
    assert "vendor/" in content
    # 新增的行被附加
    assert ".DS_Store" in content
    assert "__pycache__/" in content
    assert stats.incremental == 1


def test_merge_file_incremental_no_new_lines(tmp_path: Path):
    """增量附加但無新內容時，視為相同。"""
    src = tmp_path / "src" / "a.txt"
    dst = tmp_path / "dst" / "a.txt"
    _write(src, "line1\nline2\n")
    _write(dst, "line1\nline2\nline3\n")

    stats = MergeStats()
    with patch("script.utils.smart_merge.Prompt.ask", return_value="I"):
        result = merge_file(src, dst, "a.txt", stats=stats)

    assert result == "identical"
    assert stats.identical == 1
    # 內容不應被修改
    assert dst.read_text() == "line1\nline2\nline3\n"


# ── _compute_incremental_lines ───────────────────────────────────────────────


def test_compute_incremental_lines_basic(tmp_path: Path):
    """基本增量計算：找出來源有但目標沒有的行。"""
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    _write(src, "aaa\nbbb\nccc\n")
    _write(dst, "aaa\nddd\n")

    result = _compute_incremental_lines(src, dst)
    assert "bbb" in result
    assert "ccc" in result
    assert "aaa" not in result


def test_compute_incremental_lines_all_exist(tmp_path: Path):
    """來源的所有行都已在目標中存在，回傳空。"""
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    _write(src, "aaa\nbbb\n")
    _write(dst, "bbb\naaa\nccc\n")

    result = _compute_incremental_lines(src, dst)
    assert result == []


def test_compute_incremental_lines_ignores_blank(tmp_path: Path):
    """空白行不列入比對。"""
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    _write(src, "\n\naaa\n\n")
    _write(dst, "aaa\n")

    result = _compute_incremental_lines(src, dst)
    assert result == []


# ── merge_template ────────────────────────────────────────────────────────────


def test_merge_template_excludes_git_dir(tmp_path: Path):
    """排除 .git 目錄。"""
    template = tmp_path / "template"
    target = tmp_path / "target"
    _write(template / ".git" / "config", "git config")
    _write(template / "CLAUDE.md", "content")

    managed, _ = merge_template(template, target)

    assert "CLAUDE.md" in managed
    assert not (target / ".git").exists()


def test_merge_template_excludes_gitkeep(tmp_path: Path):
    """排除 .gitkeep 檔案。"""
    template = tmp_path / "template"
    target = tmp_path / "target"
    _write(template / ".standards" / ".gitkeep", "")
    _write(template / "CLAUDE.md", "content")

    managed, _ = merge_template(template, target)

    assert "CLAUDE.md" in managed
    assert not (target / ".standards" / ".gitkeep").exists()


def test_merge_template_excludes_root_readme(tmp_path: Path):
    """排除根目錄的 README.md。"""
    template = tmp_path / "template"
    target = tmp_path / "target"
    _write(template / "README.md", "readme")
    _write(template / ".claude" / "README.md", "sub readme")  # 子目錄不排除
    _write(template / "CLAUDE.md", "content")

    managed, _ = merge_template(template, target)

    assert "CLAUDE.md" in managed
    assert "README.md" not in managed
    assert ".claude/README.md" in managed  # 子目錄的 README.md 不排除


def test_merge_template_excludes_root_license(tmp_path: Path):
    """排除根目錄的 LICENSE。"""
    template = tmp_path / "template"
    target = tmp_path / "target"
    _write(template / "LICENSE", "MIT")
    _write(template / "CLAUDE.md", "content")

    managed, _ = merge_template(template, target)

    assert "CLAUDE.md" in managed
    assert "LICENSE" not in managed


def test_merge_template_only_files(tmp_path: Path):
    """only_files 只合併指定檔案。"""
    template = tmp_path / "template"
    target = tmp_path / "target"
    _write(template / "CLAUDE.md", "new claude")
    _write(template / "GEMINI.md", "new gemini")
    _write(target / "CLAUDE.md", "old claude")
    _write(target / "GEMINI.md", "old gemini")

    managed, stats = merge_template(
        template, target, force=True, only_files=["CLAUDE.md"]
    )

    assert "CLAUDE.md" in managed
    assert "GEMINI.md" not in managed
    assert (target / "GEMINI.md").read_text() == "old gemini"  # 未被修改


def test_merge_template_warns_tool_dirs(tmp_path: Path, capsys):
    """模板包含標準工具目錄時發出警告。"""
    template = tmp_path / "template"
    target = tmp_path / "target"
    (template / "skills").mkdir(parents=True)
    _write(template / "skills" / "some-skill" / "SKILL.md", "skill")

    with patch("script.utils.smart_merge.console") as mock_console:
        merge_template(template, target)
        # 檢查警告訊息被呼叫
        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("標準工具目錄" in c for c in calls)


def test_merge_template_skipped_not_in_managed(tmp_path: Path):
    """使用者跳過的檔案不應出現在 managed_files 中。"""
    template = tmp_path / "template"
    target = tmp_path / "target"
    _write(template / "CLAUDE.md", "new")
    _write(target / "CLAUDE.md", "old")

    with patch("script.utils.smart_merge.Prompt.ask", return_value="S"):
        managed, stats = merge_template(template, target)

    assert "CLAUDE.md" not in managed
    assert stats.skipped == 1

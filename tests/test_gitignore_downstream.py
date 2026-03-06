"""gitignore_downstream.py 的單元測試。"""

from pathlib import Path

import pytest

from script.utils.gitignore_downstream import (
    MARKER_END,
    MARKER_START,
    merge_gitignore_downstream,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestMergeGitignoreDownstream:
    """merge_gitignore_downstream 整合測試。"""

    def test_no_downstream_file_skips(self, tmp_path: Path) -> None:
        """模版無 .gitignore-downstream 時不動目標。"""
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        target_dir = tmp_path / "target"
        target_dir.mkdir()
        _write(target_dir / ".gitignore", "node_modules\n")

        result = merge_gitignore_downstream(
            template_dir=template_dir,
            target_dir=target_dir,
            template_name="my-template",
        )

        assert result is False
        assert (target_dir / ".gitignore").read_text() == "node_modules\n"

    def test_first_init_creates_block(self, tmp_path: Path) -> None:
        """首次初始化：目標有 .gitignore，附加標記區塊。"""
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        _write(template_dir / ".gitignore-downstream", ".atlas/\n")

        target_dir = tmp_path / "target"
        target_dir.mkdir()
        _write(target_dir / ".gitignore", "node_modules\n")

        result = merge_gitignore_downstream(
            template_dir=template_dir,
            target_dir=target_dir,
            template_name="my-template",
        )

        assert result is True
        content = (target_dir / ".gitignore").read_text()
        assert "node_modules" in content
        assert MARKER_START.format(name="my-template") in content
        assert ".atlas/" in content
        assert MARKER_END.format(name="my-template") in content

    def test_first_init_no_existing_gitignore(self, tmp_path: Path) -> None:
        """目標無 .gitignore 時建立新檔。"""
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        _write(template_dir / ".gitignore-downstream", ".atlas/\n")

        target_dir = tmp_path / "target"
        target_dir.mkdir()

        result = merge_gitignore_downstream(
            template_dir=template_dir,
            target_dir=target_dir,
            template_name="my-template",
        )

        assert result is True
        content = (target_dir / ".gitignore").read_text()
        assert MARKER_START.format(name="my-template") in content
        assert ".atlas/" in content

    def test_update_replaces_existing_block(self, tmp_path: Path) -> None:
        """--update：替換既有標記區塊。"""
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        _write(template_dir / ".gitignore-downstream", ".atlas/\n.stubs/\n")

        target_dir = tmp_path / "target"
        target_dir.mkdir()
        existing = (
            "node_modules\n"
            f"{MARKER_START.format(name='my-template')}\n"
            ".atlas/\n"
            f"{MARKER_END.format(name='my-template')}\n"
        )
        _write(target_dir / ".gitignore", existing)

        result = merge_gitignore_downstream(
            template_dir=template_dir,
            target_dir=target_dir,
            template_name="my-template",
        )

        assert result is True
        content = (target_dir / ".gitignore").read_text()
        assert ".stubs/" in content
        assert content.count(MARKER_START.format(name="my-template")) == 1

    def test_downstream_deleted_removes_block(self, tmp_path: Path) -> None:
        """模版刪除 .gitignore-downstream 時，移除目標區塊。"""
        template_dir = tmp_path / "template"
        template_dir.mkdir()

        target_dir = tmp_path / "target"
        target_dir.mkdir()
        existing = (
            "node_modules\n"
            f"{MARKER_START.format(name='my-template')}\n"
            ".atlas/\n"
            f"{MARKER_END.format(name='my-template')}\n"
        )
        _write(target_dir / ".gitignore", existing)

        result = merge_gitignore_downstream(
            template_dir=template_dir,
            target_dir=target_dir,
            template_name="my-template",
            remove_if_missing=True,
        )

        assert result is True
        content = (target_dir / ".gitignore").read_text()
        assert "node_modules" in content
        assert MARKER_START.format(name="my-template") not in content
        assert ".atlas/" not in content

    def test_preserves_trailing_newline(self, tmp_path: Path) -> None:
        """確保合併後檔案以換行結尾。"""
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        _write(template_dir / ".gitignore-downstream", ".atlas/")

        target_dir = tmp_path / "target"
        target_dir.mkdir()
        _write(target_dir / ".gitignore", "node_modules\n")

        merge_gitignore_downstream(
            template_dir=template_dir,
            target_dir=target_dir,
            template_name="my-template",
        )

        content = (target_dir / ".gitignore").read_text()
        assert content.endswith("\n")

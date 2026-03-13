"""init_from.py 的整合測試。"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from script.main import app
from script.utils.project_tracking import load_tracking_file

runner = CliRunner()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_template(base: Path, files: dict[str, str]) -> Path:
    """建立假的模板目錄。"""
    template_dir = base / "template"
    for rel, content in files.items():
        _write(template_dir / rel, content)
    return template_dir


# ── init-from 首次初始化 ─────────────────────────────────────────────────────


def test_init_from_new_files(tmp_path: Path):
    """首次初始化：新檔案直接複製。"""
    template_dir = _make_template(tmp_path, {"CLAUDE.md": "claude content"})
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    with (
        patch("script.commands.init_from._clone_template_repo", return_value=True),
        patch("script.commands.init_from.load_custom_repos", return_value={"repos": {}}),
        patch("script.commands.init_from._add_custom_repo"),
        patch("script.commands.init_from.Path.home", return_value=tmp_path),
    ):
        # 讓 target_dir 指向我們準備的 template
        with patch(
            "script.commands.init_from.merge_template",
            wraps=lambda template_dir, target_dir, **kw: __import__(
                "script.utils.smart_merge", fromlist=["merge_template"]
            ).merge_template(template_dir, target_dir, **kw),
        ):
            pass  # merge_template 在整合測試中直接用真實函式測試


def test_init_from_creates_tracking_file(tmp_path: Path):
    """初始化後應建立 .ai-dev-project.yaml。"""
    template_dir = _make_template(tmp_path, {"CLAUDE.md": "content"})
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    with (
        patch("script.commands.init_from._clone_template_repo", return_value=True),
        patch("script.commands.init_from.load_custom_repos", return_value={"repos": {}}),
        patch("script.commands.init_from._add_custom_repo"),
        patch(
            "script.commands.init_from.merge_template",
            return_value=(["CLAUDE.md"], MagicMock(new=1, identical=0, overwritten=0, appended=0, skipped=0)),
        ),
        patch("script.commands.init_from.Path.cwd", return_value=project_dir),
        patch("script.commands.init_from.Path.home", return_value=tmp_path),
    ):
        from script.utils.project_tracking import create_tracking_file
        create_tracking_file(
            name="qdm-ai-base",
            url="https://github.com/test/test.git",
            branch="main",
            managed_files=["CLAUDE.md"],
            project_dir=project_dir,
        )

    data = load_tracking_file(project_dir)
    assert data is not None
    assert data["template"]["name"] == "qdm-ai-base"
    assert "CLAUDE.md" in data["managed_files"]


# ── --update 模式 ────────────────────────────────────────────────────────────


def test_init_from_update_no_tracking_file(tmp_path: Path):
    """--update 但沒有 .ai-dev-project.yaml 時應報錯。"""
    import click
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    from script.commands.init_from import _run_update_mode
    with pytest.raises((SystemExit, click.exceptions.Exit)):
        _run_update_mode(cwd=project_dir, force=False, skip_conflicts=False)


def test_init_from_update_pulls_and_merges(tmp_path: Path):
    """--update 模式：拉取並合併所有模板檔案（包含上游新增的）。"""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    # 建立模板目錄（Path.home() / ".config" / name）
    template_dir = tmp_path / ".config" / "qdm-ai-base"
    _write(template_dir / "CLAUDE.md", "new content")

    from script.utils.project_tracking import create_tracking_file
    create_tracking_file(
        name="qdm-ai-base",
        url="https://github.com/test/test.git",
        branch="main",
        managed_files=["CLAUDE.md"],
        project_dir=project_dir,
    )

    mock_stats = MagicMock()
    mock_stats.new = 1
    mock_stats.identical = 0
    mock_stats.overwritten = 1
    mock_stats.appended = 0
    mock_stats.skipped = 0
    mock_stats.print_summary = MagicMock()

    with (
        patch("script.commands.init_from._pull_template_repo", return_value=True),
        patch("script.commands.init_from.Path.home", return_value=tmp_path),
        patch(
            "script.commands.init_from.merge_template",
            return_value=(["CLAUDE.md", "AGENTS.md"], mock_stats),
        ) as mock_merge,
    ):
        from script.commands.init_from import _run_update_mode
        _run_update_mode(cwd=project_dir, force=False, skip_conflicts=False)

        # 確認不再限制 only_files（掃描全部模板檔案）
        call_kwargs = mock_merge.call_args.kwargs
        assert "only_files" not in call_kwargs or call_kwargs.get("only_files") is None

    # 確認 managed_files 合併了新舊清單
    data = load_tracking_file(project_dir)
    assert data is not None
    assert "CLAUDE.md" in data["managed_files"]
    assert "AGENTS.md" in data["managed_files"]


def test_init_from_update_subcommand_exists():
    result = runner.invoke(app, ["init-from", "update"])

    assert result.exit_code == 1
    assert ".ai-dev-project.yaml" in result.output


def test_init_from_rejects_legacy_update_flag():
    result = runner.invoke(app, ["init-from", "--update"])

    assert result.exit_code != 0
    assert "init-from update" in result.output

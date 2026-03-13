from pathlib import Path

from typer.testing import CliRunner

from script.main import app
from script.commands import status as status_cmd


runner = CliRunner()


def test_status_section_filters_output(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(status_cmd.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        status_cmd.subprocess,
        "check_output",
        lambda args, **_kwargs: {
            ("node", "--version"): "v22.0.0\n",
            ("git", "--version"): "git version 2.39.0\n",
            ("git", "rev-parse", "HEAD"): "abc\n",
            ("git", "rev-parse", "origin/main"): "abc\n",
        }[tuple(args)],
    )
    monkeypatch.setattr(status_cmd, "REPOS", {})
    monkeypatch.setattr(status_cmd, "get_project_root", lambda: tmp_path)

    result = runner.invoke(app, ["status", "--section", "tools"])

    assert result.exit_code == 0
    assert "核心工具" in result.stdout
    assert "設定儲存庫" not in result.stdout


def test_status_invalid_section_exit_1():
    result = runner.invoke(app, ["status", "--section", "bad"])

    assert result.exit_code == 1
    assert "無效的 section" in result.stdout

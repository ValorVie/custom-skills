from pathlib import Path

from typer.testing import CliRunner

from script.commands import sync as sync_cmd
from script.main import app


runner = CliRunner()


def test_sync_help_includes_subcommands():
    result = runner.invoke(app, ["sync", "--help"])

    assert result.exit_code == 0
    assert "init" in result.stdout
    assert "push" in result.stdout
    assert "pull" in result.stdout


def test_sync_status_requires_init(monkeypatch):
    def _raise_missing():
        raise FileNotFoundError("missing")

    monkeypatch.setattr(sync_cmd, "load_sync_config", _raise_missing)

    result = runner.invoke(app, ["sync", "status"])

    assert result.exit_code == 0
    assert "ai-dev sync init" in result.stdout


def test_sync_init_writes_default_config(tmp_path: Path, monkeypatch):
    repo_dir = tmp_path / "sync-repo"
    captured = {}

    monkeypatch.setattr(sync_cmd, "check_command_exists", lambda _: True)
    monkeypatch.setattr(sync_cmd, "get_sync_repo_dir", lambda: repo_dir)
    monkeypatch.setattr(
        sync_cmd, "get_sync_config_path", lambda: tmp_path / "sync.yaml"
    )
    monkeypatch.setattr(
        sync_cmd, "git_init_or_clone", lambda *_args, **_kwargs: "initialized"
    )
    monkeypatch.setattr(
        sync_cmd,
        "sync_directory",
        lambda *_args, **_kwargs: {"added": 0, "updated": 0, "deleted": 0},
    )
    monkeypatch.setattr(sync_cmd, "git_add_commit", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(sync_cmd, "git_pull_rebase", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(sync_cmd, "git_push", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        sync_cmd, "save_sync_config", lambda data: captured.update({"cfg": data})
    )

    result = runner.invoke(
        app, ["sync", "init", "--remote", "git@example.com:me/sync.git"]
    )

    assert result.exit_code == 0
    assert captured["cfg"]["remote"] == "git@example.com:me/sync.git"
    assert len(captured["cfg"]["directories"]) == 2


def test_sync_add_updates_config(tmp_path: Path, monkeypatch):
    target_dir = tmp_path / "my-config"
    target_dir.mkdir()
    repo_dir = tmp_path / "sync-repo"
    repo_dir.mkdir()

    config = {
        "version": "1",
        "remote": "git@example.com:me/sync.git",
        "last_sync": None,
        "directories": [],
    }
    captured = {}

    monkeypatch.setattr(sync_cmd, "load_sync_config", lambda: config)
    monkeypatch.setattr(
        sync_cmd, "save_sync_config", lambda data: captured.update({"cfg": data})
    )
    monkeypatch.setattr(sync_cmd, "get_sync_repo_dir", lambda: repo_dir)
    monkeypatch.setattr(sync_cmd, "write_gitignore", lambda *_args, **_kwargs: None)

    result = runner.invoke(app, ["sync", "add", str(target_dir)])

    assert result.exit_code == 0
    assert len(captured["cfg"]["directories"]) == 1
    assert (repo_dir / captured["cfg"]["directories"][0]["repo_subdir"]).exists()


def test_sync_remove_rejects_last_directory(monkeypatch):
    config = {
        "version": "1",
        "remote": "git@example.com:me/sync.git",
        "last_sync": None,
        "directories": [
            {
                "path": "~/.claude",
                "repo_subdir": "claude",
                "ignore_profile": "claude",
                "custom_ignore": [],
            }
        ],
    }

    monkeypatch.setattr(sync_cmd, "load_sync_config", lambda: config)

    result = runner.invoke(app, ["sync", "remove", "~/.claude"])

    assert result.exit_code == 1
    assert "至少保留一個" in result.stdout

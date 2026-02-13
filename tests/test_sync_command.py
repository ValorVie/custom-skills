from pathlib import Path

import typer
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
        "_sync_local_to_repo",
        lambda *_args, **_kwargs: {"added": 0, "updated": 0, "deleted": 0},
    )
    monkeypatch.setattr(
        sync_cmd, "save_plugin_manifest", lambda *_args, **_kwargs: False
    )
    monkeypatch.setattr(sync_cmd, "check_lfs_available", lambda: False)
    monkeypatch.setattr(sync_cmd, "detect_lfs_patterns", lambda *_args, **_kwargs: [])
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


def test_sync_init_existing_repo_runs_lfs_migrate(tmp_path: Path, monkeypatch):
    repo_dir = tmp_path / "sync-repo"
    captured = {"patterns": None, "migrated": False}

    monkeypatch.setattr(
        sync_cmd, "check_command_exists", lambda *_args, **_kwargs: True
    )
    monkeypatch.setattr(sync_cmd, "get_sync_repo_dir", lambda: repo_dir)
    monkeypatch.setattr(
        sync_cmd, "get_sync_config_path", lambda: tmp_path / "sync.yaml"
    )
    monkeypatch.setattr(
        sync_cmd, "git_init_or_clone", lambda *_args, **_kwargs: "existing"
    )
    monkeypatch.setattr(
        sync_cmd, "save_plugin_manifest", lambda *_args, **_kwargs: False
    )
    monkeypatch.setattr(
        sync_cmd,
        "_sync_local_to_repo",
        lambda *_args, **_kwargs: {"added": 0, "updated": 0, "deleted": 0},
    )
    monkeypatch.setattr(sync_cmd, "check_lfs_available", lambda: True)
    monkeypatch.setattr(sync_cmd, "git_lfs_setup", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        sync_cmd,
        "detect_lfs_patterns",
        lambda *_args, **_kwargs: ["*.sqlite3"],
    )
    monkeypatch.setattr(
        sync_cmd,
        "git_lfs_migrate_existing",
        lambda *_args, **_kwargs: captured.update({"migrated": True}) or True,
    )
    monkeypatch.setattr(
        sync_cmd,
        "write_gitattributes",
        lambda *_args, lfs_patterns=None, **_kwargs: captured.update(
            {"patterns": lfs_patterns}
        ),
    )
    monkeypatch.setattr(sync_cmd, "git_add_commit", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(sync_cmd, "git_pull_rebase", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(sync_cmd, "git_push", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(sync_cmd, "save_sync_config", lambda *_args, **_kwargs: None)

    result = runner.invoke(
        app, ["sync", "init", "--remote", "git@example.com:me/sync.git"]
    )

    assert result.exit_code == 0
    assert captured["migrated"] is True
    assert captured["patterns"] == ["*.sqlite3"]


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


def test_sync_push_writes_gitattributes_with_lfs_patterns(tmp_path: Path, monkeypatch):
    repo_dir = tmp_path / "sync-repo"
    repo_dir.mkdir()
    captured = {"patterns": None}

    config = {
        "version": "1",
        "remote": "git@example.com:me/sync.git",
        "last_sync": None,
        "directories": [],
    }

    monkeypatch.setattr(sync_cmd, "load_sync_config", lambda: config)
    monkeypatch.setattr(sync_cmd, "get_sync_repo_dir", lambda: repo_dir)
    monkeypatch.setattr(sync_cmd, "write_gitignore", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        sync_cmd,
        "_sync_local_to_repo",
        lambda *_args, **_kwargs: {"added": 0, "updated": 0, "deleted": 0},
    )
    monkeypatch.setattr(sync_cmd, "check_lfs_available", lambda: True)
    monkeypatch.setattr(sync_cmd, "git_lfs_setup", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        sync_cmd,
        "detect_lfs_patterns",
        lambda *_args, **_kwargs: ["*.sqlite3"],
    )
    monkeypatch.setattr(
        sync_cmd,
        "write_gitattributes",
        lambda *_args, lfs_patterns=None, **_kwargs: captured.update(
            {"patterns": lfs_patterns}
        ),
    )
    monkeypatch.setattr(sync_cmd, "get_claude_subdir", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(sync_cmd, "git_add_commit", lambda *_args, **_kwargs: False)

    result = runner.invoke(app, ["sync", "push"])

    assert result.exit_code == 0
    assert captured["patterns"] == ["*.sqlite3"]


def test_sync_pull_force_skips_local_change_detection(tmp_path: Path, monkeypatch):
    repo_dir = tmp_path / "sync-repo"
    repo_dir.mkdir()
    config = {
        "version": "1",
        "remote": "git@example.com:me/sync.git",
        "last_sync": None,
        "directories": [],
    }

    monkeypatch.setattr(sync_cmd, "load_sync_config", lambda: config)
    monkeypatch.setattr(sync_cmd, "get_sync_repo_dir", lambda: repo_dir)
    monkeypatch.setattr(
        sync_cmd,
        "detect_local_changes",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("detect_local_changes should not be called")
        ),
    )
    monkeypatch.setattr(sync_cmd, "git_pull_rebase", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        sync_cmd,
        "_sync_repo_to_local",
        lambda *_args, **_kwargs: {"added": 0, "updated": 0, "deleted": 0},
    )
    monkeypatch.setattr(sync_cmd, "save_sync_config", lambda *_args, **_kwargs: None)

    result = runner.invoke(app, ["sync", "pull", "--force"])

    assert result.exit_code == 0
    assert "sync pull 完成" in result.stdout


def test_sync_pull_cancel_does_not_execute_pull(tmp_path: Path, monkeypatch):
    repo_dir = tmp_path / "sync-repo"
    repo_dir.mkdir()
    config = {
        "version": "1",
        "remote": "git@example.com:me/sync.git",
        "last_sync": None,
        "directories": [],
    }
    called = {"pulled": False}

    monkeypatch.setattr(sync_cmd, "load_sync_config", lambda: config)
    monkeypatch.setattr(sync_cmd, "get_sync_repo_dir", lambda: repo_dir)
    monkeypatch.setattr(
        sync_cmd,
        "detect_local_changes",
        lambda *_args, **_kwargs: {
            "total_changes": 1,
            "files": [{"path": "claude/settings.json", "type": "modified"}],
        },
    )
    monkeypatch.setattr(
        sync_cmd,
        "_prompt_pull_safety",
        lambda *_args, **_kwargs: sync_cmd.PULL_CHOICE_CANCEL,
    )
    monkeypatch.setattr(
        sync_cmd,
        "git_pull_rebase",
        lambda *_args, **_kwargs: called.update({"pulled": True}) or True,
    )
    monkeypatch.setattr(
        sync_cmd,
        "_sync_repo_to_local",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("pull sync should not run on cancel")
        ),
    )

    result = runner.invoke(app, ["sync", "pull"])

    assert result.exit_code == 0
    assert called["pulled"] is False
    assert "已取消" in result.stdout


def test_sync_pull_force_choice_executes_pull(tmp_path: Path, monkeypatch):
    repo_dir = tmp_path / "sync-repo"
    repo_dir.mkdir()
    config = {
        "version": "1",
        "remote": "git@example.com:me/sync.git",
        "last_sync": None,
        "directories": [],
    }
    called = {"synced": False}

    monkeypatch.setattr(sync_cmd, "load_sync_config", lambda: config)
    monkeypatch.setattr(sync_cmd, "get_sync_repo_dir", lambda: repo_dir)
    monkeypatch.setattr(
        sync_cmd,
        "detect_local_changes",
        lambda *_args, **_kwargs: {
            "total_changes": 1,
            "files": [{"path": "claude/settings.json", "type": "modified"}],
        },
    )
    monkeypatch.setattr(
        sync_cmd,
        "_prompt_pull_safety",
        lambda *_args, **_kwargs: sync_cmd.PULL_CHOICE_FORCE_PULL,
    )
    monkeypatch.setattr(sync_cmd, "git_pull_rebase", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        sync_cmd,
        "_sync_repo_to_local",
        lambda *_args, **_kwargs: called.update({"synced": True})
        or {"added": 0, "updated": 0, "deleted": 0},
    )
    monkeypatch.setattr(sync_cmd, "save_sync_config", lambda *_args, **_kwargs: None)

    result = runner.invoke(app, ["sync", "pull"])

    assert result.exit_code == 0
    assert called["synced"] is True


def test_sync_pull_push_failure_aborts_pull(tmp_path: Path, monkeypatch):
    repo_dir = tmp_path / "sync-repo"
    repo_dir.mkdir()
    config = {
        "version": "1",
        "remote": "git@example.com:me/sync.git",
        "last_sync": None,
        "directories": [],
    }
    called = {"pulled": False}

    monkeypatch.setattr(sync_cmd, "load_sync_config", lambda: config)
    monkeypatch.setattr(sync_cmd, "get_sync_repo_dir", lambda: repo_dir)
    monkeypatch.setattr(
        sync_cmd,
        "detect_local_changes",
        lambda *_args, **_kwargs: {
            "total_changes": 1,
            "files": [{"path": "claude/settings.json", "type": "modified"}],
        },
    )
    monkeypatch.setattr(
        sync_cmd,
        "_prompt_pull_safety",
        lambda *_args, **_kwargs: sync_cmd.PULL_CHOICE_PUSH_THEN_PULL,
    )
    monkeypatch.setattr(
        sync_cmd,
        "push",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(typer.Exit(code=1)),
    )
    monkeypatch.setattr(
        sync_cmd,
        "git_pull_rebase",
        lambda *_args, **_kwargs: called.update({"pulled": True}) or True,
    )

    result = runner.invoke(app, ["sync", "pull"])

    assert result.exit_code == 1
    assert called["pulled"] is False

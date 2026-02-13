from pathlib import Path

import pytest

from script.utils import sync_config


def test_load_and_save_sync_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config_path = tmp_path / "sync.yaml"
    monkeypatch.setattr(sync_config, "get_sync_config_path", lambda: config_path)

    config = {
        "version": "1",
        "remote": "git@github.com:user/sync.git",
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

    sync_config.save_sync_config(config)
    loaded = sync_config.load_sync_config()

    assert loaded["remote"] == "git@github.com:user/sync.git"
    assert loaded["directories"][0]["repo_subdir"] == "claude"


def test_load_sync_config_raises_when_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    config_path = tmp_path / "sync.yaml"
    monkeypatch.setattr(sync_config, "get_sync_config_path", lambda: config_path)

    with pytest.raises(FileNotFoundError):
        sync_config.load_sync_config()


def test_get_ignore_patterns_profiles():
    claude_patterns = sync_config.get_ignore_patterns("claude")
    mem_patterns = sync_config.get_ignore_patterns("claude-mem")
    custom_patterns = sync_config.get_ignore_patterns("custom", ["cache/", "*.log"])

    assert "debug/" in claude_patterns
    assert "worker.pid" in mem_patterns
    assert custom_patterns == ["cache/", "*.log"]


def test_prefix_excludes():
    result = sync_config.prefix_excludes("claude", ["debug/", "*.log"])
    assert result == ["claude/debug/", "claude/*.log"]


def test_generate_gitignore_contains_prefixed_rules():
    directories = [
        {
            "path": "~/.claude",
            "repo_subdir": "claude",
            "ignore_profile": "claude",
            "custom_ignore": [],
        },
        {
            "path": "~/.claude-mem",
            "repo_subdir": "claude-mem",
            "ignore_profile": "claude-mem",
            "custom_ignore": [],
        },
    ]

    content = sync_config.generate_gitignore(directories)

    assert "claude/debug/" in content
    assert "claude-mem/logs/" in content
    assert ".DS_Store" in content


def test_generate_gitattributes_contains_required_rules():
    content = sync_config.generate_gitattributes()
    assert "*.jsonl merge=union" in content
    assert "*.md text eol=lf" in content


def test_generate_gitattributes_appends_lfs_rules_when_provided():
    content = sync_config.generate_gitattributes(
        lfs_patterns=["*.sqlite3", "*.db", "*.sqlite3"]
    )

    assert "*.jsonl merge=union" in content
    assert "*.db filter=lfs diff=lfs merge=lfs -text" in content
    assert "*.sqlite3 filter=lfs diff=lfs merge=lfs -text" in content


def test_write_gitattributes_passes_lfs_patterns(tmp_path: Path):
    path = sync_config.write_gitattributes(tmp_path, lfs_patterns=["*.sqlite3"])
    content = path.read_text(encoding="utf-8")

    assert "*.sqlite3 filter=lfs diff=lfs merge=lfs -text" in content


def test_check_lfs_available_uses_git_lfs_binary(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        sync_config.shutil,
        "which",
        lambda command: "/usr/local/bin/git-lfs" if command == "git-lfs" else None,
    )
    assert sync_config.check_lfs_available() is True


def test_detect_lfs_patterns_skips_hidden_and_jsonl(tmp_path: Path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    def _truncate(path: Path, size: int) -> None:
        with open(path, "wb") as f:
            f.truncate(size)

    large_size = 2 * 1024 * 1024
    _truncate(repo_dir / "chroma.sqlite3", large_size)
    _truncate(repo_dir / "backup.db", large_size)
    _truncate(repo_dir / "history.jsonl", large_size)
    _truncate(repo_dir / ".hidden.db", large_size)

    hidden_dir = repo_dir / ".cache"
    hidden_dir.mkdir()
    _truncate(hidden_dir / "cache.sqlite3", large_size)

    patterns = sync_config.detect_lfs_patterns(repo_dir, threshold_mb=1)

    assert patterns == ["*.db", "*.sqlite3"]


def test_git_lfs_migrate_existing_runs_import(monkeypatch: pytest.MonkeyPatch):
    calls: list[list[str]] = []

    class _Result:
        def __init__(self, returncode: int):
            self.returncode = returncode

    def fake_run(command, **_kwargs):
        calls.append(command)
        return _Result(0)

    monkeypatch.setattr(sync_config.subprocess, "run", fake_run)

    ok = sync_config.git_lfs_migrate_existing("/tmp/repo", ["*.sqlite3", "*.db"])

    assert ok is True
    assert any(cmd[:4] == ["git", "lfs", "migrate", "import"] for cmd in calls)


def test_detect_local_changes_returns_empty_when_no_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    repo_dir = tmp_path / "sync-repo"
    local_dir = tmp_path / "local"
    repo_subdir = repo_dir / "claude"
    repo_subdir.mkdir(parents=True)
    local_dir.mkdir()

    (repo_subdir / "settings.json").write_text('{"theme": "light"}\n', encoding="utf-8")
    (local_dir / "settings.json").write_text('{"theme": "light"}\n', encoding="utf-8")

    monkeypatch.setattr(sync_config, "get_sync_repo_dir", lambda: repo_dir)

    config = {
        "directories": [
            {
                "path": str(local_dir),
                "repo_subdir": "claude",
                "ignore_profile": "custom",
                "custom_ignore": [],
            }
        ]
    }

    changes = sync_config.detect_local_changes(config)

    assert changes["total_changes"] == 0
    assert changes["directories"] == []
    assert changes["files"] == []


def test_detect_local_changes_reports_added_modified_deleted_and_respects_ignore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    repo_dir = tmp_path / "sync-repo"
    local_dir = tmp_path / "local"
    repo_subdir = repo_dir / "claude"
    repo_subdir.mkdir(parents=True)
    local_dir.mkdir()

    (local_dir / "local-only.txt").write_text("local\n", encoding="utf-8")
    (local_dir / "modified.txt").write_text("local-version\n", encoding="utf-8")
    (local_dir / "skip.tmp").write_text("ignored\n", encoding="utf-8")

    (repo_subdir / "modified.txt").write_text("repo-version\n", encoding="utf-8")
    (repo_subdir / "deleted.txt").write_text("repo-only\n", encoding="utf-8")

    monkeypatch.setattr(sync_config, "get_sync_repo_dir", lambda: repo_dir)

    config = {
        "directories": [
            {
                "path": str(local_dir),
                "repo_subdir": "claude",
                "ignore_profile": "custom",
                "custom_ignore": ["*.tmp"],
            }
        ]
    }

    changes = sync_config.detect_local_changes(config)

    assert changes["total_changes"] == 3
    assert len(changes["directories"]) == 1

    directory_changes = changes["directories"][0]
    assert directory_changes["added"] == ["claude/local-only.txt"]
    assert directory_changes["modified"] == ["claude/modified.txt"]
    assert directory_changes["deleted"] == ["claude/deleted.txt"]

    changed_paths = [item["path"] for item in changes["files"]]
    assert "claude/skip.tmp" not in changed_paths

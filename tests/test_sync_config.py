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

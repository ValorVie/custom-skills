import subprocess
from pathlib import Path

import pytest

from script.utils import sync_config


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    return tmp_path


def test_sync_directory_shutil_copy_and_delete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()

    (src / "keep.txt").write_text("v1\n", encoding="utf-8")
    (dst / "stale.txt").write_text("old\n", encoding="utf-8")

    monkeypatch.setattr(sync_config, "get_os", lambda: "windows")

    result = sync_config.sync_directory(src, dst, excludes=[], delete=True)

    assert (dst / "keep.txt").exists()
    assert not (dst / "stale.txt").exists()
    assert result["deleted"] == 1


def test_sync_directory_respects_excludes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "keep.txt").write_text("ok\n", encoding="utf-8")
    (src / "debug.log").write_text("skip\n", encoding="utf-8")

    monkeypatch.setattr(sync_config, "get_os", lambda: "windows")

    sync_config.sync_directory(src, dst, excludes=["*.log"], delete=True)

    assert (dst / "keep.txt").exists()
    assert not (dst / "debug.log").exists()


def test_git_init_or_clone_fallback_to_init(tmp_path: Path):
    repo_dir = tmp_path / "sync-repo"

    action = sync_config.git_init_or_clone(repo_dir, "file:///does-not-exist/repo.git")

    assert action == "initialized"
    assert (repo_dir / ".git").exists()


def test_git_add_commit_returns_false_when_no_changes(git_repo: Path):
    assert sync_config.git_add_commit(git_repo, "test commit") is False


def test_git_status_summary_counts_local_changes(git_repo: Path):
    file_path = git_repo / "demo.txt"
    file_path.write_text("v1\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "demo.txt"], cwd=git_repo, capture_output=True, check=True
    )
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=git_repo,
        capture_output=True,
        check=True,
    )

    file_path.write_text("v2\n", encoding="utf-8")
    summary = sync_config.git_status_summary(git_repo)

    assert summary["local_changes"] >= 1
    assert summary["behind_count"] == 0


def test_generate_sync_commit_message_has_required_format(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(sync_config, "get_hostname", lambda: "test-host")
    monkeypatch.setattr(sync_config, "get_timestamp", lambda: "2026-02-13-2115")

    assert (
        sync_config.generate_sync_commit_message() == "sync: test-host 2026-02-13-2115"
    )

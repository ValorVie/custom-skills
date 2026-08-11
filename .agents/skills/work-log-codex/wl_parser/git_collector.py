"""Collect git commit evidence for work-log summaries."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import datetime


_STAT_SUMMARY_RE = re.compile(
    r"(\d+) files? changed"
    r"(?:,\s*(\d+) insertions?\(\+\))?"
    r"(?:,\s*(\d+) deletions?\(-\))?"
)


def _get_git_author(project_path: str) -> str | None:
    """Return local git user.name when available."""
    try:
        result = subprocess.run(
            ["git", "-C", project_path, "config", "--local", "user.name"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    author = result.stdout.strip()
    return author or None


def _parse_commit_list(raw: str) -> list[dict[str, str]]:
    commits: list[dict[str, str]] = []
    if not raw.strip():
        return commits
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\x00")
        if len(parts) != 4:
            continue
        commits.append(
            {
                "full_hash": parts[0].strip(),
                "hash": parts[1].strip(),
                "message": parts[2].strip(),
                "date": parts[3].strip(),
            }
        )
    return commits


def _parse_show_output(raw: str) -> tuple[list[str], int, int, int]:
    files: list[str] = []
    files_changed = 0
    insertions = 0
    deletions = 0

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = _STAT_SUMMARY_RE.search(stripped)
        if match:
            files_changed = int(match.group(1))
            insertions = int(match.group(2) or 0)
            deletions = int(match.group(3) or 0)
            continue
        if stripped.startswith(
            ("commit ", "Author:", "AuthorDate:", "Date:", "Commit:", "CommitDate:")
        ):
            continue
        if stripped.startswith("@@"):
            continue
        if "|" in stripped:
            continue
        if stripped.startswith(("diff --git", "---", "+++")):
            continue
        if stripped not in files:
            files.append(stripped)

    return files, files_changed, insertions, deletions


def _run_git(
    project_path: str, args: list[str], timeout: int = 10
) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", "-C", project_path, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def collect_git_data(
    project_path: str,
    start: datetime,
    end: datetime,
    max_commits: int = 50,
) -> list[dict]:
    """Collect commit messages, stats, and touched files for a git repo."""
    if not project_path:
        return []
    git_dir = os.path.join(project_path, ".git")
    if not os.path.isdir(git_dir):
        return []

    args = [
        "log",
        f"-{max_commits}",
        "--format=%H%x00%h%x00%s%x00%ai",
        f"--after={start.isoformat()}",
        f"--before={end.isoformat()}",
    ]
    author = _get_git_author(project_path)
    if author:
        args.append(f"--author={author}")

    result = _run_git(project_path, args)
    if result is None:
        return []
    if result.returncode != 0:
        print(
            f"Warning: git log failed in {project_path}: {result.stderr.strip()}",
            file=sys.stderr,
        )
        return []

    commits = _parse_commit_list(result.stdout)
    enriched: list[dict] = []
    for commit in commits:
        show = _run_git(
            project_path,
            ["show", "--stat", "--name-only", "--format=fuller", commit["full_hash"]],
            timeout=15,
        )
        files: list[str] = []
        files_changed = 0
        insertions = 0
        deletions = 0
        if show and show.returncode == 0:
            files, files_changed, insertions, deletions = _parse_show_output(show.stdout)
        enriched.append(
            {
                **commit,
                "files_changed": files_changed,
                "insertions": insertions,
                "deletions": deletions,
                "files": files,
            }
        )
    return enriched

"""Collect git commit data from project repositories."""

import os
import re
import subprocess
import sys
from datetime import datetime


def _get_git_author(project_path: str) -> str | None:
    """Get git user.name from repo config. Returns None if not available."""
    try:
        result = subprocess.run(
            ["git", "-C", project_path, "config", "--local", "user.name"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


_STAT_SUMMARY_RE = re.compile(
    r"(\d+) files? changed"
    r"(?:,\s*(\d+) insertions?\(\+\))?"
    r"(?:,\s*(\d+) deletions?\(-\))?"
)


def _parse_git_log_output(raw: str) -> list[dict]:
    """Parse output of git log --format='%H%x00%h%x00%s%x00%ai' --stat."""
    if not raw.strip():
        return []

    commits = []
    current_commit = None

    for line in raw.split("\n"):
        stripped = line.strip()

        if "\x00" in line:
            parts = line.split("\x00", 3)
            if len(parts) == 4:
                if current_commit:
                    commits.append(current_commit)
                current_commit = {
                    "full_hash": parts[0].strip(),
                    "hash": parts[1].strip(),
                    "message": parts[2].strip(),
                    "date": parts[3].strip(),
                    "files_changed": 0,
                    "insertions": 0,
                    "deletions": 0,
                }
                continue
        line = stripped

        if current_commit and "file" in line and "changed" in line:
            m = _STAT_SUMMARY_RE.search(line)
            if m:
                current_commit["files_changed"] = int(m.group(1))
                current_commit["insertions"] = int(m.group(2) or 0)
                current_commit["deletions"] = int(m.group(3) or 0)

    if current_commit:
        commits.append(current_commit)

    return commits


def collect_git_data(
    project_path: str,
    start: datetime,
    end: datetime,
    max_commits: int = 50,
) -> list[dict]:
    """Collect git commits from a project repo within time range."""
    git_dir = os.path.join(project_path, ".git")
    if not os.path.isdir(git_dir):
        return []

    author = _get_git_author(project_path)
    cmd = [
        "git", "-C", project_path, "log",
        f"-{max_commits}",
        "--format=%H%x00%h%x00%s%x00%ai",
        "--stat",
        f"--after={start.isoformat()}",
        f"--before={end.isoformat()}",
    ]
    if author:
        cmd.append(f"--author={author}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print(f"Warning: git log failed in {project_path}: {result.stderr.strip()}", file=sys.stderr)
            return []
        return _parse_git_log_output(result.stdout)
    except subprocess.TimeoutExpired:
        print(f"Warning: git log timed out in {project_path}", file=sys.stderr)
        return []
    except FileNotFoundError:
        return []

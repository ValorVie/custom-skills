#!/usr/bin/env python3
"""
SessionEnd Hook - Record structured facts when session ends

Cross-platform (Windows, macOS, Linux)

Runs when Claude session ends. Records git changes, modified files,
commit history, and working directory state to a .tmp session file.
"""

import sys
import re
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import (
    get_sessions_dir,
    get_date_string,
    get_time_string,
    get_project_name,
    is_git_repo,
    run_git_command,
    ensure_dir,
    read_file,
    write_file,
    log
)


def _collect_git_diff_stat(max_lines: int = 50) -> str:
    """Collect git diff --stat output."""
    result = run_git_command(['diff', '--stat', 'HEAD'])
    if result is None:
        return '[無法取得]'
    if not result:
        return 'clean'
    lines = result.split('\n')
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [f'... (truncated, {len(lines)} total lines)']
    return '\n'.join(lines)


def _collect_modified_files() -> str:
    """Collect modified files with status labels."""
    result = run_git_command(['diff', '--name-status', 'HEAD'])
    if result is None:
        return '[無法取得]'
    if not result:
        return '無'

    status_map = {
        'A': '新增', 'M': '修改', 'D': '刪除',
        'R': '重命名', 'C': '複製', 'T': '類型變更',
    }
    lines = []
    for line in result.split('\n'):
        if not line.strip():
            continue
        parts = line.split('\t', 1)
        if len(parts) >= 2:
            status_code = parts[0][0] if parts[0] else '?'
            filepath = parts[1]
            status_label = status_map.get(status_code, status_code)
            lines.append(f'- {filepath} ({status_label})')
        else:
            lines.append(f'- {line}')
    return '\n'.join(lines) if lines else '無'


def _collect_commits(started_time: str, today: str, max_count: int = 20) -> str:
    """Collect commits made during this session."""
    since = f'{today}T{started_time}:00'
    result = run_git_command([
        'log', '--oneline', f'--since={since}', f'-{max_count}'
    ])
    if result is None:
        return '[無法取得]'
    if not result:
        return '無'
    lines = [f'- {line}' for line in result.split('\n') if line.strip()]
    return '\n'.join(lines) if lines else '無'


def _collect_working_dir_status() -> str:
    """Collect git status --porcelain output."""
    result = run_git_command(['status', '--porcelain'])
    if result is None:
        return '[無法取得]'
    if not result:
        return 'clean'
    lines = [f'- {line}' for line in result.split('\n') if line.strip()]
    return '\n'.join(lines)


def _get_started_time(session_file: Path) -> str:
    """Extract the Started time from an existing session file."""
    content = read_file(session_file)
    if content:
        match = re.search(r'\*\*Started:\*\*\s*(\d{2}:\d{2})', content)
        if match:
            return match.group(1)
    return get_time_string()


def main():
    sessions_dir = get_sessions_dir()
    today = get_date_string()
    session_file = sessions_dir / f'{today}-session.tmp'

    ensure_dir(sessions_dir)

    current_time = get_time_string()
    project_name = get_project_name() or '(unknown)'
    in_git = is_git_repo()

    # Get started time from existing file or use current time
    if session_file.exists():
        started_time = _get_started_time(session_file)
    else:
        started_time = current_time

    # Collect structured facts
    if in_git:
        diff_stat = _collect_git_diff_stat()
        modified_files = _collect_modified_files()
        commits = _collect_commits(started_time, today)
        working_status = _collect_working_dir_status()
    else:
        not_applicable = '不適用'
        diff_stat = not_applicable
        modified_files = not_applicable
        commits = not_applicable
        working_status = not_applicable
        project_name = f'{project_name} (非 git 專案)'

    # Build session content
    content = f"""# Session: {today}
**Date:** {today}
**Project:** {project_name}
**Started:** {started_time}
**Last Updated:** {current_time}

---

## Git 變更摘要
{diff_stat}

## 修改的檔案
{modified_files}

## Commit 記錄
{commits}

## 工作目錄狀態
{working_status}
"""

    # Preserve existing compaction notes if file already exists
    existing_content = read_file(session_file)
    if existing_content:
        # Extract compaction entries
        compaction_entries = re.findall(
            r'\n---\n\*\*\[Compaction.*?\n(?:工作目錄:.*?\n)?(?:.*?\n)*?',
            existing_content
        )
        if compaction_entries:
            content += '\n'.join(compaction_entries)

    write_file(session_file, content)
    log(f'[SessionEnd] Recorded session facts: {session_file}')

    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'[SessionEnd] Error: {e}', file=sys.stderr)
        sys.exit(0)  # Don't block on errors

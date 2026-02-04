#!/usr/bin/env python3
"""
PreCompact Hook - Save git state snapshot before context compaction

Cross-platform (Windows, macOS, Linux)

Runs before Claude compacts context. Saves git status and diff stat
to the session file so working progress survives compaction.
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import (
    get_sessions_dir,
    get_datetime_string,
    get_time_string,
    is_git_repo,
    run_git_command,
    find_files,
    ensure_dir,
    append_file,
    log
)


def _collect_compact_snapshot() -> str:
    """Collect git state for the compaction snapshot."""
    if not is_git_repo():
        return '(非 git 專案)'

    # git status summary
    status_output = run_git_command(['status', '--porcelain'])
    if status_output is None:
        status_summary = '[無法取得]'
    elif not status_output:
        status_summary = 'clean'
    else:
        file_count = len([line for line in status_output.split('\n') if line.strip()])
        status_summary = f'{file_count} 個檔案有變更'

    # git diff stat (max 20 lines)
    diff_stat = run_git_command(['diff', '--stat', 'HEAD'])
    if diff_stat is None:
        diff_stat = '[無法取得]'
    elif not diff_stat:
        diff_stat = ''
    else:
        lines = diff_stat.split('\n')
        if len(lines) > 20:
            lines = lines[:20] + ['...']
        diff_stat = '\n'.join(lines)

    result = f'工作目錄: {status_summary}'
    if diff_stat:
        result += f'\n{diff_stat}'
    return result


def main():
    sessions_dir = get_sessions_dir()
    compaction_log = sessions_dir / 'compaction-log.txt'

    ensure_dir(sessions_dir)

    # Log compaction event with timestamp
    timestamp = get_datetime_string()
    append_file(compaction_log, f'[{timestamp}] Context compaction triggered\n')

    # If there's an active session file, append snapshot
    sessions = find_files(sessions_dir, '*.tmp')

    if sessions:
        active_session = Path(sessions[0]['path'])
        time_str = get_time_string()
        snapshot = _collect_compact_snapshot()
        append_file(
            active_session,
            f'\n---\n**[Compaction at {time_str}]**\n{snapshot}\n'
        )

    log('[PreCompact] State saved before compaction')
    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'[PreCompact] Error: {e}', file=sys.stderr)
        sys.exit(0)

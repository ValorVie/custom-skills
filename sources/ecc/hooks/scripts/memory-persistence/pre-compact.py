#!/usr/bin/env python3
"""
PreCompact Hook - Save state before context compaction

Upstream: everything-claude-code
Source URL: https://github.com/anthropics/everything-claude-code
Synced Date: 2026-01-24
License: MIT

Cross-platform (Windows, macOS, Linux)

Runs before Claude compacts context, giving you a chance to
preserve important state that might get lost in summarization.
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import (
    get_sessions_dir,
    get_datetime_string,
    get_time_string,
    find_files,
    ensure_dir,
    append_file,
    log
)


def main():
    sessions_dir = get_sessions_dir()
    compaction_log = sessions_dir / 'compaction-log.txt'

    ensure_dir(sessions_dir)

    # Log compaction event with timestamp
    timestamp = get_datetime_string()
    append_file(compaction_log, f'[{timestamp}] Context compaction triggered\n')

    # If there's an active session file, note the compaction
    sessions = find_files(sessions_dir, '*.tmp')

    if sessions:
        active_session = Path(sessions[0]['path'])
        time_str = get_time_string()
        append_file(
            active_session,
            f'\n---\n**[Compaction occurred at {time_str}]** - Context was summarized\n'
        )

    log('[PreCompact] State saved before compaction')
    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'[PreCompact] Error: {e}', file=sys.stderr)
        sys.exit(0)

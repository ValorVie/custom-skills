#!/usr/bin/env python3
"""
Stop Hook (Session End) - Persist learnings when session ends

Upstream: everything-claude-code
Source URL: https://github.com/anthropics/everything-claude-code
Synced Date: 2026-01-24
License: MIT

Cross-platform (Windows, macOS, Linux)

Runs when Claude session ends. Creates/updates session log file
with timestamp for continuity tracking.
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
    ensure_dir,
    read_file,
    write_file,
    replace_in_file,
    log
)


def main():
    sessions_dir = get_sessions_dir()
    today = get_date_string()
    session_file = sessions_dir / f'{today}-session.tmp'

    ensure_dir(sessions_dir)

    current_time = get_time_string()

    # If session file exists for today, update the end time
    if session_file.exists():
        success = replace_in_file(
            session_file,
            re.compile(r'\*\*Last Updated:\*\*.*'),
            f'**Last Updated:** {current_time}'
        )

        if success:
            log(f'[SessionEnd] Updated session file: {session_file}')
    else:
        # Create new session file with template
        template = f"""# Session: {today}
**Date:** {today}
**Started:** {current_time}
**Last Updated:** {current_time}

---

## Current State

[Session context goes here]

### Completed
- [ ]

### In Progress
- [ ]

### Notes for Next Session
-

### Context to Load
```
[relevant files]
```
"""
        write_file(session_file, template)
        log(f'[SessionEnd] Created session file: {session_file}')

    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'[SessionEnd] Error: {e}', file=sys.stderr)
        sys.exit(0)

#!/usr/bin/env python3
"""
Strategic Compact Suggester

Upstream: everything-claude-code
Source URL: https://github.com/anthropics/everything-claude-code
Synced Date: 2026-01-24
License: MIT

Cross-platform (Windows, macOS, Linux)

Runs on PreToolUse or periodically to suggest manual compaction at logical intervals

Why manual over auto-compact:
- Auto-compact happens at arbitrary points, often mid-task
- Strategic compacting preserves context through logical phases
- Compact after exploration, before execution
- Compact after completing a milestone, before starting next
"""

import os
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import (
    get_temp_dir,
    get_project_name,
    read_file,
    write_file,
    log
)


def main():
    # Track tool call count (increment in a temp file)
    # Use a session-specific counter file based on session ID from environment
    session_id = os.environ.get('CLAUDE_SESSION_ID') or get_project_name() or 'default'
    counter_file = get_temp_dir() / f'claude-tool-count-{session_id}'
    threshold = int(os.environ.get('COMPACT_THRESHOLD', '50'))

    count = 1

    # Read existing count or start at 1
    existing = read_file(counter_file)
    if existing:
        try:
            count = int(existing.strip()) + 1
        except ValueError:
            count = 1

    # Save updated count
    write_file(counter_file, str(count))

    # Suggest compact after threshold tool calls
    if count == threshold:
        log(f'[StrategicCompact] {threshold} tool calls reached - consider /compact if transitioning phases')

    # Suggest at regular intervals after threshold
    if count > threshold and count % 25 == 0:
        log(f'[StrategicCompact] {count} tool calls - good checkpoint for /compact if context is stale')

    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'[StrategicCompact] Error: {e}', file=sys.stderr)
        sys.exit(0)

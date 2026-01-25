#!/usr/bin/env python3
"""
SessionStart Hook - Load previous context on new session

Upstream: everything-claude-code
Source URL: https://github.com/anthropics/everything-claude-code
Synced Date: 2026-01-24
License: MIT

Cross-platform (Windows, macOS, Linux)

Runs when a new Claude session starts. Checks for recent session
files and notifies Claude of available context to load.
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import (
    get_sessions_dir,
    get_learned_skills_dir,
    find_files,
    ensure_dir,
    log,
    detect_package_manager,
    get_selection_prompt
)


def main():
    sessions_dir = get_sessions_dir()
    learned_dir = get_learned_skills_dir()

    # Ensure directories exist
    ensure_dir(sessions_dir)
    ensure_dir(learned_dir)

    # Check for recent session files (last 7 days)
    recent_sessions = find_files(sessions_dir, '*.tmp', max_age=7)

    if recent_sessions:
        latest = recent_sessions[0]
        log(f"[SessionStart] Found {len(recent_sessions)} recent session(s)")
        log(f"[SessionStart] Latest: {latest['path']}")

    # Check for learned skills
    learned_skills = find_files(learned_dir, '*.md')

    if learned_skills:
        log(f"[SessionStart] {len(learned_skills)} learned skill(s) available in {learned_dir}")

    # Detect and report package manager
    pm = detect_package_manager()
    log(f"[SessionStart] Package manager: {pm['name']} ({pm['source']})")

    # If package manager was detected via fallback, show selection prompt
    if pm['source'] in ('fallback', 'default'):
        log('[SessionStart] No package manager preference found.')
        log(get_selection_prompt())

    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'[SessionStart] Error: {e}', file=sys.stderr)
        sys.exit(0)  # Don't block on errors

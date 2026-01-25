#!/usr/bin/env python3
"""
Continuous Learning - Session Evaluator

Upstream: everything-claude-code
Source URL: https://github.com/anthropics/everything-claude-code
Synced Date: 2026-01-24
License: MIT

Cross-platform (Windows, macOS, Linux)

Runs on Stop hook to extract reusable patterns from Claude Code sessions

Why Stop hook instead of UserPromptSubmit:
- Stop runs once at session end (lightweight)
- UserPromptSubmit runs every message (heavy, adds latency)
"""

import os
import sys
import json
import re
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import (
    get_learned_skills_dir,
    ensure_dir,
    read_file,
    count_in_file,
    log
)


def main():
    # Get plugin root directory to find config
    plugin_root = Path(__file__).parent.parent.parent
    config_file = plugin_root.parent / 'skills' / 'continuous-learning' / 'config.json'

    # Default configuration
    min_session_length = 10
    learned_skills_path = get_learned_skills_dir()

    # Load config if exists
    config_content = read_file(config_file)
    if config_content:
        try:
            config = json.loads(config_content)
            min_session_length = config.get('min_session_length', 10)

            if config.get('learned_skills_path'):
                # Handle ~ in path
                path_str = config['learned_skills_path']
                if path_str.startswith('~'):
                    path_str = str(Path.home()) + path_str[1:]
                learned_skills_path = Path(path_str)
        except json.JSONDecodeError:
            pass  # Invalid config, use defaults

    # Ensure learned skills directory exists
    ensure_dir(learned_skills_path)

    # Get transcript path from environment (set by Claude Code)
    transcript_path = os.environ.get('CLAUDE_TRANSCRIPT_PATH')

    if not transcript_path or not Path(transcript_path).exists():
        sys.exit(0)

    # Count user messages in session
    transcript_file = Path(transcript_path)
    message_count = count_in_file(transcript_file, re.compile(r'"type":"user"'))

    # Skip short sessions
    if message_count < min_session_length:
        log(f'[ContinuousLearning] Session too short ({message_count} messages), skipping')
        sys.exit(0)

    # Signal to Claude that session should be evaluated for extractable patterns
    log(f'[ContinuousLearning] Session has {message_count} messages - evaluate for extractable patterns')
    log(f'[ContinuousLearning] Save learned skills to: {learned_skills_path}')

    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'[ContinuousLearning] Error: {e}', file=sys.stderr)
        sys.exit(0)

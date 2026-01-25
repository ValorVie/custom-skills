# Claude Code Hooks (Python Implementation)

<!--
Upstream: everything-claude-code
Source URL: https://github.com/anthropics/everything-claude-code
Synced Date: 2026-01-24
License: MIT
-->

Cross-platform Python hooks for Claude Code, providing memory persistence and strategic context management.

## Overview

These hooks extend Claude Code with:
- **Memory Persistence** - Save and restore session context across sessions
- **Strategic Compact** - Intelligent suggestions for when to compact context
- **Continuous Learning** - Extract reusable patterns from sessions

## Installation

1. Copy the `hooks/` directory to your Claude Code plugin root
2. Merge `hooks.json` with your Claude Code hooks configuration
3. Ensure Python 3.8+ is available in your PATH

### Merging hooks.json

Add the hooks from `hooks.json` to your Claude Code settings:

```bash
# macOS/Linux
~/.claude/settings.json

# Windows
%USERPROFILE%\.claude\settings.json
```

Or merge into your project-specific `.claude/settings.json`.

## Hooks

### Memory Persistence Hooks

Located in `memory-persistence/`:

| Hook | Event | Description |
|------|-------|-------------|
| `session-start.py` | SessionStart | Load previous session context, detect package manager |
| `session-end.py` | SessionEnd | Save session state for next time |
| `pre-compact.py` | PreCompact | Preserve state before context compaction |
| `evaluate-session.py` | SessionEnd | Analyze session for extractable patterns |

### Strategic Compact Hooks

Located in `strategic-compact/`:

| Hook | Event | Description |
|------|-------|-------------|
| `suggest-compact.py` | PreToolUse | Suggest manual compaction at logical intervals |

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `COMPACT_THRESHOLD` | 50 | Tool calls before suggesting compact |
| `CLAUDE_PACKAGE_MANAGER` | (auto) | Force specific package manager |
| `CLAUDE_SESSION_ID` | (auto) | Session identifier for tracking |
| `CLAUDE_TRANSCRIPT_PATH` | (auto) | Path to session transcript |

### Package Manager Detection

The hooks automatically detect your package manager in this order:
1. `CLAUDE_PACKAGE_MANAGER` environment variable
2. Project `.claude/package-manager.json`
3. `package.json` `packageManager` field
4. Lock file detection (pnpm-lock.yaml, yarn.lock, etc.)
5. Global `~/.claude/package-manager.json`
6. First available in PATH

## Session Storage

Session files are stored in:
- Project-specific: `.claude/sessions/`
- Global: `~/.claude/sessions/`

Files:
- `YYYY-MM-DD-session.tmp` - Daily session context
- `compaction-log.txt` - History of context compactions

## Cross-Platform Support

All hooks use:
- `pathlib` for path handling
- Standard library only (no external dependencies)
- Platform-agnostic file operations

Tested on:
- Windows 10/11
- macOS 12+
- Ubuntu 20.04+

## Troubleshooting

### Hooks not running

1. Check Python is in PATH: `python --version`
2. Verify hooks.json is merged correctly
3. Check hook file permissions (executable on Unix)

### Session files not created

1. Check write permissions on `~/.claude/sessions/`
2. Verify directory exists: `mkdir -p ~/.claude/sessions`

### Package manager not detected

Set explicitly:
```bash
export CLAUDE_PACKAGE_MANAGER=pnpm
```

Or create `~/.claude/package-manager.json`:
```json
{"packageManager": "pnpm"}
```

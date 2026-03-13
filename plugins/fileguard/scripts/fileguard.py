"""FileGuard - Path-based access control for Claude Code.

Intercepts PreToolUse events and evaluates file paths against
firewall-style rules (first-match-wins) to allow or deny access.
"""
import json
import os
import re
import sys

# Tools that use file_path field
FILE_PATH_TOOLS = ("Read", "Write", "Edit")
# Tools that use path field (optional, falls back to cwd)
SEARCH_PATH_TOOLS = ("Grep", "Glob")


def extract_paths(tool_name: str, tool_input: dict, cwd: str) -> list[str]:
    """Extract file paths from tool input.

    Returns a list of paths to check. For Bash, returns the raw command
    string (not a real path). Returns empty list if no path found.
    """
    if tool_name in FILE_PATH_TOOLS:
        path = tool_input.get("file_path", "")
        return [path] if path else []

    if tool_name in SEARCH_PATH_TOOLS:
        path = tool_input.get("path", "") or cwd
        return [path] if path else []

    if tool_name == "Bash":
        command = tool_input.get("command", "")
        return [command] if command else []

    return []

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


def normalize_path(path: str, cwd: str) -> str:
    """Normalize a file path for consistent matching.

    - Joins relative paths with cwd
    - Resolves ../, symlinks via realpath
    - Lowercases for macOS case-insensitive comparison
    """
    if not os.path.isabs(path):
        path = os.path.join(cwd, path)
    path = os.path.realpath(path)
    return path.lower()


def match_rules(
    path: str,
    rules: list[dict],
    default: str,
    is_bash: bool,
) -> tuple[str, str | None]:
    """Evaluate path against firewall rules (first-match-wins).

    Args:
        path: Normalized path (non-Bash) or raw command string (Bash).
        rules: List of rule dicts with action/pattern/type/reason.
        default: Default action if no rule matches ("allow" or "deny").
        is_bash: True if evaluating a Bash command string.

    Returns:
        (action, reason) tuple. reason is None if default was used.
    """
    for rule in rules:
        action = rule["action"]
        pattern = rule["pattern"]
        rule_type = rule["type"]
        reason = rule.get("reason", "")

        if _matches(path, pattern, rule_type, is_bash):
            return (action, reason)

    return (default, None)


def _matches(path: str, pattern: str, rule_type: str, is_bash: bool) -> bool:
    """Check if a single rule matches the path."""
    if is_bash:
        command_lower = path.lower()
        pattern_lower = pattern.lower()
        if rule_type in ("directory", "file"):
            return pattern_lower in command_lower
        if rule_type == "regex":
            return bool(re.search(pattern, path, re.IGNORECASE))
    else:
        if rule_type == "directory":
            return path.startswith(pattern.lower())
        if rule_type == "file":
            return path == pattern.lower()
        if rule_type == "regex":
            return bool(re.search(pattern, path, re.IGNORECASE))
    return False


DISABLE_FLAG = ".disable-fileguard"


def check_hardcoded_protection(
    tool_name: str, tool_input: dict, plugin_root: str
) -> bool:
    """Check if tool call targets hardcoded protected files.

    Protected:
    - .disable-fileguard (anywhere)
    - Entire ${CLAUDE_PLUGIN_ROOT} directory

    Returns True if access should be denied.
    """
    plugin_root_lower = plugin_root.lower()

    if tool_name in FILE_PATH_TOOLS:
        fp = tool_input.get("file_path", "").lower()
        if DISABLE_FLAG in fp:
            return True
        if fp.startswith(plugin_root_lower):
            return True

    elif tool_name in SEARCH_PATH_TOOLS:
        path = tool_input.get("path", "").lower()
        pattern = tool_input.get("pattern", "").lower()
        for val in (path, pattern):
            if DISABLE_FLAG in val:
                return True
            if val.startswith(plugin_root_lower):
                return True

    elif tool_name == "Bash":
        command = tool_input.get("command", "").lower()
        if DISABLE_FLAG in command:
            return True
        if plugin_root_lower in command:
            return True

    return False

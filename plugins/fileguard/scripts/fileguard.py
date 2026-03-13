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


def make_deny_output(path: str, reason: str) -> str:
    """Build JSON output for rule-based deny."""
    return json.dumps({
        "hookSpecificOutput": {"permissionDecision": "deny"},
        "systemMessage": f"[FileGuard] \U0001f6ab 存取被拒絕\n路徑: {path}\n規則: {reason}",
    })


def make_hardcoded_deny_output() -> str:
    """Build JSON output for hardcoded protection deny."""
    return json.dumps({
        "hookSpecificOutput": {"permissionDecision": "deny"},
        "systemMessage": "[FileGuard] \U0001f512 系統保護檔案，禁止存取",
    })


def make_rules_error_output() -> str:
    """Build JSON output when rules file is missing or invalid."""
    return json.dumps({
        "hookSpecificOutput": {"permissionDecision": "deny"},
        "systemMessage": (
            "[FileGuard] \u26a0\ufe0f fileguard-rules.json 不存在或格式錯誤，"
            "所有路徑存取被拒絕。請手動建立規則檔或 touch .disable-fileguard 停用保護。"
        ),
    })


def load_rules(plugin_root: str) -> tuple[list[dict], str] | None:
    """Load rules from fileguard-rules.json.

    Returns (rules, default) or None if load fails.
    """
    rules_path = os.path.join(plugin_root, "fileguard-rules.json")
    try:
        with open(rules_path, "r") as f:
            data = json.load(f)
        return data["rules"], data.get("default", "allow")
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None


def main() -> None:
    """Main entry point — reads stdin, evaluates rules, outputs decision."""
    # Parse stdin
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    cwd = data.get("cwd", "")
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")

    # Hardcoded protection (cannot be bypassed)
    if check_hardcoded_protection(tool_name, tool_input, plugin_root):
        print(make_hardcoded_deny_output())
        sys.exit(2)

    # Check disable flag
    if os.path.exists(os.path.join(cwd, DISABLE_FLAG)):
        sys.exit(0)

    # Load rules
    rules_data = load_rules(plugin_root)
    if rules_data is None:
        print(make_rules_error_output())
        sys.exit(2)
    rules, default = rules_data

    # Extract paths
    paths = extract_paths(tool_name, tool_input, cwd)
    if not paths:
        sys.exit(0)

    is_bash = tool_name == "Bash"

    for path in paths:
        check_path = path if is_bash else normalize_path(path, cwd)
        action, reason = match_rules(check_path, rules, default, is_bash)
        if action == "deny":
            display_path = path if is_bash else tool_input.get("file_path", path)
            print(make_deny_output(display_path, reason or "Default deny"))
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()

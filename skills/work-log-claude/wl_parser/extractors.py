# wl_parser/extractors.py
"""Heuristic extractors for work log analysis."""

import re
from collections import Counter


def extract_commits(record: dict) -> list:
    """Extract git commit messages from an assistant record's tool_use blocks.

    Looks for Bash tool_use blocks where input.command contains 'git commit'.
    Handles both simple -m "msg" and heredoc $(cat <<'EOF'...) styles.

    Returns list of commit message strings.
    """
    if record.get("type") != "assistant":
        return []

    message = record.get("message", {})
    content = message.get("content", [])
    if not isinstance(content, list):
        return []

    commits = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "tool_use" or block.get("name") != "Bash":
            continue

        command = block.get("input", {}).get("command", "")
        if "git commit" not in command:
            continue

        # Try heredoc style with escaped newlines: git commit -m "$(cat <<'EOF'\nmsg\nEOF\n)"
        heredoc_match = re.search(
            r"cat\s*<<['\"]?EOF['\"]?\s*\\n(.+?)\\n.*?EOF",
            command, re.DOTALL
        )
        if heredoc_match:
            msg = heredoc_match.group(1).split("\\n")[0].strip()
            commits.append(msg)
            continue

        # Try heredoc style with real newlines (alternate serialization)
        heredoc_match2 = re.search(
            r"cat\s*<<['\"]?EOF['\"]?\s*\n(.+?)\n.*?EOF",
            command, re.DOTALL
        )
        if heredoc_match2:
            msg = heredoc_match2.group(1).split("\n")[0].strip()
            commits.append(msg)
            continue

        # Try simple style: git commit -m "message" or git commit -m 'message'
        simple_match = re.search(r'git commit\s+-m\s+["\']([^"\']+)["\']', command)
        if simple_match:
            msg = simple_match.group(1).split("\n")[0].strip()
            commits.append(msg)

    return commits


COMPLETION_KEYWORDS = re.compile(r"完成|done|已提交|已完成|committed|finished", re.IGNORECASE)
WRITE_TOOLS = {"Write", "Edit"}


def extract_first_prompt(records: list, max_length: int = 200) -> str | None:
    """Extract the first user prompt that is a plain string (not a tool_result).

    Skips XML-like system tags (e.g., <local-command-caveat>, <command-message>).
    Truncates to first line and max_length characters.
    """
    for r in records:
        if r.get("type") != "user":
            continue
        content = r.get("message", {}).get("content")
        if isinstance(content, str) and content.strip():
            first_line = content.strip().split("\n")[0].strip()
            # Skip XML-like system tags
            if first_line.startswith("<"):
                continue
            if len(first_line) > max_length:
                return first_line[:max_length] + "…"
            return first_line
    return None


def extract_files_changed(records: list) -> list:
    """Extract unique file paths from Write/Edit tool_use blocks."""
    files = set()
    for r in records:
        if r.get("type") != "assistant":
            continue
        for block in r.get("message", {}).get("content", []):
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") in WRITE_TOOLS:
                path = block.get("input", {}).get("file_path")
                if path:
                    files.add(path)
    return sorted(files)


def extract_tool_usage(records: list) -> dict:
    """Count tool_use invocations by tool name."""
    counter: Counter = Counter()
    for r in records:
        if r.get("type") != "assistant":
            continue
        for block in r.get("message", {}).get("content", []):
            if isinstance(block, dict) and block.get("type") == "tool_use":
                name = block.get("name", "unknown")
                counter[name] += 1
    return dict(counter)


def extract_tokens(records: list) -> dict:
    """Sum token usage across all assistant records."""
    totals = {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0}
    for r in records:
        if r.get("type") != "assistant":
            continue
        usage = r.get("message", {}).get("usage", {})
        totals["input"] += usage.get("input_tokens", 0)
        totals["output"] += usage.get("output_tokens", 0)
        totals["cache_creation"] += usage.get("cache_creation_input_tokens", 0)
        totals["cache_read"] += usage.get("cache_read_input_tokens", 0)
    return totals


def _last_record_is_assistant(records: list) -> bool:
    """Check if the last processable record is an assistant message."""
    for r in reversed(records):
        if r.get("type") in ("user", "assistant"):
            return r["type"] == "assistant"
    return False


def detect_session_status(records: list, duration_minutes: int = 0) -> str:
    """Detect session status: 'completed', 'in_progress', or 'abandoned'.

    Priority rules:
    1. Has git commit → completed
    2. Last assistant has completion keyword → completed
    3. tool_use >= 5 AND last record is assistant → completed
    4. tool_use > 0 OR duration > 2min → in_progress
    5. Otherwise → abandoned
    """
    # Rule 1: git commit
    for r in records:
        if extract_commits(r):
            return "completed"

    # Rule 2: completion keywords in last assistant
    for r in reversed(records):
        if r.get("type") != "assistant":
            continue
        for block in r.get("message", {}).get("content", []):
            if isinstance(block, dict) and block.get("type") == "text":
                if COMPLETION_KEYWORDS.search(block.get("text", "")):
                    return "completed"
        break  # Only check the last assistant record

    # Rule 3: significant tool usage + natural ending
    tool_count = sum(extract_tool_usage(records).values())
    if tool_count >= 5 and _last_record_is_assistant(records):
        return "completed"

    # Rule 4: some activity
    if tool_count > 0 or duration_minutes > 2:
        return "in_progress"

    # Rule 5: abandoned
    return "abandoned"

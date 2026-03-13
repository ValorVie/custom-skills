# FileGuard Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code plugin that blocks AI access to protected file paths via PreToolUse hooks with firewall-style rules.

**Architecture:** A single Python script (`fileguard.py`, pure stdlib) receives tool call JSON via stdin, extracts paths from tool inputs, normalizes them, then evaluates against a firewall rule list (first-match-wins). Hardcoded self-protection prevents AI from disabling the guard.

**Tech Stack:** Python 3 (stdlib only: `json`, `os`, `os.path`, `re`, `sys`), Claude Code plugin hooks

**Spec:** `docs/superpowers/specs/2026-03-13-fileguard-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `plugins/fileguard/.claude-plugin/plugin.json` | Plugin metadata |
| `plugins/fileguard/hooks/hooks.json` | Hook configuration — PreToolUse matcher |
| `plugins/fileguard/scripts/fileguard.py` | Core interception logic |
| `plugins/fileguard/fileguard-rules.json` | Default rule set (example) |
| `plugins/fileguard/README.md` | Usage docs, known limitations |
| `tests/test_fileguard.py` | Unit tests |

---

## Chunk 1: Core Engine

### Task 1: Plugin scaffold

**Files:**
- Create: `plugins/fileguard/.claude-plugin/plugin.json`
- Create: `plugins/fileguard/hooks/hooks.json`
- Create: `plugins/fileguard/fileguard-rules.json`

- [ ] **Step 1: Create plugin.json**

```json
{
  "name": "fileguard",
  "version": "1.0.0",
  "description": "FileGuard - Path-based access control for Claude Code",
  "author": {
    "name": "custom-skills",
    "email": "valorlove@gmail.com"
  },
  "homepage": "https://github.com/ValorVie/custom-skills",
  "repository": "https://github.com/ValorVie/custom-skills",
  "license": "MIT",
  "keywords": ["hooks", "security", "path-guard", "access-control"]
}
```

- [ ] **Step 2: Create hooks.json**

```json
{
  "description": "FileGuard - Path-based access control for Claude Code",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read|Write|Edit|Grep|Glob|Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/fileguard.py\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 3: Create default fileguard-rules.json**

```json
{
  "rules": [
    {
      "action": "deny",
      "pattern": "\\.env($|\\.)",
      "type": "regex",
      "reason": "Environment secrets"
    },
    {
      "action": "deny",
      "pattern": "\\.pem$",
      "type": "regex",
      "reason": "Certificate private keys"
    }
  ],
  "default": "allow"
}
```

- [ ] **Step 4: Commit scaffold**

```bash
git add plugins/fileguard/.claude-plugin/plugin.json plugins/fileguard/hooks/hooks.json plugins/fileguard/fileguard-rules.json
git commit -m "功能(fileguard): 建立 plugin 骨架"
```

---

### Task 2: Path extraction helpers — tests

**Files:**
- Create: `tests/test_fileguard.py`

- [ ] **Step 1: Write tests for path extraction from each tool type**

```python
"""Tests for fileguard path extraction and matching."""
import json
import os
import sys
import unittest

# Add scripts dir to path for import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'plugins', 'fileguard', 'scripts'))
import fileguard


class TestExtractPaths(unittest.TestCase):
    """Test extract_paths() for each tool type."""

    def test_read_extracts_file_path(self):
        tool_input = {"file_path": "/Users/arlen/.ssh/id_rsa"}
        paths = fileguard.extract_paths("Read", tool_input, "/home")
        self.assertEqual(paths, ["/Users/arlen/.ssh/id_rsa"])

    def test_write_extracts_file_path(self):
        tool_input = {"file_path": "/tmp/output.txt"}
        paths = fileguard.extract_paths("Write", tool_input, "/home")
        self.assertEqual(paths, ["/tmp/output.txt"])

    def test_edit_extracts_file_path(self):
        tool_input = {"file_path": "/etc/config.json"}
        paths = fileguard.extract_paths("Edit", tool_input, "/home")
        self.assertEqual(paths, ["/etc/config.json"])

    def test_grep_extracts_path(self):
        tool_input = {"pattern": "secret", "path": "/Users/arlen/.ssh"}
        paths = fileguard.extract_paths("Grep", tool_input, "/home")
        self.assertEqual(paths, ["/Users/arlen/.ssh"])

    def test_grep_falls_back_to_cwd(self):
        tool_input = {"pattern": "secret"}
        paths = fileguard.extract_paths("Grep", tool_input, "/Users/arlen/project")
        self.assertEqual(paths, ["/Users/arlen/project"])

    def test_glob_extracts_path(self):
        tool_input = {"pattern": "*.py", "path": "/Users/arlen/code"}
        paths = fileguard.extract_paths("Glob", tool_input, "/home")
        self.assertEqual(paths, ["/Users/arlen/code"])

    def test_glob_falls_back_to_cwd(self):
        tool_input = {"pattern": "**/*.txt"}
        paths = fileguard.extract_paths("Glob", tool_input, "/Users/arlen/project")
        self.assertEqual(paths, ["/Users/arlen/project"])

    def test_bash_returns_command_string(self):
        tool_input = {"command": "cat /Users/arlen/.ssh/id_rsa"}
        paths = fileguard.extract_paths("Bash", tool_input, "/home")
        self.assertEqual(paths, ["cat /Users/arlen/.ssh/id_rsa"])

    def test_missing_file_path_returns_empty(self):
        tool_input = {"some_other_field": "value"}
        paths = fileguard.extract_paths("Read", tool_input, "/home")
        self.assertEqual(paths, [])

    def test_missing_bash_command_returns_empty(self):
        tool_input = {}
        paths = fileguard.extract_paths("Bash", tool_input, "/home")
        self.assertEqual(paths, [])
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills
python3 -m pytest tests/test_fileguard.py -v
```

Expected: `ModuleNotFoundError: No module named 'fileguard'`

- [ ] **Step 3: Commit test file**

```bash
git add tests/test_fileguard.py
git commit -m "測試(fileguard): 新增路徑提取單元測試"
```

---

### Task 3: Path extraction helpers — implementation

**Files:**
- Create: `plugins/fileguard/scripts/fileguard.py`

- [ ] **Step 1: Implement extract_paths()**

```python
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
```

- [ ] **Step 2: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_fileguard.py::TestExtractPaths -v
```

Expected: all 10 tests PASS

- [ ] **Step 3: Commit**

```bash
git add plugins/fileguard/scripts/fileguard.py
git commit -m "功能(fileguard): 實作路徑提取函式"
```

---

### Task 4: Path normalization — tests

**Files:**
- Modify: `tests/test_fileguard.py`

- [ ] **Step 1: Add normalization tests**

Append to `tests/test_fileguard.py`:

```python
class TestNormalizePath(unittest.TestCase):
    """Test normalize_path() for various edge cases."""

    def test_absolute_path_unchanged(self):
        result = fileguard.normalize_path("/Users/arlen/file.txt", "/home")
        # realpath resolves symlinks; result should be lowercase
        self.assertEqual(result, os.path.realpath("/Users/arlen/file.txt").lower())

    def test_relative_path_joined_with_cwd(self):
        result = fileguard.normalize_path("sub/file.txt", "/Users/arlen/project")
        expected = os.path.realpath("/Users/arlen/project/sub/file.txt").lower()
        self.assertEqual(result, expected)

    def test_dot_dot_resolved(self):
        result = fileguard.normalize_path("/Users/arlen/project/../.ssh/id_rsa", "/home")
        expected = os.path.realpath("/Users/arlen/.ssh/id_rsa").lower()
        self.assertEqual(result, expected)

    def test_case_normalized_to_lower(self):
        result = fileguard.normalize_path("/Users/Arlen/.SSH/ID_RSA", "/home")
        self.assertTrue(result.islower() or result == result.lower())
```

- [ ] **Step 2: Run to verify fail**

```bash
python3 -m pytest tests/test_fileguard.py::TestNormalizePath -v
```

Expected: `AttributeError: module 'fileguard' has no attribute 'normalize_path'`

- [ ] **Step 3: Commit**

```bash
git add tests/test_fileguard.py
git commit -m "測試(fileguard): 新增路徑正規化測試"
```

---

### Task 5: Path normalization — implementation

**Files:**
- Modify: `plugins/fileguard/scripts/fileguard.py`

- [ ] **Step 1: Implement normalize_path()**

Add to `fileguard.py` after `extract_paths`:

```python
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
```

- [ ] **Step 2: Run tests**

```bash
python3 -m pytest tests/test_fileguard.py::TestNormalizePath -v
```

Expected: all 4 tests PASS

- [ ] **Step 3: Commit**

```bash
git add plugins/fileguard/scripts/fileguard.py
git commit -m "功能(fileguard): 實作路徑正規化"
```

---

### Task 6: Firewall rule matching — tests

**Files:**
- Modify: `tests/test_fileguard.py`

- [ ] **Step 1: Add rule matching tests**

Append to `tests/test_fileguard.py`:

```python
class TestMatchRules(unittest.TestCase):
    """Test match_rules() firewall logic (first-match-wins)."""

    def _make_rules(self, *rule_tuples):
        """Helper: (action, pattern, type, reason) -> rules list."""
        return [
            {"action": a, "pattern": p, "type": t, "reason": r}
            for a, p, t, r in rule_tuples
        ]

    def test_directory_deny(self):
        rules = self._make_rules(("deny", "/users/arlen/.ssh", "directory", "SSH"))
        result = fileguard.match_rules("/users/arlen/.ssh/id_rsa", rules, "allow", is_bash=False)
        self.assertEqual(result, ("deny", "SSH"))

    def test_directory_allow(self):
        rules = self._make_rules(("allow", "/users/arlen/.config/claude", "directory", "Claude"))
        result = fileguard.match_rules("/users/arlen/.config/claude/settings.json", rules, "deny", is_bash=False)
        self.assertEqual(result, ("allow", "Claude"))

    def test_file_exact_match(self):
        rules = self._make_rules(("deny", "/users/arlen/secrets.txt", "file", "Secrets"))
        result = fileguard.match_rules("/users/arlen/secrets.txt", rules, "allow", is_bash=False)
        self.assertEqual(result, ("deny", "Secrets"))

    def test_file_no_partial_match(self):
        rules = self._make_rules(("deny", "/users/arlen/secrets.txt", "file", "Secrets"))
        result = fileguard.match_rules("/users/arlen/secrets.txt.bak", rules, "allow", is_bash=False)
        self.assertEqual(result, ("allow", None))

    def test_regex_match(self):
        rules = self._make_rules(("deny", r"\.env($|\.)", "regex", "Env"))
        result = fileguard.match_rules("/users/arlen/project/.env", rules, "allow", is_bash=False)
        self.assertEqual(result, ("deny", "Env"))

    def test_regex_env_local(self):
        rules = self._make_rules(("deny", r"\.env($|\.)", "regex", "Env"))
        result = fileguard.match_rules("/users/arlen/project/.env.local", rules, "allow", is_bash=False)
        self.assertEqual(result, ("deny", "Env"))

    def test_first_match_wins(self):
        rules = self._make_rules(
            ("allow", "/users/arlen/.config/claude", "directory", "Claude OK"),
            ("deny", "/users/arlen/.config", "directory", "Config blocked"),
        )
        # .config/claude matches allow first
        result = fileguard.match_rules("/users/arlen/.config/claude/settings.json", rules, "deny", is_bash=False)
        self.assertEqual(result, ("allow", "Claude OK"))
        # .config/other matches deny second
        result = fileguard.match_rules("/users/arlen/.config/other/file", rules, "deny", is_bash=False)
        self.assertEqual(result, ("deny", "Config blocked"))

    def test_no_match_uses_default_allow(self):
        rules = self._make_rules(("deny", "/secret", "directory", "Secret"))
        result = fileguard.match_rules("/users/arlen/public/file.txt", rules, "allow", is_bash=False)
        self.assertEqual(result, ("allow", None))

    def test_no_match_uses_default_deny(self):
        rules = self._make_rules(("allow", "/safe", "directory", "Safe"))
        result = fileguard.match_rules("/users/arlen/other/file.txt", rules, "deny", is_bash=False)
        self.assertEqual(result, ("deny", None))

    def test_bash_directory_substring(self):
        rules = self._make_rules(("deny", "/users/arlen/.ssh", "directory", "SSH"))
        result = fileguard.match_rules("cat /users/arlen/.ssh/id_rsa", rules, "allow", is_bash=True)
        self.assertEqual(result, ("deny", "SSH"))

    def test_bash_file_substring(self):
        rules = self._make_rules(("deny", "/users/arlen/secrets.txt", "file", "Secrets"))
        result = fileguard.match_rules("cat /users/arlen/secrets.txt", rules, "allow", is_bash=True)
        self.assertEqual(result, ("deny", "Secrets"))

    def test_bash_regex(self):
        rules = self._make_rules(("deny", r"\.env($|\.| )", "regex", "Env"))
        result = fileguard.match_rules("cat /project/.env", rules, "allow", is_bash=True)
        self.assertEqual(result, ("deny", "Env"))

    def test_bash_case_insensitive(self):
        rules = self._make_rules(("deny", "/users/arlen/.ssh", "directory", "SSH"))
        result = fileguard.match_rules("cat /Users/Arlen/.SSH/id_rsa", rules, "allow", is_bash=True)
        self.assertEqual(result, ("deny", "SSH"))

    def test_empty_rules_uses_default(self):
        result = fileguard.match_rules("/any/path", [], "allow", is_bash=False)
        self.assertEqual(result, ("allow", None))

    def test_rule_missing_reason_field(self):
        rules = [{"action": "deny", "pattern": "/secret", "type": "directory"}]
        result = fileguard.match_rules("/secret/file", rules, "allow", is_bash=False)
        self.assertEqual(result, ("deny", ""))

    def test_unknown_rule_type_skipped(self):
        rules = [{"action": "deny", "pattern": "/secret", "type": "unknown", "reason": "?"}]
        result = fileguard.match_rules("/secret/file", rules, "allow", is_bash=False)
        self.assertEqual(result, ("allow", None))
```

- [ ] **Step 2: Run to verify fail**

```bash
python3 -m pytest tests/test_fileguard.py::TestMatchRules -v
```

Expected: `AttributeError: module 'fileguard' has no attribute 'match_rules'`

- [ ] **Step 3: Commit**

```bash
git add tests/test_fileguard.py
git commit -m "測試(fileguard): 新增防火牆規則匹配測試"
```

---

### Task 7: Firewall rule matching — implementation

**Files:**
- Modify: `plugins/fileguard/scripts/fileguard.py`

- [ ] **Step 1: Implement match_rules()**

Add to `fileguard.py`:

```python
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
```

- [ ] **Step 2: Run tests**

```bash
python3 -m pytest tests/test_fileguard.py::TestMatchRules -v
```

Expected: all 14 tests PASS

- [ ] **Step 3: Commit**

```bash
git add plugins/fileguard/scripts/fileguard.py
git commit -m "功能(fileguard): 實作防火牆規則匹配引擎"
```

---

## Chunk 2: Hardcoded Protection & Main Entry

### Task 8: Hardcoded self-protection — tests

**Files:**
- Modify: `tests/test_fileguard.py`

- [ ] **Step 1: Add hardcoded protection tests**

Append to `tests/test_fileguard.py`:

```python
class TestHardcodedProtection(unittest.TestCase):
    """Test check_hardcoded_protection() blocks access to guard files."""

    def setUp(self):
        self.plugin_root = "/path/to/plugins/fileguard"

    def test_blocks_read_disable_fileguard(self):
        tool_input = {"file_path": "/Users/arlen/project/.disable-fileguard"}
        result = fileguard.check_hardcoded_protection("Read", tool_input, self.plugin_root)
        self.assertTrue(result)

    def test_blocks_write_disable_fileguard(self):
        tool_input = {"file_path": "/Users/arlen/project/.disable-fileguard"}
        result = fileguard.check_hardcoded_protection("Write", tool_input, self.plugin_root)
        self.assertTrue(result)

    def test_blocks_bash_rm_disable_fileguard(self):
        tool_input = {"command": "rm .disable-fileguard"}
        result = fileguard.check_hardcoded_protection("Bash", tool_input, self.plugin_root)
        self.assertTrue(result)

    def test_blocks_bash_touch_disable_fileguard(self):
        tool_input = {"command": "touch /project/.disable-fileguard"}
        result = fileguard.check_hardcoded_protection("Bash", tool_input, self.plugin_root)
        self.assertTrue(result)

    def test_blocks_read_plugin_root_file(self):
        tool_input = {"file_path": f"{self.plugin_root}/scripts/fileguard.py"}
        result = fileguard.check_hardcoded_protection("Read", tool_input, self.plugin_root)
        self.assertTrue(result)

    def test_blocks_edit_hooks_json(self):
        tool_input = {"file_path": f"{self.plugin_root}/hooks/hooks.json"}
        result = fileguard.check_hardcoded_protection("Edit", tool_input, self.plugin_root)
        self.assertTrue(result)

    def test_blocks_grep_plugin_root(self):
        tool_input = {"pattern": "secret", "path": self.plugin_root}
        result = fileguard.check_hardcoded_protection("Grep", tool_input, self.plugin_root)
        self.assertTrue(result)

    def test_blocks_bash_cat_plugin_file(self):
        tool_input = {"command": f"cat {self.plugin_root}/fileguard-rules.json"}
        result = fileguard.check_hardcoded_protection("Bash", tool_input, self.plugin_root)
        self.assertTrue(result)

    def test_allows_unrelated_path(self):
        tool_input = {"file_path": "/Users/arlen/project/main.py"}
        result = fileguard.check_hardcoded_protection("Read", tool_input, self.plugin_root)
        self.assertFalse(result)

    def test_allows_unrelated_bash(self):
        tool_input = {"command": "ls /Users/arlen/project"}
        result = fileguard.check_hardcoded_protection("Bash", tool_input, self.plugin_root)
        self.assertFalse(result)

    def test_blocks_mixed_case_plugin_root(self):
        tool_input = {"file_path": self.plugin_root.upper() + "/scripts/fileguard.py"}
        result = fileguard.check_hardcoded_protection("Read", tool_input, self.plugin_root)
        self.assertTrue(result)

    def test_blocks_glob_pattern_with_plugin_root(self):
        tool_input = {"pattern": f"{self.plugin_root}/**/*.json"}
        result = fileguard.check_hardcoded_protection("Glob", tool_input, self.plugin_root)
        self.assertTrue(result)
```

- [ ] **Step 2: Run to verify fail**

```bash
python3 -m pytest tests/test_fileguard.py::TestHardcodedProtection -v
```

Expected: `AttributeError: module 'fileguard' has no attribute 'check_hardcoded_protection'`

- [ ] **Step 3: Commit**

```bash
git add tests/test_fileguard.py
git commit -m "測試(fileguard): 新增硬編碼保護測試"
```

---

### Task 9: Hardcoded self-protection — implementation

**Files:**
- Modify: `plugins/fileguard/scripts/fileguard.py`

- [ ] **Step 1: Implement check_hardcoded_protection()**

Add to `fileguard.py`:

```python
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
    protected_keywords = [DISABLE_FLAG]
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
```

- [ ] **Step 2: Run tests**

```bash
python3 -m pytest tests/test_fileguard.py::TestHardcodedProtection -v
```

Expected: all 10 tests PASS

- [ ] **Step 3: Commit**

```bash
git add plugins/fileguard/scripts/fileguard.py
git commit -m "功能(fileguard): 實作硬編碼自我保護"
```

---

### Task 10: Output helpers — tests & implementation

**Files:**
- Modify: `tests/test_fileguard.py`
- Modify: `plugins/fileguard/scripts/fileguard.py`

- [ ] **Step 1: Add output tests**

Append to `tests/test_fileguard.py`:

```python
class TestOutputHelpers(unittest.TestCase):
    """Test JSON output formatting."""

    def test_deny_output(self):
        output = fileguard.make_deny_output("/path/to/file", "SSH keys")
        parsed = json.loads(output)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("SSH keys", parsed["systemMessage"])
        self.assertIn("/path/to/file", parsed["systemMessage"])

    def test_hardcoded_deny_output(self):
        output = fileguard.make_hardcoded_deny_output()
        parsed = json.loads(output)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("系統保護", parsed["systemMessage"])

    def test_rules_error_output(self):
        output = fileguard.make_rules_error_output()
        parsed = json.loads(output)
        self.assertEqual(parsed["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("fileguard-rules.json", parsed["systemMessage"])
        self.assertIn(".disable-fileguard", parsed["systemMessage"])
```

- [ ] **Step 2: Implement output helpers**

Add to `fileguard.py`:

```python
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
```

- [ ] **Step 3: Run tests**

```bash
python3 -m pytest tests/test_fileguard.py::TestOutputHelpers -v
```

Expected: all 3 tests PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_fileguard.py plugins/fileguard/scripts/fileguard.py
git commit -m "功能(fileguard): 實作輸出格式化函式"
```

---

### Task 11: Main entry point — tests

**Files:**
- Modify: `tests/test_fileguard.py`

- [ ] **Step 1: Add integration tests for main()**

Append to `tests/test_fileguard.py`:

```python
import subprocess
import tempfile
import shutil


class TestMainIntegration(unittest.TestCase):
    """Integration tests running fileguard.py as a subprocess."""

    SCRIPT_PATH = os.path.join(
        os.path.dirname(__file__), '..', 'plugins', 'fileguard', 'scripts', 'fileguard.py'
    )

    def setUp(self):
        """Create a temp dir with rules and plugin structure."""
        self.tmpdir = tempfile.mkdtemp()
        self.plugin_root = os.path.join(self.tmpdir, "plugins", "fileguard")
        os.makedirs(os.path.join(self.plugin_root, "scripts"), exist_ok=True)
        # Copy script
        shutil.copy2(self.SCRIPT_PATH, os.path.join(self.plugin_root, "scripts", "fileguard.py"))
        # Write rules
        rules = {
            "rules": [
                {"action": "allow", "pattern": "/safe/allowed", "type": "directory", "reason": "Allowed"},
                {"action": "deny", "pattern": "/safe", "type": "directory", "reason": "Blocked"},
                {"action": "deny", "pattern": r"\.env($|\.)", "type": "regex", "reason": "Env secrets"},
            ],
            "default": "allow",
        }
        self.rules_path = os.path.join(self.plugin_root, "fileguard-rules.json")
        with open(self.rules_path, "w") as f:
            json.dump(rules, f)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _run(self, tool_name, tool_input, cwd=None):
        """Run fileguard.py with given input, return (exit_code, stdout, stderr)."""
        stdin_data = json.dumps({
            "tool_name": tool_name,
            "tool_input": tool_input,
            "cwd": cwd or self.tmpdir,
        })
        env = os.environ.copy()
        env["CLAUDE_PLUGIN_ROOT"] = self.plugin_root
        result = subprocess.run(
            [sys.executable, self.SCRIPT_PATH],
            input=stdin_data,
            capture_output=True,
            text=True,
            env=env,
        )
        return result.returncode, result.stdout, result.stderr

    def test_deny_protected_path(self):
        code, stdout, _ = self._run("Read", {"file_path": "/safe/secret.txt"})
        self.assertEqual(code, 2)
        output = json.loads(stdout)
        self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_allow_allowed_path(self):
        code, stdout, _ = self._run("Read", {"file_path": "/safe/allowed/file.txt"})
        self.assertEqual(code, 0)

    def test_allow_unmatched_path(self):
        code, stdout, _ = self._run("Read", {"file_path": "/other/file.txt"})
        self.assertEqual(code, 0)

    def test_deny_env_file(self):
        code, stdout, _ = self._run("Read", {"file_path": "/project/.env"})
        self.assertEqual(code, 2)

    def test_deny_env_local(self):
        code, stdout, _ = self._run("Read", {"file_path": "/project/.env.local"})
        self.assertEqual(code, 2)

    def test_deny_bash_with_protected_path(self):
        code, stdout, _ = self._run("Bash", {"command": "cat /safe/secret.txt"})
        self.assertEqual(code, 2)

    def test_hardcoded_blocks_disable_flag(self):
        code, stdout, _ = self._run("Bash", {"command": "rm .disable-fileguard"})
        self.assertEqual(code, 2)
        output = json.loads(stdout)
        self.assertIn("系統保護", output["systemMessage"])

    def test_hardcoded_blocks_plugin_root(self):
        code, stdout, _ = self._run("Read", {"file_path": f"{self.plugin_root}/fileguard-rules.json"})
        self.assertEqual(code, 2)
        output = json.loads(stdout)
        self.assertIn("系統保護", output["systemMessage"])

    def test_disable_flag_skips_all(self):
        flag_path = os.path.join(self.tmpdir, ".disable-fileguard")
        open(flag_path, "w").close()
        code, stdout, _ = self._run("Read", {"file_path": "/safe/secret.txt"}, cwd=self.tmpdir)
        self.assertEqual(code, 0)
        os.remove(flag_path)

    def test_disable_flag_still_blocks_own_access(self):
        """Even with flag present, hardcoded protection still denies access to the flag itself."""
        flag_path = os.path.join(self.tmpdir, ".disable-fileguard")
        open(flag_path, "w").close()
        code, stdout, _ = self._run("Bash", {"command": "rm .disable-fileguard"}, cwd=self.tmpdir)
        self.assertEqual(code, 2)
        os.remove(flag_path)

    def test_invalid_json_stdin_allows(self):
        """Malformed stdin should exit 0 (allow)."""
        env = os.environ.copy()
        env["CLAUDE_PLUGIN_ROOT"] = self.plugin_root
        result = subprocess.run(
            [sys.executable, self.SCRIPT_PATH],
            input="not json",
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(result.returncode, 0)

    def test_missing_rules_file_denies_all(self):
        os.remove(self.rules_path)
        code, stdout, _ = self._run("Read", {"file_path": "/any/file.txt"})
        self.assertEqual(code, 2)
        output = json.loads(stdout)
        self.assertIn("fileguard-rules.json", output["systemMessage"])
```

- [ ] **Step 2: Run to verify fail**

```bash
python3 -m pytest tests/test_fileguard.py::TestMainIntegration -v
```

Expected: failures (main() not yet implemented)

- [ ] **Step 3: Commit**

```bash
git add tests/test_fileguard.py
git commit -m "測試(fileguard): 新增主流程整合測試"
```

---

### Task 12: Main entry point — implementation

**Files:**
- Modify: `plugins/fileguard/scripts/fileguard.py`

- [ ] **Step 1: Implement main()**

Add to `fileguard.py`:

```python
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
```

- [ ] **Step 2: Run all tests**

```bash
python3 -m pytest tests/test_fileguard.py -v
```

Expected: all tests PASS

- [ ] **Step 3: Commit**

```bash
git add plugins/fileguard/scripts/fileguard.py
git commit -m "功能(fileguard): 實作主進入點與規則載入"
```

---

## Chunk 3: Documentation & Final

### Task 13: README

**Files:**
- Create: `plugins/fileguard/README.md`

- [ ] **Step 1: Write README**

內容包含：
- 概述與安裝方式
- `fileguard-rules.json` 格式與欄位說明
- 防火牆模型（first-match-wins）說明與範例
- 停用機制（`.disable-fileguard`）
- 已知限制（Bash 攔截邊界、python3 前提、symlink 限制）
- 完整的「可攔截」與「無法攔截」範例清單

- [ ] **Step 2: Commit**

```bash
git add plugins/fileguard/README.md
git commit -m "文件(fileguard): 新增 README"
```

---

### Task 14: Full test run & final commit

- [ ] **Step 1: Run complete test suite**

```bash
python3 -m pytest tests/test_fileguard.py -v --tb=short
```

Expected: all tests PASS

- [ ] **Step 2: Manual smoke test in Claude Code**

```bash
claude --debug
```

Test sequence:
1. Try `Read` on a denied path → should see `[FileGuard] 🚫` message
2. Try `Read` on an allowed path → should proceed normally
3. Try `Bash` with `cat /denied/path` → should see deny
4. Try `Bash` with `rm .disable-fileguard` → should see `🔒` message

- [ ] **Step 3: Final commit**

```bash
git add -A plugins/fileguard/ tests/test_fileguard.py
git commit -m "功能(fileguard): FileGuard v1.0.0 — 路徑存取控制 plugin"
```

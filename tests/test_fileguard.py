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

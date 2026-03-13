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

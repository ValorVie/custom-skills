from __future__ import annotations

from pathlib import Path
import sys
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from wl_parser.git_collector import _parse_show_output  # noqa: E402


class GitCollectorTest(unittest.TestCase):
    def test_parse_show_output_ignores_commit_metadata_lines(self) -> None:
        raw = """commit abcdef1234567890
Author: Test User <test@example.com>
AuthorDate: Wed Mar 11 10:00:00 2026 +0800
Commit: Test User <test@example.com>
CommitDate: Wed Mar 11 10:05:00 2026 +0800

 parser.py | 10 ++++++++++
 tests/test_parser.py | 2 ++
 2 files changed, 12 insertions(+)

parser.py
tests/test_parser.py
"""
        files, files_changed, insertions, deletions = _parse_show_output(raw)
        self.assertEqual(files, ["parser.py", "tests/test_parser.py"])
        self.assertEqual(files_changed, 2)
        self.assertEqual(insertions, 12)
        self.assertEqual(deletions, 0)


if __name__ == "__main__":
    unittest.main()

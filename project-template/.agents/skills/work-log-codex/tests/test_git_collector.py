from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from wl_parser.git_collector import _parse_show_output, collect_git_data  # noqa: E402


class GitCollectorTest(unittest.TestCase):
    @patch("wl_parser.git_collector._get_git_author", return_value=None)
    @patch("wl_parser.git_collector._run_git")
    @patch("wl_parser.git_collector.os.path.isdir", return_value=True)
    def test_collect_git_data_requests_show_without_commit_header(
        self,
        _mock_isdir,
        mock_run_git,
        _mock_author,
    ) -> None:
        mock_run_git.side_effect = [
            subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="abc1234567890\x00abc1234\x00docs: report\x002026-03-11 10:00:00 +0800\n",
                stderr="",
            ),
            subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="docs/report.md\n",
                stderr="",
            ),
        ]

        commits = collect_git_data(
            "/repo/a",
            datetime(2026, 3, 11, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 3, 11, 23, 59, tzinfo=timezone.utc),
        )

        show_args = mock_run_git.call_args_list[1].args[1]
        self.assertIn("--format=", show_args)
        self.assertNotIn("--format=fuller", show_args)
        self.assertEqual(commits[0]["files"], ["docs/report.md"])

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

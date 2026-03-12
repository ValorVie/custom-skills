from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[4]
SKILL_ROOT = ROOT / ".codex/skills/work-log-codex"
FIXTURES = SKILL_ROOT / "tests/fixtures"
PARSER_MODULE = "wl_parser.work_log_parser"
WRAPPER_SCRIPT = SKILL_ROOT / "scripts/generate_work_log.py"


class CliSmokeTest(unittest.TestCase):
    def _run_parser(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            str(SKILL_ROOT)
            if not existing_pythonpath
            else f"{SKILL_ROOT}{os.pathsep}{existing_pythonpath}"
        )
        return subprocess.run(
            [sys.executable, "-m", PARSER_MODULE, *args],
            cwd=SKILL_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def _run_wrapper(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            str(SKILL_ROOT)
            if not existing_pythonpath
            else f"{SKILL_ROOT}{os.pathsep}{existing_pythonpath}"
        )
        return subprocess.run(
            [sys.executable, str(WRAPPER_SCRIPT), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def test_parser_help_exits_zero(self) -> None:
        result = self._run_parser("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Generate work log", result.stdout)

    def test_parser_cli_emits_project_level_json(self) -> None:
        result = self._run_parser(
            "2026-03-11",
            "--codex-home",
            str(FIXTURES / "codex_sample"),
            "--claude-home",
            str(FIXTURES / "claude_sample"),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        report = json.loads(result.stdout)
        self.assertIn("projects", report)
        self.assertIn("summary", report)
        self.assertIn("sessions", report)
        self.assertGreaterEqual(report["summary"]["project_count"], 2)

        project_names = {project["short_name"] for project in report["projects"].values()}
        self.assertIn("repo-a", project_names)
        self.assertIn("repo-b", project_names)

        repo_a = next(
            project for project in report["projects"].values() if project["short_name"] == "repo-a"
        )
        self.assertIn("session_hints", repo_a)
        self.assertIn("git_commits", repo_a)
        self.assertIn("duration_minutes", repo_a)

    def test_wrapper_emits_human_readable_report(self) -> None:
        result = self._run_wrapper(
            "--range",
            "2026-03-11",
            "--codex-home",
            str(FIXTURES / "codex_sample"),
            "--claude-home",
            str(FIXTURES / "claude_sample"),
            "--output-mode",
            "report-only",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("### 當日總結", result.stdout)
        self.assertIn("### 逐專案摘要", result.stdout)
        self.assertIn("### 工時統計", result.stdout)

    def test_wrapper_writes_report_and_appendix_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir)
            result = self._run_wrapper(
                "--range",
                "2026-03-11",
                "--codex-home",
                str(FIXTURES / "codex_sample"),
                "--claude-home",
                str(FIXTURES / "claude_sample"),
                "--mode",
                "report+appendix",
                "--output-mode",
                "write-only",
                "--output-root",
                str(output_root),
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            report_path = output_root / "2026-03-11.md"
            appendix_path = output_root / "2026-03-11.appendix.md"

            self.assertTrue(report_path.exists())
            self.assertTrue(appendix_path.exists())
            self.assertIn("### 當日總結", report_path.read_text(encoding="utf-8"))
            self.assertNotIn("### Token 消耗", report_path.read_text(encoding="utf-8"))
            self.assertIn("### 專案證據附錄", appendix_path.read_text(encoding="utf-8"))
            self.assertNotIn("### 工具使用", appendix_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

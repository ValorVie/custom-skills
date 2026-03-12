from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from source_claude import load_claude_events


class ClaudeSourceTest(unittest.TestCase):
    def test_uses_transcripts_and_history_project_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "transcripts").mkdir(parents=True)
            (root / "history.jsonl").write_text(
                "\n".join(
                    [
                        '{"display":"old prompt","timestamp":1759222794000,"project":"/repo/old"}',
                        '{"display":"daily report","timestamp":1759222794882,"project":"/repo/b"}',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            transcript_file = root / "transcripts/example.jsonl"
            transcript_file.write_text(
                "\n".join(
                    [
                        '{"type":"user","timestamp":"2026-02-06T07:24:57.012Z","content":"daily report"}',
                        '{"type":"assistant","timestamp":"2026-02-06T07:25:00.000Z","content":"summary line\\nmore detail"}',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            events = load_claude_events(root)

            self.assertEqual(len(events), 2)
            self.assertEqual(events[0]["tool"], "claude")
            self.assertEqual(events[0]["session_id"], "example")
            self.assertEqual(events[0]["project_path"], "/repo/b")
            self.assertIsNone(events[0]["cwd"])
            self.assertEqual(events[0]["event_type"], "user")
            self.assertEqual(events[0]["title"], "daily report")
            self.assertEqual(events[0]["text"], "daily report")
            self.assertEqual(events[0]["evidence_path"], str(transcript_file))
            self.assertEqual(events[0]["confidence"], "high")
            self.assertEqual(events[1]["title"], "summary line")
            self.assertEqual(events[1]["text"], "summary line\nmore detail")

    def test_falls_back_to_latest_history_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "transcripts").mkdir(parents=True)
            (root / "history.jsonl").write_text(
                "\n".join(
                    [
                        '{"display":"older","timestamp":1000,"project":"/repo/old"}',
                        '{"display":"newer","timestamp":2000,"project":"/repo/latest"}',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "transcripts/work-session.jsonl").write_text(
                '{"type":"user","timestamp":"2026-02-06T08:00:00.000Z","content":"unmatched content"}\n',
                encoding="utf-8",
            )

            events = load_claude_events(root)

            self.assertEqual(events[0]["session_id"], "work-session")
            self.assertEqual(events[0]["project_path"], "/repo/latest")
            self.assertEqual(events[0]["confidence"], "low")

    def test_uses_session_tmp_and_project_fallback_without_transcripts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "history.jsonl").write_text(
                '{"display":"newer","timestamp":2000,"project":"/repo/latest"}\n',
                encoding="utf-8",
            )
            (root / "sessions").mkdir(parents=True)
            (root / "sessions/2026-03-11-session.tmp").write_text(
                "\n".join(
                    [
                        "# Session: 2026-03-11",
                        "### Completed",
                        "- shipped daily report",
                        "### In Progress",
                        "- refine weekly rollup",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            project_dir = root / "projects/-Users-arlen"
            project_dir.mkdir(parents=True)
            (project_dir / "sample.jsonl").write_text(
                '{"sessionId":"fallback","cwd":"/repo/project-fallback","timestamp":"2026-03-11T12:00:00Z","type":"user","message":{"content":"project fallback note"}}\n',
                encoding="utf-8",
            )
            observer_dir = root / "projects/-Users-arlen--claude-mem-observer-sessions"
            observer_dir.mkdir(parents=True)
            (observer_dir / "ignored.jsonl").write_text(
                '{"sessionId":"ignored","cwd":"/repo/observer","timestamp":"2026-03-11T12:05:00Z","type":"user","message":{"content":"ignore me"}}\n',
                encoding="utf-8",
            )

            events = load_claude_events(root)

            self.assertEqual(len(events), 3)
            self.assertEqual(events[0]["event_type"], "session_note")
            self.assertEqual(events[0]["project_path"], "/repo/latest")
            self.assertEqual(events[0]["confidence"], "low")
            self.assertEqual(events[0]["title"], "Completed")
            self.assertEqual(events[0]["text"], "shipped daily report")
            self.assertEqual(events[1]["event_type"], "session_note")
            self.assertEqual(events[1]["title"], "In Progress")
            self.assertEqual(events[1]["text"], "refine weekly rollup")
            self.assertEqual(events[2]["project_path"], "/repo/project-fallback")
            self.assertEqual(events[2]["session_id"], "fallback")

    def test_project_fallback_reads_nested_message_content_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "history.jsonl").write_text(
                '{"display":"newer","timestamp":2000,"project":"/repo/latest"}\n',
                encoding="utf-8",
            )
            project_dir = root / "projects/-Users-arlen"
            project_dir.mkdir(parents=True)
            (project_dir / "sample.jsonl").write_text(
                '{"sessionId":"fallback","cwd":"/repo/project-fallback","timestamp":"2026-03-11T12:00:00Z","type":"assistant","message":{"content":[{"text":"project fallback note"}]}}\n',
                encoding="utf-8",
            )

            events = load_claude_events(root)

            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["text"], "project fallback note")
            self.assertEqual(events[0]["title"], "project fallback note")

    def test_tool_events_inherit_session_level_project_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "transcripts").mkdir(parents=True)
            (root / "history.jsonl").write_text(
                '{"display":"match me","timestamp":2000,"project":"/repo/matched"}\n',
                encoding="utf-8",
            )
            (root / "transcripts/work-session.jsonl").write_text(
                "\n".join(
                    [
                        '{"type":"user","timestamp":"2026-02-06T08:00:00.000Z","content":"match me"}',
                        '{"type":"tool_use","timestamp":"2026-02-06T08:01:00.000Z","tool_name":"bash","tool_input":{"command":"ls -la","description":"list files"}}',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            events = load_claude_events(root)

            self.assertEqual(events[0]["project_path"], "/repo/matched")
            self.assertEqual(events[1]["project_path"], "/repo/matched")
            self.assertEqual(events[1]["confidence"], "high")
            self.assertIn("ls -la", events[1]["text"])


if __name__ == "__main__":
    unittest.main()

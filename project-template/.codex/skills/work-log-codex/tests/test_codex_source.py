import tempfile
import unittest
from pathlib import Path
import sys


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from source_codex import load_codex_events


class CodexSourceTest(unittest.TestCase):
    def test_loads_session_meta_and_inherits_context_to_response_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_dir = root / "sessions/2026/03/11"
            session_dir.mkdir(parents=True)
            session_file = session_dir / "rollout-example.jsonl"
            session_file.write_text(
                "\n".join(
                    [
                        '{"timestamp":"2026-03-11T10:00:00Z","type":"session_meta","payload":{"id":"s1","cwd":"/repo/a"}}',
                        '{"timestamp":"2026-03-11T10:05:00Z","type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"finish api task"}]}}',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            events = load_codex_events(root)

            self.assertEqual(len(events), 2)

            meta, message = events

            self.assertEqual(meta["tool"], "codex")
            self.assertEqual(meta["session_id"], "s1")
            self.assertEqual(meta["project_path"], "/repo/a")
            self.assertEqual(meta["cwd"], "/repo/a")
            self.assertEqual(meta["event_type"], "session_meta")
            self.assertIsNone(meta["title"])
            self.assertIsNone(meta["text"])
            self.assertEqual(meta["confidence"], "high")
            self.assertFalse(meta["is_subagent"])
            self.assertEqual(meta["evidence_path"], str(session_file))

            self.assertEqual(message["tool"], "codex")
            self.assertEqual(message["session_id"], "s1")
            self.assertEqual(message["project_path"], "/repo/a")
            self.assertEqual(message["cwd"], "/repo/a")
            self.assertEqual(message["event_type"], "response_item")
            self.assertEqual(message["title"], "user")
            self.assertEqual(message["text"], "finish api task")
            self.assertEqual(message["confidence"], "high")
            self.assertFalse(message["is_subagent"])
            self.assertEqual(message["evidence_path"], str(session_file))
            self.assertEqual(message["raw"]["payload"]["role"], "user")

    def test_marks_subagent_threads_from_session_meta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_dir = root / "sessions/2026/03/11"
            session_dir.mkdir(parents=True)
            session_file = session_dir / "rollout-subagent.jsonl"
            session_file.write_text(
                "\n".join(
                    [
                        '{"timestamp":"2026-03-11T10:00:00Z","type":"session_meta","payload":{"id":"s-sub","cwd":"/repo/a","source":{"subagent":{"thread_spawn":{"parent_thread_id":"parent-1","depth":1}}}}}',
                        '{"timestamp":"2026-03-11T10:05:00Z","type":"response_item","payload":{"type":"message","role":"assistant","content":[{"type":"output_text","text":"investigation result"}]}}',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            events = load_codex_events(root)

            self.assertEqual(len(events), 2)
            self.assertTrue(events[0]["is_subagent"])
            self.assertTrue(events[1]["is_subagent"])

    def test_loads_history_and_index_when_session_streams_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "session_index.jsonl").write_text(
                '{"id":"idx-1","thread_name":"daily summary","updated_at":"2026-03-11T10:30:00Z"}\n',
                encoding="utf-8",
            )
            (root / "history.jsonl").write_text(
                '{"session_id":"idx-1","ts":1741657800,"text":"completed report"}\n',
                encoding="utf-8",
            )

            events = load_codex_events(root)

            self.assertEqual(len(events), 2)
            self.assertEqual(events[0]["event_type"], "session_index")
            self.assertEqual(events[0]["text"], "daily summary")
            self.assertEqual(events[0]["confidence"], "low")
            self.assertEqual(events[1]["event_type"], "history")
            self.assertEqual(events[1]["text"], "completed report")
            self.assertEqual(events[1]["confidence"], "low")


if __name__ == "__main__":
    unittest.main()

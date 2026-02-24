"""Tests for pulled hashes management."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from script.utils.mem_sync import append_pulled_hashes, load_pulled_hashes


def test_load_empty_when_file_missing():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pulled-hashes.txt"
        with patch("script.utils.mem_sync._get_pulled_hashes_path", return_value=path):
            hashes = load_pulled_hashes()
            assert hashes == set()


def test_append_and_load():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pulled-hashes.txt"
        with patch("script.utils.mem_sync._get_pulled_hashes_path", return_value=path):
            append_pulled_hashes(["abc123", "def456"])
            hashes = load_pulled_hashes()
            assert hashes == {"abc123", "def456"}


def test_append_is_additive():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pulled-hashes.txt"
        with patch("script.utils.mem_sync._get_pulled_hashes_path", return_value=path):
            append_pulled_hashes(["aaa"])
            append_pulled_hashes(["bbb"])
            hashes = load_pulled_hashes()
            assert hashes == {"aaa", "bbb"}


def test_load_ignores_blank_lines():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pulled-hashes.txt"
        path.write_text("abc\n\ndef\n\n", encoding="utf-8")
        with patch("script.utils.mem_sync._get_pulled_hashes_path", return_value=path):
            hashes = load_pulled_hashes()
            assert hashes == {"abc", "def"}

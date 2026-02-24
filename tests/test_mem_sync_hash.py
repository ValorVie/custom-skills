"""Tests for compute_content_hash."""

import re

from script.utils.mem_sync import compute_content_hash


def test_basic_hash():
    obs = {
        "title": "Test observation",
        "narrative": "This is a test",
        "facts": '["fact1"]',
        "project": "test-project",
        "type": "discovery",
    }

    value = compute_content_hash(obs)

    assert isinstance(value, str)
    assert len(value) == 32
    assert re.fullmatch(r"[0-9a-f]{32}", value)


def test_same_content_same_hash():
    obs1 = {"title": "A", "narrative": "B", "facts": "[]", "project": "p", "type": "t"}
    obs2 = {"title": "A", "narrative": "B", "facts": "[]", "project": "p", "type": "t"}

    assert compute_content_hash(obs1) == compute_content_hash(obs2)


def test_different_content_different_hash():
    obs1 = {"title": "A", "narrative": "B", "facts": "[]", "project": "p", "type": "t"}
    obs2 = {"title": "A", "narrative": "C", "facts": "[]", "project": "p", "type": "t"}

    assert compute_content_hash(obs1) != compute_content_hash(obs2)


def test_ignores_metadata_fields():
    base = {"title": "A", "narrative": "B", "facts": "[]", "project": "p", "type": "t"}
    with_meta = {
        **base,
        "id": 42,
        "memory_session_id": "ms-001",
        "created_at_epoch": 1234567890,
        "origin_device_id": 1,
    }

    assert compute_content_hash(base) == compute_content_hash(with_meta)


def test_missing_fields_default_to_empty():
    value = compute_content_hash({"title": "A"})

    assert len(value) == 32

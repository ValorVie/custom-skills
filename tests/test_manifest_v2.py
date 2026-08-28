"""manifest v2 schema 與 3-way 衝突分類的單元測試。"""

from pathlib import Path
from types import SimpleNamespace

import pytest

from script.utils import manifest as M
from script.utils import shared as S


def test_classify_no_base_when_entry_missing():
    assert M.classify_file(None, "src", "dst") == "no-base"


def test_classify_no_base_when_entry_empty_fields():
    fe = M.FileEntry(
        src_hash="", src_commit="", src_source="x",
        dst_hash_at_sync="", decision="accepted", decided_at="",
    )
    assert M.classify_file(fe, "a", "b") == "no-base"


def test_classify_clean_when_dst_unchanged_src_changed():
    fe = M.FileEntry(
        src_hash="S", src_commit="c", src_source="x",
        dst_hash_at_sync="D", decision="accepted", decided_at="",
    )
    assert M.classify_file(fe, "S2", "D") == "clean"


def test_classify_local_only_when_src_unchanged_dst_changed():
    fe = M.FileEntry(
        src_hash="S", src_commit="c", src_source="x",
        dst_hash_at_sync="D", decision="accepted", decided_at="",
    )
    assert M.classify_file(fe, "S", "D2") == "local-only"


def test_classify_both_changed():
    fe = M.FileEntry(
        src_hash="S", src_commit="c", src_source="x",
        dst_hash_at_sync="D", decision="accepted", decided_at="",
    )
    assert M.classify_file(fe, "S2", "D2") == "both-changed"


def test_classify_no_change_returns_clean():
    fe = M.FileEntry(
        src_hash="S", src_commit="c", src_source="x",
        dst_hash_at_sync="D", decision="accepted", decided_at="",
    )
    assert M.classify_file(fe, "S", "D") == "clean"


def test_v2_to_v1_view_strips_v2_fields():
    v2 = {
        "schema_version": 2,
        "version": "1.2.8",
        "managed_by": "ai-dev",
        "last_sync": "2026-05-08T10:00:00+08:00",
        "target": "claude",
        "last_sync_commit_by_source": {"custom-skills": "abc"},
        "files": {
            "skills": {
                "demo": {
                    "hash": "h1",
                    "source": "custom-skills",
                    "files": {"SKILL.md": {"src_hash": "x"}},
                }
            },
            "commands": {},
            "agents": {},
            "workflows": {},
        },
    }
    v1 = M.v2_to_v1_view(v2)
    assert v1["files"]["skills"] == {"demo": {"hash": "h1", "source": "custom-skills"}}
    assert "schema_version" not in v1
    assert "last_sync_commit_by_source" not in v1


def test_record_skip_and_is_skipped_lifecycle():
    m = {"schema_version": 2, "files": {"skills": {"demo": {}}}}
    M.record_skip(m, "skills", "demo", "SKILL.md", "abc")
    assert M.is_skipped(m, "skills", "demo", "SKILL.md", "abc") is True
    # 不同 src_commit 不命中
    assert M.is_skipped(m, "skills", "demo", "SKILL.md", "def") is False
    # clear
    M.clear_skip(m, "skills", "demo", "SKILL.md")
    assert M.is_skipped(m, "skills", "demo", "SKILL.md", "abc") is False


def test_record_file_decision_writes_entry_for_skill():
    m = {"schema_version": 2, "files": {"skills": {"demo": {}}}}
    M.record_file_decision(
        m, "skills", "demo", "SKILL.md",
        src_hash="S", src_commit="c", src_source="custom-skills",
        dst_hash="D", decision="accepted",
    )
    fe = M.get_file_entry(m, "skills", "demo", "SKILL.md")
    assert fe is not None
    assert fe.src_hash == "S"
    assert fe.dst_hash_at_sync == "D"
    assert fe.decision == "accepted"


def test_compute_skill_file_map_excludes_pycache(tmp_path: Path):
    skill = tmp_path / "demo"
    skill.mkdir()
    (skill / "SKILL.md").write_text("hi")
    expected_hash = M.compute_dir_hash(skill)
    (skill / "__pycache__").mkdir()
    (skill / "__pycache__" / "noise.pyc").write_text("x")
    (skill / ".DS_Store").write_bytes(b"Finder metadata")
    file_map = M.compute_skill_file_map(skill)
    assert "SKILL.md" in file_map
    assert all("__pycache__" not in k for k in file_map)
    assert ".DS_Store" not in file_map
    assert M.compute_dir_hash(skill) == expected_hash


def test_to_manifest_v2_shape(tmp_path: Path):
    skill = tmp_path / "demo"
    skill.mkdir()
    (skill / "SKILL.md").write_text("hi")
    t = M.ManifestTracker(target="claude")
    t.record_skill("demo", skill, source="custom-skills", src_path=skill)
    m = t.to_manifest("1.2.8")
    assert m["schema_version"] == 2
    assert "last_sync_commit_by_source" in m
    skill_block = m["files"]["skills"]["demo"]
    assert "hash" in skill_block
    assert skill_block["source"] == "custom-skills"


def test_migrate_to_v2_idempotent_on_v2_input():
    v2 = {"schema_version": 2, "files": {"skills": {}}}
    out = M.migrate_to_v2(v2, "claude")
    assert out is v2  # no-op


def test_prompt_file_decision_overwrite_via_uppercase(monkeypatch, tmp_path):
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    src.write_text("new")
    dst.write_text("old")
    monkeypatch.setattr("builtins.input", lambda *a, **k: "O")
    result = M.prompt_file_decision(
        skill_name="demo",
        rel_path="src.txt",
        src_path=src,
        dst_path=dst,
        base_blob_getter=lambda rel: b"base",
    )
    assert result == "overwrite"


def test_prompt_file_decision_skip_via_lowercase(monkeypatch, tmp_path):
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    src.write_text("new")
    dst.write_text("old")
    monkeypatch.setattr("builtins.input", lambda *a, **k: "s")
    result = M.prompt_file_decision(
        skill_name="demo",
        rel_path="src.txt",
        src_path=src,
        dst_path=dst,
        base_blob_getter=lambda rel: b"base",
    )
    assert result == "skip"


def test_prompt_file_decision_base_unavailable_eof_returns_skip(monkeypatch, tmp_path):
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    src.write_text("new")
    dst.write_text("old")
    def raiser(*a, **k):
        raise EOFError
    monkeypatch.setattr("builtins.input", raiser)
    result = M.prompt_file_decision(
        skill_name="demo",
        rel_path="src.txt",
        src_path=src,
        dst_path=dst,
        base_blob_getter=lambda rel: None,
    )
    assert result == "skip"


def test_clone_local_only_restore_reinstates_pre_copy_bytes(tmp_path: Path):
    destination = tmp_path / "SKILL.md"
    destination.write_bytes(b"upstream replacement")

    S._v2_restore_preserved({destination: b"local content"})

    assert destination.read_bytes() == b"local content"


def test_clone_decision_writeback_records_overwrite_and_skip():
    manifest = {"schema_version": 2, "files": {"skills": {}}}
    decisions = {"skip_set": {("skills", "demo", "keep.md", "source-commit")}}

    S._v2_apply_decisions(
        manifest,
        [
            (
                "skills",
                "demo",
                "replace.md",
                "source-hash",
                "source-commit",
                "custom-skills",
                "source-hash",
                "overwritten",
            )
        ],
        decisions,
    )

    entry = M.get_file_entry(manifest, "skills", "demo", "replace.md")
    assert entry is not None
    assert entry.decision == "overwritten"
    assert M.is_skipped(manifest, "skills", "demo", "keep.md", "source-commit")


def test_clone_no_base_skip_anchors_current_source_and_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    destination = tmp_path / "installed" / "demo" / "SKILL.md"
    destination.parent.mkdir(parents=True)
    destination.write_text("local", encoding="utf-8")
    source = tmp_path / "source" / "demo"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("upstream", encoding="utf-8")
    tracker = SimpleNamespace(
        skills={
            "demo": M.FileRecord(
                name="demo",
                hash="skill-hash",
                source="custom-skills",
                source_path=source,
                src_path=source,
                files={"SKILL.md": "source-hash"},
            )
        }
    )
    manifest = {"schema_version": 2, "files": {"skills": {}}}
    conflict = SimpleNamespace(resource_type="skills", name="demo")
    monkeypatch.setattr(S, "_v2_get_dst_path", lambda *_args: destination)
    monkeypatch.setattr(M, "get_file_commit", lambda *_args, **_kwargs: "source-commit")

    S._v2_anchor_no_base_skips(
        new_manifest=manifest,
        target="claude",
        prescan_tracker=tracker,
        no_base_conflicts=[conflict],
        skip_names={"demo"},
        source_heads={},
    )

    entry = M.get_file_entry(manifest, "skills", "demo", "SKILL.md")
    assert entry is not None
    assert entry.src_hash == "source-hash"
    assert entry.dst_hash_at_sync == M.compute_file_hash(destination)
    assert entry.decision == "skipped"


def test_cleanup_orphans_leaves_retired_auto_skill_for_confirmed_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    auto_skill = tmp_path / "auto-skill"
    auto_skill.mkdir()
    other = tmp_path / "other-skill"
    other.mkdir()

    monkeypatch.setattr(
        M,
        "_get_target_resource_path",
        lambda _target, _resource_type, name: tmp_path / name,
    )

    M.cleanup_orphans(
        "claude",
        {
            "skills": ["auto-skill", "other-skill"],
            "commands": [],
            "agents": [],
            "workflows": [],
        },
    )

    assert auto_skill.exists()
    assert not other.exists()

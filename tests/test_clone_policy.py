import json
from pathlib import Path

import script.utils.manifest as manifest
from script.utils import shared
from script.utils.manifest import ManifestTracker


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def test_load_clone_policy_valid(tmp_path: Path):
    skill_dir = tmp_path / "auto-skill"
    skill_dir.mkdir(parents=True)
    _write_json(
        skill_dir / ".clonepolicy.json",
        {
            "rules": [
                {"pattern": "*/_index.json", "strategy": "key-merge"},
                {"pattern": "knowledge-base/*.md", "strategy": "skip-if-exists"},
            ]
        },
    )

    policy = shared._load_clone_policy(skill_dir)

    assert policy is not None
    assert policy["rules"][0]["strategy"] == "key-merge"


def test_load_clone_policy_invalid_returns_none(tmp_path: Path):
    skill_dir = tmp_path / "bad-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / ".clonepolicy.json").write_text("{bad json", encoding="utf-8")

    assert shared._load_clone_policy(skill_dir) is None


def test_merge_index_json_keeps_existing_and_adds_new_entries(tmp_path: Path):
    src_file = tmp_path / "src" / "_index.json"
    dst_file = tmp_path / "dst" / "_index.json"

    _write_json(
        src_file,
        {
            "lastUpdated": "2026-02-13",
            "categories": [
                {"id": "workflow", "count": 0},
                {"id": "devops", "count": 0},
            ],
            "skills": [
                {"skillId": "skill-a", "count": 0},
                {"skillId": "skill-b", "count": 0},
            ],
        },
    )
    _write_json(
        dst_file,
        {
            "lastUpdated": "2026-01-01",
            "categories": [{"id": "workflow", "count": 2}],
            "skills": [{"skillId": "skill-a", "count": 5}],
        },
    )

    shared._merge_index_json(src_file, dst_file)
    merged = json.loads(dst_file.read_text(encoding="utf-8"))

    categories = {item["id"]: item for item in merged["categories"]}
    skills = {item["skillId"]: item for item in merged["skills"]}

    assert categories["workflow"]["count"] == 2
    assert "devops" in categories
    assert skills["skill-a"]["count"] == 5
    assert "skill-b" in skills


def test_copy_skill_with_policy_first_clone_copies_templates(tmp_path: Path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"

    _write_json(
        src / ".clonepolicy.json",
        {
            "rules": [
                {"pattern": "*/_index.json", "strategy": "key-merge"},
                {"pattern": "knowledge-base/*.md", "strategy": "skip-if-exists"},
                {"pattern": "experience/*.md", "strategy": "skip-if-exists"},
            ]
        },
    )
    (src / "SKILL.md").write_text("upstream\n", encoding="utf-8")
    _write_json(src / "knowledge-base" / "_index.json", {"categories": []})
    (src / "knowledge-base" / "workflow.md").write_text("template\n", encoding="utf-8")
    _write_json(src / "experience" / "_index.json", {"skills": []})
    (src / "experience" / "skill-x.md").write_text("template\n", encoding="utf-8")

    policy = shared._load_clone_policy(src)
    assert policy is not None

    shared._copy_skill_with_policy(
        src,
        dst,
        policy,
        force=False,
        skip_conflicts=False,
    )

    assert (dst / "SKILL.md").exists()
    assert (dst / "knowledge-base" / "workflow.md").exists()
    assert (dst / "experience" / "skill-x.md").exists()
    assert not (dst / ".clonepolicy.json").exists()


def test_copy_skill_with_policy_second_clone_preserves_user_data_and_merges_index(
    tmp_path: Path,
):
    src = tmp_path / "src"
    dst = tmp_path / "dst"

    _write_json(
        src / ".clonepolicy.json",
        {
            "rules": [
                {"pattern": "*/_index.json", "strategy": "key-merge"},
                {"pattern": "knowledge-base/*.md", "strategy": "skip-if-exists"},
            ]
        },
    )
    (src / "SKILL.md").write_text("upstream\n", encoding="utf-8")
    _write_json(
        src / "knowledge-base" / "_index.json",
        {
            "categories": [
                {"id": "workflow", "count": 0},
                {"id": "devops", "count": 0},
            ]
        },
    )
    (src / "knowledge-base" / "workflow.md").write_text("template\n", encoding="utf-8")

    dst.mkdir(parents=True)
    (dst / "SKILL.md").write_text("user custom\n", encoding="utf-8")
    (dst / "knowledge-base").mkdir(parents=True)
    (dst / "knowledge-base" / "workflow.md").write_text(
        "user content\n", encoding="utf-8"
    )
    _write_json(
        dst / "knowledge-base" / "_index.json",
        {"categories": [{"id": "workflow", "count": 2}]},
    )

    policy = shared._load_clone_policy(src)
    assert policy is not None

    shared._copy_skill_with_policy(
        src,
        dst,
        policy,
        force=False,
        skip_conflicts=True,
    )

    assert (dst / "knowledge-base" / "workflow.md").read_text(
        encoding="utf-8"
    ) == "user content\n"
    merged = json.loads(
        (dst / "knowledge-base" / "_index.json").read_text(encoding="utf-8")
    )
    categories = {item["id"]: item for item in merged["categories"]}
    assert categories["workflow"]["count"] == 2
    assert "devops" in categories
    assert (dst / "SKILL.md").read_text(encoding="utf-8") == "user custom\n"


def test_copy_skill_with_policy_force_overwrites_default_strategy(tmp_path: Path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir(parents=True)
    dst.mkdir(parents=True)

    (src / "SKILL.md").write_text("upstream\n", encoding="utf-8")
    (dst / "SKILL.md").write_text("user custom\n", encoding="utf-8")

    shared._copy_skill_with_policy(
        src,
        dst,
        {"rules": []},
        force=True,
        skip_conflicts=False,
    )

    assert (dst / "SKILL.md").read_text(encoding="utf-8") == "upstream\n"


def test_copy_with_log_passes_flags_to_policy_copy(tmp_path: Path, monkeypatch):
    src_root = tmp_path / "src" / "skills"
    dst_root = tmp_path / "dst" / "skills"
    src_root.mkdir(parents=True)
    dst_root.mkdir(parents=True)

    skill = src_root / "auto-skill"
    skill.mkdir(parents=True)
    _write_json(skill / ".clonepolicy.json", {"rules": []})

    called: dict[str, bool] = {}

    def _fake_copy(
        src: Path, dst: Path, policy: dict, force: bool, skip_conflicts: bool
    ):
        called["force"] = force
        called["skip_conflicts"] = skip_conflicts
        dst.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(shared, "_copy_skill_with_policy", _fake_copy)

    tracker = ManifestTracker(target="claude")
    shared._copy_with_log(
        src_root,
        dst_root,
        "skills",
        "Claude Code",
        tracker=tracker,
        force=True,
        skip_conflicts=False,
    )

    assert called == {"force": True, "skip_conflicts": False}


def test_copy_with_log_without_policy_keeps_copytree_behavior(tmp_path: Path):
    src_root = tmp_path / "src" / "skills"
    dst_root = tmp_path / "dst" / "skills"
    src_root.mkdir(parents=True)

    skill = src_root / "plain-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("hello\n", encoding="utf-8")

    tracker = ManifestTracker(target="claude")
    shared._copy_with_log(
        src_root,
        dst_root,
        "skills",
        "Claude Code",
        tracker=tracker,
    )

    assert (dst_root / "plain-skill" / "SKILL.md").exists()


def test_copy_with_log_invalid_policy_falls_back_to_copytree(tmp_path: Path):
    src_root = tmp_path / "src" / "skills"
    dst_root = tmp_path / "dst" / "skills"
    src_root.mkdir(parents=True)

    skill = src_root / "bad-policy"
    skill.mkdir(parents=True)
    (skill / ".clonepolicy.json").write_text("{bad json", encoding="utf-8")
    (skill / "SKILL.md").write_text("hello\n", encoding="utf-8")

    tracker = ManifestTracker(target="claude")
    shared._copy_with_log(
        src_root,
        dst_root,
        "skills",
        "Claude Code",
        tracker=tracker,
    )

    assert (dst_root / "bad-policy" / "SKILL.md").exists()
    assert (dst_root / "bad-policy" / ".clonepolicy.json").exists()


def test_conflict_prescan_skips_skill_with_valid_clone_policy(
    tmp_path: Path, monkeypatch
):
    custom_dir = tmp_path / "custom-skills"
    src_skills = custom_dir / "skills"
    src_skills.mkdir(parents=True)

    with_policy = src_skills / "auto-skill"
    with_policy.mkdir(parents=True)
    _write_json(with_policy / ".clonepolicy.json", {"rules": []})
    (with_policy / "SKILL.md").write_text("auto\n", encoding="utf-8")

    plain_skill = src_skills / "plain-skill"
    plain_skill.mkdir(parents=True)
    (plain_skill / "SKILL.md").write_text("plain\n", encoding="utf-8")

    empty = custom_dir / "commands"
    (empty / "claude").mkdir(parents=True)
    (empty / "antigravity").mkdir(parents=True)
    (empty / "opencode").mkdir(parents=True)
    (empty / "gemini").mkdir(parents=True)
    (empty / "workflows").mkdir(parents=True)
    (custom_dir / "agents" / "claude").mkdir(parents=True)
    (custom_dir / "agents" / "opencode").mkdir(parents=True)
    (custom_dir / "plugins" / "ecc-hooks-opencode").mkdir(parents=True)

    monkeypatch.setattr(shared, "get_custom_skills_dir", lambda: custom_dir)
    monkeypatch.setattr(shared, "_migrate_opencode_plugin_dir_if_needed", lambda: None)
    monkeypatch.setattr(shared, "_prescan_custom_repos", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        shared, "_distribute_custom_repos", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        shared, "_sync_to_project_directory", lambda *args, **kwargs: None
    )

    fake_targets = {
        "claude": {
            "skills": tmp_path / "targets" / "claude" / "skills",
            "commands": tmp_path / "targets" / "claude" / "commands",
            "agents": tmp_path / "targets" / "claude" / "agents",
            "workflows": tmp_path / "targets" / "claude" / "workflows",
        },
        "antigravity": {
            "skills": tmp_path / "targets" / "antigravity" / "skills",
            "workflows": tmp_path / "targets" / "antigravity" / "workflows",
        },
        "opencode": {
            "skills": tmp_path / "targets" / "opencode" / "skills",
            "commands": tmp_path / "targets" / "opencode" / "commands",
            "agents": tmp_path / "targets" / "opencode" / "agents",
            "plugins": tmp_path / "targets" / "opencode" / "plugins",
        },
        "codex": {
            "skills": tmp_path / "targets" / "codex" / "skills",
        },
        "gemini": {
            "skills": tmp_path / "targets" / "gemini" / "skills",
            "commands": tmp_path / "targets" / "gemini" / "commands",
        },
    }
    monkeypatch.setattr(shared, "COPY_TARGETS", fake_targets)

    captured_skill_sets: list[set[str]] = []

    monkeypatch.setattr(
        manifest, "read_manifest", lambda target: {"files": {"skills": {}}}
    )
    monkeypatch.setattr(manifest, "write_manifest", lambda target, data: None)
    monkeypatch.setattr(manifest, "display_conflicts", lambda conflicts: None)
    monkeypatch.setattr(
        manifest, "prompt_conflict_action", lambda conflicts=None: "skip"
    )
    monkeypatch.setattr(manifest, "show_conflict_diff", lambda conflicts: None)
    monkeypatch.setattr(
        manifest,
        "find_orphans",
        lambda old_manifest, new_manifest: {
            "skills": [],
            "commands": [],
            "agents": [],
            "workflows": [],
        },
    )
    monkeypatch.setattr(manifest, "cleanup_orphans", lambda target, orphans: None)
    monkeypatch.setattr(
        manifest, "backup_file", lambda target, resource_type, name: None
    )
    monkeypatch.setattr(manifest, "get_project_version", lambda: "1.0.0")

    def _fake_detect_conflicts(target, old_manifest, new_tracker):
        captured_skill_sets.append(set(new_tracker.skills.keys()))
        return []

    monkeypatch.setattr(manifest, "detect_conflicts", _fake_detect_conflicts)

    shared.copy_custom_skills_to_targets(sync_project=False)

    assert captured_skill_sets
    for skill_set in captured_skill_sets:
        assert "plain-skill" in skill_set
        assert "auto-skill" not in skill_set

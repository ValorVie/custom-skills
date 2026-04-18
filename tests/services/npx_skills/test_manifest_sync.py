from pathlib import Path
from unittest.mock import patch

import pytest

from script.services.npx_skills.manifest_sync import (
    cleanup_skills_from_manifests,
    get_npx_managed_skill_names,
)


def test_get_npx_managed_skill_names_reads_yaml(tmp_path: Path):
    yaml_file = tmp_path / "npx-skills.yaml"
    yaml_file.write_text(
        "version: 1\n"
        "packages:\n"
        "  - repo: a/b\n"
        "    skills: [alpha, beta]\n"
        "  - repo: c/d\n"
        "    skills: [gamma]\n"
    )

    names = get_npx_managed_skill_names(yaml_path=yaml_file)

    assert names == {"alpha", "beta", "gamma"}


def test_get_npx_managed_skill_names_missing_returns_empty(tmp_path: Path):
    assert get_npx_managed_skill_names(yaml_path=tmp_path / "none.yaml") == set()


def test_get_npx_managed_skill_names_corrupt_returns_empty(tmp_path: Path):
    f = tmp_path / "bad.yaml"
    f.write_text("packages:\n  - no_repo_key: true\n")  # 觸發 ValueError
    assert get_npx_managed_skill_names(yaml_path=f) == set()


def test_cleanup_removes_matching_skills_only(tmp_path: Path):
    manifest = {
        "files": {
            "skills": {
                "alpha": {"hash": "h1", "source": "ecc"},
                "kept": {"hash": "h2", "source": "custom-skills"},
                "beta": {"hash": "h3", "source": "anthropic"},
            },
            "commands": {"x": {"hash": "c1"}},
        }
    }

    captured: dict[str, dict] = {}

    def fake_read(target):
        return manifest if target == "claude" else None

    def fake_write(target, data):
        captured[target] = data

    with patch("script.utils.manifest.read_manifest", side_effect=fake_read), \
         patch("script.utils.manifest.write_manifest", side_effect=fake_write):
        removed = cleanup_skills_from_manifests(
            ["alpha", "beta", "never-existed"],
            targets=["claude", "codex"],
        )

    assert removed == {"claude": ["alpha", "beta"]}
    assert "alpha" not in captured["claude"]["files"]["skills"]
    assert "beta" not in captured["claude"]["files"]["skills"]
    assert "kept" in captured["claude"]["files"]["skills"]
    # commands 不受影響
    assert captured["claude"]["files"]["commands"] == {"x": {"hash": "c1"}}


def test_cleanup_noop_when_no_matches(tmp_path: Path):
    manifest = {"files": {"skills": {"x": {"hash": "h"}}}}

    def fake_read(target):
        return manifest

    writes = []

    def fake_write(target, data):
        writes.append((target, data))

    with patch("script.utils.manifest.read_manifest", side_effect=fake_read), \
         patch("script.utils.manifest.write_manifest", side_effect=fake_write):
        removed = cleanup_skills_from_manifests(["nonexistent"], targets=["claude"])

    assert removed == {}
    assert writes == []  # 沒有改動不寫檔


def test_cleanup_empty_skill_list_is_noop():
    assert cleanup_skills_from_manifests([], targets=["claude"]) == {}

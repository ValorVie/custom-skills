from pathlib import Path
from unittest.mock import patch

import pytest
import typer

from script.utils import shared


def _skill(root: Path, name: str) -> Path:
    skill = root / "skills" / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
    return skill


def test_custom_repo_npx_collision_stops_prescan(tmp_path: Path):
    repo = tmp_path / "repo"
    _skill(repo, "managed")

    with (
        patch(
            "script.services.npx_skills.get_npx_managed_skill_names",
            return_value={"managed"},
        ),
        pytest.raises(typer.Exit) as error,
    ):
        shared._scan_repo_resources(
            repo,
            target="claude",
            record_method_map={"skills": lambda *_args, **_kwargs: None},
            source="custom-repo",
        )

    assert error.value.exit_code == 1


def test_ecc_npx_collision_stops_prescan(tmp_path: Path):
    ecc = tmp_path / "ecc"
    _skill(ecc, "managed")
    config = {
        "source_path": str(ecc),
        "distribute": {
            "skills": {
                "source_path": "skills",
                "targets": ["claude"],
                "enabled": ["managed"],
            }
        },
        "skip_directories": [],
        "exclude": {},
    }

    with (
        patch(
            "script.services.npx_skills.get_npx_managed_skill_names",
            return_value={"managed"},
        ),
        pytest.raises(typer.Exit) as error,
    ):
        shared._prescan_ecc(
            "claude",
            {"skills": lambda *_args, **_kwargs: None},
            config,
        )

    assert error.value.exit_code == 1


def test_pending_npx_migration_entry_is_preserved_from_orphan_cleanup():
    old_manifest = {
        "files": {
            "skills": {
                "alpha": {"hash": "a", "source": "custom-skills"},
                "custom-simplify": {"hash": "s", "source": "custom-skills"},
                "ecc-only": {"hash": "e", "source": "ecc"},
            }
        }
    }
    new_manifest = {"files": {"skills": {}}}

    shared._preserve_pending_npx_migration_entries(
        old_manifest,
        new_manifest,
        npx_names={"alpha", "simplify"},
    )

    assert set(new_manifest["files"]["skills"]) == {"alpha", "custom-simplify"}
    assert "ecc-only" not in new_manifest["files"]["skills"]


def test_first_party_root_skills_are_not_platform_resources(tmp_path: Path):
    custom = tmp_path / "custom-skills"
    _skill(custom, "first-party")
    copied_sources: list[tuple[str, Path]] = []

    def fake_copy(src, _dst, resource_type, *_args, **_kwargs):
        copied_sources.append((resource_type, src))

    with (
        patch("script.utils.shared.get_custom_skills_dir", return_value=custom),
        patch("script.utils.shared._copy_with_log", side_effect=fake_copy),
        patch("script.utils.shared.read_manifest", return_value=None, create=True),
        patch("script.utils.shared._prescan_custom_repos"),
        patch("script.utils.shared._distribute_custom_repos"),
        patch("script.utils.shared._load_distribution_config", return_value=None),
        patch("script.utils.manifest.read_manifest", return_value=None),
        patch("script.utils.manifest.write_manifest"),
    ):
        shared.copy_custom_skills_to_targets(
            sync_project=False,
            selected_targets=("claude",),
        )

    assert all(src != custom / "skills" for _, src in copied_sources)

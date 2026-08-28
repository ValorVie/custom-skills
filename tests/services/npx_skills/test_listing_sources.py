from pathlib import Path

from script.utils import shared
from script.services.npx_skills.first_party_overlay import (
    FileState,
    FirstPartyState,
    FirstPartyStateStore,
    SkillState,
)


def test_npx_first_party_source_is_identified(tmp_path: Path, monkeypatch):
    yaml_file = tmp_path / "npx-skills.yaml"
    yaml_file.write_text(
        """version: 1
packages:
  - repo: ValorVie/ai-dev-skills
    source: ai-dev-first-party
    skills: [alpha]
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(shared, "get_npx_skills_user_yaml", lambda: yaml_file)
    monkeypatch.setattr(shared, "get_npx_skills_project_yaml", lambda: yaml_file)

    sources = shared.get_source_skills()

    assert shared.identify_source("alpha", sources) == "ai-dev-skills"
    sources["ai-dev-first-party"].add("simplify")
    assert (
        shared.identify_source("custom-simplify", sources)
        == "ai-dev-skills (legacy: simplify)"
    )


def test_missing_npx_manifest_uses_unknown_fallback(tmp_path: Path, monkeypatch):
    missing = tmp_path / "missing.yaml"
    monkeypatch.setattr(shared, "get_npx_skills_user_yaml", lambda: missing)
    monkeypatch.setattr(shared, "get_npx_skills_project_yaml", lambda: missing)

    sources = shared.get_source_skills()

    assert shared.identify_source("unprovable", sources) == "unknown"


def test_first_party_source_reports_overlay_file_count(tmp_path: Path, monkeypatch):
    yaml_file = tmp_path / "npx-skills.yaml"
    yaml_file.write_text(
        """version: 1
packages:
  - repo: ValorVie/ai-dev-skills
    source: ai-dev-first-party
    skills: [alpha]
""",
        encoding="utf-8",
    )
    state_store = FirstPartyStateStore(
        tmp_path / "npx-first-party.yaml", tmp_path / "overlays"
    )
    overlay = state_store.write_overlay("alpha", "SKILL.md", b"local")
    state_store.write(
        FirstPartyState(
            skills={
                "alpha": SkillState(
                    "ValorVie/ai-dev-skills",
                    "commit",
                    {
                        "SKILL.md": FileState(
                            "source",
                            "commit",
                            "ValorVie/ai-dev-skills",
                            overlay.hash,
                            "keep-local",
                            "now",
                            overlay,
                        )
                    },
                )
            }
        )
    )
    monkeypatch.setattr(shared, "get_npx_skills_user_yaml", lambda: yaml_file)
    monkeypatch.setattr(shared, "get_npx_skills_project_yaml", lambda: yaml_file)
    monkeypatch.setattr(
        shared, "get_npx_first_party_guard_path", lambda: state_store.manifest_path
    )
    monkeypatch.setattr(
        shared, "get_npx_first_party_overlay_dir", lambda: state_store.overlay_root
    )

    sources = shared.get_source_skills()

    assert shared.identify_source("alpha", sources) == (
        "ai-dev-skills + local overlay (1 files)"
    )


def test_first_party_source_reports_unknown_overlay_state(tmp_path: Path, monkeypatch):
    yaml_file = tmp_path / "npx-skills.yaml"
    yaml_file.write_text(
        """version: 1
packages:
  - repo: ValorVie/ai-dev-skills
    source: ai-dev-first-party
    skills: [alpha]
""",
        encoding="utf-8",
    )
    state_path = tmp_path / "npx-first-party.yaml"
    state_path.write_text("skills: [", encoding="utf-8")
    monkeypatch.setattr(shared, "get_npx_skills_user_yaml", lambda: yaml_file)
    monkeypatch.setattr(shared, "get_npx_skills_project_yaml", lambda: yaml_file)
    monkeypatch.setattr(shared, "get_npx_first_party_guard_path", lambda: state_path)
    monkeypatch.setattr(
        shared, "get_npx_first_party_overlay_dir", lambda: tmp_path / "overlays"
    )

    sources = shared.get_source_skills()

    assert shared.identify_source("alpha", sources) == (
        "ai-dev-skills (overlay state unknown)"
    )

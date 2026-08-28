from pathlib import Path

from script.utils import shared


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

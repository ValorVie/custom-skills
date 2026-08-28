from pathlib import Path
import textwrap

import pytest

from script.services.npx_skills.config import NpxSkillsConfig, SkillEntry


def test_load_parses_packages_and_defaults(tmp_path: Path):
    yaml_file = tmp_path / "npx-skills.yaml"
    yaml_file.write_text(textwrap.dedent("""
        version: 1
        defaults:
          agents: "*"
          scope: global
          yes: true
        packages:
          - repo: anthropics/skills
            source: anthropic-official
            skills: [claude-api, skill-creator]
    """).strip())

    config = NpxSkillsConfig.load(yaml_file)

    assert config.version == 1
    assert config.defaults.agents == "*"
    assert config.defaults.scope == "global"
    assert config.defaults.yes is True
    assert len(config.entries) == 2
    assert config.entries[0] == SkillEntry(
        repo="anthropics/skills",
        skill="claude-api",
        source="anthropic-official",
    )


def test_load_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        NpxSkillsConfig.load(tmp_path / "missing.yaml")


@pytest.mark.parametrize(
    ("packages", "message"),
    [
        ("- source: missing-repo\n  skills: [one]", "缺少 repo"),
        ("- repo: empty/repo\n  skills: []", "skills 不得為空"),
        ("- repo: wildcard/repo\n  skills: ['*']", "不得使用 wildcard"),
        (
            "- repo: a/repo\n  skills: [same]\n"
            "- repo: b/repo\n  skills: [same]",
            "重複 canonical ID",
        ),
    ],
)
def test_load_rejects_invalid_package_contract(
    tmp_path: Path, packages: str, message: str
):
    yaml_file = tmp_path / "npx-skills.yaml"
    yaml_file.write_text(
        "version: 1\npackages:\n" + textwrap.indent(packages, "  ") + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=message):
        NpxSkillsConfig.load(yaml_file)

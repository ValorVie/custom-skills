from script.services.npx_skills.config import (
    NpxDefaults,
    SkillEntry,
)
from script.services.npx_skills.install import build_add_command, build_update_command


def test_build_add_command_includes_global_and_agents():
    entry = SkillEntry(repo="anthropics/skills", skill="claude-api", source="anthropic")
    defaults = NpxDefaults(agents="*", scope="global", yes=True)

    cmd = build_add_command(entry, defaults)

    assert cmd == [
        "npx", "skills", "add",
        "anthropics/skills@claude-api",
        "-g", "-a", "*", "--yes",
    ]


def test_build_add_command_project_scope_omits_global():
    entry = SkillEntry(repo="x/y", skill="z", source="x")
    defaults = NpxDefaults(agents="claude", scope="project", yes=False)

    cmd = build_add_command(entry, defaults)

    assert "-g" not in cmd
    assert "--yes" not in cmd
    assert cmd == [
        "npx", "skills", "add",
        "x/y@z",
        "-a", "claude",
    ]


def test_build_update_command_uses_skill_only():
    entry = SkillEntry(repo="anthropics/skills", skill="claude-api", source="anthropic")
    defaults = NpxDefaults()

    cmd = build_update_command(entry, defaults)

    assert cmd == ["npx", "skills", "update", "claude-api", "-y"]

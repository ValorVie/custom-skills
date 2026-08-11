from script.cli.command_manifest import build_command_manifest


def test_command_manifest_contains_top_level_pipeline_commands() -> None:
    manifest = build_command_manifest()
    paths = {spec.path for spec in manifest.commands}

    assert ("install",) in paths
    assert ("update",) in paths
    assert ("clone",) in paths


def test_command_manifest_registers_expected_default_phases() -> None:
    manifest = build_command_manifest()
    commands = {spec.path: spec for spec in manifest.commands}

    assert commands[("install",)].default_phases == (
        "tools",
        "repos",
        "npx-skills",
        "targets",
    )
    assert commands[("update",)].default_phases == (
        "tools",
        "repos",
        "npx-skills",
    )
    assert commands[("clone",)].default_phases == ("targets",)


def test_pipeline_commands_register_shared_codex_skill_migration_writers() -> None:
    manifest = build_command_manifest()
    expected = {
        "~/.codex/skills/",
        "~/.agents/skills/",
        "~/.config/ai-dev/backups/codex-skills-migration/",
    }

    for spec in manifest.commands:
        assert expected <= set(spec.state_writers)


def test_clone_registers_retired_auto_skill_cleanup_writers() -> None:
    commands = {spec.path: spec for spec in build_command_manifest().commands}
    writers = set(commands[("clone",)].state_writers)

    assert "~/.config/ai-dev/backups/auto-skill-removal/" in writers
    assert "~/.claude/plugins/" in writers
    assert "~/.agents/skills/auto-skill" in writers

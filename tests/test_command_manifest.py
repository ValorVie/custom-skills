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
        "state",
        "targets",
    )
    assert commands[("update",)].default_phases == ("tools", "repos", "state")
    assert commands[("clone",)].default_phases == ("state", "targets")

import pytest

from script.cli.command_manifest import build_command_manifest, get_command_spec
from script.cli.phase_selection import build_execution_plan


def test_parse_only_and_skip_into_execution_plan() -> None:
    spec = get_command_spec(build_command_manifest(), ("clone",))
    plan = build_execution_plan(
        spec,
        only="targets",
        skip=None,
        target="claude,codex",
        dry_run=True,
    )

    assert plan.phases == ("targets",)
    assert plan.targets == ("claude", "codex")
    assert plan.dry_run is True


def test_target_requires_targets_phase() -> None:
    spec = get_command_spec(build_command_manifest(), ("clone",))

    with pytest.raises(ValueError, match="targets phase"):
        build_execution_plan(
            spec,
            only="state",
            skip=None,
            target="claude",
            dry_run=False,
        )


def test_only_and_skip_cannot_be_combined() -> None:
    spec = get_command_spec(build_command_manifest(), ("install",))

    with pytest.raises(ValueError, match="不能同時使用"):
        build_execution_plan(
            spec,
            only="tools",
            skip="repos",
            target=None,
            dry_run=False,
        )

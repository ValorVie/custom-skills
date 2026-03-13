from script.models.command_spec import CommandSpec
from script.models.execution_plan import ExecutionPlan


def test_execution_plan_exposes_basic_fields() -> None:
    plan = ExecutionPlan(
        command_name="update",
        phases=("tools", "repos", "state"),
        targets=("claude", "codex"),
        dry_run=True,
    )

    assert plan.command_name == "update"
    assert plan.phases == ("tools", "repos", "state")
    assert plan.targets == ("claude", "codex")
    assert plan.dry_run is True
    assert plan.requires_targets is False


def test_execution_plan_requires_targets_when_targets_phase_present() -> None:
    plan = ExecutionPlan(
        command_name="clone",
        phases=("state", "targets"),
        targets=("claude",),
        dry_run=False,
    )

    assert plan.requires_targets is True


def test_command_spec_holds_minimal_task_two_metadata() -> None:
    spec = CommandSpec(
        path=("install",),
        kind="top_level",
        default_phases=("tools", "repos", "state", "targets"),
        allowed_phases=("tools", "repos", "state", "targets"),
        allowed_targets=("claude", "codex"),
        flags=("only", "skip", "target", "dry_run"),
        state_writers=("~/.config/ai-dev/skills/auto-skill",),
    )

    assert spec.path == ("install",)
    assert spec.kind == "top_level"
    assert spec.default_phases == ("tools", "repos", "state", "targets")
    assert spec.allowed_phases == ("tools", "repos", "state", "targets")
    assert spec.allowed_targets == ("claude", "codex")
    assert spec.flags == ("only", "skip", "target", "dry_run")
    assert spec.state_writers == ("~/.config/ai-dev/skills/auto-skill",)

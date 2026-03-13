from __future__ import annotations

from script.models.command_spec import CommandSpec
from script.models.execution_plan import ExecutionPlan

from .target_selection import resolve_targets


def _parse_csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(part.strip() for part in value.split(",") if part.strip())


def resolve_phases(
    default_phases: tuple[str, ...],
    allowed_phases: tuple[str, ...],
    only: str | None,
    skip: str | None,
) -> tuple[str, ...]:
    if only:
        phases = _parse_csv(only)
    else:
        skip_set = set(_parse_csv(skip))
        phases = tuple(phase for phase in default_phases if phase not in skip_set)

    invalid = [phase for phase in phases if phase not in allowed_phases]
    if invalid:
        raise ValueError(f"Unknown phases: {', '.join(invalid)}")
    return phases


def build_execution_plan(
    spec: CommandSpec,
    *,
    only: str | None,
    skip: str | None,
    target: str | None,
    dry_run: bool,
) -> ExecutionPlan:
    phases = resolve_phases(spec.default_phases, spec.allowed_phases, only, skip)
    targets = resolve_targets(spec.allowed_targets, target, phases)
    return ExecutionPlan(
        command_name=" ".join(spec.path),
        phases=phases,
        targets=targets,
        dry_run=dry_run,
    )

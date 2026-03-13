from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionPlan:
    """Normalized execution plan for a top-level command."""

    command_name: str
    phases: tuple[str, ...]
    targets: tuple[str, ...]
    dry_run: bool = False

    @property
    def requires_targets(self) -> bool:
        return "targets" in self.phases

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandSpec:
    """Machine-readable command contract for CLI and docs."""

    path: tuple[str, ...]
    kind: str
    default_phases: tuple[str, ...]
    allowed_phases: tuple[str, ...]
    allowed_targets: tuple[str, ...] = ()
    flags: tuple[str, ...] = ()
    state_writers: tuple[str, ...] = ()

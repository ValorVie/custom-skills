from __future__ import annotations


def resolve_targets(
    allowed_targets: tuple[str, ...],
    target: str | None,
    phases: tuple[str, ...],
) -> tuple[str, ...]:
    if not target:
        return ()

    if "targets" not in phases:
        raise ValueError("--target requires targets phase")

    selected = tuple(part.strip() for part in target.split(",") if part.strip())
    invalid = [item for item in selected if item not in allowed_targets]
    if invalid:
        raise ValueError(f"Unknown targets: {', '.join(invalid)}")
    return selected

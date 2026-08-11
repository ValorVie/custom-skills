from __future__ import annotations

from dataclasses import dataclass

from script.models.command_spec import CommandSpec


PIPELINE_PHASES = ("tools", "repos", "state", "npx-skills", "targets")
TARGETS = ("claude", "codex", "agy", "opencode", "antigravity")
PIPELINE_FLAGS = ("only", "skip", "target", "dry_run")
CODEX_SKILL_MIGRATION_WRITERS = (
    "~/.codex/skills/",
    "~/.agents/skills/",
    "~/.config/ai-dev/backups/codex-skills-migration/",
)


@dataclass(frozen=True)
class CommandManifest:
    commands: tuple[CommandSpec, ...]


def build_command_manifest() -> CommandManifest:
    return CommandManifest(
        commands=(
            CommandSpec(
                path=("install",),
                kind="top_level",
                default_phases=PIPELINE_PHASES,
                allowed_phases=PIPELINE_PHASES,
                allowed_targets=TARGETS,
                flags=PIPELINE_FLAGS,
                state_writers=(
                    *CODEX_SKILL_MIGRATION_WRITERS,
                    "~/.config/custom-skills/",
                    "~/.config/ai-dev/skills/auto-skill",
                    "~/.config/ai-dev/npx-skills.yaml",
                    "~/.config/ai-dev/projections/<target>/auto-skill",
                ),
            ),
            CommandSpec(
                path=("update",),
                kind="top_level",
                default_phases=("tools", "repos", "state", "npx-skills"),
                allowed_phases=("tools", "repos", "state", "npx-skills"),
                allowed_targets=TARGETS,
                flags=PIPELINE_FLAGS,
                state_writers=(
                    *CODEX_SKILL_MIGRATION_WRITERS,
                    "~/.config/custom-skills/",
                    "~/.config/ai-dev/skills/auto-skill",
                    "~/.config/ai-dev/npx-skills.yaml",
                ),
            ),
            CommandSpec(
                path=("clone",),
                kind="top_level",
                default_phases=("state", "targets"),
                allowed_phases=("state", "targets"),
                allowed_targets=TARGETS,
                flags=PIPELINE_FLAGS,
                state_writers=(
                    *CODEX_SKILL_MIGRATION_WRITERS,
                    "~/.config/ai-dev/skills/auto-skill",
                    "~/.config/ai-dev/projections/<target>/auto-skill",
                ),
            ),
        )
    )


def get_command_spec(
    manifest: CommandManifest,
    path: tuple[str, ...],
) -> CommandSpec:
    for spec in manifest.commands:
        if spec.path == path:
            return spec
    raise KeyError(f"Unknown command path: {' '.join(path)}")

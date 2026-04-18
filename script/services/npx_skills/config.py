from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class NpxDefaults:
    agents: str = "*"
    scope: str = "global"
    yes: bool = True


@dataclass(frozen=True)
class SkillEntry:
    repo: str
    skill: str
    source: str


@dataclass(frozen=True)
class NpxSkillsConfig:
    version: int
    defaults: NpxDefaults
    entries: tuple[SkillEntry, ...]

    @classmethod
    def load(cls, path: Path) -> NpxSkillsConfig:
        if not path.exists():
            raise FileNotFoundError(f"npx-skills.yaml not found: {path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        defaults_raw = data.get("defaults", {}) or {}
        defaults = NpxDefaults(
            agents=defaults_raw.get("agents", "*"),
            scope=defaults_raw.get("scope", "global"),
            yes=bool(defaults_raw.get("yes", True)),
        )
        entries: list[SkillEntry] = []
        for pkg in data.get("packages", []) or []:
            repo = pkg["repo"]
            source = pkg.get("source", repo)
            for skill in pkg.get("skills", []) or []:
                entries.append(SkillEntry(repo=repo, skill=skill, source=source))
        return cls(
            version=int(data.get("version", 1)),
            defaults=defaults,
            entries=tuple(entries),
        )


def ensure_user_yaml(*, project_path: Path, user_path: Path) -> Path:
    """Copy project yaml to user-level location, overwriting any existing file."""
    if not project_path.exists():
        raise FileNotFoundError(f"project npx-skills.yaml missing: {project_path}")
    user_path.parent.mkdir(parents=True, exist_ok=True)
    user_path.write_bytes(project_path.read_bytes())
    return user_path

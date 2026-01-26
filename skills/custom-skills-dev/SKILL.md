---
name: custom-skills-dev
description: |
  Guide development workflow for the custom-skills project (ai-dev CLI tool).
  Use when: (1) adding/modifying skills, commands, or agents, (2) modifying CLI code in script/,
  (3) updating copy/distribution logic, (4) releasing new versions, (5) integrating upstream resources.
  Triggers: "develop custom-skills", "modify ai-dev", "add skill to project", "update copy logic",
  "release version", "開發 custom-skills", "修改複製邏輯", "發布版本".
---

# custom-skills-dev

Development guide for the custom-skills project (ai-dev CLI tool).

## Project Overview

This project is a **Configuration as Code** repository providing:
- Unified AI development standards (Skills, Commands, Agents)
- CLI tool (`ai-dev`) for managing AI tool configurations
- Three-stage copy architecture for resource distribution

## Quick Reference

### Key Directories

| Directory | Purpose |
|-----------|---------|
| `script/` | Python CLI implementation |
| `skills/` | Shared skills (all AI tools) |
| `commands/` | Tool-specific commands (claude/, gemini/, etc.) |
| `agents/` | Tool-specific agents (claude/, opencode/) |
| `sources/` | Upstream resource integration (ecc/) |
| `upstream/` | Upstream tracking system |

### Three-Stage Copy Flow

```
Stage 1: Clone     GitHub repos → ~/.config/
Stage 2: Integrate ~/.config/* → ~/.config/custom-skills/
Stage 3: Distribute ~/.config/custom-skills/ → ~/.claude/, ~/.gemini/, etc.
```

For details, see [references/copy-architecture.md](references/copy-architecture.md).

## Common Development Tasks

### Adding a New Skill

1. Create `skills/<skill-name>/SKILL.md`
2. Add optional `references/` for detailed docs
3. Run `ai-dev update` to distribute
4. Update CHANGELOG.md

### Adding a New CLI Command

1. Create `script/commands/<command>.py`
2. Register in `script/main.py`
3. Update README.md command table
4. Update CHANGELOG.md
5. Bump version in `pyproject.toml`

For details, see [references/cli-development.md](references/cli-development.md).

### Releasing a New Version

1. Update version in `pyproject.toml`
2. Add CHANGELOG entry with date
3. Commit: `git commit -m "chore(release): v0.X.Y"`
4. Tag: `git tag v0.X.Y`
5. Push: `git push && git push --tags`

For details, see [references/release-workflow.md](references/release-workflow.md).

### Integrating Upstream Resources

1. Add source to `upstream/sources.yaml`
2. Clone to `~/.config/`
3. Run `/custom-skills-upstream-sync` to analyze
4. Create integration proposal via `/openspec:proposal`
5. Place resources in `sources/<name>/`

## Language Convention

- Documentation: **繁體中文** (Traditional Chinese)
- Technical terms preserved in English: Skill, Command, Agent, Hook, MCP
- Commit messages: 繁體中文 with Conventional Commits format

## Testing Changes

```bash
# Install locally for testing
uv tool install . --force

# Verify installation
ai-dev --version
ai-dev status

# Test specific command
ai-dev install --skip-npm --skip-repos
```

## References

- [Copy Architecture](references/copy-architecture.md) - Three-stage flow details
- [CLI Development](references/cli-development.md) - Python CLI guide
- [Release Workflow](references/release-workflow.md) - Version release process

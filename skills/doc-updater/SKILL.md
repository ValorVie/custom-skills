---
name: doc-updater
description: |
  Maintain and update custom-skills project documentation for consistency and accuracy.
  Use when: (1) code changes affect documented features, (2) adding new skills/commands/agents,
  (3) version releases, (4) structural changes to the project, (5) user asks to update docs,
  (6) changelog needs updating.
  Triggers: "update docs", "sync documentation", "update README", "update changelog",
  "documentation audit", "doc sync", "更新文檔", "同步文件", "文檔檢查".
---

# Documentation Updater

Update and maintain custom-skills project documentation to ensure consistency across all files.

## Target Documents

### Priority 1: Core Documents (Always Check)

| Document | Purpose | Update Triggers |
|----------|---------|-----------------|
| `README.md` | Project overview, installation, CLI usage | CLI changes, new features, version bump |
| `CHANGELOG.md` | Version history | Every release, significant changes |
| `openspec/project.md` | Project context, conventions | Architecture changes, stack updates |

### Priority 2: Feature Documentation

| Document | Purpose | Update Triggers |
|----------|---------|-----------------|
| `docs/AI開發環境設定指南.md` | User setup guide | Installation process changes |
| `docs/AI輔助開發的本質原理.md` | Design philosophy | Conceptual changes |
| `docs/Skill-Command-Agent差異說明.md` | Concept clarification | New patterns introduced |

### Priority 3: Module READMEs

| Directory | README Purpose |
|-----------|----------------|
| `sources/ecc/` | ECC resource integration status |
| `sources/ecc/hooks/` | Hooks plugin documentation |
| `upstream/` | Upstream tracking system |
| `commands/claude/` | Available slash commands |
| `agents/claude/` | Agent specifications |
| `skills/` | Skills overview |

## Workflow

### Step 1: Identify Changes

Determine what changed:
```
git diff --name-only HEAD~1     # Recent changes
git log --oneline -5            # Recent commits
```

### Step 2: Map Changes to Documents

| Change Type | Documents to Update |
|-------------|---------------------|
| New CLI command | README.md, CHANGELOG.md |
| New skill | skills/README.md, commands/claude/README.md |
| New agent | agents/claude/README.md |
| Version bump | pyproject.toml, README.md, CHANGELOG.md |
| Architecture change | openspec/project.md, docs/dev-guide/ |
| New upstream source | upstream/README.md, sources/*/README.md |

### Step 3: Update Documents

Follow the format conventions in [references/doc-formats.md](references/doc-formats.md).

### Step 4: Verify Consistency

Check cross-references:
- Version numbers match across files
- Feature lists are consistent
- Links are valid
- Tables are up-to-date

## Quick Reference

### CHANGELOG Format

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- **Feature Name**: Description

### Changed
- **Breaking Change**: Description

### Fixed
- Description of fix
```

### README Section Order

1. Title and badges
2. Installation
3. Usage / Quick Start
4. Commands overview
5. Development
6. Resources / Links

### Common Update Patterns

**Adding a new command:**
1. Create command file in `commands/claude/`
2. Update `commands/claude/README.md` table
3. Update `CHANGELOG.md`

**Adding a new skill:**
1. Create skill in `skills/`
2. Update related README if applicable
3. Update `CHANGELOG.md`

**Version release:**
1. Update `pyproject.toml` version
2. Add CHANGELOG entry with date
3. Verify README reflects current features

## Language Convention

All documentation must use **繁體中文** (Traditional Chinese) with English technical terms preserved:
- Skill, Command, Agent, Hook, Plugin
- CLI, TUI, MCP, API
- Git, GitHub, upstream

## References

For detailed format specifications, see [references/doc-formats.md](references/doc-formats.md).

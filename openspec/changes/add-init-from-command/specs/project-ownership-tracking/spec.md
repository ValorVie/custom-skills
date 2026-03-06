## ADDED Requirements

### Requirement: Project tracking file format

The system SHALL create and maintain a `.ai-dev-project.yaml` file in the project root directory with the following structure:

```yaml
template:
  name: <repo-name>
  url: <clone-url>
  branch: <branch>
  initialized_at: <ISO-8601 timestamp>
  last_updated: <ISO-8601 timestamp>

managed_files:
  - CLAUDE.md
  - GEMINI.md
  - .claude/commands/tdd.md
  - .standards/commit-message.ai.yaml
  # ... file-level entries
```

#### Scenario: Tracking file created on init-from

- **WHEN** `ai-dev init-from` completes successfully
- **THEN** the system SHALL create `.ai-dev-project.yaml` in CWD
- **THEN** `managed_files` SHALL contain every file that was copied, overwritten, or appended (not skipped by user)
- **THEN** `initialized_at` SHALL contain the current ISO-8601 timestamp
- **THEN** `last_updated` SHALL equal `initialized_at`

#### Scenario: Skipped files not tracked

- **WHEN** user chooses to skip a file during smart merge
- **THEN** the file SHALL NOT appear in `managed_files`

#### Scenario: Tracking file updated on --update

- **WHEN** `ai-dev init-from --update` completes
- **THEN** `last_updated` SHALL be updated to the current timestamp
- **THEN** `managed_files` SHALL be updated to reflect any newly added or removed files

### Requirement: File-level granularity

The `managed_files` list SHALL use relative paths from the project root, one entry per file (not directory).

#### Scenario: Individual files tracked within directory

- **WHEN** the template provides `.claude/commands/tdd.md` and `.claude/commands/bdd.md`
- **THEN** `managed_files` SHALL contain both:
  - `.claude/commands/tdd.md`
  - `.claude/commands/bdd.md`
- **THEN** other files in `.claude/commands/` (e.g., from `ai-dev clone`) SHALL NOT be affected

#### Scenario: Clone can add files alongside managed files

- **WHEN** `.ai-dev-project.yaml` tracks `.claude/skills/openspec-explore/SKILL.md`
- **THEN** `ai-dev clone` SHALL be able to add `.claude/skills/some-other-skill/SKILL.md` to the same parent directory
- **THEN** `ai-dev clone` SHALL NOT modify `.claude/skills/openspec-explore/SKILL.md`

### Requirement: Tracking file committed to git

The `.ai-dev-project.yaml` file SHOULD be committed to the project's git repository so that team members are aware of the template source.

#### Scenario: File is not in gitignore

- **WHEN** `ai-dev init-from` creates `.ai-dev-project.yaml`
- **THEN** the system SHALL NOT add `.ai-dev-project.yaml` to `.gitignore`

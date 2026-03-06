## ADDED Requirements

### Requirement: init-from CLI interface

The system SHALL provide an `ai-dev init-from` command that accepts:

- **Required argument**: `source` — remote repo path (supports `owner/repo`, full HTTPS URL, SSH URL)
- **Optional flags**:
  - `--name` / `-n`: Custom name (defaults to repo name)
  - `--branch` / `-b`: Branch to track (defaults to `main`)
  - `--update`: Re-run smart merge for an already-initialized project
  - `--force`: Overwrite all conflicting files without prompting
  - `--skip-conflicts`: Skip all conflicting files without prompting

#### Scenario: First-time initialization with URL

- **WHEN** user runs `ai-dev init-from https://github.com/ValorVie/qdm-ai-base` in a project directory
- **THEN** the system SHALL clone the repo to `~/.config/qdm-ai-base/`
- **THEN** the system SHALL register the repo in `~/.config/ai-dev/repos.yaml` with `type: template`
- **THEN** the system SHALL copy all files from the template to CWD using smart merge
- **THEN** the system SHALL create `.ai-dev-project.yaml` in CWD tracking managed files

#### Scenario: First-time initialization with shorthand

- **WHEN** user runs `ai-dev init-from ValorVie/qdm-ai-base`
- **THEN** the system SHALL resolve to `https://github.com/ValorVie/qdm-ai-base.git`
- **THEN** the system SHALL use `qdm-ai-base` as the default name

#### Scenario: Template repo already cloned

- **WHEN** user runs `ai-dev init-from qdm-ai-base` and `~/.config/qdm-ai-base/` already exists
- **THEN** the system SHALL skip cloning
- **THEN** the system SHALL proceed with smart merge from the existing local copy

#### Scenario: Update mode

- **WHEN** user runs `ai-dev init-from --update` in a project with `.ai-dev-project.yaml`
- **THEN** the system SHALL read the template source from `.ai-dev-project.yaml`
- **THEN** the system SHALL pull latest changes from the template repo
- **THEN** the system SHALL re-run smart merge only for files in `managed_files`
- **THEN** the system SHALL update the `last_updated` field in `.ai-dev-project.yaml`

#### Scenario: Update mode without tracking file

- **WHEN** user runs `ai-dev init-from --update` and no `.ai-dev-project.yaml` exists
- **THEN** the system SHALL display an error: "No init-from tracking found. Run `ai-dev init-from <source>` first."

### Requirement: File exclusion during initialization

The system SHALL exclude the following paths when copying from the template repo:

- `.git/` directory
- `.gitkeep` files
- `README.md` at root level
- `LICENSE` at root level

#### Scenario: Git directory excluded

- **WHEN** the template repo contains `.git/` directory
- **THEN** the system SHALL NOT copy `.git/` to the target project

#### Scenario: Gitkeep files excluded

- **WHEN** the template repo contains `.gitkeep` files in any directory
- **THEN** the system SHALL NOT copy `.gitkeep` files to the target project

### Requirement: Smart merge flow

When copying files from template to CWD, the system SHALL follow this merge logic for each file:

1. If the destination file does not exist: copy directly
2. If the destination file exists and content is identical (SHA-256): skip
3. If the destination file exists and content differs: prompt user interactively

#### Scenario: New file — direct copy

- **WHEN** a template file `CLAUDE.md` does not exist in CWD
- **THEN** the system SHALL copy the file directly
- **THEN** the system SHALL display "  + CLAUDE.md (new)"

#### Scenario: Identical file — skip

- **WHEN** a template file `.editorconfig` exists in CWD with identical content
- **THEN** the system SHALL skip the file
- **THEN** the system SHALL display "  = .editorconfig (identical)"

#### Scenario: Different file — interactive prompt

- **WHEN** a template file `CLAUDE.md` exists in CWD with different content
- **THEN** the system SHALL prompt with options:
  - `[A]` Append to end — append template content after existing content
  - `[I]` Incremental append — only append lines from template that don't exist in target
  - `[O]` Overwrite — replace with template content
  - `[S]` Skip — keep existing content
  - `[D]` Diff — show unified diff, then re-prompt

#### Scenario: Force mode skips prompts

- **WHEN** `--force` flag is provided
- **THEN** the system SHALL overwrite all conflicting files without prompting

#### Scenario: Skip-conflicts mode

- **WHEN** `--skip-conflicts` flag is provided
- **THEN** the system SHALL skip all conflicting files without prompting

### Requirement: Completion report

After processing all files, the system SHALL display a summary report.

#### Scenario: Summary after initialization

- **WHEN** initialization completes
- **THEN** the system SHALL display counts for:
  - New files copied
  - Identical files skipped
  - Files overwritten
  - Files appended
  - Files skipped by user choice

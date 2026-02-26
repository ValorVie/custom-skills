## MODIFIED Requirements

### Requirement: Clone command distributes skills to tool directories
The clone command SHALL distribute skills/commands/agents/workflows from source repositories to all target tool directories (Claude, OpenCode, Gemini, Codex, Antigravity), NOT clone git repositories.

#### Scenario: Normal skill distribution
- **WHEN** user runs `ai-dev clone`
- **THEN** system copies all skills/commands/agents/workflows from source repos to each target's directory

#### Scenario: Developer mode detection
- **WHEN** user runs `ai-dev clone` from within the custom-skills project directory
- **THEN** system detects developer mode and uses symlinks instead of copies

#### Scenario: Force overwrite
- **WHEN** user runs `ai-dev clone --force`
- **THEN** system overwrites existing files without prompting

#### Scenario: Skip conflicts
- **WHEN** user runs `ai-dev clone --skip-conflicts`
- **THEN** system skips files that already exist in target directories

#### Scenario: Backup before overwrite
- **WHEN** user runs `ai-dev clone --backup`
- **THEN** system creates backup of existing files before overwriting

#### Scenario: Metadata change detection
- **WHEN** source files have different metadata (timestamps, content hash) than target
- **THEN** system reports which files were updated and which were unchanged

#### Scenario: Sync project option
- **WHEN** user runs `ai-dev clone --sync-project`
- **THEN** system also syncs project-template files to the current project

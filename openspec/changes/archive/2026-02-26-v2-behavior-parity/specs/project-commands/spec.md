## MODIFIED Requirements

### Requirement: Project init with smart file merging
The project init command SHALL copy template files with smart merging for .gitignore and .gitattributes.

#### Scenario: Init new project
- **WHEN** user runs `ai-dev project init` in a directory without existing config
- **THEN** system copies all files from project-template/ to current directory

#### Scenario: Gitignore smart merge
- **WHEN** target directory already has .gitignore
- **THEN** system compares line-by-line and only adds entries that don't exist

#### Scenario: Gitattributes smart merge
- **WHEN** target directory already has .gitattributes
- **THEN** system compares line-by-line and only adds entries that don't exist

#### Scenario: Backup before overwrite
- **WHEN** init would overwrite existing files
- **THEN** system creates backup of existing files before overwriting

#### Scenario: Force overwrite
- **WHEN** user runs `ai-dev project init --force`
- **THEN** system overwrites all existing files without backup

#### Scenario: Developer reverse sync
- **WHEN** user runs `ai-dev project init` from within custom-skills project
- **THEN** system syncs from project back to project-template/ (reverse direction)

### Requirement: Project update with tool filtering
The project update command SHALL run uds update and openspec update with optional tool filtering.

#### Scenario: Full update
- **WHEN** user runs `ai-dev project update`
- **THEN** system runs `uds update` and `openspec update`

#### Scenario: Update specific tool
- **WHEN** user runs `ai-dev project update --only uds`
- **THEN** system runs only `uds update`, skipping openspec

#### Scenario: File diff display
- **WHEN** update modifies files
- **THEN** system displays file-by-file diff summary

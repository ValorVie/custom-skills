## MODIFIED Requirements

### Requirement: Add-repo with format detection and source tracking
The add-repo command SHALL detect repository format and write to upstream/sources.yaml.

#### Scenario: Add upstream repository
- **WHEN** user runs `ai-dev add-repo <url>`
- **THEN** system clones repo, detects format (UDS/claude-code-native/skills-repo), writes entry to upstream/sources.yaml

#### Scenario: Format detection
- **WHEN** cloned repository contains .standards/ directory
- **THEN** system identifies it as UDS format

#### Scenario: Duplicate detection
- **WHEN** user adds a repo that already exists in upstream/
- **THEN** system warns and asks for confirmation

#### Scenario: Analyze option
- **WHEN** user runs `ai-dev add-repo <url> --analyze`
- **THEN** system analyzes repository structure and suggests integration approach

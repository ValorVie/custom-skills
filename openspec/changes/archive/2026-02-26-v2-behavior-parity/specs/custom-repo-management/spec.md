## MODIFIED Requirements

### Requirement: Add-custom-repo validates repository structure
The add-custom-repo command SHALL validate that the cloned repository has the expected directory structure.

#### Scenario: Valid repository structure
- **WHEN** user runs `ai-dev add-custom-repo <url>` and repo has skills/ or commands/ directory
- **THEN** system clones repo and writes entry to repos.yaml

#### Scenario: Invalid repository structure
- **WHEN** cloned repo has no skills/, commands/, agents/, or workflows/ directory
- **THEN** system warns about invalid structure

#### Scenario: Fix option creates missing directories
- **WHEN** user runs `ai-dev add-custom-repo <url> --fix`
- **THEN** system creates missing directory structure in the cloned repo

### Requirement: Update-custom-repo with safe update mechanism
The update-custom-repo command SHALL use fetch + backup + reset instead of simple git pull.

#### Scenario: Update with local changes
- **WHEN** a custom repo has local modifications
- **THEN** system backs up dirty files before `git reset --hard origin/{branch}`

#### Scenario: Update without local changes
- **WHEN** a custom repo has no local modifications
- **THEN** system performs `git fetch --all` then `git reset --hard origin/{branch}`

#### Scenario: Update summary
- **WHEN** update completes
- **THEN** system displays summary showing which repos were updated, which were already up-to-date, and any errors

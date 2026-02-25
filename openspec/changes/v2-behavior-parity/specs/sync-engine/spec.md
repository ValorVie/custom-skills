## MODIFIED Requirements

### Requirement: Sync init creates git-backed sync repository
The sync init command SHALL create a git-backed synchronization repository with LFS support.

#### Scenario: Init with remote URL
- **WHEN** user runs `ai-dev sync init --remote <url>`
- **THEN** system clones the remote repository and configures it as the sync target

#### Scenario: Init without remote
- **WHEN** user runs `ai-dev sync init`
- **THEN** system creates a local git repository at the default sync directory

#### Scenario: LFS detection and setup
- **WHEN** initializing sync and binary files are detected
- **THEN** system configures git LFS tracking with appropriate `.gitattributes`

### Requirement: Sync push uses git operations
The sync push command SHALL use git add/commit/push to synchronize local files to the remote repository.

#### Scenario: Normal push
- **WHEN** user runs `ai-dev sync push`
- **THEN** system copies tracked directories to sync repo, runs `git add -A`, `git commit`, and `git push`

#### Scenario: Force push
- **WHEN** user runs `ai-dev sync push --force`
- **THEN** system uses `git push --force` to overwrite remote

#### Scenario: LFS push
- **WHEN** sync repository has LFS-tracked files
- **THEN** system runs `git lfs push` after regular push

#### Scenario: Plugin manifest generation
- **WHEN** pushing sync data
- **THEN** system generates plugin manifest listing all synced resources

### Requirement: Sync pull with safety checks
The sync pull command SHALL detect local changes and offer interactive options before overwriting.

#### Scenario: Pull with no local changes
- **WHEN** user runs `ai-dev sync pull` and no local changes exist
- **THEN** system pulls from remote and copies files to local directories

#### Scenario: Pull with local changes detected
- **WHEN** user runs `ai-dev sync pull` and local changes exist
- **THEN** system presents 3 options: (1) overwrite local, (2) backup then overwrite, (3) cancel

#### Scenario: No-delete pull
- **WHEN** user runs `ai-dev sync pull --no-delete`
- **THEN** system does not delete local files that don't exist in remote

#### Scenario: Force pull
- **WHEN** user runs `ai-dev sync pull --force`
- **THEN** system overwrites local changes without prompting

### Requirement: Sync status shows detailed state
The sync status command SHALL display local change count and remote commit difference.

#### Scenario: Status with pending changes
- **WHEN** user runs `ai-dev sync status` and local files have changed
- **THEN** system shows count of modified/added/deleted files and commits behind remote

## ADDED Requirements

### Requirement: Install or update superpowers for OpenCode via ai-dev
ai-dev install/update SHALL ensure OpenCode superpowers is present at `~/.config/opencode/superpowers` by cloning if absent or pulling if present, using the official upstream repository.

#### Scenario: Fresh install
- **WHEN** ai-dev install runs on a machine without `~/.config/opencode/superpowers`
- **THEN** the tool SHALL clone `https://github.com/obra/superpowers.git` into `~/.config/opencode/superpowers`
- **AND** report success to the user.

#### Scenario: Update existing checkout
- **WHEN** ai-dev update runs and `~/.config/opencode/superpowers` already exists
- **THEN** the tool SHALL run `git pull` in that directory
- **AND** continue even if there are no changes.

### Requirement: Create plugin and skills symlinks for OpenCode
ai-dev install/update SHALL create or refresh symlinks `~/.config/opencode/plugins/superpowers.js` → `.opencode/plugins/superpowers.js` and `~/.config/opencode/skills/superpowers` → `skills/` inside the cloned repository, removing pre-existing links or directories safely beforehand.

#### Scenario: Symlink creation on clean machine
- **WHEN** ai-dev install runs and the plugin/skills paths do not exist
- **THEN** it SHALL create the two symlinks pointing into `~/.config/opencode/superpowers`
- **AND** ensure parent directories `~/.config/opencode/plugins` and `~/.config/opencode/skills` exist.

#### Scenario: Symlink refresh on re-run
- **WHEN** ai-dev update runs and the plugin/skills paths already exist (file, dir, or symlink)
- **THEN** it SHALL remove them and recreate symlinks to the current checkout targets.

### Requirement: Preserve Claude Code tracking checkout
ai-dev install/update SHALL NOT remove or modify the existing `~/.config/superpowers` directory used for Claude Code tracking.

#### Scenario: Dual checkout coexistence
- **WHEN** ai-dev install/update runs on a system that already has `~/.config/superpowers`
- **THEN** the command SHALL leave that directory untouched while completing OpenCode setup.

### Requirement: Post-install verification guidance
ai-dev install/update SHALL print verification hints showing the symlink targets (`ls -l ~/.config/opencode/plugins/superpowers.js` and `ls -l ~/.config/opencode/skills/superpowers`).

#### Scenario: User requests verification
- **WHEN** the install/update completes
- **THEN** the output SHALL include the verification commands so the user can confirm the links.

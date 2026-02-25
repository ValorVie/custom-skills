## MODIFIED Requirements

### Requirement: Install command performs full environment setup
The install command SHALL execute the complete 16-step v1 installation flow including prerequisite checks, directory creation, package installation, repository cloning, skill distribution, and shell completion.

#### Scenario: Full install flow
- **WHEN** user runs `ai-dev install`
- **THEN** system executes all steps: prerequisite check → Claude Code status → NPM packages → Bun packages → directory creation → repo cloning → custom repo cloning → skill distribution → skill listing → npm hint → shell completion

#### Scenario: Prerequisite check with version requirements
- **WHEN** user runs `ai-dev install`
- **THEN** system checks Node.js >= 20, Git, gh CLI, and Bun, displaying version for each and install instructions for missing tools

#### Scenario: Directory creation for all targets
- **WHEN** installing for the first time
- **THEN** system creates all 16 target directories (claude/opencode/gemini/codex/antigravity × skills/commands/agents/workflows)

#### Scenario: Clone all repositories
- **WHEN** user runs `ai-dev install` without `--skip-repos`
- **THEN** system clones all 7+ repositories including obsidian-skills, anthropic-skills, everything-claude-code, auto-skill

#### Scenario: Custom repository cloning
- **WHEN** `~/.config/ai-dev/repos.yaml` contains custom repositories
- **THEN** system clones all custom repositories after standard repos

#### Scenario: Skill distribution after clone
- **WHEN** repositories are cloned
- **THEN** system runs `copy_skills` to distribute skills to all target directories

#### Scenario: Naming conflict warning
- **WHEN** two sources provide a skill with the same name
- **THEN** system displays warning listing all conflicts

#### Scenario: Shell completion installation
- **WHEN** install completes
- **THEN** system installs shell completion for the current shell (bash/zsh/fish)

#### Scenario: Skip options
- **WHEN** user runs `ai-dev install --skip-npm --skip-bun --skip-repos --skip-skills`
- **THEN** corresponding steps are skipped

#### Scenario: Progress counter display
- **WHEN** installing NPM packages
- **THEN** system shows `[1/N] Installing <package>...` with version info for each

### Requirement: Update command performs comprehensive update
The update command SHALL execute the complete v1 update flow including Claude Code update, package updates, safe repository updates with backup, custom repo updates, and plugin updates.

#### Scenario: Full update flow
- **WHEN** user runs `ai-dev update`
- **THEN** system executes: Claude Code update → NPM packages → Bun packages → uds update → npx skills update → repo updates → custom repo updates → symlink refresh → plugin marketplace → summary

#### Scenario: Safe repository update with backup
- **WHEN** updating a repository that has local changes
- **THEN** system backs up dirty files before `git reset --hard origin/{branch}`

#### Scenario: Repository remote comparison
- **WHEN** updating repositories
- **THEN** system runs `git fetch --all` and compares with remote before updating

#### Scenario: Update summary
- **WHEN** update completes
- **THEN** system displays summary showing which repos had updates and which were already up-to-date

#### Scenario: Missing repository warning
- **WHEN** an expected repository directory does not exist
- **THEN** system displays warning suggesting to run `ai-dev install`

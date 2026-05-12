## ADDED Requirements

### Requirement: Custom template repo structure

A custom template repo SHALL contain project-level AI configuration files intended for direct placement in a target project directory. The repo MUST NOT contain the 5 standard tool directories (agents/, commands/, hooks/, plugins/, skills/) at root level — those belong in a custom tool repo managed via `add-custom-repo`.

#### Scenario: Valid template repo

- **WHEN** a repo contains project configuration files such as:
  - `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `INSTRUCTIONS.md`
  - `.claude/`, `.gemini/`, `.codex/`, `.opencode/`, `.agent/`
  - `.standards/`
  - `.github/`
  - `.editorconfig`, `.gitattributes`, `.gitignore`
  - `atlas.toml`, `dev-docs/`
- **THEN** the repo SHALL be considered a valid custom template

#### Scenario: Template with standard tool directories

- **WHEN** a template repo contains root-level `agents/`, `commands/`, `hooks/`, `plugins/`, or `skills/` directories
- **THEN** the system SHALL display a warning: "Template contains standard tool directories. Consider using `add-custom-repo` for tool distribution."
- **THEN** the system SHALL still proceed with initialization (warning only, not blocking)

### Requirement: Template repo registration

When used with `init-from`, the template repo SHALL be registered in `~/.config/ai-dev/repos.yaml` with a `type: template` field to distinguish it from tool repos.

#### Scenario: Template registered in repos.yaml

- **WHEN** `ai-dev init-from ValorVie/qdm-ai-base` is executed
- **THEN** `repos.yaml` SHALL contain:
  ```yaml
  repos:
    qdm-ai-base:
      url: https://github.com/ValorVie/qdm-ai-base.git
      branch: main
      local_path: ~/.config/qdm-ai-base/
      type: template
      added_at: <ISO-8601>
  ```

#### Scenario: Template repo updated via ai-dev update

- **WHEN** `ai-dev update` is executed
- **THEN** template repos in `repos.yaml` SHALL be pulled/updated alongside tool repos
- **THEN** the system SHALL display a notice if template has new commits: "Template 'qdm-ai-base' has updates. Run `ai-dev init-from --update` in your project to apply."

### Requirement: Custom template format documentation

The system SHALL include documentation at `docs/dev-guide/workflow/custom-template-format.md` describing:

1. The distinction between custom template repos and custom tool repos
2. The expected structure of a custom template repo
3. How to create a new custom template repo
4. The initialization and maintenance workflow

#### Scenario: Documentation exists

- **WHEN** the feature is implemented
- **THEN** `docs/dev-guide/workflow/custom-template-format.md` SHALL exist
- **THEN** the documentation SHALL include examples using qdm-ai-base as reference

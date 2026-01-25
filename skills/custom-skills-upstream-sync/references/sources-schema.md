# Sources Schema

## upstream/sources.yaml

```yaml
sources:
  <source-name>:
    repo: <github-user>/<repo-name>
    branch: main
    local_path: ~/.config/<repo-name>/
    last_synced_commit: <commit-hash>
    last_synced_date: YYYY-MM-DD
    tracked_paths:
      - path/to/track/
    target_dir: <target-in-custom-skills>/
```

## Fields

| Field | Required | Description |
|-------|----------|-------------|
| `repo` | Yes | GitHub repository (user/repo) |
| `branch` | Yes | Branch to track |
| `local_path` | Yes | Local clone path |
| `last_synced_commit` | Yes | Last synced commit hash |
| `last_synced_date` | Yes | Last sync date |
| `tracked_paths` | Yes | Paths to track in repo |
| `target_dir` | Yes | Target directory in custom-skills |

## upstream/<source>/mapping.yaml

```yaml
# Maps upstream files to custom-skills files
<category>:
  <upstream-file>: <custom-skills-file>

# Example
agents:
  build-error-resolver.md: sources/ecc/agents/build-error-resolver.md
  e2e-runner.md: sources/ecc/agents/e2e-runner.md

# Reference-only mappings (not copied, just for comparison)
references:
  agents/architect.md: skills/agents/code-architect.md
```

## upstream/<source>/last-sync.yaml

```yaml
last_synced_commit: abc123def456
last_synced_date: 2026-01-24
synced_by: user
changes_applied:
  - agents/build-error-resolver.md
  - commands/build-fix.md
```

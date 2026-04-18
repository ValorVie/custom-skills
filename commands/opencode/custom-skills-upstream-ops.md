# Upstream Ops | 上游操作

Unified upstream repo operations.

## Usage

```
/custom-skills-upstream-ops [audit | uds-check | overlap <target> | maintenance <sub>] [--options]
```

Default: `audit`.

## Modes

- **audit** — commit drift + sync recommendations (AI workflow)
- **uds-check** — UDS file-level SHA-256 drift (Python script)
- **overlap** — any repo vs this project overlap detection
- **maintenance** — update-last-sync / archive-reports / list-orphans

See full docs: `skills/custom-skills-upstream-ops/SKILL.md`.

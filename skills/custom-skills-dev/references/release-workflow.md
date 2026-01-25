# Release Workflow Reference

Version release process for custom-skills (ai-dev CLI).

## Table of Contents

- [Version Numbering](#version-numbering)
- [Release Checklist](#release-checklist)
- [CHANGELOG Format](#changelog-format)
- [Git Commands](#git-commands)

---

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

| Version | When to Bump | Example |
|---------|--------------|---------|
| MAJOR (X.0.0) | Breaking changes | CLI flag renamed, config format changed |
| MINOR (0.X.0) | New features | New command, new target tool |
| PATCH (0.0.X) | Bug fixes | Fix copy logic, fix TUI bug |

---

## Release Checklist

### Pre-Release

- [ ] All changes committed
- [ ] All tests pass manually
- [ ] No uncommitted changes in working directory

### Version Update

- [ ] Update `version` in `pyproject.toml`
- [ ] Update CHANGELOG.md with release date

### Commit and Tag

- [ ] Commit version bump
- [ ] Create Git tag
- [ ] Push commits and tags

### Post-Release

- [ ] Verify installation: `uv tool upgrade ai-dev`
- [ ] Test key commands work

---

## CHANGELOG Format

Follow [Keep a Changelog](https://keepachangelog.com/):

```markdown
## [0.X.Y] - YYYY-MM-DD

### Added
- **Feature Category**
  - Description of new feature

### Changed
- **Category**
  - Description of change

### Fixed
- Description of bug fix

### Documentation
- Documentation updates
```

### Categories (in order)

1. Added - New features
2. Changed - Changes in existing functionality
3. Deprecated - Soon-to-be removed features
4. Removed - Removed features
5. Fixed - Bug fixes
6. Security - Security fixes
7. Documentation - Doc-only changes

---

## Git Commands

### Standard Release

```bash
# 1. Ensure clean state
git status

# 2. Update version in pyproject.toml
# Edit pyproject.toml: version = "0.X.Y"

# 3. Update CHANGELOG.md
# Add entry for new version with today's date

# 4. Commit
git add pyproject.toml CHANGELOG.md
git commit -m "chore(release): v0.X.Y"

# 5. Tag
git tag v0.X.Y

# 6. Push
git push && git push --tags
```

### Hotfix Release

```bash
# 1. Fix the bug
# 2. Bump PATCH version
# 3. Update CHANGELOG
# 4. Commit with fix type
git commit -m "fix(component): 修復問題描述"

# 5. Commit version bump
git commit -m "chore(release): v0.X.Y"

# 6. Tag and push
git tag v0.X.Y
git push && git push --tags
```

---

## Example CHANGELOG Entry

```markdown
## [0.7.0] - 2026-01-24

### Added

- **ECC Hooks Plugin 管理**
  - 新增 `ai-dev hooks install` 安裝或更新 ECC Hooks Plugin
  - 新增 `ai-dev hooks uninstall` 移除 ECC Hooks Plugin
  - 新增 `ai-dev hooks status` 顯示安裝狀態

### Changed

- **ECC Hooks 結構重構 (Breaking Change)**
  - `sources/ecc/hooks/` 重構為符合 Claude Code 官方 plugin 規範

---
```

---

## Commit Message Format

Use Conventional Commits with 繁體中文:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types for Releases

| Type | Usage |
|------|-------|
| `feat` | New feature |
| `fix` | Bug fix |
| `chore` | Maintenance (version bump) |
| `docs` | Documentation only |

### Examples

```bash
# Feature release
git commit -m "feat(hooks): 新增 ECC Hooks Plugin 管理功能"

# Bug fix release
git commit -m "fix(tui): 修正資源名稱包含特殊字元時的錯誤"

# Version bump
git commit -m "chore(release): v0.7.0"
```

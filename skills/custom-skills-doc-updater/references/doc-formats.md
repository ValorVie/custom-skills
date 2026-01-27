# Documentation Format Reference

Detailed format specifications for each documentation type in custom-skills.

## Table of Contents

- [README.md (Root)](#readmemd-root)
- [CHANGELOG.md](#changelogmd)
- [openspec/project.md](#openspecprojectmd)
- [Module READMEs](#module-readmes)
- [docs/ Directory](#docs-directory)

---

## README.md (Root)

### Structure

```markdown
# AI 開發環境設定工具 (ai-dev)

[Brief description]

## 安裝

### 前置需求
[Prerequisites]

### 安裝 Claude Code
[Installation instructions]

### 安裝 CLI 工具
[CLI installation]

## 使用方式

### [Command Name] (verb)
[Description and examples]

#### 可選參數
| 參數 | 說明 |
|------|------|
| `--flag` | Description |

## 指令總覽

| 指令 | 說明 |
|------|------|
| `ai-dev command` | Description |

## 開發
[Development instructions]

## 資源來源
[Resource sources table]

## 未來計畫
[Future plans]
```

### Key Sections to Maintain

1. **Installation section**: Must match actual installation process
2. **Command table**: Must list all available commands
3. **Resource sources table**: Must reflect current integrations
4. **Version in examples**: Must use current version

---

## CHANGELOG.md

### Format (Keep a Changelog)

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [X.Y.Z] - YYYY-MM-DD

### Added
- **Feature Category**
  - Detailed description of new feature

### Changed
- **Category (Breaking Change)**
  - Description of what changed

### Fixed
- Description of bug fix

### Documentation
- Documentation updates

---

## [Previous Version] - Date
...
```

### Categories (in order)

1. `Added` - New features
2. `Changed` - Changes in existing functionality
3. `Deprecated` - Soon-to-be removed features
4. `Removed` - Removed features
5. `Fixed` - Bug fixes
6. `Security` - Security fixes
7. `Documentation` - Doc-only changes

### Guidelines

- Use **bold** for feature categories
- Use nested bullets for details
- Add `(Breaking Change)` suffix when applicable
- Separate versions with `---`
- Keep unreleased changes at top as `## [Unreleased]`

---

## openspec/project.md

### Structure

```markdown
# Project Context

## Purpose
[Why this project exists]

## Tech Stack

### 主要技術
[Primary technologies]

### 支援的 AI 工具
[Supported AI tools with links]

### 整合的標準來源
[Integrated standard sources with links]

## Project Conventions

### Code Style
[Coding standards]

### Architecture Patterns
[Directory structure and patterns]

### Testing Strategy
[How to test]

### Git Workflow
[Branch strategy, commit format]

## Domain Context
[Key concepts and terminology]

## Important Constraints
[Rules and limitations]

## External Dependencies
[Required tools and services]
```

### Update Triggers

- New AI tool support
- New upstream integration
- Architecture changes
- Workflow changes
- New constraints

---

## Module READMEs

### sources/ecc/README.md

```markdown
# Everything Claude Code (ECC) 資源

來源: [repo-link]
整合日期: YYYY-MM-DD
授權: License

## 概述
[What this contains]

## 目錄結構
```
[Directory tree]
```

## [Resource Type]

| Name | Description |
|------|-------------|
| `name` | Description |

## 安裝方式
[Installation methods]

## 注意事項
[Important notes]
```

### upstream/README.md

```markdown
# Upstream Tracking | 上游追蹤

[Brief description]

## 目錄結構
[Directory structure]

## 檔案說明
[File descriptions]

## 使用流程
[Workflow diagrams using ASCII]

## 常用指令
[Common commands with examples]

## 相關 Skills
[Related skills]
```

### commands/claude/README.md

```markdown
# Claude Code Custom Commands

## Available Commands | 可用命令

### [Category] | 類別名稱

| Command | Description | 說明 |
|---------|-------------|------|
| [`/cmd`](./cmd.md) | English desc | 中文說明 |

## Commands vs Skills | 命令與技能
[Comparison table]

## Adding Custom Commands | 新增自訂命令
[How to add new commands]
```

---

## docs/ Directory

### AI開發環境設定指南.md

Comprehensive setup guide. Update when:
- Installation process changes
- New tools added
- Configuration options change

### AI輔助開發的本質原理.md

Conceptual document. Update when:
- Core concepts evolve
- New patterns introduced

### Skill-Command-Agent差異說明.md

Concept clarification. Update when:
- New entity types added
- Behavior patterns change

### dev-guide/DEVELOPMENT-WORKFLOW.md

OpenSpec 開發工作流程指南。結構：

```markdown
# 開發工作流程指南

## 快速參考（熟練開發者）
[Command reference table]

### 完整 TDD 流程
[Flow diagram]

### 常用命令速查
[CLI commands]

## 完整開發流程

### Phase 0: 對話探索
### Phase 1: 調研目標
### Phase 2: 建立提案
### Phase 3: 建立規格
### Phase 4: 實作
### Phase 5: 測試
### Phase 6: 驗證
### Phase 7: 歸檔

## 附錄
[FAQ, command overview, CLI commands, directory structure]
```

Update when:
- OpenSpec workflow changes
- New opsx commands added
- TDD/testing workflow changes

### dev-guide/GIT-WORKFLOW.md

Git 分支與 PR 流程指南。結構：

```markdown
# Git 工作流程指南

## 快速參考
[Flow diagram and step table]

## 完整流程說明

### Step 1: 建立開發分支
### Step 2: 開發
### Step 3: 同步主線
### Step 4: 建立 PR
### Step 5: 確認 PR
### Step 6: Code Review
### Step 7: 合併 PR
### Step 8: 清理分支

## 常見問題
[FAQ]

## 相關命令
[Command table]
```

Update when:
- Git workflow changes
- PR process changes
- Branch naming conventions change

---

## Common Patterns

### Bilingual Headers

```markdown
## Section Name | 中文名稱
```

### Tables with Bilingual Content

```markdown
| Command | Description | 說明 |
|---------|-------------|------|
| `/cmd`  | English     | 中文 |
```

### Code Blocks

Always specify language:
```markdown
```bash
# Command
```

```yaml
# Configuration
```

```python
# Script
```
```

### Links

- Use relative paths within project
- Use full URLs for external resources
- Verify links after updates

### ASCII Diagrams

For workflows, use box-drawing characters:
```
┌─────────────────┐
│     Step 1      │
└────────┬────────┘
         ↓
┌─────────────────┐
│     Step 2      │
└─────────────────┘
```

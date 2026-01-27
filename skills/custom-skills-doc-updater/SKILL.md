---
name: doc-updater
description: |
  Maintain and update custom-skills project documentation for consistency and accuracy.
  Use when: (1) code changes affect documented features, (2) adding new skills/commands/agents,
  (3) version releases, (4) structural changes to the project, (5) user asks to update docs,
  (6) changelog needs updating.
  Triggers: "update docs", "sync documentation", "update README", "update changelog",
  "documentation audit", "doc sync", "更新文檔", "同步文件", "文檔檢查".
---

# Documentation Updater

Update and maintain custom-skills project documentation to ensure consistency across all files.

---

## Workflow

### Step 1: Identify Changes

```bash
git diff --name-only HEAD~1     # Recent changes
git log --oneline -5            # Recent commits
```

### Step 2: Determine Affected Documents

根據變更類型，使用下方的**變更類型對照表**確定需要更新的文件。

### Step 3: Read Each Target Document

**必須先讀取每個需要更新的文件**，確認：
- 目前內容是否已涵蓋變更
- 需要更新的具體位置
- 格式是否符合規範

### Step 4: Update Documents

遵循 [references/doc-formats.md](references/doc-formats.md) 的格式規範。

### Step 5: Verify Consistency

- [ ] 版本號一致
- [ ] 功能列表一致
- [ ] 連結有效
- [ ] 表格已更新

---

## 變更類型對照表

### 新增 Skill

| 文件 | 更新內容 |
|------|----------|
| `CHANGELOG.md` | 新增項目到 `[Unreleased]` 或對應版本 |
| `skills/README.md` | 如有總覽表，新增 skill 列表 |

### 新增 Agent

| 文件 | 更新內容 |
|------|----------|
| `CHANGELOG.md` | 新增項目 |
| `agents/claude/README.md` | 新增到 Built-in Agents 表格 |
| `docs/Skill-Command-Agent差異說明.md` | 新增到「附錄：內建 Agents 清單」 |

### 新增 Command

| 文件 | 更新內容 |
|------|----------|
| `CHANGELOG.md` | 新增項目 |
| `commands/claude/README.md` | 新增到對應類別的表格 |

### 新增 Command 系列（如 opsx 系列）

| 文件 | 更新內容 |
|------|----------|
| `CHANGELOG.md` | 新增整個系列的說明 |
| `commands/claude/README.md` | 新增類別區塊和表格 |
| `docs/Skill-Command-Agent差異說明.md` | 如有新概念，更新說明 |

### 上游整合

| 文件 | 更新內容 |
|------|----------|
| `CHANGELOG.md` | 新增整合項目 |
| `upstream/README.md` | 更新「整合決定記錄」區塊 |
| 相關模組 README | 如 `agents/claude/README.md`、`skills/README.md` |

### CLI 功能變更

| 文件 | 更新內容 |
|------|----------|
| `README.md` | 更新指令說明、參數表格 |
| `CHANGELOG.md` | 新增變更項目 |

### 版本發布

| 文件 | 更新內容 |
|------|----------|
| `pyproject.toml` | 更新 version 欄位 |
| `CHANGELOG.md` | 將 `[Unreleased]` 改為版本號並加日期 |
| `README.md` | 確認功能說明反映當前版本 |

### 工作流程變更

| 文件 | 更新內容 |
|------|----------|
| `docs/dev-guide/DEVELOPMENT-WORKFLOW.md` | 更新開發流程、opsx 命令 |
| `docs/dev-guide/GIT-WORKFLOW.md` | 更新 Git 流程、PR 流程 |
| `CHANGELOG.md` | 記錄工作流程變更 |

### 架構變更

| 文件 | 更新內容 |
|------|----------|
| `openspec/project.md` | 更新專案結構、慣例 |
| `docs/dev-guide/*.md` | 更新開發指南 |
| `CHANGELOG.md` | 記錄架構變更 |

---

## 文件總覽

### Priority 1: 核心文件（必檢）

| 文件 | 用途 | 更新時機 |
|------|------|----------|
| `README.md` | 專案總覽、安裝、CLI 使用 | CLI 變更、新功能、版本發布 |
| `CHANGELOG.md` | 版本歷史 | 每次發布、重大變更 |
| `openspec/project.md` | 專案上下文、慣例 | 架構變更、技術棧更新 |

### Priority 2: 功能文件

| 文件 | 用途 | 更新時機 |
|------|------|----------|
| `docs/AI開發環境設定指南.md` | 使用者設定指南 | 安裝流程變更 |
| `docs/AI輔助開發的本質原理.md` | 設計理念 | 概念性變更 |
| `docs/Skill-Command-Agent差異說明.md` | 概念說明 | **新增 Agent 時必須更新** |
| `docs/dev-guide/DEVELOPMENT-WORKFLOW.md` | OpenSpec 開發工作流程 | 工作流程變更、新增 opsx 命令 |
| `docs/dev-guide/GIT-WORKFLOW.md` | Git 分支與 PR 流程 | Git 工作流程變更 |

### Priority 3: 模組 README

| 目錄 | README 用途 | 更新時機 |
|------|-------------|----------|
| `sources/ecc/` | ECC 資源整合狀態 | ECC 整合變更 |
| `upstream/` | 上游追蹤系統 | 上游整合決定 |
| `commands/claude/` | 可用 slash commands | **新增 Command 時必須更新** |
| `agents/claude/` | Agent 規格 | **新增 Agent 時必須更新** |
| `skills/` | Skills 總覽 | 新增 Skill 時視情況更新 |

---

## 常見遺漏提醒

### 新增 Agent 時

容易遺漏的文件：
1. ⚠️ `docs/Skill-Command-Agent差異說明.md` - 「附錄：內建 Agents 清單」區塊
2. ⚠️ `agents/claude/README.md` - Built-in Agents 表格和版本歷史

### 新增 Command 系列時

容易遺漏的文件：
1. ⚠️ `commands/claude/README.md` - 需要新增完整的類別區塊
2. ⚠️ 如有新概念，需更新 `docs/Skill-Command-Agent差異說明.md`

### 上游整合時

容易遺漏的文件：
1. ⚠️ `upstream/README.md` - 「整合決定記錄」區塊
2. ⚠️ 相關模組的 README（如新增 agent 需更新 agents/claude/README.md）

---

## 格式規範

### CHANGELOG 格式

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- **Feature Category**
  - 詳細描述

### Changed
- **Category (Breaking Change)**
  - 變更描述

### Removed
- 移除項目描述

### Fixed
- 修復描述
```

### 表格格式（雙語）

```markdown
| Command | Description | 說明 |
|---------|-------------|------|
| [`/cmd`](./cmd.md) | English desc | 中文說明 |
```

### 版本歷史格式

```markdown
## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.2.0 | 2026-01-26 | Added new-feature |
| 1.1.0 | 2026-01-21 | Previous change |
```

---

## 語言規範

所有文件使用**繁體中文**，保留英文技術術語：
- Skill, Command, Agent, Hook, Plugin
- CLI, TUI, MCP, API
- Git, GitHub, upstream

---

## 檢查清單

執行文件更新前，確認以下事項：

### 新增 Skill
- [ ] `CHANGELOG.md` 已更新

### 新增 Agent
- [ ] `CHANGELOG.md` 已更新
- [ ] `agents/claude/README.md` 已更新（表格 + 版本歷史）
- [ ] `docs/Skill-Command-Agent差異說明.md` 已更新（Agent 清單）

### 新增 Command
- [ ] `CHANGELOG.md` 已更新
- [ ] `commands/claude/README.md` 已更新

### 新增 Command 系列
- [ ] `CHANGELOG.md` 已更新
- [ ] `commands/claude/README.md` 已新增類別區塊

### 上游整合
- [ ] `CHANGELOG.md` 已更新
- [ ] `upstream/README.md` 已更新（整合決定記錄）
- [ ] 相關模組 README 已更新

### 工作流程變更
- [ ] `docs/dev-guide/DEVELOPMENT-WORKFLOW.md` 已更新（如涉及開發流程）
- [ ] `docs/dev-guide/GIT-WORKFLOW.md` 已更新（如涉及 Git 流程）
- [ ] `CHANGELOG.md` 已更新

### 版本發布
- [ ] `pyproject.toml` 版本號已更新
- [ ] `CHANGELOG.md` 日期已填寫
- [ ] `README.md` 功能說明正確

---

## References

詳細格式規範請參考 [references/doc-formats.md](references/doc-formats.md)。

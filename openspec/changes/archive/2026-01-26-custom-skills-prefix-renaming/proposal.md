## Why

專案中有數個僅用於 custom-skills 專案本身的工具（Skills 和 Commands），但命名不一致：部分已有 `custom-skills-*` 前綴（如 `custom-skills-upstream-sync`），部分則沒有（如 `git-commit-custom`、`tool-overlap-analyzer`）。這造成辨識困難，無法一眼區分「專案專屬工具」與「通用可移植工具」。

統一前綴命名可：
1. 明確標示專案專屬工具，方便維護
2. 避免與上游或其他專案的同名工具混淆
3. 提供一致的命名慣例

## What Changes

### Skills 重命名
- `skills/git-commit-custom/` → `skills/custom-skills-git-commit/` **BREAKING**
- `skills/tool-overlap-analyzer/` → `skills/custom-skills-tool-overlap-analyzer/` **BREAKING**

### Commands 重命名
- `commands/claude/git-commit.md` → `commands/claude/custom-skills-git-commit.md` **BREAKING**
- `commands/antigravity/git-commit.md` → `commands/antigravity/custom-skills-git-commit.md` **BREAKING**
- `commands/claude/upstream-sync.md` → `commands/claude/custom-skills-upstream-sync.md` **BREAKING**

### 引用更新
更新所有引用上述工具的檔案：
- `README.md`
- `commands/claude/README.md`
- `upstream/README.md`
- `docs/AI開發環境設定指南.md`
- `docs/dev-guide/copy-architecture.md`
- `docs/report/tool-overlap-analysis-2026-01-26.md`
- `skills/custom-skills-dev/SKILL.md`
- `skills/custom-skills-upstream-sync/SKILL.md`
- `skills/custom-skills-upstream-compare/SKILL.md`
- `skills/custom-skills-git-commit/pr-analyze.md` (原 git-commit-custom)

### 不修改的檔案
- `CHANGELOG.md` - 歷史記錄保留原名
- `openspec/changes/archive/*` - 歸檔文件保留原名
- `openspec/specs/*` - 規格文件保留原名

## Capabilities

### New Capabilities

無新增功能，僅重命名。

### Modified Capabilities

無規格變更，僅重命名。

## Impact

### Breaking Changes

| 原命令 | 新命令 |
|--------|--------|
| `/git-commit` | `/custom-skills-git-commit` |
| `/upstream-sync` | `/custom-skills-upstream-sync` |

使用者需更新習慣使用的命令名稱。

### 受影響檔案

| 類型 | 數量 |
|------|------|
| 需重命名的目錄/檔案 | 5 |
| 需更新引用的檔案 | 12 |
| 估計修改點 | ~80 處 |

### 遷移指引

```bash
# 舊命令 → 新命令
/git-commit → /custom-skills-git-commit
/upstream-sync → /custom-skills-upstream-sync
```

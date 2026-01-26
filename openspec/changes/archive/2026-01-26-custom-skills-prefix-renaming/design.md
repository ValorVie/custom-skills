## Context

custom-skills 專案包含兩類工具：
1. **通用可移植工具**：可複製到其他專案使用（如 `commit-standards`、`testing-guide`）
2. **專案專屬工具**：僅用於維護 custom-skills 本身（如 `git-commit-custom`、`upstream-sync`）

目前專案專屬工具的命名不一致：
- 已有前綴：`custom-skills-dev`、`custom-skills-upstream-sync`、`custom-skills-upstream-compare`、`custom-skills-doc-updater`
- 未有前綴：`git-commit-custom`、`tool-overlap-analyzer`、`upstream-sync` (command)、`git-commit` (command)

## Goals / Non-Goals

**Goals:**
- 所有專案專屬工具統一使用 `custom-skills-*` 前綴
- 更新所有功能性引用，確保重命名後工具正常運作
- 更新相關文檔保持一致性

**Non-Goals:**
- 不修改歷史記錄（CHANGELOG.md 保留原名）
- 不修改歸檔文件（openspec/changes/archive/*）
- 不修改 openspec/specs/*（這些是功能規格，非工具名稱規格）
- 不新增別名或向後相容機制

## Decisions

### 1. 命名格式

**決策**：使用 `custom-skills-<function>` 格式

| 原名稱 | 新名稱 | 理由 |
|--------|--------|------|
| `git-commit-custom` | `custom-skills-git-commit` | 前綴統一在前，`-custom` 後綴移除 |
| `tool-overlap-analyzer` | `custom-skills-tool-overlap-analyzer` | 新增前綴 |

**替代方案**：
- `cs-*` 縮寫：過於簡短，不夠清晰
- `project-*`：不夠具體
- 保持 `*-custom` 後綴：與現有 `custom-skills-*` 慣例不一致

### 2. 修改範圍

**決策**：區分「必須修改」和「歷史保留」

| 類別 | 處理方式 |
|------|----------|
| 功能性引用（調用、文檔說明） | 必須更新 |
| CHANGELOG.md | 保留原名（歷史記錄） |
| openspec/changes/archive/* | 保留原名（歸檔文件） |
| openspec/specs/* | 保留原名（功能規格非工具名） |

**理由**：歷史記錄應反映當時實際狀態，不應回溯修改。

### 3. 執行順序

**決策**：先重命名檔案/目錄，再更新引用

```
1. 重命名 Skills 目錄（mv）
2. 更新 Skills 內部的 name 欄位
3. 重命名 Commands 檔案（mv）
4. 更新 Commands 內部的引用
5. 更新其他文檔引用
6. 驗證所有連結有效
```

**理由**：先完成重命名可避免引用更新時指向不存在的路徑。

## Risks / Trade-offs

### Breaking Changes

**[風險]** 使用者習慣的命令名稱改變
- `/git-commit` → `/custom-skills-git-commit`
- `/upstream-sync` → `/custom-skills-upstream-sync`

**[緩解]** 在 CHANGELOG 中詳細記錄遷移指引

### 遺漏引用

**[風險]** 可能遺漏某些引用導致文檔不一致

**[緩解]** 使用 grep 搜尋所有引用，執行後再次驗證

### 命令變長

**[Trade-off]** 新命令名稱較長（`/custom-skills-git-commit` vs `/git-commit`）

**[接受]** 清晰度優先於簡短，專案專屬工具使用頻率較低

## File Modification Plan

### Phase 1: Skills 重命名

```bash
# 1.1 重命名目錄
mv skills/git-commit-custom skills/custom-skills-git-commit
mv skills/tool-overlap-analyzer skills/custom-skills-tool-overlap-analyzer

# 1.2 更新 SKILL.md 的 name 欄位
# skills/custom-skills-git-commit/SKILL.md: name: git-commit-custom → custom-skills-git-commit
# skills/custom-skills-tool-overlap-analyzer/SKILL.md: name: tool-overlap-analyzer → custom-skills-tool-overlap-analyzer
```

### Phase 2: Commands 重命名

```bash
# 2.1 重命名檔案
mv commands/claude/git-commit.md commands/claude/custom-skills-git-commit.md
mv commands/antigravity/git-commit.md commands/antigravity/custom-skills-git-commit.md
mv commands/claude/upstream-sync.md commands/claude/custom-skills-upstream-sync.md

# 2.2 更新 Commands 內部引用
# custom-skills-git-commit.md: 調用 skill 名稱更新
# custom-skills-upstream-sync.md: 腳本路徑更新（如需要）
```

### Phase 3: 文檔引用更新

| 檔案 | 更新內容 |
|------|----------|
| README.md | `/upstream-sync` → `/custom-skills-upstream-sync` |
| commands/claude/README.md | 命令列表更新 |
| upstream/README.md | 所有 `/upstream-sync` 引用 |
| docs/AI開發環境設定指南.md | 命令列表更新 |
| docs/dev-guide/copy-architecture.md | `/upstream-sync` 引用 |
| docs/report/tool-overlap-analysis-2026-01-26.md | 工具名稱引用 |
| skills/custom-skills-dev/SKILL.md | `/upstream-sync` 引用 |
| skills/custom-skills-upstream-sync/SKILL.md | 腳本路徑 |
| skills/custom-skills-upstream-compare/SKILL.md | `/upstream-sync` 引用 |
| skills/custom-skills-git-commit/pr-analyze.md | 路徑引用 |

### Phase 4: 驗證

```bash
# 確認無殘留舊名引用（排除 archive 和 CHANGELOG）
grep -r "git-commit-custom\|/git-commit\|/upstream-sync" --include="*.md" \
  | grep -v "archive/" | grep -v "CHANGELOG"
```

---
name: custom-skills-doc-updater
description: |
  Maintain and update custom-skills project documentation for consistency and accuracy.
  Use when: (1) code changes affect documented features, (2) adding new skills/commands/agents,
  (3) version releases, (4) structural changes to the project, (5) user asks to update docs,
  (6) changelog needs updating.
  Triggers: "update docs", "sync documentation", "update README", "update changelog",
  "documentation audit", "doc sync", "更新文檔", "同步文件", "文檔檢查", "/doc-updater".
---

# Documentation Updater

智能化文件更新工作流程，確保程式碼變更與文件同步。

---

## Workflow Overview

```
Phase 1: 變更收集 → Phase 2: 變更分類 → Phase 3: 文件探索 → Phase 4: 影響分析 → Phase 5: 文件更新 → Phase 6: 驗證
```

---

## Phase 1: 變更收集

### Step 1.1: 確認分析範圍

**若使用者未指定範圍，使用 AskUserQuestion 詢問：**

```
問題：您希望分析多少個最近的 commits？
選項：
- 最近 1 個 commit（預設）
- 最近 5 個 commits
- 最近 10 個 commits
- 自訂範圍（輸入 commit hash 或分支比較）
```

### Step 1.2: 收集變更資料

根據使用者選擇執行：

```bash
# 查看最近 N 個 commits
git log --oneline -N

# 查看變更的檔案
git diff --name-only HEAD~N

# 查看詳細變更摘要
git log --stat HEAD~N..HEAD
```

**替代方案（比較分支）：**
```bash
git diff --name-only main...HEAD
git log --oneline main...HEAD
```

### Step 1.3: 整理變更清單

輸出格式：
```markdown
## 變更摘要

**分析範圍**: HEAD~5..HEAD (5 commits)

### 變更的檔案
- plugins/ecc-hooks/README.md
- plugins/ecc-hooks/hooks/hooks.json
- openspec/changes/xxx/tasks.md
- ...

### Commit 摘要
- abc1234: feat: 新增 PHP hooks 支援
- def5678: fix: 修正格式化問題
```

---

## Phase 2: 變更分類

### Step 2.1: 自動識別變更類型

根據變更的檔案路徑和內容，識別變更類型：

| 檔案路徑模式 | 變更類型 |
|-------------|---------|
| `skills/**/*.md` | Skill 變更 |
| `agents/**/*.md` | Agent 變更 |
| `commands/**/*.md` | Command 變更 |
| `plugins/**/*` | Plugin 變更 |
| `script/**/*.py` | CLI 功能變更 |
| `pyproject.toml` (version) | 版本發布 |
| `openspec/specs/**/*` | Spec 變更 |
| `upstream/**/*` | 上游整合 |
| `sources/**/*` | 資源整合 |
| `docs/**/*` | 文件變更（可能需要交叉更新） |
| `.standards/**/*` | 標準規範變更 |

### Step 2.2: 提取關鍵字

從變更中提取關鍵字用於後續文件搜尋：

1. **從檔案名稱提取**：`ecc-hooks` → 搜尋關鍵字
2. **從 commit message 提取**：`新增 PHP hooks` → `PHP`, `hooks`
3. **從新增/修改的內容提取**：function names, class names, feature names

### Step 2.3: 輸出分類結果

```markdown
## 變更分類

| 類型 | 數量 | 關鍵項目 |
|------|------|----------|
| Plugin 變更 | 3 | ecc-hooks |
| CLI 變更 | 1 | derive-tests |
| Spec 變更 | 2 | hook-testing, code-quality-hooks |

**提取的關鍵字**: `ecc-hooks`, `PHP`, `hooks`, `code-quality`, `testing`
```

---

## Phase 3: 文件探索

### Step 3.1: 優先檢查核心文件

**必檢文件（依優先順序）：**

1. `CHANGELOG.md` - 版本歷史（幾乎所有變更都需要）
2. `README.md` - 專案總覽
3. `openspec/config.yaml` - 專案上下文（舊版為 `openspec/project.md`，若存在也應檢查）
4. `docs/**/*.md` - 文件資料夾

### Step 3.2: 使用關鍵字搜尋相關文件

對每個提取的關鍵字，搜尋專案中的相關文件：

```bash
# 搜尋檔案名稱包含關鍵字
find . -name "*keyword*" -type f

# 搜尋檔案內容包含關鍵字
grep -rl "keyword" --include="*.md" .

# 搜尋 README 文件
find . -name "README.md" -type f
```

**使用 Grep 工具搜尋：**
- 搜尋 `ecc-hooks` 在所有 `.md` 文件中的出現
- 搜尋 `PHP` 在文件中的相關說明
- 搜尋功能名稱在哪些文件有記錄

### Step 3.3: 建立文件關聯圖

```markdown
## 文件關聯分析

### 關鍵字: `ecc-hooks`
找到相關文件：
- `README.md` (Line 599-627: Claude Code Plugin 區塊)
- `plugins/ecc-hooks/README.md` (主要文件)
- `docs/AI開發環境設定指南.md` (Line 514-541: Plugin 安裝說明)
- `CHANGELOG.md` (Line 136-138: 0.9.7 版本記錄)

### 關鍵字: `PHP`
找到相關文件：
- `docs/dev-guide/workflow/CODE-QUALITY-TOOLS.md` (PHP 工具安裝)
- `plugins/ecc-hooks/README.md` (PHP formatting hooks)
```

---

## Phase 4: 影響分析

### Step 4.1: 對照變更類型與文件

使用以下對照表確定需要更新的文件：

#### Plugin 變更
| 文件 | 更新內容 | 必要性 |
|------|----------|--------|
| `CHANGELOG.md` | 新增/修改項目 | **必要** |
| `plugins/<name>/README.md` | 功能說明、安裝方式 | **必要** |
| `README.md` | 若涉及使用方式變更 | 視情況 |
| `docs/AI開發環境設定指南.md` | 若涉及安裝流程 | 視情況 |

#### Skill 變更
| 文件 | 更新內容 | 必要性 |
|------|----------|--------|
| `CHANGELOG.md` | 新增項目 | **必要** |
| `skills/README.md` | 如有 skill 清單 | 視情況 |

#### Agent 變更
| 文件 | 更新內容 | 必要性 |
|------|----------|--------|
| `CHANGELOG.md` | 新增項目 | **必要** |
| `agents/claude/README.md` | Agent 清單表格 | **必要** |
| `docs/Skill-Command-Agent差異說明.md` | 「附錄：內建 Agents 清單」 | **必要** |

#### Command 變更
| 文件 | 更新內容 | 必要性 |
|------|----------|--------|
| `CHANGELOG.md` | 新增項目 | **必要** |
| `commands/claude/README.md` | Command 清單表格 | **必要** |

#### CLI 功能變更
| 文件 | 更新內容 | 必要性 |
|------|----------|--------|
| `CHANGELOG.md` | 新增/修改項目 | **必要** |
| `README.md` | 指令說明、參數表格 | **必要** |

#### 版本發布
| 文件 | 更新內容 | 必要性 |
|------|----------|--------|
| `pyproject.toml` | version 欄位 | **必要** |
| `CHANGELOG.md` | 日期、版本號 | **必要** |
| `README.md` | 確認功能說明 | 視情況 |

### Step 4.2: 版本一致性檢查

檢查以下位置的版本號是否一致：
- `pyproject.toml` → `version`
- `plugins/<name>/plugin.json` → `version`
- `plugins/<name>/package.json` → `version`（如有）

### Step 4.3: 生成影響報告

```markdown
## 影響分析報告

### 需要更新的文件

| 文件 | 原因 | 優先級 | 狀態 |
|------|------|--------|------|
| `CHANGELOG.md` | 新增 ecc-hooks 測試框架 | P1 | ⬜ 待更新 |
| `plugins/ecc-hooks/package.json` | 版本同步 (1.0.0 → 1.1.0) | P1 | ⬜ 待更新 |
| `README.md` | 功能無變更 | - | ✅ 無需更新 |
| `docs/dev-guide/workflow/CODE-QUALITY-TOOLS.md` | 功能無變更 | - | ✅ 無需更新 |

### 版本一致性
- `pyproject.toml`: 1.0.4
- `plugins/ecc-hooks/plugin.json`: 1.1.0
- `plugins/ecc-hooks/package.json`: 1.0.0 ⚠️ **不一致**
```

---

## Phase 5: 文件更新

### Step 5.1: 依優先級更新文件

1. **P1 - 必要更新**：先處理 CHANGELOG.md 和版本同步
2. **P2 - 重要更新**：功能文件、README
3. **P3 - 可選更新**：參考文件、次要文件

### Step 5.2: 更新前必須讀取

**重要**：更新任何文件前，必須先使用 Read 工具讀取該文件，確認：
- 目前內容
- 需要插入/修改的位置
- 格式規範

### Step 5.3: 遵循格式規範

#### CHANGELOG 格式
```markdown
## [Unreleased]

### Added
- **功能類別**
  - 詳細描述
  - 子項目說明

### Changed
- **Breaking Change 類別**
  - 變更描述
  - 遷移指引

### Fixed
- 修復描述

### Removed
- 移除項目描述
```

#### 版本歷史表格格式
```markdown
## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2026-01-28 | Added feature X |
```

---

## Phase 6: 驗證

### Step 6.1: 驗證清單

完成更新後，逐項確認：

```markdown
## 更新驗證清單

### 文件更新狀態
- [x] `CHANGELOG.md` - 已新增 ecc-hooks 測試框架記錄
- [x] `plugins/ecc-hooks/package.json` - 版本同步至 1.1.0
- [ ] `README.md` - 無需更新

### 版本一致性（更新後）
| 位置 | 版本 | 狀態 |
|------|------|------|
| `pyproject.toml` | 1.0.4 | ✓ |
| `plugins/ecc-hooks/plugin.json` | 1.1.0 | ✓ |
| `plugins/ecc-hooks/package.json` | 1.1.0 | ✓ |

### 交叉引用
- [x] 功能列表在各文件中一致
- [x] 連結有效
- [x] 表格已更新
```

### Step 6.2: 輸出最終摘要

```markdown
## 文件更新摘要

**分析範圍**: HEAD~5..HEAD

### 已更新
| 文件 | 更新內容 |
|------|----------|
| `CHANGELOG.md` | 新增 ECC Hooks Plugin 測試框架記錄 |
| `plugins/ecc-hooks/package.json` | 版本同步至 1.1.0 |

### 無需更新
| 文件 | 原因 |
|------|------|
| `README.md` | 主要功能無變更 |
| `docs/*` | 與此次變更無關 |

### 版本一致性
✓ 所有版本號已同步
```

---

## 快速參考

### 常見遺漏提醒

#### 新增 Agent 時
- ⚠️ `docs/Skill-Command-Agent差異說明.md` - 「附錄：內建 Agents 清單」
- ⚠️ `agents/claude/README.md` - Built-in Agents 表格

#### 新增 Command 系列時
- ⚠️ `commands/claude/README.md` - 需要新增完整的類別區塊

#### 上游整合時
- ⚠️ `upstream/README.md` - 「整合決定記錄」區塊

#### Plugin 變更時
- ⚠️ 版本號同步（plugin.json 與 package.json）

### 語言規範

所有文件使用**繁體中文**，保留英文技術術語：
- Skill, Command, Agent, Hook, Plugin
- CLI, TUI, MCP, API
- Git, GitHub, upstream

---

## 參數說明

skill 可接受以下參數：

| 參數 | 說明 | 範例 |
|------|------|------|
| 無參數 | 詢問分析範圍 | `/doc-updater` |
| `N` | 分析最近 N 個 commits | `/doc-updater 5` |
| `--since <ref>` | 從指定 ref 開始分析 | `/doc-updater --since v1.0.0` |
| `--check` | 僅檢查，不執行更新 | `/doc-updater --check` |

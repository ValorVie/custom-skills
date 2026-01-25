---
name: git-commit-pr-analyze
description: Git Commit 工作流 - PR 變更分析與摘要生成
---

## PR 變更分析

> **前置條件**：已取得 `$BASE_SHA` 和 `$HEAD_SHA` 變數

---

## 1. 讀取 Commit 歷史

```bash
# 取得所有 commit 訊息
COMMIT_LOG=$(git log --pretty=format:"- %h: %s" $BASE_SHA..$HEAD_SHA)

# 取得 commit 數量
COMMIT_COUNT=$(git rev-list --count $BASE_SHA..$HEAD_SHA)

# 取得詳細的 commit 訊息（含 body）
COMMIT_DETAILS=$(git log --pretty=format:"### %h%n%n**%s**%n%n%b%n---" $BASE_SHA..$HEAD_SHA)
```

---

## 2. 分析檔案變更

```bash
# 取得變更統計
DIFF_STAT=$(git diff --stat $BASE_SHA..$HEAD_SHA)

# 取得變更檔案清單（按狀態分類）
ADDED_FILES=$(git diff --name-only --diff-filter=A $BASE_SHA..$HEAD_SHA)
MODIFIED_FILES=$(git diff --name-only --diff-filter=M $BASE_SHA..$HEAD_SHA)
DELETED_FILES=$(git diff --name-only --diff-filter=D $BASE_SHA..$HEAD_SHA)

# 統計數量
ADDED_COUNT=$(echo "$ADDED_FILES" | grep -c . || echo 0)
MODIFIED_COUNT=$(echo "$MODIFIED_FILES" | grep -c . || echo 0)
DELETED_COUNT=$(echo "$DELETED_FILES" | grep -c . || echo 0)
```

---

## 3. 生成 PR 標題

### 若使用者指定 `--title`

直接使用使用者指定的標題。

### 若自動生成

分析 commit 歷史，生成摘要標題：

1. **單一提交**：直接使用該 commit 的標題
2. **多個提交**：
   - 分析所有 commit 的 type（feat, fix, docs 等）
   - 找出主要的變更類型
   - 生成概括性標題

```bash
# 範例：分析主要類型
PRIMARY_TYPE=$(git log --pretty=format:"%s" $BASE_SHA..$HEAD_SHA | \
    grep -oE "^(feat|fix|docs|refactor|test|chore|style|perf)" | \
    sort | uniq -c | sort -rn | head -1 | awk '{print $2}')

# 若無法判斷類型，預設為 feat
PRIMARY_TYPE=${PRIMARY_TYPE:-feat}
```

**標題格式**：
```
<type>(<scope>): <概括性描述>
```

---

## 4. 生成 PR 內文

### 若使用者指定 `--body`

直接使用使用者指定的內文。

### 若自動生成

使用以下模板：

```markdown
## Summary

[基於 commit messages 和 diff 分析的變更摘要]

此 PR 包含 {COMMIT_COUNT} 個提交，涉及 {TOTAL_FILES} 個檔案的變更。

## Changes

[從 commit messages 提取的主要變更項目]

- [變更項目 1]
- [變更項目 2]
- ...

## Files Changed

**Added ({ADDED_COUNT}):**
{ADDED_FILES_LIST}

**Modified ({MODIFIED_COUNT}):**
{MODIFIED_FILES_LIST}

**Deleted ({DELETED_COUNT}):**
{DELETED_FILES_LIST}

## Commit History

<details>
<summary>包含的提交 ({COMMIT_COUNT})</summary>

{COMMIT_LOG}

</details>

---

> Generated with [Claude Code](https://claude.ai/code)
```

---

## 5. 生成整合提交訊息

當使用整合模式（非 `--no-squash`）時，需要生成整合後的 commit message：

### 標題

使用與 PR 標題相同的格式。

### 本文

```markdown
整合自 {COMMIT_COUNT} 個開發提交

變更摘要：
- [主要變更 1]
- [主要變更 2]
- ...

原始提交：
{COMMIT_LOG}
```

---

## 6. 輸出變數

將以下變數傳遞給 `pr.md`：

| 變數 | 說明 |
|------|------|
| `$PR_TITLE` | PR 標題 |
| `$PR_BODY` | PR 內文（完整 Markdown） |
| `$SQUASHED_MESSAGE` | 整合後的 commit message |
| `$COMMIT_COUNT` | 提交數量 |
| `$TOTAL_FILES` | 變更檔案總數 |

---

## 摘要生成指引

### 分析 Commit Messages

1. **過濾無意義訊息**：忽略 "wip", "...", "fix", "temp", "test" 等無意義的訊息
2. **識別類型**：從 commit prefix 識別變更類型
3. **提取關鍵資訊**：從有意義的訊息中提取實際變更內容

### 分析 Diff 內容

1. **識別主要變更區域**：哪些目錄/模組有變更
2. **識別變更性質**：新增功能、修復、重構等
3. **識別影響範圍**：API 變更、UI 變更、配置變更等

### 撰寫摘要

1. **使用繁體中文**
2. **簡潔明瞭**：一句話概括主要變更
3. **具體明確**：說明「做了什麼」而非「如何做」
4. **技術準確**：使用正確的技術術語

---

## 範例輸出

### PR 標題

```
feat(git-commit): 新增 PR 建立模式
```

### PR 內文

```markdown
## Summary

為 `git-commit` 指令新增 `pr` 子指令，自動化建立 Pull Request 的流程。

此 PR 包含 5 個提交，涉及 4 個檔案的變更。

## Changes

- 新增 `pr.md` 主控制模組
- 新增 `pr-analyze.md` 變更分析模組
- 更新 `SKILL.md` 路由邏輯
- 更新 `git-commit.md` 指令說明

## Files Changed

**Added (2):**
- skills/git-commit-custom/pr.md
- skills/git-commit-custom/pr-analyze.md

**Modified (2):**
- skills/git-commit-custom/SKILL.md
- commands/claude/git-commit.md

## Commit History

<details>
<summary>包含的提交 (5)</summary>

- abc1234: feat(pr): 新增 pr.md 主控制模組
- def5678: feat(pr): 新增 pr-analyze.md 分析模組
- ghi9012: docs(skill): 更新 SKILL.md 路由
- jkl3456: docs(command): 更新 git-commit.md
- mno7890: fix(pr): 修正參數解析邏輯

</details>

---

> Generated with [Claude Code](https://claude.ai/code)
```

### 整合 Commit Message

```
feat(git-commit): 新增 PR 建立模式

整合自 5 個開發提交

變更摘要：
- 新增 pr.md 主控制模組
- 新增 pr-analyze.md 變更分析模組
- 更新路由邏輯與指令說明

原始提交：
- abc1234: feat(pr): 新增 pr.md 主控制模組
- def5678: feat(pr): 新增 pr-analyze.md 分析模組
- ghi9012: docs(skill): 更新 SKILL.md 路由
- jkl3456: docs(command): 更新 git-commit.md
- mno7890: fix(pr): 修正參數解析邏輯
```

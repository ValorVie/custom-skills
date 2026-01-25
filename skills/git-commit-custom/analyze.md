---
name: git-commit-analyze
description: Git Commit 工作流 - 變更分析
---

## 2. 變更分析 (Analyze)

> **前置條件**：已從 `_utils.md` 取得 `$MAIN_BRANCH` 變數

### 2.1 定義基準點

#### 若 target = `remote`

```bash
BASE_SHA=$(git merge-base HEAD origin/$MAIN_BRANCH)
```

#### 若 target = `local`

```bash
BASE_SHA=$(git merge-base HEAD $MAIN_BRANCH)
```

#### 若 --direct（主分支直接提交）

```bash
# 使用 HEAD~1 作為基準，僅比較最近的變更
# 若有未暫存的變更，則使用 HEAD 作為基準
if git diff --quiet; then
    BASE_SHA=$(git rev-parse HEAD)
else
    BASE_SHA="HEAD"
fi
```

---

### 2.2 檢查是否有變更

```bash
# 檢查已提交的差異
git diff $BASE_SHA --quiet

# 檢查未暫存的變更
git diff --quiet

# 檢查暫存區的變更
git diff --cached --quiet
```

若以上三者皆無差異，告知使用者：

> 📭 目前分支與 base 狀態一致，無須執行提交。

並中止流程。

---

### 2.3 輸出變數

將以下變數傳遞給後續模組：

| 變數 | 說明 |
|------|------|
| `$BASE_SHA` | 基準點 SHA |
| `$MAIN_BRANCH` | 主分支名稱 |

---

## 完成後

繼續執行 `commit.md` 進行提交。

---
name: git-commit-sync
description: Git Commit 工作流 - 環境同步與保護
---

## 1. 環境同步與保護 (Sync & Safeguard)

> **前置條件**：已從 `_utils.md` 取得 `$MAIN_BRANCH` 變數

### 1.1 安全暫存 (Stash)

無論有無未提交的變更，強制執行：

```bash
git stash push -m "git-commit: auto stash before rebase"
```

---

### 1.2 同步分支

首先，取得當前分支名稱：

```bash
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
```

---

#### 若 target = `remote`

```bash
# 取得遠端最新狀態
git fetch origin $MAIN_BRANCH

# 檢查是否需要同步
LOCAL_MAIN=$(git rev-parse $MAIN_BRANCH)
REMOTE_MAIN=$(git rev-parse origin/$MAIN_BRANCH)

if [ "$LOCAL_MAIN" != "$REMOTE_MAIN" ]; then
    git checkout $MAIN_BRANCH
    git pull --ff-only origin $MAIN_BRANCH
    git checkout -
fi

# 根據分支類型或 --no-rebase 參數選擇同步策略
if [[ "$NO_REBASE" == true ]] || [[ "$CURRENT_BRANCH" == test-dev-* ]]; then
    # 整合分支或強制指定：使用 Merge 策略，保留合併節點
    git merge origin/$MAIN_BRANCH --no-ff -m "chore: 同步 $MAIN_BRANCH 至整合分支"
else
    # 功能分支：使用 Rebase 策略，保持線性歷史
    git rebase origin/$MAIN_BRANCH
fi
```

---

#### 若 target = `local`

```bash
# 檢查是否需要同步
BEHIND_COUNT=$(git rev-list --count HEAD..$MAIN_BRANCH)

if [ "$BEHIND_COUNT" -gt 0 ]; then
    if [[ "$NO_REBASE" == true ]] || [[ "$CURRENT_BRANCH" == test-dev-* ]]; then
        # 整合分支或強制指定：使用 Merge 策略
        git merge $MAIN_BRANCH --no-ff -m "chore: 同步 $MAIN_BRANCH 至整合分支"
    else
        # 功能分支：使用 Rebase 策略
        git rebase $MAIN_BRANCH
    fi
fi
```

---

### 1.3 處理衝突

若發生衝突，請參考 `_utils.md` 的「衝突處理指引」章節。

---

### 1.4 還原暫存 (Stash Pop)

```bash
git stash pop
```

*注意：如果還原時發生衝突，請協助使用者解決衝突後再繼續。*

---

## 完成後

繼續執行 `analyze.md` 進行變更分析。

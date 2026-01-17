---
name: git-commit-merge
description: Git Commit 工作流 - 多分支合併
---

## 6. 多分支合併 (Merge)

> **用法**：`git-commit merge feature/A feature/B ...`

此模組用於建立暫時性整合分支，將多個功能分支合併在一起進行測試。

---

### 6.1 環境重置

切換回主分支並更新：

```bash
# 先判斷主分支名稱（參考 _utils.md）
if git rev-parse --verify main >/dev/null 2>&1; then
    MAIN_BRANCH="main"
else
    MAIN_BRANCH="master"
fi

git checkout $MAIN_BRANCH
git pull origin $MAIN_BRANCH
```

---

### 6.2 建立整合分支

```bash
# 產生時間戳記
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# 建立分支名稱
BRANCH_NAME="test-dev-$TIMESTAMP"

# 建立並切換至新分支
git checkout -b $BRANCH_NAME
```

---

### 6.3 依序合併

針對使用者提供的每一個分支，依序執行：

```bash
git merge --no-ff <feature_branch>
```

#### 若發生衝突

1. 暫停流程
2. 列出衝突檔案：
   ```bash
   git diff --name-only --diff-filter=U
   ```
3. 提示使用者手動解決衝突並執行：
   ```bash
   git add .
   git commit  # 不使用 --amend
   ```
4. 確認解決後，繼續合併下一個分支

---

### 6.4 推送結果

合併完成後，將整合分支推送至遠端：

```bash
git push origin $BRANCH_NAME
```

輸出分支名稱供使用者參考：

> ✅ 整合分支已建立並推送：`test-dev-20260115170000`

---

## 完成

流程結束。使用者可在此整合分支上進行測試。

### 後續操作提示

- 測試完成後，可刪除整合分支：
  ```bash
  git branch -d $BRANCH_NAME
  git push origin --delete $BRANCH_NAME
  ```
- 若需要更新整合分支，可再次執行 `git-commit merge` 建立新的整合分支

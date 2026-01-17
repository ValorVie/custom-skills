---
name: git-commit-push
description: Git Commit 工作流 - 推送至遠端
---

## 5. 推送至遠端 (Push)

> **前置條件**：已完成提交

---

### 5.1 檢查分叉狀態

```bash
git fetch origin
git status -sb
```

---

### 5.2 判斷推送方式

#### 若無分叉

直接執行：

```bash
git push
```

---

#### 若有分叉

顯示警告並詢問：

> ⚠️ 本地分支與遠端分支已分叉。是否要使用 `--force-with-lease` 強制推送？
> 這將覆寫遠端分支的提交歷史。

等待使用者確認後執行：

```bash
git push --force-with-lease
```

---

### 5.3 確認推送結果

```bash
git log --oneline -3
```

顯示最近三筆提交，確認推送成功。

---

## 完成

流程結束。

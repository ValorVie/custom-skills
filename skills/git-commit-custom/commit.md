---
name: git-commit-commit
description: Git Commit 工作流 - 執行提交
---

## 3. 提交 (Commit)

> **前置條件**：已從 `analyze.md` 取得 `$BASE_SHA` 變數

---

### mode = `normal`（單次提交）

根據當前暫存區的異動內容撰寫提交訊息，執行 commit。

```bash
# 檢視待提交的變更
git diff --cached

# 若無暫存變更，先加入所有變更
git add .

# 執行提交
git commit -m "[Title]" -m "[Body]"
```

---

### mode = `final`（整合提交）

#### 3.1 讀取開發歷程

```bash
git log --pretty=format:"- %s%n%b" $BASE_SHA..HEAD
```

#### 3.2 讀取最終差異

```bash
git diff $BASE_SHA
```

#### 3.3 生成提交訊息

基於上述資訊，**過濾**掉無意義的訊息（如 "wip", "...", "fix", "temp"），撰寫一個符合規範的訊息：

- **標題 (Title)**：簡潔明瞭，動詞開頭（如：新增、修復、優化）
- **內容 (Body)**：條列式說明技術實作細節與變更原因

#### 3.4 執行 Soft Reset 與提交

```bash
# 將 HEAD 指標移回 Base，保留所有變更於暫存區
git reset --soft $BASE_SHA

# 確保所有變更均已加入
git add .

# 執行最終提交
git commit -m "[Title]" -m "[Body]"
```

---

## 4. 最終確認

顯示最終的提交狀態供使用者檢視：

```bash
git show --stat HEAD
```

---

## 完成後

- 若有 `--push` 參數 → 繼續執行 `push.md`
- 否則 → 流程結束

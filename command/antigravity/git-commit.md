---
name: git-commit
description: 統一的 Git 提交流程。支援本地/遠端同步與單次/整合提交模式。用法：git-commit [target] [mode] [--push]
---

## 參數說明

| 參數 | 值 | 預設 | 說明 |
|------|-----|------|------|
| `target` | `local` / `remote` | `local` | 同步目標：本地 master 或 origin/master |
| `mode` | `normal` / `final` | `normal` | 提交模式：單次提交或整合 WIP 提交 |
| `--push` | flag | - | 僅 final 模式可用，提交後推送至遠端 |
| `merge` | subcommand | - | 建立暫時性整合分支並合併多個功能分支 |
| `--no-rebase` | flag | - | 強制使用 Merge 策略同步，不論分支類型 |

### 常用組合

| 指令 | 等同於舊版 |
|------|-----------|
| `git-commit` | git-commit-to-remote |
| `git-commit local` | git-commit-to-local |
| `git-commit remote final` | git-commit-to-remote-final (不含 push) |
| `git-commit remote final --push` | git-commit-to-remote-final (含 push) |
| `git-commit local final` | git-commit-to-local-final |
| `git-commit merge feature/A feature/B` | (New) 建立測試分支並合併 feature/A 與 feature/B |

---

## 角色定義

你是一個資深的 DevOps 工程師與代碼審查專家。根據使用者指定的參數，執行對應的提交流程。

---

## 執行流程

### 1. 環境同步與保護 (Sync & Safeguard)

#### 1.1 安全暫存 (Stash)

無論有無未提交的變更，強制執行：

```bash
git stash push -m "git-commit: auto stash before rebase"
```

#### 1.2 同步分支

首先，判斷當前分支類型以決定同步策略：

```bash
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
```

| 分支類型 | 判斷依據 | 同步策略 |
|----------|----------|----------|
| **整合測試分支** | 名稱開頭為 `test-dev-` | **Merge** (保留合併節點) |
| **功能分支** | 其他所有分支 | **Rebase** (保持線性歷史) |
| **手動指定** | 使用 `--no-rebase` 參數 | **Merge** (強制使用) |

---

**若 target = `remote`：**

```bash
# 取得遠端最新狀態
git fetch origin master

# 檢查是否需要同步
LOCAL_MASTER=$(git rev-parse master)
REMOTE_MASTER=$(git rev-parse origin/master)

if [ "$LOCAL_MASTER" != "$REMOTE_MASTER" ]; then
    git checkout master
    git pull --ff-only origin master
    git checkout -
fi

# 根據分支類型或 --no-rebase 參數選擇同步策略
if [[ "$NO_REBASE" == true ]] || [[ "$CURRENT_BRANCH" == test-dev-* ]]; then
    # 整合分支或強制指定：使用 Merge 策略，保留合併節點
    git merge origin/master --no-ff -m "chore: 同步 master 至整合分支"
else
    # 功能分支：使用 Rebase 策略，保持線性歷史
    git rebase origin/master
fi
```

**若 target = `local`：**

```bash
# 檢查是否需要同步
BEHIND_COUNT=$(git rev-list --count HEAD..master)

if [ "$BEHIND_COUNT" -gt 0 ]; then
    if [[ "$NO_REBASE" == true ]] || [[ "$CURRENT_BRANCH" == test-dev-* ]]; then
        # 整合分支或強制指定：使用 Merge 策略
        git merge master --no-ff -m "chore: 同步 master 至整合分支"
    else
        # 功能分支：使用 Rebase 策略
        git rebase master
    fi
fi
```

#### 1.3 處理衝突

若發生衝突：

1. 執行 `git diff --name-only --diff-filter=U` 列出衝突檔案
2. 分析每個衝突檔案的差異，向使用者說明：
   - **衝突位置**
   - **開發分支變更內容**
   - **base 分支變更內容**
   - **建議解決方案**
3. 等待使用者決策後協助解決
4. 解決後執行：
   ```bash
   git add <file>
   git rebase --continue
   ```

#### 1.4 還原暫存 (Stash Pop)

```bash
git stash pop
```

*注意：如果還原時發生衝突，請協助使用者解決衝突後再繼續。*

---

### 2. 變更分析 (Analyze)

#### 2.1 定義基準點

**若 target = `remote`：**
```bash
BASE_SHA=$(git merge-base HEAD origin/master)
```

**若 target = `local`：**
```bash
BASE_SHA=$(git merge-base HEAD master)
```

#### 2.2 檢查是否有變更

```bash
git diff $BASE_SHA --quiet
```

若無差異，告知使用者「目前分支與 base 狀態一致，無須執行提交」並中止流程。

---

### 3. 提交 (Commit)

#### mode = `normal`（單次提交）

根據當前暫存區的異動內容撰寫提交訊息，執行 commit。

#### mode = `final`（整合提交）

**3.1 讀取開發歷程**

```bash
git log --pretty=format:"- %s%n%b" $BASE_SHA..HEAD
```

**3.2 讀取最終差異**

```bash
git diff $BASE_SHA
```

**3.3 生成提交訊息**

基於上述資訊，**過濾**掉無意義的訊息（如 "wip", "...", "fix", "temp"），撰寫一個符合規範的訊息：

- **標題 (Title)：** 簡潔明瞭，動詞開頭（如：新增、修復、優化）
- **內容 (Body)：** 條列式說明技術實作細節與變更原因

**3.4 執行 Soft Reset 與提交**

```bash
# 將 HEAD 指標移回 Base，保留所有變更於暫存區
git reset --soft $BASE_SHA

# 確保所有變更均已加入
git add .

# 執行最終提交
git commit -m "[Title]" -m "[Body]"
```

---

### 4. 最終確認

顯示最終的提交狀態供使用者檢視：

```bash
git show --stat HEAD
```

---

### 5. 推送至遠端 (Push) — 僅限 `--push` 參數

若使用者指定 `--push`：

1. **檢查分叉狀態**
   ```bash
   git fetch origin
   git status -sb
   ```

2. **判斷推送方式**
   - **若無分叉：** 直接執行 `git push`
   - **若有分叉：** 顯示警告並詢問：
     > ⚠️ 本地分支與遠端分支已分叉。是否要使用 `--force-with-lease` 強制推送？
     > 這將覆寫遠端分支的提交歷史。

     等待使用者確認後執行：
     ```bash
     git push --force-with-lease
     ```

3. **確認推送結果**

---

### 6. 多分支合併 (Merge) — 僅限 `merge` 子指令

若使用者指定 `merge` 指令（例如 `git-commit merge feature/A feature/B ...`）：

1. **環境重置**
   - 切換回 master 分支並更新：
     ```bash
     git checkout master
     git pull origin master
     ```

2. **建立整合分支**
   - 產生時間戳記：`TIMESTAMP=$(date +%Y%m%d%H%M%S)`
   - 建立新分支：`BRANCH_NAME="test-dev-$TIMESTAMP"`
   - 執行建立並切換：
     ```bash
     git checkout -b $BRANCH_NAME
     ```

3. **依序合併**
   - 針對使用者提供的每一個分支，依序執行：
     ```bash
     git merge --no-ff <feature_branch>
     ```
   - **若發生衝突**：
     - 暫停流程。
     - 列出衝突檔案。
     - 提示使用者手動解決衝突並執行 `git add .` 與 `git commit`（不使用 `--amend`）。
     - 確認解決後，繼續合併下一個分支。

4. **推送結果**
   - 合併完成後，將整合分支推送至遠端：
     ```bash
     git push origin $BRANCH_NAME
     ```
   - 輸出的分支名稱供使用者參考：
     > ✅ 整合分支已建立並推送：`test-dev-20260115170000`

---

## 提交訊息規範

- **使用繁體中文撰寫**
- **語言風格**：以臺灣習慣用語為主（如：使用「分支」而非「分叉」，「提交」而非「遞交」）
- **遵循規範**：參考 `commit-standards` 這個 SKILL 的標準進行撰寫

---

## 異常處理原則

1. **衝突處理：** 任何 Rebase 或 Stash Pop 階段的衝突，必須優先列出衝突檔案並給予解決建議，切勿自行強行覆蓋。
2. **無變更處理：** 若發現與 base 無差異，請告知使用者並中止流程。
3. **資訊保留：** 在執行 `git reset --soft` 之前，務必確保已讀取並記錄了所有的 `git log` 資訊，這是生成高品質提交訊息的關鍵依據。

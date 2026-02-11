# Git WIP Commit 整合指南

本指南說明如何將多個 WIP（Work In Progress）暫存 commit 整合為有意義的語義化 commit，涵蓋三種方法的比較與實戰範例。

---

## 快速參考

| 方法 | 複雜度 | 安全性 | 適用場景 |
|------|--------|--------|----------|
| `git merge --squash` | 低 | 高 | 單一群組整合，線性歷史 |
| `git reset --soft` + 分批 commit | 中 | 中 | 多群組整合，需手動分組 |
| `git rm -rf .` + `git checkout` | 中 | 低 | 精確重現特定 commit 狀態 |
| `git commit-tree`（plumbing） | 高 | 高 | 進階用戶，完全不碰工作目錄 |

---

## 方法一：`git merge --squash`（推薦）

最簡單安全的方式，適合將一段連續 WIP commit 壓成一個。

### 步驟

```bash
# 1. 建立備份分支
git branch backup-before-squash HEAD

# 2. 回到要整合的起點
git reset --hard <base-commit>

# 3. 將 WIP 範圍壓入暫存區
git merge --squash <end-commit>

# 4. 建立新 commit
git commit -m "功能(模組): 有意義的 commit 訊息"

# 5. 驗證內容一致
git diff backup-before-squash --stat
# 應該為空（無差異）

# 6. 刪除備份
git branch -D backup-before-squash
```

### 多群組整合

若 WIP 需分成多個邏輯群組（如 WIP-1~5 = 功能、WIP-6~8 = 修復），可以串接：

```bash
git reset --hard <base>

# 群組 1
git merge --squash <group1-end>
git commit -m "功能: ..."

# 群組 2（git 會自動只帶入增量差異）
git merge --squash <group2-end>
git commit -m "修正: ..."
```

**注意**：群組 2 的 `merge --squash` 可能產生衝突（因為 merge base 是原始 base 而非 group1-end）。衝突時可用 `git checkout --theirs -- .` 解決，前提是後面的 WIP 是前面的超集。

---

## 方法二：`git reset --soft` + 分批 add

適合需要在同一批 WIP 中拆分不同檔案到不同 commit。

### 步驟

```bash
# 1. 備份
git branch backup-before-squash HEAD

# 2. Soft reset 保留所有變更在暫存區
git reset --soft <base-commit>

# 3. 全部 unstage
git reset HEAD .

# 4. 按群組手動 add + commit
git add docs/ openspec/
git commit -m "文件: ..."

git add tests/
git commit -m "測試: ..."

# 5. 驗證
git diff backup-before-squash --stat
```

**缺點**：新檔案會變成 untracked，刪除的檔案需要手動 `git add` 才會暫存。適合修改為主、新增/刪除較少的場景。

---

## 方法三：`git rm -rf .` + `git checkout`（精確但粗暴）

精確重現任意 commit 的完整檔案樹，包含新增和刪除。

### 步驟

```bash
git reset --hard <base>

# 對每個群組端點：
git rm -rf .                        # 清空 index + 工作目錄
git checkout <target-commit> -- .   # 從目標 commit 還原一切
git add -A                          # 暫存刪除的檔案
git commit -m "..."
```

### `git rm -rf .` 詳細說明

**做了什麼**：
1. 從 git index（暫存區）移除所有已追蹤檔案
2. 從工作目錄物理刪除這些檔案
3. `.git/` 目錄不受影響

**影響範圍**：

| 檔案類型 | 是否被刪除 |
|----------|-----------|
| 已追蹤（tracked） | **是** — 從 index + 磁碟移除 |
| 未追蹤（untracked） | **否** — git 不知道它們存在 |
| 被忽略（.gitignore） | **否** — git 刻意忽略 |

**為什麼需要先清空**：`git checkout <commit> -- .` 只還原目標 commit 中**存在**的檔案，不會刪除目標 commit 中**不存在**的檔案。先 `git rm -rf .` 清空再還原，才能得到完全一致的樹狀態。

### 副作用與修復

**問題**：commit 後工作目錄仍為空（檔案已被物理刪除），`git status` 會顯示所有檔案為 `D`（已刪除）。

**修復**：
```bash
git restore --staged .      # 重設暫存區
git checkout HEAD -- .      # 從 HEAD 還原工作目錄
```

**安全提醒**：
- 操作前**必須**建立 backup branch
- `.env`、`node_modules/`、IDE 設定等 untracked/ignored 檔案不受影響
- 但操作期間工作目錄是空的，若中途失敗需手動還原

---

## 方法四：`git commit-tree`（最安全）

使用 git plumbing 命令，完全不碰工作目錄。

### 步驟

```bash
# 直接從目標 commit 的 tree 建立新 commit
NEW=$(git commit-tree <target-commit>^{tree} -p <parent-commit> -m "commit message")

# 更新 branch 指向新 commit
git reset --hard $NEW
```

### 多群組

```bash
# 群組 1
C1=$(git commit-tree <group1-end>^{tree} -p <base> -m "功能: ...")

# 群組 2（parent 指向群組 1）
C2=$(git commit-tree <group2-end>^{tree} -p $C1 -m "修正: ...")

# 更新 HEAD
git reset --hard $C2
```

**優點**：工作目錄和 index 完全不動，只在最後 `reset --hard` 一次性同步。
**缺點**：語法較不直覺，需要理解 git 物件模型（tree、commit、parent）。

---

## 相關的清理命令比較

| 命令 | 刪除對象 | 影響範圍 |
|------|----------|----------|
| `git rm -rf .` | 已追蹤檔案 | index + 工作目錄 |
| `git rm --cached -rf .` | 已追蹤檔案 | 僅 index（保留工作目錄） |
| `git clean -fd` | 未追蹤檔案 | 僅工作目錄 |
| `git clean -fdx` | 未追蹤 + 被忽略檔案 | 僅工作目錄 |
| `git reset --hard` | 已追蹤的修改 | index + 工作目錄（還原到 HEAD） |
| `git checkout -- .` | 已追蹤的修改 | 僅工作目錄（從 index 還原） |

---

## 實戰範例

### 場景：兩個 repo 各有 10+ 個 WIP commit，需按邏輯分組整合

```
qdm-e2e-framework:  WIP-22 → WIP-31（9 個 WIP）
qdm_base_new:       WIP-1  → WIP-11（11 個 WIP）
```

**分組策略**：

```
qdm-e2e-framework:
  群組 1: WIP-22~26 → "功能(結帳): 調查修復"
  群組 2: WIP-27    → "文件(結帳): 資安評估"
  群組 3: WIP-28~31 → "修正(結帳): 資安強化"

qdm_base_new:
  群組 1: WIP-1~5   → "功能(結帳): POST 回補 + SessionStorage"
  群組 2: WIP-6~11  → "修正(結帳): AJAX 修復 + SQL escape"
```

**操作流程**（以 qdm-e2e-framework 為例）：

```bash
# 備份
git branch backup-before-squash HEAD

# 回到起點
git reset --hard <WIP-22>

# 群組 1：用 git rm + checkout 精確重現
git rm -rf . > /dev/null 2>&1
git checkout <WIP-26> -- .
git add -A
git commit -m "功能(結帳): 調查修復 ..."

# 群組 2
git rm -rf . > /dev/null 2>&1
git checkout <WIP-27> -- .
git add -A
git commit -m "文件(結帳): 資安評估 ..."

# 群組 3
git rm -rf . > /dev/null 2>&1
git checkout <WIP-31> -- .
git add -A
git commit -m "修正(結帳): 資安強化 ..."

# 驗證（diff 應為空）
git diff backup-before-squash --stat

# 還原工作目錄
git restore --staged .
git checkout HEAD -- .

# 清理備份
git branch -D backup-before-squash
```

**更安全的等價寫法**（使用 `commit-tree`）：

```bash
git branch backup-before-squash HEAD

C1=$(git commit-tree <WIP-26>^{tree} -p <WIP-22> -m "功能(結帳): 調查修復 ...")
C2=$(git commit-tree <WIP-27>^{tree} -p $C1 -m "文件(結帳): 資安評估 ...")
C3=$(git commit-tree <WIP-31>^{tree} -p $C2 -m "修正(結帳): 資安強化 ...")

git reset --hard $C3
git diff backup-before-squash --stat   # 驗證
git branch -D backup-before-squash
```

---

## 常見錯誤

| 錯誤 | 原因 | 解法 |
|------|------|------|
| `git rm -rf .` 後 status 全部 D | 工作目錄被清空 | `git restore --staged . && git checkout HEAD -- .` |
| `merge --squash` 衝突 | merge base 不是上一個群組端點 | `git checkout --theirs -- .` 或改用 `commit-tree` |
| `git checkout <hash> -- .` 失敗 | 短 hash 不明確或跨 repo 引用 | 使用完整 40 字元 hash 或 branch ref（如 `backup~3`） |
| 跨 repo `-C` 指令異常 | shell hook 干擾 cd 行為 | 改用 `GIT_DIR` + `GIT_WORK_TREE` 環境變數 |

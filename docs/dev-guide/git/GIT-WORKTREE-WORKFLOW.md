# Git Worktree 工作流程指南

本指南介紹基於 **Git Worktree** 的進階工作流程，適合需要**並行開發多個功能**或**頻繁切換上下文**的場景。

> 如果你是 Git 新手，建議先閱讀 [GIT-WORKFLOW.md](./GIT-WORKFLOW.md) 了解基礎流程。

---

## 核心概念

### 什麼是 Git Worktree？

Git Worktree 允許你在**同一個儲存庫**中建立**多個獨立的工作目錄**，每個目錄可以切換到不同的分支，互不影響。

```
傳統方式（單一工作目錄）：
~/custom-skills/           ← 只有這個目錄
    ├── git checkout main     ← 切換分支時，整個目錄內容改變
    ├── git checkout feature-a
    └── git checkout feature-b  ← 無法同時存在

Worktree 方式（多個工作目錄）：
~/custom-skills/           ← main worktree（主目錄）
    └── branch: main
~/custom-skills-wt/
    ├── feature-a/         ← 獨立目錄，branch: feature-a
    ├── feature-b/         ← 獨立目錄，branch: feature-b
    └── hotfix/            ← 獨立目錄，branch: main（緊急修復）
```

### 與基礎流程的關係

| 基礎流程 (GIT-WORKFLOW.md) | Worktree 進階流程 |
|---------------------------|-------------------|
| `git checkout` 切換分支 | 直接 `cd` 切換目錄 |
| `git stash` 暫存變更 | 不需要 stash，目錄獨立 |
| 單一 IDE 視窗 | 可多個 IDE 視窗並行 |
| 適合線性開發 | 適合並行開發 |

**兩者可以混合使用**：基礎開發用傳統流程，需要並行時用 worktree。

---

## 目錄結構規劃

```
~/projects/
├── custom-skills/              ← 主要開發目錄（main worktree）
│   ├── .git/                   ← 原始儲存庫的 git 資料
│   ├── skills/
│   ├── commands/
│   └── ...                     ← 日常開發在這裡
│
└── custom-skills-wt/           ← worktree 根目錄
    ├── feature-auth/           ← 功能分支 A
    ├── feature-api/            ← 功能分支 B
    ├── review-pr-42/           ← PR 審查臨時目錄
    ├── hotfix-260127/          ← 緊急修復
    └── spike-experiment/       ← 實驗性分支
```

### 命名慣例

| 類型 | 命名格式 | 範例 |
|------|----------|------|
| 功能開發 | `feature-<描述>` | `feature-dark-mode` |
| PR 審查 | `review-pr-<號碼>` | `review-pr-156` |
| 緊急修復 | `hotfix-<日期>` | `hotfix-260127` |
| 實驗性 | `spike-<描述>` | `spike-ai-integration` |

---

## 完整工作流程

### Step 1: 初始化 Worktree 環境

**首次設定**：

```bash
# 1. 確保主目錄在 main 分支且乾淨
cd ~/custom-skills
git checkout main
git pull origin main

# 2. 建立 worktree 根目錄
mkdir -p ~/custom-skills-wt
```

---

### Step 2: 建立開發分支（Worktree 版本）

**傳統方式 vs Worktree 方式**：

```bash
# 傳統方式（基礎流程）
git checkout -b arlen-260127

# Worktree 方式（並行開發）
git worktree add ~/custom-skills-wt/feature-auth -b arlen-260127-auth
cd ~/custom-skills-wt/feature-auth
```

**選擇建議**：
- **傳統方式**：單一功能開發，不需要頻繁切換
- **Worktree 方式**：需要同時開發多個功能，或可能需要緊急切換任務

---

### Step 3: 並行開發多個功能

**情境**：同時開發功能 A 和功能 B

```bash
# 建立兩個獨立的 worktree
git worktree add ~/custom-skills-wt/feature-a -b arlen-feature-a
git worktree add ~/custom-skills-wt/feature-b -b arlen-feature-b

# 現在你可以：
# - 在 ~/custom-skills-wt/feature-a/ 開發功能 A（IDE 視窗 1）
# - 在 ~/custom-skills-wt/feature-b/ 開發功能 B（IDE 視窗 2）
# - 兩個功能同時進行，互不影響
```

**開發過程**：

```bash
# 在 feature-a 目錄
cd ~/custom-skills-wt/feature-a
git add .
git commit -m "wip: auth logic"

# 切換到 feature-b 目錄（不需要 stash！）
cd ~/custom-skills-wt/feature-b
git add .
git commit -m "wip: api endpoint"
```

---

### Step 4: 同步主線

**每個 worktree 獨立同步**：

```bash
cd ~/custom-skills-wt/feature-a

# 方法一：Rebase（保持線性歷史）
git fetch origin
git rebase origin/main

# 方法二：Merge（保留合併節點）
git fetch origin
git merge origin/main
```

> 注意：worktree 的同步與傳統流程完全相同，只是你在不同目錄執行。

---

### Step 5: 建立 PR

**與基礎流程相同**：

```bash
cd ~/custom-skills-wt/feature-a

# 使用 git-commit 指令建立 PR
/git-commit pr
```

> `/git-commit pr` 會自動偵測當前分支和變更，無論你在哪個 worktree 都正常運作。

---

### Step 6: Code Review 與迭代

**收到 review 意見後的修改**：

```bash
cd ~/custom-skills-wt/feature-a

# 根據審查意見修改
git add .
git commit -m "address review comments"
git push
```

---

### Step 7: 合併後清理

**PR 合併後，清理 worktree**：

```bash
# 1. 先移除 worktree
git worktree remove ~/custom-skills-wt/feature-a

# 2. 刪除遠端分支（如果還沒刪除）
git push origin --delete arlen-feature-a

# 3. 清理無效的 worktree 記錄
git worktree prune

# 4. 選擇性：刪除本地分支記錄
git branch -d arlen-feature-a
```

> **重要**：`git worktree remove` 會檢查是否有未提交的變更，如果有會阻止刪除，避免遺失工作。

---

## 進階使用場景

### 場景 A：開發中遇到緊急修復

**傳統方式的痛點**：需要 stash → checkout main → 修復 → commit → checkout 回來 → stash pop

**Worktree 方式**：

```bash
# 正在 feature-a 開發，突然需要修復 production 問題
cd ~/custom-skills-wt/feature-a
# ... 開發到一半，有大量未提交變更 ...

# 直接建立新的 worktree 進行修復
git worktree add ~/custom-skills-wt/hotfix-$(date +%y%m%d) main
cd ~/custom-skills-wt/hotfix-$(date +%y%m%d)

# 進行修復
git add .
git commit -m "fix: 緊急修復 xxx"
git push origin HEAD

# 建立 PR 並合併後，清理
git worktree remove ~/custom-skills-wt/hotfix-$(date +%y%m%d)

# 回到 feature-a 繼續開發，完全沒有切換成本
cd ~/custom-skills-wt/feature-a
```

### 場景 B：審查同事的 PR

**需要完整檢視程式碼，但不想影響當前工作**：

```bash
# 建立臨時 worktree 審查 PR
git worktree add ~/custom-skills-wt/review-pr-156 pr-branch-name
cd ~/custom-skills-wt/review-pr-156

# 用 IDE 開啟，完整支援：
# - 瀏覽程式碼結構
# - 執行測試
# - 甚至可以做小修改測試

# 審查完畢，直接刪除
git worktree remove ~/custom-skills-wt/review-pr-156
```

### 場景 C：實驗性開發

**想嘗試新想法，但不確定是否採用**：

```bash
# 建立實驗性 worktree
git worktree add ~/custom-skills-wt/spike-new-architecture -b spike/arch
cd ~/custom-skills-wt/spike-new-architecture

# 盡情實驗，即使搞砸了也不影響主開發
# ... 實驗程式碼 ...

# 如果實驗成功：
git add .
git commit -m "feat: 新架構實驗成功"
# 可以選擇 merge 回主分支

# 如果實驗失敗：
git worktree remove ~/custom-skills-wt/spike-new-architecture --force
# 乾乾淨淨，沒有遺留
```

---

## 常用指令速查表

### Worktree 管理

| 指令 | 說明 |
|------|------|
| `git worktree add <路徑> <分支>` | 建立 worktree |
| `git worktree add -b <新分支> <路徑> <基礎分支>` | 建立 worktree 並建立新分支 |
| `git worktree list` | 列出所有 worktree |
| `git worktree remove <路徑>` | 移除 worktree（安全檢查）|
| `git worktree remove <路徑> --force` | 強制移除（忽略未提交變更）|
| `git worktree prune` | 清理無效的 worktree 記錄 |

### 目錄切換

```bash
# 快速切換（使用 alias）
alias csw='cd ~/custom-skills-wt'

# 然後你可以：
csw/feature-a    # 到功能 A
csw/feature-b    # 到功能 B
csw/hotfix-xxx   # 到緊急修復
```

---

## 與基礎流程的對照

| 操作 | 基礎流程 (GIT-WORKFLOW.md) | Worktree 流程 |
|------|---------------------------|---------------|
| **建立分支** | `git checkout -b <name>` | `git worktree add ~/wt/<name> -b <name>` |
| **切換分支** | `git checkout <name>` | `cd ~/wt/<name>` |
| **暫存變更** | `git stash` | 不需要，目錄獨立 |
| **同步 main** | `git rebase main` | `git rebase main`（在各目錄執行）|
| **建立 PR** | `/git-commit pr` | `/git-commit pr`（在各目錄執行）|
| **清理分支** | `git branch -d <name>` | `git worktree remove ~/wt/<name>` |

---

## 常見問題

### Q: Worktree 跟手動建立多個 `git clone` 有什麼不同？

A: 概念上類似（都能同時在不同目錄操作不同分支），但有關鍵差異：

| | Worktree | 多個 Clone |
|---|---------|-----------|
| **`.git` 資料** | 共用一份 | 每個 clone 各一份（佔空間） |
| **分支鎖定** | 同一分支不能開兩個 worktree | 每個 clone 都能 checkout 同一分支 |
| **fetch/pull** | fetch 一次，所有 worktree 都能看到 | 每個 clone 要各自 fetch |
| **stash** | 共用 stash 清單 | 各自獨立 |
| **reflog/hooks** | 共用 | 各自獨立 |
| **磁碟空間** | 只多了工作檔案 | 完整複製整個 repo 歷史 |
| **remote 設定** | 共用 | 各自維護 |

**結論**：Worktree 是輕量級的多目錄方案，適合同一個人在本地同時處理多個分支。多個 clone 比較適合完全獨立的情境（例如不同機器、不同人、或需要同一分支的多個副本）。

### Q: Worktree 會佔用多少磁碟空間？

A: Git 使用硬連結共享物件資料庫，因此：
- **.git 目錄**：只有主目錄有完整的 .git，worktree 只佔用少量元資料（約幾 KB）
- **工作檔案**：每個 worktree 有獨立的工作檔案（這是必要的）
- **node_modules**：如果你有多個 worktree 都安裝了依賴，會有多份 node_modules

**建議**：定期清理不需要的 worktree，尤其是實驗性的。

### Q: 可以在 worktree 中再建立 worktree 嗎？

A: 不建議。Git 限制一個儲存庫只能有一層 worktree。所有 worktree 都應該從 main worktree 建立。

### Q: 如果主目錄（main worktree）刪除了，worktree 還能用嗎？

A: 不能。main worktree 包含完整的 .git 資料庫，刪除後所有 worktree 都會失效。建議：
- 保留 main worktree 作為「穩定基地」
- 只在 main worktree 執行 `git fetch`、`git remote` 等儲存庫級操作

### Q: IDE（VS Code）會混淆嗎？

A: 不會。每個 worktree 都是獨立的目錄，IDE 會把它們視為獨立的專案。你可以：
- 同時開啟多個 VS Code 視窗
- 每個視窗有自己的終端、自己的 Git 狀態
- 甚至可以在不同 worktree 執行不同的 npm script

### Q: 什麼時候不該用 worktree？

A: 
- **簡單的單線開發**：用基礎流程更簡單
- **磁碟空間極度受限**：多個 worktree = 多份 node_modules
- **不熟悉 Git**：worktree 增加了一層抽象，新手可能混淆

---

## 推薦的混合策略

### 日常開發（80% 時間）

```bash
# 單一功能開發，用基礎流程
cd ~/custom-skills
git checkout -b arlen-260127
# ... 開發 ...
/git-commit pr
```

### 並行開發（15% 時間）

```bash
# 需要同時處理多個功能，用 worktree
git worktree add ~/custom-skills-wt/feature-a -b arlen-feature-a
git worktree add ~/custom-skills-wt/feature-b -b arlen-feature-b
# ... 兩個視窗並行開發 ...
```

### 臨時任務（5% 時間）

```bash
# 緊急修復或 PR 審查，用 worktree
git worktree add ~/custom-skills-wt/hotfix-$(date +%y%m%d) main
# ... 快速處理 ...
git worktree remove ~/custom-skills-wt/hotfix-$(date +%y%m%d)
```

---

## 參考

- [GIT-WORKFLOW.md](./GIT-WORKFLOW.md) - 基礎 Git 工作流程
- [Git Worktree 官方文件](https://git-scm.com/docs/git-worktree)
- [DEVELOPMENT-WORKFLOW.md](./DEVELOPMENT-WORKFLOW.md) - OpenSpec 開發工作流程

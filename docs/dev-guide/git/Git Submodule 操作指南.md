
# Git Submodule 操作指南

## 1. 全域建議設定

```bash
# 讓 submodule 狀態更清楚
git config --global status.submoduleSummary true
git config --global diff.submodule log

# 若會用 file:// 或本機路徑當遠端，避免安全限制阻擋
git config --global protocol.file.allow always
```

---

## 2. 新增 Submodule

```bash
# 從遠端 Repo 新增
git submodule add <Repo URL>
git submodule add <Repo URL> <自訂路徑>

# 從本機路徑新增
git submodule add /path/to/local/repo <目標資料夾>
```

### 範例

```bash
git submodule add https://github.com/ValorVie/Rectify-Keyboard.git
git submodule add https://github.com/ValorVie/Rectify-Voice.git
git submodule add /Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/qdm-base-ezinvoice qdm-base-arlen
```

### 將已追蹤的資料夾轉為 Submodule

如果目標路徑已被 Git 追蹤，需先移除索引再重新加為 submodule：

```bash
git rm -r --cached opt/cert-auto-remove
git commit -m "remove cert-auto-remove from index"

git submodule add /path/to/repo opt/cert-auto-remove
git commit -m "add cert-auto-remove as submodule"
```

---

## 3. Clone 含有 Submodule 的專案

### 方式一：Clone 時一併下載（推薦）

```bash
git clone --recurse-submodules <專案 Repo URL>
```

### 方式二：已 Clone 後補初始化

如果已用一般 `git clone` 下載，submodule 資料夾會是空的，需執行：

```bash
git submodule update --init --recursive
```

| 參數 | 說明 |
|:---|:---|
| `update` | 更新子模組內容 |
| `--init` | 首次下載時初始化 `.gitmodules` 配置 |
| `--recursive` | 處理巢狀子模組（子模組中的子模組） |

---

## 4. 更新 Submodule

當別人更新了 submodule 版本，你在主專案 `git pull` 後，submodule **不會自動更新**。

```bash
# 方式一：手動更新
git submodule update

# 方式二：拉取時一併更新（推薦養成習慣）
git pull --recurse-submodules
```

---

## 5. 開發 Submodule 內的程式碼

> [!warning] Detached HEAD 陷阱
> 下載 submodule 後，Git 會將其鎖定在主專案記錄的**特定 Commit ID**，而不是某個分支。這稱為 **Detached HEAD** 狀態。
>
> 在此狀態下直接修改並 Commit，一旦切換目錄或更新，這些 Commit 容易變成「懸空（Dangling）」狀態而遺失。

### 正確流程

```bash
# 1. 進入 submodule 目錄
cd path/to/submodule

# 2. 切換到開發分支（必做！避免 Detached HEAD）
git checkout main  # 或該專案使用的分支名稱

# 3. 正常開發、commit、push
git add .
git commit -m "your changes"
git push

# 4. 回到主專案，更新 submodule 指向的 commit
cd ../..
git add path/to/submodule
git commit -m "update submodule to latest"
git push
```

---

## 6. 移除 Submodule

```bash
# 反初始化（清除本地工作目錄中的內容）
git submodule deinit -f <submodule-path>

# 從 Git 索引中移除
git rm -f <submodule-path>

# 清除 .git/modules 中的殘留（可選）
rm -rf .git/modules/<submodule-path>

git commit -m "remove submodule <name>"
```

---

## 7. 整理 WIP Commits（含 Submodule）

開發過程中常用數字序號（1, 2, 3...）快速 commit，完成後再整理成有意義的 commits。
當專案有 submodule 時，需要注意處理順序：**先整理 submodule，再整理 parent repo**。

> [!important] 核心原則
> - **由內而外**：先整理 submodule，再整理 parent repo
> - **Submodule pointer 是 parent 的一部分**：parent repo 記錄的是 submodule 的 commit hash，整理 submodule 後 hash 會改變
> - **用 `git checkout <commit> -- .` 取代 `git rebase -i`**：避免 detached HEAD 的 WIP commits 產生 merge conflict

### 前提：WIP 開發狀態

以 Rectify 專案為例，結構如下：

```
Rectify/                    ← parent repo (main branch)
├── Rectify-Voice/          ← submodule (detached HEAD, WIP commits)
└── Rectify-Keyboard/       ← submodule
```

WIP commits 在 detached HEAD 上（不在任何分支）：

```bash
# Rectify-Voice (submodule)
0a497d4 9          ← HEAD (detached)
1d39d8e 8
...
3bc3140 1
b846c3f init       ← main branch

# Rectify (parent)
d0b1c5a 9          ← dev branch
...
b448cd7 init       ← main branch
```

### Step 1：記錄 WIP 最終 commit hash

```bash
# 進入 submodule，記下最終 commit
cd Rectify-Voice
git log --oneline -1
# 0a497d4 9  ← 記住這個 hash

cd ..
```

### Step 2：規劃 commit 分組

查看每個 WIP commit 的內容，規劃合理分組：

```bash
cd Rectify-Voice
git log --oneline --stat b846c3f..0a497d4
```

例如將 10 個 WIP 分成 3 個有意義的 commit：

| 分組 | WIP 範圍 | 目標 commit 訊息 |
|:---|:---|:---|
| 1 | `6d3002e`..`d7eb501` | `功能(voice): 實作 MVP` |
| 2 | `71aa95f`..`0e98aa2` | `效能(voice): 延遲量化與模式分離` |
| 3 | `02149c6`..`0a497d4` | `修正(voice): 裝置選擇器與標點符號` |

### Step 3：整理 Submodule（由內而外）

使用 `git checkout <commit> -- .` 策略，將工作目錄切換到每個分組的終點狀態：

```bash
cd Rectify-Voice

# 切回 main（目前指向 init）
git checkout main

# 重置到起點
git reset --hard b846c3f

# === 第 1 個 squash commit ===
# 將工作目錄切換到第 1 組的最後一個 WIP commit
git checkout d7eb501 -- .
git add -A
git commit -m "功能(voice): 實作 MVP 端對端語音校正流程"

# === 第 2 個 squash commit ===
git checkout 0e98aa2 -- .
git add -A
git commit -m "效能(voice): 新增延遲量化與模式分離優化"

# === 第 3 個 squash commit ===
git checkout 0a497d4 -- .
git add -A
git commit -m "修正(voice): 修正裝置選擇器與 LLM 標點符號補全"
```

驗證整理後的結果與 WIP 最終狀態一致（應該沒有任何 diff）：

```bash
git diff 0a497d4 HEAD --stat
# 應輸出空白（零差異）
```

> [!tip] 為什麼用 `git checkout <commit> -- .` 而不是 `git rebase -i`？
> WIP commits 在 detached HEAD 上，不在任何分支。`rebase -i` 需要分支基礎，且 squash 多個 `add/add` 同檔案的 commits 容易產生 conflict。`checkout -- .` 直接將整個工作目錄切換到目標狀態，乾淨無衝突。

### Step 4：整理 Parent Repo

Submodule 整理完成後，main 上的 commit hash 已改變。回到 parent repo 用相同策略整理：

```bash
cd ..  # 回到 Rectify/

# 切到 main
git checkout main
git reset --hard b448cd7  # 重置到 init

# === 第 1 個 commit：文件變更 ===
# 取出 openspec 等文件（排除 submodule）
git checkout ae7f313 -- openspec/
# 將 submodule 指向對應的 commit
cd Rectify-Voice && git checkout 25c6834 && cd ..
git add openspec/ Rectify-Voice
git commit -m "文件: 新增 OpenSpec 效能優化與進階優化規劃文件"

# === 第 2 個 commit：歸檔與文件更新 ===
git checkout d0b1c5a -- openspec/ CHANGELOG.md
# 刪除已搬移到 archive 的舊路徑（checkout 只新增/修改，不刪除）
git rm -r openspec/changes/rectify-voice-mvp openspec/changes/rectify-voice-perf-optimization
# 將 submodule 指向最終 commit
cd Rectify-Voice && git checkout 88a78d8 && cd ..
git add openspec/ CHANGELOG.md Rectify-Voice
git commit -m "雜項: 歸檔已完成 changes，新增 CHANGELOG 與主 specs"
```

驗證最終結果：

```bash
# 與 WIP 最終狀態比對（排除 submodule pointer 差異）
git diff d0b1c5a HEAD --stat -- . ":(exclude)Rectify-Voice" ":(exclude)Rectify-Keyboard"
# 應輸出空白
```

### Step 5：清理與推送

```bash
# 刪除不再需要的 dev 分支
git branch -D dev

# 推送（先推 submodule，再推 parent）
cd Rectify-Voice
git push --force-with-lease origin main
cd ..
git push --force-with-lease origin main
```

> [!warning] `--force-with-lease` 是必要的
> 因為我們重寫了 main 的歷史（squash），必須 force push。`--force-with-lease` 比 `--force` 安全，它會在遠端有你未知的新 commit 時拒絕推送。

### 注意事項

1. **`git checkout <commit> -- .` 只新增和修改，不刪除**
   如果某些檔案在新狀態中不存在（例如搬移到 archive），需要手動 `git rm`

2. **Submodule pointer 是 parent commit 的一部分**
   整理 parent repo 時，需要在每個 commit 中將 submodule checkout 到對應的 commit，才能讓 pointer 正確

3. **整理前備份 WIP hash**
   記下所有 WIP 的最終 commit hash，整理完成後用 `git diff` 驗證零差異

4. **Detached HEAD 的 WIP commits 不會立即消失**
   Git 會保留 dangling commits 約 30 天（由 `gc.reflogExpire` 控制），整理期間隨時可以回溯

---

## 8. 常用指令速查

| 操作 | 指令 |
|:---|:---|
| 新增 submodule | `git submodule add <URL> [path]` |
| Clone 含 submodule | `git clone --recurse-submodules <URL>` |
| 初始化已 clone 的 submodule | `git submodule update --init --recursive` |
| 更新 submodule | `git submodule update` |
| Pull 時一併更新 | `git pull --recurse-submodules` |
| 查看 submodule 狀態 | `git submodule status` |
| 移除 submodule | `git submodule deinit -f <path>` + `git rm -f <path>` |
| Squash WIP（submodule 內） | `git checkout <wip-commit> -- .` + `git add -A` + `git commit` |
| 驗證 squash 結果 | `git diff <original-wip-hash> HEAD --stat` |
| 安全 force push | `git push --force-with-lease origin main` |

---

## Reference

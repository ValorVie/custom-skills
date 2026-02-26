# 多版本並行維護指南

當專案同時維護多個版本（如 v1 + v2 遷移），bug 修復需要同時落在多條分支上。本指南基於 custom-skills 專案的 v1 (Python/main) ↔ v2 (TypeScript/v2-bun-migration) 並行維護經驗整理。

---

## 快速決策流程

```
遇到 bug
  ├─ 只影響共用程式碼（server、config、migration）？
  │   └─ 在 main 修 → merge 到 feature branch
  │
  ├─ 只影響新版本 client？
  │   └─ 直接在 feature branch 修
  │
  └─ 兩邊都影響？
      ├─ 共用部分 + 舊版 client → 在 main 修並提交
      ├─ merge main 到 feature branch（自動拿到共用修復）
      └─ 新版 client → 在 feature branch 修
```

---

## 核心原則

### 1. 共用程式碼只改一次

如果某段程式碼在兩條分支上都存在且完全相同（如 server 端邏輯），**只在 main 改，再 merge 到 feature branch**。

**絕對不要**兩邊各改一次 — 會造成：
- merge 時衝突
- 兩邊實作微妙不同
- 忘記改其中一邊

### 2. 分側程式碼各改各的

如果兩條分支的 client 端是不同語言/架構（如 Python vs TypeScript），各自修改是不可避免的。

### 3. 修復順序：先 main 再 feature branch

```bash
# Step 1: 在 main 提交共用修復 + 舊版 client 修復
git checkout main
# 修改共用程式碼 + v1 client
git commit -m "修正(module): 修復描述"

# Step 2: 回到 feature branch，merge main
git checkout v2-bun-migration
git merge main
# 共用修復自動帶入，不需重複修改

# Step 3: 在 feature branch 補新版 client 修復
# 修改 v2 TypeScript client
git commit -m "修正(module): v2 client 端對應修復"
```

---

## 使用 Worktree 加速

當你需要在不 stash/commit 當前工作的情況下切到另一條分支修 bug：

```bash
# 建立 worktree 切到 main（不影響當前工作目錄）
git worktree add .worktrees/hotfix main

# 在 worktree 修復並提交
cd .worktrees/hotfix
# 修改、測試、commit
git push origin main

# 回到主目錄，merge main 的修復
cd /path/to/repo
git merge main

# 清理 worktree
git worktree remove .worktrees/hotfix
```

### Worktree 注意事項

- 一個 branch 同時只能被一個 worktree checkout
- worktree 被移除後不會影響 branch 上的 commit
- 建議用 `.worktrees/` 或 `.claude/worktrees/` 目錄，加入 `.gitignore`

---

## 識別程式碼歸屬

修 bug 前先判斷修改的檔案屬於哪一類：

| 類型 | 範例 | 在哪修 |
|------|------|--------|
| **共用** | server 端邏輯、DB migration、共用 config | main |
| **舊版獨有** | v1 Python client、v1 CLI | main |
| **新版獨有** | v2 TypeScript client、v2 CLI | feature branch |
| **兩版都有但不同實作** | 各自的 hash 算法、各自的 API client | 兩邊各改 |

---

## 實際案例：mem-sync hash 不一致修復

### 問題
`ai-dev mem push` 重複執行時出現 300 pushed / 174 skipped 分裂，應該全部 skipped。

### 根因（3 個 bug 交互）
1. Server hash 算法 ≠ Client hash 算法
2. 舊 DB 唯一約束未移除
3. Client 靜默吞掉 server 錯誤

### 修復分配

| 修改 | 歸屬 | 在哪修 |
|------|------|--------|
| Server hash 算法對齊 | 共用 | main（但此次在 v2 直接改，因為 v1 不跑 server） |
| Migration 003 移除舊約束 | 共用 | main |
| Server per-row 錯誤處理 | 共用 | main |
| v1 Python `compute_content_hash` | 舊版獨有 | main |
| v2 TypeScript `MemPushResult.errors` | 新版獨有 | v2 branch |
| v2 CLI 顯示 errors | 新版獨有 | v2 branch |

### 教訓
- Server 修復應該先在 main 提交再 merge 到 v2，避免重複修改
- 兩邊 client 的 hash 算法必須保持一致，這類「隱性耦合」最容易出問題

---

## 何時結束雙線維護

雙線維護成本隨時間線性增長。優先：

1. **盡快完成 feature branch 遷移**，合併回 main
2. 合併後**移除舊版程式碼**，消除同步負擔
3. 遷移期間**減少 main 上的新功能開發**，降低需要同步的變更量

---

## 檢查清單

提交跨分支修復前確認：

- [ ] 共用程式碼只改了一次（在 main）
- [ ] feature branch 已 merge main 的修復
- [ ] 兩邊的 client 行為一致（同樣的輸入產生同樣的結果）
- [ ] 兩邊的測試都通過
- [ ] commit message 標明影響範圍（如 `v1`、`v2`、`server`）

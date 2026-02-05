# Git 工作流程指南

本指南說明團隊的 Git 分支管理與 PR 流程。

---

## 快速參考

```
main ──┬── $username-$YYMMDD ──┬── 開發 & commits ──┬── rebase main ──┬── /git-commit pr ──┬── PR Review ──┬── Merge ──┬── 刪除分支
       │                  │                    │                 │                    │               │           │
       └──────────────────┴────────────────────┴─────────────────┴────────────────────┴───────────────┴───────────┘
```

| 步驟 | 命令/操作 | 說明 |
|------|-----------|------|
| 1. 建立分支 | `git checkout -b <name>` | 從 main 建立開發分支 |
| 2. 開發 | 正常開發 | commit 訊息可隨意 |
| 3. 同步 main | `git rebase main` 或 `git merge main` | 確保與主線同步 |
| 4. 建立 PR | `/git-commit pr` | 生成摘要並開啟草稿 PR |
| 5. 確認 PR | GitHub UI | 轉為正式 PR |
| 6. Code Review | 自動 + 人工 | Claude Code Action 自動審查 |
| 7. 合併 | GitHub UI | Squash merge |
| 8. 清理 | `git branch -d <name>` | 刪除開發分支 |

---

## 完整流程說明

### Step 1: 建立開發分支

從 `main`（或 `master`）分支建立個人開發分支。

**命名規則**：`<username>-<YYMMDD>` 或 `<username>-<feature>`

```bash
# 確保在最新的 main 分支
git checkout main
git pull origin main

# 建立開發分支
git checkout -b $username-$YYMMDD
```

**提示**：
- 使用日期命名（如 `arlen-260127`）適合持續開發
- 使用功能命名（如 `arlen-add-auth`）適合特定功能

---

### Step 2: 開發

正常進行開發工作。這個階段的 commit 訊息可以隨意寫，因為最後會 squash。

```bash
# 開發過程中的 commits
git add .
git commit -m "wip"
git commit -m "fix typo"
git commit -m "調整"
```

**提示**：
- 可以搭配 OpenSpec 工作流程進行開發（見 [DEVELOPMENT-WORKFLOW.md](DEVELOPMENT-WORKFLOW.md)）
- 頻繁 commit，避免遺失進度
- 不需要花時間寫完美的 commit message

---

### Step 3: 同步主線

在建立 PR 前，確保分支與主線同步。

**選項 A：Rebase（建議）**

```bash
git fetch origin
git rebase origin/main
```

如遇衝突：
```bash
# 解決衝突後
git add .
git rebase --continue
```

**選項 B：Merge**

```bash
git fetch origin
git merge origin/main
```

**何時用 Rebase vs Merge**：
- **Rebase**：保持線性歷史，適合個人分支
- **Merge**：保留分支歷史，適合共享分支

---

### Step 4: 建立 PR

使用 `/git-commit pr` 命令生成完整的 PR 摘要並開啟草稿 PR。

```
/git-commit pr
```

**這個命令會**：
1. 分析所有 commits 的變更
2. 生成結構化的 PR 標題和描述
3. 使用 `gh pr create --draft` 建立草稿 PR
4. 回傳 PR URL

**PR 描述格式**：
```markdown
## Summary
- 變更摘要 1
- 變更摘要 2

## Test plan
- [ ] 測試項目 1
- [ ] 測試項目 2
```

---

### Step 5: 確認 PR

到 GitHub 上檢視自己的 PR：

1. 開啟 PR URL
2. 檢查變更內容是否正確
3. 確認 PR 標題和描述
4. 如果沒問題，點擊 **「Ready for review」** 轉為正式 PR

**檢查清單**：
- [ ] 變更內容符合預期
- [ ] 沒有意外包含的檔案
- [ ] PR 描述清楚說明變更目的

---

### Step 6: Code Review

PR 轉為正式後，會觸發自動審查流程。

**自動審查（Claude Code GitHub Action）**：
- 自動執行 code review
- 在 PR 留言中回報結果
- 標記潛在問題

**人工審查**：
- 審核人員檢視 Claude Code 的審查結果
- 確認沒有問題後批准 PR
- 如有問題，在 PR 留言討論

**回應審查意見**：
```bash
# 根據審查意見修改程式碼
git add .
git commit -m "address review comments"
git push
```

---

### Step 7: 合併 PR

審查通過後，由審核人員或自己合併 PR。

**合併策略**：**Squash and merge**（建議）

- 將所有 commits 壓縮成一個
- 使用 PR 標題作為 commit message
- 保持主線歷史簡潔

**GitHub UI 操作**：
1. 點擊 **「Squash and merge」**
2. 確認 commit message
3. 點擊 **「Confirm squash and merge」**

---

### Step 8: 清理分支

合併後刪除開發分支。

**GitHub UI**：
- 合併後會顯示 **「Delete branch」** 按鈕
- 點擊即可刪除遠端分支

**本地清理**：
```bash
# 切回 main 並更新
git checkout main
git pull origin main

# 刪除本地分支
git branch -d arlen-260127

# 如果分支未完全合併，強制刪除
git branch -D arlen-260127
```

---

## 常見問題

### Q: 開發到一半需要切換到其他任務怎麼辦？

A: 使用 `git stash` 暫存變更：
```bash
git stash
git checkout other-branch
# 完成其他任務後
git checkout arlen-260127
git stash pop
```

### Q: Rebase 衝突太多怎麼辦？

A: 可以改用 merge，或分批 rebase：
```bash
# 中止 rebase
git rebase --abort

# 改用 merge
git merge origin/main
```

### Q: PR 合併後發現有問題怎麼辦？

A: 建立新分支修復，不要 force push 到 main：
```bash
git checkout main
git pull
git checkout -b arlen-hotfix
# 修復問題
git commit -m "fix: ..."
# 建立新 PR
```

### Q: 如何查看 PR 的 review 狀態？

A: 使用 GitHub CLI：
```bash
gh pr status
gh pr view <pr-number>
```

---

## 相關命令

| 命令 | 說明 |
|------|------|
| `/git-commit pr` | 建立 PR 並生成摘要 |
| `/commit` | 建立單一 commit |
| `gh pr list` | 列出所有 PR |
| `gh pr view` | 查看 PR 詳情 |
| `gh pr checks` | 查看 PR 檢查狀態 |

---

## 參考

- [DEVELOPMENT-WORKFLOW.md](DEVELOPMENT-WORKFLOW.md) - OpenSpec 開發工作流程
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow) - GitHub 官方工作流程指南

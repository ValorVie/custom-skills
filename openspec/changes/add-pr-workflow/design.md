# Design: add-pr-workflow

## Architecture Overview

```
git-commit pr [options]
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│                    pr.md (主控制器)                          │
│  - 解析參數                                                  │
│  - 路由到對應步驟                                            │
└─────────────────────────────────────────────────────────────┘
      │
      ├──── 1. 前置檢查 ──────────────────────────────────────┐
      │     - 分支檢查 (不可在主分支)                          │
      │     - gh CLI 檢查                                      │
      │     - 遠端分支檢查                                     │
      │                                                        │
      ├──── 2. 範圍判定 ──────────────────────────────────────┤
      │     - --range 解析                                     │
      │     - --from 解析                                      │
      │     - merge-base 自動偵測                              │
      │                                                        │
      ├──── 3. 變更分析 (pr-analyze.md) ──────────────────────┤
      │     - commit 歷史讀取                                  │
      │     - diff 統計                                        │
      │     - 摘要生成                                         │
      │                                                        │
      ├──── 4. 提交整理 (選用) ───────────────────────────────┤
      │     - soft reset                                       │
      │     - 重新提交                                         │
      │                                                        │
      ├──── 5. 推送 ──────────────────────────────────────────┤
      │     - push -u origin                                   │
      │                                                        │
      └──── 6. PR 建立 ───────────────────────────────────────┘
            - gh pr create
            - 顯示結果
```

## Module Design

### 1. pr.md - 主控制流程

**職責**：
- 參數解析與驗證
- 流程控制與錯誤處理
- 調用子模組

**輸入**：
- 使用者參數 (`--draft`, `--from`, `--range`, etc.)

**輸出**：
- PR URL
- 操作摘要

### 2. pr-analyze.md - PR 專用分析

**職責**：
- 分析 commit 範圍內的變更
- 生成 PR 標題與內文

**輸入**：
- `$BASE_SHA`：起始點
- `$HEAD_SHA`：結束點（通常為 HEAD）

**輸出**：
- `$PR_TITLE`：建議的 PR 標題
- `$PR_BODY`：建議的 PR 內文

## PR 內文模板設計

```markdown
## Summary

[自動生成的變更摘要，基於 commit messages 和 diff 分析]

## Changes

[條列式的主要變更項目]

- [變更項目 1]
- [變更項目 2]
- ...

## Files Changed

[變更的檔案清單，按類型分組]

**Modified:**
- path/to/file1.md
- path/to/file2.py

**Added:**
- path/to/new-file.md

**Deleted:**
- path/to/old-file.md

## Commit History

[若 --no-squash，列出包含的 commits]

<details>
<summary>Commits included (N)</summary>

- abc1234: commit message 1
- def5678: commit message 2
- ...

</details>

---

> Generated with [Claude Code](https://claude.ai/code)
```

## Commit 範圍判定邏輯

```
優先順序：

1. --range a..b
   └─ 明確指定範圍，直接使用

2. --from <commit>
   └─ 範圍 = <commit>..HEAD

3. 自動偵測
   ├─ 嘗試 merge-base HEAD origin/$MAIN_BRANCH
   ├─ 若失敗，嘗試 merge-base HEAD $MAIN_BRANCH
   └─ 若仍失敗，詢問使用者或報錯
```

### 範圍驗證

```bash
# 驗證範圍有效
git rev-list --count $BASE..$HEAD

# 若為 0，表示無變更
# 若失敗，表示範圍無效
```

## 整合提交 vs 保留提交

### 整合提交 (預設)

```bash
# 1. 暫存當前狀態
CURRENT_BRANCH=$(git branch --show-current)

# 2. Soft reset 到 base
git reset --soft $BASE_SHA

# 3. 重新提交
git add .
git commit -m "$SQUASHED_MESSAGE"

# 4. 推送 (force-with-lease 因為重寫歷史)
git push --force-with-lease -u origin $CURRENT_BRANCH
```

### 保留提交 (--no-squash)

```bash
# 直接推送
git push -u origin $CURRENT_BRANCH
```

## gh CLI 整合

### PR 建立指令

```bash
# 預設：建立草稿 PR
gh pr create \
  --title "$PR_TITLE" \
  --body "$PR_BODY" \
  --base "$BASE_BRANCH" \
  --draft

# 若使用 --direct：建立正式 PR（不加 --draft）
gh pr create \
  --title "$PR_TITLE" \
  --body "$PR_BODY" \
  --base "$BASE_BRANCH"
```

### 輸出行為

建立成功後只顯示 PR URL，不自動開啟瀏覽器：

```
✅ 草稿 PR 已建立：https://github.com/owner/repo/pull/123
```

### 錯誤處理

| 情境 | 處理 |
|------|------|
| gh 未安裝 | 提示安裝指令，中止 |
| 未登入 | 提示 `gh auth login`，中止 |
| PR 已存在 | 顯示現有 PR URL，詢問是否更新 |
| 遠端分支不存在 | 自動建立 (push -u) |

## 與現有模組的關係

### 重用

| 模組 | 重用內容 |
|------|----------|
| `_utils.md` | `$MAIN_BRANCH` 判斷 |
| `analyze.md` | merge-base 計算邏輯 |
| `push.md` | 分叉處理概念 |

### 新增

| 模組 | 職責 |
|------|------|
| `pr.md` | PR 流程主控制器 |
| `pr-analyze.md` | PR 標題/內文生成 |

### 不變

| 模組 | 原因 |
|------|------|
| `sync.md` | PR 流程不需要同步本地主分支 |
| `commit.md` | 使用獨立的整合邏輯 |
| `merge.md` | 職責不同 |

## Edge Cases

### 1. 分支尚未推送到遠端

```
現況：本地分支，無遠端追蹤
處理：自動 push -u origin <branch>
```

### 2. 遠端分支已有 PR

```
現況：gh pr create 失敗
處理：
  1. 偵測錯誤訊息
  2. 使用 gh pr view 取得現有 PR
  3. 詢問：「已存在 PR #123，是否更新？」
  4. 若是，推送更新並顯示 PR URL
```

### 3. main 分支有新提交

```
現況：merge-base 與 main HEAD 不同
處理：
  1. 警告使用者
  2. 建議先 rebase 或繼續（PR 後處理衝突）
```

### 4. 無任何變更

```
現況：BASE_SHA == HEAD
處理：
  1. 顯示訊息：「📭 無任何變更需要建立 PR」
  2. 中止流程
```

## Security Considerations

1. **不在 PR 內文中暴露敏感資訊**
   - 掃描 diff 中的敏感模式
   - 警告但不阻擋

2. **force-with-lease 而非 force**
   - 防止意外覆寫他人變更

3. **gh CLI 權限**
   - 使用者需自行管理 token
   - 不儲存或傳輸 token

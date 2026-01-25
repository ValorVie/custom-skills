# Proposal: add-pr-workflow

## Summary

為 `git-commit` 指令新增 `pr` 模式，自動化「整理提交 → 推送 → 建立 Pull Request」的完整流程。

## Background

### 現況

目前 `git-commit` 指令支援：
- `local` / `remote`：同步目標選擇
- `normal` / `final`：單次提交 vs 整合 WIP 提交
- `--push`：提交後推送
- `merge`：多分支整合測試

缺少的是**從開發分支到 PR 建立**的完整流程自動化。

### 最佳實踐分析

根據 GitHub Flow 工作流程，典型的 PR 流程為：

1. **先整理提交** → 將多個 WIP 提交整合為有意義的提交
2. **推送到遠端** → 確保遠端分支最新
3. **建立 PR** → 生成 PR 描述，包含變更摘要

#### 關於「先 Commit 還是直接 PR」

| 策略 | 優點 | 缺點 | 適用情境 |
|------|------|------|----------|
| 直接整合成 1 筆提交 + PR | 歷史乾淨、PR 描述即 Commit 訊息 | 本地開發歷程消失 | Squash Merge 策略 |
| 保留多筆提交 + PR | 保留詳細開發歷程 | PR 需額外撰寫摘要 | Merge Commit 策略 |
| 彈性選擇 | 依需求調整 | 需要判斷 | 混合情境 |

**建議**：預設採用「整合成 1 筆提交 + PR」，因為：
1. 本專案採用 Squash Merge 策略
2. 最終合併到 main 也會被 squash
3. 減少認知負擔，一個 PR = 一個有意義的變更

## Proposed Changes

### 新增 `pr` 模式

擴充 `git-commit` 指令，新增 `pr` 子指令：

```bash
# 基本用法
git-commit pr                      # 自動偵測範圍，整合提交並建立草稿 PR
git-commit pr --direct             # 建立正式 PR（非草稿）
git-commit pr --no-squash          # 保留所有提交，不整合

# 指定範圍
git-commit pr --from <commit>      # 從指定 commit 開始
git-commit pr --range <a>..<b>     # 指定 commit 範圍

# 快速選項
git-commit pr --base main          # 指定 base 分支（預設自動偵測）
git-commit pr --title "PR 標題"    # 指定 PR 標題
```

### 參數說明

| 參數 | 值 | 預設 | 說明 |
|------|-----|------|------|
| `pr` | subcommand | - | 建立 Pull Request 模式 |
| `--direct` | flag | - | 建立正式 PR（預設為草稿 PR） |
| `--no-squash` | flag | - | 不整合提交，保留所有 commits |
| `--from` | commit SHA | merge-base | 指定起始 commit |
| `--range` | a..b | - | 指定 commit 範圍 |
| `--base` | branch | main/master | 指定 PR 的 base 分支 |
| `--title` | string | 自動生成 | 指定 PR 標題 |
| `--body` | string | 自動生成 | 指定 PR 內文 |

### 執行流程

```
1. 前置檢查
   ├─ 確認不在主分支上
   ├─ 確認有遠端追蹤分支或可建立
   └─ 確認 gh CLI 可用

2. 範圍判定
   ├─ IF --range 指定 → 使用指定範圍
   ├─ IF --from 指定 → 從該 commit 到 HEAD
   └─ ELSE → 自動偵測 merge-base

3. 變更分析
   ├─ 讀取 commit 歷史
   ├─ 讀取程式碼差異
   └─ 生成變更摘要

4. 提交整理 (除非 --no-squash)
   ├─ git reset --soft $BASE_SHA
   ├─ git add .
   └─ git commit -m "[整合後的訊息]"

5. 推送
   └─ git push -u origin [branch]

6. 建立 PR
   ├─ 生成 PR 標題與內文
   └─ gh pr create --title --body --draft (除非 --direct)

7. 完成
   └─ 顯示 PR URL（不自動開啟瀏覽器）
```

## Implementation Strategy

### 模組設計

在 `skills/git-commit-custom/` 新增：

| 檔案 | 說明 |
|------|------|
| `pr.md` | PR 模式主流程 |
| `pr-analyze.md` | PR 專用的變更分析與摘要生成 |

### 路由更新

更新 `SKILL.md` 路由邏輯：

```
IF pr 子指令:
    → 讀取並執行 `pr.md`
    → 結束
```

### 與現有模組的關係

- **重用** `_utils.md`：主分支判斷
- **重用** `analyze.md` 的部分邏輯：基準點計算
- **新增** PR 專用的摘要生成邏輯

## Design Decisions

以下決策已確定：

1. **PR 建立後的行為**：只顯示 URL，不自動開啟瀏覽器
2. **草稿 PR 為預設**：`git-commit pr` 預設建立草稿 PR，使用 `--direct` 建立正式 PR
3. **Reviewer 指派**：不支援 `--reviewer` 參數，由使用者在 GitHub UI 指派

## Alternatives Considered

### A. 擴充現有 `final` 模式

將 PR 功能整合到 `git-commit remote final --push --pr`

**否決原因**：
- 參數組合變得複雜
- PR 建立是獨立的工作流程，不應綁定 push

### B. 建立獨立的 `git-pr` 指令

**否決原因**：
- 與 `git-commit` 的職責有重疊
- 使用者需要學習另一個指令
- 失去與現有提交流程的整合

## Success Criteria

1. `git-commit pr` 可成功建立 PR
2. 支援自訂 commit 範圍
3. 生成的 PR 描述清晰易讀
4. 與現有 `git-commit` 流程無衝突
5. 文件完整，包含使用範例

## Related

- [Source: Code] `commands/claude/git-commit.md`：現有指令定義
- [Source: Code] `skills/git-commit-custom/SKILL.md`：現有 Skill 路由
- [Source: Code] `.standards/options/github-flow.ai.yaml`：GitHub Flow 工作流程
- [Source: Code] `.standards/options/squash-merge.ai.yaml`：Squash Merge 策略

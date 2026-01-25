---
name: git-commit-custom
description: Git 提交工作流模組 - 提供同步、分析、提交、推送與合併功能
---

# Git Commit Custom Skill

此 Skill 提供 Git 提交工作流的模組化功能，供 `git-commit` 指令調用。

---

## 模組清單

| 模組 | 檔案 | 說明 |
|------|------|------|
| 共用工具 | `_utils.md` | 主分支判斷（main/master）、衝突處理、提交規範 |
| 同步 | `sync.md` | Stash、Rebase/Merge、Stash Pop |
| 分析 | `analyze.md` | 定義基準點、檢查變更 |
| 提交 | `commit.md` | Normal/Final 模式提交 |
| 推送 | `push.md` | 推送至遠端、處理分叉 |
| 合併 | `merge.md` | 多分支整合測試 |
| PR | `pr.md` | 建立 Pull Request 流程 |
| PR 分析 | `pr-analyze.md` | PR 專用的變更分析與摘要生成 |

---

## 使用方式

此 Skill 由 `git-commit` 指令調用，**不應直接使用**。

調用時，根據路由邏輯讀取對應的模組檔案：

### 前置準備（必須）

1. **讀取 `_utils.md`**：取得主分支名稱判斷與共用函式

### 路由邏輯

```
IF pr 子指令:
    → 讀取並執行 `pr.md`（內部調用 `pr-analyze.md`）
    → 結束

IF merge 子指令:
    → 讀取並執行 `merge.md`
    → 結束

IF 當前分支為主分支 (main/master):
    IF --direct:
        → 跳過同步，直接執行分析與提交
    ELSE:
        → 警告：「⚠️ 目前在主分支上，建議切換至開發分支。若要直接提交，請使用 --direct 參數。」
        → 中止流程

ELSE (開發分支):
    1. 讀取並執行 `sync.md`   — 環境同步
    2. 讀取並執行 `analyze.md` — 變更分析
    3. 讀取並執行 `commit.md`  — 執行提交
    4. IF --push:
        → 讀取並執行 `push.md` — 推送至遠端
```

### pr 模式路由

當使用 `git-commit pr` 時：

```
1. 讀取 `_utils.md`      — 取得主分支名稱
2. 讀取並執行 `pr.md`    — PR 主流程
   ├─ 前置檢查（分支、gh CLI）
   ├─ 範圍判定
   ├─ 讀取並執行 `pr-analyze.md` — 變更分析與摘要生成
   ├─ 提交整理（除非 --no-squash）
   ├─ 推送
   └─ 建立 PR（預設草稿，--direct 為正式）
```

### --direct 模式路由

當使用 `--direct` 在主分支提交時：

```
1. 讀取並執行 `analyze.md` — 變更分析
2. 讀取並執行 `commit.md`  — 執行提交
3. IF --push:
    → 讀取並執行 `push.md` — 推送至遠端
```

---

## 角色定義

執行此 Skill 時，你是一個資深的 DevOps 工程師與代碼審查專家。根據使用者指定的參數，執行對應的提交流程。

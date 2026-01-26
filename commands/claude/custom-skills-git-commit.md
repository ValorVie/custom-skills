---
name: custom-skills-git-commit
description: 統一的 Git 提交流程。支援本地/遠端同步、單次/整合提交、PR 建立模式。用法：custom-skills-git-commit [target] [mode] [flags]
---

## 參數說明

| 參數 | 值 | 預設 | 說明 |
|------|-----|------|------|
| `target` | `local` / `remote` | `local` | 同步目標：本地主分支或 origin/主分支 |
| `mode` | `normal` / `final` | `normal` | 提交模式：單次提交或整合 WIP 提交 |
| `--push` | flag | - | 僅 final 模式可用，提交後推送至遠端 |
| `--direct` | flag | - | 允許在主分支上直接提交，跳過同步步驟 |
| `--no-rebase` | flag | - | 強制使用 Merge 策略同步，不論分支類型 |
| `merge` | subcommand | - | 建立暫時性整合分支並合併多個功能分支 |
| `pr` | subcommand | - | 建立 Pull Request（整合提交 → 推送 → 建立 PR） |

### PR 模式參數

| 參數 | 值 | 預設 | 說明 |
|------|-----|------|------|
| `--direct` | flag | - | 建立正式 PR（預設為草稿 PR） |
| `--no-squash` | flag | - | 保留所有提交，不整合為單一提交 |
| `--from` | commit SHA | merge-base | 指定起始 commit |
| `--range` | a..b | - | 指定 commit 範圍 |
| `--base` | branch | main/master | 指定 PR 的 base 分支 |
| `--title` | string | 自動生成 | 指定 PR 標題 |
| `--body` | string | 自動生成 | 指定 PR 內文 |

### 常用組合

| 指令 | 說明 |
|------|------|
| `git-commit` | 同步本地主分支並提交 |
| `git-commit local` | 同步本地主分支並提交 |
| `git-commit remote` | 同步遠端主分支並提交 |
| `git-commit remote final` | 整合所有 WIP 提交為一個 |
| `git-commit remote final --push` | 整合提交後推送至遠端 |
| `git-commit --direct` | 在主分支上直接提交（不同步） |
| `git-commit merge feature/A feature/B` | 建立測試分支並合併多個功能分支 |
| `git-commit pr` | 整合提交並建立草稿 PR |
| `git-commit pr --direct` | 整合提交並建立正式 PR |
| `git-commit pr --no-squash` | 保留所有提交並建立草稿 PR |
| `git-commit pr --from abc123` | 從指定 commit 開始建立 PR |
| `git-commit pr --range abc..def` | 指定 commit 範圍建立 PR |

---

## 執行指引

**請讀取並檢查 skill 資料庫中的 `custom-skills-git-commit` Skill 並依照其指示執行。**

> [!IMPORTANT]
> 執行前必須先讀取 Skill 的 `SKILL.md` 取得完整路由邏輯與模組說明。

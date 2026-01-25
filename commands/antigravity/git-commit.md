---
name: git-commit
description: 統一的 Git 提交流程。支援本地/遠端同步與單次/整合提交模式。用法：git-commit [target] [mode] [flags]
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

---

## 執行指引

**請讀取並檢查 skill 資料庫中的 `git-commit-custom` Skill 並依照其指示執行。**

> [!IMPORTANT]
> 執行前必須先讀取 Skill 的 `SKILL.md` 取得完整路由邏輯與模組說明。
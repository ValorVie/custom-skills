---
title: ai-dev 命令分類評估
type: report/analysis
date: 2026-03-13
author: Codex
status: updated
---

# ai-dev 命令分類評估

## 摘要

本報告總結 `ai-dev` 命令面在完成 top-level phase pipeline 後的最終分類決策。重點不是重新命名命令，而是收斂命令契約：

- `keep`：保留現有命令模型
- `clarify`：補足 preview、help、section 與系統層揭露
- `needs_scope_fix`：統一 target / scope 契約
- `split`：把混合意圖或隱含後處理改成顯式模式

## 核心結論

### `keep`

- `clone`

### `clarify`

- `install`
- `update`
- `status`
- `toggle`
- `mem auto`

### `needs_scope_fix`

- `list`
- `standards switch`
- `standards sync`
- `hooks install`
- `hooks uninstall`
- `hooks status`

### `split`

- `init-from`
- `sync init`
- `mem pull`

## 最終契約

1. read-only 命令可以在未指定 `--target` 時代表 `all`
2. 任何會寫 target 的命令都必須顯式指定 `--target`
3. project state 命令不再自動同步任何 target
4. `ai-dev init-from update` 取代舊的 `--update`
5. `sync init` 需要顯式 `--mode bootstrap`
6. `mem pull` 的 `reindex` / `cleanup` 改成顯式 flags

## 關聯文件

- [ai-dev指令與資料流參考.md](/Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills/.worktrees/maintain-command-surface/docs/ai-dev指令與資料流參考.md)
- [ai-dev命令分類與設計壓力參考.md](/Users/arlen/Documents/syncthing/backup/Sympasoft/SympasoftCode/AI-framework/custom-skills/.worktrees/maintain-command-surface/docs/ai-dev命令分類與設計壓力參考.md)

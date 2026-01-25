# Change: 新增 everything-claude-code 儲存庫更新支援與更新提示

## Why

`ai-dev update` 指令目前會更新多個上游儲存庫（custom-skills、superpowers、universal-dev-standards、obsidian-skills、anthropic-skills），但缺少對 `everything-claude-code` 儲存庫的更新支援。使用者需要手動更新此儲存庫，或無法獲得 ECC 的最新功能與修正。

此外，目前的更新流程不會顯示哪些儲存庫有新的更新，使用者無法輕易知道哪些上游有變更。

## What Changes

1. **新增 everything-claude-code 儲存庫到更新清單**
   - 在 `script/utils/paths.py` 新增 `get_ecc_dir()` 函式
   - 在 `script/commands/update.py` 的 `repos` 清單中加入 ECC 路徑

2. **新增更新提示功能**
   - 在 git fetch 後檢測是否有新 commits
   - 記錄每個儲存庫的更新狀態（有新更新 / 已是最新）
   - 在更新完成後顯示摘要，列出有新更新的儲存庫

## Impact

- Affected specs: `cli-distribution`
- Affected code:
  - `script/utils/paths.py`：新增 `get_ecc_dir()` 函式
  - `script/commands/update.py`：修改 `update()` 函式

## Non-Goals

- 不會變更 `upstream/sources.yaml` 中 ECC 的定義（已存在）
- 不會變更 `ai-dev clone` 的行為（這是另一個指令）
- 不會變更現有儲存庫的更新邏輯（強制 reset 行為保持不變）

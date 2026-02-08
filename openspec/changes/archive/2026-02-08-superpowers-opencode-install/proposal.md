## Why

ai-dev 的 install/update 目前只維護 ~/.config/superpowers 以追蹤上游，未支援官方 OpenCode 安裝流程，導致 OpenCode 用戶無法自動取得 superpowers 插件與技能連結，需要手動 clone 與建立 symlink，體驗不一致且易遺漏更新。

## What Changes

- 在 ai-dev install/update 增加 OpenCode 專用流程：clone 上游至 `~/.config/opencode/superpowers` 並建立 plugins/skills symlink。
- 保留現有 `~/.config/superpowers` 以供上游追蹤，不影響 Claude Code 插件安裝。
- 覆寫/更新時處理現有 symlink 或目錄清理，確保重複執行安全冪等。
- （可選）在 docs/README 或命令說明中補充 OpenCode 安裝說明與驗證步驟。

## Capabilities

### New Capabilities
- `opencode-superpowers-install-update`: 於 ai-dev install/update 自動安裝與更新 superpowers 到 OpenCode（含 symlink 建立與冪等清理）。

### Modified Capabilities
- 無

## Impact

- commands/ai-dev install、update 流程（新增 OpenCode 分支）。
- scripts/ 或 hooks/ 內可能新增 OpenCode 安裝子流程與路徑常數。
- docs/（若補充使用說明或驗證步驟）。

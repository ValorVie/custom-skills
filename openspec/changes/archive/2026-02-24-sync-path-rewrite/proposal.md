## Why

`ai-dev sync` 會同步 `~/.claude-mem/settings.json`，其中 `CLAUDE_MEM_DATA_DIR` 包含硬編碼的絕對路徑（如 `/Users/arlen/.claude-mem`）。當同步到另一台設備時（不同使用者名稱或不同作業系統），該路徑會導致 claude-mem 無法正確運作。

目前 plugin 系統已透過 manifest 機制解決類似問題，但一般設定檔中的路徑尚未處理。

## What Changes

- Push 階段新增**路徑標準化**：將 sync repo 中 `settings.json` 的絕對路徑替換為 `{{HOME}}` 佔位符
- Pull 階段新增**路徑展開**：將 `{{HOME}}` 佔位符展開為當前系統的 `$HOME` 路徑
- 新增 `PATH_VARIABLES` 路徑變數 registry（目前僅 `HOME`，未來可擴展）
- 替換邏輯為 JSON value 層級掃描，只替換以 `$HOME` 開頭的 string value

## Capabilities

### New Capabilities

- `sync-path-rewrite`: 同步過程中的跨平台路徑標準化與展開機制

### Modified Capabilities

- `sync-engine`: 在 push/pull 流程中整合路徑替換步驟

## Impact

- **程式碼**：`script/utils/sync_config.py`（新增函數）、`script/commands/sync.py`（push/pull 流程整合）
- **測試**：需新增路徑替換的單元測試
- **Sync repo 格式**：`settings.json` 中的路徑值將改為 `{{HOME}}` 格式（repo 層級的格式變更，不影響本機檔案）

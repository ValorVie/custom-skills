## Why

目前 `commands/` 目錄下只有 `claude/`、`antigravity/` 和 `workflows/`，缺少 `opencode/` 目錄。雖然 `ai-dev clone` 的分發邏輯（`shared.py`）已預設 `commands/opencode` 來源路徑，但實際目錄不存在，導致 OpenCode 使用者無法透過 clone 取得 commands。

同時，`plugins/ecc-hooks/` 僅支援 Claude Code 的 hooks.json 格式，OpenCode 使用完全不同的 TypeScript plugin 系統，需要建立對應的 plugin wrapper。

目標是讓 `ai-dev clone` 後，Claude Code 和 OpenCode 使用者能取得相同的工具集。

## What Changes

- 新增 `commands/opencode/` 目錄，包含與 `commands/claude/` 對等的 command 檔案，移除 Claude 特有 frontmatter 欄位（`allowed-tools`、`argument-hint`），保留 `description`
- 新增 `plugins/ecc-hooks-opencode/` 目錄，以 TypeScript plugin 格式實作，透過 OpenCode 的 hook 事件呼叫現有 `scripts/` 腳本
- 更新 `script/utils/shared.py` 分發邏輯，新增 OpenCode plugin 的分發路徑
- 更新 `script/utils/paths.py`，新增 OpenCode plugin 目錄的路徑函式

## Capabilities

### New Capabilities
- `opencode-commands`: OpenCode 專用 commands 目錄，提供與 Claude Code 對等的 slash commands
- `opencode-plugin`: OpenCode 版 ecc-hooks plugin，以 TypeScript 格式包裝現有 code quality、memory persistence、strategic compact 腳本

### Modified Capabilities
- `clone-command`: 分發邏輯需新增 OpenCode plugin 路徑，確保 `ai-dev clone` 可分發 plugin 到 `~/.config/opencode/plugin/`

## Impact

- **檔案結構**: 新增 `commands/opencode/`（約 41 個 .md 檔案）、`plugins/ecc-hooks-opencode/`（TypeScript plugin + package.json）
- **CLI 程式碼**: `script/utils/shared.py`（COPY_TARGETS、分發邏輯）、`script/utils/paths.py`（新增路徑函式）
- **依賴**: OpenCode plugin 需要 `@opencode-ai/plugin` type import（開發依賴）
- **分發目標**: `~/.config/opencode/plugin/ecc-hooks/`（新增）

# Change: 重構 install/update 流程與新增 OpenCode 完整支援

## Why

目前 `install` 和 `update` 指令的邏輯複雜且不一致：
1. 外部套件（superpowers、UDS、obsidian-skills 等）直接從各自的 clone 位置複製到目標目錄
2. 複製流程中有大量重複程式碼，難以維護
3. OpenCode 只支援 `agent` 目錄，缺少 `skills` 和 `commands` 支援
4. Claude Code 仍使用 npm 安裝方式，但 Anthropic 已推薦使用 native 安裝

此外，專案需要支援「在專案資料夾執行時同步到專案目錄」的功能。

## What Changes

### 1. 三階段複製流程

**BREAKING**: 重新設計複製邏輯為三階段：

1. **Stage 1: Clone 外部套件到 `~/.config/<repo-name>`**
   - `superpowers` → `~/.config/superpowers`
   - `universal-dev-standards` → `~/.config/universal-dev-standards`
   - `obsidian-skills` → `~/.config/obsidian-skills`
   - `anthropic-skills` → `~/.config/anthropic-skills`

2. **Stage 2: 整合到 `~/.config/custom-skills`**
   - 將各來源的 skills/commands/agents 整合到統一的 custom-skills 目錄
   - 這是所有資源的「單一真相來源」

3. **Stage 3: 分發到各工具目錄**
   - Claude Code: `~/.claude/skills`, `~/.claude/commands`
   - Antigravity: `~/.gemini/antigravity/skills`, `~/.gemini/antigravity/global_workflows`
   - **OpenCode**: `~/.config/opencode/skills`, `~/.config/opencode/commands`, `~/.config/opencode/agent`
   - Codex: `~/.codex/skills`
   - Gemini CLI: `~/.gemini/skills`, `~/.gemini/commands`
   - 專案目錄（若在專案中執行）：`<project>/skills`, `<project>/command`, `<project>/agent`

### 2. 新增 OpenCode 完整支援

- 新增 `~/.config/opencode/skills` 目錄支援
- 新增 `~/.config/opencode/commands` 目錄支援
- 維持現有 `~/.config/opencode/agent` 支援

### 3. Claude Code Native 安裝相容性

- 從 `NPM_PACKAGES` 移除 `@anthropic-ai/claude-code`
- 新增 `check_claude_installed()` 函式檢測 claude 指令是否可用
- 若未安裝，顯示 native 安裝指引而非自動透過 npm 安裝

## Impact

- **Affected specs**: `setup-script`
- **Affected code**:
  - `script/commands/install.py`
  - `script/commands/update.py`
  - `script/utils/shared.py`
  - `script/utils/paths.py`
- **Backwards compatibility**: 現有目錄結構維持相容，新增的 OpenCode 目錄會自動建立

## Why

上游 everything-claude-code 修復了 Prettier hook 的命令注入漏洞（PR #102）。我們的 `ecc-hooks` plugin 使用類似模式（`execSync` + 字串串接），雖然有 `JSON.stringify` 保護，但仍存在潛在風險。同時上游也改進了 session ID fallback 邏輯，值得一併整合。

## What Changes

### 安全修復（優先）
- 將所有格式化腳本從 `execSync` 改為 `execFileSync` + 陣列參數
- 影響檔案（兩個 plugin 版本）：
  - `plugins/ecc-hooks/scripts/code-quality/lib/format-js.js`
  - `plugins/ecc-hooks/scripts/code-quality/lib/format-php.js`
  - `plugins/ecc-hooks/scripts/code-quality/lib/format-python.js`
  - `plugins/ecc-hooks-opencode/scripts/code-quality/lib/format-js.js`
  - `plugins/ecc-hooks-opencode/scripts/code-quality/lib/format-php.js`
  - `plugins/ecc-hooks-opencode/scripts/code-quality/lib/format-python.js`

### 功能改進（可選）
- Session ID fallback 改用 project name（git repo 名稱或目錄名稱）取代 PPID
- `commandExists` 函式改用 `spawnSync` 避免 shell 注入

## Capabilities

### New Capabilities

（無新功能，此為安全修復與改進）

### Modified Capabilities

- `hook-system`: 修改 Node.js Hook 實作的安全命令執行方式，以及 Strategic Compact Hook 的 session ID fallback 邏輯
  - 安全命令執行：從 `execSync` 字串串接改為 `execFileSync` 陣列參數
  - Session fallback：從 PPID 改為 project name（git repo 或目錄名稱）

## Impact

### 影響範圍
- **檔案**: 6 個格式化 lib 檔案（2 個 plugin × 3 個檔案）+ 2 個 Python utils
- **Plugin**: `ecc-hooks`（Claude Code）、`ecc-hooks-opencode`（OpenCode）
- **行為**: 無使用者可見變更，純內部安全改進
- **相容性**: 完全向後相容
- **測試**: 需更新對應單元測試

### 風險評估
- **低風險**: 僅改變命令執行方式，不改變功能行為
- **驗證方式**: 執行現有測試 + 手動觸發格式化 hook

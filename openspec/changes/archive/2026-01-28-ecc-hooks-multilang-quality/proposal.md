## Why

目前 ecc-hooks 的 PostToolUse hooks 僅支援 PR URL 提取功能，缺乏開發時的即時程式碼品質檢查。開發者在編輯檔案後無法立即得到格式化、型別檢查和 debug 程式碼警告，需要等到 commit 前才能發現問題。

整合 everything-claude-code 上游的多語言程式碼品質 hooks，可在編輯檔案的當下提供即時回饋，提升開發效率並減少 debug 程式碼進入 commit 的風險。

## What Changes

### 新增 PostToolUse Hooks

**JavaScript/TypeScript:**
- 編輯 `.ts/.tsx/.js/.jsx` 後自動執行 Prettier 格式化
- 編輯 `.ts/.tsx` 後執行 TypeScript 型別檢查（需有 tsconfig.json）
- 編輯 `.ts/.tsx/.js/.jsx` 後檢查並警告 `console.log` 存在

**PHP:**
- 編輯 `.php` 後自動執行 Pint 或 PHP-CS-Fixer 格式化
- 編輯 `.php` 後執行 PHPStan 靜態分析（需有 phpstan.neon）
- 編輯 `.php` 後檢查並警告 `var_dump`、`print_r`、`dd`、`dump`、`ray` 存在

**Python:**
- 編輯 `.py` 後自動執行 Ruff 或 Black 格式化
- 編輯 `.py` 後執行 mypy 型別檢查（需有 pyproject.toml 或 mypy.ini）
- 編輯 `.py` 後檢查並警告 `print`、`breakpoint`、`pdb`、`ic` 存在

### 更新 Stop Hook

- 擴展現有的 console.log 檢查，支援 PHP 和 Python 的 debug 程式碼偵測
- 統一使用 Node.js 實作以與上游保持一致

## Capabilities

### New Capabilities

- `code-quality-hooks`: 多語言即時程式碼品質檢查機制（格式化、靜態分析、debug 警告）

### Modified Capabilities

- `hook-system`: 新增 PostToolUse hooks 的程式碼品質檢查需求，擴展 Stop hook 支援多語言

## Impact

**受影響檔案:**
- `plugins/ecc-hooks/hooks/hooks.json` - 新增 9 個 PostToolUse hooks，更新 1 個 Stop hook

**外部依賴（可選，專案需自行安裝）:**
- JS/TS: `prettier`, `typescript`
- PHP: `pint` 或 `php-cs-fixer`, `phpstan`
- Python: `ruff` 或 `black`, `mypy`

**相容性:**
- 所有 hooks 都有工具存在性檢查，若專案未安裝對應工具則靜默跳過
- 使用 Node.js 實作，與上游 everything-claude-code 保持一致
- 不影響現有 Python 腳本（memory persistence、strategic compact）

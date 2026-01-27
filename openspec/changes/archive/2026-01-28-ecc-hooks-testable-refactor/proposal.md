## Why

ecc-hooks 目前的 PostToolUse 和 Stop hooks 使用 Node.js one-liner 格式，嵌入在 JSON 字串中難以單元測試。上游 everything-claude-code 已將複雜邏輯（如 Stop hook）抽取為獨立腳本，支援更好的可維護性和測試。

## What Changes

### 重構為獨立腳本

- 將 Stop hook 從 one-liner 重構為獨立的 `check-debug-code.js` 腳本
- 將 PostToolUse hooks 重構為獨立腳本：
  - `format-js.js` - Prettier 格式化
  - `check-typescript.js` - TypeScript 型別檢查
  - `warn-console-log.js` - console.log 警告
  - `format-php.js` - Pint/PHP-CS-Fixer 格式化
  - `check-phpstan.js` - PHPStan 靜態分析
  - `warn-php-debug.js` - PHP debug 警告
  - `format-python.js` - Ruff/Black 格式化
  - `check-mypy.js` - mypy 型別檢查
  - `warn-python-debug.js` - Python debug 警告

### 加入測試框架

- 加入 Jest 測試框架
- 為每個獨立腳本建立對應的測試檔案
- 測試覆蓋：正常情況、工具不存在、檔案不存在、錯誤處理

## Capabilities

### New Capabilities

- `hook-testing`: hooks 腳本的單元測試框架與測試案例

### Modified Capabilities

- `hook-system`: 將 one-liner hooks 重構為獨立腳本，hooks.json 改為引用外部腳本

## Impact

**受影響檔案:**
- `plugins/ecc-hooks/hooks/hooks.json` - 更新 command 引用獨立腳本
- `plugins/ecc-hooks/hooks/scripts/` - 新增目錄存放獨立腳本（10 個 .js 檔案）
- `plugins/ecc-hooks/tests/` - 新增目錄存放測試檔案

**新增依賴:**
- `jest` (devDependency) - 測試框架
- `package.json` - 新增於 plugins/ecc-hooks/

**相容性:**
- 功能行為不變，僅重構實作方式
- 與上游 everything-claude-code 架構對齊

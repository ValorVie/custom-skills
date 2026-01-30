## Why

ECC Hooks 的 `format-*.js` 已修正 `execSync` → `execFileSync` 避免 shell injection，但 `check-*.js` 系列仍殘留 `execSync` 搭配字串模板的用法。`check-mypy.js` 和 `check-phpstan.js` 將使用者可控的 `filePath` 傳入 shell 命令，存在命令注入風險。需統一修正以保持一致性並消除安全漏洞。

## What Changes

- 將 `check-mypy.js` 從 `execSync` 改為 `execFileSync`，移除 shell 字串拼接
- 將 `check-phpstan.js` 從 `execSync` 改為 `execFileSync`，移除 shell 字串拼接
- 將 `check-typescript.js` 從 `execSync` 改為 `execFileSync`（一致性）
- 將 `check-debug-code.js` 從 `execSync` 改為 `execFileSync`（一致性）
- 同步修正 `ecc-hooks-opencode` 對應的 4 個檔案
- 更新對應的 Jest 測試以匹配新的 `execFileSync` API

## Capabilities

### New Capabilities

（無新增能力）

### Modified Capabilities

- `hook-system`: 修正 code quality check hooks 的命令執行方式，從 shell 字串改為安全的陣列參數

## Impact

- `plugins/ecc-hooks/scripts/code-quality/lib/check-mypy.js`
- `plugins/ecc-hooks/scripts/code-quality/lib/check-phpstan.js`
- `plugins/ecc-hooks/scripts/code-quality/lib/check-typescript.js`
- `plugins/ecc-hooks/scripts/code-quality/lib/check-debug-code.js`
- `plugins/ecc-hooks-opencode/scripts/code-quality/lib/` 對應 4 個檔案
- `plugins/ecc-hooks/tests/code-quality/` 對應測試檔案
- 不影響 API、不影響使用者操作流程、不影響外部依賴

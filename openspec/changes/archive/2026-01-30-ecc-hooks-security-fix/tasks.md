## 1. 安全命令執行修復

- [x] 1.1 修改 `plugins/ecc-hooks/scripts/code-quality/lib/format-js.js`：將 `execSync` 改為 `execFileSync`
- [x] 1.2 修改 `plugins/ecc-hooks/scripts/code-quality/lib/format-php.js`：將 `execSync` 改為 `execFileSync`（Pint 和 PHP-CS-Fixer 兩處）
- [x] 1.3 修改 `plugins/ecc-hooks/scripts/code-quality/lib/format-python.js`：將 `execSync` 改為 `execFileSync`（Ruff 和 Black 兩處）

## 2. OpenCode 版本同步

- [x] 2.1 複製修改後的 `format-js.js` 到 `plugins/ecc-hooks-opencode/scripts/code-quality/lib/`
- [x] 2.2 複製修改後的 `format-php.js` 到 `plugins/ecc-hooks-opencode/scripts/code-quality/lib/`
- [x] 2.3 複製修改後的 `format-python.js` 到 `plugins/ecc-hooks-opencode/scripts/code-quality/lib/`
- [x] 2.4 使用 `diff` 驗證兩個目錄的 lib 檔案一致

## 3. Session ID Fallback 改進

- [x] 3.1 在 `plugins/ecc-hooks/scripts/utils.py` 新增 `get_project_name()` 函式
- [x] 3.2 修改 `plugins/ecc-hooks/scripts/strategic-compact/suggest-compact.py` 的 session_id fallback 邏輯
- [x] 3.3 同步修改到 `plugins/ecc-hooks-opencode/scripts/` 對應檔案

## 4. 測試驗證

- [x] 4.1 更新 `plugins/ecc-hooks/tests/` 的單元測試以 mock `execFileSync`
- [x] 4.2 執行 `npm test` 確認所有測試通過
- [x] 4.3 手動測試：編輯 `.js` 檔案觸發 Prettier hook
- [x] 4.4 手動測試：編輯 `.php` 檔案觸發 Pint/PHP-CS-Fixer hook
- [x] 4.5 手動測試：編輯 `.py` 檔案觸發 Ruff/Black hook

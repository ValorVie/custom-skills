## 1. ecc-hooks check-mypy.js 修正

- [x] 1.1 將 `plugins/ecc-hooks/scripts/code-quality/lib/check-mypy.js` 的 `execSync` 改為 `execFileSync`，命令參數改為陣列形式
- [x] 1.2 將依賴注入介面從 `deps.execSync` 改為 `deps.execFileSync`

## 2. ecc-hooks check-phpstan.js 修正

- [x] 2.1 將 `plugins/ecc-hooks/scripts/code-quality/lib/check-phpstan.js` 的 `execSync` 改為 `execFileSync`，命令參數改為陣列形式
- [x] 2.2 將依賴注入介面從 `deps.execSync` 改為 `deps.execFileSync`

## 3. ecc-hooks check-typescript.js 修正

- [x] 3.1 將 `plugins/ecc-hooks/scripts/code-quality/lib/check-typescript.js` 的 `execSync` 改為 `execFileSync`，移除 `2>&1` 改用 stdio 選項
- [x] 3.2 將依賴注入介面從 `deps.execSync` 改為 `deps.execFileSync`

## 4. ecc-hooks check-debug-code.js 修正

- [x] 4.1 將 `plugins/ecc-hooks/scripts/code-quality/lib/check-debug-code.js` 的 `execSync` 改為 `execFileSync`，git 命令參數改為陣列形式
- [x] 4.2 將依賴注入介面從 `deps.execSync` 改為 `deps.execFileSync`

## 5. ecc-hooks-opencode 同步修正

- [x] 5.1 同步修正 `plugins/ecc-hooks-opencode/scripts/code-quality/lib/check-mypy.js`
- [x] 5.2 同步修正 `plugins/ecc-hooks-opencode/scripts/code-quality/lib/check-phpstan.js`
- [x] 5.3 同步修正 `plugins/ecc-hooks-opencode/scripts/code-quality/lib/check-typescript.js`
- [x] 5.4 同步修正 `plugins/ecc-hooks-opencode/scripts/code-quality/lib/check-debug-code.js`

## 6. 測試更新

- [x] 6.1 更新 `plugins/ecc-hooks/tests/code-quality/check-mypy.test.js` 的 mock 從 `execSync` 改為 `execFileSync`
- [x] 6.2 更新 `plugins/ecc-hooks/tests/code-quality/check-phpstan.test.js` 的 mock 從 `execSync` 改為 `execFileSync`
- [x] 6.3 更新 `plugins/ecc-hooks/tests/code-quality/check-typescript.test.js` 的 mock 從 `execSync` 改為 `execFileSync`
- [x] 6.4 更新 `plugins/ecc-hooks/tests/code-quality/check-debug-code.test.js` 的 mock 從 `execSync` 改為 `execFileSync`

## 7. 驗證

- [x] 7.1 執行 `cd plugins/ecc-hooks && npm test` 確認所有測試通過
- [x] 7.2 執行 `diff` 比較 ecc-hooks 與 ecc-hooks-opencode 的 lib 目錄一致性
- [x] 7.3 確認無殘留的 `execSync` 使用（grep 驗證）

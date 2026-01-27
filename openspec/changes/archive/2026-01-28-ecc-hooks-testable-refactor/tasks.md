## 1. 專案設定

- [x] 1.1 建立 `plugins/ecc-hooks/package.json`（包含 Jest devDependency）
- [x] 1.2 建立 `plugins/ecc-hooks/scripts/code-quality/` 目錄
- [x] 1.3 建立 `plugins/ecc-hooks/tests/code-quality/` 目錄
- [x] 1.4 建立 Jest 配置檔 `plugins/ecc-hooks/jest.config.js`

## 2. 測試輔助函式

- [x] 2.1 建立 `tests/helpers/mock-input.js`（createMockInput 函式）
- [x] 2.2 建立 `tests/helpers/run-script.js`（runScript 函式）

## 3. JavaScript/TypeScript Hooks 重構

- [x] 3.1 建立 `scripts/code-quality/format-js.js`（Prettier 格式化）
- [x] 3.2 建立 `scripts/code-quality/check-typescript.js`（TypeScript 型別檢查）
- [x] 3.3 建立 `scripts/code-quality/warn-console-log.js`（console.log 警告）

## 4. PHP Hooks 重構

- [x] 4.1 建立 `scripts/code-quality/format-php.js`（Pint/PHP-CS-Fixer 格式化）
- [x] 4.2 建立 `scripts/code-quality/check-phpstan.js`（PHPStan 靜態分析）
- [x] 4.3 建立 `scripts/code-quality/warn-php-debug.js`（PHP debug 警告）

## 5. Python Hooks 重構

- [x] 5.1 建立 `scripts/code-quality/format-python.js`（Ruff/Black 格式化）
- [x] 5.2 建立 `scripts/code-quality/check-mypy.js`（mypy 型別檢查）
- [x] 5.3 建立 `scripts/code-quality/warn-python-debug.js`（Python debug 警告）

## 6. Stop Hook 重構

- [x] 6.1 建立 `scripts/code-quality/check-debug-code.js`（多語言 debug 檢查）

## 7. 單元測試

- [x] 7.1 建立 `tests/code-quality/format-js.test.js`
- [x] 7.2 建立 `tests/code-quality/check-typescript.test.js`
- [x] 7.3 建立 `tests/code-quality/warn-console-log.test.js`
- [x] 7.4 建立 `tests/code-quality/format-php.test.js`
- [x] 7.5 建立 `tests/code-quality/check-phpstan.test.js`
- [x] 7.6 建立 `tests/code-quality/warn-php-debug.test.js`
- [x] 7.7 建立 `tests/code-quality/format-python.test.js`
- [x] 7.8 建立 `tests/code-quality/check-mypy.test.js`
- [x] 7.9 建立 `tests/code-quality/warn-python-debug.test.js`
- [x] 7.10 建立 `tests/code-quality/check-debug-code.test.js`

## 8. 整合

- [x] 8.1 更新 `hooks/hooks.json` 引用獨立腳本
- [x] 8.2 移除 hooks.json 中的 one-liner 程式碼
- [x] 8.3 驗證所有測試通過
- [x] 8.4 驗證 hooks 功能正常運作

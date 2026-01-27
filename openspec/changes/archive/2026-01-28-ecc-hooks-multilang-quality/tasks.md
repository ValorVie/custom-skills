## 1. JavaScript/TypeScript PostToolUse Hooks

- [x] 1.1 新增 Prettier 自動格式化 hook（matcher: `.ts/.tsx/.js/.jsx`）
- [x] 1.2 新增 TypeScript 型別檢查 hook（matcher: `.ts/.tsx`，偵測 tsconfig.json）
- [x] 1.3 新增 console.log 即時警告 hook（matcher: `.ts/.tsx/.js/.jsx`）

## 2. PHP PostToolUse Hooks

- [x] 2.1 新增 Pint/PHP-CS-Fixer 自動格式化 hook（matcher: `.php`，偵測 vendor/bin/pint 或 .php-cs-fixer.php）
- [x] 2.2 新增 PHPStan 靜態分析 hook（matcher: `.php`，偵測 vendor/bin/phpstan）
- [x] 2.3 新增 PHP debug 程式碼警告 hook（matcher: `.php`，偵測 var_dump/print_r/dd/dump/ray）

## 3. Python PostToolUse Hooks

- [x] 3.1 新增 Ruff/Black 自動格式化 hook（matcher: `.py`，Ruff 優先，Black fallback）
- [x] 3.2 新增 mypy 型別檢查 hook（matcher: `.py`，偵測 pyproject.toml 或 mypy.ini）
- [x] 3.3 新增 Python debug 程式碼警告 hook（matcher: `.py`，偵測 print/breakpoint/pdb/ic，排除註解）

## 4. Stop Hook 更新

- [x] 4.1 重寫 Stop hook 為 Node.js 實作
- [x] 4.2 擴展支援 PHP debug 檢查（var_dump/print_r/dd/dump/ray）
- [x] 4.3 擴展支援 Python debug 檢查（print/breakpoint/pdb/ic，排除註解）

## 5. 整合與驗證

- [x] 5.1 更新 hooks.json 加入所有新 hooks
- [x] 5.2 更新 hooks.json description 欄位
- [x] 5.3 驗證 JS/TS hooks 正常運作（有/無 Prettier、有/無 tsconfig.json）
- [x] 5.4 驗證 PHP hooks 正常運作（有/無 Pint、有/無 PHPStan）
- [x] 5.5 驗證 Python hooks 正常運作（有/無 Ruff/Black、有/無 mypy）
- [x] 5.6 驗證 Stop hook 多語言檢查正常運作

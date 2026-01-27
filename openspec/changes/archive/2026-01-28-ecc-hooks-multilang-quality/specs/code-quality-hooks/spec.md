## ADDED Requirements

### Requirement: PostToolUse 自動格式化

系統 SHALL 在 Edit 工具編輯檔案後自動執行對應語言的格式化工具。

#### Scenario: JavaScript/TypeScript 格式化

- **WHEN** Edit 工具編輯 `.ts`、`.tsx`、`.js` 或 `.jsx` 檔案
- **THEN** 執行 `npx prettier --write` 格式化該檔案
- **AND** 若 Prettier 未安裝或執行失敗則靜默跳過

#### Scenario: PHP 格式化

- **WHEN** Edit 工具編輯 `.php` 檔案
- **THEN** 向上搜尋專案根目錄
- **AND** 若存在 `vendor/bin/pint` 則執行 Pint 格式化
- **AND** 若存在 `.php-cs-fixer.php` 或 `.php-cs-fixer.dist.php` 則執行 PHP-CS-Fixer
- **AND** 若兩者皆無則靜默跳過

#### Scenario: Python 格式化

- **WHEN** Edit 工具編輯 `.py` 檔案
- **THEN** 優先嘗試執行 `ruff format` 格式化
- **AND** 若 Ruff 失敗則嘗試執行 `black` 格式化
- **AND** 若兩者皆失敗則靜默跳過

### Requirement: PostToolUse 靜態分析

系統 SHALL 在 Edit 工具編輯檔案後執行對應語言的靜態分析工具。

#### Scenario: TypeScript 型別檢查

- **WHEN** Edit 工具編輯 `.ts` 或 `.tsx` 檔案
- **THEN** 向上搜尋 `tsconfig.json`
- **AND** 若存在則執行 `npx tsc --noEmit`
- **AND** 輸出與該檔案相關的錯誤訊息（最多 10 行）
- **AND** 若 tsconfig.json 不存在則跳過

#### Scenario: PHPStan 靜態分析

- **WHEN** Edit 工具編輯 `.php` 檔案
- **THEN** 向上搜尋 `vendor/bin/phpstan`
- **AND** 若存在則執行 `phpstan analyse --error-format=raw`
- **AND** 輸出錯誤訊息（最多 10 行）
- **AND** 若 PHPStan 未安裝則跳過

#### Scenario: Mypy 型別檢查

- **WHEN** Edit 工具編輯 `.py` 檔案
- **THEN** 向上搜尋 `pyproject.toml` 或 `mypy.ini`
- **AND** 若存在則執行 `mypy --no-error-summary`
- **AND** 輸出與該檔案相關的 error 訊息（最多 10 行）
- **AND** 若配置不存在則跳過

### Requirement: PostToolUse Debug 程式碼警告

系統 SHALL 在 Edit 工具編輯檔案後檢查並警告 debug 程式碼存在。

#### Scenario: JavaScript/TypeScript console.log 警告

- **WHEN** Edit 工具編輯 `.ts`、`.tsx`、`.js` 或 `.jsx` 檔案
- **THEN** 檢查檔案內容是否包含 `console.log`
- **AND** 若存在則輸出警告訊息 `[Hook] WARNING: console.log found in <file>`
- **AND** 顯示包含 console.log 的行號與內容（最多 5 行）
- **AND** 輸出提醒 `[Hook] Remove before committing`

#### Scenario: PHP debug 程式碼警告

- **WHEN** Edit 工具編輯 `.php` 檔案
- **THEN** 檢查檔案是否包含 `var_dump(`、`print_r(`、`dd(`、`dump(`、`error_log(` 或 `ray(`
- **AND** 若存在則輸出警告訊息 `[Hook] WARNING: Debug code found in <file>`
- **AND** 顯示包含 debug 程式碼的行號與內容（最多 5 行）
- **AND** 輸出提醒 `[Hook] Remove var_dump/print_r/dd/dump/ray before committing`

#### Scenario: Python debug 程式碼警告

- **WHEN** Edit 工具編輯 `.py` 檔案
- **THEN** 檢查檔案是否包含 `print(`、`pprint(`、`breakpoint(`、`pdb.` 或 `ic(`
- **AND** 排除註解行（以 `#` 開頭）
- **AND** 若存在則輸出警告訊息 `[Hook] WARNING: Debug code found in <file>`
- **AND** 顯示包含 debug 程式碼的行號與內容（最多 5 行）
- **AND** 輸出提醒 `[Hook] Remove print/breakpoint/pdb/ic before committing`

### Requirement: Stop Hook 多語言 Debug 檢查

系統 SHALL 在每次回應結束後檢查所有修改檔案的 debug 程式碼。

#### Scenario: 多語言統一檢查

- **WHEN** Claude 回應結束（Stop 事件）
- **THEN** 取得 git 中所有已修改的檔案
- **AND** 依檔案副檔名套用對應的 debug 檢查規則
- **AND** `.ts/.tsx/.js/.jsx` 檢查 `console.log`
- **AND** `.php` 檢查 `var_dump/print_r/dd/dump/ray`
- **AND** `.py` 檢查 `print/breakpoint/pdb/ic`（排除註解）
- **AND** 若任一檔案存在 debug 程式碼則輸出警告

#### Scenario: 非 Git 專案處理

- **WHEN** 當前目錄不是 Git 儲存庫
- **THEN** 靜默跳過 Stop hook 檢查
- **AND** 不輸出任何錯誤訊息

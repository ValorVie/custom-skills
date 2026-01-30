## MODIFIED Requirements

### Requirement: Node.js Hook 實作

PostToolUse 程式碼品質 Hooks SHALL 使用 Node.js 獨立腳本實作，並遵循安全的命令執行方式。

#### Scenario: 獨立腳本格式（取代 One-liner）

- **WHEN** 配置 PostToolUse 品質檢查 hook
- **THEN** 使用 `node "${CLAUDE_PLUGIN_ROOT}/scripts/code-quality/<script>.js"` 格式
- **AND** 從 stdin 讀取 JSON 輸入
- **AND** 解析 `tool_input.file_path` 取得編輯的檔案路徑
- **AND** 將原始輸入輸出至 stdout

#### Scenario: 腳本目錄結構

- **WHEN** 組織程式碼品質 hooks 腳本
- **THEN** 腳本位於 `scripts/code-quality/` 目錄
- **AND** 每個功能對應一個獨立的 `.js` 檔案
- **AND** 腳本檔案使用 kebab-case 命名

#### Scenario: 腳本檔案清單

- **WHEN** 建立程式碼品質 hooks
- **THEN** 包含 `format-js.js`（Prettier 格式化）
- **AND** 包含 `check-typescript.js`（TypeScript 型別檢查）
- **AND** 包含 `warn-console-log.js`（console.log 警告）
- **AND** 包含 `format-php.js`（Pint/PHP-CS-Fixer 格式化）
- **AND** 包含 `check-phpstan.js`（PHPStan 靜態分析）
- **AND** 包含 `warn-php-debug.js`（PHP debug 警告）
- **AND** 包含 `format-python.js`（Ruff/Black 格式化）
- **AND** 包含 `check-mypy.js`（mypy 型別檢查）
- **AND** 包含 `warn-python-debug.js`（Python debug 警告）
- **AND** 包含 `check-debug-code.js`（Stop hook 多語言檢查）

#### Scenario: 安全命令執行

- **WHEN** 腳本需執行外部命令（如 prettier, pint, ruff, mypy, phpstan, tsc, git）
- **THEN** 使用 `execFileSync` 取代 `execSync`
- **AND** 命令參數以陣列傳遞，不使用字串串接
- **AND** 不依賴 shell 解析命令
- **AND** 範例：`execFileSync('npx', ['prettier', '--write', filePath], options)`
- **AND** 範例：`execFileSync('mypy', ['--no-error-summary', filePath], options)`
- **AND** 範例：`execFileSync(phpstanPath, ['analyse', '--error-format=raw', filePath], options)`
- **AND** 範例：`execFileSync('git', ['rev-parse', '--git-dir'], options)`

#### Scenario: 禁止的命令執行模式

- **WHEN** 實作命令執行
- **THEN** 禁止使用 `execSync` 搭配字串模板
- **AND** 禁止使用 shell 字串串接（如 `command + " " + arg`）
- **AND** 禁止依賴 `JSON.stringify` 作為唯一的安全措施
- **AND** 禁止在 `execFileSync` 中使用 `shell: true` 選項

#### Scenario: 依賴注入介面

- **WHEN** 腳本支援測試用依賴注入
- **THEN** 使用 `deps.execFileSync` 作為注入點
- **AND** 預設值為 `require('child_process').execFileSync`
- **AND** 禁止使用 `deps.execSync` 作為注入名稱

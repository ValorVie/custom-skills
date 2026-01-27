## MODIFIED Requirements

### Requirement: Node.js Hook 實作

PostToolUse 程式碼品質 Hooks SHALL 使用 Node.js 獨立腳本實作。

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

### Requirement: 腳本標準介面

所有獨立腳本 SHALL 遵循統一的介面標準。

#### Scenario: 輸入處理

- **WHEN** 腳本接收輸入
- **THEN** 從 `process.stdin` 讀取資料
- **AND** 將輸入解析為 JSON
- **AND** 存取 `tool_input.file_path` 取得檔案路徑

#### Scenario: 輸出處理

- **WHEN** 腳本完成處理
- **THEN** 將原始輸入（未修改）輸出至 `console.log`
- **AND** 將警告或訊息輸出至 `console.error`
- **AND** 確保在任何情況下都輸出原始輸入

#### Scenario: 錯誤處理

- **WHEN** 腳本執行過程發生錯誤
- **THEN** 使用 try-catch 捕捉所有錯誤
- **AND** 靜默處理錯誤不中斷流程
- **AND** 在 finally 區塊確保輸出原始輸入

### Requirement: hooks.json 配置更新

hooks.json SHALL 更新為引用獨立腳本。

#### Scenario: PostToolUse hooks 配置

- **WHEN** 配置 PostToolUse hooks
- **THEN** command 格式為 `node "${CLAUDE_PLUGIN_ROOT}/scripts/code-quality/<script>.js"`
- **AND** 不再使用 `node -e "..."` one-liner 格式

#### Scenario: Stop hook 配置

- **WHEN** 配置 Stop hook
- **THEN** command 為 `node "${CLAUDE_PLUGIN_ROOT}/scripts/code-quality/check-debug-code.js"`
- **AND** 支援多語言（JS/TS、PHP、Python）debug 程式碼檢查

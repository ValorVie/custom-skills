# hook-system Delta Specification

此 delta spec 修改 `openspec/specs/hook-system/spec.md` 的安全性與 session fallback 相關需求。

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

- **WHEN** 腳本需執行外部命令（如 prettier, pint, ruff）
- **THEN** 使用 `execFileSync` 取代 `execSync`
- **AND** 命令參數以陣列傳遞，不使用字串串接
- **AND** 不依賴 shell 解析命令
- **AND** 範例：`execFileSync('npx', ['prettier', '--write', filePath], options)`

#### Scenario: 禁止的命令執行模式

- **WHEN** 實作命令執行
- **THEN** 禁止使用 `execSync` 搭配字串模板
- **AND** 禁止使用 shell 字串串接（如 `command + " " + arg`）
- **AND** 禁止依賴 `JSON.stringify` 作為唯一的安全措施

### Requirement: Strategic Compact Hook

系統 SHALL 提供策略性 context 壓縮建議機制，並使用穩定的 session 識別方式。

#### Scenario: Compact 建議觸發

- **GIVEN** PreToolUse 事件（Edit 或 Write 工具）
- **WHEN** 累計工具調用次數超過閾值（預設 50）
- **THEN** 執行 `suggest-compact.py`
- **AND** 輸出壓縮建議訊息
- **AND** 每 25 次調用後重複提醒

#### Scenario: 可配置閾值

- **WHEN** 設定環境變數 `COMPACT_THRESHOLD`
- **THEN** 使用指定值作為建議閾值
- **AND** 預設值為 50

#### Scenario: 策略性建議時機

- **WHEN** 輸出壓縮建議
- **THEN** 建議在探索完成後、執行前壓縮
- **AND** 建議在完成 milestone 後壓縮
- **AND** 建議在 context 轉換前壓縮

#### Scenario: Session ID Fallback

- **WHEN** 取得 Session ID 用於計數器檔案
- **THEN** 優先使用 `CLAUDE_SESSION_ID` 環境變數
- **AND** 若不存在則使用 `getProjectName()` 函式取得專案名稱
- **AND** 專案名稱優先取自 git repository 名稱
- **AND** 若非 git 專案則使用目前目錄名稱
- **AND** 若以上皆失敗則使用 `'default'`

#### Scenario: 禁止的 Fallback 方式

- **WHEN** 實作 session ID fallback
- **THEN** 禁止使用 `PPID` 作為 fallback（不穩定）
- **AND** 禁止使用隨機值（無法跨 session 追蹤）

## ADDED Requirements

### Requirement: 雙 Plugin 同步

ecc-hooks 系統 SHALL 同時維護 Claude Code 與 OpenCode 兩個版本的 scripts。

#### Scenario: Scripts 內容一致性

- **WHEN** 修改 `plugins/ecc-hooks/scripts/code-quality/lib/*.js`
- **THEN** 同步修改 `plugins/ecc-hooks-opencode/scripts/code-quality/lib/*.js`
- **AND** 兩者內容保持完全一致

#### Scenario: 驗證同步

- **WHEN** 完成修改後
- **THEN** 使用 `diff` 命令驗證兩個目錄的 lib 檔案一致
- **AND** 測試兩個版本的 hooks 皆能正常運作

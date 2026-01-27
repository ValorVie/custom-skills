# hook-system Specification

## Purpose
TBD - created by archiving change integrate-ecc-full-expansion. Update Purpose after archive.
## Requirements
### Requirement: Claude Code Hook 支援

系統 SHALL 提供 Claude Code 事件 Hook 的 Python 及 Node.js 實作。

#### Scenario: 支援的 Hook 事件

- **WHEN** Claude Code 觸發事件
- **THEN** 支援 SessionStart 事件
- **AND** 支援 SessionEnd 事件
- **AND** 支援 PreCompact 事件
- **AND** 支援 PreToolUse 事件
- **AND** 支援 PostToolUse 事件
- **AND** 支援 Stop 事件

#### Scenario: Hook 配置格式

- **WHEN** 配置 Hooks
- **THEN** 使用 `hooks.json` 格式
- **AND** 支援 matcher 條件過濾
- **AND** 支援 command 執行腳本
- **AND** command 可使用 Python 或 Node.js

#### Scenario: 混合語言支援

- **WHEN** 同一 hooks.json 配置多個 hooks
- **THEN** 支援 Python 腳本（memory persistence）
- **AND** 支援 Node.js 腳本（程式碼品質檢查）
- **AND** 兩種語言的 hooks 可並存運作

### Requirement: Memory Persistence Hooks

系統 SHALL 提供記憶持久化 Hook 機制。

#### Scenario: Session Start Hook

- **WHEN** Claude Code 新 Session 開始
- **THEN** 執行 `session-start.py`
- **AND** 載入先前 Session 的 context
- **AND** 偵測專案的 package manager（npm/yarn/pnpm/bun）
- **AND** 將 context 輸出供 Claude 讀取

#### Scenario: Session End Hook

- **WHEN** Claude Code Session 結束
- **THEN** 執行 `session-end.py`
- **AND** 儲存當前 Session 狀態
- **AND** 記錄重要的對話摘要
- **AND** 儲存至 `~/.claude/sessions/` 或專案本地 `.claude/`

#### Scenario: Pre-Compact Hook

- **WHEN** Claude Code 即將執行 compact
- **THEN** 執行 `pre-compact.py`
- **AND** 儲存當前狀態快照
- **AND** 記錄 compact 前的關鍵資訊

### Requirement: PostToolUse 程式碼品質 Hooks

系統 SHALL 在 PostToolUse 事件提供程式碼品質檢查機制。

#### Scenario: PostToolUse Edit 觸發

- **WHEN** Edit 工具完成檔案編輯
- **THEN** 根據檔案副檔名觸發對應的品質檢查 hooks
- **AND** 支援 `.ts/.tsx/.js/.jsx` 觸發 JavaScript/TypeScript hooks
- **AND** 支援 `.php` 觸發 PHP hooks
- **AND** 支援 `.py` 觸發 Python hooks

#### Scenario: Hook 執行順序

- **WHEN** 多個 PostToolUse hooks 符合條件
- **THEN** 依序執行：格式化 → 靜態分析 → debug 警告
- **AND** 前一個 hook 失敗不影響後續 hook 執行

### Requirement: Strategic Compact Hook

系統 SHALL 提供策略性 context 壓縮建議機制。

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

### Requirement: Hook 跨平台相容

所有 Hook 腳本 SHALL 相容 Windows、macOS 和 Linux。

#### Scenario: Python 跨平台執行

- **WHEN** Hook 腳本執行
- **THEN** 使用 Python 標準庫
- **AND** 避免 shell-specific 語法
- **AND** 使用 `pathlib` 處理路徑

#### Scenario: Node.js 跨平台執行

- **WHEN** Node.js Hook 腳本執行
- **THEN** 使用 Node.js 標準庫（fs, path, child_process）
- **AND** 使用 `path.join()` 處理路徑
- **AND** 避免 shell-specific 語法

#### Scenario: 檔案路徑處理

- **WHEN** 存取檔案路徑
- **THEN** 使用 `os.path` 或 `pathlib`（Python）
- **AND** 使用 `path` 模組（Node.js）
- **AND** 正確處理 Windows 與 Unix 路徑分隔符

#### Scenario: 環境變數存取

- **WHEN** 讀取環境變數
- **THEN** 使用 `os.environ.get()`（Python）
- **AND** 使用 `process.env`（Node.js）
- **AND** 提供合理預設值

### Requirement: Hook 狀態儲存

Hook 系統 SHALL 提供狀態儲存機制。

#### Scenario: 狀態儲存位置

- **WHEN** 儲存 Session 狀態
- **THEN** 優先儲存至專案本地 `.claude/sessions/`
- **AND** 若無專案則儲存至 `~/.claude/sessions/`

#### Scenario: 狀態檔案格式

- **WHEN** 儲存狀態檔案
- **THEN** 使用 JSON 格式
- **AND** 包含時間戳記
- **AND** 包含 Session ID

#### Scenario: 狀態檔案清理

- **WHEN** 狀態檔案過多
- **THEN** 保留最近 10 個 Session 狀態
- **AND** 自動刪除舊的狀態檔案

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

### Requirement: hooks.json 配置

系統 SHALL 提供 hooks.json 配置範例。

#### Scenario: 配置檔案結構

- **WHEN** 建立 hooks.json
- **THEN** 包含 `$schema` 欄位（驗證用）
- **AND** 包含 `hooks` 物件
- **AND** 按事件類型分組（PreToolUse, PostToolUse, SessionStart 等）

#### Scenario: Hook 定義結構

- **WHEN** 定義單一 Hook
- **THEN** 包含 `matcher` 條件
- **AND** 包含 `hooks` 陣列（執行的 commands）
- **AND** 可選 `description` 說明

#### Scenario: Matcher 條件語法

- **WHEN** 定義 matcher
- **THEN** 支援 `*` 匹配所有
- **AND** 支援 `tool == "Bash"` 工具匹配
- **AND** 支援 `tool_input.file_path matches "*.ts"` 路徑匹配


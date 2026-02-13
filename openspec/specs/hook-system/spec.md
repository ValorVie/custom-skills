# hook-system Specification

## Purpose

Hook System 為 Claude Code 提供事件驅動的擴展機制，實現以下核心價值：

1. **記憶持久化**：跨 Session 保存對話上下文與專案狀態，提升 AI 助手的連貫性
2. **自動化品質檢查**：在編輯檔案後自動執行格式化、靜態分析與 debug 程式碼偵測
3. **策略性資源管理**：透過 Compact 建議機制優化 context 使用效率
4. **跨平台相容**：支援 Windows、macOS 和 Linux，使用 Python 與 Node.js 雙語言實作
5. **可擴展架構**：基於 hooks.json 配置的模組化設計，便於新增自訂 Hooks
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
- **AND** 透過 subprocess 呼叫 Node.js 讀取 session 別名
- **AND** 若有可用別名則顯示最近 5 個別名（名稱與 session 路徑）
- **AND** 若 Node.js 不可用或別名讀取失敗則靜默跳過，不影響現有功能

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

### Requirement: Auto-Skill Hooks 獨立插件

系統 SHALL 提供獨立的 `auto-skill-hooks` 插件，負責在 SessionStart 時注入知識庫與經驗索引。此插件與 ecc-hooks 職責分離，可獨立啟用/停用。

#### Scenario: 插件獨立運作

- **WHEN** 啟用 `auto-skill-hooks@custom-skills` 插件
- **THEN** 插件的 SessionStart hook 獨立於 ecc-hooks 的 SessionStart hook 執行
- **AND** 停用 auto-skill-hooks 不影響 ecc-hooks 的記憶持久化功能
- **AND** 停用 ecc-hooks 不影響 auto-skill-hooks 的知識注入功能

#### Scenario: 插件註冊

- **WHEN** 安裝 auto-skill-hooks 插件
- **THEN** 在 `~/.claude/settings.json` 的 `enabledPlugins` 新增 `"auto-skill-hooks@custom-skills": true`


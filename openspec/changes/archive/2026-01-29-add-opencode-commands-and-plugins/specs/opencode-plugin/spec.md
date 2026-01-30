## ADDED Requirements

### Requirement: OpenCode ecc-hooks plugin 存在
系統 SHALL 在 `plugins/ecc-hooks-opencode/` 目錄下提供 OpenCode 格式的 plugin。

#### Scenario: Plugin 目錄結構
- **WHEN** 檢查 `plugins/ecc-hooks-opencode/`
- **THEN** 該目錄 SHALL 包含 `plugin.ts`（主 plugin 檔案）
- **THEN** 該目錄 SHALL 包含 `package.json`（依賴宣告）
- **THEN** 該目錄 SHALL 包含 `scripts/` 目錄（從 `plugins/ecc-hooks/scripts/` 複製或符號連結）

### Requirement: Hook 事件對映
plugin SHALL 將 Claude Code hooks.json 中的事件對映到 OpenCode plugin 事件。

#### Scenario: tool.execute.before 攔截
- **WHEN** OpenCode 觸發 `tool.execute.before` 事件且工具為 `bash`
- **THEN** plugin SHALL 檢查命令是否為 dev server 指令（npm run dev 等）
- **THEN** 若匹配 SHALL 拋出錯誤阻止執行

#### Scenario: tool.execute.after 觸發 code quality
- **WHEN** OpenCode 觸發 `tool.execute.after` 事件且工具為 `edit`
- **THEN** plugin SHALL 根據檔案副檔名呼叫對應的 code quality 腳本
- **THEN** `.ts/.tsx/.js/.jsx` 檔案 SHALL 觸發 format-js、check-typescript、warn-console-log
- **THEN** `.php` 檔案 SHALL 觸發 format-php、check-phpstan、warn-php-debug
- **THEN** `.py` 檔案 SHALL 觸發 format-python、check-mypy、warn-python-debug

#### Scenario: session 事件觸發 memory persistence
- **WHEN** OpenCode 觸發 `session.created` 事件
- **THEN** plugin SHALL 執行 `scripts/memory-persistence/session-start.py`
- **WHEN** OpenCode 觸發 `session.deleted` 事件
- **THEN** plugin SHALL 執行 `scripts/memory-persistence/session-end.py` 和 `scripts/memory-persistence/evaluate-session.py`

#### Scenario: compaction 事件觸發 pre-compact
- **WHEN** OpenCode 觸發 `session.compacted` 事件
- **THEN** plugin SHALL 執行 `scripts/memory-persistence/pre-compact.py`

#### Scenario: strategic compact 建議
- **WHEN** OpenCode 觸發 `tool.execute.before` 事件且工具為 `edit` 或 `write`
- **THEN** plugin SHALL 執行 `scripts/strategic-compact/suggest-compact.py`

### Requirement: Plugin 可被分發
`ai-dev clone` SHALL 將 OpenCode plugin 分發到 `~/.config/opencode/plugin/ecc-hooks/`。

#### Scenario: clone 分發 plugin
- **WHEN** 執行 `ai-dev clone`
- **THEN** `plugins/ecc-hooks-opencode/` 的內容 SHALL 被複製到 `~/.config/opencode/plugin/ecc-hooks/`
- **THEN** 包含 `plugin.ts`、`package.json` 和 `scripts/` 目錄

# opencode-plugin Delta Specification

## MODIFIED Requirements

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

#### Scenario: file.edited 逐檔自動化（新增）
- **WHEN** OpenCode 觸發 `file.edited` 事件
- **THEN** plugin SHALL 委派至 opencode-hooks 模組處理逐檔自動化

#### Scenario: session.idle 彙總作業（新增）
- **WHEN** OpenCode 觸發 `session.idle` 事件
- **THEN** plugin SHALL 委派至 opencode-hooks 模組處理 session 級別彙總

#### Scenario: file.watcher.updated 外部變更偵測（新增）
- **WHEN** OpenCode 觸發 `file.watcher.updated` 事件
- **THEN** plugin SHALL 委派至 opencode-hooks 模組處理外部變更偵測

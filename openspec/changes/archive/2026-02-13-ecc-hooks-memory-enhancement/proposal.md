## Why

ecc-hooks 的記憶持久化腳本（session-end.py、pre-compact.py、session-start.py）目前只產生空模板，沒有記錄任何實際內容。與 claude-mem 搭配使用時，ecc-hooks 應提供零成本的結構化事實記錄（修改檔案、git 變更、指令歷史），作為 claude-mem 語意記憶的互補。

## What Changes

- **session-end.py**：改為記錄結構化事實（git diff summary、修改的檔案清單、本次會話的 commit 記錄），取代空模板
- **session-start.py**：改為載入上一次會話的結構化事實摘要並注入上下文，取代僅輸出元資訊提示
- **pre-compact.py**：改為保存當前工作狀態快照（git status、進行中的檔案變更），取代僅追加時間戳
- **evaluate-session.py**：評估是否需要改動，目前依賴 `CLAUDE_TRANSCRIPT_PATH` 環境變數，可能保持現狀或移除

## Capabilities

### New Capabilities
- `session-snapshot`: 在 SessionEnd 時收集結構化事實（git diff、修改檔案、指令歷史）並寫入 .tmp 檔
- `session-context-load`: 在 SessionStart 時載入上一次會話的結構化事實並注入 Claude 上下文
- `pre-compact-snapshot`: 在 PreCompact 時保存當前工作狀態的 git 快照

### Modified Capabilities

（無既有 spec 需修改）

## Impact

- **修改檔案**：`plugins/ecc-hooks/scripts/memory-persistence/` 下的 4 個 Python 腳本
- **依賴**：僅使用 Python 標準庫 + git CLI（已在 utils.py 中有 subprocess 呼叫模式）
- **儲存**：`~/.claude/sessions/*.tmp` 檔案大小會從 ~300 bytes 增長到 ~2-5 KB
- **效能**：SessionEnd 會多跑幾個 git 指令（git diff --stat、git log），預計增加 < 1 秒
- **相容性**：session-manager.js / session-aliases.js 的 sessions 指令系統不受影響（讀取同一個 .tmp 目錄）

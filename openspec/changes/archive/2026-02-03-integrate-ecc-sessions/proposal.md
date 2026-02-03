## Why

everything-claude-code 上游新增了 `/sessions` 指令（commit `d85b1ae`），提供完整的 session 歷史管理功能（列表、查詢、別名、統計）。本專案的 ecc-hooks 已有 session 持久化機制（`session-start.py`、`session-end.py`），但缺乏互動式查詢與管理能力。整合此功能可讓使用者回顧、搜尋和標記歷史 session，補齊 session 生命週期的最後一環。

## What Changes

- 新增 `/sessions` 指令至 `commands/claude/`，支援 list、load、alias、info 等子命令
- 新增 `scripts/lib/session-manager.js` 至 ecc-hooks，提供 session CRUD 操作
- 新增 `scripts/lib/session-aliases.js` 至 ecc-hooks，提供別名管理與原子寫入
- 修改 `scripts/lib/utils.js`（若存在）或在現有 `utils.py` 新增 `getAliasesPath` 等輔助函式
- 修改 `session-start` hook 邏輯，啟動時顯示可用別名
- 語言策略：混合（session lib 保留 Node.js，與現有 code-quality JS 腳本一致；command 嵌入 Node 腳本）

## Capabilities

### New Capabilities
- `session-management`: Session 歷史的列表、載入、查詢與統計功能（`/sessions list`、`/sessions load`、`/sessions info`）
- `session-aliases`: Session 別名的建立、刪除、列表與解析功能（`/sessions alias`、`/sessions aliases`）

### Modified Capabilities
- `hook-system`: session-start hook 新增別名顯示邏輯，啟動時列出最近使用的別名

## Impact

- **新增檔案**:
  - `commands/claude/sessions.md` — 指令定義（適配本專案路徑）
  - `plugins/ecc-hooks/scripts/lib/session-manager.js` — Session CRUD
  - `plugins/ecc-hooks/scripts/lib/session-aliases.js` — 別名管理
- **修改檔案**:
  - `plugins/ecc-hooks/scripts/memory-persistence/session-start.py` — 新增別名顯示
  - `plugins/ecc-hooks/scripts/utils.py` — 新增 aliases 路徑輔助函式
- **依賴**:
  - Node.js（已有，code-quality 腳本已使用）
  - 無新增外部套件依賴（純 Node.js 內建模組 `fs`、`path`）
- **資料**:
  - 讀取 `~/.claude/sessions/` 目錄（現有）
  - 新增 `~/.claude/session-aliases.json` 儲存別名
- **相容性**:
  - 支援新舊兩種 session 檔名格式
  - 別名檔案使用原子寫入，支援跨平台
  - 不影響現有 session-end.py 的寫入邏輯

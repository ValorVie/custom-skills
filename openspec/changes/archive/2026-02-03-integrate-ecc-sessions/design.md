## Context

本專案的 ecc-hooks plugin（`plugins/ecc-hooks/`）已有 session 持久化機制：
- `session-start.py` — 啟動時載入前次 session context
- `session-end.py` — 結束時儲存 session 狀態
- `utils.py` — Python 跨平台工具函式庫（含 `get_sessions_dir()` 等）

上游 everything-claude-code 新增了 `/sessions` 指令（commit `d85b1ae`），提供 session 歷史的互動式管理，使用 Node.js 實作：
- `scripts/lib/session-manager.js`（396 行）— Session CRUD
- `scripts/lib/session-aliases.js`（433 行）— 別名管理
- `scripts/lib/utils.js` — 基礎工具函式
- `commands/sessions.md` — 指令定義（嵌入 Node.js 腳本）

本專案的 ecc-hooks 已是混合語言架構：Python（memory-persistence）+ Node.js（code-quality）。

## Goals / Non-Goals

**Goals:**
- 整合 `/sessions` 指令，讓使用者可以列表、查詢、載入歷史 session
- 整合 session 別名系統，讓使用者可以為 session 建立易記名稱
- 修改 session-start hook，啟動時顯示可用別名
- 保持與上游程式碼的相似度，降低日後同步維護成本

**Non-Goals:**
- 不重寫 session-manager/session-aliases 為 Python（維護成本過高且無明顯收益）
- 不修改現有 `session-end.py` 的寫入邏輯
- 不同步 OpenCode 版本（ecc-hooks-opencode 暫不處理，因 OpenCode 使用 TypeScript 架構不同）
- 不新增 `ai-dev` CLI 子命令（session 管理透過 Claude Code command 操作）

## Decisions

### 決策 1：語言選擇 — 混合架構（Node.js lib + Python hook 修改）

**選擇**：session-manager 和 session-aliases 保留 Node.js，session-start hook 修改在 Python 中呼叫 Node。

**替代方案**：
- 全部移植為 Python：需重寫 829 行 JS，commands 嵌入腳本也要改，維護成本高且與上游分歧
- 全部改用 Node.js：需重寫 session-start.py，破壞現有 Python hook 生態

**理由**：
1. 本專案 code-quality hooks 已使用 Node.js，混合架構是既有慣例
2. 保留上游程式碼減少未來同步成本
3. `sessions.md` command 的嵌入腳本本身就是 Node.js，天然搭配

### 決策 2：utils.js 處理 — 引入上游 utils.js 作為獨立模組

**選擇**：將上游 `scripts/lib/utils.js` 引入 `plugins/ecc-hooks/scripts/lib/utils.js`，作為 JS lib 的共用基礎。

**理由**：
- `session-manager.js` 和 `session-aliases.js` 都 `require('./utils')`，引入 utils.js 讓上游程式碼可直接使用，不需修改 require 路徑
- utils.js 提供的函式（`getSessionsDir`、`getClaudeDir`、`readFile` 等）與本專案 `utils.py` 功能對應但語言不同，不衝突

### 決策 3：Command 放置位置 — `commands/claude/sessions.md`

**選擇**：放在 `commands/claude/` 目錄下。

**理由**：符合本專案的 commands 目錄結構慣例，所有 Claude Code 指令都在此目錄。

### 決策 4：Command 腳本路徑適配

**選擇**：修改 command 中的 `require` 路徑，從 `./scripts/lib/` 改為指向 ecc-hooks plugin 目錄。

**理由**：上游的 `sessions.md` 使用相對路徑 `require('./scripts/lib/session-manager')`，這在上游的 ecc 目錄結構下有效。本專案的 lib 位於 `plugins/ecc-hooks/scripts/lib/`，需要使用 `CLAUDE_PLUGIN_ROOT` 環境變數或絕對路徑。

**具體作法**：command 嵌入腳本中使用：
```js
const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT || path.join(os.homedir(), '.claude', 'plugins', 'ecc-hooks');
const sm = require(path.join(pluginRoot, 'scripts', 'lib', 'session-manager'));
const aa = require(path.join(pluginRoot, 'scripts', 'lib', 'session-aliases'));
```

### 決策 5：session-start.py 修改方式 — 透過 subprocess 呼叫 Node

**選擇**：在 `session-start.py` 中使用 `subprocess` 呼叫一段小型 Node 腳本來讀取別名列表。

**替代方案**：
- 直接在 Python 中讀取 `session-aliases.json`：可行但與 JS 別名邏輯可能分歧
- 新增獨立的 session-start Node hook：需修改 hooks.json，增加複雜度

**理由**：
1. 保持別名邏輯的單一來源（session-aliases.js）
2. Python subprocess 呼叫 Node 是輕量操作
3. 若 Node 不可用則靜默跳過，不影響現有功能

## Risks / Trade-offs

- **Node.js 依賴**：session 管理功能需要 Node.js 運行時。但本專案已要求 Node.js >= 20.19.0，且 code-quality hooks 已依賴 Node.js，風險低。→ 在 command 中加入 Node.js 可用性檢查。

- **上游 utils.js 與本地 utils.py 功能重疊**：兩者提供類似功能但語言不同。→ 明確標註 utils.js 僅供 JS lib 使用，utils.py 僅供 Python hooks 使用，各自獨立。

- **session-aliases.json 競態寫入**：上游已實作原子寫入（temp + rename）和備份機制，風險已緩解。

- **CLAUDE_PLUGIN_ROOT 環境變數可用性**：若在非 Claude Code plugin 環境中執行，`CLAUDE_PLUGIN_ROOT` 可能不存在。→ 提供 fallback 路徑。

## 1. JS Lib 基礎建設

- [x] 1.1 建立 `plugins/ecc-hooks/scripts/lib/` 目錄
- [x] 1.2 從上游複製 `utils.js` 至 `plugins/ecc-hooks/scripts/lib/utils.js`，標註來源與同步日期
- [x] 1.3 從上游複製 `session-manager.js` 至 `plugins/ecc-hooks/scripts/lib/session-manager.js`，標註來源
- [x] 1.4 從上游複製 `session-aliases.js` 至 `plugins/ecc-hooks/scripts/lib/session-aliases.js`，標註來源
- [x] 1.5 驗證 `require` 路徑正確：在 `plugins/ecc-hooks/scripts/lib/` 下執行 `node -e "require('./session-manager')"` 確認載入成功

## 2. /sessions Command

- [x] 2.1 從上游複製 `commands/sessions.md` 至 `commands/claude/sessions.md`
- [x] 2.2 修改嵌入腳本的 `require` 路徑：使用 `CLAUDE_PLUGIN_ROOT` 環境變數搭配 fallback（`~/.claude/plugins/ecc-hooks`）
- [x] 2.3 驗證 `/sessions list` 指令可正常列出 sessions
- [x] 2.4 驗證 `/sessions load`、`/sessions info` 可正常載入 session
- [x] 2.5 驗證 `/sessions alias` 和 `/sessions aliases` 可正常操作別名

## 3. Session Start Hook 修改

- [x] 3.1 修改 `plugins/ecc-hooks/scripts/memory-persistence/session-start.py`，新增別名顯示邏輯
- [x] 3.2 實作 subprocess 呼叫 Node.js 讀取別名列表（最多 5 個）
- [x] 3.3 加入 Node.js 不可用時的靜默 fallback（try/except 捕捉 FileNotFoundError）
- [x] 3.4 在 `plugins/ecc-hooks/scripts/utils.py` 新增 `get_aliases_path()` 函式

## 4. 驗證與文件

- [x] 4.1 端對端驗證：建立測試 session → 列表 → 建立別名 → 用別名載入 → 刪除別名
- [x] 4.2 驗證 session-start hook 啟動時顯示別名（若有）
- [x] 4.3 更新 `plugins/ecc-hooks/README.md`，新增 session 管理相關說明
- [x] 4.4 更新 CHANGELOG.md 記錄此變更

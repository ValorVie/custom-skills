## Context

`ai-dev sync` 透過 Git repo 在多台設備間同步 `~/.claude` 和 `~/.claude-mem` 目錄。目前 plugin 系統已透過 manifest 機制避免同步絕對路徑，但 `claude-mem/settings.json` 的 `CLAUDE_MEM_DATA_DIR` 仍包含硬編碼的 `$HOME` 絕對路徑。

現有同步流程：
- Push：`local → repo → git push`
- Pull：`git pull → repo → local`

路徑替換需插入這兩個流程中。

## Goals / Non-Goals

**Goals:**
- Push 時將 repo 中 `settings.json` 的 `$HOME` 開頭路徑替換為 `{{HOME}}` 佔位符
- Pull 時將本機 `settings.json` 的 `{{HOME}}` 展開為當前系統的 `$HOME`
- 設計通用機制，未來可擴展更多路徑變數

**Non-Goals:**
- 不處理歷史紀錄中的路徑（`usage-data/session-meta/` 等，保留來源系統資訊）
- 不處理 markdown 或其他非 JSON 檔案中的路徑
- 不處理 `{{HOME}}` 以外的佔位符（如 `{{NVM}}`），留待未來需要時擴展

## Decisions

### Decision 1: 佔位符格式 — `{{HOME}}`

使用 `{{HOME}}` 作為佔位符。

**理由：**
- 雙花括號不會與 JSON value 中的一般字串衝突
- 可讀性高，一看就懂含義
- 與常見模板語法（Handlebars、Jinja2）一致

**替代方案：**
- `$HOME`：可能與 shell 環境變數混淆，JSON 中需轉義
- `~`：JSON value 中 `~` 不會被自動展開，語義不明確

### Decision 2: 替換範圍 — 各同步目錄的 `settings.json`

只處理每個同步目錄下的 `settings.json` 檔案。

**理由：**
- 目前已知的硬編碼路徑問題只出現在 `settings.json`
- 範圍可控，不會意外修改其他檔案
- 未來若需擴展，可將檔案名清單改為可設定

**替代方案：**
- 所有 `.json` 檔案：風險太大，可能修改 session-meta 等歷史資料

### Decision 3: 替換邏輯 — JSON value 層級掃描

遞迴掃描 JSON 的所有 string value，將以 `str(Path.home())` 開頭的值做前綴替換。

**理由：**
- 不需維護欄位白名單
- 自動覆蓋未來新增的路徑欄位
- 只影響 string value，不會修改 key 或結構

### Decision 4: 插入點

- **Push**：`_sync_local_to_repo()` 之後、`git_add_commit()` 之前 — 修改 **repo 中的檔案**
- **Pull**：`_sync_repo_to_local()` 之後 — 修改 **本機檔案**

這確保：
- Repo 中永遠是 `{{HOME}}` 格式
- 本機永遠是展開後的真實路徑

### Decision 5: 目標檔案定位

透過 sync config 的 `directories` 列表，搭配固定的檔案名 `settings.json`：
- Push 時掃描：`{repo_dir}/{repo_subdir}/settings.json`
- Pull 時掃描：`{local_path}/settings.json`（從 config 的 `path` 取得）

## Risks / Trade-offs

- **[Risk] 佔位符出現在非路徑值中** → 極低風險。`{{HOME}}` 不太可能出現在正常設定值中。如果真的出現，expand 會錯誤替換。可透過限制只替換「看起來像路徑的值」來進一步降低風險。
- **[Risk] 首次 push 後 repo diff 會有一次性變更** → 預期行為。將所有路徑轉為 `{{HOME}}` 格式會產生一次 diff，之後跨設備同步就不會有路徑差異。
- **[Trade-off] 只支援 `HOME` 變數** → 簡單優先。未來需要時可擴展 `PATH_VARIABLES` dict。

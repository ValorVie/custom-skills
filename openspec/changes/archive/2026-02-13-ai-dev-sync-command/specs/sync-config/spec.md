## ADDED Requirements

### Requirement: sync.yaml 設定檔結構

系統 SHALL 使用 `~/.config/ai-dev/sync.yaml` 儲存同步設定，格式為 YAML。

設定檔結構：
- `version`: 設定檔版本（字串，目前為 `"1"`）
- `remote`: Git remote URL
- `last_sync`: 最後同步的 ISO 8601 時間戳
- `directories`: 同步目錄陣列，每個項目包含：
  - `path`: 目錄的絕對路徑或 `~` 開頭路徑
  - `repo_subdir`: 在 sync-repo 中對應的子目錄名稱
  - `ignore_profile`: 內建 ignore profile 名稱（`claude`、`claude-mem`、`custom`）
  - `custom_ignore`: 自訂排除模式列表（選填，僅 `ignore_profile: custom` 時使用）

#### Scenario: 預設設定檔產生

- **WHEN** `ai-dev sync init` 首次執行
- **THEN** 系統產生 `sync.yaml`，包含 `~/.claude`（profile: claude）和 `~/.claude-mem`（profile: claude-mem）兩個預設目錄

#### Scenario: 設定檔讀取

- **WHEN** 任何 sync 子指令需要讀取設定
- **THEN** 系統從 `~/.config/ai-dev/sync.yaml` 載入設定，路徑中的 `~` 展開為使用者家目錄

#### Scenario: 設定檔不存在

- **WHEN** sync 子指令嘗試讀取設定但 `sync.yaml` 不存在
- **THEN** 系統拋出明確錯誤，提示使用者先執行 `ai-dev sync init`

---

### Requirement: 內建 ignore profiles

系統 SHALL 內建以下 ignore profiles，定義各目錄類型的排除規則：

**claude profile**：
`debug/`、`cache/`、`paste-cache/`、`downloads/`、`stats-cache.json`、`.DS_Store`、`Thumbs.db`、`desktop.ini`、`shell-snapshots/`、`session-env/`、`ide/`、`statsig/`、`telemetry/`、`plugins/cache/`、`plugins/marketplaces/`、`plugins/repos/`、`plugins/install-counts-cache.json`

**claude-mem profile**：
`logs/`、`worker.pid`、`*.db-wal`、`*.db-shm`

**custom profile**：
使用者在 `sync.yaml` 中 `custom_ignore` 欄位定義的排除模式。

#### Scenario: 取得 claude profile

- **WHEN** 系統需要 `claude` ignore profile 的排除清單
- **THEN** 回傳包含 debug/、cache/ 等 16 個排除模式的列表

#### Scenario: 取得 custom profile

- **WHEN** 系統需要 `custom` ignore profile 且目錄設定有 `custom_ignore: ["cache/", "*.log"]`
- **THEN** 回傳 `["cache/", "*.log"]`

#### Scenario: 未知 profile

- **WHEN** 系統遇到不認識的 ignore profile 名稱
- **THEN** 回傳空列表並輸出警告訊息

---

### Requirement: .gitignore 產生

系統 SHALL 根據所有同步目錄的 ignore profiles 產生合併的 `.gitignore` 檔案。

- 每個目錄的排除規則以 repo 子目錄名稱為前綴（如 `claude/debug/`）
- 加入全域排除項目：`.DS_Store`、`Thumbs.db`、`desktop.ini`
- 每次 `add`/`remove` 操作後重新產生

#### Scenario: 產生含兩個目錄的 .gitignore

- **WHEN** 設定中有 `~/.claude`（subdir: claude, profile: claude）和 `~/.claude-mem`（subdir: claude-mem, profile: claude-mem）
- **THEN** 產生的 `.gitignore` 包含 `claude/debug/`、`claude/cache/` 等前綴化規則，以及 `claude-mem/logs/`、`claude-mem/worker.pid` 等規則

---

### Requirement: .gitattributes 產生

系統 SHALL 在 sync-repo 中產生 `.gitattributes`，定義合併策略和換行規則。

- `*.jsonl` 使用 `merge=union`（JSONL 逐行合併）
- `*.md` 使用 `text eol=lf`（統一換行為 LF）

#### Scenario: 產生 .gitattributes

- **WHEN** `ai-dev sync init` 建立 sync-repo
- **THEN** repo 根目錄包含 `.gitattributes`，內含 JSONL union merge 和 MD LF 規則

---

### Requirement: sync-repo 路徑管理

系統 SHALL 使用 `~/.config/ai-dev/sync-repo/` 作為本機 sync repo 的儲存位置。

- 目錄路徑透過 `paths.py` 的 `get_sync_repo_dir()` 函數取得
- 設定檔路徑透過 `paths.py` 的 `get_sync_config_path()` 函數取得

#### Scenario: 取得 sync-repo 路徑

- **WHEN** 系統呼叫 `get_sync_repo_dir()`
- **THEN** 回傳 `~/.config/ai-dev/sync-repo/` 的展開路徑

#### Scenario: 取得設定檔路徑

- **WHEN** 系統呼叫 `get_sync_config_path()`
- **THEN** 回傳 `~/.config/ai-dev/sync.yaml` 的展開路徑

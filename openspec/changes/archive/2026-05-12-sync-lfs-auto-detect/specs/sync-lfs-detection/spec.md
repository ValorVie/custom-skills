## ADDED Requirements

### Requirement: 自動偵測大檔案並產生 LFS pattern

系統 SHALL 掃描 sync repo 中所有檔案，偵測超過 50 MB 閾值的檔案，以副檔名為單位產生 Git LFS track pattern（如 `*.sqlite3`）。掃描 SHALL 排除 `.gitignore` 已忽略的目錄（如 `.git/`）以及以 `.` 開頭的隱藏檔案。

#### Scenario: 偵測到超過 50 MB 的 sqlite3 檔案
- **WHEN** sync repo 中存在 60 MB 的 `claude-mem/vector-db/chroma.sqlite3`
- **THEN** `detect_lfs_patterns()` SHALL 回傳包含 `*.sqlite3` 的 pattern 清單

#### Scenario: 無大檔案時回傳空清單
- **WHEN** sync repo 中所有檔案皆小於 50 MB
- **THEN** `detect_lfs_patterns()` SHALL 回傳空清單

#### Scenario: 多種大檔案類型
- **WHEN** sync repo 中存在 55 MB 的 `data.sqlite3` 和 80 MB 的 `backup.db`
- **THEN** `detect_lfs_patterns()` SHALL 回傳 `["*.db", "*.sqlite3"]`（排序後）

### Requirement: JSONL 排除機制

系統 SHALL 將 `*.jsonl` 排除於 LFS 偵測之外，即使檔案超過閾值。此排除確保 `.gitattributes` 中的 `*.jsonl merge=union` 合併策略不被 LFS binary 處理覆蓋。

#### Scenario: 大型 JSONL 檔案不觸發 LFS
- **WHEN** sync repo 中存在 200 MB 的 `history.jsonl`
- **THEN** `detect_lfs_patterns()` SHALL 不包含 `*.jsonl`

### Requirement: 檢測 git-lfs 安裝狀態

系統 SHALL 提供 `check_lfs_available()` 函式，檢查系統上是否已安裝 `git-lfs` 命令。

#### Scenario: git-lfs 已安裝
- **WHEN** 系統 PATH 中存在 `git-lfs` 執行檔
- **THEN** `check_lfs_available()` SHALL 回傳 `True`

#### Scenario: git-lfs 未安裝
- **WHEN** 系統 PATH 中不存在 `git-lfs` 執行檔
- **THEN** `check_lfs_available()` SHALL 回傳 `False`

### Requirement: LFS 初始化

系統 SHALL 提供 `git_lfs_setup()` 函式，在指定 repo 中執行 `git lfs install --local`，僅影響該 repo 的 git config。

#### Scenario: 成功初始化 LFS
- **WHEN** 在有效 git repo 中呼叫 `git_lfs_setup()`
- **THEN** 系統 SHALL 執行 `git lfs install --local` 並回傳 `True`

#### Scenario: git-lfs 未安裝時初始化失敗
- **WHEN** 系統未安裝 git-lfs 且呼叫 `git_lfs_setup()`
- **THEN** 系統 SHALL 回傳 `False`

### Requirement: 既有大檔案遷移

系統 SHALL 提供 `git_lfs_migrate_existing()` 函式，將已追蹤的大檔案轉換為 LFS 物件。此操作會改寫 git history。

#### Scenario: 成功 migrate 既有檔案
- **WHEN** repo 中已追蹤 `*.sqlite3` 檔案且呼叫 `git_lfs_migrate_existing(repo_dir, ["*.sqlite3"])`
- **THEN** 系統 SHALL 執行 `git lfs migrate import --include="*.sqlite3" --everything` 並回傳 `True`

#### Scenario: 無需 migrate 的新 repo
- **WHEN** repo 為新建（無歷史 commit 追蹤大檔案）
- **THEN** `git_lfs_migrate_existing()` SHALL 正常執行不報錯

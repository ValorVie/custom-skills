## Why

`ai-dev sync push` 時 GitHub 警告 `chroma.sqlite3` 為 60.85 MB，超過建議上限 50 MB。GitHub 硬限制為 100 MB，超過即拒絕 push。SQLite 資料庫只會持續增長，且 binary 無法 delta 壓縮，每次 commit 都是完整副本。需要整合 Git LFS 自動偵測大檔案，避免 push 失敗與 repo 膨脹。

## What Changes

- 新增大檔案自動偵測機制：掃描 sync repo 中超過 50 MB 的檔案，以副檔名為單位自動加入 Git LFS track
- 排除 `*.jsonl`：需保留現有 `merge=union` 合併策略，不走 LFS
- 擴充 `.gitattributes` 生成邏輯：動態加入偵測到的 LFS track pattern
- 新增 LFS 輔助函式：`check_lfs_available()`、`git_lfs_setup()`、`detect_lfs_patterns()`、`git_lfs_migrate_existing()`
- 整合到 `init` 與 `push` 流程：檔案複製到 repo 後自動偵測並設定 LFS
- Graceful degradation：未安裝 git-lfs 時顯示警告但不阻擋操作
- 更新 AI-DEV-SYNC-GUIDE.md 文件

## Capabilities

### New Capabilities

- `sync-lfs-detection`: 自動偵測 sync repo 中的大檔案並整合 Git LFS 追蹤，包含閾值掃描、pattern 生成、LFS 初始化與既有檔案遷移

### Modified Capabilities

- `sync-engine`: gitattributes 生成邏輯擴充，支援動態 LFS pattern 參數
- `sync-command`: init 與 push 流程加入 LFS 偵測與設定步驟

## Impact

- **程式碼**：`script/utils/sync_config.py`（新增 LFS 函式 + 修改 `generate_gitattributes`/`write_gitattributes`）、`script/commands/sync.py`（修改 `init`/`push`）
- **依賴**：git-lfs（選用，未安裝時 graceful degradation）
- **文件**：`docs/dev-guide/workflow/AI-DEV-SYNC-GUIDE.md`（新增 LFS 章節、更新前置條件）
- **測試**：現有 17 個 sync 測試需保持通過，新增 LFS 偵測相關測試

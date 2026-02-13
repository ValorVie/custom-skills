## 1. LFS 輔助函式 (`script/utils/sync_config.py`)

- [ ] 1.1 新增 `LFS_THRESHOLD_MB` 和 `LFS_EXCLUDE_EXTENSIONS` 常數
- [ ] 1.2 新增 `check_lfs_available()` 函式（使用 `shutil.which`）
- [ ] 1.3 新增 `git_lfs_setup(repo_dir)` 函式（`git lfs install --local`）
- [ ] 1.4 新增 `detect_lfs_patterns(repo_dir, threshold_mb)` 函式（掃描大檔案、排除 JSONL、回傳 sorted pattern）
- [ ] 1.5 新增 `git_lfs_migrate_existing(repo_dir, patterns)` 函式（`git lfs migrate import`）

## 2. gitattributes 擴充 (`script/utils/sync_config.py`)

- [ ] 2.1 修改 `generate_gitattributes()` 簽名，加入 `lfs_patterns: list[str] | None = None` 參數
- [ ] 2.2 在 `generate_gitattributes()` 中，當 `lfs_patterns` 非空時附加 LFS track 規則
- [ ] 2.3 修改 `write_gitattributes()` 簽名，加入 `lfs_patterns` 參數並傳遞給 `generate_gitattributes()`

## 3. init 流程整合 (`script/commands/sync.py`)

- [ ] 3.1 在 init 中 `_sync_local_to_repo()` 後加入 LFS 偵測邏輯
- [ ] 3.2 git-lfs 可用時：呼叫 `git_lfs_setup()`、`detect_lfs_patterns()`、顯示追蹤訊息
- [ ] 3.3 既有 repo 有大檔案時：呼叫 `git_lfs_migrate_existing()`
- [ ] 3.4 git-lfs 不可用但有大檔案時：顯示黃色警告
- [ ] 3.5 將 `lfs_patterns` 傳入 `write_gitattributes()`

## 4. push 流程整合 (`script/commands/sync.py`)

- [ ] 4.1 在 push 中 `_sync_local_to_repo()` 後加入 LFS 偵測
- [ ] 4.2 將 `lfs_patterns` 傳入 `write_gitattributes()`

## 5. 文件更新 (`docs/dev-guide/workflow/AI-DEV-SYNC-GUIDE.md`)

- [ ] 5.1 前置條件加入 git-lfs 建議安裝說明
- [ ] 5.2 新增「Git LFS 自動追蹤」章節（偵測機制、JSONL 排除、安裝方式）
- [ ] 5.3 改寫「大型檔案與倉庫膨脹」章節

## 6. 測試驗證

- [ ] 6.1 執行 `uv run pytest tests/ -k sync` 確認現有 17 個測試通過
- [ ] 6.2 本機測試 `ai-dev sync push` 觀察 LFS 偵測行為

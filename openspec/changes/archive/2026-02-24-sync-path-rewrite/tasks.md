## 1. 核心函數實作

- [x] 1.1 在 `sync_config.py` 新增 `PATH_VARIABLES` 常數和 `_replace_paths_in_json()` 遞迴替換工具函數
- [x] 1.2 實作 `normalize_paths_in_file(file_path)` — 將 `$HOME` 路徑替換為 `{{HOME}}`
- [x] 1.3 實作 `expand_paths_in_file(file_path)` — 將 `{{HOME}}` 展開為當前系統 `$HOME`

## 2. 批次處理與流程整合

- [x] 2.1 實作 `normalize_paths_in_repo(config)` — 批次處理 repo 中各目錄的 `settings.json`
- [x] 2.2 實作 `expand_paths_in_local(config)` — 批次處理本機各目錄的 `settings.json`
- [x] 2.3 在 `sync.py` 的 `push()` 中呼叫 `normalize_paths_in_repo()`（插入於 `_sync_local_to_repo()` 之後、`git_add_commit()` 之前）
- [x] 2.4 在 `sync.py` 的 `pull()` 中呼叫 `expand_paths_in_local()`（插入於 `_sync_repo_to_local()` 之後）

## 3. 測試

- [x] 3.1 新增 `normalize_paths_in_file` 單元測試（標準化、無變更、巢狀結構、檔案不存在）
- [x] 3.2 新增 `expand_paths_in_file` 單元測試（展開、無變更、檔案不存在）
- [x] 3.3 新增批次函數測試（多目錄、目錄無 settings.json）
- [x] 3.4 執行完整測試套件確認無回歸

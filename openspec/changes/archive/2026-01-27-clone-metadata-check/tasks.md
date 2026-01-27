## 1. 建立 Git Helper 模組

- [x] 1.1 建立 `script/utils/git_helpers.py` 檔案
- [x] 1.2 實作 `is_git_repo(path: Path) -> bool` 檢查是否為 git 目錄
- [x] 1.3 實作 `get_raw_diff(repo_path: Path) -> list[dict]` 解析 `git diff --raw` 輸出

## 2. 實作異動檢測邏輯

- [x] 2.1 實作 `detect_mode_changes(raw_diff: list[dict]) -> list[str]` 識別權限變更檔案
- [x] 2.2 實作 `is_only_line_ending_diff(file_path: str, repo_path: Path) -> bool` 檢測換行符差異
- [x] 2.3 實作 `detect_metadata_changes(repo_path: Path) -> MetadataChanges` 整合檢測邏輯
- [x] 2.4 定義 `MetadataChanges` dataclass 儲存檢測結果

## 3. 實作處理選項

- [x] 3.1 實作 `revert_files(files: list[str], repo_path: Path) -> bool` 還原檔案
- [x] 3.2 實作 `set_filemode_config(repo_path: Path, value: bool) -> bool` 設定 git config
- [x] 3.3 實作 `show_file_list(changes: MetadataChanges, console: Console)` 顯示詳細清單

## 4. 實作互動式介面

- [x] 4.1 實作 `handle_metadata_changes(changes: MetadataChanges, console: Console)` 互動式選單
- [x] 4.2 使用 Rich Prompt 顯示選項
- [x] 4.3 根據使用者選擇呼叫對應處理函數

## 5. 整合到 Clone 流程

- [x] 5.1 在 `script/commands/clone.py` 引入 git_helpers
- [x] 5.2 在 clone 完成後（`is_dev_dir` 為 True 時）呼叫 `detect_metadata_changes`
- [x] 5.3 若有非內容異動，呼叫 `handle_metadata_changes`

## 6. 驗證

- [x] 6.1 在開發目錄測試 `ai-dev clone`，確認檢測功能正常
- [x] 6.2 測試各處理選項（還原、忽略權限、保留、顯示清單）
- [x] 6.3 測試無異動時不顯示提示
- [x] 6.4 測試非 git 目錄不觸發檢測

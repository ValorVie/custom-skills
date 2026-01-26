## 1. 建立 Manifest 模組

- [x] 1.1 建立 `script/utils/manifest.py` 模組
- [x] 1.2 實作 `compute_file_hash(path: Path) -> str` - 計算單檔案 SHA-256 hash
- [x] 1.3 實作 `compute_dir_hash(path: Path) -> str` - 遞迴計算目錄組合 hash
- [x] 1.4 實作 `FileRecord` dataclass（name, hash）
- [x] 1.5 實作 `ManifestTracker` dataclass 及其方法
  - `record_skill(name, source_path)`
  - `record_command(name, source_path)`
  - `record_agent(name, source_path)`
  - `record_workflow(name, source_path)`
  - `to_manifest(version) -> dict`

## 2. Manifest 讀寫功能

- [x] 2.1 實作 `get_manifest_dir() -> Path` - 返回 `~/.config/ai-dev/manifests/`
- [x] 2.2 實作 `get_manifest_path(target: str) -> Path` - 返回指定平台的 manifest 路徑
- [x] 2.3 實作 `read_manifest(target: str) -> dict | None` - 讀取 manifest，損壞時返回 None 並輸出警告
- [x] 2.4 實作 `write_manifest(target: str, manifest: dict) -> None` - 寫入 manifest（自動建立目錄）

## 3. 衝突檢測功能

- [x] 3.1 定義 `ConflictInfo` dataclass（name, resource_type, old_hash, current_hash）
- [x] 3.2 實作 `detect_conflicts(target, old_manifest, new_tracker) -> list[ConflictInfo]`
  - 比對目標檔案 hash 與 manifest 記錄
  - 返回衝突清單
- [x] 3.3 實作 `display_conflicts(conflicts: list[ConflictInfo])` - 格式化顯示衝突清單
- [x] 3.4 實作 `prompt_conflict_action()` - 互動式詢問用戶處理方式

## 4. 備份功能

- [x] 4.1 實作 `get_backup_dir(target: str) -> Path` - 返回備份目錄路徑
- [x] 4.2 實作 `backup_file(target, resource_type, name) -> Path` - 備份單個檔案/目錄，返回備份路徑
- [x] 4.3 備份檔名格式：`<name>.<timestamp>`

## 5. 孤兒檔案處理

- [x] 5.1 實作 `find_orphans(old_manifest, new_manifest) -> dict[str, list[str]]`
  - 返回按資源類型分組的孤兒檔案清單
- [x] 5.2 實作 `cleanup_orphans(target, orphans) -> None`
  - 刪除孤兒檔案/目錄
  - 輸出清理日誌

## 6. 整合到分發流程

- [x] 6.1 修改 `clone.py` 新增命令列參數
  - `--force` - 強制覆蓋衝突
  - `--skip-conflicts` - 跳過衝突檔案
  - `--backup` - 備份後覆蓋
- [x] 6.2 修改 `copy_custom_skills_to_targets()` 簽名，新增衝突處理參數
- [x] 6.3 在 `copy_custom_skills_to_targets()` 中整合 manifest 流程
  - 讀取舊 manifest
  - 建立 ManifestTracker
  - 檢測衝突並處理
  - 執行複製並記錄
  - 清理孤兒
  - 寫入新 manifest
- [x] 6.4 修改 `_copy_with_log()` 接受並呼叫 tracker 記錄

## 7. 版本號讀取

- [x] 7.1 實作 `get_project_version() -> str` - 從 pyproject.toml 讀取版本號

## 8. 測試與驗證

- [x] 8.1 手動測試：首次分發（無舊 manifest）
- [x] 8.2 手動測試：正常分發（無衝突）
- [x] 8.3 手動測試：衝突檢測與處理（--force, --skip-conflicts, --backup）
- [x] 8.4 手動測試：孤兒清理（重命名檔案後分發）
- [x] 8.5 手動測試：用戶自訂檔案保護
- [x] 8.6 驗證 manifest 檔案格式正確

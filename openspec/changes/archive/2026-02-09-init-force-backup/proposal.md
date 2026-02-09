## Why

`ai-dev project init --force` 在正向初始化時，會用 `_safe_rmtree` 刪除目標專案已存在的目錄（如 `.github/`），再用 `shutil.copytree` 從模板重建。使用者在 `.github/workflows/` 中的自定義 workflow（如 `deploy.yml`、`lint.yml`）或修改過的模板檔案會被直接覆蓋而遺失，且無法復原。

## What Changes

- 在正向 init `--force` 流程中，覆蓋目錄前先比對差異，備份有差異的檔案
- 備份位置為目標專案根目錄的 `_backup_after_init_force/<YYYYMMDD_HHMMSS>/`
- 只備份「目標有但模板沒有」的檔案，以及「兩邊都有但內容不同」的檔案（保留目標版本）
- 在 `project-template/.gitignore` 中加入 `_backup_after_init_force/`
- 覆蓋完成後顯示備份摘要（備份了哪些檔案、存放路徑）

## Capabilities

### New Capabilities
- `init-force-backup`: init --force 時的差異檔案備份機制

### Modified Capabilities
- `project-commands`: init --force 流程新增備份步驟

## Impact

- `script/commands/project.py`：init 函式的 force 分支需加入備份邏輯
- `project-template/.gitignore`：新增排除項目
- 不影響反向同步（場景 B）邏輯
- 不影響非 force 的正常 init 流程

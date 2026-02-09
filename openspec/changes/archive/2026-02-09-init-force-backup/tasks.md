## 1. 核心備份函式

- [x] 1.1 在 `script/commands/project.py` 新增 `_collect_diff_files(src_dir, dst_dir)` 函式，遞迴比對兩個目錄，回傳需要備份的相對路徑清單（使用 `filecmp.cmp(shallow=False)`）
- [x] 1.2 在 `script/commands/project.py` 新增 `_backup_diff_files(target_dir, diff_files, item_name, backup_dir)` 函式，將差異檔案複製到備份目錄並保留相對路徑結構

## 2. Init --force 流程整合

- [x] 2.1 在 init 函式中（force 分支），生成共用 timestamp 並建構 `backup_base_dir` 路徑
- [x] 2.2 在目錄覆蓋前（`_safe_rmtree` 之前），呼叫 `_collect_diff_files` 比對差異並呼叫 `_backup_diff_files` 備份
- [x] 2.3 在單一檔案覆蓋前（`shutil.copy2` 之前），比對檔案內容，若不同則備份目標版本
- [x] 2.4 在 init 完成後顯示備份摘要（備份目錄路徑、檔案清單、檔案數量），無備份時不顯示

## 3. Gitignore 更新

- [x] 3.1 在 `project-template/.gitignore` 中加入 `_backup_after_init_force/` 排除規則

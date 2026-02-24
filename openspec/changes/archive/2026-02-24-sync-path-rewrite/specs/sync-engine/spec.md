## MODIFIED Requirements

### Requirement: 目錄同步函數

系統 SHALL 提供 `sync_directory(src, dst, excludes, delete=True)` 函數，在來源目錄與目標目錄之間同步檔案。

- macOS/Linux：使用 `rsync -av` 搭配 `--exclude-from` 和選擇性的 `--delete`
- Windows：使用 Python `shutil.copytree` + `fnmatch` 過濾排除模式
- `delete` 參數控制是否刪除目標中來源沒有的檔案
- 回傳同步結果（新增/修改/刪除檔案數）

Push 流程 SHALL 在 `_sync_local_to_repo()` 完成後、`git_add_commit()` 之前，呼叫 `normalize_paths_in_repo(config)` 將 repo 中 settings.json 的絕對路徑替換為佔位符。

Pull 流程 SHALL 在 `_sync_repo_to_local()` 完成後，呼叫 `expand_paths_in_local(config)` 將本機 settings.json 的佔位符展開為當前系統路徑。

#### Scenario: macOS 上同步目錄

- **WHEN** 在 macOS 上呼叫 `sync_directory(~/.claude, repo/claude/, excludes=["debug/"], delete=True)`
- **THEN** 系統使用 `rsync -av --delete --exclude-from=<tmpfile>` 同步檔案

#### Scenario: Windows 上同步目錄

- **WHEN** 在 Windows 上呼叫 `sync_directory(~/.claude, repo/claude/, excludes=["debug/"])`
- **THEN** 系統使用 Python shutil 複製檔案，跳過符合排除模式的路徑

#### Scenario: 使用 delete=False

- **WHEN** 呼叫 `sync_directory(src, dst, excludes, delete=False)`
- **THEN** 系統只新增和更新檔案，不刪除目標中多出的檔案

#### Scenario: 排除模式匹配

- **WHEN** 來源目錄包含 `debug/log.txt` 且排除模式包含 `debug/`
- **THEN** 該檔案不會被同步到目標目錄

#### Scenario: Push 時路徑標準化

- **WHEN** 執行 `sync push`
- **THEN** `_sync_local_to_repo()` 完成後呼叫 `normalize_paths_in_repo(config)`，repo 中的 `settings.json` 路徑值被替換為 `{{HOME}}` 佔位符

#### Scenario: Pull 時路徑展開

- **WHEN** 執行 `sync pull`
- **THEN** `_sync_repo_to_local()` 完成後呼叫 `expand_paths_in_local(config)`，本機的 `settings.json` 佔位符被展開為當前系統的 `$HOME` 路徑

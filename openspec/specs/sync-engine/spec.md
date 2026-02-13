## ADDED Requirements

### Requirement: 目錄同步函數

系統 SHALL 提供 `sync_directory(src, dst, excludes, delete=True)` 函數，在來源目錄與目標目錄之間同步檔案。

- macOS/Linux：使用 `rsync -av` 搭配 `--exclude-from` 和選擇性的 `--delete`
- Windows：使用 Python `shutil.copytree` + `fnmatch` 過濾排除模式
- `delete` 參數控制是否刪除目標中來源沒有的檔案
- 回傳同步結果（新增/修改/刪除檔案數）

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

---

### Requirement: Git 操作封裝

系統 SHALL 提供 Git 操作函數，封裝 sync 流程中需要的 Git 指令。

- `git_init_or_clone(repo_dir, remote_url)`: 初始化或 clone repo
- `git_add_commit(repo_dir, message)`: stage 所有變更並 commit，無變更時回傳 False
- `git_pull_rebase(repo_dir)`: 執行 `git pull --rebase`
- `git_push(repo_dir)`: 執行 `git push`
- `git_status_summary(repo_dir)`: 回傳本機變更檔案數和遠端落後 commit 數
- 所有函數使用 `script/utils/system.py` 的 `run_command()` 執行指令

#### Scenario: 初始化空 repo

- **WHEN** 呼叫 `git_init_or_clone(repo_dir, remote_url)` 且 repo_dir 不存在
- **THEN** 系統嘗試 `git clone`；若遠端為空，則 `git init` + `git remote add`

#### Scenario: commit 無變更

- **WHEN** 呼叫 `git_add_commit(repo_dir, message)` 但 working tree 無變更
- **THEN** 函數回傳 `False`，不建立空 commit

#### Scenario: 取得狀態摘要

- **WHEN** 呼叫 `git_status_summary(repo_dir)`
- **THEN** 回傳包含 `local_changes: int`（未 commit 的變更檔案數）和 `behind_count: int`（落後遠端的 commit 數）的結果

---

### Requirement: 排除模式前綴化

系統 SHALL 提供函數將 ignore profile 的排除模式轉換為帶有 repo 子目錄前綴的 `.gitignore` 規則。

- 輸入：子目錄名稱（如 `claude`）和排除模式列表（如 `["debug/", "cache/"]`）
- 輸出：前綴化規則列表（如 `["claude/debug/", "claude/cache/"]`）

#### Scenario: 前綴化排除模式

- **WHEN** 呼叫 `prefix_excludes("claude", ["debug/", "*.log"])`
- **THEN** 回傳 `["claude/debug/", "claude/*.log"]`

#### Scenario: 空排除列表

- **WHEN** 呼叫 `prefix_excludes("gemini", [])`
- **THEN** 回傳空列表

---

### Requirement: 主機名稱與時間戳取得

系統 SHALL 提供函數取得本機主機名稱和當前時間戳，用於 commit message。

- 主機名稱：使用 `socket.gethostname()`
- 時間戳格式：`YYYY-MM-DD-HHmm`

#### Scenario: 產生 commit message

- **WHEN** 系統需要自動產生 sync commit message
- **THEN** 格式為 `sync: <hostname> <YYYY-MM-DD-HHmm>`（如 `sync: macbook-pro 2026-02-13-2115`）

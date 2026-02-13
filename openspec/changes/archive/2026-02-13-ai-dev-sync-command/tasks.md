## 1. 基礎設施

- [x] 1.1 在 `script/utils/paths.py` 新增 `get_sync_config_path()` 和 `get_sync_repo_dir()` 函數
- [x] 1.2 建立 `script/utils/sync_config.py`：定義 ignore profiles（claude, claude-mem）、sync.yaml 讀寫函數、.gitignore/.gitattributes 產生函數
- [x] 1.3 建立 `script/commands/sync.py`：初始化 Typer app 並定義空的子指令骨架（init/push/pull/status/add/remove）
- [x] 1.4 在 `script/main.py` 匯入並註冊 sync 指令群組

## 2. 同步引擎

- [x] 2.1 在 `sync_config.py` 實作 `sync_directory(src, dst, excludes, delete=True)`：macOS/Linux 用 rsync，Windows 用 shutil fallback
- [x] 2.2 在 `sync_config.py` 實作 Git 操作函數：`git_init_or_clone()`、`git_add_commit()`、`git_pull_rebase()`、`git_push()`、`git_status_summary()`
- [x] 2.3 在 `sync_config.py` 實作 `prefix_excludes()` 和 `generate_gitignore()` 函數
- [x] 2.4 在 `sync_config.py` 實作 `generate_gitattributes()` 函數

## 3. 指令實作

- [x] 3.1 實作 `sync init --remote <url>`：建立 repo、同步預設目錄、產生 ignore 檔案、首次 commit + push、儲存 sync.yaml
- [x] 3.2 實作 `sync push`：讀取設定、rsync 本機→repo、git commit + pull --rebase + push、顯示結果
- [x] 3.3 實作 `sync pull --no-delete`：git pull --rebase、rsync repo→本機、顯示結果
- [x] 3.4 實作 `sync status`：Rich 表格顯示各目錄本機變更數、遠端落後數、最後同步時間
- [x] 3.5 實作 `sync add <path> --profile --ignore`：驗證路徑、更新 sync.yaml、建立子目錄、更新 .gitignore
- [x] 3.6 實作 `sync remove <path>`：從設定移除、詢問是否刪除 repo 子目錄、更新 .gitignore

## 4. 測試

- [x] 4.1 建立 `tests/test_sync_config.py`：測試 sync.yaml 讀寫、ignore profiles、.gitignore 產生、prefix_excludes
- [x] 4.2 建立 `tests/test_sync_engine.py`：測試 sync_directory（rsync/shutil）、Git 操作函數
- [x] 4.3 建立 `tests/test_sync_command.py`：測試各子指令的 CLI 行為（使用 typer.testing.CliRunner）

## 5. 文件與整合

- [x] 5.1 更新 `docs/dev-guide/ai-tools/CLAUDE-CODE-SYNC.md`：新增 ai-dev sync 方案的使用說明
- [x] 5.2 更新 CHANGELOG.md

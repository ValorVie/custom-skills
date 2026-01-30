## 1. 工具模組 (custom_repos.py)

- [x] 1.1 建立 `script/utils/custom_repos.py`，定義 `REQUIRED_DIRS = ["agents", "skills", "commands", "hooks", "plugins"]`
- [x] 1.2 實作 `get_custom_repos_config_path()` 回傳 `~/.config/ai-dev/repos.yaml`
- [x] 1.3 實作 `load_custom_repos()` 讀取設定檔，檔案不存在時回傳 `{"repos": {}}`
- [x] 1.4 實作 `save_custom_repos(data)` 寫入設定檔，自動建立 `~/.config/ai-dev/` 目錄
- [x] 1.5 實作 `add_custom_repo(name, url, branch, local_path)` 新增 repo 條目（含 `added_at` 時間戳），已存在則警告
- [x] 1.6 實作 `remove_custom_repo(name)` 移除 repo 條目
- [x] 1.7 實作 `list_custom_repos()` 回傳所有 custom repos 清單
- [x] 1.8 實作 `validate_repo_structure(repo_dir)` 驗證五個必要目錄，缺少時發出警告但不阻擋

## 2. CLI 指令 (add_custom_repo.py)

- [x] 2.1 建立 `script/commands/add_custom_repo.py`，定義 `add_custom_repo()` 函式與 Typer 參數（`remote_path`, `--name`, `--branch`）
- [x] 2.2 復用 `add_repo.py` 的 `parse_repo_url()` 解析 URL（HTTPS、SSH、簡寫格式）
- [x] 2.3 實作 clone 邏輯：clone 到 `~/.config/<name>/`，目錄已存在時跳過，失敗時終止
- [x] 2.4 呼叫 `validate_repo_structure()` 驗證 repo 結構並顯示結果
- [x] 2.5 呼叫 `add_custom_repo()` 寫入設定檔，顯示完成訊息

## 3. 註冊指令到 CLI

- [x] 3.1 修改 `script/main.py`：import `add_custom_repo` 並以 `app.command(name="add-custom-repo")` 註冊

## 4. Manifest Source 欄位

- [x] 4.1 修改 `script/utils/manifest.py`：擴充 `ManifestTracker` 的 `record_skill`、`record_command`、`record_agent`、`record_workflow` 方法，增加 `source` 參數（預設 `"custom-skills"`）
- [x] 4.2 修改 `ManifestTracker.to_manifest()`：在每個資源條目中輸出 `source` 欄位
- [x] 4.3 確認 `detect_conflicts()` 和 `find_orphans()` 讀取 manifest 時對缺少 `source` 的舊格式向後相容

## 5. 分發流程整合

- [x] 5.1 修改 `script/utils/shared.py` 的 `copy_custom_skills_to_targets()`：現有 custom-skills 資源分發時傳入 `source="custom-skills"`
- [x] 5.2 在 `copy_custom_skills_to_targets()` 中，於現有分發邏輯之後，讀取 `repos.yaml` 並逐一分發每個 custom repo 的資源（`skills/`, `commands/<platform>/`, `agents/<platform>/`），傳入對應的 `source` 名稱
- [x] 5.3 處理 custom repo 本地目錄不存在的情況：顯示警告並跳過
- [x] 5.4 確認 `integrate_to_dev_project()` 不包含 custom repo 資源

## 6. Install / Update 整合

- [x] 6.1 修改 `script/commands/install.py`：在 REPOS clone 之後，讀取 `repos.yaml` 並 clone 尚未存在的 custom repos，失敗時警告並繼續
- [x] 6.2 修改 `script/commands/update.py`：在現有 repos 更新之後，對每個 custom repo 執行 fetch + reset，失敗時警告並繼續
- [x] 6.3 確認 update 完成後的更新摘要包含有新更新的 custom repos

## 7. 驗證

- [ ] 7.1 手動測試 `ai-dev add-custom-repo owner/repo`：確認 clone、結構驗證、設定檔寫入皆正常
- [ ] 7.2 手動測試 `ai-dev update`：確認 custom repos 被更新
- [ ] 7.3 手動測試 `ai-dev clone`：確認 custom repos 資源被分發，manifest 包含 `source` 欄位
- [ ] 7.4 確認在開發專案中執行 `ai-dev clone` 時，custom repo 資源不被整合到開發目錄

## 1. 基礎模組

- [ ] 1.1 建立 `script/utils/project_tracking.py` — 實作 `.ai-dev-project.yaml` 的讀取、寫入、檔案追蹤邏輯
- [ ] 1.2 擴充 `script/utils/custom_repos.py` — 在 `add_custom_repo()` 支援 `type` 欄位（`template` / `tool`），修改 `repos.yaml` 格式
- [ ] 1.3 建立 `script/utils/smart_merge.py` — 實作智慧合併流程（SHA-256 比對、互動提示、附加/覆蓋/跳過/diff）

## 2. init-from 指令

- [ ] 2.1 建立 `script/commands/init_from.py` — 實作 `ai-dev init-from` 指令主體（參數解析、clone、smart merge 呼叫）
- [ ] 2.2 在 `script/main.py` 註冊 `init-from` 指令
- [ ] 2.3 實作 `--update` 模式 — 讀取 `.ai-dev-project.yaml`、pull 最新、重新走 smart merge
- [ ] 2.4 實作 `--force` 和 `--skip-conflicts` 批次模式
- [ ] 2.5 實作模板 repo 包含標準工具目錄時的警告訊息

## 3. clone 指令整合

- [ ] 3.1 修改 `script/utils/shared.py` 的 `_sync_to_project_directory()` — 讀取 CWD 的 `.ai-dev-project.yaml`，跳過 `managed_files` 中的檔案
- [ ] 3.2 在跳過時顯示提示訊息（含模板來源名稱）

## 4. update 指令整合

- [ ] 4.1 修改 `script/commands/update.py` — 確保 `type: template` 的 repo 也會被 pull/update
- [ ] 4.2 更新後若偵測到模板有新 commit，顯示提示訊息引導使用者執行 `ai-dev init-from --update`

## 5. 文件

- [ ] 5.1 建立 `docs/dev-guide/workflow/custom-template-format.md` — 客製化模板/工具格式規範（通用機制說明）
- [ ] 5.2 更新 `docs/dev-guide/workflow/ai-dev-framework-architecture.md` — 加入 init-from 指令說明與架構圖

## 6. 測試

- [ ] 6.1 `project_tracking.py` 單元測試 — .ai-dev-project.yaml 讀寫、managed_files 操作
- [ ] 6.2 `smart_merge.py` 單元測試 — SHA-256 比對、排除清單、各合併策略
- [ ] 6.3 `init_from.py` 整合測試 — 首次初始化、--update、--force、--skip-conflicts
- [ ] 6.4 clone 整合測試 — 有/無 .ai-dev-project.yaml 時的分發行為差異

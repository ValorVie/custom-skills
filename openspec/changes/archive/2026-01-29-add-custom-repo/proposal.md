## Why

開源框架（custom-skills）的 `add-repo` 指令將 repo 資訊寫入 `upstream/sources.yaml`（納入版控），適用於追蹤他人維護的上游專案。但使用者（如公司團隊）需要一個方式來註冊**自己維護的私有 repo**，這些 repo 的 URL 和設定不應出現在開源 repo 中。目前缺乏使用者層級的 repo 管理機制，導致公司無法在不 fork 開源 repo 的情況下整合內部 AI 工具。

## What Changes

- 新增 `ai-dev add-custom-repo` CLI 指令，用於註冊使用者自訂的 repo
- 新增使用者層級設定檔 `~/.config/ai-dev/repos.yaml`，儲存 custom repo 清單
- 定義 custom repo 的目錄結構規範（根目錄必須包含 `agents/`, `skills/`, `commands/`, `hooks/`, `plugins/`）
- 修改 `ai-dev update` 流程，使其同時拉取 custom repos
- 修改 `ai-dev install` 流程，使其同時 clone custom repos
- 修改 `ai-dev clone` 分發流程，將 custom repos 的資源合併分發到各 AI 工具目錄
- Custom repos 的資源**不會**被整合回開發專案目錄（`integrate_to_dev_project` 排除）

## Capabilities

### New Capabilities

- `custom-repo-management`: 管理使用者自訂 repo 的設定檔讀寫、結構驗證、新增與移除
- `custom-repo-cli`: `add-custom-repo` CLI 指令的介面定義與參數處理

### Modified Capabilities

- `cli-distribution`: 分發流程需額外包含 custom repos 的資源，合併進現有 manifest 追蹤，並在 manifest 中增加 `source` 欄位標記資源來源
- `setup-script`: `install` 和 `update` 指令需涵蓋 custom repos 的 clone 與 pull

## Impact

- **新增檔案**: `script/utils/custom_repos.py`, `script/commands/add_custom_repo.py`
- **修改檔案**: `script/main.py`, `script/commands/update.py`, `script/commands/install.py`, `script/utils/shared.py`
- **使用者端新增**: `~/.config/ai-dev/repos.yaml` 設定檔
- **不影響**: 現有 `add-repo` 指令、`upstream/sources.yaml`、開源 repo 的版控內容

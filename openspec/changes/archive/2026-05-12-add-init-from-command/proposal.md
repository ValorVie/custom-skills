## Why

目前 `ai-dev` 提供 `project init` 建立通用 AI 配置骨架，以及 `add-custom-repo` 管理跨專案共用工具。但當特定類型專案（如 QDM/OpenCart）需要高度客製化的 AI 配置時，缺乏一個從「客製化模板 repo」初始化專案的機制。使用者必須手動複製 CLAUDE.md、.standards/、.claude/ 等檔案，且無法追蹤上游模板的更新。

## What Changes

- 新增 `ai-dev init-from` 指令，從客製化模板 repo 初始化專案目錄
- 新增 `.ai-dev-project.yaml` 檔案級所有權追蹤機制
- 修改 `ai-dev clone` 分發流程，讀取 `.ai-dev-project.yaml` 跳過已管理的檔案
- 新增客製化模板/工具格式規範文件（custom-skills 通用機制說明）

## Capabilities

### New Capabilities

- `init-from-command`: `ai-dev init-from` 指令，支援首次初始化與 `--update` 更新模式，包含智慧合併流程（附加/覆蓋/跳過/diff 預覽）
- `project-ownership-tracking`: `.ai-dev-project.yaml` 檔案級所有權追蹤，記錄哪些檔案由哪個模板 repo 管理
- `custom-template-format`: 客製化模板 repo 的格式規範與文件，定義模板 repo 與工具 repo 的結構區分

### Modified Capabilities

- `clone-command`: 分發時讀取 CWD 的 `.ai-dev-project.yaml`，跳過由 init-from 管理的檔案

## Impact

- **新增檔案**:
  - `script/commands/init_from.py` — init-from 指令實作
  - `script/utils/project_tracking.py` — 所有權追蹤邏輯
  - `docs/dev-guide/workflow/custom-template-format.md` — 客製化模板格式規範
- **修改檔案**:
  - `script/utils/shared.py` — clone 分發流程加入所有權檢查
  - `script/main.py` — 註冊 init-from 指令
- **外部影響**:
  - qdm-ai-base repo 需新增初始化與維護流程文件
- **依賴**:
  - 無新增外部依賴，使用現有 typer + rich + pyyaml

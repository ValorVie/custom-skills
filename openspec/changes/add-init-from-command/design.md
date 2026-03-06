## Context

目前 `ai-dev` 的資源管理分為兩條管線：
- **通用模板**（`project init`）：從 `project-template/` 初始化空白 AI 配置骨架
- **通用工具**（`add-custom-repo` + `clone`）：管理跨專案共用的 skills/commands/agents，分發到全域目錄

當特定類型專案（如 QDM/OpenCart）需要客製化 AI 配置時，使用者已將需求拆為：
- **客製化模板** repo（如 `qdm-ai-base`）：CLAUDE.md、.standards/、.claude/ 等專案級配置
- **客製化工具** repo（如 `qdm-ai-tools`）：skills/commands/agents 等工具，走 `add-custom-repo` 管線

缺少的是「從客製化模板 repo 初始化專案，並追蹤檔案所有權」的機制。

## Goals / Non-Goals

**Goals:**

- 提供 `ai-dev init-from` 指令，從客製化模板 repo 初始化專案目錄
- 實作智慧合併流程（比對內容，讓使用者選擇附加/覆蓋/跳過）
- 產生 `.ai-dev-project.yaml` 追蹤哪些檔案由模板管理（檔案級粒度）
- `ai-dev clone` 分發時自動跳過由模板管理的檔案，避免覆蓋
- 支援 `--update` 模式，從上游模板拉取更新並重新走智慧合併

**Non-Goals:**

- 不處理客製化工具 repo 的分發（那是 `add-custom-repo` + `clone` 的職責）
- 不取代 `project init`（通用模板仍走現有流程）
- 不支援多個模板同時初始化同一專案（一個專案只能有一個 init-from 來源）
- 不做自動合併（所有內容差異都需使用者確認）

## Decisions

### Decision 1: 客製化模板與客製化工具分離

**選擇**：模板 repo（如 qdm-ai-base）只包含專案級配置，不包含 5 個標準工具目錄（agents/commands/hooks/plugins/skills）。工具 repo（如 qdm-ai-tools）走 `add-custom-repo`。

**替代方案**：允許模板 repo 包含工具目錄，init-from 時同時分發工具。

**理由**：
- 關注點分離——模板管理專案配置，工具管理跨專案共用能力
- 避免 init-from 和 clone 的分發路徑重疊
- 使用者已自行做了這個區分（qdm-ai-base vs qdm-ai-tools）

### Decision 2: 檔案級所有權追蹤

**選擇**：`.ai-dev-project.yaml` 記錄每個由模板管理的檔案路徑（相對路徑），而非目錄級鎖定。

**替代方案**：目錄級鎖定（如 `.claude/` 整個由模板管理）。

**理由**：
- 使用者可能在 `.claude/skills/` 中混用模板的和 clone 的 skills
- 檔案級追蹤更精確，clone 可以補充模板未覆蓋的檔案
- 追蹤開銷可接受（通常模板檔案在 50-200 個以內）

### Decision 3: 模板 repo 的本地存放

**選擇**：clone 到 `~/.config/<name>/`（與 custom repo 相同位置），並寫入 `~/.config/ai-dev/repos.yaml` 的 `templates` 段落。

**替代方案 A**：clone 到暫存目錄，用完刪除。
**替代方案 B**：新建 `~/.config/ai-dev/templates.yaml` 獨立配置。

**理由**：
- 復用現有 repos 基礎設施（clone、update 邏輯）
- `repos.yaml` 中用 `type: template` 欄位區分模板和工具 repo
- `ai-dev update` 可統一拉取所有 repo（含模板），無需額外邏輯

### Decision 4: 智慧合併的互動流程

**選擇**：逐檔互動，提供四個選項：附加到尾部 [A]、覆蓋 [O]、跳過 [S]、顯示 diff [D]。

**替代方案**：批次模式（先列出所有差異，再統一選擇策略）。

**理由**：
- 不同檔案類型適合不同策略（.gitignore 適合附加，.editorconfig 適合覆蓋）
- 逐檔互動讓使用者對每個決策有完整 context
- 提供 `--force` 和 `--skip-conflicts` 批次選項給進階使用者

### Decision 5: clone 整合方式

**選擇**：在 `copy_custom_skills_to_targets()` 的分發流程中，讀取 CWD 的 `.ai-dev-project.yaml`，對 `managed_files` 中列出的路徑在分發到**專案目錄**（非全域目錄）時跳過。

**理由**：
- clone 分發到全域目錄（~/.claude/）不受影響——全域和專案是不同層級
- 僅當 clone 要同步到專案目錄（`_sync_to_project_directory`）時才需要檢查
- 最小化對現有流程的侵入

## Risks / Trade-offs

- **[風險] 模板和通用模板的 .standards/ 衝突** → 客製化模板通常包含完整的 .standards/，會覆蓋 `project init` 產生的。這是預期行為——客製化模板的目的就是取代通用配置。使用者應先 `project init`，再 `init-from`。
- **[風險] .ai-dev-project.yaml 被使用者刪除** → clone 會回到預設行為（分發所有檔案）。無需特殊處理，這是使用者的顯性選擇。
- **[取捨] 不支援多模板** → 降低複雜度，但限制了組合靈活性。如需多模板，可手動管理或未來擴充。
- **[取捨] 逐檔互動在大量差異時較慢** → 提供 `--force` 和 `--skip-conflicts` 作為快捷方式。

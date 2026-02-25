# cli-distribution Specification

## Purpose
TBD - created by archiving change add-global-cli-distribution. Update Purpose after archive.
## Requirements
### Requirement: CLI 分發機制
ai-dev CLI SHALL 以 npm scoped package (`@valorvie/ai-dev`) 分發，取代 Python egg/wheel 格式。

#### Scenario: 套件包含必要檔案
- **WHEN** 套件發佈到 npm
- **THEN** 包含 `src/`、`dist/`、`skills/`、`commands/`、`agents/` 目錄

#### Scenario: 更新 CLI
- **WHEN** 使用者執行 `bun update -g @valorvie/ai-dev`
- **THEN** CLI 更新到最新版本

### Requirement: Update Notification (更新通知)

`ai-dev update` 指令 MUST (必須) 在更新完成後顯示哪些儲存庫有新的更新。

#### Scenario: 顯示有更新的儲存庫

給定多個上游儲存庫
當執行 `ai-dev update` 且部分儲存庫有新 commits 時
則應該：
1. 在更新完成後顯示摘要
2. 列出所有有新更新的儲存庫名稱
3. 若無任何更新，顯示「所有儲存庫皆為最新」

#### Scenario: 沒有更新時的顯示

給定所有上游儲存庫皆為最新
當執行 `ai-dev update` 時
則應該顯示「所有儲存庫皆為最新」訊息

### Requirement: Three-Stage Copy Flow (三階段複製流程)

腳本 MUST 使用簡化的分發流程來管理資源分發。

> **變更說明**：移除 Stage 2（整合到 custom-skills），`~/.config/custom-skills` 內容完全由 git repo 控制。
> Stage 2 的整合功能已移至開發者模式，透過 `ai-dev clone --sync-project` 在開發目錄執行。
> **新增**：Stage 3 擴充為同時分發 custom repos 的資源。

#### Scenario: Stage 1 - Clone 外部套件

給定外部儲存庫 URL
當執行 `ai-dev install` 時
則應該 clone 到 `~/.config/<repo-name>/`：
- superpowers → `~/.config/superpowers/`
- universal-dev-standards → `~/.config/universal-dev-standards/`
- obsidian-skills → `~/.config/obsidian-skills/`
- anthropic-skills → `~/.config/anthropic-skills/`
- everything-claude-code → `~/.config/everything-claude-code/`
- custom-skills → `~/.config/custom-skills/`

#### Scenario: Stage 3 - 分發到目標目錄（含 custom repos）

給定 `~/.config/custom-skills/` 由 git repo 控制，且 `~/.config/ai-dev/repos.yaml` 存在已註冊的 custom repos
當執行 `ai-dev clone` 時
則 MUST：
1. 先分發 `~/.config/custom-skills/` 的資源到所有目標目錄
2. 再依序分發每個 custom repo 的資源到對應目標目錄
3. 所有資源使用同一個 ManifestTracker 追蹤

#### Scenario: Custom repo 資源目錄映射

給定 custom repo 的目錄結構
當分發 custom repo 資源時
則 MUST 依照以下映射：
- `skills/` → 分發到所有平台的 skills 目錄
- `commands/claude/` → Claude Code commands 目錄
- `commands/opencode/` → OpenCode commands 目錄
- `commands/gemini/` → Gemini CLI commands 目錄
- `agents/claude/` → Claude Code agents 目錄
- `agents/opencode/` → OpenCode agents 目錄
- `hooks/` → 不分發（保留未來擴充）
- `plugins/` → 不分發（保留未來擴充）

#### Scenario: Custom repo 不存在本地目錄

給定 `repos.yaml` 中註冊了某 custom repo 但其本地目錄不存在
當執行分發時
則 MUST 跳過該 repo 並顯示警告，不中斷整體分發流程

#### Scenario: 不再自動執行 Stage 2 整合

給定使用者執行 `ai-dev clone`
當分發流程執行時
則不應該自動將外部來源（UDS, Obsidian, Anthropic）整合到 `~/.config/custom-skills`
且 `~/.config/custom-skills` 的內容應由 git repo 控制

#### Scenario: Custom repo 資源不整合回開發專案

給定使用者在 custom-skills 開發專案中執行 `ai-dev clone`
當 `integrate_to_dev_project()` 執行時
則 MUST 不包含任何 custom repo 的資源
且只整合現有的上游來源（UDS, Obsidian, Anthropic, ECC）

### Requirement: Manifest Source 追蹤 (Manifest Source Tracking)

分發流程 MUST 在 manifest 的每個資源條目中記錄 `source` 欄位，標記該資源來自哪個 repo。

#### Scenario: Custom-skills 資源的 source 標記

- **WHEN** 分發 `~/.config/custom-skills/` 的資源時
- **THEN** manifest 中該資源的 `source` 欄位 MUST 為 `"custom-skills"`

#### Scenario: Custom repo 資源的 source 標記

- **WHEN** 分發名為 `company-ai-tools` 的 custom repo 資源時
- **THEN** manifest 中該資源的 `source` 欄位 MUST 為 `"company-ai-tools"`（使用 repos.yaml 中的 key 名稱）

#### Scenario: Manifest 檔案格式

- **WHEN** 分發完成後寫入 manifest 時
- **THEN** 每個資源條目 MUST 包含 `hash` 和 `source` 兩個欄位
- **THEN** 格式如下：
  ```yaml
  files:
    skills:
      some-skill:
        hash: sha256:...
        source: custom-skills
      company-skill:
        hash: sha256:...
        source: company-ai-tools
  ```

#### Scenario: 向後相容既有 manifest

- **WHEN** 讀取不含 `source` 欄位的舊 manifest 時
- **THEN** MUST 正常運作，不因缺少 `source` 而報錯
- **THEN** 衝突檢測邏輯不受 `source` 欄位影響

### Requirement: 反向同步排除機制

`ai-dev project init --force` 的反向同步 SHALL 排除不屬於共享範本的檔案，並將同步目標固定為 repo 內的 `project-template/`。

#### Scenario: 反向同步目標為 repo 內的 project-template

- **WHEN** 在 custom-skills 專案中執行 `ai-dev project init --force`
- **THEN** 同步目標 SHALL 為 `cwd/project-template/`
- **AND** 不使用 `get_project_template_dir()`（避免指向 `~/.config`）

#### Scenario: 排除個人設定檔

- **WHEN** 反向同步複製目錄（如 `.claude/`）到 `project-template/`
- **THEN** SHALL 排除 `settings.local.json`
- **AND** 排除清單定義於 `EXCLUDE_FROM_TEMPLATE` 常數

#### Scenario: 正向 init 也排除個人設定檔

- **WHEN** 從 project-template 複製到目標專案
- **THEN** SHALL 同樣排除 `settings.local.json`
- **AND** 使用相同的排除機制


## ADDED Requirements

### Requirement: distribution.yaml 設定檔格式

系統 SHALL 支援 `upstream/distribution.yaml` 設定檔，定義外部來源的選擇性分發規則。

#### Scenario: 基本結構

- **WHEN** 讀取 `upstream/distribution.yaml`
- **THEN** SHALL 包含以下頂層欄位：`version`（整數）、`source`（來源名稱）、`source_path`（本地路徑）、`distribute`（分發規則）、`skip_directories`（跳過的目錄清單）、`exclude`（排除清單）

#### Scenario: distribute 區塊定義

- **WHEN** 解析 `distribute` 區塊
- **THEN** SHALL 支援三種資源類型：`skills`、`commands`、`agents`
- **THEN** 每種資源類型 SHALL 定義 `source_path`（來源子目錄）和 `targets`（目標平台清單）
- **THEN** `commands` 和 `agents` SHALL 支援按平台定義不同的 `source_path`

#### Scenario: source_path 展開

- **WHEN** `source_path` 包含 `~`
- **THEN** SHALL 展開為使用者家目錄的絕對路徑

### Requirement: ECC 選擇性分發邏輯

`ai-dev clone` SHALL 根據 `upstream/distribution.yaml` 從 ECC 來源目錄選擇性分發資源到各平台目標。

#### Scenario: Claude Code 平台完整分發

- **WHEN** 執行 `ai-dev clone` 且 `~/.config/everything-claude-code/` 存在
- **THEN** SHALL 分發以下資源到 Claude Code 目標：
  - `skills/` → `~/.claude/skills/`
  - `commands/*.md` → `~/.claude/commands/`
  - `agents/*.md` → `~/.claude/agents/`

#### Scenario: OpenCode 平台分發（使用 .opencode 來源）

- **WHEN** 執行 `ai-dev clone` 且 `~/.config/everything-claude-code/` 存在
- **THEN** SHALL 從 `.opencode/` 子目錄分發到 OpenCode 目標：
  - `skills/` → `~/.config/opencode/skills/`
  - `.opencode/commands/` → `~/.config/opencode/commands/`
  - `.opencode/prompts/agents/` → `~/.config/opencode/agents/`

#### Scenario: Gemini 平台部分分發

- **WHEN** 執行 `ai-dev clone` 且 `~/.config/everything-claude-code/` 存在
- **THEN** SHALL 分發到 Gemini 目標：
  - `skills/` → `~/.gemini/skills/`
  - `agents/*.md` → `~/.gemini/agents/`（共用 Claude Code 格式）
- **THEN** SHALL 不分發 commands（Gemini 使用 .toml 格式，不相容）

#### Scenario: Codex 平台僅分發 skills

- **WHEN** 執行 `ai-dev clone` 且 `~/.config/everything-claude-code/` 存在
- **THEN** SHALL 只分發 `skills/` → `~/.codex/skills/`
- **THEN** SHALL 不分發 commands 和 agents（Codex 不支援）

#### Scenario: ECC 來源目錄不存在

- **WHEN** 執行 `ai-dev clone` 且 `~/.config/everything-claude-code/` 不存在
- **THEN** SHALL 跳過 ECC 分發
- **THEN** SHALL 顯示警告訊息提示先執行 `ai-dev update`

#### Scenario: 跳過 skip_directories 定義的目錄

- **WHEN** 分發 ECC skills 時遇到 `skip_directories` 中定義的目錄名
- **THEN** SHALL 不複製該目錄及其內容

### Requirement: ECC 分發 Manifest 追蹤

ECC 分發的檔案 SHALL 納入現有 ManifestTracker 系統追蹤，支援衝突偵測和孤兒清理。

#### Scenario: 記錄分發檔案 hash

- **WHEN** ECC 檔案被分發到目標平台
- **THEN** ManifestTracker SHALL 記錄檔案路徑和 hash 值
- **THEN** source 欄位 SHALL 標記為 `ecc`（區別於 `custom-skills` 和 custom repo 來源）

#### Scenario: 偵測衝突

- **WHEN** ECC 分發的檔案與 custom-skills 或 custom repo 的檔案同名
- **THEN** SHALL 按衝突處理策略處理（force/skip/backup/interactive）

#### Scenario: 清理孤兒檔案

- **WHEN** ECC 上游移除了某個 skill/command/agent
- **THEN** 下次 clone 時 ManifestTracker SHALL 偵測到孤兒並清理目標目錄中的對應檔案

### Requirement: exclude 清單支援

distribution.yaml 的 `exclude` 欄位 SHALL 支援按資源類型和平台排除特定項目。

#### Scenario: 排除特定 skill

- **WHEN** `exclude.skills` 包含 `["example-skill"]`
- **THEN** 所有平台 SHALL 不分發名為 `example-skill` 的 skill 目錄

#### Scenario: 排除特定平台的 command

- **WHEN** `exclude.commands.claude` 包含 `["example-cmd"]`
- **THEN** Claude Code 平台 SHALL 不分發名為 `example-cmd` 的 command
- **THEN** 其他平台不受影響

#### Scenario: 空排除清單

- **WHEN** `exclude` 清單為空陣列
- **THEN** SHALL 分發該類型的所有資源（無排除）

## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Antigravity CLI (agy) 分發目標

`ai-dev` MUST 以 `agy` 作為 Antigravity CLI 的分發 target 識別碼，取代已退役的 `gemini`（Google Gemini CLI 已於 2026-06-18 關閉）。顯示名稱 MUST 為 `Antigravity CLI (agy)`。`agy` target MUST 僅分發 skills 至 `~/.gemini/skills/`（Antigravity 工具共用 skills 目錄）。`ai-dev` MUST NOT 嘗試以 npm 安裝 `@google/gemini-cli`，亦 MUST NOT 保留 `gemini` 作為相容別名。

#### Scenario: agy 為有效 target 並分發 skills

給定使用者執行 `ai-dev list --target agy --type skills`
當指令解析 target 時
則 MUST 將 `agy` 視為有效 target 並列出其 skills（位於 `~/.gemini/skills/`）

#### Scenario: 不再接受舊 target 值 gemini

給定使用者執行 `ai-dev list --target gemini`
當指令解析 target 時
則 MUST 視 `gemini` 為無效 target（不再對應任何分發目標）

#### Scenario: agy target 不分發 commands 與 agents

給定 `agy` target 的資源型別對照
當列舉或分發 `agy` 的資源時
則 MUST 僅包含 `skills`，不包含 `commands` 或 `agents`（agy 無全域 commands/agents 目錄）

#### Scenario: 安裝不再嘗試退役的 gemini npm 套件

給定使用者執行 `ai-dev install`
當安裝全域 npm 套件時
則 MUST NOT 包含 `@google/gemini-cli`
且安裝流程不因該套件退役而失敗

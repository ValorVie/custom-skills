## MODIFIED Requirements

### Requirement: Three-Stage Copy Flow (三階段複製流程)

腳本 MUST 使用簡化的分發流程管理仍由 ai-dev framework 擁有的資源。第一方 npx-managed skills 不屬於 Stage 3 copy；它們由 npx-skills phase 管理。

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

第一方 `ValorVie/ai-dev-skills` SHALL 由 `npx skills` 解析；Stage 1 SHALL NOT 另外維護一份供 copy 使用的 clone。

#### Scenario: Stage 3 - 分發到目標目錄（含 custom repos）

給定 `~/.config/custom-skills/` 由 git repo 控制，且 `~/.config/ai-dev/repos.yaml` 存在已註冊的 custom repos
當執行 `ai-dev clone` 時
則 MUST：
1. 先分發 `~/.config/custom-skills/` 中仍由 framework 管理的 commands、agents、workflows 與 plugins
2. 不分發第一方 npx-managed skills
3. 再依序分發每個 custom repo 的資源到對應目標目錄
4. 再依 `upstream/distribution.yaml` 分發 ECC 白名單資源
5. 只對 clone 實際擁有的資源使用 ManifestTracker

#### Scenario: Custom repo 資源目錄映射

給定 custom repo 的目錄結構
當分發 custom repo 資源時
則 MUST 依照以下映射：
- `skills/` → 分發到所有平台的 skills 目錄，但排除 npx manifest 已接管的 canonical IDs
- `commands/claude/` → Claude Code commands 目錄
- `commands/opencode/` → OpenCode commands 目錄
- `agents/claude/` → Claude Code agents 目錄
- `agents/opencode/` → OpenCode agents 目錄
- `hooks/` → 不分發（保留未來擴充）
- `plugins/` → 不分發（保留未來擴充）

#### Scenario: Custom repo 不存在本地目錄

給定 `repos.yaml` 中註冊了某 custom repo 但其本地目錄不存在
當執行分發時
則 MUST 跳過該 repo 並顯示警告，不中斷整體分發流程。

#### Scenario: 不再自動執行 Stage 2 整合

給定使用者執行 `ai-dev clone`
當分發流程執行時
則不應該自動將外部來源（UDS、Obsidian、Anthropic）整合到 `~/.config/custom-skills`
且 `~/.config/custom-skills` 的 framework 內容應由 git repo 控制。

#### Scenario: Custom repo 資源不整合回開發專案

給定使用者在 custom-skills 開發專案中執行 `ai-dev clone`
當 `integrate_to_dev_project()` 執行時
則 MUST 不包含任何 custom repo 的資源
且只整合既有專案層級來源；第一方 global skills SHALL 不透過此入口回寫。

## ADDED Requirements

### Requirement: 第一方 npx ownership 不進入 ai-dev distribution manifest

ai-dev SHALL 以 npx declarative manifest 辨識第一方 npx-managed skills。這些 skills SHALL 不寫入 target ManifestTracker，也不得被 clone orphan cleanup、force、backup 或 conflict resolution 當成 ai-dev-owned resource。

#### Scenario: clone prescan 遇到 npx-managed skill

- **WHEN** custom-skills、custom repo 或 ECC prescan 發現 canonical ID 已由 npx manifest 接管
- **THEN** prescan SHALL 跳過該 skill
- **THEN** 新 target manifest SHALL 不建立該 canonical ID 的 clone ownership entry

#### Scenario: 舊 manifest 尚有第一方 entry

- **WHEN** 舊 target manifest 仍有 `source=custom-skills` 的第一方 skill entry
- **THEN** 一般 clone SHALL 不直接把它視為 orphan 並刪除
- **THEN** 只有一次性遷移流程在 npx 安裝與內容驗證成功後才可移除該 entry

#### Scenario: npx-managed skill 與 ECC 同名

- **WHEN** ECC 或 custom repo 啟用的 skill 與 npx-managed canonical ID 同名
- **THEN** 系統 SHALL 在寫入目標前停止該名稱的 clone 分發
- **THEN** SHALL 顯示兩個來源與解除衝突的設定入口

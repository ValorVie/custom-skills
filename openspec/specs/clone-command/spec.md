## MODIFIED Requirements

### Requirement: Clone Command (分發指令)

CLI MUST (必須) 提供 `clone` 子命令，將 `~/.config/custom-skills` 內容分發到各工具目錄。

> **變更說明**：分發流程新增 ECC 選擇性分發階段。在 custom-skills 和 custom repos 分發完成後，從 `~/.config/everything-claude-code/` 根據 `upstream/distribution.yaml` 選擇性分發 ECC 的 skills/agents/commands。

#### Scenario: 基本分發流程（使用者模式）

給定 `~/.config/custom-skills/` 目錄由 git repo 控制
當執行 `ai-dev clone` 時
則應該：
1. 直接執行 Stage 3（分發到各工具目錄）
2. 不執行 Stage 2（不整合外部來源到 custom-skills）
3. 讀取 `upstream/distribution.yaml` 執行 ECC 選擇性分發
4. 顯示分發的目標與結果

#### Scenario: 分發順序

- **WHEN** 執行 `ai-dev clone`
- **THEN** 分發順序 SHALL 為：
  1. custom-skills 本身（skills, commands, agents, workflows）
  2. custom repos（repos.yaml 中的自訂 repo）
  3. ECC 選擇性分發（distribution.yaml 定義的規則）

#### Scenario: 分發目標

給定執行 `ai-dev clone` 時
則應該分發到以下目錄：
- Claude Code: `~/.claude/skills/`, `~/.claude/commands/`, `~/.claude/agents/`, `~/.claude/workflows/`
- OpenCode: `~/.config/opencode/skills/`, `~/.config/opencode/commands/`, `~/.config/opencode/agents/`, `~/.config/opencode/plugins/`
- Gemini CLI: `~/.gemini/skills/`, `~/.gemini/commands/`, `~/.gemini/agents/`
- Codex: `~/.codex/skills/`
- Antigravity: `~/.gemini/antigravity/global_skills/`, `~/.gemini/antigravity/global_workflows/`

#### Scenario: 含 .clonepolicy.json 的 skill 使用逐檔複製

- **WHEN** skill 目錄包含 `.clonepolicy.json`
- **THEN** 系統 SHALL 不使用 `shutil.copytree`
- **THEN** 系統 SHALL 改用逐檔遍歷，依 `.clonepolicy.json` 中的 rules 決定每個檔案的處理策略
- **THEN** 目錄結構 SHALL 在目標自動建立（保持來源的子目錄結構）

#### Scenario: 無 .clonepolicy.json 的 skill 行為不變

- **WHEN** skill 目錄不包含 `.clonepolicy.json`
- **THEN** 系統 SHALL 維持原有的 `shutil.copytree(item, dst_item, dirs_exist_ok=True)` 行為

#### Scenario: 含 policy 的 skill 跳過目錄層級衝突檢測

- **WHEN** skill 目錄包含 `.clonepolicy.json`
- **THEN** 該 skill SHALL 不參與目錄層級的 ManifestTracker 衝突檢測（因已在檔案層級處理）
- **THEN** ManifestTracker 仍 SHALL 記錄該 skill 的 hash（用於孤兒清理等功能）

### Requirement: Clone command distributes skills to tool directories
The clone command SHALL distribute skills/commands/agents/workflows from source repositories to all target tool directories (Claude, OpenCode, Gemini, Codex, Antigravity), NOT clone git repositories.

#### Scenario: Normal skill distribution
- **WHEN** user runs `ai-dev clone`
- **THEN** system copies all skills/commands/agents/workflows from source repos to each target's directory

#### Scenario: Developer mode detection
- **WHEN** user runs `ai-dev clone` from within the custom-skills project directory
- **THEN** system detects developer mode and uses symlinks instead of copies

#### Scenario: Force overwrite
- **WHEN** user runs `ai-dev clone --force`
- **THEN** system overwrites existing files without prompting

#### Scenario: Skip conflicts
- **WHEN** user runs `ai-dev clone --skip-conflicts`
- **THEN** system skips files that already exist in target directories

#### Scenario: Backup before overwrite
- **WHEN** user runs `ai-dev clone --backup`
- **THEN** system creates backup of existing files before overwriting

#### Scenario: Metadata change detection
- **WHEN** source files have different metadata (timestamps, content hash) than target
- **THEN** system reports which files were updated and which were unchanged

#### Scenario: Sync project option
- **WHEN** user runs `ai-dev clone --sync-project`
- **THEN** system also syncs project-template files to the current project

## REMOVED Requirements

### Requirement: 開發者模式整合 ECC 來源

**Reason**: ECC 內容改由 clone 分發流程直接從 `~/.config/everything-claude-code/` 處理，不再需要將 ECC 整合進開發目錄。`integrate_to_dev_project()` 的 ECC 段落（`shared.py:1561-1598`）應移除。

**Migration**: ECC 的 skills/agents/commands 由 `ai-dev clone` 的 ECC 選擇性分發階段處理，直接分發到目標目錄。開發者不再需要在 repo 內維護 `sources/ecc/` 目錄。

## MODIFIED Requirements

### Requirement: Clone Command (分發指令)

CLI MUST (必須) 提供 `clone` 子命令，將 `~/.config/custom-skills` 內容分發到各工具目錄。

> **變更說明**：分發流程新增檢查 CWD 的 `.ai-dev-project.yaml`。當同步到專案目錄時，跳過由 init-from 模板管理的檔案。

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

#### Scenario: Skip files managed by init-from in project sync

- **WHEN** `ai-dev clone` syncs to the current project directory
- **THEN** the system SHALL check for `.ai-dev-project.yaml` in CWD
- **THEN** if the tracking file exists, the system SHALL skip files listed in `managed_files`
- **THEN** the system SHALL display "  ~ Skipped .claude/commands/tdd.md (managed by qdm-ai-base)" for each skipped file

#### Scenario: No tracking file — default behavior

- **WHEN** `ai-dev clone` runs in a directory without `.ai-dev-project.yaml`
- **THEN** the system SHALL proceed with normal distribution behavior (no files skipped)

#### Scenario: Global directory distribution unaffected

- **WHEN** `ai-dev clone` distributes to global directories (`~/.claude/`, `~/.gemini/`, etc.)
- **THEN** the system SHALL NOT check `.ai-dev-project.yaml`
- **THEN** global distribution SHALL proceed unchanged regardless of project tracking

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

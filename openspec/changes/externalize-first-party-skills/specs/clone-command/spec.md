## MODIFIED Requirements

### Requirement: Clone Command (分發指令)

CLI MUST (必須) 提供 `clone` 子命令，將 `~/.config/custom-skills` 中仍由 framework 管理的 commands、agents、workflows、plugins，以及 custom repos 與 ECC 白名單資源分發到各工具目錄。`clone` SHALL NOT 從 `~/.config/custom-skills/skills/` 分發第一方 npx-managed skills。

#### Scenario: 基本分發流程（使用者模式）

給定 `~/.config/custom-skills/` 目錄由 git repo 控制
當執行 `ai-dev clone` 時
則應該：
1. 直接執行 Stage 3（分發仍由 framework 管理的資源）
2. 不執行 Stage 2（不整合外部來源到 custom-skills）
3. 不複製第一方 npx-managed skills
4. 讀取 `upstream/distribution.yaml` 執行 ECC 選擇性分發
5. 顯示分發的目標與結果

#### Scenario: 分發順序

- **WHEN** 執行 `ai-dev clone`
- **THEN** 分發順序 SHALL 為：
  1. custom-skills 本身的 commands、agents、workflows 與 plugins
  2. custom repos（repos.yaml 中的自訂 repo）
  3. ECC 選擇性分發（distribution.yaml 定義的規則）
- **THEN** 第一方 npx-managed skills SHALL 不出現在此順序中

#### Scenario: 分發目標

給定執行 `ai-dev clone` 時
則應該依仍由 clone 管理的資源分發到以下目錄：
- Claude Code: `~/.claude/commands/`, `~/.claude/agents/`, `~/.claude/workflows/`，以及 custom repo／ECC 的 skills 目錄
- OpenCode: `~/.config/opencode/commands/`, `~/.config/opencode/agents/`, `~/.config/opencode/plugins/`，以及 custom repo／ECC 的 skills 目錄
- Antigravity: `~/.gemini/antigravity/global_workflows/`，以及 custom repo／ECC 的 skills 目錄
- Codex 與 agy: 只在 custom repo 或 ECC 有啟用 skill 時處理其 skills 目錄
- 第一方 skills 的 agent 目標路徑 SHALL 由 `npx skills` 決定，clone SHALL 不直接寫入

#### Scenario: Skip files managed by init-from in project sync

- **WHEN** `ai-dev clone` syncs to the current project directory
- **THEN** the system SHALL check for `.ai-dev-project.yaml` in CWD
- **THEN** if the tracking file exists, the system SHALL skip files listed in `managed_files`
- **THEN** the system SHALL display "  ~ Skipped .claude/commands/tdd.md (managed by shared-template)" for each skipped file

#### Scenario: No tracking file — default behavior

- **WHEN** `ai-dev clone` runs in a directory without `.ai-dev-project.yaml`
- **THEN** the system SHALL proceed with normal distribution behavior (no files skipped)

#### Scenario: Global directory distribution unaffected

- **WHEN** `ai-dev clone` distributes retained resources to global directories
- **THEN** the system SHALL NOT check `.ai-dev-project.yaml`
- **THEN** retained resource distribution SHALL proceed regardless of project tracking
- **THEN** first-party npx-managed skills SHALL remain excluded

#### Scenario: 含 .clonepolicy.json 的 skill 使用逐檔複製

- **WHEN** custom repo 或 ECC 的非 npx-managed skill 目錄包含 `.clonepolicy.json`
- **THEN** 系統 SHALL 不使用 `shutil.copytree`
- **THEN** 系統 SHALL 改用逐檔遍歷，依 `.clonepolicy.json` 中的 rules 決定每個檔案的處理策略
- **THEN** 目錄結構 SHALL 在目標自動建立（保持來源的子目錄結構）

#### Scenario: 無 .clonepolicy.json 的 skill 行為不變

- **WHEN** custom repo 或 ECC 的非 npx-managed skill 目錄不包含 `.clonepolicy.json`
- **THEN** 系統 SHALL 維持原有逐目錄分發行為

#### Scenario: 含 policy 的 skill 跳過目錄層級衝突檢測

- **WHEN** custom repo 或 ECC 的非 npx-managed skill 目錄包含 `.clonepolicy.json`
- **THEN** 該 skill SHALL 不參與目錄層級的 ManifestTracker 衝突檢測（因已在檔案層級處理）
- **THEN** ManifestTracker 仍 SHALL 記錄該 skill 的 hash（用於孤兒清理等功能）

#### Scenario: 第一方 skill 來源目錄存在

- **WHEN** 遷移期間 `~/.config/custom-skills/skills/` 尚未刪除
- **THEN** clone SHALL 依 npx-managed canonical ID 清單排除第一方 skills
- **THEN** 不得因舊來源仍存在而重新取得 manifest ownership

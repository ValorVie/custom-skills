## MODIFIED Requirements

### Requirement: Clone Command (分發指令)

CLI MUST (必須) 提供 `clone` 子命令，將 `~/.config/custom-skills` 內容分發到各工具目錄。

> **變更說明**：當 skill 目錄包含 `.clonepolicy.json` 時，改用逐檔複製並依策略處理，取代原有的整個目錄 `copytree`。

#### Scenario: 基本分發流程（使用者模式）

給定 `~/.config/custom-skills/` 目錄由 git repo 控制
當執行 `ai-dev clone` 時
則應該：
1. 直接執行 Stage 3（分發到各工具目錄）
2. 不執行 Stage 2（不整合外部來源到 custom-skills）
3. 顯示分發的目標與結果

#### Scenario: 分發目標

給定執行 `ai-dev clone` 時
則應該分發到以下目錄：
- Claude Code: `~/.claude/skills/`, `~/.claude/commands/`, `~/.claude/agents/`, `~/.claude/workflows/`
- OpenCode: `~/.config/opencode/skills/`, `~/.config/opencode/commands/`, `~/.config/opencode/agents/`, `~/.config/opencode/plugins/`
- Gemini CLI: `~/.gemini/skills/`, `~/.gemini/commands/`
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

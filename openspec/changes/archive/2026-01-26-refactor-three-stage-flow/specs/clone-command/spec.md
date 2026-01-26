## MODIFIED Requirements

### Requirement: Clone Command (分發指令)

CLI MUST (必須) 提供 `clone` 子命令，將 `~/.config/custom-skills` 內容分發到各工具目錄。

> **變更說明**：移除自動 Stage 2 整合，新增開發者模式整合功能。

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
- OpenCode: `~/.config/opencode/skills/`, `~/.config/opencode/commands/`, `~/.config/opencode/agents/`
- Gemini CLI: `~/.gemini/skills/`, `~/.gemini/commands/`
- Codex: `~/.codex/skills/`
- Antigravity: `~/.gemini/antigravity/global_skills/`, `~/.gemini/antigravity/global_workflows/`

#### Scenario: 開發者模式 - 整合外部來源到開發目錄

給定使用者位於 custom-skills 開發目錄（非 `~/.config/custom-skills`）
且該目錄的 `pyproject.toml` 包含 `name = "ai-dev"`
當執行 `ai-dev clone --sync-project` 時
則應該：
1. 將外部來源整合到當前開發目錄：
   - UDS skills, agents, workflows, commands
   - Obsidian skills
   - Anthropic skill-creator
   - ECC skills, agents, commands（從 sources/ecc）
2. 然後從 `~/.config/custom-skills` 分發到各工具目錄

#### Scenario: 開發目錄提示

給定使用者位於 custom-skills 開發目錄（非 `~/.config/custom-skills`）
當執行 `ai-dev clone` 且未使用 `--sync-project` 時
則應該顯示提示訊息建議使用 `--sync-project` 來整合外部來源

#### Scenario: 在 ~/.config/custom-skills 執行時跳過整合

給定使用者位於 `~/.config/custom-skills` 目錄
當執行 `ai-dev clone --sync-project` 時
則應該：
1. 跳過整合步驟（因為這是分發目錄本身）
2. 只執行 Stage 3 分發

#### Scenario: 無來源目錄時的錯誤處理

給定 `~/.config/custom-skills/` 目錄不存在
當執行 `ai-dev clone` 時
則應該：
1. 顯示錯誤訊息指出來源目錄不存在
2. 建議先執行 `ai-dev install` 或 `ai-dev update`

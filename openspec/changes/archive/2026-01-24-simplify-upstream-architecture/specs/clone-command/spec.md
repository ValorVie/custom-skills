# clone-command Specification

## Purpose

提供 `ai-dev clone` 指令，將 `~/.config/custom-skills` 的內容分發到各 AI 工具的配置目錄。

## ADDED Requirements

### Requirement: Clone Command (分發指令)

CLI MUST (必須) 提供 `clone` 子命令，將 custom-skills 內容分發到各工具目錄。

#### Scenario: 基本分發流程

給定 `~/.config/custom-skills/` 目錄存在且包含 skills
當執行 `ai-dev clone` 時
則應該：
1. 執行 Stage 2（整合外部來源到 custom-skills）
2. 執行 Stage 3（分發到各工具目錄）
3. 顯示分發的目標與結果

#### Scenario: 分發目標

給定執行 `ai-dev clone` 時
則應該分發到以下目錄：
- Claude Code: `~/.claude/skills/`, `~/.claude/commands/`, `~/.claude/agents/`
- OpenCode: `~/.config/opencode/skills/`, `~/.config/opencode/agents/`
- Gemini CLI: `~/.gemini/skills/`
- Codex: `~/.codex/skills/`
- Antigravity: `~/.gemini/antigravity/global_skills/`

#### Scenario: 同步到專案目錄選項

給定使用者位於 custom-skills 專案目錄
當執行 `ai-dev clone --sync-project` 時
則應該額外同步到當前專案目錄

當執行 `ai-dev clone --no-sync-project` 時
則應該跳過專案目錄同步

#### Scenario: 無來源目錄時的錯誤處理

給定 `~/.config/custom-skills/` 目錄不存在
當執行 `ai-dev clone` 時
則應該：
1. 顯示錯誤訊息指出來源目錄不存在
2. 建議先執行 `ai-dev install` 或 `ai-dev update`

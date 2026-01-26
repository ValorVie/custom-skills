## MODIFIED Requirements

### Requirement: Three-Stage Copy Flow (三階段複製流程)

腳本 MUST (必須) 使用簡化的分發流程來管理資源分發。

> **變更說明**：移除 Stage 2（整合到 custom-skills），`~/.config/custom-skills` 內容完全由 git repo 控制。
> Stage 2 的整合功能已移至開發者模式，透過 `ai-dev clone --sync-project` 在開發目錄執行。

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

#### Scenario: Stage 3 - 分發到目標目錄

給定 `~/.config/custom-skills/` 由 git repo 控制
當執行 `ai-dev clone` 時
則應該複製到所有目標目錄：
- Claude Code: `~/.claude/skills`, `~/.claude/commands`, `~/.claude/agents`, `~/.claude/workflows`
- Antigravity: `~/.gemini/antigravity/global_skills`, `~/.gemini/antigravity/global_workflows`
- OpenCode: `~/.config/opencode/skills`, `~/.config/opencode/commands`, `~/.config/opencode/agents`
- Codex: `~/.codex/skills`
- Gemini CLI: `~/.gemini/skills`, `~/.gemini/commands`

#### Scenario: 不再自動執行 Stage 2 整合

給定使用者執行 `ai-dev clone`
當分發流程執行時
則不應該自動將外部來源（UDS, Obsidian, Anthropic）整合到 `~/.config/custom-skills`
且 `~/.config/custom-skills` 的內容應由 git repo 控制

## ADDED Requirements

### Requirement: 專案層級 npx skills 餵給 agy 的 agent

`ai-dev` 的專案層級 skill 同步（`_NPX_PROJECT_AGENTS`，透過外部 `npx skills` 工具）MUST 使用 `gemini-cli` 這個 npx agent 來餵給 Antigravity CLI (agy)，因為其路徑（project `.agents/skills/`、global `~/.gemini/skills/`）正是 agy 讀取的 skills 目錄。在 `npx skills` 提供 `agy`／`antigravity-cli` agent 之前，MUST NOT 將此 agent 改名為 `agy`。

#### Scenario: 保留 gemini-cli npx agent

給定 `npx skills` 目前版本未提供 `agy` agent
當 `ai-dev` 進行專案層級 npx skill 同步時
則 `_NPX_PROJECT_AGENTS` MUST 包含 `gemini-cli`
且 MUST NOT 以 `agy` 取代之

#### Scenario: 不以 antigravity agent 取代

給定 `npx skills` 的 `antigravity` agent 全域路徑為 `~/.gemini/antigravity/skills/`（agy 不讀取的位置）
當決定 agy 的全域 skill 來源 agent 時
則 MUST 使用 global 路徑為 `~/.gemini/skills/` 的 `gemini-cli` agent，而非 `antigravity` agent

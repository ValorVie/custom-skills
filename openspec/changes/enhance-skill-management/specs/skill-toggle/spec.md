# skill-toggle Specification

## Purpose
提供使用者針對特定工具（Claude Code、Antigravity、OpenCode）啟用或停用特定資源的能力。

## ADDED Requirements

### Requirement: Toggle Config File (開關配置檔)
腳本 MUST (必須) 支援 YAML 格式的開關配置檔來控制資源的啟用狀態。

#### Scenario: 配置檔不存在時使用預設值
給定 `~/.config/custom-skills/toggle-config.yaml` 不存在
當執行 `copy_skills()` 時
則應該使用預設值（全部啟用）並繼續複製。

#### Scenario: 讀取配置檔
給定 `~/.config/custom-skills/toggle-config.yaml` 存在
當執行 `copy_skills()` 時
則應該：
1. 讀取配置檔內容
2. 根據各工具的設定決定是否複製
3. 排除被停用的資源

### Requirement: Toggle Command (開關指令)
腳本 MUST (必須) 實作 `toggle` 指令以管理資源的啟用狀態。

#### Scenario: 停用特定 Skill
給定使用者執行 `uv run script/main.py toggle --target claude --type skills --name commit-standards --disable`
當指令完成時
則應該：
1. 更新 `toggle-config.yaml` 中 `claude.skills.disabled` 列表
2. 重新執行 `copy_skills()` 以套用變更
3. 顯示操作結果

#### Scenario: 啟用已停用的 Skill
給定 `commit-standards` 已在 `claude.skills.disabled` 列表中
當使用者執行 `uv run script/main.py toggle --target claude --type skills --name commit-standards --enable`
則應該：
1. 從 `disabled` 列表中移除該項目
2. 重新執行 `copy_skills()` 以套用變更
3. 顯示操作結果

#### Scenario: 列出目前的開關狀態
給定使用者執行 `uv run script/main.py toggle --list`
當指令完成時
則應該顯示所有工具的啟用/停用狀態表格。

### Requirement: Target Tool Support (目標工具支援)
腳本 MUST (必須) 支援以下目標工具：

| Target | Skills 路徑 | Commands/Workflows 路徑 | Agents 路徑 |
|--------|------------|------------------------|------------|
| claude | ~/.claude/skills/ | ~/.claude/commands/ | N/A |
| antigravity | ~/.gemini/antigravity/skills/ | ~/.gemini/antigravity/global_workflows/ | N/A |
| opencode | (讀取 ~/.claude/skills/) | N/A | ~/.config/opencode/agent/ |

#### Scenario: OpenCode 使用 Claude Skills 路徑
給定使用者停用 Claude 的某個 skill
當 OpenCode 讀取 skills 時
則該 skill 也會被停用（因為 OpenCode 預設讀取 Claude 路徑）。

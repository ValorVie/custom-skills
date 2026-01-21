# Proposal: add-codex-gemini-cli-targets

## Why

目前 `ai-dev` 工具僅支援 Claude Code、Antigravity 和 OpenCode 三種 AI 工具的 skills/commands/agents 管理。
使用者希望新增對 **OpenAI Codex CLI** 和 **Gemini CLI** 的支援，這兩個工具有各自的 skills 和 commands 目錄：

- **OpenAI Codex CLI**: `~/.codex/skills`
- **Gemini CLI**: `~/.gemini/skills` 和 `~/.gemini/commands`

新增這些目標可讓使用者統一管理所有主流 AI CLI 工具的配置。

## What Changes

### 新增兩個目標工具

1. **Codex** (`codex`)
   - Skills: `~/.codex/skills`
   - 僅支援 skills（目前 Codex CLI 不支援 commands）

2. **Gemini CLI** (`gemini`)
   - Skills: `~/.gemini/skills`
   - Commands: `~/.gemini/commands`
   - 注意：與 Antigravity（`~/.gemini/antigravity/`）不同，這是 Gemini CLI 原生目錄

### 受影響的檔案

| 檔案 | 變更內容 |
|------|----------|
| `script/utils/paths.py` | 新增 `get_codex_config_dir()` 和 `get_gemini_cli_config_dir()` |
| `script/utils/shared.py` | 更新 `TargetType`、`get_target_path()`、`copy_skills()`、`list_installed_resources()` |
| `script/commands/toggle.py` | 新增 codex/gemini 支援 |
| `script/commands/list.py` | 新增 codex/gemini 的列表支援 |
| `script/tui/app.py` | 更新 `TARGET_OPTIONS` 和 `TYPE_OPTIONS_BY_TARGET` |
| `README.md` | 更新支援的工具清單 |

### 複製策略

Skills 複製流程將新增：
- UDS + Obsidian + Anthropic → Codex Skills (`~/.codex/skills`)
- UDS + Obsidian + Anthropic → Gemini CLI Skills (`~/.gemini/skills`)
- Custom Commands → Gemini CLI Commands (`~/.gemini/commands`)

## Related Specs

- `setup-script`: 安裝與更新邏輯
- `skill-listing`: list 指令
- `skill-toggle`: toggle 指令
- `skill-tui`: TUI 介面

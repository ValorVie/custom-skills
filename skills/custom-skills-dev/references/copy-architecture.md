# Copy Architecture Reference

Detailed documentation for the three-stage copy flow.

## Table of Contents

- [Overview](#overview)
- [Stage 1: Clone](#stage-1-clone)
- [Stage 2: Integrate](#stage-2-integrate)
- [Stage 3: Distribute](#stage-3-distribute)
- [Implementation Files](#implementation-files)

---

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Stage 1: Clone                           │
├─────────────────────────────────────────────────────────────────┤
│  GitHub Repos                                                   │
│  ├── universal-dev-standards  ──→  ~/.config/universal-dev-standards/
│  ├── obsidian-skills          ──→  ~/.config/obsidian-skills/   │
│  ├── anthropic-skills         ──→  ~/.config/anthropic-skills/  │
│  ├── superpowers              ──→  ~/.config/superpowers/       │
│  └── everything-claude-code   ──→  ~/.config/everything-claude-code/
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Stage 2: Integrate                             │
├─────────────────────────────────────────────────────────────────┤
│  ~/.config/custom-skills/                                       │
│  ├── skills/        ←── UDS skills + Obsidian + Anthropic       │
│  ├── commands/                                                  │
│  │   ├── claude/    ←── UDS commands                            │
│  │   └── workflows/ ←── UDS workflows                           │
│  └── agents/                                                    │
│      ├── claude/    ←── UDS agents                              │
│      └── opencode/  ←── UDS agents                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Stage 3: Distribute                          │
├─────────────────────────────────────────────────────────────────┤
│  Claude Code    ──→  ~/.claude/{skills,commands,agents,workflows}
│  Antigravity    ──→  ~/.gemini/antigravity/{global_skills,global_workflows}
│  OpenCode       ──→  ~/.config/opencode/{skills,commands,agents}│
│  Codex          ──→  ~/.agents/skills/                           │
│  Gemini CLI     ──→  ~/.gemini/{skills,commands}                │
└─────────────────────────────────────────────────────────────────┘
```

Codex 與其他支援 Agent Skills 標準的工具共用 `~/.agents/skills`。只有 Skills
共用；Codex 的設定、agents、hooks、prompts、認證與 sessions 仍在 `.codex`。
舊版 `~/.codex/skills` 由 install、update、clone 的前置遷移處理：先備份，
再搬移缺項或移除相同副本，內容衝突則保留原狀、寫入 audit 並停止。

`auto-skill` 已退役。`clone` 只保留確認式舊安裝清理，不再建立 canonical state 或 shadow；歷史內容見 `archive/auto-skill/`。

---

## Stage 1: Clone

External Git repositories cloned to `~/.config/`.

### Source Repositories

| Name | Repository | Local Path |
|------|------------|------------|
| custom-skills | ValorVie/custom-skills | `~/.config/custom-skills/` |
| universal-dev-standards | AsiaOstrich/universal-dev-standards | `~/.config/universal-dev-standards/` |
| obsidian-skills | kepano/obsidian-skills | `~/.config/obsidian-skills/` |
| anthropic-skills | anthropics/skills | `~/.config/anthropic-skills/` |
| superpowers | obra/superpowers | `~/.config/superpowers/` |
| everything-claude-code | affaan-m/everything-claude-code | `~/.config/everything-claude-code/` |

### Implementation

- Triggered by: `ai-dev install` or `ai-dev update`
- Code: `script/commands/install.py`, `script/commands/update.py`
- Uses `git clone` for new repos, `git fetch && git reset` for updates

---

## Stage 2: Integrate

Merge resources from multiple sources into `~/.config/custom-skills/`.

### Source Mapping

| Source | From | To |
|--------|------|-----|
| UDS skills | `~/.config/universal-dev-standards/skills/claude-code/*` | `~/.config/custom-skills/skills/` |
| UDS agents | `~/.config/universal-dev-standards/skills/claude-code/agents/` | `~/.config/custom-skills/agents/claude/` |
| UDS workflows | `~/.config/universal-dev-standards/skills/claude-code/workflows/` | `~/.config/custom-skills/commands/workflows/` |
| UDS commands | `~/.config/universal-dev-standards/skills/claude-code/commands/` | `~/.config/custom-skills/commands/claude/` |
| Obsidian skills | `~/.config/obsidian-skills/skills/` | `~/.config/custom-skills/skills/` |
| Anthropic skill-creator | `~/.config/anthropic-skills/skills/skill-creator/` | `~/.config/custom-skills/skills/skill-creator/` |

### Implementation

- Code: `script/utils/shared.py`
- Notes:
  - 一般 Skills 整合進 `~/.config/custom-skills/`

---

## Stage 3: Distribute

Copy from `~/.config/custom-skills/` to each AI tool's directory.

### Distribution Mapping

| Source | Target Tool | Target Path |
|--------|-------------|-------------|
| `skills/` | Claude Code | `~/.claude/skills/` |
| `skills/` | Antigravity | `~/.gemini/antigravity/global_skills/` |
| `skills/` | OpenCode | `~/.config/opencode/skills/` |
| `skills/` | Codex | `~/.agents/skills/` |
| `skills/` | Gemini CLI | `~/.gemini/skills/` |
| `commands/claude/` | Claude Code | `~/.claude/commands/` |
| `commands/antigravity/` | Antigravity | `~/.gemini/antigravity/global_workflows/` |
| `commands/opencode/` | OpenCode | `~/.config/opencode/commands/` |
| `commands/gemini/` | Gemini CLI | `~/.gemini/commands/` |
| `commands/workflows/` | Claude Code | `~/.claude/workflows/` |
| `agents/claude/` | Claude Code | `~/.claude/agents/` |
| `agents/opencode/` | OpenCode | `~/.config/opencode/agents/` |

### Implementation

- Code: `script/utils/shared.py`
- Notes:
  - Skills 使用 copy/clone-policy 流程；`auto-skill` 名稱由退役保護規則排除。

---

## Implementation Files

| File | Purpose |
|------|---------|
| `script/utils/paths.py` | Path resolution functions |
| `script/utils/shared.py` | Copy logic, source/target configurations |
| `script/utils/legacy_auto_skill_cleanup.py` | 已退役 auto-skill 的偵測、備份與確認式清理 |
| `script/commands/install.py` | First-time installation flow |
| `script/commands/update.py` | Update flow |
| `script/commands/clone.py` | Manual distribution trigger |

### Key Functions

```python
# script/utils/shared.py

# Stage 2 sources configuration
STAGE2_SOURCES = [
    {"source": "~/.config/universal-dev-standards/skills/claude-code/*", ...},
    ...
]

# Stage 3 targets configuration
STAGE3_TARGETS = [
    {"source": "skills/", "tool": "claude", "target": "~/.claude/skills/"},
    ...
]

# Copy functions
def copy_skills_stage2(): ...
def copy_skills_stage3(): ...
```

---

## Modifying Copy Logic

### Adding a New Source (Stage 2)

1. Edit `script/utils/shared.py`
2. Add entry to `STAGE2_SOURCES`
3. Test with `ai-dev update`

### Adding a New Target Tool (Stage 3)

1. Edit `script/utils/shared.py`
2. Add entries to `STAGE3_TARGETS`
3. Update `script/utils/paths.py` if new path functions needed
4. Update TUI in `script/tui/app.py`
5. Test with `ai-dev clone`

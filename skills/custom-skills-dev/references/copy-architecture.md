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
│  auto-skill canonical state                                     │
│  `~/.config/ai-dev/skills/auto-skill`                           │
│   ←── template + upstream merge                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Stage 3: Distribute                          │
├─────────────────────────────────────────────────────────────────┤
│  Claude Code    ──→  ~/.claude/{skills,commands,agents,workflows}
│  Antigravity    ──→  ~/.gemini/antigravity/{global_skills,global_workflows}
│  OpenCode       ──→  ~/.config/opencode/{skills,commands,agents}│
│  Codex          ──→  ~/.codex/skills/                           │
│  Gemini CLI     ──→  ~/.gemini/{skills,commands}                │
└─────────────────────────────────────────────────────────────────┘
```

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
| auto-skill state | `~/.config/custom-skills/skills/auto-skill/` + `~/.config/auto-skill/` | `~/.config/ai-dev/skills/auto-skill/` |

### Implementation

- Code: `script/utils/shared.py`, `script/utils/auto_skill_state.py`
- Notes:
  - 一般 Skills 仍整合進 `~/.config/custom-skills/`
  - `auto-skill` 例外，改同步到 canonical state `~/.config/ai-dev/skills/auto-skill`

---

## Stage 3: Distribute

Copy from `~/.config/custom-skills/` to each AI tool's directory.

### Distribution Mapping

| Source | Target Tool | Target Path |
|--------|-------------|-------------|
| `skills/` | Claude Code | `~/.claude/skills/` |
| `skills/` | Antigravity | `~/.gemini/antigravity/global_skills/` |
| `skills/` | OpenCode | `~/.config/opencode/skills/` |
| `skills/` | Codex | `~/.codex/skills/` |
| `skills/` | Gemini CLI | `~/.gemini/skills/` |
| `commands/claude/` | Claude Code | `~/.claude/commands/` |
| `commands/antigravity/` | Antigravity | `~/.gemini/antigravity/global_workflows/` |
| `commands/opencode/` | OpenCode | `~/.config/opencode/commands/` |
| `commands/gemini/` | Gemini CLI | `~/.gemini/commands/` |
| `commands/workflows/` | Claude Code | `~/.claude/workflows/` |
| `agents/claude/` | Claude Code | `~/.claude/agents/` |
| `agents/opencode/` | OpenCode | `~/.config/opencode/agents/` |

### Implementation

- Code: `script/utils/shared.py`, `script/utils/auto_skill_projection.py`
- Notes:
  - 一般 Skills 仍使用 copy/clone-policy 流程
  - `auto-skill` 例外，從 canonical state 投影到各工具目錄
  - 預設使用 `symlink`；Windows 優先 `junction`；失敗 fallback `copy`

---

## Implementation Files

| File | Purpose |
|------|---------|
| `script/utils/paths.py` | Path resolution functions |
| `script/utils/shared.py` | Copy logic, source/target configurations |
| `script/utils/auto_skill_state.py` | auto-skill canonical state refresh |
| `script/utils/auto_skill_projection.py` | auto-skill projection helper |
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

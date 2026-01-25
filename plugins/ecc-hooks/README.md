# ECC Hooks Plugin

Everything Claude Code - Memory Persistence & Strategic Compact Hooks

## Features

- **SessionStart**: Load previous context and detect package manager on new session
- **SessionEnd**: Persist session state and evaluate for extractable patterns
- **PreCompact**: Save state before context compaction
- **PreToolUse**:
  - Block dev servers outside tmux
  - Reminder for long-running commands
  - Git push review reminder
  - Strategic compact suggestions
- **PostToolUse**: Log PR URL after creation
- **Stop**: Check for console.log in modified files

## Installation

### 方式 1：本地開發測試（最簡單）

直接載入本地 plugin 進行測試，無需推送到 GitHub：

```bash
claude --plugin-dir "/path/to/custom-skills/plugins/ecc-hooks"
```

### 方式 2：從 Git URL 安裝

1. 先添加 marketplace：

```bash
claude plugin marketplace add https://github.com/ValorVie/custom-skills.git
```

2. 然後安裝 plugin：

```bash
claude plugin install ecc-hooks@custom-skills
```

### 方式 3：在 Claude Code 會話中使用 slash command

```
/plugin install ecc-hooks@custom-skills
```

### 方式 4：指定完整來源路徑

```bash
/plugin install ecc-hooks --source https://github.com/ValorVie/custom-skills.git --path plugins/ecc-hooks
```

## Structure

```
ecc-hooks/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   └── hooks.json
├── scripts/
│   ├── utils.py
│   ├── memory-persistence/
│   │   ├── session-start.py
│   │   ├── session-end.py
│   │   ├── pre-compact.py
│   │   └── evaluate-session.py
│   └── strategic-compact/
│       └── suggest-compact.py
└── README.md
```

## License

MIT

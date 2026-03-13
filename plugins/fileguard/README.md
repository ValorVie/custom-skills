# FileGuard

Path-based access control plugin for Claude Code. Blocks AI from accessing specified files and directories via PreToolUse hooks.

## Features

- Firewall-style rules (first-match-wins)
- Deny/allow mixed rules
- Covers Read, Write, Edit, Grep, Glob, Bash
- Hardcoded self-protection (AI cannot disable the guard)
- `.disable-fileguard` flag for manual bypass

## Installation

This plugin is part of the custom-skills package. It is automatically installed when custom-skills is configured.

## Configuration

Edit `fileguard-rules.json` in the plugin directory:

```json
{
  "rules": [
    {
      "action": "allow",
      "pattern": "/Users/arlen/.config/claude",
      "type": "directory",
      "reason": "Claude config is safe to access"
    },
    {
      "action": "deny",
      "pattern": "/Users/arlen/.config",
      "type": "directory",
      "reason": "Config root"
    },
    {
      "action": "deny",
      "pattern": "/Users/arlen/.ssh",
      "type": "directory",
      "reason": "SSH private keys"
    },
    {
      "action": "deny",
      "pattern": "\\.env($|\\.)",
      "type": "regex",
      "reason": "Environment secrets"
    },
    {
      "action": "deny",
      "pattern": "\\.pem$",
      "type": "regex",
      "reason": "Certificate private keys"
    }
  ],
  "default": "allow"
}
```

### Rule Fields

| Field | Description |
|-------|-------------|
| `action` | `deny` or `allow` |
| `pattern` | Path string or regex |
| `type` | `directory` (prefix match), `file` (exact match), `regex` (regex match) |
| `reason` | Displayed when access is denied |
| `default` | Action when no rule matches: `allow` or `deny` |

### Matching Model

**Firewall model (first-match-wins):** Rules are evaluated in array order. The first matching rule determines the result. If no rule matches, `default` is applied.

This means **rule order matters**. Place more specific rules (like allows for subdirectories) before broader rules (like denying the parent directory).

### Matching by Tool Type

**Read, Write, Edit** — `file_path` is normalized via `realpath` (resolves `../`, symlinks) and lowercased before matching:
- `directory` → `path.startswith(pattern)`
- `file` → `path == pattern`
- `regex` → `re.search(pattern, path)`

**Grep, Glob** — `path` field is used (falls back to `cwd` if empty), same normalization as above.

**Bash** — `command` string is matched directly (no path normalization, case-insensitive):
- `directory` → substring search
- `file` → substring search
- `regex` → `re.search(pattern, command, re.IGNORECASE)`

## Disabling FileGuard

Create `.disable-fileguard` in the project directory to temporarily disable all checks:

```bash
touch .disable-fileguard    # Disable FileGuard
rm .disable-fileguard       # Re-enable protection
```

**Important:** `.disable-fileguard` itself is protected by hardcoded rules. AI cannot create, delete, or read this file. Only human operators can toggle it via their terminal.

## Hardcoded Protection

The following are always protected, regardless of rules:

- `.disable-fileguard` — prevents AI from toggling the guard
- The entire FileGuard plugin directory (`${CLAUDE_PLUGIN_ROOT}`) — prevents AI from modifying the guard's code, hooks, or rules

## Known Limitations

### Bash Interception Boundaries

**Can intercept** (path appears as plain text in command string):
- `cat /secret/file.txt`
- `cat $(echo /secret/file.txt)`
- `cd /secret && ls`
- `grep "keyword" /secret/file`
- `cp /secret/a.txt /tmp/`
- `echo "data" > /secret/file`
- `cat "/my secret/file"` (quoted paths)

**Cannot intercept** (path not visible as plain text):
- Variable indirection: `p="/secret"; cat $p`
- File-sourced paths: `cat $(head -1 paths.txt)`
- Encoded bypass: `echo L3NlY3JldA== | base64 -d | xargs cat`
- Environment variables: `cat $SECRET_PATH`
- Eval concatenation: `eval "cat /sec" + "ret/file"`
- Wildcard expansion: `cat /sec*/file` (if rule is full path `/secret`)

### Other Limitations

- **python3 required**: If python3 is not installed, hooks fail silently and all access is allowed.
- **Symlinks in Bash**: Symlink paths in command strings cannot be resolved. Only string matching applies.
- **Agent subagents**: Agent's prompt cannot be inspected for paths, but subagent tool calls (Read/Write etc.) still trigger hooks.
- **MCP tools**: Not intercepted in this version. Each MCP tool has a different input schema.
- **Hot reload**: Changes to `hooks.json` require restarting Claude Code.
- **Rules file missing**: If `fileguard-rules.json` is missing or has invalid JSON, all access is denied. Use `touch .disable-fileguard` to bypass.

<!--
Upstream: everything-claude-code
Source URL: https://github.com/anthropics/everything-claude-code
Synced Date: 2026-01-24
License: MIT
-->

# MCP Server Configurations

Model Context Protocol (MCP) servers extend Claude Code with additional tools and integrations.

## Usage

Copy the servers you need from `mcp-servers.json` to your Claude Code settings:

### macOS/Linux
```bash
~/.claude.json
```

### Windows
```bash
%USERPROFILE%\.claude.json
```

## Example Configuration

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxxx"
      }
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"]
    }
  }
}
```

## Available Servers

### Development
| Server | Description |
|--------|-------------|
| `github` | GitHub operations - PRs, issues, repos |
| `supabase` | Supabase database operations |
| `context7` | Live documentation lookup |

### Cloud Platforms
| Server | Description |
|--------|-------------|
| `vercel` | Vercel deployments and projects |
| `railway` | Railway deployments |
| `cloudflare-*` | Cloudflare Workers, docs, observability |
| `clickhouse` | ClickHouse analytics queries |

### Utilities
| Server | Description |
|--------|-------------|
| `memory` | Persistent memory across sessions |
| `sequential-thinking` | Chain-of-thought reasoning |
| `filesystem` | Filesystem operations |
| `firecrawl` | Web scraping and crawling |

## Best Practices

1. **Keep Under 10 MCPs** - Too many MCPs consume context window
2. **Use Project-Specific Config** - Disable unneeded MCPs per project
3. **Secure Your Tokens** - Never commit tokens to git
4. **Check Compatibility** - Some MCPs may conflict

## Disabling Per-Project

Create `.claude.json` in your project root:

```json
{
  "disabledMcpServers": ["clickhouse", "railway"]
}
```

## Environment Variables

Replace placeholder values in `mcp-servers.json`:

| Placeholder | Description |
|-------------|-------------|
| `YOUR_GITHUB_PAT_HERE` | GitHub Personal Access Token |
| `YOUR_FIRECRAWL_KEY_HERE` | Firecrawl API Key |
| `YOUR_PROJECT_REF` | Supabase Project Reference |

## Troubleshooting

### Server Not Starting
```bash
# Check if npx can run the package
npx -y @modelcontextprotocol/server-github --help
```

### Permission Issues
```bash
# Ensure tokens have correct scopes
# GitHub: repo, read:org, read:user
```

### Context Window Issues
- Reduce number of enabled MCPs
- Use project-specific disabling

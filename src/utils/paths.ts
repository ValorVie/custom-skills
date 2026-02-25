import { homedir } from "node:os";
import { join } from "node:path";

const home = homedir();
const config = join(home, ".config");
const claudeConfig = join(home, ".claude");
const opencodeConfig = join(config, "opencode");

export const paths = {
  home,
  config,
  customSkills: join(config, "custom-skills"),
  aiDevConfig: join(config, "ai-dev"),
  syncConfig: join(config, "ai-dev", "sync.yaml"),
  syncRepo: join(config, "ai-dev", "sync-repo"),
  claudeConfig,
  claudeSkills: join(claudeConfig, "skills"),
  claudeCommands: join(claudeConfig, "commands"),
  claudeAgents: join(claudeConfig, "agents"),
  claudeWorkflows: join(claudeConfig, "workflows"),
  antigravityConfig: join(home, ".gemini", "antigravity"),
  opencodeConfig,
  opencodeSkills: join(opencodeConfig, "skills"),
  opencodeCommands: join(opencodeConfig, "commands"),
  opencodeAgents: join(opencodeConfig, "agents"),
  opencodePlugins: join(opencodeConfig, "plugins"),
  opencodeSuperpowers: join(opencodeConfig, "superpowers"),
  codexConfig: join(home, ".codex"),
  codexSkills: join(home, ".codex", "skills"),
  geminiConfig: join(home, ".gemini"),
  geminiSkills: join(home, ".gemini", "skills"),
  geminiCommands: join(home, ".gemini", "commands"),
  geminiAgents: join(home, ".gemini", "agents"),
  superpowersRepo: join(config, "superpowers"),
  udsRepo: join(config, "universal-dev-standards"),
  obsidianSkillsRepo: join(config, "obsidian-skills"),
  anthropicSkillsRepo: join(config, "anthropic-skills"),
  everythingClaudeCodeRepo: join(config, "everything-claude-code"),
  autoSkillRepo: join(config, "auto-skill"),
  projectRoot: process.cwd(),
} as const;

export type Paths = typeof paths;

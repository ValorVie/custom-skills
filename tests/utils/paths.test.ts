import { describe, expect, test } from "bun:test";
import { homedir } from "node:os";
import { isAbsolute, join } from "node:path";

import { paths } from "../../src/utils/paths";

const home = homedir();
const config = join(home, ".config");
const claudeConfig = join(home, ".claude");
const opencodeConfig = join(config, "opencode");

describe("utils/paths", () => {
  test("all paths are absolute", () => {
    for (const [key, value] of Object.entries(paths)) {
      if (key === "projectRoot") continue;
      expect(isAbsolute(value), `paths.${key} should be absolute`).toBe(true);
    }
  });

  test("projectRoot equals process.cwd()", () => {
    expect(paths.projectRoot).toBe(process.cwd());
  });

  describe("exact path values", () => {
    const expected: Record<string, string> = {
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
    };

    for (const [key, expectedValue] of Object.entries(expected)) {
      test(`paths.${key}`, () => {
        expect((paths as Record<string, string>)[key]).toBe(expectedValue);
      });
    }
  });

  test("home-based paths start with homedir()", () => {
    const homeBased = [
      "home",
      "claudeConfig",
      "claudeSkills",
      "claudeCommands",
      "claudeAgents",
      "claudeWorkflows",
      "antigravityConfig",
      "codexConfig",
      "codexSkills",
      "geminiConfig",
      "geminiSkills",
      "geminiCommands",
      "geminiAgents",
    ] as const;

    for (const key of homeBased) {
      expect(
        paths[key].startsWith(home),
        `paths.${key} should start with homedir()`,
      ).toBe(true);
    }
  });

  test("config-based paths start with homedir()/.config", () => {
    const configBased = [
      "config",
      "customSkills",
      "aiDevConfig",
      "syncConfig",
      "syncRepo",
      "opencodeConfig",
      "opencodeSkills",
      "opencodeCommands",
      "opencodeAgents",
      "opencodePlugins",
      "opencodeSuperpowers",
      "superpowersRepo",
      "udsRepo",
      "obsidianSkillsRepo",
      "anthropicSkillsRepo",
      "everythingClaudeCodeRepo",
      "autoSkillRepo",
    ] as const;

    for (const key of configBased) {
      expect(
        paths[key].startsWith(config),
        `paths.${key} should start with .config`,
      ).toBe(true);
    }
  });
});

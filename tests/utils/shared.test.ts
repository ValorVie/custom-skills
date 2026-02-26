import { describe, expect, test } from "bun:test";
import { homedir } from "node:os";
import { join } from "node:path";

import { paths } from "../../src/utils/paths";
import {
  BUN_PACKAGES,
  COPY_TARGETS,
  NPM_PACKAGES,
  REPOS,
} from "../../src/utils/shared";

const home = homedir();
const config = join(home, ".config");

describe("utils/shared", () => {
  describe("NPM_PACKAGES", () => {
    test("is a non-empty string array", () => {
      expect(NPM_PACKAGES.length).toBeGreaterThan(0);
      for (const pkg of NPM_PACKAGES) {
        expect(typeof pkg).toBe("string");
        expect(pkg.length).toBeGreaterThan(0);
      }
    });

    test("includes expected packages", () => {
      expect(NPM_PACKAGES).toContain("@fission-ai/openspec@latest");
      expect(NPM_PACKAGES).toContain("@google/gemini-cli");
      expect(NPM_PACKAGES).toContain("universal-dev-standards");
    });
  });

  describe("BUN_PACKAGES", () => {
    test("is a non-empty string array", () => {
      expect(BUN_PACKAGES.length).toBeGreaterThan(0);
      for (const pkg of BUN_PACKAGES) {
        expect(typeof pkg).toBe("string");
        expect(pkg.length).toBeGreaterThan(0);
      }
    });

    test("includes codex", () => {
      expect(BUN_PACKAGES).toContain("@openai/codex");
    });
  });

  describe("REPOS", () => {
    test("all repos have dir starting with config path", () => {
      for (const repo of REPOS) {
        expect(
          repo.dir.startsWith(config),
          `${repo.name} dir should start with .config`,
        ).toBe(true);
      }
    });

    test("all repos have valid GitHub URL", () => {
      for (const repo of REPOS) {
        expect(
          repo.url.startsWith("https://github.com/"),
          `${repo.name} url should be GitHub`,
        ).toBe(true);
        expect(
          repo.url.endsWith(".git"),
          `${repo.name} url should end with .git`,
        ).toBe(true);
      }
    });

    test("all repos have non-empty name", () => {
      for (const repo of REPOS) {
        expect(repo.name.length).toBeGreaterThan(0);
      }
    });

    test("repo dirs match paths.*", () => {
      const repoByName: Record<string, string> = {};
      for (const repo of REPOS) {
        repoByName[repo.name] = repo.dir;
      }
      expect(repoByName["custom-skills"]).toBe(paths.customSkills);
      expect(repoByName["superpowers"]).toBe(paths.superpowersRepo);
      expect(repoByName["uds"]).toBe(paths.udsRepo);
      expect(repoByName["obsidian-skills"]).toBe(paths.obsidianSkillsRepo);
      expect(repoByName["anthropic-skills"]).toBe(paths.anthropicSkillsRepo);
      expect(repoByName["everything-claude-code"]).toBe(
        paths.everythingClaudeCodeRepo,
      );
      expect(repoByName["auto-skill"]).toBe(paths.autoSkillRepo);
    });
  });

  describe("COPY_TARGETS", () => {
    test("claude target paths match paths.*", () => {
      expect(COPY_TARGETS.claude.skills).toBe(paths.claudeSkills);
      expect(COPY_TARGETS.claude.commands).toBe(paths.claudeCommands);
      expect(COPY_TARGETS.claude.agents).toBe(paths.claudeAgents);
      expect(COPY_TARGETS.claude.workflows).toBe(paths.claudeWorkflows);
    });

    test("antigravity target paths match paths.*", () => {
      expect(COPY_TARGETS.antigravity.skills).toBe(
        `${paths.antigravityConfig}/global_skills`,
      );
      expect(COPY_TARGETS.antigravity.workflows).toBe(
        `${paths.antigravityConfig}/global_workflows`,
      );
    });

    test("opencode target paths match paths.*", () => {
      expect(COPY_TARGETS.opencode.skills).toBe(paths.opencodeSkills);
      expect(COPY_TARGETS.opencode.commands).toBe(paths.opencodeCommands);
      expect(COPY_TARGETS.opencode.agents).toBe(paths.opencodeAgents);
      expect(COPY_TARGETS.opencode.plugins).toBe(paths.opencodePlugins);
    });

    test("codex target paths match paths.*", () => {
      expect(COPY_TARGETS.codex.skills).toBe(paths.codexSkills);
    });

    test("gemini target paths match paths.*", () => {
      expect(COPY_TARGETS.gemini.skills).toBe(paths.geminiSkills);
      expect(COPY_TARGETS.gemini.commands).toBe(paths.geminiCommands);
      expect(COPY_TARGETS.gemini.agents).toBe(paths.geminiAgents);
    });
  });
});

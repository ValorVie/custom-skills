import { describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { runInstall } from "../../src/core/installer";
import { BUN_PACKAGES, NPM_PACKAGES, REPOS } from "../../src/utils/shared";
import type { RunCommandOptions } from "../../src/utils/system";

describe("core/installer", () => {
  test("runInstall returns structured result", async () => {
    const result = await runInstall({
      skipNpm: true,
      skipBun: true,
      skipRepos: true,
    });

    expect(result).toHaveProperty("prerequisites");
    expect(result).toHaveProperty("npmPackages");
    expect(result).toHaveProperty("bunPackages");
    expect(result).toHaveProperty("repos");
    expect(result).toHaveProperty("errors");
  });

  test("runInstall respects skip options", async () => {
    const result = await runInstall({
      skipNpm: true,
      skipBun: true,
      skipRepos: true,
    });

    expect(result.npmPackages.length).toBe(0);
    expect(result.bunPackages.length).toBe(0);
    expect(result.repos.length).toBe(0);
  });

  test("runInstall reports missing prerequisites when PATH is unavailable", async () => {
    const result = await runInstall({
      skipNpm: false,
      skipBun: false,
      skipRepos: false,
      deps: {
        commandExistsFn: () => false,
      },
    });

    expect(result.prerequisites.node).toBe(false);
    expect(result.prerequisites.git).toBe(false);
    expect(result.prerequisites.bun).toBe(false);
    expect(result.errors).toContain("Node.js is required");
    expect(result.errors).toContain("Git is required");
    expect(result.errors).toContain(
      "Bun is not installed; skipped Bun package installation",
    );
    expect(result.npmPackages.length).toBe(0);
    expect(result.bunPackages.length).toBe(0);
    expect(result.repos.length).toBe(0);
  });

  test("runInstall handles mixed install outcomes", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-installer-"));
    const existingRepo = join(root, "existing-repo");
    const cloneRepo = join(root, "clone-repo");

    try {
      await mkdir(join(existingRepo, ".git"), { recursive: true });

      const result = await runInstall({
        deps: {
          commandExistsFn: () => true,
          getBunVersionFn: async () => "1.3.0",
          npmPackages: ["npm-a"],
          bunPackages: ["bun-a"],
          repos: [
            {
              name: "existing-repo",
              url: "https://example.com/existing.git",
              dir: existingRepo,
            },
            {
              name: "clone-repo",
              url: "https://example.com/clone.git",
              dir: cloneRepo,
            },
          ],
          runCommandFn: async (command: string[]) => {
            if (command[0] === "npm") {
              return { stdout: "", stderr: "npm failed", exitCode: 1 };
            }
            if (command[0] === "bun") {
              return { stdout: "", stderr: "", exitCode: 0 };
            }
            if (command[0] === "git" && command[1] === "clone") {
              return { stdout: "", stderr: "", exitCode: 0 };
            }
            return { stdout: "", stderr: "", exitCode: 0 };
          },
        },
      });

      expect(result.npmPackages).toEqual([
        { name: "npm-a", success: false, message: "npm failed", version: null },
      ]);
      expect(result.bunPackages).toEqual([
        { name: "bun-a", success: true, message: undefined },
      ]);
      expect(result.repos).toEqual([
        { name: "existing-repo", success: true, message: "already cloned" },
        { name: "clone-repo", success: true, message: undefined },
      ]);
      expect(result.errors.length).toBe(0);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("runInstall passes timeoutMs to runCommandFn", async () => {
    const calls: { command: string[]; options: RunCommandOptions }[] = [];
    const root = await mkdtemp(join(tmpdir(), "ai-dev-installer-timeout-"));
    const repoDir = join(root, "repo");

    try {
      const result = await runInstall({
        deps: {
          commandExistsFn: () => true,
          getBunVersionFn: async () => "1.3.0",
          npmPackages: ["test-npm"],
          bunPackages: ["test-bun"],
          repos: [
            {
              name: "test-repo",
              url: "https://example.com/test.git",
              dir: repoDir,
            },
          ],
          runCommandFn: async (
            command: string[],
            options: RunCommandOptions = {},
          ) => {
            calls.push({ command, options });
            return { stdout: "", stderr: "", exitCode: 0 };
          },
        },
      });

      expect(result.errors.length).toBe(0);

      const npmCall = calls.find(
        (c) => c.command[0] === "npm" && c.command[1] === "install",
      );
      expect(npmCall).toBeDefined();
      expect(npmCall?.options.timeoutMs).toBe(60_000);

      const bunCall = calls.find((c) => c.command[0] === "bun");
      expect(bunCall).toBeDefined();
      expect(bunCall?.options.timeoutMs).toBe(60_000);

      const gitCall = calls.find(
        (c) => c.command[0] === "git" && c.command[1] === "clone",
      );
      expect(gitCall).toBeDefined();
      expect(gitCall?.options.timeoutMs).toBe(120_000);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("runInstall includes prerequisite details and gh check", async () => {
    const result = await runInstall({
      skipNpm: true,
      skipBun: true,
      skipRepos: true,
      deps: {
        commandExistsFn: (command: string) => command === "node",
        runCommandFn: async (command: string[]) => {
          if (command[0] === "node") {
            return { stdout: "v20.1.0\n", stderr: "", exitCode: 0 };
          }
          return { stdout: "", stderr: "", exitCode: 0 };
        },
      },
    });

    expect(result.prerequisites.node).toBe(true);
    expect(result.prerequisites.git).toBe(false);
    expect(result.prerequisites.gh).toBe(false);
    expect(result.prerequisiteDetails.node.hint).toContain("Node.js");
    expect(result.errors).toContain("GitHub CLI (gh) is required");
  });

  test("runInstall supports custom repos and skill distribution", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-installer-custom-"));
    const customRepoDir = join(root, "custom-repo");

    try {
      const result = await runInstall({
        skipNpm: true,
        skipBun: true,
        deps: {
          commandExistsFn: () => true,
          repos: [],
          loadCustomReposFn: async () => ({
            repos: {
              custom: {
                url: "https://example.com/custom.git",
                branch: "main",
                localPath: customRepoDir,
                addedAt: new Date().toISOString(),
              },
            },
          }),
          distributeSkillsFn: async () => ({
            distributed: [
              {
                name: "alpha",
                target: "claude",
                type: "skills",
              },
            ],
            conflicts: [
              {
                name: "beta",
                target: "claude",
                type: "skills",
                sources: ["/tmp/source", "/tmp/destination"],
              },
            ],
            errors: [],
            unchanged: 0,
          }),
          runCommandFn: async (command: string[]) => {
            if (command[0] === "git" && command[1] === "clone") {
              await mkdir(join(command[3] as string, ".git"), {
                recursive: true,
              });
            }
            return { stdout: "", stderr: "", exitCode: 0 };
          },
        },
      });

      expect(result.customRepos).toEqual([
        { name: "custom", success: true, message: undefined },
      ]);
      expect(result.skills.installed).toEqual(["alpha"]);
      expect(result.skills.conflicts).toEqual(["beta"]);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("runInstall respects skipSkills option", async () => {
    let distributionCalled = false;

    const result = await runInstall({
      skipNpm: true,
      skipBun: true,
      skipRepos: true,
      skipSkills: true,
      deps: {
        commandExistsFn: () => true,
        distributeSkillsFn: async () => {
          distributionCalled = true;
          return {
            distributed: [],
            conflicts: [],
            errors: [],
            unchanged: 0,
          };
        },
      },
    });

    expect(distributionCalled).toBe(false);
    expect(result.skills.installed.length).toBe(0);
  });

  test("runInstall surfaces Claude Code npm installation warning", async () => {
    const progress: string[] = [];

    const result = await runInstall({
      skipNpm: true,
      skipBun: true,
      skipRepos: true,
      skipSkills: true,
      deps: {
        commandExistsFn: (command: string) =>
          command === "claude" || command === "npm",
        runCommandFn: async (command: string[]) => {
          if (command[0] === "npm" && command[1] === "list") {
            return {
              stdout: "@anthropic-ai/claude-code@1.0.0",
              stderr: "",
              exitCode: 0,
            };
          }

          if (command[0] === "claude" && command[1] === "--version") {
            return { stdout: "2.2.0\n", stderr: "", exitCode: 0 };
          }

          return { stdout: "", stderr: "", exitCode: 0 };
        },
      },
      onProgress: (message) => {
        progress.push(message);
      },
    });

    expect(result.claudeCode.installed).toBe(true);
    expect(result.claudeCode.version).toBe("2.2.0");
    expect(progress.some((line) => line.includes("npm"))).toBe(true);
  });
});

describe("installer default constants", () => {
  test("NPM_PACKAGES is a non-empty array of strings", () => {
    expect(NPM_PACKAGES.length).toBeGreaterThan(0);
    for (const pkg of NPM_PACKAGES) {
      expect(typeof pkg).toBe("string");
    }
  });

  test("BUN_PACKAGES is a non-empty array of strings", () => {
    expect(BUN_PACKAGES.length).toBeGreaterThan(0);
    for (const pkg of BUN_PACKAGES) {
      expect(typeof pkg).toBe("string");
    }
  });

  test("REPOS is a non-empty array with valid structure", () => {
    expect(REPOS.length).toBeGreaterThan(0);
    for (const repo of REPOS) {
      expect(typeof repo.name).toBe("string");
      expect(typeof repo.url).toBe("string");
      expect(typeof repo.dir).toBe("string");
      expect(repo.url.startsWith("https://")).toBe(true);
    }
  });
});

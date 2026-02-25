import { describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { runInstall } from "../../src/core/installer";
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
        { name: "npm-a", success: false, message: "npm failed" },
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

      const npmCall = calls.find((c) => c.command[0] === "npm");
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
});

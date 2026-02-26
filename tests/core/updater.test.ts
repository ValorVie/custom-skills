import { describe, expect, test } from "bun:test";
import type { PathLike } from "node:fs";

import { runUpdate } from "../../src/core/updater";
import { BUN_PACKAGES, NPM_PACKAGES, REPOS } from "../../src/utils/shared";
import type { RunCommandOptions } from "../../src/utils/system";

describe("core/updater", () => {
  test("runUpdate respects skip options", async () => {
    const result = await runUpdate({
      skipNpm: true,
      skipBun: true,
      skipRepos: true,
      skipPlugins: true,
      deps: {
        commandExistsFn: () => true,
        runCommandFn: async () => ({
          stdout: "",
          stderr: "",
          exitCode: 0,
        }),
      },
    });

    expect(result.npmPackages.length).toBe(0);
    expect(result.bunPackages.length).toBe(0);
    expect(result.repos.length).toBe(0);
    expect(result.errors.length).toBe(0);
  });

  test("runUpdate reports missing npm and bun when commands are unavailable", async () => {
    const result = await runUpdate({
      skipRepos: true,
      skipPlugins: true,
      deps: {
        commandExistsFn: () => false,
        runCommandFn: async () => ({
          stdout: "",
          stderr: "",
          exitCode: 0,
        }),
      },
    });

    expect(result.errors).toContain("npm is not installed");
    expect(result.errors).toContain("bun is not installed");
    expect(result.npmPackages.length).toBe(0);
    expect(result.bunPackages.length).toBe(0);
    expect(result.repos.length).toBe(0);
  });

  test("runUpdate handles mixed update outcomes", async () => {
    const result = await runUpdate({
      skipPlugins: true,
      deps: {
        commandExistsFn: () => true,
        npmPackages: ["npm-a"],
        bunPackages: ["bun-a"],
        repos: [
          {
            name: "repo-found",
            url: "https://example.com/repo-found.git",
            dir: "/tmp/repo-found",
          },
          {
            name: "repo-missing",
            url: "https://example.com/repo-missing.git",
            dir: "/tmp/repo-missing",
          },
        ],
        accessFn: async (path: PathLike) => {
          if (String(path).includes("repo-found")) {
            return;
          }
          throw new Error("not found");
        },
        runCommandFn: async (command: string[]) => {
          if (command[0] === "claude") {
            return { stdout: "", stderr: "", exitCode: 0 };
          }
          if (command[0] === "uds") {
            return { stdout: "", stderr: "", exitCode: 0 };
          }
          if (command[0] === "npx" && command[1] === "skills") {
            return { stdout: "", stderr: "", exitCode: 0 };
          }
          if (command[0] === "npm") {
            return { stdout: "", stderr: "", exitCode: 0 };
          }
          if (command[0] === "bun") {
            return { stdout: "", stderr: "bun failed", exitCode: 1 };
          }
          if (command[0] === "git") {
            return { stdout: "", stderr: "", exitCode: 0 };
          }
          return { stdout: "", stderr: "", exitCode: 1 };
        },
      },
    });

    expect(result.npmPackages).toEqual([
      { name: "npm-a", success: true, message: undefined },
    ]);
    expect(result.bunPackages).toEqual([
      { name: "bun-a", success: false, message: "bun failed" },
    ]);
    expect(result.repos).toEqual([
      { name: "repo-found", success: true, message: undefined },
      { name: "repo-missing", success: false, message: "repository not found" },
    ]);
    expect(result.summary.upToDate).toEqual(["repo-found"]);
    expect(result.summary.missing).toEqual(["repo-missing"]);
    expect(result.errors).toContain("bun failed");
    expect(result.errors).toContain("repository not found");
  });

  test("runUpdate passes timeoutMs to runCommandFn", async () => {
    const calls: { command: string[]; options: RunCommandOptions }[] = [];

    const result = await runUpdate({
      skipPlugins: true,
      deps: {
        commandExistsFn: () => true,
        npmPackages: ["test-npm"],
        bunPackages: ["test-bun"],
        repos: [
          {
            name: "test-repo",
            url: "https://example.com/test.git",
            dir: "/tmp/test-repo",
          },
        ],
        accessFn: async () => {},
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

    const gitCall = calls.find((c) => c.command[0] === "git");
    expect(gitCall).toBeDefined();
    expect(gitCall?.options.timeoutMs).toBe(60_000);
  });

  test("runUpdate backs up local changes before reset", async () => {
    let backupCalled = false;

    const result = await runUpdate({
      skipNpm: true,
      skipBun: true,
      skipPlugins: true,
      deps: {
        commandExistsFn: () => true,
        repos: [
          {
            name: "repo-a",
            url: "https://example.com/repo-a.git",
            dir: "/tmp/repo-a",
          },
        ],
        accessFn: async () => {},
        hasLocalChangesFn: async () => true,
        backupDirtyFilesFn: async () => {
          backupCalled = true;
          return "/tmp/backup";
        },
        runCommandFn: async (command: string[]) => {
          if (command[0] === "uds") {
            return { stdout: "", stderr: "", exitCode: 0 };
          }
          if (command[0] === "npx" && command[1] === "skills") {
            return { stdout: "", stderr: "", exitCode: 0 };
          }
          if (
            command[0] === "git" &&
            command[command.length - 1].startsWith("HEAD...")
          ) {
            return { stdout: "0 1\n", stderr: "", exitCode: 0 };
          }
          return { stdout: "", stderr: "", exitCode: 0 };
        },
      },
    });

    expect(backupCalled).toBe(true);
    expect(result.repos[0]?.success).toBe(true);
  });

  test("runUpdate supports skipping plugin marketplace update", async () => {
    const calls: string[][] = [];

    await runUpdate({
      skipNpm: true,
      skipBun: true,
      skipRepos: true,
      skipPlugins: true,
      deps: {
        commandExistsFn: () => true,
        runCommandFn: async (command: string[]) => {
          calls.push(command);
          return { stdout: "", stderr: "", exitCode: 0 };
        },
      },
    });

    expect(
      calls.some(
        (command) =>
          command[0] === "claude" &&
          command[1] === "plugin" &&
          command[2] === "marketplace",
      ),
    ).toBe(false);
  });

  test("runUpdate reports not installed when Claude Code is missing", async () => {
    const result = await runUpdate({
      skipNpm: true,
      skipBun: true,
      skipRepos: true,
      skipPlugins: true,
      deps: {
        commandExistsFn: () => false,
        runCommandFn: async () => ({
          stdout: "",
          stderr: "",
          exitCode: 0,
        }),
      },
    });

    expect(result.claudeCode.success).toBe(false);
    expect(result.claudeCode.message).toBe("not installed");
  });
});

describe("updater default constants", () => {
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

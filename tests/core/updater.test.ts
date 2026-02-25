import { describe, expect, test } from "bun:test";
import type { PathLike } from "node:fs";

import { runUpdate } from "../../src/core/updater";
import type { RunCommandOptions } from "../../src/utils/system";

describe("core/updater", () => {
  test("runUpdate respects skip options", async () => {
    const result = await runUpdate({
      skipNpm: true,
      skipBun: true,
      skipRepos: true,
    });

    expect(result.npmPackages.length).toBe(0);
    expect(result.bunPackages.length).toBe(0);
    expect(result.repos.length).toBe(0);
    expect(result.errors.length).toBe(0);
  });

  test("runUpdate reports missing npm and bun when commands are unavailable", async () => {
    const result = await runUpdate({
      skipRepos: true,
      deps: {
        commandExistsFn: () => false,
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
    expect(result.errors.length).toBe(0);
  });

  test("runUpdate passes timeoutMs to runCommandFn", async () => {
    const calls: { command: string[]; options: RunCommandOptions }[] = [];

    const result = await runUpdate({
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

    const npmCall = calls.find((c) => c.command[0] === "npm");
    expect(npmCall).toBeDefined();
    expect(npmCall?.options.timeoutMs).toBe(60_000);

    const bunCall = calls.find((c) => c.command[0] === "bun");
    expect(bunCall).toBeDefined();
    expect(bunCall?.options.timeoutMs).toBe(60_000);

    const gitCall = calls.find((c) => c.command[0] === "git");
    expect(gitCall).toBeDefined();
    expect(gitCall?.options.timeoutMs).toBe(60_000);
  });
});

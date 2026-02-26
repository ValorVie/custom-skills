import { describe, expect, test } from "bun:test";

import { updateCustomRepos } from "../../src/core/custom-repo-updater";

describe("core/custom-repo-updater", () => {
  test("updateCustomRepos reports missing repositories", async () => {
    const result = await updateCustomRepos({
      deps: {
        loadCustomReposFn: async () => ({
          repos: {
            missing: {
              url: "https://example.com/missing.git",
              branch: "main",
              localPath: "/tmp/missing",
              addedAt: new Date().toISOString(),
            },
          },
        }),
        accessFn: async () => {
          throw new Error("missing");
        },
        runCommandFn: async () => ({ stdout: "", stderr: "", exitCode: 0 }),
        hasLocalChangesFn: async () => false,
        backupDirtyFilesFn: async () => "/tmp/backup",
      },
    });

    expect(result.summary.missing).toEqual(["missing"]);
    expect(result.items[0]?.success).toBe(false);
  });

  test("updateCustomRepos uses fetch + reset and marks updated repos", async () => {
    const calls: string[][] = [];
    let backupCalled = false;

    const result = await updateCustomRepos({
      deps: {
        loadCustomReposFn: async () => ({
          repos: {
            repoA: {
              url: "https://example.com/repoA.git",
              branch: "main",
              localPath: "/tmp/repoA",
              addedAt: new Date().toISOString(),
            },
          },
        }),
        accessFn: async () => {},
        hasLocalChangesFn: async () => true,
        backupDirtyFilesFn: async () => {
          backupCalled = true;
          return "/tmp/backup";
        },
        runCommandFn: async (command: string[]) => {
          calls.push(command);
          if (command.includes("rev-list")) {
            return { stdout: "0 2\n", stderr: "", exitCode: 0 };
          }
          return { stdout: "", stderr: "", exitCode: 0 };
        },
      },
    });

    expect(backupCalled).toBe(true);
    expect(result.summary.updated).toEqual(["repoA"]);
    expect(
      calls.some(
        (command) =>
          command[0] === "git" &&
          command.includes("fetch") &&
          command.includes("--all"),
      ),
    ).toBe(true);
    expect(
      calls.some(
        (command) =>
          command[0] === "git" &&
          command.includes("reset") &&
          command.includes("--hard"),
      ),
    ).toBe(true);
  });
});

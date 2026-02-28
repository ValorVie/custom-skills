import { describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { SyncEngine } from "../../src/core/sync-engine";

function isGitPushCommand(command: string[]): boolean {
  return command[0] === "git" && command.includes("push");
}

function isGitPullRebaseCommand(command: string[]): boolean {
  return (
    command[0] === "git" &&
    command.includes("pull") &&
    command.includes("--rebase")
  );
}

function isGitLfsPushCommand(command: string[]): boolean {
  return (
    command[0] === "git" &&
    command.includes("lfs") &&
    command.includes("push")
  );
}

describe("core/sync-engine push parity", () => {
  test("push with force requires explicit confirmation", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-push-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "local");
    const calls: string[][] = [];
    let confirmCalls = 0;

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        calls.push(command);
        return { stdout: "", stderr: "", exitCode: 0 };
      },
      confirmForcePushFn: async () => {
        confirmCalls += 1;
        return false;
      },
    });

    try {
      await mkdir(localDir, { recursive: true });
      await writeFile(join(localDir, "a.txt"), "hello\n", "utf8");
      await engine.init();
      await engine.removeDirectory("~/.claude", { skipMinCheck: true });
      await engine.addDirectory(localDir);

      calls.length = 0;
      await engine.push({ force: true });

      expect(confirmCalls).toBe(1);
      expect(calls.some(isGitPushCommand)).toBe(false);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("push returns early when no changes and force=false", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-push-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "local");
    const calls: string[][] = [];

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        calls.push(command);
        if (command.includes("status")) {
          return {
            stdout: "",
            stderr: "",
            exitCode: 0,
          };
        }
        if (command.includes("commit")) {
          return {
            stdout: "",
            stderr: "nothing to commit, working tree clean",
            exitCode: 1,
          };
        }
        return { stdout: "", stderr: "", exitCode: 0 };
      },
    });

    try {
      await mkdir(localDir, { recursive: true });
      await engine.init();
      await engine.removeDirectory("~/.claude", { skipMinCheck: true });
      await engine.addDirectory(localDir);

      calls.length = 0;
      const summary = await engine.push({ force: false });

      expect(summary).toEqual(
        expect.objectContaining({ added: 0, updated: 0, deleted: 0 }),
      );
      expect(summary.git?.status?.command).toEqual(
        expect.arrayContaining(["git", "status", "--porcelain"]),
      );
      expect(calls.some(isGitPullRebaseCommand)).toBe(false);
      expect(calls.some(isGitPushCommand)).toBe(false);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("push with force skips pull and can continue when commit has no changes", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-push-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "local");
    const calls: string[][] = [];

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        calls.push(command);
        if (command.includes("commit")) {
          return {
            stdout: "",
            stderr: "nothing to commit, working tree clean",
            exitCode: 1,
          };
        }
        return { stdout: "", stderr: "", exitCode: 0 };
      },
      confirmForcePushFn: async () => true,
    });

    try {
      await mkdir(localDir, { recursive: true });
      await writeFile(join(localDir, "a.txt"), "hello\n", "utf8");
      await engine.init();
      await engine.removeDirectory("~/.claude", { skipMinCheck: true });
      await engine.addDirectory(localDir);

      await expect(engine.push({ force: true })).resolves.toEqual(
        expect.objectContaining({
          added: 1,
          updated: 1,
        }),
      );
      expect(calls.some(isGitPullRebaseCommand)).toBe(false);
      expect(calls.some(isGitPushCommand)).toBe(true);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("push throws when git pull --rebase fails", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-push-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "local");
    const calls: string[][] = [];

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        calls.push(command);
        if (command.includes("status")) {
          return { stdout: " M a.txt\n", stderr: "", exitCode: 0 };
        }
        if (isGitPullRebaseCommand(command)) {
          return {
            stdout: "",
            stderr: "cannot rebase: local changes would be overwritten",
            exitCode: 1,
          };
        }
        return { stdout: "", stderr: "", exitCode: 0 };
      },
    });

    try {
      await mkdir(localDir, { recursive: true });
      await writeFile(join(localDir, "a.txt"), "hello\n", "utf8");
      await engine.init();
      await engine.removeDirectory("~/.claude", { skipMinCheck: true });
      await engine.addDirectory(localDir);

      await expect(engine.push()).rejects.toThrow("git pull --rebase 失敗");
      expect(calls.some(isGitPullRebaseCommand)).toBe(true);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("push stages and commits before pull to avoid dirty-tree pull failure", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-push-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "local");
    const calls: string[][] = [];
    let added = false;
    let committed = false;

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        calls.push(command);

        if (command.includes("status")) {
          return { stdout: " M a.txt\n", stderr: "", exitCode: 0 };
        }

        if (command.includes("add") && command.includes("-A")) {
          added = true;
          return { stdout: "", stderr: "", exitCode: 0 };
        }

        if (command.includes("commit")) {
          if (!added) {
            return { stdout: "", stderr: "add not called", exitCode: 1 };
          }
          committed = true;
          return { stdout: "", stderr: "", exitCode: 0 };
        }

        if (isGitPullRebaseCommand(command)) {
          if (!committed) {
            return {
              stdout: "",
              stderr: "cannot pull with rebase: You have unstaged changes.",
              exitCode: 1,
            };
          }
          return { stdout: "Already up to date.\n", stderr: "", exitCode: 0 };
        }

        return { stdout: "", stderr: "", exitCode: 0 };
      },
    });

    try {
      await mkdir(localDir, { recursive: true });
      await writeFile(join(localDir, "a.txt"), "hello\n", "utf8");
      await engine.init();
      await engine.removeDirectory("~/.claude", { skipMinCheck: true });
      await engine.addDirectory(localDir);

      await expect(engine.push()).resolves.toEqual(
        expect.objectContaining({
          added: 1,
          updated: 1,
        }),
      );

      const addIndex = calls.findIndex(
        (command) => command[0] === "git" && command.includes("add"),
      );
      const commitIndex = calls.findIndex(
        (command) => command[0] === "git" && command.includes("commit"),
      );
      const pullIndex = calls.findIndex(isGitPullRebaseCommand);

      expect(addIndex).toBeGreaterThanOrEqual(0);
      expect(commitIndex).toBeGreaterThan(addIndex);
      expect(pullIndex).toBeGreaterThan(commitIndex);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("push throws when git commit fails unexpectedly", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-push-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "local");

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        if (command.includes("status")) {
          return { stdout: " M a.txt\n", stderr: "", exitCode: 0 };
        }
        if (isGitPullRebaseCommand(command)) {
          return { stdout: "", stderr: "", exitCode: 0 };
        }
        if (command.includes("commit")) {
          return {
            stdout: "",
            stderr: "fatal: failed to write commit object",
            exitCode: 1,
          };
        }
        return { stdout: "", stderr: "", exitCode: 0 };
      },
    });

    try {
      await mkdir(localDir, { recursive: true });
      await writeFile(join(localDir, "a.txt"), "hello\n", "utf8");
      await engine.init();
      await engine.removeDirectory("~/.claude", { skipMinCheck: true });
      await engine.addDirectory(localDir);

      await expect(engine.push()).rejects.toThrow("git commit 失敗");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("push throws when git push fails", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-push-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "local");

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        if (command.includes("status")) {
          return { stdout: " M a.txt\n", stderr: "", exitCode: 0 };
        }
        if (isGitPullRebaseCommand(command)) {
          return { stdout: "", stderr: "", exitCode: 0 };
        }
        if (isGitPushCommand(command)) {
          return {
            stdout: "",
            stderr: "fatal: unable to access remote repository",
            exitCode: 1,
          };
        }
        return { stdout: "", stderr: "", exitCode: 0 };
      },
    });

    try {
      await mkdir(localDir, { recursive: true });
      await writeFile(join(localDir, "a.txt"), "hello\n", "utf8");
      await engine.init();
      await engine.removeDirectory("~/.claude", { skipMinCheck: true });
      await engine.addDirectory(localDir);

      await expect(engine.push()).rejects.toThrow("git push 失敗");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("push throws when git lfs push fails", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-push-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "local");

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        if (command.includes("status")) {
          return { stdout: " M a.txt\n", stderr: "", exitCode: 0 };
        }
        if (isGitPullRebaseCommand(command)) {
          return { stdout: "", stderr: "", exitCode: 0 };
        }
        if (isGitLfsPushCommand(command)) {
          return {
            stdout: "",
            stderr: "batch response: permission denied",
            exitCode: 1,
          };
        }
        return { stdout: "", stderr: "", exitCode: 0 };
      },
    });

    try {
      await mkdir(localDir, { recursive: true });
      await writeFile(join(localDir, "a.txt"), "hello\n", "utf8");
      await engine.init();
      await engine.removeDirectory("~/.claude", { skipMinCheck: true });
      await engine.addDirectory(localDir);

      await expect(engine.push()).rejects.toThrow("git lfs push 失敗");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("push preserves git command outputs in summary details", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-push-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "local");

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        if (command.includes("status")) {
          return { stdout: " M a.txt\n", stderr: "", exitCode: 0 };
        }
        if (isGitPullRebaseCommand(command)) {
          return { stdout: "Already up to date.\n", stderr: "", exitCode: 0 };
        }
        if (isGitLfsPushCommand(command)) {
          return {
            stdout: "",
            stderr: "Uploading LFS objects: 100% (1/1), 1 KB\n",
            exitCode: 0,
          };
        }
        if (isGitPushCommand(command)) {
          return {
            stdout: "To https://example.com/repo.git\n",
            stderr: "   abc123..def456  main -> main\n",
            exitCode: 0,
          };
        }
        return { stdout: "", stderr: "", exitCode: 0 };
      },
    });

    try {
      await mkdir(localDir, { recursive: true });
      await writeFile(join(localDir, "a.txt"), "hello\n", "utf8");
      await engine.init();
      await engine.removeDirectory("~/.claude", { skipMinCheck: true });
      await engine.addDirectory(localDir);

      const summary = await engine.push();
      expect(summary.git?.push?.stdout).toContain("To https://example.com/repo.git");
      expect(summary.git?.push?.stderr).toContain("main -> main");
      expect(summary.git?.pull?.stdout).toContain("Already up to date.");
      expect(summary.git?.lfsPush?.stderr).toContain("Uploading LFS objects");
      expect(summary.git?.push?.command).toEqual(
        expect.arrayContaining(["git", "push"]),
      );
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});

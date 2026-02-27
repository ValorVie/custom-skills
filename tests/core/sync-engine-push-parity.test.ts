import { describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { SyncEngine } from "../../src/core/sync-engine";

function isGitPushCommand(command: string[]): boolean {
  return command[0] === "git" && command.includes("push");
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
      await engine.init("https://example.com/repo.git");
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
    });

    try {
      await engine.init("https://example.com/repo.git");

      calls.length = 0;
      const summary = await engine.push({ force: false });

      expect(summary).toEqual({ added: 0, updated: 0, deleted: 0 });
      expect(calls.some(isGitPushCommand)).toBe(false);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});

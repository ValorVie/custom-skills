import { describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { SyncEngine } from "../../src/core/sync-engine";

describe("core/sync-engine pull parity", () => {
  test("pull conflict choice supports push-then-pull path", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-pull-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "local");
    const timeline: string[] = [];

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        if (command[0] === "git" && command.includes("pull")) {
          timeline.push("git-pull");
        }
        return { stdout: "", stderr: "", exitCode: 0 };
      },
      pullConflictChoiceFn: async () => "push_then_pull",
    });

    try {
      await mkdir(localDir, { recursive: true });
      await writeFile(join(localDir, "a.txt"), "local\n", "utf8");

      await engine.init();
      await engine.removeDirectory("~/.claude", { skipMinCheck: true });
      const config = await engine.addDirectory(localDir);
      const tracked = config.directories.find((item) => item.path === localDir);
      if (!tracked) {
        expect.unreachable("tracked directory should exist");
      }

      await writeFile(
        join(repoDir, tracked.repoSubdir, "a.txt"),
        "remote\n",
        "utf8",
      );

      const originalPush = engine.push.bind(engine);
      engine.push = async () => {
        timeline.push("push");
        return { added: 0, updated: 0, deleted: 0 };
      };

      try {
        await engine.pull();
      } finally {
        engine.push = originalPush;
      }

      const pushIndex = timeline.indexOf("push");
      const pullIndex = timeline.indexOf("git-pull");

      expect(pushIndex).toBeGreaterThanOrEqual(0);
      expect(pullIndex).toBeGreaterThanOrEqual(0);
      expect(pushIndex).toBeLessThan(pullIndex);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("pull uses git pull --rebase and throws on failure", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-pull-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "local");
    const calls: string[][] = [];

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        calls.push(command);
        if (command[0] === "git" && command.includes("pull")) {
          return {
            stdout: "",
            stderr: "cannot rebase onto divergent branch",
            exitCode: 1,
          };
        }
        return { stdout: "", stderr: "", exitCode: 0 };
      },
    });

    try {
      await mkdir(localDir, { recursive: true });
      await writeFile(join(localDir, "a.txt"), "local\n", "utf8");
      await engine.init();
      await engine.removeDirectory("~/.claude", { skipMinCheck: true });
      await engine.addDirectory(localDir);

      await expect(engine.pull({ force: true })).rejects.toThrow(
        "git pull --rebase 失敗",
      );

      const pullCommand = calls.find(
        (command) => command[0] === "git" && command.includes("pull"),
      );
      expect(pullCommand).toBeDefined();
      expect(pullCommand).toContain("--rebase");
      expect(pullCommand).not.toContain("--ff-only");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("pull preserves git pull outputs in summary details", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-pull-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "local");

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        if (command[0] === "git" && command.includes("pull")) {
          return {
            stdout: "Updating abc123..def456\n",
            stderr: "Fast-forward\n",
            exitCode: 0,
          };
        }
        return { stdout: "", stderr: "", exitCode: 0 };
      },
    });

    try {
      await mkdir(localDir, { recursive: true });
      await writeFile(join(localDir, "a.txt"), "local\n", "utf8");
      await engine.init();
      await engine.removeDirectory("~/.claude", { skipMinCheck: true });
      await engine.addDirectory(localDir);

      const summary = await engine.pull({ force: true });
      expect(summary.git?.pull?.stdout).toContain("Updating abc123..def456");
      expect(summary.git?.pull?.stderr).toContain("Fast-forward");
      expect(summary.git?.pull?.command).toEqual(
        expect.arrayContaining(["git", "pull", "--rebase"]),
      );
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});

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

      await engine.init("https://example.com/repo.git");
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
});

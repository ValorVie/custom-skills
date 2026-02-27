import { describe, expect, test } from "bun:test";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { SyncEngine } from "../../src/core/sync-engine";

describe("core/sync-engine init parity", () => {
  test("init throws when git clone fails", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-init-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async (command: string[]) => {
        if (command[0] === "git" && command[1] === "clone") {
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
      await expect(
        engine.init("https://bad.example.com/repo.git"),
      ).rejects.toThrow("git clone");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});

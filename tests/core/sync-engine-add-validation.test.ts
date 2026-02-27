import { describe, expect, test } from "bun:test";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { SyncEngine } from "../../src/core/sync-engine";

describe("sync-engine add validation", () => {
  test("addDirectory throws when directory does not exist", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-add-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async () => ({ stdout: "", stderr: "", exitCode: 0 }),
    });

    try {
      await engine.init("https://example.com/repo.git");
      await expect(engine.addDirectory(join(root, "missing-dir"))).rejects.toThrow(
        "目錄不存在",
      );
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});

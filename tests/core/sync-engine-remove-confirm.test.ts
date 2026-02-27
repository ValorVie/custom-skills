import { describe, expect, test } from "bun:test";
import { access, mkdir, mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { SyncEngine } from "../../src/core/sync-engine";

async function pathExists(pathValue: string): Promise<boolean> {
  try {
    await access(pathValue);
    return true;
  } catch {
    return false;
  }
}

describe("sync-engine remove directory repo subdir behavior", () => {
  test("deleteRepoSubdir=false keeps repo subdir", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-remove-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "tracked-keep");
    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async () => ({ stdout: "", stderr: "", exitCode: 0 }),
    });

    try {
      await mkdir(localDir, { recursive: true });
      await engine.init("https://example.com/repo.git");
      const added = await engine.addDirectory(localDir);
      const tracked = added.directories.find((item) => item.path === localDir);
      if (!tracked) {
        expect.unreachable("directory should be tracked");
      }

      const repoSubdirPath = join(repoDir, tracked.repoSubdir);
      expect(await pathExists(repoSubdirPath)).toBe(true);

      await engine.removeDirectory(localDir, { deleteRepoSubdir: false });
      expect(await pathExists(repoSubdirPath)).toBe(true);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("deleteRepoSubdir=true removes repo subdir", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-remove-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "tracked-delete");
    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async () => ({ stdout: "", stderr: "", exitCode: 0 }),
    });

    try {
      await mkdir(localDir, { recursive: true });
      await engine.init("https://example.com/repo.git");
      const added = await engine.addDirectory(localDir);
      const tracked = added.directories.find((item) => item.path === localDir);
      if (!tracked) {
        expect.unreachable("directory should be tracked");
      }

      const repoSubdirPath = join(repoDir, tracked.repoSubdir);
      expect(await pathExists(repoSubdirPath)).toBe(true);

      await engine.removeDirectory(localDir, { deleteRepoSubdir: true });
      expect(await pathExists(repoSubdirPath)).toBe(false);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("keeps minimum directory check and supports skipMinCheck", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-remove-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async () => ({ stdout: "", stderr: "", exitCode: 0 }),
    });

    try {
      await engine.init("https://example.com/repo.git");
      await expect(engine.removeDirectory("~/.claude")).rejects.toThrow(
        "至少保留一個同步目錄",
      );

      const removed = await engine.removeDirectory("~/.claude", {
        skipMinCheck: true,
        deleteRepoSubdir: false,
      });
      expect(removed.directories).toHaveLength(0);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});

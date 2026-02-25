import { describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { SyncEngine } from "../../src/core/sync-engine";

describe("core/sync-engine", () => {
  test("init creates config and default directory", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const engine = new SyncEngine(configPath, repoDir);

    try {
      const config = await engine.init("https://example.com/repo.git");
      expect(config.remote).toBe("https://example.com/repo.git");
      const raw = await readFile(configPath, "utf8");
      expect(raw.length > 0).toBe(true);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("add and remove directory update config", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const engine = new SyncEngine(configPath, repoDir);

    try {
      await engine.init("https://example.com/repo.git");
      const added = await engine.addDirectory("~/workspace/project");
      expect(
        added.directories.some((dir) => dir.path === "~/workspace/project"),
      ).toBe(true);

      const removed = await engine.removeDirectory("~/workspace/project");
      expect(
        removed.directories.some((dir) => dir.path === "~/workspace/project"),
      ).toBe(false);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("push and pull sync files between local and repo dirs", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const localDir = join(root, "local");
    const engine = new SyncEngine(configPath, repoDir);

    try {
      await mkdir(localDir, { recursive: true });
      await writeFile(join(localDir, "a.txt"), "hello\n", "utf8");

      await engine.init("https://example.com/repo.git");
      await engine.addDirectory(localDir);

      await engine.push();
      await rm(localDir, { recursive: true, force: true });
      await engine.pull();

      const restored = await readFile(join(localDir, "a.txt"), "utf8");
      expect(restored).toBe("hello\n");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});

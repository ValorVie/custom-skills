import { describe, expect, test } from "bun:test";
import {
  access,
  mkdir,
  mkdtemp,
  readFile,
  rm,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { SyncEngine } from "../../src/core/sync-engine";

describe("core/sync-engine ignore parity", () => {
  test("push excludes claude and custom ignore patterns", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-ignore-parity-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");
    const claudeDir = join(root, "claude-home");
    const customDir = join(root, "custom-home");

    const engine = new SyncEngine(configPath, repoDir, {
      runCommandFn: async () => ({ stdout: "", stderr: "", exitCode: 0 }),
    });

    try {
      await mkdir(join(claudeDir, "debug"), { recursive: true });
      await mkdir(join(claudeDir, "cache"), { recursive: true });
      await writeFile(join(claudeDir, "debug", "trace.log"), "trace", "utf8");
      await writeFile(join(claudeDir, "cache", "tmp.json"), "{}", "utf8");
      await writeFile(join(claudeDir, "keep.txt"), "keep-claude", "utf8");

      await mkdir(join(customDir, "cache"), { recursive: true });
      await writeFile(join(customDir, "cache", "x.txt"), "x", "utf8");
      await writeFile(join(customDir, "skip.txt"), "skip", "utf8");
      await writeFile(join(customDir, "keep.txt"), "keep-custom", "utf8");

      await engine.init();
      await engine.removeDirectory("~/.claude", { skipMinCheck: true });
      await engine.addDirectory(claudeDir, { profile: "claude" });
      const config = await engine.addDirectory(customDir, {
        profile: "custom",
        ignore: ["cache/", "skip.txt"],
      });

      const claudeEntry = config.directories.find(
        (directory) => directory.path === claudeDir,
      );
      const customEntry = config.directories.find(
        (directory) => directory.path === customDir,
      );
      if (!claudeEntry || !customEntry) {
        expect.unreachable("tracked directories should exist");
      }

      await engine.push();

      await expect(
        readFile(join(repoDir, claudeEntry.repoSubdir, "keep.txt"), "utf8"),
      ).resolves.toBe("keep-claude");
      await expect(
        access(join(repoDir, claudeEntry.repoSubdir, "debug", "trace.log")),
      ).rejects.toThrow();
      await expect(
        access(join(repoDir, claudeEntry.repoSubdir, "cache", "tmp.json")),
      ).rejects.toThrow();

      await expect(
        readFile(join(repoDir, customEntry.repoSubdir, "keep.txt"), "utf8"),
      ).resolves.toBe("keep-custom");
      await expect(
        access(join(repoDir, customEntry.repoSubdir, "cache", "x.txt")),
      ).rejects.toThrow();
      await expect(
        access(join(repoDir, customEntry.repoSubdir, "skip.txt")),
      ).rejects.toThrow();
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});

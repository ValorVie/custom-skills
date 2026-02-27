import { describe, expect, test } from "bun:test";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import YAML from "yaml";

import { SyncEngine } from "../../src/core/sync-engine";

describe("core/sync-engine config compatibility", () => {
  test("loadConfig maps legacy sync.yaml snake_case fields", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-sync-config-compat-"));
    const configPath = join(root, "sync.yaml");
    const repoDir = join(root, "sync-repo");

    const legacyConfig = {
      version: "1",
      remote: "https://example.com/repo.git",
      last_sync: "2026-02-27T10:00:00.000Z",
      directories: [
        {
          path: "~/workspace",
          repo_subdir: "workspace",
          ignore_profile: "custom",
          custom_ignore: [".env", ".cache"],
        },
      ],
    };

    try {
      await writeFile(configPath, YAML.stringify(legacyConfig), "utf8");
      const engine = new SyncEngine(configPath, repoDir);

      const config = await engine.loadConfig();

      expect(config).not.toBeNull();
      expect(config?.lastSync).toBe("2026-02-27T10:00:00.000Z");
      expect(config?.directories[0]).toEqual({
        path: "~/workspace",
        repoSubdir: "workspace",
        ignoreProfile: "custom",
        customIgnore: [".env", ".cache"],
      });
      expect((config as Record<string, unknown>).last_sync).toBeUndefined();
      expect(
        (config?.directories[0] as Record<string, unknown>).repo_subdir,
      ).toBeUndefined();
      expect(
        (config?.directories[0] as Record<string, unknown>).ignore_profile,
      ).toBeUndefined();
      expect(
        (config?.directories[0] as Record<string, unknown>).custom_ignore,
      ).toBeUndefined();
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});

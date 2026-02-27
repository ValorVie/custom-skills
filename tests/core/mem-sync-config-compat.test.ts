import { describe, expect, test } from "bun:test";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import YAML from "yaml";

import { loadMemSyncConfig } from "../../src/core/mem-sync";

describe("core mem-sync config compatibility", () => {
  test("loadMemSyncConfig reads legacy sync-server.yaml and maps snake_case keys", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-mem-config-compat-"));
    const configPath = join(root, "mem-sync.yaml");
    const legacyPath = join(root, "sync-server.yaml");

    try {
      await writeFile(
        legacyPath,
        YAML.stringify({
          server_url: "https://legacy.example.com",
          api_key: "legacy-key",
          device_name: "legacy-device",
          device_id: "legacy-id",
          last_push_epoch: 101,
          last_pull_epoch: 202,
          auto_sync: true,
          auto_sync_interval_minutes: 15,
        }),
        "utf8",
      );

      const config = await loadMemSyncConfig(configPath);

      expect(config).toEqual({
        serverUrl: "https://legacy.example.com",
        apiKey: "legacy-key",
        deviceName: "legacy-device",
        deviceId: "legacy-id",
        lastPushEpoch: 101,
        lastPullEpoch: 202,
        autoSync: true,
        autoSyncIntervalMinutes: 15,
      });
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});

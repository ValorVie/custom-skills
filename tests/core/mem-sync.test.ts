import { describe, expect, test } from "bun:test";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  cleanupDuplicates,
  getMemSyncStatus,
  loadMemSyncConfig,
  pullMemData,
  pushMemData,
  registerDevice,
  reindexMemData,
  saveMemSyncConfig,
} from "../../src/core/mem-sync";

describe("core/mem-sync", () => {
  test("register/save/load config", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-mem-"));
    const configPath = join(root, "mem-sync.yaml");

    try {
      await saveMemSyncConfig(
        {
          serverUrl: "https://example.com",
          apiKey: "key",
          deviceName: "test",
          deviceId: "id",
          lastPushEpoch: 1,
          lastPullEpoch: 2,
          autoSync: false,
          autoSyncIntervalMinutes: 10,
        },
        configPath,
      );

      const loaded = await loadMemSyncConfig(configPath);
      expect(loaded.serverUrl).toBe("https://example.com");

      const registered = await registerDevice({
        server: "https://server.test",
        name: "device-a",
        adminSecret: "secret",
        configPath,
      });
      expect(registered.serverUrl).toBe("https://server.test");
      expect(registered.deviceName).toBe("device-a");
      expect(registered.apiKey.startsWith("local-")).toBe(true);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("push/pull/status/reindex operate on local sqlite data", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-mem-"));
    const configPath = join(root, "mem-sync.yaml");
    const dbPath = join(root, "statsig.db");

    const sqlite = await import("bun:sqlite");
    const db = new sqlite.Database(dbPath);
    db.run(
      "CREATE TABLE observations (id INTEGER PRIMARY KEY, title TEXT, narrative TEXT, facts TEXT, project TEXT, type TEXT);",
    );
    db.run("INSERT INTO observations (title, narrative) VALUES ('one', 'text one');");
    db.close();

    try {
      await registerDevice({
        server: "https://server.test",
        name: "device-b",
        adminSecret: "secret",
        configPath,
      });

      const pushed = await pushMemData({ configPath, dbPath });
      expect(pushed.pushed).toBe(1);

      const pulled = await pullMemData({ configPath });
      expect(pulled.pulled).toBe(0);

      const status = await getMemSyncStatus({ configPath, dbPath });
      expect(status.localObservations).toBe(1);

      // reindex without worker returns synced=0
      const reindex = await reindexMemData({ dbPath });
      expect(reindex.total).toBe(1);
      expect(reindex.synced).toBe(0);
      expect(reindex.duplicatesRemoved).toBe(0);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("cleanup removes duplicate observations", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-mem-"));
    const dbPath = join(root, "statsig.db");

    const sqlite = await import("bun:sqlite");
    const db = new sqlite.Database(dbPath);
    db.run(
      "CREATE TABLE observations (id INTEGER PRIMARY KEY, title TEXT, narrative TEXT, facts TEXT, project TEXT, type TEXT);",
    );
    // Insert 3 rows with same content — id 2 and 3 are duplicates
    db.run("INSERT INTO observations (id, title, narrative) VALUES (1, 'dup', 'same text');");
    db.run("INSERT INTO observations (id, title, narrative) VALUES (2, 'dup', 'same text');");
    db.run("INSERT INTO observations (id, title, narrative) VALUES (3, 'dup', 'same text');");
    db.run("INSERT INTO observations (id, title, narrative) VALUES (4, 'unique', 'different');");
    db.close();

    try {
      const result = await cleanupDuplicates({ dbPath });
      expect(result.duplicatesRemoved).toBe(2);

      // Verify only 2 rows remain
      const db2 = new sqlite.Database(dbPath, { readonly: true });
      const row = db2.query("SELECT COUNT(*) AS count FROM observations").get() as {
        count: number;
      };
      db2.close();
      expect(row.count).toBe(2);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});

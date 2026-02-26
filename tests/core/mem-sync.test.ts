import { describe, expect, test } from "bun:test";
import { mkdtemp, rm } from "node:fs/promises";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";

import {
  cleanupDuplicates,
  configureAutoSync,
  defaultChromaDbPath,
  defaultMemDbPath,
  defaultMemSyncConfigPath,
  getMemSyncStatus,
  loadMemSyncConfig,
  pullMemData,
  pushMemData,
  registerDevice,
  reindexMemData,
  saveMemSyncConfig,
} from "../../src/core/mem-sync";

describe("mem-sync default paths", () => {
  const home = homedir();

  test("defaultMemSyncConfigPath returns correct path", () => {
    expect(defaultMemSyncConfigPath()).toBe(
      join(home, ".config", "ai-dev", "mem-sync.yaml"),
    );
  });

  test("defaultMemDbPath returns correct path", () => {
    expect(defaultMemDbPath()).toBe(join(home, ".claude-mem", "claude-mem.db"));
  });

  test("defaultChromaDbPath returns correct path", () => {
    expect(defaultChromaDbPath()).toBe(
      join(home, ".claude-mem", "chroma", "chroma.sqlite3"),
    );
  });
});

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
    db.run(
      "INSERT INTO observations (title, narrative) VALUES ('one', 'text one');",
    );
    db.close();

    try {
      await registerDevice({
        server: "https://server.test",
        name: "device-b",
        adminSecret: "secret",
        configPath,
      });

      const pushed = await pushMemData({ configPath, dbPath });
      // fake server returns null → counted as errors, not pushed
      expect(pushed.errors).toBe(1);
      expect(pushed.pushed).toBe(0);

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
    db.run(
      "INSERT INTO observations (id, title, narrative) VALUES (1, 'dup', 'same text');",
    );
    db.run(
      "INSERT INTO observations (id, title, narrative) VALUES (2, 'dup', 'same text');",
    );
    db.run(
      "INSERT INTO observations (id, title, narrative) VALUES (3, 'dup', 'same text');",
    );
    db.run(
      "INSERT INTO observations (id, title, narrative) VALUES (4, 'unique', 'different');",
    );
    db.close();

    try {
      const result = await cleanupDuplicates({ dbPath });
      expect(result.duplicatesRemoved).toBe(2);

      // Verify only 2 rows remain
      const db2 = new sqlite.Database(dbPath, { readonly: true });
      const row = db2
        .query("SELECT COUNT(*) AS count FROM observations")
        .get() as {
        count: number;
      };
      db2.close();
      expect(row.count).toBe(2);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("pushMemData uses preflight hash dedup and batch push", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-mem-"));
    const configPath = join(root, "mem-sync.yaml");
    const dbPath = join(root, "statsig.db");
    const originalFetch = globalThis.fetch;

    const sqlite = await import("bun:sqlite");
    const db = new sqlite.Database(dbPath);
    db.run(
      "CREATE TABLE observations (id INTEGER PRIMARY KEY, title TEXT, narrative TEXT, facts TEXT, project TEXT, type TEXT);",
    );
    db.run("INSERT INTO observations (title, narrative) VALUES ('one', 'n1');");
    db.run("INSERT INTO observations (title, narrative) VALUES ('two', 'n2');");
    db.close();

    await saveMemSyncConfig(
      {
        serverUrl: "https://sync.example.com",
        apiKey: "api-key",
        deviceName: "device-a",
        deviceId: "1",
        lastPushEpoch: 0,
        lastPullEpoch: 0,
        autoSync: false,
        autoSyncIntervalMinutes: 10,
      },
      configPath,
    );

    try {
      globalThis.fetch = (async (input, init) => {
        const url = String(input);
        if (url.endsWith("/api/sync/push-preflight")) {
          const body = JSON.parse(String(init?.body ?? "{}")) as {
            hashes?: string[];
          };
          const missing = body.hashes?.slice(0, 1) ?? [];
          return new Response(JSON.stringify({ missing }), { status: 200 });
        }

        if (url.endsWith("/api/sync/push")) {
          const body = JSON.parse(String(init?.body ?? "{}")) as {
            observations?: unknown[];
          };
          return new Response(
            JSON.stringify({
              stats: {
                observationsImported: body.observations?.length ?? 0,
              },
            }),
            { status: 200 },
          );
        }

        return new Response("{}", { status: 404 });
      }) as typeof fetch;

      const result = await pushMemData({ configPath, dbPath });
      expect(result.pushed).toBe(1);
      expect(result.skipped).toBe(1);
    } finally {
      globalThis.fetch = originalFetch;
      await rm(root, { recursive: true, force: true });
    }
  });

  test("pullMemData performs paginated pull and merges observations", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-mem-"));
    const configPath = join(root, "mem-sync.yaml");
    const dbPath = join(root, "statsig.db");
    const originalFetch = globalThis.fetch;
    let pullCall = 0;

    await saveMemSyncConfig(
      {
        serverUrl: "https://sync.example.com",
        apiKey: "api-key",
        deviceName: "device-a",
        deviceId: "1",
        lastPushEpoch: 0,
        lastPullEpoch: 0,
        autoSync: false,
        autoSyncIntervalMinutes: 10,
      },
      configPath,
    );

    try {
      globalThis.fetch = (async (input) => {
        const url = String(input);

        if (url.includes("/api/sync/pull")) {
          pullCall += 1;
          if (pullCall === 1) {
            return new Response(
              JSON.stringify({
                observations: [
                  { title: "a", narrative: "one", sync_content_hash: "hash-a" },
                  { title: "b", narrative: "two", sync_content_hash: "hash-b" },
                ],
                has_more: true,
                next_since: 1000,
              }),
              { status: 200 },
            );
          }

          return new Response(
            JSON.stringify({
              observations: [
                { title: "c", narrative: "three", sync_content_hash: "hash-c" },
              ],
              has_more: false,
              next_since: 2000,
            }),
            { status: 200 },
          );
        }

        return new Response("{}", { status: 404 });
      }) as typeof fetch;

      const result = await pullMemData({ configPath, dbPath });
      expect(result.pulled).toBe(3);

      const sqlite = await import("bun:sqlite");
      const db = new sqlite.Database(dbPath, { readonly: true });
      const row = db
        .query("SELECT COUNT(*) AS count FROM observations")
        .get() as {
        count: number;
      };
      db.close();
      expect(row.count).toBe(3);
    } finally {
      globalThis.fetch = originalFetch;
      await rm(root, { recursive: true, force: true });
    }
  });

  test("getMemSyncStatus includes pending push and remote status", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-mem-"));
    const configPath = join(root, "mem-sync.yaml");
    const dbPath = join(root, "statsig.db");
    const originalFetch = globalThis.fetch;

    const sqlite = await import("bun:sqlite");
    const db = new sqlite.Database(dbPath);
    db.run(
      "CREATE TABLE observations (id INTEGER PRIMARY KEY, title TEXT, narrative TEXT, created_at_epoch INTEGER, sync_content_hash TEXT);",
    );
    db.run(
      "INSERT INTO observations (title, narrative, created_at_epoch, sync_content_hash) VALUES ('one', 'n1', 10, 'h1');",
    );
    db.run(
      "INSERT INTO observations (title, narrative, created_at_epoch, sync_content_hash) VALUES ('two', 'n2', 20, 'h2');",
    );
    db.close();

    await saveMemSyncConfig(
      {
        serverUrl: "https://sync.example.com",
        apiKey: "api-key",
        deviceName: "device-a",
        deviceId: "1",
        lastPushEpoch: 15,
        lastPullEpoch: 0,
        autoSync: false,
        autoSyncIntervalMinutes: 10,
      },
      configPath,
    );

    try {
      globalThis.fetch = (async (input) => {
        const url = String(input);
        if (url.endsWith("/api/sync/status")) {
          return new Response(
            JSON.stringify({ observations: 99, sessions: 1, devices: 2 }),
            { status: 200 },
          );
        }
        return new Response("{}", { status: 404 });
      }) as typeof fetch;

      const status = await getMemSyncStatus({ configPath, dbPath });
      expect(status.localObservations).toBe(2);
      expect(status.pendingPushCount).toBe(1);
      expect(status.remoteStatus?.observations).toBe(99);
    } finally {
      globalThis.fetch = originalFetch;
      await rm(root, { recursive: true, force: true });
    }
  });

  test("configureAutoSync can enable and disable", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-mem-"));
    const configPath = join(root, "mem-sync.yaml");

    try {
      const enabled = await configureAutoSync({
        enable: true,
        intervalMinutes: 15,
        configPath,
      });
      expect(enabled.enabled).toBe(true);

      const status = await configureAutoSync({ status: true, configPath });
      expect(status.enabled).toBe(true);

      const disabled = await configureAutoSync({ disable: true, configPath });
      expect(disabled.enabled).toBe(false);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});

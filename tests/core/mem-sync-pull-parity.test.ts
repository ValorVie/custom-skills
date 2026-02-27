import { describe, expect, test } from "bun:test";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  pullMemData,
  saveMemSyncConfig,
} from "../../src/core/mem-sync";

const pullPayload = {
  sessions: [
    {
      content_session_id: "sess-1",
      memory_session_id: "mem-1",
      started_at_epoch: 101,
      project: "proj",
    },
  ],
  observations: [
    {
      memory_session_id: "mem-1",
      title: "obs-1",
      narrative: "n-1",
      facts: "f-1",
      project: "proj",
      type: "note",
      created_at_epoch: 101,
      sync_content_hash: "hash-obs-1",
    },
  ],
  summaries: [
    {
      session_id: "sess-1",
      memory_session_id: "mem-1",
      created_at_epoch: 101,
      request: "req-1",
    },
  ],
  prompts: [
    {
      content_session_id: "sess-1",
      prompt_number: 1,
      prompt_text: "prompt-1",
      created_at_epoch: 101,
    },
  ],
  has_more: false,
  next_since: 2000,
};

async function createMemDb(dbPath: string): Promise<void> {
  const sqlite = await import("bun:sqlite");
  const db = new sqlite.Database(dbPath);
  db.run(
    "CREATE TABLE sdk_sessions (id INTEGER PRIMARY KEY, content_session_id TEXT UNIQUE, memory_session_id TEXT, started_at_epoch INTEGER, project TEXT);",
  );
  db.run(
    "CREATE TABLE observations (id INTEGER PRIMARY KEY, memory_session_id TEXT, title TEXT, narrative TEXT, facts TEXT, project TEXT, type TEXT, created_at_epoch INTEGER, sync_content_hash TEXT UNIQUE);",
  );
  db.run(
    "CREATE TABLE session_summaries (id INTEGER PRIMARY KEY, session_id TEXT, memory_session_id TEXT UNIQUE, created_at_epoch INTEGER, request TEXT);",
  );
  db.run(
    "CREATE TABLE user_prompts (id INTEGER PRIMARY KEY, content_session_id TEXT, prompt_number INTEGER, prompt_text TEXT, created_at_epoch INTEGER, UNIQUE(content_session_id, prompt_number));",
  );
  db.close();
}

async function countRows(dbPath: string, table: string): Promise<number> {
  const sqlite = await import("bun:sqlite");
  const db = new sqlite.Database(dbPath, { readonly: true });
  const row = db.query(`SELECT COUNT(*) AS count FROM ${table}`).get() as {
    count: number;
  };
  db.close();
  return row.count;
}

describe("core/mem-sync pull parity", () => {
  test("pullMemData imports sessions/observations/summaries/prompts via worker API then fallback sqlite", async () => {
    const originalFetch = globalThis.fetch;

    const apiRoot = await mkdtemp(join(tmpdir(), "ai-dev-mem-pull-parity-"));
    const apiConfigPath = join(apiRoot, "mem-sync.yaml");
    const apiDbPath = join(apiRoot, "claude-mem.db");

    const fallbackRoot = await mkdtemp(
      join(tmpdir(), "ai-dev-mem-pull-parity-"),
    );
    const fallbackConfigPath = join(fallbackRoot, "mem-sync.yaml");
    const fallbackDbPath = join(fallbackRoot, "claude-mem.db");

    await createMemDb(apiDbPath);
    await createMemDb(fallbackDbPath);

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
      apiConfigPath,
    );
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
      fallbackConfigPath,
    );

    let importApiCalls = 0;
    let capturedImportPayload: Record<string, unknown> | null = null;

    try {
      globalThis.fetch = (async (input, init) => {
        const url = String(input);

        if (url.includes("/api/sync/pull")) {
          return new Response(JSON.stringify(pullPayload), { status: 200 });
        }

        if (url.endsWith("/api/import")) {
          importApiCalls += 1;
          capturedImportPayload = JSON.parse(
            String(init?.body ?? "{}"),
          ) as Record<string, unknown>;
          return new Response(
            JSON.stringify({
              stats: {
                sessionsImported: 1,
                observationsImported: 1,
                summariesImported: 1,
                promptsImported: 1,
                sessionsSkipped: 0,
                observationsSkipped: 0,
                summariesSkipped: 0,
                promptsSkipped: 0,
              },
            }),
            { status: 200 },
          );
        }

        return new Response("{}", { status: 404 });
      }) as typeof fetch;

      const apiResult = await pullMemData({
        configPath: apiConfigPath,
        dbPath: apiDbPath,
      });

      expect(importApiCalls).toBe(1);
      expect((capturedImportPayload?.sessions as unknown[]) ?? []).toHaveLength(
        1,
      );
      expect(
        (capturedImportPayload?.observations as unknown[]) ?? [],
      ).toHaveLength(1);
      expect((capturedImportPayload?.summaries as unknown[]) ?? []).toHaveLength(
        1,
      );
      expect((capturedImportPayload?.prompts as unknown[]) ?? []).toHaveLength(1);

      expect(apiResult.imported.sessions).toBe(1);
      expect(apiResult.imported.observations).toBe(1);
      expect(apiResult.imported.summaries).toBe(1);
      expect(apiResult.imported.prompts).toBe(1);

      globalThis.fetch = (async (input) => {
        const url = String(input);

        if (url.includes("/api/sync/pull")) {
          return new Response(JSON.stringify(pullPayload), { status: 200 });
        }

        if (url.endsWith("/api/import")) {
          importApiCalls += 1;
          throw new Error("worker unavailable");
        }

        return new Response("{}", { status: 404 });
      }) as typeof fetch;

      const fallbackResult = await pullMemData({
        configPath: fallbackConfigPath,
        dbPath: fallbackDbPath,
      });

      expect(fallbackResult.imported.sessions).toBe(1);
      expect(fallbackResult.imported.observations).toBe(1);
      expect(fallbackResult.imported.summaries).toBe(1);
      expect(fallbackResult.imported.prompts).toBe(1);
      expect(await countRows(fallbackDbPath, "sdk_sessions")).toBe(1);
      expect(await countRows(fallbackDbPath, "observations")).toBe(1);
      expect(await countRows(fallbackDbPath, "session_summaries")).toBe(1);
      expect(await countRows(fallbackDbPath, "user_prompts")).toBe(1);
    } finally {
      globalThis.fetch = originalFetch;
      await rm(apiRoot, { recursive: true, force: true });
      await rm(fallbackRoot, { recursive: true, force: true });
    }
  });
});

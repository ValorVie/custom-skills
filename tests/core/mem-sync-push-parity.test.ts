import { describe, expect, test } from "bun:test";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  loadMemSyncConfig,
  pushMemData,
  saveMemSyncConfig,
} from "../../src/core/mem-sync";

describe("core/mem-sync push parity", () => {
  test("pushMemData pushes sessions/observations/summaries/prompts since lastPushEpoch", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-mem-push-parity-"));
    const configPath = join(root, "mem-sync.yaml");
    const dbPath = join(root, "claude-mem.db");
    const originalFetch = globalThis.fetch;

    const sqlite = await import("bun:sqlite");
    const db = new sqlite.Database(dbPath);

    db.run(
      "CREATE TABLE sdk_sessions (id INTEGER PRIMARY KEY, content_session_id TEXT, memory_session_id TEXT, started_at_epoch INTEGER, project TEXT);",
    );
    db.run(
      "CREATE TABLE observations (id INTEGER PRIMARY KEY, title TEXT, narrative TEXT, facts TEXT, project TEXT, type TEXT, created_at_epoch INTEGER, sync_content_hash TEXT);",
    );
    db.run(
      "CREATE TABLE session_summaries (id INTEGER PRIMARY KEY, session_id TEXT, memory_session_id TEXT, created_at_epoch INTEGER, request TEXT);",
    );
    db.run(
      "CREATE TABLE user_prompts (id INTEGER PRIMARY KEY, content_session_id TEXT, prompt_number INTEGER, created_at_epoch INTEGER, prompt_text TEXT);",
    );

    db.run(
      "INSERT INTO sdk_sessions (content_session_id, memory_session_id, started_at_epoch, project) VALUES ('sess-100', 'mem-100', 100, 'proj');",
    );
    db.run(
      "INSERT INTO sdk_sessions (content_session_id, memory_session_id, started_at_epoch, project) VALUES ('sess-101', 'mem-101', 101, 'proj');",
    );

    db.run(
      "INSERT INTO observations (title, narrative, facts, project, type, created_at_epoch, sync_content_hash) VALUES ('old', 'n-old', 'f-old', 'proj', 'note', 100, 'hash-old');",
    );
    db.run(
      "INSERT INTO observations (title, narrative, facts, project, type, created_at_epoch, sync_content_hash) VALUES ('new', 'n-new', 'f-new', 'proj', 'note', 101, 'hash-new');",
    );

    db.run(
      "INSERT INTO session_summaries (session_id, memory_session_id, created_at_epoch, request) VALUES ('sess-100', 'mem-100', 100, 'req-old');",
    );
    db.run(
      "INSERT INTO session_summaries (session_id, memory_session_id, created_at_epoch, request) VALUES ('sess-101', 'mem-101', 101, 'req-new');",
    );

    db.run(
      "INSERT INTO user_prompts (content_session_id, prompt_number, created_at_epoch, prompt_text) VALUES ('sess-100', 1, 100, 'p-old');",
    );
    db.run(
      "INSERT INTO user_prompts (content_session_id, prompt_number, created_at_epoch, prompt_text) VALUES ('sess-101', 1, 101, 'p-new');",
    );
    db.close();

    await saveMemSyncConfig(
      {
        serverUrl: "https://sync.example.com",
        apiKey: "api-key",
        deviceName: "device-a",
        deviceId: "1",
        lastPushEpoch: 100,
        lastPullEpoch: 0,
        autoSync: false,
        autoSyncIntervalMinutes: 10,
      },
      configPath,
    );

    let capturedPushPayload: Record<string, unknown> | null = null;

    try {
      globalThis.fetch = (async (input, init) => {
        const url = String(input);

        if (url.endsWith("/api/sync/push-preflight")) {
          const body = JSON.parse(String(init?.body ?? "{}")) as {
            hashes?: string[];
          };
          return new Response(
            JSON.stringify({
              missing: body.hashes ?? [],
            }),
            { status: 200 },
          );
        }

        if (url.endsWith("/api/sync/push")) {
          capturedPushPayload = JSON.parse(
            String(init?.body ?? "{}"),
          ) as Record<string, unknown>;

          const sessions = (capturedPushPayload.sessions ?? []) as unknown[];
          const observations = (capturedPushPayload.observations ?? []) as
            | unknown[];
          const summaries = (capturedPushPayload.summaries ?? []) as unknown[];
          const prompts = (capturedPushPayload.prompts ?? []) as unknown[];

          return new Response(
            JSON.stringify({
              stats: {
                sessionsImported: sessions.length,
                observationsImported: observations.length,
                summariesImported: summaries.length,
                promptsImported: prompts.length,
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

      await pushMemData({ configPath, dbPath });

      expect(capturedPushPayload).not.toBeNull();
      expect((capturedPushPayload?.sessions as unknown[]) ?? []).toHaveLength(1);
      expect((capturedPushPayload?.observations as unknown[]) ?? []).toHaveLength(
        1,
      );
      expect((capturedPushPayload?.summaries as unknown[]) ?? []).toHaveLength(1);
      expect((capturedPushPayload?.prompts as unknown[]) ?? []).toHaveLength(1);
    } finally {
      globalThis.fetch = originalFetch;
      await rm(root, { recursive: true, force: true });
    }
  });

  test("pushMemData throws when server config is missing", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-mem-push-parity-"));
    const configPath = join(root, "mem-sync.yaml");
    const dbPath = join(root, "claude-mem.db");

    const sqlite = await import("bun:sqlite");
    const db = new sqlite.Database(dbPath);
    db.run(
      "CREATE TABLE observations (id INTEGER PRIMARY KEY, title TEXT, narrative TEXT, facts TEXT, project TEXT, type TEXT, created_at_epoch INTEGER, sync_content_hash TEXT);",
    );
    db.run(
      "INSERT INTO observations (title, narrative, facts, project, type, created_at_epoch, sync_content_hash) VALUES ('new', 'n-new', 'f-new', 'proj', 'note', 101, 'hash-new');",
    );
    db.close();

    try {
      await expect(pushMemData({ configPath, dbPath })).rejects.toThrow(
        "ai-dev mem register",
      );
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("pushMemData updates lastPushEpoch from server_epoch", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-mem-push-parity-"));
    const configPath = join(root, "mem-sync.yaml");
    const dbPath = join(root, "claude-mem.db");
    const originalFetch = globalThis.fetch;

    const sqlite = await import("bun:sqlite");
    const db = new sqlite.Database(dbPath);
    db.run(
      "CREATE TABLE observations (id INTEGER PRIMARY KEY, title TEXT, narrative TEXT, facts TEXT, project TEXT, type TEXT, created_at_epoch INTEGER, sync_content_hash TEXT);",
    );
    db.run(
      "INSERT INTO observations (title, narrative, facts, project, type, created_at_epoch, sync_content_hash) VALUES ('new', 'n-new', 'f-new', 'proj', 'note', 101, 'hash-new');",
    );
    db.close();

    await saveMemSyncConfig(
      {
        serverUrl: "https://sync.example.com",
        apiKey: "api-key",
        deviceName: "device-a",
        deviceId: "1",
        lastPushEpoch: 100,
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
          return new Response(
            JSON.stringify({
              missing: body.hashes ?? [],
            }),
            { status: 200 },
          );
        }

        if (url.endsWith("/api/sync/push")) {
          return new Response(
            JSON.stringify({
              server_epoch: 1234567890,
              stats: {
                sessionsImported: 0,
                observationsImported: 1,
                summariesImported: 0,
                promptsImported: 0,
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

      await pushMemData({ configPath, dbPath });
      const config = await loadMemSyncConfig(configPath);
      expect(config.lastPushEpoch).toBe(1234567890);
    } finally {
      globalThis.fetch = originalFetch;
      await rm(root, { recursive: true, force: true });
    }
  });
});

import { describe, expect, test } from "bun:test";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  pullMemData,
  saveMemSyncConfig,
} from "../../src/core/mem-sync";

describe("core/mem-sync since parity", () => {
  test("pullMemData sends since in epoch-seconds", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-mem-since-parity-"));
    const configPath = join(root, "mem-sync.yaml");
    const dbPath = join(root, "claude-mem.db");
    const originalFetch = globalThis.fetch;
    let capturedSince: string | null = null;

    await saveMemSyncConfig(
      {
        serverUrl: "https://sync.example.com",
        apiKey: "api-key",
        deviceName: "device-a",
        deviceId: "1",
        lastPushEpoch: 0,
        lastPullEpoch: 123,
        autoSync: false,
        autoSyncIntervalMinutes: 10,
      },
      configPath,
    );

    try {
      globalThis.fetch = (async (input) => {
        const url = new URL(String(input));

        if (url.pathname === "/api/sync/pull") {
          capturedSince = url.searchParams.get("since");
          return new Response(
            JSON.stringify({
              sessions: [],
              observations: [],
              summaries: [],
              prompts: [],
              has_more: false,
            }),
            { status: 200 },
          );
        }

        return new Response("{}", { status: 404 });
      }) as typeof fetch;

      await pullMemData({ configPath, dbPath });

      expect(capturedSince).toBe("123");
    } finally {
      globalThis.fetch = originalFetch;
      await rm(root, { recursive: true, force: true });
    }
  });
});

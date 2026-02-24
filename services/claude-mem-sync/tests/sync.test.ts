import { describe, test, expect } from "bun:test";
import { computeContentHash } from "../server/src/utils/hash.js";

// 這些測試需要 Docker Compose 環境運行
// 執行方式：cd services/claude-mem-sync && docker compose up -d && bun test

const BASE_URL = process.env.TEST_SERVER_URL || "http://localhost:3000";
const ADMIN_SECRET = process.env.ADMIN_SECRET || "test-secret";
const RUN_ID = process.env.TEST_RUN_ID || `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

const BASE_CONTENT_SESSION_ID = `test-cs-001-${RUN_ID}`;
const BASE_MEMORY_SESSION_ID = `test-ms-001-${RUN_ID}`;
const BASE_PROJECT = `test-project-${RUN_ID}`;

async function apiRequest(
  method: string,
  path: string,
  body?: any,
  headers?: Record<string, string>
): Promise<{ status: number; data: any }> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json();
  return { status: res.status, data };
}

describe("Health", () => {
  test("GET /api/health returns ok", async () => {
    const { status, data } = await apiRequest("GET", "/api/health");
    expect(status).toBe(200);
    expect(data.status).toBe("ok");
  });
});

describe("Auth", () => {
  test("POST /api/auth/register requires admin secret", async () => {
    const { status } = await apiRequest("POST", "/api/auth/register", { name: "test" });
    expect(status).toBe(403);
  });

  test("POST /api/auth/register with valid secret returns api_key", async () => {
    const { status, data } = await apiRequest(
      "POST",
      "/api/auth/register",
      { name: "test-device" },
      { "X-Admin-Secret": ADMIN_SECRET }
    );
    expect(status).toBe(200);
    expect(data.api_key).toMatch(/^cm_sync_/);
    expect(data.device_id).toBeGreaterThan(0);
  });

  test("POST /api/auth/register same name keeps device_id and rotates key", async () => {
    const first = await apiRequest(
      "POST",
      "/api/auth/register",
      { name: "idempotent-device" },
      { "X-Admin-Secret": ADMIN_SECRET }
    );
    const second = await apiRequest(
      "POST",
      "/api/auth/register",
      { name: "idempotent-device" },
      { "X-Admin-Secret": ADMIN_SECRET }
    );

    expect(first.status).toBe(200);
    expect(second.status).toBe(200);
    expect(second.data.device_id).toBe(first.data.device_id);
    expect(second.data.api_key).not.toBe(first.data.api_key);
    expect(second.data.rotated).toBe(true);

    const oldKeyStatus = await apiRequest(
      "GET",
      "/api/sync/status",
      undefined,
      { "X-API-Key": first.data.api_key }
    );
    expect(oldKeyStatus.status).toBe(401);

    const newKeyStatus = await apiRequest(
      "GET",
      "/api/sync/status",
      undefined,
      { "X-API-Key": second.data.api_key }
    );
    expect(newKeyStatus.status).toBe(200);
  });

  test("POST /api/auth/register requires name", async () => {
    const { status } = await apiRequest(
      "POST",
      "/api/auth/register",
      {},
      { "X-Admin-Secret": ADMIN_SECRET }
    );
    expect(status).toBe(400);
  });
});

describe("Sync", () => {
  let deviceAKey: string;
  let deviceBKey: string;
  let deviceAId: number;
  let deviceBId: number;

  test("setup: register two devices", async () => {
    const a = await apiRequest(
      "POST", "/api/auth/register",
      { name: `device-a-${RUN_ID}` },
      { "X-Admin-Secret": ADMIN_SECRET }
    );
    deviceAKey = a.data.api_key;
    deviceAId = a.data.device_id;

    const b = await apiRequest(
      "POST", "/api/auth/register",
      { name: `device-b-${RUN_ID}` },
      { "X-Admin-Secret": ADMIN_SECRET }
    );
    deviceBKey = b.data.api_key;
    deviceBId = b.data.device_id;

    expect(deviceAKey).toBeTruthy();
    expect(deviceBKey).toBeTruthy();
    expect(deviceAId).toBeGreaterThan(0);
    expect(deviceBId).toBeGreaterThan(0);
  });

  test("POST /api/sync/push requires auth", async () => {
    const { status } = await apiRequest("POST", "/api/sync/push", {
      sessions: [], observations: [], summaries: [], prompts: [],
    });
    expect(status).toBe(401);
  });

  test("POST /api/sync/push inserts new data", async () => {
    const { status, data } = await apiRequest(
      "POST",
      "/api/sync/push",
      {
        sessions: [{
          content_session_id: BASE_CONTENT_SESSION_ID,
          memory_session_id: BASE_MEMORY_SESSION_ID,
          project: BASE_PROJECT,
          started_at: "2026-02-24T00:00:00Z",
          started_at_epoch: 1771855200000,
          status: "completed",
        }],
        observations: [{
          memory_session_id: BASE_MEMORY_SESSION_ID,
          project: BASE_PROJECT,
          type: "discovery",
          title: `Test observation ${RUN_ID}`,
          narrative: `Narrative ${RUN_ID}`,
          facts: "[]",
          created_at: "2026-02-24T00:00:00Z",
          created_at_epoch: 1771855200000,
        }],
        summaries: [{
          session_id: BASE_MEMORY_SESSION_ID,
          request: "Test request",
          project: BASE_PROJECT,
          created_at: "2026-02-24T00:00:00Z",
          created_at_epoch: 1771855200000,
        }],
        prompts: [{
          content_session_id: BASE_CONTENT_SESSION_ID,
          project: BASE_PROJECT,
          prompt_number: 1,
          prompt_text: "hello",
          created_at: "2026-02-24T00:00:00Z",
          created_at_epoch: 1771855200000,
        }],
      },
      { "X-API-Key": deviceAKey }
    );
    expect(status).toBe(200);
    expect(data.success).toBe(true);
    expect(data.stats.sessionsImported).toBe(1);
    expect(data.stats.observationsImported).toBe(1);
    expect(data.stats.summariesImported).toBe(1);
    expect(data.stats.promptsImported).toBe(1);
  });

  test("POST /api/sync/push upserts existing session on re-push", async () => {
    const { data } = await apiRequest(
      "POST",
      "/api/sync/push",
      {
        sessions: [{
          content_session_id: BASE_CONTENT_SESSION_ID,
          memory_session_id: BASE_MEMORY_SESSION_ID,
          project: BASE_PROJECT,
          started_at: "2026-02-24T00:00:00Z",
          started_at_epoch: 1771855200000,
          status: "completed",
        }],
        observations: [],
        summaries: [],
        prompts: [],
      },
      { "X-API-Key": deviceAKey }
    );
    expect(data.stats.sessionsImported).toBe(1);
    expect(data.stats.sessionsSkipped).toBe(0);
  });

  test("POST /api/sync/push-preflight returns missing hashes", async () => {
    const existingHash = computeContentHash({
      title: `Existing observation ${RUN_ID}`,
      narrative: `Already on server ${RUN_ID}`,
      facts: "[]",
      project: BASE_PROJECT,
      type: "discovery",
    });
    const newHash = computeContentHash({
      title: `New observation ${RUN_ID}`,
      narrative: `Not on server ${RUN_ID}`,
      facts: "[]",
      project: BASE_PROJECT,
      type: "discovery",
    });

    const pushResult = await apiRequest(
      "POST",
      "/api/sync/push",
      {
        sessions: [{
          content_session_id: `preflight-cs-001-${RUN_ID}`,
          memory_session_id: `preflight-ms-001-${RUN_ID}`,
          project: BASE_PROJECT,
          started_at: "2026-02-24T01:00:00Z",
          started_at_epoch: 1771858800000,
          status: "completed",
        }],
        observations: [{
          memory_session_id: `preflight-ms-001-${RUN_ID}`,
          project: BASE_PROJECT,
          type: "discovery",
          title: `Existing observation ${RUN_ID}`,
          narrative: `Already on server ${RUN_ID}`,
          facts: "[]",
          created_at: "2026-02-24T01:00:00Z",
          created_at_epoch: 1771858800000,
          sync_content_hash: existingHash,
        }],
        summaries: [],
        prompts: [],
      },
      { "X-API-Key": deviceAKey }
    );
    expect(pushResult.status).toBe(200);

    const { status, data } = await apiRequest(
      "POST",
      "/api/sync/push-preflight",
      { hashes: [existingHash, newHash] },
      { "X-API-Key": deviceAKey }
    );
    expect(status).toBe(200);
    expect(data.missing).toEqual([newHash]);
  });

  test("POST /api/sync/push-preflight with empty hashes", async () => {
    const { status, data } = await apiRequest(
      "POST",
      "/api/sync/push-preflight",
      { hashes: [] },
      { "X-API-Key": deviceAKey }
    );
    expect(status).toBe(200);
    expect(data.missing).toEqual([]);
  });

  test("POST /api/sync/push-preflight requires auth", async () => {
    const { status } = await apiRequest(
      "POST",
      "/api/sync/push-preflight",
      { hashes: ["abc"] }
    );
    expect(status).toBe(401);
  });

  test("GET /api/sync/pull excludes own data", async () => {
    const { status, data } = await apiRequest(
      "GET",
      "/api/sync/pull?since=0",
      undefined,
      { "X-API-Key": deviceAKey }
    );
    expect(status).toBe(200);
    expect(
      data.sessions.every(
        (session: { origin_device_id: number }) =>
          session.origin_device_id !== deviceAId
      )
    ).toBe(true);
    expect(
      data.observations.every(
        (observation: { origin_device_id: number }) =>
          observation.origin_device_id !== deviceAId
      )
    ).toBe(true);
  });

  test("GET /api/sync/pull returns other device data", async () => {
    const { status, data } = await apiRequest(
      "GET",
      "/api/sync/pull?since=0",
      undefined,
      { "X-API-Key": deviceBKey }
    );
    expect(status).toBe(200);
    expect(data.sessions.length).toBeGreaterThanOrEqual(1);
    expect(data.observations.length).toBeGreaterThanOrEqual(1);
    expect(data.summaries.length).toBeGreaterThanOrEqual(1);
    expect(data.prompts.length).toBeGreaterThanOrEqual(1);
    const sessionIds = data.sessions.map((session: { content_session_id: string }) => session.content_session_id);
    expect(sessionIds).toContain(BASE_CONTENT_SESSION_ID);
  });

  test("GET /api/sync/pull includes sync_content_hash", async () => {
    const { status, data } = await apiRequest(
      "GET",
      "/api/sync/pull?since=0",
      undefined,
      { "X-API-Key": deviceBKey }
    );
    expect(status).toBe(200);
    expect(data.observations.length).toBeGreaterThan(0);
    for (const obs of data.observations) {
      expect(typeof obs.sync_content_hash).toBe("string");
      expect(obs.sync_content_hash).toHaveLength(32);
    }
  });

  test("cross-device push dedup via sync_content_hash", async () => {
    const dedupProject = `dedup-test-${RUN_ID}`;
    const baseObservation = {
      project: dedupProject,
      type: "discovery",
      title: `Cross-device test ${RUN_ID}`,
      narrative: `Should not duplicate ${RUN_ID}`,
      facts: "[]",
      created_at: "2026-02-24T02:00:00Z",
      created_at_epoch: 1771862400000,
    };

    const first = await apiRequest(
      "POST",
      "/api/sync/push",
      {
        sessions: [{
          content_session_id: `dedup-cs-001-${RUN_ID}`,
          memory_session_id: `dedup-ms-001-${RUN_ID}`,
          project: dedupProject,
          started_at: "2026-02-24T02:00:00Z",
          started_at_epoch: 1771862400000,
          status: "completed",
        }],
        observations: [{
          ...baseObservation,
          memory_session_id: `dedup-ms-001-${RUN_ID}`,
        }],
        summaries: [],
        prompts: [],
      },
      { "X-API-Key": deviceAKey }
    );
    expect(first.status).toBe(200);

    const second = await apiRequest(
      "POST",
      "/api/sync/push",
      {
        sessions: [{
          content_session_id: `dedup-cs-002-${RUN_ID}`,
          memory_session_id: `dedup-ms-002-${RUN_ID}`,
          project: dedupProject,
          started_at: "2026-02-24T02:00:00Z",
          started_at_epoch: 1771862400000,
          status: "completed",
        }],
        observations: [{
          ...baseObservation,
          memory_session_id: `dedup-ms-002-${RUN_ID}`,
          created_at_epoch: 1771862401000,
        }],
        summaries: [],
        prompts: [],
      },
      { "X-API-Key": deviceBKey }
    );
    expect(second.status).toBe(200);
    expect(second.data.stats.observationsSkipped).toBe(1);
  });

  test("GET /api/sync/status returns counts", async () => {
    const { status, data } = await apiRequest(
      "GET",
      "/api/sync/status",
      undefined,
      { "X-API-Key": deviceAKey }
    );
    expect(status).toBe(200);
    expect(data.sessions).toBeGreaterThanOrEqual(1);
    expect(data.observations).toBeGreaterThanOrEqual(1);
  });
});

import { describe, test, expect } from "bun:test";

// 這些測試需要 Docker Compose 環境運行
// 執行方式：cd services/claude-mem-sync && docker compose up -d && bun test

const BASE_URL = process.env.TEST_SERVER_URL || "http://localhost:3000";
const ADMIN_SECRET = process.env.ADMIN_SECRET || "test-secret";

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

  test("setup: register two devices", async () => {
    const a = await apiRequest(
      "POST", "/api/auth/register",
      { name: "device-a" },
      { "X-Admin-Secret": ADMIN_SECRET }
    );
    deviceAKey = a.data.api_key;

    const b = await apiRequest(
      "POST", "/api/auth/register",
      { name: "device-b" },
      { "X-Admin-Secret": ADMIN_SECRET }
    );
    deviceBKey = b.data.api_key;

    expect(deviceAKey).toBeTruthy();
    expect(deviceBKey).toBeTruthy();
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
          content_session_id: "test-cs-001",
          memory_session_id: "test-ms-001",
          project: "test-project",
          started_at: "2026-02-24T00:00:00Z",
          started_at_epoch: 1771855200000,
          status: "completed",
        }],
        observations: [{
          memory_session_id: "test-ms-001",
          project: "test-project",
          type: "discovery",
          title: "Test observation",
          created_at: "2026-02-24T00:00:00Z",
          created_at_epoch: 1771855200000,
        }],
        summaries: [{
          session_id: "test-ms-001",
          request: "Test request",
          project: "test-project",
          created_at: "2026-02-24T00:00:00Z",
          created_at_epoch: 1771855200000,
        }],
        prompts: [{
          content_session_id: "test-cs-001",
          project: "test-project",
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

  test("POST /api/sync/push deduplicates on re-push", async () => {
    const { data } = await apiRequest(
      "POST",
      "/api/sync/push",
      {
        sessions: [{
          content_session_id: "test-cs-001",
          memory_session_id: "test-ms-001",
          project: "test-project",
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
    expect(data.stats.sessionsSkipped).toBe(1);
    expect(data.stats.sessionsImported).toBe(0);
  });

  test("GET /api/sync/pull excludes own data", async () => {
    const { status, data } = await apiRequest(
      "GET",
      "/api/sync/pull?since=0",
      undefined,
      { "X-API-Key": deviceAKey }
    );
    expect(status).toBe(200);
    expect(data.sessions.length).toBe(0);
    expect(data.observations.length).toBe(0);
  });

  test("GET /api/sync/pull returns other device data", async () => {
    const { status, data } = await apiRequest(
      "GET",
      "/api/sync/pull?since=0",
      undefined,
      { "X-API-Key": deviceBKey }
    );
    expect(status).toBe(200);
    expect(data.sessions.length).toBe(1);
    expect(data.observations.length).toBe(1);
    expect(data.summaries.length).toBe(1);
    expect(data.prompts.length).toBe(1);
    expect(data.sessions[0].content_session_id).toBe("test-cs-001");
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
